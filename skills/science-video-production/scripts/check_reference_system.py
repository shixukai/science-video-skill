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
        need(profile["schema_version"] == 1 and profile["version"] == "1.1.0", "unsupported profile schema/version")
        need(profile["medium"]["mechanism"] == "pure_2d", "current series requires pure 2D")
        need(profile["medium"]["real_anchor"] == "authentic_continuous_video", "real video anchor required")
        need(profile["audio"]["speaker"] == "Serena" and profile["audio"]["language"] == "Chinese", "current voice configuration changed")
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
        need(policy["gates"]["order"] == [f"G{i}" for i in range(1, 8)], "G1-G7 stage order required")
        need(sum(policy["quality"]["weights"].values()) == 100, "quality weights must sum to 100")
        need(policy["cold_view"]["real_viewers"] == 5 and policy["cold_view"]["no_synthetic_participants"] is True, "real cold-view requirement changed")
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
        need(len(rule_ids) == 958 and len(set(rule_ids)) == len(rule_ids), "full source requirement coverage missing/duplicate")
        schema = read("assets/production-asset.schema.json")
        need(schema["$schema"] == "https://json-schema.org/draft/2020-12/schema", "asset schema version required")
        need({"name", "category", "approval", "sha256"} <= set(schema["required"]), "formal asset fields missing")

        refs = read("indexes/aesthetic-references.json")
        need(refs["catalog"] == "aesthetic_references", "wrong reference catalog")
        for r in refs["entries"]:
            need(r["url"].startswith("https://") and r["production_use"] == "not_granted",
                 "aesthetic reference does not grant production use")
            need(bool(r["version"]) and bool(r["viewing_status"]), "reference version/viewing scope required")
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
