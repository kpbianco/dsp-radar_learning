from __future__ import annotations

import cmath
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/15-use-a-spectrogram-to-see-time-varying-frequency"
QUESTION = "How do window duration and overlap control time-frequency visibility?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_stft_inputs(
    fs_hz: float = 1024.0,
    record_sample_count: int = 4096,
    window_lengths: tuple[int, ...] = (512, 128, 64),
    matched_overlap: float = 0.5,
    overlap_sweep: tuple[float, ...] = (0.0, 0.5, 0.75),
    burst_start_sample: int = 1536,
    burst_sample_count: int = 64,
    hop_sample: int = 2816,
    component_frequencies_hz: tuple[float, ...] = (90, 220, 320, 380, 156, 174),
    broken_fft_length: int = 512,
    max_frames_per_case: int = 256,
    max_spectrogram_cells: int = 100000,
    max_sweep_cases: int = 4,
    max_figure_groups: int = 4,
    actual_figure_groups: int = 4,
) -> None:
    """Independent pre-allocation contract for the bounded P15 experiment."""
    if not finite_real(fs_hz) or fs_hz <= 0:
        raise ValueError("sample rate must be a positive finite real")
    if (
        not isinstance(record_sample_count, int)
        or isinstance(record_sample_count, bool)
        or record_sample_count != 4096
    ):
        raise ValueError("the canonical record has exactly 4096 samples")
    if window_lengths != (512, 128, 64):
        raise ValueError("window sweep identity changed")
    if any(
        not isinstance(length, int)
        or isinstance(length, bool)
        or length < 2
        or length > 512
        or length % 2
        for length in window_lengths
    ):
        raise ValueError("windows must be bounded even integers")
    if not finite_real(matched_overlap) or matched_overlap != 0.5:
        raise ValueError("matched overlap must be 50 percent")
    if overlap_sweep != (0.0, 0.5, 0.75):
        raise ValueError("overlap sweep identity changed")
    if any(not finite_real(value) or not 0 <= value < 1 for value in overlap_sweep):
        raise ValueError("overlaps must be finite fractions below one")
    for length in set(window_lengths + (128,)):
        for overlap in set(overlap_sweep + (matched_overlap,)):
            overlap_samples = length * overlap
            hop = length - overlap_samples
            if overlap_samples != int(overlap_samples) or hop < 1:
                raise ValueError("overlap must create integer forward progress")
    if (
        not isinstance(burst_start_sample, int)
        or isinstance(burst_start_sample, bool)
        or not isinstance(burst_sample_count, int)
        or isinstance(burst_sample_count, bool)
        or burst_sample_count != 64
        or burst_start_sample < 0
        or burst_start_sample + burst_sample_count > record_sample_count
    ):
        raise ValueError("burst support must be canonical and in-record")
    if (
        not isinstance(hop_sample, int)
        or isinstance(hop_sample, bool)
        or not 0 < hop_sample < record_sample_count
    ):
        raise ValueError("hop must be at an interior sample")
    if len(component_frequencies_hz) != 6 or any(
        not finite_real(frequency) or not 0 < frequency < fs_hz / 2
        for frequency in component_frequencies_hz
    ):
        raise ValueError("component frequencies must lie inside Nyquist")
    if (
        not isinstance(broken_fft_length, int)
        or isinstance(broken_fft_length, bool)
        or broken_fft_length != 512
        or broken_fft_length < window_lengths[-1]
    ):
        raise ValueError("broken FFT must pad 64 samples to 512")

    hop_separation = component_frequencies_hz[-1] - component_frequencies_hz[-2]
    long_hann_width = 4 * fs_hz / window_lengths[0]
    short_hann_width = 4 * fs_hz / window_lengths[-1]
    if not long_hann_width < hop_separation < short_hann_width:
        raise ValueError("hop separation must cross the long/short Hann boundary")

    frame_counts = []
    for length in window_lengths:
        hop = int(length * (1 - matched_overlap))
        if (record_sample_count - length) % hop:
            raise ValueError("window grid must end on the record boundary")
        frame_counts.append(1 + (record_sample_count - length) // hop)
    overlap_counts = []
    for overlap in overlap_sweep:
        hop = int(128 * (1 - overlap))
        if (record_sample_count - 128) % hop:
            raise ValueError("overlap grid must end on the record boundary")
        overlap_counts.append(1 + (record_sample_count - 128) // hop)
    if len(window_lengths) > max_sweep_cases or len(overlap_sweep) > max_sweep_cases:
        raise ValueError("sweep case ceiling exceeded")
    if max(frame_counts + overlap_counts) > max_frames_per_case:
        raise ValueError("frame ceiling exceeded")
    largest_window_cells = max(
        (length // 2 + 1) * count
        for length, count in zip(window_lengths, frame_counts)
    )
    largest_overlap_cells = (128 // 2 + 1) * max(overlap_counts)
    broken_cells = (broken_fft_length // 2 + 1) * frame_counts[-1]
    if max(largest_window_cells, largest_overlap_cells, broken_cells) > max_spectrogram_cells:
        raise ValueError("spectrogram cell ceiling exceeded")
    if actual_figure_groups > max_figure_groups:
        raise ValueError("figure ceiling exceeded")


def hann_symmetric(count: int) -> list[float]:
    return [
        0.5 - 0.5 * math.cos(2 * math.pi * index / (count - 1))
        for index in range(count)
    ]


def one_sided_psd(
    samples: list[float], fs_hz: float, window: list[float], fft_length: int | None = None
) -> tuple[list[float], float]:
    """Direct DFT reference for P15's visible frame equation."""
    count = len(samples)
    if count != len(window) or count < 2 or count % 2:
        raise ValueError("PSD requires an equal-length even frame and window")
    fft_length = count if fft_length is None else fft_length
    if fft_length < count or fft_length % 2:
        raise ValueError("FFT length must be even and at least the frame length")
    window_energy = sum(value * value for value in window)
    transformed = [
        sum(
            samples[index]
            * window[index]
            * cmath.exp(-2j * math.pi * bin_index * index / fft_length)
            for index in range(count)
        )
        for bin_index in range(fft_length // 2 + 1)
    ]
    density = [abs(value) ** 2 / (fs_hz * window_energy) for value in transformed]
    for bin_index in range(1, fft_length // 2):
        density[bin_index] *= 2
    return density, fs_hz / fft_length


def validate_p15_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        candidate = module_dir / name
        if not candidate.is_file():
            errors.append(f"P15 missing {name}")
        elif not candidate.read_text(encoding="utf-8").strip():
            errors.append(f"P15 empty {name}")
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    entries = [
        entry
        for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P15"
    ]
    if len(entries) != 1:
        return errors + [f"expected one P15 manifest entry, found {len(entries)}"]
    expected = {
        "number": 15,
        "id": "P15",
        "title": "Use a Spectrogram to See Time-Varying Frequency",
        "guiding_question": QUESTION,
        "phase": 2,
        "phase_title": "Fourier, Spectral, and I/Q Intuition",
        "slug": "use-a-spectrogram-to-see-time-varying-frequency",
        "folder": "modules/15-use-a-spectrogram-to-see-time-varying-frequency",
        "status": "implemented",
        "implementation_batch": "P15",
    }
    for key, value in expected.items():
        if entries[0].get(key) != value:
            errors.append(f"P15 {key} must be {value!r}")
    return errors


class P15ModuleTests(unittest.TestCase):
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

    def test_artifacts_manifest_identity_and_prerequisite_are_permanent_facts(self):
        self.assertEqual(validate_p15_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            self.assertGreater((MODULE / name).stat().st_size, 100)
        for text in (
            self.readme,
            self.experiment,
            self.lesson,
            self.walkthrough,
            self.checks,
        ):
            self.assertIn(QUESTION, text)
        modules = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(modules["P14"]["status"], "implemented")
        self.assertIn("P14", self.readme)
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertRegex(module_index, r"\| \[P15\].*\| implemented \|")

    def test_contract_rejects_missing_empty_duplicate_nonlist_and_bad_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "checks.md").unlink()
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            errors = validate_p15_contract(fixture, self.manifest)
            self.assertIn("P15 missing checks.md", errors)
            self.assertIn("P15 empty lesson.md", errors)
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][14]))
        self.assertIn(
            "expected one P15 manifest entry, found 2",
            validate_p15_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p15_contract(MODULE, {"modules": "P15"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][14]["status"] = "scaffolded"
        malformed["modules"][14]["guiding_question"] = "generic"
        errors = validate_p15_contract(MODULE, malformed)
        self.assertIn("P15 status must be 'implemented'", errors)
        self.assertIn(f"P15 guiding_question must be {QUESTION!r}", errors)

    def test_deterministic_signal_and_manual_stft_operation_are_visible(self):
        for marker in (
            "random_seed = 1015;",
            "fs_hz = 1024;",
            "record_sample_count = 4096;",
            "steady_frequency_hz = 90;",
            "chirp_start_frequency_hz = 220;",
            "chirp_stop_frequency_hz = 320;",
            "burst_frequency_hz = 380;",
            "burst_sample_count = 64;",
            "hop_frequency_before_hz = 156;",
            "hop_frequency_after_hz = 174;",
            "hop_time_s = 2.75;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "chirp_gate(chirp_active_index) = 1;",
            "0.5*chirp_rate_hz_per_s*",
            "chirp_v = chirp_amplitude_v*chirp_gate.*cos(chirp_phase_track_rad);",
            "baseline_window = 0.5 - 0.5*cos(",
            "windowed_frame_v = record_v(frame_sample_index).*baseline_window;",
            "frame_fft_v = fft(windowed_frame_v, baseline_window_length);",
            "abs(frame_fft_v).^2/(fs_hz*baseline_window_energy)",
            "2*frame_one_sided_psd_v2_per_hz(2:end-1);",
            "(baseline_window_length - 1)/2)/fs_hz;",
        ):
            self.assertIn(marker, self.experiment)
        executable = "\n".join(
            line.split("%", 1)[0] for line in self.experiment.splitlines()
        ).lower()
        for hidden_call in (
            "spectrogram(",
            "stft(",
            "pspectrum(",
            "periodogram(",
            "pwelch(",
            "dsp.",
            "signal.",
        ):
            self.assertNotIn(hidden_call, executable)

    def test_malformed_and_resource_controls_fail_before_work(self):
        validate_stft_inputs()
        invalid_cases = (
            {"fs_hz": 0.0},
            {"fs_hz": float("nan")},
            {"fs_hz": True},
            {"record_sample_count": 4095},
            {"record_sample_count": 4096.0},
            {"window_lengths": (512, 128)},
            {"window_lengths": (512, 128, 63)},
            {"matched_overlap": 0.75},
            {"matched_overlap": float("inf")},
            {"overlap_sweep": (0.0, 0.5)},
            {"overlap_sweep": (0.0, 0.5, 1.0)},
            {"burst_start_sample": 4090},
            {"burst_sample_count": 63},
            {"hop_sample": 0},
            {"component_frequencies_hz": (90, 220, 320, 512, 156, 174)},
            {"component_frequencies_hz": (90, 220, 320, 380, 156, 164)},
            {"component_frequencies_hz": (90, 220, 320, 380, 156, 220)},
            {"broken_fft_length": 64},
            {"broken_fft_length": 513},
            {"max_sweep_cases": 2},
            {"max_frames_per_case": 100},
            {"max_spectrogram_cells": 30000},
            {"max_figure_groups": 3},
            {"actual_figure_groups": 5},
        )
        for kwargs in invalid_cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    validate_stft_inputs(**kwargs)
        guard = self.experiment.index("P15 resource ceilings must remain fixed.")
        for work_marker in (
            "stream = RandStream",
            "chirp_gate = zeros",
            "baseline_psd_v2_per_hz = zeros",
            "figure('Name'",
        ):
            self.assertLess(guard, self.experiment.index(work_marker))
        for marker in (
            "max_record_samples = 4096;",
            "max_window_length = 512;",
            "max_fft_length = 512;",
            "max_frames_per_case = 256;",
            "max_spectrogram_cells = 100000;",
            "max_figure_groups = 4;",
            "window_frequency_bin_count.*window_frame_count",
            "actual_figure_group_count <= max_figure_groups",
        ):
            self.assertIn(marker, self.experiment)
        self.assertEqual(self.experiment.count("figure('Name'"), 4)

    def test_one_sided_stft_psd_preserves_window_normalized_power(self):
        samples = [
            0.7 * math.cos(2 * math.pi * 9 * index / 64)
            + 0.2 * math.sin(2 * math.pi * 17 * index / 64)
            for index in range(64)
        ]
        window = hann_symmetric(64)
        density, bin_spacing = one_sided_psd(samples, 1024.0, window)
        integrated_power = sum(density) * bin_spacing
        expected_power = sum(
            (sample * weight) ** 2 for sample, weight in zip(samples, window)
        ) / sum(weight * weight for weight in window)
        self.assertAlmostEqual(integrated_power, expected_power, places=12)
        impulse = [1.0] + [0.0] * 63
        rectangular, _ = one_sided_psd(impulse, 1024.0, [1.0] * 64)
        self.assertAlmostEqual(rectangular[1], 2 * rectangular[0], places=15)
        self.assertAlmostEqual(rectangular[-1], rectangular[0], places=15)

    def test_baseline_steady_tone_remains_horizontal_across_the_record(self):
        fs_hz = 1024.0
        sample_count = 4096
        steady_frequency_hz = 90.0
        samples = [
            0.35 * math.cos(2 * math.pi * steady_frequency_hz * index / fs_hz + 0.2)
            for index in range(sample_count)
        ]
        window_length = 128
        window = hann_symmetric(window_length)
        observed_peak_hz: list[float] = []

        for frame_start in (0, 1984, sample_count - window_length):
            density, spacing_hz = one_sided_psd(
                samples[frame_start : frame_start + window_length],
                fs_hz,
                window,
            )
            search_bins = range(
                math.ceil(64 / spacing_hz), math.floor(120 / spacing_hz) + 1
            )
            peak_bin = max(search_bins, key=density.__getitem__)
            observed_peak_hz.append(peak_bin * spacing_hz)

        self.assertEqual(observed_peak_hz, [88.0, 88.0, 88.0])
        self.assertTrue(
            all(
                abs(observed - steady_frequency_hz) < 8.0
                for observed in observed_peak_hz
            )
        )
        for marker in (
            "steady_v = steady_amplitude_v*cos",
            "plot([0 record_duration_s], steady_frequency_hz*[1 1]",
        ):
            self.assertIn(marker, self.experiment)

    def test_baseline_chirp_ridge_tracks_linear_frequency_within_one_bin(self):
        fs_hz = 1024.0
        sample_count = 4096
        chirp_start_sample = 512
        chirp_stop_sample = 2304
        taper_count = 64
        chirp_start_hz = 220.0
        chirp_stop_hz = 320.0
        chirp_start_s = chirp_start_sample / fs_hz
        chirp_stop_s = chirp_stop_sample / fs_hz
        chirp_rate_hz_per_s = (chirp_stop_hz - chirp_start_hz) / (
            chirp_stop_s - chirp_start_s
        )

        samples = [0.0] * sample_count
        active_count = chirp_stop_sample - chirp_start_sample
        for local_index in range(active_count):
            if local_index < taper_count:
                gate = math.sin(
                    math.pi * local_index / (2 * (taper_count - 1))
                ) ** 2
            elif local_index >= active_count - taper_count:
                gate = math.sin(
                    math.pi * (active_count - 1 - local_index)
                    / (2 * (taper_count - 1))
                ) ** 2
            else:
                gate = 1.0
            sample_index = chirp_start_sample + local_index
            time_from_start_s = sample_index / fs_hz - chirp_start_s
            phase_rad = 2 * math.pi * (
                chirp_start_hz * time_from_start_s
                + 0.5 * chirp_rate_hz_per_s * time_from_start_s**2
            ) - 0.4
            samples[sample_index] = 0.25 * gate * math.cos(phase_rad)

        window_length = 128
        window = hann_symmetric(window_length)
        ridge_hz: list[float] = []
        expected_hz: list[float] = []
        for frame_start in range(0, sample_count - window_length + 1, 64):
            center_s = (frame_start + (window_length - 1) / 2) / fs_hz
            if not (
                chirp_start_s + taper_count / fs_hz
                <= center_s
                <= chirp_stop_s - taper_count / fs_hz
            ):
                continue
            density, spacing_hz = one_sided_psd(
                samples[frame_start : frame_start + window_length],
                fs_hz,
                window,
            )
            search_bins = range(
                math.ceil(204 / spacing_hz), math.floor(336 / spacing_hz) + 1
            )
            ridge_bin = max(search_bins, key=density.__getitem__)
            ridge_hz.append(ridge_bin * spacing_hz)
            expected_hz.append(
                chirp_start_hz + chirp_rate_hz_per_s * (center_s - chirp_start_s)
            )

        mean_absolute_error_hz = sum(
            abs(actual - expected)
            for actual, expected in zip(ridge_hz, expected_hz)
        ) / len(ridge_hz)
        self.assertGreater(len(ridge_hz), 20)
        self.assertGreater(ridge_hz[-1] - ridge_hz[0], 80.0)
        self.assertTrue(
            all(right >= left for left, right in zip(ridge_hz, ridge_hz[1:]))
        )
        self.assertLess(mean_absolute_error_hz, 8.0)
        for marker in (
            "chirp_expected_frequency_hz = chirp_start_frequency_hz +",
            "baseline_chirp_ridge_mae_hz =",
            "baseline_chirp_ridge_mae_hz < baseline_bin_spacing_hz",
        ):
            self.assertIn(marker, self.experiment)

    def test_window_sweep_crosses_time_frequency_visibility_boundary(self):
        lengths = (512, 128, 64)
        self.assertEqual([1024 / length for length in lengths], [2.0, 8.0, 16.0])
        self.assertEqual(
            [4 * 1024 / length for length in lengths], [8.0, 32.0, 64.0]
        )
        self.assertEqual(
            [len(range(0, 4096 - length + 1, length // 2)) for length in lengths],
            [15, 63, 127],
        )
        separation = 174 - 156
        self.assertGreater(separation, 8)
        self.assertLess(separation, 64)
        for marker in (
            "window_length_sweep = [512 128 64];",
            "sweep_window_length = window_length_sweep(sweep_index);",
            "sweep_hop_samples = window_hop_samples(sweep_index);",
            "results.window_duration_ms",
            "results.window_hann_main_lobe_width_hz",
            "results.window_resolution_ratio",
        ):
            self.assertIn(marker, self.experiment)

    def test_long_hop_centered_frame_separates_frequencies_short_frame_blends_them(self):
        fs_hz = 1024.0
        hop_sample = 2816

        def hop_sample_value(index: int) -> float:
            if index < hop_sample:
                phase = -0.3 + 2 * math.pi * 156 * index / fs_hz
            else:
                phase = (
                    -0.3
                    + 2 * math.pi * 156 * hop_sample / fs_hz
                    + 2 * math.pi * 174 * (index - hop_sample) / fs_hz
                )
            return 0.28 * math.cos(phase)

        peak_sets: list[list[float]] = []
        for length, start in ((512, 2560), (64, 2784)):
            samples = [hop_sample_value(index) for index in range(start, start + length)]
            density, spacing = one_sided_psd(samples, fs_hz, hann_symmetric(length))
            first_bin = math.ceil(130 / spacing)
            last_bin = math.floor(200 / spacing)
            peaks = [
                bin_index * spacing
                for bin_index in range(first_bin + 1, last_bin)
                if density[bin_index] > density[bin_index - 1]
                and density[bin_index] >= density[bin_index + 1]
            ]
            peak_sets.append(peaks)

        self.assertIn(156.0, peak_sets[0])
        self.assertIn(174.0, peak_sets[0])
        self.assertEqual(peak_sets[1], [160.0])

    def test_overlap_changes_time_sampling_not_frequency_response_and_captures_burst(self):
        self.assertEqual(
            [len(range(0, 4096 - 128 + 1, hop)) for hop in (128, 64, 32)],
            [32, 63, 125],
        )
        self.assertEqual([1000 * hop / 1024 for hop in (128, 64, 32)], [125.0, 62.5, 31.25])

        sample_count = 4096
        burst_start = 1536
        burst_count = 64
        samples = [0.0] * sample_count
        for local_index in range(burst_count):
            gate = 0.5 - 0.5 * math.cos(2 * math.pi * local_index / (burst_count - 1))
            index = burst_start + local_index
            samples[index] = 0.8 * gate * math.cos(2 * math.pi * 380 * index / 1024 + 0.7)
        window = hann_symmetric(128)
        burst_bin = round(380 * 128 / 1024)
        peaks: list[float] = []
        errors_ms: list[float] = []
        true_center = (burst_start + (burst_count - 1) / 2) / 1024
        for hop in (128, 64, 32):
            levels: list[float] = []
            centers: list[float] = []
            for start in range(0, sample_count - 128 + 1, hop):
                density, _ = one_sided_psd(samples[start : start + 128], 1024.0, window)
                levels.append(density[burst_bin])
                centers.append((start + 63.5) / 1024)
            peak = max(levels)
            peak_index = levels.index(peak)
            peaks.append(peak)
            errors_ms.append(1000 * abs(centers[peak_index] - true_center))
        self.assertGreater(10 * math.log10(peaks[-1] / peaks[0]), 5.0)
        self.assertEqual(errors_ms, [31.25, 31.25, 0.0])
        overlap_section = self.experiment.split("%% Sweep 2", 1)[1].split("%% Broken case", 1)[0]
        for marker in (
            "overlap_fraction_sweep = [0 0.50 0.75];",
            "baseline_window_length - sweep_overlap_samples;",
            "overlap_bin_spacing_hz = baseline_bin_spacing_hz*",
            "overlap_hann_main_lobe_width_hz = baseline_hann_main_lobe_width_hz*",
            "results.overlap_burst_capture_gain_db",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotIn("baseline_window_length =", overlap_section)

    def test_broken_zero_padding_changes_grid_not_true_window_width(self):
        samples = [
            math.cos(2 * math.pi * 10 * index / 64)
            + 0.8 * math.cos(2 * math.pi * 11.125 * index / 64)
            for index in range(64)
        ]
        window = hann_symmetric(64)
        short_density, short_spacing = one_sided_psd(samples, 1024.0, window, 512)
        self.assertEqual(len(short_density), 257)
        self.assertEqual(short_spacing, 2.0)
        self.assertEqual(4 * 1024 / 64, 64.0)
        self.assertEqual(4 * 1024 / 512, 8.0)
        self.assertIn("broken_window_length = 64;", self.experiment)
        self.assertIn("broken_fft_length = 512;", self.experiment)
        broken = self.experiment.split("%% Broken case", 1)[1]
        for marker in (
            "fft(windowed_frame_v, broken_fft_length)",
            "broken_display_bin_spacing_hz = fs_hz/broken_fft_length;",
            "broken_true_main_lobe_width_hz = 4*fs_hz/broken_window_length;",
            "recovered_true_main_lobe_width_hz = 4*fs_hz/recovered_window_length;",
            "Zero-padding must not be mistaken for a longer physical observation.",
            "results.broken_true_main_lobe_width_hz",
        ):
            self.assertIn(marker, broken)

    def test_sweep_sections_change_one_control_and_report_labeled_metrics(self):
        window_section = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        overlap_section = self.experiment.split("%% Sweep 2", 1)[1].split("%% Broken case", 1)[0]
        for section, forbidden in (
            (
                window_section,
                ("fs_hz =", "record_sample_count =", "matched_overlap_fraction =", "burst_frequency_hz ="),
            ),
            (
                overlap_section,
                ("fs_hz =", "record_sample_count =", "baseline_window_length =", "burst_frequency_hz ="),
            ),
        ):
            for assignment in forbidden:
                self.assertNotIn(assignment, section)
        for marker in (
            "Window-center time (s)",
            "Frequency (Hz)",
            "Amplitude (V)",
            "PSD (dB re 1 V^2/Hz)",
            "results.baseline_chirp_ridge_mae_hz",
            "results.baseline_burst_peak_time_error_ms",
            "results.window_frame_count",
            "results.overlap_frame_count",
        ):
            self.assertIn(marker, self.experiment)
        self.assertGreaterEqual(
            self.experiment.count("caxis([display_floor_db display_ceiling_db]);"),
            3,
        )
        self.assertGreaterEqual(
            self.experiment.count("color_scale.Label.String = 'PSD (dB re 1 V^2/Hz)';"),
            3,
        )

    def test_recovery_isolation_timeout_compatibility_and_rollback_are_documented(self):
        lowered = self.experiment.lower()
        for forbidden in (
            "close all",
            "clear all",
            "clearvars",
            "pause(",
            "input(",
            "waitfor(",
            "uiwait(",
            "while ",
            "parfor",
            "timer(",
            "webread(",
            "fopen(",
            "save(",
            "writematrix(",
            "audioplayer(",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertIn("'Tag', 'P15'", self.experiment)
        self.assertLess(
            self.experiment.index("delete(previous_p15_figures);"),
            self.experiment.index("%% Validate controls"),
        )
        self.assertLess(
            self.experiment.index("clear results;"),
            self.experiment.index("%% Validate controls"),
        )
        combined = "\n".join((self.readme, self.lesson, self.walkthrough, self.checks)).lower()
        for phrase in (
            "ctrl+c",
            "private seed",
            "writes no files",
            "global random stream",
            "manifest status to `scaffolded`",
            "base matlab",
        ):
            self.assertIn(phrase, combined)

    def test_concept_first_docs_evidence_and_no_placeholders_or_overclaim(self):
        combined = "\n".join(
            (self.readme, self.experiment, self.lesson, self.walkthrough, self.checks)
        )
        self.assertNotRegex(combined, r"(?i)\b(TODO|TBD|lorem ipsum)\b")
        self.assertNotIn("matlab runtime passed", combined.lower())
        self.assertNotIn("field validated", combined.lower())
        for text, headings in (
            (self.lesson, ("## Physical mental model", "## Limiting cases", "## Radar connection")),
            (self.walkthrough, ("## Baseline", "## Sweep 1", "## Sweep 2", "## Broken case", "## Safe rerun")),
            (self.checks, ("## Baseline observation checks", "## Interpretation checks", "## Teach-back completion")),
        ):
            for heading in headings:
                self.assertIn(heading, text)
        evidence_files = sorted((ROOT / "docs/evidence").glob("P15-*.md"))
        self.assertTrue(evidence_files, "P15 requires retained evidence")
        evidence = evidence_files[-1].read_text(encoding="utf-8").lower()
        for marker in (
            "acceptance",
            "dsp_radar_verify_profile",
            "does **not** claim matlab",
            "rollback",
            "residual",
        ):
            self.assertIn(marker, evidence)


if __name__ == "__main__":
    unittest.main()
