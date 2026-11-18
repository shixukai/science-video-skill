"""Offline unit tests for scripts/synthesize_edge_tts.py default voice adapter."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import synthesize_edge_tts as edge_adapter

HAS_FFMPEG = bool(shutil.which("ffmpeg"))


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg unavailable")
class SynthesizeEdgeTtsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.sample_mp3 = self.root / "fixture.mp3"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=220:duration=1.2",
                "-c:a",
                "libmp3lame",
                str(self.sample_mp3),
            ],
            check=True,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_profile_defaults_to_yunxi_plus4_and_writes_valid_record_and_srt(self) -> None:
        defaults = edge_adapter.load_profile_defaults(edge_adapter.DEFAULT_PROFILE)
        self.assertEqual(defaults["speaker"], "zh-CN-YunxiNeural")
        self.assertEqual(defaults["rate"], "+4%")

        script = self.root / "script.zh.txt"
        script.write_text("山坡的斜石上，稳稳停着几颗方方正正的粪粒。袋熊末端只是柔软圆环。\n", encoding="utf-8")
        out_wav = self.root / "voice.zh.wav"
        rec_json = self.root / "voice.zh.generation.json"
        srt_out = self.root / "captions.zh.srt"

        async def fake_stream(text: str, voice: str, rate: str, pitch: str, volume: str, mp3_path: Path):
            self.assertEqual(voice, "zh-CN-YunxiNeural")
            self.assertEqual(rate, "+4%")
            mp3_path.write_bytes(self.sample_mp3.read_bytes())
            return [
                {"type": "SentenceBoundary", "offset_s": 0.05, "duration_s": 0.65, "text": "山坡的斜石上，稳稳停着几颗方方正正的粪粒。"},
                {"type": "SentenceBoundary", "offset_s": 0.75, "duration_s": 0.40, "text": "袋熊末端只是柔软圆环。"},
            ]

        with mock.patch.object(edge_adapter, "_stream_edge_tts", side_effect=fake_stream):
            rec = edge_adapter.synthesize_edge(
                text_file=script,
                output_wav=out_wav,
                record_path=rec_json,
                confirmation_reference="series default v1.6.30",
                srt_out=srt_out,
            )

        self.assertEqual(rec["provider"], "Microsoft Edge")
        self.assertEqual(rec["backend"], "edge-tts")
        self.assertEqual(rec["voice"]["speaker"], "zh-CN-YunxiNeural")
        self.assertEqual(rec["voice"]["rate"], "+4%")
        self.assertTrue(out_wav.is_file() and out_wav.stat().st_size > 1000)
        self.assertTrue(srt_out.is_file() and "稳稳停着几颗方方正正的粪粒" in srt_out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
