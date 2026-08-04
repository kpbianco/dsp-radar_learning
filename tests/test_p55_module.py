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
MODULE = ROOT / "modules/55-implement-a-constant-velocity-kalman-filter"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How do process noise and measurement noise determine trust in prediction versus measurement?"
EXPECTED_IDENTITY = {
    "number": 55,
    "id": "P55",
    "title": "Implement a Constant-Velocity Kalman Filter",
    "guiding_question": QUESTION,
    "phase": 6,
    "phase_title": "Radar Tracking and Data Association",
    "slug": "implement-a-constant-velocity-kalman-filter",
    "folder": "modules/55-implement-a-constant-velocity-kalman-filter",
    "status": "implemented",
    "implementation_batch": "P55",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def validate_p55_contract(module: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P55 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P55 empty {artifact}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P55"]
    if len(entries) != 1:
        return errors + [f"expected one P55 manifest entry, found {len(entries)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if entries[0].get(key) != expected:
            errors.append(f"P55 {key} mismatch")
    return errors


def canonical_controls() -> dict[str, object]:
    return {
        "seed": 5501,
        "number_scans": 101,
        "dt": 1.0,
        "actual_q_std": 0.8,
        "actual_r_std": 25.0,
        "initial_position_std": 25.0,
        "initial_velocity_std": 15.0,
        "warmup": 15,
        "assumed_q_std": 0.8,
        "assumed_r_std": 25.0,
        "q_sweep": (0.10, 0.80, 3.20),
        "r_sweep": (5.0, 25.0, 100.0),
        "broken_q_std": 0.0,
        "broken_r_std": 0.5,
        "max_scans": 200,
        "max_sweep_cases": 5,
        "max_figures": 5,
        "max_steps": 1200,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError("unknown control")
    controls.update(overrides)
    for name in (
        "seed", "number_scans", "warmup", "max_scans", "max_sweep_cases",
        "max_figures", "max_steps",
    ):
        if not integer(controls[name]):
            raise ValueError(f"integer control {name}")
    for name in (
        "dt", "actual_q_std", "actual_r_std", "initial_position_std",
        "initial_velocity_std", "assumed_q_std", "assumed_r_std",
        "broken_q_std", "broken_r_std",
    ):
        if not finite_real(controls[name]):
            raise ValueError(f"real control {name}")
    fixed = {
        "seed": 5501, "number_scans": 101, "dt": 1.0,
        "actual_q_std": 0.8, "actual_r_std": 25.0,
        "assumed_q_std": 0.8, "assumed_r_std": 25.0,
        "broken_q_std": 0.0, "broken_r_std": 0.5,
        "max_scans": 200, "max_sweep_cases": 5,
        "max_figures": 5, "max_steps": 1200,
    }
    if any(controls[name] != expected for name, expected in fixed.items()):
        raise ValueError("reviewed control drift")
    if controls["number_scans"] > controls["max_scans"]:
        raise ValueError("scan bound")
    if not 1 <= controls["warmup"] < controls["number_scans"] - 2:
        raise ValueError("warm-up domain")
    if controls["initial_position_std"] <= 0 or controls["initial_velocity_std"] <= 0:
        raise ValueError("initial uncertainty")
    for name, baseline, allow_zero in (
        ("q_sweep", controls["assumed_q_std"], True),
        ("r_sweep", controls["assumed_r_std"], False),
    ):
        values = controls[name]
        if not isinstance(values, (tuple, list)) or not 3 <= len(values) <= controls["max_sweep_cases"]:
            raise ValueError("sweep shape")
        if not all(finite_real(value) for value in values):
            raise ValueError("sweep finite")
        if any(right <= left for left, right in zip(values, values[1:])) or baseline not in values:
            raise ValueError("sweep ordering/baseline")
        if any(value < 0 if allow_zero else value <= 0 for value in values):
            raise ValueError("sweep domain")
    run_count = 1 + len(controls["q_sweep"]) + len(controls["r_sweep"]) + 2 + 1
    if run_count * controls["number_scans"] > controls["max_steps"]:
        raise ValueError("filter-step bound")


def matmul(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    return [
        [sum(left[row][k] * right[k][column] for k in range(len(right)))
         for column in range(len(right[0]))]
        for row in range(len(left))
    ]


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(column) for column in zip(*matrix)]


def kalman_filter(
    measurements: object,
    dt: object,
    q_std: object,
    r_std: object,
    initial_state: object,
    initial_covariance: object,
) -> dict[str, list]:
    if not isinstance(measurements, (tuple, list)) or len(measurements) < 2:
        raise ValueError("measurement shape")
    if not all(finite_real(value) for value in measurements):
        raise ValueError("measurement values")
    if not finite_real(dt) or dt <= 0:
        raise ValueError("interval")
    if not finite_real(q_std) or q_std < 0 or not finite_real(r_std) or r_std <= 0:
        raise ValueError("noise model")
    if not isinstance(initial_state, (tuple, list)) or len(initial_state) != 2:
        raise ValueError("state shape")
    if not all(finite_real(value) for value in initial_state):
        raise ValueError("state values")
    if (
        not isinstance(initial_covariance, (tuple, list))
        or len(initial_covariance) != 2
        or any(not isinstance(row, (tuple, list)) or len(row) != 2 for row in initial_covariance)
    ):
        raise ValueError("covariance shape")
    p = [[float(value) for value in row] for row in initial_covariance]
    if not all(finite_real(value) for row in p for value in row):
        raise ValueError("covariance values")
    if abs(p[0][1] - p[1][0]) > 1e-12 or p[0][0] < 0 or p[1][1] < 0:
        raise ValueError("covariance symmetry/diagonal")
    if p[0][0] * p[1][1] - p[0][1] * p[1][0] < -1e-12:
        raise ValueError("covariance PSD")

    f = [[1.0, float(dt)], [0.0, 1.0]]
    g = [[0.5 * dt * dt], [float(dt)]]
    q = [[q_std * q_std * value for value in row] for row in matmul(g, transpose(g))]
    r = r_std * r_std
    states = [[float(initial_state[0]), float(initial_state[1])]]
    predictions = [states[0][:]]
    gains = [[math.nan, math.nan]]
    innovations = [math.nan]
    innovation_variances = [math.nan]
    variances = [[p[0][0], p[1][1]]]

    for measurement in measurements[1:]:
        previous = states[-1]
        predicted = [previous[0] + dt * previous[1], previous[1]]
        fp = matmul(f, p)
        predicted_p = matmul(fp, transpose(f))
        predicted_p = [[predicted_p[row][column] + q[row][column] for column in range(2)] for row in range(2)]
        innovation = measurement - predicted[0]
        innovation_variance = predicted_p[0][0] + r
        gain = [predicted_p[0][0] / innovation_variance, predicted_p[1][0] / innovation_variance]
        corrected = [predicted[row] + gain[row] * innovation for row in range(2)]

        a = [[1.0 - gain[0], 0.0], [-gain[1], 1.0]]
        joseph = matmul(matmul(a, predicted_p), transpose(a))
        krkt = [[gain[row] * r * gain[column] for column in range(2)] for row in range(2)]
        p = [[joseph[row][column] + krkt[row][column] for column in range(2)] for row in range(2)]
        p = [[0.5 * (p[row][column] + p[column][row]) for column in range(2)] for row in range(2)]

        predictions.append(predicted)
        states.append(corrected)
        gains.append(gain)
        innovations.append(innovation)
        innovation_variances.append(innovation_variance)
        variances.append([p[0][0], p[1][1]])
    return {
        "states": states,
        "predictions": predictions,
        "gains": gains,
        "innovations": innovations,
        "innovation_variances": innovation_variances,
        "variances": variances,
    }


def deterministic_scene() -> tuple[list[list[float]], list[float]]:
    accelerations = [0.8 * (((index * 7) % 11) - 5) / 3 for index in range(60)]
    truth = [[1000.0, 20.0]]
    for acceleration in accelerations:
        position, velocity = truth[-1]
        truth.append([position + velocity + 0.5 * acceleration, velocity + acceleration])
    noise = [float((((index * 13) % 17) - 8) * 3) for index in range(len(truth))]
    measurements = [state[0] + error for state, error in zip(truth, noise)]
    return truth, measurements


def rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values))


def source_binding_errors(source: str) -> list[str]:
    required = (
        "random_seed = 5501;",
        "number_scans = 101;",
        "actual_process_acceleration_std_mps2 = 0.8;",
        "actual_measurement_std_m = 25;",
        "process_std_sweep_mps2 = [0.10 0.80 3.20];",
        "measurement_std_sweep_m = [5 25 100];",
        "broken_process_std_mps2 = 0;",
        "broken_measurement_std_m = 0.5;",
        "maximum_filter_steps = 1200;",
        "private_stream = RandStream('mt19937ar', 'Seed', random_seed);",
        "F_local = [1 sample_interval_s; 0 1];",
        "G_local = [0.5*sample_interval_s^2; sample_interval_s];",
        "H_local = [1 0];",
        "Q_local = process_acceleration_std_mps2^2*(G_local*G_local');",
        "R_local = measurement_std_m^2;",
        "state_prediction(:, sample_index) = F_local*state_estimate(:, sample_index-1);",
        "covariance_prediction = F_local*covariance_estimate*F_local' + Q_local;",
        "innovation_m(sample_index) = measurement_m(sample_index) - ...",
        "H_local*state_prediction(:, sample_index);",
        "H_local*covariance_prediction*H_local' + R_local;",
        "(covariance_prediction*H_local')/innovation_variance(sample_index);",
        "state_estimate(:, sample_index) = state_prediction(:, sample_index) + ...",
        "joseph_factor = identity_state - kalman_gain(:, sample_index)*H_local;",
        "covariance_estimate = joseph_factor*covariance_prediction*joseph_factor' + ...",
        "covariance_estimate = 0.5*(covariance_estimate + covariance_estimate');",
        "~isnumeric(measurement_m) || ~isreal(measurement_m) || ...",
        "numel(measurement_m) < 2 || any(~isfinite(measurement_m))",
        "process_acceleration_std_mps2 < 0 || measurement_std_m <= 0",
        "~isequal(size(initial_state), [2 1])",
        "~isequal(size(initial_covariance), [2 2])",
        "any(eig(initial_covariance) < -1e-12)",
        "reviewed_filter_steps == 1010;",
        "baseline_velocity_coverage > 0.5",
        "results.baseline_mean_nis = baseline_mean_nis;",
        "results.broken_r_mean_nis = broken_r_mean_nis;",
    )
    errors = [marker for marker in required if marker not in source]
    try:
        operation = source[source.index("function track = run_cv_kalman"):source.index("function validate_filter_inputs")]
    except ValueError:
        return errors + ["filter operation boundary"]
    for marker in (
        "state_prediction(:, sample_index) =",
        "innovation_m(sample_index) =",
        "kalman_gain(:, sample_index) =",
        "state_estimate(:, sample_index) =",
        "covariance_estimate = joseph_factor*covariance_prediction",
    ):
        if operation.count(marker) != 1:
            errors.append(f"single operation: {marker}")
    return errors


class P55ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self) -> None:
        self.assertEqual(validate_p55_contract(MODULE, self.manifest), [])
        p54 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P54")
        self.assertEqual(p54["status"], "implemented")
        for name in ARTIFACTS:
            payload = (MODULE / name).read_bytes()
            self.assertTrue(payload.endswith(b"\n"), name)
            self.assertFalse(payload.endswith(b"\n\n"), name)
            self.assertNotIn(b"\r", payload, name)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture = Path(temporary_directory) / "module"
            shutil.copytree(MODULE, fixture)
            (fixture / "lesson.md").unlink()
            self.assertIn("P55 missing lesson.md", validate_p55_contract(fixture, self.manifest))
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P55 empty lesson.md", validate_p55_contract(fixture, self.manifest))
        for malformed in (None, [], {}, {"modules": None}, {"modules": ["P55"]}):
            self.assertTrue(validate_p55_contract(MODULE, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P55 manifest entry, found 2", validate_p55_contract(MODULE, duplicate))
        for key in EXPECTED_IDENTITY:
            drifted = copy.deepcopy(self.manifest)
            entry = next(item for item in drifted["modules"] if item["id"] == "P55")
            entry[key] = -1 if isinstance(entry[key], int) else "drift"
            self.assertTrue(validate_p55_contract(MODULE, drifted), key)

    def test_controls_accept_reviewed_and_reject_malformed_or_unbounded_values(self) -> None:
        validate_controls()
        bad_cases = (
            {"unknown": 1}, {"seed": True}, {"seed": 5502},
            {"number_scans": 100}, {"number_scans": 101.5}, {"dt": 0},
            {"actual_q_std": complex(1, 1)}, {"actual_r_std": 0},
            {"initial_position_std": 0}, {"initial_velocity_std": math.inf},
            {"warmup": 0}, {"warmup": 99}, {"assumed_q_std": -1},
            {"assumed_r_std": math.nan}, {"broken_q_std": 0.1},
            {"broken_r_std": 0}, {"q_sweep": (0.1, 0.8)},
            {"q_sweep": (0.1, 0.1, 3.2)}, {"q_sweep": (0.1, 0.7, 3.2)},
            {"r_sweep": (5, math.inf, 100)}, {"r_sweep": (5, 100, 25)},
            {"max_scans": 201}, {"max_sweep_cases": 6},
            {"max_figures": 6}, {"max_steps": 1009},
        )
        for controls in bad_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_explicit_one_step_equations_joseph_covariance_and_units(self) -> None:
        track = kalman_filter([10.0, 16.0], 2.0, 0.0, 2.0, [10.0, 2.0], [[4.0, 0.0], [0.0, 1.0]])
        self.assertEqual(track["predictions"][1], [14.0, 2.0])
        self.assertEqual(track["innovations"][1], 2.0)
        self.assertEqual(track["innovation_variances"][1], 12.0)
        self.assertAlmostEqual(track["gains"][1][0], 2 / 3)
        self.assertAlmostEqual(track["gains"][1][1], 1 / 6)
        self.assertAlmostEqual(track["states"][1][0], 46 / 3)
        self.assertAlmostEqual(track["states"][1][1], 7 / 3)
        self.assertAlmostEqual(track["variances"][1][0], 8 / 3)
        self.assertAlmostEqual(track["variances"][1][1], 2 / 3)

    def test_relative_q_r_trust_zero_innovation_and_translation_invariance(self) -> None:
        measurements = [100.0, 112.0, 125.0, 139.0]
        base = kalman_filter(measurements, 1.0, 0.8, 10.0, [100.0, 10.0], [[100.0, 0.0], [0.0, 25.0]])
        high_q = kalman_filter(measurements, 1.0, 3.2, 10.0, [100.0, 10.0], [[100.0, 0.0], [0.0, 25.0]])
        high_r = kalman_filter(measurements, 1.0, 0.8, 100.0, [100.0, 10.0], [[100.0, 0.0], [0.0, 25.0]])
        self.assertGreater(high_q["gains"][-1][0], base["gains"][-1][0])
        self.assertLess(high_r["gains"][-1][0], base["gains"][-1][0])
        zero = kalman_filter([10.0, 12.0], 1.0, 0.0, 2.0, [10.0, 2.0], [[1.0, 0.0], [0.0, 1.0]])
        self.assertEqual(zero["innovations"][1], 0.0)
        self.assertEqual(zero["states"][1], zero["predictions"][1])
        shifted = kalman_filter([150.0, 162.0, 175.0, 189.0], 1.0, 0.8, 10.0, [150.0, 10.0], [[100.0, 0.0], [0.0, 25.0]])
        for original, translated in zip(base["states"], shifted["states"]):
            self.assertAlmostEqual(translated[0] - original[0], 50.0)
            self.assertAlmostEqual(translated[1], original[1])
        for original, translated in zip(base["innovations"][1:], shifted["innovations"][1:]):
            self.assertAlmostEqual(translated, original)

    def test_oracle_rejects_malformed_measurements_noise_state_and_covariance(self) -> None:
        good = ([1.0, 2.0], 1.0, 0.8, 25.0, [1.0, 0.0], [[1.0, 0.0], [0.0, 1.0]])
        bad_args = (
            ([], *good[1:]), ([1.0], *good[1:]), ([1.0, math.nan], *good[1:]),
            (good[0], True, *good[2:]), (good[0], 0.0, *good[2:]),
            (*good[:2], -0.1, *good[3:]), (*good[:3], 0.0, *good[4:]),
            (*good[:4], [1.0], good[5]), (*good[:4], [1.0, math.inf], good[5]),
            (*good[:5], [[1.0]]), (*good[:5], [[1.0, 1.0], [0.0, 1.0]]),
            (*good[:5], [[1.0, 2.0], [2.0, 1.0]]),
        )
        for args in bad_args:
            with self.subTest(args=args), self.assertRaises(ValueError):
                kalman_filter(*args)

    def test_end_to_end_scene_exposes_q_and_r_mismatch_and_exact_recovery(self) -> None:
        truth, measurements = deterministic_scene()
        initial = [measurements[0], 0.0]
        covariance = [[25.0**2, 0.0], [0.0, 15.0**2]]
        baseline = kalman_filter(measurements, 1.0, 0.8, 25.0, initial, covariance)
        repeated = kalman_filter(measurements, 1.0, 0.8, 25.0, initial, covariance)
        broken_q = kalman_filter(measurements, 1.0, 0.0, 25.0, initial, covariance)
        broken_r = kalman_filter(measurements, 1.0, 0.8, 0.5, initial, covariance)
        evaluation = range(15, len(truth))
        baseline_nis = sum(baseline["innovations"][i] ** 2 / baseline["innovation_variances"][i] for i in evaluation) / len(evaluation)
        broken_r_nis = sum(broken_r["innovations"][i] ** 2 / broken_r["innovation_variances"][i] for i in evaluation) / len(evaluation)
        self.assertLess(broken_q["gains"][-1][0], baseline["gains"][-1][0])
        self.assertLess(broken_q["gains"][-1][1], baseline["gains"][-1][1])
        self.assertGreater(broken_r_nis, 5 * baseline_nis)
        self.assertEqual(repeated, baseline)

    def test_under_q_failure_exposes_velocity_covariance_overconfidence(self) -> None:
        truth, measurements = deterministic_scene()
        initial = [measurements[0], 0.0]
        covariance = [[25.0**2, 0.0], [0.0, 15.0**2]]
        baseline = kalman_filter(measurements, 1.0, 0.8, 25.0, initial, covariance)
        broken_q = kalman_filter(measurements, 1.0, 0.0, 25.0, initial, covariance)
        evaluation = range(15, len(truth))

        def velocity_coverage(track: dict[str, list]) -> float:
            contained = sum(
                abs(track["states"][index][1] - truth[index][1])
                <= 2 * math.sqrt(track["variances"][index][1])
                for index in evaluation
            )
            return contained / len(evaluation)

        baseline_coverage = velocity_coverage(baseline)
        broken_q_coverage = velocity_coverage(broken_q)
        self.assertGreater(baseline_coverage, 0.5)
        self.assertLess(broken_q_coverage, baseline_coverage)

    def test_reviewed_baseline_smooths_reports_and_meets_consistency_condition(self) -> None:
        truth, measurements = deterministic_scene()
        initial = [measurements[0], 0.0]
        covariance = [[25.0**2, 0.0], [0.0, 15.0**2]]
        baseline = kalman_filter(
            measurements, 1.0, 0.8, 25.0, initial, covariance
        )
        evaluation = range(15, len(truth))
        measurement_error = [
            measurements[index] - truth[index][0] for index in evaluation
        ]
        position_error = [
            baseline["states"][index][0] - truth[index][0]
            for index in evaluation
        ]
        velocity_error = [
            baseline["states"][index][1] - truth[index][1]
            for index in evaluation
        ]
        position_coverage = sum(
            abs(error) <= 2 * math.sqrt(baseline["variances"][index][0])
            for error, index in zip(position_error, evaluation)
        ) / len(position_error)
        velocity_coverage = sum(
            abs(error) <= 2 * math.sqrt(baseline["variances"][index][1])
            for error, index in zip(velocity_error, evaluation)
        ) / len(velocity_error)
        innovation_coverage = sum(
            abs(baseline["innovations"][index])
            <= 2 * math.sqrt(baseline["innovation_variances"][index])
            for index in evaluation
        ) / len(position_error)

        self.assertLess(rms(position_error), rms(measurement_error))
        self.assertGreater(position_coverage, 0.5)
        self.assertGreater(velocity_coverage, 0.5)
        self.assertGreater(innovation_coverage, 0.5)
        self.assertTrue(
            all(
                math.isfinite(variance) and variance >= 0
                for index in evaluation
                for variance in baseline["variances"][index]
            )
        )
        self.assertTrue(
            all(
                math.isfinite(baseline["innovation_variances"][index])
                and baseline["innovation_variances"][index] > 0
                for index in evaluation
            )
        )

    def test_source_is_seeded_explicit_bounded_and_mutation_sensitive(self) -> None:
        self.assertEqual(source_binding_errors(self.source), [])
        mutations = (
            self.source.replace("F_local*state_estimate", "F_local+state_estimate", 1),
            self.source.replace("measurement_m(sample_index) - ...", "measurement_m(sample_index) + ...", 1),
            self.source.replace("+ R_local;", "- R_local;", 1),
            self.source.replace("/innovation_variance(sample_index)", "*innovation_variance(sample_index)", 1),
            self.source.replace("joseph_factor*covariance_prediction", "identity_state*covariance_prediction", 1),
            self.source.replace("measurement_std_m <= 0", "measurement_std_m < 0"),
            self.source.replace("any(eig(initial_covariance) < -1e-12)", "false", 1),
            self.source.replace("baseline_velocity_coverage > 0.5", "true", 1),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation[:60]):
                self.assertTrue(source_binding_errors(mutation))
        self.assertLess(self.source.index("reviewed_filter_steps > maximum_filter_steps"), self.source.index("private_stream ="))
        self.assertLess(self.source.index("reviewed_filter_steps > maximum_filter_steps"), self.source.index("true_state = zeros"))

    def test_sweeps_failures_metrics_figures_and_resources_are_visible(self) -> None:
        self.assertEqual(self.source.count("figure('Name', 'P55 Figure"), 5)
        self.assertEqual(self.source.count("'Tag', 'P55'"), 6)
        self.assertIn("process_std_sweep_mps2(sweep_index), assumed_measurement_std_m", self.source)
        self.assertIn("assumed_process_acceleration_std_mps2, ...\n        measurement_std_sweep_m(sweep_index)", self.source)
        self.assertIn("broken_q = run_cv_kalman", self.source)
        self.assertIn("broken_r = run_cv_kalman", self.source)
        self.assertIn("recovered = run_cv_kalman", self.source)
        for unit in ("Position (m)", "Velocity (m/s)", "Innovation (m)", "Velocity gain (1/s)"):
            self.assertIn(unit, self.source)
        for metric in (
            "baseline_position_rmse_m", "baseline_velocity_rmse_mps",
            "baseline_position_coverage", "baseline_innovation_coverage",
            "baseline_mean_nis", "broken_q_position_coverage",
            "broken_q_velocity_coverage", "broken_r_mean_nis",
            "reviewed_filter_steps",
        ):
            self.assertIn(metric, self.source)

    def test_docs_cover_model_dependencies_sweeps_failure_recovery_and_claim_boundary(self) -> None:
        combined = "\n".join((self.readme, self.lesson, self.walkthrough, self.checks))
        for marker in (
            QUESTION, "P54", "P56", "P57", "F =", "G =", "H =", "Q =", "R =",
            "Joseph", "innovation", "Kalman gain", "two-sigma", "NIS", "Q sweep",
            "R sweep", "under-Q", "under-R", "recovery", "Correct:", "Incorrect:",
            "Ctrl+C", "10-second", "rollback", "R2016b", "one seeded",
            "MATLAB execution", "hardware/HIL", "field",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(combined.count("**Correct:**"), 12)
        self.assertGreaterEqual(combined.count("**Incorrect:**"), 12)

    def test_no_placeholder_unexplained_black_box_or_side_effect_regression(self) -> None:
        combined = "\n".join((self.source, self.readme, self.lesson, self.walkthrough, self.checks))
        self.assertNotIn("TODO", combined)
        self.assertNotIn("Status:** Scaffolded", combined)
        forbidden = (
            r"\brng\s*\(", r"(?<![A-Za-z])randn\s*\(", r"\binv\s*\(",
            r"\bkalman\s*\(", r"trackingKF", r"configureKalmanFilter",
            r"\bparfor\b", r"\bfopen\s*\(", r"\bwebread\s*\(",
            r"\bsystem\s*\(", r"\bunix\s*\(", r"\btimer\s*\(",
        )
        source_without_private_randn = self.source.replace("randn(private_stream,", "PRIVATE_RANDN(")
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, source_without_private_randn), pattern)
        self.assertNotIn("toolbox convenience", self.source.lower())

    def test_cli_timeout_isolation_rollback_recovery_and_future_compatibility(self) -> None:
        repository_state = ROOT / ".learning" / "progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory) / "repo"
            (fixture_root / "bin").mkdir(parents=True)
            (fixture_root / "curriculum").mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture_root / "bin/learn")
            shutil.copy2(ROOT / "curriculum/modules.json", fixture_root / "curriculum/modules.json")
            fixture_manifest = json.loads((fixture_root / "curriculum/modules.json").read_text())
            for module in fixture_manifest["modules"]:
                destination = fixture_root / module["folder"] / "README.md"
                destination.parent.mkdir(parents=True)
                shutil.copy2(ROOT / module["folder"] / "README.md", destination)
            environment = os.environ.copy()
            environment["HOME"] = temporary_directory
            process = subprocess.run(
                [str(fixture_root / "bin/learn"), "start", "55"],
                cwd=fixture_root, env=environment, text=True, capture_output=True,
                timeout=10,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("P55", process.stdout)
            self.assertIn("Tutor entry", process.stdout)
            original = copy.deepcopy(fixture_manifest)
            p55 = next(entry for entry in fixture_manifest["modules"] if entry["id"] == "P55")
            p55["status"] = "scaffolded"
            changed = [
                (before_entry["id"], key)
                for before_entry, after_entry in zip(original["modules"], fixture_manifest["modules"])
                for key in before_entry
                if before_entry.get(key) != after_entry.get(key)
            ]
            self.assertEqual(changed, [("P55", "status")])
            p54_before = next(entry for entry in original["modules"] if entry["id"] == "P54")
            p54_after = next(entry for entry in fixture_manifest["modules"] if entry["id"] == "P54")
            p56_before = next(entry for entry in original["modules"] if entry["id"] == "P56")
            p56_after = next(entry for entry in fixture_manifest["modules"] if entry["id"] == "P56")
            self.assertEqual(p54_after, p54_before)
            self.assertEqual(p56_after, p56_before)
            manifest_path = fixture_root / "curriculum/modules.json"
            manifest_path.write_text(json.dumps(fixture_manifest, indent=2) + "\n", encoding="utf-8")
            rolled_back = subprocess.run(
                [str(fixture_root / "bin/learn"), "start", "55"],
                cwd=fixture_root, env=environment, text=True, capture_output=True,
                timeout=10,
            )
            self.assertEqual(rolled_back.returncode, 3)
            self.assertIn("awaits Portfolio batch P55", rolled_back.stdout)
            manifest_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
            recovered = subprocess.run(
                [str(fixture_root / "bin/learn"), "start", "55"],
                cwd=fixture_root, env=environment, text=True, capture_output=True,
                timeout=10,
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertIn("Tutor entry", recovered.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_public_catalogs_describe_p55_without_freezing_future_state(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 55 follows P54 by propagating position, velocity, and covariance", root_readme)
        self.assertIn("Project 55 follows P54 by replacing fixed gains", start_here)
        self.assertRegex(module_index, r"\| \[P55\].*\| implemented \|")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self) -> None:
        evidence_files = sorted((ROOT / "docs/evidence").glob("P55-*.md"))
        self.assertEqual(len(evidence_files), 1)
        payload = evidence_files[0].read_bytes()
        self.assertTrue(payload.endswith(b"\n"))
        self.assertFalse(payload.endswith(b"\n\n"))
        evidence = payload.decode("utf-8")
        for heading in (
            "## Scope and claim boundary", "## Acceptance mapping",
            "## Figure and metric inventory", "## Exact commands and results",
            "## Changed and preserved invariants", "## Residual risks",
            "## Rollback and recovery", "## Unperformed validation",
        ):
            self.assertIn(heading, evidence)
        for command in (
            "python3 -m unittest tests.test_p55_module -v",
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
            "git diff --check",
        ):
            self.assertIn(command, evidence)
        self.assertIn("MATLAB and Octave did not run", evidence)
        self.assertIn("No hardware/HIL, field, real-time, deployment, or production", evidence)


if __name__ == "__main__":
    unittest.main()
