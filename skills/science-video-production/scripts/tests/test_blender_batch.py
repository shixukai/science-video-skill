"""Offline behavior tests; synthetic images are not production quality evidence."""
import copy
import json
import os
import py_compile
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import blender_batch as batch
import review_delta
from stage_checks import context_sha256


def png(path, width=8, height=6):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
                     chunk(b"IDAT", zlib.compress((b"\0" + b"\x44\x88\xcc" * width) * height)) + chunk(b"IEND", b""))


class FakeRenderer:
    def __init__(self, fail=None, change=None):
        self.fail = fail; self.change = change; self.builds = 0; self.frames = []

    def build(self, spec):
        self.builds += 1

    def set_frame(self, frame, spec):
        self.frame = frame
        return {"anchor": [0.25, 0.5]}, {"engine": "synthetic_fixture"}

    def render(self, path):
        self.frames.append(self.frame); png(path)
        if self.change:
            self.change.write_text("changed", encoding="utf-8")
        if self.frame == self.fail:
            raise RuntimeError("synthetic interrupted frame")


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "scene.py").write_text("# synthetic declared source\n", encoding="utf-8")
        (self.root / "material.txt").write_text("original", encoding="utf-8")
        (self.root / "blender-fixture.exe").write_bytes(b"synthetic non-executable fixture")
        self.spec = {"schema_version": 1, "job_id": "fixture-v1", "purpose": "motion_preview",
                     "driver": "scene.py", "blender_executable": "blender-fixture.exe",
                     "inputs": ["material.txt"], "output_dir": "frames",
                     "frames": "1:4", "render": {"engine": "CYCLES", "device": "CPU", "samples": 2,
                                                  "width": 8, "height": 6, "fps": 25}}
        self.job = self.prepare()

    def prepare(self, name="job.json"):
        (self.root / "spec.json").write_text(json.dumps(self.spec), encoding="utf-8")
        return batch.prepare(self.root / "spec.json", self.root / name)

    def test_build_once_and_every_native_frame(self):
        renderer = FakeRenderer(); result = batch.execute(self.job, renderer)
        self.assertEqual(renderer.builds, 1); self.assertEqual(renderer.frames, [1, 2, 3, 4])
        self.assertEqual(result["status"], "complete_unreviewed")
        self.assertEqual(result["valid_frames"], 4)
        self.assertNotIn("approval", result)

    def test_interruption_resumes_missing_frames_and_preserves_partial_output(self):
        with self.assertRaises(RuntimeError):
            batch.execute(self.job, FakeRenderer(fail=3))
        first = self.root / "frames/frame_000001.png"; before = first.stat().st_mtime_ns
        renderer = FakeRenderer(); result = batch.execute(self.job, renderer, resume=True)
        self.assertEqual(renderer.frames, [3, 4]); self.assertEqual(result["reused_frames"], 2)
        self.assertEqual(first.stat().st_mtime_ns, before)
        self.assertEqual(len(list((self.root / "frames/attempts").glob("*.json"))), 2)
        self.assertTrue(list((self.root / "frames/invalid").rglob("frame_000003.png")))

    def test_completed_resume_does_not_build_or_render(self):
        batch.execute(self.job, FakeRenderer()); renderer = FakeRenderer()
        result = batch.execute(self.job, renderer, resume=True)
        self.assertEqual(renderer.builds, 0); self.assertEqual(renderer.frames, [])
        self.assertEqual(result["reused_frames"], 4)

    def test_corrupt_frame_is_preserved_and_only_it_is_replaced(self):
        batch.execute(self.job, FakeRenderer())
        (self.root / "frames/frame_000002.png").write_bytes(b"corrupt")
        renderer = FakeRenderer(); batch.execute(self.job, renderer, resume=True)
        self.assertEqual(renderer.frames, [2])
        self.assertTrue(list((self.root / "frames/invalid").rglob("frame_000002.png")))

    def test_header_only_or_bad_crc_cannot_be_completed_or_reused(self):
        path = self.root / 'truncated.png'; png(path)
        good = path.read_bytes()
        for bad in (good[:24], good[:-12], good[:-13] + bytes([good[-13] ^ 1]) + good[-12:]):
            path.write_bytes(bad)
            with self.assertRaises(ValueError): batch.check_image(path, self.spec['render'])
        path.write_bytes(b'\x76\x2f\x31\x01' + b'\0' * 20)
        with self.assertRaises(ValueError): batch.check_image(path, {**self.spec['render'], 'format':'OPEN_EXR'})

    def test_incomplete_renderer_output_leaves_no_frame_receipt(self):
        class Incomplete(FakeRenderer):
            def render(self, path):
                png(path); path.write_bytes(path.read_bytes()[:24])
        with self.assertRaises(ValueError): batch.execute(self.job, Incomplete())
        self.assertFalse((self.root / 'frames/frame_000001.json').exists())
        self.assertEqual(batch.read(self.root / 'frames/state.json')['status'], 'failed')

    def test_disjoint_frame_patch_never_fills_gap(self):
        renderer = FakeRenderer(); result = batch.execute(self.job, renderer, selected="1,3")
        self.assertEqual(renderer.frames, [1, 3]); self.assertEqual(result["status"], "partial_unreviewed")
        renderer = FakeRenderer(); batch.execute(self.job, renderer, resume=True)
        self.assertEqual(renderer.frames, [2, 4])

    def test_lock_prevents_second_worker(self):
        with batch.job_lock(self.root / "frames"):
            with self.assertRaises(RuntimeError):
                batch.execute(self.job, FakeRenderer())

    def test_existing_output_requires_explicit_resume(self):
        batch.execute(self.job, FakeRenderer())
        with self.assertRaises(ValueError):
            batch.execute(self.job, FakeRenderer())

    def test_unowned_output_never_overwritten(self):
        output = self.root / "frames"; output.mkdir(); note = output / "my-file.txt"; note.write_text("keep")
        with self.assertRaises(ValueError): batch.execute(self.job, FakeRenderer())
        self.assertEqual(note.read_text(), "keep")

    def test_changed_input_rejected_before_render(self):
        (self.root / "material.txt").write_text("changed")
        renderer = FakeRenderer()
        with self.assertRaises(ValueError): batch.execute(self.job, renderer)
        self.assertEqual(renderer.builds, 0)

    def test_changed_blender_binary_cannot_mix_versions_on_resume(self):
        batch.execute(self.job, FakeRenderer())
        (self.root / "blender-fixture.exe").write_bytes(b"another executable")
        with self.assertRaises(ValueError): batch.execute(self.job, FakeRenderer(), resume=True)

    def test_source_change_during_render_taints_attempt_and_blocks_resume(self):
        with self.assertRaises(ValueError):
            batch.execute(self.job, FakeRenderer(change=self.root / "material.txt"))
        self.assertEqual(batch.read(self.root / "frames/state.json")["status"], "inputs_changed")
        (self.root / "material.txt").write_text("original")
        with self.assertRaises(ValueError): batch.execute(self.job, FakeRenderer(), resume=True)

    def test_modified_job_is_not_a_new_attempt(self):
        changed = copy.deepcopy(self.job); changed["spec"]["render"]["samples"] = 10
        with self.assertRaises(ValueError): batch.execute(changed, FakeRenderer())

    def test_new_signature_cannot_resume_old_output(self):
        batch.execute(self.job, FakeRenderer())
        self.spec["render"]["samples"] = 9; changed = self.prepare("job2.json")
        with self.assertRaises(ValueError): batch.execute(changed, FakeRenderer(), resume=True)

    def test_sparse_motion_preview_rejected_but_lookdev_allowed(self):
        self.spec["frames"] = "1,4"
        with self.assertRaises(ValueError): self.prepare("sparse.json")
        self.spec["purpose"] = "lookdev"; self.assertEqual(self.prepare("still.json")["spec"]["frames"], [1, 4])

    def test_frame_selection_cannot_expand_job(self):
        with self.assertRaises(ValueError): batch.execute(self.job, FakeRenderer(), selected="1:5")
        with self.assertRaises(ValueError): batch.parse_frames("1:3,2")

    def test_missing_gpu_identity_cannot_fallback(self):
        self.spec["render"]["device"] = "GPU"
        with self.assertRaises(ValueError): self.prepare("gpu.json")

    def test_cpu_only_job_rejects_gpu_only_denoiser(self):
        self.spec['render'].update(denoise=True, denoiser='OPTIX')
        with self.assertRaises(ValueError): self.prepare('invalid-denoiser.json')

    def test_existing_resource_check_blocks_and_records_reason(self):
        check = self.root / "resource.py"
        check.write_text("def check(spec):\n return {'ok': False, 'reason': 'synthetic task ownership conflict'}\n")
        self.spec["resource_check"] = str(check); job = self.prepare("resource-job.json")
        renderer = FakeRenderer()
        with self.assertRaises(RuntimeError): batch.execute(job, renderer)
        self.assertEqual(renderer.builds, 0)
        self.assertIn("ownership", batch.read(self.root / "frames/state.json")["resource_check"]["reason"])

    def test_high_utilization_telemetry_is_not_its_own_gate(self):
        check = self.root / "resource.py"
        check.write_text("def check(spec):\n return {'ok': True, 'gpu_utilization': 100}\n")
        self.spec["resource_check"] = str(check); job = self.prepare("telemetry-job.json")
        self.assertEqual(batch.execute(job, FakeRenderer())["status"], "complete_unreviewed")


    def test_entry_module_uses_current_source_despite_stale_bytecode(self):
        source = self.root / "scene.py"
        source.write_text("VALUE = 11\n", encoding="utf-8")
        os.utime(source, (1700000000, 1700000000))
        py_compile.compile(str(source), doraise=True)
        source.write_text("VALUE = 22\n", encoding="utf-8")
        os.utime(source, (1700000000, 1700000000))
        self.assertEqual(batch.load_module(source, "fixture_entry").VALUE, 22)
        sys.modules.pop("fixture_entry", None)

    def test_declared_helper_uses_source_and_restores_host_import_state(self):
        source = self.root / "fixture_helper.py"
        source.write_text("VALUE = 11\n", encoding="utf-8")
        os.utime(source, (1700000000, 1700000000))
        py_compile.compile(str(source), doraise=True)
        cached = batch.load_module(source, "fixture_helper")
        source.write_text("VALUE = 22\n", encoding="utf-8")
        os.utime(source, (1700000000, 1700000000))
        (self.root / "scene.py").write_text("import fixture_helper\nVALUE = fixture_helper.VALUE\n", encoding="utf-8")
        self.spec["inputs"].append(str(source)); job = self.prepare("source-job.json")
        original_path = list(sys.path)
        with batch.declared_source_imports(job["spec"]):
            module = batch.load_module(self.root / "scene.py", "fixture_driver")
            self.assertEqual(module.VALUE, 22)
        self.assertIs(sys.modules["fixture_helper"], cached)
        self.assertEqual(sys.path, original_path)
        self.assertNotIn("fixture_driver", sys.modules)
        sys.modules.pop("fixture_helper", None)

    def test_declared_package_relative_import_uses_current_source(self):
        package = self.root / "fixture_package"; package.mkdir()
        entry = package / "__init__.py"; entry.write_text("from .values import VALUE\n", encoding="utf-8")
        helper = package / "values.py"; helper.write_text("VALUE = 11\n", encoding="utf-8")
        os.utime(helper, (1700000000, 1700000000)); py_compile.compile(str(helper), doraise=True)
        helper.write_text("VALUE = 22\n", encoding="utf-8"); os.utime(helper, (1700000000, 1700000000))
        (self.root / "scene.py").write_text("from fixture_package import VALUE\n", encoding="utf-8")
        self.spec["inputs"].extend([str(entry), str(helper)]); job = self.prepare("package-job.json")
        with batch.declared_source_imports(job["spec"]):
            self.assertEqual(batch.load_module(self.root / "scene.py", "fixture_driver").VALUE, 22)
        self.assertNotIn("fixture_package", sys.modules)

    def test_source_driver_supports_dataclass_annotations(self):
        source = self.root / "scene.py"
        source.write_text("from __future__ import annotations\nfrom dataclasses import dataclass\n@dataclass\nclass Params:\n value: int = 22\n", encoding="utf-8")
        job = self.prepare("dataclass-job.json")
        with batch.declared_source_imports(job["spec"]):
            self.assertEqual(batch.load_module(source, "fixture_driver").Params().value, 22)

    def test_resource_hook_uses_current_declared_helper(self):
        helper = self.root / "fixture_resource_helper.py"
        helper.write_text("ALLOW = True \n", encoding="utf-8")
        os.utime(helper, (1700000000, 1700000000)); py_compile.compile(str(helper), doraise=True)
        helper.write_text("ALLOW = False\n", encoding="utf-8"); os.utime(helper, (1700000000, 1700000000))
        hook = self.root / "resource.py"
        hook.write_text("from fixture_resource_helper import ALLOW\ndef check(spec):\n return {'ok': ALLOW, 'reason': 'current project ownership'}\n", encoding="utf-8")
        self.spec["inputs"].append(str(helper)); self.spec["resource_check"] = str(hook)
        job = self.prepare("resource-source-job.json"); renderer = FakeRenderer()
        with self.assertRaises(RuntimeError): batch.execute(job, renderer)
        self.assertEqual(renderer.builds, 0)
        self.assertFalse(batch.read(self.root / "frames/state.json")["resource_check"]["ok"])


    def test_udim_tiles_are_each_required_and_tile_names_are_resolved(self):
        image = SimpleNamespace(filepath="surface.<UDIM>.png", source="TILED", packed_file=None,
                                library=None, tiles=[SimpleNamespace(number=1001), SimpleNamespace(number=1012)])
        def abspath(name, library=None): return str(self.root / name)
        paths = batch.image_file_paths(image, abspath)
        self.assertEqual([path.name for path in paths], ["surface.1001.png", "surface.1012.png"])
        for path in paths: png(path)
        self.spec["inputs"].append(str(paths[0])); job = self.prepare("tiles-incomplete.json")
        batch.check_external_path(paths[0], job["spec"])
        with self.assertRaises(ValueError): batch.check_external_path(paths[1], job["spec"])
        self.spec["inputs"].append(str(paths[1])); job = self.prepare("tiles-complete.json")
        for path in paths: batch.check_external_path(path, job["spec"])
        image.filepath = "surface.<UVTILE>.png"
        self.assertEqual([path.name for path in batch.image_file_paths(image, abspath)],
                         ["surface.u1_v1.png", "surface.u2_v2.png"])

    def test_dependency_loaded_after_build_must_also_be_declared(self):
        later = self.root / "later.png"; png(later)
        with self.assertRaises(ValueError): batch.check_external_path(later, self.job["spec"])
        self.spec["inputs"].append(str(later)); job = self.prepare("later-dependency.json")
        batch.check_external_path(later, job["spec"])


class ReviewDeltaTests(unittest.TestCase):
    def setUp(self):
        self.data = {"presentation_text": {"channels": {"frame": {"status": "planned", "note": "Inventory note"}},
            "items": [{"id": "label", "surface": "frame", "text": "Inlet", "purposes": ["mechanism"]}],
            "required_notices": []}, "qa": {"gates": {"G1": {"status": "not_reviewed"}}}}

    def test_coverage_normalization_keeps_semantic_g1_and_never_marks_passed(self):
        normalized = review_delta.normalize_channels(self.data)
        self.assertEqual(normalized["presentation_text"]["channels"]["frame"]["status"], "present")
        # Initially missing surfaces are a real inventory defect. Compare complete keys.
        before = copy.deepcopy(normalized); before["presentation_text"]["channels"]["frame"]["status"] = "planned"
        self.assertEqual(context_sha256(before, "G1"), context_sha256(normalized, "G1"))
        self.assertNotEqual(context_sha256(before, "G2"), context_sha256(normalized, "G2"))
        self.assertEqual(normalized["qa"], self.data["qa"])
        self.assertEqual(self.data["presentation_text"]["channels"]["frame"]["status"], "planned")

    def test_meaning_purpose_surface_and_notices_still_invalidate_g1(self):
        for field, value in (("text", "Outlet"), ("surface", "caption"), ("purposes", ["scientific_condition"])):
            changed = copy.deepcopy(self.data); changed["presentation_text"]["items"][0][field] = value
            self.assertNotEqual(context_sha256(self.data, "G1"), context_sha256(changed, "G1"))
        changed = copy.deepcopy(self.data); changed["presentation_text"]["required_notices"].append({"text": "Illustrative scale"})
        self.assertNotEqual(context_sha256(self.data, "G1"), context_sha256(changed, "G1"))

    def test_compare_does_not_change_or_approve_records(self):
        copy_before = copy.deepcopy(self.data)
        result = review_delta.compare(self.data, self.data)
        self.assertTrue(all(not item["changed"] for item in result["stages"].values()))
        self.assertEqual(self.data, copy_before); self.assertNotIn("passed", result)

    def test_bad_surface_not_normalized_into_valid_inventory(self):
        self.data["presentation_text"]["items"][0]["surface"] = "unknown"
        with self.assertRaises(ValueError): review_delta.normalize_channels(self.data)


if __name__ == "__main__":
    unittest.main()
