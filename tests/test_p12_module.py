from __future__ import annotations

import cmath
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/12-separate-leakage-from-noise"
EVIDENCE = ROOT / "docs/evidence/P12-2026-08-01.md"
QUESTION = "Why does a perfectly clean tone spread across many FFT bins?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
WINDOW_NAMES = ("Rectangular", "Hann", "Hamming", "Blackman", "Flat-top")


def validate_p12_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P12 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P12 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    entries = [
        entry
        for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P12"
    ]
    if len(entries) != 1:
        return errors + [f"expected one P12 manifest entry, found {len(entries)}"]

    expected = {
        "number": 12,
        "id": "P12",
        "title": "Separate Leakage from Noise",
        "guiding_question": QUESTION,
        "phase": 2,
        "phase_title": "Fourier, Spectral, and I/Q Intuition",
        "slug": "separate-leakage-from-noise",
        "folder": "modules/12-separate-leakage-from-noise",
        "status": "implemented",
        "implementation_batch": "P12",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P12 {key} must be {value!r}")
    return errors


def periodic_window(name: str, sample_count: int) -> list[float]:
    if isinstance(sample_count, bool) or not isinstance(sample_count, int):
        raise ValueError("sample count must be an integer")
    if sample_count < 32 or sample_count > 512 or sample_count % 2:
        raise ValueError("sample count must be even and bounded")
    if name not in WINDOW_NAMES:
        raise ValueError("unsupported window")

    values = []
    for n in range(sample_count):
        angle = 2 * math.pi * n / sample_count
        if name == "Rectangular":
            value = 1.0
        elif name == "Hann":
            value = 0.5 - 0.5 * math.cos(angle)
        elif name == "Hamming":
            value = 0.54 - 0.46 * math.cos(angle)
        elif name == "Blackman":
            value = 0.42 - 0.50 * math.cos(angle) + 0.08 * math.cos(2 * angle)
        else:
            value = (
                0.21557895
                - 0.41663158 * math.cos(angle)
                + 0.277263158 * math.cos(2 * angle)
                - 0.083578947 * math.cos(3 * angle)
                + 0.006947368 * math.cos(4 * angle)
            )
        values.append(value)
    return values


def normalized_dft(
    sample_count: int,
    fractional_bin_offset: float,
    window_name: str = "Rectangular",
) -> list[complex]:
    if not isinstance(fractional_bin_offset, (int, float)) or isinstance(
        fractional_bin_offset, bool
    ):
        raise ValueError("offset must be numeric")
    if not math.isfinite(fractional_bin_offset) or not 0 <= fractional_bin_offset <= 0.5:
        raise ValueError("offset must lie from zero through one-half bin")
    window = periodic_window(window_name, sample_count)
    coherent_sum = sum(window)
    tone_bin = 17
    samples = [
        cmath.exp(1j * (2 * math.pi * (tone_bin + fractional_bin_offset) * n / sample_count + 0.25))
        for n in range(sample_count)
    ]
    return [
        sum(
            sample * weight * cmath.exp(-2j * math.pi * k * n / sample_count)
            for n, (sample, weight) in enumerate(zip(samples, window))
        )
        / coherent_sum
        for k in range(sample_count)
    ]


def off_peak_energy_fraction(sample_count: int, offset: float) -> float:
    spectrum = normalized_dft(sample_count, offset)
    energy = [abs(value) ** 2 for value in spectrum]
    return 1.0 - max(energy) / sum(energy)


def window_response_metrics(name: str, sample_count: int = 128) -> tuple[float, float, float]:
    """Return N-bin peak error dB, dense -3 dB width bins, max sidelobe dBc."""
    window = periodic_window(name, sample_count)
    coherent_sum = sum(window)
    bin_peak = max(abs(value) for value in normalized_dft(sample_count, 0.35, name))
    peak_error_db = 20 * math.log10(bin_peak)

    points_per_bin = 64
    relative_bins = [index / points_per_bin for index in range(-8 * points_per_bin, 8 * points_per_bin + 1)]
    response = [
        abs(
            sum(
                weight * cmath.exp(-2j * math.pi * delta * n / sample_count)
                for n, weight in enumerate(window)
            )
        )
        / coherent_sum
        for delta in relative_bins
    ]
    peak_index = relative_bins.index(0.0)
    threshold = 1 / math.sqrt(2)
    left = max(index for index in range(peak_index) if response[index] < threshold) + 1
    right = peak_index + min(
        index for index, value in enumerate(response[peak_index:]) if value < threshold
    ) - 1
    width_bins = relative_bins[right] - relative_bins[left]
    half_null_width = dict(
        zip(WINDOW_NAMES, (1.0, 2.0, 2.0, 3.0, 5.0))
    )[name]
    sidelobe = max(
        value
        for value, offset in zip(response, relative_bins)
        if abs(offset) >= half_null_width
    )
    sidelobe_db_c = 20 * math.log10(sidelobe)
    return peak_error_db, width_bins, sidelobe_db_c


def circular_dense_window_metrics(
    name: str,
    tone_bin: int,
    fractional_bin_offset: float = 0.35,
    sample_count: int = 128,
    points_per_bin: int = 16,
) -> tuple[float, float]:
    """Return circular -3 dB width bins and max sidelobe dBc."""
    window = periodic_window(name, sample_count)
    coherent_sum = sum(window)
    tone_position_bins = tone_bin + fractional_bin_offset
    grid_count = sample_count * points_per_bin
    grid_bins = [index / points_per_bin for index in range(grid_count)]
    response = [
        abs(
            sum(
                weight
                * cmath.exp(
                    2j
                    * math.pi
                    * (tone_position_bins - grid_bin)
                    * n
                    / sample_count
                )
                for n, weight in enumerate(window)
            )
        )
        / coherent_sum
        for grid_bin in grid_bins
    ]
    peak_index = max(range(grid_count), key=response.__getitem__)
    peak = response[peak_index]
    half_power = peak / math.sqrt(2)
    circular_response = response * 3
    circular_peak_index = peak_index + grid_count
    left_below = max(
        index
        for index in range(circular_peak_index)
        if circular_response[index] < half_power
    )
    right_below = circular_peak_index + next(
        index
        for index, value in enumerate(circular_response[circular_peak_index:])
        if value < half_power
    )
    width_bins = (right_below - left_below - 2) / points_per_bin

    half_null_width = dict(zip(WINDOW_NAMES, (1.0, 2.0, 2.0, 3.0, 5.0)))[name]
    sidelobe = max(
        value
        for value, grid_bin in zip(response, grid_bins)
        if abs(
            (grid_bin - tone_position_bins + sample_count / 2) % sample_count
            - sample_count / 2
        )
        >= half_null_width
    )
    return width_bins, 20 * math.log10(sidelobe / peak)


class P12ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.experiment = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        cls.root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        cls.module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")

    def test_artifact_completeness_and_manifest_identity(self):
        self.assertEqual(validate_p12_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            self.assertGreater((MODULE / name).stat().st_size, 100)
        for text in (self.readme, self.experiment, self.lesson, self.walkthrough, self.checks):
            self.assertIn(QUESTION, text)

    def test_contract_validator_rejects_missing_empty_duplicate_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "checks.md").unlink()
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p12_contract(fixture, self.manifest)
            self.assertIn("P12 missing checks.md", errors)
            self.assertIn("P12 empty lesson.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][11]))
        self.assertIn(
            "expected one P12 manifest entry, found 2",
            validate_p12_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p12_contract(MODULE, {"modules": "P12"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][11]["guiding_question"] = "generic question"
        malformed["modules"][11]["status"] = "scaffolded"
        errors = validate_p12_contract(MODULE, malformed)
        self.assertIn(f"P12 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P12 status must be 'implemented'", errors)

    def test_manifest_catalogs_and_p11_dependency_preserve_p12(self):
        statuses = [module["status"] for module in self.manifest["modules"]]
        self.assertEqual(statuses[:12], ["implemented"] * 12)
        self.assertRegex(self.module_index, r"\| \[P12\].*\| implemented \|")
        self.assertIn("Project 12 separates deterministic finite-record leakage", self.root_readme)
        self.assertIn("Project 12 follows P11", self.start_here)
        self.assertIn("Learning dependency: P11", self.readme)

    def test_deterministic_private_seed_and_visible_controls(self):
        for marker in (
            "random_seed = 1012;",
            "fs_hz = 1024;",
            "record_sample_count = 128;",
            "tone_bin = 17;",
            "tone_bin_offset = 0.35;",
            "tone_amplitude_v = 1.0;",
            "tone_phase_rad = 0.25;",
            "noise_rms_v = 0.02;",
            "offset_sweep_bins = [0 0.20 0.35 0.50];",
            "display_fft_count = 8192;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "randn(stream, 1, record_sample_count)",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_explicit_window_equations_and_coherent_gain(self):
        for operation in (
            "window = ones(1, record_sample_count);",
            "window = 0.5 - 0.5*cos(2*pi*n/record_sample_count);",
            "window = 0.54 - 0.46*cos(2*pi*n/record_sample_count);",
            "0.42 - 0.50*cos(2*pi*n/record_sample_count)",
            "0.21557895 - 0.41663158*cos(2*pi*n/record_sample_count)",
            "coherent_gain(window_index) = sum(window)/record_sample_count;",
            "clean_tone_v.*window",
        ):
            self.assertIn(operation, self.experiment)
        gains = {
            name: sum(periodic_window(name, 128)) / 128 for name in WINDOW_NAMES
        }
        self.assertAlmostEqual(gains["Rectangular"], 1.0, places=12)
        self.assertAlmostEqual(gains["Hann"], 0.5, places=12)
        self.assertAlmostEqual(gains["Hamming"], 0.54, places=12)
        self.assertAlmostEqual(gains["Blackman"], 0.42, places=12)
        self.assertAlmostEqual(gains["Flat-top"], 0.21557895, places=12)

    def test_independent_window_tradeoffs_match_physical_contract(self):
        metrics = {name: window_response_metrics(name) for name in WINDOW_NAMES}
        rectangular = metrics["Rectangular"]
        hann = metrics["Hann"]
        blackman = metrics["Blackman"]
        flat_top = metrics["Flat-top"]
        self.assertGreater(rectangular[2], -14.0)
        self.assertLess(rectangular[2], -13.0)
        self.assertGreater(hann[1], rectangular[1])
        self.assertLess(hann[2], rectangular[2] - 15)
        self.assertLess(blackman[2], hann[2] - 20)
        self.assertGreater(flat_top[1], blackman[1])
        self.assertLess(abs(flat_top[0]), abs(rectangular[0]))
        self.assertLess(abs(flat_top[0]), 0.02)

    def test_window_metrics_remain_correct_when_valid_tone_nears_nyquist(self):
        for name in WINDOW_NAMES:
            interior = circular_dense_window_metrics(name, tone_bin=17)
            near_nyquist = circular_dense_window_metrics(name, tone_bin=62)
            self.assertAlmostEqual(near_nyquist[0], interior[0], places=9)
            self.assertAlmostEqual(near_nyquist[1], interior[1], places=9)

        edge_metrics = {
            name: circular_dense_window_metrics(name, tone_bin=62)
            for name in WINDOW_NAMES
        }
        self.assertLess(edge_metrics["Hann"][1], edge_metrics["Rectangular"][1] - 15)
        self.assertLess(edge_metrics["Blackman"][1], edge_metrics["Hann"][1] - 20)
        self.assertGreater(edge_metrics["Flat-top"][0], edge_metrics["Blackman"][0])
        self.assertIn("circular_magnitude_v", self.experiment)
        self.assertIn("wrapped_frequency_offset_hz", self.experiment)

    def test_fractional_offset_sweep_reaches_coherent_and_half_bin_limits(self):
        fractions = [off_peak_energy_fraction(128, offset) for offset in (0, 0.2, 0.35, 0.5)]
        self.assertLess(abs(fractions[0]), 1e-14)
        self.assertGreater(fractions[1], fractions[0])
        self.assertGreater(fractions[2], fractions[1])
        self.assertGreater(fractions[3], 0.5)
        section = self.experiment.split("%% Sweep 2", 1)[1].split("%% Broken case", 1)[0]
        self.assertIn("sweep_offset_bins = offset_sweep_bins(sweep_index);", section)
        self.assertIn("sweep_frequency_hz = (tone_bin + sweep_offset_bins)*bin_spacing_hz;", section)
        for forbidden_assignment in (
            "fs_hz =",
            "record_sample_count =",
            "tone_amplitude_v =",
            "tone_phase_rad =",
            "rectangular_window =",
        ):
            self.assertNotIn(forbidden_assignment, section)

    def test_window_sweep_changes_only_window_and_has_all_five_cases(self):
        section = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        self.assertIn("for window_index = 1:window_case_count", section)
        self.assertIn("clean_tone_v.*window", section)
        self.assertIn("first_null_half_width_bins = [1 2 2 3 5];", section)
        for forbidden_assignment in (
            "fs_hz =",
            "record_sample_count =",
            "tone_frequency_hz =",
            "tone_amplitude_v =",
            "noise_rms_v =",
        ):
            self.assertNotIn(forbidden_assignment, section)

    def test_broken_noise_estimate_confuses_deterministic_leakage(self):
        clean_spectrum = normalized_dft(128, 0.35)
        energy = [abs(value) ** 2 for value in clean_spectrum]
        broken_noise_rms = math.sqrt(sum(energy) - max(energy))
        self.assertGreater(broken_noise_rms, 0.2)
        self.assertGreater(broken_noise_rms, 10 * 0.02)
        for marker in (
            'call every nonpeak clean-tone bin "noise"',
            "true_clean_noise_rms_v = 0;",
            "recovered_noise_time_v = noisy_tone_v - clean_tone_v;",
            "noisy_tone_v)/record_sample_count -",
            "recovered_noise_rms_v - noise_rms_realized_v",
        ):
            self.assertIn(marker, self.experiment)
        combined = "\n".join((self.lesson, self.walkthrough, self.checks))
        self.assertIn("classification", combined)
        self.assertIn("Deterministic leakage", combined)

    def test_malformed_numeric_inputs_and_resource_bounds(self):
        for sample_count in (31, 33, 514, True, 128.0):
            with self.assertRaises(ValueError):
                periodic_window("Hann", sample_count)
        with self.assertRaises(ValueError):
            periodic_window("Kaiser", 128)
        for offset in (-0.1, 0.6, float("nan"), float("inf"), True, "0.2"):
            with self.assertRaises(ValueError):
                normalized_dft(128, offset)  # type: ignore[arg-type]
        for marker in (
            "max_record_samples = 512;",
            "max_display_fft_count = 16384;",
            "max_window_cases = 5;",
            "max_sweep_cases = 8;",
            "max_figure_groups = 4;",
            "P12 resource ceilings must remain fixed.",
            "random_seed <= 2^32 - 1",
            "noise_rms_v <= 0.20*tone_amplitude_v",
            "all(diff(offset_sweep_bins) > 0)",
            "mod(display_fft_count, record_sample_count) == 0",
            "The offset sweep must keep the tone below Nyquist.",
        ):
            self.assertIn(marker, self.experiment)

    def test_validation_precedes_allocation_and_figure_replacement(self):
        resource_guard = self.experiment.index("P12 resource ceilings must remain fixed.")
        signal_allocation = self.experiment.index("sample_index = 0:")
        stream_allocation = self.experiment.index("stream = RandStream")
        sweep_allocation = self.experiment.index("window_samples = zeros")
        figure_replacement = self.experiment.index("old_figures = findall")
        self.assertLess(resource_guard, signal_allocation)
        self.assertLess(signal_allocation, stream_allocation)
        self.assertLess(stream_allocation, sweep_allocation)
        self.assertLess(sweep_allocation, figure_replacement)

    def test_plots_metrics_and_units_cover_required_behavior(self):
        for figure_name in (
            "P12 clean leakage versus noise",
            "P12 window sweep",
            "P12 window metrics",
            "P12 offset sweep and broken noise estimate",
        ):
            self.assertIn(figure_name, self.experiment)
        for unit_label in (
            "Time in repeated record (ms)",
            "In-phase amplitude (V)",
            "Frequency (Hz)",
            "Magnitude relative to each peak (dBc)",
            "-3 dB width (Hz)",
            "Peak error (dB)",
            "RMS amplitude (V)",
        ):
            self.assertIn(unit_label, self.experiment)
        for metric in (
            "results.record_wrap_jump_v",
            "results.noise_rms_realized_v",
            "results.coherent_gain",
            "results.peak_amplitude_error_db",
            "results.main_lobe_3db_width_hz",
            "results.maximum_sidelobe_db_c",
            "results.offset_off_peak_energy_fraction",
            "results.broken_noise_rms_v",
            "results.recovered_noise_rms_v",
        ):
            self.assertIn(metric, self.experiment)

    def test_timeout_cancellation_recovery_isolation_and_compatibility(self):
        lowered = self.experiment.lower()
        for forbidden in (
            "close all",
            "clear all",
            "clearvars",
            "pause(",
            "input(",
            "timer(",
            "parfor",
            "backgroundpool",
            "audioplayer",
            "sound(",
            "webread(",
            "webwrite(",
            "fopen(",
            "writematrix(",
            "save(",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertNotRegex(self.experiment, r"(?mi)^\s*while\b")
        self.assertNotRegex(self.experiment, r"(?mi)^\s*function\b")
        self.assertNotRegex(self.experiment, r"(?i)\b[xy]line\s*\(")
        self.assertIn("'Tag', 'P12'", self.experiment)
        self.assertIn("Ctrl+C", self.walkthrough)
        self.assertIn("private seed", self.walkthrough)
        self.assertIn("writes no files", self.readme)
        self.assertIn("global random stream", self.readme)
        self.assertIn("manifest status to `scaffolded`", self.readme)

    def test_no_placeholder_or_unexplained_black_box_regression(self):
        combined = "\n".join(
            (self.readme, self.experiment, self.lesson, self.walkthrough, self.checks)
        )
        self.assertNotRegex(combined, r"(?i)\b(TODO|TBD|lorem ipsum)\b")
        source_without_comments = "\n".join(
            line.split("%", 1)[0] for line in self.experiment.splitlines()
        ).lower()
        for hidden_call in (
            "hann(",
            "hamming(",
            "blackman(",
            "flattopwin(",
            "periodogram(",
            "pwelch(",
            "spectrogram(",
            "pspectrum(",
            "freqz(",
        ):
            self.assertNotIn(hidden_call, source_without_comments)
        for unsupported_claim in (
            "matlab runtime passed",
            "validated on hardware",
            "field validated",
            "production validated",
        ):
            self.assertNotIn(unsupported_claim, combined.lower())

    def test_concept_first_documents_and_teach_back_are_complete(self):
        for heading in (
            "## Physical mental model",
            "## Finite observation creates the spectral shape",
            "## Three metrics answer three different questions",
            "## Leakage and noise behave differently",
            "## Limiting cases",
            "## Radar connection and common interpretation mistakes",
        ):
            self.assertIn(heading, self.lesson)
        for heading in (
            "## Baseline: prove leakage exists without noise",
            "## Sweep 1: change only the window",
            "## Sweep 2: change only fractional-bin offset",
            "## Broken case: treat nonpeak energy as noise",
            "## Recovery and concept connection",
            "## Safe rerun, cancellation, and rollback",
        ):
            self.assertIn(heading, self.walkthrough)
        for heading in (
            "## Baseline observation checks",
            "## Predict, then verify",
            "## Interpretation checks",
            "## Failure classification",
            "## Teach-back completion",
        ):
            self.assertIn(heading, self.checks)

    def test_retained_evidence_exists_and_preserves_runtime_claim_boundary(self):
        evidence = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("does **not** claim MATLAB or Octave execution", evidence)
        self.assertIn("Static validation and MATLAB runtime evidence are separate", evidence)
        self.assertIn("Generic product-data", evidence)


if __name__ == "__main__":
    unittest.main()
