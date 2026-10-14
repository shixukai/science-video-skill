"""Run the installed Skill's actual rendering-entry regressions."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('bundled_render_gate_tests',Path(__file__).resolve().parents[1]/'skills/science-video-production/scripts/tests/test_render_gate.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
RenderGateTests=module.RenderGateTests
