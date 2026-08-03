from __future__ import annotations

import cmath
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/23-build-bpsk-and-qpsk-constellation-intuition"
QUESTION = "What do symbols, phase states, and decision regions look like in IQ?"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
EXPECTED_IDENTITY = {
    "number": 23,
    "id": "P23",
    "title": "Build BPSK and QPSK Constellation Intuition",
    "guiding_question": QUESTION,
    "phase": 3,
    "phase_title": "Modulation, Channels, and Statistical Estimation",
    "slug": "build-bpsk-and-qpsk-constellation-intuition",
    "folder": "modules/23-build-bpsk-and-qpsk-constellation-intuition",
    "status": "implemented",
    "implementation_batch": "P23",
}


def validate_p23_contract(module_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_dir / name
        if not path.is_file():
            errors.append(f"P23 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P23 empty {name}")

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return errors + ["manifest modules must be a list"]
    matches = [
        entry for entry in modules
        if isinstance(entry, dict) and entry.get("id") == "P23"
    ]
    if len(matches) != 1:
        return errors + [f"expected one P23 manifest entry, found {len(matches)}"]
    entry = matches[0]
    for key, expected in EXPECTED_IDENTITY.items():
        if entry.get(key) != expected:
            errors.append(f"P23 {key} must be {expected!r}")
    return errors


def _finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def canonical_controls() -> dict:
    return {
        "random_seed": 1023,
        "symbol_count": 400,
        "displayed_symbol_count": 24,
        "baseline_ebn0_db": 6.0,
        "baseline_phase_error_deg": 12.0,
        "snr_sweep_db": (-4.0, 0.0, 4.0, 8.0),
        "phase_sweep_deg": (0.0, 15.0, 30.0, 50.0),
        "phase_sweep_ebn0_db": 8.0,
        "broken_phase_error_deg": 55.0,
        "broken_ebn0_db": 16.0,
        "constellation_axis_limit": 2.2,
        "max_symbol_count": 400,
        "max_sweep_cases": 4,
        "max_figure_groups": 5,
        "max_stored_numeric_values": 120000,
    }


def validate_controls(**overrides: object) -> None:
    controls = canonical_controls()
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)

    vectors = {
        "snr_sweep_db": (-4.0, 0.0, 4.0, 8.0),
        "phase_sweep_deg": (0.0, 15.0, 30.0, 50.0),
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
        raise ValueError("display count must fit the generated record")
    if controls["symbol_count"] > controls["max_symbol_count"]:
        raise ValueError("symbol count exceeds its resource ceiling")
    if len(controls["snr_sweep_db"]) > controls["max_sweep_cases"]:
        raise ValueError("SNR sweep exceeds its resource ceiling")
    if len(controls["phase_sweep_deg"]) > controls["max_sweep_cases"]:
        raise ValueError("phase sweep exceeds its resource ceiling")


def map_bpsk(bits: list[int]) -> list[complex]:
    return [complex(2 * bit - 1) for bit in bits]


def map_qpsk(bit_pairs: list[tuple[int, int]]) -> list[complex]:
    return [
        complex(2 * bit_i - 1, 2 * bit_q - 1) / math.sqrt(2)
        for bit_i, bit_q in bit_pairs
    ]


def receive(
    symbols: list[complex], *, phase_deg: float,
    noise: list[complex] | None = None, sigma: float = 0.0,
) -> list[complex]:
    if noise is None:
        noise = [0j] * len(symbols)
    rotation = cmath.exp(1j * math.pi * phase_deg / 180)
    return [symbol * rotation + sigma * sample for symbol, sample in zip(symbols, noise)]


def detect_bpsk(received: list[complex]) -> list[int]:
    return [int(sample.real >= 0) for sample in received]


def detect_qpsk(received: list[complex]) -> list[tuple[int, int]]:
    return [(int(sample.real >= 0), int(sample.imag >= 0)) for sample in received]


def bit_error_rate(expected: list, actual: list) -> float:
    expected_flat = [bit for item in expected for bit in (item if isinstance(item, tuple) else (item,))]
    actual_flat = [bit for item in actual for bit in (item if isinstance(item, tuple) else (item,))]
    return sum(left != right for left, right in zip(expected_flat, actual_flat)) / len(expected_flat)


class P23ModuleTests(unittest.TestCase):
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
        self.assertEqual(validate_p23_contract(MODULE, self.manifest), [])
        for name in ARTIFACTS:
            path = MODULE / name
            self.assertGreater(path.stat().st_size, 100)
            self.assertIn(QUESTION, path.read_text(encoding="utf-8"))
        prerequisite = next(
            entry for entry in self.manifest["modules"] if entry["id"] == "P22"
        )
        self.assertEqual(prerequisite["status"], "implemented")
        self.assertIn("P22", self.readme)
        self.assertIn("P22", self.lesson)
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertRegex(module_index, r"\| \[P23\].*\| implemented \|")

    def test_contract_rejects_missing_empty_duplicate_nonlist_and_wrong_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            (fixture / "experiment.m").unlink()
            (fixture / "checks.md").write_text("", encoding="utf-8")
            errors = validate_p23_contract(fixture, self.manifest)
            self.assertIn("P23 missing experiment.m", errors)
            self.assertIn("P23 empty checks.md", errors)

        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][22]))
        self.assertIn(
            "expected one P23 manifest entry, found 2",
            validate_p23_contract(MODULE, duplicate),
        )
        self.assertIn(
            "manifest modules must be a list",
            validate_p23_contract(MODULE, {"modules": "P23"}),
        )
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"][22]["guiding_question"] = "generic"
        malformed["modules"][22]["status"] = "scaffolded"
        errors = validate_p23_contract(MODULE, malformed)
        self.assertIn(f"P23 guiding_question must be {QUESTION!r}", errors)
        self.assertIn("P23 status must be 'implemented'", errors)

    def test_deterministic_visible_controls_private_bits_and_noise(self):
        for marker in (
            "random_seed = 1023;", "symbol_count = 400;",
            "baseline_ebn0_db = 6;", "baseline_phase_error_deg = 12;",
            "snr_sweep_db = [-4 0 4 8];",
            "phase_sweep_deg = [0 15 30 50];",
            "RandStream('mt19937ar', 'Seed', random_seed)",
            "rand(private_stream, 1, symbol_count)",
            "rand(private_stream, 2, symbol_count)",
            "randn(private_stream, 1, symbol_count)",
        ):
            self.assertIn(marker, self.experiment)
        self.assertNotRegex(self.experiment, r"(?m)^\s*rng\s*\(")

    def test_explicit_bpsk_qpsk_mapping_energy_and_gray_neighbors(self):
        bpsk = map_bpsk([0, 1])
        pairs = [(0, 0), (1, 0), (1, 1), (0, 1)]
        qpsk = map_qpsk(pairs)
        self.assertEqual(bpsk, [-1 + 0j, 1 + 0j])
        self.assertTrue(all(abs(abs(symbol) ** 2 - 1) < 1e-12 for symbol in qpsk))
        for left, right in zip(pairs, pairs[1:] + pairs[:1]):
            self.assertEqual(sum(a != b for a, b in zip(left, right)), 1)
        for formula in (
            "bpsk_symbols = 2*bpsk_bits - 1;",
            "qpsk_i = 2*qpsk_bits(1, :) - 1;",
            "qpsk_q = 2*qpsk_bits(2, :) - 1;",
            "qpsk_symbols = (qpsk_i + 1j*qpsk_q)/sqrt(2);",
        ):
            self.assertIn(formula, self.experiment)

    def test_explicit_ebn0_noise_scaling_and_hard_decisions(self):
        gamma = 10 ** (6 / 10)
        self.assertAlmostEqual(math.sqrt(1 / (2 * gamma)), 0.3543928915, places=9)
        self.assertAlmostEqual(math.sqrt(1 / (4 * gamma)), 0.2505936168, places=9)
        self.assertIn(
            "bpsk_noise_sigma = sqrt(1/(2*baseline_ebn0_linear));",
            self.experiment,
        )
        self.assertIn(
            "qpsk_noise_sigma = sqrt(1/(4*baseline_ebn0_linear));",
            self.experiment,
        )
        self.assertIn("double(real(bpsk_received) >= 0)", self.experiment)
        self.assertIn("double(imag(qpsk_received) >= 0)", self.experiment)

    def test_snr_only_sweep_tightens_clusters_and_nonincreases_ber(self):
        bits = [0, 1] * 100
        symbols = map_bpsk(bits)
        noise = [complex(value, 0) for value in (
            [-2.5, -1.5, -0.8, -0.2, 0.2, 0.8, 1.5, 2.5] * 25
        )]
        rates = []
        for ebn0_db in (-4, 0, 4, 8):
            sigma = math.sqrt(1 / (2 * 10 ** (ebn0_db / 10)))
            rates.append(bit_error_rate(bits, detect_bpsk(receive(
                symbols, phase_deg=0, noise=noise, sigma=sigma
            ))))
        self.assertEqual(rates, sorted(rates, reverse=True))
        self.assertGreater(rates[0], rates[-1])

        snr = self.experiment.split("%% Sweep 1", 1)[1].split("%% Sweep 2", 1)[0]
        self.assertEqual(snr.count("for sweep_index ="), 1)
        self.assertIn("case_ebn0_db = snr_sweep_db(sweep_index);", snr)
        self.assertNotIn("case_phase_error_deg", snr)
        self.assertIn("case_bpsk_received = bpsk_symbols +", snr)
        self.assertIn("case_qpsk_received = qpsk_symbols +", snr)

    def test_equal_ebn0_bpsk_qpsk_paired_bit_error_behavior(self):
        bits = [0, 0, 0, 1, 1, 0, 1, 1] * 4
        bit_pairs = list(zip(bits[::2], bits[1::2]))
        signed_disturbances = (
            [-2.5, -1.5, -0.8, -0.2, 0.2, 0.8, 1.5, 2.5] * 4
        )
        standard_noise = [
            complex((2 * bit - 1) * disturbance, 0)
            for bit, disturbance in zip(bits, signed_disturbances)
        ]
        qpsk_standard_noise = [
            complex(standard_noise[index].real, standard_noise[index + 1].real)
            for index in range(0, len(standard_noise), 2)
        ]

        bpsk_symbols = map_bpsk(bits)
        qpsk_symbols = map_qpsk(bit_pairs)
        paired_rates = []
        for ebn0_db in (-4, 0, 4, 8):
            gamma_b = 10 ** (ebn0_db / 10)
            bpsk_received = receive(
                bpsk_symbols,
                phase_deg=0,
                noise=standard_noise,
                sigma=math.sqrt(1 / (2 * gamma_b)),
            )
            qpsk_received = receive(
                qpsk_symbols,
                phase_deg=0,
                noise=qpsk_standard_noise,
                sigma=math.sqrt(1 / (4 * gamma_b)),
            )
            bpsk_decisions = detect_bpsk(bpsk_received)
            qpsk_decisions = [
                bit for pair in detect_qpsk(qpsk_received) for bit in pair
            ]
            self.assertEqual(bpsk_decisions, qpsk_decisions)
            bpsk_rate = bit_error_rate(bits, bpsk_decisions)
            qpsk_rate = bit_error_rate(bit_pairs, detect_qpsk(qpsk_received))
            self.assertEqual(bpsk_rate, qpsk_rate)
            paired_rates.append(bpsk_rate)

        self.assertEqual(paired_rates, sorted(paired_rates, reverse=True))
        self.assertGreater(paired_rates[0], paired_rates[-1])

        snr = self.experiment.split("%% Sweep 1", 1)[1].split(
            "%% Sweep 2", 1
        )[0]
        for marker in (
            "case_bpsk_noise_sigma = sqrt(1/(2*case_ebn0_linear));",
            "case_qpsk_noise_sigma = sqrt(1/(4*case_ebn0_linear));",
            "case_bpsk_noise_sigma*bpsk_noise_unit",
            "case_qpsk_noise_sigma*qpsk_noise_unit",
        ):
            self.assertIn(marker, snr)
        self.assertNotRegex(snr, r"\brandn?\s*\(")

    def test_phase_only_sweep_crosses_qpsk_before_bpsk_boundaries(self):
        bpsk_bits = [0, 1]
        qpsk_bits = [(0, 0), (1, 0), (1, 1), (0, 1)]
        bpsk = map_bpsk(bpsk_bits)
        qpsk = map_qpsk(qpsk_bits)
        self.assertEqual(bit_error_rate(
            bpsk_bits, detect_bpsk(receive(bpsk, phase_deg=50))
        ), 0)
        self.assertEqual(bit_error_rate(
            qpsk_bits, detect_qpsk(receive(qpsk, phase_deg=30))
        ), 0)
        self.assertEqual(bit_error_rate(
            qpsk_bits, detect_qpsk(receive(qpsk, phase_deg=50))
        ), 0.5)

        phase = self.experiment.split("%% Sweep 2", 1)[1].split(
            "%% Broken case", 1
        )[0]
        self.assertEqual(phase.count("for sweep_index ="), 1)
        self.assertIn(
            "case_phase_error_deg = phase_sweep_deg(sweep_index);", phase
        )
        self.assertNotIn("case_ebn0_db", phase)
        self.assertIn("phase_sweep_ebn0_db = 8;", self.experiment)

    def test_broken_phase_reference_and_exact_derotation_recovery(self):
        bits = [(0, 0), (1, 0), (1, 1), (0, 1)]
        symbols = map_qpsk(bits)
        broken = receive(symbols, phase_deg=55)
        self.assertEqual(bit_error_rate(bits, detect_qpsk(broken)), 0.5)
        recovered = [
            sample * cmath.exp(-1j * math.pi * 55 / 180) for sample in broken
        ]
        self.assertEqual(bit_error_rate(bits, detect_qpsk(recovered)), 0)
        self.assertLess(math.cos(math.pi * (45 + 55) / 180), 0)

        broken_source = self.experiment.split("%% Broken case", 1)[1].split(
            "%% Retained workspace results", 1
        )[0]
        for marker in (
            "broken_phase_error_deg = 55;", "broken_ebn0_db = 16;",
            "broken_qpsk_received", "broken_qpsk_ber",
            "recovered_qpsk", "recovered_qpsk_ber",
            "exp(-1j*pi*broken_phase_error_deg/180)",
            "broken_qpsk_ber > 0.40", "recovered_qpsk_bit_errors == 0",
            "broken_minimum_signed_ideal_margin < 0",
        ):
            self.assertIn(marker, self.experiment if " = " in marker else broken_source)

    def test_malformed_controls_and_resource_ceilings(self):
        invalid = (
            ("random_seed", True), ("symbol_count", 401),
            ("displayed_symbol_count", 25), ("baseline_ebn0_db", math.nan),
            ("baseline_phase_error_deg", complex(12, 1)),
            ("snr_sweep_db", (-4.0, 0.0, math.inf, 8.0)),
            ("phase_sweep_deg", (0.0, 15.0, 30.0)),
            ("phase_sweep_ebn0_db", 9.0),
            ("broken_phase_error_deg", 45.0), ("broken_ebn0_db", -16.0),
            ("constellation_axis_limit", 0.0), ("max_symbol_count", 800),
            ("max_sweep_cases", 5), ("max_figure_groups", 6),
            ("max_stored_numeric_values", 240000),
        )
        for key, value in invalid:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_controls(**{key: value})
        with self.assertRaises(ValueError):
            validate_controls(unknown_control=1)

    def test_matlab_guards_reject_logical_controls_before_random_work(self):
        validation = self.experiment.split("% Validation succeeded:", 1)[0]
        for control in canonical_controls():
            self.assertIn(f"~islogical({control})", validation, control)

    def test_validation_precedes_random_allocation_cleanup_and_figures(self):
        validation_end = self.experiment.index("% Validation succeeded:")
        for marker in (
            "RandStream(", "bpsk_bits =", "qpsk_bits =", "randn(",
            "close(findall(", "figure('Name'",
        ):
            self.assertGreater(self.experiment.index(marker), validation_end, marker)

    def test_plot_metric_unit_and_retained_result_inventory(self):
        self.assertEqual(self.experiment.count("figure('Name'"), 5)
        self.assertEqual(self.experiment.count("'Tag', 'P23'"), 6)
        self.assertIn("close(findall(0, 'Type', 'figure', 'Tag', 'P23'));", self.experiment)
        for unit in (
            "Symbol index", "In-phase I (normalized)",
            "Quadrature Q (normalized)", "Eb/N0=%g dB", "Phase=%g deg",
            "bit error (0 or 1)", "bit errors per symbol",
        ):
            self.assertIn(unit, self.experiment)
        for result in (
            "bpsk_bits", "qpsk_bits", "bpsk_symbols", "qpsk_symbols",
            "bpsk_received", "qpsk_received", "bpsk_detected_bits",
            "qpsk_detected_bits", "bpsk_bit_errors", "qpsk_bit_errors",
            "bpsk_ber", "qpsk_ber", "bpsk_symbol_energy",
            "qpsk_symbol_energy", "snr_sweep_bpsk_ber",
            "snr_sweep_qpsk_ber", "phase_sweep_bpsk_ber",
            "phase_sweep_qpsk_ber", "broken_qpsk_ber",
            "recovered_qpsk_ber", "recovered_qpsk_bit_errors",
        ):
            self.assertIn(f"results.{result}", self.experiment)

    def test_no_placeholder_unexplained_black_box_or_external_io(self):
        self.assertNotRegex(self.all_content, r"(?i)\bTODO\b|\bTBD\b|lorem ipsum")
        for call in (
            "pskmod(", "pskdemod(", "qammod(", "qamdemod(", "awgn(",
            "comm.", "berawgn(", "scatterplot(", "xline(", "yline(",
            "parfor ", "timer(", "webread(", "urlread(", "fopen(",
            "save(", "writetable(", "system(", "!",
        ):
            self.assertNotIn(call, self.experiment)
        self.assertIn("Base MATLAB only", self.experiment)
        self.assertIn("no communications toolbox", self.readme.lower())

    def test_concept_first_content_and_runtime_claim_boundary(self):
        for phrase in (
            "decision", "boundary", "noise", "phase error", "45 degrees",
            "derotates", "unit symbol energy", "radar",
        ):
            self.assertIn(phrase.lower(), self.lesson.lower())
        for section in ("Sweep 1", "Sweep 2", "Broken case"):
            self.assertIn(section, self.experiment)
        evidence_paths = sorted((ROOT / "docs/evidence").glob("P23-*.md"))
        self.assertEqual(len(evidence_paths), 1)
        evidence_text = evidence_paths[0].read_text(encoding="utf-8")
        self.assertIn("MATLAB", evidence_text)
        self.assertIn("did not run", evidence_text.lower())
        self.assertIn("unperformed", evidence_text.lower())

    def test_timeout_cancellation_recovery_isolation_compatibility_and_rollback(self):
        operational = "\n".join((self.walkthrough, self.checks))
        for phrase in (
            "Ctrl+C", "workspace variables", "full rerun", "private seed",
            "global random stream", ".learning/", "worker",
            "external transaction", "rollback", "P22", "base MATLAB",
        ):
            self.assertIn(phrase.lower(), operational.lower())
        self.assertIn("cannot restore", operational.lower())
        self.assertIn("max_symbol_count = 400;", self.experiment)
        self.assertIn("max_sweep_cases = 4;", self.experiment)
        self.assertIn("max_figure_groups = 5;", self.experiment)
        self.assertIn("max_stored_numeric_values = 120000;", self.experiment)
        self.assertLess(
            self.experiment.index("results = struct();"),
            self.experiment.index("RandStream("),
        )


if __name__ == "__main__":
    unittest.main()
