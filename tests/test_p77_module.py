from __future__ import annotations

import cmath
import copy
import json
import math
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/77-focus-sar-with-backprojection"
EVIDENCE = ROOT / "docs/evidence/P77-2026-08-13.md"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How does compensating the correct path length focus a point in an image?"

BASE_CONTROLS = {
    "seed": 7701,
    "c_mps": 3.0e8,
    "carrier_hz": 5.0e9,
    "range_start_m": 990.0,
    "range_end_m": 1035.0,
    "range_spacing_m": 0.5,
    "range_resolution_m": 2.5,
    "aperture_length_m": 30.0,
    "platform_spacing_m": 0.25,
    "target_x_m": [-6.0, 7.0],
    "target_y_m": [1002.0, 1020.0],
    "target_voltage": [1.0, 0.75],
    "target_phase_rad": [0.0, 0.7],
    "noise_rms": 0.015,
    "image_x_m": [-15.0 + 0.25 * index for index in range(121)],
    "image_y_m": [995.0 + 0.5 * index for index in range(65)],
    "partial_counts": [21, 61, 121],
    "path_errors_m": [0.0, 0.005, 0.010],
    "max_aperture_samples": 201,
    "max_range_samples": 121,
    "max_image_pixels": 10000,
    "max_targets": 4,
    "max_sweep_cases": 5,
    "max_private_values": 30000,
    "max_operations": 5000000,
    "max_working_values": 5000000,
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
    vectors = (
        "target_x_m", "target_y_m", "target_voltage", "target_phase_rad",
        "image_x_m", "image_y_m", "partial_counts", "path_errors_m",
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
    if errors:
        return errors
    target_count = len(controls["target_x_m"])
    if any(len(controls[name]) != target_count for name in ("target_y_m", "target_voltage", "target_phase_rad")):
        errors.append("target length mismatch")
    scalar_names = (
        "c_mps", "carrier_hz", "range_start_m", "range_end_m",
        "range_spacing_m", "range_resolution_m", "aperture_length_m",
        "platform_spacing_m", "noise_rms", "max_aperture_samples",
        "max_range_samples", "max_image_pixels", "max_targets",
        "max_sweep_cases", "max_private_values", "max_operations",
        "max_working_values", "max_figures", "max_phase_step_rad",
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
    positive = tuple(name for name in scalar_names if name != "noise_rms")
    if any(controls[name] <= 0 for name in positive):
        errors.append("nonpositive scalar")
    if controls["noise_rms"] < 0 or controls["range_end_m"] <= controls["range_start_m"]:
        errors.append("noise or range gate invalid")
    if controls["range_resolution_m"] < controls["range_spacing_m"]:
        errors.append("range response undersampled")
    if any(value <= 0 for value in controls["target_y_m"] + controls["target_voltage"]):
        errors.append("nonpositive target property")
    for name in ("image_x_m", "image_y_m", "partial_counts", "path_errors_m"):
        if any(right <= left for left, right in zip(controls[name], controls[name][1:])):
            errors.append(f"unordered {name}")
    if len(controls["image_x_m"]) < 3 or len(controls["image_y_m"]) < 3:
        errors.append("short image axis")
    if controls["path_errors_m"][0] != 0 or len(controls["path_errors_m"]) != 3 or len(controls["partial_counts"]) != 3:
        errors.append("sweep contract")
    aperture_exact = controls["aperture_length_m"] / (2 * controls["platform_spacing_m"])
    range_exact = (controls["range_end_m"] - controls["range_start_m"]) / controls["range_spacing_m"]
    if abs(aperture_exact - round(aperture_exact)) > 1e-9:
        errors.append("off-grid aperture")
    if abs(range_exact - round(range_exact)) > 1e-9:
        errors.append("off-grid range")
    if controls["max_phase_step_rad"] >= math.pi or controls["max_figures"] != 6:
        errors.append("phase or figure limit")
    if errors:
        return errors
    aperture_samples = round(controls["aperture_length_m"] / controls["platform_spacing_m"]) + 1
    range_samples = round(range_exact) + 1
    image_pixels = len(controls["image_x_m"]) * len(controls["image_y_m"])
    if aperture_samples > controls["max_aperture_samples"] or range_samples > controls["max_range_samples"] or image_pixels > controls["max_image_pixels"] or target_count > controls["max_targets"]:
        errors.append("sample ceiling")
    if max(len(controls["partial_counts"]), len(controls["path_errors_m"])) > controls["max_sweep_cases"]:
        errors.append("sweep ceiling")
    if any(count <= 0 or count % 2 != 1 or count > aperture_samples for count in controls["partial_counts"]) or controls["partial_counts"][-1] != aperture_samples:
        errors.append("partial aperture contract")
    if 2 * aperture_samples * range_samples > controls["max_private_values"]:
        errors.append("private ceiling")
    nonzero_path_cases = len(controls["path_errors_m"]) - 1
    recovery_cases = 1
    operations = image_pixels * (
        sum(controls["partial_counts"])
        + aperture_samples * (nonzero_path_cases + recovery_cases)
    )
    if operations > controls["max_operations"]:
        errors.append("operation ceiling")
    predicted_values = 30 * image_pixels * (len(controls["partial_counts"]) + len(controls["path_errors_m"])) + 20 * aperture_samples * range_samples
    if predicted_values > controls["max_working_values"]:
        errors.append("working ceiling")
    if errors:
        return errors
    wavelength = controls["c_mps"] / controls["carrier_hz"]
    positions = [-controls["aperture_length_m"] / 2 + index * controls["platform_spacing_m"] for index in range(aperture_samples)]
    for target_x, target_y in zip(controls["target_x_m"], controls["target_y_m"]):
        if min(abs(value - target_x) for value in controls["image_x_m"]) > 1e-9 or min(abs(value - target_y) for value in controls["image_y_m"]) > 1e-9:
            errors.append("target image grid")
        ranges = [math.hypot(position - target_x, target_y) for position in positions]
        phases = [-4 * math.pi * (value - controls["range_start_m"]) / wavelength for value in ranges]
        if max(abs(after - before) for before, after in zip(phases, phases[1:])) >= controls["max_phase_step_rad"]:
            errors.append("spatial alias")
        if min(ranges) <= controls["range_start_m"] + controls["range_spacing_m"] or max(ranges) >= controls["range_end_m"] - controls["range_spacing_m"]:
            errors.append("target range support")
    max_error = max(controls["path_errors_m"])
    for position in positions:
        ranges = [
            math.hypot(position - image_x, image_y + sign * max_error)
            for image_x in (controls["image_x_m"][0], controls["image_x_m"][-1])
            for image_y in (controls["image_y_m"][0], controls["image_y_m"][-1])
            for sign in (-1, 1)
        ]
        if min(ranges) <= controls["range_start_m"] or max(ranges) >= controls["range_end_m"]:
            errors.append("image range support")
            break
    return errors


def private_complex_noise(seed: int, count: int, maximum: int = 30000) -> list[complex]:
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
        raise ValueError("invalid interpolation inputs")
    spacing = range_axis[1] - range_axis[0]
    if spacing <= 0 or any(abs((right - left) - spacing) > 1e-12 for left, right in zip(range_axis, range_axis[1:])):
        raise ValueError("nonuniform range axis")
    fractional_zero_index = (requested_range - range_axis[0]) / spacing
    left = math.floor(fractional_zero_index)
    weight = fractional_zero_index - left
    if left < 0 or left >= len(row) - 1:
        raise ValueError("outside interpolation support")
    return (1 - weight) * row[left] + weight * row[left + 1]


def gridded_point_score(candidate_x: float, indices: range, path_error_amplitude_m: float = 0.0) -> float:
    wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
    positions = [-15.0 + 0.25 * index for index in range(121)]
    range_axis = [990.0 + 0.5 * index for index in range(91)]
    target_x = BASE_CONTROLS["target_x_m"][0]
    target_y = BASE_CONTROLS["target_y_m"][0]
    target_ranges = [math.hypot(position - target_x, target_y) for position in positions]
    rows = [
        [
            explicit_sinc((stored_range - target_range) / BASE_CONTROLS["range_resolution_m"])
            * cmath.exp(-1j * 4 * math.pi * (target_range - 990.0) / wavelength)
            for stored_range in range_axis
        ]
        for target_range in target_ranges
    ]
    total = 0j
    for index in indices:
        path_error = path_error_amplitude_m * math.sin(2 * math.pi * index / 120)
        assumed_range = math.hypot(positions[index] - candidate_x, target_y + path_error)
        sample = linearly_sample(rows[index], range_axis, assumed_range)
        total += sample * cmath.exp(1j * 4 * math.pi * (assumed_range - 990.0) / wavelength)
    return abs(total)


def point_focus_score(candidate_x: float, indices: range, path_error_amplitude_m: float = 0.0) -> float:
    wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
    positions = [-15.0 + 0.25 * index for index in range(121)]
    target_x = BASE_CONTROLS["target_x_m"][0]
    target_y = BASE_CONTROLS["target_y_m"][0]
    target_ranges = [math.hypot(position - target_x, target_y) for position in positions]
    total = 0j
    for index in indices:
        path_error = path_error_amplitude_m * math.sin(2 * math.pi * index / 120)
        assumed_range = math.hypot(positions[index] - candidate_x, target_y + path_error)
        measured_phase = cmath.exp(-1j * 4 * math.pi * (target_ranges[index] - 990.0) / wavelength)
        response = explicit_sinc((assumed_range - target_ranges[index]) / BASE_CONTROLS["range_resolution_m"])
        compensation = cmath.exp(1j * 4 * math.pi * (assumed_range - 990.0) / wavelength)
        total += response * measured_phase * compensation
    return abs(total)


def synthesize_full_scene() -> tuple[list[list[complex]], list[float], list[float]]:
    wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
    positions = [-15.0 + 0.25 * index for index in range(121)]
    range_axis = [990.0 + 0.5 * index for index in range(91)]
    noise = private_complex_noise(7701, len(positions) * len(range_axis))
    history: list[list[complex]] = []
    for aperture_index, position in enumerate(positions):
        row: list[complex] = []
        for range_index, stored_range in enumerate(range_axis):
            value = 0j
            for target_x, target_y, voltage, initial_phase in zip(
                BASE_CONTROLS["target_x_m"], BASE_CONTROLS["target_y_m"],
                BASE_CONTROLS["target_voltage"], BASE_CONTROLS["target_phase_rad"],
            ):
                target_range = math.hypot(position - target_x, target_y)
                value += (
                    voltage
                    * explicit_sinc((stored_range - target_range) / BASE_CONTROLS["range_resolution_m"])
                    * cmath.exp(1j * (initial_phase - 4 * math.pi * (target_range - 990.0) / wavelength))
                )
            # Match reshape(row_vector, [121 91]): MATLAB fills columns first.
            value += BASE_CONTROLS["noise_rms"] * noise[
                aperture_index + range_index * len(positions)
            ]
            row.append(value)
        history.append(row)
    return history, positions, range_axis


def full_scene_score(
    history: list[list[complex]], positions: list[float], range_axis: list[float],
    candidate_x: float, candidate_y: float, path_error_amplitude_m: float = 0.0,
) -> float:
    wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
    total = 0j
    for index, position in enumerate(positions):
        path_error = path_error_amplitude_m * math.sin(2 * math.pi * index / 120)
        assumed_range = math.hypot(position - candidate_x, candidate_y + path_error)
        sample = linearly_sample(history[index], range_axis, assumed_range)
        total += sample * cmath.exp(1j * 4 * math.pi * (assumed_range - 990.0) / wavelength)
    return abs(total)


def half_power_width(values: list[float], coordinates: list[float]) -> float:
    peak_index = max(range(len(values)), key=values.__getitem__)
    threshold = values[peak_index] / math.sqrt(2)
    left = peak_index
    while left > 0 and values[left] >= threshold:
        left -= 1
    right = peak_index
    while right < len(values) - 1 and values[right] >= threshold:
        right += 1
    if values[left] >= threshold or values[right] >= threshold:
        raise ValueError("missing crossing")
    left_cross = coordinates[left] + (threshold - values[left]) * (coordinates[left + 1] - coordinates[left]) / (values[left + 1] - values[left])
    right_cross = coordinates[right - 1] + (threshold - values[right - 1]) * (coordinates[right] - coordinates[right - 1]) / (values[right] - values[right - 1])
    return right_cross - left_cross


class P77ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.documents = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        cls.source = cls.documents["experiment.m"]

    def make_cli_fixture(self, root: Path, manifest: dict) -> Path:
        fixture = root / "repo"
        (fixture / "bin").mkdir(parents=True)
        (fixture / "curriculum").mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
        (fixture / "curriculum/modules.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        for entry in manifest["modules"]:
            readme = fixture / entry["folder"] / "README.md"
            readme.parent.mkdir(parents=True)
            readme.write_text(f"# {entry['id']}\n", encoding="utf-8")
        return fixture

    def run_cli(self, fixture: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(fixture / "bin/learn"), *arguments], cwd=fixture, text=True, capture_output=True, timeout=3, check=False)

    def test_artifacts_manifest_identity_and_permanent_dependency(self):
        self.assertEqual(artifact_errors(MODULE), [])
        entry = module_entry(self.data, "P77")
        expected = {
            "number": 77,
            "title": "Focus SAR with Backprojection",
            "guiding_question": QUESTION,
            "phase": 9,
            "phase_title": "SAR, ISAR, Passive Radar, and Capstone",
            "slug": "focus-sar-with-backprojection",
            "folder": "modules/77-focus-sar-with-backprojection",
            "status": "implemented",
            "implementation_batch": "P77",
        }
        for key, value in expected.items():
            self.assertEqual(entry[key], value)
        self.assertEqual(module_entry(self.data, "P76")["status"], "implemented")
        self.assertEqual(module_entry(self.data, "P78")["implementation_batch"], "P78")
        for name, text in self.documents.items():
            with self.subTest(name=name):
                self.assertIn(QUESTION, text)

    def test_malformed_artifact_contract_rejects_missing_empty_and_placeholder(self):
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

    def test_source_exposes_backprojection_sweeps_failure_recovery_and_bounds(self):
        markers = (
            "baseline_seed = 7701;", "carrier_frequency_hz = 5.0e9;",
            "speed_of_light_mps = 3.0e8;", "range_gate_start_m = 990.0;",
            "range_gate_end_m = 1035.0;",
            "range_sample_spacing_m = 0.5;", "range_resolution_m = 2.5;",
            "aperture_length_m = 30.0;", "platform_spacing_m = 0.25;",
            "target_cross_range_m = [-6.0 7.0];",
            "target_ground_range_m = [1002.0 1020.0];",
            "target_voltage = [1.0 0.75];",
            "target_initial_phase_rad = [0.0 0.7];",
            "noise_rms_voltage = 0.015;",
            "image_cross_range_m = -15.0:0.25:15.0;",
            "image_ground_range_m = 995.0:0.5:1027.0;",
            "partial_aperture_counts = [21 61 121];",
            "path_error_sweep_m = [0.0 0.005 0.010];",
            "maximum_aperture_samples = 201;",
            "maximum_range_samples = 121;", "maximum_image_pixels = 10000;",
            "maximum_targets = 4;", "maximum_sweep_cases = 5;",
            "maximum_private_values = 30000;",
            "maximum_backprojection_operations = 5000000;",
            "maximum_working_value_equivalents = 5000000;",
            "maximum_figures = 6;", "maximum_adjacent_phase_step_rad = 0.90*pi;",
            "minimum_input_phase_coherence = 0.99;",
            "minimum_recovered_coherence = 0.98;",
            "maximum_broken_coherence = 0.35;",
            "maximum_cross_range_error_m = 0.25;",
            "maximum_ground_range_error_m = 0.5;",
            "fractional_index = (hypothesized_range_m-range_axis_m(1))",
            "sampled_complex_value(valid_linear_index)",
            "phase_compensation = exp(1j*4*pi*",
            "image_complex = image_complex+sampled_complex_value.*",
            "Intentionally broken 10 mm path", "measurement_before_failure",
            "measurement_exact_match = isequaln", "recovery_exact_match = isequaln",
            "P77:BrokenPathDefocus", "P77:SameDataRecovery",
            "P77:SpatialAliasing", "P77:ImageRangeSupport",
            "P77:BackprojectionOperationBound", "P77:WorkingPreflight",
            "P77:BackprojectionOperationAccounting",
            "P77:SweepCount", "P77:PartialApertureCounts",
            "P77:TargetImageGrid", "P77:BackprojectionPlatform",
            "P77:BackprojectionImageAxes", "P77:PixelTermControls",
            "if case_index == 1", "executed_backprojection_operations",
            "predicted_backprojection_operations = validate_controls(controls);",
            "p77_results = run_p77_experiment();",
            "function p77_results = run_p77_experiment()",
            "pre_results_workspace_inventory = whos;",
            "pre_results_storage_bytes = sum([pre_results_workspace_inventory.bytes]);",
            "magnitude(left_index) >= threshold",
            "p77_results = struct",
        )
        for marker in markers:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P77"), 6)
        self.assertNotIn("rng(", self.source.lower())

    def test_source_has_no_opaque_toolbox_or_external_side_effect(self):
        lowered = self.source.lower()
        for forbidden in (
            "phased.", "sarprocessor", "rangecompressor", "backprojection(",
            "interp1(", "awgn(", "randn(", "parfor", "timer(", "pause(",
            "webread(", "webwrite(", "fopen(", "save(", "writematrix(",
            "system(", "unix(", "dos(", "gpuarray(", "batch(",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertIsNone(re.search(r"\b(?:sinc|fft|ifft|conv2|filter)\(", lowered))

    def test_control_contract_accepts_baseline_and_rejects_malformed_resources(self):
        self.assertEqual(controls_errors(copy.deepcopy(BASE_CONTROLS)), [])
        cases: list[tuple[str, dict]] = []
        nested = copy.deepcopy(BASE_CONTROLS); nested["target_x_m"] = [[-6.0], [7.0]]; cases.append(("column target", nested))
        lengths = copy.deepcopy(BASE_CONTROLS); lengths["target_voltage"].pop(); cases.append(("length mismatch", lengths))
        nonfinite = copy.deepcopy(BASE_CONTROLS); nonfinite["path_errors_m"][-1] = math.nan; cases.append(("nonfinite path", nonfinite))
        negative_noise = copy.deepcopy(BASE_CONTROLS); negative_noise["noise_rms"] = -1; cases.append(("negative noise", negative_noise))
        undersampled = copy.deepcopy(BASE_CONTROLS); undersampled["range_resolution_m"] = 0.25; cases.append(("range response", undersampled))
        aperture = copy.deepcopy(BASE_CONTROLS); aperture["platform_spacing_m"] = 0.4; cases.append(("aperture grid", aperture))
        range_grid = copy.deepcopy(BASE_CONTROLS); range_grid["range_end_m"] = 1035.1; cases.append(("range grid", range_grid))
        alias = copy.deepcopy(BASE_CONTROLS); alias["platform_spacing_m"] = 1.5; cases.append(("spatial alias", alias))
        target_support = copy.deepcopy(BASE_CONTROLS); target_support["range_end_m"] = 1020.5; cases.append(("target support", target_support))
        image_support = copy.deepcopy(BASE_CONTROLS); image_support["image_y_m"][-1] = 1040.0; cases.append(("image support", image_support))
        off_grid_target = copy.deepcopy(BASE_CONTROLS); off_grid_target["target_x_m"][0] = -6.1; cases.append(("off-grid target", off_grid_target))
        singleton_x = copy.deepcopy(BASE_CONTROLS); singleton_x["image_x_m"] = [0.0]; cases.append(("singleton x axis", singleton_x))
        singleton_y = copy.deepcopy(BASE_CONTROLS); singleton_y["image_y_m"] = [1002.0]; cases.append(("singleton y axis", singleton_y))
        private = copy.deepcopy(BASE_CONTROLS); private["max_private_values"] = 1000; cases.append(("private ceiling", private))
        operations = copy.deepcopy(BASE_CONTROLS); operations["max_operations"] = 100000; cases.append(("operation ceiling", operations))
        working = copy.deepcopy(BASE_CONTROLS); working["max_working_values"] = 100000; cases.append(("working ceiling", working))
        targets = copy.deepcopy(BASE_CONTROLS); targets["max_targets"] = 1; cases.append(("target ceiling", targets))
        sweeps = copy.deepcopy(BASE_CONTROLS); sweeps["max_sweep_cases"] = 2; cases.append(("sweep ceiling", sweeps))
        short_partial = copy.deepcopy(BASE_CONTROLS); short_partial["partial_counts"].pop(); cases.append(("short partial", short_partial))
        even_partial = copy.deepcopy(BASE_CONTROLS); even_partial["partial_counts"][1] = 60; cases.append(("even partial", even_partial))
        negative_partial = copy.deepcopy(BASE_CONTROLS); negative_partial["partial_counts"][0] = -3; cases.append(("negative partial", negative_partial))
        unordered = copy.deepcopy(BASE_CONTROLS); unordered["path_errors_m"] = [0.0, 0.010, 0.005]; cases.append(("unordered path", unordered))
        no_zero = copy.deepcopy(BASE_CONTROLS); no_zero["path_errors_m"] = [0.001, 0.005, 0.010]; cases.append(("no zero path", no_zero))
        figure_bound = copy.deepcopy(BASE_CONTROLS); figure_bound["max_figures"] = 5; cases.append(("figure ceiling", figure_bound))
        loose_figure_bound = copy.deepcopy(BASE_CONTROLS); loose_figure_bound["max_figures"] = 7; cases.append(("loose figure ceiling", loose_figure_bound))
        for label, controls in cases:
            with self.subTest(label=label):
                self.assertTrue(controls_errors(controls))

    def test_private_generator_is_repeatable_bounded_and_isolated(self):
        first = private_complex_noise(7701, 100)
        self.assertEqual(first, private_complex_noise(7701, 100))
        self.assertNotEqual(first, private_complex_noise(7702, 100))
        self.assertAlmostEqual(first[0].real, 1.651034520406058)
        self.assertAlmostEqual(first[0].imag, -0.2880822703749153)
        with self.assertRaises(ValueError):
            private_complex_noise(0, 1)
        with self.assertRaises(ValueError):
            private_complex_noise(7701, 15001)

    def test_partial_aperture_oracle_narrows_and_adds_coherently(self):
        widths: list[float] = []
        peaks: list[float] = []
        coordinates = BASE_CONTROLS["image_x_m"]
        for count in BASE_CONTROLS["partial_counts"]:
            start = (121 - count) // 2
            indices = range(start, start + count)
            values = [point_focus_score(candidate, indices) for candidate in coordinates]
            widths.append(half_power_width(values, coordinates))
            peaks.append(point_focus_score(-6.0, indices))
        for actual, expected in zip(widths, (5.0754090187614365, 1.7360009694360121, 0.8603324141640636)):
            self.assertAlmostEqual(actual, expected, places=10)
        self.assertEqual(peaks, [21.0, 61.0, 121.0])
        self.assertTrue(all(right < left for left, right in zip(widths, widths[1:])))

    def test_path_error_oracle_defocuses_true_pixel_and_zero_error_recovers(self):
        indices = range(121)
        reference = point_focus_score(-6.0, indices)
        ratios = [point_focus_score(-6.0, indices, error) / reference for error in BASE_CONTROLS["path_errors_m"]]
        for actual, expected in zip(ratios, (1.0, 0.7462085937220108, 0.17671757790778192)):
            self.assertAlmostEqual(actual, expected, places=10)
        self.assertTrue(all(right < left for left, right in zip(ratios, ratios[1:])))
        self.assertLess(ratios[-1], 0.35)
        self.assertAlmostEqual(explicit_sinc(0.0), 1.0)
        self.assertAlmostEqual(explicit_sinc(1.0), 0.0, places=15)
        with self.assertRaises(ValueError):
            explicit_sinc(float("nan"))

    def test_half_power_width_accepts_boundary_brackets_and_rejects_missing_support(self):
        expected_width = 2 * (1 - 1 / math.sqrt(2))
        self.assertAlmostEqual(
            half_power_width([0.0, 1.0, 0.0], [0.0, 1.0, 2.0]),
            expected_width,
        )
        with self.assertRaises(ValueError):
            half_power_width([1.0, 1.0, 0.0], [0.0, 1.0, 2.0])
        with self.assertRaises(ValueError):
            half_power_width([0.0, 1.0, 1.0], [0.0, 1.0, 2.0])

    def test_gridded_complex_interpolation_oracle_binds_range_indexing(self):
        row = [0j, 2 + 4j, 6 + 8j, 10 + 12j]
        axis = [990.0, 990.5, 991.0, 991.5]
        self.assertEqual(linearly_sample(row, axis, 990.75), 4 + 6j)
        self.assertEqual(linearly_sample(row, axis, 990.0), 0j)
        with self.assertRaises(ValueError):
            linearly_sample(row, axis, 991.5)
        with self.assertRaises(ValueError):
            linearly_sample(row, [990.0, 990.5, 991.1, 991.5], 990.75)

        indices = range(121)
        candidate_x = BASE_CONTROLS["target_x_m"][0]
        correct = gridded_point_score(candidate_x, indices)
        wrong_x = gridded_point_score(candidate_x + 1.0, indices)
        broken = gridded_point_score(candidate_x, indices, 0.010)
        recovered = gridded_point_score(candidate_x, indices, 0.0)
        self.assertGreater(correct, wrong_x)
        self.assertLess(broken / correct, 0.35)
        self.assertEqual(recovered, correct)

    def test_seeded_two_target_scene_localizes_both_and_defocuses(self):
        history, positions, range_axis = synthesize_full_scene()
        expected_peaks = (120.56406759787146, 90.23727556046373)
        expected_ratios = (
            (1.0, 0.7455574323893361, 0.17564159884544933),
            (1.0, 0.7457345279061367, 0.17591640500932404),
        )
        for target_x, target_y, expected_peak, target_ratios in zip(
            BASE_CONTROLS["target_x_m"], BASE_CONTROLS["target_y_m"],
            expected_peaks, expected_ratios,
        ):
            with self.subTest(target=(target_x, target_y)):
                local_x = [value for value in BASE_CONTROLS["image_x_m"] if abs(value - target_x) <= 3.0]
                local_y = [value for value in BASE_CONTROLS["image_y_m"] if abs(value - target_y) <= 4.0]
                peak, focused_x, focused_y = max(
                    (full_scene_score(history, positions, range_axis, x, y), x, y)
                    for y in local_y for x in local_x
                )
                self.assertEqual((focused_x, focused_y), (target_x, target_y))
                self.assertAlmostEqual(peak, expected_peak, places=10)
                ratios = [
                    full_scene_score(history, positions, range_axis, target_x, target_y, error) / peak
                    for error in BASE_CONTROLS["path_errors_m"]
                ]
                for actual, expected in zip(ratios, target_ratios):
                    self.assertAlmostEqual(actual, expected, places=10)
                self.assertTrue(all(right < left for left, right in zip(ratios, ratios[1:])))
                self.assertLess(ratios[-1], 0.35)

    def test_backprojection_work_accounting_includes_recovery_without_duplicate_zero_case(self):
        pixels = len(BASE_CONTROLS["image_x_m"]) * len(BASE_CONTROLS["image_y_m"])
        aperture_samples = 121
        reviewed_operations = pixels * (
            sum(BASE_CONTROLS["partial_counts"])
            + aperture_samples * ((len(BASE_CONTROLS["path_errors_m"]) - 1) + 1)
        )
        duplicated_zero_case_operations = reviewed_operations + pixels * aperture_samples
        self.assertEqual(reviewed_operations, 4_451_590)
        self.assertLessEqual(reviewed_operations, BASE_CONTROLS["max_operations"])
        self.assertEqual(duplicated_zero_case_operations, 5_403_255)
        self.assertGreater(duplicated_zero_case_operations, BASE_CONTROLS["max_operations"])

    def test_documents_are_concept_first_and_cover_limits(self):
        combined = " ".join("\n".join(self.documents.values()).lower().split())
        for marker in (
            "range-compressed phase history", "slant range", "linear interpolation",
            "4*pi", "two-way", "phase compensation", "coherent sum",
            "partial-aperture", "21", "61", "121", "range cut",
            "cross-range cut", "-3 db", "path error", "5 mm", "10 mm",
            "constant path", "wrong platform height", "bias", "defocus",
            "unchanged complex", "byte-for-byte retained complex phase history",
            "recovery", "range-cell migration",
            "magnitude-only", "cancellation", "ctrl+c", "rollback",
            "teach-back", "no optional toolbox", "base matlab r2016b or newer",
            "5,000,000", "six tagged figure", "p76", "p78", "p79", "p80",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(self.documents["checks.md"].count("**Correct:**"), 43)

    def test_cli_timeout_rollback_recovery_isolation_and_future_compatibility(self):
        compatible = copy.deepcopy(self.data)
        module_entry(compatible, "P78")["status"] = "implemented"
        module_entry(compatible, "P78")["future_metadata"] = {"allowed": True}
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.make_cli_fixture(Path(directory), compatible)
            started = self.run_cli(fixture, "start", "77")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("status: implemented", started.stdout)
            rolled_back = copy.deepcopy(compatible)
            module_entry(rolled_back, "P77")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8")
            refused = self.run_cli(fixture, "start", "77")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P77", refused.stdout)
            (fixture / "curriculum/modules.json").write_text(json.dumps(compatible, indent=2) + "\n", encoding="utf-8")
            recovered = self.run_cli(fixture, "start", "77")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)
        walkthrough = " ".join(self.documents["walkthrough.md"].lower().split())
        for marker in ("ctrl+c", "no worker", "no background", "rerun from the top", "rollback"):
            self.assertIn(marker, walkthrough)

    def test_default_start_routes_to_p77_and_rollback_restores_p76(self):
        implemented_before_p77 = [
            entry["id"] for entry in self.data["modules"]
            if entry["status"] == "implemented" and entry["number"] < 77
        ]
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.make_cli_fixture(Path(directory), self.data)
            progress = fixture / ".learning/progress.json"
            progress.parent.mkdir()
            progress.write_text(json.dumps({"completed": implemented_before_p77, "notes": {}}, indent=2) + "\n", encoding="utf-8")
            selected = self.run_cli(fixture, "start")
            self.assertEqual(selected.returncode, 0, selected.stderr)
            self.assertIn("P77 — Focus SAR with Backprojection", selected.stdout)
            rolled_back = copy.deepcopy(self.data)
            module_entry(rolled_back, "P77")["status"] = "scaffolded"
            module_entry(rolled_back, "P78")["status"] = "implemented"
            module_entry(rolled_back, "P78")["future_metadata"] = {"allowed": True}
            (fixture / "curriculum/modules.json").write_text(json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8")
            fallback = self.run_cli(fixture, "start")
            self.assertEqual(fallback.returncode, 0, fallback.stderr)
            self.assertIn("P76 — Perform SAR Range Compression", fallback.stdout)

    def test_catalogs_evidence_and_exact_eof_policy(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 77 backprojects the complex range history", root_readme)
        self.assertIn("Project 77 follows P76", start_here)
        self.assertRegex(module_index, r"\| \[P77\].*\| implemented \|")
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
            ROOT / "README.md", ROOT / "START_HERE.md", ROOT / "bin/learn",
            ROOT / "modules/README.md",
            ROOT / "tests/test_p77_module.py", EVIDENCE,
        ]
        for path in changed_text_paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
