"""Global installation behavior with isolated temporary files; no live production."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/science-video-production/scripts'
spec = importlib.util.spec_from_file_location('global_skill', SCRIPTS / 'global_skill.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GlobalSkillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / 'codex'
        self.installed = self.home / 'skills/science-video-production-test'
        self.skill(self.installed)

    def skill(self, path):
        path.mkdir(parents=True)
        (path / 'SKILL.md').write_text('---\nname: science-video-production\ndescription: test\n---\n', encoding='utf-8')

    def test_single_global_is_resolved(self):
        self.assertEqual(module.require_global_runtime(self.installed, self.home), self.installed.resolve())

    def test_same_bytes_in_project_are_not_global(self):
        other = self.root / 'project/rules/skill'
        self.skill(other)
        with self.assertRaises(ValueError):
            module.require_global_runtime(other, self.home)

    def test_multiple_installed_versions_require_reconciliation(self):
        self.skill(self.home / 'skills/science-video-production-second')
        with self.assertRaises(ValueError):
            module.global_installation(self.home)

    def test_missing_installation_does_not_fall_back_to_project(self):
        with self.assertRaises(ValueError):
            module.global_installation(self.root / 'absent')

    def test_unrelated_skill_is_not_a_duplicate(self):
        other = self.home / 'skills/another'
        other.mkdir()
        (other / 'SKILL.md').write_text('---\nname: another\n---\nscience-video-production', encoding='utf-8')
        self.assertEqual(module.global_installation(self.home), self.installed.resolve())

    def test_name_in_body_does_not_register_installation(self):
        p = self.root / 'body.md'
        p.write_text('---\nname: other\n---\nname: science-video-production\n', encoding='utf-8')
        self.assertFalse(module.is_science_skill(p))

    def test_audit_finds_hidden_project_copy(self):
        project = self.root / 'project'
        local = project / '.agents/skills/science-video-production'
        self.skill(local)
        result = module.audit_projects([project], self.installed)
        self.assertEqual(result['independent_project_copies'], [str(local)])
        self.assertFalse(result['scan_errors'])

    def test_missing_scan_root_is_not_reported_as_clean(self):
        result = module.audit_projects([self.root / 'missing'], self.installed)
        self.assertTrue(result['scan_errors'])

    def test_source_exemption_never_authorizes_runtime(self):
        source = self.root / 'maintenance/source'
        self.skill(source)
        self.assertFalse(module.audit_projects([source], self.installed, [source])['independent_project_copies'])
        with self.assertRaises(ValueError):
            module.require_global_runtime(source, self.home)

    def test_repository_cli_rejected_before_lock_creation(self):
        lock = self.root / 'not-created.json'
        env = dict(os.environ, CODEX_HOME=str(self.home), PYTHONUTF8='1')
        result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'render_gate.py'), 'lock', str(lock)],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Project/repository Skill execution is disabled', result.stderr)
        self.assertFalse(lock.exists())


if __name__ == '__main__':
    unittest.main()
