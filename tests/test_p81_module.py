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
MODULE = ROOT / "modules" / "81-form-an-isar-image-from-a-rotating-target"
MANIFEST = ROOT / "curriculum" / "modules.json"
CLI = ROOT / "bin" / "learn"
EVIDENCE = ROOT / "docs" / "evidence" / "P81-2026-08-14.md"
QUESTION = "How does target rotation create synthetic aperture when the radar is stationary?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")

BASE_CONTROLS = {
    "seed": 8101,
    "c_mps": 3.0e8,
    "carrier_hz": 10.0e9,
    "bandwidth_hz": 600.0e6,
    "frequency_samples": 129,
    "look_count": 65,
    "baseline_aperture_deg": 6.0,
    "baseline_rate_deg_s": 6.0,
    "translation_velocity_mps": 2.0,
    "aperture_sweep_deg": [2.0, 4.0, 6.0, 8.0],
    "rate_sweep_deg_s": [3.0, 6.0, 12.0],
    "target_x_m": [0, 0, 0, 0, -2, -1, 1, 2, -0.75, 0.75],
    "target_y_m": [-1.5, -0.5, 0.5, 1.5, 0, 0, 0, 0, -1.25, -1.25],
    "target_voltage": [1.0, 0.75, 0.85, 0.90, 0.80, 0.65, 0.65, 0.80, 0.55, 0.55],
    "display_floor_db": -35.0,
    "max_frequency_samples": 257,
    "max_look_count": 129,
    "max_target_count": 16,
    "max_sweep_cases": 6,
    "max_private_values": 64,
    "max_contributions": 900_000,
    "max_working_values": 2_500_000,
    "expected_figures": 5,
}


def artifact_errors(folder: Path) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = folder / name
        if not path.is_file():
            errors.append(f"missing {name}")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            errors.append(f"empty {name}")
        if re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", text, re.IGNORECASE):
            errors.append(f"placeholder remains in {name}")
    return errors


def controls_errors(c: dict) -> list[str]:
    errors: list[str] = []
    vector_names = (
        "aperture_sweep_deg",
        "rate_sweep_deg_s",
        "target_x_m",
        "target_y_m",
        "target_voltage",
    )
    scalar_names = (
        "seed",
        "c_mps",
        "carrier_hz",
        "bandwidth_hz",
        "frequency_samples",
        "look_count",
        "baseline_aperture_deg",
        "baseline_rate_deg_s",
        "translation_velocity_mps",
        "display_floor_db",
        "max_frequency_samples",
        "max_look_count",
        "max_target_count",
        "max_sweep_cases",
        "max_private_values",
        "max_contributions",
        "max_working_values",
        "expected_figures",
    )
    positive = set(scalar_names) - {"seed", "display_floor_db"}
    integers = {
        "seed",
        "frequency_samples",
        "look_count",
        "max_frequency_samples",
        "max_look_count",
        "max_target_count",
        "max_sweep_cases",
        "max_private_values",
        "max_contributions",
        "max_working_values",
        "expected_figures",
    }
    for name in vector_names:
        value = c.get(name)
        if (
            not isinstance(value, list)
            or not value
            or any(
                isinstance(item, bool)
                or not isinstance(item, (int, float))
                or not math.isfinite(item)
                for item in value
            )
        ):
            errors.append(f"{name} must be a finite numeric row")
    for name in scalar_names:
        value = c.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            errors.append(f"{name} must be a finite real scalar")
            continue
        if name in positive and value <= 0:
            errors.append(f"{name} must be positive")
        if name in integers and value != math.floor(value):
            errors.append(f"{name} must be an integer")
    if errors:
        return errors
    if not 0 < c["seed"] < 2_147_483_647:
        errors.append("seed outside Park-Miller range")
    if c["display_floor_db"] >= 0:
        errors.append("display floor must be negative")
    for name in ("frequency_samples", "look_count"):
        if c[name] < 5 or c[name] % 2 != 1:
            errors.append(f"{name} must be odd and at least five")
    for name in ("aperture_sweep_deg", "rate_sweep_deg_s"):
        if any(right <= left for left, right in zip(c[name], c[name][1:])):
            errors.append(f"{name} must increase")
        if any(value <= 0 for value in c[name]):
            errors.append(f"{name} must be positive")
    count = len(c["target_x_m"])
    if count != len(c["target_y_m"]) or count != len(c["target_voltage"]):
        errors.append("target vectors must have equal lengths")
    if any(value <= 0 for value in c["target_voltage"]):
        errors.append("target voltages must be positive")
    if (
        c["frequency_samples"] > c["max_frequency_samples"]
        or c["look_count"] > c["max_look_count"]
        or count > c["max_target_count"]
        or count > c["max_private_values"]
        or max(len(c["aperture_sweep_deg"]), len(c["rate_sweep_deg_s"]))
        > c["max_sweep_cases"]
    ):
        errors.append("sample, target, sweep, or generator ceiling exceeded")
    wavelength = c["c_mps"] / c["carrier_hz"]
    maximum_angle_step = math.radians(max(c["aperture_sweep_deg"])) / (
        c["look_count"] - 1
    )
    if max(map(abs, c["target_x_m"])) >= wavelength / (4 * maximum_angle_step):
        errors.append("target cross-range exceeds unambiguous support")
    frequency_step = c["bandwidth_hz"] / (c["frequency_samples"] - 1)
    if max(map(abs, c["target_y_m"])) >= c["c_mps"] / (4 * frequency_step):
        errors.append("target range exceeds unambiguous support")
    maximum_time = max(
        max(c["aperture_sweep_deg"]) / (2 * c["baseline_rate_deg_s"]),
        c["baseline_aperture_deg"] / (2 * min(c["rate_sweep_deg_s"])),
    )
    maximum_projected_range = c["translation_velocity_mps"] * maximum_time + max(
        math.hypot(x, y) for x, y in zip(c["target_x_m"], c["target_y_m"])
    )
    if maximum_projected_range >= c["c_mps"] / (4 * frequency_step):
        errors.append("complete projected path exceeds periodic range support")
    wavelength = c["c_mps"] / c["carrier_hz"]
    for rate in c["rate_sweep_deg_s"]:
        prf = (c["look_count"] - 1) * rate / c["baseline_aperture_deg"]
        rotational_doppler = 2 * max(map(abs, c["target_x_m"])) * math.radians(rate) / wavelength
        if 2 * rotational_doppler >= prf:
            errors.append("rotational Doppler exceeds slow-time Nyquist")
    history_count = 1 + len(c["aperture_sweep_deg"]) + len(c["rate_sweep_deg_s"])
    predicted = history_count * c["look_count"] * c["frequency_samples"] * count
    if predicted > c["max_contributions"]:
        errors.append("coherent contribution ceiling exceeded")
    return errors


def private_uniform(seed: int, count: int, maximum: int = 64) -> list[float]:
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 < seed < 2_147_483_647:
        raise ValueError("invalid seed")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= maximum:
        raise ValueError("invalid count")
    state = seed
    values: list[float] = []
    for _ in range(count):
        state = (16_807 * state) % 2_147_483_647
        values.append(state / 2_147_483_647)
    return values


def centered(values: list, inverse: bool = False) -> list:
    shift = len(values) // 2 if inverse else (len(values) + 1) // 2
    return values[shift:] + values[:shift]


def transform(values: list[complex], inverse: bool) -> list[complex]:
    count = len(values)
    sign = 1 if inverse else -1
    scale = count if inverse else 1
    return [
        sum(
            value * cmath.exp(sign * 2j * math.pi * output * index / count)
            for index, value in enumerate(values)
        )
        / scale
        for output in range(count)
    ]


def centered_transform(values: list[complex], inverse: bool) -> list[complex]:
    return centered(transform(centered(values, inverse=True), inverse=inverse))


class Oracle:
    def __init__(self, controls: dict = BASE_CONTROLS) -> None:
        self.c = controls
        self.wavelength = controls["c_mps"] / controls["carrier_hz"]
        count = controls["frequency_samples"]
        self.frequency_offset = [
            -controls["bandwidth_hz"] / 2
            + index * controls["bandwidth_hz"] / (count - 1)
            for index in range(count)
        ]
        self.frequency = [controls["carrier_hz"] + value for value in self.frequency_offset]
        phases = private_uniform(controls["seed"], len(controls["target_voltage"]))
        self.reflectivity = [
            voltage * cmath.exp(2j * math.pi * phase)
            for voltage, phase in zip(controls["target_voltage"], phases)
        ]
        step = self.frequency_offset[1] - self.frequency_offset[0]
        half = count // 2
        self.range_axis = [
            index * controls["c_mps"] / (2 * count * step)
            for index in range(-half, half + 1)
        ]

    def angles(self, aperture_deg: float) -> list[float]:
        count = self.c["look_count"]
        return [
            math.radians(-aperture_deg / 2 + aperture_deg * index / (count - 1))
            for index in range(count)
        ]

    def history(self, angles: list[float], translation: list[float]) -> list[list[complex]]:
        history: list[list[complex]] = []
        for angle, motion in zip(angles, translation):
            row = [0j] * len(self.frequency)
            projected = [
                motion + x * math.sin(angle) + y * math.cos(angle)
                for x, y in zip(self.c["target_x_m"], self.c["target_y_m"])
            ]
            for reflectivity, target_range in zip(self.reflectivity, projected):
                for index, frequency in enumerate(self.frequency):
                    row[index] += reflectivity * cmath.exp(
                        -4j * math.pi * frequency * target_range / self.c["c_mps"]
                    )
            history.append(row)
        return history

    def align(self, history: list[list[complex]], translation: list[float]) -> list[list[complex]]:
        return [
            [
                value
                * cmath.exp(4j * math.pi * frequency * motion / self.c["c_mps"])
                for value, frequency in zip(row, self.frequency)
            ]
            for row, motion in zip(history, translation)
        ]

    def profiles(self, history: list[list[complex]]) -> list[list[complex]]:
        return [centered_transform(row, inverse=True) for row in history]

    def image(self, profiles: list[list[complex]], angles: list[float]) -> tuple[list[list[complex]], list[float]]:
        look_count = len(angles)
        columns = list(zip(*profiles))
        transformed = [centered_transform(list(column), inverse=False) for column in columns]
        by_angle = [list(row) for row in zip(*transformed)]
        by_angle = [[value / look_count for value in row] for row in by_angle]
        angle_step = sum(
            right - left for left, right in zip(angles, angles[1:])
        ) / (look_count - 1)
        half = look_count // 2
        raw_axis = [
            -self.wavelength * index / (2 * look_count * angle_step)
            for index in range(-half, half + 1)
        ]
        order = sorted(range(look_count), key=raw_axis.__getitem__)
        image = [
            [by_angle[angle_index][range_index] for angle_index in order]
            for range_index in range(len(self.range_axis))
        ]
        return image, [raw_axis[index] for index in order]


def magnitude_correlation(first: list[list[complex]], second: list[list[complex]]) -> float:
    left = [abs(value) for row in first for value in row]
    right = [abs(value) for row in second for value in row]
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    left = [value - left_mean for value in left]
    right = [value - right_mean for value in right]
    return sum(a * b for a, b in zip(left, right)) / math.sqrt(
        sum(value * value for value in left) * sum(value * value for value in right)
    )


def truth_metrics(
    image: list[list[complex]], range_axis: list[float], cross_axis: list[float]
) -> tuple[float, float]:
    mask: set[tuple[int, int]] = set()
    for truth_range, truth_cross in zip(
        BASE_CONTROLS["target_y_m"], BASE_CONTROLS["target_x_m"]
    ):
        r_index = min(range(len(range_axis)), key=lambda index: abs(range_axis[index] - truth_range))
        x_index = min(range(len(cross_axis)), key=lambda index: abs(cross_axis[index] - truth_cross))
        for row in range(max(0, r_index - 1), min(len(range_axis), r_index + 2)):
            for column in range(max(0, x_index - 1), min(len(cross_axis), x_index + 2)):
                mask.add((row, column))
    power = [[abs(value) ** 2 for value in row] for row in image]
    truth = [power[row][column] for row, column in mask]
    background = [
        power[row][column]
        for row in range(len(power))
        for column in range(len(power[0]))
        if (row, column) not in mask
    ]
    background.sort()
    return sum(truth) / sum(map(sum, power)), max(truth) / background[len(background) // 2]


def truth_map_correlation(
    image: list[list[complex]], range_axis: list[float], cross_axis: list[float]
) -> float:
    rows, columns = len(image), len(image[0])
    truth = [[0.0] * columns for _ in range(rows)]
    for truth_range, truth_cross in zip(
        BASE_CONTROLS["target_y_m"], BASE_CONTROLS["target_x_m"]
    ):
        row = min(range(rows), key=lambda index: abs(range_axis[index] - truth_range))
        column = min(range(columns), key=lambda index: abs(cross_axis[index] - truth_cross))
        truth[row][column] += 1.0
    kernel = ((1, 2, 1), (2, 4, 2), (1, 2, 1))
    blurred = [[0.0] * columns for _ in range(rows)]
    for row in range(rows):
        for column in range(columns):
            blurred[row][column] = sum(
                kernel[kr + 1][kc + 1] * truth[row + kr][column + kc]
                for kr in (-1, 0, 1)
                for kc in (-1, 0, 1)
                if 0 <= row + kr < rows and 0 <= column + kc < columns
            ) / 16.0
    return magnitude_correlation(image, blurred)


class P81ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.documents = {
            name: (MODULE / name).read_text(encoding="utf-8")
            for name in ARTIFACTS
            if name != "experiment.m"
        }

    def test_manifest_identity_artifacts_and_permanent_dependency(self) -> None:
        module = self.manifest["modules"][80]
        prerequisite = self.manifest["modules"][79]
        successor = self.manifest["modules"][81]
        self.assertEqual(
            {key: module[key] for key in ("number", "id", "title", "guiding_question", "phase", "folder", "status", "implementation_batch")},
            {
                "number": 81,
                "id": "P81",
                "title": "Form an ISAR Image from a Rotating Target",
                "guiding_question": QUESTION,
                "phase": 9,
                "folder": "modules/81-form-an-isar-image-from-a-rotating-target",
                "status": "implemented",
                "implementation_batch": "P81",
            },
        )
        self.assertEqual(prerequisite["id"], "P80")
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertEqual(successor["id"], "P82")
        self.assertEqual(successor["implementation_batch"], "P82")
        self.assertEqual(artifact_errors(MODULE), [])
        for name in ARTIFACTS:
            self.assertIn(QUESTION, (MODULE / name).read_text(encoding="utf-8"))

    def test_artifact_validation_rejects_missing_empty_and_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            self.assertEqual(artifact_errors(fixture), [])
            (fixture / "lesson.md").unlink()
            self.assertIn("missing lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("empty lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("TODO\n", encoding="utf-8")
            self.assertIn("placeholder remains in lesson.md", artifact_errors(fixture))

    def test_source_binds_model_determinism_sweeps_failure_recovery_and_bounds(self) -> None:
        markers = (
            "baseline_seed = 8101",
            "private_uniform",
            "synthesize_history",
            "range_compress",
            "align_translation",
            "form_isar_image",
            "exp(-1j*4*pi*frequency_hz",
            "exp(1j*4*pi*(translation_m(:)*frequency_hz)",
            "aperture_sweep_deg = [2 4 6 8]",
            "rotation_rate_sweep_deg_s = [3 6 12]",
            "Intentionally broken case",
            "measurement_before_failure",
            "recovery_exact_match",
            "maximum_coherent_contributions = 900000",
            "maximum_working_value_equivalents = 2500000",
            "P81:PositiveSweep",
            "P81:FrequencyGrid",
            "P81:CompleteRangeSupport",
            "P81:RotationalNyquist",
        )
        for marker in markers:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P81"), 5)
        self.assertNotIn("rng(", self.source.lower())

    def test_source_has_no_opaque_toolbox_or_external_side_effect(self) -> None:
        lowered = self.source.lower()
        forbidden = (
            "phased.",
            "isar(",
            "rangecompressor",
            "awgn(",
            "rand(",
            "randn(",
            "parfor",
            "gpuarray",
            "batch(",
            "timer(",
            "fopen(",
            "writematrix",
            "save(",
            "webread",
            "system(",
            "unix(",
        )
        source_without_comments = "\n".join(
            line for line in lowered.splitlines() if not line.lstrip().startswith("%")
        )
        for token in forbidden:
            self.assertNotIn(token, source_without_comments)

    def test_control_contract_accepts_baseline_and_rejects_malformed_resources(self) -> None:
        self.assertEqual(controls_errors(copy.deepcopy(BASE_CONTROLS)), [])
        history_count = 1 + len(BASE_CONTROLS["aperture_sweep_deg"]) + len(BASE_CONTROLS["rate_sweep_deg_s"])
        self.assertEqual(
            history_count
            * BASE_CONTROLS["look_count"]
            * BASE_CONTROLS["frequency_samples"]
            * len(BASE_CONTROLS["target_x_m"]),
            670_800,
        )
        malformed_cases = (
            ("seed", True),
            ("seed", 0),
            ("seed", 2_147_483_647),
            ("frequency_samples", 128),
            ("frequency_samples", 3),
            ("look_count", 65.5),
            ("carrier_hz", float("nan")),
            ("bandwidth_hz", 0),
            ("baseline_aperture_deg", -1),
            ("baseline_rate_deg_s", 0),
            ("translation_velocity_mps", -1),
            ("display_floor_db", 0),
            ("aperture_sweep_deg", [2, [4], 6]),
            ("aperture_sweep_deg", [2, 2, 6]),
            ("rate_sweep_deg_s", [3, float("inf"), 12]),
            ("target_x_m", [0] * 9),
            ("target_voltage", [1] * 9 + [0]),
            ("max_frequency_samples", 100),
            ("max_look_count", 20),
            ("max_target_count", 5),
            ("max_sweep_cases", 2),
            ("max_private_values", 5),
            ("max_contributions", 100),
            ("translation_velocity_mps", 100),
        )
        for key, value in malformed_cases:
            with self.subTest(key=key, value=value):
                malformed = copy.deepcopy(BASE_CONTROLS)
                malformed[key] = value
                self.assertTrue(controls_errors(malformed))
        out_of_support = copy.deepcopy(BASE_CONTROLS)
        out_of_support["target_x_m"][0] = 10
        self.assertIn("target cross-range exceeds unambiguous support", controls_errors(out_of_support))
        out_of_range = copy.deepcopy(BASE_CONTROLS)
        out_of_range["target_y_m"][0] = 20
        self.assertIn("target range exceeds unambiguous support", controls_errors(out_of_range))

    def test_private_generator_is_repeatable_bounded_and_isolated(self) -> None:
        first = private_uniform(8101, 10)
        self.assertEqual(first, private_uniform(8101, 10))
        self.assertAlmostEqual(first[0], 0.06340141737060688, places=15)
        self.assertTrue(all(0 < value < 1 for value in first))
        for seed, count in ((True, 2), (0, 2), (8101, True), (8101, 0), (8101, 65)):
            with self.subTest(seed=seed, count=count), self.assertRaises(ValueError):
                private_uniform(seed, count)

    def test_independent_full_image_oracle_exposes_alignment_blur_and_recovery(self) -> None:
        oracle = Oracle()
        angles = oracle.angles(BASE_CONTROLS["baseline_aperture_deg"])
        rate = math.radians(BASE_CONTROLS["baseline_rate_deg_s"])
        slow_time = [angle / rate for angle in angles]
        translation = [BASE_CONTROLS["translation_velocity_mps"] * value for value in slow_time]
        raw = oracle.history(angles, translation)
        retained = copy.deepcopy(raw)
        aligned = oracle.align(raw, translation)
        aligned_image, cross_axis = oracle.image(oracle.profiles(aligned), angles)
        broken_image, broken_axis = oracle.image(oracle.profiles(raw), angles)
        recovered = oracle.align(retained, translation)
        recovered_image, recovered_axis = oracle.image(oracle.profiles(recovered), angles)
        capture, ratio = truth_metrics(aligned_image, oracle.range_axis, cross_axis)
        broken_capture, _ = truth_metrics(broken_image, oracle.range_axis, broken_axis)
        self.assertGreater(capture, 0.90)
        self.assertGreater(ratio, 1_000_000)
        self.assertLess(broken_capture, 0.20)
        self.assertLess(magnitude_correlation(aligned_image, broken_image), 0.30)
        self.assertEqual(raw, retained)
        self.assertEqual(recovered, aligned)
        self.assertEqual(recovered_axis, cross_axis)
        self.assertEqual(recovered_image, aligned_image)
        self.assertAlmostEqual(capture, 0.95932265626204, places=10)
        self.assertAlmostEqual(
            magnitude_correlation(aligned_image, broken_image),
            0.24668362243508937,
            places=10,
        )

    def test_asymmetric_scatterer_preserves_range_and_cross_range_handedness(self) -> None:
        controls = copy.deepcopy(BASE_CONTROLS)
        controls["target_x_m"] = [1.13]
        controls["target_y_m"] = [0.75]
        controls["target_voltage"] = [1.0]
        self.assertEqual(controls_errors(controls), [])

        oracle = Oracle(controls)
        angles = oracle.angles(controls["baseline_aperture_deg"])
        image, cross_axis = oracle.image(
            oracle.profiles(oracle.history(angles, [0.0] * len(angles))),
            angles,
        )
        peak_row, peak_column = max(
            (
                (row, column)
                for row in range(len(image))
                for column in range(len(image[0]))
            ),
            key=lambda location: abs(image[location[0]][location[1]]),
        )
        range_spacing = oracle.range_axis[1] - oracle.range_axis[0]
        cross_range_spacing = cross_axis[1] - cross_axis[0]

        self.assertGreater(cross_axis[peak_column], 0.0)
        self.assertAlmostEqual(
            oracle.range_axis[peak_row],
            controls["target_y_m"][0],
            delta=range_spacing / 2,
        )
        self.assertAlmostEqual(
            cross_axis[peak_column],
            controls["target_x_m"][0],
            delta=cross_range_spacing / 2,
        )
        self.assertIn(
            "raw_cross_range_m = -wavelength_m*angle_frequency_cycles_per_rad/2",
            self.source,
        )

    def test_aperture_and_rate_sweeps_preserve_one_variable_interpretation(self) -> None:
        wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
        resolutions = [
            wavelength / (2 * math.radians(aperture))
            for aperture in BASE_CONTROLS["aperture_sweep_deg"]
        ]
        self.assertTrue(all(right < left for left, right in zip(resolutions, resolutions[1:])))
        self.assertAlmostEqual(resolutions[2], 0.1432394487827058, places=12)
        cpis = [
            BASE_CONTROLS["baseline_aperture_deg"] / rate
            for rate in BASE_CONTROLS["rate_sweep_deg_s"]
        ]
        dopplers = [
            2
            * max(map(abs, BASE_CONTROLS["target_x_m"]))
            * math.radians(rate)
            / wavelength
            for rate in BASE_CONTROLS["rate_sweep_deg_s"]
        ]
        self.assertEqual(cpis, [2.0, 1.0, 0.5])
        self.assertTrue(all(right > left for left, right in zip(dopplers, dopplers[1:])))
        self.assertAlmostEqual(dopplers[1], 13.962634015954638, places=12)
        self.assertIn("same 65 aspect angles", self.documents["lesson.md"])
        self.assertIn("when total angular aperture is held fixed", self.documents["lesson.md"])

        oracle = Oracle()
        aperture_correlations = []
        for aperture in BASE_CONTROLS["aperture_sweep_deg"]:
            angles = oracle.angles(aperture)
            times = [angle / math.radians(BASE_CONTROLS["baseline_rate_deg_s"]) for angle in angles]
            translation = [BASE_CONTROLS["translation_velocity_mps"] * value for value in times]
            history = oracle.history(angles, translation)
            image, cross_axis = oracle.image(
                oracle.profiles(oracle.align(history, translation)), angles
            )
            aperture_correlations.append(
                truth_map_correlation(image, oracle.range_axis, cross_axis)
            )
        self.assertGreater(aperture_correlations[-1], aperture_correlations[0] + 0.05)
        self.assertAlmostEqual(aperture_correlations[0], 0.7290789461257223, places=10)
        self.assertAlmostEqual(aperture_correlations[-1], 0.7920998388693862, places=10)

        rate_images = []
        angles = oracle.angles(BASE_CONTROLS["baseline_aperture_deg"])
        for rate_deg_s in BASE_CONTROLS["rate_sweep_deg_s"]:
            times = [angle / math.radians(rate_deg_s) for angle in angles]
            translation = [BASE_CONTROLS["translation_velocity_mps"] * value for value in times]
            history = oracle.history(angles, translation)
            image, _ = oracle.image(oracle.profiles(oracle.align(history, translation)), angles)
            rate_images.append(image)
        self.assertTrue(
            all(magnitude_correlation(rate_images[1], image) > 1 - 1.0e-12 for image in rate_images)
        )

    def test_limiting_cases_and_sign_conventions_are_explicit(self) -> None:
        combined = "\n".join(self.documents.values())
        for marker in (
            "zero angular aperture",
            "small-angle",
            "Angular undersampling",
            "nonuniform rate",
            "aspect-dependent",
            "4 pi",
            "x = -(lambda/2) f_theta",
            "offset-frequency term",
            "carrier term",
            "rotational migration",
            "literal optical photograph",
        ):
            self.assertIn(marker.lower(), combined.lower())

    def test_documents_are_concept_first_complete_and_not_placeholders(self) -> None:
        combined = "\n".join(self.documents.values())
        for marker in (
            "P18",
            "P80",
            "base MATLAB R2016b",
            "two sweeps",
            "Ctrl+C",
            "rollback",
            "unchanged raw complex",
            "static validation",
            "MATLAB runtime",
            "physical radar/HIL",
        ):
            self.assertIn(marker.lower(), combined.lower())
        self.assertGreaterEqual(self.documents["checks.md"].count("**Answer:**"), 40)
        self.assertIsNone(re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", combined, re.IGNORECASE))

    def _run_fixture_cli(self, manifest: dict, *args: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            (fixture / "bin").mkdir()
            (fixture / "curriculum").mkdir()
            shutil.copy2(CLI, fixture / "bin" / "learn")
            (fixture / "curriculum" / "modules.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            for module in manifest["modules"]:
                readme = fixture / module["folder"] / "README.md"
                readme.parent.mkdir(parents=True)
                readme.write_text(f"# {module['id']}\n", encoding="utf-8")
            state = fixture / ".learning" / "progress.json"
            state.parent.mkdir()
            state.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P79",
                        "completed": [f"P{number:02d}" for number in range(1, 80)],
                        "notes": {},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            return subprocess.run(
                [str(fixture / "bin" / "learn"), *args],
                cwd=fixture,
                text=True,
                capture_output=True,
                timeout=3,
                env=os.environ.copy(),
            )

    def test_cli_timeout_rollback_recovery_isolation_and_future_compatibility(self) -> None:
        repository_state = ROOT / ".learning" / "progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        started = self._run_fixture_cli(copy.deepcopy(self.manifest), "start", "81")
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertIn("P81 — Form an ISAR Image from a Rotating Target", started.stdout)
        rollback = copy.deepcopy(self.manifest)
        rollback["modules"][80]["status"] = "scaffolded"
        refused = self._run_fixture_cli(rollback, "start", "81")
        self.assertEqual(refused.returncode, 3)
        self.assertIn("awaits Portfolio batch P81", refused.stdout)
        fallback = self._run_fixture_cli(rollback, "start")
        self.assertEqual(fallback.returncode, 0, fallback.stderr)
        self.assertIn("P80 — Inject SAR Motion Error and Apply Autofocus", fallback.stdout)
        future = copy.deepcopy(self.manifest)
        future["modules"][81]["status"] = "implemented"
        future["modules"][81]["future_metadata"] = {"compatible": True}
        selected = self._run_fixture_cli(future, "start", "81")
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertIn("P81 — Form an ISAR Image from a Rotating Target", selected.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_actual_matlab_script_is_repeatable_and_bounded_when_available(self) -> None:
        matlab = shutil.which("matlab")
        if matlab is None:
            self.skipTest("MATLAB executable is unavailable; runtime is not claimed")
        command = (
            "rng_before=rng; run('experiment.m'); first_results=p81_results; "
            "rng_after_first=rng; assert(first_results.recovery_exact_match); "
            "assert(first_results.executed_contributions==670800); "
            "assert(first_results.baseline_metrics.truth_capture>0.30); "
            "assert(first_results.broken_metrics.reference_correlation<0.65); "
            "assert(isequaln(rng_before,rng_after_first)); run('experiment.m'); "
            "assert(isequaln(first_results,p81_results)); assert(isequaln(rng_before,rng)); "
            "assert(numel(findall(0,'Type','figure','Tag','P81'))==5); "
            "close(findall(0,'Type','figure','Tag','P81'));"
        )
        wrapped = (
            "try; set(0,'DefaultFigureVisible','off'); "
            + command
            + " exit(0); catch ME; disp(getReport(ME)); exit(1); end"
        )
        completed = subprocess.run(
            [matlab, "-nosplash", "-nodesktop", "-nodisplay", "-r", wrapped],
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

    def test_catalogs_evidence_and_exact_eof_policy(self) -> None:
        self.assertIn(
            "Project 81 keeps the radar fixed",
            (ROOT / "README.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Project 81 follows P80",
            (ROOT / "START_HERE.md").read_text(encoding="utf-8"),
        )
        self.assertRegex(
            (ROOT / "modules" / "README.md").read_text(encoding="utf-8"),
            r"\| \[P81\].*\| implemented \|",
        )
        evidence = EVIDENCE.read_text(encoding="utf-8")
        for heading in (
            "## Claim boundary",
            "## Acceptance map",
            "## Deterministic simulated-oracle results",
            "## Figure and metric inventory",
            "## Exact commands and results",
            "## Changed and preserved invariants",
            "## Residual risks",
            "## Rollback",
            "## Unperformed validation",
        ):
            self.assertIn(heading, evidence)
        paths = [
            *[MODULE / name for name in ARTIFACTS],
            ROOT / "curriculum" / "modules.json",
            ROOT / "README.md",
            ROOT / "START_HERE.md",
            ROOT / "modules" / "README.md",
            Path(__file__),
            EVIDENCE,
        ]
        for path in paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
