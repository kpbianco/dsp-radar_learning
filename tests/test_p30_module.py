from __future__ import annotations

import copy
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/30-measure-range-from-echo-delay"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How does round-trip delay become target range?"
EXPECTED_IDENTITY = {
    "number": 30,
    "id": "P30",
    "title": "Measure Range from Echo Delay",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "measure-range-from-echo-delay",
    "folder": "modules/30-measure-range-from-echo-delay",
    "status": "implemented",
    "implementation_batch": "P30",
}
CANONICAL_CONTROLS = {
    "random_seed": 3001,
    "speed_of_light_mps": 299792458.0,
    "sample_rate_hz": 20e6,
    "pulse_duration_s": 1e-6,
    "true_round_trip_delay_s": 6.0175e-6,
    "echo_amplitude": 1.0,
    "noise_sigma": 0.03,
    "capture_duration_s": 16e-6,
    "sample_rate_sweep_hz": (10e6, 20e6, 40e6),
    "fractional_delay_integer_samples": 120,
    "fractional_delay_sweep_samples": (0.0, 0.25, 0.5, 0.75),
    "second_echo_amplitude": 0.65,
    "second_target_separation_s": (0.5e-6, 1e-6, 1.5e-6),
    "max_record_samples": 640,
    "max_pulse_samples": 40,
    "max_correlation_samples": 640,
    "max_sweep_cases": 4,
    "max_figure_groups": 6,
    "max_stored_numeric_values": 50000,
    "comparison_tolerance": 1e-10,
}


def validate_p30_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P30 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P30 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P30"]
    if len(matches) != 1:
        return errors + [f"expected one P30 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P30 {key} must be {expected!r}")
    return errors


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_controls(**overrides: object) -> dict[str, object]:
    unknown = set(overrides) - set(CANONICAL_CONTROLS)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls = dict(CANONICAL_CONTROLS)
    controls.update(overrides)
    positive = (
        "speed_of_light_mps",
        "sample_rate_hz",
        "pulse_duration_s",
        "true_round_trip_delay_s",
        "echo_amplitude",
        "capture_duration_s",
        "second_echo_amplitude",
        "comparison_tolerance",
    )
    for name in positive:
        if not finite_real(controls[name]) or controls[name] <= 0:
            raise ValueError(f"{name} must be finite and positive")
    if (
        not finite_real(controls["noise_sigma"])
        or controls["noise_sigma"] < 0
    ):
        raise ValueError("noise_sigma must be finite and nonnegative")
    for name in (
        "random_seed",
        "fractional_delay_integer_samples",
        "max_record_samples",
        "max_pulse_samples",
        "max_correlation_samples",
        "max_sweep_cases",
        "max_figure_groups",
        "max_stored_numeric_values",
    ):
        value = controls[name]
        if not finite_real(value) or int(value) != value or value < 0:
            raise ValueError(f"{name} must be a nonnegative integer")
    if controls["random_seed"] != 3001:
        raise ValueError("random_seed must remain canonical")
    vectors = (
        "sample_rate_sweep_hz",
        "fractional_delay_sweep_samples",
        "second_target_separation_s",
    )
    for name in vectors:
        value = controls[name]
        if (
            not isinstance(value, (tuple, list))
            or len(value) < 2
            or len(value) > controls["max_sweep_cases"]
            or any(not finite_real(item) for item in value)
        ):
            raise ValueError(f"{name} must be a short finite numeric vector")
    rates = controls["sample_rate_sweep_hz"]
    fractions = controls["fractional_delay_sweep_samples"]
    separations = controls["second_target_separation_s"]
    if any(value <= 0 for value in rates) or any(
        right <= left for left, right in zip(rates, rates[1:])
    ):
        raise ValueError("sample rates must be positive and increasing")
    if any(value < 0 or value >= 1 for value in fractions):
        raise ValueError("fractional delays must be in [0, 1)")
    if any(value <= 0 for value in separations) or any(
        right <= left for left, right in zip(separations, separations[1:])
    ):
        raise ValueError("separations must be positive and increasing")
    if controls["true_round_trip_delay_s"] + controls["pulse_duration_s"] + max(
        separations
    ) >= controls["capture_duration_s"]:
        raise ValueError("echo does not fit in capture")
    max_rate = max(controls["sample_rate_hz"], *rates)
    record_count = round(controls["capture_duration_s"] * max_rate)
    pulse_count = round(controls["pulse_duration_s"] * max_rate)
    stored = 40 * record_count + 20 * len(fractions) * pulse_count
    if (
        record_count > controls["max_record_samples"]
        or pulse_count > controls["max_pulse_samples"]
        or record_count > controls["max_correlation_samples"]
        or stored > controls["max_stored_numeric_values"]
    ):
        raise ValueError("resource ceiling exceeded")
    baseline_record_count = round(
        controls["capture_duration_s"] * controls["sample_rate_hz"]
    )
    baseline_pulse_count = round(
        controls["pulse_duration_s"] * controls["sample_rate_hz"]
    )
    reviewed_pulse_counts = [
        round(controls["pulse_duration_s"] * rate)
        for rate in (controls["sample_rate_hz"], *rates)
    ]
    if any(count < 1 for count in reviewed_pulse_counts):
        raise ValueError("every reviewed rate must represent at least one pulse sample")
    fractional_minimum = controls["fractional_delay_integer_samples"] + min(
        fractions
    )
    fractional_maximum = controls["fractional_delay_integer_samples"] + max(
        fractions
    )
    if (
        fractional_minimum < 1
        or fractional_maximum + baseline_pulse_count + 1 > baseline_record_count
    ):
        raise ValueError("fractional sweep peak neighborhood does not fit capture")
    return controls


def parse_matlab_controls(source: str) -> dict[str, object]:
    parsed: dict[str, object] = {}
    vector_names = {
        "sample_rate_sweep_hz",
        "fractional_delay_sweep_samples",
        "second_target_separation_s",
    }
    for name, expected in CANONICAL_CONTROLS.items():
        if name in vector_names:
            matches = re.findall(
                rf"(?m)^{re.escape(name)}\s*=\s*\[([^\]]+)\]\s*;", source
            )
            if len(matches) != 1:
                raise ValueError(f"expected one vector assignment for {name}")
            parsed[name] = tuple(float(item) for item in matches[0].split())
            continue
        matches = re.findall(
            rf"(?mi)^{re.escape(name)}\s*=\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?)\s*;",
            source,
        )
        if len(matches) != 1:
            raise ValueError(f"expected one numeric assignment for {name}")
        value = float(matches[0])
        parsed[name] = int(value) if isinstance(expected, int) else value
    return parsed


def validate_source_contract(source: str) -> list[str]:
    errors: list[str] = []
    try:
        parsed = parse_matlab_controls(source)
    except ValueError as exc:
        return [str(exc)]
    if parsed != CANONICAL_CONTROLS:
        errors.append("visible controls differ from the canonical deterministic contract")
    markers = (
        "true_range_m = speed_of_light_mps*true_round_trip_delay_s/2;",
        "integer_delay_s = integer_delay_samples/sample_rate_hz;",
        "integer_range_m = speed_of_light_mps*integer_delay_s/2;",
        "r_xs[ell] = sum_m x[ell+m]*conj(s[m])",
        "aligned_sum = aligned_sum + received_signal(received_index)*",
        "conj(transmit_pulse(pulse_index));",
        "convolution_crosscheck = conv(received_signal, fliplr(conj(transmit_pulse)));",
        "range_bin_spacing_m = speed_of_light_mps/(2*sample_rate_hz);",
        "broken_range_m = speed_of_light_mps*refined_delay_s;",
        "recovered_range_m = speed_of_light_mps*refined_delay_s/2;",
        "broken_model_valid = false;",
        "recovery_exact_match = isequal(recovery_unit_noise, unit_noise)",
    )
    for marker in markers:
        if marker not in source:
            errors.append(f"missing source marker: {marker}")
    return errors


def fractional_echo(
    record_count: int, pulse_count: int, delay_samples: float, amplitude: float = 1.0
) -> list[float]:
    if record_count <= 0 or pulse_count <= 0 or delay_samples < 0:
        raise ValueError("record, pulse, and delay must define a nonnegative finite echo")
    if delay_samples + pulse_count >= record_count:
        raise ValueError("echo does not fit")
    output: list[float] = []
    for record_index in range(record_count):
        source_position = record_index - delay_samples
        source_left = math.floor(source_position)
        fraction = source_position - source_left
        left = 1.0 if 0 <= source_left < pulse_count else 0.0
        right = 1.0 if 0 <= source_left + 1 < pulse_count else 0.0
        output.append(amplitude * ((1 - fraction) * left + fraction * right))
    return output


def explicit_correlation(received: list[float], pulse_count: int) -> list[float]:
    if pulse_count <= 0 or pulse_count > len(received):
        raise ValueError("pulse must fit received record")
    return [
        sum(received[lag + pulse_index] for pulse_index in range(pulse_count))
        for lag in range(len(received) - pulse_count + 1)
    ]


def estimate_delay(correlation: list[float]) -> tuple[int, float]:
    if len(correlation) < 3:
        raise ValueError("correlation needs an interior peak")
    magnitude = [abs(value) for value in correlation]
    peak = max(range(len(magnitude)), key=magnitude.__getitem__)
    if peak == 0 or peak == len(magnitude) - 1:
        raise ValueError("peak has no two-sided neighborhood")
    left, center, right = magnitude[peak - 1 : peak + 2]
    denominator = left - 2 * center + right
    if abs(denominator) <= 1e-12:
        raise ValueError("peak curvature is zero")
    offset = 0.5 * (left - right) / denominator
    if abs(offset) > 0.5 + 1e-12:
        raise ValueError("refinement left selected bin")
    return peak, peak + offset


def visible_peak_count(correlation: list[float]) -> int:
    magnitude = [abs(value) for value in correlation]
    threshold = 0.25 * max(magnitude)
    return sum(
        magnitude[index] > magnitude[index - 1]
        and magnitude[index] >= magnitude[index + 1]
        and magnitude[index] > threshold
        for index in range(1, len(magnitude) - 1)
    )


class P30ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text())
        cls.text = {
            name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        }
        cls.experiment = cls.text["experiment.m"]

    def test_complete_artifacts_exact_identity_and_prerequisite(self):
        self.assertEqual(validate_p30_contract(MODULE, self.manifest), [])
        for text in self.text.values():
            self.assertIn(QUESTION, text)
        prerequisite = next(
            item for item in self.manifest["modules"] if item["id"] == "P29"
        )
        self.assertEqual(prerequisite["status"], "implemented")

    def test_contract_validator_rejects_missing_empty_duplicate_and_malformed(self):
        self.assertIn("manifest modules must be a list", validate_p30_contract(MODULE, {}))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p30_contract(MODULE, {"modules": ["bad"]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn(
            "expected one P30 manifest entry, found 2",
            validate_p30_contract(MODULE, duplicate),
        )
        wrong = copy.deepcopy(self.manifest)
        entry = next(item for item in wrong["modules"] if item["id"] == "P30")
        entry["guiding_question"] = "generic delay question"
        entry["status"] = "scaffolded"
        errors = validate_p30_contract(MODULE, wrong)
        self.assertIn(f"P30 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P30 status must be 'implemented'", errors)
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary)
            for name in ARTIFACTS:
                (copied / name).write_text("content", encoding="utf-8")
            (copied / "experiment.m").unlink()
            (copied / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p30_contract(copied, self.manifest)
            self.assertIn("P30 missing experiment.m", errors)
            self.assertIn("P30 empty lesson.md", errors)

    def test_controls_are_canonical_malformed_inputs_fail_and_resources_are_bounded(self):
        self.assertEqual(parse_matlab_controls(self.experiment), CANONICAL_CONTROLS)
        self.assertEqual(validate_source_contract(self.experiment), [])
        self.assertEqual(validate_controls(), CANONICAL_CONTROLS)
        malformed = (
            {"random_seed": True},
            {"speed_of_light_mps": float("nan")},
            {"sample_rate_hz": 20e6 + 1j},
            {"sample_rate_hz": 1e9},
            {"pulse_duration_s": 0.0},
            {"true_round_trip_delay_s": float("inf")},
            {"echo_amplitude": "strong"},
            {"noise_sigma": -0.1},
            {"capture_duration_s": 1e-6},
            {"sample_rate_sweep_hz": (10e6, 10e6)},
            {"fractional_delay_sweep_samples": (0.0, 1.0)},
            {"second_target_separation_s": (1e-6, 0.5e-6)},
            {"max_record_samples": 639},
            {"max_pulse_samples": 39},
            {"max_correlation_samples": 639},
            {"max_sweep_cases": 2},
            {"max_stored_numeric_values": 1000},
            {"comparison_tolerance": 0.0},
        )
        for override in malformed:
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_controls(**override)
        with self.assertRaises(ValueError):
            validate_controls(unapproved_control=1)

    def test_source_mutations_are_rejected(self):
        mutations = (
            self.experiment.replace(
                "true_range_m = speed_of_light_mps*true_round_trip_delay_s/2;",
                "true_range_m = speed_of_light_mps*true_round_trip_delay_s;",
            ),
            self.experiment.replace(
                "conj(transmit_pulse(pulse_index));",
                "transmit_pulse(pulse_index);",
            ),
            self.experiment.replace("broken_model_valid = false;", "broken_model_valid = true;"),
            self.experiment.replace("sample_rate_hz = 20e6;", "sample_rate_hz = 19e6;"),
        )
        for mutation in mutations:
            with self.subTest():
                self.assertTrue(validate_source_contract(mutation))

    def test_fractional_echo_is_zero_extended_area_preserving_and_non_circular(self):
        echo = fractional_echo(320, 20, 120.35)
        self.assertAlmostEqual(sum(echo), 20.0)
        self.assertTrue(all(value == 0 for value in echo[:120]))
        self.assertAlmostEqual(echo[120], 0.65)
        self.assertAlmostEqual(echo[140], 0.35)
        self.assertTrue(all(value == 0 for value in echo[141:]))
        with self.assertRaises(ValueError):
            fractional_echo(10, 20, 0)
        with self.assertRaises(ValueError):
            fractional_echo(40, 20, 25)

    def test_fractional_sweep_controls_require_interior_captured_peak_behavior(self):
        controls = validate_controls()
        self.assertEqual(controls["fractional_delay_integer_samples"], 120)
        for override in (
            {"fractional_delay_integer_samples": 0},
            {"fractional_delay_integer_samples": 400},
            {"sample_rate_hz": 1.0},
        ):
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_controls(**override)
        for marker in (
            "assert(all(reviewed_pulse_sample_counts >= 1)",
            "fractional_minimum_delay_samples >= 1",
            "fractional_maximum_delay_samples + baseline_pulse_sample_count + 1 <=",
        ):
            self.assertIn(marker, self.experiment)

    def test_explicit_correlation_delay_range_and_convolution_equivalence(self):
        controls = validate_controls()
        fs = controls["sample_rate_hz"]
        c = controls["speed_of_light_mps"]
        record_count = round(controls["capture_duration_s"] * fs)
        pulse_count = round(controls["pulse_duration_s"] * fs)
        true_delay = controls["true_round_trip_delay_s"] * fs
        echo = fractional_echo(record_count, pulse_count, true_delay)
        correlation = explicit_correlation(echo, pulse_count)
        integer_delay, refined_delay = estimate_delay(correlation)
        true_range = c * controls["true_round_trip_delay_s"] / 2
        integer_range = c * integer_delay / (2 * fs)
        refined_range = c * refined_delay / (2 * fs)
        bin_spacing = c / (2 * fs)
        self.assertEqual(integer_delay, 120)
        self.assertAlmostEqual(refined_delay, 120.26923076923077)
        self.assertLessEqual(abs(integer_range - true_range), bin_spacing / 2)
        self.assertLess(abs(refined_range - true_range), abs(integer_range - true_range))

        reverse = [1.0] * pulse_count
        convolution = [0.0] * (len(echo) + len(reverse) - 1)
        for first_index, first in enumerate(echo):
            for second_index, second in enumerate(reverse):
                convolution[first_index + second_index] += first * second
        self.assertEqual(correlation, convolution[pulse_count - 1 : len(echo)])
        with self.assertRaises(ValueError):
            explicit_correlation([1.0], 2)
        with self.assertRaises(ValueError):
            estimate_delay([1.0, 1.0, 1.0])

    def test_sample_rate_and_fractional_delay_sweeps_have_expected_bounds(self):
        controls = validate_controls()
        c = controls["speed_of_light_mps"]
        true_range = c * controls["true_round_trip_delay_s"] / 2
        bin_spacings = []
        for fs in controls["sample_rate_sweep_hz"]:
            record_count = round(controls["capture_duration_s"] * fs)
            pulse_count = round(controls["pulse_duration_s"] * fs)
            delay = controls["true_round_trip_delay_s"] * fs
            integer, refined = estimate_delay(
                explicit_correlation(
                    fractional_echo(record_count, pulse_count, delay), pulse_count
                )
            )
            spacing = c / (2 * fs)
            bin_spacings.append(spacing)
            self.assertLessEqual(abs(c * integer / (2 * fs) - true_range), spacing / 2)
            self.assertLess(abs(c * refined / (2 * fs) - true_range), spacing / 2)
        self.assertEqual(bin_spacings[0] / bin_spacings[1], 2)
        self.assertEqual(bin_spacings[1] / bin_spacings[2], 2)

        integer_errors = []
        refined_errors = []
        for fraction in controls["fractional_delay_sweep_samples"]:
            true_delay = controls["fractional_delay_integer_samples"] + fraction
            integer, refined = estimate_delay(
                explicit_correlation(fractional_echo(320, 20, true_delay), 20)
            )
            integer_errors.append(integer - true_delay)
            refined_errors.append(refined - true_delay)
        self.assertTrue(all(abs(error) <= 0.5 for error in integer_errors))
        self.assertLess(max(map(abs, refined_errors)), max(map(abs, integer_errors)))
        self.assertAlmostEqual(refined_errors[0], 0.0)
        self.assertAlmostEqual(refined_errors[2], 0.0)

    def test_two_target_separation_moves_from_merged_to_two_visible_peaks(self):
        controls = validate_controls()
        fs = controls["sample_rate_hz"]
        pulse_count = round(controls["pulse_duration_s"] * fs)
        record_count = round(controls["capture_duration_s"] * fs)
        first_delay = controls["true_round_trip_delay_s"] * fs
        first = fractional_echo(record_count, pulse_count, first_delay)
        counts = []
        for separation in controls["second_target_separation_s"]:
            second = fractional_echo(
                record_count,
                pulse_count,
                first_delay + separation * fs,
                controls["second_echo_amplitude"],
            )
            correlation = explicit_correlation(
                [left + right for left, right in zip(first, second)], pulse_count
            )
            counts.append(visible_peak_count(correlation))
        self.assertEqual(counts, [1, 1, 2])

    def test_source_binds_seed_equations_sweeps_failure_recovery_and_resources(self):
        for marker in (
            "%% Sweep 1: sample rate, with physical delay and pulse duration fixed",
            "%% Sweep 2: fractional-sample delay exposes the integer-lag staircase",
            "%% Sweep 3: second-target separation versus finite-pulse correlation width",
            "%% Intentionally broken case: forget that measured delay is round trip",
            "%% Recovery: restore c*tau/2 and reproduce the baseline private stream",
            "source_position = (record_index-1)-true_delay_samples;",
            "local_threshold = 0.25*max(case_magnitude);",
            "isequal(two_target_peak_count, [1 1 2])",
            "'range_bin_spacing_m'",
            "'visible_peak_count'",
            "'factor_of_two_error'",
            "'exact_match'",
        ):
            self.assertIn(marker, self.experiment)
        self.assertEqual(
            self.experiment.count("RandStream('mt19937ar', 'Seed', random_seed)"), 2
        )
        self.assertEqual(len(re.findall(r"\brandn\s*\(", self.experiment)), 2)
        validation = self.experiment.index("% Validation succeeded:")
        for work in ("zeros(", "ones(", "RandStream(", "randn(", "figure(", "findall("):
            self.assertGreater(self.experiment.index(work), validation)
        self.assertNotRegex(
            self.experiment,
            r"(?m)^\s*(?:while|parfor)\b|^\s*(?:timer|pause)\s*\(",
        )

    def test_broken_case_is_exactly_two_and_recovery_is_deterministic(self):
        controls = validate_controls()
        measured_delay_s = 120.26923076923077 / controls["sample_rate_hz"]
        broken = controls["speed_of_light_mps"] * measured_delay_s
        recovered = controls["speed_of_light_mps"] * measured_delay_s / 2
        self.assertEqual(broken / recovered, 2)
        for marker in (
            "recovery_stream = RandStream('mt19937ar', 'Seed', random_seed);",
            "isequal(recovery_unit_noise, unit_noise)",
            "isequal(recovered_received_signal, received_signal)",
            "isequal(recovery_correlation, explicit_correlation)",
            "recovered_range_m == refined_range_m",
        ):
            self.assertIn(marker, self.experiment)

    def test_plots_metrics_and_units_are_purposeful(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 6)
        for label in (
            "Fast time after transmit (microseconds)",
            "Monostatic range c tau / 2 (m)",
            "|Correlation| (V^2 samples)",
            "Sample rate (MHz)",
            "Range error (m)",
            "Integer range-bin spacing c/(2 f_s) (m)",
            "True fractional-sample delay (samples)",
            "Delay-estimation error (samples)",
            "Reported target range (m)",
        ):
            self.assertIn(label, self.experiment)

    def test_docs_are_concept_first_complete_and_black_box_free(self):
        lesson = self.text["lesson.md"]
        walkthrough = self.text["walkthrough.md"]
        checks = self.text["checks.md"]
        for marker in (
            "Physical model: use a clock as a ruler",
            "From received samples to delay",
            "Sample rate versus waveform width",
            "Assumptions and limiting cases",
            "Common interpretation mistakes",
            "Dependencies and concept connection",
        ):
            self.assertIn(marker, lesson)
        for marker in (
            "Baseline observation",
            "Sweep one variable: sample rate only",
            "Sweep one variable: fractional delay only",
            "Add a second target",
            "Intentionally broken case",
            "Recover and connect the concept",
        ):
            self.assertIn(marker.lower(), walkthrough.lower())
        for marker in (
            "Observation checks",
            "Prediction checks",
            "Interpretation checks",
            "Failure and recovery checks",
            "Completion checklist",
            "Short teach-back rubric",
        ):
            self.assertIn(marker, checks)
        combined = "\n".join(self.text.values())
        self.assertNotIn("TODO", combined)
        self.assertNotRegex(combined, r"(?i)implementation batch `P30` is pending")
        for pattern in (
            r"\bxcorr\s*\(",
            r"\bphased\.",
            r"\bawgn\s*\(",
            r"\bcircshift\s*\(",
            r"\brng\s*\(",
            r"\bclose\s+all\b",
            r"\bsave\s*\(",
            r"\bload\s*\(",
            r"\bfopen\s*\(",
            r"\bweb(read|write|save)\s*\(",
            r"\bsystem\s*\(",
        ):
            self.assertNotRegex(self.experiment, pattern)

    def test_cancellation_isolation_compatibility_rollback_and_cli_timeout(self):
        operational = self.text["walkthrough.md"] + self.text["checks.md"]
        for marker in (
            "Ctrl+C",
            "private seed",
            "global random stream",
            "figures tagged `P30`",
            ".learning/",
            "worker",
            "timer",
            "external transaction",
            "base MATLAB",
            "rollback",
            "scaffolded",
        ):
            self.assertIn(marker.lower(), operational.lower())
        self.assertIn(
            "close(findall(0, 'Type', 'figure', 'Tag', 'P30'))", self.experiment
        )
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 30 sends a finite pulse", root_readme)
        self.assertIn("Project 30 follows P29", start_here)
        self.assertRegex(module_index, r"\| \[P30\].*\| implemented \|")

        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            fixture_root = Path(temporary) / "repo"
            fixture_cli = fixture_root / "bin/learn"
            fixture_manifest = fixture_root / "curriculum/modules.json"
            fixture_readme = fixture_root / EXPECTED_IDENTITY["folder"] / "README.md"
            fixture_cli.parent.mkdir(parents=True)
            fixture_manifest.parent.mkdir(parents=True)
            fixture_readme.parent.mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture_cli)
            shutil.copy2(ROOT / "curriculum/modules.json", fixture_manifest)
            shutil.copy2(MODULE / "README.md", fixture_readme)
            environment = os.environ.copy()
            process = subprocess.run(
                [str(fixture_cli), "start", "30"],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("P30 — Measure Range from Echo Delay", process.stdout)
            self.assertIn("status: implemented", process.stdout)
            self.assertIn("Tutor entry", process.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_retained_evidence_is_honest_and_complete(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P30-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        for marker in (
            "Acceptance mapping",
            "Figure and metric inventory",
            "Independent oracle results",
            "Exact commands and results",
            "Changed and preserved invariants",
            "Residual risks and unperformed validation",
            "Rollback and recovery",
            "Validation class",
            "MATLAB runtime status",
            "Toolboxes",
            "MATLAB",
            "did not run",
        ):
            self.assertIn(marker, evidence)
        for command in (
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
        ):
            self.assertIn(command, evidence)
        for unit in ("MHz", "microseconds", "samples", "m", "V", "50,000"):
            self.assertIn(unit, evidence)
        self.assertNotIn("PENDING —", evidence)


if __name__ == "__main__":
    unittest.main()
