#!/usr/bin/env python3
"""Offline behavioral unit tests for scripts/colab_cli.py (no live Colab allocation)."""
from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import colab_cli  # noqa: E402


class _FakeProc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class ColabCliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_gpu_validation_and_cycles_backend_auto_selection(self):
        self.assertEqual(colab_cli.normalize_gpu("a100"), "A100")
        self.assertEqual(colab_cli.normalize_gpu("G4"), "G4")
        with self.assertRaises(ValueError):
            colab_cli.normalize_gpu("RTX4090")

        # Non-RT datacenter GPUs default to CUDA to avoid OptiX compilation stalls
        self.assertEqual(colab_cli.choose_cycles_backend("A100", "auto"), "CUDA")
        self.assertEqual(colab_cli.choose_cycles_backend("H100", "auto"), "CUDA")
        self.assertEqual(colab_cli.choose_cycles_backend("T4", "auto"), "CUDA")
        # RT-capable Colab GPUs default to OPTIX (with runtime CUDA fallback inside shard script)
        self.assertEqual(colab_cli.choose_cycles_backend("G4", "auto"), "OPTIX")
        self.assertEqual(colab_cli.choose_cycles_backend("L4", "auto"), "OPTIX")
        # Explicit override is honored
        self.assertEqual(colab_cli.choose_cycles_backend("A100", "OPTIX"), "OPTIX")
        self.assertEqual(colab_cli.choose_cycles_backend("G4", "CUDA"), "CUDA")

    def test_transfer_spec_parsing_and_wsl_path_conversion(self):
        loc, rem = colab_cli.parse_transfer_spec(r"D:\work\shot.blend:/content/shot.blend", direction="upload")
        self.assertEqual(loc, r"D:\work\shot.blend")
        self.assertEqual(rem, "/content/shot.blend")

        rem2, loc2 = colab_cli.parse_transfer_spec(r"/content/out.mp4:D:\renders\out.mp4", direction="download")
        self.assertEqual(rem2, "/content/out.mp4")
        self.assertEqual(loc2, r"D:\renders\out.mp4")

        self.assertEqual(colab_cli.windows_to_wsl_path(r"C:\SvColabUnitTest\clip.mp4"), "/mnt/c/SvColabUnitTest/clip.mp4")

    def test_secret_redaction_strips_bearer_and_oauth_tokens(self):
        raw = "Authorization: Bearer super_secret_tok123 ya29.a0AfB_secret_token_99999999 ?access_token=abc123&x=1"
        cleaned = colab_cli.redact_secrets(raw)
        self.assertNotIn("super_secret_tok123", cleaned)
        self.assertNotIn("ya29.a0AfB_secret_token_99999999", cleaned)
        self.assertNotIn("abc123", cleaned)
        self.assertIn("[REDACTED]", cleaned)

    def test_global_flags_placed_before_subcommand(self):
        info = {"available": True, "transport": "native", "prefix": ["colab"], "host_os": "Linux"}
        cfg_file = self.tmp / "agent-sessions.json"
        cmd = colab_cli.build_colab_cmd(
            info,
            ["new", "-s", "ep01-sh1", "--gpu", "A100"],
            auth="adc",
            config_path=str(cfg_file),
        )
        self.assertEqual(cmd[:5], ["colab", "--auth=adc", "--config", str(cfg_file.resolve()), "new"])

    def test_preflight_unavailable_returns_1_with_fallback_modes(self):
        buf = io.StringIO()
        with (
            mock.patch.object(colab_cli, "resolve_transport", return_value={
                "available": False, "transport": "unavailable", "prefix": [], "host_os": "Windows", "reason": "not installed",
            }),
            mock.patch("sys.stdout", buf),
        ):
            rc = colab_cli.main(["preflight"])
        self.assertEqual(rc, 1)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["status"], "unavailable")
        self.assertIn("https_tunnel", payload["fallback_modes"])
        self.assertIn("local_gpu", payload["fallback_modes"])

    def test_preflight_ready_with_check_auth(self):
        calls = []

        def fake_run(cmd, **_kwargs):
            calls.append(cmd)
            if "version" in cmd:
                return _FakeProc(0, stdout="0.8.0\n")
            if "sessions" in cmd:
                return _FakeProc(0, stdout="No active sessions.\n")
            if "usage" in cmd:
                return _FakeProc(0, stdout="Current balance: 100.0 compute units\n")
            return _FakeProc(1, stderr="unexpected")

        buf = io.StringIO()
        with (
            mock.patch.object(colab_cli, "resolve_transport", return_value={
                "available": True, "transport": "native", "prefix": ["colab"], "host_os": "Linux", "wsl_distro": None,
            }),
            mock.patch("sys.stdout", buf),
        ):
            args = colab_cli.build_parser().parse_args(["--auth", "adc", "preflight", "--check-auth"])
            rc = colab_cli.cmd_preflight(args, runner=fake_run)
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["version"], "0.8.0")
        self.assertTrue(payload["auth_ok"])
        self.assertEqual(calls[0], ["colab", "--auth=adc", "version"])
        self.assertEqual(calls[1], ["colab", "--auth=adc", "sessions"])
        self.assertEqual(calls[2], ["colab", "--auth=adc", "usage"])

    def test_ephemeral_run_guarantees_stop_on_exec_failure_and_redacts_env(self):
        script = self.tmp / "job.py"
        script.write_text("print('hi')\n", encoding="utf-8")
        asset = self.tmp / "frame.png"
        asset.write_bytes(b"png-bytes-1234")
        receipt_path = self.tmp / "receipt-fail.json"
        calls = []

        def fake_run(cmd, **_kwargs):
            calls.append(cmd)
            if "new" in cmd:
                return _FakeProc(0, stdout="allocated\n")
            if "upload" in cmd:
                return _FakeProc(0, stdout="uploaded\n")
            if "exec" in cmd:
                return _FakeProc(1, stderr="RuntimeError: Bearer secret_token_xyz failed\n")
            if "stop" in cmd:
                return _FakeProc(0, stdout="stopped\n")
            return _FakeProc(1, stderr="unexpected")

        buf = io.StringIO()
        with (
            mock.patch.object(colab_cli, "resolve_transport", return_value={
                "available": True, "transport": "native", "prefix": ["colab"], "host_os": "Linux", "wsl_distro": None,
            }),
            mock.patch("sys.stdout", buf),
        ):
            args = colab_cli.build_parser().parse_args([
                "--auth", "adc",
                "run-ephemeral",
                "-s", "ep-fail-01",
                "--gpu", "A100",
                "--script", str(script),
                "--upload", f"{asset}:/content/frame.png",
                "--env", "API_SECRET=never_write_this_value",
                "--receipt", str(receipt_path),
            ])
            rc = colab_cli.cmd_run_ephemeral(args, runner=fake_run)

        self.assertEqual(rc, 1)
        # Guaranteed teardown even though exec failed
        self.assertEqual(calls[-1], ["colab", "--auth=adc", "stop", "-s", "ep-fail-01"])
        rec = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(rec["status"], "exec_failed")
        self.assertTrue(rec["teardown_attempted"])
        self.assertTrue(rec["teardown_ok"])
        self.assertEqual(rec["env_keys"], ["API_SECRET"])
        self.assertEqual(rec["review_status"], "complete_unreviewed")
        text = receipt_path.read_text(encoding="utf-8")
        self.assertNotIn("never_write_this_value", text)
        self.assertNotIn("secret_token_xyz", text)

    def test_blender_render_rejects_non_hd_without_allow_proxy_and_supports_dry_run(self):
        blend = self.tmp / "scene.blend"
        blend.write_bytes(b"BLENDER_FAKE_PACKED")
        out_mp4 = self.tmp / "render.mp4"
        receipt = self.tmp / "blender-dry.json"

        # Non-HD rejected before allocating VM unless --allow-proxy
        err_buf = io.StringIO()
        with mock.patch("sys.stderr", err_buf):
            rc_low = colab_cli.main([
                "blender-render",
                "-s", "bl-test",
                "--blend", str(blend),
                "--frame-start", "1",
                "--frame-end", "30",
                "--width", "960",
                "--height", "540",
                "--output", str(out_mp4),
                "--dry-run",
            ])
        self.assertEqual(rc_low, 2)
        self.assertIn("short edge < 1080", err_buf.getvalue())

        # Valid 1080p dry-run works offline without invoking colab
        out_buf = io.StringIO()
        with (
            mock.patch.object(colab_cli, "resolve_transport", return_value={
                "available": False, "transport": "unavailable", "prefix": [], "host_os": "Windows", "reason": "not installed",
            }),
            mock.patch("sys.stdout", out_buf),
        ):
            rc_ok = colab_cli.main([
                "--auth", "adc",
                "blender-render",
                "-s", "bl-a100-01",
                "--gpu", "A100",
                "--blend", str(blend),
                "--frame-start", "1",
                "--frame-end", "60",
                "--output", str(out_mp4),
                "--dry-run",
                "--receipt", str(receipt),
            ])
        self.assertEqual(rc_ok, 0)
        rec = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertTrue(rec["dry_run"])
        self.assertEqual(rec["blender_render"]["selected_backend"], "CUDA")
        self.assertEqual(rec["uploads"][0]["bytes"], len(b"BLENDER_FAKE_PACKED"))
        self.assertEqual(rec["review_status"], "complete_unreviewed")
        # Refuses overwriting existing receipt
        err_buf2 = io.StringIO()
        with mock.patch("sys.stderr", err_buf2):
            rc_dup = colab_cli.main([
                "blender-render",
                "-s", "bl-a100-01",
                "--blend", str(blend),
                "--frame-start", "1",
                "--frame-end", "60",
                "--output", str(out_mp4),
                "--dry-run",
                "--receipt", str(receipt),
            ])
        self.assertEqual(rc_dup, 2)

    def test_blender_render_happy_path_downloads_mp4_and_stops_vm(self):
        blend = self.tmp / "scene.blend"
        blend.write_bytes(b"BLENDER_PACKED_BYTES")
        out_mp4 = self.tmp / "out" / "shot.mp4"
        receipt = self.tmp / "blender-ok.json"
        calls = []

        def fake_run(cmd, **_kwargs):
            calls.append(cmd)
            if "download" in cmd:
                remote = cmd[-2]
                local = Path(cmd[-1])
                local.parent.mkdir(parents=True, exist_ok=True)
                if remote.endswith(".mp4"):
                    local.write_bytes(b"FAKE_MP4_DATA")
                elif remote.endswith("_meta.json"):
                    local.write_text(json.dumps({"gpu": "NVIDIA A100-SXM4-80GB", "total_frames": 30}), encoding="utf-8")
            return _FakeProc(0, stdout="ok\n")

        out_buf = io.StringIO()
        with (
            mock.patch.object(colab_cli, "resolve_transport", return_value={
                "available": True, "transport": "native", "prefix": ["colab"], "host_os": "Linux", "wsl_distro": None,
            }),
            mock.patch("sys.stdout", out_buf),
        ):
            args = colab_cli.build_parser().parse_args([
                "blender-render",
                "-s", "ep02-sh3",
                "--gpu", "G4",
                "--blend", str(blend),
                "--frame-start", "1",
                "--frame-end", "30",
                "--output", str(out_mp4),
                "--receipt", str(receipt),
            ])
            rc = colab_cli.cmd_blender_render(args, runner=fake_run)

        self.assertEqual(rc, 0)
        self.assertTrue(out_mp4.is_file())
        rec = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(rec["status"], "completed")
        self.assertEqual(rec["blender_render"]["selected_backend"], "OPTIX")
        self.assertTrue(rec["teardown_ok"])
        self.assertEqual(rec["remote_blender_meta"]["gpu"], "NVIDIA A100-SXM4-80GB")
        self.assertEqual(calls[0], ["colab", "new", "-s", "ep02-sh3", "--gpu", "G4"])
        self.assertEqual(calls[-1], ["colab", "stop", "-s", "ep02-sh3"])


if __name__ == "__main__":
    unittest.main()
