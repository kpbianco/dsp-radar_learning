from __future__ import annotations

import copy
import json
import math
import random
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/46-vary-cfar-guard-and-training-cells"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "What happens when the CFAR reference window is too small, too large, or contaminated?"
EXPECTED_IDENTITY = {
    "number": 46,
    "id": "P46",
    "title": "Vary CFAR Guard and Training Cells",
    "guiding_question": QUESTION,
    "phase": 5,
    "phase_title": "Detection and CFAR",
    "slug": "vary-cfar-guard-and-training-cells",
    "folder": "modules/46-vary-cfar-guard-and-training-cells",
    "status": "implemented",
    "implementation_batch": "P46",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p46_contract(path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        artifact = path / name
        if not artifact.is_file():
            errors.append(f"P46 missing {name}")
        elif not artifact.read_text(encoding="utf-8").strip():
            errors.append(f"P46 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P46"]
    if len(matches) != 1:
        return errors + [f"expected one P46 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P46 {key} must be {expected!r}")
    return errors


def canonical_controls() -> dict[str, object]:
    return {
        "seed": 4601,
        "cells": 256,
        "range_resolution_m": 15.0,
        "pfa": 1e-3,
        "baseline_training": 12,
        "baseline_guards": 4,
        "guard_sweep": (0, 4, 10),
        "training_sweep": (4, 12, 36),
        "training_sweep_guards": 6,
        "strong_cell": 88,
        "weak_cell": 138,
        "transition_cell": 178,
        "contaminator_cell": 126,
        "response_half_span": 18,
        "response_width": 5.0,
        "recovery_guards": 12,
        "quiet_region": tuple(range(70, 101)),
        "transition_region": tuple(range(165, 191)),
        "tolerance": 1e-10,
        "max_cells": 512,
        "max_training": 40,
        "max_guards": 12,
        "max_cases": 5,
        "max_response_half_span": 24,
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
        "baseline_training",
        "baseline_guards",
        "training_sweep_guards",
        "strong_cell",
        "weak_cell",
        "transition_cell",
        "contaminator_cell",
        "response_half_span",
        "recovery_guards",
        "max_cells",
        "max_training",
        "max_guards",
        "max_cases",
        "max_response_half_span",
        "max_figures",
        "max_stored_values",
    )
    for name in integer_names:
        value = controls[name]
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{name} must be an integer")
    for name in ("range_resolution_m", "pfa", "response_width", "tolerance"):
        if not finite_real(controls[name]):
            raise ValueError(f"{name} must be finite and real")

    if controls["seed"] != 4601 or controls["cells"] != 256:
        raise ValueError("canonical deterministic shape changed")
    if controls["cells"] > controls["max_cells"] or controls["range_resolution_m"] <= 0:
        raise ValueError("cell shape or spacing outside bounds")
    if not 0 < controls["pfa"] < 0.5 or not 0 < controls["tolerance"] <= 1e-6:
        raise ValueError("probability or tolerance outside bounds")
    if not 2 <= controls["baseline_training"] <= controls["max_training"]:
        raise ValueError("baseline training count outside bounds")
    if not 0 <= controls["baseline_guards"] <= controls["max_guards"]:
        raise ValueError("baseline guard count outside bounds")
    if not 0 <= controls["training_sweep_guards"] <= controls["max_guards"]:
        raise ValueError("training-sweep guard count outside bounds")
    if not 1 <= controls["response_half_span"] <= controls["max_response_half_span"]:
        raise ValueError("response extent outside bounds")
    if controls["response_width"] <= 1:
        raise ValueError("response width outside reviewed model")

    for name, minimum in (("guard_sweep", 0), ("training_sweep", 2)):
        values = controls[name]
        if not isinstance(values, (tuple, list)) or not 3 <= len(values) <= controls["max_cases"]:
            raise ValueError(f"{name} case count outside bounds")
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in values):
            raise ValueError(f"{name} must contain integers")
        if not all(minimum <= v for v in values) or any(b <= a for a, b in zip(values, values[1:])):
            raise ValueError(f"{name} must be strictly increasing and in range")
    if max(controls["guard_sweep"]) > controls["max_guards"]:
        raise ValueError("guard sweep exceeds ceiling")
    if max(controls["training_sweep"]) > controls["max_training"]:
        raise ValueError("training sweep exceeds ceiling")
    if controls["baseline_guards"] not in controls["guard_sweep"]:
        raise ValueError("guard sweep omits baseline")
    if controls["baseline_training"] not in controls["training_sweep"]:
        raise ValueError("training sweep omits baseline")

    positions = (
        controls["strong_cell"],
        controls["contaminator_cell"],
        controls["weak_cell"],
        controls["transition_cell"],
    )
    if not all(1 <= v <= controls["cells"] for v in positions):
        raise ValueError("scene position outside profile")
    if any(b <= a for a, b in zip(positions, positions[1:])):
        raise ValueError("scene positions must remain ordered")
    if controls["strong_cell"] - controls["response_half_span"] < 1:
        raise ValueError("strong response falls below profile")
    if controls["strong_cell"] + controls["response_half_span"] > controls["cells"]:
        raise ValueError("strong response exceeds profile")
    if controls["weak_cell"] - controls["contaminator_cell"] != controls["recovery_guards"]:
        raise ValueError("recovery geometry no longer excludes contaminator")
    if not 0 <= controls["recovery_guards"] <= controls["max_guards"]:
        raise ValueError("recovery guards outside bounds")

    largest_half_window = max(controls["training_sweep"]) + max(
        max(controls["guard_sweep"]),
        controls["training_sweep_guards"],
        controls["recovery_guards"],
    )
    if 2 * largest_half_window + 1 >= controls["cells"]:
        raise ValueError("largest stencil does not fit")
    for name in ("quiet_region", "transition_region"):
        region = controls[name]
        if not isinstance(region, (tuple, list)) or len(region) < 2:
            raise ValueError(f"{name} must be a nonempty contiguous vector")
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in region):
            raise ValueError(f"{name} must contain integers")
        if any(b != a + 1 for a, b in zip(region, region[1:])):
            raise ValueError(f"{name} must be contiguous")
        if min(region) <= largest_half_window or max(region) > controls["cells"] - largest_half_window:
            raise ValueError(f"{name} lies outside all eligible stencils")

    reviewed_ceilings = {
        "max_cells": 512,
        "max_training": 40,
        "max_guards": 12,
        "max_cases": 5,
        "max_response_half_span": 24,
        "max_figures": 5,
        "max_stored_values": 50_000,
    }
    for name, expected in reviewed_ceilings.items():
        if controls[name] != expected:
            raise ValueError(f"{name} must remain reviewed and fixed")
    estimate = (
        55 * controls["cells"]
        + 12 * controls["cells"] * len(controls["guard_sweep"])
        + 16 * controls["cells"] * len(controls["training_sweep"])
        + 2000
    )
    if estimate > controls["max_stored_values"]:
        raise ValueError("stored-value ceiling exceeded")


def ca_cfar(profile: list[float], training: int, guards: int, pfa: float) -> dict[str, object]:
    reference_count = 2 * training
    alpha = reference_count * (pfa ** (-1 / reference_count) - 1)
    first = training + guards
    last = len(profile) - training - guards
    estimates: list[float | None] = [None] * len(profile)
    thresholds: list[float | None] = [None] * len(profile)
    detections = [False] * len(profile)
    references: dict[int, tuple[int, ...]] = {}
    for cut in range(first, last):
        leading = tuple(range(cut - guards - training, cut - guards))
        lagging = tuple(range(cut + guards + 1, cut + guards + training + 1))
        indices = leading + lagging
        references[cut] = indices
        estimates[cut] = sum(profile[index] for index in indices) / reference_count
        thresholds[cut] = alpha * estimates[cut]
        detections[cut] = profile[cut] > thresholds[cut]
    return {
        "alpha": alpha,
        "first": first,
        "last": last,
        "estimates": estimates,
        "thresholds": thresholds,
        "detections": detections,
        "references": references,
    }


def background_curve(cells: int = 256) -> list[float]:
    return [
        0.75 + 0.003 * index + 2.8 / (1 + math.exp(-(index - 178) / 5.5))
        for index in range(1, cells + 1)
    ]


def sampled_sinc_response(half_span: int = 18, width: float = 5.0) -> list[float]:
    result = []
    for offset in range(-half_span, half_span + 1):
        argument = offset / width
        result.append(1.0 if offset == 0 else math.sin(math.pi * argument) / (math.pi * argument))
    peak = max(abs(value) for value in result)
    return [value / peak for value in result]


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", re.sub(r"\.\.\.\s*", "", source))
    required = (
        "random_seed = 4601",
        "RandStream('mt19937ar', 'Seed', random_seed)",
        "close(findall(0, 'Type', 'figure', 'Tag', 'P46'))",
        "background_only_received = sqrt(background_mean_power).*unit_complex_noise",
        "sin(pi*response_argument(nonzero_response))./(pi*response_argument(nonzero_response))",
        "profile_power = abs(received).^2",
        "guard_cell_sweep = [0 4 10]",
        "training_cell_sweep = [4 12 36]",
        "training_cell_count = 2*baseline_training_cells_per_side",
        "design_false_alarm_probability^(-1/training_cell_count)-1",
        "leading_training_cells = cut_cell-baseline_guard_cells_per_side-baseline_training_cells_per_side:cut_cell-baseline_guard_cells_per_side-1",
        "lagging_training_cells = cut_cell+baseline_guard_cells_per_side+1:cut_cell+baseline_guard_cells_per_side+baseline_training_cells_per_side",
        "noise_estimate_power(cut_cell) = mean(profile_power(training_cells))",
        "profile_power(cut_cell) > threshold_power(cut_cell)",
        "training_sweep_expected_estimate_power(training_index, cut_cell) = mean(background_mean_power(training_cells))",
        "training_sweep_roughness(training_index) = mean(abs(diff(quiet_estimate)))/mean(background_mean_power(quiet_region_cells))",
        "assert(training_sweep_roughness(1) > training_sweep_roughness(end))",
        "broken_reference_contains_contaminator",
        "broken_claim_is_valid = false",
        "broken_noise_estimate_power(cut_cell) = mean(contaminated_profile_power(training_cells))",
        "recovery_reference_excludes_contaminator",
        "mean(contaminated_profile_power(training_cells))",
        "estimated_stored_numeric_values <= max_stored_numeric_values",
        "results.guard_sweep_strong_target_margin",
        "results.training_sweep_locality_error",
        "results.recovery_geometry_valid",
    )
    return [marker for marker in required if marker not in compact]


class P46ModuleTests(unittest.TestCase):
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

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self):
        self.assertEqual(validate_p46_contract(MODULE, self.manifest), [])
        entries = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(entries["P45"]["status"], "implemented")
        self.assertEqual(entries["P46"], EXPECTED_IDENTITY)
        for name in ARTIFACTS:
            data = (MODULE / name).read_bytes()
            self.assertTrue(data.endswith(b"\n"), name)
            self.assertFalse(data.endswith(b"\n\n"), name)
            self.assertNotIn(b"\r", data, name)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "module"
            shutil.copytree(MODULE, fixture)
            (fixture / "lesson.md").unlink()
            self.assertIn("P46 missing lesson.md", validate_p46_contract(fixture, self.manifest))
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P46 empty lesson.md", validate_p46_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p46_contract(MODULE, None))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p46_contract(MODULE, {"modules": [None]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn(
            "expected one P46 manifest entry, found 2",
            validate_p46_contract(MODULE, duplicate),
        )
        for key in EXPECTED_IDENTITY:
            drifted = copy.deepcopy(self.manifest)
            next(item for item in drifted["modules"] if item["id"] == "P46")[key] = "drift"
            errors = validate_p46_contract(MODULE, drifted)
            if key == "id":
                self.assertTrue(any("one P46 manifest entry" in error for error in errors))
            else:
                self.assertTrue(any(key in error for error in errors), key)

    def test_controls_accept_canonical_and_reject_malformed_or_unbounded_values(self):
        validate_controls()
        invalid = (
            {"seed": True},
            {"seed": 4602},
            {"cells": 255},
            {"range_resolution_m": 0},
            {"pfa": math.nan},
            {"pfa": 0.5},
            {"baseline_training": 1},
            {"baseline_guards": -1},
            {"guard_sweep": (0, 4)},
            {"guard_sweep": (0, 4, 4)},
            {"guard_sweep": (0, 4, 13)},
            {"guard_sweep": (0, 5, 10)},
            {"training_sweep": (4, 12, 41)},
            {"training_sweep": (4, True, 36)},
            {"training_sweep": (4, 24, 36)},
            {"response_half_span": 25},
            {"response_width": 1},
            {"strong_cell": 10},
            {"contaminator_cell": 140},
            {"recovery_guards": 11},
            {"quiet_region": (70, 72)},
            {"transition_region": (20, 21)},
            {"tolerance": 0},
            {"max_training": 41},
            {"max_stored_values": 49_999},
            {"unknown": 1},
        )
        for controls in invalid:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_guard_sweep_oracle_exposes_self_masking_and_geometry_cost(self):
        profile = [1.0] * 256
        target_center = 87
        response = sampled_sinc_response()
        target_power = 10_000.0
        for offset, amplitude in zip(range(-18, 19), response):
            profile[target_center + offset] += target_power * amplitude**2
        cases = [ca_cfar(profile, 12, guards, 1e-3) for guards in (0, 4, 10)]
        margins = [
            profile[target_center] / case["thresholds"][target_center]
            for case in cases
        ]
        self.assertLess(margins[0], 1)
        self.assertGreater(margins[1], 1)
        self.assertTrue(all(right > left for left, right in zip(margins, margins[1:])))
        reference_target_means = []
        target_only = [max(value - 1.0, 0.0) for value in profile]
        for case in cases:
            references = case["references"][target_center]
            reference_target_means.append(sum(target_only[i] for i in references) / len(references))
        self.assertTrue(
            all(right < left for left, right in zip(reference_target_means, reference_target_means[1:]))
        )
        spans_m = [(2 * (12 + guards) + 1) * 15 for guards in (0, 4, 10)]
        self.assertEqual(spans_m, [375, 495, 675])

    def test_training_sweep_oracle_separates_finite_n_scale_and_locality(self):
        background = background_curve()
        cases = [ca_cfar(background, training, 6, 1e-3) for training in (4, 12, 36)]
        self.assertTrue(all(right["alpha"] < left["alpha"] for left, right in zip(cases, cases[1:])))
        locality = []
        for case in cases:
            errors = [
                abs(case["estimates"][cell] - background[cell]) / background[cell]
                for cell in range(164, 190)
            ]
            locality.append(sum(errors) / len(errors))
        self.assertTrue(all(right > left for left, right in zip(locality, locality[1:])))
        self.assertGreater(locality[-1], 2 * locality[0])
        eligible_counts = [case["last"] - case["first"] for case in cases]
        self.assertTrue(all(right < left for left, right in zip(eligible_counts, eligible_counts[1:])))

        generator = random.Random(4601)
        noisy_power = [
            mean * (generator.gauss(0, 1) ** 2 + generator.gauss(0, 1) ** 2) / 2
            for mean in background
        ]
        noisy_cases = [ca_cfar(noisy_power, training, 6, 1e-3) for training in (4, 12, 36)]
        quiet = range(69, 100)
        quiet_mean = sum(background[index] for index in quiet) / len(quiet)
        roughness = []
        for case in noisy_cases:
            estimates = [case["estimates"][index] for index in quiet]
            roughness.append(
                sum(abs(right - left) for left, right in zip(estimates, estimates[1:]))
                / (len(estimates) - 1)
                / quiet_mean
            )
        self.assertTrue(all(right < left for left, right in zip(roughness, roughness[1:])))

    def test_contaminated_reference_masks_weak_cut_and_geometry_recovery(self):
        profile = [1.0] * 256
        weak_cut = 137
        contaminator = 125
        profile[weak_cut] = 64.0
        clean = ca_cfar(profile, 12, 4, 1e-3)
        self.assertTrue(clean["detections"][weak_cut])
        contaminated = list(profile)
        contaminated[contaminator] = 2000.0
        broken = ca_cfar(contaminated, 12, 4, 1e-3)
        recovered = ca_cfar(contaminated, 12, 12, 1e-3)
        self.assertIn(contaminator, broken["references"][weak_cut])
        self.assertNotIn(contaminator, recovered["references"][weak_cut])
        self.assertFalse(broken["detections"][weak_cut])
        self.assertTrue(recovered["detections"][weak_cut])
        self.assertEqual(profile[weak_cut], contaminated[weak_cut])
        self.assertLess(recovered["thresholds"][weak_cut], broken["thresholds"][weak_cut])

    def test_source_is_deterministic_transparent_bounded_and_mutation_sensitive(self):
        self.assertEqual(source_contract_errors(self.source), [])
        for marker in (
            "guard_cell_sweep = [0 4 10]",
            "training_cell_sweep = [4 12 36]",
            "broken_noise_estimate_power(cut_cell) = ...\n        mean(contaminated_profile_power(training_cells))",
        ):
            with self.subTest(marker=marker):
                self.assertTrue(source_contract_errors(self.source.replace(marker, "removed", 1)))
        controls_end = self.source.index("estimated_stored_numeric_values <= max_stored_numeric_values")
        first_allocation = min(
            self.source.index(marker)
            for marker in ("RandStream(", "zeros(1, cell_count)", "nan(1, cell_count)")
        )
        self.assertLess(controls_end, first_allocation)
        self.assertNotRegex(
            self.source.lower(),
            r"(?m)^\s*(?:\w+\s*=\s*)?(?:cfar|phased\.[a-z0-9_]+|parfor|timer|webread|urlread|system|fopen|save|load)\s*\(",
        )
        self.assertNotIn("rng(", self.source)
        self.assertEqual(self.source.count("figure('Name'"), 5)

    def test_docs_cover_baseline_sweeps_failure_recovery_cancellation_and_teach_back(self):
        combined = "\n".join(self.docs.values())
        self.assertEqual(combined.count(QUESTION), 2)
        for marker in (
            "P45",
            "P48",
            "P49",
            "P52",
            "linear power",
            "square-law",
            "sampled sinc",
            "self-masking",
            "roughness",
            "locality",
            "contaminat",
            "base MATLAB",
            "bounded",
            "Ctrl+C",
            "recomput",
        ):
            self.assertIn(marker.lower(), combined.lower(), marker)
        walkthrough = self.docs["walkthrough.md"]
        for heading in (
            "## 1. Observe the seeded scene",
            "## 2. Read the baseline stencil and threshold",
            "## 3. Sweep guard cells only",
            "## 4. Sweep training cells only",
            "## 5. Break the homogeneous-reference assumption",
            "## Cancellation, rerun, and recovery",
        ):
            self.assertIn(heading, walkthrough)
        checks = self.docs["checks.md"]
        for heading in (
            "## Observation checks",
            "## Prediction checks",
            "## Interpretation checks",
            "## Short teach-back rubric",
        ):
            self.assertIn(heading, checks)

    def test_documented_sweep_edits_fit_reviewed_bounds_and_dynamic_outputs(self):
        walkthrough = self.docs["walkthrough.md"]
        guard_match = re.search(r"guard_cell_sweep` to `\[([0-9 ]+)\]", walkthrough)
        training_match = re.search(r"training_cell_sweep` to `\[([0-9 ]+)\]", walkthrough)
        self.assertIsNotNone(guard_match)
        self.assertIsNotNone(training_match)
        guards = tuple(int(value) for value in guard_match.group(1).split())
        training = tuple(int(value) for value in training_match.group(1).split())
        validate_controls(guard_sweep=guards)
        validate_controls(training_sweep=training)
        self.assertLessEqual(len(guards), self.controls["max_cases"])
        self.assertLessEqual(len(training), self.controls["max_cases"])
        self.assertIn("'DisplayName', 'Observed profile'", self.source)
        self.assertIn("'DisplayName', 'Known local mean'", self.source)
        self.assertIn("fprintf(' %.2f', guard_sweep_strong_target_margin)", self.source)
        self.assertIn("fprintf(' %.3f', training_sweep_roughness)", self.source)

    def test_isolated_cli_timeout_cancellation_and_scaffold_rollback_compatibility(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            fixture_root = Path(temporary) / "repo"
            fixture_cli = fixture_root / "bin/learn"
            fixture_manifest = fixture_root / "curriculum/modules.json"
            fixture_readme = fixture_root / EXPECTED_IDENTITY["folder"] / "README.md"
            fixture_cli.parent.mkdir(parents=True)
            fixture_manifest.parent.mkdir(parents=True)
            fixture_readme.parent.mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture_cli)
            shutil.copy2(ROOT / "curriculum/modules.json", fixture_manifest)
            for entry in self.manifest["modules"]:
                readme = fixture_root / entry["folder"] / "README.md"
                readme.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / entry["folder"] / "README.md", readme)
            started = subprocess.run(
                [str(fixture_cli), "start", "46"],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P46", started.stdout)
            self.assertIn("status: implemented", started.stdout)
            self.assertIn("Tutor entry", started.stdout)

            rolled = json.loads(fixture_manifest.read_text(encoding="utf-8"))
            next(item for item in rolled["modules"] if item["id"] == "P46")["status"] = "scaffolded"
            fixture_manifest.write_text(json.dumps(rolled, indent=2) + "\n", encoding="utf-8")
            waiting = subprocess.run(
                [str(fixture_cli), "start", "46"],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(waiting.returncode, 3, waiting.stderr)
            self.assertIn("awaits Portfolio batch P46", waiting.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)
        self.assertIn("Ctrl+C", self.docs["walkthrough.md"])

    def test_default_tutor_entry_advances_from_completed_p45_without_state_loss(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture_root = Path(temporary) / "repo"
            fixture_cli = fixture_root / "bin/learn"
            fixture_manifest = fixture_root / "curriculum/modules.json"
            fixture_cli.parent.mkdir(parents=True)
            fixture_manifest.parent.mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture_cli)
            shutil.copy2(ROOT / "curriculum/modules.json", fixture_manifest)
            for entry in self.manifest["modules"]:
                readme = fixture_root / entry["folder"] / "README.md"
                readme.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / entry["folder"] / "README.md", readme)

            prior_completed = [f"P{number:02d}" for number in range(1, 46)]
            progress = fixture_root / ".learning/progress.json"
            progress.parent.mkdir()
            progress.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P45",
                        "completed": prior_completed,
                        "notes": {"P45": "preserve this teach-back note"},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            started = subprocess.run(
                [str(fixture_cli), "start"],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P46 — Vary CFAR Guard and Training Cells", started.stdout)
            self.assertIn("status: implemented", started.stdout)
            state = json.loads(progress.read_text(encoding="utf-8"))
            self.assertEqual(state["current"], "P46")
            self.assertEqual(state["completed"], prior_completed)
            self.assertEqual(
                state["notes"], {"P45": "preserve this teach-back note"}
            )

    def test_p46_only_rollback_preserves_neighbor_identity(self):
        rolled = copy.deepcopy(self.manifest)
        neighbors_before = {
            item["id"]: copy.deepcopy(item)
            for item in rolled["modules"]
            if item["id"] in {"P45", "P47"}
        }
        next(item for item in rolled["modules"] if item["id"] == "P46")["status"] = "scaffolded"
        neighbors_after = {
            item["id"]: item for item in rolled["modules"] if item["id"] in {"P45", "P47"}
        }
        self.assertEqual(neighbors_after, neighbors_before)
        self.assertTrue(any("status" in error for error in validate_p46_contract(MODULE, rolled)))

    def test_public_catalogs_describe_p46_without_freezing_future_state(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 46 gives a strong target", readme)
        self.assertIn("Project 46 follows P45", start_here)
        self.assertRegex(module_index, r"\| \[P46\].*\| implemented \| 5 \|")
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?i)P46\s+(?:is\s+)?(?:the\s+)?(?:latest|last|final)")
        self.assertNotRegex(source, r"(?i)P47[^\n]*remains? scaffolded")

    def test_retained_evidence_has_claim_boundary_commands_and_single_newline(self):
        evidence = ROOT / "docs/evidence/P46-2026-08-04.md"
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
            "python3 -m unittest tests.test_p46_module -v",
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
