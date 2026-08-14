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
MODULE = ROOT / "modules/80-inject-sar-motion-error-and-apply-autofocus"
EVIDENCE = ROOT / "docs/evidence/P80-2026-08-13.md"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How small a platform-position error is enough to blur a coherent image?"

BASE_CONTROLS = {
    "seed": 8001,
    "c_mps": 3.0e8,
    "carrier_hz": 10.0e9,
    "reference_range_m": 1000.0,
    "bandwidth_hz": 200.0e6,
    "frequency_samples": 129,
    "aperture_length_m": 30.0,
    "platform_spacing_m": 0.25,
    "image_x_m": [-4.0 + 0.02 * index for index in range(401)],
    "image_range_offset_m": [-15.0 + 0.375 * index for index in range(81)],
    "target_x_m": [-1.0, 0.35, 1.45],
    "target_range_offset_m": [-10.0, 0.0, 9.0],
    "target_voltage": [1.0, 0.70, 0.50],
    "reference_gate": 1,
    "measurement_snr_db": 35.0,
    "baseline_error_fraction": 1 / 8,
    "baseline_random_fraction": 0.25,
    "error_fraction_sweep": [0.0, 1 / 32, 1 / 16, 1 / 8, 1 / 4],
    "random_fraction_sweep": [0.0, 0.25, 0.50, 0.75, 1.0],
    "broken_interferer_voltage": 0.95,
    "display_floor_db": -45.0,
    "max_aperture_samples": 161,
    "max_image_x_samples": 501,
    "max_image_range_samples": 101,
    "max_frequency_samples": 257,
    "max_targets": 4,
    "max_sweep_cases": 6,
    "max_private_values": 2048,
    "max_focus_operations": 4_500_000,
    "max_working_values": 2_000_000,
    "max_figures": 5,
    "max_phase_increment_rad": 0.90 * math.pi,
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
        "image_x_m", "image_range_offset_m", "target_x_m",
        "target_range_offset_m", "target_voltage", "error_fraction_sweep",
        "random_fraction_sweep",
    )
    for name in vectors:
        value = controls.get(name)
        if (
            not isinstance(value, list)
            or not value
            or any(isinstance(item, (bool, complex, list, tuple)) for item in value)
            or any(not isinstance(item, (int, float)) or not math.isfinite(item) for item in value)
        ):
            errors.append(f"invalid vector: {name}")
    scalar_names = (
        "c_mps", "carrier_hz", "reference_range_m", "bandwidth_hz",
        "frequency_samples", "aperture_length_m", "platform_spacing_m",
        "reference_gate", "measurement_snr_db", "baseline_error_fraction",
        "baseline_random_fraction", "broken_interferer_voltage",
        "display_floor_db", "max_aperture_samples", "max_image_x_samples",
        "max_image_range_samples", "max_frequency_samples", "max_targets",
        "max_sweep_cases", "max_private_values", "max_focus_operations",
        "max_working_values", "max_figures", "max_phase_increment_rad",
    )
    for name in scalar_names:
        value = controls.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"invalid scalar: {name}")
    seed = controls.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 1 <= seed < 2_147_483_647:
        errors.append("invalid seed")
    if errors:
        return errors

    positive = tuple(name for name in scalar_names if name not in ("display_floor_db", "baseline_random_fraction"))
    if any(controls[name] <= 0 for name in positive) or controls["display_floor_db"] >= 0:
        errors.append("nonpositive control")
    if not 0 <= controls["baseline_random_fraction"] <= 1:
        errors.append("invalid baseline mixture")
    integer_names = (
        "frequency_samples", "reference_gate", "max_aperture_samples",
        "max_image_x_samples", "max_image_range_samples", "max_frequency_samples",
        "max_targets", "max_sweep_cases", "max_private_values",
        "max_focus_operations", "max_working_values", "max_figures",
    )
    if any(controls[name] != math.floor(controls[name]) for name in integer_names):
        errors.append("noninteger count")
    if controls["frequency_samples"] < 3 or controls["frequency_samples"] % 2 != 1:
        errors.append("frequency count must be odd")
    for name in ("image_x_m", "image_range_offset_m", "error_fraction_sweep", "random_fraction_sweep"):
        if any(right <= left for left, right in zip(controls[name], controls[name][1:])):
            errors.append(f"unordered {name}")
    if (
        controls["error_fraction_sweep"][0] != 0
        or any(value < 0 for value in controls["error_fraction_sweep"])
        or controls["random_fraction_sweep"][0] != 0
        or controls["random_fraction_sweep"][-1] != 1
        or any(not 0 <= value <= 1 for value in controls["random_fraction_sweep"])
    ):
        errors.append("invalid sweep support")
    count = len(controls["target_x_m"])
    if not count == len(controls["target_range_offset_m"]) == len(controls["target_voltage"]):
        errors.append("incompatible target scene")
        return errors
    if any(value <= 0 for value in controls["target_voltage"]):
        errors.append("nonpositive target")
    gate = controls["reference_gate"] - 1
    if gate not in range(count) or controls["target_voltage"][gate] != max(controls["target_voltage"]):
        errors.append("invalid reference gate")
    if any(controls["reference_range_m"] + value <= 0 for value in controls["target_range_offset_m"]):
        errors.append("nonpositive scene range")
    if any(not controls["image_x_m"][0] <= value <= controls["image_x_m"][-1] for value in controls["target_x_m"]):
        errors.append("target outside cross-range support")
    if any(not controls["image_range_offset_m"][0] <= value <= controls["image_range_offset_m"][-1] for value in controls["target_range_offset_m"]):
        errors.append("target outside range support")
    ratio = controls["aperture_length_m"] / controls["platform_spacing_m"]
    if abs(ratio - round(ratio)) > 1e-10:
        errors.append("off-grid aperture")
        return errors
    aperture_count = round(ratio) + 1
    if (
        aperture_count > controls["max_aperture_samples"]
        or len(controls["image_x_m"]) > controls["max_image_x_samples"]
        or len(controls["image_range_offset_m"]) > controls["max_image_range_samples"]
        or controls["frequency_samples"] > controls["max_frequency_samples"]
        or count > controls["max_targets"]
        or max(len(controls["error_fraction_sweep"]), len(controls["random_fraction_sweep"])) > controls["max_sweep_cases"]
        or 2 * aperture_count * count > controls["max_private_values"]
    ):
        errors.append("resource ceiling")
    focus_count = 3 + 2 * len(controls["error_fraction_sweep"]) + 2 * len(controls["random_fraction_sweep"]) + 2
    operations = (
        focus_count * aperture_count * len(controls["image_x_m"]) * count
        + 5 * len(controls["image_range_offset_m"]) * count
        * (controls["frequency_samples"] + len(controls["image_x_m"]))
    )
    if operations > controls["max_focus_operations"]:
        errors.append("operation ceiling")
    return errors


def private_uniform(seed: int, count: int, maximum: int = 2048) -> list[float]:
    if isinstance(seed, bool) or not isinstance(seed, int) or not 1 <= seed < 2_147_483_647:
        raise ValueError("invalid seed")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= maximum:
        raise ValueError("invalid count")
    state = seed
    values: list[float] = []
    for _ in range(count):
        state = (16807 * state) % 2_147_483_647
        values.append((state + 0.5) / 2_147_483_647)
    return values


def private_normal(seed: int, count: int) -> list[float]:
    uniforms = private_uniform(seed, 2 * math.ceil(count / 2))
    values: list[float] = []
    for index in range(0, len(uniforms), 2):
        radius = math.sqrt(-2 * math.log(uniforms[index]))
        angle = 2 * math.pi * uniforms[index + 1]
        values.extend((radius * math.cos(angle), radius * math.sin(angle)))
    return values[:count]


def normalize(values: list[float]) -> list[float]:
    average = sum(values) / len(values)
    centered = [value - average for value in values]
    rms = math.sqrt(sum(value * value for value in centered) / len(centered))
    if rms <= 0:
        raise ValueError("zero template")
    return [value / rms for value in centered]


def convolve_same(values: list[float], kernel: list[float]) -> list[float]:
    radius = len(kernel) // 2
    return [
        sum(values[source] * kernel[tap] for tap in range(len(kernel)) if 0 <= (source := index + tap - radius) < len(values))
        for index in range(len(values))
    ]


def build_model() -> dict:
    c = BASE_CONTROLS
    wavelength = c["c_mps"] / c["carrier_hz"]
    count = round(c["aperture_length_m"] / c["platform_spacing_m"]) + 1
    platform = [-c["aperture_length_m"] / 2 + index * c["platform_spacing_m"] for index in range(count)]
    ranges = [c["reference_range_m"] + offset for offset in c["target_range_offset_m"]]
    phases = private_uniform(c["seed"], len(c["target_voltage"]))
    reflectivity = [voltage * cmath.exp(1j * 2 * math.pi * phase) for voltage, phase in zip(c["target_voltage"], phases)]
    signal = [
        [
            reflectivity[target] * cmath.exp(
                -1j * 4 * math.pi * (math.hypot(position - c["target_x_m"][target], ranges[target]) - c["reference_range_m"]) / wavelength
            )
            for target in range(len(ranges))
        ]
        for position in platform
    ]
    normal = private_normal(c["seed"] + 1, 2 * count * len(ranges))
    scale = 10 ** (-c["measurement_snr_db"] / 20) / math.sqrt(2)
    flat_noise = [scale * complex(normal[index], normal[count * len(ranges) + index]) for index in range(count * len(ranges))]
    # MATLAB reshape fills columns first: each target gate receives one
    # contiguous aperture-length block from the deterministic stream.
    noise = [
        [flat_noise[target * count + look] for target in range(len(ranges))]
        for look in range(count)
    ]
    unit = [(position - platform[0]) / (platform[-1] - platform[0]) for position in platform]
    smooth = normalize([math.sin(2 * math.pi * value + 0.3) + 0.35 * math.sin(6 * math.pi * value - 0.4) for value in unit])
    raw = [value - 0.5 for value in private_uniform(c["seed"] + 2, count)]
    random_template = normalize(convolve_same(raw, [1 / 16, 2 / 16, 3 / 16, 4 / 16, 3 / 16, 2 / 16, 1 / 16]))
    return {"wavelength": wavelength, "platform": platform, "ranges": ranges, "signal": signal, "noise": noise, "smooth": smooth, "random": random_template}


def mix_template(model: dict, alpha: float) -> list[float]:
    return normalize([(1 - alpha) * smooth + alpha * random for smooth, random in zip(model["smooth"], model["random"])])


def errored_history(model: dict, fraction: float, alpha: float = 0.25) -> tuple[list[list[complex]], list[float]]:
    phase = [-4 * math.pi * fraction * value for value in mix_template(model, alpha)]
    history = [
        [signal * cmath.exp(1j * error) + noise for signal, noise in zip(signal_row, noise_row)]
        for signal_row, noise_row, error in zip(model["signal"], model["noise"], phase)
    ]
    return history, phase


def focus(model: dict, history: list[list[complex]]) -> list[list[complex]]:
    c = BASE_CONTROLS
    output: list[list[complex]] = []
    for target, target_range in enumerate(model["ranges"]):
        cut: list[complex] = []
        for candidate in c["image_x_m"]:
            contributions = [
                row[target] * cmath.exp(
                    1j * 4 * math.pi * (math.hypot(position - candidate, target_range) - c["reference_range_m"]) / model["wavelength"]
                )
                for row, position in zip(history, model["platform"])
            ]
            cut.append(sum(contributions) / len(contributions))
        output.append(cut)
    return output


def phase_estimate(model: dict, history: list[list[complex]], contaminated: bool = False) -> list[float]:
    c = BASE_CONTROLS
    target = c["reference_gate"] - 1
    deramped: list[complex] = []
    for row, position in zip(history, model["platform"]):
        value = row[target]
        if contaminated:
            value += c["broken_interferer_voltage"] * row[1]
        nominal_range = math.hypot(position - c["target_x_m"][target], model["ranges"][target])
        deramped.append(value * cmath.exp(1j * 4 * math.pi * (nominal_range - c["reference_range_m"]) / model["wavelength"]))
    estimate = [cmath.phase(deramped[0])]
    for current, previous in zip(deramped[1:], deramped):
        estimate.append(estimate[-1] + cmath.phase(current * previous.conjugate()))
    return estimate


def correct(history: list[list[complex]], estimate: list[float]) -> list[list[complex]]:
    return [[value * cmath.exp(-1j * phase) for value in row] for row, phase in zip(history, estimate)]


def metrics(focused: list[list[complex]], ideal: list[list[complex]]) -> tuple[float, float]:
    peaks: list[float] = []
    entropies: list[float] = []
    for cut, ideal_cut in zip(focused, ideal):
        peaks.append(max(map(abs, cut)) / max(map(abs, ideal_cut)))
        intensity = [abs(value) ** 2 for value in cut]
        total = sum(intensity)
        probability = [value / total for value in intensity]
        entropies.append(-sum(value * math.log(max(value, float.fromhex("0x1.0p-1022"))) for value in probability))
    return sum(peaks) / len(peaks), sum(entropies) / len(entropies)


def compose_image(focused: list[list[complex]]) -> list[list[complex]]:
    c = BASE_CONTROLS
    frequency_offsets = [
        -c["bandwidth_hz"] / 2
        + index * c["bandwidth_hz"] / (c["frequency_samples"] - 1)
        for index in range(c["frequency_samples"])
    ]
    range_responses = [
        [
            sum(
                cmath.exp(
                    1j * 4 * math.pi * frequency * (candidate - target) / c["c_mps"]
                )
                for frequency in frequency_offsets
            )
            / len(frequency_offsets)
            for target in c["target_range_offset_m"]
        ]
        for candidate in c["image_range_offset_m"]
    ]
    return [
        [
            sum(
                response[target] * focused[target][cross_range]
                for target in range(len(response))
            )
            for cross_range in range(len(c["image_x_m"]))
        ]
        for response in range_responses
    ]


def image_entropy(image: list[list[complex]]) -> float:
    intensity = [abs(value) ** 2 for row in image for value in row]
    total = sum(intensity)
    probability = [value / total for value in intensity]
    return -sum(
        value * math.log(max(value, float.fromhex("0x1.0p-1022")))
        for value in probability
    )


class P80ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
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
        return subprocess.run(
            [str(fixture / "bin/learn"), *args], cwd=fixture,
            text=True, capture_output=True, timeout=3,
        )

    def test_manifest_identity_artifacts_and_permanent_dependency(self) -> None:
        current = module_entry(self.data, "P80")
        prerequisite = module_entry(self.data, "P79")
        successor = module_entry(self.data, "P81")
        self.assertEqual(
            {key: current[key] for key in ("number", "id", "title", "guiding_question", "phase", "slug", "folder", "status", "implementation_batch")},
            {
                "number": 80, "id": "P80", "title": "Inject SAR Motion Error and Apply Autofocus",
                "guiding_question": QUESTION, "phase": 9,
                "slug": "inject-sar-motion-error-and-apply-autofocus",
                "folder": "modules/80-inject-sar-motion-error-and-apply-autofocus",
                "status": "implemented", "implementation_batch": "P80",
            },
        )
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertEqual(successor["implementation_batch"], "P81")
        self.assertEqual(artifact_errors(MODULE), [])
        for name in ARTIFACTS:
            self.assertIn(QUESTION, (MODULE / name).read_text(encoding="utf-8"))

    def test_artifact_validation_rejects_missing_empty_and_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            self.assertEqual(artifact_errors(fixture), [])
            (fixture / "lesson.md").unlink()
            self.assertIn("missing lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("\n", encoding="utf-8")
            self.assertIn("empty lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("TODO placeholder\n", encoding="utf-8")
            self.assertIn("TODO remains in lesson.md", artifact_errors(fixture))

    def test_source_binds_determinism_sweeps_failure_recovery_and_bounds(self) -> None:
        for marker in (
            "baseline_seed = 8001;", "carrier_frequency_hz = 10.0e9;",
            "baseline_error_rms_fraction = 1/8;",
            "error_rms_fraction_sweep = [0 1/32 1/16 1/8 1/4];",
            "random_fraction_sweep = [0 0.25 0.50 0.75 1.0];",
            "maximum_focus_operations = 4500000;",
            "maximum_working_value_equivalents = 2000000;",
            "propagation_phase_rad = -4*pi*",
            "phase_increment_rad = angle(nominally_deramped(2:end).*",
            "cumsum(phase_increment_rad)", "P80:BaselineAutofocus",
            "P80:ErrorMagnitudeSweep", "P80:ErrorCompositionSweep",
            "P80:ContaminatedReferenceRecovery", "P80:OperationAccounting",
            "measurement_before_failure", "recovery_exact_match",
            "predicted_focus_operations = validate_controls(controls);",
            "image_sum_operations = numel(range_axis_m)*size(focused_gates, 2)*",
            "pre_results_workspace_inventory = whos;",
        ):
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P80"), 5)
        self.assertNotIn("rng(", self.source.lower())

    def test_source_has_no_opaque_toolbox_or_external_side_effect(self) -> None:
        lowered = self.source.lower()
        for forbidden in (
            "phased.", "sarprocessor", "rangecompressor", "autofocus(",
            "backprojection(", "awgn(", "rand(", "randn(", "unwrap(",
            "parfor", "timer(", "pause(", "webread(", "webwrite(",
            "fopen(", "save(", "writematrix(", "system(", "unix(",
            "dos(", "gpuarray(", "batch(",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_control_contract_accepts_baseline_and_rejects_malformed_resources(self) -> None:
        self.assertEqual(controls_errors(copy.deepcopy(BASE_CONTROLS)), [])
        aperture_count = round(
            BASE_CONTROLS["aperture_length_m"]
            / BASE_CONTROLS["platform_spacing_m"]
        ) + 1
        target_count = len(BASE_CONTROLS["target_x_m"])
        focus_calls = (
            3
            + 2 * len(BASE_CONTROLS["error_fraction_sweep"])
            + 2 * len(BASE_CONTROLS["random_fraction_sweep"])
            + 2
        )
        focus_contributions = (
            focus_calls
            * aperture_count
            * len(BASE_CONTROLS["image_x_m"])
            * target_count
        )
        range_response_contributions = (
            5
            * len(BASE_CONTROLS["image_range_offset_m"])
            * BASE_CONTROLS["frequency_samples"]
            * target_count
        )
        target_image_contributions = (
            5
            * len(BASE_CONTROLS["image_range_offset_m"])
            * len(BASE_CONTROLS["image_x_m"])
            * target_count
        )
        self.assertEqual(target_image_contributions, 487_215)
        self.assertEqual(
            focus_contributions
            + range_response_contributions
            + target_image_contributions,
            4_283_025,
        )
        self.assertLess(4_283_025, BASE_CONTROLS["max_focus_operations"])
        cases: list[dict] = []
        nested = copy.deepcopy(BASE_CONTROLS); nested["error_fraction_sweep"] = [[0.0], [0.25]]; cases.append(nested)
        nonfinite = copy.deepcopy(BASE_CONTROLS); nonfinite["image_x_m"][4] = math.nan; cases.append(nonfinite)
        boolean = copy.deepcopy(BASE_CONTROLS); boolean["carrier_hz"] = True; cases.append(boolean)
        bad_seed = copy.deepcopy(BASE_CONTROLS); bad_seed["seed"] = 0; cases.append(bad_seed)
        negative = copy.deepcopy(BASE_CONTROLS); negative["bandwidth_hz"] = -1; cases.append(negative)
        even = copy.deepcopy(BASE_CONTROLS); even["frequency_samples"] = 128; cases.append(even)
        unordered = copy.deepcopy(BASE_CONTROLS); unordered["random_fraction_sweep"] = [0.0, 1.0, 0.5]; cases.append(unordered)
        off_grid = copy.deepcopy(BASE_CONTROLS); off_grid["platform_spacing_m"] = 0.26; cases.append(off_grid)
        incompatible = copy.deepcopy(BASE_CONTROLS); incompatible["target_voltage"].pop(); cases.append(incompatible)
        weak_reference = copy.deepcopy(BASE_CONTROLS); weak_reference["reference_gate"] = 2; cases.append(weak_reference)
        outside = copy.deepcopy(BASE_CONTROLS); outside["target_x_m"][1] = 5.0; cases.append(outside)
        samples = copy.deepcopy(BASE_CONTROLS); samples["max_aperture_samples"] = 100; cases.append(samples)
        operations = copy.deepcopy(BASE_CONTROLS); operations["max_focus_operations"] = 1000; cases.append(operations)
        for malformed in cases:
            with self.subTest(keys=[key for key in malformed if malformed[key] != BASE_CONTROLS.get(key)]):
                self.assertTrue(controls_errors(malformed))

    def test_private_generators_are_repeatable_bounded_and_isolated(self) -> None:
        first = private_uniform(8001, 3)
        second = private_uniform(8001, 3)
        self.assertEqual(first, second)
        self.assertAlmostEqual(first[0], 0.06261878067749496, places=15)
        self.assertEqual(private_normal(8002, 6), private_normal(8002, 6))
        with self.assertRaises(ValueError):
            private_uniform(True, 3)
        with self.assertRaises(ValueError):
            private_uniform(8001, 2049)

    def test_independent_oracle_exposes_blur_and_autofocus_recovery(self) -> None:
        model = build_model()
        ideal_history, _ = errored_history(model, 0.0)
        ideal = focus(model, ideal_history)
        history, phase = errored_history(model, 1 / 8)
        blurred = focus(model, history)
        estimate = phase_estimate(model, history)
        corrected = focus(model, correct(history, estimate))
        blurred_peak, blurred_entropy = metrics(blurred, ideal)
        corrected_peak, corrected_entropy = metrics(corrected, ideal)
        centered_error = [value - sum(phase) / len(phase) for value in phase]
        centered_estimate = [value - sum(estimate) / len(estimate) for value in estimate]
        rmse = math.sqrt(sum((left - right) ** 2 for left, right in zip(centered_error, centered_estimate)) / len(phase))
        self.assertLess(blurred_peak, 0.65)
        self.assertGreater(corrected_peak, 0.95)
        self.assertLess(corrected_entropy, blurred_entropy - 0.8)
        self.assertLess(rmse, 0.05)
        self.assertAlmostEqual(blurred_peak, 0.5411889185807143, places=10)
        self.assertAlmostEqual(corrected_peak, 1.0013900132232754, places=10)

    def test_constant_phase_rotates_while_linear_phase_shifts_without_defocus(self) -> None:
        model = build_model()
        ideal = focus(model, model["signal"])

        constant_phase = 1.1
        constant_history = [
            [value * cmath.exp(1j * constant_phase) for value in row]
            for row in model["signal"]
        ]
        constant_focus = focus(model, constant_history)
        for ideal_cut, rotated_cut in zip(ideal, constant_focus):
            for ideal_value, rotated_value in zip(ideal_cut, rotated_cut):
                self.assertAlmostEqual(abs(rotated_value), abs(ideal_value), places=12)

        aperture_start = model["platform"][0]
        aperture_length = model["platform"][-1] - aperture_start
        linear_phase = [
            2 * math.pi * (position - aperture_start) / aperture_length
            for position in model["platform"]
        ]
        linear_history = [
            [value * cmath.exp(1j * phase) for value in row]
            for row, phase in zip(model["signal"], linear_phase)
        ]
        shifted = focus(model, linear_history)
        for ideal_cut, shifted_cut in zip(ideal, shifted):
            ideal_peak = max(range(len(ideal_cut)), key=lambda index: abs(ideal_cut[index]))
            shifted_peak = max(range(len(shifted_cut)), key=lambda index: abs(shifted_cut[index]))
            displacement = (
                BASE_CONTROLS["image_x_m"][shifted_peak]
                - BASE_CONTROLS["image_x_m"][ideal_peak]
            )
            self.assertAlmostEqual(displacement, 0.50, places=2)
            self.assertGreater(abs(shifted_cut[shifted_peak]), 0.99 * abs(ideal_cut[ideal_peak]))

            ideal_intensity = [abs(value) ** 2 for value in ideal_cut]
            shifted_intensity = [abs(value) ** 2 for value in shifted_cut]
            ideal_total = sum(ideal_intensity)
            shifted_total = sum(shifted_intensity)
            ideal_entropy = -sum(
                value / ideal_total * math.log(max(value / ideal_total, float.fromhex("0x1.0p-1022")))
                for value in ideal_intensity
            )
            shifted_entropy = -sum(
                value / shifted_total * math.log(max(value / shifted_total, float.fromhex("0x1.0p-1022")))
                for value in shifted_intensity
            )
            self.assertLess(abs(shifted_entropy - ideal_entropy), 0.02)

    def test_error_magnitude_sweep_and_phase_gradient_sampling(self) -> None:
        model = build_model()
        ideal_history, _ = errored_history(model, 0.0)
        ideal = focus(model, ideal_history)
        before: list[float] = []
        after: list[float] = []
        for fraction in BASE_CONTROLS["error_fraction_sweep"]:
            history, phase = errored_history(model, fraction)
            estimate = phase_estimate(model, history)
            before.append(metrics(focus(model, history), ideal)[0])
            after.append(metrics(focus(model, correct(history, estimate)), ideal)[0])
            self.assertLess(max(abs(right - left) for left, right in zip(phase, phase[1:])), BASE_CONTROLS["max_phase_increment_rad"])
        self.assertTrue(all(right < left for left, right in zip(before, before[1:])))
        self.assertLess(before[-1], 0.40)
        self.assertTrue(all(value > 0.95 for value in after))

    def test_composition_sweep_broken_case_and_exact_recovery(self) -> None:
        model = build_model()
        ideal_history, _ = errored_history(model, 0.0)
        ideal = focus(model, ideal_history)
        recovered_peaks: list[float] = []
        for alpha in BASE_CONTROLS["random_fraction_sweep"]:
            history, phase = errored_history(model, 1 / 8, alpha)
            estimate = phase_estimate(model, history)
            recovered_peaks.append(metrics(focus(model, correct(history, estimate)), ideal)[0])
            self.assertLess(max(abs(right - left) for left, right in zip(phase, phase[1:])), BASE_CONTROLS["max_phase_increment_rad"])
        self.assertTrue(all(value > 0.95 for value in recovered_peaks))

        history, _ = errored_history(model, 1 / 8)
        retained = copy.deepcopy(history)
        valid_estimate = phase_estimate(model, history)
        broken_estimate = phase_estimate(model, history, contaminated=True)
        valid_focus = focus(model, correct(history, valid_estimate))
        broken_focus = focus(model, correct(history, broken_estimate))
        self.assertEqual(history, retained)
        self.assertGreater(metrics(valid_focus, ideal)[0], metrics(broken_focus, ideal)[0] + 0.08)
        self.assertEqual(valid_estimate, phase_estimate(model, retained))
        self.assertEqual(valid_focus, focus(model, correct(retained, phase_estimate(model, retained))))

    def test_composite_images_expose_blur_broken_focus_and_fresh_recovery(self) -> None:
        model = build_model()
        ideal_history, _ = errored_history(model, 0.0)
        errored, _ = errored_history(model, 1 / 8)
        valid_estimate = phase_estimate(model, errored)
        broken_estimate = phase_estimate(model, errored, contaminated=True)

        ideal = compose_image(focus(model, ideal_history))
        blurred = compose_image(focus(model, errored))
        corrected = compose_image(focus(model, correct(errored, valid_estimate)))
        broken = compose_image(focus(model, correct(errored, broken_estimate)))
        recovered = compose_image(
            focus(model, correct(copy.deepcopy(errored), phase_estimate(model, errored)))
        )

        self.assertEqual(corrected, recovered)
        self.assertEqual(len(ideal), len(BASE_CONTROLS["image_range_offset_m"]))
        self.assertTrue(all(len(row) == len(BASE_CONTROLS["image_x_m"]) for row in ideal))

        peaks = {
            name: max(abs(value) for row in image for value in row)
            for name, image in (
                ("ideal", ideal), ("blurred", blurred), ("corrected", corrected),
                ("broken", broken), ("recovered", recovered),
            )
        }
        entropies = {
            name: image_entropy(image)
            for name, image in (
                ("ideal", ideal), ("blurred", blurred), ("corrected", corrected),
                ("broken", broken), ("recovered", recovered),
            )
        }
        self.assertLess(peaks["blurred"], 0.55 * peaks["ideal"])
        self.assertGreater(peaks["corrected"], 0.99 * peaks["ideal"])
        self.assertLess(peaks["broken"], 0.90 * peaks["recovered"])
        self.assertGreater(entropies["blurred"], entropies["ideal"] + 1.0)
        self.assertLess(entropies["corrected"], entropies["blurred"] - 1.0)
        self.assertGreater(entropies["broken"], entropies["recovered"] + 0.5)
        self.assertAlmostEqual(peaks["ideal"], 0.9551077165762231, places=12)
        self.assertAlmostEqual(peaks["blurred"], 0.5128258880549649, places=12)
        self.assertAlmostEqual(peaks["corrected"], 0.9553949790190807, places=12)
        self.assertAlmostEqual(peaks["broken"], 0.8514415369734442, places=12)

        for target_x, target_range in zip(
            BASE_CONTROLS["target_x_m"], BASE_CONTROLS["target_range_offset_m"]
        ):
            cross_index = min(
                range(len(BASE_CONTROLS["image_x_m"])),
                key=lambda index: abs(BASE_CONTROLS["image_x_m"][index] - target_x),
            )
            range_index = min(
                range(len(BASE_CONTROLS["image_range_offset_m"])),
                key=lambda index: abs(
                    BASE_CONTROLS["image_range_offset_m"][index] - target_range
                ),
            )
            self.assertGreater(
                abs(corrected[range_index][cross_index]),
                5.0 * abs(blurred[range_index][cross_index]),
            )

    def test_documents_are_concept_first_and_cover_limits(self) -> None:
        combined = " ".join("\n".join(self.documents.values()).lower().split())
        for marker in (
            "4 pi", "lambda/32", "lambda/16", "lambda/8", "lambda/4",
            "3.75 mm", "pi/2", "constant", "linear", "shift", "defocus",
            "peak retention", "entropy", "phase-gradient", "adjacent",
            "isolated range gate", "0.95", "contaminated", "unchanged",
            "ctrl+c", "no toolbox", "base matlab r2016b or newer",
            "4,283,025", "4,500,000", "rollback", "teach-back",
            "p75", "p76", "p77", "p78", "p79", "p81", "static",
            "matlab runtime", "hardware/hil", "field", "deployment",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(self.documents["checks.md"].count("**Answer:**"), 40)
        placeholder = re.compile(r"\b(lorem ipsum|coming soon|placeholder lesson|fill this in)\b", re.I)
        self.assertIsNone(placeholder.search(combined))

    def test_cli_timeout_rollback_recovery_isolation_and_future_compatibility(self) -> None:
        compatible = copy.deepcopy(self.data)
        module_entry(compatible, "P81")["status"] = "implemented"
        module_entry(compatible, "P81")["future_metadata"] = {"allowed": True}
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            self.make_cli_fixture(fixture, compatible)
            started = self.run_cli(fixture, "start", "80")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P80 — Inject SAR Motion Error and Apply Autofocus", started.stdout)
            rolled_back = copy.deepcopy(compatible)
            module_entry(rolled_back, "P80")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8")
            refused = self.run_cli(fixture, "start", "80")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P80", refused.stdout)
            progress = fixture / ".learning/progress.json"
            completed_before = [entry["id"] for entry in compatible["modules"] if entry["number"] < 80]
            progress.write_text(json.dumps({"schema_version": 1, "current": "P79", "completed": completed_before, "notes": {}}, indent=2) + "\n", encoding="utf-8")
            fallback = self.run_cli(fixture, "start")
            self.assertEqual(fallback.returncode, 0, fallback.stderr)
            self.assertIn("P79 — Compare SAR Resolution, Aperture Length, and Windowing", fallback.stdout)
            (fixture / "curriculum/modules.json").write_text(json.dumps(compatible, indent=2) + "\n", encoding="utf-8")
            selected = self.run_cli(fixture, "start")
            self.assertEqual(selected.returncode, 0, selected.stderr)
            self.assertIn("P80 — Inject SAR Motion Error and Apply Autofocus", selected.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_actual_matlab_script_is_repeatable_and_bounded_when_available(self) -> None:
        matlab = shutil.which("matlab")
        if matlab is None:
            self.skipTest("MATLAB executable is unavailable; no runtime evidence claimed")
        module_path = str(MODULE).replace("'", "''")
        commands = (
            "set(0,'DefaultFigureVisible','off'); rng(8001,'twister'); rng_before=rng; "
            f"cd('{module_path}'); run('experiment.m'); first_results=p80_results; "
            "rng_after_first=rng; assert(first_results.recovery_exact_match); "
            "assert(first_results.blurred_metrics.mean_peak_retention<0.65); "
            "assert(first_results.corrected_metrics.mean_peak_retention>0.95); "
            "assert(first_results.executed_focus_operations==4283025); "
            "assert(isequaln(rng_before,rng_after_first)); run('experiment.m'); "
            "assert(isequaln(first_results,p80_results)); assert(isequaln(rng_before,rng)); "
            "assert(numel(findall(0,'Type','figure','Tag','P80'))==5); "
            "close(findall(0,'Type','figure','Tag','P80'));"
        )
        guarded = f"try; {commands} exit(0); catch p80_exception; disp(getReport(p80_exception,'extended')); exit(1); end"
        completed = subprocess.run(
            [matlab, "-nosplash", "-nodesktop", "-nodisplay", "-r", guarded],
            cwd=MODULE, text=True, capture_output=True, timeout=300,
        )
        self.assertEqual(completed.returncode, 0, f"MATLAB stdout:\n{completed.stdout}\nMATLAB stderr:\n{completed.stderr}")

    def test_catalogs_evidence_and_exact_eof_policy(self) -> None:
        self.assertIn("Project 80 converts millimetre-scale", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn("Project 80 follows P79", (ROOT / "START_HERE.md").read_text(encoding="utf-8"))
        self.assertRegex((ROOT / "modules/README.md").read_text(encoding="utf-8"), r"\| \[P80\].*\| implemented \|")
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
            ROOT / "tests/test_p80_module.py", EVIDENCE,
        ]
        for path in changed_text_paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
