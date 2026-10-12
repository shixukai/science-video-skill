"""Opening evidence contracts only; semantic/perceptual judgments remain actual review.

A truthful user review is a valid source. No regex or literal-title match claims
that a generic hook answers the promised question, or that a cut feels smooth.
"""
import hashlib
import json
import math

COVERS = ("cover_3_4", "cover_4_3")
REVIEW_ITEMS = {"cover_question", "spoken_question", "answer_route", "visual_handoff"}


def obj(value):
    return value if isinstance(value, dict) else {}


def concrete(value):
    return isinstance(value, str) and value.strip().lower() not in (
        "", "pass", "ok", "pending", "unknown", "todo", "tbd", "n/a", "none",
        "未验", "待验", "待审", "通过", "无")


def finite(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def opening_context_sha256(data):
    """Bind plans and observed transcript, not a review's conclusions to themselves."""
    qa = obj(data.get("qa"))
    heard = obj(obj(qa.get("topic_alignment")).get("opening_voiceover"))
    return digest({
        **{k: data.get(k) for k in ("topic", "topic_alignment", "shots", "narration", "deliverables")},
        "media_hashes": qa.get("reviewed_sha256"),
        "heard": {k: heard.get(k) for k in ("heard_question", "heard_answer_route")},
    })


def check_opening_plan(data):
    """Require a specific comparison early; a declared verdict is not semantic proof."""
    if obj(data.get("scope")).get("kind") != "episode":
        return []
    opening = obj(obj(data.get("topic_alignment")).get("opening"))
    errors = []
    for key in ("title", "voiceover", "spoken_question", "answer_route", "cover_question", "question_comparison", "visual_handoff"):
        if not concrete(opening.get(key)):
            errors.append("opening alignment: opening." + key + " concrete plan required")
    if opening.get("question_relation") != "specific_equivalent":
        errors.append("opening alignment: specific_equivalent question review required; generic_only/different_question/pending cannot pass")
    return errors


def validate_opening_review(checks):
    """Check current files, ranges, provenance and declared reviews, never perception."""
    data, qa = checks.data, checks.qa
    envelope = obj(obj(qa.get("topic_alignment")).get("opening_alignment"))
    def need(ok, message):
        return checks.need(ok, "opening alignment: " + message)
    need(envelope.get("status") == "pass", "actual scoped review required")
    record_file = checks.evidence(envelope.get("evidence"), "opening alignment review")
    review = {}
    if record_file:
        try:
            review = obj(json.loads(record_file.read_text(encoding="utf-8")))
        except (OSError, ValueError, UnicodeError):
            need(False, "unreadable opening review record")
    need(type(review.get("schema_version")) is int and review["schema_version"] == 1, "opening review schema_version must be integer 1")
    need(review.get("status") == "pass", "actual scoped review required")
    need(review.get("review_scope") == "final_export", "final_export review required")
    need(review.get("context_sha256") == opening_context_sha256(data), "stale topic/opening/transcript context")
    outputs, hashes = obj(data.get("deliverables")), obj(qa.get("reviewed_sha256"))
    media = obj(review.get("video"))
    path = checks.evidence(media, "opening alignment final video")
    need(media.get("file") == outputs.get("video") and concrete(media.get("file")), "review must bind final video path")
    need(media.get("sha256") == hashes.get("video") and concrete(media.get("sha256")), "review must bind final video hash")
    duration = checks.duration(path, label="opening alignment final video") if path else None
    def span(value, label, outer=None):
        valid = isinstance(value, list) and len(value) == 2 and all(
            finite(v) for v in value)
        valid = valid and 0 <= value[0] < value[1]
        if outer is not None:
            valid = valid and outer[0] <= value[0] < value[1] <= outer[1]
        need(valid, label + " must be a nonempty bounded time range")
        return value if valid else None
    viewed = span(review.get("viewed_range_s"), "viewed opening")
    if viewed:
        need(viewed[0] == 0 and finite(duration) and viewed[1] <= duration + 0.05,
             "viewed opening must start at actual first frame and fit final export")
    question = span(review.get("question_range_s"), "spoken question", viewed)
    answer = span(review.get("answer_route_range_s"), "answer/route", viewed)
    if question and answer:
        need(question[1] <= answer[0], "actual question must precede concise answer/route")
    heard = obj(obj(qa.get("topic_alignment")).get("opening_voiceover"))
    for key in ("heard_question", "heard_answer_route"):
        need(concrete(heard.get(key)), "actual " + key + " required")
    need(review.get("question_relation") == "specific_equivalent", "actual question generic_only/different_question/pending cannot pass")
    need(concrete(review.get("question_comparison")), "specific question comparison observation required")
    answer_review = obj(review.get("answer_route_review"))
    need(answer_review.get("status") == "pass" and concrete(answer_review.get("observation")),
         "concise accurate answer/route actual observation required")
    covers = obj(review.get("covers"))
    need(set(covers) == set(COVERS), "both actual cover variants required")
    for key in COVERS:
        cover = obj(covers.get(key))
        checks.evidence(cover, "opening alignment " + key)
        need(cover.get("status") == "pass", key + " actual cover review failed/unreviewed")
        need(cover.get("file") == outputs.get(key) and concrete(cover.get("file")), key + " deliverable path mismatch")
        need(cover.get("sha256") == hashes.get(key) and concrete(cover.get("sha256")), key + " deliverable hash mismatch")
        need(cover.get("question_relation") == "specific_equivalent", key + " core question differs/unreviewed")
        for field in ("observed_title", "core_question", "subject", "comparison"):
            need(concrete(cover.get(field)), key + " actual " + field + " required")
    handoff = obj(review.get("visual_handoff"))
    transition = span(handoff.get("range_s"), "visual handoff", viewed)
    if transition:
        need(transition[0] == 0, "visual handoff must include actual opening entry")
    need(handoff.get("status") == "pass", "visual transition failed/unreviewed")
    need(handoff.get("mode") in ("continuous_subject", "motivated_transition"), "continuous subject or motivated transition required")
    for key in ("opening_subject", "relationship", "observation"):
        need(concrete(handoff.get(key)), "visual handoff " + key + " actual observation required")
    sources = review.get("sources")
    need(isinstance(sources, list) and bool(sources), "actual scoped review sources required")
    covered = set()
    for index, value in enumerate(sources if isinstance(sources, list) else []):
        source = obj(value)
        label = "source " + str(index + 1)
        need(source.get("status") == "pass", label + " failed/unreviewed")
        need(source.get("kind") in ("editor", "independent", "user"), label + " actual editor/independent/user kind required")
        for key in ("reviewer", "reference", "statement"):
            need(concrete(source.get(key)), label + " " + key + " required")
        items = source.get("reviewed_items")
        valid_items = isinstance(items, list) and bool(items) and all(isinstance(i, str) for i in items)
        valid_items = valid_items and set(items) <= REVIEW_ITEMS and len(set(items)) == len(items)
        need(valid_items, label + " explicit reviewed_items subset required")
        selected = set(items) if valid_items else set()
        covered.update(selected)
        source_file = checks.evidence(source.get("evidence"), "opening alignment " + label)
        if source_file:
            try:
                original = source_file.read_text(encoding="utf-8")
                need(concrete(source.get("statement")) and source["statement"] in original,
                     label + " statement missing from bound original review evidence")
            except (OSError, UnicodeError):
                need(False, label + " evidence must be readable original review text")
        for flag in ("actually_watched", "actually_heard"):
            need(type(source.get(flag)) is bool, label + " " + flag + " must describe this source's actual capability/coverage")
        if "cover_question" in selected:
            need(source.get("actually_watched") is True and source.get("method") in (
                 "actual_cover_inspection", "normal_speed_continuous_av"), label + " actual cover inspection required")
        if selected & {"spoken_question", "answer_route", "visual_handoff"}:
            need(source.get("actually_heard") is True and source.get("method") in (
                 "normal_speed_continuous_listening", "normal_speed_continuous_av"), label + " actual normal-speed continuous listening required")
            source_range = span(source.get("range_s"), label + " actual coverage", viewed)
            for item, target in (("spoken_question", question), ("answer_route", answer), ("visual_handoff", transition)):
                if item in selected and source_range and target:
                    need(source_range[0] <= target[0] and source_range[1] >= target[1], label + " actual range does not cover " + item)
        if "visual_handoff" in selected:
            need(source.get("actually_watched") is True and source.get("method") == "normal_speed_continuous_av",
                 label + " actual normal-speed continuous visual handoff review required")
    need(covered == REVIEW_ITEMS, "sources must explicitly cover all opening items; general praise is insufficient")
