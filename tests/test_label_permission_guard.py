"""Run the bundled label permission regressions in the repository test suite."""
import importlib.util
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'skills/science-video-production/scripts/tests/test_label_permission_guard.py'
spec=importlib.util.spec_from_file_location('bundled_label_permission_tests',p)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
LabelPermissionTests=module.LabelPermissionTests
consent_item=module.consent_item
