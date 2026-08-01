from __future__ import annotations

import cmath
import copy
import json
import math
import random
import re
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "05-explore-white-colored-and-impulsive-noise"
MANIFEST_PATH = ROOT / "curriculum" / "modules.json"
REQUIRED_ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
GUIDING_QUESTION = "What does the word noise hide about time behavior and spectrum?"


def validate_p05_contract(module_dir: Path, manifest: dict) -> list[str]:
    """Return deterministic P05 artifact and identity failures."""
    errors: list[str] = []
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return ["manifest modules must be a list"]
    if any(not isinstance(entry, dict) for entry in modules):
        return ["manifest module entries must be objects"]

    matches = [entry for entry in modules if entry.get("id") == "P05"]
    if len(matches) != 1:
        return [f"expected one P05 manifest entry, found {len(matches)}"]

    entry = matches[0]
    expected_identity = {
        "number": 5,
        "title": "Explore White, Colored, and Impulsive Noise",
        "phase": 1,
        "phase_title": "Signals, Sampling, and Systems",
        "slug": "explore-white-colored-and-impulsive-noise",
        "guiding_question": GUIDING_QUESTION,
        "folder": "modules/05-explore-white-colored-and-impulsive-noise",
        "status": "implemented",
        "implementation_batch": "P05",
    }
    for field, expected in expected_identity.items():
        if entry.get(field) != expected:
            errors.append(f"P05 {field} must be {expected!r}")

    for name in REQUIRED_ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P05 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P05 empty {name}")
    return errors


def root_mean_square(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values))


def center_and_normalize(values: list[float], target_rms: float) -> list[float]:
    centered = [value - sum(values) / len(values) for value in values]
    measured = root_mean_square(centered)
    if not math.isfinite(measured) or measured <= 0:
        raise ValueError("record RMS must be finite and positive")
    return [target_rms * value / measured for value in centered]


def lag_one_correlation(values: list[float]) -> float:
    return (
        sum(a * b for a, b in zip(values, values[1:])) / (len(values) - 1)
    ) / (sum(value * value for value in values) / len(values))


def one_pole(driver: list[float], alpha: float) -> list[float]:
    output = [(1 - alpha) * driver[0]]
    for value in driver[1:]:
        output.append(alpha * output[-1] + (1 - alpha) * value)
    return output


def tone_projection(values: list[float], frequency_hz: float, sample_rate_hz: float) -> complex:
    count = len(values)
    return (2 / count) * sum(
        value * cmath.exp(-2j * math.pi * frequency_hz * index / sample_rate_hz)
        for index, value in enumerate(values)
    )


def one_sided_psd(values: list[float], sample_rate_hz: float) -> list[float]:
    """Independent direct-DFT version of the documented rectangular PSD."""
    count = len(values)
    result: list[float] = []
    for bin_index in range(count // 2 + 1):
        transform = sum(
            value * cmath.exp(-2j * math.pi * bin_index * index / count)
            for index, value in enumerate(values)
        )
        density = abs(transform) ** 2 / (sample_rate_hz * count)
        if bin_index not in (0, count // 2):
            density *= 2
        result.append(density)
    return result


class P05ModuleTests(unittest.TestCase):
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

    def test_artifact_completeness_manifest_identity_and_catalogs(self):
        self.assertEqual(validate_p05_contract(MODULE, self.manifest), [])
        for artifact in (self.readme, self.lesson, self.walkthrough, self.checks):
            self.assertIn(GUIDING_QUESTION, artifact)
        self.assertIn("Project 5 is now the latest implemented lesson", self.root_readme)
        self.assertIn("Projects 6–84 intentionally wait", self.root_readme)
        self.assertIn("Project 5 is the next lesson after P04", self.start_here)
        self.assertRegex(
            self.module_index,
            r"\| \[P05\].*\| implemented \| 1 \| Explore White, Colored, and Impulsive Noise \|",
        )

    def test_contract_validator_rejects_missing_duplicate_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied_module = Path(temporary) / MODULE.name
            shutil.copytree(MODULE, copied_module)
            (copied_module / "experiment.m").unlink()
            self.assertIn(
                "P05 missing experiment.m",
                validate_p05_contract(copied_module, self.manifest),
            )

        malformed_manifest = copy.deepcopy(self.manifest)
        malformed_manifest["modules"][4]["guiding_question"] = "generic noise question"
        malformed_manifest["modules"][4]["slug"] = "wrong-module"
        malformed_manifest["modules"][4]["status"] = "scaffolded"
        errors = validate_p05_contract(MODULE, malformed_manifest)
        self.assertIn(f"P05 guiding_question must be {GUIDING_QUESTION!r}", errors)
        self.assertIn("P05 slug must be 'explore-white-colored-and-impulsive-noise'", errors)
        self.assertIn("P05 status must be 'implemented'", errors)

        duplicate_manifest = copy.deepcopy(self.manifest)
        duplicate_manifest["modules"].append(copy.deepcopy(duplicate_manifest["modules"][4]))
        self.assertEqual(
            validate_p05_contract(MODULE, duplicate_manifest),
            ["expected one P05 manifest entry, found 2"],
        )
        self.assertEqual(
            validate_p05_contract(MODULE, {"modules": "not-a-list"}),
            ["manifest modules must be a list"],
        )
        self.assertEqual(
            validate_p05_contract(MODULE, {"modules": ["not-an-object"]}),
            ["manifest module entries must be objects"],
        )

    def test_seeded_explicit_sources_and_equal_rms_contract(self):
        for expression in (
            "random_seed = 505;",
            "random_stream = RandStream('mt19937ar', 'Seed', random_seed);",
            "white_raw = randn(random_stream, 1, sample_count);",
            "colored_raw(sample_index) = colored_alpha*colored_raw(sample_index-1)",
            "narrowband_raw = cos(2*pi*tone_frequency_hz*t + narrowband_phase_rad);",
            "impulse_mask = impulse_selector < impulse_probability;",
            "impulse_mask(64) = true;",
            "raw_centered = raw_noise(noise_index,:) - mean(raw_noise(noise_index,:));",
            "noise_rms_target*raw_centered/raw_rms_v(noise_index);",
            "all(abs(noise_rms_v-noise_rms_target) < normalization_tolerance_v)",
        ):
            self.assertIn(expression, self.experiment)

        generator = random.Random(505)
        sample_count = 4096
        white = [generator.gauss(0, 1) for _ in range(sample_count)]
        colored_driver = [generator.gauss(0, 1) for _ in range(sample_count)]
        colored = one_pole(colored_driver, 0.92)
        narrowband = [
            math.cos(2 * math.pi * 512 * index / 4096 + 0.37)
            for index in range(sample_count)
        ]
        impulsive = [0.0] * sample_count
        for index in range(0, sample_count, 101):
            impulsive[index] = (-1 if index // 101 % 2 else 1) * (
                1 + abs(generator.gauss(0, 1))
            )

        target = 0.25
        normalized = [
            center_and_normalize(values, target)
            for values in (white, colored, narrowband, impulsive)
        ]
        for values in normalized:
            self.assertAlmostEqual(sum(values) / len(values), 0, places=14)
            self.assertAlmostEqual(root_mean_square(values), target, places=14)
        crest_factors = [max(map(abs, values)) / target for values in normalized]
        self.assertGreater(crest_factors[3], 5)
        self.assertGreater(crest_factors[3], crest_factors[0])
        with self.assertRaises(ValueError):
            center_and_normalize([1.0] * 64, target)

    def test_autocorrelation_and_colored_memory_sweep(self):
        for marker in (
            "Autocorrelation - measure memory directly",
            "r[ell] = mean_n x[n]*x[n+ell]",
            "autocorrelation(noise_index,lag_index)",
            "Parameter sweep 1 - change only colored-noise memory",
            "colored_alphas = [0 0.70 0.95]",
            "colored_sweep_lag_one",
            "colored_sweep_low_power_fraction",
            "all(diff(colored_sweep_lag_one) > 0.15)",
        ):
            self.assertIn(marker, self.experiment)

        generator = random.Random(505)
        driver = [generator.gauss(0, 1) for _ in range(4096)]
        correlations = [
            lag_one_correlation(center_and_normalize(one_pole(driver, alpha), 0.25))
            for alpha in (0.0, 0.70, 0.95)
        ]
        self.assertLess(abs(correlations[0]), 0.05)
        self.assertGreater(correlations[1], 0.65)
        self.assertGreater(correlations[2], 0.93)
        self.assertTrue(all(right - left > 0.2 for left, right in zip(correlations, correlations[1:])))
        # The one-pole power ratio between DC and Nyquist grows rapidly with alpha.
        theoretical_ratios = [((1 + alpha) / (1 - alpha)) ** 2 for alpha in (0.0, 0.70, 0.95)]
        self.assertEqual(theoretical_ratios[0], 1)
        self.assertGreater(theoretical_ratios[1], theoretical_ratios[0])
        self.assertGreater(theoretical_ratios[2], theoretical_ratios[1])

    def test_psd_scaling_units_and_power_conservation(self):
        for expression in (
            "X[k] = sum_n x[n]*exp(-j*2*pi*k*n/N)",
            "noise_fft = fft(noise, [], 2);",
            "abs(noise_fft(:,1:sample_count/2+1)).^2/(fs*sample_count);",
            "noise_psd_v2_per_hz(:,2:end-1)",
            "Frequency (Hz)",
            "PSD (dB V^2/Hz)",
            "low_frequency_band_hz = 200;",
        ):
            self.assertIn(expression, self.experiment)

        sample_count = 64
        sample_rate_hz = 64
        rms_target = 0.25
        amplitude = math.sqrt(2) * rms_target
        values = [
            amplitude * math.cos(2 * math.pi * 8 * index / sample_rate_hz)
            for index in range(sample_count)
        ]
        density = one_sided_psd(values, sample_rate_hz)
        frequency_spacing = sample_rate_hz / sample_count
        self.assertAlmostEqual(sum(density) * frequency_spacing, rms_target**2, places=13)
        self.assertAlmostEqual(density[8], rms_target**2 / frequency_spacing, places=13)
        self.assertLess(sum(density) - density[8], 1e-25)

    def test_same_tone_comparison_and_narrowband_offset_sweep(self):
        for marker in (
            "Add every equal-RMS record to the same tone",
            "received = noise + repmat(tone, noise_type_count, 1);",
            "(2/sample_count)*sum(received(noise_index,:).*tone_oscillator)",
            "time_domain_snr_db",
            "Parameter sweep 2 - change only narrowband offset from the target",
            "interference_offsets_hz = [0 16 128]",
            "offset_tone_error_v",
            "all(offset_tone_error_v(2:end) < 1e-10)",
        ):
            self.assertIn(marker, self.experiment)

        sample_count = 4096
        sample_rate_hz = 4096
        target_frequency_hz = 512
        target_amplitude = 0.18
        target_phase = math.pi / 9
        noise_rms = 0.25
        target = [
            target_amplitude
            * math.cos(2 * math.pi * target_frequency_hz * index / sample_rate_hz + target_phase)
            for index in range(sample_count)
        ]
        reference = target_amplitude * cmath.exp(1j * target_phase)
        errors: list[float] = []
        for offset_hz in (0, 16, 128):
            interference = [
                math.sqrt(2)
                * noise_rms
                * math.cos(
                    2
                    * math.pi
                    * (target_frequency_hz + offset_hz)
                    * index
                    / sample_rate_hz
                    + 0.37
                )
                for index in range(sample_count)
            ]
            received = [signal + noise for signal, noise in zip(target, interference)]
            errors.append(abs(tone_projection(received, target_frequency_hz, sample_rate_hz) - reference))
        self.assertAlmostEqual(errors[0], math.sqrt(2) * noise_rms, places=13)
        self.assertLess(errors[1], 1e-13)
        self.assertLess(errors[2], 1e-13)
        self.assertAlmostEqual(
            20 * math.log10((target_amplitude / math.sqrt(2)) / noise_rms),
            -5.863650028014443,
        )

    def test_required_views_labels_metrics_and_broken_case(self):
        for view in (
            "Short time records",
            "common-scale histograms",
            "Autocorrelation - measure memory directly",
            "One-sided PSD - measure where the same power lives",
            "the same tone is not equally trustworthy",
        ):
            self.assertIn(view, self.experiment)
        for label in (
            "Time (s)",
            "Noise (V)",
            "Noise amplitude (V)",
            "Sample probability",
            "Lag (samples)",
            "Normalized autocorrelation",
            "Frequency (Hz)",
            "PSD (dB V^2/Hz)",
            "Target phasor error (V)",
            "Raw generator RMS (V RMS)",
        ):
            self.assertIn(label, self.experiment)
        for marker in (
            "Deliberately broken case - compare raw generators without equal RMS",
            "raw_received = raw_noise + repmat(tone, noise_type_count, 1);",
            "raw_rms_ratio = max(raw_rms_v)/min(raw_rms_v);",
            "raw_rms_ratio > 3",
            "Recovery: subtract each record mean and rescale every centered record",
        ):
            self.assertIn(marker, self.experiment)
        self.assertIn("Compare unequal raw generator scales", self.walkthrough)
        self.assertIn("Recover the fair experiment non-destructively", self.walkthrough)

    def test_concept_first_documents_limiting_cases_and_radar_connection(self):
        combined_docs = "\n".join((self.lesson, self.walkthrough, self.checks))
        for concept in (
            "distribution",
            "bandwidth",
            "correlation",
            "impulsive",
            "crest factor",
            "one-pole",
            "periodogram",
            "co-channel",
            "orthogonal",
            "V^2/Hz",
            "radar",
            "base MATLAB",
        ):
            self.assertIn(concept.lower(), combined_docs.lower())
        for limiting_case in (
            "`alpha = 0`",
            "`alpha` approaching 1",
            "Interferer offset `0 Hz`",
            "Nonzero coherent-bin offset",
            "Impulse probability approaching zero",
            "Infinite record idealization",
        ):
            self.assertIn(limiting_case, self.lesson)
        for section in (
            "## Baseline",
            "## Sweep 1",
            "## Sweep 2",
            "## Broken case",
            "## Recovery",
            "## Concept connection",
        ):
            self.assertIn(section, self.walkthrough)
        for section in (
            "## Baseline observation checks",
            "## Predict, then verify",
            "## Identify from two views",
            "## Interpretation checks",
            "## Failure classification",
            "## Teach-back completion",
        ):
            self.assertIn(section, self.checks)

    def test_no_placeholder_or_unexplained_black_box_regression(self):
        implementation_text = "\n".join(
            (self.experiment, self.readme, self.lesson, self.walkthrough, self.checks)
        )
        self.assertIsNone(
            re.search(r"\b(TODO|TBD|FIXME|lorem ipsum|coming soon)\b", implementation_text, re.I)
        )
        for prohibited_call in (
            "awgn(",
            "filter(",
            "xcorr(",
            "periodogram(",
            "pwelch(",
            "pspectrum(",
            "phased.",
            "dsp.",
            "comm.",
            "readtable(",
            "webread(",
        ):
            self.assertNotIn(prohibited_call, implementation_text)
        self.assertIn("base MATLAB only", self.readme)
        self.assertIn("one-pole recursion", self.readme)
        self.assertIn("No Welch averaging is used", self.experiment)

    def test_malformed_controls_and_resource_bounds_precede_allocation(self):
        self.assertEqual(self.scalar_assignment("max_samples"), 16384)
        self.assertEqual(self.scalar_assignment("max_sweep_cases"), 8)
        self.assertEqual(self.scalar_assignment("max_lag_samples"), 96)
        self.assertEqual(self.scalar_assignment("histogram_bin_count"), 80)
        for guard in (
            "assert(sample_count <= max_samples",
            "assert(mod(sample_count, 2) == 0",
            "max_lag_samples < sample_count",
            "tone_frequency_hz < fs/2",
            "colored_alpha >= 0 && colored_alpha < 1",
            "impulse_probability > 0",
            "impulse_probability < 0.25",
            "histogram_bin_count >= 16 && histogram_bin_count <= 128",
            "max_samples == floor(max_samples) && max_samples == 16384",
            "max_sweep_cases == floor(max_sweep_cases) && max_sweep_cases == 8",
            "isfinite(noise_type_count) && noise_type_count == 4",
            "numel(colored_alphas) <= max_sweep_cases",
            "numel(interference_offsets_hz) <= max_sweep_cases",
        ):
            self.assertIn(guard, self.experiment)

        allocation = self.experiment.index(
            "white_raw = randn(random_stream, 1, sample_count);"
        )
        sample_guard = self.experiment.index("assert(sample_count <= max_samples")
        lag_guard = self.experiment.index("assert(max_lag_samples < sample_count")
        self.assertLess(sample_guard, allocation)
        self.assertLess(lag_guard, allocation)
        colored_sweep_allocation = self.experiment.index("colored_sweep_psd = zeros")
        colored_sweep_guard = self.experiment.index("numel(colored_alphas) <= max_sweep_cases")
        self.assertLess(colored_sweep_guard, colored_sweep_allocation)
        offset_sweep_allocation = self.experiment.index("offset_received_psd = zeros")
        offset_sweep_guard = self.experiment.index(
            "numel(interference_offsets_hz) <= max_sweep_cases"
        )
        self.assertLess(offset_sweep_guard, offset_sweep_allocation)

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
        for valid in (0.01, 96, 4096.0):
            with self.subTest(valid=valid):
                self.assertTrue(positive_finite_real_scalar(valid))

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback_scope(self):
        # P05 has no asynchronous work or persistent file/learner-state
        # mutation. Finite bounded loops and deterministic rerun are the
        # applicable cancellation and rollback contract.
        self.assertLessEqual(self.experiment.count("figure("), 8)
        self.assertNotRegex(self.experiment, r"(?m)^\s*(while|parfor|timer|parfeval|batch)\b")
        for feature in (
            "pause(",
            "drawnow",
            "VideoWriter",
            "uicontrol",
            "webread(",
            "tcpclient(",
            "serialport(",
            "audioplayer(",
            "save(",
            "delete(",
            "fopen(",
        ):
            self.assertNotIn(feature, self.experiment)
        self.assertNotIn(".learning", self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*(clear|close\s+all|clc)\s*;")
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")
        self.assertIn("random_stream = RandStream('mt19937ar', 'Seed', random_seed);", self.experiment)
        self.assertIn("prior_p05_figures = findall(groot", self.experiment)
        self.assertEqual(
            self.experiment.count("'Tag', p05_figure_tag"),
            self.experiment.count("figure(") + 1,
        )
        self.assertIn("Every loop is finite and bounded", self.experiment)
        self.assertIn("stop the finite script with Ctrl+C", self.walkthrough)
        self.assertIn("no partial file or learner-state cleanup is needed", self.walkthrough)
        self.assertIn("writes no files and changes no learner progress", self.walkthrough)
        self.assertIn("Re-running from the seed recovers", self.walkthrough)
        self.assertIn("There is no persistent file or learner-state mutation", self.checks)
        self.assertIn("preserve the\nglobal random stream and unrelated figures", self.checks)
        self.assertIn("must not wholesale-clear\nthe workspace or command window", self.checks)
        self.assertIn("no toolbox, helper function, external data", self.readme)
        self.assertRegex(
            self.readme,
            r"no toolbox, helper function, external data,[\s\S]*or asynchronous task",
        )


if __name__ == "__main__":
    unittest.main()
