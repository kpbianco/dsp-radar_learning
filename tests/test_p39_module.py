from __future__ import annotations

import cmath
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
MODULE = ROOT / "modules/39-expose-blind-speeds-and-use-staggered-prf"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Why can a moving target vanish in an MTI radar?"
SPEED_OF_LIGHT_MPS = 299_792_458.0
MAX_PULSE_COUNT = 128
MAX_RESPONSE_SAMPLES = 3001
MAX_SWEEP_CASES = 9
EXPECTED_IDENTITY = {
    "number": 39,
    "id": "P39",
    "title": "Expose Blind Speeds and Use Staggered PRF",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "expose-blind-speeds-and-use-staggered-prf",
    "folder": "modules/39-expose-blind-speeds-and-use-staggered-prf",
    "status": "implemented",
    "implementation_batch": "P39",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p39_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P39 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P39 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P39"]
    if len(matches) != 1:
        return errors + [f"expected one P39 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P39 {key} must be {expected!r}")
    return errors


def validate_controls(
    *,
    carrier_hz: object = 10e9,
    primary_prf_hz: object = 4e3,
    secondary_prf_hz: object = 5.3e3,
    pulse_count: object = 32,
    noise_rms: object = 0.02,
    threshold: object = 0.30,
    velocity_limit_mps: object = 150.0,
    response_count: object = 2401,
    secondary_prf_sweep_hz: object = (4e3, 4.2e3, 4.5e3, 4.9e3, 5.3e3, 5.7e3, 6.2e3),
) -> None:
    for value, label in (
        (carrier_hz, "carrier"),
        (primary_prf_hz, "primary PRF"),
        (secondary_prf_hz, "secondary PRF"),
        (velocity_limit_mps, "velocity limit"),
    ):
        if not finite_real(value) or value <= 0:
            raise ValueError(f"{label} must be finite and positive")
    if primary_prf_hz == secondary_prf_hz:
        raise ValueError("baseline PRFs must differ")
    if (
        not isinstance(pulse_count, int)
        or isinstance(pulse_count, bool)
        or not 8 <= pulse_count <= MAX_PULSE_COUNT
    ):
        raise ValueError("pulse count must be a bounded integer")
    if not finite_real(noise_rms) or noise_rms < 0:
        raise ValueError("noise RMS must be finite and nonnegative")
    if not finite_real(threshold) or not 0 < threshold < 1:
        raise ValueError("threshold must lie strictly between zero and one")
    if (
        not isinstance(response_count, int)
        or isinstance(response_count, bool)
        or not 101 <= response_count <= MAX_RESPONSE_SAMPLES
        or response_count % 2 == 0
    ):
        raise ValueError("response count must be a bounded odd integer")
    if (
        not isinstance(secondary_prf_sweep_hz, (list, tuple))
        or not 3 <= len(secondary_prf_sweep_hz) <= MAX_SWEEP_CASES
    ):
        raise ValueError("second-PRF sweep must have a bounded case count")
    if not all(finite_real(value) and value > 0 for value in secondary_prf_sweep_hz):
        raise ValueError("second-PRF sweep must be finite and positive")
    if any(right <= left for left, right in zip(secondary_prf_sweep_hz, secondary_prf_sweep_hz[1:])):
        raise ValueError("second-PRF sweep must increase strictly")
    if primary_prf_hz not in secondary_prf_sweep_hz:
        raise ValueError("second-PRF sweep must include the broken same-PRF case")
    if secondary_prf_hz not in secondary_prf_sweep_hz:
        raise ValueError("second-PRF sweep must include the recovered baseline")


def blind_speed_spacing(*, carrier_hz: float, prf_hz: float) -> float:
    wavelength_m = SPEED_OF_LIGHT_MPS / carrier_hz
    return wavelength_m * prf_hz / 2.0


def normalized_two_pulse_gain(
    velocity_mps: float, *, carrier_hz: float = 10e9, prf_hz: float
) -> float:
    wavelength_m = SPEED_OF_LIGHT_MPS / carrier_hz
    doppler_hz = 2.0 * velocity_mps / wavelength_m
    phase_increment_rad = 2.0 * math.pi * doppler_hz / prf_hz
    return abs(1.0 - cmath.exp(-1j * phase_increment_rad)) / 2.0


def apply_two_pulse_canceller(sequence: list[complex]) -> list[complex]:
    if not isinstance(sequence, list) or len(sequence) < 2:
        raise ValueError("sequence must contain at least two pulse samples")
    if not all(isinstance(value, (int, float, complex)) and not isinstance(value, bool) for value in sequence):
        raise ValueError("pulse samples must be numeric")
    return [sequence[index] - sequence[index - 1] for index in range(1, len(sequence))]


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", re.sub(r"\.\.\.\s*", "", source))
    required = (
        "random_seed = 3901",
        "RandStream('mt19937ar', 'Seed', random_seed)",
        "primary_clean_sequence(2:end)-primary_clean_sequence(1:end-1)",
        "secondary_clean_sequence(2:end)-secondary_clean_sequence(1:end-1)",
        "primary_blind_speed_spacing_mps = wavelength_m*primary_prf_hz/2",
        "secondary_blind_speed_spacing_mps = wavelength_m*secondary_prf_hz/2",
        "secondary_phase_axis_rad = 2*pi*doppler_axis_hz/secondary_prf_hz",
        "primary_response = abs(1-exp(-1j*primary_phase_axis_rad))",
        "secondary_response = abs(1-exp(-1j*secondary_phase_axis_rad))",
        "primary_response_normalized = primary_response/2",
        "secondary_response_normalized = secondary_response/2",
        "combined_response_normalized = max(primary_response_normalized, secondary_response_normalized)",
        "combined_detection = primary_detection | secondary_detection",
        "secondary_prf_sweep_hz = [4.0e3 4.2e3 4.5e3 4.9e3 5.3e3 5.7e3 6.2e3]",
        "broken_secondary_prf_hz = primary_prf_hz",
        "broken_model_valid = false",
        "recovered_model_valid = true",
        "assert(max_pulse_count == 128)",
        "assert(max_response_samples == 3001)",
        "assert(max_sweep_cases == 9)",
        "assert(max_figure_groups == 5)",
        "max_stored_numeric_values = 100000",
        "assert(max_stored_numeric_values == 100000)",
    )
    return [marker for marker in required if marker not in compact]


class P39ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.docs = {
            name: (MODULE / name).read_text(encoding="utf-8")
            for name in ("README.md", "lesson.md", "walkthrough.md", "checks.md")
        }

    def test_identity_artifacts_and_prerequisite_are_permanent(self):
        self.assertEqual(validate_p39_contract(MODULE, self.manifest), [])
        entries = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(entries["P38"]["status"], "implemented")
        self.assertEqual(entries["P39"], EXPECTED_IDENTITY)
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
            self.assertIn("P39 missing checks.md", validate_p39_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("", encoding="utf-8")
            self.assertIn("P39 empty checks.md", validate_p39_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p39_contract(MODULE, []))
        malformed = {"modules": [None]}
        self.assertIn("manifest module entries must be objects", validate_p39_contract(MODULE, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P39 manifest entry, found 2", validate_p39_contract(MODULE, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(item for item in drifted["modules"] if item["id"] == "P39")["guiding_question"] = "Changed"
        self.assertTrue(any("guiding_question" in error for error in validate_p39_contract(MODULE, drifted)))

    def test_control_validation_rejects_malformed_and_resource_overruns(self):
        validate_controls()
        invalid_cases = (
            {"carrier_hz": math.inf},
            {"primary_prf_hz": 0},
            {"secondary_prf_hz": 4e3},
            {"pulse_count": True},
            {"pulse_count": 7},
            {"pulse_count": 129},
            {"noise_rms": -0.01},
            {"noise_rms": math.nan},
            {"threshold": 0},
            {"threshold": 1},
            {"velocity_limit_mps": -1},
            {"response_count": 100},
            {"response_count": 2400},
            {"response_count": 3003},
            {"secondary_prf_sweep_hz": (4e3, 4e3, 5.3e3)},
            {"secondary_prf_sweep_hz": (4e3, math.nan, 5.3e3)},
            {"secondary_prf_sweep_hz": tuple(4e3 + 100 * index for index in range(10))},
            {"secondary_prf_sweep_hz": (4.2e3, 4.5e3, 5.3e3)},
            {"secondary_prf_sweep_hz": (4e3, 4.5e3, 5e3)},
        )
        for controls in invalid_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_blind_speed_equation_and_staggered_recovery_are_numerically_correct(self):
        primary_spacing = blind_speed_spacing(carrier_hz=10e9, prf_hz=4e3)
        secondary_spacing = blind_speed_spacing(carrier_hz=10e9, prf_hz=5.3e3)
        self.assertAlmostEqual(primary_spacing, 59.9584916, places=7)
        self.assertAlmostEqual(secondary_spacing, 79.44500137, places=7)
        for order in range(-2, 3):
            self.assertLessEqual(
                normalized_two_pulse_gain(order * primary_spacing, prf_hz=4e3),
                1e-12,
            )
            self.assertLessEqual(
                normalized_two_pulse_gain(order * secondary_spacing, prf_hz=5.3e3),
                1e-12,
            )
        self.assertGreater(normalized_two_pulse_gain(primary_spacing, prf_hz=5.3e3), 0.30)
        self.assertGreater(normalized_two_pulse_gain(secondary_spacing, prf_hz=4e3), 0.30)
        self.assertEqual(normalized_two_pulse_gain(0.0, prf_hz=4e3), 0.0)
        self.assertEqual(normalized_two_pulse_gain(0.0, prf_hz=5.3e3), 0.0)

    def test_explicit_canceller_nulls_repeating_samples_and_passes_staggered_samples(self):
        pulse_count = 32
        primary_spacing = blind_speed_spacing(carrier_hz=10e9, prf_hz=4e3)
        wavelength_m = SPEED_OF_LIGHT_MPS / 10e9
        doppler_hz = 2.0 * primary_spacing / wavelength_m
        primary = [cmath.exp(1j * 2.0 * math.pi * doppler_hz * pulse / 4e3) for pulse in range(pulse_count)]
        secondary = [cmath.exp(1j * 2.0 * math.pi * doppler_hz * pulse / 5.3e3) for pulse in range(pulse_count)]
        primary_output = apply_two_pulse_canceller(primary)
        secondary_output = apply_two_pulse_canceller(secondary)
        self.assertLess(max(abs(value) for value in primary_output), 1e-12)
        measured_secondary = math.sqrt(sum(abs(value) ** 2 for value in secondary_output) / len(secondary_output)) / 2.0
        self.assertAlmostEqual(measured_secondary, normalized_two_pulse_gain(primary_spacing, prf_hz=5.3e3), places=12)
        with self.assertRaises(ValueError):
            apply_two_pulse_canceller([])
        with self.assertRaises(ValueError):
            apply_two_pulse_canceller([1, True])

    def test_second_prf_sweep_contains_broken_case_and_recovery(self):
        primary_spacing = blind_speed_spacing(carrier_hz=10e9, prf_hz=4e3)
        sweep = (4e3, 4.2e3, 4.5e3, 4.9e3, 5.3e3, 5.7e3, 6.2e3)
        gains = [normalized_two_pulse_gain(primary_spacing, prf_hz=value) for value in sweep]
        self.assertLessEqual(gains[0], 1e-12)
        self.assertGreater(gains[sweep.index(5.3e3)], 0.30)
        self.assertGreater(max(gains[1:]), gains[0])

    def test_documented_carrier_edit_keeps_both_first_blind_markers_visible(self):
        edited_carrier_hz = 8e9
        primary = blind_speed_spacing(carrier_hz=edited_carrier_hz, prf_hz=4e3)
        secondary = blind_speed_spacing(carrier_hz=edited_carrier_hz, prf_hz=5.3e3)
        self.assertAlmostEqual(primary / blind_speed_spacing(carrier_hz=10e9, prf_hz=4e3), 1.25)
        self.assertAlmostEqual(secondary / blind_speed_spacing(carrier_hz=10e9, prf_hz=5.3e3), 1.25)
        self.assertLess(primary, 150.0)
        self.assertLess(secondary, 150.0)
        self.assertIn("carrier_frequency_hz` to `8e9", self.docs["walkthrough.md"])

    def test_source_is_deterministic_bounded_transparent_and_base_matlab(self):
        self.assertEqual(source_contract_errors(self.source), [])
        self.assertGreaterEqual(self.source.count("figure('Name'"), 5)
        for label in (
            "Radial velocity (m/s)",
            "Second PRF (kHz)",
            "Normalized two-pulse gain",
            "target Doppler",
        ):
            self.assertIn(label, self.source)
        for opaque_or_toolbox_marker in (
            "phased.",
            "dsp.",
            "filter(",
            "freqz(",
            "designfilt(",
            "awgn(",
            "rng(",
            "system(",
            "webread(",
            "fopen(",
            "parfor",
            "while true",
        ):
            self.assertNotIn(opaque_or_toolbox_marker, self.source)
        self.assertIn("private_stream", self.source)
        self.assertIn("estimated_stored_numeric_values", self.source)
        mutations = (
            self.source.replace(
                "secondary_phase_axis_rad = 2*pi*doppler_axis_hz/secondary_prf_hz",
                "secondary_phase_axis_rad = 2*pi*doppler_axis_hz/primary_prf_hz",
                1,
            ),
            self.source.replace("secondary_response = abs(1-exp(-1j*secondary_phase_axis_rad))", "secondary_response = primary_response", 1),
            self.source.replace("secondary_response_normalized = secondary_response/2", "secondary_response_normalized = secondary_response", 1),
            self.source.replace("combined_detection = primary_detection | secondary_detection", "combined_detection = primary_detection", 1),
            self.source.replace("assert(max_response_samples == 3001)", "assert(max_response_samples > 0)", 1),
        )
        for mutated in mutations:
            with self.subTest(mutation=len(mutated)):
                self.assertTrue(source_contract_errors(mutated))

    def test_catalogs_and_isolated_tutor_entry_have_a_timeout(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("Project 39", root_readme)
        self.assertIn("Project 39", start_here)
        self.assertRegex(module_index, r"\| \[P39\].*\| implemented \|")
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
                [str(fixture / "bin/learn"), "start", "39"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P39 — Expose Blind Speeds and Use Staggered PRF", result.stdout)
            self.assertIn("status: implemented", result.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_default_tutor_entry_advances_from_completed_p38_without_state_loss(self):
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

            prior_completed = [f"P{number:02d}" for number in range(1, 39)]
            progress = fixture / ".learning/progress.json"
            progress.parent.mkdir()
            progress.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P38",
                        "completed": prior_completed,
                        "notes": {"P38": "preserve this note"},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [str(fixture / "bin/learn"), "start"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P39 — Expose Blind Speeds and Use Staggered PRF", result.stdout)
            self.assertIn("status: implemented", result.stdout)
            state = json.loads(progress.read_text(encoding="utf-8"))
            self.assertEqual(state["current"], "P39")
            self.assertEqual(state["completed"], prior_completed)
            self.assertEqual(state["notes"], {"P38": "preserve this note"})

    def test_docs_cover_baseline_two_sweeps_broken_recovery_limits_and_teach_back(self):
        for name, text in self.docs.items():
            self.assertIn(QUESTION, text, name)
            self.assertNotIn("TODO", text, name)
            self.assertNotIn("placeholder", text.lower(), name)
        self.assertIn("## AI chat prompt", self.docs["README.md"])
        walkthrough = self.docs["walkthrough.md"]
        for marker in (
            "Baseline",
            "Sweep 1",
            "Sweep 2",
            "Intentionally broken case",
            "Recovery",
            "Expected observation",
            "Common mistake",
        ):
            self.assertIn(marker, walkthrough)
        lesson = self.docs["lesson.md"]
        for marker in (
            "v_k=k\\frac{\\lambda f_r}{2}",
            "Limiting cases",
            "zero-velocity notch",
            "noncoherent",
            "range ambiguity",
        ):
            self.assertIn(marker, lesson)
        checks = self.docs["checks.md"]
        for marker in ("Observation checks", "Interpretation checks", "Prediction checks", "teach-back rubric"):
            self.assertIn(marker, checks)
        combined = "\n".join(self.docs.values())
        for marker in ("Ctrl+C", "rollback", "private seed", "bounded"):
            self.assertIn(marker.lower(), combined.lower())

    def test_manifest_rollback_fixture_is_isolated_from_neighboring_module_identity(self):
        rolled_back = copy.deepcopy(self.manifest)
        entries_before = {entry["id"]: copy.deepcopy(entry) for entry in rolled_back["modules"] if entry["id"] in {"P38", "P40"}}
        next(entry for entry in rolled_back["modules"] if entry["id"] == "P39")["status"] = "scaffolded"
        entries_after = {entry["id"]: entry for entry in rolled_back["modules"] if entry["id"] in {"P38", "P40"}}
        self.assertEqual(entries_after, entries_before)
        self.assertTrue(any("status" in error for error in validate_p39_contract(MODULE, rolled_back)))

    def test_retained_evidence_has_claim_boundary_commands_and_rollback(self):
        evidence = ROOT / "docs/evidence/P39-2026-08-03.md"
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
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -q",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
        ):
            self.assertIn(command, text)
        for marker in (
            "Validation class",
            "MATLAB and Octave did not run",
            "static",
            "rollback",
            "P38",
            "P39",
            "unperformed validation",
        ):
            self.assertIn(marker.lower(), text.lower(), marker)
        self.assertNotRegex(text, r"(?i)MATLAB (ran|passed|validated|executed successfully)")
        data = evidence.read_bytes()
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
