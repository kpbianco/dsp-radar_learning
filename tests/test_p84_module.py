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
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/84-run-the-end-to-end-radar-processing-capstone"
MANIFEST = ROOT / "curriculum/modules.json"
CLI = ROOT / "bin/learn"
EVIDENCE = ROOT / "docs/evidence/P84-2026-08-14.md"
QUESTION = (
    "Can I trace a target from waveform generation through detection and "
    "tracking without treating any stage as a black box?"
)
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")

BASE_CONTROLS = {
    "seed": 8401,
    "c_mps": 3.0e8,
    "carrier_hz": 10.0e9,
    "sample_rate_hz": 4.0e6,
    "bandwidth_hz": 2.0e6,
    "pulse_width_s": 8.0e-6,
    "fast_time_samples": 128,
    "pulses": 32,
    "prf_hz": 31_250.0,
    "scan_interval_s": 1.0,
    "scans": 8,
    "target_initial_range_m": [900.0, 1650.0, 2550.0, 2625.0],
    "target_approach_speed_mps": [0.0, 30.0, -15.0, -15.0],
    "target_voltage": [1.8, 2.2, 3.0, 0.22],
    "clutter_edge_range_m": 1800.0,
    "quiet_clutter_voltage": 0.015,
    "high_clutter_voltage": 0.20,
    "noise_voltage": 0.18,
    "receiver_image_coefficient": 0.12,
    "receiver_dc_real": 0.04,
    "receiver_dc_imag": 0.03,
    "spur_range_m": 3900.0,
    "spur_doppler_bin": 5,
    "spur_voltage": 0.85,
    "cfar_pfa": 1.0e-3,
    "training_range": 4,
    "guard_range": 2,
    "training_doppler": 3,
    "guard_doppler": 1,
    "minimum_cluster_cells": 1,
    "tracker_alpha": 0.65,
    "tracker_beta": 0.18,
    "tracker_range_gate_m": 225.0,
    "tracker_velocity_gate_mps": 35.0,
    "maximum_coast_scans": 2,
    "taper_sweep": [0.0, 0.5, 1.0],
    "pfa_sweep": [1.0e-4, 1.0e-3, 1.0e-2],
    "display_floor_db": -45.0,
    "max_fast_time_samples": 256,
    "max_pulses": 64,
    "max_scans": 12,
    "max_targets": 6,
    "max_sweep_cases": 4,
    "max_map_evaluations": 20,
    "max_cfar_training_visits": 12_000_000,
    "max_private_values": 20_000,
    "max_working_values": 500_000,
    "max_reports_per_scan": 50,
    "max_association_pairs": 10_000,
    "max_figures": 6,
}


def artifact_errors(folder: Path) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = folder / name
        if not path.is_file():
            errors.append(f"missing {name}")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            errors.append(f"empty {name}")
        if re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", text, re.IGNORECASE):
            errors.append(f"placeholder remains in {name}")
    return errors


def p84_identity_errors(data: object) -> list[str]:
    if not isinstance(data, dict) or not isinstance(data.get("modules"), list):
        return ["manifest shape"]
    entries = [entry for entry in data["modules"] if isinstance(entry, dict) and entry.get("id") == "P84"]
    if len(entries) != 1:
        return ["P84 cardinality"]
    entry = entries[0]
    expected = {
        "number": 84,
        "id": "P84",
        "title": "Run the End-to-End Radar Processing Capstone",
        "guiding_question": QUESTION,
        "phase": 9,
        "phase_title": "SAR, ISAR, Passive Radar, and Capstone",
        "slug": "run-the-end-to-end-radar-processing-capstone",
        "folder": "modules/84-run-the-end-to-end-radar-processing-capstone",
        "status": "implemented",
        "implementation_batch": "P84",
    }
    return [name for name, value in expected.items() if entry.get(name) != value]


def finite_real(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def controls_errors(c: object) -> list[str]:
    if not isinstance(c, dict) or set(c) != set(BASE_CONTROLS):
        return ["control fields"]
    errors: list[str] = []
    vector_names = {"target_initial_range_m", "target_approach_speed_mps", "target_voltage", "taper_sweep", "pfa_sweep"}
    integer_names = {
        "seed", "fast_time_samples", "pulses", "scans", "spur_doppler_bin",
        "training_range", "guard_range", "training_doppler", "guard_doppler",
        "minimum_cluster_cells", "maximum_coast_scans", "max_fast_time_samples",
        "max_pulses", "max_scans", "max_targets", "max_sweep_cases",
        "max_map_evaluations", "max_cfar_training_visits", "max_private_values",
        "max_working_values", "max_reports_per_scan", "max_association_pairs",
        "max_figures",
    }
    for name, value in c.items():
        values = value if name in vector_names and isinstance(value, list) else [value]
        if name in vector_names and (not isinstance(value, list) or not value):
            errors.append(f"{name} vector")
            continue
        if any(not finite_real(item) for item in values):
            errors.append(f"{name} finite real")
        if name in integer_names and any(finite_real(item) and item != math.floor(item) for item in values):
            errors.append(f"{name} integer")
    if errors:
        return errors

    if not 0 < c["seed"] < 2_147_483_647:
        errors.append("seed")
    if not (
        c["c_mps"] > 0
        and c["carrier_hz"] > 0
        and c["sample_rate_hz"] > 0
        and 0 < c["bandwidth_hz"] < c["sample_rate_hz"]
        and c["pulse_width_s"] > 0
        and c["pulse_width_s"] * c["sample_rate_hz"] == round(c["pulse_width_s"] * c["sample_rate_hz"])
        and c["pulse_width_s"] * c["sample_rate_hz"] >= 2
        and c["prf_hz"] == c["sample_rate_hz"] / c["fast_time_samples"]
    ):
        errors.append("sampling")
    if not (
        1 <= c["fast_time_samples"] <= c["max_fast_time_samples"]
        and 2 <= c["pulses"] <= c["max_pulses"]
        and c["pulses"] % 2 == 0
        and 4 <= c["scans"] <= c["max_scans"]
    ):
        errors.append("cube shape")
    target_lengths = {len(c[name]) for name in ("target_initial_range_m", "target_approach_speed_mps", "target_voltage")}
    wavelength = c["c_mps"] / c["carrier_hz"] if c["carrier_hz"] > 0 else math.inf
    unambiguous_range = c["c_mps"] / (2 * c["prf_hz"]) if c["prf_hz"] > 0 else 0
    unambiguous_speed = wavelength * c["prf_hz"] / 4 if math.isfinite(wavelength) else 0
    last_ranges = [
        initial - speed * (c["scans"] - 1) * c["scan_interval_s"]
        for initial, speed in zip(c["target_initial_range_m"], c["target_approach_speed_mps"])
    ]
    range_spacing = c["c_mps"] / (2 * c["sample_rate_hz"])
    target_bins = [math.floor(value / range_spacing + 0.5) + 1 for value in c["target_initial_range_m"] + last_ranges]
    doppler_bins = [
        math.floor(2 * value / wavelength / c["prf_hz"] * c["pulses"] + 0.5)
        if value >= 0
        else math.ceil(2 * value / wavelength / c["prf_hz"] * c["pulses"] - 0.5)
        for value in c["target_approach_speed_mps"]
    ]
    if not (
        len(target_lengths) == 1
        and 4 <= len(c["target_initial_range_m"]) <= c["max_targets"]
        and all(right > left for left, right in zip(c["target_initial_range_m"], c["target_initial_range_m"][1:]))
        and all(0 < value < unambiguous_range for value in c["target_initial_range_m"] + last_ranges)
        and all(abs(value) < unambiguous_speed for value in c["target_approach_speed_mps"])
        and all(1 <= value <= c["fast_time_samples"] for value in target_bins)
        and all(-c["pulses"] // 2 <= value <= c["pulses"] // 2 - 1 for value in doppler_bins)
        and all(value > 0 for value in c["target_voltage"])
    ):
        errors.append("targets")
    if not (
        0 < c["clutter_edge_range_m"] < unambiguous_range
        and c["high_clutter_voltage"] > c["quiet_clutter_voltage"] >= 0
        and any(
            index * range_spacing > 300
            and index * range_spacing < c["clutter_edge_range_m"] - 300
            for index in range(c["fast_time_samples"])
        )
        and c["noise_voltage"] > 0
        and abs(c["receiver_image_coefficient"]) < 0.5
        and c["clutter_edge_range_m"] < c["spur_range_m"] < unambiguous_range
        and math.floor(c["spur_range_m"] / range_spacing + 0.5) + 1 <= c["fast_time_samples"]
        and abs(c["spur_doppler_bin"]) < c["pulses"] / 2
        and c["spur_voltage"] > 0
    ):
        errors.append("scene")
    if not (
        1e-6 <= c["cfar_pfa"] <= 0.1
        and all(1e-6 <= value <= 0.1 for value in c["pfa_sweep"])
        and all(right > left for left, right in zip(c["pfa_sweep"], c["pfa_sweep"][1:]))
        and all(0 <= value <= 1 for value in c["taper_sweep"])
        and all(right > left for left, right in zip(c["taper_sweep"], c["taper_sweep"][1:]))
        and 3 <= len(c["pfa_sweep"]) <= c["max_sweep_cases"]
        and 3 <= len(c["taper_sweep"]) <= c["max_sweep_cases"]
    ):
        errors.append("sweeps")
    range_outer = c["training_range"] + c["guard_range"]
    doppler_outer = c["training_doppler"] + c["guard_doppler"]
    if not (2 * range_outer + 1 < c["fast_time_samples"] and 2 * doppler_outer + 1 < c["pulses"]):
        errors.append("stencil")
    if not (
        0 < c["tracker_alpha"] <= 1
        and 0 < c["tracker_beta"] <= 1
        and c["tracker_range_gate_m"] > 0
        and c["tracker_velocity_gate_mps"] > 0
        and 1 <= c["maximum_coast_scans"] < c["scans"]
    ):
        errors.append("tracker")
    immutable = {
        "max_fast_time_samples": 256, "max_pulses": 64, "max_scans": 12,
        "max_targets": 6, "max_sweep_cases": 4, "max_map_evaluations": 20,
        "max_cfar_training_visits": 12_000_000, "max_private_values": 20_000,
        "max_working_values": 500_000, "max_association_pairs": 10_000,
        "max_reports_per_scan": 50, "max_figures": 6,
    }
    if any(c[name] != value for name, value in immutable.items()):
        errors.append("immutable ceilings")
    training_cells = (2 * range_outer + 1) * (2 * doppler_outer + 1) - (2 * c["guard_range"] + 1) * (2 * c["guard_doppler"] + 1)
    maps = c["scans"] + len(c["taper_sweep"]) + len(c["pfa_sweep"]) + 3
    testable = (c["fast_time_samples"] - 2 * range_outer) * (c["pulses"] - 2 * doppler_outer)
    visits = maps * testable * training_cells
    private_values = 2 * c["fast_time_samples"] * c["pulses"]
    working_values = 45 * c["fast_time_samples"] * c["pulses"] + 10_000
    pairs = c["scans"] * c["max_reports_per_scan"]
    if not (
        maps <= c["max_map_evaluations"]
        and visits <= c["max_cfar_training_visits"]
        and private_values <= c["max_private_values"]
        and working_values <= c["max_working_values"]
        and pairs <= c["max_association_pairs"]
    ):
        errors.append("resource plan")
    return errors


def private_complex_noise(seed: int, rows: int, columns: int, maximum: int = 20_000) -> list[complex]:
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 < seed < 2_147_483_647:
        raise ValueError("seed")
    if (
        isinstance(rows, bool)
        or isinstance(columns, bool)
        or not isinstance(rows, int)
        or not isinstance(columns, int)
        or rows < 1
        or columns < 1
        or 2 * rows * columns > maximum
    ):
        raise ValueError("shape")
    count = rows * columns
    state = seed
    uniforms: list[float] = []
    for _ in range(2 * count):
        state = (16_807 * state) % 2_147_483_647
        uniforms.append(state / 2_147_483_647)
    return [
        math.sqrt(-2 * math.log(max(uniforms[index], float.fromhex("0x0.0000000000001p-1022"))))
        * cmath.exp(2j * math.pi * uniforms[count + index])
        / math.sqrt(2)
        for index in range(count)
    ]


def convolve(left: list[complex], right: list[complex]) -> list[complex]:
    output = [0j] * (len(left) + len(right) - 1)
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            output[left_index + right_index] += left_value * right_value
    return output


def cfar_thresholds(power: list[list[float]], pfa: float, training: int = 2, guard: int = 1) -> tuple[list[list[float | None]], list[list[bool]]]:
    rows, columns = len(power), len(power[0])
    threshold: list[list[float | None]] = [[None for _ in range(columns)] for _ in range(rows)]
    detection = [[False for _ in range(columns)] for _ in range(rows)]
    offsets = [
        (row, column)
        for row in range(-training - guard, training + guard + 1)
        for column in range(-training - guard, training + guard + 1)
        if not (abs(row) <= guard and abs(column) <= guard)
    ]
    alpha = len(offsets) * (pfa ** (-1 / len(offsets)) - 1)
    outer = training + guard
    for row in range(outer, rows - outer):
        for column in range(outer, columns - outer):
            mean = sum(power[row + dr][column + dc] for dr, dc in offsets) / len(offsets)
            threshold[row][column] = alpha * mean
            detection[row][column] = power[row][column] > threshold[row][column]
    return threshold, detection


def component_count(mask: list[list[bool]]) -> int:
    rows, columns = len(mask), len(mask[0])
    visited: set[tuple[int, int]] = set()
    count = 0
    for row in range(rows):
        for column in range(columns):
            if not mask[row][column] or (row, column) in visited:
                continue
            count += 1
            queue = deque([(row, column)])
            visited.add((row, column))
            while queue:
                current_row, current_column = queue.popleft()
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        neighbor = current_row + dr, current_column + dc
                        if (
                            0 <= neighbor[0] < rows
                            and 0 <= neighbor[1] < columns
                            and mask[neighbor[0]][neighbor[1]]
                            and neighbor not in visited
                        ):
                            visited.add(neighbor)
                            queue.append(neighbor)
    return count


def maximum_one_to_one_match_count(candidates: list[set[int]], truth_count: int) -> int:
    reachable_masks = {0}
    for report_candidates in candidates:
        prior_masks = set(reachable_masks)
        for mask in prior_masks:
            for truth_index in report_candidates:
                if not 0 <= truth_index < truth_count:
                    raise ValueError("truth index")
                truth_bit = 1 << truth_index
                if not mask & truth_bit:
                    reachable_masks.add(mask | truth_bit)
    return max((mask.bit_count() for mask in reachable_masks), default=0)


class P84ModuleTests(unittest.TestCase):
    def test_manifest_identity_artifacts_and_permanent_dependency(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(p84_identity_errors(data), [])
        p83 = next(entry for entry in data["modules"] if entry["id"] == "P83")
        self.assertEqual(p83["status"], "implemented")
        self.assertEqual(artifact_errors(MODULE), [])
        for name in ARTIFACTS:
            self.assertIn(QUESTION, (MODULE / name).read_text(encoding="utf-8"))

    def test_artifact_and_manifest_negative_cases_and_additive_compatibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for name in ARTIFACTS:
                (folder / name).write_text("complete\n", encoding="utf-8")
            self.assertEqual(artifact_errors(folder), [])
            for name, content in (("experiment.m", ""), ("lesson.md", "TODO\n"), ("checks.md", "   \n")):
                original = (folder / name).read_text(encoding="utf-8")
                (folder / name).write_text(content, encoding="utf-8")
                self.assertTrue(artifact_errors(folder))
                (folder / name).write_text(original, encoding="utf-8")
            (folder / "walkthrough.md").unlink()
            self.assertIn("missing walkthrough.md", artifact_errors(folder))

        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        compatible = copy.deepcopy(data)
        compatible["future_metadata"] = {"accepted": True}
        next(entry for entry in compatible["modules"] if entry["id"] == "P84")["future_field"] = 1
        self.assertEqual(p84_identity_errors(compatible), [])
        for mutation in ("status", "folder", "guiding_question"):
            malformed = copy.deepcopy(data)
            next(entry for entry in malformed["modules"] if entry["id"] == "P84")[mutation] = "wrong"
            self.assertIn(mutation, p84_identity_errors(malformed))
        duplicate = copy.deepcopy(data)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][-1]))
        self.assertEqual(p84_identity_errors(duplicate), ["P84 cardinality"])
        self.assertEqual(p84_identity_errors([]), ["manifest shape"])

    def test_source_binds_transparent_stages_sweeps_recovery_and_bounds(self):
        source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        normalized = " ".join(source.split())
        required = (
            "make_lfm", "synthesize_scan", "correct_receiver", "conj(fliplr(replica))",
            "fftshift(fft", "ca_cfar_2d", "training_count*(requested_pfa^(-1/training_count)-1)",
            "cluster_detections", "alpha_beta_track", "provenance", "score_reports",
            "maximum_truth_report_matching", "reachable_masks", "bitand", "bitor",
            "pulse_samples >= 2", "mod(c.pulses,2) == 0", "c.scans >= 4",
            "all_target_bins", "doppler_bins", "quiet_calibration_rows",
            "taper_sweep", "pfa_sweep", "wrong_replica", "recovery_exact",
            "retained_corrected_cube", "baseline_runtime_s", "track_rmse_m",
            "empirical_false_cell_rate", "max_cfar_training_visits",
            "max_working_values", "max_reports_per_scan", "max_association_pairs",
            "max_figures",
        )
        for marker in required:
            self.assertIn(marker, normalized)
        self.assertLess(normalized.index("resource_plan = validate_controls(controls)"), normalized.index("make_lfm(controls.bandwidth_hz"))
        self.assertIn("visibility(2) = 0", normalized)
        self.assertIn("sum(fixed_detection(edge_region)) > sum(baseline.detection(edge_region))", normalized)
        self.assertIn("numel(reports) <= c.max_reports_per_scan", normalized)
        self.assertIn("isequal(recovered.matched, baseline.matched)", normalized)

    def test_source_rejects_black_boxes_global_rng_and_persistent_side_effects(self):
        source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        forbidden = (
            r"\bphased\.", r"\bcfardetector", r"\btracker\w*\s*\(",
            r"\bassignDetectionsToTracks\b", r"\bmatchpairs\b", r"\bobjectDetection\b",
            r"\b(?:rand|randn|rng)\s*\(", r"\b(?:inv|pinv)\s*\(", r"\bparfor\b",
            r"\bgpuArray\b", r"\bbatch\s*\(", r"\btimer\s*\(", r"\bfopen\s*\(",
            r"\bsave\s*\(", r"\bwritematrix\s*\(", r"\bwebread\s*\(",
            r"\bsystem\s*\(", r"\bunix\s*\(", r"(?m)^\s*!", r"\bclose\s+all\b",
            r"\bclearvars\b", r"\bpersistent\b",
        )
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, source, re.IGNORECASE), pattern)
        self.assertIn("findall(0, 'Type', 'figure', 'Tag', 'P84')", source)
        self.assertIn("private_complex_noise", source)

    def test_controls_accept_baseline_and_reject_malformed_or_unbounded_inputs(self):
        self.assertEqual(controls_errors(BASE_CONTROLS), [])
        malformed = (
            ("seed", True), ("seed", 0), ("sample_rate_hz", math.nan),
            ("bandwidth_hz", 4.0e6), ("pulse_width_s", 8.1e-6),
            ("pulse_width_s", 0.25e-6),
            ("fast_time_samples", 128.5), ("fast_time_samples", 512),
            ("pulses", 8), ("pulses", 31), ("scans", 3), ("scans", 20),
            ("carrier_hz", -1), ("clutter_edge_range_m", 500),
            ("receiver_image_coefficient", 1.0), ("spur_range_m", 4790),
            ("spur_range_m", 6000),
            ("tracker_alpha", 0), ("tracker_range_gate_m", -1),
            ("maximum_coast_scans", 8), ("cfar_pfa", 0),
            ("training_range", 70), ("display_floor_db", math.inf),
            ("max_figures", 7), ("max_reports_per_scan", 0),
            ("max_working_values", 100),
        )
        for name, value in malformed:
            with self.subTest(name=name, value=value):
                case = copy.deepcopy(BASE_CONTROLS)
                case[name] = value
                self.assertTrue(controls_errors(case))
        for name, value in (
            ("target_initial_range_m", []),
            ("target_voltage", [1.0]),
            ("target_approach_speed_mps", [0, 30, 900, -15]),
            ("target_approach_speed_mps", [0, 230, -15, -15]),
            ("pfa_sweep", [1e-3, 1e-4, 1e-2]),
            ("taper_sweep", [0, 0.5, 0.5]),
        ):
            case = copy.deepcopy(BASE_CONTROLS)
            case[name] = value
            self.assertTrue(controls_errors(case), name)

    def test_private_generator_is_exact_bounded_repeatable_and_isolated(self):
        first = private_complex_noise(8401, 2, 2)
        second = private_complex_noise(8401, 2, 2)
        different = private_complex_noise(8402, 2, 2)
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertAlmostEqual(first[0].real, 0.284280056145, places=10)
        self.assertAlmostEqual(first[0].imag, -1.625143278585, places=10)
        for args in ((0, 1, 1), (8401, 0, 1), (8401, True, 1), (8401, 101, 100)):
            with self.assertRaises(ValueError):
                private_complex_noise(*args)

    def test_independent_matched_filter_cfar_clustering_and_coast_facts(self):
        samples = 32
        bandwidth = 2.0e6
        pulse_width = 8.0e-6
        sample_rate = 4.0e6
        time = [(index - (samples - 1) / 2) / sample_rate for index in range(samples)]
        pulse = [cmath.exp(1j * math.pi * bandwidth / pulse_width * value * value) / math.sqrt(samples) for value in time]
        echo = [0j] * 96
        delay = 21
        for index, value in enumerate(pulse):
            echo[delay + index] += value
        correct = convolve(echo, [value.conjugate() for value in reversed(pulse)])
        broken = convolve(echo, list(reversed(pulse)))
        correct_peak = max(abs(value) for value in correct)
        broken_peak = max(abs(value) for value in broken)
        self.assertAlmostEqual(correct_peak, 1.0, places=12)
        self.assertLess(broken_peak, correct_peak)
        self.assertEqual(correct.index(max(correct, key=abs)) - (samples - 1), delay)

        power = [[1.0 for _ in range(20)] for _ in range(24)]
        for row in range(12, 24):
            for column in range(20):
                power[row][column] = 16.0
        power[8][10] = 100.0
        _, strict = cfar_thresholds(power, 1e-4)
        _, relaxed = cfar_thresholds(power, 1e-2)
        self.assertTrue(strict[8][10])
        self.assertTrue(all(not strict[row][column] or relaxed[row][column] for row in range(24) for column in range(20)))
        quiet_fixed = -math.log(1e-3)
        fixed_count = sum(value > quiet_fixed for row in power for value in row)
        local_count = sum(value for row in relaxed for value in row)
        self.assertGreater(fixed_count, local_count)

        mask = [[False] * 8 for _ in range(8)]
        mask[3][3] = mask[3][4] = mask[4][4] = True
        mask[6][1] = True
        self.assertEqual(component_count(mask), 2)
        self.assertLessEqual(1, 2)  # one merged component can satisfy at most one of two nearby truths

        alpha, beta, interval = 0.65, 0.18, 1.0
        ranges = [1650.0]
        rates = [-30.0]
        updated = [True]
        measurements = [1650.0, 1620.0, 1590.0, None, 1530.0]
        for measurement in measurements[1:]:
            predicted = ranges[-1] + rates[-1] * interval
            if measurement is None:
                ranges.append(predicted)
                rates.append(rates[-1])
                updated.append(False)
            else:
                innovation = measurement - predicted
                ranges.append(predicted + alpha * innovation)
                rates.append(rates[-1] + beta * innovation / interval)
                updated.append(True)
        self.assertFalse(updated[3])
        self.assertAlmostEqual(ranges[3], ranges[2] + rates[2], places=12)
        self.assertTrue(updated[4])

    def test_scoring_maximizes_one_to_one_matches_without_truth_order_bias(self):
        # Report 0 can gate to either truth and is closer to truth 0. Report 1
        # can gate only to truth 0. A truth-ordered nearest greedy scorer takes
        # report 0 first and incorrectly returns one match; the feasible
        # assignment report 1 -> truth 0, report 0 -> truth 1 returns two.
        candidates = [{0, 1}, {0}]
        self.assertEqual(maximum_one_to_one_match_count(candidates, 2), 2)
        self.assertEqual(maximum_one_to_one_match_count(list(reversed(candidates)), 2), 2)
        self.assertEqual(maximum_one_to_one_match_count([{1, 0}, {1}], 2), 2)
        self.assertEqual(maximum_one_to_one_match_count([set()], 2), 0)
        with self.assertRaises(ValueError):
            maximum_one_to_one_match_count([{2}], 2)

    def run_cli(self, manifest: dict, *args: str, initial_state: dict | None = None) -> tuple[subprocess.CompletedProcess[str], dict]:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir(parents=True)
            shutil.copy2(CLI, fixture / "bin/learn")
            (fixture / "curriculum/modules.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for module in manifest["modules"]:
                destination = fixture / module["folder"] / "README.md"
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / module["folder"] / "README.md", destination)
            if initial_state is not None:
                state_path = fixture / ".learning/progress.json"
                state_path.parent.mkdir(parents=True)
                state_path.write_text(json.dumps(initial_state, indent=2) + "\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["HOME"] = temporary
            process = subprocess.run(
                [str(fixture / "bin/learn"), *args],
                cwd=fixture,
                text=True,
                capture_output=True,
                timeout=3,
                env=environment,
            )
            state_path = fixture / ".learning/progress.json"
            state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
            return process, state

    def test_cli_timeout_rollback_recovery_isolation_and_additive_compatibility(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None

        explicit, explicit_state = self.run_cli(manifest, "start", "84")
        self.assertEqual(explicit.returncode, 0, explicit.stderr)
        self.assertIn("P84", explicit.stdout)
        self.assertIn("Tutor entry", explicit.stdout)
        self.assertEqual(explicit_state["current"], "P84")

        completed_through_p83 = [f"P{number:02d}" for number in range(1, 84)]
        initial = {
            "schema_version": 1,
            "current": "P83",
            "completed": completed_through_p83,
            "notes": {"P83": "retained prerequisite note"},
        }
        default, default_state = self.run_cli(manifest, "start", initial_state=initial)
        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertIn("P84", default.stdout)
        self.assertEqual(default_state["completed"], completed_through_p83)
        self.assertEqual(default_state["notes"]["P83"], "retained prerequisite note")

        rollback = copy.deepcopy(manifest)
        next(entry for entry in rollback["modules"] if entry["id"] == "P84")["status"] = "scaffolded"
        blocked, _ = self.run_cli(rollback, "start", "84")
        self.assertEqual(blocked.returncode, 3)
        self.assertIn("awaits Portfolio batch P84", blocked.stdout)
        fallback, _ = self.run_cli(rollback, "start", initial_state=initial)
        self.assertEqual(fallback.returncode, 0, fallback.stderr)
        self.assertIn("P83", fallback.stdout)

        compatible = copy.deepcopy(manifest)
        compatible["future_metadata"] = True
        next(entry for entry in compatible["modules"] if entry["id"] == "P84")["future_field"] = {"v": 2}
        recovered, _ = self.run_cli(compatible, "start", "84")
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_lesson_walkthrough_checks_catalogs_and_claim_boundaries(self):
        lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        combined = "\n".join((lesson, walkthrough, checks, readme)).lower()
        for marker in (
            "c/(2b)", "c/(2fs)", "conjugate time reverse", "linear power",
            "requested `pfa`", "empirical false-cell rate", "one-to-one",
            "alpha-beta", "coast", "receiver spur", "clutter edge",
            "strong/weak", "runtime", "same calibrated", "base matlab r2016b",
            "p32", "p42", "p50", "p53", "p54/p57/p58",
        ):
            self.assertIn(marker, combined)
        self.assertIn("Sweep 1", walkthrough)
        self.assertIn("Sweep 2", walkthrough)
        self.assertIn("Intentionally broken", walkthrough)
        self.assertIn("Common interpretation mistakes", walkthrough)
        self.assertIn("teach-back rubric", checks)
        self.assertGreaterEqual(len(re.findall(r"(?m)^\d+\. \*\*", checks)), 20)
        self.assertIn("| [P84]", (ROOT / "modules/README.md").read_text(encoding="utf-8"))
        self.assertIn("Project 84 closes the curriculum", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn("Project 84 follows P83", (ROOT / "START_HERE.md").read_text(encoding="utf-8"))

    def test_retained_evidence_has_acceptance_commands_limits_and_eof_policy(self):
        self.assertTrue(EVIDENCE.is_file())
        evidence = EVIDENCE.read_text(encoding="utf-8")
        for heading in (
            "## Claim boundary", "## Governance, current state, ownership, concurrency, and CI inspection",
            "## Acceptance map", "## Deterministic auxiliary results", "## Figure and metric inventory",
            "## Exact commands and results", "## Changed and preserved invariants",
            "## Residual risks", "## Rollback", "## Unperformed validation",
        ):
            self.assertIn(heading, evidence)
        for phrase in (
            "MATLAB", "not installed", "static", "simulated", "hardware/HIL",
            "field", "RT1/RT2", "Unreal", "signing", "deployment", "production",
            "DSP_RADAR_VERIFY_PROFILE=contract", "python3 -m unittest discover",
            "./scripts/agent-verify.sh", "P84-2026-08-14.md",
        ):
            self.assertIn(phrase, evidence)

        changed_text = [
            ROOT / "README.md", ROOT / "START_HERE.md", ROOT / "modules/README.md",
            MANIFEST, ROOT / "tests/test_p84_module.py", EVIDENCE,
            *(MODULE / name for name in ARTIFACTS),
        ]
        for path in changed_text:
            with self.subTest(path=path):
                raw = path.read_bytes()
                self.assertTrue(raw.endswith(b"\n"))
                self.assertFalse(raw.endswith(b"\n\n"))
                self.assertNotIn(b"\r", raw)

    @unittest.skipUnless(shutil.which("matlab"), "MATLAB runtime unavailable; execution is not claimed")
    def test_matlab_runtime_when_available(self):
        module_path = str(MODULE).replace("'", "''")
        command = (
            f"cd('{module_path}'); experiment; "
            "assert(p84_results.recovery_exact); "
            "assert(p84_results.retained_input_exact); "
            "assert(numel(findall(0,'Type','figure','Tag','P84')) == 6); "
            "close(findall(0,'Type','figure','Tag','P84'));"
        )
        process = subprocess.run(
            [shutil.which("matlab"), "-batch", command],
            cwd=MODULE,
            text=True,
            capture_output=True,
            timeout=300,
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)


if __name__ == "__main__":
    unittest.main()
