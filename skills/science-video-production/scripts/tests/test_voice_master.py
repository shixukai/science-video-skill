"""Behavior tests using disposable local records and synthetic audio only."""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import wave


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "prepare_voice_master.py"
if not SCRIPT.is_file():
    SCRIPT = HERE.parent / "prepare_voice_master.py"
spec = importlib.util.spec_from_file_location("voice_master_under_test", SCRIPT)
master = importlib.util.module_from_spec(spec)
spec.loader.exec_module(master)


def profile():
    return {"audio": {"mix_preset": {
        "id": "mandarin-continuous-master-v1",
        "narration_master": {"target_i_lufs": -18.0, "true_peak_ceiling_dbtp": -2.0,
                             "output_sample_rate_hz": 48000,
                             "processing_mode": "whole_track_linear_gain"},
        "pitch_shift_semitones": 0, "speed_factor": 1, "per_shot_normalization": False,
        "optional_processors": {"equalizer": "bypass", "compressor": "bypass",
                                "denoiser": "bypass", "limiter": "bypass"}}}}


def write_wave(path, duration=6, channels=1, transient=False, silence=False):
    rate = 24000
    data = bytearray()
    for n in range(int(duration * rate)):
        value = 0 if silence else (0.006 if transient else 0.055) * math.sin(2 * math.pi * 220 * n / rate)
        if transient and int(rate * 3) <= n < int(rate * 3) + 4:
            value = 0.95 if n % 2 else -0.95
        for channel in range(channels):
            data.extend(struct.pack("<h", round(value * (1 if channel == 0 else 0.7) * 32767)))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(data)


def float_wave(path):
    raw = path.read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise AssertionError("Expected fixture float WAV")
    offset = 12
    chunks = {}
    while offset + 8 <= len(raw):
        kind, size = struct.unpack_from("<4sI", raw, offset)
        chunks[kind] = raw[offset + 8:offset + 8 + size]
        offset += 8 + size + size % 2
    channels, rate = struct.unpack_from("<HI", chunks[b"fmt "], 2)
    values = struct.unpack("<" + "f" * (len(chunks[b"data"]) // 4), chunks[b"data"])
    return rate, channels, values


class Fixtures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("VOICE_MASTER_TEST_TEMP"))
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / "source [literal] ' $(safe).wav"
        self.src.write_bytes(b"synthetic pending fixture")
        self.out = self.root / "audio" / "master.wav"
        self.rec = self.root / "records" / "master.json"
        self.profile = self.root / "profile.json"
        self.profile.write_text(json.dumps(profile()), encoding="utf-8")


class GainPlanTests(unittest.TestCase):
    def test_quiet_source_uses_one_gain_without_peak_limiting(self):
        result = master.gain_plan({"i_lufs": -25, "true_peak_dbtp": -15}, -18, -2)
        self.assertAlmostEqual(result["applied_gain_db"], 7)
        self.assertFalse(result["peak_limited"])

    def test_transient_headroom_wins_over_loudness_goal(self):
        result = master.gain_plan({"i_lufs": -30, "true_peak_dbtp": -1}, -18, -2)
        self.assertAlmostEqual(result["applied_gain_db"], -1.1)
        self.assertTrue(result["peak_limited"])

    def test_loud_source_is_attenuated_uniformly(self):
        result = master.gain_plan({"i_lufs": -10, "true_peak_dbtp": -0.5}, -18, -2)
        self.assertAlmostEqual(result["applied_gain_db"], -8)
        self.assertFalse(result["peak_limited"])

    def test_nonfinite_measurements_are_rejected(self):
        for value in ("-inf", "nan", float("inf"), None, True):
            with self.subTest(value=value), self.assertRaises(master.VoiceMasterError):
                master.gain_plan({"i_lufs": value, "true_peak_dbtp": -10}, -18, -2)


class ConfigurationAndFilesTests(Fixtures):
    def test_actual_preset_values_are_loaded(self):
        _, target, ceiling, rate, digest = master.read_preset(self.profile)
        self.assertEqual((target, ceiling, rate), (-18, -2, 48000))
        self.assertEqual(digest, master.sha256(self.profile))

    def test_unsupported_processor_and_per_shot_settings_are_not_ignored(self):
        for key, value in (("pitch_shift_semitones", 1), ("speed_factor", 1.1),
                           ("per_shot_normalization", True),
                           ("optional_processors", {"compressor": "enabled"})):
            item = profile()
            item["audio"]["mix_preset"][key] = value
            self.profile.write_text(json.dumps(item), encoding="utf-8")
            with self.subTest(key=key), self.assertRaises(master.VoiceMasterError):
                master.read_preset(self.profile)

    def test_malformed_preset_does_not_create_output(self):
        for value in ([], {"audio": []}, {"audio": {"mix_preset": []}},
                      {"audio": {"mix_preset": {"narration_master": []}}}):
            self.profile.write_text(json.dumps(value), encoding="utf-8")
            with self.subTest(value=value), self.assertRaises(master.VoiceMasterError):
                master.prepare(self.root, self.src, self.out, self.rec, self.profile)
            self.assertFalse(self.out.exists())

    def test_existing_output_and_record_are_preserved(self):
        for target in (self.out, self.rec):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"existing user artifact")
            with self.subTest(target=target), self.assertRaises(master.VoiceMasterError):
                master.paths(self.root, self.src, self.out, self.rec, self.profile)
            self.assertEqual(target.read_bytes(), b"existing user artifact")
            target.unlink()

    def test_in_place_and_record_collisions_are_rejected(self):
        for output, record in ((self.src, self.rec), (self.out, self.out),
                               (self.out, self.profile), (self.out, self.src)):
            with self.subTest(output=output, record=record), self.assertRaises(master.VoiceMasterError):
                master.paths(self.root, self.src, output, record, self.profile)

    def test_outputs_cannot_escape_episode(self):
        with self.assertRaises(master.VoiceMasterError):
            master.paths(self.root, self.src, self.root.parent / "escaped.wav", self.rec, self.profile)

    def test_relative_audio_paths_are_rooted_at_the_episode(self):
        _, source, output, record, _ = master.paths(self.root, self.src.name,
            "audio/master.wav", "records/master.json", self.profile)
        self.assertEqual((source, output, record), (self.src, self.out, self.rec))

    def test_exclusive_reservation_preserves_a_concurrent_record_writer(self):
        self.rec.parent.mkdir(parents=True)
        self.rec.write_bytes(b"other writer")
        with self.assertRaises(FileExistsError):
            with master.reserve(self.out, self.rec):
                self.fail("A competing record must not be adopted")
        self.assertFalse(self.out.exists())
        self.assertEqual(self.rec.read_bytes(), b"other writer")

    def test_failed_work_removes_only_owned_placeholders(self):
        with self.assertRaises(RuntimeError):
            with master.reserve(self.out, self.rec):
                raise RuntimeError("fixture failure")
        self.assertFalse(self.out.exists())
        self.assertFalse(self.rec.exists())
        self.assertEqual(self.src.read_bytes(), b"synthetic pending fixture")

    def test_missing_local_tool_is_an_explicit_error(self):
        with self.assertRaises(master.VoiceMasterError):
            master.find_tool(str(self.root / "missing-ffmpeg"), "ffmpeg")

    def test_commands_are_argument_arrays_without_a_shell(self):
        with patch.object(master.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "ok", "")) as mocked:
            command = ["ffmpeg", "-i", str(self.src)]
            master.run(command)
        self.assertEqual(mocked.call_args.args[0], command)
        self.assertIs(mocked.call_args.kwargs["shell"], False)

    def test_measurement_rejects_silence_and_invalid_numbers(self):
        for value in ("-inf", "nan"):
            stderr = json.dumps({"input_i": value, "input_tp": "-inf", "input_lra": "0"})
            with self.subTest(value=value), patch.object(master, "run", return_value=subprocess.CompletedProcess([], 0, "", stderr)):
                with self.assertRaises(master.VoiceMasterError):
                    master.measure(self.src, "ffmpeg", -18, -2)

    def test_upstream_concat_hashes_bind_the_actual_source(self):
        left, right = self.root / "left.wav", self.root / "right.wav"
        left.write_bytes(b"left synthetic source")
        right.write_bytes(b"right synthetic source")
        upstream = self.root / "concat.json"
        data = {"schema_version": 1, "status": "processed", "mode": "concatenate_full_segments",
                "sources": [{"segment_id": p.stem, "file": p.name, "sha256": master.sha256(p)}
                            for p in (left, right)],
                "output": {"file": self.src.name, "sha256": master.sha256(self.src)},
                "steps": [{"tool": "fixture_concat", "version": "1", "parameters": {"fixture": True}}]}
        upstream.write_text(json.dumps(data), encoding="utf-8")
        result = master.read_upstream(upstream, self.root, self.src, master.sha256(self.src),
                                      self.out, self.rec, self.profile)
        self.assertEqual(result["file"], "concat.json")
        self.assertEqual(result["sha256"], master.sha256(upstream))
        data["output"]["sha256"] = "0" * 64
        upstream.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(master.VoiceMasterError):
            master.read_upstream(upstream, self.root, self.src, master.sha256(self.src),
                                 self.out, self.rec, self.profile)

    def test_upstream_cannot_be_an_unsafe_or_other_processing_mode(self):
        upstream = self.root / "concat.json"
        for data in ({"schema_version": 1, "status": "processed", "mode": "crop"},
                     {"schema_version": 1, "status": "processed", "mode": "concatenate_full_segments",
                      "output": {"file": "../outside.wav", "sha256": "0" * 64}}):
            upstream.write_text(json.dumps(data), encoding="utf-8")
            with self.subTest(data=data), self.assertRaises(master.VoiceMasterError):
                master.read_upstream(upstream, self.root, self.src, master.sha256(self.src),
                                     self.out, self.rec, self.profile)


FFMPEG = os.environ.get("VOICE_MASTER_TEST_FFMPEG") or shutil.which("ffmpeg")
FFPROBE = os.environ.get("VOICE_MASTER_TEST_FFPROBE") or (
    str(Path(FFMPEG).with_name("ffprobe" + Path(FFMPEG).suffix)) if FFMPEG else None)


@unittest.skipUnless(FFMPEG and FFPROBE and Path(FFMPEG).is_file() and Path(FFPROBE).is_file(),
                     "existing FFmpeg/ffprobe required for synthetic local smoke")
class NativeSyntheticTests(Fixtures):
    def process(self, **kwargs):
        return master.prepare(self.root, self.src, self.out, self.rec, self.profile,
                              FFMPEG, FFPROBE, **kwargs)

    def test_one_gain_preserves_stereo_duration_frequency_and_source(self):
        write_wave(self.src, channels=2)
        original = self.src.read_bytes()
        result = self.process()
        rate, channels, samples = float_wave(self.out)
        self.assertEqual((rate, channels, len(samples)), (48000, 2, 6 * 48000 * 2))
        signal = samples[::channels]
        crossings = sum(a <= 0 < b for a, b in zip(signal, signal[1:]))
        self.assertLess(abs(crossings / 6 - 220), 0.3)
        self.assertEqual(self.src.read_bytes(), original)
        self.assertAlmostEqual(result["measured_after"]["i_lufs"], -18, delta=0.1)
        self.assertLessEqual(result["measured_after"]["true_peak_dbtp"], -2)
        self.assertEqual(result["mode"], "whole_track_linear_gain")
        self.assertEqual(result["source"]["file"], self.src.name)
        self.assertEqual(result["output"]["sha256"], master.sha256(self.out))
        self.assertEqual(result["listening"], {"status": "pending", "heard": False})
        self.assertFalse(result["technical"]["quality_approval"])
        self.assertEqual(len(result["steps"]), 1)
        self.assertFalse(result["steps"][0]["parameters"]["dynamic_compression"])
        self.assertEqual(json.loads(self.rec.read_text(encoding="utf-8")), result)

    def test_transients_back_off_gain_and_report_mix_review_without_compression(self):
        write_wave(self.src, transient=True)
        result = self.process()
        self.assertTrue(result["gain"]["peak_limited"])
        self.assertLess(result["measured_after"]["i_lufs"], -20)
        self.assertLessEqual(result["measured_after"]["true_peak_dbtp"], -2)
        self.assertEqual(result["mix_review"], "needed_for_peak_limited_target")
        self.assertLessEqual(result["technical"]["render_attempts"], 2)

    def test_silent_source_does_not_publish_a_master(self):
        write_wave(self.src, silence=True)
        with self.assertRaises(master.VoiceMasterError):
            self.process()
        self.assertFalse(self.out.exists())
        self.assertFalse(self.rec.exists())

    def test_source_mutation_prevents_publication(self):
        write_wave(self.src)
        original_measure = master.measure
        calls = []

        def measured(path, *args):
            value = original_measure(path, *args)
            calls.append(path)
            if len(calls) == 2:
                with self.src.open("ab") as stream:
                    stream.write(b"fixture mutation")
            return value

        with patch.object(master, "measure", side_effect=measured), self.assertRaises(master.VoiceMasterError):
            self.process()
        self.assertFalse(self.out.exists())
        self.assertFalse(self.rec.exists())

    def test_profile_mutation_prevents_publication(self):
        write_wave(self.src)
        original_measure = master.measure
        calls = []

        def measured(path, *args):
            value = original_measure(path, *args)
            calls.append(path)
            if len(calls) == 2:
                with self.profile.open("ab") as stream:
                    stream.write(b" ")
            return value

        with patch.object(master, "measure", side_effect=measured), self.assertRaises(master.VoiceMasterError):
            self.process()
        self.assertFalse(self.out.exists())
        self.assertFalse(self.rec.exists())

    def test_whole_segment_concat_can_feed_one_processed_master(self):
        left, right = self.root / "left.wav", self.root / "right.wav"
        write_wave(left, duration=3)
        write_wave(right, duration=3)
        write_wave(self.src, duration=6)
        upstream = self.root / "concat.json"
        data = {"schema_version": 1, "status": "processed", "mode": "concatenate_full_segments",
                "sources": [{"segment_id": p.stem, "file": p.name, "sha256": master.sha256(p)}
                            for p in (left, right)],
                "output": {"file": self.src.name, "sha256": master.sha256(self.src)},
                "steps": [{"tool": "stdlib_wave_fixture", "version": "1",
                           "parameters": {"order": ["left", "right"]}}]}
        upstream.write_text(json.dumps(data), encoding="utf-8")
        result = self.process(upstream_record="concat.json")
        self.assertEqual(result["upstream_record"], {"file": "concat.json", "sha256": master.sha256(upstream)})
        self.assertEqual(result["source"], data["output"])
        self.assertEqual(result["mode"], "whole_track_linear_gain")

    def test_only_one_peak_correction_is_attempted(self):
        write_wave(self.src)
        measures = [{"i_lufs": -25, "true_peak_dbtp": -12, "lra_lu": 0},
                    {"i_lufs": -18, "true_peak_dbtp": -1.8, "lra_lu": 0},
                    {"i_lufs": -18.3, "true_peak_dbtp": -2.1, "lra_lu": 0}]
        with patch.object(master, "measure", side_effect=measures) as measured:
            result = self.process()
        self.assertEqual(measured.call_count, 3)
        self.assertEqual(result["technical"]["render_attempts"], 2)
        self.assertAlmostEqual(result["gain"]["applied_gain_db"], 6.7)

    def test_peak_failure_after_correction_does_not_loop_or_publish(self):
        write_wave(self.src)
        values = [{"i_lufs": -25, "true_peak_dbtp": -12, "lra_lu": 0},
                  {"i_lufs": -18, "true_peak_dbtp": -1.8, "lra_lu": 0},
                  {"i_lufs": -18.3, "true_peak_dbtp": -1.9, "lra_lu": 0}]
        with patch.object(master, "measure", side_effect=values) as measured, self.assertRaises(master.VoiceMasterError):
            self.process()
        self.assertEqual(measured.call_count, 3)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.rec.exists())


class ContinuityDiagnosticsTests(Fixtures):
    def _write_two_segment_wave(self, path, amp1=0.08, freq1=180.0, amp2=0.08, freq2=180.0, spike=False):
        rate = 24000
        data = bytearray()
        for n in range(rate * 6):
            amp, freq = (amp1, freq1) if n < rate * 3 else (amp2, freq2)
            value = amp * math.sin(2 * math.pi * freq * n / rate)
            if spike and int(rate * 1.5) <= n < int(rate * 1.5) + 6:
                value = 0.92 if n % 2 == 0 else -0.92
            data.extend(struct.pack("<h", max(-32768, min(32767, round(value * 32767)))))
        with wave.open(str(path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(rate)
            output.writeframes(data)

    def test_uniform_tone_reports_nominal_continuity_and_accurate_f0(self):
        self._write_two_segment_wave(self.src, amp1=0.08, freq1=200.0, amp2=0.08, freq2=200.0)
        diag = master.analyze_continuity(self.src, boundaries=[3.0])
        self.assertEqual(diag["status"], "within_nominal_bounds")
        self.assertEqual(diag["flags"], [])
        self.assertAlmostEqual(diag["f0_median_hz"], 200.0, delta=3.0)
        self.assertEqual(len(diag["boundary_checks"]), 1)
        self.assertFalse(diag["boundary_checks"][0]["flagged"])

    def test_boundary_level_and_pitch_jumps_are_flagged_accurately(self):
        self._write_two_segment_wave(self.src, amp1=0.04, freq1=160.0, amp2=0.16, freq2=220.0)
        diag = master.analyze_continuity(self.src, boundaries=[3.0])
        self.assertEqual(diag["status"], "flagged_for_review")
        self.assertIn("adjacent_window_level_jump", diag["flags"])
        self.assertIn("pitch_register_jump", diag["flags"])
        self.assertIn("boundary_level_or_pitch_jump", diag["flags"])
        boundary = diag["boundary_checks"][0]
        self.assertTrue(boundary["flagged"])
        self.assertGreater(boundary["level_jump_db"], 10.0)
        self.assertGreater(boundary["semitone_jump"], 4.5)

    def test_isolated_transient_spike_is_pinpointed_in_diagnostics(self):
        self._write_two_segment_wave(self.src, amp1=0.02, freq1=180.0, amp2=0.02, freq2=180.0, spike=True)
        diag = master.analyze_continuity(self.src, peak_limited=True, target_shortfall_lu=4.0)
        self.assertIn("isolated_transient_limiting_gain", diag["flags"])
        self.assertTrue(diag["isolated_transient_peaks"])
        self.assertAlmostEqual(diag["isolated_transient_peaks"][0]["second"], 1.5, delta=0.1)

    def test_analyze_only_cli_runs_without_creating_master_files(self):
        self._write_two_segment_wave(self.src, amp1=0.05, freq1=190.0, amp2=0.12, freq2=240.0)
        code = master.main(["--analyze-only", "--episode-dir", str(self.root),
                            "--input", self.src.name, "--boundaries", "3.0"])
        self.assertEqual(code, 0)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.rec.exists())


if __name__ == "__main__":
    unittest.main()
