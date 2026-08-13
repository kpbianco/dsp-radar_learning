from __future__ import annotations

import cmath
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
MODULE = ROOT / "modules/79-compare-sar-resolution-aperture-length-and-windowing"
EVIDENCE = ROOT / "docs/evidence/P79-2026-08-13.md"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "What controls range and cross-range resolution and sidelobes?"

BASE_CONTROLS = {
    "seed": 7901,
    "c_mps": 3.0e8,
    "carrier_hz": 10.0e9,
    "scene_range_m": 1000.0,
    "bandwidth_hz": 200.0e6,
    "frequency_samples": 257,
    "aperture_length_m": 30.0,
    "dense_spacing_m": 0.25,
    "bandwidth_sweep_hz": [100.0e6, 200.0e6, 400.0e6],
    "aperture_sweep_m": [10.0, 20.0, 30.0],
    "spacing_sweep_m": [0.25, 1.0, 5.0],
    "range_axis_m": [-6.0 + 0.005 * index for index in range(2401)],
    "cross_range_axis_m": [-8.0 + 0.005 * index for index in range(3201)],
    "image_x_m": [-5.0 + 0.05 * index for index in range(201)],
    "image_range_offset_m": [-2.0 + 0.05 * index for index in range(81)],
    "target_x_m": [0.0, 0.80, 0.0],
    "target_range_offset_m": [0.0, 0.0, 1.20],
    "target_voltage": [1.0, 0.65, 0.55],
    "display_floor_db": -50.0,
    "max_frequency_samples": 513,
    "max_aperture_samples": 201,
    "max_response_samples": 4001,
    "max_image_pixels": 20000,
    "max_targets": 4,
    "max_sweep_cases": 4,
    "max_private_values": 32,
    "max_response_operations": 6000000,
    "max_working_values": 2000000,
    "max_figures": 5,
    "max_dense_phase_step_rad": 0.90 * math.pi,
}


def module_entry(data: dict, module_id: str) -> dict:
    return next(item for item in data["modules"] if item["id"] == module_id)


def artifact_errors(folder: Path, status: str = "implemented") -> list[str]:
    errors: list[str] = []
    if status == "implemented":
        for name in ARTIFACTS:
            path = folder / name
            if not path.is_file():
                errors.append(f"missing {name}")
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if not text.strip():
                errors.append(f"empty {name}")
            elif "TODO" in text:
                errors.append(f"TODO remains in {name}")
    return errors


def controls_errors(controls: dict) -> list[str]:
    errors: list[str] = []
    vectors = (
        "bandwidth_sweep_hz", "aperture_sweep_m", "spacing_sweep_m",
        "range_axis_m", "cross_range_axis_m", "image_x_m",
        "image_range_offset_m", "target_x_m", "target_range_offset_m",
        "target_voltage",
    )
    for name in vectors:
        value = controls.get(name)
        if (
            not isinstance(value, list)
            or not value
            or any(isinstance(item, (bool, complex, list, tuple)) for item in value)
            or any(not isinstance(item, (int, float)) or not math.isfinite(item) for item in value)
        ):
            errors.append(f"invalid row vector: {name}")
    scalar_names = (
        "c_mps", "carrier_hz", "scene_range_m", "bandwidth_hz",
        "frequency_samples", "aperture_length_m", "dense_spacing_m",
        "display_floor_db", "max_frequency_samples", "max_aperture_samples",
        "max_response_samples", "max_image_pixels", "max_targets",
        "max_sweep_cases", "max_private_values", "max_response_operations",
        "max_working_values", "max_figures", "max_dense_phase_step_rad",
    )
    for name in scalar_names:
        value = controls.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"invalid scalar: {name}")
    seed = controls.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 1 <= seed < 2147483647:
        errors.append("invalid seed")
    if errors:
        return errors

    positive_scalars = tuple(name for name in scalar_names if name != "display_floor_db")
    if any(controls[name] <= 0 for name in positive_scalars) or controls["display_floor_db"] >= 0:
        errors.append("invalid positive control or display floor")
    integer_names = (
        "frequency_samples", "max_frequency_samples", "max_aperture_samples",
        "max_response_samples", "max_image_pixels", "max_targets",
        "max_sweep_cases", "max_private_values", "max_response_operations",
        "max_working_values", "max_figures",
    )
    if any(controls[name] != math.floor(controls[name]) for name in integer_names):
        errors.append("noninteger count or ceiling")
    if controls["frequency_samples"] < 3 or controls["frequency_samples"] % 2 != 1:
        errors.append("frequency count must be odd and at least three")
    ordered = (
        "bandwidth_sweep_hz", "aperture_sweep_m", "spacing_sweep_m",
        "range_axis_m", "cross_range_axis_m", "image_x_m", "image_range_offset_m",
    )
    for name in ordered:
        if any(right <= left for left, right in zip(controls[name], controls[name][1:])):
            errors.append(f"unordered {name}")
    if any(value <= 0 for name in ("bandwidth_sweep_hz", "aperture_sweep_m", "spacing_sweep_m") for value in controls[name]):
        errors.append("nonpositive sweep")
    if not (
        len(controls["target_x_m"])
        == len(controls["target_range_offset_m"])
        == len(controls["target_voltage"])
    ) or any(value <= 0 for value in controls["target_voltage"]):
        errors.append("incompatible target scene")
    if errors:
        return errors

    dense_ratio = controls["aperture_length_m"] / controls["dense_spacing_m"]
    if abs(dense_ratio - round(dense_ratio)) > 1e-9:
        errors.append("off-grid dense aperture")
        return errors
    dense_count = round(dense_ratio) + 1
    aperture_counts: list[int] = []
    for length in controls["aperture_sweep_m"]:
        ratio = length / controls["dense_spacing_m"]
        if abs(ratio - round(ratio)) > 1e-9:
            errors.append("off-grid aperture sweep")
            return errors
        aperture_counts.append(round(ratio) + 1)
    spacing_counts: list[int] = []
    for spacing in controls["spacing_sweep_m"]:
        ratio = controls["aperture_length_m"] / spacing
        if abs(ratio - round(ratio)) > 1e-9:
            errors.append("off-grid spacing sweep")
            return errors
        spacing_counts.append(round(ratio) + 1)
    if (
        controls["frequency_samples"] > controls["max_frequency_samples"]
        or max([dense_count, *aperture_counts, *spacing_counts]) > controls["max_aperture_samples"]
        or len(controls["range_axis_m"]) > controls["max_response_samples"]
        or len(controls["cross_range_axis_m"]) > controls["max_response_samples"]
        or len(controls["image_x_m"]) * len(controls["image_range_offset_m"]) > controls["max_image_pixels"]
        or len(controls["target_x_m"]) > controls["max_targets"]
        or max(len(controls[name]) for name in ("bandwidth_sweep_hz", "aperture_sweep_m", "spacing_sweep_m")) > controls["max_sweep_cases"]
        or len(controls["target_x_m"]) > controls["max_private_values"]
    ):
        errors.append("sample, image, target, sweep, or generator ceiling")
    if not all(min(controls[axis]) <= value <= max(controls[axis]) for axis, values in (
        ("image_x_m", controls["target_x_m"]),
        ("image_range_offset_m", controls["target_range_offset_m"]),
    ) for value in values):
        errors.append("target outside image support")
    phase_step = (
        4 * math.pi * controls["carrier_hz"] / controls["c_mps"]
        * controls["dense_spacing_m"] * max(abs(value) for value in controls["cross_range_axis_m"])
        / (controls["scene_range_m"] - controls["aperture_length_m"] / 2)
    )
    if phase_step >= controls["max_dense_phase_step_rad"]:
        errors.append("dense spatial phase alias")
    if errors:
        return errors

    nr = len(controls["range_axis_m"])
    nx = len(controls["cross_range_axis_m"])
    nir = len(controls["image_range_offset_m"])
    nix = len(controls["image_x_m"])
    nt = len(controls["target_x_m"])
    nf = controls["frequency_samples"]
    dense_image = nt * (nir * nf + nix * dense_count)
    broken_image = nt * (nir * nf + nix * spacing_counts[-1])
    operations = (
        nr * nf + nx * dense_count + dense_image
        + len(controls["bandwidth_sweep_hz"]) * nr * nf
        + nx * sum(aperture_counts) + nx * dense_count
        + nx * sum(spacing_counts) + broken_image
        + nx * dense_count + dense_image
    )
    if operations > controls["max_response_operations"]:
        errors.append("operation ceiling")
    return errors


def private_uniform(seed: int, count: int, maximum: int = 32) -> list[float]:
    if isinstance(seed, bool) or not isinstance(seed, int) or not 1 <= seed < 2147483647:
        raise ValueError("invalid seed")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= maximum:
        raise ValueError("invalid count")
    state = seed
    values: list[float] = []
    for _ in range(count):
        state = (16807 * state) % 2147483647
        values.append((state + 0.5) / 2147483647)
    return values


def range_response(offsets: list[float], bandwidth_hz: float, count: int = 257) -> list[complex]:
    if bandwidth_hz <= 0 or count < 3 or count % 2 != 1 or any(not math.isfinite(value) for value in offsets):
        raise ValueError("invalid range response request")
    frequencies = [-bandwidth_hz / 2 + index * bandwidth_hz / (count - 1) for index in range(count)]
    return [
        sum(cmath.exp(1j * 4 * math.pi * frequency * offset / BASE_CONTROLS["c_mps"]) for frequency in frequencies) / count
        for offset in offsets
    ]


def aperture_response(
    candidates: list[float], spacing_m: float = 0.25, aperture_length_m: float = 30.0,
    hamming: bool = False, target_x_m: float = 0.0, target_range_m: float = 1000.0,
) -> list[complex]:
    if spacing_m <= 0 or aperture_length_m <= 0 or target_range_m <= 0:
        raise ValueError("invalid aperture request")
    ratio = aperture_length_m / spacing_m
    if abs(ratio - round(ratio)) > 1e-9:
        raise ValueError("aperture endpoints are off grid")
    count = round(ratio) + 1
    positions = [-aperture_length_m / 2 + index * spacing_m for index in range(count)]
    weights = [
        0.54 - 0.46 * math.cos(2 * math.pi * index / (count - 1)) if hamming else 1.0
        for index in range(count)
    ]
    target_ranges = [math.hypot(position - target_x_m, target_range_m) for position in positions]
    scale = 4 * math.pi * BASE_CONTROLS["carrier_hz"] / BASE_CONTROLS["c_mps"]
    return [
        sum(
            weight * cmath.exp(1j * scale * (math.hypot(position - candidate, target_range_m) - truth_range))
            for position, truth_range, weight in zip(positions, target_ranges, weights)
        ) / sum(weights)
        for candidate in candidates
    ]


def separable_image(spacing_m: float) -> list[list[complex]]:
    image_x = BASE_CONTROLS["image_x_m"]
    image_range = BASE_CONTROLS["image_range_offset_m"]
    target_reflectivity = [
        voltage * cmath.exp(1j * 2 * math.pi * phase)
        for voltage, phase in zip(
            BASE_CONTROLS["target_voltage"],
            private_uniform(BASE_CONTROLS["seed"], len(BASE_CONTROLS["target_voltage"])),
        )
    ]
    image = [[0j for _ in image_x] for _ in image_range]
    for target_x, target_range, reflectivity in zip(
        BASE_CONTROLS["target_x_m"],
        BASE_CONTROLS["target_range_offset_m"],
        target_reflectivity,
    ):
        range_cut = range_response(
            [candidate - target_range for candidate in image_range],
            BASE_CONTROLS["bandwidth_hz"],
            BASE_CONTROLS["frequency_samples"],
        )
        cross_range_cut = aperture_response(
            image_x,
            spacing_m=spacing_m,
            target_x_m=target_x,
            target_range_m=BASE_CONTROLS["scene_range_m"] + target_range,
        )
        for range_index, range_value in enumerate(range_cut):
            for cross_index, cross_value in enumerate(cross_range_cut):
                image[range_index][cross_index] += (
                    reflectivity * range_value * cross_value
                )
    return image


def response_metrics(axis: list[float], response: list[complex]) -> dict[str, float]:
    magnitude = [abs(value) for value in response]
    peak_index = max(range(len(magnitude)), key=magnitude.__getitem__)
    peak = magnitude[peak_index]
    normalized = [value / peak for value in magnitude]
    half = 1 / math.sqrt(2)
    left = max(index for index in range(peak_index) if normalized[index] <= half)
    right = peak_index + next(index for index, value in enumerate(normalized[peak_index:]) if value <= half)

    def crossing(first: int, second: int) -> float:
        return axis[first] + (half - normalized[first]) * (axis[second] - axis[first]) / (normalized[second] - normalized[first])

    minima = [False] * len(axis)
    for index in range(1, len(axis) - 1):
        minima[index] = normalized[index] <= normalized[index - 1] and normalized[index] < normalized[index + 1]
    left_null = max(index for index in range(peak_index) if minima[index])
    right_null = peak_index + 1 + next(index for index in range(len(axis) - peak_index - 2) if minima[peak_index + 1 + index])
    sidelobe = max(normalized[: left_null + 1] + normalized[right_null:])
    return {
        "half_power_width_m": crossing(right - 1, right) - crossing(left, left + 1),
        "left_null_m": axis[left_null],
        "right_null_m": axis[right_null],
        "peak_sidelobe_db": 20 * math.log10(sidelobe),
    }


class P79ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.documents = {
            name: (MODULE / name).read_text(encoding="utf-8")
            for name in ARTIFACTS if name != "experiment.m"
        }

    def make_cli_fixture(self, fixture: Path, data: dict) -> None:
        (fixture / "bin").mkdir(parents=True)
        (fixture / "curriculum").mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
        (fixture / "curriculum/modules.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def run_cli(self, fixture: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(fixture)
        return subprocess.run(
            [str(fixture / "bin/learn"), *args], cwd=fixture, env=env,
            text=True, capture_output=True, timeout=3,
        )

    def test_manifest_identity_artifacts_and_permanent_dependency(self):
        current = module_entry(self.data, "P79")
        prerequisite = module_entry(self.data, "P78")
        successor = module_entry(self.data, "P80")
        self.assertEqual(
            {key: current[key] for key in ("number", "id", "title", "guiding_question", "phase", "slug", "folder", "status", "implementation_batch")},
            {
                "number": 79, "id": "P79",
                "title": "Compare SAR Resolution, Aperture Length, and Windowing",
                "guiding_question": QUESTION, "phase": 9,
                "slug": "compare-sar-resolution-aperture-length-and-windowing",
                "folder": "modules/79-compare-sar-resolution-aperture-length-and-windowing",
                "status": "implemented", "implementation_batch": "P79",
            },
        )
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertEqual(successor["implementation_batch"], "P80")
        self.assertEqual(artifact_errors(MODULE), [])
        for name in ARTIFACTS:
            self.assertIn(QUESTION, (MODULE / name).read_text(encoding="utf-8"))

    def test_artifact_validation_rejects_missing_empty_and_placeholder(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            self.assertEqual(artifact_errors(fixture), [])
            (fixture / "lesson.md").unlink()
            self.assertIn("missing lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("\n", encoding="utf-8")
            self.assertIn("empty lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("TODO generic\n", encoding="utf-8")
            self.assertIn("TODO remains in lesson.md", artifact_errors(fixture))

    def test_source_binds_determinism_sweeps_failure_recovery_and_bounds(self):
        markers = (
            "baseline_seed = 7901;", "carrier_frequency_hz = 10.0e9;",
            "baseline_bandwidth_hz = 200.0e6;", "frequency_sample_count = 257;",
            "baseline_aperture_length_m = 30.0;", "dense_platform_spacing_m = 0.25;",
            "bandwidth_sweep_hz = [100.0e6 200.0e6 400.0e6];",
            "aperture_length_sweep_m = [10.0 20.0 30.0];",
            "platform_spacing_sweep_m = [0.25 1.0 5.0];",
            "maximum_response_operations = 6000000;",
            "maximum_working_value_equivalents = 2000000;",
            "frequency_contributions = exp(1j*4*pi*frequency_offset_hz*",
            "predicted_slant_range_m-target_slant_range_m",
            "aperture_contributions = aperture_weights.*exp(1j*residual_phase_rad);",
            "0.54-0.46*cos(2*pi*sample_index/",
            "P79:BandwidthSweep", "P79:ApertureSweep", "P79:TaperTradeoff",
            "P79:SparseApertureAliases", "P79:SameSceneRecovery",
            "P79:OperationAccounting", "measurement_before_failure",
            "recovery_exact_match", "predicted_response_operations = validate_controls(controls);",
            "pre_results_workspace_inventory = whos;",
        )
        for marker in markers:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P79"), 5)
        self.assertNotIn("rng(", self.source.lower())

    def test_source_has_no_opaque_toolbox_or_external_side_effect(self):
        lowered = self.source.lower()
        for forbidden in (
            "phased.", "sarprocessor", "rangecompressor", "backprojection(",
            "interp1(", "awgn(", "rand(", "randn(", "parfor", "timer(",
            "pause(", "webread(", "webwrite(", "fopen(", "save(",
            "writematrix(", "system(", "unix(", "dos(", "gpuarray(", "batch(",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_control_contract_accepts_baseline_and_rejects_malformed_resources(self):
        self.assertEqual(controls_errors(copy.deepcopy(BASE_CONTROLS)), [])
        cases: list[tuple[str, dict]] = []
        nested = copy.deepcopy(BASE_CONTROLS); nested["bandwidth_sweep_hz"] = [[100e6], [200e6]]; cases.append(("nested", nested))
        nonfinite = copy.deepcopy(BASE_CONTROLS); nonfinite["cross_range_axis_m"][4] = math.nan; cases.append(("nonfinite", nonfinite))
        boolean = copy.deepcopy(BASE_CONTROLS); boolean["carrier_hz"] = True; cases.append(("Boolean", boolean))
        bad_seed = copy.deepcopy(BASE_CONTROLS); bad_seed["seed"] = 0; cases.append(("seed", bad_seed))
        negative_bandwidth = copy.deepcopy(BASE_CONTROLS); negative_bandwidth["bandwidth_hz"] = -1; cases.append(("positive", negative_bandwidth))
        even_frequency = copy.deepcopy(BASE_CONTROLS); even_frequency["frequency_samples"] = 256; cases.append(("odd", even_frequency))
        unordered = copy.deepcopy(BASE_CONTROLS); unordered["spacing_sweep_m"] = [0.25, 5.0, 1.0]; cases.append(("unordered", unordered))
        off_grid = copy.deepcopy(BASE_CONTROLS); off_grid["dense_spacing_m"] = 0.26; cases.append(("off-grid", off_grid))
        incompatible = copy.deepcopy(BASE_CONTROLS); incompatible["target_voltage"].pop(); cases.append(("target", incompatible))
        outside = copy.deepcopy(BASE_CONTROLS); outside["target_x_m"][1] = 6.0; cases.append(("support", outside))
        samples = copy.deepcopy(BASE_CONTROLS); samples["max_response_samples"] = 100; cases.append(("ceiling", samples))
        operations = copy.deepcopy(BASE_CONTROLS); operations["max_response_operations"] = 1000; cases.append(("operation", operations))
        spatial_alias = copy.deepcopy(BASE_CONTROLS); spatial_alias["dense_spacing_m"] = 5.0; cases.append(("phase alias", spatial_alias))
        for label, malformed in cases:
            with self.subTest(label=label):
                self.assertTrue(controls_errors(malformed))

    def test_private_seed_is_repeatable_bounded_and_isolated(self):
        before = random.getstate()
        first = private_uniform(7901, 3)
        second = private_uniform(7901, 3)
        after = random.getstate()
        self.assertEqual(first, second)
        self.assertEqual(before, after)
        self.assertAlmostEqual(first[0], 0.06183614375155239, places=15)
        with self.assertRaises(ValueError):
            private_uniform(True, 3)
        with self.assertRaises(ValueError):
            private_uniform(7901, 33)

    def test_independent_psf_oracle_matches_physical_limits_and_tradeoffs(self):
        range_axis = BASE_CONTROLS["range_axis_m"]
        cross_axis = BASE_CONTROLS["cross_range_axis_m"]
        range_metrics = [
            response_metrics(range_axis, range_response(range_axis, bandwidth))
            for bandwidth in BASE_CONTROLS["bandwidth_sweep_hz"]
        ]
        cross_metrics = [
            response_metrics(cross_axis, aperture_response(cross_axis, aperture_length_m=length))
            for length in BASE_CONTROLS["aperture_sweep_m"]
        ]
        range_widths = [item["half_power_width_m"] for item in range_metrics]
        cross_widths = [item["half_power_width_m"] for item in cross_metrics]
        self.assertTrue(all(right < left for left, right in zip(range_widths, range_widths[1:])))
        self.assertTrue(all(right < left for left, right in zip(cross_widths, cross_widths[1:])))
        for bandwidth, item in zip(BASE_CONTROLS["bandwidth_sweep_hz"], range_metrics):
            self.assertLess(abs(item["right_null_m"] - BASE_CONTROLS["c_mps"] / (2 * bandwidth)), 0.02)
            self.assertTrue(-13.6 < item["peak_sidelobe_db"] < -12.8)
        wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
        for length, item in zip(BASE_CONTROLS["aperture_sweep_m"], cross_metrics):
            expected = wavelength * BASE_CONTROLS["scene_range_m"] / (2 * length)
            self.assertLess(abs(item["right_null_m"] - expected), 0.06)
            self.assertTrue(-13.6 < item["peak_sidelobe_db"] < -12.8)
        self.assertAlmostEqual(range_widths[1], 0.6618321179837043, places=9)
        self.assertAlmostEqual(cross_widths[-1], 0.4393233573416686, places=9)

        uniform = cross_metrics[-1]
        hamming_response = aperture_response(cross_axis, hamming=True)
        hamming = response_metrics(cross_axis, hamming_response)
        self.assertAlmostEqual(hamming["half_power_width_m"], 0.6496595167765861, places=9)
        self.assertAlmostEqual(hamming["peak_sidelobe_db"], -42.612122386873295, places=8)
        self.assertGreater(hamming["half_power_width_m"], 1.3 * uniform["half_power_width_m"])
        self.assertLess(hamming["peak_sidelobe_db"], uniform["peak_sidelobe_db"] - 20)
        count = 121
        weights = [0.54 - 0.46 * math.cos(2 * math.pi * index / (count - 1)) for index in range(count)]
        efficiency_db = 10 * math.log10(sum(weights) ** 2 / (count * sum(value * value for value in weights)))
        self.assertAlmostEqual(efficiency_db, -1.3703107760295112, places=10)

    def test_sparse_sampling_alias_failure_and_same_scene_recovery(self):
        probes = [-6.0, -3.0, 0.0, 3.0, 6.0]
        dense = aperture_response(probes, spacing_m=0.25)
        broken = aperture_response(probes, spacing_m=5.0)
        recovered = aperture_response(probes, spacing_m=0.25)
        self.assertEqual(dense, recovered)
        self.assertGreater(abs(broken[1]), 0.999)
        self.assertGreater(abs(broken[3]), 0.999)
        self.assertLess(abs(dense[1]), 0.02)
        self.assertLess(abs(dense[3]), 0.02)
        self.assertAlmostEqual(
            BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
            * BASE_CONTROLS["scene_range_m"] / (2 * 5.0),
            3.0,
            places=12,
        )
        with self.assertRaises(ValueError):
            aperture_response([0.0], spacing_m=0.26)
        with self.assertRaises(ValueError):
            range_response([math.nan], 200e6)

    def test_composite_image_exposes_sparse_false_targets_and_exact_recovery(self):
        dense = separable_image(spacing_m=0.25)
        broken = separable_image(spacing_m=5.0)
        recovered = separable_image(spacing_m=0.25)
        self.assertEqual(dense, recovered)

        image_x = BASE_CONTROLS["image_x_m"]
        image_range = BASE_CONTROLS["image_range_offset_m"]

        def sample(image: list[list[complex]], x_m: float, range_m: float) -> float:
            x_index = min(range(len(image_x)), key=lambda index: abs(image_x[index] - x_m))
            range_index = min(
                range(len(image_range)),
                key=lambda index: abs(image_range[index] - range_m),
            )
            return abs(image[range_index][x_index])

        dense_truth = sample(dense, 0.0, 0.0)
        broken_truth = sample(broken, 0.0, 0.0)
        for alias_x in (-3.0, 3.0):
            with self.subTest(alias_x=alias_x):
                self.assertLess(sample(dense, alias_x, 0.0), 0.07 * dense_truth)
                self.assertGreater(sample(broken, alias_x, 0.0), 0.99 * broken_truth)

        dense_peak = max(abs(value) for row in dense for value in row)
        broken_peak = max(abs(value) for row in broken for value in row)
        self.assertAlmostEqual(dense_peak, 0.8707206714911779, places=12)
        self.assertAlmostEqual(broken_peak, 0.8883984455028845, places=12)

    def test_operation_accounting_includes_broken_case_and_fresh_recovery(self):
        nr, nx, nir, nix, nt, nf = 2401, 3201, 81, 201, 3, 257
        dense, aperture_counts, spacing_counts = 121, [41, 81, 121], [121, 31, 7]
        dense_image = nt * (nir * nf + nix * dense)
        broken_image = nt * (nir * nf + nix * spacing_counts[-1])
        operations = (
            nr * nf + nx * dense + dense_image + 3 * nr * nf
            + nx * sum(aperture_counts) + nx * dense
            + nx * sum(spacing_counts) + broken_image
            + nx * dense + dense_image
        )
        self.assertEqual(operations, 5_254_493)
        self.assertLessEqual(operations, BASE_CONTROLS["max_response_operations"])
        self.assertGreater(broken_image, 60_000)
        self.assertGreater(dense_image, broken_image)

    def test_documents_are_concept_first_and_cover_limits(self):
        combined = " ".join("\n".join(self.documents.values()).lower().split())
        for marker in (
            "c/(2b)", "lambda r0/(2l)", "one-sided first-null",
            "half-power width", "peak sidelobe", "20 log10", "1/sqrt(2)",
            "bandwidth", "aperture length", "hamming", "effective aperture",
            "coherent", "snr", "two-way", "lambda r0/(2d)", "3 m",
            "seven looks", "false targets", "unchanged seeded", "recovery",
            "ctrl+c", "no network", "no toolbox", "base matlab r2016b or newer",
            "rollback", "teach-back", "p33", "p62", "p75", "p77", "p78", "p80",
            "local separable", "static", "matlab runtime",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(self.documents["checks.md"].count("**Answer:**"), 30)
        placeholder = re.compile(r"\b(lorem ipsum|coming soon|placeholder lesson|fill this in)\b", re.I)
        self.assertIsNone(placeholder.search(combined))

    def test_cli_timeout_rollback_recovery_isolation_and_future_compatibility(self):
        compatible = copy.deepcopy(self.data)
        module_entry(compatible, "P80")["status"] = "implemented"
        module_entry(compatible, "P80")["future_metadata"] = {"allowed": True}
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            self.make_cli_fixture(fixture, compatible)
            started = self.run_cli(fixture, "start", "79")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P79 — Compare SAR Resolution, Aperture Length, and Windowing", started.stdout)
            rolled_back = copy.deepcopy(compatible)
            module_entry(rolled_back, "P79")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8")
            refused = self.run_cli(fixture, "start", "79")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P79", refused.stdout)
            completed_before = [entry["id"] for entry in compatible["modules"] if entry["number"] < 79]
            progress = fixture / ".learning/progress.json"
            progress.write_text(json.dumps({"schema_version": 1, "current": "P78", "completed": completed_before, "notes": {}}, indent=2) + "\n", encoding="utf-8")
            fallback = self.run_cli(fixture, "start")
            self.assertEqual(fallback.returncode, 0, fallback.stderr)
            self.assertIn("P78 — Observe and Correct Range-Cell Migration", fallback.stdout)
            (fixture / "curriculum/modules.json").write_text(json.dumps(compatible, indent=2) + "\n", encoding="utf-8")
            selected = self.run_cli(fixture, "start")
            self.assertEqual(selected.returncode, 0, selected.stderr)
            self.assertIn("P79 — Compare SAR Resolution, Aperture Length, and Windowing", selected.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_actual_matlab_script_is_repeatable_and_bounded_when_available(self):
        matlab = shutil.which("matlab")
        if matlab is None:
            self.skipTest("MATLAB executable is unavailable; no runtime evidence claimed")
        module_path = str(MODULE).replace("'", "''")
        commands = (
            "set(0,'DefaultFigureVisible','off'); rng(7901,'twister'); rng_before=rng; "
            f"cd('{module_path}'); run('experiment.m'); first_results=p79_results; "
            "rng_after_first=rng; assert(first_results.recovery_exact_match); "
            "assert(first_results.spacing_far_peak_linear(end)>0.95); "
            "assert(first_results.hamming_cross_range_metrics.peak_sidelobe_db < -30); "
            "assert(first_results.executed_response_operations == first_results.predicted_response_operations); "
            "assert(isequaln(rng_before,rng_after_first)); run('experiment.m'); "
            "assert(isequaln(first_results,p79_results)); assert(isequaln(rng_before,rng)); "
            "assert(numel(findall(0,'Type','figure','Tag','P79'))==5); "
            "close(findall(0,'Type','figure','Tag','P79'));"
        )
        guarded = f"try; {commands} exit(0); catch p79_exception; disp(getReport(p79_exception,'extended')); exit(1); end"
        completed = subprocess.run(
            [matlab, "-nosplash", "-nodesktop", "-nodisplay", "-r", guarded],
            cwd=MODULE, text=True, capture_output=True, timeout=300,
        )
        self.assertEqual(completed.returncode, 0, f"MATLAB stdout:\n{completed.stdout}\nMATLAB stderr:\n{completed.stderr}")

    def test_catalogs_evidence_and_exact_eof_policy(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 79 separates SAR range", root_readme)
        self.assertIn("Project 79 follows P78", start_here)
        self.assertRegex(module_index, r"\| \[P79\].*\| implemented \|")
        evidence = EVIDENCE.read_text(encoding="utf-8")
        for heading in (
            "## Claim boundary", "## Acceptance map",
            "## Deterministic simulated-oracle results",
            "## Figure and metric inventory", "## Exact commands and results",
            "## Changed and preserved invariants", "## Residual risks",
            "## Rollback", "## Unperformed validation",
        ):
            self.assertIn(heading, evidence)
        changed_text_paths = [
            *[MODULE / name for name in ARTIFACTS], ROOT / "curriculum/modules.json",
            ROOT / "README.md", ROOT / "START_HERE.md", ROOT / "modules/README.md",
            ROOT / "tests/test_p79_module.py", EVIDENCE,
        ]
        for path in changed_text_paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
