#!/usr/bin/env python3
"""Compose the 1080x1920 vertical feed package from an accepted 16:9 master.

Two caption modes:

- **caption band** (default when a textless master exists): pass the textless
  master exported from the accepted timeline plus the formal caption file with
  ``--captions``. Captions are re-wrapped for the narrower band below the
  picture (never splitting numbers from units or starting a line with closing
  punctuation), rendered larger than the scaled burned-in captions, and keep
  the caption file's approved timing.
- **burned-in captions**: pass the captioned master without ``--captions``; it
  is scaled to the full width and centered.

In both modes a persistent two-tier header (topic noun, then the film's
question) sits in the top band with flat palette colors and no stroke, shadow
or backing box. ``--ending-question`` swaps the question lines for one genuine
experience question from ``--ending-from`` seconds.

The package is a delivery derivative. It does not reopen G5 approval; header
and caption legibility, line breaks, the first 5 s and any zoom crop still need
actual phone-size viewing, recorded under ``qa.feed_package`` with the file in
``deliverables.feed_package``.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

CLOSING = set("，。！？、；：,.!?;:”’）)》」』】…—%")
OPENING = set("“‘（(《「『【")
CJK_UNITS = ("摄氏度", "毫米", "厘米", "微米", "纳米", "千米", "公里", "毫升", "千克", "公斤", "千瓦", "兆帕",
             "赫兹", "分钟", "小时", "米", "升", "克", "吨", "度", "秒", "倍", "伏", "瓦", "帕", "层", "次", "年", "天")
NUMBER_RE = re.compile(
    r"[-+±~]?\d+(?:[.,]\d+)*(?:\s*(?:%|‰|°C|℃|°|" + "|".join(CJK_UNITS) +
    r"|[A-Za-zμµΩ]+(?:/[A-Za-zμµΩ]+)?[²³]?))?")
LATIN_RE = re.compile(r"[A-Za-zμµΩ]+(?:[-'’/][A-Za-z]+)*[²³]?")


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


def relative_luminance(hex_color):
    h = hex_color.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast_ratio(a, b):
    la, lb = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check_palette(policy, name):
    """Return the palette and its contrast record; refuse glaring or unreadable night combinations."""
    palettes = policy["palettes"]
    if name not in palettes:
        raise ValueError("unknown palette %s; choose one of %s" % (name, "/".join(palettes)))
    pal = palettes[name]
    rules = policy["contrast"]
    record = {"band_relative_luminance": round(relative_luminance(pal["band"]), 4)}
    for role in ("topic", "question", "caption"):
        record[role] = round(contrast_ratio(pal["band"], pal[role]), 2)
    if name not in rules["exempt_palettes"]:
        problems = []
        if record["band_relative_luminance"] > rules["band_max_relative_luminance"]:
            problems.append("band too bright for night viewing")
        for role in ("topic", "question", "caption"):
            if record[role] < rules[role + "_min"]:
                problems.append("%s contrast %.2f below %.1f" % (role, record[role], rules[role + "_min"]))
            if record[role] > rules["text_max"]:
                problems.append("%s contrast %.2f above glare limit %.1f" % (role, record[role], rules["text_max"]))
        if problems:
            raise ValueError("palette %s rejected: %s" % (name, "; ".join(problems)))
    return pal, record


def _even(value):
    value = int(round(value))
    return value - (value % 2)


# ---------------------------------------------------------------------------
# Captions: parsing and wrapping
# ---------------------------------------------------------------------------

def _ts(h, m, s, frac):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(frac.ljust(3, "0")[:3]) / 1000


def parse_captions(path):
    """Return [(start, end, text)] from SRT/VTT/ASS; source line breaks become spaces for re-wrapping."""
    text = Path(path).read_text(encoding="utf-8-sig")
    cues = []
    dialogue = re.findall(r"^Dialogue:[^,]*,(\d+):(\d{2}):(\d{2})\.(\d{2}),(\d+):(\d{2}):(\d{2})\.(\d{2}),"
                          r"(?:[^,]*,){6}(.*)$", text, re.M)
    if dialogue:
        for h1, m1, s1, c1, h2, m2, s2, c2, body in dialogue:
            body = re.sub(r"\{[^}]*\}", "", body).replace("\\N", " ").replace("\\n", " ")
            cues.append((_ts(h1, m1, s1, c1 + "0"), _ts(h2, m2, s2, c2 + "0"), body))
    else:
        pattern = re.compile(r"(?:(\d+):)?(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*(?:(\d+):)?(\d{2}):(\d{2})[,.](\d{1,3})[^\n]*\n"
                             r"(.*?)(?:\n\s*\n|\Z)", re.S)
        for h1, m1, s1, f1, h2, m2, s2, f2, body in pattern.findall(text.replace("\r\n", "\n")):
            body = re.sub(r"<[^>]+>", "", body)
            cues.append((_ts(h1 or 0, m1, s1, f1), _ts(h2 or 0, m2, s2, f2), body))
    out = []
    for start, end, body in cues:
        body = re.sub(r"\s*\n\s*", " ", body).strip()
        # Drop spaces between CJK characters introduced by joined source lines.
        body = re.sub(r"(?<=[\u3000-\u9fff\uff00-\uffef])\s+(?=[\u3000-\u9fff\uff00-\uffef])", "", body)
        if body and end > start:
            out.append((round(start, 3), round(end, 3), body))
    if not out:
        raise ValueError("no SRT/VTT/ASS cues found in caption file")
    out.sort()
    for (a0, a1, _), (b0, _, _) in zip(out, out[1:]):
        if b0 < a1 - 0.001:
            raise ValueError("overlapping caption cues at %.3f s; fix the formal caption source" % b0)
    return out


def tokenize(text):
    """Split into unbreakable tokens: numbers with units, Latin words, single CJK chars; glue punctuation."""
    tokens, i = [], 0
    while i < len(text):
        m = NUMBER_RE.match(text, i) or LATIN_RE.match(text, i)
        if m and m.end() > i:
            tokens.append(m.group(0))
            i = m.end()
        else:
            tokens.append(text[i])
            i += 1
    glued = []
    for tok in tokens:
        if glued and (tok in CLOSING or (tok.isspace() and glued[-1].isspace())):
            glued[-1] += tok
        elif glued and glued[-1] and glued[-1][-1] in OPENING:
            glued[-1] += tok
        else:
            glued.append(tok)
    return glued


def wrap(text, measure, max_width, max_lines):
    """Break into at most max_lines lines that each fit max_width; prefer balanced breaks after punctuation."""
    tokens = tokenize(text)
    full = "".join(tokens).strip()
    if measure(full) <= max_width:
        return [full]
    if max_lines < 2:
        raise ValueError("caption too wide for one line: " + full)
    best = None
    for k in range(1, len(tokens)):
        a, b = "".join(tokens[:k]).strip(), "".join(tokens[k:]).strip()
        if not a or not b:
            continue
        wa, wb = measure(a), measure(b)
        if wa > max_width or wb > max_width:
            continue
        score = max(wa, wb) - (0.5 * max_width if a[-1] in CLOSING else 0)
        if best is None or score < best[0]:
            best = (score, [a, b])
    if best is None:
        raise ValueError("caption needs more than %d lines in the caption band; re-segment the formal caption "
                         "source instead of shrinking type: %s" % (max_lines, full))
    return best[1]


def _units(text):
    return len(re.findall(r"[\u3400-\u9fff]", text)) + len(re.findall(r"[A-Za-z0-9]+", text)) or 1


def fit_cue(start, end, text, measure, max_width, max_lines, depth=0):
    """Wrap a cue; if it is too long, split it at the most central punctuation and time the parts proportionally.

    Returns [(start, end, lines, split_flag)]. Split timing is an estimate from spoken units and is flagged
    for the actual phone-size caption check.
    """
    try:
        return [(start, end, wrap(text, measure, max_width, max_lines), depth > 0)]
    except ValueError:
        if depth >= 3:
            raise
    tokens = tokenize(text)
    total = _units(text)
    best = None
    for k in range(1, len(tokens)):
        a = "".join(tokens[:k]).strip()
        b = "".join(tokens[k:]).strip()
        if a and b and a[-1] in CLOSING:
            balance = abs(_units(a) / total - 0.5)
            if best is None or balance < best[0]:
                best = (balance, a, b)
    if best is None:
        raise ValueError("caption needs more than %d lines in the caption band and has no punctuation to split at; "
                         "re-segment the formal caption source instead of shrinking type: %s" % (max_lines, text))
    _, a, b = best
    mid = round(start + (end - start) * _units(a) / total, 3)
    return (fit_cue(start, mid, a, measure, max_width, max_lines, depth + 1) +
            fit_cue(mid, end, b, measure, max_width, max_lines, depth + 1))


# ---------------------------------------------------------------------------
# Layout and rendering
# ---------------------------------------------------------------------------

def layout(policy, src_w, src_h, zoom, caption_band=False):
    """Return picture geometry for the given zoom and caption mode inside the package canvas."""
    if not (1.0 <= zoom <= policy["max_zoom"]):
        raise ValueError("zoom must be between 1.0 and feed_package.max_zoom")
    cw, _ = policy["canvas"]
    scaled_w = _even(cw * zoom)
    scaled_h = _even(scaled_w * src_h / src_w)
    center = policy["caption_band"]["picture_center_y"] if caption_band else policy["picture_center_y"]
    top = _even(center - scaled_h / 2)
    geo = {"mode": "caption_band" if caption_band else "burned_in_captions",
           "scaled_w": scaled_w, "scaled_h": scaled_h, "picture_top": top, "picture_bottom": top + scaled_h,
           "crop_fraction_each_side": round((scaled_w - cw) / 2 / scaled_w, 4)}
    if caption_band:
        band = policy["caption_band"]
        line_h = round(band["size"] * band["line_spacing"])
        top_y = geo["picture_bottom"] + band["gap_below_picture"]
        baseline_box = top_y + line_h * band["max_lines"]
        if baseline_box > band["bottom_safe_y"]:
            raise ValueError("caption band does not fit above the bottom safe area; lower the zoom")
        geo.update(caption_top=top_y, caption_bottom=baseline_box, caption_line_h=line_h)
    return geo


def _text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _load_bold_font(image_font_mod, font_path, size, weight=700):
    """Load font and pin variable-font weight axis to bold when available."""
    font = image_font_mod.truetype(str(font_path), size)
    if hasattr(font, "get_variation_axes") and hasattr(font, "set_variation_by_axes"):
        try:
            axes = font.get_variation_axes() or []
            if axes:
                vals = []
                for ax in axes:
                    raw_name = ax.get("name")
                    name = (
                        raw_name.decode("utf-8", errors="ignore").lower()
                        if isinstance(raw_name, bytes)
                        else str(raw_name or "").lower()
                    )
                    if "weight" in name or name == "wght":
                        vals.append(max(ax["minimum"], min(ax["maximum"], weight)))
                    else:
                        vals.append(ax["default"])
                font.set_variation_by_axes(vals)
        except Exception:
            pass
    return font


class Renderer:
    def __init__(self, policy, font_path, palette):
        from PIL import Image, ImageDraw, ImageFont
        self.Image, self.ImageDraw = Image, ImageDraw
        self.policy = policy
        self.palette = palette
        h = policy["header"]
        self.topic_font = _load_bold_font(ImageFont, font_path, h["topic_size"], weight=700)
        self.question_font = _load_bold_font(ImageFont, font_path, h["question_size"], weight=700)
        self.caption_font = _load_bold_font(ImageFont, font_path, policy["caption_band"]["size"], weight=700)
        self._probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))

    def width(self, text, font):
        return _text_width(self._probe, text, font)

    def caption_width(self, text):
        return self.width(text, self.caption_font)

    def header_box(self, question_lines, picture_top):
        h = self.policy["header"]
        q_line = round(h["question_size"] * h["line_spacing"])
        block = h["topic_size"] + h["topic_question_gap"] + q_line * len(question_lines)
        top = picture_top - h["gap_above_picture"] - block
        if top < h["top_safe_y"]:
            raise ValueError("header does not fit between the top safe area and the picture; shorten it or lower the zoom")
        return top, top + block, q_line

    def check_header(self, topic, question_lines):
        h = self.policy["header"]
        for text, font in [(topic, self.topic_font)] + [(line, self.question_font) for line in question_lines]:
            if re.search(r"凭什么|凭啥", text):
                raise ValueError(
                    "banned confrontational interrogative ('凭什么'/'凭啥') is forbidden in vertical-feed headers; "
                    "rewrite in calm everyday Chinese: " + text
                )
            if self.width(text, font) > h["max_width"]:
                raise ValueError("header line too wide; break the question by meaning instead of shrinking type: " + text)

    def frame(self, topic, question_lines, caption_lines, geo, out_png):
        h = self.policy["header"]
        cw, ch = self.policy["canvas"]
        img = self.Image.new("RGB", (cw, ch), self.palette["band"])
        draw = self.ImageDraw.Draw(img)
        top, bottom, q_line = self.header_box(question_lines, geo["picture_top"])
        draw.text((h["left_x"], top), topic, font=self.topic_font, fill=self.palette["topic"])
        y = top + h["topic_size"] + h["topic_question_gap"]
        for line in question_lines:
            draw.text((h["left_x"], y), line, font=self.question_font, fill=self.palette["question"])
            y += q_line
        if caption_lines:
            band = self.policy["caption_band"]
            # Final-line baseline stays fixed; a one-line caption sits on the last line position.
            y = geo["caption_bottom"] - geo["caption_line_h"] * len(caption_lines)
            for line in caption_lines:
                draw.text((band["left_x"], y), line, font=self.caption_font, fill=self.palette["caption"])
                y += geo["caption_line_h"]
        img.save(out_png)
        return [top, bottom]


def _split_lines(text):
    return [l.strip() for l in (text or "").replace("\\n", "\n").split("\n") if l.strip()]


def build_states(duration, cues, ending_from):
    """Timeline of (start, end, caption_text_or_None, ending_flag) covering [0, duration]."""
    cuts = {0.0, round(duration, 3)}
    for start, end, _ in cues:
        cuts.update({max(0.0, min(duration, start)), max(0.0, min(duration, end))})
    if ending_from is not None:
        cuts.add(max(0.0, min(duration, ending_from)))
    edges = sorted(cuts)
    states = []
    for a, b in zip(edges, edges[1:]):
        if b - a <= 0:
            continue
        mid = (a + b) / 2
        text = next((t for s, e, t in cues if s <= mid < e), None)
        ending = ending_from is not None and mid >= ending_from
        if states and states[-1][2] == text and states[-1][3] == ending:
            states[-1] = (states[-1][0], b, text, ending)
        else:
            states.append((a, b, text, ending))
    return states


def _probe(path):
    run = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
                         capture_output=True, check=True, timeout=60)
    meta = json.loads(run.stdout.decode("utf-8", "replace"))
    video = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in meta.get("streams", []) if s.get("codec_type") == "audio"), None)
    if video is None:
        raise ValueError("master has no video stream")
    return meta, video, audio


def compose(master, topic, question, output, policy, zoom=None, font=None, report_path=None, crf=18,
            captions=None, ending_question=None, ending_from=None, palette=None):
    master, output = Path(master), Path(output)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required for the feed package")
    if output.exists():
        raise ValueError("output exists; use a new filename")
    topic = (topic or "").strip()
    lines = _split_lines(question)
    end_lines = _split_lines(ending_question)
    if not topic or not lines:
        raise ValueError("topic noun and question are both required")
    if len(lines) > policy["header"]["max_question_lines"] or len(end_lines) > policy["ending_question"]["max_lines"]:
        raise ValueError("question has more lines than the header allows")
    if bool(end_lines) != (ending_from is not None):
        raise ValueError("--ending-question and --ending-from must be given together")
    zoom = policy["default_zoom"] if zoom is None else zoom
    meta, vstream, astream = _probe(master)
    src_w, src_h = int(vstream["width"]), int(vstream["height"])
    if abs(src_w / src_h - 16 / 9) > 0.01:
        raise ValueError("feed package expects a 16:9 master")
    duration = float(meta["format"]["duration"])
    geo = layout(policy, src_w, src_h, zoom, caption_band=captions is not None)
    font_path = find_font(policy, font)
    palette = palette or policy["default_palette"]
    colors, contrast = check_palette(policy, palette)
    renderer = Renderer(policy, font_path, colors)
    renderer.check_header(topic, lines)
    if end_lines:
        renderer.check_header(topic, end_lines)
    band = policy["caption_band"]
    cues = parse_captions(captions) if captions else []
    fitted = []
    for start, end, text in cues:
        fitted += fit_cue(start, end, text, renderer.caption_width, band["max_width"], band["max_lines"])
    band_cues = [(s, e, "\n".join(l)) for s, e, l, _ in fitted]
    states = build_states(duration, band_cues, ending_from)
    rate = vstream.get("avg_frame_rate") or vstream.get("r_frame_rate") or "24/1"
    cw, _ = policy["canvas"]
    header_boxes = []
    with tempfile.TemporaryDirectory(prefix="feed-package-") as tmp:
        tmp = Path(tmp)
        rendered, listing = {}, ["ffconcat version 1.0"]
        for start, end, text, ending in states:
            key = (text, ending)
            if key not in rendered:
                png = tmp / ("state%04d.png" % len(rendered))
                header_boxes.append(renderer.frame(topic, end_lines if ending else lines,
                                                   text.split("\n") if text else None, geo, png))
                rendered[key] = png
            listing += ["file '%s'" % rendered[key].name, "duration %.3f" % (end - start)]
        listing.append("file '%s'" % rendered[(states[-1][2], states[-1][3])].name)
        concat = tmp / "states.ffconcat"
        concat.write_text("\n".join(listing) + "\n", encoding="utf-8")
        vf = (f"[0:v]fps={rate},format=rgb24[bg];"
              f"[1:v]scale={geo['scaled_w']}:{geo['scaled_h']}:flags=lanczos,"
              f"crop={cw}:{geo['scaled_h']}:(iw-{cw})/2:0,setsar=1[pic];"
              f"[bg][pic]overlay=0:{geo['picture_top']}:shortest=1,format=yuv420p[v]")
        args = ["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat), "-i", str(master),
                "-filter_complex", vf, "-map", "[v]"]
        if astream is not None:
            args += ["-map", "1:a:0", "-c:a", "copy"]
        args += ["-r", rate, "-t", "%.3f" % duration, "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                 "-movflags", "+faststart", str(output)]
        subprocess.run(args, check=True, capture_output=True, timeout=7200)
    _, out_v, out_a = _probe(output)
    base = Path(report_path).resolve().parent if report_path else output.resolve().parent

    def rel(path):
        return Path(os.path.relpath(Path(path).resolve(), base)).as_posix()

    return {
        "schema_version": 2,
        "tool": "scripts/feed_package.py",
        "source_master": {"file": rel(master), "sha256": sha256_file(master), "width": src_w, "height": src_h,
                          "kind": "textless_master" if captions else "captioned_master"},
        "output": {"file": rel(output), "sha256": sha256_file(output),
                   "width": out_v.get("width"), "height": out_v.get("height"),
                   "frame_rate": out_v.get("avg_frame_rate"), "audio_stream": out_a is not None},
        "palette": {"name": palette, "colors": {k: colors[k] for k in ("band", "topic", "question", "caption")},
                    "contrast": contrast},
        "header": {"topic": topic, "question_lines": lines, "font": str(font_path),
                   "font_sha256": sha256_file(font_path), "box_y": header_boxes[0] if header_boxes else None},
        "ending_question": {"lines": end_lines, "from_s": ending_from} if end_lines else None,
        "captions": ({"file": rel(captions), "sha256": sha256_file(captions), "source_cue_count": len(cues),
                      "band_cue_count": len(fitted),
                      "two_line_cues": sum(1 for f in fitted if len(f[2]) >= 2),
                      "split_cues_timing_estimated": [{"start": s, "end": e, "lines": l} for s, e, l, sp in fitted if sp],
                      "wrapped": [{"start": s, "end": e, "lines": l} for s, e, l, _ in fitted]}
                     if captions else None),
        "geometry": dict(geo, zoom=zoom),
        "phone_view": {"status": "pending", "reviewer": "", "header_legible": None,
                       "captions_legible_and_breaks_ok": None if captions else "not_applicable",
                       "first_5s_observation": "", "crop_check": "not_applicable" if zoom == 1.0 else "pending",
                       "observation": ""},
        "limits": "Derivative of the accepted master; does not reopen G5. Phone-size viewing is still required.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("compose", help="compose the vertical feed package from an accepted 16:9 master")
    c.add_argument("master", type=Path, help="textless master with --captions, otherwise the captioned master")
    c.add_argument("--topic", required=True, help="topic noun, matching the cover main title")
    c.add_argument("--question", required=True, help="the film's question; separate 1-2 lines with \\n")
    c.add_argument("--captions", type=Path, help="formal SRT/VTT/ASS caption file; renders the caption band")
    c.add_argument("--ending-question", help="one genuine experience question shown in the header at the end")
    c.add_argument("--ending-from", type=float, help="seconds; not earlier than ending.answer_time_s")
    c.add_argument("--output", type=Path, required=True)
    c.add_argument("--report", type=Path, required=True, help="new JSON report path")
    c.add_argument("--zoom", type=float, help="1.0 (default) to feed_package.max_zoom; >1 crops the sides")
    c.add_argument("--font", help="path to a legally available CJK bold font")
    c.add_argument("--palette", help="feed_package.palettes key; default feed_package.default_palette")
    args = parser.parse_args(argv)
    try:
        policy = load_policy()
        if args.report.exists():
            raise ValueError("report exists; use a new receipt filename")
        report = compose(args.master, args.topic, args.question, args.output, policy, args.zoom, args.font,
                         args.report, captions=args.captions, ending_question=args.ending_question,
                         ending_from=args.ending_from, palette=args.palette)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(args.report), "output": report["output"]}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
