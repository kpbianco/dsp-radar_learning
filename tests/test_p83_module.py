from __future__ import annotations

import cmath
import copy
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/83-compare-range-doppler-processing-with-a-small-stap-processor"
MANIFEST = ROOT / "curriculum/modules.json"
CLI = ROOT / "bin/learn"
EVIDENCE = ROOT / "docs/evidence/P83-2026-08-14.md"
QUESTION = "When is Doppler filtering alone insufficient against clutter?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")

BASE_CONTROLS = {
    "seed": 8301,
    "elements": 4,
    "pulses": 8,
    "range_cells": 48,
    "target_range_cell": 25,
    "guard_cells": 2,
    "training_indices": [*range(5, 23), *range(28, 46)],
    "spacing": 0.5,
    "wavelength_m": 0.03,
    "prf_hz": 20_000.0,
    "platform_speed_mps": 90.0,
    "clutter_angles": list(range(-60, 61, 3)),
    "clutter_power_db": 32.0,
    "noise_power": 1.0,
    "target_power_db": 18.0,
    "assumed_angle": 12.0,
    "actual_angle": 12.5,
    "assumed_doppler": 0.120,
    "actual_doppler": 0.125,
    "doppler_grid": [value / 100 for value in range(-25, 26)],
    "loading_alpha": 0.05,
    "ridge_sweep": [0.01, 0.03, 0.06, 0.10],
    "support_sweep": [8, 16, 24, 36],
    "contamination_fraction": 0.25,
    "contamination_power_db": 30.0,
    "display_floor_db": -20.0,
    "display_ceiling_db": 35.0,
    "max_elements": 6,
    "max_pulses": 12,
    "max_dimension": 72,
    "max_range_cells": 64,
    "max_patches": 61,
    "max_doppler_cells": 81,
    "max_training": 48,
    "max_sweeps": 5,
    "max_maps": 4,
    "max_solves": 200,
    "max_macs": 8_000_000,
    "max_private": 100_000,
    "max_working": 250_000,
    "max_figures": 5,
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


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


def controls_errors(c: object) -> list[str]:
    if not isinstance(c, dict) or set(c) != set(BASE_CONTROLS):
        return ["control fields"]
    errors: list[str] = []
    vectors = {
        "training_indices", "clutter_angles", "doppler_grid",
        "ridge_sweep", "support_sweep",
    }
    integers = {
        "seed", "elements", "pulses", "range_cells", "target_range_cell",
        "guard_cells", "training_indices", "support_sweep", "max_elements",
        "max_pulses", "max_dimension", "max_range_cells", "max_patches",
        "max_doppler_cells", "max_training", "max_sweeps", "max_maps",
        "max_solves", "max_macs", "max_private", "max_working", "max_figures",
    }
    for name, value in c.items():
        values = value if name in vectors and isinstance(value, list) else [value]
        if name in vectors and (not isinstance(value, list) or not value):
            errors.append(f"{name} vector")
            continue
        if not all(finite_real(item) for item in values):
            errors.append(f"{name} finite")
        if name in integers and any(
            finite_real(item) and (item != math.floor(item) or item < 0)
            for item in values
        ):
            errors.append(f"{name} integer")
    if errors:
        return errors

    dimension = c["elements"] * c["pulses"]
    denominator = c["wavelength_m"] * c["prf_hz"]
    slope = (
        2 * c["platform_speed_mps"] / denominator
        if denominator > 0 else math.inf
    )
    if not 1 <= c["seed"] <= 2_147_483_644:
        errors.append("seed range")
    if not (
        2 <= c["elements"] <= c["max_elements"]
        and 2 <= c["pulses"] <= c["max_pulses"]
        and dimension <= c["max_dimension"]
    ):
        errors.append("dimension bound")
    if not (
        c["range_cells"] <= c["max_range_cells"]
        and 1 <= c["target_range_cell"] <= c["range_cells"]
        and c["guard_cells"] >= 1
    ):
        errors.append("range bound")
    if not (
        5 <= len(c["clutter_angles"]) <= c["max_patches"]
        and all(right > left for left, right in zip(c["clutter_angles"], c["clutter_angles"][1:]))
        and all(abs(value) < 90 for value in c["clutter_angles"])
    ):
        errors.append("clutter grid")
    if not (
        5 <= len(c["doppler_grid"]) <= c["max_doppler_cells"]
        and all(right > left for left, right in zip(c["doppler_grid"], c["doppler_grid"][1:]))
        and c["doppler_grid"][0] > -0.5
        and c["doppler_grid"][-1] < 0.5
        and any(abs(value - c["assumed_doppler"]) < 1e-12 for value in c["doppler_grid"])
    ):
        errors.append("Doppler grid")
    if not (
        0 < c["spacing"] <= 0.5
        and c["wavelength_m"] > 0
        and c["prf_hz"] > 0
        and c["platform_speed_mps"] > 0
        and 0 < slope < 0.5
    ):
        errors.append("physical controls")
    if not (
        0 < c["noise_power"] <= 1e6
        and abs(c["clutter_power_db"]) <= 80
        and abs(c["target_power_db"]) <= 80
        and c["target_power_db"] <= c["contamination_power_db"] <= 80
    ):
        errors.append("power controls")
    if not (
        abs(c["assumed_angle"]) < 90
        and abs(c["actual_angle"]) < 90
        and abs(c["actual_angle"] - c["assumed_angle"]) <= 2
        and c["doppler_grid"][0] < c["actual_doppler"] < c["doppler_grid"][-1]
        and abs(c["actual_doppler"] - c["assumed_doppler"]) <= 0.02
    ):
        errors.append("target controls")
    if not 0 < c["loading_alpha"] <= 1:
        errors.append("loading control")
    training = c["training_indices"]
    if not (
        dimension <= len(training) <= c["max_training"]
        and all(right > left for left, right in zip(training, training[1:]))
        and training[0] >= 1
        and training[-1] <= c["range_cells"]
        and all(abs(value - c["target_range_cell"]) > c["guard_cells"] for value in training)
    ):
        errors.append("training controls")
    if not (
        3 <= len(c["ridge_sweep"]) <= c["max_sweeps"]
        and all(right > left for left, right in zip(c["ridge_sweep"], c["ridge_sweep"][1:]))
        and c["ridge_sweep"][0] > 0
        and slope * math.sin(math.radians(c["actual_angle"])) + c["ridge_sweep"][-1] < 0.5
    ):
        errors.append("ridge sweep")
    if not (
        3 <= len(c["support_sweep"]) <= c["max_sweeps"]
        and all(right > left for left, right in zip(c["support_sweep"], c["support_sweep"][1:]))
        and c["support_sweep"][0] >= 2
        and c["support_sweep"][-1] == len(training)
    ):
        errors.append("support sweep")
    if not 0 < c["contamination_fraction"] <= 0.5:
        errors.append("contamination")
    if not c["display_floor_db"] < 0 < c["display_ceiling_db"]:
        errors.append("display controls")
    immutable = {
        "max_maps": 4, "max_solves": 200, "max_macs": 8_000_000,
        "max_private": 100_000, "max_working": 250_000, "max_figures": 5,
    }
    if any(c[name] != value for name, value in immutable.items()):
        errors.append("immutable ceilings")

    maps = 4
    solves = 3 * len(c["doppler_grid"]) + len(c["ridge_sweep"]) + len(c["support_sweep"])
    macs = (
        solves * dimension**3
        + maps * len(c["doppler_grid"]) * c["range_cells"] * dimension
        + 4 * dimension**2 * len(training)
        + dimension * len(c["clutter_angles"]) * c["range_cells"]
    )
    working = (
        2 * dimension * len(c["clutter_angles"])
        + 6 * dimension * c["range_cells"]
        + 8 * dimension**2
        + maps * len(c["doppler_grid"]) * c["range_cells"]
        + 1000
    )
    private = 2 * max(len(c["clutter_angles"]) * c["range_cells"], dimension * c["range_cells"])
    if maps > c["max_maps"] or solves > c["max_solves"] or macs > c["max_macs"]:
        errors.append("compute resource")
    if working > c["max_working"] or private > c["max_private"]:
        errors.append("storage resource")
    return errors


def private_complex_noise(seed: int, rows: int, columns: int, maximum: int = 100_000) -> list[list[complex]]:
    if isinstance(seed, bool) or not isinstance(seed, int) or not 1 <= seed < 2_147_483_647:
        raise ValueError("seed")
    if (
        isinstance(rows, bool) or isinstance(columns, bool)
        or not isinstance(rows, int) or not isinstance(columns, int)
        or rows < 1 or columns < 1 or 2 * rows * columns > maximum
    ):
        raise ValueError("shape")
    count = rows * columns
    state = seed
    uniforms: list[float] = []
    for _ in range(2 * count):
        state = (16_807 * state) % 2_147_483_647
        uniforms.append(state / 2_147_483_647)
    samples = [
        math.sqrt(-2 * math.log(max(uniforms[index], float.fromhex("0x0.0000000000001p-1022"))))
        * cmath.exp(2j * math.pi * uniforms[count + index]) / math.sqrt(2)
        for index in range(count)
    ]
    return [
        [samples[column * rows + row] for column in range(columns)]
        for row in range(rows)
    ]


def steering(angle_deg: float, normalized_doppler: float, elements: int = 4, pulses: int = 8) -> list[complex]:
    spatial = [
        cmath.exp(2j * math.pi * 0.5 * index * math.sin(math.radians(angle_deg)))
        for index in range(elements)
    ]
    slow_time = [cmath.exp(2j * math.pi * index * normalized_doppler) for index in range(pulses)]
    return [pulse * element for pulse in slow_time for element in spatial]


def dot(left: list[complex], right: list[complex]) -> complex:
    return sum(value.conjugate() * other for value, other in zip(left, right))


def matvec(matrix: list[list[complex]], vector: list[complex]) -> list[complex]:
    return [sum(value * coefficient for value, coefficient in zip(row, vector)) for row in matrix]


def solve(matrix: list[list[complex]], vector: list[complex]) -> list[complex]:
    size = len(vector)
    work = [list(row) + [value] for row, value in zip(matrix, vector)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) < 1e-13:
            raise ValueError("singular")
        work[column], work[pivot] = work[pivot], work[column]
        divisor = work[column][column]
        work[column] = [value / divisor for value in work[column]]
        for row in range(size):
            if row == column:
                continue
            factor = work[row][column]
            work[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(work[row], work[column])
            ]
    return [work[row][-1] for row in range(size)]


def covariance(data: list[list[complex]]) -> list[list[complex]]:
    columns = len(data[0])
    return [
        [
            sum(data[row][look] * data[column][look].conjugate() for look in range(columns)) / columns
            for column in range(len(data))
        ]
        for row in range(len(data))
    ]


def loaded(covariance_matrix: list[list[complex]], alpha: float = 0.05) -> list[list[complex]]:
    dimension = len(covariance_matrix)
    loading = alpha * sum(covariance_matrix[index][index].real for index in range(dimension)) / dimension
    return [
        [value + (loading if row == column else 0) for column, value in enumerate(line)]
        for row, line in enumerate(covariance_matrix)
    ]


def loaded_solution(covariance_matrix: list[list[complex]], look: list[complex]) -> tuple[list[complex], list[complex]]:
    solution = solve(loaded(covariance_matrix), look)
    denominator = dot(look, solution)
    return solution, [value / denominator for value in solution]


def quadratic(weight: list[complex], matrix: list[list[complex]]) -> float:
    return dot(weight, matvec(matrix, weight)).real


def output_scnr_db(weight: list[complex], actual: list[complex], target_power: float, interference: list[list[complex]]) -> float:
    return 10 * math.log10(target_power * abs(dot(weight, actual)) ** 2 / quadratic(weight, interference))


def exact_oracle() -> dict[str, object]:
    elements, pulses, dimension, range_cells = 4, 8, 32, 48
    angles = [float(value) for value in range(-60, 61, 3)]
    slope = 0.30
    dopplers = [slope * math.sin(math.radians(angle)) for angle in angles]
    shapes = [math.cos(math.radians(angle)) ** 2 for angle in angles]
    total_clutter = 10 ** (32 / 10)
    powers = [total_clutter * value / sum(shapes) for value in shapes]
    clutter_vectors = [steering(angle, doppler) for angle, doppler in zip(angles, dopplers)]
    interference = [
        [1 + 0j if row == column else 0j for column in range(dimension)]
        for row in range(dimension)
    ]
    for vector, power in zip(clutter_vectors, powers):
        for row in range(dimension):
            for column in range(dimension):
                interference[row][column] += power * vector[row] * vector[column].conjugate()

    coefficients = private_complex_noise(8301, len(angles), range_cells)
    thermal = private_complex_noise(8302, dimension, range_cells)
    background = [
        [
            sum(
                math.sqrt(powers[patch]) * clutter_vectors[patch][row] * coefficients[patch][cell]
                for patch in range(len(angles))
            ) + thermal[row][cell]
            for cell in range(range_cells)
        ]
        for row in range(dimension)
    ]
    training_indices = [*range(4, 22), *range(27, 45)]
    training = [[row[index] for index in training_indices] for row in background]
    clean_covariance = covariance(training)
    clean_loaded = loaded(clean_covariance)
    actual = steering(12.5, 0.125)
    assumed = steering(12.0, 0.120)
    target_power = 10 ** (18 / 10)
    measurement = [list(row) for row in background]
    for row in range(dimension):
        measurement[row][24] += math.sqrt(target_power) * actual[row]

    conventional = [value / dot(assumed, assumed) for value in assumed]
    _, clean_weight = loaded_solution(clean_covariance, assumed)
    conventional_scnr = output_scnr_db(conventional, actual, target_power, interference)
    stap_scnr = output_scnr_db(clean_weight, actual, target_power, interference)

    grid = [value / 100 for value in range(-25, 26)]
    conventional_map: list[list[float]] = []
    adaptive_map: list[list[float]] = []
    for trial_doppler in grid:
        look = steering(12.0, trial_doppler)
        fixed = [value / dot(look, look) for value in look]
        fixed_normalization = quadratic(fixed, clean_loaded)
        conventional_map.append([
            abs(dot(fixed, [measurement[row][cell] for row in range(dimension)])) ** 2 / fixed_normalization
            for cell in range(range_cells)
        ])
        solution, _ = loaded_solution(clean_covariance, look)
        normalization = dot(look, solution).real
        adaptive_map.append([
            abs(dot(solution, [measurement[row][cell] for row in range(dimension)])) ** 2 / normalization
            for cell in range(range_cells)
        ])

    target_doppler_index = 37
    background_coordinates = [
        (doppler_index, cell)
        for doppler_index in range(len(grid))
        for cell in range(range_cells)
        if not (36 <= doppler_index <= 38 and 22 <= cell <= 26)
    ]
    conventional_background = statistics.median(
        conventional_map[doppler][cell] for doppler, cell in background_coordinates
    )
    adaptive_background = statistics.median(
        adaptive_map[doppler][cell] for doppler, cell in background_coordinates
    )
    conventional_contrast = 10 * math.log10(conventional_map[37][24] / conventional_background)
    adaptive_contrast = 10 * math.log10(adaptive_map[37][24] / adaptive_background)
    adaptive_peak = max(
        (value, doppler, cell)
        for doppler, row in enumerate(adaptive_map)
        for cell, value in enumerate(row)
    )[1:]
    conventional_peak = max(
        (value, doppler, cell)
        for doppler, row in enumerate(conventional_map)
        for cell, value in enumerate(row)
    )[1:]

    ridge_conventional: list[float] = []
    ridge_adaptive: list[float] = []
    local_ridge = slope * math.sin(math.radians(12.5))
    for offset in (0.01, 0.03, 0.06, 0.10):
        case = steering(12.5, local_ridge + offset)
        fixed = [value / dot(case, case) for value in case]
        _, joint = loaded_solution(clean_covariance, case)
        ridge_conventional.append(output_scnr_db(fixed, case, target_power, interference))
        ridge_adaptive.append(output_scnr_db(joint, case, target_power, interference))

    support_scnr: list[float] = []
    for support in (8, 16, 24, 36):
        prefix = [row[:support] for row in training]
        _, weight = loaded_solution(covariance(prefix), assumed)
        support_scnr.append(output_scnr_db(weight, actual, target_power, interference))

    contaminated = [list(row) for row in training]
    contamination = private_complex_noise(8303, 1, 36)[0]
    contaminated_count = 9
    contamination_voltage = math.sqrt(10 ** (30 / 10))
    for row in range(dimension):
        for cell in range(contaminated_count):
            contaminated[row][cell] += contamination_voltage * actual[row] * contamination[cell]
    broken_covariance = covariance(contaminated)
    _, broken_weight = loaded_solution(broken_covariance, assumed)
    broken_scnr = output_scnr_db(broken_weight, actual, target_power, interference)
    clean_target_output = target_power * abs(dot(clean_weight, actual)) ** 2
    broken_target_output = target_power * abs(dot(broken_weight, actual)) ** 2
    clean_interference_output = quadratic(clean_weight, interference)
    broken_interference_output = quadratic(broken_weight, interference)
    broken_target_output_change = 10 * math.log10(
        broken_target_output / clean_target_output
    )
    broken_interference_output_increase = 10 * math.log10(
        broken_interference_output / clean_interference_output
    )

    broken_map: list[list[float]] = []
    for trial_doppler in grid:
        look = steering(12.0, trial_doppler)
        solution, _ = loaded_solution(broken_covariance, look)
        normalization = dot(look, solution).real
        broken_map.append([
            abs(dot(solution, [measurement[row][cell] for row in range(dimension)])) ** 2 / normalization
            for cell in range(range_cells)
        ])
    broken_background = statistics.median(
        broken_map[doppler][cell] for doppler, cell in background_coordinates
    )
    broken_contrast = 10 * math.log10(broken_map[37][24] / broken_background)
    broken_peak = max(
        (value, doppler, cell)
        for doppler, row in enumerate(broken_map)
        for cell, value in enumerate(row)
    )[1:]
    return {
        "slope": slope,
        "conventional_scnr": conventional_scnr,
        "stap_scnr": stap_scnr,
        "conventional_contrast": conventional_contrast,
        "stap_contrast": adaptive_contrast,
        "conventional_peak": conventional_peak,
        "stap_peak": adaptive_peak,
        "ridge_conventional": ridge_conventional,
        "ridge_stap": ridge_adaptive,
        "support_scnr": support_scnr,
        "broken_scnr": broken_scnr,
        "clean_assumed_response": dot(clean_weight, assumed),
        "broken_assumed_response": dot(broken_weight, assumed),
        "broken_target_output_change": broken_target_output_change,
        "broken_interference_output_increase": broken_interference_output_increase,
        "broken_contrast": broken_contrast,
        "broken_peak": broken_peak,
        "clean_weight": clean_weight,
        "recovered_weight": loaded_solution(covariance(training), assumed)[1],
        "measurement_before": measurement,
        "measurement_after": [list(row) for row in measurement],
    }


class P83ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.oracle = exact_oracle()

    def make_fixture(self, base: Path, manifest: dict) -> Path:
        fixture = base / "repo"
        (fixture / "bin").mkdir(parents=True)
        (fixture / "curriculum").mkdir(parents=True)
        shutil.copy2(CLI, fixture / "bin/learn")
        (fixture / "curriculum/modules.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        for module in manifest["modules"]:
            readme = fixture / module["folder"] / "README.md"
            readme.parent.mkdir(parents=True, exist_ok=True)
            readme.write_text(f"# {module['id']}\n", encoding="utf-8")
        return fixture

    def run_fixture_cli(self, fixture: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(fixture.parent)
        return subprocess.run(
            [str(fixture / "bin/learn"), *args], cwd=fixture, text=True,
            capture_output=True, env=env, timeout=3,
        )

    def test_manifest_identity_artifacts_and_permanent_dependencies(self) -> None:
        prerequisite = self.manifest["modules"][81]
        module = self.manifest["modules"][82]
        successor = self.manifest["modules"][83]
        self.assertEqual(
            {key: module[key] for key in (
                "number", "id", "title", "guiding_question", "phase",
                "phase_title", "slug", "folder", "status", "implementation_batch",
            )},
            {
                "number": 83,
                "id": "P83",
                "title": "Compare Range-Doppler Processing with a Small STAP Processor",
                "guiding_question": QUESTION,
                "phase": 9,
                "phase_title": "SAR, ISAR, Passive Radar, and Capstone",
                "slug": "compare-range-doppler-processing-with-a-small-stap-processor",
                "folder": "modules/83-compare-range-doppler-processing-with-a-small-stap-processor",
                "status": "implemented",
                "implementation_batch": "P83",
            },
        )
        self.assertEqual((prerequisite["id"], prerequisite["status"]), ("P82", "implemented"))
        self.assertEqual(
            (successor["id"], successor["title"], successor["implementation_batch"]),
            ("P84", "Run the End-to-End Radar Processing Capstone", "P84"),
        )
        self.assertEqual(artifact_errors(MODULE), [])
        for name in ARTIFACTS:
            self.assertIn(QUESTION, (MODULE / name).read_text(encoding="utf-8"))

    def test_artifact_validation_rejects_missing_empty_and_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            self.assertEqual(artifact_errors(fixture), [])
            (fixture / "lesson.md").unlink()
            self.assertIn("missing lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("empty lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("PLACEHOLDER\n", encoding="utf-8")
            self.assertIn("placeholder remains in lesson.md", artifact_errors(fixture))

    def test_source_binds_model_sweeps_failure_recovery_and_bounds(self) -> None:
        markers = (
            "baseline_seed = 8301", "number_elements = 4", "number_pulses = 8",
            "number_range_cells = 48", "target_range_cell = 25",
            "training_indices = [5:22 28:45]", "normalized_clutter_slope = ...",
            "2*platform_speed_mps/(wavelength_m*prf_hz)",
            "clutter_normalized_doppler = ...", "kron(slow_time, space)",
            "clean_sample_covariance = clean_training_data*clean_training_data'/ ...",
            "range_doppler_weight = trial_steering/(trial_steering'*trial_steering)",
            "solution = loaded_covariance\\steering_vector", "weight = solution/denominator",
            "ridge_offset_sweep = [0.01 0.03 0.06 0.10]",
            "training_support_sweep = [8 16 24 36]",
            "contaminated_training_fraction = 0.25", "contamination_power_db = 30",
            "measurement_before_failure", "recovery_exact_match",
            "maximum_multiply_accumulates = 8000000",
            "maximum_working_numeric_values = 250000", "maximum_figures = 5",
            "P83:JointScnrImprovement", "P83:ConventionalFailure",
            "P83:RidgeSweep", "P83:SupportSweep", "P83:TrainingRecovery",
            "P83:ContaminationMechanism", "broken_target_output_change_db",
            "broken_interference_output_increase_db", "P83:ExactRecovery",
            "Clutter patch power / noise (dB)",
            "Normalized output power (dB)", "p83_results = struct( ...",
        )
        for marker in markers:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P83"), 5)
        self.assertEqual(self.source.count("'Tag', 'P83'"), 6)

    def test_source_has_no_opaque_toolbox_external_or_async_side_effect(self) -> None:
        executable = "\n".join(line.split("%", 1)[0] for line in self.source.lower().splitlines())
        for token in (
            "phased.", "phased.stap", "mvdrweights(", "steervec(", "inv(",
            "pinv(", "rng(", "rand(", "randn(", "parfor", "gpuarray",
            "batch(", "timer(", "fopen(", "save(", "writematrix", "webread",
            "urlread", "system(", "unix(", "delete(", "clear all", "close all",
            "xline(", "yline(",
        ):
            self.assertNotIn(token, executable)
        self.assertIsNone(re.search(r"(?m)^\s*!", executable))

    def test_control_contract_accepts_baseline_and_rejects_malformed_resources(self) -> None:
        self.assertEqual(controls_errors(copy.deepcopy(BASE_CONTROLS)), [])
        self.assertEqual(3 * 51 + 4 + 4, 161)
        self.assertEqual(
            161 * 32**3 + 4 * 51 * 48 * 32 + 4 * 32**2 * 36 + 32 * 41 * 48,
            5_799_424,
        )
        malformed_cases = (
            ("seed", True), ("seed", 0), ("elements", 1), ("pulses", 13),
            ("range_cells", 65), ("target_range_cell", 49), ("guard_cells", 0),
            ("spacing", 0.75), ("wavelength_m", 0), ("prf_hz", float("nan")),
            ("platform_speed_mps", 151), ("noise_power", 0),
            ("clutter_power_db", 81), ("actual_angle", 15),
            ("actual_doppler", 0.2), ("loading_alpha", 0),
            ("training_indices", [*range(5, 23), *range(27, 45)]),
            ("training_indices", [*range(5, 20)]),
            ("doppler_grid", [-0.5, 0, 0.12, 0.2, 0.3]),
            ("doppler_grid", [-0.25, 0, 0.1, 0.2, 0.25]),
            ("ridge_sweep", [0.01, 0.01, 0.10]),
            ("support_sweep", [8, 16, 24]),
            ("contamination_fraction", 0), ("contamination_power_db", 10),
            ("display_floor_db", 0), ("max_maps", 3), ("max_solves", 160),
            ("max_macs", 5_799_423), ("max_private", 100),
            ("max_working", 100), ("max_figures", 6),
        )
        for key, value in malformed_cases:
            with self.subTest(key=key, value=value):
                malformed = copy.deepcopy(BASE_CONTROLS)
                malformed[key] = value
                self.assertTrue(controls_errors(malformed))
        missing = copy.deepcopy(BASE_CONTROLS)
        missing.pop("seed")
        self.assertEqual(controls_errors(missing), ["control fields"])

    def test_private_generator_is_deterministic_bounded_and_isolated(self) -> None:
        first = private_complex_noise(8301, 4, 8)
        second = private_complex_noise(8301, 4, 8)
        different = private_complex_noise(8302, 4, 8)
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertAlmostEqual(first[0][0].real, -1.188824465679, places=10)
        self.assertAlmostEqual(first[0][0].imag, -1.149163597128, places=10)
        for args in ((True, 1, 1), (0, 1, 1), (8301, 0, 1), (8301, 1, 0), (8301, 100, 1000)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                private_complex_noise(*args)

    def test_steering_order_sign_and_limiting_geometry(self) -> None:
        vector = steering(30, 0.125, elements=2, pulses=3)
        spatial_step = cmath.exp(2j * math.pi * 0.5 * math.sin(math.radians(30)))
        doppler_step = cmath.exp(2j * math.pi * 0.125)
        expected = [1, spatial_step, doppler_step, doppler_step * spatial_step, doppler_step**2, doppler_step**2 * spatial_step]
        for actual, wanted in zip(vector, expected):
            self.assertAlmostEqual(abs(actual - wanted), 0, places=12)
        self.assertAlmostEqual(self.oracle["slope"], 0.30, places=12)
        self.assertAlmostEqual(
            0.30 * math.sin(math.radians(-30)),
            -0.30 * math.sin(math.radians(30)), places=12,
        )

    def test_independent_oracle_proves_baseline_joint_advantage_and_map_visibility(self) -> None:
        self.assertAlmostEqual(self.oracle["conventional_scnr"], -5.4322352407, places=7)
        self.assertAlmostEqual(self.oracle["stap_scnr"], 19.8249314039, places=7)
        self.assertGreater(self.oracle["stap_scnr"], self.oracle["conventional_scnr"] + 20)
        self.assertLess(self.oracle["conventional_contrast"], 1)
        self.assertGreater(self.oracle["stap_contrast"], 20)
        self.assertEqual(self.oracle["stap_peak"], (37, 24))
        self.assertNotEqual(self.oracle["conventional_peak"], (37, 24))

    def test_independent_oracle_exercises_both_one_variable_sweeps(self) -> None:
        fixed = self.oracle["ridge_conventional"]
        joint = self.oracle["ridge_stap"]
        support = self.oracle["support_scnr"]
        self.assertEqual(len(fixed), 4)
        self.assertEqual(len(joint), 4)
        self.assertGreater(joint[-1], joint[0] + 20)
        self.assertGreater((joint[-1] - fixed[-1]), 20)
        self.assertGreater(support[-1], support[0] + 10)
        self.assertTrue(all(math.isfinite(value) for value in [*fixed, *joint, *support]))

    def test_independent_oracle_exercises_broken_case_and_exact_recovery(self) -> None:
        self.assertLess(self.oracle["broken_scnr"], self.oracle["stap_scnr"] - 20)
        self.assertLess(self.oracle["broken_contrast"], 2)
        self.assertNotEqual(self.oracle["broken_peak"], (37, 24))
        for clean, recovered in zip(self.oracle["clean_weight"], self.oracle["recovered_weight"]):
            self.assertAlmostEqual(abs(clean - recovered), 0, places=12)
        self.assertEqual(self.oracle["measurement_before"], self.oracle["measurement_after"])

    def test_contamination_failure_is_interference_growth_not_target_self_null(self) -> None:
        self.assertAlmostEqual(
            abs(self.oracle["clean_assumed_response"] - 1), 0, places=12
        )
        self.assertAlmostEqual(
            abs(self.oracle["broken_assumed_response"] - 1), 0, places=12
        )
        self.assertAlmostEqual(
            self.oracle["broken_target_output_change"], -0.6152939520, places=7
        )
        self.assertAlmostEqual(
            self.oracle["broken_interference_output_increase"],
            22.8612946021,
            places=7,
        )
        self.assertGreater(self.oracle["broken_target_output_change"], -3)
        self.assertGreater(self.oracle["broken_interference_output_increase"], 20)

    def test_cli_timeout_rollback_recovery_isolation_and_later_status_compatibility(self) -> None:
        repository_state = ROOT / ".learning/progress.json"
        state_before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            current = copy.deepcopy(self.manifest)
            fixture = self.make_fixture(base, current)
            started = self.run_fixture_cli(fixture, "start", "83")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P83", started.stdout)
            self.assertIn("status: implemented", started.stdout)

            rolled_back = copy.deepcopy(current)
            rolled_back["modules"][82]["status"] = "scaffolded"
            rollback_fixture = self.make_fixture(base / "rollback", rolled_back)
            refused = self.run_fixture_cli(rollback_fixture, "start", "83")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P83", refused.stdout)
            fallback_state = rollback_fixture / ".learning/progress.json"
            fallback_state.parent.mkdir(parents=True, exist_ok=True)
            fallback_state.write_text(json.dumps({
                "schema_version": 1,
                "current": "P82",
                "completed": [f"P{number:02d}" for number in range(1, 83)],
                "notes": {},
            }) + "\n", encoding="utf-8")
            fallback = self.run_fixture_cli(rollback_fixture, "start")
            self.assertEqual(fallback.returncode, 0, fallback.stderr)
            self.assertIn("P82", fallback.stdout)

            later = copy.deepcopy(current)
            later["modules"][83]["status"] = "implemented"
            later["modules"][83]["future_metadata"] = {"compatible": True}
            later_fixture = self.make_fixture(base / "later", later)
            compatible = self.run_fixture_cli(later_fixture, "start", "83")
            self.assertEqual(compatible.returncode, 0, compatible.stderr)
            self.assertIn("P83", compatible.stdout)
        state_after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(state_after, state_before)

    def test_documents_cover_dependencies_limits_failure_cancellation_and_claims(self) -> None:
        combined = "\n".join(
            (MODULE / name).read_text(encoding="utf-8")
            for name in ("README.md", "lesson.md", "walkthrough.md", "checks.md")
        ).lower()
        for phrase in (
            "p82 is the governed", "p68", "fixed spatial beam", "kronecker",
            "already range-compressed", "diagonal loading", "target-like",
            "unchanged clean", "ctrl+c", "one array element", "one pulse",
            "doppler aliases", "range resolution", "no toolbox",
            "hardware/hil", "production evidence",
        ):
            self.assertIn(phrase, combined)
        self.assertNotRegex(combined, r"\b(?:todo|tbd|placeholder)\b")

    @unittest.skipUnless(shutil.which("matlab"), "MATLAB executable not available")
    def test_actual_matlab_runtime_when_available(self) -> None:
        matlab = shutil.which("matlab")
        command = (
            "rng_before=rng; run('experiment.m'); first=p83_results; rng_after=rng; "
            "assert(first.recovery_exact_match); assert(first.executed_map_count==4); "
            "assert(first.executed_linear_solve_count==161); "
            "assert(first.predicted_multiply_accumulates==5799424); "
            "assert(first.stap_peak(1)==25); assert(abs(first.stap_peak(2)-0.12)<1e-12); "
            "assert(first.stap_scnr_db>first.range_doppler_scnr_db+20); "
            "assert(first.broken_target_output_change_db>-3); "
            "assert(first.broken_interference_output_increase_db>20); "
            "assert(isequaln(rng_before,rng_after)); run('experiment.m'); "
            "assert(isequaln(first,p83_results)); assert(isequaln(rng_before,rng)); "
            "assert(numel(findall(0,'Type','figure','Tag','P83'))==5); "
            "close(findall(0,'Type','figure','Tag','P83'));"
        )
        wrapped = "try; set(0,'DefaultFigureVisible','off'); " + command + " exit(0); catch ME; disp(getReport(ME)); exit(1); end"
        completed = subprocess.run(
            [matlab, "-nosplash", "-nodesktop", "-nodisplay", "-r", wrapped],
            cwd=MODULE, text=True, capture_output=True, timeout=300,
        )
        self.assertEqual(
            completed.returncode, 0,
            f"MATLAB stdout:\n{completed.stdout}\nMATLAB stderr:\n{completed.stderr}",
        )

    def test_catalogs_evidence_and_exact_eof_policy(self) -> None:
        self.assertIn("Project 83 returns to moving-platform clutter", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn("Project 83 follows P82", (ROOT / "START_HERE.md").read_text(encoding="utf-8"))
        self.assertRegex(
            (ROOT / "modules/README.md").read_text(encoding="utf-8"),
            r"\| \[P83\].*\| implemented \|",
        )
        evidence = EVIDENCE.read_text(encoding="utf-8")
        for heading in (
            "## Claim boundary", "## Acceptance map", "## Deterministic simulated-oracle results",
            "## Figure and metric inventory", "## Exact commands and results",
            "## Changed and preserved invariants", "## Residual risks", "## Rollback",
            "## Unperformed validation",
        ):
            self.assertIn(heading, evidence)
        paths = [
            *[MODULE / name for name in ARTIFACTS], ROOT / "curriculum/modules.json",
            ROOT / "README.md", ROOT / "START_HERE.md", ROOT / "modules/README.md",
            Path(__file__), EVIDENCE,
        ]
        for path in paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
