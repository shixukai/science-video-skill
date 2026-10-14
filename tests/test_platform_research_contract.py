"""Bundled blank platform-record contract checks, never live data validation."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('bundled_platform_research_tests',Path(__file__).resolve().parents[1]/'skills/science-video-production/scripts/tests/test_platform_research_contract.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
PlatformResearchContractTests=module.PlatformResearchContractTests
