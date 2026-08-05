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
MODULE = ROOT / "modules/58-implement-track-initiation-confirmation-coasting-and-deletion"
QUESTION = "How does a radar avoid creating permanent tracks from single false alarms?"
EXPECTED_IDENTITY = {
    "number": 58,
    "id": "P58",
    "title": "Implement Track Initiation, Confirmation, Coasting, and Deletion",
    "slug": "implement-track-initiation-confirmation-coasting-and-deletion",
    "phase": 6,
    "phase_title": "Radar Tracking and Data Association",
    "guiding_question": QUESTION,
    "folder": "modules/58-implement-track-initiation-confirmation-coasting-and-deletion",
    "status": "implemented",
    "implementation_batch": "P58",
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


def validate_p58_contract(root: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P58 manifest must contain a module list"]
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [entry for entry in manifest["modules"] if isinstance(entry, dict) and entry.get("id") == "P58"]
    if len(matches) != 1:
        errors.append("P58 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P58 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P58 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P58 empty {artifact}")
    return errors


def validate_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "false_seed": 5801,
        "noise_seed": 5802,
        "scans": 30,
        "dt": 1.0,
        "gate": 40.0,
        "alpha": 0.70,
        "beta": 0.20,
        "m": 3,
        "n": 4,
        "coasts": 2,
        "m_sweep": (1, 3, 4),
        "coast_sweep": (0, 2, 5),
        "max_detections": 2,
        "max_tracks": 20,
        "max_sweep": 5,
        "max_runs": 9,
        "max_pairs": 12_000,
        "max_figures": 6,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    for name in (
        "false_seed", "noise_seed", "scans", "m", "n", "coasts",
        "max_detections", "max_tracks", "max_sweep", "max_runs",
        "max_pairs", "max_figures",
    ):
        if not integer(controls[name]):
            raise ValueError(f"{name} integer")
    if not (1 <= controls["false_seed"] < MODULUS and 1 <= controls["noise_seed"] < MODULUS):
        raise ValueError("seed range")
    if not (1 <= controls["m"] <= controls["n"] <= controls["scans"]):
        raise ValueError("M-of-N")
    if controls["coasts"] < 0 or controls["coasts"] > controls["scans"]:
        raise ValueError("coast limit")
    for name in ("dt", "gate", "alpha", "beta"):
        if not finite_real(controls[name]):
            raise ValueError(f"{name} finite real")
    if controls["dt"] <= 0 or controls["gate"] <= 0:
        raise ValueError("positive scale")
    if not (0 < controls["alpha"] <= 1 and 0 < controls["beta"] <= 1):
        raise ValueError("gain range")
    if controls["scans"] > 30 or controls["max_detections"] != 2 or controls["max_tracks"] != 20:
        raise ValueError("scene ceiling")
    if controls["max_sweep"] != 5 or controls["max_runs"] != 9:
        raise ValueError("run ceiling")
    if controls["max_pairs"] != 12_000 or controls["max_figures"] != 6:
        raise ValueError("fixed ceiling drift")
    for name, lower, upper, baseline in (
        ("m_sweep", 1, controls["n"], controls["m"]),
        ("coast_sweep", 0, controls["scans"], controls["coasts"]),
    ):
        values = controls[name]
        if not isinstance(values, (tuple, list)) or not values or len(values) > controls["max_sweep"]:
            raise ValueError(f"{name} shape")
        if not all(integer(value) and lower <= value <= upper for value in values):
            raise ValueError(f"{name} values")
        if any(right <= left for left, right in zip(values, values[1:])):
            raise ValueError(f"{name} increasing")
        if list(values).count(baseline) != 1:
            raise ValueError(f"{name} baseline")
    runs = 1 + len(controls["m_sweep"]) + len(controls["coast_sweep"]) + 1 + 1
    pair_slots = runs * controls["scans"] * controls["max_tracks"] * controls["max_detections"]
    if runs > controls["max_runs"] or pair_slots > controls["max_pairs"]:
        raise ValueError("resource work bound")
    return controls


def seeded_uniform(seed: object, count: object) -> tuple[float, ...]:
    if not integer(seed) or not (1 <= seed < MODULUS):
        raise ValueError("seed")
    if not integer(count) or not (1 <= count <= 60):
        raise ValueError("count")
    state = int(seed)
    values = []
    for _ in range(int(count)):
        state = (MULTIPLIER * state) % MODULUS
        values.append(state / MODULUS)
    return tuple(values)


def seeded_gaussian(seed: object, count: object) -> tuple[float, ...]:
    if not integer(count) or count < 1:
        raise ValueError("count")
    uniforms = seeded_uniform(seed, 2 * math.ceil(int(count) / 2))
    values: list[float] = []
    for index in range(0, len(uniforms), 2):
        radius = math.sqrt(-2 * math.log(max(uniforms[index], 1 / MODULUS)))
        phase = 2 * math.pi * uniforms[index + 1]
        values.extend((radius * math.cos(phase), radius * math.sin(phase)))
    return tuple(values[: int(count)])


def canonical_scene() -> tuple[list[list[tuple[float, int]]], tuple[float, ...]]:
    false_scans = (2, 5, 8, 11, 15, 18, 22, 26)
    false_uniform = seeded_uniform(5801, len(false_scans))
    false_positions = tuple(
        100 + 100 * index + 20 * (value - 0.5)
        for index, value in enumerate(false_uniform)
    )
    target_scans = tuple(scan for scan in range(4, 25) if scan not in (6, 12, 13))
    noise = seeded_gaussian(5802, len(target_scans))
    target_reports = {
        scan: 1000 + 12 * (scan - 4) + 3 * noise[index]
        for index, scan in enumerate(target_scans)
    }
    detections: list[list[tuple[float, int]]] = []
    for scan in range(1, 31):
        scan_reports: list[tuple[float, int]] = []
        if scan in target_reports:
            scan_reports.append((target_reports[scan], 1))
        if scan in false_scans:
            scan_reports.append((false_positions[false_scans.index(scan)], 0))
        detections.append(sorted(scan_reports))
    return detections, false_positions


def validate_detection_record(detections: object, max_tracks: int = 20) -> None:
    if not isinstance(detections, list) or not detections or len(detections) > 30:
        raise ValueError("scan record")
    if not integer(max_tracks) or not (1 <= max_tracks <= 20):
        raise ValueError("track bound")
    for scan_reports in detections:
        if not isinstance(scan_reports, list) or len(scan_reports) > 2:
            raise ValueError("detection row")
        for report in scan_reports:
            if not isinstance(report, tuple) or len(report) != 2:
                raise ValueError("report shape")
            position, truth = report
            if not finite_real(position) or truth not in (0, 1) or isinstance(truth, bool):
                raise ValueError("report value")


def run_manager(
    detections: list[list[tuple[float, int]]], m: object = 3, n: object = 4,
    coast_limit: object = 2, max_tracks: object = 20,
) -> dict[str, object]:
    validate_detection_record(detections, int(max_tracks) if integer(max_tracks) else -1)
    if not all(integer(value) for value in (m, n, coast_limit, max_tracks)):
        raise ValueError("integer policy")
    if not (1 <= m <= n <= 30) or not (0 <= coast_limit <= 30) or not (1 <= max_tracks <= 20):
        raise ValueError("policy range")
    tracks: list[dict[str, object]] = []
    scans = len(detections)
    lifecycle = [[0] * scans for _ in range(int(max_tracks))]
    score_history = [[0] * scans for _ in range(int(max_tracks))]
    miss_history = [[0] * scans for _ in range(int(max_tracks))]
    position_history = [[math.nan] * scans for _ in range(int(max_tracks))]
    assignment_history = [[0] * scans for _ in range(int(max_tracks))]
    active_counts: list[int] = []
    tentative_counts: list[int] = []
    confirmed_counts: list[int] = []
    coasting_counts: list[int] = []
    for scan_index, scan_reports in enumerate(detections):
        active_start = [index for index, track in enumerate(tracks) if track["active"]]
        for index in active_start:
            track = tracks[index]
            track["prediction"] = track["position"] + track["velocity"]
        candidates: list[tuple[float, int, int]] = []
        for track_index in active_start:
            for detection_index, (position, _) in enumerate(scan_reports):
                distance = abs(position - tracks[track_index]["prediction"])
                if distance <= 40:
                    candidates.append((distance, detection_index, track_index))
        candidates.sort()
        used_tracks: set[int] = set()
        used_detections: set[int] = set()
        assignments: dict[int, int] = {}
        for _, detection_index, track_index in candidates:
            if track_index not in used_tracks and detection_index not in used_detections:
                assignments[track_index] = detection_index
                used_tracks.add(track_index)
                used_detections.add(detection_index)
        for track_index in active_start:
            track = tracks[track_index]
            track["age"] += 1
            has_hit = track_index in assignments
            track["history"] = track["history"][1:] + [int(has_hit)]
            if has_hit:
                detection_index = assignments[track_index]
                position, truth = scan_reports[detection_index]
                residual = position - track["prediction"]
                track["position"] = track["prediction"] + 0.70 * residual
                track["velocity"] += 0.20 * residual
                track["misses"] = 0
                track["truth_hits"][truth] = track["truth_hits"].get(truth, 0) + 1
                assignment_history[track_index][scan_index] = detection_index + 1
            else:
                track["position"] = track["prediction"]
                track["misses"] += 1
            hit_score = sum(track["history"])
            if not track["confirmed"] and hit_score >= m:
                track["confirmed"] = True
                track["confirmation"] = scan_index + 1
            deleted = False
            if not track["confirmed"] and track["age"] >= n and hit_score < m:
                track["active"] = False
                track["deletion"] = scan_index + 1
                deleted = True
            elif track["confirmed"] and track["misses"] > coast_limit:
                track["active"] = False
                track["deletion"] = scan_index + 1
                deleted = True
            code = 4 if deleted else 1 if not track["confirmed"] else 3 if track["misses"] else 2
            lifecycle[track_index][scan_index] = code
            score_history[track_index][scan_index] = hit_score
            miss_history[track_index][scan_index] = track["misses"]
            position_history[track_index][scan_index] = track["position"]
        for detection_index, (position, truth) in enumerate(scan_reports):
            if detection_index in used_detections:
                continue
            if len(tracks) >= max_tracks:
                raise ValueError("track resource bound")
            confirmed = m <= 1
            track = {
                "id": len(tracks) + 1, "active": True, "confirmed": confirmed,
                "position": position, "velocity": 0.0, "prediction": position,
                "age": 1, "misses": 0, "history": [0] * (int(n) - 1) + [1],
                "birth": scan_index + 1, "confirmation": scan_index + 1 if confirmed else 0,
                "deletion": 0, "birth_truth": truth, "truth_hits": {truth: 1},
            }
            tracks.append(track)
            track_index = len(tracks) - 1
            lifecycle[track_index][scan_index] = 2 if confirmed else 1
            score_history[track_index][scan_index] = 1
            position_history[track_index][scan_index] = position
            assignment_history[track_index][scan_index] = detection_index + 1
        tentative_counts.append(sum(t["active"] and not t["confirmed"] for t in tracks))
        confirmed_counts.append(sum(t["active"] and t["confirmed"] and not t["misses"] for t in tracks))
        coasting_counts.append(sum(t["active"] and t["confirmed"] and t["misses"] > 0 for t in tracks))
        active_counts.append(sum(t["active"] for t in tracks))
    target_tracks = [track for track in tracks if track["birth_truth"] == 1]
    false_tracks = [track for track in tracks if track["birth_truth"] == 0]
    confirmed_target = [track for track in target_tracks if track["confirmation"]]
    confirmed_false = [track for track in false_tracks if track["confirmation"]]
    first_target = confirmed_target[0] if confirmed_target else None
    gap_survived = bool(
        first_target
        and lifecycle[first_target["id"] - 1][11:14] == [3, 3, 2]
    )
    return {
        "tracks": tracks, "lifecycle": lifecycle, "score": score_history,
        "misses": miss_history, "positions": position_history,
        "assignments": assignment_history, "active_counts": active_counts,
        "tentative_counts": tentative_counts, "confirmed_counts": confirmed_counts,
        "coasting_counts": coasting_counts,
        "target_confirmation": min((t["confirmation"] for t in confirmed_target), default=0),
        "target_last_deletion": max((t["deletion"] for t in confirmed_target), default=0),
        "confirmed_target_count": len(confirmed_target),
        "false_track_count": len(false_tracks),
        "false_confirmed": len(confirmed_false),
        "false_deleted": sum(bool(t["deletion"]) for t in false_tracks),
        "gap_survived": gap_survived,
        "allocated": len(tracks), "peak_active": max(active_counts),
        "final_active": active_counts[-1],
    }


def source_binding_errors(source: str) -> list[str]:
    required = (
        "false_alarm_seed = 5801;", "target_noise_seed = 5802;",
        "confirmation_m = 3;", "confirmation_n = 4;",
        "maximum_consecutive_coasts = 2;",
        "hit_history(track_id, confirmation_n) = has_hit;",
        "hit_history(track_id, confirmation_n) = true;",
        "hit_history(track_id, 2:confirmation_n);",
        "hit_score >= confirmation_m", "age_scans(track_id) >= confirmation_n",
        "hit_score < confirmation_m", "consecutive_misses(track_id) + 1",
        "consecutive_misses(track_id) > maximum_consecutive_coasts",
        "consecutive_misses(track_id) = 0;", "lifecycle_history(track_id, scan) = 4;",
        "confirmed(track_id) = confirmation_m <= 1;", "age_scans(track_id) = 1;",
        "pair_distance_m(track_id, :) = Inf;",
        "pair_distance_m(:, detection_index) = Inf;",
        "detection_used(detection_index) = true;",
        "find(detection_valid(:, scan) & ~detection_used)'",
        "if ~confirmed(track_id) && hit_score >= confirmation_m",
        "if ~confirmed(track_id) && age_scans(track_id) >= confirmation_n",
        "if abs(residual_m) <= association_gate_m",
        "age_scans(track_id) = age_scans(track_id) + 1;",
        "scan_interval_s*velocity_mps(active_at_scan_start);",
        "position_m(track_id) = predicted_position_m(track_id);",
        "(velocity_gain/scan_interval_s)*residual_m;",
        "radius = sqrt(-2*log(uniform_1));",
        "confirmation_m_sweep(sweep_index)", "coast_limit_sweep_scans(sweep_index)",
        "1, 1, number_scans", "recovery_exact = lifecycle_results_equal(recovered, baseline);",
        "reviewed_pair_slots > maximum_pair_evaluations",
        "state = mod(multiplier*state, modulus);",
        "~isnumeric(detection_position_m) || ~isreal(detection_position_m)",
        "confirmation_n > 30", "maximum_consecutive_coasts > 30",
        "birth_truth_id(track_id) = detection_truth_id(birth_detection, birth);",
        "false_track = allocated & birth_truth_id == 0;",
        "Truth labels enter only here, after all associations and lifecycle decisions.",
        "active_at_scan_start = find(active);",
        "allocated_track_count = allocated_track_count + 1;",
    )
    errors = [f"missing source marker: {marker}" for marker in required if marker not in source]
    if source.count("figure('Name', 'P58 Figure") != 6:
        errors.append("six bounded figures")
    if source.count("'Tag', 'P58'") != 7:
        errors.append("P58 figure tag count")
    if source.count("consecutive_misses(track_id) = 0;") < 2:
        errors.append("miss reset on initialization and hit")
    if source.count("active(track_id) = false;") != 2:
        errors.append("tentative and confirmed deletion must deactivate")
    if source.count("deletion_scan(track_id) = scan;") != 2:
        errors.append("both deletion branches must record the event scan")
    for state_code in (1, 2, 3, 4):
        if f"lifecycle_history(track_id, scan) = {state_code};" not in source:
            errors.append(f"missing lifecycle state code {state_code}")
    if re.search(r"confirmed\s*\(\s*track_id\s*\)\s*=\s*false", source):
        errors.append("confirmed tracks must not deconfirm")
    return errors


class P58ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self) -> None:
        self.assertEqual(validate_p58_contract(ROOT, self.manifest), [])
        p57 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P57")
        self.assertEqual(p57["status"], "implemented")
        for artifact in ARTIFACTS:
            payload = (MODULE / artifact).read_bytes()
            self.assertNotIn(b"\r", payload)
            self.assertTrue(payload.endswith(b"\n"), artifact)
            self.assertFalse(payload.endswith(b"\n\n"), artifact)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self) -> None:
        for manifest in (None, [], {}, {"modules": None}, {"modules": "P58"}):
            with self.subTest(manifest=manifest):
                self.assertTrue(validate_p58_contract(ROOT, manifest))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("exactly one", " ".join(validate_p58_contract(ROOT, duplicate)))
        malformed_entry = copy.deepcopy(self.manifest)
        malformed_entry["modules"].append("not an object")
        self.assertIn("every manifest module must be an object", validate_p58_contract(ROOT, malformed_entry))
        compatible_extension = copy.deepcopy(self.manifest)
        next(item for item in compatible_extension["modules"] if item["id"] == "P58")["future_metadata"] = True
        self.assertEqual(validate_p58_contract(ROOT, compatible_extension), [])
        for key in EXPECTED_IDENTITY:
            changed = copy.deepcopy(self.manifest)
            entry = next(item for item in changed["modules"] if item["id"] == "P58")
            entry[key] = "drift" if key not in {"number", "phase"} else 999
            self.assertTrue(validate_p58_contract(ROOT, changed), key)
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture = Path(temporary_directory)
            shutil.copytree(MODULE, fixture / EXPECTED_IDENTITY["folder"])
            missing = fixture / EXPECTED_IDENTITY["folder"] / "experiment.m"
            missing.unlink()
            self.assertIn("P58 missing experiment.m", validate_p58_contract(fixture, self.manifest))
            missing.write_text("", encoding="utf-8")
            self.assertIn("P58 empty experiment.m", validate_p58_contract(fixture, self.manifest))

    def test_controls_accept_reviewed_and_reject_malformed_or_unbounded_values(self) -> None:
        reviewed = validate_controls()
        self.assertEqual(reviewed["m_sweep"], (1, 3, 4))
        reviewed_runs = 1 + len(reviewed["m_sweep"]) + len(reviewed["coast_sweep"]) + 1 + 1
        reviewed_pair_slots = reviewed_runs * reviewed["scans"] * reviewed["max_tracks"] * reviewed["max_detections"]
        self.assertEqual(reviewed_runs, 9)
        self.assertEqual(reviewed_pair_slots, 10_800)
        bad_cases = (
            {"unknown": 1}, {"false_seed": 0}, {"noise_seed": MODULUS},
            {"scans": True}, {"scans": 31}, {"dt": 0}, {"gate": math.nan},
            {"alpha": 1.1}, {"beta": complex(1, 1)}, {"m": 0}, {"n": 0},
            {"m": 5}, {"coasts": -1}, {"coasts": 31}, {"max_tracks": 21},
            {"max_detections": 3}, {"max_runs": 10}, {"max_pairs": 12001},
            {"max_figures": 7}, {"m_sweep": ()}, {"m_sweep": (1, 3, 3)},
            {"m_sweep": (1, 2, 4)}, {"m_sweep": (1, 3, math.inf)},
            {"coast_sweep": (0, 2, 2)}, {"coast_sweep": (0, 1, 5)},
            {"coast_sweep": tuple(range(6))},
        )
        for controls in bad_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_seeded_records_are_exact_repeatable_and_private(self) -> None:
        expected = (
            0.04540076807392797, 0.0507090185073712,
            0.2664740533877509, 0.6294152879293148,
        )
        first = seeded_uniform(5801, 8)
        second = seeded_uniform(5801, 8)
        self.assertEqual(first, second)
        for actual, wanted in zip(first, expected):
            self.assertAlmostEqual(actual, wanted, places=15)
        _, positions = canonical_scene()
        self.assertAlmostEqual(min(b - a for a, b in zip(positions, positions[1:])), 83.76807785768427)
        self.assertLess(max(positions) + 40, 1000)
        for args in ((0, 1), (MODULUS, 1), (True, 1), (5801, 0), (5801, 61), (5801, 2.5)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                seeded_uniform(*args)

    def test_m_of_n_boundary_and_isolated_false_alarm_deletion(self) -> None:
        detections, _ = canonical_scene()
        baseline = run_manager(detections)
        target = next(track for track in baseline["tracks"] if track["truth_hits"].get(1, 0))
        self.assertEqual(target["confirmation"], 7)
        self.assertEqual(baseline["score"][target["id"] - 1][3:7], [1, 2, 2, 3])
        self.assertEqual(baseline["false_track_count"], 8)
        self.assertEqual(baseline["false_confirmed"], 0)
        self.assertEqual(baseline["false_deleted"], 8)
        self.assertTrue(all(track["deletion"] for track in baseline["tracks"] if not track["truth_hits"].get(1, 0)))

    def test_coast_boundary_reacquisition_stale_deletion_and_no_deconfirmation(self) -> None:
        detections, _ = canonical_scene()
        baseline = run_manager(detections)
        target = next(track for track in baseline["tracks"] if track["truth_hits"].get(1, 0))
        index = target["id"] - 1
        self.assertEqual(target["deletion"], 27)
        self.assertEqual(baseline["lifecycle"][index][11:14], [3, 3, 2])
        self.assertEqual(baseline["misses"][index][11:14], [1, 2, 0])
        self.assertEqual(baseline["score"][index][11:14], [3, 2, 2])
        self.assertEqual(baseline["lifecycle"][index][24:27], [3, 3, 4])
        self.assertTrue(baseline["gap_survived"])

    def test_oracle_rejects_malformed_nonfinite_and_resource_inputs(self) -> None:
        detections, _ = canonical_scene()
        malformed = (
            None, [], [None], [[(1.0, 0)] * 3], [[(math.nan, 0)]],
            [[(1.0, 2)]], [[(1.0, True)]], [[("x", 0)]], [[(1.0,)]],
            detections + [[]],
        )
        for record in malformed:
            with self.subTest(record=str(record)[:80]), self.assertRaises(ValueError):
                run_manager(record)  # type: ignore[arg-type]
        for policy in (
            {"m": 0}, {"n": 0}, {"m": 5}, {"m": True},
            {"coast_limit": -1}, {"coast_limit": 31}, {"max_tracks": 0},
            {"max_tracks": 21},
        ):
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                run_manager(detections, **policy)
        with self.assertRaises(ValueError):
            run_manager(detections, max_tracks=2)

    def test_tracks_are_isolated_and_report_order_does_not_change_lifecycle(self) -> None:
        detections, _ = canonical_scene()
        reversed_order = [list(reversed(scan)) for scan in detections]
        left = run_manager(detections)
        right = run_manager(reversed_order)
        for field in (
            "lifecycle", "score", "misses", "active_counts", "tentative_counts",
            "confirmed_counts", "coasting_counts", "target_confirmation",
            "target_last_deletion", "false_confirmed", "false_deleted",
            "allocated", "final_active",
        ):
            self.assertEqual(left[field], right[field], field)
        for scan in range(30):
            assigned = [row[scan] for row in left["assignments"] if row[scan]]
            self.assertEqual(len(assigned), len(set(assigned)))

    def test_competing_tracks_cannot_reuse_one_report_to_advance_both_lifecycles(self) -> None:
        detections = [
            [(100.0, 1), (130.0, 0)],
            [(105.0, 1)],
            [],
            [],
        ]
        result = run_manager(detections, m=2, n=3, coast_limit=1)

        self.assertEqual([row[1] for row in result["assignments"][:2]], [1, 0])
        self.assertEqual([row[1] for row in result["score"][:2]], [2, 1])
        self.assertEqual([row[1] for row in result["misses"][:2]], [0, 1])
        self.assertEqual([row[1] for row in result["lifecycle"][:2]], [2, 1])
        self.assertEqual(result["confirmed_target_count"], 1)
        self.assertEqual(result["false_confirmed"], 0)
        self.assertEqual(result["lifecycle"][1][2], 4)
        self.assertEqual(result["lifecycle"][0][2:4], [3, 4])

    def test_false_origin_track_stays_false_if_it_later_steals_a_target_report(self) -> None:
        detections = [[(100.0, 0)], [(100.0, 1)], [], []]
        result = run_manager(detections, m=2, n=3, coast_limit=1)
        self.assertEqual(result["false_track_count"], 1)
        self.assertEqual(result["false_confirmed"], 1)
        self.assertEqual(result["confirmed_target_count"], 0)

    def test_deleted_id_is_terminal_and_later_report_starts_a_new_track(self) -> None:
        detections = [
            [(100.0, 1)],
            [(100.0, 1)],
            [],
            [(100.0, 1)],
            [(100.0, 1)],
        ]
        result = run_manager(detections, m=2, n=2, coast_limit=0)

        self.assertEqual(result["allocated"], 2)
        self.assertEqual(result["lifecycle"][0], [1, 2, 4, 0, 0])
        self.assertEqual(result["assignments"][0], [1, 1, 0, 0, 0])
        self.assertEqual(result["tracks"][0]["deletion"], 3)
        self.assertFalse(result["tracks"][0]["active"])
        self.assertEqual(result["lifecycle"][1], [0, 0, 0, 1, 2])
        self.assertEqual(result["tracks"][1]["birth"], 4)
        self.assertEqual(result["tracks"][1]["confirmation"], 5)

    def test_baseline_sweeps_broken_case_and_exact_recovery(self) -> None:
        detections, _ = canonical_scene()
        baseline = run_manager(detections)
        recovered = run_manager(copy.deepcopy(detections))
        self.assertEqual(recovered, baseline)
        self.assertEqual(baseline["allocated"], 9)
        self.assertEqual(baseline["target_confirmation"], 7)
        self.assertEqual(baseline["target_last_deletion"], 27)
        self.assertEqual(baseline["final_active"], 0)
        m_results = [run_manager(detections, m=value) for value in (1, 3, 4)]
        self.assertEqual([result["target_confirmation"] for result in m_results], [4, 7, 11])
        self.assertEqual([result["false_confirmed"] for result in m_results], [8, 0, 0])
        coast_results = [run_manager(detections, coast_limit=value) for value in (0, 2, 5)]
        self.assertEqual([result["gap_survived"] for result in coast_results], [False, True, True])
        self.assertEqual([result["confirmed_target_count"] for result in coast_results], [2, 1, 1])
        self.assertEqual([result["target_last_deletion"] for result in coast_results], [25, 27, 30])
        broken = run_manager(detections, m=1, n=1, coast_limit=30)
        self.assertEqual(broken["false_confirmed"], 8)
        self.assertEqual(broken["final_active"], 9)

    def test_source_is_explicit_seeded_bounded_and_mutation_sensitive(self) -> None:
        self.assertEqual(source_binding_errors(self.source), [])
        mutations = (
            self.source.replace("hit_score >= confirmation_m", "hit_score > confirmation_m", 1),
            self.source.replace("hit_score < confirmation_m", "hit_score <= confirmation_m", 1),
            self.source.replace(
                "consecutive_misses(track_id) > maximum_consecutive_coasts",
                "consecutive_misses(track_id) >= maximum_consecutive_coasts", 1,
            ),
            self.source.replace("consecutive_misses(track_id) = 0;", "", 1),
            self.source.replace("hit_history(track_id, confirmation_n) = has_hit;", "", 1),
            self.source.replace("hit_history(track_id, confirmation_n) = true;", "hit_history(track_id, confirmation_n) = false;", 1),
            self.source.replace("hit_history(track_id, 2:confirmation_n);", "hit_history(track_id, 1:confirmation_n-1);", 1),
            self.source.replace("lifecycle_history(track_id, scan) = 4;", "", 1),
            self.source.replace("confirmed(track_id) = confirmation_m <= 1;", "confirmed(track_id) = false;", 1),
            self.source.replace("age_scans(track_id) = 1;", "age_scans(track_id) = 0;", 1),
            self.source.replace(
                "confirmed(track_id) = true;",
                "confirmed(track_id) = true; confirmed(track_id) = false;", 1,
            ),
            self.source.replace("pair_distance_m(:, detection_index) = Inf;", "", 1),
            self.source.replace("pair_distance_m(track_id, :) = Inf;", "", 1),
            self.source.replace("detection_used(detection_index) = true;", "detection_used(detection_index) = false;", 1),
            self.source.replace("find(detection_valid(:, scan) & ~detection_used)'", "find(detection_valid(:, scan))'", 1),
            self.source.replace(
                "if ~confirmed(track_id) && hit_score >= confirmation_m",
                "if hit_score >= confirmation_m", 1,
            ),
            self.source.replace(
                "if ~confirmed(track_id) && age_scans(track_id) >= confirmation_n",
                "if age_scans(track_id) >= confirmation_n", 1,
            ),
            self.source.replace("if abs(residual_m) <= association_gate_m", "if abs(residual_m) >= association_gate_m", 1),
            self.source.replace("age_scans(track_id) = age_scans(track_id) + 1;", "age_scans(track_id) = age_scans(track_id) + 2;", 1),
            self.source.replace("scan_interval_s*velocity_mps(active_at_scan_start);", "velocity_mps(active_at_scan_start);", 1),
            self.source.replace("position_m(track_id) = predicted_position_m(track_id);", "position_m(track_id) = position_m(track_id);", 1),
            self.source.replace(
                "(velocity_gain/scan_interval_s)*residual_m;",
                "velocity_gain*scan_interval_s*residual_m;", 1,
            ),
            self.source.replace("radius = sqrt(-2*log(uniform_1));", "radius = sqrt(-log(uniform_1));", 1),
            self.source.replace("active(track_id) = false;", "active(track_id) = true;", 1),
            self.source.replace("deletion_scan(track_id) = scan;", "deletion_scan(track_id) = 0;", 1),
            self.source.replace("lifecycle_history(track_id, scan) = 3;", "lifecycle_history(track_id, scan) = 2;", 1),
            self.source.replace("state = mod(multiplier*state, modulus);", "state = seed;", 1),
            self.source.replace(
                "~isnumeric(detection_position_m) || ~isreal(detection_position_m)",
                "false", 1,
            ),
            self.source.replace("confirmation_n > 30", "false", 1),
            self.source.replace("maximum_consecutive_coasts > 30", "false", 1),
            self.source.replace(
                "false_track = allocated & birth_truth_id == 0;",
                "false_track = allocated & true_hit_count == 0;", 1,
            ),
            self.source.replace("active_at_scan_start = find(active);", "active_at_scan_start = find(true(size(active)));", 1),
            self.source.replace("allocated_track_count = allocated_track_count + 1;", "allocated_track_count = max(1, allocated_track_count);", 1),
            self.source.replace("1, 1, number_scans", "3, 4, 2", 1),
            self.source.replace(
                "recovery_exact = lifecycle_results_equal(recovered, baseline);",
                "recovery_exact = true;", 1,
            ),
            self.source.replace("reviewed_pair_slots > maximum_pair_evaluations", "false", 1),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation[:80]):
                self.assertTrue(source_binding_errors(mutation))
        bound = self.source.index("reviewed_pair_slots > maximum_pair_evaluations")
        self.assertLess(bound, self.source.index("false_alarm_uniform ="))
        self.assertLess(bound, self.source.index("detection_position_m = nan"))

    def test_figures_metrics_units_state_legend_and_sweep_markers_are_visible(self) -> None:
        self.assertEqual(self.source.count("figure('Name', 'P58 Figure"), 6)
        self.assertEqual(self.source.count("'Tag', 'P58'"), 7)
        for marker in (
            "Scan index", "Cartesian position (m)", "Active track count",
            "Track lifecycle state", "Hit score (detections in N scans)",
            "Allowed consecutive coasts L (scans)", "Confirmed false-track count",
            "Final target deletion scan", "Confirmed target-track segments (tracks)",
            "baseline_target_confirmation_scan", "baseline_target_deletion_scan",
            "baseline_false_confirmed_count", "baseline_peak_active_tracks",
            "reviewed_pair_slots", "broken_final_active_tracks", "recovery_exact",
        ):
            self.assertIn(marker, self.source)

    def test_docs_cover_dependencies_model_limits_failure_recovery_and_claims(self) -> None:
        combined = "\n".join((self.readme, self.lesson, self.walkthrough, self.checks))
        for marker in (
            QUESTION, "P54", "P55", "P57", "P59", "M-of-N", "h_i(k)",
            "s_i(k)", "c_i(k)", "tentative", "confirmed", "coasting", "deleted",
            "M=1", "M=N", "L=0", "r <= L", "Limiting cases",
            "confirmation sweep", "coast sweep", "Broken case", "Recovery",
            "Correct:", "Incorrect:", "Ctrl+C", "10-second", "rollback",
            "base MATLAB", "R2016b", "MATLAB execution", "hardware/HIL",
            "field", "real-time", "truth labels",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(combined.count("**Correct:**"), 27)
        self.assertGreaterEqual(combined.count("**Incorrect:**"), 27)

    def test_no_placeholder_black_box_or_side_effect_regression(self) -> None:
        combined = "\n".join((self.source, self.readme, self.lesson, self.walkthrough, self.checks))
        self.assertNotIn("TODO", combined)
        self.assertNotIn("Status:** Scaffolded", combined)
        forbidden = (
            r"\brng\s*\(", r"(?<![A-Za-z])rand\s*\(", r"\brandn\s*\(",
            r"\binv\s*\(", r"trackerGNN", r"trackerJPDA", r"radarTracker",
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
            manifest = json.loads((fixture_root / "curriculum/modules.json").read_text())
            for module in manifest["modules"]:
                destination = fixture_root / module["folder"] / "README.md"
                destination.parent.mkdir(parents=True)
                shutil.copy2(ROOT / module["folder"] / "README.md", destination)
            environment = os.environ.copy()
            environment["HOME"] = temporary_directory
            started = subprocess.run(
                [str(fixture_root / "bin/learn"), "start", "58"], cwd=fixture_root,
                env=environment, text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P58", started.stdout)
            self.assertIn("Tutor entry", started.stdout)
            original = copy.deepcopy(manifest)
            p58 = next(entry for entry in manifest["modules"] if entry["id"] == "P58")
            p58["status"] = "scaffolded"
            changes = [
                (left["id"], key)
                for left, right in zip(original["modules"], manifest["modules"])
                for key in left if left.get(key) != right.get(key)
            ]
            self.assertEqual(changes, [("P58", "status")])
            for module_id in ("P57", "P59"):
                left = next(entry for entry in original["modules"] if entry["id"] == module_id)
                right = next(entry for entry in manifest["modules"] if entry["id"] == module_id)
                self.assertEqual(left, right)
            manifest_path = fixture_root / "curriculum/modules.json"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            rolled_back = subprocess.run(
                [str(fixture_root / "bin/learn"), "start", "58"], cwd=fixture_root,
                env=environment, text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(rolled_back.returncode, 3)
            self.assertIn("awaits Portfolio batch P58", rolled_back.stdout)
            manifest_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
            recovered = subprocess.run(
                [str(fixture_root / "bin/learn"), "start", "58"], cwd=fixture_root,
                env=environment, text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertIn("Tutor entry", recovered.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_default_tutor_entry_advances_from_completed_p57_without_state_loss(self) -> None:
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory) / "repo"
            (fixture_root / "bin").mkdir(parents=True)
            (fixture_root / "curriculum").mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture_root / "bin/learn")
            shutil.copy2(ROOT / "curriculum/modules.json", fixture_root / "curriculum/modules.json")
            for module in self.manifest["modules"]:
                destination = fixture_root / module["folder"] / "README.md"
                destination.parent.mkdir(parents=True)
                shutil.copy2(ROOT / module["folder"] / "README.md", destination)
            progress = fixture_root / ".learning/progress.json"
            progress.parent.mkdir(parents=True)
            initial = {
                "schema_version": 1, "current": "P57",
                "completed": [f"P{number:02d}" for number in range(1, 58)],
                "notes": {"P57": "Preserve this association teach-back note."},
            }
            progress.write_text(json.dumps(initial, indent=2) + "\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["HOME"] = temporary_directory
            started = subprocess.run(
                [str(fixture_root / "bin/learn"), "start"], cwd=fixture_root,
                env=environment, text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P58 — Implement Track Initiation, Confirmation, Coasting, and Deletion", started.stdout)
            advanced = json.loads(progress.read_text(encoding="utf-8"))
            self.assertEqual(advanced["current"], "P58")
            self.assertEqual(advanced["completed"], initial["completed"])
            self.assertEqual(advanced["notes"], initial["notes"])
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_public_catalogs_describe_p58_without_freezing_future_state(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 58 follows P57 by", root_readme)
        self.assertIn("Project 58 follows P57 by", start_here)
        self.assertRegex(module_index, r"\| \[P58\].*\| implemented \|")

    def test_retained_evidence_has_commands_claim_boundary_and_single_newline(self) -> None:
        evidence_files = sorted((ROOT / "docs/evidence").glob("P58-*.md"))
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
            "python3 -m unittest tests.test_p58_module -v",
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
