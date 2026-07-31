from __future__ import annotations

import cmath
import copy
import json
import math
import re
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "01-build-a-sinusoid-and-a-complex-phasor"
MANIFEST_PATH = ROOT / "curriculum" / "modules.json"
REQUIRED_ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
GUIDING_QUESTION = (
    "How do amplitude, frequency, and phase appear in time and in the complex plane?"
)


def validate_p01_contract(module_dir: Path, manifest: dict) -> list[str]:
    """Return deterministic P01 contract failures for positive and negative tests."""
    errors: list[str] = []
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return ["manifest modules must be a list"]
    if any(not isinstance(entry, dict) for entry in modules):
        return ["manifest module entries must be objects"]

    matches = [entry for entry in modules if entry.get("id") == "P01"]
    if len(matches) != 1:
        return [f"expected one P01 manifest entry, found {len(matches)}"]

    entry = matches[0]
    expected_identity = {
        "number": 1,
        "title": "Build a Sinusoid and a Complex Phasor",
        "guiding_question": GUIDING_QUESTION,
        "folder": "modules/01-build-a-sinusoid-and-a-complex-phasor",
        "status": "implemented",
        "implementation_batch": "P01",
    }
    for field, expected in expected_identity.items():
        if entry.get(field) != expected:
            errors.append(f"P01 {field} must be {expected!r}")

    for name in REQUIRED_ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P01 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P01 empty {name}")
    return errors


class P01ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.experiment = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")

    def scalar_assignment(self, name: str) -> float:
        match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*([0-9.]+)\s*;", self.experiment)
        self.assertIsNotNone(match, f"missing visible scalar assignment for {name}")
        return float(match.group(1))

    def test_artifact_completeness_and_manifest_identity(self):
        self.assertEqual(validate_p01_contract(MODULE, self.manifest), [])
        self.assertIn(GUIDING_QUESTION, self.readme)
        self.assertIn(GUIDING_QUESTION, self.lesson)
        self.assertIn(GUIDING_QUESTION, self.walkthrough)
        self.assertIn(GUIDING_QUESTION, self.checks)

    def test_contract_validator_rejects_missing_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied_module = Path(temporary) / MODULE.name
            shutil.copytree(MODULE, copied_module)
            (copied_module / "checks.md").unlink()
            errors = validate_p01_contract(copied_module, self.manifest)
            self.assertIn("P01 missing checks.md", errors)

        malformed_manifest = copy.deepcopy(self.manifest)
        malformed_manifest["modules"][0]["guiding_question"] = "placeholder"
        malformed_manifest["modules"][0]["status"] = "scaffolded"
        errors = validate_p01_contract(MODULE, malformed_manifest)
        self.assertIn(f"P01 guiding_question must be {GUIDING_QUESTION!r}", errors)
        self.assertIn("P01 status must be 'implemented'", errors)

        self.assertEqual(validate_p01_contract(MODULE, {"modules": "not-a-list"}), [
            "manifest modules must be a list"
        ])
        self.assertEqual(validate_p01_contract(MODULE, {"modules": ["not-an-object"]}), [
            "manifest module entries must be objects"
        ])

    def test_deterministic_baseline_and_broken_case_math(self):
        amplitude = self.scalar_assignment("A")
        frequency_hz = self.scalar_assignment("f0")
        sample_rate_hz = self.scalar_assignment("fs")
        duration_s = self.scalar_assignment("duration")
        phase_rad = math.pi / 6

        self.assertRegex(self.experiment, r"random_seed\s*=\s*84\s*;")
        self.assertIn("rng(random_seed, 'twister')", self.experiment)

        sample_count = round(duration_s * sample_rate_hz)
        times = [sample / sample_rate_hz for sample in range(sample_count)]
        cosine = [
            amplitude * math.cos(2 * math.pi * frequency_hz * time + phase_rad)
            for time in times
        ]
        phasor = [
            amplitude * cmath.exp(1j * (2 * math.pi * frequency_hz * time + phase_rad))
            for time in times
        ]
        self.assertLess(max(abs(real - complex_value.real) for real, complex_value in zip(cosine, phasor)), 1e-12)
        self.assertLess(max(abs(abs(value) - amplitude) for value in phasor), 1e-12)

        broken_rate_hz = self.scalar_assignment("fs_bad")
        for matlab_expression in (
            "signed_alias_frequency = f0 - round(f0/fs_bad)*fs_bad;",
            "apparent_alias_frequency = abs(signed_alias_frequency);",
            "if signed_alias_frequency < 0",
            "apparent_alias_phase = -phi;",
            "apparent_alias_phase = phi;",
            "x_alias_at_samples = A*cos(2*pi*apparent_alias_frequency*t_bad + apparent_alias_phase);",
        ):
            self.assertIn(matlab_expression, self.experiment)

        signed_alias_hz = frequency_hz - round(frequency_hz / broken_rate_hz) * broken_rate_hz
        alias_phase_rad = math.copysign(phase_rad, signed_alias_hz)
        broken_times = [sample / broken_rate_hz for sample in range(round(duration_s * broken_rate_hz))]
        true_samples = [
            amplitude * math.cos(2 * math.pi * frequency_hz * time + phase_rad)
            for time in broken_times
        ]
        alias_samples = [
            amplitude * math.cos(2 * math.pi * abs(signed_alias_hz) * time + alias_phase_rad)
            for time in broken_times
        ]
        self.assertLess(max(abs(true - alias) for true, alias in zip(true_samples, alias_samples)), 1e-12)
        self.assertLess(broken_rate_hz, 2 * frequency_hz)

        zero_alias_frequency_hz = broken_rate_hz
        zero_alias_phase_rad = phase_rad
        zero_alias_times = [
            sample / broken_rate_hz
            for sample in range(round(duration_s * broken_rate_hz))
        ]
        zero_alias_true = [
            amplitude
            * math.cos(2 * math.pi * zero_alias_frequency_hz * time + phase_rad)
            for time in zero_alias_times
        ]
        zero_alias_model = [
            amplitude * math.cos(zero_alias_phase_rad)
            for _ in zero_alias_times
        ]
        self.assertLess(
            max(abs(true - alias) for true, alias in zip(zero_alias_true, zero_alias_model)),
            1e-12,
        )

    def test_sweeps_broken_case_metrics_and_guards_are_explicit(self):
        expected_markers = (
            "Parameter sweep 1 - amplitude",
            "amplitudes = [0.5 1.0 1.5]",
            "Parameter sweep 2 - phase",
            "phases = [0 pi/4 pi/2]",
            "Parameter sweep 3 - frequency",
            "frequencies = [2.5 5.0 10.0]",
            "Deliberately broken case - undersampling",
            "signed_alias_frequency",
            "max_projection_error",
            "max_radius_error",
            "alias_sample_error",
            "assert(fs_bad < 2*f0",
            "assert(bad_sample_count <= max_baseline_samples",
        )
        for marker in expected_markers:
            self.assertIn(marker, self.experiment)

        for control in ("A", "f0", "phi", "fs", "duration"):
            self.assertRegex(
                self.experiment,
                rf"assert\([^;]*{control}",
                f"missing fail-fast guard involving {control}",
            )

    def test_rotation_sign_and_each_sweep_mechanism(self):
        for matlab_expression in (
            "z_positive = A*exp(1j*(2*pi*f0*t_direction + phi));",
            "z_negative = A*exp(1j*(-2*pi*f0*t_direction + phi));",
            "positive_step_angle = angle(conj(z_positive(1))*z_positive(2));",
            "negative_step_angle = angle(conj(z_negative(1))*z_negative(2));",
            "z_amplitude = amplitudes(k)*exp(1j*theta);",
            "x_phase = A*cos(2*pi*f0*t + phases(k));",
            "plot(A*cos(phases(k)), A*sin(phases(k)), 'o', ...",
            "x_frequency = A*cos(2*pi*frequencies(k)*t + phi);",
            "completed_rotations = frequencies(k)*t;",
        ):
            self.assertIn(matlab_expression, self.experiment)

        amplitude = self.scalar_assignment("A")
        frequency_hz = self.scalar_assignment("f0")
        sample_rate_hz = self.scalar_assignment("fs")
        phase_rad = math.pi / 6
        sample_step_s = 1 / sample_rate_hz

        positive = [
            amplitude * cmath.exp(1j * (2 * math.pi * frequency_hz * time + phase_rad))
            for time in (0, sample_step_s)
        ]
        negative = [
            amplitude * cmath.exp(1j * (-2 * math.pi * frequency_hz * time + phase_rad))
            for time in (0, sample_step_s)
        ]
        positive_cross = (positive[0].conjugate() * positive[1]).imag
        negative_cross = (negative[0].conjugate() * negative[1]).imag
        self.assertGreater(positive_cross, 0)
        self.assertLess(negative_cross, 0)

        for requested_radius in (0.5, 1.0, 1.5):
            swept_value = requested_radius * cmath.exp(1j * phase_rad)
            self.assertAlmostEqual(abs(swept_value), requested_radius)

        for requested_phase in (0, math.pi / 4, math.pi / 2):
            start = amplitude * cmath.exp(1j * requested_phase)
            self.assertAlmostEqual(start.real, amplitude * math.cos(requested_phase))
            self.assertAlmostEqual(start.imag, amplitude * math.sin(requested_phase))

        observation_s = 0.4
        self.assertEqual(
            [frequency * observation_s for frequency in (2.5, 5.0, 10.0)],
            [1.0, 2.0, 4.0],
        )

    def test_labeled_outputs_and_concept_first_documentation(self):
        for label in (
            "Time (s)",
            "Amplitude (a.u.)",
            "In-phase amplitude, I (a.u.)",
            "Quadrature amplitude, Q (a.u.)",
            "Angle advanced (rotations)",
            "samples per cycle",
            "Nyquist limit",
        ):
            self.assertIn(label, self.experiment)

        combined_docs = "\n".join((self.lesson, self.walkthrough, self.checks))
        for concept in (
            "radius",
            "rotation rate",
            "starting point",
            "projection",
            "positive frequency",
            "negative frequency",
            "broken case",
            "base MATLAB",
        ):
            self.assertIn(concept.lower(), combined_docs.lower())

        for required_section in (
            "## Baseline",
            "## Sweep 1",
            "## Sweep 2",
            "## Sweep 3",
            "## Broken case",
            "## Recovery",
        ):
            self.assertIn(required_section, self.walkthrough)
        self.assertIn("## Predict, then verify", self.checks)
        self.assertIn("## Teach-back completion", self.checks)

    def test_no_placeholder_or_unexplained_black_box_regression(self):
        implementation_text = "\n".join(
            (self.experiment, self.lesson, self.walkthrough, self.checks)
        )
        self.assertIsNone(
            re.search(r"\b(TODO|TBD|FIXME|lorem ipsum|coming soon)\b", implementation_text, re.I)
        )
        for prohibited_call in (
            "awgn(",
            "hilbert(",
            "phased.",
            "dsp.",
            "comm.",
            "Signal Processing Toolbox",
        ):
            self.assertNotIn(prohibited_call, implementation_text)
        self.assertIn("x = A*cos(theta);", self.experiment)
        self.assertIn("z = A*exp(1j*theta);", self.experiment)
        self.assertIn("base MATLAB only", self.readme)
        self.assertIn("requires no toolbox", self.lesson)

    def test_resource_bounds_and_noninteractive_compatibility(self):
        sample_rate_hz = self.scalar_assignment("fs")
        duration_s = self.scalar_assignment("duration")
        max_baseline_samples = self.scalar_assignment("max_baseline_samples")
        self.assertEqual(max_baseline_samples, 5000)
        self.assertLessEqual(round(sample_rate_hz * duration_s), max_baseline_samples)
        self.assertIn(
            "assert(baseline_sample_count <= max_baseline_samples",
            self.experiment,
        )
        self.assertIn(
            "direction_sample_count = min(baseline_sample_count, ...",
            self.experiment,
        )
        self.assertIn(
            "max(2, floor(fs/(4*f0)) + 1)",
            self.experiment,
        )
        for guarded_rate_hz, guarded_duration_s in ((11, 1), (200, 0.01), (5000, 1)):
            baseline_count = round(guarded_rate_hz * guarded_duration_s)
            direction_count = min(
                baseline_count,
                max(2, math.floor(guarded_rate_hz / (4 * 5.0)) + 1),
            )
            self.assertGreaterEqual(direction_count, 2)
            self.assertLessEqual(direction_count, baseline_count)
            self.assertLessEqual(direction_count, 5000)
        self.assertLessEqual(self.experiment.count("figure("), 8)
        self.assertNotRegex(self.experiment, r"(?m)^\s*(while|parfor)\b")
        for unbounded_or_interactive_feature in ("pause(", "drawnow", "VideoWriter", "uicontrol"):
            self.assertNotIn(unbounded_or_interactive_feature, self.experiment)

    def test_sampling_guards_and_recovery_behavior(self):
        frequency_hz = self.scalar_assignment("f0")
        sample_rate_hz = self.scalar_assignment("fs")
        duration_s = self.scalar_assignment("duration")
        broken_rate_hz = self.scalar_assignment("fs_bad")
        max_baseline_samples = self.scalar_assignment("max_baseline_samples")

        self.assertIn("fs > 2*f0", self.experiment)
        self.assertIn("assert(fs_bad < 2*f0", self.experiment)
        self.assertRegex(
            self.experiment,
            r"assert\(isscalar\(fs_bad\) && isreal\(fs_bad\) && "
            r"isfinite\(fs_bad\) && fs_bad > 0",
        )
        self.assertIn(
            "assert(bad_sample_count <= max_baseline_samples",
            self.experiment,
        )

        def baseline_guard(
            amplitude: float,
            tone_hz: float,
            phase_rad: float | complex,
            rate_hz: float,
            record_s: float,
        ) -> bool:
            if not all(
                math.isfinite(value)
                for value in (amplitude, tone_hz, rate_hz, record_s)
            ):
                return False
            if isinstance(phase_rad, complex) or not math.isfinite(phase_rad):
                return False
            requested_samples = rate_hz * record_s
            rounded_samples = math.floor(requested_samples + 0.5)
            integer_record = abs(rounded_samples - requested_samples) < (
                10 * math.ulp(requested_samples)
            )
            return (
                amplitude > 0
                and tone_hz > 0
                and rate_hz > 2 * tone_hz
                and record_s > 0
                and rounded_samples >= 2
                and integer_record
                and rounded_samples <= max_baseline_samples
            )

        def broken_case_guard(rate_hz: float, record_s: float = duration_s) -> bool:
            if (
                not math.isfinite(rate_hz)
                or rate_hz <= 0
                or not math.isfinite(record_s)
                or record_s <= 0
            ):
                return False
            requested_samples = rate_hz * record_s
            rounded_samples = math.floor(requested_samples + 0.5)
            integer_record = abs(rounded_samples - requested_samples) < (
                10 * math.ulp(requested_samples)
            )
            return (
                rate_hz < 2 * frequency_hz
                and rounded_samples >= 2
                and integer_record
                and rounded_samples <= max_baseline_samples
            )

        valid_baseline = (1.0, frequency_hz, math.pi / 6, sample_rate_hz, duration_s)
        self.assertTrue(baseline_guard(*valid_baseline))
        self.assertFalse(baseline_guard(1.0, frequency_hz, math.pi / 6, 2 * frequency_hz, duration_s))
        self.assertFalse(baseline_guard(1.0, frequency_hz, math.pi / 6, math.nan, duration_s))
        self.assertFalse(baseline_guard(1.0, frequency_hz, math.pi / 6, sample_rate_hz, math.inf))
        self.assertFalse(baseline_guard(0, frequency_hz, math.pi / 6, sample_rate_hz, duration_s))
        self.assertFalse(baseline_guard(1.0, 0, math.pi / 6, sample_rate_hz, duration_s))
        self.assertFalse(baseline_guard(1.0, frequency_hz, complex(0, 1), sample_rate_hz, duration_s))
        self.assertTrue(
            baseline_guard(
                1.0,
                frequency_hz,
                math.pi / 6,
                sample_rate_hz,
                max_baseline_samples / sample_rate_hz,
            )
        )
        self.assertFalse(
            baseline_guard(
                1.0,
                frequency_hz,
                math.pi / 6,
                sample_rate_hz,
                (max_baseline_samples + 1) / sample_rate_hz,
            )
        )

        self.assertTrue(broken_case_guard(broken_rate_hz))
        self.assertFalse(broken_case_guard(0))
        self.assertFalse(broken_case_guard(math.nan))
        for recovered_rate_hz in (12, 20):
            self.assertFalse(broken_case_guard(recovered_rate_hz))
        self.assertIn(
            "early Nyquist assertion is expected to stop",
            self.walkthrough,
        )
        self.assertIn("Finally restore\n`fs_bad = 8`", self.walkthrough)
        self.assertIn(
            "`duration*fs_bad` is an integer from 2 through\n5000 samples",
            self.walkthrough,
        )

    def test_complex_controls_are_rejected_before_relational_arithmetic(self):
        guard_fragments = {
            "A": "isscalar(A) && isreal(A) && isfinite(A) && A > 0",
            "f0": "isscalar(f0) && isreal(f0) && isfinite(f0) && f0 > 0",
            "fs": "isscalar(fs) && isreal(fs) && isfinite(fs) && fs > 2*f0",
            "duration": (
                "isscalar(duration) && isreal(duration) && "
                "isfinite(duration) && duration > 0"
            ),
            "fs_bad": (
                "isscalar(fs_bad) && isreal(fs_bad) && "
                "isfinite(fs_bad) && fs_bad > 0"
            ),
        }
        for control, fragment in guard_fragments.items():
            self.assertIn(
                fragment,
                self.experiment,
                f"{control} must reject complex input before using >",
            )

        def positive_real_scalar(value: object) -> bool:
            return (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
                and value > 0
            )

        for malformed in (1 + 1j, complex(math.inf, 0), complex(1, math.nan)):
            with self.subTest(malformed=malformed):
                self.assertFalse(positive_real_scalar(malformed))
        for valid in (1, 0.5, 200.0):
            with self.subTest(valid=valid):
                self.assertTrue(positive_real_scalar(valid))

        self.assertIn("finite positive real amplitude and frequency", self.checks)
        self.assertIn("`fs_bad` must be finite, positive, and real", self.checks)


if __name__ == "__main__":
    unittest.main()
