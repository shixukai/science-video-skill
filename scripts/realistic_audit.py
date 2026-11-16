#!/usr/bin/env python3
"""Realistic-film edit screening for an actual export.

``measure`` decodes a small proxy of every frame and the audio of an exported
film with local FFmpeg and reports places a reviewer should look at:
variable or off-policy frame rate, duplicated frames inside motion (typical of
24->30 conversion), runs of shots with nearly identical length, untrimmed
image-to-video ramp heads, freeze-padded tails, grade jumps across cuts inside
one labeled scene, near-digital-silence gaps and a missing audio stream.

Thresholds are calibratable starting points from
``config/production-policy.json`` ``realistic_audit``. The report is
screening evidence only: a flag is a place to look, an intentional choice is
recorded as such in existing review notes, and a clean report proves nothing
about science, story, sound quality or beauty.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import struct
import subprocess
import sys

SCHEMA_VERSION = 1
FLAGS = (
    "frame_rate_mismatch", "duplicate_frames_in_motion", "uniform_cadence", "slow_ramp_head",
    "frozen_tail", "grade_jump_in_scene", "digital_silence", "no_audio_stream",
)
AUDIO_RATE, AUDIO_WINDOW_S = 16000, 0.01
SCOPE = ("Screening only: flags locate places to review in the actual export; they are not "
         "acceptance, and a clean report does not establish science, story, sound or look quality.")


def load_policy(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    policy = json.loads((root / "config/production-policy.json").read_text(encoding="utf-8"))
    audit = dict(policy["realistic_audit"])
    audit.setdefault("delivery_fps", policy["defaults"]["output"]["fps"])
    return audit


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_rate(text):
    """Parse an FFprobe rational such as ``30000/1001``; None when unusable."""
    try:
        if isinstance(text, str) and "/" in text:
            num, den = text.split("/", 1)
            num, den = float(num), float(den)
            return num / den if den else None
        value = float(text)
        return value if value > 0 else None
    except (TypeError, ValueError):
        return None


def _run(args, timeout=900):
    return subprocess.run(args, capture_output=True, check=True, timeout=timeout)


def probe(path):
    run = _run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], 120)
    meta = json.loads(run.stdout.decode("utf-8", "replace"))
    streams = meta.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(meta.get("format", {}).get("duration") or 0)
    if video is None or not math.isfinite(duration) or duration <= 0:
        raise ValueError("audit media needs a decodable video stream with a duration")
    return {
        "duration_s": round(duration, 3),
        "width": video.get("width"), "height": video.get("height"),
        "r_frame_rate": video.get("r_frame_rate"), "avg_frame_rate": video.get("avg_frame_rate"),
        "has_audio": audio is not None,
    }


def decode_frames(path, width, height):
    run = _run(["ffmpeg", "-v", "error", "-i", str(path), "-an",
                "-vf", f"scale={width}:{height}:flags=area,format=rgb24",
                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    size = width * height * 3
    raw = run.stdout
    if len(raw) < size * 2:
        raise ValueError("too few video frames decoded for an edit audit")
    return [raw[i * size:(i + 1) * size] for i in range(len(raw) // size)]


def decode_audio(path):
    run = _run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(AUDIO_RATE),
                "-f", "s16le", "-"])
    count = len(run.stdout) // 2
    return struct.unpack("<%dh" % count, run.stdout[:count * 2]) if count else ()


def frame_features(frame):
    """Mean luma, blue/red color-difference and saturation of an RGB24 proxy frame (0-1)."""
    n = len(frame) // 3
    ys = cbs = crs = sats = 0.0
    for i in range(0, len(frame), 3):
        r, g, b = frame[i], frame[i + 1], frame[i + 2]
        y = 0.2126 * r + 0.7152 * g + 0.0722 * b
        ys += y
        cbs += b - y
        crs += r - y
        sats += max(r, g, b) - min(r, g, b)
    scale = 255.0 * n
    return {"luma": ys / scale, "cb": cbs / scale, "cr": crs / scale, "saturation": sats / scale}


def frame_diffs(frames):
    """Mean absolute RGB difference to the previous frame; index 0 is 0."""
    diffs = [0.0]
    for prev, cur in zip(frames, frames[1:]):
        diffs.append(sum(abs(a - b) for a, b in zip(prev, cur)) / (255.0 * len(cur)))
    return diffs


def detect_cuts(diffs, fps, cfg):
    window = int(cfg["window_frames"])
    min_gap = max(1, round(cfg["min_shot_s"] * fps))
    cuts = []
    for i in range(1, len(diffs)):
        d = diffs[i]
        if d < cfg["min_diff"]:
            continue
        neighbors = [diffs[k] for k in range(max(1, i - window), min(len(diffs), i + window + 1)) if k != i]
        local = statistics.median(neighbors) if neighbors else 0.0
        if d >= cfg["local_ratio"] * max(local, 1e-6) and (not cuts or i - cuts[-1] >= min_gap):
            cuts.append(i)
    return cuts


def load_shots(path, fps, frame_count):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, list) or not data:
        raise ValueError("shots file must be a nonempty JSON list of {id, start_s, scene}")
    shots, seen, last = [], set(), -1
    for entry in data:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not entry["id"].strip():
            raise ValueError("each shot needs a nonempty string id")
        start = entry.get("start_s")
        if isinstance(start, bool) or not isinstance(start, (int, float)) or not math.isfinite(start) or start < 0:
            raise ValueError(f"shot {entry['id']}: start_s must be a nonnegative number")
        frame = round(start * fps)
        if entry["id"] in seen or frame <= last or frame >= frame_count:
            raise ValueError(f"shot {entry['id']}: ids must be unique and starts strictly increasing within the film")
        scene = entry.get("scene")
        if scene is not None and not isinstance(scene, str):
            raise ValueError(f"shot {entry['id']}: scene must be a string when present")
        seen.add(entry["id"])
        last = frame
        shots.append({"id": entry["id"], "start": frame, "scene": (scene or "").strip() or None})
    if shots[0]["start"] > 1:
        raise ValueError("the first shot must start at the beginning of the film")
    shots[0]["start"] = 0
    return shots


def build_shots(starts_or_shots, frame_count):
    if starts_or_shots and isinstance(starts_or_shots[0], dict):
        shots = [dict(s) for s in starts_or_shots]
    else:
        starts = [0] + [c for c in starts_or_shots if c > 0]
        shots = [{"id": f"auto-{n + 1}", "start": s, "scene": None} for n, s in enumerate(starts)]
    for n, shot in enumerate(shots):
        shot["end"] = shots[n + 1]["start"] if n + 1 < len(shots) else frame_count
    return shots


def cadence_runs(durations, cfg):
    """Runs of consecutive shots whose lengths are nearly identical."""
    tol, min_len, run_min = cfg["tolerance_ratio"], cfg["min_shot_s"], int(cfg["run_min"])
    runs = []

    def close(run):
        return len(run) >= 2 and (max(run) - min(run)) <= 2 * tol * (sum(run) / len(run))

    i = 0
    while i < len(durations):
        if durations[i] < min_len:
            i += 1
            continue
        j = i + 1
        while j < len(durations) and durations[j] >= min_len and close(durations[i:j + 1]) \
                and abs(durations[j] - durations[j - 1]) <= tol * max(durations[j], durations[j - 1]):
            j += 1
        if j - i >= run_min:
            runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def shot_motion_flags(diffs, shot, fps, ramp, frozen):
    start, end = shot["start"], shot["end"]
    w = max(1, round(ramp["window_s"] * fps))
    wt = max(1, round(frozen["window_s"] * fps))
    found = {}
    body = diffs[start + 1 + w:end - wt]
    if end - start < 3 * max(w, wt) or not body:
        return found, None
    body_median = statistics.median(body)
    head = diffs[start + 1:start + 1 + w]
    tail = diffs[end - wt:end]
    if body_median >= ramp["motion_floor"] and head and sum(head) / len(head) < ramp["head_ratio"] * body_median:
        found["slow_ramp_head"] = round(sum(head) / len(head), 5)
    if body_median >= ramp["motion_floor"] and tail and max(tail) <= frozen["motion_max"]:
        found["frozen_tail"] = round(max(tail), 5)
    return found, round(body_median, 5)


def duplicate_frames(diffs, cut_set, cfg):
    dups = moving = 0
    times = []
    for i in range(2, len(diffs) - 1):
        if i in cut_set or i + 1 in cut_set:
            continue
        if diffs[i] >= cfg["motion_eps"]:
            moving += 1
        elif diffs[i] <= cfg["dup_eps"] and diffs[i - 1] >= cfg["motion_eps"] and diffs[i + 1] >= cfg["motion_eps"]:
            dups += 1
            moving += 1
            times.append(i)
    ratio = dups / moving if moving else 0.0
    return dups, moving, ratio, times


def silence_gaps(samples, gate_dbfs, min_s):
    window = int(AUDIO_RATE * AUDIO_WINDOW_S)
    gaps, run_start = [], None
    total = len(samples) - window + 1
    for start in range(0, max(total, 0), window):
        chunk = samples[start:start + window]
        rms = math.sqrt(sum(s * s for s in chunk) / window) / 32768.0
        quiet = rms <= 0 or 20 * math.log10(rms) < gate_dbfs
        if quiet and run_start is None:
            run_start = start
        elif not quiet and run_start is not None:
            if (start - run_start) / AUDIO_RATE >= min_s:
                gaps.append([round(run_start / AUDIO_RATE, 3), round(start / AUDIO_RATE, 3)])
            run_start = None
    if run_start is not None and (len(samples) - run_start) / AUDIO_RATE >= min_s:
        gaps.append([round(run_start / AUDIO_RATE, 3), round(len(samples) / AUDIO_RATE, 3)])
    return gaps


def _mean_features(features, lo, hi):
    part = features[lo:hi]
    return {k: sum(f[k] for f in part) / len(part) for k in part[0]}


def _preview_pair(video, t_before, t_after, out):
    _run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(t_before, 0):.3f}", "-i", str(video),
          "-ss", f"{max(t_after, 0):.3f}", "-i", str(video), "-filter_complex",
          "[0:v]scale=480:-2[a];[1:v]scale=480:-2[b];[a][b]hstack", "-frames:v", "1", str(out)], 120)


def measure(video, policy, shots_path=None, preview_dir=None, report_path=None):
    video = Path(video)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required for the realistic edit audit")
    stream = probe(video)
    fps = parse_rate(stream["avg_frame_rate"]) or parse_rate(stream["r_frame_rate"])
    if not fps:
        raise ValueError("cannot determine the export frame rate")
    width, height = policy["frame_size"]
    frames = decode_frames(video, width, height)
    features = [frame_features(f) for f in frames]
    diffs = frame_diffs(frames)
    findings = []

    def find(flag, at_s, detail, shot_id=None):
        item = {"flag": flag, "at_s": round(at_s, 3) if at_s is not None else None, "detail": detail}
        if shot_id is not None:
            item["shot_id"] = shot_id
        findings.append(item)

    r_rate = parse_rate(stream["r_frame_rate"])
    target = float(policy["delivery_fps"])
    if not r_rate or abs(r_rate - fps) > 0.01 * fps or abs(fps - target) > 0.01 * target:
        find("frame_rate_mismatch", None, f"r_frame_rate={stream['r_frame_rate']} avg_frame_rate="
             f"{stream['avg_frame_rate']} delivery_fps={target:g}")

    if shots_path:
        shots = build_shots(load_shots(shots_path, fps, len(frames)), len(frames))
        cut_source = "shots_file"
    else:
        shots = build_shots(detect_cuts(diffs, fps, policy["cut_detection"]), len(frames))
        cut_source = "detected"
    cut_set = {s["start"] for s in shots[1:]}

    dups, moving, ratio, dup_frames = duplicate_frames(diffs, cut_set, policy["duplicate"])
    if dups >= int(policy["duplicate"]["min_count"]) and ratio > policy["duplicate"]["ratio_max"]:
        find("duplicate_frames_in_motion", dup_frames[0] / fps,
             f"{dups} repeated frames in {moving} moving frames (ratio {ratio:.3f})")

    shot_records = []
    for shot in shots:
        flags, body = shot_motion_flags(diffs, shot, fps, policy["ramp_head"], policy["frozen_tail"])
        record = {"id": shot["id"], "scene": shot["scene"], "start_s": round(shot["start"] / fps, 3),
                  "end_s": round(shot["end"] / fps, 3), "duration_s": round((shot["end"] - shot["start"]) / fps, 3),
                  "body_motion": body, "flags": sorted(flags)}
        for flag, value in sorted(flags.items()):
            at = shot["start"] if flag == "slow_ramp_head" else shot["end"] - 1
            find(flag, at / fps, f"shot {shot['id']} motion {value} against body {body}", shot["id"])
        shot_records.append(record)

    durations = [r["duration_s"] for r in shot_records]
    runs = []
    for i, j in cadence_runs(durations, policy["cadence"]):
        ids = [shot_records[k]["id"] for k in range(i, j)]
        runs.append({"shot_ids": ids, "durations_s": durations[i:j]})
        find("uniform_cadence", shot_records[i]["start_s"],
             f"{j - i} consecutive shots of {min(durations[i:j]):.2f}-{max(durations[i:j]):.2f} s: {', '.join(ids)}")

    jump_cfg = policy["grade_jump"]
    w = max(1, round(jump_cfg["window_s"] * fps))
    cut_records = []
    for a, b in zip(shots, shots[1:]):
        before = _mean_features(features, max(a["start"], b["start"] - w), b["start"])
        after = _mean_features(features, b["start"], min(b["end"], b["start"] + w))
        delta = {"luma": abs(after["luma"] - before["luma"]),
                 "chroma": math.hypot(after["cb"] - before["cb"], after["cr"] - before["cr"]),
                 "saturation": abs(after["saturation"] - before["saturation"])}
        same_scene = bool(a["scene"]) and a["scene"] == b["scene"]
        over = [k for k in delta if delta[k] > jump_cfg[k]]
        flagged = same_scene and bool(over)
        record = {"at_s": round(b["start"] / fps, 3), "from": a["id"], "to": b["id"], "same_scene": same_scene,
                  "delta_luma": round(delta["luma"], 4), "delta_chroma": round(delta["chroma"], 4),
                  "delta_saturation": round(delta["saturation"], 4), "flagged": flagged}
        if flagged:
            find("grade_jump_in_scene", record["at_s"], f"{a['id']}->{b['id']} in scene {a['scene']}: {', '.join(over)}")
        cut_records.append(record)

    audio = {"present": stream["has_audio"], "digital_silence": []}
    if not stream["has_audio"]:
        find("no_audio_stream", None, "export has no audio stream")
    else:
        silence = policy["digital_silence"]
        audio["digital_silence"] = silence_gaps(decode_audio(video), silence["gate_dbfs"], silence["min_s"])
        for gap in audio["digital_silence"]:
            find("digital_silence", gap[0], f"near-digital silence {gap[0]:.2f}-{gap[1]:.2f} s")

    previews = []
    if preview_dir is not None:
        preview_dir = Path(preview_dir)
        preview_dir.mkdir(parents=True, exist_ok=True)
        half = 0.5 / fps
        by_id = {s["id"]: s for s in shots}
        for n, item in enumerate(f for f in findings if f["flag"] in ("grade_jump_in_scene", "slow_ramp_head", "frozen_tail")):
            out = preview_dir / f"{video.stem}-audit-{n + 1:02d}-{item['flag']}.png"
            if item["flag"] == "grade_jump_in_scene":
                # Last frames of the outgoing shot beside the first frame of the incoming shot.
                pair = (item["at_s"] - w / fps, item["at_s"] + 0.25 / fps)
            else:
                shot = by_id[item["shot_id"]]
                body = (shot["start"] + shot["end"]) / 2 / fps
                # Seek a little inside the final frame: seeking exactly at the stream end decodes nothing.
                first, last = shot["start"] / fps + 0.25 / fps, max(shot["start"], shot["end"] - 2) / fps + half
                # Ramp head: first frame beside a body frame. Frozen tail: body frame beside the last frame.
                pair = (first, body) if item["flag"] == "slow_ramp_head" else (body, last)
            _preview_pair(video, pair[0], pair[1], out)
            if out.is_file():
                previews.append(str(out))

    def rel(path):
        base = Path(report_path).resolve().parent if report_path else None
        p = Path(path).resolve()
        if base:
            try:
                return os.path.relpath(p, base).replace(os.sep, "/")
            except ValueError:
                pass
        return str(p)

    return {
        "schema_version": SCHEMA_VERSION,
        "tool": "scripts/realistic_audit.py",
        "scope": SCOPE,
        "video": {"file": rel(video), "sha256": sha256_file(video)},
        "stream": dict(stream, decoded_frames=len(frames), fps=round(fps, 4)),
        "cut_source": cut_source,
        "thresholds": {k: policy[k] for k in ("cut_detection", "cadence", "ramp_head", "frozen_tail",
                                              "duplicate", "grade_jump", "digital_silence")},
        "shots": shot_records,
        "cuts": cut_records,
        "cadence_runs": runs,
        "duplicates": {"count": dups, "moving_frames": moving, "ratio": round(ratio, 4)},
        "audio": audio,
        "previews": [rel(p) for p in previews],
        "findings": findings,
        "flags": sorted({f["flag"] for f in findings}),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("measure", help="screen an actual realistic-film export")
    m.add_argument("video", type=Path)
    m.add_argument("--shots", type=Path, help="JSON list of {id, start_s, scene} from the actual edit")
    m.add_argument("--preview-dir", type=Path, help="write before/after frame pairs for flagged cuts and shots")
    m.add_argument("--report", type=Path, required=True, help="new JSON report path")
    m.add_argument("--delivery-fps", type=float, help="episode design.output fps when it differs from the policy default")
    args = parser.parse_args(argv)
    try:
        if args.report.exists():
            raise ValueError("report exists; use a new receipt filename")
        policy = load_policy()
        if args.delivery_fps is not None:
            if not math.isfinite(args.delivery_fps) or args.delivery_fps <= 0:
                raise ValueError("--delivery-fps must be a positive number")
            policy["delivery_fps"] = args.delivery_fps
        report = measure(args.video, policy, args.shots, args.preview_dir, args.report)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(args.report), "flags": report["flags"],
                          "findings": report["findings"]}, ensure_ascii=False, indent=2))
        return 1 if report["flags"] else 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
