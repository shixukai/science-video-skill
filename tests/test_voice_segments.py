"""Synthetic PCM fixtures only; no TTS, speech or actual listening is claimed."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from unittest import mock
import wave


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "voice_segment_checks", ROOT / "scripts/check_episode.py")
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


@unittest.skipUnless(shutil.which("ffprobe"), "ffprobe required for isolated PCM fixtures")
class VoiceSegmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="science-voice-segments-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.execution = {"status": "confirmed", "mode": "local_project", "location": "/fixture-only/qwen",
                          "confirmation_reference": "mock record, no actual invocation authorization"}
        (self.root / "reason.txt").write_text("Synthetic fixture: a recorded interface length limit.")
        (self.root / "listening.txt").write_text("Synthetic evidence fixture; nobody listened to real speech.")
        inputs = ["第一段解释。\n\n", "所以，第二段继续解释。\n"]
        (self.root / "script.txt").write_text("".join(inputs), encoding="utf-8")
        self.manifest = {
            "schema_version": 1, "mode": "ordered_full_segments",
            "reason": {"kind": "interface_limit", "note": "Mock limitation, not a real model limit",
                       "evidence": self.ref("reason.txt")},
            "script": self.ref("script.txt"), "segments": [],
        }
        self.generations = []
        for index, text in enumerate(inputs):
            name = "segment-" + str(index + 1)
            (self.root / (name + ".txt")).write_text(text, encoding="utf-8")
            self.wav(name + ".wav", 1600, value=1000 * (index + 1))
            segment = {"id": name, "input": self.ref(name + ".txt"), "output": self.ref(name + ".wav")}
            generated = {
                "schema_version": 1, "status": "generated", "backend": "local_qwen", "provider": "Qwen",
                "model_id": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
                "resolved_model_revision": "1" * 40, "model_manifest_sha256": "2" * 64,
                "execution": copy.deepcopy(self.execution),
                "voice": {"speaker": "Serena", "language": "Chinese", "instruct": "连续讲述"},
                "effective_generation_params": {"top_p": 0.8},
                "load_parameters": {"device_map": "cpu", "dtype": "float32", "attn_implementation": "eager"},
                "input": {**segment["input"], "text_transformation": "none"}, "output": segment["output"],
                "seed": index, "note": "Mock generation record; no synthesis was performed",
            }
            self.generations.append(generated)
            segment["generation_record"] = self.write_json(name + ".json", generated)
            self.manifest["segments"].append(segment)
        with wave.open(str(self.root / "assembled.wav"), "wb") as output:
            output.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
            for segment in self.manifest["segments"]:
                with wave.open(str(self.root / segment["output"]["file"]), "rb") as source:
                    output.writeframes(source.readframes(source.getnframes()))
        self.post = {"schema_version": 1, "status": "processed", "mode": "concatenate_full_segments",
                     "sources": [{"segment_id": s["id"], **s["output"]} for s in self.manifest["segments"]],
                     "output": self.ref("assembled.wav"),
                     "steps": [{"tool": "Python wave fixture", "version": "stdlib",
                                "parameters": {"action": "append complete PCM frames"}}]}
        self.narration = {
            "status": "ready", "voice_type": "synthetic", "language": "zh-CN", "asset_id": "VOICE",
            "disclosure": "Synthetic test declarations only", "execution": self.execution,
            "script_file": "script.txt", "script_sha256": self.ref("script.txt")["sha256"],
            "audio_sha256": self.ref("assembled.wav")["sha256"], "generation_record": {"file": "", "sha256": ""},
            "source_listen_review": {
                "status": "pass", "scope": "assembled_voice_track", **self.ref("assembled.wav"),
                "method": "continuous_playback", "playback_speed": 1, "heard": True,
                "reviewer": "mock reviewer", "capability": "fixture only", "environment": "fixture device",
                "reviewed_at": "2026-10-10T00:00:00Z",
                "boundaries": [{"left_segment_id": "segment-1", "right_segment_id": "segment-2",
                                "at_seconds": 0.2, "range": [0.1, 0.3], "note": "Mock continuity observation",
                                "evidence": self.ref("listening.txt")}],
            },
        }
        self.save()

    def wav(self, name, frames, value=1000, rate=8000):
        with wave.open(str(self.root / name), "wb") as output:
            output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
            output.writeframes(struct.pack("<h", value) * frames)

    def ref(self, name):
        return {"file": name, "sha256": checks.file_sha256(self.root / name)}

    def write_json(self, name, value):
        (self.root / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return self.ref(name)

    def save(self):
        self.narration["generation_manifest"] = self.write_json("manifest.json", self.manifest)
        self.narration["postprocess_record"] = self.write_json("postprocess.json", self.post)

    def save_generation(self, index):
        segment = self.manifest["segments"][index]
        segment["generation_record"] = self.write_json(segment["generation_record"]["file"], self.generations[index])
        self.save()

    def errors(self):
        return checks.check_voice_segments(self.narration, self.root)

    def rejects(self, phrase):
        errors = self.errors()
        self.assertTrue(any(phrase in error for error in errors), errors)

    def test_complete_ordered_sources_pass_with_different_seeds(self):
        self.assertNotEqual(self.generations[0]["seed"], self.generations[1]["seed"])
        self.assertEqual(self.errors(), [])

    def test_wrong_order_omission_and_duplicate_ids_are_rejected(self):
        original = copy.deepcopy(self.manifest)
        for operation, phrase in (
                (lambda: self.manifest["segments"].reverse(), "exactly reconstruct"),
                (lambda: self.manifest["segments"].pop(), "at least two"),
                (lambda: self.manifest["segments"][1].update(id="segment-1"), "id missing/duplicate")):
            with self.subTest(phrase=phrase):
                self.manifest = copy.deepcopy(original)
                operation()
                self.save()
                self.rejects(phrase)

    def test_whitespace_and_added_separator_cannot_be_silently_normalized(self):
        segment = self.manifest["segments"][0]
        (self.root / segment["input"]["file"]).write_text("第一段解释。\n", encoding="utf-8")
        segment["input"] = self.ref(segment["input"]["file"])
        self.generations[0]["input"] = {**segment["input"], "text_transformation": "none"}
        self.save_generation(0)
        self.rejects("exactly reconstruct")

    def test_source_bytes_and_generation_record_hashes_are_both_checked(self):
        for name in ("segment-1.txt", "segment-1.json", "segment-1.wav", "script.txt", "manifest.json"):
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                path.write_bytes(original + b"stale")
                self.rejects("hash stale/missing")
                path.write_bytes(original)

    def test_generation_input_output_must_match_real_segment_files(self):
        original = copy.deepcopy(self.generations[0])
        for key in ("input", "output"):
            with self.subTest(key=key):
                self.generations[0] = copy.deepcopy(original)
                self.generations[0][key]["sha256"] = "0" * 64
                self.save_generation(0)
                self.rejects("generation " + key + " mismatch")

    def test_actual_configuration_drift_and_missing_parameters_are_rejected(self):
        original = copy.deepcopy(self.generations[1])
        changes = (
            ("voice", {"speaker": "Serena", "language": "Chinese", "instruct": "每段重新开场"}, "parameters drift"),
            ("effective_generation_params", {"top_p": 0.2}, "parameters drift"),
            ("effective_generation_params", {}, "actual effective"),
            ("load_parameters", {"device_map": "cuda:0"}, "parameters drift"),
            ("resolved_model_revision", "3" * 40, "parameters drift"),
            ("environment", {"package_versions": {"qwen-tts": "changed"}}, "parameters drift"),
        )
        for key, value, phrase in changes:
            with self.subTest(key=key, value=value):
                self.generations[1] = copy.deepcopy(original)
                self.generations[1][key] = value
                self.save_generation(1)
                self.rejects(phrase)

    def test_service_requires_actual_reported_parameters(self):
        self.narration["execution"] = {**self.execution, "mode": "service", "location": "https://fixture.example.test"}
        for index, generation in enumerate(self.generations):
            generation["execution"] = copy.deepcopy(self.narration["execution"])
            generation["backend"] = "confirmed_qwen_service"
            generation.pop("resolved_model_revision")
            generation.pop("model_manifest_sha256")
            generation["model_version_reference"] = "fixture response: exact weights not exposed"
            generation["runtime_parameters"] = {"service_version": "fixture-v1"}
            self.save_generation(index)
        self.assertEqual(self.errors(), [])
        self.generations[1].pop("effective_generation_params")
        self.save_generation(1)
        self.rejects("actual effective")

    def configure_cloud_segments(self, language):
        self.narration["execution"].update(mode="service", location="https://flow.google.com/project/fixture")
        self.post["steps"][0]["tool"] = "https://flow.google.com/project/fixture"
        for index, generation in enumerate(self.generations):
            for key in ("resolved_model_revision", "model_manifest_sha256", "effective_generation_params", "load_parameters"):
                generation.pop(key)
            generation.update(backend="flow_speech", provider="Google Flow", model_id="flow-speech-v1",
                              execution=copy.deepcopy(self.narration["execution"]), voice={"language": language},
                              cloud_evidence=self.write_json(f"cloud-job-{index}.json", {"job": index}))
            self.save_generation(index)

    def test_cloud_segments_bind_evidence_without_qwen_parameters(self):
        self.configure_cloud_segments("Chinese")
        packet = self.packet()
        packet.setdefault("design", {})["production_route"] = "google_flow"
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertFalse(any(e.startswith(("narration:", "narration segments:")) for e in errors), errors)

        self.generations[1]["cloud_evidence"]["sha256"] = "0" * 64
        self.save_generation(1)
        errors = checks.check_voice_segments(self.narration, self.root, cloud=True)
        self.assertTrue(any("cloud generation evidence hash stale" in e for e in errors), errors)

    def cloud_single_packet(self, language):
        self.narration["execution"].update(mode="service", location="https://flow.google.com/project/fixture")
        record = {
            "schema_version": 1, "status": "generated", "backend": "flow_speech", "provider": "Google Flow",
            "model_id": "flow-speech-v1", "execution": copy.deepcopy(self.narration["execution"]),
            "voice": {"language": language}, "cloud_evidence": self.write_json("job.json", {"job": "fixture"}),
            "input": self.ref("script.txt"), "output": self.ref("assembled.wav"),
        }
        packet = self.packet()
        packet.setdefault("design", {})["production_route"] = "google_flow"
        voice = packet["narration"]
        voice.pop("generation_manifest")
        voice.pop("postprocess_record")
        voice["generation_record"] = self.write_json("cloud-generation.json", record)
        return packet, record

    def test_ready_cloud_single_generation_requires_hash_bound_service_evidence(self):
        packet, record = self.cloud_single_packet("Chinese")
        voice = packet["narration"]
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertFalse(any(e.startswith("narration:") for e in errors), errors)

        voice["execution"]["mode"] = "local_project"
        record["execution"]["mode"] = "local_project"
        voice["generation_record"] = self.write_json("cloud-generation.json", record)
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertIn("narration: confirmed cloud service location/reference required", errors)

        voice["reuse_record"] = {"status": "previously_accepted", "reference": "fixture", "audio_sha256": voice["audio_sha256"]}
        voice.pop("generation_record")
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertIn("narration generation record: file path is missing", errors)

    def test_flow_single_voice_accepts_english_only_with_a_matching_cloud_receipt(self):
        (self.root / "script.txt").write_text("This synthetic fixture has English text.\n", encoding="utf-8")
        self.narration.update(language="en", script_sha256=self.ref("script.txt")["sha256"])
        packet, record = self.cloud_single_packet("English")
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertFalse(any(error.startswith("narration:") for error in errors), errors)

        record["voice"]["language"] = "Chinese"
        packet["narration"]["generation_record"] = self.write_json("cloud-generation.json", record)
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertIn("narration: cloud voice language must match the narration version", errors)

        record["voice"]["language"] = "English"
        packet["narration"]["generation_record"] = self.write_json("cloud-generation.json", record)
        packet["design"].pop("production_route")
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertTrue(any(error.startswith("narration:") and "language" in error for error in errors), errors)

    def test_flow_rejects_local_qwen_external_tts_and_local_postprocess(self):
        blocker_ref = self.write_json("cloud-tts-403.json", {"status": 403, "error": "Region not supported"})
        # (a) Local Qwen project fallback is forbidden on Google Flow
        packet, record = self.cloud_single_packet("Chinese")
        qwen_exec = {
            "status": "confirmed",
            "mode": "local_project",
            "location": "D:\\AI-Models\\ComfyUI-20261025\\Qwen3-TTS",
            "confirmation_reference": "series voice-baseline.json + cloud 403 blocker",
        }
        packet["narration"]["execution"] = qwen_exec
        qwen_rec = {
            "schema_version": 1, "status": "generated", "backend": "local_qwen", "provider": "Qwen",
            "model_id": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            "resolved_model_revision": "a" * 40, "model_manifest_sha256": "b" * 64,
            "execution": copy.deepcopy(qwen_exec),
            "voice": {"speaker": "Serena", "language": "Chinese", "instruct": "Calm conversational delivery."},
            "cloud_tts_blocker_evidence": blocker_ref,
            "input": self.ref("script.txt"), "output": self.ref("assembled.wav"),
        }
        packet["narration"]["generation_record"] = self.write_json("qwen-flow-zh.json", qwen_rec)
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertTrue(any("confirmed cloud service location/reference required" in e for e in errors), errors)

        # (b) Default Microsoft Edge cloud neural TTS (edge-tts, zh-CN-YunxiNeural, +4%) passes cleanly on Google Flow
        packet, record = self.cloud_single_packet("Chinese")
        packet["narration"]["execution"]["location"] = "https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1"
        record["execution"]["location"] = packet["narration"]["execution"]["location"]
        record.update(provider="Microsoft Edge", backend="edge-tts", model_id="edge-tts")
        record["voice"] = {"speaker": "zh-CN-YunxiNeural", "language": "Chinese", "rate": "+4%"}
        packet["narration"]["generation_record"] = self.write_json("edge-yunxi-flow.json", record)
        errors_edge, _ = checks.check(packet, self.root, "plan")
        self.assertFalse(any(e.startswith("narration:") for e in errors_edge), errors_edge)

        # (b2) Unapproved non-Microsoft/non-Google TTS service or wrong Chinese speaker/rate is rejected
        bad_packet, bad_rec = self.cloud_single_packet("Chinese")
        bad_packet["narration"]["execution"]["location"] = "https://tts.unapproved-vendor.example/v1"
        bad_rec["execution"]["location"] = bad_packet["narration"]["execution"]["location"]
        bad_rec.update(provider="UnapprovedVendor", backend="os_tts")
        bad_packet["narration"]["generation_record"] = self.write_json("bad-vendor-flow.json", bad_rec)
        errors, _ = checks.check(bad_packet, self.root, "plan")
        self.assertIn("narration: confirmed cloud service location/reference required", errors)
        self.assertTrue(any("edge-tts (Microsoft Edge)" in e for e in errors), errors)

        # (c) Continuous Google AI Studio (Gemini TTS) + prepare_voice_master/ffmpeg linear compositing also passes
        packet, record = self.cloud_single_packet("Chinese")
        packet["narration"]["execution"]["location"] = "https://aistudio.google.com/generate-speech"
        record["execution"]["location"] = "https://aistudio.google.com/generate-speech"
        record.update(provider="Google AI Studio", backend="gemini_tts", model_id="gemini-2.5-pro-preview-tts")
        packet["narration"]["generation_record"] = self.write_json("aistudio-gemini-zh.json", record)
        post_ok = {
            "schema_version": 1, "status": "processed",
            "source": self.ref("assembled.wav"), "output": self.ref("assembled.wav"),
            "steps": [{"tool": "prepare_voice_master.py", "version": "1.6.30", "parameters": {"action": "whole_track_linear_gain"}}],
        }
        packet["narration"]["postprocess_record"] = self.write_json("master-post.json", post_ok)
        errors_ok, _ = checks.check(packet, self.root, "plan")
        self.assertFalse(any(e.startswith("narration:") for e in errors_ok), errors_ok)

        # (c2) Local synthesize_voice/Qwen tool in postprocess_record is still rejected
        post_bad = {
            "schema_version": 1, "status": "processed",
            "source": self.ref("assembled.wav"), "output": self.ref("assembled.wav"),
            "steps": [{"tool": "synthesize_voice.py", "version": "1.0", "parameters": {"action": "local_qwen"}}],
        }
        packet["narration"]["postprocess_record"] = self.write_json("local-qwen-post.json", post_bad)
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertTrue(any("without local audio tools" in e for e in errors), errors)

        # (d) design.flow_postproduction_gaps workaround is forbidden
        packet, _ = self.cloud_single_packet("Chinese")
        packet["design"]["flow_postproduction_gaps"] = ["loudnorm"]
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertTrue(any("forbids local postproduction gap workarounds" in e for e in errors), errors)

    def test_flow_ordered_segments_bind_the_english_variant_language(self):
        inputs = ("First, observe the motion.\n\n", "Then, notice what changes.\n")
        (self.root / "script.txt").write_text("".join(inputs), encoding="utf-8")
        self.manifest["script"] = self.ref("script.txt")
        self.narration.update(language="en-US", script_sha256=self.manifest["script"]["sha256"])
        for segment, generation, text in zip(self.manifest["segments"], self.generations, inputs):
            name = segment["input"]["file"]
            (self.root / name).write_text(text, encoding="utf-8")
            segment["input"] = self.ref(name)
            generation["input"] = {**segment["input"], "text_transformation": "none"}
        self.configure_cloud_segments("English")
        packet = self.packet()
        packet.setdefault("design", {})["production_route"] = "google_flow"
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertFalse(any(error.startswith(("narration:", "narration segments:")) for error in errors), errors)

        self.generations[1]["voice"]["language"] = "Chinese"
        self.save_generation(1)
        packet["narration"]["generation_manifest"] = self.narration["generation_manifest"]
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertIn("narration segments: segment 2 cloud voice language must match the narration version", errors)

    def _indextts2_single_packet(self, *, flow=False):
        samples = b"".join(struct.pack("<f", 0.05 * math.sin(2 * math.pi * 200 * i / 48000)) for i in range(19200))
        fmt = struct.pack("<HHIIHH", 3, 1, 48000, 48000 * 4, 4, 32)
        chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(samples)) + samples
        (self.root / "polished.wav").write_bytes(b"RIFF" + struct.pack("<I", len(chunks) + 4) + b"WAVE" + chunks)
        polish_ref = self.ref("polished.wav")
        raw_ref = self.ref("assembled.wav")
        exec_cfg = {
            "status": "confirmed",
            "mode": "local_project",
            "location": "/fixture-only/indextts2",
            "confirmation_reference": "fixture audition #5",
        }
        gen_rec = {
            "schema_version": 1,
            "status": "generated",
            "provider": "IndexTTS",
            "backend": "local_indextts2",
            "model_id": "IndexTeam/IndexTTS-2.5",
            "repo_commit": "d" * 40,
            "checkpoints_fingerprint_sha256": "e" * 64,
            "model_version_reference": "IndexTTS-2.5 synthetic fixture",
            "execution": copy.deepcopy(exec_cfg),
            "voice": {
                "speaker": "user_clone",
                "voice_preset_id": "mandarin-indextts25-clone-polished-v1",
                "language": "Chinese",
                "reference_prompt_sha256": "f" * 64,
            },
            "load_parameters": {"use_bf16": True, "use_cuda_kernel": False, "use_qwen_emo": False},
            "effective_generation_params": {"lang": "ZH", "duration_factor": 1.0, "use_emo_text": False},
            "input": {**self.ref("script.txt"), "text_transformation": "none"},
            "output": raw_ref,
        }
        post_rec = {
            "schema_version": 1,
            "status": "processed",
            "mode": "whole_track_speech_polish",
            "source": raw_ref,
            "output": polish_ref,
            "steps": [
                {
                    "tool": "prepare_voice_master.py",
                    "version": "1.6.37",
                    "parameters": {
                        "processing_mode": "whole_track_speech_polish",
                        "filter_chain": "highpass=f=75,acompressor=threshold=-20dB:ratio=2",
                        "echo": "none",
                        "output_sample_rate_hz": 48000,
                        "codec": "pcm_f32le",
                        "channels": "preserve",
                        "speed_factor": 1,
                        "pitch_shift_semitones": 0,
                        "per_shot_normalization": False,
                    },
                }
            ],
        }
        packet = self.packet()
        if flow:
            packet.setdefault("design", {})["production_route"] = "google_flow"
        packet["assets"][-1].update(file="polished.wav", sha256=polish_ref["sha256"])
        voice = packet["narration"]
        voice.pop("generation_manifest", None)
        voice.pop("source_listen_review", None)
        voice["execution"] = copy.deepcopy(exec_cfg)
        voice["audio_sha256"] = polish_ref["sha256"]
        voice["series_sample_reference"] = "fixture sample #5"
        voice["generation_record"] = self.write_json("indextts2-gen.json", gen_rec)
        voice["postprocess_record"] = self.write_json("indextts2-polish.json", post_rec)
        return packet, gen_rec, polish_ref

    def test_indextts2_single_and_segmented_polish_pass_and_require_prompt_hash(self):
        for flow in (False, True):
            stage = "plan" if flow else "delivery"
            with self.subTest(flow=flow, stage=stage):
                packet, gen_rec, _ = self._indextts2_single_packet(flow=flow)
                errors, _ = checks.check(packet, self.root, stage)
                self.assertFalse(any(e.startswith("narration") for e in errors), errors)

                bad_gen = copy.deepcopy(gen_rec)
                bad_gen["voice"].pop("reference_prompt_sha256")
                packet["narration"]["generation_record"] = self.write_json("indextts2-gen-bad.json", bad_gen)
                errors_bad, _ = checks.check(packet, self.root, stage)
                self.assertTrue(any("reference_prompt_sha256" in e for e in errors_bad), errors_bad)

        # Segmented IndexTTS-2.5 + whole_track_speech_polish passes on standard & google_flow routes
        exec_cfg = {
            "status": "confirmed",
            "mode": "local_project",
            "location": "/fixture-only/indextts2",
            "confirmation_reference": "fixture audition #5",
        }
        for seg, g in zip(self.manifest["segments"], self.generations):
            for k in ("resolved_model_revision", "model_manifest_sha256"):
                g.pop(k, None)
            g.update(
                provider="IndexTTS",
                backend="local_indextts2",
                model_id="IndexTeam/IndexTTS-2.5",
                repo_commit="d" * 40,
                checkpoints_fingerprint_sha256="e" * 64,
                execution=copy.deepcopy(exec_cfg),
                voice={
                    "speaker": "user_clone",
                    "voice_preset_id": "mandarin-indextts25-clone-polished-v1",
                    "language": "Chinese",
                    "reference_prompt_sha256": "f" * 64,
                },
                load_parameters={"use_bf16": True, "use_cuda_kernel": False, "use_qwen_emo": False},
                effective_generation_params={"lang": "ZH", "duration_factor": 1.0, "use_emo_text": False},
            )
        self.narration["execution"] = copy.deepcopy(exec_cfg)
        for i in range(len(self.generations)):
            self.save_generation(i)
        samples = b"".join(struct.pack("<f", 0.05 * math.sin(2 * math.pi * 200 * i / 48000)) for i in range(19200))
        fmt = struct.pack("<HHIIHH", 3, 1, 48000, 48000 * 4, 4, 32)
        chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(samples)) + samples
        (self.root / "seg-polished.wav").write_bytes(b"RIFF" + struct.pack("<I", len(chunks) + 4) + b"WAVE" + chunks)
        polish_ref = self.ref("seg-polished.wav")
        concat_doc = copy.deepcopy(self.post)
        concat_doc["steps"][0]["tool"] = "synthesize_indextts2.py"
        concat_ref = self.write_json("seg-concat.json", concat_doc)
        master_polish = {
            "schema_version": 1,
            "status": "processed",
            "mode": "whole_track_speech_polish",
            "upstream_record": concat_ref,
            "source": self.ref("assembled.wav"),
            "output": polish_ref,
            "steps": [
                {
                    "tool": "prepare_voice_master.py",
                    "version": "1.6.37",
                    "parameters": {
                        "processing_mode": "whole_track_speech_polish",
                        "filter_chain": "highpass=f=75,acompressor=threshold=-20dB:ratio=2",
                        "echo": "none",
                        "output_sample_rate_hz": 48000,
                        "codec": "pcm_f32le",
                        "channels": "preserve",
                        "speed_factor": 1,
                        "pitch_shift_semitones": 0,
                        "per_shot_normalization": False,
                    },
                }
            ],
        }
        self.post = master_polish
        self.narration["audio_sha256"] = polish_ref["sha256"]
        self.narration["source_listen_review"].update(polish_ref)
        self.save()
        self.assertEqual(checks.check_voice_segments(self.narration, self.root, cloud=False), [])
        self.assertEqual(checks.check_voice_segments(self.narration, self.root, cloud=True, cloud_language="Chinese"), [])

    def test_reason_needs_supported_kind_and_bound_evidence(self):
        self.manifest["reason"] = {"kind": "one_shot_per_scene", "note": "Convenient segmentation"}
        self.save()
        self.rejects("actual necessary segmentation reason")
        self.rejects("reason evidence file required")

    def test_reason_and_boundary_observations_reject_placeholder_text(self):
        for value in ("pending", "not_reviewed", "blocked", "待验", "n/a"):
            with self.subTest(value=value):
                self.manifest["reason"]["note"] = value
                self.narration["source_listen_review"]["boundaries"][0]["note"] = value
                self.save()
                self.rejects("actual necessary segmentation reason")
                self.rejects("actual continuity observations")

    def test_postprocess_requires_all_sources_in_exact_order(self):
        self.post["sources"].reverse()
        self.save()
        self.rejects("all ordered segment outputs")

    def test_single_source_postprocess_cannot_hide_multiple_sources(self):
        self.post["source"] = self.post.pop("sources")[0]
        self.save()
        self.rejects("must concatenate complete segments")

    def test_postprocess_cannot_bind_another_final_audio(self):
        self.narration["audio_sha256"] = "0" * 64
        self.rejects("output must bind current narration")

    def test_trimmed_or_gapped_output_duration_is_rejected(self):
        self.wav("assembled.wav", 2400)
        self.post["output"] = self.ref("assembled.wav")
        self.narration["audio_sha256"] = self.post["output"]["sha256"]
        self.narration["source_listen_review"].update(self.post["output"])
        self.save()
        self.rejects("assembled duration must equal")

    def test_changed_source_sample_rate_is_rejected(self):
        self.wav("segment-2.wav", 3200, rate=16000)
        self.manifest["segments"][1]["output"] = self.ref("segment-2.wav")
        self.generations[1]["output"] = self.ref("segment-2.wav")
        self.post["sources"][1] = {"segment_id": "segment-2", **self.ref("segment-2.wav")}
        self.save_generation(1)
        self.rejects("share PCM codec/sample rate/channels")

    def test_boundaries_require_actual_listening_not_a_pass_note(self):
        self.narration["source_listen_review"]["heard"] = False
        self.rejects("requires actual normal-speed boundary listening")

    def test_overall_pass_cannot_override_an_explicit_failed_or_unheard_boundary(self):
        boundary = self.narration["source_listen_review"]["boundaries"][0]
        for key, value in (("status", "fail"), ("status", "pending"), ("heard", False)):
            with self.subTest(key=key, value=value):
                boundary[key] = value
                self.rejects("explicit failed/unheard review")
                boundary.pop(key)

    def test_missing_stale_or_one_sided_boundary_review_is_rejected(self):
        original = copy.deepcopy(self.narration["source_listen_review"])
        for change, phrase in (
                (lambda r: r.update(boundaries=[]), "every adjacent"),
                (lambda r: r.update(sha256="0" * 64), "bind current assembled audio"),
                (lambda r: r["boundaries"][0].update(range=[0.2, 0.3]), "range must cross"),
                (lambda r: r["boundaries"][0].update(at_seconds=0.1), "time must match"),
                (lambda r: r["boundaries"][0].update(evidence={}), "listening evidence file required")):
            with self.subTest(phrase=phrase):
                self.narration["source_listen_review"] = copy.deepcopy(original)
                change(self.narration["source_listen_review"])
                self.rejects(phrase)

    def test_nonfinite_boolean_and_huge_integer_boundary_times_fail_without_crashing(self):
        boundary = self.narration["source_listen_review"]["boundaries"][0]
        for value in (float("nan"), float("inf"), True, 10 ** 500):
            with self.subTest(kind=type(value).__name__):
                boundary["at_seconds"] = value
                self.rejects("time must match")
                boundary["at_seconds"] = 0.2
                boundary["range"] = [value, 0.3]
                self.rejects("range must cross")
                boundary["range"] = [0.1, 0.3]

    def packet(self):
        packet = json.loads((ROOT / "examples/blue-sky/episode.json").read_text())
        from stage_fixture import attach_topic_selection_fixture
        attach_topic_selection_fixture(packet)
        (self.root / "topic-anchor.json").write_bytes((ROOT / "examples/blue-sky/topic-anchor.json").read_bytes())
        packet["narration"] = copy.deepcopy(self.narration)
        packet["assets"].append({"id": "VOICE", "kind": "audio", "file": "assembled.wav",
                                 "sha256": self.narration["audio_sha256"], "source": "synthetic test fixture",
                                 "creator": "test harness", "rights": {"status": "pending"}})
        return packet

    def test_pending_candidate_does_not_require_fake_listening_but_ready_does(self):
        packet = self.packet()
        packet["narration"]["status"] = "pending"
        packet["narration"]["source_listen_review"].update(status="not_reviewed", heard=False, boundaries=[])
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertFalse(any("narration segments:" in e for e in errors), errors)
        packet["narration"]["status"] = "ready"
        errors, _ = checks.check(packet, self.root, "plan")
        self.assertTrue(any("actual normal-speed boundary listening" in e for e in errors), errors)

    def test_g2_checks_ready_segment_provenance_without_changing_stage_checks(self):
        packet = self.packet()
        packet["narration"]["source_listen_review"]["heard"] = False
        with mock.patch.object(checks, "check_stage", return_value=[]):
            errors, _ = checks.check(packet, self.root, "G2")
        self.assertTrue(any("actual normal-speed boundary listening" in e for e in errors), errors)

    def test_manifest_cannot_be_combined_with_fake_reuse_or_single_record(self):
        for addition in ({"reuse_record": {"status": "previously_accepted", "reference": "not permission"}},
                         {"generation_record": self.manifest["segments"][0]["generation_record"]}):
            with self.subTest(addition=addition):
                packet = self.packet()
                packet["narration"].update(addition)
                errors, _ = checks.check(packet, self.root, "plan")
                self.assertTrue(any("choose exactly one" in e for e in errors), errors)

    def test_unsafe_manifest_reference_is_rejected(self):
        self.narration["generation_manifest"]["file"] = "../outside.json"
        self.rejects("path missing/unsafe")

    def test_invalid_path_bytes_and_symlink_loop_fail_without_crashing(self):
        for name in ("\x00", "loop.json"):
            with self.subTest(name=repr(name)):
                if name == "loop.json":
                    from fs_support import symlink_or_skip
                    symlink_or_skip(self, self.root / name, name)
                self.narration["generation_manifest"]["file"] = name
                self.rejects("unsafe")


if __name__ == "__main__":
    unittest.main()
