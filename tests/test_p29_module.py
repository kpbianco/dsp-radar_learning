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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/29-build-a-radar-power-budget-experiment"
QUESTION = "How quickly does received echo power fall with range?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
EXPECTED_IDENTITY = {
    "number": 29,
    "id": "P29",
    "title": "Build a Radar Power-Budget Experiment",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "build-a-radar-power-budget-experiment",
    "folder": "modules/29-build-a-radar-power-budget-experiment",
    "status": "implemented",
    "implementation_batch": "P29",
}


def validate_p29_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P29 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P29 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    matches = [
        entry
        for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P29"
    ]
    if len(matches) != 1:
        return errors + [f"expected one P29 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P29 {key} must be {expected!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def canonical_controls() -> dict:
    return {
        "random_seed": 2901,
        "speed_of_light_mps": 299792458.0,
        "boltzmann_j_per_k": 1.380649e-23,
        "transmit_power_w": 100e3,
        "transmit_gain_dbi": 35.0,
        "receive_gain_dbi": 35.0,
        "carrier_frequency_hz": 10e9,
        "target_rcs_m2": 1.0,
        "system_loss_db": 6.0,
        "input_reference_temperature_k": 290.0,
        "receiver_bandwidth_hz": 1e6,
        "noise_figure_db": 4.0,
        "required_snr_db": 13.0,
        "reference_range_km": 40.0,
        "range_km": tuple(1.0 + 0.5 * index for index in range(239)),
        "rcs_sweep_m2": (0.1, 1.0, 10.0),
        "frequency_sweep_ghz": (3.0, 10.0, 30.0),
        "transmit_power_sweep_kw": (25.0, 100.0, 400.0),
        "noise_sample_count": 4096,
        "max_range_points": 239,
        "max_rcs_cases": 3,
        "max_frequency_cases": 3,
        "max_transmit_power_cases": 3,
        "max_noise_samples": 4096,
        "max_figure_groups": 4,
        "max_stored_numeric_values": 40000,
    }


def parse_matlab_controls(source: str) -> dict:
    canonical = canonical_controls()
    vector_names = {
        "range_km",
        "rcs_sweep_m2",
        "frequency_sweep_ghz",
        "transmit_power_sweep_kw",
    }
    parsed: dict[str, object] = {}
    for name in canonical.keys() - vector_names:
        matches = re.findall(
            rf"(?m)^\s*{re.escape(name)}\s*=\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?)\s*;",
            source,
            flags=re.IGNORECASE,
        )
        if len(matches) != 1:
            raise ValueError(f"expected one numeric MATLAB assignment for {name}")
        numeric_value = float(matches[0])
        if isinstance(canonical[name], int):
            if not numeric_value.is_integer():
                raise ValueError(f"MATLAB integer control {name} is not integral")
            parsed[name] = int(numeric_value)
        else:
            parsed[name] = numeric_value

    range_match = re.findall(
        r"(?m)^\s*range_km\s*=\s*([-+\d.e]+)\s*:\s*([-+\d.e]+)\s*:\s*([-+\d.e]+)\s*;",
        source,
        flags=re.IGNORECASE,
    )
    if len(range_match) != 1:
        raise ValueError("expected one MATLAB colon assignment for range_km")
    start, step, stop = (float(value) for value in range_match[0])
    count = int(round((stop - start) / step)) + 1
    parsed["range_km"] = tuple(start + step * index for index in range(count))

    for name in vector_names - {"range_km"}:
        matches = re.findall(
            rf"(?m)^\s*{re.escape(name)}\s*=\s*\[([^\]]+)\]\s*;",
            source,
        )
        if len(matches) != 1:
            raise ValueError(f"expected one MATLAB vector assignment for {name}")
        parsed[name] = tuple(float(value) for value in matches[0].split())
    return parsed


def validate_matlab_source_contract(source: str) -> list[str]:
    errors: list[str] = []
    try:
        parsed = parse_matlab_controls(source)
    except ValueError as exc:
        return [str(exc)]
    for name, expected in canonical_controls().items():
        if parsed.get(name) != expected:
            errors.append(f"MATLAB {name} drifted from the canonical control")

    compact = " ".join(source.replace("...", "").split())
    required_equations = (
        "assert(isscalar(control_value) && isnumeric(control_value) && ~islogical(control_value) && isreal(control_value) && isfinite(control_value) && control_value > 0,",
        "assert(isscalar(control_value) && isnumeric(control_value) && ~islogical(control_value) && isreal(control_value) && isfinite(control_value) && control_value >= 0,",
        "transmit_gain_linear = 10^(transmit_gain_dbi/10);",
        "receive_gain_linear = 10^(receive_gain_dbi/10);",
        "system_loss_linear = 10^(system_loss_db/10);",
        "noise_factor_linear = 10^(noise_figure_db/10);",
        "wavelength_m = speed_of_light_mps/carrier_frequency_hz;",
        "range_m = range_km*1e3;",
        "radar_equation_numerator = transmit_power_w*transmit_gain_linear* receive_gain_linear*wavelength_m^2*target_rcs_m2;",
        "received_power_w = radar_equation_numerator ./ ((4*pi)^3*range_m.^4*system_loss_linear);",
        "noise_power_w = boltzmann_j_per_k*input_reference_temperature_k* receiver_bandwidth_hz*noise_factor_linear;",
        "detection_threshold_w = noise_power_w*10^(required_snr_db/10);",
        "detection_margin_db = received_power_dbm-detection_threshold_dbm;",
        "broken_received_power_w = received_power_w(reference_index) .* ((reference_range_km*1e3)^2 ./ range_m.^2);",
        "one_at_a_time_power_ratio = one_at_a_time_received_power_w/one_at_a_time_received_power_w(1);",
        "case_transmit_power_w = transmit_power_w*[1 2 1 1 1 1 1];",
        "case_wavelength_m = wavelength_m*[1 1 1 1 2 1 1];",
        "case_system_loss_linear = system_loss_linear*[1 1 1 1 1 0.5 1];",
        "case_target_rcs_m2 = target_rcs_m2*[1 1 1 1 1 1 2];",
        "sweep_frequency_hz = frequency_sweep_ghz(frequency_index)*1e9;",
        "sweep_transmit_power_w = transmit_power_sweep_kw(power_index)*1e3;",
    )
    for equation in required_equations:
        if equation not in compact:
            errors.append(f"missing explicit MATLAB equation: {equation}")
    return errors


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    vector_names = (
        "range_km",
        "rcs_sweep_m2",
        "frequency_sweep_ghz",
        "transmit_power_sweep_kw",
    )
    canonical = canonical_controls()
    for name in vector_names:
        value = controls[name]
        if not isinstance(value, (tuple, list)):
            raise ValueError(f"{name} must be a bounded numeric vector")
        if not all(_finite_real(item) and item > 0 for item in value):
            raise ValueError(f"{name} must contain finite positive values")
        if tuple(value) != canonical[name]:
            raise ValueError(f"{name} must equal its canonical vector")

    positive_editable = (
        "transmit_power_w",
        "carrier_frequency_hz",
        "target_rcs_m2",
        "input_reference_temperature_k",
        "receiver_bandwidth_hz",
        "reference_range_km",
    )
    nonnegative_db_editable = (
        "transmit_gain_dbi",
        "receive_gain_dbi",
        "system_loss_db",
        "noise_figure_db",
        "required_snr_db",
    )
    for name in positive_editable:
        if not _finite_real(controls[name]) or controls[name] <= 0:
            raise ValueError(f"{name} must be a finite positive scalar")
    for name in nonnegative_db_editable:
        if not _finite_real(controls[name]) or controls[name] < 0:
            raise ValueError(f"{name} must be a finite nonnegative dB scalar")
    if controls["reference_range_km"] not in controls["range_km"]:
        raise ValueError("reference range must be present in range grid")

    editable = set(vector_names) | set(positive_editable) | set(nonnegative_db_editable)
    for name, expected in canonical.items():
        if name in editable:
            continue
        value = controls[name]
        if not _finite_real(value) or value != expected:
            raise ValueError(f"{name} must equal its finite canonical scalar")


    validate_resource_bounds(controls)


def validate_resource_bounds(controls: dict) -> None:
    if len(controls["range_km"]) > controls["max_range_points"]:
        raise ValueError("range grid exceeds resource ceiling")
    if len(controls["rcs_sweep_m2"]) > controls["max_rcs_cases"]:
        raise ValueError("RCS sweep exceeds resource ceiling")
    if len(controls["frequency_sweep_ghz"]) > controls["max_frequency_cases"]:
        raise ValueError("frequency sweep exceeds resource ceiling")
    if len(controls["transmit_power_sweep_kw"]) > controls["max_transmit_power_cases"]:
        raise ValueError("power sweep exceeds resource ceiling")
    if controls["noise_sample_count"] > controls["max_noise_samples"]:
        raise ValueError("noise sample count exceeds resource ceiling")
    estimated = (
        20 * len(controls["range_km"])
        + 8 * controls["noise_sample_count"]
        + 100
        * (
            len(controls["rcs_sweep_m2"])
            + len(controls["frequency_sweep_ghz"])
            + len(controls["transmit_power_sweep_kw"])
        )
    )
    if estimated > controls["max_stored_numeric_values"]:
        raise ValueError("conservative numeric storage bound exceeded")


def received_power_w(
    range_m: float,
    *,
    transmit_power_w: float,
    transmit_gain_linear: float,
    receive_gain_linear: float,
    wavelength_m: float,
    target_rcs_m2: float,
    system_loss_linear: float,
) -> float:
    values = (
        range_m,
        transmit_power_w,
        transmit_gain_linear,
        receive_gain_linear,
        wavelength_m,
        target_rcs_m2,
        system_loss_linear,
    )
    if not all(_finite_real(value) and value > 0 for value in values):
        raise ValueError("range-equation inputs must be finite and positive")
    numerator = (
        transmit_power_w
        * transmit_gain_linear
        * receive_gain_linear
        * wavelength_m**2
        * target_rcs_m2
    )
    return numerator / ((4 * math.pi) ** 3 * range_m**4 * system_loss_linear)


def watts_to_dbw(power_w: float) -> float:
    if not _finite_real(power_w) or power_w <= 0:
        raise ValueError("power must be finite and positive")
    return 10 * math.log10(power_w)


def deterministic_model(controls: dict | None = None) -> dict:
    if controls is None:
        source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        controls = parse_matlab_controls(source)
    gain_tx = 10 ** (controls["transmit_gain_dbi"] / 10)
    gain_rx = 10 ** (controls["receive_gain_dbi"] / 10)
    loss = 10 ** (controls["system_loss_db"] / 10)
    wavelength = controls["speed_of_light_mps"] / controls["carrier_frequency_hz"]
    kwargs = {
        "transmit_power_w": controls["transmit_power_w"],
        "transmit_gain_linear": gain_tx,
        "receive_gain_linear": gain_rx,
        "wavelength_m": wavelength,
        "target_rcs_m2": controls["target_rcs_m2"],
        "system_loss_linear": loss,
    }
    ranges_m = [value * 1000 for value in controls["range_km"]]
    powers_w = [received_power_w(value, **kwargs) for value in ranges_m]
    powers_dbm = [watts_to_dbw(value) + 30 for value in powers_w]

    noise_factor = 10 ** (controls["noise_figure_db"] / 10)
    noise_w = (
        controls["boltzmann_j_per_k"]
        * controls["input_reference_temperature_k"]
        * controls["receiver_bandwidth_hz"]
        * noise_factor
    )
    threshold_w = noise_w * 10 ** (controls["required_snr_db"] / 10)
    threshold_dbm = watts_to_dbw(threshold_w) + 30
    margins_db = [value - threshold_dbm for value in powers_dbm]
    numerator = (
        controls["transmit_power_w"]
        * gain_tx
        * gain_rx
        * wavelength**2
        * controls["target_rcs_m2"]
    )
    max_range_km = (
        numerator / ((4 * math.pi) ** 3 * loss * threshold_w)
    ) ** 0.25 / 1000

    generator = random.Random(controls["random_seed"])
    noise_i = [generator.gauss(0.0, 1.0) for _ in range(controls["noise_sample_count"])]
    noise_q = [generator.gauss(0.0, 1.0) for _ in range(controls["noise_sample_count"])]
    measured_noise_w = noise_w * sum(
        (i * i + q * q) / 2 for i, q in zip(noise_i, noise_q)
    ) / controls["noise_sample_count"]
    return {
        "ranges_m": ranges_m,
        "powers_w": powers_w,
        "powers_dbm": powers_dbm,
        "noise_w": noise_w,
        "threshold_w": threshold_w,
        "threshold_dbm": threshold_dbm,
        "margins_db": margins_db,
        "max_range_km": max_range_km,
        "measured_noise_w": measured_noise_w,
        "noise_i": noise_i,
        "noise_q": noise_q,
        "kwargs": kwargs,
    }


class P29ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text())
        cls.text = {
            name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        }
        cls.experiment = cls.text["experiment.m"]
        cls.model = deterministic_model()

    def test_complete_artifacts_exact_identity_and_prerequisite(self):
        self.assertEqual(validate_p29_contract(MODULE, self.manifest), [])
        for text in self.text.values():
            self.assertIn(QUESTION, text)
        prerequisite = next(
            entry for entry in self.manifest["modules"] if entry["id"] == "P28"
        )
        self.assertEqual(prerequisite["status"], "implemented")

    def test_contract_validator_rejects_malformed_identity_and_artifacts(self):
        self.assertIn("manifest modules must be a list", validate_p29_contract(MODULE, {}))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertTrue(any("found 2" in item for item in validate_p29_contract(MODULE, duplicate)))
        for key, expected in EXPECTED_IDENTITY.items():
            with self.subTest(key=key):
                wrong = copy.deepcopy(self.manifest)
                entry = next(item for item in wrong["modules"] if item["id"] == "P29")
                entry[key] = "wrong" if not isinstance(expected, int) else expected + 1
                self.assertTrue(validate_p29_contract(MODULE, wrong))

        with tempfile.TemporaryDirectory() as temporary:
            module_dir = Path(temporary)
            for name in ARTIFACTS:
                (module_dir / name).write_text("content", encoding="utf-8")
            (module_dir / "experiment.m").unlink()
            (module_dir / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p29_contract(module_dir, self.manifest)
            self.assertIn("P29 missing experiment.m", errors)
            self.assertIn("P29 empty lesson.md", errors)

    def test_controls_are_finite_canonical_and_resource_bounded(self):
        self.assertEqual(parse_matlab_controls(self.experiment), canonical_controls())
        self.assertEqual(validate_matlab_source_contract(self.experiment), [])
        validate_controls()
        validate_controls(
            transmit_power_w=50e3,
            transmit_gain_dbi=34.0,
            receive_gain_dbi=36.0,
            carrier_frequency_hz=3e9,
            target_rcs_m2=2.0,
            system_loss_db=0.0,
            input_reference_temperature_k=300.0,
            receiver_bandwidth_hz=2e6,
            noise_figure_db=0.0,
            required_snr_db=0.0,
        )
        malformed = (
            {"random_seed": True},
            {"speed_of_light_mps": float("nan")},
            {"boltzmann_j_per_k": 0.0},
            {"transmit_power_w": float("inf")},
            {"transmit_gain_dbi": True},
            {"carrier_frequency_hz": 10e9 + 1j},
            {"target_rcs_m2": "large"},
            {"system_loss_db": -1.0},
            {"range_km": canonical_controls()["range_km"][:-1]},
            {"range_km": (1.0, float("nan"))},
            {"rcs_sweep_m2": (0.1, 0.0, 10.0)},
            {"frequency_sweep_ghz": (3.0, 10.0, 31.0)},
            {"transmit_power_sweep_kw": (25.0, 100.0)},
            {"noise_sample_count": 4095},
            {"max_range_points": 238},
            {"max_rcs_cases": 2},
            {"max_frequency_cases": 2},
            {"max_transmit_power_cases": 2},
            {"max_noise_samples": 4095},
            {"max_figure_groups": 3},
            {"max_stored_numeric_values": 39999},
        )
        for override in malformed:
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_controls(**override)
        with self.assertRaises(ValueError):
            validate_controls(unapproved_control=1)

        resource_cases = []
        for name, value in (
            ("max_range_points", 238),
            ("max_rcs_cases", 2),
            ("max_frequency_cases", 2),
            ("max_transmit_power_cases", 2),
            ("max_noise_samples", 4095),
            ("max_stored_numeric_values", 38000),
        ):
            controls = canonical_controls()
            controls[name] = value
            resource_cases.append(controls)
        for controls in resource_cases:
            with self.subTest(resource_controls=controls), self.assertRaises(ValueError):
                validate_resource_bounds(controls)

    def test_source_contract_rejects_control_equation_and_overwrite_mutations(self):
        mutations = (
            self.experiment.replace("transmit_power_w = 100e3;", "transmit_power_w = 50e3;", 1),
            self.experiment.replace("transmit_power_w = 100e3;", "transmit_power_w = true;", 1),
            self.experiment.replace(
                "((4*pi)^3*range_m.^4*system_loss_linear);",
                "((4*pi)^3*range_m.^2*system_loss_linear);",
                1,
            ),
            self.experiment.replace(
                "radar_equation_numerator = transmit_power_w*transmit_gain_linear* ...\n"
                "    receive_gain_linear*wavelength_m^2*target_rcs_m2;",
                "radar_equation_numerator = transmit_power_w*transmit_gain_linear* ...\n"
                "    wavelength_m^2*target_rcs_m2;",
                1,
            ),
            self.experiment.replace(
                "noise_power_w = boltzmann_j_per_k*input_reference_temperature_k*",
                "noise_power_w = boltzmann_j_per_k*input_reference_temperature_k^2*",
                1,
            ),
            self.experiment.replace(
                "speed_of_light_mps = 299792458;",
                "speed_of_light_mps = 299792458;\nspeed_of_light_mps = 3e8;",
                1,
            ),
            self.experiment.replace(
                "noise_factor_linear = 10^(noise_figure_db/10);",
                "noise_factor_linear = 10^(noise_figure_db/20);",
                1,
            ),
            self.experiment.replace(
                "sweep_frequency_hz = frequency_sweep_ghz(frequency_index)*1e9;",
                "sweep_frequency_hz = frequency_sweep_ghz(frequency_index)*1e6;",
                1,
            ),
            self.experiment.replace(
                "sweep_transmit_power_w = transmit_power_sweep_kw(power_index)*1e3;",
                "sweep_transmit_power_w = transmit_power_sweep_kw(power_index)*1e6;",
                1,
            ),
        )
        for mutated in mutations:
            with self.subTest():
                self.assertTrue(validate_matlab_source_contract(mutated))

        varied_controls = parse_matlab_controls(mutations[0])
        varied_model = deterministic_model(varied_controls)
        self.assertAlmostEqual(
            varied_model["powers_w"][0] / self.model["powers_w"][0],
            0.5,
            places=12,
        )

    def test_range_equation_oracle_proves_fourth_power_and_unit_conversions(self):
        model = self.model
        self.assertTrue(all(value > 0 and math.isfinite(value) for value in model["powers_w"]))
        self.assertTrue(all(left > right for left, right in zip(model["powers_w"], model["powers_w"][1:])))
        index_10 = canonical_controls()["range_km"].index(10.0)
        index_100 = canonical_controls()["range_km"].index(100.0)
        self.assertAlmostEqual(model["powers_dbm"][index_100] - model["powers_dbm"][index_10], -40.0, places=11)
        p40 = received_power_w(40e3, **model["kwargs"])
        p80 = received_power_w(80e3, **model["kwargs"])
        self.assertAlmostEqual(p40 / p80, 16.0, places=12)
        self.assertAlmostEqual(10 * math.log10(p40 / p80), 10 * math.log10(16), places=12)
        self.assertAlmostEqual(watts_to_dbw(p40) + 30, 10 * math.log10(p40 / 1e-3), places=12)
        for malformed in (0.0, -1.0, float("nan"), float("inf"), True):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                received_power_w(malformed, **model["kwargs"])
            with self.assertRaises(ValueError):
                watts_to_dbw(malformed)

    def test_noise_threshold_margin_and_seeded_measurement_are_consistent(self):
        controls = canonical_controls()
        model = self.model
        expected_noise = (
            controls["boltzmann_j_per_k"]
            * controls["input_reference_temperature_k"]
            * controls["receiver_bandwidth_hz"]
            * 10 ** (controls["noise_figure_db"] / 10)
        )
        self.assertEqual(model["noise_w"], expected_noise)
        self.assertAlmostEqual(model["threshold_w"] / model["noise_w"], 10 ** 1.3, places=12)
        self.assertLess(abs(model["measured_noise_w"] / model["noise_w"] - 1), 0.1)
        self.assertEqual(deterministic_model()["noise_i"], model["noise_i"])
        self.assertEqual(deterministic_model()["noise_q"], model["noise_q"])
        self.assertGreater(model["max_range_km"], 1.0)
        self.assertLess(model["max_range_km"], 120.0)
        below = [margin for range_m, margin in zip(model["ranges_m"], model["margins_db"]) if range_m / 1000 < model["max_range_km"]]
        above = [margin for range_m, margin in zip(model["ranges_m"], model["margins_db"]) if range_m / 1000 > model["max_range_km"]]
        self.assertTrue(below and all(value > 0 for value in below))
        self.assertTrue(above and all(value < 0 for value in above))

    def test_rcs_frequency_and_budget_sweeps_change_one_variable(self):
        controls = canonical_controls()
        model = self.model
        baseline = received_power_w(40e3, **model["kwargs"])
        rcs_ratios = []
        for rcs in controls["rcs_sweep_m2"]:
            varied = dict(model["kwargs"], target_rcs_m2=rcs)
            rcs_ratios.append(received_power_w(40e3, **varied) / baseline)
        self.assertEqual(rcs_ratios, [0.1, 1.0, 10.0])

        frequency_powers = []
        for frequency_ghz in controls["frequency_sweep_ghz"]:
            varied = dict(
                model["kwargs"],
                wavelength_m=controls["speed_of_light_mps"] / (frequency_ghz * 1e9),
            )
            frequency_powers.append(received_power_w(40e3, **varied))
        self.assertTrue(all(left > right for left, right in zip(frequency_powers, frequency_powers[1:])))

        expected_changes_db = (0.0, 10 * math.log10(2), 3.0, 3.0, 10 * math.log10(4), 10 * math.log10(2), 10 * math.log10(2))
        source_ratios = (1.0, 2.0, 10 ** 0.3, 10 ** 0.3, 4.0, 2.0, 2.0)
        for actual, expected in zip((10 * math.log10(value) for value in source_ratios), expected_changes_db):
            self.assertAlmostEqual(actual, expected, places=12)

    def test_power_sweep_range_recovery_obeys_fourth_root(self):
        controls = canonical_controls()
        model = self.model
        ranges = []
        for power_kw in controls["transmit_power_sweep_kw"]:
            varied = dict(model["kwargs"], transmit_power_w=power_kw * 1000)
            numerator = (
                varied["transmit_power_w"]
                * varied["transmit_gain_linear"]
                * varied["receive_gain_linear"]
                * varied["wavelength_m"] ** 2
                * varied["target_rcs_m2"]
            )
            ranges.append((numerator / ((4 * math.pi) ** 3 * varied["system_loss_linear"] * model["threshold_w"])) ** 0.25 / 1000)
        self.assertTrue(all(left < right for left, right in zip(ranges, ranges[1:])))
        self.assertAlmostEqual(ranges[2] / ranges[1], 4 ** 0.25, places=12)
        self.assertAlmostEqual(16 ** 0.25, 2.0, places=12)

    def test_double_range_loss_is_recovered_by_power_or_antenna_gain(self):
        model = self.model
        baseline = received_power_w(40e3, **model["kwargs"])
        recovery_cases = (
            dict(model["kwargs"], transmit_power_w=16 * model["kwargs"]["transmit_power_w"]),
            dict(model["kwargs"], transmit_gain_linear=16 * model["kwargs"]["transmit_gain_linear"]),
            dict(
                model["kwargs"],
                transmit_gain_linear=4 * model["kwargs"]["transmit_gain_linear"],
                receive_gain_linear=4 * model["kwargs"]["receive_gain_linear"],
            ),
        )
        for varied in recovery_cases:
            with self.subTest(varied=varied):
                self.assertAlmostEqual(
                    received_power_w(80e3, **varied) / baseline,
                    1.0,
                    places=12,
                )
        self.assertAlmostEqual(10 * math.log10(16), 12.041199826559248, places=12)
        self.assertAlmostEqual(10 * math.log10(4), 6.020599913279624, places=12)
        for marker in (
            "required_single_gain_multiplier_for_double_range",
            "required_each_reciprocal_gain_multiplier_for_double_range",
            "double_range_recovered_power_w",
            "all(abs(double_range_recovery_power_ratio-1) < 1e-12)",
            "'required_combined_antenna_gain_db'",
            "'required_each_reciprocal_gain_db'",
            "'recovery_power_ratio'",
        ):
            self.assertIn(marker, self.experiment)

    def test_broken_case_has_wrong_slope_and_recovery_is_independent(self):
        controls = canonical_controls()
        model = self.model
        ranges_km = controls["range_km"]
        reference_index = ranges_km.index(controls["reference_range_km"])
        anchor = model["powers_w"][reference_index]
        broken = [anchor * (controls["reference_range_km"] / value) ** 2 for value in ranges_km]
        index_10 = ranges_km.index(10.0)
        index_100 = ranges_km.index(100.0)
        broken_change = watts_to_dbw(broken[index_100]) - watts_to_dbw(broken[index_10])
        correct_change = model["powers_dbm"][index_100] - model["powers_dbm"][index_10]
        self.assertAlmostEqual(broken_change, -20.0, places=11)
        self.assertAlmostEqual(correct_change, -40.0, places=11)
        self.assertEqual(broken[reference_index], model["powers_w"][reference_index])
        self.assertNotEqual(broken, model["powers_w"])

        recovery_body = self.experiment.split(
            "%% Recovery: restore both spreading trips and reproduce the private seed", 1
        )[1].split("%% Retained results for guided inspection", 1)[0]
        self.assertNotIn("recovered_received_power_w = received_power_w", recovery_body)
        for marker in (
            "range_m.^4",
            "recovery_stream = RandStream('mt19937ar', 'Seed', random_seed)",
            "randn(recovery_stream, 1, noise_sample_count)",
            "isequal(recovered_received_power_w, received_power_w)",
        ):
            self.assertIn(marker, recovery_body)

    def test_source_binds_equations_seed_sweeps_failure_and_retained_metrics(self):
        markers = (
            "Pr = Pt*Gt*Gr*lambda^2*sigma / ((4*pi)^3*R^4*L)",
            "received_power_w = radar_equation_numerator ./",
            "((4*pi)^3*range_m.^4*system_loss_linear)",
            "noise_power_w = boltzmann_j_per_k*input_reference_temperature_k*",
            "detection_margin_db = received_power_dbm-detection_threshold_dbm",
            "received_power_dbw = 10*log10(received_power_w)",
            "received_power_dbm = received_power_dbw + 30",
            "%% Sweep 1: target RCS and carrier frequency, one at a time",
            "%% Sweep 2: transmit power changes margin, but range grows by a fourth root",
            "case_transmit_power_w = transmit_power_w*[1 2 1 1 1 1 1]",
            "case_transmit_gain_linear =",
            "case_receive_gain_linear =",
            "case_wavelength_m = wavelength_m*[1 1 1 1 2 1 1]",
            "case_system_loss_linear = system_loss_linear*[1 1 1 1 1 0.5 1]",
            "case_target_rcs_m2 = target_rcs_m2*[1 1 1 1 1 1 2]",
            "one_at_a_time_received_power_w(case_index) = case_numerator/(",
            "one_at_a_time_received_power_w/one_at_a_time_received_power_w(1)",
            "broken_received_power_w = received_power_w(reference_index)",
            "range_m.^2",
            "broken_model_valid = false",
            "'required_power_multiplier_at_reference'",
            "'required_power_multiplier'",
            "'model_valid'",
            "'exact_match'",
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.experiment)
        self.assertEqual(self.experiment.count("RandStream('mt19937ar', 'Seed', random_seed)"), 2)
        self.assertEqual(len(re.findall(r"\brandn\s*\(", self.experiment)), 4)

    def test_validation_precedes_work_and_resources_are_fixed(self):
        marker = self.experiment.index("% Validation succeeded:")
        for work in ("RandStream(", "randn(", "zeros(", "figure(", "findall("):
            with self.subTest(work=work):
                self.assertGreater(self.experiment.index(work), marker)
        resources = (
            "max_range_points = 239",
            "max_rcs_cases = 3",
            "max_frequency_cases = 3",
            "max_transmit_power_cases = 3",
            "max_noise_samples = 4096",
            "max_figure_groups = 4",
            "max_stored_numeric_values = 40000",
            "estimated_stored_numeric_values <= max_stored_numeric_values",
        )
        for resource in resources:
            self.assertIn(resource, self.experiment)
        self.assertNotRegex(
            self.experiment,
            r"(?m)^\s*(?:while|parfor)\b|^\s*(?:timer|pause)\s*\(",
        )

    def test_plots_metrics_and_units_are_purposeful(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 4)
        labels = (
            "Target range (km)",
            "Target range (km, logarithmic axis)",
            "Received echo power (dBm)",
            "Power at receiver input (dBm)",
            "Detection margin (dB)",
            "Received-power change at 40 km (dB)",
            "Noise floor kTBF",
            "Detection threshold",
            "Broken R^{-2}",
            "Recovered R^{-4}",
        )
        for label in labels:
            self.assertIn(label, self.experiment)
        for metric in (
            "received_power_dbm",
            "noise_power_dbm",
            "detection_threshold_dbm",
            "detection_margin_db",
            "max_detectable_range_km",
            "penalty_db",
        ):
            self.assertIn(f"'{metric}'", self.experiment)

    def test_docs_are_concept_first_and_cover_limits_dependencies_and_invariants(self):
        lesson = self.text["lesson.md"]
        walkthrough = self.text["walkthrough.md"]
        checks = self.text["checks.md"]
        lesson_words = " ".join(lesson.lower().split())
        for marker in (
            "Physical model",
            "Why range is so expensive",
            "Receiver noise and detection margin",
            "Assumptions and limiting cases",
            "Common interpretation mistakes",
            "Dependencies and DSP/radar connection",
        ):
            self.assertIn(marker, lesson)
        for marker in (
            "P27",
            "P28",
            "free-space far-field",
            "matched polarization",
            "fixed physical antenna apertures",
            "probability of detection",
            "+6.02 dB",
            "gain product",
            "dBW",
            "dBm",
        ):
            self.assertIn(marker.lower(), lesson_words)
        for marker in (
            "Baseline observation",
            "Sweep one variable: target RCS only",
            "Sweep one variable: frequency only",
            "Sweep one variable: transmit power only",
            "Intentionally broken case",
            "Recover and connect the concept",
        ):
            self.assertIn(marker.lower(), walkthrough.lower())
        for marker in (
            "Observation checks",
            "Prediction checks",
            "Interpretation checks",
            "Failure and recovery checks",
            "Completion checklist",
            "Short teach-back rubric",
        ):
            self.assertIn(marker, checks)

    def test_placeholder_black_box_and_external_io_regressions(self):
        combined = "\n".join(self.text.values())
        self.assertNotIn("TODO", combined)
        self.assertNotRegex(combined, r"(?i)placeholder|implementation batch `P29` is pending")
        forbidden_calls = (
            r"\bphased\.",
            r"\bradar\.",
            r"\bawgn\s*\(",
            r"\brng\s*\(",
            r"\bclose\s+all\b",
            r"\bsave\s*\(",
            r"\bload\s*\(",
            r"\bfopen\s*\(",
            r"\bweb(read|write|save)\s*\(",
            r"\bsystem\s*\(",
            r"\bunix\s*\(",
        )
        for pattern in forbidden_calls:
            with self.subTest(pattern=pattern):
                self.assertNotRegex(self.experiment, pattern)

    def test_cancellation_recovery_isolation_compatibility_and_rollback_are_explicit(self):
        operational = self.text["walkthrough.md"] + self.text["checks.md"]
        for marker in (
            "Ctrl+C",
            "private seed",
            "global random stream",
            "figures tagged `P29`",
            ".learning/",
            "worker",
            "timer",
            "external transaction",
            "base MATLAB",
            "rollback",
            "scaffolded",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), operational.lower())
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P29'))", self.experiment)

    def test_public_catalogs_and_isolated_learner_entry_with_timeout(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 29 begins Phase 4", root_readme)
        self.assertIn("Project 29 follows P28", start_here)
        self.assertRegex(module_index, r"\| \[P29\].*\| implemented \|")

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
            shutil.copy2(MODULE / "README.md", fixture_readme)
            environment = os.environ.copy()
            environment["HOME"] = temporary
            process = subprocess.run(
                [str(fixture_cli), "start", "29"],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("P29 — Build a Radar Power-Budget Experiment", process.stdout)
            self.assertIn("status: implemented", process.stdout)
            self.assertIn("Tutor entry", process.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_retained_evidence_is_honest_and_complete(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P29-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        for marker in (
            "Acceptance mapping",
            "Figure and metric inventory",
            "Independent oracle results",
            "Exact commands and results",
            "Changed and preserved invariants",
            "Residual risks and unperformed validation",
            "Rollback and recovery",
            "Validation class",
            "MATLAB runtime status",
            "Toolboxes",
            "MATLAB",
            "did not run",
        ):
            self.assertIn(marker, evidence)
        for command in (
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
        ):
            self.assertIn(command, evidence)
        for outcome in (
            "PASS — Ran 18 tests",
            "PASS — Curriculum validation passed: 84 modules, 29 implemented.",
            "confirmed Ran 537 tests",
            "Ran 537 tests",
        ):
            self.assertIn(outcome, evidence)
        for units_or_metrics in (
            "dBm",
            "dBW",
            "W",
            "km",
            "GHz",
            "m^2",
            "dB/decade",
            "38,448",
        ):
            self.assertIn(units_or_metrics, evidence)
        self.assertGreaterEqual(evidence.count("| PASS |"), 8)
        self.assertNotIn("PENDING —", evidence)


if __name__ == "__main__":
    unittest.main()
