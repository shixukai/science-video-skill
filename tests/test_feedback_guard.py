"""Run the bundled feedback contract regressions in the repository test suite."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'skills/science-video-production/scripts/tests/test_feedback_guard.py'
spec = importlib.util.spec_from_file_location('bundled_feedback_contract_tests', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
FeedbackContractTests = module.FeedbackContractTests
