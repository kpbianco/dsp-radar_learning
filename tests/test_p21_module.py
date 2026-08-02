from __future__ import annotations

import cmath
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/21-visualize-am-as-carrier-and-sidebands"
EVIDENCE = ROOT / "docs/evidence/P21-2026-08-02.md"
QUESTION = "How does a baseband waveform create RF sidebands?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
EXPECTED_IDENTITY = {
    "number": 21,
    "id": "P21",
    "title": "Visualize AM as Carrier and Sidebands",
    "guiding_question": QUESTION,
    "phase": 3,
    "phase_title": "Modulation, Channels, and Statistical Estimation",
    "slug": "visualize-am-as-carrier-and-sidebands",
    "folder": "modules/21-visualize-am-as-carrier-and-sidebands",
    "status": "implemented",
    "implementation_batch": "P21",
}


def validate_p21_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P21 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P21 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    matches = [
        entry for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P21"
    ]
    if len(matches) != 1:
        return errors + [f"expected one P21 manifest entry, found {len(matches)}"]
    entry = matches[0]
    for key, expected in EXPECTED_IDENTITY.items():
        if entry.get(key) != expected:
            errors.append(f"P21 {key} must be {expected!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def canonical_controls() -> dict:
    return {
        "random_seed": 1021,
        "fs_hz": 20000.0,
        "duration_s": 0.10,
        "sample_count": 2000,
        "carrier_frequency_hz": 3000.0,
        "carrier_amplitude_v": 1.0,
        "message_frequency_hz": 200.0,
        "baseline_modulation_depth": 0.60,
        "receiver_noise_rms_v": 0.005,
        "multitone_frequencies_hz": (100.0, 350.0),
        "multitone_weights": (0.60, 0.40),
        "multitone_modulation_depth": 0.60,
        "modulation_depth_sweep": (0.20, 0.60, 1.00, 1.40),
        "message_frequency_sweep_hz": (100.0, 200.0, 400.0, 700.0),
        "broken_modulation_depth": 1.40,
        "recovery_lowpass_cutoff_hz": 900.0,
        "time_view_duration_s": 0.010,
        "max_sample_count": 2000,
        "max_sweep_cases": 4,
        "max_figure_groups": 6,
        "max_stored_numeric_values": 200000,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    scalar_names = (
        "random_seed", "fs_hz", "duration_s", "sample_count",
        "carrier_frequency_hz", "carrier_amplitude_v", "message_frequency_hz",
        "baseline_modulation_depth", "receiver_noise_rms_v",
        "multitone_modulation_depth", "broken_modulation_depth",
        "recovery_lowpass_cutoff_hz", "time_view_duration_s",
        "max_sample_count", "max_sweep_cases", "max_figure_groups",
        "max_stored_numeric_values",
    )
    if not all(_finite_real(controls[name]) for name in scalar_names):
        raise ValueError("scalar controls must be finite, real, and nonlogical")
    expected_scalars = {
        "random_seed": 1021,
        "fs_hz": 20000.0,
        "duration_s": 0.10,
        "sample_count": 2000,
        "carrier_frequency_hz": 3000.0,
        "carrier_amplitude_v": 1.0,
        "message_frequency_hz": 200.0,
        "baseline_modulation_depth": 0.60,
        "receiver_noise_rms_v": 0.005,
        "multitone_modulation_depth": 0.60,
        "broken_modulation_depth": 1.40,
        "recovery_lowpass_cutoff_hz": 900.0,
        "time_view_duration_s": 0.010,
        "max_sample_count": 2000,
        "max_sweep_cases": 4,
        "max_figure_groups": 6,
        "max_stored_numeric_values": 200000,
    }
    if any(controls[name] != expected for name, expected in expected_scalars.items()):
        raise ValueError("canonical scalar controls are fixed")

    vector_expectations = {
        "multitone_frequencies_hz": (100.0, 350.0),
        "multitone_weights": (0.60, 0.40),
        "modulation_depth_sweep": (0.20, 0.60, 1.00, 1.40),
        "message_frequency_sweep_hz": (100.0, 200.0, 400.0, 700.0),
    }
    for name, expected in vector_expectations.items():
        value = controls[name]
        if not isinstance(value, (tuple, list)):
            raise ValueError(f"{name} must be a bounded numeric vector")
        if not all(_finite_real(item) for item in value):
            raise ValueError(f"{name} must contain finite real values")
        if tuple(value) != expected:
            raise ValueError(f"{name} must equal its canonical vector")
    if sum(controls["multitone_weights"]) != 1.0:
        raise ValueError("multitone weights must sum to one")


def dft(values: list[complex]) -> list[complex]:
    count = len(values)
    return [
        sum(value * cmath.exp(-2j * math.pi * k * n / count)
            for n, value in enumerate(values))
        for k in range(count)
    ]


def idft(values: list[complex]) -> list[complex]:
    count = len(values)
    return [
        sum(value * cmath.exp(2j * math.pi * k * n / count)
            for k, value in enumerate(values)) / count
        for n in range(count)
    ]


def one_sided_amplitude(signal: list[float], frequency_hz: float, fs_hz: float) -> float:
    coefficient = sum(
        value * cmath.exp(-2j * math.pi * frequency_hz * n / fs_hz)
        for n, value in enumerate(signal)
    )
    return 2 * abs(coefficient) / len(signal)


def am_signal(
    *,
    fs_hz: float = 2000.0,
    sample_count: int = 200,
    carrier_hz: float = 300.0,
    message_hz: float = 20.0,
    depth: float = 0.6,
) -> tuple[list[float], list[float]]:
    message = [
        math.cos(2 * math.pi * message_hz * n / fs_hz)
        for n in range(sample_count)
    ]
    signal = [
        (1 + depth * value) * math.cos(2 * math.pi * carrier_hz * n / fs_hz)
        for n, value in enumerate(message)
    ]
    return message, signal


def analytic_envelope(signal: list[float]) -> list[float]:
    spectrum = dft([complex(value) for value in signal])
    count = len(signal)
    mask = [0.0] * count
    mask[0] = 1.0
    for index in range(1, count // 2):
        mask[index] = 2.0
    mask[count // 2] = 1.0
    analytic = idft([value * weight for value, weight in zip(spectrum, mask)])
    return [abs(value) for value in analytic]


def coherent_recovery(
    signal: list[float], *, depth: float, fs_hz: float = 2000.0,
    carrier_hz: float = 300.0, cutoff_hz: float = 90.0,
) -> list[float]:
    mixed = [
        2 * value * math.cos(2 * math.pi * carrier_hz * n / fs_hz)
        for n, value in enumerate(signal)
    ]
    spectrum = dft([complex(value) for value in mixed])
    count = len(signal)
    spacing = fs_hz / count
    signed_frequencies = [
        (index if index <= count // 2 else index - count) * spacing
        for index in range(count)
    ]
    baseband = idft([
        value if abs(frequency) <= cutoff_hz else 0j
        for value, frequency in zip(spectrum, signed_frequencies)
    ])
    return [(value.real - 1) / depth for value in baseband]


def rmse(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)) / len(left))


class P21ModuleTests(unittest.TestCase):
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
        self.assertEqual(validate_p21_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            path = MODULE / name
            self.assertGreater(path.stat().st_size, 100)
            self.assertIn(QUESTION, path.read_text(encoding="utf-8"))
        p20 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P20")
        self.assertEqual(p20["status"], "implemented")
        self.assertIn("P20", self.readme)
        self.assertIn("P20", self.lesson)
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertRegex(module_index, r"\| \[P21\].*\| implemented \|")

    def test_contract_rejects_missing_empty_duplicate_nonlist_and_wrong_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "experiment.m").unlink()
            (fixture / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p21_contract(fixture, self.manifest)
            self.assertIn("P21 missing experiment.m", errors)
            self.assertIn("P21 empty checks.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][20]))
        self.assertIn(
            "expected one P21 manifest entry, found 2",
            validate_p21_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p21_contract(MODULE, {"modules": "P21"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][20]["guiding_question"] = "generic"
        malformed["modules"][20]["status"] = "scaffolded"
        errors = validate_p21_contract(MODULE, malformed)
        self.assertIn(f"P21 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P21 status must be 'implemented'", errors)

    def test_deterministic_visible_am_controls_and_private_noise(self):
        for marker in (
            "random_seed = 1021;", "fs_hz = 20000;", "duration_s = 0.10;",
            "carrier_frequency_hz = 3000;", "message_frequency_hz = 200;",
            "baseline_modulation_depth = 0.60;", "receiver_noise_rms_v = 0.005;",
            "multitone_modulation_depth = baseline_modulation_depth;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "receiver_noise_v = receiver_noise_rms_v* ...\n"
            "    randn(private_stream, 1, sample_count);",
            "clean_rf_v = signed_envelope_v.*carrier;",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_single_tone_am_has_carrier_and_symmetric_sidebands(self):
        _, signal = am_signal()
        self.assertAlmostEqual(one_sided_amplitude(signal, 300, 2000), 1.0, places=12)
        self.assertAlmostEqual(one_sided_amplitude(signal, 280, 2000), 0.3, places=12)
        self.assertAlmostEqual(one_sided_amplitude(signal, 320, 2000), 0.3, places=12)
        self.assertLess(one_sided_amplitude(signal, 260, 2000), 1e-12)
        self.assertIn(
            "expected_sideband_amplitude_v = ...\n"
            "    carrier_amplitude_v*baseline_modulation_depth/2;",
            self.experiment,
        )

    def test_multitone_message_creates_weighted_sideband_pairs(self):
        fs_hz = 2000.0
        count = 200
        message = [
            0.6 * math.cos(2 * math.pi * 10 * n / fs_hz)
            + 0.4 * math.cos(2 * math.pi * 40 * n / fs_hz)
            for n in range(count)
        ]
        signal = [
            (1 + 0.6 * value) * math.cos(2 * math.pi * 300 * n / fs_hz)
            for n, value in enumerate(message)
        ]
        for frequency, expected in ((290, 0.18), (310, 0.18), (260, 0.12), (340, 0.12)):
            self.assertAlmostEqual(
                one_sided_amplitude(signal, frequency, fs_hz), expected, places=12
            )
        section = self.experiment.split("%% Multitone message", 1)[1].split(
            "%% Sweep 1", 1
        )[0]
        self.assertIn("multitone_received_rf_v = multitone_clean_rf_v + receiver_noise_v;", section)
        self.assertIn(
            "plot(1000*time_s(time_view), multitone_envelope_recovered(time_view), '--',",
            section,
        )
        self.assertNotIn("multitone_detected_envelope_v(time_view)-1", section)
        self.assertNotIn("randn(", section)

    def test_multitone_transition_changes_only_message_content(self):
        fs_hz = 2000.0
        sample_count = 200
        carrier_hz = 300.0
        depth = 0.60
        time_s = [index / fs_hz for index in range(sample_count)]
        carrier = [
            math.cos(2 * math.pi * carrier_hz * value) for value in time_s
        ]
        baseline_message = [
            math.cos(2 * math.pi * 20 * value) for value in time_s
        ]
        multitone_message = [
            0.60 * math.cos(2 * math.pi * 10 * value)
            + 0.40 * math.cos(2 * math.pi * 40 * value)
            for value in time_s
        ]
        shared_noise = [
            0.005 * math.cos(2 * math.pi * 73 * value + 0.31)
            for value in time_s
        ]
        baseline_received = [
            (1 + depth * message) * oscillator + noise
            for message, oscillator, noise in zip(
                baseline_message, carrier, shared_noise
            )
        ]
        multitone_received = [
            (1 + depth * message) * oscillator + noise
            for message, oscillator, noise in zip(
                multitone_message, carrier, shared_noise
            )
        ]
        expected_paired_difference = [
            depth * (multitone - baseline) * oscillator
            for multitone, baseline, oscillator in zip(
                multitone_message, baseline_message, carrier
            )
        ]
        self.assertLess(
            max(abs((multi - single) - expected) for multi, single, expected in zip(
                multitone_received, baseline_received, expected_paired_difference
            )),
            1e-15,
        )

        section = self.experiment.split("%% Multitone message", 1)[1].split(
            "%% Sweep 1", 1
        )[0]
        self.assertIn(
            "multitone_modulation_depth = baseline_modulation_depth;",
            self.experiment,
        )
        self.assertIn(
            "multitone_received_rf_v = multitone_clean_rf_v + receiver_noise_v;",
            section,
        )
        self.assertNotIn("randn(", section)

    def test_envelope_and_coherent_detectors_agree_before_inversion(self):
        message, signal = am_signal(depth=0.6)
        envelope = analytic_envelope(signal)
        envelope_recovered = [(value - 1) / 0.6 for value in envelope]
        coherent = coherent_recovery(signal, depth=0.6)
        self.assertLess(rmse(envelope_recovered, message), 1e-12)
        self.assertLess(rmse(coherent, message), 1e-12)
        for formula in (
            "analytic_received_v = ifft(received_spectrum_v.*analytic_mask);",
            "detected_envelope_v = abs(analytic_received_v);",
            "mixed_to_baseband_v = 2*received_rf_v.*carrier;",
            "coherent_baseband_v = real(ifft(fft(mixed_to_baseband_v).*lowpass_mask));",
        ):
            self.assertIn(formula, self.experiment)

    def test_overmodulation_breaks_magnitude_but_not_coherent_recovery(self):
        message, signal = am_signal(depth=1.4)
        envelope = analytic_envelope(signal)
        envelope_recovered = [(value - 1) / 1.4 for value in envelope]
        coherent = coherent_recovery(signal, depth=1.4)
        self.assertGreater(rmse(envelope_recovered, message), 0.1)
        self.assertLess(rmse(coherent, message), 1e-12)
        self.assertLess(min(1 + 1.4 * value for value in message), 0)
        broken = self.experiment.split("%% Broken case", 1)[1].split(
            "%% Retained workspace results", 1
        )[0]
        self.assertIn("broken_detected_envelope_v = abs(broken_analytic_v);", broken)
        self.assertIn("inverted_sample_fraction", broken)
        self.assertIn("broken_coherent_rmse < 1e-10", broken)

    def test_two_one_variable_sweeps_are_bounded_and_physically_tied(self):
        depth_section = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        frequency_section = self.experiment.split("%% Sweep 2", 1)[1].split(
            "%% Broken case", 1
        )[0]
        self.assertEqual(depth_section.count("for sweep_index ="), 1)
        self.assertEqual(frequency_section.count("for sweep_index ="), 1)
        self.assertIn("case_depth = modulation_depth_sweep(sweep_index);", depth_section)
        self.assertNotIn("case_message_frequency_hz", depth_section)
        self.assertIn(
            "case_message_frequency_hz = message_frequency_sweep_hz(sweep_index);",
            frequency_section,
        )
        self.assertNotIn("case_depth", frequency_section)
        self.assertIn("observed_lower_offset_hz", frequency_section)
        self.assertIn("observed_upper_offset_hz", frequency_section)

    def test_malformed_controls_and_resource_ceilings(self):
        for key, value in (
            ("random_seed", True), ("fs_hz", math.nan), ("duration_s", math.inf),
            ("sample_count", 2001), ("carrier_frequency_hz", complex(3000, 1)),
            ("carrier_amplitude_v", 0.0), ("message_frequency_hz", 10000.0),
            ("baseline_modulation_depth", -0.6), ("receiver_noise_rms_v", -0.005),
            ("multitone_frequencies_hz", (100.0, math.nan)),
            ("multitone_weights", (0.5, 0.5)),
            ("multitone_modulation_depth", 1.2),
            ("modulation_depth_sweep", (0.2, 0.6, 1.4)),
            ("message_frequency_sweep_hz", (100.0, 200.0, 400.0, 1000.0)),
            ("broken_modulation_depth", 1.0),
            ("recovery_lowpass_cutoff_hz", 1000.0),
            ("time_view_duration_s", 0.020),
            ("max_sample_count", 4000), ("max_sweep_cases", 5),
            ("max_figure_groups", 7), ("max_stored_numeric_values", 400000),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_controls(**{key: value})
        with self.assertRaises(ValueError):
            validate_controls(unknown_control=1)

    def test_matlab_guards_reject_logical_controls_before_signal_work(self):
        validation = self.experiment.split("% Validation succeeded:", 1)[0]
        for control in (
            "random_seed", "fs_hz", "duration_s", "sample_count",
            "carrier_frequency_hz", "carrier_amplitude_v", "message_frequency_hz",
            "baseline_modulation_depth", "receiver_noise_rms_v",
            "multitone_frequencies_hz", "multitone_weights",
            "multitone_modulation_depth", "modulation_depth_sweep",
            "message_frequency_sweep_hz", "broken_modulation_depth",
            "recovery_lowpass_cutoff_hz", "time_view_duration_s",
            "max_sample_count", "max_sweep_cases", "max_figure_groups",
            "max_stored_numeric_values",
        ):
            self.assertIn(f"~islogical({control})", validation, control)

    def test_coherent_reference_error_limiting_case_is_physical(self):
        self.assertIn("constant carrier phase error scales", self.lesson.lower())
        self.assertIn("doubled-carrier term is still removed", self.lesson.lower())
        self.assertIn("carrier frequency error produces a", self.lesson.lower())
        self.assertIn("time-varying beat", self.lesson.lower())
        self.assertNotIn(
            "phase error no longer removes the doubled-carrier term",
            self.lesson.lower(),
        )

    def test_validation_precedes_random_allocation_fft_cleanup_and_figures(self):
        validation_end = self.experiment.index("% Validation succeeded:")
        for marker in (
            "RandStream(", "time_s = (0:sample_count-1)/fs_hz;", "fft(",
            "close(findall(", "figure('Name'",
        ):
            self.assertGreater(self.experiment.index(marker), validation_end, marker)
        self.assertIn("max_sample_count = 2000;", self.experiment[:validation_end])
        self.assertIn("max_sweep_cases = 4;", self.experiment[:validation_end])
        self.assertIn("max_figure_groups = 6;", self.experiment[:validation_end])
        self.assertIn("max_stored_numeric_values = 200000;", self.experiment[:validation_end])
        self.assertLessEqual(2000 * (45 + 30 + 15), 200000)

    def test_plot_metric_unit_and_retained_result_inventory(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 6)
        self.assertEqual(self.experiment.count("'Tag', 'P21'"), 7)
        for label in (
            "Time (ms)", "Message (normalized)", "Envelope (V)", "RF voltage (V)",
            "Recovered message (normalized)", "RF frequency (Hz)",
            "Amplitude (dB re 1 V)", "One-sided sinusoid amplitude (V)",
            "Modulation depth \\mu (dimensionless)", "Minimum signed envelope (V)",
            "Recovery RMSE (normalized amplitude)", "Message frequency (Hz)",
            "Observed RF line frequency (Hz)", "Sideband offset from carrier (Hz)",
        ):
            self.assertIn(label, self.experiment)
        for result in (
            "results.measured_sideband_amplitudes_v",
            "results.envelope_recovered_message",
            "results.coherent_recovered_message",
            "results.multitone_line_frequencies_hz",
            "results.multitone_modulation_depth",
            "results.depth_minimum_signed_envelope_v",
            "results.depth_envelope_rmse",
            "results.depth_coherent_rmse",
            "results.observed_lower_sideband_hz",
            "results.observed_upper_sideband_hz",
            "results.broken_envelope_rmse",
            "results.broken_coherent_rmse",
            "results.inverted_sample_fraction",
        ):
            self.assertIn(result, self.experiment)

    def test_content_is_concept_first_complete_and_runtime_claim_boundary_is_honest(self):
        lowered = self.all_content.lower()
        for placeholder in ("todo", "tbd", "placeholder"):
            self.assertNotIn(placeholder, lowered)
        for phrase in (
            "physical mental model", "limiting cases", "radar connection",
            "common interpretation mistakes", "signed envelope", "coherent detection",
        ):
            self.assertIn(phrase, self.lesson.lower())
        for heading in (
            "## Baseline", "## Multitone transition", "## Sweep 1", "## Sweep 2",
            "## Broken case", "## Concept connection and completion handoff",
        ):
            self.assertIn(heading, self.walkthrough)
        self.assertIn("## Teach-back completion", self.checks)
        self.assertTrue(EVIDENCE.is_file())
        evidence = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("does **not** claim MATLAB or Octave execution", evidence)
        self.assertIn("Acceptance mapping", evidence)
        self.assertIn("Residual risks and unperformed validation", evidence)

    def test_no_placeholder_unexplained_black_box_or_external_io(self):
        lowered = self.experiment.lower()
        for opaque in (
            "ammod(", "amdemod(", "envelope(", "hilbert(", "lowpass(",
            "designfilt(", "phased.", "dsp.", "comm.", "helper",
        ):
            self.assertNotIn(opaque, lowered)
        for unsafe in (
            "input(", "pause(", "while ", "timer(", "parfor ", "parfeval(",
            "fopen(", "webread(", "audioplayer(", "sound(", "system(",
            "close all", "clear all", "clearvars",
        ):
            self.assertNotIn(unsafe, lowered)
        self.assertNotRegex(lowered, r"\b(?:read|write)(?:matrix|table)\s*\(")

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback(self):
        self.assertNotIn("while ", self.experiment.lower())
        self.assertIn("Ctrl+C", self.experiment)
        self.assertIn("Ctrl+C", self.walkthrough)
        self.assertIn("private seed", self.walkthrough)
        self.assertIn("global random stream", self.walkthrough)
        self.assertIn("P21-tagged", self.walkthrough)
        self.assertIn("partial P21 figure set", self.experiment)
        self.assertIn("empty/incomplete `results`", self.walkthrough)
        self.assertIn("Rerun from the top", self.walkthrough)
        self.assertIn("Rollback", self.walkthrough)
        self.assertIn("restores only P21's", self.walkthrough)
        self.assertIn("Preserve implemented P20", self.walkthrough)
        self.assertIn("base MATLAB", self.walkthrough)


if __name__ == "__main__":
    unittest.main()
