from __future__ import annotations

import cmath
import copy
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "82-build-a-passive-radar-cross-ambiguity-experiment"
MANIFEST = ROOT / "curriculum" / "modules.json"
CLI = ROOT / "bin" / "learn"
EVIDENCE = ROOT / "docs" / "evidence" / "P82-2026-08-14.md"
QUESTION = "How can a known broadcast-like reference reveal delayed Doppler-shifted echoes without transmitting?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")

BASE_CONTROLS = {
    "seed": 8201,
    "fs_hz": 200_000.0,
    "sample_count": 4096,
    "samples_per_symbol": 4,
    "c_mps": 3.0e8,
    "delay_grid": list(range(65)),
    "doppler_grid_hz": list(range(-1000, 1001, 50)),
    "target_delay": 24,
    "target_doppler_hz": 500.0,
    "direct_voltage": 2.50,
    "multipath_voltage": 0.10,
    "multipath_delay": 11,
    "target_voltage": 0.18,
    "surveillance_noise_voltage": 0.08,
    "baseline_reference_quality_db": 35.0,
    "delay_sweep": [12, 24, 48],
    "doppler_sweep_hz": [-500.0, 0.0, 500.0],
    "integration_sweep": [1024, 2048, 4096],
    "quality_sweep_db": [35.0, 15.0, 5.0],
    "under_cancel_fraction": 0.20,
    "display_floor_db": -35.0,
    "max_samples": 8192,
    "max_delay_cells": 129,
    "max_doppler_cells": 81,
    "max_sweep_cases": 4,
    "max_map_evaluations": 16,
    "max_multiply_accumulates": 175_000_000,
    "max_peak_ambiguity_values": 1_000_000,
    "max_working_values": 8_000_000,
    "max_private_values": 20_000,
    "expected_figures": 5,
}


def artifact_errors(folder: Path) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = folder / name
        if not path.is_file():
            errors.append(f"missing {name}")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            errors.append(f"empty {name}")
        if re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", text, re.IGNORECASE):
            errors.append(f"placeholder remains in {name}")
    return errors


def controls_errors(c: dict) -> list[str]:
    errors: list[str] = []
    scalar_names = (
        "seed", "fs_hz", "sample_count", "samples_per_symbol", "c_mps",
        "target_delay", "target_doppler_hz", "direct_voltage",
        "multipath_voltage", "multipath_delay", "target_voltage",
        "surveillance_noise_voltage", "baseline_reference_quality_db",
        "under_cancel_fraction", "display_floor_db", "max_samples",
        "max_delay_cells", "max_doppler_cells", "max_sweep_cases",
        "max_map_evaluations", "max_multiply_accumulates",
        "max_peak_ambiguity_values", "max_working_values", "max_private_values",
        "expected_figures",
    )
    vector_names = (
        "delay_grid", "doppler_grid_hz", "delay_sweep", "doppler_sweep_hz",
        "integration_sweep", "quality_sweep_db",
    )
    integer_names = {
        "seed", "sample_count", "samples_per_symbol", "target_delay",
        "multipath_delay", "max_samples", "max_delay_cells",
        "max_doppler_cells", "max_sweep_cases", "max_map_evaluations",
        "max_multiply_accumulates", "max_peak_ambiguity_values",
        "max_working_values", "max_private_values", "expected_figures",
    }
    for name in scalar_names:
        value = c.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            errors.append(f"{name} must be a finite real scalar")
            continue
        if name in integer_names and value != math.floor(value):
            errors.append(f"{name} must be integer valued")
    for name in vector_names:
        value = c.get(name)
        if (
            not isinstance(value, list)
            or not value
            or any(
                isinstance(item, bool)
                or not isinstance(item, (int, float))
                or not math.isfinite(item)
                for item in value
            )
        ):
            errors.append(f"{name} must be a finite numeric row")
    if errors:
        return errors
    if not 0 < c["seed"] < 2_147_483_647:
        errors.append("seed range")
    if (
        c["fs_hz"] <= 0
        or c["c_mps"] <= 0
        or c["sample_count"] < 256
        or c["samples_per_symbol"] < 2
        or c["sample_count"] % c["samples_per_symbol"]
    ):
        errors.append("sampling controls")
    if not (
        c["direct_voltage"] > c["target_voltage"] > 0
        and c["multipath_voltage"] > 0
        and c["surveillance_noise_voltage"] > 0
    ):
        errors.append("amplitudes")
    if (
        c["target_delay"] <= 0
        or c["multipath_delay"] <= 0
        or c["target_delay"] == c["multipath_delay"]
    ):
        errors.append("distinct paths")
    if c["delay_grid"] != list(range(len(c["delay_grid"]))):
        errors.append("delay grid")
    if any(right <= left for left, right in zip(c["doppler_grid_hz"], c["doppler_grid_hz"][1:])) or 0 not in c["doppler_grid_hz"]:
        errors.append("Doppler grid")
    if not set([c["target_delay"], c["multipath_delay"], *c["delay_sweep"]]).issubset(c["delay_grid"]):
        errors.append("delay support")
    if not set([c["target_doppler_hz"], *c["doppler_sweep_hz"]]).issubset(c["doppler_grid_hz"]):
        errors.append("Doppler support")
    if any(right <= left for left, right in zip(c["delay_sweep"], c["delay_sweep"][1:])):
        errors.append("delay sweep order")
    if any(right <= left for left, right in zip(c["doppler_sweep_hz"], c["doppler_sweep_hz"][1:])):
        errors.append("Doppler sweep order")
    if any(right <= left for left, right in zip(c["integration_sweep"], c["integration_sweep"][1:])):
        errors.append("integration sweep order")
    if any(right >= left for left, right in zip(c["quality_sweep_db"], c["quality_sweep_db"][1:])):
        errors.append("quality sweep order")
    if (
        any(value != math.floor(value) for value in c["integration_sweep"])
        or c["integration_sweep"][0] <= max(c["delay_grid"])
        or c["integration_sweep"][-1] != c["sample_count"]
    ):
        errors.append("integration support")
    if (
        c["baseline_reference_quality_db"] <= 0
        or any(value <= 0 for value in c["quality_sweep_db"])
        or not 0 < c["under_cancel_fraction"] < 1
        or c["display_floor_db"] >= 0
    ):
        errors.append("quality/display controls")
    if (
        c["sample_count"] > c["max_samples"]
        or len(c["delay_grid"]) > c["max_delay_cells"]
        or len(c["doppler_grid_hz"]) > c["max_doppler_cells"]
        or max(len(c[name]) for name in ("delay_sweep", "doppler_sweep_hz", "integration_sweep", "quality_sweep_db")) > c["max_sweep_cases"]
        or 2 * c["sample_count"] > c["max_private_values"]
        or min(
            c[name]
            for name in (
                "max_samples", "max_delay_cells", "max_doppler_cells",
                "max_sweep_cases", "max_map_evaluations",
                "max_multiply_accumulates", "max_peak_ambiguity_values",
                "max_working_values", "max_private_values", "expected_figures",
            )
        ) < 1
    ):
        errors.append("resource shape")
    if max(abs(value) for value in c["doppler_grid_hz"]) >= c["fs_hz"] / 2:
        errors.append("Doppler Nyquist")
    map_count = 2 + len(c["delay_sweep"]) + len(c["doppler_sweep_hz"]) + len(c["integration_sweep"]) + len(c["quality_sweep_db"]) + 2
    map_samples = (
        (2 + len(c["delay_sweep"]) + len(c["doppler_sweep_hz"]) + len(c["quality_sweep_db"]) + 2) * c["sample_count"]
        + sum(c["integration_sweep"])
    )
    work = map_samples * len(c["delay_grid"]) * len(c["doppler_grid_hz"])
    sample_count = c["sample_count"]
    delay_count = len(c["delay_grid"])
    doppler_count = len(c["doppler_grid_hz"])
    peak_values = (
        5 * sample_count
        + 2 * delay_count * sample_count
        + 2 * doppler_count * sample_count
        + 4 * doppler_count * delay_count
        + 2 * delay_count
    )
    if (
        map_count > c["max_map_evaluations"]
        or work > c["max_multiply_accumulates"]
        or peak_values > c["max_peak_ambiguity_values"]
    ):
        errors.append("resource work")
    return errors


def private_uniform(seed: int, count: int, maximum: int = 20_000) -> list[float]:
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 < seed < 2_147_483_647:
        raise ValueError("invalid seed")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= maximum:
        raise ValueError("invalid count")
    state = seed
    values: list[float] = []
    for _ in range(count):
        state = (16_807 * state) % 2_147_483_647
        values.append(state / 2_147_483_647)
    return values


def private_qpsk(seed: int, count: int) -> list[complex]:
    values = private_uniform(seed, 2 * count)
    samples = [
        complex(1 if values[2 * index] >= 0.5 else -1, 1 if values[2 * index + 1] >= 0.5 else -1) / math.sqrt(2)
        for index in range(count)
    ]
    average = sum(samples) / count
    samples = [value - average for value in samples]
    rms = math.sqrt(sum(abs(value) ** 2 for value in samples) / count)
    return [value / rms for value in samples]


def broadcast_reference(seed: int = 8201, count: int = 4096, sps: int = 4) -> list[complex]:
    symbols = private_qpsk(seed, count // sps)
    impulses = [0j] * count
    for index, value in enumerate(symbols):
        impulses[index * sps] = value
    taps: list[float] = []
    for tap in range(-12, 13):
        argument = tap / sps
        sinc_value = 1.0 if tap == 0 else math.sin(math.pi * argument) / (math.pi * argument)
        taps.append(sinc_value * (0.5 + 0.5 * math.cos(math.pi * tap / 12)))
    tap_norm = math.sqrt(sum(value * value for value in taps))
    taps = [value / tap_norm for value in taps]
    filtered = [
        sum(
            impulses[source] * taps[output - source + 12]
            for source in range(max(0, output - 12), min(count, output + 13))
        )
        for output in range(count)
    ]
    rms = math.sqrt(sum(abs(value) ** 2 for value in filtered) / count)
    return [value / rms for value in filtered]


def delayed(signal: list[complex], delay: int) -> list[complex]:
    if isinstance(delay, bool) or not isinstance(delay, int) or not 0 <= delay < len(signal):
        raise ValueError("invalid delay")
    return signal.copy() if delay == 0 else [0j] * delay + signal[:-delay]


def normalized(signal: list[complex]) -> list[complex]:
    rms = math.sqrt(sum(abs(value) ** 2 for value in signal) / len(signal))
    if rms == 0:
        raise ValueError("zero energy")
    return [value / rms for value in signal]


def cancel_direct(reference: list[complex], surveillance: list[complex]) -> tuple[list[complex], complex]:
    if not reference or len(reference) != len(surveillance):
        raise ValueError("channel shape")
    energy = sum(abs(value) ** 2 for value in reference)
    if energy == 0:
        raise ValueError("reference energy")
    coefficient = sum(value.conjugate() * sample for value, sample in zip(reference, surveillance)) / energy
    return [sample - coefficient * value for value, sample in zip(reference, surveillance)], coefficient


def coherence(reference: list[complex], surveillance: list[complex], delay: int, doppler_hz: float, fs_hz: float) -> float:
    lagged = delayed(reference, delay)
    coherent_sum = sum(
        sample * ref.conjugate() * cmath.exp(-2j * math.pi * doppler_hz * index / fs_hz)
        for index, (sample, ref) in enumerate(zip(surveillance, lagged))
    )
    denominator = math.sqrt(
        sum(abs(value) ** 2 for value in surveillance)
        * sum(abs(value) ** 2 for value in lagged)
    )
    return abs(coherent_sum) / denominator


def ambiguity_metrics(
    reference: list[complex],
    surveillance: list[complex],
    delay_grid: list[int],
    doppler_grid_hz: list[float],
    target_delay: int,
    target_doppler_hz: float,
    fs_hz: float,
) -> tuple[int, float, float, float]:
    cells = [
        (coherence(reference, surveillance, delay, doppler, fs_hz), delay, doppler)
        for delay in delay_grid
        for doppler in doppler_grid_hz
    ]
    _, peak_delay, peak_doppler = max(cells)
    target_value = coherence(
        reference, surveillance, target_delay, target_doppler_hz, fs_hz
    )
    background = [
        value
        for value, delay, doppler in cells
        if not (
            abs(delay - target_delay) <= 2
            and abs(doppler - target_doppler_hz) <= 100
        )
    ]
    contrast_db = 20 * math.log10(target_value / statistics.median(background))
    return peak_delay, peak_doppler, target_value, contrast_db


class P82ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.documents = {
            name: (MODULE / name).read_text(encoding="utf-8")
            for name in ARTIFACTS
            if name != "experiment.m"
        }

    def test_manifest_identity_artifacts_and_permanent_dependency(self) -> None:
        module = self.manifest["modules"][81]
        prerequisite = self.manifest["modules"][80]
        successor = self.manifest["modules"][82]
        self.assertEqual(
            {key: module[key] for key in ("number", "id", "title", "guiding_question", "phase", "folder", "status", "implementation_batch")},
            {
                "number": 82,
                "id": "P82",
                "title": "Build a Passive Radar Cross-Ambiguity Experiment",
                "guiding_question": QUESTION,
                "phase": 9,
                "folder": "modules/82-build-a-passive-radar-cross-ambiguity-experiment",
                "status": "implemented",
                "implementation_batch": "P82",
            },
        )
        self.assertEqual((prerequisite["id"], prerequisite["status"]), ("P81", "implemented"))
        self.assertEqual((successor["id"], successor["implementation_batch"]), ("P83", "P83"))
        self.assertEqual(artifact_errors(MODULE), [])
        for name in ARTIFACTS:
            self.assertIn(QUESTION, (MODULE / name).read_text(encoding="utf-8"))

    def test_artifact_validation_rejects_missing_empty_and_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            self.assertEqual(artifact_errors(fixture), [])
            (fixture / "lesson.md").unlink()
            self.assertIn("missing lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("", encoding="utf-8")
            self.assertIn("empty lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("TODO\n", encoding="utf-8")
            self.assertIn("placeholder remains in lesson.md", artifact_errors(fixture))

    def test_source_binds_model_sweeps_failure_recovery_and_common_scale(self) -> None:
        markers = (
            "baseline_seed = 8201", "make_broadcast_reference", "make_surveillance",
            "cancel_direct_path", "cross_ambiguity", "surveillance.*conj(lagged_reference)",
            "exp(-1j*2*pi*(doppler_grid_hz(:)*time_s))", "target_delay_sweep_samples = [12 24 48]",
            "target_doppler_sweep_hz = [-500 0 500]", "integration_sweep_samples = [1024 2048 4096]",
            "reference_quality_sweep_db = [35 15 5]", "under_cancellation_fraction = 0.20",
            "measurement_before_failure", "recovery_exact_match", "common_baseline_peak",
            "coefficient = sum(conj(reference).*surveillance)/reference_energy",
            "cancelled = surveillance-coefficient*reference",
            "delayed = [zeros(1, delay_samples) signal(1:end-delay_samples)]",
            "normalization = sqrt(sum(abs(surveillance).^2)*reference_energy)",
            "ambiguity = abs(coherent_sum)./normalization",
            "matched_voltage = abs(coherent_sum)./reference_energy",
            "maximum_multiply_accumulates = 175000000",
            "maximum_peak_ambiguity_value_equivalents = 1000000",
            "scale_bar.Label.String = 'Matched voltage / common peak (dB)'",
            "P82:DelaySupport",
            "P82:DopplerNyquist", "P82:BrokenRecovery",
        )
        for marker in markers:
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P82"), 5)
        self.assertNotIn("rng(", self.source.lower())

    def test_source_has_no_opaque_toolbox_or_external_side_effect(self) -> None:
        source_without_comments = "\n".join(
            line for line in self.source.lower().splitlines() if not line.lstrip().startswith("%")
        )
        for token in (
            "ambgfun", "xcorr(", "phased.", "awgn(", "circshift(", "rand(",
            "randn(", "parfor", "gpuarray", "batch(", "timer(", "fopen(",
            "writematrix", "save(", "webread", "system(", "unix(",
        ):
            self.assertNotIn(token, source_without_comments)

    def test_control_contract_accepts_baseline_and_rejects_malformed_resources(self) -> None:
        self.assertEqual(controls_errors(copy.deepcopy(BASE_CONTROLS)), [])
        map_samples = 60_416
        self.assertEqual(map_samples * 65 * 41, 161_008_640)
        peak_values = (
            5 * 4096 + 2 * 65 * 4096 + 2 * 41 * 4096
            + 4 * 41 * 65 + 2 * 65
        )
        self.assertEqual(peak_values, 899_622)
        malformed_cases = (
            ("seed", True), ("seed", 0), ("sample_count", 4095),
            ("samples_per_symbol", 1), ("fs_hz", float("nan")),
            ("c_mps", 0), ("target_delay", 11), ("target_voltage", -1),
            ("surveillance_noise_voltage", 0), ("delay_grid", [0, 2, 3]),
            ("delay_sweep", [12, [24], 48]), ("delay_sweep", [12, 12, 48]),
            ("doppler_sweep_hz", [-500, float("inf"), 500]),
            ("integration_sweep", [64, 2048, 4096]),
            ("integration_sweep", [1024, 2048, 4000]),
            ("quality_sweep_db", [5, 15, 35]), ("quality_sweep_db", [35, 15, 0]),
            ("under_cancel_fraction", 1), ("display_floor_db", 0),
            ("max_samples", 100), ("max_delay_cells", 10),
            ("max_doppler_cells", 10), ("max_sweep_cases", 2),
            ("max_map_evaluations", 15), ("max_multiply_accumulates", 100),
            ("max_peak_ambiguity_values", 899_621),
            ("max_working_values", 0), ("max_private_values", 100),
        )
        for key, value in malformed_cases:
            with self.subTest(key=key, value=value):
                malformed = copy.deepcopy(BASE_CONTROLS)
                malformed[key] = value
                self.assertTrue(controls_errors(malformed))
        unsupported_delay = copy.deepcopy(BASE_CONTROLS)
        unsupported_delay["target_delay"] = 70
        self.assertIn("delay support", controls_errors(unsupported_delay))
        aliased = copy.deepcopy(BASE_CONTROLS)
        aliased["doppler_grid_hz"][-1] = 100_000
        self.assertIn("Doppler Nyquist", controls_errors(aliased))

    def test_private_generator_is_repeatable_bounded_and_isolated(self) -> None:
        first = private_uniform(8201, 8)
        self.assertEqual(first, private_uniform(8201, 8))
        self.assertAlmostEqual(first[0], 0.06418405429654943, places=15)
        self.assertTrue(all(0 < value < 1 for value in first))
        self.assertEqual(private_qpsk(8202, 16), private_qpsk(8202, 16))
        for seed, count in ((True, 2), (0, 2), (8201, True), (8201, 0), (8201, 20_001)):
            with self.subTest(seed=seed, count=count), self.assertRaises(ValueError):
                private_uniform(seed, count)

    def test_independent_baseline_oracle_exposes_and_cancels_direct_path(self) -> None:
        reference = broadcast_reference()
        reference_noise = private_qpsk(8202, 4096)
        surveillance_noise = private_qpsk(8203, 4096)
        measured = normalized([
            clean + 10 ** (-35 / 20) * noise
            for clean, noise in zip(reference, reference_noise)
        ])
        time = [index / 200_000 for index in range(4096)]
        multipath = delayed(reference, 11)
        target = delayed(reference, 24)
        surveillance = [
            2.5 * clean
            + 0.10 * static
            + 0.18 * echo * cmath.exp(2j * math.pi * 500 * instant)
            + 0.08 * noise
            for clean, static, echo, instant, noise in zip(reference, multipath, target, time, surveillance_noise)
        ]
        retained = surveillance.copy()
        cancelled, coefficient = cancel_direct(measured, surveillance)
        under_cancelled = [
            sample - 0.20 * coefficient * ref
            for sample, ref in zip(surveillance, measured)
        ]
        recovered, recovered_coefficient = cancel_direct(measured, retained)

        self.assertGreater(coherence(measured, surveillance, 0, 0, 200_000), 0.99)
        self.assertLess(coherence(measured, surveillance, 24, 500, 200_000), 0.08)
        self.assertLess(coherence(measured, cancelled, 0, 0, 200_000), 1e-12)
        self.assertGreater(coherence(measured, cancelled, 24, 500, 200_000), 0.80)
        self.assertGreater(coherence(measured, cancelled, 24, 500, 200_000), coherence(measured, cancelled, 11, 0, 200_000) + 0.30)
        self.assertGreater(coherence(measured, under_cancelled, 0, 0, 200_000), 0.99)
        self.assertGreater(coherence(measured, cancelled, 24, 500, 200_000), 50 * coherence(measured, cancelled, 24, -500, 200_000))
        self.assertEqual(surveillance, retained)
        self.assertEqual(recovered, cancelled)
        self.assertEqual(recovered_coefficient, coefficient)
        self.assertAlmostEqual(coefficient.real, 2.5005683342999334, places=10)
        self.assertAlmostEqual(coefficient.imag, -0.003703096228234097, places=10)

    def test_reduced_asymmetric_map_preserves_positive_delay_and_doppler(self) -> None:
        count = 256
        fs_hz = 25_600.0
        reference = private_qpsk(8290, count)
        target_delay = 7
        target_doppler = 2 * fs_hz / count
        target = delayed(reference, target_delay)
        surveillance = [
            3.0 * direct + 0.4 * echo * cmath.exp(2j * math.pi * target_doppler * index / fs_hz)
            for index, (direct, echo) in enumerate(zip(reference, target))
        ]
        cancelled, _ = cancel_direct(reference, surveillance)
        delay_grid = list(range(17))
        doppler_grid = [bin_index * fs_hz / count for bin_index in range(-4, 5)]
        peak = max(
            (
                coherence(reference, cancelled, delay, doppler, fs_hz),
                delay,
                doppler,
            )
            for delay in delay_grid
            for doppler in doppler_grid
        )
        self.assertEqual((peak[1], peak[2]), (target_delay, target_doppler))
        self.assertGreater(peak[0], 0.99)

    def test_reduced_broken_case_fails_globally_and_recovery_restores_target(self) -> None:
        count = 256
        fs_hz = 25_600.0
        reference = private_qpsk(8294, count)
        target_delay = 7
        target_doppler = 200.0
        target = delayed(reference, target_delay)
        surveillance = [
            3.0 * direct
            + 0.4 * echo * cmath.exp(
                2j * math.pi * target_doppler * index / fs_hz
            )
            for index, (direct, echo) in enumerate(zip(reference, target))
        ]
        retained = surveillance.copy()
        cancelled, coefficient = cancel_direct(reference, surveillance)
        under_cancelled = [
            sample - 0.20 * coefficient * ref
            for sample, ref in zip(surveillance, reference)
        ]
        recovered, recovered_coefficient = cancel_direct(reference, retained)
        delay_grid = list(range(17))
        doppler_grid = [float(value) for value in range(-400, 401, 100)]

        def peak(signal: list[complex]) -> tuple[int, float]:
            return ambiguity_metrics(
                reference,
                signal,
                delay_grid,
                doppler_grid,
                target_delay,
                target_doppler,
                fs_hz,
            )[:2]

        self.assertEqual(peak(surveillance), (0, 0.0))
        self.assertEqual(peak(cancelled), (target_delay, target_doppler))
        self.assertEqual(peak(under_cancelled), (0, 0.0))
        self.assertEqual(peak(recovered), (target_delay, target_doppler))
        self.assertEqual(surveillance, retained)
        self.assertEqual(recovered, cancelled)
        self.assertEqual(recovered_coefficient, coefficient)

    def test_all_four_sweeps_have_one_variable_physical_predictions(self) -> None:
        self.assertEqual(BASE_CONTROLS["delay_sweep"], [12, 24, 48])
        self.assertEqual(BASE_CONTROLS["doppler_sweep_hz"], [-500, 0, 500])
        integration_ms = [1000 * count / BASE_CONTROLS["fs_hz"] for count in BASE_CONTROLS["integration_sweep"]]
        resolutions = [BASE_CONTROLS["fs_hz"] / count for count in BASE_CONTROLS["integration_sweep"]]
        self.assertEqual(integration_ms, [5.12, 10.24, 20.48])
        self.assertEqual(resolutions, [195.3125, 97.65625, 48.828125])
        self.assertTrue(all(right < left for left, right in zip(resolutions, resolutions[1:])))
        self.assertEqual(BASE_CONTROLS["quality_sweep_db"], [35, 15, 5])
        combined = "\n".join(self.documents.values())
        for marker in (
            "Delay moves columns", "peak changes Doppler row", "same deterministic record",
            "surveillance scene remains fixed", "1/T", "target voltage",
        ):
            self.assertIn(marker.lower(), combined.lower())

    def test_reduced_independent_oracle_exercises_all_four_sweep_behaviors(self) -> None:
        sample_count = 512
        fs_hz = 51_200.0
        clean_reference = broadcast_reference(8291, sample_count, 4)
        reference_noise = private_qpsk(8292, sample_count)
        surveillance_noise = private_qpsk(8293, sample_count)
        delay_grid = list(range(32))
        doppler_grid = [float(value) for value in range(-400, 401, 100)]
        measured_reference = normalized([
            clean + 10 ** (-35 / 20) * noise
            for clean, noise in zip(clean_reference, reference_noise)
        ])

        def make_surveillance(
            target_delay: int = 13,
            target_doppler: float = 200.0,
            target_voltage: float = 0.22,
        ) -> list[complex]:
            multipath = delayed(clean_reference, 5)
            target = delayed(clean_reference, target_delay)
            return [
                2.5 * direct
                + 0.10 * static
                + target_voltage * echo * cmath.exp(2j * math.pi * target_doppler * index / fs_hz)
                + 0.18 * noise
                for index, (direct, static, echo, noise) in enumerate(
                    zip(clean_reference, multipath, target, surveillance_noise)
                )
            ]

        for target_delay in (7, 13, 21):
            cancelled, _ = cancel_direct(
                measured_reference, make_surveillance(target_delay=target_delay)
            )
            peak_delay, peak_doppler, _, _ = ambiguity_metrics(
                measured_reference, cancelled, delay_grid, doppler_grid,
                target_delay, 200.0, fs_hz,
            )
            self.assertEqual((peak_delay, peak_doppler), (target_delay, 200.0))

        for target_doppler in (-200.0, 0.0, 200.0):
            cancelled, _ = cancel_direct(
                measured_reference, make_surveillance(target_doppler=target_doppler)
            )
            peak_delay, peak_doppler, _, _ = ambiguity_metrics(
                measured_reference, cancelled, delay_grid, doppler_grid,
                13, target_doppler, fs_hz,
            )
            self.assertEqual((peak_delay, peak_doppler), (13, target_doppler))

        surveillance = make_surveillance()
        integration_contrast_db = []
        for count in (128, 256, 512):
            cancelled, _ = cancel_direct(
                measured_reference[:count], surveillance[:count]
            )
            _, _, _, contrast_db = ambiguity_metrics(
                measured_reference[:count], cancelled, delay_grid,
                doppler_grid, 13, 200.0, fs_hz,
            )
            integration_contrast_db.append(contrast_db)
        self.assertTrue(
            all(
                later > earlier + 3
                for earlier, later in zip(
                    integration_contrast_db, integration_contrast_db[1:]
                )
            )
        )

        quality_metrics = []
        for quality_db in (35, 15, 5):
            case_reference = normalized([
                clean + 10 ** (-quality_db / 20) * noise
                for clean, noise in zip(clean_reference, reference_noise)
            ])
            cancelled, _ = cancel_direct(case_reference, surveillance)
            quality_metrics.append(
                ambiguity_metrics(
                    case_reference, cancelled, delay_grid, doppler_grid,
                    13, 200.0, fs_hz,
                )
            )
        self.assertTrue(
            all(
                later[2] < earlier[2]
                for earlier, later in zip(quality_metrics, quality_metrics[1:])
            )
        )
        self.assertGreater(quality_metrics[0][3], quality_metrics[-1][3] + 8)
        self.assertEqual(quality_metrics[0][:2], (13, 200.0))
        self.assertNotEqual(quality_metrics[-1][:2], (13, 200.0))

        no_target, _ = cancel_direct(
            measured_reference, make_surveillance(target_voltage=0.0)
        )
        self.assertLess(
            coherence(measured_reference, no_target, 13, 200.0, fs_hz),
            0.2,
        )
        target_only = delayed(measured_reference, 13)
        aliased_surveillance = [
            echo * cmath.exp(2j * math.pi * 200.0 * index / fs_hz)
            for index, echo in enumerate(target_only)
        ]
        self.assertAlmostEqual(
            coherence(measured_reference, aliased_surveillance, 13, 200.0, fs_hz),
            coherence(
                measured_reference,
                aliased_surveillance,
                13,
                200.0 + fs_hz,
                fs_hz,
            ),
            places=12,
        )

    def test_limiting_cases_dependencies_and_claim_boundary_are_explicit(self) -> None:
        combined = "\n".join(self.documents.values())
        for marker in (
            "P08", "P18", "P26", "P34", "P42", "P81", "base MATLAB R2016b",
            "bistatic excess path", "c\\tau", "not the monostatic", "zero-Doppler",
            "target voltage zero", "uncorrelated reference", "record-length delay",
            "Doppler aliases", "one-tap", "common scale", "Ctrl+C", "rollback",
            "static validation", "MATLAB runtime", "physical radar/HIL",
        ):
            self.assertIn(marker.lower(), combined.lower())
        self.assertGreaterEqual(self.documents["checks.md"].count("**Answer:**"), 40)
        self.assertIsNone(re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", combined, re.IGNORECASE))

    def _run_fixture_cli(self, manifest: dict, *args: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            (fixture / "bin").mkdir()
            (fixture / "curriculum").mkdir()
            shutil.copy2(CLI, fixture / "bin" / "learn")
            (fixture / "curriculum" / "modules.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            for module in manifest["modules"]:
                readme = fixture / module["folder"] / "README.md"
                readme.parent.mkdir(parents=True)
                readme.write_text(f"# {module['id']}\n", encoding="utf-8")
            state = fixture / ".learning" / "progress.json"
            state.parent.mkdir()
            state.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P82",
                        "completed": [f"P{number:02d}" for number in range(1, 81)],
                        "notes": {},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            return subprocess.run(
                [str(fixture / "bin" / "learn"), *args],
                cwd=fixture,
                text=True,
                capture_output=True,
                timeout=3,
                env=os.environ.copy(),
            )

    def test_cli_timeout_rollback_recovery_isolation_and_future_compatibility(self) -> None:
        repository_state = ROOT / ".learning" / "progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        started = self._run_fixture_cli(copy.deepcopy(self.manifest), "start", "82")
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertIn("P82 — Build a Passive Radar Cross-Ambiguity Experiment", started.stdout)
        rollback = copy.deepcopy(self.manifest)
        rollback["modules"][81]["status"] = "scaffolded"
        refused = self._run_fixture_cli(rollback, "start", "82")
        self.assertEqual(refused.returncode, 3)
        self.assertIn("awaits Portfolio batch P82", refused.stdout)
        fallback = self._run_fixture_cli(rollback, "start")
        self.assertEqual(fallback.returncode, 0, fallback.stderr)
        self.assertIn("P81 — Form an ISAR Image from a Rotating Target", fallback.stdout)
        future = copy.deepcopy(self.manifest)
        future["modules"][82]["status"] = "implemented"
        future["modules"][82]["future_metadata"] = {"compatible": True}
        selected = self._run_fixture_cli(future, "start", "82")
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertIn("P82 — Build a Passive Radar Cross-Ambiguity Experiment", selected.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_actual_matlab_script_is_repeatable_and_bounded_when_available(self) -> None:
        matlab = shutil.which("matlab")
        if matlab is None:
            self.skipTest("MATLAB executable is unavailable; runtime is not claimed")
        command = (
            "rng_before=rng; run('experiment.m'); first_results=p82_results; "
            "rng_after_first=rng; assert(first_results.recovery_exact_match); "
            "assert(first_results.executed_map_count==16); "
            "assert(first_results.executed_multiply_accumulates==161008640); "
            "assert(first_results.predicted_peak_ambiguity_value_equivalents==899622); "
            "assert(first_results.baseline_before.peak_delay==0); "
            "assert(first_results.baseline_after.peak_delay==24); "
            "assert(first_results.baseline_after.peak_doppler_hz==500); "
            "assert(isequaln(rng_before,rng_after_first)); run('experiment.m'); "
            "assert(isequaln(first_results,p82_results)); assert(isequaln(rng_before,rng)); "
            "assert(numel(findall(0,'Type','figure','Tag','P82'))==5); "
            "close(findall(0,'Type','figure','Tag','P82'));"
        )
        wrapped = "try; set(0,'DefaultFigureVisible','off'); " + command + " exit(0); catch ME; disp(getReport(ME)); exit(1); end"
        completed = subprocess.run(
            [matlab, "-nosplash", "-nodesktop", "-nodisplay", "-r", wrapped],
            cwd=MODULE,
            text=True,
            capture_output=True,
            timeout=300,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"MATLAB stdout:\n{completed.stdout}\nMATLAB stderr:\n{completed.stderr}",
        )

    def test_catalogs_evidence_and_exact_eof_policy(self) -> None:
        self.assertIn("Project 82 listens to one seeded broadcast-like illuminator", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn("Project 82 follows P81", (ROOT / "START_HERE.md").read_text(encoding="utf-8"))
        self.assertRegex(
            (ROOT / "modules" / "README.md").read_text(encoding="utf-8"),
            r"\| \[P82\].*\| implemented \|",
        )
        evidence = EVIDENCE.read_text(encoding="utf-8")
        for heading in (
            "## Claim boundary", "## Acceptance map", "## Deterministic simulated-oracle results",
            "## Figure and metric inventory", "## Exact commands and results",
            "## Changed and preserved invariants", "## Residual risks", "## Rollback",
            "## Unperformed validation",
        ):
            self.assertIn(heading, evidence)
        paths = [
            *[MODULE / name for name in ARTIFACTS], ROOT / "curriculum" / "modules.json",
            ROOT / "README.md", ROOT / "START_HERE.md", ROOT / "modules" / "README.md",
            Path(__file__), EVIDENCE,
        ]
        for path in paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
