from __future__ import annotations

import copy
import cmath
import json
import math
import random
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/14-compare-periodogram-and-welch-psd-estimates"
QUESTION = "Why does averaging make a noise spectrum easier to interpret?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def finite_real(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_psd_inputs(
    fs_hz: float = 1024.0,
    record_sample_count: int = 4096,
    strong_tone_hz: float = 160.0,
    weak_tone_hz: float = 172.0,
    segment_lengths: tuple[int, ...] = (1024, 512, 256),
    baseline_segment_length: int = 512,
    baseline_overlap_fraction: float = 0.5,
    overlap_sweep: tuple[float, ...] = (0.0, 0.5, 0.75),
    seed_sweep: tuple[int, ...] = tuple(range(1014, 1038)),
) -> None:
    """Independent pre-allocation contract for the bounded teaching experiment."""
    if not finite_real(fs_hz) or fs_hz <= 0:
        raise ValueError("sample rate must be a positive finite real")
    if not isinstance(record_sample_count, int) or isinstance(record_sample_count, bool):
        raise ValueError("record count must be an integer")
    if record_sample_count != 4096:
        raise ValueError("the canonical record is exactly 4096 samples")
    if not all(finite_real(f) and 0 < f < fs_hz / 2 for f in (strong_tone_hz, weak_tone_hz)):
        raise ValueError("tones must be finite and inside the one-sided band")
    if not strong_tone_hz < weak_tone_hz:
        raise ValueError("the strong tone must precede the weak tone")
    if segment_lengths != (1024, 512, 256):
        raise ValueError("segment sweep must preserve the canonical descending choices")
    if any(not isinstance(n, int) or isinstance(n, bool) or n < 32 or n > record_sample_count or n % 2 for n in segment_lengths):
        raise ValueError("segments must be bounded, even integers")
    if baseline_segment_length != 512 or baseline_overlap_fraction != 0.5:
        raise ValueError("baseline is 512 samples with 50 percent overlap")
    if overlap_sweep != (0.0, 0.5, 0.75):
        raise ValueError("overlap sweep must preserve the three canonical cases")
    if any(not finite_real(overlap) or not 0 <= overlap < 1 for overlap in overlap_sweep):
        raise ValueError("overlaps must be finite fractions below one")
    if not isinstance(seed_sweep, tuple) or len(seed_sweep) < 3 or len(seed_sweep) > 24:
        raise ValueError("seed sweep must have a bounded set of at least three trials")
    if any(not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 2**32 - 1 for seed in seed_sweep):
        raise ValueError("seeds must be unsigned 32-bit integers")
    if len(set(seed_sweep)) != len(seed_sweep):
        raise ValueError("seed sweep must contain distinct trials")
    # The tone pair must cross the approximate Hann null-to-null boundary so
    # the long segment resolves the pair while the short segment blurs it.
    tone_separation_hz = weak_tone_hz - strong_tone_hz
    long_segment_main_lobe_hz = 4 * fs_hz / max(segment_lengths)
    short_segment_main_lobe_hz = 4 * fs_hz / min(segment_lengths)
    if not long_segment_main_lobe_hz < tone_separation_hz < short_segment_main_lobe_hz:
        raise ValueError("tone separation must cross the long/short Hann boundary")


def one_sided_psd(samples: list[float], fs_hz: float, window: list[float]) -> tuple[list[float], float]:
    """Direct DFT reference: same explicit operation expected from P14."""
    count = len(samples)
    if count != len(window) or count < 2 or count % 2:
        raise ValueError("PSD needs an equal-length, even record")
    window_power = sum(value * value for value in window)
    if window_power <= 0:
        raise ValueError("window energy must be positive")
    transformed = [sum(samples[n] * window[n] * cmath.exp(-2j * math.pi * k * n / count)
                       for n in range(count)) for k in range(count // 2 + 1)]
    density = [abs(value) ** 2 / (fs_hz * window_power) for value in transformed]
    for index in range(1, count // 2):
        density[index] *= 2.0
    return density, fs_hz / count


def hann_symmetric(count: int) -> list[float]:
    return [0.5 - 0.5 * math.cos(2 * math.pi * n / (count - 1)) for n in range(count)]


def welch_psd(samples: list[float], fs_hz: float, segment_count: int, overlap: float) -> tuple[list[float], float, int]:
    hop = int(segment_count * (1 - overlap))
    if hop < 1:
        raise ValueError("overlap leaves no forward progress")
    starts = list(range(0, len(samples) - segment_count + 1, hop))
    if not starts:
        raise ValueError("no complete segments")
    window = hann_symmetric(segment_count)
    estimates = [one_sided_psd(samples[start:start + segment_count], fs_hz, window)[0] for start in starts]
    return [sum(column) / len(estimates) for column in zip(*estimates)], fs_hz / segment_count, len(starts)


def welch_psd_at_bins(
    samples: list[float],
    fs_hz: float,
    segment_count: int,
    overlap: float,
    bins: range,
) -> tuple[list[float], int]:
    """Evaluate selected interior bins without requiring a third-party FFT."""
    hop = int(segment_count * (1 - overlap))
    starts = list(range(0, len(samples) - segment_count + 1, hop))
    window = hann_symmetric(segment_count)
    window_power = sum(value * value for value in window)
    densities = []
    for bin_index in bins:
        segment_densities = []
        for start in starts:
            transformed = sum(
                samples[start + n]
                * window[n]
                * cmath.exp(-2j * math.pi * bin_index * n / segment_count)
                for n in range(segment_count)
            )
            segment_densities.append(
                2 * abs(transformed) ** 2 / (fs_hz * window_power)
            )
        densities.append(sum(segment_densities) / len(segment_densities))
    return densities, len(starts)


def validate_p14_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        candidate = module_dir / name
        if not candidate.is_file():
            errors.append(f"P14 missing {name}")
        elif not candidate.read_text(encoding="utf-8").strip():
            errors.append(f"P14 empty {name}")
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    entries = [entry for entry in modules if isinstance(entry, dict) and entry.get("id") == "P14"]
    if len(entries) != 1:
        return errors + [f"expected one P14 manifest entry, found {len(entries)}"]
    expected = {
        "number": 14, "id": "P14", "title": "Compare Periodogram and Welch PSD Estimates",
        "guiding_question": QUESTION, "phase": 2, "phase_title": "Fourier, Spectral, and I/Q Intuition",
        "slug": "compare-periodogram-and-welch-psd-estimates",
        "folder": "modules/14-compare-periodogram-and-welch-psd-estimates",
        "status": "implemented", "implementation_batch": "P14",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P14 {key} must be {value!r}")
    return errors


class P14ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.experiment = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")

    def test_artifacts_manifest_identity_and_prerequisite_are_permanent_facts(self):
        self.assertEqual(validate_p14_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            self.assertGreater((MODULE / name).stat().st_size, 100)
        for text in (self.readme, self.experiment, self.lesson, self.walkthrough, self.checks):
            self.assertIn(QUESTION, text)
        modules = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(modules["P13"]["status"], "implemented")
        self.assertIn("P13", self.readme)
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertRegex(module_index, r"\| \[P14\].*\| implemented \|")

    def test_contract_rejects_malformed_fixture_missing_empty_duplicate_and_bad_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "checks.md").unlink()
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p14_contract(fixture, self.manifest)
            self.assertIn("P14 missing checks.md", errors)
            self.assertIn("P14 empty lesson.md", errors)
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][13]))
        self.assertIn("expected one P14 manifest entry, found 2", validate_p14_contract(MODULE, duplicate))
        self.assertIn("manifest modules must be a list", validate_p14_contract(MODULE, {"modules": "P14"}))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][13]["status"] = "scaffolded"
        malformed["modules"][13]["guiding_question"] = "generic"
        errors = validate_p14_contract(MODULE, malformed)
        self.assertIn("P14 status must be 'implemented'", errors)
        self.assertIn(f"P14 guiding_question must be {QUESTION!r}", errors)

    def test_deterministic_controls_and_manual_psd_operation_are_visible(self):
        for marker in (
            "random_seed = 1014;", "fs_hz = 1024;", "record_sample_count = 4096;",
            "tone_frequency_hz = [160 172];", "tone_amplitude_v = [1.0 0.12];",
            "segment_length_sweep = [1024 512 256];", "baseline_segment_length = 512;",
            "baseline_overlap_fraction = 0.50;", "overlap_fraction_sweep = [0 0.50 0.75];",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "baseline_window = 0.5 - 0.5*cos(",
            "fft(windowed_segment_v, baseline_segment_length)",
            "baseline_window_energy = sum(baseline_window.^2);",
            "2*segment_one_sided_psd_v2_per_hz(2:end-1);", "10*log10(",
            "welch_psd_v2_per_hz = mean(baseline_segment_psd_v2_per_hz, 1);",
        ):
            self.assertIn(marker, self.experiment)
        source = "\n".join(line.split("%", 1)[0] for line in self.experiment.splitlines()).lower()
        for hidden_call in ("periodogram(", "pwelch(", "pspectrum(", "spectrogram(", "dsp.", "signal."):
            self.assertNotIn(hidden_call, source)

    def test_input_validation_rejects_malformed_controls_before_resource_work(self):
        validate_psd_inputs()
        for kwargs in (
            {"fs_hz": 0.0}, {"fs_hz": float("nan")}, {"fs_hz": True},
            {"record_sample_count": 4095}, {"record_sample_count": 4096.0},
            {"strong_tone_hz": 0.0}, {"weak_tone_hz": 512.0}, {"weak_tone_hz": 160.0},
            {"weak_tone_hz": 164.0}, {"weak_tone_hz": 176.0},
            {"segment_lengths": (1024, 512)}, {"segment_lengths": (1024, 512, 257)},
            {"baseline_segment_length": 256}, {"baseline_overlap_fraction": 0.75},
            {"overlap_sweep": (0.0, 0.5)}, {"overlap_sweep": (0.0, 0.5, 1.0)},
            {"seed_sweep": (1014, 1014, 1016)}, {"seed_sweep": (1014, 1015)},
            {"seed_sweep": (1014, -1, 1016)},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    validate_psd_inputs(**kwargs)
        guard = self.experiment.index("P14 resource ceilings must remain fixed.")
        self.assertLess(guard, self.experiment.index("stream = RandStream"))
        for marker in ("max_record_samples = 4096;", "max_fft_count = 4096;", "max_segment_count = 32;", "max_seed_trials = 24;", "max_figure_groups = 4;", "record_sample_count <= max_record_samples"):
            self.assertIn(marker, self.experiment)
        tradeoff_guard = self.experiment.index(
            "Tone separation must exceed the longest-segment Hann main-lobe width"
        )
        self.assertLess(tradeoff_guard, self.experiment.index("stream = RandStream"))

    def test_manual_one_sided_psd_scaling_preserves_windowed_power(self):
        samples = [0.7 * math.cos(2 * math.pi * 9 * n / 64) + 0.2 * math.sin(2 * math.pi * 17 * n / 64) for n in range(64)]
        window = hann_symmetric(64)
        density, bin_width = one_sided_psd(samples, 1024.0, window)
        integrated_power = sum(density) * bin_width
        expected_power = sum((x * w) ** 2 for x, w in zip(samples, window)) / sum(w * w for w in window)
        self.assertAlmostEqual(integrated_power, expected_power, places=12)
        # DC and Nyquist must not be doubled; an interior bin must be.
        impulse = [1.0] + [0.0] * 63
        rect_density, _ = one_sided_psd(impulse, 1024.0, [1.0] * 64)
        self.assertAlmostEqual(rect_density[1], 2 * rect_density[0], places=15)
        self.assertAlmostEqual(rect_density[-1], rect_density[0], places=15)

    def test_independent_model_shows_averaging_variance_and_segment_resolution_tradeoff(self):
        # Small independent model avoids depending on MATLAB yet exercises the same estimator.
        periodogram_levels, welch_levels = [], []
        for seed in range(24):
            rng = random.Random(1014 + seed)
            noise = [rng.gauss(0.0, 1.0) for _ in range(64)]
            raw, _ = one_sided_psd(noise, 1024.0, hann_symmetric(64))
            averaged, _, count = welch_psd(noise, 1024.0, 16, 0.5)
            periodogram_levels.append(raw[11])
            welch_levels.append(averaged[3])
            self.assertEqual(count, 7)
        def coefficient_of_variation(values: list[float]) -> float:
            mean = sum(values) / len(values)
            return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values)) / mean
        self.assertLess(coefficient_of_variation(welch_levels), coefficient_of_variation(periodogram_levels))
        self.assertEqual([1024 / n for n in (1024, 512, 256)], [1.0, 2.0, 4.0])
        self.assertEqual([len(range(0, 4096 - 512 + 1, hop)) for hop in (512, 256, 128)], [8, 15, 29])
        # Twelve hertz lies above the 4 Hz long-segment Hann main-lobe scale
        # and below the 16 Hz short-segment scale, so the sweep crosses the
        # intended physical-resolution boundary.
        self.assertEqual(172 - 160, 12)

    def test_canonical_segment_sweep_behaviorally_blurs_the_weak_tone(self):
        fs_hz = 1024.0
        sample_count = 4096
        rng = random.Random(1014)
        raw_noise = [rng.gauss(0.0, 1.0) for _ in range(sample_count)]
        raw_noise_rms = math.sqrt(
            sum(value * value for value in raw_noise) / sample_count
        )
        samples = [
            math.cos(2 * math.pi * 160 * n / fs_hz + 0.3)
            + 0.12 * math.cos(2 * math.pi * 172 * n / fs_hz - 0.7)
            + 0.35 * raw_noise[n] / raw_noise_rms
            for n in range(sample_count)
        ]

        prominence_db = []
        segment_counts = []
        for segment_length in (1024, 512, 256):
            first_bin = round(160 * segment_length / fs_hz)
            last_bin = round(172 * segment_length / fs_hz)
            density, segment_count = welch_psd_at_bins(
                samples,
                fs_hz,
                segment_length,
                0.5,
                range(first_bin, last_bin + 1),
            )
            prominence_db.append(
                10 * math.log10(density[-1] / min(density))
            )
            segment_counts.append(segment_count)

        self.assertEqual(segment_counts, [7, 15, 31])
        self.assertGreater(prominence_db[0], prominence_db[-1] + 5.0)
        self.assertIn(
            "segment_weak_valley_prominence_db(1) >",
            self.experiment,
        )
        self.assertIn("results.tone_separation_hz", self.experiment)

    def test_linear_power_must_be_averaged_before_db_and_broken_case_recovers(self):
        levels = [1.0, 9.0]
        correct_db = 10 * math.log10(sum(levels) / len(levels))
        broken_db = sum(10 * math.log10(value) for value in levels) / len(levels)
        self.assertGreater(correct_db - broken_db, 2.0)
        broken = self.experiment.split("%% Broken case", 1)[1]
        for marker in (
            "broken_average_psd_db = mean(broken_segment_psd_db, 1);",
            "recovered_average_psd_db = 10*log10(max(mean(",
            "average logarithmic display values",
            "averaging V^2/Hz first",
        ):
            self.assertIn(marker, broken)
        self.assertIn("results.broken_average_psd_db", self.experiment)
        self.assertIn("results.recovered_average_psd_db", self.experiment)

    def test_sweeps_change_one_control_and_report_physical_tradeoffs(self):
        segment = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        overlap = self.experiment.split("%% Sweep 2", 1)[1].split("%% Broken case", 1)[0]
        self.assertIn("sweep_segment_length = segment_length_sweep(sweep_index);", segment)
        self.assertIn("sweep_hop_samples = sweep_segment_length/2;", segment)
        self.assertIn("sweep_overlap_samples = overlap_sweep_samples(sweep_index);", overlap)
        self.assertIn("baseline_segment_length", overlap)
        for section, forbidden in ((segment, ("fs_hz =", "record_sample_count =", "tone_frequency_hz =", "tone_amplitude_v =")), (overlap, ("fs_hz =", "record_sample_count =", "baseline_segment_length =", "tone_frequency_hz ="))):
            for assignment in forbidden:
                self.assertNotIn(assignment, section)
        for metric in ("results.segment_bin_spacing_hz", "results.segment_count", "results.periodogram_probe_psd_v2_per_hz", "results.segment_weak_valley_prominence_db", "V^2/Hz", "Frequency (Hz)"):
            self.assertIn(metric, self.experiment)

    def test_recovery_isolation_timeout_compatibility_and_rollback_are_documented(self):
        lowered = self.experiment.lower()
        for forbidden in ("close all", "clear all", "clearvars", "pause(", "input(", "while ", "parfor", "timer(", "webread(", "fopen(", "save(", "writematrix("):
            self.assertNotIn(forbidden, lowered)
        self.assertIn("'Tag', 'P14'", self.experiment)
        combined = "\n".join((self.readme, self.lesson, self.walkthrough, self.checks)).lower()
        for phrase in ("ctrl+c", "private seed", "writes no files", "global random stream", "manifest status to `scaffolded`"):
            self.assertIn(phrase, combined)
        self.assertIn("base MATLAB", self.readme)

    def test_concept_first_docs_evidence_and_no_placeholders_or_runtime_overclaim(self):
        combined = "\n".join((self.readme, self.experiment, self.lesson, self.walkthrough, self.checks))
        self.assertNotRegex(combined, r"(?i)\b(TODO|TBD|lorem ipsum)\b")
        self.assertNotIn("matlab runtime passed", combined.lower())
        self.assertNotIn("field validated", combined.lower())
        for text, headings in ((self.lesson, ("## Physical mental model", "## Limiting cases", "## Radar connection")), (self.walkthrough, ("## Baseline", "## Sweep 1", "## Sweep 2", "## Broken case", "## Safe rerun")), (self.checks, ("## Baseline observation checks", "## Interpretation checks", "## Teach-back completion"))):
            for heading in headings:
                self.assertIn(heading, text)
        evidence_files = sorted((ROOT / "docs/evidence").glob("P14-*.md"))
        self.assertTrue(evidence_files, "P14 requires retained evidence")
        evidence = evidence_files[-1].read_text(encoding="utf-8")
        for marker in ("acceptance", "dsp_radar_verify_profile", "does **not** claim matlab", "rollback", "residual"):
            self.assertIn(marker, evidence.lower())


if __name__ == "__main__":
    unittest.main()
