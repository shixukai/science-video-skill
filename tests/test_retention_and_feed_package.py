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
        self.assertIn("feed_package", template["qa"])


class FeedLayoutTests(unittest.TestCase):
    def test_default_layout_keeps_full_width_without_crop(self):
        geo = feed_package.layout(FEED, 1920, 1080, 1.0)
        self.assertEqual(geo["scaled_w"], 1080)
        self.assertEqual(geo["crop_fraction_each_side"], 0)
        self.assertGreater(geo["picture_top"], FEED["header"]["top_safe_y"])

    def test_zoom_outside_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            feed_package.layout(FEED, 1920, 1080, FEED["max_zoom"] + 0.1)


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


if __name__ == "__main__":
    unittest.main()
