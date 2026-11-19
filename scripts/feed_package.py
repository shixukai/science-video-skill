#!/usr/bin/env python3
"""Compose the 1080x1920 vertical feed package from an accepted 16:9 master.

The master keeps its picture, burned-in captions and sound. It is scaled to the
full canvas width (optionally zoomed with a recorded side crop) and centered,
and a persistent two-tier header (topic noun, then the film's question) is set
in the top band with flat series colors and no stroke, shadow or backing box.

The package is a delivery derivative. It does not reopen G5 approval; header
legibility, the first 5 s and any zoom crop still need actual phone-size
viewing, recorded under ``qa.feed_package`` with the file in
``deliverables.feed_package``.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_policy(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    policy = json.loads((root / "config/production-policy.json").read_text(encoding="utf-8"))
    return policy["feed_package"]


def find_font(policy, explicit=None):
    candidates = [explicit] if explicit else policy["font_candidates"]
    for item in candidates:
        if item and Path(item).is_file():
            return Path(item)
    raise ValueError("no legally available CJK bold font found; pass --font <path to the series font>")


def _even(value):
    value = int(round(value))
    return value - (value % 2)


def layout(policy, src_w, src_h, zoom):
    """Return picture geometry for the given zoom inside the package canvas."""
    if not (1.0 <= zoom <= policy["max_zoom"]):
        raise ValueError("zoom must be between 1.0 and feed_package.max_zoom")
    cw, ch = policy["canvas"]
    scaled_w = _even(cw * zoom)
    scaled_h = _even(scaled_w * src_h / src_w)
    top = _even(policy["picture_center_y"] - scaled_h / 2)
    crop_each_side = (scaled_w - cw) / 2 / scaled_w
    return {"scaled_w": scaled_w, "scaled_h": scaled_h, "picture_top": top,
            "picture_bottom": top + scaled_h, "crop_fraction_each_side": round(crop_each_side, 4)}


def _text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def render_header(policy, topic, question_lines, font_path, picture_top, out_png):
    from PIL import Image, ImageDraw, ImageFont
    h = policy["header"]
    cw, ch = policy["canvas"]
    topic_font = ImageFont.truetype(str(font_path), h["topic_size"])
    question_font = ImageFont.truetype(str(font_path), h["question_size"])
    img = Image.new("RGB", (cw, ch), h["band_color"])
    draw = ImageDraw.Draw(img)
    for text, font in [(topic, topic_font)] + [(line, question_font) for line in question_lines]:
        if _text_width(draw, text, font) > h["max_width"]:
            raise ValueError("header line too wide; break the question by meaning instead of shrinking type: " + text)
    q_line = round(h["question_size"] * h["line_spacing"])
    block = h["topic_size"] + (h["topic_question_gap"] + q_line * len(question_lines) if question_lines else 0)
    top = picture_top - h["gap_above_picture"] - block
    if top < h["top_safe_y"]:
        raise ValueError("header does not fit between the top safe area and the picture; shorten it or lower the zoom")
    draw.text((h["left_x"], top), topic, font=topic_font, fill=h["topic_color"])
    y = top + h["topic_size"] + h["topic_question_gap"]
    for line in question_lines:
        draw.text((h["left_x"], y), line, font=question_font, fill=h["question_color"])
        y += q_line
    img.save(out_png)
    return {"top": top, "bottom": top + block}


def _probe(path):
    run = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
                         capture_output=True, check=True, timeout=60)
    meta = json.loads(run.stdout.decode("utf-8", "replace"))
    video = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in meta.get("streams", []) if s.get("codec_type") == "audio"), None)
    if video is None:
        raise ValueError("master has no video stream")
    return meta, video, audio


def compose(master, topic, question, output, policy, zoom=None, font=None, report_path=None, crf=18):
    master, output = Path(master), Path(output)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required for the feed package")
    if output.exists():
        raise ValueError("output exists; use a new filename")
    topic = (topic or "").strip()
    lines = [l.strip() for l in (question or "").replace("\\n", "\n").split("\n") if l.strip()]
    if not topic or not lines:
        raise ValueError("topic noun and question are both required")
    if len(lines) > policy["header"]["max_question_lines"]:
        raise ValueError("question has more lines than feed_package.header.max_question_lines")
    zoom = policy["default_zoom"] if zoom is None else zoom
    meta, vstream, astream = _probe(master)
    src_w, src_h = int(vstream["width"]), int(vstream["height"])
    if abs(src_w / src_h - 16 / 9) > 0.01:
        raise ValueError("feed package expects a 16:9 master")
    geo = layout(policy, src_w, src_h, zoom)
    font_path = find_font(policy, font)
    rate = vstream.get("avg_frame_rate") or vstream.get("r_frame_rate") or "24/1"
    cw, ch = policy["canvas"]
    with tempfile.TemporaryDirectory(prefix="feed-package-") as tmp:
        bg = Path(tmp) / "header.png"
        header = render_header(policy, topic, lines, font_path, geo["picture_top"], bg)
        vf = (f"[1:v]scale={geo['scaled_w']}:{geo['scaled_h']}:flags=lanczos,"
              f"crop={cw}:{geo['scaled_h']}:(iw-{cw})/2:0,setsar=1[pic];"
              f"[0:v][pic]overlay=0:{geo['picture_top']}:shortest=1,format=yuv420p[v]")
        args = ["ffmpeg", "-v", "error", "-loop", "1", "-framerate", rate, "-i", str(bg), "-i", str(master),
                "-filter_complex", vf, "-map", "[v]"]
        if astream is not None:
            args += ["-map", "1:a:0", "-c:a", "copy"]
        args += ["-r", rate, "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                 "-movflags", "+faststart", str(output)]
        subprocess.run(args, check=True, capture_output=True, timeout=7200)
    _, out_v, out_a = _probe(output)
    base = Path(report_path).resolve().parent if report_path else output.resolve().parent

    def rel(path):
        return Path(os.path.relpath(Path(path).resolve(), base)).as_posix()

    return {
        "schema_version": 1,
        "tool": "scripts/feed_package.py",
        "source_master": {"file": rel(master), "sha256": sha256_file(master), "width": src_w, "height": src_h},
        "output": {"file": rel(output), "sha256": sha256_file(output),
                   "width": out_v.get("width"), "height": out_v.get("height"),
                   "frame_rate": out_v.get("avg_frame_rate"), "audio_stream": out_a is not None},
        "header": {"topic": topic, "question_lines": lines, "font": str(font_path),
                   "font_sha256": sha256_file(font_path), "box_y": [header["top"], header["bottom"]]},
        "geometry": dict(geo, zoom=zoom),
        "phone_view": {"status": "pending", "reviewer": "", "header_legible": None,
                       "first_5s_observation": "", "crop_check": "not_applicable" if zoom == 1.0 else "pending",
                       "observation": ""},
        "limits": "Derivative of the accepted master; does not reopen G5. Phone-size viewing is still required.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("compose", help="compose the vertical feed package from an accepted 16:9 master")
    c.add_argument("master", type=Path)
    c.add_argument("--topic", required=True, help="topic noun, matching the cover main title")
    c.add_argument("--question", required=True, help="the film's question; separate 1-2 lines with \\n")
    c.add_argument("--output", type=Path, required=True)
    c.add_argument("--report", type=Path, required=True, help="new JSON report path")
    c.add_argument("--zoom", type=float, help="1.0 (default) to feed_package.max_zoom; >1 crops the sides")
    c.add_argument("--font", help="path to a legally available CJK bold font")
    args = parser.parse_args(argv)
    try:
        policy = load_policy()
        if args.report.exists():
            raise ValueError("report exists; use a new receipt filename")
        report = compose(args.master, args.topic, args.question, args.output, policy,
                         args.zoom, args.font, args.report)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(args.report), "output": report["output"]}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
