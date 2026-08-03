from __future__ import annotations

import cmath
import copy
import json
import math
import os
import random
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/38-implement-a-two-pulse-and-three-pulse-mti-canceller"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How do simple delay-line cancellers remove stationary clutter?"
SPEED_OF_LIGHT_MPS = 299_792_458.0
MAX_FAST_TIME_SAMPLES = 256
MAX_PULSE_COUNT = 128
MAX_COMPONENT_COUNT = 8
MAX_SWEEP_CASES = 9
MAX_RESPONSE_SAMPLES = 2001
EXPECTED_IDENTITY = {
    "number": 38,
    "id": "P38",
    "title": "Implement a Two-Pulse and Three-Pulse MTI Canceller",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "implement-a-two-pulse-and-three-pulse-mti-canceller",
    "folder": "modules/38-implement-a-two-pulse-and-three-pulse-mti-canceller",
    "status": "implemented",
    "implementation_batch": "P38",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p38_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P38 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P38 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P38"]
    if len(matches) != 1:
        return errors + [f"expected one P38 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P38 {key} must be {expected!r}")
    return errors


def validate_controls(
    *,
    fast_time_count: object = 128,
    pulse_count: object = 64,
    range_bins: object = (25, 63, 100),
    velocities_mps: object = (3.0, 15.0),
    carrier_hz: object = 10e9,
    prf_hz: object = 5e3,
    velocity_sweep: object = (-30, -15, -3, 0, 3, 15, 30),
    prf_sweep: object = (3e3, 4e3, 5e3, 7e3, 9e3),
    prf_sweep_target_velocity_mps: object = 12.0,
    response_count: object = 1001,
) -> None:
    if (
        not isinstance(fast_time_count, int)
        or isinstance(fast_time_count, bool)
        or not 32 <= fast_time_count <= MAX_FAST_TIME_SAMPLES
    ):
        raise ValueError("fast-time count must be a bounded integer")
    if (
        not isinstance(pulse_count, int)
        or isinstance(pulse_count, bool)
        or not 8 <= pulse_count <= MAX_PULSE_COUNT
        or pulse_count % 2
    ):
        raise ValueError("pulse count must be a bounded even integer")
    if not finite_real(carrier_hz) or carrier_hz <= 0:
        raise ValueError("carrier must be finite and positive")
    if not finite_real(prf_hz) or prf_hz <= 0:
        raise ValueError("PRF must be finite and positive")
    if not isinstance(range_bins, (list, tuple)) or not 1 <= len(range_bins) <= MAX_COMPONENT_COUNT:
        raise ValueError("range bins must be a bounded sequence")
    if not all(
        isinstance(value, int)
        and not isinstance(value, bool)
        and 1 <= value <= fast_time_count
        for value in range_bins
    ):
        raise ValueError("range bins must be valid integer rows")
    if len(set(range_bins)) != len(range_bins):
        raise ValueError("range bins must be unique")
    if not isinstance(velocities_mps, (list, tuple)) or not 1 <= len(velocities_mps) <= MAX_COMPONENT_COUNT:
        raise ValueError("velocities must be a bounded sequence")
    if not all(finite_real(value) for value in velocities_mps):
        raise ValueError("velocities must be finite")
    wavelength_m = SPEED_OF_LIGHT_MPS / carrier_hz
    if any(abs(2.0 * value / wavelength_m) >= prf_hz / 2.0 for value in velocities_mps):
        raise ValueError("baseline velocities must be strictly unambiguous")
    for sweep, label in ((velocity_sweep, "velocity"), (prf_sweep, "PRF")):
        if not isinstance(sweep, (list, tuple)) or not 3 <= len(sweep) <= MAX_SWEEP_CASES:
            raise ValueError(f"{label} sweep must have a bounded case count")
        if not all(finite_real(value) for value in sweep):
            raise ValueError(f"{label} sweep values must be finite")
        if any(right <= left for left, right in zip(sweep, sweep[1:])):
            raise ValueError(f"{label} sweep must increase strictly")
    if not any(value < 0 for value in velocity_sweep) or 0 not in velocity_sweep or not any(value > 0 for value in velocity_sweep):
        raise ValueError("velocity sweep must include both signs and zero")
    if any(value <= 0 for value in prf_sweep):
        raise ValueError("PRF sweep must be positive")
    if not finite_real(prf_sweep_target_velocity_mps) or prf_sweep_target_velocity_mps == 0:
        raise ValueError("PRF-sweep target velocity must be finite and nonzero")
    fixed_doppler_hz = 2.0 * prf_sweep_target_velocity_mps / wavelength_m
    if any(abs(fixed_doppler_hz) >= value / 2.0 for value in prf_sweep):
        raise ValueError("PRF-sweep target must be strictly unambiguous")
    if (
        not isinstance(response_count, int)
        or isinstance(response_count, bool)
        or not 3 <= response_count <= MAX_RESPONSE_SAMPLES
        or response_count % 2 == 0
    ):
        raise ValueError("response count must be a bounded odd integer")


def canceller_response(velocity_mps: float, *, carrier_hz: float = 10e9, prf_hz: float = 5e3) -> tuple[float, float]:
    wavelength_m = SPEED_OF_LIGHT_MPS / carrier_hz
    doppler_hz = 2.0 * velocity_mps / wavelength_m
    omega = 2.0 * math.pi * doppler_hz / prf_hz
    h2 = 1.0 - cmath.exp(-1j * omega)
    h3 = h2**2
    return abs(h2), abs(h3)


def apply_slow_time_canceller(matrix: list[list[complex]], order: int) -> list[list[complex]]:
    if order not in (1, 2):
        raise ValueError("supported difference orders are one and two")
    if not matrix or not all(isinstance(row, list) for row in matrix):
        raise ValueError("matrix must contain rows")
    width = len(matrix[0])
    if width <= order or any(len(row) != width for row in matrix):
        raise ValueError("matrix rows must be rectangular and long enough")
    if order == 1:
        return [[row[p] - row[p - 1] for p in range(1, width)] for row in matrix]
    return [[row[p] - 2.0 * row[p - 1] + row[p - 2] for p in range(2, width)] for row in matrix]


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", re.sub(r"\.\.\.\s*", "", source))
    required = (
        "random_seed = 3801",
        "RandStream('mt19937ar', 'Seed', random_seed)",
        "two_pulse_coefficients = [1 -1]",
        "three_pulse_coefficients = [1 -2 1]",
        "data_matrix(:, 2:end)-data_matrix(:, 1:end-1)",
        "data_matrix(:, 3:end)-2*data_matrix(:, 2:end-1)+data_matrix(:, 1:end-2)",
        "broken_fast_time_output = data_matrix(2:end, :)-data_matrix(1:end-1, :)",
        "broken_model_valid = false",
        "recovered_model_valid = true",
        "max_stored_numeric_values = 1000000",
    )
    return [marker for marker in required if marker not in compact]


class P38ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.docs = {
            name: (MODULE / name).read_text(encoding="utf-8")
            for name in ("README.md", "lesson.md", "walkthrough.md", "checks.md")
        }

    def test_identity_artifacts_and_prerequisite_are_permanent(self):
        self.assertEqual(validate_p38_contract(MODULE, self.manifest), [])
        entries = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(entries["P37"]["status"], "implemented")
        self.assertEqual(entries["P38"], EXPECTED_IDENTITY)
        for name in ARTIFACTS:
            data = (MODULE / name).read_bytes()
            self.assertTrue(data.endswith(b"\n"), name)
            self.assertFalse(data.endswith(b"\n\n"), name)
            self.assertNotIn(b"\r\n", data, name)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "module"
            shutil.copytree(MODULE, fixture)
            (fixture / "checks.md").unlink()
            self.assertIn("P38 missing checks.md", validate_p38_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("", encoding="utf-8")
            self.assertIn("P38 empty checks.md", validate_p38_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p38_contract(MODULE, []))
        malformed = {"modules": [None]}
        self.assertIn("manifest module entries must be objects", validate_p38_contract(MODULE, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P38 manifest entry, found 2", validate_p38_contract(MODULE, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(item for item in drifted["modules"] if item["id"] == "P38")["guiding_question"] = "Changed"
        self.assertTrue(any("guiding_question" in error for error in validate_p38_contract(MODULE, drifted)))

    def test_control_validation_rejects_malformed_aliasing_and_resource_overruns(self):
        validate_controls()
        invalid_cases = (
            {"fast_time_count": True},
            {"fast_time_count": 257},
            {"pulse_count": 63},
            {"pulse_count": 130},
            {"range_bins": (0, 63)},
            {"range_bins": (25, 25)},
            {"range_bins": tuple(range(1, 10))},
            {"velocities_mps": (math.nan,)},
            {"velocities_mps": (40.0,)},
            {"carrier_hz": math.inf},
            {"prf_hz": 0},
            {"velocity_sweep": (-3, 0, 0, 3)},
            {"velocity_sweep": (0, 1, 2)},
            {"velocity_sweep": (-1, math.inf, 1)},
            {"prf_sweep": (3000, 3000, 5000)},
            {"prf_sweep": (-1, 3000, 5000)},
            {"prf_sweep_target_velocity_mps": 0},
            {"prf_sweep_target_velocity_mps": math.nan},
            {"prf_sweep_target_velocity_mps": 30},
            {"response_count": 1000},
            {"response_count": 2003},
        )
        for controls in invalid_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_two_and_three_pulse_equations_null_clutter_and_match_target_gain(self):
        stationary = [[complex(row + 1, -row) for _ in range(16)] for row in range(4)]
        for order in (1, 2):
            filtered = apply_slow_time_canceller(stationary, order)
            self.assertTrue(all(abs(value) <= 1e-14 for row in filtered for value in row))

        wavelength_m = SPEED_OF_LIGHT_MPS / 10e9
        for velocity_mps in (-15.0, -3.0, 0.0, 3.0, 15.0):
            doppler_hz = 2.0 * velocity_mps / wavelength_m
            omega = 2.0 * math.pi * doppler_hz / 5e3
            samples = [[cmath.exp(1j * omega * pulse) for pulse in range(64)]]
            measured = []
            for order in (1, 2):
                output = apply_slow_time_canceller(samples, order)[0]
                measured.append(math.sqrt(sum(abs(value) ** 2 for value in output) / len(output)))
            expected = canceller_response(velocity_mps)
            self.assertAlmostEqual(measured[0], expected[0], places=12)
            self.assertAlmostEqual(measured[1], expected[1], places=12)
        slow_two, slow_three = canceller_response(3.0)
        self.assertLess(slow_three, slow_two)

    def test_mixed_scene_reveals_a_weak_moving_target_in_strong_shared_clutter(self):
        for marker in (
            "clutter_range_bins = [25 63 100]",
            "clutter_amplitudes = [20 12 8]",
            "target_range_bins = [63 92]",
            "target_velocities_mps = [3 15]",
        ):
            self.assertIn(marker, self.source)

        pulse_count = 64
        clutter_amplitude = 12.0
        target_amplitude = 1.0
        target_velocity_mps = 3.0
        wavelength_m = SPEED_OF_LIGHT_MPS / 10e9
        doppler_hz = 2.0 * target_velocity_mps / wavelength_m
        omega = 2.0 * math.pi * doppler_hz / 5e3
        clutter = [clutter_amplitude * cmath.exp(1j * math.radians(50.0))] * pulse_count
        target = [
            target_amplitude * cmath.exp(1j * (math.radians(25.0) + omega * pulse))
            for pulse in range(pulse_count)
        ]
        shared_cell = [[clutter[pulse] + target[pulse] for pulse in range(pulse_count)]]
        clutter_only = [clutter]
        target_only = [target]
        self.assertLess(target_amplitude / clutter_amplitude, 0.1)

        expected_gains = canceller_response(target_velocity_mps)
        for order, expected_gain in zip((1, 2), expected_gains):
            mixed_output = apply_slow_time_canceller(shared_cell, order)[0]
            clutter_output = apply_slow_time_canceller(clutter_only, order)[0]
            target_output = apply_slow_time_canceller(target_only, order)[0]
            self.assertEqual(len(mixed_output), pulse_count - order)
            self.assertTrue(all(abs(value) <= 1e-14 for value in clutter_output))
            self.assertLess(
                max(abs(mixed - moving) for mixed, moving in zip(mixed_output, target_output)),
                5e-15,
            )
            measured_gain = math.sqrt(
                sum(abs(value) ** 2 for value in target_output) / len(target_output)
            ) / target_amplitude
            self.assertAlmostEqual(measured_gain, expected_gain, places=12)
            self.assertGreater(measured_gain, 0.0)

    def test_frequency_periodicity_prf_sweep_and_noise_cost(self):
        wavelength_m = SPEED_OF_LIGHT_MPS / 10e9
        blind_speed = wavelength_m * 5e3 / 2.0
        for multiplier in (-2, -1, 0, 1, 2):
            two_gain, three_gain = canceller_response(multiplier * blind_speed)
            self.assertLess(two_gain, 2e-15)
            self.assertLess(three_gain, 4e-30)

        prfs = (3e3, 4e3, 5e3, 7e3, 9e3)
        gains = [canceller_response(12.0, prf_hz=prf) for prf in prfs]
        self.assertTrue(all(right[0] < left[0] for left, right in zip(gains, gains[1:])))
        self.assertTrue(all(right[1] < left[1] for left, right in zip(gains, gains[1:])))

        generator = random.Random(3801)
        noise = [[complex(generator.gauss(0, 1), generator.gauss(0, 1)) for _ in range(4096)]]
        input_power = sum(abs(value) ** 2 for value in noise[0]) / len(noise[0])
        measured_gains = []
        for order in (1, 2):
            output = apply_slow_time_canceller(noise, order)[0]
            power = sum(abs(value) ** 2 for value in output) / len(output)
            measured_gains.append(power / input_power)
        self.assertAlmostEqual(measured_gains[0], 2.0, delta=0.12)
        self.assertAlmostEqual(measured_gains[1], 6.0, delta=0.35)

    def test_wrong_axis_failure_recovery_and_isolation_contract(self):
        stationary = [[complex(row + 1, row / 3.0) for _ in range(12)] for row in range(5)]
        correct = apply_slow_time_canceller(stationary, 1)
        wrong_axis = [
            [stationary[row][pulse] - stationary[row - 1][pulse] for pulse in range(12)]
            for row in range(1, 5)
        ]
        self.assertTrue(all(value == 0 for row in correct for value in row))
        self.assertGreater(sum(abs(value) ** 2 for row in wrong_axis for value in row), 0)
        recovered = apply_slow_time_canceller(copy.deepcopy(stationary), 1)
        self.assertEqual(recovered, correct)
        self.assertEqual(self.source.count("RandStream('mt19937ar', 'Seed', random_seed)"), 2)
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P38'))", self.source)
        self.assertNotRegex(self.source, r"(?m)^\s*rng\s*\(")

    def test_source_is_transparent_bounded_and_resists_critical_mutations(self):
        self.assertEqual(source_contract_errors(self.source), [])
        lower = self.source.lower()
        for forbidden in (
            "phased.",
            "mtifilter",
            "designfilt",
            "filter(",
            "conv(",
            "parfor",
            "while true",
            "system(",
            "webread(",
            "fopen(",
        ):
            self.assertNotIn(forbidden, lower)
        for marker in (
            "velocity_sweep_mps",
            "prf_sweep_hz",
            "prf_sweep_target_velocity_mps ~= 0",
            "two_pulse_noise_power_gain_theory",
            "three_pulse_noise_power_gain_theory",
            "broken_clutter_residual_ratio",
            "estimated_stored_numeric_values <= max_stored_numeric_values",
        ):
            self.assertIn(marker, self.source)
        mutations = (
            self.source.replace("two_pulse_coefficients = [1 -1]", "two_pulse_coefficients = [1 1]", 1),
            self.source.replace("three_pulse_coefficients = [1 -2 1]", "three_pulse_coefficients = [1 -1 1]", 1),
            self.source.replace("data_matrix(:, 2:end)-data_matrix(:, 1:end-1)", "data_matrix(2:end, :)-data_matrix(1:end-1, :)", 1),
            self.source.replace("2*data_matrix(:, 2:end-1)+data_matrix(:, 1:end-2)", "data_matrix(:, 2:end-1)+data_matrix(:, 1:end-2)", 1),
            self.source.replace("broken_model_valid = false", "broken_model_valid = true", 1),
            self.source.replace("recovered_model_valid = true", "recovered_model_valid = false", 1),
        )
        for mutated in mutations:
            with self.subTest(mutation=len(mutated)):
                self.assertTrue(source_contract_errors(mutated))

    def test_lesson_walkthrough_and_checks_are_concept_first_and_complete(self):
        combined = "\n".join(self.docs.values())
        self.assertGreaterEqual(combined.count(QUESTION), 1)
        for marker in (
            "1 - exp(-j omega)",
            "[1, -2, 1]",
            "zero Doppler",
            "blind speed",
            "noise power gain",
            "velocity sweep",
            "PRF",
            "broken",
            "recovery",
            "Ctrl+C",
            "rollback",
            "private seed",
            "range rows",
            "slow time",
            "teach-back",
        ):
            self.assertIn(marker.lower(), combined.lower(), marker)
        for placeholder in ("TODO", "TBD", "lorem ipsum", "will be replaced"):
            self.assertNotIn(placeholder.lower(), combined.lower())
        self.assertNotRegex(combined, r"(?i)MATLAB (ran|passed|validated|executed successfully)")

    def test_catalogs_and_isolated_tutor_entry_with_timeout(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("Project 38", root_readme)
        self.assertIn("Project 38", start_here)
        self.assertRegex(module_index, r"\| \[P38\].*\| implemented \|")
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir()
            for entry in self.manifest["modules"]:
                destination = fixture / entry["folder"] / "README.md"
                destination.parent.mkdir(parents=True)
                shutil.copy2(ROOT / entry["folder"] / "README.md", destination)
            shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
            shutil.copy2(ROOT / "curriculum/modules.json", fixture / "curriculum/modules.json")
            result = subprocess.run(
                [str(fixture / "bin/learn"), "start", "38"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P38 — Implement a Two-Pulse and Three-Pulse MTI Canceller", result.stdout)
            self.assertIn("status: implemented", result.stdout)

            progress = fixture / ".learning/progress.json"
            prior_completed = [f"P{number:02d}" for number in range(1, 38)]
            progress.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P37",
                        "completed": prior_completed,
                        "notes": {"P37": "preserve this note"},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            default_result = subprocess.run(
                [str(fixture / "bin/learn"), "start"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            self.assertEqual(default_result.returncode, 0, default_result.stderr)
            self.assertIn("P38 — Implement a Two-Pulse and Three-Pulse MTI Canceller", default_result.stdout)
            state = json.loads(progress.read_text(encoding="utf-8"))
            self.assertEqual(state["completed"], prior_completed)
            self.assertEqual(state["notes"], {"P37": "preserve this note"})
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_retained_evidence_has_claim_boundary_commands_and_rollback(self):
        evidence = ROOT / "docs/evidence/P38-2026-08-03.md"
        self.assertTrue(evidence.is_file())
        text = evidence.read_text(encoding="utf-8")
        for heading in (
            "## Outcome and claim boundary",
            "## Governance, state, ownership, concurrency, and CI inspection",
            "## Acceptance mapping",
            "## Physical model and independent static oracle",
            "## Figure and metric inventory",
            "## Focused test coverage",
            "## Exact commands and results",
            "## Changed and preserved invariants",
            "## Rollback and recovery",
            "## Residual risks and unperformed validation",
        ):
            self.assertIn(heading, text)
        for command in (
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
        ):
            self.assertIn(command, text)
        for marker in (
            "Validation class",
            "Result: exit `0`",
            "MATLAB runtime status",
            "Toolboxes",
            "did not run",
            "static",
            "rollback",
            "P37",
        ):
            self.assertIn(marker.lower(), text.lower(), marker)
        self.assertNotRegex(text, r"(?i)MATLAB (ran|passed|validated|executed successfully)")
        data = evidence.read_bytes()
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
