from __future__ import annotations

import cmath
import copy
import functools
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
MODULE = ROOT / "modules/70-create-an-fmcw-range-doppler-map"
QUESTION = "How do fast-time beat frequency and chirp-to-chirp phase separate range and velocity?"
EXPECTED_IDENTITY = {
    "number": 70,
    "id": "P70",
    "title": "Create an FMCW Range-Doppler Map",
    "guiding_question": QUESTION,
    "phase": 8,
    "phase_title": "FMCW, MIMO, and Micro-Doppler",
    "slug": "create-an-fmcw-range-doppler-map",
    "folder": "modules/70-create-an-fmcw-range-doppler-map",
    "status": "implemented",
    "implementation_batch": "P70",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
SOURCE_MARKERS = (
    "baseline_seed = 7001;",
    "speed_of_light_mps = 3.0e8;",
    "carrier_frequency_hz = 77.0e9;",
    "sample_rate_hz = 12.8e6;",
    "chirp_duration_s = 40.0e-6;",
    "chirp_bandwidth_hz = 150.0e6;",
    "chirp_repetition_interval_s = 50.0e-6;",
    "sample_count = 512;",
    "chirp_count = 64;",
    "target_ranges_m = [20 20 23];",
    "target_velocity_bin_offsets = [-3 3 3];",
    "sample_count_sweep = [128 256 512];",
    "chirp_count_sweep = [16 32 64];",
    "target_beat_frequency_hz = 2*chirp_slope_hz_per_s* ...",
    "target_radial_doppler_frequency_hz = target_velocity_bin_offsets* ...",
    "target_dechirped_slow_frequency_hz = ...",
    "-target_radial_doppler_frequency_hz;",
    "velocity_axis_mps = -wavelength_m*doppler_frequency_hz/2;",
    "target_contribution = target_voltage(target_index)* ...",
    "dechirped_data = dechirped_targets + private_noise;",
    "range_spectrum_full = fft(windowed_fast_time_data, sample_count, 1) / ...",
    "range_data = range_spectrum_full(1:sample_count/2+1, :);",
    "range_doppler_complex = fftshift(fft(windowed_slow_time_data, ...",
    "chirp_count, 2), 2)/sum(slow_time_window);",
    "broken_noncoherent_range_data = abs(range_data);",
    "recovered_range_doppler_complex = fftshift(fft( ...",
    "'P70:MatrixShape'",
    "'P70:RangeMatrixShape'",
    "'P70:TargetRange'",
    "'P70:TargetVelocity'",
    "'P70:DistinctTargets'",
    "'P70:ChirpSweep'",
    "'P70:SampleSweep'",
    "'P70:BrokenPhaseLoss'",
    "'P70:VelocitySignRecovery'",
    "'P70:SameDataRecovery'",
    "recovered_peak_velocity_mps = velocity_axis_mps(recovered_peak_index);",
    "maximum_samples = 1024;",
    "maximum_chirps = 128;",
    "maximum_targets = 8;",
    "maximum_private_values = 100000;",
    "maximum_working_numeric_values = 2000000;",
    "maximum_figures = 7;",
    "validate_controls(controls);",
    "'P70:ControlFields'",
    "'P70:ControlScalar'",
    "'P70:ControlVector'",
    "'P70:TargetVectors'",
    "'P70:SweepVectors'",
    "'P70:PhysicalControls'",
    "'P70:TargetControls'",
    "maximum_beat_hz = max(2*(c.bandwidth_hz/c.chirp_duration_s)* ...",
    "'P70:BeatNyquist'",
    "'P70:ImmutableCeilings'",
    "2*c.sample_count*c.chirp_count <= c.max_private_values, ...",
    "'P70:NoiseCeiling'",
    "'P70:SeedRange'",
    "state = mod(16807*state, 2147483647);",
    "samples = sqrt(-2*log(first)).*exp(1j*2*pi*second)/sqrt(2);",
    "noise = reshape(samples, number_rows, number_columns);",
    "p70_results = struct( ...",
    "close(findall(0, 'Type', 'figure', 'Tag', 'P70'));",
    "clear p70_results;",
)
FORBIDDEN_LITERAL_TOKENS = (
    "phased.", "dechirp(", "beat2range(", "range2beat(",
    "phased.RangeDopplerResponse", "fft2(", "awgn(", "rng(", "rand(",
    "randn(", "parfor", "timer(", "webread", "urlread", "system(",
    "fopen(", "save(", "clear all", "clearvars", "delete(", "close all",
)
MODULUS = 2_147_483_647
MULTIPLIER = 16_807
MATLAB_CONTROL_NAMES = {
    "baseline_seed": "seed",
    "speed_of_light_mps": "c",
    "carrier_frequency_hz": "carrier",
    "sample_rate_hz": "fs",
    "chirp_duration_s": "duration",
    "chirp_bandwidth_hz": "bandwidth",
    "chirp_repetition_interval_s": "interval",
    "sample_count": "samples",
    "chirp_count": "chirps",
    "target_ranges_m": "ranges",
    "target_velocity_bin_offsets": "doppler_bins",
    "target_voltage": "voltages",
    "target_initial_phase_rad": "phases",
    "noise_rms": "noise",
    "sample_count_sweep": "sample_sweep",
    "chirp_count_sweep": "chirp_sweep",
    "plot_floor_db": "floor",
    "maximum_samples": "max_samples",
    "maximum_chirps": "max_chirps",
    "maximum_targets": "max_targets",
    "maximum_sweep_cases": "max_sweeps",
    "maximum_private_values": "max_private",
    "maximum_working_numeric_values": "max_working",
    "maximum_figures": "max_figures",
}
MATLAB_NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?\Z")


def executable_source(source: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in source.splitlines())


def source_controls(source: str) -> dict[str, object]:
    controls: dict[str, object] = {}
    for matlab_name, control_name in MATLAB_CONTROL_NAMES.items():
        matches = re.findall(
            rf"(?m)^\s*{re.escape(matlab_name)}\s*=\s*([^;\n]+);\s*$",
            source,
        )
        if len(matches) != 1:
            raise ValueError(f"{matlab_name} assignment")
        literal = matches[0].strip()
        tokens = literal[1:-1].split() if literal.startswith("[") and literal.endswith("]") else [literal]
        if not tokens or any(not MATLAB_NUMBER.fullmatch(token) for token in tokens):
            raise ValueError(f"{matlab_name} numeric literal")
        values = tuple(float(token) for token in tokens)
        controls[control_name] = values if len(tokens) > 1 else values[0]
    return controls


def p70_source_errors(source: object) -> list[str]:
    if not isinstance(source, str) or not source:
        return ["P70 source must be nonempty text"]
    executable = executable_source(source)
    errors = [
        f"missing source marker: {marker}"
        for marker in SOURCE_MARKERS
        if marker not in executable
    ]
    if executable.count("figure('Name', 'P70") != 7:
        errors.append("P70 must create exactly seven named figures")
    if executable.count("'Tag', 'P70'") != 8:
        errors.append("P70 must tag seven figures and one scoped cleanup")
    errors.extend(
        f"forbidden source token: {token}"
        for token in FORBIDDEN_LITERAL_TOKENS
        if token in executable
    )
    if re.search(r"(?m)^\s*!", executable):
        errors.append("forbidden shell escape")
    try:
        controls = source_controls(executable)
        validate_controls(controls)
        if controls != reviewed_controls():
            errors.append("visible MATLAB controls drifted from the reviewed oracle")
    except ValueError as error:
        errors.append(f"invalid visible MATLAB controls: {error}")
    return errors


def validate_p70_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P70 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [
        entry
        for entry in manifest["modules"]
        if isinstance(entry, dict) and entry.get("id") == "P70"
    ]
    if len(matches) != 1:
        errors.append("P70 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P70 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P70 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P70 empty {artifact}")
    return errors


def reviewed_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "seed": 7001,
        "c": 3.0e8,
        "carrier": 77.0e9,
        "fs": 12.8e6,
        "duration": 40.0e-6,
        "bandwidth": 150.0e6,
        "interval": 50.0e-6,
        "samples": 512,
        "chirps": 64,
        "ranges": (20.0, 20.0, 23.0),
        "doppler_bins": (-3, 3, 3),
        "voltages": (1.0, 0.82, 0.68),
        "phases": (0.10, 0.75, -0.55),
        "noise": 0.01,
        "sample_sweep": (128, 256, 512),
        "chirp_sweep": (16, 32, 64),
        "floor": -70.0,
        "max_samples": 1024,
        "max_chirps": 128,
        "max_targets": 8,
        "max_sweeps": 6,
        "max_private": 100000,
        "max_working": 2000000,
        "max_figures": 7,
    }
    controls.update(overrides)
    return controls


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def is_power_of_two(value: object) -> bool:
    return finite_real(value) and value == int(value) and value > 0 and not int(value) & (int(value) - 1)


def validate_controls(c: object) -> None:
    if not isinstance(c, dict) or set(c) != set(reviewed_controls()):
        raise ValueError("controls")
    vectors = {"ranges", "doppler_bins", "voltages", "phases", "sample_sweep", "chirp_sweep"}
    if not all(finite_real(value) for key, value in c.items() if key not in vectors):
        raise ValueError("scalar")
    for name in vectors:
        values = c[name]
        if not isinstance(values, (tuple, list)) or not values or not all(finite_real(value) for value in values):
            raise ValueError("vector")
    integer_scalars = {
        "seed", "samples", "chirps", "max_samples", "max_chirps",
        "max_targets", "max_sweeps", "max_private", "max_working", "max_figures",
    }
    if not all(c[name] > 0 and c[name] == int(c[name]) for name in integer_scalars):
        raise ValueError("integer")
    target_count = len(c["ranges"])
    if not (
        3 <= target_count <= c["max_targets"]
        and len(c["doppler_bins"]) == target_count
        and len(c["voltages"]) == target_count
        and len(c["phases"]) == target_count
        and all(value == int(value) for value in c["doppler_bins"])
        and all(value > 0 for value in c["ranges"])
        and all(0 < value <= 2 for value in c["voltages"])
        and all(abs(value) < c["chirps"] / 2 for value in c["doppler_bins"])
        and len(set(zip(c["ranges"], c["doppler_bins"]))) == target_count
    ):
        raise ValueError("targets")
    for name, upper, minimum in (
        ("sample_sweep", c["samples"], 64),
        ("chirp_sweep", c["chirps"], 8),
    ):
        values = c[name]
        if not (
            3 <= len(values) <= c["max_sweeps"]
            and all(is_power_of_two(value) and value >= minimum for value in values)
            and all(right > left for left, right in zip(values, values[1:]))
            and values[-1] == upper
        ):
            raise ValueError("sweep")
    if c["c"] <= 0 or c["duration"] <= 0:
        raise ValueError("physical")
    maximum_beat = max(
        2 * (c["bandwidth"] / c["duration"]) * value / c["c"]
        for value in c["ranges"]
    )
    if not (
        c["c"] > 0
        and c["carrier"] > 0
        and c["fs"] > 0
        and c["duration"] > 0
        and c["bandwidth"] > 0
        and c["interval"] >= c["duration"]
        and c["samples"] == round(c["fs"] * c["duration"])
        and 128 <= c["samples"] <= c["max_samples"]
        and 16 <= c["chirps"] <= c["max_chirps"]
        and 0 <= c["noise"] <= 1
        and -200 <= c["floor"] <= -20
        and maximum_beat < c["fs"] / 2
        and 2 * c["samples"] * c["chirps"] <= c["max_private"]
    ):
        raise ValueError("physical")
    immutable = {
        "max_samples": 1024,
        "max_chirps": 128,
        "max_targets": 8,
        "max_sweeps": 6,
        "max_private": 100000,
        "max_working": 2000000,
        "max_figures": 7,
    }
    if any(c[name] != value for name, value in immutable.items()):
        raise ValueError("ceiling")
    if c["seed"] > MODULUS - 5:
        raise ValueError("seed")


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
    flat = [
        math.sqrt(-2 * math.log(max(values[index], float.fromhex("0x0.0000000000001p-1022"))))
        * cmath.exp(1j * 2 * math.pi * values[count + index])
        / math.sqrt(2)
        for index in range(count)
    ]
    return [[flat[column * rows + row] for column in range(columns)] for row in range(rows)]


def radix2_fft(signal: list[complex]) -> list[complex]:
    count = len(signal)
    if count <= 0 or count & (count - 1):
        raise ValueError("fft length")
    spectrum = list(signal)
    reversed_index = 0
    for index in range(1, count):
        bit = count >> 1
        while reversed_index & bit:
            reversed_index ^= bit
            bit >>= 1
        reversed_index ^= bit
        if index < reversed_index:
            spectrum[index], spectrum[reversed_index] = spectrum[reversed_index], spectrum[index]
    block_length = 2
    while block_length <= count:
        block_twiddle = cmath.exp(-2j * math.pi / block_length)
        half_length = block_length // 2
        for block_start in range(0, count, block_length):
            twiddle = 1 + 0j
            for offset in range(half_length):
                even = spectrum[block_start + offset]
                odd = twiddle * spectrum[block_start + offset + half_length]
                spectrum[block_start + offset] = even + odd
                spectrum[block_start + offset + half_length] = even - odd
                twiddle *= block_twiddle
        block_length *= 2
    return spectrum


def fftshift(values: list[complex]) -> list[complex]:
    midpoint = len(values) // 2
    return values[midpoint:] + values[:midpoint]


@functools.lru_cache(maxsize=1)
def exact_map() -> dict[str, object]:
    c = 3.0e8
    carrier = 77.0e9
    wavelength = c / carrier
    fs = 12.8e6
    duration = 40.0e-6
    bandwidth = 150.0e6
    slope = bandwidth / duration
    interval = 50.0e-6
    prf = 1 / interval
    rows = 512
    columns = 64
    ranges = (20.0, 20.0, 23.0)
    offsets = (-3, 3, 3)
    voltages = (1.0, 0.82, 0.68)
    phases = (0.10, 0.75, -0.55)
    beats = tuple(2 * slope * value / c for value in ranges)
    radial_dopplers = tuple(value * prf / columns for value in offsets)
    dechirped_slow_frequencies = tuple(-value for value in radial_dopplers)
    velocities = tuple(wavelength * value / 2 for value in radial_dopplers)
    noise = private_complex_noise(7001, rows, columns)
    data = []
    for row in range(rows):
        fast_time = row / fs
        data_row = []
        for column in range(columns):
            slow_time = column * interval
            target_sum = sum(
                voltage
                * cmath.exp(
                    1j
                    * (
                        2 * math.pi * (beat * fast_time + slow_frequency * slow_time)
                        + phase
                    )
                )
                for beat, slow_frequency, voltage, phase in zip(
                    beats, dechirped_slow_frequencies, voltages, phases
                )
            )
            data_row.append(target_sum + 0.01 * noise[row][column])
        data.append(data_row)
    fast_window = [0.5 - 0.5 * math.cos(2 * math.pi * row / (rows - 1)) for row in range(rows)]
    fast_gain = sum(fast_window)
    range_data = [[0j for _ in range(columns)] for _ in range(rows // 2 + 1)]
    for column in range(columns):
        spectrum = radix2_fft([data[row][column] * fast_window[row] for row in range(rows)])
        for range_bin in range(rows // 2 + 1):
            range_data[range_bin][column] = spectrum[range_bin] / fast_gain
    slow_window = [0.5 - 0.5 * math.cos(2 * math.pi * column / (columns - 1)) for column in range(columns)]
    slow_gain = sum(slow_window)
    rd_map = []
    for row in range(rows // 2 + 1):
        spectrum = fftshift(radix2_fft([range_data[row][column] * slow_window[column] for column in range(columns)]))
        rd_map.append([value / slow_gain for value in spectrum])
    broken_map = []
    for row in range(rows // 2 + 1):
        spectrum = fftshift(radix2_fft([abs(range_data[row][column]) * slow_window[column] for column in range(columns)]))
        broken_map.append([value / slow_gain for value in spectrum])
    range_spacing = c * fs / (2 * slope * rows)
    velocity_spacing = wavelength * prf / (2 * columns)
    measured = []
    for known_range, offset in zip(ranges, offsets):
        center_range = round(known_range / range_spacing)
        center_doppler = -offset + columns // 2
        candidates = [
            (abs(rd_map[range_bin][doppler_bin]), range_bin, doppler_bin)
            for range_bin in range(center_range - 1, center_range + 2)
            for doppler_bin in range(center_doppler - 1, center_doppler + 2)
        ]
        _, range_bin, doppler_bin = max(candidates)
        measured.append((range_bin * range_spacing, -(doppler_bin - columns // 2) * velocity_spacing))
    isolated_range_bin = round(ranges[2] / range_spacing)
    broken_peak = max(range(columns), key=lambda index: abs(broken_map[isolated_range_bin][index]))
    return {
        "ranges": ranges,
        "velocities": velocities,
        "beats": beats,
        "radial_dopplers": radial_dopplers,
        "dechirped_slow_frequencies": dechirped_slow_frequencies,
        "range_spacing": range_spacing,
        "velocity_spacing": velocity_spacing,
        "measured": tuple(measured),
        "peak_indices": tuple((round(value[0] / range_spacing), -round(value[1] / velocity_spacing) + columns // 2) for value in measured),
        "broken_peak_velocity": -(broken_peak - columns // 2) * velocity_spacing,
        "rd_map": tuple(tuple(row) for row in rd_map),
    }


class P70ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")

    def make_fixture(self, base: Path, manifest: dict) -> Path:
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

    def run_cli(self, fixture: Path, *args: str) -> subprocess.CompletedProcess[str]:
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
        self.assertEqual(validate_p70_contract(ROOT, self.manifest), [])
        p69 = next(module for module in self.manifest["modules"] if module["id"] == "P69")
        self.assertEqual(p69["status"], "implemented")

    def test_contract_rejects_malformed_duplicate_drift_missing_and_empty(self):
        self.assertTrue(validate_p70_contract(ROOT, None))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append(None)
        self.assertIn("every manifest module must be an object", validate_p70_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("P70 must have exactly one manifest entry", validate_p70_contract(ROOT, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(module for module in drifted["modules"] if module["id"] == "P70")["guiding_question"] = "changed"
        self.assertIn("P70 manifest identity drift", validate_p70_contract(ROOT, drifted))
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            module = fixture / EXPECTED_IDENTITY["folder"]
            module.mkdir(parents=True)
            for artifact in ARTIFACTS[1:]:
                (module / artifact).write_text("content\n", encoding="utf-8")
            self.assertIn("P70 missing README.md", validate_p70_contract(fixture, self.manifest))
            (module / "README.md").write_text("\n", encoding="utf-8")
            self.assertIn("P70 empty README.md", validate_p70_contract(fixture, self.manifest))

    def test_source_exposes_determinism_axes_sweeps_failure_recovery_and_bounds(self):
        self.assertEqual(p70_source_errors(self.source), [])
        for mutation in (
            self.source.replace("baseline_seed = 7001;", "baseline_seed = 1;", 1),
            self.source.replace("range_data = range_spectrum_full(1:sample_count/2+1, :);", "range_data = range_spectrum_full;", 1),
            self.source.replace("broken_noncoherent_range_data = abs(range_data);", "broken_noncoherent_range_data = range_data;", 1),
            self.source.replace("recovered_range_doppler_complex = fftshift(fft( ...", "recovered_range_doppler_complex = broken_range_doppler_complex; %", 1),
            self.source.replace("'P70:BeatNyquist'", "'P70:RemovedBeatGuard'", 1),
            self.source.replace("'P70:VelocitySignRecovery'", "'P70:RemovedSignRecovery'", 1),
            self.source.replace("'P70:ImmutableCeilings'", "'P70:RemovedCeilings'", 1),
            self.source.replace("'P70:NoiseCeiling'", "'P70:RemovedNoiseBound'", 1),
        ):
            with self.subTest():
                self.assertTrue(any("missing source marker" in error for error in p70_source_errors(mutation)))
        self.assertTrue(p70_source_errors(self.source + "\nresult = fft2(range_data);\n"))

    def test_visible_matlab_controls_match_the_validated_oracle_inputs(self):
        observed = source_controls(executable_source(self.source))
        self.assertEqual(observed, reviewed_controls())
        validate_controls(observed)
        for old, new in (
            ("target_voltage = [1.00 0.82 0.68];", "target_voltage = [1.00 0.20 0.00];"),
            ("target_initial_phase_rad = [0.10 0.75 -0.55];", "target_initial_phase_rad = [0.10 NaN -0.55];"),
            ("noise_rms = 0.01;", "noise_rms = NaN;"),
            ("plot_floor_db = -70;", "plot_floor_db = -20;"),
        ):
            with self.subTest(control=old.split(" =", 1)[0]):
                self.assertTrue(p70_source_errors(self.source.replace(old, new, 1)))

    def test_controls_accept_reviewed_and_reject_malformed_resource_inputs(self):
        validate_controls(reviewed_controls())
        invalid = (
            None,
            reviewed_controls(fs=True),
            reviewed_controls(duration=math.nan),
            reviewed_controls(seed=1.5),
            reviewed_controls(c=0),
            reviewed_controls(carrier=0),
            reviewed_controls(fs=10.0e6),
            reviewed_controls(duration=41.0e-6),
            reviewed_controls(bandwidth=0),
            reviewed_controls(interval=30.0e-6),
            reviewed_controls(samples=2048),
            reviewed_controls(chirps=256),
            reviewed_controls(ranges=(20.0, 20.0)),
            reviewed_controls(ranges=(20.0, math.inf, 23.0)),
            reviewed_controls(doppler_bins=(-3, 3.5, 3)),
            reviewed_controls(doppler_bins=(-3, 3, 40)),
            reviewed_controls(doppler_bins=(-3, -3, 3), ranges=(20.0, 20.0, 23.0)),
            reviewed_controls(voltages=(1.0, 0.0, 0.68)),
            reviewed_controls(phases=(0.1, 0.2)),
            reviewed_controls(noise=-0.1),
            reviewed_controls(sample_sweep=(128, 192, 512)),
            reviewed_controls(sample_sweep=(128, 256, 1024)),
            reviewed_controls(chirp_sweep=(16, 16, 64)),
            reviewed_controls(chirp_sweep=(16, 32, 128)),
            reviewed_controls(floor=-10),
            reviewed_controls(ranges=(20.0, 20.0, 500.0)),
            reviewed_controls(max_samples=2048),
            reviewed_controls(max_chirps=256),
            reviewed_controls(max_targets=9),
            reviewed_controls(max_sweeps=7),
            reviewed_controls(max_private=200000),
            reviewed_controls(max_working=3000000),
            reviewed_controls(max_figures=8),
        )
        for controls in invalid:
            with self.subTest(controls=controls):
                with self.assertRaises(ValueError):
                    validate_controls(controls)

    def test_private_generator_is_exact_repeatable_isolated_and_bounded(self):
        values = private_uniform(7001, 5)
        expected = (
            0.0547924111852387,
            0.8960547903068619,
            0.9928606874276236,
            0.009573596068459376,
            0.9034291225967133,
        )
        for observed, wanted in zip(values, expected):
            self.assertAlmostEqual(observed, wanted, places=15)
        self.assertEqual(values, private_uniform(7001, 5))
        self.assertNotEqual(values, private_uniform(7002, 5))
        noise = private_complex_noise(7001, 512, 64)
        self.assertEqual((len(noise), len(noise[0])), (512, 64))
        for bad_seed in (True, 0, MODULUS, math.nan):
            with self.assertRaises(ValueError):
                private_uniform(bad_seed, 1)
        for bad_count in (True, 0, 1.5, 100001, math.inf):
            with self.assertRaises(ValueError):
                private_uniform(7001, bad_count)

    def test_ideal_phase_increments_separate_fast_and_slow_time(self):
        c = 3.0e8
        carrier = 77.0e9
        wavelength = c / carrier
        fs = 12.8e6
        slope = 150.0e6 / 40.0e-6
        interval = 50.0e-6
        beat = 2 * slope * 20.0 / c
        radial_doppler = 2 * (3 * wavelength * (1 / interval) / (2 * 64)) / wavelength
        dechirped_slow_frequency = -radial_doppler
        expected_fast = cmath.exp(1j * 2 * math.pi * beat / fs)
        expected_slow = cmath.exp(1j * 2 * math.pi * dechirped_slow_frequency * interval)
        samples = [cmath.exp(1j * 2 * math.pi * beat * index / fs) for index in range(8)]
        chirps = [cmath.exp(1j * 2 * math.pi * dechirped_slow_frequency * index * interval) for index in range(8)]
        self.assertLess(max(abs(left.conjugate() * right - expected_fast) for left, right in zip(samples, samples[1:])), 2e-14)
        self.assertLess(max(abs(left.conjugate() * right - expected_slow) for left, right in zip(chirps, chirps[1:])), 2e-14)
        self.assertGreater(cmath.phase(expected_fast), 0)
        self.assertLess(cmath.phase(expected_slow), 0)

    def test_exact_deterministic_oracle_places_all_targets_and_broken_peak(self):
        result = exact_map()
        for observed, expected in zip(result["beats"], (500000.0, 500000.0, 575000.0)):
            self.assertAlmostEqual(observed, expected, places=8)
        self.assertAlmostEqual(result["range_spacing"], 1.0, places=12)
        self.assertAlmostEqual(result["velocity_spacing"], 0.6087662337662338, places=12)
        for observed, expected in zip(
            result["measured"],
            ((20.0, -1.8262987012987013), (20.0, 1.8262987012987013), (23.0, 1.8262987012987013)),
        ):
            self.assertAlmostEqual(observed[0], expected[0], places=12)
            self.assertAlmostEqual(observed[1], expected[1], places=12)
        self.assertEqual(len(set(result["peak_indices"])), 3)
        self.assertAlmostEqual(result["broken_peak_velocity"], 0.0, places=12)

    def test_observation_count_sweeps_obey_physical_spacing_laws(self):
        c = 3.0e8
        wavelength = c / 77.0e9
        prf = 1 / 50.0e-6
        velocity_spacings = tuple(wavelength * prf / (2 * count) for count in (16, 32, 64))
        cpis = tuple(count * 50.0e-6 for count in (16, 32, 64))
        self.assertEqual(tuple(round(value, 12) for value in velocity_spacings), (2.435064935065, 1.217532467532, 0.608766233766))
        self.assertEqual(cpis, (0.0008, 0.0016, 0.0032))
        observed_bandwidths = tuple((150.0e6 / 40.0e-6) * count / 12.8e6 for count in (128, 256, 512))
        range_spacings = tuple(c / (2 * value) for value in observed_bandwidths)
        for observed, expected in zip(observed_bandwidths, (37.5e6, 75.0e6, 150.0e6)):
            self.assertAlmostEqual(observed, expected, places=6)
        for observed, expected in zip(range_spacings, (4.0, 2.0, 1.0)):
            self.assertAlmostEqual(observed, expected, places=12)

    def test_documents_are_concept_first_complete_and_not_placeholders(self):
        documents = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        for name, document in documents.items():
            with self.subTest(document=name):
                self.assertIn(QUESTION, document)
                self.assertNotIn("TODO", document)
        lesson = documents["lesson.md"]
        for marker in ("f_b = S(2R/c)", "f_d = 2v/lambda", "v = -lambda f_slow/2", "dimension 1", "dimension 2", "Limiting cases and model boundary", "P71"):
            self.assertIn(marker, lesson)
        walkthrough = documents["walkthrough.md"]
        for marker in ("Sweep 1", "Sweep 2", "Broken case", "Recovery", "Ctrl+C", "unchanged"):
            self.assertIn(marker, walkthrough)
        checks = documents["checks.md"]
        self.assertIn("Short teach-back rubric", checks)
        self.assertGreaterEqual(checks.count("**Correct:**"), 30)

    def test_cli_start_advance_rollback_recovery_timeout_and_isolation(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.make_fixture(base, self.manifest)
            started = self.run_cli(fixture, "start", "70")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P70", started.stdout)
            self.assertIn("status: implemented", started.stdout)
            state = fixture / ".learning/progress.json"
            state.write_text(
                json.dumps({"schema_version": 1, "current": "P69", "completed": [f"P{number:02d}" for number in range(1, 70)], "notes": {}}) + "\n",
                encoding="utf-8",
            )
            advanced = self.run_cli(fixture, "start")
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertIn("P70 — Create an FMCW Range-Doppler Map", advanced.stdout)
            era_manifest = copy.deepcopy(self.manifest)
            for module in era_manifest["modules"]:
                if module["number"] > 70:
                    module["status"] = "scaffolded"
            rolled_back = copy.deepcopy(era_manifest)
            next(module for module in rolled_back["modules"] if module["id"] == "P70")["status"] = "scaffolded"
            original_p69 = copy.deepcopy(next(module for module in rolled_back["modules"] if module["id"] == "P69"))
            original_p71_identity = {
                key: value
                for key, value in next(module for module in self.manifest["modules"] if module["id"] == "P71").items()
                if key != "status"
            }
            rollback_fixture = self.make_fixture(base / "rollback", rolled_back)
            refused = self.run_cli(rollback_fixture, "start", "70")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P70", refused.stdout)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P69"), original_p69)
            self.assertEqual(
                {key: value for key, value in next(module for module in rolled_back["modules"] if module["id"] == "P71").items() if key != "status"},
                original_p71_identity,
            )
            (rollback_fixture / "curriculum/modules.json").write_text(
                json.dumps(era_manifest, indent=2) + "\n", encoding="utf-8"
            )
            recovered = self.run_cli(rollback_fixture, "start", "70")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_cancellation_external_side_effect_compatibility_and_rerun_boundaries(self):
        executable = executable_source(self.source)
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P70'));", executable)
        self.assertIn("clear p70_results;", executable)
        for token in ("parfor", "timer(", "fopen(", "save(", "system(", "webread"):
            self.assertNotIn(token, executable)
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        normalized = " ".join(walkthrough.split())
        self.assertIn("MATLAB R2016b or newer", readme)
        self.assertIn("no optional toolbox", readme)
        self.assertIn("Ctrl+C", walkthrough)
        self.assertIn("no worker, timer", walkthrough)
        self.assertIn("no background or external persistent state", normalized)

    def test_public_catalogs_preserve_dependency_and_future_extension(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 70 follows P69", readme)
        self.assertIn("Project 70 follows P69", start_here)
        self.assertRegex(index, r"\| \[P70\].*\| implemented \| 8 \|")
        p71 = next(module for module in self.manifest["modules"] if module["id"] == "P71")
        self.assertEqual(p71["title"], "Expose FMCW Range-Doppler Coupling")

    def test_evidence_maps_acceptance_commands_claims_and_rollback(self):
        paths = sorted((ROOT / "docs/evidence").glob("P70-*.md"))
        self.assertEqual(len(paths), 1)
        evidence = paths[0].read_text(encoding="utf-8")
        for marker in (
            "# P70 Retained Evidence",
            "## Acceptance map",
            "## Deterministic simulated-oracle results",
            "## Figure and metric inventory",
            "## Exact commands and results",
            "## Focused coverage",
            "## Changed and preserved invariants",
            "## Residual risks",
            "## Rollback",
            "## Unperformed validation",
            "MATLAB runtime",
            "DSP_RADAR_VERIFY_PROFILE=contract",
            "DSP_RADAR_VERIFY_PROFILE=quick",
            "DSP_RADAR_VERIFY_PROFILE=full",
            "84 modules",
            "70 implemented",
            "operator-managed",
        ):
            self.assertIn(marker, evidence)
        self.assertNotIn("PENDING", evidence)
        self.assertNotIn("recorded after execution", evidence)
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
                ROOT / "tests/test_p70_module.py",
            ]
        )
        paths.extend(sorted((ROOT / "docs/evidence").glob("P70-*.md")))
        for path in paths:
            with self.subTest(path=path):
                data = path.read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
