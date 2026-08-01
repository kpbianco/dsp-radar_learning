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
MODULE = ROOT / "modules" / "09-compare-fir-and-iir-filters-by-behavior"
MANIFEST_PATH = ROOT / "curriculum" / "modules.json"
GUIDING_QUESTION = (
    "How can two filters with similar magnitude response behave differently in time and phase?"
)
REQUIRED_ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def validate_p09_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P09 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P09 empty {name}")

    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P09"]
    if len(entries) != 1:
        return errors + [f"expected one P09 manifest entry, found {len(entries)}"]

    expected = {
        "number": 9,
        "id": "P09",
        "title": "Compare FIR and IIR Filters by Behavior",
        "guiding_question": GUIDING_QUESTION,
        "phase": 1,
        "phase_title": "Signals, Sampling, and Systems",
        "slug": "compare-fir-and-iir-filters-by-behavior",
        "folder": "modules/09-compare-fir-and-iir-filters-by-behavior",
        "status": "implemented",
        "implementation_batch": "P09",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P09 {key} must be {value!r}")
    return errors


def design_fir(
    tap_count: int = 21,
    cutoff_hz: float = 100.0,
    fs_hz: float = 1000.0,
    design_scale: float = 1.20,
    max_taps: int = 81,
) -> list[float]:
    values = (cutoff_hz, fs_hz, design_scale)
    if any(not math.isfinite(value) for value in values):
        raise ValueError("FIR controls must be finite")
    if isinstance(tap_count, bool) or not isinstance(tap_count, int):
        raise ValueError("tap count must be an integer")
    if tap_count < 5 or tap_count % 2 == 0 or tap_count > max_taps:
        raise ValueError("tap count must be bounded, odd, and at least five")
    if fs_hz <= 0 or cutoff_hz <= 0 or design_scale <= 1:
        raise ValueError("FIR frequency controls must be positive")
    if design_scale * cutoff_hz >= fs_hz / 2:
        raise ValueError("FIR design cutoff must remain below Nyquist")

    half_order = (tap_count - 1) // 2
    design_cutoff_hz = design_scale * cutoff_hz
    coefficients: list[float] = []
    for tap_index in range(tap_count):
        centered_index = tap_index - half_order
        argument = 2 * design_cutoff_hz / fs_hz * centered_index
        sinc_value = 1.0 if centered_index == 0 else math.sin(math.pi * argument) / (
            math.pi * argument
        )
        ideal_value = 2 * design_cutoff_hz / fs_hz * sinc_value
        window_value = 0.54 - 0.46 * math.cos(2 * math.pi * tap_index / (tap_count - 1))
        coefficients.append(ideal_value * window_value)
    coefficient_sum = sum(coefficients)
    return [value / coefficient_sum for value in coefficients]


def design_iir(
    q: float = 1 / math.sqrt(2), cutoff_hz: float = 100.0, fs_hz: float = 1000.0
) -> tuple[list[float], list[float]]:
    if any(not math.isfinite(value) for value in (q, cutoff_hz, fs_hz)):
        raise ValueError("IIR controls must be finite")
    if q <= 0 or fs_hz <= 0 or cutoff_hz <= 0 or cutoff_hz >= fs_hz / 2:
        raise ValueError("IIR controls must define a positive in-band cutoff and Q")
    coefficient_k = math.tan(math.pi * cutoff_hz / fs_hz)
    norm = 1 / (1 + coefficient_k / q + coefficient_k**2)
    numerator = [coefficient_k**2 * norm, 2 * coefficient_k**2 * norm, coefficient_k**2 * norm]
    denominator = [
        1.0,
        2 * (coefficient_k**2 - 1) * norm,
        (1 - coefficient_k / q + coefficient_k**2) * norm,
    ]
    return numerator, denominator


def second_order_poles(denominator: list[float]) -> tuple[complex, complex]:
    if len(denominator) != 3 or abs(denominator[0] - 1) > 1e-12:
        raise ValueError("expected a normalized second-order denominator")
    discriminant = denominator[1] ** 2 - 4 * denominator[2]
    root = cmath.sqrt(discriminant)
    return ((-denominator[1] + root) / 2, (-denominator[1] - root) / 2)


def explicit_response(
    numerator: list[float], denominator: list[float], frequency_hz: float, fs_hz: float
) -> complex:
    omega = 2 * math.pi * frequency_hz / fs_hz
    z_inverse = cmath.exp(-1j * omega)
    top = sum(value * z_inverse**index for index, value in enumerate(numerator))
    bottom = sum(value * z_inverse**index for index, value in enumerate(denominator))
    return top / bottom


def measured_cutoff_hz(
    numerator: list[float], denominator: list[float], fs_hz: float = 1000.0, points: int = 1025
) -> float:
    target = 1 / math.sqrt(2)
    for index in range(points):
        frequency_hz = fs_hz * index / (2 * (points - 1))
        if abs(explicit_response(numerator, denominator, frequency_hz, fs_hz)) <= target:
            return frequency_hz
    raise AssertionError("response did not cross minus three decibels")


def group_delay_samples(
    numerator: list[float], denominator: list[float], frequency_hz: float, fs_hz: float = 1000.0
) -> float:
    delta_hz = 0.01
    below = explicit_response(numerator, denominator, frequency_hz - delta_hz, fs_hz)
    above = explicit_response(numerator, denominator, frequency_hz + delta_hz, fs_hz)
    phase_change = cmath.phase(above / below)
    omega_change = 4 * math.pi * delta_hz / fs_hz
    return -phase_change / omega_change


def apply_difference_equation(
    numerator: list[float],
    denominator: list[float],
    samples: list[float],
    *,
    max_samples: int = 512,
    require_stable: bool = False,
) -> list[float]:
    if not numerator or not denominator or abs(denominator[0] - 1) > 1e-12:
        raise ValueError("coefficient vectors must be nonempty with a0 equal to one")
    if len(samples) > max_samples:
        raise ValueError("sample record exceeds resource ceiling")
    if any(not math.isfinite(value) for value in numerator + denominator + samples):
        raise ValueError("coefficients and samples must be finite")
    if require_stable and len(denominator) == 3:
        if max(abs(pole) for pole in second_order_poles(denominator)) >= 1:
            raise ValueError("stable execution requested for unstable poles")

    output: list[float] = []
    for output_index in range(len(samples)):
        accumulator = sum(
            coefficient * samples[output_index - coefficient_index]
            for coefficient_index, coefficient in enumerate(numerator)
            if output_index >= coefficient_index
        )
        accumulator -= sum(
            denominator[coefficient_index] * output[output_index - coefficient_index]
            for coefficient_index in range(1, len(denominator))
            if output_index >= coefficient_index
        )
        output.append(accumulator)
    return output


def window_rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values))


class P09ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.experiment = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        cls.start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        cls.module_index = (ROOT / "modules" / "README.md").read_text(encoding="utf-8")

    def test_artifact_completeness_and_manifest_identity(self):
        self.assertEqual(validate_p09_contract(MODULE, self.manifest), [])
        for artifact in REQUIRED_ARTIFACTS:
            self.assertGreater((MODULE / artifact).stat().st_size, 100)

    def test_contract_validator_rejects_missing_empty_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture = Path(temporary_directory) / "module"
            shutil.copytree(MODULE, fixture)
            (fixture / "checks.md").unlink()
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p09_contract(fixture, self.manifest)
            self.assertIn("P09 missing checks.md", errors)
            self.assertIn("P09 empty lesson.md", errors)

        self.assertIn("manifest modules must be a list", validate_p09_contract(MODULE, None))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p09_contract(MODULE, {"modules": ["P09"]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][8]))
        self.assertIn("expected one P09 manifest entry, found 2", validate_p09_contract(MODULE, duplicate))

    def test_guiding_question_and_declared_dependency_are_preserved(self):
        for content in (self.readme, self.lesson, self.walkthrough, self.checks):
            self.assertIn(GUIDING_QUESTION, content)
        self.assertIn("P08 is the declared prerequisite", self.lesson)
        self.assertIn("P08 is the prerequisite", self.walkthrough)

    def test_manifest_and_public_catalogs_preserve_p09(self):
        statuses = [entry["status"] for entry in self.manifest["modules"]]
        self.assertEqual(statuses[:9], ["implemented"] * 9)
        self.assertRegex(self.module_index, r"\| \[P09\].*\| implemented \|")
        self.assertIn("Project 9 is the next lesson after P08.", self.start_here)

    def test_deterministic_input_contract_and_visible_parameters(self):
        markers = (
            "random_seed = 909;",
            "random_seed <= 2^32-1",
            "fs_hz = 1000;",
            "cutoff_hz = 100;",
            "fir_tap_count = 21;",
            "iir_q = 1/sqrt(2);",
            "desired_tone_hz = 60;",
            "interferer_tone_hz = 250;",
            "noise_rms_v = 0.15;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "randn(random_stream, 1, record_sample_count)",
            "seed_signature",
        )
        for marker in markers:
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?<![A-Za-z])rng\s*\(")

    def test_underlying_fir_and_iir_operations_are_explicit(self):
        markers = (
            "sinc_value = sin(pi*sinc_argument)/(pi*sinc_argument);",
            "fir_accumulator = fir_accumulator+",
            "iir_accumulator = iir_b(1)*",
            "iir_a(2)*iir_output_matrix_v",
            "iir_a(3)*iir_output_matrix_v",
            "fir_sum = fir_sum+fir_b",
            "iir_numerator = iir_b(1)",
            "iir_denominator = iir_a(1)",
        )
        for marker in markers:
            self.assertIn(marker, self.experiment)
        for opaque_call in ("filter", "filtfilt", "fir1", "butter", "designfilt", "freqz", "grpdelay", "impz"):
            self.assertNotRegex(self.experiment, rf"(?<![A-Za-z0-9_]){opaque_call}\s*\(")

    def test_baseline_coefficients_have_dc_gain_symmetry_and_stable_poles(self):
        fir = design_fir()
        iir_b, iir_a = design_iir()
        self.assertAlmostEqual(sum(fir), 1.0, places=12)
        self.assertLess(max(abs(left - right) for left, right in zip(fir, reversed(fir))), 1e-12)
        self.assertAlmostEqual(sum(iir_b) / sum(iir_a), 1.0, places=12)
        self.assertLess(max(abs(pole) for pole in second_order_poles(iir_a)), 1.0)

    def test_baseline_cutoffs_are_comparable_but_stopbands_differ(self):
        fir = design_fir()
        iir_b, iir_a = design_iir()
        fir_cutoff = measured_cutoff_hz(fir, [1.0])
        iir_cutoff = measured_cutoff_hz(iir_b, iir_a)
        self.assertLessEqual(abs(fir_cutoff - iir_cutoff), 3.0)
        self.assertAlmostEqual(fir_cutoff, 100.09765625, places=8)
        self.assertAlmostEqual(iir_cutoff, 100.09765625, places=8)
        fir_stopband_db = 20 * math.log10(abs(explicit_response(fir, [1.0], 250, 1000)))
        iir_stopband_db = 20 * math.log10(abs(explicit_response(iir_b, iir_a, 250, 1000)))
        self.assertLess(fir_stopband_db, iir_stopband_db - 20)

    def test_phase_and_group_delay_contract_is_numerically_distinct(self):
        fir = design_fir()
        iir_b, iir_a = design_iir()
        for frequency_hz in (60.0, 150.0, 250.0):
            self.assertAlmostEqual(group_delay_samples(fir, [1.0], frequency_hz), 10.0, places=7)
        iir_delay_60 = group_delay_samples(iir_b, iir_a, 60.0)
        iir_delay_150 = group_delay_samples(iir_b, iir_a, 150.0)
        self.assertGreater(abs(iir_delay_60 - iir_delay_150), 0.2)
        self.assertGreater(abs(iir_delay_60 - 10.0), 1.0)

    def test_impulse_support_and_recurrence_behavior_differ(self):
        impulse = [1.0] + [0.0] * 159
        fir = design_fir()
        iir_b, iir_a = design_iir()
        fir_output = apply_difference_equation(fir, [1.0], impulse)
        iir_output = apply_difference_equation(iir_b, iir_a, impulse, require_stable=True)
        self.assertEqual(fir_output[21:], [0.0] * 139)
        self.assertGreater(max(abs(value) for value in iir_output[21:40]), 1e-6)
        self.assertLess(max(abs(value) for value in iir_output[-20:]), 1e-12)

    def test_fir_tap_sweep_changes_delay_with_one_visible_control(self):
        self.assertIn("fir_tap_count_sweep = [9 21 41];", self.experiment)
        self.assertIn("Parameter sweep 1 - change only FIR tap count", self.experiment)
        delays = [(tap_count - 1) // 2 for tap_count in (9, 21, 41)]
        self.assertEqual(delays, [4, 10, 20])
        for tap_count, expected_delay in zip((9, 21, 41), delays):
            coefficients = design_fir(tap_count=tap_count)
            self.assertAlmostEqual(
                group_delay_samples(coefficients, [1.0], 60.0), expected_delay, places=7
            )

    def test_iir_q_sweep_is_stable_and_increases_overshoot(self):
        self.assertIn("iir_q_sweep = [0.50 1/sqrt(2) 2.00];", self.experiment)
        self.assertIn("Parameter sweep 2 - change only IIR Q", self.experiment)
        step = [0.0] * 15 + [1.0] * 145
        radii: list[float] = []
        overshoots: list[float] = []
        for q in (0.5, 1 / math.sqrt(2), 2.0):
            numerator, denominator = design_iir(q=q)
            radii.append(max(abs(pole) for pole in second_order_poles(denominator)))
            output = apply_difference_equation(numerator, denominator, step, require_stable=True)
            overshoots.append(100 * (max(output) - 1))
        self.assertTrue(all(left < right for left, right in zip(radii, radii[1:])))
        self.assertTrue(all(left < right for left, right in zip(overshoots, overshoots[1:])))

    def test_broken_unstable_case_and_recovery_are_bounded_and_distinct(self):
        self.assertIn("broken_pole_radius = 1.02;", self.experiment)
        self.assertIn("recovered_pole_radius = 0.98;", self.experiment)
        self.assertIn("Deliberately broken case", self.experiment)
        impulse = [1.0] + [0.0] * 159
        ratios: dict[float, float] = {}
        for radius in (1.02, 0.98):
            angle = 2 * math.pi * 100 / 1000
            denominator = [1.0, -2 * radius * math.cos(angle), radius**2]
            numerator = [sum(denominator), 0.0, 0.0]
            output = apply_difference_equation(numerator, denominator, impulse)
            self.assertTrue(all(math.isfinite(value) for value in output))
            ratios[radius] = window_rms(output[-32:]) / window_rms(output[:32])
        self.assertGreater(ratios[1.02], 2.0)
        self.assertLess(ratios[0.98], 0.2)
        self.assertRaises(
            ValueError,
            apply_difference_equation,
            [sum([1.0, -2 * 1.02 * math.cos(2 * math.pi / 10), 1.02**2]), 0.0, 0.0],
            [1.0, -2 * 1.02 * math.cos(2 * math.pi / 10), 1.02**2],
            impulse,
            require_stable=True,
        )

    def test_malformed_and_resource_bound_numeric_inputs_fail_fast(self):
        invalid_fir_cases = (
            {"tap_count": 4},
            {"tap_count": 20},
            {"tap_count": 83},
            {"cutoff_hz": 0},
            {"cutoff_hz": float("nan")},
            {"cutoff_hz": 450, "design_scale": 1.20},
        )
        for controls in invalid_fir_cases:
            with self.subTest(controls=controls):
                with self.assertRaises(ValueError):
                    design_fir(**controls)
        for controls in ({"q": 0}, {"q": float("inf")}, {"cutoff_hz": 500}):
            with self.subTest(controls=controls):
                with self.assertRaises(ValueError):
                    design_iir(**controls)
        with self.assertRaises(ValueError):
            apply_difference_equation([1.0], [1.0], [0.0] * 513)
        with self.assertRaises(ValueError):
            apply_difference_equation([float("nan")], [1.0], [0.0])

        scalar_controls = (
            "step_onset_sample",
            "pulse_onset_sample",
            "pulse_width_samples",
            "desired_tone_hz",
            "interferer_tone_hz",
            "noise_rms_v",
            "frequency_grid_count",
            "settling_tolerance_fraction",
            "tail_threshold",
            "comparison_tolerance",
            "aggressive_pole_angle_hz",
            "broken_pole_radius",
            "recovered_pole_radius",
        )
        for control in scalar_controls:
            self.assertRegex(
                self.experiment,
                rf"(?s)assert\(isscalar\({control}\).*?isnumeric\({control}\).*?isreal\({control}\)",
            )
        self.assertIn("P09 resource ceilings must remain fixed.", self.experiment)

    def test_no_match_tail_and_settling_metrics_are_explicit(self):
        markers = (
            "fir_tail_metric_found = ~isempty(fir_last_tail_index);",
            "iir_tail_metric_found = ~isempty(iir_last_tail_index);",
            "fir_settling_metric_found = false;",
            "iir_settling_metric_found = false;",
            "fir_last_tail_sample = NaN;",
            "iir_last_tail_sample = NaN;",
            "fir_settling_after_onset_samples = NaN;",
            "iir_settling_after_onset_samples = NaN;",
        )
        for marker in markers:
            self.assertIn(marker, self.experiment)

        iir_b, iir_a = design_iir()
        impulse = apply_difference_equation(
            iir_b, iir_a, [1.0] + [0.0] * 159, require_stable=True
        )
        self.assertEqual([index for index, value in enumerate(impulse) if abs(value) > 2.0], [])

        step = apply_difference_equation(
            iir_b, iir_a, [0.0] * 15 + [1.0] * 145, require_stable=True
        )
        qualifying = [
            index
            for index in range(15, len(step))
            if all(abs(value - 1.0) <= 1e-16 for value in step[index:])
        ]
        self.assertEqual(qualifying, [])
        self.assertIn("found=0", self.walkthrough)

    def test_validation_precedes_allocation_and_figure_replacement(self):
        first_assert = self.experiment.index("assert(")
        first_data_allocation = self.experiment.index("fir_b = zeros")
        figure_lookup = self.experiment.index("prior_p09_figures = findall")
        last_numerical_assert = self.experiment.index("broken_tail_growth_ratio > 2")
        first_figure = self.experiment.index("figure('Name'")
        self.assertLess(first_assert, first_data_allocation)
        self.assertLess(last_numerical_assert, figure_lookup)
        self.assertLess(figure_lookup, first_figure)

    def test_timeout_cancellation_isolation_and_compatibility_contracts(self):
        forbidden_patterns = (
            r"(?m)^\s*while\b",
            r"\bpause\s*\(",
            r"\binput\s*\(",
            r"\btimer\s*\(",
            r"\bparfor\b",
            r"\bparfeval\b",
            r"\bclose\s+all\b",
            r"\bclear\s+all\b",
            r"\bfopen\s*\(",
            r"\bfprintf\s*\(\s*[^'\"]",
            r"\bwebread\s*\(",
            r"\btcpclient\s*\(",
            r"\bserialport\s*\(",
        )
        for pattern in forbidden_patterns:
            self.assertNotRegex(self.experiment, pattern)
        self.assertIn("max_record_samples = 512;", self.experiment)
        self.assertIn("max_response_samples = 256;", self.experiment)
        self.assertIn("max_fir_taps = 81;", self.experiment)
        self.assertIn("max_frequency_grid_count = 2049;", self.experiment)
        self.assertIn("max_sweep_cases = 8;", self.experiment)
        self.assertIn("max_figure_groups = 6;", self.experiment)
        self.assertIn("'Tag', 'P09'", self.experiment)
        self.assertIn("Ctrl+C", self.walkthrough)
        self.assertIn("base MATLAB", self.lesson)
        self.assertNotIn("function ", self.experiment)

    def test_plots_metrics_and_units_cover_required_behavior(self):
        for phrase in (
            "Magnitude (dB)",
            "Unwrapped phase (rad)",
            "Group delay (samples)",
            "Time (ms)",
            "Voltage (V)",
            "Response (V/V)",
            "Impulse response",
            "step overshoot",
            "settling",
            "multiplies",
            "adds/sample",
            "pole radius",
        ):
            self.assertIn(phrase.lower(), self.experiment.lower())
        self.assertEqual(self.experiment.count("figure('Name'"), 6)
        self.assertIn("results = struct();", self.experiment)

    def test_walkthrough_checks_and_lesson_are_concept_first_and_complete(self):
        for phrase in (
            "## Physical mental model",
            "## The two operations made visible",
            "## Limiting cases",
            "## Radar connection and common interpretation mistakes",
        ):
            self.assertIn(phrase, self.lesson)
        for phrase in (
            "## Baseline: start with the frequency behavior",
            "## Sweep 1: change only FIR tap count",
            "## Sweep 2: change only IIR Q",
            "## Broken case",
            "## Recovery and rollback",
        ):
            self.assertIn(phrase, self.walkthrough)
        for phrase in (
            "## Baseline observation checks",
            "## Predict, then verify",
            "## Interpretation checks",
            "## Failure classification",
            "## Teach-back completion",
        ):
            self.assertIn(phrase, self.checks)
        combined = "\n".join((self.lesson, self.walkthrough, self.checks))
        for concept in ("phase", "group delay", "ringing", "stability", "unit circle", "arithmetic"):
            self.assertIn(concept, combined.lower())
        self.assertNotIn("MATLAB syntax", self.lesson)

    def test_no_placeholder_or_unsupported_runtime_claim(self):
        combined = "\n".join((self.readme, self.experiment, self.lesson, self.walkthrough, self.checks))
        self.assertNotRegex(combined, r"(?i)\b(TODO|TBD|lorem ipsum)\b")
        for unsupported_claim in (
            "validated on hardware",
            "MATLAB runtime passed",
            "field validated",
            "production validated",
        ):
            self.assertNotIn(unsupported_claim, combined.lower())


if __name__ == "__main__":
    unittest.main()
