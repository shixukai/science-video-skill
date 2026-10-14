"""Run bundled adult-topic evidence tests, never actual audience validation."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('bundled_topic_selection_tests',Path(__file__).resolve().parents[1]/'skills/science-video-production/scripts/tests/test_topic_selection_guard.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
TopicSelectionTests=module.TopicSelectionTests
