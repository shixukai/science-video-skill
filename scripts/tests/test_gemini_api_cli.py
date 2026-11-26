#!/usr/bin/env python3
"""Offline behavioral unit tests for scripts/gemini_api_cli.py (no live Gemini API calls)."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_episode  # noqa: E402
import gemini_api_cli  # noqa: E402


class _FakeProc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _ffprobe_json(width: int = 1920, height: int = 1080, fps: str = "24/1", duration: str = "7.833", audio: bool = True) -> str:
    streams = [
        {
            "codec_type": "video",
            "codec_name": "h264",
            "width": width,
            "height": height,
            "avg_frame_rate": fps,
            "r_frame_rate": fps,
            "duration": duration,
        }
    ]
    if audio:
        streams.append(
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": duration,
            }
        )
    return json.dumps({"streams": streams, "format": {"duration": duration}})


class GeminiApiCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.fake_bin = self.tmp / "gemini-api"
        self.fake_bin.write_text("#!/bin/sh\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_secret_redaction_strips_api_keys_and_tokens(self) -> None:
        raw = (
            "x-goog-api-key: AIzaSyDemoSecretKey1234567890123456 "
            "Authorization: Bearer ya29.a0AfB_secret_token_99999999 "
            "GEMINI_API_KEY=secret_env_val ?key=secret_q&ok=1"
        )
        cleaned = gemini_api_cli.redact_secrets(raw)
        self.assertNotIn("AIzaSyDemoSecretKey1234567890123456", cleaned)
        self.assertNotIn("ya29.a0AfB_secret_token_99999999", cleaned)
        self.assertNotIn("secret_env_val", cleaned)
        self.assertNotIn("secret_q", cleaned)
        self.assertIn("[REDACTED]", cleaned)

    def test_preflight_unavailable_returns_1_with_fallback(self) -> None:
        buf = io.StringIO()
        with (
            mock.patch.object(
                gemini_api_cli,
                "resolve_binary",
                return_value={"available": False, "binary": None, "source": "not_found", "host_os": "Windows", "reason": "missing"},
            ),
            mock.patch("sys.stdout", buf),
        ):
            rc = gemini_api_cli.main(["preflight"])
        self.assertEqual(rc, 1)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["status"], "unavailable")
        self.assertIn("google_flow_web", payload["fallback_modes"])
        self.assertEqual(payload["default_models"]["video"], "gemini-omni-1.2-flash")

    def test_preflight_unauthenticated_vs_ready_and_verify_live(self) -> None:
        def make_runner(api_key_source: str, live_ok: bool = True):
            def _run(cmd, **_kwargs):
                if "version" in cmd:
                    return _FakeProc(0, stdout=json.dumps({"name": "gemini-api", "version": "0.5.0"}))
                if "whoami" in cmd:
                    return _FakeProc(
                        0,
                        stdout=json.dumps(
                            {
                                "credentials": {
                                    "api-key": {"source": api_key_source, "value": "***"},
                                    "access-token": {"source": "unset", "value": ""},
                                },
                                "global_parameters": {"api-version": {"source": "default", "value": "v1beta"}},
                            }
                        ),
                    )
                if "models" in cmd and "list" in cmd:
                    return _FakeProc(0 if live_ok else 3, stdout='{"models": []}' if live_ok else "", stderr="" if live_ok else "invalid key")
                return _FakeProc(1, stderr=f"unexpected cmd: {cmd}")

            return _run

        buf1 = io.StringIO()
        with mock.patch("sys.stdout", buf1):
            rc1 = gemini_api_cli.main(["--binary", str(self.fake_bin), "preflight", "--check-auth"], runner=make_runner("unset"))
        self.assertEqual(rc1, 1)
        p1 = json.loads(buf1.getvalue())
        self.assertEqual(p1["status"], "unauthenticated")
        self.assertFalse(p1["auth_configured"])

        rep_ok = self.tmp / "preflight_ok.json"
        buf2 = io.StringIO()
        with mock.patch("sys.stdout", buf2):
            rc2 = gemini_api_cli.main(
                ["--binary", str(self.fake_bin), "preflight", "--check-auth", "--verify-live", "--report", str(rep_ok)],
                runner=make_runner("env", live_ok=True),
            )
        self.assertEqual(rc2, 0)
        p2 = json.loads(buf2.getvalue())
        self.assertEqual(p2["status"], "ready")
        self.assertTrue(p2["auth_configured"])
        self.assertTrue(p2["live_models_checked"])
        self.assertEqual(p2["version"], "0.5.0")
        self.assertTrue(rep_ok.is_file())

    def test_video_blocks_720p_without_allow_proxy_and_supports_dry_run_body_merge(self) -> None:
        err_buf = io.StringIO()
        with mock.patch("sys.stderr", err_buf):
            rc = gemini_api_cli.main(["--binary", str(self.fake_bin), "video", "steam rising", "--resolution", "720p"])
        self.assertEqual(rc, 2)
        self.assertIn(">= 1080p", err_buf.getvalue())

        seen_cmds: list[list[str]] = []

        def fake_run(cmd, **_kwargs):
            seen_cmds.append(cmd)
            return _FakeProc(0, stdout=json.dumps({"method": "POST", "url": "https://generativelanguage.googleapis.com/v1beta/interactions"}))

        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            rc2 = gemini_api_cli.main(
                [
                    "--binary",
                    str(self.fake_bin),
                    "video",
                    "Glass valve opening under heat. Audio: soft glass tap.",
                    "--duration",
                    "8s",
                    "--previous-interaction-id",
                    "v1_prev123",
                    "--dry-run",
                ],
                runner=fake_run,
            )
        self.assertEqual(rc2, 0)
        self.assertEqual(len(seen_cmds), 1)
        cmd = seen_cmds[0]
        self.assertIn("--no-interactive", cmd)
        self.assertIn("--dry-run", cmd)
        self.assertIn("--output-format", cmd)
        body_idx = cmd.index("--body") + 1
        body = json.loads(cmd[body_idx])
        self.assertEqual(body["model"], "gemini-omni-1.2-flash")
        self.assertEqual(body["response_format"]["type"], "video")
        self.assertEqual(body["response_format"]["aspect_ratio"], "16:9")
        self.assertEqual(body["response_format"]["resolution"], "1080p")
        self.assertEqual(body["response_format"]["duration"], "8s")
        self.assertNotIn("store", body)
        self.assertEqual(body["previous_interaction_id"], "v1_prev123")

        # Reject store=false in --body for background video interactions
        err_store = io.StringIO()
        with mock.patch("sys.stderr", err_store):
            rc3 = gemini_api_cli.main(
                [
                    "--binary",
                    str(self.fake_bin),
                    "video",
                    "Glass valve",
                    "--body",
                    '{"store": false}',
                    "--dry-run",
                ],
                runner=fake_run,
            )
        self.assertEqual(rc3, 2)
        self.assertIn("store=false", err_store.getvalue())

    def test_video_auto_uploads_large_input_updates_ledger_and_probes_hd(self) -> None:
        large_img = self.tmp / "tail_frame_big.png"
        large_img.write_bytes(b"0" * 16)  # patched size below
        out_mp4 = self.tmp / "clips" / "SH01.mp4"
        ledger = self.tmp / "prompt-ledger.json"
        receipt = self.tmp / "sh01-receipt.json"
        seen_cmds: list[list[str]] = []

        def fake_run(cmd, **_kwargs):
            seen_cmds.append(cmd)
            if cmd[0] == "ffprobe":
                return _FakeProc(0, stdout=_ffprobe_json(1920, 1080, "24/1", "7.833"))
            if "files" in cmd and "upload" in cmd:
                return _FakeProc(0, stdout=json.dumps({"name": "files/abc123def"}))
            if "video" in cmd:
                out_mp4.parent.mkdir(parents=True, exist_ok=True)
                out_mp4.write_bytes(b"fake-mp4-bytes")
                return _FakeProc(
                    0,
                    stdout=json.dumps(
                        {
                            "kind": "video",
                            "mime_type": "video/mp4",
                            "path": str(out_mp4),
                            "size_bytes": 14,
                            "response_id": "v1_video_sh01",
                            "status": "completed",
                        }
                    ),
                )
            return _FakeProc(1, stderr=f"unexpected cmd: {cmd}")

        buf = io.StringIO()
        with (
            mock.patch.object(gemini_api_cli, "MAX_INLINE_RAW_BYTES", 8),
            mock.patch("sys.stdout", buf),
        ):
            rc = gemini_api_cli.main(
                [
                    "--binary",
                    str(self.fake_bin),
                    "video",
                    "High-speed steam valve snap. Audio: crisp metallic click.",
                    "-i",
                    str(large_img),
                    "--shot-id",
                    "SH01",
                    "--ledger",
                    str(ledger),
                    "--out",
                    str(out_mp4),
                    "--receipt",
                    str(receipt),
                ],
                runner=fake_run,
            )
        self.assertEqual(rc, 0)
        # Upload called first, then video with files/abc123def, then ffprobe
        self.assertEqual(len(seen_cmds), 3)
        self.assertIn("files", seen_cmds[0])
        self.assertIn("--wait", seen_cmds[0])
        self.assertIn("files/abc123def", seen_cmds[1])
        self.assertIn("--resolution", seen_cmds[1])
        self.assertIn("1080p", seen_cmds[1])
        self.assertEqual(seen_cmds[2][0], "ffprobe")

        saved_receipt = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(saved_receipt["entry"]["status"], "completed")
        self.assertEqual(saved_receipt["entry"]["response_id"], "v1_video_sh01")
        self.assertEqual(saved_receipt["entry"]["flags"], [])
        self.assertEqual(saved_receipt["review_status"], "generated_unreviewed")

        saved_ledger = json.loads(ledger.read_text(encoding="utf-8"))
        self.assertEqual(len(saved_ledger["entries"]), 1)
        self.assertEqual(saved_ledger["entries"][0]["shot_id"], "SH01")
        self.assertEqual(saved_ledger["entries"][0]["response_id"], "v1_video_sh01")

    def test_video_flags_720p_actual_output_and_refuses_receipt_overwrite(self) -> None:
        out_mp4 = self.tmp / "SH02.mp4"
        receipt = self.tmp / "sh02-receipt.json"

        def fake_run(cmd, **_kwargs):
            if cmd[0] == "ffprobe":
                return _FakeProc(0, stdout=_ffprobe_json(1280, 720, "24/1", "7.833"))
            out_mp4.write_bytes(b"720p-bytes")
            return _FakeProc(0, stdout=json.dumps({"kind": "video", "path": str(out_mp4), "response_id": "v1_720"}))

        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            rc = gemini_api_cli.main(
                ["--binary", str(self.fake_bin), "video", "Water boiling", "--out", str(out_mp4), "--receipt", str(receipt)],
                runner=fake_run,
            )
        self.assertEqual(rc, 1)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(data["entry"]["status"], "flagged")
        self.assertEqual(data["entry"]["flags"][0]["code"], "low_res_generated_clip")

        # Refuse overwriting existing receipt
        err_buf = io.StringIO()
        with mock.patch("sys.stderr", err_buf):
            rc2 = gemini_api_cli.main(
                ["--binary", str(self.fake_bin), "video", "Water boiling", "--dry-run", "--receipt", str(receipt)],
                runner=fake_run,
            )
        self.assertEqual(rc2, 2)
        self.assertIn("Refusing to overwrite", err_buf.getvalue())

    def test_async_submission_and_resume_recovery(self) -> None:
        ledger = self.tmp / "ledger.json"
        out_mp4 = self.tmp / "SH03.mp4"
        rec_async = self.tmp / "sh03-async.json"
        rec_resume = self.tmp / "sh03-resume.json"

        def fake_async(cmd, **_kwargs):
            self.assertIn("--async", cmd)
            return _FakeProc(0, stdout=json.dumps({"id": "v1_async_99", "status": "in_progress"}))

        with mock.patch("sys.stdout", io.StringIO()):
            rc1 = gemini_api_cli.main(
                [
                    "--binary",
                    str(self.fake_bin),
                    "video",
                    "Spring latch snapping",
                    "--async",
                    "--shot-id",
                    "SH03",
                    "--ledger",
                    str(ledger),
                    "--receipt",
                    str(rec_async),
                ],
                runner=fake_async,
            )
        self.assertEqual(rc1, 0)
        d1 = json.loads(rec_async.read_text(encoding="utf-8"))
        self.assertEqual(d1["entry"]["status"], "submitted_async")
        self.assertEqual(d1["entry"]["response_id"], "v1_async_99")

        def fake_resume(cmd, **_kwargs):
            if cmd[0] == "ffprobe":
                return _FakeProc(0, stdout=_ffprobe_json(1920, 1080, "24/1", "7.833"))
            self.assertIn("--resume", cmd)
            self.assertIn("v1_async_99", cmd)
            out_mp4.write_bytes(b"resumed-mp4")
            return _FakeProc(0, stdout=json.dumps({"kind": "video", "path": str(out_mp4), "response_id": "v1_async_99", "status": "completed"}))

        with mock.patch("sys.stdout", io.StringIO()):
            rc2 = gemini_api_cli.main(
                [
                    "--binary",
                    str(self.fake_bin),
                    "resume",
                    "v1_async_99",
                    "--shot-id",
                    "SH03",
                    "--ledger",
                    str(ledger),
                    "--out",
                    str(out_mp4),
                    "--receipt",
                    str(rec_resume),
                ],
                runner=fake_resume,
            )
        self.assertEqual(rc2, 0)
        d2 = json.loads(rec_resume.read_text(encoding="utf-8"))
        self.assertEqual(d2["entry"]["status"], "completed")
        self.assertEqual(d2["entry"]["flags"], [])

    def test_image_and_music_commands(self) -> None:
        cover_jpg = self.tmp / "cover_3_4_raw.jpg"
        bgm_wav = self.tmp / "bgm.wav"

        def fake_img(cmd, **_kwargs):
            self.assertIn("image", cmd)
            self.assertIn("3:4", cmd)
            self.assertIn("2K", cmd)
            cover_jpg.write_bytes(b"fake-jpg")
            return _FakeProc(0, stdout=json.dumps({"kind": "image", "path": str(cover_jpg), "response_id": "v1_img_1"}))

        rec_img = self.tmp / "img.json"
        with mock.patch("sys.stdout", io.StringIO()):
            rc_img = gemini_api_cli.main(
                [
                    "--binary",
                    str(self.fake_bin),
                    "image",
                    "Macro studio shot of safety hammer hitting tempered bus window, clean upper left sky, no text",
                    "--aspect-ratio",
                    "3:4",
                    "--out",
                    str(cover_jpg),
                    "--receipt",
                    str(rec_img),
                ],
                runner=fake_img,
            )
        self.assertEqual(rc_img, 0)
        self.assertEqual(json.loads(rec_img.read_text(encoding="utf-8"))["entry"]["response_id"], "v1_img_1")

        def fake_music(cmd, **_kwargs):
            if cmd[0] == "ffprobe":
                return _FakeProc(0, stdout=json.dumps({"streams": [{"codec_type": "audio", "codec_name": "pcm_s16le", "sample_rate": "48000", "duration": "30.0"}], "format": {"duration": "30.0"}}))
            self.assertIn("music", cmd)
            self.assertIn("lyria-3.5", cmd)
            bgm_wav.write_bytes(b"fake-wav")
            return _FakeProc(0, stdout=json.dumps({"kind": "audio", "path": str(bgm_wav)}))

        rec_mus = self.tmp / "music.json"
        with mock.patch("sys.stdout", io.StringIO()):
            rc_mus = gemini_api_cli.main(
                ["--binary", str(self.fake_bin), "music", "Subtle documentary pulse", "--out", str(bgm_wav), "--receipt", str(rec_mus)],
                runner=fake_music,
            )
        self.assertEqual(rc_mus, 0)
        self.assertEqual(json.loads(rec_mus.read_text(encoding="utf-8"))["status"], "completed")

    def test_tts_emits_check_episode_compatible_cloud_generation_record(self) -> None:
        script_txt = self.tmp / "script.en.txt"
        script_txt.write_text("Heat expands the trapped vapor smoothly.\n", encoding="utf-8")
        out_wav = self.tmp / "narration.en.wav"
        rec_tts = self.tmp / "tts_en_gen.json"

        def fake_tts(cmd, **_kwargs):
            if cmd[0] == "ffprobe":
                return _FakeProc(0, stdout=json.dumps({"streams": [{"codec_type": "audio", "codec_name": "pcm_s16le", "sample_rate": "24000", "duration": "3.2"}], "format": {"duration": "3.2"}}))
            self.assertIn("tts", cmd)
            self.assertIn("gemini-3.8-flash-tts", cmd)
            out_wav.write_bytes(b"RIFFfakewav")
            return _FakeProc(0, stdout=json.dumps({"model": "gemini-3.8-flash-tts", "path": str(out_wav), "mime_type": "audio/l16", "size_bytes": 11}))

        with mock.patch("sys.stdout", io.StringIO()):
            rc = gemini_api_cli.main(
                [
                    "--binary",
                    str(self.fake_bin),
                    "tts",
                    "--script-file",
                    str(script_txt),
                    "--language",
                    "en-US",
                    "--voice",
                    "Kore",
                    "--episode-dir",
                    str(self.tmp),
                    "--out",
                    str(out_wav),
                    "--receipt",
                    str(rec_tts),
                ],
                runner=fake_tts,
            )
        self.assertEqual(rc, 0)
        record = json.loads(rec_tts.read_text(encoding="utf-8"))
        self.assertTrue(check_episode.cloud_voice_execution(record["execution"]))
        errors: list[str] = []

        def need(ok, msg):
            if not ok:
                errors.append(msg)
            return bool(ok)

        def evidence(ref, label):
            self.assertIsInstance(ref, dict, label)
            p = self.tmp / ref["file"]
            self.assertTrue(p.is_file(), label)
            self.assertEqual(gemini_api_cli.sha256_file(p), ref["sha256"])

        check_episode.check_cloud_voice_generation(record, need, evidence, "narration:", "English")
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
