from __future__ import annotations

import cmath
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/11-make-fft-bins-concrete"
EVIDENCE = ROOT / "docs/evidence/P11-2026-08-01.md"
QUESTION = "What frequency does each FFT bin represent?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def validate_p11_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P11 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P11 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    entries = [
        entry
        for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P11"
    ]
    if len(entries) != 1:
        return errors + [f"expected one P11 manifest entry, found {len(entries)}"]

    expected = {
        "number": 11,
        "id": "P11",
        "title": "Make FFT Bins Concrete",
        "guiding_question": QUESTION,
        "phase": 2,
        "phase_title": "Fourier, Spectral, and I/Q Intuition",
        "slug": "make-fft-bins-concrete",
        "folder": "modules/11-make-fft-bins-concrete",
        "status": "implemented",
        "implementation_batch": "P11",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P11 {key} must be {value!r}")
    return errors


def dft_spectrum(
    fs_hz: float,
    sample_count: int,
    tone_frequency_hz: float,
    amplitude_v: float = 1.0,
    phase_rad: float = 0.35,
) -> list[complex]:
    if not math.isfinite(fs_hz) or fs_hz <= 0:
        raise ValueError("sample rate must be finite and positive")
    if isinstance(sample_count, bool) or not isinstance(sample_count, int):
        raise ValueError("sample count must be an integer")
    if sample_count < 16 or sample_count > 256 or sample_count % 2:
        raise ValueError("sample count must be even and bounded")
    if not math.isfinite(tone_frequency_hz) or not 0 <= tone_frequency_hz < fs_hz / 2:
        raise ValueError("tone must lie from DC through, but not at, Nyquist")
    if not math.isfinite(amplitude_v) or amplitude_v <= 0:
        raise ValueError("amplitude must be finite and positive")
    if not math.isfinite(phase_rad):
        raise ValueError("phase must be finite")

    samples = [
        amplitude_v
        * cmath.exp(1j * (2 * math.pi * tone_frequency_hz * n / fs_hz + phase_rad))
        for n in range(sample_count)
    ]
    return [
        sum(
            sample * cmath.exp(-2j * math.pi * k * n / sample_count)
            for n, sample in enumerate(samples)
        )
        / sample_count
        for k in range(sample_count)
    ]


def wrap_phase(value: float) -> float:
    return (value + math.pi) % (2 * math.pi) - math.pi


class P11ModuleTests(unittest.TestCase):
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
        cls.start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        cls.module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")

    def test_artifact_completeness_and_manifest_identity(self):
        self.assertEqual(validate_p11_contract(MODULE, self.manifest), [])
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
            errors = validate_p11_contract(fixture, self.manifest)
            self.assertIn("P11 missing checks.md", errors)
            self.assertIn("P11 empty lesson.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][10]))
        self.assertIn(
            "expected one P11 manifest entry, found 2",
            validate_p11_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p11_contract(MODULE, {"modules": "P11"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][10]["guiding_question"] = "generic question"
        malformed["modules"][10]["status"] = "scaffolded"
        errors = validate_p11_contract(MODULE, malformed)
        self.assertIn(f"P11 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P11 status must be 'implemented'", errors)

    def test_manifest_catalogs_and_dependency_preserve_p11(self):
        statuses = [module["status"] for module in self.manifest["modules"]]
        self.assertEqual(statuses[:11], ["implemented"] * 11)
        self.assertRegex(self.module_index, r"\| \[P11\].*\| implemented \|")
        self.assertIn("Project 11 begins Phase 2 after P10", self.start_here)
        self.assertIn("Learning dependency: P10", self.readme)

    def test_deterministic_private_seed_and_visible_controls(self):
        for marker in (
            "random_seed = 1011;",
            "fs_hz = 1024;",
            "record_sample_count = 64;",
            "tone_bin = 9;",
            "tone_bin_offset = 0.0;",
            "tone_amplitude_v = 1.0;",
            "tone_phase_rad = 0.35;",
            "noise_rms_v = 0.002;",
            "fractional_bin_sweep = [0 0.25 0.50];",
            "record_length_sweep = [32 64 128];",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "randn(stream, 1, record_sample_count)",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_explicit_dft_and_fft_are_equivalent_for_coherent_tone(self):
        spectrum = dft_spectrum(1024.0, 64, 144.0)
        magnitudes = [abs(value) for value in spectrum]
        self.assertEqual(max(range(64), key=magnitudes.__getitem__), 9)
        self.assertAlmostEqual(magnitudes[9], 1.0, places=12)
        self.assertAlmostEqual(wrap_phase(cmath.phase(spectrum[9]) - 0.35), 0.0, places=12)
        self.assertLess(max(magnitudes[:9] + magnitudes[10:]), 1e-12)
        for operation in (
            "basis = exp(-1j*2*pi*k*sample_index/record_sample_count);",
            "dft_projection_v(bin_index) = sum(observed_v.*basis);",
            "fft_projection_v = fft(observed_v);",
            "dft_projection_v - fft_projection_v",
        ):
            self.assertIn(operation, self.experiment)

    def test_half_bin_tone_projects_to_both_neighbors_with_meaningful_phase(self):
        spectrum = dft_spectrum(1024.0, 64, 152.0)
        lower = spectrum[9]
        upper = spectrum[10]
        expected_magnitude = 1 / (64 * math.sin(math.pi / 128))
        self.assertAlmostEqual(abs(lower), expected_magnitude, places=12)
        self.assertAlmostEqual(abs(upper), expected_magnitude, places=12)
        self.assertAlmostEqual(abs(wrap_phase(cmath.phase(lower) - cmath.phase(upper))),
                               math.pi * 63 / 64, places=12)
        self.assertIn("half_case_index", self.experiment)
        self.assertIn("offset_lower_phase_rad", self.experiment)
        self.assertIn("offset_upper_phase_rad", self.experiment)

    def test_fractional_offset_sweep_changes_only_tone_frequency(self):
        section = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        self.assertIn("sweep_offset = fractional_bin_sweep(sweep_index);", section)
        self.assertIn("sweep_frequency_hz = (tone_bin + sweep_offset)*bin_spacing_hz;", section)
        self.assertIn("sweep_tone_v + complex_noise_v", section)
        for forbidden_assignment in (
            "fs_hz =",
            "record_sample_count =",
            "tone_amplitude_v =",
            "tone_phase_rad =",
            "complex_noise_v =",
        ):
            self.assertNotIn(forbidden_assignment, section)

    def test_record_length_sweep_has_expected_grid_and_peak_behavior(self):
        expected_bins = [4.5, 9.0, 18.0]
        spacings = []
        peaks = []
        for sample_count in (32, 64, 128):
            spacing = 1024.0 / sample_count
            spectrum = dft_spectrum(1024.0, sample_count, 144.0)
            spacings.append(spacing)
            peaks.append(max(range(sample_count), key=lambda k: abs(spectrum[k])))
        self.assertEqual(spacings, [32.0, 16.0, 8.0])
        self.assertEqual([144.0 / value for value in spacings], expected_bins)
        self.assertIn(peaks[0], (4, 5))
        self.assertEqual(peaks[1:], [9, 18])
        section = self.experiment.split("%% Sweep 2", 1)[1].split("%% Broken case", 1)[0]
        self.assertIn("fixed_tone_frequency_hz = tone_bin*bin_spacing_hz;", section)
        self.assertIn("sweep_sample_count = record_length_sweep(sweep_index);", section)
        self.assertNotIn("fs_hz =", section)

    def test_broken_one_based_axis_and_recovery_are_exactly_one_bin_apart(self):
        spacing_hz = 1024.0 / 64
        matlab_index = 10
        broken_hz = matlab_index * spacing_hz
        recovered_hz = (matlab_index - 1) * spacing_hz
        self.assertEqual(broken_hz, 160.0)
        self.assertEqual(recovered_hz, 144.0)
        self.assertIn("broken_frequency_axis_hz = (1:record_sample_count)*bin_spacing_hz;", self.experiment)
        self.assertIn("recovered_frequency_axis_hz = (0:(record_sample_count - 1))*bin_spacing_hz;", self.experiment)
        combined = "\n".join((self.lesson, self.walkthrough, self.checks))
        self.assertIn("metadata error", combined)
        self.assertIn("exactly one 16 Hz bin", combined)

    def test_editable_offsets_and_edge_bins_preserve_peak_label_recovery(self):
        spacing_hz = 1024.0 / 64
        expected_nearest = {
            0.0: {9},
            0.25: {9},
            0.5: {9, 10},
        }
        for offset, expected_bins in expected_nearest.items():
            spectrum = dft_spectrum(1024.0, 64, (9 + offset) * spacing_hz)
            magnitudes = [abs(value) for value in spectrum]
            peak_magnitude = max(magnitudes)
            nearest_bins = {
                index
                for index, magnitude in enumerate(magnitudes)
                if math.isclose(magnitude, peak_magnitude, rel_tol=0.0, abs_tol=1e-12)
            }
            self.assertEqual(nearest_bins, expected_bins)
            for peak_bin in nearest_bins:
                recovered_hz = peak_bin * spacing_hz
                broken_hz = (peak_bin + 1) * spacing_hz
                self.assertAlmostEqual(broken_hz - recovered_hz, spacing_hz)

        for marker in (
            "baseline_peak_is_nearest = baseline_peak_bin == tone_bin ||",
            "baseline_peak_bin == tone_bin + 1",
            "expected_peak_bin_frequency_hz = baseline_peak_bin*bin_spacing_hz;",
            "broken_reported_frequency_hz - recovered_reported_frequency_hz",
            "0.60*tone_amplitude_v",
            "nearby_bins = max(0, tone_bin - 3):min(record_sample_count - 1, tone_bin + 4);",
            "Bin %d = %.1f Hz; tone = %.1f Hz",
        ):
            self.assertIn(marker, self.experiment)

    def test_signed_frequency_mapping_and_special_bins_are_explained(self):
        self.assertIn("signed_frequency_hz(bin_numbers > record_sample_count/2)", self.experiment)
        self.assertIn("signed_frequency_hz(bin_numbers > record_sample_count/2) - fs_hz", self.experiment)
        self.assertIn("DC and Nyquist are special", self.lesson)
        self.assertIn("(k-N)f_s/N", self.checks)

    def test_malformed_numeric_inputs_and_resource_bounds(self):
        for sample_count in (15, 17, 258, True, 64.0):
            with self.assertRaises(ValueError):
                dft_spectrum(1024.0, sample_count, 144.0)
        for fs_hz in (0.0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                dft_spectrum(fs_hz, 64, 144.0)
        for tone_hz in (-1.0, 512.0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                dft_spectrum(1024.0, 64, tone_hz)
        with self.assertRaises(ValueError):
            dft_spectrum(1024.0, 64, 144.0, amplitude_v=0.0)
        with self.assertRaises(ValueError):
            dft_spectrum(1024.0, 64, 144.0, phase_rad=float("nan"))
        for marker in (
            "max_record_samples = 256;",
            "max_sweep_cases = 8;",
            "max_figure_groups = 4;",
            "max_explicit_dft_terms = 65536;",
            "P11 resource ceilings must remain fixed.",
            "record_sample_count <= max_record_samples",
            "record_sample_count^2 <= max_explicit_dft_terms",
            "random_seed <= 2^32 - 1",
            "noise_rms_v <= 0.05*tone_amplitude_v",
            "all(diff(fractional_bin_sweep) > 0)",
            "all(diff(record_length_sweep) > 0)",
            "numel(record_length_sweep) >= 3",
            "record sweep must exercise both half-bin and exact-bin tone placement",
        ):
            self.assertIn(marker, self.experiment)

    def test_validation_precedes_allocation_and_figure_replacement(self):
        resource_guard = self.experiment.index("P11 resource ceilings must remain fixed.")
        stream_allocation = self.experiment.index("stream = RandStream")
        explicit_allocation = self.experiment.index("dft_projection_v = complex(zeros")
        figure_replacement = self.experiment.index("old_figures = findall")
        self.assertLess(resource_guard, stream_allocation)
        self.assertLess(stream_allocation, explicit_allocation)
        self.assertLess(explicit_allocation, figure_replacement)

    def test_plots_metrics_and_units_cover_required_behavior(self):
        for figure_name in (
            "P11 baseline bin map",
            "P11 fractional-bin sweep",
            "P11 record-length sweep",
            "P11 broken axis and recovery",
        ):
            self.assertIn(figure_name, self.experiment)
        for unit_label in (
            "Time (ms)",
            "I/Q amplitude (V)",
            "Signed frequency (Hz)",
            "Projection phase (rad)",
            "Neighbor magnitude (V)",
            "Record length N (samples)",
        ):
            self.assertIn(unit_label, self.experiment)
        for metric in (
            "results.bin_spacing_hz",
            "results.baseline_peak_bin",
            "results.baseline_peak_matlab_index",
            "results.offset_lower_magnitude_v",
            "results.offset_upper_phase_rad",
            "results.record_peak_error_hz",
            "results.broken_frequency_error_hz",
            "results.recovered_frequency_error_hz",
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
        self.assertIn("'Tag', 'P11'", self.experiment)
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
            "dftmtx(",
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
            "## The bin-frequency map",
            "## Exact-bin and between-bin tones",
            "## Limiting cases",
            "## Radar connection and common interpretation mistakes",
        ):
            self.assertIn(heading, self.lesson)
        for heading in (
            "## Baseline: read the bin before reading the peak",
            "## Sweep 1: change only fractional-bin offset",
            "## Sweep 2: change only record length",
            "## Broken case",
            "## Recovery and rollback",
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
        self.assertIn("P11 is **ready for deterministic review**", evidence)


if __name__ == "__main__":
    unittest.main()
