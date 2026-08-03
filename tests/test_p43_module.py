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
MODULE = ROOT / "modules/43-use-a-fixed-detection-threshold"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Why does a threshold that works in one noise level fail in another?"
EXPECTED_IDENTITY = {
    "number": 43,
    "id": "P43",
    "title": "Use a Fixed Detection Threshold",
    "guiding_question": QUESTION,
    "phase": 5,
    "phase_title": "Detection and CFAR",
    "slug": "use-a-fixed-detection-threshold",
    "folder": "modules/43-use-a-fixed-detection-threshold",
    "status": "implemented",
    "implementation_batch": "P43",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p43_contract(path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        artifact = path / name
        if not artifact.is_file():
            errors.append(f"P43 missing {name}")
        elif not artifact.read_text(encoding="utf-8").strip():
            errors.append(f"P43 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P43"]
    if len(matches) != 1:
        return errors + [f"expected one P43 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P43 {key} must be {expected!r}")
    return errors


def validate_controls(
    *,
    cells: object = 256,
    targets: object = (48, 103, 171, 226),
    trials: object = 20_000,
    design_pfa: object = 0.01,
    noise_ratios: object = (0.75, 1.0, 1.25, 1.5, 2.0),
    clutter_ratios: object = (0.0, 0.5, 1.0, 1.5, 2.0),
    max_stored_values: object = 800_000,
) -> None:
    if not isinstance(cells, int) or isinstance(cells, bool) or not 64 <= cells <= 512:
        raise ValueError("cells must be a bounded integer")
    if not isinstance(trials, int) or isinstance(trials, bool) or not 10_000 <= trials <= 25_000:
        raise ValueError("trials must be a bounded integer")
    if not isinstance(targets, (tuple, list)) or not 2 <= len(targets) <= 8:
        raise ValueError("target indices must have a bounded count")
    if not all(isinstance(item, int) and not isinstance(item, bool) for item in targets):
        raise ValueError("target indices must be integers")
    if not all(1 <= item <= cells for item in targets) or any(
        right <= left for left, right in zip(targets, targets[1:])
    ):
        raise ValueError("target indices must be unique, ordered, and in range")
    if not finite_real(design_pfa) or not 0 < design_pfa < 0.5:
        raise ValueError("design Pfa must be finite and one-sided")
    for name, values, require_zero in (
        ("noise ratios", noise_ratios, False),
        ("clutter ratios", clutter_ratios, True),
    ):
        if not isinstance(values, (tuple, list)) or not 3 <= len(values) <= 9:
            raise ValueError(f"{name} must have a bounded case count")
        if not all(finite_real(item) for item in values):
            raise ValueError(f"{name} must be finite real values")
        if any(right <= left for left, right in zip(values, values[1:])):
            raise ValueError(f"{name} must be strictly increasing")
        if require_zero:
            if values[0] != 0 or any(item < 0 for item in values):
                raise ValueError("clutter ratios must begin at zero")
        elif any(item <= 0 for item in values) or not any(item == 1 for item in values):
            raise ValueError("noise ratios must be positive and include reference")
    if (
        not isinstance(max_stored_values, int)
        or isinstance(max_stored_values, bool)
        or max_stored_values != 800_000
    ):
        raise ValueError("stored-value ceiling must be the reviewed fixed bound")
    estimated_values = (
        20 * trials
        + trials * len(noise_ratios)
        + 8 * cells
        + 40 * (len(noise_ratios) + len(clutter_ratios))
    )
    if estimated_values > max_stored_values:
        raise ValueError("controls exceed stored-value ceiling")


def q_function(value: float) -> float:
    return 0.5 * math.erfc(value / math.sqrt(2))


def matlab_controls(source: str) -> dict[str, object]:
    def scalar(name: str) -> float:
        match = re.search(rf"^{name}\s*=\s*([0-9.]+);$", source, re.MULTILINE)
        if match is None:
            raise ValueError(f"missing canonical MATLAB control {name}")
        return float(match.group(1))

    def vector(name: str) -> tuple[float, ...]:
        match = re.search(rf"^{name}\s*=\s*\[([^\]]+)\];$", source, re.MULTILINE)
        if match is None:
            raise ValueError(f"missing canonical MATLAB vector {name}")
        return tuple(float(item) for item in match.group(1).split())

    return {
        "trials": int(scalar("trial_count")),
        "design_pfa": scalar("design_false_alarm_probability"),
        "amplitude": scalar("target_amplitude"),
        "noise_ratios": vector("noise_rms_ratios"),
        "clutter_ratios": vector("clutter_pedestal_ratios"),
        "probability_tolerance": scalar("probability_tolerance"),
    }


def detector_oracle(
    *,
    trials: int = 20_000,
    design_pfa: float = 0.01,
    amplitude: float = 4.0,
    noise_ratios: tuple[float, ...] = (0.75, 1.0, 1.25, 1.5, 2.0),
    clutter_ratios: tuple[float, ...] = (0.0, 0.5, 1.0, 1.5, 2.0),
) -> dict[str, object]:
    """Independent standard-library oracle for the documented Gaussian model."""
    generator = random.Random(4301)
    h0 = [generator.gauss(0.0, 1.0) for _ in range(trials)]
    h1_noise = [generator.gauss(0.0, 1.0) for _ in range(trials)]
    gamma = statistics.NormalDist().inv_cdf(1 - design_pfa)
    fixed_h0_decisions = [
        tuple(ratio * value > gamma for value in h0) for ratio in noise_ratios
    ]
    fixed_h1_decisions = [
        tuple(amplitude + ratio * value > gamma for value in h1_noise)
        for ratio in noise_ratios
    ]
    pfa = [sum(case) / trials for case in fixed_h0_decisions]
    pd = [sum(case) / trials for case in fixed_h1_decisions]
    analytic_pfa = [q_function(gamma / ratio) for ratio in noise_ratios]
    analytic_pd = [q_function((gamma - amplitude) / ratio) for ratio in noise_ratios]
    clutter_pfa = [
        sum(pedestal + value > gamma for value in h0) / trials
        for pedestal in clutter_ratios
    ]
    clutter_pd = [
        sum(pedestal + amplitude + value > gamma for value in h1_noise) / trials
        for pedestal in clutter_ratios
    ]
    analytic_clutter_pfa = [
        q_function(gamma - pedestal) for pedestal in clutter_ratios
    ]
    analytic_clutter_pd = [
        q_function(gamma - pedestal - amplitude) for pedestal in clutter_ratios
    ]
    adaptive = [
        sum((ratio * value) / ratio > gamma for value in h0) / trials
        for ratio in noise_ratios
    ]
    recovered = [
        tuple(ratio * value > gamma for value in h0) for ratio in noise_ratios
    ]
    return {
        "gamma": gamma,
        "noise_ratios": noise_ratios,
        "pfa": pfa,
        "pd": pd,
        "analytic_pfa": analytic_pfa,
        "analytic_pd": analytic_pd,
        "clutter_pfa": clutter_pfa,
        "clutter_pd": clutter_pd,
        "analytic_clutter_pfa": analytic_clutter_pfa,
        "analytic_clutter_pd": analytic_clutter_pd,
        "adaptive": adaptive,
        "fixed_h0_decisions": fixed_h0_decisions,
        "recovered": recovered,
    }


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", re.sub(r"\.\.\.\s*", "", source))
    required = (
        "random_seed = 4301",
        "RandStream('mt19937ar', 'Seed', random_seed)",
        "clearvars;",
        "close(findall(0, 'Type', 'figure', 'Tag', 'P43'))",
        "design_false_alarm_probability = 0.01",
        "fixed_threshold_amplitude = reference_noise_rms*normalized_threshold",
        "standard_noise_h0 = randn(private_stream, trial_count, 1)",
        "standard_noise_h1 = randn(private_stream, trial_count, 1)",
        "baseline_false_alarm_decisions = baseline_h0 > fixed_threshold_amplitude",
        "baseline_detection_decisions = baseline_h1 > fixed_threshold_amplitude",
        "noise_rms_ratios = [0.75 1.00 1.25 1.50 2.00]",
        "clutter_pedestal_ratios = [0 0.5 1.0 1.5 2.0]",
        "case_h0 = case_sigma*standard_noise_h0",
        "case_h1 = target_amplitude+case_sigma*standard_noise_h1",
        "case_h0 > fixed_threshold_amplitude",
        "all(diff(noise_false_alarm_counts) > 0)",
        "all(diff(noise_detection_counts) < 0)",
        "fixed_threshold_amplitude/(sqrt(2)*case_sigma)",
        "clutter_h0 = case_pedestal+reference_noise_rms*standard_noise_h0",
        "clutter_h1 = case_pedestal+target_amplitude+reference_noise_rms*standard_noise_h1",
        "fixed_threshold_amplitude-case_pedestal",
        "normalized_h0 = (case_sigma*standard_noise_h0)/case_sigma",
        "broken_fixed_threshold_claim = false",
        "recovered_h0 > fixed_threshold_amplitude",
        "recovery_exact = recovery_exact && isequal(recovered_decisions_h0, fixed_noise_decisions_h0(:, case_index))",
        "assert(max_range_cells == 512 && max_trials == 25000",
        "estimated_stored_numeric_values = 20*trial_count+trial_count*numel(noise_rms_ratios)",
        "max_stored_numeric_values == 800000",
        "results.noise_false_alarm_counts",
        "results.noise_miss_counts",
        "results.clutter_false_alarm_counts",
        "results.broken_fixed_threshold_claim",
        "results.recovery_exact",
    )
    errors = [marker for marker in required if marker not in compact]
    if compact.count("fixed_threshold_amplitude-case_pedestal") != 2:
        errors.append("both clutter Gaussian-tail equations")
    return errors


class P43ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.docs = {
            name: (MODULE / name).read_text(encoding="utf-8")
            for name in ARTIFACTS
            if name != "experiment.m"
        }

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self):
        self.assertEqual(validate_p43_contract(MODULE, self.manifest), [])
        entries = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(entries["P42"]["status"], "implemented")
        self.assertEqual(entries["P43"], EXPECTED_IDENTITY)
        for name in ARTIFACTS:
            data = (MODULE / name).read_bytes()
            self.assertTrue(data.endswith(b"\n"), name)
            self.assertFalse(data.endswith(b"\n\n"), name)
            self.assertNotIn(b"\r", data, name)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "module"
            shutil.copytree(MODULE, fixture)
            (fixture / "checks.md").unlink()
            self.assertIn("P43 missing checks.md", validate_p43_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("", encoding="utf-8")
            self.assertIn("P43 empty checks.md", validate_p43_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p43_contract(MODULE, []))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p43_contract(MODULE, {"modules": [None]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn(
            "expected one P43 manifest entry, found 2",
            validate_p43_contract(MODULE, duplicate),
        )
        for key in EXPECTED_IDENTITY:
            drifted = copy.deepcopy(self.manifest)
            next(item for item in drifted["modules"] if item["id"] == "P43")[key] = "drift"
            errors = validate_p43_contract(MODULE, drifted)
            if key == "id":
                self.assertTrue(any("one P43 manifest entry" in error for error in errors))
            else:
                self.assertTrue(any(key in error for error in errors), key)

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self):
        validate_controls()
        invalid = (
            {"cells": True},
            {"cells": 63},
            {"cells": 513},
            {"targets": (48,)},
            {"targets": (48, 48)},
            {"targets": (48, 513)},
            {"targets": (48, False)},
            {"trials": 9999},
            {"trials": 25001},
            {"design_pfa": math.nan},
            {"design_pfa": 0},
            {"design_pfa": 0.5},
            {"noise_ratios": (0.75, 1.25, 2.0)},
            {"noise_ratios": (0.75, 1.0, math.inf)},
            {"noise_ratios": (0.75, 1.0, 1.0)},
            {"clutter_ratios": (0.5, 1.0, 1.5)},
            {"clutter_ratios": (0.0, 1.0, -1.0)},
            {"clutter_ratios": tuple(float(x) for x in range(10))},
            {"max_stored_values": 500_000},
        )
        for controls in invalid:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_independent_gaussian_oracle_matches_baseline_and_noise_sweep(self):
        controls = matlab_controls(self.source)
        result = detector_oracle(
            trials=controls["trials"],
            design_pfa=controls["design_pfa"],
            amplitude=controls["amplitude"],
            noise_ratios=controls["noise_ratios"],
            clutter_ratios=controls["clutter_ratios"],
        )
        self.assertAlmostEqual(result["gamma"], 2.326347874, places=8)
        pfa = result["pfa"]
        pd = result["pd"]
        self.assertTrue(all(right > left for left, right in zip(pfa, pfa[1:])))
        self.assertTrue(all(right < left for left, right in zip(pd, pd[1:])))
        tolerance = controls["probability_tolerance"]
        self.assertEqual(tolerance, 0.01)
        self.assertLess(max(abs(a - b) for a, b in zip(pfa, result["analytic_pfa"])), tolerance)
        self.assertLess(max(abs(a - b) for a, b in zip(pd, result["analytic_pd"])), tolerance)
        reference = result["noise_ratios"].index(1.0)
        self.assertLess(abs(pfa[reference] - controls["design_pfa"]), tolerance)

    def test_clutter_shift_failure_hidden_adaptation_and_exact_recovery(self):
        controls = matlab_controls(self.source)
        result = detector_oracle(
            trials=controls["trials"],
            design_pfa=controls["design_pfa"],
            amplitude=controls["amplitude"],
            noise_ratios=controls["noise_ratios"],
            clutter_ratios=controls["clutter_ratios"],
        )
        clutter_pfa = result["clutter_pfa"]
        clutter_pd = result["clutter_pd"]
        self.assertTrue(all(right > left for left, right in zip(clutter_pfa, clutter_pfa[1:])))
        self.assertTrue(all(right >= left for left, right in zip(clutter_pd, clutter_pd[1:])))
        self.assertLess(max(result["adaptive"]) - min(result["adaptive"]), 1e-15)
        self.assertEqual(result["recovered"], result["fixed_h0_decisions"])

    def test_common_clutter_shift_behavior_is_bound_to_both_hypotheses(self):
        controls = matlab_controls(self.source)
        result = detector_oracle(
            trials=controls["trials"],
            design_pfa=controls["design_pfa"],
            amplitude=controls["amplitude"],
            noise_ratios=controls["noise_ratios"],
            clutter_ratios=controls["clutter_ratios"],
        )
        tolerance = controls["probability_tolerance"]
        self.assertLess(
            max(
                abs(empirical - analytic)
                for empirical, analytic in zip(
                    result["clutter_pfa"], result["analytic_clutter_pfa"]
                )
            ),
            tolerance,
        )
        self.assertLess(
            max(
                abs(empirical - analytic)
                for empirical, analytic in zip(
                    result["clutter_pd"], result["analytic_clutter_pd"]
                )
            ),
            tolerance,
        )
        self.assertGreater(result["clutter_pd"][-1], result["clutter_pd"][0])
        omitted_h1_shift = self.source.replace(
            "clutter_h1 = case_pedestal+target_amplitude+...\n"
            "        reference_noise_rms*standard_noise_h1",
            "clutter_h1 = target_amplitude+reference_noise_rms*standard_noise_h1",
            1,
        )
        self.assertNotEqual(omitted_h1_shift, self.source)
        self.assertTrue(source_contract_errors(omitted_h1_shift))

    def test_probability_bookkeeping_and_one_sided_model_are_source_bound(self):
        self.assertEqual(self.source.count("randn(private_stream"), 3)
        self.assertIn("baseline_false_alarm_count = sum(baseline_false_alarm_decisions)", self.source)
        self.assertIn("baseline_detection_count = sum(baseline_detection_decisions)", self.source)
        self.assertIn("baseline_miss_count = trial_count-baseline_detection_count", self.source)
        self.assertIn("0.5*erfc(fixed_threshold_amplitude/", self.source)
        self.assertNotIn("abs(baseline_h0)", self.source)
        self.assertNotIn("abs(case_h0)", self.source)
        self.assertNotIn("baseline_detection_decisions = baseline_h0", self.source)

    def test_source_contract_markers_mutations_and_base_matlab_compatibility(self):
        self.assertEqual(source_contract_errors(self.source), [])
        self.assertEqual(self.source.count("figure('Name'"), 5)
        banned = (
            "phased.",
            "dsp.",
            "norminv(",
            "awgn(",
            "cfar",
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
        lowered_source = self.source.lower()
        for marker in banned:
            self.assertNotIn(marker, lowered_source)
        mutations = (
            self.source.replace("case_h0 > fixed_threshold_amplitude", "case_h0 > case_sigma*normalized_threshold", 1),
            self.source.replace("broken_fixed_threshold_claim = false", "broken_fixed_threshold_claim = true", 1),
            self.source.replace("standard_noise_h1 = randn(private_stream", "standard_noise_h1 = standard_noise_h0; %", 1),
            self.source.replace("fixed_threshold_amplitude/(sqrt(2)*case_sigma)", "case_sigma/(sqrt(2)*fixed_threshold_amplitude)", 1),
            self.source.replace("fixed_threshold_amplitude-case_pedestal", "fixed_threshold_amplitude+case_pedestal", 1),
            self.source.replace("clutter_h1 = case_pedestal+target_amplitude", "clutter_h1 = target_amplitude", 1),
            self.source.replace("max_stored_numeric_values == 800000", "max_stored_numeric_values > 0", 1),
        )
        for mutated in mutations:
            self.assertTrue(source_contract_errors(mutated))

    def _fixture(self) -> Path:
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
        shutil.copy2(ROOT / "curriculum/modules.json", fixture / "curriculum/modules.json")
        return fixture

    def test_isolated_learn_start_43_has_timeout_and_preserves_repository_state(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        fixture = self._fixture()
        result = subprocess.run(
            [str(fixture / "bin/learn"), "start", "43"],
            cwd=fixture,
            text=True,
            capture_output=True,
            env=os.environ.copy(),
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("P43 — Use a Fixed Detection Threshold", result.stdout)
        self.assertIn("status: implemented", result.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_docs_cover_sweeps_failure_recovery_cancellation_and_teach_back(self):
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
            "rollback",
        ):
            self.assertIn(marker, walkthrough)
        combined = "\n".join(self.docs.values()).lower()
        for marker in (
            "p42",
            "target-absent",
            "target-present",
            "one-sided",
            "amplitude units",
            "private seed",
            "base matlab",
            "bounded",
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

    def test_controls_precede_random_work_and_resources_are_bounded(self):
        validation = self.source.index("%% Reject malformed")
        stream = self.source.index("private_stream = RandStream")
        first_figure = self.source.index("figure('Name'")
        self.assertLess(validation, stream)
        self.assertLess(stream, first_figure)
        self.assertIn("estimated_stored_numeric_values <= max_stored_numeric_values", self.source)
        validate_controls(
            cells=512,
            targets=(1, 64, 128, 192, 256, 320, 384, 512),
            trials=25_000,
            noise_ratios=(0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0),
            clutter_ratios=(0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0),
        )
        self.assertNotIn("\nwhile ", self.source)
        self.assertEqual(self.source.count("for case_index = 1:"), 4)

    def test_p43_only_rollback_preserves_neighbor_identity(self):
        rolled = copy.deepcopy(self.manifest)
        neighbors_before = {
            item["id"]: copy.deepcopy(item)
            for item in rolled["modules"]
            if item["id"] in {"P42", "P44"}
        }
        next(item for item in rolled["modules"] if item["id"] == "P43")["status"] = "scaffolded"
        neighbors_after = {
            item["id"]: item
            for item in rolled["modules"]
            if item["id"] in {"P42", "P44"}
        }
        self.assertEqual(neighbors_after, neighbors_before)
        self.assertTrue(any("status" in error for error in validate_p43_contract(MODULE, rolled)))

    def test_public_catalogs_describe_p43_without_freezing_future_state(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 43 begins Phase 5", readme)
        self.assertIn("Project 43 follows P42", start_here)
        self.assertRegex(module_index, r"\| \[P43\].*\| implemented \| 5 \|")

    def test_retained_evidence_has_required_claim_boundary_and_commands(self):
        evidence = ROOT / "docs/evidence/P43-2026-08-03.md"
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
