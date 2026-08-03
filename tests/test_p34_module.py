from __future__ import annotations

import cmath
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
MODULE = ROOT / "modules/34-plot-and-interpret-the-ambiguity-function"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How does a waveform respond to simultaneous delay and Doppler mismatch?"
EXPECTED_IDENTITY = {
    "number": 34,
    "id": "P34",
    "title": "Plot and Interpret the Ambiguity Function",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "plot-and-interpret-the-ambiguity-function",
    "folder": "modules/34-plot-and-interpret-the-ambiguity-function",
    "status": "implemented",
    "implementation_batch": "P34",
}
CANONICAL_CONTROLS = {
    "random_seed": 3401,
    "sample_rate_hz": 10e6,
    "baseline_pulse_duration_s": 13e-6,
    "baseline_bandwidth_hz": 3e6,
    "baseline_code_length_chips": 13,
    "chip_duration_s": 1e-6,
    "doppler_limit_hz": 200e3,
    "doppler_bin_count": 101,
    "duration_sweep_s": (6.5e-6, 13e-6, 26e-6),
    "bandwidth_sweep_hz": (1.5e6, 3e6, 4.5e6),
    "code_length_sweep_chips": (7, 13, 31),
    "ridge_probe_doppler_hz": 120e3,
    "comparison_tolerance": 1e-10,
    "db_floor": -60.0,
    "max_signal_samples": 310,
    "max_surface_signal_samples": 160,
    "max_surface_delay_bins": 319,
    "max_doppler_bins": 121,
    "max_duration_cases": 3,
    "max_bandwidth_cases": 3,
    "max_code_length_cases": 3,
    "max_figure_groups": 7,
    "max_stored_numeric_values": 500000,
    "max_complex_multiply_accumulates": 10000000,
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p34_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P34 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P34 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P34"]
    if len(matches) != 1:
        return errors + [f"expected one P34 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P34 {key} must be {expected!r}")
    return errors


def validate_controls(**overrides: object) -> dict[str, object]:
    unknown = set(overrides) - set(CANONICAL_CONTROLS)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls = dict(CANONICAL_CONTROLS)
    controls.update(overrides)

    positive = (
        "sample_rate_hz",
        "baseline_pulse_duration_s",
        "baseline_bandwidth_hz",
        "baseline_code_length_chips",
        "chip_duration_s",
        "doppler_limit_hz",
        "doppler_bin_count",
        "ridge_probe_doppler_hz",
        "comparison_tolerance",
        "max_signal_samples",
        "max_surface_signal_samples",
        "max_surface_delay_bins",
        "max_doppler_bins",
        "max_duration_cases",
        "max_bandwidth_cases",
        "max_code_length_cases",
        "max_figure_groups",
        "max_stored_numeric_values",
        "max_complex_multiply_accumulates",
    )
    for name in positive:
        if not finite_real(controls[name]) or controls[name] <= 0:
            raise ValueError(f"{name} must be finite and positive")
    if controls["random_seed"] != 3401 or not finite_real(controls["random_seed"]):
        raise ValueError("random seed must remain canonical")
    if not finite_real(controls["db_floor"]) or controls["db_floor"] >= 0:
        raise ValueError("dB floor must be finite and negative")

    integer_names = (
        "random_seed",
        "baseline_code_length_chips",
        "doppler_bin_count",
        "max_signal_samples",
        "max_surface_signal_samples",
        "max_surface_delay_bins",
        "max_doppler_bins",
        "max_duration_cases",
        "max_bandwidth_cases",
        "max_code_length_cases",
        "max_figure_groups",
        "max_stored_numeric_values",
        "max_complex_multiply_accumulates",
    )
    for name in integer_names:
        if int(controls[name]) != controls[name]:
            raise ValueError(f"{name} must be an integer")
    if controls["doppler_bin_count"] % 2 != 1:
        raise ValueError("Doppler grid must contain zero")
    if controls["baseline_bandwidth_hz"] >= controls["sample_rate_hz"] / 2:
        raise ValueError("baseline LFM bandwidth exceeds Nyquist")
    if controls["ridge_probe_doppler_hz"] >= controls["doppler_limit_hz"]:
        raise ValueError("ridge probe must be inside the Doppler grid")

    vector_specs = (
        ("duration_sweep_s", "max_duration_cases", False),
        ("bandwidth_sweep_hz", "max_bandwidth_cases", False),
        ("code_length_sweep_chips", "max_code_length_cases", True),
    )
    for name, maximum_name, integers_only in vector_specs:
        values = controls[name]
        if (
            not isinstance(values, (tuple, list))
            or len(values) < 2
            or len(values) > controls[maximum_name]
            or any(not finite_real(item) or item <= 0 for item in values)
            or any(right <= left for left, right in zip(values, values[1:]))
            or (integers_only and any(int(item) != item for item in values))
        ):
            raise ValueError(f"{name} must be a bounded increasing positive vector")
    if max(controls["bandwidth_sweep_hz"]) >= controls["sample_rate_hz"] / 2:
        raise ValueError("bandwidth sweep exceeds Nyquist")
    if not any(
        math.isclose(value, controls["baseline_pulse_duration_s"], abs_tol=controls["comparison_tolerance"])
        for value in controls["duration_sweep_s"]
    ):
        raise ValueError("duration sweep must include baseline")
    if not any(
        math.isclose(value, controls["baseline_bandwidth_hz"], abs_tol=controls["comparison_tolerance"])
        for value in controls["bandwidth_sweep_hz"]
    ):
        raise ValueError("bandwidth sweep must include baseline")
    if controls["baseline_code_length_chips"] not in controls["code_length_sweep_chips"]:
        raise ValueError("code-length sweep must include baseline")

    baseline_count = round(controls["baseline_pulse_duration_s"] * controls["sample_rate_hz"])
    samples_per_chip = round(controls["chip_duration_s"] * controls["sample_rate_hz"])
    duration_counts = [round(value * controls["sample_rate_hz"]) for value in controls["duration_sweep_s"]]
    code_counts = [int(value) * samples_per_chip for value in controls["code_length_sweep_chips"]]
    surface_delay_count = 2 * baseline_count - 1
    stored = (
        4 * surface_delay_count * controls["doppler_bin_count"]
        + 20 * controls["max_signal_samples"]
        + 40 * controls["max_surface_delay_bins"]
        + 20 * controls["max_doppler_bins"]
    )
    operations = (
        4 * controls["doppler_bin_count"] * baseline_count**2
        + sum(count**2 + count * controls["doppler_bin_count"] for count in duration_counts)
        + len(controls["bandwidth_sweep_hz"]) * (2 * baseline_count**2)
        + sum(count**2 + count * controls["doppler_bin_count"] for count in code_counts)
        + baseline_count * surface_delay_count
    )
    if baseline_count < 3 or baseline_count > controls["max_surface_signal_samples"]:
        raise ValueError("baseline surface resource ceiling exceeded")
    if samples_per_chip < 2:
        raise ValueError("chip must contain at least two samples")
    if baseline_count != controls["baseline_code_length_chips"] * samples_per_chip:
        raise ValueError("baseline duration and code duration must agree")
    if max(duration_counts + code_counts) > controls["max_signal_samples"]:
        raise ValueError("signal resource ceiling exceeded")
    if surface_delay_count > controls["max_surface_delay_bins"]:
        raise ValueError("surface delay resource ceiling exceeded")
    if controls["doppler_bin_count"] > controls["max_doppler_bins"]:
        raise ValueError("Doppler resource ceiling exceeded")
    if controls["max_figure_groups"] < 7:
        raise ValueError("figure resource ceiling exceeded")
    if stored > controls["max_stored_numeric_values"]:
        raise ValueError("stored-value resource ceiling exceeded")
    if operations > controls["max_complex_multiply_accumulates"]:
        raise ValueError("operation resource ceiling exceeded")
    return controls


def parse_matlab_controls(source: str) -> dict[str, object]:
    parsed: dict[str, object] = {}
    vector_names = {
        "duration_sweep_s",
        "bandwidth_sweep_hz",
        "code_length_sweep_chips",
    }
    for name, expected in CANONICAL_CONTROLS.items():
        if name in vector_names:
            matches = re.findall(rf"(?m)^{name}\s*=\s*\[([^\]]+)\]\s*;", source)
            if len(matches) != 1:
                raise ValueError(f"expected one vector assignment for {name}")
            values = tuple(float(item) for item in matches[0].split())
            parsed[name] = tuple(int(item) for item in values) if all(
                isinstance(item, int) for item in expected
            ) else values
            continue
        matches = re.findall(
            rf"(?mi)^{name}\s*=\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?)\s*;",
            source,
        )
        if len(matches) != 1:
            raise ValueError(f"expected one numeric assignment for {name}")
        value = float(matches[0])
        parsed[name] = int(value) if isinstance(expected, int) else value
    return parsed


def ambiguity_magnitude(
    signal: list[complex], sample_rate_hz: float, delays: list[int], dopplers: list[float]
) -> list[list[float]]:
    if (
        not signal
        or not finite_real(sample_rate_hz)
        or sample_rate_hz <= 0
        or not delays
        or not dopplers
        or any(not isinstance(delay, int) or abs(delay) >= len(signal) for delay in delays)
        or any(not finite_real(doppler) for doppler in dopplers)
        or any(not math.isfinite(value.real) or not math.isfinite(value.imag) for value in signal)
    ):
        raise ValueError("ambiguity inputs must be finite, bounded vectors")
    energy = sum(abs(value) ** 2 for value in signal)
    if energy <= 0:
        raise ValueError("signal energy must be positive")
    output: list[list[float]] = []
    for doppler in dopplers:
        row: list[float] = []
        for delay in delays:
            if delay >= 0:
                pairs = ((index, index - delay) for index in range(delay, len(signal)))
            else:
                pairs = ((index, index - delay) for index in range(0, len(signal) + delay))
            value = sum(
                signal[current]
                * signal[shifted].conjugate()
                * cmath.exp(-1j * 2 * math.pi * doppler * current / sample_rate_hz)
                for current, shifted in pairs
            )
            row.append(abs(value) / energy)
        output.append(row)
    return output


def mainlobe_width(axis: list[float], magnitude: list[float]) -> float:
    if (
        len(axis) != len(magnitude)
        or len(axis) < 3
        or any(not finite_real(value) for value in axis + magnitude)
        or any(right <= left for left, right in zip(axis, axis[1:]))
        or any(value < 0 for value in magnitude)
    ):
        raise ValueError("width needs finite increasing samples")
    peak = max(range(len(magnitude)), key=magnitude.__getitem__)
    threshold = magnitude[peak] / math.sqrt(2)
    left = peak
    while left > 0 and magnitude[left] >= threshold:
        left -= 1
    right = peak
    while right < len(magnitude) - 1 and magnitude[right] >= threshold:
        right += 1
    if left == peak or right == peak or magnitude[left] >= threshold or magnitude[right] >= threshold:
        raise ValueError("mainlobe crossings are not bounded")
    left_crossing = axis[left] + (threshold - magnitude[left]) * (axis[left + 1] - axis[left]) / (
        magnitude[left + 1] - magnitude[left]
    )
    right_crossing = axis[right - 1] + (threshold - magnitude[right - 1]) * (
        axis[right] - axis[right - 1]
    ) / (magnitude[right] - magnitude[right - 1])
    return right_crossing - left_crossing


def rectangular_cuts(duration_s: float) -> tuple[float, float]:
    controls = validate_controls()
    count = round(duration_s * controls["sample_rate_hz"])
    signal = [1 + 0j] * count
    delays = list(range(-(count - 1), count))
    delay_axis_us = [1e6 * value / controls["sample_rate_hz"] for value in delays]
    dopplers = [
        -controls["doppler_limit_hz"]
        + 2 * controls["doppler_limit_hz"] * index / (controls["doppler_bin_count"] - 1)
        for index in range(controls["doppler_bin_count"])
    ]
    delay_cut = ambiguity_magnitude(signal, controls["sample_rate_hz"], delays, [0.0])[0]
    doppler_cut = [row[0] for row in ambiguity_magnitude(signal, controls["sample_rate_hz"], [0], dopplers)]
    return mainlobe_width(delay_axis_us, delay_cut), mainlobe_width([value / 1e3 for value in dopplers], doppler_cut)


def lfm_signal(bandwidth_hz: float) -> list[complex]:
    controls = validate_controls()
    count = round(controls["baseline_pulse_duration_s"] * controls["sample_rate_hz"])
    centered = [
        index / controls["sample_rate_hz"] - (count - 1) / (2 * controls["sample_rate_hz"])
        for index in range(count)
    ]
    rate = bandwidth_hz / controls["baseline_pulse_duration_s"]
    return [cmath.exp(1j * math.pi * rate * value**2) for value in centered]


def lfm_metrics(bandwidth_hz: float) -> tuple[float, float]:
    controls = validate_controls()
    signal = lfm_signal(bandwidth_hz)
    delays = list(range(-(len(signal) - 1), len(signal)))
    delay_axis_us = [1e6 * value / controls["sample_rate_hz"] for value in delays]
    cuts = ambiguity_magnitude(
        signal,
        controls["sample_rate_hz"],
        delays,
        [0.0, controls["ridge_probe_doppler_hz"]],
    )
    width = mainlobe_width(delay_axis_us, cuts[0])
    ridge_delay = delay_axis_us[max(range(len(cuts[1])), key=cuts[1].__getitem__)]
    return width, ridge_delay


def source_contract_errors(source: str) -> list[str]:
    required = (
        "function ambiguity_magnitude = explicit_ambiguity",
        "zero_filled_overlap = signal(current_indices).*",
        "conj(signal(shifted_indices))",
        "doppler_phasor = exp(-1j*2*pi*doppler_hz(doppler_index)*",
        "ambiguity_magnitude(doppler_index, delay_index) = abs(sum(",
        "4*surface_delay_count*doppler_bin_count",
        "4*doppler_bin_count*baseline_sample_count^2",
        "(2*baseline_sample_count^2)",
        "baseline_sample_count*surface_delay_count",
        "baseline_sample_count == ...",
        "baseline_code_length_chips*samples_per_chip",
        "broken_circular_delay_cut",
        "wrapped_shifted_indices = mod(",
        "broken_model_valid = false",
        "recovered_model_valid = true",
        "isequal(recovered_phase_code_ambiguity, phase_code_ambiguity)",
    )
    errors = [f"missing source marker: {marker}" for marker in required if marker not in source]
    for pattern in (r"\bambgfun\s*\(", r"\bxcorr\s*\(", r"\bphased\.", r"\bparfor\b"):
        if re.search(pattern, source, flags=re.IGNORECASE):
            errors.append(f"opaque or unsupported operation: {pattern}")
    return errors


class P34ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.text = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        cls.experiment = cls.text["experiment.m"]

    def test_complete_artifacts_exact_identity_and_prerequisite(self):
        self.assertEqual(validate_p34_contract(MODULE, self.manifest), [])
        for name, text in self.text.items():
            self.assertGreater(len(text), 100, name)
            self.assertIn(QUESTION, text)
        prerequisite = next(item for item in self.manifest["modules"] if item["id"] == "P33")
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertIn("P33", self.text["README.md"])
        self.assertIn("P33", self.text["lesson.md"])

    def test_contract_rejects_missing_empty_duplicate_and_malformed_inputs(self):
        self.assertIn("manifest modules must be a list", validate_p34_contract(MODULE, {}))
        self.assertIn("manifest module entries must be objects", validate_p34_contract(MODULE, {"modules": ["bad"]}))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P34 manifest entry, found 2", validate_p34_contract(MODULE, duplicate))
        wrong = copy.deepcopy(self.manifest)
        entry = next(item for item in wrong["modules"] if item["id"] == "P34")
        entry["guiding_question"] = "generic"
        entry["status"] = "scaffolded"
        errors = validate_p34_contract(MODULE, wrong)
        self.assertIn(f"P34 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P34 status must be 'implemented'", errors)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            for name in ARTIFACTS:
                (fixture / name).write_text("content\n", encoding="utf-8")
            (fixture / "experiment.m").unlink()
            (fixture / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p34_contract(fixture, self.manifest)
            self.assertIn("P34 missing experiment.m", errors)
            self.assertIn("P34 empty checks.md", errors)

    def test_controls_are_canonical_malformed_inputs_fail_and_resources_are_bounded(self):
        self.assertEqual(parse_matlab_controls(self.experiment), CANONICAL_CONTROLS)
        self.assertEqual(validate_controls(), CANONICAL_CONTROLS)
        malformed = (
            {"random_seed": True},
            {"random_seed": 3402},
            {"sample_rate_hz": float("nan")},
            {"sample_rate_hz": 9e6},
            {"baseline_pulse_duration_s": 0.0},
            {"baseline_bandwidth_hz": 5e6},
            {"baseline_code_length_chips": 13.5},
            {"chip_duration_s": 0.1e-6},
            {"chip_duration_s": 0.9e-6},
            {"doppler_limit_hz": float("inf")},
            {"doppler_bin_count": 100},
            {"duration_sweep_s": (13e-6, 6.5e-6)},
            {"duration_sweep_s": (6.5e-6, float("nan"))},
            {"duration_sweep_s": (6.5e-6, 26e-6)},
            {"bandwidth_sweep_hz": (1.5e6, 5e6)},
            {"bandwidth_sweep_hz": (1.5e6, 4.5e6)},
            {"code_length_sweep_chips": (7, 13.5, 31)},
            {"code_length_sweep_chips": (7, 31)},
            {"ridge_probe_doppler_hz": 200e3},
            {"comparison_tolerance": -1.0},
            {"db_floor": 0.0},
            {"max_signal_samples": 309},
            {"max_surface_signal_samples": 129},
            {"max_surface_delay_bins": 258},
            {"max_doppler_bins": 100},
            {"max_duration_cases": 2},
            {"max_bandwidth_cases": 2},
            {"max_code_length_cases": 2},
            {"max_figure_groups": 6},
            {"max_stored_numeric_values": 1},
            {"max_complex_multiply_accumulates": 1},
            {"not_a_control": 1},
        )
        for override in malformed:
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_controls(**override)

    def test_explicit_ambiguity_origin_symmetry_lfm_coupling_and_input_rejection(self):
        controls = validate_controls()
        signal = lfm_signal(controls["baseline_bandwidth_hz"])
        delays = list(range(-(len(signal) - 1), len(signal)))
        values = ambiguity_magnitude(
            signal,
            controls["sample_rate_hz"],
            delays,
            [-controls["ridge_probe_doppler_hz"], 0.0, controls["ridge_probe_doppler_hz"]],
        )
        center = len(signal) - 1
        self.assertAlmostEqual(values[1][center], 1.0, places=12)
        self.assertTrue(all(math.isclose(left, right, abs_tol=1e-12) for left, right in zip(values[1], reversed(values[1]))))
        negative_peak = delays[max(range(len(values[0])), key=values[0].__getitem__)]
        positive_peak = delays[max(range(len(values[2])), key=values[2].__getitem__)]
        self.assertLess(negative_peak, 0)
        self.assertGreater(positive_peak, 0)
        for args in (
            ([], controls["sample_rate_hz"], [0], [0.0]),
            ([0j], controls["sample_rate_hz"], [0], [0.0]),
            ([1 + 0j], 0.0, [0], [0.0]),
            ([1 + 0j], controls["sample_rate_hz"], [1], [0.0]),
            ([complex(float("nan"), 0)], controls["sample_rate_hz"], [0], [0.0]),
            ([1 + 0j], controls["sample_rate_hz"], [0], [float("inf")]),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                ambiguity_magnitude(*args)

    def test_joint_delay_doppler_surface_has_auto_ambiguity_symmetry(self):
        controls = validate_controls()
        signal = [
            1.0 + 0.0j,
            0.25 + 0.75j,
            -0.5 + 0.2j,
            -0.1 - 0.9j,
            0.6 - 0.4j,
        ]
        delays = list(range(-(len(signal) - 1), len(signal)))
        dopplers = [-123456.0, -40000.0, 0.0, 40000.0, 123456.0]
        surface = ambiguity_magnitude(
            signal,
            controls["sample_rate_hz"],
            delays,
            dopplers,
        )

        for doppler_index, doppler in enumerate(dopplers):
            for delay_index, delay in enumerate(delays):
                with self.subTest(delay=delay, doppler=doppler):
                    self.assertAlmostEqual(
                        surface[doppler_index][delay_index],
                        surface[-doppler_index - 1][-delay_index - 1],
                        places=12,
                    )

    def test_duration_bandwidth_and_code_length_behavior(self):
        controls = validate_controls()
        duration_metrics = [rectangular_cuts(value) for value in controls["duration_sweep_s"]]
        self.assertTrue(all(right[0] > left[0] for left, right in zip(duration_metrics, duration_metrics[1:])))
        self.assertTrue(all(right[1] < left[1] for left, right in zip(duration_metrics, duration_metrics[1:])))
        bandwidth_metrics = [lfm_metrics(value) for value in controls["bandwidth_sweep_hz"]]
        self.assertTrue(all(right[0] < left[0] for left, right in zip(bandwidth_metrics, bandwidth_metrics[1:])))
        self.assertTrue(all(abs(right[1]) <= abs(left[1]) for left, right in zip(bandwidth_metrics, bandwidth_metrics[1:])))
        code_doppler_widths = []
        dopplers = [
            -controls["doppler_limit_hz"]
            + 2 * controls["doppler_limit_hz"] * index / (controls["doppler_bin_count"] - 1)
            for index in range(controls["doppler_bin_count"])
        ]
        samples_per_chip = round(controls["chip_duration_s"] * controls["sample_rate_hz"])
        for chips in controls["code_length_sweep_chips"]:
            signal = [1 + 0j] * (chips * samples_per_chip)
            cut = [row[0] for row in ambiguity_magnitude(signal, controls["sample_rate_hz"], [0], dopplers)]
            code_doppler_widths.append(mainlobe_width([value / 1e3 for value in dopplers], cut))
        self.assertTrue(all(right < left for left, right in zip(code_doppler_widths, code_doppler_widths[1:])))

    def test_broken_circular_shift_fails_and_zero_fill_recovers(self):
        controls = validate_controls()
        count = round(controls["baseline_pulse_duration_s"] * controls["sample_rate_hz"])
        signal = [1 + 0j] * count
        extreme = -(count - 1)
        correct = ambiguity_magnitude(signal, controls["sample_rate_hz"], [extreme], [0.0])[0][0]
        broken = abs(
            sum(signal[index] * signal[(index - extreme) % count].conjugate() for index in range(count))
        ) / count
        recovered = ambiguity_magnitude(signal, controls["sample_rate_hz"], [extreme], [0.0])[0][0]
        self.assertAlmostEqual(correct, 1 / count, places=12)
        self.assertAlmostEqual(broken, 1.0, places=12)
        self.assertEqual(recovered, correct)

    def test_source_is_transparent_mutations_are_rejected_and_sweeps_are_marked(self):
        self.assertEqual(source_contract_errors(self.experiment), [])
        for old, new in (
            ("zero_filled_overlap = signal(current_indices).*", "hidden_overlap = signal(current_indices).*"),
            ("conj(signal(shifted_indices))", "signal(shifted_indices)"),
            ("doppler_phasor = exp(-1j*2*pi*doppler_hz(doppler_index)*", "doppler_phasor = ones(size("),
            ("wrapped_shifted_indices = mod(", "wrapped_shifted_indices = floor("),
            ("recovered_model_valid = true", "recovered_model_valid = false"),
            ("4*surface_delay_count*doppler_bin_count", "3*surface_delay_count*doppler_bin_count"),
            ("4*doppler_bin_count*baseline_sample_count^2", "3*doppler_bin_count*baseline_sample_count^2"),
            ("baseline_sample_count*surface_delay_count", "baseline_sample_count^2"),
            ("baseline_code_length_chips*samples_per_chip", "baseline_code_length_chips+samples_per_chip"),
        ):
            mutated = self.experiment.replace(old, new, 1)
            self.assertTrue(source_contract_errors(mutated), old)
        for marker in (
            "Sweep 1",
            "Sweep 2",
            "Sweep 3",
            "duration_sweep_s",
            "bandwidth_sweep_hz",
            "code_length_sweep_chips",
            "Intentionally broken case",
            "Recovery",
        ):
            self.assertIn(marker.lower(), self.experiment.lower())

    def test_docs_checks_catalog_cli_timeout_cancellation_and_isolation(self):
        combined = "\n".join(self.text.values())
        for marker in (
            "ambiguity",
            "rectangular",
            "LFM",
            "phase-coded",
            "zero-Doppler",
            "zero-delay",
            "sidelobe",
            "coupling",
            "P33",
            "base MATLAB",
        ):
            self.assertIn(marker.lower(), combined.lower())
        guided = self.text["walkthrough.md"] + self.text["checks.md"]
        for marker in (
            "Baseline observation",
            "Sweep one variable",
            "broken",
            "recover",
            "Observation checks",
            "Prediction checks",
            "Interpretation checks",
            "teach-back",
        ):
            self.assertIn(marker.lower(), guided.lower())
        for marker in (
            "Ctrl+C",
            "private seed",
            "global random stream",
            "figures tagged `P34`",
            ".learning/",
            "worker",
            "timer",
            "external transaction",
            "rollback",
            "scaffolded",
        ):
            self.assertIn(marker.lower(), guided.lower())
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P34'))", self.experiment)
        for figure_name in (
            "P34 waveform phase histories",
            "P34 baseline ambiguity surfaces",
            "P34 ambiguity cuts and LFM ridge",
            "P34 rectangular-duration sweep",
            "P34 LFM-bandwidth sweep",
            "P34 phase-code-length sweep",
            "P34 circular-shift failure and recovery",
        ):
            self.assertIn(f"'Name', '{figure_name}'", self.experiment)
            self.assertIn(f"`{figure_name}`", self.text["walkthrough.md"])
        self.assertNotRegex(self.text["walkthrough.md"], r"\bFigures?\s+[1-7]\b")
        self.assertEqual(self.experiment.count("RandStream('mt19937ar', 'Seed', random_seed)"), 2)
        self.assertNotRegex(self.experiment, r"(?m)^\s*while\s+true\b")
        self.assertNotIn("TODO", combined)
        self.assertNotRegex(combined, r"(?i)implementation batch `P34` is pending")
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("Project 34", root_readme)
        self.assertIn("Project 34", start_here)
        self.assertRegex(module_index, r"\| \[P34\].*\| implemented \|")
        state = ROOT / ".learning/progress.json"
        before = state.read_bytes() if state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir()
            target = fixture / EXPECTED_IDENTITY["folder"]
            target.mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
            shutil.copy2(ROOT / "curriculum/modules.json", fixture / "curriculum/modules.json")
            shutil.copy2(MODULE / "README.md", target / "README.md")
            result = subprocess.run(
                [str(fixture / "bin/learn"), "start", "34"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P34 — Plot and Interpret the Ambiguity Function", result.stdout)
            self.assertIn("status: implemented", result.stdout)
        self.assertEqual(state.read_bytes() if state.exists() else None, before)

    def test_artifact_newlines_placeholders_and_runtime_claim_boundary(self):
        combined = "\n".join(self.text.values())
        for name, text in self.text.items():
            self.assertTrue(text.endswith("\n"), name)
            self.assertFalse(text.endswith("\n\n"), name)
        for phrase in ("lorem ipsum", "placeholder", "fill this in", "coming soon"):
            self.assertNotIn(phrase, combined.lower())
        self.assertNotRegex(combined, r"(?i)MATLAB (?:was )?(?:executed|validated|passed)")

    def test_retained_evidence_is_honest_and_complete(self):
        paths = sorted((ROOT / "docs/evidence").glob("P34-*.md"))
        self.assertEqual(len(paths), 1)
        evidence = paths[0].read_text(encoding="utf-8")
        for marker in (
            "Acceptance mapping",
            "Figure and metric inventory",
            "Exact commands and results",
            "Changed and preserved invariants",
            "Residual risks and unperformed validation",
            "Rollback and recovery",
            "Validation class",
            "MATLAB runtime status",
            "Toolboxes",
            "did not run",
        ):
            self.assertIn(marker, evidence)
        for command in (
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
        ):
            self.assertIn(command, evidence)
        self.assertNotIn("PENDING —", evidence)


if __name__ == "__main__":
    unittest.main()
