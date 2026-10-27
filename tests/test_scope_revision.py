"""Include the bundled task-scope regressions in repository discovery."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'skills/science-video-production/scripts/tests/test_scope_revision.py'
spec = importlib.util.spec_from_file_location('bundled_scope_revision_tests', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromModule(module)
