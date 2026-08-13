from __future__ import annotations

import cmath
import copy
import json
import math
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/74-create-a-micro-doppler-spectrogram"
EVIDENCE = ROOT / "docs/evidence/P74-2026-08-12.md"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How do rotating or swinging target parts produce time-varying Doppler around bulk motion?"

BASE_CONTROLS = {
    "seed": 7401,
    "c_mps": 3.0e8,
    "carrier_hz": 24.0e9,
    "sample_rate_hz": 4800.0,
    "duration_s": 4.0,
    "bulk_velocity_mps": 1.2,
    "swing_speed_mps": 2.0,
    "swing_rate_hz": 1.5,
    "scatterer_voltage": [1.0, 0.35, 0.28],
    "scatterer_phase_rad": [0.0, 0.7, -0.9],
    "snr_db": 25.0,
    "window_samples": 512,
    "overlap_samples": 384,
    "stft_fft_length": 2048,
    "spectrum_fft_length": 32768,
    "speed_sweep_mps": [1.0, 2.0, 3.0],
    "carrier_sweep_hz": [10.0e9, 24.0e9, 77.0e9],
    "window_sweep_samples": [192, 512, 1536],
    "overlap_fraction": 0.75,
    "max_samples": 20000,
    "max_stft_fft": 4096,
    "max_spectrum_fft": 65536,
    "max_frames": 1000,
    "max_sweep_cases": 5,
    "max_private_values": 50000,
    "max_working_values": 15000000,
    "max_figures": 5,
}


def module_entry(data: dict, module_id: str) -> dict:
    return next(item for item in data["modules"] if item["id"] == module_id)


def artifact_errors(folder: Path, status: str = "implemented") -> list[str]:
    errors: list[str] = []
    if status == "implemented":
        for name in ARTIFACTS:
            path = folder / name
            if not path.is_file():
                errors.append(f"missing {name}")
            elif not path.read_text(encoding="utf-8", errors="replace").strip():
                errors.append(f"empty {name}")
            elif "TODO" in path.read_text(encoding="utf-8", errors="replace"):
                errors.append(f"TODO remains in {name}")
    return errors


def private_uniform(seed: int, count: int, maximum: int = 50000) -> list[float]:
    if not isinstance(seed, int) or isinstance(seed, bool) or not 1 <= seed < 2147483647:
        raise ValueError("invalid seed")
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= maximum:
        raise ValueError("invalid count")
    state = seed
    values: list[float] = []
    for _ in range(count):
        state = (16807 * state) % 2147483647
        values.append(state / 2147483647)
    return values


def private_complex_noise(seed: int, count: int) -> list[complex]:
    uniforms = private_uniform(seed, 2 * count)
    values: list[complex] = []
    for index in range(0, len(uniforms), 2):
        radius = math.sqrt(-2 * math.log(max(uniforms[index], float.fromhex("0x1p-1022"))))
        phase = 2 * math.pi * uniforms[index + 1]
        values.append(radius * cmath.exp(1j * phase) / math.sqrt(2))
    return values


def component_state(
    time_s: float,
    carrier_hz: float = 24.0e9,
    bulk_mps: float = 1.2,
    swing_mps: float = 2.0,
    swing_hz: float = 1.5,
) -> tuple[list[float], list[float]]:
    wavelength = 3.0e8 / carrier_hz
    angle = 2 * math.pi * swing_hz * time_s
    velocities = [
        bulk_mps,
        bulk_mps + swing_mps * math.cos(angle),
        bulk_mps + swing_mps * math.cos(angle + math.pi),
    ]
    advances = [
        bulk_mps * time_s,
        bulk_mps * time_s + swing_mps / (2 * math.pi * swing_hz) * math.sin(angle),
        bulk_mps * time_s + swing_mps / (2 * math.pi * swing_hz) * math.sin(angle + math.pi),
    ]
    phases = [-4 * math.pi * advance / wavelength for advance in advances]
    return velocities, phases


def clean_return(times: list[float]) -> list[complex]:
    amplitudes = BASE_CONTROLS["scatterer_voltage"]
    starts = BASE_CONTROLS["scatterer_phase_rad"]
    result: list[complex] = []
    for time_s in times:
        _, phases = component_state(time_s)
        result.append(sum(a * cmath.exp(1j * (phase + start)) for a, phase, start in zip(amplitudes, phases, starts)))
    return result


def simulated_return(
    times: list[float],
    seed: int,
    carrier_hz: float = 24.0e9,
    swing_mps: float = 2.0,
) -> tuple[list[complex], list[complex], list[complex]]:
    amplitudes = BASE_CONTROLS["scatterer_voltage"]
    starts = BASE_CONTROLS["scatterer_phase_rad"]
    clean: list[complex] = []
    for time_s in times:
        _, phases = component_state(
            time_s, carrier_hz=carrier_hz, swing_mps=swing_mps
        )
        clean.append(
            sum(
                amplitude * cmath.exp(1j * (phase + start))
                for amplitude, phase, start in zip(amplitudes, phases, starts)
            )
        )
    nominal_signal_rms = math.sqrt(sum(amplitude**2 for amplitude in amplitudes))
    noise_rms = nominal_signal_rms * 10 ** (-BASE_CONTROLS["snr_db"] / 20)
    noise = [noise_rms * value for value in private_complex_noise(seed, len(times))]
    received = [signal + additive for signal, additive in zip(clean, noise)]
    return received, clean, noise


def projection(signal: list[complex], times: list[float], raw_frequency_hz: float) -> complex:
    count = len(signal)
    window = [0.5 - 0.5 * math.cos(2 * math.pi * index / (count - 1)) for index in range(count)]
    return sum(
        sample * weight * cmath.exp(-2j * math.pi * raw_frequency_hz * time_s)
        for sample, weight, time_s in zip(signal, window, times)
    ) / sum(window)


def control_errors(controls: dict) -> list[str]:
    errors: list[str] = []
    vectors = (
        "scatterer_voltage", "scatterer_phase_rad", "speed_sweep_mps",
        "carrier_sweep_hz", "window_sweep_samples",
    )
    for name in vectors:
        values = controls.get(name)
        if (
            not isinstance(values, list)
            or not values
            or any(isinstance(value, (list, tuple, bool)) for value in values)
            or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values)
        ):
            errors.append(f"invalid row vector: {name}")
    if errors:
        return errors
    samples = round(controls["duration_s"] * controls["sample_rate_hz"])
    if samples > controls["max_samples"] or samples < controls["window_samples"]:
        errors.append("invalid sample count")
    if controls["overlap_samples"] < 0 or controls["overlap_samples"] >= controls["window_samples"]:
        errors.append("invalid overlap")
    if not 0 <= controls["overlap_fraction"] < 1:
        errors.append("invalid overlap fraction")
    if controls["stft_fft_length"] < max([controls["window_samples"], *controls["window_sweep_samples"]]) or controls["stft_fft_length"] > controls["max_stft_fft"]:
        errors.append("invalid STFT FFT")
    if controls["spectrum_fft_length"] < samples or controls["spectrum_fft_length"] > controls["max_spectrum_fft"]:
        errors.append("invalid spectrum FFT")
    if any(len(controls[name]) > controls["max_sweep_cases"] for name in ("speed_sweep_mps", "carrier_sweep_hz", "window_sweep_samples")):
        errors.append("sweep ceiling")
    if errors:
        return errors
    minimum_hop = min(
        window - math.floor(controls["overlap_fraction"] * window)
        for window in controls["window_sweep_samples"]
    )
    frames = math.floor((samples - min(controls["window_sweep_samples"])) / minimum_hop) + 1
    if frames > controls["max_frames"]:
        errors.append("frame ceiling")
    maximum_swing = max([controls["swing_speed_mps"], *controls["speed_sweep_mps"]])
    maximum_carrier = max([controls["carrier_hz"], *controls["carrier_sweep_hz"]])
    maximum_velocity = abs(controls["bulk_velocity_mps"]) + maximum_swing
    maximum_doppler = 2 * maximum_velocity * maximum_carrier / controls["c_mps"]
    if maximum_doppler >= controls["sample_rate_hz"] / 2:
        errors.append("Doppler Nyquist")
    if 2 * samples > controls["max_private_values"]:
        errors.append("private ceiling")
    if errors:
        return errors
    baseline_frames = (samples - controls["window_samples"]) // (
        controls["window_samples"] - controls["overlap_samples"]
    ) + 1
    window_frames = sum(
        (samples - window) // (window - math.floor(controls["overlap_fraction"] * window)) + 1
        for window in controls["window_sweep_samples"]
    )
    total_frames = baseline_frames * (
        1 + len(controls["speed_sweep_mps"]) + len(controls["carrier_sweep_hz"]) + 2
    ) + window_frames
    predicted = (
        3 * controls["stft_fft_length"] * total_frames
        + 30 * samples
        + 4 * controls["spectrum_fft_length"]
    )
    if predicted > controls["max_working_values"]:
        errors.append("working preflight")
    return errors


class P74ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.documents = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS}
        cls.source = cls.documents["experiment.m"]

    def make_cli_fixture(self, root: Path, manifest: dict) -> Path:
        fixture = root / "repo"
        (fixture / "bin").mkdir(parents=True)
        (fixture / "curriculum").mkdir(parents=True)
        shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
        (fixture / "curriculum/modules.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        for entry in manifest["modules"]:
            readme = fixture / entry["folder"] / "README.md"
            readme.parent.mkdir(parents=True)
            readme.write_text(f"# {entry['id']}\n", encoding="utf-8")
        return fixture

    def run_cli(self, fixture: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(fixture / "bin/learn"), *arguments], cwd=fixture, text=True,
            capture_output=True, timeout=3, check=False,
        )

    def test_artifacts_manifest_identity_and_permanent_dependencies(self):
        self.assertEqual(artifact_errors(MODULE), [])
        entry = module_entry(self.data, "P74")
        expected = {
            "number": 74,
            "title": "Create a Micro-Doppler Spectrogram",
            "guiding_question": QUESTION,
            "phase": 8,
            "phase_title": "FMCW, MIMO, and Micro-Doppler",
            "slug": "create-a-micro-doppler-spectrogram",
            "folder": "modules/74-create-a-micro-doppler-spectrogram",
            "status": "implemented",
            "implementation_batch": "P74",
        }
        for key, value in expected.items():
            self.assertEqual(entry[key], value)
        self.assertEqual(module_entry(self.data, "P73")["status"], "implemented")
        self.assertEqual(module_entry(self.data, "P75")["implementation_batch"], "P75")
        for name, text in self.documents.items():
            with self.subTest(name=name):
                self.assertIn(QUESTION, text)

    def test_malformed_artifact_contract_rejects_missing_empty_and_placeholder(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            self.assertEqual(artifact_errors(fixture), [])
            (fixture / "lesson.md").unlink()
            self.assertIn("missing lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("\n", encoding="utf-8")
            self.assertIn("empty lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("TODO generic lesson\n", encoding="utf-8")
            self.assertIn("TODO remains in lesson.md", artifact_errors(fixture))

    def test_source_exposes_model_stft_sweeps_failure_recovery_and_bounds(self):
        markers = (
            "baseline_seed = 7401;", "slow_time_sample_rate_hz = 4800.0;",
            "bulk_radial_velocity_mps = 1.2;", "swing_speed_mps = 2.0;",
            "scatterer_voltage = [1.0 0.35 0.28];", "validate_controls(controls);",
            "radial_advance_m", "phase_rad = -4*pi*radial_advance_m/wavelength_m",
            "component_returns", "explicit_hann", "explicit_stft",
            "stft_raw(:, frame_index) = fftshift(fft(frame, fft_length))",
            "stft_values = stft_raw(end:-1:1, :);",
            "swing_speed_sweep_mps = [1.0 2.0 3.0];",
            "carrier_sweep_hz = [10.0 24.0 77.0]*1.0e9;",
            "window_sweep_samples = [192 512 1536];",
            "Intentionally broken case", "magnitude_only_record = abs",
            "isequaln(broken_complex_measurement", "SameDataRecovery",
            "P74:DopplerNyquist", "P74:ResourceCeilings", "p74_results = struct",
            "maximum_swing_speed_mps = max([controls.swing_speed_mps",
            "maximum_carrier_hz = max([controls.carrier_hz",
            "max([controls.window_samples",
            "P74:WorkingPreflight", "workspace_inventory = whos;",
            "P74:OverlapFraction",
            "working_value_equivalents = ceil(working_storage_bytes/8);",
            "nominal_signal_rms = sqrt(sum(scatterer_voltage.^2));",
            "noise = noise_rms*unit_noise;", "received = clean+noise;",
            "Signed Doppler frequency (Hz, + approaching)",
        )
        for marker in markers:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P74"), 5)
        self.assertNotIn("rng(", self.source.lower())

    def test_source_has_no_opaque_toolbox_or_external_side_effect(self):
        lowered = self.source.lower()
        for forbidden in (
            "spectrogram(", "pspectrum(", "instfreq(", "phased.", "parfor",
            "timer(", "webread(", "webwrite(", "urlread(", "fopen(",
            "save(", "writematrix(", "system(", "unix(", "dos(",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertIsNone(re.search(r"(?<!explicit_)\bstft\(", lowered))
        self.assertIsNone(re.search(r"(?<!explicit_)\bhann\(", lowered))

    def test_control_contract_accepts_baseline_and_rejects_malformed_resources(self):
        self.assertEqual(control_errors(copy.deepcopy(BASE_CONTROLS)), [])
        cases: list[tuple[str, dict]] = []
        nested = copy.deepcopy(BASE_CONTROLS)
        nested["speed_sweep_mps"] = [[1.0], [2.0], [3.0]]
        cases.append(("column sweep", nested))
        nonfinite = copy.deepcopy(BASE_CONTROLS)
        nonfinite["carrier_sweep_hz"][1] = math.nan
        cases.append(("nonfinite carrier", nonfinite))
        overlap = copy.deepcopy(BASE_CONTROLS)
        overlap["overlap_samples"] = overlap["window_samples"]
        cases.append(("zero hop", overlap))
        overlap_fraction = copy.deepcopy(BASE_CONTROLS)
        overlap_fraction["overlap_fraction"] = 1.0
        cases.append(("zero sweep hop", overlap_fraction))
        fft_size = copy.deepcopy(BASE_CONTROLS)
        fft_size["stft_fft_length"] = 1024
        cases.append(("window exceeds FFT", fft_size))
        baseline_window = copy.deepcopy(BASE_CONTROLS)
        baseline_window["window_samples"] = 4096
        cases.append(("baseline window exceeds FFT", baseline_window))
        frames = copy.deepcopy(BASE_CONTROLS)
        frames["max_frames"] = 100
        cases.append(("frame ceiling", frames))
        private = copy.deepcopy(BASE_CONTROLS)
        private["max_private_values"] = 1000
        cases.append(("private ceiling", private))
        alias = copy.deepcopy(BASE_CONTROLS)
        alias["sample_rate_hz"] = 4000.0
        cases.append(("Doppler Nyquist", alias))
        baseline_carrier_alias = copy.deepcopy(BASE_CONTROLS)
        baseline_carrier_alias["carrier_hz"] = 100.0e9
        cases.append(("baseline carrier Nyquist", baseline_carrier_alias))
        baseline_swing_alias = copy.deepcopy(BASE_CONTROLS)
        baseline_swing_alias["swing_speed_mps"] = 4.0
        cases.append(("baseline swing Nyquist", baseline_swing_alias))
        working = copy.deepcopy(BASE_CONTROLS)
        working["max_working_values"] = 1000000
        cases.append(("working preflight", working))
        for label, controls in cases:
            with self.subTest(label=label):
                self.assertTrue(control_errors(controls))

    def test_private_generator_is_repeatable_bounded_and_isolated(self):
        first = private_complex_noise(7401, 100)
        repeated = private_complex_noise(7401, 100)
        other = private_complex_noise(7501, 100)
        self.assertEqual(first, repeated)
        self.assertNotEqual(first, other)
        self.assertAlmostEqual(private_uniform(7401, 1)[0], 0.057922958889008946)
        with self.assertRaises(ValueError):
            private_uniform(0, 1)
        with self.assertRaises(ValueError):
            private_uniform(7401, 50001)

    def test_integrated_motion_oracle_has_correct_velocity_phase_and_sign(self):
        wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
        velocities, phases = component_state(0.0)
        self.assertEqual(velocities, [1.2, 3.2, -0.8])
        self.assertAlmostEqual(2 * velocities[0] / wavelength, 192.0)
        self.assertAlmostEqual(2 * (velocities[1] - velocities[0]) / wavelength, 320.0)
        dt = 1.0e-7
        _, next_phases = component_state(dt)
        raw_frequency_estimates = [
            (after - before) / (2 * math.pi * dt)
            for before, after in zip(phases, next_phases)
        ]
        expected_raw = [-2 * velocity / wavelength for velocity in velocities]
        for actual, expected in zip(raw_frequency_estimates, expected_raw):
            self.assertAlmostEqual(actual, expected, delta=0.001)

    def test_direct_projection_oracle_finds_negative_raw_and_positive_display_bulk(self):
        sample_rate = BASE_CONTROLS["sample_rate_hz"]
        times = [index / sample_rate for index in range(round(sample_rate))]
        signal = clean_return(times)
        at_bulk_raw = abs(projection(signal, times, -192.0))
        at_wrong_sign = abs(projection(signal, times, 192.0))
        self.assertGreater(at_bulk_raw, 8 * at_wrong_sign)
        displayed_physical_frequency = -(-192.0)
        self.assertEqual(displayed_physical_frequency, 192.0)

    def test_speed_and_carrier_sweeps_have_permanent_physical_scaling(self):
        wavelength = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
        bulk = 2 * BASE_CONTROLS["bulk_velocity_mps"] / wavelength
        extents = [2 * speed / wavelength for speed in BASE_CONTROLS["speed_sweep_mps"]]
        self.assertEqual(extents, [160.0, 320.0, 480.0])
        for actual, expected in zip(
            [bulk - value for value in extents], [32.0, -128.0, -288.0]
        ):
            self.assertAlmostEqual(actual, expected)
        carrier_bulk = [
            2 * BASE_CONTROLS["bulk_velocity_mps"] * carrier / BASE_CONTROLS["c_mps"]
            for carrier in BASE_CONTROLS["carrier_sweep_hz"]
        ]
        self.assertEqual(carrier_bulk, [80.0, 192.0, 616.0])
        maximum_doppler = 2 * 4.2 * 77.0e9 / 3.0e8
        self.assertAlmostEqual(maximum_doppler, 2156.0)
        self.assertLess(maximum_doppler, BASE_CONTROLS["sample_rate_hz"] / 2)

    def test_controlled_sweeps_reuse_noise_and_window_sweep_reuses_measurement(self):
        self.assertRegex(
            self.source,
            r"for case_index = 1:speed_case_count[\s\S]*?simulate_micro_doppler\(baseline_seed\+100,",
        )
        self.assertRegex(
            self.source,
            r"for case_index = 1:carrier_case_count[\s\S]*?simulate_micro_doppler\(baseline_seed\+200,",
        )
        self.assertRegex(
            self.source,
            r"for case_index = 1:window_case_count[\s\S]*?explicit_stft\([\s\S]*?baseline_return,",
        )
        durations_ms = [1000 * value / BASE_CONTROLS["sample_rate_hz"] for value in BASE_CONTROLS["window_sweep_samples"]]
        native_hz = [BASE_CONTROLS["sample_rate_hz"] / value for value in BASE_CONTROLS["window_sweep_samples"]]
        self.assertEqual(durations_ms, [40.0, 106.66666666666667, 320.0])
        self.assertEqual(native_hz, [25.0, 9.375, 3.125])
        self.assertTrue(all(a > b for a, b in zip(native_hz, native_hz[1:])))

    def test_physical_sweeps_behaviorally_reuse_the_same_additive_noise(self):
        sample_rate = BASE_CONTROLS["sample_rate_hz"]
        times = [index / sample_rate for index in range(64)]

        speed_cases = [
            simulated_return(times, 7501, swing_mps=speed)
            for speed in BASE_CONTROLS["speed_sweep_mps"]
        ]
        carrier_cases = [
            simulated_return(times, 7601, carrier_hz=carrier)
            for carrier in BASE_CONTROLS["carrier_sweep_hz"]
        ]

        for cases in (speed_cases, carrier_cases):
            reference_noise = cases[0][2]
            self.assertTrue(any(cases[0][1][index] != cases[-1][1][index] for index in range(len(times))))
            for received, clean, noise in cases:
                self.assertEqual(noise, reference_noise)
                for sample, clean_sample, expected_noise in zip(received, clean, noise):
                    self.assertAlmostEqual(
                        abs((sample - clean_sample) - expected_noise), 0.0, delta=1.0e-12
                    )

    def test_magnitude_only_failure_and_unchanged_complex_recovery_oracle(self):
        sample_rate = BASE_CONTROLS["sample_rate_hz"]
        times = [index / sample_rate for index in range(round(sample_rate))]
        complex_signal = clean_return(times)
        immutable = list(complex_signal)
        magnitude_signal = [abs(value) for value in complex_signal]
        broken_dc = abs(projection([complex(value, 0.0) for value in magnitude_signal], times, 0.0))
        broken_bulk = abs(projection([complex(value, 0.0) for value in magnitude_signal], times, -192.0))
        recovered_bulk = abs(projection(complex_signal, times, -192.0))
        self.assertGreater(broken_dc, 5 * broken_bulk)
        self.assertGreater(recovered_bulk, 5 * broken_bulk)
        self.assertEqual(complex_signal, immutable)

    def test_documents_are_concept_first_and_cover_limits(self):
        combined = "\n".join(self.documents.values()).lower()
        for marker in (
            "integrated", "bulk doppler", "micro-doppler", "torso ridge",
            "periodic", "dwell-wide", "two-sided", "center of its window",
            "swing-speed", "carrier-frequency", "window-duration", "zero-padding",
            "magnitude-only", "unchanged", "recovery", "nyquist", "cancellation",
            "crossing", "rollback", "teach-back", "no optional toolbox",
            "base matlab r2016b or newer", "15,000,000", "five tagged figure",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(self.documents["checks.md"].count("**Correct:**"), 55)

    def test_cli_timeout_cancellation_rollback_recovery_isolation_and_future_compatibility(self):
        compatible = copy.deepcopy(self.data)
        module_entry(compatible, "P75")["status"] = "implemented"
        module_entry(compatible, "P75")["future_metadata"] = {"allowed": True}
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.make_cli_fixture(Path(directory), compatible)
            started = self.run_cli(fixture, "start", "74")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("status: implemented", started.stdout)
            rolled_back = copy.deepcopy(compatible)
            module_entry(rolled_back, "P74")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8")
            refused = self.run_cli(fixture, "start", "74")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P74", refused.stdout)
            (fixture / "curriculum/modules.json").write_text(json.dumps(compatible, indent=2) + "\n", encoding="utf-8")
            recovered = self.run_cli(fixture, "start", "74")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)
        walkthrough = " ".join(self.documents["walkthrough.md"].lower().split())
        for marker in ("ctrl+c", "no worker", "no background", "rerun from the top", "rollback"):
            self.assertIn(marker, walkthrough)

    def test_catalogs_evidence_and_exact_eof_policy(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 74 closes Phase 8", root_readme)
        self.assertIn("Project 74 follows P73", start_here)
        self.assertRegex(module_index, r"\| \[P74\].*\| implemented \|")
        evidence = EVIDENCE.read_text(encoding="utf-8")
        for heading in (
            "## Claim boundary", "## Acceptance map",
            "## Deterministic simulated-oracle results",
            "## Figure and metric inventory", "## Exact commands and results",
            "## Changed and preserved invariants", "## Residual risks",
            "## Rollback", "## Unperformed validation",
        ):
            self.assertIn(heading, evidence)
        changed_text_paths = [
            *[MODULE / name for name in ARTIFACTS], ROOT / "curriculum/modules.json",
            ROOT / "README.md", ROOT / "START_HERE.md", ROOT / "modules/README.md",
            ROOT / "tests/test_p74_module.py", EVIDENCE,
        ]
        for path in changed_text_paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
