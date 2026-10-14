"""Run bundled connector evidence regressions, not actual visual acceptance."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('bundled_connection_tests',Path(__file__).resolve().parents[1]/'skills/science-video-production/scripts/tests/test_connection_guard.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
ConnectionGuardTests=module.ConnectionGuardTests
