#!/usr/bin/env python3
"""Read-only checks of a local production packet; never a legal/visual approval."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlparse


REVIEW_KEYS = ("science", "rights", "visual_frames", "mobile_preview", "audio", "narration", "covers")
KINDS = {"real_capture", "real_observation", "screen_recording", "simulation", "ai_generated", "graphic", "audio", "font"}
OUTPUTS = ("video", "cover_3_4", "cover_4_3")


def platform_metadata_sha256(data, preview):
    """Bind a declared preview to its text/destination; this does not perform a review."""
    context = {key: data.get(key) for key in ("title", "description", "tags")}
    context.update({key: preview.get(key) for key in ("platform", "account", "surface")})
    payload = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def check(data, root, stage):
    errors, notes = [], []

    def require(ok, message):
        if not ok:
            errors.append(message)
        return bool(ok)

    def nonempty(value):
        return isinstance(value, str) and bool(value.strip())

    def records(key):
        values = data.get(key)
        if not require(isinstance(values, list) and bool(values), f"{key}: expected a nonempty list"):
            return {}
        result = {}
        for index, item in enumerate(values):
            if not require(isinstance(item, dict), f"{key}[{index}]: expected an object"):
                continue
            ident = item.get("id")
            if require(nonempty(ident) and ident not in result, f"{key}[{index}]: missing or duplicate id"):
                result[ident] = item
        return result

    def local_file(value, label):
        if not require(nonempty(value), f"{label}: file path is missing"):
            return None
        path = Path(value)
        target = (root / path).resolve()
        if not require(not path.is_absolute() and target.is_relative_to(root), f"{label}: path must stay inside the episode directory"):
            return None
        return target if require(target.is_file(), f"{label}: file not found: {value}") else None

    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(nonempty(data.get("episode_id")), "episode_id is missing")
    title = data.get("title", "")
    description = data.get("description", "")
    tags = data.get("tags", [])
    require(nonempty(title) and len(title) <= 30, "title: expected 1–30 Unicode code points")
    require(isinstance(description, str), "description must be a string")
    valid_tags = isinstance(tags, list) and all(nonempty(t) for t in tags)
    require(valid_tags, "tags must be a list of nonempty strings (or [])")
    if isinstance(description, str) and valid_tags:
        caption = description + ("\n" if tags else "") + " ".join(tags)
        require(len(caption) <= 1000, "description + tags exceeds 1000 Unicode code points")
        if isinstance(title, str):
            require(not any(mark in title + caption for mark in ("@", "＠")), "title/caption: @ mentions are not allowed")
    sources, claims, assets, shots = (records(k) for k in ("sources", "claims", "assets", "shots"))
    for ident, source in sources.items():
        url = source.get("url", "")
        parsed = urlparse(url) if isinstance(url, str) else None
        require(parsed is not None and parsed.scheme in ("https", "http") and bool(parsed.netloc), f"{ident}: valid source URL required")
        checked_on = source.get("accessed_on", "")
        try:
            valid_date = isinstance(checked_on, str) and date.fromisoformat(checked_on).isoformat() == checked_on
        except ValueError:
            valid_date = False
        require(valid_date and nonempty(source.get("note")), f"{ident}: source check date (YYYY-MM-DD) and note required")
    for ident, claim in claims.items():
        require(nonempty(claim.get("text")), f"{ident}: claim text required")
        refs = claim.get("source_ids")
        require(isinstance(refs, list) and bool(refs) and all(isinstance(r, str) and r in sources for r in refs), f"{ident}: unknown or missing source_ids")
    for ident, asset in assets.items():
        require(asset.get("kind") in KINDS, f"{ident}: unknown asset kind")
        require(nonempty(asset.get("source")) and nonempty(asset.get("creator")), f"{ident}: source and creator required")
        rights = asset.get("rights", {})
        if not isinstance(rights, dict):
            require(False, f"{ident}: rights must be an object")
            rights = {}
        require(rights.get("status") in ("pending", "cleared", "denied"), f"{ident}: rights status must be pending/cleared/denied")
        if asset.get("kind") in ("simulation", "ai_generated"):
            require(nonempty(asset.get("disclosure")), f"{ident}: simulation/AI disclosure required")
        if stage == "delivery":
            require(rights.get("status") == "cleared", f"{ident}: rights not cleared")
            require(all(nonempty(rights.get(k)) for k in ("evidence", "scope")), f"{ident}: actual rights evidence and allowed scope required")
            local_file(asset.get("file"), ident)
        else:
            if rights.get("status") != "cleared":
                notes.append(f"{ident}: {rights.get('status')} rights; not usable as a finished asset")
            value = asset.get("file")
            acquired = False
            if nonempty(value):
                path = Path(value)
                target = (root / path).resolve()
                if require(not path.is_absolute() and target.is_relative_to(root), f"{ident}: path must stay inside the episode directory"):
                    acquired = target.is_file()
            if not acquired:
                notes.append(f"{ident}: media not acquired locally; rights status does not establish asset availability")
    for ident, shot in shots.items():
        for key, lookup in (("asset_ids", assets), ("claim_ids", claims)):
            refs = shot.get(key)
            require(isinstance(refs, list) and all(isinstance(r, str) and r in lookup for r in refs), f"{ident}: invalid {key}")
        require(bool(shot.get("asset_ids")), f"{ident}: asset_ids required")
        require(nonempty(shot.get("visual_note")), f"{ident}: visual_note required")
    narration = data.get("narration", {})
    if not isinstance(narration, dict):
        require(False, "narration must be an object")
        narration = {}
    language = narration.get("language")
    require(isinstance(language, str) and language.lower().split("-")[0] == "zh", "narration: Chinese language (zh or zh-*) required")
    require(narration.get("status") in ("pending", "ready"), "narration: status must be pending/ready")
    voice_type = narration.get("voice_type")
    require(voice_type in ("pending", "human", "synthetic"), "narration: voice_type must be pending/human/synthetic")
    narration_id = narration.get("asset_id")
    if nonempty(narration_id):
        require(narration_id in assets and assets[narration_id].get("kind") == "audio", "narration: asset_id must reference an audio asset")
    if voice_type == "synthetic":
        require(nonempty(narration.get("disclosure")), "narration: synthetic voice disclosure required")
    if stage == "delivery":
        require(narration.get("status") == "ready" and voice_type in ("human", "synthetic"), "narration: ready Chinese voiceover required; captions/music alone are incomplete")
        require(nonempty(narration_id), "narration: recorded voiceover asset_id required")
        require(nonempty(narration.get("series_sample_reference")), "narration: first shared series voice sample reference required")
    elif narration.get("status") != "ready":
        notes.append("narration: pending Chinese voiceover; captions/music alone are not a completed episode")
    if stage == "plan":
        notes.append("PLAN ONLY: no footage, rights, decoding, scientific accuracy or visual/mobile approval is established")
        return errors, notes

    require(nonempty(data.get("production_statement")), "actual production_statement required")
    deliverables = data.get("deliverables", {})
    qa = data.get("qa", {})
    if not isinstance(deliverables, dict):
        require(False, "deliverables must be an object")
        deliverables = {}
    if not isinstance(qa, dict):
        require(False, "qa must be an object")
        qa = {}
    for key in REVIEW_KEYS:
        record = qa.get(key, {})
        require(isinstance(record, dict) and record.get("status") == "pass" and nonempty(record.get("note")), f"qa.{key}: actual pass and specific review note required")
    comprehension = qa.get("comprehension", {})
    if not isinstance(comprehension, dict):
        comprehension = {}
    comprehension_status = comprehension.get("status")
    require(comprehension_status in ("editor_reviewed", "audience_checked") and nonempty(comprehension.get("note")), "qa.comprehension: editor_reviewed or audience_checked with a specific note required; pending/fail cannot pass delivery")
    if comprehension_status == "audience_checked":
        require(nonempty(comprehension.get("audience_feedback_reference")), "qa.comprehension: actual audience feedback reference required")
    elif comprehension_status == "editor_reviewed":
        notes.append("Comprehension: editorial review only; actual audience understanding remains unverified")
    narration_review = qa.get("narration", {})
    require(isinstance(narration_review, dict) and narration_review.get("review_scope") == "final_export", "qa.narration: final_export listening scope required; short-sample approval does not approve a full episode")
    preview = qa.get("mobile_preview", {})
    if not isinstance(preview, dict):
        preview = {}
    require(preview.get("review_scope") == "target_platform", "qa.mobile_preview: actual target_platform review required")
    require(preview.get("surface") in ("actual_device", "desktop_platform_preview"), "qa.mobile_preview: surface must distinguish actual_device from desktop_platform_preview; bare players/proxies are insufficient")
    require(nonempty(preview.get("platform")) and nonempty(preview.get("account")), "qa.mobile_preview: actual platform and account required")
    preview_hash = platform_metadata_sha256(data, preview)
    require(preview.get("reviewed_metadata_sha256") == preview_hash, f"qa.mobile_preview: missing/stale preview context hash; current hash {preview_hash}")
    reviewed = qa.get("reviewed_sha256", {})
    if not isinstance(reviewed, dict):
        require(False, "qa.reviewed_sha256 must be an object")
        reviewed = {}
    probe, decoder = shutil.which("ffprobe"), shutil.which("ffmpeg")
    require(bool(probe), "ffprobe unavailable: dimensions/streams cannot be verified")
    require(bool(decoder), "ffmpeg unavailable: full decoding cannot be verified")
    for key in OUTPUTS:
        target = local_file(deliverables.get(key), key)
        if target is None:
            continue
        with target.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        require(reviewed.get(key) == digest, f"{key}: reviewed_sha256 missing/stale; current hash {digest}")
        if not probe:
            continue
        try:
            raw = subprocess.run([probe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(target)], capture_output=True, text=True, timeout=60)
            if raw.returncode:
                require(False, f"{key}: ffprobe failed: {raw.stderr.strip()[:400]}")
                continue
            media = json.loads(raw.stdout)
            streams = media.get("streams", [])
            videos = [s for s in streams if s.get("codec_type") == "video"]
            if not require(bool(videos), f"{key}: no visual stream"):
                continue
            width, height = videos[0].get("width", 0), videos[0].get("height", 0)
            require(width > 0 and height > 0, f"{key}: invalid pixel dimensions")
            require(videos[0].get("sample_aspect_ratio", "1:1") in ("1:1", "N/A", "0:1"), f"{key}: normalize non-square pixels before checking layout")
            rotations = [s.get("rotation", 0) for s in videos[0].get("side_data_list", [])]
            rotations.append(videos[0].get("tags", {}).get("rotate", 0))
            require(all(float(r) % 360 == 0 for r in rotations), f"{key}: normalize rotation metadata before checking layout")
            notes.append(f"{key}: {width}x{height}")
            if key == "cover_3_4":
                require(width * 4 == height * 3, "cover_3_4: incorrect aspect ratio")
            elif key == "cover_4_3":
                require(width * 3 == height * 4, "cover_4_3: incorrect aspect ratio")
            else:
                require(any(s.get("codec_type") == "audio" for s in streams), "video: audio stream missing")
                require(float(media.get("format", {}).get("duration", 0)) > 0, "video: duration missing/invalid")
                if width >= height:
                    notes.append("video: landscape/square; manually confirm the intended destination")
            if decoder:
                decoded = subprocess.run([decoder, "-hide_banner", "-v", "error", "-xerror", "-nostdin", "-i", str(target), "-map", "0:v", "-map", "0:a?", "-f", "null", "-"], capture_output=True, text=True, timeout=600)
                require(decoded.returncode == 0 and not decoded.stderr.strip(), f"{key}: decode failure: {decoded.stderr.strip()[:400]}")
        except (OSError, subprocess.TimeoutExpired, ValueError, TypeError) as exc:
            require(False, f"{key}: unable to verify: {exc}")
    notes.append("Local checks cannot verify legal rights, scientific truth, optical centering, mobile readability or publication")
    notes.append("An audio stream or approved short sample does not prove full-episode quality; actual listening must verify naturalness, pronunciation, pacing, voice consistency, subtitle sync and the mix")
    notes.append("QA fields and preview hashes are declarations/context checks, not proof of real viewing, audience understanding, visual quality or platform fit")
    return errors, notes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--stage", choices=("plan", "delivery"), required=True)
    args = parser.parse_args()
    try:
        data = json.loads(args.episode.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("episode JSON must be an object")
        errors, notes = check(data, args.episode.resolve().parent, args.stage)
    except (OSError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for note in notes:
        print(f"NOTE: {note}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"{args.stage.upper()}: {'BLOCKED' if errors else 'LOCAL CHECKS PASS'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
