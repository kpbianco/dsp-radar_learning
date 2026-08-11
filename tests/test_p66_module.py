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
MODULE = ROOT / "modules/66-estimate-doa-with-music"
QUESTION = "How can subspace methods resolve sources more finely than a conventional beam?"
EXPECTED_IDENTITY = {
    "number": 66,
    "id": "P66",
    "title": "Estimate DOA with MUSIC",
    "guiding_question": QUESTION,
    "phase": 7,
    "phase_title": "Arrays, Beamforming, DOA, and STAP",
    "slug": "estimate-doa-with-music",
    "folder": "modules/66-estimate-doa-with-music",
    "status": "implemented",
    "implementation_batch": "P66",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
SOURCE_MARKERS = (
    "baseline_seed = 6601;",
    "number_elements = 10;",
    "element_spacing_wavelengths = 0.5;",
    "source_angles_deg = [-3 3];",
    "source_snr_db = 10;",
    "number_snapshots = 512;",
    "assumed_source_count = 2;",
    "scan_angles_deg = -40:0.1:40;",
    "source_spacing_sweep_deg = [2 3 4 5 6 8 10 12];",
    "snr_sweep_db = [-10 -5 0 5 10 15];",
    "snapshot_sweep = [16 32 64 128 256 512];",
    "assumed_count_sweep = [1 2 3 4];",
    "sample_covariance = baseline_sensor_data*baseline_sensor_data'/number_snapshots;",
    "sample_covariance = (sample_covariance+sample_covariance')/2;",
    "[eigenvectors, eigenvalue_matrix] = eig(covariance_matrix);",
    "[eigenvalues, eigenvalue_order] = sort(real(diag(eigenvalue_matrix)), ...",
    "eigenvectors = eigenvectors(:, eigenvalue_order);",
    "noise_subspace = eigenvectors(:, source_count+1:end);",
    "bartlett_power = real(sum(conj(scan_steering).* ...",
    "music_denominator = sum(abs(noise_subspace'*scan_steering).^2, 1);",
    "music_power = 1./max(music_denominator, realmin);",
    "coherent_waveforms = [source_waveforms(1, :); ...",
    "subarray_data = coherent_sensor_data( ...",
    "smoothed_covariance = smoothed_covariance/number_subarrays;",
    "smoothed_scan_steering = exp(1j*2*pi*element_spacing_wavelengths* ...",
    "maximum_elements = 16;",
    "maximum_sources = 4;",
    "maximum_snapshots = 512;",
    "maximum_scan_samples = 1001;",
    "maximum_sweep_cases = 8;",
    "maximum_private_values = 20000;",
    "maximum_working_numeric_values = 1000000;",
    "maximum_figures = 6;",
    "validate_controls(controls);",
    "p66_results = struct( ...",
    "close(findall(0, 'Type', 'figure', 'Tag', 'P66'));",
    "clear p66_results;",
    "samples = sqrt(-2*log(first)).*exp(1j*2*pi*second)/sqrt(2);",
    "noise = reshape(samples, number_rows, number_columns);",
    "isnumeric(value) && ~islogical(value) && isreal(value) && ...",
)
FORBIDDEN_SOURCE_TOKENS = (
    "phased.",
    "musicdoa(",
    "rootmusic(",
    "phased.MUSICEstimator",
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
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def p66_source_contract_errors(source: object) -> list[str]:
    if not isinstance(source, str) or not source:
        return ["P66 source must be nonempty text"]
    errors = [f"missing source marker: {marker}" for marker in SOURCE_MARKERS if marker not in source]
    if source.count("figure('Name', 'P66") != 6:
        errors.append("P66 must create exactly six named figures")
    if source.count("'Tag', 'P66'") != 7:
        errors.append("P66 must tag six figures and one scoped cleanup")
    errors.extend(f"forbidden source token: {token}" for token in FORBIDDEN_SOURCE_TOKENS if token in source)
    return errors


def validate_p66_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P66 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [
        entry for entry in manifest["modules"]
        if isinstance(entry, dict) and entry.get("id") == "P66"
    ]
    if len(matches) != 1:
        errors.append("P66 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P66 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P66 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P66 empty {artifact}")
    return errors


def reviewed_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "seed": 6601,
        "elements": 10,
        "spacing": 0.5,
        "source_angles": (-3.0, 3.0),
        "source_snr_db": 10.0,
        "noise_power": 1.0,
        "snapshots": 512,
        "scene_snapshots": 512,
        "assumed_sources": 2,
        "scan_angles": tuple(-40.0 + 0.1 * index for index in range(801)),
        "minimum_peak_separation": 1.0,
        "spacing_sweep": (2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0),
        "snr_sweep": (-10.0, -5.0, 0.0, 5.0, 10.0, 15.0),
        "snapshot_sweep": (16, 32, 64, 128, 256, 512),
        "snapshot_sweep_snr_db": 0.0,
        "count_sweep": (1, 2, 3, 4),
        "coherent_phase": 0.7,
        "smoothing_elements": 7,
        "plot_floor_db": -60.0,
        "max_elements": 16,
        "max_sources": 4,
        "max_snapshots": 512,
        "max_scan_samples": 1001,
        "max_sweep_cases": 8,
        "max_private_values": 20000,
        "max_working_values": 1000000,
        "max_figures": 6,
    }
    controls.update(overrides)
    return controls


def validate_real_sweep(values: object, integral: bool = False) -> None:
    if not isinstance(values, (tuple, list)) or not 3 <= len(values) <= 8:
        raise ValueError("sweep")
    if not all(finite_real(value) for value in values):
        raise ValueError("sweep finite")
    if integral and not all(integer(value) for value in values):
        raise ValueError("sweep integer")
    if any(right <= left for left, right in zip(values, values[1:])):
        raise ValueError("sweep order")


def validate_controls(controls: object) -> None:
    if not isinstance(controls, dict) or set(controls) != set(reviewed_controls()):
        raise ValueError("controls")
    sequence_names = {"source_angles", "scan_angles", "spacing_sweep", "snr_sweep", "snapshot_sweep", "count_sweep"}
    if not all(finite_real(value) for name, value in controls.items() if name not in sequence_names):
        raise ValueError("finite scalar")
    integer_names = {
        "seed", "elements", "snapshots", "scene_snapshots", "assumed_sources",
        "smoothing_elements", "max_elements", "max_sources", "max_snapshots",
        "max_scan_samples", "max_sweep_cases", "max_private_values",
        "max_working_values", "max_figures",
    }
    if not all(integer(controls[name]) and controls[name] > 0 for name in integer_names):
        raise ValueError("integer")
    source_angles = controls["source_angles"]
    if (
        not isinstance(source_angles, (tuple, list))
        or len(source_angles) != controls["assumed_sources"]
        or len(source_angles) > controls["max_sources"]
        or not all(finite_real(angle) and abs(angle) < 90 for angle in source_angles)
        or any(right <= left for left, right in zip(source_angles, source_angles[1:]))
    ):
        raise ValueError("source angles")
    scan = controls["scan_angles"]
    if (
        not isinstance(scan, (tuple, list))
        or len(scan) < 3
        or not all(finite_real(value) for value in scan)
        or any(right <= left for left, right in zip(scan, scan[1:]))
        or len(scan) > controls["max_scan_samples"]
        or any(abs(value) >= 90 for value in scan)
        or scan[0] > source_angles[0]
        or scan[-1] < source_angles[-1]
    ):
        raise ValueError("scan")
    validate_real_sweep(controls["spacing_sweep"])
    validate_real_sweep(controls["snr_sweep"])
    validate_real_sweep(controls["snapshot_sweep"], integral=True)
    validate_real_sweep(controls["count_sweep"], integral=True)
    elements = int(controls["elements"])
    assumed = int(controls["assumed_sources"])
    smoothing = int(controls["smoothing_elements"])
    if not (
        elements <= controls["max_elements"]
        and assumed <= controls["max_sources"]
        and assumed == 2
        and assumed < elements
        and controls["snapshots"] <= controls["scene_snapshots"] <= controls["max_snapshots"]
        and 0 < controls["spacing"] <= 0.5
        and controls["noise_power"] > 0
        and controls["noise_power"] <= 1e6
        and controls["minimum_peak_separation"] > 0
        and -200 <= controls["plot_floor_db"] <= -10
        and controls["spacing_sweep"][0] > 0
        and controls["spacing_sweep"][-1] / 2 <= min(abs(scan[0]), abs(scan[-1]))
        and all(abs(value) <= 40 for value in controls["snr_sweep"])
        and abs(controls["source_snr_db"]) <= 60
        and abs(controls["snapshot_sweep_snr_db"]) <= 60
        and controls["snapshot_sweep"][0] >= elements
        and controls["snapshot_sweep"][-1] <= controls["scene_snapshots"]
        and controls["count_sweep"][0] >= 1
        and controls["count_sweep"][-1] <= controls["max_sources"]
        and controls["count_sweep"][-1] < elements
        and assumed in controls["count_sweep"]
        and assumed < smoothing < elements
        and elements - smoothing + 1 >= assumed
    ):
        raise ValueError("physical bounds")
    immutable = {
        "max_elements": 16,
        "max_sources": 4,
        "max_snapshots": 512,
        "max_scan_samples": 1001,
        "max_sweep_cases": 8,
        "max_private_values": 20000,
        "max_working_values": 1000000,
        "max_figures": 6,
    }
    if any(controls[name] != value for name, value in immutable.items()):
        raise ValueError("immutable ceiling")
    if 2 * elements * controls["scene_snapshots"] > controls["max_private_values"]:
        raise ValueError("resource")


def private_uniform(seed: object, count: object, maximum: int = 20000) -> tuple[float, ...]:
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
    return [[samples[column * int(rows) + row] for column in range(int(columns))] for row in range(int(rows))]


def steering(angle_deg: float, elements: int = 10) -> list[complex]:
    return [
        cmath.exp(1j * 2 * math.pi * 0.5 * index * math.sin(math.radians(angle_deg)))
        for index in range(elements)
    ]


def conjugate_dot(left: list[complex], right: list[complex]) -> complex:
    return sum(value.conjugate() * other for value, other in zip(left, right))


def deterministic_components() -> tuple[list[list[complex]], list[list[complex]]]:
    snapshots = 512
    waveforms = [
        [cmath.exp(1j * 2 * math.pi * value) for value in private_uniform(seed, snapshots)]
        for seed in (6601, 6602)
    ]
    return waveforms, private_complex_noise(6603, 10, snapshots)


def deterministic_scene(
    angles: tuple[float, float] = (-3.0, 3.0),
    snr_db: float = 10.0,
    snapshots: int = 512,
    coherent: bool = False,
) -> list[list[complex]]:
    waveforms, noise = deterministic_components()
    if coherent:
        waveforms[1] = [value * cmath.exp(1j * 0.7) for value in waveforms[0]]
    vectors = [steering(angle) for angle in angles]
    amplitude = math.sqrt(10 ** (snr_db / 10))
    return [
        [
            amplitude * sum(vectors[source][row] * waveforms[source][column] for source in range(2))
            + noise[row][column]
            for column in range(snapshots)
        ]
        for row in range(10)
    ]


def covariance(data: list[list[complex]]) -> list[list[complex]]:
    elements = len(data)
    snapshots = len(data[0])
    return [
        [
            sum(data[row][look] * data[column][look].conjugate() for look in range(snapshots)) / snapshots
            for column in range(elements)
        ]
        for row in range(elements)
    ]


def matrix_vector(matrix: list[list[complex]], vector: list[complex]) -> list[complex]:
    return [sum(value * vector[column] for column, value in enumerate(row)) for row in matrix]


def orthonormalize(columns: list[list[complex]]) -> list[list[complex]]:
    result: list[list[complex]] = []
    for column in columns:
        working = list(column)
        for basis in result:
            projection = conjugate_dot(basis, working)
            working = [value - projection * basis_value for value, basis_value in zip(working, basis)]
        norm = math.sqrt(max(conjugate_dot(working, working).real, 0.0))
        if norm < 1e-14:
            raise ValueError("dependent iteration")
        result.append([value / norm for value in working])
    return result


def dominant_subspace(matrix: list[list[complex]], count: int, iterations: int = 350) -> list[list[complex]]:
    size = len(matrix)
    columns = [
        [cmath.exp(1j * 2 * math.pi * row * column / size) / math.sqrt(size) for row in range(size)]
        for column in range(count)
    ]
    for _ in range(iterations):
        columns = orthonormalize([matrix_vector(matrix, column) for column in columns])
    return columns


def spatial_spectra(
    matrix: list[list[complex]], source_count: int, scan: tuple[float, ...]
) -> tuple[list[float], list[float]]:
    elements = len(matrix)
    signal_subspace = dominant_subspace(matrix, source_count)
    bartlett = []
    music = []
    for angle in scan:
        vector = steering(angle, elements)
        bartlett.append(max(conjugate_dot(vector, matrix_vector(matrix, vector)).real / elements**2, 1e-15))
        signal_projection = sum(abs(conjugate_dot(basis, vector)) ** 2 for basis in signal_subspace)
        noise_projection = max(elements - signal_projection, 1e-15)
        music.append(1 / noise_projection)
    bartlett_max = max(bartlett)
    music_max = max(music)
    return (
        [10 * math.log10(max(value / bartlett_max, 1e-6)) for value in bartlett],
        [10 * math.log10(max(value / music_max, 1e-6)) for value in music],
    )


def select_peaks(spectrum: list[float], scan: tuple[float, ...], count: int) -> tuple[float, ...]:
    candidates = [
        index for index in range(1, len(spectrum) - 1)
        if spectrum[index] > spectrum[index - 1] and spectrum[index] >= spectrum[index + 1]
    ]
    candidates.sort(key=lambda index: spectrum[index], reverse=True)
    selected = []
    for index in candidates:
        if all(abs(scan[index] - scan[other]) >= 1.0 for other in selected):
            selected.append(index)
        if len(selected) == count:
            break
    return tuple(sorted(scan[index] for index in selected))


def matched_rmse(estimates: tuple[float, ...], truth: tuple[float, ...]) -> float:
    if len(estimates) != len(truth):
        return math.inf
    return math.sqrt(sum((estimate - actual) ** 2 for estimate, actual in zip(sorted(estimates), sorted(truth))) / len(truth))


def midpoint_contrast(spectrum: list[float], scan: tuple[float, ...], truth: tuple[float, float]) -> float:
    indices = [min(range(len(scan)), key=lambda index: abs(scan[index] - angle)) for angle in truth]
    midpoint = min(range(len(scan)), key=lambda index: abs(scan[index] - sum(truth) / 2))
    return min(spectrum[index] for index in indices) - spectrum[midpoint]


def spatially_smoothed_covariance(data: list[list[complex]], subarray_elements: int = 7) -> list[list[complex]]:
    subarrays = len(data) - subarray_elements + 1
    output = [[0j for _ in range(subarray_elements)] for _ in range(subarray_elements)]
    for start in range(subarrays):
        case = covariance(data[start : start + subarray_elements])
        for row in range(subarray_elements):
            for column in range(subarray_elements):
                output[row][column] += case[row][column] / subarrays
    return output


class P66ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.scan = tuple(-40.0 + 0.1 * index for index in range(801))
        cls.baseline_covariance = covariance(deterministic_scene())

    def make_cli_fixture(self, base: Path, manifest: dict) -> Path:
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

    def run_fixture_cli(self, fixture: Path, *args: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["HOME"] = str(fixture.parent)
        return subprocess.run(
            [str(fixture / "bin/learn"), *args], cwd=fixture, env=environment,
            text=True, capture_output=True, timeout=10,
        )

    def test_artifacts_manifest_identity_and_dependency_are_complete(self):
        self.assertEqual(validate_p66_contract(ROOT, self.manifest), [])
        p65 = next(module for module in self.manifest["modules"] if module["id"] == "P65")
        self.assertEqual(p65["status"], "implemented")

    def test_contract_rejects_malformed_duplicate_drift_missing_and_empty(self):
        self.assertTrue(validate_p66_contract(ROOT, None))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append(None)
        self.assertIn("every manifest module must be an object", validate_p66_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("P66 must have exactly one manifest entry", validate_p66_contract(ROOT, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(module for module in drifted["modules"] if module["id"] == "P66")["guiding_question"] = "changed"
        self.assertIn("P66 manifest identity drift", validate_p66_contract(ROOT, drifted))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(MODULE, root / EXPECTED_IDENTITY["folder"])
            (root / EXPECTED_IDENTITY["folder"] / "lesson.md").unlink()
            self.assertIn("P66 missing lesson.md", validate_p66_contract(root, self.manifest))
            (root / EXPECTED_IDENTITY["folder"] / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P66 empty lesson.md", validate_p66_contract(root, self.manifest))

    def test_source_exposes_music_sweeps_failure_recovery_and_bounds(self):
        self.assertEqual(p66_source_contract_errors(self.source), [])
        for marker in (
            "sample_covariance = baseline_sensor_data*baseline_sensor_data'/number_snapshots;",
            "noise_subspace = eigenvectors(:, source_count+1:end);",
            "music_denominator = sum(abs(noise_subspace'*scan_steering).^2, 1);",
            "smoothed_covariance = smoothed_covariance/number_subarrays;",
            "clear p66_results;",
        ):
            with self.subTest(marker=marker):
                self.assertTrue(p66_source_contract_errors(self.source.replace(marker, "removed", 1)))
        self.assertTrue(p66_source_contract_errors(self.source + "\nphased.MUSICEstimator"))

    def test_control_contract_accepts_reviewed_and_rejects_malformed_values(self):
        validate_controls(reviewed_controls())
        validate_controls(reviewed_controls(
            spacing_sweep=(2.5, 3.5, 7.5),
            snr_sweep=(0.0, 5.0, 10.0),
            snapshot_sweep=(128, 256, 512),
            count_sweep=(1, 2, 4),
        ))
        mutations = (
            {"elements": True},
            {"snapshots": 512.5},
            {"source_snr_db": float("nan")},
            {"noise_power": 1e308},
            {"spacing": 0.75},
            {"source_angles": (-3.0, -3.0)},
            {"source_angles": (3.0, -3.0)},
            {"scan_angles": (-40.0, 0.0, 0.0, 40.0)},
            {"scan_angles": (-100.0, 0.0, 100.0)},
            {"spacing_sweep": (2.0, 4.0, 3.0)},
            {"snr_sweep": (-10.0, float("inf"), 10.0)},
            {"snr_sweep": (-10.0, 0.0, 400.0)},
            {"source_snr_db": 400.0},
            {"snapshot_sweep": (16, 32.5, 512)},
            {"snapshot_sweep": (8, 16, 512)},
            {"count_sweep": (1, 2, 10)},
            {"count_sweep": (1, 2, 5)},
            {"assumed_sources": 0},
            {"assumed_sources": 3, "source_angles": (-3.0, 0.0, 3.0)},
            {"smoothing_elements": 2},
            {"smoothing_elements": 10},
            {"max_elements": 32},
            {"max_sources": 8},
            {"max_snapshots": 1024},
            {"max_scan_samples": 2001},
            {"max_sweep_cases": 16},
            {"max_private_values": 100},
            {"max_working_values": 2000000},
            {"max_figures": 7},
            {"plot_floor_db": -500.0},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_controls(reviewed_controls(**mutation))
        with self.assertRaises(ValueError):
            validate_controls({})

    def test_private_generator_is_repeatable_isolated_and_bounded(self):
        expected = (
            0.05166186348146846,
            0.280939533040365,
            0.7507318094143326,
            0.5495208266887445,
        )
        actual = private_uniform(6601, 4)
        for observed, wanted in zip(actual, expected):
            self.assertAlmostEqual(observed, wanted, places=15)
        self.assertEqual(actual, private_uniform(6601, 4))
        for invalid in (True, 0, MODULUS, float("nan")):
            with self.assertRaises(ValueError):
                private_uniform(invalid, 4)
        for invalid in (0, 1.5, 20001):
            with self.assertRaises(ValueError):
                private_uniform(6601, invalid)
        before = private_uniform(123, 8)
        private_complex_noise(6603, 10, 512)
        self.assertEqual(before, private_uniform(123, 8))

    def test_noise_layout_matches_matlab_column_major_reshape(self):
        noise = private_complex_noise(6603, 10, 512)
        fixtures = {
            (0, 0): complex(-1.149145665741945, 1.2814822356661866),
            (9, 0): complex(-0.2654456562478039, 0.4261532478272769),
            (0, 1): complex(0.8894544096353076, -0.7347468121961482),
            (9, 511): complex(1.0265526934804552, -0.8571290379385051),
        }
        for (row, column), wanted in fixtures.items():
            self.assertAlmostEqual(noise[row][column].real, wanted.real, places=14)
            self.assertAlmostEqual(noise[row][column].imag, wanted.imag, places=14)

    def test_independent_baseline_oracle_resolves_merged_bartlett_pair(self):
        bartlett, music = spatial_spectra(self.baseline_covariance, 2, self.scan)
        peaks = select_peaks(music, self.scan, 2)
        self.assertLess(matched_rmse(peaks, (-3.0, 3.0)), 0.25)
        self.assertLess(midpoint_contrast(bartlett, self.scan, (-3.0, 3.0)), 0)
        self.assertGreater(midpoint_contrast(music, self.scan, (-3.0, 3.0)), 10)
        self.assertEqual(len(peaks), 2)

    def test_spacing_sweep_reuses_inputs_and_exposes_super_resolution(self):
        records = []
        for separation in (2.0, 4.0, 12.0):
            truth = (-separation / 2, separation / 2)
            matrix = covariance(deterministic_scene(truth))
            bartlett, music = spatial_spectra(matrix, 2, self.scan)
            records.append((midpoint_contrast(bartlett, self.scan, truth), midpoint_contrast(music, self.scan, truth)))
        self.assertLess(records[1][0], 0)
        self.assertGreater(records[1][1], 8)
        self.assertGreater(records[2][0], 0)

    def test_snr_and_snapshot_endpoint_sweeps_expose_evidence_limits(self):
        low_music = spatial_spectra(covariance(deterministic_scene(snr_db=-10)), 2, self.scan)[1]
        high_music = spatial_spectra(covariance(deterministic_scene(snr_db=15)), 2, self.scan)[1]
        self.assertGreater(matched_rmse(select_peaks(low_music, self.scan, 2), (-3.0, 3.0)), 5)
        self.assertLess(matched_rmse(select_peaks(high_music, self.scan, 2), (-3.0, 3.0)), 0.25)
        short_music = spatial_spectra(covariance(deterministic_scene(snr_db=0, snapshots=16)), 2, self.scan)[1]
        long_music = spatial_spectra(covariance(deterministic_scene(snr_db=0, snapshots=512)), 2, self.scan)[1]
        self.assertGreater(matched_rmse(select_peaks(short_music, self.scan, 2), (-3.0, 3.0)), 5)
        self.assertLess(matched_rmse(select_peaks(long_music, self.scan, 2), (-3.0, 3.0)), 0.25)

    def test_assumed_source_count_changes_one_unchanged_projection(self):
        one_music = spatial_spectra(self.baseline_covariance, 1, self.scan)[1]
        two_music = spatial_spectra(self.baseline_covariance, 2, self.scan)[1]
        one_peak = select_peaks(one_music, self.scan, 1)[0]
        self.assertLess(abs(one_peak), 1)
        self.assertLess(matched_rmse(select_peaks(two_music, self.scan, 2), (-3.0, 3.0)), 0.25)

    def test_overestimated_source_count_adds_artifacts_on_unchanged_covariance(self):
        truth = (-3.0, 3.0)
        for assumed_count in (3, 4):
            with self.subTest(assumed_count=assumed_count):
                music = spatial_spectra(self.baseline_covariance, assumed_count, self.scan)[1]
                peaks = select_peaks(music, self.scan, assumed_count)
                self.assertEqual(len(peaks), assumed_count)
                for true_angle in truth:
                    self.assertLess(min(abs(peak - true_angle) for peak in peaks), 0.25)
                artifacts = [
                    peak for peak in peaks
                    if all(abs(peak - true_angle) >= 0.25 for true_angle in truth)
                ]
                self.assertEqual(len(artifacts), assumed_count - len(truth))

    def test_coherent_failure_and_same_data_spatial_smoothing_recovery(self):
        coherent_data = deterministic_scene(coherent=True)
        raw_music = spatial_spectra(covariance(coherent_data), 2, self.scan)[1]
        smoothed = spatially_smoothed_covariance(coherent_data, 7)
        recovered_music = spatial_spectra(smoothed, 2, self.scan)[1]
        raw_error = matched_rmse(select_peaks(raw_music, self.scan, 2), (-3.0, 3.0))
        recovered_error = matched_rmse(select_peaks(recovered_music, self.scan, 2), (-3.0, 3.0))
        self.assertGreater(raw_error, 5)
        self.assertLess(recovered_error, 0.25)
        self.assertEqual(len(smoothed), 7)
        self.assertEqual(len(smoothed[0]), 7)

    def test_power_quantities_use_power_db_convention(self):
        self.assertIn("covariance_magnitude_db = 10*log10", self.source)
        self.assertIn("bartlett_db = 10*log10", self.source)
        self.assertIn("music_db = 10*log10", self.source)
        self.assertNotIn("music_db = 20*log10", self.source)
        self.assertNotIn("bartlett_db = 20*log10", self.source)

    def test_docs_are_concept_first_complete_and_not_placeholders(self):
        documents = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        for name, document in documents.items():
            with self.subTest(document=name):
                self.assertIn(QUESTION, document)
                self.assertNotIn("TODO", document)
        lesson = documents["lesson.md"]
        for marker in (
            "Rhat = X X^H / L", "En = U(:,K+1:M)",
            "PMUSIC(theta) = 1 / ||En^H a(theta)||^2", "source number",
            "coherence collapses source rank", "Limiting cases and claim boundary",
        ):
            self.assertIn(marker, lesson)
        walkthrough = documents["walkthrough.md"]
        for marker in ("Sweep 1", "Sweep 2", "Sweep 3", "Sweep 4", "Broken case", "Recovery", "Ctrl+C", "unchanged"):
            self.assertIn(marker, walkthrough)
        checks = documents["checks.md"]
        self.assertIn("Short teach-back rubric", checks)
        self.assertGreaterEqual(checks.count("**Correct:**"), 37)

    def test_cli_start_advance_rollback_recovery_timeout_and_isolation(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.make_cli_fixture(base, self.manifest)
            started = self.run_fixture_cli(fixture, "start", "66")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P66", started.stdout)
            self.assertIn("status: implemented", started.stdout)
            state = fixture / ".learning/progress.json"
            state.write_text(
                json.dumps({
                    "schema_version": 1,
                    "current": "P65",
                    "completed": [f"P{number:02d}" for number in range(1, 66)],
                    "notes": {},
                }) + "\n",
                encoding="utf-8",
            )
            advanced = self.run_fixture_cli(fixture, "start")
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertIn("P66 — Estimate DOA with MUSIC", advanced.stdout)

            rolled_back = copy.deepcopy(self.manifest)
            next(module for module in rolled_back["modules"] if module["id"] == "P66")["status"] = "scaffolded"
            original_p65 = next(module for module in self.manifest["modules"] if module["id"] == "P65")
            original_p67 = next(module for module in self.manifest["modules"] if module["id"] == "P67")
            fixture = self.make_cli_fixture(base / "rollback", rolled_back)
            refused = self.run_fixture_cli(fixture, "start", "66")
            self.assertEqual(refused.returncode, 3, refused.stderr)
            self.assertIn("awaits Portfolio batch P66", refused.stdout)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P65"), original_p65)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P67"), original_p67)
            (fixture / "curriculum/modules.json").write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")
            recovered = self.run_fixture_cli(fixture, "start", "66")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_cancellation_is_foreground_scoped_and_has_no_external_side_effects(self):
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P66'));", self.source)
        self.assertIn("clear p66_results;", self.source)
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
        self.assertIn("Project 66 follows P65", readme)
        self.assertIn("Project 66 follows P65", start_here)
        self.assertRegex(index, r"\| \[P66\].*\| implemented \| 7 \|")
        self.assertIn("P67 will show", (MODULE / "README.md").read_text(encoding="utf-8"))

    def test_evidence_maps_acceptance_commands_claims_and_rollback(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P66-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        for marker in (
            "# P66 Retained Evidence", "## Acceptance map",
            "## Deterministic simulated-oracle results", "## Figure and metric inventory",
            "## Exact commands and results", "## Focused positive and negative coverage",
            "## Changed and preserved invariants", "## Residual risks and known content gaps",
            "## Rollback", "## Unperformed validation", "MATLAB runtime",
            "DSP_RADAR_VERIFY_PROFILE=contract", "DSP_RADAR_VERIFY_PROFILE=quick",
            "DSP_RADAR_VERIFY_PROFILE=full", "84 modules", "66 implemented", "operator-provided",
        ):
            self.assertIn(marker, evidence)
        self.assertTrue(evidence.endswith("\n"))
        self.assertFalse(evidence.endswith("\n\n"))

    def test_changed_text_files_have_exactly_one_terminal_newline(self):
        paths = [MODULE / name for name in ARTIFACTS]
        paths.extend([
            ROOT / "curriculum/modules.json", ROOT / "README.md", ROOT / "START_HERE.md",
            ROOT / "modules/README.md", ROOT / "tests/test_p66_module.py",
        ])
        paths.extend(sorted((ROOT / "docs/evidence").glob("P66-*.md")))
        for path in paths:
            with self.subTest(path=path):
                data = path.read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
