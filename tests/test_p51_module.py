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
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/51-stress-cfar-with-clutter-edges-sidelobes-and-multiple-targets"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Where do standard CFAR assumptions break?"
EXPECTED_IDENTITY = {
    "number": 51,
    "id": "P51",
    "title": "Stress CFAR with Clutter Edges, Sidelobes, and Multiple Targets",
    "guiding_question": QUESTION,
    "phase": 5,
    "phase_title": "Detection and CFAR",
    "slug": "stress-cfar-with-clutter-edges-sidelobes-and-multiple-targets",
    "folder": "modules/51-stress-cfar-with-clutter-edges-sidelobes-and-multiple-targets",
    "status": "implemented",
    "implementation_batch": "P51",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def validate_p51_contract(module: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P51 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P51 empty {artifact}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        errors.append("manifest modules must be a list")
        return errors
    if not all(isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("manifest module entries must be objects")
        return errors
    entries = [entry for entry in manifest["modules"] if entry.get("id") == "P51"]
    if len(entries) != 1:
        errors.append(f"expected one P51 manifest entry, found {len(entries)}")
        return errors
    for key, expected in EXPECTED_IDENTITY.items():
        if entries[0].get(key) != expected:
            errors.append(f"P51 {key} mismatch")
    return errors


def validate_controls(**overrides: object) -> None:
    controls: dict[str, object] = {
        "seed": 5101,
        "cells": 256,
        "spacing": 30.0,
        "pfa": 1e-3,
        "training": 12,
        "guard": 3,
        "rank": 18,
        "iterations": 80,
        "edge": 145,
        "targets": (70, 82, 141, 205, 194, 198, 212, 216),
        "target_snr_db": (28.0, 14.0, 14.0, 13.0, 20.0, 20.0, 20.0, 20.0),
        "contrast_sweep": (0.0, 6.0, 12.0, 18.0),
        "count_sweep": (0, 2, 4, 6, 7, 8),
        "trials": 12000,
        "max_cells": 320,
        "max_training": 24,
        "max_guard": 8,
        "max_targets": 10,
        "max_cases": 8,
        "max_trials": 15000,
        "max_iterations": 100,
        "max_random": 400000,
        "max_stored": 1200000,
        "max_visits": 2000000,
        "max_figures": 7,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    integer_names = (
        "seed", "cells", "training", "guard", "rank", "iterations", "edge",
        "trials", "max_cells", "max_training", "max_guard", "max_targets",
        "max_cases", "max_trials", "max_iterations", "max_random", "max_stored",
        "max_visits", "max_figures",
    )
    if not all(integer(controls[name]) for name in integer_names):
        raise ValueError("integer controls")
    expected_ceilings = {
        "max_cells": 320,
        "max_training": 24,
        "max_guard": 8,
        "max_targets": 10,
        "max_cases": 8,
        "max_trials": 15000,
        "max_iterations": 100,
        "max_random": 400000,
        "max_stored": 1200000,
        "max_visits": 2000000,
        "max_figures": 7,
    }
    if any(controls[name] != expected for name, expected in expected_ceilings.items()):
        raise ValueError("resource ceiling drift")
    if controls["seed"] != 5101 or not 128 <= controls["cells"] <= controls["max_cells"]:
        raise ValueError("determinism or cell count")
    if not finite_real(controls["spacing"]) or controls["spacing"] <= 0:
        raise ValueError("spacing")
    if not finite_real(controls["pfa"]) or not 1e-6 <= controls["pfa"] < 0.1:
        raise ValueError("Pfa")
    if not 2 <= controls["training"] <= controls["max_training"]:
        raise ValueError("training")
    if not 1 <= controls["guard"] <= controls["max_guard"]:
        raise ValueError("guard")
    training_count = 2 * controls["training"]
    half_width = controls["training"] + controls["guard"]
    if not 1 <= controls["rank"] <= training_count:
        raise ValueError("rank")
    if not half_width < controls["edge"] <= controls["cells"] - half_width:
        raise ValueError("edge")
    targets = controls["targets"]
    snr = controls["target_snr_db"]
    if not isinstance(targets, (tuple, list)) or not isinstance(snr, (tuple, list)):
        raise ValueError("target shape")
    if not targets or len(targets) > controls["max_targets"] or len(set(targets)) != len(targets):
        raise ValueError("target count")
    if not all(integer(value) and half_width < value <= controls["cells"] - half_width for value in targets):
        raise ValueError("target cells")
    if len(snr) != len(targets) or not all(finite_real(value) and -20 <= value <= 40 for value in snr):
        raise ValueError("target powers")
    contrast = controls["contrast_sweep"]
    if (
        not isinstance(contrast, (tuple, list))
        or not 3 <= len(contrast) <= controls["max_cases"]
        or not all(finite_real(value) and 0 <= value <= 24 for value in contrast)
        or any(a >= b for a, b in zip(contrast, contrast[1:]))
        or 12 not in contrast
    ):
        raise ValueError("contrast sweep")
    counts = controls["count_sweep"]
    capacity = training_count - controls["rank"]
    if (
        not isinstance(counts, (tuple, list))
        or not 3 <= len(counts) <= controls["max_cases"]
        or not all(integer(value) and 0 <= value <= training_count for value in counts)
        or counts[0] != 0
        or any(a >= b for a, b in zip(counts, counts[1:]))
        or capacity not in counts
        or capacity + 1 not in counts
    ):
        raise ValueError("count sweep")
    if not 40 <= controls["iterations"] <= controls["max_iterations"]:
        raise ValueError("iterations")
    if not 1000 <= controls["trials"] <= controls["max_trials"]:
        raise ValueError("trials")
    generated = controls["cells"] + controls["trials"] * (training_count + 2)
    stored = 40 * controls["cells"] + controls["trials"] * (3 * training_count + 12)
    visits = (
        (1 + len(contrast)) * controls["cells"] * training_count
        + len(counts) * controls["trials"] * training_count
    )
    if generated > controls["max_random"] or stored > controls["max_stored"] or visits > controls["max_visits"]:
        raise ValueError("resource budget")


def variant_pfa(alpha: float, training_per_side: int, variant: str) -> float:
    if not finite_real(alpha) or alpha < 0:
        raise ValueError("alpha")
    if not integer(training_per_side) or training_per_side < 1:
        raise ValueError("training")
    if variant not in {"GO", "SO"}:
        raise ValueError("variant")
    term_sum = 0.0
    for order in range(training_per_side):
        log_term = (
            (training_per_side + order) * math.log(training_per_side)
            + math.lgamma(training_per_side + order)
            - math.lgamma(training_per_side)
            - math.lgamma(order + 1)
            - (training_per_side + order) * math.log(2 * training_per_side + alpha)
        )
        term_sum += math.exp(log_term)
    so_probability = 2 * term_sum
    if variant == "SO":
        return so_probability
    return 2 * (training_per_side / (training_per_side + alpha)) ** training_per_side - so_probability


def os_pfa(alpha: float, training_count: int, rank: int) -> float:
    if not finite_real(alpha) or alpha < 0:
        raise ValueError("alpha")
    if not integer(training_count) or training_count < 1:
        raise ValueError("training")
    if not integer(rank) or not 1 <= rank <= training_count:
        raise ValueError("rank")
    return math.exp(
        sum(
            math.log(training_count - offset)
            - math.log(training_count - offset + alpha)
            for offset in range(rank)
        )
    )


def calibrated_scale(probability, requested_pfa: float, iterations: int = 100) -> float:
    if not finite_real(requested_pfa) or not 0 < requested_pfa < 1:
        raise ValueError("Pfa")
    if not integer(iterations) or iterations < 1:
        raise ValueError("iterations")
    lower, upper = 0.0, 1.0
    for _ in range(32):
        if probability(upper) <= requested_pfa:
            break
        upper *= 2
    else:
        raise ValueError("bracket")
    for _ in range(iterations):
        middle = (lower + upper) / 2
        if probability(middle) > requested_pfa:
            lower = middle
        else:
            upper = middle
    return (lower + upper) / 2


def detector_scales(training_per_side: int = 12, rank: int = 18, pfa: float = 1e-3) -> tuple[float, ...]:
    training_count = 2 * training_per_side
    ca = training_count * (pfa ** (-1 / training_count) - 1)
    go = calibrated_scale(lambda value: variant_pfa(value, training_per_side, "GO"), pfa)
    so = calibrated_scale(lambda value: variant_pfa(value, training_per_side, "SO"), pfa)
    os_scale = calibrated_scale(lambda value: os_pfa(value, training_count, rank), pfa)
    return ca, go, so, os_scale


def cut_decisions(
    cut_power: float,
    leading: list[float],
    lagging: list[float],
    rank: int = 18,
    scales: tuple[float, ...] | None = None,
) -> tuple[list[float], list[bool]]:
    if not finite_real(cut_power) or cut_power < 0:
        raise ValueError("CUT")
    if not leading or len(leading) != len(lagging):
        raise ValueError("equal nonempty sides")
    refs = leading + lagging
    if any(not finite_real(value) or value < 0 for value in refs):
        raise ValueError("references")
    if not integer(rank) or not 1 <= rank <= len(refs):
        raise ValueError("rank")
    if scales is None:
        scales = detector_scales(len(leading), rank)
    if len(scales) != 4 or any(not finite_real(value) or value < 0 for value in scales):
        raise ValueError("scales")
    statistics = (
        sum(refs) / len(refs),
        max(sum(leading) / len(leading), sum(lagging) / len(lagging)),
        min(sum(leading) / len(leading), sum(lagging) / len(lagging)),
        sorted(refs)[rank - 1],
    )
    thresholds = [scale * statistic for scale, statistic in zip(scales, statistics)]
    return thresholds, [cut_power > threshold for threshold in thresholds]


def apply_profile(power: list[float], training: int = 12, guard: int = 3, rank: int = 18):
    if not power or any(not finite_real(value) or value < 0 for value in power):
        raise ValueError("power profile")
    half_width = training + guard
    if len(power) <= 2 * half_width:
        raise ValueError("stencil does not fit")
    scales = detector_scales(training, rank)
    thresholds = [[math.nan] * 4 for _ in power]
    detections = [[False] * 4 for _ in power]
    for cut in range(half_width, len(power) - half_width):
        leading = power[cut - guard - training : cut - guard]
        lagging = power[cut + guard + 1 : cut + guard + 1 + training]
        thresholds[cut], detections[cut] = cut_decisions(power[cut], leading, lagging, rank, scales)
    return thresholds, detections


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", "", source)
    required = (
        "random_seed=5101;",
        "private_stream=RandStream('mt19937ar','Seed',random_seed);",
        "unit_background_power=-log(max(rand(private_stream,range_cell_count,1),realmin));",
        "background_mean_power=low_side_mean_power.*",
        "leading_mean_power(cut)=sum(received_power(leading_cells))/training_cells_per_side;",
        "lagging_mean_power(cut)=sum(received_power(lagging_cells))/training_cells_per_side;",
        "ca_mean_power(cut)=sum(reference_power)/training_cell_count;",
        "sorted_reference_power=sort(reference_power,'ascend');",
        "os_order_power(cut)=sorted_reference_power(os_rank);",
        "received_power(cut)>ca_threshold_power(cut);",
        "clutter_contrast_sweep_db=[061218];",
        "candidate_multiplier=10^(clutter_contrast_sweep_db(contrast_index)/10);",
        "contrast_edge_crossings(contrast_index,:)=sum(...candidate_detection(edge_evaluation_cells,:)&...~truth_target_mask(edge_evaluation_cells),1);",
        "crowded_count_sweep=[024678];",
        "disagreement_causes=cell(numel(disagreement_cells),1);",
        "broken_shared_scale_factor=ca_scale_factor;",
        "broken_equal_pfa_claim_is_valid=false;",
        "recovered_variant_specific_calibration=",
        "modeled_target_response_power=zeros(range_cell_count,1);",
        "response_artifact_mask=modeled_target_response_power>0&~truth_target_mask;",
        "target_miss_cause_matrix=cell(numel(target_cells),4);",
        "h0_crossing_category_counts=zeros(4,numel(h0_category_names));",
        "response_artifact_crossing_counts=zeros(4,numel(target_cells));",
        "numel(crowded_count_sweep)*sweep_trial_count*training_cell_count;",
        "results.max_figure_groups=max_figure_groups;",
    )
    return [marker for marker in required if marker not in compact]


def clutter_contrast_oracle() -> dict[str, object]:
    contrasts_db = (0.0, 6.0, 12.0, 18.0)
    scales = detector_scales()
    low_side_target_decisions = []
    high_side_background_decisions = []
    for contrast_db in contrasts_db:
        high_side_power = 10 ** (contrast_db / 10)
        leading = [1.0] * 12
        lagging = [high_side_power] * 12
        _, low_decisions = cut_decisions(
            50.0, leading, lagging, scales=scales
        )
        _, high_decisions = cut_decisions(
            2 * high_side_power, leading, lagging, scales=scales
        )
        low_side_target_decisions.append(low_decisions)
        high_side_background_decisions.append(high_decisions)
    return {
        "contrasts_db": contrasts_db,
        "low_side_target_decisions": low_side_target_decisions,
        "high_side_background_decisions": high_side_background_decisions,
    }


@lru_cache(maxsize=1)
def contamination_oracle() -> dict[str, object]:
    generator = random.Random(5101)
    scales = detector_scales()
    counts = (0, 2, 4, 6, 7, 8)
    trials = 10000
    detected = [[0] * 4 for _ in counts]
    order = (0, 12, 1, 13, 2, 14, 3, 15, 4, 16, 5, 17, 6, 18, 7, 19)
    for _ in range(trials):
        refs = [-math.log1p(-generator.random()) for _ in range(24)]
        noise_i = generator.gauss(0, 1 / math.sqrt(2))
        noise_q = generator.gauss(0, 1 / math.sqrt(2))
        amplitude = math.sqrt(10 ** (13 / 10))
        cut_power = (noise_i + amplitude) ** 2 + noise_q**2
        for count_index, count in enumerate(counts):
            contaminated = refs.copy()
            for column in order[:count]:
                contaminated[column] += 100
            _, decisions = cut_decisions(cut_power, contaminated[:12], contaminated[12:], scales=scales)
            for detector, decision in enumerate(decisions):
                detected[count_index][detector] += decision
    probabilities = [[count / trials for count in row] for row in detected]
    return {"counts": counts, "probabilities": probabilities}


class P51ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self):
        self.assertEqual(validate_p51_contract(MODULE, self.manifest), [])
        p50 = next(item for item in self.manifest["modules"] if item["id"] == "P50")
        self.assertEqual(p50["status"], "implemented")
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
            self.assertIn("P51 missing checks.md", validate_p51_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("\n", encoding="utf-8")
            self.assertIn("P51 empty checks.md", validate_p51_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p51_contract(MODULE, {}))
        self.assertIn("manifest module entries must be objects", validate_p51_contract(MODULE, {"modules": ["P51"]}))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P51 manifest entry, found 2", validate_p51_contract(MODULE, duplicate))
        for key, expected in EXPECTED_IDENTITY.items():
            drifted = copy.deepcopy(self.manifest)
            next(item for item in drifted["modules"] if item["id"] == "P51")[key] = f"wrong-{expected}"
            self.assertTrue(validate_p51_contract(MODULE, drifted))

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self):
        validate_controls()
        invalid = (
            {"unexpected": 1}, {"seed": True}, {"seed": 5102}, {"cells": 127},
            {"spacing": math.nan}, {"pfa": 0.0}, {"pfa": 0.1}, {"training": 1},
            {"guard": 9}, {"rank": 25}, {"edge": 15}, {"targets": (70, 70)},
            {"targets": (14, 82)}, {"target_snr_db": (28.0,)},
            {"target_snr_db": (28.0, 14.0, 14.0, 13.0, 20.0, 20.0, 20.0, math.inf)},
            {"contrast_sweep": (0.0, 18.0, 12.0)}, {"contrast_sweep": (0.0, 6.0, 18.0)},
            {"contrast_sweep": tuple(range(9))}, {"count_sweep": (0, 2, 4, 7, 8)},
            {"count_sweep": (0, 2, 4, 6, 8)}, {"trials": 15001}, {"iterations": 39},
            {"max_cells": 321}, {"max_random": 399999}, {"max_stored": 1000000},
            {"max_visits": 300000},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                validate_controls(**overrides)

    def test_exact_equal_pfa_calibration_and_broken_common_scale(self):
        ca, go, so, os_scale = detector_scales()
        self.assertAlmostEqual(ca, 8.004514371919775, places=12)
        self.assertAlmostEqual(go, 7.089038451813456, places=12)
        self.assertAlmostEqual(so, 10.480855745946773, places=12)
        self.assertAlmostEqual(os_scale, 6.502430709645976, places=12)
        calibrated = (
            (1 + ca / 24) ** -24,
            variant_pfa(go, 12, "GO"),
            variant_pfa(so, 12, "SO"),
            os_pfa(os_scale, 24, 18),
        )
        for actual in calibrated:
            self.assertAlmostEqual(actual, 1e-3, places=14)
        broken = (variant_pfa(ca, 12, "GO"), variant_pfa(ca, 12, "SO"), os_pfa(ca, 24, 18))
        self.assertAlmostEqual(broken[0], 0.0004729226614182537, places=15)
        self.assertAlmostEqual(broken[1], 0.0038688671274318283, places=15)
        self.assertAlmostEqual(broken[2], 0.00028446438594153275, places=15)
        for malformed in ((-1.0, 12, "GO"), (1.0, 0, "SO"), (1.0, 12, "CA")):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                variant_pfa(*malformed)
        for malformed in ((-1.0, 24, 18), (1.0, True, 18), (1.0, 24, 25)):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                os_pfa(*malformed)

    def test_handcrafted_edge_and_one_sided_contamination_explain_disagreements(self):
        edge_thresholds, edge_decisions = cut_decisions(50.0, [1.0] * 12, [10.0] * 12)
        self.assertEqual(edge_decisions, [True, False, True, False])
        self.assertGreater(edge_thresholds[1], 50)
        self.assertLess(edge_thresholds[2], 50)
        contaminated = [100.0] * 4 + [1.0] * 8
        contamination_thresholds, contamination_decisions = cut_decisions(20.0, contaminated, [1.0] * 12)
        self.assertEqual(contamination_decisions, [False, False, True, True])
        self.assertGreater(contamination_thresholds[0], 20)
        self.assertGreater(contamination_thresholds[1], 20)
        self.assertLess(contamination_thresholds[2], 20)
        self.assertLess(contamination_thresholds[3], 20)

    def test_clutter_contrast_oracle_exposes_go_so_edge_tradeoff(self):
        oracle = clutter_contrast_oracle()
        self.assertEqual(oracle["contrasts_db"], (0.0, 6.0, 12.0, 18.0))
        low_target = oracle["low_side_target_decisions"]
        high_background = oracle["high_side_background_decisions"]
        self.assertEqual(low_target[:2], [[True] * 4, [True] * 4])
        self.assertEqual(
            low_target[2:],
            [[False, False, True, False], [False, False, True, False]],
        )
        self.assertEqual(high_background[:2], [[False] * 4, [False] * 4])
        self.assertEqual(
            high_background[2:],
            [[False, False, True, False], [False, False, True, False]],
        )

    def test_os_capacity_boundary_and_malformed_detector_inputs(self):
        scales = detector_scales()
        for contaminator_count, expected_os in ((6, True), (7, False)):
            refs = [1.0] * (24 - contaminator_count) + [100.0] * contaminator_count
            _, decisions = cut_decisions(20.0, refs[:12], refs[12:], scales=scales)
            self.assertEqual(decisions[3], expected_os)
        malformed = (
            (-1.0, [1.0] * 12, [1.0] * 12, 18, None),
            (20.0, [], [], 18, None),
            (20.0, [1.0], [1.0, 1.0], 1, None),
            (20.0, [math.nan] * 12, [1.0] * 12, 18, None),
            (20.0, [1.0] * 12, [1.0] * 12, 25, None),
            (20.0, [1.0] * 12, [1.0] * 12, 18, (1.0,)),
        )
        for cut, leading, lagging, rank, scales_value in malformed:
            with self.subTest(rank=rank, scales=scales_value), self.assertRaises(ValueError):
                cut_decisions(cut, leading, lagging, rank, scales_value)

    def test_profile_edges_and_uniform_scale_invariance(self):
        generator = random.Random(5101)
        power = [-math.log1p(-generator.random()) for _ in range(80)]
        power[40] += 100
        threshold, detection = apply_profile(power)
        scaled_threshold, scaled_detection = apply_profile([4 * value for value in power])
        self.assertEqual(detection, scaled_detection)
        for index in list(range(15)) + list(range(65, 80)):
            self.assertEqual(detection[index], [False] * 4)
            self.assertTrue(all(math.isnan(value) for value in threshold[index]))
        for index in range(15, 65):
            for detector in range(4):
                self.assertAlmostEqual(scaled_threshold[index][detector], 4 * threshold[index][detector], places=11)
        with self.assertRaises(ValueError):
            apply_profile([])
        with self.assertRaises(ValueError):
            apply_profile([1.0, math.inf])
        with self.assertRaises(ValueError):
            apply_profile([1.0] * 30)

    def test_paired_target_density_oracle_crosses_os_capacity(self):
        oracle = contamination_oracle()
        counts = oracle["counts"]
        probabilities = oracle["probabilities"]
        self.assertEqual(counts, (0, 2, 4, 6, 7, 8))
        at_six = probabilities[counts.index(6)]
        at_seven = probabilities[counts.index(7)]
        self.assertGreater(at_six[3], 0.35)
        self.assertLess(at_seven[3], 0.05)
        self.assertGreater(at_six[3], at_six[0] + 0.25)
        self.assertGreater(probabilities[0][0], 0.9)
        self.assertGreater(probabilities[0][3], 0.9)

    def test_source_is_seeded_transparent_bounded_and_mutation_sensitive(self):
        self.assertEqual(source_contract_errors(self.source), [])
        controls_end = self.source.index("%% Calibrate each statistic")
        first_random = self.source.index("private_stream =")
        self.assertLess(controls_end, first_random)
        self.assertIn("estimated_generated_random_values", self.source[:controls_end])
        self.assertIn("estimated_stored_numeric_values", self.source[:controls_end])
        self.assertIn("estimated_training_sample_visits", self.source[:controls_end])
        self.assertIn("numel(crowded_count_sweep)*sweep_trial_count", self.source[:controls_end])
        self.assertEqual(self.source.count("figure('Name'"), 7)
        self.assertNotRegex(
            self.source.lower(),
            r"\b(?:phased\.|cfardetector\w*|ordfilt\w*\s*\(|movmean\s*\(|awgn\s*\(|"
            r"parfor\b|fopen\s*\(|webread\s*\(|system\s*\(|timer\s*\(|rng\s*\()",
        )
        self.assertNotRegex(self.source, r"(?mi)^\s*while\b")
        for marker in (
            "ca_mean_power(cut) = sum(reference_power)/training_cell_count;",
            "sorted_reference_power = sort(reference_power, 'ascend');",
            "os_order_power(cut) = sorted_reference_power(os_rank);",
            "clutter_contrast_sweep_db = [0 6 12 18];",
            "candidate_multiplier = 10^(clutter_contrast_sweep_db(contrast_index)/10);",
            "crowded_count_sweep = [0 2 4 6 7 8];",
            "broken_shared_scale_factor = ca_scale_factor;",
            "broken_equal_pfa_claim_is_valid = false;",
            "response_artifact_mask = modeled_target_response_power > 0 & ~truth_target_mask;",
            "target_miss_cause_matrix = cell(numel(target_cells), 4);",
        ):
            mutated = self.source.replace(marker, "mutated", 1)
            self.assertTrue(source_contract_errors(mutated), marker)

    def test_docs_cover_model_sweeps_failure_recovery_limits_and_teach_back(self):
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        combined = "\n".join((readme, lesson, walkthrough, checks))
        normalized = re.sub(r"\s+", " ", combined)
        for phrase in (
            QUESTION, "linear square-law power", "CA", "GO", "SO", "OS",
            "same nominal homogeneous Pfa", "clutter edge", "sidelobe", "weak neighbor",
            "nonuniform noise", "Expected observation", "Sweep 1", "Sweep 2",
            "intentionally broken", "Recovery", "Ctrl+C", "Short teach-back rubric",
            "no calibrated test", "P45", "P48", "P49", "P50", "P52",
        ):
            self.assertIn(phrase, normalized)
        self.assertNotRegex(combined, r"(?i)TODO|coming soon|placeholder")
        self.assertLess(lesson.index("Start with the physical training window"), lesson.index("Four answers from the same training cells"))

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
        environment = os.environ.copy()
        environment["HOME"] = temporary.name
        process = subprocess.run(
            [str(fixture_cli), *args], cwd=fixture_root, text=True,
            capture_output=True, env=environment, timeout=10, check=False,
        )
        state_path = fixture_root / ".learning/progress.json"
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
        return process, state

    def test_isolated_cli_timeout_cancellation_and_scaffold_rollback_compatibility(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        process, state = self._run_fixture_cli(self.manifest, "start", "51")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("P51 — Stress CFAR", process.stdout)
        self.assertIn("status: implemented", process.stdout)
        self.assertEqual(state["current"], "P51")
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        self.assertIn("Ctrl+C", walkthrough)
        self.assertIn("Rerun from the top", walkthrough)
        rolled = copy.deepcopy(self.manifest)
        next(item for item in rolled["modules"] if item["id"] == "P51")["status"] = "scaffolded"
        rolled_process, _ = self._run_fixture_cli(rolled, "start", "51")
        self.assertEqual(rolled_process.returncode, 3)
        self.assertIn("awaits Portfolio batch P51", rolled_process.stdout)

    def test_default_tutor_entry_advances_from_completed_p50_without_state_loss(self):
        prior_completed = [f"P{number:02d}" for number in range(1, 51)]
        initial = {
            "schema_version": 1, "current": "P50", "completed": prior_completed,
            "notes": {"P50": "preserve this two-dimensional CFAR teach-back"},
        }
        process, state = self._run_fixture_cli(self.manifest, "start", initial_state=initial)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("P51 — Stress CFAR", process.stdout)
        self.assertEqual(state["current"], "P51")
        self.assertEqual(state["completed"], prior_completed)
        self.assertEqual(state["notes"], initial["notes"])

    def test_p51_only_rollback_preserves_neighbor_identity(self):
        rolled = copy.deepcopy(self.manifest)
        neighbors_before = {
            item["id"]: copy.deepcopy(item)
            for item in rolled["modules"] if item["id"] in {"P50", "P52"}
        }
        next(item for item in rolled["modules"] if item["id"] == "P51")["status"] = "scaffolded"
        neighbors_after = {item["id"]: item for item in rolled["modules"] if item["id"] in {"P50", "P52"}}
        self.assertEqual(neighbors_after, neighbors_before)
        self.assertTrue(any("status" in error for error in validate_p51_contract(MODULE, rolled)))

    def test_public_catalogs_describe_p51_without_freezing_future_state(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 51 combines a clutter edge", readme)
        self.assertIn("Project 51 follows P50", start_here)
        self.assertRegex(module_index, r"\| \[P51\].*\| implemented \| 5 \|")
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?i)P51\s+(?:is\s+)?(?:the\s+)?(?:latest|last|final)")
        self.assertNotRegex(source, r"(?i)P52[^\n]*remains? scaffolded")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self):
        evidence = ROOT / "docs/evidence/P51-2026-08-04.md"
        self.assertTrue(evidence.is_file())
        text = evidence.read_text(encoding="utf-8")
        for heading in (
            "## Outcome and claim boundary", "## Acceptance mapping",
            "## Physical model and independent static oracle", "## Figure and metric inventory",
            "## Focused test coverage", "## Exact commands and results",
            "## Changed and preserved invariants", "## Rollback and recovery",
            "## Residual risks and unperformed validation",
        ):
            self.assertIn(heading, text)
        for command in (
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
            "python3 -m unittest tests.test_p51_module -v",
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
