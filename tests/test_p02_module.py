from __future__ import annotations

import cmath
import copy
import json
import math
import re
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "02-see-sampling-as-taking-measurements"
MANIFEST_PATH = ROOT / "curriculum" / "modules.json"
REQUIRED_ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
GUIDING_QUESTION = (
    "What information is lost when a continuous-looking signal is represented by discrete samples?"
)


def validate_p02_contract(module_dir: Path, manifest: dict) -> list[str]:
    """Return deterministic P02 contract failures for positive and negative tests."""
    errors: list[str] = []
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return ["manifest modules must be a list"]
    if any(not isinstance(entry, dict) for entry in modules):
        return ["manifest module entries must be objects"]

    matches = [entry for entry in modules if entry.get("id") == "P02"]
    if len(matches) != 1:
        return [f"expected one P02 manifest entry, found {len(matches)}"]

    entry = matches[0]
    expected_identity = {
        "number": 2,
        "title": "See Sampling as Taking Measurements",
        "phase": 1,
        "phase_title": "Signals, Sampling, and Systems",
        "slug": "see-sampling-as-taking-measurements",
        "guiding_question": GUIDING_QUESTION,
        "folder": "modules/02-see-sampling-as-taking-measurements",
        "status": "implemented",
        "implementation_batch": "P02",
    }
    for field, expected in expected_identity.items():
        if entry.get(field) != expected:
            errors.append(f"P02 {field} must be {expected!r}")

    for name in REQUIRED_ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P02 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P02 empty {name}")
    return errors


class P02ModuleTests(unittest.TestCase):
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

    def test_artifact_completeness_and_manifest_identity(self):
        self.assertEqual(validate_p02_contract(MODULE, self.manifest), [])
        for artifact in (self.readme, self.lesson, self.walkthrough, self.checks):
            self.assertIn(GUIDING_QUESTION, artifact)
        self.assertIn("Project 2 is now implemented", self.root_readme)
        self.assertIn("Project 2 is the next available\nlesson", self.start_here)
        self.assertRegex(
            self.module_index,
            r"\| \[P02\].*\| implemented \| 1 \| See Sampling as Taking Measurements \|",
        )

    def test_contract_validator_rejects_missing_duplicate_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied_module = Path(temporary) / MODULE.name
            shutil.copytree(MODULE, copied_module)
            (copied_module / "checks.md").unlink()
            self.assertIn(
                "P02 missing checks.md",
                validate_p02_contract(copied_module, self.manifest),
            )

        malformed_manifest = copy.deepcopy(self.manifest)
        malformed_manifest["modules"][1]["guiding_question"] = "placeholder"
        malformed_manifest["modules"][1]["slug"] = "wrong-module"
        malformed_manifest["modules"][1]["status"] = "scaffolded"
        errors = validate_p02_contract(MODULE, malformed_manifest)
        self.assertIn(f"P02 guiding_question must be {GUIDING_QUESTION!r}", errors)
        self.assertIn("P02 slug must be 'see-sampling-as-taking-measurements'", errors)
        self.assertIn("P02 status must be 'implemented'", errors)

        duplicate_manifest = copy.deepcopy(self.manifest)
        duplicate_manifest["modules"].append(copy.deepcopy(duplicate_manifest["modules"][1]))
        self.assertEqual(
            validate_p02_contract(MODULE, duplicate_manifest),
            ["expected one P02 manifest entry, found 2"],
        )
        self.assertEqual(
            validate_p02_contract(MODULE, {"modules": "not-a-list"}),
            ["manifest modules must be a list"],
        )
        self.assertEqual(
            validate_p02_contract(MODULE, {"modules": ["not-an-object"]}),
            ["manifest module entries must be objects"],
        )

    def test_deterministic_baseline_measurement_contract(self):
        amplitude = self.scalar_assignment("A")
        frequency_hz = self.scalar_assignment("f0")
        duration_s = self.scalar_assignment("duration")
        sample_rate_hz = self.scalar_assignment("fs_baseline")
        reference_rate_hz = self.scalar_assignment("fs_reference")
        phase_rad = math.pi / 5

        self.assertRegex(self.experiment, r"random_seed\s*=\s*202\s*;")
        self.assertIn("rng(random_seed, 'twister')", self.experiment)
        self.assertIn("x_dense = A*cos(2*pi*f0*t_dense + phi);", self.experiment)
        self.assertIn("x_baseline = A*cos(2*pi*f0*t_baseline + phi);", self.experiment)

        sample_count = round(duration_s * sample_rate_hz)
        self.assertEqual(sample_count, 80)
        self.assertGreater(sample_rate_hz, 2 * frequency_hz)
        self.assertEqual(round(duration_s * reference_rate_hz) + 1, 2001)
        sample_times = [index / sample_rate_hz for index in range(sample_count)]
        measured = [
            amplitude * math.cos(2 * math.pi * frequency_hz * time + phase_rad)
            for time in sample_times
        ]
        independent_reference = [
            (
                amplitude
                * cmath.exp(1j * (2 * math.pi * frequency_hz * time + phase_rad))
            ).real
            for time in sample_times
        ]
        self.assertLess(
            max(abs(actual - expected) for actual, expected in zip(measured, independent_reference)),
            1e-12,
        )
        self.assertAlmostEqual(sample_rate_hz / frequency_hz, 80 / 7)

    def test_two_sweeps_and_visible_sampling_regimes(self):
        for marker in (
            "Parameter sweep 1 - far above, near, and below twice the tone frequency",
            "sample_rates = [80 16 12]",
            "numel(sample_rates) == 3",
            "sample_rates(1) > 4*f0",
            "sample_rates(2) > 2*f0 && sample_rates(2) < 3*f0",
            "sample_rates(3) < 2*f0",
            "rate_sweep_rmse",
            "Parameter sweep 2 - move the measurement clock",
            "sample_offset_fractions = [0 0.25 0.50]",
            "offset_sweep_rmse",
        ):
            self.assertIn(marker, self.experiment)

        frequency_hz = self.scalar_assignment("f0")
        rates_hz = (80.0, 16.0, 12.0)
        self.assertGreater(rates_hz[0], 4 * frequency_hz)
        self.assertGreater(rates_hz[1], 2 * frequency_hz)
        self.assertLess(rates_hz[1], 3 * frequency_hz)
        self.assertLess(rates_hz[2], 2 * frequency_hz)
        self.assertEqual(
            [round(rate / frequency_hz, 3) for rate in rates_hz],
            [11.429, 2.286, 1.714],
        )

        amplitude = self.scalar_assignment("A")
        duration_s = self.scalar_assignment("duration")
        reference_rate_hz = self.scalar_assignment("fs_reference")
        phase_rad = math.pi / 5

        def explicit_linear_rmse(rate_hz: float) -> float:
            sample_count = round(duration_s * rate_hz)
            sample_times = [index / rate_hz for index in range(sample_count)]
            samples = [
                amplitude * math.cos(2 * math.pi * frequency_hz * time + phase_rad)
                for time in sample_times
            ]
            dense_count = math.floor(sample_times[-1] * reference_rate_hz) + 1
            squared_errors: list[float] = []
            for dense_index in range(dense_count):
                time = dense_index / reference_rate_hz
                segment = min(math.floor(time * rate_hz), sample_count - 2)
                alpha = (time - sample_times[segment]) / (
                    sample_times[segment + 1] - sample_times[segment]
                )
                linear_value = (
                    (1 - alpha) * samples[segment] + alpha * samples[segment + 1]
                )
                true_value = amplitude * math.cos(
                    2 * math.pi * frequency_hz * time + phase_rad
                )
                squared_errors.append((linear_value - true_value) ** 2)
            return math.sqrt(sum(squared_errors) / len(squared_errors))

        rate_rmses = [explicit_linear_rmse(rate) for rate in rates_hz]
        self.assertLess(rate_rmses[0], rate_rmses[1])
        self.assertLess(rate_rmses[1], rate_rmses[2])
        self.assertEqual([round(value, 6) for value in rate_rmses], [0.019284, 0.411372, 0.659829])

        offset_rate_hz = self.scalar_assignment("fs_offset")
        zero_offset = math.cos(phase_rad)
        half_sample_offset = math.cos(
            2 * math.pi * frequency_hz * (0.5 / offset_rate_hz) + phase_rad
        )
        self.assertNotAlmostEqual(zero_offset, half_sample_offset)

    def test_broken_case_proves_multiple_continuous_candidates_share_samples(self):
        amplitude = self.scalar_assignment("A")
        frequency_hz = self.scalar_assignment("f0")
        broken_rate_hz = self.scalar_assignment("fs_bad")
        duration_s = self.scalar_assignment("duration")
        phase_rad = math.pi / 5

        for expression in (
            "f_alias_low = fs_bad - f0;",
            "phi_alias_low = -phi;",
            "f_alias_high = f0 + fs_bad;",
            "x_alias_low_at_samples = A*cos(2*pi*f_alias_low*t_bad + phi_alias_low);",
            "x_alias_high_at_samples = A*cos(2*pi*f_alias_high*t_bad + phi);",
            "low_alias_sample_error",
            "high_alias_sample_error",
            "assert(fs_reference > 2*f_alias_high",
            "alias_argument_scale",
            "alias_tolerance",
        ):
            self.assertIn(expression, self.experiment)

        self.assertGreater(broken_rate_hz, frequency_hz)
        self.assertLess(broken_rate_hz, 2 * frequency_hz)
        low_hz = broken_rate_hz - frequency_hz
        high_hz = frequency_hz + broken_rate_hz
        times = [
            index / broken_rate_hz
            for index in range(round(duration_s * broken_rate_hz))
        ]
        original = [
            amplitude * math.cos(2 * math.pi * frequency_hz * time + phase_rad)
            for time in times
        ]
        low_candidate = [
            amplitude * math.cos(2 * math.pi * low_hz * time - phase_rad)
            for time in times
        ]
        high_candidate = [
            amplitude * math.cos(2 * math.pi * high_hz * time + phase_rad)
            for time in times
        ]
        self.assertLess(
            max(abs(true - alias) for true, alias in zip(original, low_candidate)),
            1e-12,
        )
        self.assertLess(
            max(abs(true - alias) for true, alias in zip(original, high_candidate)),
            1e-12,
        )
        self.assertEqual((low_hz, frequency_hz, high_hz), (5.0, 7.0, 19.0))
        self.assertGreater(self.scalar_assignment("fs_reference"), 2 * high_hz)

        long_frequency_hz = 1.0
        long_rate_hz = 1.9
        long_duration_s = 1000.0
        long_times = [
            index / long_rate_hz
            for index in range(round(long_duration_s * long_rate_hz))
        ]
        long_low_hz = long_rate_hz - long_frequency_hz
        long_high_hz = long_frequency_hz + long_rate_hz
        long_original = [
            math.cos(2 * math.pi * long_frequency_hz * time + phase_rad)
            for time in long_times
        ]
        long_low = [
            math.cos(2 * math.pi * long_low_hz * time - phase_rad)
            for time in long_times
        ]
        long_high = [
            math.cos(2 * math.pi * long_high_hz * time + phase_rad)
            for time in long_times
        ]
        long_error = max(
            max(abs(true - alias) for true, alias in zip(long_original, long_low)),
            max(abs(true - alias) for true, alias in zip(long_original, long_high)),
        )
        argument_scale = 1 + max(
            abs(2 * math.pi * frequency * time + candidate_phase)
            for frequency, candidate_phase in (
                (long_frequency_hz, phase_rad),
                (long_low_hz, -phase_rad),
                (long_high_hz, phase_rad),
            )
            for time in long_times
        )
        tolerance = min(1e-9, 64 * math.ulp(1.0) * argument_scale)
        self.assertGreater(long_error, 1e-12)
        self.assertLess(long_error, tolerance)

    def test_interpolation_operation_and_labeled_metrics_are_explicit(self):
        for expression in (
            "baseline_segment = floor(t_baseline_reconstruction*fs_baseline) + 1;",
            "x_baseline_linear = (1-alpha).*x_baseline(baseline_segment)",
            "sweep_segment = floor(t_sweep_reconstruction*fs_sweep) + 1;",
            "offset_segment = floor((t_offset_reconstruction-t_offset(1))*fs_offset) + 1;",
            "baseline_linear_rmse",
            "measurement_error",
        ):
            self.assertIn(expression, self.experiment)

        for label in (
            "Time (s)",
            "Amplitude (a.u.)",
            "Sample index n (samples)",
            "Measured amplitude x[n] (a.u.)",
            "measurement rate",
            "Nyquist limit",
            "samples per cycle",
            "linear interpolation RMSE",
        ):
            self.assertIn(label, self.experiment)

    def test_concept_first_documentation_and_completion_rubric(self):
        combined_docs = "\n".join((self.lesson, self.walkthrough, self.checks))
        for concept in (
            "measurement",
            "between",
            "interpolation",
            "Nyquist",
            "bandlimited",
            "anti-alias filter",
            "fast-time",
            "slow-time",
            "broken case",
            "base MATLAB",
        ):
            self.assertIn(concept.lower(), combined_docs.lower())

        for section in (
            "## Baseline",
            "## Sweep 1",
            "## Sweep 2",
            "## Broken case",
            "## Recovery",
        ):
            self.assertIn(section, self.walkthrough)
        self.assertIn("## Predict, then verify", self.checks)
        self.assertIn("## Teach-back completion", self.checks)
        self.assertIn("two or more different\n  continuous signals", self.checks)

    def test_no_placeholder_or_unexplained_black_box_regression(self):
        implementation_text = "\n".join(
            (self.experiment, self.lesson, self.walkthrough, self.checks)
        )
        self.assertIsNone(
            re.search(
                r"\b(TODO|TBD|FIXME|lorem ipsum|coming soon)\b",
                implementation_text,
                re.I,
            )
        )
        for prohibited_call in (
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
        self.assertIn("requires no toolbox", self.lesson)
        self.assertIn("Sampling, interpolation,\nand every alias candidate are written as explicit arithmetic", self.lesson)

    def test_resource_bounds_malformed_controls_and_recovery_contract(self):
        max_reference_points = self.scalar_assignment("max_reference_points")
        max_measurement_samples = self.scalar_assignment("max_measurement_samples")
        max_sweep_cases = self.scalar_assignment("max_sweep_cases")
        self.assertEqual(max_reference_points, 20001)
        self.assertEqual(max_measurement_samples, 5000)
        self.assertEqual(max_sweep_cases, 12)
        for guard in (
            "assert(reference_point_count <= max_reference_points",
            "assert(baseline_sample_count <= max_measurement_samples",
            "assert(numel(sample_rates) == 3",
            "assert(sweep_sample_count <= max_measurement_samples",
            "assert(numel(sample_offset_fractions) <= max_sweep_cases",
            "assert(offset_sample_count >= 2 && offset_sample_count <= max_measurement_samples",
            "assert(bad_sample_count <= max_measurement_samples",
        ):
            self.assertIn(guard, self.experiment)

        for control in ("A", "f0", "duration", "fs_bad"):
            self.assertRegex(
                self.experiment,
                rf"(?s)assert\(isscalar\({control}\)[^;]*?isnumeric\({control}\)[^;]*?"
                rf"~islogical\({control}\)[^;]*?isreal\({control}\)[^;]*?"
                rf"isfinite\({control}\)[^;]*?{control} > 0[^;]*?;",
            )
        for control in ("fs_reference", "fs_baseline", "fs_offset"):
            self.assertRegex(
                self.experiment,
                rf"(?s)assert\(isscalar\({control}\)[^;]*?isnumeric\({control}\)[^;]*?"
                rf"~islogical\({control}\)[^;]*?isreal\({control}\)[^;]*?"
                rf"isfinite\({control}\)[^;]*?{control} > 2\*f0[^;]*?;",
            )
        self.assertRegex(
            self.experiment,
            r"(?s)assert\(isscalar\(phi\)[^;]*?isnumeric\(phi\)[^;]*?~islogical\(phi\)[^;]*?"
            r"isreal\(phi\)[^;]*?isfinite\(phi\)[^;]*?;",
        )
        self.assertRegex(
            self.experiment,
            r"(?s)assert\(isvector\(sample_rates\)[^;]*?isnumeric\(sample_rates\)[^;]*?"
            r"~islogical\(sample_rates\)[^;]*?isreal\(sample_rates\)[^;]*?"
            r"all\(isfinite\(sample_rates\)\)[^;]*?all\(sample_rates > 0\)[^;]*?;",
        )
        self.assertRegex(
            self.experiment,
            r"(?s)assert\(isvector\(sample_offset_fractions\)[^;]*?"
            r"isnumeric\(sample_offset_fractions\)[^;]*?~islogical\(sample_offset_fractions\)[^;]*?"
            r"isreal\(sample_offset_fractions\)[^;]*?all\(isfinite\(sample_offset_fractions\)\)[^;]*?"
            r"all\(sample_offset_fractions >= 0\)[^;]*?all\(sample_offset_fractions < 1\)[^;]*?;",
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
        for valid in (0.5, 12, 2000.0):
            with self.subTest(valid=valid):
                self.assertTrue(positive_finite_real_scalar(valid))

        self.assertIn("Restore `fs_baseline = 80`", self.walkthrough)
        self.assertIn("20001 reference points, 5000\nmeasurements", self.walkthrough)
        self.assertIn("exactly three rate cases, and 12 clock-offset cases", self.walkthrough)
        self.assertIn("f0 < fs_bad < 2*f0", self.walkthrough)
        self.assertIn("above `2*(f0 + fs_bad)`", self.walkthrough)

        maximum_interpolation_evaluations = max_reference_points * (
            1 + 3 + max_sweep_cases
        )
        self.assertEqual(maximum_interpolation_evaluations, 320016)
        self.assertNotIn("for segment =", self.experiment)

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
        self.assertIn("for rate_index = 1:numel(sample_rates)", self.experiment)
        self.assertIn("for offset_index = 1:numel(sample_offset_fractions)", self.experiment)
        self.assertIn("Toolboxes, external data, helper functions, hardware, and network access: none", self.readme)


if __name__ == "__main__":
    unittest.main()
