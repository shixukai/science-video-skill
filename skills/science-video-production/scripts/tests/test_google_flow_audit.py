#!/usr/bin/env python3
"""Unit tests for scripts/google_flow_audit.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = SKILL_ROOT / "scripts" / "google_flow_audit.py"
PYTHON = sys.executable


def make_clip(path: Path, width: int = 1920, height: int = 1080, fps: int = 24, duration_s: float = 7.833) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s={width}x{height}:r={fps}:d={duration_s}",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r=48000:cl=stereo:d={duration_s}",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(fps),
        "-c:a",
        "aac",
        "-shortest",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed creating fixture {path}: {proc.stderr}")


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def run_audit(args: list[str]) -> tuple[int, dict | None, str]:
    proc = subprocess.run([PYTHON, "-X", "utf8", str(SCRIPT_PATH), "measure", *args], capture_output=True, text=True, encoding="utf-8")
    report_idx = args.index("--report") + 1
    rpath = Path(args[report_idx])
    data = json.loads(rpath.read_text(encoding="utf-8")) if rpath.is_file() else None
    return proc.returncode, data, proc.stderr


class GoogleFlowAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.clips_dir = self.root / "clips"
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        for sid in ("SH01", "SH02", "SH03"):
            make_clip(self.clips_dir / f"{sid}.mp4", 1920, 1080, 24, 7.833)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _build_clean_project(self) -> tuple[Path, Path, Path, Path, Path, Path]:
        zh_vid = self.root / "export_zh.mp4"
        en_vid = self.root / "export_en.mp4"
        make_clip(zh_vid, 1920, 1080, 24, 18.0)
        make_clip(en_vid, 1920, 1080, 24, 18.0)

        zh_srt = self.root / "captions.zh.srt"
        zh_srt.write_text(
            "1\n00:00:00,000 --> 00:00:05,200\n玻璃假体里的液体在稳定流动。\n\n"
            "2\n00:00:06,200 --> 00:00:11,500\n加热后压力把阀门顶开了一毫米。\n\n"
            "3\n00:00:12,500 --> 00:00:17,600\n冷却收缩后阀门重新回落闭合。\n",
            encoding="utf-8",
            newline="\n",
        )
        en_srt = self.root / "captions.en.srt"
        en_srt.write_text(
            "1\n00:00:00,000 --> 00:00:05,100\nFluid inside the clear glass phantom\nmoves steadily upward.\n\n"
            "2\n00:00:06,100 --> 00:00:11,400\nHeating pushes the inner valve open\nby one millimeter.\n\n"
            "3\n00:00:12,400 --> 00:00:17,500\nWhen the vessel cools down again,\nthe valve closes shut.\n",
            encoding="utf-8",
            newline="\n",
        )

        # ~72 CJK chars in 18s = 240 chars/min; ~44 EN words in 18s = ~146.7 wpm.
        zh_text = "玻璃假体里的透明液体在稳定向前流动，随着底部持续升温，膨胀压力稳步上升并把内部阀门平稳顶开，最后冷却收缩使阀门再次完全回落关闭。"
        en_text = (
            "Transparent fluid inside the clear glass phantom moves steadily forward through the channel. "
            "As heat builds from below, rising internal pressure lifts the valve smoothly open by one full millimeter. "
            "Once cooling returns the liquid back to rest, the valve settles shut cleanly."
        )
        ep_zh = self.root / "episode.zh.json"
        ep_en = self.root / "episode.en.json"
        common_design = {"production_route": "google_flow", "output": {"width": 1920, "height": 1080, "fps": 24}}
        shots_zh = [
            {"id": "SH01", "duration_s": 6.0, "observation_hold_s": 0.8},
            {"id": "SH02", "duration_s": 6.0, "observation_hold_s": 0.9},
            {"id": "SH03", "duration_s": 6.0, "observation_hold_s": 0.8},
        ]
        shots_en = [
            {"id": "SH01", "duration_s": 6.0, "observation_hold_s": 0.8},
            {"id": "SH02", "duration_s": 6.0, "observation_hold_s": 0.9},
            {"id": "SH03", "duration_s": 6.0, "observation_hold_s": 0.8},
        ]
        write_json(ep_zh, {"design": common_design, "narration": {"language": "zh", "text": zh_text}, "shots": shots_zh, "captions": {"file": "captions.zh.srt", "wrap_style": 2, "font_size": 22}})
        write_json(ep_en, {"design": common_design, "narration": {"language": "en", "text": en_text}, "shots": shots_en, "captions": {"file": "captions.en.srt", "wrap_style": 0}})
        return zh_vid, en_vid, ep_zh, ep_en, zh_srt, en_srt

    def test_clean_bilingual_pass(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, _, _ = self._build_clean_project()
        report = self.root / "report_clean.json"
        code, data, err = run_audit([
            str(zh_vid),
            "--en-video",
            str(en_vid),
            "--episode-zh",
            str(ep_zh),
            "--episode-en",
            str(ep_en),
            "--clips-dir",
            str(self.clips_dir),
            "--report",
            str(report),
        ])
        self.assertEqual(code, 0, f"Unexpected stderr/flags: {err} {data}")
        self.assertEqual(data["status"], "clean")
        self.assertEqual(data["flags"], [])

    def test_clips_only_catches_720p(self) -> None:
        make_clip(self.clips_dir / "SH04.mp4", 1280, 720, 24, 7.917)
        report = self.root / "report_720.json"
        code, data, _ = run_audit(["--clips-only", "--clips-dir", str(self.clips_dir), "--report", str(report)])
        self.assertEqual(code, 1)
        self.assertIn("low_res_source_clip", data["summary"]["flag_codes"])

    def test_catches_clip_duration_overrun_and_fps_cadence_and_mismatch(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, _, _ = self._build_clean_project()
        make_clip(en_vid, 1920, 1080, 30, 12.0)
        ep_zh_data = json.loads(ep_zh.read_text(encoding="utf-8"))
        ep_zh_data["shots"][1]["duration_s"] = 10.5  # > 7.833 s native clip
        ep_zh_data["narration"]["text"] = "高" * 110  # ~366 chars/min
        for s in ep_zh_data["shots"]:
            s["observation_hold_s"] = 0.0
        write_json(ep_zh, ep_zh_data)

        ep_en_data = json.loads(ep_en.read_text(encoding="utf-8"))
        ep_en_data["shots"] = ep_en_data["shots"][:2]  # mismatched shot count/order
        write_json(ep_en, ep_en_data)

        report = self.root / "report_bad.json"
        code, data, _ = run_audit([
            str(zh_vid),
            "--en-video",
            str(en_vid),
            "--episode-zh",
            str(ep_zh),
            "--episode-en",
            str(ep_en),
            "--clips-dir",
            str(self.clips_dir),
            "--report",
            str(report),
        ])
        self.assertEqual(code, 1)
        codes = set(data["summary"]["flag_codes"])
        self.assertIn("clip_duration_overrun", codes)
        self.assertIn("fps_cadence_mismatch", codes)
        self.assertIn("speech_rate_out_of_range", codes)
        self.assertIn("missing_observation_holds", codes)
        self.assertIn("shot_sequence_mismatch", codes)
        self.assertIn("edition_duration_divergence", codes)

    def test_refuses_overwrite_existing_report(self) -> None:
        report = self.root / "existing.json"
        report.write_text("{\"keep\": true}\n", encoding="utf-8")
        code, data, err = run_audit(["--clips-only", "--clips-dir", str(self.clips_dir), "--report", str(report)])
        self.assertEqual(code, 2)
        self.assertIn("Refusing to overwrite", err)
        self.assertEqual(data, {"keep": True})

    def test_missing_bilingual_and_caption_wrap_and_allow_fps(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, zh_srt, _ = self._build_clean_project()
        report_single = self.root / "report_single.json"
        code1, data1, _ = run_audit([str(zh_vid), "--episode-zh", str(ep_zh), "--clips-dir", str(self.clips_dir), "--report", str(report_single)])
        self.assertEqual(code1, 1)
        self.assertIn("missing_bilingual_edition", data1["summary"]["flag_codes"])

        # Bad WrapStyle on zh episode + caption past end
        zh_srt.write_text(zh_srt.read_text(encoding="utf-8") + "\n4\n00:00:18,200 --> 00:00:22,500\n超时字幕。\n", encoding="utf-8")
        ep_zh_data = json.loads(ep_zh.read_text(encoding="utf-8"))
        ep_zh_data["captions"]["wrap_style"] = 0
        write_json(ep_zh, ep_zh_data)

        report_cap = self.root / "report_cap.json"
        code2, data2, _ = run_audit([
            str(zh_vid),
            "--en-video",
            str(en_vid),
            "--episode-zh",
            str(ep_zh),
            "--episode-en",
            str(ep_en),
            "--clips-dir",
            str(self.clips_dir),
            "--report",
            str(report_cap),
        ])
        self.assertEqual(code2, 1)
        self.assertIn("caption_sync_or_wrap_issue", data2["summary"]["flag_codes"])

        # Test --allow-fps-conversion permits 30fps without emitting fps_cadence_mismatch
        zh_30 = self.root / "zh_30.mp4"
        en_30 = self.root / "en_30.mp4"
        make_clip(zh_30, 1920, 1080, 30, 18.0)
        make_clip(en_30, 1920, 1080, 30, 18.0)
        ep_zh_clean, ep_en_clean = self._build_clean_project()[2:4]
        report_30 = self.root / "report_30.json"
        code3, data3, _ = run_audit([
            str(zh_30),
            "--en-video",
            str(en_30),
            "--episode-zh",
            str(ep_zh_clean),
            "--episode-en",
            str(ep_en_clean),
            "--clips-dir",
            str(self.clips_dir),
            "--allow-fps-conversion",
            "--report",
            str(report_30),
        ])
        self.assertEqual(code3, 0, f"Expected clean with --allow-fps-conversion, got {data3}")


if __name__ == "__main__":
    unittest.main()
