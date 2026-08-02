from __future__ import annotations

import cmath
import copy
import json
import math
import random
import statistics
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/20-estimate-tone-frequency-and-phase-from-noisy-samples"
EVIDENCE = ROOT / "docs/evidence/P20-2026-08-02.md"
QUESTION = "How accurately can frequency and phase be estimated from a finite noisy record?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
EXPECTED_IDENTITY = {
    "number": 20,
    "id": "P20",
    "title": "Estimate Tone Frequency and Phase from Noisy Samples",
    "guiding_question": QUESTION,
    "phase": 2,
    "phase_title": "Fourier, Spectral, and I/Q Intuition",
    "slug": "estimate-tone-frequency-and-phase-from-noisy-samples",
    "folder": "modules/20-estimate-tone-frequency-and-phase-from-noisy-samples",
    "status": "implemented",
    "implementation_batch": "P20",
}


def validate_p20_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P20 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P20 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    matches = [entry for entry in modules if isinstance(entry, dict) and entry.get("id") == "P20"]
    if len(matches) != 1:
        return errors + [f"expected one P20 manifest entry, found {len(matches)}"]
    entry = matches[0]
    for key, expected in EXPECTED_IDENTITY.items():
        if entry.get(key) != expected:
            errors.append(f"P20 {key} must be {expected!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def canonical_controls() -> dict:
    return {
        "random_seed": 1020,
        "fs_hz": 1024.0,
        "record_sample_count": 256,
        "tone_frequency_hz": 123.25,
        "tone_amplitude_v": 1.0,
        "tone_phase_rad": 2.70,
        "baseline_snr_db": 8.0,
        "snr_sweep_db": (-10.0, 0.0, 10.0, 20.0),
        "record_length_sweep": (64, 128, 256, 512),
        "trial_count": 40,
        "coherence_threshold": 0.20,
        "low_amplitude_v": 0.02,
        "max_record_samples": 512,
        "max_fft_length": 512,
        "max_sweep_cases": 4,
        "max_trials": 40,
        "max_stored_numeric_values": 100000,
        "max_figure_groups": 6,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    scalar_names = (
        "random_seed", "fs_hz", "record_sample_count", "tone_frequency_hz",
        "tone_amplitude_v", "tone_phase_rad", "baseline_snr_db", "trial_count",
        "coherence_threshold", "low_amplitude_v", "max_record_samples",
        "max_fft_length", "max_sweep_cases", "max_trials",
        "max_stored_numeric_values", "max_figure_groups",
    )
    if not all(_finite_real(controls[name]) for name in scalar_names):
        raise ValueError("scalar controls must be finite, real, and nonlogical")
    if controls["random_seed"] != 1020:
        raise ValueError("canonical seed required")
    if controls["fs_hz"] != 1024 or controls["record_sample_count"] != 256:
        raise ValueError("canonical sampling record required")
    if controls["tone_frequency_hz"] != 123.25:
        raise ValueError("canonical fractional-bin tone required")
    if controls["tone_amplitude_v"] != 1 or controls["tone_phase_rad"] != 2.70:
        raise ValueError("canonical amplitude and phase required")
    if controls["baseline_snr_db"] != 8:
        raise ValueError("canonical SNR required")
    if controls["snr_sweep_db"] != (-10.0, 0.0, 10.0, 20.0):
        raise ValueError("canonical SNR sweep required")
    if controls["record_length_sweep"] != (64, 128, 256, 512):
        raise ValueError("canonical length sweep required")
    if not all(_finite_real(value) for value in controls["snr_sweep_db"]):
        raise ValueError("SNR sweep must be finite and real")
    if not all(
        _finite_real(value) and value == int(value) and 2 <= value <= 512
        for value in controls["record_length_sweep"]
    ):
        raise ValueError("length sweep must contain bounded integers")
    if controls["trial_count"] != 40:
        raise ValueError("canonical trial count required")
    if controls["coherence_threshold"] != 0.20:
        raise ValueError("canonical coherence gate required")
    if controls["low_amplitude_v"] != 0.02:
        raise ValueError("canonical low amplitude required")
    ceilings = {
        "max_record_samples": 512,
        "max_fft_length": 512,
        "max_sweep_cases": 4,
        "max_trials": 40,
        "max_stored_numeric_values": 100000,
        "max_figure_groups": 6,
    }
    if any(controls[name] != expected for name, expected in ceilings.items()):
        raise ValueError("resource ceilings are fixed")


def tone(count: int, *, amplitude: float = 1.0) -> list[complex]:
    fs_hz = 1024.0
    frequency_hz = 123.25
    phase_rad = 2.70
    return [
        amplitude * cmath.exp(1j * (2 * math.pi * frequency_hz * n / fs_hz + phase_rad))
        for n in range(count)
    ]


def dft(signal: list[complex]) -> list[complex]:
    count = len(signal)
    return [
        sum(value * cmath.exp(-2j * math.pi * k * n / count) for n, value in enumerate(signal))
        for k in range(count)
    ]


def three_frequency_estimates(signal: list[complex], fs_hz: float = 1024.0) -> tuple[float, float, float]:
    spectrum = dft(signal)
    magnitudes = [abs(value) / len(signal) for value in spectrum]
    peak_index = max(range(len(signal)), key=magnitudes.__getitem__)
    signed_peak = peak_index - len(signal) if peak_index >= len(signal) / 2 else peak_index
    left = (peak_index - 1) % len(signal)
    right = (peak_index + 1) % len(signal)
    logs = [math.log(max(magnitudes[index], 1e-15)) for index in (left, peak_index, right)]
    denominator = logs[0] - 2 * logs[1] + logs[2]
    delta = 0.5 * (logs[0] - logs[2]) / denominator if abs(denominator) > 1e-15 else 0.0
    delta = max(-0.5, min(0.5, delta))
    adjacent = [a.conjugate() * b for a, b in zip(signal, signal[1:])]
    coherent = sum(adjacent)
    return (
        signed_peak * fs_hz / len(signal),
        (signed_peak + delta) * fs_hz / len(signal),
        cmath.phase(coherent) * fs_hz / (2 * math.pi),
    )


def phase_estimate(signal: list[complex], frequency_hz: float, fs_hz: float = 1024.0) -> float:
    projection = sum(
        value * cmath.exp(-2j * math.pi * frequency_hz * n / fs_hz)
        for n, value in enumerate(signal)
    )
    return cmath.phase(projection)


def wrapped_error(estimate: float, truth: float) -> float:
    return math.atan2(math.sin(estimate - truth), math.cos(estimate - truth))


def coherence(signal: list[complex]) -> float:
    adjacent = [a.conjugate() * b for a, b in zip(signal, signal[1:])]
    return abs(sum(adjacent)) / sum(abs(value) for value in adjacent)


def noisy_tone(rng: random.Random, count: int, snr_db: float, *, amplitude: float = 1.0) -> list[complex]:
    noise_rms = 10 ** (-8.0 / 20.0)
    if amplitude == 1.0:
        noise_rms = amplitude * 10 ** (-snr_db / 20.0)
    sigma = noise_rms / math.sqrt(2)
    return [
        value + complex(rng.gauss(0.0, sigma), rng.gauss(0.0, sigma))
        for value in tone(count, amplitude=amplitude)
    ]


class P20ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.experiment = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        cls.all_content = "\n".join(
            (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        )

    def test_artifacts_manifest_identity_dependency_and_public_catalogs(self):
        self.assertEqual(validate_p20_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            path = MODULE / name
            self.assertGreater(path.stat().st_size, 100)
            self.assertIn(QUESTION, path.read_text(encoding="utf-8"))
        p19 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P19")
        self.assertEqual(p19["status"], "implemented")
        self.assertIn("P19", self.readme)
        self.assertIn("P19", self.lesson)
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertRegex(module_index, r"\| \[P20\].*\| implemented \|")

    def test_contract_rejects_missing_empty_duplicate_nonlist_and_wrong_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "checks.md").unlink()
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p20_contract(fixture, self.manifest)
            self.assertIn("P20 missing checks.md", errors)
            self.assertIn("P20 empty lesson.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][19]))
        self.assertIn(
            "expected one P20 manifest entry, found 2",
            validate_p20_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p20_contract(MODULE, {"modules": "P20"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][19]["guiding_question"] = "generic"
        malformed["modules"][19]["status"] = "scaffolded"
        errors = validate_p20_contract(MODULE, malformed)
        self.assertIn(f"P20 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P20 status must be 'implemented'", errors)

    def test_deterministic_visible_complex_tone_and_noise_contract(self):
        for marker in (
            "random_seed = 1020;",
            "fs_hz = 1024;",
            "record_sample_count = 256;",
            "tone_frequency_hz = 123.25;",
            "tone_phase_rad = 2.70;",
            "baseline_snr_db = 8;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "noise_rms_v = tone_amplitude_v*10^(-baseline_snr_db/20);",
            "complex_noise_v = noise_rms_v/sqrt(2)*( ...",
            "clean_iq_v = tone_amplitude_v*exp(1j*true_phase_v);",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_noiseless_estimators_expose_grid_interpolation_and_coherent_phase(self):
        signal = tone(256)
        peak, interpolated, phase_increment = three_frequency_estimates(signal)
        self.assertEqual(peak, 124.0)
        self.assertLess(abs(interpolated - 123.25), abs(peak - 123.25))
        self.assertAlmostEqual(phase_increment, 123.25, places=11)
        self.assertAlmostEqual(phase_estimate(signal, phase_increment), 2.70, places=11)
        self.assertGreater(abs(wrapped_error(phase_estimate(signal, peak), 2.70)), 0.1)

    def test_matlab_source_is_linked_to_independently_checked_equations(self):
        for formula in (
            "baseline_fft_v = fft(noisy_iq_v);",
            "interpolated_bin_offset = 0.5*(log_left-log_right)/ ...\n"
            "    interpolation_denominator;",
            "adjacent_products_v2 = conj(noisy_iq_v(1:end-1)).*noisy_iq_v(2:end);",
            "phase_increment_frequency_hz = phase_increment_rad*fs_hz/(2*pi);",
            "baseline_phase_estimates_rad(estimator_index) = angle(sum( ...\n"
            "        noisy_iq_v.*estimated_reference));",
            "baseline_phase_errors_rad(estimator_index) = atan2( ...\n"
            "        sin(phase_difference_rad), cos(phase_difference_rad));",
        ):
            self.assertIn(formula, self.experiment)

    def test_snr_changes_coherence_and_phase_increment_spread_deterministically(self):
        def trial_metrics(snr_db: float) -> tuple[float, float]:
            rng = random.Random(2020)
            estimates = []
            coherences = []
            for _ in range(40):
                signal = noisy_tone(rng, 256, snr_db)
                adjacent = [a.conjugate() * b for a, b in zip(signal, signal[1:])]
                estimates.append(cmath.phase(sum(adjacent)) * 1024 / (2 * math.pi))
                coherences.append(coherence(signal))
            return statistics.pstdev(estimates), statistics.mean(coherences)

        low = trial_metrics(-10.0)
        high = trial_metrics(20.0)
        self.assertGreater(low[0], high[0] * 5)
        self.assertLess(low[1], high[1])
        self.assertEqual(high, trial_metrics(20.0))
        self.assertIn(
            "sweep_standard_noise = 1/sqrt(2)*( ...", self.experiment
        )
        self.assertIn(
            "trial_noise_v = case_noise_rms_v* ...\n"
            "            sweep_standard_noise(trial_index, 1:record_sample_count);",
            self.experiment,
        )

    def test_record_length_adds_coherent_evidence_for_fixed_tone_and_snr(self):
        rng = random.Random(3020)
        noise_rows = [
            [complex(rng.gauss(0.0, 1 / math.sqrt(2)), rng.gauss(0.0, 1 / math.sqrt(2)))
             for _ in range(512)]
            for _ in range(40)
        ]
        errors: dict[int, list[float]] = {64: [], 512: []}
        for count in errors:
            clean = tone(count)
            noise_rms = 10 ** (-8.0 / 20.0)
            for trial_index in range(40):
                signal = [
                    value + noise_rms * noise
                    for value, noise in zip(clean, noise_rows[trial_index][:count])
                ]
                adjacent = [a.conjugate() * b for a, b in zip(signal, signal[1:])]
                estimate = cmath.phase(sum(adjacent)) * 1024 / (2 * math.pi)
                errors[count].append(estimate - 123.25)
        self.assertGreater(statistics.pstdev(errors[64]), statistics.pstdev(errors[512]))
        self.assertEqual([len(values) for values in errors.values()], [40, 40])
        length_section = self.experiment.split("%% Sweep 2", 1)[1].split("%% Broken case", 1)[0]
        self.assertIn("record_length_sweep = [64 128 256 512];", self.experiment)
        self.assertNotIn("baseline_snr_db =", length_section)
        self.assertNotIn("tone_frequency_hz =", length_section)
        self.assertIn(
            "sweep_standard_noise(trial_index, 1:case_sample_count)",
            length_section,
        )

    def test_broken_wrapped_endpoint_and_low_amplitude_gate(self):
        signal = tone(256)
        elapsed = 255 / 1024
        broken = cmath.phase(signal[-1] * signal[0].conjugate()) / (2 * math.pi * elapsed)
        adjacent = [a.conjugate() * b for a, b in zip(signal, signal[1:])]
        recovered = cmath.phase(sum(adjacent)) * 1024 / (2 * math.pi)
        self.assertGreater(abs(broken - 123.25), 100)
        self.assertAlmostEqual(recovered, 123.25, places=11)

        rng = random.Random(4020)
        low_signal = noisy_tone(rng, 256, -26.0, amplitude=0.02)
        self.assertLess(coherence(low_signal), 0.20)
        broken_section = self.experiment.split("%% Broken case", 1)[1].split(
            "%% Retained workspace results", 1
        )[0]
        self.assertIn("broken_endpoint_frequency_hz", broken_section)
        self.assertIn("low_amplitude_reported_frequency_hz = NaN;", broken_section)
        self.assertIn("low_amplitude_coherence >= coherence_threshold", broken_section)

    def test_low_amplitude_gate_pairs_the_same_noise_and_withholds_only_unsupported_result(self):
        rng = random.Random(4020)
        noise_rms = 10 ** (-8.0 / 20.0)
        noise = [
            complex(
                rng.gauss(0.0, noise_rms / math.sqrt(2)),
                rng.gauss(0.0, noise_rms / math.sqrt(2)),
            )
            for _ in range(256)
        ]
        baseline_signal = [
            clean + disturbance
            for clean, disturbance in zip(tone(256), noise)
        ]
        low_amplitude_signal = [
            clean + disturbance
            for clean, disturbance in zip(tone(256, amplitude=0.02), noise)
        ]

        baseline_coherence = coherence(baseline_signal)
        low_amplitude_coherence = coherence(low_amplitude_signal)
        low_amplitude_candidate_hz = three_frequency_estimates(low_amplitude_signal)[2]
        low_amplitude_reported_hz = (
            low_amplitude_candidate_hz
            if low_amplitude_coherence >= 0.20
            else math.nan
        )

        self.assertGreater(baseline_coherence, 0.20)
        self.assertLess(low_amplitude_coherence, 0.20)
        self.assertTrue(math.isfinite(low_amplitude_candidate_hz))
        self.assertTrue(math.isnan(low_amplitude_reported_hz))

        broken_section = self.experiment.split("%% Broken case", 1)[1].split(
            "%% Retained workspace results", 1
        )[0]
        self.assertIn(
            "low_amplitude_iq_v = low_amplitude_clean_iq_v + complex_noise_v;",
            broken_section,
        )
        self.assertNotIn("randn(", broken_section)

    def test_malformed_controls_and_resource_ceilings(self):
        for key, value in (
            ("random_seed", True),
            ("fs_hz", math.nan),
            ("record_sample_count", 255),
            ("tone_frequency_hz", complex(123.25, 1)),
            ("tone_amplitude_v", 0.0),
            ("tone_phase_rad", math.inf),
            ("baseline_snr_db", 7.0),
            ("snr_sweep_db", (-10.0, 0.0, 20.0)),
            ("record_length_sweep", (64, 128, 256, 1024)),
            ("trial_count", 41),
            ("coherence_threshold", 0.0),
            ("low_amplitude_v", -0.02),
            ("max_record_samples", 1024),
            ("max_fft_length", 1024),
            ("max_sweep_cases", 5),
            ("max_trials", 80),
            ("max_stored_numeric_values", 200000),
            ("max_figure_groups", 7),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_controls(**{key: value})
        with self.assertRaises(ValueError):
            validate_controls(unknown_control=1)

    def test_validation_precedes_random_signal_fft_cleanup_and_figure_work(self):
        validation_end = self.experiment.index("% Validation succeeded:")
        for marker in (
            "RandStream(",
            "time_s = (0:record_sample_count-1)/fs_hz;",
            "fft(",
            "close(findall(",
            "figure('Name'",
        ):
            self.assertGreater(self.experiment.index(marker), validation_end, marker)
        self.assertIn("workspace_vector_equivalents = 80;", self.experiment[:validation_end])
        self.assertIn("figure_vector_equivalents = 30;", self.experiment[:validation_end])
        self.assertIn("resource_safety_vector_equivalents = 10;", self.experiment[:validation_end])
        self.assertIn("max_stored_numeric_values = 100000;", self.experiment[:validation_end])
        self.assertLessEqual(512 * (80 + 30 + 10), 100000)

    def test_sweep_and_plot_metric_unit_inventory_is_complete(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 6)
        self.assertEqual(self.experiment.count("'Tag', 'P20'"), 7)
        self.assertEqual(self.experiment.count("for sweep_index ="), 2)
        self.assertEqual(self.experiment.count("for trial_index ="), 2)
        for label in (
            "Time (ms)", "In-phase sample I (V)", "Quadrature sample Q (V)",
            "Frequency (Hz)", "Frequency error (Hz)", "Residual phase (rad)",
            "Frequency bias (Hz)", "Frequency standard deviation (Hz)",
            "Circular phase bias (deg)", "Phase circular std (deg)",
            "Mean adjacent-product coherence (0 to 1)",
            "Adjacent-product coherence (0 to 1)",
        ):
            self.assertIn(label, self.experiment)
        snr_plot_section = self.experiment.split(
            "figure('Name', 'P20 SNR estimator sweep'", 1
        )[1].split("%% Sweep 2", 1)[0]
        self.assertNotIn("10*snr_mean_coherence", snr_plot_section)
        self.assertIn(
            "ylabel('Mean adjacent-product coherence (0 to 1)');",
            snr_plot_section,
        )
        for result in (
            "results.baseline_frequency_estimates_hz",
            "results.baseline_phase_estimates_rad",
            "results.baseline_coherence",
            "results.snr_frequency_bias_hz",
            "results.snr_frequency_std_hz",
            "results.snr_phase_circular_std_rad",
            "results.length_frequency_bias_hz",
            "results.length_phase_circular_std_rad",
            "results.broken_endpoint_frequency_hz",
            "results.low_amplitude_reported_frequency_hz",
        ):
            self.assertIn(result, self.experiment)

    def test_content_is_concept_first_complete_and_runtime_claim_boundary_is_honest(self):
        lowered = self.all_content.lower()
        for placeholder in ("todo", "tbd", "placeholder"):
            self.assertNotIn(placeholder, lowered)
        for phrase in (
            "physical mental model", "limiting cases", "radar connection",
            "common interpretation mistakes", "coherent phase increment",
        ):
            self.assertIn(phrase, self.lesson.lower())
        for heading in (
            "## Baseline", "## Sweep 1", "## Sweep 2", "## Broken case",
            "## Concept connection and completion handoff",
        ):
            self.assertIn(heading, self.walkthrough)
        self.assertIn("## Teach-back completion", self.checks)
        self.assertTrue(EVIDENCE.is_file())
        evidence = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("does **not** claim MATLAB or Octave execution", evidence)
        self.assertIn("Acceptance mapping", evidence)
        self.assertIn("Residual risks and unperformed validation", evidence)

    def test_no_placeholder_unexplained_black_box_or_external_io(self):
        lowered = self.experiment.lower()
        for opaque in (
            "instfreq(", "periodogram(", "pwelch(", "spectrogram(", "hilbert(",
            "phased.", "dsp.", "comm.", "helper",
        ):
            self.assertNotIn(opaque, lowered)
        for unsafe in (
            "input(", "pause(", "while ", "timer(", "parfor ", "parfeval(",
            "fopen(", "webread(", "audioplayer(", "sound(", "system(",
            "close all", "clear all", "clearvars",
        ):
            self.assertNotIn(unsafe, lowered)
        self.assertNotRegex(lowered, r"\b(?:read|write)(?:matrix|table)\s*\(")

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback(self):
        self.assertNotIn("while ", self.experiment.lower())
        self.assertIn("Ctrl+C", self.experiment)
        self.assertIn("Ctrl+C", self.walkthrough)
        self.assertIn("private seed", self.walkthrough)
        self.assertIn("global random stream", self.walkthrough)
        self.assertIn("P20-tagged figures", self.walkthrough)
        self.assertIn("partial P20 figure set", self.experiment)
        self.assertIn("empty/incomplete `results`", self.walkthrough)
        self.assertIn("Rerun from the top", self.walkthrough)
        self.assertIn("Rollback", self.walkthrough)
        self.assertIn("restores only P20's", self.walkthrough)
        self.assertIn("Preserve implemented P19", self.walkthrough)


if __name__ == "__main__":
    unittest.main()
