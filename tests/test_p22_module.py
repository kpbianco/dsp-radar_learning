from __future__ import annotations

import cmath
import copy
import json
import math
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/22-relate-fm-deviation-to-bandwidth"
QUESTION = "How does instantaneous frequency motion create an FM spectrum?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
EXPECTED_IDENTITY = {
    "number": 22,
    "id": "P22",
    "title": "Relate FM Deviation to Bandwidth",
    "guiding_question": QUESTION,
    "phase": 3,
    "phase_title": "Modulation, Channels, and Statistical Estimation",
    "slug": "relate-fm-deviation-to-bandwidth",
    "folder": "modules/22-relate-fm-deviation-to-bandwidth",
    "status": "implemented",
    "implementation_batch": "P22",
}


def validate_p22_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P22 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P22 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    matches = [
        entry for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P22"
    ]
    if len(matches) != 1:
        return errors + [f"expected one P22 manifest entry, found {len(matches)}"]
    entry = matches[0]
    for key, expected in EXPECTED_IDENTITY.items():
        if entry.get(key) != expected:
            errors.append(f"P22 {key} must be {expected!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def canonical_controls() -> dict:
    return {
        "random_seed": 1022,
        "fs_hz": 24000.0,
        "duration_s": 0.20,
        "sample_count": 4800,
        "carrier_frequency_hz": 3000.0,
        "carrier_amplitude_v": 1.0,
        "message_frequency_hz": 100.0,
        "frequency_deviation_hz": 400.0,
        "receiver_noise_rms_v": 0.002,
        "occupied_power_fraction": 0.98,
        "deviation_sweep_hz": (50.0, 200.0, 400.0, 800.0),
        "message_frequency_sweep_hz": (50.0, 100.0, 200.0, 400.0),
        "broken_carrier_frequency_hz": 8000.0,
        "broken_frequency_deviation_hz": 5000.0,
        "recovery_guard_hz": 500.0,
        "recovery_fs_hz": 30000.0,
        "recovery_sample_count": 6000,
        "time_view_duration_s": 0.020,
        "max_sample_count": 6000,
        "max_sweep_cases": 4,
        "max_figure_groups": 5,
        "max_stored_numeric_values": 650000,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    vectors = {
        "deviation_sweep_hz": (50.0, 200.0, 400.0, 800.0),
        "message_frequency_sweep_hz": (50.0, 100.0, 200.0, 400.0),
    }
    for name, expected in vectors.items():
        value = controls[name]
        if not isinstance(value, (tuple, list)):
            raise ValueError(f"{name} must be a bounded numeric vector")
        if not all(_finite_real(item) for item in value):
            raise ValueError(f"{name} must contain finite real values")
        if tuple(value) != expected:
            raise ValueError(f"{name} must equal its canonical vector")

    for name, expected in canonical_controls().items():
        if name in vectors:
            continue
        value = controls[name]
        if not _finite_real(value) or value != expected:
            raise ValueError(f"{name} must equal its finite canonical scalar")

    if controls["carrier_frequency_hz"] - max(controls["deviation_sweep_hz"]) <= 0:
        raise ValueError("valid sweep frequencies must stay positive")
    if (
        controls["carrier_frequency_hz"]
        + max(controls["deviation_sweep_hz"])
        + max(controls["message_frequency_sweep_hz"])
        >= controls["fs_hz"] / 2
    ):
        raise ValueError("valid sweeps need Nyquist guard")
    recovery_target_upper_hz = (
        controls["broken_carrier_frequency_hz"]
        + controls["broken_frequency_deviation_hz"]
        + controls["message_frequency_hz"]
    )
    if (
        controls["recovery_fs_hz"] / 2
        < recovery_target_upper_hz + controls["recovery_guard_hz"]
    ):
        raise ValueError("recovery must guard the Carson occupied-band target")


def fm_signal(
    *, fs_hz: float = 2400.0, sample_count: int = 480,
    carrier_hz: float = 300.0, message_hz: float = 10.0,
    deviation_hz: float = 40.0, amplitude: float = 1.0,
) -> tuple[list[complex], list[float]]:
    beta = deviation_hz / message_hz
    phasor: list[complex] = []
    instantaneous_frequency: list[float] = []
    for index in range(sample_count):
        time_s = index / fs_hz
        phase = (
            2 * math.pi * carrier_hz * time_s
            + beta * math.sin(2 * math.pi * message_hz * time_s)
        )
        phasor.append(amplitude * cmath.exp(1j * phase))
        instantaneous_frequency.append(
            carrier_hz + deviation_hz * math.cos(2 * math.pi * message_hz * time_s)
        )
    return phasor, instantaneous_frequency


def one_sided_amplitude(signal: list[float], frequency_hz: float, fs_hz: float) -> float:
    coefficient = sum(
        value * cmath.exp(-2j * math.pi * frequency_hz * index / fs_hz)
        for index, value in enumerate(signal)
    )
    return 2 * abs(coefficient) / len(signal)


def occupied_line_order(
    signal: list[float], *, fs_hz: float, carrier_hz: float,
    message_hz: float, fraction: float = 0.98,
) -> tuple[int, float]:
    maximum_order = int(min(carrier_hz, fs_hz / 2 - carrier_hz) // message_hz)
    powers = {
        order: one_sided_amplitude(
            signal, carrier_hz + order * message_hz, fs_hz
        ) ** 2
        for order in range(-maximum_order, maximum_order + 1)
    }
    total = sum(powers.values())
    for order in range(maximum_order + 1):
        retained = sum(power for key, power in powers.items() if abs(key) <= order)
        if retained / total >= fraction:
            return order, retained / total
    raise AssertionError("bounded line-power search did not converge")


class P22ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.experiment = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        cls.all_content = "\n".join(
            (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        )

    def test_artifacts_manifest_identity_dependency_and_public_catalogs(self):
        self.assertEqual(validate_p22_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            path = MODULE / name
            self.assertGreater(path.stat().st_size, 100)
            self.assertIn(QUESTION, path.read_text(encoding="utf-8"))
        prerequisite = next(
            entry for entry in self.manifest["modules"] if entry["id"] == "P21"
        )
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertIn("P21", self.readme)
        self.assertIn("P21", self.lesson)
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertRegex(module_index, r"\| \[P22\].*\| implemented \|")

    def test_contract_rejects_missing_empty_duplicate_nonlist_and_wrong_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "experiment.m").unlink()
            (fixture / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p22_contract(fixture, self.manifest)
            self.assertIn("P22 missing experiment.m", errors)
            self.assertIn("P22 empty checks.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][21]))
        self.assertIn(
            "expected one P22 manifest entry, found 2",
            validate_p22_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p22_contract(MODULE, {"modules": "P22"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][21]["guiding_question"] = "generic"
        malformed["modules"][21]["status"] = "scaffolded"
        errors = validate_p22_contract(MODULE, malformed)
        self.assertIn(f"P22 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P22 status must be 'implemented'", errors)

    def test_deterministic_visible_fm_controls_and_private_noise(self):
        for marker in (
            "random_seed = 1022;", "fs_hz = 24000;", "duration_s = 0.20;",
            "carrier_frequency_hz = 3000;", "message_frequency_hz = 100;",
            "frequency_deviation_hz = 400;", "occupied_power_fraction = 0.98;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "receiver_noise_v = receiver_noise_rms_v* ...\n"
            "    randn(private_stream, 1, sample_count);",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_phase_law_has_constant_magnitude_and_expected_frequency_motion(self):
        phasor, instantaneous_frequency = fm_signal()
        self.assertLess(max(abs(abs(value) - 1.0) for value in phasor), 1e-15)
        self.assertAlmostEqual(min(instantaneous_frequency), 260.0, places=12)
        self.assertAlmostEqual(max(instantaneous_frequency), 340.0, places=12)
        for formula in (
            "modulation_index = frequency_deviation_hz/message_frequency_hz;",
            "instantaneous_phase_rad = 2*pi*carrier_frequency_hz*time_s + ...",
            "frequency_deviation_hz*message;",
            "fm_phasor_v = carrier_amplitude_v*exp(1j*instantaneous_phase_rad);",
            "fs_hz*diff(unwrap(angle(fm_phasor_v)))/(2*pi)",
        ):
            self.assertIn(formula, self.experiment)

    def test_beta_four_creates_multiple_bessel_like_lines_and_carson_width(self):
        phasor, _ = fm_signal()
        signal = [value.real for value in phasor]
        order, retained_fraction = occupied_line_order(
            signal, fs_hz=2400.0, carrier_hz=300.0, message_hz=10.0
        )
        self.assertEqual(order, 5)
        self.assertGreaterEqual(retained_fraction, 0.98)
        self.assertEqual(2 * order * 10.0, 2 * (40.0 + 10.0))
        amplitudes = [
            one_sided_amplitude(signal, 300 + n * 10, 2400.0)
            for n in range(-5, 6)
        ]
        self.assertGreater(sum(value > 0.05 for value in amplitudes), 7)
        self.assertIn("line_power_v2 = clean_amplitude_v(line_indices).^2;", self.experiment)
        self.assertIn(
            "carson_bandwidth_hz = 2*(frequency_deviation_hz+message_frequency_hz);",
            self.experiment,
        )

    def test_two_one_variable_sweeps_are_bounded_and_physically_tied(self):
        deviation = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        message = self.experiment.split("%% Sweep 2", 1)[1].split(
            "%% Broken case", 1
        )[0]
        self.assertEqual(deviation.count("for sweep_index ="), 1)
        self.assertEqual(message.count("for sweep_index ="), 1)
        self.assertIn(
            "case_frequency_deviation_hz = deviation_sweep_hz(sweep_index);",
            deviation,
        )
        self.assertNotIn("case_message_frequency_hz", deviation)
        self.assertIn(
            "case_message_frequency_hz = message_frequency_sweep_hz(sweep_index);",
            message,
        )
        self.assertNotIn("case_frequency_deviation_hz", message)
        self.assertIn("deviation_sweep_hz = [50 200 400 800];", self.experiment)
        self.assertIn("message_frequency_sweep_hz = [50 100 200 400];", self.experiment)

        deviation_widths = []
        for deviation_hz in (5.0, 20.0, 40.0, 80.0):
            phasor, _ = fm_signal(message_hz=10.0, deviation_hz=deviation_hz)
            order, _ = occupied_line_order(
                [value.real for value in phasor], fs_hz=2400.0,
                carrier_hz=300.0, message_hz=10.0,
            )
            deviation_widths.append(2 * order * 10.0)
        self.assertEqual(deviation_widths, sorted(deviation_widths))

        message_widths = []
        for message_hz in (5.0, 10.0, 20.0, 40.0):
            phasor, _ = fm_signal(message_hz=message_hz, deviation_hz=40.0)
            order, _ = occupied_line_order(
                [value.real for value in phasor], fs_hz=2400.0,
                carrier_hz=300.0, message_hz=message_hz,
            )
            message_widths.append(2 * order * message_hz)
        self.assertEqual(message_widths, [90.0, 100.0, 120.0, 160.0])
        self.assertIn(
            "isequal(deviation_sweep_occupied_bandwidth_hz, ...\n"
            "    [200 600 1000 1800])",
            self.experiment,
        )
        self.assertIn(
            "case_modulation_index*sin(2*pi*case_message_frequency_hz*time_s)",
            message,
        )

    def test_broken_case_exposes_aliasing_and_calculates_recovery(self):
        broken_maximum_hz = 8000.0 + 5000.0
        broken_carson_upper_hz = broken_maximum_hz + 100.0
        nyquist_hz = 24000.0 / 2
        minimum_recovery_fs_hz = 2 * (broken_carson_upper_hz + 500.0)
        self.assertGreater(broken_maximum_hz, nyquist_hz)
        self.assertEqual(minimum_recovery_fs_hz, 27200.0)
        broken_phasor, broken_intended = fm_signal(
            fs_hz=2400.0, sample_count=480, carrier_hz=800.0,
            message_hz=10.0, deviation_hz=500.0,
        )
        broken_observed = [
            cmath.phase(current * previous.conjugate()) * 2400.0 / (2 * math.pi)
            for previous, current in zip(broken_phasor, broken_phasor[1:])
        ]
        broken_alias_fraction = sum(
            abs(observed - intended) > 2400.0 / 4
            for observed, intended in zip(broken_observed, broken_intended[1:])
        ) / len(broken_observed)
        self.assertGreater(broken_alias_fraction, 0.15)

        recovery_phasor, recovery_intended = fm_signal(
            fs_hz=3000.0, sample_count=600, carrier_hz=800.0,
            message_hz=10.0, deviation_hz=500.0,
        )
        recovery_observed = [
            cmath.phase(current * previous.conjugate()) * 3000.0 / (2 * math.pi)
            for previous, current in zip(recovery_phasor, recovery_phasor[1:])
        ]
        self.assertLess(
            max(abs(observed - intended) for observed, intended in zip(
                recovery_observed, recovery_intended[1:]
            )),
            6.0,
        )
        broken = self.experiment.split("%% Broken case", 1)[1].split(
            "%% Retained workspace results", 1
        )[0]
        for marker in (
            "broken_nyquist_margin_hz", "broken_alias_sample_fraction",
            "broken_observed_frequency_hz", "broken_carson_bandwidth_hz",
            "broken_carson_upper_frequency_hz", "minimum_recovery_fs_hz",
            "recovery_fs_hz", "recovery_observed_frequency_hz",
            "recovery_phase_slope_margin_hz", "recovery_frequency_error_hz",
            "fftshift(fft(broken_phasor_v))",
        ):
            self.assertIn(marker, broken)
        self.assertIn("occupied-bandwidth reading is invalid", broken)
        self.assertIn("broken_alias_sample_fraction > 0.15", broken)

    def test_recovery_rate_preserves_the_target_occupied_cluster(self):
        recovery_phasor, _ = fm_signal(
            fs_hz=30000.0, sample_count=6000, carrier_hz=8000.0,
            message_hz=100.0, deviation_hz=5000.0,
        )
        occupied_order, retained_fraction = occupied_line_order(
            [value.real for value in recovery_phasor], fs_hz=30000.0,
            carrier_hz=8000.0, message_hz=100.0,
        )
        occupied_bandwidth_hz = 2 * occupied_order * 100.0
        occupied_upper_frequency_hz = 8000.0 + occupied_bandwidth_hz / 2

        self.assertEqual(occupied_order, 51)
        self.assertGreaterEqual(retained_fraction, 0.98)
        self.assertEqual(occupied_bandwidth_hz, 10200.0)
        self.assertEqual(occupied_upper_frequency_hz, 13100.0)
        self.assertEqual(30000.0 / 2 - occupied_upper_frequency_hz, 1900.0)

        broken = self.experiment.split("%% Broken case", 1)[1].split(
            "%% Retained workspace results", 1
        )[0]
        for source_contract in (
            "broken_carson_bandwidth_hz = 2*(broken_frequency_deviation_hz + ...",
            "minimum_recovery_fs_hz = 2*(broken_carson_upper_frequency_hz + ...",
            "recovery_occupied_sideband_order == 51",
            "recovery_occupied_bandwidth_hz == broken_carson_bandwidth_hz",
            "recovery_occupied_margin_hz >= recovery_guard_hz",
        ):
            self.assertIn(source_contract, broken)

    def test_malformed_controls_and_resource_ceilings(self):
        invalid = (
            ("random_seed", True), ("fs_hz", math.nan),
            ("duration_s", math.inf), ("sample_count", 4801),
            ("carrier_frequency_hz", complex(3000, 1)),
            ("carrier_amplitude_v", 0.0), ("message_frequency_hz", -100.0),
            ("frequency_deviation_hz", 0.0), ("receiver_noise_rms_v", -0.002),
            ("occupied_power_fraction", 1.0),
            ("deviation_sweep_hz", (50.0, 200.0, math.nan, 800.0)),
            ("message_frequency_sweep_hz", (50.0, 100.0, 200.0)),
            ("broken_carrier_frequency_hz", 3000.0),
            ("broken_frequency_deviation_hz", 400.0),
            ("recovery_guard_hz", 0.0), ("recovery_fs_hz", 24000.0),
            ("recovery_sample_count", 4800), ("time_view_duration_s", 0.040),
            ("max_sample_count", 12000), ("max_sweep_cases", 5),
            ("max_figure_groups", 6), ("max_stored_numeric_values", 1300000),
        )
        for key, value in invalid:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_controls(**{key: value})
        with self.assertRaises(ValueError):
            validate_controls(unknown_control=1)

    def test_matlab_guards_reject_logical_controls_before_signal_work(self):
        validation = self.experiment.split("% Validation succeeded:", 1)[0]
        for control in canonical_controls():
            self.assertIn(f"~islogical({control})", validation, control)

    def test_validation_precedes_random_allocation_fft_cleanup_and_figures(self):
        validation_end = self.experiment.index("% Validation succeeded:")
        for marker in (
            "RandStream(", "time_s = (0:sample_count-1)/fs_hz;", "fft(",
            "close(findall(", "figure('Name'",
        ):
            self.assertGreater(self.experiment.index(marker), validation_end, marker)

    def test_plot_metric_unit_and_retained_result_inventory(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 5)
        self.assertEqual(self.experiment.count("'Tag', 'P22'"), 6)
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P22'));", self.experiment)
        for unit in (
            "Time (ms)", "Instantaneous frequency (Hz)", "Phasor magnitude (V)",
            "RF voltage (V)", "RF frequency (Hz)", "Amplitude (dB re 1 V)",
            "Sampled signed frequency (Hz)",
        ):
            self.assertIn(unit, self.experiment)
        for result in (
            "instantaneous_phase_rad", "instantaneous_frequency_hz",
            "measured_frequency_hz", "received_amplitude_v",
            "occupied_bandwidth_hz", "carson_bandwidth_hz",
            "deviation_sweep_occupied_bandwidth_hz",
            "message_sweep_occupied_bandwidth_hz", "broken_nyquist_margin_hz",
            "broken_alias_sample_fraction", "broken_carson_bandwidth_hz",
            "broken_carson_upper_frequency_hz", "minimum_recovery_fs_hz",
            "recovery_observed_frequency_hz", "recovery_phase_slope_margin_hz",
            "recovery_occupied_sideband_order",
            "recovery_occupied_bandwidth_hz", "recovery_occupied_margin_hz",
            "recovery_frequency_error_hz",
        ):
            self.assertIn(f"results.{result}", self.experiment)

    def test_no_placeholder_unexplained_black_box_or_external_io(self):
        self.assertNotRegex(self.all_content, r"(?i)\bTODO\b|\bTBD\b|lorem ipsum")
        for call in (
            "fmmod(", "obw(", "bandwidth(", "pspectrum(", "hilbert(",
            "spectrogram(", "xline(", "yline(", "parfor ", "timer(",
            "webread(", "urlread(",
            "fopen(", "save(", "writetable(", "system(", "!",
        ):
            self.assertNotIn(call, self.experiment)
        self.assertIn("Base MATLAB only", self.experiment)
        self.assertIn("no modulation toolbox", self.readme.lower())

    def test_content_is_concept_first_complete_and_runtime_claim_boundary_is_honest(self):
        for phrase in (
            "phase slope", "Bessel-like", "Carson", "Nyquist", "constant",
        ):
            self.assertIn(phrase.lower(), self.lesson.lower())
        self.assertIn("Sweep 1", self.experiment)
        self.assertIn("Sweep 2", self.experiment)
        self.assertIn("Broken case", self.experiment)
        evidence = ROOT / "docs/evidence/P22-2026-08-02.md"
        self.assertTrue(evidence.is_file())
        evidence_text = evidence.read_text(encoding="utf-8")
        self.assertIn("MATLAB", evidence_text)
        self.assertIn("did not run", evidence_text.lower())
        self.assertIn("unperformed", evidence_text.lower())

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback(self):
        operational = "\n".join((self.walkthrough, self.checks))
        for phrase in (
            "Ctrl+C", "workspace variables", "full rerun", "private seed",
            "global random stream", ".learning/", "worker", "external transaction",
            "Rollback", "P21", "base MATLAB",
        ):
            self.assertIn(phrase.lower(), operational.lower())
        self.assertIn("cannot restore", operational.lower())
        self.assertIn("max_sample_count = 6000;", self.experiment)
        self.assertIn("max_sweep_cases = 4;", self.experiment)
        self.assertIn("max_figure_groups = 5;", self.experiment)
        self.assertIn("max_stored_numeric_values = 650000;", self.experiment)
        self.assertLess(
            self.experiment.index("results = struct();"),
            self.experiment.index("RandStream("),
        )


if __name__ == "__main__":
    unittest.main()
