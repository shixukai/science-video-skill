"""Discover the bundled synthetic opening-contract regression suite."""
import importlib.util
from pathlib import Path
path = Path(__file__).resolve().parents[1] / 'skills/science-video-production/scripts/tests/test_opening_alignment_guard.py'
spec = importlib.util.spec_from_file_location('bundled_opening_alignment_tests', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
OpeningAlignmentTests = module.OpeningAlignmentTests
