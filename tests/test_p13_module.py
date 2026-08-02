from __future__ import annotations

import cmath
import copy
import json
import math
import random
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/13-prove-zero-padding-does-not-improve-true-resolution"
EVIDENCE = ROOT / "docs/evidence/P13-2026-08-01.md"
QUESTION = "Why does a smoother FFT plot not necessarily contain more information?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def is_finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p13_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P13 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P13 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    entries = [
        entry
        for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P13"
    ]
    if len(entries) != 1:
        return errors + [f"expected one P13 manifest entry, found {len(entries)}"]

    expected = {
        "number": 13,
        "id": "P13",
        "title": "Prove Zero-Padding Does Not Improve True Resolution",
        "guiding_question": QUESTION,
        "phase": 2,
        "phase_title": "Fourier, Spectral, and I/Q Intuition",
        "slug": "prove-zero-padding-does-not-improve-true-resolution",
        "folder": "modules/13-prove-zero-padding-does-not-improve-true-resolution",
        "status": "implemented",
        "implementation_batch": "P13",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P13 {key} must be {value!r}")
    return errors


def validate_resolution_inputs(
    fs_hz: float = 1024.0,
    short_sample_count: int = 128,
    long_multiplier: int = 4,
    tone_center_hz: float = 200.0,
    tone_separation_hz: float = 4.0,
    padding_factors: tuple[int, ...] = (1, 4, 16),
    amplitude_v: float = 1.0,
    phases_rad: tuple[float, float] = (0.0, 0.0),
    noise_rms_v: float = 0.002,
    comparison_fft_count: int = 8192,
    probe_frequency_hz: float = 201.5,
) -> None:
    if not is_finite_real(fs_hz) or fs_hz <= 0:
        raise ValueError("sample rate must be finite and positive")
    if isinstance(short_sample_count, bool) or not isinstance(short_sample_count, int):
        raise ValueError("sample count must be an integer")
    if short_sample_count < 32 or short_sample_count > 512 or short_sample_count % 2:
        raise ValueError("sample count must be even and bounded")
    if isinstance(long_multiplier, bool) or not isinstance(long_multiplier, int):
        raise ValueError("long multiplier must be an integer")
    if long_multiplier < 2 or short_sample_count * long_multiplier > 512:
        raise ValueError("long record exceeds the sample bound")
    if padding_factors != (1, 4, 16):
        raise ValueError("padding factors must be the canonical unique sweep")
    if not is_finite_real(amplitude_v) or amplitude_v <= 0:
        raise ValueError("amplitude must be finite and positive")
    if (
        not isinstance(phases_rad, tuple)
        or len(phases_rad) != 2
        or any(not is_finite_real(value) for value in phases_rad)
    ):
        raise ValueError("phases must contain two finite real values")
    if (
        not is_finite_real(noise_rms_v)
        or not 0 <= noise_rms_v <= 0.02 * amplitude_v
    ):
        raise ValueError("noise RMS must be finite, nonnegative, and bounded")
    if not is_finite_real(tone_center_hz) or not is_finite_real(tone_separation_hz):
        raise ValueError("tone controls must be finite")
    if tone_separation_hz <= 0:
        raise ValueError("tone separation must be positive")
    tones = (tone_center_hz - tone_separation_hz / 2,
             tone_center_hz + tone_separation_hz / 2)
    if not all(0 < tone < fs_hz / 2 for tone in tones):
        raise ValueError("tones must lie between DC and Nyquist")
    short_rayleigh = fs_hz / short_sample_count
    long_rayleigh = fs_hz / (short_sample_count * long_multiplier)
    if not long_rayleigh < tone_separation_hz < short_rayleigh:
        raise ValueError("tone pair must cross the short/long resolution boundary")
    if short_sample_count * max(padding_factors) > 8192:
        raise ValueError("padded FFT exceeds the resource bound")
    if (
        isinstance(comparison_fft_count, bool)
        or not isinstance(comparison_fft_count, int)
        or comparison_fft_count < short_sample_count
        or comparison_fft_count > 8192
    ):
        raise ValueError("comparison FFT must be an integer and bounded")
    record_counts = tuple(short_sample_count * factor for factor in (1, 2, 4))
    padded_counts = tuple(short_sample_count * factor for factor in padding_factors)
    if any(comparison_fft_count % count for count in record_counts + padded_counts):
        raise ValueError("comparison grid must refine every record grid")
    if (
        not is_finite_real(probe_frequency_hz)
        or not 0 < probe_frequency_hz < fs_hz / 2
    ):
        raise ValueError("probe must be finite and inside Nyquist")
    dense_spacing = fs_hz / padded_counts[-1]
    if not math.isclose(
        probe_frequency_hz / dense_spacing,
        round(probe_frequency_hz / dense_spacing),
        rel_tol=0.0,
        abs_tol=1e-10,
    ):
        raise ValueError("probe must align with the densest padding grid")


def complex_two_tone_samples(
    sample_count: int,
    fs_hz: float = 1024.0,
    frequencies_hz: tuple[float, float] = (198.0, 202.0),
) -> list[complex]:
    return [
        cmath.exp(2j * math.pi * frequencies_hz[0] * n / fs_hz)
        + cmath.exp(2j * math.pi * frequencies_hz[1] * n / fs_hz)
        for n in range(sample_count)
    ]


def finite_projection(samples: list[complex], fs_hz: float, frequency_hz: float) -> complex:
    return sum(
        sample * cmath.exp(-2j * math.pi * frequency_hz * n / fs_hz)
        for n, sample in enumerate(samples)
    ) / len(samples)


def direct_dft(samples: list[complex], fft_count: int) -> list[complex]:
    if fft_count < len(samples):
        raise ValueError("FFT count cannot discard measured samples")
    return [
        sum(
            sample * cmath.exp(-2j * math.pi * k * n / fft_count)
            for n, sample in enumerate(samples)
        ) / len(samples)
        for k in range(fft_count)
    ]


def midpoint_to_tone_level_db(sample_count: int) -> float:
    samples = complex_two_tone_samples(sample_count)
    left = abs(finite_projection(samples, 1024.0, 198.0))
    middle = abs(finite_projection(samples, 1024.0, 200.0))
    right = abs(finite_projection(samples, 1024.0, 202.0))
    return 20 * math.log10(max(middle / math.sqrt(left * right), 1e-15))


def dominant_peak_count(sample_count: int) -> int:
    samples = complex_two_tone_samples(sample_count)
    frequencies = [190.0 + 0.125 * index for index in range(161)]
    magnitudes = [
        abs(finite_projection(samples, 1024.0, frequency))
        for frequency in frequencies
    ]
    threshold = 0.5 * max(magnitudes)
    return sum(
        magnitudes[index] > magnitudes[index - 1]
        and magnitudes[index] >= magnitudes[index + 1]
        and magnitudes[index] >= threshold
        for index in range(1, len(magnitudes) - 1)
    )


def noisy_resolution_metrics(seed: int) -> tuple[float, float, int, int]:
    """Independently model the default shared-prefix noise behavior."""
    rng = random.Random(seed)
    raw_noise = [
        complex(rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0)) / math.sqrt(2.0)
        for _ in range(512)
    ]
    raw_rms = math.sqrt(sum(abs(value) ** 2 for value in raw_noise) / 512)
    noise = [0.002 * value / raw_rms for value in raw_noise]
    clean = complex_two_tone_samples(512)
    longest = [signal + perturbation for signal, perturbation in zip(clean, noise)]

    def metrics(samples: list[complex]) -> tuple[float, int]:
        left = abs(finite_projection(samples, 1024.0, 198.0))
        middle = abs(finite_projection(samples, 1024.0, 200.0))
        right = abs(finite_projection(samples, 1024.0, 202.0))
        midpoint_db = 20 * math.log10(
            max(middle / math.sqrt(left * right), 1e-15)
        )
        frequencies = [190.0 + 0.125 * index for index in range(161)]
        magnitudes = [
            abs(finite_projection(samples, 1024.0, frequency))
            for frequency in frequencies
        ]
        threshold = 0.5 * max(magnitudes)
        peaks = sum(
            magnitudes[index] > magnitudes[index - 1]
            and magnitudes[index] >= magnitudes[index + 1]
            and magnitudes[index] >= threshold
            for index in range(1, len(magnitudes) - 1)
        )
        return midpoint_db, peaks

    short_midpoint_db, short_peaks = metrics(longest[:128])
    long_midpoint_db, long_peaks = metrics(longest)
    return short_midpoint_db, long_midpoint_db, short_peaks, long_peaks


class P13ModuleTests(unittest.TestCase):
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
        self.assertEqual(validate_p13_contract(MODULE, self.manifest), [])
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
            errors = validate_p13_contract(fixture, self.manifest)
            self.assertIn("P13 missing checks.md", errors)
            self.assertIn("P13 empty lesson.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][12]))
        self.assertIn(
            "expected one P13 manifest entry, found 2",
            validate_p13_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p13_contract(MODULE, {"modules": "P13"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][12]["guiding_question"] = "generic question"
        malformed["modules"][12]["status"] = "scaffolded"
        errors = validate_p13_contract(MODULE, malformed)
        self.assertIn(f"P13 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P13 status must be 'implemented'", errors)

    def test_manifest_catalogs_and_p12_dependency_preserve_p13(self):
        modules_by_id = {module["id"]: module for module in self.manifest["modules"]}
        self.assertEqual(modules_by_id["P11"]["status"], "implemented")
        self.assertEqual(modules_by_id["P12"]["status"], "implemented")
        self.assertEqual(modules_by_id["P13"]["status"], "implemented")
        self.assertRegex(self.module_index, r"\| \[P13\].*\| implemented \|")
        self.assertIn("Project 13 proves that zero-padding", self.root_readme)
        self.assertIn("Project 13 follows P12", self.start_here)
        self.assertIn("Learning dependencies: P11", self.readme)
        self.assertIn("P12 supplies", self.readme)

    def test_deterministic_private_seed_and_visible_controls(self):
        for marker in (
            "random_seed = 1013;",
            "fs_hz = 1024;",
            "short_sample_count = 128;",
            "long_observation_multiplier = 4;",
            "tone_center_hz = 200;",
            "tone_separation_hz = 4;",
            "tone_amplitude_v = 1.0;",
            "tone_phase_rad = [0 0];",
            "noise_rms_v = 0.002;",
            "padding_factors = [1 4 16];",
            "observation_multiplier_sweep = [1 2 4];",
            "comparison_fft_count = 8192;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "randn(stream, 1, long_sample_count)",
            "complex_noise_v = noise_rms_v*raw_complex_noise_v/",
            "sqrt(mean(abs(raw_complex_noise_v).^2));",
            "rectangular_window = ones(1, long_sample_count);",
            "(tone_1_v + tone_2_v + complex_noise_v).*rectangular_window",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_zero_padding_preserves_original_dft_values_independently(self):
        samples = complex_two_tone_samples(128)
        base = direct_dft(samples, 128)
        for factor in (1, 4, 16):
            padded = direct_dft(samples, 128 * factor)
            recovered = padded[::factor]
            self.assertEqual(len(recovered), len(base))
            self.assertLess(max(abs(a - b) for a, b in zip(base, recovered)), 1e-12)
        for marker in (
            "sweep_projection_v = fft(short_record_v, sweep_fft_count)/short_sample_count;",
            "original_grid_projection_v = sweep_projection_v(1:padding_factor:end);",
            "original_grid_projection_v - base_projection_v",
            "Zero-padding must preserve every original N-point DFT value.",
        ):
            self.assertIn(marker, self.experiment)

    def test_explicit_finite_sum_matches_dense_grid_projection(self):
        samples = complex_two_tone_samples(128)
        explicit = finite_projection(samples, 1024.0, 201.5)
        dense = direct_dft(samples, 2048)
        dense_index = round(201.5 / (1024.0 / 2048))
        self.assertLess(abs(explicit - dense[dense_index]), 1e-12)
        for marker in (
            "explicit_probe_v = sum(short_record_v.*exp(",
            "-1j*2*pi*probe_frequency_hz*short_time_s))/short_sample_count;",
            "explicit_probe_error_v = abs(explicit_probe_v - dense_probe_v);",
        ):
            self.assertIn(marker, self.experiment)

    def test_padding_sweep_changes_only_display_grid(self):
        self.assertEqual([1024 / (128 * factor) for factor in (1, 4, 16)], [8, 2, 0.5])
        self.assertEqual([1024 / 128] * 3, [8, 8, 8])
        self.assertEqual([2 * 1024 / 128] * 3, [16, 16, 16])
        section = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        self.assertIn("padding_factor = padding_factors(sweep_index);", section)
        self.assertIn("fft(short_record_v, sweep_fft_count)", section)
        for forbidden_assignment in (
            "fs_hz =",
            "short_sample_count =",
            "short_record_v =",
            "tone_frequency_hz =",
            "noise_rms_v =",
        ):
            self.assertNotIn(forbidden_assignment, section)

    def test_longer_observation_improves_resolution_independently(self):
        self.assertEqual([1024 / count for count in (128, 256, 512)], [8, 4, 2])
        self.assertEqual([4 / value for value in (8, 4, 2)], [0.5, 1, 2])
        self.assertGreater(midpoint_to_tone_level_db(128), 0)
        self.assertLess(midpoint_to_tone_level_db(512), -200)
        self.assertEqual(dominant_peak_count(128), 1)
        self.assertEqual(dominant_peak_count(512), 2)
        self.assertIn("midpoint_to_tone_level_db(1) > 0", self.experiment)
        self.assertIn("midpoint_to_tone_level_db(end) < -20", self.experiment)
        self.assertIn("dominant_peak_count(1) == 1", self.experiment)
        self.assertIn("dominant_peak_count(end) == 2", self.experiment)

    def test_observation_sweep_uses_shared_prefix_and_one_physical_change(self):
        section = self.experiment.split("%% Sweep 2", 1)[1].split("%% Broken case", 1)[0]
        self.assertIn("sweep_sample_count = observation_sample_count(sweep_index);", section)
        self.assertIn("sweep_record_v = long_record_v(1:sweep_sample_count);", section)
        self.assertIn("fft(sweep_record_v, comparison_fft_count)", section)
        for forbidden_assignment in (
            "fs_hz =",
            "tone_frequency_hz =",
            "tone_amplitude_v =",
            "tone_phase_rad =",
            "comparison_fft_count =",
            "long_record_v =",
        ):
            self.assertNotIn(forbidden_assignment, section)

    def test_observation_peak_search_uses_an_elementwise_frequency_mask(self):
        frequencies = [index * 1024.0 / 8192 for index in range(8192)]
        selected = [frequency for frequency in frequencies if 190 <= frequency <= 210]
        self.assertEqual(selected[0], 190)
        self.assertEqual(selected[-1], 210)
        self.assertEqual(len(selected), 161)

        section = self.experiment.split("%% Sweep 2", 1)[1].split(
            "%% Broken case", 1
        )[0]
        self.assertIn(
            "search_mask = (comparison_frequency_axis_hz >= ...",
            section,
        )
        self.assertIn(
            "tone_frequency_hz(1) - short_rayleigh_hz) & ...",
            section,
        )
        self.assertIn(
            "(comparison_frequency_axis_hz <= ...",
            section,
        )
        self.assertNotIn("short_rayleigh_hz &&", section)

    def test_default_noise_preserves_short_blend_and_long_separation_behavior(self):
        for seed in range(100):
            with self.subTest(seed=seed):
                short_midpoint_db, long_midpoint_db, short_peaks, long_peaks = (
                    noisy_resolution_metrics(seed)
                )
                self.assertGreater(short_midpoint_db, 0)
                self.assertLess(long_midpoint_db, -20)
                self.assertEqual(short_peaks, 1)
                self.assertEqual(long_peaks, 2)

    def test_supported_alternate_record_length_keeps_behavior_and_truthful_labels(self):
        short_sample_count = 64
        long_sample_count = 256
        frequencies_hz = (196.0, 204.0)
        validate_resolution_inputs(
            short_sample_count=short_sample_count,
            tone_separation_hz=8.0,
            probe_frequency_hz=201.0,
        )

        def metrics(sample_count: int) -> tuple[float, int]:
            samples = complex_two_tone_samples(
                sample_count,
                frequencies_hz=frequencies_hz,
            )
            left = abs(finite_projection(samples, 1024.0, frequencies_hz[0]))
            middle = abs(finite_projection(samples, 1024.0, 200.0))
            right = abs(finite_projection(samples, 1024.0, frequencies_hz[1]))
            midpoint_db = 20 * math.log10(
                max(middle / math.sqrt(left * right), 1e-15)
            )
            search_frequencies_hz = [180.0 + 0.125 * index for index in range(321)]
            magnitudes = [
                abs(finite_projection(samples, 1024.0, frequency_hz))
                for frequency_hz in search_frequencies_hz
            ]
            threshold = 0.5 * max(magnitudes)
            peaks = sum(
                magnitudes[index] > magnitudes[index - 1]
                and magnitudes[index] >= magnitudes[index + 1]
                and magnitudes[index] >= threshold
                for index in range(1, len(magnitudes) - 1)
            )
            return midpoint_db, peaks

        short_midpoint_db, short_peaks = metrics(short_sample_count)
        long_midpoint_db, long_peaks = metrics(long_sample_count)
        self.assertGreater(short_midpoint_db, 0)
        self.assertEqual(short_peaks, 1)
        self.assertLess(long_midpoint_db, -20)
        self.assertEqual(long_peaks, 2)

        figure_section = self.experiment.split("%% Purposeful figures", 1)[1]
        for marker in (
            "short_record_title = sprintf(",
            "padding_legend{sweep_index} = sprintf(",
            "observation_legend{sweep_index} = sprintf(",
            "sprintf('True: %d samples', short_sample_count)",
            "sprintf('True: %d samples', long_sample_count)",
            "short_recovery_label = sprintf(",
            "long_recovery_label = sprintf(",
        ):
            self.assertIn(marker, figure_section)
        for stale_default_label in (
            "The same 128 nonzero measured samples",
            "1x: 8 Hz grid",
            "128 samples (0.125 s)",
            "True: 128 samples",
            "128 measured samples, dense grid",
        ):
            self.assertNotIn(stale_default_label, figure_section)

    def test_broken_grid_spacing_claim_and_recovery_are_measurable(self):
        broken_grid_hz = 1024 / 2048
        short_rayleigh_hz = 1024 / 128
        long_rayleigh_hz = 1024 / 512
        self.assertEqual(broken_grid_hz, 0.5)
        self.assertEqual(4 / broken_grid_hz, 8)
        self.assertEqual(4 / short_rayleigh_hz, 0.5)
        self.assertEqual(4 / long_rayleigh_hz, 2)
        for marker in (
            "broken_claimed_resolution_hz = padding_display_spacing_hz(end);",
            "recovered_short_resolution_hz = short_rayleigh_hz;",
            "recovered_long_resolution_hz = long_rayleigh_hz;",
            "broken grid-spacing claim must contradict",
        ):
            self.assertIn(marker, self.experiment)
        combined = "\n".join((self.lesson, self.walkthrough, self.checks))
        self.assertIn("classification", combined)
        self.assertIn("grid spacing, not true", combined)

    def test_long_rayleigh_boundary_is_rejected_before_allocation(self):
        with self.assertRaises(ValueError):
            validate_resolution_inputs(tone_separation_hz=2.0)
        self.assertIn("tone_separation_hz > long_rayleigh_hz", self.experiment)
        self.assertIn(
            "Tone separation must be below the short and above the long Rayleigh interval.",
            self.experiment,
        )

    def test_malformed_numeric_inputs_and_resource_bounds(self):
        validate_resolution_inputs()
        for sample_count in (31, 33, 514, True, 128.0):
            with self.assertRaises(ValueError):
                validate_resolution_inputs(short_sample_count=sample_count)  # type: ignore[arg-type]
        for sample_rate in (0.0, float("nan"), float("inf"), True, 1024 + 0j):
            with self.assertRaises(ValueError):
                validate_resolution_inputs(fs_hz=sample_rate)
        for multiplier in (1, 5, True, 4.0):
            with self.assertRaises(ValueError):
                validate_resolution_inputs(long_multiplier=multiplier)  # type: ignore[arg-type]
        for separation in (
            0.0, 1.0, 8.0, float("nan"), float("inf"), True, 4 + 0j
        ):
            with self.assertRaises(ValueError):
                validate_resolution_inputs(tone_separation_hz=separation)
        for factors in ((1, 16), (1, 4, 4), (1, 4, 32)):
            with self.assertRaises(ValueError):
                validate_resolution_inputs(padding_factors=factors)
        for center_hz in (511.0, True, 200 + 0j, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                validate_resolution_inputs(tone_center_hz=center_hz)
        for amplitude in (0.0, True, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                validate_resolution_inputs(amplitude_v=amplitude)
        for phases in ((0.0,), (0.0, True), (0.0, float("nan"))):
            with self.assertRaises(ValueError):
                validate_resolution_inputs(phases_rad=phases)  # type: ignore[arg-type]
        for noise_rms in (-0.1, 0.021, True, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                validate_resolution_inputs(noise_rms_v=noise_rms)
        for fft_count in (127, 2047, 16384, True, 8192.0):
            with self.assertRaises(ValueError):
                validate_resolution_inputs(comparison_fft_count=fft_count)  # type: ignore[arg-type]
        for probe_hz in (-1.0, 201.4, 512.0, True, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                validate_resolution_inputs(probe_frequency_hz=probe_hz)

        for marker in (
            "max_record_samples = 512;",
            "max_fft_count = 8192;",
            "max_padding_factor = 16;",
            "max_sweep_cases = 8;",
            "max_figure_groups = 4;",
            "max_explicit_dft_terms = 512;",
            "P13 resource ceilings must remain fixed.",
            "random_seed <= 2^32 - 1",
            "isreal(fs_hz) && ...",
            "~islogical(fs_hz)",
            "isreal(tone_center_hz)",
            "~islogical(tone_center_hz)",
            "isreal(tone_separation_hz)",
            "~islogical(tone_separation_hz)",
            "isequal(padding_factors, [1 4 16])",
            "all(diff(observation_multiplier_sweep) > 0)",
            "comparison_fft_count <= max_fft_count",
            "Tone separation must be below the short",
        ):
            self.assertIn(marker, self.experiment)

    def test_validation_precedes_signal_random_fft_and_figure_allocation(self):
        resource_guard = self.experiment.index("P13 resource ceilings must remain fixed.")
        signal_allocation = self.experiment.index("max_sample_index = 0:")
        stream_allocation = self.experiment.index("stream = RandStream")
        fft_allocation = self.experiment.index("padding_frequency_axis_hz = cell")
        figure_replacement = self.experiment.index("old_figures = findall")
        self.assertLess(resource_guard, signal_allocation)
        self.assertLess(signal_allocation, stream_allocation)
        self.assertLess(stream_allocation, fft_allocation)
        self.assertLess(fft_allocation, figure_replacement)

    def test_plots_metrics_and_units_cover_required_behavior(self):
        for figure_name in (
            "P13 same samples, denser FFT grid",
            "P13 padding sweep invariants",
            "P13 observation-time sweep",
            "P13 broken resolution claim and recovery",
        ):
            self.assertIn(figure_name, self.experiment)
        for unit_label in (
            "Measured time (ms)",
            "I/Q amplitude (V)",
            "Frequency (Hz)",
            "Finite-record magnitude (V)",
            "Frequency scale (Hz)",
            "Measured record length N (samples)",
            "Magnitude relative to each case peak (dBc)",
        ):
            self.assertIn(unit_label, self.experiment)
        for metric in (
            "results.padding_display_spacing_hz",
            "results.noise_rms_realized_v",
            "results.observation_noise_rms_realized_v",
            "results.padding_rayleigh_hz",
            "results.original_grid_error_v",
            "results.explicit_probe_error_v",
            "results.observation_rayleigh_hz",
            "results.separation_rayleigh_ratio",
            "results.midpoint_to_tone_level_db",
            "results.dominant_peak_count",
            "results.broken_claimed_resolution_hz",
            "results.recovered_long_resolution_hz",
        ):
            self.assertIn(metric, self.experiment)

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback(self):
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
        self.assertIn("'Tag', 'P13'", self.experiment)
        self.assertIn("Ctrl+C", self.walkthrough)
        self.assertIn("private seed", self.walkthrough)
        self.assertIn("shared noise prefix", self.readme)
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
            "periodogram(",
            "pwelch(",
            "spectrogram(",
            "pspectrum(",
            "findpeaks(",
            "dftmtx(",
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
            "## One finite record, many display grids",
            "## Resolution comes from observation time",
            "## Two close tones expose the distinction",
            "## Broken interpretation and recovery",
            "## Limiting cases",
            "## Radar connection and common interpretation mistakes",
        ):
            self.assertIn(heading, self.lesson)
        for heading in (
            "## Baseline: the same 128 samples on three grids",
            "## Sweep 1: change only the zero-padding factor",
            "## Sweep 2: change only measured observation length",
            "## Broken case: call display spacing true resolution",
            "## Concept connection and completion handoff",
            "## Safe rerun, cancellation, recovery, and rollback",
        ):
            self.assertIn(heading, self.walkthrough)
        for heading in (
            "## Baseline observation checks",
            "## Predict, then verify",
            "## Interpretation checks",
            "## Failure classification",
            "## Recovery, isolation, compatibility, and resource bounds",
            "## Teach-back completion",
        ):
            self.assertIn(heading, self.checks)

    def test_retained_evidence_exists_and_preserves_runtime_claim_boundary(self):
        evidence = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("does **not** claim MATLAB or Octave execution", evidence)
        self.assertIn("Static validation and MATLAB runtime evidence are separate", evidence)
        self.assertIn("P13 is **ready for deterministic review**", evidence)


if __name__ == "__main__":
    unittest.main()
