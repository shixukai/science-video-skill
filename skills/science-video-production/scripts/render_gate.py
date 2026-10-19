#!/usr/bin/env python3
"""Run a project renderer only after phase-appropriate checks. No quality approval."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

LIMITS = "Records and execution checks do not prove actual viewing, taste, hearing, science or authorization. A rendered candidate remains unreviewed."
SKILL_ROOT = Path(__file__).resolve().parents[1]
IGNORED = {"__pycache__", ".git"}


def obj(x):
    return x if isinstance(x, dict) else {}


def seq(x):
    return x if isinstance(x, list) else []


def digest(x):
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def file_hash(p):
    with Path(p).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def meaningful(x):
    return isinstance(x, str) and x.strip().casefold() not in {"", "pass", "ok", "todo", "pending", "tbd", "none", "unknown", "n/a", "通过", "待审", "待验", "未验", "待补", "无"}


def stamp(x):
    try:
        d = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
        return d if d.utcoffset() is not None and d <= datetime.now(timezone.utc) else None
    except ValueError:
        return None


def skill_snapshot(root=SKILL_ROOT):
    root = Path(root).resolve()
    files = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if any(part in IGNORED for part in rel.parts) or p.suffix == ".pyc":
            continue
        if p.is_symlink():
            raise ValueError("Skill lock does not accept symlinks: " + str(rel))
        if p.is_file():
            files[rel.as_posix()] = file_hash(p)
    return {"version": json.loads((root / "config/series-profile.json").read_text())["version"],
            "files": files, "tree_sha256": digest(files)}


def make_lock(path, root=SKILL_ROOT):
    if Path(path).resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("Skill lock belongs in the private episode directory, outside the installed Skill")
    record = {"schema_version": 1, "kind": "production_skill_lock", "created_at": now(), **skill_snapshot(root)}
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2); f.write("\n")
    return record


def read_record(checks, ref, label):
    p = checks.evidence(ref, label)
    if p is not None:
        try:
            result = json.loads(p.read_text(encoding="utf-8"))
            if checks.need(isinstance(result, dict), label + " must be an object"):
                return result
        except (OSError, ValueError):
            checks.need(False, label + " JSON unreadable")
    return {}


def check_lock(checks):
    record = read_record(checks, obj(checks.data.get("execution")).get("skill_lock"), "execution Skill lock")
    actual = skill_snapshot()
    checks.need(record.get("kind") == "production_skill_lock" and record.get("schema_version") == 1
                and stamp(record.get("created_at")) is not None, "execution valid generated Skill lock required")
    checks.need(all(record.get(k) == v for k, v in actual.items()), "execution installed Skill differs from locked version/hash; explicitly migrate before rendering")
    return record


def input_asset_ids(data, shot_ids):
    required = set()
    for row in seq(data.get("shots")):
        if obj(row).get("id") in shot_ids:
            required.update(x for x in seq(obj(row).get("asset_ids")) if isinstance(x, str))
    narration = obj(data.get("narration")); design = obj(data.get("design"))
    required.update(x for x in (narration.get("asset_id"), design.get("font_asset_id")) if isinstance(x, str) and x)
    required.update(x for x in seq(design.get("render_asset_ids")) if isinstance(x, str))
    return required


def input_snapshot(checks, shot_ids):
    """Declared actual dependencies only, not every unused candidate in the library."""
    data = checks.data; refs = []
    required = input_asset_ids(data, shot_ids)
    assets = [obj(a) for a in seq(data.get("assets")) if obj(a).get("id") in required]
    ids = [a.get("id") for a in assets]
    checks.need(set(ids) == required and len(ids) == len(set(ids)), "execution selected input asset IDs missing/ambiguous")
    for asset in assets:
        refs.append((asset, "asset " + str(asset.get("id"))))
    narration = obj(data.get("narration")); design = obj(data.get("design"))
    if "script_file" in narration:
        refs.append(({"file": narration.get("script_file"), "sha256": narration.get("script_sha256")}, "narration script"))
    if "audio_sha256" in narration:
        audio = next((a for a in assets if a.get("id") == narration.get("asset_id")), {})
        refs.append(({"file": audio.get("file"), "sha256": narration.get("audio_sha256")}, "narration audio"))
    if design.get("board_reference"):
        refs.append(({"file": design.get("board_reference"), "sha256": design.get("board_sha256")}, "design board"))
    execution = obj(data.get("execution")); baseline = obj(design.get("approved_film_reference"))
    refs += [(execution.get(k), k) for k in ("entrypoint", "skill_lock")]
    refs += [(baseline.get(k), "baseline " + k) for k in ("approval_evidence", "viewing")]
    refs += [(obj(frame).get("image"), "baseline visual frame") for frame in seq(obj(baseline.get("viewing")).get("frames"))]
    from realism_guard import references as realism_references
    refs += list(realism_references(data, shot_ids))
    from origin_guard import references as origin_references
    refs += list(origin_references(data, shot_ids))
    snapshot = {}
    for reference, label in refs:
        path = checks.evidence(reference, "execution input " + label)
        if path is not None:
            snapshot[path.relative_to(checks.root).as_posix()] = file_hash(path)
    return snapshot


def design_context(data, shot_ids):
    """Freeze render inputs, excluding later review declarations and output hashes."""
    shots = []
    for row in seq(data.get("shots")):
        if obj(row).get("id") not in shot_ids:
            continue
        row = dict(row)
        row["shotbook"] = {k: v for k, v in obj(row.get("shotbook")).items()
                           if k not in {"status", "keyframe_review", "render_file", "render_sha256"}}
        shots.append(row)
    result = {k: data.get(k) for k in ("episode_id", "topic", "scope", "origin_contract", "assets", "narration", "design", "presentation_text")}
    from origin_guard import context_assets as origin_assets
    result["origin_assets"] = origin_assets(data, shot_ids)
    result["assets"] = [{k: v for k, v in obj(a).items() if k not in {"catalog", "rights", "observation"}} for a in seq(data.get("assets")) if obj(a).get("id") in input_asset_ids(data, shot_ids)]
    design = {k: v for k, v in obj(data.get("design")).items() if k not in {"approval", "actual_deviations"}}
    design["keyframe_scales"] = {name: {k: v for k, v in obj(frame).items() if k not in {"status", "note", "evidence", "reviewer", "reviewed_at"}} for name, frame in obj(design.get("keyframe_scales")).items()}
    baseline = dict(obj(design.get("approved_film_reference")))
    baseline["viewing"] = {k: obj(baseline.get("viewing")).get(k) for k in ("file", "sha256")}
    design["approved_film_reference"] = baseline
    result["design"] = design
    result["scope"] = {k: v for k, v in obj(result["scope"]).items() if k != "publication_ready"}
    result["topic_selection_sha256"] = selection_context_sha256(data)
    result.update(shots=shots, entrypoint=obj(data.get("execution")).get("entrypoint"),
                  skill_lock=obj(data.get("execution")).get("skill_lock"))
    return digest(result)


def selected_design(checks, shot_ids):
    rows = seq(checks.data.get("shots")); ids = [obj(r).get("id") for r in rows]
    checks.need(bool(ids) and all(meaningful(i) for i in ids) and len(set(i for i in ids if isinstance(i, str))) == len(ids), "execution unique shot IDs required")
    checks.need(bool(shot_ids) and all(isinstance(i, str) for i in shot_ids) and len(set(i for i in shot_ids if isinstance(i, str))) == len(shot_ids) and shot_ids == [i for i in ids if i in shot_ids], "execution explicit valid shot selection required")
    for row in rows:
        row = obj(row)
        if row.get("id") not in shot_ids:
            continue
        book = obj(row.get("shotbook"))
        for field in ("claim_support", "subject", "action", "attention_target", "viewer_takeaway"):
            checks.need(meaningful(book.get(field)), "execution shot " + str(row.get("id")) + " design missing " + field)


def check_baseline(checks):
    baseline = obj(obj(checks.data.get("design")).get("approved_film_reference"))
    checks.need(baseline.get("kind") == "approved_finished_film", "execution approved actual finished-film baseline required, not generic stills")
    checks.need(meaningful(baseline.get("approval_reference")) and meaningful(baseline.get("applicable_style")), "execution traceable baseline approval and applicable style required")
    checks.evidence(baseline.get("approval_evidence"), "execution baseline approval evidence")
    view = obj(baseline.get("viewing"))
    if view.get("method") == "frame_samples":
        # A finite visual reference may guide a candidate. It is never evidence
        # of motion/hearing or a replacement for G3/full-episode playback.
        from cover_guard import image_size
        path = checks.evidence(view, "execution approved baseline")
        duration = checks.duration(path, require_audio=False) if path else None
        checks.need(view.get("scope") == "approved_film_visual_reference" and view.get("purpose") == "appearance_only",
                    "execution finite baseline reference must be appearance-only scoped")
        checks.need(view.get("watched") is True and view.get("heard") is False
                    and view.get("playback_speed") is None and view.get("ranges") == [],
                    "execution frame samples require honest visual-only, not listening/continuous playback declarations")
        for field in ("reviewer", "capability", "reviewed_at", "note"):
            checks.need(meaningful(view.get(field)), "execution baseline visual " + field + " required")
        number = lambda value: isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
        checks.need(number(duration) and number(view.get("duration")) and abs(view["duration"] - duration) < .05,
                    "execution baseline duration must match actual finished film")
        frames = seq(view.get("frames"))
        checks.need(bool(frames), "execution baseline actual visual frame observations required")
        for frame in frames:
            frame = obj(frame); at = frame.get("time")
            checks.need(number(at) and number(duration) and 0 <= at < duration,
                        "execution baseline frame time outside actual film")
            checks.need(frame.get("source_sha256") == view.get("sha256") and frame.get("actually_opened") is True
                        and meaningful(frame.get("observation")), "execution baseline frame must bind source and actual visual observation")
            image_size(checks, frame.get("image"), "execution baseline visual frame")
    else:
        view = checks.viewing(view, "execution approved baseline", "approved_film")
    checks.need(baseline.get("approved_media_sha256") == view.get("sha256"), "execution baseline approval must bind actual film")
    checks.need(stamp(view.get("reviewed_at")) is not None, "execution baseline viewing timestamp invalid/future")
    return view.get("sha256")


def validate_receipt(checks, reference, phase):
    r = read_record(checks, reference, "execution " + phase + " render receipt")
    checks.need(r.get("kind") == "guarded_render_receipt" and r.get("schema_version") == 1
                and r.get("phase") == phase and r.get("result") == "rendered_unreviewed"
                and r.get("returncode") == 0 and r.get("preflight_errors") == [], "execution successful actual " + phase + " invocation receipt required")
    ids = seq(r.get("shot_ids")); selected_design(checks, ids)
    checks.need(r.get("design_sha256") == design_context(checks.data, ids), "execution stale " + phase + " design/renderer/baseline binding")
    checks.need(r.get("skill_tree_sha256") == skill_snapshot()["tree_sha256"], "execution stale " + phase + " Skill binding")
    start, end = stamp(r.get("started_at")), stamp(r.get("completed_at"))
    lock = read_record(checks, obj(checks.data.get("execution")).get("skill_lock"), "execution Skill lock")
    locked = stamp(lock.get("created_at"))
    checks.need(bool(start and end and locked and locked <= start <= end), "execution lock and design receipt must precede actual rendering; do not backfill history")
    checks.evidence(r.get("output"), "execution " + phase + " actual output")
    return r


from topic_selection_guard import validate_topic_selection, selection_context_sha256


def preflight(data, root, phase, shot_ids):
    from stage_checks import Checks, check_stage
    c = Checks(data, root)
    c.need(phase in ("sample", "full"), "execution phase must be sample or full")
    validate_topic_selection(c)
    from realism_guard import validate_realism
    validate_realism(c, shot_ids, phase)
    from origin_guard import validate_origin
    validate_origin(c, shot_ids, final=phase == "full")
    check_lock(c); selected_design(c, shot_ids); baseline_hash = check_baseline(c)
    input_snapshot(c, shot_ids)
    from connection_guard import plans as connection_plans
    connection_plans(c, shot_ids)
    entry = c.evidence(obj(data.get("execution")).get("entrypoint"), "execution renderer entrypoint")
    c.need(entry is not None and entry.suffix == ".py", "execution project Python adapter required")
    if phase == "full":
        c.need(shot_ids == [obj(s).get("id") for s in seq(data.get("shots"))], "execution full render must include every designed shot in order")
        c.need(c.record("visual_frames.animation").get("next_action") == "expand", "execution full render requires explicit expansion after sample review")
        c.expansion_failures(True)
        c.errors.extend(check_stage(data, root, "G3"))
        for key in ("technical", "audio", "narration"):
            c.need(c.record(key).get("status") not in ("fail", "failed", "blocked", "needs_changes"), "execution known " + key + " failure blocks expansion")
        r = validate_receipt(c, obj(data.get("execution")).get("sample_receipt"), "sample")
        review = c.record("visual_frames.animation")
        viewed, rendered = stamp(obj(review.get("viewing")).get("reviewed_at")), stamp(r.get("completed_at"))
        c.need(bool(viewed and rendered and rendered <= viewed), "execution sample must actually be viewed after its render completed")
        c.need(obj(r.get("output")) == {k: obj(review.get("viewing")).get(k) for k in ("file", "sha256")}, "execution reviewed sample must be the guarded render output")
        compare = obj(review.get("style_comparison"))
        c.need(compare.get("status") == "pass" and compare.get("baseline_sha256") == baseline_hash
               and compare.get("sample_sha256") == obj(r.get("output")).get("sha256")
               and compare.get("actually_compared") is True and meaningful(compare.get("observation")), "execution actual same-style sample comparison missing/failed")
    return c.errors


def validate_final_execution(checks):
    """G5-G7 reuse their full playback records; keep three results separate."""
    from realism_guard import validate_realism
    validate_realism(checks, [obj(s).get('id') for s in seq(checks.data.get('shots'))], 'full')
    from origin_guard import validate_origin
    validate_origin(checks, [obj(s).get("id") for s in seq(checks.data.get("shots"))], final=True)
    check_lock(checks)
    r = validate_receipt(checks, obj(checks.data.get("execution")).get("full_receipt"), "full")
    checks.need(r.get("shot_ids") == [obj(s).get("id") for s in seq(checks.data.get("shots"))], "execution final receipt must cover the complete episode")
    checks.need(obj(r.get("output")) == {"file": obj(checks.data.get("deliverables")).get("video"), "sha256": obj(checks.qa.get("reviewed_sha256")).get("video")}, "execution final review must bind guarded full render output")
    producer = obj(obj(checks.data.get("brief")).get("roles")).get("producer")
    checks.need(meaningful(producer), "execution producer identity required")
    for key in ("technical", "visual_frames", "audio"):
        checks.need(checks.record(key).get("status") == "pass", "execution separate " + key + " result must pass; technical checks cannot certify aesthetics/hearing")
    records = [checks.record("visual_frames").get("viewing")]
    records += list(obj(checks.record("audio").get("listening")).values())
    for raw in records:
        record = obj(raw); reviewer = record.get("reviewer")
        checks.need(meaningful(reviewer) and isinstance(producer, str) and reviewer.strip().casefold() != producer.strip().casefold(), "execution independent full-film visual/listening reviewer must differ from producer")
        reviewed, rendered = stamp(record.get("reviewed_at")), stamp(r.get("completed_at"))
        checks.need(bool(reviewed and rendered and rendered <= reviewed), "execution complete viewing/listening must occur after rendering")


def safe_new(root, name):
    p = (root / name).resolve()
    if Path(name).is_absolute() or not p.is_relative_to(root) or p.exists() or (root / name).is_symlink():
        raise ValueError("new output/receipt must be unused and inside episode directory: " + name)
    return p


def run_render(episode, phase, shot_ids, output, receipt):
    from stage_checks import Checks
    episode = Path(episode).resolve(); root = episode.parent
    raw = episode.read_bytes(); data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("episode must be an object")
    out = safe_new(root, output); rec = safe_new(root, receipt)
    if out == rec:
        raise ValueError("output and receipt must differ")
    errors = preflight(data, root, phase, shot_ids)
    input_checks = Checks(data, root); inputs = input_snapshot(input_checks, shot_ids); errors.extend(input_checks.errors)
    entry = (root / obj(obj(data.get("execution")).get("entrypoint")).get("file", "")).resolve()
    command = [sys.executable, str(entry), "--episode", str(episode), "--phase", phase,
               "--shot-ids", ",".join(shot_ids), "--output", str(out)]
    record = {"schema_version": 1, "kind": "guarded_render_receipt", "phase": phase,
              "shot_ids": shot_ids, "started_at": now(), "completed_at": None,
              "episode_sha256": hashlib.sha256(raw).hexdigest(), "design_sha256": design_context(data, shot_ids),
              "skill_tree_sha256": skill_snapshot()["tree_sha256"], "command": command,
              "input_files": inputs, "preflight_errors": errors, "returncode": None, "result": "blocked" if errors else "started",
              "limits": LIMITS}
    # Persist the real pre-render design/version snapshot BEFORE invoking the
    # renderer. A crash leaves started, never a successful or reviewed receipt.
    with rec.open("x", encoding="utf-8") as f:
        def save():
            f.seek(0); json.dump(record, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n"); f.truncate(); f.flush(); os.fsync(f.fileno())
        save()
        if errors:
            return 1, record
        if file_hash(episode) != record["episode_sha256"]:
            record.update(result="input_changed", completed_at=now()); save(); return 2, record
        # Recheck all evidence just before the command, not merely an old report.
        errors = preflight(data, root, phase, shot_ids)
        if errors:
            record.update(result="blocked", preflight_errors=errors, completed_at=now()); save(); return 1, record
        try:
            result = subprocess.run(command, cwd=root, check=False)
            record.update(returncode=result.returncode, completed_at=now(), result="render_failed")
            if result.returncode == 0 and out.is_file() and not out.is_symlink():
                probe = Checks(data, root); probe.duration(out)
                if input_snapshot(probe, shot_ids) != inputs:
                    probe.errors.append("actual render input bytes changed during invocation")
                if file_hash(episode) != record["episode_sha256"] or skill_snapshot()["tree_sha256"] != record["skill_tree_sha256"]:
                    probe.errors.append("render inputs changed during invocation")
                if file_hash(entry) != obj(obj(data.get("execution")).get("entrypoint")).get("sha256"):
                    probe.errors.append("renderer changed during invocation")
                record["output_checks"] = probe.errors
                if not probe.errors:
                    record.update(result="rendered_unreviewed", output={"file": output, "sha256": file_hash(out)})
            save()
        except (OSError, ValueError) as exc:
            record.update(result="render_failed", error=str(exc), completed_at=now()); save()
        return (0 if record["result"] == "rendered_unreviewed" else 2), record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    lock = sub.add_parser("lock"); lock.add_argument("output", type=Path)
    run = sub.add_parser("run"); run.add_argument("episode", type=Path)
    run.add_argument("--phase", choices=("sample", "full"), required=True)
    run.add_argument("--shot-ids", required=True, help="ordered comma-separated shot IDs; adapter must honor this scope")
    run.add_argument("--output", required=True, help="new episode-relative audiovisual output")
    run.add_argument("--receipt", required=True, help="new episode-relative execution receipt")
    args = parser.parse_args()
    try:
        if args.action == "lock":
            record = make_lock(args.output); print(record["version"], record["tree_sha256"]); return 0
        code, record = run_render(args.episode, args.phase, args.shot_ids.split(","), args.output, args.receipt)
        print(record["result"]); print(LIMITS)
        for error in record.get("preflight_errors", []):
            print(error)
        return code
    except (OSError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
