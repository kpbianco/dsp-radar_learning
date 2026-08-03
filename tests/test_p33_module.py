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
MODULE = ROOT / "modules/33-control-pulse-compression-sidelobes"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Why can a strong target hide a weak nearby target after matched filtering?"
EXPECTED_IDENTITY = {
    "number": 33,
    "id": "P33",
    "title": "Control Pulse-Compression Sidelobes",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "control-pulse-compression-sidelobes",
    "folder": "modules/33-control-pulse-compression-sidelobes",
    "status": "implemented",
    "implementation_batch": "P33",
}
CANONICAL_CONTROLS = {
    "random_seed": 3301,
    "speed_of_light_mps": 299792458.0,
    "sample_rate_hz": 40e6,
    "capture_duration_s": 40e-6,
    "baseline_pulse_duration_s": 10e-6,
    "baseline_bandwidth_hz": 8e6,
    "strong_target_range_m": 2400.0,
    "weak_target_amplitude": 0.04,
    "weak_target_separation_samples": 17,
    "noise_sigma": 0.12,
    "taper_alpha_sweep": (0.0, 0.5, 1.0),
    "separation_sweep_samples": (7, 13, 17, 32),
    "broken_separation_samples": 7,
    "comparison_tolerance": 1e-10,
    "max_record_samples": 1600,
    "max_pulse_samples": 400,
    "max_correlation_samples": 1999,
    "max_taper_cases": 3,
    "max_separation_cases": 4,
    "max_figure_groups": 6,
    "max_stored_numeric_values": 500000,
}


def finite_real(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_p33_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P33 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P33 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P33"]
    if len(matches) != 1:
        return errors + [f"expected one P33 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P33 {key} must be {expected!r}")
    return errors


def validate_controls(**overrides: object) -> dict[str, object]:
    unknown = set(overrides) - set(CANONICAL_CONTROLS)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls = dict(CANONICAL_CONTROLS)
    controls.update(overrides)
    for name in ("speed_of_light_mps", "sample_rate_hz", "capture_duration_s", "baseline_pulse_duration_s", "baseline_bandwidth_hz", "strong_target_range_m", "weak_target_amplitude", "noise_sigma", "comparison_tolerance"):
        if not finite_real(controls[name]) or controls[name] <= 0:
            raise ValueError(f"{name} must be finite and positive")
    for name in ("random_seed", "weak_target_separation_samples", "broken_separation_samples", "max_record_samples", "max_pulse_samples", "max_correlation_samples", "max_taper_cases", "max_separation_cases", "max_figure_groups", "max_stored_numeric_values"):
        value = controls[name]
        if not finite_real(value) or int(value) != value or value <= 0:
            raise ValueError(f"{name} must be a positive finite integer")
    if controls["random_seed"] != 3301:
        raise ValueError("random seed must remain canonical")
    for name, ceiling in (("taper_alpha_sweep", "max_taper_cases"), ("separation_sweep_samples", "max_separation_cases")):
        values = controls[name]
        if not isinstance(values, (tuple, list)) or len(values) < 2 or len(values) > controls[ceiling] or any(not finite_real(item) for item in values) or any(right <= left for left, right in zip(values, values[1:])):
            raise ValueError(f"{name} must be a bounded increasing finite vector")
    if any(not 0 <= item <= 1 for item in controls["taper_alpha_sweep"]):
        raise ValueError("taper alpha must be in [0, 1]")
    if any(int(item) != item or item <= 0 for item in controls["separation_sweep_samples"]):
        raise ValueError("separation sweep must contain positive integer samples")
    if controls["weak_target_separation_samples"] not in controls["separation_sweep_samples"]:
        raise ValueError("baseline separation must be in the separation sweep")
    if controls["broken_separation_samples"] not in controls["separation_sweep_samples"]:
        raise ValueError("broken separation must be in the separation sweep")
    if controls["baseline_bandwidth_hz"] >= controls["sample_rate_hz"] / 2:
        raise ValueError("bandwidth exceeds Nyquist")
    record_count = round(controls["capture_duration_s"] * controls["sample_rate_hz"])
    pulse_count = round(controls["baseline_pulse_duration_s"] * controls["sample_rate_hz"])
    delay = round(2 * controls["strong_target_range_m"] * controls["sample_rate_hz"] / controls["speed_of_light_mps"])
    correlation_count = record_count + pulse_count - 1
    stored = 100 * record_count + 50 * correlation_count + 20 * pulse_count * (len(controls["taper_alpha_sweep"]) + len(controls["separation_sweep_samples"]))
    if record_count < 1 or record_count > controls["max_record_samples"]:
        raise ValueError("record resource ceiling exceeded")
    if pulse_count < 3 or pulse_count > controls["max_pulse_samples"]:
        raise ValueError("pulse resource ceiling exceeded")
    if correlation_count > controls["max_correlation_samples"]:
        raise ValueError("correlation resource ceiling exceeded")
    largest_separation = max(
        controls["weak_target_separation_samples"],
        controls["broken_separation_samples"],
        *controls["separation_sweep_samples"],
    )
    if delay + largest_separation + pulse_count > record_count:
        raise ValueError("echoes do not fit the capture")
    if controls["max_figure_groups"] < 6:
        raise ValueError("figure resource ceiling exceeded")
    if stored > controls["max_stored_numeric_values"]:
        raise ValueError("stored-value resource ceiling exceeded")
    return controls


def parse_matlab_controls(source: str) -> dict[str, object]:
    parsed: dict[str, object] = {}
    vectors = {"taper_alpha_sweep", "separation_sweep_samples"}
    for name, expected in CANONICAL_CONTROLS.items():
        if name in vectors:
            matches = re.findall(rf"(?m)^{name}\s*=\s*\[([^\]]+)\]\s*;", source)
            if len(matches) != 1:
                raise ValueError(f"expected one vector assignment for {name}")
            parsed[name] = tuple(float(item) for item in matches[0].split())
        else:
            matches = re.findall(rf"(?mi)^{name}\s*=\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?)\s*;", source)
            if len(matches) != 1:
                raise ValueError(f"expected one numeric assignment for {name}")
            value = float(matches[0])
            parsed[name] = int(value) if isinstance(expected, int) else value
    return parsed


def matlab_binding_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", "", source.replace("...", ""))
    required = {
        "explicit Hann weights": "hann_weights=0.5-0.5*cos(2*pi*sample_index/(baseline_pulse_count-1));",
        "Hann receive filter": "hann_filter=fliplr(conj(transmit_chirp.*hann_weights));",
        "taper family": "weights=(1-alpha)+alpha*hann_weights;",
        "sweep filter": "weighted_filter=fliplr(conj(transmit_chirp.*weights));",
        "sweep response": "weighted_strong_response=conv(strong_echo,weighted_filter);",
        "baseline Hann leakage": "hann_strong_leakage=abs(hann_strong_response(weak_output_index));",
        "broken scene delay": "broken_weak_delay_samples=strong_delay_samples+broken_separation_samples;",
        "broken Hann response": "broken_hann_response=conv(broken_received_signal,hann_filter);",
        "broken clean local-peak check": "broken_weak_local_peak=abs(broken_clean_hann_response(broken_weak_output_index))>abs(broken_clean_hann_response(broken_weak_output_index-1))&&abs(broken_clean_hann_response(broken_weak_output_index))>abs(broken_clean_hann_response(broken_weak_output_index+1));",
        "recovery scene": "recovery_received_signal=strong_echo+weak_echo+noise_sigma*recovery_unit_noise;",
        "recovery Hann response": "recovery_hann_response=conv(recovery_received_signal,hann_filter);",
    }
    return [label for label, marker in required.items() if marker not in compact]


def lfm(count: int, bandwidth_hz: float, duration_s: float, sample_rate_hz: float) -> list[complex]:
    if count < 2 or bandwidth_hz <= 0 or duration_s <= 0 or sample_rate_hz <= 0:
        raise ValueError("LFM controls must be positive and sampled")
    rate = bandwidth_hz / duration_s
    return [cmath.exp(1j * math.pi * rate * ((index - (count - 1) / 2) / sample_rate_hz) ** 2) for index in range(count)]


def taper(count: int, alpha: float) -> list[float]:
    if count < 2 or not finite_real(alpha) or not 0 <= alpha <= 1:
        raise ValueError("taper needs a sampled alpha in [0, 1]")
    hann = [0.5 - 0.5 * math.cos(2 * math.pi * index / (count - 1)) for index in range(count)]
    return [(1 - alpha) + alpha * item for item in hann]


def correlation(received: list[complex], replica: list[complex]) -> list[complex]:
    if not received or not replica or len(replica) > len(received):
        raise ValueError("replica must be nonempty and fit the received record")
    return [sum(received[start + index] * replica[index].conjugate() for index in range(len(replica))) for start in range(len(received) - len(replica) + 1)]


def full_convolution(signal: list[complex], filter_coefficients: list[complex]) -> list[complex]:
    if not signal or not filter_coefficients:
        raise ValueError("convolution inputs must be nonempty")
    output = [0j] * (len(signal) + len(filter_coefficients) - 1)
    for signal_index, sample in enumerate(signal):
        for filter_index, coefficient in enumerate(filter_coefficients):
            output[signal_index + filter_index] += sample * coefficient
    return output


def response_metrics(alpha: float, separation: int) -> tuple[float, float, float, float]:
    controls = validate_controls()
    count = round(controls["baseline_pulse_duration_s"] * controls["sample_rate_hz"])
    signal = lfm(count, controls["baseline_bandwidth_hz"], controls["baseline_pulse_duration_s"], controls["sample_rate_hz"])
    weights = taper(count, alpha)
    replica = [weight * sample for weight, sample in zip(weights, signal)]
    # Append zeros so the explicit valid correlation exposes every nonnegative
    # delay of the zero-extended pulse autocorrelation, rather than one point.
    auto = correlation(signal + [0j] * (count - 1), replica)
    peak = abs(auto[0])
    magnitude = [abs(value) for value in auto]
    # Locate the first null after the peak instead of applying a fixed exclusion:
    # tapering deliberately broadens the main lobe.
    first_null = next(
        index
        for index in range(1, len(magnitude) - 1)
        if magnitude[index] <= magnitude[index - 1] and magnitude[index] < magnitude[index + 1]
    )
    pslr = 20 * math.log10(max(magnitude[first_null + 1 :]) / peak)
    half = peak / math.sqrt(2)
    right = 1
    while right < len(auto) and magnitude[right] >= half:
        right += 1
    if right >= len(auto):
        raise ValueError("response has no bounded half-power crossing")
    right_crossing = (right - 1) + (magnitude[right - 1] - half) / (
        magnitude[right - 1] - magnitude[right]
    )
    range_spacing_m = controls["speed_of_light_mps"] / (
        2 * controls["sample_rate_hz"]
    )
    full_width_m = 2 * right_crossing * range_spacing_m
    # Output SNR is not proportional to raw peak amplitude.  For white input
    # noise, a weighted replica has (sum(w))^2 / (N sum(w^2)) of the
    # rectangular output SNR.  Raw Hann peak loss is about -6.04 dB, whereas
    # its output-SNR loss is only about -1.77 dB.
    snr_loss = 10 * math.log10(sum(weights) ** 2 / (count * sum(weight ** 2 for weight in weights)))
    weak_ratio = controls["weak_target_amplitude"] * peak / max(abs(auto[separation]), 1e-300)
    return pslr, full_width_m, snr_loss, 20 * math.log10(weak_ratio)


def coherent_scene_visibility(alpha: float, separation: int) -> tuple[float, bool]:
    """Return leakage margin and whether the weak bin is a distinct local peak."""
    controls = validate_controls()
    count = round(controls["baseline_pulse_duration_s"] * controls["sample_rate_hz"])
    signal = lfm(count, controls["baseline_bandwidth_hz"], controls["baseline_pulse_duration_s"], controls["sample_rate_hz"])
    weights = taper(count, alpha)
    replica_filter = [sample.conjugate() * weight for sample, weight in zip(reversed(signal), reversed(weights))]
    received = [0j] * (count + separation)
    received[:count] = signal
    received[separation : separation + count] = [
        received[separation + index] + controls["weak_target_amplitude"] * sample
        for index, sample in enumerate(signal)
    ]
    response = full_convolution(received, replica_filter)
    strong_index = count - 1
    weak_index = strong_index + separation
    isolated_strong = full_convolution(signal, replica_filter)
    weak_peak = controls["weak_target_amplitude"] * sum(weights)
    leakage_margin_db = 20 * math.log10(weak_peak / abs(isolated_strong[weak_index]))
    weak_is_local_peak = (
        abs(response[weak_index]) > abs(response[weak_index - 1])
        and abs(response[weak_index]) > abs(response[weak_index + 1])
    )
    return leakage_margin_db, weak_is_local_peak


class P33ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.text = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        cls.experiment = cls.text["experiment.m"]

    def test_complete_artifacts_exact_identity_and_p32_prerequisite(self):
        self.assertEqual(validate_p33_contract(MODULE, self.manifest), [])
        for name, text in self.text.items():
            self.assertGreater(len(text), 100, name)
            self.assertIn(QUESTION, text)
        p32 = next(item for item in self.manifest["modules"] if item["id"] == "P32")
        self.assertEqual(p32["status"], "implemented")
        self.assertIn("P32", self.text["README.md"])
        self.assertIn("P32", self.text["lesson.md"])

    def test_contract_rejects_missing_empty_duplicate_and_malformed_inputs(self):
        self.assertIn("manifest modules must be a list", validate_p33_contract(MODULE, {}))
        self.assertIn("manifest module entries must be objects", validate_p33_contract(MODULE, {"modules": ["bad"]}))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P33 manifest entry, found 2", validate_p33_contract(MODULE, duplicate))
        wrong = copy.deepcopy(self.manifest)
        entry = next(item for item in wrong["modules"] if item["id"] == "P33")
        entry["status"] = "scaffolded"
        self.assertIn("P33 status must be 'implemented'", validate_p33_contract(MODULE, wrong))
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            for name in ARTIFACTS:
                (fixture / name).write_text("content\n", encoding="utf-8")
            (fixture / "experiment.m").unlink()
            (fixture / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p33_contract(fixture, self.manifest)
            self.assertIn("P33 missing experiment.m", errors)
            self.assertIn("P33 empty checks.md", errors)

    def test_controls_are_canonical_malformed_inputs_fail_and_resources_are_bounded(self):
        self.assertEqual(parse_matlab_controls(self.experiment), CANONICAL_CONTROLS)
        self.assertEqual(validate_controls(), CANONICAL_CONTROLS)
        malformed = (
            {"random_seed": True},
            {"random_seed": 3302},
            {"speed_of_light_mps": float("nan")},
            {"sample_rate_hz": 16e6},
            {"capture_duration_s": float("inf")},
            {"baseline_pulse_duration_s": 0},
            {"baseline_bandwidth_hz": 20e6},
            {"weak_target_amplitude": 0},
            {"weak_target_separation_samples": 2000},
            {
                "weak_target_separation_samples": 2000,
                "separation_sweep_samples": (7, 13, 17, 2000),
            },
            {"noise_sigma": -1},
            {"taper_alpha_sweep": (0, 0.5, 1.1)},
            {"taper_alpha_sweep": (0, float("nan"))},
            {"separation_sweep_samples": (7, 7)},
            {"separation_sweep_samples": (7, 12.5)},
            {"broken_separation_samples": 8},
            {"broken_separation_samples": 2000},
            {
                "broken_separation_samples": 2000,
                "separation_sweep_samples": (7, 13, 17, 2000),
            },
            {"baseline_pulse_duration_s": 2 / 40e6},
            {"comparison_tolerance": 0},
            {"max_record_samples": 1599},
            {"max_pulse_samples": 399},
            {"max_correlation_samples": 1998},
            {"max_taper_cases": 2},
            {"max_separation_cases": 3},
            {"max_figure_groups": 5},
            {"max_stored_numeric_values": 1000},
        )
        for override in malformed:
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_controls(**override)
        with self.assertRaises(ValueError):
            validate_controls(unknown=1)

    def test_explicit_lfm_tapered_matched_filter_and_no_black_boxes(self):
        self.assertEqual(matlab_binding_errors(self.experiment), [])
        for marker in ("exp(1j*pi*chirp_rate_hz_per_s*", "rectangular_filter", "hann_filter", "fliplr(conj", "hann", "conv(", "strong_target", "weak_target", "comparison_tolerance", "recovery", "broken"):
            self.assertIn(marker, self.experiment)
        for pattern in (r"\bxcorr\s*\(", r"\bchirp\s*\(", r"\b(?:hann|hamming|blackman|taylorwin|chebwin)\s*\(", r"\bfindpeaks\s*\(", r"\bphased\.", r"\bawgn\s*\(", r"\bcircshift\s*\(", r"\brng\s*\(", r"\bclose\s+all\b", r"\b(save|load|fopen|system)\s*\(", r"\bweb(read|write|save)\s*\(", r"(?m)^\s*(?:parfor|timer|pause)\b"):
            self.assertNotRegex(self.experiment, pattern)
        # Keep the explicitly reported output-SNR metric distinct from the
        # raw weighted-filter peak, which uses a different 20*log10 ratio.
        self.assertRegex(
            self.experiment,
            r"hann_snr_loss_db\s*=\s*10\*log10\(sum\(hann_weights\)\^2/\s*\.\.\.\s*\(baseline_pulse_count\*sum\(hann_weights\.\^2\)\)\)",
        )

    def test_matlab_bindings_reject_taper_sweep_broken_and_recovery_mutations(self):
        mutations = (
            ("transmit_chirp.*hann_weights", "transmit_chirp.*rectangular_weights"),
            ("transmit_chirp.*weights", "transmit_chirp.*hann_weights"),
            ("hann_strong_response(weak_output_index)", "rectangular_strong_response(weak_output_index)"),
            ("broken_received_signal, hann_filter", "broken_received_signal, rectangular_filter"),
            ("recovery_received_signal, hann_filter", "recovery_received_signal, rectangular_filter"),
        )
        for old, new in mutations:
            with self.subTest(mutation=old):
                mutated = self.experiment.replace(old, new, 1)
                self.assertNotEqual(mutated, self.experiment)
                self.assertTrue(matlab_binding_errors(mutated))

    def test_independent_oracle_shows_taper_tradeoffs_and_weak_target_visibility(self):
        separation = CANONICAL_CONTROLS["weak_target_separation_samples"]
        rectangular = response_metrics(0.0, separation)
        hann = response_metrics(1.0, separation)
        self.assertLess(hann[0], rectangular[0] - 10.0, "Hann must lower PSLR")
        self.assertGreater(hann[1], rectangular[1], "Hann must widen the main lobe")
        self.assertLess(hann[2], rectangular[2] - 1.5, "Hann must incur output-SNR loss")
        self.assertGreater(hann[2], rectangular[2] - 2.0, "Hann output-SNR loss is not raw peak loss")
        self.assertGreater(hann[3], rectangular[3], "Hann must improve the weak-target leakage margin")
        rectangular_scene = coherent_scene_visibility(0.0, separation)
        hann_scene = coherent_scene_visibility(1.0, separation)
        self.assertAlmostEqual(rectangular_scene[0], -4.52, places=2)
        self.assertAlmostEqual(hann_scene[0], 13.14, places=2)
        self.assertFalse(rectangular_scene[1], "rectangular scene must not show a distinct weak peak")
        self.assertTrue(hann_scene[1], "Hann scene must show a distinct weak peak")
        self.assertEqual(round(CANONICAL_CONTROLS["baseline_pulse_duration_s"] * CANONICAL_CONTROLS["sample_rate_hz"]), 400)

    def test_sweeps_broken_case_and_exact_recovery_markers(self):
        controls = validate_controls()
        pslrs = [response_metrics(alpha, controls["weak_target_separation_samples"])[0] for alpha in controls["taper_alpha_sweep"]]
        widths = [response_metrics(alpha, controls["weak_target_separation_samples"])[1] for alpha in controls["taper_alpha_sweep"]]
        self.assertTrue(all(right < left for left, right in zip(pslrs, pslrs[1:])))
        self.assertTrue(all(right >= left for left, right in zip(widths, widths[1:])))
        near_margin = response_metrics(0.0, controls["broken_separation_samples"])[3]
        farther_margin = response_metrics(0.0, 32)[3]
        self.assertLess(near_margin, farther_margin)
        for marker in ("Sweep 1", "Sweep 2", "broken", "recovery", "broken_model_valid = false", "recovered_model_valid = true", "isequal"):
            self.assertIn(marker.lower(), self.experiment.lower())

    def test_lowest_pslr_rule_fails_behaviorally_and_recovery_restores_peak(self):
        controls = validate_controls()
        broken_separation = controls["broken_separation_samples"]
        recovered_separation = controls["weak_target_separation_samples"]
        rectangular_pslr = response_metrics(0.0, broken_separation)[0]
        hann_pslr = response_metrics(1.0, broken_separation)[0]
        broken_margin, broken_local_peak = coherent_scene_visibility(
            1.0, broken_separation
        )
        recovered_margin, recovered_local_peak = coherent_scene_visibility(
            1.0, recovered_separation
        )
        self.assertLess(hann_pslr, rectangular_pslr - 10.0)
        self.assertLess(broken_margin, 0.0)
        self.assertFalse(broken_local_peak)
        self.assertGreater(recovered_margin, 0.0)
        self.assertTrue(recovered_local_peak)

    def test_docs_checks_catalog_cli_timeout_and_isolation(self):
        combined = "\n".join(self.text.values())
        for marker in ("sidelobe", "SNR", "strong target", "weak target", "taper", "matched filter", "P32"):
            self.assertIn(marker.lower(), combined.lower())
        self.assertRegex(combined, r"(?i)main[ -]?lobe")
        for marker in ("Baseline observation", "Sweep", "broken", "recover", "Observation checks", "Prediction checks", "Interpretation checks", "teach-back"):
            self.assertIn(marker.lower(), (self.text["walkthrough.md"] + self.text["checks.md"]).lower())
        operational = self.text["walkthrough.md"] + self.text["checks.md"]
        for marker in (
            "Ctrl+C",
            "private seed",
            "global random stream",
            "figures tagged `P33`",
            ".learning/",
            "worker",
            "timer",
            "external transaction",
            "base MATLAB",
            "rollback",
            "scaffolded",
        ):
            self.assertIn(marker.lower(), operational.lower())
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P33'))", self.experiment)
        self.assertEqual(
            self.experiment.count("RandStream('mt19937ar', 'Seed', random_seed)"),
            2,
        )
        self.assertNotRegex(self.experiment, r"(?m)^\s*while\s+true\b")
        self.assertNotIn("TODO", combined)
        self.assertNotRegex(combined, r"(?i)implementation batch `P33` is pending")
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 33", root_readme)
        self.assertRegex(module_index, r"\| \[P33\].*\| implemented \|")
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
            result = subprocess.run([str(fixture / "bin/learn"), "start", "33"], cwd=fixture, text=True, capture_output=True, env=os.environ.copy(), timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P33 — Control Pulse-Compression Sidelobes", result.stdout)
            self.assertIn("status: implemented", result.stdout)
        self.assertEqual(state.read_bytes() if state.exists() else None, before)

    def test_retained_evidence_is_honest_and_complete(self):
        paths = sorted((ROOT / "docs/evidence").glob("P33-*.md"))
        self.assertEqual(len(paths), 1)
        evidence = paths[0].read_text(encoding="utf-8")
        for marker in ("Acceptance mapping", "Figure and metric inventory", "Exact commands and results", "Changed and preserved invariants", "Residual risks and unperformed validation", "Rollback and recovery", "Validation class", "MATLAB runtime status", "Toolboxes", "did not run"):
            self.assertIn(marker, evidence)
        for command in ("DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py", "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v", "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh"):
            self.assertIn(command, evidence)
        self.assertNotIn("PENDING —", evidence)


if __name__ == "__main__":
    unittest.main()
