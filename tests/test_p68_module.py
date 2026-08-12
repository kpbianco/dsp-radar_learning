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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/68-build-an-introductory-stap-clutter-ridge-experiment"
QUESTION = "How can space and slow time be processed together to suppress moving-platform clutter?"
EXPECTED_IDENTITY = {
    "number": 68,
    "id": "P68",
    "title": "Build an Introductory STAP Clutter-Ridge Experiment",
    "guiding_question": QUESTION,
    "phase": 7,
    "phase_title": "Arrays, Beamforming, DOA, and STAP",
    "slug": "build-an-introductory-stap-clutter-ridge-experiment",
    "folder": "modules/68-build-an-introductory-stap-clutter-ridge-experiment",
    "status": "implemented",
    "implementation_batch": "P68",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
SOURCE_MARKERS = (
    "baseline_seed = 6801;",
    "number_elements = 8;",
    "number_pulses = 8;",
    "wavelength_m = 0.03;",
    "prf_hz = 20000;",
    "platform_speed_mps = 105;",
    "clutter_angles_deg = -60:2:60;",
    "normalized_clutter_slope = ...",
    "2*platform_speed_mps/(wavelength_m*prf_hz);",
    "clutter_normalized_doppler = normalized_clutter_slope*sind(clutter_angles_deg);",
    "weighted_clutter_steering = clutter_steering.* ...",
    "interference_covariance = weighted_clutter_steering* ...",
    "actual_target_angle_deg = 10.7;",
    "actual_target_normalized_doppler = 0.208;",
    "number_training_cells = 128;",
    "training_data = weighted_clutter_steering*clutter_coefficients + ...",
    "joint_sample_covariance = training_data*training_data'/number_training_cells;",
    "cell_matrix.'*conj(cell_matrix)/(number_elements*number_training_cells);",
    "separable_weight = kron(doppler_weight, spatial_weight);",
    "joint_weight = loaded_mvdr(joint_sample_covariance, ...",
    "loading = alpha*real(trace(covariance_matrix))/dimension;",
    "solution = loaded_covariance\\steering_vector;",
    "weight = solution/denominator;",
    "training_support_sweep = [8 16 32 64 128];",
    "case_data = training_data(:, 1:support);",
    "contamination_fraction_sweep = [0 0.05 0.10 0.20 0.40];",
    "sqrt(contamination_power)*actual_target_steering* ...",
    "broken_training_data = training_data;",
    "recovered_weight = loaded_mvdr(joint_sample_covariance, ...",
    "norm(recovered_weight-joint_weight) < 1e-12",
    "'P68:JointImprovement'",
    "'P68:TrainingRecovery'",
    "maximum_space_time_dimension = 100;",
    "maximum_training_cells = 256;",
    "maximum_map_samples = 5000;",
    "maximum_private_values = 100000;",
    "maximum_working_numeric_values = 1000000;",
    "maximum_figures = 6;",
    "validate_controls(controls);",
    "'P68:PreflightWorkingBound'",
    "'P68:WorkingBound'",
    "state = mod(16807*state, 2147483647);",
    "samples = sqrt(-2*log(first)).*exp(1j*2*pi*second)/sqrt(2);",
    "noise = reshape(samples, number_rows, number_columns);",
    "p68_results = struct( ...",
    "close(findall(0, 'Type', 'figure', 'Tag', 'P68'));",
    "clear p68_results;",
)
FORBIDDEN_SOURCE_TOKENS = (
    "phased.", "phased.STAP", "stap", "mvdrweights(", "steervec(",
    "collectPlaneWave(", "awgn(", "inv(", "pinv(", "rng(", "rand(",
    "randn(", "parfor", "timer(", "webread", "urlread", "system(",
    "fopen(", "save(", "clear all", "clearvars", "delete(", "close all",
)
MODULUS = 2_147_483_647
MULTIPLIER = 16_807


def p68_source_errors(source: object) -> list[str]:
    if not isinstance(source, str) or not source:
        return ["P68 source must be nonempty text"]
    executable = "\n".join(line.split("%", 1)[0] for line in source.splitlines())
    errors = [f"missing source marker: {marker}" for marker in SOURCE_MARKERS if marker not in executable]
    if executable.count("figure('Name', 'P68") != 6:
        errors.append("P68 must create exactly six named figures")
    if executable.count("'Tag', 'P68'") != 7:
        errors.append("P68 must tag six figures and one scoped cleanup")
    errors.extend(f"forbidden source token: {token}" for token in FORBIDDEN_SOURCE_TOKENS if token in executable)
    if re.search(r"(?m)^\s*!", executable):
        errors.append("forbidden shell escape")
    return errors


def validate_p68_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P68 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [entry for entry in manifest["modules"] if isinstance(entry, dict) and entry.get("id") == "P68"]
    if len(matches) != 1:
        errors.append("P68 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P68 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P68 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P68 empty {artifact}")
    return errors


def reviewed_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "seed": 6801, "elements": 8, "pulses": 8, "spacing": 0.5,
        "wavelength": 0.03, "prf": 20000.0, "speed": 105.0,
        "clutter_angles": tuple(float(value) for value in range(-60, 61, 2)),
        "clutter_db": 30.0, "noise_power": 1.0, "target_db": 0.0,
        "assumed_angle": 10.0, "actual_angle": 10.7,
        "assumed_doppler": 0.2, "actual_doppler": 0.208,
        "training": 128, "loading": 0.03,
        "support": (8, 16, 32, 64, 128),
        "contamination": (0.0, 0.05, 0.10, 0.20, 0.40),
        "contamination_db": 20.0,
        "map_angles": tuple(float(value) for value in range(-60, 61, 2)),
        "map_doppler": tuple(-0.45 + 0.015 * index for index in range(61)),
        "plot_floor": -60.0, "max_elements": 10, "max_pulses": 10,
        "max_dimension": 100, "max_patches": 61, "max_training": 256,
        "max_map": 5000, "max_sweeps": 8, "max_private": 100000,
        "max_working": 1000000, "max_figures": 6,
    }
    controls.update(overrides)
    return controls


def finite_real(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_controls(c: object) -> None:
    if not isinstance(c, dict) or set(c) != set(reviewed_controls()):
        raise ValueError("controls")
    vectors = {"clutter_angles", "support", "contamination", "map_angles", "map_doppler"}
    if not all(finite_real(value) for key, value in c.items() if key not in vectors):
        raise ValueError("scalar")
    integers = {"seed", "elements", "pulses", "training", "max_elements", "max_pulses", "max_dimension", "max_patches", "max_training", "max_map", "max_sweeps", "max_private", "max_working", "max_figures"}
    if not all(c[name] > 0 and c[name] == int(c[name]) for name in integers):
        raise ValueError("integer")
    for name in vectors:
        values = c[name]
        if not isinstance(values, (tuple, list)) or not values or not all(finite_real(v) for v in values) or any(b <= a for a, b in zip(values, values[1:])):
            raise ValueError("vector")
    slope = 2 * c["speed"] / (c["wavelength"] * c["prf"])
    if not (
        c["elements"] <= c["max_elements"] and c["pulses"] <= c["max_pulses"]
        and c["elements"] * c["pulses"] <= c["max_dimension"]
        and 5 <= len(c["clutter_angles"]) <= c["max_patches"]
        and c["training"] <= c["max_training"]
        and len(c["map_angles"]) * len(c["map_doppler"]) <= c["max_map"]
        and 3 <= len(c["support"]) <= c["max_sweeps"]
        and all(value == int(value) for value in c["support"])
        and c["support"][0] >= 2 and c["support"][-1] == c["training"]
        and 3 <= len(c["contamination"]) <= c["max_sweeps"]
        and c["contamination"][0] == 0 and c["contamination"][-1] <= 0.5
        and 0 < c["spacing"] <= 0.5 and 0 < slope < 0.5
        and c["noise_power"] > 0 and 0 < c["loading"] <= 1
        and c["contamination_db"] >= c["target_db"] and c["contamination_db"] <= 60
        and c["wavelength"] > 0 and c["prf"] > 0 and c["speed"] > 0
        and c["noise_power"] <= 1e6
        and abs(c["clutter_db"]) <= 80 and abs(c["target_db"]) <= 80
        and -200 <= c["plot_floor"] <= -10
        and all(abs(angle) < 90 for angle in c["clutter_angles"])
        and all(abs(angle) < 90 for angle in c["map_angles"])
        and c["map_doppler"][0] > -0.5 and c["map_doppler"][-1] < 0.5
        and min(slope * math.sin(math.radians(angle)) for angle in c["clutter_angles"]) >= c["map_doppler"][0]
        and max(slope * math.sin(math.radians(angle)) for angle in c["clutter_angles"]) <= c["map_doppler"][-1]
        and c["map_angles"][0] <= c["clutter_angles"][0]
        and c["map_angles"][-1] >= c["clutter_angles"][-1]
        and c["map_angles"][0] < c["assumed_angle"] < c["map_angles"][-1]
        and c["map_angles"][0] < c["actual_angle"] < c["map_angles"][-1]
        and c["map_doppler"][0] < c["assumed_doppler"] < c["map_doppler"][-1]
        and c["map_doppler"][0] < c["actual_doppler"] < c["map_doppler"][-1]
        and abs(c["actual_angle"] - c["assumed_angle"]) <= 2
        and abs(c["actual_doppler"] - c["assumed_doppler"]) <= 0.02
        and abs(c["actual_doppler"] - slope * math.sin(math.radians(c["actual_angle"]))) >= 0.05
    ):
        raise ValueError("physical")
    immutable = {"max_elements": 10, "max_pulses": 10, "max_dimension": 100, "max_patches": 61, "max_training": 256, "max_map": 5000, "max_sweeps": 8, "max_private": 100000, "max_working": 1000000, "max_figures": 6}
    if any(c[name] != value for name, value in immutable.items()) or c["seed"] > MODULUS - 5:
        raise ValueError("ceiling")


def private_uniform(seed: object, count: object, maximum: int = 100000) -> tuple[float, ...]:
    if not finite_real(seed) or seed != int(seed) or not 1 <= seed < MODULUS:
        raise ValueError("seed")
    if not finite_real(count) or count != int(count) or not 1 <= count <= maximum:
        raise ValueError("count")
    state = int(seed)
    output = []
    for _ in range(int(count)):
        state = (MULTIPLIER * state) % MODULUS
        output.append(state / MODULUS)
    return tuple(output)


def private_complex_noise(seed: int, rows: int, columns: int) -> list[list[complex]]:
    count = rows * columns
    values = private_uniform(seed, 2 * count)
    samples = [
        math.sqrt(-2 * math.log(max(values[index], float.fromhex("0x0.0000000000001p-1022"))))
        * cmath.exp(1j * 2 * math.pi * values[count + index]) / math.sqrt(2)
        for index in range(count)
    ]
    return [[samples[column * rows + row] for column in range(columns)] for row in range(rows)]


def steering(angle: float, doppler: float, size: int = 6) -> list[complex]:
    spatial = [cmath.exp(1j * 2 * math.pi * 0.5 * index * math.sin(math.radians(angle))) for index in range(size)]
    slow = [cmath.exp(1j * 2 * math.pi * index * doppler) for index in range(size)]
    return [pulse * element for pulse in slow for element in spatial]


def outer(vector: list[complex]) -> list[list[complex]]:
    return [[left * right.conjugate() for right in vector] for left in vector]


def add_matrix(left: list[list[complex]], right: list[list[complex]], scale: float = 1.0) -> list[list[complex]]:
    return [[value + scale * other for value, other in zip(row, other_row)] for row, other_row in zip(left, right)]


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
            work[row] = [value - factor * pivot_value for value, pivot_value in zip(work[row], work[column])]
    return [work[row][-1] for row in range(size)]


def dot(left: list[complex], right: list[complex]) -> complex:
    return sum(a.conjugate() * b for a, b in zip(left, right))


def mvdr(covariance: list[list[complex]], look: list[complex], alpha: float = 0.03) -> list[complex]:
    size = len(look)
    average = sum(covariance[index][index].real for index in range(size)) / size
    loaded = [[value + (alpha * average if row == column else 0) for column, value in enumerate(line)] for row, line in enumerate(covariance)]
    solution = solve(loaded, look)
    denominator = dot(look, solution)
    return [value / denominator for value in solution]


def quadratic(weight: list[complex], matrix: list[list[complex]]) -> float:
    product = [sum(value * coefficient for value, coefficient in zip(row, weight)) for row in matrix]
    return dot(weight, product).real


def covariance(data: list[list[complex]]) -> list[list[complex]]:
    columns = len(data[0])
    return [[sum(data[row][look] * data[column][look].conjugate() for look in range(columns)) / columns for column in range(len(data))] for row in range(len(data))]


def scnr_db(weight: list[complex], actual: list[complex], interference: list[list[complex]]) -> float:
    return 10 * math.log10(abs(dot(weight, actual)) ** 2 / quadratic(weight, interference))


def exact_finite_record_results() -> tuple[float, float, tuple[float, ...], float]:
    elements = pulses = 8
    angles = [float(value) for value in range(-60, 61, 2)]
    dopplers = [0.35 * math.sin(math.radians(angle)) for angle in angles]
    shapes = [math.cos(math.radians(angle)) ** 2 for angle in angles]
    powers = [1000 * value / sum(shapes) for value in shapes]
    responses = [steering(angle, doppler, elements) for angle, doppler in zip(angles, dopplers)]
    dimension = elements * pulses
    interference = [[1 + 0j if row == column else 0j for column in range(dimension)] for row in range(dimension)]
    for response, power in zip(responses, powers):
        interference = add_matrix(interference, outer(response), power)
    coefficients = private_complex_noise(6801, len(angles), 128)
    noise = private_complex_noise(6802, dimension, 128)
    training = [[sum(math.sqrt(powers[patch]) * responses[patch][row] * coefficients[patch][look] for patch in range(len(angles))) + noise[row][look] for look in range(128)] for row in range(dimension)]
    nominal = steering(10.0, 0.2, elements)
    actual = steering(10.7, 0.208, elements)
    joint = mvdr(covariance(training), nominal)

    spatial_covariance = [[0j for _ in range(elements)] for _ in range(elements)]
    doppler_covariance = [[0j for _ in range(pulses)] for _ in range(pulses)]
    for look in range(128):
        cell = [[training[pulse * elements + element][look] for pulse in range(pulses)] for element in range(elements)]
        for row in range(elements):
            for column in range(elements):
                spatial_covariance[row][column] += sum(cell[row][pulse] * cell[column][pulse].conjugate() for pulse in range(pulses)) / (pulses * 128)
        for row in range(pulses):
            for column in range(pulses):
                doppler_covariance[row][column] += sum(cell[element][row] * cell[element][column].conjugate() for element in range(elements)) / (elements * 128)
    spatial_look = [cmath.exp(1j * 2 * math.pi * 0.5 * index * math.sin(math.radians(10.0))) for index in range(elements)]
    doppler_look = [cmath.exp(1j * 2 * math.pi * index * 0.2) for index in range(pulses)]
    separable = [pulse * element for pulse in mvdr(doppler_covariance, doppler_look) for element in mvdr(spatial_covariance, spatial_look)]
    support = tuple(scnr_db(mvdr(covariance([row[:count] for row in training]), nominal), actual, interference) for count in (8, 16, 32, 64, 128))
    waveform = private_complex_noise(6803, 1, 128)[0]
    contaminated = [list(row) for row in training]
    for row in range(dimension):
        for look in range(round(0.4 * 128)):
            contaminated[row][look] += 10 * actual[row] * waveform[look]
    broken = mvdr(covariance(contaminated), nominal)
    return scnr_db(separable, actual, interference), scnr_db(joint, actual, interference), support, scnr_db(broken, actual, interference)


def reviewed_covariance(size: int = 6) -> tuple[list[list[complex]], list[complex], list[complex], list[float], list[float]]:
    angles = [float(value) for value in range(-60, 61, 5)]
    dopplers = [0.35 * math.sin(math.radians(angle)) for angle in angles]
    shapes = [math.cos(math.radians(angle)) ** 2 for angle in angles]
    powers = [1000 * value / sum(shapes) for value in shapes]
    dimension = size * size
    covariance = [[1 + 0j if row == column else 0j for column in range(dimension)] for row in range(dimension)]
    for angle, doppler, power in zip(angles, dopplers, powers):
        covariance = add_matrix(covariance, outer(steering(angle, doppler, size)), power)
    return covariance, steering(10.0, 0.2, size), steering(10.7, 0.208, size), angles, dopplers


class P68ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")

    def make_fixture(self, base: Path, manifest: dict) -> Path:
        fixture = base / "repo"
        (fixture / "bin").mkdir(parents=True)
        (fixture / "curriculum").mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
        (fixture / "curriculum/modules.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        for module in manifest["modules"]:
            readme = fixture / module["folder"] / "README.md"
            readme.parent.mkdir(parents=True, exist_ok=True)
            readme.write_text(f"# {module['id']}\n", encoding="utf-8")
        return fixture

    def run_cli(self, fixture: Path, *args: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["HOME"] = str(fixture.parent)
        return subprocess.run([str(fixture / "bin/learn"), *args], cwd=fixture, env=environment, text=True, capture_output=True, timeout=10)

    def test_artifacts_manifest_identity_and_dependency_are_complete(self):
        self.assertEqual(validate_p68_contract(ROOT, self.manifest), [])
        p67 = next(module for module in self.manifest["modules"] if module["id"] == "P67")
        self.assertEqual(p67["status"], "implemented")

    def test_contract_rejects_malformed_duplicate_drift_missing_and_empty(self):
        self.assertTrue(validate_p68_contract(ROOT, None))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append(None)
        self.assertIn("every manifest module must be an object", validate_p68_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("P68 must have exactly one manifest entry", validate_p68_contract(ROOT, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(module for module in drifted["modules"] if module["id"] == "P68")["guiding_question"] = "changed"
        self.assertIn("P68 manifest identity drift", validate_p68_contract(ROOT, drifted))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(MODULE, root / EXPECTED_IDENTITY["folder"])
            (root / EXPECTED_IDENTITY["folder"] / "lesson.md").unlink()
            self.assertIn("P68 missing lesson.md", validate_p68_contract(root, self.manifest))
            (root / EXPECTED_IDENTITY["folder"] / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P68 empty lesson.md", validate_p68_contract(root, self.manifest))

    def test_source_exposes_model_sweeps_failure_recovery_and_bounds(self):
        self.assertEqual(p68_source_errors(self.source), [])
        for marker in SOURCE_MARKERS:
            with self.subTest(marker=marker):
                self.assertTrue(p68_source_errors(self.source.replace(marker, "removed")))
        for unsafe in ("\nphased.STAP", "\ninv(R)", "\nrng(1)", "\nparfor i=1:2", "\nsave('x.mat')", "\n!touch x"):
            with self.subTest(unsafe=unsafe):
                self.assertTrue(p68_source_errors(self.source + unsafe))
        covariance_bypass = self.source.replace(
            "joint_sample_covariance = training_data*training_data'/number_training_cells;",
            "joint_sample_covariance = eye(space_time_dimension);",
        ) + "\n% joint_sample_covariance = training_data*training_data'/number_training_cells;"
        recovery_bypass = self.source.replace(
            "recovered_weight = loaded_mvdr(joint_sample_covariance, ...",
            "recovered_weight = broken_weight; % bypass",
        ) + "\n% recovered_weight = loaded_mvdr(joint_sample_covariance, ..."
        self.assertTrue(p68_source_errors(covariance_bypass))
        self.assertTrue(p68_source_errors(recovery_bypass))

    def test_controls_accept_reviewed_and_reject_malformed_resource_inputs(self):
        validate_controls(reviewed_controls())
        mutations = (
            {"elements": True}, {"pulses": 8.5}, {"speed": float("nan")},
            {"seed": MODULUS - 4}, {"spacing": 0.75}, {"speed": 1000.0},
            {"wavelength": -0.03, "prf": -20000.0},
            {"training": 300}, {"support": (8, 64, 64, 128)},
            {"support": (8, 16, 64)}, {"contamination": (0.0, 0.2, 0.6)},
            {"map_doppler": (-0.6, 0.0, 0.45)}, {"actual_doppler": 0.08},
            {"map_doppler": (-0.1, 0.0, 0.3)},
            {"clutter_angles": (-95.0, -60.0, 0.0, 60.0, 95.0)},
            {"map_angles": (-95.0, 0.0, 95.0)},
            {"actual_angle": 20.0}, {"loading": 0.0}, {"noise_power": 0.0},
            {"noise_power": 1e50}, {"plot_floor": -5.0},
            {"max_dimension": 200}, {"max_patches": 100},
            {"max_training": 512}, {"max_map": 10000},
            {"max_private": 200000}, {"max_working": 2000000},
            {"max_figures": 7},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_controls(reviewed_controls(**mutation))
        with self.assertRaises(ValueError):
            validate_controls({})

    def test_private_generator_is_exact_repeatable_isolated_and_bounded(self):
        expected = (0.05322713733335358, 0.5884971616736134, 0.871796248420978, 0.27954721137860195)
        actual = private_uniform(6801, 4)
        for observed, wanted in zip(actual, expected):
            self.assertAlmostEqual(observed, wanted, places=15)
        self.assertEqual(actual, private_uniform(6801, 4))
        self.assertNotEqual(actual, private_uniform(6802, 4))
        for invalid in (True, 0, MODULUS, float("nan")):
            with self.assertRaises(ValueError):
                private_uniform(invalid, 4)
        for invalid in (0, 1.5, 100001):
            with self.assertRaises(ValueError):
                private_uniform(6801, invalid)

    def test_ridge_law_and_target_overlap_are_physical(self):
        slope = 2 * 105 / (0.03 * 20000)
        self.assertAlmostEqual(slope, 0.35, places=15)
        angles = list(range(-60, 61, 2))
        ridge = [slope * math.sin(math.radians(angle)) for angle in angles]
        self.assertGreater(min(ridge), -0.5)
        self.assertLess(max(ridge), 0.5)
        self.assertAlmostEqual(ridge[angles.index(10)], slope * math.sin(math.radians(10)), places=15)
        same_doppler_angle = math.degrees(math.asin(0.208 / slope))
        self.assertTrue(-60 < same_doppler_angle < 60)
        self.assertGreater(abs(0.208 - slope * math.sin(math.radians(10.7))), 0.05)

    def test_independent_joint_oracle_beats_separable_product(self):
        covariance, nominal, actual, angles, dopplers = reviewed_covariance()
        size = 6
        spatial_covariance = [[1 + 0j if row == column else 0j for column in range(size)] for row in range(size)]
        doppler_covariance = [[1 + 0j if row == column else 0j for column in range(size)] for row in range(size)]
        shapes = [math.cos(math.radians(angle)) ** 2 for angle in angles]
        powers = [1000 * value / sum(shapes) for value in shapes]
        for angle, doppler, power in zip(angles, dopplers, powers):
            spatial = steering(angle, 0.0, size)[:size]
            slow = [cmath.exp(1j * 2 * math.pi * index * doppler) for index in range(size)]
            spatial_covariance = add_matrix(spatial_covariance, outer(spatial), power)
            doppler_covariance = add_matrix(doppler_covariance, outer(slow), power)
        spatial_look = steering(10.0, 0.0, size)[:size]
        doppler_look = [cmath.exp(1j * 2 * math.pi * index * 0.2) for index in range(size)]
        separable = [pulse * element for pulse in mvdr(doppler_covariance, doppler_look) for element in mvdr(spatial_covariance, spatial_look)]
        joint = mvdr(covariance, nominal)
        sep_scnr = 10 * math.log10(abs(dot(separable, actual)) ** 2 / quadratic(separable, covariance))
        joint_scnr = 10 * math.log10(abs(dot(joint, actual)) ** 2 / quadratic(joint, covariance))
        self.assertAlmostEqual(dot(joint, nominal).real, 1.0, places=10)
        self.assertGreater(joint_scnr, sep_scnr + 20)

    def test_exact_finite_record_oracle_reproduces_retained_metrics(self):
        separable, joint, support, broken = exact_finite_record_results()
        self.assertAlmostEqual(separable, -9.125680222792566, places=9)
        self.assertAlmostEqual(joint, 16.462679327074724, places=9)
        expected_support = (-6.798879483099363, 5.923644889688251, 15.235820157031368, 15.630305529054183, 16.462679327074724)
        for observed, expected in zip(support, expected_support):
            self.assertAlmostEqual(observed, expected, places=9)
        self.assertAlmostEqual(broken, -7.395031861791259, places=9)
        self.assertGreater(joint - separable, 20)
        self.assertGreater(joint - broken, 20)

    def test_contaminated_mismatched_oracle_breaks_and_clean_covariance_recovers(self):
        covariance, nominal, actual, _, _ = reviewed_covariance()
        clean_weight = mvdr(covariance, nominal)
        contaminated = add_matrix(covariance, outer(actual), 100.0)
        broken_weight = mvdr(contaminated, nominal)
        clean_scnr = 10 * math.log10(abs(dot(clean_weight, actual)) ** 2 / quadratic(clean_weight, covariance))
        broken_scnr = 10 * math.log10(abs(dot(broken_weight, actual)) ** 2 / quadratic(broken_weight, covariance))
        broken_gain_db = 20 * math.log10(abs(dot(broken_weight, actual)))
        self.assertGreater(clean_scnr, broken_scnr + 15)
        self.assertLess(broken_gain_db, -3)
        self.assertEqual(mvdr(covariance, nominal), clean_weight)

    def test_trace_scaled_loading_preserves_constraint_but_changes_matched_weight(self):
        covariance, nominal, actual, _, _ = reviewed_covariance()
        clean_weight = mvdr(covariance, nominal)
        matched_covariance = add_matrix(covariance, outer(nominal), 100.0)
        matched_weight = mvdr(matched_covariance, nominal)
        mismatched_covariance = add_matrix(covariance, outer(actual), 100.0)
        mismatched_weight = mvdr(mismatched_covariance, nominal)

        relative_matched_change = math.sqrt(
            sum(abs(clean - matched) ** 2 for clean, matched in zip(clean_weight, matched_weight))
            / sum(abs(clean) ** 2 for clean in clean_weight)
        )
        matched_actual_gain_db = 20 * math.log10(abs(dot(matched_weight, actual)))
        mismatched_actual_gain_db = 20 * math.log10(abs(dot(mismatched_weight, actual)))

        self.assertAlmostEqual(relative_matched_change * 100, 0.12413046678258096, places=9)
        self.assertAlmostEqual(abs(dot(matched_weight, nominal)), 1.0, places=12)
        self.assertAlmostEqual(matched_actual_gain_db, 0.057987675412396855, places=9)
        self.assertAlmostEqual(mismatched_actual_gain_db, -3.3413640582236526, places=9)

    def test_power_and_voltage_db_conventions_are_explicit(self):
        self.assertIn("'target_response_db', 20*log10", self.source)
        self.assertIn("'scnr_db', 10*log10", self.source)
        self.assertIn("10*log10(max(joint_eigenvalues", self.source)
        self.assertNotIn("'scnr_db', 20*log10", self.source)

    def test_documents_are_concept_first_complete_and_not_placeholders(self):
        documents = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        for name, document in documents.items():
            with self.subTest(document=name):
                self.assertIn(QUESTION, document)
                self.assertNotIn("TODO", document)
        lesson = documents["lesson.md"]
        for marker in ("s(theta,nu) = kron(b(nu), a(theta))", "nu_c(theta)", "Rhat = (1/L)", "w_sep = kron(w_d, w_s)", "SCNR_out", "Limiting cases and claim boundary"):
            self.assertIn(marker, lesson)
        walkthrough = documents["walkthrough.md"]
        for marker in ("Sweep 1", "Sweep 2", "Broken case", "Recovery", "Ctrl+C", "unchanged"):
            self.assertIn(marker, walkthrough)
        checks = documents["checks.md"]
        self.assertIn("Short teach-back rubric", checks)
        self.assertGreaterEqual(checks.count("**Correct:**"), 22)

    def test_cli_start_advance_rollback_recovery_timeout_and_isolation(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.make_fixture(base, self.manifest)
            started = self.run_cli(fixture, "start", "68")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P68", started.stdout)
            self.assertIn("status: implemented", started.stdout)
            state = fixture / ".learning/progress.json"
            state.write_text(json.dumps({"schema_version": 1, "current": "P67", "completed": [f"P{number:02d}" for number in range(1, 68)], "notes": {}}) + "\n", encoding="utf-8")
            advanced = self.run_cli(fixture, "start")
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertIn("P68 — Build an Introductory STAP", advanced.stdout)
            era_manifest = copy.deepcopy(self.manifest)
            for module in era_manifest["modules"]:
                if module["number"] > 68:
                    module["status"] = "scaffolded"
            rolled_back = copy.deepcopy(era_manifest)
            next(module for module in rolled_back["modules"] if module["id"] == "P68")["status"] = "scaffolded"
            original_p67 = copy.deepcopy(next(module for module in rolled_back["modules"] if module["id"] == "P67"))
            original_p69_identity = {key: value for key, value in next(module for module in self.manifest["modules"] if module["id"] == "P69").items() if key != "status"}
            fixture = self.make_fixture(base / "rollback", rolled_back)
            refused = self.run_cli(fixture, "start", "68")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P68", refused.stdout)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P67"), original_p67)
            self.assertEqual({key: value for key, value in next(module for module in rolled_back["modules"] if module["id"] == "P69").items() if key != "status"}, original_p69_identity)
            (fixture / "curriculum/modules.json").write_text(json.dumps(era_manifest, indent=2) + "\n", encoding="utf-8")
            recovered = self.run_cli(fixture, "start", "68")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_cancellation_external_side_effect_and_rerun_boundaries(self):
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P68'));", self.source)
        self.assertIn("clear p68_results;", self.source)
        for token in ("parfor", "timer(", "fopen(", "save(", "system(", "webread"):
            self.assertNotIn(token, self.source)
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        normalized_walkthrough = " ".join(walkthrough.split())
        self.assertIn("Ctrl+C", walkthrough)
        self.assertIn("no worker, timer", walkthrough)
        self.assertIn("intermediate variables", normalized_walkthrough)
        self.assertIn("no background or external persistent state", normalized_walkthrough)

    def test_public_catalogs_preserve_dependency_and_future_extension(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 68 follows P67", readme)
        self.assertIn("Project 68 follows P67", start_here)
        self.assertRegex(index, r"\| \[P68\].*\| implemented \| 7 \|")
        p69 = next(module for module in self.manifest["modules"] if module["id"] == "P69")
        self.assertEqual(p69["title"], "Derive FMCW Range from Beat Frequency")

    def test_evidence_maps_acceptance_commands_claims_and_rollback(self):
        paths = sorted((ROOT / "docs/evidence").glob("P68-*.md"))
        self.assertEqual(len(paths), 1)
        evidence = paths[0].read_text(encoding="utf-8")
        for marker in ("# P68 Retained Evidence", "## Acceptance map", "## Deterministic simulated-oracle results", "## Figure and metric inventory", "## Exact commands and results", "## Focused coverage", "## Changed and preserved invariants", "## Residual risks", "## Rollback", "## Unperformed validation", "MATLAB runtime", "DSP_RADAR_VERIFY_PROFILE=contract", "DSP_RADAR_VERIFY_PROFILE=quick", "DSP_RADAR_VERIFY_PROFILE=full", "84 modules", "68 implemented", "operator-managed"):
            self.assertIn(marker, evidence)
        self.assertIn("all 1,127 tests", evidence)
        self.assertIn("verify-20260812-024650.log", evidence)
        self.assertNotIn("recorded after execution", evidence)
        self.assertNotIn("no passing result is claimed in advance", evidence)
        self.assertTrue(evidence.endswith("\n"))
        self.assertFalse(evidence.endswith("\n\n"))

    def test_changed_text_files_have_exactly_one_terminal_newline(self):
        paths = [MODULE / name for name in ARTIFACTS]
        paths.extend([ROOT / "curriculum/modules.json", ROOT / "README.md", ROOT / "START_HERE.md", ROOT / "modules/README.md", ROOT / "tests/test_p68_module.py"])
        paths.extend(sorted((ROOT / "docs/evidence").glob("P68-*.md")))
        for path in paths:
            with self.subTest(path=path):
                data = path.read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
