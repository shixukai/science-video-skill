"""Discover the bundled voice_master_binding tests."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'skills/science-video-production/scripts/tests/test_voice_master_binding.py'
spec = importlib.util.spec_from_file_location('bundled_voice_master_binding_tests', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def load_tests(loader, tests, pattern):
    return loader.loadTestsFromModule(module)
