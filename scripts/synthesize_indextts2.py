#!/usr/bin/env python3
"""Default series Mandarin voice-clone adapter using local IndexTTS-2.5.

Synthesizes cohesive conversational narration paragraphs (split strictly on
blank lines ``\\n\\n`` without per-shot slicing) using an explicitly confirmed
local ``IndexTeam/IndexTTS-2.5`` checkout and a private <=15 s reference voice
prompt, concatenates paragraphs losslessly with configured silence gaps, writes
an optional clause-level ``.srt``, and outputs a hash-bound generation record
compatible with ``check_episode.py`` and ``prepare_voice_master.py --polish``.
"""

from __future__ import annotations

import argparse
import array
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import struct
import sys
import tempfile
import threading
import wave
from typing import Any

MODEL_ID = "IndexTeam/IndexTTS-2.5"
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = SKILL_ROOT / "config" / "series-profile.json"
_SYNTHESIS_LOCK = threading.Lock()


class SynthesisError(RuntimeError):
    """Actionable synthesis failure without leaking private narration text."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def default_baseline_path() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
    return codex_home / "data" / "science-video-production" / "voice-baseline.json"


def load_profile_defaults(profile_path: Path = DEFAULT_PROFILE) -> dict[str, Any]:
    data = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    audio = data.get("audio", {})
    cfg = audio.get("indextts2", {})
    rt = cfg.get("runtime", {})
    gen = cfg.get("generation_params", {})
    return {
        "model_id": cfg.get("model_id", audio.get("model_id", MODEL_ID)),
        "voice_preset_id": audio.get("voice_preset_id", "mandarin-indextts25-clone-polished-v1"),
        "speaker": audio.get("speaker", "user_clone"),
        "language": audio.get("language", "Chinese"),
        "lang": gen.get("lang", "ZH"),
        "duration_factor": float(gen.get("duration_factor", 1.0)),
        "interval_silence": int(gen.get("interval_silence", 220)),
        "paragraph_silence_s": float(gen.get("paragraph_silence_s", 0.55)),
        "use_emo_text": bool(gen.get("use_emo_text", False)),
        "use_bf16": bool(rt.get("use_bf16", True)),
        "use_cuda_kernel": bool(rt.get("use_cuda_kernel", False)),
        "use_qwen_emo": bool(rt.get("use_qwen_emo", False)),
        "speech_polish_preset": cfg.get("speech_polish_preset", "mandarin-clone-polish-v1"),
    }


def resolve_baseline(baseline_path: Path | None, use_baseline: bool) -> dict[str, Any]:
    if not use_baseline:
        return {}
    explicit = baseline_path is not None
    target = Path(baseline_path) if baseline_path is not None else default_baseline_path()
    if not target.is_file():
        if explicit:
            raise SynthesisError(f"Requested baseline file does not exist: {target}")
        return {}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SynthesisError(f"Unreadable baseline JSON ({target}): {exc}") from exc
    if not isinstance(data, dict):
        return {}
    if data.get("backend") == "local_indextts2" and data.get("provider") == "IndexTTS":
        return data
    return {}


def validate_local_checkpoints(
    checkpoints_dir: Path,
    cfg_path: Path,
    *,
    use_qwen_emo: bool,
    allow_model_download: bool,
) -> None:
    if not cfg_path.is_file():
        raise SynthesisError(f"IndexTTS-2.5 config file not found: {cfg_path}")
    if allow_model_download:
        return
    if not checkpoints_dir.is_dir():
        raise SynthesisError(f"IndexTTS-2.5 checkpoints directory not found: {checkpoints_dir}")
    missing: list[str] = []
    for rel_file in ("gpt.pth", "codec.pth", "s2mel.pth", "hf_cache/campplus_cn_common.bin"):
        if not (checkpoints_dir / rel_file).is_file():
            missing.append(rel_file)
    for rel_dir in ("hf_cache/w2v-bert-2.0", "hf_cache/bigvgan"):
        if not (checkpoints_dir / rel_dir).is_dir():
            missing.append(rel_dir)
    if use_qwen_emo and not (checkpoints_dir / "qwen0.6bemo4-merge").is_dir():
        missing.append("qwen0.6bemo4-merge")
    if missing:
        raise SynthesisError(
            "Missing local IndexTTS-2.5 checkpoints (offline mode): " + ", ".join(missing)
        )


def checkpoints_fingerprint(checkpoints_dir: Path, cfg_path: Path) -> str:
    h = hashlib.sha256()
    h.update(Path(cfg_path).read_bytes())
    entries: list[tuple[str, int]] = []
    if checkpoints_dir.is_dir():
        for child in sorted(checkpoints_dir.iterdir(), key=lambda p: p.name):
            if child.name.startswith("."):
                continue
            if child.is_file():
                entries.append((child.name, child.stat().st_size))
        hf_cache = checkpoints_dir / "hf_cache"
        if hf_cache.is_dir():
            for item in sorted(hf_cache.rglob("*"), key=lambda p: p.as_posix()):
                rel = item.relative_to(checkpoints_dir)
                if item.is_file() and not any(part.startswith(".") for part in rel.parts):
                    entries.append((rel.as_posix(), item.stat().st_size))
    h.update(json.dumps(entries, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    return h.hexdigest()


def git_head_commit(project_dir: Path) -> str | None:
    git_dir = project_dir / ".git"
    head_file = git_dir / "HEAD"
    if not head_file.is_file():
        return None
    try:
        head_text = head_file.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    if re.fullmatch(r"[0-9a-fA-F]{40}", head_text):
        return head_text.lower()
    if head_text.startswith("ref:"):
        ref_rel = head_text.split(":", 1)[1].strip()
        ref_file = git_dir / ref_rel
        if ref_file.is_file():
            val = ref_file.read_text(encoding="utf-8", errors="replace").strip()
            if re.fullmatch(r"[0-9a-fA-F]{40}", val):
                return val.lower()
        packed = git_dir / "packed-refs"
        if packed.is_file():
            for line in packed.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line or line.startswith(("#", "^")):
                    continue
                parts = line.split()
                if len(parts) == 2 and parts[1] == ref_rel and re.fullmatch(r"[0-9a-fA-F]{40}", parts[0]):
                    return parts[0].lower()
    return None


def probe_wav_info(path: Path) -> dict[str, Any]:
    path = Path(path)
    try:
        with wave.open(str(path), "rb") as wf:
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            rate = wf.getframerate()
            frames = wf.getnframes()
            raw = wf.readframes(frames)
        if rate <= 0 or channels <= 0 or frames <= 0:
            raise SynthesisError(f"Invalid WAV audio parameters in {path}")
        peak_abs: float | None = None
        if sampwidth == 2:
            arr = array.array("h")
            arr.frombytes(raw[: frames * channels * 2])
            if sys.byteorder != "little":
                arr.byteswap()
            peak_abs = max((abs(v) / 32768.0 for v in arr), default=0.0)
        elif sampwidth == 4:
            arr_i = array.array("i")
            arr_i.frombytes(raw[: frames * channels * 4])
            if sys.byteorder != "little":
                arr_i.byteswap()
            peak_abs = max((abs(v) / 2147483648.0 for v in arr_i), default=0.0)
        elif sampwidth == 1:
            peak_abs = max((abs(b - 128) / 128.0 for b in raw), default=0.0)
        return {
            "sample_rate": rate,
            "channels": channels,
            "sampwidth": sampwidth,
            "frames": frames,
            "duration_seconds": frames / float(rate),
            "peak_abs": peak_abs,
        }
    except wave.Error:
        raw = path.read_bytes()
        if len(raw) < 44 or raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
            raise SynthesisError(f"Unreadable WAV file: {path}") from None
        offset = 12
        fmt_chunk = None
        data_chunk = None
        while offset + 8 <= len(raw):
            kind, size = struct.unpack_from("<4sI", raw, offset)
            payload = raw[offset + 8 : offset + 8 + size]
            if kind == b"fmt ":
                fmt_chunk = payload
            elif kind == b"data":
                data_chunk = payload
                break
            offset += 8 + size + (size % 2)
        if fmt_chunk is None or len(fmt_chunk) < 16 or data_chunk is None:
            raise SynthesisError(f"Malformed WAV chunks in {path}") from None
        fmt_tag, channels, rate, _, block_align, bits = struct.unpack_from("<HHIIHH", fmt_chunk, 0)
        if fmt_tag == 0xFFFE and len(fmt_chunk) >= 40:
            fmt_tag = struct.unpack_from("<H", fmt_chunk, 24)[0]
        if rate <= 0 or channels <= 0 or block_align <= 0:
            raise SynthesisError(f"Invalid WAV format values in {path}") from None
        frames = len(data_chunk) // block_align
        if frames <= 0:
            raise SynthesisError(f"Empty WAV data in {path}") from None
        peak_abs = None
        if fmt_tag == 3 and bits == 32:
            arr_f = array.array("f")
            arr_f.frombytes(data_chunk[: frames * channels * 4])
            if sys.byteorder != "little":
                arr_f.byteswap()
            if not all(math.isfinite(v) for v in arr_f):
                raise SynthesisError(f"Non-finite audio sample in {path}")
            peak_abs = max((abs(v) for v in arr_f), default=0.0)
        return {
            "sample_rate": rate,
            "channels": channels,
            "sampwidth": bits // 8,
            "frames": frames,
            "duration_seconds": frames / float(rate),
            "peak_abs": peak_abs,
        }


def _trim_edge_silence_pcm(
    data: bytes,
    params: Any,
    *,
    threshold_dbfs: float = -45.0,
    keep_head_s: float = 0.04,
    keep_tail_s: float = 0.04,
) -> tuple[bytes, float, float]:
    """Trim excess leading/trailing silence while keeping a short natural breath margin."""
    sampwidth = params.sampwidth
    channels = params.nchannels
    rate = params.framerate
    frame_bytes = sampwidth * channels
    if sampwidth not in (1, 2, 4) or frame_bytes <= 0 or rate <= 0:
        return data, 0.0, 0.0
    nframes = len(data) // frame_bytes
    if nframes <= 0:
        return data, 0.0, 0.0

    if sampwidth == 2:
        arr = array.array("h")
        arr.frombytes(data[: nframes * frame_bytes])
        if sys.byteorder != "little":
            arr.byteswap()
        scale = 1.0 / 32768.0
        samples = [v * scale for v in arr]
    elif sampwidth == 4:
        arr_i = array.array("i")
        arr_i.frombytes(data[: nframes * frame_bytes])
        if sys.byteorder != "little":
            arr_i.byteswap()
        scale = 1.0 / 2147483648.0
        samples = [v * scale for v in arr_i]
    else:
        samples = [(b - 128) / 128.0 for b in data[: nframes * frame_bytes]]

    threshold_rms = 10.0 ** (threshold_dbfs / 20.0)
    win_frames = max(1, int(round(rate * 0.01)))
    first_active: int | None = None
    last_active_end: int | None = None
    for f_start in range(0, nframes, win_frames):
        f_end = min(nframes, f_start + win_frames)
        s_lo = f_start * channels
        s_hi = f_end * channels
        seg = samples[s_lo:s_hi]
        if not seg:
            continue
        rms = math.sqrt(sum(v * v for v in seg) / len(seg))
        if rms >= threshold_rms:
            if first_active is None:
                first_active = f_start
            last_active_end = f_end

    if first_active is None or last_active_end is None:
        return data, 0.0, 0.0

    head_margin = int(round(max(0.0, keep_head_s) * rate))
    tail_margin = int(round(max(0.0, keep_tail_s) * rate))
    new_start = max(0, first_active - head_margin)
    new_end = min(nframes, last_active_end + tail_margin)
    if new_start >= new_end:
        return data, 0.0, 0.0
    trimmed_head_s = new_start / float(rate)
    trimmed_tail_s = (nframes - new_end) / float(rate)
    return data[new_start * frame_bytes : new_end * frame_bytes], trimmed_head_s, trimmed_tail_s


def concat_wavs_with_silence(
    wav_paths: list[Path],
    out_path: Path,
    silence_s: float,
    *,
    trim_edge_silence: bool = True,
) -> list[dict[str, Any]]:
    if not wav_paths:
        raise SynthesisError("No synthesized paragraph WAVs to concatenate.")
    if not isinstance(silence_s, (int, float)) or isinstance(silence_s, bool) or not math.isfinite(silence_s) or silence_s < 0:
        raise SynthesisError("paragraph_silence_s must be a finite non-negative number.")
    params = None
    chunks: list[bytes] = []
    silence_bytes = b""
    silence_dur_s = 0.0
    timings: list[dict[str, Any]] = []
    cursor_frames = 0
    silence_frames = 0
    max_peak = 0.0
    saw_peak_check = False

    for idx, p in enumerate(wav_paths):
        info = probe_wav_info(p)
        if info["peak_abs"] is not None:
            saw_peak_check = True
            max_peak = max(max_peak, float(info["peak_abs"]))
        with wave.open(str(p), "rb") as wf:
            p_params = wf.getparams()
            if params is None:
                params = p_params
                silence_frames = int(round(silence_s * params.framerate))
                silence_bytes = b"\x00" * (silence_frames * params.nchannels * params.sampwidth)
                silence_dur_s = silence_frames / float(params.framerate)
            else:
                if (p_params.nchannels, p_params.sampwidth, p_params.framerate) != (
                    params.nchannels,
                    params.sampwidth,
                    params.framerate,
                ):
                    raise SynthesisError(
                        f"Mismatched paragraph WAV format in {p}: {p_params} vs {params}"
                    )
            if idx > 0 and silence_bytes:
                chunks.append(silence_bytes)
                cursor_frames += silence_frames
            nframes = wf.getnframes()
            if nframes <= 0:
                raise SynthesisError(f"Synthesized paragraph audio is empty: {p}")
            data = wf.readframes(nframes)
        trimmed_head_s, trimmed_tail_s = 0.0, 0.0
        if trim_edge_silence:
            data, trimmed_head_s, trimmed_tail_s = _trim_edge_silence_pcm(
                data,
                params,
                keep_head_s=0.03 if idx == 0 else 0.04,
                keep_tail_s=0.04,
            )
            nframes = len(data) // (params.nchannels * params.sampwidth)
        chunks.append(data)
        start_s = cursor_frames / float(params.framerate)
        cursor_frames += nframes
        end_s = cursor_frames / float(params.framerate)
        timings.append(
            {
                "index": idx + 1,
                "start_s": round(start_s, 4),
                "end_s": round(end_s, 4),
                "duration_s": round(end_s - start_s, 4),
                "gap_after_s": round(silence_dur_s, 4) if idx < len(wav_paths) - 1 else 0.0,
                "trimmed_leading_s": round(trimmed_head_s, 4),
                "trimmed_trailing_s": round(trimmed_tail_s, 4),
            }
        )

    if saw_peak_check and max_peak <= 0.0:
        raise SynthesisError("Synthesized audio waveform is completely silent.")
    assert params is not None
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as out_wf:
        out_wf.setnchannels(params.nchannels)
        out_wf.setsampwidth(params.sampwidth)
        out_wf.setframerate(params.framerate)
        for chunk in chunks:
            out_wf.writeframes(chunk)
    return timings


def _format_srt_ts(seconds: float) -> str:
    ms_total = max(0, int(round(seconds * 1000)))
    hrs, rem = divmod(ms_total, 3_600_000)
    mins, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"


def _strip_pinyin_markup(text: str) -> str:
    return re.sub(r"<([^|>]+)\|[^>]+>", r"\1", text)


_ZH_PIVOT_START_RE = re.compile(
    r"^(?:可是|可|却|但是|但|然而|反而|结果|偏偏|于是|竟然|居然|其实|原来|没想到|问题在于|关键在于|真正)"
)
_ZH_SPLIT_TOKEN_RE = re.compile(r"(——|—{2,}|[，、。！？；：]+)")


def _split_zh_clauses_with_pauses(sentence: str, max_chars: int = 22) -> list[tuple[str, str]]:
    """Split Mandarin narration into anti-spoiler cues with trailing pause kinds."""
    cleaned = re.sub(r"\s+", "", _strip_pinyin_markup(sentence).strip())
    if not cleaned:
        return []
    tokens = _ZH_SPLIT_TOKEN_RE.split(cleaned)
    raw_items: list[tuple[str, str]] = []
    i = 0
    while i < len(tokens):
        part = tokens[i].strip("，、。！？；：—-")
        delim = tokens[i + 1] if i + 1 < len(tokens) else ""
        i += 2
        if not part:
            continue
        if "—" in delim:
            pause_kind = "dash"
        elif any(ch in delim for ch in "。！？"):
            pause_kind = "sentence"
        elif delim:
            pause_kind = "comma"
        else:
            pause_kind = "none"
        raw_items.append((part, pause_kind))

    if not raw_items:
        return [(cleaned, "none")]

    merged: list[list[str]] = []
    for part, pause_kind in raw_items:
        if merged:
            prev_text, prev_pause = merged[-1]
            # Never merge across sentence boundaries, em-dash suspense pivots, or reversal starters.
            can_merge = (
                prev_pause == "comma"
                and not _ZH_PIVOT_START_RE.match(part)
                and len(prev_text) + 1 + len(part) <= max_chars
            )
            if can_merge:
                merged[-1][0] = f"{prev_text}，{part}"
                merged[-1][1] = pause_kind
                continue
        merged.append([part, pause_kind])
    merged[-1][1] = "none"
    return [(txt, pk) for txt, pk in merged]


def _split_zh_clauses(sentence: str, max_chars: int = 22) -> list[str]:
    return [txt for txt, _ in _split_zh_clauses_with_pauses(sentence, max_chars=max_chars)]


def build_srt_from_paragraphs(
    paragraphs: list[str],
    timings: list[dict[str, Any]],
    *,
    interval_silence_ms: int = 220,
) -> str:
    cues: list[tuple[float, float, str]] = []
    sent_pause_s = max(0.0, float(interval_silence_ms) / 1000.0)
    dash_pause_s = min(0.20, max(0.14, sent_pause_s * 0.85)) if sent_pause_s > 0 else 0.14
    comma_pause_s = 0.05
    pause_map = {"sentence": sent_pause_s, "dash": dash_pause_s, "comma": comma_pause_s, "none": 0.0}

    for para, timing in zip(paragraphs, timings):
        start_s = float(timing["start_s"])
        end_s = float(timing["end_s"])
        dur_s = max(0.25, end_s - start_s)
        clauses = _split_zh_clauses_with_pauses(para)
        if not clauses:
            continue
        raw_pauses = [pause_map.get(pk, 0.0) for _, pk in clauses]
        raw_pause_total = sum(raw_pauses)
        max_pause_budget = dur_s * 0.35
        pause_scale = (max_pause_budget / raw_pause_total) if raw_pause_total > max_pause_budget and raw_pause_total > 0 else 1.0
        eff_pauses = [p * pause_scale for p in raw_pauses]
        speech_budget = max(0.15, dur_s - sum(eff_pauses))
        total_weight = max(1, sum(len(txt) for txt, _ in clauses))
        cursor = start_s
        for idx, ((clause, _), pause_after) in enumerate(zip(clauses, eff_pauses)):
            if idx == len(clauses) - 1:
                cue_end = max(cursor + 0.15, end_s)
            else:
                span = speech_budget * (len(clause) / total_weight)
                cue_end = max(cursor + 0.15, cursor + span)
            cues.append((cursor, cue_end, clause))
            cursor = cue_end + pause_after
    blocks = []
    for idx, (st, ed, line) in enumerate(cues, 1):
        blocks.append(f"{idx}\n{_format_srt_ts(st)} --> {_format_srt_ts(ed)}\n{line}\n")
    return "\n".join(blocks)


def load_indextts2_class(project_dir: Path, *, allow_model_download: bool = False) -> Any:
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    if not allow_model_download:
        os.environ["HF_HUB_OFFLINE"] = "1"
    proj_str = str(Path(project_dir).resolve())
    if proj_str not in sys.path:
        sys.path.insert(0, proj_str)
    try:
        from indextts.infer_v2_5 import IndexTTS2
    except ImportError as exc:
        raise SynthesisError(
            f"Could not import IndexTTS2 from {proj_str}: {exc}. Use its configured environment."
        ) from exc
    return IndexTTS2


def _package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in (
        "indextts",
        "torch",
        "torchaudio",
        "transformers",
        "accelerate",
        "numpy",
        "soundfile",
        "huggingface-hub",
    ):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not_installed"
    return versions


def _publish_files(wav_src: Path, wav_dst: Path, rec_src: Path, rec_dst: Path) -> None:
    wav_moved = False
    try:
        os.replace(wav_src, wav_dst)
        wav_moved = True
        os.replace(rec_src, rec_dst)
    except OSError:
        if wav_moved and wav_dst.exists():
            wav_dst.unlink(missing_ok=True)
        raise


def synthesize_indextts2(
    *,
    text_file: Path,
    output_wav: Path,
    record_path: Path,
    confirmation_reference: str | None = None,
    project_dir: Path | None = None,
    reference_prompt: Path | None = None,
    checkpoints_dir: Path | None = None,
    cfg_path: Path | None = None,
    profile_path: Path = DEFAULT_PROFILE,
    baseline_path: Path | None = None,
    use_baseline: bool = True,
    lang: str | None = None,
    duration_factor: float | None = None,
    interval_silence: int | None = None,
    paragraph_silence_s: float | None = None,
    use_bf16: bool | None = None,
    use_cuda_kernel: bool | None = None,
    use_qwen_emo: bool | None = None,
    use_emo_text: bool | None = None,
    emo_alpha: float | None = None,
    seed: int | None = None,
    srt_out: Path | None = None,
    trim_edge_silence: bool = True,
    allow_model_download: bool = False,
) -> dict[str, Any]:
    text_file = Path(text_file).expanduser().resolve()
    output_wav = Path(output_wav).expanduser().resolve()
    record_path = Path(record_path).expanduser().resolve()
    profile_resolved = Path(profile_path).expanduser().resolve()

    if output_wav.suffix.lower() != ".wav":
        raise SynthesisError("Source narration output must be a .wav file.")
    for dest in (output_wav, record_path):
        if dest.exists() or dest.is_symlink():
            raise FileExistsError(f"Refusing to overwrite existing output: {dest}")
    if len({text_file, output_wav, record_path, profile_resolved}) != 4:
        raise SynthesisError("Input text, output WAV, record JSON and profile paths must be distinct.")
    if not text_file.is_file():
        raise SynthesisError(f"Input script file does not exist: {text_file}")

    raw_bytes = text_file.read_bytes()
    try:
        text = raw_bytes.decode("utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        raise SynthesisError("Input narration script must be valid UTF-8 text.") from exc
    if not text:
        raise SynthesisError("Input narration script is empty.")

    paragraphs = [p.strip() for p in text.replace("\r\n", "\n").split("\n\n") if p.strip()]
    if not paragraphs:
        raise SynthesisError("No speakable paragraphs found in input narration script.")

    defaults = load_profile_defaults(profile_resolved)
    baseline = resolve_baseline(baseline_path, use_baseline)
    base_exec = baseline.get("execution", {}) if isinstance(baseline.get("execution"), dict) else {}
    base_voice = baseline.get("voice", {}) if isinstance(baseline.get("voice"), dict) else {}
    base_prompt = base_voice.get("reference_prompt", {}) if isinstance(base_voice.get("reference_prompt"), dict) else {}
    base_load = baseline.get("load_parameters", {}) if isinstance(baseline.get("load_parameters"), dict) else {}
    base_gen = baseline.get("generation_params", {}) if isinstance(baseline.get("generation_params"), dict) else {}

    eff_project = project_dir if project_dir is not None else base_exec.get("location")
    eff_prompt = reference_prompt if reference_prompt is not None else base_prompt.get("file")
    eff_conf_ref = (
        confirmation_reference.strip()
        if isinstance(confirmation_reference, str) and confirmation_reference.strip()
        else base_exec.get("confirmation_reference")
    )

    if not eff_project or not str(eff_project).strip():
        raise SynthesisError(
            "Confirmed local IndexTTS-2.5 --project-dir (or voice-baseline.json execution.location) is required."
        )
    if not eff_prompt or not str(eff_prompt).strip():
        raise SynthesisError(
            "Private reference voice prompt (--reference-prompt or voice-baseline.json voice.reference_prompt.file) is required."
        )
    if not eff_conf_ref or not str(eff_conf_ref).strip():
        raise SynthesisError(
            "Explicit --confirmation-reference (or baseline execution.confirmation_reference) is required."
        )

    proj_dir = Path(str(eff_project)).expanduser().resolve()
    ref_prompt = Path(str(eff_prompt)).expanduser().resolve()
    if not proj_dir.is_dir():
        raise SynthesisError(f"Confirmed IndexTTS-2.5 project_dir does not exist: {proj_dir}")
    if not ref_prompt.is_file():
        raise SynthesisError(f"Reference voice prompt file does not exist: {ref_prompt}")

    eff_ckpt_dir_raw = checkpoints_dir if checkpoints_dir is not None else base_exec.get("checkpoints_dir")
    ckpt_dir = (
        Path(str(eff_ckpt_dir_raw)).expanduser().resolve()
        if eff_ckpt_dir_raw
        else (proj_dir / "checkpoints").resolve()
    )
    eff_cfg_raw = cfg_path if cfg_path is not None else base_exec.get("cfg_path")
    cfg_file = (
        Path(str(eff_cfg_raw)).expanduser().resolve()
        if eff_cfg_raw
        else (ckpt_dir / "config.yaml").resolve()
    )

    eff_lang = str(lang if lang is not None else base_gen.get("lang", defaults["lang"]))
    eff_duration_factor = float(
        duration_factor if duration_factor is not None else base_gen.get("duration_factor", defaults["duration_factor"])
    )
    eff_interval_silence = int(
        interval_silence if interval_silence is not None else base_gen.get("interval_silence", defaults["interval_silence"])
    )
    eff_para_silence = float(
        paragraph_silence_s
        if paragraph_silence_s is not None
        else base_gen.get("paragraph_silence_s", defaults["paragraph_silence_s"])
    )
    eff_use_bf16 = bool(use_bf16 if use_bf16 is not None else base_load.get("use_bf16", defaults["use_bf16"]))
    eff_use_cuda_kernel = bool(
        use_cuda_kernel if use_cuda_kernel is not None else base_load.get("use_cuda_kernel", defaults["use_cuda_kernel"])
    )
    eff_use_qwen_emo = bool(
        use_qwen_emo if use_qwen_emo is not None else base_load.get("use_qwen_emo", defaults["use_qwen_emo"])
    )
    eff_use_emo_text = bool(
        use_emo_text if use_emo_text is not None else base_gen.get("use_emo_text", defaults["use_emo_text"])
    )

    if eff_use_emo_text and not eff_use_qwen_emo:
        raise SynthesisError("use_emo_text=True requires use_qwen_emo=True.")
    if not math.isfinite(eff_duration_factor) or eff_duration_factor <= 0:
        raise SynthesisError("duration_factor must be a finite positive number.")
    if eff_interval_silence < 0:
        raise SynthesisError("interval_silence must be a non-negative integer.")
    if not math.isfinite(eff_para_silence) or eff_para_silence < 0:
        raise SynthesisError("paragraph_silence_s must be a finite non-negative number.")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32):
        raise SynthesisError("seed must be an integer in [0, 2^32 - 1].")

    validate_local_checkpoints(
        ckpt_dir,
        cfg_file,
        use_qwen_emo=eff_use_qwen_emo,
        allow_model_download=allow_model_download,
    )

    ref_sha = sha256_file(ref_prompt)
    try:
        ref_dur_s: float | None = round(probe_wav_info(ref_prompt)["duration_seconds"], 6)
    except SynthesisError:
        ref_dur_s = None

    commit = git_head_commit(proj_dir)
    ckpt_fp = checkpoints_fingerprint(ckpt_dir, cfg_file)
    srt_resolved = Path(srt_out).expanduser().resolve() if srt_out is not None else None

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    record_path.parent.mkdir(parents=True, exist_ok=True)

    temps: list[Path] = []
    with _SYNTHESIS_LOCK:
        prev_cwd = Path.cwd()
        try:
            with tempfile.TemporaryDirectory(prefix="indextts2-parts-") as part_tmp_str:
                part_tmp = Path(part_tmp_str)
                try:
                    os.chdir(proj_dir)
                    if seed is not None:
                        random.seed(seed)
                        if "torch" in sys.modules:
                            sys.modules["torch"].manual_seed(seed)
                    cls = load_indextts2_class(proj_dir, allow_model_download=allow_model_download)
                    tts = cls(
                        cfg_path=str(cfg_file),
                        model_dir=str(ckpt_dir),
                        use_bf16=eff_use_bf16,
                        use_cuda_kernel=eff_use_cuda_kernel,
                        use_qwen_emo=eff_use_qwen_emo,
                    )
                    part_paths: list[Path] = []
                    for idx, para in enumerate(paragraphs):
                        part_out = part_tmp / f"para_{idx:03d}.wav"
                        infer_kwargs: dict[str, Any] = {
                            "spk_audio_prompt": str(ref_prompt),
                            "text": para,
                            "output_path": str(part_out),
                            "lang": eff_lang,
                            "duration_factor": eff_duration_factor,
                            "interval_silence": eff_interval_silence,
                            "use_emo_text": eff_use_emo_text,
                            "verbose": False,
                        }
                        if eff_use_emo_text and emo_alpha is not None:
                            infer_kwargs["emo_alpha"] = float(emo_alpha)
                        tts.infer(**infer_kwargs)
                        if not part_out.is_file() or part_out.stat().st_size == 0:
                            raise SynthesisError(f"IndexTTS2 produced empty audio for paragraph {idx + 1}.")
                        part_paths.append(part_out)
                finally:
                    os.chdir(prev_cwd)

                wav_handle = tempfile.NamedTemporaryFile(
                    prefix=".indextts2-", suffix=".wav", dir=output_wav.parent, delete=False
                )
                wav_handle.close()
                wav_temp = Path(wav_handle.name)
                temps.append(wav_temp)

                rec_handle = tempfile.NamedTemporaryFile(
                    prefix=".indextts2-", suffix=".json", dir=record_path.parent, delete=False
                )
                rec_handle.close()
                rec_temp = Path(rec_handle.name)
                temps.append(rec_temp)

                timings = concat_wavs_with_silence(
                    part_paths,
                    wav_temp,
                    eff_para_silence,
                    trim_edge_silence=trim_edge_silence,
                )
                for para, row in zip(paragraphs, timings):
                    row["char_count"] = len(_strip_pinyin_markup(para))

                out_info = probe_wav_info(wav_temp)
                out_sha = sha256_file(wav_temp)

                if srt_resolved is not None:
                    srt_resolved.parent.mkdir(parents=True, exist_ok=True)
                    srt_resolved.write_text(
                        build_srt_from_paragraphs(
                            paragraphs,
                            timings,
                            interval_silence_ms=eff_interval_silence,
                        ),
                        encoding="utf-8",
                        newline="\n",
                    )

                ep_dir = record_path.parent

                def _rel(target: Path) -> str:
                    t_res = target.resolve()
                    try:
                        return t_res.relative_to(ep_dir).as_posix()
                    except ValueError:
                        return str(t_res)

                eff_gen_params: dict[str, Any] = {
                    "lang": eff_lang,
                    "duration_factor": eff_duration_factor,
                    "interval_silence": eff_interval_silence,
                    "paragraph_silence_s": eff_para_silence,
                    "trim_edge_silence": bool(trim_edge_silence),
                    "use_emo_text": eff_use_emo_text,
                }
                if eff_use_emo_text and emo_alpha is not None:
                    eff_gen_params["emo_alpha"] = float(emo_alpha)

                record: dict[str, Any] = {
                    "schema_version": 1,
                    "status": "generated",
                    "provider": "IndexTTS",
                    "backend": "local_indextts2",
                    "model_id": defaults["model_id"],
                    "model_version_reference": (
                        f"IndexTTS-2.5 local checkout ({commit or 'unversioned'}), "
                        f"checkpoints fingerprint {ckpt_fp[:12]}"
                    ),
                    "repo_commit": commit,
                    "checkpoints_fingerprint_sha256": ckpt_fp,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "execution": {
                        "status": "confirmed",
                        "mode": "local_project",
                        "location": str(proj_dir),
                        "confirmation_reference": str(eff_conf_ref),
                        "checkpoints_dir": str(ckpt_dir),
                        "python_executable": sys.executable,
                    },
                    "voice": {
                        "speaker": defaults["speaker"],
                        "voice_preset_id": defaults["voice_preset_id"],
                        "language": "Chinese",
                        "reference_prompt_file": str(ref_prompt),
                        "reference_prompt_sha256": ref_sha,
                        "reference_prompt_duration_s": ref_dur_s,
                    },
                    "load_parameters": {
                        "cfg_path": str(cfg_file),
                        "model_dir": str(ckpt_dir),
                        "use_bf16": eff_use_bf16,
                        "use_cuda_kernel": eff_use_cuda_kernel,
                        "use_qwen_emo": eff_use_qwen_emo,
                    },
                    "effective_generation_params": eff_gen_params,
                    "actual_device": str(getattr(tts, "device", "unknown")),
                    "seed": seed,
                    "environment": {
                        "python": platform.python_version(),
                        "platform": platform.platform(),
                        "package_versions": _package_versions(),
                    },
                    "implementation": {
                        "file": str(Path(__file__).resolve()),
                        "sha256": sha256_file(Path(__file__).resolve()),
                    },
                    "profile": {
                        "file": str(profile_resolved),
                        "sha256": sha256_file(profile_resolved),
                    },
                    "input": {
                        "file": _rel(text_file),
                        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
                        "encoding": "utf-8",
                        "text_transformation": "none",
                    },
                    "output": {
                        "file": _rel(output_wav),
                        "sha256": out_sha,
                        "format": "WAV",
                        "sample_rate": out_info["sample_rate"],
                        "channels": out_info["channels"],
                        "duration_seconds": round(out_info["duration_seconds"], 6),
                        "postprocess": "none",
                    },
                    "paragraph_timings": timings,
                    "listening": {
                        "status": "pending",
                        "scope": "source_voice_track",
                        "heard": False,
                    },
                }
                rec_temp.write_text(
                    json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
                _publish_files(wav_temp, output_wav, rec_temp, record_path)
                return record
        finally:
            for t in temps:
                t.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Synthesize continuous Mandarin voice-clone narration with local IndexTTS-2.5."
    )
    p.add_argument("--profile", type=Path, default=DEFAULT_PROFILE, help="Series profile JSON path.")
    p.add_argument("--baseline", type=Path, help="Optional private voice-baseline.json override.")
    p.add_argument(
        "--no-baseline",
        action="store_true",
        help="Ignore private voice-baseline.json and require explicit local execution arguments.",
    )
    p.add_argument("--text-file", type=Path, required=True, help="Complete UTF-8 narration script file.")
    p.add_argument("--output", type=Path, required=True, help="New raw WAV output path; never overwrites.")
    p.add_argument("--record", type=Path, required=True, help="New JSON generation record path.")
    p.add_argument("--confirmation-reference", help="Confirmation reference (defaults to baseline).")
    p.add_argument("--project-dir", type=Path, help="Local IndexTTS-2.5 checkout directory.")
    p.add_argument("--reference-prompt", type=Path, help="Private <=15 s reference WAV prompt.")
    p.add_argument("--checkpoints-dir", type=Path, help="IndexTTS-2.5 checkpoints directory.")
    p.add_argument("--cfg-path", type=Path, help="IndexTTS-2.5 config.yaml path.")
    p.add_argument("--lang", help="IndexTTS language code (default 'ZH').")
    p.add_argument("--duration-factor", type=float, help="Relative duration factor (default 1.0).")
    p.add_argument("--interval-silence", type=int, help="Intra-paragraph silence ms (default 220).")
    p.add_argument("--paragraph-silence", type=float, help="Inter-paragraph gap seconds (default 0.55).")
    p.add_argument("--bf16", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--cuda-kernel", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--qwen-emo", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--emo-text", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--emo-alpha", type=float)
    p.add_argument("--seed", type=int)
    p.add_argument("--srt-out", type=Path, help="Optional clause-aligned .srt output path.")
    p.add_argument(
        "--trim-edge-silence",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Trim excess per-paragraph leading/trailing silence (keeping ~30-40 ms breath margin) before joining.",
    )
    p.add_argument("--allow-model-download", action="store_true", help="Allow HF downloads if weights are missing.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rec = synthesize_indextts2(
            text_file=args.text_file,
            output_wav=args.output,
            record_path=args.record,
            confirmation_reference=args.confirmation_reference,
            project_dir=args.project_dir,
            reference_prompt=args.reference_prompt,
            checkpoints_dir=args.checkpoints_dir,
            cfg_path=args.cfg_path,
            profile_path=args.profile,
            baseline_path=args.baseline,
            use_baseline=not args.no_baseline,
            lang=args.lang,
            duration_factor=args.duration_factor,
            interval_silence=args.interval_silence,
            paragraph_silence_s=args.paragraph_silence,
            use_bf16=args.bf16,
            use_cuda_kernel=args.cuda_kernel,
            use_qwen_emo=args.qwen_emo,
            use_emo_text=args.emo_text,
            emo_alpha=args.emo_alpha,
            seed=args.seed,
            srt_out=args.srt_out,
            trim_edge_silence=args.trim_edge_silence,
            allow_model_download=args.allow_model_download,
        )
    except Exception as exc:
        msg = str(exc) if isinstance(exc, (SynthesisError, FileExistsError, ValueError)) else type(exc).__name__
        print(json.dumps({"status": "failed", "error": msg}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": rec["status"],
                "voice": {
                    "speaker": rec["voice"]["speaker"],
                    "voice_preset_id": rec["voice"]["voice_preset_id"],
                    "reference_prompt_sha256": rec["voice"]["reference_prompt_sha256"],
                },
                "output": rec["output"],
                "record": str(Path(args.record).resolve()),
                "listening": "pending",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
