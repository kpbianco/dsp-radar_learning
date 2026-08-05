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
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/56-use-an-ekf-for-range-bearing-measurements"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How can nonlinear radar measurements update Cartesian target state?"
EXPECTED_IDENTITY = {
    "number": 56,
    "id": "P56",
    "title": "Use an EKF for Range-Bearing Measurements",
    "guiding_question": QUESTION,
    "phase": 6,
    "phase_title": "Radar Tracking and Data Association",
    "slug": "use-an-ekf-for-range-bearing-measurements",
    "folder": "modules/56-use-an-ekf-for-range-bearing-measurements",
    "status": "implemented",
    "implementation_batch": "P56",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def validate_p56_contract(module: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P56 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P56 empty {artifact}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P56"]
    if len(entries) != 1:
        return errors + [f"expected one P56 manifest entry, found {len(entries)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if entries[0].get(key) != expected:
            errors.append(f"P56 {key} mismatch")
    return errors


def canonical_controls() -> dict[str, object]:
    return {
        "seed": 5601,
        "number_scans": 101,
        "dt": 1.0,
        "initial_x": -1600.0,
        "initial_vx": 4.0,
        "initial_y": 600.0,
        "initial_vy": -12.0,
        "actual_q_std": 0.25,
        "actual_range_std": 18.0,
        "actual_bearing_std_deg": 0.8,
        "assumed_q_std": 0.25,
        "assumed_range_std": 18.0,
        "assumed_bearing_std_deg": 0.8,
        "initial_velocity_std": 20.0,
        "warmup": 15,
        "bearing_sweep": (0.2, 0.8, 3.2),
        "geometry_sweep": (500.0, 1500.0, 3000.0),
        "minimum_range": 25.0,
        "max_scans": 200,
        "max_sweep_cases": 5,
        "max_figures": 5,
        "max_updates": 700,
        "ellipse_points": 73,
        "max_ellipse_points": 73,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError("unknown control")
    controls.update(overrides)
    for name in (
        "seed", "number_scans", "warmup", "max_scans", "max_sweep_cases",
        "max_figures", "max_updates", "ellipse_points", "max_ellipse_points",
    ):
        if not integer(controls[name]):
            raise ValueError(f"integer control {name}")
    for name in (
        "dt", "initial_x", "initial_vx", "initial_y", "initial_vy",
        "actual_q_std", "actual_range_std", "actual_bearing_std_deg",
        "assumed_q_std", "assumed_range_std", "assumed_bearing_std_deg",
        "initial_velocity_std", "minimum_range",
    ):
        if not finite_real(controls[name]):
            raise ValueError(f"real control {name}")
    fixed = {
        "seed": 5601, "number_scans": 101, "dt": 1.0,
        "initial_x": -1600.0, "initial_vx": 4.0,
        "initial_y": 600.0, "initial_vy": -12.0,
        "actual_q_std": 0.25, "actual_range_std": 18.0,
        "actual_bearing_std_deg": 0.8, "assumed_q_std": 0.25,
        "assumed_range_std": 18.0, "assumed_bearing_std_deg": 0.8,
        "minimum_range": 25.0, "max_scans": 200,
        "max_sweep_cases": 5, "max_figures": 5, "max_updates": 700,
        "ellipse_points": 73, "max_ellipse_points": 73,
    }
    if any(controls[name] != expected for name, expected in fixed.items()):
        raise ValueError("reviewed control drift")
    if controls["number_scans"] > controls["max_scans"]:
        raise ValueError("scan bound")
    if not 1 <= controls["warmup"] < controls["number_scans"] - 2:
        raise ValueError("warm-up domain")
    if controls["initial_velocity_std"] <= 0:
        raise ValueError("initial uncertainty")
    for name, baseline in (
        ("bearing_sweep", controls["assumed_bearing_std_deg"]),
        ("geometry_sweep", 1500.0),
    ):
        values = controls[name]
        if not isinstance(values, (tuple, list)) or not 3 <= len(values) <= controls["max_sweep_cases"]:
            raise ValueError("sweep shape")
        if not all(finite_real(value) and value > 0 for value in values):
            raise ValueError("sweep domain")
        if any(right <= left for left, right in zip(values, values[1:])) or baseline not in values:
            raise ValueError("sweep ordering/baseline")
    run_count = 1 + len(controls["bearing_sweep"]) + 1 + 1
    if run_count * (controls["number_scans"] - 1) > controls["max_updates"]:
        raise ValueError("filter-update bound")


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(column) for column in zip(*matrix)]


def matmul(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    return [
        [
            sum(left[row][k] * right[k][column] for k in range(len(right)))
            for column in range(len(right[0]))
        ]
        for row in range(len(left))
    ]


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(value * vector[index] for index, value in enumerate(row)) for row in matrix]


def inverse_2x2(matrix: list[list[float]]) -> list[list[float]]:
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    if not math.isfinite(determinant) or determinant <= 0:
        raise ValueError("innovation covariance")
    return [
        [matrix[1][1] / determinant, -matrix[0][1] / determinant],
        [-matrix[1][0] / determinant, matrix[0][0] / determinant],
    ]


def determinant(matrix: list[list[float]]) -> float:
    work = [[float(value) for value in row] for row in matrix]
    result = 1.0
    for column in range(len(work)):
        pivot = max(range(column, len(work)), key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) < 1e-14:
            return 0.0
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            result = -result
        pivot_value = work[column][column]
        result *= pivot_value
        for row in range(column + 1, len(work)):
            scale = work[row][column] / pivot_value
            for entry in range(column + 1, len(work)):
                work[row][entry] -= scale * work[column][entry]
    return result


def wrap_angle(angle: float) -> float:
    if not finite_real(angle):
        raise ValueError("angle")
    return math.atan2(math.sin(angle), math.cos(angle))


def measurement_model(state: list[float], minimum_range: float) -> tuple[list[float], list[list[float]]]:
    px, _, py, _ = state
    squared_range = px * px + py * py
    if squared_range <= minimum_range * minimum_range:
        raise ValueError("linearization singularity")
    range_m = math.sqrt(squared_range)
    measurement = [range_m, math.atan2(py, px)]
    jacobian = [
        [px / range_m, 0.0, py / range_m, 0.0],
        [-py / squared_range, 0.0, px / squared_range, 0.0],
    ]
    return measurement, jacobian


def validate_ekf_inputs(
    measurements: object,
    dt: object,
    q_std: object,
    range_std: object,
    bearing_std_deg: object,
    initial_state: object,
    initial_covariance: object,
    minimum_range: object,
    wrap_innovation: object,
) -> None:
    if (
        not isinstance(measurements, (tuple, list))
        or len(measurements) < 2
        or any(not isinstance(row, (tuple, list)) or len(row) != 2 for row in measurements)
        or any(not finite_real(value) for row in measurements for value in row)
        or any(row[0] <= 0 or row[1] < -math.pi or row[1] > math.pi for row in measurements)
    ):
        raise ValueError("measurement")
    if (
        not finite_real(dt) or dt <= 0
        or not finite_real(q_std) or q_std < 0
        or not finite_real(range_std) or range_std <= 0
        or not finite_real(bearing_std_deg) or bearing_std_deg <= 0
        or not finite_real(minimum_range) or minimum_range <= 0
    ):
        raise ValueError("noise model")
    if (
        not isinstance(initial_state, (tuple, list))
        or len(initial_state) != 4
        or any(not finite_real(value) for value in initial_state)
        or math.hypot(initial_state[0], initial_state[2]) <= minimum_range
    ):
        raise ValueError("state")
    if (
        not isinstance(initial_covariance, (tuple, list))
        or len(initial_covariance) != 4
        or any(not isinstance(row, (tuple, list)) or len(row) != 4 for row in initial_covariance)
        or any(not finite_real(value) for row in initial_covariance for value in row)
    ):
        raise ValueError("covariance")
    for row in range(4):
        if initial_covariance[row][row] < 0:
            raise ValueError("covariance diagonal")
        for column in range(4):
            if abs(initial_covariance[row][column] - initial_covariance[column][row]) > 1e-10:
                raise ValueError("covariance symmetry")
    for size in range(1, 5):
        for indices in combinations(range(4), size):
            principal = [[initial_covariance[row][column] for column in indices] for row in indices]
            if determinant(principal) < -1e-9:
                raise ValueError("covariance PSD")
    if not isinstance(wrap_innovation, bool):
        raise ValueError("wrap control")


def ekf_filter(
    measurements: object,
    dt: object,
    q_std: object,
    range_std: object,
    bearing_std_deg: object,
    initial_state: object,
    initial_covariance: object,
    minimum_range: object,
    wrap_innovation: object,
) -> dict[str, list]:
    validate_ekf_inputs(
        measurements, dt, q_std, range_std, bearing_std_deg, initial_state,
        initial_covariance, minimum_range, wrap_innovation,
    )
    measurements = [[float(value) for value in row] for row in measurements]
    dt = float(dt)
    f = [
        [1.0, dt, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, dt], [0.0, 0.0, 0.0, 1.0],
    ]
    g = [
        [0.5 * dt * dt, 0.0], [dt, 0.0],
        [0.0, 0.5 * dt * dt], [0.0, dt],
    ]
    q = [[q_std * q_std * value for value in row] for row in matmul(g, transpose(g))]
    bearing_std_rad = bearing_std_deg * math.pi / 180.0
    r_cov = [[range_std * range_std, 0.0], [0.0, bearing_std_rad * bearing_std_rad]]
    identity = [[float(row == column) for column in range(4)] for row in range(4)]
    p = [[float(value) for value in row] for row in initial_covariance]
    states = [[float(value) for value in initial_state]]
    predictions = [states[0][:]]
    covariances = [[row[:] for row in p]]
    innovations = [[math.nan, math.nan]]
    innovation_covariances = [None]
    gains = [None]
    nis = [math.nan]

    for polar_report in measurements[1:]:
        predicted = matvec(f, states[-1])
        predicted_p = matmul(matmul(f, p), transpose(f))
        predicted_p = [
            [predicted_p[row][column] + q[row][column] for column in range(4)]
            for row in range(4)
        ]
        predicted_report, h = measurement_model(predicted, float(minimum_range))
        innovation = [
            polar_report[0] - predicted_report[0],
            polar_report[1] - predicted_report[1],
        ]
        if wrap_innovation:
            innovation[1] = wrap_angle(innovation[1])
        s = matmul(matmul(h, predicted_p), transpose(h))
        s = [[s[row][column] + r_cov[row][column] for column in range(2)] for row in range(2)]
        inverse_s = inverse_2x2(s)
        gain = matmul(matmul(predicted_p, transpose(h)), inverse_s)
        correction = matvec(gain, innovation)
        corrected = [predicted[index] + correction[index] for index in range(4)]
        kh = matmul(gain, h)
        joseph_factor = [
            [identity[row][column] - kh[row][column] for column in range(4)]
            for row in range(4)
        ]
        p = matmul(matmul(joseph_factor, predicted_p), transpose(joseph_factor))
        krkt = matmul(matmul(gain, r_cov), transpose(gain))
        p = [[p[row][column] + krkt[row][column] for column in range(4)] for row in range(4)]
        p = [[0.5 * (p[row][column] + p[column][row]) for column in range(4)] for row in range(4)]
        weighted_innovation = matvec(inverse_s, innovation)
        nis_value = sum(left * right for left, right in zip(innovation, weighted_innovation))

        predictions.append(predicted)
        states.append(corrected)
        covariances.append([[value for value in row] for row in p])
        innovations.append(innovation)
        innovation_covariances.append(s)
        gains.append(gain)
        nis.append(nis_value)
    return {
        "states": states,
        "predictions": predictions,
        "covariances": covariances,
        "innovations": innovations,
        "innovation_covariances": innovation_covariances,
        "gains": gains,
        "nis": nis,
    }


def deterministic_scene() -> tuple[list[list[float]], list[list[float]], list[list[float]]]:
    truth = [[-1600.0, 4.0, 600.0, -12.0]]
    for index in range(60):
        ax = 0.25 * (((index * 7) % 9) - 4) / 4
        ay = 0.25 * (((index * 5) % 11) - 5) / 5
        px, vx, py, vy = truth[-1]
        truth.append([
            px + vx + 0.5 * ax, vx + ax,
            py + vy + 0.5 * ay, vy + ay,
        ])
    measurements: list[list[float]] = []
    raw_cartesian: list[list[float]] = []
    for index, state in enumerate(truth):
        range_noise = float((((index * 13) % 17) - 8) * 2.25)
        bearing_noise = 0.8 * math.pi / 180 * ((((index * 11) % 13) - 6) / 3)
        range_m = math.hypot(state[0], state[2]) + range_noise
        bearing = wrap_angle(math.atan2(state[2], state[0]) + bearing_noise)
        measurements.append([range_m, bearing])
        raw_cartesian.append([range_m * math.cos(bearing), range_m * math.sin(bearing)])
    return truth, measurements, raw_cartesian


def initial_conditions(measurements: list[list[float]]) -> tuple[list[float], list[list[float]]]:
    range_m, bearing = measurements[0]
    state = [range_m * math.cos(bearing), 0.0, range_m * math.sin(bearing), 0.0]
    range_variance = 18.0**2
    bearing_variance = (0.8 * math.pi / 180) ** 2
    jacobian = [
        [math.cos(bearing), -range_m * math.sin(bearing)],
        [math.sin(bearing), range_m * math.cos(bearing)],
    ]
    polar_covariance = [[range_variance, 0.0], [0.0, bearing_variance]]
    position_covariance = matmul(matmul(jacobian, polar_covariance), transpose(jacobian))
    covariance = [[0.0] * 4 for _ in range(4)]
    covariance[0][0] = position_covariance[0][0]
    covariance[0][2] = position_covariance[0][1]
    covariance[2][0] = position_covariance[1][0]
    covariance[2][2] = position_covariance[1][1]
    covariance[1][1] = 20.0**2
    covariance[3][3] = 20.0**2
    return state, covariance


def rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values))


def source_binding_errors(source: str) -> list[str]:
    required = (
        "random_seed = 5601;",
        "number_scans = 101;",
        "initial_true_x_m = -1600;",
        "initial_true_vx_mps = 4;",
        "initial_true_y_m = 600;",
        "initial_true_vy_mps = -12;",
        "actual_process_acceleration_std_mps2 = 0.25;",
        "actual_range_std_m = 18;",
        "actual_bearing_std_deg = 0.8;",
        "bearing_std_sweep_deg = [0.2 0.8 3.2];",
        "geometry_range_sweep_m = [500 1500 3000];",
        "minimum_linearization_range_m = 25;",
        "maximum_filter_updates = 700;",
        "reviewed_filter_updates = filter_run_count*(number_scans - 1);",
        "ellipse_point_count = 73;",
        "private_stream = RandStream('mt19937ar', 'Seed', random_seed);",
        "predicted_measurement(:, sample_index) = [predicted_range_m; ...",
        "atan2(predicted_y_m, predicted_x_m)];",
        "predicted_x_m/predicted_range_m 0 ...",
        "-predicted_y_m/predicted_range_squared_m2 0 ...",
        "innovation(:, sample_index) = measurement(:, sample_index) - ...",
        "innovation(2, sample_index) = atan2( ...",
        "H_local*covariance_prediction*H_local' + R_local;",
        "det(current_innovation_covariance) <= 0",
        "(covariance_prediction*H_local')/ ...",
        "state_estimate(:, sample_index) = state_prediction(:, sample_index) + ...",
        "joseph_factor = identity_state - kalman_gain(:, :, sample_index)*H_local;",
        "covariance_estimate = joseph_factor*covariance_prediction*joseph_factor' + ...",
        "covariance_estimate = 0.5*(covariance_estimate + covariance_estimate');",
        "predicted_range_squared_m2 <= minimum_range_m^2",
        "any(measurement(1, :) <= 0)",
        "any(measurement(1, :) > maximum_supported_range_m)",
        "any(measurement(2, :) < -pi | measurement(2, :) > pi)",
        "~isa(measurement, 'double')",
        "~isa(sample_interval_s, 'double')",
        "~isa(initial_state, 'double')",
        "~isa(initial_covariance, 'double')",
        "any(eig(initial_covariance) < -1e-10)",
        "any(eig(covariance_estimate) < -1e-8)",
        "any(~isfinite(state_estimate(:, sample_index)))",
        "~isfinite(nis(sample_index)) || nis(sample_index) < 0",
        "reviewed_filter_updates == 600;",
        "baseline_position_coverage > 0.5",
        "broken_max_bearing_innovation_deg > 180",
        "results.geometry_tangential_sigma_m = geometry_tangential_sigma_m;",
        "results.broken_position_rmse_m = broken_position_rmse_m;",
    )
    errors = [marker for marker in required if marker not in source]
    try:
        operation = source[
            source.index("function track = run_range_bearing_ekf"):
            source.index("function validate_filter_inputs")
        ]
    except ValueError:
        return errors + ["EKF operation boundary"]
    for marker in (
        "state_prediction(:, sample_index) =",
        "predicted_measurement(:, sample_index) =",
        "innovation(:, sample_index) =",
        "kalman_gain(:, :, sample_index) =",
        "state_estimate(:, sample_index) =",
        "covariance_estimate = joseph_factor*covariance_prediction",
    ):
        if operation.count(marker) != 1:
            errors.append(f"single operation: {marker}")
    return errors


class P56ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self) -> None:
        self.assertEqual(validate_p56_contract(MODULE, self.manifest), [])
        p55 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P55")
        self.assertEqual(p55["status"], "implemented")
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
            self.assertIn("P56 missing lesson.md", validate_p56_contract(fixture, self.manifest))
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P56 empty lesson.md", validate_p56_contract(fixture, self.manifest))
        for malformed in (None, [], {}, {"modules": None}, {"modules": ["P56"]}):
            self.assertTrue(validate_p56_contract(MODULE, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P56 manifest entry, found 2", validate_p56_contract(MODULE, duplicate))
        for key in EXPECTED_IDENTITY:
            drifted = copy.deepcopy(self.manifest)
            entry = next(item for item in drifted["modules"] if item["id"] == "P56")
            entry[key] = -1 if isinstance(entry[key], int) else "drift"
            self.assertTrue(validate_p56_contract(MODULE, drifted), key)

    def test_controls_accept_reviewed_and_reject_malformed_or_unbounded_values(self) -> None:
        validate_controls()
        bad_cases = (
            {"unknown": 1}, {"seed": True}, {"seed": 5602},
            {"number_scans": 100}, {"number_scans": 101.5}, {"dt": 0},
            {"initial_x": -1599}, {"initial_vx": math.nan},
            {"initial_y": 599}, {"initial_vy": complex(1, 1)},
            {"actual_q_std": complex(1, 1)}, {"actual_range_std": 0},
            {"actual_bearing_std_deg": math.inf}, {"assumed_q_std": -1},
            {"assumed_range_std": math.nan}, {"assumed_bearing_std_deg": 0},
            {"initial_velocity_std": 0}, {"warmup": 0}, {"warmup": 99},
            {"minimum_range": 0}, {"bearing_sweep": (0.2, 0.8)},
            {"bearing_sweep": (0.2, 0.2, 3.2)},
            {"bearing_sweep": (0.2, 0.7, 3.2)},
            {"geometry_sweep": (500, math.inf, 3000)},
            {"geometry_sweep": (500, 3000, 1500)},
            {"max_scans": 201}, {"max_sweep_cases": 6},
            {"max_figures": 6}, {"max_updates": 599},
            {"ellipse_points": 72}, {"max_ellipse_points": 74},
        )
        for controls in bad_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)
        with self.assertRaisesRegex(ValueError, "filter-update bound"):
            validate_controls(bearing_sweep=(0.1, 0.2, 0.8, 1.6, 3.2))

    def test_measurement_model_jacobian_signs_units_and_finite_difference(self) -> None:
        predicted, jacobian = measurement_model([3.0, 7.0, 4.0, -2.0], 0.1)
        self.assertEqual(predicted, [5.0, math.atan2(4.0, 3.0)])
        expected = [[0.6, 0.0, 0.8, 0.0], [-0.16, 0.0, 0.12, 0.0]]
        for row in range(2):
            for column in range(4):
                self.assertAlmostEqual(jacobian[row][column], expected[row][column])
        epsilon = 1e-6
        for state_index in (0, 2):
            plus = [3.0, 7.0, 4.0, -2.0]
            minus = plus[:]
            plus[state_index] += epsilon
            minus[state_index] -= epsilon
            h_plus, _ = measurement_model(plus, 0.1)
            h_minus, _ = measurement_model(minus, 0.1)
            for measurement_index in range(2):
                derivative = (h_plus[measurement_index] - h_minus[measurement_index]) / (2 * epsilon)
                self.assertAlmostEqual(derivative, jacobian[measurement_index][state_index], places=6)

    def test_wrapped_branch_cut_is_local_and_unwrapped_failure_is_large(self) -> None:
        initial_bearing = math.radians(179.0)
        range_m = 1000.0
        initial_state = [range_m * math.cos(initial_bearing), 0.0, range_m * math.sin(initial_bearing), 0.0]
        covariance = [[0.0] * 4 for _ in range(4)]
        for index, variance in enumerate((100.0, 25.0, 100.0, 25.0)):
            covariance[index][index] = variance
        measurements = [[range_m, initial_bearing], [range_m, math.radians(-179.0)]]
        wrapped = ekf_filter(measurements, 1.0, 0.0, 10.0, 1.0, initial_state, covariance, 25.0, True)
        broken = ekf_filter(measurements, 1.0, 0.0, 10.0, 1.0, initial_state, covariance, 25.0, False)
        self.assertAlmostEqual(math.degrees(wrapped["innovations"][1][1]), 2.0)
        self.assertAlmostEqual(math.degrees(broken["innovations"][1][1]), -358.0)
        wrapped_move = math.hypot(
            wrapped["states"][1][0] - wrapped["predictions"][1][0],
            wrapped["states"][1][2] - wrapped["predictions"][1][2],
        )
        broken_move = math.hypot(
            broken["states"][1][0] - broken["predictions"][1][0],
            broken["states"][1][2] - broken["predictions"][1][2],
        )
        self.assertGreater(broken_move, 100 * wrapped_move)

    def test_oracle_rejects_malformed_inputs_and_near_origin_geometry(self) -> None:
        good = (
            [[1000.0, 0.1], [1001.0, 0.11]], 1.0, 0.25, 18.0, 0.8,
            [995.0, 1.0, 100.0, 0.0],
            [[100.0, 0.0, 0.0, 0.0], [0.0, 25.0, 0.0, 0.0],
             [0.0, 0.0, 100.0, 0.0], [0.0, 0.0, 0.0, 25.0]],
            25.0, True,
        )
        bad_args = (
            ([], *good[1:]), ([[1.0, 0.0]], *good[1:]),
            ([[1.0, 0.0], [math.nan, 0.0]], *good[1:]),
            ([[0.0, 0.0], [1.0, 0.0]], *good[1:]),
            ([[1.0, 4.0], [1.0, 0.0]], *good[1:]),
            (good[0], True, *good[2:]), (good[0], 0.0, *good[2:]),
            (*good[:2], -0.1, *good[3:]), (*good[:3], 0.0, *good[4:]),
            (*good[:4], 0.0, *good[5:]), (*good[:5], [1.0], *good[6:]),
            (*good[:5], [1.0, 0.0, 1.0, 0.0], *good[6:]),
            (*good[:6], [[1.0]], *good[7:]),
            (*good[:6], [[1.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
                         [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]], *good[7:]),
            (*good[:6], [[1.0, 0.0, 2.0, 0.0], [0.0, 1.0, 0.0, 0.0],
                         [2.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]], *good[7:]),
            (*good[:7], 0.0, good[8]), (*good[:8], 1),
        )
        for args in bad_args:
            with self.subTest(args=str(args)[:100]), self.assertRaises(ValueError):
                ekf_filter(*args)
        with self.assertRaises(ValueError):
            measurement_model([10.0, 0.0, 10.0, 0.0], 25.0)

    def test_geometry_range_sweep_and_bearing_noise_change_tangential_uncertainty(self) -> None:
        bearing_std_rad = math.radians(0.8)
        tangential = [range_m * bearing_std_rad for range_m in (500.0, 1500.0, 3000.0)]
        self.assertAlmostEqual(tangential[1], 3 * tangential[0])
        self.assertAlmostEqual(tangential[2], 2 * tangential[1])
        self.assertEqual([18.0] * 3, [18.0 for _ in tangential])

        truth, measurements, _ = deterministic_scene()
        initial_state, covariance = initial_conditions(measurements)
        narrow = ekf_filter(measurements, 1.0, 0.25, 18.0, 0.2, initial_state, covariance, 25.0, True)
        wide = ekf_filter(measurements, 1.0, 0.25, 18.0, 3.2, initial_state, covariance, 25.0, True)
        index = len(truth) - 1
        radial = [truth[index][0], truth[index][2]]
        norm = math.hypot(*radial)
        tangent = [-radial[1] / norm, radial[0] / norm]

        def projected_variance(track: dict[str, list]) -> float:
            p = track["covariances"][index]
            position_p = [[p[0][0], p[0][2]], [p[2][0], p[2][2]]]
            return sum(
                tangent[row] * position_p[row][column] * tangent[column]
                for row in range(2) for column in range(2)
            )

        self.assertGreater(projected_variance(wide), projected_variance(narrow))

    def test_bearing_noise_sweep_exposes_overconfidence_in_nis_on_same_reports(self) -> None:
        _, measurements, _ = deterministic_scene()
        initial_state, covariance = initial_conditions(measurements)
        mean_nis: dict[float, float] = {}
        for bearing_std_deg in (0.2, 0.8, 3.2):
            track = ekf_filter(
                measurements, 1.0, 0.25, 18.0, bearing_std_deg,
                initial_state, covariance, 25.0, True,
            )
            evaluated_nis = track["nis"][15:]
            mean_nis[bearing_std_deg] = sum(evaluated_nis) / len(evaluated_nis)

        self.assertGreater(mean_nis[0.2], 5 * mean_nis[0.8])
        self.assertGreater(mean_nis[0.8], 2 * mean_nis[3.2])

    def test_end_to_end_baseline_smooths_reports_is_finite_and_recovers_exactly(self) -> None:
        truth, measurements, raw = deterministic_scene()
        initial_state, covariance = initial_conditions(measurements)
        baseline = ekf_filter(measurements, 1.0, 0.25, 18.0, 0.8, initial_state, covariance, 25.0, True)
        recovered = ekf_filter(measurements, 1.0, 0.25, 18.0, 0.8, initial_state, covariance, 25.0, True)
        broken = ekf_filter(measurements, 1.0, 0.25, 18.0, 0.8, initial_state, covariance, 25.0, False)
        evaluation = range(15, len(truth))
        raw_errors = [math.hypot(raw[i][0] - truth[i][0], raw[i][1] - truth[i][2]) for i in evaluation]
        baseline_errors = [
            math.hypot(baseline["states"][i][0] - truth[i][0], baseline["states"][i][2] - truth[i][2])
            for i in evaluation
        ]
        broken_errors = [
            math.hypot(broken["states"][i][0] - truth[i][0], broken["states"][i][2] - truth[i][2])
            for i in evaluation
        ]
        self.assertLess(rms(baseline_errors), rms(raw_errors))
        self.assertGreater(rms(broken_errors), rms(baseline_errors))
        self.assertEqual(recovered, baseline)
        self.assertLessEqual(max(abs(baseline["innovations"][i][1]) for i in evaluation), math.pi)
        self.assertGreater(max(abs(broken["innovations"][i][1]) for i in evaluation), math.pi)
        for index in evaluation:
            self.assertTrue(all(math.isfinite(value) for value in baseline["states"][index]))
            self.assertTrue(math.isfinite(baseline["nis"][index]) and baseline["nis"][index] >= 0)
            s = baseline["innovation_covariances"][index]
            self.assertGreater(s[0][0] * s[1][1] - s[0][1] * s[1][0], 0)
            p = baseline["covariances"][index]
            self.assertTrue(all(math.isfinite(value) for row in p for value in row))
            self.assertTrue(all(p[diagonal][diagonal] >= 0 for diagonal in range(4)))

    def test_source_is_seeded_explicit_bounded_and_mutation_sensitive(self) -> None:
        self.assertEqual(source_binding_errors(self.source), [])
        mutations = (
            self.source.replace("predicted_x_m/predicted_range_m", "predicted_x_m*predicted_range_m", 1),
            self.source.replace("-predicted_y_m/predicted_range_squared_m2", "predicted_y_m/predicted_range_squared_m2", 1),
            self.source.replace("measurement(:, sample_index) - ...", "measurement(:, sample_index) + ...", 1),
            self.source.replace("innovation(2, sample_index) = atan2( ...", "innovation(2, sample_index) = ( ...", 1),
            self.source.replace("+ R_local;", "- R_local;", 1),
            self.source.replace("joseph_factor*covariance_prediction", "identity_state*covariance_prediction", 1),
            self.source.replace("any(eig(initial_covariance) < -1e-10)", "false", 1),
            self.source.replace("det(current_innovation_covariance) <= 0", "false", 1),
            self.source.replace("any(eig(covariance_estimate) < -1e-8)", "false", 1),
            self.source.replace("number_scans - 1", "number_scans", 1),
            self.source.replace("broken_max_bearing_innovation_deg > 180", "true", 1),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation[:60]):
                self.assertTrue(source_binding_errors(mutation))
        bound = self.source.index("reviewed_filter_updates > maximum_filter_updates")
        self.assertLess(bound, self.source.index("private_stream ="))
        self.assertLess(bound, self.source.index("true_state = zeros"))

    def test_sweeps_broken_recovery_metrics_figures_and_resources_are_visible(self) -> None:
        self.assertEqual(self.source.count("figure('Name', 'P56 Figure"), 5)
        self.assertEqual(self.source.count("'Tag', 'P56'"), 6)
        self.assertIn("bearing_std_sweep_deg(sweep_index), initial_state_estimate", self.source)
        self.assertIn("geometry_tangential_sigma_m = geometry_range_sweep_m*geometry_bearing_std_rad;", self.source)
        self.assertIn("minimum_linearization_range_m, false", self.source)
        self.assertIn("minimum_linearization_range_m, true", self.source)
        self.assertIn("legend([truth_handle raw_handle ekf_handle ellipse_handle radar_handle]", self.source)
        self.assertNotIn("ylabel('Metres or dimensionless')", self.source)
        self.assertIn("ylabel('Tangential sigma (m)')", self.source)
        self.assertIn("ylabel('Mean NIS (dimensionless)')", self.source)
        for unit in (
            "Cartesian x (m)", "Cartesian y (m)", "Range innovation (m)",
            "Wrapped bearing innovation (deg)", "NIS (dimensionless)",
            "Position RMSE (m)", "uncertainty (m)",
        ):
            self.assertIn(unit, self.source)
        for metric in (
            "raw_position_rmse_m", "baseline_position_rmse_m",
            "baseline_position_coverage", "baseline_innovation_coverage",
            "baseline_mean_nis", "baseline_radial_sigma_m",
            "baseline_tangential_sigma_m", "broken_position_rmse_m",
            "broken_max_bearing_innovation_deg", "reviewed_filter_updates",
        ):
            self.assertIn(metric, self.source)

    def test_docs_cover_model_dependencies_limits_failure_recovery_and_claim_boundary(self) -> None:
        combined = "\n".join((self.readme, self.lesson, self.walkthrough, self.checks))
        for marker in (
            QUESTION, "P55", "P57", "P30", "P18", "P27", "h(x)", "H =",
            "Q =", "R =", "Joseph", "Jacobian", "innovation", "NIS",
            "covariance ellipse", "bearing-noise sweep", "geometry sweep",
            "branch cut", "r*sigma", "Near zero range", "Correct:", "Incorrect:",
            "Ctrl+C", "10-second", "rollback", "R2016b", "one seeded",
            "MATLAB execution", "hardware/HIL", "field",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(combined.count("**Correct:**"), 18)
        self.assertGreaterEqual(combined.count("**Incorrect:**"), 18)

    def test_no_placeholder_unexplained_black_box_or_side_effect_regression(self) -> None:
        combined = "\n".join((self.source, self.readme, self.lesson, self.walkthrough, self.checks))
        self.assertNotIn("TODO", combined)
        self.assertNotIn("Status:** Scaffolded", combined)
        forbidden = (
            r"\brng\s*\(", r"(?<![A-Za-z])randn\s*\(", r"\binv\s*\(",
            r"trackingEKF", r"initcvekf", r"trackingKF", r"objectDetection",
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
                [str(fixture_root / "bin/learn"), "start", "56"],
                cwd=fixture_root, env=environment, text=True, capture_output=True,
                timeout=10,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("P56", process.stdout)
            self.assertIn("Tutor entry", process.stdout)
            original = copy.deepcopy(fixture_manifest)
            p56 = next(entry for entry in fixture_manifest["modules"] if entry["id"] == "P56")
            p56["status"] = "scaffolded"
            changed = [
                (before_entry["id"], key)
                for before_entry, after_entry in zip(original["modules"], fixture_manifest["modules"])
                for key in before_entry
                if before_entry.get(key) != after_entry.get(key)
            ]
            self.assertEqual(changed, [("P56", "status")])
            for module_id in ("P55", "P57"):
                before_entry = next(entry for entry in original["modules"] if entry["id"] == module_id)
                after_entry = next(entry for entry in fixture_manifest["modules"] if entry["id"] == module_id)
                self.assertEqual(after_entry, before_entry)
            manifest_path = fixture_root / "curriculum/modules.json"
            manifest_path.write_text(json.dumps(fixture_manifest, indent=2) + "\n", encoding="utf-8")
            rolled_back = subprocess.run(
                [str(fixture_root / "bin/learn"), "start", "56"],
                cwd=fixture_root, env=environment, text=True, capture_output=True,
                timeout=10,
            )
            self.assertEqual(rolled_back.returncode, 3)
            self.assertIn("awaits Portfolio batch P56", rolled_back.stdout)
            manifest_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
            recovered = subprocess.run(
                [str(fixture_root / "bin/learn"), "start", "56"],
                cwd=fixture_root, env=environment, text=True, capture_output=True,
                timeout=10,
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertIn("Tutor entry", recovered.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_default_tutor_entry_advances_from_completed_p55_without_state_loss(self) -> None:
        repository_state = ROOT / ".learning" / "progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory) / "repo"
            fixture_cli = fixture_root / "bin/learn"
            fixture_manifest = fixture_root / "curriculum/modules.json"
            fixture_cli.parent.mkdir(parents=True)
            fixture_manifest.parent.mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture_cli)
            shutil.copy2(ROOT / "curriculum/modules.json", fixture_manifest)
            for module in self.manifest["modules"]:
                destination = fixture_root / module["folder"] / "README.md"
                destination.parent.mkdir(parents=True)
                shutil.copy2(ROOT / module["folder"] / "README.md", destination)

            prior_completed = [f"P{number:02d}" for number in range(1, 56)]
            initial_state = {
                "schema_version": 1,
                "current": "P55",
                "completed": prior_completed,
                "notes": {"P55": "Preserve this Kalman-filter teach-back note."},
            }
            progress = fixture_root / ".learning/progress.json"
            progress.parent.mkdir(parents=True)
            progress.write_text(
                json.dumps(initial_state, indent=2) + "\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["HOME"] = temporary_directory

            started = subprocess.run(
                [str(fixture_cli), "start"],
                cwd=fixture_root,
                env=environment,
                text=True,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn(
                "P56 — Use an EKF for Range-Bearing Measurements",
                started.stdout,
            )
            self.assertIn("status: implemented", started.stdout)
            self.assertIn("Tutor entry", started.stdout)
            advanced_state = json.loads(progress.read_text(encoding="utf-8"))
            self.assertEqual(advanced_state["current"], "P56")
            self.assertEqual(advanced_state["completed"], prior_completed)
            self.assertEqual(advanced_state["notes"], initial_state["notes"])

        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_public_catalogs_describe_p56_without_freezing_future_state(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 56 follows P55 by mapping range-bearing reports", root_readme)
        self.assertIn("Project 56 follows P55 by replacing the linear report", start_here)
        self.assertRegex(module_index, r"\| \[P56\].*\| implemented \|")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self) -> None:
        evidence_files = sorted((ROOT / "docs/evidence").glob("P56-*.md"))
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
            "python3 -m unittest tests.test_p56_module -v",
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
