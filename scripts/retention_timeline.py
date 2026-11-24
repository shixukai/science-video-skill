#!/usr/bin/env python3
"""Whole-film retention-risk locator for an actual export.

``measure`` decodes a complete export with local FFmpeg, reads the episode's
viewing promise, open-loop ledger (``payoff_steps[].opens_question`` /
``closes_question`` / ``time_s``) and ``ending.answer_time_s``, and reports
intervals worth rewatching at normal speed:

- ``late_viewing_promise``: the promise finishes after the promise window.
- ``payoff_gap_over_review``: a stretch without a timed payoff step.
- ``no_open_question_interval``: after the promise and before the final
  answer, no recorded question is open.
- ``final_answer_early``: the main question closes early in the runtime.
- ``long_tail_after_answer``: the film continues long after the final answer.
- ``long_low_change_shot``: one shot runs long with little visual change.
- ``mid_video_black_or_blank_frame``: pitch-black camera clip-through frames or
  sustained low-detail blank/off-subject background stretches inside the body.
- ``low_cut_density``: a >= 25 s film averages very few scene cuts per 10 s,
  flagging risk of single-shot orbiting monotony.
- ``silent_mix_interval``: the mixed soundtrack is silent for a while.

Untimed ledger fields are reported under ``missing``, never as passed. The
numbers locate intervals only; they are not a gate, a score or an audience
prediction. Intended flags take a concrete reason in ``exceptions``.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

SCHEMA_VERSION = 1
FLAGS = (
    "late_viewing_promise", "payoff_gap_over_review", "no_open_question_interval",
    "final_answer_early", "long_tail_after_answer", "long_low_change_shot",
    "mid_video_black_or_blank_frame", "low_cut_density", "silent_mix_interval",
)
MAIN = "main"


def obj(value):
    return value if isinstance(value, dict) else {}


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_policy(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    policy = json.loads((root / "config/production-policy.json").read_text(encoding="utf-8"))
    return policy["retention_design"]


def _norm(text):
    return re.sub(r"\s+", "", text) if isinstance(text, str) else ""


# ---------------------------------------------------------------------------
# Ledger analysis (pure functions, no media)
# ---------------------------------------------------------------------------

def ledger_from_episode(data):
    """Extract promise, timed payoff steps and answer time from an episode dict."""
    ta = obj(data.get("topic_alignment"))
    opening = obj(ta.get("opening"))
    ending = obj(ta.get("ending"))
    promise = obj(opening.get("viewing_promise"))
    missing = []
    promise_time = promise.get("time_s")
    if not finite(promise_time):
        promise_time = None
        missing.append("topic_alignment.opening.viewing_promise.time_s")
    steps = []
    raw = opening.get("payoff_steps") if isinstance(opening.get("payoff_steps"), list) else []
    for index, step in enumerate(raw):
        step = obj(step)
        label = step.get("scope_id") or ("step" + str(index + 1))
        if not finite(step.get("time_s")):
            missing.append("payoff_steps[%d].time_s (%s)" % (index, label))
            continue
        steps.append({
            "label": str(label),
            "time_s": float(step["time_s"]),
            "opens": _norm(step.get("opens_question")),
            "closes": _norm(step.get("closes_question")),
        })
    steps.sort(key=lambda s: s["time_s"])
    answer = ending.get("answer_time_s")
    if not finite(answer):
        answer = None
        missing.append("topic_alignment.ending.answer_time_s")
    return {"promise_time_s": promise_time, "steps": steps, "answer_time_s": answer,
            "missing": missing, "ledger_recorded": any(s["opens"] or s["closes"] for s in steps)}


def main_close_time(ledger):
    for step in ledger["steps"]:
        if step["closes"] == MAIN:
            return step["time_s"]
    return ledger["answer_time_s"]


def payoff_gaps(ledger, duration, threshold):
    """Gaps between consecutive timed payoffs, from the promise (or 0) to the final answer."""
    times = [s["time_s"] for s in ledger["steps"]]
    start = ledger["promise_time_s"] if ledger["promise_time_s"] is not None else 0.0
    end = main_close_time(ledger)
    end = end if end is not None else duration
    points = sorted({round(t, 3) for t in [start] + times + [end] if start <= t <= end})
    gaps = []
    for a, b in zip(points, points[1:]):
        if b - a > threshold:
            gaps.append([round(a, 3), round(b, 3)])
    return gaps


def open_question_intervals(ledger, window_start, min_len):
    """Intervals inside [window_start, final answer) where no recorded question is open.

    The main question opens at 0 and closes at the first ``closes_question=main``
    step or at ``ending.answer_time_s``. Sub-questions open at their step time and
    close at the step whose ``closes_question`` matches them; unclosed ones stay
    open until the final answer.
    """
    end = ledger["answer_time_s"]
    if end is None:
        end = main_close_time(ledger)
    if end is None or not ledger["ledger_recorded"]:
        return None
    events = [(0.0, "open", MAIN)]
    main_close = main_close_time(ledger)
    if main_close is not None:
        events.append((main_close, "close", MAIN))
    for step in ledger["steps"]:
        if step["closes"] and step["closes"] != MAIN:
            events.append((step["time_s"], "close", step["closes"]))
        if step["opens"]:
            events.append((step["time_s"], "open", step["opens"]))
    # At equal times process closes before opens so a hand-off counts as continuous.
    events.sort(key=lambda e: (e[0], 0 if e[1] == "close" else 1))
    open_set, empty_since, empty = set(), None, []
    for t, kind, q in events:
        if t >= end:
            break
        if kind == "open":
            open_set.add(q)
            if empty_since is not None:
                empty.append([empty_since, t])
                empty_since = None
        else:
            open_set.discard(q)
            if not open_set and empty_since is None:
                empty_since = t
    if empty_since is not None:
        empty.append([empty_since, end])
    result = []
    for a, b in empty:
        a = max(a, window_start)
        if b - a >= min_len:
            result.append([round(a, 3), round(b, 3)])
    return result


def ledger_flags(ledger, duration, policy):
    flags, intervals = [], {}
    promise_end = policy["promise_window_s"][1]
    if ledger["promise_time_s"] is not None and ledger["promise_time_s"] > promise_end:
        flags.append("late_viewing_promise")
        intervals["late_viewing_promise"] = [[round(ledger["promise_time_s"], 3), round(ledger["promise_time_s"], 3)]]
    gaps = payoff_gaps(ledger, duration, policy["payoff_gap_review_s"]) if ledger["steps"] else []
    if gaps:
        flags.append("payoff_gap_over_review")
        intervals["payoff_gap_over_review"] = gaps
    empty = open_question_intervals(ledger, promise_end, policy["no_open_question_min_s"])
    if empty:
        flags.append("no_open_question_interval")
        intervals["no_open_question_interval"] = empty
    close = main_close_time(ledger)
    if close is not None and duration > 0 and close / duration < policy["final_answer_min_ratio"]:
        flags.append("final_answer_early")
        intervals["final_answer_early"] = [[round(close, 3), round(close, 3)]]
    if ledger["answer_time_s"] is not None and duration - ledger["answer_time_s"] > policy["answer_to_end_review_s"]:
        flags.append("long_tail_after_answer")
        intervals["long_tail_after_answer"] = [[round(ledger["answer_time_s"], 3), round(duration, 3)]]
    return flags, intervals, empty


# ---------------------------------------------------------------------------
# Media measurement
# ---------------------------------------------------------------------------

def _run(args, timeout=600):
    return subprocess.run(args, capture_output=True, check=True, timeout=timeout)


def _probe(path):
    run = _run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], 60)
    meta = json.loads(run.stdout.decode("utf-8", "replace"))
    duration = float(meta["format"]["duration"])
    streams = meta.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if video is None or not finite(duration) or duration <= 0:
        raise ValueError("retention timeline needs a decodable video stream")
    return duration, video, audio


def _decode_luma_stats(path, fps, size):
    w, h = size
    run = _run(["ffmpeg", "-v", "error", "-i", str(path), "-an",
                "-vf", f"fps={fps},scale={w}:{h}:flags=area,format=gray",
                "-f", "rawvideo", "-pix_fmt", "gray", "-"])
    n = w * h
    raw = run.stdout
    frames = [raw[i * n:(i + 1) * n] for i in range(len(raw) // n)]
    if len(frames) < 2:
        raise ValueError("export frames could not be decoded")
    motion = [sum(abs(x - y) for x, y in zip(a, b)) / (255.0 * n) for a, b in zip(frames, frames[1:])]
    means, stds = [], []
    for frame in frames:
        mean = sum(frame) / (255.0 * n)
        var = sum((b / 255.0 - mean) ** 2 for b in frame) / n
        means.append(mean)
        stds.append(math.sqrt(var))
    return motion, means, stds


def _motion(path, fps, size):
    motion, _, _ = _decode_luma_stats(path, fps, size)
    return motion


def blank_or_black_intervals(means, stds, fps, duration, policy):
    """Locate mid-video pitch-black clip-through frames or sustained low-detail blank stretches."""
    black_max = policy.get("blank_frame_luma_max", 0.03)
    std_max = policy.get("low_detail_std_max", 0.045)
    low_min_s = policy.get("low_detail_min_s", 1.0)
    margin = 0.5
    findings = []

    # 1. Mid-video pitch-black frames (camera clipping through opaque walls/doors)
    b_start = None
    for idx, mean in enumerate(means):
        t = idx / fps
        if margin <= t <= duration - margin and mean < black_max:
            if b_start is None:
                b_start = t
        elif b_start is not None:
            findings.append({"kind": "mid_video_black_frame", "interval": [round(b_start, 3), round(t, 3)]})
            b_start = None
    if b_start is not None:
        findings.append({"kind": "mid_video_black_frame", "interval": [round(b_start, 3), round(min(duration, len(means) / fps), 3)]})

    # 2. Sustained low-detail blank/off-subject background stretches (e.g. empty fabric/wall)
    l_start = None
    for idx, std in enumerate(stds):
        t = idx / fps
        if margin <= t <= duration - margin and std < std_max and means[idx] >= black_max:
            if l_start is None:
                l_start = t
        elif l_start is not None:
            if t - l_start >= low_min_s:
                findings.append({"kind": "low_detail_blank_stretch", "interval": [round(l_start, 3), round(t, 3)]})
            l_start = None
    if l_start is not None:
        end_t = min(duration, len(stds) / fps)
        if end_t - l_start >= low_min_s:
            findings.append({"kind": "low_detail_blank_stretch", "interval": [round(l_start, 3), round(end_t, 3)]})
    return findings


def _cuts(path, threshold):
    run = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-an",
                          "-vf", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"],
                         capture_output=True, timeout=600)
    if run.returncode != 0:
        raise RuntimeError("scene detection failed")
    text = run.stderr.decode("utf-8", "replace")
    return sorted({round(float(t), 3) for t in re.findall(r"pts_time:([0-9.]+)", text)})


def _silences(path, dbfs, min_s):
    run = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-vn",
                          "-af", f"silencedetect=noise={dbfs}dB:d={min_s}", "-f", "null", "-"],
                         capture_output=True, timeout=600)
    if run.returncode != 0:
        raise RuntimeError("silence detection failed")
    text = run.stderr.decode("utf-8", "replace")
    starts = [float(v) for v in re.findall(r"silence_start: (-?[0-9.]+)", text)]
    ends = [float(v) for v in re.findall(r"silence_end: ([0-9.]+)", text)]
    out = []
    for i, start in enumerate(starts):
        end = ends[i] if i < len(ends) else None
        out.append([round(max(0.0, start), 3), round(end, 3) if end is not None else None])
    return out


def shot_spans(cuts, duration):
    edges = [0.0] + [c for c in cuts if 0 < c < duration] + [duration]
    return [[round(a, 3), round(b, 3)] for a, b in zip(edges, edges[1:]) if b > a]


def long_low_change_shots(spans, motion, fps, policy):
    out = []
    for a, b in spans:
        if b - a <= policy["long_shot_review_s"]:
            continue
        lo, hi = int(a * fps), max(int(a * fps) + 1, int(b * fps) - 1)
        seg = motion[lo:hi]
        mean = sum(seg) / len(seg) if seg else 0.0
        if mean < policy["long_shot_low_change_mae"]:
            out.append({"interval": [a, b], "mean_mae": round(mean, 6)})
    return out


def _timeline_png(out, duration, motion, fps, cuts, silences, ledger, intervals, empty):
    from PIL import Image, ImageDraw
    W, H, L, R = 1600, 380, 60, 20
    img = Image.new("RGB", (W, H), (250, 250, 247))
    d = ImageDraw.Draw(img)
    x = lambda t: L + (W - L - R) * max(0.0, min(duration, t)) / duration
    shade = {"payoff_gap_over_review": (255, 214, 153), "no_open_question_interval": (255, 179, 179),
             "long_tail_after_answer": (220, 200, 255), "long_low_change_shot": (210, 225, 255)}
    for name, color in shade.items():
        for item in intervals.get(name, []):
            a, b = item["interval"] if isinstance(item, dict) else item
            d.rectangle([x(a), 40, max(x(a) + 1, x(b)), 300], fill=color)
    for a, b in silences:
        d.rectangle([x(a), 285, x(b if b is not None else duration), 300], fill=(150, 150, 150))
    peak = max(motion) or 1.0
    pts = [(x((i + 1) / fps), 260 - 180 * m / peak) for i, m in enumerate(motion)]
    if len(pts) > 1:
        d.line(pts, fill=(40, 70, 90), width=2)
    for c in cuts:
        d.line([x(c), 40, x(c), 60], fill=(0, 0, 0), width=1)
    for s in ledger["steps"]:
        d.line([x(s["time_s"]), 300, x(s["time_s"]), 330], fill=(30, 140, 60), width=3)
        d.text((x(s["time_s"]) + 3, 332), s["label"][:10], fill=(30, 100, 50))
    if ledger["promise_time_s"] is not None:
        d.line([x(ledger["promise_time_s"]), 40, x(ledger["promise_time_s"]), 330], fill=(40, 90, 220), width=2)
        d.text((x(ledger["promise_time_s"]) + 3, 22), "promise", fill=(40, 90, 220))
    close = main_close_time(ledger)
    if close is not None:
        d.line([x(close), 40, x(close), 330], fill=(200, 40, 40), width=3)
        d.text((x(close) + 3, 22), "answer", fill=(200, 40, 40))
    for t in range(0, int(duration) + 1, 10):
        d.line([x(t), 300, x(t), 306], fill=(0, 0, 0))
        d.text((x(t) - 6, 356), str(t), fill=(0, 0, 0))
    d.text((8, 4), "motion (line) | cuts (top ticks) | payoffs (green) | silence (grey) | "
                   "orange=payoff gap  red=no open question  violet=tail  blue=long low-change shot", fill=(0, 0, 0))
    img.save(out)


def measure(video, episode, policy, preview_dir=None, report_path=None):
    video, episode = Path(video), Path(episode)
    base = Path(report_path).resolve().parent if report_path else video.resolve().parent

    def rel(path):
        return Path(os.path.relpath(Path(path).resolve(), base)).as_posix()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required for the retention timeline")
    data = json.loads(episode.read_text(encoding="utf-8"))
    duration, vstream, astream = _probe(video)
    fps, size = policy["sample_fps"], policy["sample_size"]
    motion, luma_means, luma_stds = _decode_luma_stats(video, fps, size)
    cuts = _cuts(video, policy["scene_cut_threshold"])
    spans = shot_spans(cuts, duration)
    silences = _silences(video, policy["silence_dbfs"], policy["silence_min_s"]) if astream else []
    silences = [[a, b if b is not None else round(duration, 3)] for a, b in silences]
    ledger = ledger_from_episode(data)
    flags, intervals, empty = ledger_flags(ledger, duration, policy)
    long_shots = long_low_change_shots(spans, motion, fps, policy)
    if long_shots:
        flags.append("long_low_change_shot")
        intervals["long_low_change_shot"] = long_shots
    blanks = blank_or_black_intervals(luma_means, luma_stds, fps, duration, policy)
    if blanks:
        flags.append("mid_video_black_or_blank_frame")
        intervals["mid_video_black_or_blank_frame"] = blanks
    cuts_per_10s = round(len(cuts) / (duration / 10.0), 3) if duration > 0 else 0.0
    min_cuts = policy.get("min_cuts_per_10s_review")
    if finite(min_cuts) and duration >= 25.0 and cuts_per_10s < min_cuts:
        flags.append("low_cut_density")
        intervals["low_cut_density"] = [[0.0, round(duration, 3)]]
    audible_silences = [s for s in silences if s[1] - s[0] >= policy["silence_min_s"]]
    if audible_silences:
        flags.append("silent_mix_interval")
        intervals["silent_mix_interval"] = audible_silences
    lengths = sorted(b - a for a, b in spans)
    report = {
        "schema_version": SCHEMA_VERSION,
        "tool": "scripts/retention_timeline.py",
        "video": {"file": rel(video), "sha256": sha256_file(video), "duration_s": round(duration, 3),
                  "width": vstream.get("width"), "height": vstream.get("height")},
        "episode": {"file": rel(episode), "sha256": sha256_file(episode)},
        "policy": {k: policy[k] for k in (
            "promise_window_s", "payoff_gap_review_s", "no_open_question_min_s", "final_answer_min_ratio",
            "answer_to_end_review_s", "long_shot_review_s", "long_shot_low_change_mae",
            "blank_frame_luma_max", "low_detail_std_max", "low_detail_min_s", "min_cuts_per_10s_review",
            "scene_cut_threshold", "silence_dbfs", "silence_min_s", "sample_fps", "sample_size") if k in policy},
        "measurements": {
            "audio_stream": astream is not None,
            "cut_times_s": cuts,
            "shot_count": len(spans),
            "cuts_per_10s": cuts_per_10s,
            "median_shot_s": round(lengths[len(lengths) // 2], 3) if lengths else None,
            "longest_shot_s": round(lengths[-1], 3) if lengths else None,
            "viewing_promise_time_s": ledger["promise_time_s"],
            "payoff_times_s": [s["time_s"] for s in ledger["steps"]],
            "main_answer_time_s": main_close_time(ledger),
            "main_answer_ratio": round(main_close_time(ledger) / duration, 3) if main_close_time(ledger) is not None else None,
            "answer_to_end_s": round(duration - ledger["answer_time_s"], 3) if ledger["answer_time_s"] is not None else None,
            "open_loop_ledger_recorded": ledger["ledger_recorded"],
            "silences_s": silences,
        },
        "flags": flags,
        "intervals": intervals,
        "missing": ledger["missing"] + ([] if ledger["ledger_recorded"] else
                                        ["payoff_steps[].opens_question/closes_question (open-loop ledger)"]),
        "exceptions": {},
        "timeline": None,
        "limits": "Locator only: rewatch flagged intervals at normal speed. Not a gate, score or audience prediction.",
    }
    if preview_dir:
        out_dir = Path(preview_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        png = out_dir / (video.stem + "-retention-timeline.png")
        _timeline_png(png, duration, motion, fps, cuts, silences, ledger, intervals, empty)
        report["timeline"] = {"file": rel(png), "sha256": sha256_file(png)}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("measure", help="locate retention risks on an actual export")
    m.add_argument("video", type=Path)
    m.add_argument("--episode", type=Path, required=True, help="episode.json with the timed open-loop ledger")
    m.add_argument("--preview-dir", type=Path, help="write a local timeline PNG here")
    m.add_argument("--report", type=Path, required=True, help="new JSON report path inside the episode directory")
    p = sub.add_parser("ledger", help="check the open-loop ledger in an episode.json without media")
    p.add_argument("episode", type=Path)
    p.add_argument("--duration", type=float, required=True, help="planned or actual runtime in seconds")
    args = parser.parse_args(argv)
    try:
        policy = load_policy()
        if args.command == "ledger":
            data = json.loads(args.episode.read_text(encoding="utf-8"))
            ledger = ledger_from_episode(data)
            flags, intervals, _ = ledger_flags(ledger, args.duration, policy)
            print(json.dumps({"flags": flags, "intervals": intervals, "missing": ledger["missing"]},
                             ensure_ascii=False, indent=2))
            return 1 if flags else 0
        if args.report.exists():
            raise ValueError("report exists; use a new receipt filename")
        report = measure(args.video, args.episode, policy, args.preview_dir, args.report)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(args.report), "flags": report["flags"], "missing": report["missing"]},
                         ensure_ascii=False, indent=2))
        return 1 if report["flags"] else 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
