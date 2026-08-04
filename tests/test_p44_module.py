from __future__ import annotations

import copy
import json
import math
import os
import random
import re
import shutil
import statistics
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/44-build-an-empirical-radar-roc-curve"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How does threshold choice trade probability of detection against false alarm?"
EXPECTED_IDENTITY = {
    "number": 44,
    "id": "P44",
    "title": "Build an Empirical Radar ROC Curve",
    "guiding_question": QUESTION,
    "phase": 5,
    "phase_title": "Detection and CFAR",
    "slug": "build-an-empirical-radar-roc-curve",
    "folder": "modules/44-build-an-empirical-radar-roc-curve",
    "status": "implemented",
    "implementation_batch": "P44",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p44_contract(path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        artifact = path / name
        if not artifact.is_file():
            errors.append(f"P44 missing {name}")
        elif not artifact.read_text(encoding="utf-8").strip():
            errors.append(f"P44 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P44"]
    if len(matches) != 1:
        return errors + [f"expected one P44 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P44 {key} must be {expected!r}")
    return errors


def canonical_controls() -> dict[str, object]:
    return {
        "seed": 4401,
        "samples": 16,
        "trials": 60_000,
        "amplitude": 1.0,
        "snr_db": (-6.0, 0.0, 6.0, 12.0),
        "baseline_snr_db": 6.0,
        "thresholds": (-1.0, 0.0, 1.0, 2.0, 2.5, 3.090232306, 3.5, 4.0, 5.0),
        "design_pfa": 0.001,
        "operating_index": 6,
        "trial_sweep": (500, 2_000, 10_000, 60_000),
        "searched_cells": 1_000_000,
        "broken_training_count": 250,
        "max_stored_values": 2_400_000,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    for name in ("seed", "samples", "trials", "operating_index", "searched_cells", "broken_training_count", "max_stored_values"):
        value = controls[name]
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{name} must be an integer")
    for name in ("amplitude", "baseline_snr_db", "design_pfa"):
        if not finite_real(controls[name]):
            raise ValueError(f"{name} must be finite and real")

    if controls["seed"] != 4401:
        raise ValueError("seed must remain canonical")
    if controls["samples"] != 16:
        raise ValueError("sample count must match the fixed 16-sample template")
    if not 10_000 <= controls["trials"] <= 60_000:
        raise ValueError("trial count outside reviewed bounds")
    if controls["amplitude"] <= 0:
        raise ValueError("amplitude must be positive")
    if not 0 < controls["design_pfa"] < 0.5:
        raise ValueError("design Pfa must be a one-sided probability")
    if not 60_000 <= controls["searched_cells"] <= 10_000_000:
        raise ValueError("searched cell count outside reviewed bounds")
    if not 100 <= controls["broken_training_count"] < controls["trials"] / 10:
        raise ValueError("broken-bank size outside reviewed bounds")
    if controls["max_stored_values"] != 2_400_000:
        raise ValueError("stored-value ceiling must remain reviewed and fixed")

    vectors = (
        ("snr_db", 3, 6),
        ("thresholds", 7, 12),
        ("trial_sweep", 3, 6),
    )
    for name, minimum, maximum in vectors:
        values = controls[name]
        if not isinstance(values, (tuple, list)) or not minimum <= len(values) <= maximum:
            raise ValueError(f"{name} must have a bounded case count")
        if not all(finite_real(item) for item in values):
            raise ValueError(f"{name} must contain finite real values")
        if any(right <= left for left, right in zip(values, values[1:])):
            raise ValueError(f"{name} must be strictly increasing")

    snr_db = tuple(float(value) for value in controls["snr_db"])
    thresholds = tuple(float(value) for value in controls["thresholds"])
    trial_sweep = tuple(controls["trial_sweep"])
    if controls["baseline_snr_db"] not in snr_db:
        raise ValueError("baseline SNR must be in the SNR sweep")
    if controls["operating_index"] < 1 or controls["operating_index"] > len(thresholds):
        raise ValueError("operating index outside threshold grid")
    gamma = math.sqrt(2) * _erfcinv(2 * controls["design_pfa"])
    if abs(thresholds[controls["operating_index"] - 1] - gamma) >= 1e-8:
        raise ValueError("operating threshold must match design Pfa")
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in trial_sweep):
        raise ValueError("trial sweep must contain integer counts")
    if trial_sweep[-1] != controls["trials"] or trial_sweep[0] < 100:
        raise ValueError("trial sweep must be bounded by the full bank")

    estimated = (
        2 * controls["samples"] * controls["trials"]
        + 6 * controls["trials"]
        + 100 * (len(snr_db) * len(thresholds) + len(trial_sweep))
    )
    if estimated > controls["max_stored_values"]:
        raise ValueError("controls exceed the stored-value ceiling")


def _erfcinv(value: float) -> float:
    """Invert erfc through the standard-library normal quantile."""
    return statistics.NormalDist().inv_cdf(1 - value / 2) / math.sqrt(2)


def q_function(value: float) -> float:
    return 0.5 * math.erfc(value / math.sqrt(2))


def matlab_controls(source: str) -> dict[str, object]:
    def scalar(name: str) -> float:
        match = re.search(rf"^{name}\s*=\s*([0-9.]+);$", source, re.MULTILINE)
        if match is None:
            raise ValueError(f"missing MATLAB scalar {name}")
        return float(match.group(1))

    def vector(name: str) -> tuple[float, ...]:
        match = re.search(rf"^{name}\s*=\s*\[([^\]]+)\];$", source, re.MULTILINE)
        if match is None:
            raise ValueError(f"missing MATLAB vector {name}")
        return tuple(float(item) for item in match.group(1).split())

    return {
        "trials": int(scalar("trial_count")),
        "snr_db": vector("snr_db_sweep"),
        "thresholds": vector("threshold_sigma_sweep"),
        "design_pfa": scalar("design_false_alarm_probability"),
        "operating_index": int(scalar("operating_threshold_index")),
        "searched_cells": int(scalar("searched_cell_count")),
        "broken_training_count": int(scalar("broken_training_count")),
        "probability_tolerance": scalar("probability_tolerance"),
    }


def independent_oracle(controls: dict[str, object]) -> dict[str, object]:
    generator = random.Random(4401)
    trials = int(controls["trials"])
    h0 = [generator.gauss(0.0, 1.0) for _ in range(trials)]
    h1_noise = [generator.gauss(0.0, 1.0) for _ in range(trials)]
    thresholds = tuple(controls["thresholds"])
    snr_db = tuple(controls["snr_db"])
    d_prime = [math.sqrt(10 ** (value / 10)) for value in snr_db]
    false_alarm_counts = [sum(value > gamma for value in h0) for gamma in thresholds]
    empirical_pfa = [count / trials for count in false_alarm_counts]
    analytic_pfa = [q_function(gamma) for gamma in thresholds]
    detection_counts = [
        [sum(shift + value > gamma for value in h1_noise) for gamma in thresholds]
        for shift in d_prime
    ]
    empirical_pd = [[count / trials for count in row] for row in detection_counts]
    analytic_pd = [
        [q_function(gamma - shift) for gamma in thresholds] for shift in d_prime
    ]
    broken_count = int(controls["broken_training_count"])
    sorted_h0 = sorted(h0)
    broken_training = sorted_h0[:broken_count]
    broken_holdout = sorted_h0[broken_count:]
    broken_threshold = max(broken_training)
    return {
        "h0": h0,
        "h1_noise": h1_noise,
        "d_prime": d_prime,
        "false_alarm_counts": false_alarm_counts,
        "empirical_pfa": empirical_pfa,
        "analytic_pfa": analytic_pfa,
        "detection_counts": detection_counts,
        "empirical_pd": empirical_pd,
        "analytic_pd": analytic_pd,
        "broken_threshold": broken_threshold,
        "broken_training_false_alarms": sum(value > broken_threshold for value in broken_training),
        "broken_holdout_false_alarms": sum(value > broken_threshold for value in broken_holdout),
    }


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", re.sub(r"\.\.\.\s*", "", source))
    required = (
        "random_seed = 4401",
        "RandStream('mt19937ar', 'Seed', random_seed)",
        "clearvars;",
        "close(findall(0, 'Type', 'figure', 'Tag', 'P44'))",
        "unit_noise_h0 = randn(private_stream, sample_count, trial_count)",
        "unit_noise_h1 = randn(private_stream, sample_count, trial_count)",
        "normalized_noise_h0 = (template.'*unit_noise_h0)/sqrt(template_energy)",
        "normalized_noise_h1 = (template.'*unit_noise_h1)/sqrt(template_energy)",
        "target_present_score = d_prime_sweep(snr_index)+normalized_noise_h1",
        "d_prime_sweep = sqrt(10.^(snr_db_sweep/10))",
        "false_alarm_decisions = normalized_noise_h0 > threshold_sigma",
        "detection_decisions = target_present_score > threshold_sigma",
        "false_alarm_counts(threshold_index)/trial_count",
        "detection_counts(snr_index, threshold_index)/trial_count",
        "0.5*erfc(threshold_sigma/sqrt(2))",
        "threshold_sigma-d_prime_sweep(snr_index)",
        "roc_empirical_pfa = [1 empirical_pfa 0]",
        "roc_empirical_pd = [ones(snr_case_count, 1) empirical_pd zeros(snr_case_count, 1)]",
        "design_false_alarm_probability = 0.001",
        "searched_cell_count*operating_empirical_pfa",
        "trial_count_sweep = [500 2000 10000 60000]",
        "trial_sweep_probability_resolution(trial_index) = 1/case_trial_count",
        "sorted_noise_h0 = sort(normalized_noise_h0)",
        "broken_training_h0 = sorted_noise_h0(1:broken_training_count)",
        "broken_holdout_h0 = sorted_noise_h0(broken_training_count+1:end)",
        "broken_tuned_threshold_sigma = max(broken_training_h0)",
        "broken_claim_is_valid = false",
        "recovery_stream = RandStream('mt19937ar', 'Seed', random_seed)",
        "recovery_exact = isequal(recovery_normalized_noise_h0, normalized_noise_h0) && isequal(recovery_normalized_noise_h1, normalized_noise_h1)",
        "max_stored_numeric_values == 2400000",
        "estimated_stored_numeric_values <= max_stored_numeric_values",
        "results.expected_false_alarms_per_scan_empirical",
        "results.broken_claim_is_valid",
        "results.recovery_exact",
    )
    return [marker for marker in required if marker not in compact]


class P44ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.docs = {
            name: (MODULE / name).read_text(encoding="utf-8")
            for name in ARTIFACTS
            if name != "experiment.m"
        }
        cls.controls = matlab_controls(cls.source)
        cls.oracle = independent_oracle(cls.controls)

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self):
        self.assertEqual(validate_p44_contract(MODULE, self.manifest), [])
        entries = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(entries["P43"]["status"], "implemented")
        self.assertEqual(entries["P44"], EXPECTED_IDENTITY)
        for name in ARTIFACTS:
            data = (MODULE / name).read_bytes()
            self.assertTrue(data.endswith(b"\n"), name)
            self.assertFalse(data.endswith(b"\n\n"), name)
            self.assertNotIn(b"\r", data, name)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "module"
            shutil.copytree(MODULE, fixture)
            (fixture / "walkthrough.md").unlink()
            self.assertIn("P44 missing walkthrough.md", validate_p44_contract(fixture, self.manifest))
            (fixture / "walkthrough.md").write_text("", encoding="utf-8")
            self.assertIn("P44 empty walkthrough.md", validate_p44_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p44_contract(MODULE, None))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p44_contract(MODULE, {"modules": [None]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn(
            "expected one P44 manifest entry, found 2",
            validate_p44_contract(MODULE, duplicate),
        )
        for key in EXPECTED_IDENTITY:
            drifted = copy.deepcopy(self.manifest)
            next(item for item in drifted["modules"] if item["id"] == "P44")[key] = "drift"
            errors = validate_p44_contract(MODULE, drifted)
            if key == "id":
                self.assertTrue(any("one P44 manifest entry" in error for error in errors))
            else:
                self.assertTrue(any(key in error for error in errors), key)

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self):
        validate_controls()
        invalid = (
            {"seed": True},
            {"seed": 4402},
            {"samples": 8},
            {"samples": 15},
            {"samples": 17},
            {"samples": 32},
            {"trials": 9999},
            {"trials": 60_001},
            {"amplitude": math.nan},
            {"amplitude": 0},
            {"design_pfa": 0},
            {"design_pfa": 0.5},
            {"snr_db": (-6, 6, 0)},
            {"snr_db": (-6, 0, math.inf)},
            {"baseline_snr_db": 3},
            {"thresholds": (-1, 0, 1, 2, 2.5, 3.0, 3.5)},
            {"thresholds": (-1, 0, 1, 2, 2.5, math.nan, 3.5, 4, 5)},
            {"operating_index": 0},
            {"trial_sweep": (500, 500, 60_000)},
            {"trial_sweep": (500.0, 2_000, 60_000)},
            {"searched_cells": 59_999},
            {"searched_cells": 10_000_001},
            {"broken_training_count": 99},
            {"broken_training_count": 6_000},
            {"max_stored_values": 2_300_000},
            {"unknown": 1},
        )
        for controls in invalid:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_independent_gaussian_oracle_matches_roc_model_and_limits(self):
        pfa = self.oracle["empirical_pfa"]
        analytic_pfa = self.oracle["analytic_pfa"]
        pd = self.oracle["empirical_pd"]
        analytic_pd = self.oracle["analytic_pd"]
        self.assertTrue(all(right <= left for left, right in zip(pfa, pfa[1:])))
        for row in pd:
            self.assertTrue(all(right <= left for left, right in zip(row, row[1:])))
        for threshold_index in range(len(self.controls["thresholds"])):
            column = [row[threshold_index] for row in pd]
            self.assertTrue(all(right > left for left, right in zip(column, column[1:])))
        tolerance = self.controls["probability_tolerance"]
        self.assertEqual(tolerance, 0.015)
        self.assertLess(max(abs(a - b) for a, b in zip(pfa, analytic_pfa)), tolerance)
        self.assertLess(
            max(abs(a - b) for erow, arow in zip(pd, analytic_pd) for a, b in zip(erow, arow)),
            tolerance,
        )
        for row in pd:
            roc_pfa = [1, *pfa, 0]
            roc_pd = [1, *row, 0]
            self.assertEqual((roc_pfa[0], roc_pd[0]), (1, 1))
            self.assertEqual((roc_pfa[-1], roc_pd[-1]), (0, 0))

    def test_operating_point_false_alarm_cost_and_conditioned_counts(self):
        index = int(self.controls["operating_index"]) - 1
        gamma = self.controls["thresholds"][index]
        self.assertAlmostEqual(gamma, 3.090232306, places=9)
        self.assertAlmostEqual(q_function(gamma), self.controls["design_pfa"], places=9)
        empirical_pfa = self.oracle["false_alarm_counts"][index] / self.controls["trials"]
        expected_false_alarms = self.controls["searched_cells"] * empirical_pfa
        self.assertGreater(self.oracle["false_alarm_counts"][index], 0)
        self.assertLess(abs(empirical_pfa - self.controls["design_pfa"]), 0.001)
        self.assertEqual(expected_false_alarms, self.controls["searched_cells"] * empirical_pfa)
        self.assertEqual(self.controls["searched_cells"] * self.controls["design_pfa"], 1000)
        for row in self.oracle["detection_counts"]:
            self.assertLessEqual(row[index], self.controls["trials"])

    def test_finite_trial_resolution_broken_training_and_independent_recovery(self):
        trial_sweep = canonical_controls()["trial_sweep"]
        resolution = [1 / count for count in trial_sweep]
        self.assertTrue(all(right < left for left, right in zip(resolution, resolution[1:])))
        self.assertGreater(resolution[0], self.controls["design_pfa"])
        self.assertEqual(self.oracle["broken_training_false_alarms"], 0)
        self.assertGreater(self.oracle["broken_holdout_false_alarms"], 0)
        replay = independent_oracle(self.controls)
        self.assertEqual(replay["h0"], self.oracle["h0"])
        self.assertEqual(replay["h1_noise"], self.oracle["h1_noise"])
        self.assertEqual(replay["false_alarm_counts"], self.oracle["false_alarm_counts"])
        self.assertEqual(replay["detection_counts"], self.oracle["detection_counts"])

    def test_source_contract_mutations_and_base_matlab_compatibility(self):
        self.assertEqual(source_contract_errors(self.source), [])
        self.assertEqual(self.source.count("figure('Name'"), 5)
        banned = (
            "phased.",
            "dsp.",
            "awgn(",
            "norminv(",
            "perfcurve(",
            "cfar(",
            "rng(",
            "fopen(",
            "fwrite(",
            "load(",
            "save(",
            "system(",
            "webread(",
            "urlread(",
            "parfor",
            "while true",
            "timer(",
            "global ",
        )
        lowered = self.source.lower()
        for marker in banned:
            self.assertNotIn(marker, lowered)
        mutations = (
            self.source.replace("sqrt(10.^(snr_db_sweep/10))", "10.^(snr_db_sweep/10)", 1),
            self.source.replace("false_alarm_counts(threshold_index)/trial_count", "false_alarm_counts(threshold_index)/(2*trial_count)", 1),
            self.source.replace("broken_claim_is_valid = false", "broken_claim_is_valid = true", 1),
            self.source.replace("unit_noise_h1 = randn(private_stream", "unit_noise_h1 = unit_noise_h0; %", 1),
            self.source.replace("max_stored_numeric_values == 2400000", "max_stored_numeric_values > 0", 1),
        )
        for mutated in mutations:
            self.assertTrue(source_contract_errors(mutated))

    def test_controls_precede_allocation_and_loops_are_bounded(self):
        validation = self.source.index("%% Reject malformed")
        first_allocation = self.source.index("unit_noise_h0 = randn")
        first_figure = self.source.index("figure('Name'")
        self.assertLess(validation, first_allocation)
        self.assertLess(first_allocation, first_figure)
        self.assertIn("estimated_stored_numeric_values <= max_stored_numeric_values", self.source)
        self.assertNotIn("\nwhile ", self.source)
        self.assertEqual(len(re.findall(r"^for ", self.source, re.MULTILINE)), 5)

    def test_fixed_template_rejects_in_range_sample_count_shape_mismatch(self):
        guard = "sample_count == 16 && sample_count <= max_sample_count"
        self.assertIn(guard, self.source)
        self.assertLess(self.source.index(guard), self.source.index("unit_noise_h0 = randn"))
        for mismatched_count in (8, 15, 17, 32):
            with self.subTest(sample_count=mismatched_count), self.assertRaises(ValueError):
                validate_controls(samples=mismatched_count)

    def _fixture(self, *, rolled_back: bool = False) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        fixture = Path(temporary.name) / "repo"
        (fixture / "bin").mkdir(parents=True)
        (fixture / "curriculum").mkdir()
        for entry in self.manifest["modules"]:
            destination = fixture / entry["folder"] / "README.md"
            destination.parent.mkdir(parents=True)
            shutil.copy2(ROOT / entry["folder"] / "README.md", destination)
        shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
        manifest = copy.deepcopy(self.manifest)
        if rolled_back:
            next(item for item in manifest["modules"] if item["id"] == "P44")["status"] = "scaffolded"
        (fixture / "curriculum/modules.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        return fixture

    def test_isolated_cli_timeout_and_scaffold_rollback_compatibility(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        fixture = self._fixture()
        result = subprocess.run(
            [str(fixture / "bin/learn"), "start", "44"],
            cwd=fixture,
            text=True,
            capture_output=True,
            env=os.environ.copy(),
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("P44 — Build an Empirical Radar ROC Curve", result.stdout)
        self.assertIn("status: implemented", result.stdout)
        rolled = self._fixture(rolled_back=True)
        rollback_result = subprocess.run(
            [str(rolled / "bin/learn"), "start", "44"],
            cwd=rolled,
            text=True,
            capture_output=True,
            env=os.environ.copy(),
            timeout=10,
        )
        self.assertEqual(rollback_result.returncode, 3)
        self.assertIn("status: scaffolded", rollback_result.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_docs_cover_baseline_sweeps_failure_recovery_and_teach_back(self):
        for name, text in self.docs.items():
            self.assertIn(QUESTION, text, name)
            self.assertNotIn("TODO", text, name)
            self.assertNotIn("placeholder", text.lower(), name)
        walkthrough = self.docs["walkthrough.md"]
        for marker in (
            "Baseline",
            "Sweep 1",
            "Sweep 2",
            "Intentionally broken case",
            "Recovery",
            "Expected observation",
            "Common mistake",
            "Ctrl+C",
        ):
            self.assertIn(marker, walkthrough)
        combined = "\n".join(self.docs.values()).lower()
        for marker in (
            "p43",
            "target-absent",
            "target-present",
            "matched-filter",
            "private seed",
            "base matlab",
            "bounded",
            "one million",
        ):
            self.assertIn(marker, combined)
        checks = self.docs["checks.md"]
        for marker in (
            "Observation checks",
            "Interpretation checks",
            "Prediction checks",
            "Short teach-back rubric",
        ):
            self.assertIn(marker, checks)

    def test_p44_only_rollback_preserves_neighbor_identity(self):
        rolled = copy.deepcopy(self.manifest)
        neighbors_before = {
            item["id"]: copy.deepcopy(item)
            for item in rolled["modules"]
            if item["id"] in {"P43", "P45"}
        }
        next(item for item in rolled["modules"] if item["id"] == "P44")["status"] = "scaffolded"
        neighbors_after = {
            item["id"]: item
            for item in rolled["modules"]
            if item["id"] in {"P43", "P45"}
        }
        self.assertEqual(neighbors_after, neighbors_before)
        self.assertTrue(any("status" in error for error in validate_p44_contract(MODULE, rolled)))

    def test_public_catalogs_describe_p44_without_freezing_future_state(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 44 forms independent normalized matched-filter", readme)
        self.assertIn("Project 44 follows P43", start_here)
        self.assertRegex(module_index, r"\| \[P44\].*\| implemented \| 5 \|")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self):
        evidence = ROOT / "docs/evidence/P44-2026-08-04.md"
        self.assertTrue(evidence.is_file())
        text = evidence.read_text(encoding="utf-8")
        for heading in (
            "## Outcome and claim boundary",
            "## Acceptance mapping",
            "## Physical model and independent static oracle",
            "## Figure and metric inventory",
            "## Focused test coverage",
            "## Exact commands and results",
            "## Changed and preserved invariants",
            "## Rollback and recovery",
            "## Residual risks and unperformed validation",
        ):
            self.assertIn(heading, text)
        for command in (
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
        ):
            self.assertIn(command, text)
        self.assertIn("matlab and octave did not run", re.sub(r"\s+", " ", text.lower()))
        data = evidence.read_bytes()
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))
        self.assertNotIn(b"\r", data)


if __name__ == "__main__":
    unittest.main()
