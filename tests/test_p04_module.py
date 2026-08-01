from __future__ import annotations

import copy
import cmath
import json
import math
import random
import re
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "04-quantize-a-signal-and-hear-see-the-error"
MANIFEST_PATH = ROOT / "curriculum" / "modules.json"
REQUIRED_ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
GUIDING_QUESTION = "How do ADC bit depth and full-scale range change the measurement?"


def validate_p04_contract(module_dir: Path, manifest: dict) -> list[str]:
    """Return deterministic P04 contract failures for positive and negative tests."""
    errors: list[str] = []
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return ["manifest modules must be a list"]
    if any(not isinstance(entry, dict) for entry in modules):
        return ["manifest module entries must be objects"]

    matches = [entry for entry in modules if entry.get("id") == "P04"]
    if len(matches) != 1:
        return [f"expected one P04 manifest entry, found {len(matches)}"]

    entry = matches[0]
    expected_identity = {
        "number": 4,
        "title": "Quantize a Signal and Hear/See the Error",
        "phase": 1,
        "phase_title": "Signals, Sampling, and Systems",
        "slug": "quantize-a-signal-and-hear-see-the-error",
        "guiding_question": GUIDING_QUESTION,
        "folder": "modules/04-quantize-a-signal-and-hear-see-the-error",
        "status": "implemented",
        "implementation_batch": "P04",
    }
    for field, expected in expected_identity.items():
        if entry.get(field) != expected:
            errors.append(f"P04 {field} must be {expected!r}")

    for name in REQUIRED_ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P04 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P04 empty {name}")
    return errors


def quantize_midrise(values: list[float], bits: int, full_scale: float) -> tuple[list[float], float, int]:
    """Independent host-language model of the documented P04 quantizer."""
    levels = 2**bits
    delta = 2 * full_scale / levels
    output: list[float] = []
    clipped = 0
    for value in values:
        clipped += int(value < -full_scale or value > full_scale)
        limited = min(max(value, -full_scale), full_scale)
        code = math.floor((limited + full_scale) / delta)
        code = min(max(code, 0), levels - 1)
        output.append(-full_scale + (code + 0.5) * delta)
    return output, delta, clipped


def root_mean_square(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values))


class P04ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.experiment = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        cls.root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        cls.module_index = (ROOT / "modules" / "README.md").read_text(encoding="utf-8")

    def scalar_assignment(self, name: str) -> float:
        match = re.search(
            rf"(?m)^{re.escape(name)}\s*=\s*([0-9.]+)\s*;",
            self.experiment,
        )
        self.assertIsNotNone(match, f"missing visible scalar assignment for {name}")
        return float(match.group(1))

    def baseline(self) -> tuple[list[float], float, float, float, float, int]:
        amplitude = self.scalar_assignment("A")
        frequency_hz = self.scalar_assignment("f0")
        sample_rate_hz = self.scalar_assignment("fs")
        duration_s = self.scalar_assignment("duration")
        phase_rad = math.pi / 7
        sample_count = round(duration_s * sample_rate_hz)
        values = [
            amplitude
            * math.cos(2 * math.pi * frequency_hz * index / sample_rate_hz + phase_rad)
            for index in range(sample_count)
        ]
        return values, amplitude, frequency_hz, sample_rate_hz, duration_s, sample_count

    def test_artifact_completeness_manifest_identity_and_catalogs(self):
        self.assertEqual(validate_p04_contract(MODULE, self.manifest), [])
        for artifact in (self.readme, self.lesson, self.walkthrough, self.checks):
            self.assertIn(GUIDING_QUESTION, artifact)
        self.assertIn("Project 4 is now implemented as the latest lesson", self.root_readme)
        self.assertIn("Project 4 is the next lesson after P03", self.start_here)
        self.assertRegex(
            self.module_index,
            r"\| \[P04\].*\| implemented \| 1 \| Quantize a Signal and Hear/See the Error \|",
        )

    def test_contract_validator_rejects_missing_duplicate_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied_module = Path(temporary) / MODULE.name
            shutil.copytree(MODULE, copied_module)
            (copied_module / "checks.md").unlink()
            self.assertIn(
                "P04 missing checks.md",
                validate_p04_contract(copied_module, self.manifest),
            )

        malformed_manifest = copy.deepcopy(self.manifest)
        malformed_manifest["modules"][3]["guiding_question"] = "placeholder"
        malformed_manifest["modules"][3]["slug"] = "wrong-module"
        malformed_manifest["modules"][3]["status"] = "scaffolded"
        errors = validate_p04_contract(MODULE, malformed_manifest)
        self.assertIn(f"P04 guiding_question must be {GUIDING_QUESTION!r}", errors)
        self.assertIn("P04 slug must be 'quantize-a-signal-and-hear-see-the-error'", errors)
        self.assertIn("P04 status must be 'implemented'", errors)

        duplicate_manifest = copy.deepcopy(self.manifest)
        duplicate_manifest["modules"].append(copy.deepcopy(duplicate_manifest["modules"][3]))
        self.assertEqual(
            validate_p04_contract(MODULE, duplicate_manifest),
            ["expected one P04 manifest entry, found 2"],
        )
        self.assertEqual(
            validate_p04_contract(MODULE, {"modules": "not-a-list"}),
            ["manifest modules must be a list"],
        )
        self.assertEqual(
            validate_p04_contract(MODULE, {"modules": ["not-an-object"]}),
            ["manifest module entries must be objects"],
        )

    def test_explicit_midrise_operation_endpoints_and_saturation(self):
        for expression in (
            "level_count = 2^bits_baseline;",
            "delta = 2*full_scale/level_count;",
            "x_limited = min(max(x, -full_scale), full_scale);",
            "code = floor((x_limited + full_scale)/delta);",
            "code = min(max(code, 0), level_count-1);",
            "x_quantized = -full_scale + (code+0.5)*delta;",
            "quantization_error = x_quantized-x;",
        ):
            self.assertIn(expression, self.experiment)

        inputs = [-1.2, -1.0, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1.0, 1.2]
        quantized, delta, clipped = quantize_midrise(inputs, bits=3, full_scale=1.0)
        self.assertEqual(delta, 0.25)
        self.assertEqual(clipped, 2)
        self.assertEqual(
            quantized,
            [-0.875, -0.875, -0.625, -0.375, -0.125, 0.125, 0.375, 0.625, 0.875, 0.875, 0.875],
        )
        self.assertTrue(all(-0.875 <= value <= 0.875 for value in quantized))

    def test_deterministic_coherent_baseline_and_error_bound(self):
        values, amplitude, frequency_hz, sample_rate_hz, duration_s, sample_count = self.baseline()
        bits = int(self.scalar_assignment("bits_baseline"))
        full_scale = self.scalar_assignment("full_scale")
        quantized, delta, clipped = quantize_midrise(values, bits, full_scale)
        errors = [measured - original for measured, original in zip(quantized, values)]

        self.assertRegex(self.experiment, r"random_seed\s*=\s*404\s*;")
        self.assertIn("rng(random_seed, 'twister')", self.experiment)
        self.assertEqual((frequency_hz, sample_rate_hz, duration_s, sample_count), (128, 4096, 0.25, 1024))
        self.assertEqual(frequency_hz * duration_s, 32)
        self.assertEqual(sample_count % 2, 0)
        self.assertLess(amplitude, full_scale)
        self.assertEqual(clipped, 0)
        self.assertEqual(delta, 0.03125)
        self.assertLessEqual(max(abs(error) for error in errors), delta / 2 + 1e-15)
        self.assertAlmostEqual(root_mean_square(errors), 0.008998690827526655, places=14)

    def test_bit_depth_sweep_halves_steps_and_reduces_error(self):
        for marker in (
            "Parameter sweep 1 - change only ADC bit depth",
            "bit_depths = [3 6 10 14]",
            "all(diff(bit_steps_v) < 0)",
            "all(diff(bit_error_rms_v) < 0)",
            "Measured signal/error ratio (dB)",
        ):
            self.assertIn(marker, self.experiment)

        values, *_ = self.baseline()
        full_scale = self.scalar_assignment("full_scale")
        steps: list[float] = []
        error_rms: list[float] = []
        for bits in (3, 6, 10, 14):
            quantized, delta, clipped = quantize_midrise(values, bits, full_scale)
            steps.append(delta)
            error_rms.append(root_mean_square([a - b for a, b in zip(quantized, values)]))
            self.assertEqual(clipped, 0)
        self.assertEqual(steps, [0.25, 0.03125, 0.001953125, 0.0001220703125])
        self.assertTrue(all(a > b for a, b in zip(error_rms, error_rms[1:])))
        self.assertEqual(
            [round(value, 12) for value in error_rms],
            [0.062634780746, 0.008998690828, 0.000685940906, 0.000036551938],
        )

    def test_full_scale_utilization_sweep_separates_waste_from_clipping(self):
        for marker in (
            "Parameter sweep 2 - change only the ADC full-scale range",
            "utilization_fractions = [0.90 0.25 0.10]",
            "full_scale_settings = A./utilization_fractions;",
            "utilization_bits = 8;",
            "utilization_steps_v",
            "utilization_clip_count",
            "20*log10(utilization_fractions(1)/utilization_fractions(end))",
            "utilization_snr_loss_db > 15",
        ):
            self.assertIn(marker, self.experiment)

        values, amplitude, *_ = self.baseline()
        snrs: list[float] = []
        steps: list[float] = []
        error_rms: list[float] = []
        for fraction in (0.90, 0.25, 0.10):
            full_scale_case = amplitude / fraction
            quantized, delta, clipped = quantize_midrise(values, 8, full_scale_case)
            errors = [a - b for a, b in zip(quantized, values)]
            error_rms.append(root_mean_square(errors))
            snrs.append(20 * math.log10(root_mean_square(values) / error_rms[-1]))
            steps.append(delta)
            self.assertEqual(clipped, 0)
        self.assertEqual(steps, [0.0078125, 0.028125, 0.0703125])
        self.assertTrue(all(a < b for a, b in zip(error_rms, error_rms[1:])))
        self.assertEqual(
            [round(value, 12) for value in error_rms],
            [0.002616949791, 0.008457781914, 0.01702053573],
        )
        self.assertGreater(snrs[0] - snrs[-1], 15)
        self.assertAlmostEqual(snrs[0] - snrs[-1], 16.26355670675344, places=10)
        self.assertAlmostEqual(20 * math.log10(0.9 / 0.1), 19.084850188786497)

    def test_full_scale_sweep_reuses_the_same_signal_samples(self):
        """Guard the canonical experiment against substituting an amplitude sweep."""
        self.assertIn("clipped_case = x < -full_scale_case | x > full_scale_case;", self.experiment)
        self.assertIn("error_case = xq_case-x;", self.experiment)
        self.assertIn("plot(t(view), x(view)", self.experiment)
        self.assertNotIn("x_case = utilization_case*full_scale", self.experiment)

        values, amplitude, frequency_hz, sample_rate_hz, _, sample_count = self.baseline()
        phase_rad = math.pi / 7
        same_signal_error_rms: list[float] = []
        amplitude_sweep_error_rms: list[float] = []
        for fraction in (0.90, 0.25, 0.10):
            full_scale_case = amplitude / fraction
            same_output, _, _ = quantize_midrise(values, 8, full_scale_case)
            same_signal_error_rms.append(
                root_mean_square([measured - original for measured, original in zip(same_output, values)])
            )

            changed_values = [
                fraction
                * math.cos(2 * math.pi * frequency_hz * index / sample_rate_hz + phase_rad)
                for index in range(sample_count)
            ]
            changed_output, _, _ = quantize_midrise(changed_values, 8, 1.0)
            amplitude_sweep_error_rms.append(
                root_mean_square(
                    [measured - original for measured, original in zip(changed_output, changed_values)]
                )
            )

        self.assertEqual(
            [round(value, 12) for value in same_signal_error_rms],
            [0.002616949791, 0.008457781914, 0.01702053573],
        )
        self.assertNotEqual(
            [round(value, 12) for value in same_signal_error_rms[1:]],
            [round(value, 12) for value in amplitude_sweep_error_rms[1:]],
        )

    def test_dither_is_seeded_prequantizer_and_repeatable(self):
        for marker in (
            "Optional dither - add seeded TPDF dither before quantization",
            "dither = delta*(rand(size(x))-rand(size(x)));",
            "x_with_dither = x+dither;",
            "dither_code = floor((x_dither_limited + full_scale)/delta);",
            "dither_total_error = x_quantized_dither-x;",
            "Dither spreads error energy instead of promising lower RMS error",
        ):
            self.assertIn(marker, self.experiment)

        def seeded_tpdf(seed: int, count: int, delta: float) -> list[float]:
            generator = random.Random(seed)
            return [delta * (generator.random() - generator.random()) for _ in range(count)]

        first = seeded_tpdf(404, 1024, 0.03125)
        second = seeded_tpdf(404, 1024, 0.03125)
        changed = seeded_tpdf(405, 1024, 0.03125)
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)
        self.assertTrue(all(-0.03125 <= value <= 0.03125 for value in first))
        self.assertGreater(root_mean_square(first), 0)

        values, *_ = self.baseline()
        baseline_quantized, _, _ = quantize_midrise(values, 6, 1.0)
        dithered_quantized, _, dithered_clips = quantize_midrise(
            [value + noise for value, noise in zip(values, first)],
            6,
            1.0,
        )
        baseline_error = [measured - value for measured, value in zip(baseline_quantized, values)]
        dithered_error = [measured - value for measured, value in zip(dithered_quantized, values)]

        def correlation(left: list[float], right: list[float]) -> float:
            left_mean = sum(left) / len(left)
            right_mean = sum(right) / len(right)
            left_centered = [value - left_mean for value in left]
            right_centered = [value - right_mean for value in right]
            return sum(a * b for a, b in zip(left_centered, right_centered)) / math.sqrt(
                sum(value * value for value in left_centered)
                * sum(value * value for value in right_centered)
            )

        def one_sided_dft_magnitudes(signal: list[float]) -> list[float]:
            count = len(signal)
            return [
                abs(
                    sum(
                        value * cmath.exp(-2j * math.pi * bin_index * index / count)
                        for index, value in enumerate(signal)
                    )
                )
                / count
                for bin_index in range(count // 2 + 1)
            ]

        baseline_correlation = correlation(values, baseline_error)
        dithered_correlation = correlation(values, dithered_error)
        baseline_spectrum = one_sided_dft_magnitudes(baseline_error)
        dithered_spectrum = one_sided_dft_magnitudes(dithered_error)
        baseline_spread_bins = sum(
            magnitude > 0.1 * max(baseline_spectrum) for magnitude in baseline_spectrum
        )
        dithered_spread_bins = sum(
            magnitude > 0.1 * max(dithered_spectrum) for magnitude in dithered_spectrum
        )

        self.assertEqual(dithered_clips, 0)
        self.assertGreater(root_mean_square(dithered_error), root_mean_square(baseline_error))
        self.assertLess(abs(dithered_correlation), abs(baseline_correlation))
        self.assertLess(max(dithered_spectrum), max(baseline_spectrum))
        self.assertGreater(dithered_spread_bins, baseline_spread_bins)
        self.assertAlmostEqual(dithered_correlation, -0.021164965542981813)
        self.assertEqual((baseline_spread_bins, dithered_spread_bins), (8, 465))

    def test_broken_clipping_case_is_worse_and_recovery_is_explicit(self):
        for marker in (
            "Deliberately broken case - choose too little range and clip",
            "overload_amplitude = 1.35",
            "overload_clipped = x_overload < -full_scale | x_overload > full_scale;",
            "overload_clip_count > 0",
            "overload_error_rms > max(utilization_error_rms_v)",
            "Clipping error exceeds the half-LSB quantization bound",
        ):
            self.assertIn(marker, self.experiment)

        _, _, frequency_hz, sample_rate_hz, _, sample_count = self.baseline()
        phase_rad = math.pi / 7
        values = [
            1.35 * math.cos(2 * math.pi * frequency_hz * index / sample_rate_hz + phase_rad)
            for index in range(sample_count)
        ]
        quantized, delta, clipped = quantize_midrise(values, 8, 1.0)
        errors = [a - b for a, b in zip(quantized, values)]
        self.assertEqual(delta, 0.0078125)
        self.assertEqual(clipped, 512)
        self.assertAlmostEqual(root_mean_square(errors), 0.1762850725533559)
        self.assertGreater(max(abs(error) for error in errors), delta / 2)
        self.assertIn("Restore `A = 0.9`, `f0 = 128`", self.walkthrough)
        self.assertIn("reducing front-end gain or\nincreasing the ADC range", self.walkthrough)

    def test_spectrum_scaling_labels_metrics_and_audio_boundary_are_explicit(self):
        for expression in (
            "E[k] = sum_n e[n]*exp(-j*2*pi*k*n/N)",
            "error_fft = fft(quantization_error);",
            "frequency_hz = one_sided_bins*fs/sample_count;",
            "error_magnitude = abs(error_fft(1:sample_count/2+1))/sample_count;",
            "error_magnitude(2:end-1) = 2*error_magnitude(2:end-1);",
            "error_dbfs = 20*log10(max(error_magnitude/full_scale, spectrum_floor));",
            "audio_preview",
            "audio_error_preview",
        ):
            self.assertIn(expression, self.experiment)
        for label in (
            "Time (s)",
            "Voltage (V)",
            "Sample index n (samples)",
            "Frequency (Hz)",
            "Error magnitude (dBFS)",
            "Error (V RMS)",
            "ADC bit depth (bits)",
            "Input peak / ADC full scale (%)",
            "clipped samples",
        ):
            self.assertIn(label, self.experiment)

        _, _, _, sample_rate_hz, _, sample_count = self.baseline()
        frequencies = [index * sample_rate_hz / sample_count for index in range(sample_count // 2 + 1)]
        self.assertEqual(len(frequencies), 513)
        self.assertEqual((frequencies[0], frequencies[-1]), (0, sample_rate_hz / 2))
        self.assertIsNone(re.search(r"(?m)^\s*soundsc\(", self.experiment))
        self.assertIn("no audio device is required", self.experiment)

    def test_concept_first_documentation_and_completion_rubric(self):
        combined_docs = "\n".join((self.lesson, self.walkthrough, self.checks))
        for concept in (
            "mid-rise",
            "half an LSB",
            "full-scale utilization",
            "clipping",
            "signal-dependent",
            "dither",
            "dBFS",
            "dynamic-range",
            "weak target",
            "base MATLAB",
        ):
            self.assertIn(concept.lower(), combined_docs.lower())
        for limiting_case in (
            "One more bit",
            "Signal near zero",
            "Exactly at an input endpoint",
            "Very small signal",
            "More bits during overload",
            "Dithered signal",
        ):
            self.assertIn(limiting_case, self.lesson)
        for section in (
            "## Baseline",
            "## Sweep 1",
            "## Sweep 2",
            "## Optional dither comparison",
            "## Broken case",
            "## Recovery",
        ):
            self.assertIn(section, self.walkthrough)
        self.assertIn("## Predict, then verify", self.checks)
        self.assertIn("## Failure classification", self.checks)
        self.assertIn("## Teach-back completion", self.checks)
        self.assertIn("distinguish quantization noise,\nclipping, and poor full-scale utilization", self.walkthrough)

    def test_no_placeholder_or_unexplained_black_box_regression(self):
        implementation_text = "\n".join((self.experiment, self.lesson, self.walkthrough, self.checks))
        self.assertIsNone(
            re.search(r"\b(TODO|TBD|FIXME|lorem ipsum|coming soon)\b", implementation_text, re.I)
        )
        for prohibited_call in (
            "quantiz(",
            "awgn(",
            "periodogram(",
            "pwelch(",
            "audioread(",
            "phased.",
            "dsp.",
            "comm.",
            "Signal Processing Toolbox",
        ):
            self.assertNotIn(prohibited_call, implementation_text)
        self.assertIn("base MATLAB only", self.readme)
        self.assertIn("explicit arithmetic", self.readme)
        self.assertIn("no toolbox quantizer hides the operation", self.lesson)

    def test_malformed_controls_resource_bounds_and_noninteractive_compatibility(self):
        self.assertEqual(self.scalar_assignment("max_samples"), 16384)
        self.assertEqual(self.scalar_assignment("max_sweep_cases"), 8)
        self.assertEqual(self.scalar_assignment("max_bits"), 16)
        for guard in (
            "assert(sample_count <= max_samples",
            "assert(mod(sample_count, 2) == 0",
            "f0*duration-round(f0*duration)",
            "bits_baseline == floor(bits_baseline)",
            "bits_baseline >= 2 && bits_baseline <= max_bits",
            "numel(bit_depths) <= max_sweep_cases",
            "numel(utilization_fractions) <= max_sweep_cases",
            "audio_gap_sample_count <= max_samples",
            "audio_preview_sample_count <= 5*max_samples",
            "audio_error_preview_sample_count <= 3*max_samples",
            "view_sample_count = min(96, sample_count);",
        ):
            self.assertIn(guard, self.experiment)

        for control in ("A", "f0", "duration", "full_scale"):
            self.assertRegex(
                self.experiment,
                rf"(?s)assert\(isscalar\({control}\)[^;]*?isnumeric\({control}\)[^;]*?"
                rf"~islogical\({control}\)[^;]*?isreal\({control}\)[^;]*?"
                rf"isfinite\({control}\)[^;]*?{control} > 0[^;]*?;",
            )
        self.assertRegex(
            self.experiment,
            r"(?s)assert\(isscalar\(fs\)[^;]*?isnumeric\(fs\)[^;]*?"
            r"~islogical\(fs\)[^;]*?isreal\(fs\)[^;]*?isfinite\(fs\)[^;]*?"
            r"fs > 2\*f0[^;]*?;",
        )
        for control in ("bits_baseline", "utilization_bits", "overload_bits"):
            self.assertRegex(
                self.experiment,
                rf"(?s)assert\(isscalar\({control}\)[^;]*?isnumeric\({control}\)[^;]*?"
                rf"~islogical\({control}\)[^;]*?isreal\({control}\)[^;]*?"
                rf"isfinite\({control}\)[^;]*?{control} == floor\({control}\)[^;]*?"
                rf"{control} >= 2[^;]*?{control} <= max_bits[^;]*?;",
            )

        def positive_finite_real_scalar(value: object) -> bool:
            return (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
                and value > 0
            )

        for malformed in (0, -1, math.nan, math.inf, 1 + 1j, True):
            with self.subTest(malformed=malformed):
                self.assertFalse(positive_finite_real_scalar(malformed))
        for valid in (0.1, 16, 4096.0):
            with self.subTest(valid=valid):
                self.assertTrue(positive_finite_real_scalar(valid))

        self.assertLessEqual(self.experiment.count("figure("), 8)
        self.assertNotRegex(self.experiment, r"(?m)^\s*(while|parfor)\b")
        for feature in (
            "pause(",
            "drawnow",
            "VideoWriter",
            "uicontrol",
            "webread",
            "tcpclient",
            "serialport",
            "audioplayer(",
        ):
            self.assertNotIn(feature, self.experiment)
        self.assertIn("for bit_index = 1:numel(bit_depths)", self.experiment)
        self.assertIn("for utilization_index = 1:numel(utilization_fractions)", self.experiment)
        self.assertIn(
            "no toolbox, helper function, external data,\n  hardware, audio device, or network access is required",
            self.readme,
        )
        gap_guard = self.experiment.index("audio_gap_sample_count <= max_samples")
        preview_guard = self.experiment.index("audio_preview_sample_count <= 5*max_samples")
        allocation = self.experiment.index("audio_gap = zeros(1, audio_gap_sample_count);")
        self.assertLess(gap_guard, allocation)
        self.assertLess(preview_guard, allocation)

    def test_timeout_cancellation_isolation_compatibility_and_recovery_scope(self):
        # P04 has no asynchronous task or stream to cancel. Its bounded finite
        # loops are the applicable timeout/cancellation contract.
        self.assertNotRegex(self.experiment, r"(?m)^\s*(timer|parfeval|batch|websocket)\b")
        self.assertEqual(len(re.findall(r"(?m)^for ", self.experiment)), 2)
        self.assertIn("finite bounded loops", self.lesson)
        self.assertIn("stop it with Ctrl+C if your\nMATLAB environment blocks", self.walkthrough)
        self.assertIn("do not require an audio device", self.readme)
        self.assertNotIn(".learning", self.experiment)
        self.assertNotIn("delete(", self.experiment)
        self.assertIn("digital gain after quantization cannot recreate discarded detail", self.walkthrough)


if __name__ == "__main__":
    unittest.main()
