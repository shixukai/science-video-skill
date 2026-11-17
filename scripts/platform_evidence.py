"""Local evidence utilities; never infer audience causes or fill missing observations.

Input JSON: {"curves": {"work-alias": [{"time_s": 2, "value": 50}]},
"comments": [{"id": "c", "parent_id": null, "author_id": "v"}],
"owner_id": "owner", "comments_complete": false}.
Keep real account inputs/results outside this repository. Values retain their original
units; callers establish metric/cohort compatibility before comparing curves.
"""
import argparse
import json
import math
from pathlib import Path


def align_observed_times(curves):
    """Outer-join observed timestamps, retaining nulls, never interpolate."""
    indexed = {}
    for name, points in curves.items():
        samples = {}
        for point in points:
            time = point["time_s"]
            if isinstance(time, bool) or not isinstance(time, (int, float)) or not math.isfinite(time) or time < 0:
                raise ValueError("time_s must be a finite nonnegative number")
            if time in samples:
                raise ValueError("duplicate timestamp: reconcile source snapshots first")
            samples[time] = point["value"]
        indexed[name] = samples
    times = sorted({time for samples in indexed.values() for time in samples})
    return [{"time_s": time, "values": {name: samples.get(time) for name, samples in indexed.items()},
             "observed": {name: time in samples for name, samples in indexed.items()}} for time in times]


def summarize_comments(comments, owner_id=None, complete=False):
    """Count retrieved records only; unknown identities are not inferred people."""
    unique = {}
    for comment in comments:
        identity = comment.get("id")
        if not isinstance(identity, str) or not identity:
            raise ValueError("comment ID required for deduplication")
        parent = comment.get("parent_id")
        relation = "unknown" if "parent_id" not in comment or parent == "" else "root" if parent is None else "reply"
        if relation == "reply" and not isinstance(parent, str):
            raise ValueError("parent_id must be null, a nonempty ID or unknown")
        author = comment.get("author_id")
        if author is not None and not isinstance(author, str):
            raise ValueError("author_id must be a string or null")
        normalized = {"id": identity, "parent_id": parent, "author_id": author, "relation": relation}
        if identity in unique and unique[identity] != normalized:
            raise ValueError("conflicting comment identity; reconcile snapshots first")
        unique[identity] = normalized
    rows = list(unique.values())
    roots = sum(row["relation"] == "root" for row in rows)
    known_authors = {row["author_id"] for row in rows if row["author_id"]}
    return {"retrieved_unique_comments": len(rows), "retrieved_root_threads": roots,
            "retrieved_replies": sum(row["relation"] == "reply" for row in rows),
            "unknown_relationship_records": sum(row["relation"] == "unknown" for row in rows),
            "distinct_non_owner_commenters": len(known_authors - {owner_id}) if owner_id else None,
            "unknown_author_records": sum(not row["author_id"] for row in rows),
            "owner_reply_count": sum(row["author_id"] == owner_id and row["relation"] == "reply" for row in rows) if owner_id else None,
            "coverage": "declared_complete" if complete is True else "partial_or_unknown",
            "audience_consensus": "not_inferred"}


def summarize_media_observations(published_version, observations):
    """Group supplied observations, not verification; never inherit across surfaces.

    Each record identifies version, surface (publication_text/captions/narration),
    and a nonempty observation. Media records also need finite start_s/end_s.
    Intervals describe observed coverage, not inferred subtitle boundaries.
    """
    if not isinstance(published_version, str) or not published_version.strip():
        raise ValueError("published version required")
    surfaces = {key: [] for key in ("publication_text", "captions", "narration")}
    excluded = 0
    for record in observations:
        version = record.get("version")
        if not isinstance(version, str) or not version.strip():
            raise ValueError("observation version required")
        surface = record.get("surface")
        if surface not in surfaces:
            raise ValueError("unknown observation surface")
        note = record.get("observation")
        if not isinstance(note, str) or not note.strip():
            raise ValueError("actual observation required")
        result = {"observation": note}
        if surface != "publication_text":
            start, end = record.get("start_s"), record.get("end_s")
            for value in (start, end):
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    raise ValueError("finite nonnegative media observation interval required")
            if end < start:
                raise ValueError("observation interval reversed")
            result.update(start_s=start, end_s=end)
        if version != published_version:
            excluded += 1
            continue
        surfaces[surface].append(result)
    return {"published_version": published_version,
            "surfaces": {key: {"coverage": "observed_intervals_only" if rows else "unknown",
                               "observations": rows} for key, rows in surfaces.items()},
            "other_version_records": excluded,
            "scientific_correctness": "not_assessed",
            "continuous_audiovisual_review": "not_assessed",
            "correction_verification": "not_assessed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    result = {"aligned_observations": align_observed_times(data.get("curves", {})),
              "comment_coverage": summarize_comments(data.get("comments", []), data.get("owner_id"), data.get("comments_complete", False))}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
