"""Structural regression for opening instructions, not an audience/AI evaluation.

The synthetic contrast cases in the owner reference require independent semantic
review. These checks catch dropped ownership, priority and role handoffs only.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class OpeningOrientationContractTests(unittest.TestCase):
    def text(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_owner_requires_context_before_dependent_detail(self):
        text = self.text("references/viewer-retention-design.md")
        self.assertIn("### Orient the viewer before introducing a detail", text)
        self.assertIn("before a component, procedure, unexplained number or technical term depends on it", text)
        self.assertIn("without the title, cover, description or task chat", text)
        self.assertIn("Necessary naming is not a title echo", text)

    def test_orientation_not_a_fixed_spoken_template(self):
        text = self.text("references/viewer-retention-design.md")
        for phrase in ("They need not use the same sentence order", "do not demand spoken repetition",
                       "not a new gate, fixed sentence template or extra timing quota",
                       "a script-only check cannot approve a planned image"):
            self.assertIn(phrase, text)

    def test_hook_priority_and_chip_example_do_not_defer_context(self):
        text = self.text("references/viewer-retention-design.md")
        self.assertIn("it is not yet an opening", text)
        self.assertIn("not put anonymous fine lines first", text)
        self.assertIn("coherent alternative application-led route", text)
        self.assertNotIn("the table shows the bridge that follows the hook", text)
        hook = self.text("references/viral-appeal-and-packaging.md")
        self.assertIn("later background cannot retroactively supply a missing referent", hook)
        self.assertIn("not necessary subject naming", hook)

    def test_visible_clue_is_not_the_capture_tool(self):
        owner = self.text("references/viewer-retention-design.md")
        for phrase in ("If the subject is the specimen or phenomenon",
                       "If the subject is how the tool works",
                       "the instrument can stay offscreen",
                       "only if the source identifies them",
                       "Leave the explanation open"):
            self.assertIn(phrase, owner)
        hook = self.text("references/viral-appeal-and-packaging.md")
        self.assertIn("what visible clue makes it worth watching", hook)
        self.assertIn("viewer-retention-design.md#orient-the-viewer-before-introducing-a-detail", hook)

    def test_roles_route_to_shared_owner(self):
        for role in ("video_researcher", "video_audio_editor", "video_reviewer"):
            with self.subTest(role=role):
                text = self.text("agents/" + role + ".toml")
                self.assertIn("viewer-retention-design.md#orient-the-viewer-before-introducing-a-detail", text)
                self.assertIn("Necessary subject naming is not a forbidden preamble", text)

    def test_positive_and_negative_calibration_cases_retained(self):
        text = self.text("references/viewer-retention-design.md")
        for name in ("Detail without an object", "Instrument and question together",
                     "Same image, different subject", "A recognizable everyday object",
                     "Topic word without a connection", "Background instead of orientation"):
            self.assertIn("| " + name + " |", text)

if __name__ == "__main__":
    unittest.main()
