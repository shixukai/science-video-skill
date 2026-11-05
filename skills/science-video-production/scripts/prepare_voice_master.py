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


def prepare(episode_dir, source, output, record, profile=DEFAULT_PROFILE, ffmpeg=None, ffprobe=None,
            upstream_record=None):
    root, src, out, rec, prof = paths(episode_dir, source, output, record, profile)
    preset, target, ceiling, rate, profile_hash = read_preset(prof)
    ffmpeg = find_tool(ffmpeg, "ffmpeg")
    ffprobe = find_tool(ffprobe, "ffprobe", ffmpeg)
    ffmpeg_version = run([ffmpeg, "-version"]).stdout.splitlines()[0]
    ffprobe_version = run([ffprobe, "-version"]).stdout.splitlines()[0]
    source_hash = sha256(src)
    upstream = read_upstream(upstream_record, root, src, source_hash, out, rec, prof)
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
    parser.add_argument("--episode-dir", required=True, help="existing episode root for relative source-chain references")
    parser.add_argument("--input", required=True, help="whole dry narration; relative paths use episode-dir")
    parser.add_argument("--output", required=True, help="new WAV; relative paths use episode-dir")
    parser.add_argument("--record", required=True, help="new provenance JSON; relative paths use episode-dir")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--upstream-record", help="existing processed concatenate_full_segments record for necessary segmented synthesis")
    parser.add_argument("--ffmpeg", help="existing local ffmpeg binary (otherwise PATH)")
    parser.add_argument("--ffprobe", help="existing ffprobe (otherwise beside ffmpeg or PATH)")
    args = parser.parse_args(argv)
    try:
        result = prepare(args.episode_dir, args.input, args.output, args.record,
                         args.profile, args.ffmpeg, args.ffprobe, args.upstream_record)
    except (VoiceMasterError, OSError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"status": "processed", "output": result["output"],
                      "record": str((Path(args.episode_dir).resolve() / args.record).resolve()), "preset_id": result["preset_id"],
                      "measured_after": result["measured_after"], "gain": result["gain"],
                      "mix_review": result["mix_review"], "listening": "pending"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
