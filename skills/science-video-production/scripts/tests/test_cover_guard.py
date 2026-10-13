"""Synthetic evidence regressions; passing tests never approve real covers."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cover_guard import OBSERVATIONS, validate_cover_review, image_size
_spec = importlib.util.spec_from_file_location("synthetic_cover_fixture", Path(__file__).with_name("cover_fixture.py"))
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)
attach_cover_fixture, png, ref, save_cover_fixture = (_fixture.attach_cover_fixture, _fixture.png, _fixture.ref, _fixture.save_cover_fixture)
from stage_checks import Checks, context_sha256, check_stage
import check_episode


class CoverGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.data = {}; self.record = attach_cover_fixture(self.data, self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def errors(self, save=True):
        if save:
            save_cover_fixture(self.data, self.root, self.record)
        checks = Checks(self.data, self.root); validate_cover_review(checks)
        return checks.errors

    def row(self):
        return self.record["variants"]["cover_3_4"]

    def test_complete_synthetic_record_passes_structure_only(self):
        self.assertEqual(self.errors(), [])

    def test_legacy_missing_record_does_not_bypass(self):
        self.data["qa"]["covers"].pop("visual_review")
        self.assertTrue(any("visual review" in e for e in self.errors(False)))

    def test_g5_g6_g7_require_cover_evidence_without_standalone_command(self):
        self.data["qa"]["covers"].pop("visual_review")
        for gate in ("G5", "G6", "G7"):
            self.assertTrue(any("covers visual review" in e for e in check_stage(self.data, self.root, gate)), gate)

    def test_deleted_variant_fails(self):
        self.record["variants"].pop("cover_4_3")
        self.assertTrue(self.errors())

    def test_failed_or_pending_review_cannot_be_offset(self):
        for status in ("pending", "failed", "unviewed"):
            self.record["status"] = status
            self.assertTrue(self.errors())

    def test_missing_baseline_approval_trace_fails(self):
        self.record["baseline"].pop("approval_evidence")
        self.assertTrue(any("approval evidence" in e for e in self.errors()))

    def test_generic_style_reference_not_approved_cover_fails(self):
        self.record["baseline"]["kind"] = "generic_style_reference"
        self.assertTrue(self.errors())

    def test_approval_for_another_image_fails(self):
        self.record["baseline"]["approved_image_sha256"] = "b" * 64
        self.assertTrue(any("exact baseline" in e for e in self.errors()))

    def test_baseline_must_be_opened(self):
        self.record["baseline"]["actually_opened"] = False
        self.assertTrue(self.errors())

    def test_code_or_hash_only_review_fails(self):
        for method in ("code_only", "hashes_only", "automated_tests"):
            self.record["method"] = method
            self.assertTrue(self.errors())

    def test_same_producer_reviewer_fails(self):
        self.record["reviewer"] = " SYNTHETIC PRODUCER "
        self.assertTrue(any("independent reviewer" in e for e in self.errors()))

    def test_independence_declaration_required(self):
        self.record["independent_review"] = False
        self.assertTrue(self.errors())

    def test_review_timestamp_must_be_real_format_with_timezone(self):
        for stamp in ("yesterday", "2026-01-01T00:00:00", None):
            self.record["reviewed_at"] = stamp
            self.assertTrue(self.errors())

    def test_future_review_cannot_be_pre_signed(self):
        self.record["reviewed_at"] = "2999-01-01T00:00:00Z"
        self.assertTrue(any("future" in e for e in self.errors()))

    def test_mechanism_page_is_blocked(self):
        for kind in ("mechanism_page", "subtitle_capture", "slide"):
            self.row()["layout_kind"] = kind
            self.assertTrue(self.errors())

    def test_wrong_style_or_title_position_fails(self):
        for field, value in (("style", "flat_components"), ("title_position", "bottom_center")):
            old = self.row()[field]; self.row()[field] = value
            self.assertTrue(self.errors()); self.row()[field] = old

    def test_prohibited_elements_must_be_explicitly_clear(self):
        for value in (None, ["mechanism_arrows"], ["small_labels"], "none"):
            self.row()["prohibited_elements"] = value
            self.assertTrue(self.errors())

    def test_missing_title_question_or_subject_fails(self):
        for field in ("title", "question", "subject"):
            old = self.row()[field]; self.row()[field] = ""
            self.assertTrue(self.errors()); self.row()[field] = old

    def test_actual_opening_and_comparison_required_for_each_export(self):
        for field in ("actual_export_opened", "baseline_compared"):
            self.row()[field] = False
            self.assertTrue(self.errors()); self.row()[field] = True

    def test_actual_preview_and_comparison_opening_required(self):
        for field in ("mobile_preview", "comparison"):
            self.row()[field]["actually_opened"] = False
            self.assertTrue(self.errors()); self.row()[field]["actually_opened"] = True

    def test_each_required_observation_must_pass_and_describe_actual_result(self):
        for key in OBSERVATIONS:
            original = self.row()["observations"][key]
            for value in ({"status": "pending", "observation": "unviewed"}, {"status": "pass", "observation": "pass"}, {}):
                self.row()["observations"][key] = value
                self.assertTrue(self.errors(), key)
            self.row()["observations"][key] = original

    def test_updated_export_file_invalidates_saved_review(self):
        png(self.root / self.data["deliverables"]["cover_3_4"], 48, 64, (130, 0, 20))
        self.assertTrue(any("hash stale" in e for e in self.errors()))

    def test_same_check_same_path_changed_bytes_cannot_reuse_image_metadata(self):
        checks = Checks(self.data, self.root)
        path = self.root / "changing.png"
        png(path, 3, 4)
        self.assertEqual(image_size(checks, ref(self.root, path.name), "before"), (3, 4))
        png(path, 4, 3)
        self.assertEqual(image_size(checks, ref(self.root, path.name), "new shape"), (4, 3))
        path.write_text("not image")
        self.assertIsNone(image_size(checks, ref(self.root, path.name), "corrupt"))
        self.assertTrue(checks.errors)

    def test_export_hash_must_match_delivery_manifest(self):
        self.data["qa"]["reviewed_sha256"]["cover_3_4"] = "b" * 64
        self.assertTrue(any("export hash" in e for e in self.errors()))

    def test_updated_review_file_fails_without_ref_hash_update(self):
        (self.root / "synthetic-cover-review.json").write_text(json.dumps(self.record) + "\n")
        self.assertTrue(any("hash stale" in e for e in self.errors(False)))

    def test_wrong_export_ratio_fails(self):
        name = self.data["deliverables"]["cover_3_4"]; png(self.root / name, 64, 48)
        reference = ref(self.root, name); self.row()["export"] = reference
        self.data["qa"]["reviewed_sha256"]["cover_3_4"] = reference["sha256"]
        self.assertTrue(any("aspect ratio" in e for e in self.errors()))

    def test_text_disguised_as_image_fails(self):
        path = self.root / self.row()["comparison"]["file"]; path.write_text("not an image")
        self.row()["comparison"].update(ref(self.root, path.name))
        self.assertTrue(any("image" in e for e in self.errors()))

    def test_mobile_preview_must_bind_current_export(self):
        self.row()["mobile_preview"]["source_sha256"] = "b" * 64
        self.assertTrue(any("stale mobile" in e for e in self.errors()))

    def test_preview_requires_actual_phone_display_context(self):
        for field, value in (("display_width_px", 0), ("display_width_px", True), ("display_width_px", float("nan")), ("display_context", "full_resolution_desktop")):
            old = self.row()["mobile_preview"][field]; self.row()["mobile_preview"][field] = value
            self.assertTrue(self.errors()); self.row()["mobile_preview"][field] = old

    def test_stale_comparison_bindings_fail(self):
        for field in ("baseline_sha256", "export_sha256", "preview_sha256"):
            old = self.row()["comparison"][field]; self.row()["comparison"][field] = "b" * 64
            self.assertTrue(any("stale comparison" in e for e in self.errors()))
            self.row()["comparison"][field] = old

    def test_unsafe_path_is_rejected(self):
        self.record["baseline"]["approval_evidence"]["file"] = "/etc/passwd"
        self.assertTrue(any("unsafe" in e for e in self.errors()))

    def test_malformed_json_is_blocked(self):
        (self.root / "synthetic-cover-review.json").write_text("[")
        self.data["qa"]["covers"]["visual_review"] = ref(self.root, "synthetic-cover-review.json")
        self.assertTrue(any("JSON unreadable" in e for e in self.errors(False)))

    def test_cover_review_ref_changes_late_gate_context_only(self):
        before = {g: context_sha256(self.data, g) for g in ("G2", "G3", "G5", "G6", "G7")}
        self.record["baseline"]["approval_reference"] = "Another synthetic approval source"
        save_cover_fixture(self.data, self.root, self.record)
        for gate in ("G5", "G6", "G7"):
            self.assertNotEqual(before[gate], context_sha256(self.data, gate))
        for gate in ("G2", "G3"):
            self.assertEqual(before[gate], context_sha256(self.data, gate))

    def test_cover_only_check_does_not_require_movie_or_grant_movie_approval(self):
        errors, notes = check_episode.check(self.data, self.root, "covers")
        self.assertEqual(errors, []); self.assertIn("do not prove actual viewing", notes[0])

    def test_cover_only_cli_receipt_and_no_overwrite(self):
        episode = self.root / "episode.json"; episode.write_text(json.dumps(self.data))
        report = self.root / "cover-check.json"
        command = [sys.executable, str(Path(check_episode.__file__)), str(episode), "--stage", "covers", "--report", str(report)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads(report.read_text()); self.assertEqual(receipt["stage"], "covers")
        self.assertIn("scripts/cover_guard.py", receipt["validation_resources"])
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
