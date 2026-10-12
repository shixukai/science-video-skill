"""Include bundled rendering-boundary regressions in standard discovery."""
import importlib.util
from pathlib import Path
p = Path(__file__).resolve().parents[1] / "skills/science-video-production/scripts/tests/test_render_evidence_checks.py"
spec = importlib.util.spec_from_file_location("bundled_render_evidence_tests", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
NumericChecks = module.NumericChecks
ViewingCopyChecks = module.ViewingCopyChecks
