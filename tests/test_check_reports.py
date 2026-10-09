"""CLI receipts preserve the actual input and never grant or rewrite approval."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "skills/science-video-production/scripts/check_episode.py"
spec = importlib.util.spec_from_file_location("receipt_checks", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class CheckReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="science-receipts-")
        self.root = Path(self.temp.name)
        for name in ("episode.json", "topic-anchor.json"):
            shutil.copyfile(PROJECT / "examples/blue-sky" / name, self.root / name)
        self.packet = self.root / "episode.json"
        self.report = self.root / "plan-check.json"

    def tearDown(self):
        self.temp.cleanup()

    def run_check(self, report=True):
        command = [sys.executable, str(SCRIPT), str(self.packet), "--stage", "plan"]
        if report:
            command.extend(["--report", str(self.report)])
        return subprocess.run(command, capture_output=True, text=True, timeout=30)

    def receipt(self):
        return json.loads(self.report.read_text())

    def test_passing_receipt_binds_packet_and_rules_without_changing_qa(self):
        before = self.packet.read_bytes()
        run = self.run_check()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        report = self.receipt()
        self.assertEqual(report["result"], "local_checks_pass")
        self.assertEqual(report["stage"], "plan")
        self.assertEqual(report["episode"]["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(report["validation_resources"]["scripts/check_episode.py"],
                         hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
        self.assertEqual(report["errors"], [])
        self.assertTrue(report["notes"])
        self.assertEqual(self.packet.read_bytes(), before)

    def test_blocked_receipt_preserves_actionable_errors(self):
        data = json.loads(self.packet.read_text())
        data["claims"][0]["source_ids"] = ["missing-source"]
        self.packet.write_text(json.dumps(data))
        run = self.run_check()
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        report = self.receipt()
        self.assertEqual(report["result"], "blocked")
        self.assertTrue(any("source_ids" in error for error in report["errors"]))

    def test_malformed_json_also_has_a_failed_receipt(self):
        self.packet.write_text('{"unfinished":')
        run = self.run_check()
        self.assertEqual(run.returncode, 2)
        report = self.receipt()
        self.assertEqual(report["result"], "invalid_input")
        self.assertTrue(report["errors"])
        self.assertEqual(report["episode"]["sha256"],
                         hashlib.sha256(self.packet.read_bytes()).hexdigest())

    def test_report_cannot_overwrite_packet_or_earlier_receipt(self):
        self.report = self.packet
        before = self.packet.read_bytes()
        self.assertEqual(self.run_check().returncode, 2)
        self.assertEqual(self.packet.read_bytes(), before)
        self.report = self.root / "old-receipt.json"
        self.report.write_text("previous result")
        self.assertEqual(self.run_check().returncode, 2)
        self.assertEqual(self.report.read_text(), "previous result")

    def test_report_cannot_follow_a_dangling_symlink(self):
        target = self.root / "absent.json"
        self.report.symlink_to(target)
        self.assertEqual(self.run_check().returncode, 2)
        self.assertFalse(target.exists())
        self.assertTrue(self.report.is_symlink())

    def test_packet_changed_while_checking_cannot_get_passing_receipt(self):
        original = self.packet.read_bytes()

        def change_packet(*args):
            self.packet.write_bytes(original + b"\n")
            return [], []

        argv = [str(SCRIPT), str(self.packet), "--stage", "plan", "--report", str(self.report)]
        with patch.object(sys, "argv", argv), patch.object(checker, "check", side_effect=change_packet):
            self.assertEqual(checker.main(), 1)
        report = self.receipt()
        self.assertEqual(report["result"], "blocked")
        self.assertEqual(report["episode"]["sha256"], hashlib.sha256(original).hexdigest())
        self.assertTrue(any("changed during validation" in e for e in report["errors"]))

    def test_without_report_keeps_read_only_cli(self):
        before = set(self.root.iterdir())
        self.assertEqual(self.run_check(report=False).returncode, 0)
        self.assertEqual(set(self.root.iterdir()), before)

    def test_invalid_input_without_report_keeps_stderr_diagnostics(self):
        self.packet.write_text("not JSON")
        run = self.run_check(report=False)
        self.assertEqual(run.returncode, 2)
        self.assertIn("ERROR:", run.stderr)
        self.assertEqual(run.stdout, "")
        self.assertFalse(self.report.exists())


if __name__ == "__main__":
    unittest.main()
