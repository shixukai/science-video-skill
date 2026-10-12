"""Fail-closed label permission and actual-overlay evidence checks.

This validates evidence bindings, not the truth of a user's consent or a human's
visual observations. No OCR/perceptual approval is claimed and no older guard is
replaced. Scientific labels and ordinary captions do not need label permission.
"""
import json
import math
import re
import unicodedata

MARKING_PURPOSES = {"attribution", "license", "ai_simulation", "production_meta",
                    "watermark", "internal_qa", "production_excuse", "material_defect"}
VISUAL_SURFACES = {"frame", "caption", "cover"}
ZONES = {"subtitles", "corners", "opening", "closing", "in_art", "body"}


def obj(value):
    return value if isinstance(value, dict) else {}


def seq(value):
    return value if isinstance(value, list) else []


def text(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {
        "pending", "todo", "tbd", "待验", "未验", "unknown"}


def marking_cue(value):
    """Supplementary cues only; actual purpose/source inspection is mandatory."""
    raw = unicodedata.normalize("NFKC", str(value)).casefold()
    raw = "".join(c for c in raw if not unicodedata.category(c).startswith("C"))
    ai = r"(?<![a-z])a\s*[._-]?\s*i(?![a-z])|(?<![a-z])aigc(?![a-z])|人工智能"
    return bool(re.search(r"(?:" + ai + r").{0,16}(?:模拟|模擬|生成|绘|繪|制作|製作|合成|辅助|輔助|示意|simulat|generat|art\b|drawn|made|creat|assist)", raw)
                or re.search(r"(?:created|generated|made|drawn|illustrated)\s+(?:with|by|using)\s+(?:generative\s+)?(?:" + ai + r")", raw)
                or re.search(r"(?:(?:本片|视频|製作|制作|版权|版權).{0,8}水印|(?:video|production|copyright|creator)[ -]*watermark|制作说明|製作說明|内部验收|內部驗收|验收记录|驗收記錄|测试通过|測試通過|非实拍|非實拍)", raw))


def is_marking(item):
    return (item.get("kind") == "marking" or bool(item.get("graphic_sha256"))
            or bool(set(p for p in seq(item.get("purposes")) if isinstance(p, str)) & MARKING_PURPOSES)
            or marking_cue(item.get("text", "")))


def valid_range(value):
    return (isinstance(value, list) and len(value) == 2
            and all(type(n) in (int, float) and math.isfinite(n) for n in value)
            and 0 <= value[0] < value[1])


def scope(item):
    return {key: item.get(key) for key in ("text", "surface", "position", "time_range", "graphic_sha256")}


def validate_label_plan(checks, items):
    """G1 checks consent only; it never requires a not-yet-rendered video."""
    for ident, item in items.items():
        if item.get("surface") not in VISUAL_SURFACES or not is_marking(item):
            continue
        label = "label permission " + str(ident) + ": "
        checks.need(text(item.get("position")) and valid_range(item.get("time_range")),
                    label + "exact position and time range required")
        graphic = item.get("graphic_sha256")
        if graphic is not None:
            checks.need(isinstance(graphic, str) and bool(re.fullmatch(r"[0-9a-f]{64}", graphic)),
                        label + "actual graphic SHA-256 required")
            ref = obj(item.get("graphic_source"))
            checks.need(ref.get("sha256") == graphic, label + "graphic source must bind the exact consented asset")
            checks.evidence(ref, label + "actual graphic source")
        approval = obj(item.get("user_approval"))
        checks.need(approval.get("scope") == scope(item), label + "user consent must match exact content/surface/position/time range")
        checks.need(text(approval.get("user_message_ref")) and text(approval.get("user_quote")),
                    label + "original user message reference and exact quote required; self-declared approval is insufficient")
        path = checks.evidence(approval.get("evidence"), label + "original user consent")
        if path:
            try:
                quote = approval.get("user_quote")
                checks.need(text(quote) and quote in path.read_text(encoding="utf-8"),
                            label + "quote absent from bound original user consent")
            except (OSError, UnicodeError):
                checks.need(False, label + "original user consent is unreadable")


def validate_overlay_review(checks, gate, viewing, review, items, selected_ids):
    """Require actual-output/source inventory, then block unknown/mismatched overlays.

    Existing continuous viewing and, where installed, audience_text_guard remain
    mandatory. A complete declaration is not machine proof of complete capture.
    """
    from stage_checks import digest
    label = gate + " overlay guard: "
    def need(ok, message):
        return checks.need(ok, label + message)
    path = checks.evidence(review.get("overlay_evidence"), label + "actual output/source review")
    if not path:
        return
    try:
        data = obj(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, ValueError):
        need(False, "invalid actual output/source review")
        return
    need(data.get("schema_version") == 1 and data.get("status") == "pass", "unreviewed/failed evidence")
    need(data.get("media_sha256") == viewing.get("sha256")
         and data.get("inventory_sha256") == digest(checks.data.get("presentation_text")), "stale media/inventory binding")
    need(data.get("stage") == gate and data.get("time_range") == [0, viewing.get("duration")],
         "whole current viewing file must be inspected, including the full representative clip")
    need(data.get("method") == "actual_output_and_sources" and data.get("actual_output_inspected") is True
         and text(data.get("reviewer")) and text(data.get("observation")),
         "actual output and overlay sources must be inspected; source-only screening is insufficient")
    need(isinstance(data.get("zones"), list) and len(data["zones"]) == len(ZONES)
         and all(isinstance(z, str) for z in data["zones"]) and set(data["zones"]) == ZONES,
         "subtitles/corners/opening/closing/in-art/body coverage required")
    need(data.get("unknown_overlays") == [], "unknown/untracked overlays block output")
    if gate == "G5":
        expected = sorted(obj(ref).get("sha256", "") for ref in seq(review.get("cover_files")))
        actual = data.get("cover_sha256")
        need(isinstance(actual, list) and all(isinstance(h, str) for h in actual)
             and sorted(actual) == expected and len(expected) == 2, "both current covers must be bound")
    sources = {}
    entries = data.get("sources")
    need(isinstance(entries, list) and bool(entries), "complete renderer/caption/asset source inventory required")
    for source in seq(entries):
        source = obj(source); ident = source.get("id")
        valid = text(ident) and ident not in sources
        need(valid, "source ID missing/duplicate")
        if not valid:
            continue
        sources[ident] = source
        need(source.get("kind") in {"renderer", "caption", "text_asset", "footage", "image"}, "unknown overlay source kind")
        checks.evidence(source, label + "source " + ident)
    observations = data.get("observed")
    need(isinstance(observations, list), "actual text and graphic overlay inventory required, even when empty")
    seen = set()
    applicable = {i for i in selected_ids if i in items and items[i].get("surface") in VISUAL_SURFACES}
    for observed in seq(observations):
        observed = obj(observed); ident = observed.get("item_id")
        valid = isinstance(ident, str) and ident in applicable
        need(valid, "unknown/unclassified actual overlay")
        refs = observed.get("source_ids")
        need(isinstance(refs, list) and bool(refs) and all(isinstance(i, str) and i in sources for i in refs),
             "actual overlay source unknown/untracked")
        if not valid:
            continue
        seen.add(ident); item = items[ident]
        need(observed.get("text") == item.get("text") and observed.get("surface") == item.get("surface")
             and observed.get("graphic_sha256") == item.get("graphic_sha256"), "actual overlay differs from classified content")
        need(text(observed.get("position")) and valid_range(observed.get("time_range")), "actual overlay position/time range missing")
        interval = observed.get("time_range")
        if valid_range(interval) and item.get("surface") != "cover":
            duration = viewing.get("duration")
            need(type(duration) in (int, float) and interval[1] <= duration, "actual overlay exceeds current output duration")
        if item.get("graphic_sha256") is not None:
            graphic_ref = obj(item.get("graphic_source"))
            need(any(obj(sources.get(source_id)).get("kind") in {"text_asset", "image"}
                     and obj(sources.get(source_id)).get("sha256") == item.get("graphic_sha256")
                     and obj(sources.get(source_id)).get("file") == graphic_ref.get("file")
                     for source_id in seq(refs) if isinstance(source_id, str)),
                 "actual graphic is not bound to its reviewed source asset")
        if is_marking(item):
            need(scope(observed) == scope(item), "actual label differs from specifically consented position/time/content")
        # Changing the source classification cannot disguise a visible marking.
        need(not marking_cue(observed.get("text", "")) or is_marking(item), "visible marking misclassified as scientific text")
    need(seen == applicable, "actual output inventory does not cover all classified visible items")
