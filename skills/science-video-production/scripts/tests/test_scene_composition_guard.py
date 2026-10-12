"""Synthetic record regressions only; no private media or perceptual approval."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import subject_motion as motion
from feedback_guard import validate_feedback
from stage_checks import Checks, context_sha256


class SceneCompositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.data = {"workflow_version": 3, "qa": {"visual_frames": {"status": "pending", "failures": []}}}
        self.media_sha = "a" * 64
        self.units = [{"start": 0, "end": 4, "step_ids": ["S1"]}]
        self.review = {"status": "pass", "media_sha256": self.media_sha, "units": [
            {"start": 0, "end": 4, "step_ids": ["S1"], "status": "pass", "mode": "visible_result",
             "subject": "Synthetic physical test object with unchanged background",
             "overlay_isolation": "Synthetic diagnostic: extra labels and scale overlay temporarily hidden; full object retained in ROI",
             "observation": "Synthetic declaration: shape state and contact result visible without the scale overlay",
             "scientific_boundary": "Unchanged environment allowed; temperature is a diagram variable, not visible colored material",
             "evidence": "Synthetic current-media object ROI 0–4 s, not an actual review"}]}
        self.record = {"object_result_review": self.review}

    def tearDown(self):
        self.tmp.cleanup()

    def errors(self):
        checks = Checks(self.data, self.root)
        motion.validate_object_results(checks, self.record, self.units, self.media_sha, "G3 ")
        return checks.errors

    def test_current_structural_record_with_static_environment_allowed(self):
        self.assertEqual(self.errors(), [])

    def test_invisible_mechanism_diagram_with_reason_allowed(self):
        self.review["units"][0].update(mode="diagram_only", diagram_only_reason="Synthetic invisible variable comparison; no visible material change claimed", observation="Synthetic diagram relationships inspected after restoring necessary mechanism graphics")
        self.assertEqual(self.errors(), [])

    def test_diagram_mode_does_not_excuse_missing_scientific_boundary_or_reason(self):
        row = self.review["units"][0]
        row["mode"] = "diagram_only"
        self.assertTrue(any("reason required" in e for e in self.errors()))
        row["diagram_only_reason"] = "Synthetic invisible variable"
        row["scientific_boundary"] = "pending"
        self.assertTrue(any("scientific_boundary" in e for e in self.errors()))

    def test_legacy_packet_without_diagnostic_compatible(self):
        self.record = {}
        for version in (2, "absent"):
            if version == "absent":
                self.data.pop("workflow_version", None)
            else:
                self.data["workflow_version"] = version
            self.assertEqual(self.errors(), [])

    def test_current_template_cannot_delete_required_diagnostic(self):
        self.record = {}
        self.assertTrue(any("diagnostic required" in e for e in self.errors()))

    def test_explicit_null_and_empty_diagnostic_do_not_use_legacy_escape(self):
        for version in (2, 3):
            self.data["workflow_version"] = version
            for value in (None, {}, [], "pending"):
                self.record["object_result_review"] = value
                self.assertTrue(self.errors(), (version, value))

    def test_invalid_workflow_versions_fail_closed(self):
        for value in (None, True, "3", 0, 4, float("nan"), []):
            self.data["workflow_version"] = value
            self.assertTrue(any("workflow_version" in e for e in self.errors()), value)

    def test_new_workflow_context_changes_on_downgrade(self):
        current = {gate: context_sha256(self.data, gate) for gate in ("G2", "G3", "G5")}
        self.data["workflow_version"] = 2
        for gate in current:
            self.assertNotEqual(current[gate], context_sha256(self.data, gate))

    def test_legacy_context_binding_is_unchanged(self):
        self.data["workflow_version"] = 2
        before = context_sha256(self.data, "G3")
        self.data.pop("workflow_version")
        self.assertEqual(before, context_sha256(self.data, "G3"))

    def test_stale_media_fails(self):
        self.review["media_sha256"] = "b" * 64
        self.assertTrue(any("stale media" in e for e in self.errors()))

    def test_top_level_and_nested_unreviewed_status_fail(self):
        for target in (self.review, self.review["units"][0]):
            for status in ("pending", "fail", None):
                target["status"] = status
                self.assertTrue(self.errors())
            target["status"] = "pass"

    def test_missing_or_duplicate_semantic_units_fail(self):
        original = copy.deepcopy(self.review["units"])
        for value in (None, [], original * 2):
            self.review["units"] = value
            self.assertTrue(self.errors())

    def test_mismatched_time_or_steps_fail(self):
        for key, value in (("start", 1), ("end", 5), ("step_ids", ["S2"]), ("step_ids", ["S1", "S1"])):
            original = copy.deepcopy(self.review["units"][0])
            self.review["units"][0][key] = value
            self.assertTrue(self.errors())
            self.review["units"][0] = original

    def test_nonfinite_boolean_and_malformed_ranges_fail_without_crash(self):
        for value in (None, True, "0", float("nan"), 10**1000, []):
            self.review["units"][0]["start"] = value
            self.assertTrue(self.errors())

    def test_missing_unknown_modes_fail(self):
        for value in (None, "label_only", "static_environment", "not_applicable", ""):
            self.review["units"][0]["mode"] = value
            self.assertTrue(self.errors())

    def test_placeholder_and_structured_pending_evidence_rejected(self):
        row = self.review["units"][0]
        for key in ("subject", "overlay_isolation", "observation", "scientific_boundary", "evidence"):
            original = row[key]
            for value in ("pending", " 待审 ", "", None, {"status": "pending", "note": "synthetic"}):
                row[key] = value
                self.assertTrue(self.errors(), (key, value))
            row[key] = original

    def test_legacy_opt_in_diagnostic_still_validated(self):
        self.data["workflow_version"] = 2
        self.review["status"] = "pending"
        self.assertTrue(self.errors())

    def test_optional_local_polish_note_is_not_invented_as_a_failure(self):
        self.data["qa"]["visual_frames"]["review_notes"] = [{"severity": "P2", "status": "optional", "note": "Synthetic optional edge polish; no failed quality dimension or user rejection"}]
        checks = Checks(self.data, self.root)
        checks.expansion_failures(True)
        self.assertEqual(checks.errors, [])

    def test_p2_known_visual_failure_still_blocks_expansion(self):
        self.data["qa"]["visual_frames"]["failures"] = [{"id": "synthetic-F1", "scope": "segment", "severity": "P2", "note": "Synthetic same-shot benchmark gap: detailed assets remain an incoherent collage", "status": "open"}]
        self.data["qa"]["comprehension"] = {"status": "audience_checked"}
        checks = Checks(self.data, self.root)
        checks.expansion_failures(False)
        self.assertEqual(checks.errors, [])
        checks.expansion_failures(True)
        self.assertTrue(any("blocks expansion" in e for e in checks.errors))

    def test_p2_renaming_cannot_clear_failed_art_dimension(self):
        self.data["qa"]["visual_frames"]["art"] = {"status": "fail", "severity": "P2"}
        checks = Checks(self.data, self.root)
        checks.expansion_failures(True)
        self.assertTrue(any("blocks expansion" in e for e in checks.errors))

    def test_explicit_user_art_rejection_labeled_p2_still_blocks(self):
        self.data["qa"]["feedback"] = [{"contract_version": 1, "feedback_id": "synthetic-feedback", "origin": "user", "severity": "P2", "source_ref": "synthetic-source", "received_at": "2026-01-01", "original_feedback": "Synthetic feedback: clear explanation, visibly rough scene", "media_version": "synthetic-v1", "media_sha256": self.media_sha, "scope": "test sample", "scope_kind": "segment", "time_range_s": [0, 4], "applies_to_gates": ["G3"], "dimensions": {"comprehension": {"status": "pass", "note": "Synthetic relation recognized"}, "art": {"status": "fail", "note": "Synthetic user rejection of scene target"}}, "status": "candidate", "what_changes": "Repair coherent scene before extension", "skill_update": {"disposition": "execution_fix", "proposed_change": "Apply existing art rules", "status": "pending"}}]
        checks = Checks(self.data, self.root)
        validate_feedback(checks, "G3", expanding=True)
        self.assertTrue(any("unresolved failed dimensions block expansion" in e for e in checks.errors))

    def test_guard_is_called_by_existing_subject_motion_validation(self):
        # Stub only decoder/pacing dependencies; this tests record integration,
        # never actual motion, pacing, art or audiovisual acceptance.
        media = self.root / "synthetic.bin"
        media.write_bytes(b"synthetic bytes, not media")
        sha = hashlib.sha256(media.read_bytes()).hexdigest()
        report = {"duration": 4, "regions": [], "low_motion_ranges": []}
        report_path = self.root / "screen.json"
        report_path.write_text(json.dumps(report))
        ref = {"file": report_path.name, "sha256": motion.sha(report_path)}
        self.data["qa"]["gates"] = {"G3": {"evidence": [ref]}}
        record = {"status": "pass", "context_sha256": context_sha256(self.data, "G3"), "media_sha256": sha,
                  "roi_review": "Synthetic complete object ROI", "excluded_motion_review": {k: "Synthetic exclusion reviewed" for k in motion.IGNORED}, "screen": ref,
                  "spans": [{"start": 0, "end": 4, "kind": "subject_change", "subject": "Synthetic object", "observation": "Synthetic changing state", "narration_relation": "Synthetic relation", "evidence": "Synthetic time range"}],
                  "semantic_units": [dict(self.units[0], spoken_point="Synthetic point", progression_observed="Synthetic transition", evidence="Synthetic times")],
                  "longest_no_progress_seconds": 0, "screen_resolutions": []}
        checks = Checks(self.data, self.root)
        with patch.object(motion, "screen", return_value=report), patch.object(motion, "validate_pacing", create=True):
            motion.validate(checks, record, {"file": media.name, "sha256": sha}, "G3", {"screen": {}, "max_no_progress_seconds": 3}, {"S1"})
        self.assertEqual(checks.errors, ["stage: G3 subject motion object result diagnostic required; null/omission is not a current review"])

    def test_new_template_declares_workflow3_and_pending_all_stage_diagnostics(self):
        root = Path(motion.__file__).resolve().parents[1]
        data = json.loads((root / "assets/episode-template.json").read_text())
        self.assertEqual(data["workflow_version"], 3)
        for parent in (data["qa"]["shotbook"], data["qa"]["visual_frames"]["animation"], data["qa"]["visual_frames"]):
            self.assertEqual(parent["subject_motion"]["object_result_review"], {"status": "pending", "media_sha256": "", "units": []})

    def test_owner_reference_clauses_are_present_and_bound(self):
        from check_reference_system import check
        root = Path(motion.__file__).resolve().parents[1]
        self.assertEqual(check(root), [])
        registry = json.loads((root / "indexes/standard-coverage.json").read_text())
        contracts = {c["id"]: c for c in registry["failure_contracts"]}
        cases = [("field-art", "精细独立资产合成后仍可能像拼贴"), ("V-feedback_issue", "关键美术失败"), ("MOTION-subject-continuity-failure", "在上述主体ROI复查中，另做对象结果诊断")]
        for ident, prefix in cases:
            found = [c for c in contracts[ident]["clauses"] if c["quote"].startswith(prefix)]
            self.assertEqual(len(found), 1)
            clause = found[0]
            self.assertIn(clause["quote"], (root / clause["file"]).read_text())
            self.assertEqual(hashlib.sha256(clause["quote"].encode()).hexdigest(), clause["quote_sha256"])


if __name__ == "__main__":
    unittest.main()
