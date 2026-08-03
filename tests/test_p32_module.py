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
MODULE = ROOT / "modules/32-perform-lfm-pulse-compression"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How can a long energetic pulse achieve short-pulse range resolution?"
EXPECTED_IDENTITY = {
    "number": 32,
    "id": "P32",
    "title": "Perform LFM Pulse Compression",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "perform-lfm-pulse-compression",
    "folder": "modules/32-perform-lfm-pulse-compression",
    "status": "implemented",
    "implementation_batch": "P32",
}
CANONICAL_CONTROLS = {
    "random_seed": 3201,
    "speed_of_light_mps": 299792458.0,
    "sample_rate_hz": 40e6,
    "capture_duration_s": 40e-6,
    "baseline_pulse_duration_s": 10e-6,
    "baseline_bandwidth_hz": 8e6,
    "bandwidth_sweep_hz": (4e6, 8e6, 16e6),
    "duration_sweep_s": (5e-6, 10e-6, 20e-6),
    "first_target_range_m": 2400.0,
    "second_target_separation_m": 75.0,
    "first_echo_amplitude": 1.0,
    "second_echo_amplitude": 0.65,
    "noise_sigma": 2.0,
    "broken_replica_bandwidth_scale": 0.55,
    "comparison_tolerance": 1e-10,
    "max_record_samples": 1600,
    "max_pulse_samples": 800,
    "max_correlation_samples": 2400,
    "max_bandwidth_cases": 3,
    "max_duration_cases": 3,
    "max_figure_groups": 6,
    "max_stored_numeric_values": 500000,
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p32_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P32 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P32 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P32"]
    if len(matches) != 1:
        return errors + [f"expected one P32 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P32 {key} must be {expected!r}")
    return errors


def validate_controls(**overrides: object) -> dict[str, object]:
    unknown = set(overrides) - set(CANONICAL_CONTROLS)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls = dict(CANONICAL_CONTROLS)
    controls.update(overrides)

    positive = (
        "speed_of_light_mps",
        "sample_rate_hz",
        "capture_duration_s",
        "baseline_pulse_duration_s",
        "baseline_bandwidth_hz",
        "first_target_range_m",
        "second_target_separation_m",
        "first_echo_amplitude",
        "second_echo_amplitude",
        "noise_sigma",
        "comparison_tolerance",
    )
    for name in positive:
        if not finite_real(controls[name]) or controls[name] <= 0:
            raise ValueError(f"{name} must be finite and positive")
    if (
        not finite_real(controls["broken_replica_bandwidth_scale"])
        or not 0 < controls["broken_replica_bandwidth_scale"] < 1
    ):
        raise ValueError("broken replica scale must be finite and between zero and one")

    integer_names = (
        "random_seed",
        "max_record_samples",
        "max_pulse_samples",
        "max_correlation_samples",
        "max_bandwidth_cases",
        "max_duration_cases",
        "max_figure_groups",
        "max_stored_numeric_values",
    )
    for name in integer_names:
        value = controls[name]
        if not finite_real(value) or int(value) != value or value <= 0:
            raise ValueError(f"{name} must be a positive finite integer")
    if controls["random_seed"] != 3201:
        raise ValueError("random seed must remain canonical")

    vectors = (
        ("bandwidth_sweep_hz", "max_bandwidth_cases"),
        ("duration_sweep_s", "max_duration_cases"),
    )
    for name, maximum_name in vectors:
        values = controls[name]
        if (
            not isinstance(values, (tuple, list))
            or len(values) < 2
            or len(values) > controls[maximum_name]
            or any(not finite_real(item) or item <= 0 for item in values)
            or any(right <= left for left, right in zip(values, values[1:]))
        ):
            raise ValueError(f"{name} must be a bounded increasing positive vector")
    if max(controls["bandwidth_sweep_hz"]) >= controls["sample_rate_hz"] / 2:
        raise ValueError("bandwidth sweep exceeds Nyquist")
    if controls["baseline_bandwidth_hz"] >= controls["sample_rate_hz"] / 2:
        raise ValueError("baseline bandwidth exceeds Nyquist")

    record_count = round(controls["capture_duration_s"] * controls["sample_rate_hz"])
    pulse_counts = [
        round(duration * controls["sample_rate_hz"])
        for duration in (
            controls["baseline_pulse_duration_s"],
            *controls["duration_sweep_s"],
        )
    ]
    first_delay = round(
        2 * controls["first_target_range_m"] * controls["sample_rate_hz"]
        / controls["speed_of_light_mps"]
    )
    second_delay = round(
        2
        * (controls["first_target_range_m"] + controls["second_target_separation_m"])
        * controls["sample_rate_hz"]
        / controls["speed_of_light_mps"]
    )
    full_count = record_count + max(pulse_counts) - 1
    stored = 80 * record_count + 40 * full_count + 20 * sum(pulse_counts[1:])
    if record_count < 1 or record_count > controls["max_record_samples"]:
        raise ValueError("record resource ceiling exceeded")
    if min(pulse_counts) < 2 or max(pulse_counts) > controls["max_pulse_samples"]:
        raise ValueError("pulse resource ceiling exceeded")
    if full_count > controls["max_correlation_samples"]:
        raise ValueError("correlation resource ceiling exceeded")
    if controls["max_figure_groups"] < 6:
        raise ValueError("figure resource ceiling exceeded")
    if second_delay + max(pulse_counts) > record_count or first_delay < 0:
        raise ValueError("delayed echoes do not fit the capture")
    if stored > controls["max_stored_numeric_values"]:
        raise ValueError("stored-value resource ceiling exceeded")
    return controls


def parse_matlab_controls(source: str) -> dict[str, object]:
    parsed: dict[str, object] = {}
    vector_names = {"bandwidth_sweep_hz", "duration_sweep_s"}
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


def build_lfm(bandwidth_hz: float, duration_s: float, sample_rate_hz: float) -> list[complex]:
    if (
        not all(finite_real(value) and value > 0 for value in (bandwidth_hz, duration_s, sample_rate_hz))
        or bandwidth_hz >= sample_rate_hz / 2
    ):
        raise ValueError("LFM controls must be positive, finite, and below Nyquist")
    count = round(duration_s * sample_rate_hz)
    if count < 2:
        raise ValueError("LFM pulse needs at least two samples")
    rate = bandwidth_hz / duration_s
    return [
        cmath.exp(1j * math.pi * rate * (index / sample_rate_hz - (count - 1) / (2 * sample_rate_hz)) ** 2)
        for index in range(count)
    ]


def insert_echo(waveform: list[complex], record_count: int, delay_samples: int, amplitude: float = 1.0) -> list[complex]:
    if (
        not waveform
        or not isinstance(record_count, int)
        or not isinstance(delay_samples, int)
        or record_count <= 0
        or delay_samples < 0
        or delay_samples + len(waveform) > record_count
        or not finite_real(amplitude)
    ):
        raise ValueError("echo must be finite, integer-delayed, and fit the record")
    output = [0j] * record_count
    output[delay_samples : delay_samples + len(waveform)] = [
        amplitude * sample for sample in waveform
    ]
    return output


def matched_response(received: list[complex], replica: list[complex]) -> list[complex]:
    if not replica or len(replica) > len(received):
        raise ValueError("replica must be nonempty and fit the received record")
    return [
        sum(received[lag + index] * replica[index].conjugate() for index in range(len(replica)))
        for lag in range(len(received) - len(replica) + 1)
    ]


def half_power_width(magnitude: list[float], spacing: float) -> float:
    if len(magnitude) < 3 or not finite_real(spacing) or spacing <= 0:
        raise ValueError("width measurement needs a finite sampled response")
    peak = max(range(len(magnitude)), key=magnitude.__getitem__)
    threshold = magnitude[peak] / math.sqrt(2)
    left = peak
    while left > 0 and magnitude[left] >= threshold:
        left -= 1
    right = peak
    while right < len(magnitude) - 1 and magnitude[right] >= threshold:
        right += 1
    if left == peak or right == peak or magnitude[left] >= threshold or magnitude[right] >= threshold:
        raise ValueError("response has no bounded half-power crossings")
    left_crossing = left + (threshold - magnitude[left]) / (magnitude[left + 1] - magnitude[left])
    right_crossing = (right - 1) + (magnitude[right - 1] - threshold) / (magnitude[right - 1] - magnitude[right])
    return (right_crossing - left_crossing) * spacing


def clean_case(bandwidth_hz: float, duration_s: float, *, replica_bandwidth_hz: float | None = None) -> tuple[list[complex], float]:
    controls = validate_controls()
    waveform = build_lfm(bandwidth_hz, duration_s, controls["sample_rate_hz"])
    replica = build_lfm(
        bandwidth_hz if replica_bandwidth_hz is None else replica_bandwidth_hz,
        duration_s,
        controls["sample_rate_hz"],
    )
    delay = round(
        2 * controls["first_target_range_m"] * controls["sample_rate_hz"]
        / controls["speed_of_light_mps"]
    )
    echo = insert_echo(waveform, round(controls["capture_duration_s"] * controls["sample_rate_hz"]), delay)
    response = matched_response(echo, replica)
    width = half_power_width(
        [abs(value) for value in response],
        controls["speed_of_light_mps"] / (2 * controls["sample_rate_hz"]),
    )
    return response, width


class P32ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.text = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        cls.experiment = cls.text["experiment.m"]

    def test_complete_artifacts_exact_identity_and_prerequisite(self):
        self.assertEqual(validate_p32_contract(MODULE, self.manifest), [])
        for name, text in self.text.items():
            self.assertGreater(len(text), 100, name)
            self.assertIn(QUESTION, text)
        prerequisite = next(item for item in self.manifest["modules"] if item["id"] == "P31")
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertIn("P31", self.text["README.md"])
        self.assertIn("P31", self.text["lesson.md"])

    def test_contract_rejects_missing_empty_duplicate_and_malformed_inputs(self):
        self.assertIn("manifest modules must be a list", validate_p32_contract(MODULE, {}))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p32_contract(MODULE, {"modules": ["bad"]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P32 manifest entry, found 2", validate_p32_contract(MODULE, duplicate))
        wrong = copy.deepcopy(self.manifest)
        entry = next(item for item in wrong["modules"] if item["id"] == "P32")
        entry["guiding_question"] = "generic"
        entry["status"] = "scaffolded"
        errors = validate_p32_contract(MODULE, wrong)
        self.assertIn(f"P32 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P32 status must be 'implemented'", errors)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            for name in ARTIFACTS:
                (fixture / name).write_text("content\n", encoding="utf-8")
            (fixture / "experiment.m").unlink()
            (fixture / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p32_contract(fixture, self.manifest)
            self.assertIn("P32 missing experiment.m", errors)
            self.assertIn("P32 empty checks.md", errors)

    def test_controls_are_canonical_malformed_inputs_fail_and_resources_are_bounded(self):
        self.assertEqual(parse_matlab_controls(self.experiment), CANONICAL_CONTROLS)
        self.assertEqual(validate_controls(), CANONICAL_CONTROLS)
        malformed = (
            {"random_seed": True},
            {"random_seed": 3202},
            {"speed_of_light_mps": float("nan")},
            {"sample_rate_hz": 20e6},
            {"capture_duration_s": 20e-6},
            {"baseline_pulse_duration_s": 0.0},
            {"baseline_bandwidth_hz": 25e6},
            {"bandwidth_sweep_hz": (4e6, 4e6)},
            {"bandwidth_sweep_hz": (4e6, float("inf"))},
            {"duration_sweep_s": (20e-6, 5e-6)},
            {"duration_sweep_s": (1e-9, 10e-6)},
            {"first_target_range_m": "far"},
            {"second_target_separation_m": -1.0},
            {"noise_sigma": 0.0},
            {"broken_replica_bandwidth_scale": 1.0},
            {"comparison_tolerance": float("nan")},
            {"max_record_samples": 1599},
            {"max_pulse_samples": 799},
            {"max_correlation_samples": 2398},
            {"max_bandwidth_cases": 2},
            {"max_duration_cases": 2},
            {"max_figure_groups": 5},
            {"max_stored_numeric_values": 1000},
        )
        for override in malformed:
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_controls(**override)
        with self.assertRaises(ValueError):
            validate_controls(unapproved_control=1)

    def test_explicit_lfm_echo_correlation_range_and_no_black_box_regression(self):
        required = (
            "s(t)=exp(j*pi*k*(t-T/2)^2), k=B/T",
            "transmit_chirp = exp(1j*pi*baseline_chirp_rate_hz_per_s*",
            "matched_filter = fliplr(conj(transmit_chirp));",
            "first_echo(first_indices) = first_echo_amplitude*transmit_chirp;",
            "aligned_sum = aligned_sum+received_signal(received_index)*",
            "matched_filter(filter_index);",
            "convolution_crosscheck = conv(received_signal, matched_filter);",
            "(baseline_pulse_count-1)",
            "speed_of_light_mps*baseline_lags_samples/",
            "(2*sample_rate_hz)",
            "nominal_resolution_m = speed_of_light_mps/(2*baseline_bandwidth_hz);",
            "time_bandwidth_product = baseline_bandwidth_hz*baseline_pulse_duration_s;",
        )
        for marker in required:
            self.assertIn(marker, self.experiment)
        for pattern in (
            r"\bxcorr\s*\(",
            r"\bchirp\s*\(",
            r"\bfindpeaks\s*\(",
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
            r"(?m)^\s*(?:parfor|timer|pause)\b",
        ):
            self.assertNotRegex(self.experiment, pattern)

    def test_independent_oracle_is_zero_extended_compressed_and_range_aligned(self):
        controls = validate_controls()
        waveform = build_lfm(controls["baseline_bandwidth_hz"], controls["baseline_pulse_duration_s"], controls["sample_rate_hz"])
        self.assertEqual(len(waveform), 400)
        self.assertTrue(all(abs(abs(value) - 1) < 1e-12 for value in waveform))
        delay = round(2 * controls["first_target_range_m"] * controls["sample_rate_hz"] / controls["speed_of_light_mps"])
        echo = insert_echo(waveform, 1600, delay)
        self.assertTrue(all(value == 0 for value in echo[:delay]))
        self.assertTrue(all(value == 0 for value in echo[delay + len(waveform) :]))
        response = matched_response(echo, waveform)
        peak = max(range(len(response)), key=lambda index: abs(response[index]))
        width = half_power_width([abs(value) for value in response], controls["speed_of_light_mps"] / (2 * controls["sample_rate_hz"]))
        self.assertEqual(peak, delay)
        self.assertAlmostEqual(abs(response[peak]), len(waveform), places=9)
        self.assertLess(width, controls["speed_of_light_mps"] * controls["baseline_pulse_duration_s"] / 50)
        with self.assertRaises(ValueError):
            build_lfm(float("nan"), 10e-6, 40e6)
        with self.assertRaises(ValueError):
            build_lfm(8e6, 1e-9, 40e6)
        with self.assertRaises(ValueError):
            insert_echo(waveform, 200, 1)
        with self.assertRaises(ValueError):
            matched_response([0j], [])
        with self.assertRaises(ValueError):
            half_power_width([1.0, 1.0, 1.0], 1.0)

    def test_bandwidth_sweep_narrows_width_at_fixed_duration(self):
        controls = validate_controls()
        widths = [
            clean_case(bandwidth, controls["baseline_pulse_duration_s"])[1]
            for bandwidth in controls["bandwidth_sweep_hz"]
        ]
        nominal = [controls["speed_of_light_mps"] / (2 * bandwidth) for bandwidth in controls["bandwidth_sweep_hz"]]
        self.assertTrue(all(right < left for left, right in zip(widths, widths[1:])))
        self.assertTrue(all(right < left for left, right in zip(nominal, nominal[1:])))
        for actual, expected in zip(widths, (32.957955, 16.442479, 8.202776)):
            self.assertAlmostEqual(actual, expected, places=6)
        self.assertIn("%% Sweep 1: bandwidth only, fixed duration, scene, amplitudes, and noise", self.experiment)

    def test_duration_sweep_preserves_width_and_increases_time_bandwidth_gain(self):
        controls = validate_controls()
        widths = [
            clean_case(controls["baseline_bandwidth_hz"], duration)[1]
            for duration in controls["duration_sweep_s"]
        ]
        products = [controls["baseline_bandwidth_hz"] * duration for duration in controls["duration_sweep_s"]]
        gains = [10 * math.log10(product) for product in products]
        spacing = controls["speed_of_light_mps"] / (2 * controls["sample_rate_hz"])
        self.assertLess(max(widths) - min(widths), spacing)
        self.assertEqual(products, [40.0, 80.0, 160.0])
        self.assertTrue(all(right > left for left, right in zip(gains, gains[1:])))
        self.assertIn("%% Sweep 2: duration only, fixed bandwidth, scene, amplitude, and noise basis", self.experiment)
        self.assertIn("sampled_coherent_gain_db = 10*log10(baseline_pulse_count);", self.experiment)
        self.assertIn("predicted_processing_gain_db = 10*log10(time_bandwidth_product);", self.experiment)

    def test_broken_replica_degrades_and_exact_recovery_is_bound(self):
        controls = validate_controls()
        good_response, good_width = clean_case(controls["baseline_bandwidth_hz"], controls["baseline_pulse_duration_s"])
        bad_response, bad_width = clean_case(
            controls["baseline_bandwidth_hz"],
            controls["baseline_pulse_duration_s"],
            replica_bandwidth_hz=controls["broken_replica_bandwidth_scale"] * controls["baseline_bandwidth_hz"],
        )
        self.assertLess(max(map(abs, bad_response)), 0.5 * max(map(abs, good_response)))
        self.assertGreater(bad_width, 5 * good_width)
        for marker in (
            "%% Intentionally broken case: compress with a mismatched chirp-rate replica",
            "%% Recovery: restore the transmitted replica and recreate the private seed",
            "broken_model_valid = false;",
            "recovery_noise_exact_match = isequal(recovery_unit_noise, unit_noise);",
            "recovery_response_exact_match = isequal(recovery_response,",
            "recovered_model_valid = true;",
        ):
            self.assertIn(marker, self.experiment)

    def test_mismatch_plot_uses_shared_recovered_peak_reference(self):
        controls = validate_controls()
        good_response, _ = clean_case(
            controls["baseline_bandwidth_hz"],
            controls["baseline_pulse_duration_s"],
        )
        bad_response, _ = clean_case(
            controls["baseline_bandwidth_hz"],
            controls["baseline_pulse_duration_s"],
            replica_bandwidth_hz=(
                controls["broken_replica_bandwidth_scale"]
                * controls["baseline_bandwidth_hz"]
            ),
        )
        reference_peak = max(map(abs, good_response))
        recovered_db = [20 * math.log10(abs(value) / reference_peak) for value in good_response if value]
        broken_db = [20 * math.log10(abs(value) / reference_peak) for value in bad_response if value]
        self.assertAlmostEqual(max(recovered_db), 0.0, places=12)
        self.assertLess(max(broken_db), -6.0)
        for marker in (
            "mismatch_peak_loss_db = 20*log10(broken_peak/recovered_peak);",
            "mismatch_reference_peak = recovered_peak;",
            "abs(broken_response)/mismatch_reference_peak",
            "abs(baseline_clean_single_response)/...",
            "mismatch_reference_peak, 1e-8));",
            "Matched output relative to recovered peak (dB)",
            "fprintf('  Mismatch peak loss = %.2f dB\\n', mismatch_peak_loss_db);",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotIn(
            "abs(broken_response)/max(abs(broken_response))",
            self.experiment,
        )

    def test_plots_docs_and_checks_are_purposeful_and_placeholder_free(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 6)
        for label in (
            "Pulse time (microseconds)",
            "Instantaneous frequency (MHz)",
            "Apparent monostatic range c t / 2 (m)",
            "Normalized matched-output magnitude (dB)",
            "Chirp bandwidth B (MHz)",
            "Compressed range width (m)",
            "Pulse duration T (microseconds)",
            "B T processing gain (dB)",
        ):
            self.assertIn(label, self.experiment)
        for marker in (
            "Physical model: label time inside the pulse",
            "The matched filter performs coherent alignment",
            "Bandwidth sets width; duration carries energy",
            "Two gain conventions that must not be mixed",
            "The mismatch limit",
            "Assumptions and limiting cases",
            "Common interpretation mistakes",
            "Dependencies and concept connection",
        ):
            self.assertIn(marker, self.text["lesson.md"])
        for marker in (
            "Baseline observation",
            "Sweep one variable: bandwidth only",
            "Sweep one variable: duration only",
            "Intentionally broken case",
            "Recover and connect the concept",
        ):
            self.assertIn(marker.lower(), self.text["walkthrough.md"].lower())
        for marker in (
            "Observation checks",
            "Prediction checks",
            "Interpretation checks",
            "Failure and recovery checks",
            "Completion checklist",
            "Short teach-back rubric",
        ):
            self.assertIn(marker, self.text["checks.md"])
        combined = "\n".join(self.text.values())
        self.assertNotIn("TODO", combined)
        self.assertNotRegex(combined, r"(?i)implementation batch `P32` is pending")
        for term in ("bandwidth", "duration", "time-bandwidth", "matched filter", "processing gain", "mismatch"):
            self.assertIn(term, combined.lower())

    def test_cancellation_timeout_isolation_compatibility_catalogs_and_rollback(self):
        operational = self.text["walkthrough.md"] + self.text["checks.md"]
        for marker in (
            "Ctrl+C",
            "private seed",
            "global random stream",
            "figures tagged `P32`",
            ".learning/",
            "worker",
            "timer",
            "external transaction",
            "base MATLAB",
            "rollback",
            "scaffolded",
        ):
            self.assertIn(marker.lower(), operational.lower())
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P32'))", self.experiment)
        self.assertEqual(self.experiment.count("RandStream('mt19937ar', 'Seed', random_seed)"), 2)
        self.assertNotRegex(self.experiment, r"(?m)^\s*parfor\b")
        self.assertEqual(len(re.findall(r"(?m)^\s*while\b", self.experiment)), 2)
        self.assertIn("while left_index > 1", self.experiment)
        self.assertIn("while right_index < numel(magnitude)", self.experiment)
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 32 builds a complex-baseband LFM pulse", root_readme)
        self.assertIn("Project 32 follows P31", start_here)
        self.assertRegex(module_index, r"\| \[P32\].*\| implemented \|")

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
                [str(fixture_cli), "start", "32"],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("P32 — Perform LFM Pulse Compression", process.stdout)
            self.assertIn("status: implemented", process.stdout)
            self.assertIn("Tutor entry", process.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_retained_evidence_is_honest_and_complete(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P32-*.md"))
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
        for unit in ("MHz", "dB", "microseconds", "samples", "m", "500,000"):
            self.assertIn(unit, evidence)
        self.assertNotIn("PENDING —", evidence)


if __name__ == "__main__":
    unittest.main()
