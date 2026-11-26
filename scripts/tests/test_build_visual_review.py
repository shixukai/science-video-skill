"""Tests for pre-render captioned beat-board review mode in scripts/build_visual_review.py."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_visual_review import (  # noqa: E402
    ReviewError,
    build_beat_board,
    extract_frame_number,
    main,
    match_cues_at_time,
    parse_srt,
    sha256,
)

SAMPLE_SRT = """\ufeff1
00:00:00,000 --> 00:00:03,200
先看谁不动、谁在动：
中间这根钢杆和底座始终锁死。

2
00:00:03,500 --> 00:00:06,800
拉起拨杆压下顶针，高压氮气通道立刻打开。

3
00:00:07,200 --> 00:00:10,500
没有对应预审静帧的台词会被明确标出。
"""


def _write_test_png(path: Path, color=(40, 120, 200)) -> None:
    try:
        from PIL import Image
        Image.new("RGB", (320, 180), color).save(path, format="PNG")
        return
    except ImportError:
        pass
    # Minimal valid 1x1 PNG fallback when Pillow is not installed.
    import struct
    import zlib

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack("!IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw = zlib.compress(b"\x00" + bytes(color))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", raw) + chunk(b"IEND", b""))


class BeatBoardTests(unittest.TestCase):
    def test_parse_srt_and_match_cues(self):
        with tempfile.TemporaryDirectory() as tmp:
            srt = Path(tmp) / "captions.srt"
            srt.write_text(SAMPLE_SRT, encoding="utf-8")
            cues = parse_srt(srt)
            self.assertEqual(len(cues), 3)
            self.assertEqual(cues[0]["start_s"], 0.0)
            self.assertEqual(cues[0]["end_s"], 3.2)
            self.assertIn("钢杆和底座", cues[0]["text"])

            exact = match_cues_at_time(cues, 1.5)
            self.assertEqual(exact["match_kind"], "exact")
            self.assertEqual(exact["cue_indices"], [1])

            margin = match_cues_at_time(cues, 3.35, margin_s=0.25)
            self.assertEqual(margin["match_kind"], "breath_margin")
            self.assertEqual(margin["cue_indices"], [1])

            silent = match_cues_at_time(cues, 20.0, margin_s=0.25)
            self.assertEqual(silent["match_kind"], "silent_gap")
            self.assertEqual(silent["cue_indices"], [])
            self.assertIn("nearest", silent["nearest_text"])

    def test_extract_frame_number_and_rejects_non_numeric(self):
        self.assertEqual(extract_frame_number(Path("frame_0001.png")), 1)
        self.assertEqual(extract_frame_number(Path("shot03_f0240.png")), 240)
        with self.assertRaises(ReviewError):
            extract_frame_number(Path("hero_still.png"))

    def test_build_beat_board_preserves_raw_stills_and_flags_uncovered_cues(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stills = root / "stills"
            stills.mkdir()
            p1 = stills / "frame_0031.png"  # (31 - 1) / 30 = 1.00s -> cue 1
            p2 = stills / "frame_0151.png"  # (151 - 1) / 30 = 5.00s -> cue 2
            _write_test_png(p1, (30, 90, 150))
            _write_test_png(p2, (160, 80, 40))
            h1, h2 = sha256(p1), sha256(p2)
            srt = root / "captions.srt"
            srt.write_text(SAMPLE_SRT, encoding="utf-8")
            out_dir = root / "beat-board-v1"

            manifest = build_beat_board(stills, srt, out_dir, fps=30, frame_origin=1, title="Test Board")
            self.assertEqual(manifest["review_status"], "internal_comprehension_review_only_not_approval")
            self.assertTrue(manifest["raw_stills_unmodified"])
            self.assertEqual(manifest["still_count"], 2)
            self.assertEqual(manifest["covered_cue_count"], 2)
            self.assertEqual(manifest["uncovered_cue_count"], 1)
            self.assertEqual(manifest["uncovered_cues"][0]["index"], 3)

            # Raw PNGs copied untouched with exact SHA-256 parity
            self.assertEqual(sha256(out_dir / "stills" / "frame_0031.png"), h1)
            self.assertEqual(sha256(out_dir / "stills" / "frame_0151.png"), h2)
            html_text = (out_dir / "beat-board.html").read_text(encoding="utf-8")
            self.assertIn("钢杆和底座", html_text)
            self.assertIn("拉起拨杆压下顶针", html_text)
            self.assertIn("Uncovered Spoken Cues (1)", html_text)
            self.assertTrue((out_dir / "manifest.json").is_file())
            if manifest["sheet_file"]:
                self.assertTrue((out_dir / manifest["sheet_file"]).is_file())
                self.assertGreater((out_dir / manifest["sheet_file"]).stat().st_size, 0)

            # Existing output directory must be rejected without overwriting
            with self.assertRaises(ReviewError):
                build_beat_board(stills, srt, out_dir, fps=30)

    def test_duplicate_frame_number_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stills = root / "stills"
            stills.mkdir()
            _write_test_png(stills / "a_0030.png")
            _write_test_png(stills / "b_0030.png")
            srt = root / "captions.srt"
            srt.write_text(SAMPLE_SRT, encoding="utf-8")
            with self.assertRaises(ReviewError):
                build_beat_board(stills, srt, root / "out", fps=30)

    def test_cli_beat_board_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stills = root / "stills"
            stills.mkdir()
            _write_test_png(stills / "f0001.png")
            srt = root / "captions.srt"
            srt.write_text(SAMPLE_SRT, encoding="utf-8")
            out_dir = root / "cli-board"
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([
                    "beat-board",
                    "--stills-dir", str(stills),
                    "--captions", str(srt),
                    "--fps", "30",
                    "--output", str(out_dir),
                ])
            self.assertEqual(rc, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["status"], "internal_comprehension_review_only_not_approval")
            self.assertEqual(payload["still_count"], 1)
            self.assertTrue(payload["raw_stills_unmodified"])


if __name__ == "__main__":
    unittest.main()
