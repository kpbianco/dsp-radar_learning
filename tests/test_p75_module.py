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
MODULE = ROOT / "modules/75-build-sar-phase-history-intuition"
EVIDENCE = ROOT / "docs/evidence/P75-2026-08-13.md"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Why does moving one antenna create a large synthetic aperture?"

BASE_CONTROLS = {
    "seed": 7501,
    "c_mps": 3.0e8,
    "carrier_hz": 5.0e9,
    "closest_range_m": 1000.0,
    "target_cross_range_m": 0.0,
    "aperture_length_m": 80.0,
    "platform_spacing_m": 0.2,
    "range_min_m": 995.0,
    "range_max_m": 1005.0,
    "range_spacing_m": 0.05,
    "envelope_sigma_m": 0.60,
    "target_voltage": 1.0,
    "snr_db": 30.0,
    "cross_range_sweep_m": [-20.0, 0.0, 20.0],
    "aperture_sweep_m": [20.0, 40.0, 80.0],
    "focus_cross_range_m": [-26.0 + 0.25 * index for index in range(209)],
    "max_aperture_samples": 501,
    "max_fast_time_samples": 301,
    "max_focus_candidates": 301,
    "max_sweep_cases": 5,
    "max_private_values": 400000,
    "max_working_values": 4000000,
    "max_figures": 5,
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
            elif not path.read_text(encoding="utf-8", errors="replace").strip():
                errors.append(f"empty {name}")
            elif "TODO" in path.read_text(encoding="utf-8", errors="replace"):
                errors.append(f"TODO remains in {name}")
    return errors


def controls_errors(controls: dict) -> list[str]:
    errors: list[str] = []
    vectors = ("cross_range_sweep_m", "aperture_sweep_m", "focus_cross_range_m")
    for name in vectors:
        values = controls.get(name)
        if (
            not isinstance(values, list)
            or not values
            or any(isinstance(value, (list, tuple, bool, complex)) for value in values)
            or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values)
        ):
            errors.append(f"invalid row vector: {name}")
    if errors:
        return errors
    finite_scalars = (
        "target_cross_range_m", "range_min_m", "range_max_m", "snr_db",
    )
    for name in finite_scalars:
        value = controls.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"invalid finite scalar: {name}")
    positive = (
        "c_mps", "carrier_hz", "closest_range_m", "aperture_length_m",
        "platform_spacing_m", "range_spacing_m", "envelope_sigma_m",
        "target_voltage", "max_aperture_samples", "max_fast_time_samples",
        "max_focus_candidates", "max_sweep_cases", "max_private_values",
        "max_working_values", "max_figures", "max_phase_step_rad",
    )
    for name in positive:
        value = controls.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            errors.append(f"invalid positive scalar: {name}")
    seed = controls.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 1 <= seed < 2147483647:
        errors.append("invalid seed")
    if controls["range_min_m"] <= 0 or controls["range_max_m"] <= controls["range_min_m"]:
        errors.append("invalid fast-time axis")
    try:
        noise_rms = controls["target_voltage"] * 10 ** (-controls["snr_db"] / 20)
    except OverflowError:
        noise_rms = math.inf
    if not math.isfinite(noise_rms) or noise_rms < 0:
        errors.append("invalid noise scale")
    if controls["max_phase_step_rad"] >= math.pi:
        errors.append("invalid phase limit")
    if any(a >= b for a, b in zip(controls["focus_cross_range_m"], controls["focus_cross_range_m"][1:])):
        errors.append("invalid focus grid")
    if any(value <= 0 or value > controls["aperture_length_m"] for value in controls["aperture_sweep_m"]):
        errors.append("invalid aperture sweep")
    baseline_ratio = controls["aperture_length_m"] / (2 * controls["platform_spacing_m"])
    if abs(baseline_ratio - round(baseline_ratio)) > 1.0e-9:
        errors.append("off-grid baseline aperture")
    fast_ratio = (controls["range_max_m"] - controls["range_min_m"]) / controls["range_spacing_m"]
    if abs(fast_ratio - round(fast_ratio)) > 1.0e-9:
        errors.append("off-grid fast time")
    for value in controls["aperture_sweep_m"]:
        ratio = value / (2 * controls["platform_spacing_m"])
        if abs(ratio - round(ratio)) > 1.0e-9:
            errors.append("off-grid aperture")
    if errors:
        return errors
    aperture_samples = round(controls["aperture_length_m"] / controls["platform_spacing_m"]) + 1
    fast_samples = round((controls["range_max_m"] - controls["range_min_m"]) / controls["range_spacing_m"]) + 1
    if aperture_samples > controls["max_aperture_samples"] or fast_samples > controls["max_fast_time_samples"]:
        errors.append("sample ceiling")
    if len(controls["focus_cross_range_m"]) > controls["max_focus_candidates"]:
        errors.append("focus ceiling")
    if max(len(controls["cross_range_sweep_m"]), len(controls["aperture_sweep_m"])) > controls["max_sweep_cases"]:
        errors.append("sweep ceiling")
    if 2 * aperture_samples * fast_samples > controls["max_private_values"]:
        errors.append("private ceiling")
    predicted = (
        12 * aperture_samples * fast_samples
        + 20 * aperture_samples * len(controls["cross_range_sweep_m"])
        + 12 * aperture_samples * len(controls["focus_cross_range_m"])
        + 20 * (aperture_samples + fast_samples + len(controls["focus_cross_range_m"]))
    )
    if predicted > controls["max_working_values"]:
        errors.append("working preflight")
    if errors:
        return errors
    wavelength = controls["c_mps"] / controls["carrier_hz"]
    positions = [
        -controls["aperture_length_m"] / 2 + index * controls["platform_spacing_m"]
        for index in range(aperture_samples)
    ]
    reviewed = [controls["target_cross_range_m"], *controls["cross_range_sweep_m"], *controls["focus_cross_range_m"]]
    for target in reviewed:
        ranges = [math.hypot(position - target, controls["closest_range_m"]) for position in positions]
        phases = [-4 * math.pi * (value - controls["closest_range_m"]) / wavelength for value in ranges]
        if max(abs(after - before) for before, after in zip(phases, phases[1:])) >= controls["max_phase_step_rad"]:
            errors.append("spatial alias")
        if min(ranges) - 4 * controls["envelope_sigma_m"] < controls["range_min_m"]:
            errors.append("low echo support")
        if max(ranges) + 4 * controls["envelope_sigma_m"] > controls["range_max_m"]:
            errors.append("high echo support")
    return errors


def private_complex_noise(seed: int, count: int, maximum: int = 400000) -> list[complex]:
    if not isinstance(seed, int) or isinstance(seed, bool) or not 1 <= seed < 2147483647:
        raise ValueError("invalid seed")
    if not isinstance(count, int) or isinstance(count, bool) or count < 1 or 2 * count > maximum:
        raise ValueError("invalid count")
    state = seed
    uniforms: list[float] = []
    for _ in range(2 * count):
        state = (16807 * state) % 2147483647
        uniforms.append(state / 2147483647)
    values: list[complex] = []
    for index in range(0, len(uniforms), 2):
        radius = math.sqrt(-2 * math.log(max(uniforms[index], float.fromhex("0x1p-1022"))))
        angle = 2 * math.pi * uniforms[index + 1]
        values.append(radius * cmath.exp(1j * angle) / math.sqrt(2))
    return values


def range_phase(position_m: float, target_m: float = 0.0) -> tuple[float, float]:
    wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
    slant = math.hypot(position_m - target_m, BASE_CONTROLS["closest_range_m"])
    return slant, -4 * math.pi * (slant - BASE_CONTROLS["closest_range_m"]) / wavelength


def coherent_score(measurement: list[complex], positions: list[float], candidates: list[float]) -> list[float]:
    normalizer = sum(abs(value) for value in measurement)
    scores: list[float] = []
    for candidate in candidates:
        phasors = [cmath.exp(1j * range_phase(position, candidate)[1]) for position in positions]
        scores.append(abs(sum(value * phasor.conjugate() for value, phasor in zip(measurement, phasors))) / normalizer)
    return scores


def noisy_phase_history(
    target_m: float = 0.0,
) -> tuple[
    list[float],
    list[float],
    list[list[complex]],
    list[list[complex]],
    list[list[complex]],
]:
    positions = [-40.0 + 0.2 * index for index in range(401)]
    range_axis = [995.0 + 0.05 * index for index in range(201)]
    noise = private_complex_noise(7501, len(positions) * len(range_axis))
    noise_rms = 10 ** (-30.0 / 20)
    received: list[list[complex]] = []
    clean: list[list[complex]] = []
    additive_noise: list[list[complex]] = []
    for aperture_index, position in enumerate(positions):
        slant, phase = range_phase(position, target_m)
        phasor = cmath.exp(1j * phase)
        clean_row: list[complex] = []
        noise_row: list[complex] = []
        received_row: list[complex] = []
        for range_index, sampled_range in enumerate(range_axis):
            envelope = math.exp(-0.5 * ((sampled_range - slant) / 0.60) ** 2)
            signal = envelope * phasor
            # MATLAB reshape fills the aperture dimension first (column-major).
            additive = noise_rms * noise[
                aperture_index + range_index * len(positions)
            ]
            clean_row.append(signal)
            noise_row.append(additive)
            received_row.append(signal + additive)
        clean.append(clean_row)
        additive_noise.append(noise_row)
        received.append(received_row)
    return positions, range_axis, received, clean, additive_noise


def ridge_measurement(
    phase_history: list[list[complex]],
    positions: list[float],
    range_axis: list[float],
    target_m: float = 0.0,
) -> list[complex]:
    measurement: list[complex] = []
    for aperture_index, position in enumerate(positions):
        slant, _ = range_phase(position, target_m)
        ridge_index = min(
            range(len(range_axis)),
            key=lambda index: abs(range_axis[index] - slant),
        )
        measurement.append(phase_history[aperture_index][ridge_index])
    return measurement


class P75ModuleTests(unittest.TestCase):
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
        return subprocess.run(
            [str(fixture / "bin/learn"), *arguments], cwd=fixture,
            text=True, capture_output=True, timeout=3, check=False,
        )

    def test_artifacts_manifest_identity_and_permanent_dependency(self):
        self.assertEqual(artifact_errors(MODULE), [])
        entry = module_entry(self.data, "P75")
        expected = {
            "number": 75,
            "title": "Build SAR Phase-History Intuition",
            "guiding_question": QUESTION,
            "phase": 9,
            "phase_title": "SAR, ISAR, Passive Radar, and Capstone",
            "slug": "build-sar-phase-history-intuition",
            "folder": "modules/75-build-sar-phase-history-intuition",
            "status": "implemented",
            "implementation_batch": "P75",
        }
        for key, value in expected.items():
            self.assertEqual(entry[key], value)
        self.assertEqual(module_entry(self.data, "P74")["status"], "implemented")
        self.assertEqual(module_entry(self.data, "P76")["implementation_batch"], "P76")
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
            (fixture / "lesson.md").write_text("TODO generic lesson\n", encoding="utf-8")
            self.assertIn("TODO remains in lesson.md", artifact_errors(fixture))

    def test_source_exposes_geometry_history_sweeps_failure_recovery_and_bounds(self):
        markers = (
            "baseline_seed = 7501;", "carrier_frequency_hz = 5.0e9;",
            "closest_range_m = 1000.0;", "aperture_length_m = 80.0;",
            "platform_spacing_m = 0.2;", "validate_controls(controls);",
            "slant_range_m = sqrt(closest_range_m^2",
            "delay_s = 2*slant_range_m/c_mps;",
            "phase_rad = -4*pi*(slant_range_m-closest_range_m)/wavelength_m;",
            "range_envelope", "raw_phase_history", "fast_time_us",
            "target_cross_range_sweep_m = [-20.0 0.0 20.0];",
            "aperture_length_sweep_m = [20.0 40.0 80.0];",
            "Intentionally broken case", "magnitude_only_measurement = abs",
            "explicit_cross_range_score", "isequaln(complex_aperture_measurement",
            "P75:SameDataRecovery", "P75:SpatialAliasing",
            "P75:EchoSupport", "P75:NoiseScale", "P75:BaselineApertureGrid",
            "P75:FastTimeGrid", "P75:ResourceCeilings", "P75:WorkingPreflight",
            "pre_results_workspace_inventory = whos;", "p75_results = struct",
        )
        for marker in markers:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P75"), 5)
        self.assertNotIn("rng(", self.source.lower())

    def test_source_has_no_opaque_toolbox_or_external_side_effect(self):
        lowered = self.source.lower()
        for forbidden in (
            "phased.", "sar", "backprojection(", "rangecompressor",
            "pulsecompression", "awgn(", "normrnd(", "randn(", "parfor",
            "timer(", "webread(", "webwrite(", "urlread(", "fopen(",
            "save(", "writematrix(", "system(", "unix(", "dos(",
        ):
            if forbidden == "sar":
                continue
            self.assertNotIn(forbidden, lowered)
        self.assertIsNone(re.search(r"\b(?:fft|ifft|xcorr|conv2|imresize)\(", lowered))

    def test_control_contract_accepts_baseline_and_rejects_malformed_resources(self):
        self.assertEqual(controls_errors(copy.deepcopy(BASE_CONTROLS)), [])
        cases: list[tuple[str, dict]] = []
        nested = copy.deepcopy(BASE_CONTROLS)
        nested["cross_range_sweep_m"] = [[-20.0], [0.0], [20.0]]
        cases.append(("column sweep", nested))
        nonfinite = copy.deepcopy(BASE_CONTROLS)
        nonfinite["focus_cross_range_m"][3] = math.nan
        cases.append(("nonfinite focus", nonfinite))
        zero_range = copy.deepcopy(BASE_CONTROLS)
        zero_range["closest_range_m"] = 0.0
        cases.append(("zero range", zero_range))
        reversed_axis = copy.deepcopy(BASE_CONTROLS)
        reversed_axis["range_max_m"] = reversed_axis["range_min_m"]
        cases.append(("reversed range", reversed_axis))
        off_grid = copy.deepcopy(BASE_CONTROLS)
        off_grid["aperture_sweep_m"][0] = 20.1
        cases.append(("off-grid aperture", off_grid))
        baseline_grid = copy.deepcopy(BASE_CONTROLS)
        baseline_grid["platform_spacing_m"] = 0.3
        cases.append(("off-grid baseline", baseline_grid))
        fast_grid = copy.deepcopy(BASE_CONTROLS)
        fast_grid["range_spacing_m"] = 0.06
        cases.append(("off-grid fast time", fast_grid))
        focus = copy.deepcopy(BASE_CONTROLS)
        focus["focus_cross_range_m"][2] = focus["focus_cross_range_m"][1]
        cases.append(("non-increasing focus", focus))
        phase_limit = copy.deepcopy(BASE_CONTROLS)
        phase_limit["max_phase_step_rad"] = math.pi
        cases.append(("unsafe limit", phase_limit))
        alias = copy.deepcopy(BASE_CONTROLS)
        alias["platform_spacing_m"] = 1.0
        cases.append(("spatial alias", alias))
        support = copy.deepcopy(BASE_CONTROLS)
        support["range_max_m"] = 1002.0
        cases.append(("truncated echo", support))
        snr = copy.deepcopy(BASE_CONTROLS)
        snr["snr_db"] = -10000.0
        cases.append(("overflow noise", snr))
        private = copy.deepcopy(BASE_CONTROLS)
        private["max_private_values"] = 1000
        cases.append(("private ceiling", private))
        working = copy.deepcopy(BASE_CONTROLS)
        working["max_working_values"] = 100000
        cases.append(("working ceiling", working))
        sweep = copy.deepcopy(BASE_CONTROLS)
        sweep["max_sweep_cases"] = 2
        cases.append(("sweep ceiling", sweep))
        for label, controls in cases:
            with self.subTest(label=label):
                self.assertTrue(controls_errors(controls))

    def test_geometry_phase_factor_sign_curvature_and_cross_range_oracle(self):
        wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
        center_range, center_phase = range_phase(0.0)
        edge_range, edge_phase = range_phase(40.0)
        self.assertEqual(center_range, 1000.0)
        self.assertEqual(center_phase, 0.0)
        self.assertAlmostEqual(edge_range - center_range, 0.7996802557443061)
        self.assertAlmostEqual((center_phase - edge_phase) / (2 * math.pi), 26.656008524810204)
        self.assertLess(edge_phase, 0.0)
        h = 0.01
        _, left_phase = range_phase(-h)
        _, right_phase = range_phase(h)
        curvature = (left_phase - 2 * center_phase + right_phase) / h**2
        self.assertAlmostEqual(curvature, -4 * math.pi / (wavelength * 1000.0), delta=1.0e-5)
        for target in (-20.0, 0.0, 20.0):
            positions = [-40.0 + 0.2 * index for index in range(401)]
            ranges = [range_phase(position, target)[0] for position in positions]
            self.assertAlmostEqual(positions[ranges.index(min(ranges))], target)
        self.assertAlmostEqual(range_phase(0.0, -20.0)[0], range_phase(0.0, 20.0)[0])
        self.assertAlmostEqual(range_phase(0.0, -20.0)[1], range_phase(0.0, 20.0)[1])
        self.assertNotAlmostEqual(range_phase(-10.0, -20.0)[1], range_phase(-10.0, 20.0)[1])

    def test_aperture_sweep_uses_centered_subsets_with_permanent_scaling(self):
        spans: list[float] = []
        counts: list[int] = []
        for length in BASE_CONTROLS["aperture_sweep_m"]:
            positions = [-length / 2 + 0.2 * index for index in range(round(length / 0.2) + 1)]
            phases = [range_phase(position)[1] / (2 * math.pi) for position in positions]
            counts.append(len(positions))
            spans.append(max(phases) - min(phases))
        self.assertEqual(counts, [101, 201, 401])
        for actual, expected in zip(spans, [1.6666250020837956, 6.666000133301017, 26.656008524810204]):
            self.assertAlmostEqual(actual, expected)
        self.assertTrue(all(a < b for a, b in zip(spans, spans[1:])))
        self.assertRegex(self.source, r"keep = abs\(platform_position_m\).*?[\s\S]*?case_positions_m = platform_position_m\(keep\)")

    def test_private_generator_is_repeatable_bounded_and_isolated(self):
        first = private_complex_noise(7501, 100)
        repeated = private_complex_noise(7501, 100)
        other = private_complex_noise(7601, 100)
        self.assertEqual(first, repeated)
        self.assertNotEqual(first, other)
        self.assertAlmostEqual(first[0].real, -0.8575952870989945)
        self.assertAlmostEqual(first[0].imag, -1.4490516040472932)
        with self.assertRaises(ValueError):
            private_complex_noise(0, 1)
        with self.assertRaises(ValueError):
            private_complex_noise(7501, 200001)

    def test_magnitude_failure_and_unchanged_complex_recovery_oracle(self):
        positions = [-40.0 + 0.2 * index for index in range(401)]
        measurement = [cmath.exp(1j * range_phase(position)[1]) for position in positions]
        immutable = list(measurement)
        candidates = BASE_CONTROLS["focus_cross_range_m"]
        broken = coherent_score([complex(abs(value), 0.0) for value in measurement], positions, candidates)
        recovered = coherent_score(measurement, positions, candidates)
        broken_index = max(range(len(broken)), key=broken.__getitem__)
        recovered_index = max(range(len(recovered)), key=recovered.__getitem__)
        self.assertLess(broken[broken_index], 0.08)
        self.assertEqual(candidates[recovered_index], 0.0)
        self.assertAlmostEqual(recovered[recovered_index], 1.0)
        self.assertEqual(measurement, immutable)

    def test_full_noisy_matrix_ridge_failure_and_recovery_oracle(self):
        positions, range_axis, received, clean, additive_noise = noisy_phase_history()
        repeated = noisy_phase_history()
        self.assertEqual((positions, range_axis, received, clean, additive_noise), repeated)
        self.assertEqual(len(received), 401)
        self.assertTrue(all(len(row) == 201 for row in received))
        for aperture_index, range_index in ((0, 0), (0, 116), (200, 100), (400, 200)):
            self.assertEqual(
                received[aperture_index][range_index],
                clean[aperture_index][range_index]
                + additive_noise[aperture_index][range_index],
            )
        self.assertEqual(max(range(201), key=lambda index: abs(clean[200][index])), 100)
        self.assertEqual(max(range(201), key=lambda index: abs(clean[0][index])), 116)
        self.assertEqual(max(range(201), key=lambda index: abs(clean[400][index])), 116)

        candidates = BASE_CONTROLS["focus_cross_range_m"]
        measurement = ridge_measurement(received, positions, range_axis)
        immutable = list(measurement)
        broken = coherent_score([complex(abs(value), 0.0) for value in measurement], positions, candidates)
        recovered = coherent_score(measurement, positions, candidates)
        broken_index = max(range(len(broken)), key=broken.__getitem__)
        recovered_index = max(range(len(recovered)), key=recovered.__getitem__)
        self.assertEqual(candidates[broken_index], 24.0)
        self.assertAlmostEqual(broken[broken_index], 0.07414065587828747)
        self.assertEqual(candidates[recovered_index], 0.0)
        self.assertAlmostEqual(recovered[recovered_index], 0.9997666916507448)
        self.assertEqual(measurement, immutable)

    def test_equal_closest_range_targets_focus_to_distinct_cross_range_coordinates(self):
        candidates = BASE_CONTROLS["focus_cross_range_m"]
        measurements: dict[float, list[complex]] = {}
        for target_m in (-20.0, 20.0):
            positions, range_axis, received, _, _ = noisy_phase_history(target_m)
            measurement = ridge_measurement(received, positions, range_axis, target_m)
            measurements[target_m] = measurement
            scores = coherent_score(measurement, positions, candidates)
            peak_index = max(range(len(scores)), key=scores.__getitem__)
            self.assertEqual(range_phase(target_m, target_m)[0], 1000.0)
            self.assertEqual(candidates[peak_index], target_m)
            self.assertGreater(scores[peak_index], 0.99)
        self.assertNotEqual(measurements[-20.0], measurements[20.0])

    def test_documents_are_concept_first_and_cover_limits(self):
        combined = "\n".join(self.documents.values()).lower()
        for marker in (
            "two-way", "phase curvature", "fast time", "cross-range",
            "closest approach", "vertex", "aperture length", "spatial sampling",
            "magnitude-only", "unchanged", "recovery", "range migration",
            "motion error", "point-target", "cancellation", "ctrl+c", "rollback",
            "teach-back", "no optional toolbox", "base matlab r2016b or newer",
            "4,000,000", "five tagged figure", "p76", "p77", "p78", "p80",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(self.documents["checks.md"].count("**Correct:**"), 29)

    def test_cli_timeout_cancellation_rollback_recovery_isolation_and_future_compatibility(self):
        compatible = copy.deepcopy(self.data)
        module_entry(compatible, "P76")["status"] = "implemented"
        module_entry(compatible, "P76")["future_metadata"] = {"allowed": True}
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.make_cli_fixture(Path(directory), compatible)
            started = self.run_cli(fixture, "start", "75")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("status: implemented", started.stdout)
            rolled_back = copy.deepcopy(compatible)
            module_entry(rolled_back, "P75")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8")
            refused = self.run_cli(fixture, "start", "75")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P75", refused.stdout)
            (fixture / "curriculum/modules.json").write_text(json.dumps(compatible, indent=2) + "\n", encoding="utf-8")
            recovered = self.run_cli(fixture, "start", "75")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)
        walkthrough = " ".join(self.documents["walkthrough.md"].lower().split())
        for marker in ("ctrl+c", "no worker", "no background", "rerun from the top", "rollback"):
            self.assertIn(marker, walkthrough)

    def test_catalogs_evidence_and_exact_eof_policy(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 75 begins Phase 9", root_readme)
        self.assertIn("Project 75 follows P74", start_here)
        self.assertRegex(module_index, r"\| \[P75\].*\| implemented \|")
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
            ROOT / "tests/test_p75_module.py", EVIDENCE,
        ]
        for path in changed_text_paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
