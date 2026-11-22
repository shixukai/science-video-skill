import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import compose_cover
import feed_package
import google_flow_audit
import opening_hook
import presentation_checks


class TestBannedRhetoricalPhrases(unittest.TestCase):
    def test_opening_hook_rejects_pingshenme(self):
        self.assertIsNotNone(opening_hook.CLICKBAIT_HOOK_RE.search("老电饭煲没有芯片，饭熟凭什么自动跳保温？"))
        self.assertIsNotNone(opening_hook.CLICKBAIT_HOOK_RE.search("隔着玻璃，锅凭啥变烫？"))
        self.assertIsNone(opening_hook.CLICKBAIT_HOOK_RE.search("老电饭煲没有芯片，饭熟怎么自动跳保温？"))

    def test_google_flow_audit_rejects_pingshenme(self):
        self.assertIsNotNone(google_flow_audit.CLICKBAIT_HOOK_RE.search("砸一块陶瓷，凭什么生出几千伏高压？"))
        self.assertIsNone(google_flow_audit.CLICKBAIT_HOOK_RE.search("砸一块陶瓷，怎么会生出几千伏高压？"))

    def test_presentation_checks_rejects_pingshenme(self):
        for surface in ("voiceover", "caption", "cover", "frame"):
            item = {"surface": surface, "text": "涂层凭什么粘在锅上？", "purposes": ["topic"]}
            self.assertTrue(presentation_checks.prohibited_cue(item, {}, {}))
        clean = {"surface": "voiceover", "text": "涂层怎么牢牢粘在锅上？", "purposes": ["topic"]}
        self.assertFalse(presentation_checks.prohibited_cue(clean, {}, {}))

    def test_compose_cover_rejects_pingshenme(self):
        with self.assertRaises(ValueError):
            compose_cover.parse_lines("老电饭煲", "老电饭煲没有芯片，\n饭熟凭什么自动跳保温？")
        with self.assertRaises(ValueError):
            compose_cover.parse_lines("凭啥不粘锅", "鸡蛋都不粘，\n涂层怎么粘在锅上？")
        title, lines = compose_cover.parse_lines("老电饭煲", "老电饭煲没有芯片，\n饭熟怎么自动跳保温？")
        self.assertEqual(title, "老电饭煲")
        self.assertEqual(len(lines), 2)

    def test_feed_package_header_rejects_pingshenme(self):
        policy = feed_package.load_policy()
        font_path = feed_package.find_font(policy)
        pal, _ = feed_package.check_palette(policy, "slate")
        renderer = feed_package.Renderer(policy, font_path, pal)
        with self.assertRaises(ValueError):
            renderer.check_header("磁性物理", ["老电饭煲没有芯片，", "饭熟凭什么自动跳保温？"])
        renderer.check_header("磁性物理", ["老电饭煲没有芯片，", "饭熟怎么自动跳保温？"])


if __name__ == "__main__":
    unittest.main()
