"""Behavioral checks for role installation without touching real Codex settings."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "sync_video_agents.py"
spec = importlib.util.spec_from_file_location("sync_video_agents", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class AgentSyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.home = self.root / "home"
        self.source.mkdir()
        self.home.mkdir()
        for name in sync.ROLE_NAMES:
            (self.source / f"{name}.toml").write_text(
                f'name = "{name}"\ndescription = "Purpose"\ndeveloper_instructions = "Do assigned work"\n',
                encoding="utf-8")

    def test_check_does_not_install_and_install_is_idempotent(self):
        (self.home / "config.toml").write_bytes(b"unrelated settings")
        planned = sync.plan_sync(self.source, self.home)
        self.assertFalse((self.home / "agents").exists())
        self.assertTrue(all(row["status"] == "missing" for row in planned))
        sync.install(planned)
        current = sync.plan_sync(self.source, self.home)
        self.assertTrue(all(row["status"] == "current" for row in current))
        before = [(Path(row["target"]).stat().st_mtime_ns) for row in current]
        sync.install(current)
        self.assertEqual(before, [Path(row["target"]).stat().st_mtime_ns for row in current])
        self.assertEqual((self.home / "config.toml").read_bytes(), b"unrelated settings")

    def test_update_requires_explicit_replacement_and_preserves_prior_version(self):
        sync.install(sync.plan_sync(self.source, self.home))
        target = self.home / "agents" / f"{sync.ROLE_NAMES[0]}.toml"
        original = target.read_bytes()
        (self.home / "agents" / "unrelated.toml").write_bytes(b"keep me")
        (self.source / target.name).write_bytes(original.replace(b"Purpose", b"Updated purpose"))
        plan = sync.plan_sync(self.source, self.home)
        with self.assertRaises(ValueError):
            sync.install(plan)
        self.assertEqual(target.read_bytes(), original)
        sync.install(plan, replace_existing=True)
        self.assertEqual(Path(plan[0]["backup"]).read_bytes(), original)
        self.assertIn(b"Updated purpose", target.read_bytes())
        self.assertEqual((self.home / "agents" / "unrelated.toml").read_bytes(), b"keep me")

    def test_malformed_source_prevents_all_writes(self):
        (self.source / f"{sync.ROLE_NAMES[-1]}.toml").write_text('name = "wrong"', encoding="utf-8")
        with self.assertRaises(ValueError):
            sync.plan_sync(self.source, self.home)
        self.assertFalse((self.home / "agents").exists())

    def test_destination_owned_by_another_role_is_not_overwritten(self):
        (self.home / "agents").mkdir()
        target = self.home / "agents" / f"{sync.ROLE_NAMES[0]}.toml"
        target.write_text('name = "another_role"', encoding="utf-8")
        with self.assertRaises(ValueError):
            sync.plan_sync(self.source, self.home)
        self.assertEqual(target.read_text(encoding="utf-8"), 'name = "another_role"')

    def test_changed_destination_aborts_before_writing_missing_roles(self):
        plan = sync.plan_sync(self.source, self.home)
        (self.home / "agents").mkdir()
        target = self.home / "agents" / f"{sync.ROLE_NAMES[-1]}.toml"
        target.write_bytes(b"a concurrent change")
        with self.assertRaises(ValueError):
            sync.install(plan)
        self.assertEqual(list((self.home / "agents").iterdir()), [target])

    def test_later_backup_conflict_does_not_partially_update_earlier_role(self):
        sync.install(sync.plan_sync(self.source, self.home))
        originals = {}
        for name in sync.ROLE_NAMES[:2]:
            target = self.home / "agents" / f"{name}.toml"
            originals[name] = target.read_bytes()
            (self.source / target.name).write_bytes(originals[name].replace(b"Purpose", b"Changed"))
        second = sync.ROLE_NAMES[1]
        backup_dir = self.home / "agents" / ".science-video-backups"
        backup_dir.mkdir()
        (backup_dir / f"{second}-{sync.sha(originals[second])}.bak").write_bytes(b"conflict")
        with self.assertRaises(ValueError):
            sync.install(sync.plan_sync(self.source, self.home), replace_existing=True)
        for name, content in originals.items():
            self.assertEqual((self.home / "agents" / f"{name}.toml").read_bytes(), content)

    def test_linked_backup_cannot_masquerade_as_a_saved_previous_version(self):
        sync.install(sync.plan_sync(self.source, self.home))
        name = sync.ROLE_NAMES[0]
        target = self.home / "agents" / f"{name}.toml"
        original = target.read_bytes()
        (self.source / target.name).write_bytes(original.replace(b"Purpose", b"Changed"))
        backup_dir = self.home / "agents" / ".science-video-backups"
        backup_dir.mkdir()
        backup = backup_dir / f"{name}-{sync.sha(original)}.bak"
        try:
            backup.symlink_to(target)
        except OSError:
            self.skipTest("Host does not allow creation of test symlinks")
        with self.assertRaises(ValueError):
            sync.install(sync.plan_sync(self.source, self.home), replace_existing=True)
        self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
