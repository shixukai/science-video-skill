"""Include bundled local-repair scope regressions in root unittest discovery."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'skills/science-video-production/scripts/tests/test_local_repair_scope.py'
spec = importlib.util.spec_from_file_location('bundled_local_repair_scope_tests', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
LocalRepairScopeTests = module.LocalRepairScopeTests
UnknownSpanDiagnosticsTests = module.UnknownSpanDiagnosticsTests
