"""Include bundled observation-scope regressions in standard discovery."""
import importlib.util
from pathlib import Path
p = Path(__file__).resolve().parents[1] / "skills/science-video-production/scripts/tests/test_evidence_scope.py"
spec = importlib.util.spec_from_file_location("bundled_evidence_scope_tests", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
EvidenceScopeTests = module.EvidenceScopeTests
