"""Discover the bundled sequence and review-context behavior tests."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'skills/science-video-production/scripts/tests/test_blender_batch.py'
spec = importlib.util.spec_from_file_location('bundled_blender_batch_tests', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def load_tests(loader, tests, pattern):
    return loader.loadTestsFromModule(module)
