from __future__ import annotations

import cmath
import copy
import json
import math
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/10-decimate-and-interpolate-without-creating-artifacts"
EVIDENCE = ROOT / "docs/evidence/P10-2026-08-01.md"
QUESTION = "Why must filtering accompany sample-rate changes?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def validate_p10_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P10 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P10 empty {name}")
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    entries = [entry for entry in modules if isinstance(entry, dict) and entry.get("id") == "P10"]
    if len(entries) != 1:
        return errors + [f"expected one P10 manifest entry, found {len(entries)}"]
    expected = {
        "number": 10,
        "id": "P10",
        "title": "Decimate and Interpolate Without Creating Artifacts",
        "guiding_question": QUESTION,
        "phase": 1,
        "phase_title": "Signals, Sampling, and Systems",
        "slug": "decimate-and-interpolate-without-creating-artifacts",
        "folder": "modules/10-decimate-and-interpolate-without-creating-artifacts",
        "status": "implemented",
        "implementation_batch": "P10",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P10 {key} must be {value!r}")
    return errors


def design_fir(tap_count: int = 65, fs_hz: float = 2400.0, cutoff_hz: float = 240.0) -> list[float]:
    if isinstance(tap_count, bool) or not isinstance(tap_count, int):
        raise ValueError("tap count must be an integer")
    if tap_count < 9 or tap_count > 129 or tap_count % 2 == 0:
        raise ValueError("tap count must be odd and bounded")
    if not math.isfinite(fs_hz) or fs_hz <= 0:
        raise ValueError("sample rate must be finite and positive")
    if not math.isfinite(cutoff_hz) or not 0 < cutoff_hz < fs_hz / 2:
        raise ValueError("cutoff must lie between DC and Nyquist")
    delay = (tap_count - 1) // 2
    coefficients: list[float] = []
    for tap, centered_index in enumerate(range(-delay, delay + 1)):
        if centered_index == 0:
            ideal = 2 * cutoff_hz / fs_hz
        else:
            ideal = math.sin(2 * math.pi * cutoff_hz * centered_index / fs_hz) / (
                math.pi * centered_index
            )
        window = 0.54 - 0.46 * math.cos(2 * math.pi * tap / (tap_count - 1))
        coefficients.append(ideal * window)
    dc_gain = sum(coefficients)
    return [coefficient / dc_gain for coefficient in coefficients]


def fir_aligned(signal: list[float], coefficients: list[float], gain: float = 1.0) -> list[float]:
    output = [0.0] * (len(signal) + len(coefficients) - 1)
    for tap, coefficient in enumerate(coefficients):
        for index, sample in enumerate(signal):
            output[index + tap] += gain * coefficient * sample
    delay = (len(coefficients) - 1) // 2
    return output[delay : delay + len(signal)]


def tone_amplitude(signal: list[float], frequency_hz: float, fs_hz: float) -> float:
    projection = sum(
        sample * cmath.exp(-2j * math.pi * frequency_hz * index / fs_hz)
        for index, sample in enumerate(signal)
    )
    return 2 * abs(projection) / len(signal)


def fold_frequency(frequency_hz: float, fs_hz: float) -> float:
    if not math.isfinite(frequency_hz) or not math.isfinite(fs_hz) or fs_hz <= 0:
        raise ValueError("finite frequency and positive sample rate required")
    return abs(frequency_hz - round(frequency_hz / fs_hz) * fs_hz)


class P10ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.experiment = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        cls.start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        cls.module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")

    def test_artifact_completeness_and_manifest_identity(self):
        self.assertEqual(validate_p10_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            self.assertGreater((MODULE / name).stat().st_size, 100)
        for text in (self.readme, self.experiment, self.lesson, self.walkthrough, self.checks):
            self.assertIn(QUESTION, text)

    def test_retained_evidence_exists_and_preserves_runtime_claim_boundary(self):
        evidence = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("does **not** claim MATLAB or Octave execution", evidence)
        self.assertIn("P10 is **ready for deterministic review**", evidence)

    def test_contract_validator_rejects_missing_empty_duplicate_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "checks.md").unlink()
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p10_contract(fixture, self.manifest)
            self.assertIn("P10 missing checks.md", errors)
            self.assertIn("P10 empty lesson.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][9]))
        self.assertIn("expected one P10 manifest entry, found 2", validate_p10_contract(MODULE, duplicate))
        self.assertIn(
            "manifest modules must be a list",
            validate_p10_contract(MODULE, {"modules": "P10"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][9]["guiding_question"] = "generic question"
        malformed["modules"][9]["status"] = "scaffolded"
        errors = validate_p10_contract(MODULE, malformed)
        self.assertIn(f"P10 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P10 status must be 'implemented'", errors)

    def test_manifest_and_public_catalogs_preserve_p10(self):
        statuses = [module["status"] for module in self.manifest["modules"]]
        self.assertEqual(statuses[:10], ["implemented"] * 10)
        self.assertRegex(self.module_index, r"\| \[P10\].*\| implemented \|")
        self.assertIn("Project 10 completes the first-phase sequence", self.start_here)

    def test_declared_dependency_and_base_matlab_path_are_explicit(self):
        self.assertIn("Learning dependency: P09", self.readme)
        self.assertIn("Base MATLAB only", self.experiment)
        self.assertIn("P09 filter behavior", self.experiment)
        for operation in (
            "ideal_lowpass(tap_index)",
            "anti_alias_fir = anti_alias_fir/sum(anti_alias_fir)",
            "filtered_full_v(output_indices)",
            "x_v(1:decimation_factor:end)",
            "zero_inserted_v(1:decimation_factor:end)",
            "reconstruction_fir = decimation_factor*anti_alias_fir",
        ):
            self.assertIn(operation, self.experiment)

    def test_deterministic_input_contract_and_visible_controls(self):
        for marker in (
            "random_seed = 1010;",
            "fs_hz = 2400;",
            "decimation_factor = 4;",
            "low_tone_hz = 90;",
            "high_tone_hz = 420;",
            "noise_rms_v = 0.01;",
            "anti_alias_cutoff_hz = 240;",
            "filter_tap_count = 65;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "randn(stream, 1, record_sample_count)",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_decimation_alias_and_prefilter_recovery_independently(self):
        fs_hz = 2400.0
        factor = 4
        sample_count = 2400
        signal = [
            math.cos(2 * math.pi * 90 * index / fs_hz + 0.20)
            + 0.65 * math.cos(2 * math.pi * 420 * index / fs_hz - 0.35)
            for index in range(sample_count)
        ]
        filtered = fir_aligned(signal, design_fir())
        naive = signal[::factor]
        proper = filtered[::factor]
        fs_low_hz = fs_hz / factor
        alias_hz = fold_frequency(420.0, fs_low_hz)
        self.assertEqual(alias_hz, 180.0)
        self.assertAlmostEqual(tone_amplitude(naive, alias_hz, fs_low_hz), 0.65, places=10)
        self.assertLess(tone_amplitude(proper, alias_hz, fs_low_hz), 0.01)
        self.assertGreater(tone_amplitude(proper, 90.0, fs_low_hz), 0.95)

    def test_zero_insertion_images_and_reconstruction_recovery_independently(self):
        fs_hz = 2400.0
        fs_low_hz = 600.0
        low_rate = [math.cos(2 * math.pi * 90 * index / fs_low_hz + 0.20) for index in range(600)]
        zero_inserted = [0.0] * 2400
        zero_inserted[::4] = low_rate
        reconstructed = fir_aligned(zero_inserted, design_fir(), gain=4.0)
        self.assertAlmostEqual(tone_amplitude(zero_inserted, 90.0, fs_hz), 0.25, places=10)
        self.assertAlmostEqual(tone_amplitude(zero_inserted, 510.0, fs_hz), 0.25, places=10)
        self.assertGreater(tone_amplitude(reconstructed, 90.0, fs_hz), 0.95)
        self.assertLess(tone_amplitude(reconstructed, 510.0, fs_hz), 0.01)

    def test_end_to_end_filtered_rate_change_rejects_alias_and_image(self):
        fs_hz = 2400.0
        factor = 4
        sample_count = 2400
        signal = [
            math.cos(2 * math.pi * 90 * index / fs_hz + 0.20)
            + 0.65 * math.cos(2 * math.pi * 420 * index / fs_hz - 0.35)
            for index in range(sample_count)
        ]
        coefficients = design_fir()
        decimated = fir_aligned(signal, coefficients)[::factor]
        zero_inserted = [0.0] * sample_count
        zero_inserted[::factor] = decimated
        reconstructed = fir_aligned(zero_inserted, coefficients, gain=float(factor))

        self.assertGreater(tone_amplitude(reconstructed, 90.0, fs_hz), 0.95)
        self.assertLess(tone_amplitude(reconstructed, 180.0, fs_hz), 0.01)
        self.assertLess(tone_amplitude(reconstructed, 510.0, fs_hz), 0.01)
        self.assertIn(
            "zero_inserted_v(1:decimation_factor:end) = decimated_filtered_v;",
            self.experiment,
        )

    def test_reconstruction_filter_cannot_repair_naive_decimation_alias(self):
        fs_hz = 2400.0
        factor = 4
        sample_count = 2400
        signal = [
            math.cos(2 * math.pi * 90 * index / fs_hz + 0.20)
            + 0.65 * math.cos(2 * math.pi * 420 * index / fs_hz - 0.35)
            for index in range(sample_count)
        ]
        naively_decimated = signal[::factor]
        zero_inserted = [0.0] * sample_count
        zero_inserted[::factor] = naively_decimated
        reconstruction_only = fir_aligned(
            zero_inserted,
            design_fir(),
            gain=float(factor),
        )

        self.assertGreater(tone_amplitude(reconstruction_only, 90.0, fs_hz), 0.95)
        self.assertGreater(tone_amplitude(reconstruction_only, 180.0, fs_hz), 0.60)
        self.assertLess(tone_amplitude(reconstruction_only, 420.0, fs_hz), 0.01)
        self.assertIn(
            "Once 420 Hz and 180 Hz share the same low-rate samples, no later filter can",
            self.lesson,
        )

    def test_high_tone_sweep_crosses_nyquist_with_one_visible_control(self):
        sweep = [220.0, 280.0, 340.0, 420.0]
        self.assertEqual([fold_frequency(value, 600.0) for value in sweep], [220.0, 280.0, 260.0, 180.0])
        self.assertIn("high_tone_sweep_hz = [220 280 340 420];", self.experiment)
        sweep_section = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        self.assertIn("sweep_high_hz = high_tone_sweep_hz(sweep_index);", sweep_section)
        self.assertIn("anti_alias_fir(tap_index)*sweep_input_v", sweep_section)
        self.assertNotIn("anti_alias_cutoff_hz =", sweep_section)
        self.assertNotIn("decimation_factor =", sweep_section)

    def test_reconstruction_tap_sweep_reduces_first_image(self):
        fs_hz = 2400.0
        low_rate = [math.cos(2 * math.pi * 90 * index / 600.0 + 0.20) for index in range(600)]
        zero_inserted = [0.0] * 2400
        zero_inserted[::4] = low_rate
        image_amplitudes = [
            tone_amplitude(fir_aligned(zero_inserted, design_fir(taps), gain=4.0), 510.0, fs_hz)
            for taps in (9, 17, 33, 65)
        ]
        self.assertGreater(image_amplitudes[0], 0.1)
        self.assertLess(image_amplitudes[-1], 0.01)
        self.assertLess(image_amplitudes[-1], image_amplitudes[1])
        self.assertIn("reconstruction_tap_sweep = [9 17 33 65];", self.experiment)
        self.assertIn("change only reconstruction-filter length", self.walkthrough.lower())

    def test_malformed_numeric_inputs_and_resource_bounds(self):
        for tap_count in (8, 10, 130, True):
            with self.assertRaises(ValueError):
                design_fir(tap_count)
        for cutoff in (0.0, 1200.0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                design_fir(cutoff_hz=cutoff)
        with self.assertRaises(ValueError):
            design_fir(fs_hz=0.0)
        with self.assertRaises(ValueError):
            fold_frequency(420.0, 0.0)
        for marker in (
            "max_record_samples = 4800;",
            "max_filter_taps = 129;",
            "max_sweep_cases = 8;",
            "max_figure_groups = 5;",
            "record_sample_count <= max_record_samples",
            "filter_tap_count <= max_filter_taps",
            "P10 resource ceilings must remain fixed.",
        ):
            self.assertIn(marker, self.experiment)

    def test_validation_precedes_allocation_and_figure_replacement(self):
        resource_guard = self.experiment.index("P10 resource ceilings must remain fixed.")
        stream_allocation = self.experiment.index("stream = RandStream")
        figure_replacement = self.experiment.index("old_figures = findall")
        self.assertLess(resource_guard, stream_allocation)
        self.assertLess(stream_allocation, figure_replacement)
        self.assertIn("new_nyquist_hz = fs_low_hz/2;", self.experiment)
        self.assertIn("anti_alias_cutoff_hz < new_nyquist_hz", self.experiment)
        self.assertIn("mod(record_sample_count, decimation_factor) == 0", self.experiment)

    def test_plots_metrics_and_units_cover_both_artifacts(self):
        for figure_name in (
            "P10 baseline decimation",
            "P10 baseline interpolation",
            "P10 high-tone sweep",
            "P10 reconstruction sweep",
            "P10 broken case and recovery",
        ):
            self.assertIn(figure_name, self.experiment)
        for unit_label in (
            "Time (ms)",
            "Amplitude (V)",
            "Frequency (Hz)",
            "Amplitude (dBV)",
            "Original high-tone frequency (Hz)",
            "Reconstruction FIR taps",
        ):
            self.assertIn(unit_label, self.experiment)
        for metric in (
            "results.alias_high_hz",
            "results.anti_alias_suppression_db",
            "results.first_image_hz",
            "results.image_suppression_db",
            "results.sweep_alias_frequency_hz",
            "results.sweep_image_amplitude_v",
        ):
            self.assertIn(metric, self.experiment)

    def test_broken_case_recovery_and_ordering_are_explicit(self):
        self.assertIn("Broken: drop samples", self.experiment)
        self.assertIn("Broken: zero insertion only", self.experiment)
        self.assertIn("Recovery: prefilter", self.experiment)
        self.assertIn("Recovery: reconstruction FIR", self.experiment)
        combined = "\n".join((self.lesson, self.walkthrough, self.checks))
        self.assertIn("before decimation", combined)
        self.assertIn("after zero insertion", combined)
        self.assertIn("irreversible aliasing", combined)
        self.assertIn("interpolation images", combined)

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
        self.assertIn("'Tag', 'P10'", self.experiment)
        self.assertIn("Ctrl+C", self.walkthrough)
        self.assertIn("private seed", self.walkthrough)
        self.assertIn("writes no files", self.readme)
        self.assertIn("manifest status to `scaffolded`", self.readme)

    def test_no_placeholder_or_unexplained_black_box_regression(self):
        combined = "\n".join((self.readme, self.experiment, self.lesson, self.walkthrough, self.checks))
        self.assertNotRegex(combined, r"(?i)\b(TODO|TBD|lorem ipsum)\b")
        source_without_comments = "\n".join(
            line.split("%", 1)[0] for line in self.experiment.splitlines()
        ).lower()
        for hidden_call in (
            "decimate(",
            "downsample(",
            "upsample(",
            "interp(",
            "resample(",
            "fir1(",
            "designfilt(",
            "filter(",
            "fftfilt(",
            "sinc(",
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
            "## The two operations made visible",
            "## Limiting cases",
            "## Radar connection and common interpretation mistakes",
        ):
            self.assertIn(heading, self.lesson)
        for heading in (
            "## Baseline: observe decimation before interpolation",
            "## Sweep 1: change only the high-tone frequency",
            "## Sweep 2: change only reconstruction-filter length",
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
        self.assertNotIn("MATLAB syntax", self.lesson)


if __name__ == "__main__":
    unittest.main()
