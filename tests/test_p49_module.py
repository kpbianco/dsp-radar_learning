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
MODULE = ROOT / "modules/49-use-ordered-statistic-cfar-with-interfering-targets"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How can CFAR resist several contaminated training cells?"
EXPECTED_IDENTITY = {
    "number": 49,
    "id": "P49",
    "title": "Use Ordered-Statistic CFAR with Interfering Targets",
    "guiding_question": QUESTION,
    "phase": 5,
    "phase_title": "Detection and CFAR",
    "slug": "use-ordered-statistic-cfar-with-interfering-targets",
    "folder": "modules/49-use-ordered-statistic-cfar-with-interfering-targets",
    "status": "implemented",
    "implementation_batch": "P49",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p49_contract(module: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module / name
        if not path.is_file():
            errors.append(f"P49 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P49 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    modules = manifest["modules"]
    if any(not isinstance(item, dict) for item in modules):
        return errors + ["manifest module entries must be objects"]
    entries = [item for item in modules if item.get("id") == "P49"]
    if len(entries) != 1:
        return errors + [f"expected one P49 manifest entry, found {len(entries)}"]
    entry = entries[0]
    for key, expected in EXPECTED_IDENTITY.items():
        if entry.get(key) != expected:
            errors.append(f"P49 {key} must be {expected!r}")
    return errors


def validate_controls(**overrides: object) -> None:
    controls: dict[str, object] = {
        "seed": 4901,
        "cells": 256,
        "mean_power": 1.0,
        "training": 12,
        "guards": 2,
        "pfa": 1e-3,
        "primary": 128,
        "primary_snr_db": 15.0,
        "interferer_cells": (115, 120, 136, 141),
        "interferer_db": 20.0,
        "rank": 18,
        "count_sweep": (0, 2, 4, 6, 7, 8),
        "strength_sweep": (-20.0, 0.0, 10.0, 20.0, 30.0),
        "rank_sweep": (12, 16, 18, 20, 22, 24),
        "sweep_snr_db": 13.0,
        "trials": 20_000,
        "iterations": 80,
        "max_random": 600_000,
        "max_stored": 1_600_000,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    integer_names = ("seed", "cells", "training", "guards", "primary", "rank", "trials", "iterations")
    if any(
        not finite_real(controls[name]) or int(controls[name]) != controls[name]
        for name in integer_names
    ):
        raise ValueError("integer controls")
    if controls["seed"] != 4901 or not 80 <= controls["cells"] <= 320:
        raise ValueError("determinism or cells")
    if not 2 <= controls["training"] <= 24 or not 0 <= controls["guards"] <= 8:
        raise ValueError("stencil")
    total = 2 * int(controls["training"])
    half = int(controls["training"]) + int(controls["guards"])
    if not half < controls["primary"] <= controls["cells"] - half:
        raise ValueError("primary")
    for name in ("mean_power", "pfa", "primary_snr_db", "interferer_db", "sweep_snr_db"):
        if not finite_real(controls[name]):
            raise ValueError("real control")
    if not 1e-6 <= controls["mean_power"] <= 1e6 or not 1e-6 <= controls["pfa"] < 0.1:
        raise ValueError("power or Pfa")
    if any(not -30 <= controls[name] <= 40 for name in ("primary_snr_db", "interferer_db", "sweep_snr_db")):
        raise ValueError("target power bounds")
    if not 1 <= controls["rank"] <= total:
        raise ValueError("rank")
    interferers = controls["interferer_cells"]
    if (
        not isinstance(interferers, (tuple, list))
        or not interferers
        or len(set(interferers)) != len(interferers)
        or any(not finite_real(cell) or int(cell) != cell for cell in interferers)
        or controls["primary"] in interferers
    ):
        raise ValueError("interferer cells")
    left = range(int(controls["primary"] - controls["guards"] - controls["training"]), int(controls["primary"] - controls["guards"]))
    right = range(int(controls["primary"] + controls["guards"] + 1), int(controls["primary"] + controls["guards"] + controls["training"] + 1))
    if not set(interferers).issubset(set(left) | set(right)):
        raise ValueError("contamination geometry")
    count_sweep = controls["count_sweep"]
    rank_sweep = controls["rank_sweep"]
    strength_sweep = controls["strength_sweep"]
    if any(not isinstance(values, (tuple, list)) or not 3 <= len(values) <= 8 for values in (count_sweep, rank_sweep, strength_sweep)):
        raise ValueError("sweep shape")
    if (
        any(not finite_real(value) or int(value) != value for value in count_sweep)
        or count_sweep[0] != 0
        or 4 not in count_sweep
        or total - controls["rank"] + 1 not in count_sweep
        or any(a >= b for a, b in zip(count_sweep, count_sweep[1:]))
        or count_sweep[-1] > total
    ):
        raise ValueError("count sweep")
    if (
        any(not finite_real(value) or int(value) != value for value in rank_sweep)
        or controls["rank"] not in rank_sweep
        or 22 not in rank_sweep
        or any(a >= b for a, b in zip(rank_sweep, rank_sweep[1:]))
        or rank_sweep[0] < 1
        or rank_sweep[-1] > total
    ):
        raise ValueError("rank sweep")
    if (
        any(not finite_real(value) for value in strength_sweep)
        or controls["interferer_db"] not in strength_sweep
        or any(a >= b for a, b in zip(strength_sweep, strength_sweep[1:]))
        or strength_sweep[0] < -30
        or strength_sweep[-1] > 40
    ):
        raise ValueError("strength sweep")
    if not 1000 <= controls["trials"] <= 25_000 or not 40 <= controls["iterations"] <= 100:
        raise ValueError("work")
    if controls["max_random"] != 600_000 or controls["max_stored"] != 1_600_000:
        raise ValueError("ceiling lock")
    generated = int(controls["cells"] + controls["trials"] * (total + 2))
    stored = int(controls["trials"] * (3 * total + 5) + 20 * controls["cells"])
    if generated > controls["max_random"] or stored > controls["max_stored"]:
        raise ValueError("resource ceiling")


def os_pfa(alpha: float, training: int, rank: int) -> float:
    if not finite_real(alpha) or alpha < 0:
        raise ValueError("alpha")
    if not finite_real(training) or int(training) != training or training < 1:
        raise ValueError("training")
    if not finite_real(rank) or int(rank) != rank or not 1 <= rank <= training:
        raise ValueError("rank")
    return math.exp(
        sum(
            math.log(training - offset) - math.log(training - offset + alpha)
            for offset in range(int(rank))
        )
    )


def calibrated_os_scale(training: int, rank: int, pfa: float, iterations: int = 100) -> float:
    if not finite_real(pfa) or not 0 < pfa < 1:
        raise ValueError("Pfa")
    if not finite_real(iterations) or int(iterations) != iterations or iterations < 1:
        raise ValueError("iterations")
    lower, upper = 0.0, 1.0
    for _ in range(32):
        if os_pfa(upper, training, rank) <= pfa:
            break
        upper *= 2
    else:
        raise ValueError("calibration bracket")
    for _ in range(int(iterations)):
        middle = 0.5 * (lower + upper)
        if os_pfa(middle, training, rank) > pfa:
            lower = middle
        else:
            upper = middle
    return 0.5 * (lower + upper)


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", source.replace("...", ""))
    required = (
        "random_seed = 4901;",
        "range_cell_count = 256;",
        "training_cells_per_side = 12;",
        "guard_cells_per_side = 2;",
        "design_false_alarm_probability = 1e-3;",
        "primary_target_cell = 128;",
        "primary_target_snr_db = 15;",
        "interfering_target_cells = [115 120 136 141];",
        "interferer_excess_power_db = 20;",
        "os_rank = 18;",
        "interferer_count_sweep = [0 2 4 6 7 8];",
        "interferer_strength_sweep_db = [-20 0 10 20 30];",
        "rank_sweep = [12 16 18 20 22 24];",
        "sweep_target_snr_db = 13;",
        "sweep_trial_count = 20000;",
        "calibration_iteration_count = 80;",
        "if max_range_cells ~= 320 || max_training_cells_per_side ~= 24 || max_guard_cells_per_side ~= 8 || max_targets ~= 10 || max_sweep_cases ~= 8 || max_sweep_trials ~= 25000 || max_calibration_iterations ~= 100 || max_generated_random_values ~= 600000 || max_stored_numeric_values ~= 1600000 || max_figures ~= 5",
        "estimated_stored_numeric_values = sweep_trial_count*(3*total_training_cell_count+5) + 20*range_cell_count;",
        "private_stream = RandStream('mt19937ar', 'Seed', random_seed);",
        "ca_scale_factor = total_training_cell_count*( design_false_alarm_probability^(-1/total_training_cell_count)-1);",
        "os_scale_factor = calibrated_os_scale(total_training_cell_count, os_rank, design_false_alarm_probability, calibration_iteration_count);",
        "reference_power = received_power(reference_cells);",
        "sorted_reference_power = sort(reference_power, 'ascend');",
        "ca_background_estimate = sum(reference_power)/total_training_cell_count;",
        "os_background_statistic = sorted_reference_power(os_rank);",
        "os_threshold_power(cut) = os_scale_factor*os_background_statistic;",
        "outlier_capacity = total_training_cell_count-os_rank;",
        "target_cut_power = abs(unit_target_noise+sqrt(10^(sweep_target_snr_db/10))).^2;",
        "contaminated_reference_power(:, 1:interferer_count) = contaminated_reference_power(:, 1:interferer_count) + strong_interferer_power;",
        "contaminated_reference_power(:, 1:strength_sweep_interferer_count) = contaminated_reference_power(:, 1:strength_sweep_interferer_count) + contaminator_power;",
        "count_sweep_os_pd(count_index) = sum(target_cut_power > os_trial_threshold)/sweep_trial_count;",
        "strength_sweep_os_pd(strength_index) = sum(target_cut_power > os_trial_threshold)/sweep_trial_count;",
        "rank_sweep_os_pd(rank_index) = sum(target_cut_power > candidate_threshold)/sweep_trial_count;",
        "clear contaminated_reference_power sorted_contaminated_power ca_trial_threshold os_trial_threshold;",
        "log(training_count-spacing_index+alpha);",
        "broken_reused_scale_pfa(rank_index) = homogeneous_os_pfa( os_scale_factor, total_training_cell_count, candidate_rank);",
        "recovered_rank_pfa(rank_index) = homogeneous_os_pfa( rank_scale_factors(rank_index), total_training_cell_count, candidate_rank);",
        "broken_reused_scale_claim_is_valid = false;",
        "results.recovered_rank_specific_calibration = recovered_rank_specific_calibration;",
        "results.design_false_alarm_probability = design_false_alarm_probability;",
        "results.sweep_trial_count = sweep_trial_count;",
        "results.rank_outlier_capacity = total_training_cell_count-rank_sweep;",
    )
    return [marker for marker in required if marker not in compact]


@functools.lru_cache(maxsize=1)
def independent_behavior_oracle() -> dict[str, object]:
    generator = random.Random(4901)
    trials = 20_000
    training = 24
    rank = 18
    pfa = 1e-3
    ca_alpha = training * (pfa ** (-1 / training) - 1)
    os_alpha = calibrated_os_scale(training, rank, pfa)
    references = [
        [generator.expovariate(1.0) for _ in range(training)]
        for _ in range(trials)
    ]
    cuts = [
        abs(
            complex(
                generator.gauss(0.0, 1 / math.sqrt(2)),
                generator.gauss(0.0, 1 / math.sqrt(2)),
            )
            + math.sqrt(10 ** 1.3)
        )
        ** 2
        for _ in range(trials)
    ]

    count_pd: dict[int, tuple[float, float]] = {}
    for count in (0, 2, 4, 6, 7, 8):
        ca_detect = os_detect = 0
        for row, cut in zip(references, cuts):
            contaminated = [value + (100.0 if index < count else 0.0) for index, value in enumerate(row)]
            ca_detect += cut > ca_alpha * sum(contaminated) / training
            os_detect += cut > os_alpha * sorted(contaminated)[rank - 1]
        count_pd[count] = (ca_detect / trials, os_detect / trials)

    strength_pd: dict[float, tuple[float, float]] = {}
    for strength_db in (-20.0, 0.0, 10.0, 20.0, 30.0):
        added_power = 10 ** (strength_db / 10)
        ca_detect = os_detect = 0
        for row, cut in zip(references, cuts):
            contaminated = [value + (added_power if index < 4 else 0.0) for index, value in enumerate(row)]
            ca_detect += cut > ca_alpha * sum(contaminated) / training
            os_detect += cut > os_alpha * sorted(contaminated)[rank - 1]
        strength_pd[strength_db] = (ca_detect / trials, os_detect / trials)

    clean_rank_pd: dict[int, float] = {}
    rank_pd: dict[int, float] = {}
    for candidate in (12, 16, 18, 20, 22, 24):
        alpha = calibrated_os_scale(training, candidate, pfa)
        clean_detected = 0
        detected = 0
        for row, cut in zip(references, cuts):
            clean_detected += cut > alpha * sorted(row)[candidate - 1]
            contaminated = [value + (100.0 if index < 4 else 0.0) for index, value in enumerate(row)]
            detected += cut > alpha * sorted(contaminated)[candidate - 1]
        clean_rank_pd[candidate] = clean_detected / trials
        rank_pd[candidate] = detected / trials
    return {
        "count_pd": count_pd,
        "strength_pd": strength_pd,
        "clean_rank_pd": clean_rank_pd,
        "rank_pd": rank_pd,
    }


class P49ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self):
        self.assertEqual(validate_p49_contract(MODULE, self.manifest), [])
        p48 = next(item for item in self.manifest["modules"] if item["id"] == "P48")
        self.assertEqual(p48["status"], "implemented")
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
            self.assertIn("P49 missing checks.md", validate_p49_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("\n", encoding="utf-8")
            self.assertIn("P49 empty checks.md", validate_p49_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p49_contract(MODULE, {}))
        self.assertIn("manifest module entries must be objects", validate_p49_contract(MODULE, {"modules": ["P49"]}))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P49 manifest entry, found 2", validate_p49_contract(MODULE, duplicate))
        for key, expected in EXPECTED_IDENTITY.items():
            drifted = copy.deepcopy(self.manifest)
            next(item for item in drifted["modules"] if item["id"] == "P49")[key] = f"wrong-{expected}"
            self.assertTrue(validate_p49_contract(MODULE, drifted))

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self):
        validate_controls()
        invalid = (
            {"unexpected": 1},
            {"seed": True},
            {"seed": 4902},
            {"cells": 321},
            {"mean_power": math.nan},
            {"mean_power": 0.0},
            {"mean_power": 1e-7},
            {"mean_power": 1e7},
            {"training": 25},
            {"guards": -1},
            {"pfa": 0.0},
            {"pfa": 1e-7},
            {"primary_snr_db": 41.0},
            {"interferer_db": -31.0},
            {"primary": 2},
            {"rank": 25},
            {"interferer_cells": (115, 115)},
            {"interferer_cells": (100, 120)},
            {"count_sweep": (0, 4, 2)},
            {"count_sweep": (0, 2, 25)},
            {"count_sweep": (0, 2, 7)},
            {"count_sweep": (0, 2, 4, 6, 8)},
            {"strength_sweep": (-20.0, math.inf, 20.0)},
            {"strength_sweep": (-20.0, 0.0, 30.0)},
            {"rank_sweep": (12, 16, 22)},
            {"rank_sweep": (12, 16, 18, 20)},
            {"rank_sweep": (12, 18, 25)},
            {"trials": 25_001},
            {"iterations": 39},
            {"max_random": 700_000},
            {"max_stored": 1_000_000},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                validate_controls(**overrides)

    def test_source_is_seeded_transparent_bounded_and_mutation_sensitive(self):
        self.assertEqual(source_contract_errors(self.source), [])
        controls_end = self.source.index("%% Calibrate CA and the selected OS rank")
        first_allocation = self.source.index("private_stream =")
        self.assertLess(controls_end, first_allocation)
        self.assertIn("estimated_generated_random_values", self.source[:controls_end])
        self.assertIn("estimated_stored_numeric_values", self.source[:controls_end])
        self.assertIn("islogical(control_value)", self.source[:controls_end])
        self.assertEqual(self.source.count("figure('Name'"), 5)
        self.assertNotIn("sorted_clean_reference_power", self.source)
        self.assertNotRegex(
            self.source.lower(),
            r"\b(?:phased\.|cfardetector|ordfilt\w*\s*\(|prctile\s*\(|quantile\s*\(|"
            r"exprnd\s*\(|awgn\s*\(|parfor\b|while\b|fopen\s*\(|webread\s*\(|"
            r"system\s*\(|timer\s*\(|rng\s*\()",
        )
        for marker in (
            "if max_range_cells ~= 320 || max_training_cells_per_side ~= 24 ||",
            "reference_power = received_power(reference_cells);",
            "sorted_reference_power = sort(reference_power, 'ascend');",
            "design_false_alarm_probability = 1e-3;",
            "design_false_alarm_probability^(-1/total_training_cell_count)",
            "log(training_count-spacing_index+alpha);",
            "contaminated_reference_power(:, 1:strength_sweep_interferer_count) =",
            "count_sweep_os_pd(count_index) =",
            "rank_sweep_os_pd(rank_index) =",
            "broken_reused_scale_claim_is_valid = false;",
        ):
            mutated = self.source.replace(marker, "mutated", 1)
            self.assertTrue(source_contract_errors(mutated), marker)

    def test_exact_os_calibration_capacity_and_malformed_inputs(self):
        training = 24
        pfa = 1e-3
        alpha = calibrated_os_scale(training, 18, pfa)
        ca_alpha = training * (pfa ** (-1 / training) - 1)
        self.assertAlmostEqual(alpha, 6.502430709645976, places=12)
        self.assertAlmostEqual(ca_alpha, 8.004514371919775, places=12)
        self.assertAlmostEqual(os_pfa(alpha, training, 18), pfa, places=14)
        self.assertEqual(training - 18, 6)
        self.assertAlmostEqual(os_pfa(alpha, training, 12), 0.024385022411216258, places=14)
        self.assertAlmostEqual(calibrated_os_scale(training, 12, pfa), 13.996715751543068, places=12)
        for malformed in ((math.nan, 24, 18), (1.0, True, 1), (1.0, 24, 25)):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                os_pfa(*malformed)
        with self.assertRaises(ValueError):
            calibrated_os_scale(24, 18, 0.0)

    def test_independent_oracle_exposes_count_and_strength_limits(self):
        oracle = independent_behavior_oracle()
        count = oracle["count_pd"]
        self.assertGreater(count[0][0], 0.95)
        self.assertGreater(count[0][1], 0.95)
        self.assertLess(count[4][0], 0.1)
        self.assertGreater(count[4][1], 0.75)
        self.assertGreater(count[6][1], 0.35)
        self.assertLess(count[7][1], 0.1)
        self.assertLess(count[8][1], 0.1)
        strength = oracle["strength_pd"]
        self.assertGreater(strength[-20.0][0], 0.95)
        self.assertLess(strength[20.0][0], 0.1)
        self.assertGreater(strength[20.0][1], 0.75)
        self.assertAlmostEqual(strength[20.0][1], strength[30.0][1], delta=0.01)

    def test_rank_tradeoff_broken_reuse_and_recovery(self):
        rank_pd = independent_behavior_oracle()["rank_pd"]
        self.assertGreater(rank_pd[12], 0.8)
        self.assertGreater(rank_pd[18], 0.75)
        self.assertLess(rank_pd[22], 0.1)
        self.assertLess(rank_pd[24], 0.1)
        baseline_alpha = calibrated_os_scale(24, 18, 1e-3)
        self.assertGreater(os_pfa(baseline_alpha, 24, 12), 20e-3)
        self.assertAlmostEqual(os_pfa(calibrated_os_scale(24, 12, 1e-3), 24, 12), 1e-3, places=14)

    def test_clean_scene_rank_cost_reverses_the_contaminated_preference(self):
        oracle = independent_behavior_oracle()
        clean_rank_pd = oracle["clean_rank_pd"]
        contaminated_rank_pd = oracle["rank_pd"]
        self.assertGreater(clean_rank_pd[18], clean_rank_pd[12] + 0.01)
        self.assertGreater(contaminated_rank_pd[12], contaminated_rank_pd[18] + 0.02)
        self.assertGreater(clean_rank_pd[12], contaminated_rank_pd[12] + 0.05)

    def test_docs_cover_model_sweeps_failure_recovery_limits_and_teach_back(self):
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        combined = "\n".join((readme, lesson, walkthrough, checks))
        normalized = re.sub(r"\s+", " ", combined)
        for phrase in (
            QUESTION,
            "x_(1) <= x_(2) <= ... <= x_(N)",
            "q <= N-k",
            "interferer count",
            "interferer strength",
            "rank-specific calibration",
            "intentionally broken",
            "Recovery",
            "Ctrl+C",
            "Short teach-back rubric",
            "With `k = N`",
            "With `k = 1`",
            "P45",
            "P48",
            "P50",
            "P52",
        ):
            self.assertIn(phrase, normalized)
        self.assertNotRegex(combined, r"(?i)TODO|coming soon|placeholder")
        self.assertLess(lesson.index("Start with the physical window"), lesson.index("OS-CFAR: sort"))

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
        process, state = self._run_fixture_cli(self.manifest, "start", "49")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("P49 — Use Ordered-Statistic CFAR with Interfering Targets", process.stdout)
        self.assertIn("status: implemented", process.stdout)
        self.assertEqual(state["current"], "P49")
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

        rolled = copy.deepcopy(self.manifest)
        next(item for item in rolled["modules"] if item["id"] == "P49")["status"] = "scaffolded"
        rolled_process, _ = self._run_fixture_cli(rolled, "start", "49")
        self.assertEqual(rolled_process.returncode, 3)
        self.assertIn("awaits Portfolio batch P49", rolled_process.stdout)

    def test_default_tutor_entry_advances_from_completed_p48_without_state_loss(self):
        prior_completed = [f"P{number:02d}" for number in range(1, 49)]
        initial = {
            "schema_version": 1,
            "current": "P48",
            "completed": prior_completed,
            "notes": {"P48": "preserve this equal-Pfa edge teach-back"},
        }
        process, state = self._run_fixture_cli(self.manifest, "start", initial_state=initial)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("P49 — Use Ordered-Statistic CFAR", process.stdout)
        self.assertEqual(state["current"], "P49")
        self.assertEqual(state["completed"], prior_completed)
        self.assertEqual(state["notes"], initial["notes"])

    def test_p49_only_rollback_preserves_neighbor_identity(self):
        rolled = copy.deepcopy(self.manifest)
        neighbors_before = {
            item["id"]: copy.deepcopy(item)
            for item in rolled["modules"]
            if item["id"] in {"P48", "P50"}
        }
        next(item for item in rolled["modules"] if item["id"] == "P49")["status"] = "scaffolded"
        neighbors_after = {
            item["id"]: item for item in rolled["modules"] if item["id"] in {"P48", "P50"}
        }
        self.assertEqual(neighbors_after, neighbors_before)
        self.assertTrue(any("status" in error for error in validate_p49_contract(MODULE, rolled)))

    def test_public_catalogs_describe_p49_without_freezing_future_state(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 49 sorts all square-law training powers", readme)
        self.assertIn("Project 49 follows P48", start_here)
        self.assertRegex(module_index, r"\| \[P49\].*\| implemented \| 5 \|")
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?i)P49\s+(?:is\s+)?(?:the\s+)?(?:latest|last|final)")
        self.assertNotRegex(source, r"(?i)P50[^\n]*remains? scaffolded")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self):
        evidence = ROOT / "docs/evidence/P49-2026-08-04.md"
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
            "python3 -m unittest tests.test_p49_module -v",
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
