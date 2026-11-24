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
        self.assertEqual(rec["blender_render"]["modeling_profile"], "high_poly_industrial_v1")
        self.assertEqual(rec["blender_render"]["adaptive_threshold"], 0.015)
        self.assertEqual(rec["blender_render"]["denoising_input_passes"], "RGB_ALBEDO_NORMAL")
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

    def test_evaluate_industrial_audit_passes_clean_high_poly_scene(self):
        stats = {
            "frame": 1,
            "mesh_object_count": 3,
            "evaluated_polygon_count": 48200,
            "evaluated_triangle_count": 96400,
            "meshes": [
                {
                    "name": "CNC_Housing_Main",
                    "polygon_count": 32000,
                    "triangle_count": 64000,
                    "smooth_face_ratio": 0.92,
                    "modifiers": ["BEVEL", "WEIGHTED_NORMAL"],
                    "has_bevel": True,
                    "has_subsurf": False,
                    "has_weighted_normal": True,
                    "has_solidify": False,
                    "has_node_material": True,
                },
                {
                    "name": "ISO4762_M6_Bolts",
                    "polygon_count": 16199,
                    "triangle_count": 32398,
                    "smooth_face_ratio": 0.85,
                    "modifiers": ["BEVEL", "EDGE_SPLIT"],
                    "has_bevel": True,
                    "has_subsurf": False,
                    "has_weighted_normal": True,
                    "has_solidify": False,
                    "has_node_material": True,
                },
                {
                    "name": "Graphite_Workbench_Floor",
                    "polygon_count": 1,
                    "triangle_count": 2,
                    "smooth_face_ratio": 0.0,
                    "modifiers": [],
                    "has_bevel": False,
                    "has_subsurf": False,
                    "has_weighted_normal": False,
                    "has_solidify": False,
                    "has_node_material": True,
                },
            ],
            "non_uniform_scale_objects": [],
            "unapplied_uniform_scale_objects": [],
            "viewport_only_material_objects": [],
            "has_active_rigidbody_world": False,
            "unpacked_external_images": [],
            "missing_libraries": [],
            "color_management": {"display_device": "sRGB", "view_transform": "AgX", "look": "None", "exposure": 0.0, "gamma": 1.0},
            "cycles_bounces": {"max_bounces": 12, "glossy_bounces": 4, "transmission_bounces": 12, "diffuse_bounces": 4},
        }
        audit = colab_cli.evaluate_industrial_audit(stats, shards=2)
        self.assertEqual(audit["profile"], "high_poly_industrial_v1")
        self.assertEqual(audit["review_status"], "technical_screening_only_not_visual_acceptance")
        self.assertTrue(audit["passed"])
        self.assertTrue(audit["strict_passed"])
        self.assertEqual(audit["blocking_issues"], [])
        self.assertEqual(audit["warnings"], [])

    def test_evaluate_industrial_audit_flags_low_poly_flat_unbaked_and_unpacked_defects(self):
        stats = {
            "frame": 1,
            "mesh_object_count": 2,
            "evaluated_polygon_count": 48,
            "evaluated_triangle_count": 96,
            "meshes": [
                {
                    "name": "Toy_Cylinder_16seg",
                    "polygon_count": 32,
                    "triangle_count": 64,
                    "smooth_face_ratio": 0.0,
                    "modifiers": [],
                    "has_bevel": False,
                    "has_subsurf": False,
                    "has_weighted_normal": False,
                    "has_solidify": False,
                    "has_node_material": False,
                },
                {
                    "name": "Beveled_Cap_NoWN",
                    "polygon_count": 16,
                    "triangle_count": 32,
                    "smooth_face_ratio": 1.0,
                    "modifiers": ["BEVEL"],
                    "has_bevel": True,
                    "has_subsurf": False,
                    "has_weighted_normal": False,
                    "has_solidify": False,
                    "has_node_material": True,
                },
            ],
            "non_uniform_scale_objects": [{"name": "Toy_Cylinder_16seg", "scale": [1.0, 1.0, 2.5]}],
            "unapplied_uniform_scale_objects": [{"name": "Beveled_Cap_NoWN", "scale": [0.5, 0.5, 0.5]}],
            "viewport_only_material_objects": ["Toy_Cylinder_16seg"],
            "has_active_rigidbody_world": True,
            "unpacked_external_images": ["brushed_metal.png"],
            "missing_libraries": ["//missing_cad.blend"],
        }
        audit = colab_cli.evaluate_industrial_audit(stats, shards=2)
        self.assertFalse(audit["passed"])
        self.assertFalse(audit["strict_passed"])
        blocking_codes = {item["code"] for item in audit["blocking_issues"]}
        warning_codes = {item["code"] for item in audit["warnings"]}
        self.assertEqual(
            blocking_codes,
            {
                "unbaked_rigidbody_world",
                "unpacked_external_images",
                "missing_linked_libraries",
                "viewport_only_materials",
                "non_uniform_scale",
            },
        )
        self.assertEqual(
            warning_codes,
            {
                "low_poly_scene",
                "flat_shaded_curved_meshes",
                "unbeveled_low_detail_meshes",
                "beveled_without_weighted_normal",
                "unapplied_uniform_scale",
            },
        )

        # Custom profile suppresses high-poly-specific geometry warnings while retaining Colab render blockers
        custom_audit = colab_cli.evaluate_industrial_audit(stats, modeling_profile="custom", shards=2)
        self.assertEqual(custom_audit["profile"], "custom")
        self.assertFalse(custom_audit["passed"])
        self.assertEqual({item["code"] for item in custom_audit["warnings"]}, {"unapplied_uniform_scale"})

    def test_remote_blender_driver_compiles_with_oidn_albedo_normal_and_audit(self):
        driver_src = colab_cli._build_remote_blender_driver(
            remote_blend="/content/hero.blend",
            remote_mp4="/content/out.mp4",
            remote_meta="/content/meta.json",
            frame_start=1,
            frame_end=120,
            samples=96,
            width=1920,
            height=1080,
            fps=30,
            crf=14,
            shards=2,
            backend="CUDA",
            blender_url=colab_cli.DEFAULT_BLENDER_LINUX_URL,
            adaptive_threshold=0.012,
            modeling_profile="high_poly_industrial",
            min_scene_triangles=40000,
            strict_modeling_audit=True,
        )
        compile(driver_src, "<remote_blender_driver>", "exec")
        compile(colab_cli._INDUSTRIAL_AUDIT_BLENDER_CODE, "<industrial_audit_blender>", "exec")
        self.assertIn("RGB_ALBEDO_NORMAL", driver_src)
        self.assertIn("industrial_modeling_audit", driver_src)
        self.assertIn("0.012", driver_src)
        self.assertIn("strict_modeling_audit", driver_src)

    def test_audit_blend_cli_runs_headless_blender_and_enforces_strict_mode(self):
        blend = self.tmp / "hero.blend"
        blend.write_bytes(b"BLENDER_FAKE")
        fake_blender = self.tmp / "blender.exe"
        fake_blender.write_bytes(b"FAKE_BIN")
        report_warn = self.tmp / "audit-warn.json"
        report_strict = self.tmp / "audit-strict.json"

        low_poly_stats = {
            "frame": 10,
            "mesh_object_count": 1,
            "evaluated_polygon_count": 32,
            "evaluated_triangle_count": 64,
            "meshes": [{
                "name": "LowPoly_Tube",
                "polygon_count": 32,
                "triangle_count": 64,
                "smooth_face_ratio": 0.0,
                "modifiers": [],
                "has_bevel": False,
                "has_subsurf": False,
                "has_weighted_normal": False,
                "has_solidify": False,
                "has_node_material": True,
            }],
            "non_uniform_scale_objects": [],
            "unapplied_uniform_scale_objects": [],
            "viewport_only_material_objects": [],
            "has_active_rigidbody_world": False,
            "unpacked_external_images": [],
            "missing_libraries": [],
        }

        def fake_blender_run(cmd, **_kwargs):
            out_idx = cmd.index("--out-json") + 1
            Path(cmd[out_idx]).write_text(json.dumps(low_poly_stats), encoding="utf-8")
            return _FakeProc(0, stdout="INDUSTRIAL_AUDIT_STATS=" + json.dumps(low_poly_stats) + "\n")

        # Non-strict mode passes (exit 0) when only advisory high-poly warnings exist
        out1 = io.StringIO()
        with mock.patch("sys.stdout", out1):
            args1 = colab_cli.build_parser().parse_args([
                "audit-blend",
                "--blend", str(blend),
                "--blender", str(fake_blender),
                "--frame", "10",
                "--report", str(report_warn),
            ])
            rc1 = colab_cli.cmd_audit_blend(args1, runner=fake_blender_run)
        self.assertEqual(rc1, 0)
        rec1 = json.loads(report_warn.read_text(encoding="utf-8"))
        self.assertTrue(rec1["passed"])
        self.assertFalse(rec1["strict_passed"])
        self.assertTrue(any(w["code"] == "low_poly_scene" for w in rec1["warnings"]))

        # Strict mode fails (exit 1) when high-poly industrial warnings exist
        out2 = io.StringIO()
        with mock.patch("sys.stdout", out2):
            args2 = colab_cli.build_parser().parse_args([
                "audit-blend",
                "--blend", str(blend),
                "--blender", str(fake_blender),
                "--strict",
                "--report", str(report_strict),
            ])
            rc2 = colab_cli.cmd_audit_blend(args2, runner=fake_blender_run)
        self.assertEqual(rc2, 1)
        self.assertTrue(report_strict.is_file())

        # Existing report cannot be overwritten silently
        err3 = io.StringIO()
        with mock.patch("sys.stderr", err3):
            args3 = colab_cli.build_parser().parse_args([
                "audit-blend",
                "--blend", str(blend),
                "--blender", str(fake_blender),
                "--report", str(report_strict),
            ])
            rc3 = colab_cli.cmd_audit_blend(args3, runner=fake_blender_run)
        self.assertEqual(rc3, 2)

    def test_industrial_audit_flags_hollow_single_stage_glide(self):
        base_stats = {
            "frame": 1,
            "mesh_object_count": 2,
            "evaluated_polygon_count": 20000,
            "evaluated_triangle_count": 40000,
            "meshes": [{
                "name": "HeroAssembly",
                "polygon_count": 20000,
                "triangle_count": 40000,
                "smooth_face_ratio": 0.9,
                "modifiers": ["BEVEL", "WEIGHTED_NORMAL"],
                "has_bevel": True,
                "has_subsurf": False,
                "has_weighted_normal": True,
                "has_solidify": True,
                "has_node_material": True,
            }],
            "non_uniform_scale_objects": [],
            "unapplied_uniform_scale_objects": [],
            "viewport_only_material_objects": [],
            "has_active_rigidbody_world": False,
            "unpacked_external_images": [],
            "missing_libraries": [],
        }
        hollow = dict(base_stats, camera_staging={
            "fps": 30.0, "frame_start": 0, "frame_end": 1200,
            "duration_s": 40.0, "hard_cut_count": 1, "hard_cut_times_s": [4.3],
            "longest_unbroken_shot_s": 35.7,
        })
        res_hollow = colab_cli.evaluate_industrial_audit(hollow)
        self.assertTrue(any(w["code"] == "hollow_single_stage_glide" for w in res_hollow["warnings"]))

        multi_cut = dict(base_stats, camera_staging={
            "fps": 30.0, "frame_start": 0, "frame_end": 1200,
            "duration_s": 40.0, "hard_cut_count": 6, "hard_cut_times_s": [4.0, 9.5, 16.0, 22.0, 28.5, 34.0],
            "longest_unbroken_shot_s": 6.5,
        })
        res_multi = colab_cli.evaluate_industrial_audit(multi_cut)
        self.assertFalse(any(w["code"] == "hollow_single_stage_glide" for w in res_multi["warnings"]))
        self.assertTrue(res_multi["strict_passed"])

    def test_blender_stills_dry_run_and_frame_spec_parser(self):
        parsed = colab_cli.parse_still_frames_spec("01_hook:16, 02_shatter:84, 200")
        self.assertEqual(parsed, [("01_hook_f0016", 16), ("02_shatter_f0084", 84), ("frame_0200", 200)])
        with self.assertRaises(ValueError):
            colab_cli.parse_still_frames_spec("bad:abc")

        blend = self.tmp / "lookdev.blend"
        blend.write_bytes(b"BLENDER_STILLS_TEST")
        out_dir = self.tmp / "stills_out"
        receipt = self.tmp / "stills-receipt.json"
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            args = colab_cli.build_parser().parse_args([
                "blender-stills",
                "-s", "stills-test",
                "--blend", str(blend),
                "--frames", "hook:16,quench:350",
                "--out-dir", str(out_dir),
                "--gpu", "G4",
                "--dry-run",
                "--receipt", str(receipt),
            ])
            rc = colab_cli.cmd_blender_stills(args)
        self.assertEqual(rc, 0)
        rec = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(rec["status"], "dry_run")
        self.assertEqual(rec["blender_stills"]["selected_backend"], "OPTIX")
        self.assertEqual(rec["blender_stills"]["frames"], [["hook_f0016", 16], ["quench_f0350", 350]])


if __name__ == "__main__":
    unittest.main()
