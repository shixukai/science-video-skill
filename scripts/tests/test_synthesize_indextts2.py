"""Offline unit tests for scripts/synthesize_indextts2.py (#5 voice clone adapter)."""
from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import synthesize_indextts2 as idx_adapter


def _write_sine_wav(path: Path, duration_s: float = 0.6, rate: int = 22050, freq: float = 220.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nframes = int(round(duration_s * rate))
    frames = bytearray()
    for i in range(nframes):
        val = int(round(0.2 * math.sin(2 * math.pi * freq * i / rate) * 32767))
        frames.extend(struct.pack("<h", val))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(bytes(frames))


def _create_fake_project(proj_dir: Path) -> tuple[Path, Path]:
    ckpt = proj_dir / "checkpoints"
    ckpt.mkdir(parents=True, exist_ok=True)
    cfg = ckpt / "config.yaml"
    cfg.write_text("version: 2.5\n", encoding="utf-8")
    for fname in ("gpt.pth", "codec.pth", "s2mel.pth"):
        (ckpt / fname).write_bytes(b"fake-weight")
    hf = ckpt / "hf_cache"
    (hf / "w2v-bert-2.0").mkdir(parents=True, exist_ok=True)
    (hf / "w2v-bert-2.0" / "config.json").write_text("{}", encoding="utf-8")
    (hf / "bigvgan").mkdir(parents=True, exist_ok=True)
    (hf / "bigvgan" / "config.json").write_text("{}", encoding="utf-8")
    (hf / "campplus_cn_common.bin").write_bytes(b"fake-campplus")
    git_dir = proj_dir / ".git"
    git_dir.mkdir(exist_ok=True)
    (git_dir / "HEAD").write_text("d" * 40 + "\n", encoding="utf-8")
    return ckpt, cfg


class SynthesizeIndexTTS2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.proj_dir = self.root / "indextts2-checkout"
        self.ckpt_dir, self.cfg_path = _create_fake_project(self.proj_dir)
        self.ref_prompt = self.root / "private-prompt-13s.wav"
        _write_sine_wav(self.ref_prompt, duration_s=1.0, rate=48000)
        self.script = self.root / "script.zh.txt"
        self.script.write_text(
            "铁钉淋雨会生锈，那为什么不锈钢却能稳稳亮着？\n\n"
            "因为里面加入了<铬|GE4>，能迅速形成致密的保护膜。\n",
            encoding="utf-8",
            newline="\n",
        )
        self.out_wav = self.root / "ep" / "raw-voice.wav"
        self.rec_json = self.root / "ep" / "raw-voice.generation.json"
        self.srt_out = self.root / "ep" / "captions.zh.srt"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_profile_defaults_match_number5_settings(self) -> None:
        defaults = idx_adapter.load_profile_defaults(idx_adapter.DEFAULT_PROFILE)
        self.assertEqual(defaults["model_id"], "IndexTeam/IndexTTS-2.5")
        self.assertEqual(defaults["voice_preset_id"], "mandarin-indextts25-clone-polished-v1")
        self.assertEqual(defaults["speaker"], "user_clone")
        self.assertEqual(defaults["lang"], "ZH")
        self.assertEqual(defaults["duration_factor"], 1.0)
        self.assertEqual(defaults["interval_silence"], 220)
        self.assertEqual(defaults["paragraph_silence_s"], 0.55)
        self.assertFalse(defaults["use_emo_text"])
        self.assertTrue(defaults["use_bf16"])
        self.assertFalse(defaults["use_cuda_kernel"])
        self.assertFalse(defaults["use_qwen_emo"])
        self.assertEqual(defaults["speech_polish_preset"], "mandarin-clone-polish-v1")

    def test_missing_local_execution_without_baseline_fails_explicitly(self) -> None:
        with self.assertRaises(idx_adapter.SynthesisError) as ctx:
            idx_adapter.synthesize_indextts2(
                text_file=self.script,
                output_wav=self.out_wav,
                record_path=self.rec_json,
                use_baseline=False,
            )
        self.assertIn("project-dir", str(ctx.exception))

        with self.assertRaises(idx_adapter.SynthesisError) as ctx2:
            idx_adapter.synthesize_indextts2(
                text_file=self.script,
                output_wav=self.out_wav,
                record_path=self.rec_json,
                project_dir=self.proj_dir,
                use_baseline=False,
            )
        self.assertIn("reference voice prompt", str(ctx2.exception))

    def test_refuses_to_overwrite_existing_output_or_record(self) -> None:
        self.out_wav.parent.mkdir(parents=True, exist_ok=True)
        self.out_wav.write_bytes(b"existing audio")
        with self.assertRaises(FileExistsError):
            idx_adapter.synthesize_indextts2(
                text_file=self.script,
                output_wav=self.out_wav,
                record_path=self.rec_json,
                project_dir=self.proj_dir,
                reference_prompt=self.ref_prompt,
                confirmation_reference="test ref",
                use_baseline=False,
            )
        self.assertEqual(self.out_wav.read_bytes(), b"existing audio")
        self.out_wav.unlink()

        self.rec_json.write_bytes(b"existing record")
        with self.assertRaises(FileExistsError):
            idx_adapter.synthesize_indextts2(
                text_file=self.script,
                output_wav=self.out_wav,
                record_path=self.rec_json,
                project_dir=self.proj_dir,
                reference_prompt=self.ref_prompt,
                confirmation_reference="test ref",
                use_baseline=False,
            )
        self.assertEqual(self.rec_json.read_bytes(), b"existing record")

    def test_private_baseline_resolution(self) -> None:
        baseline_file = self.root / "voice-baseline.json"
        baseline_payload = {
            "schema_version": 1,
            "preset_id": "mandarin-indextts25-clone-polished-v1",
            "provider": "IndexTTS",
            "backend": "local_indextts2",
            "execution": {
                "status": "confirmed",
                "mode": "local_project",
                "location": str(self.proj_dir),
                "checkpoints_dir": str(self.ckpt_dir),
                "cfg_path": str(self.cfg_path),
                "confirmation_reference": "private baseline #5",
            },
            "voice": {
                "speaker": "user_clone",
                "language": "Chinese",
                "reference_prompt": {"file": str(self.ref_prompt)},
            },
            "load_parameters": {"use_bf16": True, "use_cuda_kernel": False, "use_qwen_emo": False},
            "generation_params": {"lang": "ZH", "duration_factor": 1.0, "interval_silence": 220, "paragraph_silence_s": 0.55, "use_emo_text": False},
        }
        baseline_file.write_text(json.dumps(baseline_payload), encoding="utf-8")
        resolved = idx_adapter.resolve_baseline(baseline_file, use_baseline=True)
        self.assertEqual(resolved["execution"]["location"], str(self.proj_dir))
        self.assertEqual(idx_adapter.resolve_baseline(baseline_file, use_baseline=False), {})

        init_calls: list[dict] = []
        infer_calls: list[dict] = []

        class FakeIndexTTS2:
            device = "cuda:0"

            def __init__(self, **kwargs) -> None:
                init_calls.append(kwargs)

            def infer(self, **kwargs) -> None:
                infer_calls.append(kwargs)
                _write_sine_wav(Path(kwargs["output_path"]), duration_s=0.8, rate=22050)

        prev_cwd = Path.cwd()
        with mock.patch.object(idx_adapter, "load_indextts2_class", return_value=FakeIndexTTS2):
            rec = idx_adapter.synthesize_indextts2(
                text_file=self.script,
                output_wav=self.out_wav,
                record_path=self.rec_json,
                baseline_path=baseline_file,
                use_baseline=True,
                srt_out=self.srt_out,
            )

        self.assertEqual(Path.cwd(), prev_cwd)
        self.assertEqual(len(init_calls), 1)
        self.assertFalse(init_calls[0]["use_qwen_emo"])
        self.assertTrue(init_calls[0]["use_bf16"])
        self.assertEqual(len(infer_calls), 2)
        self.assertEqual(infer_calls[0]["text"], "铁钉淋雨会生锈，那为什么不锈钢却能稳稳亮着？")
        self.assertIn("<铬|GE4>", infer_calls[1]["text"])
        self.assertFalse(infer_calls[0]["use_emo_text"])
        self.assertEqual(infer_calls[0]["duration_factor"], 1.0)
        self.assertEqual(infer_calls[0]["interval_silence"], 220)

        # Total duration = 0.8 + 0.55 + 0.8 = 2.15 s
        info = idx_adapter.probe_wav_info(self.out_wav)
        self.assertAlmostEqual(info["duration_seconds"], 2.15, delta=0.01)

        self.assertEqual(rec["provider"], "IndexTTS")
        self.assertEqual(rec["backend"], "local_indextts2")
        self.assertEqual(rec["repo_commit"], "d" * 40)
        self.assertEqual(rec["input"]["text_transformation"], "none")
        self.assertEqual(rec["input"]["sha256"], hashlib.sha256(self.script.read_bytes()).hexdigest())
        self.assertEqual(rec["output"]["sha256"], idx_adapter.sha256_file(self.out_wav))
        self.assertEqual(rec["voice"]["reference_prompt_sha256"], idx_adapter.sha256_file(self.ref_prompt))
        self.assertEqual(rec["listening"], {"status": "pending", "scope": "source_voice_track", "heard": False})
        self.assertEqual(len(rec["paragraph_timings"]), 2)
        self.assertTrue(self.rec_json.is_file())
        srt_text = self.srt_out.read_text(encoding="utf-8")
        self.assertIn("因为里面加入了铬", srt_text)
        self.assertNotIn("GE4", srt_text)

    def test_emo_text_without_qwen_emo_is_rejected(self) -> None:
        with self.assertRaises(idx_adapter.SynthesisError) as ctx:
            idx_adapter.synthesize_indextts2(
                text_file=self.script,
                output_wav=self.out_wav,
                record_path=self.rec_json,
                project_dir=self.proj_dir,
                reference_prompt=self.ref_prompt,
                confirmation_reference="test ref",
                use_baseline=False,
                use_emo_text=True,
                use_qwen_emo=False,
            )
        self.assertIn("use_qwen_emo=True", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
