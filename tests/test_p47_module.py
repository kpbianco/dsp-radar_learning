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
MODULE = ROOT / "modules/47-measure-cfar-loss"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How much extra SNR does adaptive threshold estimation cost?"
EXPECTED_IDENTITY = {
    "number": 47,
    "id": "P47",
    "title": "Measure CFAR Loss",
    "guiding_question": QUESTION,
    "phase": 5,
    "phase_title": "Detection and CFAR",
    "slug": "measure-cfar-loss",
    "folder": "modules/47-measure-cfar-loss",
    "status": "implemented",
    "implementation_batch": "P47",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p47_contract(path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        artifact = path / name
        if not artifact.is_file():
            errors.append(f"P47 missing {name}")
        elif not artifact.read_text(encoding="utf-8").strip():
            errors.append(f"P47 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P47"]
    if len(matches) != 1:
        return errors + [f"expected one P47 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P47 {key} must be {expected!r}")
    return errors


def canonical_controls() -> dict[str, object]:
    return {
        "seed": 4701,
        "trials": 50_000,
        "block_trials": 2_000,
        "snr_db": tuple(3 + 0.5 * index for index in range(29)),
        "pfa": 1e-3,
        "target_pd": 0.8,
        "baseline_training": 16,
        "training_sweep": (8, 16, 32, 64),
        "pfa_sweep": (1e-2, 1e-3, 1e-4),
        "example_snr_db": 10.0,
        "display_trials": 240,
        "monotone_tolerance": 0.01,
        "probability_sigma": 5.0,
        "max_trials": 60_000,
        "max_block_trials": 5_000,
        "max_snr_cases": 40,
        "max_training": 64,
        "max_sweep_cases": 5,
        "max_figures": 5,
        "max_generated_random_reals": 7_000_000,
        "max_stored_values": 2_000_000,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    integer_names = (
        "seed",
        "trials",
        "block_trials",
        "baseline_training",
        "display_trials",
        "max_trials",
        "max_block_trials",
        "max_snr_cases",
        "max_training",
        "max_sweep_cases",
        "max_figures",
        "max_generated_random_reals",
        "max_stored_values",
    )
    for name in integer_names:
        if not isinstance(controls[name], int) or isinstance(controls[name], bool):
            raise ValueError(f"{name} must be an integer")
    for name in (
        "pfa",
        "target_pd",
        "example_snr_db",
        "monotone_tolerance",
        "probability_sigma",
    ):
        if not finite_real(controls[name]):
            raise ValueError(f"{name} must be finite and real")

    if controls["seed"] != 4701 or controls["trials"] != 50_000:
        raise ValueError("canonical deterministic experiment changed")
    if not 1 <= controls["trials"] <= controls["max_trials"]:
        raise ValueError("trial count outside bounds")
    if not 100 <= controls["block_trials"] <= controls["max_block_trials"]:
        raise ValueError("block size outside bounds")
    if controls["trials"] % controls["block_trials"]:
        raise ValueError("block size must divide trials")
    if not 0 < controls["pfa"] < 0.1 or not 0 < controls["target_pd"] < 1:
        raise ValueError("probability outside bounds")
    if not 0 < controls["monotone_tolerance"] <= 0.02:
        raise ValueError("monotone tolerance outside bounds")
    if not 3 <= controls["probability_sigma"] <= 8:
        raise ValueError("probability tolerance outside bounds")

    snr_db = controls["snr_db"]
    if not isinstance(snr_db, (tuple, list)) or not 5 <= len(snr_db) <= controls["max_snr_cases"]:
        raise ValueError("SNR case count outside bounds")
    if not all(finite_real(value) for value in snr_db):
        raise ValueError("SNR values must be finite real numbers")
    if any(b <= a for a, b in zip(snr_db, snr_db[1:])):
        raise ValueError("SNR grid must be strictly increasing")
    if controls["example_snr_db"] not in snr_db:
        raise ValueError("example SNR must lie on grid")

    training = controls["training_sweep"]
    if not isinstance(training, (tuple, list)) or not 3 <= len(training) <= controls["max_sweep_cases"]:
        raise ValueError("training sweep case count outside bounds")
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in training):
        raise ValueError("training sweep must contain integers")
    if min(training) < 4 or max(training) > controls["max_training"]:
        raise ValueError("training sweep outside bounds")
    if any(b <= a for a, b in zip(training, training[1:])):
        raise ValueError("training sweep must be strictly increasing")
    if controls["baseline_training"] not in training:
        raise ValueError("training sweep omits baseline")

    pfa_sweep = controls["pfa_sweep"]
    if not isinstance(pfa_sweep, (tuple, list)) or not 3 <= len(pfa_sweep) <= controls["max_sweep_cases"]:
        raise ValueError("Pfa sweep case count outside bounds")
    if not all(finite_real(value) and 0 < value < 0.1 for value in pfa_sweep):
        raise ValueError("Pfa sweep values outside bounds")
    if any(b >= a for a, b in zip(pfa_sweep, pfa_sweep[1:])):
        raise ValueError("Pfa sweep must be strictly decreasing")
    if controls["pfa"] not in pfa_sweep:
        raise ValueError("Pfa sweep omits baseline")

    if not 50 <= controls["display_trials"] <= controls["block_trials"]:
        raise ValueError("display trial count outside bounds")
    ceilings = {
        "max_trials": 60_000,
        "max_block_trials": 5_000,
        "max_snr_cases": 40,
        "max_training": 64,
        "max_sweep_cases": 5,
        "max_figures": 5,
        "max_generated_random_reals": 7_000_000,
        "max_stored_values": 2_000_000,
    }
    for name, expected in ceilings.items():
        if controls[name] != expected:
            raise ValueError(f"{name} must remain reviewed and fixed")
    generated = 2 * controls["trials"] * (max(training) + 2)
    stored = controls["trials"] * (len(snr_db) + len(training) + 4) + 10_000
    if generated > controls["max_generated_random_reals"]:
        raise ValueError("generated-random-value ceiling exceeded")
    if stored > controls["max_stored_values"]:
        raise ValueError("stored-value ceiling exceeded")


def monotone_crossing(snr_db: list[float], pd: list[float], target_pd: float) -> tuple[float, float]:
    if len(snr_db) != len(pd) or len(snr_db) < 2:
        raise ValueError("curve shapes must match")
    if not all(finite_real(value) for value in (*snr_db, *pd, target_pd)):
        raise ValueError("curve values must be finite and real")
    if any(b <= a for a, b in zip(snr_db, snr_db[1:])):
        raise ValueError("SNR grid must be strictly increasing")
    if not 0 < target_pd < 1 or any(value < 0 or value > 1 for value in pd):
        raise ValueError("probabilities outside bounds")
    monotone: list[float] = []
    for value in pd:
        monotone.append(max(value, monotone[-1] if monotone else value))
    adjustment = max(abs(a - b) for a, b in zip(monotone, pd))
    upper = next((index for index, value in enumerate(monotone) if value >= target_pd), None)
    if upper is None or upper == 0:
        raise ValueError("target Pd is not internally bracketed")
    lower = upper - 1
    gap = monotone[upper] - monotone[lower]
    if gap <= 0:
        raise ValueError("target crossing has zero probability span")
    crossing = snr_db[lower] + (target_pd - monotone[lower]) * (
        snr_db[upper] - snr_db[lower]
    ) / gap
    return crossing, adjustment


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", source.replace("...", ""))
    required = (
        "random_seed = 4701;",
        "trial_count = 50000;",
        "block_trial_count = 2000;",
        "snr_db = 3:0.5:17;",
        "training_cell_count_sweep = [8 16 32 64];",
        "false_alarm_probability_sweep = [1e-2 1e-3 1e-4];",
        "private_stream = RandStream('mt19937ar', 'Seed', random_seed);",
        "1i*randn(private_stream, trial_count, 1))/sqrt(2);",
        "reference_power_cumulative = cumsum(abs(reference_noise_block).^2, 2);",
        "target_present_power(:, snr_index) = abs(unit_cut_noise+ sqrt(snr_linear)*unit_target_phasor).^2;",
        "known_noise_threshold_power = -log(design_false_alarm_probability);",
        "cfar_scale_factor = training_cell_count*( design_false_alarm_probability^(-1/training_cell_count)-1);",
        "training_sweep_cfar_loss_db = training_sweep_snr_at_target_pd_db- known_snr_at_target_pd_db;",
        "broken_actual_false_alarm_probability = (1+known_noise_threshold_power/ baseline_training_cell_count)^(-baseline_training_cell_count);",
        "broken_claim_is_valid = false;",
        "recovery_exact = recovered_scale_factor == baseline_cfar_scale_factor",
        "results.baseline_cfar_loss_db = baseline_cfar_loss_db;",
    )
    return [marker for marker in required if marker not in compact]


@functools.lru_cache(maxsize=1)
def independent_oracle() -> dict[str, object]:
    generator = random.Random(4701)
    trial_count = 30_000
    snr_db = [3 + 0.5 * index for index in range(29)]
    target_pd = 0.8
    cut_noise = [
        complex(
            generator.gauss(0.0, 1 / math.sqrt(2)),
            generator.gauss(0.0, 1 / math.sqrt(2)),
        )
        for _ in range(trial_count)
    ]
    estimates = {
        count: [generator.gammavariate(count, 1 / count) for _ in range(trial_count)]
        for count in (8, 16, 32, 64)
    }

    def pd_curve(thresholds: list[float]) -> list[float]:
        return [
            sum(
                abs(math.sqrt(10 ** (snr / 10)) + noise) ** 2 > threshold
                for noise, threshold in zip(cut_noise, thresholds)
            )
            / trial_count
            for snr in snr_db
        ]

    pfa = 1e-3
    known_curve = pd_curve([-math.log(pfa)] * trial_count)
    known_snr, _ = monotone_crossing(snr_db, known_curve, target_pd)
    losses: dict[int, float] = {}
    training_curves: dict[int, list[float]] = {}
    for count, estimate in estimates.items():
        alpha = count * (pfa ** (-1 / count) - 1)
        curve = pd_curve([alpha * value for value in estimate])
        training_curves[count] = curve
        required_snr, _ = monotone_crossing(snr_db, curve, target_pd)
        losses[count] = required_snr - known_snr

    pfa_losses: dict[float, float] = {}
    for probability in (1e-2, 1e-3, 1e-4):
        known = pd_curve([-math.log(probability)] * trial_count)
        known_required, _ = monotone_crossing(snr_db, known, target_pd)
        alpha = 16 * (probability ** (-1 / 16) - 1)
        cfar = pd_curve([alpha * value for value in estimates[16]])
        cfar_required, _ = monotone_crossing(snr_db, cfar, target_pd)
        pfa_losses[probability] = cfar_required - known_required

    baseline_count = 16
    baseline_estimate = estimates[baseline_count]
    known_multiplier = -math.log(pfa)
    calibrated_multiplier = baseline_count * (pfa ** (-1 / baseline_count) - 1)
    broken_thresholds = [known_multiplier * value for value in baseline_estimate]
    broken_curve = pd_curve(broken_thresholds)
    broken_required, _ = monotone_crossing(snr_db, broken_curve, target_pd)
    broken_theoretical_pfa = (1 + known_multiplier / baseline_count) ** -baseline_count
    h0_power = [abs(value) ** 2 for value in cut_noise]
    broken_empirical_pfa = sum(
        cut > threshold for cut, threshold in zip(h0_power, broken_thresholds)
    ) / trial_count

    recovered_multiplier = baseline_count * (pfa ** (-1 / baseline_count) - 1)
    recovered_thresholds = [recovered_multiplier * value for value in baseline_estimate]
    recovered_curve = pd_curve(recovered_thresholds)
    recovered_required, _ = monotone_crossing(snr_db, recovered_curve, target_pd)
    return {
        "losses": losses,
        "pfa_losses": pfa_losses,
        "broken_case": {
            "requested_pfa": pfa,
            "calibrated_multiplier": calibrated_multiplier,
            "calibrated_curve": training_curves[baseline_count],
            "calibrated_loss": losses[baseline_count],
            "broken_theoretical_pfa": broken_theoretical_pfa,
            "broken_empirical_pfa": broken_empirical_pfa,
            "broken_apparent_loss": broken_required - known_snr,
            "recovered_multiplier": recovered_multiplier,
            "recovered_curve": recovered_curve,
            "recovered_loss": recovered_required - known_snr,
        },
    }


class P47ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text())
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self):
        self.assertEqual(validate_p47_contract(MODULE, self.manifest), [])
        p46 = next(item for item in self.manifest["modules"] if item["id"] == "P46")
        self.assertEqual(p46["status"], "implemented")
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
            self.assertIn("P47 missing checks.md", validate_p47_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("\n", encoding="utf-8")
            self.assertIn("P47 empty checks.md", validate_p47_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p47_contract(MODULE, {}))
        malformed = {"modules": ["P47"]}
        self.assertIn("manifest module entries must be objects", validate_p47_contract(MODULE, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P47 manifest entry, found 2", validate_p47_contract(MODULE, duplicate))
        for key, expected in EXPECTED_IDENTITY.items():
            drifted = copy.deepcopy(self.manifest)
            entry = next(item for item in drifted["modules"] if item["id"] == "P47")
            entry[key] = f"wrong-{expected}"
            self.assertTrue(validate_p47_contract(MODULE, drifted))

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self):
        validate_controls()
        invalid = (
            {"unexpected": 1},
            {"seed": True},
            {"seed": 4702},
            {"trials": 60_001},
            {"block_trials": 3_000},
            {"pfa": math.nan},
            {"pfa": 0.0},
            {"target_pd": 1.0},
            {"snr_db": (3.0, 3.0, 4.0, 5.0, 10.0)},
            {"snr_db": (3.0, 4.0, math.inf, 6.0, 10.0)},
            {"training_sweep": (8, 16, 16, 64)},
            {"training_sweep": (8, 32, 64)},
            {"training_sweep": (8, 16, 32, 65)},
            {"pfa_sweep": (1e-2, 1e-3, 1e-3)},
            {"pfa_sweep": (1e-2, 1e-4, 1e-5)},
            {"display_trials": 2_001},
            {"max_trials": 70_000},
            {"max_stored_values": 100},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                validate_controls(**overrides)

    def test_source_is_seeded_transparent_bounded_and_mutation_sensitive(self):
        self.assertEqual(source_contract_errors(self.source), [])
        controls_end = self.source.index("%% Generate paired CUT trials")
        first_allocation = self.source.index("unit_cut_noise =")
        self.assertLess(controls_end, first_allocation)
        self.assertIn("estimated_generated_random_real_values", self.source[:first_allocation])
        self.assertIn("estimated_stored_numeric_values", self.source[:first_allocation])
        self.assertEqual(self.source.count("figure('Name'"), 5)
        self.assertNotRegex(
            self.source.lower(),
            r"\b(?:phased\.|cfardetector|exprnd\s*\(|awgn\s*\(|parfor\b|while\b|"
            r"fopen\s*\(|webread\s*\(|system\s*\(|timer\s*\(|rng\s*\()",
        )
        for marker in (
            "known_noise_threshold_power = -log(design_false_alarm_probability);",
            "broken_claim_is_valid = false;",
            "sqrt(snr_linear)*unit_target_phasor",
        ):
            mutated = self.source.replace(marker, "mutated", 1)
            self.assertTrue(source_contract_errors(mutated), marker)

    def test_exact_threshold_formula_limits_and_broken_false_alarm(self):
        pfa = 1e-3
        known = -math.log(pfa)
        counts = (8, 16, 32, 64)
        alphas = [count * (pfa ** (-1 / count) - 1) for count in counts]
        self.assertTrue(all(alpha > known for alpha in alphas))
        self.assertTrue(all(b < a for a, b in zip(alphas, alphas[1:])))
        for count, alpha in zip(counts, alphas):
            self.assertAlmostEqual((1 + alpha / count) ** (-count), pfa, places=14)
        self.assertLess(abs(100_000 * (pfa ** (-1 / 100_000) - 1) - known), 3e-4)
        broken_actual = (1 + known / 16) ** -16
        self.assertAlmostEqual(broken_actual, 0.0032077400266028754, places=14)
        self.assertGreater(broken_actual, 3 * pfa)

    def test_interpolation_is_explicit_monotone_and_rejects_malformed_curves(self):
        crossing, adjustment = monotone_crossing(
            [0.0, 1.0, 2.0, 3.0], [0.1, 0.6, 0.55, 0.9], 0.8
        )
        self.assertAlmostEqual(crossing, 2.6666666666666665)
        self.assertAlmostEqual(adjustment, 0.05)
        malformed = (
            ([0.0], [0.5], 0.5),
            ([0.0, 1.0], [0.1], 0.5),
            ([0.0, 0.0], [0.1, 0.9], 0.5),
            ([0.0, math.inf], [0.1, 0.9], 0.5),
            ([0.0, 1.0], [0.1, 1.1], 0.5),
            ([0.0, 1.0], [0.7, 0.9], 0.5),
            ([0.0, 1.0], [0.1, 0.2], 0.5),
            ([0.0, 1.0, 2.0], [0.1, 0.8, 0.8], 0.9),
        )
        for snr, pd, target in malformed:
            with self.subTest(snr=snr, pd=pd, target=target), self.assertRaises(ValueError):
                monotone_crossing(snr, pd, target)

    def test_independent_monte_carlo_oracle_measures_expected_loss_trends(self):
        oracle = independent_oracle()
        losses = oracle["losses"]
        self.assertEqual(list(losses), [8, 16, 32, 64])
        self.assertTrue(all(b < a for a, b in zip(losses.values(), list(losses.values())[1:])))
        expected_ranges = {
            8: (1.8, 2.2),
            16: (0.8, 1.15),
            32: (0.35, 0.65),
            64: (0.15, 0.35),
        }
        for count, bounds in expected_ranges.items():
            self.assertGreater(losses[count], bounds[0])
            self.assertLess(losses[count], bounds[1])
        pfa_losses = oracle["pfa_losses"]
        self.assertLess(pfa_losses[1e-2], pfa_losses[1e-3])
        self.assertLess(pfa_losses[1e-3], pfa_losses[1e-4])
        self.assertTrue(all(value > 0 for value in pfa_losses.values()))

    def test_broken_calibration_only_looks_better_and_recovery_restores_behavior(self):
        broken = independent_oracle()["broken_case"]
        self.assertLess(broken["broken_apparent_loss"], broken["calibrated_loss"])
        self.assertGreater(
            broken["broken_theoretical_pfa"], 3 * broken["requested_pfa"]
        )
        self.assertGreater(broken["broken_empirical_pfa"], 3 * broken["requested_pfa"])
        self.assertAlmostEqual(
            broken["recovered_multiplier"], broken["calibrated_multiplier"]
        )
        self.assertEqual(broken["recovered_curve"], broken["calibrated_curve"])
        self.assertAlmostEqual(broken["recovered_loss"], broken["calibrated_loss"])

    def test_docs_cover_model_sweeps_failure_recovery_cancellation_and_teach_back(self):
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        combined = "\n".join((readme, lesson, walkthrough, checks))
        normalized = re.sub(r"\s+", " ", combined)
        for phrase in (
            QUESTION,
            "alpha(N,Pfa) = N * (Pfa^(-1/N) - 1)",
            "CFAR loss (dB) = SNR_required,CFAR - SNR_required,known",
            "same false-alarm probability",
            "training-count sweep",
            "requested-`Pfa` sweep",
            "broken detector",
            "Recovery",
            "Ctrl+C",
            "Short teach-back rubric",
            "As `N` tends to infinity",
            "P52",
        ):
            self.assertIn(phrase, normalized)
        self.assertNotRegex(combined, r"(?i)TODO|coming soon|placeholder")
        self.assertLess(lesson.index("Start with the physical comparison"), lesson.index("The two threshold operations"))

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

    def test_isolated_cli_timeout_and_scaffold_rollback_compatibility(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        process, state = self._run_fixture_cli(self.manifest, "start", "47")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("P47 — Measure CFAR Loss", process.stdout)
        self.assertIn("status: implemented", process.stdout)
        self.assertEqual(state["current"], "P47")
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

        rolled = copy.deepcopy(self.manifest)
        next(item for item in rolled["modules"] if item["id"] == "P47")["status"] = "scaffolded"
        rolled_process, _ = self._run_fixture_cli(rolled, "start", "47")
        self.assertEqual(rolled_process.returncode, 3)
        self.assertIn("awaits Portfolio batch P47", rolled_process.stdout)

    def test_default_tutor_entry_advances_from_completed_p46_without_state_loss(self):
        prior_completed = [f"P{number:02d}" for number in range(1, 47)]
        initial = {
            "schema_version": 1,
            "current": "P46",
            "completed": prior_completed,
            "notes": {"P46": "preserve this CFAR-window teach-back"},
        }
        process, state = self._run_fixture_cli(self.manifest, "start", initial_state=initial)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("P47 — Measure CFAR Loss", process.stdout)
        self.assertEqual(state["current"], "P47")
        self.assertEqual(state["completed"], prior_completed)
        self.assertEqual(state["notes"], initial["notes"])

    def test_p47_only_rollback_preserves_neighbor_identity(self):
        rolled = copy.deepcopy(self.manifest)
        neighbors_before = {
            item["id"]: copy.deepcopy(item)
            for item in rolled["modules"]
            if item["id"] in {"P46", "P48"}
        }
        next(item for item in rolled["modules"] if item["id"] == "P47")["status"] = "scaffolded"
        neighbors_after = {
            item["id"]: item for item in rolled["modules"] if item["id"] in {"P46", "P48"}
        }
        self.assertEqual(neighbors_after, neighbors_before)
        self.assertTrue(any("status" in error for error in validate_p47_contract(MODULE, rolled)))

    def test_public_catalogs_describe_p47_without_freezing_future_state(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 47 compares a fixed known-noise", readme)
        self.assertIn("Project 47 follows P46", start_here)
        self.assertRegex(module_index, r"\| \[P47\].*\| implemented \| 5 \|")
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?i)P47\s+(?:is\s+)?(?:the\s+)?(?:latest|last|final)")
        self.assertNotRegex(source, r"(?i)P48[^\n]*remains? scaffolded")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self):
        evidence = ROOT / "docs/evidence/P47-2026-08-04.md"
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
            "python3 -m unittest tests.test_p47_module -v",
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
