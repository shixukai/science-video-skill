#!/usr/bin/env python3
"""Build static, local review material; never approve an episode or change QA."""
import argparse
from bisect import bisect_left, bisect_right
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


LIMITS = ("静帧接触表仅供人工检查构图、层级、文字与画面一致性；不能证明动态、"
          "科学内容、声音或整体审美质量。它不是验收结果，不修改 episode 或 QA。")
BEAT_BOARD_LIMITS = (
    "Internal pre-render comprehension review board pairing unmodified textless 3D/video "
    "preflight stills with actual synchronized captions.srt lines in an external review margin. "
    "Supports the 1-Second Layperson Pointing Test before full rendering; never ships as media "
    "or approves an episode."
)
# A local playlist can still reference remote URLs or files outside the packet.
# Accept self-contained video containers and file transport only, in both tools.
INPUT_OPTIONS = ["-protocol_whitelist", "file", "-format_whitelist",
                 "mov,matroska,avi,mpegts,flv,mpeg,ogg,nut,mxf"]
SRT_TIME_RE = re.compile(
    r"^\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})"
)
STILL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class ReviewError(ValueError):
    """An actionable input or local-tool failure."""


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def number(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def run_tool(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewError(Path(command[0]).name + " could not finish; no review was published.") from exc
    if result.returncode:
        raise ReviewError(Path(command[0]).name + " failed; no review was published.")
    return result.stdout


def video_geometry(stream, frames):
    """Keep this sampler simple: reject geometry needing display transforms."""
    guidance = (" Export a square-pixel review copy without a rotation/display matrix "
                "from your editing software; the source media was not changed.")
    width, height = stream.get("width"), stream.get("height")
    if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in (width, height)):
        raise ReviewError("The video dimensions are invalid." + guidance)

    def ratio(value):
        try:
            return Fraction(str(value).replace(":", "/"))
        except (ValueError, ZeroDivisionError):
            return None

    sar = stream.get("sample_aspect_ratio")
    if ratio(sar) != 1:
        raise ReviewError("Non-square or unspecified sample aspect ratio is unsupported." + guidance)
    expected_dar = Fraction(width, height)
    if stream.get("display_aspect_ratio") and ratio(stream["display_aspect_ratio"]) != expected_dar:
        raise ReviewError("The display aspect ratio requires a geometry transform." + guidance)
    identity = [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]
    for record in [stream, *frames]:
        if record.get("width", width) != width or record.get("height", height) != height:
            raise ReviewError("Changing video dimensions are unsupported." + guidance)
        if ratio(record.get("sample_aspect_ratio", sar)) != 1:
            raise ReviewError("Non-square frame sample aspect ratio is unsupported." + guidance)
        rotation_tag = record.get("tags", {}).get("rotate", "0")
        if ratio(rotation_tag) != 0:
            raise ReviewError("Video rotation is unsupported." + guidance)
        for side_data in record.get("side_data_list", []):
            if side_data.get("side_data_type") != "Display Matrix":
                continue
            try:
                matrix = [int(value) for line in side_data.get("displaymatrix", "").splitlines()
                          if ":" in line for value in line.split(":", 1)[1].split()]
            except ValueError:
                matrix = []
            if matrix != identity or ratio(side_data.get("rotation", 0)) != 0:
                raise ReviewError("A non-default display matrix or rotation is unsupported." + guidance)
    return {"coded_width": width, "coded_height": height, "display_width": width,
            "display_height": height, "sample_aspect_ratio": "1:1",
            "display_aspect_ratio": f"{expected_dar.numerator}:{expected_dar.denominator}",
            "rotation_degrees": 0, "display_transform": "identity"}


def probe_video(media, ffprobe):
    # Decode the frame timeline once. Selecting real frame indices avoids seeking
    # beyond EOF or inventing timestamps from an average frame rate on VFR media.
    raw = run_tool([
        ffprobe, "-v", "error", "-select_streams", "v:0", "-show_streams", "-show_format",
        "-show_frames", "-show_entries",
        "stream=index,codec_type,width,height,start_time,duration,avg_frame_rate,r_frame_rate,sample_aspect_ratio,display_aspect_ratio:"
        "stream_disposition=attached_pic:stream_tags=rotate:stream_side_data:format=start_time,duration:"
        "frame=best_effort_timestamp_time,duration_time,pkt_duration_time,width,height,sample_aspect_ratio:frame_side_data",
        "-of", "json", *INPUT_OPTIONS, str(media),
    ])
    try:
        data = json.loads(raw)
        stream = data["streams"][0]
        frames = data["frames"]
        if stream.get("disposition", {}).get("attached_pic") or not frames:
            raise ReviewError("The media must contain a timed video stream, not cover art.")
        stream["geometry"] = video_geometry(stream, frames)
        pts = [float(frame["best_effort_timestamp_time"]) for frame in frames]
        container = data.get("format", {})
        origin = float(container.get("start_time", stream.get("start_time", pts[0])))
        times = [value - origin for value in pts]
        if (not all(number(value) and value >= 0 for value in times)
                or any(a >= b for a, b in zip(times, times[1:]))):
            raise ReviewError("Video frame timestamps must be finite, nonnegative and increasing.")
        if "duration" in stream:
            duration = float(stream.get("start_time", pts[0])) - origin + float(stream["duration"])
        else:
            # Frame durations are preferable to a container duration which may
            # include an audio tail beyond the last video frame.
            last = frames[-1]
            frame_duration = last.get("duration_time", last.get("pkt_duration_time"))
            if frame_duration is None:
                raise ReviewError("The video has no usable stream or final-frame duration.")
            duration = times[-1] + float(frame_duration)
        if not number(duration) or duration <= times[-1]:
            raise ReviewError("The video duration must extend beyond its last decoded frame.")
    except (KeyError, IndexError, TypeError, ValueError, OverflowError) as exc:
        if isinstance(exc, ReviewError):
            raise
        raise ReviewError("ffprobe did not return a usable video timeline and duration.") from exc
    return stream, duration, times


def shot_samples(data, duration, times):
    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        raise ReviewError("episode.shots must be a nonempty list with actual shotbook times.")
    result, ids, previous_end = [], set(), 0
    for index, shot in enumerate(shots, 1):
        if not isinstance(shot, dict):
            raise ReviewError("Each shot must be an object.")
        ident, book = shot.get("id"), shot.get("shotbook")
        if not isinstance(ident, str) or not ident.strip() or ident in ids:
            raise ReviewError("Shot IDs must be nonempty, unique strings.")
        ids.add(ident)
        if not isinstance(book, dict):
            raise ReviewError("Each shot needs a shotbook with actual start/end seconds.")
        basis = book.get("timing_basis", {})
        if isinstance(basis, dict) and basis.get("mode") == "relative_plan":
            raise ReviewError("relative_plan cannot be sampled; supply actual video-aligned shot times.")
        start, end = book.get("start"), book.get("end")
        if not number(start) or not number(end) or not 0 <= start < end:
            raise ReviewError("Shot times must be finite, non-boolean seconds with 0 <= start < end; null plans cannot be sampled.")
        if start < previous_end:
            raise ReviewError("Shots overlap or are out of timeline order.")
        if end > duration:
            raise ReviewError("A shot exceeds the actual video duration.")
        previous_end = end
        samples = []
        for position, requested in (("start", start), ("mid", start + (end - start) / 2), ("end", end)):
            # At start/mid show the frame held at that time. End is exclusive:
            # a frame exactly at the next cut belongs to the following shot.
            frame_index = ((bisect_left(times, requested) if position == "end"
                            else bisect_right(times, requested)) - 1)
            if frame_index < 0:
                raise ReviewError("A requested shot time precedes the first decoded video frame.")
            samples.append({"position": position, "requested_seconds": requested,
                            "frame_seconds": times[frame_index], "frame_index": frame_index,
                            "file": f"frames/{index:04d}-{position}.png"})
        result.append({"id": ident, "start": start, "end": end, "samples": samples,
                       "visual_note": str(shot.get("visual_note", "")),
                       "subject": str(book.get("subject", "")), "action": str(book.get("action", ""))})
    return result


def timeline_coverage(shots, duration):
    intervals, gaps, cursor = [], [], 0
    for shot in shots:
        start, end = shot["start"], shot["end"]
        intervals.append([start, end])
        if start > cursor:
            gaps.append([cursor, start])
        cursor = end
    if cursor < duration:
        gaps.append([cursor, duration])
    return {"video_duration_seconds": duration, "listed_intervals": intervals,
            "uncovered_intervals": gaps}


def parse_srt(path):
    """Parse a UTF-8 SRT file into ordered cues with float start_s/end_s and clean text."""
    path = Path(path)
    if not path.is_file():
        raise ReviewError(f"Captions SRT file not found: {path}")
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ReviewError("Captions SRT must be valid UTF-8 text.") from exc
    blocks = re.split(r"\r?\n\s*\r?\n", raw.strip())
    cues = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        time_idx = None
        match = None
        for idx, line in enumerate(lines):
            m = SRT_TIME_RE.match(line)
            if m:
                time_idx = idx
                match = m
                break
        if match is None:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = (int(v) for v in match.groups())
        start_s = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
        end_s = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
        if end_s < start_s:
            raise ReviewError(f"SRT cue has end < start: {lines[time_idx]}")
        text = " ".join(lines[time_idx + 1:]).strip()
        if not text:
            continue
        cues.append({
            "index": len(cues) + 1,
            "start_s": round(start_s, 3),
            "end_s": round(end_s, 3),
            "text": text,
        })
    if not cues:
        raise ReviewError("Captions SRT contains no readable timed cues.")
    return cues


def match_cues_at_time(cues, t_s, margin_s=0.25):
    """Find active spoken subtitle cue(s) at timestamp t_s, with optional breath margin."""
    exact = [cue for cue in cues if cue["start_s"] <= t_s <= cue["end_s"]]
    if exact:
        return {
            "match_kind": "exact",
            "cue_indices": [c["index"] for c in exact],
            "text": " / ".join(c["text"] for c in exact),
            "nearest_text": "",
        }
    best = None
    best_dist = float("inf")
    for cue in cues:
        if t_s < cue["start_s"]:
            dist = cue["start_s"] - t_s
        else:
            dist = t_s - cue["end_s"]
        if dist < best_dist:
            best_dist = dist
            best = cue
    if best is not None and best_dist <= margin_s:
        return {
            "match_kind": "breath_margin",
            "cue_indices": [best["index"]],
            "text": best["text"],
            "nearest_text": "",
        }
    nearest = f"(nearest {best['start_s']:.2f}-{best['end_s']:.2f}s: {best['text']})" if best else ""
    return {
        "match_kind": "silent_gap",
        "cue_indices": [],
        "text": "[no active spoken cue]",
        "nearest_text": nearest,
    }


def extract_frame_number(path):
    """Extract the frame integer from a still filename (uses the last digit run in stem)."""
    matches = re.findall(r"\d+", Path(path).stem)
    if not matches:
        raise ReviewError(f"Cannot infer frame number from still filename: {Path(path).name}")
    return int(matches[-1])


def resolve_review_font_path(skill_root=None):
    """Load commercially cleared font candidates from config/production-policy.json."""
    root = Path(skill_root) if skill_root else Path(__file__).resolve().parents[1]
    policy_path = root / "config" / "production-policy.json"
    candidates = []
    if policy_path.is_file():
        try:
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            candidates = list(policy.get("feed_package", {}).get("font_candidates", []))
        except (OSError, json.JSONDecodeError, TypeError):
            candidates = []
    for raw in candidates:
        p = Path(raw)
        if p.is_file():
            return p
    return None


def _wrap_text_px(draw, text, font, max_width_px, max_lines=3):
    """Character-aware line wrap supporting CJK and Latin text without horizontal overflow."""
    lines = []
    current = ""
    for ch in text:
        candidate = current + ch
        if current and draw.textlength(candidate, font=font) > max_width_px:
            lines.append(current.strip())
            current = ch.lstrip()
            if len(lines) >= max_lines:
                break
        else:
            current = candidate
    if len(lines) < max_lines and current.strip():
        lines.append(current.strip())
    if len(lines) == max_lines and sum(len(x) for x in lines) < len(text.replace(" ", "")):
        tail = lines[-1]
        while len(tail) > 1 and draw.textlength(tail + "…", font=font) > max_width_px:
            tail = tail[:-1]
        lines[-1] = tail + "…"
    return lines or [""]


def render_beat_board_html(title, items, uncovered_cues, fps, frame_origin):
    esc = html.escape
    cards = []
    for idx, item in enumerate(items, 1):
        badge_cls = "exact" if item["match_kind"] == "exact" else (
            "margin" if item["match_kind"] == "breath_margin" else "silent"
        )
        nearest_html = (
            f'<div class="nearest">{esc(item["nearest_text"])}</div>'
            if item.get("nearest_text") else ""
        )
        cards.append(
            f'<article class="card">'
            f'<div class="frame-wrap"><img src="{esc(item["file"])}" '
            f'alt="frame {item["frame"]}"></div>'
            f'<div class="meta">'
            f'<span class="tag">#{idx:02d} · f{item["frame"]:04d} · {item["time_s"]:.2f}s</span>'
            f'<span class="badge {badge_cls}">{esc(item["match_kind"])}</span>'
            f'</div>'
            f'<p class="caption">{esc(item["caption_text"])}</p>'
            f'{nearest_html}'
            f'</article>'
        )
    if uncovered_cues:
        uncovered_rows = "".join(
            f'<li>#{c["index"]} ({c["start_s"]:.2f}–{c["end_s"]:.2f}s): {esc(c["text"])}</li>'
            for c in uncovered_cues
        )
        uncovered_html = (
            f'<section class="warn"><h2>Uncovered Spoken Cues ({len(uncovered_cues)})</h2>'
            f'<p>These spoken subtitle lines currently have NO preflight still covering them. '
            f'Add stills for any key visual transition before full rendering:</p>'
            f'<ul>{uncovered_rows}</ul></section>'
        )
    else:
        uncovered_html = '<p class="ok">All timed spoken SRT cues are covered by at least one preflight still.</p>'
    return (
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\' data:; style-src \'unsafe-inline\'">'
        f'<title>{esc(title)} · Captioned Beat Review Board</title><style>'
        'body{margin:0;padding:24px;background:#101317;color:#eceae4;font:15px/1.5 system-ui,sans-serif}'
        'main{max-width:1680px;margin:auto}h1{font-size:24px;margin:0 0 8px}h2{font-size:18px;margin:0 0 8px}'
        '.note{color:#aeb6bf;margin:0 0 14px}.checklist{background:#181d23;border:1px solid #2b3440;'
        'border-radius:8px;padding:12px 16px;margin:12px 0 18px}.checklist ul{margin:6px 0 0;padding-left:20px}'
        '.warn{background:#2a1d19;border:1px solid #8a4332;border-radius:8px;padding:12px 16px;margin:14px 0}'
        '.warn ul{margin:6px 0 0;padding-left:20px}.ok{color:#86d29f;margin:8px 0 14px}'
        '.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:18px}'
        '.card{background:#171c22;border:1px solid #28313c;border-radius:8px;overflow:hidden;display:flex;flex-direction:column}'
        '.frame-wrap{background:#000}.frame-wrap img{display:block;width:100%;height:auto}'
        '.meta{display:flex;justify-content:space-between;align-items:center;padding:8px 12px 2px;font-size:12px;color:#9ea8b3}'
        '.badge{padding:2px 6px;border-radius:4px;font-size:11px;text-transform:uppercase}'
        '.badge.exact{background:#1d3b2a;color:#97e4b1}.badge.margin{background:#3b321a;color:#f0cf7b}'
        '.badge.silent{background:#402022;color:#f09b9b}'
        '.caption{margin:4px 12px 10px;font-size:17px;font-weight:600;color:#f7f3ea;line-height:1.45}'
        '.nearest{margin:-4px 12px 10px;font-size:12px;color:#9ea8b3}'
        '</style><main>'
        f'<h1>{esc(title)} · Pre-Render Captioned Beat Review Board</h1>'
        f'<p class="note">{esc(BEAT_BOARD_LIMITS)} (fps={fps:g}, frame_origin={frame_origin}, raw stills unmodified)</p>'
        '<section class="checklist"><strong>1-Second Layperson Pointing Test (inspect EVERY tile before full Colab render):</strong>'
        '<ul>'
        '<li><strong>Referent lock:</strong> Read ONLY the spoken line below the still—can a cold viewer point to the exact named part within &lt;1 s?</li>'
        '<li><strong>Fixed vs. moving &amp; physics subject:</strong> Is the actually moving/load-bearing surface shown clearly with recognizable host anchors?</li>'
        '<li><strong>In-frame cause &amp; visible change:</strong> Are actuator and target in frame, valve port gaps unobstructed, and fluid/gas direction unmistakable?</li>'
        '<li><strong>16:9 composition &amp; zero slop:</strong> No &lt;25%-wide vertical "telephone pole" in empty void, no decorative floating glowing rings, no mystery cubes.</li>'
        '</ul></section>'
        f'{uncovered_html}'
        f'<section class="grid">{"".join(cards)}</section>'
        '</main></html>\n'
    )


def render_beat_board_sheet(items, output_jpeg, *, cols=3, tile_width=640, font_path=None):
    """Render an external-margin JPEG contact sheet without modifying any raw still pixels."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    if not items:
        raise ReviewError("At least one still is required to render a beat-board sheet.")
    cols = max(1, min(int(cols), len(items)))
    rows = math.ceil(len(items) / cols)
    pad = 16
    header_h = 44
    margin_h = 104
    tile_w = int(tile_width)
    # Derive uniform tile image height from the first image aspect ratio (default 16:9).
    with Image.open(items[0]["source_path"]) as sample_img:
        sw, sh = sample_img.size
    tile_img_h = max(120, int(round(tile_w * sh / max(1, sw))))
    tile_total_h = tile_img_h + margin_h
    sheet_w = pad + cols * (tile_w + pad)
    sheet_h = header_h + pad + rows * (tile_total_h + pad)
    canvas = Image.new("RGB", (sheet_w, sheet_h), (16, 19, 23))
    draw = ImageDraw.Draw(canvas)
    if font_path and Path(font_path).is_file():
        font_hdr = ImageFont.truetype(str(font_path), 18)
        font_meta = ImageFont.truetype(str(font_path), 16)
        font_cap = ImageFont.truetype(str(font_path), 21)
    else:
        font_hdr = ImageFont.load_default()
        font_meta = ImageFont.load_default()
        font_cap = ImageFont.load_default()
    draw.text(
        (pad, 12),
        "INTERNAL PRE-RENDER BEAT BOARD (RAW 3D FRAMES UNMODIFIED | EXTERNAL SRT REVIEW MARGIN)",
        fill=(182, 192, 204),
        font=font_hdr,
    )
    for idx, item in enumerate(items):
        r, c = divmod(idx, cols)
        x0 = pad + c * (tile_w + pad)
        y0 = header_h + pad + r * (tile_total_h + pad)
        with Image.open(item["source_path"]) as raw_img:
            rgb = raw_img.convert("RGB")
            resized = rgb.resize((tile_w, tile_img_h), Image.Resampling.LANCZOS)
        canvas.paste(resized, (x0, y0))
        bar_y = y0 + tile_img_h
        draw.rectangle([x0, bar_y, x0 + tile_w, bar_y + margin_h], fill=(23, 28, 34))
        draw.line([x0, bar_y, x0 + tile_w, bar_y], fill=(54, 66, 80), width=1)
        badge_color = (146, 224, 175) if item["match_kind"] == "exact" else (
            (240, 207, 123) if item["match_kind"] == "breath_margin" else (240, 155, 155)
        )
        meta_line = f"#{idx + 1:02d}  f{item['frame']:04d}  {item['time_s']:.2f}s  [{item['match_kind']}]"
        draw.text((x0 + 10, bar_y + 7), meta_line, fill=badge_color, font=font_meta)
        wrapped = _wrap_text_px(draw, item["caption_text"], font_cap, tile_w - 20, max_lines=3)
        ty = bar_y + 30
        for line in wrapped:
            draw.text((x0 + 10, ty), line, fill=(247, 243, 234), font=font_cap)
            ty += 24
    output_jpeg = Path(output_jpeg)
    canvas.save(output_jpeg, format="JPEG", quality=92, subsampling=0)
    return output_jpeg


def build_beat_board(
    stills_dir,
    captions,
    output,
    *,
    fps=30.0,
    frame_origin=1,
    cols=3,
    tile_width=640,
    title=None,
    build_sheet=True,
    breath_margin_s=0.25,
):
    """Build an internal captioned pre-render beat board from textless stills + actual captions.srt."""
    stills_dir = Path(stills_dir).resolve()
    captions = Path(captions).resolve()
    output_arg = Path(output)
    if not stills_dir.is_dir():
        raise ReviewError(f"Stills directory not found: {stills_dir}")
    if not number(fps) or fps <= 0:
        raise ReviewError("fps must be a positive finite number.")
    if not isinstance(frame_origin, int) or isinstance(frame_origin, bool) or frame_origin not in (0, 1):
        raise ReviewError("frame_origin must be 0 or 1.")
    if output_arg.exists() or output_arg.is_symlink():
        raise ReviewError("The output already exists; choose a new directory.")
    output = output_arg.resolve()
    cues = parse_srt(captions)
    captions_hash = sha256(captions)
    still_paths = sorted(
        p for p in stills_dir.iterdir()
        if p.is_file() and p.suffix.lower() in STILL_EXTENSIONS
    )
    if not still_paths:
        raise ReviewError(f"No still images ({', '.join(sorted(STILL_EXTENSIONS))}) found in {stills_dir}")
    seen_frames = {}
    parsed_stills = []
    for path in still_paths:
        frame_num = extract_frame_number(path)
        if frame_num in seen_frames:
            raise ReviewError(
                f"Duplicate frame number {frame_num} in stills directory: "
                f"{seen_frames[frame_num].name} and {path.name}"
            )
        seen_frames[frame_num] = path
        parsed_stills.append((frame_num, path))
    parsed_stills.sort(key=lambda pair: pair[0])

    covered_cue_indices = set()
    items = []
    for frame_num, src_path in parsed_stills:
        t_s = round(max(0.0, (frame_num - frame_origin) / float(fps)), 3)
        matched = match_cues_at_time(cues, t_s, margin_s=breath_margin_s)
        covered_cue_indices.update(matched["cue_indices"])
        rel_name = f"stills/{src_path.name}"
        items.append({
            "frame": frame_num,
            "time_s": t_s,
            "source_file": src_path.name,
            "source_path": src_path,
            "file": rel_name,
            "match_kind": matched["match_kind"],
            "cue_indices": matched["cue_indices"],
            "caption_text": matched["text"],
            "nearest_text": matched["nearest_text"],
        })
    uncovered_cues = [cue for cue in cues if cue["index"] not in covered_cue_indices]
    board_title = title or stills_dir.name
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".beat-board-", dir=output.parent) as temporary:
        staging = Path(temporary)
        staged_stills = staging / "stills"
        staged_stills.mkdir()
        output_files = []
        manifest_items = []
        for item in items:
            src = item["source_path"]
            dst = staging / item["file"]
            shutil.copyfile(src, dst)
            src_hash = sha256(src)
            dst_hash = sha256(dst)
            if src_hash != dst_hash:
                raise ReviewError(f"Still changed during staging: {src.name}")
            output_files.append({"file": item["file"], "sha256": dst_hash})
            manifest_items.append({
                "frame": item["frame"],
                "time_s": item["time_s"],
                "source_file": item["source_file"],
                "file": item["file"],
                "sha256": dst_hash,
                "match_kind": item["match_kind"],
                "cue_indices": item["cue_indices"],
                "caption_text": item["caption_text"],
                "nearest_text": item["nearest_text"],
            })
        html_path = staging / "beat-board.html"
        html_path.write_text(
            render_beat_board_html(board_title, manifest_items, uncovered_cues, fps, frame_origin),
            encoding="utf-8",
        )
        output_files.insert(0, {"file": "beat-board.html", "sha256": sha256(html_path)})
        sheet_file = None
        sheet_skipped_reason = None
        if build_sheet:
            font_path = resolve_review_font_path()
            sheet_out = render_beat_board_sheet(
                items,
                staging / "beat-board.jpg",
                cols=cols,
                tile_width=tile_width,
                font_path=font_path,
            )
            if sheet_out is not None:
                sheet_file = "beat-board.jpg"
                output_files.insert(1, {"file": sheet_file, "sha256": sha256(sheet_out)})
            else:
                sheet_skipped_reason = "pillow_unavailable"
        manifest = {
            "schema_version": 1,
            "kind": "captioned_beat_review_board",
            "review_status": "internal_comprehension_review_only_not_approval",
            "raw_stills_unmodified": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "limits": BEAT_BOARD_LIMITS,
            "title": board_title,
            "fps": float(fps),
            "frame_origin": frame_origin,
            "captions": {"file": captions.name, "sha256": captions_hash, "cue_count": len(cues)},
            "still_count": len(manifest_items),
            "covered_cue_count": len(covered_cue_indices),
            "uncovered_cue_count": len(uncovered_cues),
            "uncovered_cues": uncovered_cues,
            "sheet_file": sheet_file,
            "sheet_skipped_reason": sheet_skipped_reason,
            "items": manifest_items,
            "output_files": output_files,
        }
        (staging / "manifest.json").write_bytes(json_bytes(manifest))
        if output.exists() or output.is_symlink():
            raise ReviewError("The output appeared during staging; it was not overwritten.")
        os.rename(staging, output)
    return manifest


def render_html(title, shots, coverage, cues=None):
    esc = html.escape
    ranges = lambda values: "、".join(f"{start:.3f}–{end:.3f}s" for start, end in values) or "无"
    sections, overview = [], []
    for index, shot in enumerate(shots, 1):
        middle = shot["samples"][1]
        overview.append(f'<a href="#shot-{index:04d}"><img src="{middle["file"]}" '
                        f'alt="{esc(shot["id"])} mid"><span>{index:02d} · {esc(shot["id"])}<br>'
                        f'{shot["start"]:.3f}–{shot["end"]:.3f}s</span></a>')
        frame_figs = []
        for sample in shot["samples"]:
            cap_note = ""
            if cues:
                matched = match_cues_at_time(cues, sample["frame_seconds"])
                cap_note = f'<br><strong>{esc(matched["text"])}</strong>'
            frame_figs.append(
                f'<figure><img src="{sample["file"]}" alt="{esc(shot["id"])} {sample["position"]}">'
                f'<figcaption>{sample["position"]} · 请求 {sample["requested_seconds"]:.6f}s'
                f' · 实际帧 {sample["frame_seconds"]:.6f}s{cap_note}</figcaption></figure>'
            )
        frames = "".join(frame_figs)
        details = " · ".join(esc(shot[key]) for key in ("subject", "action", "visual_note") if shot[key])
        sections.append(f'<section id="shot-{index:04d}"><h2>{index:02d} · {esc(shot["id"])}'
                        f' <small>{shot["start"]:.6f}–{shot["end"]:.6f}s</small></h2>'
                        f'<p>{details}</p><div class="frames">{frames}</div></section>')
    return ("<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\">"
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\' data:; style-src \'unsafe-inline\'">'
            f'<title>{esc(title)} · 静帧审查材料</title><style>'
            'body{margin:0;padding:28px;background:#121416;color:#e9e9e7;font:16px system-ui,sans-serif}'
            'main{max-width:1500px;margin:auto}h1{font-size:26px}h2{font-size:20px}'
            'small,p,figcaption{color:#c0c3c5}small{font-size:14px}section{margin:32px 0}'
            '.overview{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px}'
            '.overview a{color:inherit;text-decoration:none}.overview span{display:block;font-size:12px;'
            'padding-top:6px;overflow-wrap:anywhere}'
            '.frames{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}'
            'figure{margin:0}img{display:block;width:100%;height:auto;background:#000}'
            'figcaption{font-size:12px;margin-top:8px;overflow-wrap:anywhere}'
            'p{line-height:1.6;overflow-wrap:anywhere}@media(max-width:700px){.frames{grid-template-columns:1fr}}'
            f'</style><main><h1>{esc(title)} · 静帧审查材料</h1><p>{esc(LIMITS)}</p>'
            '<p>按镜头原顺序显示 start / mid / end；end 采用结束边界前的实际帧。低帧率或短镜头可能重复同一帧。'
            '完整画幅仅缩放显示，不裁切。请另行连续观看与听验当前视频。</p>'
            f'<p>源视频时长：{coverage["video_duration_seconds"]:.3f}s；'
            f'已列镜头区间：{ranges(coverage["listed_intervals"])}；'
            f'未覆盖区间：{ranges(coverage["uncovered_intervals"])}。区间覆盖不等于已完整审查。</p>'
            '<h2>所列镜头总览</h2><p>每镜复用 mid 帧；点击进入三帧明细。观察所列区间的色彩、构图与密度变化。</p>'
            '<nav class="overview" aria-label="镜头总览">' + "".join(overview) + '</nav>'
            + "".join(sections) + "</main></html>\n")


def build_review(episode, media, output, captions=None):
    episode = Path(episode).resolve()
    root = episode.parent
    raw = episode.read_bytes()
    packet_hash = hashlib.sha256(raw).hexdigest()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewError("The episode must contain valid UTF-8 JSON.") from exc
    if not isinstance(data, dict):
        raise ReviewError("The episode must be a JSON object.")
    media_arg, output_arg = Path(media), Path(output)
    if media_arg.is_absolute():
        raise ReviewError("--media must be a path relative to the episode directory.")
    media = (root / media_arg).resolve()
    if not media.is_relative_to(root) or not media.is_file():
        raise ReviewError("The source media must be an existing file inside the episode directory.")
    cues = None
    if captions is not None:
        cap_arg = Path(captions)
        cap_path = cap_arg.resolve() if cap_arg.is_absolute() else (root / cap_arg).resolve()
        cues = parse_srt(cap_path)
    # Relative outputs also use the episode directory, independent of cwd.
    output_arg = output_arg if output_arg.is_absolute() else root / output_arg
    if output_arg.exists() or output_arg.is_symlink():
        raise ReviewError("The output already exists; choose a new directory.")
    output = output_arg.resolve()
    if not output.is_relative_to(root):
        raise ReviewError("The output must remain inside the episode directory.")
    tools = {name: shutil.which(name) for name in ("ffmpeg", "ffprobe")}
    if not all(tools.values()):
        raise ReviewError("ffmpeg and ffprobe are required; no tool is installed automatically.")
    media_hash = sha256(media)
    versions = {name: run_tool([path, "-version"]).splitlines()[0] for name, path in tools.items()}
    stream, duration, times = probe_video(media, tools["ffprobe"])
    shots = shot_samples(data, duration, times)
    coverage = timeline_coverage(shots, duration)
    timeline = [{key: shot[key] for key in ("id", "start", "end")} for shot in shots]
    selected = sorted({sample["frame_index"] for shot in shots for sample in shot["samples"]})
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".visual-review-", dir=output.parent) as temporary:
        staging = Path(temporary)
        raw_frames, final_frames = staging / "extracted", staging / "frames"
        raw_frames.mkdir()
        final_frames.mkdir()
        expression = "+".join(f"eq(n\\,{index})" for index in selected)
        run_tool([tools["ffmpeg"], "-v", "error", "-nostdin", *INPUT_OPTIONS, "-i", str(media), "-map", "0:v:0",
                  "-an", "-sn", "-vf", "select=" + expression, "-fps_mode", "passthrough",
                  "-frames:v", str(len(selected)), "-threads", "1", "-c:v", "png",
                  str(raw_frames / "%08d.png")])
        extracted = sorted(raw_frames.glob("*.png"))
        if len(extracted) != len(selected) or any(path.stat().st_size == 0 for path in extracted):
            raise ReviewError("ffmpeg did not produce every selected frame; no review was published.")
        files, lookup = [], dict(zip(selected, extracted))
        for shot in shots:
            for sample in shot["samples"]:
                destination = staging / sample["file"]
                shutil.copyfile(lookup[sample["frame_index"]], destination)
                sample["sha256"] = sha256(destination)
                files.append({"file": sample["file"], "sha256": sample["sha256"]})
        shutil.rmtree(raw_frames)
        (staging / "index.html").write_text(
            render_html(str(data.get("title") or "视频"), shots, coverage, cues=cues),
            encoding="utf-8",
        )
        files.insert(0, {"file": "index.html", "sha256": sha256(staging / "index.html")})
        manifest = {
            "schema_version": 1, "kind": "static_visual_review", "status": "generated_for_review",
            "generated_at": datetime.now(timezone.utc).isoformat(), "limits": LIMITS,
            "episode": {"file": episode.name, "sha256": packet_hash, "path_base": "episode_directory",
                        "hash_scope": "original bytes at generation; later QA edits change this snapshot hash"},
            "timeline_sha256": hashlib.sha256(json_bytes(timeline)).hexdigest(),
            "timeline": timeline, "coverage": coverage,
            "media": {"file": media.relative_to(root).as_posix(), "sha256": media_hash,
                      "path_base": "episode_directory", "duration_seconds": duration,
                      "width": stream["width"], "height": stream["height"],
                      "geometry": stream["geometry"],
                      "frame_rate": stream.get("avg_frame_rate"), "video_stream_index": stream["index"]},
            "tools": versions, "shots": shots, "output_path_base": "review_directory",
            "output_directory": output.relative_to(root).as_posix(), "output_files": files,
        }
        (staging / "manifest.json").write_bytes(json_bytes(manifest))
        evidence = [{"file": (output.relative_to(root) / item["file"]).as_posix(), "sha256": item["sha256"]}
                    for item in [{"file": "manifest.json", "sha256": sha256(staging / "manifest.json")}, *files]]
        (staging / "gate-evidence.json").write_bytes(json_bytes(evidence))
        if sha256(episode) != packet_hash or sha256(media) != media_hash:
            raise ReviewError("Episode or media changed during extraction; rerun against stable inputs.")
        if output.exists() or output.is_symlink():
            raise ReviewError("The output appeared during extraction; it was not overwritten.")
        os.rename(staging, output)
    return manifest


def main_beat_board(argv):
    parser = argparse.ArgumentParser(
        prog="build_visual_review.py beat-board",
        description="Build an internal pre-render captioned beat review board from textless stills + captions.srt.",
    )
    parser.add_argument("--stills-dir", type=Path, required=True, help="directory of raw preflight stills with frame numbers")
    parser.add_argument("--captions", type=Path, required=True, help="actual synchronized captions.srt file")
    parser.add_argument("--output", type=Path, required=True, help="NEW output directory for beat-board.html/jpg/manifest.json")
    parser.add_argument("--fps", type=float, default=30.0, help="timeline frames per second (default: 30)")
    parser.add_argument("--frame-origin", type=int, choices=(0, 1), default=1, help="first frame index of t=0 (default: 1 for Blender)")
    parser.add_argument("--cols", type=int, default=3, help="columns in beat-board.jpg (default: 3)")
    parser.add_argument("--tile-width", type=int, default=640, help="per-tile width in pixels for beat-board.jpg (default: 640)")
    parser.add_argument("--title", type=str, default=None, help="optional human-readable title for the HTML board")
    parser.add_argument("--no-sheet", action="store_true", help="skip JPEG contact-sheet generation (HTML + manifest only)")
    args = parser.parse_args(argv)
    try:
        manifest = build_beat_board(
            args.stills_dir,
            args.captions,
            args.output,
            fps=args.fps,
            frame_origin=args.frame_origin,
            cols=args.cols,
            tile_width=args.tile_width,
            title=args.title,
            build_sheet=not args.no_sheet,
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({
        "status": manifest["review_status"],
        "output": str(Path(args.output).resolve()),
        "still_count": manifest["still_count"],
        "covered_cue_count": manifest["covered_cue_count"],
        "uncovered_cue_count": manifest["uncovered_cue_count"],
        "sheet_file": manifest["sheet_file"],
        "raw_stills_unmodified": manifest["raw_stills_unmodified"],
    }, ensure_ascii=False))
    return 0


def main(argv=None):
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv and raw_argv[0] == "beat-board":
        return main_beat_board(raw_argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--media", type=Path, required=True, help="video path relative to the episode directory")
    parser.add_argument("--output", type=Path, required=True,
                        help="NEW directory inside the episode directory; relative paths use that directory")
    parser.add_argument("--captions", type=Path, default=None,
                        help="optional synchronized captions.srt to display active spoken lines per sampled frame")
    args = parser.parse_args(raw_argv)
    try:
        manifest = build_review(args.episode, args.media, args.output, captions=args.captions)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({"status": manifest["status"], "output": manifest["output_directory"],
                      "review": "pending"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
