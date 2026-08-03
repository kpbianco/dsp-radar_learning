from __future__ import annotations

import copy
import json
import math
import os
import random
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/41-model-ground-clutter-and-swerling-targets"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "Why do clutter and target amplitude fluctuate differently from white noise?"
MAX_RANGE_BINS = 128
MAX_PULSES = 128
MAX_TRIALS = 4096
MAX_SWEEP_CASES = 8
EXPECTED_IDENTITY = {
    "number": 41,
    "id": "P41",
    "title": "Model Ground Clutter and Swerling Targets",
    "guiding_question": QUESTION,
    "phase": 4,
    "phase_title": "Pulsed and Pulse-Doppler Radar Foundations",
    "slug": "model-ground-clutter-and-swerling-targets",
    "folder": "modules/41-model-ground-clutter-and-swerling-targets",
    "status": "implemented",
    "implementation_batch": "P41",
}


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_p41_contract(module_path: Path, manifest: object) -> list[str]:
    errors: list[str] = []
    for name in ARTIFACTS:
        path = module_path / name
        if not path.is_file():
            errors.append(f"P41 missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P41 empty {name}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return errors + ["manifest modules must be a list"]
    if not all(isinstance(item, dict) for item in manifest["modules"]):
        return errors + ["manifest module entries must be objects"]
    matches = [item for item in manifest["modules"] if item.get("id") == "P41"]
    if len(matches) != 1:
        return errors + [f"expected one P41 manifest entry, found {len(matches)}"]
    for key, expected in EXPECTED_IDENTITY.items():
        if matches[0].get(key) != expected:
            errors.append(f"P41 {key} must be {expected!r}")
    return errors


def validate_controls(
    *,
    range_bin_count: object = 96,
    pulse_count: object = 64,
    target_trial_count: object = 2000,
    broken_trial_count: object = 1024,
    range_correlation: object = 0.85,
    slow_time_correlation: object = 0.92,
    target_average_snr_db: object = -3.0,
    false_alarm_probability: object = 0.05,
    integration_sweep: object = (1, 2, 4, 8, 16, 32),
    correlation_sweep: object = (0, 0.50, 0.85, 0.97),
) -> None:
    integer_bounds = (
        ("range bins", range_bin_count, 32, MAX_RANGE_BINS),
        ("pulse count", pulse_count, 32, MAX_PULSES),
        ("target trials", target_trial_count, 1000, MAX_TRIALS),
        ("broken trials", broken_trial_count, 512, MAX_TRIALS),
    )
    for name, value, lower, upper in integer_bounds:
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not lower <= value <= upper
        ):
            raise ValueError(f"{name} must be a bounded integer")
    for name, value in (
        ("range correlation", range_correlation),
        ("slow-time correlation", slow_time_correlation),
    ):
        if not finite_real(value) or not 0 <= value < 1:
            raise ValueError(f"{name} must be finite and in [0, 1)")
    if not finite_real(target_average_snr_db) or not -20 <= target_average_snr_db <= 20:
        raise ValueError("target average SNR must be finite and bounded")
    if (
        not finite_real(false_alarm_probability)
        or not 0 < false_alarm_probability < 0.5
    ):
        raise ValueError("false-alarm probability must be finite and in (0, 0.5)")
    if (
        not isinstance(integration_sweep, (list, tuple))
        or not 4 <= len(integration_sweep) <= MAX_SWEEP_CASES
    ):
        raise ValueError("integration sweep must have a bounded case count")
    if not all(
        isinstance(value, int)
        and not isinstance(value, bool)
        and 1 <= value <= pulse_count
        for value in integration_sweep
    ):
        raise ValueError("integration sweep entries must be bounded integers")
    if any(right <= left for left, right in zip(integration_sweep, integration_sweep[1:])):
        raise ValueError("integration sweep must increase strictly")
    if (
        not isinstance(correlation_sweep, (list, tuple))
        or not 4 <= len(correlation_sweep) <= MAX_SWEEP_CASES
    ):
        raise ValueError("correlation sweep must have a bounded case count")
    if not all(finite_real(value) and 0 <= value < 1 for value in correlation_sweep):
        raise ValueError("correlation sweep entries must be finite and in [0, 1)")
    if any(right <= left for left, right in zip(correlation_sweep, correlation_sweep[1:])):
        raise ValueError("correlation sweep must increase strictly")
    if not any(math.isclose(value, range_correlation) for value in correlation_sweep):
        raise ValueError("correlation sweep must contain the baseline")


def clutter_power_profile(
    ranges_km: list[float],
    *,
    near_power: float = 25.0,
    floor_power: float = 0.10,
    exponent: float = 2.0,
) -> list[float]:
    if not ranges_km or not all(finite_real(value) and value > 0 for value in ranges_km):
        raise ValueError("ranges must be finite and positive")
    if any(right <= left for left, right in zip(ranges_km, ranges_km[1:])):
        raise ValueError("ranges must increase strictly")
    if not all(finite_real(value) and value > 0 for value in (near_power, floor_power, exponent)):
        raise ValueError("profile controls must be finite and positive")
    reference = ranges_km[0]
    return [floor_power + near_power * (value / reference) ** (-exponent) for value in ranges_km]


def ar1_sequence(innovations: list[complex], correlation: float) -> list[complex]:
    if not isinstance(innovations, list) or not innovations:
        raise ValueError("innovations must be a nonempty list")
    if not all(
        isinstance(value, (int, float, complex))
        and not isinstance(value, bool)
        and math.isfinite(complex(value).real)
        and math.isfinite(complex(value).imag)
        for value in innovations
    ):
        raise ValueError("innovations must be numeric")
    if not finite_real(correlation) or not 0 <= correlation < 1:
        raise ValueError("correlation must be finite and in [0, 1)")
    output = [complex(innovations[0])]
    innovation_scale = math.sqrt(1.0 - correlation**2)
    for innovation in innovations[1:]:
        output.append(correlation * output[-1] + innovation_scale * innovation)
    return output


def swerling_power(model: str, u1: float, u2: float | None = None) -> float:
    if not finite_real(u1) or not 0 < u1 < 1:
        raise ValueError("u1 must be finite and in (0, 1)")
    if model in {"I", "II"}:
        return -math.log(u1)
    if model in {"III", "IV"}:
        if not finite_real(u2) or not 0 < u2 < 1:
            raise ValueError("u2 must be finite and in (0, 1)")
        return -0.5 * math.log(u1 * u2)
    raise ValueError("unknown Swerling model")


def theoretical_clean_power_cv(model: str, pulse_count: int) -> float:
    if not isinstance(pulse_count, int) or isinstance(pulse_count, bool) or pulse_count < 1:
        raise ValueError("pulse count must be a positive integer")
    values = {
        "steady": 0.0,
        "I": 1.0,
        "II": 1.0 / math.sqrt(pulse_count),
        "III": 1.0 / math.sqrt(2.0),
        "IV": 1.0 / math.sqrt(2.0 * pulse_count),
    }
    if model not in values:
        raise ValueError("unknown target model")
    return values[model]


def background_crossing_probability(threshold: float, mean_power: float) -> float:
    if not finite_real(threshold) or threshold < 0:
        raise ValueError("threshold must be finite and nonnegative")
    if not finite_real(mean_power) or mean_power <= 0:
        raise ValueError("mean power must be finite and positive")
    return math.exp(-threshold / mean_power)


def equal_snr_target_crossing_rates(
    seed: int = 4101,
    *,
    trial_count: int = 2000,
    pulse_count: int = 16,
    average_snr_db: float = -3.0,
    false_alarm_probability: float = 0.05,
) -> tuple[dict[str, float], float, dict[str, float]]:
    seeded = random.Random(seed)
    average_power = 10 ** (average_snr_db / 10)
    model_names = ("steady", "I", "II", "III", "IV")
    target_statistics = {name: [] for name in model_names}
    clean_power_sums = {name: 0.0 for name in model_names}

    for _ in range(trial_count):
        slow_exponential = average_power * swerling_power("I", seeded.random())
        slow_gamma_two = average_power * swerling_power(
            "III", seeded.random(), seeded.random()
        )
        statistic_sums = {name: 0.0 for name in model_names}
        for _ in range(pulse_count):
            powers = {
                "steady": average_power,
                "I": slow_exponential,
                "II": average_power * swerling_power("II", seeded.random()),
                "III": slow_gamma_two,
                "IV": average_power
                * swerling_power("IV", seeded.random(), seeded.random()),
            }
            common_noise = complex(
                seeded.gauss(0, 1 / math.sqrt(2)),
                seeded.gauss(0, 1 / math.sqrt(2)),
            )
            for name, power in powers.items():
                statistic_sums[name] += abs(math.sqrt(power) + common_noise) ** 2
                clean_power_sums[name] += power
        for name in model_names:
            target_statistics[name].append(statistic_sums[name] / pulse_count)

    noise_only_statistics = []
    for _ in range(trial_count):
        power_sum = 0.0
        for _ in range(pulse_count):
            real_part = seeded.gauss(0, 1 / math.sqrt(2))
            imaginary_part = seeded.gauss(0, 1 / math.sqrt(2))
            power_sum += real_part**2 + imaginary_part**2
        noise_only_statistics.append(power_sum / pulse_count)

    threshold_index = math.ceil(
        (1 - false_alarm_probability) * trial_count
    ) - 1
    threshold = sorted(noise_only_statistics)[threshold_index]
    crossing_rates = {
        name: sum(value > threshold for value in values) / trial_count
        for name, values in target_statistics.items()
    }
    noise_only_rate = (
        sum(value > threshold for value in noise_only_statistics) / trial_count
    )
    clean_power_means = {
        name: power_sum / (trial_count * pulse_count)
        for name, power_sum in clean_power_sums.items()
    }
    return crossing_rates, noise_only_rate, clean_power_means


def source_contract_errors(source: str) -> list[str]:
    compact = re.sub(r"\s+", " ", re.sub(r"\.\.\.\s*", "", source))
    required = (
        "random_seed = 4101",
        "RandStream('mt19937ar', 'Seed', random_seed)",
        "assert(~islogical(random_seed) && ~islogical(range_bin_count)",
        "assert(~islogical(integration_pulse_sweep) && ~islogical(range_correlation_sweep))",
        "clutter_power_profile = clutter_power_floor+clutter_power_near*",
        "range_correlation*spatial_innovation(range_index-1)+sqrt(1-range_correlation^2)*white_innovation(range_index)",
        "slow_time_correlation*unit_clutter(pulse_index-1, :)+sqrt(1-slow_time_correlation^2)*spatial_innovation",
        "target_power(:, :, 2) = repmat(swerling_i_dwell_power",
        "target_power(:, :, 3) = -target_average_power*log(max(",
        "target_power(:, :, 4) = repmat(swerling_iii_dwell_power",
        "target_power(:, :, 5) = -(target_average_power/2)*log(max(",
        "target_samples = sqrt(target_power(:, :, model_index))*exp(1j*target_phase_rad)+target_noise",
        "correlation_white_rows = (randn(private_stream",
        "row_white = correlation_white_rows(pulse_index, :)",
        "recovered_normalized_power = broken_background_power./local_background_power",
        "broken_model_valid = false",
        "recovered_model_valid = true",
        "assert(max_range_bins == 128)",
        "assert(max_pulses == 128)",
        "assert(max_trials == 4096)",
        "assert(max_sweep_cases == 8)",
        "assert(max_figure_groups == 6)",
        "max_stored_numeric_values = 1200000",
        "assert(max_stored_numeric_values == 1200000)",
        "assert(target_trial_count >= 1000 && target_trial_count <= max_trials)",
        "assert(broken_trial_count >= 512 && broken_trial_count <= max_trials)",
        "target_phase_numeric_values = baseline_numeric_values+(2*target_model_count+3)*target_trial_count*largest_integration_count",
        "broken_phase_numeric_values = baseline_numeric_values+5*broken_trial_count*range_bin_count",
        "clear target_power target_observation_power target_noise noise_only_trials",
    )
    return [marker for marker in required if marker not in compact]


class P41ModuleTests(unittest.TestCase):
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
        self.assertEqual(validate_p41_contract(MODULE, self.manifest), [])
        entries = {entry["id"]: entry for entry in self.manifest["modules"]}
        self.assertEqual(entries["P40"]["status"], "implemented")
        self.assertEqual(entries["P41"], EXPECTED_IDENTITY)
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
            self.assertIn("P41 missing checks.md", validate_p41_contract(fixture, self.manifest))
            (fixture / "checks.md").write_text("", encoding="utf-8")
            self.assertIn("P41 empty checks.md", validate_p41_contract(fixture, self.manifest))
        self.assertIn("manifest modules must be a list", validate_p41_contract(MODULE, []))
        self.assertIn(
            "manifest module entries must be objects",
            validate_p41_contract(MODULE, {"modules": [None]}),
        )
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn(
            "expected one P41 manifest entry, found 2",
            validate_p41_contract(MODULE, duplicate),
        )
        drifted = copy.deepcopy(self.manifest)
        next(item for item in drifted["modules"] if item["id"] == "P41")[
            "guiding_question"
        ] = "Changed"
        self.assertTrue(
            any("guiding_question" in error for error in validate_p41_contract(MODULE, drifted))
        )

    def test_control_validation_rejects_malformed_and_resource_overruns(self):
        validate_controls()
        invalid_cases = (
            {"range_bin_count": True},
            {"range_bin_count": 31},
            {"range_bin_count": 129},
            {"pulse_count": True},
            {"pulse_count": 31},
            {"pulse_count": 129},
            {"target_trial_count": True},
            {"target_trial_count": 999},
            {"target_trial_count": 4097},
            {"broken_trial_count": True},
            {"broken_trial_count": 511},
            {"broken_trial_count": 4097},
            {"range_correlation": True},
            {"range_correlation": math.nan},
            {"range_correlation": -0.01},
            {"range_correlation": 1.0},
            {"slow_time_correlation": math.inf},
            {"target_average_snr_db": True},
            {"target_average_snr_db": -21},
            {"target_average_snr_db": 21},
            {"false_alarm_probability": True},
            {"false_alarm_probability": 0},
            {"false_alarm_probability": 0.5},
            {"integration_sweep": (1, 2, 4)},
            {"integration_sweep": (1, 2, 4, 4)},
            {"integration_sweep": (1, 2, True, 8)},
            {"integration_sweep": tuple(range(1, 10))},
            {"correlation_sweep": (0, 0.5, 0.85)},
            {"correlation_sweep": (0, 0.5, 0.5, 0.97)},
            {"correlation_sweep": (0, 0.5, True, 0.97)},
            {"correlation_sweep": (0, 0.5, 0.9, 0.97)},
            {"correlation_sweep": tuple(value / 10 for value in range(9))},
        )
        for controls in invalid_cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_clutter_profile_and_ar_equation_have_correct_limits(self):
        ranges = [0.25 + 0.05 * index for index in range(96)]
        profile = clutter_power_profile(ranges)
        self.assertAlmostEqual(profile[0], 25.1, places=12)
        self.assertAlmostEqual(profile[-1], 0.1625, places=12)
        self.assertTrue(all(right < left for left, right in zip(profile, profile[1:])))
        innovations = [1 + 0j, 2 - 1j, -1 + 2j, 0.5 - 0.25j]
        self.assertEqual(ar1_sequence(innovations, 0), innovations)
        correlated = ar1_sequence(innovations, 0.85)
        self.assertAlmostEqual(
            correlated[1].real,
            0.85 * innovations[0].real + math.sqrt(1 - 0.85**2) * innovations[1].real,
            places=14,
        )
        self.assertEqual(len(correlated), len(innovations))
        for malformed in ([], [True], [math.nan]):
            with self.assertRaises(ValueError):
                ar1_sequence(malformed, 0.85)
        with self.assertRaises(ValueError):
            clutter_power_profile([0.25, 0.20])

    def test_swerling_transforms_moments_update_rates_and_amplitude_mapping(self):
        seeded = random.Random(4101)
        exponential = [swerling_power("I", seeded.random()) for _ in range(100_000)]
        gamma_two = [
            swerling_power("III", seeded.random(), seeded.random())
            for _ in range(100_000)
        ]
        for samples, expected_variance in ((exponential, 1.0), (gamma_two, 0.5)):
            mean = sum(samples) / len(samples)
            variance = sum((value - mean) ** 2 for value in samples) / len(samples)
            self.assertAlmostEqual(mean, 1.0, delta=0.015)
            self.assertAlmostEqual(variance, expected_variance, delta=0.025)
            self.assertAlmostEqual(sum(value for value in samples) / len(samples), mean)
            amplitudes = [math.sqrt(value) for value in samples[:100]]
            self.assertTrue(all(math.isclose(amplitude**2, power) for amplitude, power in zip(amplitudes, samples)))
        slow_draw = swerling_power("I", 0.2)
        self.assertEqual([slow_draw] * 8, [slow_draw for _ in range(8)])
        fast_draws = [swerling_power("II", value) for value in (0.2, 0.3, 0.4, 0.5)]
        self.assertEqual(len(set(fast_draws)), 4)
        self.assertAlmostEqual(swerling_power("I", 0.2), swerling_power("II", 0.2))
        self.assertAlmostEqual(
            swerling_power("III", 0.2, 0.7),
            swerling_power("IV", 0.2, 0.7),
        )
        for malformed in (0, 1, math.nan, True):
            with self.assertRaises(ValueError):
                swerling_power("I", malformed)

    def test_clean_power_variability_separates_slow_and_fast_models(self):
        self.assertEqual(theoretical_clean_power_cv("steady", 32), 0)
        self.assertEqual(theoretical_clean_power_cv("I", 32), 1)
        self.assertAlmostEqual(theoretical_clean_power_cv("II", 32), 1 / math.sqrt(32))
        self.assertAlmostEqual(theoretical_clean_power_cv("III", 32), 1 / math.sqrt(2))
        self.assertAlmostEqual(theoretical_clean_power_cv("IV", 32), 1 / 8)
        self.assertEqual(theoretical_clean_power_cv("I", 1), theoretical_clean_power_cv("II", 1))
        self.assertEqual(theoretical_clean_power_cv("III", 1), theoretical_clean_power_cv("IV", 1))
        self.assertLess(theoretical_clean_power_cv("II", 64), theoretical_clean_power_cv("II", 4))
        self.assertEqual(theoretical_clean_power_cv("I", 64), theoretical_clean_power_cv("I", 4))
        with self.assertRaises(ValueError):
            theoretical_clean_power_cv("II", True)

    def test_equal_average_snr_has_model_dependent_threshold_crossing_stability(self):
        first = equal_snr_target_crossing_rates()
        second = equal_snr_target_crossing_rates()
        self.assertEqual(first, second)
        crossing_rates, noise_only_rate, clean_power_means = first
        self.assertAlmostEqual(noise_only_rate, 0.05, places=12)
        for mean_power in clean_power_means.values():
            self.assertAlmostEqual(mean_power, 10 ** (-3 / 10), delta=0.04)
        self.assertGreater(crossing_rates["II"], crossing_rates["I"] + 0.05)
        self.assertGreater(crossing_rates["IV"], crossing_rates["III"] + 0.025)
        self.assertGreater(
            max(crossing_rates.values()) - min(crossing_rates.values()),
            0.05,
        )

    def test_broken_global_threshold_is_range_biased_and_oracle_normalization_recovers(self):
        ranges = [0.25 + 0.05 * index for index in range(96)]
        local_means = [value + 1.0 for value in clutter_power_profile(ranges)]
        requested_pfa = 0.05
        global_mean = sum(local_means) / len(local_means)
        global_threshold = -global_mean * math.log(requested_pfa)
        broken_rates = [background_crossing_probability(global_threshold, value) for value in local_means]
        self.assertGreater(sum(broken_rates[:16]) / 16, 5 * (sum(broken_rates[-16:]) / 16))
        normalized_threshold = -math.log(requested_pfa)
        recovered_rates = [background_crossing_probability(normalized_threshold, 1.0) for _ in local_means]
        self.assertTrue(all(math.isclose(value, requested_pfa) for value in recovered_rates))
        with self.assertRaises(ValueError):
            background_crossing_probability(-1, 1)
        with self.assertRaises(ValueError):
            background_crossing_probability(1, 0)

    def test_source_is_deterministic_bounded_transparent_and_base_matlab(self):
        self.assertEqual(source_contract_errors(self.source), [])
        self.assertEqual(self.source.count("figure('Name'"), 6)
        for label in (
            "Range (km)",
            "Pulse index",
            "Mean power (amplitude^2)",
            "Normalized correlation",
            "Target power / average power",
            "Dwell-power coefficient of variation",
            "Target-present threshold crossings (%)",
            "Background threshold crossings (%)",
        ):
            self.assertIn(label, self.source)
        for opaque_or_toolbox_marker in (
            "phased.",
            "dsp.",
            "xcorr(",
            "corrcoef(",
            "gamrnd(",
            "exprnd(",
            "fitdist(",
            "awgn(",
            "rng(",
            "system(",
            "webread(",
            "urlread(",
            "fopen(",
            "parfor",
            "while true",
        ):
            self.assertNotIn(opaque_or_toolbox_marker, self.source)
        mutations = (
            self.source.replace("sqrt(1-range_correlation^2)", "1", 1),
            self.source.replace("sqrt(1-slow_time_correlation^2)", "1", 1),
            self.source.replace("sqrt(target_power(:, :, model_index))", "target_power(:, :, model_index)", 1),
            self.source.replace("repmat(swerling_i_dwell_power", "repmat(target_average_power", 1),
            self.source.replace("row_white = correlation_white_rows(pulse_index, :)", "row_white = randn(1, range_bin_count)", 1),
            self.source.replace(
                "broken_background_power./...\n    local_background_power",
                "broken_background_power./...\n    global_background_power",
                1,
            ),
            self.source.replace("assert(max_stored_numeric_values == 1200000)", "assert(max_stored_numeric_values > 0)", 1),
        )
        for mutated in mutations:
            with self.subTest(mutation=len(mutated)):
                self.assertTrue(source_contract_errors(mutated))

    def test_catalogs_and_isolated_tutor_entry_have_a_timeout(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("Project 41", root_readme)
        self.assertIn("Project 41", start_here)
        self.assertRegex(module_index, r"\| \[P41\].*\| implemented \|")
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
                [str(fixture / "bin/learn"), "start", "41"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=os.environ.copy(),
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("P41 — Model Ground Clutter and Swerling Targets", result.stdout)
            self.assertIn("status: implemented", result.stdout)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_default_tutor_entry_advances_from_completed_p40_without_state_loss(self):
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
            prior_completed = [f"P{number:02d}" for number in range(1, 41)]
            progress = fixture / ".learning/progress.json"
            progress.parent.mkdir()
            progress.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "current": "P40",
                        "completed": prior_completed,
                        "notes": {"P40": "preserve this note"},
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
            self.assertIn("P41 — Model Ground Clutter and Swerling Targets", result.stdout)
            state = json.loads(progress.read_text(encoding="utf-8"))
            self.assertEqual(state["current"], "P41")
            self.assertEqual(state["completed"], prior_completed)
            self.assertEqual(state["notes"], {"P40": "preserve this note"})

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
            "u_{p,r}=\\alpha",
            "g_{p,r}=\\beta",
            "P=-\\bar P\\log U",
            "Swerling I",
            "Swerling IV",
            "Limiting cases",
            "P42",
            "P43",
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
        for marker in ("Ctrl+C", "rollback", "private seed", "bounded", "oracle"):
            self.assertIn(marker.lower(), combined.lower())
        self.assertIn("not a CFAR", combined)

    def test_manifest_rollback_fixture_is_isolated_from_neighboring_module_identity(self):
        rolled_back = copy.deepcopy(self.manifest)
        entries_before = {
            entry["id"]: copy.deepcopy(entry)
            for entry in rolled_back["modules"]
            if entry["id"] in {"P40", "P42"}
        }
        next(entry for entry in rolled_back["modules"] if entry["id"] == "P41")[
            "status"
        ] = "scaffolded"
        entries_after = {
            entry["id"]: entry
            for entry in rolled_back["modules"]
            if entry["id"] in {"P40", "P42"}
        }
        self.assertEqual(entries_after, entries_before)
        self.assertTrue(
            any("status" in error for error in validate_p41_contract(MODULE, rolled_back))
        )

    def test_retained_evidence_has_claim_boundary_commands_and_rollback(self):
        evidence = ROOT / "docs/evidence/P41-2026-08-03.md"
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
            "P40",
            "P41",
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
