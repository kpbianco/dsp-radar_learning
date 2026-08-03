from __future__ import annotations

import copy
import json
import math
import os
import random
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/31-separate-range-resolution-from-range-accuracy"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Why can an estimate be precise even when two targets cannot be resolved?"
EXPECTED_IDENTITY = {
    "number": 31,
    "id": "P31",
    "title": "Separate Range Resolution from Range Accuracy",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "separate-range-resolution-from-range-accuracy",
    "folder": "modules/31-separate-range-resolution-from-range-accuracy",
    "status": "implemented",
    "implementation_batch": "P31",
}
CANONICAL_CONTROLS = {
    "random_seed": 3101,
    "speed_of_light_mps": 299792458.0,
    "sample_rate_hz": 80e6,
    "capture_duration_s": 12e-6,
    "baseline_bandwidth_hz": 4e6,
    "bandwidth_sweep_hz": (2e6, 4e6, 8e6),
    "single_target_range_m": 900.37,
    "two_target_separation_m": 22.0,
    "separation_sweep_m": (10.0, 22.0, 45.0),
    "echo_amplitude": 1.0,
    "high_matched_snr_db": 50.0,
    "accuracy_snr_db_sweep": (0.0, 15.0, 30.0),
    "accuracy_trial_count": 128,
    "pulse_truncation_sigma": 4.0,
    "accuracy_gate_half_width_m": 80.0,
    "fine_grid_factor": 16,
    "visible_peak_threshold_ratio": 0.35,
    "comparison_tolerance": 1e-10,
    "max_record_samples": 960,
    "max_pulse_samples": 91,
    "max_correlation_lags": 960,
    "max_bandwidth_cases": 3,
    "max_separation_cases": 3,
    "max_snr_cases": 3,
    "max_accuracy_trials": 128,
    "max_fine_grid_factor": 16,
    "max_figure_groups": 6,
    "max_stored_numeric_values": 500000,
}


def finite_real(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_p31_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P31 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P31 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P31"]
    if len(matches) != 1:
        return errors + [f"expected one P31 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P31 {key} must be {expected!r}")
    return errors


def validate_controls(**overrides: object) -> dict[str, object]:
    unknown = set(overrides) - set(CANONICAL_CONTROLS)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls = dict(CANONICAL_CONTROLS)
    controls.update(overrides)
    positive = (
        "speed_of_light_mps", "sample_rate_hz", "capture_duration_s",
        "baseline_bandwidth_hz", "single_target_range_m",
        "two_target_separation_m", "echo_amplitude", "pulse_truncation_sigma",
        "accuracy_gate_half_width_m", "visible_peak_threshold_ratio",
        "comparison_tolerance",
    )
    for name in positive:
        if not finite_real(controls[name]) or controls[name] <= 0:
            raise ValueError(f"{name} must be finite and positive")
    if controls["visible_peak_threshold_ratio"] >= 1:
        raise ValueError("peak threshold ratio must be below one")
    integers = (
        "random_seed", "accuracy_trial_count", "fine_grid_factor",
        "max_record_samples", "max_pulse_samples", "max_correlation_lags",
        "max_bandwidth_cases", "max_separation_cases", "max_snr_cases",
        "max_accuracy_trials", "max_fine_grid_factor", "max_figure_groups",
        "max_stored_numeric_values",
    )
    for name in integers:
        value = controls[name]
        if not finite_real(value) or int(value) != value or value <= 0:
            raise ValueError(f"{name} must be a positive finite integer")
    if controls["random_seed"] != 3101:
        raise ValueError("random seed must remain canonical")
    if not finite_real(controls["high_matched_snr_db"]):
        raise ValueError("high SNR must be finite")
    vectors = (
        ("bandwidth_sweep_hz", "max_bandwidth_cases"),
        ("separation_sweep_m", "max_separation_cases"),
        ("accuracy_snr_db_sweep", "max_snr_cases"),
    )
    for name, maximum_name in vectors:
        values = controls[name]
        if (
            not isinstance(values, (tuple, list))
            or len(values) < 2
            or len(values) > controls[maximum_name]
            or any(not finite_real(value) for value in values)
            or any(right <= left for left, right in zip(values, values[1:]))
        ):
            raise ValueError(f"{name} must be a bounded increasing finite vector")
    if min(controls["bandwidth_sweep_hz"]) <= 0:
        raise ValueError("bandwidth must be positive")
    if max(controls["bandwidth_sweep_hz"]) >= controls["sample_rate_hz"] / 2:
        raise ValueError("bandwidth exceeds Nyquist")
    if min(controls["separation_sweep_m"]) <= 0:
        raise ValueError("separation must be positive")
    record_count = round(controls["capture_duration_s"] * controls["sample_rate_hz"])
    sigma_t = math.sqrt(math.log(2)) / (math.pi * min(controls["bandwidth_sweep_hz"]))
    pulse_count = 2 * math.ceil(
        controls["pulse_truncation_sigma"] * sigma_t * controls["sample_rate_hz"]
    ) + 1
    largest_delay_samples = (
        2
        * (controls["single_target_range_m"] + max(controls["separation_sweep_m"]))
        / controls["speed_of_light_mps"]
        * controls["sample_rate_hz"]
    )
    stored = (
        controls["accuracy_trial_count"] * record_count
        + 60 * record_count
        + 20 * controls["fine_grid_factor"] * record_count
    )
    if (
        record_count > controls["max_record_samples"]
        or pulse_count > controls["max_pulse_samples"]
        or record_count > controls["max_correlation_lags"]
        or controls["accuracy_trial_count"] > controls["max_accuracy_trials"]
        or controls["fine_grid_factor"] > controls["max_fine_grid_factor"]
        or stored > controls["max_stored_numeric_values"]
    ):
        raise ValueError("resource ceiling exceeded")
    if largest_delay_samples + pulse_count + 1 >= record_count:
        raise ValueError("delayed pulse or peak neighborhood does not fit")
    nominal = controls["speed_of_light_mps"] / (2 * controls["baseline_bandwidth_hz"])
    if (
        controls["accuracy_gate_half_width_m"] < 2 * nominal
        or controls["single_target_range_m"] <= controls["accuracy_gate_half_width_m"]
    ):
        raise ValueError("accuracy gate is inconsistent")
    return controls


def parse_matlab_controls(source: str) -> dict[str, object]:
    parsed: dict[str, object] = {}
    vectors = {"bandwidth_sweep_hz", "separation_sweep_m", "accuracy_snr_db_sweep"}
    for name, expected in CANONICAL_CONTROLS.items():
        if name in vectors:
            matches = re.findall(rf"(?m)^{re.escape(name)}\s*=\s*\[([^\]]+)\]\s*;", source)
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


def build_gaussian_pulse(bandwidth_hz: float, controls: dict[str, object]) -> list[float]:
    sigma_t = math.sqrt(math.log(2)) / (math.pi * bandwidth_hz)
    fs = controls["sample_rate_hz"]
    half = math.ceil(controls["pulse_truncation_sigma"] * sigma_t * fs)
    pulse = [math.exp(-0.5 * ((index / fs) / sigma_t) ** 2) for index in range(-half, half + 1)]
    energy = math.sqrt(sum(value * value for value in pulse))
    return [value / energy for value in pulse]


def insert_echo(
    pulse: list[float], record_count: int, delay_samples: float, amplitude: float = 1.0
) -> list[float]:
    if record_count <= 0 or not math.isfinite(delay_samples) or delay_samples < 0:
        raise ValueError("echo controls must be finite and nonnegative")
    if delay_samples + len(pulse) + 1 >= record_count:
        raise ValueError("echo does not fit")
    output = [0.0] * record_count
    for record_index in range(record_count):
        source_position = record_index - delay_samples
        left_index = math.floor(source_position)
        fraction = source_position - left_index
        left = pulse[left_index] if 0 <= left_index < len(pulse) else 0.0
        right_index = left_index + 1
        right = pulse[right_index] if 0 <= right_index < len(pulse) else 0.0
        output[record_index] = amplitude * ((1 - fraction) * left + fraction * right)
    return output


def matched_response(received: list[float], pulse: list[float]) -> list[float]:
    if not pulse or len(pulse) > len(received):
        raise ValueError("pulse must fit received record")
    return [
        sum(received[lag + index] * pulse[index] for index in range(len(pulse)))
        for lag in range(len(received) - len(pulse) + 1)
    ]


def visible_peaks(magnitude: list[float], threshold_ratio: float = 0.35) -> list[int]:
    threshold = threshold_ratio * max(magnitude)
    return [
        index
        for index in range(1, len(magnitude) - 1)
        if magnitude[index] > magnitude[index - 1]
        and magnitude[index] >= magnitude[index + 1]
        and magnitude[index] >= threshold
    ]


def half_power_width(magnitude: list[float], spacing: float) -> float:
    selected = [index for index, value in enumerate(magnitude) if value >= max(magnitude) / math.sqrt(2)]
    if len(selected) < 2:
        raise ValueError("response has no measurable half-power width")
    return (selected[-1] - selected[0]) * spacing


def refined_peak(magnitude: list[float], peak: int) -> float:
    if peak <= 0 or peak >= len(magnitude) - 1:
        raise ValueError("peak needs neighbors")
    left, center, right = magnitude[peak - 1 : peak + 2]
    denominator = left - 2 * center + right
    if abs(denominator) <= 1e-12:
        raise ValueError("peak has no curvature")
    offset = 0.5 * (left - right) / denominator
    if abs(offset) > 0.5 + 1e-12:
        raise ValueError("refinement escaped selected bin")
    return peak + offset


def clean_pair_case(bandwidth_hz: float, separation_m: float) -> tuple[list[float], float]:
    controls = validate_controls()
    fs = controls["sample_rate_hz"]
    c = controls["speed_of_light_mps"]
    record_count = round(controls["capture_duration_s"] * fs)
    pulse = build_gaussian_pulse(bandwidth_hz, controls)
    first_delay = 2 * controls["single_target_range_m"] / c * fs
    second_delay = 2 * (controls["single_target_range_m"] + separation_m) / c * fs
    first = insert_echo(pulse, record_count, first_delay)
    second = insert_echo(pulse, record_count, second_delay)
    pair = matched_response([left + right for left, right in zip(first, second)], pulse)
    single = matched_response(first, pulse)
    spacing = c / (2 * fs)
    return pair, half_power_width([abs(value) for value in single], spacing)


def accuracy_sweep_metrics() -> tuple[list[float], list[float], list[float], list[float]]:
    """Independently reproduce the bounded single-target SNR experiment."""
    controls = validate_controls()
    fs = controls["sample_rate_hz"]
    c = controls["speed_of_light_mps"]
    record_count = round(controls["capture_duration_s"] * fs)
    pulse = build_gaussian_pulse(controls["baseline_bandwidth_hz"], controls)
    true_delay = 2 * controls["single_target_range_m"] / c * fs
    echo = insert_echo(pulse, record_count, true_delay)
    clean_response = matched_response(echo, pulse)
    clean_peak = max(abs(value) for value in clean_response)
    range_spacing = c / (2 * fs)
    response_width = half_power_width(
        [abs(value) for value in clean_response], range_spacing
    )
    gate_indices = [
        lag
        for lag in range(len(clean_response))
        if abs(lag * range_spacing - controls["single_target_range_m"])
        <= controls["accuracy_gate_half_width_m"]
    ]

    generator = random.Random(controls["random_seed"])
    unit_noise = [
        [generator.gauss(0.0, 1.0) for _ in range(record_count)]
        for _ in range(controls["accuracy_trial_count"])
    ]

    biases: list[float] = []
    standard_deviations: list[float] = []
    rmses: list[float] = []
    widths: list[float] = []
    for snr_db in controls["accuracy_snr_db_sweep"]:
        noise_sigma = clean_peak / (10 ** (snr_db / 20))
        estimates: list[float] = []
        for trial_noise in unit_noise:
            received = [
                signal + noise_sigma * noise
                for signal, noise in zip(echo, trial_noise)
            ]
            magnitude = [abs(value) for value in matched_response(received, pulse)]
            peak = max(gate_indices, key=magnitude.__getitem__)
            left, center, right = magnitude[peak - 1 : peak + 2]
            denominator = left - 2 * center + right
            if denominator < -controls["comparison_tolerance"]:
                offset = 0.5 * (left - right) / denominator
                offset = max(-0.5, min(0.5, offset))
            else:
                offset = 0.0
            estimates.append((peak + offset) * range_spacing)
        errors = [estimate - controls["single_target_range_m"] for estimate in estimates]
        bias = sum(errors) / len(errors)
        sample_variance = sum((error - bias) ** 2 for error in errors) / (len(errors) - 1)
        biases.append(bias)
        standard_deviations.append(math.sqrt(sample_variance))
        rmses.append(math.sqrt(sum(error * error for error in errors) / len(errors)))
        widths.append(response_width)
    return biases, standard_deviations, rmses, widths


class P31ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text())
        cls.text = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        cls.experiment = cls.text["experiment.m"]

    def test_complete_artifacts_exact_identity_and_prerequisite(self):
        self.assertEqual(validate_p31_contract(MODULE, self.manifest), [])
        for text in self.text.values():
            self.assertIn(QUESTION, text)
        prerequisite = next(item for item in self.manifest["modules"] if item["id"] == "P30")
        self.assertEqual(prerequisite["status"], "implemented")

    def test_contract_validator_rejects_missing_empty_duplicate_and_malformed(self):
        self.assertIn("manifest modules must be a list", validate_p31_contract(MODULE, {}))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p31_contract(MODULE, {"modules": ["bad"]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P31 manifest entry, found 2", validate_p31_contract(MODULE, duplicate))
        wrong = copy.deepcopy(self.manifest)
        entry = next(item for item in wrong["modules"] if item["id"] == "P31")
        entry["guiding_question"] = "generic question"
        entry["status"] = "scaffolded"
        errors = validate_p31_contract(MODULE, wrong)
        self.assertIn(f"P31 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P31 status must be 'implemented'", errors)
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary)
            for name in ARTIFACTS:
                (copied / name).write_text("content", encoding="utf-8")
            (copied / "experiment.m").unlink()
            (copied / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p31_contract(copied, self.manifest)
            self.assertIn("P31 missing experiment.m", errors)
            self.assertIn("P31 empty lesson.md", errors)

    def test_controls_are_canonical_malformed_inputs_fail_and_resources_are_bounded(self):
        self.assertEqual(parse_matlab_controls(self.experiment), CANONICAL_CONTROLS)
        self.assertEqual(validate_controls(), CANONICAL_CONTROLS)
        malformed = (
            {"random_seed": True}, {"random_seed": 3102},
            {"speed_of_light_mps": float("nan")}, {"sample_rate_hz": 10e6},
            {"capture_duration_s": 1e-6}, {"baseline_bandwidth_hz": 0.0},
            {"bandwidth_sweep_hz": (2e6, 2e6)},
            {"bandwidth_sweep_hz": (2e6, 50e6)},
            {"single_target_range_m": float("inf")},
            {"separation_sweep_m": (45.0, 10.0)}, {"echo_amplitude": "one"},
            {"accuracy_snr_db_sweep": (0.0, float("nan"))},
            {"accuracy_trial_count": 129}, {"pulse_truncation_sigma": 20.0},
            {"accuracy_gate_half_width_m": 10.0}, {"fine_grid_factor": 17},
            {"visible_peak_threshold_ratio": 1.0}, {"comparison_tolerance": 0.0},
            {"max_record_samples": 959}, {"max_pulse_samples": 80},
            {"max_correlation_lags": 959}, {"max_bandwidth_cases": 2},
            {"max_separation_cases": 2}, {"max_snr_cases": 2},
            {"max_accuracy_trials": 127}, {"max_fine_grid_factor": 15},
            {"max_stored_numeric_values": 1000},
        )
        for override in malformed:
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_controls(**override)
        with self.assertRaises(ValueError):
            validate_controls(unapproved_control=1)

    def test_source_mutations_are_rejected_by_canonical_parser_or_markers(self):
        mutation = self.experiment.replace("sample_rate_hz = 80e6;", "sample_rate_hz = 20e6;")
        self.assertNotEqual(parse_matlab_controls(mutation), CANONICAL_CONTROLS)
        required = (
            "sigma_t=sqrt(log(2))/(pi*B)",
            "y[ell] = sum_m x[ell+m]*conj(s[m])",
            "speed_of_light_mps/(2*baseline_bandwidth_hz)",
            "speed_of_light_mps*baseline_lags_samples/",
            "(2*sample_rate_hz)",
            "broken_model_valid = false;",
            "recovery_response_exact_match",
        )
        for marker in required:
            self.assertIn(marker, self.experiment)

    def test_gaussian_echo_is_normalized_fractional_zero_extended_and_non_circular(self):
        controls = validate_controls()
        pulse = build_gaussian_pulse(controls["baseline_bandwidth_hz"], controls)
        self.assertAlmostEqual(sum(value * value for value in pulse), 1.0)
        self.assertEqual(len(pulse) % 2, 1)
        echo = insert_echo(pulse, 960, 480.5)
        self.assertTrue(all(value == 0 for value in echo[:480]))
        self.assertTrue(all(value == 0 for value in echo[480 + len(pulse) + 1 :]))
        self.assertAlmostEqual(sum(echo), sum(pulse), places=12)
        with self.assertRaises(ValueError):
            insert_echo(pulse, 10, 2)
        with self.assertRaises(ValueError):
            insert_echo(pulse, 960, float("nan"))

    def test_bandwidth_sweep_narrows_response_and_changes_one_peak_to_two(self):
        controls = validate_controls()
        widths = []
        counts = []
        nominal = []
        for bandwidth in controls["bandwidth_sweep_hz"]:
            pair, width = clean_pair_case(bandwidth, controls["two_target_separation_m"])
            widths.append(width)
            counts.append(len(visible_peaks([abs(value) for value in pair])))
            nominal.append(controls["speed_of_light_mps"] / (2 * bandwidth))
        self.assertTrue(all(right < left for left, right in zip(widths, widths[1:])))
        self.assertTrue(all(right < left for left, right in zip(nominal, nominal[1:])))
        self.assertEqual(counts, [1, 1, 2])

    def test_spacing_sweep_changes_only_geometry_and_has_expected_peak_counts(self):
        controls = validate_controls()
        counts = []
        widths = []
        for separation in controls["separation_sweep_m"]:
            pair, width = clean_pair_case(controls["baseline_bandwidth_hz"], separation)
            counts.append(len(visible_peaks([abs(value) for value in pair])))
            widths.append(width)
        self.assertEqual(counts, [1, 1, 2])
        self.assertEqual(widths, [widths[0]] * 3)

    def test_single_target_refinement_is_accurate_below_response_width(self):
        controls = validate_controls()
        fs = controls["sample_rate_hz"]
        c = controls["speed_of_light_mps"]
        record_count = round(controls["capture_duration_s"] * fs)
        pulse = build_gaussian_pulse(controls["baseline_bandwidth_hz"], controls)
        true_delay = 2 * controls["single_target_range_m"] / c * fs
        echo = insert_echo(pulse, record_count, true_delay)
        response = matched_response(echo, pulse)
        magnitude = [abs(value) for value in response]
        peak = max(range(len(magnitude)), key=magnitude.__getitem__)
        refined = refined_peak(magnitude, peak)
        spacing = c / (2 * fs)
        width = half_power_width(magnitude, spacing)
        integer_error = peak * spacing - controls["single_target_range_m"]
        refined_error = refined * spacing - controls["single_target_range_m"]
        self.assertLessEqual(abs(integer_error), spacing / 2)
        self.assertLess(abs(refined_error), abs(integer_error))
        self.assertLess(abs(refined_error), width / 20)
        self.assertLess(width, c / controls["baseline_bandwidth_hz"])
        with self.assertRaises(ValueError):
            refined_peak([1.0, 1.0, 1.0], 1)

    def test_seeded_snr_sweep_improves_error_without_changing_response_width(self):
        biases, standard_deviations, rmses, widths = accuracy_sweep_metrics()
        self.assertEqual(widths, [widths[0]] * 3)
        self.assertLess(rmses[-1], rmses[0] / 5)
        self.assertLess(standard_deviations[-1], standard_deviations[0] / 5)
        self.assertLess(rmses[-1], widths[-1] / 20)
        for actual, expected in zip(
            biases, (-4.412788, -0.130994, -0.019772)
        ):
            self.assertAlmostEqual(actual, expected, places=6)
        for actual, expected in zip(
            standard_deviations, (45.285779, 2.583411, 0.447242)
        ):
            self.assertAlmostEqual(actual, expected, places=6)
        for actual, expected in zip(rmses, (45.323864, 2.576632, 0.445930)):
            self.assertAlmostEqual(actual, expected, places=6)

    def test_dense_display_does_not_create_a_second_physical_peak(self):
        controls = validate_controls()
        pair, _ = clean_pair_case(
            controls["baseline_bandwidth_hz"], controls["two_target_separation_m"]
        )
        magnitude = [abs(value) for value in pair]
        self.assertEqual(len(visible_peaks(magnitude)), 1)
        fine: list[float] = []
        factor = controls["fine_grid_factor"]
        for index in range(len(magnitude) - 1):
            for step in range(factor):
                fraction = step / factor
                fine.append((1 - fraction) * magnitude[index] + fraction * magnitude[index + 1])
        fine.append(magnitude[-1])
        best = sorted(range(len(fine)), key=fine.__getitem__, reverse=True)[:2]
        reported_separation = abs(best[0] - best[1]) / factor * (
            controls["speed_of_light_mps"] / (2 * controls["sample_rate_hz"])
        )
        self.assertLessEqual(reported_separation, 2 * controls["speed_of_light_mps"] / (2 * controls["sample_rate_hz"]) / factor)
        self.assertGreater(abs(reported_separation - controls["two_target_separation_m"]), 20)

    def test_source_binds_sweeps_failure_recovery_resources_and_no_hidden_toolbox(self):
        for marker in (
            "%% Sweep 1: bandwidth only, fixed targets and fixed high SNR",
            "%% Sweep 2: target spacing only, fixed 4 MHz waveform and fixed high SNR",
            "%% Sweep 3: SNR changes estimator error, not waveform response width",
            "%% Intentionally broken case: call two dense display samples two targets",
            "%% Recovery: restore physical peak counting and change actual bandwidth",
            "source_position = (record_index-1)-delay_samples;",
            "aligned_sum = aligned_sum+received_signal(received_index)*",
            "conj(pulse(pulse_index));",
            "full_half_power_width",
            "refine_parabolic_peak",
            "case_high_noise_sigma = case_clean_peak/10^(high_matched_snr_db/20);",
            "case_noise_sigma = baseline_clean_peak/",
            "accuracy_rmse_m(end) < accuracy_rmse_m(1)/5",
            "all(accuracy_response_width_m == baseline_response_width_m)",
            "isequal(bandwidth_peak_count, [1 1 2])",
            "isequal(separation_peak_count, [1 1 2])",
            "'nominal_resolution_m'",
            "'standard_deviation_m'",
            "'model_valid'",
            "'response_exact_match'",
        ):
            self.assertIn(marker, self.experiment)
        self.assertEqual(self.experiment.count("RandStream('mt19937ar', 'Seed', random_seed)"), 2)
        self.assertEqual(len(re.findall(r"\brandn\s*\(", self.experiment)), 3)
        validation = self.experiment.index("% Validation succeeded:")
        for work in ("zeros(", "ones(", "RandStream(", "randn(", "figure(", "findall("):
            self.assertGreater(self.experiment.index(work), validation)
        self.assertNotRegex(self.experiment, r"(?m)^\s*(?:while|parfor)\b|^\s*(?:timer|pause)\s*\(")
        for pattern in (
            r"\bxcorr\s*\(", r"\bfindpeaks\s*\(", r"\bphased\.", r"\bawgn\s*\(",
            r"\bcircshift\s*\(", r"\brng\s*\(", r"\bclose\s+all\b", r"\bsave\s*\(",
            r"\bload\s*\(", r"\bfopen\s*\(", r"\bweb(read|write|save)\s*\(", r"\bsystem\s*\(",
        ):
            self.assertNotRegex(self.experiment, pattern)

    def test_plots_metrics_and_units_are_purposeful(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 6)
        for label in (
            "Pulse time about envelope center (microseconds)",
            "Two-sided -3 dB pulse bandwidth (MHz)",
            "Monostatic range c tau / 2 (m)",
            "Range width (m)",
            "Matched-filter SNR (dB)",
            "Single-target range error metric (m)",
            "Measured full -3 dB response width (m)",
            "Interpolated display range (m)",
        ):
            self.assertIn(label, self.experiment)

    def test_docs_are_concept_first_complete_and_placeholder_free(self):
        lesson = self.text["lesson.md"]
        walkthrough = self.text["walkthrough.md"]
        checks = self.text["checks.md"]
        for marker in (
            "Physical model: width versus location", "From bandwidth to a range response",
            "Accuracy can be sub-response-width", "The blended-peak trap",
            "Assumptions and limiting cases", "Common interpretation mistakes",
            "Dependencies and concept connection",
        ):
            self.assertIn(marker, lesson)
        for marker in (
            "Baseline observation", "Sweep one variable: bandwidth only",
            "Sweep one variable: target spacing only", "Hold bandwidth fixed",
            "Intentionally broken case", "Recover and connect the concept",
        ):
            self.assertIn(marker.lower(), walkthrough.lower())
        self.assertIn("`[0 15 30]` dB", walkthrough)
        self.assertNotIn("`[5 15 30]` dB", walkthrough)
        for marker in (
            "Observation checks", "Prediction checks", "Interpretation checks",
            "Failure and recovery checks", "Completion checklist", "Short teach-back rubric",
        ):
            self.assertIn(marker, checks)
        combined = "\n".join(self.text.values())
        self.assertNotIn("TODO", combined)
        self.assertNotRegex(combined, r"(?i)implementation batch `P31` is pending")
        for term in ("accuracy", "bias", "precision", "standard deviation", "RMSE", "resolution"):
            self.assertIn(term.lower(), combined.lower())

    def test_cancellation_isolation_compatibility_rollback_and_cli_timeout(self):
        operational = self.text["walkthrough.md"] + self.text["checks.md"]
        for marker in (
            "Ctrl+C", "private seed", "global random stream", "figures tagged `P31`",
            ".learning/", "worker", "timer", "external transaction", "base MATLAB",
            "rollback", "scaffolded",
        ):
            self.assertIn(marker.lower(), operational.lower())
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P31'))", self.experiment)
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 31 separates bandwidth-driven", root_readme)
        self.assertIn("Project 31 follows P30", start_here)
        self.assertRegex(module_index, r"\| \[P31\].*\| implemented \|")

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
            process = subprocess.run(
                [str(fixture_cli), "start", "31"], cwd=fixture_root, text=True,
                capture_output=True, env=os.environ.copy(), timeout=10,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("P31 — Separate Range Resolution from Range Accuracy", process.stdout)
            self.assertIn("status: implemented", process.stdout)
            self.assertIn("Tutor entry", process.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_retained_evidence_is_honest_and_complete(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P31-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        for marker in (
            "Acceptance mapping", "Figure and metric inventory", "Independent oracle results",
            "Exact commands and results", "Changed and preserved invariants",
            "Residual risks and unperformed validation", "Rollback and recovery",
            "Validation class", "MATLAB runtime status", "Toolboxes", "MATLAB", "did not run",
        ):
            self.assertIn(marker, evidence)
        for command in (
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
        ):
            self.assertIn(command, evidence)
        for unit in ("MHz", "dB", "microseconds", "samples", "m", "500,000"):
            self.assertIn(unit, evidence)
        self.assertNotIn("PENDING —", evidence)


if __name__ == "__main__":
    unittest.main()
