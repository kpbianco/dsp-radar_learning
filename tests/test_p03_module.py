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
MODULE = ROOT / "modules" / "03-make-aliasing-visually-obvious"
MANIFEST_PATH = ROOT / "curriculum" / "modules.json"
REQUIRED_ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
GUIDING_QUESTION = (
    "Why does a high-frequency tone appear as a lower-frequency tone after sampling?"
)


def validate_p03_contract(module_dir: Path, manifest: dict) -> list[str]:
    """Return deterministic P03 contract failures for positive and negative tests."""
    errors: list[str] = []
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return ["manifest modules must be a list"]
    if any(not isinstance(entry, dict) for entry in modules):
        return ["manifest module entries must be objects"]

    matches = [entry for entry in modules if entry.get("id") == "P03"]
    if len(matches) != 1:
        return [f"expected one P03 manifest entry, found {len(matches)}"]

    entry = matches[0]
    expected_identity = {
        "number": 3,
        "title": "Make Aliasing Visually Obvious",
        "phase": 1,
        "phase_title": "Signals, Sampling, and Systems",
        "slug": "make-aliasing-visually-obvious",
        "guiding_question": GUIDING_QUESTION,
        "folder": "modules/03-make-aliasing-visually-obvious",
        "status": "implemented",
        "implementation_batch": "P03",
    }
    for field, expected in expected_identity.items():
        if entry.get(field) != expected:
            errors.append(f"P03 {field} must be {expected!r}")

    for name in REQUIRED_ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P03 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P03 empty {name}")
    return errors


class P03ModuleTests(unittest.TestCase):
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

    @staticmethod
    def matlab_nearest_integer(value: float) -> int:
        """Match MATLAB round for the nonnegative sweep values used by P03."""
        return math.floor(value + 0.5)

    def test_artifact_completeness_and_manifest_identity(self):
        self.assertEqual(validate_p03_contract(MODULE, self.manifest), [])
        for artifact in (self.readme, self.lesson, self.walkthrough, self.checks):
            self.assertIn(GUIDING_QUESTION, artifact)
        self.assertIn("Project 3 is now implemented as the latest lesson", self.root_readme)
        self.assertIn("Project 3 is the next lesson after P02", self.start_here)
        self.assertRegex(
            self.module_index,
            r"\| \[P03\].*\| implemented \| 1 \| Make Aliasing Visually Obvious \|",
        )

    def test_contract_validator_rejects_missing_duplicate_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied_module = Path(temporary) / MODULE.name
            shutil.copytree(MODULE, copied_module)
            (copied_module / "checks.md").unlink()
            self.assertIn(
                "P03 missing checks.md",
                validate_p03_contract(copied_module, self.manifest),
            )

        malformed_manifest = copy.deepcopy(self.manifest)
        malformed_manifest["modules"][2]["guiding_question"] = "placeholder"
        malformed_manifest["modules"][2]["slug"] = "wrong-module"
        malformed_manifest["modules"][2]["status"] = "scaffolded"
        errors = validate_p03_contract(MODULE, malformed_manifest)
        self.assertIn(f"P03 guiding_question must be {GUIDING_QUESTION!r}", errors)
        self.assertIn("P03 slug must be 'make-aliasing-visually-obvious'", errors)
        self.assertIn("P03 status must be 'implemented'", errors)

        duplicate_manifest = copy.deepcopy(self.manifest)
        duplicate_manifest["modules"].append(copy.deepcopy(duplicate_manifest["modules"][2]))
        self.assertEqual(
            validate_p03_contract(MODULE, duplicate_manifest),
            ["expected one P03 manifest entry, found 2"],
        )
        self.assertEqual(
            validate_p03_contract(MODULE, {"modules": "not-a-list"}),
            ["manifest modules must be a list"],
        )
        self.assertEqual(
            validate_p03_contract(MODULE, {"modules": ["not-an-object"]}),
            ["manifest module entries must be objects"],
        )

    def test_deterministic_baseline_fold_and_recurrence_estimator(self):
        amplitude = self.scalar_assignment("A")
        input_hz = self.scalar_assignment("f_input")
        sample_rate_hz = self.scalar_assignment("fs")
        duration_s = self.scalar_assignment("duration")
        display_rate_hz = self.scalar_assignment("fs_display")
        phase_rad = math.pi / 5

        self.assertRegex(self.experiment, r"random_seed\s*=\s*303\s*;")
        self.assertIn("rng(random_seed, 'twister')", self.experiment)
        self.assertIn("alias_order = round(f_input/fs);", self.experiment)
        self.assertIn("f_alias_signed = f_input - alias_order*fs;", self.experiment)
        self.assertIn("f_apparent = abs(f_alias_signed);", self.experiment)
        self.assertIn("x_neighbor_sum = x_sample(3:end) + x_sample(1:end-2);", self.experiment)
        self.assertIn("f_apparent_hat = fs*acos(cos_omega_hat)/(2*pi);", self.experiment)

        self.assertEqual((input_hz, sample_rate_hz), (700.0, 1000.0))
        self.assertGreater(input_hz, sample_rate_hz / 2)
        alias_order = self.matlab_nearest_integer(input_hz / sample_rate_hz)
        signed_alias_hz = input_hz - alias_order * sample_rate_hz
        self.assertEqual(signed_alias_hz, -300.0)
        phase_alias_rad = -phase_rad
        sample_count = round(duration_s * sample_rate_hz)
        times = [index / sample_rate_hz for index in range(sample_count)]
        original = [
            amplitude * math.cos(2 * math.pi * input_hz * time + phase_rad)
            for time in times
        ]
        alias = [
            amplitude * math.cos(2 * math.pi * abs(signed_alias_hz) * time + phase_alias_rad)
            for time in times
        ]
        self.assertLess(max(abs(a - b) for a, b in zip(original, alias)), 1e-12)

        center = original[1:-1]
        neighbors = [original[index + 1] + original[index - 1] for index in range(1, sample_count - 1)]
        cos_estimate = sum(a * b for a, b in zip(center, neighbors)) / (
            2 * sum(value * value for value in center)
        )
        apparent_estimate_hz = sample_rate_hz * math.acos(max(-1, min(1, cos_estimate))) / (2 * math.pi)
        self.assertAlmostEqual(apparent_estimate_hz, 300.0, places=9)
        self.assertGreater(display_rate_hz, 2 * input_hz)

    def test_input_frequency_sweep_estimates_repeating_folds(self):
        for marker in (
            "Parameter sweep 1 - sweep input frequency with sample rate fixed",
            "input_frequency_sweep = 0:25:3000",
            "f_case - round(f_case/fs)*fs",
            "estimated_frequency_sweep",
            "sweep_estimator_error",
            "DC through three multiples of fs",
        ):
            self.assertIn(marker, self.experiment)

        amplitude = self.scalar_assignment("A")
        sample_rate_hz = self.scalar_assignment("fs")
        duration_s = self.scalar_assignment("duration")
        phase_rad = math.pi / 5
        sample_count = round(duration_s * sample_rate_hz)
        sample_indices = list(range(sample_count))
        maximum_error_hz = 0.0
        expected_points = {0: 0, 500: 500, 700: 300, 1000: 0, 1500: 500, 3000: 0}

        for input_hz in range(0, 3001, 25):
            signed_hz = input_hz - self.matlab_nearest_integer(input_hz / sample_rate_hz) * sample_rate_hz
            expected_hz = abs(signed_hz)
            values = [
                amplitude * math.cos(2 * math.pi * input_hz * index / sample_rate_hz + phase_rad)
                for index in sample_indices
            ]
            center = values[1:-1]
            neighbors = [values[index + 1] + values[index - 1] for index in range(1, sample_count - 1)]
            cos_estimate = sum(a * b for a, b in zip(center, neighbors)) / (
                2 * sum(value * value for value in center)
            )
            estimate_hz = sample_rate_hz * math.acos(max(-1, min(1, cos_estimate))) / (2 * math.pi)
            maximum_error_hz = max(maximum_error_hz, abs(estimate_hz - expected_hz))
            self.assertLessEqual(abs(signed_hz), sample_rate_hz / 2)
            if input_hz in expected_points:
                self.assertEqual(expected_hz, expected_points[input_hz])
        self.assertLess(maximum_error_hz, 1e-8)

    def test_representative_and_sample_rate_sweeps_have_expected_folds(self):
        for marker in (
            "representative_frequencies = [450 500 550 950 1000 1050]",
            "Representative sequences - look immediately around two folds",
            "Parameter sweep 2 - hold the input fixed and change only sample rate",
            "sample_rate_sweep = [2000 1200 1000 800]",
            "sample_rate_aliases",
            "sample_rate_aliases <= sample_rate_sweep/2",
        ):
            self.assertIn(marker, self.experiment)

        input_hz = self.scalar_assignment("f_input")
        representative_expected = {
            450: 450,
            500: 500,
            550: 450,
            950: 50,
            1000: 0,
            1050: 50,
        }
        for frequency_hz, expected_hz in representative_expected.items():
            signed_hz = frequency_hz - self.matlab_nearest_integer(frequency_hz / 1000) * 1000
            self.assertEqual(abs(signed_hz), expected_hz)

        aliases = []
        for rate_hz in (2000, 1200, 1000, 800):
            signed_hz = input_hz - self.matlab_nearest_integer(input_hz / rate_hz) * rate_hz
            aliases.append(abs(signed_hz))
        self.assertEqual(aliases, [700.0, 500.0, 300.0, 100.0])

    def test_broken_case_exposes_reflected_phase_error_and_recovery(self):
        for marker in (
            "Deliberately broken case - ignore phase reversal after a reflected fold",
            "f_wrong_alias = f_apparent;",
            "phi_wrong_alias = phi;",
            "wrong_phase_error",
            "correct_phase_error",
            "assert(wrong_phase_error > 0.5*A",
        ):
            self.assertIn(marker, self.experiment)

        amplitude = self.scalar_assignment("A")
        input_hz = self.scalar_assignment("f_input")
        sample_rate_hz = self.scalar_assignment("fs")
        duration_s = self.scalar_assignment("duration")
        phase_rad = math.pi / 5
        apparent_hz = 300.0
        times = [index / sample_rate_hz for index in range(round(duration_s * sample_rate_hz))]
        original = [
            amplitude * math.cos(2 * math.pi * input_hz * time + phase_rad)
            for time in times
        ]
        correct = [
            amplitude * math.cos(2 * math.pi * apparent_hz * time - phase_rad)
            for time in times
        ]
        broken = [
            amplitude * math.cos(2 * math.pi * apparent_hz * time + phase_rad)
            for time in times
        ]
        self.assertLess(max(abs(a - b) for a, b in zip(original, correct)), 1e-12)
        self.assertGreater(max(abs(a - b) for a, b in zip(original, broken)), 0.5 * amplitude)
        self.assertIn("Restore `phi_alias = -phi`", self.walkthrough)

    def test_operations_labels_and_metrics_are_explicit(self):
        for expression in (
            "x[n+1] + x[n-1] = 2*cos(omega)*x[n]",
            "recurrence_denominator = 2*sum(x_center.^2);",
            "cos_omega_hat = sum(x_center.*x_neighbor_sum)/recurrence_denominator;",
            "alias_sample_error",
            "estimator_error",
            "sweep_estimator_error",
        ):
            self.assertIn(expression, self.experiment)
        for label in (
            "Time (s)",
            "Amplitude (a.u.)",
            "Sample index n (samples)",
            "Measured amplitude x[n] (a.u.)",
            "Input frequency (Hz)",
            "Apparent frequency (Hz)",
            "Signed folded frequency (Hz)",
            "sample rate",
            "Nyquist limit",
        ):
            self.assertIn(label, self.experiment)

    def test_concept_first_documentation_and_completion_rubric(self):
        combined_docs = "\n".join((self.lesson, self.walkthrough, self.checks))
        for concept in (
            "deterministic folding",
            "Nyquist",
            "phase",
            "anti-alias filter",
            "alias family",
            "complex I/Q",
            "pulse-Doppler",
            "PRF",
            "base MATLAB",
        ):
            self.assertIn(concept.lower(), combined_docs.lower())
        for limiting_case in ("DC", "Exactly at Nyquist", "integer multiple", "Several multiples"):
            self.assertIn(limiting_case, self.lesson)
        for section in ("## Baseline", "## Sweep 1", "## Sweep 2", "## Broken case", "## Recovery"):
            self.assertIn(section, self.walkthrough)
        self.assertIn("## Predict, then verify", self.checks)
        self.assertIn("## Teach-back completion", self.checks)
        self.assertIn("700 Hz at 1000 samples/s appears at 300 Hz", self.checks)

    def test_no_placeholder_or_unexplained_black_box_regression(self):
        implementation_text = "\n".join((self.experiment, self.lesson, self.walkthrough, self.checks))
        self.assertIsNone(
            re.search(r"\b(TODO|TBD|FIXME|lorem ipsum|coming soon)\b", implementation_text, re.I)
        )
        for prohibited_call in (
            "fft(",
            "periodogram(",
            "findpeaks(",
            "interp1(",
            "resample(",
            "awgn(",
            "hilbert(",
            "phased.",
            "dsp.",
            "comm.",
            "Signal Processing Toolbox",
        ):
            self.assertNotIn(prohibited_call, implementation_text)
        self.assertIn("base MATLAB only", self.readme)
        self.assertIn("requires no toolbox beyond\nbase MATLAB", self.lesson)
        self.assertIn("explicit arithmetic", self.readme)

    def test_resource_bounds_malformed_controls_and_recovery_contract(self):
        self.assertEqual(self.scalar_assignment("max_display_points"), 20001)
        self.assertEqual(self.scalar_assignment("max_samples_per_case"), 5000)
        self.assertEqual(self.scalar_assignment("max_sweep_cases"), 128)
        self.assertEqual(self.scalar_assignment("max_representative_cases"), 8)
        for guard in (
            "assert(sample_count <= max_samples_per_case",
            "assert(display_point_count <= max_display_points",
            "numel(input_frequency_sweep) <= max_sweep_cases",
            "numel(representative_frequencies) >= 3",
            "numel(representative_frequencies) <= max_representative_cases",
            "assert(sample_count_case <= max_samples_per_case",
            "baseline_view_count = min(20, sample_count);",
            "representative_view_count = min(16, sample_count);",
            "rate_view_count = min(16, sample_count_case);",
            "representative_plot_rows = ceil(numel(representative_frequencies)/2);",
            "subplot(representative_plot_rows,2,representative_index);",
            "rate_plot_rows = ceil(numel(sample_rate_sweep)/2);",
            "subplot(rate_plot_rows,2,rate_index);",
        ):
            self.assertIn(guard, self.experiment)

        for accepted_short_count in range(5, 20):
            with self.subTest(accepted_short_count=accepted_short_count):
                self.assertLessEqual(min(20, accepted_short_count), accepted_short_count)
                self.assertLessEqual(min(16, accepted_short_count), accepted_short_count)
        for accepted_case_count in range(3, 9):
            with self.subTest(accepted_case_count=accepted_case_count):
                plot_capacity = math.ceil(accepted_case_count / 2) * 2
                self.assertGreaterEqual(plot_capacity, accepted_case_count)
                trial_rates = [800 + 100 * index for index in range(accepted_case_count)]
                trial_aliases = []
                for rate_hz in trial_rates:
                    fold_hz = 700 - self.matlab_nearest_integer(700 / rate_hz) * rate_hz
                    trial_aliases.append(abs(fold_hz))
                self.assertEqual(len(trial_aliases), accepted_case_count)
                self.assertTrue(
                    all(alias_hz <= rate_hz / 2 for alias_hz, rate_hz in zip(trial_aliases, trial_rates))
                )

        for control in ("A", "f_input", "fs", "duration"):
            self.assertRegex(
                self.experiment,
                rf"(?s)assert\(isscalar\({control}\)[^;]*?isnumeric\({control}\)[^;]*?"
                rf"~islogical\({control}\)[^;]*?isreal\({control}\)[^;]*?"
                rf"isfinite\({control}\)[^;]*?{control} > 0[^;]*?;",
            )
        self.assertRegex(
            self.experiment,
            r"(?s)assert\(isvector\(input_frequency_sweep\)[^;]*?"
            r"isnumeric\(input_frequency_sweep\)[^;]*?"
            r"~islogical\(input_frequency_sweep\)[^;]*?"
            r"isreal\(input_frequency_sweep\)[^;]*?"
            r"all\(isfinite\(input_frequency_sweep\)\)[^;]*?"
            r"all\(input_frequency_sweep >= 0\)[^;]*?;",
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
        for valid in (0.2, 700, 20000.0):
            with self.subTest(valid=valid):
                self.assertTrue(positive_finite_real_scalar(valid))

        self.assertIn("Restore `A = 1`, `f_input = 700`, `fs = 1000`", self.walkthrough)
        self.assertIn("20001 dense display\npoints, 5000 samples per record, 128", self.walkthrough)
        self.assertIn("analog anti-alias filter", self.walkthrough)

    def test_finite_noninteractive_base_matlab_compatibility(self):
        self.assertLessEqual(self.experiment.count("figure("), 6)
        self.assertNotRegex(self.experiment, r"(?m)^\s*(while|parfor)\b")
        for feature in (
            "pause(",
            "drawnow",
            "VideoWriter",
            "uicontrol",
            "webread",
            "tcpclient",
            "serialport",
        ):
            self.assertNotIn(feature, self.experiment)
        self.assertIn("for frequency_index = 1:numel(input_frequency_sweep)", self.experiment)
        self.assertIn("for rate_index = 1:numel(sample_rate_sweep)", self.experiment)
        self.assertIn(
            "Toolboxes, external data, helper functions, hardware, and network access: none",
            self.readme,
        )


if __name__ == "__main__":
    unittest.main()
