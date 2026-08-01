from __future__ import annotations
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin/learn"

class LearnCliTests(unittest.TestCase):
    def run_cli(self, *args, initial_state=None):
        with tempfile.TemporaryDirectory() as td:
            fixture_root = Path(td) / "repo"
            fixture_cli = fixture_root / "bin" / "learn"
            fixture_manifest = fixture_root / "curriculum" / "modules.json"
            fixture_cli.parent.mkdir(parents=True)
            fixture_manifest.parent.mkdir(parents=True)
            shutil.copy2(CLI, fixture_cli)
            shutil.copy2(ROOT / "curriculum" / "modules.json", fixture_manifest)

            manifest = json.loads(fixture_manifest.read_text(encoding="utf-8"))
            for module in manifest["modules"]:
                fixture_readme = fixture_root / module["folder"] / "README.md"
                fixture_readme.parent.mkdir(parents=True)
                shutil.copy2(ROOT / module["folder"] / "README.md", fixture_readme)

            if initial_state is not None:
                fixture_state = fixture_root / ".learning" / "progress.json"
                fixture_state.parent.mkdir(parents=True)
                fixture_state.write_text(
                    json.dumps(initial_state, indent=2) + "\n",
                    encoding="utf-8",
                )

            env = os.environ.copy()
            env["HOME"] = td
            proc = subprocess.run(
                [str(fixture_cli), *args],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                env=env,
                timeout=10,
            )
            return proc

    def test_runs_are_isolated_from_repository_learning_state(self):
        repository_state = ROOT / ".learning" / "progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        p = self.run_cli("start", "2")
        self.assertEqual(p.returncode, 0, p.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_status(self):
        p = self.run_cli("status")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("curriculum: 84 modules", p.stdout)
        self.assertIn("implemented: 4", p.stdout)

    def test_start_reference_module(self):
        p = self.run_cli("start", "1")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P01", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_start_p02_module(self):
        p = self.run_cli("start", "2")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P02", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_start_p03_module(self):
        p = self.run_cli("start", "3")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P03", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_start_p04_module(self):
        p = self.run_cli("start", "4")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P04", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_default_start_resumes_an_incomplete_current_module(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P01",
                "completed": [],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P01 — Build a Sinusoid and a Complex Phasor", p.stdout)

    def test_default_start_advances_to_p02_after_p01_completion(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P01",
                "completed": ["P01"],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P02 — See Sampling as Taking Measurements", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_default_start_advances_to_p03_after_p02_completion(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P02",
                "completed": ["P01", "P02"],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P03 — Make Aliasing Visually Obvious", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_default_start_advances_to_p04_after_p03_completion(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P03",
                "completed": ["P01", "P02", "P03"],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P04 — Quantize a Signal and Hear/See the Error", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_default_start_does_not_cross_into_p05_after_all_implemented_complete(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P04",
                "completed": ["P01", "P02", "P03", "P04"],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P04 — Quantize a Signal and Hear/See the Error", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)
        self.assertNotIn("P05", p.stdout)

    def test_continue_resumes_the_current_module_even_when_completed(self):
        p = self.run_cli(
            "continue",
            initial_state={
                "schema_version": 1,
                "current": "P01",
                "completed": ["P01"],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P01 — Build a Sinusoid and a Complex Phasor", p.stdout)

    def test_default_complete_does_not_advance_from_completed_current_module(self):
        p = self.run_cli(
            "complete",
            initial_state={
                "schema_version": 1,
                "current": "P01",
                "completed": ["P01"],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Recorded local completion for P01.", p.stdout)
        self.assertNotIn("P02", p.stdout)

    def test_default_start_skips_a_scaffolded_current_module(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P05",
                "completed": ["P01", "P02", "P03"],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P04 — Quantize a Signal and Hear/See the Error", p.stdout)

    def test_next_scaffolded_module_is_not_tutorable(self):
        p = self.run_cli("start", "5")
        self.assertEqual(p.returncode, 3)
        self.assertIn("awaits Portfolio batch P05", p.stdout)

    def test_doctor(self):
        p = self.run_cli("doctor")
        self.assertEqual(p.returncode, 0, p.stderr)

if __name__ == "__main__":
    unittest.main()
