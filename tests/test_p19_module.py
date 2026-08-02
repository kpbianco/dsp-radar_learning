from __future__ import annotations

import cmath
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/19-inject-and-correct-iq-impairments"
EVIDENCE = ROOT / "docs/evidence/P19-2026-08-02.md"
QUESTION = "How do DC offset, gain mismatch, and quadrature error change an IQ spectrum?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def validate_p19_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P19 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P19 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    entries = [
        entry for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P19"
    ]
    if len(entries) != 1:
        return errors + [f"expected one P19 manifest entry, found {len(entries)}"]

    expected = {
        "number": 19,
        "id": "P19",
        "title": "Inject and Correct IQ Impairments",
        "guiding_question": QUESTION,
        "phase": 2,
        "phase_title": "Fourier, Spectral, and I/Q Intuition",
        "slug": "inject-and-correct-iq-impairments",
        "folder": "modules/19-inject-and-correct-iq-impairments",
        "status": "implemented",
        "implementation_batch": "P19",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P19 {key} must be {value!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_controls(**overrides: object) -> None:
    controls: dict[str, object] = {
        "random_seed": 1019,
        "fs_hz": 2048.0,
        "record_sample_count": 4096,
        "tone_frequency_hz": 160.0,
        "tone_amplitude_v": 1.0,
        "tone_phase_rad": 0.35,
        "noise_rms_v": 0.002,
        "dc_i_v": 0.12,
        "dc_q_v": -0.08,
        "i_gain": 1.15,
        "q_gain": 0.85,
        "quadrature_error_deg": 8.0,
        "i_gain_sweep": (1.0, 1.10, 1.30),
        "quadrature_error_sweep_deg": (0.0, 5.0, 15.0),
        "max_record_samples": 4096,
        "max_fft_length": 4096,
        "max_sweep_cases": 3,
        "max_stored_numeric_values": 360000,
        "max_figure_groups": 6,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    scalar_names = (
        "random_seed", "fs_hz", "record_sample_count", "tone_frequency_hz",
        "tone_amplitude_v", "tone_phase_rad", "noise_rms_v", "dc_i_v",
        "dc_q_v", "i_gain", "q_gain", "quadrature_error_deg",
    )
    if not all(_finite_real(controls[name]) for name in scalar_names):
        raise ValueError("scalar controls must be finite real nonlogical values")
    if controls["random_seed"] != 1019:
        raise ValueError("canonical seed required")
    if controls["fs_hz"] != 2048 or controls["record_sample_count"] != 4096:
        raise ValueError("canonical rate and record required")
    if int(controls["record_sample_count"]) % 2:
        raise ValueError("record must be even")
    cycles = (
        controls["tone_frequency_hz"]
        * controls["record_sample_count"]
        / controls["fs_hz"]
    )
    if controls["tone_frequency_hz"] != 160 or cycles != int(cycles):
        raise ValueError("canonical coherent tone required")
    if not 0 < controls["tone_amplitude_v"] <= 2:
        raise ValueError("amplitude must be positive and bounded")
    if not 0 <= controls["noise_rms_v"] <= 0.01:
        raise ValueError("noise must be nonnegative and bounded")
    if controls["dc_i_v"] != 0.12 or controls["dc_q_v"] != -0.08:
        raise ValueError("canonical DC offset required")
    if controls["i_gain"] != 1.15 or controls["q_gain"] != 0.85:
        raise ValueError("canonical branch gains required")
    if controls["i_gain"] <= 0 or controls["q_gain"] <= 0:
        raise ValueError("branch gains must be positive")
    if controls["quadrature_error_deg"] != 8:
        raise ValueError("canonical quadrature error required")
    if abs(controls["quadrature_error_deg"]) >= 45:
        raise ValueError("quadrature correction must remain invertible")

    gain_sweep = controls["i_gain_sweep"]
    phase_sweep = controls["quadrature_error_sweep_deg"]
    if gain_sweep != (1.0, 1.10, 1.30):
        raise ValueError("canonical gain sweep required")
    if phase_sweep != (0.0, 5.0, 15.0):
        raise ValueError("canonical phase sweep required")
    if not all(_finite_real(value) and value > 0 for value in gain_sweep):
        raise ValueError("gain sweep values must be finite and positive")
    if not all(_finite_real(value) and abs(value) < 45 for value in phase_sweep):
        raise ValueError("phase sweep values must be finite and invertible")

    ceilings = {
        "max_record_samples": 4096,
        "max_fft_length": 4096,
        "max_sweep_cases": 3,
        "max_stored_numeric_values": 360000,
        "max_figure_groups": 6,
    }
    if any(controls[name] != expected for name, expected in ceilings.items()):
        raise ValueError("resource ceilings are fixed")


def build_tone(
    count: int = 256,
    frequency_hz: float = 32.0,
    fs_hz: float = 256.0,
    amplitude_v: float = 1.0,
    phase_rad: float = 0.35,
) -> list[complex]:
    phase_step = cmath.exp(2j * math.pi * frequency_hz / fs_hz)
    sample = amplitude_v * cmath.exp(1j * phase_rad)
    result: list[complex] = []
    for _ in range(count):
        result.append(sample)
        sample *= phase_step
    return result


def impair(
    signal: list[complex], *, dc: complex = 0j, i_gain: float = 1.0,
    q_gain: float = 1.0, phase_error_rad: float = 0.0,
) -> list[complex]:
    return [
        i_gain * value.real + dc.real
        + 1j * (
            q_gain * (
                value.imag * math.cos(phase_error_rad)
                + value.real * math.sin(phase_error_rad)
            )
            + dc.imag
        )
        for value in signal
    ]


def coefficient(signal: list[complex], reference: list[complex]) -> complex:
    return sum(value * basis for value, basis in zip(signal, reference)) / len(signal)


def metrics(
    signal: list[complex], tone: list[complex], floor: float = 1e-15,
) -> tuple[float, float, float, float]:
    unit_tone = [value / abs(value) for value in tone]
    desired = abs(coefficient(signal, [value.conjugate() for value in unit_tone]))
    image = abs(coefficient(signal, unit_tone))
    dc = abs(sum(signal) / len(signal))
    irr_db = 20 * math.log10(max(desired, floor) / max(image, floor))
    return dc, desired, image, irr_db


def correct(
    signal: list[complex], amplitude_v: float = 1.0,
) -> tuple[list[complex], complex, float, float, float]:
    estimated_dc = sum(signal) / len(signal)
    centered = [value - estimated_dc for value in signal]
    estimated_i_gain = math.sqrt(
        2 * sum(value.real**2 for value in centered) / len(centered)
    ) / amplitude_v
    estimated_q_gain = math.sqrt(
        2 * sum(value.imag**2 for value in centered) / len(centered)
    ) / amplitude_v
    gain_corrected = [
        value.real / estimated_i_gain + 1j * value.imag / estimated_q_gain
        for value in centered
    ]
    rho = (
        2
        * sum(value.real * value.imag for value in gain_corrected)
        / len(gain_corrected)
        / amplitude_v**2
    )
    rho = max(-1.0, min(1.0, rho))
    estimated_phase = math.asin(rho)
    corrected = [
        value.real
        + 1j
        * (
            value.imag - value.real * math.sin(estimated_phase)
        )
        / math.cos(estimated_phase)
        for value in gain_corrected
    ]
    return (
        corrected, estimated_dc, estimated_i_gain, estimated_q_gain,
        estimated_phase,
    )


class P19ModuleTests(unittest.TestCase):
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
        self.assertEqual(validate_p19_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            path = MODULE / name
            self.assertGreater(path.stat().st_size, 100)
            self.assertIn(QUESTION, path.read_text(encoding="utf-8"))
        p18 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P18")
        self.assertEqual(p18["status"], "implemented")
        self.assertIn("P18", self.readme)
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertRegex(module_index, r"\| \[P19\].*\| implemented \|")

    def test_contract_rejects_missing_empty_duplicate_nonlist_and_wrong_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "checks.md").unlink()
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p19_contract(fixture, self.manifest)
            self.assertIn("P19 missing checks.md", errors)
            self.assertIn("P19 empty lesson.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][18]))
        self.assertIn(
            "expected one P19 manifest entry, found 2",
            validate_p19_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p19_contract(MODULE, {"modules": "P19"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][18]["guiding_question"] = "generic"
        malformed["modules"][18]["status"] = "scaffolded"
        errors = validate_p19_contract(MODULE, malformed)
        self.assertIn(f"P19 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P19 status must be 'implemented'", errors)

    def test_deterministic_visible_explicit_base_matlab_contract(self):
        for marker in (
            "random_seed = 1019;",
            "fs_hz = 2048;",
            "record_sample_count = 4096;",
            "tone_frequency_hz = 160;",
            "dc_i_v = 0.12;",
            "dc_q_v = -0.08;",
            "i_gain = 1.15;",
            "q_gain = 0.85;",
            "quadrature_error_deg = 8;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "randn(private_stream, 1, record_sample_count)",
            "clean_iq_v = tone_amplitude_v*exp(1j*tone_phase_v)",
            "reference_positive = exp(-1j*tone_phase_v);",
            "reference_negative = exp(1j*tone_phase_v);",
            "impaired_iq_v = (i_gain*clean_i_v + dc_i_v)",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_independent_signatures_separate_dc_gain_and_quadrature_error(self):
        tone = build_tone()
        clean = metrics(tone, tone)
        dc_only = metrics(impair(tone, dc=0.12 - 0.08j), tone)
        gain_only = metrics(impair(tone, i_gain=1.15, q_gain=0.85), tone)
        phase_only = metrics(impair(tone, phase_error_rad=math.radians(8)), tone)

        self.assertLess(clean[0], 1e-14)
        self.assertLess(clean[2], 1e-14)
        self.assertAlmostEqual(dc_only[0], math.hypot(0.12, 0.08), places=12)
        self.assertLess(dc_only[2], 1e-14)
        self.assertAlmostEqual(gain_only[1], 1.0, places=12)
        self.assertAlmostEqual(gain_only[2], 0.15, places=12)
        self.assertAlmostEqual(
            gain_only[3], 20 * math.log10(1 / 0.15), places=11
        )
        self.assertAlmostEqual(
            phase_only[3],
            20 * math.log10(1 / math.tan(math.radians(8) / 2)),
            places=10,
        )

    def test_staged_correction_recovers_combined_impairment(self):
        tone = build_tone()
        phase_error = math.radians(8)
        impaired = impair(
            tone, dc=0.12 - 0.08j, i_gain=1.15, q_gain=0.85,
            phase_error_rad=phase_error,
        )
        before = metrics(impaired, tone)
        corrected, estimated_dc, gi, gq, estimated_phase = correct(impaired)
        after = metrics(corrected, tone)

        self.assertAlmostEqual(estimated_dc.real, 0.12, places=12)
        self.assertAlmostEqual(estimated_dc.imag, -0.08, places=12)
        self.assertAlmostEqual(gi, 1.15, places=12)
        self.assertAlmostEqual(gq, 0.85, places=12)
        self.assertAlmostEqual(estimated_phase, phase_error, places=12)
        self.assertLess(max(abs(a - b) for a, b in zip(corrected, tone)), 1e-12)
        self.assertGreater(after[3], before[3] + 200)

    def test_matlab_source_is_linked_to_the_independently_checked_equations(self):
        for formula in (
            "impaired_iq_v = (i_gain*clean_i_v + dc_i_v) + 1j*( ...\n"
            "    q_gain*(clean_q_v*cos(quadrature_error_rad) + ...\n"
            "    clean_i_v*sin(quadrature_error_rad)) + dc_q_v);",
            "estimated_dc_v = mean(impaired_iq_v);\n"
            "dc_corrected_iq_v = impaired_iq_v - estimated_dc_v;",
            "estimated_i_gain = sqrt(2*mean(real(dc_corrected_iq_v).^2))/ ...\n"
            "    tone_amplitude_v;",
            "estimated_q_gain = sqrt(2*mean(imag(dc_corrected_iq_v).^2))/ ...\n"
            "    tone_amplitude_v;",
            "estimated_iq_correlation = 2*mean( ...\n"
            "    gain_corrected_i_v.*gain_corrected_q_v)/(tone_amplitude_v^2);",
            "estimated_quadrature_error_rad = asin(estimated_iq_correlation);",
            "phase_corrected_q_v = (gain_corrected_q_v - ...\n"
            "    gain_corrected_i_v*sin(estimated_quadrature_error_rad))/ ...\n"
            "    cos(estimated_quadrature_error_rad);",
        ):
            self.assertIn(formula, self.experiment)

    def test_gain_sweep_changes_only_axis_scale_and_image_rejection(self):
        section = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        self.assertIn("i_gain_sweep = [1 1.10 1.30];", self.experiment)
        self.assertNotIn("q_gain =", section)
        self.assertNotIn("quadrature_error_deg =", section)
        tone = build_tone()
        irrs = []
        for gain in (1.0, 1.10, 1.30):
            signal = impair(tone, i_gain=gain)
            _, _, _, irr = metrics(signal, tone)
            axis_ratio = math.sqrt(
                sum(value.real**2 for value in signal)
                / sum(value.imag**2 for value in signal)
            )
            self.assertAlmostEqual(axis_ratio, gain, places=12)
            irrs.append(irr)
        self.assertGreater(irrs[0], irrs[1])
        self.assertGreater(irrs[1], irrs[2])

    def test_quadrature_sweep_changes_only_shear_and_image_rejection(self):
        section = self.experiment.split("%% Sweep 2", 1)[1].split("%% Broken case", 1)[0]
        self.assertIn(
            "quadrature_error_sweep_deg = [0 5 15];", self.experiment
        )
        self.assertNotIn("i_gain =", section)
        self.assertNotIn("q_gain =", section)
        tone = build_tone()
        irrs = []
        for degrees in (0.0, 5.0, 15.0):
            signal = impair(tone, phase_error_rad=math.radians(degrees))
            centered_i = [value.real for value in signal]
            centered_q = [value.imag for value in signal]
            correlation = sum(a * b for a, b in zip(centered_i, centered_q)) / math.sqrt(
                sum(a * a for a in centered_i) * sum(b * b for b in centered_q)
            )
            self.assertAlmostEqual(correlation, math.sin(math.radians(degrees)), places=12)
            irrs.append(metrics(signal, tone)[3])
        self.assertGreater(irrs[0], irrs[1])
        self.assertGreater(irrs[1], irrs[2])

    def test_broken_global_rotation_preserves_image_and_shear_recovery(self):
        tone = build_tone()
        phase_error = math.radians(8)
        phase_impaired = impair(tone, phase_error_rad=phase_error)
        before = metrics(phase_impaired, tone)
        broken = [value * cmath.exp(-1j * phase_error) for value in phase_impaired]
        broken_metrics = metrics(broken, tone)
        corrected, *_ = correct(phase_impaired)
        recovered = metrics(corrected, tone)

        self.assertAlmostEqual(broken_metrics[1], before[1], places=12)
        self.assertAlmostEqual(broken_metrics[2], before[2], places=12)
        self.assertAlmostEqual(broken_metrics[3], before[3], places=11)
        self.assertGreater(recovered[3], broken_metrics[3] + 200)
        broken_section = self.experiment.split("%% Broken case", 1)[1].split(
            "%% Retained workspace results", 1
        )[0]
        self.assertIn("broken_rotated_iq_v", broken_section)
        self.assertIn("phase_corrected_q_v", self.experiment)

    def test_malformed_controls_and_resource_ceilings(self):
        for key, value in (
            ("random_seed", True),
            ("fs_hz", math.nan),
            ("record_sample_count", 4095),
            ("tone_frequency_hz", complex(160, 1)),
            ("tone_amplitude_v", 0.0),
            ("noise_rms_v", -0.1),
            ("dc_i_v", 0.13),
            ("dc_q_v", math.inf),
            ("i_gain", 0.0),
            ("q_gain", 1.0),
            ("quadrature_error_deg", 45.0),
            ("i_gain_sweep", (1.0, 1.1, 1.31)),
            ("quadrature_error_sweep_deg", (0.0, 5.0, 45.0)),
            ("max_record_samples", 8192),
            ("max_fft_length", 8192),
            ("max_sweep_cases", 4),
            ("max_stored_numeric_values", 720000),
            ("max_figure_groups", 7),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_controls(**{key: value})
        with self.assertRaises(ValueError):
            validate_controls(unknown_control=1)

    def test_validation_precedes_random_signal_fft_cleanup_and_figure_work(self):
        validation_end = self.experiment.index("% Validation succeeded:")
        for marker in (
            "RandStream(",
            "time_s = (0:record_sample_count-1)/fs_hz;",
            "fft(",
            "close(findall(",
            "figure('Name'",
        ):
            self.assertGreater(self.experiment.index(marker), validation_end, marker)
        self.assertIn("estimated_stored_numeric_values", self.experiment[:validation_end])
        self.assertIn("max_figure_groups = 6;", self.experiment[:validation_end])
        self.assertIn("workspace_vector_equivalents = 52;", self.experiment[:validation_end])
        self.assertIn("figure_vector_equivalents = 24;", self.experiment[:validation_end])
        self.assertIn("resource_safety_vector_equivalents = 4;", self.experiment[:validation_end])
        self.assertIn("max_stored_numeric_values = 360000;", self.experiment[:validation_end])
        self.assertLessEqual(4096 * (52 + 24 + 4), 360000)

    def test_plot_metric_result_and_unit_inventory_is_complete(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 6)
        self.assertEqual(self.experiment.count("'Tag', 'P19'"), 7)
        for label in (
            "I (V)", "Q (V)", "Signed frequency (Hz)",
            "Magnitude (dB re 1 V)",
        ):
            self.assertIn(label, self.experiment)
        for result in (
            "results.case_dc_dbc",
            "results.case_irr_db",
            "results.case_iq_correlation",
            "results.estimated_dc_v",
            "results.estimated_i_gain",
            "results.estimated_q_gain",
            "results.estimated_quadrature_error_deg",
            "results.stage_irr_db",
            "results.gain_sweep_irr_db",
            "results.phase_sweep_irr_db",
            "results.broken_irr_db",
        ):
            self.assertIn(result, self.experiment)

    def test_content_is_concept_first_complete_and_runtime_claim_boundary_is_honest(self):
        lowered = self.all_content.lower()
        for placeholder in ("todo", "tbd", "placeholder"):
            self.assertNotIn(placeholder, lowered)
        for phrase in (
            "physical mental model",
            "limiting cases",
            "radar connection",
            "common interpretation mistakes",
            "quadrature shear",
        ):
            self.assertIn(phrase, self.lesson.lower())
        for heading in (
            "## Baseline",
            "## Correction stages",
            "## Sweep 1",
            "## Sweep 2",
            "## Broken case",
            "## Completion handoff",
        ):
            self.assertIn(heading, self.walkthrough)
        self.assertIn("## Teach-back completion", self.checks)
        self.assertIn("P18", self.lesson)
        self.assertTrue(EVIDENCE.is_file())
        evidence = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("does **not** claim MATLAB or Octave execution", evidence)
        self.assertIn("Acceptance mapping", evidence)
        self.assertIn("Residual risks and unperformed validation", evidence)

    def test_no_unexplained_black_box_and_base_matlab_compatibility(self):
        lowered = self.experiment.lower()
        for opaque in (
            "iqimbal", "comm.", "dsp.", "rf.", "helper", "correctiq",
            "hilbert(", "pwelch(", "spectrogram(", "periodogram(",
        ):
            self.assertNotIn(opaque, lowered)
        for unsafe in (
            "input(", "pause(", "while ", "timer(", "parfor ", "parfeval(",
            "fopen(", "webread(", "audioplayer(", "sound(", "system(",
            "close all", "clear all", "clearvars",
        ):
            self.assertNotIn(unsafe, lowered)
        self.assertNotRegex(lowered, r"\b(?:read|write)(?:matrix|table)\s*\(")

    def test_timeout_cancellation_isolation_recovery_and_rollback_contracts(self):
        self.assertEqual(self.experiment.count("for sweep_index ="), 2)
        self.assertEqual(self.experiment.count("for case_index ="), 4)
        self.assertEqual(self.experiment.count("for stage_index ="), 2)
        self.assertNotIn("while ", self.experiment.lower())
        self.assertIn("Ctrl+C", self.experiment)
        self.assertIn("Ctrl+C", self.walkthrough)
        self.assertIn("private seed", self.walkthrough)
        self.assertIn("global random stream", self.walkthrough)
        self.assertIn("P19-tagged figures", self.walkthrough)
        self.assertIn("partial P19 figure set", self.experiment)
        self.assertIn("empty/incomplete `results`", self.walkthrough)
        self.assertIn("Rerun from the top", self.walkthrough)
        self.assertIn("Rollback", self.walkthrough)
        self.assertIn("restores only P19's", self.walkthrough)
        self.assertIn("Preserve implemented P18", self.walkthrough)


if __name__ == "__main__":
    unittest.main()
