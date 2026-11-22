#!/usr/bin/env python3
"""Deterministic series cover typography compositor.

Reads locked font family, weights, exact per-ratio pixel sizes, margins, line gaps
and closed background-matched color presets from ``config/production-policy.json``
(``cover_typography``). Eliminates per-episode drift in font, size and color pairing.

Never silently substitutes another font family, never shrinks font size to force
overlong copy in, and never adds strokes, shadows, glows or backing boxes.
Actual full-resolution and phone-thumbnail inspection remain separate reviews.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "production-policy.json"
RATIO_ALIASES = {
    "3:4": "cover_3_4",
    "3x4": "cover_3_4",
    "cover_3_4": "cover_3_4",
    "4:3": "cover_4_3",
    "4x3": "cover_4_3",
    "cover_4_3": "cover_4_3",
    "16:9": "cover_16_9",
    "16x9": "cover_16_9",
    "cover_16_9": "cover_16_9",
}
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def load_spec(policy_path: Path = POLICY_PATH) -> dict:
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    spec = data.get("cover_typography")
    if not isinstance(spec, dict):
        raise ValueError(f"cover_typography missing from {policy_path}")
    return spec


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    if not isinstance(hex_color, str) or not HEX_RE.fullmatch(hex_color.strip()):
        raise ValueError(f"invalid hex color: {hex_color!r}")
    h = hex_color.strip().lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    def lin(v: float) -> float:
        s = max(0.0, min(1.0, v / 255.0))
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(luma_a: float, luma_b: float) -> float:
    hi = max(luma_a, luma_b)
    lo = min(luma_a, luma_b)
    return (hi + 0.05) / (lo + 0.05)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_font_path(font_spec: dict, explicit_font: Path | None = None) -> Path:
    if explicit_font is not None:
        if not explicit_font.is_file():
            raise FileNotFoundError(f"explicit font file not found: {explicit_font}")
        return explicit_font
    for raw in font_spec.get("candidates", []):
        p = Path(raw)
        if p.is_file():
            return p
    family = font_spec.get("family", "required font")
    raise FileNotFoundError(
        f"Locked cover font family {family!r} not found in configured candidates "
        f"(allow_fallback_family=false; install {family} or pass --font pointing to that family)."
    )


def load_truetype(font_path: Path, size: int, weight: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(font_path), size=size)
    if "VF" in font_path.name.upper() or hasattr(font, "set_variation_by_axes"):
        try:
            axes = font.get_variation_axes() if hasattr(font, "get_variation_axes") else []
            if axes:
                # Set wght axis cleanly when variable font exposes it
                vals = []
                for ax in axes:
                    name = (ax.get("name") or b"").decode("utf-8", errors="ignore").lower() if isinstance(ax.get("name"), bytes) else str(ax.get("name") or "").lower()
                    if "weight" in name or name == "wght":
                        vals.append(max(ax["minimum"], min(ax["maximum"], weight)))
                    else:
                        vals.append(ax["default"])
                font.set_variation_by_axes(vals)
        except Exception:
            pass
    return font


def parse_lines(title: str, question: str) -> tuple[str, list[str]]:
    clean_title = title.replace("\\n", "\n").strip()
    if not clean_title or "\n" in clean_title:
        raise ValueError("Main title must be a single non-empty line with no line breaks.")
    raw_q = question.replace("\\n", "\n").strip()
    q_lines = [ln.strip() for ln in raw_q.splitlines() if ln.strip()]
    if len(q_lines) != 2:
        raise ValueError(
            f"Question subtitle must be strictly 2 non-empty lines separated by \\n (got {len(q_lines)} line(s))."
        )
    return clean_title, q_lines


def measure_region_luma(img: Image.Image, box: tuple[int, int, int, int]) -> float:
    w, h = img.size
    x0 = max(0, min(w - 1, int(box[0])))
    y0 = max(0, min(h - 1, int(box[1])))
    x1 = max(x0 + 1, min(w, int(box[2])))
    y1 = max(y0 + 1, min(h, int(box[3])))
    crop = img.crop((x0, y0, x1, y1)).convert("RGB")
    # Sample on a small grid for deterministic, fast mean relative luminance
    small = crop.resize((max(1, min(64, crop.width)), max(1, min(64, crop.height))), Image.Resampling.BILINEAR)
    raw_bytes = small.tobytes()
    n_px = len(raw_bytes) // 3
    if n_px <= 0:
        return 0.5
    return sum(relative_luminance((raw_bytes[i], raw_bytes[i + 1], raw_bytes[i + 2])) for i in range(0, n_px * 3, 3)) / n_px


def compose_cover(
    raw_image: Path,
    ratio_key: str,
    title: str,
    question: str,
    output: Path,
    report: Path,
    *,
    palette: str | None = None,
    lang: str = "zh",
    font_path: Path | None = None,
    policy_path: Path = POLICY_PATH,
    skip_contrast_check: bool = False,
) -> dict:
    spec = load_spec(policy_path)
    if report.exists():
        raise FileExistsError(f"report already exists; use a new receipt filename: {report}")
    if ratio_key not in spec["ratios"]:
        raise ValueError(f"unsupported ratio {ratio_key!r}; expected one of {sorted(spec['ratios'])}")
    if lang not in spec["fonts"]:
        raise ValueError(f"unsupported lang {lang!r}; expected one of {sorted(spec['fonts'])}")

    palette_id = palette or spec["default_palette"]
    presets = spec["color_presets"]
    if palette_id not in presets:
        raise ValueError(
            f"palette {palette_id!r} is not in locked cover_typography.color_presets: {sorted(presets)}"
        )
    preset = presets[palette_id]
    main_hex = preset["main_hex"].upper()
    sub_hex = preset["subtitle_hex"].upper()
    main_rgb = hex_to_rgb(main_hex)
    sub_rgb = hex_to_rgb(sub_hex)

    clean_title, q_lines = parse_lines(title, question)
    ratio_cfg = spec["ratios"][ratio_key]
    lang_sizes = ratio_cfg[lang]
    font_cfg = spec["fonts"][lang]
    resolved_font = resolve_font_path(font_cfg, explicit_font=font_path)

    out_w, out_h = int(ratio_cfg["canvas"][0]), int(ratio_cfg["canvas"][1])
    margin_x = int(ratio_cfg["margin_x"])
    margin_y = int(ratio_cfg["margin_y"])
    max_text_w = int(ratio_cfg["max_text_width"])
    main_size = int(lang_sizes["main_size_px"])
    sub_size = int(lang_sizes["subtitle_size_px"])
    tier_gap = int(lang_sizes["tier_gap_px"])
    line_gap = int(lang_sizes["line_gap_px"])
    main_weight = int(font_cfg["main_weight"])
    sub_weight = int(font_cfg["subtitle_weight"])

    f_main = load_truetype(resolved_font, main_size, main_weight)
    f_sub = load_truetype(resolved_font, sub_size, sub_weight)

    raw_img = Image.open(raw_image).convert("RGB")
    # Refuse aspect ratio mismatch that would silently stretch the artwork (>2% tolerance)
    src_ar = raw_img.width / raw_img.height
    dst_ar = out_w / out_h
    if abs(src_ar - dst_ar) / dst_ar > 0.02:
        raise ValueError(
            f"raw image aspect ratio {raw_img.width}x{raw_img.height} ({src_ar:.4f}) does not match "
            f"{ratio_key} {out_w}x{out_h} ({dst_ar:.4f}); compose each ratio independently rather than stretching."
        )

    bg_rgb = raw_img.resize((out_w, out_h), Image.Resampling.LANCZOS)
    text_layer = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    # Measure exact text boxes BEFORE rendering; enforce no_auto_shrink!
    b_main = draw.textbbox((margin_x, margin_y), clean_title, font=f_main)
    main_w = b_main[2] - b_main[0]
    if main_w > max_text_w:
        raise ValueError(
            f"Main title width {main_w}px exceeds locked max_text_width {max_text_w}px at fixed {main_size}px "
            f"(no_auto_shrink=true; shorten main title rather than shrinking font size)."
        )

    y_sub1 = b_main[3] + tier_gap
    b_sub1 = draw.textbbox((margin_x, y_sub1), q_lines[0], font=f_sub)
    y_sub2 = b_sub1[3] + line_gap
    b_sub2 = draw.textbbox((margin_x, y_sub2), q_lines[1], font=f_sub)

    for idx, (ln, bb) in enumerate(((q_lines[0], b_sub1), (q_lines[1], b_sub2)), 1):
        lw = bb[2] - bb[0]
        if lw > max_text_w:
            raise ValueError(
                f"Subtitle line {idx} ({ln!r}) width {lw}px exceeds locked max_text_width {max_text_w}px at fixed "
                f"{sub_size}px (no_auto_shrink=true; tighten wording or break lines cleanly rather than shrinking font size)."
            )

    # Measure real upper-left background luminance and contrast under actual text footprints!
    main_bg_luma = measure_region_luma(bg_rgb, b_main)
    sub_union = (
        min(b_sub1[0], b_sub2[0]),
        min(b_sub1[1], b_sub2[1]),
        max(b_sub1[2], b_sub2[2]),
        max(b_sub1[3], b_sub2[3]),
    )
    sub_bg_luma = measure_region_luma(bg_rgb, sub_union)
    region_luma = 0.5 * (main_bg_luma + sub_bg_luma)

    main_cr = contrast_ratio(relative_luminance(main_rgb), main_bg_luma)
    sub_cr = contrast_ratio(relative_luminance(sub_rgb), sub_bg_luma)

    contrast_cfg = spec["contrast"]
    bg_tone = preset["background_tone"]
    if not skip_contrast_check:
        if bg_tone == "light" and region_luma < float(contrast_cfg["light_bg_min_luma"]):
            raise ValueError(
                f"Light-background palette {palette_id!r} cannot be placed on a dark upper-left region "
                f"(measured luma={region_luma:.3f} < {contrast_cfg['light_bg_min_luma']}); "
                f"choose a dark preset ('dark_terracotta' or 'dark_ocean_gold') or brighten upper-left background."
            )
        if bg_tone == "dark" and region_luma > float(contrast_cfg["dark_bg_max_luma"]):
            raise ValueError(
                f"Dark-background palette {palette_id!r} cannot be placed on a bright upper-left region "
                f"(measured luma={region_luma:.3f} > {contrast_cfg['dark_bg_max_luma']}); "
                f"choose a light preset ('daylight_terracotta' or 'daylight_navy')."
            )
        if main_cr < float(contrast_cfg["main_min"]):
            raise ValueError(
                f"Main title contrast {main_cr:.2f}:1 below locked minimum {contrast_cfg['main_min']}:1 "
                f"for palette {palette_id!r} ({main_hex}) on background luma={main_bg_luma:.3f}."
            )
        if sub_cr < float(contrast_cfg["subtitle_min"]):
            raise ValueError(
                f"Subtitle contrast {sub_cr:.2f}:1 below locked minimum {contrast_cfg['subtitle_min']}:1 "
                f"for palette {palette_id!r} ({sub_hex}) on background luma={sub_bg_luma:.3f}."
            )

    # Flat fill only: strictly zero strokes, shadows, glows or backing boxes
    draw.text((margin_x, margin_y), clean_title, font=f_main, fill=main_rgb + (255,))
    draw.text((margin_x, y_sub1), q_lines[0], font=f_sub, fill=sub_rgb + (255,))
    draw.text((margin_x, y_sub2), q_lines[1], font=f_sub, fill=sub_rgb + (255,))

    composed = Image.alpha_composite(bg_rgb.convert("RGBA"), text_layer).convert("RGB")
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)

    bg_out = output.with_name(f"{output.stem}-background.png")
    txt_out = output.with_name(f"{output.stem}-text-layer.png")
    pw = int(ratio_cfg["mobile_preview_width_px"])
    ph = int(round(out_h * pw / out_w))
    preview_out = output.with_name(f"{output.stem}-preview-{pw}w.png")

    composed.save(output, "PNG", optimize=True)
    bg_rgb.save(bg_out, "PNG", optimize=True)
    text_layer.save(txt_out, "PNG", optimize=True)
    composed.resize((pw, ph), Image.Resampling.LANCZOS).save(preview_out, "PNG", optimize=True)

    typography_record = {
        "spec_version": spec["version"],
        "lang": lang,
        "font_family": font_cfg["family"],
        "font_file": str(resolved_font),
        "main_weight": main_weight,
        "subtitle_weight": sub_weight,
        "main_size_px": main_size,
        "subtitle_size_px": sub_size,
        "margin_x": margin_x,
        "margin_y": margin_y,
        "tier_gap_px": tier_gap,
        "line_gap_px": line_gap,
        "palette": palette_id,
        "main_color_hex": main_hex,
        "subtitle_color_hex": sub_hex,
        "main_lines": 1,
        "subtitle_lines": 2,
        "stroke_shadow_or_backing": False,
    }

    receipt = {
        "schema_version": 1,
        "tool": "scripts/compose_cover.py",
        "ratio_key": ratio_key,
        "canvas": [out_w, out_h],
        "title": clean_title,
        "question_lines": q_lines,
        "typography": typography_record,
        "measurements": {
            "main_bbox": list(b_main),
            "subtitle_bboxes": [list(b_sub1), list(b_sub2)],
            "main_bg_luma": round(main_bg_luma, 4),
            "subtitle_bg_luma": round(sub_bg_luma, 4),
            "region_luma_mean": round(region_luma, 4),
            "main_contrast_ratio": round(main_cr, 2),
            "subtitle_contrast_ratio": round(sub_cr, 2),
        },
        "files": {
            "raw_source": {"file": str(raw_image), "sha256": sha256_file(raw_image)},
            "export": {"file": str(output), "sha256": sha256_file(output)},
            "background": {"file": str(bg_out), "sha256": sha256_file(bg_out)},
            "text_layer": {"file": str(txt_out), "sha256": sha256_file(txt_out)},
            "mobile_preview": {
                "file": str(preview_out),
                "sha256": sha256_file(preview_out),
                "display_width_px": pw,
                "display_height_px": ph,
                "display_context": "phone_thumbnail",
            },
        },
        "note": "Composition receipt proves locked typography/color parameters only; actual full-res and phone-thumbnail art review remain required.",
    }
    report.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def cmd_list_palettes(args: argparse.Namespace) -> int:
    spec = load_spec(args.policy)
    out = {
        "version": spec["version"],
        "default_palette": spec["default_palette"],
        "fonts": {k: {"family": v["family"], "main_weight": v["main_weight"], "subtitle_weight": v["subtitle_weight"]} for k, v in spec["fonts"].items()},
        "ratios": spec["ratios"],
        "color_presets": spec["color_presets"],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_compose(args: argparse.Namespace) -> int:
    ratio_key = RATIO_ALIASES.get(args.ratio.strip().lower())
    if not ratio_key:
        print(f"ERROR: unsupported --ratio {args.ratio!r}; use 3:4, 4:3 or 16:9", file=sys.stderr)
        return 2
    try:
        receipt = compose_cover(
            raw_image=args.raw_image,
            ratio_key=ratio_key,
            title=args.title,
            question=args.question,
            output=args.output,
            report=args.report,
            palette=args.palette,
            lang=args.lang,
            font_path=args.font,
            policy_path=args.policy,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "report": str(args.report),
        "export": receipt["files"]["export"],
        "mobile_preview": receipt["files"]["mobile_preview"],
        "typography": receipt["typography"],
        "measurements": receipt["measurements"],
    }, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list-palettes", help="Print locked cover fonts, pixel sizes and color presets.")
    p_list.add_argument("--policy", type=Path, default=POLICY_PATH)
    p_list.set_defaults(func=cmd_list_palettes)

    p_comp = sub.add_parser("compose", help="Compose a series cover using locked typography and color presets.")
    p_comp.add_argument("raw_image", type=Path, help="Clean text-free cover artwork matching the requested aspect ratio.")
    p_comp.add_argument("--ratio", required=True, help="Target ratio: 3:4 (1080x1440), 4:3 (1440x1080), or 16:9 (1920x1080).")
    p_comp.add_argument("--title", required=True, help="1-line topic-noun main title.")
    p_comp.add_argument("--question", required=True, help=r"2-line question subtitle separated with \n.")
    p_comp.add_argument("--palette", default=None, help="Locked preset from cover_typography.color_presets (default: daylight_terracotta).")
    p_comp.add_argument("--lang", choices=("zh", "en"), default="zh", help="Language typography lock (zh or en).")
    p_comp.add_argument("--font", type=Path, default=None, help="Explicit path to a font file of the locked family.")
    p_comp.add_argument("--output", type=Path, required=True, help="Output PNG path.")
    p_comp.add_argument("--report", type=Path, required=True, help="New JSON receipt path (will not overwrite).")
    p_comp.add_argument("--policy", type=Path, default=POLICY_PATH)
    p_comp.set_defaults(func=cmd_compose)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
