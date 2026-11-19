#!/usr/bin/env python3
"""Screening audit for Google Flow cloud video source clips and bilingual exports."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SKILL_ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = SKILL_ROOT / "config" / "production-policy.json"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
SRT_TIME_RE = re.compile(
    r"^\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")
LEAKED_MARKUP_RE = re.compile(r"</?(?:speak|break|phoneme|prosody|say-as|sub)\b", re.IGNORECASE)
PROMPT_COLON_RE = re.compile(
    r"(?:^|[\n。！？])\s*(?:第[一二三四五六七八九十\d]+[步点条层关][^，。！？\n]{0,8}|"
    r"先打破一个常识误区|一句话总结|核心在于|关键在于|原因如下|说白了)[：:，,]"
)
CLICKBAIT_HOOK_RE = re.compile(
    r"(?:竟能?[^，。！？\n]{1,12}[，,][^，。！？\n]{0,14}怎么(?:做到的|回事)|"
    r"明明[^，。！？\n]{1,10}却[^，。！？\n]{1,10}[，,][^，。！？\n]{0,14}怎么(?:做到的|回事))"
)
STRAWMAN_REVERSAL_RE = re.compile(
    r"(?:不是[^，。！？\n]{1,16}[，,]?而是|并非[^，。！？\n]{1,16}[，,]?而是|"
    r"你以为[^，。！？\n]{1,16}[，,]?其实|看似[^，。！？\n]{1,16}[，,]?实则)"
)
SLOGAN_CLOSING_RE = re.compile(
    r"(?:只有[^，。！？\n]{1,14}配[^，。！？\n]{1,14}[，,]才|正是[^，。！？\n]{1,20}造就了)"
)
PCT_RATE_RE = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*%\s*$")


def load_policy() -> dict[str, Any]:
    with POLICY_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    audit = data.get("google_flow_audit")
    if not isinstance(audit, dict):
        raise RuntimeError("Missing google_flow_audit section in config/production-policy.json")
    return audit


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_rate(rate_str: str | None) -> float | None:
    if not rate_str or rate_str in {"0/0", "N/A"}:
        return None
    if "/" in rate_str:
        num_s, den_s = rate_str.split("/", 1)
        try:
            num, den = float(num_s), float(den_s)
        except ValueError:
            return None
        return num / den if den != 0 else None
    try:
        return float(rate_str)
    except ValueError:
        return None


def ffprobe_media(path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {proc.stderr.strip()}")
    raw = json.loads(proc.stdout or "{}")
    streams = raw.get("streams", [])
    fmt = raw.get("format", {})
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    avg_fps = parse_rate(v_stream.get("avg_frame_rate")) if v_stream else None
    r_fps = parse_rate(v_stream.get("r_frame_rate")) if v_stream else None
    dur = None
    for candidate in (
        v_stream.get("duration") if v_stream else None,
        fmt.get("duration"),
        a_stream.get("duration") if a_stream else None,
    ):
        if candidate is not None:
            try:
                dur = float(candidate)
                break
            except (TypeError, ValueError):
                pass
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "has_video": v_stream is not None,
        "has_audio": a_stream is not None,
        "width": int(v_stream["width"]) if v_stream and v_stream.get("width") else None,
        "height": int(v_stream["height"]) if v_stream and v_stream.get("height") else None,
        "avg_fps": round(avg_fps, 4) if avg_fps is not None else None,
        "r_fps": round(r_fps, 4) if r_fps is not None else None,
        "duration_s": round(dur, 4) if dur is not None else None,
        "video_codec": v_stream.get("codec_name") if v_stream else None,
        "audio_codec": a_stream.get("codec_name") if a_stream else None,
        "audio_sample_rate": int(a_stream["sample_rate"]) if a_stream and a_stream.get("sample_rate") else None,
    }


def _srt_to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_srt(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\r?\n\s*\r?\n", text.strip())
    cues: list[dict[str, Any]] = []
    for block in blocks:
        lines = [ln.rstrip("\r") for ln in block.splitlines() if ln.strip() != ""]
        if not lines:
            continue
        time_idx = 0
        if not SRT_TIME_RE.match(lines[0]) and len(lines) > 1 and SRT_TIME_RE.match(lines[1]):
            time_idx = 1
        m = SRT_TIME_RE.match(lines[time_idx])
        if not m:
            continue
        start_s = _srt_to_seconds(*m.groups()[:4])
        end_s = _srt_to_seconds(*m.groups()[4:])
        cue_lines = lines[time_idx + 1 :]
        cues.append({"start_s": start_s, "end_s": end_s, "lines": cue_lines, "text": "\n".join(cue_lines)})
    return cues


def parse_ass_metadata(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig")
    wrap_style = None
    font_sizes: list[float] = []
    cues: list[dict[str, Any]] = []
    section = ""
    style_fields: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        if section == "script info" and line.lower().startswith("wrapstyle:"):
            try:
                wrap_style = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif section.startswith("v4") and line.startswith("Format:"):
            style_fields = [f.strip().lower() for f in line.split(":", 1)[1].split(",")]
        elif section.startswith("v4") and line.startswith("Style:") and style_fields:
            vals = [v.strip() for v in line.split(":", 1)[1].split(",")]
            if "fontsize" in style_fields:
                idx = style_fields.index("fontsize")
                if idx < len(vals):
                    try:
                        font_sizes.append(float(vals[idx]))
                    except ValueError:
                        pass
        elif section == "events" and line.startswith("Dialogue:"):
            parts = line.split(":", 1)[1].split(",", 9)
            if len(parts) >= 10:
                start_s = _ass_time_to_seconds(parts[1].strip())
                end_s = _ass_time_to_seconds(parts[2].strip())
                raw_txt = re.sub(r"\{[^}]*\}", "", parts[9]).replace("\\N", "\n").replace("\\n", "\n")
                if start_s is not None and end_s is not None:
                    cues.append(
                        {
                            "start_s": start_s,
                            "end_s": end_s,
                            "lines": raw_txt.splitlines() or [""],
                            "text": raw_txt,
                        }
                    )
    return {"wrap_style": wrap_style, "font_sizes": font_sizes, "cues": cues}


def _ass_time_to_seconds(stamp: str) -> float | None:
    m = re.match(r"^(\d+):(\d{2}):(\d{2})\.(\d{2,3})$", stamp)
    if not m:
        return None
    h, mn, sec, frac = m.groups()
    denom = 100.0 if len(frac) == 2 else 1000.0
    return int(h) * 3600 + int(mn) * 60 + int(sec) + int(frac) / denom


def _resolve_path(base_dir: Path, raw_path: str | Path) -> Path:
    p = Path(raw_path)
    return p if p.is_absolute() else (base_dir / p).resolve()


def _extract_shot_id(shot: dict[str, Any], index: int) -> str:
    return str(shot.get("shot_id") or shot.get("id") or f"SHOT_{index + 1:02d}")


def _extract_shot_duration(shot: dict[str, Any]) -> float | None:
    for key in ("actual_duration_s", "duration_s", "edit_duration_s", "target_duration_s"):
        val = shot.get(key)
        if isinstance(val, (int, float)) and val > 0:
            return float(val)
    start, end = shot.get("start_s"), shot.get("end_s")
    if isinstance(start, (int, float)) and isinstance(end, (int, float)) and end > start:
        return float(end - start)
    nar = shot.get("narration_duration_s")
    hold = shot.get("observation_hold_s", shot.get("hold_s", 0.0))
    if isinstance(nar, (int, float)) and nar > 0:
        return float(nar) + (float(hold) if isinstance(hold, (int, float)) else 0.0)
    return None


def _extract_observation_hold(shot: dict[str, Any]) -> float | None:
    for key in ("observation_hold_s", "hold_s", "pause_after_s", "tail_hold_s"):
        val = shot.get(key)
        if isinstance(val, (int, float)):
            return float(val)
    dur = _extract_shot_duration(shot)
    nar_dur = shot.get("narration_duration_s")
    if dur is not None and isinstance(nar_dur, (int, float)) and dur >= nar_dur:
        return float(dur - nar_dur)
    return None


def _collect_episode_clips(
    episode: dict[str, Any] | None,
    episode_dir: Path | None,
    clips_dir: Path | None,
    clips_manifest: dict[str, Any] | None,
) -> tuple[dict[str, list[Path]], list[tuple[str, Path]]]:
    """Return mapping of shot_id -> list of declared/discovered clip Paths and missing entries."""
    by_shot: dict[str, list[Path]] = {}
    missing: list[tuple[str, Path]] = []

    if isinstance(clips_manifest, dict):
        items = clips_manifest.get("clips") if isinstance(clips_manifest.get("clips"), list) else None
        base = clips_dir or episode_dir or Path.cwd()
        if items is not None:
            for item in items:
                if isinstance(item, dict) and item.get("shot_id") and item.get("file"):
                    sid = str(item["shot_id"])
                    p = _resolve_path(base, item["file"])
                    if p.is_file():
                        by_shot.setdefault(sid, []).append(p)
                    else:
                        missing.append((sid, p))
        else:
            for sid, rel in clips_manifest.items():
                if isinstance(rel, str):
                    p = _resolve_path(base, rel)
                    if p.is_file():
                        by_shot.setdefault(str(sid), []).append(p)
                    else:
                        missing.append((str(sid), p))
    elif isinstance(clips_manifest, list):
        base = clips_dir or episode_dir or Path.cwd()
        for item in clips_manifest:
            if isinstance(item, dict) and item.get("shot_id") and item.get("file"):
                sid = str(item["shot_id"])
                p = _resolve_path(base, item["file"])
                if p.is_file():
                    by_shot.setdefault(sid, []).append(p)
                else:
                    missing.append((sid, p))

    if episode and episode_dir:
        assets_by_id: dict[str, Path] = {}
        for asset in episode.get("assets", []):
            if not isinstance(asset, dict):
                continue
            aid = str(asset.get("id") or "")
            raw_file = asset.get("file") or asset.get("path")
            if aid and isinstance(raw_file, str):
                p = _resolve_path(episode_dir, raw_file)
                if p.suffix.lower() in VIDEO_EXTENSIONS or asset.get("kind") == "video" or asset.get("type") == "video":
                    assets_by_id[aid] = p

        for idx, shot in enumerate(episode.get("shots", [])):
            if not isinstance(shot, dict):
                continue
            sid = _extract_shot_id(shot, idx)
            if sid in by_shot:
                continue
            declared_paths: list[Path] = []
            for key in ("clip", "source_clip", "video_path", "file"):
                raw_val = shot.get(key)
                if isinstance(raw_val, str) and raw_val.strip():
                    declared_paths.append(_resolve_path(episode_dir, raw_val))
            for aid in shot.get("asset_ids", []):
                if str(aid) in assets_by_id:
                    declared_paths.append(assets_by_id[str(aid)])
            for p in declared_paths:
                if p.is_file():
                    by_shot.setdefault(sid, []).append(p)
                else:
                    missing.append((sid, p))

    if clips_dir and clips_dir.is_dir():
        video_files = sorted(p for p in clips_dir.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS)
        if episode and isinstance(episode.get("shots"), list):
            for idx, shot in enumerate(episode["shots"]):
                if not isinstance(shot, dict):
                    continue
                sid = _extract_shot_id(shot, idx)
                if sid in by_shot or any(m_sid == sid for m_sid, _ in missing):
                    continue
                sid_low = sid.lower()
                matches = [
                    vf
                    for vf in video_files
                    if vf.stem.lower() == sid_low
                    or vf.stem.lower().startswith(f"{sid_low}_")
                    or vf.stem.lower().startswith(f"{sid_low}-")
                ]
                if matches:
                    by_shot[sid] = matches
                else:
                    missing.append((sid, clips_dir / f"{sid}.mp4"))
        elif not by_shot:
            for vf in video_files:
                by_shot[vf.stem] = [vf]

    return by_shot, missing


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _extract_episode_text(episode: dict[str, Any] | None, cues: list[dict[str, Any]]) -> str:
    if episode:
        nar = episode.get("narration")
        if isinstance(nar, dict):
            for key in ("spoken_text", "text", "script"):
                val = nar.get(key)
                if isinstance(val, str) and val.strip():
                    return val
        elif isinstance(nar, str) and nar.strip():
            return nar
        shot_texts = []
        for s in episode.get("shots", []):
            if isinstance(s, dict):
                t = s.get("spoken_text") or s.get("narration") or s.get("caption_text")
                if isinstance(t, str) and t.strip():
                    shot_texts.append(t.strip())
        if shot_texts:
            return "\n".join(shot_texts)
    return "\n".join(c["text"] for c in cues if c.get("text"))


def _check_captions(
    edition: str,
    cap_path: Path | None,
    episode: dict[str, Any] | None,
    video_dur_s: float | None,
    policy: dict[str, Any],
    flags: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    if cap_path is None and episode:
        caps_obj = episode.get("captions")
        if isinstance(caps_obj, dict) and isinstance(caps_obj.get("file"), str):
            base = episode.get("_dir")
            if isinstance(base, Path):
                cand = _resolve_path(base, caps_obj["file"])
                if cand.is_file():
                    cap_path = cand
    if cap_path is None:
        return [], None
    if not cap_path.is_file():
        flags.append(
            {
                "code": "caption_sync_or_wrap_issue",
                "edition": edition,
                "detail": f"Missing caption file: {cap_path}",
            }
        )
        return [], None

    wrap_meta = policy.get("caption", {})
    max_sync_offset = float(wrap_meta.get("max_sync_offset_s", 0.35))
    ass_info: dict[str, Any] | None = None
    if cap_path.suffix.lower() == ".ass":
        ass_info = parse_ass_metadata(cap_path)
        cues = ass_info["cues"]
        expected_wrap = wrap_meta["zh_wrap_style"] if edition == "zh" else wrap_meta["en_wrap_style"]
        if ass_info["wrap_style"] is not None and ass_info["wrap_style"] != expected_wrap:
            flags.append(
                {
                    "code": "caption_sync_or_wrap_issue",
                    "edition": edition,
                    "detail": f"ASS WrapStyle={ass_info['wrap_style']} != expected {expected_wrap} for {edition}",
                }
            )
        if edition == "zh" and ass_info["font_sizes"]:
            min_fs = float(wrap_meta.get("min_zh_font_size", 20))
            if min(ass_info["font_sizes"]) < min_fs:
                flags.append(
                    {
                        "code": "caption_sync_or_wrap_issue",
                        "edition": edition,
                        "detail": f"ASS zh Fontsize {min(ass_info['font_sizes'])} < {min_fs}",
                    }
                )
    else:
        cues = parse_srt(cap_path)

    if episode and isinstance(episode.get("captions"), dict):
        cap_cfg = episode["captions"]
        expected_wrap = wrap_meta["zh_wrap_style"] if edition == "zh" else wrap_meta["en_wrap_style"]
        if cap_cfg.get("wrap_style") is not None and cap_cfg.get("wrap_style") != expected_wrap:
            flags.append(
                {
                    "code": "caption_sync_or_wrap_issue",
                    "edition": edition,
                    "detail": f"Episode captions.wrap_style={cap_cfg['wrap_style']} != expected {expected_wrap}",
                }
            )
        if edition == "zh" and isinstance(cap_cfg.get("font_size"), (int, float)):
            min_fs = float(wrap_meta.get("min_zh_font_size", 20))
            if float(cap_cfg["font_size"]) < min_fs:
                flags.append(
                    {
                        "code": "caption_sync_or_wrap_issue",
                        "edition": edition,
                        "detail": f"Episode captions.font_size={cap_cfg['font_size']} < {min_fs}",
                    }
                )

    if not cues:
        flags.append(
            {
                "code": "caption_sync_or_wrap_issue",
                "edition": edition,
                "detail": f"No parsed caption cues in {cap_path.name}",
            }
        )
        return [], {"path": str(cap_path), "cue_count": 0}

    prev_end = -1.0
    for idx, cue in enumerate(cues):
        if cue["end_s"] <= cue["start_s"] or cue["start_s"] < 0:
            flags.append(
                {
                    "code": "caption_sync_or_wrap_issue",
                    "edition": edition,
                    "cue_index": idx + 1,
                    "detail": f"Invalid cue timestamps {cue['start_s']:.2f}->{cue['end_s']:.2f}",
                }
            )
            break
        if prev_end > cue["start_s"] + 0.05:
            flags.append(
                {
                    "code": "caption_sync_or_wrap_issue",
                    "edition": edition,
                    "cue_index": idx + 1,
                    "detail": f"Overlapping cue start {cue['start_s']:.2f} < previous end {prev_end:.2f}",
                }
            )
            break
        if LEAKED_MARKUP_RE.search(cue["text"]):
            flags.append(
                {
                    "code": "caption_sync_or_wrap_issue",
                    "edition": edition,
                    "cue_index": idx + 1,
                    "detail": "Leaked SSML/markup tag inside subtitle text",
                }
            )
            break
        prev_end = cue["end_s"]

    if video_dur_s is not None and cues[-1]["end_s"] > video_dur_s + max_sync_offset:
        flags.append(
            {
                "code": "caption_sync_or_wrap_issue",
                "edition": edition,
                "detail": f"Last caption ends at {cues[-1]['end_s']:.2f}s past video end {video_dur_s:.2f}s",
            }
        )

    summary = {"path": str(cap_path), "cue_count": len(cues), "last_end_s": round(cues[-1]["end_s"], 3)}
    if ass_info:
        summary["wrap_style"] = ass_info["wrap_style"]
    return cues, summary


def _is_google_flow_url(location: Any) -> bool:
    if not isinstance(location, str) or not location.strip():
        return False
    try:
        parsed = urlparse(location.strip())
    except ValueError:
        return False
    if parsed.scheme != "https" or parsed.username:
        return False
    return parsed.hostname in (
        "speech.platform.bing.com",
        "flow.google.com",
        "aistudio.google.com",
        "generativelanguage.googleapis.com",
    ) or (
        parsed.hostname == "labs.google" and parsed.path.startswith(("/fx/tools/flow", "/flow"))
    )


def _is_google_flow_tool(tool_val: Any) -> bool:
    if not isinstance(tool_val, str) or not tool_val.strip():
        return False
    raw = tool_val.strip()
    low = raw.lower()
    if any(bad in low for bad in ("synthesize_voice", "qwen", "os_tts")):
        return False
    stem = Path(raw.replace("\\", "/")).stem.lower()
    if low in (
        "indextts2",
        "synthesize_indextts2",
        "synthesize_indextts2.py",
        "scripts/synthesize_indextts2.py",
        "edge-tts",
        "synthesize_edge_tts",
        "synthesize_edge_tts.py",
        "scripts/synthesize_edge_tts.py",
        "google_flow",
        "google flow",
        "google_ai_studio",
        "google ai studio",
        "gemini_tts",
        "ffmpeg",
        "prepare_voice_master",
        "prepare_voice_master.py",
        "scripts/prepare_voice_master.py",
    ) or stem in ("indextts2", "synthesize_indextts2", "edge-tts", "synthesize_edge_tts", "ffmpeg", "prepare_voice_master"):
        return True
    return _is_google_flow_url(raw)


def _check_flow_origin_purity(
    episode: dict[str, Any] | None,
    edition: str,
    flags: list[dict[str, Any]],
) -> None:
    """Flag local TTS workarounds (e.g. Qwen/OS TTS) or forbidden gap workarounds."""
    if not isinstance(episode, dict):
        return
    reasons: list[str] = []
    design = episode.get("design") if isinstance(episode.get("design"), dict) else {}
    if design.get("flow_postproduction_gaps"):
        reasons.append("flow_postproduction_gaps_forbidden")
    nar = episode.get("narration") if isinstance(episode.get("narration"), dict) else {}
    exc = nar.get("execution") if isinstance(nar.get("execution"), dict) else {}
    ep_dir = episode.get("_dir")
    gen_data: dict[str, Any] | None = None
    if isinstance(ep_dir, Path):
        gen_ref = nar.get("generation_record")
        if isinstance(gen_ref, dict) and isinstance(gen_ref.get("file"), str) and gen_ref["file"].strip():
            gen_path = _resolve_path(ep_dir, gen_ref["file"])
            if gen_path.is_file():
                try:
                    loaded = _load_json(gen_path)
                    if isinstance(loaded, dict):
                        gen_data = loaded
                except (OSError, ValueError):
                    pass
    is_indextts2_zh = (
        edition == "zh"
        and isinstance(gen_data, dict)
        and gen_data.get("provider") == "IndexTTS"
        and gen_data.get("backend") == "local_indextts2"
    )
    if exc:
        mode = exc.get("mode")
        loc = exc.get("location")
        if is_indextts2_zh:
            if mode != "local_project":
                reasons.append(f"execution_mode:{mode}")
            if not (isinstance(loc, str) and loc.strip()):
                reasons.append("non_flow_execution_location")
        else:
            if mode and mode != "service":
                reasons.append(f"execution_mode:{mode}")
            if isinstance(loc, str) and loc.strip() and not _is_google_flow_url(loc):
                reasons.append("non_flow_execution_location")
    if isinstance(gen_data, dict) and not is_indextts2_zh:
        prov = gen_data.get("provider")
        if isinstance(prov, str) and prov.strip() and prov not in (
            "Microsoft Edge",
            "Google Flow",
            "Google AI Studio",
            "Google",
        ):
            reasons.append(f"non_flow_provider:{prov}")
        bk = gen_data.get("backend")
        if isinstance(bk, str) and any(t in bk.lower() for t in ("local", "qwen", "os_tts")):
            reasons.append(f"non_flow_backend:{bk}")
    if isinstance(ep_dir, Path):
        post_ref = nar.get("postprocess_record")
        if isinstance(post_ref, dict) and isinstance(post_ref.get("file"), str) and post_ref["file"].strip():
            post_path = _resolve_path(ep_dir, post_ref["file"])
            if post_path.is_file():
                try:
                    post_data = _load_json(post_path)
                    steps = post_data.get("steps") if isinstance(post_data, dict) else None
                    if isinstance(steps, list):
                        for step in steps:
                            if isinstance(step, dict) and step.get("tool") is not None and not _is_google_flow_tool(step.get("tool")):
                                reasons.append(f"local_postprocess_tool:{step.get('tool')}")
                except (OSError, ValueError):
                    pass
    if reasons:
        flags.append(
            {
                "code": "non_flow_voice_or_local_resource",
                "edition": edition,
                "reasons": reasons,
            }
        )


def _check_speech_and_holds(
    edition: str,
    episode: dict[str, Any] | None,
    cues: list[dict[str, Any]],
    total_dur_s: float | None,
    policy: dict[str, Any],
    flags: list[dict[str, Any]],
) -> dict[str, Any]:
    speech_cfg = policy.get("speech", {})
    text = _extract_episode_text(episode, cues)
    dur_s = total_dur_s
    if dur_s is None and episode and isinstance(episode.get("shots"), list):
        shot_durs = [d for s in episode["shots"] if isinstance(s, dict) and (d := _extract_shot_duration(s))]
        if shot_durs:
            dur_s = sum(shot_durs)

    rate_val = None
    active_dur_s = dur_s
    if len(cues) >= 1:
        cue_span = sum(max(0.0, c["end_s"] - c["start_s"]) for c in cues)
        if cue_span > 0.5 and (dur_s is None or cue_span <= dur_s + 0.5):
            active_dur_s = cue_span
    elif episode and isinstance(episode.get("shots"), list) and dur_s:
        shot_holds = [h for s in episode["shots"] if isinstance(s, dict) and (h := _extract_observation_hold(s)) is not None and h > 0]
        if shot_holds and dur_s > sum(shot_holds) + 1.0:
            active_dur_s = dur_s - sum(shot_holds)

    if text.strip() and active_dur_s and active_dur_s > 0:
        minutes = active_dur_s / 60.0
        if edition == "zh":
            chars = len(CJK_RE.findall(text))
            if chars > 0:
                rate_val = round(chars / minutes, 1)
                lo, hi = speech_cfg.get("cjk_chars_per_min", [175, 240])
                if rate_val < lo or rate_val > hi:
                    flags.append(
                        {
                            "code": "speech_rate_out_of_range",
                            "edition": edition,
                            "unit": "chars_per_min",
                            "measured": rate_val,
                            "expected_range": [lo, hi],
                        }
                    )
        else:
            words = len(WORD_RE.findall(text))
            if words > 0:
                rate_val = round(words / minutes, 1)
                lo, hi = speech_cfg.get("en_words_per_min", [115, 160])
                if rate_val < lo or rate_val > hi:
                    flags.append(
                        {
                            "code": "speech_rate_out_of_range",
                            "edition": edition,
                            "unit": "words_per_min",
                            "measured": rate_val,
                            "expected_range": [lo, hi],
                        }
                    )

    min_hold = float(speech_cfg.get("min_observation_hold_s", 0.8))
    min_hold_ratio = float(speech_cfg.get("min_observation_hold_ratio", 0.15))
    long_wait_s = float(speech_cfg.get("long_empty_wait_s", 1.45))
    max_long_ratio = float(speech_cfg.get("max_long_empty_wait_ratio", 0.4))
    max_abs_rate_pct = float(speech_cfg.get("max_tts_rate_abs_pct", 6.0))
    hold_count: int | None = None
    sample_units = 0
    known: list[float] = []
    if episode and isinstance(episode.get("shots"), list):
        explicit_holds = [_extract_observation_hold(s) for s in episode["shots"] if isinstance(s, dict)]
        known = [h for h in explicit_holds if h is not None]
        if len(known) >= 3:
            sample_units = len(known)
            hold_count = sum(1 for h in known if h >= min_hold)
    if hold_count is None and len(cues) >= 3:
        gaps = [cues[i + 1]["start_s"] - cues[i]["end_s"] for i in range(len(cues) - 1)]
        sample_units = len(gaps) + 1
        hold_count = sum(1 for g in gaps if g >= min_hold)

    if hold_count is not None and sample_units >= 3:
        required = max(1, int(sample_units * min_hold_ratio))
        if hold_count < required:
            flags.append(
                {
                    "code": "missing_observation_holds",
                    "edition": edition,
                    "holds_ge_min_s": hold_count,
                    "required_min": required,
                    "min_hold_s": min_hold,
                }
            )
    if len(known) >= 6:
        long_holds = sum(1 for h in known if h >= long_wait_s)
        if long_holds / len(known) > max_long_ratio:
            flags.append(
                {
                    "code": "mechanical_chopped_pauses",
                    "edition": edition,
                    "long_holds": long_holds,
                    "total_shots": len(known),
                    "threshold_s": long_wait_s,
                }
            )

    raw_rate = None
    script_source_text = text
    if episode and isinstance(episode.get("narration"), dict):
        nar = episode["narration"]
        raw_rate = nar.get("rate")
        ep_dir = episode.get("_dir")
        if raw_rate is None and isinstance(ep_dir, Path):
            gen_ref = nar.get("generation_record")
            if isinstance(gen_ref, dict) and isinstance(gen_ref.get("file"), str):
                gen_path = _resolve_path(ep_dir, gen_ref["file"])
                if gen_path.is_file():
                    try:
                        gen_data = _load_json(gen_path)
                        if isinstance(gen_data, dict) and isinstance(gen_data.get("voice"), dict):
                            raw_rate = gen_data["voice"].get("rate")
                    except (OSError, ValueError):
                        pass
        if isinstance(ep_dir, Path) and isinstance(nar.get("script_file"), str) and nar["script_file"].strip():
            script_path = _resolve_path(ep_dir, nar["script_file"])
            if script_path.is_file():
                try:
                    script_source_text = script_path.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    pass

    if raw_rate is not None:
        m_rate = PCT_RATE_RE.match(str(raw_rate))
        if m_rate and abs(float(m_rate.group(1))) > max_abs_rate_pct:
            flags.append(
                {
                    "code": "tts_rate_warping",
                    "edition": edition,
                    "measured_rate": str(raw_rate).strip(),
                    "max_abs_pct": max_abs_rate_pct,
                }
            )

    if isinstance(script_source_text, str) and script_source_text.strip():
        ai_reasons = []
        raw_sents = [s.strip() for s in re.split(r"[。！？!?]+", script_source_text) if s.strip()]
        if edition == "zh":
            if PROMPT_COLON_RE.search(script_source_text):
                ai_reasons.append("prompt_header_colon")
            if CLICKBAIT_HOOK_RE.search(script_source_text):
                ai_reasons.append("clickbait_contrast_hook")
            if len(STRAWMAN_REVERSAL_RE.findall(script_source_text)) >= 2:
                ai_reasons.append("strawman_reversal_density")
            zh_sents = [len(CJK_RE.findall(s)) for s in raw_sents if len(CJK_RE.findall(s)) > 0]
            if len(zh_sents) >= 8:
                mean_cjk = sum(zh_sents) / len(zh_sents)
                short_ratio = sum(1 for n in zh_sents if n <= 18) / len(zh_sents)
                if mean_cjk < 22.0 or short_ratio >= 0.55:
                    ai_reasons.append(f"telegraphic_short_sentences:mean={mean_cjk:.1f},short_ratio={short_ratio:.2f}")
            tail_text = "。".join(raw_sents[-2:]) if raw_sents else ""
            if SLOGAN_CLOSING_RE.search(tail_text):
                ai_reasons.append("slogan_closing_formula")
        semi_count = len(re.findall(r"[；;]", script_source_text))
        tail_semi = any(re.search(r"[；;]", s) for s in raw_sents[-2:]) if raw_sents else False
        if semi_count >= 2 or tail_semi:
            ai_reasons.append("semicolon_tail_stuffing")
        blocks = [b.strip() for b in re.split(r"\r?\n\s*\r?\n", script_source_text) if b.strip()]
        if len(blocks) >= 8 and sum(1 for b in blocks if len(b) <= 95) / len(blocks) >= 0.7:
            ai_reasons.append(f"per_shot_paragraph_splitting:{len(blocks)}_blocks")
        if ai_reasons:
            flags.append(
                {
                    "code": "script_ai_tone_markers",
                    "edition": edition,
                    "reasons": ai_reasons,
                }
            )

    _check_narrative_depth_and_world_continuity(episode, edition, script_source_text, dur_s, policy, flags)
    _check_flow_origin_purity(episode, edition, flags)
    return {"edition": edition, "speech_rate": rate_val, "observation_holds": hold_count, "sample_units": sample_units}


def _extract_required_scope_count(episode: dict[str, Any] | None) -> int:
    if not isinstance(episode, dict):
        return 0
    scope_obj = episode.get("scope")
    if isinstance(scope_obj, dict) and scope_obj.get("kind", "episode") != "episode":
        return 0
    counts = [0]
    topic = episode.get("topic")
    if isinstance(topic, dict):
        cur = topic.get("current")
        if isinstance(cur, dict) and isinstance(cur.get("required_scope"), list):
            counts.append(len(cur["required_scope"]))
    ta = episode.get("topic_alignment")
    if isinstance(ta, dict) and isinstance(ta.get("coverage"), list):
        counts.append(len(ta["coverage"]))
    return max(counts)


def _extract_shot_observation_level(shot: dict[str, Any]) -> str | None:
    if isinstance(shot.get("observation_level"), str) and shot["observation_level"].strip():
        return shot["observation_level"].strip()
    sb = shot.get("shotbook")
    if isinstance(sb, dict):
        rl = sb.get("realism")
        if isinstance(rl, dict) and isinstance(rl.get("observation_level"), str) and rl["observation_level"].strip():
            return rl["observation_level"].strip()
    return None


def _check_narrative_depth_and_world_continuity(
    episode: dict[str, Any] | None,
    edition: str,
    script_text: str,
    dur_s: float | None,
    policy: dict[str, Any],
    flags: list[dict[str, Any]],
) -> None:
    if not isinstance(episode, dict):
        return
    depth_cfg = policy.get("narrative_depth", {})
    min_scopes = int(depth_cfg.get("min_scope_items_for_full_depth", 4))
    scope_count = _extract_required_scope_count(episode)
    if scope_count >= min_scopes:
        depth_reasons: list[str] = []
        if edition == "zh":
            min_zh = max(
                int(depth_cfg.get("min_episode_cjk_chars", 450)),
                int(depth_cfg.get("min_cjk_chars_per_scope_item", 95)) * scope_count,
            )
            cjk_len = len(CJK_RE.findall(script_text or ""))
            if cjk_len < min_zh:
                depth_reasons.append(f"cjk_chars:{cjk_len}<{min_zh}")
        else:
            min_en = max(
                int(depth_cfg.get("min_episode_en_words", 280)),
                int(depth_cfg.get("min_en_words_per_scope_item", 60)) * scope_count,
            )
            en_len = len(WORD_RE.findall(script_text or ""))
            if en_len < min_en:
                depth_reasons.append(f"en_words:{en_len}<{min_en}")
        min_dur = float(depth_cfg.get("min_episode_duration_s", 135.0))
        if dur_s is not None and dur_s < min_dur:
            depth_reasons.append(f"duration_s:{round(dur_s, 2)}<{min_dur}")
        if depth_reasons:
            flags.append(
                {
                    "code": "compressed_checklist_episode",
                    "edition": edition,
                    "scope_count": scope_count,
                    "reasons": depth_reasons,
                }
            )

    shots = episode.get("shots")
    if isinstance(shots, list):
        seq: list[tuple[str, str | None]] = []
        for idx, sh in enumerate(shots):
            if isinstance(sh, dict):
                seq.append((_extract_shot_id(sh, idx), _extract_shot_observation_level(sh)))
        if len(seq) >= 4:
            islands: list[str] = []
            for idx in range(1, len(seq) - 1):
                prev_lvl = seq[idx - 1][1]
                cur_lvl = seq[idx][1]
                next_lvl = seq[idx + 1][1]
                if (
                    prev_lvl
                    and cur_lvl
                    and next_lvl
                    and prev_lvl == next_lvl
                    and cur_lvl != prev_lvl
                    and ("not_observable" in (prev_lvl, cur_lvl))
                ):
                    islands.append(f"{seq[idx][0]}:{prev_lvl}->{cur_lvl}->{next_lvl}")
            if islands:
                flags.append(
                    {
                        "code": "world_ping_pong_cuts",
                        "edition": edition,
                        "islands": islands,
                    }
                )


def run_audit(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    policy = load_policy()
    flags: list[dict[str, Any]] = []
    min_edge = int(policy.get("min_short_edge_px", 1080))
    expected_clip_fps = float(policy.get("expected_clip_fps", 24))
    native_fps = float(policy.get("native_fps", 24))

    ep_zh: dict[str, Any] | None = None
    ep_en: dict[str, Any] | None = None
    ep_zh_dir: Path | None = None
    ep_en_dir: Path | None = None

    if args.episode_zh:
        p = Path(args.episode_zh).resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Episode zh JSON not found: {p}")
        ep_zh = _load_json(p)
        ep_zh_dir = p.parent
        ep_zh["_dir"] = ep_zh_dir
    if args.episode_en:
        p = Path(args.episode_en).resolve()
        if not p.is_file():
            flags.append({"code": "missing_bilingual_edition", "missing": "episode_en", "path": str(p)})
        else:
            ep_en = _load_json(p)
            ep_en_dir = p.parent
            ep_en["_dir"] = ep_en_dir

    clips_dir = Path(args.clips_dir).resolve() if args.clips_dir else None
    clips_manifest = _load_json(Path(args.clips_manifest).resolve()) if args.clips_manifest else None

    clip_map, missing_clips = _collect_episode_clips(ep_zh or ep_en, ep_zh_dir or ep_en_dir, clips_dir, clips_manifest)
    for sid, mpath in missing_clips:
        flags.append({"code": "missing_source_clip", "shot_id": sid, "path": str(mpath)})
    if args.clips_only and not clip_map and not missing_clips:
        flags.append({"code": "missing_source_clip", "shot_id": None, "detail": "No source clips resolved in --clips-only mode"})

    probed_clips: dict[str, list[dict[str, Any]]] = {}
    seen_clip_probes: dict[str, dict[str, Any]] = {}
    for sid, paths in clip_map.items():
        for cpath in paths:
            key = str(cpath.resolve())
            if key not in seen_clip_probes:
                try:
                    info = ffprobe_media(cpath)
                except RuntimeError as exc:
                    flags.append({"code": "missing_source_clip", "shot_id": sid, "path": key, "detail": str(exc)})
                    continue
                seen_clip_probes[key] = info
                if not info["has_video"] or info["width"] is None or info["height"] is None:
                    flags.append({"code": "missing_source_clip", "shot_id": sid, "path": key, "detail": "No valid video stream"})
                elif min(info["width"], info["height"]) < min_edge:
                    flags.append(
                        {
                            "code": "low_res_source_clip",
                            "shot_id": sid,
                            "path": key,
                            "width": info["width"],
                            "height": info["height"],
                            "min_short_edge_px": min_edge,
                        }
                    )
                if info["avg_fps"] is not None and abs(info["avg_fps"] - expected_clip_fps) > 0.25:
                    flags.append(
                        {
                            "code": "source_clip_fps_drift",
                            "shot_id": sid,
                            "path": key,
                            "measured_fps": info["avg_fps"],
                            "expected_fps": expected_clip_fps,
                        }
                    )
            if key in seen_clip_probes:
                probed_clips.setdefault(sid, []).append(seen_clip_probes[key])

    exports_info: dict[str, dict[str, Any]] = {}
    speech_metrics: dict[str, Any] = {}
    caption_metrics: dict[str, Any] = {}

    if not args.clips_only:
        if args.video is None:
            raise ValueError("Export video path is required unless --clips-only is specified")
        zh_path = Path(args.video).resolve()
        if not zh_path.is_file():
            raise FileNotFoundError(f"Primary export video not found: {zh_path}")
        exports_info["zh"] = ffprobe_media(zh_path)

        if not args.en_video:
            flags.append({"code": "missing_bilingual_edition", "missing": "en_video"})
        else:
            en_path = Path(args.en_video).resolve()
            if not en_path.is_file():
                flags.append({"code": "missing_bilingual_edition", "missing": "en_video", "path": str(en_path)})
            else:
                exports_info["en"] = ffprobe_media(en_path)

        if (ep_zh is not None) != (ep_en is not None):
            missing_key = "episode_en" if ep_zh is not None else "episode_zh"
            if not any(f["code"] == "missing_bilingual_edition" and f.get("missing") == missing_key for f in flags):
                flags.append({"code": "missing_bilingual_edition", "missing": missing_key})

        editions_cfg = [("zh", exports_info.get("zh"), ep_zh, args.captions_zh), ("en", exports_info.get("en"), ep_en, args.captions_en)]
        for ed, exp, ep_obj, cap_arg in editions_cfg:
            if exp is not None:
                scene_min_edge = min_edge
                if not exp["has_video"] or not exp["has_audio"]:
                    flags.append(
                        {
                            "code": "export_stream_mismatch",
                            "edition": ed,
                            "has_video": exp["has_video"],
                            "has_audio": exp["has_audio"],
                        }
                    )
                elif exp["width"] is not None and exp["height"] is not None and min(exp["width"], exp["height"]) < scene_min_edge:
                    flags.append(
                        {
                            "code": "export_stream_mismatch",
                            "edition": ed,
                            "width": exp["width"],
                            "height": exp["height"],
                            "min_short_edge_px": scene_min_edge,
                        }
                    )
                if ep_obj and isinstance(ep_obj.get("design"), dict) and isinstance(ep_obj["design"].get("output"), dict):
                    out_cfg = ep_obj["design"]["output"]
                    exp_w, exp_h = out_cfg.get("width"), out_cfg.get("height")
                    if exp_w and exp_h and (exp["width"] != exp_w or exp["height"] != exp_h):
                        flags.append(
                            {
                                "code": "export_stream_mismatch",
                                "edition": ed,
                                "measured": [exp["width"], exp["height"]],
                                "expected": [exp_w, exp_h],
                            }
                        )
                    cfg_fps = out_cfg.get("fps")
                    if cfg_fps is not None and not args.allow_fps_conversion and abs(float(cfg_fps) - native_fps) > 0.25:
                        flags.append(
                            {
                                "code": "fps_cadence_mismatch",
                                "edition": ed,
                                "detail": f"design.output.fps={cfg_fps} diverges from native {native_fps} fps without --allow-fps-conversion",
                            }
                        )

                if not args.allow_fps_conversion:
                    if exp["avg_fps"] is not None and abs(exp["avg_fps"] - native_fps) > 0.25:
                        flags.append(
                            {
                                "code": "fps_cadence_mismatch",
                                "edition": ed,
                                "measured_fps": exp["avg_fps"],
                                "expected_native_fps": native_fps,
                            }
                        )
                    if exp["avg_fps"] is not None and exp["r_fps"] is not None and abs(exp["avg_fps"] - exp["r_fps"]) > 0.5:
                        flags.append(
                            {
                                "code": "fps_cadence_mismatch",
                                "edition": ed,
                                "avg_fps": exp["avg_fps"],
                                "r_fps": exp["r_fps"],
                                "detail": "Variable frame rate detected on Flow timeline",
                            }
                        )

            cues, cap_summary = _check_captions(
                ed,
                Path(cap_arg).resolve() if cap_arg else None,
                ep_obj,
                exp["duration_s"] if exp else None,
                policy,
                flags,
            )
            if cap_summary is not None:
                caption_metrics[ed] = cap_summary
            if exp is not None or ep_obj is not None or cues:
                speech_metrics[ed] = _check_speech_and_holds(
                    ed,
                    ep_obj,
                    cues,
                    exp["duration_s"] if exp else None,
                    policy,
                    flags,
                )

        if "zh" in exports_info and "en" in exports_info:
            ez, ee = exports_info["zh"], exports_info["en"]
            if (ez["width"], ez["height"]) != (ee["width"], ee["height"]) or (
                ez["avg_fps"] and ee["avg_fps"] and abs(ez["avg_fps"] - ee["avg_fps"]) > 0.25
            ):
                flags.append(
                    {
                        "code": "export_stream_mismatch",
                        "detail": "zh and en export streams differ in dimensions or frame rate",
                        "zh": [ez["width"], ez["height"], ez["avg_fps"]],
                        "en": [ee["width"], ee["height"], ee["avg_fps"]],
                    }
                )
            dz, de = ez.get("duration_s"), ee.get("duration_s")
            if dz and de:
                diff_s = abs(dz - de)
                diff_ratio = diff_s / max(dz, de)
                div_cfg = policy.get("bilingual", {})
                max_ratio = float(div_cfg.get("max_duration_divergence_ratio", 0.12))
                max_abs_s = float(div_cfg.get("max_duration_divergence_s", 15.0))
                if diff_s > max_abs_s or (diff_ratio > max_ratio and diff_s > 2.0):
                    flags.append(
                        {
                            "code": "edition_duration_divergence",
                            "zh_duration_s": dz,
                            "en_duration_s": de,
                            "diff_s": round(diff_s, 3),
                            "diff_ratio": round(diff_ratio, 4),
                        }
                    )

        if ep_zh and ep_en:
            zh_ids = [_extract_shot_id(s, i) for i, s in enumerate(ep_zh.get("shots", [])) if isinstance(s, dict)]
            en_ids = [_extract_shot_id(s, i) for i, s in enumerate(ep_en.get("shots", [])) if isinstance(s, dict)]
            if zh_ids != en_ids:
                flags.append(
                    {
                        "code": "shot_sequence_mismatch",
                        "zh_count": len(zh_ids),
                        "en_count": len(en_ids),
                        "zh_ids": zh_ids,
                        "en_ids": en_ids,
                    }
                )

    overrun_cfg = policy.get("clip_duration", {})
    max_ratio = float(overrun_cfg.get("max_overrun_ratio", 1.05))
    max_abs = float(overrun_cfg.get("max_overrun_s", 0.35))
    for ed, ep_obj in (("zh", ep_zh), ("en", ep_en)):
        if not ep_obj:
            continue
        for idx, shot in enumerate(ep_obj.get("shots", [])):
            if not isinstance(shot, dict):
                continue
            sid = _extract_shot_id(shot, idx)
            shot_dur = _extract_shot_duration(shot)
            if shot_dur is None:
                continue
            src_list = probed_clips.get(sid, [])
            if src_list and all(c.get("duration_s") is not None for c in src_list):
                native_dur = sum(float(c["duration_s"]) for c in src_list)
            elif isinstance(shot.get("source_clip_duration_s"), (int, float)):
                native_dur = float(shot["source_clip_duration_s"])
            else:
                continue
            allowed = max(native_dur * max_ratio, native_dur + max_abs)
            if shot_dur > allowed:
                flags.append(
                    {
                        "code": "clip_duration_overrun",
                        "edition": ed,
                        "shot_id": sid,
                        "shot_duration_s": round(shot_dur, 3),
                        "source_clip_duration_s": round(native_dur, 3),
                        "implied_stretch_ratio": round(shot_dur / max(native_dur, 1e-6), 3),
                    }
                )

    report = {
        "tool": "scripts/google_flow_audit.py",
        "report_schema_version": 1,
        "status": "flagged" if flags else "clean",
        "clips_only": bool(args.clips_only),
        "allow_fps_conversion": bool(args.allow_fps_conversion),
        "inputs": {
            "zh_video": str(args.video) if args.video else None,
            "en_video": str(args.en_video) if args.en_video else None,
            "episode_zh": str(args.episode_zh) if args.episode_zh else None,
            "episode_en": str(args.episode_en) if args.episode_en else None,
            "clips_dir": str(clips_dir) if clips_dir else None,
        },
        "measurements": {
            "staged_clips_count": len(seen_clip_probes),
            "staged_clips": seen_clip_probes,
            "exports": exports_info,
            "speech": speech_metrics,
            "captions": caption_metrics,
        },
        "flags": flags,
        "summary": {
            "flag_count": len(flags),
            "flag_codes": sorted({f["code"] for f in flags}),
        },
    }
    return report, (1 if flags else 0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit Google Flow source clips and paired zh/en exports.")
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("measure", help="Measure clips and/or paired bilingual exports.")
    m.add_argument("video", nargs="?", help="Primary (zh) export video path (optional when --clips-only).")
    m.add_argument("--en-video", help="Paired English export video path.")
    m.add_argument("--episode-zh", help="Sibling Chinese episode.zh.json path.")
    m.add_argument("--episode-en", help="Sibling English episode.en.json path.")
    m.add_argument("--clips-dir", help="Directory containing staged Google Flow source clips.")
    m.add_argument("--clips-manifest", help="JSON manifest mapping shot IDs to staged clip files.")
    m.add_argument("--captions-zh", help="Chinese .srt or .ass subtitle path.")
    m.add_argument("--captions-en", help="English .srt or .ass subtitle path.")
    m.add_argument("--clips-only", action="store_true", help="Audit staged source clips only without requiring final exports.")
    m.add_argument("--allow-fps-conversion", action="store_true", help="Permit non-24 fps timelines when explicitly commissioned.")
    m.add_argument("--report", required=True, help="Output path for a new JSON audit report (refuses overwrite).")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report_path = Path(args.report)
    if report_path.exists():
        print(f"Refusing to overwrite existing report: {report_path}", file=sys.stderr)
        return 2
    try:
        report, code = run_audit(args)
    except (FileNotFoundError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"google_flow_audit status={report['status']} flags={report['summary']['flag_count']} report={report_path}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
