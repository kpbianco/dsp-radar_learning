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
MODULE = ROOT / "modules/48-compare-go-cfar-and-so-cfar-at-a-clutter-edge"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Which side of a changing background should control the threshold?"
EXPECTED_IDENTITY = {
    "number": 48,
    "id": "P48",
    "title": "Compare GO-CFAR and SO-CFAR at a Clutter Edge",
    "guiding_question": QUESTION,
    "phase": 5,
    "phase_title": "Detection and CFAR",
    "slug": "compare-go-cfar-and-so-cfar-at-a-clutter-edge",
    "folder": "modules/48-compare-go-cfar-and-so-cfar-at-a-clutter-edge",
    "status": "implemented",
    "implementation_batch": "P48",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p48_contract(path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        artifact = path / name
        if not artifact.is_file():
            errors.append(f"P48 missing {name}")
        elif not artifact.read_text(encoding="utf-8").strip():
            errors.append(f"P48 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P48"]
    if len(matches) != 1:
        return errors + [f"expected one P48 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P48 {key} must be {expected!r}")
    return errors


def canonical_controls() -> dict[str, object]:
    return {
        "seed": 4801,
        "cells": 240,
        "edge": 121,
        "low_mean": 1.0,
        "step_db": 12.0,
        "training": 12,
        "guards": 2,
        "pfa": 1e-3,
        "target_cells": (70, 116, 126, 174),
        "target_power_db": (16.0, 13.0, 13.0, 16.0),
        "contrast_sweep": (0.0, 6.0, 12.0, 18.0),
        "interferer_sweep": (-20.0, 0.0, 10.0, 20.0),
        "weak_snr_db": 13.0,
        "trials": 25_000,
        "iterations": 80,
        "max_cells": 320,
        "max_training": 24,
        "max_guards": 8,
        "max_targets": 8,
        "max_sweep_cases": 6,
        "max_trials": 30_000,
        "max_iterations": 100,
        "max_random": 1_000_000,
        "max_stored": 1_500_000,
        "max_figures": 5,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    integer_names = (
        "seed", "cells", "edge", "training", "guards", "trials", "iterations",
        "max_cells", "max_training", "max_guards", "max_targets",
        "max_sweep_cases", "max_trials", "max_iterations", "max_random",
        "max_stored", "max_figures",
    )
    if any(
        not isinstance(controls[name], int) or isinstance(controls[name], bool)
        for name in integer_names
    ):
        raise ValueError("integer controls must be integers")
    for name in ("low_mean", "step_db", "pfa", "weak_snr_db"):
        if not finite_real(controls[name]):
            raise ValueError(f"{name} must be finite and real")
    if controls["seed"] != 4801 or not 80 <= controls["cells"] <= controls["max_cells"]:
        raise ValueError("deterministic scene changed or cells out of bounds")
    if not 2 <= controls["training"] <= controls["max_training"]:
        raise ValueError("training outside bounds")
    if not 0 <= controls["guards"] <= controls["max_guards"]:
        raise ValueError("guards outside bounds")
    half_width = controls["training"] + controls["guards"]
    if not half_width < controls["edge"] <= controls["cells"] - half_width:
        raise ValueError("edge does not support full stencil")
    if controls["low_mean"] <= 0 or not 0 <= controls["step_db"] <= 24:
        raise ValueError("background outside bounds")
    if not 0 < controls["pfa"] < 0.1:
        raise ValueError("Pfa outside bounds")
    if not 1000 <= controls["trials"] <= controls["max_trials"]:
        raise ValueError("trials outside bounds")
    if not 40 <= controls["iterations"] <= controls["max_iterations"]:
        raise ValueError("iterations outside bounds")

    target_cells = controls["target_cells"]
    target_power = controls["target_power_db"]
    if not isinstance(target_cells, (tuple, list)) or not target_cells:
        raise ValueError("target cells malformed")
    if len(target_cells) > controls["max_targets"] or len(set(target_cells)) != len(target_cells):
        raise ValueError("target cells duplicate or unbounded")
    if not all(
        isinstance(value, int) and not isinstance(value, bool)
        and half_width < value <= controls["cells"] - half_width
        for value in target_cells
    ):
        raise ValueError("target cells outside valid CUT region")
    if not isinstance(target_power, (tuple, list)) or len(target_power) != len(target_cells):
        raise ValueError("target powers do not match targets")
    if not all(finite_real(value) for value in target_power):
        raise ValueError("target powers must be finite")

    for name, lower, upper, must_include in (
        ("contrast_sweep", 0.0, 24.0, controls["step_db"]),
        ("interferer_sweep", -30.0, 30.0, None),
    ):
        values = controls[name]
        if not isinstance(values, (tuple, list)) or not 3 <= len(values) <= controls["max_sweep_cases"]:
            raise ValueError(f"{name} case count outside bounds")
        if not all(finite_real(value) for value in values):
            raise ValueError(f"{name} must be finite and real")
        if any(b <= a for a, b in zip(values, values[1:])):
            raise ValueError(f"{name} must increase")
        if values[0] < lower or values[-1] > upper:
            raise ValueError(f"{name} outside bounds")
        if must_include is not None and must_include not in values:
            raise ValueError(f"{name} omits baseline")

    ceilings = {
        "max_cells": 320,
        "max_training": 24,
        "max_guards": 8,
        "max_targets": 8,
        "max_sweep_cases": 6,
        "max_trials": 30_000,
        "max_iterations": 100,
        "max_random": 1_000_000,
        "max_stored": 1_500_000,
        "max_figures": 5,
    }
    if any(controls[name] != expected for name, expected in ceilings.items()):
        raise ValueError("reviewed ceilings must remain fixed")
    generated = controls["cells"] + controls["trials"] * (2 * controls["training"] + 3)
    stored = controls["trials"] * (2 * controls["training"] + 8) + 20 * controls["cells"]
    if generated > controls["max_random"] or stored > controls["max_stored"]:
        raise ValueError("resource estimate exceeds ceiling")


def variant_pfa(alpha: float, training: int, variant: str) -> float:
    if not finite_real(alpha) or alpha < 0:
        raise ValueError("alpha must be finite and nonnegative")
    if not isinstance(training, int) or isinstance(training, bool) or training < 1:
        raise ValueError("training must be a positive integer")
    if variant not in {"GO", "SO"}:
        raise ValueError("unknown variant")
    term_sum = sum(
        math.exp(
            (training + order) * math.log(training)
            + math.lgamma(training + order)
            - math.lgamma(training)
            - math.lgamma(order + 1)
            - (training + order) * math.log(2 * training + alpha)
        )
        for order in range(training)
    )
    so_pfa = 2 * term_sum
    if variant == "SO":
        return so_pfa
    return 2 * (training / (training + alpha)) ** training - so_pfa


def calibrated_scale(training: int, pfa: float, variant: str, iterations: int = 100) -> float:
    if not finite_real(pfa) or not 0 < pfa < 1:
        raise ValueError("Pfa outside bounds")
    lower, upper = 0.0, 1.0
    for _ in range(32):
        if variant_pfa(upper, training, variant) <= pfa:
            break
        upper *= 2
    else:
        raise ValueError("calibration did not bracket")
    for _ in range(iterations):
        middle = 0.5 * (lower + upper)
        if variant_pfa(middle, training, variant) > pfa:
            lower = middle
        else:
            upper = middle
    return 0.5 * (lower + upper)


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", source.replace("...", ""))
    required = (
        "random_seed = 4801;",
        "clutter_edge_cell = 121;",
        "training_cells_per_side = 12;",
        "guard_cells_per_side = 2;",
        "clutter_contrast_sweep_db = [0 6 12 18];",
        "interferer_excess_power_sweep_db = [-20 0 10 20];",
        "sweep_trial_count = 25000;",
        "calibration_iteration_count = 80;",
        "if max_range_cells ~= 320 || max_training_cells_per_side ~= 24 || max_guard_cells_per_side ~= 8 || max_targets ~= 8 || max_sweep_cases ~= 6 || max_sweep_trials ~= 30000 || max_calibration_iterations ~= 100 || max_generated_random_values ~= 1000000 || max_stored_numeric_values ~= 1500000 || max_figures ~= 5",
        "private_stream = RandStream('mt19937ar', 'Seed', random_seed);",
        "background_power = -background_mean_power.*log(uniform_power_draw);",
        "baseline_reference_power = background_power;",
        "go_background_estimate = max(leading_mean_power(cut), lagging_mean_power(cut));",
        "so_background_estimate = min(leading_mean_power(cut), lagging_mean_power(cut));",
        "go_threshold_power(cut) = go_scale_factor*go_background_estimate;",
        "so_threshold_power(cut) = so_scale_factor*so_background_estimate;",
        "broken_shared_scale_factor = total_training_cell_count*( design_false_alarm_probability^(-1/total_training_cell_count)-1);",
        "broken_shared_claim_is_valid = false;",
        "broken_claim_is_valid = false;",
        "results.recovery_reduces_edge_false_alarms = recovery_reduces_edge_false_alarms;",
    )
    return [marker for marker in required if marker not in compact]


@functools.lru_cache(maxsize=1)
def independent_behavior_oracle() -> dict[str, object]:
    generator = random.Random(4801)
    trials = 30_000
    training = 12
    go_alpha = calibrated_scale(training, 1e-3, "GO")
    so_alpha = calibrated_scale(training, 1e-3, "SO")
    left = [
        [generator.expovariate(1.0) for _ in range(training)]
        for _ in range(trials)
    ]
    right = [
        [generator.expovariate(1.0) for _ in range(training)]
        for _ in range(trials)
    ]
    cut_h0 = [generator.expovariate(1.0) for _ in range(trials)]
    left_means = [sum(row) / training for row in left]
    right_means = [sum(row) / training for row in right]

    edge_pfa: dict[float, tuple[float, float]] = {}
    for contrast_db in (0.0, 6.0, 12.0, 18.0):
        contrast = 10 ** (contrast_db / 10)
        go_false = so_false = 0
        for left_mean, right_mean, cut in zip(left_means, right_means, cut_h0):
            high_mean = contrast * right_mean
            high_cut = contrast * cut
            go_false += high_cut > go_alpha * max(left_mean, high_mean)
            so_false += high_cut > so_alpha * min(left_mean, high_mean)
        edge_pfa[contrast_db] = (go_false / trials, so_false / trials)

    cut_noise = [
        complex(
            generator.gauss(0.0, 1 / math.sqrt(2)),
            generator.gauss(0.0, 1 / math.sqrt(2)),
        )
        for _ in range(trials)
    ]
    cut_h1 = [abs(noise + math.sqrt(10 ** 1.3)) ** 2 for noise in cut_noise]
    interferer_pd: dict[float, tuple[float, float]] = {}
    for interferer_db in (-20.0, 0.0, 10.0, 20.0):
        extra_mean = 10 ** (interferer_db / 10) / training
        go_detect = so_detect = 0
        for left_mean, right_mean, cut in zip(left_means, right_means, cut_h1):
            contaminated = left_mean + extra_mean
            go_detect += cut > go_alpha * max(contaminated, right_mean)
            so_detect += cut > so_alpha * min(contaminated, right_mean)
        interferer_pd[interferer_db] = (go_detect / trials, so_detect / trials)

    low_side_target_pd: dict[float, tuple[float, float]] = {}
    for contrast_db in (0.0, 6.0, 12.0, 18.0):
        contrast = 10 ** (contrast_db / 10)
        go_detect = so_detect = 0
        for left_mean, right_mean, cut in zip(left_means, right_means, cut_h1):
            bright_side_mean = contrast * right_mean
            go_detect += cut > go_alpha * max(left_mean, bright_side_mean)
            so_detect += cut > so_alpha * min(left_mean, bright_side_mean)
        low_side_target_pd[contrast_db] = (go_detect / trials, so_detect / trials)
    return {
        "edge_pfa": edge_pfa,
        "interferer_pd": interferer_pd,
        "low_side_target_pd": low_side_target_pd,
    }


class P48ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text())
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self):
        self.assertEqual(validate_p48_contract(MODULE, self.manifest), [])
        p47 = next(item for item in self.manifest["modules"] if item["id"] == "P47")
        self.assertEqual(p47["status"], "implemented")
        for name in ARTIFACTS:
            with self.subTest(artifact=name):
                data = (MODULE / name).read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))
                self.assertNotIn(b"\r", data)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            for name in ARTIFACTS:
                shutil.copy2(MODULE / name, fixture / name)
            (fixture / "checks.md").unlink()
            self.assertIn("P48 missing checks.md", validate_p48_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("\n", encoding="utf-8")
            self.assertIn("P48 empty checks.md", validate_p48_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p48_contract(MODULE, {}))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p48_contract(MODULE, {"modules": ["P48"]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P48 manifest entry, found 2", validate_p48_contract(MODULE, duplicate))
        for key, expected in EXPECTED_IDENTITY.items():
            drifted = copy.deepcopy(self.manifest)
            next(item for item in drifted["modules"] if item["id"] == "P48")[key] = f"wrong-{expected}"
            self.assertTrue(validate_p48_contract(MODULE, drifted))

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self):
        validate_controls()
        invalid = (
            {"unexpected": 1},
            {"seed": True},
            {"seed": 4802},
            {"cells": 321},
            {"edge": 10},
            {"low_mean": math.nan},
            {"low_mean": 0.0},
            {"step_db": 25.0},
            {"training": 2.5},
            {"training": 25},
            {"guards": -1},
            {"pfa": 0.0},
            {"target_cells": (70, 70)},
            {"target_cells": (2, 116)},
            {"target_power_db": (16.0,)},
            {"target_power_db": (16.0, 13.0, math.inf, 16.0)},
            {"contrast_sweep": (0.0, 12.0, 6.0)},
            {"contrast_sweep": (0.0, 6.0, 18.0)},
            {"interferer_sweep": (-20.0, math.nan, 20.0)},
            {"interferer_sweep": (-20.0, 0.0, 31.0)},
            {"trials": 30_001},
            {"iterations": 39},
            {"max_random": 2_000_000},
            {"max_stored": 100},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                validate_controls(**overrides)

    def test_source_is_seeded_transparent_bounded_and_mutation_sensitive(self):
        self.assertEqual(source_contract_errors(self.source), [])
        controls_end = self.source.index("%% Calibrate GO and SO independently")
        first_allocation = self.source.index("private_stream =")
        self.assertLess(controls_end, first_allocation)
        self.assertIn("estimated_generated_random_values", self.source[:controls_end])
        self.assertIn("estimated_stored_numeric_values", self.source[:controls_end])
        self.assertIn("islogical(control_value)", self.source[:controls_end])
        self.assertEqual(self.source.count("figure('Name'"), 5)
        self.assertNotRegex(
            self.source.lower(),
            r"\b(?:phased\.|cfardetector|exprnd\s*\(|awgn\s*\(|parfor\b|while\b|"
            r"fopen\s*\(|webread\s*\(|system\s*\(|timer\s*\(|rng\s*\()",
        )
        for marker in (
            "if max_range_cells ~= 320 || max_training_cells_per_side ~= 24 ||",
            "go_background_estimate = max(leading_mean_power(cut), lagging_mean_power(cut));",
            "so_background_estimate = min(leading_mean_power(cut), lagging_mean_power(cut));",
            "broken_shared_claim_is_valid = false;",
        ):
            mutated = self.source.replace(marker, "mutated", 1)
            self.assertTrue(source_contract_errors(mutated), marker)

    def test_exact_variant_calibration_and_broken_shared_scale(self):
        training = 12
        pfa = 1e-3
        go_alpha = calibrated_scale(training, pfa, "GO")
        so_alpha = calibrated_scale(training, pfa, "SO")
        ca_alpha = 2 * training * (pfa ** (-1 / (2 * training)) - 1)
        self.assertAlmostEqual(go_alpha, 7.089038451813456, places=12)
        self.assertAlmostEqual(so_alpha, 10.480855745946773, places=12)
        self.assertLess(go_alpha, ca_alpha)
        self.assertLess(ca_alpha, so_alpha)
        self.assertAlmostEqual(variant_pfa(go_alpha, training, "GO"), pfa, places=14)
        self.assertAlmostEqual(variant_pfa(so_alpha, training, "SO"), pfa, places=14)
        self.assertAlmostEqual(variant_pfa(ca_alpha, training, "GO"), 4.729226614182537e-4, places=14)
        self.assertAlmostEqual(variant_pfa(ca_alpha, training, "SO"), 3.8688671274318283e-3, places=14)
        for malformed in ((math.nan, 12, "GO"), (1.0, True, "GO"), (1.0, 12, "CA")):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                variant_pfa(*malformed)

    def test_independent_oracle_exposes_edge_and_interferer_tradeoff(self):
        oracle = independent_behavior_oracle()
        edge = oracle["edge_pfa"]
        self.assertLess(abs(edge[0.0][0] - 1e-3), 7e-4)
        self.assertLess(abs(edge[0.0][1] - 1e-3), 7e-4)
        self.assertLess(edge[18.0][0], 0.01)
        self.assertGreater(edge[18.0][1], 0.7)
        self.assertTrue(all(b[1] > a[1] for a, b in zip(edge.values(), list(edge.values())[1:])))
        interferer = oracle["interferer_pd"]
        self.assertGreater(interferer[-20.0][0], 0.75)
        self.assertGreater(interferer[-20.0][1], 0.75)
        self.assertLess(interferer[20.0][0], 0.1)
        self.assertGreater(interferer[20.0][1], 0.75)
        self.assertGreater(interferer[20.0][1] - interferer[20.0][0], 0.7)

    def test_low_side_target_behavior_exposes_go_masking_cost(self):
        target_pd = independent_behavior_oracle()["low_side_target_pd"]
        self.assertGreater(target_pd[0.0][0], 0.75)
        self.assertGreater(target_pd[0.0][1], 0.75)
        self.assertLess(target_pd[18.0][0], 0.1)
        self.assertGreater(target_pd[18.0][1], 0.75)
        self.assertGreater(target_pd[18.0][1] - target_pd[18.0][0], 0.7)

    def test_docs_cover_baseline_sweeps_failure_recovery_limits_and_teach_back(self):
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        combined = "\n".join((readme, lesson, walkthrough, checks))
        normalized = re.sub(r"\s+", " ", combined)
        for phrase in (
            QUESTION,
            "m_GO = max(m_left, m_right)",
            "m_SO = min(m_left, m_right)",
            "separate GO and SO calibration",
            "clutter contrast",
            "one side remains representative",
            "broken shared CA multiplier",
            "Recovery",
            "Ctrl+C",
            "Short teach-back rubric",
            "As `T` grows without bound",
            "both halves are contaminated",
            "P52",
        ):
            self.assertIn(phrase, normalized)
        self.assertNotRegex(combined, r"(?i)TODO|coming soon|placeholder")
        self.assertLess(lesson.index("Start with the physical edge"), lesson.index("Expose both one-sided estimates"))

    def _run_fixture_cli(self, manifest: dict, *args: str, initial_state=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        fixture_root = Path(temporary.name) / "repo"
        fixture_cli = fixture_root / "bin/learn"
        fixture_manifest = fixture_root / "curriculum/modules.json"
        fixture_cli.parent.mkdir(parents=True)
        fixture_manifest.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", fixture_cli)
        fixture_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        for module in manifest["modules"]:
            source_readme = ROOT / module["folder"] / "README.md"
            target_readme = fixture_root / module["folder"] / "README.md"
            target_readme.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_readme, target_readme)
        if initial_state is not None:
            state_path = fixture_root / ".learning/progress.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps(initial_state, indent=2) + "\n", encoding="utf-8")
        env = os.environ.copy()
        env["HOME"] = temporary.name
        process = subprocess.run(
            [str(fixture_cli), *args],
            cwd=fixture_root,
            text=True,
            capture_output=True,
            env=env,
            timeout=10,
            check=False,
        )
        state_path = fixture_root / ".learning/progress.json"
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
        return process, state

    def test_isolated_cli_timeout_cancellation_and_scaffold_rollback_compatibility(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        process, state = self._run_fixture_cli(self.manifest, "start", "48")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("P48 — Compare GO-CFAR and SO-CFAR at a Clutter Edge", process.stdout)
        self.assertIn("status: implemented", process.stdout)
        self.assertEqual(state["current"], "P48")
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

        rolled = copy.deepcopy(self.manifest)
        next(item for item in rolled["modules"] if item["id"] == "P48")["status"] = "scaffolded"
        rolled_process, _ = self._run_fixture_cli(rolled, "start", "48")
        self.assertEqual(rolled_process.returncode, 3)
        self.assertIn("awaits Portfolio batch P48", rolled_process.stdout)

    def test_default_tutor_entry_advances_from_completed_p47_without_state_loss(self):
        prior_completed = [f"P{number:02d}" for number in range(1, 48)]
        initial = {
            "schema_version": 1,
            "current": "P47",
            "completed": prior_completed,
            "notes": {"P47": "preserve this equal-Pfa teach-back"},
        }
        process, state = self._run_fixture_cli(self.manifest, "start", initial_state=initial)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("P48 — Compare GO-CFAR and SO-CFAR", process.stdout)
        self.assertEqual(state["current"], "P48")
        self.assertEqual(state["completed"], prior_completed)
        self.assertEqual(state["notes"], initial["notes"])

    def test_p48_only_rollback_preserves_neighbor_identity(self):
        rolled = copy.deepcopy(self.manifest)
        neighbors_before = {
            item["id"]: copy.deepcopy(item)
            for item in rolled["modules"]
            if item["id"] in {"P47", "P49"}
        }
        next(item for item in rolled["modules"] if item["id"] == "P48")["status"] = "scaffolded"
        neighbors_after = {
            item["id"]: item for item in rolled["modules"] if item["id"] in {"P47", "P49"}
        }
        self.assertEqual(neighbors_after, neighbors_before)
        self.assertTrue(any("status" in error for error in validate_p48_contract(MODULE, rolled)))

    def test_public_catalogs_describe_p48_without_freezing_future_state(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 48 forms separate leading", readme)
        self.assertIn("Project 48 follows P47", start_here)
        self.assertRegex(module_index, r"\| \[P48\].*\| implemented \| 5 \|")
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?i)P48\s+(?:is\s+)?(?:the\s+)?(?:latest|last|final)")
        self.assertNotRegex(source, r"(?i)P49[^\n]*remains? scaffolded")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self):
        evidence = ROOT / "docs/evidence/P48-2026-08-04.md"
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
            "python3 -m unittest tests.test_p48_module -v",
        ):
            self.assertIn(command, text)
        self.assertIn("MATLAB and Octave did not run", text)
        self.assertIn("allowed-path audit", text)
        self.assertIn("pre-existing", text)
        data = evidence.read_bytes()
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))
        self.assertNotIn(b"\r", data)


if __name__ == "__main__":
    unittest.main()
