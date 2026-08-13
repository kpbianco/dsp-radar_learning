from __future__ import annotations

import cmath
import copy
import json
import math
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/76-perform-sar-range-compression"
EVIDENCE = ROOT / "docs/evidence/P76-2026-08-13.md"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "What information is created before azimuth focusing begins?"

BASE_CONTROLS = {
    "seed": 7601,
    "c_mps": 3.0e8,
    "carrier_hz": 5.0e9,
    "sample_rate_hz": 120.0e6,
    "pulse_duration_s": 2.0e-6,
    "bandwidth_hz": 20.0e6,
    "gate_start_m": 950.0,
    "gate_end_m": 1400.0,
    "aperture_length_m": 80.0,
    "platform_spacing_m": 0.2,
    "target_x_m": [-15.0, 0.0, 18.0],
    "target_y_m": [1000.0, 1025.0, 1070.0],
    "target_voltage": [1.0, 0.8, 0.6],
    "target_phase_rad": [0.0, 0.6, -0.9],
    "noise_rms": 0.2,
    "bandwidth_sweep_hz": [10.0e6, 20.0e6, 40.0e6],
    "spacing_sweep_m": [3.75, 10.0, 15.0],
    "max_aperture_samples": 501,
    "max_fast_time_samples": 401,
    "max_compressed_samples": 701,
    "max_targets": 5,
    "max_sweep_cases": 5,
    "max_private_values": 400000,
    "max_working_values": 12000000,
    "max_figures": 6,
    "max_phase_step_rad": 0.90 * math.pi,
}


def module_entry(data: dict, module_id: str) -> dict:
    return next(item for item in data["modules"] if item["id"] == module_id)


def artifact_errors(folder: Path, status: str = "implemented") -> list[str]:
    errors: list[str] = []
    if status == "implemented":
        for name in ARTIFACTS:
            path = folder / name
            if not path.is_file():
                errors.append(f"missing {name}")
            elif not path.read_text(encoding="utf-8", errors="replace").strip():
                errors.append(f"empty {name}")
            elif "TODO" in path.read_text(encoding="utf-8", errors="replace"):
                errors.append(f"TODO remains in {name}")
    return errors


def controls_errors(controls: dict) -> list[str]:
    errors: list[str] = []
    vectors = (
        "target_x_m", "target_y_m", "target_voltage", "target_phase_rad",
        "bandwidth_sweep_hz", "spacing_sweep_m",
    )
    for name in vectors:
        value = controls.get(name)
        if (
            not isinstance(value, list)
            or not value
            or any(isinstance(item, (bool, complex, list, tuple)) for item in value)
            or any(not isinstance(item, (int, float)) or not math.isfinite(item) for item in value)
        ):
            errors.append(f"invalid row vector: {name}")
    if errors:
        return errors
    target_count = len(controls["target_x_m"])
    if any(len(controls[name]) != target_count for name in ("target_y_m", "target_voltage", "target_phase_rad")):
        errors.append("target length mismatch")
    scalar_names = (
        "c_mps", "carrier_hz", "sample_rate_hz", "pulse_duration_s",
        "bandwidth_hz", "gate_start_m", "gate_end_m", "aperture_length_m",
        "platform_spacing_m", "noise_rms", "max_aperture_samples",
        "max_fast_time_samples", "max_compressed_samples", "max_targets",
        "max_sweep_cases", "max_private_values", "max_working_values",
        "max_figures", "max_phase_step_rad",
    )
    for name in scalar_names:
        value = controls.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"invalid scalar: {name}")
    seed = controls.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 1 <= seed < 2147483647:
        errors.append("invalid seed")
    if errors:
        return errors
    positive = (
        "c_mps", "carrier_hz", "sample_rate_hz", "pulse_duration_s",
        "bandwidth_hz", "gate_start_m", "gate_end_m", "aperture_length_m",
        "platform_spacing_m", "max_aperture_samples", "max_fast_time_samples",
        "max_compressed_samples", "max_targets", "max_sweep_cases",
        "max_private_values", "max_working_values", "max_figures",
        "max_phase_step_rad",
    )
    if any(controls[name] <= 0 for name in positive):
        errors.append("nonpositive scalar")
    if controls["noise_rms"] < 0 or controls["gate_end_m"] <= controls["gate_start_m"]:
        errors.append("noise or gate invalid")
    if any(value <= 0 for value in controls["target_y_m"] + controls["target_voltage"] + controls["bandwidth_sweep_hz"] + controls["spacing_sweep_m"]):
        errors.append("nonpositive vector")
    if any(right <= left for left, right in zip(controls["bandwidth_sweep_hz"], controls["bandwidth_sweep_hz"][1:])) or any(right <= left for left, right in zip(controls["spacing_sweep_m"], controls["spacing_sweep_m"][1:])):
        errors.append("sweep order")
    if controls["bandwidth_hz"] >= controls["sample_rate_hz"] / 2 or max(controls["bandwidth_sweep_hz"]) >= controls["sample_rate_hz"] / 2:
        errors.append("Nyquist margin")
    pulse_exact = controls["sample_rate_hz"] * controls["pulse_duration_s"]
    if abs(pulse_exact - round(pulse_exact)) > 1e-9:
        errors.append("off-grid pulse")
    aperture_exact = controls["aperture_length_m"] / (2 * controls["platform_spacing_m"])
    if abs(aperture_exact - round(aperture_exact)) > 1e-9:
        errors.append("off-grid aperture")
    range_spacing = controls["c_mps"] / (2 * controls["sample_rate_hz"])
    gate_exact = (controls["gate_end_m"] - controls["gate_start_m"]) / range_spacing
    if abs(gate_exact - round(gate_exact)) > 1e-9:
        errors.append("off-grid gate")
    if controls["max_phase_step_rad"] >= math.pi:
        errors.append("unsafe phase limit")
    if controls["max_figures"] < 6:
        errors.append("figure ceiling")
    if errors:
        return errors
    aperture_samples = round(controls["aperture_length_m"] / controls["platform_spacing_m"]) + 1
    fast_samples = round(gate_exact) + 1
    pulse_samples = round(pulse_exact)
    compressed_samples = fast_samples + pulse_samples - 1
    if aperture_samples > controls["max_aperture_samples"] or fast_samples > controls["max_fast_time_samples"] or compressed_samples > controls["max_compressed_samples"] or target_count > controls["max_targets"]:
        errors.append("sample ceiling")
    if max(len(controls["bandwidth_sweep_hz"]), len(controls["spacing_sweep_m"])) > controls["max_sweep_cases"]:
        errors.append("sweep ceiling")
    if len(controls["bandwidth_sweep_hz"]) != 3 or len(controls["spacing_sweep_m"]) != 3:
        errors.append("sweep count")
    if any(abs(value / range_spacing - round(value / range_spacing)) > 1e-9 for value in controls["spacing_sweep_m"]):
        errors.append("spacing grid")
    largest_pair_delay = round((1000.0 + max(controls["spacing_sweep_m"]) - controls["gate_start_m"]) / range_spacing)
    if largest_pair_delay < 0 or largest_pair_delay + pulse_samples > fast_samples:
        errors.append("spacing support")
    if 2 * aperture_samples * fast_samples > controls["max_private_values"]:
        errors.append("private ceiling")
    predicted = (
        18 * aperture_samples * compressed_samples
        + 12 * aperture_samples * fast_samples
        + 20 * target_count * aperture_samples
        + 20 * compressed_samples * (len(controls["bandwidth_sweep_hz"]) + len(controls["spacing_sweep_m"]))
    )
    if predicted > controls["max_working_values"]:
        errors.append("working ceiling")
    if errors:
        return errors
    wavelength = controls["c_mps"] / controls["carrier_hz"]
    positions = [-controls["aperture_length_m"] / 2 + index * controls["platform_spacing_m"] for index in range(aperture_samples)]
    for target_x, target_y in zip(controls["target_x_m"], controls["target_y_m"]):
        ranges = [math.hypot(position - target_x, target_y) for position in positions]
        phases = [-4 * math.pi * (value - target_y) / wavelength for value in ranges]
        if max(abs(after - before) for before, after in zip(phases, phases[1:])) >= controls["max_phase_step_rad"]:
            errors.append("spatial alias")
        delays = [round((value - controls["gate_start_m"]) / range_spacing) for value in ranges]
        if min(delays) < 0 or max(delays) + pulse_samples > fast_samples:
            errors.append("echo support")
    return errors


def build_lfm(bandwidth_hz: float, duration_s: float = 2e-6, sample_rate_hz: float = 120e6) -> list[complex]:
    if not all(math.isfinite(value) for value in (bandwidth_hz, duration_s, sample_rate_hz)) or bandwidth_hz <= 0 or duration_s <= 0 or sample_rate_hz <= 0 or bandwidth_hz >= sample_rate_hz / 2:
        raise ValueError("invalid LFM controls")
    count_float = duration_s * sample_rate_hz
    count = round(count_float)
    if count < 8 or abs(count - count_float) > 1e-9:
        raise ValueError("invalid LFM samples")
    times = [index / sample_rate_hz - (count - 1) / (2 * sample_rate_hz) for index in range(count)]
    return [cmath.exp(1j * math.pi * (bandwidth_hz / duration_s) * time**2) for time in times]


def private_complex_noise(seed: int, count: int, maximum: int = 400000) -> list[complex]:
    if isinstance(seed, bool) or not isinstance(seed, int) or not 1 <= seed < 2147483647:
        raise ValueError("invalid seed")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1 or 2 * count > maximum:
        raise ValueError("invalid count")
    state = seed
    uniforms: list[float] = []
    for _ in range(2 * count):
        state = (16807 * state) % 2147483647
        uniforms.append(state / 2147483647)
    return [
        math.sqrt(-2 * math.log(max(uniforms[index], float.fromhex("0x1p-1022"))))
        * cmath.exp(1j * 2 * math.pi * uniforms[index + 1])
        / math.sqrt(2)
        for index in range(0, len(uniforms), 2)
    ]


def compressed_profile(waveform: list[complex], delays: list[int], amplitudes: list[complex], record_count: int = 361) -> list[complex]:
    if not waveform or len(delays) != len(amplitudes) or any(delay < 0 or delay + len(waveform) > record_count for delay in delays):
        raise ValueError("unsupported echo")
    received = [0j] * record_count
    for delay, amplitude in zip(delays, amplitudes):
        for index, value in enumerate(waveform):
            received[delay + index] += amplitude * value
    matched_filter = [value.conjugate() for value in reversed(waveform)]
    energy = sum(abs(value) ** 2 for value in waveform)
    output: list[complex] = []
    for output_index in range(record_count + len(waveform) - 1):
        input_min = max(0, output_index - len(matched_filter) + 1)
        input_max = min(record_count - 1, output_index)
        output.append(sum(received[index] * matched_filter[output_index - index] for index in range(input_min, input_max + 1)) / energy)
    return output


def half_power_width(magnitude: list[float], spacing_m: float = 1.25) -> float:
    peak_index = max(range(len(magnitude)), key=magnitude.__getitem__)
    threshold = magnitude[peak_index] / math.sqrt(2)
    left = peak_index
    while left > 0 and magnitude[left] >= threshold:
        left -= 1
    right = peak_index
    while right < len(magnitude) - 1 and magnitude[right] >= threshold:
        right += 1
    if left == 0 or right == len(magnitude) - 1:
        raise ValueError("missing crossing")
    left_cross = left + (threshold - magnitude[left]) / (magnitude[left + 1] - magnitude[left])
    right_cross = right - 1 + (threshold - magnitude[right - 1]) / (magnitude[right] - magnitude[right - 1])
    return (right_cross - left_cross) * spacing_m


class P76ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.documents = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        cls.source = cls.documents["experiment.m"]

    def make_cli_fixture(self, root: Path, manifest: dict) -> Path:
        fixture = root / "repo"
        (fixture / "bin").mkdir(parents=True)
        (fixture / "curriculum").mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
        (fixture / "curriculum/modules.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        for entry in manifest["modules"]:
            readme = fixture / entry["folder"] / "README.md"
            readme.parent.mkdir(parents=True)
            readme.write_text(f"# {entry['id']}\n", encoding="utf-8")
        return fixture

    def run_cli(self, fixture: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(fixture / "bin/learn"), *arguments], cwd=fixture, text=True, capture_output=True, timeout=3, check=False)

    def test_artifacts_manifest_identity_and_permanent_dependency(self):
        self.assertEqual(artifact_errors(MODULE), [])
        entry = module_entry(self.data, "P76")
        expected = {
            "number": 76,
            "title": "Perform SAR Range Compression",
            "guiding_question": QUESTION,
            "phase": 9,
            "phase_title": "SAR, ISAR, Passive Radar, and Capstone",
            "slug": "perform-sar-range-compression",
            "folder": "modules/76-perform-sar-range-compression",
            "status": "implemented",
            "implementation_batch": "P76",
        }
        for key, value in expected.items():
            self.assertEqual(entry[key], value)
        self.assertEqual(module_entry(self.data, "P75")["status"], "implemented")
        self.assertEqual(module_entry(self.data, "P77")["implementation_batch"], "P77")
        for name, text in self.documents.items():
            with self.subTest(name=name):
                self.assertIn(QUESTION, text)

    def test_malformed_artifact_contract_rejects_missing_empty_and_placeholder(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            self.assertEqual(artifact_errors(fixture), [])
            (fixture / "lesson.md").unlink()
            self.assertIn("missing lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("\n", encoding="utf-8")
            self.assertIn("empty lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("TODO generic\n", encoding="utf-8")
            self.assertIn("TODO remains in lesson.md", artifact_errors(fixture))

    def test_source_exposes_range_compression_sweeps_failure_recovery_and_bounds(self):
        markers = (
            "baseline_seed = 7601;", "sample_rate_hz = 120.0e6;",
            "baseline_bandwidth_hz = 20.0e6;", "aperture_length_m = 80.0;",
            "target_cross_range_m = [-15.0 0.0 18.0];",
            "target_perpendicular_range_m = [1000.0 1025.0 1070.0];",
            "transmit_chirp", "matched_filter = fliplr(conj(transmit_chirp));",
            "aligned_sum = aligned_sum +", "matched_filter_energy",
            "filter_delay_samples = numel(transmit_chirp)-1;",
            "convolution_crosscheck_error", "target_phase_coherence",
            "bandwidth_sweep_hz = [10.0e6 20.0e6 40.0e6];",
            "spacing_sweep_m = [3.75 10.0 15.0];",
            "Intentionally broken case", "magnitude_only_range_history = abs",
            "recovery_exact_match = isequaln", "P76:MagnitudeOnlyFailure",
            "P76:SameDataRecovery", "P76:EchoSupport", "P76:SpatialAliasing",
            "P76:ResourceCeilings", "P76:SweepCount", "P76:WorkingPreflight",
            "P76:SweepOrder", "P76:SpacingGrid", "P76:SpacingSupport",
            "P76:FigureCeiling",
            "max(range_quantization_error_m(:))",
            "pre_results_workspace_inventory = whos;", "p76_results = struct",
        )
        for marker in markers:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P76"), 6)
        self.assertNotIn("rng(", self.source.lower())

    def test_source_has_no_opaque_toolbox_or_external_side_effect(self):
        lowered = self.source.lower()
        for forbidden in (
            "phased.", "rangecompressor", "pulsecompression", "backprojection(",
            "chirp(", "xcorr(", "awgn(", "findpeaks(", "randn(", "parfor",
            "timer(", "pause(", "webread(", "webwrite(", "fopen(", "save(",
            "writematrix(", "system(", "unix(", "dos(", "circshift(",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertIsNone(re.search(r"\b(?:fft|ifft|conv2|filter)\(", lowered))

    def test_control_contract_accepts_baseline_and_rejects_malformed_resources(self):
        self.assertEqual(controls_errors(copy.deepcopy(BASE_CONTROLS)), [])
        cases: list[tuple[str, dict]] = []
        nested = copy.deepcopy(BASE_CONTROLS); nested["target_x_m"] = [[-15.0], [0.0]]; cases.append(("column target", nested))
        lengths = copy.deepcopy(BASE_CONTROLS); lengths["target_voltage"].pop(); cases.append(("length mismatch", lengths))
        nonfinite = copy.deepcopy(BASE_CONTROLS); nonfinite["spacing_sweep_m"][0] = math.nan; cases.append(("nonfinite spacing", nonfinite))
        nyquist = copy.deepcopy(BASE_CONTROLS); nyquist["bandwidth_sweep_hz"][-1] = 60e6; cases.append(("Nyquist", nyquist))
        pulse = copy.deepcopy(BASE_CONTROLS); pulse["pulse_duration_s"] = 2.001e-6; cases.append(("pulse grid", pulse))
        aperture = copy.deepcopy(BASE_CONTROLS); aperture["platform_spacing_m"] = 0.3; cases.append(("aperture grid", aperture))
        gate = copy.deepcopy(BASE_CONTROLS); gate["gate_end_m"] = 1400.1; cases.append(("gate grid", gate))
        alias = copy.deepcopy(BASE_CONTROLS); alias["platform_spacing_m"] = 1.0; cases.append(("spatial alias", alias))
        support = copy.deepcopy(BASE_CONTROLS); support["gate_end_m"] = 1200.0; cases.append(("echo support", support))
        private = copy.deepcopy(BASE_CONTROLS); private["max_private_values"] = 1000; cases.append(("private ceiling", private))
        working = copy.deepcopy(BASE_CONTROLS); working["max_working_values"] = 100000; cases.append(("working ceiling", working))
        targets = copy.deepcopy(BASE_CONTROLS); targets["max_targets"] = 2; cases.append(("target ceiling", targets))
        sweep = copy.deepcopy(BASE_CONTROLS); sweep["max_sweep_cases"] = 2; cases.append(("sweep ceiling", sweep))
        short_spacing = copy.deepcopy(BASE_CONTROLS); short_spacing["spacing_sweep_m"].pop(); cases.append(("short spacing sweep", short_spacing))
        short_bandwidth = copy.deepcopy(BASE_CONTROLS); short_bandwidth["bandwidth_sweep_hz"].pop(); cases.append(("short bandwidth sweep", short_bandwidth))
        unordered = copy.deepcopy(BASE_CONTROLS); unordered["spacing_sweep_m"] = [3.75, 15.0, 10.0]; cases.append(("unordered sweep", unordered))
        off_grid_spacing = copy.deepcopy(BASE_CONTROLS); off_grid_spacing["spacing_sweep_m"][-1] = 15.1; cases.append(("off-grid spacing", off_grid_spacing))
        unsupported_spacing = copy.deepcopy(BASE_CONTROLS); unsupported_spacing["spacing_sweep_m"] = [3.75, 10.0, 300.0]; cases.append(("unsupported spacing", unsupported_spacing))
        figure_bound = copy.deepcopy(BASE_CONTROLS); figure_bound["max_figures"] = 5; cases.append(("figure ceiling", figure_bound))
        for label, controls in cases:
            with self.subTest(label=label):
                self.assertTrue(controls_errors(controls))

    def test_private_generator_is_repeatable_bounded_and_isolated(self):
        first = private_complex_noise(7601, 100)
        self.assertEqual(first, private_complex_noise(7601, 100))
        self.assertNotEqual(first, private_complex_noise(7602, 100))
        self.assertAlmostEqual(first[0].real, 0.7030816305588198)
        self.assertAlmostEqual(first[0].imag, -1.525664765215736)
        with self.assertRaises(ValueError):
            private_complex_noise(0, 1)
        with self.assertRaises(ValueError):
            private_complex_noise(7601, 200001)

    def test_matched_filter_peak_axis_energy_and_bandwidth_oracle(self):
        widths: list[float] = []
        for bandwidth in BASE_CONTROLS["bandwidth_sweep_hz"]:
            waveform = build_lfm(bandwidth)
            self.assertEqual(len(waveform), 240)
            self.assertTrue(all(abs(abs(value) - 1) < 1e-12 for value in waveform))
            response = compressed_profile(waveform, [40], [1 + 0j])
            peak = max(range(len(response)), key=lambda index: abs(response[index]))
            self.assertEqual(peak, 40 + len(waveform) - 1)
            self.assertAlmostEqual(abs(response[peak]), 1.0, places=12)
            corrected_range = 950 + (peak - (len(waveform) - 1)) * 1.25
            self.assertEqual(corrected_range, 1000.0)
            widths.append(half_power_width([abs(value) for value in response]))
        for actual, expected in zip(widths, (13.1539937894, 6.55251475046, 3.22304308451)):
            self.assertAlmostEqual(actual, expected, places=8)
        self.assertTrue(all(right < left for left, right in zip(widths, widths[1:])))
        with self.assertRaises(ValueError):
            build_lfm(float("nan"))
        with self.assertRaises(ValueError):
            compressed_profile([], [1], [1])
        with self.assertRaises(ValueError):
            half_power_width([1.0, 1.0, 1.0])

    def test_spacing_sweep_oracle_progresses_from_merged_to_resolved(self):
        waveform = build_lfm(20e6)
        ratios: list[float] = []
        resolved: list[bool] = []
        base_delay = 40
        half_width = max(1, round(0.25 * 7.5 / 1.25))
        for spacing in BASE_CONTROLS["spacing_sweep_m"]:
            delays = [base_delay, base_delay + round(spacing / 1.25)]
            response = compressed_profile(waveform, delays, [1 + 0j, 1 + 0j])
            magnitude = [abs(value) for value in response]
            peaks = []
            for delay in delays:
                peak_index = delay + len(waveform) - 1
                peaks.append(max(magnitude[peak_index - half_width:peak_index + half_width + 1]))
            left = delays[0] + len(waveform) - 1
            right = delays[1] + len(waveform) - 1
            ratio = min(magnitude[left:right + 1]) / min(peaks)
            ratios.append(ratio)
            resolved.append(ratio < 1 / math.sqrt(2))
        for actual, expected in zip(ratios, (0.922431322208, 0.957646520196, 0.0512840247297)):
            self.assertAlmostEqual(actual, expected, places=9)
        self.assertEqual(resolved, [False, False, True])

    def test_baseline_composite_ridges_track_slant_range_across_aperture(self):
        c = BASE_CONTROLS["c_mps"]
        wavelength = c / BASE_CONTROLS["carrier_hz"]
        range_spacing = c / (2 * BASE_CONTROLS["sample_rate_hz"])
        waveform = build_lfm(BASE_CONTROLS["bandwidth_hz"])
        filter_delay = len(waveform) - 1
        observed_delay_bins: list[list[int]] = []
        maximum_range_error = 0.0

        for position in (-40.0, 0.0, 40.0):
            true_ranges: list[float] = []
            delays: list[int] = []
            amplitudes: list[complex] = []
            for target_x, target_y, voltage, initial_phase in zip(
                BASE_CONTROLS["target_x_m"], BASE_CONTROLS["target_y_m"],
                BASE_CONTROLS["target_voltage"], BASE_CONTROLS["target_phase_rad"],
            ):
                slant_range = math.hypot(position - target_x, target_y)
                delay = round((slant_range - BASE_CONTROLS["gate_start_m"]) / range_spacing)
                phase = initial_phase - 4 * math.pi * (slant_range - target_y) / wavelength
                true_ranges.append(slant_range)
                delays.append(delay)
                amplitudes.append(voltage * cmath.exp(1j * phase))

            response = compressed_profile(waveform, delays, amplitudes)
            row_bins: list[int] = []
            for true_range, delay in zip(true_ranges, delays):
                expected_peak = delay + filter_delay
                search = range(expected_peak - 2, expected_peak + 3)
                observed_peak = max(search, key=lambda index: abs(response[index]))
                observed_delay = observed_peak - filter_delay
                observed_range = BASE_CONTROLS["gate_start_m"] + observed_delay * range_spacing
                row_bins.append(observed_delay)
                maximum_range_error = max(maximum_range_error, abs(observed_range - true_range))
                self.assertEqual(observed_peak, expected_peak)
            observed_delay_bins.append(row_bins)

        self.assertEqual(observed_delay_bins, [[40, 61, 97], [40, 60, 96], [41, 61, 96]])
        self.assertLessEqual(maximum_range_error, range_spacing / 2)

    def test_full_noisy_ridges_preserve_phase_and_magnitude_only_breaks_it(self):
        c = BASE_CONTROLS["c_mps"]
        wavelength = c / BASE_CONTROLS["carrier_hz"]
        spacing = c / (2 * BASE_CONTROLS["sample_rate_hz"])
        waveform = build_lfm(BASE_CONTROLS["bandwidth_hz"])
        positions = [-40.0 + 0.2 * index for index in range(401)]
        fast_count = 361
        unit_noise = private_complex_noise(7601, len(positions) * fast_count)
        ridges: list[list[complex]] = [[] for _ in range(3)]
        phasors: list[list[complex]] = [[] for _ in range(3)]
        for aperture_index, position in enumerate(positions):
            received = [0.2 * unit_noise[aperture_index + range_index * len(positions)] for range_index in range(fast_count)]
            delays: list[int] = []
            phases: list[float] = []
            for target_x, target_y, voltage, initial_phase in zip(BASE_CONTROLS["target_x_m"], BASE_CONTROLS["target_y_m"], BASE_CONTROLS["target_voltage"], BASE_CONTROLS["target_phase_rad"]):
                slant = math.hypot(position - target_x, target_y)
                delay = round((slant - BASE_CONTROLS["gate_start_m"]) / spacing)
                phase = initial_phase - 4 * math.pi * (slant - target_y) / wavelength
                delays.append(delay)
                phases.append(phase)
                amplitude = voltage * cmath.exp(1j * phase)
                for index, value in enumerate(waveform):
                    received[delay + index] += amplitude * value
            for target_index, (delay, phase) in enumerate(zip(delays, phases)):
                ridge = sum(received[delay + index] * waveform[index].conjugate() for index in range(len(waveform))) / len(waveform)
                ridges[target_index].append(ridge)
                phasors[target_index].append(cmath.exp(1j * phase))
        coherences: list[float] = []
        broken: list[float] = []
        immutable_ridges = copy.deepcopy(ridges)
        magnitude_only_ridges = [[abs(value) for value in target_ridge] for target_ridge in ridges]
        recovered_ridges = copy.deepcopy(immutable_ridges)
        for target_ridge, expected in zip(recovered_ridges, phasors):
            coherences.append(abs(sum((value / max(abs(value), 1e-16)) * phasor.conjugate() for value, phasor in zip(target_ridge, expected)) / len(positions)))
            broken.append(abs(sum(phasor.conjugate() for phasor in expected) / len(positions)))
        for actual, expected in zip(coherences, (0.999852232609, 0.999673454983, 0.999508671079)):
            self.assertAlmostEqual(actual, expected, places=9)
        self.assertTrue(all(value > 0.98 for value in coherences))
        self.assertTrue(all(value < 0.2 for value in broken))
        self.assertEqual(recovered_ridges, immutable_ridges)
        self.assertEqual(magnitude_only_ridges, [[abs(value) for value in target_ridge] for target_ridge in immutable_ridges])

    def test_documents_are_concept_first_and_cover_limits(self):
        combined = "\n".join(self.documents.values()).lower()
        for marker in (
            "range-compressed phase history", "fast time", "slant range",
            "aperture phase", "azimuth focusing", "matched filter", "n-1",
            "c/(2b)", "c/(2 fs)", "bandwidth", "target spacing",
            "magnitude-only", "unchanged complex", "recovery", "integer delay",
            "range-cell migration", "spatially alias", "sidelobes",
            "cancellation", "ctrl+c", "rollback", "teach-back",
            "no optional toolbox", "base matlab r2016b or newer", "12,000,000",
            "six tagged figure", "p75", "p77", "p78", "p79", "p80",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(self.documents["checks.md"].count("**Correct:**"), 34)

    def test_cli_timeout_cancellation_rollback_recovery_isolation_and_future_compatibility(self):
        compatible = copy.deepcopy(self.data)
        module_entry(compatible, "P77")["status"] = "implemented"
        module_entry(compatible, "P77")["future_metadata"] = {"allowed": True}
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.make_cli_fixture(Path(directory), compatible)
            started = self.run_cli(fixture, "start", "76")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("status: implemented", started.stdout)
            rolled_back = copy.deepcopy(compatible)
            module_entry(rolled_back, "P76")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8")
            refused = self.run_cli(fixture, "start", "76")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P76", refused.stdout)
            (fixture / "curriculum/modules.json").write_text(json.dumps(compatible, indent=2) + "\n", encoding="utf-8")
            recovered = self.run_cli(fixture, "start", "76")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)
        walkthrough = " ".join(self.documents["walkthrough.md"].lower().split())
        for marker in ("ctrl+c", "no worker", "no background", "rerun from the top", "rollback"):
            self.assertIn(marker, walkthrough)

    def test_default_start_routes_to_p76_frontier_and_rollback_restores_p75(self):
        implemented_before_p76 = [
            entry["id"] for entry in self.data["modules"]
            if entry["status"] == "implemented" and entry["number"] < 76
        ]
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.make_cli_fixture(Path(directory), self.data)
            progress = fixture / ".learning/progress.json"
            progress.parent.mkdir()
            progress.write_text(json.dumps({
                "completed": implemented_before_p76,
                "notes": {},
            }, indent=2) + "\n", encoding="utf-8")

            selected = self.run_cli(fixture, "start")
            self.assertEqual(selected.returncode, 0, selected.stderr)
            self.assertIn("P76 — Perform SAR Range Compression", selected.stdout)
            self.assertIn("status: implemented", selected.stdout)

            rolled_back = copy.deepcopy(self.data)
            module_entry(rolled_back, "P76")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(
                json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8"
            )
            fallback = self.run_cli(fixture, "start")
            self.assertEqual(fallback.returncode, 0, fallback.stderr)
            self.assertIn("P75 — Build SAR Phase-History Intuition", fallback.stdout)
            self.assertIn("status: implemented", fallback.stdout)

    def test_catalogs_evidence_and_exact_eof_policy(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 76 transmits an explicit LFM pulse", root_readme)
        self.assertIn("Project 76 follows P75", start_here)
        self.assertRegex(module_index, r"\| \[P76\].*\| implemented \|")
        evidence = EVIDENCE.read_text(encoding="utf-8")
        for heading in (
            "## Claim boundary", "## Acceptance map",
            "## Deterministic simulated-oracle results",
            "## Figure and metric inventory", "## Exact commands and results",
            "## Changed and preserved invariants", "## Residual risks",
            "## Rollback", "## Unperformed validation",
        ):
            self.assertIn(heading, evidence)
        changed_text_paths = [
            *[MODULE / name for name in ARTIFACTS], ROOT / "curriculum/modules.json",
            ROOT / "README.md", ROOT / "START_HERE.md", ROOT / "modules/README.md",
            ROOT / "tests/test_p76_module.py", EVIDENCE,
        ]
        for path in changed_text_paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
