from __future__ import annotations

import cmath
import copy
import json
import math
import os
import shutil
import statistics
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/63-implement-conventional-delay-and-sum-beamforming"
QUESTION = "How does steering align one direction and misalign others?"
EXPECTED_IDENTITY = {
    "number": 63,
    "id": "P63",
    "title": "Implement Conventional Delay-and-Sum Beamforming",
    "guiding_question": QUESTION,
    "phase": 7,
    "phase_title": "Arrays, Beamforming, DOA, and STAP",
    "slug": "implement-conventional-delay-and-sum-beamforming",
    "folder": "modules/63-implement-conventional-delay-and-sum-beamforming",
    "status": "implemented",
    "implementation_batch": "P63",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
SOURCE_MARKERS = (
    "baseline_seed = 6301;",
    "number_elements = 8;",
    "element_spacing_wavelengths = 0.5;",
    "source_angles_deg = [-20 25];",
    "source_snr_db = 10.0;",
    "number_snapshots = 128;",
    "scan_angles_deg = -60:0.1:60;",
    "source_separation_sweep_deg = [6 12 24];",
    "array_size_sweep = [4 8 16];",
    "snr_sweep_db = [-15 0 15];",
    "snapshot_sweep = [1 8 128];",
    "broken_source_angles_deg = [-20 30];",
    "baseline_scan_steering = exp(1j*baseline_scan_phase_rad);",
    "baseline_weights = baseline_scan_steering/number_elements;",
    "baseline_beam_outputs = baseline_weights'*baseline_sensor_data;",
    "baseline_power = mean(abs(baseline_beam_outputs).^2, 2).';",
    "sample_covariance = baseline_sensor_data*baseline_sensor_data'/ ...",
    "scan_weight'*sample_covariance*scan_weight",
    "aligned_element_contributions = conj(aligned_weight).* ...",
    "mismatched_element_contributions = conj(mismatched_weight).* ...",
    "assert(~separation_sweep_resolved(1) && ...",
    "array_sweep_resolved",
    "assert(all(diff(snr_sweep_background_db) < 0), 'P63:SNRSweep', ...",
    "snapshot_sweep_background_ripple_db",
    "broken_power = scan_power(broken_sensor_data, ...",
    "recovered_power = scan_power(broken_sensor_data, ...",
    "mirror_error = max(abs(broken_power-fliplr(recovered_power)));",
    "source_uniforms = private_uniform(seed, ...",
    "source_snapshots = reshape(exp(1j*2*pi*source_uniforms), ...",
    "noise = private_complex_noise(seed+1, maximum_elements, ...",
    "source_steering = exp(1j*2*pi*spacing_wavelengths* ...",
    "sensor_data = source_steering*source_snapshots+noise;",
    "steering = exp(1j*steering_sign*2*pi*spacing_wavelengths* ...",
    "beam_outputs = weights'*sensor_data;\n    power = mean(abs(beam_outputs).^2, 2).';",
    "samples = sqrt(-2*log(first)).*exp(1j*2*pi*second)/sqrt(2);",
    "noise = reshape(samples, number_rows, number_columns);",
    "peak_is_local(source_index) = selected_index > 1 && ...",
    "maximum_elements = 16;",
    "maximum_snapshots = 256;",
    "maximum_scan_samples = 2001;",
    "maximum_working_numeric_values = 500000;",
    "maximum_figures = 5;",
    "validate_controls(controls);",
    "p63_results = struct( ...",
    "close(findall(0, 'Type', 'figure', 'Tag', 'P63'));",
)
FORBIDDEN_SOURCE_TOKENS = (
    "phased.",
    "sensorcov(",
    "steervec(",
    "collectPlaneWave(",
    "beamscan(",
    "findpeaks(",
    "awgn(",
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


def p63_source_contract_errors(source: object) -> list[str]:
    if not isinstance(source, str) or not source:
        return ["P63 source must be nonempty text"]
    errors = [
        f"missing source marker: {marker}" for marker in SOURCE_MARKERS if marker not in source
    ]
    if source.count("figure('Name', 'P63") != 5:
        errors.append("P63 must create exactly five named figures")
    if source.count("'Tag', 'P63'") != 6:
        errors.append("P63 must tag five figures and one scoped cleanup")
    errors.extend(
        f"forbidden source token: {token}"
        for token in FORBIDDEN_SOURCE_TOKENS
        if token in source
    )
    return errors


def validate_p63_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P63 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [
        entry
        for entry in manifest["modules"]
        if isinstance(entry, dict) and entry.get("id") == "P63"
    ]
    if len(matches) != 1:
        errors.append("P63 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P63 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P63 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P63 empty {artifact}")
    return errors


def reviewed_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "seed": 6301,
        "elements": 8,
        "spacing": 0.5,
        "source_angles": (-20.0, 25.0),
        "snr_db": 10.0,
        "snapshots": 128,
        "scan_angles": tuple(-60.0 + 0.1 * index for index in range(1201)),
        "floor_db": -35.0,
        "separation_sweep": (6.0, 12.0, 24.0),
        "array_sweep": (4, 8, 16),
        "array_source_angles": (-8.0, 8.0),
        "snr_sweep": (-15.0, 0.0, 15.0),
        "snapshot_sweep": (1, 8, 128),
        "broken_angles": (-20.0, 30.0),
        "broken_seed": 6315,
        "max_elements": 16,
        "max_sources": 2,
        "max_snapshots": 256,
        "max_scan": 2001,
        "max_cases": 5,
        "max_private": 20000,
        "max_values": 500000,
        "max_figures": 5,
        "tolerance": 1e-10,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    for name in (
        "seed",
        "elements",
        "snapshots",
        "broken_seed",
        "max_elements",
        "max_sources",
        "max_snapshots",
        "max_scan",
        "max_cases",
        "max_private",
        "max_values",
        "max_figures",
    ):
        if not integer(controls[name]):
            raise ValueError(f"{name} integer")
    for name in ("spacing", "snr_db", "floor_db", "tolerance"):
        if not finite_real(controls[name]):
            raise ValueError(f"{name} finite")
    if controls["seed"] != 6301 or controls["broken_seed"] != 6315:
        raise ValueError("seed")
    if controls["elements"] != 8 or not 2 <= controls["elements"] <= controls["max_elements"] == 16:
        raise ValueError("elements")
    if controls["spacing"] != 0.5 or controls["snr_db"] != 10.0:
        raise ValueError("baseline")
    if controls["snapshots"] != 128 or controls["max_snapshots"] != 256:
        raise ValueError("snapshots")
    for name, expected in (
        ("source_angles", (-20.0, 25.0)),
        ("array_source_angles", (-8.0, 8.0)),
        ("broken_angles", (-20.0, 30.0)),
    ):
        values = controls[name]
        if (
            not isinstance(values, (tuple, list))
            or tuple(values) != expected
            or len(values) > controls["max_sources"] == 2
            or not all(finite_real(value) and abs(value) < 60 for value in values)
            or any(right <= left for left, right in zip(values, values[1:]))
        ):
            raise ValueError(name)
    scan_angles = controls["scan_angles"]
    if (
        not isinstance(scan_angles, (tuple, list))
        or not scan_angles
        or len(scan_angles) > controls["max_scan"] == 2001
        or not all(finite_real(value) for value in scan_angles)
        or scan_angles[0] != -60.0
        or abs(scan_angles[-1] - 60.0) > 1e-9
        or any(right <= left for left, right in zip(scan_angles, scan_angles[1:]))
        or any(abs((right - left) - 0.1) > 1e-9 for left, right in zip(scan_angles, scan_angles[1:]))
    ):
        raise ValueError("scan angles")
    for name, expected in (
        ("separation_sweep", (6.0, 12.0, 24.0)),
        ("array_sweep", (4, 8, 16)),
        ("snr_sweep", (-15.0, 0.0, 15.0)),
        ("snapshot_sweep", (1, 8, 128)),
    ):
        values = controls[name]
        if (
            not isinstance(values, (tuple, list))
            or tuple(values) != expected
            or len(values) > controls["max_cases"] == 5
            or not all(finite_real(value) for value in values)
            or any(right <= left for left, right in zip(values, values[1:]))
        ):
            raise ValueError(name)
    if not all(integer(value) for value in controls["array_sweep"] + controls["snapshot_sweep"]):
        raise ValueError("integer sweep")
    if (
        controls["floor_db"] != -35.0
        or controls["tolerance"] != 1e-10
        or controls["max_private"] != 20000
        or controls["max_values"] != 500000
        or controls["max_figures"] != 5
    ):
        raise ValueError("immutable ceiling")
    private_request = 2 * controls["max_elements"] * controls["snapshots"]
    working_request = (
        len(scan_angles) * controls["snapshots"]
        + 2 * controls["max_elements"] * controls["snapshots"]
        + controls["max_elements"] * len(scan_angles)
    )
    if private_request > controls["max_private"] or working_request > controls["max_values"]:
        raise ValueError("resource ceiling")
    return controls


def private_uniform(seed: object, count: object, maximum: int = 20000) -> tuple[float, ...]:
    if not integer(seed) or not 1 <= seed < MODULUS:
        raise ValueError("seed")
    if not integer(count) or not 1 <= count <= maximum:
        raise ValueError("count")
    state = int(seed)
    values = []
    for _ in range(int(count)):
        state = (MULTIPLIER * state) % MODULUS
        values.append((state + 0.5) / MODULUS)
    return tuple(values)


def private_complex_noise(seed: int, rows: int, columns: int, maximum: int = 20000) -> list[list[complex]]:
    if not integer(rows) or not integer(columns) or rows < 1 or columns < 1:
        raise ValueError("noise shape")
    uniforms = private_uniform(seed, 2 * rows * columns, maximum)
    samples = [
        math.sqrt(-2 * math.log(uniforms[index]))
        * cmath.exp(1j * 2 * math.pi * uniforms[index + 1])
        / math.sqrt(2)
        for index in range(0, len(uniforms), 2)
    ]
    matrix = [[0j for _ in range(columns)] for _ in range(rows)]
    for linear_index, sample in enumerate(samples):
        row = linear_index % rows
        column = linear_index // rows
        matrix[row][column] = sample
    return matrix


def simulate_scene(
    seed: int,
    elements: int,
    source_angles: tuple[float, ...],
    snr_db: float,
    snapshots: int,
    maximum_elements: int = 16,
) -> list[list[complex]]:
    if not integer(elements) or not 2 <= elements <= maximum_elements:
        raise ValueError("elements")
    if not integer(snapshots) or not 1 <= snapshots <= 256:
        raise ValueError("snapshots")
    if (
        not isinstance(source_angles, (tuple, list))
        or len(source_angles) != 2
        or not all(finite_real(angle) and abs(angle) < 60 for angle in source_angles)
    ):
        raise ValueError("source angles")
    if not finite_real(snr_db):
        raise ValueError("snr")
    uniforms = private_uniform(seed, len(source_angles) * snapshots)
    sources = [[0j for _ in range(snapshots)] for _ in source_angles]
    for linear_index, value in enumerate(uniforms):
        row = linear_index % len(source_angles)
        column = linear_index // len(source_angles)
        sources[row][column] = cmath.exp(1j * 2 * math.pi * value)
    noise = private_complex_noise(seed + 1, maximum_elements, snapshots)
    noise_scale = 10 ** (-snr_db / 20)
    data = [[0j for _ in range(snapshots)] for _ in range(elements)]
    for element in range(elements):
        for snapshot in range(snapshots):
            signal = sum(
                cmath.exp(1j * 2 * math.pi * 0.5 * element * math.sin(math.radians(angle)))
                * sources[source][snapshot]
                for source, angle in enumerate(source_angles)
            )
            data[element][snapshot] = signal + noise_scale * noise[element][snapshot]
    return data


def scan_power(
    sensor_data: object,
    scan_angles: object,
    steering_sign: object = 1,
) -> tuple[float, ...]:
    if (
        not isinstance(sensor_data, list)
        or len(sensor_data) < 2
        or any(not isinstance(row, list) or not row for row in sensor_data)
        or len({len(row) for row in sensor_data}) != 1
        or any(not math.isfinite(value.real) or not math.isfinite(value.imag) for row in sensor_data for value in row)
    ):
        raise ValueError("sensor data")
    if (
        not isinstance(scan_angles, (tuple, list))
        or not scan_angles
        or not all(finite_real(angle) and -60 <= angle <= 60 for angle in scan_angles)
    ):
        raise ValueError("scan angles")
    if steering_sign not in (-1, 1):
        raise ValueError("steering sign")
    elements = len(sensor_data)
    snapshots = len(sensor_data[0])
    powers = []
    for angle in scan_angles:
        weight = [
            cmath.exp(1j * steering_sign * 2 * math.pi * 0.5 * element * math.sin(math.radians(angle)))
            / elements
            for element in range(elements)
        ]
        total = 0.0
        for snapshot in range(snapshots):
            output = sum(weight[element].conjugate() * sensor_data[element][snapshot] for element in range(elements))
            total += abs(output) ** 2
        powers.append(total / snapshots)
    return tuple(powers)


def covariance_power(sensor_data: list[list[complex]], scan_angles: tuple[float, ...]) -> tuple[float, ...]:
    elements = len(sensor_data)
    snapshots = len(sensor_data[0])
    covariance = [[0j for _ in range(elements)] for _ in range(elements)]
    for row in range(elements):
        for column in range(elements):
            covariance[row][column] = sum(
                sensor_data[row][snapshot] * sensor_data[column][snapshot].conjugate()
                for snapshot in range(snapshots)
            ) / snapshots
    powers = []
    for angle in scan_angles:
        weight = [
            cmath.exp(1j * 2 * math.pi * 0.5 * element * math.sin(math.radians(angle))) / elements
            for element in range(elements)
        ]
        value = sum(
            weight[row].conjugate() * covariance[row][column] * weight[column]
            for row in range(elements)
            for column in range(elements)
        )
        powers.append(value.real)
    return tuple(powers)


def peak_near_with_local(
    scan_angles: tuple[float, ...],
    powers: tuple[float, ...],
    expected_angles: tuple[float, ...],
    radius: float = 5.0,
) -> tuple[tuple[float, ...], tuple[bool, ...]]:
    if (
        len(scan_angles) != len(powers)
        or len(scan_angles) < 3
        or not all(finite_real(value) for value in scan_angles + powers)
        or not finite_real(radius)
        or radius <= 0
    ):
        raise ValueError("peak record")
    peaks = []
    local_flags = []
    for expected in expected_angles:
        candidates = [index for index, angle in enumerate(scan_angles) if abs(angle - expected) <= radius]
        if not candidates:
            raise ValueError("empty peak window")
        index = max(candidates, key=lambda candidate: powers[candidate])
        peaks.append(scan_angles[index])
        local_flags.append(
            0 < index < len(powers) - 1
            and powers[index] >= powers[index - 1]
            and powers[index] > powers[index + 1]
        )
    return tuple(peaks), tuple(local_flags)


def peak_near(
    scan_angles: tuple[float, ...],
    powers: tuple[float, ...],
    expected_angles: tuple[float, ...],
    radius: float = 5.0,
) -> tuple[float, ...]:
    return peak_near_with_local(scan_angles, powers, expected_angles, radius)[0]


def relative_background_db(
    scan_angles: tuple[float, ...],
    powers: tuple[float, ...],
    source_angles: tuple[float, ...],
) -> tuple[float, float]:
    background = [
        power / max(powers)
        for angle, power in zip(scan_angles, powers)
        if all(abs(angle - source) > 12 for source in source_angles)
    ]
    db = [10 * math.log10(max(value, 10 ** (-35 / 10))) for value in background]
    return 10 * math.log10(statistics.median(background)), statistics.stdev(db)


class P63ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.scan_angles = tuple(-60.0 + 0.1 * index for index in range(1201))

    def run_fixture_cli(self, fixture_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(fixture_root.parent)
        return subprocess.run(
            [str(fixture_root / "bin/learn"), *args],
            cwd=fixture_root,
            env=env,
            text=True,
            capture_output=True,
            timeout=10,
        )

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

    def test_artifacts_and_manifest_identity_are_complete(self):
        self.assertEqual(validate_p63_contract(ROOT, self.manifest), [])
        p62 = next(module for module in self.manifest["modules"] if module["id"] == "P62")
        self.assertEqual(p62["status"], "implemented")

    def test_contract_rejects_malformed_duplicate_drift_missing_and_empty(self):
        self.assertTrue(validate_p63_contract(ROOT, None))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append(None)
        self.assertIn("every manifest module must be an object", validate_p63_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("P63 must have exactly one manifest entry", validate_p63_contract(ROOT, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(module for module in drifted["modules"] if module["id"] == "P63")["guiding_question"] = "changed"
        self.assertIn("P63 manifest identity drift", validate_p63_contract(ROOT, drifted))
        with tempfile.TemporaryDirectory() as temp:
            fixture_root = Path(temp)
            fixture_module = fixture_root / EXPECTED_IDENTITY["folder"]
            fixture_module.parent.mkdir(parents=True)
            shutil.copytree(MODULE, fixture_module)
            (fixture_module / "lesson.md").unlink()
            self.assertIn("P63 missing lesson.md", validate_p63_contract(fixture_root, self.manifest))
            (fixture_module / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P63 empty lesson.md", validate_p63_contract(fixture_root, self.manifest))

    def test_source_exposes_model_sweeps_failure_recovery_and_bounds(self):
        self.assertEqual(p63_source_contract_errors(self.source), [])

    def test_source_contract_rejects_black_boxes_and_representative_mutants(self):
        for marker in (
            "validate_controls(controls);",
            "baseline_weights = baseline_scan_steering/number_elements;",
            "baseline_beam_outputs = baseline_weights'*baseline_sensor_data;",
            "scan_weight'*sample_covariance*scan_weight",
            "aligned_element_contributions = conj(aligned_weight).* ...",
            "assert(~separation_sweep_resolved(1) && ...",
            "assert(all(diff(snr_sweep_background_db) < 0), 'P63:SNRSweep', ...",
            "mirror_error = max(abs(broken_power-fliplr(recovered_power)));",
            "source_snapshots = reshape(exp(1j*2*pi*source_uniforms), ...",
            "noise = private_complex_noise(seed+1, maximum_elements, ...",
            "source_steering = exp(1j*2*pi*spacing_wavelengths* ...",
            "sensor_data = source_steering*source_snapshots+noise;",
            "steering = exp(1j*steering_sign*2*pi*spacing_wavelengths* ...",
            "beam_outputs = weights'*sensor_data;\n    power = mean(abs(beam_outputs).^2, 2).';",
            "samples = sqrt(-2*log(first)).*exp(1j*2*pi*second)/sqrt(2);",
            "noise = reshape(samples, number_rows, number_columns);",
            "peak_is_local(source_index) = selected_index > 1 && ...",
            "maximum_working_numeric_values = 500000;",
        ):
            with self.subTest(marker=marker):
                self.assertTrue(p63_source_contract_errors(self.source.replace(marker, "removed", 1)))
        self.assertTrue(p63_source_contract_errors(self.source + "\nphased.ULA(8)"))

    def test_controls_accept_reviewed_values_and_reject_malformed_inputs(self):
        controls = reviewed_controls()
        self.assertEqual(controls["elements"], 8)
        cases = (
            {"seed": 0},
            {"elements": True},
            {"elements": 1},
            {"elements": 8.5},
            {"elements": 17},
            {"spacing": 0.0},
            {"snr_db": float("nan")},
            {"source_angles": (-20.0, -20.0)},
            {"source_angles": (-61.0, 25.0)},
            {"snapshots": 128.5},
            {"scan_angles": ()},
            {"scan_angles": (-60.0, 0.0, -1.0, 60.0)},
            {"scan_angles": tuple(float(index) for index in range(2002))},
            {"separation_sweep": (6.0, 24.0, 12.0)},
            {"snr_sweep": (-15.0, -15.0, 15.0)},
            {"snapshot_sweep": (1, 8.5, 128)},
            {"broken_angles": (-20.0, 20.0)},
            {"max_private": 4095},
            {"max_values": 1000},
            {"max_figures": 6},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    reviewed_controls(**changes)
        with self.assertRaises(ValueError):
            reviewed_controls(unknown=1)

    def test_private_seed_is_exact_repeatable_isolated_and_bounded(self):
        expected = (
            0.049313952936471415,
            0.819603090323323,
            0.06913515113719514,
            0.9544812498867891,
        )
        first = private_uniform(6301, 4)
        second = private_uniform(6301, 4)
        for actual, wanted in zip(first, expected):
            self.assertAlmostEqual(actual, wanted, places=14)
        self.assertEqual(first, second)
        for seed, count in ((0, 4), (MODULUS, 4), (6301.5, 4), (6301, 0), (6301, 20001)):
            with self.subTest(seed=seed, count=count):
                with self.assertRaises(ValueError):
                    private_uniform(seed, count)

    def test_complex_noise_and_scene_fixture_bind_matlab_generator_layout(self):
        noise = private_complex_noise(6302, 16, 128)
        expected_noise = (
            (0, 0, 1.6536543696061154, -0.5242296733883073),
            (1, 0, -0.37518247599470733, 0.22786976460913552),
            (0, 1, 0.10593052337887736, 0.1011994824792398),
            (15, 127, -1.0383091512182963, -0.6913783392931689),
        )
        for row, column, real, imag in expected_noise:
            self.assertAlmostEqual(noise[row][column].real, real, places=14)
            self.assertAlmostEqual(noise[row][column].imag, imag, places=14)

        scene = simulate_scene(6301, 8, (-20.0, 25.0), 10.0, 128)
        expected_scene = (
            (0, 0, 1.8988326005929896, -0.7667474996468961),
            (1, 0, 1.5841861331686653, -0.42720964183653454),
            (0, 1, 1.9000047837799654, 0.17073867767465004),
            (7, 127, 0.1986434017796892, -0.3769143454661958),
        )
        for row, column, real, imag in expected_scene:
            self.assertAlmostEqual(scene[row][column].real, real, places=14)
            self.assertAlmostEqual(scene[row][column].imag, imag, places=14)

    def test_independent_baseline_oracle_peaks_and_covariance_identity(self):
        data = simulate_scene(6301, 8, (-20.0, 25.0), 10.0, 128)
        direct = scan_power(data, self.scan_angles)
        covariance = covariance_power(data, self.scan_angles)
        peaks = peak_near(self.scan_angles, direct, (-20.0, 25.0))
        self.assertAlmostEqual(peaks[0], -19.9, places=9)
        self.assertAlmostEqual(peaks[1], 25.0, places=9)
        self.assertLess(max(abs(left - right) for left, right in zip(direct, covariance)), 1e-12)

    def test_alignment_oracle_distinguishes_matched_and_mismatched_phases(self):
        source_angle = -20.0
        source = [
            cmath.exp(1j * 2 * math.pi * 0.5 * element * math.sin(math.radians(source_angle)))
            for element in range(8)
        ]
        aligned = [value.conjugate() * sample / 8 for value, sample in zip(source, source)]
        broadside = [1 / 8 for _ in range(8)]
        mismatched = [weight.conjugate() * sample for weight, sample in zip(broadside, source)]
        self.assertAlmostEqual(abs(sum(aligned)), 1.0, places=14)
        self.assertLess(abs(sum(mismatched)), 0.25)

    def test_source_separation_and_array_size_control_resolution(self):
        separation_peaks = []
        separation_local = []
        for separation in (6.0, 12.0, 24.0):
            angles = (-separation / 2, separation / 2)
            power = scan_power(simulate_scene(6311, 8, angles, 10.0, 128), self.scan_angles)
            peaks, local = peak_near_with_local(self.scan_angles, power, angles, 4.0)
            separation_peaks.append(peaks)
            separation_local.append(local)
        self.assertLess(separation_peaks[0][1] - separation_peaks[0][0], 1e-9)
        self.assertGreater(separation_peaks[-1][1] - separation_peaks[-1][0], 20)
        self.assertTrue(all(separation_local[-1]))

        array_peaks = []
        array_local = []
        for elements in (4, 8, 16):
            power = scan_power(simulate_scene(6312, elements, (-8.0, 8.0), 10.0, 128), self.scan_angles)
            peaks, local = peak_near_with_local(self.scan_angles, power, (-8.0, 8.0))
            array_peaks.append(peaks)
            array_local.append(local)
        self.assertLess(array_peaks[0][1] - array_peaks[0][0], 8)
        self.assertGreater(array_peaks[1][1] - array_peaks[1][0], 16)
        self.assertGreater(array_peaks[2][1] - array_peaks[2][0], 16)
        self.assertTrue(all(array_local[1]))
        self.assertTrue(all(array_local[2]))

    def test_resolution_rejects_disjoint_windows_on_one_broad_shoulder(self):
        scan_angles = (-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0)
        one_lobe = (0.1, 0.2, 0.4, 0.8, 1.0, 0.8, 0.4, 0.2, 0.1)
        peaks, local = peak_near_with_local(
            scan_angles, one_lobe, (-2.0, 2.0), 1.0
        )
        self.assertEqual(peaks, (-1.0, 1.0))
        self.assertEqual(local, (False, False))

    def test_snr_and_snapshot_sweeps_change_reliability_not_geometry(self):
        floors = []
        for snr in (-15.0, 0.0, 15.0):
            power = scan_power(simulate_scene(6313, 8, (-20.0, 25.0), snr, 128), self.scan_angles)
            floors.append(relative_background_db(self.scan_angles, power, (-20.0, 25.0))[0])
        self.assertTrue(all(right < left for left, right in zip(floors, floors[1:])))

        full = simulate_scene(6314, 8, (-20.0, 25.0), 0.0, 128)
        ripples = []
        for snapshots in (1, 8, 128):
            prefix = [row[:snapshots] for row in full]
            power = scan_power(prefix, self.scan_angles)
            ripples.append(relative_background_db(self.scan_angles, power, (-20.0, 25.0))[1])
        self.assertLess(ripples[-1], ripples[0])

    def test_repeating_one_plane_wave_preserves_scan_power_and_beam_shape(self):
        source_angle = 10.0
        one_snapshot = [
            [
                cmath.exp(
                    1j
                    * 2
                    * math.pi
                    * 0.5
                    * element
                    * math.sin(math.radians(source_angle))
                )
            ]
            for element in range(8)
        ]
        repeated_snapshots = [row * 128 for row in one_snapshot]

        one_look = scan_power(one_snapshot, self.scan_angles)
        many_look = scan_power(repeated_snapshots, self.scan_angles)
        self.assertLess(
            max(abs(left - right) for left, right in zip(one_look, many_look)),
            1e-12,
        )
        self.assertAlmostEqual(
            self.scan_angles[max(range(len(one_look)), key=one_look.__getitem__)],
            source_angle,
            places=9,
        )
        one_half_power = tuple(
            angle for angle, power in zip(self.scan_angles, one_look) if power >= 0.5 * max(one_look)
        )
        many_half_power = tuple(
            angle for angle, power in zip(self.scan_angles, many_look) if power >= 0.5 * max(many_look)
        )
        self.assertEqual(many_half_power, one_half_power)

    def test_broken_sign_mirrors_and_recovery_restores_unchanged_data(self):
        data = simulate_scene(6315, 8, (-20.0, 30.0), 10.0, 128)
        broken = scan_power(data, self.scan_angles, -1)
        recovered = scan_power(data, self.scan_angles, 1)
        broken_peaks = peak_near(self.scan_angles, broken, (-30.0, 20.0))
        recovered_peaks = peak_near(self.scan_angles, recovered, (-20.0, 30.0))
        self.assertLess(max(abs(left - right) for left, right in zip(broken, reversed(recovered))), 1e-12)
        for actual, expected in zip(broken_peaks, (-29.9, 20.1)):
            self.assertAlmostEqual(actual, expected, places=9)
        for actual, expected in zip(recovered_peaks, (-20.1, 29.9)):
            self.assertAlmostEqual(actual, expected, places=9)

    def test_oracles_reject_nonfinite_nonphysical_and_malformed_records(self):
        scene_cases = (
            (6301, 1, (-20.0, 25.0), 10.0, 128),
            (6301, 17, (-20.0, 25.0), 10.0, 128),
            (6301, 8, (-20.0,), 10.0, 128),
            (6301, 8, (-20.0, float("nan")), 10.0, 128),
            (6301, 8, (-20.0, 25.0), float("inf"), 128),
            (6301, 8, (-20.0, 25.0), 10.0, 0),
        )
        for args in scene_cases:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    simulate_scene(*args)
        scan_cases = (
            (None, self.scan_angles, 1),
            ([[1j], []], self.scan_angles, 1),
            ([[1j], [complex(float("nan"), 0)]], self.scan_angles, 1),
            ([[1j], [1j]], (), 1),
            ([[1j], [1j]], self.scan_angles, 0),
        )
        for args in scan_cases:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    scan_power(*args)
        with self.assertRaises(ValueError):
            peak_near((0.0,), (1.0, 2.0), (0.0,))

    def test_documents_are_concept_first_and_cover_limits_and_dependencies(self):
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        for document in (readme, lesson, walkthrough, checks):
            self.assertIn(QUESTION, document)
            self.assertNotIn("TODO", document)
        for marker in (
            "a_m(theta) = exp(j 2 pi m q sin(theta))",
            "X = A_s S + N",
            "y_theta[ell] = w(theta)^H x[ell]",
            "P_DAS(theta) = w(theta)^H Rhat w(theta)",
            "P_broken(theta) = P_correct(-theta)",
            "far-field",
            "narrowband",
            "P61",
            "P62",
            "P65",
            "P67",
        ):
            self.assertIn(marker, lesson)
        for marker in ("Sweep 1", "Sweep 2", "Broken case", "Recovery", "Ctrl+C"):
            self.assertIn(marker, walkthrough)
        self.assertIn("Short teach-back rubric", checks)
        self.assertGreaterEqual(checks.count("**Correct:**"), 32)

    def test_cli_timeout_isolation_rollback_recovery_and_future_compatibility(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        compatible = copy.deepcopy(self.manifest)
        p64 = next(module for module in compatible["modules"] if module["id"] == "P64")
        p64["future_extension"] = {"accepted": True}
        original_p62 = copy.deepcopy(next(module for module in compatible["modules"] if module["id"] == "P62"))
        original_p64 = copy.deepcopy(p64)
        with tempfile.TemporaryDirectory() as temp:
            fixture = self.make_cli_fixture(Path(temp), compatible)
            started = self.run_fixture_cli(fixture, "start", "63")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P63", started.stdout)
            self.assertIn("status: implemented", started.stdout)
            state_path = fixture / ".learning/progress.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P62",
                        "completed": [f"P{number:02d}" for number in range(1, 63)],
                        "notes": {"P62": "prerequisite complete"},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            advanced = self.run_fixture_cli(fixture, "start")
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertIn("P63 — Implement Conventional Delay-and-Sum Beamforming", advanced.stdout)
            rolled_back = copy.deepcopy(compatible)
            next(module for module in rolled_back["modules"] if module["id"] == "P63")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(
                json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8"
            )
            refused = self.run_fixture_cli(fixture, "start", "63")
            self.assertEqual(refused.returncode, 3, refused.stderr)
            self.assertIn("awaits Portfolio batch P63", refused.stdout)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P62"), original_p62)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P64"), original_p64)
            (fixture / "curriculum/modules.json").write_text(
                json.dumps(compatible, indent=2) + "\n", encoding="utf-8"
            )
            recovered = self.run_fixture_cli(fixture, "start", "63")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_cancellation_cleanup_has_no_external_or_persistent_side_effects(self):
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P63'));", self.source)
        self.assertNotIn("close all", self.source)
        for token in ("timer(", "parfor", "webread", "urlread", "fopen(", "save(", "system("):
            self.assertNotIn(token, self.source)
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        self.assertIn("Ctrl+C", walkthrough)
        self.assertIn("no background task, checkpoint, or partial output", walkthrough)

    def test_public_catalogs_describe_permanent_p63_facts(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 63 follows P62", readme)
        self.assertIn("Project 63 follows P62", start_here)
        self.assertIn(
            "| [P63](../modules/63-implement-conventional-delay-and-sum-beamforming/) | implemented | 7 |",
            module_index,
        )

    def test_retained_evidence_has_claim_boundary_commands_and_lifecycle_coverage(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P63-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        for marker in (
            "# P63 Retained Evidence",
            "## Acceptance map",
            "84 modules, 63 implemented",
            "## Deterministic simulated-oracle results",
            "## Figure and metric inventory",
            "## Exact commands and results",
            "python3 -m unittest tests.test_p63_module -v",
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
            "command -v matlab",
            "command -v octave",
            "No MATLAB runtime evidence was produced",
            "## Focused positive and negative coverage",
            "Malformed input",
            "Timeout guard",
            "Cancellation",
            "Rollback and recovery",
            "Isolation",
            "Compatibility",
            "Resource bounds",
            "## Changed and preserved invariants",
            "## Residual risks and known content gaps",
            "## Rollback",
            "## Unperformed validation",
            "Hardware/HIL",
            "RT1/RT2",
            "Unreal",
            "signing",
            "deployment",
            "production",
            "operator-provided `contracts/active-batch.yaml`",
            "operator-provided `contracts/repo-profile.yaml`",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, evidence)
        self.assertTrue(evidence.endswith("\n"))
        self.assertFalse(evidence.endswith("\n\n"))

    def test_changed_text_files_have_exactly_one_terminal_newline(self):
        paths = [MODULE / artifact for artifact in ARTIFACTS] + [
            ROOT / "README.md",
            ROOT / "START_HERE.md",
            ROOT / "modules/README.md",
            ROOT / "curriculum/modules.json",
            ROOT / "tests/test_p63_module.py",
            ROOT / "docs/evidence/P63-2026-08-05.md",
        ]
        for path in paths:
            with self.subTest(path=path):
                data = path.read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
