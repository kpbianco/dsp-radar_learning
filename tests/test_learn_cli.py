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
MANIFEST = json.loads((ROOT / "curriculum" / "modules.json").read_text(encoding="utf-8"))


def implemented_modules() -> list[dict]:
    return [module for module in MANIFEST["modules"] if module["status"] == "implemented"]


def first_scaffolded_module() -> dict | None:
    return next(
        (module for module in MANIFEST["modules"] if module["status"] == "scaffolded"),
        None,
    )

class LearnCliTests(unittest.TestCase):
    def run_cli(self, *args, initial_state=None, state_capture=None):
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
            if state_capture is not None:
                fixture_state = fixture_root / ".learning" / "progress.json"
                state_capture.update(json.loads(fixture_state.read_text(encoding="utf-8")))
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
        self.assertIn(f"implemented: {len(implemented_modules())}", p.stdout)

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

    def test_start_p05_module(self):
        p = self.run_cli("start", "5")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P05", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_start_p06_module(self):
        p = self.run_cli("start", "6")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P06", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_start_p07_module(self):
        p = self.run_cli("start", "7")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P07", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_start_p08_module(self):
        p = self.run_cli("start", "8")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P08", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_start_p09_module(self):
        p = self.run_cli("start", "9")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P09", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_start_p10_module(self):
        p = self.run_cli("start", "10")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P10", p.stdout)
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

    def test_default_start_advances_to_p05_after_p04_completion(self):
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
        self.assertIn("P05 — Explore White, Colored, and Impulsive Noise", p.stdout)
        self.assertIn("status: implemented", p.stdout)
        self.assertIn("Tutor entry", p.stdout)

    def test_default_start_advances_to_p06_after_p05_completion(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P05",
                "completed": ["P01", "P02", "P03", "P04", "P05"],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P06 — Use an Impulse to Reveal a System", p.stdout)
        self.assertIn("status: implemented", p.stdout)

    def test_default_start_advances_to_p07_after_p06_completion(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P06",
                "completed": ["P01", "P02", "P03", "P04", "P05", "P06"],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P07 — Understand Convolution as Echo Addition", p.stdout)
        self.assertIn("status: implemented", p.stdout)

    def test_default_start_advances_to_p08_after_p07_completion(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P07",
                "completed": ["P01", "P02", "P03", "P04", "P05", "P06", "P07"],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P08 — Use Correlation to Find a Hidden Pattern", p.stdout)
        self.assertIn("status: implemented", p.stdout)

    def test_default_start_advances_to_p09_after_p08_completion(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P08",
                "completed": ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08"],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P09 — Compare FIR and IIR Filters by Behavior", p.stdout)
        self.assertIn("status: implemented", p.stdout)

    def test_default_start_advances_to_p10_after_p09_completion(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P09",
                "completed": [
                    "P01", "P02", "P03", "P04", "P05",
                    "P06", "P07", "P08", "P09",
                ],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P10 — Decimate and Interpolate Without Creating Artifacts", p.stdout)
        self.assertIn("status: implemented", p.stdout)

    def test_default_start_does_not_skip_p09_after_scaffolded_p10_becomes_implemented(self):
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": "P10",
                "completed": [
                    "P01", "P02", "P03", "P04", "P05",
                    "P06", "P07", "P08",
                ],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("P09 — Compare FIR and IIR Filters by Behavior", p.stdout)
        self.assertNotIn("P10 — Decimate and Interpolate Without Creating Artifacts", p.stdout)

    def test_default_start_stays_at_manifest_frontier_after_all_implemented_complete(self):
        implemented = implemented_modules()
        frontier = implemented[-1]
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": frontier["id"],
                "completed": [module["id"] for module in implemented],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(f"{frontier['id']} — {frontier['title']}", p.stdout)
        self.assertIn("status: implemented", p.stdout)

    def test_complete_p05_persists_current_completion_and_note(self):
        persisted_state = {}
        p = self.run_cli(
            "complete",
            "5",
            "--note",
            "Distinguished equal-RMS noise by distribution and spectrum.",
            initial_state={
                "schema_version": 1,
                "current": "P04",
                "completed": ["P01", "P02", "P03", "P04"],
                "notes": {},
            },
            state_capture=persisted_state,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Recorded local completion for P05.", p.stdout)
        self.assertEqual(persisted_state["current"], "P05")
        self.assertEqual(
            persisted_state["completed"],
            ["P01", "P02", "P03", "P04", "P05"],
        )
        self.assertEqual(
            persisted_state["notes"]["P05"],
            "Distinguished equal-RMS noise by distribution and spectrum.",
        )

    def test_complete_p06_persists_current_completion_and_note(self):
        persisted_state = {}
        p = self.run_cli(
            "complete",
            "6",
            "--note",
            "Explained LTI output as weighted delayed input copies.",
            initial_state={
                "schema_version": 1,
                "current": "P05",
                "completed": ["P01", "P02", "P03", "P04", "P05"],
                "notes": {},
            },
            state_capture=persisted_state,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Recorded local completion for P06.", p.stdout)
        self.assertEqual(persisted_state["current"], "P06")
        self.assertEqual(
            persisted_state["completed"],
            ["P01", "P02", "P03", "P04", "P05", "P06"],
        )
        self.assertEqual(
            persisted_state["notes"]["P06"],
            "Explained LTI output as weighted delayed input copies.",
        )

    def test_complete_p07_persists_current_completion_and_note(self):
        persisted_state = {}
        p = self.run_cli(
            "complete",
            "7",
            "--note",
            "Explained every convolution sample as the sum of echo-path terms.",
            initial_state={
                "schema_version": 1,
                "current": "P06",
                "completed": ["P01", "P02", "P03", "P04", "P05", "P06"],
                "notes": {},
            },
            state_capture=persisted_state,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Recorded local completion for P07.", p.stdout)
        self.assertEqual(persisted_state["current"], "P07")
        self.assertEqual(
            persisted_state["completed"],
            ["P01", "P02", "P03", "P04", "P05", "P06", "P07"],
        )
        self.assertEqual(
            persisted_state["notes"]["P07"],
            "Explained every convolution sample as the sum of echo-path terms.",
        )

    def test_complete_p08_persists_current_completion_and_note(self):
        persisted_state = {}
        p = self.run_cli(
            "complete",
            "8",
            "--note",
            "Located a hidden code by reading the correlation lag axis.",
            initial_state={
                "schema_version": 1,
                "current": "P07",
                "completed": ["P01", "P02", "P03", "P04", "P05", "P06", "P07"],
                "notes": {},
            },
            state_capture=persisted_state,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Recorded local completion for P08.", p.stdout)
        self.assertEqual(persisted_state["current"], "P08")
        self.assertEqual(
            persisted_state["completed"],
            ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08"],
        )
        self.assertEqual(
            persisted_state["notes"]["P08"],
            "Located a hidden code by reading the correlation lag axis.",
        )

    def test_complete_p09_persists_current_completion_and_note(self):
        persisted_state = {}
        p = self.run_cli(
            "complete",
            "9",
            "--note",
            "Chose FIR or IIR from delay, transient, stability, and cost needs.",
            initial_state={
                "schema_version": 1,
                "current": "P08",
                "completed": ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08"],
                "notes": {},
            },
            state_capture=persisted_state,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Recorded local completion for P09.", p.stdout)
        self.assertEqual(persisted_state["current"], "P09")
        self.assertEqual(
            persisted_state["completed"],
            ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09"],
        )
        self.assertEqual(
            persisted_state["notes"]["P09"],
            "Chose FIR or IIR from delay, transient, stability, and cost needs.",
        )

    def test_complete_p10_persists_current_completion_and_note(self):
        persisted_state = {}
        p = self.run_cli(
            "complete",
            "10",
            "--note",
            "Explained pre-decimation anti-aliasing and post-insertion reconstruction.",
            initial_state={
                "schema_version": 1,
                "current": "P09",
                "completed": [
                    "P01", "P02", "P03", "P04", "P05",
                    "P06", "P07", "P08", "P09",
                ],
                "notes": {},
            },
            state_capture=persisted_state,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Recorded local completion for P10.", p.stdout)
        self.assertEqual(persisted_state["current"], "P10")
        self.assertEqual(
            persisted_state["completed"],
            ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10"],
        )
        self.assertEqual(
            persisted_state["notes"]["P10"],
            "Explained pre-decimation anti-aliasing and post-insertion reconstruction.",
        )

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
        implemented = implemented_modules()
        pending = first_scaffolded_module()
        if pending is None:
            self.skipTest("all curriculum modules are implemented")
        expected = implemented[-1]
        p = self.run_cli(
            "start",
            initial_state={
                "schema_version": 1,
                "current": pending["id"],
                "completed": [module["id"] for module in implemented[:-1]],
                "notes": {},
            },
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(f"{expected['id']} — {expected['title']}", p.stdout)

    def test_next_scaffolded_module_is_not_tutorable(self):
        pending = first_scaffolded_module()
        if pending is None:
            self.skipTest("all curriculum modules are implemented")
        p = self.run_cli("start", pending["id"])
        self.assertEqual(p.returncode, 3)
        self.assertIn(f"awaits Portfolio batch {pending['implementation_batch']}", p.stdout)

    def test_doctor(self):
        p = self.run_cli("doctor")
        self.assertEqual(p.returncode, 0, p.stderr)

if __name__ == "__main__":
    unittest.main()
