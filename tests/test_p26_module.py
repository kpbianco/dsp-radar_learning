from __future__ import annotations

import copy
import json
import math
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/26-use-lms-to-cancel-an-interferer"
QUESTION = "How can an adaptive filter learn an unknown coupling path?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
EXPECTED_IDENTITY = {
    "number": 26,
    "id": "P26",
    "title": "Use LMS to Cancel an Interferer",
    "guiding_question": QUESTION,
    "phase": 3,
    "phase_title": "Modulation, Channels, and Statistical Estimation",
    "slug": "use-lms-to-cancel-an-interferer",
    "folder": "modules/26-use-lms-to-cancel-an-interferer",
    "status": "implemented",
    "implementation_batch": "P26",
}


def validate_p26_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P26 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P26 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    matches = [
        entry
        for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P26"
    ]
    if len(matches) != 1:
        return errors + [f"expected one P26 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P26 {key} must be {expected!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def canonical_controls() -> dict:
    return {
        "random_seed": 2601,
        "sample_count": 6000,
        "sampling_rate_hz": 8000,
        "filter_tap_count": 8,
        "path_change_sample": 3001,
        "path_before": (0.80, -0.50, 0.30, 0.20, -0.15, 0.10, 0.05, -0.03),
        "path_after": (0.35, 0.70, -0.45, 0.25, 0.15, -0.10, 0.08, 0.03),
        "baseline_step_size": 0.006,
        "step_size_sweep": (0.0005, 0.002, 0.006, 0.012),
        "reference_correlation_sweep": (1.0, 0.75, 0.50, 0.25, 0.0),
        "broken_step_size": 0.35,
        "desired_frequencies_hz": (700.0, 1100.0),
        "desired_amplitudes": (0.25, 0.18),
        "desired_phase_rad": (0.0, 0.40),
        "receiver_noise_std": 0.05,
        "moving_average_length": 128,
        "spectrum_fft_length": 2048,
        "spectrum_segment_length": 1024,
        "reacquisition_mismatch_threshold": 0.08,
        "reacquisition_hold_samples": 64,
        "broken_weight_norm_limit": 1e4,
        "broken_error_limit": 1e6,
        "max_sample_count": 6000,
        "max_filter_taps": 8,
        "max_step_sweep_cases": 4,
        "max_reference_sweep_cases": 5,
        "max_fft_length": 2048,
        "max_figure_groups": 5,
        "max_stored_numeric_values": 500000,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    vectors = {
        "path_before": canonical_controls()["path_before"],
        "path_after": canonical_controls()["path_after"],
        "step_size_sweep": canonical_controls()["step_size_sweep"],
        "reference_correlation_sweep": canonical_controls()[
            "reference_correlation_sweep"
        ],
        "desired_frequencies_hz": canonical_controls()["desired_frequencies_hz"],
        "desired_amplitudes": canonical_controls()["desired_amplitudes"],
        "desired_phase_rad": canonical_controls()["desired_phase_rad"],
    }
    for name, expected in vectors.items():
        value = controls[name]
        if not isinstance(value, (tuple, list)):
            raise ValueError(f"{name} must be a bounded numeric vector")
        if not all(_finite_real(item) for item in value):
            raise ValueError(f"{name} must contain finite real values")
        if tuple(value) != expected:
            raise ValueError(f"{name} must equal its canonical vector")

    for name, expected in canonical_controls().items():
        if name in vectors:
            continue
        value = controls[name]
        if not _finite_real(value) or value != expected:
            raise ValueError(f"{name} must equal its finite canonical scalar")

    if controls["sample_count"] > controls["max_sample_count"]:
        raise ValueError("sample count exceeds resource ceiling")
    if controls["filter_tap_count"] > controls["max_filter_taps"]:
        raise ValueError("tap count exceeds resource ceiling")
    if len(controls["path_before"]) != controls["filter_tap_count"]:
        raise ValueError("first path does not fit adaptive filter")
    if len(controls["path_after"]) != controls["filter_tap_count"]:
        raise ValueError("changed path does not fit adaptive filter")
    if not 1 < controls["path_change_sample"] <= controls["sample_count"]:
        raise ValueError("path change lies outside record")
    if len(controls["step_size_sweep"]) > controls["max_step_sweep_cases"]:
        raise ValueError("step sweep exceeds resource ceiling")
    if (
        len(controls["reference_correlation_sweep"])
        > controls["max_reference_sweep_cases"]
    ):
        raise ValueError("reference sweep exceeds resource ceiling")
    if controls["spectrum_fft_length"] > controls["max_fft_length"]:
        raise ValueError("FFT exceeds resource ceiling")
    if controls["spectrum_segment_length"] > controls["spectrum_fft_length"]:
        raise ValueError("spectrum segment exceeds FFT")
    if max(controls["desired_frequencies_hz"]) >= controls["sampling_rate_hz"] / 2:
        raise ValueError("desired tone violates Nyquist")
    estimated_values = controls["sample_count"] * (24 + 20 + 20) + 10 * controls[
        "spectrum_fft_length"
    ]
    if estimated_values > controls["max_stored_numeric_values"]:
        raise ValueError("conservative numeric storage bound exceeded")


def normalize(values: list[float]) -> list[float]:
    rms = math.sqrt(sum(value * value for value in values) / len(values))
    return [value / rms for value in values]


def convolve(left: list[float], right: list[float]) -> list[float]:
    output = [0.0] * (len(left) + len(right) - 1)
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            output[left_index + right_index] += left_value * right_value
    return output


def deterministic_problem() -> dict:
    controls = canonical_controls()
    generator = random.Random(controls["random_seed"])
    count = controls["sample_count"]
    reference = normalize([generator.gauss(0.0, 1.0) for _ in range(count)])
    independent = normalize([generator.gauss(0.0, 1.0) for _ in range(count)])
    receiver_noise = normalize([generator.gauss(0.0, 1.0) for _ in range(count)])
    desired_clean = [
        controls["desired_amplitudes"][0]
        * math.sin(
            2
            * math.pi
            * controls["desired_frequencies_hz"][0]
            * sample
            / controls["sampling_rate_hz"]
            + controls["desired_phase_rad"][0]
        )
        + controls["desired_amplitudes"][1]
        * math.sin(
            2
            * math.pi
            * controls["desired_frequencies_hz"][1]
            * sample
            / controls["sampling_rate_hz"]
            + controls["desired_phase_rad"][1]
        )
        for sample in range(count)
    ]
    desired = [
        clean + controls["receiver_noise_std"] * receiver_noise[sample]
        for sample, clean in enumerate(desired_clean)
    ]
    before = convolve(reference, list(controls["path_before"]))[:count]
    after = convolve(reference, list(controls["path_after"]))[:count]
    change = controls["path_change_sample"] - 1
    interference = before[:change] + after[change:]
    primary = [signal + unwanted for signal, unwanted in zip(desired, interference)]
    return {
        "reference": reference,
        "independent": independent,
        "desired_clean": desired_clean,
        "desired": desired,
        "interference": interference,
        "primary": primary,
    }


def run_lms(
    primary: list[float],
    reference: list[float],
    interference: list[float],
    step_size: float,
    *,
    guard: bool = False,
) -> dict:
    controls = canonical_controls()
    tap_count = controls["filter_tap_count"]
    change = controls["path_change_sample"] - 1
    before = controls["path_before"]
    after = controls["path_after"]
    weights = [0.0] * tap_count
    errors: list[float] = []
    residuals: list[float] = []
    mismatch: list[float] = []
    history: list[tuple[float, ...]] = []
    stop_sample: int | None = None
    for sample, primary_value in enumerate(primary):
        vector = [reference[sample - tap] if sample >= tap else 0.0 for tap in range(tap_count)]
        estimate = sum(weight * value for weight, value in zip(weights, vector))
        error = primary_value - estimate
        candidate = [
            weight + step_size * error * value
            for weight, value in zip(weights, vector)
        ]
        if guard and (
            not math.isfinite(error)
            or any(not math.isfinite(value) for value in candidate)
            or math.sqrt(sum(value * value for value in candidate))
            > controls["broken_weight_norm_limit"]
            or abs(error) > controls["broken_error_limit"]
        ):
            stop_sample = sample + 1
            break
        weights = candidate
        active = before if sample < change else after
        errors.append(error)
        residuals.append(interference[sample] - estimate)
        mismatch.append(
            math.sqrt(
                sum((weight - target) ** 2 for weight, target in zip(weights, active))
                / tap_count
            )
        )
        history.append(tuple(weights))
    return {
        "weights": tuple(weights),
        "errors": errors,
        "residuals": residuals,
        "mismatch": mismatch,
        "history": history,
        "stop_sample": stop_sample,
    }


def mean_square(values: list[float]) -> float:
    return sum(value * value for value in values) / len(values)


def reacquisition_samples(mismatch: list[float]) -> int | None:
    controls = canonical_controls()
    start = controls["path_change_sample"] - 1
    hold = controls["reacquisition_hold_samples"]
    below = [
        value < controls["reacquisition_mismatch_threshold"]
        for value in mismatch[start:]
    ]
    for offset in range(len(below) - hold + 1):
        if all(below[offset : offset + hold]):
            return offset + hold
    return None


class P26ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text())
        cls.text = {
            name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        }
        cls.experiment = cls.text["experiment.m"]
        cls.problem = deterministic_problem()

    def test_complete_artifacts_and_exact_manifest_identity(self):
        self.assertEqual(validate_p26_contract(MODULE, self.manifest), [])
        for text in self.text.values():
            self.assertIn(QUESTION, text)
        p25 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P25")
        self.assertEqual(p25["status"], "implemented")

    def test_contract_validator_rejects_nonlist_duplicate_and_wrong_identity(self):
        self.assertIn("manifest modules must be a list", validate_p26_contract(MODULE, {}))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertTrue(
            any("found 2" in error for error in validate_p26_contract(MODULE, duplicate))
        )
        for key, expected in EXPECTED_IDENTITY.items():
            with self.subTest(key=key):
                wrong = copy.deepcopy(self.manifest)
                entry = next(item for item in wrong["modules"] if item["id"] == "P26")
                entry[key] = "wrong" if not isinstance(expected, int) else expected + 1
                self.assertTrue(validate_p26_contract(MODULE, wrong))

    def test_contract_validator_rejects_missing_and_empty_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            module_dir = Path(temporary)
            for name in ARTIFACTS:
                (module_dir / name).write_text("content", encoding="utf-8")
            (module_dir / "lesson.md").unlink()
            (module_dir / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p26_contract(module_dir, self.manifest)
            self.assertIn("P26 missing lesson.md", errors)
            self.assertIn("P26 empty checks.md", errors)

    def test_controls_are_finite_canonical_and_resource_bounded(self):
        validate_controls()
        malformed = (
            {"random_seed": True},
            {"sample_count": float("nan")},
            {"sampling_rate_hz": 8000 + 1j},
            {"filter_tap_count": 9},
            {"path_change_sample": 3000},
            {"path_before": "eight taps"},
            {"path_before": [0.8] * 8},
            {"path_after": [0.35, float("inf")] + [0.0] * 6},
            {"step_size_sweep": [0.0005, 0.002, 0.006]},
            {"reference_correlation_sweep": [1, 0.75, 0.5, 0.25, -0.1]},
            {"broken_step_size": 0.3},
            {"desired_frequencies_hz": [700, 4000]},
            {"spectrum_segment_length": 2048},
            {"max_sample_count": 5999},
            {"max_stored_numeric_values": float("inf")},
        )
        for override in malformed:
            with self.subTest(override=override):
                with self.assertRaises(ValueError):
                    validate_controls(**override)
        with self.assertRaises(ValueError):
            validate_controls(not_a_control=1)

    def test_private_seed_and_deterministic_signal_contract(self):
        self.assertIn("RandStream('mt19937ar', 'Seed', random_seed)", self.experiment)
        self.assertNotIn("rng(", self.experiment)
        for marker in (
            "reference_signal = reference_signal/sqrt(mean(reference_signal.^2));",
            "desired_clean_signal =",
            "coupled_before_full = conv(reference_signal, path_before);",
            "coupled_after_full = conv(reference_signal, path_after);",
            "primary_signal = desired_signal + true_interference;",
        ):
            self.assertIn(marker, self.experiment)

    def test_independent_lms_oracle_converges_and_reacquires(self):
        result = run_lms(
            self.problem["primary"],
            self.problem["reference"],
            self.problem["interference"],
            canonical_controls()["baseline_step_size"],
        )
        change = canonical_controls()["path_change_sample"] - 1
        segment = canonical_controls()["spectrum_segment_length"]
        pre = slice(change - segment, change)
        post = slice(-segment, None)
        pre_suppression = 10 * math.log10(
            mean_square(self.problem["interference"][pre])
            / mean_square(result["residuals"][pre])
        )
        post_suppression = 10 * math.log10(
            mean_square(self.problem["interference"][post])
            / mean_square(result["residuals"][post])
        )
        self.assertGreater(pre_suppression, 20)
        self.assertGreater(post_suppression, 20)
        self.assertLess(result["mismatch"][change - 1], 0.04)
        self.assertGreater(result["mismatch"][change], 0.35)
        self.assertLess(result["mismatch"][-1], 0.04)
        reacquisition = reacquisition_samples(result["mismatch"])
        self.assertIsNotNone(reacquisition)
        self.assertLess(reacquisition, 600)
        for marker in (
            "estimated_interference = baseline_weights.'*reference_vector;",
            "error_sample = primary_signal(sample_index) - estimated_interference;",
            "baseline_weights = baseline_weights +",
            "baseline_step_size*error_sample*reference_vector;",
            "baseline_path_mismatch(sample_index)",
        ):
            self.assertIn(marker, self.experiment)

    def test_canceller_preserves_desired_signal_in_settled_epochs(self):
        result = run_lms(
            self.problem["primary"],
            self.problem["reference"],
            self.problem["interference"],
            canonical_controls()["baseline_step_size"],
        )
        change = canonical_controls()["path_change_sample"] - 1
        segment = canonical_controls()["spectrum_segment_length"]
        for epoch in (slice(change - segment, change), slice(-segment, None)):
            observed = result["errors"][epoch]
            desired = self.problem["desired_clean"][epoch]
            primary = self.problem["primary"][epoch]
            coherent_gain = sum(
                output * target for output, target in zip(observed, desired)
            ) / sum(target * target for target in desired)
            normalized_correlation = sum(
                output * target for output, target in zip(observed, desired)
            ) / math.sqrt(
                sum(output * output for output in observed)
                * sum(target * target for target in desired)
            )
            primary_correlation = sum(
                input_sample * target for input_sample, target in zip(primary, desired)
            ) / math.sqrt(
                sum(input_sample * input_sample for input_sample in primary)
                * sum(target * target for target in desired)
            )
            self.assertAlmostEqual(coherent_gain, 1.0, delta=0.03)
            self.assertGreater(normalized_correlation, 0.95)
            self.assertGreater(normalized_correlation, primary_correlation + 0.5)
        for marker in (
            "baseline_pre_desired_gain =",
            "baseline_post_desired_gain =",
            "Settled canceller output must preserve the clean desired waveform gain.",
            "results.baseline.pre_desired_gain",
            "results.baseline.post_desired_gain",
        ):
            self.assertIn(marker, self.experiment)

    def test_step_size_sweep_exposes_speed_and_misadjustment(self):
        reacquisition: list[int | None] = []
        late_power: list[float] = []
        segment = canonical_controls()["spectrum_segment_length"]
        for step_size in canonical_controls()["step_size_sweep"]:
            result = run_lms(
                self.problem["primary"],
                self.problem["reference"],
                self.problem["interference"],
                step_size,
            )
            reacquisition.append(reacquisition_samples(result["mismatch"]))
            late_power.append(mean_square(result["errors"][-segment:]))
        self.assertIsNone(reacquisition[0])
        self.assertGreater(reacquisition[1], reacquisition[2])
        self.assertGreater(reacquisition[2], reacquisition[3])
        self.assertGreater(late_power[3], late_power[1])
        for marker in (
            "step_size_sweep = [0.0005 0.002 0.006 0.012];",
            "sweep_step_size = step_size_sweep(sweep_index);",
            "results.step_sweep.reacquisition_samples",
        ):
            self.assertIn(marker, self.experiment)

    def test_reference_correlation_sweep_is_one_variable_and_predictive(self):
        suppression: list[float] = []
        controls = canonical_controls()
        segment = controls["spectrum_segment_length"]
        interference_power = mean_square(self.problem["interference"][-segment:])
        for rho in controls["reference_correlation_sweep"]:
            candidate = normalize(
                [
                    rho * source + math.sqrt(1 - rho * rho) * independent
                    for source, independent in zip(
                        self.problem["reference"], self.problem["independent"]
                    )
                ]
            )
            result = run_lms(
                self.problem["primary"],
                candidate,
                self.problem["interference"],
                controls["baseline_step_size"],
            )
            suppression.append(
                10
                * math.log10(
                    interference_power / mean_square(result["residuals"][-segment:])
                )
            )
        self.assertGreater(suppression[0], 20)
        self.assertGreater(suppression[0], suppression[-1] + 15)
        self.assertLess(suppression[-1], 3)
        for left, right in zip(suppression, suppression[1:]):
            self.assertGreater(left, right)
        walkthrough = self.text["walkthrough.md"].lower()
        self.assertIn("change only how much", walkthrough)
        self.assertIn("primary signal", walkthrough)
        self.assertIn("results.reference_sweep.suppression_db", self.experiment)

    def test_broken_guard_and_clean_recovery_oracle(self):
        controls = canonical_controls()
        broken = run_lms(
            self.problem["primary"],
            self.problem["reference"],
            self.problem["interference"],
            controls["broken_step_size"],
            guard=True,
        )
        baseline = run_lms(
            self.problem["primary"],
            self.problem["reference"],
            self.problem["interference"],
            controls["baseline_step_size"],
        )
        recovery = run_lms(
            self.problem["primary"],
            self.problem["reference"],
            self.problem["interference"],
            controls["baseline_step_size"],
        )
        self.assertIsNotNone(broken["stop_sample"])
        self.assertLess(broken["stop_sample"], 500)
        self.assertEqual(recovery["errors"], baseline["errors"])
        self.assertEqual(recovery["weights"], baseline["weights"])
        for marker in (
            "%% Intentionally broken case",
            "norm(candidate_weights) > broken_weight_norm_limit",
            "broken_guard_triggered = true;",
            "recovery_weights = zeros(filter_tap_count, 1);",
            "recovery_error-baseline_error",
        ):
            self.assertIn(marker, self.experiment)

    def test_conservative_step_bound_and_limiting_cases_are_explained(self):
        combined = "\n".join(self.text.values()).lower()
        for phrase in (
            "2}{\\lambda_{\\max}",
            "mean coefficient error",
            "not a mean-square stability guarantee",
            "2}{(l+2)p_x}",
            "conservative",
            "misadjustment",
            "limiting cases",
            "uncorrelated reference",
            "too few taps",
            "desired signal correlated",
            "cannot predict",
        ):
            self.assertIn(phrase, combined)
        self.assertIn(
            "conservative_step_limit = 0.1/(filter_tap_count*reference_power);",
            self.experiment,
        )
        self.assertIn(
            "white_gaussian_mean_square_step_limit =",
            self.experiment,
        )

    def test_figures_metrics_units_and_results_inventory(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 5)
        self.assertIn("findall(0, 'Type', 'figure', 'Tag', 'P26')", self.experiment)
        for marker in (
            "Time (ms)",
            "Sample index n",
            "RMS coefficient mismatch",
            "128-sample mean-square power (dB re 1)",
            "Frequency (Hz)",
            "Windowed bin power (dB re 1)",
            "Residual interference suppression (dB)",
            "results.baseline.weight_history",
            "results.broken.stop_sample",
            "fprintf('Residual interference suppression:",
        ):
            self.assertIn(marker, self.experiment)

    def test_placeholder_black_box_external_io_and_unbounded_work_regression(self):
        combined = "\n".join(self.text.values())
        for placeholder in ("TODO", "FIXME", "TBD", "lorem ipsum"):
            self.assertNotIn(placeholder.lower(), combined.lower())
        banned = (
            "dsp.lmsfilter",
            "adaptfilt",
            "lms(",
            "awgn(",
            "comm.",
            "fopen(",
            "save(",
            "writetable(",
            "system(",
            "webread(",
            "parfor",
            "timer(",
            "while ",
            "close all",
        )
        for operation in banned:
            self.assertNotIn(operation, self.experiment.lower())

    def test_validation_precedes_rng_allocation_convolution_fft_cleanup_and_figures(self):
        validation_end = self.experiment.index("results = struct();")
        for operation in (
            "RandStream(",
            "zeros(",
            "conv(",
            "fft(",
            "findall(",
            "figure(",
        ):
            with self.subTest(operation=operation):
                self.assertGreater(self.experiment.index(operation), validation_end)
        for marker in (
            "max_sample_count = 6000;",
            "max_filter_taps = 8;",
            "max_step_sweep_cases = 4;",
            "max_reference_sweep_cases = 5;",
            "max_fft_length = 2048;",
            "max_figure_groups = 5;",
            "max_stored_numeric_values = 500000;",
        ):
            self.assertIn(marker, self.experiment)

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback(self):
        operational = "\n".join((self.text["walkthrough.md"], self.text["checks.md"]))
        for phrase in (
            "Ctrl+C",
            "full rerun",
            "private seed",
            "global random stream",
            "workspace variables",
            "cannot restore",
            ".learning/",
            "worker",
            "timer",
            "external transaction",
            "rollback",
            "P25",
            "base MATLAB",
        ):
            self.assertIn(phrase.lower(), operational.lower())

    def test_public_catalogs_record_permanent_p26_facts(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 26 uses", root_readme)
        self.assertIn("Project 26 follows P25", start_here)
        self.assertRegex(module_index, r"\| \[P26\].*\| implemented \|")

    def test_learner_cli_starts_p26_in_isolated_state_with_timeout(self):
        repository_state = ROOT / ".learning/progress.json"
        state_before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            isolated_root = Path(temporary)
            (isolated_root / "bin").mkdir()
            (isolated_root / "curriculum").mkdir()
            shutil.copy2(ROOT / "bin/learn", isolated_root / "bin/learn")
            shutil.copy2(
                ROOT / "curriculum/modules.json",
                isolated_root / "curriculum/modules.json",
            )
            process = subprocess.run(
                [sys.executable, str(isolated_root / "bin/learn"), "start", "26"],
                cwd=isolated_root,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("P26 — Use LMS to Cancel an Interferer", process.stdout)
            self.assertIn(QUESTION, process.stdout)
            state = json.loads(
                (isolated_root / ".learning/progress.json").read_text(encoding="utf-8")
            )
            self.assertEqual(state["current"], "P26")
        state_after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(state_after, state_before)

    def test_retained_evidence_has_honest_runtime_boundary(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P26-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        self.assertIn("MATLAB", evidence)
        self.assertIn("did not run", evidence.lower())
        self.assertIn("unperformed", evidence.lower())


if __name__ == "__main__":
    unittest.main()
