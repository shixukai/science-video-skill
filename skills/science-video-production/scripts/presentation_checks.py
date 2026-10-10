"""Classified text and declared continuous listening; no perceptual verdicts."""
import re
import html
from pathlib import Path
from subject_motion import text as meaningful

SURFACES = {"frame", "caption", "voiceover", "cover"}
ALLOWED = {"topic", "mechanism", "accessibility", "scientific_condition", "attribution", "license", "ai_simulation"}
PROTECTED = {"scientific_condition", "attribution", "license", "ai_simulation"}
FORBIDDEN = {"material_defect", "internal_qa", "production_excuse"}
VOICE_CRITERIA = {"tone", "rhythm", "speech_rate", "loudness", "joins"}
# Screening is supplementary: category/necessity and actual-media reviews remain
# required, including for wording that does not match any of these patterns.
EXCUSE_CUES = (
    re.compile(r"(?:原(?:始)?(?:视频|片|素材)|素材).{0,8}(?:无|没有|缺少).{0,5}(?:音轨|声音|原声)"),
    re.compile(r"(?:本片|本视频|制作端|成片).{0,10}(?:待验|未验|测试通过|审查通过|验收通过)"),
    re.compile(r"(?:素材|模型|渲染|制作|导出).{0,8}(?:受限|不足|失败|不支持|方便|省时)"),
    re.compile(r"(?:不作|不做|未做).{0,8}(?:飞行声音|原声|音轨).{0,4}(?:比较|对比)"),
)


def prohibited_cue(item, record):
    """Ambiguous scientific-model limits require a matching protected notice.

    Purpose labels never exempt material defects, QA or production-choice
    excuses. Actual scientific purpose still requires current-media review.
    """
    wording = item.get("text", "")
    for index, pattern in enumerate(EXCUSE_CUES):
        if not pattern.search(wording): continue
        notices = record.get("required_notices", [])
        if not isinstance(notices, list): notices = []
        protected = any(isinstance(n, dict) and n.get("id") == item.get("notice_id")
                        and n.get("purpose") == "scientific_condition" and n.get("text") == wording
                        and meaningful(n.get("basis")) for n in notices)
        purposes = item.get("purposes", [])
        if not isinstance(purposes, list): purposes = []
        scientific_model = (index == 2 and "scientific_condition" in purposes and protected
                            and "模型" in wording and not re.search(r"素材|渲染|制作|导出|(?:所以|因此).{0,6}(?:用|采用|展示|表现)", wording))
        if not scientific_model: return True
    return False


def caption_body(raw, suffix):
    if suffix == ".ass":
        lines = [line.split(",", 9)[-1] for line in raw.splitlines() if line.startswith("Dialogue:")]
        return re.sub(r"\{[^}]*\}", "", "\n".join(lines)).replace("\\N", "\n").replace("\\n", "\n")
    if suffix == ".txt":
        return raw
    if suffix not in (".srt", ".vtt"):
        raise ValueError("caption text extraction needs txt/srt/vtt/ass; convert other formats to a supported formal caption format and review it")
    bodies = []
    for block in re.split(r"\r?\n\s*\r?\n", raw.strip()):
        lines = block.splitlines()
        time = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if time is not None:
            # Numeric years, quantities and frequency values after the cue's
            # time line are audience text, not sequence indices.
            bodies.extend(lines[time+1:])
        elif block and not (suffix == ".vtt" and lines[0].startswith(("WEBVTT", "NOTE", "STYLE", "REGION"))):
            raise ValueError("caption cue has no time line")
    # Strip only recognized caption markup, not mathematical inequalities.
    markup = r"</?(?:b|i|u|font|c|ruby|rt)(?:[ \t][^<>]*|\.[\w.-]+)?\s*>|<(?:v|lang)[ \t]+[^<>]+>|</(?:v|lang)>|<\d{2}:\d{2}(?::\d{2})?[.,]\d{3}>"
    return html.unescape(re.sub(markup, "", "\n".join(bodies), flags=re.IGNORECASE))


def normalized(raw):
    return re.sub(r"\s+", "", raw)


def validate_text_plan(checks):
    from stage_checks import obj, seq, text
    substantive = meaningful
    record = obj(checks.data.get("presentation_text"))
    channels = obj(record.get("channels"))
    checks.need(set(channels) == SURFACES, "presentation text four surface inventory required")
    items = seq(record.get("items")); found = {}; surfaces = set()
    for item in items:
        item = obj(item); ident = item.get("id"); surface = item.get("surface")
        checks.need(text(ident) and ident not in found, "presentation text item ID missing/duplicate")
        if text(ident): found[ident] = item
        checks.need(surface in SURFACES, "presentation text unknown surface")
        if surface in SURFACES: surfaces.add(surface)
        purposes = item.get("purposes")
        valid = isinstance(purposes, list) and bool(purposes) and all(isinstance(p, str) and p in ALLOWED | FORBIDDEN for p in purposes)
        checks.need(valid, "presentation text classified purpose required")
        checks.need(valid and not (set(purposes) & FORBIDDEN), "presentation text material defects/internal QA/production excuses cannot enter audience media")
        for key in ("text", "necessity", "removal_loss"):
            checks.need(substantive(item.get(key)), "presentation text "+key+" required")
        if text(item.get("text")):
            checks.need(not prohibited_cue(item, record), "presentation text production/material-defect cue requires removal or concise scientific rewrite")
    for surface in SURFACES:
        channel = obj(channels.get(surface)); state = channel.get("status")
        checks.need(state in ("present", "absent") and substantive(channel.get("note")), "presentation text explicit channel coverage required: "+surface)
        checks.need((state == "present") == (surface in surfaces), "presentation text channel/item inventory conflicts: "+surface)
    required = record.get("required_notices")
    checks.need(isinstance(required, list), "presentation text protected notices must be explicit")
    notice_ids = set()
    for notice in seq(required):
        notice = obj(notice); ident = notice.get("id")
        checks.need(text(ident) and ident not in notice_ids, "presentation protected notice ID missing/duplicate")
        if text(ident): notice_ids.add(ident)
        checks.need(notice.get("purpose") in PROTECTED and substantive(notice.get("text")) and substantive(notice.get("basis")), "presentation protected notice scientific/rights basis required")
        matches = [x for x in items if obj(x).get("notice_id") == ident]
        checks.need(bool(matches) and all(obj(x).get("text") == notice.get("text") and notice.get("purpose") in seq(obj(x).get("purposes")) for x in matches), "presentation required attribution/license/AI/scientific condition removed or changed")
    # Referenced asset obligations cannot disappear just by deleting the notice.
    used, _, _ = __import__("stage_checks").dependencies(checks.data)
    for asset in seq(checks.data.get("assets")):
        asset = obj(asset)
        if asset.get("id") not in used: continue
        refs = asset.get("required_notice_ids", [])
        checks.need(isinstance(refs, list) and all(text(i) and i in notice_ids for i in refs), "presentation used asset required notice unresolved")
    return found


def validate_text_review(checks, gate, viewing, items):
    from stage_checks import obj, seq, context_sha256, digest
    substantive = meaningful
    r = obj(obj(checks.record("presentation_text")).get(gate))
    label = gate+" presentation text "
    def need(ok, message): return checks.need(ok, label+message)
    need(r.get("status") == "pass", "actual review failed/unreviewed")
    need(r.get("context_sha256") == context_sha256(checks.data, gate) and r.get("media_sha256") == viewing.get("sha256"), "stale stage/media")
    need(r.get("inventory_sha256") == digest(checks.data.get("presentation_text")), "stale classified inventory")
    need(r.get("actual_media_inspected") is True and substantive(r.get("evidence")), "actual media text/voice inspection required; OCR/source-only checks do not qualify")
    channels = SURFACES if gate == "G5" else SURFACES-{"cover"}
    reviews = obj(r.get("channel_reviews"))
    need(set(reviews) == channels, "complete applicable surface review required")
    ids = set()
    for surface in channels:
        review = obj(reviews.get(surface)); selected = review.get("item_ids")
        valid = isinstance(selected, list) and all(isinstance(i, str) and i in items and items[i].get("surface") == surface for i in selected)
        need(valid and len(set(selected)) == len(selected), surface+" item coverage invalid")
        if valid: ids.update(selected)
        need(review.get("status") == "pass" and substantive(review.get("observation")) and substantive(review.get("evidence")), surface+" actual purpose/deletion review required")
    if gate != "G3":
        need(ids == {i for i, item in items.items() if item.get("surface") in channels}, "full export text inventory coverage incomplete")
    sources = obj(r.get("sources"))
    for surface in ("voiceover", "caption"):
        path = checks.evidence(sources.get(surface), label+surface)
        expected = (obj(checks.data.get("narration")).get("script_file") if gate != "G3" else None) if surface == "voiceover" else (
            obj(checks.record("visual_frames.animation").get("captions")).get("file") if gate == "G3" else
            obj(checks.data.get("deliverables")).get("captions") if gate == "G5" else None)
        if expected: need(obj(sources.get(surface)).get("file") == expected, surface+" source must bind formal current file")
        if path:
            try:
                raw = path.read_text(encoding="utf-8")
                if surface == "caption": raw = caption_body(raw, path.suffix)
                # Source screening never scans off-media project notes or code.
                classified = "".join(item.get("text", "") for ident, item in items.items() if ident in ids and item.get("surface") == surface)
                # Every source character must match screened classified items;
                # ambiguous scientific-model conditions keep their bound basis.
                need(normalized(classified) == normalized(raw), surface+" formal text is not completely classified in source order")
            except (OSError, UnicodeError, ValueError): need(False, surface+" UTF-8 text extraction/source unreadable")
    if gate == "G5":
        refs = r.get("cover_files"); actual = []
        for ref in seq(refs):
            checks.evidence(ref, label+"cover"); actual.append(obj(ref).get("file"))
        need(isinstance(refs, list) and len(actual) == 2 and set(actual) == {
            obj(checks.data.get("deliverables")).get("cover_3_4"), obj(checks.data.get("deliverables")).get("cover_4_3")}, "both actual cover versions required")
    need(substantive(r.get("protected_notices_review")), "required scientific/rights/AI notice preservation review required")


def validate_voice_continuity(checks, gate, viewing):
    from stage_checks import obj, seq, number, context_sha256, digest
    substantive = meaningful
    label = gate+" voice continuity "
    def need(ok, message): return checks.need(ok, label+message)
    narration = obj(checks.data.get("narration")); plan = obj(narration.get("delivery_plan"))
    mode = plan.get("mode")
    need(mode in ("continuous_first", "context_preserving_segments"), "continuous-first or verified contextual segmentation required")
    target = obj(plan.get("target"))
    need(set(target) == VOICE_CRITERIA-{"joins"} and all(substantive(x) for x in target.values()), "whole-episode tone/rhythm/rate/loudness target required")
    if mode == "context_preserving_segments":
        for key in ("technical_limit", "verified_method", "capability_evidence", "context_handoff"):
            need(substantive(plan.get(key)), "segmentation "+key+" required; unverified fixed methods cannot qualify")
    r = obj(obj(checks.record("audio.continuity")).get(gate))
    need(r.get("status") == "pass", "failed/unreviewed")
    need(r.get("context_sha256") == context_sha256(checks.data, gate) and r.get("media_sha256") == viewing.get("sha256")
         and r.get("audio_sha256") == narration.get("audio_sha256") and r.get("plan_sha256") == digest(plan), "stale media/audio/target plan")
    need(r.get("method") == "normal_speed_continuous_listening" and r.get("actually_heard") is True
         and substantive(r.get("reviewer")) and substantive(r.get("capability")) and substantive(r.get("evidence")),
         "actual complete continuous listening required; same speaker/seed/ASR/decoding is insufficient")
    need(r.get("ranges") == viewing.get("ranges"), "listening must cover complete reviewed clip/export")
    criteria = obj(r.get("criteria"))
    need(set(criteria) == VOICE_CRITERIA, "tone/rhythm/rate/loudness/joins criteria required")
    for key in VOICE_CRITERIA:
        item = obj(criteria.get(key))
        need(item.get("status") == "pass" and substantive(item.get("observation")) and substantive(item.get("evidence")), key+" failure cannot be offset by technical checks")
    episode_shots = seq(checks.data.get("shots"))
    shots = [obj(s).get("id") for s in episode_shots if isinstance(obj(s).get("id"), str)]
    if gate == "G3":
        _, selected, _ = __import__("stage_checks").dependencies(checks.data, True)
        intervals = seq(checks.record("visual_frames.animation").get("shot_intervals"))
    else:
        selected = set(shots)
        intervals = [{"shot_id": obj(s).get("id"), **{k: obj(obj(s).get("shotbook")).get(k) for k in ("start", "end")}} for s in episode_shots]
    cursor = 0; timeline = []; boundaries = {}; valid_timeline = bool(intervals)
    for interval in intervals:
        interval = obj(interval); ident = interval.get("shot_id"); start, end = interval.get("start"), interval.get("end")
        valid = (isinstance(ident, str) and ident in shots and ident not in timeline and number(start) and number(end)
                 and number(viewing.get("duration")) and abs(start-cursor) <= .001 and start < end <= viewing["duration"]+.001)
        need(valid, "current-media shot timeline missing/invalid; self-reported transition times are insufficient")
        valid_timeline &= valid
        if valid:
            if timeline: boundaries[(timeline[-1], ident)] = start
            timeline.append(ident); cursor = end
    need(valid_timeline and selected <= set(timeline) and number(viewing.get("duration")) and abs(cursor-viewing["duration"]) <= .001,
         "current-media shot timeline must cover complete reviewed media and selected shots")
    expected = set(boundaries); found = set()
    for row in seq(r.get("transitions")):
        row = obj(row); pair = (row.get("from_shot"), row.get("to_shot"))
        if not all(isinstance(v, str) for v in pair): need(False, "transition shot IDs invalid"); continue
        need(pair in expected and pair not in found, "transition missing/duplicate/irrelevant"); found.add(pair)
        at = row.get("at"); span = row.get("listen_range")
        need(number(at) and isinstance(span, list) and len(span) == 2 and all(number(x) for x in span)
             and number(viewing.get("duration")) and 0 <= span[0] < at < span[1] <= viewing["duration"]+.001,
             "cross-shot listening must actually straddle current-media boundary")
        need(pair in boundaries and number(at) and abs(at-boundaries.get(pair, 0)) <= .001,
             "transition time must match actual current-media shot boundary")
        need(row.get("status") == "pass" and substantive(row.get("observation")) and substantive(row.get("evidence")), "cross-shot change failed/unreviewed")
    need(found == expected, "cross-shot continuous listening coverage incomplete")
    if mode == "context_preserving_segments":
        segments = plan.get("segments"); need(isinstance(segments, list) and len(segments) >= 2, "segmented source/context records required")
        previous = None
        for segment in seq(segments):
            segment = obj(segment)
            for key in ("id", "context_before", "context_after", "handoff_evidence"):
                need(substantive(segment.get(key)), "segment "+key+" required")
            checks.evidence(segment.get("script"), label+"segment script")
            checks.evidence(segment.get("audio"), label+"segment audio")
            if previous is not None:
                need(segment.get("context_before") == previous.get("context_after"), "segment narrative context handoff mismatch")
            previous = segment
