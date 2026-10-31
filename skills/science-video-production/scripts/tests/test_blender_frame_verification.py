"""Synthetic local validation tests; technical evidence is never visual approval."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest import mock
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import blender_batch as batch
import test_blender_batch as fixtures
from test_blender_batch import FakeRenderer, png


def tagged_png(path, tag=b"A"):
    png(path)
    raw = path.read_bytes(); kind = b"tEXt"; data = b"fixture\0" + tag
    chunk = struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    path.write_bytes(raw[:-12] + chunk + raw[-12:])


class VerificationTests(unittest.TestCase):
    setUp = fixtures.BatchTests.setUp
    prepare = fixtures.BatchTests.prepare

    def test_new_frames_decode_once_and_final_scan_rehashes_content(self):
        with mock.patch.object(batch, "check_image", wraps=batch.check_image) as decode:
            result = batch.execute(self.job, FakeRenderer())
        self.assertEqual(decode.call_count, 4)
        stats = result["frame_validation"]
        self.assertEqual((stats["content_hashes"], stats["decoded_frames"], stats["cached_decode_reuses"]), (8, 4, 4))
        self.assertGreater(stats["validation_seconds"], 0)
        self.assertGreater(stats["content_hash_seconds"], 0)
        self.assertGreater(stats["decode_seconds"], 0)
        record = batch.read(self.root / "frames/frame_000001.json")
        self.assertEqual(record["validation"]["sha256"], record["sha256"])
        self.assertEqual(record["validation_metrics"]["decoded_frames"], 1)
        self.assertNotIn("approval", record)

    def test_completed_resume_hashes_once_without_decoding_or_building(self):
        batch.execute(self.job, FakeRenderer()); renderer = FakeRenderer()
        with mock.patch.object(batch, "check_image", wraps=batch.check_image) as decode:
            result = batch.execute(self.job, renderer, resume=True)
        self.assertEqual((decode.call_count, renderer.builds), (0, 0))
        self.assertEqual(result["frame_validation"]["content_hashes"], 4)
        self.assertEqual(result["frame_validation"]["cached_decode_reuses"], 4)

    def test_same_size_content_with_restored_mtime_is_detected(self):
        class Tagged(FakeRenderer):
            def render(self, path):
                self.frames.append(self.frame); tagged_png(path)
        batch.execute(self.job, Tagged())
        image = self.root / "frames/frame_000002.png"
        before = image.stat(); tagged_png(image, b"B")
        self.assertEqual(image.stat().st_size, before.st_size)
        os.utime(image, ns=(before.st_atime_ns, before.st_mtime_ns))
        batch.check_image(image, self.spec["render"])
        renderer = FakeRenderer(); result = batch.execute(self.job, renderer, resume=True)
        self.assertEqual(renderer.frames, [2]); self.assertEqual(result["valid_frames"], 4)
        archived = list((self.root / "frames/invalid").rglob("frame_000002.png"))
        self.assertEqual(len(archived), 1)

    def test_validator_context_change_rechecks_all_decodes(self):
        batch.execute(self.job, FakeRenderer())
        with mock.patch.object(batch, "FRAME_VALIDATOR_VERSION", batch.FRAME_VALIDATOR_VERSION + 1):
            result = batch.execute(self.job, FakeRenderer(), resume=True)
        self.assertEqual(result["frame_validation"]["decoded_frames"], 4)
        self.assertEqual(result["rendered_frames"], 0)

    def test_current_executor_context_change_cannot_reuse_decode_evidence(self):
        batch.execute(self.job, FakeRenderer())
        original = batch.file_hash
        def changed(path):
            return "a" * 64 if Path(path).resolve() == Path(batch.__file__).resolve() else original(path)
        with mock.patch.object(batch, "file_hash", side_effect=changed):
            verifier = batch.FrameVerifier(self.job)
            self.assertTrue(verifier.valid_frame(1))
        self.assertEqual(verifier.metrics["decoded_frames"], 1)

    def test_changed_job_context_rechecks_decode_and_keeps_resume_lock(self):
        batch.execute(self.job, FakeRenderer())
        changed = copy.deepcopy(self.job); changed["spec"]["render"]["samples"] = 9
        changed["signature"] = batch.digest(changed["spec"])
        with self.assertRaises(ValueError): batch.execute(changed, FakeRenderer(), resume=True)
        receipt = self.root / "frames/frame_000001.json"
        record = batch.read(receipt); record["signature"] = changed["signature"]; batch.write(receipt, record)
        verifier = batch.FrameVerifier(changed)
        self.assertTrue(verifier.valid_frame(1)); self.assertEqual(verifier.metrics["decoded_frames"], 1)

    def test_legacy_receipts_fully_checked_before_separate_cache_upgrade(self):
        batch.execute(self.job, FakeRenderer())
        (self.root / "frames/frame-validation-cache.json").unlink()
        before = {}
        for receipt in (self.root / "frames").glob("frame_*.json"):
            record = batch.read(receipt); record.pop("validation"); record.pop("validation_metrics")
            batch.write(receipt, record); before[receipt] = receipt.read_bytes()
        history = {path: path.read_bytes() for path in (self.root / "frames/attempts").glob("*.json")}
        result = batch.execute(self.job, FakeRenderer(), resume=True)
        self.assertEqual(result["frame_validation"]["decoded_frames"], 4)
        self.assertTrue(all(path.read_bytes() == raw for path, raw in before.items()))
        self.assertTrue(all(path.read_bytes() == raw for path, raw in history.items()))
        result = batch.execute(self.job, FakeRenderer(), resume=True)
        self.assertEqual(result["frame_validation"]["decoded_frames"], 0)

    def test_malformed_receipts_are_invalid_and_do_not_crash_resume(self):
        batch.execute(self.job, FakeRenderer())
        variants = [[], {"signature": self.job["signature"], "frame": 2}, None, "broken"]
        for frame, record in enumerate(variants, 1):
            batch.write(self.root / f"frames/frame_{frame:06d}.json", record)
        renderer = FakeRenderer(); result = batch.execute(self.job, renderer, resume=True)
        self.assertEqual(renderer.frames, [1, 2, 3, 4]); self.assertEqual(result["valid_frames"], 4)

    def test_missing_receipt_does_not_inherit_valid_cache(self):
        batch.execute(self.job, FakeRenderer())
        (self.root / "frames/frame_000003.json").unlink()
        renderer = FakeRenderer(); batch.execute(self.job, renderer, resume=True)
        self.assertEqual(renderer.frames, [3])

    def test_malformed_validation_evidence_is_fully_decoded(self):
        batch.execute(self.job, FakeRenderer())
        (self.root / "frames/frame-validation-cache.json").write_text("[]", encoding="utf-8")
        for receipt in (self.root / "frames").glob("frame_*.json"):
            record = batch.read(receipt); record["validation"] = []
            batch.write(receipt, record)
        result = batch.execute(self.job, FakeRenderer(), resume=True)
        self.assertEqual(result["frame_validation"]["decoded_frames"], 4)

    def test_corrupt_png_with_matching_receipt_hash_still_needs_decode_evidence(self):
        batch.execute(self.job, FakeRenderer())
        (self.root / "frames/frame-validation-cache.json").unlink()
        image = self.root / "frames/frame_000002.png"; image.write_bytes(image.read_bytes()[:24])
        receipt = self.root / "frames/frame_000002.json"; record = batch.read(receipt)
        record["sha256"] = batch.file_hash(image); record.pop("validation"); batch.write(receipt, record)
        renderer = FakeRenderer(); result = batch.execute(self.job, renderer, resume=True)
        self.assertEqual(renderer.frames, [2]); self.assertEqual(result["valid_frames"], 4)

    def test_subset_noop_hashes_unselected_frames_for_real_completion_count(self):
        batch.execute(self.job, FakeRenderer())
        (self.root / "frames/frame_000004.png").write_bytes(b"corrupt")
        renderer = FakeRenderer(); result = batch.execute(self.job, renderer, resume=True, selected="1")
        self.assertEqual(renderer.frames, []); self.assertEqual(result["valid_frames"], 3)
        self.assertEqual(result["status"], "partial_unreviewed")
        self.assertEqual(result["frame_validation"]["content_hashes"], 4)

    def test_renderer_mutation_of_earlier_frame_is_detected_at_completion(self):
        class Mutating(FakeRenderer):
            def render(inner, path):
                super(Mutating, inner).render(path)
                if inner.frame == 4:
                    (self.root / "frames/frame_000001.png").write_bytes(b"corrupt")
        result = batch.execute(self.job, Mutating())
        self.assertEqual(result["valid_frames"], 3)
        self.assertEqual(result["status"], "partial_unreviewed")
        renderer = FakeRenderer(); result = batch.execute(self.job, renderer, resume=True)
        self.assertEqual(renderer.frames, [1]); self.assertEqual(result["valid_frames"], 4)

    def test_renderer_mutation_of_unselected_frame_is_detected(self):
        batch.execute(self.job, FakeRenderer(), selected="1")
        class Mutating(FakeRenderer):
            def render(inner, path):
                super(Mutating, inner).render(path)
                (self.root / "frames/frame_000001.png").write_bytes(b"corrupt")
        result = batch.execute(self.job, Mutating(), resume=True, selected="2")
        self.assertEqual(result["valid_frames"], 1); self.assertEqual(result["status"], "partial_unreviewed")

    def test_interruption_keeps_evidence_and_original_failure_history(self):
        with self.assertRaises(RuntimeError): batch.execute(self.job, FakeRenderer(fail=3))
        history = {path: path.read_bytes() for path in (self.root / "frames/attempts").glob("*.json")}
        # Simulate losing only the derived cache during abrupt shutdown.
        (self.root / "frames/frame-validation-cache.json").unlink()
        result = batch.execute(self.job, FakeRenderer(), resume=True)
        self.assertEqual(result["reused_frames"], 2)
        self.assertEqual(result["frame_validation"]["decoded_frames"], 2)
        self.assertTrue(all(path.read_bytes() == raw for path, raw in history.items()))

    def test_initial_resume_scan_time_is_included_in_batch_seconds(self):
        batch.execute(self.job, FakeRenderer())
        clock = [100.0]; original = batch.FrameVerifier.valid_frame
        def delayed(verifier, frame):
            clock[0] += 7.0
            return original(verifier, frame)
        with mock.patch.object(batch.time, "monotonic", side_effect=lambda: clock[0]), \
                mock.patch.object(batch.FrameVerifier, "valid_frame", delayed):
            result = batch.execute(self.job, FakeRenderer(), resume=True)
        self.assertEqual(result["initial_scan_seconds"], 28.0)
        self.assertEqual(result["batch_seconds"], 28.0)

    def test_cache_save_failure_preserves_finished_outcome_and_original_error(self):
        class CacheCollision(FakeRenderer):
            def build(inner, spec):
                super(CacheCollision, inner).build(spec)
                (Path(spec["output_dir"]) / "frame-validation-cache.json").mkdir()
        with self.assertRaisesRegex(RuntimeError, "synthetic interrupted frame"):
            batch.execute(self.job, CacheCollision(fail=3))
        failed = batch.read(self.root / "frames/state.json")
        self.assertEqual(failed["status"], "failed")
        self.assertIn("finished_at", failed); self.assertIn("frame_validation_cache_error", failed)
        self.assertEqual(failed["error"], "synthetic interrupted frame")
        history = {path: path.read_bytes() for path in (self.root / "frames/attempts").glob("*.json")}
        result = batch.execute(self.job, FakeRenderer(), resume=True)
        self.assertEqual(result["status"], "complete_unreviewed")
        self.assertIn("finished_at", result); self.assertIn("frame_validation_cache_error", result)
        self.assertEqual(batch.read(self.root / "frames/state.json")["status"], "complete_unreviewed")
        self.assertTrue(all(path.read_bytes() == raw for path, raw in history.items()))

    def test_fake_exr_requires_real_decoder_and_rejects_bad_pixels(self):
        path = self.root / "fake.exr"; path.write_bytes(b"\x76\x2f\x31\x01" + b"\0" * 80)
        render = {**self.spec["render"], "format": "OPEN_EXR"}
        with mock.patch.dict(sys.modules, {"bpy": None}):
            with self.assertRaisesRegex(ValueError, "actual Blender worker decoder"):
                batch.check_image(path, render)
        removed = []
        image = SimpleNamespace(size=(8, 6), has_data=True, pixels=[0.0], channels=4)
        bpy = SimpleNamespace(data=SimpleNamespace(images=SimpleNamespace(
            load=lambda *args, **kwargs: image, remove=removed.append)))
        with mock.patch.dict(sys.modules, {"bpy": bpy}):
            with self.assertRaisesRegex(ValueError, "pixels cannot be decoded"):
                batch.check_image(path, render)
        self.assertEqual(removed, [image])

    def test_exr_cached_evidence_cannot_bypass_missing_or_changed_decoder(self):
        self.spec.update(frames="1", output_dir="frames-exr")
        self.spec["render"]["format"] = "OPEN_EXR"; job = self.prepare("exr-job.json")
        class ExrRenderer(FakeRenderer):
            def render(self, path): path.write_bytes(b"\x76\x2f\x31\x01" + b"\0" * 80)
        image = SimpleNamespace(size=(8, 6), has_data=True, pixels=[0.0] * (8 * 6 * 4), channels=4)
        bpy = SimpleNamespace(app=SimpleNamespace(version_string="synthetic-1", build_hash=b"fixture"),
                              data=SimpleNamespace(images=SimpleNamespace(
                                  load=lambda *args, **kwargs: image, remove=lambda image: None)))
        with mock.patch.dict(sys.modules, {"bpy": bpy}):
            batch.execute(job, ExrRenderer())
            verifier = batch.FrameVerifier(job)
            self.assertTrue(verifier.valid_frame(1)); self.assertEqual(verifier.metrics["decoded_frames"], 0)
            bpy.app.version_string = "synthetic-2"
            verifier = batch.FrameVerifier(job)
            self.assertTrue(verifier.valid_frame(1)); self.assertEqual(verifier.metrics["decoded_frames"], 1)
        with mock.patch.dict(sys.modules, {"bpy": None}):
            self.assertFalse(batch.valid_frame(job, 1))

    def test_exr_mutation_during_path_decode_cannot_get_receipt(self):
        self.spec.update(frames="1", output_dir="frames-exr")
        self.spec["render"]["format"] = "OPEN_EXR"; job = self.prepare("exr-job.json")
        class ExrRenderer(FakeRenderer):
            def render(self, path): path.write_bytes(b"\x76\x2f\x31\x01" + b"\0" * 80)
        image = SimpleNamespace(size=(8, 6), has_data=True, pixels=[0.0] * (8 * 6 * 4), channels=4)
        def load(path, **kwargs):
            Path(path).write_bytes(b"\x76\x2f\x31\x01" + b"X" * 80)
            return image
        bpy = SimpleNamespace(data=SimpleNamespace(images=SimpleNamespace(load=load, remove=lambda image: None)))
        with mock.patch.dict(sys.modules, {"bpy": bpy}):
            with self.assertRaisesRegex(ValueError, "EXR changed during verification"):
                batch.execute(job, ExrRenderer())
        self.assertFalse((self.root / "frames-exr/frame_000001.json").exists())


if __name__ == "__main__":
    unittest.main()
