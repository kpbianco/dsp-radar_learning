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
MODULE = ROOT / "modules" / "07-understand-convolution-as-echo-addition"
MANIFEST_PATH = ROOT / "curriculum" / "modules.json"
GUIDING_QUESTION = "What is convolution actually doing at each output sample?"
REQUIRED_ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def validate_p07_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P07 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P07 empty {name}")

    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P07"]
    if len(entries) != 1:
        return errors + [f"expected one P07 manifest entry, found {len(entries)}"]

    expected = {
        "number": 7,
        "id": "P07",
        "title": "Understand Convolution as Echo Addition",
        "guiding_question": GUIDING_QUESTION,
        "phase": 1,
        "phase_title": "Signals, Sampling, and Systems",
        "slug": "understand-convolution-as-echo-addition",
        "folder": "modules/07-understand-convolution-as-echo-addition",
        "status": "implemented",
        "implementation_batch": "P07",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P07 {key} must be {value!r}")
    return errors


def full_convolution(values: list[float], response: list[float]) -> list[float]:
    output = [0.0] * (len(values) + len(response) - 1)
    for input_index, input_value in enumerate(values):
        for lag, response_value in enumerate(response):
            output[input_index + lag] += input_value * response_value
    return output


def shifted_copy_sum(
    values: list[float], delays: list[int], gains: list[float]
) -> tuple[list[list[float]], list[float]]:
    count = len(values) + max(delays)
    contributions = [[0.0] * count for _ in delays]
    for path, (delay, gain) in enumerate(zip(delays, gains)):
        for input_index, input_value in enumerate(values):
            contributions[path][input_index + delay] = gain * input_value
    output = [sum(path[index] for path in contributions) for index in range(count)]
    return contributions, output


def broken_overwrite(
    values: list[float], delays: list[int], gains: list[float]
) -> list[float]:
    output = [0.0] * (len(values) + max(delays))
    for delay, gain in zip(delays, gains):
        for input_index, input_value in enumerate(values):
            if input_value != 0:
                output[input_index + delay] = gain * input_value
    return output


class P07ModuleTests(unittest.TestCase):
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

    def baseline_fixture(self) -> tuple[list[float], list[int], list[float]]:
        values = [0.0] * 40
        values[5:12] = [0.25, 0.50, 0.75, 1.00, 0.75, 0.50, 0.25]
        return values, [0, 5, 9], [1.0, 0.6, -0.35]

    def test_artifact_completeness_manifest_identity_and_catalogs(self):
        self.assertEqual(validate_p07_contract(MODULE, self.manifest), [])
        for artifact in (self.readme, self.lesson, self.walkthrough, self.checks):
            self.assertIn(GUIDING_QUESTION, artifact)
        self.assertIn("Project 7 is the latest implemented lesson", self.root_readme)
        self.assertIn("Projects 8–84", self.root_readme)
        self.assertIn("Project 7 is the next lesson after P06", self.start_here)
        self.assertRegex(
            self.module_index,
            r"\| \[P07\].*\| implemented \| 1 \| Understand Convolution as Echo Addition \|",
        )

    def test_contract_validator_rejects_missing_duplicate_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied_module = Path(temporary) / MODULE.name
            shutil.copytree(MODULE, copied_module)
            (copied_module / "experiment.m").unlink()
            self.assertIn("P07 missing experiment.m", validate_p07_contract(copied_module, self.manifest))

        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][6]["guiding_question"] = "generic convolution question"
        malformed["modules"][6]["slug"] = "wrong-module"
        malformed["modules"][6]["status"] = "scaffolded"
        errors = validate_p07_contract(MODULE, malformed)
        self.assertIn(f"P07 guiding_question must be {GUIDING_QUESTION!r}", errors)
        self.assertIn("P07 slug must be 'understand-convolution-as-echo-addition'", errors)
        self.assertIn("P07 status must be 'implemented'", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][6]))
        self.assertEqual(validate_p07_contract(MODULE, duplicate), ["expected one P07 manifest entry, found 2"])
        self.assertEqual(validate_p07_contract(MODULE, {"modules": "bad"}), ["manifest modules must be a list"])
        self.assertEqual(validate_p07_contract(MODULE, {"modules": ["bad"]}), ["manifest module entries must be objects"])

    def test_deterministic_input_and_visible_convolution_contract(self):
        for marker in (
            "random_seed = 707;",
            "random_stream = RandStream('mt19937ar', 'Seed', random_seed);",
            "pulse_shape_v = [0.25 0.50 0.75 1.00 0.75 0.50 0.25]",
            "tap_delays_samples = [0 5 9]",
            "tap_gains = [1.00 0.60 -0.35]",
            "echo_contributions_v(path_index, output_index) =",
            "manual_echo_sum_v = sum(echo_contributions_v, 1);",
            "y[n] = sum_k h[k]*x[n-k]",
            "explicit_convolution_v(output_index) =",
            "conv_output_v = conv(input_pulse_v, channel_impulse_response);",
        ):
            self.assertIn(marker, self.experiment)
        self.assertIn("P06 is the prerequisite", self.readme)
        self.assertIn("base MATLAB", self.readme)

    def test_independent_shifted_copies_equal_full_convolution(self):
        values, delays, gains = self.baseline_fixture()
        contributions, manual = shifted_copy_sum(values, delays, gains)
        response = [0.0] * 10
        for delay, gain in zip(delays, gains):
            response[delay] = gain
        expected = full_convolution(values, response)
        self.assertEqual(len(manual), 49)
        self.assertEqual(manual, expected)
        for path, (delay, gain) in enumerate(zip(delays, gains)):
            nonzero = [index for index, value in enumerate(contributions[path]) if value]
            self.assertEqual(nonzero, list(range(5 + delay, 12 + delay)))
            self.assertAlmostEqual(max(map(abs, contributions[path])), abs(gain))

        selected = [path[14] for path in contributions]
        for actual, expected_term in zip(selected, [0.0, 0.45, -0.0875]):
            self.assertAlmostEqual(actual, expected_term)
        self.assertAlmostEqual(sum(selected), 0.3625)
        self.assertEqual([8 + delay for delay in delays], [8, 13, 17])

    def test_echo_addition_is_linear_for_asymmetric_signed_inputs(self):
        delays = [0, 2, 5]
        gains = [0.8, -0.45, 0.2]
        response = [0.0] * 6
        for delay, gain in zip(delays, gains):
            response[delay] = gain

        first = [1.0, -0.25, 0.5, 0.0, 0.75, -0.4]
        second = [0.1, 0.3, -0.2, 0.6, 0.0, -0.8]
        first_scale = -1.7
        second_scale = 0.35
        mixed = [
            first_scale * first_value + second_scale * second_value
            for first_value, second_value in zip(first, second)
        ]

        mixed_contributions, mixed_output = shifted_copy_sum(mixed, delays, gains)
        first_output = full_convolution(first, response)
        second_output = full_convolution(second, response)
        expected_mixed = [
            first_scale * first_value + second_scale * second_value
            for first_value, second_value in zip(first_output, second_output)
        ]

        for actual, expected in zip(mixed_output, full_convolution(mixed, response)):
            self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(mixed_output, expected_mixed):
            self.assertAlmostEqual(actual, expected)
        for output_index, output_value in enumerate(mixed_output):
            self.assertAlmostEqual(
                output_value,
                sum(path[output_index] for path in mixed_contributions),
            )
        self.assertNotEqual(
            mixed_output,
            full_convolution(list(reversed(mixed)), response),
            "the asymmetric fixture must expose an accidental input reversal",
        )

    def test_small_sequence_animation_is_one_sum_per_output_sample(self):
        values = [1.0, 0.5, -0.25, 0.0, 0.0, 0.0, 0.0, 0.0]
        response = [1.0, 0.0, 0.6, -0.35]
        expected = full_convolution(values, response)
        self.assertEqual(len(expected), 11)
        for index, output_value in enumerate(expected):
            products = [
                response[lag] * values[index - lag]
                for lag in range(len(response))
                if 0 <= index - lag < len(values)
            ]
            self.assertAlmostEqual(sum(products), output_value)
        for marker in (
            "Bounded overlap-and-sum animation for a small sequence",
            "animation_frame_count = numel(animation_input_v) +",
            "animation_frame_count <= max_animation_frames",
            "animation_output_v(frame_index) = sum(animation_products_v(frame_index,:));",
            "Add the upper products",
        ):
            self.assertIn(marker, self.experiment)

    def test_two_sweeps_change_one_physical_mechanism(self):
        values, delays, gains = self.baseline_fixture()
        delay_outputs = []
        for middle_delay in (3, 5, 7):
            _, output = shifted_copy_sum(values, [delays[0], middle_delay, delays[2]], gains)
            delay_outputs.append(output)
        middle_path_peaks = [8 + delay for delay in (3, 5, 7)]
        self.assertEqual(middle_path_peaks, [11, 13, 15])
        self.assertTrue(all(left != right for left, right in zip(delay_outputs, delay_outputs[1:])))

        gain_outputs = []
        for third_gain in (-0.70, -0.35, 0.35):
            contributions, output = shifted_copy_sum(values, delays, [gains[0], gains[1], third_gain])
            gain_outputs.append(output)
            self.assertEqual(
                [index for index, value in enumerate(contributions[2]) if value],
                list(range(14, 21)),
            )
        self.assertLess(gain_outputs[0][17], gain_outputs[1][17])
        self.assertLess(gain_outputs[1][17], gain_outputs[2][17])

        negative_values = [0.0] * 40
        negative_values[20:23] = [-1.0, -0.5, -0.25]
        negative_third = []
        for third_gain in (-0.70, 0.35):
            contributions, _ = shifted_copy_sum(
                negative_values, delays, [gains[0], gains[1], third_gain]
            )
            negative_third.append(contributions[2])
        self.assertGreater(max(map(abs, negative_third[1])), 0)
        self.assertLess(
            max(abs(negative + 2 * positive) for negative, positive in zip(*negative_third)),
            1e-15,
        )

        for marker in (
            "Parameter sweep 1 - change only the middle echo delay",
            "middle_delay_sweep_samples = [3 5 7]",
            "middle_delay_sweep_ms = 1000*middle_delay_sweep_samples/fs;",
            "Only middle delay changes; its gain stays",
            "Parameter sweep 2 - change only the signed third-path gain",
            "third_gain_sweep = [-0.70 -0.35 0.35]",
            "Only third gain changes; its delay stays",
            "signed_gain_reversal_error_v = max(abs(",
            "signed_gain_reversal_error_v < comparison_tolerance_v",
        ):
            self.assertIn(marker, self.experiment)

    def test_broken_overwrite_case_and_recovery(self):
        values, _, gains = self.baseline_fixture()
        delays = [0, 3, 6]
        _, correct = shifted_copy_sum(values[:24], delays, gains)
        broken = broken_overwrite(values[:24], delays, gains)
        residual = [wrong - right for wrong, right in zip(broken, correct)]
        affected = sum(abs(value) > 2e-12 for value in residual)
        self.assertGreater(max(map(abs, residual)), 0.25)
        self.assertGreaterEqual(affected, 3)
        response = [0.0] * 7
        for delay, gain in zip(delays, gains):
            response[delay] = gain
        self.assertEqual(full_convolution(values[:24], response), correct)

        for marker in (
            "broken_input_sample_count = 24;",
            "broken_pulse_start_sample = 5;",
            "broken_pulse_shape_v = [0.25 0.50 0.75 1.00 0.75 0.50 0.25];",
            "broken_delays_samples = [0 3 6];",
            "broken_gains = [1.00 0.60 -0.35];",
            "broken_pulse_indices = broken_pulse_start_sample +",
            "Deliberately broken case - overwrite instead of add at overlaps",
            "broken_overwrite_output_v(output_index) = path_term_v;",
            "correct_accumulated_output_v(output_index) + path_term_v;",
            "broken_max_error_v > 0.25 && overlap_sample_count >= 3",
            "Addition at overlaps must recover linear convolution",
        ):
            self.assertIn(marker, self.experiment)
        broken_section = self.experiment.split(
            "%% Deliberately broken case - overwrite instead of add at overlaps", 1
        )[1]
        self.assertNotIn("broken_input_v(pulse_indices+1)", broken_section)
        self.assertNotIn("broken_gains = tap_gains", broken_section)

        # Accepted baseline edits must not alter the fixed failure fixture.
        edited_values = [0.0] * 40
        edited_values[20:23] = [0.1, 0.2, 0.1]
        _, edited_output = shifted_copy_sum(
            edited_values, [0, 5, 9], [0.2, -0.1, 0.05]
        )
        self.assertEqual(len(edited_output), 49)
        fixed_values = [0.0] * 24
        fixed_values[5:12] = [0.25, 0.50, 0.75, 1.00, 0.75, 0.50, 0.25]
        _, fixed_correct = shifted_copy_sum(fixed_values, delays, gains)
        fixed_broken = broken_overwrite(fixed_values, delays, gains)
        self.assertGreater(
            max(abs(wrong - right) for wrong, right in zip(fixed_broken, fixed_correct)),
            0.25,
        )

    def test_required_views_labels_metrics_and_concept_first_documents(self):
        for view in (
            "pulse and three-tap echo channel",
            "delayed scaled copies add into the output",
            "manual addition equals convolution",
            "bounded overlap-and-sum animation",
            "path delay moves one whole echo copy",
            "signed path gain controls addition or cancellation",
            "overwrite loses overlapping echo terms",
        ):
            self.assertIn(view, self.experiment)
        for label in (
            "Input sample index n",
            "Input voltage x[n] (V)",
            "Path delay k (samples)",
            "Path gain h[k] (V/V)",
            "Output sample index n",
            "Output voltage y[n] (V)",
            "Signed contribution (V)",
            "Overwrite-minus-add error (V)",
        ):
            self.assertIn(label, self.experiment)

        combined = "\n".join((self.lesson, self.walkthrough, self.checks)).lower()
        for concept in (
            "delayed",
            "scaled",
            "overlap",
            "signed sum",
            "echo",
            "linear convolution",
            "radar",
            "base matlab",
        ):
            self.assertIn(concept, combined)
        for limiting_case in (
            "If `h[0] = 1`",
            "If all tap gains are zero",
            "If one echo gain becomes zero",
            "If two taps have the same delay",
            "If a path delay exceeds",
            "If the pulse becomes one unit sample",
            "finite input of length `N_x`",
            "linear time-invariant channel",
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
            "cconv(",
            "phased.",
            "dsp.",
            "readtable(",
            "webread(",
        ):
            self.assertNotIn(prohibited, implementation)
        self.assertIn("base MATLAB `conv`", self.readme)
        self.assertIn("only then does base MATLAB `conv`", self.readme)
        self.assertLess(self.experiment.index("Linear convolution is y[n]"), self.experiment.index("conv_output_v = conv("))

    def test_malformed_controls_and_resource_bounds_precede_allocation(self):
        self.assertEqual(self.scalar_assignment("max_input_samples"), 256)
        self.assertEqual(self.scalar_assignment("max_output_samples"), 512)
        self.assertEqual(self.scalar_assignment("max_taps"), 8)
        self.assertEqual(self.scalar_assignment("max_sweep_cases"), 8)
        self.assertEqual(self.scalar_assignment("max_animation_frames"), 64)
        for guard in (
            "input_sample_count <= max_input_samples",
            "random_seed <= 2^32-1",
            "pulse_start_sample + numel(pulse_shape_v) <= input_sample_count",
            "output_sample_count <= max_output_samples",
            "numel(tap_delays_samples) == expected_tap_count",
            "all(diff(tap_delays_samples) > 0)",
            "numel(unique(abs(tap_gains))) == expected_tap_count",
            "numel(middle_delay_sweep_samples) <= max_sweep_cases",
            "numel(third_gain_sweep) <= max_sweep_cases",
            "broken_input_sample_count == 24",
            "isequal(broken_delays_samples, [0 3 6])",
            "broken_pulse_start_sample + numel(broken_pulse_shape_v) <=",
            "animation_frame_count <= max_animation_frames",
            "animation_pause_s <= 0.25",
        ):
            self.assertIn(guard, self.experiment)
        first_signal_allocation = self.experiment.index("input_pulse_v = zeros")
        self.assertLess(self.experiment.index("input_sample_count <= max_input_samples"), first_signal_allocation)
        self.assertLess(self.experiment.index("output_sample_count <= max_output_samples"), first_signal_allocation)
        self.assertLess(
            self.experiment.index("numel(middle_delay_sweep_samples) <= max_sweep_cases"),
            self.experiment.index("delay_sweep_outputs_v = zeros"),
        )
        self.assertLess(
            self.experiment.index("numel(third_gain_sweep) <= max_sweep_cases"),
            self.experiment.index("gain_sweep_outputs_v = zeros"),
        )

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
        for valid in (0, 5, 256.0):
            self.assertTrue(finite_nonnegative_integer(valid))

        def supported_random_seed(value: object) -> bool:
            return finite_nonnegative_integer(value) and value <= 2**32 - 1

        for malformed_seed in (-1, 1.5, math.nan, math.inf, True, 2**32):
            with self.subTest(malformed_seed=malformed_seed):
                self.assertFalse(supported_random_seed(malformed_seed))
        for valid_seed in (0, 707, 2**32 - 1):
            self.assertTrue(supported_random_seed(valid_seed))

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback_scope(self):
        self.assertLessEqual(self.experiment.count("figure("), 8)
        self.assertNotRegex(self.experiment, r"(?m)^\s*(while|parfor|timer|parfeval|batch)\b")
        for destructive in ("clear all", "close all", "clc", "rng("):
            self.assertNotIn(destructive, self.experiment.lower())
        for external in ("fopen(", "save(", "writetable(", "urlread(", "webread(", "tcpclient(", "serialport(", "audiorecorder(", "input("):
            self.assertNotIn(external, self.experiment.lower())
        for marker in (
            "prior_p07_figures = findall",
            "close(prior_p07_figures);",
            "RandStream('mt19937ar'",
            "animation_pause_s = 0.08",
            "animation_pause_s <= 0.25",
            "Ctrl+C",
            "There is no persistent file",
            "base MATLAB only",
        ):
            self.assertIn(marker, "\n".join((self.experiment, self.walkthrough, self.checks)))
        self.assertIn("restore only P07", self.readme)
        self.assertIn("manifest status to `scaffolded`", self.readme)


if __name__ == "__main__":
    unittest.main()
