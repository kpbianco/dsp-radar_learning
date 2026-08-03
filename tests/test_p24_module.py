from __future__ import annotations

import cmath
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/24-see-pulse-shaping-and-matched-filtering"
QUESTION = "Why are symbols filtered before transmission and again at reception?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
EXPECTED_IDENTITY = {
    "number": 24,
    "id": "P24",
    "title": "See Pulse Shaping and Matched Filtering",
    "guiding_question": QUESTION,
    "phase": 3,
    "phase_title": "Modulation, Channels, and Statistical Estimation",
    "slug": "see-pulse-shaping-and-matched-filtering",
    "folder": "modules/24-see-pulse-shaping-and-matched-filtering",
    "status": "implemented",
    "implementation_batch": "P24",
}


def validate_p24_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P24 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P24 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    matches = [
        entry for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P24"
    ]
    if len(matches) != 1:
        return errors + [f"expected one P24 manifest entry, found {len(matches)}"]
    entry = matches[0]
    for key, expected in EXPECTED_IDENTITY.items():
        if entry.get(key) != expected:
            errors.append(f"P24 {key} must be {expected!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def canonical_controls() -> dict:
    return {
        "random_seed": 1024,
        "symbol_count": 320,
        "samples_per_symbol": 8,
        "displayed_symbol_count": 12,
        "baseline_rolloff": 0.25,
        "baseline_span_symbols": 8,
        "baseline_esn0_db": 14.0,
        "spectrum_fft_length": 4096,
        "rolloff_sweep": (0.10, 0.25, 0.50, 1.00),
        "span_sweep_symbols": (2, 4, 6, 8),
        "broken_timing_offset_samples": 4,
        "eye_trace_count": 40,
        "max_symbol_count": 320,
        "max_samples_per_symbol": 8,
        "max_span_symbols": 8,
        "max_sweep_cases": 4,
        "max_figure_groups": 5,
        "max_stored_numeric_values": 500000,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    vectors = {
        "rolloff_sweep": (0.10, 0.25, 0.50, 1.00),
        "span_sweep_symbols": (2, 4, 6, 8),
    }
    for name, expected in vectors.items():
        value = controls[name]
        if not isinstance(value, (tuple, list)):
            raise ValueError(f"{name} must be a bounded numeric vector")
        if not all(_finite_real(item) for item in value):
            raise ValueError(f"{name} must contain finite real values")
        if tuple(value) != expected:
            raise ValueError(f"{name} must equal its canonical vector")

    for name, expected in canonical_controls().items():
        if name in vectors:
            continue
        value = controls[name]
        if not _finite_real(value) or value != expected:
            raise ValueError(f"{name} must equal its finite canonical scalar")

    if controls["displayed_symbol_count"] > controls["symbol_count"]:
        raise ValueError("display count exceeds the symbol record")
    if controls["symbol_count"] > controls["max_symbol_count"]:
        raise ValueError("symbol count exceeds its resource ceiling")
    if controls["samples_per_symbol"] > controls["max_samples_per_symbol"]:
        raise ValueError("sample rate exceeds its resource ceiling")
    if controls["baseline_span_symbols"] > controls["max_span_symbols"]:
        raise ValueError("span exceeds its resource ceiling")
    if max(controls["span_sweep_symbols"]) > controls["max_span_symbols"]:
        raise ValueError("span sweep exceeds its resource ceiling")
    if len(controls["rolloff_sweep"]) > controls["max_sweep_cases"]:
        raise ValueError("roll-off sweep exceeds its resource ceiling")
    if len(controls["span_sweep_symbols"]) > controls["max_sweep_cases"]:
        raise ValueError("span sweep exceeds its resource ceiling")


def rrc_pulse(rolloff: float, span_symbols: int, samples_per_symbol: int) -> list[float]:
    taps: list[float] = []
    half_samples = span_symbols * samples_per_symbol // 2
    for sample in range(-half_samples, half_samples + 1):
        x = sample / samples_per_symbol
        if abs(x) < 1e-12:
            value = 1 + rolloff * (4 / math.pi - 1)
        elif abs(abs(x) - 1 / (4 * rolloff)) < 1e-12:
            value = rolloff / math.sqrt(2) * (
                (1 + 2 / math.pi) * math.sin(math.pi / (4 * rolloff))
                + (1 - 2 / math.pi) * math.cos(math.pi / (4 * rolloff))
            )
        else:
            value = (
                math.sin(math.pi * x * (1 - rolloff))
                + 4 * rolloff * x * math.cos(math.pi * x * (1 + rolloff))
            ) / (math.pi * x * (1 - (4 * rolloff * x) ** 2))
        taps.append(value)
    energy = math.sqrt(sum(value * value for value in taps))
    return [value / energy for value in taps]


def convolve(left: list[complex], right: list[complex]) -> list[complex]:
    output = [0j] * (len(left) + len(right) - 1)
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            output[left_index + right_index] += left_value * right_value
    return output


def deterministic_qpsk(symbol_count: int) -> list[complex]:
    symbols = []
    for index in range(symbol_count):
        i_value = 1 if (37 * index + 11) % 101 >= 50 else -1
        q_value = 1 if (53 * index + 7) % 97 >= 48 else -1
        symbols.append(complex(i_value, q_value) / math.sqrt(2))
    return symbols


def shaped_samples(
    symbols: list[complex], pulse: list[float], samples_per_symbol: int,
    *, timing_offset: int = 0,
) -> tuple[list[complex], list[complex], list[complex]]:
    upsampled = [0j] * (len(symbols) * samples_per_symbol)
    upsampled[::samples_per_symbol] = symbols
    transmitted = convolve(upsampled, [complex(value) for value in pulse])
    matched = [complex(value).conjugate() for value in reversed(pulse)]
    output = convolve(transmitted, matched)
    total_delay = len(pulse) - 1
    samples = [
        output[total_delay + timing_offset + index * samples_per_symbol]
        for index in range(len(symbols))
    ]
    return transmitted, output, samples


def evm(reference: list[complex], measured: list[complex], guard: int) -> float:
    selected = range(guard, len(reference) - guard)
    return math.sqrt(
        sum(abs(measured[index] - reference[index]) ** 2 for index in selected)
        / len(list(selected))
    )


def symbol_error_rate(reference: list[complex], measured: list[complex]) -> float:
    errors = sum(
        (sample.real >= 0) != (symbol.real >= 0)
        or (sample.imag >= 0) != (symbol.imag >= 0)
        for symbol, sample in zip(reference, measured)
    )
    return errors / len(reference)


def sampled_output_snr(
    pulse: list[float], receive_filter: list[complex], noise_variance: float,
) -> float:
    filtered_pulse = convolve(
        [complex(value) for value in pulse], receive_filter
    )
    decision_index = len(pulse) - 1
    signal_power = abs(filtered_pulse[decision_index]) ** 2
    output_noise_variance = noise_variance * sum(
        abs(value) ** 2 for value in receive_filter
    )
    return signal_power / output_noise_variance


def occupied_bandwidth_bins(pulse: list[float], fft_length: int = 512) -> int:
    shifted_bins = list(range(-fft_length // 2, fft_length // 2))
    powers = []
    for frequency_bin in shifted_bins:
        response = sum(
            tap * cmath.exp(-2j * math.pi * frequency_bin * index / fft_length)
            for index, tap in enumerate(pulse)
        )
        powers.append(abs(response) ** 2)
    total = sum(powers)
    center = fft_length // 2
    for half_width in range(fft_length // 2):
        if sum(powers[center - half_width:center + half_width + 1]) / total >= 0.99:
            return half_width
    raise AssertionError("99% pulse power was not found inside the FFT grid")


class P24ModuleTests(unittest.TestCase):
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
        cls.all_content = "\n".join(
            (MODULE / name).read_text(encoding="utf-8") for name in ARTIFACTS
        )

    def test_artifacts_manifest_identity_dependency_and_public_catalogs(self):
        self.assertEqual(validate_p24_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            path = MODULE / name
            self.assertGreater(path.stat().st_size, 100)
            self.assertIn(QUESTION, path.read_text(encoding="utf-8"))
        prerequisite = next(
            entry for entry in self.manifest["modules"] if entry["id"] == "P23"
        )
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertIn("P23", self.readme)
        self.assertIn("P23", self.lesson)
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertRegex(module_index, r"\| \[P24\].*\| implemented \|")

    def test_contract_rejects_missing_empty_duplicate_nonlist_and_wrong_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "experiment.m").unlink()
            (fixture / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p24_contract(fixture, self.manifest)
            self.assertIn("P24 missing experiment.m", errors)
            self.assertIn("P24 empty checks.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][23]))
        self.assertIn(
            "expected one P24 manifest entry, found 2",
            validate_p24_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p24_contract(MODULE, {"modules": "P24"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][23]["guiding_question"] = "generic"
        malformed["modules"][23]["status"] = "scaffolded"
        errors = validate_p24_contract(MODULE, malformed)
        self.assertIn(f"P24 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P24 status must be 'implemented'", errors)

    def test_deterministic_visible_controls_private_symbols_and_noise(self):
        for marker in (
            "random_seed = 1024;", "symbol_count = 320;",
            "samples_per_symbol = 8;", "baseline_rolloff = 0.25;",
            "baseline_span_symbols = 8;", "baseline_esn0_db = 14;",
            "rolloff_sweep = [0.10 0.25 0.50 1.00];",
            "span_sweep_symbols = [2 4 6 8];",
            "broken_timing_offset_samples = 4;",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "rand(private_stream, 2, symbol_count)",
            "randn(private_stream, 1, max_waveform_samples)",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_explicit_qpsk_zero_stuffing_and_unit_energy_pulses(self):
        for formula in (
            "qpsk_i = 2*qpsk_bits(1, :) - 1;",
            "qpsk_q = 2*qpsk_bits(2, :) - 1;",
            "qpsk_symbols = (qpsk_i + 1j*qpsk_q)/sqrt(2);",
            "upsampled_symbols(1:samples_per_symbol:end) = qpsk_symbols;",
            "rectangular_pulse = ones(1, samples_per_symbol)/sqrt(samples_per_symbol);",
            "rrc_pulse = rrc_pulse/sqrt(sum(abs(rrc_pulse).^2));",
        ):
            self.assertIn(formula, self.experiment)
        symbols = deterministic_qpsk(100)
        self.assertTrue(all(abs(abs(symbol) ** 2 - 1) < 1e-12 for symbol in symbols))
        pulse = rrc_pulse(0.25, 8, 8)
        self.assertEqual(len(pulse), 65)
        self.assertAlmostEqual(sum(value * value for value in pulse), 1.0, places=12)

    def test_rrc_singularity_branches_are_finite_and_formula_bound(self):
        pulse = rrc_pulse(0.25, 8, 8)
        self.assertTrue(all(math.isfinite(value) for value in pulse))
        self.assertAlmostEqual(pulse[32], pulse[-33], places=12)
        self.assertAlmostEqual(pulse[24], pulse[40], places=12)
        for marker in (
            "if abs(x) < 1e-12",
            "abs(abs(x) - 1/(4*baseline_rolloff)) < 1e-12",
            "1 + baseline_rolloff*(4/pi - 1)",
            "sin(pi*x*(1-baseline_rolloff))",
            "1-(4*baseline_rolloff*x)^2",
        ):
            self.assertIn(marker, self.experiment)

    def test_matched_filter_timing_and_noiseless_isi_oracle(self):
        symbols = deterministic_qpsk(160)
        pulse = rrc_pulse(0.25, 8, 8)
        transmitted, _, matched_samples = shaped_samples(symbols, pulse, 8)
        transmit_delay = (len(pulse) - 1) // 2
        raw_samples = [
            transmitted[transmit_delay + index * 8] / pulse[transmit_delay]
            for index in range(len(symbols))
        ]
        matched_evm = evm(symbols, matched_samples, 8)
        raw_evm = evm(symbols, raw_samples, 8)
        self.assertLess(matched_evm, 0.02)
        self.assertLess(matched_evm, raw_evm / 5)
        for marker in (
            "rrc_matched_filter = conj(fliplr(rrc_pulse));",
            "rrc_matched_output = conv(rrc_received, rrc_matched_filter);",
            "rrc_total_group_delay = numel(rrc_pulse)-1;",
            "rrc_sample_indices = 1 + rrc_total_group_delay +",
        ):
            self.assertIn(marker, self.experiment)

    def test_esn0_complex_noise_and_unit_energy_matched_variance(self):
        # Each standardized complex sample has zero mean, E|n|^2=1, and
        # E(Re(n)^2)=E(Im(n)^2)=1/2.
        standardized = [
            complex(i_value, q_value) / math.sqrt(2)
            for i_value, q_value in ((1, 1), (1, -1), (-1, 1), (-1, -1))
        ]
        self.assertAlmostEqual(sum(standardized).real, 0.0, places=12)
        self.assertAlmostEqual(sum(standardized).imag, 0.0, places=12)
        self.assertAlmostEqual(
            sum(abs(sample) ** 2 for sample in standardized) / len(standardized),
            1.0,
            places=12,
        )

        pulse = rrc_pulse(0.25, 8, 8)
        esn0_db = 14.0
        noise_sigma = math.sqrt(10 ** (-esn0_db / 10))
        input_complex_variance = noise_sigma ** 2
        matched_output_variance = input_complex_variance * sum(
            value * value for value in pulse
        )
        self.assertAlmostEqual(matched_output_variance, 10 ** (-1.4), places=12)
        self.assertAlmostEqual(
            100 * math.sqrt(matched_output_variance),
            100 * 10 ** (-esn0_db / 20),
            places=12,
        )

        for marker in (
            "1j*randn(private_stream, 1, max_waveform_samples))/sqrt(2);",
            "baseline_noise_sigma = sqrt(10^(-baseline_esn0_db/10));",
            "baseline_noise_sigma*noise_unit(1:numel(rectangular_transmitted))",
            "baseline_noise_sigma*noise_unit(1:numel(rrc_transmitted))",
            "abs(sum(abs(rrc_pulse).^2)-1) < 1e-12",
        ):
            self.assertIn(marker, self.experiment)

    def test_matched_filter_maximizes_sampled_snr_for_equal_energy_receivers(self):
        pulse = rrc_pulse(0.25, 8, 8)
        matched = [complex(value).conjugate() for value in reversed(pulse)]

        center_sampler = [0j] * len(pulse)
        center_sampler[len(pulse) // 2] = 1
        flat_integrator = [complex(1 / math.sqrt(len(pulse)))] * len(pulse)
        shifted_match = [0j] + matched[:-1]
        shifted_energy = math.sqrt(sum(abs(value) ** 2 for value in shifted_match))
        shifted_match = [value / shifted_energy for value in shifted_match]
        receivers = (center_sampler, flat_integrator, shifted_match)

        noise_variance = 10 ** (-14.0 / 10)
        matched_snr = sampled_output_snr(pulse, matched, noise_variance)
        alternative_snrs = [
            sampled_output_snr(pulse, receiver, noise_variance)
            for receiver in receivers
        ]

        self.assertAlmostEqual(sum(abs(value) ** 2 for value in matched), 1.0)
        for receiver in receivers:
            self.assertAlmostEqual(sum(abs(value) ** 2 for value in receiver), 1.0)
        self.assertAlmostEqual(matched_snr, 10 ** (14.0 / 10), places=12)
        self.assertGreater(matched_snr, max(alternative_snrs))
        self.assertEqual(
            self.experiment.count(
                "rrc_matched_filter = conj(fliplr(rrc_pulse));"
            ),
            1,
        )
        self.assertIn(
            "maximizes output signal-to-noise ratio at that sample",
            self.lesson,
        )

    def test_rolloff_only_sweep_expands_occupied_bandwidth(self):
        widths = [
            occupied_bandwidth_bins(rrc_pulse(rolloff, 8, 8))
            for rolloff in (0.10, 0.25, 0.50, 1.00)
        ]
        self.assertEqual(widths, sorted(widths))
        self.assertGreater(widths[-1], widths[0])
        sweep = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        self.assertEqual(sweep.count("for sweep_index ="), 1)
        self.assertIn("case_rolloff = rolloff_sweep(sweep_index);", sweep)
        self.assertIn("case_span_symbols = baseline_span_symbols;", sweep)
        self.assertNotIn("span_sweep_symbols(sweep_index)", sweep)
        self.assertNotRegex(sweep, r"\brandn?\s*\(")

    def test_span_only_sweep_reduces_controlled_truncation_isi(self):
        symbols = deterministic_qpsk(160)
        values = []
        for span in (2, 4, 6, 8):
            _, _, samples = shaped_samples(symbols, rrc_pulse(0.25, span, 8), 8)
            values.append(evm(symbols, samples, span))
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertGreater(values[0], values[-1] * 10)

        sweep = self.experiment.split("%% Sweep 2", 1)[1].split(
            "%% Broken case", 1
        )[0]
        self.assertEqual(sweep.count("for sweep_index ="), 1)
        self.assertIn(
            "case_span_symbols = span_sweep_symbols(sweep_index);", sweep
        )
        self.assertIn("case_rolloff = baseline_rolloff;", sweep)
        self.assertNotIn("rolloff_sweep(sweep_index)", sweep)
        self.assertNotRegex(sweep, r"\brandn?\s*\(")

    def test_broken_half_symbol_timing_and_exact_recovery(self):
        symbols = deterministic_qpsk(160)
        pulse = rrc_pulse(0.25, 8, 8)
        _, _, correct = shaped_samples(symbols, pulse, 8)
        _, _, broken = shaped_samples(symbols, pulse, 8, timing_offset=4)
        self.assertGreater(evm(symbols, broken, 8), 0.40)
        self.assertGreater(symbol_error_rate(symbols, broken), 0.05)
        self.assertLess(evm(symbols, correct, 8), 0.02)

        broken_source = self.experiment.split("%% Broken case", 1)[1].split(
            "%% Baseline view 4", 1
        )[0]
        for marker in (
            "broken_sample_indices = rrc_sample_indices + broken_timing_offset_samples;",
            "broken_isi_evm_pct", "broken_symbol_errors", "broken_ser",
            "broken_sample_indices-broken_timing_offset_samples",
            "recovered_isi_evm_pct", "recovered_symbol_errors == 0",
        ):
            self.assertIn(marker, broken_source)

    def test_malformed_controls_and_resource_ceilings(self):
        invalid = (
            ("random_seed", True), ("symbol_count", 321),
            ("samples_per_symbol", 16), ("displayed_symbol_count", 13),
            ("baseline_rolloff", math.nan),
            ("baseline_span_symbols", complex(8, 1)),
            ("baseline_esn0_db", math.inf), ("spectrum_fft_length", 2048),
            ("rolloff_sweep", (0.1, 0.25, 0.5)),
            ("span_sweep_symbols", (2, 4, 6, 10)),
            ("broken_timing_offset_samples", 3), ("eye_trace_count", 80),
            ("max_symbol_count", 640), ("max_samples_per_symbol", 16),
            ("max_span_symbols", 12), ("max_sweep_cases", 8),
            ("max_figure_groups", 6),
            ("max_stored_numeric_values", 1000000),
        )
        for key, value in invalid:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_controls(**{key: value})
        with self.assertRaises(ValueError):
            validate_controls(unknown_control=1)

    def test_matlab_guards_precede_random_allocation_fft_cleanup_and_figures(self):
        validation = self.experiment.split("% Validation succeeded:", 1)[0]
        for control in canonical_controls():
            self.assertIn(f"~islogical({control})", validation, control)
        validation_end = self.experiment.index("% Validation succeeded:")
        for marker in (
            "RandStream(", "qpsk_bits =", "complex(zeros(", "conv(",
            "fft(", "close(findall(", "figure('Name'",
        ):
            self.assertGreater(self.experiment.index(marker), validation_end, marker)

    def test_plot_metric_unit_and_retained_result_inventory(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 5)
        self.assertEqual(self.experiment.count("'Tag', 'P24'"), 6)
        self.assertIn(
            "close(findall(0, 'Type', 'figure', 'Tag', 'P24'));",
            self.experiment,
        )
        for unit in (
            "Time (symbol periods T)", "Normalized frequency f/R_s",
            "Pulse power response (dB)", "In-phase I (normalized)",
            "Quadrature Q (normalized)", "ISI-only EVM (%)",
            "99% occupied bandwidth / R_s",
        ):
            self.assertIn(unit, self.experiment)
        for result in (
            "qpsk_bits", "qpsk_symbols", "upsampled_symbols",
            "rectangular_pulse", "rrc_pulse", "rrc_matched_filter",
            "rectangular_transmitted", "rrc_transmitted", "rrc_received",
            "rrc_matched_output", "rrc_sample_indices",
            "rrc_pre_filter_samples", "rrc_samples",
            "rrc_matched_evm_pct", "rrc_isi_only_evm_pct", "rrc_ser",
            "rectangular_occupied_bandwidth_rs", "rrc_occupied_bandwidth_rs",
            "rectangular_transmitted_spectrum_power",
            "rrc_transmitted_spectrum_power",
            "rolloff_sweep_bandwidth_rs", "rolloff_sweep_isi_evm_pct",
            "span_sweep_tap_counts", "span_sweep_isi_evm_pct",
            "broken_samples", "broken_ser", "broken_isi_evm_pct",
            "recovered_samples", "recovered_ser", "recovered_isi_evm_pct",
        ):
            self.assertIn(f"results.{result}", self.experiment)

    def test_no_placeholder_unexplained_black_box_or_external_io(self):
        self.assertNotRegex(self.all_content, r"(?i)\bTODO\b|\bTBD\b|lorem ipsum")
        for call in (
            "rcosdesign(", "rcosflt(", "upfirdn(", "filter(", "awgn(",
            "comm.", "eyediagram(", "scatterplot(", "xline(", "yline(",
            "parfor ", "timer(", "webread(", "urlread(", "fopen(",
            "save(", "writetable(", "system(", "!",
        ):
            self.assertNotIn(call, self.experiment)
        self.assertIn("Base MATLAB only", self.experiment)
        self.assertIn("no communications toolbox", self.readme.lower())

    def test_concept_first_content_and_runtime_claim_boundary(self):
        for phrase in (
            "pulse shaping", "occupied bandwidth", "intersymbol interference",
            "conjugated", "time-reversed", "white noise", "group delay",
            "symbol clock", "finite tap span", "rectangular", "radar",
        ):
            self.assertIn(phrase, self.lesson.lower())
        for section in ("Sweep 1", "Sweep 2", "Broken case"):
            self.assertIn(section, self.experiment)
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P24-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence_text = evidence_paths[0].read_text(encoding="utf-8")
        self.assertIn("MATLAB", evidence_text)
        self.assertIn("did not run", evidence_text.lower())
        self.assertIn("unperformed", evidence_text.lower())

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback(self):
        operational = "\n".join((self.walkthrough, self.checks))
        for phrase in (
            "Ctrl+C", "workspace variables", "full rerun", "private seed",
            "global random stream", ".learning/", "worker", "timer",
            "external transaction", "rollback", "P23", "base MATLAB",
        ):
            self.assertIn(phrase.lower(), operational.lower())
        self.assertIn("cannot restore", operational.lower())
        self.assertIn("max_symbol_count = 320;", self.experiment)
        self.assertIn("max_samples_per_symbol = 8;", self.experiment)
        self.assertIn("max_span_symbols = 8;", self.experiment)
        self.assertIn("max_sweep_cases = 4;", self.experiment)
        self.assertIn("max_figure_groups = 5;", self.experiment)
        self.assertIn("max_stored_numeric_values = 500000;", self.experiment)
        self.assertLess(
            self.experiment.index("results = struct();"),
            self.experiment.index("RandStream("),
        )


if __name__ == "__main__":
    unittest.main()
