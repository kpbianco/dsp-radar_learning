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
MODULE = ROOT / "modules/69-derive-fmcw-range-from-beat-frequency"
QUESTION = "Why does a delayed chirp produce a nearly constant beat frequency?"
EXPECTED_IDENTITY = {
    "number": 69,
    "id": "P69",
    "title": "Derive FMCW Range from Beat Frequency",
    "guiding_question": QUESTION,
    "phase": 8,
    "phase_title": "FMCW, MIMO, and Micro-Doppler",
    "slug": "derive-fmcw-range-from-beat-frequency",
    "folder": "modules/69-derive-fmcw-range-from-beat-frequency",
    "status": "implemented",
    "implementation_batch": "P69",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
SOURCE_MARKERS = (
    "baseline_seed = 6901;",
    "speed_of_light_mps = 3.0e8;",
    "sample_rate_hz = 80.0e6;",
    "chirp_duration_s = 40.0e-6;",
    "chirp_bandwidth_hz = 20.0e6;",
    "target_range_m = 45.0;",
    "chirp_slope_hz_per_s = chirp_bandwidth_hz/chirp_duration_s;",
    "round_trip_delay_s = 2*target_range_m/speed_of_light_mps;",
    "valid_overlap = time_s >= round_trip_delay_s & time_s < chirp_duration_s;",
    "transmit_phase_rad = pi*chirp_slope_hz_per_s* ...",
    "delayed_time_s = time_s-round_trip_delay_s;",
    "received_chirp(valid_overlap) = echo_voltage*exp(1j*pi* ...",
    "dechirped_beat = transmitted_chirp(valid_overlap).* ...",
    "conj(received_chirp(valid_overlap));",
    "beat_spectrum = fft(windowed_beat, fft_length);",
    "estimated_range_m = speed_of_light_mps*estimated_beat_frequency_hz / ...",
    "(2*chirp_slope_hz_per_s);",
    "phase_beat_frequency_hz > 0 && ...",
    "range_sweep_m = [15 30 45 60 75];",
    "slope_bandwidth_sweep_hz = [10 15 20 25 30]*1.0e6;",
    "case_delay_s = 2*case_range_m/speed_of_light_mps;",
    "slope_sweep_theory_hz = slope_sweep_hz_per_s*round_trip_delay_s;",
    "broken_one_way_range_m = speed_of_light_mps*estimated_beat_frequency_hz / ...",
    "recovered_monostatic_range_m = speed_of_light_mps* ...",
    "'P69:BaselineBeat'",
    "'P69:RangeSweep'",
    "'P69:SlopeSweep'",
    "'P69:BrokenFactor'",
    "'P69:SameMeasurementRecovery'",
    "maximum_samples = 4096;",
    "maximum_fft_length = 131072;",
    "maximum_sweep_cases = 8;",
    "maximum_private_values = 100000;",
    "maximum_working_numeric_values = 1000000;",
    "maximum_figures = 6;",
    "maximum_range_m = max([c.range_m c.range_sweep_m(:).']);",
    "validate_controls(controls);",
    "'P69:PreflightWorkingBound'",
    "'P69:WorkingBound'",
    "state = mod(16807*state, 2147483647);",
    "samples = sqrt(-2*log(first)).*exp(1j*2*pi*second)/sqrt(2);",
    "noise = reshape(samples, number_rows, number_columns);",
    "p69_results = struct( ...",
    "close(findall(0, 'Type', 'figure', 'Tag', 'P69'));",
    "clear p69_results;",
)
FORBIDDEN_LITERAL_TOKENS = (
    "phased.", "dechirp(", "beat2range(", "range2beat(", "delayseq(",
    "circshift(", "awgn(", "rng(", "rand(", "randn(", "parfor",
    "timer(", "webread", "urlread", "system(", "fopen(", "save(",
    "clear all", "clearvars", "delete(", "close all",
)
MODULUS = 2_147_483_647
MULTIPLIER = 16_807


def executable_source(source: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in source.splitlines())


def p69_source_errors(source: object) -> list[str]:
    if not isinstance(source, str) or not source:
        return ["P69 source must be nonempty text"]
    executable = executable_source(source)
    errors = [
        f"missing source marker: {marker}"
        for marker in SOURCE_MARKERS
        if marker not in executable
    ]
    if executable.count("figure('Name', 'P69") != 6:
        errors.append("P69 must create exactly six named figures")
    if executable.count("'Tag', 'P69'") != 7:
        errors.append("P69 must tag six figures and one scoped cleanup")
    errors.extend(
        f"forbidden source token: {token}"
        for token in FORBIDDEN_LITERAL_TOKENS
        if token in executable
    )
    if re.search(r"(?<![A-Za-z0-9_])chirp\s*\(", executable):
        errors.append("forbidden chirp toolbox call")
    if re.search(r"(?m)^\s*!", executable):
        errors.append("forbidden shell escape")
    return errors


def validate_p69_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P69 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [
        entry
        for entry in manifest["modules"]
        if isinstance(entry, dict) and entry.get("id") == "P69"
    ]
    if len(matches) != 1:
        errors.append("P69 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P69 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P69 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P69 empty {artifact}")
    return errors


def reviewed_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "seed": 6901,
        "c": 3.0e8,
        "fs": 80.0e6,
        "duration": 40.0e-6,
        "bandwidth": 20.0e6,
        "range": 45.0,
        "echo": 0.70,
        "noise": 0.01,
        "fft": 65536,
        "ranges": (15.0, 30.0, 45.0, 60.0, 75.0),
        "bandwidths": (10.0e6, 15.0e6, 20.0e6, 25.0e6, 30.0e6),
        "floor": -80.0,
        "max_samples": 4096,
        "max_fft": 131072,
        "max_sweeps": 8,
        "max_private": 100000,
        "max_working": 1000000,
        "max_figures": 6,
    }
    controls.update(overrides)
    return controls


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_controls(c: object) -> None:
    if not isinstance(c, dict) or set(c) != set(reviewed_controls()):
        raise ValueError("controls")
    vectors = {"ranges", "bandwidths"}
    if not all(finite_real(value) for key, value in c.items() if key not in vectors):
        raise ValueError("scalar")
    for name in vectors:
        values = c[name]
        if (
            not isinstance(values, (tuple, list))
            or not 3 <= len(values) <= c["max_sweeps"]
            or not all(finite_real(value) for value in values)
            or any(right <= left for left, right in zip(values, values[1:]))
        ):
            raise ValueError("vector")
    integers = {
        "seed", "fft", "max_samples", "max_fft", "max_sweeps",
        "max_private", "max_working", "max_figures",
    }
    if not all(c[name] > 0 and c[name] == int(c[name]) for name in integers):
        raise ValueError("integer")
    if c["c"] <= 0 or c["fs"] <= 0 or c["duration"] <= 0:
        raise ValueError("physical")
    samples = c["fs"] * c["duration"]
    maximum_delay = 2 * max(c["range"], *c["ranges"]) / c["c"]
    maximum_bandwidth = max(c["bandwidth"], *c["bandwidths"])
    maximum_beat = maximum_bandwidth / c["duration"] * maximum_delay
    if not (
        c["c"] > 0
        and c["fs"] > 0
        and c["duration"] > 0
        and c["bandwidth"] > 0
        and c["range"] > 0
        and 0 < c["echo"] <= 1
        and 0 <= c["noise"] <= 1
        and abs(samples - round(samples)) < 1e-9
        and 128 <= samples <= c["max_samples"]
        and maximum_bandwidth < c["fs"]
        and maximum_beat < c["fs"] / 2
        and maximum_delay < c["duration"]
        and round(samples - c["fs"] * maximum_delay) >= 128
        and samples <= c["fft"] <= c["max_fft"]
        and c["fft"] & (c["fft"] - 1) == 0
        and -200 <= c["floor"] <= -20
    ):
        raise ValueError("physical")
    immutable = {
        "max_samples": 4096,
        "max_fft": 131072,
        "max_sweeps": 8,
        "max_private": 100000,
        "max_working": 1000000,
        "max_figures": 6,
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


def private_complex_noise(seed: int, count: int) -> tuple[complex, ...]:
    values = private_uniform(seed, 2 * count)
    return tuple(
        math.sqrt(-2 * math.log(max(values[index], float.fromhex("0x0.0000000000001p-1022"))))
        * cmath.exp(1j * 2 * math.pi * values[count + index])
        / math.sqrt(2)
        for index in range(count)
    )


def radix2_fft(signal: tuple[complex, ...], nfft: int) -> list[complex]:
    if nfft < len(signal) or nfft <= 0 or nfft & (nfft - 1):
        raise ValueError("nfft")
    spectrum = list(signal) + [0j] * (nfft - len(signal))
    reversed_index = 0
    for index in range(1, nfft):
        bit = nfft >> 1
        while reversed_index & bit:
            reversed_index ^= bit
            bit >>= 1
        reversed_index ^= bit
        if index < reversed_index:
            spectrum[index], spectrum[reversed_index] = spectrum[reversed_index], spectrum[index]
    block_length = 2
    while block_length <= nfft:
        block_twiddle = cmath.exp(-2j * math.pi / block_length)
        half_length = block_length // 2
        for block_start in range(0, nfft, block_length):
            twiddle = 1 + 0j
            for offset in range(half_length):
                even = spectrum[block_start + offset]
                odd = twiddle * spectrum[block_start + offset + half_length]
                spectrum[block_start + offset] = even + odd
                spectrum[block_start + offset + half_length] = even - odd
                twiddle *= block_twiddle
        block_length *= 2
    return spectrum


def full_fft_peak(signal: tuple[complex, ...], fs: float, nfft: int) -> float:
    window = tuple(
        0.5 - 0.5 * math.cos(2 * math.pi * index / (len(signal) - 1))
        for index in range(len(signal))
    )
    spectrum = radix2_fft(
        tuple(sample * weight for sample, weight in zip(signal, window)), nfft
    )
    powers = [abs(value) ** 2 for value in spectrum[: nfft // 2 + 1]]
    peak_bin = max(range(1, len(powers)), key=powers.__getitem__)
    if peak_bin >= len(powers) - 1:
        raise AssertionError("oracle peak reached Nyquist")
    log_power = [
        math.log(max(value, float.fromhex("0x0.0000000000001p-1022")))
        for value in powers[peak_bin - 1 : peak_bin + 2]
    ]
    denominator = log_power[0] - 2 * log_power[1] + log_power[2]
    if abs(denominator) <= 100 * math.ulp(max(abs(value) for value in log_power)):
        offset = 0.0
    else:
        offset = 0.5 * (log_power[0] - log_power[2]) / denominator
    offset = max(-0.5, min(0.5, offset))
    return (peak_bin + offset) * fs / nfft


def exact_case(range_m: float = 45.0, bandwidth_hz: float = 20.0e6) -> tuple[float, float, float]:
    c = 3.0e8
    fs = 80.0e6
    duration = 40.0e-6
    slope = bandwidth_hz / duration
    delay = 2 * range_m / c
    count = round(fs * duration)
    times = tuple(index / fs for index in range(count))
    noise = private_complex_noise(6901, count)
    beat = []
    for index, time_s in enumerate(times):
        if time_s < delay:
            continue
        transmit = cmath.exp(1j * math.pi * slope * (time_s - duration / 2) ** 2)
        receive = (
            0.70
            * cmath.exp(1j * math.pi * slope * (time_s - delay - duration / 2) ** 2)
            + 0.01 * noise[index]
        )
        beat.append(transmit * receive.conjugate())
    theoretical_hz = slope * delay
    estimated_hz = full_fft_peak(tuple(beat), fs, 65536)
    estimated_range = c * estimated_hz / (2 * slope)
    return theoretical_hz, estimated_hz, estimated_range


class P69ModuleTests(unittest.TestCase):
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
        self.assertEqual(validate_p69_contract(ROOT, self.manifest), [])
        p68 = next(module for module in self.manifest["modules"] if module["id"] == "P68")
        self.assertEqual(p68["status"], "implemented")

    def test_contract_rejects_malformed_duplicate_drift_missing_and_empty(self):
        self.assertTrue(validate_p69_contract(ROOT, None))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append(None)
        self.assertIn("every manifest module must be an object", validate_p69_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("P69 must have exactly one manifest entry", validate_p69_contract(ROOT, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(module for module in drifted["modules"] if module["id"] == "P69")["guiding_question"] = "changed"
        self.assertIn("P69 manifest identity drift", validate_p69_contract(ROOT, drifted))
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            module = fixture / EXPECTED_IDENTITY["folder"]
            module.mkdir(parents=True)
            for artifact in ARTIFACTS[1:]:
                (module / artifact).write_text("content\n", encoding="utf-8")
            self.assertIn("P69 missing README.md", validate_p69_contract(fixture, self.manifest))
            (module / "README.md").write_text("\n", encoding="utf-8")
            self.assertIn("P69 empty README.md", validate_p69_contract(fixture, self.manifest))

    def test_source_exposes_determinism_model_sweeps_failure_recovery_and_bounds(self):
        self.assertEqual(p69_source_errors(self.source), [])
        for mutation, expected in (
            (self.source.replace("baseline_seed = 6901;", "baseline_seed = 1;", 1), "missing source marker"),
            (self.source.replace("valid_overlap = time_s >= round_trip_delay_s & time_s < chirp_duration_s;", "valid_overlap = true(size(time_s));", 1), "missing source marker"),
            (self.source.replace("beat_spectrum = fft(windowed_beat, fft_length);", "beat_spectrum = windowed_beat;", 1), "missing source marker"),
            (self.source.replace("recovered_monostatic_range_m = speed_of_light_mps* ...", "recovered_monostatic_range_m = broken_one_way_range_m; %", 1), "missing source marker"),
        ):
            with self.subTest(expected=expected):
                self.assertTrue(any(expected in error for error in p69_source_errors(mutation)))
        self.assertTrue(p69_source_errors(self.source + "\nvalue = chirp(time_s, 1, 2, 'linear');\n"))

    def test_controls_accept_reviewed_and_reject_malformed_resource_inputs(self):
        validate_controls(reviewed_controls())
        invalid = (
            None,
            reviewed_controls(fs=True),
            reviewed_controls(duration=math.nan),
            reviewed_controls(seed=1.5),
            reviewed_controls(ranges=(15.0, 15.0, 30.0)),
            reviewed_controls(ranges=(15.0, math.inf, 30.0)),
            reviewed_controls(ranges=tuple(float(value) for value in range(9))),
            reviewed_controls(c=0),
            reviewed_controls(fs=30.0e6),
            reviewed_controls(duration=40.01e-6),
            reviewed_controls(bandwidth=0),
            reviewed_controls(range=0),
            reviewed_controls(range=7000.0),
            reviewed_controls(echo=1.1),
            reviewed_controls(noise=-0.1),
            reviewed_controls(fft=60000),
            reviewed_controls(fft=2048),
            reviewed_controls(floor=-10),
            reviewed_controls(ranges=(15.0, 30.0, 5.0e6)),
            reviewed_controls(bandwidths=(10.0e6, 20.0e6, 90.0e6)),
            reviewed_controls(range=5000.0, bandwidths=(10.0e6, 30.0e6, 50.0e6)),
            reviewed_controls(max_samples=5000),
            reviewed_controls(max_fft=262144),
            reviewed_controls(max_sweeps=9),
            reviewed_controls(max_private=100001),
            reviewed_controls(max_working=1000001),
            reviewed_controls(max_figures=7),
        )
        for controls in invalid:
            with self.subTest(controls=controls):
                with self.assertRaises(ValueError):
                    validate_controls(controls)

    def test_private_generator_is_exact_repeatable_isolated_and_bounded(self):
        values = private_uniform(6901, 5)
        expected = (
            0.054009774259296144,
            0.7422759759902376,
            0.4323284679243008,
            0.14456040372353066,
            0.6267053813797913,
        )
        for observed, wanted in zip(values, expected):
            self.assertAlmostEqual(observed, wanted, places=15)
        self.assertEqual(values, private_uniform(6901, 5))
        self.assertNotEqual(values, private_uniform(6902, 5))
        self.assertEqual(len(private_complex_noise(6901, 3200)), 3200)
        for bad_seed in (True, 0, MODULUS, math.nan):
            with self.assertRaises(ValueError):
                private_uniform(bad_seed, 1)
        for bad_count in (True, 0, 1.5, 100001, math.inf):
            with self.assertRaises(ValueError):
                private_uniform(6901, bad_count)

    def test_ideal_sampled_dechirp_has_constant_positive_frequency(self):
        fs = 80.0e6
        duration = 40.0e-6
        slope = 20.0e6 / duration
        delay = 2 * 45.0 / 3.0e8
        times = [index / fs for index in range(round(fs * duration)) if index / fs >= delay]
        beat = [
            cmath.exp(1j * math.pi * slope * (time - duration / 2) ** 2)
            * cmath.exp(-1j * math.pi * slope * (time - delay - duration / 2) ** 2)
            for time in times
        ]
        increments = [left.conjugate() * right for left, right in zip(beat, beat[1:])]
        expected = cmath.exp(1j * 2 * math.pi * slope * delay / fs)
        self.assertGreater(cmath.phase(expected), 0)
        self.assertLess(max(abs(value - expected) for value in increments), 2e-11)

    def test_exact_deterministic_baseline_oracle_reproduces_retained_metrics(self):
        theoretical, estimated, estimated_range = exact_case()
        self.assertAlmostEqual(theoretical, 150000.0, places=9)
        self.assertAlmostEqual(estimated, 150005.34204346416, places=7)
        self.assertAlmostEqual(estimated_range, 45.00160261303925, places=9)
        self.assertLess(abs(estimated - theoretical), 2 * 80.0e6 / 65536)

    def test_full_spectrum_peak_search_is_not_biased_to_the_expected_bin(self):
        fs = 8.0e6
        count = 1024
        expected_tone_hz = 150.0e3
        stronger_unexpected_tone_hz = 500.0e3
        signal = tuple(
            cmath.exp(2j * math.pi * expected_tone_hz * index / fs)
            + 2 * cmath.exp(2j * math.pi * stronger_unexpected_tone_hz * index / fs)
            for index in range(count)
        )
        observed_hz = full_fft_peak(signal, fs, 4096)
        self.assertLess(abs(observed_hz - stronger_unexpected_tone_hz), fs / 4096)
        self.assertGreater(abs(observed_hz - expected_tone_hz), 100.0e3)

    def test_range_and_slope_sweeps_obey_the_physical_oracle(self):
        range_results = [exact_case(range_m=value) for value in (15.0, 30.0, 45.0, 60.0, 75.0)]
        expected_beats = (50000.0, 100000.0, 150000.0, 200000.0, 250000.0)
        for known, result, expected_beat in zip((15.0, 30.0, 45.0, 60.0, 75.0), range_results, expected_beats):
            self.assertAlmostEqual(result[0], expected_beat, places=7)
            self.assertLess(abs(result[2] - known), 0.01)
        slope_results = [exact_case(bandwidth_hz=value) for value in (10.0e6, 15.0e6, 20.0e6, 25.0e6, 30.0e6)]
        expected_slope_beats = (75000.0, 112500.0, 150000.0, 187500.0, 225000.0)
        for result, expected_beat in zip(slope_results, expected_slope_beats):
            self.assertAlmostEqual(result[0], expected_beat, places=7)
            self.assertLess(abs(result[2] - 45.0), 0.01)

    def test_broken_factor_two_and_same_measurement_recovery(self):
        _, estimated_beat, recovered = exact_case()
        slope = 20.0e6 / 40.0e-6
        broken = 3.0e8 * estimated_beat / slope
        self.assertAlmostEqual(broken, 2 * recovered, places=12)
        self.assertGreater(abs(broken - 45.0), 40.0)
        self.assertLess(abs(recovered - 45.0), 0.01)

    def test_documents_are_concept_first_complete_and_not_placeholders(self):
        documents = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        for name, document in documents.items():
            with self.subTest(document=name):
                self.assertIn(QUESTION, document)
                self.assertNotIn("TODO", document)
        lesson = documents["lesson.md"]
        for marker in ("S = B/T", "tau = 2R/c", "f_b = S tau", "R = c f_b/(2S)", "valid overlap", "Limiting cases and claim boundary"):
            self.assertIn(marker, lesson)
        walkthrough = documents["walkthrough.md"]
        for marker in ("Sweep 1", "Sweep 2", "Broken case", "Recovery", "Ctrl+C", "unchanged"):
            self.assertIn(marker, walkthrough)
        checks = documents["checks.md"]
        self.assertIn("Short teach-back rubric", checks)
        self.assertGreaterEqual(checks.count("**Correct:**"), 26)

    def test_cli_start_advance_rollback_recovery_timeout_and_isolation(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.make_fixture(base, self.manifest)
            started = self.run_cli(fixture, "start", "69")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P69", started.stdout)
            self.assertIn("status: implemented", started.stdout)
            state = fixture / ".learning/progress.json"
            state.write_text(
                json.dumps({"schema_version": 1, "current": "P68", "completed": [f"P{number:02d}" for number in range(1, 69)], "notes": {}}) + "\n",
                encoding="utf-8",
            )
            advanced = self.run_cli(fixture, "start")
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertIn("P69 — Derive FMCW Range", advanced.stdout)
            era_manifest = copy.deepcopy(self.manifest)
            for module in era_manifest["modules"]:
                if module["number"] > 69:
                    module["status"] = "scaffolded"
            rolled_back = copy.deepcopy(era_manifest)
            next(module for module in rolled_back["modules"] if module["id"] == "P69")["status"] = "scaffolded"
            original_p68 = copy.deepcopy(next(module for module in rolled_back["modules"] if module["id"] == "P68"))
            original_p70_identity = {
                key: value
                for key, value in next(module for module in self.manifest["modules"] if module["id"] == "P70").items()
                if key != "status"
            }
            rollback_fixture = self.make_fixture(base / "rollback", rolled_back)
            refused = self.run_cli(rollback_fixture, "start", "69")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P69", refused.stdout)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P68"), original_p68)
            self.assertEqual(
                {key: value for key, value in next(module for module in rolled_back["modules"] if module["id"] == "P70").items() if key != "status"},
                original_p70_identity,
            )
            (rollback_fixture / "curriculum/modules.json").write_text(
                json.dumps(era_manifest, indent=2) + "\n", encoding="utf-8"
            )
            recovered = self.run_cli(rollback_fixture, "start", "69")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_cancellation_external_side_effect_and_rerun_boundaries(self):
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P69'));", self.source)
        self.assertIn("clear p69_results;", self.source)
        for token in ("parfor", "timer(", "fopen(", "save(", "system(", "webread"):
            self.assertNotIn(token, executable_source(self.source))
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        normalized = " ".join(walkthrough.split())
        self.assertIn("Ctrl+C", walkthrough)
        self.assertIn("no worker, timer", walkthrough)
        self.assertIn("intermediate variables", normalized)
        self.assertIn("no background or external persistent state", normalized)

    def test_public_catalogs_preserve_dependency_and_future_extension(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 69 follows P68", readme)
        self.assertIn("Project 69 follows P68", start_here)
        self.assertRegex(index, r"\| \[P69\].*\| implemented \| 8 \|")
        p70 = next(module for module in self.manifest["modules"] if module["id"] == "P70")
        self.assertEqual(p70["title"], "Create an FMCW Range-Doppler Map")

    def test_evidence_maps_acceptance_commands_claims_and_rollback(self):
        paths = sorted((ROOT / "docs/evidence").glob("P69-*.md"))
        self.assertEqual(len(paths), 1)
        evidence = paths[0].read_text(encoding="utf-8")
        for marker in (
            "# P69 Retained Evidence",
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
            "69 implemented",
            "operator-managed",
        ):
            self.assertIn(marker, evidence)
        self.assertNotIn("recorded after execution", evidence)
        self.assertNotIn("no passing result is claimed in advance", evidence)
        self.assertIn("all 1,143 tests", evidence)
        self.assertIn("verify-20260812-032550.log", evidence)
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
                ROOT / "tests/test_p69_module.py",
            ]
        )
        paths.extend(sorted((ROOT / "docs/evidence").glob("P69-*.md")))
        for path in paths:
            with self.subTest(path=path):
                data = path.read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
