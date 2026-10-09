#!/usr/bin/env python3
"""Subject-ROI frame-difference screening; never a semantic motion verdict."""
import argparse
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import subprocess

ACTIVE = {"subject_change", "authentic_motion"}
IGNORED = {"captions", "titles", "decoration", "camera_transform", "static_cuts"}


def finite(x):
    try:
        return type(x) in (int, float) and math.isfinite(x)
    except OverflowError:
        return False


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def text(x):
    return isinstance(x, str) and bool(x.strip()) and x.strip().casefold() not in {
        "pending", "todo", "tbd", "n/a", "na", "none", "not_applicable", "not applicable",
        "未验", "待验", "待审", "未审", "不适用", "无"}


def timeline(rows, duration, label):
    if not isinstance(rows, list) or not rows:
        raise ValueError(label + " complete timeline required")
    cursor = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(label + " object required")
        a, b = row.get("start"), row.get("end")
        if not (finite(a) and finite(b) and abs(a-cursor) <= .001 and a < b <= duration+.001):
            raise ValueError(label + " gap/overlap/invalid interval")
        cursor = b
    if abs(cursor-duration) > .001:
        raise ValueError(label + " full media coverage required")


def rect(r):
    if not (isinstance(r, list) and len(r) == 4 and all(finite(x) for x in r)):
        raise ValueError("normalized ROI/mask [x,y,width,height] required")
    x, y, w, h = r
    if not (0 <= x < 1 and 0 <= y < 1 and w > 0 and h > 0 and x+w <= 1 and y+h <= 1):
        raise ValueError("ROI/mask outside frame")
    return r


@lru_cache(maxsize=48)
def _screen(path, media_sha, regions_json, settings_json):
    regions, settings = json.loads(regions_json), json.loads(settings_json)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path],
                           capture_output=True, text=True, check=True, timeout=60)
    meta = json.loads(probe.stdout)
    duration = float(meta["format"]["duration"])
    if not finite(duration) or duration <= 0 or not any(s["codec_type"] == "video" for s in meta["streams"]):
        raise ValueError("screen media needs a valid video duration")
    timeline(regions, duration, "screen regions")
    fps, size = settings["sample_fps"], settings["sample_size"]
    if not (type(fps) is int and 1 <= fps <= 30 and type(size) is int and 16 <= size <= 256):
        raise ValueError("invalid screen sampling settings")
    if not finite(settings["mae_threshold"]) or not 0 < settings["mae_threshold"] < 1:
        raise ValueError("invalid normalized MAE threshold")
    result = []
    for region in regions:
        if not text(region.get("subject")) or not text(region.get("isolation_note")):
            raise ValueError("subject identity and ROI isolation note required")
        x, y, w, h = rect(region.get("roi"))
        masks = region.get("masks")
        if not isinstance(masks, list):
            raise ValueError("explicit mask list required")
        filters = []
        for mask in masks:
            if not isinstance(mask, dict) or mask.get("kind") not in {"captions", "titles", "decoration"}:
                raise ValueError("mask kind must identify non-subject content")
            mx, my, mw, mh = rect(mask.get("rect"))
            # An opaque mask must cover the complete box, including thick edges.
            filters.append(f"drawbox=x=iw*{mx}:y=ih*{my}:w=iw*{mw}:h=ih*{mh}:color=black:t=fill")
        filters += [f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y}", f"fps={fps}", f"scale={size}:{size}", "format=gray"]
        run = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(region["start"]), "-i", path,
                              "-t", str(region["end"]-region["start"]), "-vf", ",".join(filters),
                              "-an", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                             capture_output=True, check=True, timeout=60)
        raw, n = run.stdout, size*size
        if len(raw) < n or len(raw) % n:
            raise ValueError("screen frame decode incomplete")
        count = len(raw)//n
        if abs(count/fps-(region["end"]-region["start"])) > 1/fps+.05:
            raise ValueError("screen frame coverage incomplete")
        previous, start, lows = None, region["start"], []
        for i in range(count):
            frame = raw[i*n:(i+1)*n]
            t = min(region["end"], region["start"]+i/fps)
            if previous is not None:
                mae = sum(abs(a-b) for a, b in zip(previous, frame))/(255*n)
                if mae >= settings["mae_threshold"]:
                    # Exclude the changing sample interval. Retain short still
                    # ranges until region boundaries are merged below.
                    if t-1/fps > start:
                        lows.append([round(start, 6), round(t-1/fps, 6)])
                    start = t
            previous = frame
        if region["end"] > start:
            lows.append([round(start, 6), region["end"]])
        result += lows
    # Region changes/cuts cannot reset an adjacent low-motion interval.
    joined = []
    for a, b in result:
        if joined and a <= joined[-1][1]+.001:
            joined[-1][1] = b
        else:
            joined.append([a, b])
    joined = [[a, b] for a, b in joined if b-a >= settings["candidate_min_seconds"]]
    return {"schema_version": 1, "kind": "subject_roi_screen_only", "media_sha256": media_sha,
            "duration": duration, "settings": settings, "regions": regions, "low_motion_ranges": joined,
            "longest_low_motion_seconds": max((b-a for a, b in joined), default=0)}


def screen(path, regions, settings):
    return _screen(str(Path(path).resolve()), sha(path), json.dumps(regions, sort_keys=True), json.dumps(settings, sort_keys=True))


def validate(checks, record, viewing, gate, policy, step_ids):
    """Validate declared continuous observations plus replayed media screening."""
    prefix = gate + " subject motion "
    def need(ok, msg):
        return checks.need(ok, prefix+msg)
    if not isinstance(record, dict):
        need(False, "review required")
        return
    need(record.get("status") == "pass", "failed/unreviewed")
    from stage_checks import context_sha256
    need(record.get("context_sha256") == context_sha256(checks.data, gate), "stale context")
    need(record.get("media_sha256") == viewing.get("sha256"), "stale media")
    need(text(record.get("roi_review")), "actual subject/mask isolation review required")
    bypass = record.get("excluded_motion_review")
    need(isinstance(bypass, dict) and set(bypass) == IGNORED and all(text(v) for v in bypass.values()),
         "all caption/title/decoration/camera/static-cut bypasses must be reviewed")
    path = checks.evidence(record.get("screen"), prefix+"screen")
    if not path:
        return
    # A report is an immutable stage artifact, not just an unbound text link.
    evidence = checks.record("gates."+gate).get("evidence", [])
    need(isinstance(evidence, list) and record["screen"] in evidence, "screen must be bound in gate evidence")
    media = checks.evidence({"file": viewing.get("file"), "sha256": viewing.get("sha256")}, prefix+"media")
    try:
        report = json.loads(path.read_text())
        actual = screen(media, report["regions"], policy["screen"])
        need(report == actual, "screen stale/tampered; regenerate against current export/settings")
        duration = actual["duration"]
        spans = record.get("spans")
        timeline(spans, duration, prefix+"observed spans")
        units = record.get("semantic_units")
        timeline(units, duration, prefix+"spoken semantic units")
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        need(False, "screen/timeline invalid: "+str(exc))
        return
    inactive_start, longest = None, 0
    for span in spans:
        kind = span.get("kind")
        need(kind in ACTIVE | {"purposeful_read", "no_progress"}, "invalid observed span kind")
        for key in ("subject", "observation", "narration_relation", "evidence"):
            need(text(span.get(key)), "span "+key+" required")
        if kind in ACTIVE:
            if inactive_start is not None:
                longest = max(longest, span["start"]-inactive_start)
            inactive_start = None
        elif inactive_start is None:
            inactive_start = span["start"]
        if kind == "purposeful_read":
            need(span["end"]-span["start"] <= policy["max_purposeful_read_seconds"], "purposeful read too long")
            need(text(span.get("purpose")) and text(span.get("resume_evidence")), "read purpose/resumption evidence required")
    if inactive_start is not None:
        longest = max(longest, duration-inactive_start)
    need(longest <= policy["max_no_progress_seconds"], "longest interval without effective subject progression exceeds project limit")
    need(finite(record.get("longest_no_progress_seconds")) and abs(record["longest_no_progress_seconds"]-longest) <= .001,
         "longest interval declaration inconsistent")
    covered = set()
    for unit in units:
        ids = unit.get("step_ids")
        valid = isinstance(ids, list) and bool(ids) and all(isinstance(i, str) and i in step_ids for i in ids)
        need(valid, "semantic unit must map to reviewed explanation steps")
        if valid:
            covered.update(ids)
        for key in ("spoken_point", "progression_observed", "evidence"):
            need(text(unit.get(key)), "semantic unit "+key+" required")
        need(any(s.get("kind") in ACTIVE and min(s["end"], unit["end"])-max(s["start"], unit["start"]) > .001 for s in spans),
             "complete spoken semantic unit is a slideshow; read pauses do not exempt it")
    need(covered == set(step_ids), "semantic units omit reviewed explanation coverage")
    resolutions = record.get("screen_resolutions")
    need(isinstance(resolutions, list) and len(resolutions) == len(actual["low_motion_ranges"]), "unresolved low-motion screen candidates")
    for interval, resolution in zip(actual["low_motion_ranges"], resolutions if isinstance(resolutions, list) else []):
        need(isinstance(resolution, dict) and resolution.get("range") == interval
             and resolution.get("result") == "effective_subject_progression"
             and text(resolution.get("observation")) and text(resolution.get("evidence")),
             "low-motion candidate needs actual continuous subject-change recheck; static/read-only resolution fails")
        need(any(s.get("kind") in ACTIVE and min(s["end"], interval[1])-max(s["start"], interval[0]) > .001 for s in spans),
             "screen resolution contradicts observed no-progression timeline")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("media", type=Path)
    p.add_argument("--regions", type=Path, required=True, help="JSON array covering the full clip; normalized ROIs/masks")
    p.add_argument("--report", type=Path, required=True, help="new immutable JSON file")
    args = p.parse_args()
    try:
        policy = json.loads((Path(__file__).resolve().parents[1]/"config/production-policy.json").read_text())
        result = screen(args.media, json.loads(args.regions.read_text()), policy["subject_motion"]["screen"])
        with args.report.open("x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("Subject ROI screen saved; continuous semantic/audio-visual review still required.")
        return 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        print("Subject ROI screen failed: "+str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
