"""Use synthetic release records to check declaration applicability."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage_checks import Checks
from cover_fixture import png, ref


class ReleaseAIDisclosureTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        png(self.root / "preview.png", 2, 2)
        self.declaration = {
            "status": "pass",
            "contains_generated_content": True,
            "platform_declaration_required": False,
            "applicable_platform_controls_checked": True,
            "platform_declaration_used": False,
            "required_provenance_preserved": True,
            "current_rule_reference": "Synthetic destination rule",
            "declaration_evidence": "Synthetic reviewed destination control",
            "not_applicable_reason": "Synthetic rule does not require this declaration",
        }
        self.data = {
            "narration": {"voice_type": "synthetic"},
            "qa": {
                "reviewed_sha256": {"video": "a" * 64},
                "mobile_preview": {"phone": {
                    "status": "pass", "surface": "actual_device",
                    "device": "Fixture", "app_version": "1", "checked_at": "fixture time",
                    "video_sha256": "a" * 64, "main_content_visible": True,
                    "captions_visible": True, "audio_checked": True,
                    "actual_overlay_geometry": [{"x": 0, "y": 0, "width": 1, "height": 1}],
                    "overlay_coordinate_space": "screenshot_pixels", "canvas": [2, 2],
                    "screenshot": ref(self.root, "preview.png"),
                }},
                "release": {"ai_disclosure": self.declaration},
            },
        }

    def errors(self):
        checks = Checks(self.data, self.root)
        checks.platform_and_disclosure()
        return checks.errors

    def test_verified_optional_declaration_with_synthetic_audio(self):
        self.assertEqual(self.errors(), [])
        for key, missing in (("not_applicable_reason", ""), ("current_rule_reference", ""),
                             ("declaration_evidence", ""), ("applicable_platform_controls_checked", False),
                             ("required_provenance_preserved", False)):
            with self.subTest(key=key):
                saved = self.declaration[key]
                self.declaration[key] = missing
                self.assertTrue(self.errors())
                self.declaration[key] = saved

    def test_required_declaration_for_explicit_and_legacy_records(self):
        self.declaration["platform_declaration_required"] = True
        self.assertIn("stage: AI disclosure platform_declaration_used not checked", self.errors())
        del self.declaration["platform_declaration_required"]
        self.assertIn("stage: AI disclosure platform_declaration_used not checked", self.errors())
        self.declaration["platform_declaration_used"] = True
        self.assertEqual(self.errors(), [])

    def test_unknown_requirement_cannot_pass(self):
        self.declaration["platform_declaration_required"] = None
        self.assertIn("stage: AI disclosure platform declaration requirement must be verified", self.errors())

    def test_generated_content_presence_depends_on_actual_release_inputs(self):
        self.declaration["contains_generated_content"] = False
        expected = "stage: known generated content cannot be marked absent"
        self.assertIn(expected, self.errors())
        self.data["narration"]["voice_type"] = "recorded"
        self.data["assets"] = [{"id": "AI1", "kind": "ai_generated"}]
        self.assertEqual(self.errors(), [])
        self.data["shots"] = [{"id": "SH1", "asset_ids": ["AI1"]}]
        self.assertIn(expected, self.errors())
