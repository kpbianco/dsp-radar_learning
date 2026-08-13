from __future__ import annotations

import cmath
import copy
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/78-observe-and-correct-range-cell-migration"
EVIDENCE = ROOT / "docs/evidence/P78-2026-08-13.md"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Why does a target move through range bins during a long synthetic aperture?"

BASE_CONTROLS = {
    "seed": 7801,
    "c_mps": 3.0e8,
    "carrier_hz": 1.0e9,
    "range_start_m": 955.0,
    "range_end_m": 1075.0,
    "range_spacing_m": 0.5,
    "range_resolution_m": 2.0,
    "aperture_length_m": 400.0,
    "platform_spacing_m": 0.25,
    "target_x_m": 60.0,
    "target_y_m": 1000.0,
    "target_voltage": 1.0,
    "target_phase_rad": 0.3,
    "noise_rms": 0.02,
    "aperture_sweep_m": [100.0, 200.0, 400.0],
    "squint_sweep_m": [0.0, 60.0, 80.0],
    "image_x_m": [-40.0 + 2.0 * index for index in range(101)],
    "image_y_m": [995.0 + index for index in range(11)],
    "max_aperture_samples": 2001,
    "max_range_samples": 251,
    "max_image_pixels": 1500,
    "max_sweep_cases": 5,
    "max_private_values": 800000,
    "max_interpolation_operations": 1200000,
    "max_image_operations": 4000000,
    "max_total_operations": 5200000,
    "max_working_values": 12000000,
    "max_figures": 6,
    "max_phase_step_rad": 0.90 * math.pi,
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
    vectors = ("aperture_sweep_m", "squint_sweep_m", "image_x_m", "image_y_m")
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
        "c_mps", "carrier_hz", "range_start_m", "range_end_m",
        "range_spacing_m", "range_resolution_m", "aperture_length_m",
        "platform_spacing_m", "target_x_m", "target_y_m", "target_voltage",
        "target_phase_rad", "noise_rms", "max_aperture_samples",
        "max_range_samples", "max_image_pixels", "max_sweep_cases",
        "max_private_values", "max_interpolation_operations",
        "max_image_operations", "max_total_operations", "max_working_values",
        "max_figures", "max_phase_step_rad",
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

    positive = tuple(name for name in scalar_names if name not in ("target_x_m", "target_phase_rad", "noise_rms"))
    if any(controls[name] <= 0 for name in positive):
        errors.append("nonpositive physical control or ceiling")
    if controls["noise_rms"] < 0 or controls["range_end_m"] <= controls["range_start_m"]:
        errors.append("invalid noise or range gate")
    if controls["range_resolution_m"] < controls["range_spacing_m"]:
        errors.append("undersampled range response")
    for name in vectors:
        if any(right <= left for left, right in zip(controls[name], controls[name][1:])):
            errors.append(f"unordered {name}")
    if (
        len(controls["aperture_sweep_m"]) != 3
        or len(controls["squint_sweep_m"]) != 3
        or controls["aperture_sweep_m"][-1] != controls["aperture_length_m"]
        or controls["squint_sweep_m"][1] != controls["target_x_m"]
    ):
        errors.append("sweep contract")
    if len(controls["image_x_m"]) < 3 or len(controls["image_y_m"]) < 3:
        errors.append("short image axis")
    if controls["target_x_m"] not in controls["image_x_m"] or controls["target_y_m"] not in controls["image_y_m"]:
        errors.append("target absent from image grid")
    if controls["max_figures"] != 6 or controls["max_phase_step_rad"] >= math.pi:
        errors.append("figure or phase ceiling")
    if errors:
        return errors

    aperture_steps = controls["aperture_length_m"] / controls["platform_spacing_m"]
    range_steps = (controls["range_end_m"] - controls["range_start_m"]) / controls["range_spacing_m"]
    if abs(aperture_steps - round(aperture_steps)) > 1e-9 or abs(range_steps - round(range_steps)) > 1e-9:
        errors.append("off-grid endpoint")
        return errors
    aperture_count = round(aperture_steps) + 1
    range_count = round(range_steps) + 1
    image_pixels = len(controls["image_x_m"]) * len(controls["image_y_m"])
    if (
        aperture_count > controls["max_aperture_samples"]
        or range_count > controls["max_range_samples"]
        or image_pixels > controls["max_image_pixels"]
        or max(len(controls["aperture_sweep_m"]), len(controls["squint_sweep_m"])) > controls["max_sweep_cases"]
    ):
        errors.append("sample, pixel, or sweep ceiling")
    if 2 * aperture_count * range_count > controls["max_private_values"]:
        errors.append("private generator ceiling")
    interpolation_operations = 3 * aperture_count * range_count
    image_operations = 2 * aperture_count * image_pixels
    total_operations = interpolation_operations + image_operations
    if interpolation_operations > controls["max_interpolation_operations"]:
        errors.append("interpolation operation ceiling")
    if image_operations > controls["max_image_operations"]:
        errors.append("image operation ceiling")
    if total_operations > controls["max_total_operations"]:
        errors.append("total operation ceiling")
    predicted_working = 24 * aperture_count * range_count + 20 * image_pixels
    if predicted_working > controls["max_working_values"]:
        errors.append("working value ceiling")
    if errors:
        return errors

    wavelength = controls["c_mps"] / controls["carrier_hz"]
    positions = [
        -controls["aperture_length_m"] / 2 + index * controls["platform_spacing_m"]
        for index in range(aperture_count)
    ]
    ranges = [math.hypot(position - controls["target_x_m"], controls["target_y_m"]) for position in positions]
    for offset_case in controls["squint_sweep_m"]:
        case_ranges = [math.hypot(position - offset_case, controls["target_y_m"]) for position in positions]
        phases = [-4 * math.pi * value / wavelength for value in case_ranges]
        if max(abs(right - left) for left, right in zip(phases, phases[1:])) >= controls["max_phase_step_rad"]:
            errors.append("spatial phase alias")
            break
    offset = max(ranges) - min(ranges)
    if (
        min(ranges) - offset - 2 * controls["range_resolution_m"] <= controls["range_start_m"]
        or max(ranges) + offset + 2 * controls["range_resolution_m"] >= controls["range_end_m"]
    ):
        errors.append("migration range support")
    for position in positions:
        for x in (controls["image_x_m"][0], controls["image_x_m"][-1]):
            for y in (controls["image_y_m"][0], controls["image_y_m"][-1]):
                requested = math.hypot(position - x, y)
                if not controls["range_start_m"] + controls["range_spacing_m"] < requested < controls["range_end_m"] - controls["range_spacing_m"]:
                    errors.append("image range support")
                    return errors
    return errors


def private_complex_noise(seed: int, count: int, maximum: int = 800000) -> list[complex]:
    if isinstance(seed, bool) or not isinstance(seed, int) or not 1 <= seed < 2147483647:
        raise ValueError("invalid seed")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1 or 2 * count > maximum:
        raise ValueError("invalid count")
    state = seed
    uniforms: list[float] = []
    for _ in range(2 * count):
        state = (16807 * state) % 2147483647
        uniforms.append(state / 2147483647)
    return [
        math.sqrt(-2 * math.log(max(uniforms[index], float.fromhex("0x1p-1022"))))
        * cmath.exp(1j * 2 * math.pi * uniforms[index + 1])
        / math.sqrt(2)
        for index in range(0, len(uniforms), 2)
    ]


def explicit_sinc(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("nonfinite sinc input")
    return 1.0 if abs(value) <= 1e-12 else math.sin(math.pi * value) / (math.pi * value)


def linearly_sample(row: list[complex], range_axis: list[float], requested_range: float) -> complex:
    if len(row) != len(range_axis) or len(row) < 2 or not math.isfinite(requested_range):
        raise ValueError("invalid interpolation input")
    spacing = range_axis[1] - range_axis[0]
    if spacing <= 0 or any(abs((right - left) - spacing) > 1e-12 for left, right in zip(range_axis, range_axis[1:])):
        raise ValueError("nonuniform range axis")
    fractional = (requested_range - range_axis[0]) / spacing
    left = math.floor(fractional)
    weight = fractional - left
    if left < 0 or left >= len(row) - 1:
        return 0j
    return (1 - weight) * row[left] + weight * row[left + 1]


def synthesize_history() -> tuple[list[list[complex]], list[float], list[float], list[float]]:
    controls = BASE_CONTROLS
    aperture_count = round(controls["aperture_length_m"] / controls["platform_spacing_m"]) + 1
    range_count = round((controls["range_end_m"] - controls["range_start_m"]) / controls["range_spacing_m"]) + 1
    positions = [-controls["aperture_length_m"] / 2 + index * controls["platform_spacing_m"] for index in range(aperture_count)]
    range_axis = [controls["range_start_m"] + index * controls["range_spacing_m"] for index in range(range_count)]
    slant_ranges = [math.hypot(position - controls["target_x_m"], controls["target_y_m"]) for position in positions]
    wavelength = controls["c_mps"] / controls["carrier_hz"]
    noise = private_complex_noise(controls["seed"], aperture_count * range_count)
    history: list[list[complex]] = []
    for row_index, target_range in enumerate(slant_ranges):
        phase = controls["target_phase_rad"] - 4 * math.pi * (target_range - controls["range_start_m"]) / wavelength
        row: list[complex] = []
        for column_index, sample_range in enumerate(range_axis):
            clean = controls["target_voltage"] * explicit_sinc((sample_range - target_range) / controls["range_resolution_m"]) * cmath.exp(1j * phase)
            # MATLAB reshape fills down aperture rows before advancing columns.
            noise_index = row_index + aperture_count * column_index
            row.append(clean + controls["noise_rms"] * noise[noise_index])
        history.append(row)
    return history, positions, range_axis, slant_ranges


def shift_history(history: list[list[complex]], range_axis: list[float], offsets: list[float], sign: int) -> list[list[complex]]:
    if sign not in (-1, 1) or len(history) != len(offsets):
        raise ValueError("invalid shift contract")
    return [
        [linearly_sample(row, range_axis, output_range + sign * offset) for output_range in range_axis]
        for row, offset in zip(history, offsets)
    ]


def coherent_profile(history: list[list[complex]], slant_ranges: list[float]) -> list[complex]:
    wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
    compensation = [cmath.exp(1j * 4 * math.pi * (value - BASE_CONTROLS["range_start_m"]) / wavelength) for value in slant_ranges]
    return [sum(row[column] * phase for row, phase in zip(history, compensation)) for column in range(len(history[0]))]


def image_score(
    history: list[list[complex]], positions: list[float], range_axis: list[float],
    candidate_x: float, candidate_y: float, follow_path: bool,
) -> complex:
    if not isinstance(follow_path, bool) or not math.isfinite(candidate_x) or not math.isfinite(candidate_y):
        raise ValueError("invalid image hypothesis")
    if len(history) != len(positions) or not history or not positions:
        raise ValueError("invalid image history")
    wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
    reference_range = math.hypot(candidate_x, candidate_y)
    total = 0j
    for row, position in zip(history, positions):
        predicted_range = math.hypot(position - candidate_x, candidate_y)
        requested_range = predicted_range if follow_path else reference_range
        sampled = linearly_sample(row, range_axis, requested_range)
        compensation = cmath.exp(
            1j * 4 * math.pi * (predicted_range - BASE_CONTROLS["range_start_m"]) / wavelength
        )
        total += sampled * compensation
    return total


class P78ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.documents = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS if name != "experiment.m"}

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
        current = module_entry(self.data, "P78")
        prerequisite = module_entry(self.data, "P77")
        successor = module_entry(self.data, "P79")
        self.assertEqual(
            {key: current[key] for key in ("number", "id", "title", "guiding_question", "phase", "slug", "folder", "status", "implementation_batch")},
            {
                "number": 78, "id": "P78", "title": "Observe and Correct Range-Cell Migration",
                "guiding_question": QUESTION, "phase": 9,
                "slug": "observe-and-correct-range-cell-migration",
                "folder": "modules/78-observe-and-correct-range-cell-migration",
                "status": "implemented", "implementation_batch": "P78",
            },
        )
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertEqual(successor["implementation_batch"], "P79")
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
            "baseline_seed = 7801;", "carrier_frequency_hz = 1.0e9;",
            "range_gate_start_m = 955.0;", "range_gate_end_m = 1075.0;",
            "range_sample_spacing_m = 0.5;", "range_resolution_m = 2.0;",
            "aperture_length_m = 400.0;", "platform_spacing_m = 0.25;",
            "target_cross_range_m = 60.0;", "target_ground_range_m = 1000.0;",
            "target_initial_phase_rad = 0.3;", "noise_rms_voltage = 0.02;",
            "aperture_length_sweep_m = [100.0 200.0 400.0];",
            "squint_offset_sweep_m = [0.0 60.0 80.0];",
            "maximum_interpolation_operations = 1200000;",
            "maximum_image_operations = 4000000;",
            "maximum_total_operations = 5200000;",
            "maximum_working_value_equivalents = 12000000;",
            "target_slant_range_m = hypot(platform_position_m-target_cross_range_m",
            "requested_range_m = range_axis_m+",
            "direction_sign*migration_offset_m(aperture_index)",
            "fractional_index = (requested_range_m-range_axis_m(1))",
            "shift_range_history(retained_complex_range_history",
            "form_range_cross_range_image(retained_complex_range_history",
            "phase_compensation = exp(1j*4*pi*(predicted_range_m-",
            "image_complex = image_complex+sampled_complex_value.*",
            "P78:VisibleMigration", "P78:CorrectedRidgeAlignment",
            "P78:FixedBinSmear", "P78:WrongSignDoublesMigration",
            "P78:SameDataRecovery", "P78:OperationAccounting",
            "measurement_before_failure", "recovery_exact_match",
            "predicted_operations = validate_controls(controls);",
            "p78_results = run_p78_experiment();",
            "pre_results_workspace_inventory = whos;",
        )
        for marker in markers:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P78"), 6)
        self.assertNotIn("rng(", self.source.lower())

    def test_source_has_no_opaque_toolbox_or_external_side_effect(self):
        lowered = self.source.lower()
        for forbidden in (
            "phased.", "sarprocessor", "rangecompressor", "interp1(", "circshift(",
            "awgn(", "randn(", "parfor", "timer(", "pause(", "webread(",
            "webwrite(", "fopen(", "save(", "writematrix(", "system(", "unix(",
            "dos(", "gpuarray(", "batch(",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_control_contract_accepts_baseline_and_rejects_malformed_resources(self):
        self.assertEqual(controls_errors(copy.deepcopy(BASE_CONTROLS)), [])
        cases: list[tuple[str, dict]] = []
        nested = copy.deepcopy(BASE_CONTROLS); nested["aperture_sweep_m"] = [[100.0], [200.0], [400.0]]; cases.append(("nested sweep", nested))
        nonfinite = copy.deepcopy(BASE_CONTROLS); nonfinite["squint_sweep_m"][-1] = math.nan; cases.append(("nonfinite sweep", nonfinite))
        boolean = copy.deepcopy(BASE_CONTROLS); boolean["carrier_hz"] = True; cases.append(("Boolean scalar", boolean))
        bad_seed = copy.deepcopy(BASE_CONTROLS); bad_seed["seed"] = 0; cases.append(("seed", bad_seed))
        negative_noise = copy.deepcopy(BASE_CONTROLS); negative_noise["noise_rms"] = -1; cases.append(("noise", negative_noise))
        reversed_gate = copy.deepcopy(BASE_CONTROLS); reversed_gate["range_end_m"] = 950; cases.append(("gate", reversed_gate))
        undersampled = copy.deepcopy(BASE_CONTROLS); undersampled["range_resolution_m"] = 0.25; cases.append(("resolution", undersampled))
        off_grid = copy.deepcopy(BASE_CONTROLS); off_grid["range_end_m"] = 1075.1; cases.append(("endpoint", off_grid))
        unordered = copy.deepcopy(BASE_CONTROLS); unordered["aperture_sweep_m"] = [100.0, 400.0, 200.0]; cases.append(("order", unordered))
        missing_baseline = copy.deepcopy(BASE_CONTROLS); missing_baseline["squint_sweep_m"] = [0.0, 70.0, 80.0]; cases.append(("baseline", missing_baseline))
        absent_target = copy.deepcopy(BASE_CONTROLS); absent_target["target_x_m"] = 61.0; cases.append(("image target", absent_target))
        short_axis = copy.deepcopy(BASE_CONTROLS); short_axis["image_y_m"] = [999.0, 1000.0]; cases.append(("axis", short_axis))
        phase_alias = copy.deepcopy(BASE_CONTROLS); phase_alias["platform_spacing_m"] = 0.5; cases.append(("phase alias", phase_alias))
        truncated = copy.deepcopy(BASE_CONTROLS); truncated["range_start_m"] = 990.0; cases.append(("migration support", truncated))
        aperture_limit = copy.deepcopy(BASE_CONTROLS); aperture_limit["max_aperture_samples"] = 1000; cases.append(("aperture limit", aperture_limit))
        range_limit = copy.deepcopy(BASE_CONTROLS); range_limit["max_range_samples"] = 100; cases.append(("range limit", range_limit))
        pixel_limit = copy.deepcopy(BASE_CONTROLS); pixel_limit["max_image_pixels"] = 1000; cases.append(("pixel limit", pixel_limit))
        sweep_limit = copy.deepcopy(BASE_CONTROLS); sweep_limit["max_sweep_cases"] = 2; cases.append(("sweep limit", sweep_limit))
        private_limit = copy.deepcopy(BASE_CONTROLS); private_limit["max_private_values"] = 700000; cases.append(("private limit", private_limit))
        interpolation_limit = copy.deepcopy(BASE_CONTROLS); interpolation_limit["max_interpolation_operations"] = 1000000; cases.append(("interpolation limit", interpolation_limit))
        image_limit = copy.deepcopy(BASE_CONTROLS); image_limit["max_image_operations"] = 3000000; cases.append(("image limit", image_limit))
        total_limit = copy.deepcopy(BASE_CONTROLS); total_limit["max_total_operations"] = 4000000; cases.append(("total limit", total_limit))
        working_limit = copy.deepcopy(BASE_CONTROLS); working_limit["max_working_values"] = 8000000; cases.append(("working limit", working_limit))
        figure_limit = copy.deepcopy(BASE_CONTROLS); figure_limit["max_figures"] = 5; cases.append(("figure limit", figure_limit))
        for label, controls in cases:
            with self.subTest(label=label):
                self.assertTrue(controls_errors(controls))

    def test_private_generator_and_interpolation_are_repeatable_bounded_and_isolated(self):
        first = private_complex_noise(7801, 100)
        self.assertEqual(first, private_complex_noise(7801, 100))
        self.assertNotEqual(first, private_complex_noise(7802, 100))
        self.assertAlmostEqual(first[0].real, 1.1727844238167962)
        self.assertAlmostEqual(first[0].imag, 1.191881427525603)
        with self.assertRaises(ValueError):
            private_complex_noise(0, 1)
        with self.assertRaises(ValueError):
            private_complex_noise(7801, 400001)
        self.assertAlmostEqual(explicit_sinc(0.0), 1.0)
        self.assertAlmostEqual(explicit_sinc(1.0), 0.0, places=15)
        with self.assertRaises(ValueError):
            explicit_sinc(math.nan)
        row = [0j, 2 + 4j, 6 + 8j, 10 + 12j]
        axis = [955.0, 955.5, 956.0, 956.5]
        self.assertEqual(linearly_sample(row, axis, 955.75), 4 + 6j)
        self.assertEqual(linearly_sample(row, axis, 954.5), 0j)
        self.assertEqual(linearly_sample(row, axis, 956.5), 0j)
        with self.assertRaises(ValueError):
            linearly_sample(row, [955.0, 955.5, 956.1, 956.5], 955.75)
        with self.assertRaises(ValueError):
            shift_history([row], axis, [], +1)
        with self.assertRaises(ValueError):
            shift_history([row], axis, [0.0], 0)
        with self.assertRaises(ValueError):
            image_score([row], [0.0], axis, math.nan, 1000.0, True)
        with self.assertRaises(ValueError):
            image_score([row], [0.0], axis, 0.0, 1000.0, 1)

    def test_geometry_sweeps_and_phase_sampling_oracle(self):
        controls = BASE_CONTROLS
        positions = [-200.0 + 0.25 * index for index in range(1601)]
        ranges = [math.hypot(position - controls["target_x_m"], controls["target_y_m"]) for position in positions]
        span = max(ranges) - min(ranges)
        self.assertAlmostEqual(span, 33.24730824715925, places=10)
        self.assertAlmostEqual(span / controls["range_spacing_m"], 66.4946164943185, places=10)
        self.assertAlmostEqual(span / controls["range_resolution_m"], 16.623654123579625, places=10)
        aperture_spans = []
        for length in controls["aperture_sweep_m"]:
            case_positions = [-length / 2 + 0.25 * index for index in range(round(length / 0.25) + 1)]
            case_ranges = [math.hypot(position - controls["target_x_m"], controls["target_y_m"]) for position in case_positions]
            aperture_spans.append(max(case_ranges) - min(case_ranges))
        squint_spans = []
        for offset in controls["squint_sweep_m"]:
            case_ranges = [math.hypot(position - offset, controls["target_y_m"]) for position in positions]
            squint_spans.append(max(case_ranges) - min(case_ranges))
        for actual, expected in zip(aperture_spans, (5.981809892189062, 12.719112093772992, 33.24730824715925)):
            self.assertAlmostEqual(actual, expected, places=10)
        for actual, expected in zip(squint_spans, (19.80390271855697, 33.24730824715925, 38.46039885977348)):
            self.assertAlmostEqual(actual, expected, places=10)
        self.assertTrue(all(right > left for left, right in zip(aperture_spans, aperture_spans[1:])))
        self.assertTrue(all(right > left for left, right in zip(squint_spans, squint_spans[1:])))
        wavelength = controls["c_mps"] / controls["carrier_hz"]
        maximum_steps = []
        for offset in controls["squint_sweep_m"]:
            case_ranges = [math.hypot(position - offset, controls["target_y_m"]) for position in positions]
            phase_steps = [abs(-4 * math.pi * (right - left) / wavelength) for left, right in zip(case_ranges, case_ranges[1:])]
            maximum_steps.append(max(phase_steps))
        self.assertAlmostEqual(maximum_steps[-1], 2.822389024484437, places=10)
        self.assertTrue(all(value < controls["max_phase_step_rad"] for value in maximum_steps))

    def test_seeded_profile_oracle_isolates_migration_and_exact_recovery(self):
        history, positions, range_axis, slant_ranges = synthesize_history()
        reference = slant_ranges[len(slant_ranges) // 2]
        offsets = [value - reference for value in slant_ranges]
        corrected = shift_history(history, range_axis, offsets, +1)
        wrong = shift_history(history, range_axis, offsets, -1)
        recovered = shift_history(history, range_axis, offsets, +1)
        self.assertEqual(corrected, recovered)
        fixed_profile = coherent_profile(history, slant_ranges)
        corrected_profile = coherent_profile(corrected, slant_ranges)
        wrong_profile = coherent_profile(wrong, slant_ranges)
        self.assertEqual(corrected_profile, coherent_profile(recovered, slant_ranges))
        fixed_peak = max(abs(value) for value in fixed_profile)
        corrected_peak = max(abs(value) for value in corrected_profile)
        wrong_peak = max(abs(value) for value in wrong_profile)
        fixed_power = [abs(value) ** 2 for value in fixed_profile]
        corrected_power = [abs(value) ** 2 for value in corrected_profile]
        peak_gain = corrected_peak / fixed_peak
        concentration_gain = (max(corrected_power) / sum(corrected_power)) / (max(fixed_power) / sum(fixed_power))
        self.assertAlmostEqual(fixed_peak, 436.3967692647651, places=8)
        self.assertAlmostEqual(corrected_peak, 1548.0803720920485, places=8)
        self.assertAlmostEqual(wrong_peak, 307.2823324292318, places=8)
        self.assertAlmostEqual(peak_gain, 3.5474148323788732, places=10)
        self.assertAlmostEqual(concentration_gain, 1.6411301260234474, places=10)
        self.assertGreater(peak_gain, 3.0)
        self.assertGreater(concentration_gain, 1.4)
        measured_ridge = [range_axis[max(range(len(row)), key=lambda index: abs(row[index]))] for row in history]
        corrected_ridge = [range_axis[max(range(len(row)), key=lambda index: abs(row[index]))] for row in corrected]
        wrong_ridge = [range_axis[max(range(len(row)), key=lambda index: abs(row[index]))] for row in wrong]
        measured_span = max(measured_ridge) - min(measured_ridge)
        corrected_span = max(corrected_ridge) - min(corrected_ridge)
        wrong_span = max(wrong_ridge) - min(wrong_ridge)
        self.assertEqual((measured_span, corrected_span, wrong_span), (33.5, 0.5, 66.5))
        self.assertGreater(wrong_span, 1.8 * measured_span)

        fixed_image: list[tuple[float, float, float]] = []
        corrected_image: list[tuple[float, float, float]] = []
        for candidate_y in BASE_CONTROLS["image_y_m"]:
            for candidate_x in BASE_CONTROLS["image_x_m"]:
                fixed_image.append((
                    abs(image_score(history, positions, range_axis, candidate_x, candidate_y, False)),
                    candidate_x, candidate_y,
                ))
                corrected_image.append((
                    abs(image_score(history, positions, range_axis, candidate_x, candidate_y, True)),
                    candidate_x, candidate_y,
                ))
        fixed_true = next(value for value, x, y in fixed_image if (x, y) == (60.0, 1000.0))
        corrected_true = next(value for value, x, y in corrected_image if (x, y) == (60.0, 1000.0))
        fixed_powers = [value * value for value, _, _ in fixed_image]
        corrected_powers = [value * value for value, _, _ in corrected_image]
        true_pixel_ratio = fixed_true / corrected_true
        image_concentration_gain = (
            max(corrected_powers) / sum(corrected_powers)
        ) / (max(fixed_powers) / sum(fixed_powers))
        corrected_peak, corrected_x, corrected_y = max(corrected_image)
        self.assertAlmostEqual(true_pixel_ratio, 0.2184656084252973, places=9)
        self.assertAlmostEqual(image_concentration_gain, 2.3819839452, places=8)
        self.assertEqual((corrected_x, corrected_y), (60.0, 1000.0))
        self.assertLess(true_pixel_ratio, 0.40)
        self.assertGreater(image_concentration_gain, 1.8)

    def test_actual_matlab_script_is_repeatable_and_bounded_when_available(self):
        matlab = shutil.which("matlab")
        if matlab is None:
            self.skipTest("MATLAB executable is unavailable; no runtime evidence claimed")

        module_path = str(MODULE).replace("'", "''")
        matlab_commands = (
            "set(0,'DefaultFigureVisible','off'); "
            "rng(7801,'twister'); rng_before = rng; "
            f"cd('{module_path}'); run('experiment.m'); "
            "first_results = p78_results; rng_after_first = rng; "
            "assert(first_results.measurement_exact_match); "
            "assert(first_results.recovery_exact_match); "
            "assert(first_results.profile_recovery_exact_match); "
            "assert(first_results.corrected_ridge_span_m <= 1.0); "
            "assert(first_results.wrong_ridge_span_m > "
            "1.8*first_results.measured_migration_span_m); "
            "assert(isequaln(rng_before,rng_after_first)); "
            "run('experiment.m'); "
            "assert(isequaln(first_results,p78_results)); "
            "assert(isequaln(rng_before,rng)); "
            "assert(numel(findall(0,'Type','figure','Tag','P78')) == 6); "
            "close(findall(0,'Type','figure','Tag','P78'));"
        )
        guarded_commands = (
            f"try; {matlab_commands} exit(0); "
            "catch p78_exception; "
            "disp(getReport(p78_exception,'extended')); exit(1); end"
        )
        completed = subprocess.run(
            [matlab, "-nosplash", "-nodesktop", "-nodisplay", "-r", guarded_commands],
            cwd=MODULE,
            text=True,
            capture_output=True,
            timeout=300,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"MATLAB stdout:\n{completed.stdout}\nMATLAB stderr:\n{completed.stderr}",
        )

    def test_operation_accounting_includes_failure_and_fresh_recovery(self):
        aperture_count = 1601
        range_count = 241
        image_pixels = 101 * 11
        interpolation = 3 * aperture_count * range_count
        image = 2 * aperture_count * image_pixels
        self.assertEqual(interpolation, 1_157_523)
        self.assertEqual(image, 3_557_422)
        self.assertEqual(interpolation + image, 4_714_945)
        self.assertLessEqual(interpolation, BASE_CONTROLS["max_interpolation_operations"])
        self.assertLessEqual(image, BASE_CONTROLS["max_image_operations"])
        self.assertLessEqual(interpolation + image, BASE_CONTROLS["max_total_operations"])
        self.assertGreater(2 * aperture_count * range_count, 700000)

    def test_documents_are_concept_first_and_cover_limits(self):
        combined = " ".join("\n".join(self.documents.values()).lower().split())
        for marker in (
            "stationary", "slant range", "square root", "round-trip delay",
            "stored range bin", "resolution cell", "0.5 m", "2 m", "33.25",
            "66.5", "16.6", "linear interpolation", "fractional index",
            "4*pi", "two-way", "phase compensation", "fixed-bin",
            "path-following", "backprojection", "aperture length", "squint",
            "wrong sign", "doubles", "unchanged complex", "recovery",
            "ctrl+c", "no worker", "no optional toolbox", "base matlab r2016b or newer",
            "rollback", "teach-back", "p76", "p77", "p79", "p80",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(self.documents["checks.md"].count("**Correct:**"), 39)

    def test_cli_timeout_rollback_recovery_isolation_and_future_compatibility(self):
        compatible = copy.deepcopy(self.data)
        module_entry(compatible, "P79")["status"] = "implemented"
        module_entry(compatible, "P79")["future_metadata"] = {"allowed": True}
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            self.make_cli_fixture(fixture, compatible)
            started = self.run_cli(fixture, "start", "78")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P78 — Observe and Correct Range-Cell Migration", started.stdout)
            rolled_back = copy.deepcopy(compatible)
            module_entry(rolled_back, "P78")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8")
            refused = self.run_cli(fixture, "start", "78")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P78", refused.stdout)
            completed_before = [entry["id"] for entry in compatible["modules"] if entry["number"] < 78]
            progress = fixture / ".learning/progress.json"
            progress.write_text(json.dumps({"schema_version": 1, "current": "P77", "completed": completed_before, "notes": {}}, indent=2) + "\n", encoding="utf-8")
            fallback = self.run_cli(fixture, "start")
            self.assertEqual(fallback.returncode, 0, fallback.stderr)
            self.assertIn("P77 — Focus SAR with Backprojection", fallback.stdout)
            (fixture / "curriculum/modules.json").write_text(json.dumps(compatible, indent=2) + "\n", encoding="utf-8")
            selected = self.run_cli(fixture, "start")
            self.assertEqual(selected.returncode, 0, selected.stderr)
            self.assertIn("P78 — Observe and Correct Range-Cell Migration", selected.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)
        walkthrough = " ".join(self.documents["walkthrough.md"].lower().split())
        for marker in ("ctrl+c", "no worker", "timer", "background task", "rerun from the top", "rollback"):
            self.assertIn(marker, walkthrough)

    def test_catalogs_evidence_and_exact_eof_policy(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 78 holds one stationary target", root_readme)
        self.assertIn("Project 78 follows P77", start_here)
        self.assertRegex(module_index, r"\| \[P78\].*\| implemented \|")
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
            ROOT / "tests/test_p78_module.py", EVIDENCE,
        ]
        for path in changed_text_paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
