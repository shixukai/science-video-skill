"""Offline setting-contract tests; fake Blender state is not visual quality evidence."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
SCRIPT_DIR = HERE if (HERE / "blender_batch.py").is_file() else HERE.parent
sys.path.insert(0, str(SCRIPT_DIR))
import blender_batch as batch


class ColorOwner:
    """Enum rejection, transform-dependent looks and numeric clamps mimic RNA."""
    def __init__(self, events, **values):
        object.__setattr__(self, "events", events)
        self.__dict__.update(values)

    def __setattr__(self, key, value):
        if key == "view_transform":
            if value not in ("AgX", "Standard"):
                raise TypeError("enum not found")
            self.__dict__["look"] = "None"
        if key == "look" and value not in ("None", "AgX - Medium High Contrast"):
            raise TypeError("enum not found")
        if key == "display_device" and value != "sRGB":
            raise TypeError("enum not found")
        self.events.append((key, value))
        if key == "gamma":
            value = min(5.0, max(0.0, value))
        if key == "exposure":
            value = min(32.0, max(-32.0, value))
        object.__setattr__(self, key, value)


def scene_fixture():
    events = []
    return SimpleNamespace(
        render=SimpleNamespace(image_settings=SimpleNamespace(), use_motion_blur=False,
                               use_persistent_data=False),
        view_settings=ColorOwner(events, view_transform="Standard", look="None", exposure=-0.35, gamma=1.1),
        display_settings=ColorOwner(events, display_device="sRGB"),
        cycles=SimpleNamespace(device="GPU", samples=8, use_denoising=False, denoiser="OPTIX",
                               denoising_use_gpu=True, use_adaptive_sampling=False, adaptive_threshold=0.01,
                               max_bounces=12, seed=17, diffuse_bounces=4, glossy_bounces=4,
                               transmission_bounces=12, volume_bounces=0, transparent_max_bounces=8,
                               adaptive_min_samples=0, sample_clamp_direct=0.0, sample_clamp_indirect=10.0,
                               caustics_reflective=True, caustics_refractive=True),
        events=events,
    )


def spec_fixture():
    return {"schema_version": 1, "job_id": "color-contract-v1", "purpose": "lookdev",
            "driver": "scene.py", "blender_executable": "existing-blender.exe", "inputs": [],
            "output_dir": "frames", "frames": [1],
            "render": {"engine": "CYCLES", "device": "CPU", "samples": 8,
                       "width": 8, "height": 6, "fps": 25}}


class ColorSettingsTests(unittest.TestCase):
    def setUp(self):
        self.spec = spec_fixture()
        self.scene = scene_fixture()
        self.bpy = SimpleNamespace()

    def test_explicit_supported_settings_apply_in_dependency_order_and_read_back(self):
        # Input order deliberately differs from the Blender dependency order.
        requested = {"gamma": 1.2, "look": "AgX - Medium High Contrast", "exposure": 0.75,
                     "view_transform": "AgX", "display_device": "sRGB"}
        self.spec["render"]["color_management"] = requested
        batch.validate_spec(self.spec)
        actual = batch.configure(self.scene, self.spec["render"], self.bpy)
        self.assertEqual([key for key, _ in self.scene.events],
                         ["display_device", "view_transform", "look", "exposure", "gamma"])
        self.assertEqual({key: actual[key] for key in requested}, requested)
        json.dumps(actual, allow_nan=False)

    def test_absent_color_block_inherits_authored_values_without_color_writes(self):
        actual = batch.configure(self.scene, self.spec["render"], self.bpy)
        self.assertEqual(self.scene.events, [])
        self.assertEqual({key: actual[key] for key in ("view_transform", "look", "exposure", "gamma", "display_device")},
                         {"view_transform": "Standard", "look": "None", "exposure": -0.35,
                          "gamma": 1.1, "display_device": "sRGB"})

    def test_partial_or_empty_block_only_applies_explicit_properties(self):
        for requested in ({}, {"exposure": 0.5}):
            with self.subTest(requested=requested):
                scene = scene_fixture()
                render = {**self.spec["render"], "color_management": requested}
                actual = batch.configure(scene, render, self.bpy)
                self.assertEqual(scene.events, list(requested.items()))
                self.assertEqual(actual["gamma"], 1.1)
                self.assertEqual(actual["view_transform"], "Standard")
                self.assertEqual(actual["exposure"], requested.get("exposure", -0.35))

    def test_all_existing_consumed_render_keys_remain_accepted(self):
        render = self.spec["render"]
        render.update(fps_base=1.001, format="OPEN_EXR", color_mode="RGB", threads=2,
                      persistent_data=False, denoise=False, denoiser="OPENIMAGEDENOISE", max_bounces=4,
                      noise_threshold=0.02, backend="OPTIX", device_name="Existing GPU", device_id="existing-id")
        batch.validate_spec(self.spec)
        actual = batch.configure(self.scene, render, self.bpy)
        self.assertEqual(actual["format"], "OPEN_EXR")
        self.assertEqual(actual["color_mode"], "RGB")
        self.assertEqual(actual["device"], "CPU")
        self.assertFalse(actual["cycles"]["use_denoising"])
        self.assertEqual(actual["cycles"]["max_bounces"], 4)

    def test_actual_diagnostics_read_available_values_and_omit_missing_version_fields(self):
        before = {key: getattr(self.scene.cycles, key) for key in
                  ("diffuse_bounces", "transmission_bounces", "sample_clamp_indirect", "adaptive_min_samples")}
        actual = batch.configure(self.scene, self.spec["render"], self.bpy)
        self.assertEqual({key: actual["cycles"][key] for key in before}, before)
        self.assertNotIn("denoising_quality", actual["cycles"])
        self.scene.cycles.denoising_quality = "HIGH"
        actual = batch.configure(self.scene, self.spec["render"], self.bpy)
        self.assertEqual(actual["cycles"]["denoising_quality"], "HIGH")
        self.assertEqual(actual["cycles"]["seed"], 17)

    def test_color_state_readback_is_available_for_other_supported_engines(self):
        for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
            with self.subTest(engine=engine):
                render = {**self.spec["render"], "engine": engine,
                          "color_management": {"exposure": 0.25}}
                actual = batch.configure(scene_fixture(), render, self.bpy)
                self.assertEqual(actual["exposure"], 0.25)
                self.assertIsNone(actual["cycles"])

    def test_unknown_render_keys_are_rejected_with_driver_and_supported_key_guidance(self):
        for key in ("exposure", "view_transform", "sampls", "quality", "lighting"):
            with self.subTest(key=key):
                self.spec["render"][key] = 1
                with self.assertRaises(ValueError) as caught:
                    batch.validate_spec(self.spec)
                message = str(caught.exception)
                for expected in ("render." + key, "Supported job render keys", "color_management", "driver", "baked blend"):
                    self.assertIn(expected, message)
                del self.spec["render"][key]

    def test_unknown_render_or_color_key_is_blocked_before_child_launch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scene.py").write_text("raise AssertionError('driver must not run')\n", encoding="utf-8")
            (root / "existing-blender.exe").write_bytes(b"not executable; must not launch")
            spec_path = root / "spec.json"
            spec_path.write_text(json.dumps(self.spec), encoding="utf-8")
            job = batch.prepare(spec_path, root / "valid-job.json")
            for addition in ({"exposure": 1}, {"color_management": {"exposuer": 1}}):
                with self.subTest(addition=addition):
                    invalid = copy.deepcopy(job)
                    invalid["spec"]["render"].update(addition)
                    # Valid signature isolates validation from tamper detection.
                    invalid["signature"] = batch.digest(invalid["spec"])
                    job_path = root / "invalid-job.json"
                    batch.write(job_path, invalid)
                    with mock.patch.object(batch.subprocess, "run") as child:
                        with self.assertRaisesRegex(ValueError, "Unsupported"):
                            batch.main(["run", str(job_path), "--blender", str(root / "existing-blender.exe")])
                        child.assert_not_called()
            self.assertFalse((root / "frames").exists())

    def test_invalid_container_string_numeric_and_gamma_values_reject_before_apply(self):
        invalid = [None, [], "AgX", 1, {"look": " "}, {"look": True}, {"view_transform": 3},
                   {"display_device": []}, {"exposure": True}, {"exposure": "1"},
                   {"exposure": float("nan")}, {"exposure": float("inf")},
                   {"exposure": -float("inf")}, {"exposure": 10 ** 1000},
                   {"gamma": False}, {"gamma": 0}, {"gamma": -1}, {"gamma": "1"},
                   {"gamma": float("nan")}, {"gamma": float("inf")}, {"gamma": 10 ** 1000},
                   {"contrast": "High"}]
        for color in invalid:
            with self.subTest(color=color):
                render = {**self.spec["render"], "color_management": color}
                with self.assertRaises(ValueError):
                    batch.validate_spec({**self.spec, "render": render})
                with self.assertRaises(ValueError):
                    batch.configure(self.scene, render, self.bpy)
                self.assertEqual(self.scene.events, [])
        for render in (None, [], "CYCLES"):
            with self.subTest(render=render):
                with self.assertRaisesRegex(ValueError, "render must be an object"):
                    batch.validate_spec({**self.spec, "render": render})

    def test_invalid_runtime_enum_and_clamped_numeric_request_fail_clearly(self):
        for color in ({"view_transform": "Unknown transform"}, {"look": "Unknown look"},
                      {"display_device": "Unknown display"}, {"gamma": 6}, {"exposure": 33}):
            with self.subTest(color=color):
                render = {**self.spec["render"], "color_management": color}
                batch.validate_render_settings(render)
                with self.assertRaisesRegex(ValueError, r"render\.color_management\..*Blender/OCIO"):
                    batch.configure(scene_fixture(), render, self.bpy)

    def test_existing_job_template_render_defaults_stay_valid_without_color_preset(self):
        template_path = Path(os.environ.get("BLENDER_JOB_TEMPLATE", str(SCRIPT_DIR.parent / "assets" / "blender-job-template.json")))
        template = batch.read(template_path)
        # Template intentionally leaves these two deployment-specific pins empty.
        template["blender_executable"] = "existing-blender.exe"
        template["render"]["device_name"] = "Existing GPU"
        self.assertEqual(batch.validate_spec(template), list(range(1, 101)))
        self.assertNotIn("color_management", template["render"])


if __name__ == "__main__":
    unittest.main()
