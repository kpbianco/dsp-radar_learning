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
MODULE = ROOT / "modules/54-build-an-alpha-beta-tracker"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How can a simple predictor smooth noisy position while following constant velocity?"
EXPECTED_IDENTITY = {
    "number": 54,
    "id": "P54",
    "title": "Build an Alpha-Beta Tracker",
    "guiding_question": QUESTION,
    "phase": 6,
    "phase_title": "Radar Tracking and Data Association",
    "slug": "build-an-alpha-beta-tracker",
    "folder": "modules/54-build-an-alpha-beta-tracker",
    "status": "implemented",
    "implementation_batch": "P54",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def validate_p54_contract(module: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P54 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P54 empty {artifact}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P54"]
    if len(entries) != 1:
        return errors + [f"expected one P54 manifest entry, found {len(entries)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if entries[0].get(key) != expected:
            errors.append(f"P54 {key} mismatch")
    return errors


def canonical_controls() -> dict[str, object]:
    return {
        "seed": 5401,
        "number_scans": 81,
        "dt": 1.0,
        "initial_position": 1000.0,
        "initial_velocity": 20.0,
        "changed_velocity": 32.0,
        "change_scan": 41,
        "noise_std": 30.0,
        "dropouts": (18, 19, 20, 66, 67, 68),
        "initial_velocity_estimate": 0.0,
        "warmup_scans": 10,
        "alpha": 0.35,
        "beta": 0.08,
        "alpha_sweep": (0.10, 0.35, 0.85),
        "beta_sweep": (0.01, 0.08, 0.30),
        "broken_beta": 0.0,
        "max_scans": 200,
        "max_sweep_cases": 5,
        "max_figures": 5,
        "max_steps": 1000,
    }


def validate_gain_pair(alpha: object, beta: object, *, allow_zero_beta: bool = False) -> None:
    if not finite_real(alpha) or not finite_real(beta):
        raise ValueError("finite real gains")
    if not 0 < alpha < 2:
        raise ValueError("alpha stability")
    if beta == 0 and allow_zero_beta:
        return
    if not 0 < beta < 4 - 2 * alpha:
        raise ValueError("beta stability")


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    for name in (
        "seed", "number_scans", "change_scan", "warmup_scans", "max_scans",
        "max_sweep_cases", "max_figures", "max_steps",
    ):
        if not integer(controls[name]):
            raise ValueError(f"integer control: {name}")
    for name in (
        "dt", "initial_position", "initial_velocity", "changed_velocity",
        "noise_std", "initial_velocity_estimate", "alpha", "beta", "broken_beta",
    ):
        if not finite_real(controls[name]):
            raise ValueError(f"real control: {name}")
    fixed = {
        "seed": 5401,
        "number_scans": 81,
        "dt": 1.0,
        "initial_velocity": 20.0,
        "changed_velocity": 32.0,
        "max_scans": 200,
        "max_sweep_cases": 5,
        "max_figures": 5,
        "max_steps": 1000,
    }
    if any(controls[name] != value for name, value in fixed.items()):
        raise ValueError("fixed reviewed control")
    if controls["number_scans"] > controls["max_scans"] or controls["noise_std"] < 0:
        raise ValueError("physical/resource bound")
    if not controls["warmup_scans"] + 2 < controls["change_scan"] < controls["number_scans"] - 2:
        raise ValueError("maneuver placement")
    if controls["warmup_scans"] < 0:
        raise ValueError("warm-up range")
    dropouts = controls["dropouts"]
    if not isinstance(dropouts, (tuple, list)) or not dropouts:
        raise ValueError("dropout shape")
    if not all(integer(index) and 1 < index <= controls["number_scans"] for index in dropouts):
        raise ValueError("dropout values")
    if any(right <= left for left, right in zip(dropouts, dropouts[1:])):
        raise ValueError("dropout order")
    steady_window = range(controls["warmup_scans"] + 1, controls["change_scan"])
    if all(scan in dropouts for scan in steady_window):
        raise ValueError("empty steady comparison window")
    validate_gain_pair(controls["alpha"], controls["beta"])
    if controls["broken_beta"] != 0:
        raise ValueError("broken beta")
    for name, baseline, other, alpha_is_swept in (
        ("alpha_sweep", controls["alpha"], controls["beta"], True),
        ("beta_sweep", controls["beta"], controls["alpha"], False),
    ):
        sweep = controls[name]
        if not isinstance(sweep, (tuple, list)) or not 3 <= len(sweep) <= controls["max_sweep_cases"]:
            raise ValueError("sweep shape")
        if not all(finite_real(value) for value in sweep):
            raise ValueError("sweep finite")
        if any(right <= left for left, right in zip(sweep, sweep[1:])) or baseline not in sweep:
            raise ValueError("sweep order/baseline")
        for value in sweep:
            if alpha_is_swept:
                validate_gain_pair(value, other)
            else:
                validate_gain_pair(other, value)
    run_count = 1 + len(controls["alpha_sweep"]) + len(controls["beta_sweep"]) + 2
    if run_count * controls["number_scans"] > controls["max_steps"]:
        raise ValueError("tracker step bound")


def alpha_beta(
    measurement: object,
    available: object,
    dt: object,
    alpha: object,
    beta: object,
    initial_position: object,
    initial_velocity: object,
) -> dict[str, list[float]]:
    if not isinstance(measurement, (tuple, list)) or not measurement:
        raise ValueError("measurement shape")
    if not isinstance(available, (tuple, list)) or len(available) != len(measurement):
        raise ValueError("availability shape")
    if not all(type(value) is bool for value in available) or not available[0]:
        raise ValueError("availability type/initialization")
    if not finite_real(dt) or dt <= 0 or not finite_real(initial_position) or not finite_real(initial_velocity):
        raise ValueError("state controls")
    validate_gain_pair(alpha, beta, allow_zero_beta=True)
    for value, is_available in zip(measurement, available):
        if is_available and not finite_real(value):
            raise ValueError("available report")
        if not is_available and not isinstance(value, float):
            raise ValueError("missing report")
        if not is_available and not math.isnan(value):
            raise ValueError("missing report")

    count = len(measurement)
    predicted_position = [0.0] * count
    predicted_velocity = [0.0] * count
    innovation = [math.nan] * count
    position = [0.0] * count
    velocity = [0.0] * count
    predicted_position[0] = position[0] = float(initial_position)
    predicted_velocity[0] = velocity[0] = float(initial_velocity)
    innovation[0] = float(measurement[0]) - predicted_position[0]
    for index in range(1, count):
        predicted_position[index] = position[index - 1] + dt * velocity[index - 1]
        predicted_velocity[index] = velocity[index - 1]
        if available[index]:
            innovation[index] = measurement[index] - predicted_position[index]
            position[index] = predicted_position[index] + alpha * innovation[index]
            velocity[index] = predicted_velocity[index] + (beta / dt) * innovation[index]
        else:
            position[index] = predicted_position[index]
            velocity[index] = predicted_velocity[index]
    return {
        "predicted_position": predicted_position,
        "predicted_velocity": predicted_velocity,
        "innovation": innovation,
        "position": position,
        "velocity": velocity,
    }


def rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values))


def deterministic_scene() -> tuple[list[float], list[float], list[float], list[bool]]:
    count = 81
    velocity = [20.0] * count
    velocity[40:] = [32.0] * (count - 40)
    truth = [1000.0] + [0.0] * (count - 1)
    for index in range(1, count):
        truth[index] = truth[index - 1] + velocity[index - 1]
    noise = [float(((index * 5) % 13 - 6) * 4) for index in range(count)]
    measurement = [position + error for position, error in zip(truth, noise)]
    available = [True] * count
    for one_based_index in (18, 19, 20, 66, 67, 68):
        available[one_based_index - 1] = False
        measurement[one_based_index - 1] = math.nan
    return truth, velocity, measurement, available


def source_binding_errors(source: str) -> list[str]:
    required = (
        "random_seed = 5401;",
        "number_scans = 81;",
        "scan_interval_s = 1;",
        "dropout_scans = [18 19 20 66 67 68];",
        "alpha_gain = 0.35;",
        "beta_gain = 0.08;",
        "alpha_sweep = [0.10 0.35 0.85];",
        "beta_sweep = [0.01 0.08 0.30];",
        "broken_beta_gain = 0;",
        "maximum_number_scans = 200;",
        "maximum_tracker_steps = 1000;",
        "private_stream = RandStream('mt19937ar', 'Seed', random_seed);",
        "measurement_noise_std_m*randn(private_stream, 1, number_scans);",
        "measurement_available(dropout_scans) = false;",
        "measurement_position_m(~measurement_available) = NaN;",
        "steady_window_scans = warmup_scans+1:velocity_change_scan-1;",
        "if all(ismember(steady_window_scans, dropout_scans))",
        "~isnumeric(measurement_m) || ~isreal(measurement_m) || ...\n            islogical(measurement_m)",
        "position_prediction_m(sample_index) = position_estimate_m(sample_index-1) + ...\n            sample_interval_s*velocity_estimate_mps(sample_index-1);",
        "innovation_m(sample_index) = measurement_m(sample_index) - ...\n                position_prediction_m(sample_index);",
        "position_estimate_m(sample_index) = position_prediction_m(sample_index) + ...\n                alpha*innovation_m(sample_index);",
        "velocity_estimate_mps(sample_index) = velocity_prediction_mps(sample_index) + ...\n                (beta/sample_interval_s)*innovation_m(sample_index);",
        "position_estimate_m(sample_index) = position_prediction_m(sample_index);",
        "velocity_estimate_mps(sample_index) = velocity_prediction_mps(sample_index);",
        "alpha_sweep(sweep_index), beta_gain",
        "alpha_gain, beta_sweep(sweep_index)",
        "reviewed_run = random_seed == 5401 && number_scans == 81 &&",
        "isequal(alpha_sweep, [0.10 0.35 0.85])",
        "isequal(beta_sweep, [0.01 0.08 0.30])",
        "results.baseline_received_position_rmse_m = baseline_received_position_rmse_m;",
        "results.baseline_all_scan_position_rmse_m = baseline_all_scan_position_rmse_m;",
        "results.broken_position_rmse_m = broken_position_rmse_m;",
        "results.reviewed_tracker_steps = reviewed_tracker_steps;",
    )
    errors = [marker for marker in required if marker not in source]
    try:
        tracker = source[
            source.index("function track = run_alpha_beta"):
            source.index("function validate_gain_pair")
        ]
    except ValueError:
        return errors + ["tracker operation boundary"]
    if tracker.count("innovation_m(sample_index) =") != 1:
        errors.append("single innovation assignment")
    if tracker.count("position_prediction_m(sample_index) =") != 1:
        errors.append("single prediction assignment")
    if source.count("measurement_available(dropout_scans) = false;") != 1:
        errors.append("single dropout-mask assignment")
    if source.count("measurement_position_m(~measurement_available) = NaN;") != 1:
        errors.append("single missing-report assignment")
    if source.count("reviewed_run =") != 1:
        errors.append("single reviewed-run assignment")
    if "if available(sample_index)" not in tracker or "else\n            position_estimate_m" not in tracker:
        errors.append("explicit dropout branch")
    return errors


class P54ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self) -> None:
        self.assertEqual(validate_p54_contract(MODULE, self.manifest), [])
        p53 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P53")
        self.assertEqual(p53["status"], "implemented")
        for name in ARTIFACTS:
            payload = (MODULE / name).read_bytes()
            self.assertTrue(payload.endswith(b"\n"), name)
            self.assertFalse(payload.endswith(b"\n\n"), name)
            self.assertNotIn(b"\r", payload, name)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture = Path(temporary_directory) / "module"
            shutil.copytree(MODULE, fixture)
            (fixture / "experiment.m").unlink()
            self.assertIn("P54 missing experiment.m", validate_p54_contract(fixture, self.manifest))
            (fixture / "experiment.m").write_text("", encoding="utf-8")
            self.assertIn("P54 empty experiment.m", validate_p54_contract(fixture, self.manifest))
        for malformed in (None, [], {}, {"modules": None}, {"modules": ["P54"]}):
            self.assertTrue(validate_p54_contract(MODULE, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P54 manifest entry, found 2", validate_p54_contract(MODULE, duplicate))
        for key in EXPECTED_IDENTITY:
            drifted = copy.deepcopy(self.manifest)
            entry = next(item for item in drifted["modules"] if item["id"] == "P54")
            entry[key] = -1 if isinstance(entry[key], int) else "drift"
            self.assertTrue(validate_p54_contract(MODULE, drifted), key)

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self) -> None:
        validate_controls()
        bad_cases = (
            {"unknown": 1}, {"seed": True}, {"seed": 5402},
            {"number_scans": 80}, {"number_scans": 200.5}, {"dt": 0},
            {"initial_position": complex(1, 1)}, {"noise_std": -1},
            {"warmup_scans": -1},
            {"change_scan": 11}, {"change_scan": 80},
            {"dropouts": ()}, {"dropouts": (1, 2)}, {"dropouts": (18, 18)},
            {"dropouts": (18, 82)}, {"dropouts": (20, 19)},
            {"dropouts": tuple(range(11, 41))},
            {"alpha": True}, {"alpha": 0}, {"alpha": 2},
            {"beta": math.nan}, {"beta": 4}, {"broken_beta": 0.01},
            {"alpha_sweep": (0.1, 0.35)}, {"alpha_sweep": (0.1, 0.1, 0.85)},
            {"alpha_sweep": (0.1, 0.2, 0.85)}, {"beta_sweep": (0.01, math.inf, 0.3)},
            {"beta_sweep": (0.01, 0.3, 0.08)}, {"max_scans": 201},
            {"max_sweep_cases": 6}, {"max_figures": 6}, {"max_steps": 728},
        )
        for controls in bad_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_explicit_equations_units_limiting_cases_and_translation_invariance(self) -> None:
        measurement = [100.0, 112.0, 125.0]
        available = [True, True, True]
        track = alpha_beta(measurement, available, 2.0, 0.5, 0.2, 100.0, 5.0)
        self.assertEqual(track["predicted_position"][1], 110.0)
        self.assertEqual(track["innovation"][1], 2.0)
        self.assertEqual(track["position"][1], 111.0)
        self.assertEqual(track["velocity"][1], 5.2)

        zero_innovation = alpha_beta([10.0, 12.0], [True, True], 1.0, 0.5, 0.1, 10.0, 2.0)
        self.assertEqual(zero_innovation["position"][1], 12.0)
        self.assertEqual(zero_innovation["velocity"][1], 2.0)
        alpha_one = alpha_beta([10.0, 16.0], [True, True], 1.0, 1.0, 0.1, 10.0, 2.0)
        self.assertEqual(alpha_one["position"][1], 16.0)
        beta_zero = alpha_beta([10.0, 16.0, 22.0], [True] * 3, 1.0, 0.5, 0.0, 10.0, 0.0)
        self.assertEqual(beta_zero["velocity"], [0.0, 0.0, 0.0])

        translated = alpha_beta([150.0, 162.0, 175.0], available, 2.0, 0.5, 0.2, 150.0, 5.0)
        for base, shifted in zip(track["position"], translated["position"]):
            self.assertAlmostEqual(shifted - base, 50.0)
        self.assertEqual(track["velocity"], translated["velocity"])
        self.assertEqual(track["innovation"], translated["innovation"])

    def test_dropout_coasts_on_prediction_and_next_report_recovers_from_new_innovation(self) -> None:
        measurement = [100.0, 110.0, math.nan, math.nan, 142.0]
        available = [True, True, False, False, True]
        track = alpha_beta(measurement, available, 1.0, 0.4, 0.2, 100.0, 10.0)
        for index in (2, 3):
            self.assertEqual(track["position"][index], track["predicted_position"][index])
            self.assertEqual(track["velocity"][index], track["predicted_velocity"][index])
            self.assertTrue(math.isnan(track["innovation"][index]))
        self.assertEqual(track["predicted_position"][3] - track["predicted_position"][2], 10.0)
        self.assertGreater(track["innovation"][4], 0)
        self.assertGreater(track["velocity"][4], track["predicted_velocity"][4])

    def test_alpha_sweep_exposes_measurement_following_smoothing_and_lag_tradeoff(self) -> None:
        truth, _, measurement, available = deterministic_scene()
        tracks = {
            alpha: alpha_beta(
                measurement, available, 1.0, alpha, 0.08, measurement[0], 0.0,
            )
            for alpha in (0.10, 0.35, 0.85)
        }
        steady = [index for index in range(10, 40) if available[index]]
        maneuver = range(40, 55)
        steady_truth_rmse = {
            alpha: rms([track["position"][index] - truth[index] for index in steady])
            for alpha, track in tracks.items()
        }
        steady_report_rmse = {
            alpha: rms([track["position"][index] - measurement[index] for index in steady])
            for alpha, track in tracks.items()
        }
        peak_maneuver_error = {
            alpha: max(abs(track["position"][index] - truth[index]) for index in maneuver)
            for alpha, track in tracks.items()
        }

        self.assertLess(steady_report_rmse[0.85], steady_report_rmse[0.35])
        self.assertLess(steady_report_rmse[0.35], steady_report_rmse[0.10])
        self.assertLess(steady_truth_rmse[0.35], steady_truth_rmse[0.10])
        self.assertLess(steady_truth_rmse[0.35], steady_truth_rmse[0.85])
        self.assertGreater(peak_maneuver_error[0.10], peak_maneuver_error[0.35])

    def test_end_to_end_scene_smooths_constant_motion_exposes_lag_and_beta_zero_failure(self) -> None:
        truth, true_velocity, measurement, available = deterministic_scene()
        baseline = alpha_beta(measurement, available, 1.0, 0.35, 0.08, measurement[0], 0.0)
        repeat = alpha_beta(measurement, available, 1.0, 0.35, 0.08, measurement[0], 0.0)
        self.assertEqual(baseline, repeat)
        steady = [index for index in range(10, 40) if available[index]]
        raw_rmse = rms([measurement[index] - truth[index] for index in steady])
        track_rmse = rms([baseline["position"][index] - truth[index] for index in steady])
        self.assertLess(track_rmse, raw_rmse)
        maneuver_lag = [truth[index] - baseline["position"][index] for index in range(40, 55)]
        self.assertGreater(max(abs(value) for value in maneuver_lag), 0)
        self.assertGreater(baseline["velocity"][-1], 26.0)

        slow_beta = alpha_beta(measurement, available, 1.0, 0.35, 0.01, measurement[0], 0.0)
        fast_beta = alpha_beta(measurement, available, 1.0, 0.35, 0.30, measurement[0], 0.0)
        slow_crossing = next(index for index in range(40, 81) if slow_beta["velocity"][index] >= 26.0)
        fast_crossing = next(index for index in range(40, 81) if fast_beta["velocity"][index] >= 26.0)
        self.assertLess(fast_crossing, slow_crossing)

        broken = alpha_beta(measurement, available, 1.0, 0.35, 0.0, measurement[0], 0.0)
        self.assertEqual(broken["velocity"], [0.0] * 81)
        baseline_rmse = rms([baseline["position"][index] - truth[index] for index in range(10, 81)])
        broken_rmse = rms([broken["position"][index] - truth[index] for index in range(10, 81)])
        self.assertGreater(broken_rmse, baseline_rmse)
        self.assertNotEqual(true_velocity[40], true_velocity[39])
        self.assertEqual(truth[40] - truth[39], true_velocity[39])

    def test_oracle_rejects_malformed_measurements_states_and_gain_pairs(self) -> None:
        good = ([1.0, 2.0], [True, True], 1.0, 0.3, 0.1, 1.0, 0.0)
        alpha_beta(*good)
        malformed = (
            ([], [True], 1.0, 0.3, 0.1, 1.0, 0.0),
            ([1.0], [], 1.0, 0.3, 0.1, 1.0, 0.0),
            ([1.0, 2.0], [True, 1], 1.0, 0.3, 0.1, 1.0, 0.0),
            ([1.0, 2.0], [False, True], 1.0, 0.3, 0.1, 1.0, 0.0),
            ([1.0, math.nan], [True, True], 1.0, 0.3, 0.1, 1.0, 0.0),
            ([1.0, 0.0], [True, False], 1.0, 0.3, 0.1, 1.0, 0.0),
            ([1.0, math.nan], [True, False], 0.0, 0.3, 0.1, 1.0, 0.0),
            ([1.0, 2.0], [True, True], 1.0, True, 0.1, 1.0, 0.0),
            ([1.0, 2.0], [True, True], 1.0, 0.3, math.inf, 1.0, 0.0),
            ([1.0, 2.0], [True, True], 1.0, 2.0, 0.1, 1.0, 0.0),
            ([1.0, 2.0], [True, True], 1.0, 0.3, 3.5, 1.0, 0.0),
            ([1.0, 2.0], [True, True], 1.0, 0.3, 0.1, math.nan, 0.0),
        )
        for arguments in malformed:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                alpha_beta(*arguments)

    def test_source_is_seeded_explicit_bounded_and_mutation_sensitive(self) -> None:
        self.assertEqual(source_binding_errors(self.source), [])
        self.assertNotRegex(self.source, r"(?<![A-Za-z])rng\s*\(")
        self.assertNotRegex(self.source, r"randn\((?!private_stream)")
        for banned in (
            "trackingABF", "trackingKF", "objectDetection", "alphaBetaFilter",
            "configureKalmanFilter", "vision.", "phased.", "dsp.", "kalman(",
            "parfor", "fopen(", "webread(", "system(", "timer(", "tcpclient(",
        ):
            self.assertNotIn(banned, self.source)
        validation_end = self.source.index("% Validation above precedes random work")
        for marker in ("RandStream(", "zeros(1, number_scans)", "figure('Name', 'P54"):
            self.assertGreater(self.source.index(marker), validation_end)

        mutations = (
            self.source.replace("random_seed = 5401;", "random_seed = 54;", 1),
            self.source.replace("sample_interval_s*velocity_estimate_mps(sample_index-1)", "-sample_interval_s*velocity_estimate_mps(sample_index-1)", 1),
            self.source.replace("measurement_m(sample_index) - ...\n                position_prediction_m(sample_index)", "position_prediction_m(sample_index) - ...\n                measurement_m(sample_index)", 1),
            self.source.replace("alpha*innovation_m(sample_index)", "beta*innovation_m(sample_index)", 1),
            self.source.replace("(beta/sample_interval_s)*innovation_m(sample_index)", "beta*innovation_m(sample_index)", 1),
            self.source.replace("position_estimate_m(sample_index) = position_prediction_m(sample_index);", "position_estimate_m(sample_index) = 0;", 1),
            self.source.replace("alpha_sweep(sweep_index), beta_gain", "alpha_gain, beta_gain", 1),
            self.source.replace("alpha_gain, beta_sweep(sweep_index)", "alpha_gain, beta_gain", 1),
            self.source.replace("reviewed_run = random_seed == 5401 &&", "reviewed_run = false && random_seed == 5401 &&", 1),
            self.source.replace("isequal(alpha_sweep, [0.10 0.35 0.85])", "true", 1),
            self.source.replace("measurement_position_m(~measurement_available) = NaN;", "measurement_position_m(~measurement_available) = 0;", 1),
            self.source.replace(
                "~isnumeric(measurement_m) || ~isreal(measurement_m) || ...\n            islogical(measurement_m)",
                "false",
                1,
            ),
            self.source.replace(
                "results.baseline_received_position_rmse_m = baseline_received_position_rmse_m;",
                "results.baseline_received_position_rmse_m = 0;",
                1,
            ),
            self.source.replace("measurement_available(dropout_scans) = false;", "measurement_available(:) = true;", 1),
            self.source.replace(
                "if all(ismember(steady_window_scans, dropout_scans))",
                "if false && all(ismember(steady_window_scans, dropout_scans))",
                1,
            ),
        )
        for mutated in mutations:
            self.assertTrue(source_binding_errors(mutated))

    def test_sweeps_broken_case_metrics_and_resources_are_visible(self) -> None:
        for marker in (
            "%% Explicit baseline predict, innovation, and correction",
            "%% Sweep 1: change only alpha, keep beta and reports fixed",
            "%% Sweep 2: change only beta, keep alpha and reports fixed",
            "%% Broken case: beta zero prevents velocity learning; restore positive beta",
            "position_prediction_m", "velocity_estimate_mps", "innovation_m",
            "measurement_rmse_m", "baseline_received_position_rmse_m",
            "baseline_all_scan_position_rmse_m",
            "baseline_peak_post_change_absolute_error_m", "baseline_dropout_max_error_m",
            "beta_midpoint_delay_scans", "reviewed_tracker_steps",
        ):
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P54"), 5)
        controls = canonical_controls()
        run_count = 1 + len(controls["alpha_sweep"]) + len(controls["beta_sweep"]) + 2
        self.assertEqual(run_count * controls["number_scans"], 729)
        self.assertLessEqual(729, controls["max_steps"])

    def test_docs_cover_model_dependencies_sweeps_failure_recovery_and_claim_boundary(self) -> None:
        combined = "\n".join((self.readme, self.lesson, self.walkthrough, self.checks))
        for term in (
            QUESTION, "P53", "P55", "P57", "constant velocity", "x_pred",
            "innovation", "residual", "alpha", "beta/T", "metres per second",
            "stability", "dropout", "coast", "velocity change", "model mismatch",
            "Sweep 1", "Sweep 2", "broken", "Recovery", "Ctrl+C", "timeout",
            "teach-back", "base MATLAB", "hardware/HIL", "operational radar",
        ):
            self.assertIn(term.lower(), combined.lower())
        self.assertIn("change only alpha", self.walkthrough)
        self.assertIn("change only beta", self.walkthrough)
        self.assertGreaterEqual(self.checks.count("Correct:"), 10)
        self.assertGreaterEqual(self.checks.count("Incorrect:"), 10)

    def test_no_placeholder_or_unexplained_black_box_regression(self) -> None:
        combined = "\n".join((self.source, self.readme, self.lesson, self.walkthrough, self.checks))
        self.assertNotRegex(combined, r"(?i)\bTODO\b|\bTBD\b|lorem ipsum|coming soon")
        self.assertNotRegex(combined, r"(?i)copy.+toolbox|use a tracking object")
        self.assertGreater(len(self.source.splitlines()), 400)
        self.assertGreater(len(self.lesson.splitlines()), 120)

    def _run_fixture_cli(
        self, manifest: dict, *arguments: str, initial_state: dict | None = None,
        state_capture: dict | None = None,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory) / "repo"
            fixture_cli = fixture_root / "bin/learn"
            fixture_manifest = fixture_root / "curriculum/modules.json"
            fixture_cli.parent.mkdir(parents=True)
            fixture_manifest.parent.mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture_cli)
            fixture_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for module in manifest["modules"]:
                readme = fixture_root / module["folder"] / "README.md"
                readme.parent.mkdir(parents=True)
                shutil.copy2(ROOT / module["folder"] / "README.md", readme)
            if initial_state is not None:
                state = fixture_root / ".learning/progress.json"
                state.parent.mkdir(parents=True)
                state.write_text(json.dumps(initial_state, indent=2) + "\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["HOME"] = temporary_directory
            result = subprocess.run(
                [str(fixture_cli), *arguments], cwd=fixture_root, text=True,
                capture_output=True, env=environment, timeout=10, check=False,
            )
            if state_capture is not None:
                fixture_state = fixture_root / ".learning/progress.json"
                state_capture.update(json.loads(fixture_state.read_text(encoding="utf-8")))
            return result

    def test_cli_advance_timeout_isolation_and_scaffold_rollback_compatibility(self) -> None:
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        completed = [f"P{number:02d}" for number in range(1, 54)]
        initial = {
            "schema_version": 1, "current": "P53", "completed": completed,
            "notes": {"P53": "Formed one report per accepted component."},
        }
        advanced_state: dict = {}
        advanced = self._run_fixture_cli(
            self.manifest, "start", initial_state=initial, state_capture=advanced_state,
        )
        self.assertEqual(advanced.returncode, 0, advanced.stderr)
        self.assertIn("P54 — Build an Alpha-Beta Tracker", advanced.stdout)
        self.assertIn("status: implemented", advanced.stdout)
        self.assertIn("Tutor entry", advanced.stdout)
        self.assertEqual(advanced_state["current"], "P54")
        self.assertEqual(advanced_state["completed"], completed)
        self.assertEqual(advanced_state["notes"], initial["notes"])

        rolled_back = copy.deepcopy(self.manifest)
        p53_before = copy.deepcopy(next(entry for entry in rolled_back["modules"] if entry["id"] == "P53"))
        p55_before = copy.deepcopy(next(entry for entry in rolled_back["modules"] if entry["id"] == "P55"))
        next(entry for entry in rolled_back["modules"] if entry["id"] == "P54")["status"] = "scaffolded"
        changed_entries = [
            (before_entry["id"], key)
            for before_entry, after_entry in zip(self.manifest["modules"], rolled_back["modules"])
            for key in before_entry
            if before_entry.get(key) != after_entry.get(key)
        ]
        self.assertEqual(changed_entries, [("P54", "status")])
        rollback_state: dict = {}
        rollback = self._run_fixture_cli(
            rolled_back, "start", "54", initial_state=initial, state_capture=rollback_state,
        )
        self.assertEqual(rollback.returncode, 3)
        self.assertIn("awaits Portfolio batch P54", rollback.stdout)
        self.assertEqual(rollback_state["current"], "P54")
        self.assertEqual(rollback_state["completed"], completed)
        self.assertEqual(rollback_state["notes"], initial["notes"])
        self.assertEqual(next(entry for entry in rolled_back["modules"] if entry["id"] == "P53"), p53_before)
        self.assertEqual(next(entry for entry in rolled_back["modules"] if entry["id"] == "P55"), p55_before)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_public_catalogs_describe_p54_without_freezing_future_state(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 54 follows P53", root_readme)
        self.assertIn("Project 54 follows P53", start_here)
        self.assertRegex(module_index, r"\| \[P54\].*\| implemented \| 6 \|")
        self.assertNotRegex("\n".join((root_readme, start_here)), r"(?i)P54 is (the )?latest")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self) -> None:
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P54-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        payload = evidence_paths[0].read_bytes()
        self.assertTrue(payload.endswith(b"\n"))
        self.assertFalse(payload.endswith(b"\n\n"))
        self.assertNotIn(b"\r", payload)
        evidence = payload.decode("utf-8")
        for heading in (
            "## Scope and claim boundary", "## Acceptance mapping",
            "## Figure and metric inventory", "## Exact commands and results",
            "## Changed and preserved invariants", "## Residual risks",
            "## Rollback and recovery", "## Unperformed validation",
        ):
            self.assertIn(heading, evidence)
        for command in (
            "python3 -m unittest tests.test_p54_module -v",
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
            "git diff --check",
        ):
            self.assertIn(command, evidence)
        for term in ("MATLAB and Octave did not run", "static", "hardware/HIL", "production", "rollback"):
            self.assertIn(term.lower(), evidence.lower())
        self.assertNotRegex(evidence, r"(?i)\bpending\b|\bTODO\b|\bTBD\b")


if __name__ == "__main__":
    unittest.main()
