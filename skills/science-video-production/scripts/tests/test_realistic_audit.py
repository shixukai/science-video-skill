"""Realistic edit audit tests on synthetic numbers and synthetic media only."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import realistic_audit as ra

POLICY = ra.load_policy()
HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


class PolicyAndParsingTests(unittest.TestCase):
    def test_policy_points_to_owner_and_tool(self):
        root = Path(__file__).resolve().parents[2]
        policy = json.loads((root / "config/production-policy.json").read_text(encoding="utf-8"))["realistic_audit"]
        owner, _, anchor = policy["owner"].partition("#")
        self.assertTrue((root / owner).is_file())
        self.assertIn("## Measure the edit before judging it", (root / owner).read_text(encoding="utf-8"))
        self.assertEqual(anchor, "measure-the-edit-before-judging-it")
        self.assertTrue((root / policy["measurement_tool"]).is_file())
        self.assertTrue(policy["measurement_is_not_acceptance"])
        self.assertEqual(policy["required_stages"], [])

    def test_parse_rate(self):
        self.assertAlmostEqual(ra.parse_rate("30000/1001"), 29.97, places=2)
        self.assertEqual(ra.parse_rate("30/1"), 30.0)
        self.assertIsNone(ra.parse_rate("0/0"))
        self.assertIsNone(ra.parse_rate("bad"))

    def test_shots_file_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shots.json"
            path.write_text(json.dumps([{"id": "A", "start_s": 0, "scene": "kitchen"},
                                        {"id": "B", "start_s": 2.0, "scene": "kitchen"}]))
            shots = ra.build_shots(ra.load_shots(path, 30, 120), 120)
            self.assertEqual([(s["id"], s["start"], s["end"], s["scene"]) for s in shots],
                             [("A", 0, 60, "kitchen"), ("B", 60, 120, "kitchen")])
            for bad in ([], [{"id": "A", "start_s": 1.0}], [{"id": "A", "start_s": 0}, {"id": "A", "start_s": 1}],
                        [{"id": "A", "start_s": 0}, {"id": "B", "start_s": 9}],
                        [{"id": "A", "start_s": 0}, {"id": "B", "start_s": True}]):
                path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError, msg=bad):
                    ra.load_shots(path, 30, 120)


class ScreeningLogicTests(unittest.TestCase):
    def test_uniform_cadence_needs_a_run_of_similar_lengths(self):
        cfg = POLICY["cadence"]
        self.assertEqual(ra.cadence_runs([5.0, 5.1, 4.9, 5.0, 2.0], cfg), [(0, 4)])
        self.assertEqual(ra.cadence_runs([1.4, 3.2, 2.1, 5.0, 2.6], cfg), [])
        # Very short montage beats are below the length floor and do not form a cadence run.
        self.assertEqual(ra.cadence_runs([0.5, 0.5, 0.5, 0.5, 0.5], cfg), [])
        # A slow drift is not a uniform run.
        self.assertEqual(ra.cadence_runs([2.0, 2.2, 2.4, 2.65, 2.9], cfg), [])

    def test_duplicates_only_count_inside_motion(self):
        cfg = POLICY["duplicate"]
        moving = [0.0] + [0.02, 0.02, 0.02, 0.02, 0.0] * 6 + [0.02]
        dups, total, ratio, _ = ra.duplicate_frames(moving, set(), cfg)
        self.assertGreaterEqual(dups, 5)
        self.assertGreater(ratio, cfg["ratio_max"])
        static = [0.0] * 40
        self.assertEqual(ra.duplicate_frames(static, set(), cfg)[0], 0)

    def test_cut_detection_uses_local_contrast(self):
        diffs = [0.0] + [0.01] * 29 + [0.4] + [0.01] * 29
        self.assertEqual(ra.detect_cuts(diffs, 30, POLICY["cut_detection"]), [30])
        busy = [0.0] + [0.15] * 59
        self.assertEqual(ra.detect_cuts(busy, 30, POLICY["cut_detection"]), [])

    def test_ramp_head_and_frozen_tail(self):
        fps = 30
        diffs = [0.0] + [0.0005] * 12 + [0.02] * 60 + [0.0] * 12
        shot = {"start": 0, "end": len(diffs)}
        flags, body = ra.shot_motion_flags(diffs, shot, fps, POLICY["ramp_head"], POLICY["frozen_tail"])
        self.assertEqual(set(flags), {"slow_ramp_head", "frozen_tail"})
        steady = [0.0] + [0.02] * 84
        self.assertEqual(ra.shot_motion_flags(steady, {"start": 0, "end": 85}, fps,
                                              POLICY["ramp_head"], POLICY["frozen_tail"])[0], {})
        # A deliberately static locked-off shot is not a ramp or a freeze.
        still = [0.0] + [0.0002] * 84
        self.assertEqual(ra.shot_motion_flags(still, {"start": 0, "end": 85}, fps,
                                              POLICY["ramp_head"], POLICY["frozen_tail"])[0], {})

    def test_silence_gaps(self):
        rate = ra.AUDIO_RATE
        tone = [8000, -8000] * (rate // 2)
        samples = tone + [0] * (rate // 2) + tone
        gaps = ra.silence_gaps(samples, POLICY["digital_silence"]["gate_dbfs"], POLICY["digital_silence"]["min_s"])
        self.assertEqual(len(gaps), 1)
        self.assertAlmostEqual(gaps[0][0], 1.0, places=1)
        self.assertAlmostEqual(gaps[0][1], 1.5, places=1)
        quiet_room = [40, -40] * rate
        self.assertEqual(ra.silence_gaps(quiet_room, -70, 0.15), [])


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg/ffprobe unavailable")
class AuditMeasurementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, name, inputs, graph, audio=True):
        args = ["ffmpeg", "-v", "error", "-y"]
        for src in inputs:
            args += ["-f", "lavfi", "-i", src]
        if audio:
            args += ["-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000"]
        args += ["-filter_complex", graph, "-map", "[v]"]
        if audio:
            args += ["-map", f"{len(inputs)}:a", "-shortest", "-c:a", "aac"]
        out = self.root / name
        args += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", str(out)]
        subprocess.run(args, check=True, capture_output=True, timeout=180)
        return out

    def src(self, seconds, rate=30):
        return f"testsrc2=size=160x90:rate={rate}:duration={seconds}"

    def test_clean_continuous_export_has_no_flags(self):
        video = self.make("clean.mp4", [self.src(4)], "[0:v]null[v]")
        report = ra.measure(video, POLICY, report_path=self.root / "r.json")
        self.assertEqual(report["flags"], [])
        self.assertEqual(report["video"]["file"], "clean.mp4")
        self.assertEqual(report["cut_source"], "detected")

    def test_converted_24fps_motion_is_flagged(self):
        video = self.make("dup.mp4", [self.src(4, 24)], "[0:v]fps=30[v]")
        self.assertIn("duplicate_frames_in_motion", ra.measure(video, POLICY)["flags"])

    def test_ramp_head_frozen_tail_and_no_audio(self):
        video = self.make("ramp.mp4", [self.src(3)],
                          "[0:v]tpad=start_mode=clone:start_duration=0.6:stop_mode=clone:stop_duration=0.6[v]",
                          audio=False)
        report = ra.measure(video, POLICY, preview_dir=self.root / "prev", report_path=self.root / "ramp.json")
        flags = set(report["flags"])
        self.assertTrue({"slow_ramp_head", "frozen_tail", "no_audio_stream"} <= flags, flags)
        shot_findings = [f for f in report["findings"] if f["flag"] in ("slow_ramp_head", "frozen_tail")]
        self.assertTrue(all(f["shot_id"] == "auto-1" for f in shot_findings))
        self.assertEqual(len(report["previews"]), 2)
        self.assertTrue(all((self.root / p).is_file() for p in report["previews"]))

    def test_grade_jump_only_inside_labeled_scene(self):
        video = self.make("jump.mp4", [self.src(2), self.src(2)],
                          "[1:v]eq=brightness=0.3:saturation=0.4[b];[0:v][b]concat=n=2:v=1:a=0[v]")
        same = self.root / "same.json"
        same.write_text(json.dumps([{"id": "A", "start_s": 0, "scene": "kitchen"},
                                    {"id": "B", "start_s": 2.0, "scene": "kitchen"}]))
        other = self.root / "other.json"
        other.write_text(json.dumps([{"id": "A", "start_s": 0, "scene": "kitchen"},
                                     {"id": "B", "start_s": 2.0, "scene": "street"}]))
        preview = self.root / "prev"
        report = ra.measure(video, POLICY, shots_path=same, preview_dir=preview, report_path=self.root / "j.json")
        self.assertIn("grade_jump_in_scene", report["flags"])
        self.assertTrue(report["previews"] and (self.root / report["previews"][0]).is_file())
        self.assertNotIn("grade_jump_in_scene", ra.measure(video, POLICY, shots_path=other)["flags"])

    def test_cli_refuses_existing_report_and_flags_silence(self):
        video = self.root / "silence.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", self.src(3), "-f", "lavfi", "-i",
                        "sine=frequency=300:sample_rate=48000:duration=3", "-filter_complex",
                        "[1:a]volume=enable='between(t,1.0,1.6)':volume=0[a]", "-map", "0:v", "-map", "[a]",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(video)],
                       check=True, capture_output=True, timeout=180)
        report = self.root / "audit.json"
        self.assertEqual(ra.main(["measure", str(video), "--report", str(report)]), 1)
        self.assertIn("digital_silence", json.loads(report.read_text(encoding="utf-8"))["flags"])
        self.assertEqual(ra.main(["measure", str(video), "--report", str(report)]), 2)


if __name__ == "__main__":
    unittest.main()
