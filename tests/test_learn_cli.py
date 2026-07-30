from __future__ import annotations
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin/learn"

class LearnCliTests(unittest.TestCase):
    def run_cli(self, *args):
        with tempfile.TemporaryDirectory() as td:
            env = os.environ.copy()
            env["HOME"] = td
            proc = subprocess.run([str(CLI), *args], cwd=ROOT, text=True, capture_output=True, env=env)
            return proc

    def test_status(self):
        p = self.run_cli("status")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("curriculum: 84 modules", p.stdout)
        self.assertIn("implemented: 1", p.stdout)

    def test_start_reference_module(self):
        p = self.run_cli("start", "1")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P01", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_scaffolded_module_is_not_tutorable(self):
        p = self.run_cli("start", "2")
        self.assertEqual(p.returncode, 3)
        self.assertIn("awaits Portfolio batch P02", p.stdout)

    def test_doctor(self):
        p = self.run_cli("doctor")
        self.assertEqual(p.returncode, 0, p.stderr)

if __name__ == "__main__":
    unittest.main()
