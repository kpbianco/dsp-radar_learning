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
MODULE = ROOT / "modules/67-inject-array-calibration-and-mutual-coupling-errors"
QUESTION = "How sensitive are beamforming and DOA results to imperfect channels?"
EXPECTED_IDENTITY = {
    "number": 67,
    "id": "P67",
    "title": "Inject Array Calibration and Mutual-Coupling Errors",
    "guiding_question": QUESTION,
    "phase": 7,
    "phase_title": "Arrays, Beamforming, DOA, and STAP",
    "slug": "inject-array-calibration-and-mutual-coupling-errors",
    "folder": "modules/67-inject-array-calibration-and-mutual-coupling-errors",
    "status": "implemented",
    "implementation_batch": "P67",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
SOURCE_MARKERS = (
    "baseline_seed = 6701;",
    "number_elements = 10;",
    "element_spacing_wavelengths = 0.5;",
    "source_angles_deg = [-15 10];",
    "interferer_inr_db = 25;",
    "desired_snr_db = 10;",
    "number_snapshots = 512;",
    "receiver_noise = private_complex_noise(baseline_seed+3, number_elements, ...",
    "calibration_angle_deg = 10;",
    "calibration_snr_db = 30;",
    "calibration_snapshots = 256;",
    "gain_error_rms_fraction = 0.18;",
    "phase_error_rms_deg = 20;",
    "position_error_rms_wavelengths = 0.05;",
    "coupling_magnitude = 0.18;",
    "error_scale_sweep = [0 0.25 0.5 0.75 1 1.25 1.5];",
    "coupling_magnitude_sweep = [0 0.05 0.10 0.15 0.20 0.25 0.30];",
    "array_error_matrix = diag(channel_gains)*coupling_matrix;",
    "source_powers = noise_power*10.^([interferer_inr_db desired_snr_db]/10);",
    "actual_source_steering = array_error_matrix*steering_matrix( ...",
    "actual_calibration_steering = array_error_matrix*steering_matrix( ...",
    "impaired_sensor_data = actual_source_steering* ...",
    "measured_calibration_response = calibration_sensor_data* ...",
    "estimated_channel_response = measured_calibration_response./ ...",
    "calibration_equalizer = diag(1./estimated_channel_response);",
    "calibrated_sensor_data = calibration_equalizer*impaired_sensor_data;",
    "'P67:CalibrationInvertibility'",
    "bartlett_power = real(sum(conj(scan_steering).* ...",
    "capon_solutions = loaded_covariance\\scan_steering;",
    "capon_power = 1./max(capon_denominator, realmin);",
    "noise_subspace = eigenvectors(:, source_count+1:end);",
    "noise_whitener = noise_vectors*diag(1./sqrt(noise_values))*noise_vectors';",
    "whitened_scan_steering = noise_whitener*scan_steering;",
    "scan_steering, diagonal_loading_alpha, plot_floor_db, ...\n    calibrated_noise_covariance);",
    "diagonal_loading_alpha, plot_floor_db, ...\n        noise_power*case_equalizer*case_equalizer');",
    "music_power = 1./max(music_denominator, realmin);",
    "wrong_reference_equalizer = diag(1./measured_calibration_response);",
    "calibrated_noise_covariance = noise_power*calibration_equalizer* ...",
    "calibrated_source_steering, source_powers, calibrated_noise_covariance);",
    "known_response_after_db > known_response_before_db+8",
    "case_error_matrix = diag(case_gains)*coupling_matrix;",
    "case_error_matrix = diag(channel_gains)*case_coupling;",
    "after_data = equalizer*before_data;",
    "maximum_elements = 16;",
    "maximum_sources = 3;",
    "maximum_snapshots = 512;",
    "maximum_calibration_snapshots = 512;",
    "maximum_scan_samples = 1001;",
    "maximum_sweep_cases = 8;",
    "maximum_private_values = 30000;",
    "maximum_working_numeric_values = 1000000;",
    "maximum_figures = 6;",
    "validate_controls(controls);",
    "preflight_working_value_bound = ...",
    "'P67:PreflightWorkingBound'",
    "assert(working_value_count <= maximum_working_numeric_values, ...",
    "'P67:WorkingBound'",
    "c.calibration_angle == c.source_angles(2)",
    "numel(c.scan_angles) >= 2*c.assumed_sources+1",
    "c.scan_angles(1) < c.source_angles(1)",
    "c.scan_angles(end) > c.source_angles(end)",
    "c.max_figures == 6 && c.seed <= 2147483641",
    "state = mod(16807*state, 2147483647);",
    "function validate_controls(c)\n    scalar_names = {'seed', 'elements', 'spacing', 'interferer_inr_db', ...",
    "p67_results = struct( ...",
    "close(findall(0, 'Type', 'figure', 'Tag', 'P67'));",
    "clear p67_results;",
    "samples = sqrt(-2*log(first)).*exp(1j*2*pi*second)/sqrt(2);",
    "noise = reshape(samples, number_rows, number_columns);",
)
SOURCE_MARKER_MIN_COUNTS = {
    "diagonal_loading_alpha, plot_floor_db, ...\n        noise_power*case_equalizer*case_equalizer');": 2,
}
FORBIDDEN_SOURCE_TOKENS = (
    "phased.",
    "phased.MUSICEstimator",
    "musicdoa(",
    "rootmusic(",
    "mvdrweights(",
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
    "clear all",
    "clearvars",
    "delete(",
    "websave",
    "unix(",
    "dos(",
    "close all",
)
MODULUS = 2_147_483_647
MULTIPLIER = 16_807


def finite_real(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def p67_source_contract_errors(source: object) -> list[str]:
    if not isinstance(source, str) or not source:
        return ["P67 source must be nonempty text"]
    errors = [f"missing source marker: {marker}" for marker in SOURCE_MARKERS if marker not in source]
    errors.extend(
        f"insufficient source marker count: {marker}"
        for marker, minimum in SOURCE_MARKER_MIN_COUNTS.items()
        if source.count(marker) < minimum
    )
    if source.count("figure('Name', 'P67") != 6:
        errors.append("P67 must create exactly six named figures")
    if source.count("'Tag', 'P67'") != 7:
        errors.append("P67 must tag six figures and one scoped cleanup")
    errors.extend(f"forbidden source token: {token}" for token in FORBIDDEN_SOURCE_TOKENS if token in source)
    if re.search(r"(?m)^\s*(?:save|delete|unix|dos)\s+[^=(]", source, re.IGNORECASE):
        errors.append("forbidden command-form external side effect")
    if re.search(r"(?m)^\s*!", source):
        errors.append("forbidden shell escape")
    return errors


def validate_p67_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P67 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [
        entry for entry in manifest["modules"]
        if isinstance(entry, dict) and entry.get("id") == "P67"
    ]
    if len(matches) != 1:
        errors.append("P67 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P67 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P67 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P67 empty {artifact}")
    return errors


def reviewed_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "seed": 6701,
        "elements": 10,
        "spacing": 0.5,
        "source_angles": (-15.0, 10.0),
        "interferer_inr_db": 25.0,
        "desired_snr_db": 10.0,
        "noise_power": 1.0,
        "snapshots": 512,
        "calibration_angle": 10.0,
        "calibration_snr_db": 30.0,
        "calibration_snapshots": 256,
        "gain_error_rms": 0.18,
        "phase_error_rms_deg": 20.0,
        "position_error_rms": 0.05,
        "coupling_magnitude": 0.18,
        "coupling_phase_deg": 25.0,
        "next_neighbor_scale": 0.30,
        "loading_alpha": 0.02,
        "assumed_sources": 2,
        "scan_angles": tuple(-40.0 + 0.1 * index for index in range(801)),
        "minimum_peak_separation": 2.0,
        "error_scale_sweep": (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5),
        "coupling_sweep": (0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30),
        "plot_floor_db": -60.0,
        "max_elements": 16,
        "max_sources": 3,
        "max_snapshots": 512,
        "max_calibration_snapshots": 512,
        "max_scan_samples": 1001,
        "max_sweep_cases": 8,
        "max_private_values": 30000,
        "max_working_values": 1000000,
        "max_figures": 6,
    }
    controls.update(overrides)
    return controls


def validate_sweep(values: object, low: float, high: float) -> None:
    if not isinstance(values, (tuple, list)) or not 3 <= len(values) <= 8:
        raise ValueError("sweep shape")
    if not all(finite_real(value) for value in values):
        raise ValueError("sweep finite")
    if any(right <= left for left, right in zip(values, values[1:])):
        raise ValueError("sweep order")
    if values[0] < low or values[-1] > high:
        raise ValueError("sweep range")


def validate_controls(controls: object) -> None:
    if not isinstance(controls, dict) or set(controls) != set(reviewed_controls()):
        raise ValueError("controls")
    sequences = {"source_angles", "scan_angles", "error_scale_sweep", "coupling_sweep"}
    if not all(finite_real(value) for key, value in controls.items() if key not in sequences):
        raise ValueError("finite scalar")
    integer_names = {
        "seed", "elements", "snapshots", "calibration_snapshots", "assumed_sources",
        "max_elements", "max_sources", "max_snapshots", "max_calibration_snapshots",
        "max_scan_samples", "max_sweep_cases", "max_private_values",
        "max_working_values", "max_figures",
    }
    if not all(integer(controls[name]) and controls[name] > 0 for name in integer_names):
        raise ValueError("integer")
    angles = controls["source_angles"]
    if (
        not isinstance(angles, (tuple, list))
        or len(angles) != controls["assumed_sources"]
        or len(angles) > controls["max_sources"]
        or not all(finite_real(angle) and abs(angle) < 90 for angle in angles)
        or any(right <= left for left, right in zip(angles, angles[1:]))
    ):
        raise ValueError("source angles")
    scan = controls["scan_angles"]
    if (
        not isinstance(scan, (tuple, list))
        or not 2 * controls["assumed_sources"] + 1 <= len(scan) <= controls["max_scan_samples"]
        or not all(finite_real(value) and abs(value) < 90 for value in scan)
        or any(right <= left for left, right in zip(scan, scan[1:]))
        or scan[0] >= angles[0]
        or scan[-1] <= angles[-1]
    ):
        raise ValueError("scan")
    validate_sweep(controls["error_scale_sweep"], 0.0, 2.0)
    validate_sweep(controls["coupling_sweep"], 0.0, 0.35)
    if not (
        controls["elements"] <= controls["max_elements"]
        and controls["assumed_sources"] == 2
        and controls["assumed_sources"] < controls["elements"]
        and controls["snapshots"] <= controls["max_snapshots"]
        and controls["calibration_snapshots"] <= controls["max_calibration_snapshots"]
        and 0 < controls["spacing"] <= 0.5
        and 0 < controls["noise_power"] <= 1e6
        and 0 <= controls["gain_error_rms"] <= 0.30
        and 0 <= controls["phase_error_rms_deg"] <= 45
        and 0 <= controls["position_error_rms"] <= 0.10
        and 0 <= controls["coupling_magnitude"] <= 0.35
        and 0 <= controls["next_neighbor_scale"] <= 0.5
        and 0 < controls["loading_alpha"] <= 1
        and abs(controls["interferer_inr_db"]) <= 60
        and abs(controls["desired_snr_db"]) <= 60
        and abs(controls["calibration_snr_db"]) <= 80
        and controls["calibration_angle"] == angles[1]
        and 0 < controls["minimum_peak_separation"] <= 10
        and -200 <= controls["plot_floor_db"] <= -10
    ):
        raise ValueError("physical bounds")
    immutable = {
        "max_elements": 16,
        "max_sources": 3,
        "max_snapshots": 512,
        "max_calibration_snapshots": 512,
        "max_scan_samples": 1001,
        "max_sweep_cases": 8,
        "max_private_values": 30000,
        "max_working_values": 1000000,
        "max_figures": 6,
    }
    if any(controls[name] != value for name, value in immutable.items()):
        raise ValueError("immutable ceiling")
    if controls["seed"] > MODULUS - 6:
        raise ValueError("derived seed")
    if 2 * controls["elements"] * max(controls["snapshots"], controls["calibration_snapshots"]) > controls["max_private_values"]:
        raise ValueError("private bound")


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
    return [[samples[column * int(rows) + row] for column in range(int(columns))] for row in range(int(rows))]


def unit_rms(values: list[float]) -> list[float]:
    mean = sum(values) / len(values)
    centered = [value - mean for value in values]
    rms = math.sqrt(sum(value * value for value in centered) / len(centered))
    if not math.isfinite(rms) or rms <= 0:
        raise ValueError("pattern")
    return [value / rms for value in centered]


def steering(angle_deg: float, positions: list[float]) -> list[complex]:
    return [
        cmath.exp(1j * 2 * math.pi * position * math.sin(math.radians(angle_deg)))
        for position in positions
    ]


def coupling_matrix(elements: int, magnitude: float, phase_deg: float = 25.0, next_scale: float = 0.30) -> list[list[complex]]:
    matrix = [[1 + 0j if row == column else 0j for column in range(elements)] for row in range(elements)]
    nearest = magnitude * cmath.exp(1j * math.radians(phase_deg))
    next_nearest = next_scale * nearest**2
    for row in range(elements - 1):
        matrix[row][row + 1] = nearest
        matrix[row + 1][row] = nearest
    for row in range(elements - 2):
        matrix[row][row + 2] = next_nearest
        matrix[row + 2][row] = next_nearest
    return matrix


def matrix_vector(matrix: list[list[complex]], vector: list[complex]) -> list[complex]:
    return [sum(value * vector[column] for column, value in enumerate(row)) for row in matrix]


def covariance(data: list[list[complex]]) -> list[list[complex]]:
    rows = len(data)
    columns = len(data[0])
    return [
        [
            sum(data[row][look] * data[column][look].conjugate() for look in range(columns)) / columns
            for column in range(rows)
        ]
        for row in range(rows)
    ]


def orthonormalize(columns: list[list[complex]]) -> list[list[complex]]:
    result: list[list[complex]] = []
    for column in columns:
        working = list(column)
        for basis in result:
            projection = conjugate_dot(basis, working)
            working = [
                value - projection * basis_value
                for value, basis_value in zip(working, basis)
            ]
        magnitude = norm(working)
        if magnitude < 1e-14:
            raise ValueError("dependent subspace iteration")
        result.append([value / magnitude for value in working])
    return result


def dominant_subspace(
    matrix: list[list[complex]], count: int, iterations: int = 350
) -> list[list[complex]]:
    size = len(matrix)
    columns = [
        [
            cmath.exp(1j * 2 * math.pi * row * column / size) / math.sqrt(size)
            for row in range(size)
        ]
        for column in range(count)
    ]
    for _ in range(iterations):
        columns = orthonormalize(
            [matrix_vector(matrix, column) for column in columns]
        )
    return columns


def music_peaks(
    data: list[list[complex]],
    scan: tuple[float, ...],
    whitening_scales: list[float] | None = None,
    peak_count: int = 2,
    minimum_separation_deg: float = 2.0,
) -> list[float]:
    elements = len(data)
    scales = whitening_scales or [1.0] * elements
    whitened_data = [
        [scales[row] * value for value in sensor_record]
        for row, sensor_record in enumerate(data)
    ]
    signal_subspace = dominant_subspace(covariance(whitened_data), peak_count)
    positions = [0.5 * index for index in range(elements)]
    power = []
    for angle in scan:
        candidate = elementwise(scales, steering(angle, positions))
        signal_projection = sum(
            abs(conjugate_dot(basis, candidate)) ** 2
            for basis in signal_subspace
        )
        noise_projection = max(
            conjugate_dot(candidate, candidate).real - signal_projection,
            float.fromhex("0x0.0000000000001p-1022"),
        )
        power.append(1 / noise_projection)

    candidates = [
        index
        for index in range(1, len(scan) - 1)
        if power[index] > power[index - 1]
        and power[index] >= power[index + 1]
    ]
    candidates.sort(key=power.__getitem__, reverse=True)
    selected: list[int] = []
    for index in candidates:
        if all(
            abs(scan[index] - scan[prior]) >= minimum_separation_deg
            for prior in selected
        ):
            selected.append(index)
        if len(selected) == peak_count:
            break
    if len(selected) != peak_count:
        raise ValueError("peak count")
    return sorted(scan[index] for index in selected)


def solve(matrix: list[list[complex]], vector: list[complex]) -> list[complex]:
    size = len(vector)
    augmented = [list(row) + [value] for row, value in zip(matrix, vector)]
    for pivot_column in range(size):
        pivot_row = max(range(pivot_column, size), key=lambda row: abs(augmented[row][pivot_column]))
        if abs(augmented[pivot_row][pivot_column]) < 1e-14:
            raise ValueError("singular")
        augmented[pivot_column], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_column]
        pivot = augmented[pivot_column][pivot_column]
        augmented[pivot_column] = [value / pivot for value in augmented[pivot_column]]
        for row in range(size):
            if row == pivot_column:
                continue
            factor = augmented[row][pivot_column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[pivot_column])
            ]
    return [augmented[row][-1] for row in range(size)]


def mvdr_weight(data: list[list[complex]], look: list[complex], alpha: float = 0.02) -> list[complex]:
    matrix = covariance(data)
    average_power = sum(matrix[index][index].real for index in range(len(matrix))) / len(matrix)
    loaded = [
        [value + (alpha * average_power if row == column else 0) for column, value in enumerate(line)]
        for row, line in enumerate(matrix)
    ]
    numerator = solve(loaded, look)
    denominator = conjugate_dot(look, numerator)
    return [value / denominator for value in numerator]


def capon_peaks(
    data: list[list[complex]],
    scan: tuple[float, ...],
    peak_count: int = 2,
    minimum_separation_deg: float = 2.0,
    alpha: float = 0.02,
) -> list[float]:
    matrix = covariance(data)
    elements = len(matrix)
    average_power = sum(matrix[index][index].real for index in range(elements)) / elements
    loaded = [
        [value + (alpha * average_power if row == column else 0) for column, value in enumerate(line)]
        for row, line in enumerate(matrix)
    ]
    positions = [0.5 * index for index in range(elements)]
    power = []
    for angle in scan:
        look = steering(angle, positions)
        solution = solve(loaded, look)
        denominator = conjugate_dot(look, solution).real
        power.append(1 / max(denominator, float.fromhex("0x0.0000000000001p-1022")))

    candidates = [
        index for index in range(1, len(scan) - 1)
        if power[index] > power[index - 1] and power[index] >= power[index + 1]
    ]
    candidates.sort(key=power.__getitem__, reverse=True)
    selected: list[int] = []
    for index in candidates:
        if all(abs(scan[index] - scan[prior]) >= minimum_separation_deg for prior in selected):
            selected.append(index)
        if len(selected) == peak_count:
            break
    if len(selected) != peak_count:
        raise ValueError("peak count")
    return sorted(scan[index] for index in selected)


def elementwise(left: list[complex], right: list[complex]) -> list[complex]:
    return [a * b for a, b in zip(left, right)]


def conjugate_dot(left: list[complex], right: list[complex]) -> complex:
    return sum(value.conjugate() * other for value, other in zip(left, right))


def norm(vector: list[complex]) -> float:
    return math.sqrt(max(conjugate_dot(vector, vector).real, 0.0))


def reviewed_array(scale: float = 1.0, coupling: float = 0.18) -> tuple[list[float], list[complex], list[list[complex]]]:
    values = private_uniform(6701, 30)
    gain = unit_rms([2 * value - 1 for value in values[:10]])
    phase = unit_rms([2 * value - 1 for value in values[10:20]])
    position = unit_rms([2 * value - 1 for value in values[20:]])
    nominal_positions = [0.5 * index for index in range(10)]
    actual_positions = [p + scale * 0.05 * e for p, e in zip(nominal_positions, position)]
    gains = [
        (1 + scale * 0.18 * ge) * cmath.exp(1j * math.radians(scale * 20 * pe))
        for ge, pe in zip(gain, phase)
    ]
    return actual_positions, gains, coupling_matrix(10, coupling)


def physical_response(angle_deg: float, scale: float = 1.0, coupling: float = 0.18) -> list[complex]:
    positions, gains, coupling = reviewed_array(scale, coupling)
    return elementwise(gains, matrix_vector(coupling, steering(angle_deg, positions)))


def exact_equalizer(calibration_angle: float = 10.0, scale: float = 1.0, coupling: float = 0.18) -> list[complex]:
    nominal = steering(calibration_angle, [0.5 * index for index in range(10)])
    measured = physical_response(calibration_angle, scale, coupling)
    return [reference / actual for reference, actual in zip(nominal, measured)]


def scan_peak(vector: list[complex], scan: tuple[float, ...]) -> float:
    positions = [0.5 * index for index in range(10)]
    responses = [abs(conjugate_dot(vector, steering(angle, positions))) for angle in scan]
    return scan[max(range(len(scan)), key=responses.__getitem__)]


def finite_record_calibration() -> tuple[
    list[list[complex]],
    tuple[float, float],
    list[list[complex]],
    list[list[complex]],
    list[complex],
    list[complex],
]:
    elements = 10
    snapshots = 512
    calibration_snapshots = 256
    angles = (-15.0, 10.0)
    powers = (10 ** 2.5, 10 ** 1.0)
    amplitudes = tuple(math.sqrt(value) for value in powers)
    responses = [physical_response(angle) for angle in angles]
    waveforms = [
        [cmath.exp(1j * 2 * math.pi * value) for value in private_uniform(seed, snapshots)]
        for seed in (6702, 6703)
    ]
    receiver_noise = private_complex_noise(6704, elements, snapshots)
    impaired = [
        [
            sum(responses[source][row] * amplitudes[source] * waveforms[source][column] for source in range(2))
            + receiver_noise[row][column]
            for column in range(snapshots)
        ]
        for row in range(elements)
    ]
    pilot = [
        cmath.exp(1j * 2 * math.pi * value)
        for value in private_uniform(6705, calibration_snapshots)
    ]
    calibration_noise = private_complex_noise(6706, elements, calibration_snapshots)
    calibration_amplitude = math.sqrt(10 ** 3.0)
    measured = [
        sum(
            (responses[1][row] * calibration_amplitude * pilot[column] + calibration_noise[row][column])
            * pilot[column].conjugate()
            for column in range(calibration_snapshots)
        ) / calibration_snapshots / calibration_amplitude
        for row in range(elements)
    ]
    nominal = steering(10.0, [0.5 * index for index in range(elements)])
    equalizer = [reference / actual for reference, actual in zip(nominal, measured)]
    calibrated = [
        [equalizer[row] * value for value in impaired[row]]
        for row in range(elements)
    ]
    return responses, powers, impaired, calibrated, equalizer, nominal


class P67ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.scan = tuple(-40.0 + 0.1 * index for index in range(801))

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
        self.assertEqual(validate_p67_contract(ROOT, self.manifest), [])
        p66 = next(module for module in self.manifest["modules"] if module["id"] == "P66")
        self.assertEqual(p66["status"], "implemented")

    def test_contract_rejects_malformed_duplicate_drift_missing_and_empty(self):
        self.assertTrue(validate_p67_contract(ROOT, None))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append(None)
        self.assertIn("every manifest module must be an object", validate_p67_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("P67 must have exactly one manifest entry", validate_p67_contract(ROOT, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(module for module in drifted["modules"] if module["id"] == "P67")["guiding_question"] = "changed"
        self.assertIn("P67 manifest identity drift", validate_p67_contract(ROOT, drifted))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(MODULE, root / EXPECTED_IDENTITY["folder"])
            (root / EXPECTED_IDENTITY["folder"] / "lesson.md").unlink()
            self.assertIn("P67 missing lesson.md", validate_p67_contract(root, self.manifest))
            (root / EXPECTED_IDENTITY["folder"] / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P67 empty lesson.md", validate_p67_contract(root, self.manifest))

    def test_source_exposes_impairments_algorithms_sweeps_recovery_and_bounds(self):
        self.assertEqual(p67_source_contract_errors(self.source), [])
        for marker in SOURCE_MARKERS:
            with self.subTest(marker=marker):
                self.assertTrue(p67_source_contract_errors(self.source.replace(marker, "removed", 1)))
        self.assertTrue(p67_source_contract_errors(self.source + "\nphased.MUSICEstimator"))
        for unsafe in ("\nclear all", "\nclearvars", "\ndelete('x')", "\nwebsave('x','y')", "\n!touch x", "\nsave output.mat data"):
            with self.subTest(unsafe=unsafe):
                self.assertTrue(p67_source_contract_errors(self.source + unsafe))

    def test_control_contract_accepts_alternates_and_rejects_malformed_values(self):
        validate_controls(reviewed_controls())
        validate_controls(reviewed_controls(
            scan_angles=(-35.0, -15.0, 0.0, 10.0, 35.0),
            error_scale_sweep=(0.0, 0.5, 1.0),
            coupling_sweep=(0.0, 0.10, 0.25),
        ))
        mutations = (
            {"elements": True},
            {"snapshots": 512.5},
            {"calibration_snr_db": float("nan")},
            {"seed": MODULUS - 5},
            {"noise_power": 1e308},
            {"spacing": 0.75},
            {"source_angles": (-15.0, -15.0)},
            {"source_angles": (10.0, -15.0)},
            {"assumed_sources": 3, "source_angles": (-15.0, 0.0, 10.0)},
            {"calibration_angle": 5.0},
            {"calibration_angle": -15.0},
            {"scan_angles": (-15.0, 0.0, 10.0)},
            {"scan_angles": (-20.0, -15.0, 0.0, 10.0)},
            {"scan_angles": (-40.0, 0.0, 0.0, 40.0)},
            {"scan_angles": (-100.0, 0.0, 100.0)},
            {"error_scale_sweep": (0.0, 1.0, 0.5)},
            {"error_scale_sweep": (0.0, 1.0, 2.5)},
            {"coupling_sweep": (0.0, float("inf"), 0.3)},
            {"coupling_sweep": (0.0, 0.2, 0.4)},
            {"gain_error_rms": 0.5},
            {"phase_error_rms_deg": 60.0},
            {"position_error_rms": 0.2},
            {"coupling_magnitude": 0.5},
            {"loading_alpha": 0.0},
            {"minimum_peak_separation": 0.0},
            {"plot_floor_db": -500.0},
            {"max_elements": 32},
            {"max_sources": 4},
            {"max_snapshots": 1024},
            {"max_calibration_snapshots": 1024},
            {"max_scan_samples": 2001},
            {"max_sweep_cases": 16},
            {"max_private_values": 100},
            {"max_working_values": 2000000},
            {"max_figures": 7},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_controls(reviewed_controls(**mutation))
        with self.assertRaises(ValueError):
            validate_controls({})

    def test_private_generator_repeatability_layout_isolation_and_bounds(self):
        expected = (
            0.05244450040741102,
            0.4347183473569892,
            0.31126402891765537,
            0.4145340190336732,
        )
        actual = private_uniform(6701, 4)
        for observed, wanted in zip(actual, expected):
            self.assertAlmostEqual(observed, wanted, places=15)
        self.assertEqual(actual, private_uniform(6701, 4))
        for invalid in (True, 0, MODULUS, float("nan")):
            with self.assertRaises(ValueError):
                private_uniform(invalid, 4)
        for invalid in (0, 1.5, 30001):
            with self.assertRaises(ValueError):
                private_uniform(6701, invalid)
        before = private_uniform(123, 8)
        private_complex_noise(6704, 10, 512)
        self.assertEqual(before, private_uniform(123, 8))
        noise = private_complex_noise(6704, 10, 512)
        self.assertAlmostEqual(noise[0][0].real, -1.713299779998622, places=14)
        self.assertAlmostEqual(noise[9][511].imag, 0.6242392797159259, places=14)

    def test_independent_oracle_known_direction_is_restored(self):
        nominal = steering(10.0, [0.5 * index for index in range(10)])
        physical = physical_response(10.0)
        equalizer = exact_equalizer()
        corrected = elementwise(equalizer, physical)
        before_error = norm([value - reference for value, reference in zip(physical, nominal)]) / norm(nominal)
        after_error = norm([value - reference for value, reference in zip(corrected, nominal)]) / norm(nominal)
        self.assertGreater(before_error, 0.4)
        self.assertLess(after_error, 1e-12)
        self.assertAlmostEqual(scan_peak(corrected, self.scan), 10.0, places=12)

    def test_independent_oracle_calibration_improves_physical_pattern(self):
        positions = [0.5 * index for index in range(10)]
        nominal_look = steering(10.0, positions)
        equalizer = exact_equalizer()
        ideal_pattern = []
        impaired_pattern = []
        calibrated_pattern = []
        for angle in self.scan:
            ideal = steering(angle, positions)
            physical = physical_response(angle)
            corrected = elementwise(equalizer, physical)
            ideal_pattern.append(abs(conjugate_dot(nominal_look, ideal)) / 10)
            impaired_pattern.append(abs(conjugate_dot(nominal_look, physical)) / 10)
            calibrated_pattern.append(abs(conjugate_dot(nominal_look, corrected)) / 10)
        impaired_rms = math.sqrt(sum((actual - ideal) ** 2 for actual, ideal in zip(impaired_pattern, ideal_pattern)) / len(self.scan))
        calibrated_rms = math.sqrt(sum((actual - ideal) ** 2 for actual, ideal in zip(calibrated_pattern, ideal_pattern)) / len(self.scan))
        self.assertLess(calibrated_rms, impaired_rms * 0.8)

    def test_finite_record_mvdr_recovery_satisfies_reviewed_runtime_assertion(self):
        responses, _, impaired, calibrated, equalizer, nominal = finite_record_calibration()
        before_weight = mvdr_weight(impaired, nominal)
        after_weight = mvdr_weight(calibrated, nominal)
        before_response_db = 20 * math.log10(abs(conjugate_dot(before_weight, responses[1])))
        corrected_known = elementwise(equalizer, responses[1])
        after_response_db = 20 * math.log10(abs(conjugate_dot(after_weight, corrected_known)))
        improvement_db = after_response_db - before_response_db
        self.assertAlmostEqual(before_response_db, -8.5249380943, places=8)
        self.assertAlmostEqual(after_response_db, 0.0019106930, places=8)
        self.assertGreater(improvement_db, 8.0)
        self.assertLess(improvement_db, 9.0)

    def test_finite_record_wrong_reference_corrupts_capon_and_same_data_recovers(self):
        _, _, impaired, calibrated, equalizer, nominal = finite_record_calibration()
        measured = [reference / correction for reference, correction in zip(nominal, equalizer)]
        wrong = [
            [value / measured[row] for value in sensor_record]
            for row, sensor_record in enumerate(impaired)
        ]

        impaired_peaks = capon_peaks(impaired, self.scan)
        calibrated_peaks = capon_peaks(calibrated, self.scan)
        wrong_peaks = capon_peaks(wrong, self.scan)
        for observed, expected in zip(impaired_peaks, (-15.2, 9.7)):
            self.assertAlmostEqual(observed, expected, places=12)
        for observed, expected in zip(calibrated_peaks, (-14.8, 10.0)):
            self.assertAlmostEqual(observed, expected, places=12)
        for observed, expected in zip(wrong_peaks, (-25.4, 0.0)):
            self.assertAlmostEqual(observed, expected, places=12)

        calibrated_rmse = math.sqrt(sum(
            (observed - truth) ** 2
            for observed, truth in zip(calibrated_peaks, (-15.0, 10.0))
        ) / 2)
        wrong_rmse = math.sqrt(sum(
            (observed - truth) ** 2
            for observed, truth in zip(wrong_peaks, (-15.0, 10.0))
        ) / 2)
        self.assertLess(calibrated_rmse, 0.2)
        self.assertGreater(wrong_rmse, 10.0)

    def test_finite_record_calibrated_sinr_uses_colored_receiver_noise(self):
        responses, powers, _, calibrated, equalizer, nominal = finite_record_calibration()
        weight = mvdr_weight(calibrated, nominal)
        corrected_responses = [
            abs(conjugate_dot(weight, elementwise(equalizer, response))) ** 2
            for response in responses
        ]
        desired_power = powers[1] * corrected_responses[1]
        interference_power = powers[0] * corrected_responses[0]
        colored_noise_power = sum(
            abs(coefficient) ** 2 * abs(weight_value) ** 2
            for coefficient, weight_value in zip(equalizer, weight)
        )
        incorrectly_white_noise_power = sum(abs(value) ** 2 for value in weight)
        whitened_noise_diagonal = [
            abs(coefficient) ** -2 * abs(coefficient) ** 2
            for coefficient in equalizer
        ]
        colored_sinr_db = 10 * math.log10(
            desired_power / (interference_power + colored_noise_power)
        )
        incorrectly_white_sinr_db = 10 * math.log10(
            desired_power / (interference_power + incorrectly_white_noise_power)
        )

        self.assertAlmostEqual(colored_noise_power, 0.07057348856777898, places=13)
        self.assertAlmostEqual(colored_sinr_db, 20.80705003502867, places=11)
        self.assertAlmostEqual(incorrectly_white_sinr_db, 19.354574787305697, places=11)
        self.assertGreater(abs(colored_sinr_db - incorrectly_white_sinr_db), 1.4)
        for value in whitened_noise_diagonal:
            self.assertAlmostEqual(value, 1.0, places=14)
        self.assertIn(
            "calibrated_source_steering, source_powers, calibrated_noise_covariance);",
            self.source,
        )

    def test_finite_record_whitened_music_recovers_and_wrong_reference_fails(self):
        _, _, impaired, calibrated, equalizer, nominal = finite_record_calibration()
        calibrated_whitener = [1 / abs(value) for value in equalizer]
        impaired_peaks = music_peaks(impaired, self.scan)
        unwhitened_calibrated_peaks = music_peaks(calibrated, self.scan)
        calibrated_peaks = music_peaks(
            calibrated, self.scan, calibrated_whitener
        )

        measured = [
            reference / correction
            for reference, correction in zip(nominal, equalizer)
        ]
        wrong_equalizer = [1 / value for value in measured]
        wrong = [
            [wrong_equalizer[row] * value for value in sensor_record]
            for row, sensor_record in enumerate(impaired)
        ]
        wrong_peaks = music_peaks(
            wrong,
            self.scan,
            [1 / abs(value) for value in wrong_equalizer],
        )

        for observed, expected in zip(impaired_peaks, (-15.2, 9.7)):
            self.assertAlmostEqual(observed, expected, places=12)
        for observed, expected in zip(unwhitened_calibrated_peaks, (-14.8, 10.0)):
            self.assertAlmostEqual(observed, expected, places=12)
        for observed, expected in zip(calibrated_peaks, (-14.9, 10.0)):
            self.assertAlmostEqual(observed, expected, places=12)
        for observed, expected in zip(wrong_peaks, (-25.5, 0.0)):
            self.assertAlmostEqual(observed, expected, places=12)

        calibrated_rmse = math.sqrt(sum(
            (observed - truth) ** 2
            for observed, truth in zip(calibrated_peaks, (-15.0, 10.0))
        ) / 2)
        wrong_rmse = math.sqrt(sum(
            (observed - truth) ** 2
            for observed, truth in zip(wrong_peaks, (-15.0, 10.0))
        ) / 2)
        self.assertLess(calibrated_rmse, 0.1)
        self.assertGreater(wrong_rmse, 10.0)
        self.assertNotEqual(calibrated_peaks, unwhitened_calibrated_peaks)

    def test_one_look_calibration_leaves_coupling_dependent_off_angle_residual(self):
        nominal_off_angle = steering(-15.0, [0.5 * index for index in range(10)])
        residuals = []
        for coupling in (0.0, 0.10, 0.20, 0.30):
            equalizer = exact_equalizer(coupling=coupling)
            corrected = elementwise(equalizer, physical_response(-15.0, coupling=coupling))
            residuals.append(norm([value - reference for value, reference in zip(corrected, nominal_off_angle)]) / norm(nominal_off_angle))
            known = elementwise(equalizer, physical_response(10.0, coupling=coupling))
            self.assertLess(norm([value - reference for value, reference in zip(known, steering(10.0, [0.5 * index for index in range(10)]))]), 1e-12)
        self.assertGreater(residuals[-1], residuals[0])
        self.assertTrue(all(math.isfinite(value) and value > 0 for value in residuals))

    def test_sweep_oracle_changes_only_the_declared_array_cause(self):
        baseline_positions, baseline_gains, baseline_coupling = reviewed_array()
        mild_positions, mild_gains, mild_coupling = reviewed_array(scale=0.5)
        changed_positions, changed_gains, changed_coupling = reviewed_array(coupling=0.30)
        self.assertEqual(mild_coupling, baseline_coupling)
        self.assertNotEqual(mild_positions, baseline_positions)
        self.assertNotEqual(mild_gains, baseline_gains)
        self.assertEqual(changed_positions, baseline_positions)
        self.assertEqual(changed_gains, baseline_gains)
        self.assertNotEqual(changed_coupling, baseline_coupling)
        self.assertNotEqual(physical_response(10.0, scale=0.5), physical_response(10.0))
        self.assertNotEqual(physical_response(10.0, coupling=0.30), physical_response(10.0))

    def test_wrong_broadside_reference_breaks_and_same_data_model_recovers(self):
        physical = physical_response(10.0)
        wrong_equalizer = [1 / value for value in physical]
        wrong = elementwise(wrong_equalizer, physical)
        corrected = elementwise(exact_equalizer(), physical)
        self.assertLess(norm([value - 1 for value in wrong]), 1e-12)
        self.assertAlmostEqual(scan_peak(wrong, self.scan), 0.0, places=12)
        self.assertAlmostEqual(scan_peak(corrected, self.scan), 10.0, places=12)

    def test_power_and_voltage_db_conventions_and_noise_accounting(self):
        self.assertIn("bartlett_db = 10*log10", self.source)
        self.assertIn("capon_db = 10*log10", self.source)
        self.assertIn("music_db = 10*log10", self.source)
        self.assertIn("ideal_mvdr_pattern_db = 20*log10", self.source)
        self.assertIn("calibrated_noise_covariance = noise_power*calibration_equalizer* ...", self.source)
        self.assertNotIn("music_db = 20*log10", self.source)
        self.assertNotIn("capon_db = 20*log10", self.source)

    def test_docs_are_concept_first_complete_and_not_placeholders(self):
        documents = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        for name, document in documents.items():
            with self.subTest(document=name):
                self.assertIn(QUESTION, document)
                self.assertNotIn("TODO", document)
        lesson = documents["lesson.md"]
        for marker in (
            "b(theta) = Dg C ap(theta)",
            "PB(theta) = a0(theta)^H Rhat a0(theta) / M^2",
            "Wn Rn Wn^H = I",
            "PMUSIC(theta) = 1 / ||En^H Wn a0(theta)||^2",
            "qhat = bhat_c ./ a0(theta_c)",
            "Rn,cal = sigma_n^2 E E^H",
            "one effective response vector",
            "Limiting cases and claim boundary",
        ):
            self.assertIn(marker, lesson)
        walkthrough = documents["walkthrough.md"]
        for marker in ("Sweep 1", "Sweep 2", "Broken case", "Recovery", "Ctrl+C", "unchanged"):
            self.assertIn(marker, walkthrough)
        checks = documents["checks.md"]
        self.assertIn("Short teach-back rubric", checks)
        self.assertGreaterEqual(checks.count("**Correct:**"), 48)

    def test_cli_start_advance_rollback_recovery_timeout_and_isolation(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.make_cli_fixture(base, self.manifest)
            started = self.run_fixture_cli(fixture, "start", "67")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P67", started.stdout)
            self.assertIn("status: implemented", started.stdout)
            state = fixture / ".learning/progress.json"
            state.write_text(json.dumps({
                "schema_version": 1,
                "current": "P66",
                "completed": [f"P{number:02d}" for number in range(1, 67)],
                "notes": {},
            }) + "\n", encoding="utf-8")
            advanced = self.run_fixture_cli(fixture, "start")
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertIn("P67 — Inject Array Calibration", advanced.stdout)

            rolled_back = copy.deepcopy(self.manifest)
            next(module for module in rolled_back["modules"] if module["id"] == "P67")["status"] = "scaffolded"
            original_p66 = copy.deepcopy(next(module for module in self.manifest["modules"] if module["id"] == "P66"))
            original_p68 = copy.deepcopy(next(module for module in self.manifest["modules"] if module["id"] == "P68"))
            fixture = self.make_cli_fixture(base / "rollback", rolled_back)
            refused = self.run_fixture_cli(fixture, "start", "67")
            self.assertEqual(refused.returncode, 3, refused.stderr)
            self.assertIn("awaits Portfolio batch P67", refused.stdout)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P66"), original_p66)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P68"), original_p68)
            (fixture / "curriculum/modules.json").write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")
            recovered = self.run_fixture_cli(fixture, "start", "67")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_cancellation_recovery_and_external_side_effect_boundaries(self):
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P67'));", self.source)
        self.assertIn("clear p67_results;", self.source)
        for token in ("parfor", "timer(", "fopen(", "save(", "system(", "webread"):
            self.assertNotIn(token, self.source)
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        self.assertIn("Ctrl+C", walkthrough)
        self.assertIn("there is no\nworker, timer", walkthrough)
        self.assertIn("partial persistent state", walkthrough)

    def test_public_catalogs_preserve_dependency_and_future_extension(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 67 follows P66", readme)
        self.assertIn("Project 67 follows P66", start_here)
        self.assertRegex(index, r"\| \[P67\].*\| implemented \| 7 \|")
        p68 = next(module for module in self.manifest["modules"] if module["id"] == "P68")
        self.assertEqual(p68["title"], "Build an Introductory STAP Clutter-Ridge Experiment")
        self.assertIn("P68 can", (MODULE / "README.md").read_text(encoding="utf-8"))

    def test_evidence_maps_acceptance_commands_claims_and_rollback(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P67-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        for marker in (
            "# P67 Retained Evidence",
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
            "67 implemented",
            "operator-provided",
        ):
            self.assertIn(marker, evidence)
        self.assertTrue(evidence.endswith("\n"))
        self.assertFalse(evidence.endswith("\n\n"))

    def test_changed_text_files_have_exactly_one_terminal_newline(self):
        paths = [MODULE / name for name in ARTIFACTS]
        paths.extend([
            ROOT / "curriculum/modules.json",
            ROOT / "README.md",
            ROOT / "START_HERE.md",
            ROOT / "modules/README.md",
            ROOT / "tests/test_p67_module.py",
        ])
        paths.extend(sorted((ROOT / "docs/evidence").glob("P67-*.md")))
        for path in paths:
            with self.subTest(path=path):
                data = path.read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
