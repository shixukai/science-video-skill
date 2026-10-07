#!/usr/bin/env python3
"""Read-only checks of a local production packet; never a legal/visual approval."""
import argparse
from datetime import date
import hashlib
import json
import math
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


def file_sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def shotbook_sha256(data):
    """Bind semantic timing and selected visuals to the declared audio revision."""
    narration = data.get("narration")
    narration = narration if isinstance(narration, dict) else {}
    payload = {"audio_sha256": narration.get("audio_sha256"),
               "shots": data.get("shots"), "assets": data.get("assets")}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def topic_review_sha256(data):
    """Version binding only; neither semantic review nor user authorization."""
    qa = data.get("qa") if isinstance(data.get("qa"), dict) else {}
    return canonical_sha256({"topic": data.get("topic"), "scope": data.get("scope"),
        "alignment": data.get("topic_alignment"), "shots": data.get("shots"),
        "narration": data.get("narration"), "assets": data.get("assets"),
        "deliverables": data.get("deliverables"), "media_hashes": qa.get("reviewed_sha256")})


def check_topic(data, root, stage, shots):
    errors = []
    def need(ok, message):
        if not ok:
            errors.append("topic: " + message)
        return bool(ok)
    def text(value):
        return isinstance(value, str) and bool(value.strip())
    def obj(value):
        return value if isinstance(value, dict) else {}
    def anchor_fields(value, label):
        value = obj(value)
        for key in ("version", "title", "question", "intent"):
            need(text(value.get(key)), f"{label}.{key} required")
        scope = value.get("required_scope")
        result = {}
        if need(isinstance(scope, list) and bool(scope), f"{label}.required_scope required"):
            for item in scope:
                item = obj(item)
                ident = item.get("id")
                if need(text(ident) and ident not in result and text(item.get("answer_requirement")), f"{label}: scope id/answer requirement missing or duplicate"):
                    result[ident] = item
        return result
    topic = obj(data.get("topic"))
    need(text(topic.get("origin_reference")), "original request reference required")
    path = topic.get("anchor_file")
    anchor = {}
    if need(text(path), "frozen anchor_file required"):
        target = (root / path).resolve()
        if need(not Path(path).is_absolute() and target.is_relative_to(root), "anchor path must stay inside episode directory"):
            if need(target.is_file(), "frozen anchor file missing"):
                try:
                    anchor = json.loads(target.read_text(encoding="utf-8"))
                except (OSError, ValueError) as exc:
                    need(False, f"unreadable anchor: {exc}")
    anchor_fields(anchor, "original")
    original_hash = canonical_sha256(anchor)
    need(topic.get("anchor_sha256") == original_hash, "original anchor hash mismatch")
    current = obj(topic.get("current"))
    required = anchor_fields(current, "current")
    current_hash = canonical_sha256(current)
    need(topic.get("current_sha256") == current_hash, "current topic hash mismatch")
    if current_hash != original_hash:
        change = obj(topic.get("change_approval"))
        need(change.get("status") == "explicit_user_request" and text(change.get("request_reference"))
             and change.get("from_sha256") == original_hash and change.get("to_sha256") == current_hash,
             "topic/scope change requires a referenced explicit user request bound to both versions")
    scope = obj(data.get("scope"))
    kind = scope.get("kind")
    need(kind in ("episode", "local_sample", "chapter"), "scope.kind must distinguish episode/local_sample/chapter")
    if kind in ("local_sample", "chapter"):
        for key in ("parent_episode_id", "chapter_id", "purpose", "delivery_context"):
            need(text(scope.get(key)), f"local scope.{key} required")
        need(scope.get("placement") == "chapter_only", "local work cannot substitute for episode opening")
        need(scope.get("publication_ready") is False, "local work cannot be marked publication ready")
        need(stage != "delivery", "local sample/chapter cannot pass complete-episode delivery")
    alignment = obj(data.get("topic_alignment"))
    need(alignment.get("topic_sha256") == current_hash, "alignment bound to wrong topic version")
    for section, fields in (("opening", ("title", "voiceover")), ("ending", ("answer",))):
        record = obj(alignment.get(section))
        for field in fields:
            need(text(record.get(field)), f"{section}.{field} required")
        need(record.get("intent") == current.get("intent"), f"{section} question type differs from anchored intent")
        refs = record.get("scope_ids")
        valid = isinstance(refs, list) and bool(refs) and all(isinstance(x, str) and x in required for x in refs)
        need(valid, f"{section}: valid required-scope mapping required")
        if kind == "episode" and valid:
            need(set(refs) == set(required), f"{section}: incomplete episode answer scope")
        ids = record.get("shot_ids")
        need(isinstance(ids, list) and bool(ids) and all(isinstance(x, str) and x in shots for x in ids), f"{section}: existing shot_ids required")
        if shots and isinstance(ids, list):
            boundary = next(iter(shots)) if section == "opening" else next(reversed(shots))
            need(boundary in ids, f"{section}: mapping must include actual boundary shot")
    coverage = alignment.get("coverage")
    covered = set()
    if need(isinstance(coverage, list) and bool(coverage), "coverage mapping required"):
        for record in coverage:
            record = obj(record)
            ident = record.get("scope_id")
            valid = isinstance(ident, str) and ident in required and ident not in covered
            if need(valid, "unknown/duplicate coverage scope_id"):
                covered.add(ident)
            ids = record.get("shot_ids")
            need(isinstance(ids, list) and bool(ids) and all(isinstance(x, str) and x in shots for x in ids), "coverage must reference existing shots")
            need(text(record.get("answer_evidence")), "coverage answer evidence required")
    if kind == "episode":
        need(alignment.get("omitted_scope_ids") == [], "complete episode must declare no omitted scope")
        need(covered == set(required), "necessary answer scope missing from episode coverage")
    else:
        omitted = alignment.get("omitted_scope_ids")
        need(isinstance(omitted, list) and all(isinstance(x, str) for x in omitted) and set(omitted) == set(required) - covered,
             "local work must identify omitted episode scope")
    if stage == "delivery":
        review = obj(obj(data.get("qa")).get("topic_alignment"))
        need(review.get("status") == "pass" and review.get("reviewer_role") in ("editor", "independent"), "actual editorial/independent topic review required")
        need(review.get("reviewed_sha256") == topic_review_sha256(data), "stale topic/media review context")
        for key in ("opening_title", "opening_voiceover", "coverage", "ending"):
            check = obj(review.get(key))
            need(check.get("status") == "pass" and text(check.get("note")) and text(check.get("evidence")), f"{key} recheck failed/missing evidence")
    return errors


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
            asset_file = local_file(asset.get("file"), ident)
            if asset_file:
                require(asset.get("sha256") == file_sha256(asset_file), f"{ident}: stale/missing asset sha256; review selected material again")
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
    # Shotbook declarations constrain the packet; they never prove visual quality.
    def seconds(value):
        try:
            return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0
        except OverflowError:
            return False

    last_end = 0
    for ident, shot in shots.items():
        book = shot.get("shotbook")
        if book is None and stage == "plan":
            notes.append(f"{ident}: shotbook pending; complete after final voiceover and visual selection")
            continue
        if not require(isinstance(book, dict), f"{ident}: shotbook required"):
            continue
        start, end = book.get("start"), book.get("end")
        timed = seconds(start) and seconds(end) and start < end
        require(timed, f"{ident}: shotbook needs finite start < end seconds")
        if timed:
            require(start >= last_end, f"{ident}: shotbook shots overlap or are out of order")
            last_end = end
        for key in ("subject", "action", "framing", "claim_support", "motion_purpose"):
            require(nonempty(book.get(key)), f"{ident}: shotbook.{key} required")
        beats = book.get("beats")
        if require(isinstance(beats, list), f"{ident}: semantic beats must be a list"):
            if not beats:
                require(nonempty(book.get("silence_reason")), f"{ident}: silent observation needs silence_reason")
            previous = start if timed else 0
            for beat in beats:
                if not require(isinstance(beat, dict), f"{ident}: beat must be an object"):
                    continue
                at = beat.get("at")
                if require(seconds(at), f"{ident}: beat.at must be finite seconds"):
                    require(timed and start <= at < end and at >= previous, f"{ident}: beat outside shot or out of order")
                    previous = at
                for key in ("trigger_words", "attention_subject", "action"):
                    require(nonempty(beat.get(key)), f"{ident}: beat.{key} required")
        candidates = book.get("candidates")
        chosen = []
        if require(isinstance(candidates, list) and bool(candidates), f"{ident}: viewed candidates required"):
            for candidate in candidates:
                if not require(isinstance(candidate, dict), f"{ident}: candidate must be an object"):
                    continue
                for key in ("source", "viewing_note", "decision_reason"):
                    require(nonempty(candidate.get(key)), f"{ident}: candidate.{key} required")
                selected = candidate.get("selected")
                require(isinstance(selected, bool), f"{ident}: candidate.selected must be boolean")
                if selected is True:
                    chosen.append(candidate)
                    require(isinstance(shot.get("asset_ids"), list) and candidate.get("asset_id") in shot["asset_ids"], f"{ident}: chosen candidate must use a shot asset")
                    interval = candidate.get("source_interval")
                    require(nonempty(interval), f"{ident}: chosen candidate source_interval required (still/full or actual in-out)")
            require(len(chosen) == 1, f"{ident}: exactly one selected primary candidate required")
            if len(candidates) < 2:
                require(nonempty(book.get("alternatives_note")), f"{ident}: explain unavailable alternatives")
        if stage == "delivery":
            keyframe = book.get("keyframe_review", {})
            if not isinstance(keyframe, dict):
                keyframe = {}
            require(keyframe.get("status") == "pass" and nonempty(keyframe.get("note")), f"{ident}: finished keyframe review required before animation")
            frame = local_file(keyframe.get("file"), f"{ident} keyframe")
            if frame:
                require(keyframe.get("sha256") == file_sha256(frame), f"{ident}: stale keyframe review hash")
    if stage == "delivery":
        audio = assets.get(narration_id) if isinstance(narration_id, str) else None
        audio_file = local_file(audio.get("file"), "shotbook narration") if audio else None
        if audio_file:
            require(narration.get("audio_sha256") == file_sha256(audio_file), "shotbook: audio changed or unbound; realign beats and review")
        qa_book = data.get("qa", {}).get("shotbook", {}) if isinstance(data.get("qa"), dict) else {}
        if not isinstance(qa_book, dict):
            qa_book = {}
        require(qa_book.get("status") == "pass" and nonempty(qa_book.get("note")), "qa.shotbook: actual representative audiovisual review required")
        require(qa_book.get("reviewed_sha256") == shotbook_sha256(data), "qa.shotbook: stale audio/shotbook context; review again")
    errors.extend(check_topic(data, root, stage, shots))
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
                duration = float(media.get("format", {}).get("duration", 0))
                require(math.isfinite(duration) and duration > 0, "video: duration missing/invalid")
                for shot_id, shot in shots.items():
                    book = shot.get("shotbook")
                    if isinstance(book, dict) and seconds(book.get("end")):
                        require(book["end"] <= duration, f"{shot_id}: shotbook exceeds actual video duration")
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
