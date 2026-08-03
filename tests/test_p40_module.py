from __future__ import annotations

import cmath
import copy
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/40-compare-coherent-and-noncoherent-integration"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "When should pulse phases be added and when should magnitudes be added?"
MAX_PULSE_COUNT = 128
MAX_SWEEP_CASES = 12
EXPECTED_IDENTITY = {
    "number": 40,
    "id": "P40",
    "title": "Compare Coherent and Noncoherent Integration",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "compare-coherent-and-noncoherent-integration",
    "folder": "modules/40-compare-coherent-and-noncoherent-integration",
    "status": "implemented",
    "implementation_batch": "P40",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p40_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P40 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P40 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P40"]
    if len(matches) != 1:
        return errors + [f"expected one P40 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P40 {key} must be {expected!r}")
    return errors


def validate_controls(
    *,
    pulse_count: object = 32,
    target_amplitude: object = 1.0,
    input_snr_db: object = -8.0,
    pulse_count_sweep: object = (1, 2, 4, 8, 16, 32, 64),
    phase_jitter_sweep_deg: object = (0, 5, 15, 30, 60, 90, 120, 180),
    broken_cycle_deg: object = (0, 90, 180, -90),
) -> None:
    if (
        not isinstance(pulse_count, int)
        or isinstance(pulse_count, bool)
        or not 4 <= pulse_count <= MAX_PULSE_COUNT
    ):
        raise ValueError("pulse count must be a bounded integer")
    if not finite_real(target_amplitude) or target_amplitude <= 0:
        raise ValueError("target amplitude must be finite and positive")
    if not finite_real(input_snr_db) or not -40 <= input_snr_db <= 20:
        raise ValueError("input SNR must be finite and bounded")
    if not isinstance(broken_cycle_deg, (list, tuple)) or tuple(broken_cycle_deg) != (
        0,
        90,
        180,
        -90,
    ):
        raise ValueError("broken phase cycle must retain the exact quadrature pattern")
    if pulse_count % len(broken_cycle_deg):
        raise ValueError("pulse count must contain complete broken phase cycles")
    if (
        not isinstance(pulse_count_sweep, (list, tuple))
        or not 4 <= len(pulse_count_sweep) <= MAX_SWEEP_CASES
    ):
        raise ValueError("pulse-count sweep must have a bounded case count")
    if not all(
        isinstance(value, int)
        and not isinstance(value, bool)
        and 1 <= value <= MAX_PULSE_COUNT
        for value in pulse_count_sweep
    ):
        raise ValueError("pulse-count sweep entries must be bounded integers")
    if any(right <= left for left, right in zip(pulse_count_sweep, pulse_count_sweep[1:])):
        raise ValueError("pulse-count sweep must increase strictly")
    if pulse_count not in pulse_count_sweep:
        raise ValueError("pulse-count sweep must include the baseline")
    if (
        not isinstance(phase_jitter_sweep_deg, (list, tuple))
        or not 4 <= len(phase_jitter_sweep_deg) <= MAX_SWEEP_CASES
    ):
        raise ValueError("phase-jitter sweep must have a bounded case count")
    if not all(
        finite_real(value) and 0 <= value <= 180
        for value in phase_jitter_sweep_deg
    ):
        raise ValueError("phase-jitter values must be finite and bounded")
    if any(
        right <= left
        for left, right in zip(phase_jitter_sweep_deg, phase_jitter_sweep_deg[1:])
    ):
        raise ValueError("phase-jitter sweep must increase strictly")
    if phase_jitter_sweep_deg[0] != 0:
        raise ValueError("phase-jitter sweep must include the stable-phase limit")


def stable_integration_metrics(
    pulse_count: int, *, input_snr_db: float = -8.0
) -> tuple[float, float, float]:
    if (
        not isinstance(pulse_count, int)
        or isinstance(pulse_count, bool)
        or not 1 <= pulse_count <= MAX_PULSE_COUNT
    ):
        raise ValueError("pulse count must be a bounded integer")
    if not finite_real(input_snr_db) or not -40 <= input_snr_db <= 20:
        raise ValueError("input SNR must be finite and bounded")
    single_pulse_snr = 10.0 ** (input_snr_db / 10.0)
    coherent_output_snr = pulse_count * single_pulse_snr
    coherent_detectability = pulse_count * single_pulse_snr
    noncoherent_detectability = math.sqrt(pulse_count) * single_pulse_snr
    return coherent_output_snr, coherent_detectability, noncoherent_detectability


def expected_coherent_gain(pulse_count: int, phase_jitter_std_deg: float) -> float:
    if (
        not isinstance(pulse_count, int)
        or isinstance(pulse_count, bool)
        or not 1 <= pulse_count <= MAX_PULSE_COUNT
    ):
        raise ValueError("pulse count must be a bounded integer")
    if not finite_real(phase_jitter_std_deg) or not 0 <= phase_jitter_std_deg <= 180:
        raise ValueError("phase jitter must be finite and bounded")
    sigma_rad = math.radians(phase_jitter_std_deg)
    return 1.0 + (pulse_count - 1) * math.exp(-(sigma_rad**2))


def integrate_clean_sequence(
    samples: list[complex], phase_reference: list[complex]
) -> tuple[complex, float]:
    if not isinstance(samples, list) or not isinstance(phase_reference, list):
        raise ValueError("samples and phase reference must be lists")
    if not samples or len(samples) != len(phase_reference):
        raise ValueError("samples and phase reference must have equal nonzero length")
    values = samples + phase_reference
    if not all(
        isinstance(value, (int, float, complex)) and not isinstance(value, bool)
        for value in values
    ):
        raise ValueError("sequence values must be numeric")
    coherent = sum(
        sample * reference.conjugate()
        for sample, reference in zip(samples, phase_reference)
    )
    noncoherent_energy = sum(abs(sample) ** 2 for sample in samples)
    return coherent, noncoherent_energy


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", re.sub(r"\.\.\.\s*", "", source))
    required = (
        "random_seed = 4001",
        "RandStream('mt19937ar', 'Seed', random_seed)",
        "assert(~islogical(random_seed) && ~islogical(pulse_count)",
        "assert(~islogical(pulse_count_sweep) && ~islogical(phase_jitter_std_sweep_deg)",
        "phase_aligned_samples = observed_samples.*conj(phase_reference)",
        "coherent_sum = sum(phase_aligned_samples)",
        "coherent_power_statistic = abs(coherent_sum)^2",
        "noncoherent_power_statistic = sum(abs(observed_samples).^2)",
        "pulse_count_sweep = [1 2 4 8 16 32 64]",
        "phase_jitter_std_sweep_deg = [0 5 15 30 60 90 120 180]",
        "phase_coherence_factor = exp(-(phase_jitter_std_sweep_rad).^2)",
        "coherent_effective_gain = 1+(pulse_count-1)*phase_coherence_factor",
        "broken_phase_jitter_cycle_deg = [0 90 180 -90]",
        "broken_clean_samples.*conj(phase_reference)",
        "exp(-1j*broken_phase_jitter_pattern_rad)",
        "broken_model_valid = false",
        "recovered_model_valid = true",
        "assert(max_pulse_count == 128)",
        "assert(max_sweep_cases == 12)",
        "assert(max_figure_groups == 4)",
        "max_stored_numeric_values = 50000",
        "assert(max_stored_numeric_values == 50000)",
        "assert(comparison_tolerance == 1e-10)",
    )
    return [marker for marker in required if marker not in compact]


class P40ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.docs = {
            name: (MODULE / name).read_text(encoding="utf-8")
            for name in ("README.md", "lesson.md", "walkthrough.md", "checks.md")
        }

    def test_identity_artifacts_and_prerequisite_are_permanent(self):
        self.assertEqual(validate_p40_contract(MODULE, self.manifest), [])
        entries = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(entries["P39"]["status"], "implemented")
        self.assertEqual(entries["P40"], EXPECTED_IDENTITY)
        for name in ARTIFACTS:
            data = (MODULE / name).read_bytes()
            self.assertTrue(data.endswith(b"\n"), name)
            self.assertFalse(data.endswith(b"\n\n"), name)
            self.assertNotIn(b"\r", data, name)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "module"
            shutil.copytree(MODULE, fixture)
            (fixture / "checks.md").unlink()
            self.assertIn("P40 missing checks.md", validate_p40_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("", encoding="utf-8")
            self.assertIn("P40 empty checks.md", validate_p40_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p40_contract(MODULE, []))
        malformed = {"modules": [None]}
        self.assertIn(
            "manifest module entries must be objects",
            validate_p40_contract(MODULE, malformed),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn(
            "expected one P40 manifest entry, found 2",
            validate_p40_contract(MODULE, duplicate),
        )
        drifted = copy.deepcopy(self.manifest)
        next(item for item in drifted["modules"] if item["id"] == "P40")[
            "guiding_question"
        ] = "Changed"
        self.assertTrue(
            any("guiding_question" in error for error in validate_p40_contract(MODULE, drifted))
        )

    def test_control_validation_rejects_malformed_and_resource_overruns(self):
        validate_controls()
        invalid_cases = (
            {"pulse_count": True},
            {"pulse_count": 3},
            {"pulse_count": 129},
            {"pulse_count": 30},
            {"target_amplitude": 0},
            {"target_amplitude": True},
            {"target_amplitude": math.inf},
            {"input_snr_db": True},
            {"input_snr_db": math.nan},
            {"input_snr_db": -41},
            {"input_snr_db": 21},
            {"pulse_count_sweep": (1, 2, 32)},
            {"pulse_count_sweep": (1, 4, 32, 32)},
            {"pulse_count_sweep": (1, 4, 64, 128)},
            {"pulse_count_sweep": tuple(range(1, 14))},
            {"pulse_count_sweep": (1, 4, True, 32)},
            {"phase_jitter_sweep_deg": (0, 30, 30, 180)},
            {"phase_jitter_sweep_deg": (5, 30, 90, 180)},
            {"phase_jitter_sweep_deg": (0, 30, math.inf, 180)},
            {"phase_jitter_sweep_deg": (0, 30, 90, 181)},
            {"phase_jitter_sweep_deg": tuple(range(13))},
            {"broken_cycle_deg": (0, 180)},
        )
        for controls in invalid_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_stable_phase_gain_and_statistic_separation_are_numerically_correct(self):
        single_snr = 10.0 ** (-8.0 / 10.0)
        for pulse_count in (4, 8, 16, 32, 64, 128):
            output_snr, coherent_d, noncoherent_d = stable_integration_metrics(pulse_count)
            self.assertAlmostEqual(output_snr, pulse_count * single_snr, places=14)
            self.assertAlmostEqual(coherent_d, pulse_count * single_snr, places=14)
            self.assertAlmostEqual(noncoherent_d, math.sqrt(pulse_count) * single_snr, places=14)
            self.assertGreater(coherent_d, noncoherent_d)
        output_32, _, _ = stable_integration_metrics(32)
        self.assertAlmostEqual(10.0 * math.log10(output_32), 7.0514997832, places=9)

    def test_phase_jitter_loss_has_correct_limits_and_noncoherent_energy_is_invariant(self):
        sweep = (0, 5, 15, 30, 60, 90, 120, 180)
        gains = [expected_coherent_gain(32, value) for value in sweep]
        self.assertAlmostEqual(gains[0], 32.0, places=14)
        self.assertTrue(all(right < left for left, right in zip(gains, gains[1:])))
        self.assertLess(gains[-1], 1.01)
        for jitter in sweep:
            phases = [cmath.exp(1j * math.radians(jitter)) for _ in range(32)]
            self.assertAlmostEqual(sum(abs(value) ** 2 for value in phases) / 32.0, 1.0)
        for malformed in (math.nan, math.inf, -1, 181):
            with self.assertRaises(ValueError):
                expected_coherent_gain(32, malformed)

    def test_common_phase_offset_preserves_coherent_gain_while_relative_phase_cancels(self):
        pulse_count = 32
        reference = [
            cmath.exp(1j * math.radians(25 + 35 * pulse))
            for pulse in range(pulse_count)
        ]
        common_offset = math.radians(73)
        common_offset_samples = [
            value * cmath.exp(1j * common_offset) for value in reference
        ]
        common_sum, common_energy = integrate_clean_sequence(
            common_offset_samples, reference
        )

        quadrature_cycle = (0, 90, 180, -90)
        varying_samples = [
            value
            * cmath.exp(
                1j * math.radians(quadrature_cycle[pulse % len(quadrature_cycle)])
            )
            for pulse, value in enumerate(reference)
        ]
        varying_sum, varying_energy = integrate_clean_sequence(varying_samples, reference)

        self.assertAlmostEqual(abs(common_sum) / pulse_count, 1.0, places=14)
        self.assertAlmostEqual(cmath.phase(common_sum), common_offset, places=14)
        self.assertLessEqual(abs(varying_sum), 1e-12)
        self.assertAlmostEqual(common_energy / pulse_count, 1.0, places=14)
        self.assertAlmostEqual(varying_energy / pulse_count, 1.0, places=14)

    def test_broken_quadrature_cycle_cancels_and_exact_derotation_recovers(self):
        pulse_count = 32
        reference = [cmath.exp(1j * math.radians(25 + 35 * pulse)) for pulse in range(pulse_count)]
        cycle = (0, 90, 180, -90)
        errors = [math.radians(cycle[pulse % len(cycle)]) for pulse in range(pulse_count)]
        broken = [ref * cmath.exp(1j * error) for ref, error in zip(reference, errors)]
        broken_sum, broken_energy = integrate_clean_sequence(broken, reference)
        recovered = [sample * cmath.exp(-1j * error) for sample, error in zip(broken, errors)]
        recovered_sum, recovered_energy = integrate_clean_sequence(recovered, reference)
        self.assertLessEqual(abs(broken_sum), 1e-12)
        self.assertAlmostEqual(broken_energy / pulse_count, 1.0, places=14)
        self.assertAlmostEqual(abs(recovered_sum) / pulse_count, 1.0, places=14)
        self.assertAlmostEqual(recovered_energy / pulse_count, 1.0, places=14)
        with self.assertRaises(ValueError):
            integrate_clean_sequence([], [])
        with self.assertRaises(ValueError):
            integrate_clean_sequence([1], [1, 1])
        with self.assertRaises(ValueError):
            integrate_clean_sequence([True], [1])

    def test_source_is_deterministic_bounded_transparent_and_base_matlab(self):
        self.assertEqual(source_contract_errors(self.source), [])
        self.assertEqual(self.source.count("figure('Name'"), 4)
        for label in (
            "Pulse index",
            "Coherent output SNR (dB)",
            "Phase-jitter standard deviation (deg)",
            "Detectability index d (standard deviations)",
            "Cumulative power (amplitude^2)",
        ):
            self.assertIn(label, self.source)
        for opaque_or_toolbox_marker in (
            "phased.",
            "dsp.",
            "filter(",
            "freqz(",
            "designfilt(",
            "awgn(",
            "rng(",
            "system(",
            "webread(",
            "fopen(",
            "parfor",
            "while true",
        ):
            self.assertNotIn(opaque_or_toolbox_marker, self.source)
        self.assertIn("private_stream", self.source)
        self.assertIn("estimated_stored_numeric_values", self.source)
        mutations = (
            self.source.replace(
                "phase_aligned_samples = observed_samples.*conj(phase_reference)",
                "phase_aligned_samples = abs(observed_samples)",
                1,
            ),
            self.source.replace(
                "noncoherent_power_statistic = sum(abs(observed_samples).^2)",
                "noncoherent_power_statistic = abs(sum(observed_samples))^2",
                1,
            ),
            self.source.replace(
                "phase_coherence_factor = exp(-(phase_jitter_std_sweep_rad).^2)",
                "phase_coherence_factor = ones(size(phase_jitter_std_sweep_rad))",
                1,
            ),
            self.source.replace(
                "exp(-1j*broken_phase_jitter_pattern_rad)",
                "ones(size(broken_phase_jitter_pattern_rad))",
                1,
            ),
            self.source.replace(
                "assert(max_stored_numeric_values == 50000)",
                "assert(max_stored_numeric_values > 0)",
                1,
            ),
        )
        for mutated in mutations:
            with self.subTest(mutation=len(mutated)):
                self.assertTrue(source_contract_errors(mutated))

    def test_catalogs_and_isolated_tutor_entry_have_a_timeout(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("Project 40", root_readme)
        self.assertIn("Project 40", start_here)
        self.assertRegex(module_index, r"\| \[P40\].*\| implemented \|")
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir()
            for entry in self.manifest["modules"]:
                destination = fixture / entry["folder"] / "README.md"
                destination.parent.mkdir(parents=True)
                shutil.copy2(ROOT / entry["folder"] / "README.md", destination)
            shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
            shutil.copy2(ROOT / "curriculum/modules.json", fixture / "curriculum/modules.json")
            result = subprocess.run(
                [str(fixture / "bin/learn"), "start", "40"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P40 — Compare Coherent and Noncoherent Integration", result.stdout)
            self.assertIn("status: implemented", result.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_default_tutor_entry_advances_from_completed_p39_without_state_loss(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir()
            for entry in self.manifest["modules"]:
                destination = fixture / entry["folder"] / "README.md"
                destination.parent.mkdir(parents=True)
                shutil.copy2(ROOT / entry["folder"] / "README.md", destination)
            shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
            shutil.copy2(ROOT / "curriculum/modules.json", fixture / "curriculum/modules.json")
            prior_completed = [f"P{number:02d}" for number in range(1, 40)]
            progress = fixture / ".learning/progress.json"
            progress.parent.mkdir()
            progress.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P39",
                        "completed": prior_completed,
                        "notes": {"P39": "preserve this note"},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [str(fixture / "bin/learn"), "start"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P40 — Compare Coherent and Noncoherent Integration", result.stdout)
            state = json.loads(progress.read_text(encoding="utf-8"))
            self.assertEqual(state["current"], "P40")
            self.assertEqual(state["completed"], prior_completed)
            self.assertEqual(state["notes"], {"P39": "preserve this note"})

    def test_docs_cover_baseline_two_sweeps_broken_recovery_limits_and_teach_back(self):
        for name, text in self.docs.items():
            self.assertIn(QUESTION, text, name)
            self.assertNotIn("TODO", text, name)
            self.assertNotIn("placeholder", text.lower(), name)
        self.assertIn("## AI chat prompt", self.docs["README.md"])
        walkthrough = self.docs["walkthrough.md"]
        for marker in (
            "Baseline",
            "Sweep 1",
            "Sweep 2",
            "Intentionally broken case",
            "Recovery",
            "Expected observation",
            "Common mistake",
        ):
            self.assertIn(marker, walkthrough)
        lesson = self.docs["lesson.md"]
        for marker in (
            "\\mathrm{SNR}_{c,\\mathrm{out}}=N\\rho",
            "d_c=N\\rho",
            "e^{-\\sigma_\\phi^2}",
            "Limiting cases",
            "P41",
        ):
            self.assertIn(marker, lesson)
        checks = self.docs["checks.md"]
        for marker in (
            "Observation checks",
            "Interpretation checks",
            "Prediction checks",
            "teach-back rubric",
        ):
            self.assertIn(marker, checks)
        combined = "\n".join(self.docs.values())
        for marker in ("Ctrl+C", "rollback", "private seed", "bounded"):
            self.assertIn(marker.lower(), combined.lower())

    def test_manifest_rollback_fixture_is_isolated_from_neighboring_module_identity(self):
        rolled_back = copy.deepcopy(self.manifest)
        entries_before = {
            entry["id"]: copy.deepcopy(entry)
            for entry in rolled_back["modules"]
            if entry["id"] in {"P39", "P41"}
        }
        next(entry for entry in rolled_back["modules"] if entry["id"] == "P40")[
            "status"
        ] = "scaffolded"
        entries_after = {
            entry["id"]: entry
            for entry in rolled_back["modules"]
            if entry["id"] in {"P39", "P41"}
        }
        self.assertEqual(entries_after, entries_before)
        self.assertTrue(
            any("status" in error for error in validate_p40_contract(MODULE, rolled_back))
        )

    def test_retained_evidence_has_claim_boundary_commands_and_rollback(self):
        evidence = ROOT / "docs/evidence/P40-2026-08-03.md"
        self.assertTrue(evidence.is_file())
        text = evidence.read_text(encoding="utf-8")
        for heading in (
            "## Outcome and claim boundary",
            "## Governance, state, ownership, concurrency, and CI inspection",
            "## Acceptance mapping",
            "## Physical model and independent static oracle",
            "## Figure and metric inventory",
            "## Focused test coverage",
            "## Exact commands and results",
            "## Changed and preserved invariants",
            "## Rollback and recovery",
            "## Residual risks and unperformed validation",
        ):
            self.assertIn(heading, text)
        for command in (
            "DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py",
            "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -q",
            "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh",
        ):
            self.assertIn(command, text)
        for marker in (
            "Validation class",
            "MATLAB and Octave did not run",
            "static",
            "rollback",
            "P39",
            "P40",
            "unperformed validation",
        ):
            self.assertIn(marker.lower(), text.lower(), marker)
        self.assertNotRegex(text, r"(?i)MATLAB (ran|passed|validated|executed successfully)")
        data = evidence.read_bytes()
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))
        self.assertNotIn(b"\r", data)


if __name__ == "__main__":
    unittest.main()
