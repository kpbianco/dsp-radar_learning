from __future__ import annotations

import cmath
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
MODULE = ROOT / "modules/36-measure-doppler-from-pulse-to-pulse-phase"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How does target velocity create coherent phase progression across pulses?"
SPEED_OF_LIGHT_MPS = 299_792_458.0
MAX_PULSE_COUNT = 128
MAX_SWEEP_CASES = 7
EXPECTED_IDENTITY = {
    "number": 36,
    "id": "P36",
    "title": "Measure Doppler from Pulse-to-Pulse Phase",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "measure-doppler-from-pulse-to-pulse-phase",
    "folder": "modules/36-measure-doppler-from-pulse-to-pulse-phase",
    "status": "implemented",
    "implementation_batch": "P36",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p36_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P36 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P36 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P36"]
    if len(matches) != 1:
        return errors + [f"expected one P36 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P36 {key} must be {expected!r}")
    return errors


def doppler_model(
    velocity_mps: float,
    carrier_hz: float,
    prf_hz: float,
    *,
    reject_alias: bool = True,
) -> tuple[float, float, float, float]:
    """Independent monostatic oracle; positive velocity means approaching."""
    if not finite_real(velocity_mps):
        raise ValueError("velocity must be finite")
    if not finite_real(carrier_hz) or carrier_hz <= 0:
        raise ValueError("carrier must be finite and positive")
    if not finite_real(prf_hz) or prf_hz <= 0:
        raise ValueError("PRF must be finite and positive")
    wavelength_m = SPEED_OF_LIGHT_MPS / carrier_hz
    doppler_hz = 2.0 * velocity_mps / wavelength_m
    phase_increment_rad = 2.0 * math.pi * doppler_hz / prf_hz
    unambiguous_velocity_mps = wavelength_m * prf_hz / 4.0
    if reject_alias and abs(doppler_hz) >= prf_hz / 2.0:
        raise ValueError("Doppler must remain inside the unambiguous interval")
    return wavelength_m, doppler_hz, phase_increment_rad, unambiguous_velocity_mps


def synthesize_echo(
    velocity_mps: float,
    carrier_hz: float,
    prf_hz: float,
    pulse_count: int,
    noise_rms: float = 0.0,
    seed: int = 3601,
) -> tuple[list[complex], float]:
    if (
        not isinstance(pulse_count, int)
        or isinstance(pulse_count, bool)
        or not 4 <= pulse_count <= MAX_PULSE_COUNT
        or pulse_count % 2
    ):
        raise ValueError("pulse count must be a bounded even integer")
    if not finite_real(noise_rms) or noise_rms < 0:
        raise ValueError("noise RMS must be finite and nonnegative")
    _, doppler_hz, phase_increment_rad, _ = doppler_model(
        velocity_mps, carrier_hz, prf_hz
    )
    generator = random.Random(seed)
    samples: list[complex] = []
    for pulse_index in range(pulse_count):
        ideal = cmath.exp(1j * (math.radians(25.0) + pulse_index * phase_increment_rad))
        noise = noise_rms / math.sqrt(2.0) * complex(
            generator.gauss(0.0, 1.0), generator.gauss(0.0, 1.0)
        )
        samples.append(ideal + noise)
    products = [sample.conjugate() * following for sample, following in zip(samples, samples[1:])]
    estimated_phase = cmath.phase(sum(products))
    return samples, estimated_phase * prf_hz / (2.0 * math.pi)


def centered_dft_peak(samples: list[complex], prf_hz: float) -> tuple[float, float]:
    count = len(samples)
    if count < 4 or count % 2:
        raise ValueError("DFT requires an even coherent pulse count")
    window = [0.5 - 0.5 * math.cos(2.0 * math.pi * n / (count - 1)) for n in range(count)]
    bins = list(range(-count // 2, count // 2))
    spectrum = [
        sum(
            samples[n] * window[n] * cmath.exp(-2j * math.pi * k * n / count)
            for n in range(count)
        )
        for k in bins
    ]
    peak_index = max(range(count), key=lambda index: abs(spectrum[index]))
    return bins[peak_index] * prf_hz / count, prf_hz / count


def validate_sweep_shape(values: object, *, allow_signed: bool) -> None:
    if not isinstance(values, (list, tuple)) or not 2 <= len(values) <= MAX_SWEEP_CASES:
        raise ValueError("sweep must have a bounded case count")
    if not all(finite_real(value) for value in values):
        raise ValueError("sweep values must be finite real numbers")
    if any(right <= left for left, right in zip(values, values[1:])):
        raise ValueError("sweep values must increase strictly")
    if not allow_signed and any(value <= 0 for value in values):
        raise ValueError("sweep values must be positive")


def source_contract_errors(source: str) -> list[str]:
    required = (
        "random_seed = 3601;",
        "speed_of_light_mps = 299792458;",
        "carrier_frequency_hz = 10e9;",
        "pulse_repetition_frequency_hz = 4e3;",
        "baseline_velocity_mps = 15;",
        "pulse_count = 32;",
        "wavelength_m = speed_of_light_mps/carrier_frequency_hz;",
        "pulse_repetition_interval_s = 1/pulse_repetition_frequency_hz;",
        "doppler_frequency_hz = 2*baseline_velocity_mps/wavelength_m;",
        "phase_increment_rad = 2*pi*doppler_frequency_hz*",
        "pulse_repetition_interval_s;",
        "pulse_index = 0:pulse_count-1;",
        "adjacent_products = conj(received_echo(1:end-1)).*",
        "received_echo(2:end);",
        "estimated_phase_increment_rad = angle(sum(adjacent_products));",
        "unwrapped_phase_rad = unwrap(angle(received_echo));",
        "doppler_spectrum = fftshift(fft(received_echo.*slow_time_window,",
        "doppler_axis_hz = (-pulse_count/2:pulse_count/2-1)*",
        "velocity_sweep_mps",
        "carrier_sweep_hz",
        "pulse_count_sweep",
        "max_pulse_count",
        "max_sweep_cases",
        "Intentionally broken case",
        "broken_echo = abs(received_echo);",
        "broken_model_valid = false;",
        "recovered_model_valid = true;",
        "close(findall(0, 'Type', 'figure', 'Tag', 'P36'))",
    )
    errors = [f"missing source marker: {marker}" for marker in required if marker not in source]
    for pattern in (
        r"\bphased\.",
        r"\bdop2speed\s*\(",
        r"\bspeed2dop\s*\(",
        r"\brange2doppler\s*\(",
        r"\bparfor\b",
        r"(?m)^\s*while\s+true\b",
    ):
        if re.search(pattern, source, flags=re.IGNORECASE):
            errors.append(f"opaque or unbounded operation: {pattern}")
    return errors


class P36ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.text = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        cls.experiment = cls.text["experiment.m"]

    def test_complete_artifacts_exact_identity_and_permanent_prerequisite(self):
        self.assertEqual(validate_p36_contract(MODULE, self.manifest), [])
        for name, text in self.text.items():
            self.assertGreater(len(text), 100, name)
            self.assertIn(QUESTION, text)
        prerequisite = next(item for item in self.manifest["modules"] if item["id"] == "P35")
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertIn("P35", self.text["README.md"])
        self.assertIn("P35", self.text["lesson.md"])

    def test_contract_rejects_missing_empty_duplicate_and_malformed_inputs(self):
        self.assertIn("manifest modules must be a list", validate_p36_contract(MODULE, {}))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p36_contract(MODULE, {"modules": ["bad"]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P36 manifest entry, found 2", validate_p36_contract(MODULE, duplicate))
        wrong = copy.deepcopy(self.manifest)
        entry = next(item for item in wrong["modules"] if item["id"] == "P36")
        entry["guiding_question"] = "generic"
        entry["status"] = "scaffolded"
        errors = validate_p36_contract(MODULE, wrong)
        self.assertIn(f"P36 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P36 status must be 'implemented'", errors)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            for name in ARTIFACTS:
                (fixture / name).write_text("content\n", encoding="utf-8")
            (fixture / "experiment.m").unlink()
            (fixture / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p36_contract(fixture, self.manifest)
            self.assertIn("P36 missing experiment.m", errors)
            self.assertIn("P36 empty checks.md", errors)

    def test_independent_doppler_oracle_sign_factor_two_and_limits(self):
        wavelength_m, doppler_hz, phase_rad, unambiguous_velocity = doppler_model(
            15.0, 10e9, 4e3
        )
        self.assertAlmostEqual(wavelength_m, 0.0299792458, places=10)
        self.assertAlmostEqual(doppler_hz, 1000.6922855944561, places=9)
        self.assertAlmostEqual(phase_rad, 1.5718837664637613, places=9)
        self.assertAlmostEqual(unambiguous_velocity, 29.9792458, places=9)
        for velocity in (-20.0, -10.0, 0.0, 10.0, 20.0):
            _, signed_doppler, signed_phase, _ = doppler_model(velocity, 10e9, 4e3)
            with self.subTest(velocity=velocity):
                self.assertEqual(math.copysign(1, signed_doppler), math.copysign(1, velocity))
                self.assertAlmostEqual(signed_phase, 2 * math.pi * signed_doppler / 4e3)
        for args in (
            (float("nan"), 10e9, 4e3),
            (float("inf"), 10e9, 4e3),
            (0.0, 0.0, 4e3),
            (0.0, -1.0, 4e3),
            (0.0, 10e9, 0.0),
            (0.0, 10e9, True),
            (30.0, 10e9, 4e3),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                doppler_model(*args)

    def test_phase_and_fft_oracles_recover_signed_velocity_with_bounded_error(self):
        for velocity in (-15.0, 0.0, 15.0):
            samples, phase_estimate_hz = synthesize_echo(
                velocity, 10e9, 4e3, 32, noise_rms=0.03
            )
            _, expected_hz, _, _ = doppler_model(velocity, 10e9, 4e3)
            peak_hz, bin_spacing_hz = centered_dft_peak(samples, 4e3)
            with self.subTest(velocity=velocity):
                self.assertLess(abs(phase_estimate_hz - expected_hz), 20.0)
                self.assertLessEqual(abs(peak_hz - expected_hz), bin_spacing_hz / 2)
                if velocity:
                    self.assertEqual(
                        math.copysign(1, phase_estimate_hz),
                        math.copysign(1, expected_hz),
                    )

        samples, _ = synthesize_echo(15.0, 10e9, 4e3, 32)
        magnitude_only = [abs(sample) for sample in samples]
        broken_peak_hz, _ = centered_dft_peak(magnitude_only, 4e3)
        broken_products = [left.conjugate() * right for left, right in zip(magnitude_only, magnitude_only[1:])]
        self.assertEqual(cmath.phase(sum(broken_products)), 0.0)
        self.assertEqual(broken_peak_hz, 0.0)

    def test_slow_time_sampling_aliases_dopplers_separated_by_one_prf(self):
        carrier_hz = 10e9
        prf_hz = 4e3
        pulse_count = 32
        base_velocity_mps = 10.0
        wavelength_m, base_doppler_hz, _, _ = doppler_model(
            base_velocity_mps, carrier_hz, prf_hz
        )
        aliased_velocity_mps = base_velocity_mps + wavelength_m * prf_hz / 2.0
        _, aliased_doppler_hz, _, _ = doppler_model(
            aliased_velocity_mps, carrier_hz, prf_hz, reject_alias=False
        )
        self.assertAlmostEqual(aliased_doppler_hz - base_doppler_hz, prf_hz)

        initial_phase_rad = math.radians(25.0)
        base_samples = [
            cmath.exp(
                1j
                * (
                    initial_phase_rad
                    + 2.0 * math.pi * base_doppler_hz * pulse_index / prf_hz
                )
            )
            for pulse_index in range(pulse_count)
        ]
        aliased_samples = [
            cmath.exp(
                1j
                * (
                    initial_phase_rad
                    + 2.0 * math.pi * aliased_doppler_hz * pulse_index / prf_hz
                )
            )
            for pulse_index in range(pulse_count)
        ]
        self.assertTrue(
            all(
                abs(base - aliased) < 1e-12
                for base, aliased in zip(base_samples, aliased_samples)
            )
        )
        self.assertEqual(
            centered_dft_peak(base_samples, prf_hz),
            centered_dft_peak(aliased_samples, prf_hz),
        )

    def test_sweeps_isolate_velocity_carrier_and_pulse_count(self):
        velocities = (-20.0, -10.0, 0.0, 10.0, 20.0)
        dopplers = [doppler_model(value, 10e9, 4e3)[1] for value in velocities]
        self.assertTrue(all(right > left for left, right in zip(dopplers, dopplers[1:])))
        low = doppler_model(15.0, 5e9, 4e3)
        high = doppler_model(15.0, 10e9, 4e3)
        self.assertAlmostEqual(high[1], 2.0 * low[1])
        self.assertAlmostEqual(high[2], 2.0 * low[2])
        self.assertAlmostEqual(low[3], 2.0 * high[3])
        pulse_counts = (8, 16, 32, 64)
        spacings = [4e3 / count for count in pulse_counts]
        self.assertEqual(spacings, [500.0, 250.0, 125.0, 62.5])
        self.assertTrue(all(right < left for left, right in zip(spacings, spacings[1:])))

    def test_resource_bounds_and_malformed_sweeps_are_rejected(self):
        synthesize_echo(10.0, 10e9, 4e3, 32, noise_rms=0.0)
        for pulse_count in (0, 3, 7, MAX_PULSE_COUNT + 2, True, 8.0):
            with self.subTest(pulse_count=pulse_count), self.assertRaises(ValueError):
                synthesize_echo(10.0, 10e9, 4e3, pulse_count)  # type: ignore[arg-type]
        for noise in (-1.0, float("nan"), float("inf"), True):
            with self.subTest(noise=noise), self.assertRaises(ValueError):
                synthesize_echo(10.0, 10e9, 4e3, 8, noise_rms=noise)
        validate_sweep_shape([-1.0, 0.0, 1.0], allow_signed=True)
        validate_sweep_shape([1.0, 2.0], allow_signed=False)
        for values, allow_signed in (
            ([], True),
            ([1.0], True),
            (list(range(MAX_SWEEP_CASES + 1)), True),
            ([0.0, 0.0, 1.0], True),
            ([1.0, float("nan")], True),
            ([0.0, 1.0], False),
            ("1,2", True),
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                validate_sweep_shape(values, allow_signed=allow_signed)

    def test_transparent_source_mutations_sweeps_failure_and_recovery(self):
        self.assertEqual(source_contract_errors(self.experiment), [])
        for old, new in (
            ("2*baseline_velocity_mps/wavelength_m", "baseline_velocity_mps/wavelength_m"),
            ("2*pi*doppler_frequency_hz*", "-2*pi*doppler_frequency_hz*"),
            (
                "pulse_repetition_interval_s = 1/pulse_repetition_frequency_hz;",
                "pulse_repetition_interval_s = pulse_repetition_frequency_hz;",
            ),
            ("conj(received_echo(1:end-1))", "received_echo(1:end-1)"),
            ("fftshift(fft(received_echo.*slow_time_window,", "fft(received_echo.*slow_time_window,"),
            ("broken_model_valid = false;", "broken_model_valid = true;"),
            ("recovered_model_valid = true;", "recovered_model_valid = false;"),
        ):
            with self.subTest(old=old):
                self.assertTrue(source_contract_errors(self.experiment.replace(old, new, 1)))
        for marker in (
            "Sweep 1",
            "Sweep 2",
            "Sweep 3",
            "velocity_sweep_mps",
            "carrier_sweep_hz",
            "pulse_count_sweep",
            "Intentionally broken case",
            "Recovery",
        ):
            self.assertIn(marker.lower(), self.experiment.lower())
        self.assertEqual(self.experiment.count("RandStream('mt19937ar', 'Seed', random_seed)"), 2)

    def test_docs_cli_timeout_cancellation_isolation_and_compatibility_contract(self):
        combined = "\n".join(self.text.values())
        for marker in (
            "positive radial velocity",
            "approaching",
            "receding",
            "wavelength",
            "slow time",
            "phase increment",
            "Doppler FFT",
            "unambiguous",
            "P35",
            "base MATLAB",
            "Baseline observation",
            "Sweep one variable",
            "broken",
            "recover",
            "Observation checks",
            "Prediction checks",
            "Interpretation checks",
            "teach-back",
            "Ctrl+C",
            "private",
            "global random stream",
            "figures tagged `P36`",
            ".learning/",
            "worker",
            "timer",
            "external transaction",
            "rollback",
            "scaffolded",
        ):
            self.assertIn(marker.lower(), combined.lower(), marker)
        self.assertNotRegex(combined, r"(?i)implementation batch `P36` is pending")
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("Project 36", root_readme)
        self.assertIn("Project 36", start_here)
        self.assertRegex(module_index, r"\| \[P36\].*\| implemented \|")
        state = ROOT / ".learning/progress.json"
        before = state.read_bytes() if state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir()
            target = fixture / EXPECTED_IDENTITY["folder"]
            target.mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
            shutil.copy2(ROOT / "curriculum/modules.json", fixture / "curriculum/modules.json")
            shutil.copy2(MODULE / "README.md", target / "README.md")
            result = subprocess.run(
                [str(fixture / "bin/learn"), "start", "36"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P36 — Measure Doppler from Pulse-to-Pulse Phase", result.stdout)
            self.assertIn("status: implemented", result.stdout)
        self.assertEqual(state.read_bytes() if state.exists() else None, before)

    def test_artifact_newlines_no_placeholders_and_honest_runtime_boundary(self):
        combined = "\n".join(self.text.values())
        for name, text in self.text.items():
            self.assertTrue(text.endswith("\n"), name)
            self.assertFalse(text.endswith("\n\n"), name)
        for phrase in ("lorem ipsum", "placeholder", "fill this in", "coming soon"):
            self.assertNotIn(phrase, combined.lower())
        self.assertNotRegex(combined, r"(?i)MATLAB (?:was )?(?:executed|validated|passed)")

    def test_retained_evidence_is_honest_complete_and_has_one_newline(self):
        paths = sorted((ROOT / "docs/evidence").glob("P36-*.md"))
        self.assertEqual(len(paths), 1)
        evidence = paths[0].read_text(encoding="utf-8")
        for marker in (
            "Acceptance mapping",
            "Figure and metric inventory",
            "Exact commands and results",
            "Changed and preserved invariants",
            "Residual risks and unperformed validation",
            "Rollback and recovery",
            "Validation class",
            "MATLAB runtime status",
            "Toolboxes",
            "did not run",
        ):
            self.assertIn(marker, evidence)
        for command in (
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
        ):
            self.assertIn(command, evidence)
        self.assertNotIn("PENDING —", evidence)
        self.assertTrue(evidence.endswith("\n"))
        self.assertFalse(evidence.endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
