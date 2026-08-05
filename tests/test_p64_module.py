from __future__ import annotations

import cmath
import copy
import json
import math
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/64-build-an-amplitude-comparison-monopulse-experiment"
QUESTION = "How can sum and difference beams estimate small angle error around boresight?"
EXPECTED_IDENTITY = {
    "number": 64,
    "id": "P64",
    "title": "Build an Amplitude-Comparison Monopulse Experiment",
    "guiding_question": QUESTION,
    "phase": 7,
    "phase_title": "Arrays, Beamforming, DOA, and STAP",
    "slug": "build-an-amplitude-comparison-monopulse-experiment",
    "folder": "modules/64-build-an-amplitude-comparison-monopulse-experiment",
    "status": "implemented",
    "implementation_batch": "P64",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
SOURCE_MARKERS = (
    "baseline_seed = 6401;",
    "number_elements = 12;",
    "element_spacing_wavelengths = 0.5;",
    "beam_squint_deg = 3.0;",
    "target_angle_deg = 2.0;",
    "receiver_snr_db = 15.0;",
    "number_snapshots = 256;",
    "pattern_angles_deg = -10:0.05:10;",
    "calibration_limit_deg = 4.0;",
    "sum_guard = 0.15;",
    "squint_sweep_deg = [1.5 3.0 5.0];",
    "snr_sweep_db = [-5 5 15 25];",
    "broken_right_gain = 1.12;",
    "steering = exp(1j*2*pi*element_spacing_wavelengths*element_index* ...",
    "left_weight = left_steering/number_elements;",
    "right_weight = right_steering/number_elements;",
    "left_phase_correction = exp(-1j*angle(left_boresight_voltage));",
    "right_phase_correction = exp(-1j*angle(right_boresight_voltage));",
    "sum_pattern = (right_pattern+left_pattern)/2;",
    "difference_pattern = (right_pattern-left_pattern)/2;",
    "normalized_ratio = real(difference_pattern./sum_pattern);",
    "assert(all(diff(calibration_ratio) > 0), 'P64:CalibrationMonotonic', ...",
    "baseline_sensor_data = target_steering*target_voltage+ ...",
    "baseline_left = (left_weight'*baseline_sensor_data)*left_phase_correction;",
    "baseline_right = (right_weight'*baseline_sensor_data)*right_phase_correction;",
    "baseline_sum = (baseline_right+baseline_left)/2;",
    "baseline_difference = (baseline_right-baseline_left)/2;",
    "baseline_ratio_samples = real(baseline_difference./baseline_sum);",
    "baseline_valid_samples = abs(baseline_sum) >= sum_guard;",
    "baseline_ratio_mean = real(mean(baseline_difference)/mean(baseline_sum));",
    "squint_slopes_per_deg",
    "assert(all(diff(squint_boresight_sum) < 0), 'P64:SquintSumSweep', ...",
    "shared_noise = private_complex_noise(baseline_seed+1, maximum_elements, ...",
    "assert(all(diff(snr_sweep_rmse_deg) < 0), 'P64:SNRSweep', ...",
    "broken_right = broken_right_gain*ideal_right;",
    "broken_ratio = real(broken_difference/broken_sum);",
    "recovered_right = broken_right/broken_right_gain;",
    "assert(max(abs(recovered_ratio_curve-normalized_ratio)) < ...",
    "flat_estimates(sample_index) = calibration_angles_deg(lower_index)+ ...",
    "samples = sqrt(-2*log(first)).*exp(1j*2*pi*second)/sqrt(2);",
    "noise = reshape(samples, number_rows, number_columns);",
    "maximum_angle_samples = 1001;",
    "maximum_working_numeric_values = 500000;",
    "maximum_figures = 5;",
    "validate_controls(controls);",
    "p64_results = struct( ...",
    "close(findall(0, 'Type', 'figure', 'Tag', 'P64'));",
)
FORBIDDEN_SOURCE_TOKENS = (
    "phased.",
    "monopulseEstimator(",
    "steervec(",
    "collectPlaneWave(",
    "awgn(",
    "interp1(",
    "polyfit(",
    "rng(",
    "rand(",
    "randn(",
    "parfor",
    "timer(",
    "webread",
    "urlread",
    "system(",
    "fopen(",
    "save(",
    "close all",
)
MODULUS = 2_147_483_647
MULTIPLIER = 16_807


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def p64_source_contract_errors(source: object) -> list[str]:
    if not isinstance(source, str) or not source:
        return ["P64 source must be nonempty text"]
    errors = [
        f"missing source marker: {marker}" for marker in SOURCE_MARKERS if marker not in source
    ]
    if source.count("figure('Name', 'P64") != 5:
        errors.append("P64 must create exactly five named figures")
    if source.count("'Tag', 'P64'") != 6:
        errors.append("P64 must tag five figures and one scoped cleanup")
    errors.extend(
        f"forbidden source token: {token}"
        for token in FORBIDDEN_SOURCE_TOKENS
        if token in source
    )
    return errors


def validate_p64_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P64 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [
        entry
        for entry in manifest["modules"]
        if isinstance(entry, dict) and entry.get("id") == "P64"
    ]
    if len(matches) != 1:
        errors.append("P64 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P64 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P64 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P64 empty {artifact}")
    return errors


def reviewed_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "seed": 6401,
        "elements": 12,
        "spacing": 0.5,
        "squint": 3.0,
        "target_angle": 2.0,
        "target_phase": 0.4,
        "snr_db": 15.0,
        "snapshots": 256,
        "angles": tuple(-10.0 + 0.05 * index for index in range(401)),
        "calibration_limit": 4.0,
        "sum_guard": 0.15,
        "squint_sweep": (1.5, 3.0, 5.0),
        "snr_sweep": (-5.0, 5.0, 15.0, 25.0),
        "broken_gain": 1.12,
        "broken_angle": 0.0,
        "max_elements": 16,
        "max_snapshots": 512,
        "max_angles": 1001,
        "max_cases": 5,
        "max_private": 20000,
        "max_values": 500000,
        "max_figures": 5,
        "tolerance": 1e-10,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    for name in (
        "seed",
        "elements",
        "snapshots",
        "max_elements",
        "max_snapshots",
        "max_angles",
        "max_cases",
        "max_private",
        "max_values",
        "max_figures",
    ):
        if not integer(controls[name]):
            raise ValueError(f"{name} integer")
    for name in (
        "spacing",
        "squint",
        "target_angle",
        "target_phase",
        "snr_db",
        "calibration_limit",
        "sum_guard",
        "broken_gain",
        "broken_angle",
        "tolerance",
    ):
        if not finite_real(controls[name]):
            raise ValueError(f"{name} finite")
    if controls["seed"] != 6401:
        raise ValueError("seed")
    if controls["elements"] != 12 or controls["max_elements"] != 16:
        raise ValueError("elements")
    if controls["snapshots"] != 256 or controls["max_snapshots"] != 512:
        raise ValueError("snapshots")
    if (
        controls["spacing"] != 0.5
        or controls["squint"] != 3.0
        or controls["target_angle"] != 2.0
        or controls["snr_db"] != 15.0
    ):
        raise ValueError("baseline")
    angles = controls["angles"]
    if (
        not isinstance(angles, (tuple, list))
        or len(angles) != 401
        or len(angles) > controls["max_angles"]
        or not all(finite_real(value) for value in angles)
        or abs(angles[0] + 10.0) > 1e-9
        or abs(angles[-1] - 10.0) > 1e-9
        or any(right <= left for left, right in zip(angles, angles[1:]))
        or any(abs((right - left) - 0.05) > 1e-9 for left, right in zip(angles, angles[1:]))
    ):
        raise ValueError("angles")
    for name, expected in (
        ("squint_sweep", (1.5, 3.0, 5.0)),
        ("snr_sweep", (-5.0, 5.0, 15.0, 25.0)),
    ):
        values = controls[name]
        if (
            not isinstance(values, (tuple, list))
            or tuple(values) != expected
            or len(values) > controls["max_cases"]
            or not all(finite_real(value) for value in values)
            or any(right <= left for left, right in zip(values, values[1:]))
        ):
            raise ValueError(name)
    if (
        controls["calibration_limit"] != 4.0
        or controls["sum_guard"] != 0.15
        or controls["broken_gain"] != 1.12
        or controls["broken_angle"] != 0.0
        or controls["max_private"] != 20000
        or controls["max_values"] != 500000
        or controls["max_figures"] != 5
        or controls["tolerance"] != 1e-10
    ):
        raise ValueError("immutable contract")
    private_request = 2 * controls["max_elements"] * controls["snapshots"]
    working_request = (
        controls["elements"] * controls["snapshots"]
        + 8 * len(angles)
        + controls["max_cases"] * len(angles)
    )
    if private_request > controls["max_private"] or working_request > controls["max_values"]:
        raise ValueError("resource ceiling")
    return controls


def private_uniform(seed: object, count: object, maximum: int = 20000) -> tuple[float, ...]:
    if not integer(seed) or not 1 <= seed < MODULUS:
        raise ValueError("seed")
    if not integer(count) or not 1 <= count <= maximum:
        raise ValueError("count")
    state = int(seed)
    values = []
    for _ in range(int(count)):
        state = (MULTIPLIER * state) % MODULUS
        values.append((state + 0.5) / MODULUS)
    return tuple(values)


def private_complex_noise(seed: int, rows: int, columns: int) -> list[list[complex]]:
    if not integer(rows) or not integer(columns) or rows < 1 or columns < 1:
        raise ValueError("noise shape")
    uniforms = private_uniform(seed, 2 * rows * columns)
    samples = [
        math.sqrt(-2 * math.log(uniforms[index]))
        * cmath.exp(1j * 2 * math.pi * uniforms[index + 1])
        / math.sqrt(2)
        for index in range(0, len(uniforms), 2)
    ]
    return [
        [samples[column * rows + row] for column in range(columns)]
        for row in range(rows)
    ]


def steering_vector(angle_deg: object, elements: object = 12, spacing: object = 0.5) -> tuple[complex, ...]:
    if not finite_real(angle_deg) or abs(angle_deg) > 90:
        raise ValueError("angle")
    if not integer(elements) or not 2 <= elements <= 16:
        raise ValueError("elements")
    if not finite_real(spacing) or spacing <= 0:
        raise ValueError("spacing")
    return tuple(
        cmath.exp(
            1j * 2 * math.pi * spacing * element * math.sin(math.radians(angle_deg))
        )
        for element in range(int(elements))
    )


def monopulse_channels(
    sensor_data: object, squint_deg: object = 3.0, spacing: object = 0.5
) -> tuple[tuple[complex, ...], tuple[complex, ...]]:
    if (
        not isinstance(sensor_data, list)
        or not 2 <= len(sensor_data) <= 16
        or any(not isinstance(row, list) or not row for row in sensor_data)
        or len({len(row) for row in sensor_data}) != 1
        or any(
            not math.isfinite(value.real) or not math.isfinite(value.imag)
            for row in sensor_data
            for value in row
        )
    ):
        raise ValueError("sensor data")
    if not finite_real(squint_deg) or squint_deg <= 0 or squint_deg >= 10:
        raise ValueError("squint")
    elements = len(sensor_data)
    snapshots = len(sensor_data[0])
    left_weight = tuple(value / elements for value in steering_vector(-squint_deg, elements, spacing))
    right_weight = tuple(value / elements for value in steering_vector(squint_deg, elements, spacing))
    left_boresight = sum(value.conjugate() for value in left_weight)
    right_boresight = sum(value.conjugate() for value in right_weight)
    left_phase = cmath.exp(-1j * cmath.phase(left_boresight))
    right_phase = cmath.exp(-1j * cmath.phase(right_boresight))
    left = tuple(
        sum(left_weight[row].conjugate() * sensor_data[row][snapshot] for row in range(elements))
        * left_phase
        for snapshot in range(snapshots)
    )
    right = tuple(
        sum(right_weight[row].conjugate() * sensor_data[row][snapshot] for row in range(elements))
        * right_phase
        for snapshot in range(snapshots)
    )
    return left, right


def beam_patterns(
    angles_deg: object, squint_deg: object = 3.0
) -> tuple[tuple[complex, ...], tuple[complex, ...]]:
    if (
        not isinstance(angles_deg, (tuple, list))
        or not angles_deg
        or not all(finite_real(angle) for angle in angles_deg)
        or any(right <= left for left, right in zip(angles_deg, angles_deg[1:]))
    ):
        raise ValueError("angle grid")
    data = [
        [steering_vector(angle)[element] for angle in angles_deg]
        for element in range(12)
    ]
    return monopulse_channels(data, squint_deg)


def ratio_record(
    left: object, right: object, sum_guard: object = 0.15
) -> tuple[tuple[float, ...], tuple[bool, ...]]:
    if (
        not isinstance(left, (tuple, list))
        or not isinstance(right, (tuple, list))
        or not left
        or len(left) != len(right)
        or not finite_real(sum_guard)
        or sum_guard <= 0
    ):
        raise ValueError("ratio record")
    ratios = []
    valid = []
    for left_value, right_value in zip(left, right):
        if not all(
            math.isfinite(component)
            for component in (left_value.real, left_value.imag, right_value.real, right_value.imag)
        ):
            raise ValueError("nonfinite channel")
        sigma = (right_value + left_value) / 2
        delta = (right_value - left_value) / 2
        if sigma == 0:
            raise ValueError("zero sum channel")
        valid.append(abs(sigma) >= sum_guard)
        ratios.append((delta / sigma).real)
    return tuple(ratios), tuple(valid)


def bounded_ratio_to_angle(
    ratios: object,
    calibration_ratio: object,
    calibration_angles: object,
) -> tuple[float, ...]:
    if (
        not isinstance(ratios, (tuple, list))
        or not ratios
        or not all(finite_real(value) for value in ratios)
        or not isinstance(calibration_ratio, (tuple, list))
        or not isinstance(calibration_angles, (tuple, list))
        or len(calibration_ratio) != len(calibration_angles)
        or len(calibration_ratio) < 2
        or not all(finite_real(value) for value in calibration_ratio + calibration_angles)
        or any(right <= left for left, right in zip(calibration_ratio, calibration_ratio[1:]))
        or any(right <= left for left, right in zip(calibration_angles, calibration_angles[1:]))
    ):
        raise ValueError("calibration")
    estimates = []
    for ratio in ratios:
        clipped = min(max(ratio, calibration_ratio[0]), calibration_ratio[-1])
        upper = next(index for index, value in enumerate(calibration_ratio) if value >= clipped)
        if upper == 0:
            estimates.append(calibration_angles[0])
        else:
            lower = upper - 1
            fraction = (clipped - calibration_ratio[lower]) / (
                calibration_ratio[upper] - calibration_ratio[lower]
            )
            estimates.append(
                calibration_angles[lower]
                + fraction * (calibration_angles[upper] - calibration_angles[lower])
            )
    return tuple(estimates)


def calibration() -> tuple[tuple[float, ...], tuple[float, ...]]:
    angles = tuple(-10.0 + 0.05 * index for index in range(401))
    left, right = beam_patterns(angles)
    ratios, _ = ratio_record(left, right)
    selected = tuple(index for index, angle in enumerate(angles) if abs(angle) <= 4.0 + 1e-12)
    return tuple(ratios[index] for index in selected), tuple(angles[index] for index in selected)


def simulate_target(
    seed: object = 6401,
    target_angle: object = 2.0,
    snr_db: object = 15.0,
    snapshots: object = 256,
) -> list[list[complex]]:
    if not integer(seed) or not 1 <= seed < MODULUS:
        raise ValueError("seed")
    if not finite_real(target_angle) or abs(target_angle) > 4:
        raise ValueError("target angle")
    if not finite_real(snr_db):
        raise ValueError("snr")
    if not integer(snapshots) or not 1 <= snapshots <= 512:
        raise ValueError("snapshots")
    steering = steering_vector(target_angle)
    target = cmath.exp(1j * 0.4)
    noise = private_complex_noise(int(seed), 16, int(snapshots))
    scale = 10 ** (-snr_db / 20)
    return [
        [steering[row] * target + scale * noise[row][column] for column in range(int(snapshots))]
        for row in range(12)
    ]


class P64ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.pattern_angles = tuple(-10.0 + 0.05 * index for index in range(401))
        cls.calibration_ratio, cls.calibration_angles = calibration()

    def run_fixture_cli(self, fixture_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(fixture_root.parent)
        return subprocess.run(
            [str(fixture_root / "bin/learn"), *args],
            cwd=fixture_root,
            env=env,
            text=True,
            capture_output=True,
            timeout=10,
        )

    def make_cli_fixture(self, base: Path, manifest: dict) -> Path:
        fixture = base / "repo"
        (fixture / "bin").mkdir(parents=True)
        (fixture / "curriculum").mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
        (fixture / "curriculum/modules.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        for module in manifest["modules"]:
            readme = fixture / module["folder"] / "README.md"
            readme.parent.mkdir(parents=True, exist_ok=True)
            readme.write_text(f"# {module['id']}\n", encoding="utf-8")
        return fixture

    def test_artifacts_manifest_identity_and_dependency_are_complete(self):
        self.assertEqual(validate_p64_contract(ROOT, self.manifest), [])
        p63 = next(module for module in self.manifest["modules"] if module["id"] == "P63")
        self.assertEqual(p63["status"], "implemented")

    def test_contract_rejects_malformed_duplicate_drift_missing_and_empty(self):
        self.assertTrue(validate_p64_contract(ROOT, None))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append(None)
        self.assertIn("every manifest module must be an object", validate_p64_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("P64 must have exactly one manifest entry", validate_p64_contract(ROOT, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(module for module in drifted["modules"] if module["id"] == "P64")["guiding_question"] = "changed"
        self.assertIn("P64 manifest identity drift", validate_p64_contract(ROOT, drifted))
        with tempfile.TemporaryDirectory() as temp:
            fixture_root = Path(temp)
            fixture_module = fixture_root / EXPECTED_IDENTITY["folder"]
            fixture_module.parent.mkdir(parents=True)
            shutil.copytree(MODULE, fixture_module)
            (fixture_module / "lesson.md").unlink()
            self.assertIn("P64 missing lesson.md", validate_p64_contract(fixture_root, self.manifest))
            (fixture_module / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P64 empty lesson.md", validate_p64_contract(fixture_root, self.manifest))

    def test_source_exposes_model_sweeps_failure_recovery_and_bounds(self):
        self.assertEqual(p64_source_contract_errors(self.source), [])

    def test_source_contract_rejects_black_boxes_and_representative_mutants(self):
        for marker in (
            "left_weight = left_steering/number_elements;",
            "right_weight = right_steering/number_elements;",
            "sum_pattern = (right_pattern+left_pattern)/2;",
            "difference_pattern = (right_pattern-left_pattern)/2;",
            "normalized_ratio = real(difference_pattern./sum_pattern);",
            "baseline_ratio_samples = real(baseline_difference./baseline_sum);",
            "baseline_valid_samples = abs(baseline_sum) >= sum_guard;",
            "assert(all(diff(squint_boresight_sum) < 0), 'P64:SquintSumSweep', ...",
            "assert(all(diff(snr_sweep_rmse_deg) < 0), 'P64:SNRSweep', ...",
            "broken_right = broken_right_gain*ideal_right;",
            "recovered_right = broken_right/broken_right_gain;",
            "flat_estimates(sample_index) = calibration_angles_deg(lower_index)+ ...",
            "samples = sqrt(-2*log(first)).*exp(1j*2*pi*second)/sqrt(2);",
            "maximum_working_numeric_values = 500000;",
        ):
            with self.subTest(marker=marker):
                self.assertTrue(p64_source_contract_errors(self.source.replace(marker, "removed", 1)))
        self.assertTrue(p64_source_contract_errors(self.source + "\nphased.ULA(12)"))

    def test_controls_accept_reviewed_values_and_reject_malformed_inputs(self):
        self.assertEqual(reviewed_controls()["elements"], 12)
        cases = (
            {"seed": 0},
            {"elements": True},
            {"elements": 12.5},
            {"elements": 17},
            {"spacing": 0.0},
            {"squint": float("nan")},
            {"target_angle": 5.0},
            {"snr_db": float("inf")},
            {"snapshots": 256.5},
            {"angles": ()},
            {"angles": (-10.0, 0.0, -1.0, 10.0)},
            {"angles": tuple(float(index) for index in range(1002))},
            {"calibration_limit": 0.0},
            {"sum_guard": -1.0},
            {"squint_sweep": (1.5, 5.0, 3.0)},
            {"snr_sweep": (-5.0, 5.0, 5.0, 25.0)},
            {"broken_gain": -1.12},
            {"max_private": 8191},
            {"max_values": 1000},
            {"max_figures": 6},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    reviewed_controls(**changes)
        with self.assertRaises(ValueError):
            reviewed_controls(unknown=1)

    def test_private_seed_is_exact_repeatable_isolated_and_bounded(self):
        expected = (
            0.05009658986241398,
            0.9733819046399472,
            0.6296673706405178,
            0.8194944422317177,
        )
        first = private_uniform(6401, 4)
        second = private_uniform(6401, 4)
        for actual, wanted in zip(first, expected):
            self.assertAlmostEqual(actual, wanted, places=14)
        self.assertEqual(first, second)
        for seed, count in ((0, 4), (MODULUS, 4), (6401.5, 4), (6401, 0), (6401, 20001)):
            with self.subTest(seed=seed, count=count):
                with self.assertRaises(ValueError):
                    private_uniform(seed, count)

    def test_complex_noise_fixture_binds_matlab_generator_layout(self):
        noise = private_complex_noise(6401, 16, 256)
        expected = (
            (0, 0, 1.7061182465031899, -0.2880327564276668),
            (1, 0, 0.28762487090966304, -0.6163079715314499),
            (0, 1, 0.08463551713416892, -0.17883121367157268),
            (15, 255, 0.26341207914719594, 0.08921762784537988),
        )
        for row, column, real, imag in expected:
            self.assertAlmostEqual(noise[row][column].real, real, places=14)
            self.assertAlmostEqual(noise[row][column].imag, imag, places=14)

    def test_independent_pattern_oracle_has_required_symmetry_and_local_monotonicity(self):
        left, right = beam_patterns(self.pattern_angles)
        ratios, valid = ratio_record(left, right)
        self.assertTrue(all(valid[index] for index, angle in enumerate(self.pattern_angles) if abs(angle) <= 4))
        for index in range(len(self.pattern_angles)):
            mirror = len(self.pattern_angles) - 1 - index
            self.assertAlmostEqual(abs(left[index]), abs(right[mirror]), places=12)
            self.assertAlmostEqual(abs((right[index] + left[index]) / 2), abs((right[mirror] + left[mirror]) / 2), places=12)
            self.assertAlmostEqual(ratios[index], -ratios[mirror], places=11)
        self.assertAlmostEqual(ratios[200], 0.0, places=13)
        self.assertTrue(all(right_value > left_value for left_value, right_value in zip(self.calibration_ratio, self.calibration_ratio[1:])))
        self.assertAlmostEqual(self.calibration_ratio[0], -0.5020664573616728, places=12)
        self.assertAlmostEqual(self.calibration_ratio[-1], 0.5020664573616728, places=12)

    def test_noise_free_lookup_recovers_angles_and_bounds_saturation(self):
        requested = (-4.0, -2.0, 0.0, 2.0, 4.0)
        left, right = beam_patterns(requested)
        ratios, _ = ratio_record(left, right)
        estimates = bounded_ratio_to_angle(ratios, self.calibration_ratio, self.calibration_angles)
        for actual, expected in zip(estimates, requested):
            self.assertAlmostEqual(actual, expected, places=11)
        saturated = bounded_ratio_to_angle((-99.0, 99.0), self.calibration_ratio, self.calibration_angles)
        self.assertEqual(saturated, (-4.0, 4.0))

    def test_simultaneous_common_target_voltage_cancels_from_ratio_and_angle(self):
        target_steering = steering_vector(2.0)
        target_voltages = tuple(
            magnitude * cmath.exp(1j * phase)
            for magnitude, phase in ((0.5, -2.0), (1.0, 0.4), (2.0, 1.3), (5.0, -0.7))
        )
        data = [
            [target_steering[row] * voltage for voltage in target_voltages]
            for row in range(12)
        ]
        left, right = monopulse_channels(data)
        ratios, valid = ratio_record(left, right)
        estimates = bounded_ratio_to_angle(
            ratios, self.calibration_ratio, self.calibration_angles
        )
        expected_ratio = self.calibration_ratio[self.calibration_angles.index(2.0)]
        self.assertTrue(all(valid))
        for ratio, estimate in zip(ratios, estimates):
            self.assertAlmostEqual(ratio, expected_ratio, places=12)
            self.assertAlmostEqual(estimate, 2.0, places=11)

    def test_deterministic_noisy_baseline_matches_reviewed_metrics(self):
        data = simulate_target()
        left, right = monopulse_channels(data)
        ratios, valid = ratio_record(left, right)
        estimates = bounded_ratio_to_angle(
            tuple(value for value, accepted in zip(ratios, valid) if accepted),
            self.calibration_ratio,
            self.calibration_angles,
        )
        sigma = tuple((right_value + left_value) / 2 for left_value, right_value in zip(left, right))
        delta = tuple((right_value - left_value) / 2 for left_value, right_value in zip(left, right))
        coherent_ratio = (sum(delta) / sum(sigma)).real
        coherent_estimate = bounded_ratio_to_angle(
            (coherent_ratio,), self.calibration_ratio, self.calibration_angles
        )[0]
        rmse = math.sqrt(sum((estimate - 2.0) ** 2 for estimate in estimates) / len(estimates))
        self.assertTrue(all(valid))
        self.assertAlmostEqual(ratios[0], 0.23540455035473232, places=13)
        self.assertAlmostEqual(coherent_ratio, 0.2341409192657401, places=13)
        self.assertAlmostEqual(coherent_estimate, 1.9928646603789308, places=12)
        self.assertAlmostEqual(rmse, 0.1839513638757116, places=12)

    def test_squint_sweep_trades_slope_against_sum_strength(self):
        slopes = []
        boresight_sums = []
        minus = self.pattern_angles.index(-1.0)
        plus = self.pattern_angles.index(1.0)
        zero = self.pattern_angles.index(0.0)
        for squint in (1.5, 3.0, 5.0):
            left, right = beam_patterns(self.pattern_angles, squint)
            ratios, _ = ratio_record(left, right)
            slopes.append((ratios[plus] - ratios[minus]) / 2)
            boresight_sums.append(abs((right[zero] + left[zero]) / 2))
        self.assertTrue(all(right > left for left, right in zip(slopes, slopes[1:])))
        self.assertTrue(all(right < left for left, right in zip(boresight_sums, boresight_sums[1:])))

    def test_snr_sweep_reuses_noise_and_reduces_snapshot_rmse(self):
        noise = private_complex_noise(6402, 16, 256)
        target_steering = steering_vector(2.0)
        target = cmath.exp(1j * 0.4)
        rmses = []
        rejected = []
        coherent = []
        for snr in (-5.0, 5.0, 15.0, 25.0):
            scale = 10 ** (-snr / 20)
            data = [
                [target_steering[row] * target + scale * noise[row][column] for column in range(256)]
                for row in range(12)
            ]
            left, right = monopulse_channels(data)
            ratios, valid = ratio_record(left, right)
            accepted = tuple(value for value, flag in zip(ratios, valid) if flag)
            estimates = bounded_ratio_to_angle(accepted, self.calibration_ratio, self.calibration_angles)
            rmses.append(math.sqrt(sum((estimate - 2) ** 2 for estimate in estimates) / len(estimates)))
            rejected.append(valid.count(False))
            sigma = tuple((r + l) / 2 for l, r in zip(left, right))
            delta = tuple((r - l) / 2 for l, r in zip(left, right))
            coherent.append(
                bounded_ratio_to_angle(
                    ((sum(delta) / sum(sigma)).real,), self.calibration_ratio, self.calibration_angles
                )[0]
            )
        self.assertTrue(all(right < left for left, right in zip(rmses, rmses[1:])))
        self.assertEqual(rejected, [2, 0, 0, 0])
        expected_rmse = (1.8149541476915518, 0.6626636698475726, 0.21073000516627255, 0.06693073943628736)
        expected_coherent = (2.0221795396778877, 2.0066424686644564, 2.002061264907546, 2.000647832197615)
        for actual, expected in zip(rmses, expected_rmse):
            self.assertAlmostEqual(actual, expected, places=11)
        for actual, expected in zip(coherent, expected_coherent):
            self.assertAlmostEqual(actual, expected, places=11)

    def test_gain_mismatch_bias_and_same_data_recovery_are_exact(self):
        left, ideal_right = beam_patterns((0.0,))
        broken_right = (1.12 * ideal_right[0],)
        broken_ratio, _ = ratio_record(left, broken_right)
        broken_estimate = bounded_ratio_to_angle(
            broken_ratio, self.calibration_ratio, self.calibration_angles
        )[0]
        recovered_right = (broken_right[0] / 1.12,)
        recovered_ratio, _ = ratio_record(left, recovered_right)
        recovered_estimate = bounded_ratio_to_angle(
            recovered_ratio, self.calibration_ratio, self.calibration_angles
        )[0]
        self.assertAlmostEqual(broken_ratio[0], (1.12 - 1) / (1.12 + 1), places=14)
        self.assertAlmostEqual(broken_estimate, 0.4908913734993808, places=12)
        self.assertAlmostEqual(recovered_ratio[0], 0.0, places=14)
        self.assertAlmostEqual(recovered_estimate, 0.0, places=14)
        self.assertAlmostEqual(recovered_right[0], ideal_right[0], places=14)

    def test_coherent_averaging_does_not_remove_fixed_gain_bias(self):
        target_voltages = tuple(
            magnitude * cmath.exp(1j * phase)
            for magnitude, phase in ((0.5, -2.0), (1.0, 0.4), (2.0, 1.3), (5.0, -0.7))
        )
        boresight = steering_vector(0.0)
        data = [
            [boresight[row] * voltage for voltage in target_voltages]
            for row in range(12)
        ]
        left, ideal_right = monopulse_channels(data)
        broken_right = tuple(1.12 * value for value in ideal_right)
        broken_ratios, valid = ratio_record(left, broken_right)
        broken_sigma = tuple((right + left_value) / 2 for left_value, right in zip(left, broken_right))
        broken_delta = tuple((right - left_value) / 2 for left_value, right in zip(left, broken_right))
        coherent_broken_ratio = (sum(broken_delta) / sum(broken_sigma)).real

        recovered_right = tuple(value / 1.12 for value in broken_right)
        recovered_sigma = tuple(
            (right + left_value) / 2 for left_value, right in zip(left, recovered_right)
        )
        recovered_delta = tuple(
            (right - left_value) / 2 for left_value, right in zip(left, recovered_right)
        )
        coherent_recovered_ratio = (sum(recovered_delta) / sum(recovered_sigma)).real

        expected_bias = (1.12 - 1) / (1.12 + 1)
        self.assertTrue(all(valid))
        for ratio in broken_ratios:
            self.assertAlmostEqual(ratio, expected_bias, places=14)
        self.assertAlmostEqual(coherent_broken_ratio, expected_bias, places=14)
        self.assertAlmostEqual(coherent_recovered_ratio, 0.0, places=14)
        for actual, expected in zip(recovered_right, ideal_right):
            self.assertAlmostEqual(actual, expected, places=14)

    def test_oracles_reject_nonfinite_malformed_and_low_sum_records(self):
        for args in ((float("nan"),), (91.0,), (0.0, 1), (0.0, 17), (0.0, 12, 0.0)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    steering_vector(*args)
        for data in (None, [[1j], []], [[1j], [complex(float("nan"), 0)]], [[1j]] * 17):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    monopulse_channels(data)
        for args in (((),), ((0.0, 0.0),), ((0.0, float("inf")),)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    beam_patterns(*args)
        with self.assertRaises(ValueError):
            ratio_record((1 + 0j,), (-1 + 0j,))
        ratios, valid = ratio_record((1 + 0j,), (-0.9 + 0j,))
        self.assertFalse(valid[0])
        self.assertLess(ratios[0], -10)
        malformed_calibrations = (
            ((), self.calibration_ratio, self.calibration_angles),
            ((0.0,), (0.0, 0.0), (-1.0, 1.0)),
            ((0.0,), (0.0, 1.0), (1.0, -1.0)),
            ((float("nan"),), self.calibration_ratio, self.calibration_angles),
        )
        for args in malformed_calibrations:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    bounded_ratio_to_angle(*args)
        for args in ((0, 2.0, 15.0, 256), (6401, 5.0, 15.0, 256), (6401, 2.0, float("nan"), 256), (6401, 2.0, 15.0, 513)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    simulate_target(*args)

    def test_documents_are_concept_first_and_cover_limits_and_dependencies(self):
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        for document in (readme, lesson, walkthrough, checks):
            self.assertIn(QUESTION, document)
            self.assertNotIn("TODO", document)
        for marker in (
            "a_m(theta) = exp(j 2 pi m q sin(theta))",
            "Sigma = (R + L)/2",
            "Delta = (R - L)/2",
            "eta   = Re{Delta/Sigma}",
            "eta_broken = (g A - A)/(g A + A) = (g - 1)/(g + 1)",
            "power ratio",
            "narrowband",
            "far-field",
            "P61",
            "P62",
            "P63",
            "P67",
        ):
            self.assertIn(marker, lesson)
        for marker in ("Sweep 1", "Sweep 2", "Broken case", "Recovery", "Ctrl+C"):
            self.assertIn(marker, walkthrough)
        self.assertIn("Short teach-back rubric", checks)
        self.assertGreaterEqual(checks.count("**Correct:**"), 32)

    def test_cli_timeout_isolation_rollback_recovery_and_future_compatibility(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        compatible = copy.deepcopy(self.manifest)
        p65 = next(module for module in compatible["modules"] if module["id"] == "P65")
        p65["future_extension"] = {"accepted": True}
        original_p63 = copy.deepcopy(next(module for module in compatible["modules"] if module["id"] == "P63"))
        original_p65 = copy.deepcopy(p65)
        with tempfile.TemporaryDirectory() as temp:
            fixture = self.make_cli_fixture(Path(temp), compatible)
            started = self.run_fixture_cli(fixture, "start", "64")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P64", started.stdout)
            self.assertIn("status: implemented", started.stdout)
            state_path = fixture / ".learning/progress.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P63",
                        "completed": [f"P{number:02d}" for number in range(1, 64)],
                        "notes": {"P63": "prerequisite complete"},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            advanced = self.run_fixture_cli(fixture, "start")
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertIn("P64 — Build an Amplitude-Comparison Monopulse Experiment", advanced.stdout)
            rolled_back = copy.deepcopy(compatible)
            next(module for module in rolled_back["modules"] if module["id"] == "P64")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(
                json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8"
            )
            refused = self.run_fixture_cli(fixture, "start", "64")
            self.assertEqual(refused.returncode, 3, refused.stderr)
            self.assertIn("awaits Portfolio batch P64", refused.stdout)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P63"), original_p63)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P65"), original_p65)
            (fixture / "curriculum/modules.json").write_text(
                json.dumps(compatible, indent=2) + "\n", encoding="utf-8"
            )
            recovered = self.run_fixture_cli(fixture, "start", "64")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_cancellation_cleanup_has_no_external_or_persistent_side_effects(self):
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P64'));", self.source)
        self.assertNotIn("close all", self.source)
        for token in ("timer(", "parfor", "webread", "urlread", "fopen(", "save(", "system("):
            self.assertNotIn(token, self.source)
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        self.assertIn("Ctrl+C", walkthrough)
        self.assertIn("no worker, timer", walkthrough)

    def test_public_catalogs_describe_permanent_p64_facts(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 64 follows P63", readme)
        self.assertIn("Project 64 follows P63", start_here)
        self.assertIn(
            "| [P64](../modules/64-build-an-amplitude-comparison-monopulse-experiment/) | implemented | 7 |",
            module_index,
        )

    def test_retained_evidence_has_claim_boundary_commands_and_lifecycle_coverage(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P64-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        for marker in (
            "# P64 Retained Evidence",
            "## Acceptance map",
            "84 modules, 64 implemented",
            "## Deterministic simulated-oracle results",
            "## Figure and metric inventory",
            "## Exact commands and results",
            "python3 -m unittest tests.test_p64_module -v",
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
            "command -v matlab",
            "command -v octave",
            "No MATLAB runtime evidence was produced",
            "## Focused positive and negative coverage",
            "Malformed input",
            "Timeout guard",
            "Cancellation",
            "Rollback and recovery",
            "Isolation",
            "Compatibility",
            "Resource bounds",
            "## Changed and preserved invariants",
            "## Residual risks and known content gaps",
            "## Rollback",
            "## Unperformed validation",
            "Hardware/HIL",
            "RT1/RT2",
            "Unreal",
            "signing",
            "deployment",
            "production",
            "operator-provided `contracts/active-batch.yaml`",
            "operator-provided `contracts/repo-profile.yaml`",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, evidence)
        self.assertTrue(evidence.endswith("\n"))
        self.assertFalse(evidence.endswith("\n\n"))

    def test_changed_text_files_have_exactly_one_terminal_newline(self):
        paths = [MODULE / artifact for artifact in ARTIFACTS] + [
            ROOT / "README.md",
            ROOT / "START_HERE.md",
            ROOT / "modules/README.md",
            ROOT / "curriculum/modules.json",
            ROOT / "tests/test_p64_module.py",
            ROOT / "docs/evidence/P64-2026-08-05.md",
        ]
        for path in paths:
            with self.subTest(path=path):
                data = path.read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
