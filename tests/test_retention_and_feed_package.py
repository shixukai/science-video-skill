"""Synthetic regressions for the retention locator and the vertical feed package.

All media are generated in a temporary directory; no user footage is read.
The checks cover ledger arithmetic and output structure only, never appeal.
"""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import feed_package  # noqa: E402
import retention_timeline as rt  # noqa: E402

POLICY = json.loads((ROOT / "config/production-policy.json").read_text(encoding="utf-8"))
RETENTION = POLICY["retention_design"]
FEED = POLICY["feed_package"]
HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def episode(steps, promise=6.0, answer=52.0):
    return {"topic_alignment": {
        "opening": {"viewing_promise": {"line": "答案藏在冰晶的空隙里。", "fulfilled_by_scope_id": "R2", "time_s": promise},
                    "payoff_steps": steps},
        "ending": {"answer": "synthetic", "answer_time_s": answer}}}


GOOD_STEPS = [
    {"scope_id": "R1", "time_s": 15.0, "opens_question": "为什么结冰后占地方更大？", "closes_question": ""},
    {"scope_id": "R2", "time_s": 30.0, "opens_question": "空隙去哪了？", "closes_question": "为什么结冰后占地方更大？"},
    {"scope_id": "R3", "time_s": 45.0, "opens_question": "", "closes_question": "空隙去哪了？"},
]


class LedgerTests(unittest.TestCase):
    def flags(self, data, duration=56.0):
        return rt.ledger_flags(rt.ledger_from_episode(data), duration, RETENTION)

    def test_well_ordered_ledger_has_no_flags(self):
        flags, intervals, empty = self.flags(episode(GOOD_STEPS))
        self.assertEqual(flags, [])
        self.assertEqual(empty, [])

    def test_main_answered_early_without_new_question(self):
        steps = copy.deepcopy(GOOD_STEPS)
        steps[0]["closes_question"] = "main"
        steps[0]["opens_question"] = ""
        steps[1]["opens_question"] = ""
        steps[2]["closes_question"] = ""
        flags, intervals, _ = self.flags(episode(steps))
        self.assertIn("final_answer_early", flags)
        self.assertIn("no_open_question_interval", flags)
        self.assertEqual(intervals["no_open_question_interval"][0][0], 15.0)

    def test_payoff_gap_late_promise_and_long_tail(self):
        steps = [GOOD_STEPS[0], GOOD_STEPS[2]]
        flags, intervals, _ = self.flags(episode(steps, promise=11.0, answer=52.0), duration=70.0)
        self.assertIn("late_viewing_promise", flags)
        self.assertIn("payoff_gap_over_review", flags)
        self.assertIn([15.0, 45.0], intervals["payoff_gap_over_review"])
        self.assertIn("long_tail_after_answer", flags)

    def test_untimed_fields_are_missing_not_passed(self):
        data = episode([{"scope_id": "R1", "opens_question": "q", "closes_question": "", "time_s": None}],
                       promise=None, answer=None)
        ledger = rt.ledger_from_episode(data)
        self.assertIn("topic_alignment.opening.viewing_promise.time_s", ledger["missing"])
        self.assertIn("topic_alignment.ending.answer_time_s", ledger["missing"])
        self.assertTrue(any(m.startswith("payoff_steps[0].time_s") for m in ledger["missing"]))

    def test_template_carries_ledger_fields(self):
        template = json.loads((ROOT / "assets/episode-template.json").read_text(encoding="utf-8"))
        opening = template["topic_alignment"]["opening"]
        for field in RETENTION["ledger_fields"]:
            self.assertIn(field, opening["payoff_steps"][0])
        self.assertIn("viewing_promise", opening)
        self.assertIn("answer_time_s", template["topic_alignment"]["ending"])
        self.assertIn("feed_package", template["deliverables"])
        self.assertIn("textless_master", template["deliverables"])
        self.assertIn("feed_package", template["qa"])


class FeedLayoutTests(unittest.TestCase):
    def test_default_layout_keeps_full_width_without_crop(self):
        geo = feed_package.layout(FEED, 1920, 1080, 1.0)
        self.assertEqual(geo["scaled_w"], 1080)
        self.assertEqual(geo["crop_fraction_each_side"], 0)
        self.assertGreater(geo["picture_top"], FEED["header"]["top_safe_y"])

    def test_caption_band_sits_between_picture_and_bottom_safe_area(self):
        geo = feed_package.layout(FEED, 1920, 1080, 1.0, caption_band=True)
        self.assertGreater(geo["caption_top"], geo["picture_bottom"])
        self.assertLessEqual(geo["caption_bottom"], FEED["caption_band"]["bottom_safe_y"])

    def test_zoom_outside_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            feed_package.layout(FEED, 1920, 1080, FEED["max_zoom"] + 0.1)


class PaletteTests(unittest.TestCase):
    def test_all_non_exempt_palettes_are_dark_and_glare_checked(self):
        for name in FEED["palettes"]:
            with self.subTest(palette=name):
                colors, record = feed_package.check_palette(FEED, name)
                if name not in FEED["contrast"]["exempt_palettes"]:
                    self.assertLessEqual(record["band_relative_luminance"], FEED["contrast"]["band_max_relative_luminance"])

    def test_bright_band_and_glaring_text_are_rejected(self):
        policy = copy.deepcopy(FEED)
        policy["palettes"]["bright"] = {"band": "#FFFBF1", "topic": "#994B37", "question": "#193E4B", "caption": "#243840"}
        policy["palettes"]["glare"] = {"band": "#000000", "topic": "#E39B78", "question": "#FFFFFF", "caption": "#FFFFFF"}
        for name in ("bright", "glare"):
            with self.subTest(palette=name), self.assertRaises(ValueError):
                feed_package.check_palette(policy, name)

    def test_default_is_a_night_palette(self):
        self.assertNotIn(FEED["default_palette"], FEED["contrast"]["exempt_palettes"])


class CaptionWrapTests(unittest.TestCase):
    measure = staticmethod(lambda text: 54 * len(text))  # synthetic monospace width

    def test_numbers_stay_with_units_and_punctuation_never_starts_a_line(self):
        self.assertIn("0.917 g/cm³", feed_package.tokenize("密度只有0.917 g/cm³左右。"))
        self.assertIn("4 °C", feed_package.tokenize("水在4 °C时最重"))
        self.assertIn("100摄氏度，", feed_package.tokenize("加热到100摄氏度，"))
        lines = feed_package.wrap("同样是水分子，结冰后却排成了带空隙的六边形。", self.measure, 828, 2)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].endswith("，"))
        self.assertTrue(all(line[0] not in feed_package.CLOSING for line in lines))

    def test_overlong_cue_is_split_with_flagged_estimated_timing(self):
        text = "同样是水分子，结冰后却排成了带空隙的六边形，所以密度只有0.917 g/cm³左右，比水还轻一点。"
        parts = feed_package.fit_cue(2.0, 8.0, text, self.measure, 828, 2)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(split for _, _, _, split in parts))
        self.assertEqual(parts[0][0], 2.0)
        self.assertEqual(parts[-1][1], 8.0)
        for a, b in zip(parts, parts[1:]):
            self.assertEqual(a[1], b[0])

    def test_unsplittable_cue_is_rejected(self):
        with self.assertRaises(ValueError):
            feed_package.fit_cue(0, 3, "这是一句没有任何标点而且长得根本放不进两行字幕带里的超长字幕文本内容示例", self.measure, 828, 2)

    def test_parse_srt_and_ass_and_reject_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            srt = Path(tmp) / "c.srt"
            srt.write_text("1\n00:00:00,000 --> 00:00:01,500\n冰是固体，\n却浮在水上。\n\n2\n00:00:02,000 --> 00:00:03,000\n第二句\n",
                           encoding="utf-8")
            self.assertEqual(feed_package.parse_captions(srt)[0], (0.0, 1.5, "冰是固体，却浮在水上。"))
            ass = Path(tmp) / "c.ass"
            ass.write_text("[Events]\nDialogue: 0,0:00:01.00,0:00:02.50,Default,,0,0,0,,{\\b1}第一句\\N换行\n", encoding="utf-8")
            self.assertEqual(feed_package.parse_captions(ass), [(1.0, 2.5, "第一句换行")])
            bad = Path(tmp) / "bad.srt"
            bad.write_text("1\n00:00:00,000 --> 00:00:02,000\n甲\n\n2\n00:00:01,000 --> 00:00:03,000\n乙\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                feed_package.parse_captions(bad)

    def test_states_switch_header_for_ending_question(self):
        states = feed_package.build_states(10.0, [(0.0, 2.0, "a"), (3.0, 9.0, "b")], ending_from=8.0)
        self.assertEqual(states[0], (0.0, 2.0, "a", False))
        self.assertIn((8.0, 9.0, "b", True), states)
        self.assertEqual(states[-1], (9.0, 10.0, None, True))


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe required")
class MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="synthetic-retention-")
        cls.root = Path(cls.tmp.name)
        cls.master = cls.root / "master.mp4"
        # 20 s: moving block, then a long static hold, plus a silent final stretch.
        video = ("nullsrc=s=320x180:r=8,geq=lum='if(lt(T,8),if(between(X,10+20*T,60+20*T),200,40),"
                 "if(between(X,100,160),200,40))':cb=128:cr=128")
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", video,
                        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
                        "-t", "20", "-af", "volume='if(gt(t,16),0,1)':eval=frame",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(cls.master)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_measure_reports_long_static_shot_and_silence(self):
        ep = self.root / "episode.json"
        ep.write_text(json.dumps(episode([{"scope_id": "R1", "time_s": 5.0, "opens_question": "q",
                                            "closes_question": ""}], promise=4.0, answer=12.0)), encoding="utf-8")
        policy = dict(RETENTION, long_shot_review_s=8.0)
        report = rt.measure(self.master, ep, policy, preview_dir=self.root / "preview",
                            report_path=self.root / "r.json")
        self.assertEqual(report["tool"], "scripts/retention_timeline.py")
        self.assertIn("long_low_change_shot", report["flags"])
        self.assertIn("silent_mix_interval", report["flags"])
        self.assertIn("long_tail_after_answer", report["flags"])
        self.assertTrue((self.root / report["timeline"]["file"]).is_file())

    def test_feed_package_composes_vertical_canvas(self):
        try:
            font = feed_package.find_font(FEED)
        except ValueError:
            self.skipTest("no CJK bold font on this machine")
        master = self.root / "master169.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=1920x1080:r=24",
                        "-f", "lavfi", "-i", "sine=frequency=330:sample_rate=48000", "-t", "2",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(master)], check=True)
        out = self.root / "feed.mp4"
        report = feed_package.compose(master, "浮冰", "冰是固体，\n为什么会浮在水上？", out, FEED, font=str(font),
                                      report_path=self.root / "feed.json")
        self.assertEqual([report["output"]["width"], report["output"]["height"]], FEED["canvas"])
        self.assertTrue(report["output"]["audio_stream"])
        self.assertEqual(report["phone_view"]["status"], "pending")
        with self.assertRaises(ValueError):
            feed_package.compose(master, "浮冰", "一\n二\n三", self.root / "bad.mp4", FEED, font=str(font))

    def test_caption_band_package_draws_captions_only_during_cues(self):
        try:
            font = feed_package.find_font(FEED)
        except ValueError:
            self.skipTest("no CJK bold font on this machine")
        master = self.root / "textless.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=1920x1080:r=24",
                        "-f", "lavfi", "-i", "sine=frequency=330:sample_rate=48000", "-t", "4",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(master)], check=True)
        srt = self.root / "band.srt"
        srt.write_text("1\n00:00:00,500 --> 00:00:02,000\n冰是固体，却浮在水上。\n", encoding="utf-8")
        out = self.root / "band.mp4"
        report = feed_package.compose(master, "浮冰", "为什么会浮？", out, FEED, font=str(font),
                                      captions=srt, ending_question="你家冰块浮着吗？", ending_from=3.0)
        geo = report["geometry"]
        self.assertEqual(geo["mode"], "caption_band")
        self.assertEqual(report["source_master"]["kind"], "textless_master")

        band_luma = round(255 * feed_package.relative_luminance(report["palette"]["colors"]["band"]) ** (1 / 2.2))

        def text_pixels(t):
            y0, y1 = geo["caption_top"], geo["caption_bottom"]
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(out), "-frames:v", "1",
                                  "-vf", f"crop=1080:{y1 - y0}:0:{y0},format=gray", "-f", "rawvideo", "-"],
                                 capture_output=True, check=True).stdout
            return sum(1 for v in raw if abs(v - band_luma) > 60)

        self.assertEqual(report["palette"]["name"], FEED["default_palette"])
        self.assertGreater(text_pixels(1.0), 500)
        self.assertLess(text_pixels(2.6), 50)
        self.assertEqual(report["ending_question"]["from_s"], 3.0)


if __name__ == "__main__":
    unittest.main()
