from __future__ import annotations

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
MODULE = ROOT / "modules/42-create-a-full-range-doppler-map"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How do matched filtering and slow-time FFT combine to separate targets?"
EXPECTED_IDENTITY = {
    "number": 42,
    "id": "P42",
    "title": "Create a Full Range-Doppler Map",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "create-a-full-range-doppler-map",
    "folder": "modules/42-create-a-full-range-doppler-map",
    "status": "implemented",
    "implementation_batch": "P42",
}


def finite_real(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_p42_contract(path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        artifact = path / name
        if not artifact.is_file():
            errors.append(f"P42 missing {name}")
        elif not artifact.read_text(encoding="utf-8").strip():
            errors.append(f"P42 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P42"]
    if len(matches) != 1:
        return errors + [f"expected one P42 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P42 {key} must be {expected!r}")
    return errors


def validate_controls(*, samples: object = 512, pulses: object = 64,
                      pulse_samples: object = 48, targets: object = 3,
                      clutter: object = 24, sweep: object = (16, 32, 64),
                      tone_offset: object = 10.10) -> None:
    for name, value, lower, upper in (
        ("samples", samples, 128, 512), ("pulses", pulses, 16, 128),
        ("pulse samples", pulse_samples, 16, 128), ("targets", targets, 3, 6),
        ("clutter", clutter, 8, 32),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or not lower <= value <= upper:
            raise ValueError(f"{name} must be a bounded integer")
    if pulses % 2 or pulse_samples > samples:
        raise ValueError("pulse dimensions are incompatible")
    if not isinstance(sweep, (tuple, list)) or not 3 <= len(sweep) <= 6:
        raise ValueError("CPI sweep must have a bounded case count")
    if not all(isinstance(x, int) and not isinstance(x, bool) and 16 <= x <= pulses and x % 2 == 0 for x in sweep):
        raise ValueError("CPI sweep entries must be bounded even integers")
    if any(right <= left for left, right in zip(sweep, sweep[1:])) or sweep[-1] != pulses:
        raise ValueError("CPI sweep must increase to the baseline")
    if not finite_real(tone_offset) or abs(tone_offset) >= pulses / 2 - 3:
        raise ValueError("tone offset must be finite and away from Nyquist")


def dft(values: list[complex]) -> list[complex]:
    count = len(values)
    return [sum(value * complex(math.cos(-2 * math.pi * k * n / count), math.sin(-2 * math.pi * k * n / count))
                for n, value in enumerate(values)) for k in range(count)]


def range_compressed_oracle(delays: tuple[int, ...], doppler_bins: tuple[int, ...], *,
                            length: int = 8, pulses: int = 16) -> list[list[complex]]:
    """Small independent LFM match-filter oracle."""
    if len(delays) != len(doppler_bins) or not delays or length < 4 or pulses < 8:
        raise ValueError("malformed oracle scene")
    waveform = [complex(math.cos(math.pi * 0.17 * n * n), math.sin(math.pi * 0.17 * n * n)) for n in range(length)]
    rows = max(delays) + 2 * length
    raw = [[0j for _ in range(pulses)] for _ in range(rows)]
    for delay, bin_number in zip(delays, doppler_bins):
        for n, sample in enumerate(waveform):
            for pulse in range(pulses):
                phase = 2 * math.pi * bin_number * pulse / pulses
                raw[delay + n][pulse] += sample * complex(math.cos(phase), math.sin(phase))
    matched = [[0j for _ in range(pulses)] for _ in range(rows)]
    for row in range(rows):
        for pulse in range(pulses):
            # aligned correlation y[d] = sum_n x[d+n] conj(s[n])
            matched[row][pulse] = sum(raw[row + n][pulse] * waveform[n].conjugate()
                                       for n in range(length) if row + n < rows)
    return matched


def range_doppler_oracle(delays: tuple[int, ...], doppler_bins: tuple[int, ...], *,
                         length: int = 8, pulses: int = 16) -> list[list[complex]]:
    """Small independent LFM match-filter + slow-time DFT oracle."""
    return [dft(trace) for trace in range_compressed_oracle(
        delays, doppler_bins, length=length, pulses=pulses
    )]


def fast_time_dft(matrix: list[list[complex]]) -> list[list[complex]]:
    """Deliberately transform range rows while leaving pulse columns intact."""
    if not matrix or not matrix[0] or any(len(row) != len(matrix[0]) for row in matrix):
        raise ValueError("matrix must be nonempty and rectangular")
    rows, pulses = len(matrix), len(matrix[0])
    return [[sum(matrix[row][pulse] * complex(
        math.cos(-2 * math.pi * frequency * row / rows),
        math.sin(-2 * math.pi * frequency * row / rows),
    ) for row in range(rows)) for pulse in range(pulses)] for frequency in range(rows)]


def peak_near(matrix: list[list[complex]], delay: int, doppler_bin: int, radius: int = 1) -> tuple[int, int]:
    pulses = len(matrix[0])
    candidates = ((row, column) for row in range(max(0, delay-radius), min(len(matrix), delay+radius+1))
                  for column in range(pulses) if abs(((column - doppler_bin + pulses // 2) % pulses) - pulses // 2) <= radius)
    return max(candidates, key=lambda place: abs(matrix[place[0]][place[1]]))


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", re.sub(r"\.\.\.\s*", "", source))
    required = (
        "random_seed = 4201", "RandStream('mt19937ar', 'Seed', random_seed)",
        "clearvars;", "close(findall(0, 'Type', 'figure', 'Tag', 'P42'))",
        "matched_filter = conj(flipud(transmit_pulse))",
        "full_response = conv(raw_data(:, pulse_number), matched_filter, 'full')",
        "range_compressed(:, pulse_number) = full_response(",
        "fft(windowed_range_data, pulse_count, 2)",
        "positive radial velocity means approaching", "target_ranges_m(1) == target_ranges_m(2)",
        "target_velocities_mps(2) == target_velocities_mps(3)",
        "pi/180+2*pi*target_doppler_hz(target_index)*slow_time_s",
        "cpi_pulse_sweep = [16 32 64]", "assert(all(diff(cpi_velocity_spacing_mps) < 0))",
        "window_sidelobe_level_db(2) < window_sidelobe_level_db(1)",
        "window_mainlobe_width_bins(2) > window_mainlobe_width_bins(1)",
        "size(unique(measured_target_peak_indices, 'rows'), 1) == target_count",
        "all(target_peak_to_median_db > 20)",
        "fft(range_compressed, fast_time_sample_count, 1)", "broken_model_valid = false",
        "recovered_model_valid = true", "recovery_error = max(abs(recovered_range_doppler_complex(:)-",
        "assert(max_fast_time_samples == 512 && max_pulses == 128",
        "max_stored_numeric_values == 600000", "results.broken_model_valid",
        "results.recovered_model_valid", "results.recovery_error",
    )
    return [marker for marker in required if marker not in compact]


class P42ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.docs = {name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS if name != "experiment.m"}

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self):
        self.assertEqual(validate_p42_contract(MODULE, self.manifest), [])
        entries = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(entries["P41"]["status"], "implemented")
        self.assertEqual(entries["P42"], EXPECTED_IDENTITY)
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
            self.assertIn("P42 missing checks.md", validate_p42_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("", encoding="utf-8")
            self.assertIn("P42 empty checks.md", validate_p42_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p42_contract(MODULE, []))
        self.assertIn("manifest module entries must be objects", validate_p42_contract(MODULE, {"modules": [None]}))
        duplicate = copy.deepcopy(self.manifest); duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("expected one P42 manifest entry, found 2", validate_p42_contract(MODULE, duplicate))
        drifted = copy.deepcopy(self.manifest)
        next(x for x in drifted["modules"] if x["id"] == "P42")["title"] = "drift"
        self.assertTrue(any("title" in x for x in validate_p42_contract(MODULE, drifted)))

    def test_controls_reject_malformed_and_unbounded_values(self):
        validate_controls()
        for controls in ({"samples": True}, {"samples": 127}, {"samples": 513}, {"pulses": 15}, {"pulses": 129},
                         {"pulse_samples": 129}, {"targets": 2}, {"clutter": 33}, {"sweep": (16, 32)},
                         {"sweep": (16, 16, 64)}, {"sweep": (16, 32, 62)}, {"sweep": (16, 32, True)},
                         {"sweep": tuple(range(16, 128, 16))}, {"tone_offset": math.nan}, {"tone_offset": 29}):
            with self.subTest(controls=controls), self.assertRaises(ValueError): validate_controls(**controls)

    def test_independent_lfm_match_filter_and_slow_time_dft_oracle(self):
        first = range_doppler_oracle((5, 5, 17), (-3, 4, 4))
        self.assertEqual(first, range_doppler_oracle((5, 5, 17), (-3, 4, 4)))
        # Equal range, opposite signed Dopplers: the DFT preserves the documented sign.
        self.assertEqual(peak_near(first, 5, -3), (5, 13))
        self.assertEqual(peak_near(first, 5, 4), (5, 4))
        # Equal Doppler but separated delays: matched filtering preserves range separation.
        self.assertEqual(peak_near(first, 17, 4), (17, 4))
        self.assertGreater(abs(first[5][4]), 20)
        self.assertGreater(abs(first[17][4]), 20)

    def test_wrong_axis_has_no_doppler_peak_and_slow_time_recovery_is_exact(self):
        compressed = range_compressed_oracle((5,), (3,))
        correct = [dft(trace) for trace in compressed]
        wrong_axis = fast_time_dft(compressed)

        self.assertEqual(peak_near(correct, 5, 3), (5, 3))
        self.assertGreater(abs(correct[5][3]), 100)
        self.assertLess(max(abs(correct[5][column]) for column in range(16) if column != 3), 1e-10)

        # A fast-time DFT preserves pulse columns. For one coherent target its
        # magnitude is therefore flat across pulse index, not concentrated in
        # the target's Doppler bin, even though the output is finite and nonzero.
        self.assertGreater(sum(abs(value) ** 2 for row in wrong_axis for value in row), 0)
        self.assertLess(max(
            max(abs(value) for value in row) - min(abs(value) for value in row)
            for row in wrong_axis
        ), 1e-10)

        recovered = [dft(trace) for trace in compressed]
        self.assertEqual(recovered, correct)

    def test_baseline_physical_coordinates_match_the_documented_matlab_grid(self):
        speed_of_light = 299_792_458.0
        sample_rate = 20e6
        carrier_frequency = 10e9
        prf = 4000.0
        pulse_count = 64
        ranges = (1200.0, 1200.0, 2400.0)
        velocities = (-7.5, 10.3, 10.3)
        delays = tuple(round(2 * value / speed_of_light * sample_rate) for value in ranges)
        wavelength = speed_of_light / carrier_frequency
        doppler_spacing = prf / pulse_count
        doppler_bins = tuple(round((2 * value / wavelength) / doppler_spacing) for value in velocities)
        self.assertEqual(delays, (160, 160, 320))
        self.assertEqual(doppler_bins, (-8, 11, 11))
        measured_ranges = tuple(value * speed_of_light / (2 * sample_rate) for value in delays)
        measured_velocities = tuple(value * doppler_spacing * wavelength / 2 for value in doppler_bins)
        self.assertTrue(all(abs(actual - expected) <= speed_of_light / (4 * sample_rate)
                            for actual, expected in zip(measured_ranges, ranges)))
        self.assertTrue(all(abs(actual - expected) <= doppler_spacing * wavelength / 2
                            for actual, expected in zip(measured_velocities, velocities)))

    def test_cpi_and_window_oracles_capture_the_documented_tradeoffs(self):
        wavelength, prf = 0.03, 4000.0
        spacings = [wavelength * prf / (2 * pulses) for pulses in (16, 32, 64)]
        durations = [pulses / prf for pulses in (16, 32, 64)]
        self.assertTrue(all(b < a for a, b in zip(spacings, spacings[1:])))
        self.assertTrue(all(b > a for a, b in zip(durations, durations[1:])))
        count, offset = 64, 10.10
        tone = [complex(math.cos(2*math.pi*offset*n/count), math.sin(2*math.pi*offset*n/count)) for n in range(count)]
        windows = ([1.0] * count, [0.5 - 0.5*math.cos(2*math.pi*n/(count-1)) for n in range(count)])
        metrics = []
        for window in windows:
            spectrum = dft([x*w for x, w in zip(tone, window)])
            peak = max(range(count), key=lambda index: abs(spectrum[index]))
            db = [20*math.log10(max(abs(x)/max(map(abs, spectrum)), 1e-12)) for x in spectrum]
            width = sum(x >= -6 for x in db)
            sidelobe = max(x for index, x in enumerate(db) if abs(((index-peak+count//2)%count)-count//2) > 2)
            metrics.append((width, sidelobe))
        self.assertGreater(metrics[1][0], metrics[0][0])
        self.assertLess(metrics[1][1], metrics[0][1])

    def test_source_contract_markers_mutations_and_banned_apis(self):
        self.assertEqual(source_contract_errors(self.source), [])
        self.assertEqual(self.source.count("figure('Name'"), 7)
        for banned in ("phased.", "dsp.", "xcorr(", "corrcoef(", "awgn(", "rng(", "fopen(", "fwrite(", "load(", "save(", "system(", "webread(", "urlread(", "parfor", "while true", "timer(", "global "):
            self.assertNotIn(banned, self.source)
        for mutated in (self.source.replace("fft(windowed_range_data, ...\n    pulse_count, 2)", "fft(windowed_range_data, ...\n    pulse_count, 1)", 1),
                        self.source.replace("matched_filter = conj(flipud(transmit_pulse))", "matched_filter = transmit_pulse", 1),
                        self.source.replace("2*pi*target_doppler_hz(target_index)*slow_time_s", "-2*pi*target_doppler_hz(target_index)*slow_time_s", 1),
                        self.source.replace("broken_model_valid = false", "broken_model_valid = true", 1),
                        self.source.replace("max_stored_numeric_values == 600000", "max_stored_numeric_values > 0", 1)):
            self.assertTrue(source_contract_errors(mutated))

    def _fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        fixture = Path(temporary.name) / "repo"
        (fixture / "bin").mkdir(parents=True); (fixture / "curriculum").mkdir()
        for entry in self.manifest["modules"]:
            destination = fixture / entry["folder"] / "README.md"; destination.parent.mkdir(parents=True)
            shutil.copy2(ROOT / entry["folder"] / "README.md", destination)
        shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
        shutil.copy2(ROOT / "curriculum/modules.json", fixture / "curriculum/modules.json")
        return fixture

    def test_isolated_learn_start_42_has_timeout_and_preserves_repository_state(self):
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        fixture = self._fixture()
        result = subprocess.run([str(fixture / "bin/learn"), "start", "42"], cwd=fixture, text=True, capture_output=True, env=os.environ.copy(), timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("P42 — Create a Full Range-Doppler Map", result.stdout)
        self.assertIn("status: implemented", result.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_default_tutor_advance_from_completed_p41_preserves_state(self):
        fixture = self._fixture(); progress = fixture / ".learning/progress.json"; progress.parent.mkdir()
        completed = [f"P{number:02d}" for number in range(1, 42)]
        progress.write_text(json.dumps({"schema_version": 1, "current": "P41", "completed": completed, "notes": {"P41": "keep"}}, indent=2) + "\n", encoding="utf-8")
        result = subprocess.run([str(fixture / "bin/learn"), "start"], cwd=fixture, text=True, capture_output=True, env=os.environ.copy(), timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr); self.assertIn("P42 — Create a Full Range-Doppler Map", result.stdout)
        state = json.loads(progress.read_text(encoding="utf-8"))
        self.assertEqual(state["current"], "P42"); self.assertEqual(state["completed"], completed); self.assertEqual(state["notes"], {"P41": "keep"})

    def test_docs_cover_baseline_two_sweeps_broken_recovery_cancellation_and_rollback_limits(self):
        for name, text in self.docs.items():
            self.assertIn(QUESTION, text, name); self.assertNotIn("TODO", text); self.assertNotIn("placeholder", text.lower())
        walkthrough = self.docs["walkthrough.md"]
        for marker in ("Baseline", "Sweep 1", "Sweep 2", "Intentionally broken case", "Recovery", "Expected observation", "Common mistake", "Ctrl+C", "rollback"):
            self.assertIn(marker, walkthrough)
        combined = "\n".join(self.docs.values()).lower()
        for marker in ("matched filtering", "slow-time fft", "bounded", "private seed", "p43", "not itself a detector"):
            self.assertIn(marker, combined)
        for marker in ("Observation checks", "Interpretation checks", "Prediction checks", "teach-back rubric"):
            self.assertIn(marker, self.docs["checks.md"])

    def test_p42_only_rollback_preserves_p41_and_p43_identity(self):
        rolled = copy.deepcopy(self.manifest)
        neighbors_before = {x["id"]: copy.deepcopy(x) for x in rolled["modules"] if x["id"] in {"P41", "P43"}}
        next(x for x in rolled["modules"] if x["id"] == "P42")["status"] = "scaffolded"
        neighbors_after = {x["id"]: x for x in rolled["modules"] if x["id"] in {"P41", "P43"}}
        self.assertEqual(neighbors_after, neighbors_before)
        self.assertTrue(any("status" in error for error in validate_p42_contract(MODULE, rolled)))

    def test_retained_evidence_structure_when_evidence_is_written(self):
        evidence = ROOT / "docs/evidence/P42-2026-08-03.md"
        self.assertTrue(evidence.is_file())
        text = evidence.read_text(encoding="utf-8")
        for heading in ("## Outcome and claim boundary", "## Acceptance mapping", "## Physical model and independent static oracle", "## Figure and metric inventory", "## Focused test coverage", "## Exact commands and results", "## Rollback and recovery", "## Residual risks and unperformed validation"):
            self.assertIn(heading, text)
        for command in ("DSP_RADAR_VERIFY_PROFILE=contract python3 scripts/validate_curriculum.py", "DSP_RADAR_VERIFY_PROFILE=quick python3 -m unittest discover -s tests -v", "DSP_RADAR_VERIFY_PROFILE=full ./scripts/agent-verify.sh"):
            self.assertIn(command, text)
        self.assertIn("rollback", text.lower())
        self.assertIn("matlab and octave did not run", re.sub(r"\s+", " ", text.lower()))
        data = evidence.read_bytes(); self.assertTrue(data.endswith(b"\n")); self.assertFalse(data.endswith(b"\n\n")); self.assertNotIn(b"\r", data)


if __name__ == "__main__":
    unittest.main()
