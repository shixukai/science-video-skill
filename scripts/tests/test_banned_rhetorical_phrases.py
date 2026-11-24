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

    def test_google_flow_audit_flags_curiosity_killers_and_flat_additive_lists(self):
        for spoiler in (
            "冰块浮在水上，其实原理很简单，就是密度变小了。",
            "说到底就是因为水分子之间撑开了空隙。",
            "简单来说就是因为光速比声速快得多。",
            "直接告诉你答案，里面藏着一块磁铁。",
        ):
            self.assertIsNotNone(google_flow_audit.PREMATURE_SPOILER_RE.search(spoiler), spoiler)
        for hype in (
            "今天我们来揭开微波炉的秘密。",
            "看到最后你就明白了。",
            "接下来我们一起来看它的内部结构。",
            "带你一探究竟，一起揭秘不粘锅。",
        ):
            self.assertIsNotNone(google_flow_audit.EMPTY_SUSPENSE_RE.search(hype), hype)
        flat_list = "此外，锅底涂了氟塑料。另外，中间还有底漆。与此同时，金属表面做了喷砂。"
        self.assertGreaterEqual(len(google_flow_audit.ADDITIVE_LIST_TRANSITION_RE.findall(flat_list)), 3)
        causal_story = (
            "按理说东西越冷越紧实，可冰块扔进水里却稳稳浮在上面。"
            "温度越低，水分子怎么反而越排越松？"
            "于是水分子开始排成规则的六边形，可新问题马上来了，这些空隙直接把整体体积撑大了一圈。"
        )
        self.assertIsNone(google_flow_audit.PREMATURE_SPOILER_RE.search(causal_story))
        self.assertIsNone(google_flow_audit.EMPTY_SUSPENSE_RE.search(causal_story))
        self.assertLess(len(google_flow_audit.ADDITIVE_LIST_TRANSITION_RE.findall(causal_story)), 3)

        for bad_en in (
            "Welcome back to our channel, let's dive right in.",
            "The short answer is pressure drop, stay until the end.",
            "You won't believe what happens next will shock you.",
        ):
            self.assertIsNotNone(google_flow_audit.EN_CURIOSITY_KILLER_RE.search(bad_en), bad_en)
        good_en = (
            "By all rights, frozen water should sink like any other solid — yet an ice cube bobs right back to the surface. "
            "Which immediately creates a puzzle: why do cooling water molecules spread farther apart instead of packing tighter?"
        )
        self.assertIsNone(google_flow_audit.EN_CURIOSITY_KILLER_RE.search(good_en))

        for early_dump in (
            "先来了解一下它的基本结构。",
            "它主要由主阀、副管和薄膜三部分组成。",
            "整个过程分为以下三个部分。",
        ):
            self.assertIsNotNone(google_flow_audit.EARLY_STRUCTURE_DUMP_RE.search(early_dump), early_dump)

        for end_sig in (
            "总结一下，这就是加油枪为什么会自动跳枪的原因。",
            "所以说到底，一切都靠这股小气流。",
            "讲到这里，你应该明白了它的秘密。",
        ):
            self.assertIsNotNone(google_flow_audit.PREMATURE_ENDING_SIGNAL_RE.search(end_sig), end_sig)
        self.assertIsNone(
            google_flow_audit.PREMATURE_ENDING_SIGNAL_RE.search(
                "下次听见油枪那声清脆的咔哒，其实不是机器算准了油量，而是那股刚好被油面封住的小气流替你按下了开关。"
            )
        )

        for bad_en_end in (
            "In conclusion, that is how ice stays afloat.",
            "To summarize, pressure closes the valve.",
            "Now you know why it clicks shut.",
        ):
            self.assertIsNotNone(google_flow_audit.EN_ENDING_SIGNAL_RE.search(bad_en_end), bad_en_end)
        bad_en_list = "The valve drops. Furthermore, air enters the tube. Moreover, suction builds up."
        self.assertGreaterEqual(len(google_flow_audit.EN_ADDITIVE_LIST_RE.findall(bad_en_list)), 2)

    def test_opening_hook_rejects_preamble_and_premature_spoiler(self):
        for bad_line in (
            "大家好，今天我们来聊聊冰块为什么会浮起来。",
            "你知道吗，其实原理很简单。",
            "先来了解一下它的基本结构。",
            "看到最后你就明白了。",
        ):
            self.assertIsNotNone(opening_hook.OPENING_FILLER_RE.search(bad_line), bad_line)
        self.assertIsNone(opening_hook.OPENING_FILLER_RE.search("按理说东西越冷越紧实，可冰块放进水里却稳稳浮在上面。"))

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

    def test_feed_package_header_rejects_pingshenme_and_abstract_discipline_topics(self):
        policy = feed_package.load_policy()
        font_path = feed_package.find_font(policy)
        pal, _ = feed_package.check_palette(policy, "slate")
        renderer = feed_package.Renderer(policy, font_path, pal)
        with self.assertRaises(ValueError):
            renderer.check_header("老电饭煲", ["老电饭煲没有芯片，", "饭熟凭什么自动跳保温？"])
        for abstract_topic in ("磁性物理", "材料力学", "流体气压", "几何光学", "机械结构", "电磁屏蔽"):
            with self.assertRaises(ValueError, msg=abstract_topic):
                renderer.check_header(abstract_topic, ["砸正面不破，", "轻磕边角怎么瞬间全碎？"])
        for concrete_topic in ("钢化玻璃", "老电饭煲", "饮料瓶盖", "加油枪自动跳枪"):
            renderer.check_header(concrete_topic, ["砸正面不破，", "轻磕边角怎么瞬间全碎？"])

    def test_retention_timeline_blank_frame_and_tight_tail_detection(self):
        import retention_timeline
        policy = retention_timeline.load_policy()
        self.assertLessEqual(policy["answer_to_end_review_s"], 3.5)
        # 4.5s post-answer tail must trigger long_tail_after_answer
        ledger = retention_timeline.ledger_from_episode({
            "topic_alignment": {
                "opening": {"viewing_promise": {"time_s": 6.0}, "payoff_steps": []},
                "ending": {"answer_time_s": 39.5},
            }
        })
        flags, _, _ = retention_timeline.ledger_flags(ledger, 44.5, policy)
        self.assertIn("long_tail_after_answer", flags)
        flags_tight, _, _ = retention_timeline.ledger_flags(ledger, 41.0, policy)
        self.assertNotIn("long_tail_after_answer", flags_tight)

        # Synthetic 4 fps stats: 10 seconds (40 frames), pitch-black clip at 3.5-4.0s and flat blank at 6.0-7.5s
        means = [0.4] * 40
        stds = [0.18] * 40
        for i in range(14, 16):
            means[i] = 0.01
            stds[i] = 0.005
        for i in range(24, 30):
            means[i] = 0.35
            stds[i] = 0.02
        findings = retention_timeline.blank_or_black_intervals(means, stds, 4, 10.0, policy)
        kinds = {item["kind"] for item in findings}
        self.assertEqual(kinds, {"mid_video_black_frame", "low_detail_blank_stretch"})


if __name__ == "__main__":
    unittest.main()
