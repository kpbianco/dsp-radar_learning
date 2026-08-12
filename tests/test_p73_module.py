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
MODULE = ROOT / "modules/73-build-a-tdm-mimo-virtual-array"
EVIDENCE = ROOT / "docs/evidence/P73-2026-08-12.md"
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
QUESTION = "How do multiple transmit and receive channels create more spatial samples?"

BASE_CONTROLS = {
    "seed": 7301,
    "c_mps": 3.0e8,
    "carrier_hz": 77.0e9,
    "rx_positions_lambda": [0.0, 0.5, 1.0, 1.5],
    "tx_positions_lambda": [0.0, 2.0],
    "target_angle_deg": 18.0,
    "target_velocity_mps": 0.0,
    "tdm_cycles": 64,
    "tx_slot_s": 40.0e-6,
    "snr_db": 20.0,
    "scan_angles_deg": [-60.0 + 0.1 * index for index in range(1201)],
    "separation_sweep_deg": [8.0, 16.0, 28.0],
    "velocity_sweep_mps": [-10.0, -5.0, 0.0, 5.0, 10.0],
    "broken_velocity_mps": 10.0,
    "resolution_dip_db": 0.25,
    "max_virtual_channels": 32,
    "max_tdm_cycles": 128,
    "max_scan_samples": 2001,
    "max_sweep_cases": 7,
    "max_private_values": 20000,
    "max_working_values": 500000,
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
            elif "TODO" in path.read_text(encoding="utf-8", errors="replace"):
                errors.append(f"TODO remains in {name}")
    return errors


def private_uniform(seed: int, count: int) -> list[float]:
    state = seed
    values: list[float] = []
    for _ in range(count):
        state = (16807 * state) % 2147483647
        values.append(state / 2147483647)
    return values


def private_complex_noise(seed: int, rows: int, columns: int) -> list[list[complex]]:
    uniforms = private_uniform(seed, 2 * rows * columns)
    flat: list[complex] = []
    for index in range(0, len(uniforms), 2):
        radius = math.sqrt(-2 * math.log(max(uniforms[index], float.fromhex("0x1p-1022"))))
        phase = 2 * math.pi * uniforms[index + 1]
        flat.append(
            complex(radius * math.cos(phase), radius * math.sin(phase))
            / math.sqrt(2)
        )
    # MATLAB reshape fills the first (row) dimension first.
    return [[flat[column * rows + row] for column in range(columns)] for row in range(rows)]


def virtual_geometry(
    tx_positions: list[float], rx_positions: list[float]
) -> tuple[list[float], list[int]]:
    positions: list[float] = []
    slots: list[int] = []
    for tx_slot, tx_position in enumerate(tx_positions):
        for rx_position in rx_positions:
            positions.append(tx_position + rx_position)
            slots.append(tx_slot)
    return positions, slots


def steering(positions: list[float], angle_deg: float) -> list[complex]:
    direction_cosine = math.sin(math.radians(angle_deg))
    return [cmath.exp(-2j * math.pi * position * direction_cosine) for position in positions]


def array_response_power(
    positions: list[float], scan_angles: list[float], source_angles: list[float]
) -> list[float]:
    count = len(positions)
    power = [0.0] * len(scan_angles)
    for source_angle in source_angles:
        source = steering(positions, source_angle)
        for scan_index, scan_angle in enumerate(scan_angles):
            candidate = steering(positions, scan_angle)
            output = sum(a.conjugate() * x for a, x in zip(candidate, source)) / count
            power[scan_index] += abs(output) ** 2
    return power


def half_power_width(scan_angles: list[float], power: list[float]) -> float:
    peak_index = max(range(len(power)), key=power.__getitem__)
    half = power[peak_index] / 2
    left = peak_index
    while left > 0 and power[left] >= half:
        left -= 1
    right = peak_index
    while right < len(power) - 1 and power[right] >= half:
        right += 1

    def crossing(i0: int, i1: int) -> float:
        p0, p1 = power[i0], power[i1]
        return scan_angles[i0] + (half - p0) * (
            scan_angles[i1] - scan_angles[i0]
        ) / (p1 - p0)

    return crossing(right - 1, right) - crossing(left, left + 1)


def pair_metrics(scan_angles: list[float], power: list[float]) -> tuple[float, bool]:
    center = min(range(len(scan_angles)), key=lambda index: abs(scan_angles[index]))
    left = max(range(center + 1), key=power.__getitem__)
    right = max(range(center, len(power)), key=power.__getitem__)
    smaller_peak = min(power[left], power[right])
    dip_db = max(0.0, 10 * math.log10(smaller_peak / power[center]))
    resolved = (
        dip_db >= BASE_CONTROLS["resolution_dip_db"]
        and scan_angles[left] < -0.25
        and scan_angles[right] > 0.25
    )
    return dip_db, resolved


def simulate_tdm_record(seed: int, velocity_mps: float) -> list[list[complex]]:
    positions, slots = virtual_geometry(
        BASE_CONTROLS["tx_positions_lambda"], BASE_CONTROLS["rx_positions_lambda"]
    )
    cycles = BASE_CONTROLS["tdm_cycles"]
    slot_s = BASE_CONTROLS["tx_slot_s"]
    cycle_s = len(BASE_CONTROLS["tx_positions_lambda"]) * slot_s
    wavelength_m = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
    doppler_hz = 2 * velocity_mps / wavelength_m
    noise = private_complex_noise(seed, len(positions), cycles)
    noise_rms = 10 ** (-BASE_CONTROLS["snr_db"] / 20)
    target = steering(positions, BASE_CONTROLS["target_angle_deg"])
    data: list[list[complex]] = []
    for channel, (spatial_sample, slot) in enumerate(zip(target, slots)):
        row: list[complex] = []
        for cycle in range(cycles):
            sample_time_s = cycle * cycle_s + slot * slot_s
            row.append(
                spatial_sample * cmath.exp(-2j * math.pi * doppler_hz * sample_time_s)
                + noise_rms * noise[channel][cycle]
            )
        data.append(row)
    return data


def estimate_doppler(data: list[list[complex]]) -> float:
    product = sum(
        row[index].conjugate() * row[index + 1]
        for row in data
        for index in range(len(row) - 1)
    )
    cycle_s = len(BASE_CONTROLS["tx_positions_lambda"]) * BASE_CONTROLS["tx_slot_s"]
    return -cmath.phase(product) / (2 * math.pi * cycle_s)


def compensate(data: list[list[complex]], doppler_hz: float) -> list[list[complex]]:
    _, slots = virtual_geometry(
        BASE_CONTROLS["tx_positions_lambda"], BASE_CONTROLS["rx_positions_lambda"]
    )
    slot_s = BASE_CONTROLS["tx_slot_s"]
    return [
        [sample * cmath.exp(2j * math.pi * doppler_hz * slots[row] * slot_s) for sample in values]
        for row, values in enumerate(data)
    ]


def scan_power(data: list[list[complex]], positions: list[float]) -> list[float]:
    cycles = len(data[0])
    result: list[float] = []
    for scan_angle in BASE_CONTROLS["scan_angles_deg"]:
        candidate = steering(positions, scan_angle)
        accumulated = 0.0
        for cycle in range(cycles):
            output = sum(
                weight.conjugate() * data[channel][cycle]
                for channel, weight in enumerate(candidate)
            ) / len(positions)
            accumulated += abs(output) ** 2
        result.append(accumulated / cycles)
    return result


def peak_angle(power: list[float]) -> float:
    return BASE_CONTROLS["scan_angles_deg"][max(range(len(power)), key=power.__getitem__)]


def control_errors(controls: dict) -> list[str]:
    errors: list[str] = []
    vector_names = (
        "rx_positions_lambda",
        "tx_positions_lambda",
        "scan_angles_deg",
        "separation_sweep_deg",
        "velocity_sweep_mps",
    )
    for name in vector_names:
        values = controls.get(name)
        if (
            not isinstance(values, list)
            or not values
            or any(isinstance(value, (list, tuple)) for value in values)
            or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values)
        ):
            errors.append(f"invalid row vector: {name}")
    if errors:
        return errors
    if controls["rx_positions_lambda"] != [0.0, 0.5, 1.0, 1.5]:
        errors.append("invalid RX geometry")
    if controls["tx_positions_lambda"] != [0.0, 2.0]:
        errors.append("invalid TX geometry")
    if controls["tdm_cycles"] < 2 or controls["tdm_cycles"] > controls["max_tdm_cycles"]:
        errors.append("invalid TDM cycle count")
    if len(controls["scan_angles_deg"]) > controls["max_scan_samples"]:
        errors.append("scan grid exceeds ceiling")
    if len(controls["velocity_sweep_mps"]) > controls["max_sweep_cases"]:
        errors.append("velocity sweep exceeds ceiling")
    virtual_count = len(controls["rx_positions_lambda"]) * len(controls["tx_positions_lambda"])
    if virtual_count > controls["max_virtual_channels"]:
        errors.append("virtual channels exceed ceiling")
    if 2 * virtual_count * controls["tdm_cycles"] > controls["max_private_values"]:
        errors.append("private noise exceeds ceiling")
    wavelength_m = controls["c_mps"] / controls["carrier_hz"]
    cycle_s = len(controls["tx_positions_lambda"]) * controls["tx_slot_s"]
    maximum_speed = max(abs(value) for value in controls["velocity_sweep_mps"])
    if 2 * maximum_speed / wavelength_m >= 1 / (2 * cycle_s):
        errors.append("same-TX Doppler aliases")
    return errors


class P73ModuleTests(unittest.TestCase):
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
        (fixture / "curriculum/modules.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        for entry in manifest["modules"]:
            readme = fixture / entry["folder"] / "README.md"
            readme.parent.mkdir(parents=True)
            readme.write_text(f"# {entry['id']}\n", encoding="utf-8")
        return fixture

    def run_cli(self, fixture: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(fixture / "bin/learn"), *arguments],
            cwd=fixture,
            text=True,
            capture_output=True,
            timeout=3,
            check=False,
        )

    def test_artifacts_manifest_identity_and_prerequisite(self):
        self.assertEqual(artifact_errors(MODULE), [])
        entry = module_entry(self.data, "P73")
        self.assertEqual(entry["number"], 73)
        self.assertEqual(entry["title"], "Build a TDM-MIMO Virtual Array")
        self.assertEqual(entry["guiding_question"], QUESTION)
        self.assertEqual(entry["folder"], "modules/73-build-a-tdm-mimo-virtual-array")
        self.assertEqual(entry["implementation_batch"], "P73")
        self.assertEqual(entry["status"], "implemented")
        self.assertEqual(module_entry(self.data, "P72")["status"], "implemented")
        for name, text in self.documents.items():
            with self.subTest(name=name):
                self.assertIn(QUESTION, text)

    def test_malformed_artifact_contract_rejects_missing_and_placeholder_content(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            for name in ARTIFACTS:
                (fixture / name).write_text("complete\n", encoding="utf-8")
            self.assertEqual(artifact_errors(fixture), [])
            (fixture / "lesson.md").unlink()
            self.assertIn("missing lesson.md", artifact_errors(fixture))
            (fixture / "lesson.md").write_text("TODO generic lesson\n", encoding="utf-8")
            self.assertIn("TODO remains in lesson.md", artifact_errors(fixture))

    def test_source_exposes_model_sweeps_failure_and_recovery(self):
        for marker in (
            "baseline_seed = 7301;",
            "validate_controls(controls);",
            "isrow(values)",
            "'P73:DopplerNyquist'",
            "'P73:ResourceCeilings'",
            "construct_virtual_positions",
            "positions_lambda(output_index) =",
            "tx_positions_lambda(tx_index_local)+",
            "rx_positions_lambda(rx_index_local);",
            "scan_steering = exp(-1j*2*pi*positions_lambda(:)*",
            "beam_outputs = weights'*data;",
            "separation_sweep_deg = [8 16 28];",
            "velocity_sweep_mps = [-10 -5 0 5 10];",
            "Intentionally broken case and same-data recovery",
            "estimate_same_tx_doppler",
            "compensate_tdm_slots",
            "isequaln(broken_data, broken_data_before_recovery)",
            "x_{virtual}=x_{TX}+x_{RX}",
            "Broadside-referenced scan angle (deg)",
            "Radial velocity (m/s, + approaching)",
        ):
            self.assertIn(marker, self.source)
        self.assertEqual(self.source.count("figure('Name', 'P73"), 5)
        self.assertNotIn("phased.", self.source.lower())
        self.assertNotIn("phasedarray", self.source.lower())
        self.assertNotIn("rng(", self.source.lower())

    def test_source_has_no_opaque_or_external_side_effect_paths(self):
        lowered = self.source.lower()
        for forbidden in (
            "phased.ula", "phased.tdm", "beamformer(", "musicdoa(",
            "parfor", "timer(", "webread(", "webwrite(", "urlread(",
            "fopen(", "save(", "writematrix(", "system(", "unix(", "dos(",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_control_contract_accepts_baseline_and_rejects_malformed_inputs(self):
        self.assertEqual(control_errors(copy.deepcopy(BASE_CONTROLS)), [])
        cases: list[tuple[str, dict]] = []
        nested = copy.deepcopy(BASE_CONTROLS)
        nested["velocity_sweep_mps"] = [[-10.0], [-5.0], [0.0], [5.0], [10.0]]
        cases.append(("column-shaped sweep", nested))
        nonfinite = copy.deepcopy(BASE_CONTROLS)
        nonfinite["scan_angles_deg"][10] = math.nan
        cases.append(("nonfinite scan", nonfinite))
        geometry = copy.deepcopy(BASE_CONTROLS)
        geometry["tx_positions_lambda"] = [0.0, 1.5]
        cases.append(("duplicate virtual geometry", geometry))
        cycles = copy.deepcopy(BASE_CONTROLS)
        cycles["tdm_cycles"] = 129
        cases.append(("cycle ceiling", cycles))
        scan = copy.deepcopy(BASE_CONTROLS)
        scan["scan_angles_deg"] = [float(index) for index in range(2002)]
        cases.append(("scan ceiling", scan))
        private = copy.deepcopy(BASE_CONTROLS)
        private["max_private_values"] = 100
        cases.append(("private resource ceiling", private))
        alias = copy.deepcopy(BASE_CONTROLS)
        alias["velocity_sweep_mps"] = [-20.0, 0.0, 20.0]
        cases.append(("Doppler Nyquist", alias))
        for label, controls in cases:
            with self.subTest(label=label):
                self.assertTrue(control_errors(controls))

    def test_virtual_geometry_and_beamwidth_oracle(self):
        positions, slots = virtual_geometry(
            BASE_CONTROLS["tx_positions_lambda"], BASE_CONTROLS["rx_positions_lambda"]
        )
        self.assertEqual(positions, [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5])
        self.assertEqual(slots, [0, 0, 0, 0, 1, 1, 1, 1])
        self.assertEqual(len(set(positions)), 8)
        rx_power = array_response_power(
            BASE_CONTROLS["rx_positions_lambda"],
            BASE_CONTROLS["scan_angles_deg"],
            [BASE_CONTROLS["target_angle_deg"]],
        )
        virtual_power = array_response_power(
            positions,
            BASE_CONTROLS["scan_angles_deg"],
            [BASE_CONTROLS["target_angle_deg"]],
        )
        rx_width = half_power_width(BASE_CONTROLS["scan_angles_deg"], rx_power)
        virtual_width = half_power_width(BASE_CONTROLS["scan_angles_deg"], virtual_power)
        self.assertAlmostEqual(rx_width, 27.75, delta=0.15)
        self.assertAlmostEqual(virtual_width, 13.47, delta=0.15)
        self.assertLess(virtual_width, 0.6 * rx_width)

    def test_separation_sweep_oracle_exposes_resolution_gain(self):
        positions, _ = virtual_geometry(
            BASE_CONTROLS["tx_positions_lambda"], BASE_CONTROLS["rx_positions_lambda"]
        )
        rx_resolved: list[bool] = []
        virtual_resolved: list[bool] = []
        rx_dips: list[float] = []
        virtual_dips: list[float] = []
        for separation in BASE_CONTROLS["separation_sweep_deg"]:
            source_angles = [-separation / 2, separation / 2]
            rx_power = array_response_power(
                BASE_CONTROLS["rx_positions_lambda"],
                BASE_CONTROLS["scan_angles_deg"],
                source_angles,
            )
            virtual_power = array_response_power(
                positions, BASE_CONTROLS["scan_angles_deg"], source_angles
            )
            rx_dip, rx_flag = pair_metrics(BASE_CONTROLS["scan_angles_deg"], rx_power)
            virtual_dip, virtual_flag = pair_metrics(
                BASE_CONTROLS["scan_angles_deg"], virtual_power
            )
            rx_dips.append(rx_dip)
            virtual_dips.append(virtual_dip)
            rx_resolved.append(rx_flag)
            virtual_resolved.append(virtual_flag)
        self.assertEqual(rx_resolved, [False, False, True])
        self.assertEqual(virtual_resolved, [False, True, True])
        self.assertGreater(virtual_dips[1], 1.8)
        self.assertLess(rx_dips[1], 0.01)

    def test_private_generator_is_repeatable_and_does_not_share_case_state(self):
        first = private_complex_noise(7301, 8, 64)
        repeated = private_complex_noise(7301, 8, 64)
        other = private_complex_noise(7401, 8, 64)
        self.assertEqual(first, repeated)
        self.assertNotEqual(first, other)
        self.assertNotEqual(first[0], first[1])
        self.assertAlmostEqual(private_uniform(7301, 1)[0], 0.057140321963066384)

    def test_velocity_sweep_changes_only_velocity_and_reuses_noise_record(self):
        self.assertRegex(
            self.source,
            r"for case_index = 1:velocity_case_count[\s\S]*?"
            r"case_data = simulate_tdm_record\(baseline_seed\+100,",
        )
        positions, slots = virtual_geometry(
            BASE_CONTROLS["tx_positions_lambda"], BASE_CONTROLS["rx_positions_lambda"]
        )
        wavelength_m = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
        cycle_s = len(BASE_CONTROLS["tx_positions_lambda"]) * BASE_CONTROLS["tx_slot_s"]
        reference_residual: list[list[complex]] | None = None
        for velocity_mps in BASE_CONTROLS["velocity_sweep_mps"]:
            data = simulate_tdm_record(7401, velocity_mps)
            doppler_hz = 2 * velocity_mps / wavelength_m
            spatial = steering(positions, BASE_CONTROLS["target_angle_deg"])
            residual = [
                [
                    sample
                    - spatial[channel]
                    * cmath.exp(
                        -2j
                        * math.pi
                        * doppler_hz
                        * (cycle * cycle_s + slots[channel] * BASE_CONTROLS["tx_slot_s"])
                    )
                    for cycle, sample in enumerate(row)
                ]
                for channel, row in enumerate(data)
            ]
            if reference_residual is None:
                reference_residual = residual
                continue
            for reference_row, actual_row in zip(reference_residual, residual):
                for reference, actual in zip(reference_row, actual_row):
                    self.assertAlmostEqual(actual.real, reference.real, places=14)
                    self.assertAlmostEqual(actual.imag, reference.imag, places=14)

    def test_full_motion_oracle_biases_and_recovers_unchanged_data(self):
        positions, _ = virtual_geometry(
            BASE_CONTROLS["tx_positions_lambda"], BASE_CONTROLS["rx_positions_lambda"]
        )
        wavelength_m = BASE_CONTROLS["c_mps"] / BASE_CONTROLS["carrier_hz"]
        naive_angles: list[float] = []
        recovered_angles: list[float] = []
        estimated_dopplers: list[float] = []
        broken_before: list[list[complex]] | None = None
        broken_after: list[list[complex]] | None = None
        for velocity in BASE_CONTROLS["velocity_sweep_mps"]:
            data = simulate_tdm_record(7401, velocity)
            immutable_copy = copy.deepcopy(data)
            estimate_hz = estimate_doppler(data)
            corrected = compensate(data, estimate_hz)
            naive_angles.append(peak_angle(scan_power(data, positions)))
            recovered_angles.append(peak_angle(scan_power(corrected, positions)))
            estimated_dopplers.append(estimate_hz)
            self.assertEqual(data, immutable_copy)
            if velocity == BASE_CONTROLS["broken_velocity_mps"]:
                broken_before = data
                broken_after = corrected
        truth_hz = [
            2 * velocity / wavelength_m
            for velocity in BASE_CONTROLS["velocity_sweep_mps"]
        ]
        self.assertLess(max(abs(a - b) for a, b in zip(estimated_dopplers, truth_hz)), 8)
        for actual, expected in zip(naive_angles, [13.3, 15.6, 18.0, 20.3, 22.8]):
            self.assertAlmostEqual(actual, expected, places=9)
        self.assertLess(
            max(abs(angle - BASE_CONTROLS["target_angle_deg"]) for angle in recovered_angles),
            0.3,
        )
        self.assertIsNotNone(broken_before)
        self.assertIsNotNone(broken_after)
        self.assertNotEqual(broken_before, broken_after)
        broken_doppler_hz = 2 * BASE_CONTROLS["broken_velocity_mps"] / wavelength_m
        phase_rad = -2 * math.pi * broken_doppler_hz * BASE_CONTROLS["tx_slot_s"]
        self.assertAlmostEqual(broken_doppler_hz, 5133.333333333333, places=9)
        self.assertAlmostEqual(phase_rad, -1.2901473830742085, places=12)

    def test_documents_are_concept_first_and_cover_limits(self):
        combined = "\n".join(self.documents.values()).lower()
        for marker in (
            "position sum", "x_virtual", "half-wavelength", "aperture",
            "beamwidth", "separation", "incoherent", "dechirped",
            "tx .* conj(rx)", "same-tx", "doppler", "velocity sweep",
            "broken case", "unchanged", "recovery", "duplicate", "gap",
            "nyquist", "zero velocity", "one tx", "2 pi", "cancellation",
            "rollback", "teach-back", "no optional toolbox",
        ):
            self.assertIn(marker, combined)
        self.assertGreaterEqual(self.documents["checks.md"].count("**Correct:**"), 45)

    def test_cli_timeout_cancellation_rollback_recovery_isolation_and_future_compatibility(self):
        compatible = copy.deepcopy(self.data)
        module_entry(compatible, "P74")["status"] = "implemented"
        module_entry(compatible, "P74")["future_metadata"] = {"allowed": True}
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.make_cli_fixture(Path(directory), compatible)
            started = self.run_cli(fixture, "start", "73")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn("P73", started.stdout)
            self.assertIn("status: implemented", started.stdout)

            rolled_back = copy.deepcopy(compatible)
            module_entry(rolled_back, "P73")["status"] = "scaffolded"
            (fixture / "curriculum/modules.json").write_text(
                json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8"
            )
            refused = self.run_cli(fixture, "start", "73")
            self.assertEqual(refused.returncode, 3)
            self.assertIn("awaits Portfolio batch P73", refused.stdout)

            (fixture / "curriculum/modules.json").write_text(
                json.dumps(compatible, indent=2) + "\n", encoding="utf-8"
            )
            recovered = self.run_cli(fixture, "start", "73")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)
        walkthrough = " ".join(self.documents["walkthrough.md"].lower().split())
        for marker in ("ctrl+c", "no worker", "no external persistent state", "rerun from the top", "rollback"):
            self.assertIn(marker, walkthrough)

    def test_compatibility_resources_catalogs_evidence_and_eof_policy(self):
        combined = "\n".join(self.documents.values()).lower()
        self.assertIn("matlab r2016b or newer", combined)
        self.assertIn("base matlab", combined)
        self.assertIn("500,000", combined)
        self.assertIn("five tagged figure", combined)
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 73 combines two explicit TX positions", root_readme)
        self.assertIn("Project 73 follows P72", start_here)
        self.assertRegex(module_index, r"\| \[P73\].*\| implemented \|")
        evidence = EVIDENCE.read_text(encoding="utf-8")
        for heading in (
            "## Claim boundary",
            "## Acceptance map",
            "## Deterministic simulated-oracle results",
            "## Figure and metric inventory",
            "## Exact commands and results",
            "## Changed and preserved invariants",
            "## Residual risks",
            "## Rollback",
            "## Unperformed validation",
        ):
            self.assertIn(heading, evidence)
        changed_text_paths = [
            *[MODULE / name for name in ARTIFACTS],
            ROOT / "curriculum/modules.json",
            ROOT / "README.md",
            ROOT / "START_HERE.md",
            ROOT / "modules/README.md",
            ROOT / "tests/test_p73_module.py",
            EVIDENCE,
        ]
        for path in changed_text_paths:
            with self.subTest(path=path):
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
