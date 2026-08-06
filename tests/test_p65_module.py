from __future__ import annotations

import cmath
import copy
import json
import math
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/65-use-mvdr-capon-adaptive-beamforming"
QUESTION = "How can a beamformer place data-dependent nulls on interference?"
EXPECTED_IDENTITY = {
    "number": 65,
    "id": "P65",
    "title": "Use MVDR/Capon Adaptive Beamforming",
    "guiding_question": QUESTION,
    "phase": 7,
    "phase_title": "Arrays, Beamforming, DOA, and STAP",
    "slug": "use-mvdr-capon-adaptive-beamforming",
    "folder": "modules/65-use-mvdr-capon-adaptive-beamforming",
    "status": "implemented",
    "implementation_batch": "P65",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
SOURCE_MARKERS = (
    "baseline_seed = 6501;",
    "number_elements = 8;",
    "element_spacing_wavelengths = 0.5;",
    "desired_angle_deg = 3.0;",
    "interferer_angle_deg = 30.0;",
    "desired_snr_db = -3.0;",
    "interferer_inr_db = 25.0;",
    "number_snapshots = 128;",
    "maximum_scene_snapshots = 256;",
    "baseline_loading_alpha = 0.01;",
    "scan_angles_deg = -50:0.1:50;",
    "snapshot_sweep = [4 8 16 32 64 128 256];",
    "loading_sweep_alpha = [1e-6 1e-4 1e-3 1e-2 1e-1 1];",
    "mismatch_deg = 3.0;",
    "broken_snapshot_count = 4;",
    "sample_covariance = baseline_sensor_data*baseline_sensor_data'/number_snapshots;",
    "sample_covariance = (sample_covariance+sample_covariance')/2;",
    "conventional_weight = desired_steering/number_elements;",
    "loading_power = alpha*loading_scale;",
    "numerator = loaded_covariance\\look_steering;",
    "denominator = look_steering'*numerator;",
    "weight = numerator/denominator;",
    "distortionless_response = mvdr_weight'*desired_steering;",
    "output_sinr = output_desired/(output_interference+output_noise);",
    "case_data = full_sensor_data(:, 1:case_snapshots);",
    "broken_solve_refused = broken_raw_rcond < minimum_reciprocal_condition;",
    "loaded_recovery_weight",
    "corrected_recovery_weight",
    "assert(abs(corrected_recovery_weight'*desired_steering-1) < 1e-10",
    "samples = sqrt(-2*log(first)).*exp(1j*2*pi*second)/sqrt(2);",
    "noise = reshape(samples, number_rows, number_columns);",
    "maximum_elements = 16;",
    "maximum_snapshots = 512;",
    "maximum_scan_samples = 1001;",
    "maximum_sweep_cases = 8;",
    "maximum_private_values = 30000;",
    "maximum_working_numeric_values = 600000;",
    "maximum_figures = 5;",
    "validate_controls(controls);",
    "p65_results = struct( ...",
    "close(findall(0, 'Type', 'figure', 'Tag', 'P65'));",
    "clear p65_results;",
    "loading_sweep_white_noise_gain_db, 'd-'",
    "covariance_magnitude_db = 10*log10(max(abs(sample_covariance)/ ...",
    "isnumeric(value) && ~islogical(value) && isreal(value) && ...",
    "c.max_elements == 16 && c.max_snapshots == 512 && ...",
)
FORBIDDEN_SOURCE_TOKENS = (
    "phased.",
    "mvdrbeamformer(",
    "steervec(",
    "collectPlaneWave(",
    "awgn(",
    "inv(",
    "pinv(",
    "rng(",
    "rand(",
    "randn(",
    "parfor",
    "timer(",
    "webread",
    "urlread",
    "system(",
    "fopen(",
    "save(",
    "close all",
)
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


def p65_source_contract_errors(source: object) -> list[str]:
    if not isinstance(source, str) or not source:
        return ["P65 source must be nonempty text"]
    errors = [
        f"missing source marker: {marker}" for marker in SOURCE_MARKERS if marker not in source
    ]
    if source.count("figure('Name', 'P65") != 5:
        errors.append("P65 must create exactly five named figures")
    if source.count("'Tag', 'P65'") != 6:
        errors.append("P65 must tag five figures and one scoped cleanup")
    errors.extend(
        f"forbidden source token: {token}"
        for token in FORBIDDEN_SOURCE_TOKENS
        if token in source
    )
    return errors


def validate_p65_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P65 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [
        entry
        for entry in manifest["modules"]
        if isinstance(entry, dict) and entry.get("id") == "P65"
    ]
    if len(matches) != 1:
        errors.append("P65 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P65 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P65 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P65 empty {artifact}")
    return errors


def reviewed_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "seed": 6501,
        "elements": 8,
        "spacing": 0.5,
        "desired_angle": 3.0,
        "interferer_angle": 30.0,
        "desired_snr_db": -3.0,
        "interferer_inr_db": 25.0,
        "noise_power": 1.0,
        "snapshots": 128,
        "scene_snapshots": 256,
        "loading_alpha": 0.01,
        "scan_angles": tuple(-50.0 + 0.1 * index for index in range(1001)),
        "snapshot_sweep": (4, 8, 16, 32, 64, 128, 256),
        "loading_sweep": (1e-6, 1e-4, 1e-3, 1e-2, 1e-1, 1.0),
        "mismatch_deg": 3.0,
        "broken_snapshots": 4,
        "recovery_alpha": 0.1,
        "max_elements": 16,
        "max_snapshots": 512,
        "max_scan_samples": 1001,
        "max_sweep_cases": 8,
        "max_private_values": 30000,
        "max_working_values": 600000,
        "max_figures": 5,
        "min_rcond": 1e-12,
    }
    controls.update(overrides)
    return controls


def validate_controls(controls: object) -> None:
    if not isinstance(controls, dict):
        raise ValueError("controls")
    required = set(reviewed_controls())
    if set(controls) != required:
        raise ValueError("control fields")
    scalar_names = required - {"scan_angles", "snapshot_sweep", "loading_sweep"}
    if not all(finite_real(controls[name]) for name in scalar_names):
        raise ValueError("finite scalar")
    integer_names = {
        "seed", "elements", "snapshots", "scene_snapshots", "broken_snapshots",
        "max_elements", "max_snapshots", "max_scan_samples", "max_sweep_cases",
        "max_private_values", "max_working_values", "max_figures",
    }
    if not all(integer(controls[name]) and controls[name] > 0 for name in integer_names):
        raise ValueError("integer")
    elements = int(controls["elements"])
    scene_snapshots = int(controls["scene_snapshots"])
    if not (
        elements <= controls["max_elements"]
        and controls["snapshots"] <= scene_snapshots <= controls["max_snapshots"]
        and controls["broken_snapshots"] < elements
        and 0 < controls["spacing"] <= 0.5
        and controls["noise_power"] > 0
        and controls["loading_alpha"] > 0
        and controls["recovery_alpha"] > 0
        and controls["min_rcond"] > 0
    ):
        raise ValueError("physical bounds")
    if (
        controls["desired_angle"] == controls["interferer_angle"]
        or any(abs(controls[name]) >= 90 for name in ("desired_angle", "interferer_angle"))
        or abs(controls["desired_angle"] + controls["mismatch_deg"]) >= 90
    ):
        raise ValueError("angles")
    scan = controls["scan_angles"]
    snapshots = controls["snapshot_sweep"]
    loads = controls["loading_sweep"]
    for sequence in (scan, snapshots, loads):
        if not isinstance(sequence, (tuple, list)) or len(sequence) < 3:
            raise ValueError("sequence")
        if not all(finite_real(value) for value in sequence):
            raise ValueError("sequence finite")
        if any(right <= left for left, right in zip(sequence, sequence[1:])):
            raise ValueError("sequence order")
    if len(scan) > controls["max_scan_samples"]:
        raise ValueError("scan bound")
    if len(snapshots) > controls["max_sweep_cases"] or not all(integer(x) for x in snapshots):
        raise ValueError("snapshot cases")
    if snapshots[0] < 1 or snapshots[-1] > scene_snapshots:
        raise ValueError("snapshot range")
    if len(loads) > controls["max_sweep_cases"] or loads[0] <= 0:
        raise ValueError("loading cases")
    immutable_ceilings = {
        "max_elements": 16,
        "max_snapshots": 512,
        "max_scan_samples": 1001,
        "max_sweep_cases": 8,
        "max_private_values": 30000,
        "max_working_values": 600000,
        "max_figures": 5,
    }
    if any(controls[name] != expected for name, expected in immutable_ceilings.items()):
        raise ValueError("immutable ceiling")
    if 2 * elements * scene_snapshots > controls["max_private_values"]:
        raise ValueError("resource")


def private_uniform(seed: object, count: object, maximum: int = 30000) -> tuple[float, ...]:
    if not integer(seed) or not 1 <= seed < MODULUS:
        raise ValueError("seed")
    if not integer(count) or not 1 <= count <= maximum:
        raise ValueError("count")
    state = int(seed)
    output = []
    for _ in range(int(count)):
        state = (MULTIPLIER * state) % MODULUS
        output.append(state / MODULUS)
    return tuple(output)


def private_complex_noise(seed: object, rows: object, columns: object) -> list[list[complex]]:
    if not integer(rows) or not integer(columns) or rows < 1 or columns < 1:
        raise ValueError("shape")
    count = int(rows * columns)
    values = private_uniform(seed, 2 * count)
    samples = [
        math.sqrt(-2 * math.log(max(values[index], float.fromhex("0x0.0000000000001p-1022"))))
        * cmath.exp(1j * 2 * math.pi * values[count + index])
        / math.sqrt(2)
        for index in range(count)
    ]
    return [
        [samples[column * int(rows) + row] for column in range(int(columns))]
        for row in range(int(rows))
    ]


def steering(angle_deg: float, elements: int = 8) -> list[complex]:
    return [
        cmath.exp(1j * 2 * math.pi * 0.5 * index * math.sin(math.radians(angle_deg)))
        for index in range(elements)
    ]


def conjugate_dot(left: list[complex], right: list[complex]) -> complex:
    return sum(value.conjugate() * other for value, other in zip(left, right))


def covariance(data: list[list[complex]], snapshots: int) -> list[list[complex]]:
    elements = len(data)
    return [
        [
            sum(data[row][look] * data[column][look].conjugate() for look in range(snapshots))
            / snapshots
            for column in range(elements)
        ]
        for row in range(elements)
    ]


def solve(matrix: list[list[complex]], vector: list[complex]) -> list[complex]:
    size = len(vector)
    augmented = [list(row) + [value] for row, value in zip(matrix, vector)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-14:
            raise ValueError("singular")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                left - factor * right
                for left, right in zip(augmented[row], augmented[column])
            ]
    return [augmented[row][-1] for row in range(size)]


def mvdr_weight(
    raw_covariance: list[list[complex]], look: list[complex], alpha: float
) -> tuple[list[complex], float]:
    if not finite_real(alpha) or alpha <= 0:
        raise ValueError("alpha")
    elements = len(look)
    scale = sum(raw_covariance[index][index].real for index in range(elements)) / elements
    loaded = [
        [
            raw_covariance[row][column] + (alpha * scale if row == column else 0)
            for column in range(elements)
        ]
        for row in range(elements)
    ]
    numerator = solve(loaded, look)
    denominator = conjugate_dot(look, numerator)
    if not math.isfinite(denominator.real) or denominator.real <= 0:
        raise ValueError("normalization")
    return [value / denominator for value in numerator], alpha * scale


def metrics(weight: list[complex]) -> dict[str, float]:
    desired = steering(3.0)
    interferer = steering(30.0)
    desired_power = 10 ** (-3 / 10)
    interferer_power = 10 ** (25 / 10)
    desired_response = abs(conjugate_dot(weight, desired))
    interferer_response = abs(conjugate_dot(weight, interferer))
    energy = conjugate_dot(weight, weight).real
    signal = desired_power * desired_response**2
    interference = interferer_power * interferer_response**2
    noise = energy
    return {
        "desired_response_db": 20 * math.log10(desired_response),
        "interferer_response_db": 20 * math.log10(interferer_response),
        "white_noise_gain_db": 10 * math.log10(1 / energy),
        "output_sinr_db": 10 * math.log10(signal / (interference + noise)),
    }


def deterministic_scene(interferer_angle_deg: float = 30.0) -> list[list[complex]]:
    elements = 8
    snapshots = 256
    desired = steering(3.0)
    interferer = steering(interferer_angle_deg)
    desired_samples = [cmath.exp(1j * 2 * math.pi * value) for value in private_uniform(6501, snapshots)]
    interferer_samples = [cmath.exp(1j * 2 * math.pi * value) for value in private_uniform(6502, snapshots)]
    noise = private_complex_noise(6503, elements, snapshots)
    desired_scale = math.sqrt(10 ** (-3 / 10))
    interferer_scale = math.sqrt(10 ** (25 / 10))
    return [
        [
            desired_scale * desired[row] * desired_samples[column]
            + interferer_scale * interferer[row] * interferer_samples[column]
            + noise[row][column]
            for column in range(snapshots)
        ]
        for row in range(elements)
    ]


def matrix_rank(matrix: list[list[complex]], tolerance: float = 1e-10) -> int:
    working = [list(row) for row in matrix]
    rows = len(working)
    columns = len(working[0])
    rank = 0
    for column in range(columns):
        pivot = max(range(rank, rows), key=lambda row: abs(working[row][column]), default=rank)
        if abs(working[pivot][column]) <= tolerance:
            continue
        working[rank], working[pivot] = working[pivot], working[rank]
        pivot_value = working[rank][column]
        for row in range(rank + 1, rows):
            factor = working[row][column] / pivot_value
            for index in range(column, columns):
                working[row][index] -= factor * working[rank][index]
        rank += 1
        if rank == rows:
            break
    return rank


class P65ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.scene = deterministic_scene()

    def make_cli_fixture(self, base: Path, manifest: dict) -> Path:
        fixture = base / "repo"
        (fixture / "bin").mkdir(parents=True)
        (fixture / "curriculum").mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
        (fixture / "curriculum/modules.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        for module in manifest["modules"]:
            readme = fixture / module["folder"] / "README.md"
            readme.parent.mkdir(parents=True, exist_ok=True)
            readme.write_text(f"# {module['id']}\n", encoding="utf-8")
        return fixture

    def run_fixture_cli(self, fixture: Path, *args: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["HOME"] = str(fixture.parent)
        return subprocess.run(
            [str(fixture / "bin/learn"), *args],
            cwd=fixture,
            env=environment,
            text=True,
            capture_output=True,
            timeout=10,
        )

    def test_artifacts_manifest_identity_and_dependency_are_complete(self):
        self.assertEqual(validate_p65_contract(ROOT, self.manifest), [])
        p64 = next(module for module in self.manifest["modules"] if module["id"] == "P64")
        self.assertEqual(p64["status"], "implemented")

    def test_contract_rejects_malformed_duplicate_drift_missing_and_empty(self):
        self.assertTrue(validate_p65_contract(ROOT, None))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append(None)
        self.assertIn("every manifest module must be an object", validate_p65_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("P65 must have exactly one manifest entry", validate_p65_contract(ROOT, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(module for module in drifted["modules"] if module["id"] == "P65")["title"] = "changed"
        self.assertIn("P65 manifest identity drift", validate_p65_contract(ROOT, drifted))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(MODULE, root / EXPECTED_IDENTITY["folder"])
            (root / EXPECTED_IDENTITY["folder"] / "lesson.md").unlink()
            self.assertIn("P65 missing lesson.md", validate_p65_contract(root, self.manifest))
            (root / EXPECTED_IDENTITY["folder"] / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P65 empty lesson.md", validate_p65_contract(root, self.manifest))

    def test_source_exposes_equations_sweeps_failure_recovery_and_bounds(self):
        self.assertEqual(p65_source_contract_errors(self.source), [])
        for marker in (
            "sample_covariance = baseline_sensor_data*baseline_sensor_data'/number_snapshots;",
            "numerator = loaded_covariance\\look_steering;",
            "weight = numerator/denominator;",
            "output_sinr = output_desired/(output_interference+output_noise);",
            "broken_solve_refused = broken_raw_rcond < minimum_reciprocal_condition;",
            "clear p65_results;",
        ):
            with self.subTest(marker=marker):
                self.assertTrue(p65_source_contract_errors(self.source.replace(marker, "removed", 1)))
        self.assertTrue(p65_source_contract_errors(self.source + "\nphased.ULA(8)"))

    def test_control_contract_accepts_reviewed_and_rejects_malformed_values(self):
        validate_controls(reviewed_controls())
        mutations = (
            {"elements": True},
            {"snapshots": 128.5},
            {"noise_power": float("nan")},
            {"spacing": 0.75},
            {"desired_angle": 30.0},
            {"scan_angles": (-60.0, 0.0, 0.0, 60.0)},
            {"snapshot_sweep": (4, 16, 8)},
            {"snapshot_sweep": (4, 8.5, 256)},
            {"loading_sweep": (1e-3, 1e-3, 1e-1)},
            {"loading_sweep": (0.0, 1e-3, 1e-1)},
            {"broken_snapshots": 8},
            {"max_figures": 6},
            {"max_private_values": 100},
            {"max_elements": 32},
            {"max_snapshots": 1024},
            {"max_scan_samples": 2001},
            {"max_sweep_cases": 16},
            {"max_private_values": 60000},
            {"max_working_values": 1200000},
            {"mismatch_deg": 90.0},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_controls(reviewed_controls(**mutation))
        with self.assertRaises(ValueError):
            validate_controls({})

    def test_private_generator_is_repeatable_isolated_and_bounded(self):
        expected = (
            0.050879226555525896,
            0.12716071872374077,
            0.19019958991100994,
            0.6845076343438158,
        )
        actual = private_uniform(6501, 4)
        for observed, wanted in zip(actual, expected):
            self.assertAlmostEqual(observed, wanted, places=15)
        self.assertEqual(actual, private_uniform(6501, 4))
        for invalid in (True, 0, MODULUS, float("nan")):
            with self.assertRaises(ValueError):
                private_uniform(invalid, 4)
        for invalid in (0, 1.5, 30001):
            with self.assertRaises(ValueError):
                private_uniform(6501, invalid)
        before = private_uniform(123, 8)
        private_complex_noise(6503, 8, 256)
        self.assertEqual(before, private_uniform(123, 8))

    def test_noise_layout_matches_matlab_column_major_reshape(self):
        noise = private_complex_noise(6503, 8, 256)
        fixtures = {
            (0, 0): complex(-1.5610206562645994, 0.735668046378368),
            (7, 0): complex(0.6034851289850605, 0.2355647276521446),
            (0, 1): complex(-0.8646904084853118, 0.13800636995239898),
            (7, 255): complex(-0.16615266336743884, -0.14495116728253934),
        }
        for (row, column), wanted in fixtures.items():
            self.assertAlmostEqual(noise[row][column].real, wanted.real, places=14)
            self.assertAlmostEqual(noise[row][column].imag, wanted.imag, places=14)

    def test_independent_baseline_oracle_preserves_look_and_improves_sinr(self):
        raw = covariance(self.scene, 128)
        adaptive, loading_power = mvdr_weight(raw, steering(3.0), 0.01)
        conventional = [value / 8 for value in steering(3.0)]
        adaptive_metrics = metrics(adaptive)
        conventional_metrics = metrics(conventional)
        self.assertAlmostEqual(abs(conjugate_dot(adaptive, steering(3.0))), 1.0, places=11)
        self.assertGreater(loading_power, 0)
        self.assertGreater(
            adaptive_metrics["output_sinr_db"], conventional_metrics["output_sinr_db"] + 10
        )
        self.assertLess(
            adaptive_metrics["interferer_response_db"],
            conventional_metrics["interferer_response_db"] - 10,
        )
        self.assertGreater(adaptive_metrics["white_noise_gain_db"], 0)

    def test_adaptive_null_follows_changed_interference_covariance(self):
        original_angle = 30.0
        moved_angle = -25.0
        original_weight, _ = mvdr_weight(
            covariance(deterministic_scene(original_angle), 128), steering(3.0), 0.01
        )
        moved_weight, _ = mvdr_weight(
            covariance(deterministic_scene(moved_angle), 128), steering(3.0), 0.01
        )
        original_response = {
            angle: 20 * math.log10(abs(conjugate_dot(original_weight, steering(angle))))
            for angle in (original_angle, moved_angle)
        }
        moved_response = {
            angle: 20 * math.log10(abs(conjugate_dot(moved_weight, steering(angle))))
            for angle in (original_angle, moved_angle)
        }
        self.assertLess(original_response[original_angle], original_response[moved_angle] - 20)
        self.assertLess(moved_response[moved_angle], moved_response[original_angle] - 20)
        self.assertLess(original_response[original_angle], -40)
        self.assertLess(moved_response[moved_angle], -40)

    def test_power_and_voltage_quantities_use_their_respective_db_conventions(self):
        self.assertIn(
            "covariance_magnitude_db = 10*log10(max(abs(sample_covariance)/ ...",
            self.source,
        )
        self.assertIn("10^(plot_floor_db/10)));", self.source)
        self.assertIn("mvdr_pattern_db = 20*log10", self.source)
        self.assertIn("component_powers_db = 10*log10", self.source)
        self.assertNotIn("covariance_magnitude_db = 20*log10", self.source)

    def test_snapshot_prefix_sweep_improves_long_record_without_monotonic_claim(self):
        sinr = []
        nulls = []
        for snapshots in (4, 8, 16, 32, 64, 128, 256):
            weight, _ = mvdr_weight(covariance(self.scene, snapshots), steering(3.0), 0.01)
            record = metrics(weight)
            sinr.append(record["output_sinr_db"])
            nulls.append(record["interferer_response_db"])
        self.assertGreater(sinr[-1], sinr[0] + 0.5)
        self.assertTrue(all(math.isfinite(value) for value in sinr + nulls))
        self.assertGreater(max(nulls) - min(nulls), 3)

    def test_loading_sweep_exposes_mismatch_tradeoff(self):
        raw = covariance(self.scene, 8)
        sinr = []
        desired_response = []
        nulls = []
        for alpha in (1e-6, 1e-4, 1e-3, 1e-2, 1e-1, 1.0):
            weight, _ = mvdr_weight(raw, steering(6.0), alpha)
            record = metrics(weight)
            sinr.append(record["output_sinr_db"])
            desired_response.append(record["desired_response_db"])
            nulls.append(record["interferer_response_db"])
        self.assertGreater(max(sinr[2:5]), sinr[0] + 3)
        self.assertGreater(desired_response[4], desired_response[0] + 2)
        self.assertGreater(nulls[-1], min(nulls[:-1]))

    def test_rank_deficient_broken_case_is_refused_and_same_data_recovers(self):
        raw = covariance(self.scene, 4)
        self.assertLessEqual(matrix_rank(raw), 4)
        self.assertGreater(len(raw), matrix_rank(raw))
        tiny_load, _ = mvdr_weight(raw, steering(6.0), 1e-6)
        loaded_mismatch, _ = mvdr_weight(raw, steering(6.0), 0.1)
        corrected, _ = mvdr_weight(raw, steering(3.0), 0.1)
        self.assertTrue(all(math.isfinite(value.real) and math.isfinite(value.imag) for value in corrected))
        self.assertAlmostEqual(abs(conjugate_dot(corrected, steering(3.0))), 1.0, places=11)
        self.assertGreater(
            metrics(loaded_mismatch)["output_sinr_db"],
            metrics(tiny_load)["output_sinr_db"] + 3,
        )
        self.assertGreater(
            metrics(corrected)["desired_response_db"],
            metrics(loaded_mismatch)["desired_response_db"] + 0.1,
        )

    def test_docs_are_concept_first_complete_and_not_placeholders(self):
        documents = {
            name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        }
        for name, document in documents.items():
            with self.subTest(document=name):
                self.assertIn(QUESTION, document)
                self.assertNotIn("TODO", document)
        lesson = documents["lesson.md"]
        for marker in (
            "minimize    w^H Rhat w",
            "w^H a0 = 1",
            "Rhat = X X^H / L",
            "alpha -> infinity",
            "Output SINR",
            "steering mismatch",
            "Limiting cases and claim boundary",
        ):
            self.assertIn(marker, lesson)
        walkthrough = documents["walkthrough.md"]
        for marker in ("Sweep 1", "Sweep 2", "Broken case", "Ctrl+C", "same", "Recovery"):
            self.assertIn(marker, walkthrough)
        checks = documents["checks.md"]
        self.assertIn("Short teach-back rubric", checks)
        self.assertGreaterEqual(checks.count("**Correct:**"), 32)

    def test_cli_start_advance_rollback_recovery_timeout_and_isolation(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.make_cli_fixture(base, self.manifest)
            started = self.run_fixture_cli(fixture, "start", "65")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P65", started.stdout)
            self.assertIn("status: implemented", started.stdout)

            state = fixture / ".learning/progress.json"
            state.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P64",
                        "completed": [f"P{number:02d}" for number in range(1, 65)],
                        "notes": {},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            advanced = self.run_fixture_cli(fixture, "start")
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertIn("P65 — Use MVDR/Capon Adaptive Beamforming", advanced.stdout)

            rolled_back = copy.deepcopy(self.manifest)
            next(module for module in rolled_back["modules"] if module["id"] == "P65")["status"] = "scaffolded"
            original_p64 = next(module for module in self.manifest["modules"] if module["id"] == "P64")
            original_p66 = next(module for module in self.manifest["modules"] if module["id"] == "P66")
            fixture = self.make_cli_fixture(base / "rollback", rolled_back)
            refused = self.run_fixture_cli(fixture, "start", "65")
            self.assertEqual(refused.returncode, 3, refused.stderr)
            self.assertIn("awaits Portfolio batch P65", refused.stdout)
            self.assertEqual(next(m for m in rolled_back["modules"] if m["id"] == "P64"), original_p64)
            self.assertEqual(next(m for m in rolled_back["modules"] if m["id"] == "P66"), original_p66)

            (fixture / "curriculum/modules.json").write_text(
                json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8"
            )
            recovered = self.run_fixture_cli(fixture, "start", "65")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_cancellation_is_foreground_scoped_and_has_no_external_side_effects(self):
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P65'));", self.source)
        self.assertIn("clear p65_results;", self.source)
        for token in ("parfor", "timer(", "fopen(", "save(", "system(", "webread"):
            self.assertNotIn(token, self.source)
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        self.assertIn("Ctrl+C", walkthrough)
        self.assertIn("no worker, timer", walkthrough)
        self.assertIn("partial persistent state", walkthrough)

    def test_public_catalogs_preserve_dependency_and_future_extension(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 65 follows P64", readme)
        self.assertIn("Project 65 follows P64", start_here)
        self.assertRegex(index, r"\| \[P65\].*\| implemented \| 7 \|")
        self.assertIn("P66 will reuse covariance structure", (MODULE / "README.md").read_text())

    def test_evidence_maps_acceptance_commands_claims_and_rollback(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P65-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        for marker in (
            "# P65 Retained Evidence",
            "## Acceptance map",
            "## Deterministic simulated-oracle results",
            "## Figure and metric inventory",
            "## Exact commands and results",
            "## Focused positive and negative coverage",
            "## Changed and preserved invariants",
            "## Residual risks and known content gaps",
            "## Rollback",
            "## Unperformed validation",
            "MATLAB runtime",
            "DSP_RADAR_VERIFY_PROFILE=contract",
            "DSP_RADAR_VERIFY_PROFILE=quick",
            "DSP_RADAR_VERIFY_PROFILE=full",
            "84 modules",
            "65 implemented",
            "operator-provided",
        ):
            self.assertIn(marker, evidence)
        self.assertTrue(evidence.endswith("\n"))
        self.assertFalse(evidence.endswith("\n\n"))

    def test_changed_text_files_have_exactly_one_terminal_newline(self):
        paths = [MODULE / name for name in ARTIFACTS]
        paths.extend(
            [
                ROOT / "curriculum/modules.json",
                ROOT / "README.md",
                ROOT / "START_HERE.md",
                ROOT / "modules/README.md",
                ROOT / "tests/test_p65_module.py",
            ]
        )
        paths.extend(sorted((ROOT / "docs/evidence").glob("P65-*.md")))
        for path in paths:
            with self.subTest(path=path):
                data = path.read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
