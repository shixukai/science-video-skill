#!/usr/bin/env python3
"""Behavioral regression tests for the reference/config/catalog contract."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / "skills/science-video-production"
sys.path.insert(0, str(ROOT / "scripts"))
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
    def test_legacy_pure_2d_cannot_be_default_main_picture(self):
        self.edit("config/series-profile.json", lambda d: d["medium"].update(mechanism="pure_2d"))
        self.errors("realistic main footage")
    def test_legacy_style_must_not_claim_realistic_approval(self):
        self.edit("config/series-profile.json", lambda d: d["design"].update(style_reference_scope="visual_style_only"))
        self.errors("scoped to legacy 2D")
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
    def test_optional_feedback_cannot_be_mandatory(self):
        self.edit("config/production-policy.json", lambda d: d["optional_audience_feedback"].update(required=True))
        self.errors("must not depend on audience")
    def test_internal_perception_cannot_be_disabled(self):
        self.edit("config/production-policy.json", lambda d: d["internal_review"].update(actual_full_audio_visual_review_required=False))
        self.errors("actual full internal audio/visual review required")
    def test_audience_text_protected_notices_cannot_be_disabled(self):
        self.edit("config/production-policy.json", lambda d: d["audience_text"].update(protected_purposes=[]))
        self.errors("audience purpose/protected notice boundaries required")
    def test_audience_source_checks_cannot_replace_actual_inspection(self):
        self.edit("config/production-policy.json", lambda d: d["audience_text"].update(source_screening_is_not_actual_media_inspection=False))
        self.errors("audience purpose/protected notice boundaries required")
    def test_actual_continuous_voice_listening_cannot_be_disabled(self):
        self.edit("config/production-policy.json", lambda d: d["voice_continuity"].update(actual_continuous_listening_required=False))
        self.errors("whole-episode continuous voice boundaries required")
    def test_segmentation_capability_requirement_cannot_be_disabled(self):
        self.edit("config/production-policy.json", lambda d: d["voice_continuity"].update(segmentation_requires_verified_capability_and_context_handoff=False))
        self.errors("whole-episode continuous voice boundaries required")
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
        self.errors("complete responsibility owners")
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
        self.errors("scoped to legacy 2D")
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
        p.write_text(p.read_text().replace("<svg ", '<svg data-test-mutation="1" ', 1))
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


    def test_observation_hold_cannot_bypass_actual_review(self):
        self.edit("config/production-policy.json", lambda d: d["subject_motion"].update(observation_hold_requires_actual_review=False))
        self.errors("subject motion screening/semantic boundaries required")

    def test_subject_motion_project_limit_cannot_be_weakened_to_ten_seconds(self):
        self.edit("config/production-policy.json", lambda d: d["subject_motion"].update(max_no_progress_seconds=10))
        self.errors("conservative subject motion project limits required")


    def test_navigation_cannot_be_promoted_to_rule_authority(self):
        self.edit("indexes/standard-coverage.json", lambda d: d.update(authority="rules"))
        self.errors("navigation must defer to canonical bodies")

    def test_navigation_must_cover_every_canonical_body(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["sections"].pop())
        self.errors("stale/incomplete chapter navigation")

    def test_duplicate_navigation_entry_is_rejected(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["sections"].append(copy.deepcopy(d["sections"][0])))
        self.errors("stale/incomplete chapter navigation")

    def test_navigation_cannot_invent_an_owner(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["sections"][0].update(owner_id="unknown"))
        self.errors("stale/incomplete chapter navigation")

    def test_navigation_rejects_a_forged_body_digest(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["sections"][0].update(sha256="0" * 64))
        self.errors("stale/incomplete chapter navigation")

    def test_navigation_rejects_a_missing_heading(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["sections"][0]["anchors"].pop())
        self.errors("stale/incomplete chapter navigation")

    def test_navigation_rejects_a_forged_heading(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["sections"][0]["anchors"].append("invented"))
        self.errors("stale/incomplete chapter navigation")

    def test_navigation_cannot_reintroduce_copied_requirements(self):
        self.edit("indexes/standard-coverage.json", lambda d: d.update(rules=[{"quote":"invented requirement"}]))
        self.errors("stale/incomplete chapter navigation")

    def test_body_edit_invalidates_navigation_even_without_heading_changes(self):
        p = self.root / "references/quality-acceptance.md"
        p.write_bytes(p.read_bytes() + b"\nChanged body.\n")
        self.errors("stale/incomplete chapter navigation")

    def test_supporting_body_edit_invalidates_navigation(self):
        p = self.root / "references/animation-scene-design.md"
        p.write_bytes(p.read_bytes() + b"\nChanged supporting body.\n")
        self.errors("stale/incomplete chapter navigation")

    def test_rebuild_is_navigation_only_and_does_not_claim_review(self):
        from rebuild_standard_index import build
        p = self.root / "references/quality-acceptance.md"
        p.write_bytes(p.read_bytes() + b"\nAdditional editorial guidance.\n")
        registry = build(self.root)
        self.assertEqual(registry["status"], "navigation_only")
        self.assertNotIn("rules", registry)
        self.assertNotIn("failure_contracts", registry)
        self.edit("indexes/standard-coverage.json", lambda d: (d.clear(), d.update(registry)))
        self.assertEqual(m.check(self.root), [])

    def test_unsupported_profile_version_format_is_rejected(self):
        self.edit("config/series-profile.json", lambda d: d.update(version="latest"))
        self.errors("unsupported profile schema/version")

    def test_new_maintenance_version_does_not_require_validator_edit(self):
        self.edit("config/series-profile.json", lambda d: d.update(version="1.6.10"))
        self.assertEqual(m.check(self.root), [])

    def test_navigation_does_not_make_learning_candidates_mandatory(self):
        registry = json.loads((self.root / "indexes/standard-coverage.json").read_text())
        self.assertTrue(all("learning-candidates/" not in row["file"] for row in registry["sections"]))

    def test_art_and_feedback_sections_keep_canonical_owners(self):
        registry = json.loads((self.root / "indexes/standard-coverage.json").read_text())
        sections = {row["file"]: row for row in registry["sections"]}
        for file, owner, anchors in (
            ("references/production-checkpoints.md", "production", ("3-阶段推进与代表样", "逐段声画与图内文字对应")),
            ("references/visual-system.md", "visual", ("纯2d解释与真实素材",)),
            ("references/quality-acceptance.md", "quality", ("失败后的处理", "主体动态与长静帧")),
        ):
            with self.subTest(file=file):
                self.assertEqual(sections[file]["owner_id"], owner)
                self.assertTrue(set(anchors) <= set(sections[file]["anchors"]))

    def test_navigation_rebuild_cannot_hide_broken_cross_references(self):
        from rebuild_standard_index import build
        routes = (
            ("references/production-checkpoints.md", "quality-acceptance.md#失败后的处理"),
            ("references/quality-acceptance.md", "production-checkpoints.md#逐段声画与图内文字对应"),
            ("references/quality-acceptance.md", "production-checkpoints.md#3-阶段推进与代表样"),
            ("references/quality-acceptance.md", "#记录与技术检查"),
        )
        registry_path = self.root / "indexes/standard-coverage.json"
        original_registry = registry_path.read_bytes()
        for file, target in routes:
            with self.subTest(file=file, target=target):
                p = self.root / file
                original = p.read_bytes()
                self.assertIn(target.encode(), original)
                try:
                    broken = target.split("#", 1)[0] + "#missing-owner-anchor"
                    p.write_bytes(original.replace(target.encode(), broken.encode()))
                    registry_path.write_text(json.dumps(build(self.root), ensure_ascii=False), encoding="utf-8")
                    self.errors("broken heading link")
                finally:
                    p.write_bytes(original)
                    registry_path.write_bytes(original_registry)
        self.assertEqual(m.check(self.root), [])

    def test_navigation_path_cannot_escape_skill(self):
        self.edit("indexes/rule-owners.json", lambda d: d["owners"][0].update(file="../../outside.md"))
        self.assertTrue(m.check(self.root))

    def test_deleted_subject_motion_section_requires_reviewed_index_update(self):
        p = self.root / "references/quality-acceptance.md"
        original = p.read_bytes()
        p.write_bytes(original.replace("## 主体动态与长静帧".encode(), b"## Deleted section"))
        self.errors("stale/incomplete chapter navigation")


if __name__ == "__main__":
    unittest.main()
