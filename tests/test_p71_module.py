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
MODULE = ROOT / "modules/71-expose-fmcw-range-doppler-coupling"
EXPERIMENT = MODULE / "experiment.m"
QUESTION = "Why can target motion bias the range estimated from one chirp?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def manifest() -> dict:
    return json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))


def module_entry(data: dict, module_id: str) -> dict:
    matches = [entry for entry in data["modules"] if entry.get("id") == module_id]
    if len(matches) != 1:
        raise ValueError(f"expected one {module_id} entry, found {len(matches)}")
    return matches[0]


def artifact_errors(data: dict, root: Path) -> list[str]:
    errors: list[str] = []
    try:
        entry = module_entry(data, "P71")
    except (KeyError, TypeError, ValueError) as exc:
        return [str(exc)]
    expected = {
        "number": 71,
        "title": "Expose FMCW Range-Doppler Coupling",
        "guiding_question": QUESTION,
        "phase": 8,
        "phase_title": "FMCW, MIMO, and Micro-Doppler",
        "slug": "expose-fmcw-range-doppler-coupling",
        "folder": "modules/71-expose-fmcw-range-doppler-coupling",
        "status": "implemented",
        "implementation_batch": "P71",
    }
    for key, value in expected.items():
        if entry.get(key) != value:
            errors.append(f"P71 {key} drifted")
    folder = root / str(entry.get("folder", ""))
    for name in ARTIFACTS:
        path = folder / name
        if not path.is_file():
            errors.append(f"P71 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P71 empty {name}")
    return errors


def park_miller_uniform(seed: int, count: int) -> list[float]:
    if not isinstance(seed, int) or isinstance(seed, bool) or not 1 <= seed < 2147483647:
        raise ValueError("invalid seed")
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 20000:
        raise ValueError("invalid count")
    state = seed
    values: list[float] = []
    for _ in range(count):
        state = (16807 * state) % 2147483647
        values.append(state / 2147483647)
    return values


def private_complex_noise(seed: int, count: int) -> list[complex]:
    if 2 * count > 20000:
        raise ValueError("private generator request exceeds ceiling")
    values = park_miller_uniform(seed, 2 * count)
    return [
        math.sqrt(-2 * math.log(max(values[index], float.fromhex("0x1.0p-1022"))))
        * cmath.exp(1j * 2 * math.pi * values[count + index])
        / math.sqrt(2)
        for index in range(count)
    ]


def oracle(seed: int = 7101, velocity_mps: float = 20.0, bandwidth_hz: float = 20e6) -> dict:
    c_mps = 3e8
    carrier_hz = 77e9
    fs_hz = 80e6
    duration_s = 40e-6
    range_m = 45.0
    phase_rad = 0.35
    noise_rms = 0.002
    sample_count = round(fs_hz * duration_s)
    slope = bandwidth_hz / duration_s
    delay_s = 2 * range_m / c_mps
    wavelength_m = c_mps / carrier_hz
    doppler_hz = 2 * velocity_mps / wavelength_m
    delay_beat_hz = slope * delay_s
    ideal_beat_hz = delay_beat_hz - doppler_hz
    noise = private_complex_noise(seed, sample_count)
    valid: list[complex] = []
    for index in range(sample_count):
        time_s = index / fs_hz
        if time_s < delay_s:
            continue
        tx = cmath.exp(1j * math.pi * slope * (time_s - duration_s / 2) ** 2)
        rx = cmath.exp(
            1j
            * (
                math.pi * slope * (time_s - delay_s - duration_s / 2) ** 2
                + 2 * math.pi * doppler_hz * time_s
                + phase_rad
            )
        )
        valid.append(tx * rx.conjugate() + noise_rms * noise[index])
    lag_product = sum(valid[index].conjugate() * valid[index + 1] for index in range(len(valid) - 1))
    measured_beat_hz = cmath.phase(lag_product) * fs_hz / (2 * math.pi)
    naive_range_m = c_mps * measured_beat_hz / (2 * slope)
    corrected_range_m = c_mps * (measured_beat_hz + doppler_hz) / (2 * slope)
    wrong_range_m = c_mps * (measured_beat_hz - doppler_hz) / (2 * slope)
    return {
        "sample_count": sample_count,
        "valid_count": len(valid),
        "slope": slope,
        "delay_s": delay_s,
        "doppler_hz": doppler_hz,
        "delay_beat_hz": delay_beat_hz,
        "ideal_beat_hz": ideal_beat_hz,
        "measured_beat_hz": measured_beat_hz,
        "naive_range_m": naive_range_m,
        "corrected_range_m": corrected_range_m,
        "wrong_range_m": wrong_range_m,
    }


def validate_controls(values: dict) -> list[str]:
    errors: list[str] = []
    required = {
        "seed", "c", "fc", "fs", "duration", "bandwidth", "range", "velocity",
        "amplitude", "phase", "noise", "velocity_sweep", "bandwidth_sweep",
        "floor", "max_samples", "max_sweep", "max_private", "max_working", "max_figures",
    }
    if set(values) != required:
        return ["missing or unexpected controls"]
    scalar_names = required - {"velocity_sweep", "bandwidth_sweep"}
    for name in scalar_names:
        value = values[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"{name} must be finite numeric scalar")
    for name in ("velocity_sweep", "bandwidth_sweep"):
        value = values[name]
        if not isinstance(value, list) or not value or any(
            isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item)
            for item in value
        ):
            errors.append(f"{name} must be finite numeric vector")
    if errors:
        return errors
    sample_count = values["fs"] * values["duration"]
    if abs(sample_count - round(sample_count)) > 100 * math.ulp(round(sample_count)) or not 256 <= sample_count <= values["max_samples"]:
        errors.append("sample count invalid")
    if not 0 < values["bandwidth"] < values["fs"]:
        errors.append("baseline bandwidth invalid")
    if not 0 < values["range"] or not 0 < values["amplitude"] <= 2:
        errors.append("target controls invalid")
    if not 0 <= values["noise"] <= 0.2:
        errors.append("noise invalid")
    velocity_sweep = values["velocity_sweep"]
    if not 3 <= len(velocity_sweep) <= values["max_sweep"] or not all(
        left < right for left, right in zip(velocity_sweep, velocity_sweep[1:])
    ) or not min(velocity_sweep) < 0 < max(velocity_sweep) or 0 not in velocity_sweep:
        errors.append("velocity sweep invalid")
    bandwidth_sweep = values["bandwidth_sweep"]
    if not 3 <= len(bandwidth_sweep) <= values["max_sweep"] or not all(
        0 < left < right for left, right in zip(bandwidth_sweep, bandwidth_sweep[1:])
    ) or bandwidth_sweep[-1] >= values["fs"] or values["bandwidth"] not in bandwidth_sweep:
        errors.append("bandwidth sweep invalid")
    delay_s = 2 * values["range"] / values["c"]
    overlap_count = sum(
        index / values["fs"] >= delay_s for index in range(round(sample_count))
    )
    if not 0 < delay_s < values["duration"] or overlap_count < 2:
        errors.append("echo overlap invalid")
    wavelength = values["c"] / values["fc"]
    dopplers = [2 * item / wavelength for item in [values["velocity"], *velocity_sweep]]
    slopes = [item / values["duration"] for item in [values["bandwidth"], *bandwidth_sweep]]
    if any(abs(slope * delay_s - doppler) >= values["fs"] / 2 for slope in slopes for doppler in dopplers):
        errors.append("signed beat violates Nyquist")
    ceilings = (values["max_samples"], values["max_sweep"], values["max_private"], values["max_working"], values["max_figures"])
    if ceilings != (5000, 7, 20000, 250000, 6):
        errors.append("resource ceilings drifted")
    if 2 * round(sample_count) > values["max_private"]:
        errors.append("private request exceeds ceiling")
    return errors


BASE_CONTROLS = {
    "seed": 7101,
    "c": 3e8,
    "fc": 77e9,
    "fs": 80e6,
    "duration": 40e-6,
    "bandwidth": 20e6,
    "range": 45.0,
    "velocity": 20.0,
    "amplitude": 1.0,
    "phase": 0.35,
    "noise": 0.002,
    "velocity_sweep": [-30, -15, 0, 15, 30],
    "bandwidth_sweep": [10e6, 15e6, 20e6, 25e6, 30e6],
    "floor": -80,
    "max_samples": 5000,
    "max_sweep": 7,
    "max_private": 20000,
    "max_working": 250000,
    "max_figures": 6,
}


class P71ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = manifest()
        cls.source = EXPERIMENT.read_text(encoding="utf-8")
        cls.documents = {
            name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        }

    def run_cli(self, *args: str, data: dict | None = None, initial_state: dict | None = None):
        with tempfile.TemporaryDirectory() as temp_directory:
            fixture = Path(temp_directory) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
            fixture_data = copy.deepcopy(data if data is not None else self.data)
            (fixture / "curriculum/modules.json").write_text(
                json.dumps(fixture_data, indent=2) + "\n", encoding="utf-8"
            )
            for entry in fixture_data["modules"]:
                destination = fixture / entry["folder"] / "README.md"
                destination.parent.mkdir(parents=True)
                source = ROOT / entry["folder"] / "README.md"
                destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            if initial_state is not None:
                state_path = fixture / ".learning/progress.json"
                state_path.parent.mkdir(parents=True)
                state_path.write_text(json.dumps(initial_state) + "\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["HOME"] = temp_directory
            return subprocess.run(
                [str(fixture / "bin/learn"), *args], cwd=fixture, env=environment,
                text=True, capture_output=True, timeout=10
            )

    def test_artifacts_identity_and_prerequisite_are_permanent(self):
        self.assertEqual(artifact_errors(self.data, ROOT), [])
        self.assertEqual(module_entry(self.data, "P70")["status"], "implemented")
        p72 = module_entry(self.data, "P72")
        self.assertEqual(p72["number"], 72)
        self.assertEqual(p72["implementation_batch"], "P72")
        for name, text in self.documents.items():
            self.assertIn(QUESTION, text, name)

    def test_artifact_validation_rejects_malformed_identity_and_files(self):
        for mutation in ("duplicate", "identity", "status", "missing", "empty"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp_directory:
                fixture = Path(temp_directory)
                shutil.copytree(MODULE, fixture / MODULE.relative_to(ROOT))
                data = copy.deepcopy(self.data)
                entry = module_entry(data, "P71")
                if mutation == "duplicate":
                    data["modules"].append(copy.deepcopy(entry))
                elif mutation == "identity":
                    entry["guiding_question"] = "drifted"
                elif mutation == "status":
                    entry["status"] = "scaffolded"
                elif mutation == "missing":
                    (fixture / entry["folder"] / "checks.md").unlink()
                else:
                    (fixture / entry["folder"] / "lesson.md").write_text("", encoding="utf-8")
                self.assertTrue(artifact_errors(data, fixture))

    def test_experiment_exposes_equations_stages_sweeps_failure_and_recovery(self):
        required = (
            "baseline_seed = 7101", "tx.*conj(rx)", "f_beat = S*tau - f_d",
            "transmit_chirp = exp", "received_echo", "dechirped_beat",
            "estimate_signed_tone_frequency", "signed_frequency_axis_hz",
            "velocity_sweep_mps", "bandwidth_sweep_hz", "Sweep 1", "Sweep 2",
            "wrong_sign_range_estimate_m", "recovered_range_estimate_m",
            "independently supplied", "same-measurement recovery", "p71_results",
            "xlabel(", "ylabel(", "maximum_working_numeric_values", "validate_controls",
            "overlap_count_local >= 2",
        )
        for marker in required:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P71"), 6)
        self.assertEqual(self.source.count("chirp_bandwidth_hz, ...\n        baseline_seed);"), 1)
        self.assertEqual(self.source.count("bandwidth_sweep_hz(case_index), ...\n        baseline_seed);"), 1)
        forbidden = ("phased.", "rdcoupling", "beat2range", "dechirp(", "rng(", "clear all", "close all", "parfor", "timer(", "webread", "urlread", "fopen(", "system(", "TODO")
        lowered = self.source.lower()
        for marker in forbidden:
            self.assertNotIn(marker.lower(), lowered)

    def test_visible_controls_match_reviewed_oracle_contract(self):
        assignments = {
            "seed": r"baseline_seed = 7101;",
            "c": r"speed_of_light_mps = 3\.0e8;",
            "fc": r"carrier_frequency_hz = 77\.0e9;",
            "fs": r"sample_rate_hz = 80\.0e6;",
            "duration": r"chirp_duration_s = 40\.0e-6;",
            "bandwidth": r"chirp_bandwidth_hz = 20\.0e6;",
            "range": r"target_range_m = 45\.0;",
            "velocity": r"target_velocity_mps = 20\.0;",
            "amplitude": r"target_voltage = 1\.0;",
            "phase": r"target_initial_phase_rad = 0\.35;",
            "noise": r"noise_rms = 0\.002;",
            "velocity_sweep": r"velocity_sweep_mps = \[-30 -15 0 15 30\];",
            "bandwidth_sweep": r"bandwidth_sweep_hz = \[10 15 20 25 30\]\*1\.0e6;",
            "floor": r"plot_floor_db = -80;",
            "ceilings": r"maximum_samples = 5000;[\s\S]*maximum_sweep_cases = 7;[\s\S]*maximum_private_values = 20000;[\s\S]*maximum_working_numeric_values = 250000;[\s\S]*maximum_figures = 6;",
        }
        for name, pattern in assignments.items():
            self.assertRegex(self.source, pattern, name)
        self.assertEqual(validate_controls(copy.deepcopy(BASE_CONTROLS)), [])

    def test_control_validation_rejects_negative_malformed_nonfinite_and_bounds(self):
        mutations = {
            "missing": lambda value: value.pop("range"),
            "malformed": lambda value: value.__setitem__("velocity_sweep", "fast"),
            "nonfinite": lambda value: value.__setitem__("velocity", math.inf),
            "negative bandwidth": lambda value: value.__setitem__("bandwidth", -1),
            "no overlap": lambda value: value.__setitem__("range", 7000),
            "unordered velocity": lambda value: value.__setitem__("velocity_sweep", [-30, 0, -1, 30]),
            "missing zero": lambda value: value.__setitem__("velocity_sweep", [-30, -15, 15, 30]),
            "duplicate bandwidth": lambda value: value.__setitem__("bandwidth_sweep", [10e6, 20e6, 20e6]),
            "Nyquist": lambda value: value.__setitem__("velocity_sweep", [-1e6, 0, 1e6]),
            "sample bound": lambda value: value.__setitem__("duration", 100e-6),
            "ceiling drift": lambda value: value.__setitem__("max_figures", 60),
            "private bound": lambda value: value.__setitem__("max_private", 100),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                values = copy.deepcopy(BASE_CONTROLS)
                mutate(values)
                self.assertTrue(validate_controls(values))

    def test_control_validation_rejects_one_sample_overlap_before_processing(self):
        values = copy.deepcopy(BASE_CONTROLS)
        values["range"] = 5997.0
        sample_count = round(values["fs"] * values["duration"])
        delay_s = 2 * values["range"] / values["c"]
        overlap_count = sum(
            index / values["fs"] >= delay_s for index in range(sample_count)
        )
        self.assertEqual(overlap_count, 1)
        self.assertEqual(validate_controls(values), ["echo overlap invalid"])

    def test_private_generator_is_repeatable_isolated_and_bounded(self):
        first = private_complex_noise(7101, 3200)
        second = private_complex_noise(7101, 3200)
        companion = private_complex_noise(7102, 3200)
        self.assertEqual(first, second)
        self.assertNotEqual(first[:8], companion[:8])
        self.assertAlmostEqual(first[0].real, -1.198917346488484, places=12)
        self.assertAlmostEqual(first[0].imag, -1.2052460950872212, places=12)
        with self.assertRaises(ValueError):
            private_complex_noise(7101, 10001)
        with self.assertRaises(ValueError):
            park_miller_uniform(0, 2)

    def test_full_signal_oracle_preserves_signed_baseline_and_recovery(self):
        result = oracle()
        self.assertEqual(result["sample_count"], 3200)
        self.assertEqual(result["valid_count"], 3176)
        self.assertAlmostEqual(result["delay_s"], 0.3e-6, places=15)
        self.assertAlmostEqual(result["delay_beat_hz"], 150000.0, places=8)
        self.assertAlmostEqual(result["doppler_hz"], 10266.666666666666, places=8)
        self.assertAlmostEqual(result["ideal_beat_hz"], 139733.3333333333, places=8)
        self.assertAlmostEqual(result["measured_beat_hz"], 139738.25831608725, places=6)
        self.assertAlmostEqual(result["naive_range_m"], 41.92147749482618, places=9)
        self.assertAlmostEqual(result["corrected_range_m"], 45.001477494826176, places=9)
        self.assertAlmostEqual(result["wrong_range_m"], 38.84147749482618, places=9)

    def test_velocity_and_slope_sweep_laws_cover_both_signs_and_zero(self):
        fc = 77e9
        slope = 20e6 / 40e-6
        velocities = [-30, -15, 0, 15, 30]
        biases = [-fc * velocity / slope for velocity in velocities]
        self.assertEqual(biases, [4.620000000000001, 2.3100000000000005, -0.0, -2.3100000000000005, -4.620000000000001])
        expected = [-6.16, -4.106666666666667, -3.08, -2.464, -2.0533333333333337]
        for bandwidth_mhz, expected_bias in zip([10, 15, 20, 25, 30], expected):
            result = oracle(seed=7201 + bandwidth_mhz, bandwidth_hz=bandwidth_mhz * 1e6)
            ideal_bias = -fc * 20 / result["slope"]
            self.assertAlmostEqual(ideal_bias, expected_bias, places=12)
            self.assertLess(abs(result["naive_range_m"] - 45 - ideal_bias), 0.2)

    def test_wrong_sign_is_broken_and_recovery_uses_same_measurement(self):
        result = oracle()
        measured = result["measured_beat_hz"]
        correct_bias = result["corrected_range_m"] - 45
        wrong_bias = result["wrong_range_m"] - 45
        self.assertLess(abs(correct_bias), 0.08)
        self.assertAlmostEqual(wrong_bias, -6.158522505173821, places=9)
        self.assertEqual(measured, result["measured_beat_hz"])
        self.assertIn("unchanged measurement", self.documents["walkthrough.md"])
        self.assertIn("independently supplied", self.documents["walkthrough.md"])

    def test_documents_are_concept_first_and_cover_limits_and_checks(self):
        combined = "\n".join(self.documents.values()).lower()
        for marker in (
            "one beat", "two unknown", "approaching", "receding", "signed",
            "velocity sweep", "chirp-slope sweep", "wrong correction sign",
            "zero-padding", "nyquist", "overlap", "range migration", "p72",
            "cancellation", "rollback", "teach-back", "no optional toolbox",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(self.documents["checks.md"].count("**Correct:**"), 32)
        lesson_prefix = self.documents["lesson.md"][:500].lower()
        self.assertNotIn("for loop", lesson_prefix)
        self.assertNotIn("matlab syntax", lesson_prefix)

    def test_cli_selection_timeout_advancement_rollback_and_isolation(self):
        state_path = ROOT / ".learning/progress.json"
        before = state_path.read_bytes() if state_path.exists() else None
        start = self.run_cli("start", "71")
        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertIn("P71 — Expose FMCW Range-Doppler Coupling", start.stdout)
        self.assertIn("status: implemented", start.stdout)
        completed = [f"P{number:02d}" for number in range(1, 71)]
        advance = self.run_cli(
            "start",
            initial_state={"schema_version": 1, "current": "P70", "completed": completed, "notes": {}},
        )
        self.assertEqual(advance.returncode, 0, advance.stderr)
        self.assertIn("P71 — Expose FMCW Range-Doppler Coupling", advance.stdout)
        rolled_back = copy.deepcopy(self.data)
        module_entry(rolled_back, "P71")["status"] = "scaffolded"
        refused = self.run_cli("complete", "71", data=rolled_back)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("Cannot complete P71", refused.stderr)
        recovered = self.run_cli("start", "71")
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = state_path.read_bytes() if state_path.exists() else None
        self.assertEqual(after, before)

    def test_compatibility_resources_side_effects_and_eof_policy(self):
        self.assertIn("MATLAB R2016b or newer", self.documents["README.md"])
        self.assertIn("Base MATLAB only", self.source)
        self.assertIn("preflight_working_value_bound", self.source)
        self.assertIn("working_value_count", self.source)
        self.assertIn("maximum_figures = 6", self.source)
        for name in ARTIFACTS:
            data = (MODULE / name).read_bytes()
            self.assertTrue(data.endswith(b"\n"), name)
            self.assertFalse(data.endswith(b"\n\n"), name)
        for path in (ROOT / "README.md", ROOT / "START_HERE.md", ROOT / "modules/README.md", ROOT / "curriculum/modules.json"):
            data = path.read_bytes()
            self.assertTrue(data.endswith(b"\n"), path.name)
            self.assertFalse(data.endswith(b"\n\n"), path.name)

    def test_public_catalogs_and_retained_evidence_integrate_without_freezing_future(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 71 restores within-chirp Doppler", root_readme)
        self.assertIn("Project 71 follows P70", start_here)
        self.assertRegex(module_index, r"\| \[P71\].*\| implemented \| 8 \|")
        evidence_files = sorted((ROOT / "docs/evidence").glob("P71-*.md"))
        self.assertEqual(len(evidence_files), 1)
        evidence = evidence_files[0].read_text(encoding="utf-8")
        for heading in ("## Claim boundary", "## Acceptance map", "## Exact commands and results", "## Changed and preserved invariants", "## Residual risks", "## Rollback", "## Unperformed validation"):
            self.assertIn(heading, evidence)


if __name__ == "__main__":
    unittest.main()
