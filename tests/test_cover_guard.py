"""Expose bundled synthetic cover regressions to repository discovery."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "skills/science-video-production/scripts/tests/test_cover_guard.py"
spec = importlib.util.spec_from_file_location("bundled_cover_tests", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
CoverGuardTests = module.CoverGuardTests
