from __future__ import annotations

import cmath
import copy
import json
import math
import random
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/16-create-an-analytic-signal-with-the-hilbert-transform"
GUIDING_QUESTION = "How can a real waveform be represented by a complex envelope?"
REQUIRED_ARTIFACTS = (
    "README.md",
    "experiment.m",
    "lesson.md",
    "walkthrough.md",
    "checks.md",
)


def validate_p16_contract(root: Path) -> list[str]:
    errors: list[str] = []
    module = root / "modules/16-create-an-analytic-signal-with-the-hilbert-transform"
    for name in REQUIRED_ARTIFACTS:
        path = module / name
        if not path.is_file():
            errors.append(f"P16 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P16 empty {name}")

    manifest_path = root / "curriculum/modules.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return errors + [f"invalid manifest: {exc}"]
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    entries = [entry for entry in modules if isinstance(entry, dict) and entry.get("id") == "P16"]
    if len(entries) != 1:
        return errors + [f"expected one P16 manifest entry, found {len(entries)}"]
    entry = entries[0]
    expected = {
        "number": 16,
        "id": "P16",
        "title": "Create an Analytic Signal with the Hilbert Transform",
        "guiding_question": GUIDING_QUESTION,
        "phase": 2,
        "phase_title": "Fourier, Spectral, and I/Q Intuition",
        "slug": "create-an-analytic-signal-with-the-hilbert-transform",
        "folder": "modules/16-create-an-analytic-signal-with-the-hilbert-transform",
        "status": "implemented",
        "implementation_batch": "P16",
    }
    for key, value in expected.items():
        if entry.get(key) != value:
            errors.append(f"P16 {key} must be {value!r}")
    return errors


def dft(values: list[complex]) -> list[complex]:
    count = len(values)
    return [
        sum(value * cmath.exp(-2j * math.pi * k * n / count) for n, value in enumerate(values))
        for k in range(count)
    ]


def idft(values: list[complex]) -> list[complex]:
    count = len(values)
    return [
        sum(value * cmath.exp(2j * math.pi * k * n / count) for k, value in enumerate(values)) / count
        for n in range(count)
    ]


def analytic_signal(real_values: list[float]) -> tuple[list[complex], list[float]]:
    count = len(real_values)
    if count < 2 or count % 2:
        raise ValueError("analytic model requires a positive even record length")
    mask = [0.0] * count
    mask[0] = 1.0
    for index in range(1, count // 2):
        mask[index] = 2.0
    mask[count // 2] = 1.0
    spectrum = dft([complex(value) for value in real_values])
    return idft([value * gain for value, gain in zip(spectrum, mask)]), mask


def unwrap_phase(values: list[complex]) -> list[float]:
    wrapped = [cmath.phase(value) for value in values]
    unwrapped = [wrapped[0]]
    for value in wrapped[1:]:
        step = value - unwrapped[-1]
        step = (step + math.pi) % (2 * math.pi) - math.pi
        unwrapped.append(unwrapped[-1] + step)
    return unwrapped


def gate_phase_difference_frequency(
    raw_frequency_hz: list[float],
    magnitude_v: list[float],
    threshold_v: float,
    evaluation_mask: list[bool],
) -> tuple[list[float], list[bool]]:
    if not (
        len(raw_frequency_hz) == len(magnitude_v) == len(evaluation_mask)
    ):
        raise ValueError("frequency, magnitude, and evaluation records must align")
    reliable = [
        bool(
            index > 0
            and evaluation_mask[index]
            and magnitude_v[index - 1] >= threshold_v
            and magnitude_v[index] >= threshold_v
        )
        for index in range(len(raw_frequency_hz))
    ]
    gated = [
        value if is_reliable else float("nan")
        for value, is_reliable in zip(raw_frequency_hz, reliable)
    ]
    return gated, reliable


def validate_controls(**overrides: object) -> None:
    controls: dict[str, object] = {
        "random_seed": 1016,
        "fs_hz": 2048.0,
        "record_sample_count": 4096,
        "carrier_frequency_hz": 240.0,
        "modulation_rates_hz": [2.0, 3.0],
        "envelope_depth_sweep": [0.20, 0.60, 0.90],
        "phase_deviation_sweep_rad": [0.20, 0.60, 1.20],
        "notch_center_s": 1.0,
        "notch_width_s": 0.025,
        "minimum_envelope_v": 0.001,
        "broken_noise_rms_v": 0.010,
        "threshold_v": 0.05,
        "max_record_samples": 4096,
        "max_fft_length": 4096,
        "max_sweep_cases": 3,
        "max_stored_numeric_values": 250000,
        "max_figure_groups": 5,
    }
    controls.update(overrides)

    seed = controls["random_seed"]
    fs = controls["fs_hz"]
    count = controls["record_sample_count"]
    carrier = controls["carrier_frequency_hz"]
    rates = controls["modulation_rates_hz"]
    envelope_sweep = controls["envelope_depth_sweep"]
    phase_sweep = controls["phase_deviation_sweep_rad"]
    numeric_scalars = (seed, fs, count, carrier)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in numeric_scalars):
        raise ValueError("scalar controls must be numeric and nonlogical")
    if any(not math.isfinite(float(value)) for value in numeric_scalars):
        raise ValueError("scalar controls must be finite")
    if int(seed) != seed or seed < 0 or seed > 2**32 - 1:
        raise ValueError("invalid seed")
    if fs <= 0 or count != 4096 or int(count) != count or int(count) % 2:
        raise ValueError("invalid sampling record")
    if not isinstance(rates, list) or rates != [2.0, 3.0]:
        raise ValueError("invalid modulation rates")
    if carrier <= 5 * max(rates) or carrier + max(phase_sweep) * rates[1] >= fs / 2:
        raise ValueError("carrier/modulation outside supported band")
    if envelope_sweep != [0.20, 0.60, 0.90] or phase_sweep != [0.20, 0.60, 1.20]:
        raise ValueError("noncanonical sweep")
    if any(isinstance(value, bool) or not math.isfinite(value) for value in envelope_sweep + phase_sweep):
        raise ValueError("malformed sweep")
    duration = count / fs
    center = controls["notch_center_s"]
    width = controls["notch_width_s"]
    minimum = controls["minimum_envelope_v"]
    noise = controls["broken_noise_rms_v"]
    threshold = controls["threshold_v"]
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
           for value in (center, width, minimum, noise, threshold)):
        raise ValueError("malformed broken case")
    if not (0 < center < duration) or center * fs != int(center * fs):
        raise ValueError("invalid notch center")
    if not (4 / fs < width < duration / 10):
        raise ValueError("invalid notch width")
    if not (0 < minimum < 0.01 and minimum < noise <= 0.02):
        raise ValueError("invalid broken amplitude/noise relationship")
    if not (noise < threshold < 1 - max(envelope_sweep)):
        raise ValueError("invalid reliability threshold")
    ceilings = (
        controls["max_record_samples"],
        controls["max_fft_length"],
        controls["max_sweep_cases"],
        controls["max_stored_numeric_values"],
        controls["max_figure_groups"],
    )
    if ceilings != (4096, 4096, 3, 250000, 5):
        raise ValueError("resource ceiling changed")


class P16ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.experiment = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")
        cls.all_content = "\n".join(
            (cls.readme, cls.experiment, cls.lesson, cls.walkthrough, cls.checks)
        )
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))

    def fixture_copy(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        fixture_root = Path(temp_dir.name)
        fixture_module = fixture_root / MODULE.relative_to(ROOT)
        fixture_module.mkdir(parents=True)
        for name in REQUIRED_ARTIFACTS:
            (fixture_module / name).write_text(
                (MODULE / name).read_text(encoding="utf-8"), encoding="utf-8"
            )
        fixture_manifest = fixture_root / "curriculum/modules.json"
        fixture_manifest.parent.mkdir(parents=True)
        fixture_manifest.write_text(json.dumps(self.manifest), encoding="utf-8")
        return temp_dir, fixture_root

    def test_artifacts_manifest_identity_dependency_and_public_catalogs(self):
        self.assertEqual(validate_p16_contract(ROOT), [])
        entries = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(entries["P15"]["status"], "implemented")
        self.assertEqual(entries["P16"]["status"], "implemented")
        for text in (self.readme, self.lesson, self.walkthrough, self.checks):
            self.assertIn(GUIDING_QUESTION, text)
        self.assertIn("P11", self.readme)
        self.assertIn("P12", self.readme)
        self.assertIn("P15", self.readme)
        self.assertRegex((ROOT / "modules/README.md").read_text(), r"\| \[P16\].*\| implemented \|")

    def test_contract_rejects_missing_empty_duplicate_nonlist_and_wrong_identity(self):
        temp_dir, fixture_root = self.fixture_copy()
        try:
            (fixture_root / MODULE.relative_to(ROOT) / "checks.md").unlink()
            self.assertIn("P16 missing checks.md", validate_p16_contract(fixture_root))
        finally:
            temp_dir.cleanup()

        temp_dir, fixture_root = self.fixture_copy()
        try:
            (fixture_root / MODULE.relative_to(ROOT) / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("P16 empty lesson.md", validate_p16_contract(fixture_root))
        finally:
            temp_dir.cleanup()

        for mutation, expected in (
            (lambda data: data["modules"].append(copy.deepcopy(data["modules"][15])),
             "expected one P16 manifest entry, found 2"),
            (lambda data: data.__setitem__("modules", {}), "manifest modules must be a list"),
            (lambda data: data["modules"][15].__setitem__("guiding_question", "Changed"),
             "P16 guiding_question must be"),
        ):
            temp_dir, fixture_root = self.fixture_copy()
            try:
                manifest_path = fixture_root / "curriculum/modules.json"
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                mutation(data)
                manifest_path.write_text(json.dumps(data), encoding="utf-8")
                self.assertTrue(
                    any(expected in error for error in validate_p16_contract(fixture_root))
                )
            finally:
                temp_dir.cleanup()

    def test_deterministic_visible_controls_and_explicit_base_matlab_operation(self):
        required_markers = (
            "random_seed = 1016;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "randn(private_stream",
            "analytic_fft_mask(1) = 1;",
            "analytic_fft_mask(2:record_sample_count/2) = 2;",
            "analytic_fft_mask(record_sample_count/2 + 1) = 1;",
            "ifft(real_spectrum_v.*analytic_fft_mask)",
            "abs(analytic_signal_v)",
            "unwrap(angle(analytic_signal_v))",
            "diff(recovered_phase_rad)*fs_hz/(2*pi)",
        )
        for marker in required_markers:
            self.assertIn(marker, self.experiment)
        self.assertNotIn("hilbert(", self.experiment.lower())
        self.assertNotIn("envelope(", self.experiment.lower())
        self.assertNotRegex(self.experiment.lower(), r"\brng\s*\(")

    def test_malformed_controls_and_resource_ceilings_fail_independently(self):
        validate_controls()
        invalid_cases = (
            {"random_seed": True},
            {"random_seed": float("nan")},
            {"fs_hz": float("inf")},
            {"record_sample_count": 4095},
            {"carrier_frequency_hz": 1023.0},
            {"modulation_rates_hz": [2.0, float("nan")]},
            {"envelope_depth_sweep": [0.2, 0.6]},
            {"phase_deviation_sweep_rad": [0.2, 0.6, True]},
            {"notch_center_s": -1.0},
            {"notch_width_s": 0.5},
            {"minimum_envelope_v": 0.02},
            {"broken_noise_rms_v": 0.0001},
            {"threshold_v": 0.2},
            {"max_record_samples": 4095},
            {"max_fft_length": 8192},
            {"max_sweep_cases": 100},
            {"max_stored_numeric_values": 249999},
            {"max_figure_groups": 4},
        )
        for controls in invalid_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

        validation_position = self.experiment.index("%% Validate controls")
        work_positions = (
            self.experiment.index("RandStream("),
            self.experiment.index("real_spectrum_v = fft("),
            self.experiment.index("figure('Name'"),
        )
        self.assertTrue(all(validation_position < position for position in work_positions))
        self.assertIn("estimated_stored_numeric_values <= max_stored_numeric_values", self.experiment)
        for scalar_guard in (
            "~islogical(carrier_frequency_hz)",
            "~islogical(envelope_modulation_frequency_hz)",
            "~islogical(phase_modulation_frequency_hz)",
            "~islogical(broken_notch_center_s)",
            "~islogical(broken_notch_width_s)",
            "~islogical(broken_minimum_envelope_v)",
            "~islogical(broken_noise_rms_v)",
            "~islogical(reliability_threshold_v)",
        ):
            self.assertIn(scalar_guard, self.experiment)

    def test_fft_mask_reconstructs_real_tone_and_removes_negative_frequency(self):
        count = 64
        tone_bin = 7
        real_values = [math.cos(2 * math.pi * tone_bin * n / count + 0.2) for n in range(count)]
        analytic, mask = analytic_signal(real_values)
        self.assertEqual(mask[0], 1.0)
        self.assertTrue(all(value == 2.0 for value in mask[1 : count // 2]))
        self.assertEqual(mask[count // 2], 1.0)
        self.assertTrue(all(value == 0.0 for value in mask[count // 2 + 1 :]))
        self.assertLess(max(abs(value.real - original) for value, original in zip(analytic, real_values)), 1e-12)
        self.assertLess(max(abs(abs(value) - 1.0) for value in analytic), 1e-12)
        spectrum = dft(analytic)
        positive = sum(abs(value) ** 2 for value in spectrum[1 : count // 2])
        negative = sum(abs(value) ** 2 for value in spectrum[count // 2 + 1 :])
        self.assertGreater(positive / max(negative, 1e-24), 1e20)

    def test_independent_envelope_phase_and_frequency_recovery(self):
        count = 256
        fs_hz = 256.0
        carrier_hz = 32.0
        envelope_rate_hz = 2.0
        phase_rate_hz = 3.0
        depth = 0.6
        beta = 0.6
        time_s = [n / fs_hz for n in range(count)]
        envelope = [1 + depth * math.cos(2 * math.pi * envelope_rate_hz * t) for t in time_s]
        phase = [2 * math.pi * carrier_hz * t + 0.35 + beta * math.sin(2 * math.pi * phase_rate_hz * t) for t in time_s]
        real_values = [amplitude * math.cos(angle) for amplitude, angle in zip(envelope, phase)]
        analytic, _ = analytic_signal(real_values)
        recovered_envelope = [abs(value) for value in analytic]
        recovered_phase = unwrap_phase(analytic)
        recovered_frequency = [
            (recovered_phase[index] - recovered_phase[index - 1]) * fs_hz / (2 * math.pi)
            for index in range(1, count)
        ]
        designed_midpoint_frequency = [
            carrier_hz + beta * phase_rate_hz * math.cos(2 * math.pi * phase_rate_hz * ((index - 0.5) / fs_hz))
            for index in range(1, count)
        ]
        envelope_rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(recovered_envelope, envelope)) / count)
        frequency_rmse = math.sqrt(
            sum((a - b) ** 2 for a, b in zip(recovered_frequency, designed_midpoint_frequency)) / (count - 1)
        )
        self.assertLess(envelope_rmse, 1e-10)
        self.assertLess(frequency_rmse, 0.01)

    def test_two_one_variable_sweeps_preserve_their_intended_invariants(self):
        self.assertIn("%% Sweep 1: change only envelope modulation depth", self.experiment)
        self.assertIn("envelope_depth_sweep = [0.20 0.60 0.90];", self.experiment)
        self.assertIn("case_envelope_v = 1 + case_depth", self.experiment)
        self.assertIn("case_real_v = case_envelope_v.*cos(designed_phase_rad)", self.experiment)
        for actual, expected in zip(
            [1 - depth for depth in (0.2, 0.6, 0.9)], [0.8, 0.4, 0.1]
        ):
            self.assertAlmostEqual(actual, expected, places=12)

        self.assertIn("%% Sweep 2: change only phase-deviation index", self.experiment)
        self.assertIn("phase_deviation_sweep_rad = [0.20 0.60 1.20];", self.experiment)
        self.assertIn("case_real_v = designed_envelope_v.*cos(case_phase_rad)", self.experiment)
        deviations = [beta * 3.0 for beta in (0.2, 0.6, 1.2)]
        self.assertEqual(deviations, [0.6000000000000001, 1.7999999999999998, 3.5999999999999996])

    def test_independent_broken_case_exposes_and_gates_low_amplitude_frequency(self):
        count = 256
        fs_hz = 256.0
        carrier_hz = 32.0
        rng = random.Random(1016)
        time_s = [n / fs_hz for n in range(count)]
        designed_phase = [2 * math.pi * carrier_hz * t + 0.6 * math.sin(2 * math.pi * 3 * t) for t in time_s]
        designed_frequency = [carrier_hz + 1.8 * math.cos(2 * math.pi * 3 * t) for t in time_s]
        envelope = [1 - 0.999 * math.exp(-0.5 * ((t - 0.5) / 0.025) ** 2) for t in time_s]
        real_values = [
            amplitude * math.cos(phase) + 0.01 * rng.gauss(0.0, 1.0)
            for amplitude, phase in zip(envelope, designed_phase)
        ]
        analytic, _ = analytic_signal(real_values)
        magnitude = [abs(value) for value in analytic]
        phase = unwrap_phase(analytic)
        raw_frequency = [float("nan")] + [
            (phase[index] - phase[index - 1]) * fs_hz / (2 * math.pi)
            for index in range(1, count)
        ]
        low = [index for index in range(1, count) if magnitude[index] < 0.05]
        valid = [
            index
            for index in range(16, count - 16)
            if magnitude[index] >= 0.05 and magnitude[index - 1] >= 0.05
        ]
        threshold_exits = [
            index
            for index in range(1, count)
            if magnitude[index] >= 0.05 and magnitude[index - 1] < 0.05
        ]
        self.assertGreater(len(low), 0)
        low_max_error = max(abs(raw_frequency[index] - designed_frequency[index]) for index in low)
        valid_rmse = math.sqrt(
            sum((raw_frequency[index] - designed_frequency[index]) ** 2 for index in valid) / len(valid)
        )
        self.assertGreater(low_max_error, 10.0)
        self.assertLess(valid_rmse, low_max_error / 4)
        self.assertGreater(len(threshold_exits), 0)
        self.assertIn("[false broken_magnitude_reliable_mask(1:end-1)]", self.experiment)
        self.assertIn("any(broken_low_amplitude_mask)", self.experiment)
        self.assertIn("any(broken_reliable_mask)", self.experiment)
        self.assertIn("broken_recovered_frequency_hz(~broken_reliable_mask) = NaN;", self.experiment)

    def test_phase_difference_gate_behavior_rejects_both_low_amplitude_transitions(self):
        raw_frequency_hz = [float("nan"), 241.0, 900.0, -700.0, 239.0, 800.0]
        magnitude_v = [0.20, 0.20, 0.01, 0.20, 0.20, 0.01]
        evaluation_mask = [False, True, True, True, True, True]

        gated_frequency_hz, reliable = gate_phase_difference_frequency(
            raw_frequency_hz,
            magnitude_v,
            threshold_v=0.05,
            evaluation_mask=evaluation_mask,
        )

        self.assertEqual(reliable, [False, True, False, False, True, False])
        self.assertTrue(math.isnan(gated_frequency_hz[0]))
        self.assertEqual(gated_frequency_hz[1], 241.0)
        self.assertTrue(math.isnan(gated_frequency_hz[2]))  # enters the notch
        self.assertTrue(math.isnan(gated_frequency_hz[3]))  # exits the notch
        self.assertEqual(gated_frequency_hz[4], 239.0)
        self.assertTrue(math.isnan(gated_frequency_hz[5]))
        self.assertIn(
            "broken_magnitude_reliable_mask & ...\n    "
            "[false broken_magnitude_reliable_mask(1:end-1)] & evaluation_mask",
            self.experiment,
        )

    def test_plot_metric_result_and_unit_inventory_is_complete(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 5)
        for unit_label in (
            "Time (s)",
            "Amplitude (V)",
            "Envelope (V)",
            "Unwrapped phase (rad)",
            "Frequency (Hz)",
            "Magnitude (dB re 1 V)",
        ):
            self.assertIn(unit_label, self.experiment)
        for result in (
            "results.analytic_signal_v",
            "results.envelope_rmse_v",
            "results.instantaneous_frequency_rmse_hz",
            "results.negative_frequency_suppression_db",
            "results.envelope_depth_sweep",
            "results.phase_deviation_sweep_rad",
            "results.broken_reliable_mask",
            "results.broken_low_amplitude_max_error_hz",
        ):
            self.assertIn(result, self.experiment)

    def test_timeout_cancellation_isolation_compatibility_and_recovery_contracts(self):
        lowered = self.experiment.lower()
        forbidden = (
            "input(", "pause(", "waitfor(", "uiwait(", "timer(", "parfor ",
            "backgroundpool", "fopen(", "writematrix(", "save(", "webread(",
            "webwrite(", "audioplayer(", "sound(", "while ", "system(", "unix(",
            "xline(", "yline(",
        )
        for marker in forbidden:
            self.assertNotIn(marker, lowered)
        self.assertIn("findall(groot, 'Type', 'figure', 'Tag', 'P16')", self.experiment)
        self.assertIn("clear results;", self.experiment)
        self.assertLess(self.experiment.index("clear results;"), self.experiment.index("%% Validate controls"))
        self.assertNotIn("RandStream.setGlobalStream", self.experiment)
        for text in (self.readme, self.lesson, self.walkthrough, self.checks):
            self.assertIn("Ctrl+C", text)
            self.assertRegex(text.lower(), r"rerun|rerunning")
        self.assertIn("base MATLAB", self.readme)
        self.assertIn("restores only P16", self.walkthrough)
        self.assertRegex(self.checks, r"Preserve\s+P15")

    def test_content_is_concept_first_complete_and_has_no_runtime_overclaim(self):
        for artifact_name in REQUIRED_ARTIFACTS:
            content = (MODULE / artifact_name).read_text(encoding="utf-8")
            self.assertNotRegex(content, r"\bTODO\b|\bTBD\b|coming soon|placeholder")
        self.assertIn("## Limiting cases", self.lesson)
        self.assertIn("## Common interpretation mistakes", self.lesson)
        self.assertIn("## Sweep 1", self.walkthrough)
        self.assertIn("## Sweep 2", self.walkthrough)
        self.assertIn("## Broken case", self.walkthrough)
        self.assertIn("## Teach-back completion", self.checks)
        self.assertIn("does not call", self.readme)
        self.assertIn("static", self.readme)
        evidence = (ROOT / "docs/evidence/P16-2026-08-02.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("does **not** claim MATLAB or Octave execution", evidence)
        self.assertIn("## Acceptance mapping", evidence)
        self.assertIn("## Exact commands and results", evidence)
        unsupported_claims = (
            "MATLAB execution passed",
            "rendered figures verified",
            "hardware validated",
            "field validated",
            "production validated",
        )
        for claim in unsupported_claims:
            self.assertNotIn(claim, self.all_content)


if __name__ == "__main__":
    unittest.main()
