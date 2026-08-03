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
MODULE = ROOT / "modules/37-build-a-pulse-doppler-data-matrix"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "What are fast time and slow time in a radar data block?"
SPEED_OF_LIGHT_MPS = 299_792_458.0
MAX_FAST_TIME_SAMPLES = 512
MAX_PULSE_COUNT = 128
MAX_TARGET_COUNT = 6
MAX_SWEEP_CASES = 7
EXPECTED_IDENTITY = {
    "number": 37,
    "id": "P37",
    "title": "Build a Pulse-Doppler Data Matrix",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "build-a-pulse-doppler-data-matrix",
    "folder": "modules/37-build-a-pulse-doppler-data-matrix",
    "status": "implemented",
    "implementation_batch": "P37",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p37_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P37 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P37 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P37"]
    if len(matches) != 1:
        return errors + [f"expected one P37 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P37 {key} must be {expected!r}")
    return errors


def validate_sweep(values: object, *, allow_signed: bool) -> None:
    if not isinstance(values, (list, tuple)) or not 2 <= len(values) <= MAX_SWEEP_CASES:
        raise ValueError("sweep must have a bounded case count")
    if not all(finite_real(value) for value in values):
        raise ValueError("sweep values must be finite real numbers")
    if any(right <= left for left, right in zip(values, values[1:])):
        raise ValueError("sweep values must increase strictly")
    if not allow_signed and any(value <= 0 for value in values):
        raise ValueError("sweep values must be positive")


def synthesize_clean_matrix(
    ranges_m: object,
    velocities_mps: object,
    amplitudes: object,
    *,
    sample_rate_hz: float = 20e6,
    carrier_hz: float = 10e9,
    prf_hz: float = 5e3,
    fast_time_count: int = 256,
    pulse_count: int = 32,
    sigma_samples: float = 1.2,
) -> tuple[list[list[complex]], list[int], list[float], list[float]]:
    if (
        not isinstance(fast_time_count, int)
        or isinstance(fast_time_count, bool)
        or not 32 <= fast_time_count <= MAX_FAST_TIME_SAMPLES
    ):
        raise ValueError("fast-time count must be a bounded integer")
    if (
        not isinstance(pulse_count, int)
        or isinstance(pulse_count, bool)
        or not 8 <= pulse_count <= MAX_PULSE_COUNT
        or pulse_count % 2
    ):
        raise ValueError("pulse count must be a bounded even integer")
    for value, label in (
        (sample_rate_hz, "sample rate"),
        (carrier_hz, "carrier"),
        (prf_hz, "PRF"),
        (sigma_samples, "range-response sigma"),
    ):
        if not finite_real(value) or value <= 0:
            raise ValueError(f"{label} must be finite and positive")
    if not all(isinstance(values, (list, tuple)) for values in (ranges_m, velocities_mps, amplitudes)):
        raise ValueError("target controls must be sequences")
    if not 1 <= len(ranges_m) <= MAX_TARGET_COUNT:
        raise ValueError("target count must be bounded")
    if len(ranges_m) != len(velocities_mps) or len(ranges_m) != len(amplitudes):
        raise ValueError("target controls must have equal lengths")
    if not all(finite_real(value) and value > 0 for value in ranges_m):
        raise ValueError("ranges must be finite and positive")
    if not all(finite_real(value) for value in velocities_mps):
        raise ValueError("velocities must be finite")
    if not all(finite_real(value) and value > 0 for value in amplitudes):
        raise ValueError("amplitudes must be finite and positive")

    wavelength_m = SPEED_OF_LIGHT_MPS / carrier_hz
    target_bins = [
        round(2.0 * target_range / SPEED_OF_LIGHT_MPS * sample_rate_hz) + 1
        for target_range in ranges_m
    ]
    if any(target_bin <= 1 or target_bin >= fast_time_count for target_bin in target_bins):
        raise ValueError("target must lie inside the recorded fast-time window")
    if len(set(target_bins)) != len(target_bins):
        raise ValueError("targets must occupy distinct baseline rows")
    dopplers_hz = [2.0 * velocity / wavelength_m for velocity in velocities_mps]
    if any(abs(doppler) >= prf_hz / 2.0 for doppler in dopplers_hz):
        raise ValueError("target Doppler must be strictly unambiguous")
    phase_steps_rad = [2.0 * math.pi * doppler / prf_hz for doppler in dopplers_hz]
    initial_phases_rad = [math.radians(value) for value in (0.0, 40.0, -30.0, 15.0, 70.0, -80.0)]
    matrix = [[0j for _ in range(pulse_count)] for _ in range(fast_time_count)]
    for target_index, target_bin in enumerate(target_bins):
        center = target_bin - 1
        for fast_index in range(fast_time_count):
            envelope = math.exp(-0.5 * ((fast_index - center) / sigma_samples) ** 2)
            for pulse_index in range(pulse_count):
                phase = initial_phases_rad[target_index] + phase_steps_rad[target_index] * pulse_index
                matrix[fast_index][pulse_index] += amplitudes[target_index] * envelope * cmath.exp(1j * phase)
    return matrix, target_bins, dopplers_hz, phase_steps_rad


def adjacent_phase(trace: list[complex]) -> float:
    if len(trace) < 2:
        raise ValueError("trace requires at least two pulses")
    return cmath.phase(sum(left.conjugate() * right for left, right in zip(trace, trace[1:])))


def source_contract_errors(source: str) -> list[str]:
    required = (
        "random_seed = 3701;",
        "speed_of_light_mps = 299792458;",
        "carrier_frequency_hz = 10e9;",
        "sample_rate_hz = 20e6;",
        "pulse_repetition_frequency_hz = 5e3;",
        "fast_time_sample_count = 256;",
        "pulse_count = 32;",
        "target_ranges_m = [450 900 1200];",
        "target_velocities_mps = [0 12 -18];",
        "wavelength_m = speed_of_light_mps/carrier_frequency_hz;",
        "range_bin_spacing_m = speed_of_light_mps/(2*sample_rate_hz);",
        "fast_time_s = fast_time_index/sample_rate_hz;",
        "slow_time_s = pulse_index*pulse_repetition_interval_s;",
        "target_delay_samples = round(2*target_ranges_m/speed_of_light_mps*",
        "target_range_bins = target_delay_samples+1;",
        "assert(all(target_range_bins > range_response_margin_samples)",
        "assert(all(range_sweep_bins > range_response_margin_samples)",
        "target_doppler_hz = 2*target_velocities_mps/wavelength_m;",
        "2*pi*target_doppler_hz(target_index)*slow_time_s",
        "max_neglected_range_migration_bins < 0.5",
        "clean_data_matrix = complex(zeros(fast_time_sample_count, pulse_count));",
        "range_response*slow_time_sequence;",
        "data_matrix = clean_data_matrix+complex_noise;",
        "selected_range_traces = data_matrix(target_range_bins, :);",
        "range_sweep_m",
        "velocity_sweep_mps",
        "Intentionally broken case",
        "broken_data_matrix = abs(data_matrix);",
        "broken_model_valid = false;",
        "recovered_model_valid = true;",
        "ylabel('Relative magnitude');",
        "ylabel('Ideal relative magnitude');",
        "axis xy;",
        "close(findall(0, 'Type', 'figure', 'Tag', 'P37'))",
    )
    errors = [f"missing source marker: {marker}" for marker in required if marker not in source]
    for pattern in (
        r"\bphased\.",
        r"\brange2time\s*\(",
        r"\btime2range\s*\(",
        r"\bdop2speed\s*\(",
        r"\bspeed2dop\s*\(",
        r"-2\*pi\*target_doppler_hz\(target_index\)\*slow_time_s",
        r"\bparfor\b",
        r"(?m)^\s*while\s+true\b",
    ):
        if re.search(pattern, source, flags=re.IGNORECASE):
            errors.append(f"opaque or unbounded operation: {pattern}")
    return errors


class P37ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.text = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        cls.experiment = cls.text["experiment.m"]

    def test_complete_artifacts_exact_identity_and_permanent_prerequisite(self):
        self.assertEqual(validate_p37_contract(MODULE, self.manifest), [])
        for name, text in self.text.items():
            self.assertGreater(len(text), 100, name)
            self.assertIn(QUESTION, text)
        prerequisite = next(item for item in self.manifest["modules"] if item["id"] == "P36")
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertIn("P36", self.text["README.md"])
        self.assertIn("P36", self.text["lesson.md"])

    def test_contract_rejects_missing_empty_duplicate_and_malformed_inputs(self):
        self.assertIn("manifest modules must be a list", validate_p37_contract(MODULE, {}))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p37_contract(MODULE, {"modules": ["bad"]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P37 manifest entry, found 2", validate_p37_contract(MODULE, duplicate))
        wrong = copy.deepcopy(self.manifest)
        entry = next(item for item in wrong["modules"] if item["id"] == "P37")
        entry["guiding_question"] = "generic"
        entry["status"] = "scaffolded"
        errors = validate_p37_contract(MODULE, wrong)
        self.assertIn(f"P37 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P37 status must be 'implemented'", errors)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            for name in ARTIFACTS:
                (fixture / name).write_text("content\n", encoding="utf-8")
            (fixture / "experiment.m").unlink()
            (fixture / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p37_contract(fixture, self.manifest)
            self.assertIn("P37 missing experiment.m", errors)
            self.assertIn("P37 empty checks.md", errors)

    def test_independent_matrix_oracle_maps_range_rows_and_slow_time_phase(self):
        matrix, bins, dopplers, phase_steps = synthesize_clean_matrix(
            [450.0, 900.0, 1200.0], [0.0, 12.0, -18.0], [1.0, 0.75, 0.55]
        )
        self.assertEqual((len(matrix), len(matrix[0])), (256, 32))
        self.assertEqual(bins, [61, 121, 161])
        spacing_m = SPEED_OF_LIGHT_MPS / (2.0 * 20e6)
        measured_ranges = [(target_bin - 1) * spacing_m for target_bin in bins]
        for truth, measured in zip((450.0, 900.0, 1200.0), measured_ranges):
            self.assertLessEqual(abs(truth - measured), spacing_m / 2.0)
        self.assertAlmostEqual(dopplers[0], 0.0)
        self.assertAlmostEqual(dopplers[1], 800.553828475565, places=9)
        self.assertAlmostEqual(dopplers[2], -1200.8307427133475, places=9)
        dwell_s = (32 - 1) / 5e3
        neglected_migration_m = max(abs(value) for value in (0.0, 12.0, -18.0)) * dwell_s
        self.assertAlmostEqual(neglected_migration_m, 0.1116, places=12)
        self.assertLess(neglected_migration_m / spacing_m, 0.5)

        for target_bin, expected_phase in zip(bins, phase_steps):
            trace = matrix[target_bin - 1]
            self.assertAlmostEqual(adjacent_phase(trace), expected_phase, places=9)
            local_rows = range(max(0, target_bin - 3), min(len(matrix), target_bin + 2))
            row_powers = {
                row: sum(abs(value) ** 2 for value in matrix[row]) / len(matrix[row])
                for row in local_rows
            }
            self.assertEqual(max(row_powers, key=row_powers.get), target_bin - 1)

    def test_sweeps_isolate_fast_time_row_from_slow_time_phase(self):
        range_cases = (300.0, 750.0, 1200.0)
        range_bins = []
        range_phases = []
        for target_range in range_cases:
            matrix, bins, _, phases = synthesize_clean_matrix(
                [target_range], [12.0], [1.0]
            )
            range_bins.append(bins[0])
            range_phases.append(adjacent_phase(matrix[bins[0] - 1]))
            self.assertAlmostEqual(range_phases[-1], phases[0], places=12)
        self.assertTrue(all(right > left for left, right in zip(range_bins, range_bins[1:])))
        self.assertTrue(all(abs(value - range_phases[0]) < 1e-12 for value in range_phases))

        velocity_cases = (-18.0, 0.0, 18.0)
        velocity_bins = []
        velocity_phases = []
        for velocity in velocity_cases:
            matrix, bins, _, _ = synthesize_clean_matrix([900.0], [velocity], [1.0])
            velocity_bins.append(bins[0])
            velocity_phases.append(adjacent_phase(matrix[bins[0] - 1]))
        self.assertEqual(velocity_bins, [121, 121, 121])
        self.assertLess(velocity_phases[0], velocity_phases[1])
        self.assertLess(velocity_phases[1], velocity_phases[2])
        self.assertAlmostEqual(velocity_phases[0], -velocity_phases[2], places=12)

    def test_magnitude_only_failure_preserves_range_and_loses_doppler_phase(self):
        matrix, bins, _, phase_steps = synthesize_clean_matrix([900.0], [12.0], [1.0])
        coherent_trace = matrix[bins[0] - 1]
        broken_trace = [abs(value) for value in coherent_trace]
        recovered_trace = list(coherent_trace)
        self.assertAlmostEqual(adjacent_phase(coherent_trace), phase_steps[0], places=12)
        self.assertEqual(adjacent_phase([complex(value) for value in broken_trace]), 0.0)
        self.assertTrue(all(abs(value) > 0 for value in broken_trace))
        self.assertEqual(recovered_trace, coherent_trace)
        self.assertAlmostEqual(adjacent_phase(recovered_trace), phase_steps[0], places=12)

    def test_resource_bounds_and_malformed_controls_are_rejected(self):
        synthesize_clean_matrix([900.0], [0.0], [1.0])
        invalid_cases = (
            {"ranges_m": [], "velocities_mps": [], "amplitudes": []},
            {"ranges_m": [900.0], "velocities_mps": [], "amplitudes": [1.0]},
            {"ranges_m": [float("nan")], "velocities_mps": [0.0], "amplitudes": [1.0]},
            {"ranges_m": [900.0], "velocities_mps": [float("inf")], "amplitudes": [1.0]},
            {"ranges_m": [900.0], "velocities_mps": [0.0], "amplitudes": [0.0]},
            {"ranges_m": [900.0], "velocities_mps": [40.0], "amplitudes": [1.0]},
            {"ranges_m": [5000.0], "velocities_mps": [0.0], "amplitudes": [1.0]},
            {"ranges_m": [900.0, 900.1], "velocities_mps": [0.0, 1.0], "amplitudes": [1.0, 1.0]},
        )
        for controls in invalid_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                synthesize_clean_matrix(**controls)
        for key, value in (
            ("fast_time_count", 31),
            ("fast_time_count", MAX_FAST_TIME_SAMPLES + 1),
            ("fast_time_count", True),
            ("pulse_count", 7),
            ("pulse_count", 9),
            ("pulse_count", MAX_PULSE_COUNT + 2),
            ("sample_rate_hz", 0.0),
            ("carrier_hz", float("nan")),
            ("prf_hz", True),
            ("sigma_samples", -1.0),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                synthesize_clean_matrix([900.0], [0.0], [1.0], **{key: value})

        validate_sweep([-1.0, 0.0, 1.0], allow_signed=True)
        validate_sweep([1.0, 2.0], allow_signed=False)
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
                validate_sweep(values, allow_signed=allow_signed)

    def test_transparent_source_mutations_sweeps_failure_and_recovery(self):
        self.assertEqual(source_contract_errors(self.experiment), [])
        for old, new in (
            ("2*target_ranges_m/speed_of_light_mps", "target_ranges_m/speed_of_light_mps"),
            ("2*target_velocities_mps/wavelength_m", "target_velocities_mps/wavelength_m"),
            (
                "2*pi*target_doppler_hz(target_index)*slow_time_s",
                "-2*pi*target_doppler_hz(target_index)*slow_time_s",
            ),
            ("target_range_bins = target_delay_samples+1;", "target_range_bins = target_delay_samples;"),
            ("range_response*slow_time_sequence", "slow_time_sequence.'*range_response.'"),
            ("data_matrix(target_range_bins, :)", "data_matrix(:, target_range_bins)"),
            ("broken_data_matrix = abs(data_matrix);", "broken_data_matrix = data_matrix;"),
            ("broken_model_valid = false;", "broken_model_valid = true;"),
            ("recovered_model_valid = true;", "recovered_model_valid = false;"),
            ("axis xy;", "axis ij;"),
        ):
            with self.subTest(old=old):
                self.assertTrue(source_contract_errors(self.experiment.replace(old, new, 1)))
        for marker in (
            "Baseline",
            "Sweep 1",
            "Sweep 2",
            "Intentionally broken case",
            "Recovery",
            "fast-time rows",
            "slow-time",
        ):
            self.assertIn(marker.lower(), self.experiment.lower())
        self.assertEqual(self.experiment.count("RandStream('mt19937ar', 'Seed', random_seed)"), 2)
        self.assertLess(
            self.experiment.index("assert(all(target_range_bins > range_response_margin_samples)"),
            self.experiment.index("target_measured_ranges_m = range_axis_m(target_range_bins).';"),
        )
        self.assertLess(
            self.experiment.index("assert(all(range_sweep_bins > range_response_margin_samples)"),
            self.experiment.index("range_sweep_measured_m = range_axis_m(range_sweep_bins).';"),
        )

    def test_docs_cli_timeout_cancellation_isolation_and_compatibility_contract(self):
        combined = "\n".join(self.text.values())
        for marker in (
            "fast time",
            "slow time",
            "rows",
            "columns",
            "delay",
            "range-bin spacing",
            "phase",
            "Doppler",
            "P36",
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
            "figures tagged `P37`",
            ".learning/",
            "worker",
            "timer",
            "external transaction",
            "rollback",
            "scaffolded",
        ):
            self.assertIn(marker.lower(), combined.lower(), marker)
        self.assertNotRegex(combined, r"(?i)implementation batch `P37` is pending")
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("Project 37", root_readme)
        self.assertIn("Project 37", start_here)
        self.assertRegex(module_index, r"\| \[P37\].*\| implemented \|")
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
                [str(fixture / "bin/learn"), "start", "37"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P37 — Build a Pulse-Doppler Data Matrix", result.stdout)
            self.assertIn("status: implemented", result.stdout)
        self.assertEqual(state.read_bytes() if state.exists() else None, before)

    def test_default_start_selects_p37_after_prerequisites_are_complete(self):
        prerequisite_ids = [
            item["id"] for item in self.manifest["modules"] if item["number"] < 37
        ]
        initial_state = {
            "schema_version": 1,
            "current": "P36",
            "completed": prerequisite_ids,
            "notes": {"P36": "prerequisite teach-back retained"},
        }
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir()
            fixture_state = fixture / ".learning/progress.json"
            fixture_state.parent.mkdir()
            fixture_state.write_text(
                json.dumps(initial_state, indent=2) + "\n", encoding="utf-8"
            )
            shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
            shutil.copy2(
                ROOT / "curriculum/modules.json", fixture / "curriculum/modules.json"
            )
            result = subprocess.run(
                [str(fixture / "bin/learn"), "start"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            persisted_state = json.loads(fixture_state.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("P37 — Build a Pulse-Doppler Data Matrix", result.stdout)
        self.assertIn("status: implemented", result.stdout)
        self.assertEqual(persisted_state["current"], "P37")
        self.assertEqual(persisted_state["completed"], prerequisite_ids)
        self.assertEqual(persisted_state["notes"], initial_state["notes"])
        self.assertEqual(repository_state.read_bytes() if repository_state.exists() else None, before)

    def test_artifact_newlines_no_placeholders_and_honest_runtime_boundary(self):
        combined = "\n".join(self.text.values())
        for name, text in self.text.items():
            self.assertTrue(text.endswith("\n"), name)
            self.assertFalse(text.endswith("\n\n"), name)
        for phrase in ("lorem ipsum", "placeholder", "fill this in", "coming soon"):
            self.assertNotIn(phrase, combined.lower())
        self.assertNotRegex(combined, r"(?i)MATLAB (?:was )?(?:executed|validated|passed)")

    def test_retained_evidence_is_honest_complete_and_has_one_newline(self):
        paths = sorted((ROOT / "docs/evidence").glob("P37-*.md"))
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
            self.assertRegex(
                evidence,
                rf"{re.escape(command)}[\s\S]{{0,500}}?Result: exit `0`",
            )
        for unfinished in ("pending", "will be replaced", "not yet run", "result forthcoming"):
            self.assertNotIn(unfinished, evidence.lower())
        self.assertTrue(evidence.endswith("\n"))
        self.assertFalse(evidence.endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
