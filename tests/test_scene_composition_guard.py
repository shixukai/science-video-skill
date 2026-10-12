"""Include bundled scene/object-result regressions in root unittest discovery."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'skills/science-video-production/scripts/tests/test_scene_composition_guard.py'
spec = importlib.util.spec_from_file_location('bundled_scene_composition_tests', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SceneCompositionTests = module.SceneCompositionTests
