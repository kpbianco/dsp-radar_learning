from __future__ import annotations

import copy
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/35-create-unambiguous-range-aliasing"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Why can a distant target appear at a shorter false range?"
SPEED_OF_LIGHT_MPS = 299_792_458.0
MAX_PULSE_COUNT = 8
MAX_RANGE_SWEEP_CASES = 6
MAX_PRF_SWEEP_CASES = 5
EXPECTED_IDENTITY = {
    "number": 35,
    "id": "P35",
    "title": "Create Unambiguous-Range Aliasing",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "create-unambiguous-range-aliasing",
    "folder": "modules/35-create-unambiguous-range-aliasing",
    "status": "implemented",
    "implementation_batch": "P35",
}


def finite_real(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_p35_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P35 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P35 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P35"]
    if len(matches) != 1:
        return errors + [f"expected one P35 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P35 {key} must be {expected!r}")
    return errors


def fold_range(true_range_m: float, prf_hz: float) -> tuple[float, int, float]:
    """Independent physical oracle for the pulse-identity ambiguity model."""
    if not finite_real(true_range_m) or true_range_m < 0:
        raise ValueError("true range must be finite and nonnegative")
    if not finite_real(prf_hz) or prf_hz <= 0:
        raise ValueError("PRF must be finite and positive")
    unambiguous_range_m = SPEED_OF_LIGHT_MPS / (2.0 * prf_hz)
    ambiguity_order = math.floor(true_range_m / unambiguous_range_m)
    apparent_range_m = true_range_m - ambiguity_order * unambiguous_range_m
    # Protect the exact-multiple endpoint from a floating-point residue.
    if math.isclose(apparent_range_m, unambiguous_range_m, rel_tol=0.0, abs_tol=1e-9):
        apparent_range_m = 0.0
        ambiguity_order += 1
    return apparent_range_m, ambiguity_order, unambiguous_range_m


def periodic_echo_gates(
    true_range_m: float,
    prf_hz: float,
    sample_rate_hz: float,
    pulse_count: int,
) -> tuple[list[int], list[int], int, float, float, int]:
    """Sample a periodic echo timeline and discard transmit-pulse identity."""
    apparent_range_m, ambiguity_order, unambiguous_range_m = fold_range(
        true_range_m, prf_hz
    )
    if not finite_real(sample_rate_hz) or sample_rate_hz <= 0:
        raise ValueError("sample rate must be finite and positive")
    if (
        not isinstance(pulse_count, int)
        or isinstance(pulse_count, bool)
        or not 2 <= pulse_count <= MAX_PULSE_COUNT
    ):
        raise ValueError("pulse count must be a bounded integer")
    samples_per_pri = math.floor(sample_rate_hz / prf_hz + 0.5)
    if samples_per_pri < 1:
        raise ValueError("PRI must contain at least one sample")
    delay_samples = math.floor(
        2.0 * true_range_m * sample_rate_hz / SPEED_OF_LIGHT_MPS + 0.5
    )
    timeline_samples = pulse_count * samples_per_pri
    echo_samples = [
        pulse_index * samples_per_pri + delay_samples
        for pulse_index in range(pulse_count)
        if pulse_index * samples_per_pri + delay_samples < timeline_samples
    ]
    listening_intervals = [sample // samples_per_pri for sample in echo_samples]
    fast_time_samples = [sample % samples_per_pri for sample in echo_samples]
    return (
        listening_intervals,
        fast_time_samples,
        ambiguity_order,
        apparent_range_m,
        unambiguous_range_m,
        samples_per_pri,
    )


def validate_simulation_shape(pulse_count: object, range_cases: object, prf_cases: object) -> None:
    """Bound the pedagogical simulation independently of MATLAB implementation."""
    for name, value, maximum in (
        ("pulse_count", pulse_count, MAX_PULSE_COUNT),
        ("range_cases", range_cases, MAX_RANGE_SWEEP_CASES),
        ("prf_cases", prf_cases, MAX_PRF_SWEEP_CASES),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
            raise ValueError(f"{name} must be a bounded positive integer")


def source_contract_errors(source: str) -> list[str]:
    required = (
        "random_seed = 3501;",
        "speed_of_light_mps = 299792458;",
        "sample_rate_hz = 20e6;",
        "baseline_prf_hz = 20e3;",
        "baseline_true_range_m = 18e3;",
        "pulse_count = 6;",
        "pri_s = 1/prf_hz;",
        "unambiguous_range_m = speed_of_light_mps/(2*prf_hz);",
        "ambiguity_order = floor(true_range_m/unambiguous_range_m);",
        "apparent_range_m = true_range_m - ambiguity_order*unambiguous_range_m;",
        "echo_start_sample = transmit_start_sample+...\n"
        "        round(round_trip_delay_s*sample_rate_hz);",
        "transmit_start_samples(ambiguity_order+1);",
        "measured_fast_time_s = baseline_echo_arrival_s-",
        "timeline_s(listening_interval_start_sample);",
        "measured_apparent_range_m = speed_of_light_mps*measured_fast_time_s/2;",
        "range_sweep_m",
        "prf_sweep_hz",
        "max_pulse_count",
        "max_range_sweep_cases",
        "max_prf_sweep_cases",
        "Intentionally broken case",
        "Recovery",
        "broken_model_valid = false",
        "recovered_model_valid = true",
        "close(findall(0, 'Type', 'figure', 'Tag', 'P35'))",
    )
    errors = [f"missing source marker: {marker}" for marker in required if marker not in source]
    for pattern in (
        r"\bambgfun\s*\(", r"\brange2time\s*\(", r"\btime2range\s*\(",
        r"\bphased\.", r"\bparfor\b", r"(?m)^\s*while\s+true\b",
    ):
        if re.search(pattern, source, flags=re.IGNORECASE):
            errors.append(f"opaque or unbounded operation: {pattern}")
    return errors


class P35ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.text = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        cls.experiment = cls.text["experiment.m"]

    def test_complete_artifacts_exact_identity_and_permanent_prerequisite(self):
        self.assertEqual(validate_p35_contract(MODULE, self.manifest), [])
        for name, text in self.text.items():
            self.assertGreater(len(text), 100, name)
            self.assertIn(QUESTION, text)
        prerequisite = next(item for item in self.manifest["modules"] if item["id"] == "P34")
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertIn("P34", self.text["README.md"])
        self.assertIn("P34", self.text["lesson.md"])

    def test_contract_rejects_missing_empty_duplicate_and_malformed_inputs(self):
        self.assertIn("manifest modules must be a list", validate_p35_contract(MODULE, {}))
        self.assertIn("manifest module entries must be objects", validate_p35_contract(MODULE, {"modules": ["bad"]}))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P35 manifest entry, found 2", validate_p35_contract(MODULE, duplicate))
        wrong = copy.deepcopy(self.manifest)
        entry = next(item for item in wrong["modules"] if item["id"] == "P35")
        entry["guiding_question"] = "generic"
        entry["status"] = "scaffolded"
        errors = validate_p35_contract(MODULE, wrong)
        self.assertIn(f"P35 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P35 status must be 'implemented'", errors)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            for name in ARTIFACTS:
                (fixture / name).write_text("content\n", encoding="utf-8")
            (fixture / "experiment.m").unlink()
            (fixture / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p35_contract(fixture, self.manifest)
            self.assertIn("P35 missing experiment.m", errors)
            self.assertIn("P35 empty checks.md", errors)

    def test_independent_range_aliasing_oracle_and_edge_cases(self):
        prf_hz = 10_000.0
        apparent, order, unambiguous = fold_range(2.25 * SPEED_OF_LIGHT_MPS / (2 * prf_hz), prf_hz)
        self.assertAlmostEqual(unambiguous, 14_989.6229, places=4)
        self.assertEqual(order, 2)
        self.assertAlmostEqual(apparent, 0.25 * unambiguous, places=9)
        for multiplier, expected_order, expected_apparent in ((0, 0, 0), (1, 1, 0), (3, 3, 0), (3.75, 3, 0.75)):
            apparent, order, value = fold_range(multiplier * unambiguous, prf_hz)
            with self.subTest(multiplier=multiplier):
                self.assertEqual(order, expected_order)
                self.assertAlmostEqual(apparent, expected_apparent * value, places=8)
        for args in ((-1.0, prf_hz), (float("nan"), prf_hz), (float("inf"), prf_hz), (1.0, 0.0), (1.0, -1.0), (1.0, True)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                fold_range(*args)

    def test_periodic_echo_timeline_loses_identity_and_repeats_one_fast_time_gate(self):
        (
            listening_intervals,
            fast_time_samples,
            ambiguity_order,
            apparent_range_m,
            unambiguous_range_m,
            samples_per_pri,
        ) = periodic_echo_gates(18_000.0, 20_000.0, 20_000_000.0, 6)
        self.assertEqual(ambiguity_order, 2)
        self.assertEqual(samples_per_pri, 1000)
        self.assertEqual(listening_intervals, [2, 3, 4, 5])
        self.assertEqual(fast_time_samples, [402, 402, 402, 402])
        sampled_apparent_range_m = (
            fast_time_samples[0] * SPEED_OF_LIGHT_MPS / (2.0 * 20_000_000.0)
        )
        half_sample_m = SPEED_OF_LIGHT_MPS / (4.0 * 20_000_000.0)
        self.assertLessEqual(abs(sampled_apparent_range_m - apparent_range_m), half_sample_m)

        shifted = periodic_echo_gates(
            18_000.0 + 3.0 * unambiguous_range_m,
            20_000.0,
            20_000_000.0,
            8,
        )
        self.assertEqual(shifted[2], 5)
        self.assertEqual(shifted[1], [402, 402, 402])
        self.assertAlmostEqual(shifted[3], apparent_range_m, places=8)

        for old, new in (
            (
                "round(round_trip_delay_s*sample_rate_hz);",
                "floor(round_trip_delay_s*sample_rate_hz);",
            ),
            (
                "transmit_start_samples(ambiguity_order+1);",
                "transmit_start_samples(ambiguity_order+2);",
            ),
            (
                "timeline_s(listening_interval_start_sample);",
                "timeline_s(transmit_start_samples(1));",
            ),
        ):
            with self.subTest(old=old):
                self.assertTrue(source_contract_errors(self.experiment.replace(old, new, 1)))

    def test_higher_prf_reduces_unambiguous_range_and_recovery_is_physical(self):
        true_range_m = 37_000.0
        low_apparent, low_order, low_unambiguous = fold_range(true_range_m, 5_000.0)
        high_apparent, high_order, high_unambiguous = fold_range(true_range_m, 18_000.0)
        self.assertGreater(low_unambiguous, high_unambiguous)
        self.assertGreaterEqual(high_order, low_order)
        self.assertNotAlmostEqual(low_apparent, high_apparent, places=6)
        # A lower PRF is a valid recovery only when its unambiguous range covers the target.
        recovered, recovered_order, _ = fold_range(true_range_m, 3_000.0)
        self.assertEqual(recovered_order, 0)
        self.assertAlmostEqual(recovered, true_range_m, places=9)

    def test_resource_bounds_reject_malformed_or_unbounded_simulation_shapes(self):
        validate_simulation_shape(5, 4, 3)
        for shape in (
            (0, 4, 3), (MAX_PULSE_COUNT + 1, 4, 3), (True, 4, 3),
            (5, 0, 3), (5, MAX_RANGE_SWEEP_CASES + 1, 3), (5, 4.0, 3),
            (5, 4, 0), (5, 4, MAX_PRF_SWEEP_CASES + 1), (5, 4, float("nan")),
        ):
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                validate_simulation_shape(*shape)

    def test_deterministic_transparent_source_sweeps_broken_case_and_recovery(self):
        self.assertEqual(source_contract_errors(self.experiment), [])
        for old, new in (
            ("floor(true_range_m/unambiguous_range_m)", "round(true_range_m/unambiguous_range_m)"),
            ("true_range_m - ambiguity_order*unambiguous_range_m", "true_range_m"),
            ("broken_model_valid = false", "broken_model_valid = true"),
            ("recovered_model_valid = true", "recovered_model_valid = false"),
            ("speed_of_light_mps = 299792458;", "speed_of_light_mps = 3e8;"),
        ):
            with self.subTest(old=old):
                self.assertTrue(source_contract_errors(self.experiment.replace(old, new, 1)))
        for marker in ("Sweep 1", "Sweep 2", "range_sweep_m", "prf_sweep_hz", "Intentionally broken case", "Recovery"):
            self.assertIn(marker.lower(), self.experiment.lower())

    def test_docs_cli_timeout_cancellation_isolation_and_compatibility_contract(self):
        combined = "\n".join(self.text.values())
        for marker in (
            "pulse repetition frequency", "PRI", "round-trip", "unambiguous range", "ambiguity order",
            "apparent range", "P34", "base MATLAB", "Baseline observation", "Sweep one variable",
            "broken", "recover", "Observation checks", "Prediction checks", "Interpretation checks", "teach-back",
            "Ctrl+C", "private seed", "global random stream", "figures tagged `P35`", ".learning/",
            "worker", "timer", "external transaction", "rollback", "scaffolded",
        ):
            self.assertIn(marker.lower(), combined.lower(), marker)
        self.assertNotRegex(combined, r"(?i)implementation batch `P35` is pending")
        self.assertEqual(self.experiment.count("RandStream('mt19937ar', 'Seed', random_seed)"), 2)
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("Project 35", root_readme)
        self.assertIn("Project 35", start_here)
        self.assertRegex(module_index, r"\| \[P35\].*\| implemented \|")
        state = ROOT / ".learning/progress.json"
        before = state.read_bytes() if state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir()
            target = fixture / EXPECTED_IDENTITY["folder"]
            target.mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
            shutil.copy2(ROOT / "curriculum/modules.json", fixture / "curriculum/modules.json")
            shutil.copy2(MODULE / "README.md", target / "README.md")
            result = subprocess.run([str(fixture / "bin/learn"), "start", "35"], cwd=fixture, text=True,
                                    capture_output=True, env=os.environ.copy(), timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P35 — Create Unambiguous-Range Aliasing", result.stdout)
            self.assertIn("status: implemented", result.stdout)
        self.assertEqual(state.read_bytes() if state.exists() else None, before)

    def test_artifact_newlines_no_placeholders_and_honest_runtime_boundary(self):
        combined = "\n".join(self.text.values())
        for name, text in self.text.items():
            self.assertTrue(text.endswith("\n"), name)
            self.assertFalse(text.endswith("\n\n"), name)
        for phrase in ("lorem ipsum", "placeholder", "fill this in", "coming soon"):
            self.assertNotIn(phrase, combined.lower())
        self.assertNotRegex(combined, r"(?i)MATLAB (?:was )?(?:executed|validated|passed)")

    def test_retained_evidence_is_honest_complete_and_has_one_newline(self):
        paths = sorted((ROOT / "docs/evidence").glob("P35-*.md"))
        self.assertEqual(len(paths), 1)
        evidence = paths[0].read_text(encoding="utf-8")
        for marker in (
            "Acceptance mapping", "Figure and metric inventory", "Exact commands and results",
            "Changed and preserved invariants", "Residual risks and unperformed validation", "Rollback and recovery",
            "Validation class", "MATLAB runtime status", "Toolboxes", "did not run",
        ):
            self.assertIn(marker, evidence)
        for command in (
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
        ):
            self.assertIn(command, evidence)
        self.assertNotIn("PENDING —", evidence)
        self.assertTrue(evidence.endswith("\n"))
        self.assertFalse(evidence.endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
