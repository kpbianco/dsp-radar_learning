from __future__ import annotations

import copy
import json
import math
import re
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "08-use-correlation-to-find-a-hidden-pattern"
MANIFEST_PATH = ROOT / "curriculum" / "modules.json"
GUIDING_QUESTION = "How can a known waveform be located inside noise and delay?"
REQUIRED_ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
REFERENCE_CHIPS = [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1]


def validate_p08_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P08 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P08 empty {name}")

    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P08"]
    if len(entries) != 1:
        return errors + [f"expected one P08 manifest entry, found {len(entries)}"]

    expected = {
        "number": 8,
        "id": "P08",
        "title": "Use Correlation to Find a Hidden Pattern",
        "guiding_question": GUIDING_QUESTION,
        "phase": 1,
        "phase_title": "Signals, Sampling, and Systems",
        "slug": "use-correlation-to-find-a-hidden-pattern",
        "folder": "modules/08-use-correlation-to-find-a-hidden-pattern",
        "status": "implemented",
        "implementation_batch": "P08",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P08 {key} must be {value!r}")
    return errors


def normalized_reference() -> list[float]:
    repeated = [chip for chip in REFERENCE_CHIPS for _ in range(2)]
    mean = sum(repeated) / len(repeated)
    centered = [value - mean for value in repeated]
    rms = math.sqrt(sum(value * value for value in centered) / len(centered))
    return [value / rms for value in centered]


def embed(record_length: int, reference: list[float], delay: int, amplitude: float) -> list[float]:
    record = [0.0] * record_length
    for index, value in enumerate(reference):
        record[delay + index] += amplitude * value
    return record


def explicit_correlation(received: list[float], reference: list[float]) -> tuple[list[int], list[float]]:
    lags = list(range(-(len(reference) - 1), len(received)))
    output: list[float] = []
    for lag in lags:
        output.append(
            sum(
                received[lag + reference_index] * reference_value
                for reference_index, reference_value in enumerate(reference)
                if 0 <= lag + reference_index < len(received)
            )
        )
    return lags, output


def full_convolution(first: list[float], second: list[float]) -> list[float]:
    output = [0.0] * (len(first) + len(second) - 1)
    for first_index, first_value in enumerate(first):
        for second_index, second_value in enumerate(second):
            output[first_index + second_index] += first_value * second_value
    return output


def local_maximum_at(values: list[float], index: int) -> bool:
    return 0 < index < len(values) - 1 and values[index] > values[index - 1] and values[index] > values[index + 1]


class P08ModuleTests(unittest.TestCase):
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
        match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*([0-9.]+)\s*;", self.experiment)
        self.assertIsNotNone(match, f"missing visible scalar assignment for {name}")
        return float(match.group(1))

    def test_artifact_completeness_manifest_identity_and_catalogs(self):
        self.assertEqual(validate_p08_contract(MODULE, self.manifest), [])
        for artifact in (self.readme, self.lesson, self.walkthrough, self.checks):
            self.assertIn(GUIDING_QUESTION, artifact)
        self.assertIn("Project 8 is the latest implemented lesson", self.root_readme)
        self.assertIn("Projects 9–84", self.root_readme)
        self.assertIn("Project 8 is the next lesson after P07", self.start_here)
        self.assertRegex(
            self.module_index,
            r"\| \[P08\].*\| implemented \| 1 \| Use Correlation to Find a Hidden Pattern \|",
        )

    def test_contract_validator_rejects_missing_duplicate_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied_module = Path(temporary) / MODULE.name
            shutil.copytree(MODULE, copied_module)
            (copied_module / "checks.md").unlink()
            self.assertIn("P08 missing checks.md", validate_p08_contract(copied_module, self.manifest))

        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][7]["guiding_question"] = "generic pattern question"
        malformed["modules"][7]["slug"] = "wrong-module"
        malformed["modules"][7]["status"] = "scaffolded"
        errors = validate_p08_contract(MODULE, malformed)
        self.assertIn(f"P08 guiding_question must be {GUIDING_QUESTION!r}", errors)
        self.assertIn("P08 slug must be 'use-correlation-to-find-a-hidden-pattern'", errors)
        self.assertIn("P08 status must be 'implemented'", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][7]))
        self.assertEqual(validate_p08_contract(MODULE, duplicate), ["expected one P08 manifest entry, found 2"])
        self.assertEqual(validate_p08_contract(MODULE, {"modules": "bad"}), ["manifest modules must be a list"])
        self.assertEqual(validate_p08_contract(MODULE, {"modules": ["bad"]}), ["manifest module entries must be objects"])

    def test_deterministic_input_and_visible_correlation_contract(self):
        for marker in (
            "random_seed = 808;",
            "random_stream = RandStream('mt19937ar', 'Seed', random_seed);",
            "reference_chips = [1 1 1 1 1 -1 -1 1 1 -1 1 -1 1];",
            "hidden_delay_samples = 137;",
            "hidden_amplitude_v = 0.65;",
            "noise_sigma_v = 0.50;",
            "r_xs[lag] = sum_m x[lag+m]*s[m]",
            "explicit_correlation_v(lag_index) =",
            "conv_correlation_v = conv(received_v, fliplr(reference));",
            "estimated_delay_samples == hidden_delay_samples",
        ):
            self.assertIn(marker, self.experiment)
        self.assertIn("P07 is the prerequisite", self.readme)
        self.assertIn("base MATLAB", self.readme)

    def test_independent_correlation_locates_hidden_delay_and_matches_reversed_convolution(self):
        reference = normalized_reference()
        self.assertEqual(len(reference), 26)
        self.assertAlmostEqual(sum(reference), 0.0)
        self.assertAlmostEqual(sum(value * value for value in reference), 26.0)
        self.assertNotEqual(reference, list(reversed(reference)))

        delay = 137
        clean = embed(256, reference, delay, 0.65)
        bounded_noise = [0.5 * (((index * 37) % 17) - 8) / 16 for index in range(256)]
        received = [signal + noise for signal, noise in zip(clean, bounded_noise)]
        lags, correlation = explicit_correlation(received, reference)
        peak_index = max(range(len(correlation)), key=correlation.__getitem__)
        self.assertEqual(lags[peak_index], delay)

        convolution = full_convolution(received, list(reversed(reference)))
        self.assertEqual(len(correlation), 281)
        for actual, expected in zip(correlation, convolution):
            self.assertAlmostEqual(actual, expected)
        aligned_products = [received[delay + index] * value for index, value in enumerate(reference)]
        self.assertAlmostEqual(sum(aligned_products), correlation[peak_index])

    def test_correlation_is_linear_and_preserves_signed_copy_polarity(self):
        reference = normalized_reference()
        first = embed(128, reference, 17, 0.80)
        second = embed(128, reference, 71, -0.45)
        first_scale = -1.25
        second_scale = 0.60
        mixed = [
            first_scale * first_value + second_scale * second_value
            for first_value, second_value in zip(first, second)
        ]

        lags, mixed_correlation = explicit_correlation(mixed, reference)
        first_lags, first_correlation = explicit_correlation(first, reference)
        second_lags, second_correlation = explicit_correlation(second, reference)
        self.assertEqual(lags, first_lags)
        self.assertEqual(lags, second_lags)
        for actual, first_value, second_value in zip(
            mixed_correlation, first_correlation, second_correlation
        ):
            self.assertAlmostEqual(
                actual,
                first_scale * first_value + second_scale * second_value,
            )

        negative_delay = 43
        negative_amplitude = -0.70
        negative_copy = embed(128, reference, negative_delay, negative_amplitude)
        negative_lags, negative_correlation = explicit_correlation(negative_copy, reference)
        absolute_peak_index = max(
            range(len(negative_correlation)),
            key=lambda index: abs(negative_correlation[index]),
        )
        self.assertEqual(negative_lags[absolute_peak_index], negative_delay)
        self.assertAlmostEqual(
            negative_correlation[absolute_peak_index],
            negative_amplitude * sum(value * value for value in reference),
        )
        self.assertLess(negative_correlation[absolute_peak_index], 0.0)
        self.assertNotEqual(
            negative_lags[max(range(len(negative_correlation)), key=negative_correlation.__getitem__)],
            negative_delay,
            "a signed maximum must not silently behave like an absolute-value detector",
        )

    def test_amplitude_and_noise_changes_reuse_every_other_input(self):
        reference = normalized_reference()
        energy = sum(value * value for value in reference)
        delay = 80
        unit_noise = [(((index * 11) % 19) - 9) / 9 for index in range(180)]

        true_lag_values = []
        for amplitude in (0.10, 0.30, 0.65):
            clean = embed(180, reference, delay, amplitude)
            received = [signal + 0.5 * noise for signal, noise in zip(clean, unit_noise)]
            lags, output = explicit_correlation(received, reference)
            true_lag_values.append(output[lags.index(delay)])
        self.assertAlmostEqual(true_lag_values[1] - true_lag_values[0], 0.20 * energy)
        self.assertAlmostEqual(true_lag_values[2] - true_lag_values[1], 0.35 * energy)
        peak_to_noise_rms_ratio = 0.65 * math.sqrt(energy) / 0.50
        power_snr_linear = peak_to_noise_rms_ratio**2
        self.assertAlmostEqual(power_snr_linear, 0.65**2 * energy / 0.50**2)
        self.assertIn("matched_output_peak_to_noise_rms_ratio", self.experiment)
        self.assertIn("matched_output_power_snr_linear", self.experiment)

        clean = embed(180, reference, delay, 0.65)
        noise_outputs = []
        for sigma in (0.20, 0.50, 0.90):
            received = [signal + sigma * noise for signal, noise in zip(clean, unit_noise)]
            _, output = explicit_correlation(received, reference)
            noise_outputs.append(output)
        clean_output = explicit_correlation(clean, reference)[1]
        for output_index in range(len(clean_output)):
            low_residual = noise_outputs[0][output_index] - clean_output[output_index]
            high_residual = noise_outputs[2][output_index] - clean_output[output_index]
            self.assertAlmostEqual(high_residual, 4.5 * low_residual)

        for marker in (
            "Parameter sweep 1 - change only hidden amplitude",
            "amplitude_sweep_v = [0.10 0.30 0.65]",
            "Only amplitude changes; true-lag response must change by delta A times energy",
            "Controlled noise comparison - change only noise standard deviation",
            "noise_sweep_sigma_v = [0.20 0.50 0.90]",
            "exact standard-normal realization remains fixed",
        ):
            self.assertIn(marker, self.experiment)

    def test_second_copy_separation_exposes_merged_and_distinct_peaks(self):
        reference = normalized_reference()
        first_delay = 100
        local_peak_results = {}
        for separation in (1, 8, 32):
            received = embed(220, reference, first_delay, 0.65)
            second = embed(220, reference, first_delay + separation, 0.50)
            received = [first + later for first, later in zip(received, second)]
            lags, output = explicit_correlation(received, reference)
            first_index = lags.index(first_delay)
            second_index = lags.index(first_delay + separation)
            local_peak_results[separation] = (
                local_maximum_at(output, first_index),
                local_maximum_at(output, second_index),
            )

        self.assertEqual(local_peak_results[1], (True, False))
        self.assertEqual(local_peak_results[8], (True, True))
        self.assertEqual(local_peak_results[32], (True, True))
        for marker in (
            "Parameter sweep 2 - change only second-copy separation",
            "second_separation_sweep_samples = [1 8 32]",
            "At one",
            "sample separation the two autocorrelation lobes overlap into one main peak",
            "merged to resolvable peaks",
        ):
            self.assertIn(marker, self.experiment)

    def test_broken_vector_index_mapping_and_recovery(self):
        reference = normalized_reference()
        delay = 73
        received = embed(160, reference, delay, 0.65)
        lags, correlation = explicit_correlation(received, reference)
        peak_index_zero_based = max(range(len(correlation)), key=correlation.__getitem__)
        broken_delay = peak_index_zero_based
        recovered_delay = lags[peak_index_zero_based]
        self.assertEqual(broken_delay - delay, len(reference) - 1)
        self.assertEqual(recovered_delay, delay)

        for marker in (
            "Deliberately broken case - report the convolution index as delay",
            "broken_reported_delay_samples = broken_peak_index - 1;",
            "recovered_delay_samples = correlation_lags_samples(broken_peak_index);",
            "broken_delay_error_samples == reference_sample_count-1",
            "recovery_delay_error_samples == 0",
            "vector index is not physical lag",
        ):
            self.assertIn(marker, self.experiment)

    def test_required_views_labels_metrics_and_concept_first_documents(self):
        for view in (
            "known pattern hidden in a noisy record",
            "explicit similarity versus relative delay",
            "amplitude controls correlation peak strength",
            "noise raises random correlation structure",
            "close delayed copies merge in correlation",
            "vector index is not physical lag",
        ):
            self.assertIn(view, self.experiment)
        for label in (
            "Reference sample index m",
            "Reference s[m] (dimensionless)",
            "Record time (ms)",
            "Received voltage x[n] (V)",
            "Relative lag (samples)",
            "Correlation r_{xs}[lag] (V)",
            "delay error",
            "peak/outside-neighborhood ratio",
            "peak/noise-RMS amplitude ratio",
            "matched-output power SNR (linear)",
        ):
            self.assertIn(label, self.experiment)

        combined = "\n".join((self.lesson, self.walkthrough, self.checks)).lower()
        for concept in (
            "relative delay",
            "aligned products",
            "coherent",
            "noise",
            "autocorrelation",
            "matched filtering",
            "radar",
            "base matlab",
        ):
            self.assertIn(concept, combined)
        for limiting_case in (
            "If `A = 0`",
            "If `sigma = 0`",
            "If `D = 0`",
            "reference has length one",
            "reference is all zeros",
            "copy is negative",
            "reference is periodic",
            "record boundary",
            "Colored noise",
        ):
            self.assertIn(limiting_case, self.lesson)
        for section in ("## Baseline", "## Sweep 1", "## Controlled noise comparison", "## Sweep 2", "## Broken case", "## Recovery", "## Concept connection"):
            self.assertIn(section, self.walkthrough)
        for section in ("## Baseline observation checks", "## Predict, then verify", "## Interpretation checks", "## Failure classification", "## Teach-back completion"):
            self.assertIn(section, self.checks)

    def test_no_placeholder_or_unexplained_black_box_regression(self):
        implementation = "\n".join((self.experiment, self.readme, self.lesson, self.walkthrough, self.checks))
        self.assertIsNone(re.search(r"\b(TODO|TBD|FIXME|lorem ipsum|coming soon)\b", implementation, re.I))
        for prohibited in (
            "xcorr(",
            "finddelay(",
            "filter(",
            "phased.",
            "dsp.",
            "readtable(",
            "webread(",
        ):
            self.assertNotIn(prohibited, implementation)
        self.assertIn("base MATLAB `conv(x,fliplr(s))`", self.readme)
        self.assertIn("explicit bounded loops before using", self.readme)
        self.assertLess(
            self.experiment.index("Correlate explicitly over relative delay"),
            self.experiment.index("conv_correlation_v = conv("),
        )

    def test_malformed_controls_and_resource_bounds_precede_allocation(self):
        self.assertEqual(self.scalar_assignment("max_record_samples"), 512)
        self.assertEqual(self.scalar_assignment("max_reference_samples"), 64)
        self.assertEqual(self.scalar_assignment("max_correlation_samples"), 1024)
        self.assertEqual(self.scalar_assignment("max_sweep_cases"), 8)
        self.assertEqual(self.scalar_assignment("max_figure_groups"), 6)
        for guard in (
            "random_seed <= 2^32-1",
            "record_sample_count <= max_record_samples",
            "numel(reference_chips)*samples_per_chip <= max_reference_samples",
            "correlation_sample_count <= max_correlation_samples",
            "hidden_delay_samples + reference_sample_count <= record_sample_count",
            "hidden_delay_samples + max(second_separation_sweep_samples)",
            "numel(amplitude_sweep_v) <= max_sweep_cases",
            "numel(noise_sweep_sigma_v) <= max_sweep_cases",
            "numel(second_separation_sweep_samples) <= max_sweep_cases",
            "all(second_separation_sweep_samples ==",
            "~isequal(reference_chips, fliplr(reference_chips))",
            "zoom_start_sample = max(0, hidden_delay_samples-12)",
            "zoom_stop_sample = min(record_sample_count-1",
        ):
            self.assertIn(guard, self.experiment)
        first_record_allocation = self.experiment.index("clean_hidden_v = zeros")
        self.assertLess(self.experiment.index("record_sample_count <= max_record_samples"), first_record_allocation)
        self.assertLess(self.experiment.index("correlation_sample_count <= max_correlation_samples"), first_record_allocation)
        self.assertLess(
            self.experiment.index("numel(amplitude_sweep_v) <= max_sweep_cases"),
            self.experiment.index("amplitude_sweep_correlations_v = zeros"),
        )
        self.assertLess(
            self.experiment.index("zoom_start_sample = max(0, hidden_delay_samples-12)"),
            self.experiment.index("prior_p08_figures = findall"),
        )

        reference_length = 26
        max_separation = 32
        maximum_accepted_delay = 256 - reference_length - max_separation
        self.assertEqual(maximum_accepted_delay, 198)
        for delay in (0, 5, 137, maximum_accepted_delay):
            zoom_start = max(0, delay - 12)
            zoom_stop = min(256 - 1, delay + reference_length + 11)
            self.assertGreaterEqual(zoom_start, 0)
            self.assertLessEqual(zoom_stop, 255)
            self.assertLessEqual(zoom_start, zoom_stop)

        def finite_nonnegative_integer(value: object) -> bool:
            return (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
                and value >= 0
                and value == math.floor(value)
            )

        for malformed in (-1, 1.5, math.nan, math.inf, 1 + 1j, True):
            with self.subTest(malformed=malformed):
                self.assertFalse(finite_nonnegative_integer(malformed))
        for valid in (0, 137, 512.0):
            self.assertTrue(finite_nonnegative_integer(valid))

        def supported_seed(value: object) -> bool:
            return finite_nonnegative_integer(value) and value <= 2**32 - 1

        for malformed_seed in (-1, 1.5, math.nan, math.inf, True, 2**32):
            self.assertFalse(supported_seed(malformed_seed))
        for valid_seed in (0, 808, 2**32 - 1):
            self.assertTrue(supported_seed(valid_seed))

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback_scope(self):
        self.assertLessEqual(self.experiment.count("figure("), 6)
        self.assertNotRegex(self.experiment, r"(?m)^\s*(while|parfor|timer|parfeval|batch)\b")
        for destructive in ("clear all", "close all", "clc", "rng("):
            self.assertNotIn(destructive, self.experiment.lower())
        for external in (
            "fopen(", "save(", "writetable(", "urlread(", "webread(",
            "tcpclient(", "serialport(", "audiorecorder(", "input(", "pause(",
        ):
            self.assertNotIn(external, self.experiment.lower())
        for marker in (
            "prior_p08_figures = findall",
            "close(prior_p08_figures);",
            "RandStream('mt19937ar'",
            "Ctrl+C",
            "There is no persistent file",
            "base MATLAB only",
        ):
            self.assertIn(marker, "\n".join((self.experiment, self.walkthrough, self.checks)))
        self.assertGreater(
            self.experiment.index("prior_p08_figures = findall"),
            self.experiment.index("hidden_delay_samples + max(second_separation_sweep_samples)"),
        )
        self.assertNotIn(".learning", self.experiment)
        self.assertIn("restore only P08", self.readme)
        self.assertIn("manifest status to `scaffolded`", self.readme)


if __name__ == "__main__":
    unittest.main()
