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
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/53-group-detection-cells-into-target-reports"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How do several threshold-crossing cells become one physical detection?"
EXPECTED_IDENTITY = {
    "number": 53,
    "id": "P53",
    "title": "Group Detection Cells into Target Reports",
    "guiding_question": QUESTION,
    "phase": 6,
    "phase_title": "Radar Tracking and Data Association",
    "slug": "group-detection-cells-into-target-reports",
    "folder": "modules/53-group-detection-cells-into-target-reports",
    "status": "implemented",
    "implementation_batch": "P53",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def validate_p53_contract(module: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P53 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P53 empty {artifact}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P53"]
    if len(entries) != 1:
        return errors + [f"expected one P53 manifest entry, found {len(entries)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if entries[0].get(key) != expected:
            errors.append(f"P53 {key} mismatch")
    return errors


def canonical_controls() -> dict[str, object]:
    return {
        "seed": 5301,
        "range_bins": 72,
        "velocity_bins": 65,
        "range_spacing": 15.0,
        "velocity_spacing": 0.5,
        "threshold": 1.0,
        "minimum_cells": 3,
        "weight_exponent": 1.0,
        "size_sweep": (1, 3, 18),
        "weight_sweep": (0.0, 1.0, 2.0),
        "max_scene_cells": 20_000,
        "max_queue_cells": 20_000,
        "max_sweep_cases": 5,
        "max_figures": 6,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    integer_names = (
        "seed", "range_bins", "velocity_bins", "minimum_cells",
        "max_scene_cells", "max_queue_cells", "max_sweep_cases", "max_figures",
    )
    if not all(integer(controls[name]) for name in integer_names):
        raise ValueError("integer controls")
    if not all(
        finite_real(controls[name])
        for name in ("range_spacing", "velocity_spacing", "threshold", "weight_exponent")
    ):
        raise ValueError("real controls")
    fixed = {
        "max_scene_cells": 20_000,
        "max_queue_cells": 20_000,
        "max_sweep_cases": 5,
        "max_figures": 6,
    }
    if any(controls[name] != value for name, value in fixed.items()):
        raise ValueError("resource ceiling drift")
    if controls["seed"] != 5301:
        raise ValueError("seed")
    if controls["range_bins"] != 72 or controls["velocity_bins"] != 65:
        raise ValueError("fixed scene dimensions")
    scene_cells = controls["range_bins"] * controls["velocity_bins"]
    if scene_cells > controls["max_scene_cells"] or scene_cells > controls["max_queue_cells"]:
        raise ValueError("scene budget")
    if controls["range_spacing"] != 15 or controls["velocity_spacing"] != 0.5:
        raise ValueError("fixed scene spacing")
    if controls["threshold"] != 1:
        raise ValueError("normalized threshold")
    if not 1 <= controls["minimum_cells"] <= scene_cells:
        raise ValueError("minimum cells")
    if not 0 <= controls["weight_exponent"] <= 2:
        raise ValueError("weight exponent")
    size_sweep = controls["size_sweep"]
    if not isinstance(size_sweep, (tuple, list)) or not 3 <= len(size_sweep) <= controls["max_sweep_cases"]:
        raise ValueError("size sweep shape")
    if not all(integer(value) and 1 <= value <= scene_cells for value in size_sweep):
        raise ValueError("size sweep values")
    if any(right <= left for left, right in zip(size_sweep, size_sweep[1:])):
        raise ValueError("size sweep order")
    if controls["minimum_cells"] not in size_sweep:
        raise ValueError("size sweep baseline")
    weight_sweep = controls["weight_sweep"]
    if not isinstance(weight_sweep, (tuple, list)) or not 3 <= len(weight_sweep) <= controls["max_sweep_cases"]:
        raise ValueError("weight sweep shape")
    if not all(finite_real(value) and 0 <= value <= 2 for value in weight_sweep):
        raise ValueError("weight sweep values")
    if any(right <= left for left, right in zip(weight_sweep, weight_sweep[1:])):
        raise ValueError("weight sweep order")
    if controls["weight_exponent"] not in weight_sweep:
        raise ValueError("weight sweep baseline")


def validate_scene(score: object, mask: object, range_axis: object, velocity_axis: object) -> tuple[int, int]:
    if not isinstance(score, list) or not score or not all(isinstance(row, list) for row in score):
        raise ValueError("score matrix")
    columns = len(score[0])
    if columns == 0 or any(len(row) != columns for row in score):
        raise ValueError("rectangular score")
    if not all(finite_real(value) for row in score for value in row):
        raise ValueError("finite score")
    if any(value < 0 for row in score for value in row):
        raise ValueError("nonnegative score")
    if not isinstance(mask, list) or len(mask) != len(score) or any(
        not isinstance(row, list) or len(row) != columns for row in mask
    ):
        raise ValueError("mask shape")
    if not all(type(value) is bool for row in mask for value in row):
        raise ValueError("logical mask")
    if any(mask[row][column] and score[row][column] <= 1 for row in range(len(score)) for column in range(columns)):
        raise ValueError("detection threshold")
    if not isinstance(range_axis, (tuple, list)) or len(range_axis) != len(score):
        raise ValueError("range axis")
    if not isinstance(velocity_axis, (tuple, list)) or len(velocity_axis) != columns:
        raise ValueError("velocity axis")
    for axis in (range_axis, velocity_axis):
        if not all(finite_real(value) for value in axis) or any(
            right <= left for left, right in zip(axis, axis[1:])
        ):
            raise ValueError("increasing finite axis")
        steps = [right - left for left, right in zip(axis, axis[1:])]
        if steps and any(not math.isclose(step, steps[0], rel_tol=0, abs_tol=1e-12) for step in steps):
            raise ValueError("uniform axis")
    return len(score), columns


def local_maxima(score: list[list[float]], mask: list[list[bool]]) -> list[list[bool]]:
    rows = len(score)
    columns = len(score[0])
    output = [[False] * columns for _ in range(rows)]
    visited = [[False] * columns for _ in range(rows)]
    for seed_row in range(rows):
        for seed_column in range(columns):
            if not mask[seed_row][seed_column] or visited[seed_row][seed_column]:
                continue
            plateau_value = score[seed_row][seed_column]
            plateau_is_maximum = True
            visited[seed_row][seed_column] = True
            queue = deque([(seed_row, seed_column)])
            while queue:
                row, column = queue.popleft()
                for row_step in (-1, 0, 1):
                    for column_step in (-1, 0, 1):
                        if row_step == column_step == 0:
                            continue
                        neighbor_row = row + row_step
                        neighbor_column = column + column_step
                        if not (0 <= neighbor_row < rows and 0 <= neighbor_column < columns):
                            continue
                        if not mask[neighbor_row][neighbor_column]:
                            continue
                        if score[neighbor_row][neighbor_column] > plateau_value:
                            plateau_is_maximum = False
                        elif score[neighbor_row][neighbor_column] == plateau_value and not visited[neighbor_row][neighbor_column]:
                            visited[neighbor_row][neighbor_column] = True
                            queue.append((neighbor_row, neighbor_column))
            output[seed_row][seed_column] = plateau_is_maximum
    return output


def group_reports(
    score: list[list[float]],
    mask: list[list[bool]],
    range_axis: list[float],
    velocity_axis: list[float],
    minimum_cells: int = 3,
    exponent: float = 1.0,
) -> tuple[list[list[int]], list[dict[str, float]]]:
    rows, columns = validate_scene(score, mask, range_axis, velocity_axis)
    if not integer(minimum_cells) or not 1 <= minimum_cells <= rows * columns:
        raise ValueError("minimum cells")
    if not finite_real(exponent) or not 0 <= exponent <= 2:
        raise ValueError("exponent")
    labels = [[0] * columns for _ in range(rows)]
    reports: list[dict[str, float]] = []
    component_id = 0
    for seed_row in range(rows):
        for seed_column in range(columns):
            if not mask[seed_row][seed_column] or labels[seed_row][seed_column]:
                continue
            component_id += 1
            labels[seed_row][seed_column] = component_id
            queue = deque([(seed_row, seed_column)])
            cells: list[tuple[int, int]] = []
            while queue:
                row, column = queue.popleft()
                cells.append((row, column))
                for row_step in (-1, 0, 1):
                    for column_step in (-1, 0, 1):
                        if row_step == column_step == 0:
                            continue
                        neighbor_row = row + row_step
                        neighbor_column = column + column_step
                        if not (0 <= neighbor_row < rows and 0 <= neighbor_column < columns):
                            continue
                        if mask[neighbor_row][neighbor_column] and not labels[neighbor_row][neighbor_column]:
                            labels[neighbor_row][neighbor_column] = component_id
                            queue.append((neighbor_row, neighbor_column))
            if len(cells) < minimum_cells:
                continue
            excess = [score[row][column] - 1 for row, column in cells]
            weights = [value**exponent for value in excess]
            weight_sum = sum(weights)
            if not math.isfinite(weight_sum) or weight_sum <= 0:
                raise ValueError("degenerate weights")
            estimated_range = sum(weight * range_axis[row] for weight, (row, _) in zip(weights, cells)) / weight_sum
            estimated_velocity = sum(weight * velocity_axis[column] for weight, (_, column) in zip(weights, cells)) / weight_sum
            effective_cells = weight_sum**2 / sum(weight**2 for weight in weights)
            range_second = sum(
                weight * (range_axis[row] - estimated_range) ** 2
                for weight, (row, _) in zip(weights, cells)
            ) / weight_sum
            velocity_second = sum(
                weight * (velocity_axis[column] - estimated_velocity) ** 2
                for weight, (_, column) in zip(weights, cells)
            ) / weight_sum
            range_spacing = min(right - left for left, right in zip(range_axis, range_axis[1:]))
            velocity_spacing = min(right - left for left, right in zip(velocity_axis, velocity_axis[1:]))
            reports.append(
                {
                    "component_id": component_id,
                    "range": estimated_range,
                    "velocity": estimated_velocity,
                    "cells": float(len(cells)),
                    "integrated_excess": sum(excess),
                    "effective_cells": effective_cells,
                    "range_proxy": math.sqrt(range_second / effective_cells + range_spacing**2 / 12),
                    "velocity_proxy": math.sqrt(velocity_second / effective_cells + velocity_spacing**2 / 12),
                }
            )
    return labels, reports


def source_binding_errors(source: str) -> list[str]:
    required = (
        "random_seed = 5301;",
        "number_range_bins = 72;",
        "number_velocity_bins = 65;",
        "minimum_component_cells = 3;",
        "centroid_weight_exponent = 1;",
        "minimum_component_cell_sweep = [1 3 18];",
        "centroid_weight_exponent_sweep = [0 1 2];",
        "~isscalar(number_range_bins)",
        "~isreal(integer_controls)",
        "~isscalar(range_bin_spacing_m)",
        "islogical(normalized_detection_threshold)",
        "~isreal(real_controls)",
        "~isreal(minimum_component_cell_sweep)",
        "~isreal(centroid_weight_exponent_sweep)",
        "minimum_component_cells < 1",
        "any(minimum_component_cell_sweep < 1)",
        "minimum_component_cell_sweep(sweep_index)",
        "centroid_weight_exponent_sweep(sweep_index)",
        "private_stream = RandStream('mt19937ar', 'Seed', random_seed);",
        "normalized_score = 0.25 + 0.20*background_texture;",
        "detection_mask = normalized_score > normalized_detection_threshold;",
        "plateau_value = score(seed_row, seed_column);",
        "if neighbor_value > plateau_value",
        "elseif neighbor_value == plateau_value && ...\n                            ~plateau_visited(neighbor_row, neighbor_column)",
        "local_maximum_mask(seed_row, seed_column) = true;",
        "if row_step == 0 && column_step == 0\n                        continue;\n                    end\n                    neighbor_row = current_row + row_step;",
        "neighbor_row = current_row + row_step;",
        "neighbor_column = current_column + column_step;",
        "labels(neighbor_row, neighbor_column) = component_count;",
        "if component_cell_count < minimum_cells\n            continue;\n        end",
        "component_excess = score(component_linear_indices) - 1;",
        "weights = component_excess.^weight_exponent;",
        "estimated_range_m = sum(weights.*component_ranges)/weight_sum;",
        "estimated_velocity_mps = sum(weights.*component_velocities)/weight_sum;",
        "effective_cell_count = weight_sum^2/sum(weights.^2);",
        "report.range_m = estimated_range_m;",
        "report.velocity_mps = estimated_velocity_mps;",
        "[broken_rows, broken_columns] = find(local_maximum_mask);",
        "broken_report_count = numel(broken_rows);",
        "assert(isequal(size_sweep_report_count, [7 2 1])",
        "assert(isequal(size_sweep_truth_count, [2 2 1])",
        "reviewed_run = random_seed == 5301 &&",
        "isequal(minimum_component_cell_sweep, [1 3 18])",
        "isequal(centroid_weight_exponent_sweep, [0 1 2])",
        "if reviewed_run",
        "results.broken_report_count = broken_report_count;",
        "results.recovered_report_count = recovered_report_count;",
    )
    errors = [marker for marker in required if marker not in source]
    try:
        peak_source = source[
            source.index("function local_maximum_mask = select_local_maxima"):
            source.index("function [labels, reports, component_count] = group_detection_cells")
        ]
        group_source = source[
            source.index("function [labels, reports, component_count] = group_detection_cells"):
            source.index("function metrics = compare_known_truth_components")
        ]
    except ValueError:
        return errors + ["local operation boundaries"]
    connectivity_block = (
        "if row_step == 0 && column_step == 0\n"
        "                        continue;\n"
        "                    end\n"
        "                    neighbor_row = current_row + row_step;"
    )
    if connectivity_block not in peak_source:
        errors.append("peak 8-connectivity traversal")
    if connectivity_block not in group_source:
        errors.append("group 8-connectivity traversal")
    if "neighbor_value == plateau_value" not in peak_source:
        errors.append("plateau equality traversal")
    if "component_cell_count < minimum_cells" not in group_source:
        errors.append("minimum-size acceptance")
    if "component_excess = score(component_linear_indices) - 1;" not in group_source:
        errors.append("excess-score weights")
    detection_assignments = re.findall(
        r"(?m)^\s*detection_mask(?:\s*\([^\n=]*\))?\s*=", source,
    )
    if len(detection_assignments) != 1:
        errors.append("single detection-mask assignment")
    if len(re.findall(r"(?m)^\s*reviewed_run\s*=", source)) != 1:
        errors.append("single reviewed-run assignment")
    if len(re.findall(r"(?m)^\s*report\.range_m\s*=", group_source)) != 1:
        errors.append("single report range assignment")
    if len(re.findall(r"(?m)^\s*report\.velocity_mps\s*=", group_source)) != 1:
        errors.append("single report velocity assignment")
    return errors


class P53ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self) -> None:
        self.assertEqual(validate_p53_contract(MODULE, self.manifest), [])
        p52 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P52")
        self.assertEqual(p52["status"], "implemented")
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
            self.assertIn("P53 missing lesson.md", validate_p53_contract(fixture, self.manifest))
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P53 empty lesson.md", validate_p53_contract(fixture, self.manifest))
        for malformed in (None, [], {}, {"modules": None}, {"modules": ["P53"]}):
            self.assertTrue(validate_p53_contract(MODULE, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P53 manifest entry, found 2", validate_p53_contract(MODULE, duplicate))
        for key in EXPECTED_IDENTITY:
            drifted = copy.deepcopy(self.manifest)
            entry = next(item for item in drifted["modules"] if item["id"] == "P53")
            entry[key] = "drift" if not isinstance(entry[key], int) else -1
            self.assertTrue(validate_p53_contract(MODULE, drifted), key)

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self) -> None:
        validate_controls()
        bad_cases = (
            {"unknown": 1}, {"seed": True}, {"seed": 5302},
            {"range_bins": 71}, {"velocity_bins": 66},
            {"range_spacing": 14.5}, {"velocity_spacing": math.nan},
            {"threshold": 1.1}, {"minimum_cells": 0},
            {"weight_exponent": 2.1}, {"size_sweep": (1, 1, 3)},
            {"size_sweep": (1, 5, 7)}, {"weight_sweep": (0, 2, 1)},
            {"weight_sweep": (0, 1, math.inf)}, {"max_scene_cells": 20_001},
            {"max_queue_cells": 4679}, {"max_sweep_cases": 6},
            {"max_figures": 7},
        )
        for controls in bad_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_local_maximum_oracle_handles_edges_and_row_major_plateau_ties(self) -> None:
        score = [[2.0, 2.0, 0.2], [1.2, 1.5, 0.2], [0.2, 0.2, 3.0]]
        mask = [[value > 1 for value in row] for row in score]
        maxima = local_maxima(score, mask)
        self.assertTrue(maxima[0][0])
        self.assertFalse(maxima[0][1])
        self.assertFalse(maxima[1][0])
        self.assertFalse(maxima[1][1])
        self.assertTrue(maxima[2][2])
        self.assertEqual(sum(sum(row) for row in maxima), 2)
        nonconvex_score = [[2.0, 0.2, 2.0], [0.2, 2.0, 0.2], [0.2, 0.2, 0.2]]
        nonconvex_mask = [[value > 1 for value in row] for row in nonconvex_score]
        nonconvex_maxima = local_maxima(nonconvex_score, nonconvex_mask)
        self.assertTrue(nonconvex_maxima[0][0])
        self.assertFalse(nonconvex_maxima[0][2])
        self.assertFalse(nonconvex_maxima[1][1])
        self.assertEqual(sum(sum(row) for row in nonconvex_maxima), 1)

    def test_grouping_oracle_joins_diagonals_filters_noise_and_separates_blobs(self) -> None:
        score = [[0.2] * 8 for _ in range(7)]
        for row, column, value in (
            (0, 0, 2.0), (1, 1, 2.5), (2, 2, 2.0),
            (4, 5, 1.5), (4, 6, 3.0), (5, 6, 1.5),
            (6, 0, 1.4),
        ):
            score[row][column] = value
        mask = [[value > 1 for value in row] for row in score]
        labels, reports = group_reports(score, mask, list(range(7)), list(range(8)))
        self.assertEqual(labels[0][0], labels[2][2])
        self.assertNotEqual(labels[0][0], labels[4][5])
        self.assertEqual(len(reports), 2)
        self.assertEqual([report["cells"] for report in reports], [3.0, 3.0])
        self.assertGreater(reports[0]["range_proxy"], 0)
        self.assertGreater(reports[1]["velocity_proxy"], 0)

    def test_end_to_end_peak_only_failure_and_grouped_report_recovery(self) -> None:
        score = [[0.2] * 9 for _ in range(7)]
        for row, column, value in (
            (1, 1, 2.0), (1, 2, 3.0), (2, 1, 2.2), (2, 2, 1.8),
            (4, 5, 1.6), (4, 6, 2.7), (5, 5, 2.1), (5, 6, 1.7),
            (0, 8, 1.3),
            (6, 0, 1.4), (6, 1, 1.2),
        ):
            score[row][column] = value
        mask = [[value > 1 for value in row] for row in score]
        peaks = local_maxima(score, mask)
        range_axis = [100.0 + 15.0 * row for row in range(7)]
        velocity_axis = [-2.0 + 0.5 * column for column in range(9)]

        labels, recovered = group_reports(
            score, mask, range_axis, velocity_axis, minimum_cells=3,
        )
        report_counts = [
            len(group_reports(score, mask, range_axis, velocity_axis, minimum_cells=size)[1])
            for size in (1, 3, 5)
        ]

        self.assertEqual(sum(sum(row) for row in mask), 11)
        self.assertEqual(sum(sum(row) for row in peaks), 4)
        self.assertEqual(report_counts, [4, 2, 0])
        self.assertEqual(len(recovered), 2)
        self.assertEqual([report["cells"] for report in recovered], [4.0, 4.0])
        for report in recovered:
            component_id = report["component_id"]
            component_peak_count = sum(
                peaks[row][column] and labels[row][column] == component_id
                for row in range(7)
                for column in range(9)
            )
            self.assertEqual(component_peak_count, 1)

    def test_documented_four_case_size_sweep_runs_without_default_assertion_contract(self) -> None:
        score = [[0.2] * 9 for _ in range(7)]
        for row, column, value in (
            (1, 1, 2.0), (1, 2, 3.0), (2, 1, 2.2), (2, 2, 1.8),
            (4, 5, 1.6), (4, 6, 2.7), (5, 5, 2.1), (5, 6, 1.7),
            (0, 8, 1.3),
            (6, 0, 1.4), (6, 1, 1.2),
        ):
            score[row][column] = value
        mask = [[value > 1 for value in row] for row in score]
        range_axis = [100.0 + 15.0 * row for row in range(7)]
        velocity_axis = [-2.0 + 0.5 * column for column in range(9)]
        documented_sweep = (1, 2, 3, 18)

        report_counts = [
            len(group_reports(score, mask, range_axis, velocity_axis, minimum_cells=size)[1])
            for size in documented_sweep
        ]
        self.assertEqual(report_counts, [4, 3, 2, 0])
        self.assertIn("Try `[1 2 3 18]`", self.walkthrough)
        reviewed_predicate = self.source[
            self.source.index("reviewed_run ="):self.source.index("if reviewed_run")
        ]
        self.assertIn("isequal(minimum_component_cell_sweep, [1 3 18])", reviewed_predicate)
        self.assertIn("isequal(centroid_weight_exponent_sweep, [0 1 2])", reviewed_predicate)

    def test_weighted_centroid_equations_and_limiting_invariants(self) -> None:
        score = [[2.0, 3.0, 4.0], [0.2, 0.2, 0.2]]
        mask = [[True, True, True], [False, False, False]]
        axes = [0.0, 10.0, 20.0]
        _, uniform = group_reports(score, mask, [100.0, 115.0], axes, minimum_cells=1, exponent=0)
        _, weighted = group_reports(score, mask, [100.0, 115.0], axes, minimum_cells=1, exponent=1)
        self.assertAlmostEqual(uniform[0]["velocity"], 10.0)
        self.assertAlmostEqual(weighted[0]["velocity"], (0 + 20 + 60) / 6)
        self.assertGreater(weighted[0]["velocity"], uniform[0]["velocity"])
        self.assertAlmostEqual(weighted[0]["range"], 100.0)
        translated_axes = [value + 7.5 for value in axes]
        _, translated = group_reports(score, mask, [100.0, 115.0], translated_axes, minimum_cells=1, exponent=1)
        self.assertAlmostEqual(translated[0]["velocity"] - weighted[0]["velocity"], 7.5)

    def test_oracle_rejects_malformed_scene_and_degenerate_controls(self) -> None:
        good_score = [[2.0, 0.2], [0.2, 2.0]]
        good_mask = [[True, False], [False, True]]
        malformed = (
            ([], good_mask, [0, 1], [0, 1]),
            ([[2.0], [2.0, 3.0]], good_mask, [0, 1], [0, 1]),
            ([[math.nan, 0.2], [0.2, 2.0]], good_mask, [0, 1], [0, 1]),
            (good_score, [[1, False], [False, True]], [0, 1], [0, 1]),
            (good_score, [[True]], [0, 1], [0, 1]),
            ([[-0.1, 0.2], [0.2, 2.0]], [[False, False], [False, True]], [0, 1], [0, 1]),
            (good_score, good_mask, [0], [0, 1]),
            (good_score, good_mask, [0, 0], [0, 1]),
            ([[2.0, 0.2, 0.2], [0.2, 0.2, 2.0]], [[True, False, False], [False, False, True]], [0, 1], [0, 1, 2.5]),
            (good_score, good_mask, [0, 1], [0, math.inf]),
        )
        for arguments in malformed:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                group_reports(*arguments, minimum_cells=1)
        with self.assertRaises(ValueError):
            group_reports(good_score, good_mask, [0, 1], [0, 1], minimum_cells=True)
        with self.assertRaises(ValueError):
            group_reports(good_score, good_mask, [0, 1], [0, 1], exponent=math.nan)
        with self.assertRaises(ValueError):
            group_reports(good_score, good_mask, [0, 1], [0, 1], exponent=True)

    def test_source_is_seeded_transparent_bounded_and_mutation_sensitive(self) -> None:
        self.assertEqual(source_binding_errors(self.source), [])
        self.assertNotRegex(self.source, r"(?<![A-Za-z])rng\s*\(")
        self.assertNotRegex(self.source, r"randn\((?!private_stream)")
        for banned in (
            "bwconncomp", "bwlabel", "regionprops", "imregionalmax", "imdilate",
            "strel(", "graph(", "conncomp(", "parfor", "fopen(", "webread(",
            "system(", "timer(", "tcpclient(", "trackingKF", "objectDetection",
        ):
            self.assertNotIn(banned, self.source)
        self.assertLess(self.source.index("%% Visible controls"), self.source.index("queue_rows = zeros(maximum_queue_cells"))
        mutations = (
            self.source.replace("random_seed = 5301;", "random_seed = 53;", 1),
            self.source.replace("normalized_score > normalized_detection_threshold", "normalized_score >= normalized_detection_threshold", 1),
            self.source.replace("weights = component_excess.^weight_exponent;", "weights = ones(size(component_excess));", 1),
            self.source.replace(
                "if row_step == 0 && column_step == 0\n                        continue;\n                    end\n                    neighbor_row = current_row + row_step;",
                "if row_step == 0 || column_step == 0\n                        continue;\n                    end\n                    neighbor_row = current_row + row_step;",
            ),
            self.source.replace("component_cell_count < minimum_cells", "component_cell_count <= minimum_cells", 1),
            self.source.replace("component_excess = score(component_linear_indices) - 1;", "component_excess = score(component_linear_indices);", 1),
            self.source.replace("neighbor_value == plateau_value", "neighbor_value <= plateau_value", 1),
            self.source.replace("if neighbor_value > plateau_value", "if neighbor_value < plateau_value", 1),
            self.source.replace("find(local_maximum_mask)", "find(detection_mask)", 1),
            self.source.replace("broken_report_count = numel(broken_rows);", "broken_report_count = recovered_report_count + 1;", 1),
            self.source.replace("report.range_m = estimated_range_m;", "report.range_m = 0;", 1),
            self.source.replace("report.velocity_mps = estimated_velocity_mps;", "report.velocity_mps = 0;", 1),
            self.source.replace(
                "reviewed_run = random_seed == 5301 &&",
                "reviewed_run = false && random_seed == 5301 &&",
                1,
            ),
            self.source.replace(
                "isequal(minimum_component_cell_sweep, [1 3 18])",
                "true",
                1,
            ),
            self.source.replace(
                "detection_mask = normalized_score > normalized_detection_threshold;",
                "detection_mask = normalized_score > normalized_detection_threshold;\n"
                "detection_mask(:) = false;",
                1,
            ),
            self.source.replace("any(minimum_component_cell_sweep < 1)", "false", 1),
            self.source.replace("minimum_component_cell_sweep(sweep_index)", "minimum_component_cells", 1),
            self.source.replace("centroid_weight_exponent_sweep(sweep_index)", "centroid_weight_exponent", 1),
            self.source.replace("size_sweep_report_count, [7 2 1]", "size_sweep_report_count, [7 2 2]", 1),
        )
        for mutated in mutations:
            self.assertTrue(source_binding_errors(mutated))

    def test_sweeps_broken_case_markers_outputs_and_resource_bounds(self) -> None:
        for marker in (
            "%% Sweep 1: change only the minimum accepted component size",
            "%% Sweep 2: change only the excess-power centroid exponent",
            "%% Broken case: promote every local maximum directly to a tracker report",
            "range_extent_m", "velocity_extent_mps", "integrated_excess_ratio",
            "range_uncertainty_proxy_m", "velocity_uncertainty_proxy_mps",
            "uncalibrated morphology proxy, not tracker covariance R",
            "results.size_sweep_report_count", "results.weight_sweep_range_error_m",
        ):
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P53"), 6)
        controls = canonical_controls()
        self.assertEqual(controls["range_bins"] * controls["velocity_bins"], 4680)
        self.assertLessEqual(4680, controls["max_scene_cells"])
        self.assertLessEqual(4680, controls["max_queue_cells"])

    def test_docs_cover_model_sweeps_failure_recovery_cancellation_and_teach_back(self) -> None:
        combined = "\n".join((self.readme, self.lesson, self.walkthrough, self.checks))
        for term in (
            QUESTION, "P42", "P50", "P52", "P54", "P57", "local maximum",
            "8-connect", "row-major", "component", "weighted centroid",
            "score - 1", "minimum component", "extent", "uncalibrated",
            "covariance", "touching", "Sweep 1", "Sweep 2", "broken",
            "Recovery", "Ctrl+C", "timeout", "teach-back", "hardware/HIL",
            "operational radar",
        ):
            self.assertIn(term.lower(), combined.lower())
        self.assertIn("change only minimum component size", self.walkthrough)
        self.assertIn("change only centroid weighting", self.walkthrough)
        self.assertGreaterEqual(self.checks.count("Correct:"), 10)
        self.assertGreaterEqual(self.checks.count("Incorrect:"), 10)

    def test_no_placeholder_or_unexplained_black_box_regression(self) -> None:
        combined = "\n".join((self.source, self.readme, self.lesson, self.walkthrough, self.checks))
        self.assertNotRegex(combined, r"(?i)\bTODO\b|\bTBD\b|lorem ipsum|coming soon")
        self.assertNotRegex(combined, r"(?i)copy.+toolbox|use an image processing object")
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
        completed = [f"P{number:02d}" for number in range(1, 53)]
        initial = {
            "schema_version": 1, "current": "P52", "completed": completed,
            "notes": {"P52": "Validated the detector model before grouping."},
        }
        advanced_state: dict = {}
        advanced = self._run_fixture_cli(
            self.manifest, "start", initial_state=initial, state_capture=advanced_state,
        )
        self.assertEqual(advanced.returncode, 0, advanced.stderr)
        self.assertIn("P53 — Group Detection Cells into Target Reports", advanced.stdout)
        self.assertIn("status: implemented", advanced.stdout)
        self.assertEqual(advanced_state["current"], "P53")
        self.assertEqual(advanced_state["completed"], completed)
        self.assertEqual(advanced_state["notes"], initial["notes"])

        rolled_back = copy.deepcopy(self.manifest)
        p52_before = copy.deepcopy(next(entry for entry in rolled_back["modules"] if entry["id"] == "P52"))
        p54_before = copy.deepcopy(next(entry for entry in rolled_back["modules"] if entry["id"] == "P54"))
        next(entry for entry in rolled_back["modules"] if entry["id"] == "P53")["status"] = "scaffolded"
        changed_entries = [
            (before_entry["id"], key)
            for before_entry, after_entry in zip(self.manifest["modules"], rolled_back["modules"])
            for key in before_entry
            if before_entry.get(key) != after_entry.get(key)
        ]
        self.assertEqual(changed_entries, [("P53", "status")])
        rollback_state: dict = {}
        rollback_result = self._run_fixture_cli(
            rolled_back, "start", "53", initial_state=initial,
            state_capture=rollback_state,
        )
        self.assertEqual(rollback_result.returncode, 3)
        self.assertIn("awaits Portfolio batch P53", rollback_result.stdout)
        self.assertEqual(rollback_state["current"], "P53")
        self.assertEqual(rollback_state["completed"], initial["completed"])
        self.assertEqual(rollback_state["notes"], initial["notes"])
        self.assertEqual(next(entry for entry in rolled_back["modules"] if entry["id"] == "P52"), p52_before)
        self.assertEqual(next(entry for entry in rolled_back["modules"] if entry["id"] == "P54"), p54_before)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_public_catalogs_describe_p53_without_freezing_future_state(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 53 begins Phase 6", root_readme)
        self.assertIn("Project 53 follows P52 and begins Phase 6", start_here)
        self.assertRegex(module_index, r"\| \[P53\].*\| implemented \| 6 \|")
        self.assertNotRegex("\n".join((root_readme, start_here)), r"(?i)P53 is (the )?latest")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self) -> None:
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P53-*.md"))
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
            "python3 -m unittest tests.test_p53_module -v",
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
