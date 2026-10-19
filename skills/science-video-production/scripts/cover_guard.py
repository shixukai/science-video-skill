"""Bind declared cover review to actual files. Never certifies visual perception."""
from datetime import datetime, timezone
import hashlib
import json
import math
import shutil
import subprocess


VARIANTS = {"cover_3_4": (3, 4), "cover_4_3": (4, 3)}
OBSERVATIONS = ("style_match", "large_natural_subject", "upper_left_title_and_short_question",
                "independent_composition", "scientific_appearance", "mobile_readability",
                "no_mechanism_page_or_subtitle_capture")
LIMITS = ("Cover record/file checks only: hashes, declarations and tests do not prove actual "
          "viewing, appearance, scientific truth, authorization or publication. Keep unviewed work pending.")
_IMAGE_SIZES = {}


def obj(value):
    return value if isinstance(value, dict) else {}


def meaningful(value):
    return isinstance(value, str) and value.strip().casefold() not in {
        "", "pending", "todo", "tbd", "unknown", "n/a", "none", "pass", "ok", "true",
        "待审", "未验", "待验", "待核", "通过", "完成", "合格", "无", "不适用"}


def image_size(checks, reference, label):
    """ffprobe checks an actual still image, not the visual assertions about it."""
    path = checks.evidence(reference, label)
    if path is None:
        return None
    # Cache decoded metadata by the current bytes, never by a declared hash or
    # filename. Every call still verifies containment and the supplied digest.
    with path.open("rb") as handle:
        actual_digest = hashlib.file_digest(handle, "sha256").hexdigest()
    if actual_digest in _IMAGE_SIZES:
        return _IMAGE_SIZES[actual_digest]
    key = ("cover-image", path, actual_digest)
    if key in checks.cache:
        return checks.cache[key]
    result = None
    probe = shutil.which("ffprobe")
    if not checks.need(bool(probe), label + " ffprobe required for image verification"):
        return None
    try:
        p = subprocess.run([probe, "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(path)],
                           capture_output=True, text=True, timeout=30)
        metadata = obj(json.loads(p.stdout))
        streams = metadata.get("streams", [])
        video = [s for s in streams if isinstance(s, dict) and s.get("codec_type") == "video"]
        valid = (p.returncode == 0 and not p.stderr.strip() and len(video) == 1
                 and video[0].get("nb_read_frames") == "1"
                 and obj(metadata.get("format")).get("format_name") in ("png_pipe", "jpeg_pipe", "webp_pipe", "image2")
                 and video[0].get("codec_name") in ("png", "mjpeg", "webp")
                 and all(type(video[0].get(k)) is int and video[0][k] > 0 for k in ("width", "height")))
        if checks.need(valid, label + " must be an actual PNG/JPEG/WebP still image"):
            result = (video[0]["width"], video[0]["height"])
            if len(_IMAGE_SIZES) >= 256:
                _IMAGE_SIZES.clear()
            _IMAGE_SIZES[actual_digest] = result
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired):
        checks.need(False, label + " image unreadable")
    checks.cache[key] = result
    return result


def validate_cover_review(checks):
    """Required for cover-only delivery and G5–G7; old missing records do not pass."""
    from origin_guard import validate_cover_origins
    validate_cover_origins(checks)
    qa = obj(checks.data.get("qa"))
    covers = obj(qa.get("covers"))
    checks.need(covers.get("status") == "pass", "covers review must pass after actual inspection")
    checks.need(meaningful(covers.get("note")), "covers actual review note required")
    path = checks.evidence(covers.get("visual_review"), "covers visual review")
    if path is None:
        return
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        checks.need(False, "covers visual review JSON unreadable")
        return
    if not checks.need(isinstance(record, dict), "covers visual review must be an object"):
        return
    checks.need(type(record.get("schema_version")) is int and record["schema_version"] == 1,
                "covers visual review schema_version must be 1")
    checks.need(record.get("status") == "pass", "covers actual visual review pending/failed")
    checks.need(record.get("method") == "actual_images_and_mobile_comparison",
                "covers actual images and mobile comparison required; code-only review is insufficient")
    for field in ("producer", "reviewer", "reviewed_at"):
        checks.need(meaningful(record.get(field)), "covers " + field + " required")
    reviewer, producer = record.get("reviewer"), record.get("producer")
    checks.need(isinstance(reviewer, str) and isinstance(producer, str)
                and reviewer.strip().casefold() != producer.strip().casefold()
                and record.get("independent_review") is True,
                "covers independent reviewer must differ from producer")
    checks.need(covers.get("reviewer") == reviewer, "covers reviewer must match visual review")
    try:
        stamp = datetime.fromisoformat(str(record.get("reviewed_at")).replace("Z", "+00:00"))
        checks.need(stamp.utcoffset() is not None, "covers reviewed_at needs timezone")
        if stamp.utcoffset() is not None:
            checks.need(stamp <= datetime.now(timezone.utc), "covers review cannot be dated in the future")
    except ValueError:
        checks.need(False, "covers reviewed_at invalid")

    baseline = obj(record.get("baseline"))
    checks.need(baseline.get("kind") == "approved_cover" and baseline.get("scope") == "cover_appearance",
                "covers baseline must be a traceable approved cover, not a generic style description")
    checks.need(baseline.get("actually_opened") is True and meaningful(baseline.get("observation")),
                "covers approved baseline must actually be opened and observed")
    image_size(checks, baseline.get("image"), "covers approved baseline")
    checks.evidence(baseline.get("approval_evidence"), "covers private approval evidence")
    checks.need(meaningful(baseline.get("approval_reference")), "covers approval reference required")
    checks.need(baseline.get("approved_image_sha256") == obj(baseline.get("image")).get("sha256"),
                "covers approval must bind the exact baseline image")

    variants = obj(record.get("variants"))
    checks.need(set(variants) == set(VARIANTS), "covers both independently composed variants required")
    exports = obj(checks.data.get("deliverables"))
    hashes = obj(qa.get("reviewed_sha256"))
    for name, ratio in VARIANTS.items():
        row = obj(variants.get(name)); label = "covers " + name
        reference = obj(row.get("export"))
        checks.need(reference.get("file") == exports.get(name) and meaningful(exports.get(name)),
                    label + " must bind actual deliverable path")
        checks.need(reference.get("sha256") == hashes.get(name) and meaningful(hashes.get(name)),
                    label + " stale/unbound export hash")
        size = image_size(checks, reference, label + " export")
        if size:
            checks.need(size[0] * ratio[1] == size[1] * ratio[0], label + " aspect ratio mismatch")
        checks.need(row.get("actual_export_opened") is True and row.get("baseline_compared") is True,
                    label + " actual export opening and baseline comparison required")
        checks.need(row.get("layout_kind") == "independent_cover_scene", label + " mechanism/slide/capture layout prohibited")
        checks.need(row.get("style") == "detailed_2d_nature" and row.get("title_position") == "upper_left",
                    label + " current series requires detailed 2D nature and upper-left title")
        for field in ("subject", "title", "question"):
            checks.need(meaningful(row.get(field)), label + " " + field + " required")
        checks.need(row.get("prohibited_elements") == [], label + " prohibited arrows/small labels/subtitle capture unresolved")
        preview = obj(row.get("mobile_preview"))
        image_size(checks, preview, label + " mobile preview")
        checks.need(preview.get("file") != reference.get("file"), label + " separate mobile preview required")
        checks.need(preview.get("source_sha256") == reference.get("sha256"), label + " stale mobile preview source")
        width = preview.get("display_width_px")
        checks.need(type(width) in (int, float) and math.isfinite(width) and width > 0
                    and preview.get("display_context") == "phone_thumbnail",
                    label + " recorded phone-thumbnail display width and context required")
        checks.need(preview.get("actually_opened") is True, label + " mobile preview must actually be opened")
        comparison = obj(row.get("comparison"))
        image_size(checks, comparison, label + " comparison evidence")
        checks.need(comparison.get("actually_opened") is True, label + " comparison image must actually be opened")
        checks.need(comparison.get("baseline_sha256") == obj(baseline.get("image")).get("sha256")
                    and comparison.get("export_sha256") == reference.get("sha256")
                    and comparison.get("preview_sha256") == preview.get("sha256"),
                    label + " stale comparison bindings")
        observations = obj(row.get("observations"))
        for criterion in OBSERVATIONS:
            item = obj(observations.get(criterion))
            checks.need(item.get("status") == "pass" and meaningful(item.get("observation")),
                        label + " actual observation missing/failed: " + criterion)
