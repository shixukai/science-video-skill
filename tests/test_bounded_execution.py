"""Explicit synthetic-only regression entrypoints; never run live renderer entrypoints."""
import pathlib, subprocess, sys, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
class BoundedExecutionTests(unittest.TestCase):
    def test_synthetic_entrypoints(self):
        base = ROOT / 'skills/science-video-production/scripts'
        for rel in ('bounded_i2v/tests/test_core.py', 'bounded_i2v/tests/test_runner.py', 'bounded_blender/test_blender_reuse.py', 'bounded_blender/test_blender_continuous.py'):
            with self.subTest(entry=rel):
                proc = subprocess.run([sys.executable, '-I', '-S', '-B', str(base / rel), '-v'], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
if __name__ == '__main__':
    unittest.main()
