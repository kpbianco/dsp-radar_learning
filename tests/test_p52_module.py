from __future__ import annotations

import copy
import functools
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
MODULE = ROOT / "modules/52-validate-cfar-pfa-by-monte-carlo"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Does the implemented detector actually achieve the requested false-alarm probability?"
EXPECTED_IDENTITY = {
    "number": 52,
    "id": "P52",
    "title": "Validate CFAR Pfa by Monte Carlo",
    "guiding_question": QUESTION,
    "phase": 5,
    "phase_title": "Detection and CFAR",
    "slug": "validate-cfar-pfa-by-monte-carlo",
    "folder": "modules/52-validate-cfar-pfa-by-monte-carlo",
    "status": "implemented",
    "implementation_batch": "P52",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def validate_p52_contract(module: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P52 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P52 empty {artifact}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P52"]
    if len(entries) != 1:
        return errors + [f"expected one P52 manifest entry, found {len(entries)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if entries[0].get(key) != expected:
            errors.append(f"P52 {key} mismatch")
    return errors


def canonical_controls() -> dict[str, object]:
    return {
        "seed": 5201,
        "trials": 200_000,
        "block_trials": 2_000,
        "pfa": 1e-3,
        "baseline_training": 24,
        "pfa_sweep": (1e-2, 3e-3, 1e-3),
        "training_sweep": (8, 16, 24, 32, 64),
        "correlation": 0.65,
        "texture_log_std": 0.90,
        "confidence_z": 1.96,
        "running_trials": (200, 500, 1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000, 200_000),
        "display_trials": 240,
        "probability_sigma": 5.0,
        "max_trials": 250_000,
        "max_block_trials": 5_000,
        "max_training": 64,
        "max_sweep_cases": 6,
        "max_running_cases": 12,
        "max_random_reals": 55_000_000,
        "max_stored_values": 1_000_000,
        "max_comparisons": 3_000_000,
        "max_figures": 5,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    integer_names = (
        "seed", "trials", "block_trials", "baseline_training", "display_trials",
        "max_trials", "max_block_trials", "max_training", "max_sweep_cases",
        "max_running_cases", "max_random_reals", "max_stored_values",
        "max_comparisons", "max_figures",
    )
    if not all(integer(controls[name]) for name in integer_names):
        raise ValueError("integer controls")
    for name in ("pfa", "correlation", "texture_log_std", "confidence_z", "probability_sigma"):
        if not finite_real(controls[name]):
            raise ValueError(f"{name} must be finite and real")

    fixed_ceilings = {
        "max_trials": 250_000,
        "max_block_trials": 5_000,
        "max_training": 64,
        "max_sweep_cases": 6,
        "max_running_cases": 12,
        "max_random_reals": 55_000_000,
        "max_stored_values": 1_000_000,
        "max_comparisons": 3_000_000,
        "max_figures": 5,
    }
    if any(controls[name] != value for name, value in fixed_ceilings.items()):
        raise ValueError("resource ceiling drift")
    if controls["seed"] != 5201 or not 10_000 <= controls["trials"] <= controls["max_trials"]:
        raise ValueError("determinism or trial count")
    if not 100 <= controls["block_trials"] <= controls["max_block_trials"]:
        raise ValueError("block size")
    if controls["trials"] % controls["block_trials"]:
        raise ValueError("block size must divide trials")
    if not 1e-5 <= controls["pfa"] < 0.1:
        raise ValueError("Pfa")
    if not 0 < controls["correlation"] < 1:
        raise ValueError("correlation")
    if not 0 < controls["texture_log_std"] <= 1.5:
        raise ValueError("texture")
    if not 1 <= controls["confidence_z"] <= 4 or not 3 <= controls["probability_sigma"] <= 8:
        raise ValueError("uncertainty")

    pfa_sweep = controls["pfa_sweep"]
    if not isinstance(pfa_sweep, (tuple, list)) or not 3 <= len(pfa_sweep) <= controls["max_sweep_cases"]:
        raise ValueError("Pfa sweep shape")
    if not all(finite_real(value) and 1e-5 <= value < 0.1 for value in pfa_sweep):
        raise ValueError("Pfa sweep values")
    if any(right >= left for left, right in zip(pfa_sweep, pfa_sweep[1:])):
        raise ValueError("Pfa sweep order")
    if controls["pfa"] not in pfa_sweep:
        raise ValueError("Pfa sweep baseline")

    training = controls["training_sweep"]
    if not isinstance(training, (tuple, list)) or not 3 <= len(training) <= controls["max_sweep_cases"]:
        raise ValueError("training sweep shape")
    if not all(integer(value) and 4 <= value <= controls["max_training"] for value in training):
        raise ValueError("training sweep values")
    if any(right <= left for left, right in zip(training, training[1:])):
        raise ValueError("training sweep order")
    if controls["baseline_training"] not in training:
        raise ValueError("training sweep baseline")

    running = controls["running_trials"]
    if not isinstance(running, (tuple, list)) or not 4 <= len(running) <= controls["max_running_cases"]:
        raise ValueError("running checkpoint shape")
    if not all(integer(value) for value in running) or running[0] < 100:
        raise ValueError("running checkpoint values")
    if any(right <= left for left, right in zip(running, running[1:])) or running[-1] != controls["trials"]:
        raise ValueError("running checkpoint order")
    if not 50 <= controls["display_trials"] <= controls["block_trials"]:
        raise ValueError("display trials")

    nmax = max(training)
    nbase = controls["baseline_training"]
    generated = (
        2 * controls["trials"] * (nmax + 1)
        + 2 * controls["trials"] * (nbase + 2)
        + 3 * controls["trials"] * (nbase + 1)
    )
    stored = controls["trials"] + controls["block_trials"] * (
        2 * (nmax + 1) + 5 * (nbase + 1)
    ) + 10_000
    comparisons = controls["trials"] * (len(pfa_sweep) + len(training) + 4)
    if generated > controls["max_random_reals"]:
        raise ValueError("random generation budget")
    if stored > controls["max_stored_values"]:
        raise ValueError("storage budget")
    if comparisons > controls["max_comparisons"]:
        raise ValueError("comparison budget")


def ca_alpha(training_count: int, pfa: float) -> float:
    if not integer(training_count) or training_count < 1:
        raise ValueError("training count")
    if not finite_real(pfa) or not 0 < pfa < 1:
        raise ValueError("Pfa")
    return training_count * (pfa ** (-1 / training_count) - 1)


def ca_pfa(alpha: float, training_count: int) -> float:
    if not finite_real(alpha) or alpha < 0:
        raise ValueError("alpha")
    if not integer(training_count) or training_count < 1:
        raise ValueError("training count")
    return (1 + alpha / training_count) ** (-training_count)


def wilson_interval(alarms: int, trials: int, z_score: float = 1.96) -> tuple[float, float]:
    if not integer(alarms) or not integer(trials) or trials < 1 or not 0 <= alarms <= trials:
        raise ValueError("alarm count")
    if not finite_real(z_score) or not 1 <= z_score <= 4:
        raise ValueError("z score")
    measured = alarms / trials
    denominator = 1 + z_score * z_score / trials
    center = (measured + z_score * z_score / (2 * trials)) / denominator
    half = z_score / denominator * math.sqrt(
        measured * (1 - measured) / trials + z_score * z_score / (4 * trials * trials)
    )
    return max(0.0, center - half), min(1.0, center + half)


@functools.lru_cache(maxsize=1)
def mismatch_oracle() -> tuple[float, float, float]:
    rng = random.Random(5201)
    trials = 20_000
    training_count = 24
    alpha = ca_alpha(training_count, 1e-3)
    rho = 0.65
    sigma = 0.90
    iid_alarms = 0
    correlated_alarms = 0
    textured_alarms = 0
    for _ in range(trials):
        iid_cut = rng.expovariate(1.0)
        iid_mean = sum(rng.expovariate(1.0) for _ in range(training_count)) / training_count
        iid_alarms += iid_cut > alpha * iid_mean

        common = complex(rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0)) / math.sqrt(2)
        correlated: list[float] = []
        for _ in range(training_count + 1):
            innovation = complex(rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0)) / math.sqrt(2)
            sample = math.sqrt(rho) * common + math.sqrt(1 - rho) * innovation
            correlated.append(abs(sample) ** 2)
        correlated_alarms += correlated[0] > alpha * sum(correlated[1:]) / training_count

        textured = [
            rng.expovariate(1.0) * math.exp(sigma * rng.gauss(0.0, 1.0) - 0.5 * sigma * sigma)
            for _ in range(training_count + 1)
        ]
        textured_alarms += textured[0] > alpha * sum(textured[1:]) / training_count
    return tuple(value / trials for value in (iid_alarms, correlated_alarms, textured_alarms))


def source_binding_errors(source: str) -> list[str]:
    required = (
        "random_seed = 5201;",
        "trial_count = 200000;",
        "design_false_alarm_probability = 1e-3;",
        "baseline_training_cell_count = 24;",
        "false_alarm_probability_sweep = [1e-2 3e-3 1e-3];",
        "training_cell_count_sweep = [8 16 24 32 64];",
        "correlation_coefficient = 0.65;",
        "texture_log_standard_deviation = 0.90;",
        "training_power_cumulative = cumsum(independent_power(:, 2:end), 2);",
        "cfar_scale_factor = training_cell_count*(...\n            design_false_alarm_probability^(-1/training_cell_count)-1);",
        "sum(cut_power > cfar_scale_factor*training_mean_power)",
        "unit_mean_texture = exp(texture_log_standard_deviation*...",
        "common_noise = (randn(private_stream",
        "broken_theoretical_pfa = (1+known_noise_scale_factor/...",
        "recovered_scale_factor = baseline_training_cell_count*(...",
        "results.pfa_wilson_lower = pfa_wilson_lower;",
        "results.model_measured_pfa = model_measured_pfa;",
        "clear running_alarm_count;",
        "is_reviewed_default_run = trial_count == 200000 && ...",
        "block_trial_count == 2000 && ...",
        "if is_reviewed_default_run",
        "confidence_level_percent = 100*erf(confidence_z_score/sqrt(2));",
        "results.confidence_level_percent = confidence_level_percent;",
        "~isrow(false_alarm_probability_sweep)",
        "~isrow(training_cell_count_sweep)",
        "~isreal(running_trial_counts) || ~isrow(running_trial_counts)",
    )
    return [marker for marker in required if marker not in source]


def run_fixture_cli(manifest: dict, *args: str, state: dict | None = None) -> tuple[subprocess.CompletedProcess[str], dict | None]:
    with tempfile.TemporaryDirectory() as temporary:
        fixture = Path(temporary) / "repo"
        cli = fixture / "bin/learn"
        manifest_path = fixture / "curriculum/modules.json"
        cli.parent.mkdir(parents=True)
        manifest_path.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", cli)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if state is not None:
            state_path = fixture / ".learning/progress.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        environment = os.environ.copy()
        environment["HOME"] = temporary
        completed = subprocess.run(
            [str(cli), *args],
            cwd=fixture,
            env=environment,
            text=True,
            capture_output=True,
            timeout=10,
        )
        captured = None
        state_path = fixture / ".learning/progress.json"
        if state_path.exists():
            captured = json.loads(state_path.read_text(encoding="utf-8"))
        return completed, captured


class P52ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self) -> None:
        self.assertEqual(validate_p52_contract(MODULE, self.manifest), [])
        entry = next(item for item in self.manifest["modules"] if item["id"] == "P52")
        predecessor = next(item for item in self.manifest["modules"] if item["id"] == "P51")
        self.assertEqual(predecessor["status"], "implemented")
        self.assertIn("P51 is the direct prerequisite", self.readme)
        self.assertIn(QUESTION, self.readme)
        for name in ARTIFACTS:
            data = (MODULE / name).read_bytes()
            self.assertTrue(data.endswith(b"\n"), name)
            self.assertFalse(data.endswith(b"\n\n"), name)
        self.assertEqual(entry, EXPECTED_IDENTITY)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "module"
            shutil.copytree(MODULE, fixture)
            (fixture / "experiment.m").unlink()
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p52_contract(fixture, self.manifest)
            self.assertIn("P52 missing experiment.m", errors)
            self.assertIn("P52 empty lesson.md", errors)
        for malformed in (None, {}, {"modules": {}}, {"modules": [None]}):
            self.assertTrue(validate_p52_contract(MODULE, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertTrue(validate_p52_contract(MODULE, duplicate))
        for key, expected in EXPECTED_IDENTITY.items():
            drifted = copy.deepcopy(self.manifest)
            entry = next(item for item in drifted["modules"] if item.get("id") == "P52")
            entry[key] = f"bad-{expected}"
            self.assertTrue(validate_p52_contract(MODULE, drifted), key)

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self) -> None:
        validate_controls()
        invalid = (
            {"unknown": 1}, {"seed": 5202}, {"trials": True}, {"trials": 9_999},
            {"trials": 250_001}, {"block_trials": 0}, {"block_trials": 3_000},
            {"pfa": float("nan")}, {"pfa": 0}, {"pfa": 0.1},
            {"pfa_sweep": (1e-3, 1e-2, 1e-4)}, {"pfa_sweep": (1e-2, 3e-3, 2e-3)},
            {"training_sweep": (8, 24, 16)}, {"training_sweep": (8, 16, 32)},
            {"training_sweep": (8, 16, 24, 32, 65)}, {"correlation": 0},
            {"correlation": 1}, {"texture_log_std": 0}, {"texture_log_std": 1.6},
            {"confidence_z": complex(1.96, 1)}, {"probability_sigma": 2},
            {"running_trials": (200, 1_000, 200_000, 100_000)},
            {"running_trials": (200, 1_000, 10_000)}, {"display_trials": 49},
            {"max_random_reals": 54_999_999}, {"max_stored_values": 999_999},
            {"max_comparisons": 2_999_999}, {"max_figures": 6},
        )
        for override in invalid:
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_controls(**override)

    def test_exact_finite_n_calibration_covers_both_sweeps_and_limits(self) -> None:
        for training_count in (8, 16, 24, 32, 64):
            alpha = ca_alpha(training_count, 1e-3)
            self.assertAlmostEqual(ca_pfa(alpha, training_count), 1e-3, places=14)
        for pfa in (1e-2, 3e-3, 1e-3):
            self.assertAlmostEqual(ca_pfa(ca_alpha(24, pfa), 24), pfa, places=14)
        self.assertGreater(ca_alpha(24, 1e-3), -math.log(1e-3))
        self.assertAlmostEqual(ca_alpha(1_000_000, 1e-3), -math.log(1e-3), places=4)
        for args in ((0, 1e-3), (24, 0), (24, float("nan")), (True, 1e-3)):
            with self.assertRaises(ValueError):
                ca_alpha(*args)
        for args in ((-1.0, 24), (1.0, 0), (float("inf"), 24)):
            with self.assertRaises(ValueError):
                ca_pfa(*args)

    def test_wilson_interval_handles_rare_zero_and_narrowing_cases(self) -> None:
        lower, upper = wilson_interval(0, 200_000)
        self.assertEqual(lower, 0)
        self.assertGreater(upper, 0)
        short = wilson_interval(1, 1_000)
        long = wilson_interval(200, 200_000)
        self.assertLess(long[1] - long[0], short[1] - short[0])
        self.assertLessEqual(long[0], 1e-3)
        self.assertGreaterEqual(long[1], 1e-3)
        for args in ((-1, 10), (11, 10), (0, 0), (1.5, 10), (1, 10, 0.5)):
            with self.assertRaises(ValueError):
                wilson_interval(*args)

    def test_editable_wilson_z_score_changes_width_and_reported_confidence(self) -> None:
        alarms = 200
        trials = 200_000
        one_sigma = wilson_interval(alarms, trials, 1.0)
        reviewed = wilson_interval(alarms, trials, 1.96)
        three_sigma = wilson_interval(alarms, trials, 3.0)
        widths = tuple(upper - lower for lower, upper in (one_sigma, reviewed, three_sigma))
        self.assertLess(widths[0], widths[1])
        self.assertLess(widths[1], widths[2])
        confidence_levels = tuple(100 * math.erf(z_score / math.sqrt(2)) for z_score in (1.0, 1.96, 3.0))
        self.assertAlmostEqual(confidence_levels[0], 68.2689, places=4)
        self.assertAlmostEqual(confidence_levels[1], 95.0004, places=4)
        self.assertAlmostEqual(confidence_levels[2], 99.7300, places=4)
        self.assertIn("confidence_interval_label", self.source)
        self.assertIn("fprintf('%s: [%.6g, %.6g]\\n', confidence_interval_label", self.source)

    def test_independent_oracle_exposes_correlation_and_heavy_tail_directions(self) -> None:
        iid, correlated, textured = mismatch_oracle()
        self.assertGreater(iid, 0)
        self.assertLess(abs(iid - 1e-3), 1.5e-3)
        self.assertLess(correlated, 0.6e-3)
        self.assertGreater(textured, 8e-3)
        self.assertLess(correlated, iid)
        self.assertGreater(textured, iid)

    def test_broken_infinite_training_scale_overspends_and_recovery_is_exact(self) -> None:
        pfa = 1e-3
        training_count = 24
        broken_alpha = -math.log(pfa)
        broken_pfa = ca_pfa(broken_alpha, training_count)
        recovered_alpha = ca_alpha(training_count, pfa)
        self.assertGreater(broken_pfa, 2 * pfa)
        self.assertLess(broken_alpha, recovered_alpha)
        self.assertAlmostEqual(ca_pfa(recovered_alpha, training_count), pfa, places=14)
        self.assertIn("known_noise_scale_factor = -log(design_false_alarm_probability);", self.source)
        self.assertIn("recovered_scale_factor = baseline_training_cell_count*(...", self.source)

    def test_source_is_seeded_transparent_bounded_and_mutation_sensitive(self) -> None:
        self.assertEqual(source_binding_errors(self.source), [])
        self.assertIn("RandStream('mt19937ar', 'Seed', random_seed)", self.source)
        self.assertNotRegex(self.source, r"(?<![A-Za-z])rng\s*\(")
        self.assertNotRegex(self.source, r"randn\((?!private_stream)")
        for banned in (
            "cfarDetector", "phased.CFAR", "fitdist(", "binofit(", "parfor",
            "fopen(", "webread(", "system(", "timer(", "tcpclient(",
        ):
            self.assertNotIn(banned, self.source)
        self.assertLess(
            self.source.index("%% Homogeneous baseline"),
            self.source.index("private_stream = RandStream"),
        )
        mutations = (
            self.source.replace(
                "training_cell_count*(...\n            design_false_alarm_probability^(-1/training_cell_count)-1)",
                "-log(design_false_alarm_probability)",
                1,
            ),
            self.source.replace("correlation_coefficient = 0.65;", "correlation_coefficient = 0.05;", 1),
            self.source.replace("texture_log_standard_deviation = 0.90;", "texture_log_standard_deviation = 0.10;", 1),
            self.source.replace("~isrow(training_cell_count_sweep) || ...", "false || ...", 1),
        )
        for mutated in mutations:
            self.assertTrue(source_binding_errors(mutated))

    def test_sweep_and_broken_case_markers_bind_visible_outputs_and_metrics(self) -> None:
        for marker in (
            "%% Figure 2: requested-Pfa sweep",
            "%% Figure 3: total training-count sweep",
            "%% Figure 4: noise-model sweep",
            "%% Figure 5: broken infinite-training multiplier",
            "Measured false-alarm probability (alarms / tested CUTs)",
            "Normalized square-law power",
            "confidence_interval_label",
            "results.pfa_alarm_counts",
            "results.training_alarm_counts",
            "results.model_alarm_counts",
            "results.broken_theoretical_pfa",
            "results.recovered_theoretical_pfa",
        ):
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P52"), 5)

    def test_docs_cover_model_limits_sweeps_failure_recovery_and_teach_back(self) -> None:
        combined = "\n".join((self.readme, self.lesson, self.walkthrough, self.checks))
        for term in (
            QUESTION, "P27", "P45", "P47", "P51", "Wilson", "numerator",
            "denominator", "independent", "correlated", "compound-lognormal",
            "heavy-tailed", "finite-`N`", "-log(Pfa)", "Recovery", "Ctrl+C",
            "timeout", "teach-back", "hardware", "operational",
        ):
            self.assertIn(term.lower(), combined.lower())
        self.assertIn("Sweep 1", self.walkthrough)
        self.assertIn("Sweep 2", self.walkthrough)
        self.assertIn("change only the noise model", self.walkthrough.lower())
        self.assertGreaterEqual(self.checks.count("Correct:"), 4)
        self.assertGreaterEqual(self.checks.count("Incorrect:"), 4)

    def test_no_placeholder_or_unexplained_black_box_regression(self) -> None:
        combined = "\n".join(
            (self.source, self.readme, self.lesson, self.walkthrough, self.checks)
        )
        self.assertNotRegex(combined, r"(?i)\bTODO\b|\bTBD\b|lorem ipsum|coming soon")
        self.assertNotRegex(combined, r"(?i)copy.+toolbox|use a CFAR object")
        self.assertGreater(len(self.source.splitlines()), 350)
        self.assertGreater(len(self.lesson.splitlines()), 100)

    def test_default_tutor_entry_advances_from_completed_p51_without_state_loss(self) -> None:
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        completed_ids = [f"P{number:02d}" for number in range(1, 52)]
        initial = {
            "schema_version": 1,
            "current": "P51",
            "completed": completed_ids,
            "notes": {"P51": "Explained detector disagreements from training contents."},
        }
        completed, captured = run_fixture_cli(self.manifest, "start", state=initial)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("P52 — Validate CFAR Pfa by Monte Carlo", completed.stdout)
        self.assertIn("status: implemented", completed.stdout)
        self.assertEqual(captured["completed"], completed_ids)
        self.assertEqual(captured["notes"], initial["notes"])
        self.assertEqual(captured["current"], "P52")
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_isolated_cli_timeout_cancellation_and_scaffold_rollback_compatibility(self) -> None:
        rollback = copy.deepcopy(self.manifest)
        p51_before = copy.deepcopy(next(item for item in rollback["modules"] if item["id"] == "P51"))
        p53_before = copy.deepcopy(next(item for item in rollback["modules"] if item["id"] == "P53"))
        next(item for item in rollback["modules"] if item["id"] == "P52")["status"] = "scaffolded"
        completed, captured = run_fixture_cli(rollback, "start", "52")
        self.assertEqual(completed.returncode, 3)
        self.assertIn("awaits Portfolio batch P52", completed.stdout)
        self.assertEqual(captured["current"], "P52")
        self.assertEqual(next(item for item in rollback["modules"] if item["id"] == "P51"), p51_before)
        self.assertEqual(next(item for item in rollback["modules"] if item["id"] == "P53"), p53_before)
        self.assertIn("Pressing Ctrl+C", self.walkthrough)
        self.assertIn("no file", self.walkthrough.lower())
        self.assertIn("fresh private stream", self.walkthrough)
        self.assertIn("linked bookkeeping controls", self.walkthrough)

    def test_public_catalogs_describe_p52_without_freezing_future_state(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 52 closes Phase 5", root_readme)
        self.assertIn("Project 52 follows P51", start_here)
        self.assertRegex(module_index, r"\| \[P52\].*\| implemented \| 5 \|")
        self.assertNotRegex(self.readme + self.lesson + self.walkthrough + self.checks, r"P5[3-9].*scaffolded")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self) -> None:
        evidence = ROOT / "docs/evidence/P52-2026-08-04.md"
        self.assertTrue(evidence.is_file())
        data = evidence.read_bytes()
        text = data.decode("utf-8")
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))
        for marker in (
            "Acceptance mapping", "Static validation", "MATLAB runtime",
            "Figure and metric inventory", "Exact commands and results",
            "Changed and preserved invariants", "Residual risks",
            "Rollback and recovery", "Unperformed validation",
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
        ):
            self.assertIn(marker, text)
        self.assertRegex(text, r"(?i)MATLAB and Octave did not run")


if __name__ == "__main__":
    unittest.main()
