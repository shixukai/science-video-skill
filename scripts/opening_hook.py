#!/usr/bin/env python3
"""First-two-seconds hook measurement and evidence contract.

``measure`` decodes only the opening window of an actual export with local
FFmpeg and records objective technical openers that commonly lose feed viewers:
black/fade-in starts, a frozen or barely moving first half-second, late sound onset, late first
caption and a murky low-contrast first frame. It also writes local phone-feed
previews for the cold two-second test.

The numbers are screening evidence, never a perceptual pass: whether the first
two seconds actually stop a scrolling viewer is decided by the recorded
cold test of a reviewer who actually watched and heard the bound file.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

SCHEMA_VERSION = 1
FLAGS = (
    "black_first_frame", "fade_in_from_black", "low_motion_first_half_second",
    "low_motion_until_payload_deadline", "late_audio_onset", "late_first_caption",
    "low_contrast_first_frame",
)
PATTERNS = (
    "result_first", "strange_phenomenon", "extreme_contrast", "question_with_evidence",
    "satisfying_process", "stakes_in_action", "extreme_scale", "failure_or_breakage",
)
HOST_RELATIONS = ("standalone", "part_of_host")
COLD_METHODS = ("normal_speed_continuous_av",)
FRAME_W, FRAME_H, FRAME_FPS = 64, 36, 10
AUDIO_RATE, AUDIO_WINDOW_S = 16000, 0.01


def obj(value):
    return value if isinstance(value, dict) else {}


def concrete(value):
    return isinstance(value, str) and value.strip().lower() not in (
        "", "pass", "ok", "pending", "unknown", "todo", "tbd", "n/a", "none",
        "未验", "待验", "待审", "通过", "无")


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
    return policy["opening_hook"]


def spoken_units(text):
    """Count Mandarin syllable-bearing units: CJK characters plus Latin/digit words."""
    if not isinstance(text, str):
        return 0
    cjk = len(re.findall(r"[\u3400-\u9fff\uf900-\ufaff]", text))
    words = len(re.findall(r"[A-Za-z0-9]+(?:[.%][A-Za-z0-9]+)*", text))
    return cjk + words


def check_hook_plan(opening, policy):
    """Plan-level structure for a newly designed hook; never a judgment of appeal."""
    hook = obj(opening.get("hook"))
    errors = []
    def need(ok, message):
        if not ok:
            errors.append("opening hook: " + message)
    for key in ("first_frame", "frame0_motion", "first_sound", "first_line", "payload_clause",
                "tension", "muted_read", "phone_read"):
        need(concrete(hook.get(key)), "hook." + key + " concrete plan required")
    need(hook.get("pattern") in PATTERNS, "hook.pattern must be one of " + "/".join(PATTERNS))
    if any(k in hook for k in ("host_relation", "host_system", "whole_to_part_bridge")):
        relation = hook.get("host_relation")
        need(relation in HOST_RELATIONS, "hook.host_relation must be one of " + "/".join(HOST_RELATIONS))
        if relation == "part_of_host":
            need(concrete(hook.get("host_system")),
                 "hook.host_system concrete host object or functional host cabin/bay required when host_relation=part_of_host")
            need(concrete(hook.get("whole_to_part_bridge")),
                 "hook.whole_to_part_bridge concrete 0-5 s host-to-mechanism single-take/cutaway orientation plan required when host_relation=part_of_host")
    line, payload = hook.get("first_line"), hook.get("payload_clause")
    if concrete(line) and concrete(payload):
        position = line.find(payload)
        need(position >= 0, "hook.payload_clause must be quoted verbatim from hook.first_line")
        if position >= 0:
            units = spoken_units(line[:position + len(payload)])
            limit = policy["payload_max_spoken_units"]
            need(units <= limit, f"hook payload ends after {units} spoken units; front-load it within "
                 f"{limit} so it lands by about {policy['payload_deadline_s']} s at series pace")
    voiceover = opening.get("voiceover")
    if concrete(line) and concrete(voiceover):
        need(voiceover.strip().startswith(line.strip()), "opening.voiceover must start with hook.first_line")
    candidates = hook.get("candidates")
    minimum = policy["min_candidates"]
    valid = isinstance(candidates, list) and len(candidates) >= minimum
    need(valid, f"at least {minimum} compared hook candidates required")
    if valid:
        selected = [c for c in candidates if obj(c).get("selected") is True]
        need(len(selected) == 1, "exactly one selected hook candidate required")
        patterns = {obj(c).get("pattern") for c in candidates}
        need(len(patterns) >= 2, "hook candidates must explore at least two different patterns")
        for index, value in enumerate(candidates):
            c = obj(value)
            for key in ("first_frame", "first_line", "tension"):
                need(concrete(c.get(key)), f"candidate {index + 1} {key} required")
            need(c.get("pattern") in PATTERNS, f"candidate {index + 1} pattern invalid")
            if not c.get("selected"):
                need(concrete(c.get("lost_because")), f"candidate {index + 1} lost_because required")
    return errors


# ---------------------------------------------------------------- measurement

def _run(args, timeout=120):
    return subprocess.run(args, capture_output=True, check=True, timeout=timeout)


def _probe(path):
    run = _run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], 60)
    meta = json.loads(run.stdout.decode("utf-8", "replace"))
    duration = float(meta["format"]["duration"])
    streams = meta.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if video is None or not finite(duration) or duration <= 0:
        raise ValueError("opening hook media needs a decodable video stream")
    return duration, video, audio


def _frames(path, seconds):
    run = _run(["ffmpeg", "-v", "error", "-i", str(path), "-t", f"{seconds:.3f}", "-an",
                "-vf", f"fps={FRAME_FPS},scale={FRAME_W}:{FRAME_H}:flags=area,format=gray",
                "-f", "rawvideo", "-pix_fmt", "gray", "-"])
    n = FRAME_W * FRAME_H
    raw = run.stdout
    if len(raw) < n:
        raise ValueError("opening frames could not be decoded")
    return [raw[i * n:(i + 1) * n] for i in range(len(raw) // n)]


def _mean(frame):
    return sum(frame) / (255.0 * len(frame))


def _std(frame):
    m = sum(frame) / len(frame)
    return math.sqrt(sum((v - m) ** 2 for v in frame) / len(frame)) / 255.0


def _mae(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / (255.0 * len(a))


def _audio_onset(path, seconds, gate_dbfs):
    run = _run(["ffmpeg", "-v", "error", "-i", str(path), "-t", f"{seconds:.3f}", "-vn",
                "-ac", "1", "-ar", str(AUDIO_RATE), "-f", "s16le", "-"])
    raw = run.stdout
    count = len(raw) // 2
    if not count:
        return None
    samples = struct.unpack("<%dh" % count, raw[:count * 2])
    window = int(AUDIO_RATE * AUDIO_WINDOW_S)
    for start in range(0, count - window + 1, window):
        chunk = samples[start:start + window]
        rms = math.sqrt(sum(s * s for s in chunk) / window) / 32768.0
        if rms > 0 and 20 * math.log10(rms) >= gate_dbfs:
            return round(start / AUDIO_RATE, 3)
    return None


def _caption_start(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    times = []
    for h, m, s, frac in re.findall(r"(\d+):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->", text):
        times.append(int(h) * 3600 + int(m) * 60 + int(s) + int(frac.ljust(3, "0")) / 1000)
    for h, m, s, cs in re.findall(r"^Dialogue:[^,]*,(\d+):(\d{2}):(\d{2})\.(\d{2}),", text, re.M):
        times.append(int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100)
    if not times:
        raise ValueError("no SRT/VTT/ASS cue times found in caption file")
    return round(min(times), 3)


def _previews(path, out_dir, stem, rel):
    out_dir.mkdir(parents=True, exist_ok=True)
    strip = out_dir / (stem + "-hook-strip.png")
    clip = out_dir / (stem + "-hook-feed-0-3s.mp4")
    tile = "scale=270:480:force_original_aspect_ratio=decrease,pad=270:480:(ow-iw)/2:(oh-ih)/2:color=black"
    _run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-t", "2.25", "-an",
          "-vf", f"fps=2,{tile},tile=5x1:padding=6:margin=6:color=0x505050", "-frames:v", "1", str(strip)])
    feed = "scale=540:960:force_original_aspect_ratio=decrease,pad=540:960:(ow-iw)/2:(oh-ih)/2:color=black"
    _run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-t", "3", "-vf", feed,
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k",
          "-movflags", "+faststart", str(clip)], 180)
    return {
        "strip": {"file": rel(strip), "sha256": sha256_file(strip),
                  "content": "frames at 0.0/0.5/1.0/1.5/2.0 s inside a 9:16 phone-feed tile"},
        "feed_clip": {"file": rel(clip), "sha256": sha256_file(clip),
                      "content": "first 3 s letterboxed into a 540x960 phone-feed canvas, with sound"},
    }


def measure(video, policy, captions=None, preview_dir=None, report_path=None, host_relation=None):
    if host_relation is not None and host_relation not in HOST_RELATIONS:
        raise ValueError("host_relation must be one of " + "/".join(HOST_RELATIONS))
    video = Path(video)
    base = Path(report_path).resolve().parent if report_path else video.resolve().parent
    def rel(path):
        return Path(os.path.relpath(Path(path).resolve(), base)).as_posix()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required for opening hook measurement")
    duration, vstream, astream = _probe(video)
    deadline = policy["payload_deadline_s"]
    window = min(duration, deadline + 0.05)
    frames = _frames(video, window)
    first = frames[0]
    half = max(2, int(round(0.5 * FRAME_FPS)) + 1)
    early = frames[:half]
    later = frames[half - 1:]
    def mean_motion(seq):
        diffs = [_mae(a, b) for a, b in zip(seq, seq[1:])]
        return round(sum(diffs) / len(diffs), 6) if diffs else None
    m = {
        "first_frame_luma_mean": round(_mean(first), 4),
        "first_frame_luma_std": round(_std(first), 4),
        "luma_mean_at_0_5s": round(_mean(frames[min(len(frames) - 1, half - 1)]), 4),
        "motion_mae_0_to_0_5s": mean_motion(early),
        "motion_mae_0_5s_to_deadline": mean_motion(later),
        "audio_stream": astream is not None,
        "audio_onset_s": _audio_onset(video, window, policy["audio_gate_dbfs"]) if astream else None,
        "first_caption_s": _caption_start(captions) if captions else None,
        "frame_sample": {"fps": FRAME_FPS, "size": [FRAME_W, FRAME_H], "decoded_frames": len(frames)},
    }
    flags = []
    if m["first_frame_luma_mean"] < policy["black_luma_max"]:
        flags.append("black_first_frame")
    elif (m["luma_mean_at_0_5s"] > policy["black_luma_max"] * 2
          and m["first_frame_luma_mean"] < policy["fade_in_ratio"] * m["luma_mean_at_0_5s"]):
        flags.append("fade_in_from_black")
    if m["motion_mae_0_to_0_5s"] is not None and m["motion_mae_0_to_0_5s"] < policy["static_mae_max"]:
        flags.append("low_motion_first_half_second")
    if m["motion_mae_0_5s_to_deadline"] is not None and m["motion_mae_0_5s_to_deadline"] < policy["static_mae_max"]:
        flags.append("low_motion_until_payload_deadline")
    if m["audio_onset_s"] is None or m["audio_onset_s"] > policy["audio_onset_max_s"]:
        flags.append("late_audio_onset")
    if m["first_caption_s"] is not None and m["first_caption_s"] > policy["first_caption_max_s"]:
        flags.append("late_first_caption")
    if m["first_frame_luma_std"] < policy["first_frame_contrast_min"]:
        flags.append("low_contrast_first_frame")
    report = {
        "schema_version": SCHEMA_VERSION,
        "tool": "scripts/opening_hook.py",
        "video": {"file": rel(video), "sha256": sha256_file(video), "duration_s": round(duration, 3),
                  "width": vstream.get("width"), "height": vstream.get("height")},
        "captions": {"file": rel(captions), "sha256": sha256_file(captions)} if captions else None,
        "window_s": [0, round(window, 3)],
        "policy": {k: policy[k] for k in ("payload_deadline_s", "audio_onset_max_s", "first_caption_max_s",
                                          "static_mae_max", "black_luma_max", "fade_in_ratio",
                                          "first_frame_contrast_min", "audio_gate_dbfs")},
        "measurements": m,
        "flags": flags,
        "exceptions": {},
        "previews": _previews(video, Path(preview_dir), video.stem, rel) if preview_dir else None,
        "cold_test": {
            "status": "pending", "reviewer": "", "review_task_id": "", "context": "pending",
            "method": "pending", "actually_watched": False, "actually_heard": False,
            "muted_at_1s": "", "muted_at_2s": "", "sound_at_2s": "", "object_named": "",
            "host_system_seen": "", "part_in_whole_clear": None,
            "tension_or_question": "", "would_stop": None, "swipe_reason_if_any": "",
        },
        "limits": "Technical screen only; the cold test records actual perception. No audience prediction.",
    }
    if host_relation is not None:
        report["host_relation"] = host_relation
    return report


# ---------------------------------------------------------------- evidence validation

def _validate_report(checks, entry, label, policy, expected_sha=None, host_relation=None):
    def need(ok, message):
        return checks.need(ok, "opening hook " + label + ": " + message)
    entry = obj(entry)
    need(entry.get("status") == "pass", "actual measured and cold-tested pass required")
    path = checks.evidence(entry.get("evidence"), "opening hook " + label + " report")
    if not path:
        return
    try:
        report = obj(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, UnicodeError):
        need(False, "unreadable hook report")
        return
    need(type(report.get("schema_version")) is int and report["schema_version"] == SCHEMA_VERSION,
         "hook report schema_version must be integer 1")
    video = obj(report.get("video"))
    media = (path.parent / video["file"]).resolve() if concrete(video.get("file")) else None
    need(media is not None and media.is_file() and media.is_relative_to(checks.root),
         "measured video (path relative to the report) must exist inside the episode")
    if media is not None and media.is_file():
        need(video.get("sha256") == sha256_file(media), "measured video hash stale")
    if expected_sha is not None:
        need(video.get("sha256") == expected_sha, "hook report must measure the current reviewed final video")
    window = report.get("window_s")
    need(isinstance(window, list) and len(window) == 2 and window[0] == 0 and finite(window[1])
         and window[1] >= policy["payload_deadline_s"], "measurement window must start at frame 0 and cover the payload deadline")
    flags = report.get("flags")
    need(isinstance(flags, list) and all(f in FLAGS for f in flags), "known technical flag list required")
    exceptions = obj(report.get("exceptions"))
    for flag in flags if isinstance(flags, list) else []:
        need(concrete(exceptions.get(flag)), "unresolved technical flag " + str(flag) +
             "; repair the opening or record a concrete scientific/commission exception")
    cold = obj(report.get("cold_test"))
    need(cold.get("status") == "pass", "cold two-second test failed/unreviewed")
    need(cold.get("context") == "cold_view", "cold two-second test must be a first view without script/package context")
    need(cold.get("method") in COLD_METHODS, "normal-speed continuous audiovisual cold view required")
    need(cold.get("actually_watched") is True and cold.get("actually_heard") is True,
         "cold test must actually watch and hear the bound file")
    for key in ("reviewer", "muted_at_1s", "muted_at_2s", "sound_at_2s", "object_named", "tension_or_question"):
        need(concrete(cold.get(key)), "cold test " + key + " observation required")
    effective_relation = host_relation if host_relation is not None else report.get("host_relation")
    if effective_relation is not None:
        need(effective_relation in HOST_RELATIONS,
             "hook host_relation must be one of " + "/".join(HOST_RELATIONS))
    if effective_relation == "part_of_host":
        need(concrete(cold.get("host_system_seen")),
             "cold test host_system_seen visual observation required when host_relation=part_of_host")
        need(cold.get("part_in_whole_clear") is True,
             "cold viewer could not visually place the mechanism inside its recognizable host or functional cabin/bay; establish macro host-to-part orientation in the 0-5 s opening")
    need(cold.get("would_stop") is True, "cold viewer would not stop; redesign the first two seconds")


def validate_opening_hook(checks, policy, stage):
    """Required for complete episodes whose record carries qa.opening_hook (new template).

    Chapter and local-sample scopes keep their own scope; they do not need a
    new feed hook unless the commission makes them a complete feed film.
    """
    qa = checks.qa
    if "opening_hook" not in qa:
        return
    data = obj(getattr(checks, "data", {}))
    if obj(data.get("scope")).get("kind", "episode") != "episode":
        return
    record = obj(qa.get("opening_hook"))
    hook_policy = policy["opening_hook"]
    if record.get("status") == "not_applicable":
        checks.need(concrete(record.get("not_applicable_reason")) and concrete(record.get("commission_reference")),
                    "opening hook: not_applicable needs the commission reference and concrete non-feed reason")
        return
    plan_hook = obj(obj(obj(data.get("topic_alignment")).get("opening")).get("hook"))
    host_relation = plan_hook.get("host_relation") if "host_relation" in plan_hook else None
    if stage == "G3":
        _validate_report(checks, record.get("sample"), "sample", hook_policy, host_relation=host_relation)
    else:
        expected = obj(qa.get("reviewed_sha256")).get("video")
        _validate_report(checks, record.get("final"), "final", hook_policy,
                         expected_sha=expected, host_relation=host_relation)
        checks.need(record.get("status") == "pass", "opening hook: final opening hook status must be pass")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("measure", help="measure the first seconds of an actual export")
    m.add_argument("video", type=Path)
    m.add_argument("--captions", type=Path, help="SRT/VTT/ASS caption file used by this export")
    m.add_argument("--preview-dir", type=Path, help="write local phone-feed strip and 0-3 s feed clip here")
    m.add_argument("--host-relation", choices=HOST_RELATIONS,
                   help="standalone subject or part_of_host subsystem requiring macro host-to-part orientation")
    m.add_argument("--report", type=Path, required=True, help="new JSON report path inside the episode directory")
    p = sub.add_parser("plan", help="check topic_alignment.opening.hook in an episode.json")
    p.add_argument("episode", type=Path)
    args = parser.parse_args(argv)
    try:
        policy = load_policy()
        if args.command == "plan":
            data = json.loads(args.episode.read_text(encoding="utf-8"))
            errors = check_hook_plan(obj(obj(data.get("topic_alignment")).get("opening")), policy)
            for error in errors:
                print("ERROR:", error)
            if not errors:
                print("Hook plan structure passed; appeal still needs the cold two-second test on actual media.")
            return 1 if errors else 0
        if args.report.exists():
            raise ValueError("report exists; use a new receipt filename")
        report = measure(args.video, policy, args.captions, args.preview_dir, args.report, args.host_relation)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(args.report), "flags": report["flags"],
                          "measurements": report["measurements"]}, ensure_ascii=False, indent=2))
        return 1 if report["flags"] else 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
