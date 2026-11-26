#!/usr/bin/env python3
"""Behavioral regression tests for the reference/config/catalog contract."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from tests.reference_overlay import ReferenceOverlay

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("reference_checks", ROOT / "scripts/check_reference_system.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReferenceSystemTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT
        self.enterContext(ReferenceOverlay(ROOT))
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
    def test_indextts2_private_paths_cannot_be_hardcoded_in_public_profile(self):
        self.edit("config/series-profile.json", lambda d: d["audio"]["indextts2"].update(project_dir="/private/indextts2"))
        self.errors("private local paths")
    def test_indextts2_drive_literal_path_cannot_leak_into_public_profile(self):
        self.edit("config/series-profile.json", lambda d: d["audio"]["indextts2"].update(reference_prompt_policy="D:\\private\\prompt.wav"))
        self.errors("private local paths")
    def test_speech_polish_preset_must_not_enable_echo(self):
        self.edit("config/series-profile.json", lambda d: d["audio"]["speech_polish_preset"].update(echo="room"))
        self.errors("speech polish")
    def test_aesthetic_average_cannot_replace_dimension_completion(self):
        self.edit("config/production-policy.json", lambda d: d["quality"]["finesse"].update(no_average_override=False))
        self.errors("independent dimension target")
    def test_external_sources_are_immutable(self):
        self.edit("indexes/external-skills.json", lambda d: d["entries"][0].update(commit="main"))
        self.errors("immutable commit")
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
    def test_real_video_required(self):
        self.edit("config/series-profile.json", lambda d: d["medium"].update(real_anchor="photo"))
        self.errors("real video")
    def test_reference_not_media_license(self):
        self.edit("indexes/aesthetic-references.json", lambda d: d["entries"][0].update(production_use="granted"))
        self.errors("does not grant")
    def test_palette_path_cannot_escape_the_skill(self):
        self.edit("config/series-profile.json", lambda d: d["design"]["lighting_material_standard"].update(palette_start_points="../../outside.json"))
        self.errors("path escapes Skill")
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
        self.edit("config/series-profile.json", lambda d: d["design"]["lighting_material_standard"].update(material_identity_and_scientific_colors_preserved=False))
        self.errors("science colors")
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
            ("references/production-checkpoints.md", "production", ("3-stage-progression-and-representative-samples", "match-each-sections-picture-sound-and-in-picture-text")),
            ("references/visual-system.md", "visual", ("pure-2d-explanation-and-real-assets",)),
            ("references/quality-acceptance.md", "quality", ("handling-failures", "subject-motion-and-long-static-holds")),
        ):
            with self.subTest(file=file):
                self.assertEqual(sections[file]["owner_id"], owner)
                self.assertTrue(set(anchors) <= set(sections[file]["anchors"]))

    def test_navigation_rebuild_cannot_hide_broken_cross_references(self):
        from rebuild_standard_index import build
        routes = (
            ("references/production-checkpoints.md", "quality-acceptance.md#handling-failures"),
            ("references/quality-acceptance.md", "production-checkpoints.md#match-each-sections-picture-sound-and-in-picture-text"),
            ("references/quality-acceptance.md", "production-checkpoints.md#3-stage-progression-and-representative-samples"),
            ("references/quality-acceptance.md", "#autonomous-explanation-and-expression-review"),
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
        p.write_bytes(original.replace("## Subject Motion and Long Static Holds".encode(), b"## Deleted section"))
        self.errors("stale/incomplete chapter navigation")

    def test_google_flow_audit_cannot_reintroduce_episode_duration_floor(self):
        self.edit("config/production-policy.json", lambda d: d["google_flow_audit"].update(narrative_depth={"min_episode_duration_s": 135.0}))
        self.errors("must not impose mandatory episode duration")

    def test_editorial_positioning_must_preserve_user_commissioned_topics(self):
        self.edit("config/series-profile.json", lambda d: d["editorial_positioning"].update(preserves_user_commissioned_topics=False))
        self.errors("preserve user-commissioned topics")

    def test_publication_spacing_requires_positive_gap(self):
        self.edit("config/series-profile.json", lambda d: d["operations"]["publication_spacing"].update(recommended_min_gap_hours=0))
        self.errors("publication spacing guidance")

    def test_douyin_collections_require_publish_assignment(self):
        self.edit("config/series-profile.json", lambda d: d["operations"]["douyin_collections"].update(require_collection_at_publication=False))
        self.errors("douyin_collections standing taxonomy")

    def test_douyin_collections_require_four_ordered_standing_collections(self):
        self.edit("config/series-profile.json", lambda d: d["operations"]["douyin_collections"]["collections"].pop())
        self.errors("four ordered standing collections")

    def test_colab_cli_catalog_and_canonical_routing_stay_linked(self):
        external = json.loads((self.root / "indexes/external-skills.json").read_text(encoding="utf-8"))
        entries = {row["id"]: row for row in external["entries"]}
        self.assertIn("google-colab-cli", entries)
        colab_entry = entries["google-colab-cli"]
        self.assertEqual(colab_entry["execution"]["routing_reference"], "references/tool-routing.md#colab-cli-and-remote-gpu-integration")
        self.assertTrue((self.root / "scripts/colab_cli.py").is_file())
        profile = json.loads((self.root / "config/series-profile.json").read_text(encoding="utf-8"))
        td = profile["video_generation"]["style_routing"]["three_d_animation"]
        self.assertEqual(td["blender_render_compute_policy"], "colab_first_with_local_fallback")
        self.assertEqual(td["blender_colab_entrypoint"], "scripts/colab_cli.py blender-render")
        self.assertEqual(td["colab_default_visual_style"], "high_poly_industrial_3d")
        self.assertEqual(td["colab_modeling_standard"], "high_poly_industrial_v1")
        self.assertEqual(
            td["colab_3d_default"]["modeling_guide"],
            "references/engineering-blender.md#high-poly-industrial-modeling-standard-for-colab-3d",
        )
        registry = json.loads((self.root / "indexes/standard-coverage.json").read_text(encoding="utf-8"))
        sections = {row["file"]: row for row in registry["sections"]}
        self.assertEqual(sections["references/tool-routing.md"]["owner_id"], "tools")
        self.assertIn("colab-cli-and-remote-gpu-integration", sections["references/tool-routing.md"]["anchors"])
        self.assertIn(
            "default-colab-3d-modeling-and-visual-style-high-poly-industrial",
            sections["references/tool-routing.md"]["anchors"],
        )
        self.assertIn(
            "high-poly-industrial-modeling-standard-for-colab-3d",
            sections["references/engineering-blender.md"]["anchors"],
        )

    def test_gemini_api_cli_catalog_and_google_flow_routing_stay_linked(self):
        external = json.loads((self.root / "indexes/external-skills.json").read_text(encoding="utf-8"))
        entries = {row["id"]: row for row in external["entries"]}
        self.assertIn("google-gemini-api-cli", entries)
        cli_entry = entries["google-gemini-api-cli"]
        self.assertEqual(cli_entry["repository"], "https://github.com/google-gemini/gemini-api-cli")
        self.assertEqual(
            cli_entry["execution"]["routing_reference"],
            "references/google-flow-production.md#gemini-api-cli-headless-cloud-execution",
        )
        self.assertTrue((self.root / "scripts/gemini_api_cli.py").is_file())
        profile = json.loads((self.root / "config/series-profile.json").read_text(encoding="utf-8"))
        cloud = profile["video_generation"]["cloud_route"]
        self.assertIn("gemini_api_cli", cloud["execution_modes"])
        self.assertIn("google_flow_web", cloud["execution_modes"])
        gcli = cloud["gemini_api_cli"]
        self.assertEqual(gcli["source_id"], "google-gemini-api-cli")
        self.assertEqual(gcli["cli_helper"], "scripts/gemini_api_cli.py")
        self.assertEqual(gcli["default_video_resolution"], "1080p")
        self.assertEqual(
            gcli["guide"],
            "references/google-flow-production.md#gemini-api-cli-headless-cloud-execution",
        )
        registry = json.loads((self.root / "indexes/standard-coverage.json").read_text(encoding="utf-8"))
        sections = {row["file"]: row for row in registry["sections"]}
        self.assertEqual(sections["references/google-flow-production.md"]["owner_id"], "google-flow")
        self.assertIn(
            "gemini-api-cli-headless-cloud-execution",
            sections["references/google-flow-production.md"]["anchors"],
        )

    def test_gemini_api_cli_default_video_resolution_cannot_drop_to_720p(self):
        self.edit(
            "config/series-profile.json",
            lambda d: d["video_generation"]["cloud_route"]["gemini_api_cli"].update(default_video_resolution="720p"),
        )
        self.errors("gemini_api_cli helper")

    def test_colab_high_poly_segment_floor_cannot_be_weakened(self):
        self.edit(
            "config/series-profile.json",
            lambda d: d["video_generation"]["style_routing"]["three_d_animation"]["colab_3d_default"]["geometry_standards"].update(
                hero_cylinder_min_segments=16
            ),
        )
        self.errors("high_poly_industrial_3d")

    def test_colab_modeling_screening_cannot_claim_visual_acceptance(self):
        self.edit(
            "config/series-profile.json",
            lambda d: d["video_generation"]["style_routing"]["three_d_animation"]["colab_3d_default"]["geometry_standards"].update(
                screening_is_not_visual_acceptance=False
            ),
        )
        self.errors("high_poly_industrial_3d")

    def test_colab_oidn_albedo_normal_pass_cannot_be_dropped(self):
        self.edit(
            "config/series-profile.json",
            lambda d: d["video_generation"]["style_routing"]["three_d_animation"]["colab_3d_default"]["cycles_defaults"].update(
                denoising_input_passes="RGB"
            ),
        )
        self.errors("high_poly_industrial_3d")

    def test_v2_visual_first_and_anti_void_anti_box_gates_cannot_be_weakened(self):
        for field, bad_val in (
            ("workflow_order", "script_first"),
            ("require_strict_audit_blend", False),
            ("require_real_host_in_cutaways", False),
            ("ban_void_backdrop_planes", False),
            ("ban_primitive_box_hero_substitutes", False),
            ("ban_blind_contextless_macro_slivers", False),
            ("ban_legacy_episode_template_reuse", False),
        ):
            with self.subTest(field=field):
                self.edit(
                    "config/series-profile.json",
                    lambda d, k=field, v=bad_val: d["video_generation"]["style_routing"]["three_d_animation"]["colab_3d_default"].update({k: v}),
                )
                self.errors("high_poly_industrial_3d")
                # restore via ReferenceOverlay isolation on next subTest? No — edit persists inside same test method!
                # Reset cleanly after each assertion:
                self.edit(
                    "config/series-profile.json",
                    lambda d, k=field: d["video_generation"]["style_routing"]["three_d_animation"]["colab_3d_default"].update(
                        {k: "silent_visual_causality_first" if k == "workflow_order" else True}
                    ),
                )

    def test_lighting_background_value_cannot_restore_black_void_backdoor(self):
        self.edit(
            "config/series-profile.json",
            lambda d: d["design"]["lighting_material_standard"].update(background_value="light_mid_dark_or_black_allowed"),
        )
        self.errors("ban flat void backdrops")

    def test_google_flow_route_isolation_excludes_moneyprinter_and_vork(self):
        skill = (self.root / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1]
        self.assertNotIn("MoneyPrinterTurbo", frontmatter)
        self.assertNotIn("vork", frontmatter.lower())
        self.assertIn("## Route isolation (load only the active route)", skill)
        self.assertIn("Never load", skill)
        flow_reachable = (
            "references/google-flow-production.md",
            "references/voice-reference.md",
            "references/viral-appeal-and-packaging.md",
            "references/realistic-direction.md",
            "references/topic-contract.md",
            "references/viewer-retention-design.md",
            "references/production-checkpoints.md",
            "references/quality-acceptance.md",
            "references/visual-system.md",
            "references/science-and-rights.md",
            "references/shotbook.md",
            "references/subagent-orchestration.md",
        )
        for rel in flow_reachable:
            text = (self.root / rel).read_text(encoding="utf-8")
            with self.subTest(file=rel):
                self.assertNotIn("MoneyPrinterTurbo", text)
                self.assertNotRegex(text, r"(?i)\bvork\b")
                self.assertNotRegex(text, r"\]\([^)]*tool-routing\.md")
                self.assertNotRegex(text, r"\]\([^)]*ai-generated-video\.md")
        for toml in sorted((self.root / "agents").glob("*.toml")):
            text = toml.read_text(encoding="utf-8")
            with self.subTest(agent=toml.name):
                self.assertIn("Route Isolation gate", text)
                self.assertIn("google_flow", text)
                self.assertNotIn("MoneyPrinterTurbo", text)
                self.assertNotRegex(text, r"(?i)\bvork\b")

    def test_proprietary_feed_font_candidate_is_rejected(self):
        self.edit("config/production-policy.json", lambda d: d["feed_package"]["font_candidates"].append("C:/Windows/Fonts/msyhbd.ttc"))
        self.errors("non-proprietary fonts only")

    def test_proprietary_en_cover_font_is_rejected(self):
        self.edit("config/production-policy.json", lambda d: d["cover_typography"]["fonts"]["en"].update(family="Segoe UI", candidates=["C:/Windows/Fonts/segoeuib.ttf"]))
        self.errors("without proprietary fonts")

    def test_proprietary_annotation_token_font_is_rejected(self):
        self.edit("assets/style/precision-annotations.tokens.json", lambda d: d["type"]["fallbacks"].append("Microsoft YaHei"))
        self.errors("must not reference proprietary fonts")

    def test_proprietary_annotation_svg_font_is_rejected(self):
        p = self.root / "assets/style/leader-and-arrow.svg"
        p.write_text(p.read_text(encoding="utf-8").replace("Noto Sans SC", "Microsoft YaHei"), encoding="utf-8")
        self.errors("must not reference proprietary fonts")


if __name__ == "__main__":
    unittest.main()
