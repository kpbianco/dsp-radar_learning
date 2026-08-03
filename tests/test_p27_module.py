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
MODULE = ROOT / "modules/27-use-monte-carlo-trials-instead-of-one-lucky-run"
QUESTION = "Why is one noise realization not enough to judge an algorithm?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
EXPECTED_IDENTITY = {
    "number": 27,
    "id": "P27",
    "title": "Use Monte Carlo Trials Instead of One Lucky Run",
    "guiding_question": QUESTION,
    "phase": 3,
    "phase_title": "Modulation, Channels, and Statistical Estimation",
    "slug": "use-monte-carlo-trials-instead-of-one-lucky-run",
    "folder": "modules/27-use-monte-carlo-trials-instead-of-one-lucky-run",
    "status": "implemented",
    "implementation_batch": "P27",
}


def validate_p27_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P27 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P27 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    matches = [
        entry
        for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P27"
    ]
    if len(matches) != 1:
        return errors + [f"expected one P27 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P27 {key} must be {expected!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def canonical_controls() -> dict:
    return {
        "random_seed": 2701,
        "symbol_count": 4000,
        "samples_per_symbol": 16,
        "baseline_eb_n0_db": 2.0,
        "bit_energy": 1.0,
        "trial_count_sweep": (10, 25, 100, 500, 4000),
        "eb_n0_db_sweep": (-4.0, -2.0, 0.0, 2.0, 4.0),
        "confidence_z": 1.96,
        "block_length": 100,
        "broken_repeat_count": 4000,
        "max_trial_count": 4000,
        "max_samples_per_symbol": 16,
        "max_trial_sweep_cases": 5,
        "max_snr_sweep_cases": 5,
        "max_figure_groups": 5,
        "max_stored_numeric_values": 700000,
        "workspace_vector_equivalents": 36,
        "waveform_matrix_equivalents": 8,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    vectors = {
        "trial_count_sweep": canonical_controls()["trial_count_sweep"],
        "eb_n0_db_sweep": canonical_controls()["eb_n0_db_sweep"],
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

    if controls["symbol_count"] > controls["max_trial_count"]:
        raise ValueError("trial count exceeds resource ceiling")
    if controls["samples_per_symbol"] > controls["max_samples_per_symbol"]:
        raise ValueError("waveform length exceeds resource ceiling")
    if len(controls["trial_count_sweep"]) > controls["max_trial_sweep_cases"]:
        raise ValueError("trial sweep exceeds resource ceiling")
    if len(controls["eb_n0_db_sweep"]) > controls["max_snr_sweep_cases"]:
        raise ValueError("SNR sweep exceeds resource ceiling")
    if controls["trial_count_sweep"][-1] != controls["symbol_count"]:
        raise ValueError("trial sweep must end at baseline count")
    if controls["symbol_count"] % controls["block_length"]:
        raise ValueError("block length must divide trial count")
    if controls["broken_repeat_count"] != controls["symbol_count"]:
        raise ValueError("broken report must use the baseline nominal count")
    estimated = (
        controls["symbol_count"] * controls["workspace_vector_equivalents"]
        + controls["symbol_count"]
        * controls["samples_per_symbol"]
        * controls["waveform_matrix_equivalents"]
        + 1000
    )
    if estimated > controls["max_stored_numeric_values"]:
        raise ValueError("conservative numeric storage bound exceeded")


def wilson_interval(errors: int, count: int, z_value: float = 1.96) -> tuple[float, float]:
    estimate = errors / count
    denominator = 1 + z_value * z_value / count
    center = (estimate + z_value * z_value / (2 * count)) / denominator
    half = z_value / denominator * math.sqrt(
        estimate * (1 - estimate) / count
        + z_value * z_value / (4 * count * count)
    )
    return max(0.0, center - half), min(1.0, center + half)


def display_histogram_counts(values: list[float], edges: tuple[float, ...]) -> list[int]:
    """Bin every finite value while folding unbounded tails into endpoint bins."""
    if len(edges) < 2 or any(left >= right for left, right in zip(edges, edges[1:])):
        raise ValueError("histogram edges must be strictly increasing")
    counts = [0] * (len(edges) - 1)
    for value in values:
        if not math.isfinite(value):
            raise ValueError("histogram values must be finite")
        if value < edges[1]:
            counts[0] += 1
            continue
        if value >= edges[-2]:
            counts[-1] += 1
            continue
        for index in range(1, len(edges) - 2):
            if edges[index] <= value < edges[index + 1]:
                counts[index] += 1
                break
    return counts


def deterministic_trials() -> dict:
    controls = canonical_controls()
    generator = random.Random(controls["random_seed"])
    count = controls["symbol_count"]
    sample_count = controls["samples_per_symbol"]
    symbols = [1 if generator.random() >= 0.5 else -1 for _ in range(count)]
    noise = [
        [generator.gauss(0.0, 1.0) for _ in range(count)]
        for _ in range(sample_count)
    ]
    pulse_sample = 1 / math.sqrt(sample_count)

    def outcomes(eb_n0_db: float) -> tuple[list[float], list[bool]]:
        linear = 10 ** (eb_n0_db / 10)
        noise_std = math.sqrt(controls["bit_energy"] / (2 * linear))
        statistics = [
            symbols[index]
            + noise_std
            * sum(noise[row][index] * pulse_sample for row in range(sample_count))
            for index in range(count)
        ]
        errors = [
            (1 if statistic >= 0 else -1) != symbol
            for statistic, symbol in zip(statistics, symbols)
        ]
        return statistics, errors

    statistics, errors = outcomes(controls["baseline_eb_n0_db"])
    return {
        "symbols": symbols,
        "noise": noise,
        "statistics": statistics,
        "errors": errors,
        "outcomes": outcomes,
    }


class P27ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text())
        cls.text = {
            name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        }
        cls.experiment = cls.text["experiment.m"]
        cls.trials = deterministic_trials()

    def test_complete_artifacts_exact_identity_and_prerequisite(self):
        self.assertEqual(validate_p27_contract(MODULE, self.manifest), [])
        for text in self.text.values():
            self.assertIn(QUESTION, text)
        prerequisite = next(
            entry for entry in self.manifest["modules"] if entry["id"] == "P26"
        )
        self.assertEqual(prerequisite["status"], "implemented")

    def test_contract_validator_rejects_nonlist_duplicate_and_wrong_identity(self):
        self.assertIn("manifest modules must be a list", validate_p27_contract(MODULE, {}))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertTrue(any("found 2" in item for item in validate_p27_contract(MODULE, duplicate)))
        for key, expected in EXPECTED_IDENTITY.items():
            with self.subTest(key=key):
                wrong = copy.deepcopy(self.manifest)
                entry = next(item for item in wrong["modules"] if item["id"] == "P27")
                entry[key] = "wrong" if not isinstance(expected, int) else expected + 1
                self.assertTrue(validate_p27_contract(MODULE, wrong))

    def test_contract_validator_rejects_missing_and_empty_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            module_dir = Path(temporary)
            for name in ARTIFACTS:
                (module_dir / name).write_text("content", encoding="utf-8")
            (module_dir / "lesson.md").unlink()
            (module_dir / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p27_contract(module_dir, self.manifest)
            self.assertIn("P27 missing lesson.md", errors)
            self.assertIn("P27 empty checks.md", errors)

    def test_controls_are_canonical_finite_and_resource_bounded(self):
        validate_controls()
        malformed = (
            {"random_seed": True},
            {"symbol_count": float("nan")},
            {"samples_per_symbol": 16 + 1j},
            {"baseline_eb_n0_db": float("inf")},
            {"bit_energy": 0.5},
            {"trial_count_sweep": "ten trials"},
            {"trial_count_sweep": (10, 25, 100, 500)},
            {"eb_n0_db_sweep": (-4, -2, 0, 2, float("nan"))},
            {"confidence_z": 2.0},
            {"block_length": 80},
            {"broken_repeat_count": 3999},
            {"max_trial_count": 3999},
            {"max_samples_per_symbol": 15},
            {"max_trial_sweep_cases": 4},
            {"max_snr_sweep_cases": 4},
            {"max_stored_numeric_values": 600000},
        )
        for override in malformed:
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_controls(**override)
        with self.assertRaises(ValueError):
            validate_controls(unapproved_control=1)

    def test_independent_baseline_matches_bpsk_awgn_behavior(self):
        controls = canonical_controls()
        errors = self.trials["errors"]
        error_count = sum(errors)
        empirical = error_count / controls["symbol_count"]
        analytic = 0.5 * math.erfc(
            math.sqrt(10 ** (controls["baseline_eb_n0_db"] / 10))
        )
        lower, upper = wilson_interval(error_count, controls["symbol_count"])
        self.assertGreater(error_count, 0)
        self.assertLess(error_count, controls["symbol_count"])
        self.assertLess(abs(empirical - analytic), 0.02)
        self.assertLess(lower, analytic)
        self.assertGreater(upper, analytic)

    def test_trial_count_sweep_uses_fixed_prefixes_and_narrows_uncertainty(self):
        errors = self.trials["errors"]
        counts = canonical_controls()["trial_count_sweep"]
        estimates = [sum(errors[:count]) / count for count in counts]
        intervals = [wilson_interval(sum(errors[:count]), count) for count in counts]
        widths = [upper - lower for lower, upper in intervals]
        self.assertEqual(estimates[0], 0.0)
        self.assertLess(widths[-1], widths[0])
        self.assertLess(abs(estimates[-1] - 0.037506128358925986), 0.02)

    def test_eb_n0_sweep_changes_only_noise_scale_and_reduces_ber(self):
        empirical = []
        analytic = []
        for value in canonical_controls()["eb_n0_db_sweep"]:
            _, errors = self.trials["outcomes"](value)
            empirical.append(sum(errors) / len(errors))
            analytic.append(0.5 * math.erfc(math.sqrt(10 ** (value / 10))))
        self.assertTrue(all(left >= right for left, right in zip(empirical, empirical[1:])))
        self.assertTrue(all(left > right for left, right in zip(analytic, analytic[1:])))
        self.assertTrue(all(abs(a - b) < 0.025 for a, b in zip(empirical, analytic)))

    def test_broken_pseudoreplication_and_clean_recovery(self):
        controls = canonical_controls()
        correct = next(index for index, error in enumerate(self.trials["errors"]) if not error)
        repeated_statistics = [self.trials["statistics"][correct]] * controls["broken_repeat_count"]
        repeated_errors = [False] * controls["broken_repeat_count"]
        _, nominal_upper = wilson_interval(sum(repeated_errors), len(repeated_errors))
        analytic = 0.5 * math.erfc(math.sqrt(10 ** (controls["baseline_eb_n0_db"] / 10)))
        self.assertEqual(len(set(repeated_statistics)), 1)
        self.assertEqual(sum(repeated_errors), 0)
        self.assertLess(nominal_upper, analytic)
        self.assertEqual(deterministic_trials()["statistics"], self.trials["statistics"])
        self.assertEqual(deterministic_trials()["errors"], self.trials["errors"])

    def test_empirical_distributions_conserve_mass_including_tail_samples(self):
        edges = (-3.0, -2.0, 0.0, 2.0, 3.0)
        values = [-10.0, -3.0, -2.0, -0.5, 0.0, 2.0, 3.0, 10.0]
        counts = display_histogram_counts(values, edges)
        self.assertEqual(counts, [2, 2, 1, 3])
        self.assertEqual(sum(counts), len(values))

        block_rates = [
            sum(self.trials["errors"][start : start + 100]) / 100
            for start in range(0, canonical_controls()["symbol_count"], 100)
        ]
        block_counts = display_histogram_counts(
            block_rates, (-0.005, 0.005, 0.025, 0.205)
        )
        self.assertEqual(sum(block_counts), len(block_rates))

        for marker in (
            "bin_index == 1",
            "matched_filter_statistic < decision_bin_edges(bin_index+1)",
            "matched_filter_statistic >= decision_bin_edges(bin_index)",
            "sum(negative_symbol_counts) == sum(transmitted_symbols == -1)",
            "sum(positive_symbol_counts) == sum(transmitted_symbols == 1)",
            "sum(block_ber_counts) == numel(block_error_rates)",
            "endpoint bins include tails",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.experiment)

    def test_experiment_exposes_equations_metrics_sweeps_and_distributions(self):
        required = (
            "pulse.'*received_waveforms",
            "baseline_noise_std = sqrt(bit_energy/(2*baseline_eb_n0_linear))",
            "detected_symbols(matched_filter_statistic < 0) = -1",
            "error_outcomes = detected_symbols ~= transmitted_symbols",
            "0.5*erfc(sqrt(baseline_eb_n0_linear))",
            "running_ci_lower",
            "running_ci_upper",
            "block_error_rates",
            "trial_count_sweep = [10 25 100 500 4000]",
            "eb_n0_db_sweep = [-4 -2 0 2 4]",
            "Common random numbers",
            "sweep_noise_std = sqrt(bit_energy/(2*sweep_eb_n0_linear))",
            "sweep_received = transmitted_waveforms + sweep_noise_std*noise_unit",
            "Intentionally broken case",
            "broken_independence_valid = false",
            "recovery_exact_match",
            "results.trial_count_sweep",
            "results.eb_n0_sweep",
            "results.broken",
            "results.recovery",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.experiment)
        sweep_body = self.experiment.split(
            "%% Sweep 2: change only Eb/N0", 1
        )[1].split("%% Intentionally broken case", 1)[0]
        self.assertNotRegex(sweep_body, r"\brand\s*\(|\brandn\s*\(")

    def test_validation_precedes_work_and_resources_are_fixed(self):
        marker = self.experiment.index("% Validation succeeded:")
        for work in ("RandStream(", "rand(", "randn(", "zeros(", "figure(", "findall("):
            with self.subTest(work=work):
                self.assertGreater(self.experiment.index(work), marker)
        for resource in (
            "max_trial_count = 4000",
            "max_samples_per_symbol = 16",
            "max_trial_sweep_cases = 5",
            "max_snr_sweep_cases = 5",
            "max_figure_groups = 5",
            "max_stored_numeric_values = 700000",
            "estimated_stored_numeric_values <= max_stored_numeric_values",
        ):
            self.assertIn(resource, self.experiment)
        self.assertNotRegex(self.experiment, r"\bwhile\b|\bparfor\b|\btimer\s*\(")

    def test_plots_and_retained_metrics_have_units_and_purpose(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 5)
        labels = (
            "Sample within symbol (dimensionless)",
            "Normalized amplitude",
            "Matched-filter statistic (normalized amplitude)",
            "Independent trial index (dimensionless)",
            "Bit-error probability",
            "BER in each 100-independent-trial block",
            "E_b/N_0 (dB)",
        )
        for label in labels:
            self.assertIn(label, self.experiment)
        for metric in ("error_count", "empirical_ber", "analytic_ber", "final_ci"):
            self.assertIn(f"'{metric}'", self.experiment)

    def test_docs_are_concept_first_and_cover_limits_interpretation_and_dependencies(self):
        lesson = self.text["lesson.md"]
        walkthrough = self.text["walkthrough.md"]
        checks = self.text["checks.md"]
        for marker in ("Physical model", "Wilson interval", "Limiting cases", "Common interpretation mistakes", "DSP and radar connection"):
            self.assertIn(marker, lesson)
        for marker in ("P23", "P24", "1/\\sqrt{N}", "zero observed errors", "pseudo-replication"):
            self.assertIn(marker.lower(), lesson.lower())
        for marker in ("Sweep one variable", "intentionally broken case", "Recover", "Completion connection"):
            self.assertIn(marker.lower(), walkthrough.lower())
        for marker in ("Observation checks", "Prediction checks", "Completion checklist", "Short teach-back rubric"):
            self.assertIn(marker, checks)

    def test_placeholder_black_box_and_external_io_regressions(self):
        combined = "\n".join(self.text.values())
        self.assertNotIn("TODO", combined)
        self.assertNotRegex(combined, r"(?i)placeholder|implementation batch `P27` is pending")
        forbidden_calls = (
            r"\bawgn\s*\(",
            r"\bqfunc\s*\(",
            r"\bbiterr\s*\(",
            r"\bfitdist\s*\(",
            r"\bcomm\.",
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
            "figures tagged `P27`",
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
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P27'))", self.experiment)
        self.assertEqual(self.experiment.count("RandStream('mt19937ar', 'Seed', random_seed)"), 2)

    def test_public_catalogs_and_isolated_learner_entry(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 27 sends seeded BPSK pulses", root_readme)
        self.assertIn("Project 27 follows P26", start_here)
        self.assertRegex(module_index, r"\| \[P27\].*\| implemented \|")

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
                [str(fixture_cli), "start", "27"],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("P27 — Use Monte Carlo Trials Instead of One Lucky Run", process.stdout)
            self.assertIn("status: implemented", process.stdout)
            self.assertIn("Tutor entry", process.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_retained_evidence_is_honest_and_complete(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P27-*.md"))
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
            self.assertIn(marker.lower(), evidence.lower())


if __name__ == "__main__":
    unittest.main()
