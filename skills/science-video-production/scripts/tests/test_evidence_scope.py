"""Synthetic viewing-scope contracts; never actual media or comprehension approval."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import subject_motion as motion
from stage_checks import Checks, context_sha256


class EvidenceScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        media = self.root / "synthetic.bin"
        media.write_bytes(b"Synthetic fixture, not playable or reviewed media")
        self.sha = motion.sha(media)
        self.screen = {"duration": 4, "regions": [], "low_motion_ranges": []}
        path = self.root / "screen.json"
        path.write_text(json.dumps(self.screen), encoding="utf-8")
        self.screen_ref = {"file": path.name, "sha256": motion.sha(path)}
        self.data = {"workflow_version": 2, "qa": {"gates": {
            gate: {"evidence": [self.screen_ref]} for gate in ("G2", "G3", "G5")}}}
        self.viewing = {
            "file": media.name, "sha256": self.sha, "reviewer": "Synthetic actual reviewer",
            "capability": "Synthetic declared playback capability; not actual viewing",
            "reviewed_at": "2026-01-01", "note": "Synthetic object recognized and state change followed",
            "scope": "representative", "method": "continuous_playback", "playback_speed": 1,
            "watched": True, "heard": True, "duration": 4, "ranges": [[0, 4]],
        }
        self.record = {
            "status": "pass", "media_sha256": self.sha, "screen": self.screen_ref,
            "roi_review": "Synthetic object ROI, inspected separately after continuous viewing",
            "excluded_motion_review": {k: "Synthetic exclusion only" for k in motion.IGNORED},
            "spans": [{"start": 0, "end": 4, "kind": "subject_change", "subject": "Synthetic object",
                       "observation": "Synthetic changing state", "narration_relation": "Synthetic relation",
                       "evidence": "Synthetic current-media interval only"}],
            "semantic_units": [{"start": 0, "end": 4, "step_ids": ["S1"],
                                "spoken_point": "Synthetic point", "progression_observed": "Synthetic state change",
                                "evidence": "Synthetic interval, not actual viewing"}],
            "longest_no_progress_seconds": 0, "screen_resolutions": [],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def errors(self, gate="G3"):
        checks = Checks(self.data, self.root)
        self.record["context_sha256"] = context_sha256(self.data, gate)
        # Reuse the public workflow's existing viewing and motion validators.
        # Media decoding alone is stubbed; file existence, JSON and hashes are real.
        with patch.object(checks, "duration", return_value=4), \
                patch.object(motion, "screen", return_value=self.screen):
            checks.viewing(self.viewing, gate + " viewing", self.viewing["scope"])
            motion.validate(checks, self.record, self.viewing, gate,
                            {"screen": {}, "max_no_progress_seconds": 3}, {"S1"})
        return checks.errors

    def diagnostic(self):
        return {"status": "pass", "media_sha256": self.sha, "units": [{
            "start": 0, "end": 4, "step_ids": ["S1"], "status": "pass", "mode": "visible_result",
            "subject": "Synthetic physical object", "overlay_isolation": "Synthetic labels hidden, object retained",
            "method": "frame_samples", "frame_scope": "roi_only",
            "observation": "Synthetic local state difference only",
            "scientific_boundary": "Synthetic local inspection does not prove original full-frame visibility",
            "evidence": "Synthetic object ROI times only"}]}

    def test_existing_records_without_new_fields_remain_compatible(self):
        self.assertEqual(self.errors(), [])
        self.data.pop("workflow_version")
        self.assertEqual(self.errors(), [])

    def test_explicit_full_frame_capable_viewing_is_structurally_valid_in_existing_gates(self):
        self.viewing.update(frame_scope="full_frame", visual_review_capable=True)
        self.data["workflow_version"] = 3
        self.record["object_result_review"] = self.diagnostic()
        for gate, scope in (("G2", "full_roughcut"), ("G3", "representative"), ("G5", "full_episode")):
            self.viewing["scope"] = scope
            self.assertEqual(self.errors(gate), [])

    def test_each_new_field_can_be_supplied_independently(self):
        for key, value in (("frame_scope", "full_frame"), ("visual_review_capable", True)):
            self.viewing[key] = value
            self.assertEqual(self.errors(), [])
            self.viewing.pop(key)

    def test_roi_only_viewing_cannot_sign_full_frame_under_subject_pass(self):
        self.viewing.update(frame_scope="roi_only", visual_review_capable=True)
        errors = self.errors()
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("declared viewing frame_scope", errors[0])

    def test_unknown_or_malformed_frame_scope_cannot_be_pass(self):
        for value in (None, "pending", "unknown", "", True, [], {}, ["full_frame", "roi_only"]):
            with self.subTest(value=value):
                self.viewing["frame_scope"] = value
                self.assertTrue(any("declared viewing frame_scope" in e for e in self.errors()))

    def test_unavailable_unknown_or_malformed_actual_reviewer_capability_rejected(self):
        for value in (False, None, "pending", "unknown", "true", 1, [], {}):
            with self.subTest(value=value):
                self.viewing["visual_review_capable"] = value
                self.assertTrue(any("visual capability" in e for e in self.errors()))

    def test_existing_method_contract_still_rejects_still_samples_and_contact_sheets(self):
        self.viewing.update(frame_scope="full_frame", visual_review_capable=True)
        for method in ("still_frames", "frame_samples", "contact_sheet", None, "unknown"):
            self.viewing["method"] = method
            self.assertTrue(any("normal-speed continuous playback required" in e for e in self.errors()))

    def test_existing_speed_contract_still_rejects_non_normal_and_malformed_speeds(self):
        for speed in (0, .5, 2, True, None, "1", float("nan"), float("inf")):
            self.viewing["playback_speed"] = speed
            self.assertTrue(any("normal-speed continuous playback required" in e for e in self.errors()))

    def test_positive_fields_do_not_replace_actual_watch_and_listen_declarations(self):
        self.viewing.update(frame_scope="full_frame", visual_review_capable=True)
        for key in ("watched", "heard"):
            self.viewing[key] = False
            self.assertTrue(any("actual viewing and listening required" in e for e in self.errors()))
            self.viewing[key] = True

    def test_positive_fields_do_not_expand_temporal_coverage(self):
        self.viewing.update(frame_scope="full_frame", visual_review_capable=True, ranges=[[0, 1]])
        self.assertTrue(any("full evidence clip must actually be covered" in e for e in self.errors()))

    def test_positive_fields_do_not_refresh_stale_media(self):
        self.viewing.update(frame_scope="full_frame", visual_review_capable=True, sha256="b" * 64)
        errors = self.errors()
        self.assertTrue(any("evidence hash stale" in e for e in errors))
        self.assertTrue(any("stale media" in e for e in errors))

    def test_separate_local_diagnostic_is_allowed_after_full_frame_viewing(self):
        self.viewing.update(frame_scope="full_frame", visual_review_capable=True)
        self.viewing["diagnostics"] = [{"method": "frame_samples", "frame_scope": "roi_only"}]
        self.record["object_result_review"] = self.diagnostic()
        self.assertEqual(self.errors(), [])

    def test_capable_user_observation_does_not_inherit_another_agents_limits(self):
        self.viewing.update(frame_scope="full_frame", visual_review_capable=True, reviewer="Synthetic capable user")
        self.data["qa"]["explanation_review"] = {
            "status": "pending", "reviewer": "Synthetic other agent", "visual_review_capable": False}
        self.assertEqual(self.errors(), [])  # Only these validators, not complete G5 approval.

    def test_detailed_prose_cannot_override_explicit_roi_only(self):
        self.viewing.update(frame_scope="roi_only", note="Synthetic prose claims full-frame causal clarity")
        self.assertTrue(any("declared viewing frame_scope" in e for e in self.errors()))

    def test_pending_candidate_is_not_mutated_into_pass_or_observed_slideshow(self):
        self.record["status"] = "pending"
        self.viewing.update(watched=False, method="frame_samples", frame_scope="roi_only", visual_review_capable=False)
        before = copy.deepcopy(self.viewing)
        errors = self.errors()
        self.assertTrue(errors)  # Producing a candidate does not authorize signing these reviews.
        self.assertEqual(self.viewing, before)
        self.assertEqual(self.record["status"], "pending")
        self.assertFalse(any("slideshow" in e for e in errors))

    def test_unknown_observation_does_not_erase_a_known_failure(self):
        self.record["status"] = "fail"
        self.viewing.update(frame_scope="unknown", visual_review_capable=None)
        self.data["qa"]["visual_frames"] = {"status": "fail", "failures": [{
            "id": "synthetic-known-failure", "status": "open", "scope": "segment",
            "note": "Synthetic prior full-frame relationship not readable"}]}
        before = copy.deepcopy(self.data)
        self.assertTrue(any("failed/unreviewed" in e for e in self.errors()))
        checks = Checks(self.data, self.root)
        checks.expansion_failures(True)
        self.assertTrue(any("blocks expansion" in e for e in checks.errors))
        self.assertEqual(self.data, before)

    def test_missing_screen_does_not_hide_explicit_viewing_scope_contradiction(self):
        self.record["screen"] = {}
        self.viewing["frame_scope"] = "roi_only"
        self.assertTrue(any("declared viewing frame_scope" in e for e in self.errors()))


if __name__ == "__main__":
    unittest.main()
