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
MODULE = ROOT / "modules/17-perform-complex-downconversion-by-hand"
EVIDENCE = ROOT / "docs/evidence/P17-2026-08-02.md"
QUESTION = "How does multiplying by a complex oscillator move an RF/IF signal to baseband?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def validate_p17_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P17 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P17 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    entries = [
        entry
        for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P17"
    ]
    if len(entries) != 1:
        return errors + [f"expected one P17 manifest entry, found {len(entries)}"]

    expected = {
        "number": 17,
        "id": "P17",
        "title": "Perform Complex Downconversion by Hand",
        "guiding_question": QUESTION,
        "phase": 2,
        "phase_title": "Fourier, Spectral, and I/Q Intuition",
        "slug": "perform-complex-downconversion-by-hand",
        "folder": "modules/17-perform-complex-downconversion-by-hand",
        "status": "implemented",
        "implementation_batch": "P17",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P17 {key} must be {value!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_controls(**overrides: object) -> None:
    controls: dict[str, object] = {
        "random_seed": 1017,
        "fs_hz": 2048.0,
        "record_sample_count": 4096,
        "carrier_frequency_hz": 240.0,
        "carrier_amplitude_v": 1.0,
        "carrier_phase_rad": 0.35,
        "noise_rms_v": 0.002,
        "lo_frequency_hz": 240.0,
        "lo_phase_rad": 0.0,
        "lo_frequency_sweep_hz": (204.0, 240.0, 276.0),
        "lo_phase_sweep_rad": (0.0, math.pi / 2, math.pi),
        "broken_lo_frequency_hz": 216.0,
        "lowpass_cutoff_hz": 80.0,
        "lowpass_tap_count": 129,
        "evaluation_guard_sample_count": 192,
        "max_record_samples": 4096,
        "max_fft_length": 4096,
        "max_filter_taps": 129,
        "max_sweep_cases": 3,
        "max_stored_numeric_values": 180000,
        "max_figure_groups": 5,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    scalar_names = (
        "random_seed",
        "fs_hz",
        "record_sample_count",
        "carrier_frequency_hz",
        "carrier_amplitude_v",
        "carrier_phase_rad",
        "noise_rms_v",
        "lo_frequency_hz",
        "lo_phase_rad",
        "broken_lo_frequency_hz",
        "lowpass_cutoff_hz",
        "lowpass_tap_count",
        "evaluation_guard_sample_count",
    )
    if not all(_finite_real(controls[name]) for name in scalar_names):
        raise ValueError("scalar controls must be finite real nonlogical values")
    if (
        controls["random_seed"] != int(controls["random_seed"])
        or not 0 <= controls["random_seed"] <= 2**32 - 1
    ):
        raise ValueError("seed must be an unsigned 32-bit integer")
    if controls["fs_hz"] != 2048 or controls["record_sample_count"] != 4096:
        raise ValueError("canonical sample rate and record are required")
    if int(controls["record_sample_count"]) % 2:
        raise ValueError("record must be even")
    if controls["carrier_frequency_hz"] != 240:
        raise ValueError("canonical 240 Hz carrier required")
    if not 0 < controls["carrier_amplitude_v"] <= 2:
        raise ValueError("amplitude must be positive and bounded")
    if not 0 <= controls["noise_rms_v"] <= 0.01:
        raise ValueError("noise must be nonnegative and bounded")
    if controls["lowpass_tap_count"] != 129 or int(controls["lowpass_tap_count"]) % 2 == 0:
        raise ValueError("canonical odd FIR length required")
    if controls["evaluation_guard_sample_count"] != 192:
        raise ValueError("canonical guard required")
    if controls["lo_frequency_hz"] != controls["carrier_frequency_hz"]:
        raise ValueError("baseline LO must exactly match the carrier")

    frequency_sweep = controls["lo_frequency_sweep_hz"]
    phase_sweep = controls["lo_phase_sweep_rad"]
    if frequency_sweep != (204.0, 240.0, 276.0):
        raise ValueError("canonical LO-frequency sweep required")
    if phase_sweep != (0.0, math.pi / 2, math.pi):
        raise ValueError("canonical LO-phase sweep required")
    if controls["broken_lo_frequency_hz"] != 216:
        raise ValueError("canonical broken case required")

    all_los = (controls["lo_frequency_hz"], *frequency_sweep, controls["broken_lo_frequency_hz"])
    if any(not _finite_real(value) or value <= 0 for value in all_los):
        raise ValueError("LO frequencies must be finite and positive")
    if controls["carrier_frequency_hz"] + max(all_los) >= controls["fs_hz"] / 2:
        raise ValueError("sum image must remain below Nyquist")
    desired = [controls["carrier_frequency_hz"] - value for value in frequency_sweep]
    if max(abs(value) for value in desired) >= controls["lowpass_cutoff_hz"]:
        raise ValueError("LPF must retain sweep beats")
    if controls["lowpass_cutoff_hz"] >= (
        controls["carrier_frequency_hz"] + min(all_los)
    ) / 3:
        raise ValueError("LPF must remain separated from sum images")

    ceilings = {
        "max_record_samples": 4096,
        "max_fft_length": 4096,
        "max_filter_taps": 129,
        "max_sweep_cases": 3,
        "max_stored_numeric_values": 180000,
        "max_figure_groups": 5,
    }
    if any(controls[name] != expected for name, expected in ceilings.items()):
        raise ValueError("resource ceilings are fixed")


def dft(signal: list[complex]) -> list[complex]:
    count = len(signal)
    return [
        sum(
            sample * cmath.exp(-2j * math.pi * bin_index * index / count)
            for index, sample in enumerate(signal)
        )
        for bin_index in range(count)
    ]


def idft(spectrum: list[complex]) -> list[complex]:
    count = len(spectrum)
    return [
        sum(
            value * cmath.exp(2j * math.pi * bin_index * index / count)
            for bin_index, value in enumerate(spectrum)
        )
        / count
        for index in range(count)
    ]


def ideal_lowpass(signal: list[complex], cutoff_hz: float, fs_hz: float) -> list[complex]:
    spectrum = dft(signal)
    count = len(signal)
    kept: list[complex] = []
    for bin_index, value in enumerate(spectrum):
        frequency_hz = bin_index * fs_hz / count
        if frequency_hz >= fs_hz / 2:
            frequency_hz -= fs_hz
        kept.append(value if abs(frequency_hz) <= cutoff_hz else 0j)
    return idft(kept)


def projection(signal: list[complex], frequency_hz: float, fs_hz: float) -> complex:
    return sum(
        sample * cmath.exp(-2j * math.pi * frequency_hz * index / fs_hz)
        for index, sample in enumerate(signal)
    ) / len(signal)


def wrap_phase(value: float) -> float:
    return math.atan2(math.sin(value), math.cos(value))


def build_real_tone(
    *, fs_hz: float = 256.0, count: int = 256, frequency_hz: float = 48.0,
    amplitude_v: float = 1.0, phase_rad: float = 0.35,
) -> list[float]:
    return [
        amplitude_v * math.cos(2 * math.pi * frequency_hz * index / fs_hz + phase_rad)
        for index in range(count)
    ]


def mix(signal: list[float], frequency_hz: float, fs_hz: float, phase_rad: float = 0.0, sign: int = -1) -> list[complex]:
    return [
        sample * cmath.exp(sign * 1j * (2 * math.pi * frequency_hz * index / fs_hz + phase_rad))
        for index, sample in enumerate(signal)
    ]


def design_fir(tap_count: int = 129, fs_hz: float = 2048.0, cutoff_hz: float = 80.0) -> list[float]:
    if isinstance(tap_count, bool) or tap_count != 129 or tap_count % 2 == 0:
        raise ValueError("P17 uses the canonical odd 129-tap FIR")
    if not math.isfinite(fs_hz) or fs_hz <= 0:
        raise ValueError("sample rate must be finite and positive")
    if not math.isfinite(cutoff_hz) or not 0 < cutoff_hz < fs_hz / 2:
        raise ValueError("cutoff must lie between DC and Nyquist")
    half = (tap_count - 1) // 2
    coefficients: list[float] = []
    for tap, centered in enumerate(range(-half, half + 1)):
        ideal = (
            2 * cutoff_hz / fs_hz
            if centered == 0
            else math.sin(2 * math.pi * cutoff_hz * centered / fs_hz) / (math.pi * centered)
        )
        window = 0.54 - 0.46 * math.cos(2 * math.pi * tap / (tap_count - 1))
        coefficients.append(ideal * window)
    gain = sum(coefficients)
    return [coefficient / gain for coefficient in coefficients]


def fir_response(coefficients: list[float], frequency_hz: float, fs_hz: float) -> float:
    return abs(sum(
        coefficient * cmath.exp(-2j * math.pi * frequency_hz * tap / fs_hz)
        for tap, coefficient in enumerate(coefficients)
    ))


def apply_fir_and_remove_group_delay(
    signal: list[complex], coefficients: list[float]
) -> list[complex]:
    if len(coefficients) % 2 == 0:
        raise ValueError("linear-phase group-delay removal requires an odd FIR")
    full = [0j] * (len(signal) + len(coefficients) - 1)
    for sample_index, sample in enumerate(signal):
        for tap_index, coefficient in enumerate(coefficients):
            full[sample_index + tap_index] += sample * coefficient
    half = (len(coefficients) - 1) // 2
    return full[half:half + len(signal)]


def windowed_projection(
    signal: list[complex], frequency_hz: float, fs_hz: float, guard: int
) -> complex:
    indices = range(guard, len(signal) - guard)
    return sum(
        signal[index] * cmath.exp(-2j * math.pi * frequency_hz * index / fs_hz)
        for index in indices
    ) / (len(signal) - 2 * guard)


class P17ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.experiment = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        cls.all_content = "\n".join(
            (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        )

    def test_artifact_completeness_manifest_identity_and_dependency(self):
        self.assertEqual(validate_p17_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            self.assertGreater((MODULE / name).stat().st_size, 100)
            self.assertIn(QUESTION, (MODULE / name).read_text(encoding="utf-8"))
        p16 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P16")
        self.assertEqual(p16["status"], "implemented")
        self.assertIn("P16", self.readme)
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertRegex(module_index, r"\| \[P17\].*\| implemented \|")

    def test_contract_validator_rejects_missing_empty_duplicate_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "checks.md").unlink()
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p17_contract(fixture, self.manifest)
            self.assertIn("P17 missing checks.md", errors)
            self.assertIn("P17 empty lesson.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][16]))
        self.assertIn(
            "expected one P17 manifest entry, found 2",
            validate_p17_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p17_contract(MODULE, {"modules": "P17"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][16]["guiding_question"] = "generic"
        malformed["modules"][16]["status"] = "scaffolded"
        errors = validate_p17_contract(MODULE, malformed)
        self.assertIn(f"P17 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P17 status must be 'implemented'", errors)

    def test_deterministic_visible_base_matlab_operation_contract(self):
        for marker in (
            "random_seed = 1017;",
            "fs_hz = 2048;",
            "record_sample_count = 4096;",
            "carrier_frequency_hz = 240;",
            "lo_frequency_hz = 240;",
            "lowpass_cutoff_hz = 80;",
            "lowpass_tap_count = 129;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "randn(private_stream, 1, record_sample_count)",
            "exp(-1j*(2*pi*lo_frequency_hz*time_s + lo_phase_rad))",
            "mixed_signal_v = real_passband_v.*complex_oscillator;",
            "ideal_fir(tap_index) = sin(2*pi*lowpass_cutoff_hz*",
            "lowpass_fir = lowpass_fir/sum(lowpass_fir);",
            "mixed_full_v = conv(mixed_signal_v, lowpass_fir, 'full');",
            "baseband_iq_v = 2*filtered_mixer_v;",
        ):
            self.assertIn(marker, self.experiment)
        lowered = self.experiment.lower()
        for opaque in (
            "lowpass(", "fir1(", "designfilt(", "filter(", "downconvert(",
            "demod(", "comm.", "dsp.", "hilbert(", "pwelch(",
        ):
            self.assertNotIn(opaque, lowered)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_complex_mixing_and_lowpass_translate_signed_frequency_independently(self):
        fs_hz = 256.0
        tone = build_real_tone(fs_hz=fs_hz)
        phase_rad = 0.35
        for lo_hz, expected_hz in ((40.0, 8.0), (48.0, 0.0), (56.0, -8.0)):
            mixed = mix(tone, lo_hz, fs_hz)
            filtered = ideal_lowpass(mixed, 20.0, fs_hz)
            desired = projection(filtered, expected_hz, fs_hz)
            image = projection(filtered, -(48.0 + lo_hz), fs_hz)
            self.assertAlmostEqual(abs(desired), 0.5, places=11)
            self.assertAlmostEqual(wrap_phase(cmath.phase(desired) - phase_rad), 0.0, places=11)
            self.assertLess(abs(image), 1e-12)

        exact_mixed = mix(tone, 48.0, fs_hz)
        self.assertAlmostEqual(abs(projection(exact_mixed, 0.0, fs_hz)), 0.5, places=11)
        self.assertAlmostEqual(abs(projection(exact_mixed, -96.0, fs_hz)), 0.5, places=11)

    def test_explicit_fir_passes_every_sweep_beat_and_rejects_sum_images(self):
        coefficients = design_fir()
        self.assertAlmostEqual(sum(coefficients), 1.0, places=14)
        for beat_hz in (-36.0, 0.0, 36.0):
            self.assertGreater(fir_response(coefficients, beat_hz, 2048.0), 0.995)
        for image_hz in (444.0, 456.0, 480.0, 516.0):
            self.assertLess(fir_response(coefficients, image_hz, 2048.0), 0.001)
        for tap_count in (128, 130, True):
            with self.assertRaises(ValueError):
                design_fir(tap_count=tap_count)

    def test_finite_fir_chain_removes_group_delay_and_preserves_signed_phase(self):
        fs_hz = 2048.0
        carrier_hz = 240.0
        carrier_phase_rad = 0.35
        guard = 192
        tone = build_real_tone(
            fs_hz=fs_hz,
            count=4096,
            frequency_hz=carrier_hz,
            phase_rad=carrier_phase_rad,
        )
        coefficients = design_fir(fs_hz=fs_hz)

        for lo_hz, expected_hz in ((204.0, 36.0), (240.0, 0.0), (276.0, -36.0)):
            mixed = mix(tone, lo_hz, fs_hz)
            calibrated = [
                2 * value
                for value in apply_fir_and_remove_group_delay(mixed, coefficients)
            ]
            desired = windowed_projection(calibrated, expected_hz, fs_hz, guard)
            image = windowed_projection(
                calibrated,
                -(carrier_hz + lo_hz),
                fs_hz,
                guard,
            )
            with self.subTest(lo_hz=lo_hz):
                self.assertGreater(abs(desired), 0.995)
                self.assertLess(abs(desired), 1.001)
                self.assertAlmostEqual(
                    wrap_phase(cmath.phase(desired) - carrier_phase_rad),
                    0.0,
                    places=11,
                )
                self.assertLess(abs(image), 0.001)

        self.assertIn(
            "filtered_mixer_v = mixed_full_v(filter_half_length+1:",
            self.experiment,
        )
        self.assertEqual(
            self.experiment.count(
                "case_baseband_v = 2*case_full_v(filter_half_length+1:"
            ),
            2,
        )
        self.assertIn(
            "wrong_side_baseband_v = 2*wrong_side_full_v(filter_half_length+1:",
            self.experiment,
        )
        self.assertIn(
            "recovery_baseband_v = 2*recovery_full_v(filter_half_length+1:",
            self.experiment,
        )

    def test_lo_frequency_sweep_changes_only_signed_translation(self):
        section = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        self.assertIn("lo_frequency_sweep_hz = [204 240 276];", self.experiment)
        self.assertIn(
            "case_expected_frequency_hz = carrier_frequency_hz - case_lo_frequency_hz;",
            section,
        )
        self.assertNotIn("carrier_frequency_hz =", section)
        self.assertNotIn("carrier_phase_rad =", section)
        self.assertNotIn("lowpass_cutoff_hz =", section)
        self.assertEqual([240 - lo for lo in (204, 240, 276)], [36, 0, -36])
        for statement in (
            "`+36 Hz` counterclockwise", "`0 Hz` stationary", "`-36 Hz`",
        ):
            self.assertIn(statement, self.checks)

    def test_lo_phase_sweep_preserves_amplitude_and_frequency_independently(self):
        fs_hz = 256.0
        tone = build_real_tone(fs_hz=fs_hz)
        section = self.experiment.split("%% Sweep 2", 1)[1].split("%% Broken case", 1)[0]
        self.assertIn("lo_phase_sweep_rad = [0 pi/2 pi];", self.experiment)
        self.assertNotIn("lo_frequency_hz =", section)
        self.assertNotIn("carrier_amplitude_v =", section)
        for lo_phase in (0.0, math.pi / 2, math.pi):
            filtered = ideal_lowpass(mix(tone, 48.0, fs_hz, lo_phase), 20.0, fs_hz)
            output = 2 * projection(filtered, 0.0, fs_hz)
            self.assertAlmostEqual(abs(output), 1.0, places=11)
            self.assertAlmostEqual(
                wrap_phase(cmath.phase(output) - (0.35 - lo_phase)),
                0.0,
                places=11,
            )

    def test_broken_wrong_side_selects_conjugate_and_recovery_restores_sign(self):
        fs_hz = 256.0
        tone = build_real_tone(fs_hz=fs_hz)
        wrong = ideal_lowpass(mix(tone, 40.0, fs_hz, sign=+1), 20.0, fs_hz)
        recovered = ideal_lowpass(mix(tone, 40.0, fs_hz, sign=-1), 20.0, fs_hz)
        wrong_projection = 2 * projection(wrong, -8.0, fs_hz)
        recovered_projection = 2 * projection(recovered, 8.0, fs_hz)
        self.assertAlmostEqual(abs(wrong_projection), 1.0, places=11)
        self.assertAlmostEqual(abs(recovered_projection), 1.0, places=11)
        self.assertAlmostEqual(wrap_phase(cmath.phase(wrong_projection) + 0.35), 0.0, places=11)
        self.assertAlmostEqual(wrap_phase(cmath.phase(recovered_projection) - 0.35), 0.0, places=11)
        broken = self.experiment.split("%% Broken case", 1)[1]
        self.assertIn("wrong_side_oscillator = exp(+1j*2*pi*broken_lo_frequency_hz*time_s);", broken)
        self.assertIn("recovery_oscillator = exp(-1j*2*pi*broken_lo_frequency_hz*time_s);", broken)
        self.assertIn("does not produce nothing", broken)
        self.assertIn("wrong oscillator sign selected the other copy", self.walkthrough)

    def test_malformed_controls_and_resource_bounds(self):
        for name in (
            "random_seed", "fs_hz", "record_sample_count", "carrier_frequency_hz",
            "carrier_amplitude_v", "carrier_phase_rad", "noise_rms_v",
            "lo_frequency_hz", "lo_phase_rad", "broken_lo_frequency_hz", "lowpass_cutoff_hz",
            "lowpass_tap_count", "evaluation_guard_sample_count",
        ):
            for bad in (True, float("nan"), float("inf")):
                with self.subTest(name=name, bad=bad):
                    with self.assertRaises(ValueError):
                        validate_controls(**{name: bad})
        for overrides in (
            {"fs_hz": 0.0},
            {"random_seed": -1},
            {"random_seed": 2**32},
            {"record_sample_count": 4095},
            {"carrier_frequency_hz": 1024.0},
            {"carrier_frequency_hz": 241.0},
            {"lo_frequency_hz": 216.0},
            {"lo_frequency_hz": 900.0},
            {"lowpass_tap_count": 128},
            {"lowpass_cutoff_hz": 30.0},
            {"lowpass_cutoff_hz": 160.0},
            {"lo_frequency_sweep_hz": (204.0, 240.0)},
            {"lo_phase_sweep_rad": (0.0, math.pi)},
            {"broken_lo_frequency_hz": 220.0},
            {"max_record_samples": 8192},
            {"max_stored_numeric_values": 200000},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    validate_controls(**overrides)
        for marker in (
            "max_record_samples = 4096;",
            "max_fft_length = 4096;",
            "max_filter_taps = 129;",
            "max_sweep_cases = 3;",
            "max_stored_numeric_values = 180000;",
            "max_figure_groups = 5;",
            "P17 resource ceilings must remain fixed.",
        ):
            self.assertIn(marker, self.experiment)

    def test_validation_precedes_all_signal_and_transform_allocation(self):
        guard = self.experiment.index("P17 resource ceilings must remain fixed.")
        self.assertLess(guard, self.experiment.index("private_stream = RandStream"))
        self.assertLess(guard, self.experiment.index("real_passband_v ="))
        self.assertLess(guard, self.experiment.index("ideal_fir = zeros"))
        self.assertLess(guard, self.experiment.index("passband_spectrum_v ="))
        self.assertLess(guard, self.experiment.index("figure('Name'"))
        self.assertIn("clear results;", self.experiment)
        self.assertLess(self.experiment.index("clear results;"), self.experiment.index("%% Validate controls"))

    def test_plot_metric_result_and_unit_inventory_is_complete(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 5)
        for figure_name in (
            "P17 baseline signal flow",
            "P17 spectra through downconversion",
            "P17 LO-frequency sweep",
            "P17 LO-phase sweep",
            "P17 broken side selection and recovery",
        ):
            self.assertIn(figure_name, self.experiment)
        for unit_label in (
            "Time (ms)", "Time (s)", "Amplitude (V)", "Mixer output (V)",
            "Calibrated I/Q (V)", "I (V)", "Q (V)", "Frequency (Hz)",
            "Magnitude (dB re 1 V)",
        ):
            self.assertIn(unit_label, self.experiment)
        for result in (
            "results.expected_baseband_frequency_hz",
            "results.estimated_baseband_amplitude_v",
            "results.estimated_baseband_phase_rad",
            "results.unscaled_mixer_gain",
            "results.image_suppression_db",
            "results.lo_sweep_expected_frequency_hz",
            "results.lo_sweep_estimated_frequency_hz",
            "results.phase_sweep_estimated_phase_rad",
            "results.wrong_side_estimated_frequency_hz",
            "results.recovery_estimated_frequency_hz",
        ):
            self.assertIn(result, self.experiment)

    def test_timeout_cancellation_isolation_compatibility_recovery_and_rollback(self):
        lowered = self.experiment.lower()
        forbidden = (
            "input(", "pause(", "waitfor(", "uiwait(", "timer(", "parfor ",
            "backgroundpool", "fopen(", "writematrix(", "save(", "webread(",
            "webwrite(", "audioplayer(", "sound(", "while ", "system(", "unix(",
            "xline(", "yline(", "close all", "clear all", "clearvars",
        )
        for marker in forbidden:
            self.assertNotIn(marker, lowered)
        self.assertIn("findall(groot, 'Type', 'figure', 'Tag', 'P17')", self.experiment)
        self.assertNotIn("RandStream.setGlobalStream", self.experiment)
        for text in (self.readme, self.lesson, self.walkthrough, self.checks):
            self.assertIn("Ctrl+C", text)
            self.assertRegex(text.lower(), r"rerun|rerunning")
        self.assertIn("restores only P17", self.walkthrough)
        self.assertRegex(self.checks, r"Preserve\s+implemented P16")
        self.assertIn("writes no files", self.readme)

    def test_content_is_concept_first_complete_and_runtime_claim_boundary_is_honest(self):
        for name in ARTIFACTS:
            content = (MODULE / name).read_text(encoding="utf-8")
            self.assertNotRegex(content, r"\bTODO\b|\bTBD\b|coming soon|placeholder")
        for heading in (
            "## Physical mental model", "## Limiting cases",
            "## Radar connection", "## Common interpretation mistakes",
        ):
            self.assertIn(heading, self.lesson)
        for heading in ("## Baseline", "## Sweep 1", "## Sweep 2", "## Broken case"):
            self.assertIn(heading, self.walkthrough)
        self.assertIn("## Teach-back completion", self.checks)
        evidence = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("does **not** claim MATLAB or Octave execution", evidence)
        for heading in (
            "## Acceptance mapping", "## Changed and preserved invariants",
            "## Residual risks and unperformed validation",
            "## Rollback and recovery", "## Exact commands and results",
        ):
            self.assertIn(heading, evidence)
        unsupported = (
            "MATLAB execution passed", "rendered figures verified",
            "hardware validated", "field validated", "production validated",
        )
        for claim in unsupported:
            self.assertNotIn(claim, self.all_content + "\n" + evidence)


if __name__ == "__main__":
    unittest.main()
