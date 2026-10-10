#!/usr/bin/env python3
"""Offline structural checks; never art, rights, media or publication approval."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET

OWNER_IDS = {"topic", "science-rights", "production", "visual", "voice", "shotbook", "quality"}
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
        need({o["id"] for o in owners} == OWNER_IDS and len(owners) == 7, "exactly seven responsibility owners required")
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

        profile = read("config/series-profile.json")
        need(profile["schema_version"] == 1 and profile["version"] == "1.3.0", "unsupported profile schema/version")
        need(profile["medium"]["mechanism"] == "pure_2d", "current series requires pure 2D")
        need(profile["medium"]["real_anchor"] == "authentic_continuous_video", "real video anchor required")
        need(profile["audio"]["speaker"] == "Serena" and profile["audio"]["language"] == "Chinese", "current voice configuration changed")
        voice = profile["audio"]
        need(voice.get("backend") == "confirm_at_invocation" and voice.get("provider") == "Qwen",
             "voice execution location must be confirmed at invocation")
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
        need(profile["design"].get("style_reference_scope") == "visual_style_only",
             "selected style scope must remain appearance only")
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
        need(audience["owner"] == "references/visual-system.md#可见文字用途与制作辩解"
             and audience["plan_stage"] == "G1" and audience["actual_review_stages"] == ["G2", "G3", "G5"], "audience text owner/stages required")
        need(set(audience["surfaces"]) == {"frame", "caption", "voiceover", "cover"}
             and set(audience["forbidden_purposes"]) == {"material_defect", "internal_qa", "production_excuse"}
             and set(audience["protected_purposes"]) == {"scientific_condition", "attribution", "license", "ai_simulation"}
             and audience["source_screening_is_not_actual_media_inspection"] is True, "audience purpose/protected notice boundaries required")
        continuity = policy["voice_continuity"]
        need(continuity["owner"] == "references/voice-reference.md#整期旁白连续性"
             and continuity["required_stages"] == ["G2", "G3", "G5"]
             and continuity["continuous_narration_preferred"] is True
             and continuity["segmentation_requires_verified_capability_and_context_handoff"] is True
             and continuity["same_speaker_seed_decode_asr_is_not_acceptance"] is True
             and continuity["actual_continuous_listening_required"] is True
             and continuity["feedback_failure_owner"] == "qa.visual_frames.failures", "whole-episode continuous voice boundaries required")
        motion = policy["subject_motion"]
        need(motion["owner"] == "references/quality-acceptance.md#主体动态与长静帧"
             and motion["required_stages"] == ["G2", "G3", "G5"], "subject motion canonical owner/stages required")
        need(type(motion["max_no_progress_seconds"]) in (int, float) and 0 < motion["max_no_progress_seconds"] <= 3
             and type(motion["max_purposeful_read_seconds"]) in (int, float)
             and 0 < motion["max_purposeful_read_seconds"] <= 1.6, "conservative subject motion project limits required")
        need(motion["automatic_screen_is_not_semantic_acceptance"] is True
             and motion["no_whole_semantic_unit_exception"] is True
             and motion["no_cut_or_speed_workaround"] is True, "subject motion screening/semantic boundaries required")
        need(motion["screen"] == {"sample_fps": 4, "sample_size": 64, "mae_threshold": .002, "candidate_min_seconds": 3.0},
             "subject motion screen settings must match current project revision")
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
        # Exact references prove only integrity, not the semantics or actual execution.
        failure_contracts = {}
        for contract in registry.get("failure_contracts", []):
            ident = contract.get("id")
            need(isinstance(ident, str) and bool(ident) and ident not in failure_contracts, "failure contract ID missing/duplicate")
            failure_contracts[ident] = contract
            need(bool(contract.get("failure_condition")) and bool(contract.get("application")), "specific failure/application condition required")
            clauses = contract.get("clauses")
            need(isinstance(clauses, list) and bool(clauses), "precise failure clauses required")
            for clause in clauses or []:
                p = local_path(root, root, clause["file"])
                body = p.read_text(encoding="utf-8")
                quote = clause.get("quote")
                valid = isinstance(quote, str) and bool(quote.strip())
                need(valid and quote in body, "failure clause text missing/stale")
                need(valid and hashlib.sha256(quote.encode()).hexdigest() == clause.get("quote_sha256"), "failure clause digest inconsistent")
                headings = list(re.finditer(r"^(#+) (.+)$", body, re.M))
                matching = [i for i, h in enumerate(headings) if slug(h.group(2)) == clause.get("anchor")]
                need(bool(matching), "failure clause anchor missing")
                if matching and valid:
                    i = matching[0]; start = headings[i].end(); level = len(headings[i].group(1))
                    end = next((h.start() for h in headings[i+1:] if len(h.group(1)) <= level), len(body))
                    need(quote in body[start:end], "failure clause outside referenced section")
        need(bool(failure_contracts), "precise failure contracts missing")
        navigation = registry.get("explanation_standard", {})
        need(navigation.get("status") == "navigation_only" and navigation.get("authority") == "responsibility_body", "explanation navigation must defer to responsibility body")
        entries = navigation.get("entries", [])
        need(isinstance(entries, list) and len(entries) == 12 and {e.get("id") for e in entries if isinstance(e, dict)} == {f"E{i:02}" for i in range(1, 13)}, "E01-E12 explanation navigation missing/duplicate")
        for entry in entries:
            target = local_path(root, root, entry.get("owner"))
            need(str(target) in owner_files, "explanation navigation has no canonical owner")
            heads = [slug(h) for h in re.findall(r"^#+ (.+)$", target.read_text(), re.M)]
            need(entry.get("owner_anchor") in heads, "explanation navigation anchor missing")
            contracts = entry.get("contract_ids", [])
            valid = isinstance(contracts, list) and bool(contracts) and all(isinstance(i, str) and i in failure_contracts for i in contracts)
            need(valid, "explanation navigation contract missing")
            if valid:
                for ident in contracts:
                    clauses = failure_contracts[ident].get("clauses", [])
                    need(bool(clauses) and all(c.get("file") == entry.get("owner") and c.get("anchor") == entry.get("owner_anchor") for c in clauses), "explanation navigation contract owner/anchor mismatch")
        rule_ids = []
        for rule in registry["rules"]:
            rule_ids.append(rule["id"])
            failure_ref = rule.get("failure_condition_ref", {})
            ref_ids = failure_ref.get("contract_ids", [failure_ref.get("contract_id")]) if isinstance(failure_ref, dict) else []
            need(isinstance(ref_ids, list) and bool(ref_ids) and all(isinstance(i, str) and i in failure_contracts for i in ref_ids) and len(set(ref_ids)) == len(ref_ids), "rule precise failure reference missing")
            need(rule.get("action") == rule.get("rule") and bool(rule.get("action")), "rule concrete action missing")
            need(rule.get("mapping_status") in ("verified_semantic_mapping", "source_boundary_or_conditional"), "rule semantic mapping unresolved")
            need(bool(rule["rule"]) and rule["modality"] in ("hard", "recommended", "default", "conditional", "permission", "boundary"), "invalid standard rule")
            target = local_path(root, root, rule["owner"])
            need(str(target) in owner_files, "standard rule has no canonical owner")
            heads = [slug(h) for h in re.findall(r"^#+ (.+)$", target.read_text(), re.M)]
            need(rule.get("owner_anchor") in heads, "standard rule anchor missing")
            need(rule.get("applicability_contract") in registry.get("contracts", {}) and rule.get("failure_contract") in registry.get("contracts", {}), "rule conditions/failure contract missing")
            need(rule.get("sample_reference") in registry.get("sample_references", {}), "rule sample scope missing")
            for location in rule.get("evidence_locations", []):
                evidence_path = local_path(root, root, location["file"])
                value = json.loads(evidence_path.read_text())
                for key in re.findall(r"[^.\[\]]+", location["selector"]):
                    value = value[int(key)] if isinstance(value, list) else value[key]
        need(len(rule_ids) == registry.get("rule_count") and len(set(rule_ids)) == len(rule_ids)
             and len(rule_ids) > 0, "current requirement coverage count missing/duplicate")
        need({"EX-structure", "EX-expression-card", "EX-internal-review", "ART-finesse", "VOICE-execution", "MOTION-subject-continuity", "TEXT-audience-purpose", "VOICE-continuity"} <= set(rule_ids),
             "current explanation/finesse/voice coverage missing")
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
                for node in ET.fromstring(p.read_text()).iter():
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
                        heads = [slug(h) for h in re.findall(r"^#+ (.+)$", target.read_text(), re.M)]
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
