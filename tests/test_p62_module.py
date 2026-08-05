from __future__ import annotations

import cmath
import copy
import json
import math
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/62-plot-array-factor-beamwidth-and-grating-lobes"
QUESTION = "How do aperture size and element spacing shape a beam pattern?"
EXPECTED_IDENTITY = {
    "number": 62,
    "id": "P62",
    "title": "Plot Array Factor, Beamwidth, and Grating Lobes",
    "guiding_question": QUESTION,
    "phase": 7,
    "phase_title": "Arrays, Beamforming, DOA, and STAP",
    "slug": "plot-array-factor-beamwidth-and-grating-lobes",
    "folder": "modules/62-plot-array-factor-beamwidth-and-grating-lobes",
    "status": "implemented",
    "implementation_batch": "P62",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
SOURCE_MARKERS = (
    "baseline_seed = 6201;",
    "number_elements = 8;",
    "element_spacing_wavelengths = 0.5;",
    "steering_angle_deg = 0.0;",
    "angle_grid_deg = -90:0.025:90;",
    "element_count_sweep = [4 8 16];",
    "spacing_sweep_wavelengths = [0.5 0.75 1.0];",
    "taper_weights = 0.54 - 0.46*cos(2*pi*element_index/(number_elements-1));",
    "broken_steering_angle_deg = 30.0;",
    "broken_spacing_wavelengths = 1.0;",
    "broken_grating_angle_deg = -30.0;",
    "recovered_spacing_wavelengths = 0.5;",
    "baseline_phase_rad = 2*pi*element_spacing_wavelengths* ...",
    "baseline_element_contributions = uniform_weights.*exp(1j*baseline_phase_rad);",
    "abs(sum(baseline_element_contributions, 1))/sum(abs(uniform_weights));",
    "half_power = 1/sqrt(2);",
    "left_half_power_deg = interpolate_crossing(",
    "local_minimum(2:end-1) = normalized(2:end-1) <= normalized(1:end-2)",
    "peak_sidelobe_level_db = 20*log10(max(sidelobe_samples));",
    "candidate_direction = direction_steer+order/spacing_wavelengths;",
    "broken_visible_grating_angles_deg = visible_grating_angles(",
    "abs(broken_true_peak-broken_alias_peak) < comparison_tolerance",
    "recovered_false_direction_level < comparison_tolerance",
    "private_uniform(baseline_seed, probe_count,",
    "maximum_elements = 32;",
    "maximum_angle_samples = 10001;",
    "maximum_sweep_cases = 5;",
    "maximum_stored_numeric_values = 250000;",
    "maximum_figures = 5;",
    "validate_controls(controls);",
    "p62_results = struct(",
    "close(findall(0, 'Type', 'figure', 'Tag', 'P62'));",
)
FORBIDDEN_SOURCE_TOKENS = (
    "phased.ULA",
    "phased.ArrayResponse",
    "phased.SteeringVector",
    "arrayfactor(",
    "beamwidth(",
    "findpeaks(",
    "hamming(",
    "hann(",
    "taylorwin(",
    "rng(",
    "rand(",
    "randn(",
    "parfor",
    "timer(",
    "webread",
    "urlread",
    "system(",
    "fopen(",
    "save(",
    "close all",
)
MODULUS = 2_147_483_647
MULTIPLIER = 16_807


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def p62_source_contract_errors(source: object) -> list[str]:
    if not isinstance(source, str) or not source:
        return ["P62 source must be nonempty text"]
    errors = [
        f"missing source marker: {marker}" for marker in SOURCE_MARKERS if marker not in source
    ]
    if source.count("figure('Name', 'P62") != 5:
        errors.append("P62 must create exactly five named figures")
    if source.count("'Tag', 'P62'") != 6:
        errors.append("P62 must tag five figures and one scoped cleanup")
    errors.extend(
        f"forbidden source token: {token}"
        for token in FORBIDDEN_SOURCE_TOKENS
        if token in source
    )
    return errors


def validate_p62_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P62 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [
        entry
        for entry in manifest["modules"]
        if isinstance(entry, dict) and entry.get("id") == "P62"
    ]
    if len(matches) != 1:
        errors.append("P62 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P62 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P62 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P62 empty {artifact}")
    return errors


def reviewed_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "seed": 6201,
        "elements": 8,
        "spacing": 0.5,
        "steering": 0.0,
        "angles": tuple(-90.0 + 0.025 * index for index in range(7201)),
        "floor_db": -60.0,
        "element_sweep": (4, 8, 16),
        "spacing_sweep": (0.5, 0.75, 1.0),
        "broken_steering": 30.0,
        "broken_spacing": 1.0,
        "broken_grating": -30.0,
        "recovered_spacing": 0.5,
        "max_elements": 32,
        "max_angles": 10001,
        "max_cases": 5,
        "max_probes": 8,
        "max_values": 250000,
        "max_figures": 5,
        "tolerance": 1e-10,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    for name in (
        "seed",
        "elements",
        "max_elements",
        "max_angles",
        "max_cases",
        "max_probes",
        "max_values",
        "max_figures",
    ):
        if not integer(controls[name]):
            raise ValueError(f"{name} integer")
    for name in ("spacing", "steering", "floor_db", "broken_steering", "broken_spacing", "broken_grating", "recovered_spacing", "tolerance"):
        if not finite_real(controls[name]):
            raise ValueError(f"{name} finite")
    if controls["seed"] != 6201 or not 1 <= controls["seed"] < MODULUS:
        raise ValueError("seed")
    if controls["elements"] != 8 or not 2 <= controls["elements"] <= controls["max_elements"] == 32:
        raise ValueError("elements")
    if controls["spacing"] != 0.5 or controls["steering"] != 0.0:
        raise ValueError("baseline geometry")
    angles = controls["angles"]
    if (
        not isinstance(angles, (tuple, list))
        or not angles
        or len(angles) > controls["max_angles"] == 10001
        or not all(finite_real(value) for value in angles)
        or angles[0] != -90.0
        or abs(angles[-1] - 90.0) > 1e-10
        or any(right <= left for left, right in zip(angles, angles[1:]))
        or any(abs((right - left) - 0.025) > 1e-10 for left, right in zip(angles, angles[1:]))
    ):
        raise ValueError("angle grid")
    for name, expected in (
        ("element_sweep", (4, 8, 16)),
        ("spacing_sweep", (0.5, 0.75, 1.0)),
    ):
        values = controls[name]
        if (
            not isinstance(values, (tuple, list))
            or tuple(values) != expected
            or len(values) > controls["max_cases"] == 5
            or not all(finite_real(value) and value > 0 for value in values)
            or any(right <= left for left, right in zip(values, values[1:]))
        ):
            raise ValueError(name)
    if (
        controls["broken_steering"] != 30.0
        or controls["broken_spacing"] != 1.0
        or controls["broken_grating"] != -30.0
        or controls["recovered_spacing"] != 0.5
    ):
        raise ValueError("broken fixture")
    if (
        controls["floor_db"] != -60.0
        or controls["tolerance"] != 1e-10
        or controls["max_probes"] != 8
        or controls["max_values"] != 250000
        or controls["max_figures"] != 5
    ):
        raise ValueError("immutable ceiling")
    estimated_values = len(angles) * (
        4 + len(controls["element_sweep"]) + len(controls["spacing_sweep"]) + controls["elements"]
    ) + 100 * controls["max_elements"]
    if estimated_values > controls["max_values"]:
        raise ValueError("resource ceiling")
    return controls


def private_uniform(seed: object, count: object, maximum: int = 8) -> tuple[float, ...]:
    if not integer(seed) or not 1 <= seed < MODULUS:
        raise ValueError("seed")
    if not integer(count) or not 1 <= count <= maximum:
        raise ValueError("count")
    state = int(seed)
    values = []
    for _ in range(int(count)):
        state = (MULTIPLIER * state) % MODULUS
        values.append((state + 0.5) / MODULUS)
    return tuple(values)


def array_factor(
    elements: object,
    spacing_wavelengths: object,
    steering_angle_deg: object,
    observation_angles_deg: object,
    weights: object | None = None,
) -> tuple[float, ...]:
    if not integer(elements) or not 2 <= elements <= 32:
        raise ValueError("elements")
    if not finite_real(spacing_wavelengths) or spacing_wavelengths <= 0:
        raise ValueError("spacing")
    if not finite_real(steering_angle_deg) or not -90 < steering_angle_deg < 90:
        raise ValueError("steering")
    if not isinstance(observation_angles_deg, (tuple, list)) or not observation_angles_deg:
        raise ValueError("observation angles")
    if not all(finite_real(angle) and -90 <= angle <= 90 for angle in observation_angles_deg):
        raise ValueError("observation angles")
    if weights is None:
        weights = tuple(1.0 for _ in range(int(elements)))
    if (
        not isinstance(weights, (tuple, list))
        or len(weights) != elements
        or not all(finite_real(weight) and weight >= 0 for weight in weights)
        or sum(weights) <= 0
    ):
        raise ValueError("weights")
    steering_direction = math.sin(math.radians(steering_angle_deg))
    response = []
    for angle in observation_angles_deg:
        direction_offset = math.sin(math.radians(angle)) - steering_direction
        total = sum(
            weight
            * cmath.exp(1j * 2 * math.pi * spacing_wavelengths * index * direction_offset)
            for index, weight in enumerate(weights)
        )
        response.append(abs(total) / sum(weights))
    return tuple(response)


def crossing(x1: float, y1: float, x2: float, y2: float, target: float) -> float:
    if not all(finite_real(value) for value in (x1, y1, x2, y2, target)):
        raise ValueError("finite crossing")
    if x2 <= x1 or y2 == y1 or not min(y1, y2) <= target <= max(y1, y2):
        raise ValueError("crossing bracket")
    return x1 + (target - y1) * (x2 - x1) / (y2 - y1)


def pattern_metrics(angles: object, response: object, expected_peak: object) -> dict[str, float]:
    if (
        not isinstance(angles, (tuple, list))
        or not isinstance(response, (tuple, list))
        or len(angles) != len(response)
        or len(angles) < 5
        or not all(finite_real(value) for value in angles)
        or not all(finite_real(value) and value >= 0 for value in response)
        or any(right <= left for left, right in zip(angles, angles[1:]))
        or not finite_real(expected_peak)
    ):
        raise ValueError("metric record")
    expected_index = min(range(len(angles)), key=lambda index: abs(angles[index] - expected_peak))
    step = sorted(right - left for left, right in zip(angles, angles[1:]))[len(angles) // 2]
    half_window = max(1, round(5 / step))
    first = max(0, expected_index - half_window)
    last = min(len(response), expected_index + half_window + 1)
    peak_index = max(range(first, last), key=lambda index: response[index])
    peak = response[peak_index]
    if peak <= 0:
        raise ValueError("zero peak")
    normalized = [value / peak for value in response]
    level = 1 / math.sqrt(2)
    left_candidates = [index for index in range(peak_index + 1) if normalized[index] <= level]
    right_candidates = [index for index in range(peak_index, len(normalized)) if normalized[index] <= level]
    if not left_candidates or not right_candidates:
        raise ValueError("missing half-power crossing")
    left_index = left_candidates[-1]
    right_index = right_candidates[0]
    if left_index >= peak_index or right_index <= peak_index:
        raise ValueError("bad half-power crossing")
    left_crossing = crossing(
        angles[left_index], normalized[left_index], angles[left_index + 1], normalized[left_index + 1], level
    )
    right_crossing = crossing(
        angles[right_index - 1], normalized[right_index - 1], angles[right_index], normalized[right_index], level
    )
    minima = [
        index
        for index in range(1, len(normalized) - 1)
        if normalized[index] <= normalized[index - 1] and normalized[index] < normalized[index + 1]
    ]
    left_minima = [index for index in minima if index < peak_index]
    right_minima = [index for index in minima if index > peak_index]
    if not left_minima or not right_minima:
        raise ValueError("missing first null")
    left_null = left_minima[-1]
    right_null = right_minima[0]
    sidelobes = normalized[: left_null + 1] + normalized[right_null:]
    return {
        "peak_angle": angles[peak_index],
        "peak_value": peak,
        "left_half_power": left_crossing,
        "right_half_power": right_crossing,
        "hpbw": right_crossing - left_crossing,
        "left_null": angles[left_null],
        "right_null": angles[right_null],
        "fnbw": angles[right_null] - angles[left_null],
        "psl_db": 20 * math.log10(max(sidelobes)),
    }


def visible_grating_angles(spacing: object, steering: object) -> tuple[float, ...]:
    if not finite_real(spacing) or spacing <= 0:
        raise ValueError("spacing")
    if not finite_real(steering) or not -90 < steering < 90:
        raise ValueError("steering")
    steering_direction = math.sin(math.radians(steering))
    extent = math.ceil(2 * spacing)
    directions = []
    for order in range(-extent, extent + 1):
        if order == 0:
            continue
        candidate = steering_direction + order / spacing
        if abs(candidate) <= 1:
            directions.append(math.degrees(math.asin(candidate)))
    return tuple(sorted(directions))


class P62ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.angles = tuple(-90.0 + 0.025 * index for index in range(7201))

    def run_fixture_cli(self, fixture_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(fixture_root.parent)
        return subprocess.run(
            [str(fixture_root / "bin/learn"), *args],
            cwd=fixture_root,
            env=env,
            text=True,
            capture_output=True,
            timeout=10,
        )

    def make_cli_fixture(self, base: Path, manifest: dict) -> Path:
        fixture = base / "repo"
        (fixture / "bin").mkdir(parents=True)
        (fixture / "curriculum").mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
        (fixture / "curriculum/modules.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        for module in manifest["modules"]:
            readme = fixture / module["folder"] / "README.md"
            readme.parent.mkdir(parents=True, exist_ok=True)
            readme.write_text(f"# {module['id']}\n", encoding="utf-8")
        return fixture

    def test_artifacts_and_manifest_identity_are_complete(self):
        self.assertEqual(validate_p62_contract(ROOT, self.manifest), [])
        p61 = next(module for module in self.manifest["modules"] if module["id"] == "P61")
        self.assertEqual(p61["status"], "implemented")

    def test_contract_rejects_malformed_duplicate_drift_missing_and_empty(self):
        self.assertTrue(validate_p62_contract(ROOT, None))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append(None)
        self.assertIn("every manifest module must be an object", validate_p62_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("P62 must have exactly one manifest entry", validate_p62_contract(ROOT, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(module for module in drifted["modules"] if module["id"] == "P62")["guiding_question"] = "changed"
        self.assertIn("P62 manifest identity drift", validate_p62_contract(ROOT, drifted))
        with tempfile.TemporaryDirectory() as temp:
            fixture_root = Path(temp)
            fixture_module = fixture_root / EXPECTED_IDENTITY["folder"]
            fixture_module.parent.mkdir(parents=True)
            shutil.copytree(MODULE, fixture_module)
            (fixture_module / "lesson.md").unlink()
            self.assertIn("P62 missing lesson.md", validate_p62_contract(fixture_root, self.manifest))
            (fixture_module / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P62 empty lesson.md", validate_p62_contract(fixture_root, self.manifest))

    def test_source_exposes_model_sweeps_failure_recovery_and_bounds(self):
        self.assertEqual(p62_source_contract_errors(self.source), [])

    def test_source_contract_rejects_black_boxes_and_representative_mutants(self):
        for marker in (
            "validate_controls(controls);",
            "baseline_element_contributions = uniform_weights.*exp(1j*baseline_phase_rad);",
            "abs(sum(baseline_element_contributions, 1))/sum(abs(uniform_weights));",
            "half_power = 1/sqrt(2);",
            "peak_sidelobe_level_db = 20*log10(max(sidelobe_samples));",
            "candidate_direction = direction_steer+order/spacing_wavelengths;",
            "abs(broken_true_peak-broken_alias_peak) < comparison_tolerance",
            "recovered_false_direction_level < comparison_tolerance",
            "maximum_stored_numeric_values = 250000;",
        ):
            with self.subTest(marker=marker):
                self.assertTrue(p62_source_contract_errors(self.source.replace(marker, "removed", 1)))
        self.assertTrue(p62_source_contract_errors(self.source + "\nphased.ULA(8)"))

    def test_controls_accept_reviewed_values_and_reject_malformed_inputs(self):
        controls = reviewed_controls()
        self.assertEqual(controls["elements"], 8)
        cases = (
            {"seed": 0},
            {"elements": True},
            {"elements": 1},
            {"elements": 8.5},
            {"elements": 33},
            {"spacing": 0.0},
            {"spacing": float("nan")},
            {"steering": 90.0},
            {"angles": ()},
            {"angles": (-90.0, 0.0, -1.0, 90.0)},
            {"angles": tuple(float(index) for index in range(10002))},
            {"element_sweep": (4, 16, 8)},
            {"spacing_sweep": (0.5, 0.5, 1.0)},
            {"broken_spacing": 0.75},
            {"broken_grating": -20.0},
            {"max_values": 249999},
            {"max_figures": 6},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    reviewed_controls(**changes)
        with self.assertRaises(ValueError):
            reviewed_controls(unknown=1)

    def test_private_seed_is_exact_repeatable_isolated_and_bounded(self):
        expected = (
            0.048531316010528854,
            0.6658242760066987,
            0.5086029316338724,
            0.0894680575418603,
        )
        first = private_uniform(6201, 4)
        second = private_uniform(6201, 4)
        for actual, wanted in zip(first, expected):
            self.assertAlmostEqual(actual, wanted, places=14)
        self.assertEqual(first, second)
        for seed, count in ((0, 4), (MODULUS, 4), (6201.5, 4), (6201, 0), (6201, 9)):
            with self.subTest(seed=seed, count=count):
                with self.assertRaises(ValueError):
                    private_uniform(seed, count)

    def test_independent_baseline_oracle_measures_beamwidth_nulls_and_sidelobes(self):
        response = array_factor(8, 0.5, 0.0, self.angles)
        metrics = pattern_metrics(self.angles, response, 0.0)
        self.assertAlmostEqual(max(response), 1.0, places=14)
        self.assertAlmostEqual(metrics["peak_angle"], 0.0, places=12)
        self.assertAlmostEqual(metrics["hpbw"], 12.802523075064096, places=9)
        self.assertAlmostEqual(metrics["fnbw"], 28.95, places=9)
        self.assertAlmostEqual(metrics["psl_db"], -12.79735355607447, places=9)
        for left, right in zip(response, reversed(response)):
            self.assertAlmostEqual(left, right, places=12)

    def test_element_count_sweep_links_aperture_to_narrower_beam(self):
        widths = []
        apertures = []
        for elements in (4, 8, 16):
            metrics = pattern_metrics(
                self.angles, array_factor(elements, 0.5, 0.0, self.angles), 0.0
            )
            widths.append(metrics["hpbw"])
            apertures.append((elements - 1) * 0.5)
        self.assertEqual(apertures, [1.5, 3.5, 7.5])
        self.assertTrue(all(right < left for left, right in zip(widths, widths[1:])))
        for actual, expected in zip(widths, (26.3229454, 12.8025231, 6.3587092)):
            self.assertAlmostEqual(actual, expected, places=5)

    def test_spacing_sweep_predicts_only_actual_visible_grating_lobes(self):
        widths = []
        predicted = []
        for spacing in (0.5, 0.75, 1.0):
            metrics = pattern_metrics(
                self.angles, array_factor(8, spacing, 0.0, self.angles), 0.0
            )
            widths.append(metrics["hpbw"])
            predicted.append(visible_grating_angles(spacing, 0.0))
        self.assertTrue(all(right < left for left, right in zip(widths, widths[1:])))
        self.assertEqual(predicted[0], ())
        self.assertEqual(predicted[1], ())
        self.assertEqual(predicted[2], (-90.0, 90.0))

    def test_explicit_hamming_taper_lowers_sidelobes_and_widens_beam(self):
        uniform = pattern_metrics(self.angles, array_factor(8, 0.5, 0.0, self.angles), 0.0)
        weights = tuple(0.54 - 0.46 * math.cos(2 * math.pi * index / 7) for index in range(8))
        tapered = pattern_metrics(
            self.angles, array_factor(8, 0.5, 0.0, self.angles, weights), 0.0
        )
        self.assertGreater(tapered["hpbw"], uniform["hpbw"] + 5)
        self.assertLess(tapered["psl_db"], uniform["psl_db"] - 15)
        self.assertAlmostEqual(tapered["hpbw"], 20.40733114095132, places=8)
        self.assertAlmostEqual(tapered["psl_db"], -33.621195652975786, places=8)

    def test_hamming_taper_cannot_repair_exact_grating_alias(self):
        weights = tuple(0.54 - 0.46 * math.cos(2 * math.pi * index / 7) for index in range(8))
        tapered_broken = array_factor(8, 1.0, 30.0, (30.0, -30.0), weights)
        self.assertAlmostEqual(tapered_broken[0], 1.0, places=14)
        self.assertAlmostEqual(tapered_broken[1], 1.0, places=14)
        self.assertAlmostEqual(tapered_broken[0], tapered_broken[1], places=14)

    def test_broken_grating_lobe_is_exact_and_safe_spacing_recovers(self):
        self.assertEqual(visible_grating_angles(1.0, 30.0), (-30.000000000000004,))
        broken = array_factor(8, 1.0, 30.0, (30.0, -30.0))
        recovered = array_factor(8, 0.5, 30.0, (30.0, -30.0))
        self.assertAlmostEqual(broken[0], 1.0, places=14)
        self.assertAlmostEqual(broken[1], 1.0, places=14)
        self.assertEqual(visible_grating_angles(0.5, 30.0), ())
        self.assertAlmostEqual(recovered[0], 1.0, places=14)
        self.assertLess(recovered[1], 1e-12)

    def test_oracles_reject_nonfinite_nonphysical_and_malformed_records(self):
        array_cases = (
            (1, 0.5, 0.0, (0.0,), None),
            (8, 0.0, 0.0, (0.0,), None),
            (8, 0.5, 90.0, (0.0,), None),
            (8, 0.5, 0.0, (), None),
            (8, 0.5, 0.0, (float("nan"),), None),
            (8, 0.5, 0.0, (0.0,), (1.0,) * 7),
            (8, 0.5, 0.0, (0.0,), (0.0,) * 8),
            (8, 0.5, 0.0, (0.0,), (1.0,) * 7 + (-1.0,)),
        )
        for args in array_cases:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    array_factor(*args)
        metric_cases = (
            (None, None, 0.0),
            ((-1.0, 0.0, 1.0), (0.0, 1.0), 0.0),
            ((-1.0, 0.0, 1.0), (1.0, float("nan"), 1.0), 0.0),
            ((-2.0, -1.0, 0.0, 1.0, 2.0), (1.0, 1.0, 1.0, 1.0, 1.0), 0.0),
        )
        for args in metric_cases:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    pattern_metrics(*args)
        for args in ((0.0, 0.0), (float("inf"), 0.0), (0.5, 90.0)):
            with self.assertRaises(ValueError):
                visible_grating_angles(*args)

    def test_documents_are_concept_first_and_cover_limits_and_dependencies(self):
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        for document in (readme, lesson, walkthrough, checks):
            self.assertIn(QUESTION, document)
            self.assertNotIn("TODO", document)
        for marker in (
            "AF(theta) = |sum_m c_m(theta)| / sum_m |w_m|",
            "sin(theta_g) = sin(theta_0) + k/q",
            "Half-power beamwidth",
            "Peak sidelobe level",
            "far-field",
            "narrowband",
            "P61",
            "P67",
        ):
            self.assertIn(marker, lesson)
        for marker in ("Sweep 1", "Sweep 2", "Broken case", "Recovery", "Ctrl+C"):
            self.assertIn(marker, walkthrough)
        self.assertIn("Short teach-back rubric", checks)
        self.assertGreaterEqual(checks.count("**Correct:**"), 27)

    def test_cli_timeout_isolation_rollback_recovery_and_future_compatibility(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        compatible = copy.deepcopy(self.manifest)
        p63 = next(module for module in compatible["modules"] if module["id"] == "P63")
        p63["future_extension"] = {"accepted": True}
        original_p61 = copy.deepcopy(next(module for module in compatible["modules"] if module["id"] == "P61"))
        original_p63 = copy.deepcopy(p63)
        with tempfile.TemporaryDirectory() as temp:
            fixture = self.make_cli_fixture(Path(temp), compatible)
            started = self.run_fixture_cli(fixture, "start", "62")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P62", started.stdout)
            self.assertIn("status: implemented", started.stdout)
            state_path = fixture / ".learning/progress.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P61",
                        "completed": [f"P{number:02d}" for number in range(1, 62)],
                        "notes": {"P61": "prerequisite complete"},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            advanced = self.run_fixture_cli(fixture, "start")
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertIn("P62 — Plot Array Factor, Beamwidth, and Grating Lobes", advanced.stdout)
            rolled_back = copy.deepcopy(compatible)
            next(module for module in rolled_back["modules"] if module["id"] == "P62")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(
                json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8"
            )
            refused = self.run_fixture_cli(fixture, "start", "62")
            self.assertEqual(refused.returncode, 3, refused.stderr)
            self.assertIn("awaits Portfolio batch P62", refused.stdout)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P61"), original_p61)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P63"), original_p63)
            (fixture / "curriculum/modules.json").write_text(
                json.dumps(compatible, indent=2) + "\n", encoding="utf-8"
            )
            recovered = self.run_fixture_cli(fixture, "start", "62")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_cancellation_cleanup_has_no_external_or_persistent_side_effects(self):
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P62'));", self.source)
        self.assertNotIn("close all", self.source)
        for token in ("timer(", "parfor", "webread", "urlread", "fopen(", "save(", "system("):
            self.assertNotIn(token, self.source)
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        self.assertIn("Ctrl+C", walkthrough)
        self.assertIn("no background task, checkpoint, or partial output", walkthrough)

    def test_public_catalogs_describe_permanent_p62_facts(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 62 follows P61", readme)
        self.assertIn("Project 62 follows P61", start_here)
        self.assertIn(
            "| [P62](../modules/62-plot-array-factor-beamwidth-and-grating-lobes/) | implemented | 7 |",
            module_index,
        )

    def test_retained_evidence_has_claim_boundary_commands_and_lifecycle_coverage(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P62-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        for marker in (
            "# P62 Retained Evidence",
            "## Acceptance map",
            "84 modules, 62 implemented",
            "## Deterministic simulated-oracle results",
            "## Figure and metric inventory",
            "## Exact commands and results",
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
            "command -v matlab",
            "No MATLAB runtime evidence was produced",
            "## Focused positive and negative coverage",
            "Timeout guard",
            "Cancellation",
            "Rollback and recovery",
            "Isolation",
            "Compatibility",
            "Resource bounds",
            "## Changed and preserved invariants",
            "## Residual risks and known content gaps",
            "## Rollback",
            "## Unperformed validation",
            "Hardware/HIL",
            "RT1/RT2",
            "Unreal",
            "signing",
            "deployment",
            "production",
            "operator-provided `contracts/active-batch.yaml`",
            "operator-provided `contracts/repo-profile.yaml`",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, evidence)
        self.assertTrue(evidence.endswith("\n"))
        self.assertFalse(evidence.endswith("\n\n"))

    def test_changed_text_files_have_exactly_one_terminal_newline(self):
        paths = [MODULE / artifact for artifact in ARTIFACTS] + [
            ROOT / "README.md",
            ROOT / "START_HERE.md",
            ROOT / "modules/README.md",
            ROOT / "curriculum/modules.json",
            ROOT / "tests/test_p62_module.py",
            ROOT / "docs/evidence/P62-2026-08-05.md",
        ]
        for path in paths:
            with self.subTest(path=path):
                data = path.read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
