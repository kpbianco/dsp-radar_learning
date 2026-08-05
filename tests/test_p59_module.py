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
MODULE = ROOT / "modules/59-track-crossing-targets-and-observe-association-failure"
QUESTION = "Why do simple nearest-neighbor trackers swap identities?"
EXPECTED_IDENTITY = {
    "number": 59,
    "id": "P59",
    "title": "Track Crossing Targets and Observe Association Failure",
    "guiding_question": QUESTION,
    "phase": 6,
    "phase_title": "Radar Tracking and Data Association",
    "slug": "track-crossing-targets-and-observe-association-failure",
    "folder": "modules/59-track-crossing-targets-and-observe-association-failure",
    "status": "implemented",
    "implementation_batch": "P59",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
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


def validate_p59_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P59 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [
        entry for entry in manifest["modules"]
        if isinstance(entry, dict) and entry.get("id") == "P59"
    ]
    if len(matches) != 1:
        errors.append("P59 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P59 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P59 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P59 empty {artifact}")
    return errors


def validate_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "seed": 5908,
        "scans": 25,
        "dt": 1.0,
        "sigma_p": 6.0,
        "sigma_v": 3.0,
        "alpha": 0.60,
        "beta": 0.25,
        "feature_weight": 1.0,
        "miss_distance": 0.0,
        "trials": 200,
        "noise_sweep": (2.0, 6.0, 10.0),
        "interval_sweep": (0.5, 1.0, 2.0),
        "separation_sweep": (0.0, 12.0, 24.0),
        "max_scans": 25,
        "max_trials": 200,
        "max_cases": 5,
        "max_passes": 3605,
        "max_pairs": 360_500,
        "max_random_per_scene": 200,
        "max_random_total": 360_200,
        "max_figures": 6,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    for name in (
        "seed", "scans", "trials", "max_scans", "max_trials", "max_cases",
        "max_passes", "max_pairs", "max_random_per_scene", "max_random_total",
        "max_figures",
    ):
        if not integer(controls[name]):
            raise ValueError(f"{name} integer")
    if not 1 <= controls["seed"] < MODULUS:
        raise ValueError("seed range")
    if not 3 <= controls["scans"] <= controls["max_scans"] == 25:
        raise ValueError("scan bound")
    if not 1 <= controls["trials"] <= controls["max_trials"] == 200:
        raise ValueError("trial bound")
    for name in ("dt", "sigma_p", "sigma_v", "alpha", "beta"):
        if not finite_real(controls[name]) or controls[name] <= 0:
            raise ValueError(f"{name} positive")
    if controls["alpha"] > 1 or controls["beta"] > 1:
        raise ValueError("gain range")
    if not finite_real(controls["feature_weight"]) or controls["feature_weight"] < 0:
        raise ValueError("feature weight")
    if not finite_real(controls["miss_distance"]) or controls["miss_distance"] < 0:
        raise ValueError("miss distance")
    for name, baseline, positive in (
        ("noise_sweep", controls["sigma_p"], True),
        ("interval_sweep", controls["dt"], True),
        ("separation_sweep", controls["miss_distance"], False),
    ):
        values = controls[name]
        if (
            not isinstance(values, (tuple, list))
            or not values
            or len(values) > controls["max_cases"]
            or not all(finite_real(value) for value in values)
            or any(right <= left for left, right in zip(values, values[1:]))
            or list(values).count(baseline) != 1
            or (positive and any(value <= 0 for value in values))
            or (not positive and any(value < 0 for value in values))
        ):
            raise ValueError(f"{name} invalid")
    cases = sum(len(controls[name]) for name in (
        "noise_sweep", "interval_sweep", "separation_sweep"
    ))
    passes = 2 + 2 * controls["trials"] * cases + 2
    pairs = passes * controls["scans"] * 4
    random_values_per_scene = controls["scans"] * 2 * 4
    random_values_total = random_values_per_scene * (controls["trials"] * cases + 1)
    if (
        controls["max_passes"] != 3605
        or controls["max_pairs"] != 360_500
        or controls["max_random_per_scene"] != 200
        or controls["max_random_total"] != 360_200
        or controls["max_figures"] != 6
        or passes > controls["max_passes"]
        or pairs > controls["max_pairs"]
        or random_values_per_scene > controls["max_random_per_scene"]
        or random_values_total > controls["max_random_total"]
    ):
        raise ValueError("resource ceiling")
    return controls


def private_gaussian(seed: object, count: object, maximum: int = 200) -> tuple[float, ...]:
    if not integer(seed) or not 1 <= seed < MODULUS:
        raise ValueError("seed")
    if not integer(count) or not 1 <= count <= maximum:
        raise ValueError("count")
    state = int(seed)
    values: list[float] = []
    for _ in range(math.ceil(int(count) / 2)):
        state = (MULTIPLIER * state) % MODULUS
        uniform_1 = (state + 0.5) / MODULUS
        state = (MULTIPLIER * state) % MODULUS
        uniform_2 = (state + 0.5) / MODULUS
        radius = math.sqrt(-2 * math.log(uniform_1))
        angle = 2 * math.pi * uniform_2
        values.extend((radius * math.cos(angle), radius * math.sin(angle)))
    return tuple(values[: int(count)])


def build_scene(
    seed: object = 5908,
    sigma_p: object = 6.0,
    dt: object = 1.0,
    miss_distance: object = 0.0,
    scans: object = 25,
    sigma_v: object = 3.0,
) -> dict[str, object]:
    if not integer(scans) or not 3 <= scans <= 25 or int(scans) % 2 != 1:
        raise ValueError("scans")
    for name, value, allow_zero in (
        ("sigma_p", sigma_p, False), ("dt", dt, False),
        ("miss_distance", miss_distance, True), ("sigma_v", sigma_v, False),
    ):
        if not finite_real(value) or value < 0 or (not allow_zero and value == 0):
            raise ValueError(name)
    noise = private_gaussian(seed, int(scans) * 2 * 4)
    cursor = 0
    centre = (int(scans) + 1) // 2
    truth_velocity = ((20.0, 5.0), (20.0, -5.0))
    truth_position: list[list[tuple[float, float]]] = []
    report_position: list[list[tuple[float, float]]] = []
    report_velocity: list[list[tuple[float, float]]] = []
    report_truth: list[list[int]] = []
    for scan in range(int(scans)):
        time = (scan + 1 - centre) * float(dt)
        truth = [
            (20 * time - float(miss_distance) / 2, 5 * time),
            (20 * time + float(miss_distance) / 2, -5 * time),
        ]
        unsorted_position: list[tuple[float, float]] = []
        unsorted_velocity: list[tuple[float, float]] = []
        for truth_id in range(2):
            unsorted_position.append((
                truth[truth_id][0] + float(sigma_p) * noise[cursor],
                truth[truth_id][1] + float(sigma_p) * noise[cursor + 1],
            ))
            unsorted_velocity.append((
                truth_velocity[truth_id][0] + float(sigma_v) * noise[cursor + 2],
                truth_velocity[truth_id][1] + float(sigma_v) * noise[cursor + 3],
            ))
            cursor += 4
        order = (0, 1) if scan % 2 == 0 else (1, 0)
        truth_position.append(truth)
        report_position.append([unsorted_position[index] for index in order])
        report_velocity.append([unsorted_velocity[index] for index in order])
        report_truth.append([index + 1 for index in order])
    return {
        "truth_position": truth_position,
        "truth_velocity": truth_velocity,
        "initial_position": truth_position[0],
        "initial_velocity": truth_velocity,
        "report_position": report_position,
        "report_velocity": report_velocity,
        "report_truth": report_truth,
        "sigma_p": float(sigma_p), "sigma_v": float(sigma_v), "dt": float(dt),
    }


def validate_scene(scene: object) -> None:
    if not isinstance(scene, dict):
        raise ValueError("scene object")
    required = {
        "initial_position", "initial_velocity", "report_position",
        "report_velocity", "report_truth", "sigma_p", "sigma_v", "dt",
    }
    if not required <= set(scene):
        raise ValueError("scene keys")
    if not all(finite_real(scene[name]) and scene[name] > 0 for name in ("sigma_p", "sigma_v", "dt")):
        raise ValueError("scene scales")
    reports = scene["report_position"]
    velocities = scene["report_velocity"]
    truths = scene["report_truth"]
    if not isinstance(reports, list) or not 3 <= len(reports) <= 25:
        raise ValueError("scan record")
    if not isinstance(velocities, list) or not isinstance(truths, list) or not (len(reports) == len(velocities) == len(truths)):
        raise ValueError("scan alignment")
    for position_row, velocity_row, truth_row in zip(reports, velocities, truths):
        if not all(isinstance(row, list) and len(row) == 2 for row in (position_row, velocity_row, truth_row)):
            raise ValueError("report row")
        for vector in position_row + velocity_row:
            if not isinstance(vector, tuple) or len(vector) != 2 or not all(finite_real(value) for value in vector):
                raise ValueError("report vector")
        if sorted(truth_row) != [1, 2]:
            raise ValueError("audit identity")


def run_tracker(scene: object, feature_weight: object = 0.0, allow_reuse: object = False) -> dict[str, object]:
    validate_scene(scene)
    if not finite_real(feature_weight) or feature_weight < 0:
        raise ValueError("feature weight")
    if not isinstance(allow_reuse, bool):
        raise ValueError("reuse flag")
    track_position = [list(vector) for vector in scene["initial_position"]]
    track_velocity = [list(vector) for vector in scene["initial_velocity"]]
    assignments: list[list[int]] = []
    positions: list[list[tuple[float, float]]] = []
    velocities: list[list[tuple[float, float]]] = []
    costs: list[list[list[float]]] = []
    duplicate_scans = 0
    for scan, (position_row, velocity_row) in enumerate(zip(scene["report_position"], scene["report_velocity"])):
        predicted = [
            list(track_position[track]) if scan == 0 else [
                track_position[track][axis] + scene["dt"] * track_velocity[track][axis]
                for axis in range(2)
            ] for track in range(2)
        ]
        matrix = [[0.0] * 2 for _ in range(2)]
        for track in range(2):
            for report in range(2):
                position_cost = sum(
                    (position_row[report][axis] - predicted[track][axis]) ** 2
                    for axis in range(2)
                ) / scene["sigma_p"] ** 2
                velocity_cost = sum(
                    (velocity_row[report][axis] - track_velocity[track][axis]) ** 2
                    for axis in range(2)
                ) / scene["sigma_v"] ** 2
                matrix[track][report] = position_cost + float(feature_weight) * velocity_cost
        if allow_reuse:
            assignment = [min(range(2), key=lambda report: matrix[track][report]) for track in range(2)]
        else:
            candidates = sorted(
                (matrix[track][report], report, track)
                for track in range(2) for report in range(2)
            )
            assignment = [-1, -1]
            used_tracks: set[int] = set()
            used_reports: set[int] = set()
            for _, report, track in candidates:
                if track not in used_tracks and report not in used_reports:
                    assignment[track] = report
                    used_tracks.add(track)
                    used_reports.add(report)
        if assignment[0] == assignment[1]:
            duplicate_scans += 1
        for track, report in enumerate(assignment):
            residual = [position_row[report][axis] - predicted[track][axis] for axis in range(2)]
            track_position[track] = [predicted[track][axis] + 0.60 * residual[axis] for axis in range(2)]
            track_velocity[track] = [
                track_velocity[track][axis] + (0.25 / scene["dt"]) * residual[axis]
                for axis in range(2)
            ]
        assignments.append(assignment)
        positions.append([tuple(vector) for vector in track_position])
        velocities.append([tuple(vector) for vector in track_velocity])
        costs.append(matrix)
    assigned_truth = [[], []]
    for scan, assignment in enumerate(assignments):
        for track, report in enumerate(assignment):
            assigned_truth[track].append(scene["report_truth"][scan][report])
    wrong = sum(
        truth_id != track + 1
        for track, history in enumerate(assigned_truth) for truth_id in history
    )
    transitions = sum(
        left != right
        for history in assigned_truth for left, right in zip(history, history[1:])
    )
    return {
        "assignment": assignments, "positions": positions, "velocities": velocities,
        "costs": costs, "assigned_truth": assigned_truth, "wrong": wrong,
        "transitions": transitions, "duplicate_scans": duplicate_scans,
    }


def sweep(kind: str, values: tuple[float, ...]) -> tuple[list[int], list[int], list[int], list[int]]:
    position_failures: list[int] = []
    velocity_failures: list[int] = []
    position_wrong: list[int] = []
    velocity_wrong: list[int] = []
    for value in values:
        failures = [0, 0]
        wrong = [0, 0]
        for seed in range(5901, 6101):
            options = {"sigma_p": 6.0, "dt": 1.0, "miss_distance": 0.0}
            options[kind] = value
            scene = build_scene(seed=seed, **options)
            for method, weight in enumerate((0.0, 1.0)):
                result = run_tracker(scene, weight)
                failures[method] += result["wrong"] > 0
                wrong[method] += result["wrong"]
        position_failures.append(failures[0])
        velocity_failures.append(failures[1])
        position_wrong.append(wrong[0])
        velocity_wrong.append(wrong[1])
    return position_failures, velocity_failures, position_wrong, velocity_wrong


class P59ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self) -> None:
        self.assertEqual(validate_p59_contract(ROOT, self.manifest), [])
        p58 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P58")
        self.assertEqual(p58["status"], "implemented")
        for artifact in ARTIFACTS:
            payload = (MODULE / artifact).read_bytes()
            self.assertNotIn(b"\r", payload)
            self.assertTrue(payload.endswith(b"\n"), artifact)
            self.assertFalse(payload.endswith(b"\n\n"), artifact)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self) -> None:
        for manifest in (None, [], {}, {"modules": None}, {"modules": "P59"}):
            self.assertTrue(validate_p59_contract(ROOT, manifest))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append("bad")
        self.assertIn("every manifest module must be an object", validate_p59_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("exactly one", " ".join(validate_p59_contract(ROOT, duplicate)))
        compatible = copy.deepcopy(self.manifest)
        next(entry for entry in compatible["modules"] if entry["id"] == "P59")["future_metadata"] = True
        self.assertEqual(validate_p59_contract(ROOT, compatible), [])
        for key in EXPECTED_IDENTITY:
            changed = copy.deepcopy(self.manifest)
            entry = next(item for item in changed["modules"] if item["id"] == "P59")
            entry[key] = 999 if key in {"number", "phase"} else "drift"
            self.assertTrue(validate_p59_contract(ROOT, changed), key)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            shutil.copytree(MODULE, fixture / EXPECTED_IDENTITY["folder"])
            target = fixture / EXPECTED_IDENTITY["folder"] / "experiment.m"
            target.unlink()
            self.assertIn("P59 missing experiment.m", validate_p59_contract(fixture, self.manifest))
            target.write_text("", encoding="utf-8")
            self.assertIn("P59 empty experiment.m", validate_p59_contract(fixture, self.manifest))

    def test_controls_reject_malformed_nonfinite_and_resource_inputs(self) -> None:
        reviewed = validate_controls()
        self.assertEqual(reviewed["max_pairs"], 360_500)
        bad = (
            {"unknown": 1}, {"seed": 0}, {"seed": MODULUS}, {"scans": True},
            {"scans": 26}, {"trials": 201}, {"dt": 0}, {"sigma_p": math.nan},
            {"sigma_v": complex(3, 1)}, {"alpha": 1.1}, {"beta": 0},
            {"feature_weight": -1}, {"miss_distance": -1}, {"max_pairs": 360_501},
            {"max_passes": 3606}, {"max_random_per_scene": 201},
            {"max_random_total": 360_201}, {"max_figures": 7},
            {"noise_sweep": ()}, {"noise_sweep": (2, 6, 6)},
            {"noise_sweep": (2, 4, 10)}, {"interval_sweep": (0, 1, 2)},
            {"separation_sweep": (-1, 0, 24)},
            {"separation_sweep": (0, 6, 12, 18, 24, 30)},
        )
        for controls in bad:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_private_seeded_record_is_exact_repeatable_and_bounded(self) -> None:
        expected = (1.7504860308069068, 1.7560458598250133, -0.579064234411043, -1.9921898560066356)
        first = private_gaussian(5908, 200)
        self.assertEqual(first, private_gaussian(5908, 200))
        for actual, wanted in zip(first, expected):
            self.assertAlmostEqual(actual, wanted, places=14)
        for args in ((0, 1), (MODULUS, 1), (True, 1), (5908, 0), (5908, 201), (5908, 2.5)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                private_gaussian(*args)

    def test_baseline_swap_velocity_reduction_and_exact_recovery(self) -> None:
        scene = build_scene()
        position = run_tracker(scene, 0.0)
        velocity = run_tracker(scene, 1.0)
        recovered = run_tracker(scene, 1.0)
        self.assertEqual(position["wrong"], 24)
        self.assertEqual(position["transitions"], 2)
        self.assertEqual(position["assigned_truth"][0][:13], [1] * 13)
        self.assertEqual(position["assigned_truth"][0][13:], [2] * 12)
        self.assertEqual(velocity["wrong"], 0)
        self.assertEqual(velocity["transitions"], 0)
        self.assertEqual(recovered["assignment"], velocity["assignment"])
        self.assertEqual(recovered["positions"], velocity["positions"])
        self.assertEqual(recovered["velocities"], velocity["velocities"])
        self.assertEqual(run_tracker(scene, 0.0), position)

    def test_report_permutation_does_not_change_physical_track_histories(self) -> None:
        scene = build_scene()
        permuted = copy.deepcopy(scene)
        for field in ("report_position", "report_velocity", "report_truth"):
            permuted[field] = [list(reversed(scan)) for scan in permuted[field]]

        for feature_weight in (0.0, 1.0):
            with self.subTest(feature_weight=feature_weight):
                reviewed = run_tracker(scene, feature_weight)
                reordered = run_tracker(permuted, feature_weight)
                for field in (
                    "assigned_truth", "positions", "velocities", "wrong",
                    "transitions", "duplicate_scans",
                ):
                    self.assertEqual(reviewed[field], reordered[field], field)

    def test_one_to_one_and_broken_duplicate_report_behavior(self) -> None:
        scene = build_scene()
        valid = run_tracker(scene, 0.0)
        self.assertTrue(all(sorted(assignment) == [0, 1] for assignment in valid["assignment"]))
        self.assertEqual(valid["duplicate_scans"], 0)
        broken = run_tracker(scene, 0.0, True)
        self.assertEqual(broken["duplicate_scans"], 12)
        self.assertEqual(broken["wrong"], 12)
        self.assertEqual(broken["transitions"], 1)

    def test_sweeps_reuse_seed_family_and_show_reviewed_tradeoffs(self) -> None:
        noise = sweep("sigma_p", (2.0, 6.0, 10.0))
        interval = sweep("dt", (0.5, 1.0, 2.0))
        separation = sweep("miss_distance", (0.0, 12.0, 24.0))
        self.assertEqual(noise, ([97, 163, 189], [14, 38, 101], [194, 1198, 2278], [28, 280, 998]))
        self.assertEqual(interval, ([196, 163, 118], [118, 38, 20], [2720, 1198, 348], [1318, 280, 62]))
        self.assertEqual(separation, ([163, 109, 16], [38, 18, 2], [1198, 1226, 362], [280, 98, 24]))
        for result in (noise, interval, separation):
            self.assertTrue(all(rich < simple for rich, simple in zip(result[1], result[0])))

    def test_oracle_rejects_malformed_shapes_nonfinite_values_and_controls(self) -> None:
        for options in (
            {"seed": 0}, {"seed": True}, {"sigma_p": 0}, {"sigma_p": math.inf},
            {"sigma_v": 0}, {"dt": 0}, {"miss_distance": -1}, {"scans": 26},
            {"scans": 24},
        ):
            with self.subTest(options=options), self.assertRaises(ValueError):
                build_scene(**options)
        scene = build_scene()
        malformed = (None, [], {}, {"report_position": []})
        for record in malformed:
            with self.subTest(record=record), self.assertRaises(ValueError):
                run_tracker(record)
        for weight in (-1, math.nan, math.inf, complex(1, 1), True):
            with self.subTest(weight=weight), self.assertRaises(ValueError):
                run_tracker(scene, weight)
        with self.assertRaises(ValueError):
            run_tracker(scene, 0.0, 1)
        corrupt = copy.deepcopy(scene)
        corrupt["report_position"][0][0] = (math.nan, 0.0)
        with self.assertRaises(ValueError):
            run_tracker(corrupt)
        corrupt = copy.deepcopy(scene)
        corrupt["report_truth"][0] = [1, 1]
        with self.assertRaises(ValueError):
            run_tracker(corrupt)

    def test_source_is_explicit_seeded_bounded_and_mutation_sensitive(self) -> None:
        required = (
            "baseline_seed = 5908;", "position_noise_sweep_m = [2 6 10];",
            "update_interval_sweep_s = [0.5 1 2];",
            "closest_approach_sweep_m = [0 12 24];",
            "remaining_cost(selected_track,:) = inf;",
            "remaining_cost(:,selected_report) = inf;",
            "sum(position_residual_m.^2)/scene.position_noise_sigma_m^2;",
            "feature_weight*velocity_cost(track,report,scan);",
            "(c.velocity_gain/scene.scan_interval_s)*residual_m;",
            "report_truth_id(assignment(track,scan),scan);",
            "state = mod(multiplier*state, modulus);",
            "recovery_exact = isequal(recovered.assignment, velocity_aware.assignment)",
            "pair_evaluations > c.maximum_pair_evaluations",
            "total_random_values > c.maximum_total_random_values",
            "c.maximum_pair_evaluations ~= 360500",
            "Reviewed resource ceilings are immutable.",
            "sort(scene.report_truth_id(:,scan))",
            "Truth IDs are retained in a separate audit array",
        )
        for marker in required:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P59 Figure"), 6)
        self.assertEqual(self.source.count("'Tag', 'P59'"), 7)
        self.assertNotIn("inv(", self.source)
        forbidden = (
            "trackerGNN", "trackerJPDA", "radarTracker", "assignDetectionsToTracks",
            "matchpairs", "trackingKF", "trackingEKF", "rng(", "rand(", "randn(",
            "parfor", "timer(", "webread", "urlread", "system(", "fopen(", "save(",
        )
        for token in forbidden:
            self.assertNotIn(token, self.source)
        mutated = self.source.replace("remaining_cost(:,selected_report) = inf;", "")
        self.assertNotIn("remaining_cost(:,selected_report) = inf;", mutated)
        self.assertIn("remaining_cost(:,selected_report) = inf;", self.source)

    def test_docs_cover_dependencies_model_limits_failure_recovery_and_claims(self) -> None:
        combined = "\n".join((self.readme, self.lesson, self.walkthrough, self.checks))
        for marker in (
            QUESTION, "P57", "P58", "Base MATLAB R2016b", "Jp(i,j)",
            "dimensionless", "Limiting cases", "position_noise_sweep_m",
            "update_interval_sweep_s", "closest_approach_sweep_m",
            "24 wrong links", "two identity transitions", "12 scans",
            "coalescence", "exact", "Ctrl+C", "10-second", "rollback",
            "temporary repository", "Claim boundary", "hardware/HIL",
            "does not eliminate", "unobservable", "amplitude",
        ):
            self.assertIn(marker, combined)
        self.assertNotIn("TODO", combined)

    def test_public_catalogs_describe_p59_without_freezing_future_state(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 59 follows P58", root_readme)
        self.assertIn("Project 59 follows P58", start_here)
        self.assertRegex(module_index, r"\| \[P59\].*\| implemented \| 6 \|")

    def test_cli_timeout_isolation_rollback_recovery_and_future_compatibility(self) -> None:
        cli = ROOT / "bin/learn"
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir(parents=True)
            shutil.copy2(cli, fixture / "bin/learn")
            manifest_path = fixture / "curriculum/modules.json"
            manifest_path.write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")
            for module in self.manifest["modules"]:
                target = fixture / module["folder"] / "README.md"
                target.parent.mkdir(parents=True)
                shutil.copy2(ROOT / module["folder"] / "README.md", target)
            env = os.environ.copy()
            env["HOME"] = temporary
            start = subprocess.run(
                [str(fixture / "bin/learn"), "start", "59"], cwd=fixture,
                text=True, capture_output=True, env=env, timeout=10,
            )
            self.assertEqual(start.returncode, 0, start.stderr)
            self.assertIn("Tutor entry", start.stdout)
            rolled_back = copy.deepcopy(self.manifest)
            p59 = next(entry for entry in rolled_back["modules"] if entry["id"] == "P59")
            p58_before = copy.deepcopy(next(entry for entry in rolled_back["modules"] if entry["id"] == "P58"))
            p60_before = copy.deepcopy(next(entry for entry in rolled_back["modules"] if entry["id"] == "P60"))
            p59["status"] = "scaffolded"
            manifest_path.write_text(json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8")
            stopped = subprocess.run(
                [str(fixture / "bin/learn"), "start", "59"], cwd=fixture,
                text=True, capture_output=True, env=env, timeout=10,
            )
            self.assertEqual(stopped.returncode, 3)
            self.assertIn("awaits Portfolio batch P59", stopped.stdout)
            self.assertEqual(next(entry for entry in rolled_back["modules"] if entry["id"] == "P58"), p58_before)
            self.assertEqual(next(entry for entry in rolled_back["modules"] if entry["id"] == "P60"), p60_before)
            manifest_path.write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")
            recovered = subprocess.run(
                [str(fixture / "bin/learn"), "start", "59"], cwd=fixture,
                text=True, capture_output=True, env=env, timeout=10,
            )
            self.assertEqual(recovered.returncode, 0)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_default_tutor_entry_advances_from_completed_p58_without_state_loss(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir(parents=True)
            (fixture / ".learning").mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
            shutil.copy2(ROOT / "curriculum/modules.json", fixture / "curriculum/modules.json")
            for module in self.manifest["modules"]:
                target = fixture / module["folder"] / "README.md"
                target.parent.mkdir(parents=True)
                shutil.copy2(ROOT / module["folder"] / "README.md", target)
            state = {"schema_version": 1, "current": "P58", "completed": [f"P{n:02d}" for n in range(1, 59)], "notes": {"P58": "kept"}}
            (fixture / ".learning/progress.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            proc = subprocess.run(
                [str(fixture / "bin/learn"), "start"], cwd=fixture,
                text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("P59", proc.stdout)
            saved = json.loads((fixture / ".learning/progress.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["completed"], state["completed"])
            self.assertEqual(saved["notes"], state["notes"])
            self.assertEqual(saved["current"], "P59")

    def test_retained_evidence_has_commands_claim_boundary_and_single_newline(self) -> None:
        evidence = sorted((ROOT / "docs/evidence").glob("P59-*.md"))
        self.assertEqual(len(evidence), 1)
        payload = evidence[0].read_bytes()
        self.assertTrue(payload.endswith(b"\n"))
        self.assertFalse(payload.endswith(b"\n\n"))
        text = payload.decode("utf-8")
        for marker in (
            "# P59 Retained Evidence", "Acceptance map", "Exact commands and results",
            "Figure and metric inventory", "Changed and preserved invariants",
            "Residual risks", "Rollback and recovery", "Unperformed validation",
            "python3 scripts/validate_curriculum.py", "python3 -m unittest discover",
            "./scripts/agent-verify.sh", "MATLAB", "unavailable", "static",
            "hardware/HIL", "field", "real-time", "production",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
