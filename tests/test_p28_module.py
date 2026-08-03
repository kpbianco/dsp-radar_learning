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
MODULE = ROOT / "modules/28-connect-thresholds-to-roc-curves-and-estimator-limits"
QUESTION = "How do false alarms, detections, bias, variance, and theoretical bounds relate?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
EXPECTED_IDENTITY = {
    "number": 28,
    "id": "P28",
    "title": "Connect Thresholds to ROC Curves and Estimator Limits",
    "guiding_question": QUESTION,
    "phase": 3,
    "phase_title": "Modulation, Channels, and Statistical Estimation",
    "slug": "connect-thresholds-to-roc-curves-and-estimator-limits",
    "folder": "modules/28-connect-thresholds-to-roc-curves-and-estimator-limits",
    "status": "implemented",
    "implementation_batch": "P28",
}


def validate_p28_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P28 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P28 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    matches = [
        entry
        for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P28"
    ]
    if len(matches) != 1:
        return errors + [f"expected one P28 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P28 {key} must be {expected!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def canonical_controls() -> dict:
    return {
        "random_seed": 2801,
        "trial_count": 12000,
        "sample_count": 16,
        "signal_amplitude": 1.0,
        "baseline_matched_snr_db": 6.0,
        "operating_threshold_sigma": 1.5,
        "threshold_sigma_sweep": (-1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0),
        "estimator_snr_db_sweep": (-6.0, -3.0, 0.0, 3.0, 6.0, 9.0, 12.0),
        "max_trial_count": 12000,
        "max_sample_count": 16,
        "max_threshold_cases": 9,
        "max_estimator_snr_cases": 7,
        "max_figure_groups": 5,
        "max_stored_numeric_values": 2500000,
        "workspace_vector_equivalents": 80,
        "workspace_matrix_equivalents": 7,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    vectors = {
        "threshold_sigma_sweep": canonical_controls()["threshold_sigma_sweep"],
        "estimator_snr_db_sweep": canonical_controls()["estimator_snr_db_sweep"],
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

    if controls["trial_count"] > controls["max_trial_count"]:
        raise ValueError("trial count exceeds resource ceiling")
    if controls["sample_count"] > controls["max_sample_count"]:
        raise ValueError("sample count exceeds resource ceiling")
    if len(controls["threshold_sigma_sweep"]) > controls["max_threshold_cases"]:
        raise ValueError("threshold sweep exceeds resource ceiling")
    if len(controls["estimator_snr_db_sweep"]) > controls["max_estimator_snr_cases"]:
        raise ValueError("SNR sweep exceeds resource ceiling")
    if controls["operating_threshold_sigma"] not in controls["threshold_sigma_sweep"]:
        raise ValueError("operating threshold must be in the sweep")
    estimated = (
        controls["trial_count"] * controls["workspace_vector_equivalents"]
        + controls["trial_count"]
        * controls["sample_count"]
        * controls["workspace_matrix_equivalents"]
        + 100
        * (
            len(controls["threshold_sigma_sweep"])
            + len(controls["estimator_snr_db_sweep"])
            + 49
        )
    )
    if estimated > controls["max_stored_numeric_values"]:
        raise ValueError("conservative numeric storage bound exceeded")


def sample_variance(values: list[float]) -> float:
    center = sum(values) / len(values)
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def deterministic_model() -> dict:
    controls = canonical_controls()
    generator = random.Random(controls["random_seed"])
    count = controls["trial_count"]
    template = (1, 1, 1, -1, 1, -1, -1, 1, -1, 1, -1, -1, -1, 1, 1, -1)
    energy = sum(value * value for value in template)
    snr_linear = 10 ** (controls["baseline_matched_snr_db"] / 10)
    noise_std = controls["signal_amplitude"] * math.sqrt(energy / snr_linear)
    d_prime = controls["signal_amplitude"] * math.sqrt(energy) / noise_std

    h0_unit_projection = [
        sum(value * generator.gauss(0.0, 1.0) for value in template)
        for _ in range(count)
    ]
    h1_unit_projection = [
        sum(value * generator.gauss(0.0, 1.0) for value in template)
        for _ in range(count)
    ]
    score_h0 = [projection / math.sqrt(energy) for projection in h0_unit_projection]
    score_h1 = [d_prime + projection / math.sqrt(energy) for projection in h1_unit_projection]
    amplitude_estimates = [
        controls["signal_amplitude"] + noise_std * projection / energy
        for projection in h1_unit_projection
    ]
    return {
        "energy": energy,
        "noise_std": noise_std,
        "d_prime": d_prime,
        "h0_unit_projection": h0_unit_projection,
        "h1_unit_projection": h1_unit_projection,
        "score_h0": score_h0,
        "score_h1": score_h1,
        "amplitude_estimates": amplitude_estimates,
    }


def display_histogram_counts(values: list[float], edges: tuple[float, ...]) -> list[int]:
    if len(edges) < 2 or any(left >= right for left, right in zip(edges, edges[1:])):
        raise ValueError("histogram edges must be strictly increasing")
    counts = [0] * (len(edges) - 1)
    for value in values:
        if not math.isfinite(value):
            raise ValueError("histogram values must be finite")
        if value < edges[1]:
            counts[0] += 1
        elif value >= edges[-2]:
            counts[-1] += 1
        else:
            for index in range(1, len(edges) - 2):
                if edges[index] <= value < edges[index + 1]:
                    counts[index] += 1
                    break
    return counts


class P28ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text())
        cls.text = {
            name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        }
        cls.experiment = cls.text["experiment.m"]
        cls.model = deterministic_model()

    def test_complete_artifacts_exact_identity_and_prerequisite(self):
        self.assertEqual(validate_p28_contract(MODULE, self.manifest), [])
        for text in self.text.values():
            self.assertIn(QUESTION, text)
        prerequisite = next(
            entry for entry in self.manifest["modules"] if entry["id"] == "P27"
        )
        self.assertEqual(prerequisite["status"], "implemented")

    def test_contract_validator_rejects_nonlist_duplicate_and_wrong_identity(self):
        self.assertIn("manifest modules must be a list", validate_p28_contract(MODULE, {}))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertTrue(any("found 2" in item for item in validate_p28_contract(MODULE, duplicate)))
        for key, expected in EXPECTED_IDENTITY.items():
            with self.subTest(key=key):
                wrong = copy.deepcopy(self.manifest)
                entry = next(item for item in wrong["modules"] if item["id"] == "P28")
                entry[key] = "wrong" if not isinstance(expected, int) else expected + 1
                self.assertTrue(validate_p28_contract(MODULE, wrong))

    def test_contract_validator_rejects_missing_and_empty_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            module_dir = Path(temporary)
            for name in ARTIFACTS:
                (module_dir / name).write_text("content", encoding="utf-8")
            (module_dir / "experiment.m").unlink()
            (module_dir / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p28_contract(module_dir, self.manifest)
            self.assertIn("P28 missing experiment.m", errors)
            self.assertIn("P28 empty lesson.md", errors)

    def test_controls_are_canonical_finite_and_resource_bounded(self):
        validate_controls()
        malformed = (
            {"random_seed": True},
            {"trial_count": float("nan")},
            {"sample_count": 16 + 1j},
            {"signal_amplitude": float("inf")},
            {"baseline_matched_snr_db": 5.0},
            {"operating_threshold_sigma": "high"},
            {"threshold_sigma_sweep": (-1, -0.5, 0, 0.5, 1, 1.5, 2, 2.5)},
            {"threshold_sigma_sweep": (-1, -0.5, 0, 0.5, 1, float("nan"), 2, 2.5, 3)},
            {"estimator_snr_db_sweep": [-6, -3, 0, 3, 6, 9, 13]},
            {"max_trial_count": 11999},
            {"max_sample_count": 15},
            {"max_threshold_cases": 8},
            {"max_estimator_snr_cases": 6},
            {"max_figure_groups": 4},
            {"max_stored_numeric_values": 2300000},
        )
        for override in malformed:
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_controls(**override)
        with self.assertRaises(ValueError):
            validate_controls(unapproved_control=1)

    def test_independent_hypotheses_and_roc_match_gaussian_model(self):
        controls = canonical_controls()
        model = self.model
        empirical_pfa = []
        empirical_pd = []
        analytic_pfa = []
        analytic_pd = []
        for threshold in controls["threshold_sigma_sweep"]:
            empirical_pfa.append(sum(value >= threshold for value in model["score_h0"]) / controls["trial_count"])
            empirical_pd.append(sum(value >= threshold for value in model["score_h1"]) / controls["trial_count"])
            analytic_pfa.append(0.5 * math.erfc(threshold / math.sqrt(2)))
            analytic_pd.append(0.5 * math.erfc((threshold - model["d_prime"]) / math.sqrt(2)))
        self.assertTrue(all(left >= right for left, right in zip(empirical_pfa, empirical_pfa[1:])))
        self.assertTrue(all(left >= right for left, right in zip(empirical_pd, empirical_pd[1:])))
        self.assertLess(max(abs(a - b) for a, b in zip(empirical_pfa, analytic_pfa)), 0.025)
        self.assertLess(max(abs(a - b) for a, b in zip(empirical_pd, analytic_pd)), 0.025)
        self.assertNotEqual(model["h0_unit_projection"], model["h1_unit_projection"])

        private_draws = (
            "noise_h0_unit = randn(private_stream, sample_count, trial_count)",
            "noise_h1_unit = randn(private_stream, sample_count, trial_count)",
            "recovery_noise_h0_unit = randn(recovery_stream, sample_count, trial_count)",
            "recovery_noise_h1_unit = randn(recovery_stream, sample_count, trial_count)",
        )
        for draw in private_draws:
            with self.subTest(draw=draw):
                self.assertIn(draw, self.experiment)
        self.assertEqual(len(re.findall(r"\brandn\s*\(", self.experiment)), 4)

    def test_amplitude_snr_sweep_tracks_bias_variance_and_crlb(self):
        controls = canonical_controls()
        model = self.model
        variances = []
        bounds = []
        normalized_biases = []
        for snr_db in controls["estimator_snr_db_sweep"]:
            snr_linear = 10 ** (snr_db / 10)
            noise_std = controls["signal_amplitude"] * math.sqrt(model["energy"] / snr_linear)
            estimates = [
                controls["signal_amplitude"] + noise_std * projection / model["energy"]
                for projection in model["h1_unit_projection"]
            ]
            bias = sum(estimates) / len(estimates) - controls["signal_amplitude"]
            variance = sample_variance(estimates)
            crlb = noise_std * noise_std / model["energy"]
            variances.append(variance)
            bounds.append(crlb)
            normalized_biases.append(abs(bias) / math.sqrt(crlb))
        self.assertTrue(all(left > right for left, right in zip(bounds, bounds[1:])))
        self.assertLess(max(abs(variance / bound - 1) for variance, bound in zip(variances, bounds)), 0.08)
        self.assertLess(max(normalized_biases), 0.05)

    def test_detected_only_estimation_is_biased_and_recovery_is_exact(self):
        controls = canonical_controls()
        model = self.model
        selected = [
            estimate
            for estimate, score in zip(model["amplitude_estimates"], model["score_h1"])
            if score >= controls["operating_threshold_sigma"]
        ]
        all_mean = sum(model["amplitude_estimates"]) / controls["trial_count"]
        selected_bias = sum(selected) / len(selected) - controls["signal_amplitude"]
        all_bias = all_mean - controls["signal_amplitude"]
        crlb = model["noise_std"] ** 2 / model["energy"]
        alpha = controls["operating_threshold_sigma"] - model["d_prime"]
        survival = 0.5 * math.erfc(alpha / math.sqrt(2))
        density = math.exp(-0.5 * alpha * alpha) / math.sqrt(2 * math.pi)
        analytic_selection_bias = math.sqrt(crlb) * density / survival
        self.assertGreater(len(selected), 0)
        self.assertLess(len(selected), controls["trial_count"])
        self.assertGreater(selected_bias, all_bias + 0.1)
        self.assertLess(abs(selected_bias - analytic_selection_bias), 0.04)
        self.assertEqual(deterministic_model()["amplitude_estimates"], model["amplitude_estimates"])

    def test_threshold_conditioning_uses_the_same_h1_records(self):
        controls = canonical_controls()
        model = self.model
        estimate_scale = model["noise_std"] / math.sqrt(model["energy"])
        for score, estimate in zip(model["score_h1"], model["amplitude_estimates"]):
            self.assertAlmostEqual(estimate, estimate_scale * score, places=12)

        selected_counts = []
        selected_biases = []
        for threshold in controls["threshold_sigma_sweep"]:
            selected = [
                estimate
                for estimate, score in zip(
                    model["amplitude_estimates"], model["score_h1"]
                )
                if score >= threshold
            ]
            selected_counts.append(len(selected))
            selected_biases.append(
                sum(selected) / len(selected) - controls["signal_amplitude"]
            )

        self.assertTrue(
            all(left > right for left, right in zip(selected_counts, selected_counts[1:]))
        )
        self.assertTrue(
            all(left < right for left, right in zip(selected_biases, selected_biases[1:]))
        )

        broken_body = self.experiment.split(
            "%% Intentionally broken case: estimate only after the detector fires", 1
        )[1].split("%% Recovery: restore every independent H1 trial", 1)[0]
        for marker in (
            "amplitude_estimates = matched_filter_h1/template_energy",
            "detected_h1 = score_h1 >= operating_threshold_sigma",
            "broken_selected_estimates = amplitude_estimates(detected_h1)",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.experiment)
        self.assertNotIn("score_h0 >= operating_threshold_sigma", broken_body)

    def test_recovery_replays_full_h1_bank_instead_of_aliasing_estimates(self):
        controls = canonical_controls()
        replayed = deterministic_model()
        selected_count = sum(
            score >= controls["operating_threshold_sigma"]
            for score in self.model["score_h1"]
        )
        self.assertLess(selected_count, len(replayed["amplitude_estimates"]))
        self.assertEqual(
            replayed["amplitude_estimates"], self.model["amplitude_estimates"]
        )

        recovery_body = self.experiment.split(
            "%% Recovery: restore every independent H1 trial and reproduce the seed", 1
        )[1].split("%% Retained results for guided inspection", 1)[0]
        self.assertNotIn("recovered_estimates = amplitude_estimates", recovery_body)
        for marker in (
            "recovery_received_h1 = signal_amplitude*template*ones(1, trial_count)",
            "baseline_noise_std*recovery_noise_h1_unit",
            "recovery_matched_filter_h1 = template.'*recovery_received_h1",
            "recovered_estimates = recovery_matched_filter_h1/template_energy",
            "isequal(recovered_estimates, amplitude_estimates)",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, recovery_body)

    def test_display_bins_conserve_mass_including_malformed_and_tail_cases(self):
        edges = (-5.0, -4.0, 0.0, 6.0, 7.0)
        values = [-100.0, -5.0, -4.0, -0.5, 0.0, 6.0, 7.0, 100.0]
        counts = display_histogram_counts(values, edges)
        self.assertEqual(counts, [2, 2, 1, 3])
        self.assertEqual(sum(counts), len(values))
        with self.assertRaises(ValueError):
            display_histogram_counts([0.0], (0.0, 0.0, 1.0))
        with self.assertRaises(ValueError):
            display_histogram_counts([float("nan")], (-1.0, 0.0, 1.0))
        source_markers = (
            "bin_index == 1",
            "score_h0 < statistic_bin_edges(bin_index+1)",
            "score_h1 >= statistic_bin_edges(bin_index)",
            "sum(h0_statistic_counts) == trial_count",
            "sum(h1_statistic_counts) == trial_count",
            "endpoint bins include tails",
        )
        for marker in source_markers:
            self.assertIn(marker, self.experiment)

    def test_experiment_exposes_model_sweeps_failure_and_recovery(self):
        required = (
            "template.'*received_h0",
            "template.'*received_h1",
            "score_h0 = matched_filter_h0/(baseline_noise_std*sqrt(template_energy))",
            "baseline_noise_std = signal_amplitude*sqrt(",
            "template_energy/baseline_matched_snr_linear)",
            "baseline_snr_reconstructed = signal_amplitude^2*template_energy/",
            "baseline_snr_reconstructed-baseline_matched_snr_linear",
            "threshold_sigma_sweep = [-1 -0.5 0 0.5 1 1.5 2 2.5 3]",
            "0.5*erfc(threshold_value/sqrt(2))",
            "0.5*erfc((threshold_value-baseline_d_prime)/sqrt(2))",
            "roc_empirical_pfa_with_limits = [1 empirical_pfa 0]",
            "roc_empirical_pd_with_limits = [1 empirical_pd 0]",
            "roc_analytic_pfa_with_limits = [1 analytic_pfa 0]",
            "roc_analytic_pd_with_limits = [1 analytic_pd 0]",
            "sweep_noise_std = signal_amplitude*sqrt(template_energy/sweep_snr_linear)",
            "sweep_amplitude_estimates = template.'*sweep_received/template_energy",
            "template_energy/sweep_noise_std^2",
            "1/estimator_fisher_information(snr_index)",
            "estimator_reconstructed_snr(snr_index) = signal_amplitude^2*",
            "estimator_reconstructed_snr-estimator_declared_snr_linear",
            "Intentionally broken case",
            "broken_unbiased_claim_valid = false",
            "selection_alpha = operating_threshold_sigma-baseline_d_prime",
            "selection_survival = 0.5*erfc(selection_alpha/sqrt(2))",
            "selection_density = exp(-0.5*selection_alpha^2)/sqrt(2*pi)",
            "selection_density/selection_survival",
            "broken_selected_bias-analytic_selection_bias",
            "recovery_exact_match",
            "results.roc",
            "results.estimator_snr_sweep",
            "results.broken",
            "results.recovery",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.experiment)
        threshold_body = self.experiment.split(
            "%% Sweep 1: change only the normalized decision threshold", 1
        )[1].split("%% Sweep 2: change only matched-filter SNR", 1)[0]
        self.assertNotRegex(threshold_body, r"\brand\s*\(|\brandn\s*\(")
        snr_body = self.experiment.split(
            "%% Sweep 2: change only matched-filter SNR", 1
        )[1].split("%% Intentionally broken case", 1)[0]
        self.assertNotRegex(snr_body, r"\brand\s*\(|\brandn\s*\(")

    def test_validation_precedes_work_and_resources_are_fixed(self):
        marker = self.experiment.index("% Validation succeeded:")
        for work in ("RandStream(", "randn(", "zeros(", "figure(", "findall("):
            with self.subTest(work=work):
                self.assertGreater(self.experiment.index(work), marker)
        resources = (
            "max_trial_count = 12000",
            "max_sample_count = 16",
            "max_threshold_cases = 9",
            "max_estimator_snr_cases = 7",
            "max_figure_groups = 5",
            "max_stored_numeric_values = 2500000",
            "estimated_stored_numeric_values <= max_stored_numeric_values",
        )
        for resource in resources:
            self.assertIn(resource, self.experiment)
        self.assertNotRegex(self.experiment, r"\bwhile\b|\bparfor\b|\btimer\s*\(")

    def test_plots_metrics_and_units_are_purposeful(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 5)
        labels = (
            "Sample within pulse (dimensionless)",
            "Real amplitude (normalized units)",
            "Normalized matched-filter statistic u (noise sigma)",
            "False-alarm probability P_{FA}",
            "Detection probability P_D",
            "Decision threshold gamma (noise sigma)",
            "Matched-filter signal-to-noise ratio (dB)",
            "Squared amplitude error (normalized amplitude^2)",
            "Amplitude bias (normalized amplitude)",
        )
        for label in labels:
            self.assertIn(label, self.experiment)
        for metric in ("empirical_pfa", "empirical_pd", "amplitude_bias", "amplitude_variance", "amplitude_crlb"):
            self.assertIn(f"'{metric}'", self.experiment)

    def test_docs_are_concept_first_and_cover_limits_and_dependencies(self):
        lesson = self.text["lesson.md"]
        walkthrough = self.text["walkthrough.md"]
        checks = self.text["checks.md"]
        for marker in ("Physical model", "Detection: a threshold", "Estimation: bias", "Limiting cases", "Common interpretation mistakes", "DSP and radar connection"):
            self.assertIn(marker, lesson)
        for marker in ("P27", "P08", "P24", "real noise", "Fisher information", "effective RMS bandwidth", "selection bias"):
            self.assertIn(marker.lower(), lesson.lower())
        for marker in ("Sweep one variable: threshold only", "Sweep one variable: noise scale", "Intentionally broken case", "Recover", "Completion connection"):
            self.assertIn(marker.lower(), walkthrough.lower())
        for marker in (
            "known positive signal polarity",
            "raising SNR only by increasing the unknown true amplitude",
            "relative error instead",
        ):
            self.assertIn(marker.lower(), lesson.lower())
        for marker in ("Observation checks", "Prediction checks", "Interpretation checks", "Completion checklist", "Short teach-back rubric"):
            self.assertIn(marker, checks)

    def test_placeholder_black_box_and_external_io_regressions(self):
        combined = "\n".join(self.text.values())
        self.assertNotIn("TODO", combined)
        self.assertNotRegex(combined, r"(?i)placeholder|implementation batch `P28` is pending")
        forbidden_calls = (
            r"\bawgn\s*\(",
            r"\bqfunc\s*\(",
            r"\bperfcurve\s*\(",
            r"\bfitdist\s*\(",
            r"\bmle\s*\(",
            r"\bcomm\.",
            r"\bphased\.",
            r"\brng\s*\(",
            r"\bclose\s+all\b",
            r"\bsave\s*\(",
            r"\bfopen\s*\(",
            r"\bweb(read|write|save)\s*\(",
            r"\bsystem\s*\(",
        )
        for pattern in forbidden_calls:
            with self.subTest(pattern=pattern):
                self.assertNotRegex(self.experiment, pattern)

    def test_cancellation_recovery_isolation_compatibility_and_rollback_are_explicit(self):
        operational = self.text["walkthrough.md"] + self.text["checks.md"]
        for marker in (
            "Ctrl+C",
            "private seed",
            "global random",
            "figures tagged `P28`",
            ".learning/",
            "worker",
            "timer",
            "external transaction",
            "base MATLAB",
            "Rollback",
            "scaffolded",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), operational.lower())
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P28'))", self.experiment)
        self.assertEqual(self.experiment.count("RandStream('mt19937ar', 'Seed', random_seed)"), 2)

    def test_public_catalogs_and_isolated_learner_entry_with_timeout(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 28 closes Phase 3", root_readme)
        self.assertIn("Project 28 follows P27", start_here)
        self.assertRegex(module_index, r"\| \[P28\].*\| implemented \|")

        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            fixture_root = Path(temporary) / "repo"
            fixture_cli = fixture_root / "bin/learn"
            fixture_manifest = fixture_root / "curriculum/modules.json"
            fixture_cli.parent.mkdir(parents=True)
            fixture_manifest.parent.mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture_cli)
            shutil.copy2(ROOT / "curriculum/modules.json", fixture_manifest)
            environment = os.environ.copy()
            environment["HOME"] = temporary
            process = subprocess.run(
                [str(fixture_cli), "start", "28"],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("P28 — Connect Thresholds to ROC Curves and Estimator Limits", process.stdout)
            self.assertIn("status: implemented", process.stdout)
            self.assertIn("Tutor entry", process.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_retained_evidence_is_honest_and_complete(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P28-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        for marker in (
            "Acceptance mapping",
            "Exact commands and results",
            "Changed and preserved invariants",
            "Residual risks and unperformed validation",
            "Rollback and recovery",
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
        for outcome in (
            "PASS — Curriculum validation passed: 84 modules, 28 implemented.",
            "PASS — Ran 519 tests; OK.",
            "PASS — Curriculum validation passed with 84 modules and 28 implemented; Ran",
        ):
            self.assertIn(outcome, evidence)


if __name__ == "__main__":
    unittest.main()
