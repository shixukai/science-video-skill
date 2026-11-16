"""Opening-hook plan, measurement and evidence tests on synthetic media only."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opening_hook import check_hook_plan, load_policy, measure, sha256_file, spoken_units, validate_opening_hook
from opening_alignment_guard import check_opening_plan

POLICY = load_policy()
FULL_POLICY = {"opening_hook": POLICY}
HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def good_opening():
    return {
        "voiceover": "冰是固体，却浮在水上。同样多的水，结冰后体积变大了。",
        "hook": {
            "pattern": "strange_phenomenon",
            "first_frame": "冰块正落入透明水杯，溅起水花后浮在水面",
            "frame0_motion": "冰块在第0帧已在下落途中",
            "first_sound": "冰块入水的清脆声与旁白同时起",
            "first_line": "冰是固体，却浮在水上。",
            "payload_clause": "却浮在水上",
            "tension": "固体通常更密，冰却浮起",
            "muted_read": "静音也能看到冰落水后浮起并读到首句字幕",
            "phone_read": "竖屏信息流中横屏小窗内冰块占画面高度一半",
            "source_shot_id": "SH1",
            "return_in_body": "SH6 回到同一杯水解释密度",
            "candidates": [
                {"pattern": "strange_phenomenon", "first_frame": "冰落水浮起", "first_line": "冰是固体，却浮在水上。",
                 "tension": "反常", "selected": True, "lost_because": ""},
                {"pattern": "extreme_contrast", "first_frame": "冰与石蜡并排入水", "first_line": "冰浮起，固体石蜡却沉底。",
                 "tension": "同为固体结果相反", "selected": False, "lost_because": "需要额外解释石蜡，首帧主体变成两个"},
                {"pattern": "stakes_in_action", "first_frame": "冻裂的水管", "first_line": "这根水管，是被冰撑裂的。",
                 "tension": "日常损失", "selected": False, "lost_because": "答案偏向膨胀力而不是浮起，承诺偏题"},
            ],
        },
    }


class HookPlanTests(unittest.TestCase):
    def test_complete_front_loaded_plan_passes(self):
        self.assertEqual(check_hook_plan(good_opening(), POLICY), [])

    def test_context_first_line_is_rejected(self):
        opening = good_opening()
        opening["hook"]["first_line"] = "杯子里放着一块普通的冰，同样是水，结冰后为什么会浮在水上？"
        opening["hook"]["payload_clause"] = "为什么会浮在水上"
        opening["voiceover"] = opening["hook"]["first_line"]
        errors = check_hook_plan(opening, POLICY)
        self.assertTrue(any("front-load" in e for e in errors), errors)

    def test_payload_must_be_quoted_and_voiceover_must_start_with_line(self):
        opening = good_opening()
        opening["hook"]["payload_clause"] = "冰会漂浮"
        opening["voiceover"] = "大家好。" + opening["voiceover"]
        errors = check_hook_plan(opening, POLICY)
        self.assertTrue(any("verbatim" in e for e in errors))
        self.assertTrue(any("must start with" in e for e in errors))

    def test_candidates_need_comparison(self):
        opening = good_opening()
        opening["hook"]["candidates"] = opening["hook"]["candidates"][:1]
        self.assertTrue(any("candidates" in e for e in check_hook_plan(opening, POLICY)))
        opening = good_opening()
        for c in opening["hook"]["candidates"]:
            c["pattern"] = "strange_phenomenon"
        self.assertTrue(any("two different patterns" in e for e in check_hook_plan(opening, POLICY)))
        opening = good_opening()
        opening["hook"]["candidates"][1]["lost_because"] = ""
        self.assertTrue(any("lost_because" in e for e in check_hook_plan(opening, POLICY)))

    def test_spoken_units_count_cjk_and_words(self):
        self.assertEqual(spoken_units("冰是固体，却浮在水上"), 9)
        self.assertEqual(spoken_units("5G芯片"), 3)

    def test_opening_guard_checks_hook_only_when_present(self):
        data = {"scope": {"kind": "episode"}, "topic_alignment": {"opening": {}}}
        legacy = check_opening_plan(data)
        self.assertFalse(any("opening hook" in e for e in legacy))
        data["topic_alignment"]["opening"]["hook"] = {}
        self.assertTrue(any("opening hook" in e for e in check_opening_plan(data)))

    def test_part_of_host_hook_requires_macro_host_and_whole_to_part_bridge(self):
        opening = good_opening()
        opening["hook"]["host_relation"] = "standalone"
        self.assertEqual(check_hook_plan(opening, POLICY), [])
        opening["hook"]["host_relation"] = "invalid_scope"
        self.assertTrue(any("host_relation" in e for e in check_hook_plan(opening, POLICY)))
        opening["hook"]["host_relation"] = "part_of_host"
        errors = check_hook_plan(opening, POLICY)
        self.assertTrue(any("host_system" in e for e in errors), errors)
        self.assertTrue(any("whole_to_part_bridge" in e for e in errors), errors)
        opening["hook"]["host_system"] = "一整台行驶中的双发客机发动机短舱"
        opening["hook"]["whole_to_part_bridge"] = "0-1.5s 先看到机翼下完整短舱进气，1.5-5.0s 连续半透明剖开外壳推入高压压气机级间安装位"
        self.assertEqual(check_hook_plan(opening, POLICY), [])


class FakeChecks:
    def __init__(self, root, qa):
        self.root = Path(root).resolve()
        self.qa = qa
        self.errors = []

    def need(self, ok, message):
        if not ok:
            self.errors.append(message)
        return bool(ok)

    def evidence(self, ref, label):
        ref = ref if isinstance(ref, dict) else {}
        name = ref.get("file")
        if not self.need(isinstance(name, str) and name, label + " evidence file required"):
            return None
        path = (self.root / name).resolve()
        if not self.need(path.is_file(), label + " missing"):
            return None
        self.need(ref.get("sha256") == sha256_file(path), label + " evidence hash stale")
        return path


class HookEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "exports").mkdir()
        self.video = self.root / "exports" / "final.mp4"
        self.video.write_bytes(b"synthetic-final-video")
        self.cold = {"status": "pass", "reviewer": "fresh-reviewer-task-17", "review_task_id": "task-17",
                     "context": "cold_view", "method": "normal_speed_continuous_av",
                     "actually_watched": True, "actually_heard": True,
                     "muted_at_1s": "冰块正在落入水杯", "muted_at_2s": "冰块浮在水面，字幕读到却浮在水上",
                     "sound_at_2s": "入水声后旁白说冰是固体却浮在水上", "object_named": "冰块和一杯水",
                     "tension_or_question": "固体为什么会浮起", "would_stop": True, "swipe_reason_if_any": ""}

    def tearDown(self):
        self.tmp.cleanup()

    def write_report(self, name="hook-final-001.json", **changes):
        report = {"schema_version": 1, "video": {"file": "final.mp4", "sha256": sha256_file(self.video)},
                  "window_s": [0, 2.05], "flags": [], "exceptions": {}, "cold_test": copy.deepcopy(self.cold)}
        report.update(changes)
        path = self.root / "exports" / name
        path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
        return {"file": "exports/" + name, "sha256": sha256_file(path)}

    def qa(self, evidence, **record):
        base = {"status": "pass", "final": {"status": "pass", "evidence": evidence}}
        base.update(record)
        return {"opening_hook": base, "reviewed_sha256": {"video": sha256_file(self.video)}}

    def run_validate(self, qa, stage="G5"):
        checks = FakeChecks(self.root, qa)
        validate_opening_hook(checks, FULL_POLICY, stage)
        return checks.errors

    def test_bound_cold_tested_report_passes(self):
        self.assertEqual(self.run_validate(self.qa(self.write_report())), [])

    def test_legacy_record_without_field_is_not_required(self):
        self.assertEqual(self.run_validate({"reviewed_sha256": {}}), [])

    def test_stale_video_and_unresolved_flag_fail(self):
        evidence = self.write_report(flags=["late_audio_onset"])
        qa = self.qa(evidence)
        qa["reviewed_sha256"]["video"] = "0" * 64
        errors = self.run_validate(qa)
        self.assertTrue(any("current reviewed final video" in e for e in errors))
        self.assertTrue(any("unresolved technical flag" in e for e in errors))

    def test_flag_with_concrete_exception_passes(self):
        evidence = self.write_report(flags=["low_contrast_first_frame"],
                                     exceptions={"low_contrast_first_frame": "真实雾中观测条件，主体由运动和声音识别"})
        self.assertEqual(self.run_validate(self.qa(evidence)), [])

    def test_informed_or_unheard_or_non_stopping_cold_test_fails(self):
        for change in ({"context": "informed"}, {"actually_heard": False}, {"would_stop": False}, {"muted_at_2s": ""}):
            cold = dict(self.cold, **change)
            errors = self.run_validate(self.qa(self.write_report(name="r-%d.json" % len(change), cold_test=cold)))
            self.assertTrue(errors, change)

    def test_not_applicable_needs_commission_reason(self):
        self.assertTrue(self.run_validate({"opening_hook": {"status": "not_applicable"}}))
        ok = {"opening_hook": {"status": "not_applicable", "not_applicable_reason": "课堂内嵌讲解，不进入信息流",
                               "commission_reference": "user message 2026-11-11 21:00"}}
        self.assertEqual(self.run_validate(ok), [])

    def test_g3_sample_report_is_required(self):
        evidence = self.write_report(name="hook-sample-001.json")
        qa = {"opening_hook": {"status": "pending", "sample": {"status": "pass", "evidence": evidence}}}
        self.assertEqual(self.run_validate(qa, "G3"), [])
        qa["opening_hook"]["sample"]["status"] = "pending"
        self.assertTrue(self.run_validate(qa, "G3"))

    def test_local_sample_scope_does_not_need_a_feed_hook(self):
        checks = FakeChecks(self.root, {"opening_hook": {"status": "pending"}})
        checks.data = {"scope": {"kind": "local_sample"}}
        validate_opening_hook(checks, FULL_POLICY, "G3")
        self.assertEqual(checks.errors, [])

    def test_part_of_host_cold_test_requires_visual_host_and_part_in_whole_clarity(self):
        plan_data = {"scope": {"kind": "episode"},
                     "topic_alignment": {"opening": {"hook": {"host_relation": "part_of_host"}}}}
        missing_host = self.write_report(name="hook-part-missing.json")
        checks = FakeChecks(self.root, self.qa(missing_host))
        checks.data = plan_data
        validate_opening_hook(checks, FULL_POLICY, "G5")
        self.assertTrue(any("host_system_seen" in e for e in checks.errors), checks.errors)
        self.assertTrue(any("recognizable host or functional cabin/bay" in e for e in checks.errors), checks.errors)

        unclear_cold = dict(self.cold, host_system_seen="仅见孤立金属台架壳体，看不出所属设备或舱室", part_in_whole_clear=False)
        unclear_rep = self.write_report(name="hook-part-unclear.json", cold_test=unclear_cold)
        checks2 = FakeChecks(self.root, self.qa(unclear_rep))
        checks2.data = plan_data
        validate_opening_hook(checks2, FULL_POLICY, "G5")
        self.assertTrue(any("recognizable host or functional cabin/bay" in e for e in checks2.errors), checks2.errors)

        cabin_cold = dict(self.cold, host_system_seen="敞门汽车驾驶室（方向盘、座椅、三点式安全带与B柱安装位）", part_in_whole_clear=True)
        cabin_rep = self.write_report(name="hook-part-cabin-clear.json", cold_test=cabin_cold)
        checks_cabin = FakeChecks(self.root, self.qa(cabin_rep))
        checks_cabin.data = plan_data
        validate_opening_hook(checks_cabin, FULL_POLICY, "G5")
        self.assertEqual(checks_cabin.errors, [])

        clear_cold = dict(self.cold, host_system_seen="完整机翼与发动机短舱外轮廓", part_in_whole_clear=True)
        clear_rep = self.write_report(name="hook-part-clear.json", cold_test=clear_cold)
        checks3 = FakeChecks(self.root, self.qa(clear_rep))
        checks3.data = plan_data
        validate_opening_hook(checks3, FULL_POLICY, "G5")
        self.assertEqual(checks3.errors, [])


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg/ffprobe unavailable")
class HookMeasurementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, name, video_filter, audio_filter):
        out = self.root / name
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", video_filter, "-f", "lavfi",
                        "-i", "sine=frequency=300:duration=3", "-filter_complex", audio_filter,
                        "-map", "0:v", "-map", "[a]", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", str(out)], check=True, capture_output=True, timeout=120)
        return out

    def test_moving_open_with_immediate_sound_has_no_flags(self):
        video = self.make("good.mp4", "testsrc2=size=640x360:rate=30:duration=3", "[1:a]anull[a]")
        report = measure(video, POLICY, preview_dir=self.root / "prev", report_path=self.root / "r.json")
        self.assertEqual(report["flags"], [])
        self.assertEqual(report["video"]["file"], "good.mp4")
        self.assertTrue((self.root / "prev" / "good-hook-strip.png").is_file())

    def test_black_static_late_sound_and_caption_are_flagged(self):
        video = self.make("bad.mp4", "color=c=black:size=640x360:rate=30:duration=3",
                          "[1:a]adelay=1000|1000[a]")
        captions = self.root / "bad.srt"
        captions.write_text("1\n00:00:00,900 --> 00:00:02,000\n测试\n", encoding="utf-8")
        flags = set(measure(video, POLICY, captions=captions)["flags"])
        self.assertTrue({"black_first_frame", "low_motion_first_half_second", "late_audio_onset",
                         "late_first_caption", "low_contrast_first_frame"} <= flags, flags)


if __name__ == "__main__":
    unittest.main()
