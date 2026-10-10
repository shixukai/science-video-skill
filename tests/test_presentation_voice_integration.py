"""Voice-plan/source integration fixtures; no synthesis or listening is claimed."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from stage_fixture import gates
import presentation_checks as presentation


class PresentationVoiceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="science-presentation-voice-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = {
            "schema_version": 1, "mode": "ordered_full_segments",
            "reason": {"kind": "contextual_retake", "note": "Synthetic defect record requiring a whole-context retake",
                       "evidence": self.file("reason.txt", "Synthetic defect evidence, no actual listening")},
            "segments": [
                {"id": ident, "input": self.file(ident + ".txt", "Synthetic input " + ident),
                 "output": self.file(ident + ".wav", "Opaque fixture only, not a playable or generated voice")}
                for ident in ("A", "B")],
        }
        self.manifest_ref = self.file("manifest.json", json.dumps(self.manifest))
        self.plan = {
            "mode": "context_preserving_segments", "generation_manifest": copy.deepcopy(self.manifest_ref),
            "target": {key: "Synthetic stable " + key for key in presentation.VOICE_CRITERIA - {"joins"}},
            "verified_method": "Synthetic whole-segment replacement method", "capability_evidence": "Synthetic method receipt",
            "context_handoff": "Synthetic continuing argument",
            "segments": [
                {"id": "A", "context_before": "opening premise", "context_after": "shared condition",
                 "handoff_evidence": "Synthetic A context receipt"},
                {"id": "B", "context_before": "shared condition", "context_after": "conclusion",
                 "handoff_evidence": "Synthetic B context receipt"},
            ],
        }
        self.data = {
            "narration": {"generation_manifest": copy.deepcopy(self.manifest_ref), "delivery_plan": self.plan,
                          "audio_sha256": "1" * 64},
            "shots": [{"id": "S1", "shotbook": {"start": 0, "end": 1}}],
            "qa": {"audio": {"continuity": {}}},
        }
        self.viewing = {"sha256": "2" * 64, "duration": 1, "ranges": [[0, 1]]}

    def file(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return {"file": name, "sha256": gates.file_digest(path)}

    def save_manifest(self):
        ref = self.file("manifest.json", json.dumps(self.manifest))
        self.data["narration"]["generation_manifest"] = ref
        self.plan["generation_manifest"] = copy.deepcopy(ref)

    def errors(self, gate="G5"):
        self.data["qa"]["audio"]["continuity"][gate] = {
            "status": "pass", "context_sha256": gates.context_sha256(self.data, gate),
            "media_sha256": self.viewing["sha256"], "audio_sha256": self.data["narration"]["audio_sha256"],
            "plan_sha256": gates.digest(self.plan), "method": "normal_speed_continuous_listening",
            "actually_heard": True, "reviewer": "Synthetic reviewer", "capability": "Synthetic capability",
            "evidence": "Synthetic review declaration only", "ranges": self.viewing["ranges"],
            "criteria": {key: {"status": "pass", "observation": "Synthetic " + key, "evidence": "Fixture only"}
                         for key in presentation.VOICE_CRITERIA}, "transitions": [],
        }
        checks = gates.Checks(self.data, self.root)
        presentation.validate_voice_continuity(checks, gate, self.viewing)
        return checks.errors

    def rejects(self, phrase):
        errors = self.errors()
        self.assertTrue(any(phrase in error for error in errors), errors)

    def test_contextual_retake_uses_bound_manifest_reason_without_fake_technical_limit(self):
        self.assertNotIn("technical_limit", self.plan)
        self.assertEqual(self.errors(), [])

    def test_manifest_cannot_be_hidden_by_continuous_first_mode(self):
        self.plan["mode"] = "continuous_first"
        for gate in ("G2", "G5"):
            with self.subTest(gate=gate):
                self.assertTrue(any("actual generation manifest requires" in error for error in self.errors(gate)))

    def test_plan_must_reference_same_manifest_file_and_hash(self):
        for ref in ({}, {"file": "other.json", "sha256": self.manifest_ref["sha256"]},
                    {"file": "manifest.json", "sha256": "0" * 64}):
            with self.subTest(ref=ref):
                self.plan["generation_manifest"] = ref
                self.rejects("must reference the current generation manifest")

    def test_segment_ids_order_omission_and_extra_rows_must_match_manifest(self):
        original = copy.deepcopy(self.plan["segments"])
        for rows in (list(reversed(original)), original[:1], original + [original[0]],
                     [{**original[0], "id": "unrelated"}, original[1]]):
            with self.subTest(rows=rows):
                self.plan["segments"] = rows
                self.rejects("must match generation manifest IDs and order")

    def test_optional_legacy_script_audio_refs_must_match_actual_manifest_sources(self):
        for row, source in zip(self.plan["segments"], self.manifest["segments"]):
            row.update(script=copy.deepcopy(source["input"]), audio=copy.deepcopy(source["output"]))
        self.assertEqual(self.errors(), [])
        for key in ("script", "audio", "input", "output"):
            with self.subTest(key=key):
                old = copy.deepcopy(self.plan["segments"][0])
                self.plan["segments"][0][key] = {"file": "B.txt", "sha256": "0" * 64}
                self.rejects("differs from generation manifest source/hash")
                self.plan["segments"][0] = old

    def test_manifest_source_file_hash_is_checked_when_plan_only_contains_context(self):
        (self.root / "A.txt").write_text("Changed source input", encoding="utf-8")
        self.rejects("evidence hash stale")

    def test_actual_reason_evidence_cannot_be_replaced_by_a_technical_limit_note(self):
        self.plan["technical_limit"] = "Synthetic claim without an actual reason record"
        self.manifest["reason"]["evidence"] = {}
        self.save_manifest()
        self.rejects("manifest segmentation reason evidence file required")

    def test_context_handoff_remains_required_for_manifest_segments(self):
        self.plan["segments"][1]["context_before"] = "Unrelated new opening"
        self.rejects("segment narrative context handoff mismatch")

    def test_stale_and_unsafe_manifest_references_fail_without_crashing(self):
        (self.root / "manifest.json").write_text(json.dumps({}), encoding="utf-8")
        self.rejects("evidence hash stale")
        for name in ("\x00", "../outside.json"):
            with self.subTest(name=repr(name)):
                self.data["narration"]["generation_manifest"] = {"file": name, "sha256": "0" * 64}
                self.plan["generation_manifest"] = copy.deepcopy(self.data["narration"]["generation_manifest"])
                self.assertTrue(self.errors())

    def test_existing_continuous_single_and_reuse_plans_remain_valid(self):
        self.data["narration"].pop("generation_manifest")
        self.plan.pop("generation_manifest")
        self.plan.update(mode="continuous_first", segments=[])
        for provenance in ({"generation_record": {"file": "single.json", "sha256": "3" * 64}},
                           {"reuse_record": {"status": "previously_accepted", "reference": "Fixture only"}}):
            with self.subTest(provenance=provenance):
                self.data["narration"].pop("generation_record", None)
                self.data["narration"].pop("reuse_record", None)
                self.data["narration"].update(provenance)
                self.assertEqual(self.errors(), [])

    def test_existing_verified_segment_plan_without_manifest_remains_valid(self):
        self.data["narration"].pop("generation_manifest")
        self.plan.pop("generation_manifest")
        self.plan["technical_limit"] = "Synthetic previously verified interface limit"
        for row, source in zip(self.plan["segments"], self.manifest["segments"]):
            row.update(script=source["input"], audio=source["output"])
        self.assertEqual(self.errors(), [])
        self.plan.pop("technical_limit")
        self.rejects("segmentation technical_limit required")


if __name__ == "__main__":
    unittest.main()
