"""Synthetic media verifies extraction and provenance, never visual quality."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/science-video-production/scripts/build_visual_review.py"
SPEC = importlib.util.spec_from_file_location("build_visual_review", SCRIPT)
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "local ffmpeg/ffprobe are required")
class VisualReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory(prefix="visual-review-fixture-")
        cls.source = Path(cls.fixture.name) / "source.mp4"
        subprocess.run([
            "ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i",
            "testsrc2=size=64x48:rate=4:duration=2", "-an", "-c:v", "libx264",
            "-bf", "0", "-pix_fmt", "yuv420p", str(cls.source),
        ], check=True, capture_output=True, timeout=30)
        cls.rotated = Path(cls.fixture.name) / "rotated.mp4"
        cls.anamorphic = Path(cls.fixture.name) / "anamorphic.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-display_rotation", "90", "-i", str(cls.source),
                        "-c", "copy", str(cls.rotated)], check=True, capture_output=True, timeout=30)
        subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(cls.source), "-vf", "setsar=2/1",
                        "-c:v", "libx264", "-bf", "0", str(cls.anamorphic)],
                       check=True, capture_output=True, timeout=30)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="visual-review-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.media = self.root / "video.mp4"
        shutil.copyfile(self.source, self.media)
        self.episode = self.root / "episode.json"
        self.output = self.root / "review-v1"
        self.data = {"title": "静帧回归测试", "qa": {"status": "pending"}, "shots": [
            {"id": "SH1", "visual_note": "第一镜", "shotbook": {"start": 0, "end": 1, "subject": "对象"}},
            {"id": "SH2", "visual_note": "第二镜", "shotbook": {"start": 1, "end": 2, "action": "变化"}},
        ]}
        self.save()

    def save(self):
        self.episode.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")

    def build(self, **kwargs):
        return review.build_review(self.episode, kwargs.get("media", "video.mp4"),
                                   kwargs.get("output", "review-v1"))

    def assert_no_output(self):
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".visual-review-*")), [])

    def test_real_video_without_audio_builds_ordered_full_frames_and_bound_evidence(self):
        original = self.episode.read_bytes()
        manifest = self.build()
        self.assertEqual(manifest["status"], "generated_for_review")
        self.assertEqual([shot["id"] for shot in manifest["shots"]], ["SH1", "SH2"])
        samples = [sample for shot in manifest["shots"] for sample in shot["samples"]]
        self.assertEqual([sample["position"] for sample in samples], ["start", "mid", "end"] * 2)
        self.assertEqual([sample["requested_seconds"] for sample in samples], [0, 0.5, 1, 1, 1.5, 2])
        self.assertEqual([sample["frame_seconds"] for sample in samples], [0, 0.5, 0.75, 1, 1.5, 1.75])
        self.assertLess(samples[-1]["frame_seconds"], manifest["media"]["duration_seconds"])
        for sample in samples:
            image = self.output / sample["file"]
            self.assertEqual(review.sha256(image), sample["sha256"])
            # PNG IHDR confirms native full-frame dimensions, without Pillow.
            self.assertEqual(struct.unpack(">II", image.read_bytes()[16:24]), (64, 48))
        self.assertEqual(manifest["episode"]["sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(manifest["media"]["sha256"], review.sha256(self.media))
        self.assertEqual(manifest["media"]["geometry"], {
            "coded_width": 64, "coded_height": 48, "display_width": 64, "display_height": 48,
            "sample_aspect_ratio": "1:1", "display_aspect_ratio": "4:3", "rotation_degrees": 0,
            "display_transform": "identity"})
        self.assertEqual(manifest["coverage"]["uncovered_intervals"], [])
        self.assertEqual(set(manifest["tools"]), {"ffmpeg", "ffprobe"})
        self.assertEqual(self.episode.read_bytes(), original)
        self.assertEqual(json.loads((self.output / "manifest.json").read_text()), manifest)
        evidence = json.loads((self.output / "gate-evidence.json").read_text())
        self.assertEqual(len(evidence), 8)  # manifest, HTML, six frames; no self-reference
        for item in evidence:
            self.assertEqual(review.sha256(self.root / item["file"]), item["sha256"])
        self.assertFalse(any(item["file"].endswith("gate-evidence.json") for item in evidence))
        self.assertEqual({item["file"] for item in manifest["output_files"]},
                         {"index.html", *(sample["file"] for sample in samples)})
        page = (self.output / "index.html").read_text()
        self.assertIn('href="#shot-0001"', page)
        self.assertIn('id="shot-0001"', page)
        self.assertEqual(page.count('src="frames/0001-mid.png"'), 2)  # overview reuses the detail frame

    def test_html_escapes_episode_content_and_does_not_embed_executable_input(self):
        payload = '<script>alert("x")</script><img src=x onerror=alert(1)>'
        self.data["title"] = payload
        self.data["shots"][0].update(id=payload, visual_note=payload)
        self.data["shots"][0]["shotbook"]["subject"] = payload
        self.save()
        self.build()
        page = (self.output / "index.html").read_text()
        self.assertNotIn("<script", page)
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("Content-Security-Policy", page)
        self.assertIn("不能证明动态", page)
        self.assertIn("frames/0001-start.png", page)

    def test_invalid_plans_and_timing_fail_without_completed_output(self):
        valid = copy.deepcopy(self.data)
        cases = [
            ({"start": None, "end": None}, "null plans"),
            ({"start": 0, "end": 1, "timing_basis": {"mode": "relative_plan"}}, "relative_plan"),
            ({"start": True, "end": 1}, "non-boolean"),
            ({"start": 0, "end": float("inf")}, "finite"),
            ({"start": float("nan"), "end": 1}, "finite"),
            ({"start": -1, "end": 1}, "start < end"),
            ({"start": 1, "end": 1}, "start < end"),
            ({"start": 0, "end": 3}, "actual video duration"),
        ]
        for book, message in cases:
            with self.subTest(book=book):
                self.data = copy.deepcopy(valid)
                self.data["shots"][0]["shotbook"] = book
                self.save()
                with self.assertRaisesRegex(review.ReviewError, message):
                    self.build()
                self.assert_no_output()
        for start in (0.5, 0):
            self.data = copy.deepcopy(valid)
            self.data["shots"][1]["shotbook"]["start"] = start
            self.save()
            with self.assertRaisesRegex(review.ReviewError, "overlap|order"):
                self.build()
            self.assert_no_output()

    def test_output_cannot_overwrite_existing_directory_or_follow_symlink(self):
        self.output.mkdir()
        accepted = self.output / "accepted.txt"
        accepted.write_text("keep this review")
        with self.assertRaisesRegex(review.ReviewError, "already exists"):
            self.build()
        self.assertEqual(accepted.read_text(), "keep this review")
        alternate = self.root / "review-link"
        alternate.symlink_to(self.root / "missing-review", target_is_directory=True)
        with self.assertRaisesRegex(review.ReviewError, "already exists"):
            self.build(output=alternate)
        self.assertFalse((self.root / "missing-review").exists())

    def test_paths_cannot_escape_episode_directory_including_symlinks(self):
        self.root.joinpath("outside-video.mp4").symlink_to(self.source)
        for media in (str(self.source), "../outside.mp4", "outside-video.mp4"):
            with self.subTest(media=media):
                with self.assertRaisesRegex(review.ReviewError, "relative|inside"):
                    self.build(media=media)
                self.assert_no_output()
        with self.assertRaisesRegex(review.ReviewError, "inside"):
            self.build(output="../outside-review")
        self.assert_no_output()

    def test_failed_extraction_removes_staging_and_does_not_publish(self):
        real_run = review.run_tool

        def fail_extraction(command):
            if "-vf" in command:
                raise review.ReviewError("simulated extraction failure")
            return real_run(command)

        with mock.patch.object(review, "run_tool", side_effect=fail_extraction):
            with self.assertRaisesRegex(review.ReviewError, "simulated"):
                self.build()
        self.assert_no_output()

    def test_input_change_during_extraction_prevents_publication(self):
        real_run = review.run_tool

        def mutate_input(command):
            result = real_run(command)
            if "-vf" in command:
                self.episode.write_bytes(self.episode.read_bytes() + b"\n")
            return result

        with mock.patch.object(review, "run_tool", side_effect=mutate_input):
            with self.assertRaisesRegex(review.ReviewError, "changed during extraction"):
                self.build()
        self.assert_no_output()

    def test_timeline_digest_ignores_later_qa_record_edits(self):
        first = self.build()
        self.data["qa"]["note"] = "new review record does not alter timing"
        self.save()
        second = self.build(output="review-v2")
        self.assertNotEqual(first["episode"]["sha256"], second["episode"]["sha256"])
        self.assertEqual(first["timeline_sha256"], second["timeline_sha256"])

    def test_vfr_and_short_shots_select_displayed_frames_without_eof_sampling(self):
        data = {"shots": [{"id": "short", "shotbook": {"start": 0.2, "end": 0.3}},
                          {"id": "tail", "shotbook": {"start": 0.3, "end": 2}}]}
        shots = review.shot_samples(data, 2, [0, 0.1, 0.8, 1.9])
        self.assertEqual([item["frame_seconds"] for item in shots[0]["samples"]], [0.1, 0.1, 0.1])
        self.assertEqual(shots[1]["samples"][-1]["frame_seconds"], 1.9)

    def test_real_short_shot_reuses_one_decoded_frame_for_three_positions(self):
        self.data["shots"] = [{"id": "short", "shotbook": {"start": 0.1, "end": 0.2}}]
        self.save()
        manifest = self.build()
        samples = manifest["shots"][0]["samples"]
        self.assertEqual([sample["frame_index"] for sample in samples], [0, 0, 0])
        self.assertEqual(len({sample["sha256"] for sample in samples}), 1)
        self.assertEqual(len(list((self.output / "frames").glob("*.png"))), 3)
        self.assertEqual(manifest["coverage"], {"video_duration_seconds": 2,
                         "listed_intervals": [[0.1, 0.2]], "uncovered_intervals": [[0, 0.1], [0.2, 2]]})
        page = (self.output / "index.html").read_text()
        self.assertIn("所列镜头总览", page)
        self.assertNotIn("整期总览", page)
        self.assertIn("未覆盖区间：0.000–0.100s、0.200–2.000s", page)

    def test_gaps_are_reported_without_claiming_full_episode_coverage(self):
        self.data["shots"][0]["shotbook"].update(start=0.1, end=0.5)
        self.data["shots"][1]["shotbook"].update(start=1, end=1.5)
        self.save()
        manifest = self.build()
        self.assertEqual(manifest["coverage"]["uncovered_intervals"], [[0, 0.1], [0.5, 1], [1.5, 2]])

    def test_real_rotation_and_non_square_pixels_are_rejected_without_outputs(self):
        for source, message in ((self.rotated, "display matrix|rotation"),
                                (self.anamorphic, "sample aspect ratio")):
            with self.subTest(source=source.name):
                shutil.copyfile(source, self.media)
                before = review.sha256(self.media)
                with self.assertRaisesRegex(review.ReviewError, message) as caught:
                    self.build()
                self.assertIn("review copy", str(caught.exception))
                self.assertEqual(review.sha256(self.media), before)
                self.assert_no_output()

    def test_local_playlists_cannot_load_media_outside_the_episode(self):
        playlist = self.root / "indirect.ffconcat"
        playlist.write_text("ffconcat version 1.0\nfile '" + str(self.source) + "'\n")
        with self.assertRaisesRegex(review.ReviewError, "ffprobe failed"):
            self.build(media=playlist.name)
        self.assert_no_output()

    def test_cli_uses_episode_relative_paths_from_other_working_directory(self):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.episode), "--media", "video.mp4",
                                 "--output", "review-v1"], cwd=self.fixture.name,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["review"], "pending")
        self.assertTrue((self.output / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
