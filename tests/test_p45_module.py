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
MODULE = ROOT / "modules/45-implement-1-d-cell-averaging-cfar"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How can the threshold adapt to the local noise level?"
EXPECTED_IDENTITY = {
    "number": 45,
    "id": "P45",
    "title": "Implement 1-D Cell-Averaging CFAR",
    "guiding_question": QUESTION,
    "phase": 5,
    "phase_title": "Detection and CFAR",
    "slug": "implement-1-d-cell-averaging-cfar",
    "folder": "modules/45-implement-1-d-cell-averaging-cfar",
    "status": "implemented",
    "implementation_batch": "P45",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p45_contract(path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        artifact = path / name
        if not artifact.is_file():
            errors.append(f"P45 missing {name}")
        elif not artifact.read_text(encoding="utf-8").strip():
            errors.append(f"P45 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P45"]
    if len(matches) != 1:
        return errors + [f"expected one P45 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P45 {key} must be {expected!r}")
    return errors


def canonical_controls() -> dict[str, object]:
    return {
        "seed": 4501,
        "cells": 256,
        "range_resolution_m": 15.0,
        "training_per_side": 12,
        "guards_per_side": 2,
        "design_pfa": 1e-3,
        "target_cells": (62, 132, 211),
        "target_snr_db": (19.0, 17.0, 20.0),
        "target_phase_rad": (0.2, -0.8, 1.1),
        "pfa_sweep": (1e-2, 1e-3, 1e-4),
        "scale_sweep": (0.5, 1.0, 2.0),
        "tolerance": 1e-10,
        "max_cells": 512,
        "max_training": 32,
        "max_guards": 8,
        "max_targets": 6,
        "max_probability_cases": 5,
        "max_scale_cases": 5,
        "max_figures": 5,
        "max_stored_values": 50_000,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    integer_names = (
        "seed",
        "cells",
        "training_per_side",
        "guards_per_side",
        "max_cells",
        "max_training",
        "max_guards",
        "max_targets",
        "max_probability_cases",
        "max_scale_cases",
        "max_figures",
        "max_stored_values",
    )
    for name in integer_names:
        value = controls[name]
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{name} must be an integer")
    for name in ("range_resolution_m", "design_pfa", "tolerance"):
        if not finite_real(controls[name]):
            raise ValueError(f"{name} must be finite and real")

    if controls["seed"] != 4501:
        raise ValueError("seed must remain canonical")
    if controls["cells"] != 256 or controls["cells"] > controls["max_cells"]:
        raise ValueError("cell count outside reviewed shape")
    if controls["range_resolution_m"] <= 0:
        raise ValueError("range resolution must be positive")
    if not 2 <= controls["training_per_side"] <= controls["max_training"]:
        raise ValueError("training geometry outside reviewed bounds")
    if not 1 <= controls["guards_per_side"] <= controls["max_guards"]:
        raise ValueError("guard geometry outside reviewed bounds")
    if 2 * (controls["training_per_side"] + controls["guards_per_side"]) + 1 >= controls["cells"]:
        raise ValueError("CFAR window does not fit")
    if not 0 < controls["design_pfa"] < 0.5:
        raise ValueError("design Pfa outside one-sided reviewed bounds")
    if not 0 < controls["tolerance"] <= 1e-6:
        raise ValueError("comparison tolerance outside reviewed bounds")

    target_vectors = (
        controls["target_cells"],
        controls["target_snr_db"],
        controls["target_phase_rad"],
    )
    if not all(isinstance(vector, (tuple, list)) for vector in target_vectors):
        raise ValueError("target controls must be vectors")
    if not 2 <= len(controls["target_cells"]) <= controls["max_targets"]:
        raise ValueError("target count outside reviewed bounds")
    if len({len(vector) for vector in target_vectors}) != 1:
        raise ValueError("target vectors must have equal lengths")
    if not all(
        isinstance(value, int) and not isinstance(value, bool)
        for value in controls["target_cells"]
    ):
        raise ValueError("target cells must be integers")
    if not all(
        finite_real(value)
        for vector in (controls["target_snr_db"], controls["target_phase_rad"])
        for value in vector
    ):
        raise ValueError("target SNR and phase must be finite real values")

    first = controls["training_per_side"] + controls["guards_per_side"] + 1
    last = controls["cells"] - controls["training_per_side"] - controls["guards_per_side"]
    targets = tuple(controls["target_cells"])
    if not all(first <= value <= last for value in targets):
        raise ValueError("target outside eligible CUT range")
    if any(right <= left for left, right in zip(targets, targets[1:])):
        raise ValueError("target cells must be strictly increasing")
    minimum_spacing = 2 * (controls["training_per_side"] + controls["guards_per_side"])
    if any(right - left <= minimum_spacing for left, right in zip(targets, targets[1:])):
        raise ValueError("target windows must remain separated")

    pfas = controls["pfa_sweep"]
    scales = controls["scale_sweep"]
    if not isinstance(pfas, (tuple, list)) or not 3 <= len(pfas) <= controls["max_probability_cases"]:
        raise ValueError("Pfa sweep case count outside reviewed bounds")
    if not all(finite_real(value) and 0 < value < 0.5 for value in pfas):
        raise ValueError("Pfa sweep values must be finite probabilities")
    if any(right >= left for left, right in zip(pfas, pfas[1:])):
        raise ValueError("Pfa sweep must be strictly decreasing")
    if controls["design_pfa"] not in pfas:
        raise ValueError("design Pfa must appear in sweep")
    if not isinstance(scales, (tuple, list)) or not 3 <= len(scales) <= controls["max_scale_cases"]:
        raise ValueError("scale sweep case count outside reviewed bounds")
    if not all(finite_real(value) and value > 0 for value in scales):
        raise ValueError("scene scales must be finite and positive")
    if any(right <= left for left, right in zip(scales, scales[1:])):
        raise ValueError("scene scale sweep must be strictly increasing")
    if 1 not in scales:
        raise ValueError("scene scale sweep must include baseline")

    reviewed_ceilings = {
        "max_cells": 512,
        "max_training": 32,
        "max_guards": 8,
        "max_targets": 6,
        "max_probability_cases": 5,
        "max_scale_cases": 5,
        "max_figures": 5,
        "max_stored_values": 50_000,
    }
    for name, expected in reviewed_ceilings.items():
        if controls[name] != expected:
            raise ValueError(f"{name} must remain reviewed and fixed")
    estimated = (
        40 * controls["cells"]
        + 12 * controls["cells"] * len(pfas)
        + 12 * controls["cells"] * len(scales)
        + 1000
    )
    if estimated > controls["max_stored_values"]:
        raise ValueError("controls exceed stored-value ceiling")


def ca_cfar(
    profile: list[float], training_per_side: int, guards_per_side: int, pfa: float
) -> dict[str, object]:
    training_count = 2 * training_per_side
    alpha = training_count * (pfa ** (-1 / training_count) - 1)
    first = training_per_side + guards_per_side
    last = len(profile) - training_per_side - guards_per_side
    estimate: list[float | None] = [None] * len(profile)
    threshold: list[float | None] = [None] * len(profile)
    detections = [False] * len(profile)
    references: dict[int, tuple[int, ...]] = {}
    for cut in range(first, last):
        left = tuple(range(cut - guards_per_side - training_per_side, cut - guards_per_side))
        right = tuple(range(cut + guards_per_side + 1, cut + guards_per_side + training_per_side + 1))
        indices = left + right
        references[cut] = indices
        estimate[cut] = sum(profile[index] for index in indices) / training_count
        threshold[cut] = alpha * estimate[cut]
        detections[cut] = profile[cut] > threshold[cut]
    return {
        "training_count": training_count,
        "alpha": alpha,
        "first": first,
        "last": last,
        "estimate": estimate,
        "threshold": threshold,
        "detections": detections,
        "references": references,
    }


def deterministic_profile(controls: dict[str, object]) -> tuple[list[float], list[float]]:
    generator = random.Random(int(controls["seed"]))
    cells = int(controls["cells"])
    background = [
        0.65 + 0.0045 * index + 0.32 * (1 + math.sin(2 * math.pi * (index - 18) / 190))
        for index in range(1, cells + 1)
    ]
    noise = [
        complex(generator.gauss(0, 1), generator.gauss(0, 1)) / math.sqrt(2)
        for _ in range(cells)
    ]
    received = [math.sqrt(mean) * value for mean, value in zip(background, noise)]
    for cell, snr_db, phase in zip(
        controls["target_cells"], controls["target_snr_db"], controls["target_phase_rad"]
    ):
        index = int(cell) - 1
        amplitude = math.sqrt(background[index] * 10 ** (float(snr_db) / 10))
        received[index] += amplitude * complex(math.cos(float(phase)), math.sin(float(phase)))
    return background, [abs(value) ** 2 for value in received]


def broken_db_average(profile: list[float], controls: dict[str, object]) -> dict[str, object]:
    training = int(controls["training_per_side"])
    guards = int(controls["guards_per_side"])
    correct = ca_cfar(profile, training, guards, float(controls["design_pfa"]))
    estimate: list[float | None] = [None] * len(profile)
    threshold: list[float | None] = [None] * len(profile)
    detections = [False] * len(profile)
    for cut, indices in correct["references"].items():
        values = [max(profile[index], float.fromhex("0x0.0000000000001p-1022")) for index in indices]
        estimate[cut] = math.exp(sum(math.log(value) for value in values) / len(values))
        threshold[cut] = correct["alpha"] * estimate[cut]
        detections[cut] = profile[cut] > threshold[cut]
    return {"estimate": estimate, "threshold": threshold, "detections": detections}


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", re.sub(r"\.\.\.\s*", "", source))
    required = (
        "random_seed = 4501",
        "RandStream('mt19937ar', 'Seed', random_seed)",
        "close(findall(0, 'Type', 'figure', 'Tag', 'P45'))",
        "unit_complex_noise = (unit_noise_i+1i*unit_noise_q)/sqrt(2)",
        "profile_power = abs(received).^2",
        "training_cell_count = 2*training_cells_per_side",
        "design_false_alarm_probability^(-1/training_cell_count)-1",
        "leading_training_cells = cut_cell-guard_cells_per_side-training_cells_per_side:cut_cell-guard_cells_per_side-1",
        "lagging_training_cells = cut_cell+guard_cells_per_side+1:cut_cell+guard_cells_per_side+training_cells_per_side",
        "assert(all(abs(training_cells-cut_cell) > guard_cells_per_side)); noise_estimate_power(cut_cell) = mean(profile_power(training_cells))",
        "threshold_power(cut_cell) = cfar_scale_factor*noise_estimate_power(cut_cell)",
        "profile_power(cut_cell) > threshold_power(cut_cell)",
        "noise_estimate_power = nan(1, cell_count); threshold_power = nan(1, cell_count)",
        "false_alarm_probability_sweep = [1e-2 1e-3 1e-4]",
        "background_scale_sweep = [0.5 1 2]",
        "scaled_profile_power = background_scale*profile_power",
        "assert(isequal(background_sweep_detection_mask(background_index, :), detection_mask))",
        "training_power_db = 10*log10(max(profile_power(training_cells), realmin))",
        "10^(mean(training_power_db)/10)",
        "broken_claim_is_valid = false",
        "recovery_noise_estimate_power(cut_cell) = mean(profile_power(training_cells))",
        "recovery_exact = isequaln(recovery_noise_estimate_power, noise_estimate_power)",
        "estimated_stored_numeric_values <= max_stored_numeric_values",
        "max_stored_numeric_values == 50000",
        "results.background_sweep_threshold_ratio",
        "results.broken_threshold_ratio",
        "results.recovery_exact",
    )
    return [marker for marker in required if marker not in compact]


class P45ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.docs = {
            name: (MODULE / name).read_text(encoding="utf-8")
            for name in ARTIFACTS
            if name != "experiment.m"
        }
        cls.controls = canonical_controls()
        cls.background, cls.profile = deterministic_profile(cls.controls)
        cls.oracle = ca_cfar(
            cls.profile,
            int(cls.controls["training_per_side"]),
            int(cls.controls["guards_per_side"]),
            float(cls.controls["design_pfa"]),
        )

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self):
        self.assertEqual(validate_p45_contract(MODULE, self.manifest), [])
        entries = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(entries["P44"]["status"], "implemented")
        self.assertEqual(entries["P45"], EXPECTED_IDENTITY)
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
            self.assertIn("P45 missing checks.md", validate_p45_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("", encoding="utf-8")
            self.assertIn("P45 empty checks.md", validate_p45_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p45_contract(MODULE, None))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p45_contract(MODULE, {"modules": [None]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn(
            "expected one P45 manifest entry, found 2",
            validate_p45_contract(MODULE, duplicate),
        )
        for key in EXPECTED_IDENTITY:
            drifted = copy.deepcopy(self.manifest)
            next(item for item in drifted["modules"] if item["id"] == "P45")[key] = "drift"
            errors = validate_p45_contract(MODULE, drifted)
            if key == "id":
                self.assertTrue(any("one P45 manifest entry" in error for error in errors))
            else:
                self.assertTrue(any(key in error for error in errors), key)

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self):
        validate_controls()
        invalid = (
            {"seed": True},
            {"seed": 4502},
            {"cells": 255},
            {"range_resolution_m": True},
            {"range_resolution_m": 0},
            {"training_per_side": 1},
            {"training_per_side": 33},
            {"guards_per_side": 0},
            {"guards_per_side": 9},
            {"design_pfa": math.nan},
            {"design_pfa": 0},
            {"design_pfa": 0.5},
            {"target_cells": (14, 132, 211)},
            {"target_cells": (62, 62, 211)},
            {"target_cells": (62, 70, 211)},
            {"target_cells": (62.0, 132, 211)},
            {"target_snr_db": (19, math.inf, 20)},
            {"target_phase_rad": (0.2, True, 1.1)},
            {"target_phase_rad": (0.2, 1.1)},
            {"pfa_sweep": (1e-2, 1e-2, 1e-4)},
            {"pfa_sweep": (1e-2, math.nan, 1e-4)},
            {"pfa_sweep": (1e-2, 1e-4, 1e-3)},
            {"scale_sweep": (0.5, 0, 2)},
            {"scale_sweep": (0.5, 2, 1)},
            {"scale_sweep": (0.5, 2, 3)},
            {"tolerance": 0},
            {"max_stored_values": 49_999},
            {"max_figures": 6},
            {"unknown": 1},
        )
        for controls in invalid:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_independent_oracle_checks_alpha_references_edges_and_truth_isolation(self):
        training = int(self.controls["training_per_side"])
        guards = int(self.controls["guards_per_side"])
        expected_alpha = 2 * training * (
            float(self.controls["design_pfa"]) ** (-1 / (2 * training)) - 1
        )
        self.assertAlmostEqual(self.oracle["alpha"], expected_alpha)
        self.assertEqual(self.oracle["training_count"], 24)
        eligible_count = int(self.controls["cells"]) - 2 * (training + guards)
        self.assertEqual(self.oracle["last"] - self.oracle["first"], eligible_count)
        for cut, references in self.oracle["references"].items():
            self.assertEqual(len(references), 24)
            self.assertNotIn(cut, references)
            self.assertTrue(all(abs(index - cut) > guards for index in references))
        for index in range(len(self.profile)):
            eligible = self.oracle["first"] <= index < self.oracle["last"]
            self.assertEqual(self.oracle["threshold"][index] is not None, eligible)
            if not eligible:
                self.assertFalse(self.oracle["detections"][index])
        replay = ca_cfar(self.profile, training, guards, float(self.controls["design_pfa"]))
        self.assertEqual(replay, self.oracle)

    def test_pfa_sweep_and_uniform_scene_scale_have_expected_invariants(self):
        pfa_cases = [
            ca_cfar(
                self.profile,
                int(self.controls["training_per_side"]),
                int(self.controls["guards_per_side"]),
                pfa,
            )
            for pfa in self.controls["pfa_sweep"]
        ]
        self.assertTrue(
            all(right["alpha"] > left["alpha"] for left, right in zip(pfa_cases, pfa_cases[1:]))
        )
        counts = [sum(case["detections"]) for case in pfa_cases]
        self.assertTrue(all(right <= left for left, right in zip(counts, counts[1:])))

        baseline = self.oracle
        for scale in self.controls["scale_sweep"]:
            scaled = ca_cfar(
                [scale * value for value in self.profile],
                int(self.controls["training_per_side"]),
                int(self.controls["guards_per_side"]),
                float(self.controls["design_pfa"]),
            )
            for index in baseline["references"]:
                self.assertAlmostEqual(
                    scaled["threshold"][index], scale * baseline["threshold"][index], places=11
                )
            self.assertEqual(scaled["detections"], baseline["detections"])

    def test_one_profile_adapts_between_local_power_regions(self):
        region_length = 80
        local_scale = 10.0
        low_region = [1.0 + 0.05 * ((7 * index) % 11) for index in range(region_length)]
        target_index = 40
        low_region[target_index] = 20.0
        profile = low_region + [local_scale * value for value in low_region]

        result = ca_cfar(
            profile,
            int(self.controls["training_per_side"]),
            int(self.controls["guards_per_side"]),
            float(self.controls["design_pfa"]),
        )
        window_radius = int(self.controls["training_per_side"]) + int(
            self.controls["guards_per_side"]
        )
        paired_low_cuts = range(window_radius, region_length - window_radius)
        for low_cut in paired_low_cuts:
            high_cut = low_cut + region_length
            self.assertAlmostEqual(
                result["threshold"][high_cut],
                local_scale * result["threshold"][low_cut],
                places=11,
            )
            self.assertEqual(
                result["detections"][high_cut], result["detections"][low_cut]
            )

        self.assertTrue(result["detections"][target_index])
        self.assertTrue(result["detections"][target_index + region_length])

    def test_broken_db_geometric_mean_bias_and_recomputed_recovery(self):
        broken = broken_db_average(self.profile, self.controls)
        eligible = self.oracle["references"].keys()
        for index in eligible:
            self.assertLessEqual(broken["estimate"][index], self.oracle["estimate"][index])
            self.assertLessEqual(broken["threshold"][index], self.oracle["threshold"][index])
            if self.oracle["detections"][index]:
                self.assertTrue(broken["detections"][index])
        self.assertGreaterEqual(sum(broken["detections"]), sum(self.oracle["detections"]))
        recovered = ca_cfar(
            list(self.profile),
            int(self.controls["training_per_side"]),
            int(self.controls["guards_per_side"]),
            float(self.controls["design_pfa"]),
        )
        self.assertEqual(recovered["estimate"], self.oracle["estimate"])
        self.assertEqual(recovered["threshold"], self.oracle["threshold"])
        self.assertEqual(recovered["detections"], self.oracle["detections"])

    def test_source_contract_mutations_and_base_matlab_compatibility(self):
        self.assertEqual(source_contract_errors(self.source), [])
        self.assertEqual(self.source.count("figure('Name'"), 5)
        banned = (
            "phased.",
            "dsp.",
            "cfardetector",
            "movmean(",
            "exprnd(",
            "awgn(",
            "wgn(",
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
            self.source.replace("2*training_cells_per_side", "training_cells_per_side", 1),
            self.source.replace("^(-1/training_cell_count)-1", "^(1/training_cell_count)-1", 1),
            self.source.replace("noise_estimate_power(cut_cell) = mean(profile_power(training_cells))", "noise_estimate_power(cut_cell) = profile_power(cut_cell)", 1),
            self.source.replace("threshold_power = nan(1, cell_count)", "threshold_power = zeros(1, cell_count)", 1),
            self.source.replace("broken_claim_is_valid = false", "broken_claim_is_valid = true", 1),
            self.source.replace("max_stored_numeric_values == 50000", "max_stored_numeric_values > 0", 1),
        )
        for mutated in mutations:
            self.assertTrue(source_contract_errors(mutated))

    def test_controls_precede_allocation_and_loops_and_resources_are_bounded(self):
        validation = self.source.index("%% Reject malformed")
        first_allocation = self.source.index("unit_noise_i = randn")
        first_figure = self.source.index("figure('Name'")
        self.assertLess(validation, first_allocation)
        self.assertLess(first_allocation, first_figure)
        self.assertIn("estimated_stored_numeric_values <= max_stored_numeric_values", self.source)
        self.assertIn("results.excluded_edge_count", self.source)
        self.assertIn("results.max_figure_groups", self.source)
        self.assertNotIn("\nwhile ", self.source)
        self.assertLessEqual(len(re.findall(r"^for ", self.source, re.MULTILINE)), 10)

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
            next(item for item in manifest["modules"] if item["id"] == "P45")["status"] = "scaffolded"
        (fixture / "curriculum/modules.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        return fixture

    def test_isolated_cli_timeout_and_scaffold_rollback_compatibility(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        fixture = self._fixture()
        result = subprocess.run(
            [str(fixture / "bin/learn"), "start", "45"],
            cwd=fixture,
            text=True,
            capture_output=True,
            env=os.environ.copy(),
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("P45 — Implement 1-D Cell-Averaging CFAR", result.stdout)
        self.assertIn("status: implemented", result.stdout)
        rolled = self._fixture(rolled_back=True)
        rollback_result = subprocess.run(
            [str(rolled / "bin/learn"), "start", "45"],
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
            "p44",
            "square-law",
            "exponential",
            "linear power",
            "guard",
            "training",
            "private seed",
            "base matlab",
            "bounded",
            "edge",
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

    def test_p45_only_rollback_preserves_neighbor_identity(self):
        rolled = copy.deepcopy(self.manifest)
        neighbors_before = {
            item["id"]: copy.deepcopy(item)
            for item in rolled["modules"]
            if item["id"] in {"P44", "P46"}
        }
        next(item for item in rolled["modules"] if item["id"] == "P45")["status"] = "scaffolded"
        neighbors_after = {
            item["id"]: item for item in rolled["modules"] if item["id"] in {"P44", "P46"}
        }
        self.assertEqual(neighbors_after, neighbors_before)
        self.assertTrue(any("status" in error for error in validate_p45_contract(MODULE, rolled)))

    def test_public_catalogs_describe_p45_without_freezing_future_state(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 45 applies an explicit square-law CA-CFAR", readme)
        self.assertIn("Project 45 follows P44", start_here)
        self.assertRegex(module_index, r"\| \[P45\].*\| implemented \| 5 \|")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self):
        evidence = ROOT / "docs/evidence/P45-2026-08-04.md"
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
        for result_marker in (
            "contract profile: exit 0",
            "quick profile: exit 0; 738 tests passed",
            "full repository verification: exit 0",
            "focused P45 command: exit 0; 14 tests passed",
            "docs/evidence/local/verify-20260804-143509.log",
            "allowed-path audit found only P45",
        ):
            self.assertIn(result_marker, text)
        self.assertNotIn("recorded after the final verification run", text.lower())
        self.assertIn("matlab and octave did not run", re.sub(r"\s+", " ", text.lower()))
        data = evidence.read_bytes()
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))
        self.assertNotIn(b"\r", data)


if __name__ == "__main__":
    unittest.main()
