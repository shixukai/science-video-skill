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
        self.assertIsNone(google_flow_audit.CLICKBAIT_HOOK_RE.search("打火机里这块小陶瓷，一按就能压出几千伏高压？"))

    def test_google_flow_audit_flags_blunt_or_harsh_tone(self):
        for harsh in (
            "油这么热，它为什么不悄悄蒸发，偏要炸？",
            "别傻了，涂层根本不是靠胶水粘住的。",
            "听好了，先说结论，一秒看懂它的原理。",
            "这股压力直接把油面干爆。",
        ):
            self.assertIsNotNone(google_flow_audit.BLUNT_HARSH_TONE_RE.search(harsh), harsh)
        for warm in (
            "油这么烫，水为什么不慢慢蒸发掉，反而会一下子溅出来呢？",
            "打火机里这块小陶瓷，手指轻轻一按，怎么就能压出几千伏高压？",
            "我们先拿一杯凉油试试，滴进一滴染过色的水。",
        ):
            self.assertIsNone(google_flow_audit.BLUNT_HARSH_TONE_RE.search(warm), warm)

    def test_google_flow_audit_flags_abrupt_camera_stage_direction(self):
        for abrupt in (
            "钢化玻璃正面敲不破，边角轻轻一磕却碎成一片。顺着截面往里看，里面藏着两股互相拉扯的力。",
            "切开它的截面，里面藏着两股互相拉扯的力。",
            "剖开锅底就能看到一块感温磁铁。",
            "放大锅底截面，就能看到底层的微米小坑。",
            "放大这个小切口，诀窍就藏在缺口最尖端那一点。",
            "凑近门里这层金属网，奥妙就在尺寸差里。",
            "把冰放大到分子这一层，你会看到很多小空隙。",
            "仔细看拉头里面，藏着一道丫字形通道。",
        ):
            self.assertIsNotNone(google_flow_audit.ABRUPT_CAMERA_DIRECTION_RE.search(abrupt), abrupt)
        for natural in (
            "同一块玻璃反差这么大，是因为它内部早就藏着两股互相拉扯的力。",
            "算上卷进来的空气，最终吹出的风量能放大十几倍。",
            "第一级杠杆先把指力放大近十倍，尖端受力被成倍放大。",
            "同是电磁波却待遇不同，正好卡在小孔和波长的尺寸差上。",
        ):
            self.assertIsNone(google_flow_audit.ABRUPT_CAMERA_DIRECTION_RE.search(natural), natural)

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
