"""Mock inference only: these fixtures never establish real speech or listening quality."""
import contextlib
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import io
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "synthesize_voice", ROOT / "skills/science-video-production/scripts/synthesize_voice.py")
voice = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(voice)
REVISION = "0c0e3051f131929182e2c023b9537f8b1c68adfe"


class Array(list):
    ndim = 1

    @property
    def size(self):
        return len(self)

    def max(self):
        return max(self)

    def all(self):
        return all(self)


class FakeSoundfile:
    """Writes a small actual IEEE float WAV, with no model or external libraries."""
    def write(self, path, data, samplerate, *, format, subtype):
        assert (format, subtype) == ("WAV", "FLOAT")
        samples = struct.pack("<" + "f" * len(data), *data)
        fmt = struct.pack("<HHIIHH", 3, 1, samplerate, samplerate * 4, 4, 32)
        Path(path).write_bytes(b"RIFF" + struct.pack("<I", 36 + len(samples)) + b"WAVEfmt " +
                              struct.pack("<I", len(fmt)) + fmt + b"data" +
                              struct.pack("<I", len(samples)) + samples)

    def info(self, path):
        data = Path(path).read_bytes()
        return SimpleNamespace(frames=(len(data) - 44) // 4,
                               samplerate=struct.unpack("<I", data[24:28])[0], channels=1)


class SynthesisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = self.root / "profile.json"
        self.text = self.root / "script.txt"
        self.output = self.root / "voice-v1.wav"
        self.record = self.root / "voice-v1.generation.json"
        self.project = self.root / "confirmed-project"
        self.cache = self.root / "confirmed-cache"
        self.project.mkdir()
        self.cache.mkdir()
        self.execution_reference = "fixture:explicit-local-selection; not real user confirmation"
        self.text.write_text("这是模拟接口测试，不是实际科普解说。\n", encoding="utf-8")
        self.settings = {"audio": {
            "backend": "local_qwen", "provider": "Qwen", "model_id": voice.MODEL_ID,
            "model": voice.MODEL_ID.split("/", 1)[1], "model_revision": REVISION,
            "speaker": "Serena", "language": "Chinese", "instruct": "自然口语",
            "runtime": {"device": "cpu", "dtype": "float32", "attn_implementation": "eager"},
            "generation_params": {"top_p": 0.75},
            "local_adapter_example": {
                "scope": "optional_local_adapter_only", "model_revision": "a" * 40,
                "runtime": {"device": "mps", "dtype": "float16", "attn_implementation": "eager"},
                "generation_params": {"top_p": 0.1},
            },
        }}
        self.save_settings()
        self.snapshot = (self.cache / "models--Qwen--Qwen3-TTS-12Hz-1.7B-CustomVoice" /
                         "snapshots" / REVISION)
        (self.snapshot / "speech_tokenizer").mkdir(parents=True)
        (self.snapshot / "config.json").write_text(json.dumps({
            "model_type": "qwen3_tts", "tts_model_type": "custom_voice", "tts_model_size": "1b7"}))
        (self.snapshot / "generation_config.json").write_text('{"temperature":0.9}')
        (self.snapshot / "speech_tokenizer/config.json").write_text('{}')
        (self.snapshot / "model.safetensors").write_bytes(b"not real weights; mocked test only")
        self.np = SimpleNamespace(
            asarray=lambda data, **kwargs: Array(data),
            abs=lambda data: Array(abs(x) for x in data),
            isfinite=lambda data: Array(math.isfinite(x) for x in data),
            float32="float32", random=SimpleNamespace(seed=mock.Mock()))
        self.torch = SimpleNamespace(
            float32="torch.float32", float16="torch.float16", bfloat16="torch.bfloat16",
            manual_seed=mock.Mock(), backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: False)),
            cuda=SimpleNamespace(is_available=lambda: False, device_count=lambda: 0))
        self.model = mock.Mock()
        self.model.device = "cpu"
        self.model.get_supported_speakers.return_value = ["serena", "vivian"]
        self.model.get_supported_languages.return_value = ["chinese", "english"]
        self.model._merge_generate_kwargs.side_effect = lambda **kwargs: {"temperature": 0.9, "max_new_tokens": 2048, **kwargs}
        self.model.generate_custom_voice.return_value = ([Array([0.25, -0.5, 2.0])], 24000)
        self.model_class = mock.Mock()
        self.model_class.from_pretrained.return_value = self.model
        self.download = mock.Mock(return_value=str(self.snapshot))
        runtime = (self.np, self.torch, FakeSoundfile(), self.download, self.model_class)
        self.patch = mock.patch.object(voice, "load_runtime", return_value=runtime)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def save_settings(self):
        self.profile.write_text(json.dumps(self.settings, ensure_ascii=False), encoding="utf-8")

    def run_synthesis(self, **kwargs):
        options = {"execution_reference": self.execution_reference,
                   "project_dir": self.project, "cache_dir": self.cache, **kwargs}
        return voice.synthesize(self.profile, self.text, self.output, self.record, **options)

    def assert_no_outputs(self):
        self.assertFalse(self.output.exists())
        self.assertFalse(self.record.exists())
        self.assertEqual(list(self.root.glob(".qwen-*")), [])

    def test_offline_generation_binds_actual_input_output_and_voice(self):
        result = self.run_synthesis(seed=42)
        self.assertEqual(self.download.call_args.kwargs["local_files_only"], True)
        self.assertEqual(self.download.call_args.kwargs["endpoint"], voice.HUB_ENDPOINT)
        self.assertIs(self.download.call_args.kwargs["token"], False)
        load = self.model_class.from_pretrained.call_args.kwargs
        self.assertEqual(load["device_map"], "cpu")
        self.assertEqual(load["dtype"], "torch.float32")
        self.assertIs(load["local_files_only"], True)
        call = self.model.generate_custom_voice.call_args.kwargs
        self.assertEqual(call["text"], self.text.read_text(encoding="utf-8"))
        self.assertEqual((call["speaker"], call["language"]), ("Serena", "Chinese"))
        self.assertEqual(call["top_p"], 0.75)
        self.assertEqual(result["effective_generation_params"]["temperature"], 0.9)
        self.assertEqual(result["resolved_model_revision"], REVISION)
        self.assertEqual(result["input"]["sha256"], voice.file_sha256(self.text))
        self.assertEqual(result["output"]["sha256"], voice.file_sha256(self.output))
        self.assertEqual(result["status"], "generated")
        self.assertEqual(result["listening"], {"status": "pending", "scope": "source_voice_track", "heard": False})
        self.assertEqual(json.loads(self.record.read_text())["output"], result["output"])
        # The raw sample above 1 is retained, not silently clipped or normalized.
        self.assertEqual(struct.unpack("<3f", self.output.read_bytes()[44:]), (0.25, -0.5, 2.0))
        self.torch.manual_seed.assert_called_once_with(42)

    def test_model_download_is_only_explicit_and_contains_no_text_argument(self):
        self.run_synthesis(allow_model_download=True, revision="reviewed-branch")
        self.assertFalse(self.download.call_args.kwargs["local_files_only"])
        self.assertEqual(self.download.call_args.kwargs["revision"], "reviewed-branch")
        self.assertNotIn("text", self.download.call_args.kwargs)

    def test_no_overwrite_of_existing_voice(self):
        self.output.write_bytes(b"accepted source voice")
        with self.assertRaisesRegex(voice.SynthesisError, "already exists"):
            self.run_synthesis()
        self.assertEqual(self.output.read_bytes(), b"accepted source voice")
        self.download.assert_not_called()

    def test_broken_output_symlink_is_not_followed_or_overwritten(self):
        missing = self.root / "unrelated.wav"
        self.output.symlink_to(missing)
        with self.assertRaisesRegex(voice.SynthesisError, "already exists"):
            self.run_synthesis()
        self.assertTrue(self.output.is_symlink())
        self.assertFalse(missing.exists())
        self.download.assert_not_called()

    def test_unconfigured_or_changed_backend_fails_before_download(self):
        self.settings["audio"]["backend"] = "remote_demo"
        self.save_settings()
        with self.assertRaisesRegex(voice.SynthesisError, "Only a confirmed local_qwen"):
            self.run_synthesis()
        self.download.assert_not_called()
        self.assert_no_outputs()

    def test_confirmation_and_targets_are_required_before_import_or_output_mkdir(self):
        self.output = self.root / "must-not-be-created" / "voice.wav"
        for options in ({"execution_reference": None}, {"execution_reference": "  "},
                        {"project_dir": None}, {"cache_dir": None},
                        {"project_dir": self.root / "missing-project"},
                        {"cache_dir": self.root / "missing-cache"}):
            with self.subTest(options=options):
                with self.assertRaises(voice.SynthesisError):
                    self.run_synthesis(**options)
                self.download.assert_not_called()
                voice.load_runtime.assert_not_called()
                self.assertFalse(self.output.parent.exists())
                self.assert_no_outputs()

    def test_invocation_confirmed_profile_records_actual_explicit_target(self):
        self.settings["audio"]["backend"] = "confirm_at_invocation"
        self.save_settings()
        result = self.run_synthesis()
        execution = result["execution"]
        self.assertEqual(result["backend"], "local_qwen")
        self.assertEqual(execution["status"], "confirmed")
        self.assertEqual(execution["mode"], "local_project")
        self.assertEqual(execution["adapter"], "local_qwen")
        self.assertEqual(execution["location"], str(self.project.resolve()))
        self.assertEqual(execution["confirmation_reference"], self.execution_reference)
        self.assertEqual(execution["model_cache_dir"], str(self.cache.resolve()))
        self.assertEqual(execution["python_executable"], sys.executable)
        self.assertEqual(self.download.call_args.kwargs["cache_dir"], str(self.cache.resolve()))
        actual_work = Path(execution["working_directory"])
        self.assertEqual(actual_work.parent, self.output.parent.resolve())
        self.assertFalse(actual_work.exists())
        self.assertEqual(json.loads(self.record.read_text())["execution"], execution)

    def test_optional_adapter_example_is_used_only_for_unset_settings(self):
        audio = self.settings["audio"]
        audio["backend"] = "confirm_at_invocation"
        audio["local_adapter_example"] = {
            "scope": "optional_local_adapter_only",
            **{key: audio.pop(key) for key in ("model_revision", "runtime", "generation_params")},
        }
        self.save_settings()
        result = self.run_synthesis()
        self.assertEqual(result["resolved_model_revision"], REVISION)
        self.assertEqual(result["load_parameters"]["device_map"], "cpu")
        self.assertEqual(result["requested_generation_params"], {"top_p": 0.75})

    def test_revision_mismatch_is_rejected(self):
        with self.assertRaisesRegex(voice.SynthesisError, "does not match"):
            self.run_synthesis(revision="a" * 40)
        self.model_class.from_pretrained.assert_not_called()
        self.assert_no_outputs()

    def test_incomplete_or_wrong_model_is_rejected(self):
        (self.snapshot / "speech_tokenizer/config.json").unlink()
        with self.assertRaisesRegex(voice.SynthesisError, "incomplete"):
            self.run_synthesis()
        self.assert_no_outputs()

    def test_missing_speaker_fails_without_switching(self):
        self.model.get_supported_speakers.return_value = ["vivian"]
        with self.assertRaisesRegex(voice.SynthesisError, "configured speaker"):
            self.run_synthesis()
        self.model.generate_custom_voice.assert_not_called()
        self.assert_no_outputs()

    def test_requested_mps_does_not_fall_back_to_cpu(self):
        with self.assertRaisesRegex(voice.SynthesisError, "MPS device is unavailable"):
            self.run_synthesis(device="mps")
        self.download.assert_not_called()
        self.assert_no_outputs()

    def test_generation_failure_does_not_write_success_record(self):
        self.model.generate_custom_voice.side_effect = RuntimeError("private input must not be echoed")
        with self.assertRaisesRegex(voice.SynthesisError, "generation failed") as ctx:
            self.run_synthesis()
        self.assertNotIn("private input", str(ctx.exception))
        self.assert_no_outputs()

    def test_invalid_or_silent_waveform_is_rejected(self):
        for samples in ([float("nan")], [0.0], []):
            with self.subTest(samples=samples):
                self.model.generate_custom_voice.return_value = ([Array(samples)], 24000)
                with self.assertRaises(voice.SynthesisError):
                    self.run_synthesis()
                self.assert_no_outputs()

    def test_empty_text_fails_before_any_model_operation(self):
        self.text.write_text(" \n", encoding="utf-8")
        with self.assertRaisesRegex(voice.SynthesisError, "text is empty"):
            self.run_synthesis()
        self.download.assert_not_called()
        self.assert_no_outputs()

    def test_malformed_settings_fail_before_runtime_import(self):
        valid_audio = self.settings["audio"]
        cases = [
            ([], "profile must be an object"),
            ({}, "audio must be an object"),
            ({"audio": []}, "audio must be an object"),
            ({"audio": {**valid_audio, "runtime": None}}, "runtime must be an object"),
            ({"audio": {**valid_audio, "runtime": [["device", "cpu"]]}}, "runtime must be an object"),
            ({"audio": {**valid_audio, "generation_params": {"non_streaming_mode": "false"}}},
             "non_streaming_mode must be a boolean"),
            ({"audio": {**valid_audio, "generation_params": {"temperature": float("nan")}}},
             "finite JSON values"),
        ]
        for settings, error in cases:
            with self.subTest(error=error, settings=settings):
                self.profile.write_text(json.dumps(settings), encoding="utf-8")
                with self.assertRaisesRegex(voice.SynthesisError, error):
                    self.run_synthesis()
                voice.load_runtime.assert_not_called()
                self.download.assert_not_called()
                self.assert_no_outputs()

    def test_invalid_profile_encoding_or_json_has_actionable_error(self):
        for content in (b"\xff", b'{"audio":'):
            with self.subTest(content=content):
                self.profile.write_bytes(content)
                with self.assertRaisesRegex(voice.SynthesisError, "valid JSON text"):
                    self.run_synthesis()
                voice.load_runtime.assert_not_called()
                self.assert_no_outputs()

    def test_concurrent_calls_do_not_share_or_delete_each_others_working_directory(self):
        previous_cwd = Path.cwd()
        first_entered = threading.Event()
        second_started = threading.Event()
        second_entered = threading.Event()
        release_first = threading.Event()
        workdirs = []

        def isolated_synthesis(*args, **kwargs):
            workdir = Path.cwd()
            workdirs.append(workdir)
            if len(workdirs) == 1:
                first_entered.set()
                self.assertTrue(release_first.wait(timeout=5))
            else:
                second_entered.set()
            self.assertEqual(Path.cwd(), workdir)
            return {}

        def second_call():
            second_started.set()
            return voice.synthesize(
                self.profile, self.text, self.root / "voice-v2.wav", self.root / "voice-v2.json",
                execution_reference=self.execution_reference, project_dir=self.project,
                cache_dir=self.cache)

        try:
            with mock.patch.object(voice, "_synthesize", side_effect=isolated_synthesis):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    first = pool.submit(self.run_synthesis)
                    try:
                        self.assertTrue(first_entered.wait(timeout=5))
                        second = pool.submit(second_call)
                        self.assertTrue(second_started.wait(timeout=5))
                        self.assertFalse(second_entered.wait(timeout=0.1),
                                         "A second inference changed the process working directory")
                    finally:
                        release_first.set()
                    first.result(timeout=5)
                    second.result(timeout=5)
            self.assertEqual(Path.cwd(), previous_cwd)
            self.assertEqual(len(workdirs), 2)
            self.assertNotEqual(*workdirs)
            self.assertTrue(all(not path.exists() for path in workdirs))
        finally:
            # Preserve the test runner's cwd even when testing a broken implementation.
            voice.os.chdir(previous_cwd)

    def test_dependency_session_files_stay_in_disposable_private_storage(self):
        previous_cwd = Path.cwd()
        real_loader = voice.load_runtime
        import_cwd = []
        def loader():
            import_cwd.append(Path.cwd())
            Path(':memory:.ses').write_text('simulated dependency import side effect')
            return real_loader()
        with mock.patch.object(voice, 'load_runtime', side_effect=loader):
            self.run_synthesis()
        self.assertEqual(Path.cwd(), previous_cwd)
        self.assertEqual(import_cwd[0].parent, self.output.parent.resolve())
        self.assertFalse(import_cwd[0].exists())

    def test_record_publish_failure_removes_only_new_output(self):
        calls = 0
        real_link = voice.os.link
        def link(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("disk failure")
            real_link(source, target)
        with mock.patch.object(voice.os, "link", side_effect=link):
            with self.assertRaises(OSError):
                self.run_synthesis()
        self.assert_no_outputs()

    def test_cli_reports_missing_dependencies_without_claiming_success(self):
        self.patch.stop()
        with mock.patch.object(voice, "load_runtime", side_effect=voice.SynthesisError("Missing local Qwen dependencies")):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                result = voice.main(["--profile", str(self.profile), "--text-file", str(self.text),
                                     "--output", str(self.output), "--record", str(self.record),
                                     "--execution-reference", self.execution_reference,
                                     "--project-dir", str(self.project), "--cache-dir", str(self.cache)])
        self.assertEqual(result, 1)
        self.assertEqual(json.loads(stderr.getvalue())["status"], "failed")
        self.assert_no_outputs()


if __name__ == "__main__":
    unittest.main()
