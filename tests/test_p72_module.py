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
MODULE = ROOT / "modules/72-use-up-down-triangular-chirps-to-separate-range-and-velocity"
EXPERIMENT = MODULE / "experiment.m"
EVIDENCE = ROOT / "docs/evidence/P72-2026-08-12.md"
QUESTION = "How can opposite chirp slopes disentangle delay and Doppler?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def manifest() -> dict:
    return json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))


def module_entry(data: dict, module_id: str) -> dict:
    matches = [entry for entry in data["modules"] if entry.get("id") == module_id]
    if len(matches) != 1:
        raise ValueError(f"expected one {module_id} entry, found {len(matches)}")
    return matches[0]


def artifact_errors(data: dict, root: Path) -> list[str]:
    errors: list[str] = []
    try:
        entry = module_entry(data, "P72")
    except (KeyError, TypeError, ValueError) as exc:
        return [str(exc)]
    expected = {
        "number": 72,
        "title": "Use Up/Down Triangular Chirps to Separate Range and Velocity",
        "guiding_question": QUESTION,
        "phase": 8,
        "phase_title": "FMCW, MIMO, and Micro-Doppler",
        "slug": "use-up-down-triangular-chirps-to-separate-range-and-velocity",
        "folder": "modules/72-use-up-down-triangular-chirps-to-separate-range-and-velocity",
        "status": "implemented",
        "implementation_batch": "P72",
    }
    for key, value in expected.items():
        if entry.get(key) != value:
            errors.append(f"P72 {key} drifted")
    folder = root / str(entry.get("folder", ""))
    for name in ARTIFACTS:
        path = folder / name
        if not path.is_file():
            errors.append(f"P72 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P72 empty {name}")
    return errors


def park_miller_uniform(seed: int, count: int) -> list[float]:
    if not isinstance(seed, int) or isinstance(seed, bool) or not 1 <= seed < 2147483647:
        raise ValueError("invalid seed")
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 20000:
        raise ValueError("invalid count")
    state = seed
    values: list[float] = []
    for _ in range(count):
        state = (16807 * state) % 2147483647
        values.append(state / 2147483647)
    return values


def private_complex_noise(seed: int, count: int) -> list[complex]:
    if 2 * count > 20000:
        raise ValueError("private generator request exceeds ceiling")
    values = park_miller_uniform(seed, 2 * count)
    return [
        math.sqrt(-2 * math.log(max(values[index], float.fromhex("0x1.0p-1022"))))
        * cmath.exp(1j * 2 * math.pi * values[count + index])
        / math.sqrt(2)
        for index in range(count)
    ]


def oracle_pair(
    seed: int = 7201,
    range_m: float = 45.0,
    velocity_mps: float = 20.0,
    noise_rms: float = 0.002,
) -> dict:
    c_mps = 3e8
    carrier_hz = 77e9
    fs_hz = 80e6
    duration_s = 40e-6
    bandwidth_hz = 20e6
    phase_rad = 0.35
    sample_count = round(fs_hz * duration_s)
    slope = bandwidth_hz / duration_s
    delay_s = 2 * range_m / c_mps
    wavelength_m = c_mps / carrier_hz
    doppler_hz = 2 * velocity_mps / wavelength_m
    up_noise = private_complex_noise(seed, sample_count)
    down_noise = private_complex_noise(seed + 1, sample_count)
    up_valid: list[complex] = []
    down_valid: list[complex] = []
    for index in range(sample_count):
        time_s = index / fs_hz
        if time_s < delay_s:
            continue
        centered = time_s - duration_s / 2
        delayed_centered = time_s - delay_s - duration_s / 2
        up_tx = cmath.exp(1j * math.pi * slope * centered**2)
        down_tx = cmath.exp(-1j * math.pi * slope * centered**2)
        up_rx = cmath.exp(
            1j
            * (
                math.pi * slope * delayed_centered**2
                + 2 * math.pi * doppler_hz * time_s
                + phase_rad
            )
        )
        down_rx = cmath.exp(
            1j
            * (
                -math.pi * slope * delayed_centered**2
                + 2 * math.pi * doppler_hz * time_s
                + phase_rad
            )
        )
        up_valid.append(up_tx * up_rx.conjugate() + noise_rms * up_noise[index])
        down_valid.append(down_tx * down_rx.conjugate() + noise_rms * down_noise[index])

    def estimate(samples: list[complex]) -> float:
        lag_product = sum(
            samples[index].conjugate() * samples[index + 1]
            for index in range(len(samples) - 1)
        )
        return cmath.phase(lag_product) * fs_hz / (2 * math.pi)

    up_hz = estimate(up_valid)
    down_hz = estimate(down_valid)
    delay_beat_hz = (up_hz - down_hz) / 2
    measured_doppler_hz = -(up_hz + down_hz) / 2
    estimated_range_m = c_mps * delay_beat_hz / (2 * slope)
    estimated_velocity_mps = wavelength_m * measured_doppler_hz / 2
    return {
        "sample_count": sample_count,
        "valid_count": len(up_valid),
        "slope": slope,
        "delay_s": delay_s,
        "doppler_hz": doppler_hz,
        "ideal_up_hz": slope * delay_s - doppler_hz,
        "ideal_down_hz": -slope * delay_s - doppler_hz,
        "up_hz": up_hz,
        "down_hz": down_hz,
        "delay_beat_hz": delay_beat_hz,
        "measured_doppler_hz": measured_doppler_hz,
        "range_m": estimated_range_m,
        "velocity_mps": estimated_velocity_mps,
    }


BASE_CONTROLS = {
    "seed": 7201,
    "c": 3e8,
    "fc": 77e9,
    "fs": 80e6,
    "duration": 40e-6,
    "bandwidth": 20e6,
    "range": 45.0,
    "velocity": 20.0,
    "amplitude": 1.0,
    "phase": 0.35,
    "noise": 0.002,
    "range_sweep": [15, 30, 45, 60, 75],
    "velocity_sweep": [-30, -15, 0, 15, 30],
    "noise_sweep": [0, 0.002, 0.01, 0.03, 0.08],
    "multi_range": [30, 65],
    "multi_velocity": [15, -10],
    "multi_amplitude": [1.0, 0.8],
    "multi_phase": [0.2, -0.6],
    "min_separation": 60e3,
    "floor": -80,
    "max_samples": 5000,
    "max_sweep": 7,
    "max_targets": 3,
    "max_private": 20000,
    "max_working": 350000,
    "max_figures": 7,
}


def validate_controls(values: dict) -> list[str]:
    errors: list[str] = []
    required = set(BASE_CONTROLS)
    if set(values) != required:
        return ["missing or unexpected controls"]
    vectors = {
        "range_sweep", "velocity_sweep", "noise_sweep", "multi_range",
        "multi_velocity", "multi_amplitude", "multi_phase",
    }
    for name in required - vectors:
        value = values[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"{name} must be finite numeric scalar")
    for name in vectors:
        value = values[name]
        if not isinstance(value, list) or not value or any(
            isinstance(item, list) for item in value
        ) or any(
            isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item)
            for item in value
        ):
            errors.append(f"{name} must be finite numeric vector")
    if errors:
        return errors
    sample_count = values["fs"] * values["duration"]
    if abs(sample_count - round(sample_count)) > 100 * math.ulp(round(sample_count)) or not 256 <= sample_count <= values["max_samples"]:
        errors.append("sample count invalid")
    if not 0 < values["bandwidth"] < values["fs"] or not values["range"] > 0:
        errors.append("waveform or target invalid")
    if not 0 <= values["noise"] <= 0.2 or not 0 < values["min_separation"] < values["fs"] / 4:
        errors.append("noise or separation invalid")
    range_sweep = values["range_sweep"]
    if not 3 <= len(range_sweep) <= values["max_sweep"] or not all(
        0 < left < right for left, right in zip(range_sweep, range_sweep[1:])
    ) or values["range"] not in range_sweep:
        errors.append("range sweep invalid")
    velocity_sweep = values["velocity_sweep"]
    if not 3 <= len(velocity_sweep) <= values["max_sweep"] or not all(
        left < right for left, right in zip(velocity_sweep, velocity_sweep[1:])
    ) or not min(velocity_sweep) < 0 < max(velocity_sweep) or 0 not in velocity_sweep:
        errors.append("velocity sweep invalid")
    noise_sweep = values["noise_sweep"]
    if not 3 <= len(noise_sweep) <= values["max_sweep"] or noise_sweep[0] != 0 or not all(
        0 <= left < right for left, right in zip(noise_sweep, noise_sweep[1:])
    ) or values["noise"] not in noise_sweep or noise_sweep[-1] > 0.2:
        errors.append("noise sweep invalid")
    multi_lengths = {
        len(values[name]) for name in ("multi_range", "multi_velocity", "multi_amplitude", "multi_phase")
    }
    if multi_lengths != {2} or not all(item > 0 for item in values["multi_range"] + values["multi_amplitude"]):
        errors.append("multi-target controls invalid")
    c_mps = values["c"]
    maximum_delay_s = 2 * max([values["range"], *range_sweep, *values["multi_range"]]) / c_mps
    overlap_count = sum(index / values["fs"] >= maximum_delay_s for index in range(round(sample_count)))
    if not 0 < maximum_delay_s < values["duration"] or overlap_count < 2:
        errors.append("common overlap invalid")
    slope = values["bandwidth"] / values["duration"]
    wavelength = c_mps / values["fc"]
    all_ranges = [values["range"], *range_sweep, *values["multi_range"]]
    all_velocities = [values["velocity"], *velocity_sweep, *values["multi_velocity"]]
    for range_value in all_ranges:
        delay_beat = 2 * slope * range_value / c_mps
        for velocity in all_velocities:
            doppler = 2 * velocity / wavelength
            if max(abs(delay_beat - doppler), abs(-delay_beat - doppler)) >= values["fs"] / 2:
                errors.append("signed beat violates Nyquist")
                break
    up = sorted(2 * slope * item / c_mps - 2 * velocity / wavelength for item, velocity in zip(values["multi_range"], values["multi_velocity"]))
    down = sorted(-2 * slope * item / c_mps - 2 * velocity / wavelength for item, velocity in zip(values["multi_range"], values["multi_velocity"]))
    if min(up[1] - up[0], down[1] - down[0]) <= values["min_separation"]:
        errors.append("multi-target peak separation invalid")
    ceilings = (
        values["max_samples"], values["max_sweep"], values["max_targets"],
        values["max_private"], values["max_working"], values["max_figures"],
    )
    if ceilings != (5000, 7, 3, 20000, 350000, 7):
        errors.append("resource ceilings drifted")
    if 2 * round(sample_count) > values["max_private"]:
        errors.append("private request exceeds ceiling")
    return errors


def solve_pair(up_hz, down_hz) -> tuple[list[float], list[float]]:
    if len(up_hz) != len(down_hz):
        raise ValueError("beat lists must have equal length")
    c_mps = 3e8
    slope = 20e6 / 40e-6
    wavelength = c_mps / 77e9
    ranges = [c_mps * (up - down) / (4 * slope) for up, down in zip(up_hz, down_hz)]
    velocities = [-wavelength * (up + down) / 4 for up, down in zip(up_hz, down_hz)]
    return ranges, velocities


def radix2_fft(samples: list[complex]) -> list[complex]:
    """Compute the power-of-two FFT needed by the dependency-free P72 oracle."""
    count = len(samples)
    if count < 1 or count & (count - 1):
        raise ValueError("FFT length must be a positive power of two")
    transformed = list(samples)
    target = 0
    for source in range(1, count):
        bit = count >> 1
        while target & bit:
            target ^= bit
            bit >>= 1
        target ^= bit
        if source < target:
            transformed[source], transformed[target] = transformed[target], transformed[source]
    span = 2
    while span <= count:
        twiddle_step = cmath.exp(-2j * math.pi / span)
        half_span = span // 2
        for start in range(0, count, span):
            twiddle = 1 + 0j
            for offset in range(half_span):
                even = transformed[start + offset]
                odd = transformed[start + offset + half_span] * twiddle
                transformed[start + offset] = even + odd
                transformed[start + offset + half_span] = even - odd
                twiddle *= twiddle_step
        span *= 2
    return transformed


def estimate_separated_tones(
    samples: list[complex], fs_hz: float, tone_count: int, separation_hz: float
) -> list[float]:
    """Mirror the MATLAB Hann/FFT/blank/interpolate multi-peak path."""
    sample_count = len(samples)
    if sample_count < 2:
        raise ValueError("peak estimation requires at least two samples")
    fft_count = 8 * (1 << (sample_count - 1).bit_length())
    windowed = [
        sample
        * (0.5 - 0.5 * math.cos(2 * math.pi * index / (sample_count - 1)))
        for index, sample in enumerate(samples)
    ]
    spectrum = radix2_fft(windowed + [0j] * (fft_count - sample_count))
    shifted = spectrum[fft_count // 2 :] + spectrum[: fft_count // 2]
    magnitude = [abs(value) for value in shifted]
    search_magnitude = magnitude.copy()
    bin_width_hz = fs_hz / fft_count
    blank_half_width = max(1, math.ceil(separation_hz / bin_width_hz))
    frequencies_hz: list[float] = []
    for _ in range(tone_count):
        peak_index = max(range(fft_count), key=search_magnitude.__getitem__)
        peak_value = search_magnitude[peak_index]
        if peak_value <= 100 * math.ulp(1.0) or not 0 < peak_index < fft_count - 1:
            raise ValueError("separated-tone estimation requires interior nonzero peaks")
        left_value = magnitude[peak_index - 1]
        center_value = magnitude[peak_index]
        right_value = magnitude[peak_index + 1]
        denominator = left_value - 2 * center_value + right_value
        offset = 0.0
        if abs(denominator) > 100 * math.ulp(1.0):
            offset = 0.5 * (left_value - right_value) / denominator
            offset = max(-0.5, min(0.5, offset))
        frequencies_hz.append((peak_index - fft_count / 2 + offset) * bin_width_hz)
        blank_start = max(0, peak_index - blank_half_width)
        blank_stop = min(fft_count - 1, peak_index + blank_half_width)
        search_magnitude[blank_start : blank_stop + 1] = [0.0] * (
            blank_stop - blank_start + 1
        )
    return sorted(frequencies_hz)


def composite_pairing_oracle() -> dict:
    """Exercise the deterministic composite echo through detected beat reports."""
    c_mps = 3e8
    carrier_hz = 77e9
    fs_hz = 80e6
    duration_s = 40e-6
    slope = 20e6 / duration_s
    wavelength_m = c_mps / carrier_hz
    sample_count = round(fs_hz * duration_s)
    ranges = BASE_CONTROLS["multi_range"]
    velocities = BASE_CONTROLS["multi_velocity"]
    amplitudes = BASE_CONTROLS["multi_amplitude"]
    phases = BASE_CONTROLS["multi_phase"]
    maximum_delay_s = 2 * max(ranges) / c_mps
    up_noise = private_complex_noise(BASE_CONTROLS["seed"] + 500, sample_count)
    down_noise = private_complex_noise(BASE_CONTROLS["seed"] + 501, sample_count)
    up_valid: list[complex] = []
    down_valid: list[complex] = []
    for index in range(sample_count):
        time_s = index / fs_hz
        if time_s < maximum_delay_s:
            continue
        centered = time_s - duration_s / 2
        up_tx = cmath.exp(1j * math.pi * slope * centered**2)
        down_tx = cmath.exp(-1j * math.pi * slope * centered**2)
        up_echo = 0j
        down_echo = 0j
        for range_m, velocity_mps, amplitude, phase_rad in zip(
            ranges, velocities, amplitudes, phases
        ):
            delay_s = 2 * range_m / c_mps
            delayed_centered = time_s - delay_s - duration_s / 2
            doppler_hz = 2 * velocity_mps / wavelength_m
            up_echo += amplitude * cmath.exp(
                1j
                * (
                    math.pi * slope * delayed_centered**2
                    + 2 * math.pi * doppler_hz * time_s
                    + phase_rad
                )
            )
            down_echo += amplitude * cmath.exp(
                1j
                * (
                    -math.pi * slope * delayed_centered**2
                    + 2 * math.pi * doppler_hz * time_s
                    + phase_rad
                )
            )
        up_valid.append(
            up_tx * up_echo.conjugate() + BASE_CONTROLS["noise"] * up_noise[index]
        )
        down_valid.append(
            down_tx * down_echo.conjugate()
            + BASE_CONTROLS["noise"] * down_noise[index]
        )
    detected_up_hz = estimate_separated_tones(
        up_valid, fs_hz, 2, BASE_CONTROLS["min_separation"]
    )
    detected_down_hz = estimate_separated_tones(
        down_valid, fs_hz, 2, BASE_CONTROLS["min_separation"]
    )
    ghost_range_m, ghost_velocity_mps = solve_pair(detected_up_hz, detected_down_hz)
    recovered_range_m, recovered_velocity_mps = solve_pair(
        detected_up_hz, list(reversed(detected_down_hz))
    )
    return {
        "valid_count": len(up_valid),
        "detected_up_hz": detected_up_hz,
        "detected_down_hz": detected_down_hz,
        "ghost_range_m": ghost_range_m,
        "ghost_velocity_mps": ghost_velocity_mps,
        "recovered_range_m": recovered_range_m,
        "recovered_velocity_mps": recovered_velocity_mps,
    }


class P72ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = manifest()
        cls.source = EXPERIMENT.read_text(encoding="utf-8")
        cls.documents = {
            name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        }

    def make_cli_fixture(self, base: Path, data: dict) -> Path:
        fixture = base / "repo"
        (fixture / "bin").mkdir(parents=True)
        (fixture / "curriculum").mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
        (fixture / "curriculum/modules.json").write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8"
        )
        for entry in data["modules"]:
            destination = fixture / entry["folder"] / "README.md"
            destination.parent.mkdir(parents=True)
            destination.write_text(
                (ROOT / entry["folder"] / "README.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        return fixture

    def run_cli(self, fixture: Path, *args: str):
        environment = os.environ.copy()
        environment["HOME"] = str(fixture.parent)
        return subprocess.run(
            [str(fixture / "bin/learn"), *args], cwd=fixture, env=environment,
            text=True, capture_output=True, timeout=10,
        )

    def test_artifacts_identity_and_prerequisite_are_permanent(self):
        self.assertEqual(artifact_errors(self.data, ROOT), [])
        self.assertEqual(module_entry(self.data, "P71")["status"], "implemented")
        p73 = module_entry(self.data, "P73")
        self.assertEqual(p73["number"], 73)
        self.assertEqual(p73["implementation_batch"], "P73")
        for name, text in self.documents.items():
            self.assertIn(QUESTION, text, name)

    def test_artifact_validation_rejects_malformed_identity_and_files(self):
        for mutation in ("duplicate", "identity", "status", "missing", "empty"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                fixture = Path(directory)
                shutil.copytree(MODULE, fixture / MODULE.relative_to(ROOT))
                data = copy.deepcopy(self.data)
                entry = module_entry(data, "P72")
                if mutation == "duplicate":
                    data["modules"].append(copy.deepcopy(entry))
                elif mutation == "identity":
                    entry["guiding_question"] = "drifted"
                elif mutation == "status":
                    entry["status"] = "scaffolded"
                elif mutation == "missing":
                    (fixture / entry["folder"] / "checks.md").unlink()
                else:
                    (fixture / entry["folder"] / "lesson.md").write_text("", encoding="utf-8")
                self.assertTrue(artifact_errors(data, fixture))

    def test_experiment_exposes_model_stages_sweeps_failure_and_recovery(self):
        required = (
            "baseline_seed = 7201", "tx.*conj(rx)",
            "f_up = S*tau - f_d and f_down = -S*tau - f_d",
            "up_transmit_chirp = exp", "down_transmit_chirp = exp",
            "up_received_echo", "down_received_echo", "up_dechirped_beat",
            "down_dechirped_beat", "estimate_signed_tone_frequency",
            "measured_delay_beat_frequency_hz", "measured_doppler_frequency_hz",
            "range_sweep_m", "velocity_sweep_mps", "noise_sweep_rms",
            "Sweep 1", "Sweep 2", "Sweep 3", "Intentionally broken case",
            "wrong_paired_down_hz", "correct_paired_down_hz",
            "same-data", "estimate_separated_tones", "p72_results",
            "xlabel(", "ylabel(", "maximum_working_numeric_values",
            "validate_controls", "overlap_count_local >= 2",
        )
        for marker in required:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P72"), 7)
        forbidden = (
            "phased.", "beat2range", "dechirp(", "rng(", "clear all", "close all",
            "parfor", "timer(", "webread", "urlread", "fopen(", "system(", "TODO",
        )
        lowered = self.source.lower()
        for marker in forbidden:
            self.assertNotIn(marker.lower(), lowered)

    def test_visible_controls_match_reviewed_contract(self):
        assignments = {
            "seed": r"baseline_seed = 7201;",
            "c": r"speed_of_light_mps = 3\.0e8;",
            "fc": r"carrier_frequency_hz = 77\.0e9;",
            "fs": r"sample_rate_hz = 80\.0e6;",
            "duration": r"chirp_duration_s = 40\.0e-6;",
            "bandwidth": r"chirp_bandwidth_hz = 20\.0e6;",
            "range": r"target_range_m = 45\.0;",
            "velocity": r"target_velocity_mps = 20\.0;",
            "range sweep": r"range_sweep_m = \[15 30 45 60 75\];",
            "velocity sweep": r"velocity_sweep_mps = \[-30 -15 0 15 30\];",
            "noise sweep": r"noise_sweep_rms = \[0 0\.002 0\.01 0\.03 0\.08\];",
            "multi scene": r"multi_target_range_m = \[30 65\];[\s\S]*multi_target_velocity_mps = \[15 -10\];",
            "ceilings": r"maximum_samples = 5000;[\s\S]*maximum_sweep_cases = 7;[\s\S]*maximum_targets = 3;[\s\S]*maximum_private_values = 20000;[\s\S]*maximum_working_numeric_values = 350000;[\s\S]*maximum_figures = 7;",
        }
        for name, pattern in assignments.items():
            self.assertRegex(self.source, pattern, name)
        self.assertEqual(validate_controls(copy.deepcopy(BASE_CONTROLS)), [])

    def test_control_validation_rejects_malformed_nonfinite_and_bounds(self):
        mutations = {
            "missing": lambda value: value.pop("range"),
            "malformed": lambda value: value.__setitem__("velocity_sweep", "fast"),
            "column-shaped sweep": lambda value: value.__setitem__("range_sweep", [[15], [30], [45]]),
            "nonfinite": lambda value: value.__setitem__("velocity", math.inf),
            "negative bandwidth": lambda value: value.__setitem__("bandwidth", -1),
            "no overlap": lambda value: value.__setitem__("range_sweep", [45, 80, 7000]),
            "unordered range": lambda value: value.__setitem__("range_sweep", [15, 45, 30]),
            "missing zero velocity": lambda value: value.__setitem__("velocity_sweep", [-30, -15, 15, 30]),
            "noise starts above zero": lambda value: value.__setitem__("noise_sweep", [0.002, 0.01, 0.03]),
            "multi length mismatch": lambda value: value.__setitem__("multi_phase", [0.2]),
            "unresolved peaks": lambda value: value.__setitem__("min_separation", 150e3),
            "Nyquist": lambda value: value.__setitem__("velocity_sweep", [-1e8, 0, 1e8]),
            "sample bound": lambda value: value.__setitem__("duration", 100e-6),
            "ceiling drift": lambda value: value.__setitem__("max_figures", 70),
            "private bound": lambda value: value.__setitem__("max_private", 100),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                values = copy.deepcopy(BASE_CONTROLS)
                mutate(values)
                self.assertTrue(validate_controls(values))

    def test_control_validation_rejects_one_sample_common_overlap(self):
        values = copy.deepcopy(BASE_CONTROLS)
        values["range_sweep"] = [45.0, 75.0, 5997.0]
        sample_count = round(values["fs"] * values["duration"])
        delay_s = 2 * max(values["range_sweep"]) / values["c"]
        overlap_count = sum(index / values["fs"] >= delay_s for index in range(sample_count))
        self.assertEqual(overlap_count, 1)
        self.assertIn("common overlap invalid", validate_controls(values))
        self.assertIn("overlap_count_local >= 2", self.source)

    def test_private_generator_is_repeatable_distinct_and_bounded(self):
        first = private_complex_noise(7201, 3200)
        repeated = private_complex_noise(7201, 3200)
        down_leg = private_complex_noise(7202, 3200)
        self.assertEqual(first, repeated)
        self.assertNotEqual(first[:8], down_leg[:8])
        self.assertAlmostEqual(first[0].real, 1.2401067226574614, places=12)
        self.assertAlmostEqual(first[0].imag, -1.1567938380657896, places=12)
        with self.assertRaises(ValueError):
            private_complex_noise(7201, 10001)
        with self.assertRaises(ValueError):
            park_miller_uniform(0, 2)

    def test_full_signal_oracle_recovers_range_and_velocity(self):
        result = oracle_pair()
        self.assertEqual(result["sample_count"], 3200)
        self.assertEqual(result["valid_count"], 3176)
        self.assertAlmostEqual(result["slope"], 0.5e12, places=3)
        self.assertAlmostEqual(result["delay_s"], 0.3e-6, places=15)
        self.assertAlmostEqual(result["doppler_hz"], 10266.666666666666, places=8)
        self.assertAlmostEqual(result["ideal_up_hz"], 139733.3333333333, places=8)
        self.assertAlmostEqual(result["ideal_down_hz"], -160266.6666666667, places=8)
        self.assertLess(abs(result["up_hz"] - result["ideal_up_hz"]), 250)
        self.assertLess(abs(result["down_hz"] - result["ideal_down_hz"]), 250)
        self.assertLess(abs(result["range_m"] - 45), 0.08)
        self.assertLess(abs(result["velocity_mps"] - 20), 0.08)

    def test_range_velocity_and_noise_sweeps_isolate_one_variable(self):
        for range_m in BASE_CONTROLS["range_sweep"]:
            result = oracle_pair(range_m=range_m)
            self.assertLess(abs(result["range_m"] - range_m), 0.1)
            self.assertLess(abs(result["velocity_mps"] - 20), 0.1)
        for velocity_mps in BASE_CONTROLS["velocity_sweep"]:
            result = oracle_pair(velocity_mps=velocity_mps)
            self.assertLess(abs(result["range_m"] - 45), 0.1)
            self.assertLess(abs(result["velocity_mps"] - velocity_mps), 0.1)
        noiseless = oracle_pair(noise_rms=0)
        self.assertLess(abs(noiseless["range_m"] - 45), 1e-9)
        self.assertLess(abs(noiseless["velocity_mps"] - 20), 1e-9)
        for noise_rms in BASE_CONTROLS["noise_sweep"]:
            result = oracle_pair(noise_rms=noise_rms)
            self.assertTrue(math.isfinite(result["range_m"]))
            self.assertTrue(math.isfinite(result["velocity_mps"]))

    def test_wrong_multi_target_pairing_creates_ghosts_and_same_data_recovers(self):
        c_mps = 3e8
        slope = 20e6 / 40e-6
        wavelength = c_mps / 77e9
        ranges = BASE_CONTROLS["multi_range"]
        velocities = BASE_CONTROLS["multi_velocity"]
        up_hz = sorted(2 * slope * item / c_mps - 2 * velocity / wavelength for item, velocity in zip(ranges, velocities))
        down_hz = sorted(-2 * slope * item / c_mps - 2 * velocity / wavelength for item, velocity in zip(ranges, velocities))
        ghost_ranges, ghost_velocities = solve_pair(up_hz, down_hz)
        recovered_ranges, recovered_velocities = solve_pair(up_hz, list(reversed(down_hz)))
        self.assertAlmostEqual(up_hz[0], 92300.0, places=8)
        self.assertAlmostEqual(up_hz[1], 221800.0, places=8)
        self.assertAlmostEqual(down_hz[0], -211533.33333333334, places=8)
        self.assertAlmostEqual(down_hz[1], -107700.0, places=8)
        self.assertAlmostEqual(ghost_ranges[0], 45.575, places=12)
        self.assertAlmostEqual(ghost_ranges[1], 49.425, places=12)
        self.assertTrue(all(abs(item) > 90 for item in ghost_velocities))
        self.assertEqual(recovered_ranges, ranges)
        for actual, expected in zip(recovered_velocities, velocities):
            self.assertAlmostEqual(actual, expected, places=12)
        self.assertIn("unchanged detected beat lists", self.documents["lesson.md"])
        self.assertIn("association cue", self.documents["walkthrough.md"])

    def test_composite_echo_peak_path_creates_ghosts_and_recovers(self):
        for marker in (
            "window = 0.5-0.5*cos",
            "fft_count = 8*2^nextpow2(sample_count_local);",
            "spectrum = fftshift(fft(samples(:).*window, fft_count))/sum(window);",
            "blank_half_width = max(1, ceil(minimum_separation_hz /",
            "offset = 0.5*(left_value-right_value)/denominator;",
            "search_magnitude(blank_start:blank_stop) = 0;",
        ):
            self.assertIn(marker, self.source)
        result = composite_pairing_oracle()
        self.assertEqual(result["valid_count"], 3165)
        self.assertEqual(result["detected_up_hz"], sorted(result["detected_up_hz"]))
        self.assertEqual(result["detected_down_hz"], sorted(result["detected_down_hz"]))
        for actual, expected in zip(result["detected_up_hz"], (92300.0, 221800.0)):
            self.assertLess(abs(actual - expected), 600)
        for actual, expected in zip(
            result["detected_down_hz"], (-211533.33333333334, -107700.0)
        ):
            self.assertLess(abs(actual - expected), 600)
        for ghost in result["ghost_range_m"]:
            self.assertGreater(min(abs(ghost - truth) for truth in (30, 65)), 5)
        for actual, expected in zip(result["recovered_range_m"], (30, 65)):
            self.assertLess(abs(actual - expected), 0.8)
        for actual, expected in zip(result["recovered_velocity_mps"], (15, -10)):
            self.assertLess(abs(actual - expected), 1.5)

    def test_documents_are_concept_first_and_cover_limits_and_checks(self):
        combined = "\n".join(self.documents.values()).lower()
        for marker in (
            "two slopes", "signed", "difference", "sum", "positive approaching",
            "range sweep", "velocity sweep", "noise sweep", "distinct",
            "wrong pairing", "association", "zero velocity", "zero delay",
            "zero slope", "nyquist", "overlap", "sequential", "acceleration",
            "zero-padding", "cancellation", "rollback", "teach-back",
            "no optional toolbox",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(self.documents["checks.md"].count("**Correct:**"), 38)

    def test_cli_timeout_isolation_rollback_recovery_and_future_compatibility(self):
        compatible = copy.deepcopy(self.data)
        module_entry(compatible, "P73")["status"] = "implemented"
        module_entry(compatible, "P73")["future_metadata"] = {"allowed": True}
        original_repository_state = ROOT / ".learning/progress.json"
        before = original_repository_state.read_bytes() if original_repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.make_cli_fixture(Path(directory), compatible)
            result = self.run_cli(fixture, "start", "72")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P72", result.stdout)
            self.assertIn("status: implemented", result.stdout)

            rolled_back = copy.deepcopy(compatible)
            module_entry(rolled_back, "P72")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(
                json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8"
            )
            refused = self.run_cli(fixture, "start", "72")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P72", refused.stdout)

            (fixture / "curriculum/modules.json").write_text(
                json.dumps(compatible, indent=2) + "\n", encoding="utf-8"
            )
            recovered = self.run_cli(fixture, "start", "72")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = original_repository_state.read_bytes() if original_repository_state.exists() else None
        self.assertEqual(after, before)
        walkthrough = " ".join(self.documents["walkthrough.md"].lower().split())
        for marker in ("ctrl+c", "no worker", "no external persistent state", "rerun from the top", "rollback"):
            self.assertIn(marker, walkthrough)

    def test_compatibility_resources_catalogs_evidence_and_eof_policy(self):
        combined = "\n".join(self.documents.values()).lower()
        self.assertIn("matlab r2016b or newer", combined)
        self.assertIn("base matlab", combined)
        self.assertIn("350,000", combined)
        self.assertIn("seven tagged figure", combined)
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 72 adds an equal-magnitude down-chirp measurement", root_readme)
        self.assertIn("Project 72 follows P71", start_here)
        self.assertRegex(module_index, r"\| \[P72\].*\| implemented \|")
        evidence = EVIDENCE.read_text(encoding="utf-8")
        for heading in (
            "## Claim boundary", "## Acceptance map", "## Deterministic simulated-oracle results",
            "## Figure and metric inventory", "## Exact commands and results",
            "## Changed and preserved invariants", "## Residual risks",
            "## Rollback", "## Unperformed validation",
        ):
            self.assertIn(heading, evidence)
        changed_text_paths = [
            *[MODULE / name for name in ARTIFACTS], ROOT / "curriculum/modules.json",
            ROOT / "README.md", ROOT / "START_HERE.md", ROOT / "modules/README.md",
            ROOT / "tests/test_p72_module.py", EVIDENCE,
        ]
        for path in changed_text_paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
