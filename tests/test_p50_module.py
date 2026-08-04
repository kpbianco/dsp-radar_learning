from __future__ import annotations

import copy
import json
import math
import os
import random
import re
import shutil
import subprocess
import tempfile
import unittest
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/50-apply-2-d-cfar-to-a-range-doppler-map"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How does local thresholding extend from one range profile to two dimensions?"
EXPECTED_IDENTITY = {
    "number": 50,
    "id": "P50",
    "title": "Apply 2-D CFAR to a Range-Doppler Map",
    "guiding_question": QUESTION,
    "phase": 5,
    "phase_title": "Detection and CFAR",
    "slug": "apply-2-d-cfar-to-a-range-doppler-map",
    "folder": "modules/50-apply-2-d-cfar-to-a-range-doppler-map",
    "status": "implemented",
    "implementation_batch": "P50",
}


def validate_p50_contract(module: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P50 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P50 empty {artifact}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        errors.append("manifest modules must be a list")
        return errors
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("manifest module entries must be objects")
        return errors
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P50"]
    if len(entries) != 1:
        errors.append(f"expected one P50 manifest entry, found {len(entries)}")
        return errors
    for key, expected in EXPECTED_IDENTITY.items():
        if entries[0].get(key) != expected:
            errors.append(f"P50 {key} mismatch")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _integer(value: object) -> bool:
    return _finite_real(value) and value == int(value)


def validate_controls(**overrides: object) -> None:
    controls: dict[str, object] = {
        "seed": 5001,
        "range_bins": 96,
        "doppler_bins": 64,
        "range_spacing": 30.0,
        "velocity_spacing": 0.625,
        "pfa": 1e-3,
        "tr": 6,
        "gr": 2,
        "td": 4,
        "gd": 2,
        "range_sweep": (3, 6, 12),
        "doppler_sweep": (2, 4, 8),
        "target_rows": (28, 53, 76, 4),
        "target_columns": (45, 22, 35, 8),
        "target_snr_db": (24.0, 20.0, 18.0, 20.0),
        "max_range_bins": 128,
        "max_doppler_bins": 96,
        "max_targets": 6,
        "max_half_width": 16,
        "max_cases": 4,
        "max_figures": 6,
        "max_stored": 400_000,
        "max_visits": 30_000_000,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    integer_names = (
        "seed",
        "range_bins",
        "doppler_bins",
        "tr",
        "gr",
        "td",
        "gd",
        "max_range_bins",
        "max_doppler_bins",
        "max_targets",
        "max_half_width",
        "max_cases",
        "max_figures",
        "max_stored",
        "max_visits",
    )
    if not all(_integer(controls[name]) for name in integer_names):
        raise ValueError("integer controls must be finite non-logical integers")
    if controls["seed"] != 5001:
        raise ValueError("seed drift")
    if controls["max_range_bins"] != 128 or controls["max_doppler_bins"] != 96:
        raise ValueError("map ceiling drift")
    if (
        controls["max_targets"] != 6
        or controls["max_half_width"] != 16
        or controls["max_cases"] != 4
        or controls["max_figures"] != 6
        or controls["max_stored"] != 400_000
        or controls["max_visits"] != 30_000_000
    ):
        raise ValueError("resource ceiling drift")
    if not (32 <= controls["range_bins"] <= controls["max_range_bins"]):
        raise ValueError("range size")
    if not (
        32 <= controls["doppler_bins"] <= controls["max_doppler_bins"]
        and controls["doppler_bins"] % 2 == 0
    ):
        raise ValueError("Doppler size")
    for name in ("range_spacing", "velocity_spacing"):
        if not _finite_real(controls[name]) or controls[name] <= 0:
            raise ValueError("axis spacing")
    if not _finite_real(controls["pfa"]) or not 1e-6 <= controls["pfa"] <= 0.1:
        raise ValueError("Pfa")
    for name in ("tr", "gr", "td", "gd"):
        if not 1 <= controls[name] <= controls["max_half_width"]:
            raise ValueError("geometry")

    for name, baseline in (("range_sweep", 6), ("doppler_sweep", 4)):
        values = controls[name]
        if not isinstance(values, (tuple, list)) or not 3 <= len(values) <= controls["max_cases"]:
            raise ValueError("sweep shape")
        if not all(_integer(value) and 1 <= value <= controls["max_half_width"] for value in values):
            raise ValueError("sweep values")
        if any(a >= b for a, b in zip(values, values[1:])) or baseline not in values:
            raise ValueError("sweep ordering/baseline")

    rows = controls["target_rows"]
    columns = controls["target_columns"]
    snr = controls["target_snr_db"]
    if not all(isinstance(values, (tuple, list)) for values in (rows, columns, snr)):
        raise ValueError("target shape")
    if not len(rows) == len(columns) == len(snr) or not 4 <= len(rows) <= controls["max_targets"]:
        raise ValueError("target count")
    if not all(_integer(value) and 1 <= value <= controls["range_bins"] for value in rows):
        raise ValueError("target rows")
    if not all(_integer(value) and 1 <= value <= controls["doppler_bins"] for value in columns):
        raise ValueError("target columns")
    if not all(_finite_real(value) and -10 <= value <= 40 for value in snr):
        raise ValueError("target SNR")

    largest_r = max(controls["range_sweep"]) + controls["gr"]
    largest_d = max(controls["doppler_sweep"]) + controls["gd"]
    if 2 * largest_r + 1 >= controls["range_bins"] or 2 * largest_d + 1 >= controls["doppler_bins"]:
        raise ValueError("geometry does not fit")
    stored = 34 * controls["range_bins"] * controls["doppler_bins"] + 5000
    visits = (
        (2 + len(controls["range_sweep"]) + len(controls["doppler_sweep"]))
        * controls["range_bins"]
        * controls["doppler_bins"]
        * (2 * largest_r + 1)
        * (2 * largest_d + 1)
    )
    if stored > controls["max_stored"] or visits > controls["max_visits"]:
        raise ValueError("resource budget")


def stencil_offsets(tr: int, gr: int, td: int, gd: int) -> list[tuple[int, int]]:
    hr, hd = tr + gr, td + gd
    return [
        (row, column)
        for row in range(-hr, hr + 1)
        for column in range(-hd, hd + 1)
        if not (abs(row) <= gr and abs(column) <= gd)
    ]


def ca_alpha(training_count: int, pfa: float) -> float:
    if not _integer(training_count) or training_count <= 0:
        raise ValueError("training count")
    if not _finite_real(pfa) or not 0 < pfa < 1:
        raise ValueError("Pfa")
    return training_count * (pfa ** (-1 / training_count) - 1)


def apply_cfar(
    power: list[list[float]], tr: int, gr: int, td: int, gd: int, pfa: float
) -> tuple[list[list[float]], list[list[bool]], list[list[bool]]]:
    if not power or not power[0] or any(len(row) != len(power[0]) for row in power):
        raise ValueError("rectangular nonempty power map required")
    if any(not _finite_real(value) or value < 0 for row in power for value in row):
        raise ValueError("finite nonnegative power required")
    offsets = stencil_offsets(tr, gr, td, gd)
    alpha = ca_alpha(len(offsets), pfa)
    rows, columns = len(power), len(power[0])
    hr, hd = tr + gr, td + gd
    if rows <= 2 * hr or columns <= 2 * hd:
        raise ValueError("stencil does not fit")
    threshold = [[math.nan] * columns for _ in range(rows)]
    testable = [[False] * columns for _ in range(rows)]
    detection = [[False] * columns for _ in range(rows)]
    for row in range(hr, rows - hr):
        for column in range(hd, columns - hd):
            estimate = sum(power[row + dr][column + dc] for dr, dc in offsets) / len(offsets)
            threshold[row][column] = alpha * estimate
            testable[row][column] = True
            detection[row][column] = power[row][column] > threshold[row][column]
    return threshold, testable, detection


def apply_zero_padded_cfar(
    power: list[list[float]], tr: int, gr: int, td: int, gd: int, pfa: float
) -> tuple[list[list[float]], list[list[bool]]]:
    if not power or not power[0] or any(len(row) != len(power[0]) for row in power):
        raise ValueError("rectangular nonempty power map required")
    if any(not _finite_real(value) or value < 0 for row in power for value in row):
        raise ValueError("finite nonnegative power required")
    offsets = stencil_offsets(tr, gr, td, gd)
    alpha = ca_alpha(len(offsets), pfa)
    rows, columns = len(power), len(power[0])
    threshold = [[0.0] * columns for _ in range(rows)]
    detection = [[False] * columns for _ in range(rows)]
    for row in range(rows):
        for column in range(columns):
            training_sum = sum(
                power[sample_row][sample_column]
                if 0 <= sample_row < rows and 0 <= sample_column < columns
                else 0.0
                for dr, dc in offsets
                for sample_row, sample_column in ((row + dr, column + dc),)
            )
            threshold[row][column] = alpha * training_sum / len(offsets)
            detection[row][column] = power[row][column] > threshold[row][column]
    return threshold, detection


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", "", source)
    required = (
        "random_seed=5001;",
        "private_stream=RandStream('mt19937ar','Seed',random_seed);",
        "background_mean_power=range_background_scale*doppler_background_scale;",
        "range_doppler_power=abs(complex_background).^2;",
        "training_mask(guard_rows,guard_columns)=false;",
        "training_cell_count=sum(training_mask(:));",
        "design_false_alarm_probability^(-1/training_cell_count)-1",
        "training_power=local_power(training_mask);",
        "sum(training_power)/training_cell_count;",
        "cfar_detection=testable_mask&range_doppler_power>cfar_threshold;",
        "range_training_sweep=[3612];",
        "doppler_training_sweep=[248];",
        "candidate_range_training=range_training_sweep(case_index);",
        "candidate_doppler_training=doppler_training_sweep(case_index);",
        "padded_power=zeros(range_bin_count+2*range_outer_half_width,",
        "broken_all_cells_calibrated_claim_is_valid=false;",
        "recovered_threshold(border_mask)=NaN;",
        "isequal(recovered_detection,cfar_detection);",
        "results.max_training_sample_visits=max_training_sample_visits;",
    )
    return [marker for marker in required if marker not in compact]


@lru_cache(maxsize=1)
def independent_scene_oracle() -> dict[str, object]:
    rows, columns = 96, 64
    velocity = [(index - columns / 2) * 0.625 for index in range(columns)]
    background = [
        [
            (0.8 + 1.2 * (row / (rows - 1)) ** 2)
            * (1 + 2.5 * math.exp(-((speed / 2.5) ** 2)))
            for speed in velocity
        ]
        for row in range(rows)
    ]
    generator = random.Random(5001)
    power = [
        [-mean * math.log1p(-generator.random()) for mean in row]
        for row in background
    ]
    target_rows = (27, 52, 75, 3)
    target_columns = (44, 21, 34, 7)
    target_snr = (24.0, 20.0, 18.0, 20.0)
    range_response = (0.015, 0.05, 0.20, 0.55, 1, 0.55, 0.20, 0.05, 0.015)
    doppler_response = (0.01, 0.04, 0.18, 0.50, 1, 0.50, 0.18, 0.04, 0.01)
    for center_row, center_column, snr_db in zip(target_rows, target_columns, target_snr):
        peak = background[center_row][center_column] * 10 ** (snr_db / 10)
        for response_row, row_weight in enumerate(range_response, start=-4):
            for response_column, column_weight in enumerate(doppler_response, start=-4):
                row = center_row + response_row
                column = center_column + response_column
                if 0 <= row < rows and 0 <= column < columns:
                    power[row][column] += peak * row_weight * column_weight
    threshold, testable, detection = apply_cfar(power, 6, 2, 4, 2, 1e-3)
    scaled_threshold, scaled_testable, scaled_detection = apply_cfar(
        [[4 * value for value in row] for row in power], 6, 2, 4, 2, 1e-3
    )
    return {
        "power": power,
        "threshold": threshold,
        "testable": testable,
        "detection": detection,
        "scaled_threshold": scaled_threshold,
        "scaled_testable": scaled_testable,
        "scaled_detection": scaled_detection,
        "target_rows": target_rows,
        "target_columns": target_columns,
    }


class P50ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self):
        self.assertEqual(validate_p50_contract(MODULE, self.manifest), [])
        p49 = next(item for item in self.manifest["modules"] if item["id"] == "P49")
        self.assertEqual(p49["status"], "implemented")
        for name in ARTIFACTS:
            with self.subTest(artifact=name):
                data = (MODULE / name).read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))
                self.assertNotIn(b"\r", data)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            for name in ARTIFACTS:
                shutil.copy2(MODULE / name, fixture / name)
            (fixture / "checks.md").unlink()
            self.assertIn("P50 missing checks.md", validate_p50_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("\n", encoding="utf-8")
            self.assertIn("P50 empty checks.md", validate_p50_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p50_contract(MODULE, {}))
        self.assertIn("manifest module entries must be objects", validate_p50_contract(MODULE, {"modules": ["P50"]}))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P50 manifest entry, found 2", validate_p50_contract(MODULE, duplicate))
        for key, expected in EXPECTED_IDENTITY.items():
            drifted = copy.deepcopy(self.manifest)
            next(item for item in drifted["modules"] if item["id"] == "P50")[key] = f"wrong-{expected}"
            self.assertTrue(validate_p50_contract(MODULE, drifted))

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self):
        validate_controls()
        invalid = (
            {"unexpected": 1},
            {"seed": True},
            {"seed": 5002},
            {"range_bins": 129},
            {"doppler_bins": 63},
            {"range_spacing": math.nan},
            {"velocity_spacing": 0.0},
            {"pfa": 0.0},
            {"pfa": 0.2},
            {"tr": 0},
            {"gr": 17},
            {"td": 2.5},
            {"range_sweep": (3, 12, 6)},
            {"range_sweep": (3, 7, 12)},
            {"range_sweep": (3, 6, 12, 15, 16)},
            {"doppler_sweep": (2, math.inf, 8)},
            {"doppler_sweep": (2, 4, 17)},
            {"target_rows": (28, 53, 97, 4)},
            {"target_columns": (45, 22, 35)},
            {"target_snr_db": (24.0, 20.0, 18.0, 41.0)},
            {"max_range_bins": 127},
            {"max_figures": 7},
            {"max_stored": 399_999},
            {"max_visits": 29_000_000},
            {"range_bins": 32, "range_sweep": (6, 12, 16)},
            {"doppler_bins": 32, "doppler_sweep": (4, 8, 16)},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                validate_controls(**overrides)

    def test_geometry_calibration_edges_and_malformed_oracle_inputs(self):
        offsets = stencil_offsets(6, 2, 4, 2)
        self.assertEqual(len(offsets), 17 * 13 - 5 * 5)
        self.assertNotIn((0, 0), offsets)
        self.assertNotIn((2, 2), offsets)
        self.assertIn((3, 3), offsets)
        self.assertIn((8, 6), offsets)
        alpha = ca_alpha(len(offsets), 1e-3)
        self.assertAlmostEqual((1 + alpha / len(offsets)) ** (-len(offsets)), 1e-3, places=14)
        self.assertAlmostEqual(alpha, 7.030925258328118, places=12)
        for malformed in ((0, 1e-3), (True, 1e-3), (196, 0.0), (196, math.nan)):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                ca_alpha(*malformed)
        with self.assertRaises(ValueError):
            apply_cfar([], 6, 2, 4, 2, 1e-3)
        with self.assertRaises(ValueError):
            apply_cfar([[1.0, math.nan]], 1, 1, 1, 1, 1e-3)
        with self.assertRaises(ValueError):
            apply_cfar([[1.0] * 10 for _ in range(10)], 6, 2, 4, 2, 1e-3)

    def test_independent_oracle_detects_interior_targets_excludes_border_and_scales(self):
        oracle = independent_scene_oracle()
        testable = oracle["testable"]
        detection = oracle["detection"]
        threshold = oracle["threshold"]
        target_rows = oracle["target_rows"]
        target_columns = oracle["target_columns"]
        self.assertEqual(sum(sum(row) for row in testable), (96 - 16) * (64 - 12))
        for row, column in zip(target_rows[:3], target_columns[:3]):
            self.assertTrue(testable[row][column])
            self.assertTrue(detection[row][column])
        self.assertFalse(testable[target_rows[3]][target_columns[3]])
        self.assertFalse(detection[target_rows[3]][target_columns[3]])
        self.assertTrue(all(math.isnan(threshold[0][column]) for column in range(64)))
        self.assertEqual(oracle["scaled_testable"], testable)
        self.assertEqual(oracle["scaled_detection"], detection)
        for row in range(8, 88):
            for column in range(6, 58):
                self.assertAlmostEqual(oracle["scaled_threshold"][row][column], 4 * threshold[row][column], places=11)

    def test_zero_padding_invents_edge_detection_and_complete_stencil_recovers_baseline(self):
        rows, columns = 24, 20
        power = [[1.0] * columns for _ in range(rows)]
        power[0][0] = 3.0
        baseline_threshold, testable, baseline_detection = apply_cfar(
            power, 6, 2, 4, 2, 1e-3
        )
        broken_threshold, broken_detection = apply_zero_padded_cfar(
            power, 6, 2, 4, 2, 1e-3
        )

        full_reference_threshold = ca_alpha(len(stencil_offsets(6, 2, 4, 2)), 1e-3)
        self.assertFalse(testable[0][0])
        self.assertLess(broken_threshold[0][0], full_reference_threshold)
        self.assertTrue(broken_detection[0][0])
        self.assertGreater(
            sum(
                broken_detection[row][column] and not testable[row][column]
                for row in range(rows)
                for column in range(columns)
            ),
            0,
        )

        recovered_threshold = [
            [broken_threshold[row][column] if testable[row][column] else math.nan for column in range(columns)]
            for row in range(rows)
        ]
        recovered_detection = [
            [testable[row][column] and broken_detection[row][column] for column in range(columns)]
            for row in range(rows)
        ]
        self.assertEqual(recovered_detection, baseline_detection)
        for row in range(rows):
            for column in range(columns):
                if testable[row][column]:
                    self.assertAlmostEqual(
                        recovered_threshold[row][column], baseline_threshold[row][column]
                    )
                else:
                    self.assertTrue(math.isnan(recovered_threshold[row][column]))

    def test_sweep_geometry_changes_only_the_selected_axis(self):
        range_counts = [len(stencil_offsets(value, 2, 4, 2)) for value in (3, 6, 12)]
        range_valid_shapes = [(96 - 2 * (value + 2), 64 - 2 * (4 + 2)) for value in (3, 6, 12)]
        doppler_counts = [len(stencil_offsets(6, 2, value, 2)) for value in (2, 4, 8)]
        doppler_valid_shapes = [(96 - 2 * (6 + 2), 64 - 2 * (value + 2)) for value in (2, 4, 8)]
        self.assertEqual(range_counts, [118, 196, 352])
        self.assertEqual(range_valid_shapes, [(86, 52), (80, 52), (68, 52)])
        self.assertEqual(doppler_counts, [128, 196, 332])
        self.assertEqual(doppler_valid_shapes, [(80, 56), (80, 52), (80, 44)])
        self.assertTrue(all(a < b for a, b in zip(range_counts, range_counts[1:])))
        self.assertTrue(all(a < b for a, b in zip(doppler_counts, doppler_counts[1:])))

    def test_source_is_seeded_transparent_bounded_and_mutation_sensitive(self):
        self.assertEqual(source_contract_errors(self.source), [])
        controls_end = self.source.index("%% Build a compact square-law range-Doppler map")
        first_allocation = self.source.index("range_axis_m =")
        self.assertLess(controls_end, first_allocation)
        self.assertIn("estimated_stored_numeric_values", self.source[:controls_end])
        self.assertIn("estimated_training_sample_visits", self.source[:controls_end])
        self.assertIn("~islogical", self.source[:controls_end])
        self.assertEqual(self.source.count("figure('Name'"), 6)
        self.assertNotRegex(
            self.source.lower(),
            r"\b(?:phased\.|cfardetector\w*|conv2\s*\(|filter2\s*\(|ordfilt\w*\s*\(|"
            r"awgn\s*\(|parfor\b|while\b|fopen\s*\(|webread\s*\(|system\s*\(|"
            r"timer\s*\(|rng\s*\()",
        )
        for marker in (
            "training_mask(guard_rows, guard_columns) = false;",
            "training_cell_count = sum(training_mask(:));",
            "training_power = local_power(training_mask);",
            "range_training_sweep = [3 6 12];",
            "doppler_training_sweep = [2 4 8];",
            "broken_all_cells_calibrated_claim_is_valid = false;",
            "recovered_threshold(border_mask) = NaN;",
        ):
            mutated = self.source.replace(marker, "mutated", 1)
            self.assertTrue(source_contract_errors(mutated), marker)

    def test_docs_cover_model_sweeps_failure_recovery_limits_and_teach_back(self):
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        combined = "\n".join((readme, lesson, walkthrough, checks))
        normalized = re.sub(r"\s+", " ", combined)
        for phrase in (
            QUESTION,
            "rectangular annulus",
            "linear square-law power",
            "range training half-width",
            "Doppler training half-width",
            "Expected observation",
            "intentionally broken",
            "Recovery",
            "Ctrl+C",
            "Short teach-back rubric",
            "no calibrated test",
            "P42",
            "P45",
            "P49",
            "P51",
            "P52",
        ):
            self.assertIn(phrase, normalized)
        self.assertNotRegex(combined, r"(?i)TODO|coming soon|placeholder")
        self.assertLess(lesson.index("Start with the physical window"), lesson.index("explicit 2-D CA-CFAR operation"))

    def _run_fixture_cli(self, manifest: dict, *args: str, initial_state=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        fixture_root = Path(temporary.name) / "repo"
        fixture_cli = fixture_root / "bin/learn"
        fixture_manifest = fixture_root / "curriculum/modules.json"
        fixture_cli.parent.mkdir(parents=True)
        fixture_manifest.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", fixture_cli)
        fixture_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        for module in manifest["modules"]:
            source_readme = ROOT / module["folder"] / "README.md"
            target_readme = fixture_root / module["folder"] / "README.md"
            target_readme.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_readme, target_readme)
        if initial_state is not None:
            state_path = fixture_root / ".learning/progress.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps(initial_state, indent=2) + "\n", encoding="utf-8")
        env = os.environ.copy()
        env["HOME"] = temporary.name
        process = subprocess.run(
            [str(fixture_cli), *args],
            cwd=fixture_root,
            text=True,
            capture_output=True,
            env=env,
            timeout=10,
            check=False,
        )
        state_path = fixture_root / ".learning/progress.json"
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
        return process, state

    def test_isolated_cli_timeout_cancellation_and_scaffold_rollback_compatibility(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        process, state = self._run_fixture_cli(self.manifest, "start", "50")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("P50 — Apply 2-D CFAR to a Range-Doppler Map", process.stdout)
        self.assertIn("status: implemented", process.stdout)
        self.assertEqual(state["current"], "P50")
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        self.assertIn("Ctrl+C", walkthrough)
        self.assertIn("Rerun from the top", walkthrough)

        rolled = copy.deepcopy(self.manifest)
        next(item for item in rolled["modules"] if item["id"] == "P50")["status"] = "scaffolded"
        rolled_process, _ = self._run_fixture_cli(rolled, "start", "50")
        self.assertEqual(rolled_process.returncode, 3)
        self.assertIn("awaits Portfolio batch P50", rolled_process.stdout)

    def test_default_tutor_entry_advances_from_completed_p49_without_state_loss(self):
        prior_completed = [f"P{number:02d}" for number in range(1, 50)]
        initial = {
            "schema_version": 1,
            "current": "P49",
            "completed": prior_completed,
            "notes": {"P49": "preserve this ordered-statistic teach-back"},
        }
        process, state = self._run_fixture_cli(self.manifest, "start", initial_state=initial)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("P50 — Apply 2-D CFAR", process.stdout)
        self.assertEqual(state["current"], "P50")
        self.assertEqual(state["completed"], prior_completed)
        self.assertEqual(state["notes"], initial["notes"])

    def test_p50_only_rollback_preserves_neighbor_identity(self):
        rolled = copy.deepcopy(self.manifest)
        neighbors_before = {
            item["id"]: copy.deepcopy(item)
            for item in rolled["modules"]
            if item["id"] in {"P49", "P51"}
        }
        next(item for item in rolled["modules"] if item["id"] == "P50")["status"] = "scaffolded"
        neighbors_after = {
            item["id"]: item for item in rolled["modules"] if item["id"] in {"P49", "P51"}
        }
        self.assertEqual(neighbors_after, neighbors_before)
        self.assertTrue(any("status" in error for error in validate_p50_contract(MODULE, rolled)))

    def test_public_catalogs_describe_p50_without_freezing_future_state(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 50 slides an explicit rectangular CA-CFAR annulus", readme)
        self.assertIn("Project 50 follows P49", start_here)
        self.assertRegex(module_index, r"\| \[P50\].*\| implemented \| 5 \|")
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?i)P50\s+(?:is\s+)?(?:the\s+)?(?:latest|last|final)")
        self.assertNotRegex(source, r"(?i)P51[^\n]*remains? scaffolded")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self):
        evidence = ROOT / "docs/evidence/P50-2026-08-04.md"
        self.assertTrue(evidence.is_file())
        text = evidence.read_text(encoding="utf-8")
        for heading in (
            "## Outcome and claim boundary",
            "## Acceptance mapping",
            "## Physical model and independent static oracle",
            "## Figure and metric inventory",
            "## Focused test coverage",
            "## Exact commands and results",
            "## Changed and preserved invariants",
            "## Rollback and recovery",
            "## Residual risks and unperformed validation",
        ):
            self.assertIn(heading, text)
        for command in (
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
            "python3 -m unittest tests.test_p50_module -v",
        ):
            self.assertIn(command, text)
        self.assertIn("MATLAB and Octave did not run", text)
        self.assertIn("allowed-path audit", text)
        self.assertIn("pre-existing", text)
        data = evidence.read_bytes()
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))
        self.assertNotIn(b"\r", data)


if __name__ == "__main__":
    unittest.main()
