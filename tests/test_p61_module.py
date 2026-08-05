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
MODULE = ROOT / "modules/61-see-phase-steering-in-a-uniform-linear-array"
QUESTION = "How does a direction of arrival become a phase slope across sensors?"
EXPECTED_IDENTITY = {
    "number": 61,
    "id": "P61",
    "title": "See Phase Steering in a Uniform Linear Array",
    "guiding_question": QUESTION,
    "phase": 7,
    "phase_title": "Arrays, Beamforming, DOA, and STAP",
    "slug": "see-phase-steering-in-a-uniform-linear-array",
    "folder": "modules/61-see-phase-steering-in-a-uniform-linear-array",
    "status": "implemented",
    "implementation_batch": "P61",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
MODULUS = 2_147_483_647
MULTIPLIER = 16_807
SOURCE_MARKERS = (
    "baseline_seed = 6101;",
    "speed_of_light_mps = 299792458;",
    "carrier_frequency_hz = 3.0e9;",
    "number_elements = 8;",
    "arrival_angle_deg = 30.0;",
    "element_spacing_m = 0.5*wavelength_m;",
    "arrival_angle_sweep_deg = [-60 -30 0 30 60];",
    "spacing_sweep_wavelengths = [0.25 0.375 0.50];",
    "frequency_sweep_hz = [1.5e9 2.25e9 3.0e9];",
    "geometric_delay_s = -element_position_m*sind(arrival_angle_deg)/",
    "ideal_phase_rad = initial_phase_rad - ...",
    "2*pi*carrier_frequency_hz*geometric_delay_s;",
    "2*pi*(element_spacing_m/wavelength_m)*sind(arrival_angle_deg);",
    "conj(received_snapshot(1:end-1)).*received_snapshot(2:end)",
    "estimated_arrival_angle_deg = asind(angle_argument);",
    "broken_spacing_wavelengths = 1.0;",
    "broken_true_angle_deg = asind(0.6);",
    "broken_alias_angle_deg = asind(-0.4);",
    "'broken_alias_angle_deg', broken_alias_angle_deg, ...",
    "broken_snapshot_mismatch = max(abs(",
    "recovered_spacing_wavelengths = 0.5;",
    "private_standard_normal(baseline_seed,",
    "maximum_elements = 32;",
    "maximum_sweep_cases = 7;",
    "maximum_random_values = 64;",
    "maximum_stored_numeric_values = 5000;",
    "maximum_figures = 5;",
    "validate_controls(controls);",
    "ideal_snapshot = exp(1j*ideal_phase_rad);",
    "sum(centered_index.*centered_phase_rad)/sum(centered_index.^2);",
    "assert(abs(angle_error_deg) < 1.0, 'P61:BaselineAngleError');",
    "assert(phase_fit_rmse_rad < 0.08, 'P61:BaselinePhaseFitError');",
    "c.broken_spacing_wavelengths == 1.0",
    "isrow(values)",
    "close(findall(0, 'Type', 'figure', 'Tag', 'P61'));",
)
FORBIDDEN_SOURCE_TOKENS = (
    "phased.ULA",
    "phased.SteeringVector",
    "phased.ArrayResponse",
    "steervec(",
    "collectPlaneWave",
    "awgn(",
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


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def p61_source_contract_errors(source: object) -> list[str]:
    if not isinstance(source, str) or not source:
        return ["P61 source must be nonempty text"]
    errors = [
        f"missing source marker: {marker}"
        for marker in SOURCE_MARKERS
        if marker not in source
    ]
    if source.count("figure('Name', 'P61") != 5:
        errors.append("P61 must create exactly five named figures")
    if source.count("'Tag', 'P61'") != 6:
        errors.append("P61 must tag five figures and one scoped cleanup")
    errors.extend(
        f"forbidden source token: {token}"
        for token in FORBIDDEN_SOURCE_TOKENS
        if token in source
    )
    return errors


def validate_p61_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P61 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [
        entry
        for entry in manifest["modules"]
        if isinstance(entry, dict) and entry.get("id") == "P61"
    ]
    if len(matches) != 1:
        errors.append("P61 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P61 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P61 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P61 empty {artifact}")
    return errors


def validate_controls(**overrides: object) -> dict[str, object]:
    c = 299_792_458.0
    frequency = 3.0e9
    wavelength = c / frequency
    controls: dict[str, object] = {
        "seed": 6101,
        "c": c,
        "frequency": frequency,
        "elements": 8,
        "angle": 30.0,
        "phase": 20.0,
        "snr": 35.0,
        "spacing": 0.5 * wavelength,
        "angle_sweep": (-60.0, -30.0, 0.0, 30.0, 60.0),
        "spacing_sweep": (0.25, 0.375, 0.5),
        "frequency_sweep": (1.5e9, 2.25e9, 3.0e9),
        "broken_spacing": 1.0,
        "broken_true_angle": math.degrees(math.asin(0.6)),
        "broken_alias_angle": math.degrees(math.asin(-0.4)),
        "max_elements": 32,
        "max_cases": 7,
        "max_random": 64,
        "max_values": 5000,
        "max_figures": 5,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    for name in (
        "seed",
        "elements",
        "max_elements",
        "max_cases",
        "max_random",
        "max_values",
        "max_figures",
    ):
        if not integer(controls[name]):
            raise ValueError(f"{name} integer")
    if controls["seed"] != 6101 or not 1 <= controls["seed"] < MODULUS:
        raise ValueError("seed")
    for name in ("c", "frequency", "spacing"):
        if not finite_real(controls[name]) or controls[name] <= 0:
            raise ValueError(f"{name} positive")
    for name in ("angle", "phase", "snr", "broken_spacing", "broken_true_angle", "broken_alias_angle"):
        if not finite_real(controls[name]):
            raise ValueError(f"{name} finite")
    if not -90 < controls["angle"] < 90:
        raise ValueError("angle domain")
    if not 2 <= controls["elements"] <= controls["max_elements"] == 32:
        raise ValueError("element bound")
    if (
        controls["broken_spacing"] != 1.0
        or abs(math.sin(math.radians(controls["broken_true_angle"])) - 0.6) > 1e-12
        or abs(math.sin(math.radians(controls["broken_alias_angle"])) + 0.4) > 1e-12
    ):
        raise ValueError("broken alias fixture")
    if (
        controls["max_cases"] != 7
        or controls["max_random"] != 64
        or controls["max_values"] != 5000
        or controls["max_figures"] != 5
    ):
        raise ValueError("immutable ceiling")
    sweep_contracts = (
        ("angle_sweep", -90.0, 90.0, controls["angle"]),
        ("spacing_sweep", 0.0, 0.5000000001, 0.5),
        ("frequency_sweep", 0.0, controls["frequency"] + 1.0, controls["frequency"]),
    )
    for name, lower, upper, baseline in sweep_contracts:
        values = controls[name]
        if (
            not isinstance(values, (tuple, list))
            or not values
            or len(values) > controls["max_cases"]
            or not all(finite_real(value) for value in values)
            or any(right <= left for left, right in zip(values, values[1:]))
            or any(not lower < value < upper for value in values)
            or list(values).count(baseline) != 1
        ):
            raise ValueError(f"{name} invalid")
    random_values = 2 * controls["elements"]
    stored_values = 20 * controls["elements"] + 12 * sum(
        len(controls[name])
        for name in ("angle_sweep", "spacing_sweep", "frequency_sweep")
    )
    if random_values > controls["max_random"] or stored_values > controls["max_values"]:
        raise ValueError("resource ceiling")
    return controls


def private_standard_normal(seed: object, count: object, maximum: int = 64) -> tuple[float, ...]:
    if not integer(seed) or not 1 <= seed < MODULUS:
        raise ValueError("seed")
    if not integer(count) or not 1 <= count <= maximum:
        raise ValueError("count")
    state = int(seed)
    values: list[float] = []
    for _ in range(math.ceil(int(count) / 2)):
        state = (MULTIPLIER * state) % MODULUS
        uniform_1 = (state + 0.5) / MODULUS
        state = (MULTIPLIER * state) % MODULUS
        uniform_2 = (state + 0.5) / MODULUS
        radius = math.sqrt(-2 * math.log(uniform_1))
        angle = 2 * math.pi * uniform_2
        values.extend((radius * math.cos(angle), radius * math.sin(angle)))
    return tuple(values[: int(count)])


def unwrap(phases: list[float]) -> list[float]:
    if len(phases) < 2 or not all(finite_real(value) for value in phases):
        raise ValueError("phase record")
    result = [phases[0]]
    for phase in phases[1:]:
        while phase - result[-1] > math.pi:
            phase -= 2 * math.pi
        while phase - result[-1] < -math.pi:
            phase += 2 * math.pi
        result.append(phase)
    return result


def slope(values: list[float]) -> float:
    if len(values) < 2 or not all(finite_real(value) for value in values):
        raise ValueError("slope record")
    centre = (len(values) - 1) / 2
    mean_value = sum(values) / len(values)
    numerator = sum((index - centre) * (value - mean_value) for index, value in enumerate(values))
    denominator = sum((index - centre) ** 2 for index in range(len(values)))
    return numerator / denominator


def infer_angle(snapshot: object, spacing_m: object, wavelength_m: object) -> dict[str, float]:
    if (
        not isinstance(snapshot, (tuple, list))
        or len(snapshot) < 2
        or not all(isinstance(value, complex) for value in snapshot)
        or not all(math.isfinite(value.real) and math.isfinite(value.imag) for value in snapshot)
    ):
        raise ValueError("snapshot")
    if not finite_real(spacing_m) or spacing_m <= 0:
        raise ValueError("spacing")
    if not finite_real(wavelength_m) or wavelength_m <= 0:
        raise ValueError("wavelength")
    phases = unwrap([cmath.phase(value) for value in snapshot])
    fitted_slope = slope(phases)
    argument = fitted_slope * wavelength_m / (2 * math.pi * spacing_m)
    if abs(argument) > 1:
        raise ValueError("angle argument")
    adjacent = sum(value.conjugate() * following for value, following in zip(snapshot, snapshot[1:]))
    return {
        "slope": fitted_slope,
        "angle": math.degrees(math.asin(argument)),
        "adjacent_step": cmath.phase(adjacent),
    }


def clean_snapshot(elements: int, spacing_wavelengths: float, angle_deg: float, phase_deg: float = 20.0) -> tuple[complex, ...]:
    if not integer(elements) or not 2 <= elements <= 32:
        raise ValueError("elements")
    if not finite_real(spacing_wavelengths) or spacing_wavelengths <= 0:
        raise ValueError("spacing")
    if not finite_real(angle_deg) or not -90 < angle_deg < 90:
        raise ValueError("angle")
    phase = math.radians(phase_deg)
    step = 2 * math.pi * spacing_wavelengths * math.sin(math.radians(angle_deg))
    return tuple(cmath.exp(1j * (phase + index * step)) for index in range(elements))


class P61ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")

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
        self.assertEqual(validate_p61_contract(ROOT, self.manifest), [])
        p60 = next(module for module in self.manifest["modules"] if module["id"] == "P60")
        self.assertEqual(p60["status"], "implemented")

    def test_contract_rejects_malformed_duplicate_and_drifted_manifest(self):
        self.assertTrue(validate_p61_contract(ROOT, None))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append(None)
        self.assertIn("every manifest module must be an object", validate_p61_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("P61 must have exactly one manifest entry", validate_p61_contract(ROOT, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(module for module in drifted["modules"] if module["id"] == "P61")["guiding_question"] = "changed"
        self.assertIn("P61 manifest identity drift", validate_p61_contract(ROOT, drifted))

        with tempfile.TemporaryDirectory() as temp:
            fixture_root = Path(temp)
            fixture_module = fixture_root / EXPECTED_IDENTITY["folder"]
            fixture_module.parent.mkdir(parents=True)
            shutil.copytree(MODULE, fixture_module)
            (fixture_module / "lesson.md").unlink()
            self.assertIn("P61 missing lesson.md", validate_p61_contract(fixture_root, self.manifest))
            (fixture_module / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P61 empty lesson.md", validate_p61_contract(fixture_root, self.manifest))

    def test_source_exposes_model_sweeps_failure_recovery_and_bounds(self):
        self.assertEqual(p61_source_contract_errors(self.source), [])

    def test_source_contract_rejects_black_box_and_representative_mutants(self):
        for marker in (
            "validate_controls(controls);",
            "ideal_snapshot = exp(1j*ideal_phase_rad);",
            "geometric_delay_s = -element_position_m*sind(arrival_angle_deg)/",
            "ideal_phase_rad = initial_phase_rad - ...",
            "2*pi*carrier_frequency_hz*geometric_delay_s;",
            "conj(received_snapshot(1:end-1)).*received_snapshot(2:end)",
            "sum(centered_index.*centered_phase_rad)/sum(centered_index.^2);",
            "assert(abs(angle_error_deg) < 1.0, 'P61:BaselineAngleError');",
            "broken_snapshot_mismatch = max(abs(",
            "maximum_stored_numeric_values = 5000;",
        ):
            with self.subTest(marker=marker):
                mutant = self.source.replace(marker, "removed", 1)
                self.assertTrue(p61_source_contract_errors(mutant))
        self.assertTrue(p61_source_contract_errors(self.source + "\nphased.ULA(8)"))

    def test_controls_accept_reviewed_case_and_reject_malformed_values(self):
        controls = validate_controls()
        self.assertEqual(controls["elements"], 8)
        cases = (
            {"frequency": 0.0},
            {"frequency": float("nan")},
            {"angle": 90.0},
            {"elements": 1},
            {"elements": 33},
            {"elements": 8.5},
            {"spacing": complex(1, 1)},
            {"angle_sweep": (-30.0, 30.0, 0.0)},
            {"spacing_sweep": (0.25, 0.5, 0.75)},
            {"frequency_sweep": tuple(float(index + 1) for index in range(8))},
            {"broken_spacing": -1.0},
            {"broken_spacing": 0.75},
            {"broken_alias_angle": 10.0},
            {"max_values": 4999},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    validate_controls(**changes)
        with self.assertRaises(ValueError):
            validate_controls(unknown=1)

    def test_private_seed_is_exact_repeatable_and_bounded(self):
        expected = (
            -2.4594363255591865,
            -0.1864958758150864,
            0.05219237172820211,
            0.3223791768106528,
        )
        first = private_standard_normal(6101, 16)
        second = private_standard_normal(6101, 16)
        for actual, wanted in zip(first[:4], expected):
            self.assertAlmostEqual(actual, wanted, places=14)
        self.assertEqual(first, second)
        for bad_seed, bad_count in ((0, 16), (MODULUS, 16), (6101.5, 16), (6101, 0), (6101, 65)):
            with self.subTest(seed=bad_seed, count=bad_count):
                with self.assertRaises(ValueError):
                    private_standard_normal(bad_seed, bad_count)

    def test_noisy_baseline_matches_geometry_and_recovers_angle(self):
        controls = validate_controls()
        wavelength = controls["c"] / controls["frequency"]
        spacing = controls["spacing"]
        ideal = clean_snapshot(8, spacing / wavelength, 30.0)
        noise = private_standard_normal(6101, 16)
        noise_sigma = 10 ** (-controls["snr"] / 20) / math.sqrt(2)
        received = tuple(
            ideal[index] + noise_sigma * (noise[index] + 1j * noise[8 + index])
            for index in range(8)
        )
        estimate = infer_angle(received, spacing, wavelength)
        unwrapped = unwrap([cmath.phase(value) for value in received])
        phase_mean = sum(unwrapped) / len(unwrapped)
        phase_fit = [
            phase_mean + estimate["slope"] * (index - 3.5)
            for index in range(len(unwrapped))
        ]
        phase_fit_rmse = math.sqrt(
            sum((actual - fitted) ** 2 for actual, fitted in zip(unwrapped, phase_fit))
            / len(unwrapped)
        )
        expected_delay_ps = -spacing * math.sin(math.radians(30)) / controls["c"] * 1e12
        self.assertAlmostEqual(wavelength, 0.09993081933333334, places=14)
        self.assertAlmostEqual(expected_delay_ps, -83.33333333333333, places=11)
        self.assertAlmostEqual(estimate["slope"], 1.5687500925676876, places=13)
        self.assertAlmostEqual(estimate["angle"], 29.95691726617107, places=12)
        self.assertLess(abs(estimate["adjacent_step"] - math.pi / 2), 0.05)
        self.assertAlmostEqual(phase_fit_rmse, 0.014886743039711934, places=14)
        self.assertLess(phase_fit_rmse, 0.08)

    def test_one_way_wavefront_delay_causally_produces_bearing(self):
        c = 299_792_458.0
        frequency = 3.0e9
        wavelength = c / frequency
        spacing = 0.5 * wavelength
        positions = tuple(index * spacing for index in range(8))
        initial_phase = math.radians(20.0)

        for bearing in (-30.0, 0.0, 30.0):
            relative_delays = tuple(
                -position * math.sin(math.radians(bearing)) / c
                for position in positions
            )
            snapshot = tuple(
                cmath.exp(1j * (initial_phase - 2 * math.pi * frequency * delay))
                for delay in relative_delays
            )
            estimate = infer_angle(snapshot, spacing, wavelength)
            expected_step = math.pi * math.sin(math.radians(bearing))

            self.assertAlmostEqual(
                relative_delays[1] - relative_delays[0],
                -spacing * math.sin(math.radians(bearing)) / c,
                places=25,
            )
            self.assertAlmostEqual(estimate["slope"], expected_step, places=13)
            self.assertAlmostEqual(estimate["angle"], bearing, places=12)

        positive_delay = -positions[-1] * math.sin(math.radians(30.0)) / c
        self.assertLess(positive_delay, 0.0)

    def test_angle_spacing_and_frequency_sweeps_obey_the_model(self):
        angles = (-60.0, -30.0, 0.0, 30.0, 60.0)
        angle_slopes = [math.pi * math.sin(math.radians(angle)) for angle in angles]
        self.assertTrue(all(right > left for left, right in zip(angle_slopes, angle_slopes[1:])))
        self.assertAlmostEqual(angle_slopes[0], -angle_slopes[-1], places=14)
        self.assertEqual(angle_slopes[2], 0.0)
        for angle in angles:
            estimate = infer_angle(clean_snapshot(8, 0.5, angle), 0.5, 1.0)
            self.assertAlmostEqual(estimate["angle"], angle, places=12)

        spacing_wavelengths = (0.25, 0.375, 0.5)
        spacing_slopes = [2 * math.pi * value * 0.5 for value in spacing_wavelengths]
        frequency = (1.5e9, 2.25e9, 3.0e9)
        c = 299_792_458.0
        physical_spacing = 0.5 * c / 3.0e9
        frequency_slopes = [2 * math.pi * physical_spacing / (c / value) * 0.5 for value in frequency]
        for spacing_slope, frequency_slope in zip(spacing_slopes, frequency_slopes):
            self.assertAlmostEqual(spacing_slope, frequency_slope, places=14)
        delays = [-physical_spacing * 0.5 / c for _ in frequency]
        self.assertEqual(delays, [delays[0]] * 3)

    def test_alias_is_exact_and_safe_spacing_recovers(self):
        true_angle = math.degrees(math.asin(0.6))
        alias_angle = math.degrees(math.asin(-0.4))
        true_snapshot = clean_snapshot(8, 1.0, true_angle)
        alias_snapshot = clean_snapshot(8, 1.0, alias_angle)
        mismatch = max(abs(true - alias) for true, alias in zip(true_snapshot, alias_snapshot))
        broken = infer_angle(true_snapshot, 1.0, 1.0)
        recovered = infer_angle(clean_snapshot(8, 0.5, true_angle), 0.5, 1.0)
        self.assertLess(mismatch, 1e-12)
        self.assertAlmostEqual(broken["angle"], alias_angle, places=12)
        self.assertGreater(abs(broken["angle"] - true_angle), 50.0)
        self.assertAlmostEqual(recovered["angle"], true_angle, places=12)

    def test_estimator_rejects_malformed_nonfinite_and_nonphysical_input(self):
        good = clean_snapshot(8, 0.5, 30.0)
        bad_cases = (
            (None, 0.5, 1.0),
            ((1 + 0j,), 0.5, 1.0),
            ((1 + 0j, complex(float("nan"), 0)), 0.5, 1.0),
            (good, 0.0, 1.0),
            (good, 0.5, float("inf")),
        )
        for snapshot, spacing, wavelength in bad_cases:
            with self.subTest(snapshot=snapshot, spacing=spacing, wavelength=wavelength):
                with self.assertRaises(ValueError):
                    infer_angle(snapshot, spacing, wavelength)
        with self.assertRaises(ValueError):
            infer_angle(clean_snapshot(8, 0.5, 80.0), 0.1, 1.0)

    def test_documents_are_concept_first_and_cover_limits_and_dependencies(self):
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        for document in (readme, lesson, walkthrough, checks):
            self.assertIn(QUESTION, document)
            self.assertNotIn("TODO", document)
        for marker in (
            "tau_m = -m d sin(theta) / c",
            "Delta_phi = 2 pi (d/lambda) sin(theta)",
            "far field",
            "narrowband",
            "`unwrap`",
            "one-way",
            "P36",
            "P60",
        ):
            self.assertIn(marker, lesson)
        for marker in ("Sweep 1", "Sweep 2", "Broken case", "Recovery", "Ctrl+C"):
            self.assertIn(marker, walkthrough)
        self.assertIn("Short teach-back rubric", checks)
        self.assertGreaterEqual(checks.count("**Correct:**"), 24)

    def test_cli_ten_second_guard_isolation_rollback_and_recovery(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        compatible = copy.deepcopy(self.manifest)
        p62 = next(module for module in compatible["modules"] if module["id"] == "P62")
        p62["future_extension"] = {"accepted": True}
        original_p60 = copy.deepcopy(next(module for module in compatible["modules"] if module["id"] == "P60"))
        original_p62 = copy.deepcopy(p62)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            fixture = self.make_cli_fixture(base, compatible)
            started = self.run_fixture_cli(fixture, "start", "61")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P61", started.stdout)
            self.assertIn("status: implemented", started.stdout)

            state_path = fixture / ".learning/progress.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P60",
                        "completed": [f"P{number:02d}" for number in range(1, 61)],
                        "notes": {"P60": "prerequisite complete"},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            advanced = self.run_fixture_cli(fixture, "start")
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertIn("P61 — See Phase Steering in a Uniform Linear Array", advanced.stdout)
            advanced_state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(advanced_state["completed"], [f"P{number:02d}" for number in range(1, 61)])
            self.assertEqual(advanced_state["notes"], {"P60": "prerequisite complete"})

            rolled_back = copy.deepcopy(compatible)
            next(module for module in rolled_back["modules"] if module["id"] == "P61")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(
                json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8"
            )
            refused = self.run_fixture_cli(fixture, "start", "61")
            self.assertEqual(refused.returncode, 3, refused.stderr)
            self.assertIn("awaits Portfolio batch P61", refused.stdout)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P60"), original_p60)
            self.assertEqual(next(module for module in rolled_back["modules"] if module["id"] == "P62"), original_p62)

            (fixture / "curriculum/modules.json").write_text(
                json.dumps(compatible, indent=2) + "\n", encoding="utf-8"
            )
            recovered = self.run_fixture_cli(fixture, "start", "61")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_cancellation_cleanup_has_no_external_or_persistent_side_effects(self):
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P61'));", self.source)
        self.assertNotIn("close all", self.source)
        for token in ("timer(", "parfor", "webread", "urlread", "fopen(", "save(", "system("):
            self.assertNotIn(token, self.source)
        walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        self.assertIn("Ctrl+C", walkthrough)
        self.assertIn("no checkpoint or partial output", walkthrough)

    def test_public_catalogs_describe_permanent_p61_facts(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 61 follows P60", readme)
        self.assertIn("Project 61 follows P60", start_here)
        self.assertIn(
            "| [P61](../modules/61-see-phase-steering-in-a-uniform-linear-array/) | implemented | 7 |",
            module_index,
        )

    def test_retained_evidence_has_commands_claim_boundary_and_single_newline(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P61-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        for marker in (
            "# P61 Retained Evidence",
            "## Acceptance map",
            "84 modules, 61 implemented",
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
            "## Unperformed validation",
            "Hardware/HIL",
            "RT1/RT2",
            "Unreal",
            "signing",
            "deployment",
            "production",
            "operator-provided `contracts/active-batch.yaml`",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, evidence)
        self.assertTrue(evidence.endswith("\n"))
        self.assertFalse(evidence.endswith("\n\n"))

    def test_changed_text_files_have_one_terminal_newline(self):
        paths = [MODULE / artifact for artifact in ARTIFACTS] + [
            ROOT / "README.md",
            ROOT / "START_HERE.md",
            ROOT / "modules/README.md",
            ROOT / "curriculum/modules.json",
            ROOT / "tests/test_p61_module.py",
            ROOT / "docs/evidence/P61-2026-08-05.md",
        ]
        for path in paths:
            with self.subTest(path=path.name):
                data = path.read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
