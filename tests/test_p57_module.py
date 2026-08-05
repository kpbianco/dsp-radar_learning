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
MODULE = ROOT / "modules/57-gate-and-associate-detections-by-nearest-neighbor"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Which measurement should update which track?"
EXPECTED_IDENTITY = {
    "number": 57,
    "id": "P57",
    "title": "Gate and Associate Detections by Nearest Neighbor",
    "guiding_question": QUESTION,
    "phase": 6,
    "phase_title": "Radar Tracking and Data Association",
    "slug": "gate-and-associate-detections-by-nearest-neighbor",
    "folder": "modules/57-gate-and-associate-detections-by-nearest-neighbor",
    "status": "implemented",
    "implementation_batch": "P57",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def validate_p57_contract(module: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P57 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P57 empty {artifact}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P57"]
    if len(entries) != 1:
        return errors + [f"expected one P57 manifest entry, found {len(entries)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if entries[0].get(key) != expected:
            errors.append(f"P57 {key} mismatch")
    return errors


def canonical_controls() -> dict[str, object]:
    return {
        "seed": 5701,
        "tracks": 3,
        "target_reports": 3,
        "clutter_reports": 3,
        "dt": 1.0,
        "process_std": 1.0,
        "measurement_std": 6.0,
        "gate": 5.991,
        "gate_sweep": (0.5, 5.991, 13.816),
        "covariance_sweep": (0.25, 1.0, 4.0),
        "ellipse_points": 73,
        "max_tracks": 8,
        "max_measurements": 12,
        "max_sweep_cases": 5,
        "max_figures": 6,
        "max_pair_slots": 200,
        "max_ellipse_points": 73,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    integer_names = (
        "seed", "tracks", "target_reports", "clutter_reports", "ellipse_points",
        "max_tracks", "max_measurements", "max_sweep_cases", "max_figures",
        "max_pair_slots", "max_ellipse_points",
    )
    if not all(integer(controls[name]) and controls[name] > 0 for name in integer_names):
        raise ValueError("integer controls")
    for name in ("dt", "process_std", "measurement_std", "gate"):
        if not finite_real(controls[name]) or controls[name] <= 0:
            raise ValueError("real controls")
    if controls["seed"] != 5701 or controls["tracks"] != 3:
        raise ValueError("reviewed scene")
    if controls["target_reports"] != 3 or controls["clutter_reports"] != 3:
        raise ValueError("reviewed reports")
    if (
        controls["dt"] != 1
        or controls["process_std"] != 1
        or controls["measurement_std"] != 6
        or controls["gate"] != 5.991
    ):
        raise ValueError("tuning drift")
    fixed_ceilings = {
        "max_tracks": 8,
        "max_measurements": 12,
        "max_sweep_cases": 5,
        "max_figures": 6,
        "max_pair_slots": 200,
        "max_ellipse_points": 73,
        "ellipse_points": 73,
    }
    if any(controls[name] != value for name, value in fixed_ceilings.items()):
        raise ValueError("resource ceiling drift")
    for name, baseline in (("gate_sweep", 5.991), ("covariance_sweep", 1.0)):
        values = controls[name]
        if not isinstance(values, (tuple, list)) or not 3 <= len(values) <= controls["max_sweep_cases"]:
            raise ValueError("sweep shape")
        if not all(finite_real(value) and value > 0 for value in values):
            raise ValueError("sweep values")
        if any(right <= left for left, right in zip(values, values[1:])):
            raise ValueError("sweep ordering")
        if sum(value == baseline for value in values) != 1:
            raise ValueError("sweep baseline")
    if tuple(controls["gate_sweep"]) != (0.5, 5.991, 13.816):
        raise ValueError("reviewed gate sweep")
    if tuple(controls["covariance_sweep"]) != (0.25, 1.0, 4.0):
        raise ValueError("reviewed covariance sweep")
    measurements = controls["target_reports"] + controls["clutter_reports"]
    association_runs = 1 + len(controls["gate_sweep"]) + len(controls["covariance_sweep"]) + 2
    if controls["tracks"] > controls["max_tracks"] or measurements > controls["max_measurements"]:
        raise ValueError("scene bound")
    if association_runs * controls["tracks"] * measurements > controls["max_pair_slots"]:
        raise ValueError("pair-slot bound")


def canonical_scene() -> tuple[list[list[float]], list[list[list[float]]], list[list[float]], list[int]]:
    predictions = [[0.0, 0.0], [200.0, 50.0], [400.0, -100.0]]
    innovation_covariances = [
        [[2086.25, 0.0], [0.0, 89.25]],
        [[196.25, 0.0], [0.0, 196.25]],
        [[248.25, 0.0], [0.0, 145.25]],
    ]
    noise = seeded_gaussian_noise(5701, 2, 3)
    target_truth = [[44.0, 0.0], [204.0, 45.0], [394.0, -93.0]]
    target_reports = [
        [truth[0] + 6 * noise[0][index], truth[1] + 6 * noise[1][index]]
        for index, truth in enumerate(target_truth)
    ]
    measurements = [
        target_reports[1],
        [0.0, 30.0],
        target_reports[0],
        [110.0, 140.0],
        target_reports[2],
        [520.0, 40.0],
    ]
    truth_ids = [2, 0, 1, 0, 3, 0]
    return predictions, innovation_covariances, measurements, truth_ids


def seeded_gaussian_noise(seed: object, rows: object, columns: object) -> list[list[float]]:
    if (
        not integer(seed) or not 0 < seed < 2_147_483_647
        or not integer(rows) or rows <= 0
        or not integer(columns) or columns <= 0
        or rows * columns > 96
    ):
        raise ValueError("noise request")
    modulus = 2_147_483_647
    multiplier = 16_807
    state = int(seed)
    count = int(rows * columns)
    sequence: list[float] = []
    for _ in range(math.ceil(count / 2)):
        state = (multiplier * state) % modulus
        uniform_1 = (state + 0.5) / modulus
        state = (multiplier * state) % modulus
        uniform_2 = (state + 0.5) / modulus
        radius = math.sqrt(-2 * math.log(uniform_1))
        angle = 2 * math.pi * uniform_2
        sequence.extend((radius * math.cos(angle), radius * math.sin(angle)))
    output = [[0.0] * int(columns) for _ in range(int(rows))]
    for linear_index, value in enumerate(sequence[:count]):
        row = linear_index % int(rows)
        column = linear_index // int(rows)
        output[row][column] = value
    return output


def validate_association_inputs(
    predictions: object,
    covariances: object,
    measurements: object,
) -> tuple[list[list[float]], list[list[list[float]]], list[list[float]]]:
    if not isinstance(predictions, list) or not predictions:
        raise ValueError("predictions")
    if not isinstance(measurements, list) or not measurements:
        raise ValueError("measurements")
    if not all(
        isinstance(point, list) and len(point) == 2 and all(finite_real(value) for value in point)
        for point in predictions + measurements
    ):
        raise ValueError("finite 2-D points")
    if not isinstance(covariances, list) or len(covariances) != len(predictions):
        raise ValueError("covariance pages")
    if len(predictions) > 8 or len(measurements) > 12 or len(predictions) * len(measurements) > 96:
        raise ValueError("association input bound")
    for covariance in covariances:
        if (
            not isinstance(covariance, list)
            or len(covariance) != 2
            or any(not isinstance(row, list) or len(row) != 2 for row in covariance)
            or any(not finite_real(value) for row in covariance for value in row)
        ):
            raise ValueError("covariance shape")
        if not math.isclose(covariance[0][1], covariance[1][0], abs_tol=1e-10):
            raise ValueError("covariance symmetry")
        determinant = covariance[0][0] * covariance[1][1] - covariance[0][1] * covariance[1][0]
        if covariance[0][0] <= 0 or covariance[1][1] <= 0 or determinant <= 0:
            raise ValueError("covariance positive definite")
    return predictions, covariances, measurements


def association_distances(
    predictions: object,
    covariances: object,
    measurements: object,
) -> list[list[float]]:
    predictions, covariances, measurements = validate_association_inputs(
        predictions, covariances, measurements
    )
    distances: list[list[float]] = []
    for prediction, covariance in zip(predictions, covariances):
        determinant = covariance[0][0] * covariance[1][1] - covariance[0][1] * covariance[1][0]
        inverse = [
            [covariance[1][1] / determinant, -covariance[0][1] / determinant],
            [-covariance[1][0] / determinant, covariance[0][0] / determinant],
        ]
        row = []
        for measurement in measurements:
            residual = [measurement[0] - prediction[0], measurement[1] - prediction[1]]
            solved = [
                inverse[0][0] * residual[0] + inverse[0][1] * residual[1],
                inverse[1][0] * residual[0] + inverse[1][1] * residual[1],
            ]
            distance = residual[0] * solved[0] + residual[1] * solved[1]
            if not math.isfinite(distance) or distance < 0:
                raise ValueError("distance")
            row.append(distance)
        distances.append(row)
    return distances


def greedy_nearest_neighbor(distances: object, valid: object) -> list[int]:
    if not isinstance(distances, list) or not distances or not all(isinstance(row, list) for row in distances):
        raise ValueError("distance matrix")
    columns = len(distances[0])
    if columns == 0 or any(len(row) != columns for row in distances):
        raise ValueError("rectangular distance")
    if len(distances) > 8 or columns > 12 or len(distances) * columns > 96:
        raise ValueError("assignment bound")
    if any(not finite_real(value) or value < 0 for row in distances for value in row):
        raise ValueError("distance values")
    if (
        not isinstance(valid, list)
        or len(valid) != len(distances)
        or any(not isinstance(row, list) or len(row) != columns for row in valid)
        or any(type(value) is not bool for row in valid for value in row)
    ):
        raise ValueError("gate mask")
    assignment = [0] * len(distances)
    remaining_tracks = set(range(len(distances)))
    remaining_measurements = set(range(columns))
    for _ in range(min(len(distances), columns)):
        candidates = [
            (distances[track][measurement], measurement, track)
            for measurement in remaining_measurements
            for track in remaining_tracks
            if valid[track][measurement]
        ]
        if not candidates:
            break
        _, measurement, track = min(candidates)
        assignment[track] = measurement + 1
        remaining_tracks.remove(track)
        remaining_measurements.remove(measurement)
    return assignment


def source_binding_errors(source: str) -> list[str]:
    required = (
        "random_seed = 5701;",
        "number_tracks = 3;",
        "number_clutter_reports = 3;",
        "measurement_std_m = 6;",
        "gate_threshold_d2 = 5.991;",
        "gate_threshold_sweep_d2 = [0.5 5.991 13.816];",
        "covariance_scale_sweep = [0.25 1 4];",
        "maximum_pair_slots = 200;",
        "reviewed_pair_slots = association_run_count*number_tracks*number_measurements;",
        "reviewed_pair_slots > maximum_pair_slots",
        "measurement_std_m*seeded_gaussian_noise( ...",
        "function standard_normal = seeded_gaussian_noise(seed, row_count, column_count)",
        "state = mod(multiplier*state, modulus);",
        "radius = sqrt(-2*log(uniform_1));",
        "normal_sequence(2*pair_index-1) = radius*cos(angle_rad);",
        "normal_sequence(2*pair_index) = radius*sin(angle_rad);",
        "~isequal(gate_threshold_sweep_d2, [0.5 5.991 13.816])",
        "predicted_state(:, track_index) = F*prior_state(:, track_index);",
        "F*prior_covariance(:, :, track_index)*F' + Q;",
        "H*predicted_covariance(:, :, track_index)*H' + R;",
        "measurement_m(:, measurement_index) - predicted_measurement(:, track_index);",
        "~ismatrix(predicted_measurement) || ~ismatrix(measurement_m)",
        "ndims(innovation_covariance) > 3",
        "current_residual'*(current_covariance\\current_residual);",
        "gate_mask = squared_mahalanobis_distance <= gate_threshold_d2;",
        "working_distance(track_index, :) = Inf;",
        "working_distance(:, measurement_index) = Inf;",
        "any(eig(current_covariance) <= 0)",
        "size(distance, 1) > 8 || size(distance, 2) > 12 || numel(distance) > 96",
        "broken_assignment = greedy_nearest_neighbor( ...",
        "true(size(euclidean_squared_distance_m2))",
        "recovery_exact = isequal(recovered_assignment, baseline_assignment);",
        "broken_assignment(1) == 2 && baseline_assignment(1) == 3",
        "reviewed_pair_slots == 162 && association_run_count == 9",
        "results.squared_mahalanobis_distance = squared_mahalanobis_distance;",
        "results.recovered_assignment = recovered_assignment;",
    )
    errors = [marker for marker in required if marker not in source]
    try:
        operation = source[
            source.index("function [residual_m, squared_distance] = association_distances"):
            source.index("function assignment = greedy_nearest_neighbor")
        ]
        assignment = source[
            source.index("function assignment = greedy_nearest_neighbor"):
            source.index("function ellipse_xy = covariance_ellipse")
        ]
    except ValueError:
        return errors + ["operation boundaries"]
    if operation.count("squared_distance(track_index, measurement_index) =") != 1:
        errors.append("single Mahalanobis operation")
    if assignment.count("assignment(track_index) = measurement_index;") != 1:
        errors.append("single assignment operation")
    covariance_marker = "H*predicted_covariance(:, :, track_index)*H' + R;"
    if source.count(covariance_marker) != 2:
        errors.append("baseline and scaled innovation covariance")
    if source.count("state = mod(multiplier*state, modulus);") != 2:
        errors.append("two Park-Miller uniform updates")
    return errors


class P57ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self) -> None:
        self.assertEqual(validate_p57_contract(MODULE, self.manifest), [])
        p56 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P56")
        self.assertEqual(p56["status"], "implemented")
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
            self.assertIn("P57 missing lesson.md", validate_p57_contract(fixture, self.manifest))
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P57 empty lesson.md", validate_p57_contract(fixture, self.manifest))
        for malformed in (None, [], {}, {"modules": None}, {"modules": ["P57"]}):
            self.assertTrue(validate_p57_contract(MODULE, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P57 manifest entry, found 2", validate_p57_contract(MODULE, duplicate))
        for key in EXPECTED_IDENTITY:
            drifted = copy.deepcopy(self.manifest)
            entry = next(item for item in drifted["modules"] if item["id"] == "P57")
            entry[key] = -1 if isinstance(entry[key], int) else "drift"
            self.assertTrue(validate_p57_contract(MODULE, drifted), key)

    def test_controls_accept_reviewed_and_reject_malformed_or_unbounded_values(self) -> None:
        validate_controls()
        bad_cases = (
            {"unknown": 1}, {"seed": True}, {"seed": 5702}, {"tracks": 2},
            {"target_reports": 2}, {"clutter_reports": 4}, {"dt": 0},
            {"process_std": math.nan}, {"measurement_std": complex(1, 1)},
            {"gate": 0}, {"gate_sweep": (0.5, 5.991)},
            {"gate_sweep": (0.5, 5.991, 5.991)},
            {"gate_sweep": (0.5, 6.0, 13.816)},
            {"gate_sweep": (0.4, 5.991, 13.816)},
            {"covariance_sweep": (0.25, math.inf, 4)},
            {"covariance_sweep": (1, 0.25, 4)},
            {"covariance_sweep": (0.5, 1, 4)},
            {"ellipse_points": 72}, {"max_tracks": 9},
            {"max_measurements": 13}, {"max_sweep_cases": 6},
            {"max_figures": 7}, {"max_pair_slots": 161},
            {"max_ellipse_points": 74},
        )
        for controls in bad_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_prediction_innovation_covariance_units_and_values(self) -> None:
        predictions, covariances, _, _ = canonical_scene()
        self.assertEqual(predictions, [[0.0, 0.0], [200.0, 50.0], [400.0, -100.0]])
        self.assertEqual(covariances[0], [[2086.25, 0.0], [0.0, 89.25]])
        self.assertEqual(covariances[1], [[196.25, 0.0], [0.0, 196.25]])
        self.assertEqual(covariances[2], [[248.25, 0.0], [0.0, 145.25]])
        for covariance in covariances:
            self.assertGreater(covariance[0][0] * covariance[1][1], 0)

    def test_seeded_gaussian_record_matches_reviewed_cross_language_values(self) -> None:
        noise = seeded_gaussian_noise(5701, 2, 3)
        expected = (
            (1.9889108226578411, -1.5044811990340416),
            (0.07541470912527752, -0.8311182149882606),
            (-0.34815623852871047, 1.4989975617365228),
        )
        for column, pair in enumerate(expected):
            self.assertAlmostEqual(noise[0][column], pair[0], places=14)
            self.assertAlmostEqual(noise[1][column], pair[1], places=14)
        for args in ((0, 2, 3), (True, 2, 3), (5701, 0, 3), (5701, 2.5, 3), (5701, 9, 12)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                seeded_gaussian_noise(*args)

    def test_mahalanobis_distance_gate_and_anisotropic_counterexample(self) -> None:
        predictions, covariances, measurements, _ = canonical_scene()
        distances = association_distances(predictions, covariances, measurements)
        noise = seeded_gaussian_noise(5701, 2, 3)
        expected_track1 = (44.0 + 6 * noise[0][0]) ** 2 / 2086.25 + (6 * noise[1][0]) ** 2 / 89.25
        self.assertAlmostEqual(distances[0][2], expected_track1)
        self.assertAlmostEqual(distances[0][1], 30.0**2 / 89.25)
        euclidean_true = math.dist(predictions[0], measurements[2])
        euclidean_clutter = math.dist(predictions[0], measurements[1])
        self.assertLess(euclidean_clutter, euclidean_true)
        self.assertLess(distances[0][2], 5.991)
        self.assertGreater(distances[0][1], 5.991)

    def test_one_to_one_nearest_neighbor_and_deterministic_tie_policy(self) -> None:
        distances = [[1.0, 5.0], [2.0, 3.0]]
        valid = [[True, True], [True, True]]
        self.assertEqual(greedy_nearest_neighbor(distances, valid), [1, 2])
        shared_best = [[1.0, 4.0], [1.5, 3.0]]
        assigned = greedy_nearest_neighbor(shared_best, valid)
        self.assertEqual(assigned, [1, 2])
        self.assertEqual(len({value for value in assigned if value}), 2)
        ties = [[1.0, 1.0], [1.0, 1.0]]
        self.assertEqual(greedy_nearest_neighbor(ties, valid), [1, 2])
        self.assertEqual(greedy_nearest_neighbor([[1.0]], [[False]]), [0])

    def test_competing_tracks_cannot_reuse_the_only_valid_detection(self) -> None:
        distances = [[0.5], [0.25], [0.75]]
        valid = [[True], [True], [True]]
        assignment = greedy_nearest_neighbor(distances, valid)
        self.assertEqual(assignment, [0, 1, 0])
        self.assertEqual(sum(value == 1 for value in assignment), 1)

    def test_oracle_rejects_malformed_nonfinite_indefinite_and_unbounded_inputs(self) -> None:
        predictions, covariances, measurements, _ = canonical_scene()
        bad_distance_args = (
            ([], covariances, measurements), (predictions, [], measurements),
            (predictions, covariances, []), ([[0.0]], covariances, measurements),
            ([[0.0, math.nan]], [covariances[0]], measurements),
            (predictions, covariances[:2], measurements),
            (predictions, [[[1.0, 2.0], [0.0, 1.0]]] * 3, measurements),
            (predictions, [[[1.0, 0.0], [0.0, 0.0]]] * 3, measurements),
            (predictions * 3, covariances * 3, measurements * 3),
        )
        for args in bad_distance_args:
            with self.subTest(args=str(args)[:100]), self.assertRaises(ValueError):
                association_distances(*args)
        bad_assignment_args = (
            ([], []), ([[1.0], []], [[True], []]),
            ([[math.nan]], [[True]]), ([[-1.0]], [[True]]),
            ([[1.0]], [[1]]), ([[1.0, 2.0]], [[True]]),
            ([[1.0] * 13], [[True] * 13]),
        )
        for args in bad_assignment_args:
            with self.subTest(args=str(args)), self.assertRaises(ValueError):
                greedy_nearest_neighbor(*args)

    def test_baseline_positive_negative_broken_and_exact_recovery(self) -> None:
        predictions, covariances, measurements, truth_ids = canonical_scene()
        distances = association_distances(predictions, covariances, measurements)
        gate = [[distance <= 5.991 for distance in row] for row in distances]
        baseline = greedy_nearest_neighbor(distances, gate)
        self.assertEqual(baseline, [3, 1, 5])
        self.assertEqual([truth_ids[index - 1] for index in baseline], [1, 2, 3])
        unassigned = set(range(1, 7)) - set(baseline)
        self.assertEqual(unassigned, {2, 4, 6})
        self.assertTrue(all(truth_ids[index - 1] == 0 for index in unassigned))
        euclidean = [
            [math.dist(prediction, measurement) ** 2 for measurement in measurements]
            for prediction in predictions
        ]
        broken = greedy_nearest_neighbor(euclidean, [[True] * 6 for _ in range(3)])
        recovered = greedy_nearest_neighbor(distances, gate)
        self.assertEqual(broken[0], 2)
        self.assertLess(sum(a == b for a, b in zip(broken, [3, 1, 5])), 3)
        self.assertGreater(sum(truth_ids[index - 1] == 0 for index in broken), 0)
        self.assertEqual(recovered, baseline)

    def test_gate_and_covariance_sweeps_reuse_inputs_and_move_expected_metrics(self) -> None:
        predictions, covariances, measurements, _ = canonical_scene()
        distances = association_distances(predictions, covariances, measurements)
        candidate_counts = [
            sum(distance <= threshold for row in distances for distance in row)
            for threshold in (0.5, 5.991, 13.816)
        ]
        self.assertEqual(candidate_counts, [0, 3, 4])
        self.assertEqual(
            greedy_nearest_neighbor(distances, [[d <= 5.991 for d in row] for row in distances]),
            [3, 1, 5],
        )
        target_d2 = []
        clutter_d2 = []
        gate_areas = []
        predicted_track1 = [[2050.25, 0.0], [0.0, 53.25]]
        for scale in (0.25, 1.0, 4.0):
            covariance = [[scale * predicted_track1[0][0] + 36, 0.0], [0.0, scale * predicted_track1[1][1] + 36]]
            scaled = association_distances([predictions[0]], [covariance], measurements)
            target_d2.append(scaled[0][2])
            clutter_d2.append(scaled[0][1])
            gate_areas.append(math.pi * 5.991 * math.sqrt(covariance[0][0] * covariance[1][1]))
        self.assertTrue(all(right < left for left, right in zip(target_d2, target_d2[1:])))
        self.assertTrue(all(right < left for left, right in zip(clutter_d2, clutter_d2[1:])))
        self.assertTrue(all(right > left for left, right in zip(gate_areas, gate_areas[1:])))

    def test_source_is_seeded_explicit_bounded_and_mutation_sensitive(self) -> None:
        self.assertEqual(source_binding_errors(self.source), [])
        mutations = (
            self.source.replace("F*prior_state(:, track_index)", "prior_state(:, track_index)", 1),
            self.source.replace(
                "H*predicted_covariance(:, :, track_index)*H' + R;",
                "H*predicted_covariance(:, :, track_index)*H' - R;",
                1,
            ),
            self.source.replace("measurement_m(:, measurement_index) -", "measurement_m(:, measurement_index) +", 1),
            self.source.replace("~ismatrix(predicted_measurement) || ~ismatrix(measurement_m)", "false", 1),
            self.source.replace("ndims(innovation_covariance) > 3", "false", 1),
            self.source.replace("current_covariance\\current_residual", "current_covariance*current_residual", 1),
            self.source.replace("<= gate_threshold_d2", ">= gate_threshold_d2", 1),
            self.source.replace("working_distance(:, measurement_index) = Inf;", "", 1),
            self.source.replace("any(eig(current_covariance) <= 0)", "false", 1),
            self.source.replace("state = mod(multiplier*state, modulus);", "state = seed;", 1),
            self.source.replace("radius = sqrt(-2*log(uniform_1));", "radius = uniform_1;", 1),
            self.source.replace("reviewed_pair_slots > maximum_pair_slots", "false", 1),
            self.source.replace("recovery_exact = isequal(recovered_assignment, baseline_assignment);", "recovery_exact = true;", 1),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation[:80]):
                self.assertTrue(source_binding_errors(mutation))
        bound = self.source.index("reviewed_pair_slots > maximum_pair_slots")
        self.assertLess(bound, self.source.index("measurement_noise_m ="))
        self.assertLess(bound, self.source.index("residual_m = zeros"))

    def test_sweeps_broken_recovery_metrics_figures_and_units_are_visible(self) -> None:
        self.assertEqual(self.source.count("figure('Name', 'P57 Figure"), 6)
        self.assertEqual(self.source.count("'Tag', 'P57'"), 7)
        self.assertIn("gate_threshold_sweep_d2(sweep_index)", self.source)
        self.assertIn("covariance_scale_sweep(sweep_index)*", self.source)
        self.assertIn("expected_measurement_for_track = [3 1 5];", self.source)
        self.assertIn("baseline_clutter_assignment_count == 0", self.source)
        self.assertIn("recovery_exact", self.source)
        for unit in (
            "Cartesian x (m)", "Cartesian y (m)", "dimensionless",
            "Track 1 gate area (m^2)", "Valid pair count per scan", "Count per scan",
        ):
            self.assertIn(unit, self.source)
        for metric in (
            "squared_mahalanobis_distance", "gate_sweep_candidate_count",
            "covariance_sweep_track1_target_d2", "covariance_sweep_track1_clutter_d2",
            "baseline_correct_count", "broken_correct_count",
            "baseline_clutter_assignment_count", "broken_clutter_assignment_count",
            "reviewed_pair_slots",
        ):
            self.assertIn(metric, self.source)

    def test_docs_cover_model_dependencies_limits_failure_recovery_and_claim_boundary(self) -> None:
        combined = "\n".join((self.readme, self.lesson, self.walkthrough, self.checks))
        for marker in (
            QUESTION, "P53", "P55", "P56", "P58", "P59", "F x", "P_i^-",
            "nu_ij", "S =", "Mahalanobis", "d^2", "5.991", "one-to-one",
            "greedy", "gate-threshold sweep", "covariance-scale sweep",
            "Euclidean", "Limiting cases", "Correct:", "Incorrect:",
            "Ctrl+C", "10-second", "rollback", "R2016b", "MATLAB execution",
            "hardware/HIL", "field", "single-scan",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(combined.count("**Correct:**"), 23)
        self.assertGreaterEqual(combined.count("**Incorrect:**"), 23)

    def test_no_placeholder_unexplained_black_box_or_side_effect_regression(self) -> None:
        combined = "\n".join((self.source, self.readme, self.lesson, self.walkthrough, self.checks))
        self.assertNotIn("TODO", combined)
        self.assertNotIn("Status:** Scaffolded", combined)
        forbidden = (
            r"\brng\s*\(", r"(?<![A-Za-z])randn\s*\(", r"\binv\s*\(",
            r"assignDetectionsToTracks", r"matchpairs", r"trackingKF",
            r"trackingEKF", r"objectDetection", r"\bparfor\b", r"\bfopen\s*\(",
            r"\bwebread\s*\(", r"\bsystem\s*\(", r"\bunix\s*\(", r"\btimer\s*\(",
        )
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, self.source), pattern)

    def test_cli_timeout_isolation_rollback_recovery_and_future_compatibility(self) -> None:
        repository_state = ROOT / ".learning/progress.json"
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
            started = subprocess.run(
                [str(fixture_root / "bin/learn"), "start", "57"],
                cwd=fixture_root, env=environment, text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P57", started.stdout)
            self.assertIn("Tutor entry", started.stdout)
            original = copy.deepcopy(fixture_manifest)
            p57 = next(entry for entry in fixture_manifest["modules"] if entry["id"] == "P57")
            p57["status"] = "scaffolded"
            changed = [
                (before_entry["id"], key)
                for before_entry, after_entry in zip(original["modules"], fixture_manifest["modules"])
                for key in before_entry
                if before_entry.get(key) != after_entry.get(key)
            ]
            self.assertEqual(changed, [("P57", "status")])
            for module_id in ("P56", "P58"):
                before_entry = next(entry for entry in original["modules"] if entry["id"] == module_id)
                after_entry = next(entry for entry in fixture_manifest["modules"] if entry["id"] == module_id)
                self.assertEqual(after_entry, before_entry)
            manifest_path = fixture_root / "curriculum/modules.json"
            manifest_path.write_text(json.dumps(fixture_manifest, indent=2) + "\n", encoding="utf-8")
            rolled_back = subprocess.run(
                [str(fixture_root / "bin/learn"), "start", "57"],
                cwd=fixture_root, env=environment, text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(rolled_back.returncode, 3)
            self.assertIn("awaits Portfolio batch P57", rolled_back.stdout)
            manifest_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
            recovered = subprocess.run(
                [str(fixture_root / "bin/learn"), "start", "57"],
                cwd=fixture_root, env=environment, text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertIn("Tutor entry", recovered.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_default_tutor_entry_advances_from_completed_p56_without_state_loss(self) -> None:
        repository_state = ROOT / ".learning/progress.json"
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
            prior_completed = [f"P{number:02d}" for number in range(1, 57)]
            initial_state = {
                "schema_version": 1,
                "current": "P56",
                "completed": prior_completed,
                "notes": {"P56": "Preserve this EKF teach-back note."},
            }
            progress = fixture_root / ".learning/progress.json"
            progress.parent.mkdir(parents=True)
            progress.write_text(json.dumps(initial_state, indent=2) + "\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["HOME"] = temporary_directory
            started = subprocess.run(
                [str(fixture_cli), "start"], cwd=fixture_root, env=environment,
                text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P57 — Gate and Associate Detections by Nearest Neighbor", started.stdout)
            advanced_state = json.loads(progress.read_text(encoding="utf-8"))
            self.assertEqual(advanced_state["current"], "P57")
            self.assertEqual(advanced_state["completed"], prior_completed)
            self.assertEqual(advanced_state["notes"], initial_state["notes"])
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_public_catalogs_describe_p57_without_freezing_future_state(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 57 follows P56 by testing every predicted track", root_readme)
        self.assertIn("Project 57 follows P56 by comparing each prediction", start_here)
        self.assertRegex(module_index, r"\| \[P57\].*\| implemented \|")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self) -> None:
        evidence_files = sorted((ROOT / "docs/evidence").glob("P57-*.md"))
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
            "python3 -m unittest tests.test_p57_module -v",
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
            "git diff --check",
        ):
            self.assertIn(command, evidence)
        self.assertIn("MATLAB and Octave did not run", evidence)
        for boundary in ("No hardware/HIL", "field", "real-time", "RT1/RT2", "Unreal", "signing"):
            self.assertIn(boundary, evidence)


if __name__ == "__main__":
    unittest.main()
