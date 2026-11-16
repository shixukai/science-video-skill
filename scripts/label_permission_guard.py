"""Fail-closed label permission and actual-overlay evidence checks.

This validates evidence bindings, not the truth of a user's consent or a human's
visual observations. No OCR/perceptual approval is claimed and no older guard is
replaced. Ordinary captions keep their existing role. 3D picture text permits
only necessary single-letter markers; scientific/consent flags do not waive it.
"""
import json
import hashlib
import math
import re
import unicodedata
from task_scope import cover_keys

MARKING_PURPOSES = {"attribution", "license", "ai_simulation", "production_meta",
                    "watermark", "internal_qa", "production_excuse", "material_defect"}
VISUAL_SURFACES = {"frame", "caption", "cover"}
ZONES = {"subtitles", "corners", "opening", "closing", "in_art", "body"}
ORDINARY_CAPTION_ROLES = {'spoken_sync', 'sound_accessibility'}


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


def scientific_subject_review(item):
    """A traceable semantic review, not a blanket keyword exemption."""
    review = obj(item.get('cue_review'))
    ids = review.get('claim_ids')
    return (review.get('status') == 'pass' and review.get('interpretation') == 'scientific_subject'
            and all(text(review.get(k)) for k in ('reviewer', 'scientific_basis', 'audience_task', 'note'))
            and isinstance(ids, list) and bool(ids) and all(text(i) for i in ids)
            and review.get('text_sha256') == hashlib.sha256(str(item.get('text', '')).encode()).hexdigest()
            and bool(obj(review.get('evidence')).get('file')))


def scientific_condition_review(item, record):
    """A current-text scientific condition, never a purpose-label exemption."""
    review = obj(item.get('cue_review'))
    ids = review.get('claim_ids')
    return (review.get('status') == 'pass' and review.get('interpretation') == 'scientific_condition'
            and 'scientific_condition' in seq(item.get('purposes'))
            and all(text(review.get(k)) for k in ('reviewer', 'scientific_basis', 'audience_task', 'note'))
            and isinstance(ids, list) and bool(ids) and all(text(i) for i in ids)
            and review.get('text_sha256') == hashlib.sha256(str(item.get('text', '')).encode()).hexdigest()
            and bool(obj(review.get('evidence')).get('file'))
            and any(obj(n).get('id') == item.get('notice_id')
                    and obj(n).get('purpose') == 'scientific_condition'
                    and obj(n).get('placement') == 'audience'
                    and obj(n).get('text') == item.get('text')
                    and obj(n).get('basis') == review.get('scientific_basis')
                    for n in seq(record.get('required_notices'))))


def three_d_shots(data):
    """Declared shot bindings only; this does not establish visible 3D quality."""
    return {s.get('id') for s in seq(data.get('shots')) if isinstance(s, dict) and text(s.get('id'))
            and (s.get('modality') == 'controlled_3d'
                 or obj(obj(s.get('shotbook')).get('realism')).get('medium') == 'three_d')}


def three_d_text_scope(item, data):
    """Use declared 3D shots; valid explicit bindings narrow mixed episodes."""
    declared = three_d_shots(data)
    if not declared or item.get('surface') == 'cover':
        return False
    ids = item.get('shot_ids')
    known = {obj(s).get('id') for s in seq(data.get('shots')) if text(obj(s).get('id'))}
    if isinstance(ids, list) and bool(ids) and all(text(i) and i in known for i in ids):
        return bool(set(ids) & declared)
    # Do not silently exempt an unbound/malformed item in a declared 3D episode.
    # The frame plan separately rejects missing/invalid actual shot bindings.
    return True


def single_letter_marker(value):
    """Marker content only, not proof of a real referent or visible necessity."""
    if not isinstance(value, str):
        return False
    raw = value.strip()
    normalized = unicodedata.normalize('NFKC', raw)
    return (len(raw) == len(normalized) == 1 and raw.isalpha()
            and unicodedata.name(normalized, '').startswith(('LATIN ', 'GREEK ')))


def validate_three_d_frame_text(checks, item, shot_ids=None):
    """Fail closed for declared 3D frame words, including marked/object text."""
    if item.get('surface') != 'frame' or not three_d_text_scope(item, checks.data):
        return
    if shot_ids is not None:
        if not (three_d_shots(checks.data) & set(shot_ids)):
            return
        ids = item.get('shot_ids')
        known = {obj(s).get('id') for s in seq(checks.data.get('shots')) if text(obj(s).get('id'))}
        if (isinstance(ids, list) and bool(ids) and all(text(i) and i in known for i in ids)
                and not (set(ids) & set(shot_ids))):
            return
    checks.need(single_letter_marker(item.get('text')),
                'presentation 3D picture permits only single-letter markers; explanatory words/numbers/units must be removed')


def spatial_auxiliary(item, data):
    return (item.get('surface') == 'frame'
            and item.get('kind') != 'physical_lettering'
            and bool({i for i in seq(item.get('shot_ids')) if text(i)} & three_d_shots(data)))


def scoped_caption(item, data):
    return item.get('surface') == 'caption' and three_d_text_scope(item, data)


def validate_spatial_text_plan(checks, item):
    """Extend the existing inventory only where actual shot metadata scopes it.

    Unbound frame text in a declared 3D episode cannot silently opt out. Mixed
    episodes bind each item to its actual shots. Ordinary captions also need a
    current spoken/audible correspondence review; changing the surface does not
    turn an auxiliary label into a synchronized caption. Physical lettering is
    inspected as part of the object.
    """
    validate_three_d_frame_text(checks, item)
    if scoped_caption(item, checks.data):
        checks.need(isinstance(item.get('caption_role'), str) and item.get('caption_role') in ORDINARY_CAPTION_ROLES
                    and item.get('kind') != 'auxiliary_text',
                    'presentation 3D caption ordinary synchronized role required; auxiliary labels must use frame shot_ids/spatial_3d')
        return
    if item.get('surface') != 'frame' or not three_d_text_scope(item, checks.data):
        return
    ids = item.get('shot_ids')
    known = {obj(s).get('id') for s in seq(checks.data.get('shots')) if text(obj(s).get('id'))}
    valid = (isinstance(ids, list) and bool(ids) and all(text(i) and i in known for i in ids)
             and len(set(ids)) == len(ids))
    checks.need(valid, 'presentation frame text actual shot_ids required in declared 3D episodes')
    if not valid:
        return
    if bool(set(ids) & three_d_shots(checks.data)):
        checks.need(item.get('kind') in (None, 'auxiliary_text', 'physical_lettering', 'marking'),
                    'presentation 3D frame text kind must identify auxiliary text or physical lettering')
    if item.get('kind') == 'physical_lettering':
        asset_id = item.get('source_asset_id')
        assets = [obj(a) for a in seq(checks.data.get('assets')) if text(asset_id) and obj(a).get('id') == asset_id]
        shots = [obj(s) for s in seq(checks.data.get('shots')) if obj(s).get('id') in ids]
        checks.need(len(assets) == 1 and all(asset_id in seq(s.get('asset_ids')) for s in shots),
                    'presentation physical lettering must bind an actual object/source asset in every linked shot')
        if len(assets) == 1:
            checks.evidence(assets[0], 'presentation physical lettering actual object/source asset')
    if spatial_auxiliary(item, checks.data):
        checks.need(item.get('representation') == 'spatial_3d',
                    'presentation 3D auxiliary text requires spatial_3d representation; captions remain clear 2D')


def is_marking(item):
    return (item.get("kind") == "marking" or bool(item.get("graphic_sha256"))
            or bool(set(p for p in seq(item.get("purposes")) if isinstance(p, str)) & MARKING_PURPOSES)
            or (marking_cue(item.get("text", "")) and not scientific_subject_review(item)))


def valid_range(value):
    return (isinstance(value, list) and len(value) == 2
            and all(type(n) in (int, float) and math.isfinite(n) for n in value)
            and 0 <= value[0] < value[1])


def scope(item):
    return {key: item.get(key) for key in ("text", "surface", "position", "time_range", "graphic_sha256")}


def validate_label_plan(checks, items):
    """G1 checks consent only; it never requires a not-yet-rendered video."""
    for ident, item in items.items():
        if (item.get("surface") not in VISUAL_SURFACES and 'ai_simulation' not in seq(item.get('purposes'))) or not is_marking(item):
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
             and sorted(actual) == expected and len(expected) == len(cover_keys(checks.data)), "requested current covers must be bound")
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
    caption_ids = {i for i in applicable if scoped_caption(items[i], checks.data)}
    if caption_ids:
        correspondence = obj(obj(obj(review.get('channel_reviews')).get('caption')).get('caption_correspondence'))
        covered = correspondence.get('item_ids')
        need(correspondence.get('status') == 'pass' and text(correspondence.get('observation'))
             and isinstance(covered, list) and all(text(i) for i in covered)
             and len(set(covered)) == len(covered) and set(covered) == caption_ids,
             'actual ordinary captions require current speech/audible accessibility correspondence review; detached auxiliary annotations must be repaired')
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
        actual_item = {**item, **{key: observed.get(key) for key in
                       ('text', 'surface', 'shot_ids', 'kind', 'representation')}}
        validate_three_d_frame_text(checks, item)
        validate_three_d_frame_text(checks, actual_item)
        need(observed.get("text") == item.get("text") and observed.get("surface") == item.get("surface")
             and observed.get("graphic_sha256") == item.get("graphic_sha256"), "actual overlay differs from classified content")
        if scoped_caption(item, checks.data) or scoped_caption(actual_item, checks.data):
            need(isinstance(item.get('caption_role'), str) and item.get('caption_role') in ORDINARY_CAPTION_ROLES
                 and item.get('kind') != 'auxiliary_text'
                 and observed.get('caption_role') == item.get('caption_role'),
                 'actual caption role must match ordinary synchronized narration/sound accessibility; auxiliary relabeling is not exempt')
            formal = obj(obj(review.get('sources')).get('caption'))
            need(text(formal.get('file')) and text(formal.get('sha256'))
                 and any(obj(sources.get(source_id)).get('kind') == 'caption'
                         and obj(sources.get(source_id)).get('file') == formal.get('file')
                         and obj(sources.get(source_id)).get('sha256') == formal.get('sha256')
                         for source_id in seq(refs) if isinstance(source_id, str)),
                 'actual ordinary caption source must bind the current formal caption file and SHA-256')
        if item.get('surface') in ('frame', 'caption') and (three_d_text_scope(item, checks.data) or three_d_text_scope(actual_item, checks.data)):
            need(observed.get('shot_ids') == item.get('shot_ids') and observed.get('kind') == item.get('kind'),
                 'actual frame text shot/kind binding differs from classified inventory')
        if spatial_auxiliary(item, checks.data) or spatial_auxiliary(actual_item, checks.data):
            need(item.get('representation') == 'spatial_3d' and observed.get('representation') == 'spatial_3d',
                 'actual 3D auxiliary text spatial representation missing/mismatched')
            spatial = obj(observed.get('spatial_review'))
            need(spatial.get('status') == 'pass' and text(spatial.get('observation')),
                 'actual spatial text appearance/readability/target-binding review failed/unreviewed; return for repair')
        if (item.get('surface') == 'frame' and item.get('kind') == 'physical_lettering'
                and three_d_text_scope(item, checks.data)):
            asset_id = item.get('source_asset_id')
            assets = [obj(a) for a in seq(checks.data.get('assets')) if text(asset_id) and obj(a).get('id') == asset_id]
            need(observed.get('source_asset_id') == asset_id and text(observed.get('observation')),
                 'actual pre-existing/functional physical lettering and object binding must be observed')
            need(len(assets) == 1 and any(obj(sources.get(source_id)).get('asset_id') == asset_id
                 and obj(sources.get(source_id)).get('file') == assets[0].get('file')
                 and obj(sources.get(source_id)).get('sha256') == assets[0].get('sha256')
                 for source_id in seq(refs) if isinstance(source_id, str)),
                 'actual physical lettering source must bind the same object/asset file and SHA-256')
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
        need(not marking_cue(observed.get("text", "")) or is_marking(item)
             or (three_d_text_scope(item, checks.data) and scientific_subject_review(item)),
             "visible marking misclassified as scientific text")
    need(seen == applicable, "actual output inventory does not cover all classified visible items")
