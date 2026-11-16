"""Validate registered feedback evidence only; cannot read chats or judge art."""
import json
import hashlib
import math
import re

GATES = tuple(f"G{i}" for i in range(1, 8))
STATIC_DIMENSIONS = {"art", "static_art", "layout", "composition", "color",
                     "lighting", "material", "detail", "style"}


def obj(value):
    return value if isinstance(value, dict) else {}


def seq(value):
    return value if isinstance(value, list) else []


def text(value):
    return isinstance(value, str) and bool(value.strip())


def sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def finite(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def interval(value):
    return (isinstance(value, list) and len(value) == 2
            and all(finite(v) for v in value) and 0 <= value[0] < value[1])


def feedback_context_sha256(row):
    keys = ("feedback_id", "source_ref", "original_feedback", "media_version", "media_sha256",
            "scope", "scope_kind", "time_range_s", "applies_to_gates", "dimensions", "what_changes", "repair_time_range_s")
    payload = {key: row.get(key) for key in keys}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def validate_feedback(checks, target, expanding=False):
    """Opt in per current feedback, preserving untouched legacy packet structure."""
    qa = checks.qa
    rows = qa.get("feedback", [])
    checks.need(isinstance(rows, list), "feedback must be a list")
    expected = qa.get("feedback_expected_ids", [])
    checks.need(isinstance(expected, list) and all(text(i) for i in seq(expected))
                and len(set(i for i in seq(expected) if text(i))) == len(seq(expected)),
                "feedback expected IDs must be unique text IDs")
    ids = [obj(r).get("feedback_id") for r in seq(rows) if text(obj(r).get("feedback_id"))]
    checks.need(len(ids) == len(set(ids)), "feedback IDs must be unique")
    checks.need(set(i for i in seq(expected) if text(i)) <= set(ids),
                "explicit feedback omitted from qa.feedback")
    tracked = set(i for i in seq(expected) if text(i))
    for failure in seq(checks.record("visual_frames").get("failures")):
        ref = obj(failure).get("feedback_id")
        if text(ref):
            tracked.add(ref)
        if ref is not None:
            checks.need(text(ref) and ref in ids, "visual failure references missing feedback")
    for index, raw in enumerate(seq(rows)):
        row = obj(raw)
        # Existing non-user archival rows are not forcibly migrated. Newly received
        # user feedback must declare origin=user, even when no media work is authorized.
        if row.get("origin") != "user" and "contract_version" not in row and (not text(row.get("feedback_id")) or row.get("feedback_id") not in tracked):
            continue
        label = "feedback " + str(row.get("feedback_id", index))
        checks.need(row.get("contract_version") == 1, label + " contract_version required")
        for key in ("feedback_id", "source_ref", "received_at", "original_feedback", "media_version", "scope", "what_changes"):
            checks.need(text(row.get(key)), label + " " + key + " required")
        checks.need(sha(row.get("media_sha256")), label + " original media hash required")
        checks.need(row.get("scope_kind") in ("segment", "whole_episode", "series_style", "static_direction"),
                    label + " explicit scope_kind required")
        original_range = row.get("time_range_s")
        checks.need(original_range == [] or interval(original_range), label + " original time range required; [] means whole stated scope")
        gates = row.get("applies_to_gates")
        checks.need(isinstance(gates, list) and bool(gates)
                    and all(isinstance(g, str) and g in GATES for g in seq(gates)),
                    label + " explicit applicable gates required")
        dimensions = row.get("dimensions")
        checks.need(isinstance(dimensions, dict) and bool(dimensions), label + " dimension results required")
        failed = set()
        for dimension, result in obj(dimensions).items():
            result = obj(result)
            checks.need(text(dimension) and result.get("status") in ("pass", "fail", "pending")
                        and text(result.get("note")), label + " actual scoped dimension finding required")
            if result.get("status") == "fail":
                failed.add(dimension)
        static_only = row.get("scope_kind") == "static_direction"
        if static_only:
            checks.need(original_range == [], label + " static source uses [] time range")
            checks.need(set(obj(dimensions)) <= STATIC_DIMENSIONS,
                        label + " static feedback dimensions must use the static-only whitelist; no audiovisual dimensions or release claims")
        status = row.get("status")
        checks.need(status in ("open", "pending", "candidate", "resolved", "recorded"), label + " status invalid")
        update = obj(row.get("skill_update"))
        checks.need(update.get("disposition") in ("rule_change", "execution_fix", "pending")
                    and text(update.get("proposed_change")), label + " Skill disposition and action required")
        checks.need(update.get("status") in ("pending", "implemented"), label + " Skill update status required")
        if update.get("status") == "implemented":
            for key in ("rule_id", "rule_version"):
                checks.need(text(update.get(key)), label + " Skill " + key + " required")
            checks.evidence(update.get("change_evidence"), label + " Skill change record")
            regressions = update.get("regression_evidence")
            checks.need(isinstance(regressions, list) and bool(regressions), label + " actual regression evidence required")
            for evidence in seq(regressions):
                receipt_path = checks.evidence(evidence, label + " regression")
                if receipt_path:
                    try:
                        receipt = obj(json.loads(receipt_path.read_text(encoding="utf-8")))
                    except (OSError, ValueError, TypeError):
                        receipt = {}
                    checks.need(receipt.get("rule_id") == update.get("rule_id")
                                and receipt.get("rule_version") == update.get("rule_version")
                                and receipt.get("change_sha256") == obj(update.get("change_evidence")).get("sha256"),
                                label + " stale regression rule/version/change binding")
                    checks.need(type(receipt.get("exit_code")) is int and receipt["exit_code"] == 0
                                and receipt.get("result") in ("pass", "tests_pass", "local_checks_pass")
                                and text(receipt.get("command")) and receipt.get("executed") is True,
                                label + " regression must record actual successful execution")
        applicable = [GATES.index(g) for g in seq(gates) if isinstance(g, str) and g in GATES]
        relevant = bool(applicable) and GATES.index(target) >= min(applicable)
        if status != "resolved":
            if relevant and failed:
                checks.need(not expanding, label + " unresolved failed dimensions block expansion")
                mapping = {"art": "visual_frames.art", "motion": "visual_frames.motion", "comprehension": "comprehension"}
                for dimension in failed:
                    if dimension in mapping:
                        checks.need(checks.record(mapping[dimension]).get("status") not in
                                    ("pass", "audience_checked", "editor_reviewed"),
                                    label + " failed " + dimension + " cannot be overwritten by QA pass")
                if failed & {"art", "motion", "layout"}:
                    checks.need(checks.record("visual_frames").get("status") != "pass",
                                label + " failed art/visual dimension cannot become overall visual pass")
            checks.need(not failed or status != "recorded", label + " failed feedback cannot be only recorded")
            continue
        checks.need(not failed or update.get("status") == "implemented", label + " unresolved Skill action cannot close feedback")
        artifacts = row.get("repair_artifacts")
        checks.need(isinstance(artifacts, list) and bool(artifacts), label + " actual repair artifacts required")
        hashes = set()
        durations = {}
        repair_range = row.get("repair_time_range_s")
        checks.need(repair_range == [] if static_only else interval(repair_range),
                    label + " repaired actual time range required; static uses []")
        for artifact in seq(artifacts):
            artifact_path = checks.evidence(artifact, label + " repaired media")
            if artifact_path:
                media_hash = obj(artifact).get("sha256")
                if sha(media_hash):
                    hashes.add(media_hash)
                    if static_only:
                        try:
                            from PIL import Image
                            with Image.open(artifact_path) as picture:
                                checks.need(getattr(picture, "n_frames", 1) == 1, label + " static repair must be a still image")
                                picture.verify()
                        except (ImportError, OSError, ValueError):
                            checks.need(False, label + " actual repaired still image could not be verified")
                    else:
                        durations[media_hash] = checks.duration(artifact_path, label=label + " repaired media")
        retests = row.get("retest_evidence")
        checks.need(isinstance(retests, list) and bool(retests), label + " actual retest required")
        repaired = set()
        current = (checks.record("shotbook").get("viewing") if target == "G2" else
                   checks.record("visual_frames.animation").get("viewing") if target in ("G3", "G4") else
                   {"sha256": obj(qa.get("reviewed_sha256")).get("video")})
        for evidence in seq(retests):
            path = checks.evidence(evidence, label + " retest")
            if path is None:
                continue
            try:
                review = obj(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError, TypeError):
                checks.need(False, label + " retest must be a readable JSON review record")
                continue
            checks.need(review.get("feedback_id") == row.get("feedback_id"), label + " retest feedback mismatch")
            checks.need(review.get("feedback_context_sha256") == feedback_context_sha256(row),
                        label + " stale feedback scope/adjustment in retest")
            checks.need(review.get("scope_kind") == row.get("scope_kind"),
                        label + " local/static retest cannot close a broader feedback scope")
            checks.need(review.get("source_time_range_s") == original_range and text(review.get("scope_mapping")),
                        label + " retest must map original feedback range to repaired range")
            ranges = review.get("ranges")
            review_hash = review.get("media_sha256")
            duration = durations.get(review_hash) if sha(review_hash) else None
            checks.need(review.get("status") == "pass", label + " retest overall status must actually pass")
            valid_ranges = isinstance(ranges, list) and bool(ranges) and all(interval(r) for r in seq(ranges))
            if static_only:
                checks.need(ranges == [] and review.get("normal_speed_continuous_av") in (False, None),
                            label + " static review uses [] ranges and cannot claim continuous playback")
            else:
                checks.need(valid_ranges and duration is not None and all(r[1] <= duration for r in ranges),
                            label + " actual retest ranges must be within repaired media")
            if row.get("scope_kind") in ("whole_episode", "series_style"):
                checks.need(interval(repair_range) and duration is not None and repair_range[0] == 0
                            and abs(repair_range[1] - duration) <= 0.05,
                            label + " whole/style failure cannot close with a partial repair range")
            if valid_ranges and interval(repair_range):
                stop = repair_range[0]
                for start, end in sorted(ranges):
                    if start <= stop:
                        stop = max(stop, end)
                checks.need(stop >= repair_range[1], label + " actual retest does not cover repaired scope")
            checks.need(not failed or review.get("media_sha256") != row.get("media_sha256"),
                        label + " old failed media cannot be its own repair")
            checks.need(sha(review.get("media_sha256")) and review.get("media_sha256") in hashes,
                        label + " retest must bind actual repaired media")
            if relevant and expanding and not static_only:
                checks.need(review.get("media_sha256") == obj(current).get("sha256"),
                            label + " stale retest cannot approve current media")
            checks.need(review.get("actual_viewed") is True and text(review.get("reviewer"))
                        and text(review.get("scope")) and text(review.get("observation")),
                        label + " actual viewing scope/reviewer/observation required")
            if not static_only and failed & {"art", "motion", "comprehension", "layout"}:
                checks.need(review.get("normal_speed_continuous_av") is True,
                            label + " actual continuous audiovisual sample review required")
            outcomes = obj(review.get("dimension_results"))
            if static_only:
                checks.need(set(outcomes) <= STATIC_DIMENSIONS,
                            label + " static retest dimensions must use the static-only whitelist")
            for dimension in obj(dimensions):
                result = obj(outcomes.get(dimension))
                checks.need(result.get("status") == "pass" and text(result.get("observation")),
                            label + " each dimension needs current-version actual retest: " + dimension)
                if result.get("status") == "pass":
                    repaired.add(dimension)
        checks.need(failed <= repaired, label + " failed dimensions not actually retested")
