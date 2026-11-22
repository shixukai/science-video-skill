#!/usr/bin/env python3
"""Offline structural checks; never art, rights, media or publication approval."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET

OWNER_IDS = {"topic", "science-rights", "ai-generated-video", "google-flow", "production", "visual", "voice", "shotbook", "quality", "realism", "engineering", "tools", "render-evidence"}
HEX = re.compile(r"#[0-9A-Fa-f]{6}$")
PRIVATE_ID = re.compile(r"(?:libfile_|Sentinel_)[0-9a-f]{20,}|file_[0-9a-f]{24,}")


def local_path(root, base, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("relative local path required")
    p = (base / relative).resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError("path escapes Skill")
    return p


def slug(text):
    return "".join(c for c in text.lower()
                   if not unicodedata.category(c).startswith("P") or c in "_-").replace(" ", "-")


def caption_baselines(profile, width, height):
    """Read absolute targets for this revision, never apply the increment again."""
    c = profile["captions"]
    w, h = c["canvas"]
    if width <= 0 or height <= 0 or width * h != height * w:
        raise ValueError("new aspect ratio needs layout review")
    return {name: round(record["target"] * height / h)
            for name, record in c["baselines"].items()}


def check_operations(operations):
    """Current project targets and accounting declarations, not measured output."""
    errors = []
    if not isinstance(operations, dict):
        return ["operations must be an object"]
    for key in ("daily_completed_unique_target", "daily_actual_unique_target"):
        if type(operations.get(key)) is not int or operations[key] != 10:
            errors.append("current series " + key + " must be 10")
    counting = operations.get("daily_counting", {})
    if not isinstance(counting, dict):
        return errors + ["daily_counting must be an object"]
    if counting.get("counters_independent") is not True:
        errors.append("completion and actual publication must be counted separately")
    if counting.get("completion_basis") != "unique_full_episode_completed_and_G5_passed_today":
        errors.append("completion counter must require a newly completed quality-passed full episode")
    if counting.get("publication_basis") != "unique_first_publication_with_verified_G7_readback_today":
        errors.append("publication counter must require a new unique verified publication")
    excluded = counting.get("excluded_credits")
    required = {"failed", "sample", "draft", "rendering", "old_video", "duplicate", "previous_day_completion", "previously_published_reupload"}
    if not isinstance(excluded, list) or not all(isinstance(v, str) for v in excluded) or not required <= set(excluded):
        errors.append("daily counters must exclude failed, sample, draft, rendering, duplicate and old-video credits")
    if counting.get("new_work_eligibility") != "current_new_work_scope_with_source_and_version_evidence":
        errors.append("new-work eligibility requires source and version evidence")
    if counting.get("unpublished_inventory") != "not_automatically_eligible; determine new-work scope from source/version evidence":
        errors.append("old/unpublished inventory cannot automatically satisfy the new-work target")
    if operations.get("no_schedule_change_from_adoption") is not True:
        errors.append("profile target changes do not create or change a schedule")
    spacing = operations.get("publication_spacing")
    if (not isinstance(spacing, dict)
            or type(spacing.get("recommended_min_gap_hours")) not in (int, float)
            or spacing["recommended_min_gap_hours"] < 1
            or spacing.get("avoid_burst_posting") is not True
            or not str(spacing.get("scope", "")).strip()):
        errors.append("publication spacing guidance requires a positive gap and explicit non-scheduling scope")
    collections_cfg = operations.get("douyin_collections")
    if (not isinstance(collections_cfg, dict)
            or collections_cfg.get("enabled") is not True
            or collections_cfg.get("owner") != "references/production-checkpoints.md#assign-every-public-video-to-its-matching-douyin-collection"
            or collections_cfg.get("require_collection_at_publication") is not True
            or collections_cfg.get("no_ad_hoc_collections_without_authorization") is not True
            or collections_cfg.get("exclude_private_or_personal_videos") is not True
            or collections_cfg.get("episode_ordering") != "newest_first"
            or not str(collections_cfg.get("classification_priority", "")).strip()
            or not str(collections_cfg.get("scope", "")).strip()):
        errors.append("douyin_collections standing taxonomy and publication assignment rules required")
    else:
        rows = collections_cfg.get("collections")
        order = collections_cfg.get("profile_display_order")
        expected_titles = ["透视日常造物", "解码巅峰工程", "丈量天地寰宇", "探秘生命法则"]
        if (not isinstance(rows, list) or len(rows) != 4
                or not all(isinstance(r, dict)
                           and bool(str(r.get("id", "")).strip())
                           and bool(str(r.get("title", "")).strip())
                           and bool(str(r.get("description", "")).strip())
                           and bool(str(r.get("scope", "")).strip())
                           and r.get("cover_ratio") == "1:1"
                           and r.get("display_order") == idx
                           for idx, r in enumerate(rows, start=1))
                or [r["title"] for r in rows] != expected_titles
                or order != [r["id"] for r in rows]):
            errors.append("douyin_collections must define the four ordered standing collections with scopes and 1:1 covers")
    return errors


def check_platform_record_formats(ledger):
    """Check blank research templates, not live platform evidence or performance."""
    if not isinstance(ledger, dict) or not isinstance(ledger.get("record_formats"), dict):
        return ["platform research record formats required"]
    errors = []
    formats = ledger["record_formats"]
    required = {
        "platform_snapshot": {"collected_at", "denominators", "hours_since_publication", "duration_s", "traffic_and_audience", "source_url", "page_filters", "window_note", "data_updated_display", "update_status", "published_display", "publication_timezone", "age_basis", "sample_note", "field_definitions", "raw_display_values", "field_states", "inconsistency_note", "evidence"},
        "platform_research": {"collected_at", "snapshot_references", "availability_note", "candidate_hypotheses", "ai_suggestions", "activity_constraints", "next_check", "commissioned_series", "coverage", "cohort_basis", "diagnosis_limits", "next_production_brief"},
        "experiment": {"hypothesis", "primary_variable", "baseline_version", "candidate_version", "comparison_window", "metrics_to_check", "traffic_and_sample_limits", "observation_status", "result", "limits", "production_action", "responsible_role", "review_segment"},
        "retention_review": {"first_verified_payoff_s", "payoff_evidence"},
    }
    for name, keys in required.items():
        record = formats.get(name)
        if not isinstance(record, dict) or not keys <= record.keys():
            errors.append("platform research " + name + " traceability fields required")
    snapshot = formats.get("platform_snapshot", {})
    if isinstance(snapshot, dict):
        if (snapshot.get("update_status") != "unknown" or snapshot.get("hours_since_publication") is not None
                or snapshot.get("duration_s") is not None):
            errors.append("blank platform snapshot must not invent freshness or work age")
        for name in ("raw_display_values", "field_states", "field_definitions", "field_names_as_platform_shows", "denominators", "traffic_and_audience"):
            if snapshot.get(name) != {}:
                errors.append("blank platform snapshot must not invent observed fields")
    if ledger.get("platform_snapshots") != []:
        errors.append("blank platform snapshots must not invent observations")
    experiment = formats.get("experiment", {})
    if isinstance(experiment, dict) and (experiment.get("observation_status") != "not_measured" or experiment.get("result") != ""):
        errors.append("blank experiment must preserve unmeasured status and empty result")
    research = formats.get("platform_research", {})
    if isinstance(research, dict):
        if research.get("coverage") != {} or any(research.get(key) != "" for key in
                ("commissioned_series", "cohort_basis", "diagnosis_limits", "next_production_brief")):
            errors.append("blank research must not invent coverage, diagnosis or next-production findings")
    retention = formats.get("retention_review", {})
    if isinstance(retention, dict) and (retention.get("first_verified_payoff_s") is not None
            or retention.get("payoff_evidence") != []):
        errors.append("blank retention review must not invent a verified media payoff")
    if isinstance(experiment, dict) and any(experiment.get(key) != "" for key in
            ("production_action", "responsible_role", "review_segment")):
        errors.append("blank experiment must not invent an implemented production change")
    if ledger.get("platform_research") != []:
        errors.append("blank platform research must not invent research findings")
    return errors


def check(root):
    root = Path(root).resolve()
    errors = []
    def need(ok, message):
        if not ok:
            errors.append(message)
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    try:
        owners = read("indexes/rule-owners.json")["owners"]
        need({o["id"] for o in owners} == OWNER_IDS and len(owners) == len(OWNER_IDS), "complete responsibility owners required")
        assigned = []
        owner_files = []
        for o in owners:
            p = local_path(root, root, o["file"])
            need(p.is_file() and p.suffix == ".md", "owner file missing")
            owner_files.append(str(p))
            need(bool(o["owns"]), "owner has no responsibility")
            assigned += o["owns"]
        need(len(owner_files) == len(set(owner_files)), "duplicate owner file")
        need(len(assigned) == len(set(assigned)), "responsibility has multiple owners")

        errors.extend(check_platform_record_formats(read("assets/project-ledger-template.json")))
        profile = read("config/series-profile.json")
        need(profile["schema_version"] == 1 and bool(re.fullmatch(r"\d+\.\d+\.\d+", str(profile.get("version", "")))), "unsupported profile schema/version")
        positioning = profile.get("editorial_positioning")
        mix = positioning.get("content_mix_guidance") if isinstance(positioning, dict) else None
        need(isinstance(positioning, dict)
             and bool(str(positioning.get("id", "")).strip())
             and positioning.get("preserves_user_commissioned_topics") is True
             and isinstance(mix, dict)
             and all(isinstance(mix.get(k), dict) and bool(str(mix[k].get("id", "")).strip()) and bool(str(mix[k].get("focus", "")).strip())
                     for k in ("primary_pillar", "secondary_pillar"))
             and isinstance(mix.get("deprioritized_editorial_defaults"), list)
             and all(isinstance(item, str) and item.strip() for item in mix["deprioritized_editorial_defaults"]),
             "editorial positioning must define primary/secondary pillars and preserve user-commissioned topics")
        errors.extend(check_operations(profile.get("operations")))
        need(profile["medium"]["mechanism"] == "realistic_main_with_scoped_explanation", "current series requires realistic main footage with scoped explanation")
        need(profile["medium"]["real_anchor"] == "verified_authorized_user_capture_only", "real video anchor must be verified authorized user capture only")
        voice = profile["audio"]
        need(voice.get("speaker") == "user_clone"
             and voice.get("language") == "Chinese"
             and voice.get("voice_preset_id") == "mandarin-indextts25-clone-polished-v1",
             "current voice configuration changed")
        need(voice.get("backend") == "local_indextts2" and voice.get("provider") == "IndexTTS"
             and voice.get("model_id") == "IndexTeam/IndexTTS-2.5"
             and (root / "scripts/synthesize_indextts2.py").is_file(),
             "default IndexTTS-2.5 voice clone backend required; local project and optional Qwen execution locations must be confirmed at invocation")
        indextts2 = voice.get("indextts2", {})
        forbidden_private_keys = {"project_dir", "python_executable", "checkpoints_dir", "cfg_path", "reference_prompt", "reference_prompt_file"}
        def _has_private_path(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k in forbidden_private_keys or _has_private_path(v):
                        return True
            elif isinstance(node, list):
                return any(_has_private_path(v) for v in node)
            elif isinstance(node, str):
                if re.search(r"(?:^|[\s\"'=])(?:[A-Za-z]:[/\\]|\\\\)", node):
                    return True
            return False
        need(isinstance(indextts2, dict)
             and indextts2.get("adapter") == "scripts/synthesize_indextts2.py"
             and isinstance(indextts2.get("generation_params"), dict)
             and indextts2["generation_params"].get("use_emo_text") is False,
             "default IndexTTS-2.5 configuration and use_emo_text=False required")
        need(not _has_private_path(indextts2),
             "private local paths must stay outside public series-profile.json")
        edge = voice.get("edge_fallback", {})
        need(isinstance(edge, dict) and edge.get("provider") == "Microsoft Edge"
             and edge.get("backend") == "edge-tts"
             and edge.get("speaker") == "zh-CN-YunxiNeural"
             and edge.get("en_speaker") == "en-US-AndrewMultilingualNeural"
             and edge.get("rate") == "+4%"
             and (root / "scripts/synthesize_edge_tts.py").is_file(),
             "paired English and cloud fallback edge-tts configuration required")
        polish = voice.get("speech_polish_preset", {})
        need(isinstance(polish, dict) and polish.get("id") == "mandarin-clone-polish-v1"
             and polish.get("processing_mode") == "whole_track_speech_polish"
             and polish.get("echo") == "none"
             and polish.get("per_shot_normalization") is False
             and polish.get("pitch_shift_semitones") == 0
             and polish.get("speed_factor") == 1
             and polish.get("target_i_lufs") == -18.0
             and polish.get("true_peak_ceiling_dbtp") == -2.0
             and polish.get("output_sample_rate_hz") == 48000
             and isinstance(polish.get("filter_chain"), str)
             and bool(polish["filter_chain"].strip())
             and "aecho" not in polish["filter_chain"].lower(),
             "default #5 speech polish preset without echo required")
        execution = voice.get("execution_policy", {})
        need(isinstance(execution, dict) and execution.get("confirmation_required") is True
             and execution.get("confirmation_scope") == "available_context"
             and execution.get("prefer_existing_project") is True
             and execution.get("missing_location_action") == "ask_user"
             and execution.get("auto_create_environment") is False
             and execution.get("auto_download_model") is False
             and set(execution.get("modes", [])) == {"local_project", "service"},
             "voice invocation confirmation policy required")
        example = voice.get("local_adapter_example", {})
        need(isinstance(example, dict) and example.get("scope") == "optional_local_adapter_only"
             and bool(re.fullmatch(r"[0-9a-f]{40}", str(example.get("model_revision", "")))),
             "optional local adapter fixed revision required")
        c = profile["captions"]
        need(c["apply_once"] is True and bool(c["revision"]), "caption revision must be idempotent")
        for k in ("narration", "real_footage"):
            record = c["baselines"][k]
            need(record["target"] == record["previous"] + c["increment_y"], "caption increment inconsistent")
            need(record["target"] == record["original"] + c["total_y"], "caption total inconsistent")
        need(caption_baselines(profile, 1080, 1920) == {"narration": 1615, "real_footage": 1690}, "current series baseline mismatch")
        limits = profile["delivery"]
        need(limits.get("canvas") == [1920, 1080] and limits.get("aspect_ratio") == "16:9",
             "new production default must be HD landscape")
        landscape = profile.get("landscape_captions", {})
        need(limits.get("caption_layout") == "landscape_captions" and landscape.get("canvas") == [1920, 1080]
             and landscape.get("status") == "project_layout_review_required" and landscape.get("baselines") is None,
             "landscape captions need independent actual layout review, not portrait baseline scaling")
        need(str(c.get("scope", "")).startswith("legacy_portrait_revision_only"), "old caption coordinates must be scoped to legacy portrait")
        need(limits["title_max_codepoints"] == 30 and limits["description_and_tags_max_codepoints"] == 1000,
             "series limits must remain aligned with packet checker")
        tokens_path = local_path(root, root / "config", profile["design"]["tokens"])
        tokens = json.loads(tokens_path.read_text(encoding="utf-8"))
        need(tokens["status"] == "working_baseline_v1" and tokens["science_color_priority"] is True,
             "style defaults must preserve science colors and scoped adoption")
        direction_path = local_path(root, root / "config", profile["design"]["art_direction"])
        direction = json.loads(direction_path.read_text(encoding="utf-8"))
        style_path = local_path(root, root / "config", profile["design"]["style_reference"])
        selected_style_hash = profile["design"].get("style_reference_sha256")
        need(style_path.is_file() and style_path.suffix == ".png", "selected style image missing")
        if style_path.is_file():
            need(hashlib.sha256(style_path.read_bytes()).hexdigest() == selected_style_hash,
                 "selected style image hash mismatch")
        need(profile["design"].get("style_reference_scope") == "legacy_2d_only; not approval for realistic main footage",
             "selected historical style must remain scoped to legacy 2D appearance")
        reference = direction["reference"]
        need(local_path(root, direction_path.parent, reference["file"]) == style_path
             and reference["sha256"] == selected_style_hash, "art direction reference binding mismatch")
        need(local_path(root, tokens_path.parent, tokens["art_direction"]) == direction_path,
             "tokens art direction binding mismatch")
        fields = direction["input_fields"]
        need(isinstance(fields, dict) and bool(fields) and all(isinstance(v, str) and v.strip() for v in fields.values()),
             "art brief input fields missing")
        templates = direction["brief_templates"]
        need(set(templates) == {"whole_scene", "object", "mechanism"}, "art brief modes missing")
        for template in templates.values():
            prompt = template["prompt_template"]
            need(isinstance(prompt, list) and bool(prompt) and all(isinstance(s, str) and s.strip() for s in prompt),
                 "art brief template malformed")
            slots = set(re.findall(r"\{\{([a-z_]+)\}\}", "\n".join(prompt)))
            need(slots == set(fields), "art brief template inputs inconsistent")
        for color in tokens["colors"].values():
            need(bool(HEX.fullmatch(color["hex"])) and bool(color["role"]), "invalid palette color/role")
        ratio = tokens["suggested_scene_ratio"]
        need(ratio["status"] == "adjustable_starting_point", "scene ratio must be adjustable")
        values = [ratio[k] for k in ("air_and_light", "vegetation", "structure", "emphasis")]
        need(all(type(v) in (int, float) and 0 <= v <= 100 for v in values) and sum(values) == 100,
             "starting ratio must sum to 100")
        need("caption_baseline_y" not in tokens["spacing"], "caption position duplicated outside series profile")
        need(tokens["type"]["font_files_bundled"] is False, "font license requires separate verification")

        policy = read("config/production-policy.json")
        audience = policy["audience_text"]
        need(audience["owner"] == "references/visual-system.md#visible-text-purposes-and-production-excuses"
             and audience["plan_stage"] == "G1" and audience["actual_review_stages"] == ["G2", "G3", "G5"], "audience text owner/stages required")
        need(set(audience["surfaces"]) == {"frame", "caption", "voiceover", "cover"}
             and set(audience["forbidden_purposes"]) == {"material_defect", "internal_qa", "production_excuse", "production_meta"}
             and set(audience["protected_purposes"]) == {"scientific_condition", "attribution", "license", "ai_simulation"}
             and audience["source_screening_is_not_actual_media_inspection"] is True, "audience purpose/protected notice boundaries required")
        need(audience.get("label_permission_owner") == "references/visual-system.md#in-picture-markings-require-specific-consent"
             and audience.get("actual_overlay_evidence_required") is True
             and set(audience["allowed_purposes"]) == {"topic", "mechanism", "accessibility", "scientific_condition", "attribution", "license", "ai_simulation", "watermark"}
             and audience.get("default_companion_purposes") == ["ai_simulation"] and audience.get("on_frame_disclosure_requires_specific_consent") is True, "specific label permission and default off-frame AI disclosure required")
        continuity = policy["voice_continuity"]
        need(continuity["owner"] == "references/voice-reference.md#whole-episode-narration-continuity"
             and continuity["required_stages"] == ["G2", "G3", "G5"]
             and continuity["continuous_narration_preferred"] is True
             and continuity["segmentation_requires_verified_capability_and_context_handoff"] is True
             and continuity["same_speaker_seed_decode_asr_is_not_acceptance"] is True
             and continuity["actual_continuous_listening_required"] is True
             and continuity["feedback_failure_owner"] == "qa.visual_frames.failures", "whole-episode continuous voice boundaries required")
        motion = policy["subject_motion"]
        need(motion["owner"] == "references/quality-acceptance.md#subject-motion-and-long-static-holds"
             and motion["required_stages"] == ["G2", "G3", "G5"], "subject motion canonical owner/stages required")
        need(type(motion["max_no_progress_seconds"]) in (int, float) and 0 < motion["max_no_progress_seconds"] <= 3
             and type(motion["max_purposeful_read_seconds"]) in (int, float)
             and 0 < motion["max_purposeful_read_seconds"] <= 1.6, "conservative subject motion project limits required")
        need(motion["automatic_screen_is_not_semantic_acceptance"] is True
             and motion.get("timing_mode") == "review_triggers" and motion.get("observation_hold_requires_actual_review") is True
             and motion["no_cut_or_speed_workaround"] is True, "subject motion screening/semantic boundaries required")
        need(motion["screen"] == {"sample_fps": 4, "sample_size": 64, "mae_threshold": .002, "candidate_min_seconds": 3.0},
             "subject motion screen settings must match current project revision")
        hook = policy["opening_hook"]
        need(hook["owner"] == "references/viral-appeal-and-packaging.md#win-the-first-two-seconds"
             and hook["required_stages"] == ["G1", "G3", "G5"]
             and hook["measurement_tool"] == "scripts/opening_hook.py"
             and (root / hook["measurement_tool"]).is_file()
             and hook["measurement_is_not_appeal_acceptance"] is True, "opening hook owner/stages/tool required")
        need(type(hook["payload_deadline_s"]) in (int, float) and 0 < hook["payload_deadline_s"] <= 4.5
             and type(hook["payload_max_spoken_units"]) is int and 8 <= hook["payload_max_spoken_units"] <= 24
             and type(hook["min_candidates"]) is int and hook["min_candidates"] >= 2
             and 0 < hook["audio_onset_max_s"] <= hook["payload_deadline_s"]
             and 0 < hook["first_caption_max_s"] <= hook["payload_deadline_s"], "opening hook timing defaults out of range")
        retention = policy.get("retention_design", {})
        need(retention.get("owner") == "references/viral-appeal-and-packaging.md#keep-a-reason-to-stay"
             and retention.get("measurement_tool") == "scripts/retention_timeline.py"
             and (root / str(retention.get("measurement_tool"))).is_file()
             and retention.get("measurement_is_not_acceptance") is True
             and retention.get("required_stages") == [], "retention timeline must stay a locator owned by viral appeal")
        window = retention.get("promise_window_s")
        need(isinstance(window, list) and len(window) == 2 and all(type(v) in (int, float) for v in window)
             and hook["payload_deadline_s"] <= window[0] < window[1] <= 15
             and 0 < retention.get("final_answer_min_ratio", 0) < 1
             and 0 < retention.get("answer_to_end_review_s", 0) <= 15
             and 0 < retention.get("payoff_gap_review_s", 0) <= 60, "retention review points out of range")
        feed = policy.get("feed_package", {})
        need(feed.get("owner") == "references/viral-appeal-and-packaging.md#package-the-landscape-master-for-vertical-feeds"
             and feed.get("tool") == "scripts/feed_package.py" and (root / str(feed.get("tool"))).is_file()
             and feed.get("canvas") == [1080, 1920] and feed.get("required_stages") == []
             and feed.get("derivative_does_not_reopen_g5") is True and feed.get("actual_phone_view_required") is True
             and feed.get("header", {}).get("stroke_shadow_or_backing") is False
             and 1.0 <= feed.get("default_zoom", 0) <= feed.get("max_zoom", 0) <= 1.5
             and feed.get("caption_band", {}).get("requires_textless_master") is True
             and feed.get("caption_band", {}).get("anchor") == "final_line_baseline"
             and 1 <= feed.get("caption_band", {}).get("max_lines", 0) <= 3
             and feed.get("default_palette") in feed.get("palettes", {})
             and feed.get("default_palette") not in feed.get("contrast", {}).get("exempt_palettes", [None])
             and 0 < feed.get("contrast", {}).get("band_max_relative_luminance", 1) <= 0.1,
             "vertical feed package must stay a reviewed derivative of the landscape master")
        cov_t = policy.get("cover_typography", {})
        need(cov_t.get("owner") == "references/visual-system.md#finished-cover-standards-for-engineering-and-manufacturing-topics"
             and cov_t.get("tool") == "scripts/compose_cover.py" and (root / str(cov_t.get("tool"))).is_file()
             and limits.get("cover_compositor") == "scripts/compose_cover.py"
             and cov_t.get("title_position") == "upper_left"
             and cov_t.get("main_lines") == 1 and cov_t.get("subtitle_lines") == 2
             and cov_t.get("stroke_shadow_or_backing") is False
             and cov_t.get("no_auto_shrink") is True,
             "cover_typography must lock upper-left 1+2 flat typography via scripts/compose_cover.py without auto-shrink")
        cov_fonts = cov_t.get("fonts", {})
        need(isinstance(cov_fonts, dict) and {"zh", "en"} <= set(cov_fonts)
             and cov_fonts["zh"].get("family") == "Noto Sans SC"
             and cov_fonts["zh"].get("allow_fallback_family") is False
             and all(type(cov_fonts[l].get(k)) is int and cov_fonts[l][k] > 0
                     for l in ("zh", "en") for k in ("main_weight", "subtitle_weight"))
             and all(isinstance(cov_fonts[l].get("candidates"), list) and bool(cov_fonts[l]["candidates"]) for l in ("zh", "en")),
             "cover_typography must lock Noto Sans SC (zh) and en font specs without silent fallback")
        cov_ratios = cov_t.get("ratios", {})
        need(isinstance(cov_ratios, dict) and {"cover_1_1", "cover_3_4", "cover_4_3", "cover_16_9"} <= set(cov_ratios)
             and cov_ratios["cover_1_1"].get("canvas") == [1080, 1080]
             and cov_ratios["cover_3_4"].get("canvas") == [1080, 1440]
             and cov_ratios["cover_4_3"].get("canvas") == [1440, 1080]
             and cov_ratios["cover_16_9"].get("canvas") == [1920, 1080],
             "cover_typography must define locked pixel canvases for 1:1, 3:4, 4:3 and 16:9")
        for rk in ("cover_1_1", "cover_3_4", "cover_4_3", "cover_16_9"):
            rcfg = cov_ratios.get(rk, {})
            need(all(type(rcfg.get(k)) is int and rcfg[k] > 0 for k in ("margin_x", "margin_y", "max_text_width", "mobile_preview_width_px"))
                 and all(type(rcfg.get(l, {}).get(k)) is int and rcfg[l][k] > 0
                         for l in ("zh", "en") for k in ("main_size_px", "subtitle_size_px", "tier_gap_px", "line_gap_px"))
                 and all(rcfg[l]["main_size_px"] > rcfg[l]["subtitle_size_px"] for l in ("zh", "en")),
                 "cover_typography fixed pixel sizes/margins malformed for " + rk)
        cov_presets = cov_t.get("color_presets", {})
        need(isinstance(cov_presets, dict) and len(cov_presets) >= 2
             and cov_t.get("default_palette") in cov_presets
             and all(isinstance(p, dict) and p.get("background_tone") in {"light", "dark"}
                     and bool(HEX.fullmatch(str(p.get("main_hex", ""))))
                     and bool(HEX.fullmatch(str(p.get("subtitle_hex", ""))))
                     and bool(str(p.get("note", "")).strip())
                     for p in cov_presets.values()),
             "cover_typography closed color_presets must define valid hex pairs and light/dark background tones")
        need([policy["defaults"]["output"]["width"], policy["defaults"]["output"]["height"]] == limits["canvas"], "policy output must match current series default canvas")
        audit = policy["realistic_audit"]
        need(audit["owner"] == "references/realistic-direction.md#measure-the-edit-before-judging-it"
             and audit["measurement_tool"] == "scripts/realistic_audit.py"
             and (root / audit["measurement_tool"]).is_file()
             and audit["measurement_is_not_acceptance"] is True
             and audit["required_stages"] == [], "realistic audit must stay a screening tool owned by the realistic direction handbook")
        flow_audit = policy["google_flow_audit"]
        need(flow_audit["owner"] == "references/google-flow-production.md#audit-staged-clips-and-paired-editions-before-delivery"
             and flow_audit["measurement_tool"] == "scripts/google_flow_audit.py"
             and (root / flow_audit["measurement_tool"]).is_file()
             and flow_audit["measurement_is_not_acceptance"] is True
             and flow_audit["required_stages"] == [], "google flow audit must stay a screening tool owned by the google flow handbook")
        need("narrative_depth" not in flow_audit and "min_episode_duration_s" not in flow_audit,
             "google flow audit must not impose mandatory episode duration or word-count floors")
        need(policy["gates"]["order"] == [f"G{i}" for i in range(1, 8)], "G1-G7 stage order required")
        need(sum(policy["quality"]["weights"].values()) == 100, "quality weights must sum to 100")
        need("cold_view" not in policy and policy["internal_review"]["real_audience_required"] is False
             and policy["optional_audience_feedback"]["required"] is False
             and policy["optional_audience_feedback"]["blocks_production"] is False,
             "internal review must not depend on audience recruitment")
        need(policy["internal_review"]["actual_full_audio_visual_review_required"] is True,
             "actual full internal audio/visual review required")
        need(policy["optional_audience_feedback"]["no_synthetic_participants"] is True
             and policy["optional_audience_feedback"]["no_automatic_external_recruitment"] is True,
             "optional feedback must preserve actual participants and authorized recruitment")
        need(policy["quality"]["finesse"]["target_level"] == "L3"
             and policy["quality"]["finesse"]["no_average_override"] is True, "L3 independent dimension target required")
        need(set(policy["listening"]["required_environments"]) == {"headphones", "phone_speaker"}, "dual listening environments required")
        need(policy["defaults"]["semantic_sync_warning_ms"] == 150, "semantic warning starting point changed")
        registry = read("indexes/standard-coverage.json")
        from rebuild_standard_index import build as build_navigation
        need(registry == build_navigation(root), "stale/incomplete chapter navigation; review changes then run rebuild_standard_index.py")
        need(registry.get("schema_version") == 2 and registry.get("authority") == "responsibility_body", "navigation must defer to canonical bodies")
        schema = read("assets/production-asset.schema.json")
        need(schema["$schema"] == "https://json-schema.org/draft/2020-12/schema", "asset schema version required")
        need({"name", "category", "approval", "sha256"} <= set(schema["required"]), "formal asset fields missing")

        refs = read("indexes/aesthetic-references.json")
        need(refs["catalog"] == "aesthetic_references", "wrong reference catalog")
        ref_ids = []
        local_styles = []
        for r in refs["entries"]:
            ref_ids.append(r["id"])
            need(r["production_use"] == "not_granted", "aesthetic reference does not grant production use")
            need(("url" in r) != ("file" in r), "aesthetic reference needs exactly one URL or local file")
            if "file" in r:
                p = local_path(root, root, r["file"])
                need(p.is_file(), "local aesthetic reference missing")
                if p.is_file():
                    need(hashlib.sha256(p.read_bytes()).hexdigest() == r.get("sha256"),
                         "local aesthetic reference hash mismatch")
                need(r.get("approval_scope") == "visual_style_only" and bool(r.get("rights_scope")),
                     "local aesthetic reference needs scoped appearance and use boundaries")
                local_styles.append((p, r.get("sha256")))
            else:
                need(isinstance(r.get("url"), str) and r["url"].startswith("https://"),
                     "aesthetic reference URL must use HTTPS")
            need(bool(r["version"]) and bool(r["viewing_status"]), "reference version/viewing scope required")
        need(len(ref_ids) == len(set(ref_ids)), "duplicate aesthetic reference id")
        need((style_path, selected_style_hash) in local_styles, "selected style missing from aesthetic references")
        assets = read("indexes/reusable-assets.json")
        need(assets["catalog"] == "reusable_assets", "wrong reusable asset catalog")
        ids = []
        for a in assets["entries"]:
            ids.append(a["id"])
            p = local_path(root, root, a["file"])
            need(p.is_file(), "indexed asset missing")
            if not p.is_file():
                continue
            need(hashlib.sha256(p.read_bytes()).hexdigest() == a["sha256"], "indexed asset hash mismatch")
            need(all(a.get(k) for k in ("version", "status", "use", "not_for", "approval_scope")), "asset scope fields missing")
            need(all(a["rights"].get(k) for k in ("basis", "evidence", "scope")), "asset rights evidence missing")
            need(p.suffix in (".svg", ".json", ".css", ".py"), "public catalog contains production media")
            if p.suffix == ".svg":
                for node in ET.fromstring(p.read_text(encoding="utf-8")).iter():
                    need(node.tag.split("}")[-1] not in ("image", "script", "foreignObject"), "SVG embeds media or executable content")
                    for key, value in node.attrib.items():
                        if key.split("}")[-1] in ("href", "src"):
                            need(value.startswith("#"), "SVG external dependency")
        need(len(ids) == len(set(ids)), "duplicate asset id")

        external = read("indexes/external-skills.json")
        need(external["catalog"] == "external_skills" and len(external["entries"]) == external["entry_count"],
             "external skills catalog/count inconsistent")
        external_ids = []
        copies = 0
        for entry in external["entries"]:
            external_ids.append(entry["id"])
            need(bool(re.fullmatch(r"[0-9a-f]{40}", entry["commit"])) and entry["repository"].startswith("https://github.com/"),
                 "external source needs immutable commit and primary repository")
            for source in entry["source_files"]:
                need(bool(re.fullmatch(r"[0-9a-f]{64}", source["sha256"])) and entry["commit"] in source["url"],
                     "external source file needs fixed version/hash")
                if source.get("local_copy"):
                    copied = local_path(root, root, source["local_copy"])
                    need(copied.is_file() and hashlib.sha256(copied.read_bytes()).hexdigest() == source["sha256"],
                         "copied external reference hash mismatch")
                    if copied.name != "LICENSE":
                        copies += 1
                    need(bool(entry["license"]["evidence"]), "copied reference needs actual license evidence")
        need(len(set(external_ids)) == len(external_ids) and copies == external["copied_reference_count"],
             "external source identity/copy count inconsistent")

        for p in root.rglob("*"):
            if any(part in {".git", "__pycache__"} for part in p.relative_to(root).parts):
                continue
            if p.is_file() and p.suffix in (".md", ".json", ".svg", ".css", ".py"):
                text = p.read_text(encoding="utf-8")
                need(PRIVATE_ID.search(text) is None, "private identity in public resource: " + str(p.relative_to(root)))
                if p.suffix != ".md":
                    continue
                for link in re.findall(r"\]\(([^)]+)\)", text):
                    if "://" in link or link.startswith("mailto:"):
                        continue
                    name, _, anchor = link.partition("#")
                    target = local_path(root, p.parent, name) if name else p
                    need(target.exists(), "broken local link: " + link)
                    if anchor and target.is_file() and target.suffix == ".md":
                        heads = [slug(h) for h in re.findall(r"^#+ (.+)$", target.read_text(encoding="utf-8"), re.M)]
                        need(anchor in heads, "broken heading link: " + link)
    except (KeyError, IndexError, TypeError, ValueError, OSError, ET.ParseError) as exc:
        errors.append("malformed reference system: " + str(exc))
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    problems = check(args.root)
    for problem in problems:
        print("ERROR:", problem)
    if not problems:
        print("Reference/config/catalog structure passed; actual design, rights and media remain separate reviews.")
    raise SystemExit(bool(problems))
