"""Check declared connector plans and actual-review bindings, never infer physical quality."""
from cover_guard import image_size, meaningful
import hashlib
import json

OBSERVATIONS = ("topology_and_ports", "diameter_and_transition", "joint_geometry", "occlusion", "continuity")
VIEWS = {"overview", "joint_closeup", "motion_or_cut_key_states"}


def obj(x):
    return x if isinstance(x, dict) else {}


def seq(x):
    return x if isinstance(x, list) else []


def digest(x):
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def endpoint(x):
    return {k: obj(x).get(k) for k in ("object_id", "port_id", "role")}


def pair(row):
    return sorted([endpoint(obj(row).get("from")), endpoint(obj(row).get("to"))], key=lambda x: json.dumps(x, sort_keys=True))


def plans(checks, shot_ids):
    """N/A is one truthful reason, not an invented connector or forced uniform diameter."""
    found = {}; identities = {}
    for raw in seq(checks.data.get("shots")):
        shot = obj(raw); sid = shot.get("id")
        if sid not in shot_ids:
            continue
        plan = obj(obj(shot.get("shotbook")).get("connections")); links = plan.get("links")
        label = "connections " + str(sid)
        checks.need(isinstance(plan.get("applicable"), bool), label + " applicability must be explicitly assessed")
        if plan.get("applicable") is False:
            checks.need(links == [] and meaningful(plan.get("not_applicable_reason")), label + " truthful N/A needs no links and a reason")
            continue
        checks.need(isinstance(links, list) and bool(links), label + " actual connection topology required")
        for raw_link in seq(links):
            link = obj(raw_link); ident = link.get("id")
            if not checks.need(meaningful(ident), label + " stable connection ID required"):
                continue
            key = (sid, ident)
            checks.need(key not in found, label + " duplicate connection ID")
            found[key] = link
            checks.need(link.get("kind") in ("pipe", "cable", "linkage", "other"), label + " applicable connector kind required")
            for side in ("from", "to"):
                checks.need(meaningful(obj(link.get(side)).get("role_basis")) and obj(link.get(side)).get("role_basis", "").strip().casefold() not in {"unverified", "未核实", "待确认"}, label + " " + ident + " verified port-role basis required; do not infer from color")
                for name, value in endpoint(link.get(side)).items():
                    checks.need(meaningful(value), label + " " + ident + " " + side + "." + name + " required")
            a, b = endpoint(link.get("from")), endpoint(link.get("to"))
            checks.need((a["object_id"], a["port_id"]) != (b["object_id"], b["port_id"]), label + " connection cannot attach both ends to the same port")
            for name in OBSERVATIONS[1:]:
                checks.need(meaningful(link.get(name)), label + " " + ident + " planned " + name + " required")
            if ident in identities and pair(link) != identities[ident]:
                checks.need(meaningful(link.get("topology_change_reason")), label + " unexplained endpoint/role change across shots")
            identities[ident] = pair(link)
    return found


def plan_sha256(data, shot_ids):
    return digest([{ "shot_id": obj(s).get("id"), "connections": obj(obj(s).get("shotbook")).get("connections")}
                   for s in seq(data.get("shots")) if obj(s).get("id") in shot_ids])


def validate_connection_review(checks, stage, shot_ids):
    expected = plans(checks, shot_ids)
    if not expected:
        return
    parent = checks.record("visual_frames.animation" if stage == "G3" else "visual_frames")
    record = obj(parent.get("connection_review")); view = obj(parent.get("viewing"))
    label = "connections " + stage
    checks.need(record.get("status") == "pass" and record.get("actually_inspected") is True,
                label + " actual physical/visual inspection required; technical fields are insufficient")
    checks.need(record.get("media_sha256") == view.get("sha256") and meaningful(view.get("sha256")), label + " stale actual clip binding")
    checks.need(record.get("plan_sha256") == plan_sha256(checks.data, shot_ids), label + " stale connector plan binding")
    checks.need(meaningful(record.get("reviewer")) and record.get("reviewer") == view.get("reviewer"), label + " reviewer must match actual continuous viewing")
    seen = set()
    for raw in seq(record.get("links")):
        row = obj(raw); sid = row.get("shot_id"); ident = row.get("connection_id")
        if not checks.need(isinstance(sid, str) and isinstance(ident, str), label + " review must identify shot and connection"):
            continue
        key = (sid, ident)
        if not checks.need(key in expected and key not in seen, label + " missing/duplicate/unknown connection review"):
            continue
        seen.add(key); plan = expected[key]
        checks.need(row.get("status") == "pass" and row.get("issues") == [], label + " unresolved physical/visual connection issue")
        checks.need(pair(row) == pair(plan), label + " observed topology/port roles do not match design")
        for name in OBSERVATIONS:
            checks.need(meaningful(obj(row.get("observations")).get(name)), label + " actual " + name + " observation required")
        kinds = set()
        for raw_evidence in seq(row.get("views")):
            evidence = obj(raw_evidence); kind = evidence.get("kind")
            if checks.need(isinstance(kind, str) and kind in VIEWS and kind not in kinds, label + " overview/interface/key-state view type invalid/duplicate"):
                kinds.add(kind)
            image_size(checks, evidence, label + " actual inspection view")
            checks.need(evidence.get("source_media_sha256") == view.get("sha256") and evidence.get("actually_opened") is True
                        and meaningful(evidence.get("observation")), label + " inspection view must be opened and bound to actual clip")
        checks.need(kinds == VIEWS, label + " full scene, joint closeup and motion/cut key states must all be inspected")
    checks.need(seen == set(expected), label + " every applicable connection must be reviewed")
