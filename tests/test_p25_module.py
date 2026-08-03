from __future__ import annotations

import cmath
import copy
import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/25-create-and-equalize-a-multipath-channel"
QUESTION = "How do delayed copies distort symbols even when noise is small?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
EXPECTED_IDENTITY = {
    "number": 25,
    "id": "P25",
    "title": "Create and Equalize a Multipath Channel",
    "guiding_question": QUESTION,
    "phase": 3,
    "phase_title": "Modulation, Channels, and Statistical Estimation",
    "slug": "create-and-equalize-a-multipath-channel",
    "folder": "modules/25-create-and-equalize-a-multipath-channel",
    "status": "implemented",
    "implementation_batch": "P25",
}


def validate_p25_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P25 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P25 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    matches = [
        entry for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P25"
    ]
    if len(matches) != 1:
        return errors + [f"expected one P25 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P25 {key} must be {expected!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def canonical_controls() -> dict:
    return {
        "random_seed": 1025,
        "symbol_count": 480,
        "samples_per_symbol": 8,
        "displayed_symbol_count": 14,
        "baseline_rolloff": 0.25,
        "baseline_span_symbols": 8,
        "baseline_esn0_db": 18.0,
        "baseline_path_delays_symbols": (0, 1, 2),
        "baseline_path_gains": (
            1 + 0j,
            0.45 * cmath.exp(0.45j),
            0.20 * cmath.exp(-0.80j),
        ),
        "equalizer_tap_count": 31,
        "metric_guard_symbols": 40,
        "spectrum_fft_length": 2048,
        "eye_trace_count": 32,
        "echo_gain_sweep": (0.0, 0.25, 0.50, 0.75),
        "regularization_sweep": (0.001, 0.01, 0.03, 0.10),
        "broken_path_delays_symbols": (0, 1),
        "broken_path_gains": (1.0, -0.999),
        "max_symbol_count": 480,
        "max_samples_per_symbol": 8,
        "max_span_symbols": 8,
        "max_path_count": 3,
        "max_path_delay_symbols": 2,
        "max_equalizer_taps": 31,
        "max_sweep_cases": 4,
        "max_figure_groups": 5,
        "max_stored_numeric_values": 750000,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    real_vectors = {
        "baseline_path_delays_symbols": (0, 1, 2),
        "echo_gain_sweep": (0.0, 0.25, 0.50, 0.75),
        "regularization_sweep": (0.001, 0.01, 0.03, 0.10),
        "broken_path_delays_symbols": (0, 1),
        "broken_path_gains": (1.0, -0.999),
    }
    complex_vectors = {
        "baseline_path_gains": canonical_controls()["baseline_path_gains"],
    }
    for name, expected in real_vectors.items():
        value = controls[name]
        if not isinstance(value, (tuple, list)):
            raise ValueError(f"{name} must be a bounded numeric vector")
        if not all(_finite_real(item) for item in value):
            raise ValueError(f"{name} must contain finite real values")
        if tuple(value) != expected:
            raise ValueError(f"{name} must equal its canonical vector")
    for name, expected in complex_vectors.items():
        value = controls[name]
        if not isinstance(value, (tuple, list)) or len(value) != len(expected):
            raise ValueError(f"{name} must have canonical shape")
        if any(
            isinstance(item, bool)
            or not math.isfinite(complex(item).real)
            or not math.isfinite(complex(item).imag)
            for item in value
        ):
            raise ValueError(f"{name} must contain finite numeric values")
        if any(abs(complex(a) - b) > 1e-12 for a, b in zip(value, expected)):
            raise ValueError(f"{name} must equal its canonical vector")

    vectors = set(real_vectors) | set(complex_vectors)
    for name, expected in canonical_controls().items():
        if name in vectors:
            continue
        value = controls[name]
        if not _finite_real(value) or value != expected:
            raise ValueError(f"{name} must equal its finite canonical scalar")

    if controls["displayed_symbol_count"] > controls["symbol_count"]:
        raise ValueError("display count exceeds record")
    if controls["symbol_count"] > controls["max_symbol_count"]:
        raise ValueError("symbol count exceeds resource ceiling")
    if controls["equalizer_tap_count"] > controls["max_equalizer_taps"]:
        raise ValueError("equalizer exceeds resource ceiling")
    if len(controls["baseline_path_gains"]) > controls["max_path_count"]:
        raise ValueError("path count exceeds resource ceiling")
    if max(controls["baseline_path_delays_symbols"]) > controls["max_path_delay_symbols"]:
        raise ValueError("path delay exceeds resource ceiling")
    if len(controls["echo_gain_sweep"]) > controls["max_sweep_cases"]:
        raise ValueError("echo sweep exceeds resource ceiling")
    if len(controls["regularization_sweep"]) > controls["max_sweep_cases"]:
        raise ValueError("regularization sweep exceeds resource ceiling")


def convolve(left: list[complex], right: list[complex]) -> list[complex]:
    output = [0j] * (len(left) + len(right) - 1)
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            output[left_index + right_index] += left_value * right_value
    return output


def causal_zf(channel: list[complex], tap_count: int) -> list[complex]:
    taps = [0j] * tap_count
    taps[0] = 1 / channel[0]
    for output_index in range(1, tap_count):
        postcursor = sum(
            channel[channel_index] * taps[output_index - channel_index]
            for channel_index in range(1, min(output_index, len(channel) - 1) + 1)
        )
        taps[output_index] = -postcursor / channel[0]
    return taps


def solve_dense(matrix: list[list[complex]], rhs: list[complex]) -> list[complex]:
    augmented = [row[:] + [value] for row, value in zip(matrix, rhs)]
    size = len(rhs)
    for pivot_column in range(size):
        pivot_row = max(
            range(pivot_column, size),
            key=lambda row: abs(augmented[row][pivot_column]),
        )
        if abs(augmented[pivot_row][pivot_column]) < 1e-14:
            raise ValueError("singular matrix")
        augmented[pivot_column], augmented[pivot_row] = (
            augmented[pivot_row], augmented[pivot_column]
        )
        pivot = augmented[pivot_column][pivot_column]
        augmented[pivot_column] = [value / pivot for value in augmented[pivot_column]]
        for row in range(size):
            if row == pivot_column:
                continue
            factor = augmented[row][pivot_column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[pivot_column])
            ]
    return [augmented[row][-1] for row in range(size)]


def regularized_equalizer(
    channel: list[complex], tap_count: int, regularization: float
) -> list[complex]:
    output_length = len(channel) + tap_count - 1
    convolution_matrix = [[0j] * tap_count for _ in range(output_length)]
    for column in range(tap_count):
        for channel_index, value in enumerate(channel):
            convolution_matrix[column + channel_index][column] = value
    normal = [[0j] * tap_count for _ in range(tap_count)]
    rhs = [0j] * tap_count
    for row in range(tap_count):
        for column in range(tap_count):
            normal[row][column] = sum(
                convolution_matrix[k][row].conjugate()
                * convolution_matrix[k][column]
                for k in range(output_length)
            )
        normal[row][row] += regularization
        rhs[row] = convolution_matrix[0][row].conjugate()
    return solve_dense(normal, rhs)


def root_raised_cosine(rolloff: float, span_symbols: int, samples_per_symbol: int) -> list[float]:
    half_length = span_symbols * samples_per_symbol // 2
    pulse: list[float] = []
    for sample_offset in range(-half_length, half_length + 1):
        time_symbols = sample_offset / samples_per_symbol
        if abs(time_symbols) < 1e-12:
            value = 1 + rolloff * (4 / math.pi - 1)
        elif abs(abs(time_symbols) - 1 / (4 * rolloff)) < 1e-12:
            value = rolloff / math.sqrt(2) * (
                (1 + 2 / math.pi) * math.sin(math.pi / (4 * rolloff))
                + (1 - 2 / math.pi) * math.cos(math.pi / (4 * rolloff))
            )
        else:
            value = (
                math.sin(math.pi * time_symbols * (1 - rolloff))
                + 4
                * rolloff
                * time_symbols
                * math.cos(math.pi * time_symbols * (1 + rolloff))
            ) / (
                math.pi
                * time_symbols
                * (1 - (4 * rolloff * time_symbols) ** 2)
            )
        pulse.append(value)
    energy = sum(value * value for value in pulse)
    return [value / math.sqrt(energy) for value in pulse]


def deterministic_qpsk(symbol_count: int) -> list[complex]:
    state = 1025
    signs: list[int] = []
    for _ in range(2 * symbol_count):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        signs.append(1 if state & 0x80000000 else -1)
    return [
        complex(signs[2 * index], signs[2 * index + 1]) / math.sqrt(2)
        for index in range(symbol_count)
    ]


def deterministic_noise(sample_count: int, variance: float) -> list[complex]:
    state = 0x25A5A5A5

    def uniform() -> float:
        nonlocal state
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        return (state + 0.5) / 2**32

    unit_noise: list[complex] = []
    for _ in range(sample_count):
        radius = math.sqrt(-2 * math.log(uniform()))
        angle = 2 * math.pi * uniform()
        unit_noise.append(
            complex(radius * math.cos(angle), radius * math.sin(angle))
        )
    mean_power = sum(abs(value) ** 2 for value in unit_noise) / sample_count
    scale = math.sqrt(variance / mean_power)
    return [scale * value for value in unit_noise]


def matched_channel_samples(
    symbols: list[complex],
    pulse: list[float],
    samples_per_symbol: int,
    channel: list[complex],
    noise_variance: float,
) -> list[complex]:
    upsampled = [0j] * (len(symbols) * samples_per_symbol)
    upsampled[::samples_per_symbol] = symbols
    transmitted = convolve(upsampled, pulse)
    channel_impulse = [0j] * (1 + (len(channel) - 1) * samples_per_symbol)
    channel_impulse[::samples_per_symbol] = channel
    channel_output = convolve(transmitted, channel_impulse)
    noise = deterministic_noise(len(channel_output), noise_variance)
    received = [signal + disturbance for signal, disturbance in zip(channel_output, noise)]
    matched = convolve(received, list(reversed(pulse)))
    first_sample = len(pulse) - 1
    return [
        matched[first_sample + index * samples_per_symbol]
        for index in range(len(symbols) + len(channel) - 1)
    ]


def evm_percent(actual: list[complex], reference: list[complex], guard: int) -> float:
    errors = (
        abs(actual[index] - reference[index]) ** 2
        for index in range(guard, len(reference) - guard)
    )
    return 100 * math.sqrt(sum(errors) / (len(reference) - 2 * guard))


class P25ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text())
        cls.text = {
            name: (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        }
        cls.experiment = cls.text["experiment.m"]

    def test_complete_artifacts_and_exact_manifest_identity(self):
        self.assertEqual(validate_p25_contract(MODULE, self.manifest), [])
        for text in self.text.values():
            self.assertIn(QUESTION, text)
        p24 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P24")
        self.assertEqual(p24["status"], "implemented")

    def test_contract_validator_rejects_missing_empty_duplicate_and_wrong_identity(self):
        with self.subTest("non-list manifest"):
            self.assertIn("manifest modules must be a list", validate_p25_contract(MODULE, {}))
        with self.subTest("duplicate"):
            duplicate = copy.deepcopy(self.manifest)
            duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
            self.assertTrue(any("found 2" in error for error in validate_p25_contract(MODULE, duplicate)))
        for key, expected in EXPECTED_IDENTITY.items():
            with self.subTest(key=key):
                wrong = copy.deepcopy(self.manifest)
                entry = next(item for item in wrong["modules"] if item["id"] == "P25")
                entry[key] = "wrong" if not isinstance(expected, int) else expected + 1
                self.assertTrue(validate_p25_contract(MODULE, wrong))

    def test_contract_validator_rejects_missing_and_empty_artifacts(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temporary:
            module_dir = Path(temporary)
            for name in ARTIFACTS:
                (module_dir / name).write_text("content", encoding="utf-8")
            (module_dir / "lesson.md").unlink()
            (module_dir / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p25_contract(module_dir, self.manifest)
            self.assertIn("P25 missing lesson.md", errors)
            self.assertIn("P25 empty checks.md", errors)

    def test_controls_are_finite_canonical_and_resource_bounded(self):
        validate_controls()
        malformed = (
            {"random_seed": True},
            {"symbol_count": float("nan")},
            {"samples_per_symbol": 8 + 1j},
            {"displayed_symbol_count": 15},
            {"baseline_path_delays_symbols": [0, 2, 1]},
            {"baseline_path_delays_symbols": "0 1 2"},
            {"baseline_path_gains": [1, complex(float("inf"), 0), 0.2]},
            {"baseline_path_gains": [1, 0.2]},
            {"echo_gain_sweep": [0, 0.25, 0.5, 0.8]},
            {"regularization_sweep": [0.001, 0.01, 0.03]},
            {"broken_path_gains": [1, -1]},
            {"equalizer_tap_count": 33},
            {"max_symbol_count": 479},
            {"max_stored_numeric_values": float("inf")},
        )
        for override in malformed:
            with self.subTest(override=override):
                with self.assertRaises(ValueError):
                    validate_controls(**override)

    def test_private_seed_and_complex_noise_contract(self):
        self.assertIn("RandStream('mt19937ar', 'Seed', random_seed)", self.experiment)
        self.assertNotIn("rng(", self.experiment)
        self.assertGreaterEqual(self.experiment.count("/sqrt(2)"), 3)
        self.assertIn("noise_variance = 10^(-baseline_esn0_db/10);", self.experiment)
        self.assertIn("noise_sigma = sqrt(noise_variance);", self.experiment)
        self.assertIn("noise_sigma*baseline_noise_unit", self.experiment)

    def test_explicit_pulse_channel_sampling_and_equalizer_operations(self):
        required = (
            "rrc_pulse = rrc_pulse/sqrt(sum(abs(rrc_pulse).^2));",
            "matched_filter = conj(fliplr(rrc_pulse));",
            "baseline_channel_impulse(sample_index)",
            "conv(transmitted_waveform,",
            "baseline_sample_indices = 1 + total_pulse_group_delay_samples",
            "baseline_convolution_matrix(row_indices, column_index)",
            "baseline_zf_equalizer =",
            "noise_variance*eye(equalizer_tap_count)",
            "baseline_convolution_matrix'*equalizer_target",
            "sum(abs(baseline_zf_equalizer).^2)",
        )
        for marker in required:
            self.assertIn(marker, self.experiment)

    def test_independent_baseline_zf_oracle(self):
        channel = [1, 0.45 * cmath.exp(0.45j), 0.20 * cmath.exp(-0.80j)]
        taps = causal_zf(channel, 31)
        combined = convolve(channel, taps)
        self.assertAlmostEqual(combined[0].real, 1.0, places=12)
        self.assertLess(max(abs(value) for value in combined[1:31]), 2e-15)
        self.assertLess(abs(combined[-1]), 2e-6)
        self.assertAlmostEqual(sum(abs(value) ** 2 for value in taps), 1.3703252717, places=9)
        self.assertIn("baseline_zf_evm_pct < baseline_unequalized_evm_pct", self.experiment)

    def test_independent_deep_null_zf_and_mmse_oracle(self):
        channel = [1 + 0j, -0.999 + 0j]
        zf = causal_zf(channel, 31)
        zf_combined = convolve(channel, zf)
        zf_noise_gain = sum(abs(value) ** 2 for value in zf)
        self.assertAlmostEqual(abs(zf_combined[-1]), 0.999**31, places=12)
        self.assertAlmostEqual(zf_noise_gain, 30.0881783717, places=9)
        self.assertAlmostEqual(20 * math.log10(abs(1 - 0.999)), -60.0, places=9)

        recovered = regularized_equalizer(channel, 31, 0.01)
        recovered_combined = convolve(channel, recovered)
        recovered_noise_gain = sum(abs(value) ** 2 for value in recovered)
        recovered_residual = sum(
            abs(value - (1 if index == 0 else 0)) ** 2
            for index, value in enumerate(recovered_combined)
        )
        self.assertAlmostEqual(recovered_noise_gain, 4.4349354185, places=8)
        self.assertAlmostEqual(recovered_residual, 0.0502530899, places=9)
        self.assertLess(recovered_noise_gain, zf_noise_gain)
        self.assertIn("recovered_mmse_evm_pct < broken_zf_evm_pct", self.experiment)

    def test_end_to_end_multipath_and_equalization_behavior(self):
        controls = canonical_controls()
        symbol_count = controls["symbol_count"]
        tap_count = controls["equalizer_tap_count"]
        guard = controls["metric_guard_symbols"]
        noise_variance = 10 ** (-controls["baseline_esn0_db"] / 10)
        symbols = deterministic_qpsk(symbol_count)
        pulse = root_raised_cosine(
            controls["baseline_rolloff"],
            controls["baseline_span_symbols"],
            controls["samples_per_symbol"],
        )

        baseline_channel = list(controls["baseline_path_gains"])
        baseline_samples = matched_channel_samples(
            symbols,
            pulse,
            controls["samples_per_symbol"],
            baseline_channel,
            noise_variance,
        )
        baseline_zf = causal_zf(baseline_channel, tap_count)
        baseline_mmse = regularized_equalizer(
            baseline_channel, tap_count, noise_variance
        )
        unequalized_evm = evm_percent(baseline_samples[:symbol_count], symbols, guard)
        zf_evm = evm_percent(
            convolve(baseline_samples, baseline_zf)[:symbol_count], symbols, guard
        )
        mmse_evm = evm_percent(
            convolve(baseline_samples, baseline_mmse)[:symbol_count], symbols, guard
        )

        broken_channel = [complex(value) for value in controls["broken_path_gains"]]
        broken_samples = matched_channel_samples(
            symbols,
            pulse,
            controls["samples_per_symbol"],
            broken_channel,
            noise_variance,
        )
        broken_zf = causal_zf(broken_channel, tap_count)
        recovered = regularized_equalizer(broken_channel, tap_count, 0.01)
        broken_zf_evm = evm_percent(
            convolve(broken_samples, broken_zf)[:symbol_count], symbols, guard
        )
        recovered_evm = evm_percent(
            convolve(broken_samples, recovered)[:symbol_count], symbols, guard
        )

        self.assertLess(zf_evm, 0.40 * unequalized_evm)
        self.assertLess(mmse_evm, 0.40 * unequalized_evm)
        self.assertGreater(broken_zf_evm, 2.0 * recovered_evm)
        self.assertLess(
            sum(abs(value) ** 2 for value in recovered),
            sum(abs(value) ** 2 for value in broken_zf),
        )
        for marker in (
            "transmitted_waveform = conv(upsampled_symbols, rrc_pulse);",
            "baseline_samples = baseline_matched_waveform(baseline_sample_indices);",
            "baseline_zf_output = conv(baseline_samples,",
            "baseline_mmse_output = conv(baseline_samples,",
            "broken_zf_output = conv(broken_samples, broken_zf_equalizer.');",
            "recovered_mmse_output = conv(broken_samples,",
        ):
            self.assertIn(marker, self.experiment)

    def test_sweeps_are_one_variable_bounded_and_retained(self):
        for marker in (
            "echo_gain_sweep = [0 0.25 0.50 0.75];",
            "sweep_symbol_channel(2) =",
            "regularization_sweep = [0.001 0.01 0.03 0.10];",
            "lambda = regularization_sweep(sweep_index);",
            "results.echo_sweep.gain = echo_gain_sweep;",
            "results.broken.regularization = regularization_sweep;",
        ):
            self.assertIn(marker, self.experiment)
        walkthrough = self.text["walkthrough.md"].lower()
        self.assertIn("change only", walkthrough)
        self.assertIn("keep the broken channel and the same data/noise fixed", walkthrough)

    def test_broken_case_recovery_and_limiting_cases_are_explained(self):
        combined = "\n".join(self.text.values()).lower()
        for phrase in (
            "intentionally broken", "deep null", "noise enhancement",
            "residual isi", "h=[1, -0.999]", "limiting cases",
            "cannot recover", "recovery", "frequency-selective fading",
        ):
            self.assertIn(phrase, combined)

    def test_figures_metrics_units_and_results_inventory(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 5)
        self.assertIn("findall(0, 'Type', 'figure', 'Tag', 'P25')", self.experiment)
        for phrase in (
            "Path delay (symbol periods)",
            "Normalized frequency f/R_s (cycles/symbol)",
            "Time (symbol periods)",
            "Matched-filter I amplitude (normalized)",
            "In-phase (normalized)",
            "EVM (%)",
            "Equalizer noise gain (dB)",
            "results.baseline.path_delays_symbols",
            "results.broken.minimum_response_db",
            "fprintf('Baseline EVM:",
        ):
            self.assertIn(phrase, self.experiment)

    def test_placeholder_black_box_and_external_io_regression(self):
        combined = "\n".join(self.text.values())
        for placeholder in ("TODO", "FIXME", "TBD", "lorem ipsum"):
            self.assertNotIn(placeholder.lower(), combined.lower())
        banned = (
            "rcosdesign(", "awgn(", "comm.", "equalize(", "lineareq(",
            "dfe(", "upfirdn(", "fopen(", "save(", "writetable(",
            "system(", "webread(", "parfor", "timer(", "close all",
        )
        for operation in banned:
            self.assertNotIn(operation.lower(), self.experiment.lower())

    def test_validation_precedes_allocations_solves_fft_cleanup_and_figures(self):
        validation_end = self.experiment.index("results = struct();")
        operations = (
            "RandStream(", "complex(zeros(", "conv(", " \\ ", "fft(",
            "findall(", "figure(",
        )
        for operation in operations:
            with self.subTest(operation=operation):
                self.assertGreater(self.experiment.index(operation), validation_end)
        for marker in (
            "max_symbol_count = 480;", "max_samples_per_symbol = 8;",
            "max_path_count = 3;", "max_path_delay_symbols = 2;",
            "max_equalizer_taps = 31;", "max_sweep_cases = 4;",
            "max_figure_groups = 5;", "max_stored_numeric_values = 750000;",
        ):
            self.assertIn(marker, self.experiment)

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback(self):
        operational = "\n".join((self.text["walkthrough.md"], self.text["checks.md"]))
        for phrase in (
            "Ctrl+C", "full rerun", "private seed", "global random stream",
            "workspace variables", "cannot restore", ".learning/", "worker",
            "timer", "external transaction", "rollback", "P24", "base MATLAB",
        ):
            self.assertIn(phrase.lower(), operational.lower())

    def test_public_catalogs_record_permanent_p25_facts(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 25 passes", root_readme)
        self.assertIn("Project 25 follows P24", start_here)
        self.assertRegex(module_index, r"\| \[P25\].*\| implemented \|")

    def test_learner_cli_starts_p25_in_isolated_state_with_timeout(self):
        repository_state = ROOT / ".learning/progress.json"
        state_before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            isolated_root = Path(temporary)
            (isolated_root / "bin").mkdir()
            (isolated_root / "curriculum").mkdir()
            shutil.copy2(ROOT / "bin/learn", isolated_root / "bin/learn")
            shutil.copy2(
                ROOT / "curriculum/modules.json",
                isolated_root / "curriculum/modules.json",
            )
            process = subprocess.run(
                [sys.executable, str(isolated_root / "bin/learn"), "start", "25"],
                cwd=isolated_root,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("P25 — Create and Equalize a Multipath Channel", process.stdout)
            self.assertIn(QUESTION, process.stdout)
            state = json.loads(
                (isolated_root / ".learning/progress.json").read_text(encoding="utf-8")
            )
            self.assertEqual(state["current"], "P25")
        state_after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(state_after, state_before)

    def test_retained_evidence_has_honest_runtime_boundary(self):
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P25-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence = evidence_paths[0].read_text(encoding="utf-8")
        self.assertIn("MATLAB", evidence)
        self.assertIn("did not run", evidence.lower())
        self.assertIn("unperformed", evidence.lower())


if __name__ == "__main__":
    unittest.main()
