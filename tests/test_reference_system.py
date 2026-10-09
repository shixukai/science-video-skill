#!/usr/bin/env python3
"""Behavioral regression tests for the reference/config/catalog contract."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / "skills/science-video-production"
spec = importlib.util.spec_from_file_location("reference_checks", ROOT / "scripts/check_reference_system.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReferenceSystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "skill"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns("__pycache__"))
    def tearDown(self):
        self.temp.cleanup()
    def edit(self, path, f):
        p = self.root / path
        d = json.loads(p.read_text())
        f(d)
        p.write_text(json.dumps(d, ensure_ascii=False))
    def errors(self, text):
        self.assertTrue(any(text in e for e in m.check(self.root)), m.check(self.root))
    def test_clean_system(self):
        self.assertEqual(m.check(self.root), [])
    def test_audience_cannot_be_restored_as_production_requirement(self):
        self.edit("config/production-policy.json", lambda d: d["internal_review"].update(real_audience_required=True))
        self.errors("must not depend on audience")
    def test_global_profile_cannot_force_a_local_execution_location(self):
        self.edit("config/series-profile.json", lambda d: d["audio"].update(backend="local_qwen"))
        self.errors("confirmed at invocation")
    def test_voice_location_needs_confirmation_before_execution(self):
        self.edit("config/series-profile.json", lambda d: d["audio"]["execution_policy"].update(confirmation_required=False))
        self.errors("invocation confirmation policy")
    def test_voice_location_must_not_create_a_new_environment_automatically(self):
        self.edit("config/series-profile.json", lambda d: d["audio"]["execution_policy"].update(auto_create_environment=True))
        self.errors("invocation confirmation policy")
    def test_moving_model_revision_is_not_a_fixed_default(self):
        self.edit("config/series-profile.json", lambda d: d["audio"]["local_adapter_example"].update(model_revision="main"))
        self.errors("optional local adapter fixed revision")
    def test_aesthetic_average_cannot_replace_dimension_completion(self):
        self.edit("config/production-policy.json", lambda d: d["quality"]["finesse"].update(no_average_override=False))
        self.errors("independent dimension target")
    def test_external_sources_are_immutable(self):
        self.edit("indexes/external-skills.json", lambda d: d["entries"][0].update(commit="main"))
        self.errors("immutable commit")
    def test_modified_copied_reference_needs_explicit_update(self):
        p = self.root / "third-party/videozero-motion-canvas/TWEENING.md"
        p.write_text(p.read_text() + "\nAltered example\n")
        self.errors("copied external reference hash mismatch")
    def test_explanation_navigation_required(self):
        self.edit("indexes/standard-coverage.json", lambda d: d.pop("explanation_standard"))
        self.errors("E01-E12 explanation navigation")
    def test_explanation_navigation_duplicate_rejected(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["explanation_standard"]["entries"][1].update(id="E01"))
        self.errors("E01-E12 explanation navigation")
    def test_explanation_navigation_contract_required(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["explanation_standard"]["entries"][0].update(contract_ids=["missing-contract"]))
        self.errors("explanation navigation contract missing")
    def test_explanation_navigation_anchor_required(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["explanation_standard"]["entries"][0].update(owner_anchor="nonexistent"))
        self.errors("explanation navigation anchor missing")
    def test_optional_feedback_cannot_be_mandatory(self):
        self.edit("config/production-policy.json", lambda d: d["optional_audience_feedback"].update(required=True))
        self.errors("must not depend on audience")
    def test_internal_perception_cannot_be_disabled(self):
        self.edit("config/production-policy.json", lambda d: d["internal_review"].update(actual_full_audio_visual_review_required=False))
        self.errors("actual full internal audio/visual review required")
    def test_optional_feedback_cannot_use_synthetic_participants(self):
        self.edit("config/production-policy.json", lambda d: d["optional_audience_feedback"].update(no_synthetic_participants=False))
        self.errors("actual participants and authorized recruitment")
    def test_optional_feedback_cannot_recruit_automatically(self):
        self.edit("config/production-policy.json", lambda d: d["optional_audience_feedback"].update(no_automatic_external_recruitment=False))
        self.errors("actual participants and authorized recruitment")
    def test_duplicate_responsibility(self):
        self.edit("indexes/rule-owners.json", lambda d: d["owners"][1]["owns"].append(d["owners"][0]["owns"][0]))
        self.errors("multiple owners")
    def test_missing_owner(self):
        self.edit("indexes/rule-owners.json", lambda d: d["owners"].pop())
        self.errors("seven")
    def test_missing_reference_file(self):
        (self.root / "references/shotbook.md").unlink()
        self.errors("owner file")
    def test_caption_idempotence_and_scaling(self):
        p = json.loads((self.root / "config/series-profile.json").read_text())
        self.assertEqual(m.caption_baselines(p, 1080, 1920), {"narration": 1615, "real_footage": 1690})
        self.assertEqual(m.caption_baselines(p, 1080, 1920), m.caption_baselines(copy.deepcopy(p), 1080, 1920))
        self.assertEqual(m.caption_baselines(p, 540, 960), {"narration": 808, "real_footage": 845})
        with self.assertRaises(ValueError):
            m.caption_baselines(p, 1920, 1080)
    def test_repeated_caption_increment_rejected(self):
        self.edit("config/series-profile.json", lambda d: d["captions"]["baselines"]["narration"].update(target=1515))
        self.errors("increment inconsistent")
    def test_real_video_required(self):
        self.edit("config/series-profile.json", lambda d: d["medium"].update(real_anchor="photo"))
        self.errors("real video")
    def test_reference_not_media_license(self):
        self.edit("indexes/aesthetic-references.json", lambda d: d["entries"][0].update(production_use="granted"))
        self.errors("does not grant")
    def test_selected_style_image_cannot_be_replaced_without_rebinding(self):
        path = self.root / "assets/style/accepted-style-reference.png"
        path.write_bytes(path.read_bytes() + b"altered-reference")
        self.errors("selected style image hash mismatch")
        self.errors("local aesthetic reference hash mismatch")
    def test_selected_style_path_cannot_escape_the_skill(self):
        self.edit("config/series-profile.json", lambda d: d["design"].update(style_reference="../../outside.png"))
        self.errors("path escapes Skill")
    def test_selected_style_does_not_approve_science_or_motion(self):
        self.edit("config/series-profile.json", lambda d: d["design"].update(style_reference_scope="complete_episode"))
        self.errors("appearance only")
    def test_art_brief_cannot_silently_bind_a_different_reference(self):
        self.edit("assets/style/bright-nature.art-direction.json", lambda d: d["reference"].update(sha256="0" * 64))
        self.errors("art direction reference binding mismatch")
    def test_local_style_reference_is_not_a_cleared_production_asset(self):
        self.edit("indexes/aesthetic-references.json", lambda d: d["entries"][-1].update(production_use="granted"))
        self.errors("does not grant")
    def test_local_reference_cannot_have_two_conflicting_locations(self):
        self.edit("indexes/aesthetic-references.json", lambda d: d["entries"][-1].update(url="https://example.com/other-style"))
        self.errors("exactly one URL or local file")
    def test_changed_component_needs_new_hash(self):
        p = self.root / "assets/style/leader-and-arrow.svg"
        p.write_text(p.read_text().replace("#243840", "#000000"))
        self.errors("hash mismatch")
    def test_external_svg_dependency(self):
        p = self.root / "assets/style/leader-and-arrow.svg"
        p.write_text(p.read_text().replace("</svg>", '<image href="https://example.test/private.png"/></svg>'))
        self.errors("embeds media")
    def test_path_escape_rejected(self):
        self.edit("indexes/reusable-assets.json", lambda d: d["entries"][0].update(file="../../outside.svg"))
        self.errors("escapes")
    def test_duplicate_asset_id(self):
        self.edit("indexes/reusable-assets.json", lambda d: d["entries"].append(copy.deepcopy(d["entries"][0])))
        self.errors("duplicate asset")
    def test_science_color_priority(self):
        self.edit("assets/style/bright-nature.tokens.json", lambda d: d.update(science_color_priority=False))
        self.errors("science colors")
    def test_ratio_not_universal_gate(self):
        self.edit("assets/style/bright-nature.tokens.json", lambda d: d["suggested_scene_ratio"].update(status="mandatory"))
        self.errors("adjustable")
    def test_invalid_hex_rejected(self):
        self.edit("assets/style/bright-nature.tokens.json", lambda d: d["colors"]["sky"].update(hex="blue"))
        self.errors("palette")
    def test_private_id_rejected(self):
        (self.root / "leak.md").write_text("libfile_" + "a" * 32)
        self.errors("private identity")
    def test_broken_anchor_rejected(self):
        p = self.root / "SKILL.md"
        p.write_text(p.read_text() + "\n[broken](references/visual-system.md#not-a-section)\n")
        self.errors("broken heading")
    def test_malformed_config_rejected(self):
        (self.root / "config/series-profile.json").write_text("{")
        self.errors("malformed")


    def test_failure_clause_text_stale(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["failure_contracts"][0]["clauses"][0].update(quote="invented reference text"))
        self.errors("failure clause text missing/stale")
    def test_failure_clause_digest_stale(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["failure_contracts"][0]["clauses"][0].update(quote_sha256="0" * 64))
        self.errors("failure clause digest inconsistent")
    def test_failure_contract_unresolved(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["rules"][0].update(failure_condition_ref={"contract_id":"unknown"}))
        self.errors("rule precise failure reference missing")
    def test_unreviewed_mapping_cannot_claim_complete(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["rules"][0].update(mapping_status="pending"))
        self.errors("rule semantic mapping unresolved")

    def test_requirement_count_must_match_current_registry(self):
        self.edit("indexes/standard-coverage.json", lambda d: d.update(rule_count=d["rule_count"] + 1))
        self.errors("current requirement coverage count missing/duplicate")

    def test_requirement_count_tracks_new_unique_rules(self):
        def append_rule(registry):
            rule = copy.deepcopy(registry["rules"][0])
            rule["id"] = "TEST-unique-current-requirement"
            registry["rules"].append(rule)
            registry["rule_count"] = len(registry["rules"])
        self.edit("indexes/standard-coverage.json", append_rule)
        self.assertEqual(m.check(self.root), [])

    def test_current_explanation_finesse_voice_rules_cannot_be_removed(self):
        def remove_rule(registry):
            registry["rules"] = [r for r in registry["rules"] if r["id"] != "VOICE-execution"]
            registry["rule_count"] = len(registry["rules"])
        self.edit("indexes/standard-coverage.json", remove_rule)
        self.errors("current explanation/finesse/voice coverage missing")

    def test_art_handoff_rule_removal_breaks_reference_integrity(self):
        """Deleting an execution boundary must fail structurally, not judge art."""
        contracts = {c["id"]: c for c in json.loads(
            (self.root / "indexes/standard-coverage.json").read_text())["failure_contracts"]}
        cases = [
            ("field-gates", "G2的低精细度指尚未精修", "references/production-checkpoints.md"),
            ("field-style_approval", "把当前生产资产经实际渲染", "references/visual-system.md"),
            ("field-style_approval", "若实际资产已变成另一种造型语言", "references/visual-system.md"),
            ("V-natural_editable_shapes", "对本镜需要独立显隐", "references/visual-system.md"),
            ("field-art", "已有批准画风时，美术审查须核", "references/quality-acceptance.md"),
        ]
        for ident, prefix, owner in cases:
            with self.subTest(contract=ident, clause=prefix):
                matches = [c for c in contracts[ident]["clauses"] if c["quote"].startswith(prefix)]
                self.assertEqual(len(matches), 1, "Execution rule must have a precise existing-contract reference")
                clause = matches[0]
                self.assertEqual(clause["file"], owner)
                p = self.root / owner
                original = p.read_text()
                try:
                    p.write_text(original.replace(clause["quote"], ""))
                    self.errors("failure clause text missing/stale")
                finally:
                    p.write_text(original)
        self.assertEqual(m.check(self.root), [])

    def test_spatial_relation_owner_clauses_cannot_be_removed(self):
        """Test owner/reference integrity, not whether a scene is understandable."""
        registry = json.loads((self.root / "indexes/standard-coverage.json").read_text())
        contracts = {c["id"]: c for c in registry["failure_contracts"]}
        owners = {o["id"]: o["file"] for o in json.loads(
            (self.root / "indexes/rule-owners.json").read_text())["owners"]}
        routes = [
            ("H-h-failure-100", "production", "逐段声画与图内文字对应", 2),
            ("field-art", "visual", "纯2d解释与真实素材", 1),
        ]
        for ident, owner, anchor, expected_count in routes:
            clauses = [c for c in contracts[ident]["clauses"]
                       if c["file"] == owners[owner] and c["anchor"] == anchor]
            self.assertEqual(len(clauses), expected_count)
            for clause in clauses:
                with self.subTest(contract=ident, digest=clause["quote_sha256"]):
                    p = self.root / owners[owner]
                    original = p.read_text()
                    try:
                        p.write_text(original.replace(clause["quote"], ""))
                        self.errors("failure clause text missing/stale")
                    finally:
                        p.write_text(original)
        self.assertEqual(m.check(self.root), [])

    def test_spatial_quality_cross_reference_rejects_broken_owner_anchor(self):
        """A synchronized quote/hash must not hide a broken responsibility link."""
        target = "production-checkpoints.md#逐段声画与图内文字对应"
        broken = "production-checkpoints.md#missing-spatial-relation"
        registry_path = self.root / "indexes/standard-coverage.json"
        registry = json.loads(registry_path.read_text())
        contract = next(c for c in registry["failure_contracts"] if c["id"] == "field-art")
        matches = [c for c in contract["clauses"]
                   if c["file"] == "references/quality-acceptance.md" and target in c["quote"]]
        self.assertEqual(len(matches), 1)
        p = self.root / "references/quality-acceptance.md"
        p.write_text(p.read_text().replace(target, broken))
        for contract in registry["failure_contracts"]:
            for clause in contract["clauses"]:
                if clause["file"] == "references/quality-acceptance.md" and target in clause["quote"]:
                    clause["quote"] = clause["quote"].replace(target, broken)
                    clause["quote_sha256"] = hashlib.sha256(clause["quote"].encode()).hexdigest()
        registry_path.write_text(json.dumps(registry, ensure_ascii=False))
        self.errors("broken heading link")

    def test_feedback_scope_clauses_keep_their_responsibility_owners(self):
        """Missing scope/closure references fail; no media scope is inferred."""
        registry = json.loads((self.root / "indexes/standard-coverage.json").read_text())
        contracts = {c["id"]: c for c in registry["failure_contracts"]}
        owners = {o["id"]: o["file"] for o in json.loads(
            (self.root / "indexes/rule-owners.json").read_text())["owners"]}
        routes = [
            ("V-allowed_stage", "production", "3-阶段推进与代表样", 2),
            ("V-failure_scope", "quality", "失败后的处理", 1),
            ("V-regression", "quality", "失败后的处理", 1),
        ]
        for ident, owner, anchor, expected_count in routes:
            clauses = contracts[ident]["clauses"]
            self.assertEqual(len(clauses), expected_count)
            for clause in clauses:
                with self.subTest(contract=ident, digest=clause["quote_sha256"]):
                    self.assertEqual((clause["file"], clause["anchor"]), (owners[owner], anchor))
                    p = self.root / owners[owner]
                    original = p.read_text()
                    try:
                        p.write_text(original.replace(clause["quote"], ""))
                        self.errors("failure clause text missing/stale")
                    finally:
                        p.write_text(original)
        self.assertEqual(m.check(self.root), [])

    def test_feedback_scope_links_fail_even_with_synchronized_quotes(self):
        registry_path = self.root / "indexes/standard-coverage.json"
        original_registry = registry_path.read_text()
        routes = [
            ("references/production-checkpoints.md", "quality-acceptance.md#失败后的处理"),
            ("references/quality-acceptance.md", "production-checkpoints.md#3-阶段推进与代表样"),
            ("references/quality-acceptance.md", "#记录与技术检查"),
        ]
        for file, target in routes:
            with self.subTest(file=file, target=target):
                p = self.root / file
                original = p.read_text()
                self.assertIn("](" + target + ")", original)
                broken = target.split("#", 1)[0] + "#missing-feedback-scope-target"
                registry = json.loads(original_registry)
                try:
                    p.write_text(original.replace(target, broken))
                    for contract in registry["failure_contracts"]:
                        for clause in contract["clauses"]:
                            if clause["file"] == file and target in clause["quote"]:
                                clause["quote"] = clause["quote"].replace(target, broken)
                                clause["quote_sha256"] = hashlib.sha256(clause["quote"].encode()).hexdigest()
                    registry_path.write_text(json.dumps(registry, ensure_ascii=False))
                    self.errors("broken heading link")
                finally:
                    p.write_text(original)
                    registry_path.write_text(original_registry)
        self.assertEqual(m.check(self.root), [])

if __name__ == "__main__":
    unittest.main()
