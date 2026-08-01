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
MODULE = ROOT / "modules" / "06-use-an-impulse-to-reveal-a-system"
MANIFEST_PATH = ROOT / "curriculum" / "modules.json"
GUIDING_QUESTION = "Why does an impulse response describe an LTI system?"
REQUIRED_ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def validate_p06_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P06 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P06 empty {name}")

    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P06"]
    if len(entries) != 1:
        return errors + [f"expected one P06 manifest entry, found {len(entries)}"]

    entry = entries[0]
    expected = {
        "number": 6,
        "id": "P06",
        "title": "Use an Impulse to Reveal a System",
        "guiding_question": GUIDING_QUESTION,
        "phase": 1,
        "phase_title": "Signals, Sampling, and Systems",
        "slug": "use-an-impulse-to-reveal-a-system",
        "folder": "modules/06-use-an-impulse-to-reveal-a-system",
        "status": "implemented",
        "implementation_batch": "P06",
    }
    for key, value in expected.items():
        if entry.get(key) != value:
            errors.append(f"P06 {key} must be {value!r}")
    return errors


def causal_convolution(values: list[float], response: list[float]) -> list[float]:
    count = len(values)
    return [
        sum(response[lag] * values[index - lag] for lag in range(index + 1))
        for index in range(count)
    ]


def direct_system_outputs(
    values: list[float],
    delay: int,
    average_length: int,
    echo_delay: int,
    echo_gain: float,
    radius: float,
    angle_rad: float,
    resonator_gain: float,
) -> list[list[float]]:
    count = len(values)
    delayed = [0.0] * count
    averaged = [0.0] * count
    echoed = [0.0] * count
    resonated = [0.0] * count
    for index in range(count):
        if index >= delay:
            delayed[index] = values[index - delay]
        averaged[index] = sum(values[max(0, index - average_length + 1) : index + 1]) / average_length
        echoed[index] = values[index]
        if index >= echo_delay:
            echoed[index] += echo_gain * values[index - echo_delay]
        previous_1 = resonated[index - 1] if index >= 1 else 0.0
        previous_2 = resonated[index - 2] if index >= 2 else 0.0
        resonated[index] = (
            2 * radius * math.cos(angle_rad) * previous_1
            - radius**2 * previous_2
            + resonator_gain * values[index]
        )
    return [delayed, averaged, echoed, resonated]


def circular_convolution(values: list[float], response: list[float]) -> list[float]:
    count = len(values)
    return [
        sum(response[lag] * values[(index - lag) % count] for lag in range(count))
        for index in range(count)
    ]


class P06ModuleTests(unittest.TestCase):
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
        self.assertEqual(validate_p06_contract(MODULE, self.manifest), [])
        for artifact in (self.readme, self.lesson, self.walkthrough, self.checks):
            self.assertIn(GUIDING_QUESTION, artifact)
        self.assertIn("Project 6 is now the latest implemented lesson", self.root_readme)
        self.assertIn("Projects 7–84", self.root_readme)
        self.assertIn("Project 6 is the next lesson after P05", self.start_here)
        self.assertRegex(
            self.module_index,
            r"\| \[P06\].*\| implemented \| 1 \| Use an Impulse to Reveal a System \|",
        )

    def test_contract_validator_rejects_missing_duplicate_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied_module = Path(temporary) / MODULE.name
            shutil.copytree(MODULE, copied_module)
            (copied_module / "experiment.m").unlink()
            self.assertIn("P06 missing experiment.m", validate_p06_contract(copied_module, self.manifest))

        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][5]["guiding_question"] = "generic system question"
        malformed["modules"][5]["slug"] = "wrong-module"
        malformed["modules"][5]["status"] = "scaffolded"
        errors = validate_p06_contract(MODULE, malformed)
        self.assertIn(f"P06 guiding_question must be {GUIDING_QUESTION!r}", errors)
        self.assertIn("P06 slug must be 'use-an-impulse-to-reveal-a-system'", errors)
        self.assertIn("P06 status must be 'implemented'", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][5]))
        self.assertEqual(validate_p06_contract(MODULE, duplicate), ["expected one P06 manifest entry, found 2"])
        self.assertEqual(validate_p06_contract(MODULE, {"modules": "bad"}), ["manifest modules must be a list"])
        self.assertEqual(validate_p06_contract(MODULE, {"modules": ["bad"]}), ["manifest module entries must be objects"])

    def test_deterministic_probe_and_visible_system_contract(self):
        for expression in (
            "random_seed = 606;",
            "random_stream = RandStream('mt19937ar', 'Seed', random_seed);",
            "probe_noise = randn(random_stream, 1, sample_count);",
            "impulse(1) = 1;",
            "h_delay",
            "h_moving_average",
            "h_echo_path",
            "h_resonator",
            "y[n] = sum_k h[k]*x[n-k]",
            "full_linear_convolution = conv(general_input_v",
        ):
            self.assertIn(expression, self.experiment)
        self.assertIn("P05 is the curriculum prerequisite", self.readme)

    def test_independent_impulse_responses_reveal_four_systems(self):
        count = 128
        delay = 7
        average_length = 5
        echo_delay = 13
        echo_gain = 0.4
        radius = 0.8
        angle_rad = 2 * math.pi * 0.1
        resonator_gain = 0.15
        impulse = [1.0] + [0.0] * (count - 1)
        direct = direct_system_outputs(
            impulse, delay, average_length, echo_delay, echo_gain,
            radius, angle_rad, resonator_gain,
        )
        self.assertEqual(direct[0][delay], 1.0)
        self.assertEqual(sum(abs(v) for i, v in enumerate(direct[0]) if i != delay), 0.0)
        self.assertTrue(all(abs(v - 1 / average_length) < 1e-15 for v in direct[1][:average_length]))
        self.assertAlmostEqual(sum(direct[1]), 1.0)
        self.assertEqual(direct[2][0], 1.0)
        self.assertEqual(direct[2][echo_delay], echo_gain)
        for index, value in enumerate(direct[3]):
            expected = (
                resonator_gain
                * radius**index
                * math.sin((index + 1) * angle_rad)
                / math.sin(angle_rad)
            )
            self.assertAlmostEqual(value, expected, places=14)
        zero_crossings = sum(
            left * right < 0 for left, right in zip(direct[3], direct[3][1:])
        )
        self.assertGreater(zero_crossings, 10)

    def test_direct_processing_matches_independent_convolution(self):
        count = 128
        values = [
            0.6 * math.cos(2 * math.pi * 5 * index / count + 0.2)
            + 0.2 * math.sin(2 * math.pi * 17 * index / count)
            for index in range(count)
        ]
        delay = 11
        average_length = 9
        echo_delay = 21
        echo_gain = 0.55
        radius = 0.86
        angle_rad = 2 * math.pi * 0.09
        resonator_gain = 0.15
        direct = direct_system_outputs(
            values, delay, average_length, echo_delay, echo_gain,
            radius, angle_rad, resonator_gain,
        )
        responses = direct_system_outputs(
            [1.0] + [0.0] * (count - 1), delay, average_length,
            echo_delay, echo_gain, radius, angle_rad, resonator_gain,
        )
        for direct_case, response in zip(direct, responses):
            reconstructed = causal_convolution(values, response)
            self.assertLess(max(abs(a - b) for a, b in zip(direct_case, reconstructed)), 2e-15)

        for marker in (
            "Process the general signal directly using the same four system rules",
            "Rebuild every output from weighted, delayed input copies",
            "max_abs_error_v",
            "all(max_abs_error_v < comparison_tolerance_v)",
            "Direct processing and convolution agree to numerical precision",
        ):
            self.assertIn(marker, self.experiment)

    def test_four_system_models_are_linear_and_time_invariant(self):
        count = 128
        first_input = [
            0.7 * math.cos(2 * math.pi * 3 * index / count + 0.1)
            for index in range(count)
        ]
        second_input = [
            0.25 * math.sin(2 * math.pi * 19 * index / count)
            + (0.4 if 37 <= index < 45 else 0.0)
            for index in range(count)
        ]
        scale_first = 1.6
        scale_second = -0.45
        system_parameters = (11, 9, 21, 0.55, 0.86, 2 * math.pi * 0.09, 0.15)

        first_outputs = direct_system_outputs(first_input, *system_parameters)
        second_outputs = direct_system_outputs(second_input, *system_parameters)
        combined_input = [
            scale_first * first + scale_second * second
            for first, second in zip(first_input, second_input)
        ]
        combined_outputs = direct_system_outputs(combined_input, *system_parameters)
        for system_index, (combined, first, second) in enumerate(
            zip(combined_outputs, first_outputs, second_outputs), start=1
        ):
            expected = [
                scale_first * first_value + scale_second * second_value
                for first_value, second_value in zip(first, second)
            ]
            self.assertLess(
                max(abs(actual - wanted) for actual, wanted in zip(combined, expected)),
                1e-12,
                f"system {system_index} violated superposition",
            )

        shift = 9
        shifted_input = [0.0] * shift + first_input[:-shift]
        shifted_outputs = direct_system_outputs(shifted_input, *system_parameters)
        for system_index, (shifted, original) in enumerate(
            zip(shifted_outputs, first_outputs), start=1
        ):
            expected = [0.0] * shift + original[:-shift]
            self.assertLess(
                max(abs(actual - wanted) for actual, wanted in zip(shifted, expected)),
                1e-12,
                f"system {system_index} violated time invariance",
            )

    def test_two_sweeps_change_one_physical_mechanism(self):
        for marker in (
            "Parameter sweep 1 - change only echo delay",
            "echo_delay_sweep_samples = [8 32 64]",
            "echo_delay_sweep_ms = 1000*echo_delay_sweep_samples/fs;",
            "Parameter sweep 2 - change only resonator memory",
            "resonator_radius_sweep = [0.25 0.70 0.92]",
            "resonator_time_constant_samples(sweep_index) = -1/log(radius_case);",
            "all(diff(resonator_time_constant_samples) > 0)",
        ):
            self.assertIn(marker, self.experiment)

        delays_ms = [1000 * delay / 1000 for delay in (8, 32, 64)]
        self.assertEqual(delays_ms, [8.0, 32.0, 64.0])
        time_constants = [-1 / math.log(pole) for pole in (0.25, 0.70, 0.92)]
        self.assertTrue(all(right > left for left, right in zip(time_constants, time_constants[1:])))
        angle_rad = 2 * math.pi * 0.09
        for radius in (0.25, 0.70, 0.92):
            response = [
                0.15
                * radius**index
                * math.sin((index + 1) * angle_rad)
                / math.sin(angle_rad)
                for index in range(256)
            ]
            zero_crossings = sum(
                left * right < 0 for left, right in zip(response, response[1:])
            )
            self.assertGreater(zero_crossings, 20)
        self.assertGreater(abs(response[64]), 1e-4)

    def test_broken_circular_case_and_recovery(self):
        count = 128
        values = [math.sin(2 * math.pi * 7 * index / count) + 0.3 for index in range(count)]
        response = [0.0] * count
        response[0] = 1.0
        response[24] = 0.55
        linear = causal_convolution(values, response)
        circular = circular_convolution(values, response)
        error = [a - b for a, b in zip(circular, linear)]
        self.assertGreater(max(map(abs, error)), 0.05)
        self.assertGreater(sum(v * v for v in error[:24]), 1e-3)
        self.assertTrue(all(abs(a - b) < 1e-15 for a, b in zip(linear, causal_convolution(values, response))))

        for marker in (
            "Deliberately broken case - unpadded FFT creates circular convolution",
            "y_circular[n] = sum_k h[k]*x[mod(n-k,N)]",
            "broken_circular_output_v = real(ifft(fft(general_input_v, sample_count).*",
            "correct_linear_full_v = conv(general_input_v, h_echo_path);",
            "broken_max_error_v > 0.05",
            "Linear convolution must recover the direct echo-path output",
        ):
            self.assertIn(marker, self.experiment)

    def test_required_views_labels_metrics_and_concept_first_documents(self):
        for view in (
            "two probes",
            "impulse responses reveal the systems",
            "direct rule equals convolution",
            "numerical agreement metric",
            "echo delay moves one response tap",
            "the pole controls response memory",
            "circular wraparound is not the LTI output",
        ):
            self.assertIn(view, self.experiment)
        for label in (
            "Sample index n",
            "Time (s)",
            "Input voltage x[n] (V)",
            "Lag k (samples)",
            "h[k] (V/V)",
            "Output voltage y[n] (V)",
            "Maximum absolute error (V)",
            "Circular-minus-linear error (V)",
        ):
            self.assertIn(label, self.experiment)

        combined = "\n".join((self.lesson, self.walkthrough, self.checks)).lower()
        for concept in (
            "linearity",
            "time invariance",
            "weighted",
            "delayed",
            "moving average",
            "echo",
            "resonator",
            "circular convolution",
            "radar",
            "base matlab",
        ):
            self.assertIn(concept, combined)
        for limiting_case in (
            "Delay `0 samples`",
            "Moving-average length `1`",
            "Echo gain `0`",
            "Resonator radius `r = 0`",
            "approaches `1`",
            "A non-LTI system",
            "Infinite observation",
        ):
            self.assertIn(limiting_case, self.lesson)
        for section in ("## Baseline", "## Sweep 1", "## Sweep 2", "## Broken case", "## Recovery", "## Concept connection"):
            self.assertIn(section, self.walkthrough)
        for section in ("## Baseline observation checks", "## Predict, then verify", "## Interpretation checks", "## Failure classification", "## Teach-back completion"):
            self.assertIn(section, self.checks)

    def test_no_placeholder_or_unexplained_black_box_regression(self):
        implementation = "\n".join((self.experiment, self.readme, self.lesson, self.walkthrough, self.checks))
        self.assertIsNone(re.search(r"\b(TODO|TBD|FIXME|lorem ipsum|coming soon)\b", implementation, re.I))
        for prohibited in (
            "filter(",
            "impz(",
            "freqz(",
            "dimpulse(",
            "lsim(",
            "cconv(",
            "phased.",
            "dsp.",
            "readtable(",
            "webread(",
        ):
            self.assertNotIn(prohibited, implementation)
        self.assertIn("base MATLAB only", self.readme)
        self.assertIn("Each system operation is visible", self.experiment)
        self.assertIn("after the wraparound equation is stated", self.readme)

    def test_malformed_controls_and_resource_bounds_precede_allocation(self):
        self.assertEqual(self.scalar_assignment("max_samples"), 4096)
        self.assertEqual(self.scalar_assignment("max_sweep_cases"), 8)
        self.assertEqual(self.scalar_assignment("system_count"), 4)
        for guard in (
            "max_samples == floor(max_samples) && max_samples == 4096",
            "max_sweep_cases == floor(max_sweep_cases) && max_sweep_cases == 8",
            "isfinite(system_count) && system_count == 4",
            "assert(sample_count <= max_samples",
            "delay_samples < sample_count",
            "moving_average_length <= min(64, sample_count)",
            "echo_delay_samples < sample_count/2",
            "resonator_radius < 1",
            "resonator_frequency_hz < fs/2",
            "abs(sin(resonator_angle_rad)) > 1e-6",
            "numel(echo_delay_sweep_samples) <= max_sweep_cases",
            "numel(resonator_radius_sweep) <= max_sweep_cases",
        ):
            self.assertIn(guard, self.experiment)

        first_signal_allocation = self.experiment.index("impulse = zeros(1, sample_count);")
        self.assertLess(self.experiment.index("assert(sample_count <= max_samples"), first_signal_allocation)
        self.assertLess(self.experiment.index("echo_delay_samples < sample_count/2"), first_signal_allocation)
        self.assertLess(
            self.experiment.index("numel(echo_delay_sweep_samples) <= max_sweep_cases"),
            self.experiment.index("echo_sweep_outputs_v = zeros"),
        )
        self.assertLess(
            self.experiment.index("numel(resonator_radius_sweep) <= max_sweep_cases"),
            self.experiment.index("resonator_sweep_responses = zeros"),
        )

        def finite_positive_real(value: object) -> bool:
            return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0

        for malformed in (0, -1, math.nan, math.inf, 1 + 1j, True):
            with self.subTest(malformed=malformed):
                self.assertFalse(finite_positive_real(malformed))
        for valid in (0.001, 8, 4096.0):
            self.assertTrue(finite_positive_real(valid))

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback_scope(self):
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
            "save(",
            "delete(",
            "fopen(",
        ):
            self.assertNotIn(feature, self.experiment)
        self.assertNotIn(".learning", self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*(clear|close\s+all|clc)\s*;")
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")
        self.assertIn("prior_p06_figures = findall(groot", self.experiment)
        self.assertEqual(
            self.experiment.count("'Tag', p06_figure_tag"),
            self.experiment.count("figure(") + 1,
        )
        self.assertIn("Every loop is finite and bounded", self.experiment)
        self.assertIn("stop the finite script with Ctrl+C", self.walkthrough)
        self.assertIn("no partial file or learner-state cleanup is needed", self.walkthrough)
        self.assertIn("Re-running from private seed 606 recovers", self.walkthrough)
        self.assertIn("There is no persistent file or learner-state mutation", self.checks)
        self.assertIn("no toolbox, helper function, external data", self.readme)


if __name__ == "__main__":
    unittest.main()
