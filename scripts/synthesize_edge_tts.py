#!/usr/bin/env python3
"""Default series cloud neural TTS adapter using Microsoft Edge edge-tts.

Synthesizes whole-episode continuous narration using the series default
``zh-CN-YunxiNeural`` at ``+4%`` (or the paired English neural voice for
bilingual editions), decodes to 48 kHz FLOAT32 WAV for ``prepare_voice_master.py``,
records neural sentence/word boundary timestamps, and writes a hash-bound
generation record compatible with ``check_episode.py``.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

EDGE_TTS_ENDPOINT = "https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1"
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = SKILL_ROOT / "config" / "series-profile.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _format_srt_ts(seconds: float) -> str:
    ms_total = max(0, int(round(seconds * 1000)))
    hrs, rem = divmod(ms_total, 3_600_000)
    mins, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"


def _split_zh_clauses(sentence: str, max_chars: int = 22) -> list[str]:
    cleaned = re.sub(r"\s+", "", sentence.strip())
    if not cleaned:
        return []
    raw_parts = [p.strip("，、。！？；：") for p in re.split(r"[，、。！？；：]+", cleaned) if p.strip("，、。！？；：")]
    merged: list[str] = []
    for part in raw_parts:
        if merged and len(merged[-1]) + 1 + len(part) <= max_chars:
            merged[-1] = f"{merged[-1]}，{part}"
        else:
            merged.append(part)
    return merged or [cleaned]


def _split_en_clauses(sentence: str, max_words: int = 12) -> list[str]:
    words = sentence.strip().split()
    if not words:
        return []
    if len(words) <= max_words:
        return [" ".join(words)]
    chunks: list[str] = []
    cur: list[str] = []
    for w in words:
        cur.append(w)
        if len(cur) >= max_words or (len(cur) >= 6 and w.endswith((",", ";", ":", "."))):
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        if chunks and len(cur) <= 3:
            chunks[-1] = f"{chunks[-1]} {' '.join(cur)}"
        else:
            chunks.append(" ".join(cur))
    return chunks


def build_srt_from_boundaries(boundaries: list[dict[str, Any]], language: str) -> str:
    cues: list[tuple[float, float, str]] = []
    is_zh = language.lower().startswith(("zh", "chinese"))
    for b in boundaries:
        start_s = float(b["offset_s"])
        dur_s = max(0.25, float(b["duration_s"]))
        end_s = start_s + dur_s
        txt = str(b.get("text") or "").strip()
        if not txt:
            continue
        clauses = _split_zh_clauses(txt) if is_zh else _split_en_clauses(txt)
        total_weight = max(1, sum(len(c) for c in clauses))
        cursor = start_s
        for idx, clause in enumerate(clauses):
            span = (end_s - cursor) if idx == len(clauses) - 1 else dur_s * (len(clause) / total_weight)
            cues.append((cursor, cursor + max(0.2, span), clause))
            cursor += span
    blocks = []
    for idx, (st, ed, line) in enumerate(cues, 1):
        blocks.append(f"{idx}\n{_format_srt_ts(st)} --> {_format_srt_ts(ed)}\n{line}\n")
    return "\n".join(blocks)


async def _stream_edge_tts(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    volume: str,
    mp3_path: Path,
) -> list[dict[str, Any]]:
    import edge_tts

    comm = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
        volume=volume,
        boundary="SentenceBoundary",
    )
    boundaries: list[dict[str, Any]] = []
    with mp3_path.open("wb") as fh:
        async for chunk in comm.stream():
            ctype = chunk.get("type")
            if ctype == "audio":
                fh.write(chunk["data"])
            elif ctype in ("SentenceBoundary", "WordBoundary"):
                boundaries.append(
                    {
                        "type": ctype,
                        "offset_s": round(chunk["offset"] / 10_000_000.0, 4),
                        "duration_s": round(chunk["duration"] / 10_000_000.0, 4),
                        "text": chunk.get("text", ""),
                    }
                )
    return boundaries


def load_profile_defaults(profile_path: Path) -> dict[str, Any]:
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    audio = data.get("audio", {})
    edge_cfg = audio.get("edge_fallback") if isinstance(audio.get("edge_fallback"), dict) else audio
    return {
        "speaker": edge_cfg.get("speaker", "zh-CN-YunxiNeural"),
        "en_speaker": edge_cfg.get("en_speaker", audio.get("en_speaker", "en-US-AndrewMultilingualNeural")),
        "rate": edge_cfg.get("rate", audio.get("rate", "+4%")),
        "pitch": edge_cfg.get("pitch", audio.get("pitch", "+0Hz")),
        "volume": edge_cfg.get("volume", audio.get("volume", "+0%")),
    }


def synthesize_edge(
    *,
    text_file: Path,
    output_wav: Path,
    record_path: Path,
    confirmation_reference: str,
    profile_path: Path = DEFAULT_PROFILE,
    language: str = "Chinese",
    voice: str | None = None,
    rate: str | None = None,
    pitch: str | None = None,
    volume: str | None = None,
    srt_out: Path | None = None,
    boundaries_out: Path | None = None,
    ffmpeg_bin: str = "ffmpeg",
) -> dict[str, Any]:
    for p in (output_wav, record_path):
        if p.exists():
            raise FileExistsError(f"Refusing to overwrite existing output: {p}")
    raw_bytes = text_file.read_bytes()
    text = raw_bytes.decode("utf-8").strip()
    if not text:
        raise ValueError("Input script text is empty.")

    defaults = load_profile_defaults(profile_path)
    is_en = language.lower().startswith(("en", "english"))
    norm_lang = "English" if is_en else "Chinese"
    eff_voice = voice or (defaults["en_speaker"] if is_en else defaults["speaker"])
    eff_rate = rate if rate is not None else defaults["rate"]
    eff_pitch = pitch if pitch is not None else defaults["pitch"]
    eff_volume = volume if volume is not None else defaults["volume"]

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    mp3_path = output_wav.with_suffix(".raw.mp3")
    b_path = boundaries_out or output_wav.with_suffix(".boundaries.json")

    boundaries = asyncio.run(_stream_edge_tts(text, eff_voice, eff_rate, eff_pitch, eff_volume, mp3_path))
    if not mp3_path.is_file() or mp3_path.stat().st_size == 0:
        raise RuntimeError("edge-tts produced an empty audio stream.")

    proc = subprocess.run(
        [
            ffmpeg_bin,
            "-v",
            "error",
            "-y",
            "-i",
            str(mp3_path),
            "-ac",
            "1",
            "-ar",
            "48000",
            "-c:a",
            "pcm_f32le",
            str(output_wav),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0 or not output_wav.is_file():
        raise RuntimeError(f"ffmpeg decode to 48kHz pcm_f32le WAV failed: {proc.stderr.strip()}")

    try:
        pkg_ver = importlib.metadata.version("edge-tts")
    except importlib.metadata.PackageNotFoundError:
        pkg_ver = "unknown"

    b_payload = {
        "schema_version": 1,
        "provider": "Microsoft Edge",
        "backend": "edge-tts",
        "edge_tts_version": pkg_ver,
        "endpoint": EDGE_TTS_ENDPOINT,
        "voice": eff_voice,
        "language": norm_lang,
        "rate": eff_rate,
        "pitch": eff_pitch,
        "volume": eff_volume,
        "raw_mp3_sha256": sha256_file(mp3_path),
        "boundaries": boundaries,
    }
    b_path.parent.mkdir(parents=True, exist_ok=True)
    b_path.write_text(json.dumps(b_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    if srt_out is not None and boundaries:
        srt_out.parent.mkdir(parents=True, exist_ok=True)
        srt_out.write_text(build_srt_from_boundaries(boundaries, norm_lang), encoding="utf-8", newline="\n")

    ep_dir = record_path.parent.resolve()

    def _rel(target: Path) -> str:
        t_res = target.resolve()
        try:
            return t_res.relative_to(ep_dir).as_posix()
        except ValueError:
            return str(t_res)

    record = {
        "schema_version": 1,
        "status": "generated",
        "provider": "Microsoft Edge",
        "backend": "edge-tts",
        "model_id": "edge-tts",
        "model_version_reference": f"edge-tts {pkg_ver} cloud neural service ({eff_voice}); weights hosted by Microsoft Edge ReadAloud",
        "execution": {
            "status": "confirmed",
            "mode": "service",
            "location": EDGE_TTS_ENDPOINT,
            "confirmation_reference": confirmation_reference,
        },
        "voice": {
            "speaker": eff_voice,
            "language": norm_lang,
            "rate": eff_rate,
            "pitch": eff_pitch,
            "volume": eff_volume,
        },
        "runtime_parameters": {
            "endpoint": EDGE_TTS_ENDPOINT,
            "edge_tts_version": pkg_ver,
            "boundary": "SentenceBoundary",
            "decode_format": "pcm_f32le_48000hz_mono",
        },
        "effective_generation_params": {
            "rate": eff_rate,
            "pitch": eff_pitch,
            "volume": eff_volume,
        },
        "cloud_evidence": {
            "file": _rel(b_path),
            "sha256": sha256_file(b_path),
        },
        "input": {
            "file": _rel(text_file),
            "sha256": sha256_file(text_file),
            "text_transformation": "none",
        },
        "output": {
            "file": _rel(output_wav),
            "sha256": sha256_file(output_wav),
        },
        "listening": {"status": "pending", "scope": "source_voice_track", "heard": False},
    }
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return record


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Synthesize continuous narration with Microsoft Edge edge-tts.")
    p.add_argument("--profile", type=Path, default=DEFAULT_PROFILE, help="Series profile JSON path.")
    p.add_argument("--text-file", type=Path, required=True, help="Complete UTF-8 narration script file.")
    p.add_argument("--output", type=Path, required=True, help="Output 48kHz FLOAT32 WAV path.")
    p.add_argument("--record", type=Path, required=True, help="Output JSON generation record path.")
    p.add_argument("--confirmation-reference", required=True, help="Commission or series default reference.")
    p.add_argument("--language", default="Chinese", choices=("Chinese", "English", "zh", "en"))
    p.add_argument("--voice", help="Override neural voice name (defaults to series-profile speaker / en_speaker).")
    p.add_argument("--rate", help="Override rate (defaults to series-profile rate '+4%').")
    p.add_argument("--pitch", help="Override pitch (defaults to '+0Hz').")
    p.add_argument("--volume", help="Override volume (defaults to '+0%').")
    p.add_argument("--srt-out", type=Path, help="Optional neural-aligned .srt output path.")
    p.add_argument("--boundaries-out", type=Path, help="Optional boundary metadata JSON path.")
    p.add_argument("--ffmpeg", default="ffmpeg", help="FFmpeg binary path.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rec = synthesize_edge(
            text_file=args.text_file,
            output_wav=args.output,
            record_path=args.record,
            confirmation_reference=args.confirmation_reference,
            profile_path=args.profile,
            language=args.language,
            voice=args.voice,
            rate=args.rate,
            pitch=args.pitch,
            volume=args.volume,
            srt_out=args.srt_out,
            boundaries_out=args.boundaries_out,
            ffmpeg_bin=args.ffmpeg,
        )
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({"status": rec["status"], "voice": rec["voice"], "output": rec["output"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
