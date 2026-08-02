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
MODULE = ROOT / "modules/18-contrast-real-and-complex-sampling"
EVIDENCE = ROOT / "docs/evidence/P18-2026-08-02.md"
QUESTION = "Why can complex samples distinguish positive and negative frequencies?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def validate_p18_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P18 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P18 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    entries = [
        entry for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P18"
    ]
    if len(entries) != 1:
        return errors + [f"expected one P18 manifest entry, found {len(entries)}"]

    expected = {
        "number": 18,
        "id": "P18",
        "title": "Contrast Real and Complex Sampling",
        "guiding_question": QUESTION,
        "phase": 2,
        "phase_title": "Fourier, Spectral, and I/Q Intuition",
        "slug": "contrast-real-and-complex-sampling",
        "folder": "modules/18-contrast-real-and-complex-sampling",
        "status": "implemented",
        "implementation_batch": "P18",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P18 {key} must be {value!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_controls(**overrides: object) -> None:
    controls: dict[str, object] = {
        "random_seed": 1018,
        "fs_hz": 2048.0,
        "record_sample_count": 4096,
        "tone_frequency_hz": 160.0,
        "tone_amplitude_v": 1.0,
        "tone_phase_rad": 0.35,
        "noise_rms_v": 0.002,
        "lo_frequency_hz": 600.0,
        "lowpass_cutoff_hz": 450.0,
        "lowpass_tap_count": 129,
        "evaluation_guard_sample_count": 192,
        "offset_frequency_sweep_hz": (40.0, 160.0, 400.0),
        "sample_rate_sweep_hz": (2048.0, 512.0, 256.0),
        "sweep_record_duration_s": 0.5,
        "max_record_samples": 4096,
        "max_fft_length": 4096,
        "max_filter_taps": 129,
        "max_sweep_cases": 3,
        "max_stored_numeric_values": 180000,
        "max_figure_groups": 6,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    scalar_names = (
        "random_seed", "fs_hz", "record_sample_count", "tone_frequency_hz",
        "tone_amplitude_v", "tone_phase_rad", "noise_rms_v",
        "lo_frequency_hz", "lowpass_cutoff_hz", "lowpass_tap_count",
        "evaluation_guard_sample_count", "sweep_record_duration_s",
    )
    if not all(_finite_real(controls[name]) for name in scalar_names):
        raise ValueError("scalar controls must be finite real nonlogical values")
    if controls["random_seed"] != 1018:
        raise ValueError("canonical seed required")
    if controls["fs_hz"] != 2048 or controls["record_sample_count"] != 4096:
        raise ValueError("canonical rate and record required")
    if int(controls["record_sample_count"]) % 2:
        raise ValueError("record must be even")
    if controls["tone_frequency_hz"] != 160:
        raise ValueError("canonical tone required")
    if not 0 < controls["tone_amplitude_v"] <= 2:
        raise ValueError("amplitude must be positive and bounded")
    if not 0 <= controls["noise_rms_v"] <= 0.01:
        raise ValueError("noise must be nonnegative and bounded")
    if controls["lo_frequency_hz"] != 600:
        raise ValueError("canonical LO required")
    if controls["lowpass_cutoff_hz"] != 450:
        raise ValueError("canonical cutoff required")
    if controls["lowpass_tap_count"] != 129 or int(controls["lowpass_tap_count"]) % 2 == 0:
        raise ValueError("canonical odd FIR required")
    if controls["evaluation_guard_sample_count"] != 192:
        raise ValueError("canonical guard required")

    offsets = controls["offset_frequency_sweep_hz"]
    rates = controls["sample_rate_sweep_hz"]
    if offsets != (40.0, 160.0, 400.0):
        raise ValueError("canonical offset sweep required")
    if rates != (2048.0, 512.0, 256.0):
        raise ValueError("canonical rate sweep required")
    if controls["sweep_record_duration_s"] != 0.5:
        raise ValueError("canonical sweep duration required")
    if not all(_finite_real(value) and value > 0 for value in (*offsets, *rates)):
        raise ValueError("sweeps must contain positive finite real values")
    if any(rate * controls["sweep_record_duration_s"] % 1 for rate in rates):
        raise ValueError("sweep records must contain integer sample counts")
    if controls["lo_frequency_hz"] + max(offsets) >= controls["fs_hz"] / 2:
        raise ValueError("RF side exceeds Nyquist")
    if not max(offsets) < controls["lowpass_cutoff_hz"] < 2 * controls["lo_frequency_hz"] - max(offsets):
        raise ValueError("low-pass does not separate beats and sum terms")

    ceilings = {
        "max_record_samples": 4096,
        "max_fft_length": 4096,
        "max_filter_taps": 129,
        "max_sweep_cases": 3,
        "max_stored_numeric_values": 180000,
        "max_figure_groups": 6,
    }
    if any(controls[name] != expected for name, expected in ceilings.items()):
        raise ValueError("resource ceilings are fixed")


def build_pair(
    frequency_hz: float, fs_hz: float, count: int, phase_rad: float = 0.35
) -> tuple[list[complex], list[complex]]:
    positive = [
        cmath.exp(1j * (2 * math.pi * frequency_hz * index / fs_hz + phase_rad))
        for index in range(count)
    ]
    negative = [value.conjugate() for value in positive]
    return positive, negative


def estimate_frequency(signal: list[complex], fs_hz: float) -> float:
    product = sum(a.conjugate() * b for a, b in zip(signal, signal[1:]))
    return cmath.phase(product) * fs_hz / (2 * math.pi)


def alias_frequency(frequency_hz: float, fs_hz: float) -> float:
    return (frequency_hz + fs_hz / 2) % fs_hz - fs_hz / 2


def dft(signal: list[complex]) -> list[complex]:
    count = len(signal)
    return [
        sum(
            sample * cmath.exp(-2j * math.pi * bin_index * index / count)
            for index, sample in enumerate(signal)
        )
        for bin_index in range(count)
    ]


def conjugate_symmetry_error(spectrum: list[complex]) -> float:
    count = len(spectrum)
    return max(
        abs(spectrum[bin_index] - spectrum[(-bin_index) % count].conjugate())
        for bin_index in range(count)
    )


def magnitude_symmetry_error(spectrum: list[complex]) -> float:
    count = len(spectrum)
    return max(
        abs(abs(spectrum[bin_index]) - abs(spectrum[(-bin_index) % count]))
        for bin_index in range(count)
    )


def design_fir(
    tap_count: int = 129, fs_hz: float = 2048.0, cutoff_hz: float = 450.0
) -> list[float]:
    if isinstance(tap_count, bool) or tap_count != 129 or tap_count % 2 == 0:
        raise ValueError("P18 uses the canonical odd 129-tap FIR")
    if not math.isfinite(fs_hz) or fs_hz <= 0:
        raise ValueError("sample rate must be finite and positive")
    if not math.isfinite(cutoff_hz) or not 0 < cutoff_hz < fs_hz / 2:
        raise ValueError("cutoff must lie between DC and Nyquist")
    half = (tap_count - 1) // 2
    coefficients: list[float] = []
    for tap, centered in enumerate(range(-half, half + 1)):
        ideal = (
            2 * cutoff_hz / fs_hz
            if centered == 0
            else math.sin(2 * math.pi * cutoff_hz * centered / fs_hz)
            / (math.pi * centered)
        )
        window = 0.54 - 0.46 * math.cos(2 * math.pi * tap / (tap_count - 1))
        coefficients.append(ideal * window)
    gain = sum(coefficients)
    return [coefficient / gain for coefficient in coefficients]


def apply_fir_and_remove_group_delay(
    signal: list[float], coefficients: list[float]
) -> list[float]:
    full = [0.0] * (len(signal) + len(coefficients) - 1)
    for sample_index, sample in enumerate(signal):
        for tap_index, coefficient in enumerate(coefficients):
            full[sample_index + tap_index] += sample * coefficient
    half = (len(coefficients) - 1) // 2
    return full[half:half + len(signal)]


class P18ModuleTests(unittest.TestCase):
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
        cls.all_content = "\n".join(
            (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        )

    def test_artifacts_manifest_identity_dependency_and_public_catalogs(self):
        self.assertEqual(validate_p18_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            path = MODULE / name
            self.assertGreater(path.stat().st_size, 100)
            self.assertIn(QUESTION, path.read_text(encoding="utf-8"))
        p17 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P17")
        self.assertEqual(p17["status"], "implemented")
        self.assertIn("P17", self.readme)
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertRegex(module_index, r"\| \[P18\].*\| implemented \|")

    def test_contract_rejects_missing_empty_duplicate_nonlist_and_wrong_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "checks.md").unlink()
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p18_contract(fixture, self.manifest)
            self.assertIn("P18 missing checks.md", errors)
            self.assertIn("P18 empty lesson.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][17]))
        self.assertIn(
            "expected one P18 manifest entry, found 2",
            validate_p18_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p18_contract(MODULE, {"modules": "P18"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][17]["guiding_question"] = "generic"
        malformed["modules"][17]["status"] = "scaffolded"
        errors = validate_p18_contract(MODULE, malformed)
        self.assertIn(f"P18 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P18 status must be 'implemented'", errors)

    def test_deterministic_visible_base_matlab_operation_contract(self):
        for marker in (
            "random_seed = 1018;",
            "fs_hz = 2048;",
            "record_sample_count = 4096;",
            "tone_frequency_hz = 160;",
            "lo_frequency_hz = 600;",
            "lowpass_cutoff_hz = 450;",
            "lowpass_tap_count = 129;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "randn(private_stream, 1, record_sample_count)",
            "positive_iq_clean_v = tone_amplitude_v*exp(1j*(",
            "negative_iq_clean_v = tone_amplitude_v*exp(-1j*(",
            "negative_iq_v = conj(positive_iq_v);",
            "complex_lo = exp(-1j*2*pi*lo_frequency_hz*time_s);",
            "upper_complex_baseband_v = upper_rf_iq_v.*complex_lo;",
            "real_lo = 2*cos(2*pi*lo_frequency_hz*time_s);",
            "ideal_fir(tap_index) = sin(2*pi*lowpass_cutoff_hz*",
            "lowpass_fir = lowpass_fir/sum(lowpass_fir);",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_complex_pair_has_opposite_rotation_and_identical_real_projection(self):
        positive, negative = build_pair(32.0, 256.0, 256)
        self.assertAlmostEqual(estimate_frequency(positive, 256.0), 32.0, places=12)
        self.assertAlmostEqual(estimate_frequency(negative, 256.0), -32.0, places=12)
        self.assertLess(
            max(abs(a.real - b.real) for a, b in zip(positive, negative)),
            1e-14,
        )
        self.assertGreater(
            max(abs(a.imag - b.imag) for a, b in zip(positive, negative)),
            1.0,
        )

    def test_centered_spectra_separate_complex_sign_and_real_spectrum_is_symmetric(self):
        fs_hz = 64.0
        count = 64
        positive, negative = build_pair(8.0, fs_hz, count, phase_rad=0.0)
        real_tone = [value.real for value in positive]
        positive_dft = dft(positive)
        negative_dft = dft(negative)
        real_dft = dft([complex(value) for value in real_tone])
        self.assertEqual(max(range(count), key=lambda k: abs(positive_dft[k])), 8)
        self.assertEqual(max(range(count), key=lambda k: abs(negative_dft[k])), 56)
        self.assertAlmostEqual(abs(positive_dft[8]) / count, 1.0, places=12)
        self.assertAlmostEqual(abs(negative_dft[56]) / count, 1.0, places=12)
        self.assertAlmostEqual(abs(real_dft[8]) / count, 0.5, places=12)
        self.assertAlmostEqual(abs(real_dft[56]) / count, 0.5, places=12)
        for bin_index in range(1, count):
            self.assertAlmostEqual(
                abs(real_dft[bin_index]), abs(real_dft[-bin_index]), places=11
            )

    def test_real_spectrum_metric_checks_conjugate_phase_not_only_magnitude(self):
        real_tone = [
            math.cos(2 * math.pi * 8 * index / 64 + 0.35)
            for index in range(64)
        ]
        real_dft = dft([complex(value) for value in real_tone])
        self.assertLess(conjugate_symmetry_error(real_dft), 1e-10)

        magnitude_symmetric_but_phase_broken = [1 + 0j, 1j, 2 + 0j, 1j]
        self.assertEqual(
            magnitude_symmetry_error(magnitude_symmetric_but_phase_broken), 0.0
        )
        self.assertEqual(
            conjugate_symmetry_error(magnitude_symmetric_but_phase_broken), 2.0
        )

        self.assertIn(
            "real_spectrum_complex_v = fftshift(fft(positive_real_v))",
            self.experiment,
        )
        self.assertIn(
            "conj(circshift(fliplr(real_spectrum_complex_v)", self.experiment
        )
        self.assertNotIn(
            "real_spectrum_v - ...\n    circshift(fliplr(real_spectrum_v)",
            self.experiment,
        )

    def test_complex_downconversion_preserves_side_of_lo(self):
        fs_hz = 512.0
        lo_hz = 128.0
        offset_hz = 32.0
        count = 512
        phase = 0.35
        upper = [
            cmath.exp(1j * (2 * math.pi * (lo_hz + offset_hz) * n / fs_hz + phase))
            for n in range(count)
        ]
        lower = [
            cmath.exp(1j * (2 * math.pi * (lo_hz - offset_hz) * n / fs_hz - phase))
            for n in range(count)
        ]
        oscillator = [
            cmath.exp(-1j * 2 * math.pi * lo_hz * n / fs_hz)
            for n in range(count)
        ]
        upper_baseband = [sample * lo for sample, lo in zip(upper, oscillator)]
        lower_baseband = [sample * lo for sample, lo in zip(lower, oscillator)]
        self.assertAlmostEqual(estimate_frequency(upper_baseband, fs_hz), 32.0, places=12)
        self.assertAlmostEqual(estimate_frequency(lower_baseband, fs_hz), -32.0, places=12)
        self.assertAlmostEqual(cmath.phase(upper_baseband[0]), phase, places=12)
        self.assertAlmostEqual(cmath.phase(lower_baseband[0]), -phase, places=12)

    def test_finite_real_mixer_and_explicit_fir_collapse_upper_and_lower_sides(self):
        fs_hz = 2048.0
        count = 4096
        lo_hz = 600.0
        offset_hz = 160.0
        phase = 0.35
        coefficients = design_fir()
        self.assertAlmostEqual(sum(coefficients), 1.0, places=13)
        real_lo = [2 * math.cos(2 * math.pi * lo_hz * n / fs_hz) for n in range(count)]
        upper = [
            math.cos(2 * math.pi * (lo_hz + offset_hz) * n / fs_hz + phase)
            for n in range(count)
        ]
        lower = [
            math.cos(2 * math.pi * (lo_hz - offset_hz) * n / fs_hz - phase)
            for n in range(count)
        ]
        upper_filtered = apply_fir_and_remove_group_delay(
            [value * mixer for value, mixer in zip(upper, real_lo)], coefficients
        )
        lower_filtered = apply_fir_and_remove_group_delay(
            [value * mixer for value, mixer in zip(lower, real_lo)], coefficients
        )
        guard = 192
        rmse = math.sqrt(sum(
            (a - b) ** 2
            for a, b in zip(
                upper_filtered[guard:-guard], lower_filtered[guard:-guard]
            )
        ) / (count - 2 * guard))
        self.assertLess(rmse, 0.001)
        expected = [
            math.cos(2 * math.pi * offset_hz * n / fs_hz + phase)
            for n in range(count)
        ]
        expected_rmse = math.sqrt(sum(
            (actual - target) ** 2
            for actual, target in zip(upper_filtered[guard:-guard], expected[guard:-guard])
        ) / (count - 2 * guard))
        self.assertLess(expected_rmse, 0.001)

    def test_offset_sweep_changes_only_rotation_speed_and_retains_collapse(self):
        section = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        self.assertIn("offset_frequency_sweep_hz = [40 160 400];", self.experiment)
        self.assertNotIn("fs_hz =", section)
        self.assertNotIn("tone_amplitude_v =", section)
        self.assertNotIn("tone_phase_rad =", section)
        for offset_hz in (40.0, 160.0, 400.0):
            positive, negative = build_pair(offset_hz, 2048.0, 4096)
            with self.subTest(offset_hz=offset_hz):
                self.assertAlmostEqual(estimate_frequency(positive, 2048.0), offset_hz, places=11)
                self.assertAlmostEqual(estimate_frequency(negative, 2048.0), -offset_hz, places=11)
                self.assertLess(
                    max(abs(a.real - b.real) for a, b in zip(positive, negative)),
                    1e-13,
                )

    def test_sample_rate_sweep_exposes_signed_alias_limit(self):
        section = self.experiment.split("%% Sweep 2", 1)[1].split("%% Broken case", 1)[0]
        self.assertIn("sample_rate_sweep_hz = [2048 512 256];", self.experiment)
        self.assertNotIn("tone_frequency_hz =", section)
        self.assertNotIn("tone_amplitude_v =", section)
        self.assertNotIn("tone_phase_rad =", section)
        expected = ((2048.0, 160.0, -160.0), (512.0, 160.0, -160.0), (256.0, -96.0, 96.0))
        for fs_hz, positive_alias, negative_alias in expected:
            positive, negative = build_pair(160.0, fs_hz, int(fs_hz / 2))
            with self.subTest(fs_hz=fs_hz):
                self.assertEqual(alias_frequency(160.0, fs_hz), positive_alias)
                self.assertEqual(alias_frequency(-160.0, fs_hz), negative_alias)
                self.assertAlmostEqual(estimate_frequency(positive, fs_hz), positive_alias, places=11)
                self.assertAlmostEqual(estimate_frequency(negative, fs_hz), negative_alias, places=11)

    def test_broken_q_discard_destroys_sign_and_iq_recovery_restores_it(self):
        positive, negative = build_pair(32.0, 256.0, 256)
        broken_positive = [complex(value.real) for value in positive]
        broken_negative = [complex(value.real) for value in negative]
        self.assertEqual(broken_positive, broken_negative)
        self.assertAlmostEqual(estimate_frequency(broken_positive, 256.0), 0.0, places=12)
        self.assertAlmostEqual(estimate_frequency(broken_negative, 256.0), 0.0, places=12)
        self.assertAlmostEqual(estimate_frequency(positive, 256.0), 32.0, places=12)
        self.assertAlmostEqual(estimate_frequency(negative, 256.0), -32.0, places=12)
        broken_section = self.experiment.split("%% Broken case", 1)[1].split(
            "%% Retained workspace results", 1
        )[0]
        self.assertIn("broken_positive_real_v = real(positive_iq_clean_v);", broken_section)
        self.assertIn("recovered_positive_frequency_hz", broken_section)
        self.assertNotIn("abs(broken_positive_frequency_hz)", broken_section)

    def test_malformed_controls_and_resource_ceilings(self):
        for key, value in (
            ("random_seed", True),
            ("fs_hz", math.nan),
            ("record_sample_count", 4095),
            ("tone_frequency_hz", complex(160, 1)),
            ("tone_amplitude_v", 0.0),
            ("noise_rms_v", -0.1),
            ("lo_frequency_hz", 700.0),
            ("lowpass_cutoff_hz", 399.0),
            ("lowpass_tap_count", 128),
            ("evaluation_guard_sample_count", 64),
            ("offset_frequency_sweep_hz", (40.0, 160.0, 401.0)),
            ("sample_rate_sweep_hz", (2048.0, 512.0, 255.0)),
            ("sweep_record_duration_s", 0.3),
            ("max_record_samples", 8192),
            ("max_fft_length", 8192),
            ("max_filter_taps", 257),
            ("max_sweep_cases", 4),
            ("max_stored_numeric_values", 360000),
            ("max_figure_groups", 7),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_controls(**{key: value})
        with self.assertRaises(ValueError):
            validate_controls(unknown_control=1)
        for tap_count in (128, 130, True):
            with self.assertRaises(ValueError):
                design_fir(tap_count=tap_count)

    def test_validation_precedes_random_signal_fft_fir_and_figure_work(self):
        validation_end = self.experiment.index("% Validation succeeded:")
        for marker in (
            "RandStream(",
            "time_s = (0:record_sample_count-1)/fs_hz;",
            "fft(",
            "ideal_fir = zeros",
            "figure('Name'",
            "close(findall(",
        ):
            self.assertGreater(self.experiment.index(marker), validation_end, marker)
        self.assertIn("estimated_stored_numeric_values", self.experiment[:validation_end])
        self.assertIn("max_figure_groups = 6;", self.experiment[:validation_end])

    def test_plot_metric_result_and_unit_inventory_is_complete(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 6)
        self.assertEqual(self.experiment.count("'Tag', 'P18'"), 7)
        for label in (
            "Time (ms)", "Real sample (V)", "I (V)", "Q (V)",
            "Signed frequency (Hz)", "Magnitude (dB re 1 V)",
            "Real baseband after LPF (V)",
        ):
            self.assertIn(label, self.experiment)
        for result in (
            "results.positive_estimated_frequency_hz",
            "results.negative_estimated_frequency_hz",
            "results.real_projection_rmse_v",
            "results.real_spectrum_symmetry_error_v",
            "results.upper_complex_frequency_hz",
            "results.lower_complex_frequency_hz",
            "results.real_mixer_collapse_rmse_v",
            "results.offset_sweep_positive_frequency_hz",
            "results.sample_rate_positive_alias_hz",
            "results.broken_positive_frequency_hz",
            "results.recovered_positive_frequency_hz",
        ):
            self.assertIn(result, self.experiment)

    def test_content_is_concept_first_complete_and_runtime_claim_boundary_is_honest(self):
        lowered = self.all_content.lower()
        for placeholder in ("todo", "tbd", "placeholder"):
            self.assertNotIn(placeholder, lowered)
        for phrase in (
            "rotation direction",
            "conjugate symmetry",
            "upper and lower rf sides",
            "limiting cases",
            "radar connection",
            "common interpretation mistakes",
        ):
            self.assertIn(phrase, self.lesson.lower())
        for heading in (
            "## Baseline",
            "## Downconversion comparison",
            "## Sweep 1",
            "## Sweep 2",
            "## Broken case",
            "## Completion handoff",
        ):
            self.assertIn(heading, self.walkthrough)
        self.assertIn("## Teach-back completion", self.checks)
        self.assertIn("P17", self.lesson)
        self.assertIn("P17", self.walkthrough)
        self.assertTrue(EVIDENCE.is_file())
        evidence = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("does **not** claim MATLAB or Octave execution", evidence)
        self.assertIn("Acceptance mapping", evidence)
        self.assertIn("Residual risks and unperformed validation", evidence)

    def test_no_unexplained_black_box_and_base_matlab_compatibility(self):
        lowered = self.experiment.lower()
        for opaque in (
            "hilbert(", "lowpass(", "fir1(", "designfilt(", "filter(",
            "downconvert(", "demod(", "comm.", "dsp.", "pwelch(",
            "spectrogram(", "periodogram(",
        ):
            self.assertNotIn(opaque, lowered)
        for unsafe in (
            "input(", "pause(", "while ", "timer(", "parfor ", "parfeval(",
            "fopen(", "webread(", "audioplayer(", "sound(", "system(",
            "close all", "clear all", "clearvars",
        ):
            self.assertNotIn(unsafe, lowered)
        self.assertNotRegex(lowered, r"\b(?:read|write)(?:matrix|table)\s*\(")

    def test_timeout_cancellation_isolation_recovery_and_rollback_contracts(self):
        self.assertEqual(self.experiment.count("for case_index ="), 2)
        self.assertEqual(self.experiment.count("for tap_index ="), 1)
        self.assertNotIn("while ", self.experiment.lower())
        self.assertIn("Ctrl+C", self.experiment)
        self.assertIn("Ctrl+C", self.walkthrough)
        self.assertIn("private seed", self.walkthrough)
        self.assertIn("global random stream", self.walkthrough)
        self.assertIn("P18-tagged figures", self.walkthrough)
        self.assertIn("partial P18 figure set", self.experiment)
        self.assertIn("empty/incomplete `results`", self.walkthrough)
        self.assertIn("rerun from the top to recover", self.walkthrough)
        self.assertIn("Rollback", self.walkthrough)
        self.assertIn("restores only P18's manifest", self.walkthrough)
        self.assertIn("Preserve implemented P17", self.walkthrough)


if __name__ == "__main__":
    unittest.main()
