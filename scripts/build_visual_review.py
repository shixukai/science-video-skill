#!/usr/bin/env python3
"""Build static, local review material; never approve an episode or change QA."""
import argparse
from bisect import bisect_left, bisect_right
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import html
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


LIMITS = ("静帧接触表仅供人工检查构图、层级、文字与画面一致性；不能证明动态、"
          "科学内容、声音或整体审美质量。它不是验收结果，不修改 episode 或 QA。")
# A local playlist can still reference remote URLs or files outside the packet.
# Accept self-contained video containers and file transport only, in both tools.
INPUT_OPTIONS = ["-protocol_whitelist", "file", "-format_whitelist",
                 "mov,matroska,avi,mpegts,flv,mpeg,ogg,nut,mxf"]


class ReviewError(ValueError):
    """An actionable input or local-tool failure."""


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def number(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def run_tool(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewError(Path(command[0]).name + " could not finish; no review was published.") from exc
    if result.returncode:
        raise ReviewError(Path(command[0]).name + " failed; no review was published.")
    return result.stdout


def video_geometry(stream, frames):
    """Keep this sampler simple: reject geometry needing display transforms."""
    guidance = (" Export a square-pixel review copy without a rotation/display matrix "
                "from your editing software; the source media was not changed.")
    width, height = stream.get("width"), stream.get("height")
    if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in (width, height)):
        raise ReviewError("The video dimensions are invalid." + guidance)

    def ratio(value):
        try:
            return Fraction(str(value).replace(":", "/"))
        except (ValueError, ZeroDivisionError):
            return None

    sar = stream.get("sample_aspect_ratio")
    if ratio(sar) != 1:
        raise ReviewError("Non-square or unspecified sample aspect ratio is unsupported." + guidance)
    expected_dar = Fraction(width, height)
    if stream.get("display_aspect_ratio") and ratio(stream["display_aspect_ratio"]) != expected_dar:
        raise ReviewError("The display aspect ratio requires a geometry transform." + guidance)
    identity = [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]
    for record in [stream, *frames]:
        if record.get("width", width) != width or record.get("height", height) != height:
            raise ReviewError("Changing video dimensions are unsupported." + guidance)
        if ratio(record.get("sample_aspect_ratio", sar)) != 1:
            raise ReviewError("Non-square frame sample aspect ratio is unsupported." + guidance)
        rotation_tag = record.get("tags", {}).get("rotate", "0")
        if ratio(rotation_tag) != 0:
            raise ReviewError("Video rotation is unsupported." + guidance)
        for side_data in record.get("side_data_list", []):
            if side_data.get("side_data_type") != "Display Matrix":
                continue
            try:
                matrix = [int(value) for line in side_data.get("displaymatrix", "").splitlines()
                          if ":" in line for value in line.split(":", 1)[1].split()]
            except ValueError:
                matrix = []
            if matrix != identity or ratio(side_data.get("rotation", 0)) != 0:
                raise ReviewError("A non-default display matrix or rotation is unsupported." + guidance)
    return {"coded_width": width, "coded_height": height, "display_width": width,
            "display_height": height, "sample_aspect_ratio": "1:1",
            "display_aspect_ratio": f"{expected_dar.numerator}:{expected_dar.denominator}",
            "rotation_degrees": 0, "display_transform": "identity"}


def probe_video(media, ffprobe):
    # Decode the frame timeline once. Selecting real frame indices avoids seeking
    # beyond EOF or inventing timestamps from an average frame rate on VFR media.
    raw = run_tool([
        ffprobe, "-v", "error", "-select_streams", "v:0", "-show_streams", "-show_format",
        "-show_frames", "-show_entries",
        "stream=index,codec_type,width,height,start_time,duration,avg_frame_rate,r_frame_rate,sample_aspect_ratio,display_aspect_ratio:"
        "stream_disposition=attached_pic:stream_tags=rotate:stream_side_data:format=start_time,duration:"
        "frame=best_effort_timestamp_time,duration_time,pkt_duration_time,width,height,sample_aspect_ratio:frame_side_data",
        "-of", "json", *INPUT_OPTIONS, str(media),
    ])
    try:
        data = json.loads(raw)
        stream = data["streams"][0]
        frames = data["frames"]
        if stream.get("disposition", {}).get("attached_pic") or not frames:
            raise ReviewError("The media must contain a timed video stream, not cover art.")
        stream["geometry"] = video_geometry(stream, frames)
        pts = [float(frame["best_effort_timestamp_time"]) for frame in frames]
        container = data.get("format", {})
        origin = float(container.get("start_time", stream.get("start_time", pts[0])))
        times = [value - origin for value in pts]
        if (not all(number(value) and value >= 0 for value in times)
                or any(a >= b for a, b in zip(times, times[1:]))):
            raise ReviewError("Video frame timestamps must be finite, nonnegative and increasing.")
        if "duration" in stream:
            duration = float(stream.get("start_time", pts[0])) - origin + float(stream["duration"])
        else:
            # Frame durations are preferable to a container duration which may
            # include an audio tail beyond the last video frame.
            last = frames[-1]
            frame_duration = last.get("duration_time", last.get("pkt_duration_time"))
            if frame_duration is None:
                raise ReviewError("The video has no usable stream or final-frame duration.")
            duration = times[-1] + float(frame_duration)
        if not number(duration) or duration <= times[-1]:
            raise ReviewError("The video duration must extend beyond its last decoded frame.")
    except (KeyError, IndexError, TypeError, ValueError, OverflowError) as exc:
        if isinstance(exc, ReviewError):
            raise
        raise ReviewError("ffprobe did not return a usable video timeline and duration.") from exc
    return stream, duration, times


def shot_samples(data, duration, times):
    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        raise ReviewError("episode.shots must be a nonempty list with actual shotbook times.")
    result, ids, previous_end = [], set(), 0
    for index, shot in enumerate(shots, 1):
        if not isinstance(shot, dict):
            raise ReviewError("Each shot must be an object.")
        ident, book = shot.get("id"), shot.get("shotbook")
        if not isinstance(ident, str) or not ident.strip() or ident in ids:
            raise ReviewError("Shot IDs must be nonempty, unique strings.")
        ids.add(ident)
        if not isinstance(book, dict):
            raise ReviewError("Each shot needs a shotbook with actual start/end seconds.")
        basis = book.get("timing_basis", {})
        if isinstance(basis, dict) and basis.get("mode") == "relative_plan":
            raise ReviewError("relative_plan cannot be sampled; supply actual video-aligned shot times.")
        start, end = book.get("start"), book.get("end")
        if not number(start) or not number(end) or not 0 <= start < end:
            raise ReviewError("Shot times must be finite, non-boolean seconds with 0 <= start < end; null plans cannot be sampled.")
        if start < previous_end:
            raise ReviewError("Shots overlap or are out of timeline order.")
        if end > duration:
            raise ReviewError("A shot exceeds the actual video duration.")
        previous_end = end
        samples = []
        for position, requested in (("start", start), ("mid", start + (end - start) / 2), ("end", end)):
            # At start/mid show the frame held at that time. End is exclusive:
            # a frame exactly at the next cut belongs to the following shot.
            frame_index = ((bisect_left(times, requested) if position == "end"
                            else bisect_right(times, requested)) - 1)
            if frame_index < 0:
                raise ReviewError("A requested shot time precedes the first decoded video frame.")
            samples.append({"position": position, "requested_seconds": requested,
                            "frame_seconds": times[frame_index], "frame_index": frame_index,
                            "file": f"frames/{index:04d}-{position}.png"})
        result.append({"id": ident, "start": start, "end": end, "samples": samples,
                       "visual_note": str(shot.get("visual_note", "")),
                       "subject": str(book.get("subject", "")), "action": str(book.get("action", ""))})
    return result


def timeline_coverage(shots, duration):
    intervals, gaps, cursor = [], [], 0
    for shot in shots:
        start, end = shot["start"], shot["end"]
        intervals.append([start, end])
        if start > cursor:
            gaps.append([cursor, start])
        cursor = end
    if cursor < duration:
        gaps.append([cursor, duration])
    return {"video_duration_seconds": duration, "listed_intervals": intervals,
            "uncovered_intervals": gaps}


def render_html(title, shots, coverage):
    esc = html.escape
    ranges = lambda values: "、".join(f"{start:.3f}–{end:.3f}s" for start, end in values) or "无"
    sections, overview = [], []
    for index, shot in enumerate(shots, 1):
        middle = shot["samples"][1]
        overview.append(f'<a href="#shot-{index:04d}"><img src="{middle["file"]}" '
                        f'alt="{esc(shot["id"])} mid"><span>{index:02d} · {esc(shot["id"])}<br>'
                        f'{shot["start"]:.3f}–{shot["end"]:.3f}s</span></a>')
        frames = "".join(
            f'<figure><img src="{sample["file"]}" alt="{esc(shot["id"])} {sample["position"]}">'
            f'<figcaption>{sample["position"]} · 请求 {sample["requested_seconds"]:.6f}s'
            f' · 实际帧 {sample["frame_seconds"]:.6f}s</figcaption></figure>'
            for sample in shot["samples"])
        details = " · ".join(esc(shot[key]) for key in ("subject", "action", "visual_note") if shot[key])
        sections.append(f'<section id="shot-{index:04d}"><h2>{index:02d} · {esc(shot["id"])}'
                        f' <small>{shot["start"]:.6f}–{shot["end"]:.6f}s</small></h2>'
                        f'<p>{details}</p><div class="frames">{frames}</div></section>')
    return ("<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\">"
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\' data:; style-src \'unsafe-inline\'">'
            f'<title>{esc(title)} · 静帧审查材料</title><style>'
            'body{margin:0;padding:28px;background:#121416;color:#e9e9e7;font:16px system-ui,sans-serif}'
            'main{max-width:1500px;margin:auto}h1{font-size:26px}h2{font-size:20px}'
            'small,p,figcaption{color:#c0c3c5}small{font-size:14px}section{margin:32px 0}'
            '.overview{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px}'
            '.overview a{color:inherit;text-decoration:none}.overview span{display:block;font-size:12px;'
            'padding-top:6px;overflow-wrap:anywhere}'
            '.frames{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}'
            'figure{margin:0}img{display:block;width:100%;height:auto;background:#000}'
            'figcaption{font-size:12px;margin-top:8px;overflow-wrap:anywhere}'
            'p{line-height:1.6;overflow-wrap:anywhere}@media(max-width:700px){.frames{grid-template-columns:1fr}}'
            f'</style><main><h1>{esc(title)} · 静帧审查材料</h1><p>{esc(LIMITS)}</p>'
            '<p>按镜头原顺序显示 start / mid / end；end 采用结束边界前的实际帧。低帧率或短镜头可能重复同一帧。'
            '完整画幅仅缩放显示，不裁切。请另行连续观看与听验当前视频。</p>'
            f'<p>源视频时长：{coverage["video_duration_seconds"]:.3f}s；'
            f'已列镜头区间：{ranges(coverage["listed_intervals"])}；'
            f'未覆盖区间：{ranges(coverage["uncovered_intervals"])}。区间覆盖不等于已完整审查。</p>'
            '<h2>所列镜头总览</h2><p>每镜复用 mid 帧；点击进入三帧明细。观察所列区间的色彩、构图与密度变化。</p>'
            '<nav class="overview" aria-label="镜头总览">' + "".join(overview) + '</nav>'
            + "".join(sections) + "</main></html>\n")


def build_review(episode, media, output):
    episode = Path(episode).resolve()
    root = episode.parent
    raw = episode.read_bytes()
    packet_hash = hashlib.sha256(raw).hexdigest()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewError("The episode must contain valid UTF-8 JSON.") from exc
    if not isinstance(data, dict):
        raise ReviewError("The episode must be a JSON object.")
    media_arg, output_arg = Path(media), Path(output)
    if media_arg.is_absolute():
        raise ReviewError("--media must be a path relative to the episode directory.")
    media = (root / media_arg).resolve()
    if not media.is_relative_to(root) or not media.is_file():
        raise ReviewError("The source media must be an existing file inside the episode directory.")
    # Relative outputs also use the episode directory, independent of cwd.
    output_arg = output_arg if output_arg.is_absolute() else root / output_arg
    if output_arg.exists() or output_arg.is_symlink():
        raise ReviewError("The output already exists; choose a new directory.")
    output = output_arg.resolve()
    if not output.is_relative_to(root):
        raise ReviewError("The output must remain inside the episode directory.")
    tools = {name: shutil.which(name) for name in ("ffmpeg", "ffprobe")}
    if not all(tools.values()):
        raise ReviewError("ffmpeg and ffprobe are required; no tool is installed automatically.")
    media_hash = sha256(media)
    versions = {name: run_tool([path, "-version"]).splitlines()[0] for name, path in tools.items()}
    stream, duration, times = probe_video(media, tools["ffprobe"])
    shots = shot_samples(data, duration, times)
    coverage = timeline_coverage(shots, duration)
    timeline = [{key: shot[key] for key in ("id", "start", "end")} for shot in shots]
    selected = sorted({sample["frame_index"] for shot in shots for sample in shot["samples"]})
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".visual-review-", dir=output.parent) as temporary:
        staging = Path(temporary)
        raw_frames, final_frames = staging / "extracted", staging / "frames"
        raw_frames.mkdir()
        final_frames.mkdir()
        expression = "+".join(f"eq(n\\,{index})" for index in selected)
        run_tool([tools["ffmpeg"], "-v", "error", "-nostdin", *INPUT_OPTIONS, "-i", str(media), "-map", "0:v:0",
                  "-an", "-sn", "-vf", "select=" + expression, "-fps_mode", "passthrough",
                  "-frames:v", str(len(selected)), "-threads", "1", "-c:v", "png",
                  str(raw_frames / "%08d.png")])
        extracted = sorted(raw_frames.glob("*.png"))
        if len(extracted) != len(selected) or any(path.stat().st_size == 0 for path in extracted):
            raise ReviewError("ffmpeg did not produce every selected frame; no review was published.")
        files, lookup = [], dict(zip(selected, extracted))
        for shot in shots:
            for sample in shot["samples"]:
                destination = staging / sample["file"]
                shutil.copyfile(lookup[sample["frame_index"]], destination)
                sample["sha256"] = sha256(destination)
                files.append({"file": sample["file"], "sha256": sample["sha256"]})
        shutil.rmtree(raw_frames)
        (staging / "index.html").write_text(render_html(str(data.get("title") or "视频"), shots, coverage), encoding="utf-8")
        files.insert(0, {"file": "index.html", "sha256": sha256(staging / "index.html")})
        manifest = {
            "schema_version": 1, "kind": "static_visual_review", "status": "generated_for_review",
            "generated_at": datetime.now(timezone.utc).isoformat(), "limits": LIMITS,
            "episode": {"file": episode.name, "sha256": packet_hash, "path_base": "episode_directory",
                        "hash_scope": "original bytes at generation; later QA edits change this snapshot hash"},
            "timeline_sha256": hashlib.sha256(json_bytes(timeline)).hexdigest(),
            "timeline": timeline, "coverage": coverage,
            "media": {"file": media.relative_to(root).as_posix(), "sha256": media_hash,
                      "path_base": "episode_directory", "duration_seconds": duration,
                      "width": stream["width"], "height": stream["height"],
                      "geometry": stream["geometry"],
                      "frame_rate": stream.get("avg_frame_rate"), "video_stream_index": stream["index"]},
            "tools": versions, "shots": shots, "output_path_base": "review_directory",
            "output_directory": output.relative_to(root).as_posix(), "output_files": files,
        }
        (staging / "manifest.json").write_bytes(json_bytes(manifest))
        evidence = [{"file": (output.relative_to(root) / item["file"]).as_posix(), "sha256": item["sha256"]}
                    for item in [{"file": "manifest.json", "sha256": sha256(staging / "manifest.json")}, *files]]
        (staging / "gate-evidence.json").write_bytes(json_bytes(evidence))
        if sha256(episode) != packet_hash or sha256(media) != media_hash:
            raise ReviewError("Episode or media changed during extraction; rerun against stable inputs.")
        if output.exists() or output.is_symlink():
            raise ReviewError("The output appeared during extraction; it was not overwritten.")
        os.rename(staging, output)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--media", type=Path, required=True, help="video path relative to the episode directory")
    parser.add_argument("--output", type=Path, required=True,
                        help="NEW directory inside the episode directory; relative paths use that directory")
    args = parser.parse_args(argv)
    try:
        manifest = build_review(args.episode, args.media, args.output)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({"status": manifest["status"], "output": manifest["output_directory"],
                      "review": "pending"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
