#!/usr/bin/env python3
"""Prepare one whole narration master with measured, constant linear gain.

This local tool does not synthesize, join, crop, compress or pitch-shift audio.
It records technical processing only; actual voice/listening QA stays pending.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import struct
import subprocess
import sys
import tempfile


DEFAULT_PROFILE = Path(__file__).resolve().parents[1] / "config/series-profile.json"
PEAK_MARGIN_DB = 0.1  # Meter rounding/resampling headroom, not a new sound-quality score.


class VoiceMasterError(RuntimeError):
    """An actionable processing failure without any voice-quality verdict."""


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def finite(value, label):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise VoiceMasterError(label + " is not a finite number") from None
    if isinstance(value, bool) or not math.isfinite(result):
        raise VoiceMasterError(label + " is not a finite number")
    return result


def read_preset(profile):
    raw = Path(profile).read_bytes()
    try:
        preset = json.loads(raw)["audio"]["mix_preset"]
        master = preset["narration_master"]
    except (ValueError, KeyError, TypeError):
        raise VoiceMasterError("Profile needs audio.mix_preset.narration_master") from None
    if not isinstance(preset, dict) or not isinstance(master, dict):
        raise VoiceMasterError("mix_preset and narration_master must be objects")
    if (not isinstance(preset.get("id"), str) or not preset["id"].strip() or
            master.get("processing_mode") != "whole_track_linear_gain"):
        raise VoiceMasterError("An identified whole_track_linear_gain preset is required")
    target = finite(master.get("target_i_lufs"), "target_i_lufs")
    ceiling = finite(master.get("true_peak_ceiling_dbtp"), "true_peak_ceiling_dbtp")
    rate = master.get("output_sample_rate_hz")
    if not -70 <= target <= -5 or not -9 <= ceiling <= 0:
        raise VoiceMasterError("Target is outside FFmpeg loudnorm measurement ranges")
    if isinstance(rate, bool) or not isinstance(rate, int) or rate <= 0:
        raise VoiceMasterError("output_sample_rate_hz must be a positive integer")
    if (finite(preset.get("pitch_shift_semitones", 0), "pitch_shift_semitones") != 0 or
            finite(preset.get("speed_factor", 1), "speed_factor") != 1 or
            preset.get("per_shot_normalization", False) is not False):
        raise VoiceMasterError("This tool supports no speed, pitch or per-shot processing")
    processors = preset.get("optional_processors", {})
    if not isinstance(processors, dict) or any(value != "bypass" for value in processors.values()):
        raise VoiceMasterError("Optional processors must be bypassed for this linear-gain tool")
    return preset, target, ceiling, rate, hashlib.sha256(raw).hexdigest()


def find_tool(requested, name, partner=None):
    candidate = requested
    if candidate is None and partner is not None:
        adjacent = Path(partner).with_name(name + Path(partner).suffix)
        if adjacent.is_file():
            candidate = str(adjacent)
    candidate = candidate or shutil.which(name)
    if not candidate:
        raise VoiceMasterError("Existing local " + name + " was not found; supply its path")
    path = Path(candidate).expanduser()
    if not path.is_file():
        found = shutil.which(str(candidate))
        if found:
            path = Path(found)
    if not path.is_file():
        raise VoiceMasterError("Existing local " + name + " was not found")
    return str(path.resolve())


def run(command):
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", shell=False)
    except OSError as error:
        raise VoiceMasterError("Cannot run the selected local tool: " + str(error)) from error
    if result.returncode:
        raise VoiceMasterError("Local audio command failed: " + result.stderr.strip()[-1800:])
    return result


def probe(path, ffprobe):
    result = run([ffprobe, "-v", "error", "-protocol_whitelist", "file,pipe", "-i", str(path),
                  "-show_streams", "-show_format", "-of", "json"])
    try:
        data = json.loads(result.stdout)
        streams = [item for item in data.get("streams", []) if item.get("codec_type") == "audio"]
        if len(streams) != 1:
            raise VoiceMasterError("Input/output must have exactly one audio stream")
        audio = streams[0]
        rate, channels = int(audio["sample_rate"]), int(audio["channels"])
        if audio.get("duration_ts") is not None and audio.get("time_base"):
            duration = float(int(audio["duration_ts"]) * Fraction(audio["time_base"]))
        else:
            duration = finite(audio.get("duration", data.get("format", {}).get("duration")), "duration")
        if rate <= 0 or channels <= 0 or duration <= 0:
            raise VoiceMasterError("Audio must have a positive rate, channel count and duration")
        return {"sample_rate_hz": rate, "channels": channels, "duration_seconds": duration,
                "codec": audio.get("codec_name"), "channel_layout": audio.get("channel_layout"),
                "duration_basis": "stream" if audio.get("duration_ts") is not None else "container"}
    except (ValueError, KeyError, TypeError):
        raise VoiceMasterError("Cannot read a valid audio stream from the probe") from None


def measure(path, ffmpeg, target, ceiling):
    # loudnorm is used only to measure INPUT values; its processed stream is discarded.
    result = run([ffmpeg, "-hide_banner", "-nostdin", "-protocol_whitelist", "file,pipe",
                  "-i", str(path), "-map", "0:a:0", "-vn", "-af",
                  f"loudnorm=I={target}:TP={ceiling}:LRA=50:print_format=json", "-f", "null", "-"])
    matches = list(re.finditer(r'\{[^{}]*"input_i"[^{}]*\}', result.stderr, re.S))
    if not matches:
        raise VoiceMasterError("FFmpeg did not return input loudness measurements")
    try:
        raw = json.loads(matches[-1].group(0))
        return {"i_lufs": finite(raw["input_i"], "integrated loudness (silent or too-short input?)"),
                "true_peak_dbtp": finite(raw["input_tp"], "true peak"),
                "lra_lu": finite(raw["input_lra"], "loudness range")}
    except (KeyError, ValueError, TypeError):
        raise VoiceMasterError("Invalid input loudness measurement") from None


def gain_plan(measured, target, ceiling):
    desired = finite(target, "target") - finite(measured["i_lufs"], "input loudness")
    available = finite(ceiling, "ceiling") - finite(measured["true_peak_dbtp"], "input peak") - PEAK_MARGIN_DB
    applied = min(desired, available)
    return {"desired_gain_db": desired, "applied_gain_db": applied,
            "peak_limited": applied < desired - 1e-9,
            "measurement_headroom_db": PEAK_MARGIN_DB}


def read_pcm_mono(path):
    """Read RIFF WAVE PCM/float audio into mono float samples without external deps."""
    raw = Path(path).read_bytes()
    if len(raw) < 44 or raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise VoiceMasterError("Expected a valid RIFF WAVE file for continuity analysis")
    offset = 12
    fmt_chunk = None
    data_chunk = None
    while offset + 8 <= len(raw):
        kind, size = struct.unpack_from("<4sI", raw, offset)
        payload = raw[offset + 8:offset + 8 + size]
        if kind == b"fmt ":
            fmt_chunk = payload
        elif kind == b"data":
            data_chunk = payload
            break
        offset += 8 + size + (size % 2)
    if fmt_chunk is None or len(fmt_chunk) < 16 or data_chunk is None:
        raise VoiceMasterError("WAV file is missing fmt or data chunk")
    fmt_tag, channels, rate, _, block_align, bits = struct.unpack_from("<HHIIHH", fmt_chunk, 0)
    if fmt_tag == 0xFFFE and len(fmt_chunk) >= 40:
        fmt_tag = struct.unpack_from("<H", fmt_chunk, 24)[0]
    if channels <= 0 or rate <= 0 or block_align <= 0:
        raise VoiceMasterError("Invalid WAV header channel/rate parameters")
    frames = len(data_chunk) // block_align
    if frames <= 0:
        raise VoiceMasterError("WAV data chunk contains no audio frames")
    trimmed = data_chunk[:frames * block_align]
    if fmt_tag == 3 and bits == 32:
        values = struct.unpack("<" + "f" * (frames * channels), trimmed)
    elif fmt_tag == 3 and bits == 64:
        values = struct.unpack("<" + "d" * (frames * channels), trimmed)
    elif fmt_tag == 1 and bits == 16:
        ints = struct.unpack("<" + "h" * (frames * channels), trimmed)
        values = [v / 32768.0 for v in ints]
    elif fmt_tag == 1 and bits == 32:
        ints = struct.unpack("<" + "i" * (frames * channels), trimmed)
        values = [v / 2147483648.0 for v in ints]
    elif fmt_tag == 1 and bits == 24:
        values = []
        for idx in range(0, len(trimmed), 3):
            b0, b1, b2 = trimmed[idx], trimmed[idx + 1], trimmed[idx + 2]
            val = b0 | (b1 << 8) | (b2 << 16)
            if val & 0x800000:
                val -= 0x1000000
            values.append(val / 8388608.0)
    else:
        raise VoiceMasterError(f"Unsupported WAV encoding (tag={fmt_tag}, bits={bits})")
    if channels == 1:
        mono = list(values)
    else:
        inv = 1.0 / channels
        mono = [sum(values[i * channels:(i + 1) * channels]) * inv for i in range(frames)]
    return rate, channels, mono


def estimate_frame_f0(frame_samples, sample_rate):
    """Estimate fundamental frequency (Hz) on a voiced speech frame using autocorrelation."""
    step = max(1, sample_rate // 6000)
    eff_rate = sample_rate / step
    sub = frame_samples[::step]
    n = len(sub)
    if n < 32:
        return None
    mean = sum(sub) / n
    centered = [x - mean for x in sub]
    energy0 = sum(x * x for x in centered)
    if energy0 <= 1e-10:
        return None
    min_lag = max(2, int(eff_rate / 380.0))
    max_lag = min(n // 2, int(eff_rate / 75.0))
    if min_lag >= max_lag:
        return None
    best_lag = None
    best_corr = -1.0
    corrs = {}
    for lag in range(min_lag, max_lag + 1):
        limit = n - lag
        num = 0.0
        e1 = 0.0
        e2 = 0.0
        for i in range(limit):
            a = centered[i]
            b = centered[i + lag]
            num += a * b
            e1 += a * a
            e2 += b * b
        denom = math.sqrt(e1 * e2)
        corr = num / denom if denom > 1e-12 else 0.0
        corrs[lag] = corr
        if corr > best_corr:
            best_corr = corr
            best_lag = lag
    if best_lag is None or best_corr < 0.55:
        return None
    threshold = max(0.55, 0.92 * best_corr)
    for lag in range(min_lag + 1, max_lag):
        if corrs[lag] >= threshold and corrs[lag] >= corrs[lag - 1] and corrs[lag] >= corrs[lag + 1]:
            best_lag = lag
            break
    refined_lag = float(best_lag)
    if min_lag < best_lag < max_lag:
        y1, y2, y3 = corrs[best_lag - 1], corrs[best_lag], corrs[best_lag + 1]
        denom = y1 - 2.0 * y2 + y3
        if abs(denom) > 1e-9:
            delta = 0.5 * (y1 - y3) / denom
            if -0.5 <= delta <= 0.5:
                refined_lag += delta
    return round(eff_rate / refined_lag, 2)


def _percentile(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = (len(sorted_vals) - 1) * (q / 100.0)
    lo = int(math.floor(pos))
    hi = min(len(sorted_vals) - 1, lo + 1)
    frac = pos - lo
    return float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)


def analyze_continuity(path, boundaries=None, window_seconds=3.0, peak_limited=False, target_shortfall_lu=0.0):
    """Measure windowed active-speech level, pitch register, spectral ZCR and seam jumps."""
    rate, _, mono = read_pcm_mono(path)
    total_frames = len(mono)
    duration = total_frames / rate
    frame_len = max(1, int(round(rate * 0.05)))
    frame_step = frame_len / rate
    frames = []
    for idx in range(0, total_frames, frame_len):
        chunk = mono[idx:idx + frame_len]
        if len(chunk) < max(4, frame_len // 4):
            break
        sq_sum = 0.0
        peak = 0.0
        crossings = 0
        prev = chunk[0]
        for s in chunk:
            abs_s = abs(s)
            if abs_s > peak:
                peak = abs_s
            sq_sum += s * s
            if (prev <= 0.0 < s) or (prev >= 0.0 > s):
                crossings += 1
            prev = s
        rms = math.sqrt(sq_sum / len(chunk))
        rms_db = 20.0 * math.log10(max(rms, 1e-9))
        peak_db = 20.0 * math.log10(max(peak, 1e-9))
        zcr_hz = (crossings / (len(chunk) / rate)) * 0.5
        t_mid = (idx + 0.5 * len(chunk)) / rate
        f0 = estimate_frame_f0(chunk, rate) if rms_db > -50.0 else None
        frames.append({"t": t_mid, "rms": rms, "rms_db": rms_db, "peak_db": peak_db, "zcr_hz": zcr_hz, "f0": f0})

    non_silent_rms = sorted(f["rms_db"] for f in frames if f["rms_db"] > -65.0)
    p95_rms = _percentile(non_silent_rms, 95.0) if non_silent_rms else -65.0
    active_gate_db = max(-50.0, p95_rms - 22.0)
    for f in frames:
        f["active"] = f["rms_db"] >= active_gate_db

    eff_window = min(float(window_seconds), max(1.0, duration / 4.0)) if duration > 0 else float(window_seconds)
    num_windows = max(1, int(math.ceil(duration / eff_window)))
    windows = []
    isolated_transients = []
    for w_idx in range(num_windows):
        w_start = w_idx * eff_window
        w_end = min(duration, (w_idx + 1) * eff_window)
        w_frames = [f for f in frames if w_start <= f["t"] < w_end or (w_idx == num_windows - 1 and f["t"] <= w_end)]
        if not w_frames:
            continue
        act = [f for f in w_frames if f["active"]]
        if not act:
            continue
        mean_sq = sum(f["rms"] * f["rms"] for f in act) / len(act)
        act_rms_db = round(20.0 * math.log10(max(math.sqrt(mean_sq), 1e-9)), 2)
        w_peak_db = round(max(f["peak_db"] for f in w_frames), 2)
        f0s = [f["f0"] for f in act if f["f0"] is not None]
        w_f0 = round(float(statistics.median(f0s)), 2) if f0s else None
        w_zcr = round(float(statistics.median(f["zcr_hz"] for f in act)), 1)
        crest_db = round(w_peak_db - act_rms_db, 2)
        w_item = {"start": round(w_start, 3), "end": round(w_end, 3), "active_rms_dbfs": act_rms_db,
                  "peak_dbfs": w_peak_db, "crest_db": crest_db, "f0_median_hz": w_f0, "zcr_median_hz": w_zcr}
        windows.append(w_item)
        if crest_db >= 13.0 and w_peak_db >= -6.0:
            peak_frame = max(w_frames, key=lambda item: item["peak_db"])
            isolated_transients.append({"second": round(peak_frame["t"], 3), "peak_dbfs": w_peak_db,
                                        "active_rms_dbfs": act_rms_db, "crest_db": crest_db})

    rms_vals = sorted(w["active_rms_dbfs"] for w in windows)
    rms_median = round(_percentile(rms_vals, 50.0), 2) if rms_vals else None
    rms_spread = round((_percentile(rms_vals, 95.0) - _percentile(rms_vals, 5.0)) if len(rms_vals) >= 5
                       else ((rms_vals[-1] - rms_vals[0]) if len(rms_vals) >= 2 else 0.0), 2)
    max_level_jump = 0.0
    max_level_jump_at = None
    max_semitone_jump = 0.0
    max_semitone_jump_at = None
    for left_w, right_w in zip(windows, windows[1:]):
        ljump = abs(right_w["active_rms_dbfs"] - left_w["active_rms_dbfs"])
        if ljump > max_level_jump:
            max_level_jump = round(ljump, 2)
            max_level_jump_at = right_w["start"]
        if left_w["f0_median_hz"] and right_w["f0_median_hz"] and left_w["f0_median_hz"] > 0 and right_w["f0_median_hz"] > 0:
            sjump = abs(12.0 * math.log2(right_w["f0_median_hz"] / left_w["f0_median_hz"]))
            if sjump > max_semitone_jump:
                max_semitone_jump = round(sjump, 2)
                max_semitone_jump_at = right_w["start"]

    f0_vals = sorted(w["f0_median_hz"] for w in windows if w["f0_median_hz"] is not None)
    f0_median = round(_percentile(f0_vals, 50.0), 2) if f0_vals else None
    f0_spread_st = round(12.0 * math.log2(f0_vals[-1] / f0_vals[0]), 2) if len(f0_vals) >= 2 and f0_vals[0] > 0 else 0.0

    boundary_checks = []
    span = max(1.5, eff_window)
    for b_raw in (boundaries or []):
        b_sec = finite(b_raw, "boundary second")
        if not (0.0 < b_sec < duration):
            continue
        left_act = [f for f in frames if max(0.0, b_sec - span) <= f["t"] < b_sec and f["active"]]
        right_act = [f for f in frames if b_sec <= f["t"] <= min(duration, b_sec + span) and f["active"]]
        if not left_act or not right_act:
            continue
        l_rms = round(20.0 * math.log10(max(math.sqrt(sum(f["rms"] ** 2 for f in left_act) / len(left_act)), 1e-9)), 2)
        r_rms = round(20.0 * math.log10(max(math.sqrt(sum(f["rms"] ** 2 for f in right_act) / len(right_act)), 1e-9)), 2)
        l_f0s = [f["f0"] for f in left_act if f["f0"] is not None]
        r_f0s = [f["f0"] for f in right_act if f["f0"] is not None]
        l_f0 = round(float(statistics.median(l_f0s)), 2) if l_f0s else None
        r_f0 = round(float(statistics.median(r_f0s)), 2) if r_f0s else None
        lvl_diff = round(r_rms - l_rms, 2)
        st_diff = round(12.0 * math.log2(r_f0 / l_f0), 2) if (l_f0 and r_f0 and l_f0 > 0 and r_f0 > 0) else 0.0
        flagged = abs(lvl_diff) > 2.5 or abs(st_diff) > 2.0
        boundary_checks.append({
            "at_seconds": round(b_sec, 3), "left_active_rms_dbfs": l_rms, "right_active_rms_dbfs": r_rms,
            "level_jump_db": lvl_diff, "left_f0_hz": l_f0, "right_f0_hz": r_f0,
            "semitone_jump": st_diff, "flagged": flagged,
        })

    flags = []
    if max_level_jump > 3.0:
        flags.append("adjacent_window_level_jump")
    if rms_spread > 4.5:
        flags.append("wide_episode_level_spread")
    if max_semitone_jump > 2.5:
        flags.append("pitch_register_jump")
    if any(item["flagged"] for item in boundary_checks):
        flags.append("boundary_level_or_pitch_jump")
    if isolated_transients and (peak_limited or target_shortfall_lu > 2.0):
        flags.append("isolated_transient_limiting_gain")

    isolated_transients.sort(key=lambda item: item["peak_dbfs"], reverse=True)
    return {
        "window_seconds": round(eff_window, 3),
        "frame_seconds": round(frame_step, 4),
        "active_gate_dbfs": round(active_gate_db, 2),
        "active_window_count": len(windows),
        "active_rms_median_dbfs": rms_median,
        "active_rms_spread_db": rms_spread,
        "max_adjacent_level_jump_db": max_level_jump,
        "max_adjacent_level_jump_at_seconds": max_level_jump_at,
        "f0_median_hz": f0_median,
        "f0_spread_semitones": f0_spread_st,
        "max_adjacent_semitone_jump": max_semitone_jump,
        "max_adjacent_semitone_jump_at_seconds": max_semitone_jump_at,
        "isolated_transient_peaks": isolated_transients[:10],
        "boundary_checks": boundary_checks,
        "flags": flags,
        "status": "flagged_for_review" if flags else "within_nominal_bounds",
    }


def paths(episode_dir, source, output, record, profile):
    root = Path(episode_dir).resolve(strict=True)
    if not root.is_dir():
        raise VoiceMasterError("episode-dir must be an existing directory")
    def episode_path(item):
        value = Path(item).expanduser()
        return value if value.is_absolute() else root / value

    if any(episode_path(item).is_symlink() for item in (output, record)):
        raise VoiceMasterError("Output and record must be new files, not symbolic links")
    src, out, rec = [episode_path(item).resolve() for item in (source, output, record)]
    prof = Path(profile).expanduser().resolve()
    if not src.is_file() or not prof.is_file():
        raise VoiceMasterError("The source audio and selected profile must already exist")
    identities = [os.path.normcase(str(item)) for item in (src, out, rec, prof)]
    if len(set(identities)) != len(identities):
        raise VoiceMasterError("Source, output, record and profile paths must be distinct")
    if not all(item.is_relative_to(root) for item in (src, out, rec)):
        raise VoiceMasterError("Source, output and record must stay inside episode-dir")
    if out.suffix.lower() != ".wav" or rec.suffix.lower() != ".json":
        raise VoiceMasterError("Output must be a new .wav and record a new .json")
    if out.exists() or rec.exists():
        raise VoiceMasterError("Output or record already exists; choose new versioned paths")
    return root, src, out, rec, prof


def read_upstream(path, root, source, source_hash, output, record, profile):
    """Bind only an existing legacy full-segment concatenation record."""
    if path is None:
        return None
    value = Path(path).expanduser()
    path = (value if value.is_absolute() else root / value).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file() or path in (source, output, record, profile):
        raise VoiceMasterError("upstream-record must be a distinct existing episode-contained file")
    raw = path.read_bytes()
    try:
        data = json.loads(raw)
    except ValueError:
        raise VoiceMasterError("Invalid upstream record JSON") from None
    if (not isinstance(data, dict) or data.get("schema_version") != 1 or
            data.get("status") != "processed" or data.get("mode") != "concatenate_full_segments"):
        raise VoiceMasterError("upstream-record must be a processed concatenate_full_segments record")

    def ref(item):
        if not isinstance(item, dict) or not isinstance(item.get("file"), str):
            raise VoiceMasterError("Missing upstream file reference")
        name = Path(item["file"])
        resolved = (root / name).resolve()
        if name.is_absolute() or not resolved.is_relative_to(root) or not resolved.is_file():
            raise VoiceMasterError("Unsafe/missing upstream source/output reference")
        if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256"))) or sha256(resolved) != item["sha256"]:
            raise VoiceMasterError("Upstream source/output hash mismatch")
        return resolved

    if ref(data.get("output")) != source or data["output"]["sha256"] != source_hash:
        raise VoiceMasterError("Upstream output must bind the actual whole-track input")
    sources = data.get("sources")
    steps = data.get("steps")
    if not isinstance(sources, list) or len(sources) < 2:
        raise VoiceMasterError("Upstream concatenation needs its ordered sources")
    for item in sources:
        ref(item)
    if not isinstance(steps, list) or not steps or any(
            not isinstance(step, dict) or not step.get("tool") or not step.get("version") or
            not step.get("parameters") for step in steps):
        raise VoiceMasterError("Upstream record needs actual processing steps")
    return {"file": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(raw).hexdigest()}


@contextmanager
def reserve(output, record):
    """Hold exclusive new files so another writer cannot win a publication race."""
    handles = []
    ok = False
    try:
        for path in (output, record):
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = path.open("xb")
            handles.append((path, handle, os.fstat(handle.fileno())))
        yield handles[0][1], handles[1][1]
        ok = True
    finally:
        for path, handle, identity in handles:
            handle.close()
            if not ok:
                try:
                    current = path.stat()
                    if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                        path.unlink()
                except FileNotFoundError:
                    pass


def _parse_boundaries(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [finite(item, "boundary second") for item in value]
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
        return [finite(part, "boundary second") for part in parts]
    raise VoiceMasterError("boundaries must be a list of seconds or comma-separated string")


def _infer_upstream_boundaries(upstream, root):
    if not upstream:
        return []
    try:
        data = json.loads((root / upstream["file"]).read_text(encoding="utf-8"))
        sources = data.get("sources") or []
        elapsed = 0.0
        result = []
        for item in sources[:-1]:
            rate, _, mono = read_pcm_mono(root / item["file"])
            elapsed += len(mono) / rate
            result.append(round(elapsed, 4))
        return result
    except Exception:
        return []


def prepare(episode_dir, source, output, record, profile=DEFAULT_PROFILE, ffmpeg=None, ffprobe=None,
            upstream_record=None, boundaries=None):
    root, src, out, rec, prof = paths(episode_dir, source, output, record, profile)
    preset, target, ceiling, rate, profile_hash = read_preset(prof)
    parsed_boundaries = _parse_boundaries(boundaries)
    ffmpeg = find_tool(ffmpeg, "ffmpeg")
    ffprobe = find_tool(ffprobe, "ffprobe", ffmpeg)
    ffmpeg_version = run([ffmpeg, "-version"]).stdout.splitlines()[0]
    ffprobe_version = run([ffprobe, "-version"]).stdout.splitlines()[0]
    source_hash = sha256(src)
    upstream = read_upstream(upstream_record, root, src, source_hash, out, rec, prof)
    if parsed_boundaries is None and upstream:
        parsed_boundaries = _infer_upstream_boundaries(upstream, root)
    before_info = probe(src, ffprobe)
    before = measure(src, ffmpeg, target, ceiling)
    plan = gain_plan(before, target, ceiling)
    started = datetime.now(timezone.utc).isoformat()
    with reserve(out, rec) as (audio_handle, record_handle):
        # Only this task-owned temporary directory is cleaned up.
        with tempfile.TemporaryDirectory(prefix="voice-master-", dir=out.parent) as temporary:
            candidate = Path(temporary) / "master.wav"
            render_commands = []
            for attempt in range(2):
                if candidate.exists():
                    candidate.unlink()  # This tool's own unpublished candidate only.
                command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
                           "-protocol_whitelist", "file,pipe", "-i", str(src), "-map", "0:a:0", "-vn",
                           "-af", f"volume={plan['applied_gain_db']:.10f}dB:precision=double:eval=once",
                           "-ar", str(rate), "-c:a", "pcm_f32le", str(candidate)]
                run(command)
                render_commands.append(command)
                after = measure(candidate, ffmpeg, target, ceiling)
                if after["true_peak_dbtp"] <= ceiling:
                    break
                if attempt == 1:
                    raise VoiceMasterError("Measured output still exceeds true-peak ceiling after one bounded correction")
                plan["applied_gain_db"] -= after["true_peak_dbtp"] - ceiling + PEAK_MARGIN_DB
                plan["peak_limited"] = True
            after_info = probe(candidate, ffprobe)
            if after_info["sample_rate_hz"] != rate or after_info["channels"] != before_info["channels"]:
                raise VoiceMasterError("Processed rate or channels differ from the declared recipe")
            if (before_info["channel_layout"] and after_info["channel_layout"] and
                    before_info["channel_layout"] != after_info["channel_layout"]):
                raise VoiceMasterError("Channel layout changed")
            duration_delta = after_info["duration_seconds"] - before_info["duration_seconds"]
            # PCM/FLAC timestamps are sample-based; compressed container durations
            # can include decoder priming. Do not call that sample-exact evidence.
            lossless = str(before_info["codec"]).startswith("pcm_") or before_info["codec"] == "flac"
            duration_tolerance = 2 / min(rate, before_info["sample_rate_hz"]) if lossless else 0.05
            if abs(duration_delta) > duration_tolerance:
                raise VoiceMasterError("Audio duration changed beyond the applicable sample/container rounding")
            if (sha256(src) != source_hash or sha256(prof) != profile_hash or
                    (upstream and sha256(root / upstream["file"]) != upstream["sha256"])):
                raise VoiceMasterError("Source audio or profile changed during processing; prepare a new version")
            continuity = analyze_continuity(
                candidate, boundaries=parsed_boundaries, peak_limited=plan["peak_limited"],
                target_shortfall_lu=max(0.0, target - after["i_lufs"]))
            output_hash = sha256(candidate)
            document = {"schema_version": 1, "status": "processed", "kind": "whole_narration_master",
                "mode": "whole_track_linear_gain",
                "source": {"file": src.relative_to(root).as_posix(), "sha256": source_hash},
                "output": {"file": out.relative_to(root).as_posix(), "sha256": output_hash},
                "steps": [{"tool": ffmpeg, "version": ffmpeg_version,
                           "parameters": {"processing_mode": "whole_track_linear_gain",
                               "gain_db": plan["applied_gain_db"], "output_sample_rate_hz": rate,
                               "codec": "pcm_f32le", "channels": "preserve", "render_commands": render_commands,
                               "pitch_shift_semitones": 0, "speed_factor": 1,
                               "dynamic_compression": False, "per_shot_normalization": False}}],
                "preset_id": preset["id"], "profile_sha256": profile_hash,
                "targets": {"narration_i_lufs": target, "true_peak_ceiling_dbtp": ceiling},
                "measured_before": before, "measured_after": after, "gain": plan,
                "integrated_difference_from_target_lu": after["i_lufs"] - target,
                "continuity_diagnostics": continuity,
                "mix_review": "needed_for_peak_limited_target" if plan["peak_limited"] else "pending",
                "probe": {"tool": ffprobe, "version": ffprobe_version, "before": before_info,
                          "after": after_info, "duration_difference_seconds": duration_delta,
                          "sample_exact_duration_basis": lossless},
                "technical": {"true_peak_ceiling_met": True, "render_attempts": len(render_commands),
                              "source_preserved": True, "quality_approval": False},
                "listening": {"status": "pending", "heard": False},
                "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(),
                "limits": "One constant gain for the whole supplied narration. No synthesis, pitch/register/timbre recognition, per-shot levelling, dynamic compression, equalization or denoising. Headroom-limited loudness is reported for mix review; actual voice/source/final listening remains required. Final music/effects mix uses its separate policy."}
            if upstream:
                document["upstream_record"] = upstream
            with candidate.open("rb") as stream:
                shutil.copyfileobj(stream, audio_handle)
            audio_handle.flush()
            os.fsync(audio_handle.fileno())
            record_handle.write((json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8"))
            record_handle.flush()
            os.fsync(record_handle.fileno())
    return document


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-dir", help="existing episode root for relative source-chain references")
    parser.add_argument("--input", required=True, help="whole dry narration; relative paths use episode-dir")
    parser.add_argument("--output", help="new WAV; relative paths use episode-dir")
    parser.add_argument("--record", help="new provenance JSON; relative paths use episode-dir")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--upstream-record", help="existing processed concatenate_full_segments record for necessary segmented synthesis")
    parser.add_argument("--boundaries", help="optional comma-separated boundary seconds for seam level/pitch continuity diagnostics")
    parser.add_argument("--analyze-only", action="store_true", help="run read-only continuity/transient diagnostics on --input without writing a master")
    parser.add_argument("--ffmpeg", help="existing local ffmpeg binary (otherwise PATH)")
    parser.add_argument("--ffprobe", help="existing ffprobe (otherwise beside ffmpeg or PATH)")
    args = parser.parse_args(argv)
    try:
        if args.analyze_only:
            base = Path(args.episode_dir).expanduser().resolve(strict=True) if args.episode_dir else Path.cwd()
            inp = Path(args.input).expanduser()
            target_wav = (inp if inp.is_absolute() else base / inp).resolve(strict=True)
            diag = analyze_continuity(target_wav, boundaries=_parse_boundaries(args.boundaries))
            print(json.dumps({"status": "analyzed", "input": str(target_wav),
                              "continuity_diagnostics": diag, "listening": "pending"}, ensure_ascii=False))
            return 0
        if not args.episode_dir or not args.output or not args.record:
            raise VoiceMasterError("--episode-dir, --output and --record are required unless --analyze-only is set")
        result = prepare(args.episode_dir, args.input, args.output, args.record,
                         args.profile, args.ffmpeg, args.ffprobe, args.upstream_record,
                         boundaries=args.boundaries)
    except (VoiceMasterError, OSError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"status": "processed", "output": result["output"],
                      "record": str((Path(args.episode_dir).resolve() / args.record).resolve()), "preset_id": result["preset_id"],
                      "measured_after": result["measured_after"], "gain": result["gain"],
                      "continuity_status": result["continuity_diagnostics"]["status"],
                      "continuity_flags": result["continuity_diagnostics"]["flags"],
                      "mix_review": result["mix_review"], "listening": "pending"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
