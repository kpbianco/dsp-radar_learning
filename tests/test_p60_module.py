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
MODULE = ROOT / "modules/60-use-an-imm-for-a-maneuvering-target"
QUESTION = "How can a tracker adapt when the target alternates between straight motion and maneuvers?"
EXPECTED_IDENTITY = {
    "number": 60,
    "id": "P60",
    "title": "Use an IMM for a Maneuvering Target",
    "guiding_question": QUESTION,
    "phase": 6,
    "phase_title": "Radar Tracking and Data Association",
    "slug": "use-an-imm-for-a-maneuvering-target",
    "folder": "modules/60-use-an-imm-for-a-maneuvering-target",
    "status": "implemented",
    "implementation_batch": "P60",
}
ARTIFACTS = ("README.md", "experiment.m", "lesson.md", "walkthrough.md", "checks.md")
MODULUS = 2_147_483_647
MULTIPLIER = 16_807
SOURCE_MARKERS = (
    "baseline_seed = 6007;",
    "position_noise_sigma_m = 10.0;",
    "steady_acceleration_sigma_mps2 = 0.35;",
    "maneuver_jerk_sigma_mps3 = 0.80;",
    "maneuver_acceleration_sweep_mps2 = [0.8 2.0 3.2];",
    "mode_stay_probability_sweep = [0.80 0.94 0.99];",
    "maximum_scans = 60;",
    "initial_state = [0; 20; 0; 0; 5; 0];",
    "straight_block = [1 dt 0; 0 1 0; 0 0 0];",
    "maneuver_block = [1 dt 0.5*dt^2; 0 1 dt; 0 0 1];",
    "measurement_matrix = [1 0 0 0 0 0; 0 0 0 1 0 0];",
    "predicted_mode_probability = transition_probability.'*",
    "mixing_probability = transition_probability(:,destination_model).*",
    "state_offset*state_offset.'",
    "scan_log_weight(model) = log(predicted_mode_probability(model)) +",
    "log(det(innovation_covariance))",
    "relative_weight = exp(scan_log_weight - maximum_log_weight);",
    "combined_state(:,scan) = updated_state*mode_probability(:,scan);",
    "kalman_gain = (predicted_covariance*measurement_matrix.') /",
    "joseph_factor = identity - kalman_gain*measurement_matrix;",
    "broken_transition_probability = eye(2);",
    "broken_initial_mode_probability = [1; 0];",
    "isequal(recovered_imm.combined_state,",
    "model_updates > c.maximum_model_updates",
    "total_random_values > c.maximum_total_random_values",
    "c.maximum_model_updates ~= 1500",
    "Reviewed resource ceilings are immutable.",
    "state = mod(multiplier*state, modulus);",
    "close(findall(0, 'Type', 'figure', 'Tag', 'P60'));",
    "likelihood also penalizes uncertainty volume",
)
FORBIDDEN_SOURCE_TOKENS = (
    "trackingIMM", "trackingKF", "trackingEKF", "trackerGNN",
    "radarTracker", "interactingMultipleModel", "rng(", "rand(",
    "randn(", "parfor", "timer(", "webread", "urlread", "system(",
    "fopen(", "save(", "inv(", "close all",
)


def finite_real(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integer(value: object) -> bool:
    return finite_real(value) and value == int(value)


def p60_source_contract_errors(source: object) -> list[str]:
    if not isinstance(source, str) or not source:
        return ["P60 source must be nonempty text"]
    errors = [f"missing source marker: {marker}" for marker in SOURCE_MARKERS if marker not in source]
    if source.count("figure('Name', 'P60 Figure") != 6:
        errors.append("P60 must create exactly six named figures")
    if source.count("'Tag', 'P60'") != 7:
        errors.append("P60 must tag six figures and one scoped cleanup")
    if source.count("state_offset*state_offset.'") != 2:
        errors.append("P60 must retain between-model spread in both covariance combinations")
    errors.extend(
        f"forbidden source token: {token}"
        for token in FORBIDDEN_SOURCE_TOKENS
        if token in source
    )
    return errors


def validate_p60_contract(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        return ["P60 manifest must contain a module list"]
    errors: list[str] = []
    if any(not isinstance(entry, dict) for entry in manifest["modules"]):
        errors.append("every manifest module must be an object")
    matches = [
        entry for entry in manifest["modules"]
        if isinstance(entry, dict) and entry.get("id") == "P60"
    ]
    if len(matches) != 1:
        errors.append("P60 must have exactly one manifest entry")
    elif any(matches[0].get(key) != value for key, value in EXPECTED_IDENTITY.items()):
        errors.append("P60 manifest identity drift")
    module = root / EXPECTED_IDENTITY["folder"]
    for artifact in ARTIFACTS:
        path = module / artifact
        if not path.is_file():
            errors.append(f"P60 missing {artifact}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"P60 empty {artifact}")
    return errors


def validate_controls(**overrides: object) -> dict[str, object]:
    controls: dict[str, object] = {
        "seed": 6007,
        "scans": 60,
        "dt": 1.0,
        "sigma_position": 10.0,
        "maneuver_acceleration": 2.0,
        "sigma_steady_acceleration": 0.35,
        "sigma_maneuver_jerk": 0.80,
        "stay_probability": 0.94,
        "initial_probability": (0.85, 0.15),
        "acceleration_sweep": (0.8, 2.0, 3.2),
        "persistence_sweep": (0.80, 0.94, 0.99),
        "max_scans": 60,
        "max_cases": 5,
        "max_model_updates": 1500,
        "max_random_per_scene": 120,
        "max_random_total": 480,
        "max_figures": 6,
    }
    unknown = set(overrides) - set(controls)
    if unknown:
        raise ValueError(f"unknown controls: {sorted(unknown)}")
    controls.update(overrides)
    for name in (
        "seed", "scans", "max_scans", "max_cases", "max_model_updates",
        "max_random_per_scene", "max_random_total", "max_figures",
    ):
        if not integer(controls[name]):
            raise ValueError(f"{name} integer")
    if not 1 <= controls["seed"] < MODULUS:
        raise ValueError("seed range")
    if not 48 <= controls["scans"] <= controls["max_scans"]:
        raise ValueError("scan bound")
    for name in (
        "dt", "sigma_position", "maneuver_acceleration",
        "sigma_steady_acceleration", "sigma_maneuver_jerk",
    ):
        if not finite_real(controls[name]) or controls[name] <= 0:
            raise ValueError(f"{name} positive")
    if (
        not finite_real(controls["stay_probability"])
        or not 0.5 < controls["stay_probability"] < 1
    ):
        raise ValueError("stay probability")
    validate_probability(controls["initial_probability"])
    for name, baseline in (
        ("acceleration_sweep", controls["maneuver_acceleration"]),
        ("persistence_sweep", controls["stay_probability"]),
    ):
        values = controls[name]
        if (
            not isinstance(values, (tuple, list))
            or not values
            or len(values) > controls["max_cases"]
            or not all(finite_real(value) and value > 0 for value in values)
            or any(right <= left for left, right in zip(values, values[1:]))
            or list(values).count(baseline) != 1
        ):
            raise ValueError(f"{name} invalid")
    if any(not 0.5 < value < 1 for value in controls["persistence_sweep"]):
        raise ValueError("persistence sweep range")
    cases = len(controls["acceleration_sweep"]) + len(controls["persistence_sweep"])
    model_updates = controls["scans"] * (3 + 3 * cases + 2 + 2)
    random_per_scene = 2 * controls["scans"]
    random_total = random_per_scene * (1 + len(controls["acceleration_sweep"]))
    if (
        controls["max_scans"] != 60
        or controls["max_cases"] != 5
        or controls["max_model_updates"] != 1500
        or controls["max_random_per_scene"] != 120
        or controls["max_random_total"] != 480
        or controls["max_figures"] != 6
        or model_updates > controls["max_model_updates"]
        or random_per_scene > controls["max_random_per_scene"]
        or random_total > controls["max_random_total"]
    ):
        raise ValueError("resource ceiling")
    return controls


def validate_probability(probability: object) -> tuple[float, float]:
    if (
        not isinstance(probability, (tuple, list))
        or len(probability) != 2
        or not all(finite_real(value) and value >= 0 for value in probability)
        or abs(sum(probability) - 1) > 1e-12
    ):
        raise ValueError("probability")
    return float(probability[0]), float(probability[1])


def validate_transition(transition: object) -> tuple[tuple[float, float], tuple[float, float]]:
    if not isinstance(transition, (tuple, list)) or len(transition) != 2:
        raise ValueError("transition shape")
    rows: list[tuple[float, float]] = []
    for row in transition:
        if (
            not isinstance(row, (tuple, list))
            or len(row) != 2
            or not all(finite_real(value) and value >= 0 for value in row)
            or abs(sum(row) - 1) > 1e-12
        ):
            raise ValueError("transition row")
        rows.append((float(row[0]), float(row[1])))
    return rows[0], rows[1]


def private_gaussian(seed: object, count: object, maximum: int = 120) -> tuple[float, ...]:
    if not integer(seed) or not 1 <= seed < MODULUS:
        raise ValueError("seed")
    if not integer(count) or not 1 <= count <= maximum:
        raise ValueError("count")
    state = int(seed)
    values: list[float] = []
    for _ in range(math.ceil(int(count) / 2)):
        state = (MULTIPLIER * state) % MODULUS
        uniform_1 = (state + 0.5) / MODULUS
        state = (MULTIPLIER * state) % MODULUS
        uniform_2 = (state + 0.5) / MODULUS
        radius = math.sqrt(-2 * math.log(uniform_1))
        angle = 2 * math.pi * uniform_2
        values.extend((radius * math.cos(angle), radius * math.sin(angle)))
    return tuple(values[: int(count)])


def build_scene(
    seed: object = 6007,
    scans: object = 60,
    dt: object = 1.0,
    sigma_position: object = 10.0,
    maneuver_acceleration: object = 2.0,
) -> dict[str, object]:
    if not integer(scans) or not 48 <= scans <= 60:
        raise ValueError("scans")
    for name, value in (
        ("dt", dt), ("sigma_position", sigma_position),
        ("maneuver_acceleration", maneuver_acceleration),
    ):
        if not finite_real(value) or value <= 0:
            raise ValueError(name)
    noise = private_gaussian(seed, int(scans) * 2, maximum=120)
    state = [0.0, 20.0, 0.0, 0.0, 5.0, 0.0]
    truth: list[tuple[float, ...]] = []
    measurements: list[tuple[float, float]] = []
    maneuvers: list[bool] = []
    for scan in range(1, int(scans) + 1):
        acceleration = (0.0, 0.0)
        maneuver = False
        if 16 <= scan <= 25:
            acceleration = (0.0, float(maneuver_acceleration))
            maneuver = True
        elif 39 <= scan <= 48:
            acceleration = (-float(maneuver_acceleration), 0.0)
            maneuver = True
        state[2], state[5] = acceleration
        state[0] += float(dt) * state[1] + 0.5 * float(dt) ** 2 * acceleration[0]
        state[1] += float(dt) * acceleration[0]
        state[3] += float(dt) * state[4] + 0.5 * float(dt) ** 2 * acceleration[1]
        state[4] += float(dt) * acceleration[1]
        truth.append(tuple(state))
        cursor = 2 * (scan - 1)
        measurements.append((
            state[0] + float(sigma_position) * noise[cursor],
            state[3] + float(sigma_position) * noise[cursor + 1],
        ))
        maneuvers.append(maneuver)
    return {
        "truth": truth,
        "measurements": measurements,
        "maneuvers": maneuvers,
        "sigma_position": float(sigma_position),
        "dt": float(dt),
    }


Matrix = list[list[float]]
Vector = list[float]


def zeros(rows: int, columns: int) -> Matrix:
    return [[0.0 for _ in range(columns)] for _ in range(rows)]


def identity(size: int) -> Matrix:
    result = zeros(size, size)
    for index in range(size):
        result[index][index] = 1.0
    return result


def diagonal(values: list[float]) -> Matrix:
    result = zeros(len(values), len(values))
    for index, value in enumerate(values):
        result[index][index] = value
    return result


def transpose(matrix: Matrix) -> Matrix:
    return [list(row) for row in zip(*matrix)]


def matrix_add(left: Matrix, right: Matrix) -> Matrix:
    return [[a + b for a, b in zip(row_a, row_b)] for row_a, row_b in zip(left, right)]


def matrix_subtract(left: Matrix, right: Matrix) -> Matrix:
    return [[a - b for a, b in zip(row_a, row_b)] for row_a, row_b in zip(left, right)]


def matrix_scale(scale: float, matrix: Matrix) -> Matrix:
    return [[scale * value for value in row] for row in matrix]


def matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    columns = transpose(right)
    return [[sum(a * b for a, b in zip(row, column)) for column in columns] for row in left]


def matrix_vector(matrix: Matrix, vector: Vector) -> Vector:
    return [sum(a * b for a, b in zip(row, vector)) for row in matrix]


def vector_add(left: Vector, right: Vector) -> Vector:
    return [a + b for a, b in zip(left, right)]


def vector_subtract(left: Vector, right: Vector) -> Vector:
    return [a - b for a, b in zip(left, right)]


def vector_scale(scale: float, vector: Vector) -> Vector:
    return [scale * value for value in vector]


def outer(left: Vector, right: Vector) -> Matrix:
    return [[a * b for b in right] for a in left]


def inverse_2(matrix: Matrix) -> tuple[Matrix, float]:
    if len(matrix) != 2 or any(len(row) != 2 for row in matrix):
        raise ValueError("inverse shape")
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    if not math.isfinite(determinant) or determinant <= 1e-12:
        raise ValueError("singular innovation")
    return ([
        [matrix[1][1] / determinant, -matrix[0][1] / determinant],
        [-matrix[1][0] / determinant, matrix[0][0] / determinant],
    ], determinant)


def quadratic(vector: Vector, matrix: Matrix) -> float:
    mapped = matrix_vector(matrix, vector)
    return sum(a * b for a, b in zip(vector, mapped))


def model_bank(dt: float = 1.0, sigma_steady: float = 0.35, sigma_jerk: float = 0.80) -> tuple[list[Matrix], list[Matrix], Matrix]:
    straight_block = [[1.0, dt, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]]
    maneuver_block = [[1.0, dt, 0.5 * dt * dt], [0.0, 1.0, dt], [0.0, 0.0, 1.0]]
    models: list[Matrix] = []
    for block in (straight_block, maneuver_block):
        model = zeros(6, 6)
        for offset in (0, 3):
            for row in range(3):
                for column in range(3):
                    model[offset + row][offset + column] = block[row][column]
        models.append(model)
    process: list[Matrix] = []
    for shape, sigma in (
        ([0.5 * dt * dt, dt, 1.0], sigma_steady),
        ([dt ** 3 / 6, dt * dt / 2, dt], sigma_jerk),
    ):
        block = matrix_scale(sigma * sigma, outer(shape, shape))
        covariance = zeros(6, 6)
        for offset in (0, 3):
            for row in range(3):
                for column in range(3):
                    covariance[offset + row][offset + column] = block[row][column]
        process.append(covariance)
    measurement = [[1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]]
    return models, process, measurement


def kalman_step(
    state: Vector,
    covariance: Matrix,
    measurement: tuple[float, float],
    transition: Matrix,
    process: Matrix,
    observation: Matrix,
    measurement_covariance: Matrix,
) -> tuple[Vector, Matrix, float, float]:
    if len(state) != 6 or len(covariance) != 6 or any(len(row) != 6 for row in covariance):
        raise ValueError("filter shape")
    if len(measurement) != 2 or not all(finite_real(value) for value in measurement):
        raise ValueError("measurement")
    predicted_state = matrix_vector(transition, state)
    predicted_covariance = matrix_add(
        matrix_multiply(matrix_multiply(transition, covariance), transpose(transition)),
        process,
    )
    innovation = vector_subtract(list(measurement), matrix_vector(observation, predicted_state))
    innovation_covariance = matrix_add(
        matrix_multiply(matrix_multiply(observation, predicted_covariance), transpose(observation)),
        measurement_covariance,
    )
    inverse_innovation, determinant = inverse_2(innovation_covariance)
    gain = matrix_multiply(
        matrix_multiply(predicted_covariance, transpose(observation)),
        inverse_innovation,
    )
    updated_state = vector_add(predicted_state, matrix_vector(gain, innovation))
    joseph = matrix_subtract(identity(6), matrix_multiply(gain, observation))
    updated_covariance = matrix_add(
        matrix_multiply(matrix_multiply(joseph, predicted_covariance), transpose(joseph)),
        matrix_multiply(matrix_multiply(gain, measurement_covariance), transpose(gain)),
    )
    updated_covariance = matrix_scale(
        0.5, matrix_add(updated_covariance, transpose(updated_covariance))
    )
    nis = quadratic(innovation, inverse_innovation)
    log_likelihood = -0.5 * (2 * math.log(2 * math.pi) + math.log(determinant) + nis)
    if not math.isfinite(log_likelihood) or not math.isfinite(nis):
        raise ValueError("likelihood")
    return updated_state, updated_covariance, log_likelihood, nis


def validate_scene(scene: object) -> None:
    if not isinstance(scene, dict):
        raise ValueError("scene")
    required = {"truth", "measurements", "maneuvers", "sigma_position", "dt"}
    if not required <= set(scene):
        raise ValueError("scene keys")
    truth = scene["truth"]
    measurements = scene["measurements"]
    maneuvers = scene["maneuvers"]
    if (
        not isinstance(truth, list)
        or not 48 <= len(truth) <= 60
        or not isinstance(measurements, list)
        or not isinstance(maneuvers, list)
        or not (len(truth) == len(measurements) == len(maneuvers))
    ):
        raise ValueError("scene records")
    if not all(finite_real(scene[name]) and scene[name] > 0 for name in ("sigma_position", "dt")):
        raise ValueError("scene scales")
    for state, measurement, maneuver in zip(truth, measurements, maneuvers):
        if not isinstance(state, tuple) or len(state) != 6 or not all(finite_real(value) for value in state):
            raise ValueError("truth state")
        if not isinstance(measurement, tuple) or len(measurement) != 2 or not all(finite_real(value) for value in measurement):
            raise ValueError("report")
        if not isinstance(maneuver, bool):
            raise ValueError("regime")


def initial_filter(scene: dict[str, object]) -> tuple[Vector, Matrix]:
    return (
        [0.0, 20.0, 0.0, 0.0, 5.0, 0.0],
        diagonal([100.0, 100.0, 16.0, 100.0, 100.0, 16.0]),
    )


def run_fixed(scene: object) -> dict[str, object]:
    validate_scene(scene)
    models, processes, observation = model_bank(scene["dt"])
    measurement_covariance = matrix_scale(scene["sigma_position"] ** 2, identity(2))
    state, covariance = initial_filter(scene)
    states: list[Vector] = []
    for measurement in scene["measurements"]:
        state, covariance, _, _ = kalman_step(
            state, covariance, measurement, models[0], processes[0],
            observation, measurement_covariance,
        )
        states.append(state)
    return {"states": states}


def run_imm(
    scene: object,
    stay_probability: object = 0.94,
    initial_probability: object = (0.85, 0.15),
    transition_override: object | None = None,
) -> dict[str, object]:
    validate_scene(scene)
    if transition_override is None:
        if not finite_real(stay_probability) or not 0.5 < stay_probability < 1:
            raise ValueError("stay probability")
        transition = validate_transition((
            (stay_probability, 1 - stay_probability),
            (1 - stay_probability, stay_probability),
        ))
    else:
        transition = validate_transition(transition_override)
    mode_probability = list(validate_probability(initial_probability))
    models, processes, observation = model_bank(scene["dt"])
    measurement_covariance = matrix_scale(scene["sigma_position"] ** 2, identity(2))
    initial_state, initial_covariance = initial_filter(scene)
    states = [initial_state[:], initial_state[:]]
    covariances = [copy.deepcopy(initial_covariance), copy.deepcopy(initial_covariance)]
    combined_history: list[Vector] = []
    combined_covariance_history: list[Matrix] = []
    probability_history: list[tuple[float, float]] = []
    nis_history: list[tuple[float, float]] = []
    model_history: list[tuple[Vector, Vector]] = []
    model_covariance_history: list[tuple[Matrix, Matrix]] = []
    for measurement in scene["measurements"]:
        predicted_probability = [
            sum(transition[source][destination] * mode_probability[source] for source in range(2))
            for destination in range(2)
        ]
        mixed_states: list[Vector] = []
        mixed_covariances: list[Matrix] = []
        for destination in range(2):
            if predicted_probability[destination] > 0:
                mixing = [
                    transition[source][destination] * mode_probability[source]
                    / predicted_probability[destination]
                    for source in range(2)
                ]
            else:
                mixing = [0.0, 0.0]
                mixing[destination] = 1.0
            mixed_state = [sum(mixing[source] * states[source][index] for source in range(2)) for index in range(6)]
            mixed_covariance = zeros(6, 6)
            for source in range(2):
                offset = vector_subtract(states[source], mixed_state)
                contribution = matrix_add(covariances[source], outer(offset, offset))
                mixed_covariance = matrix_add(mixed_covariance, matrix_scale(mixing[source], contribution))
            mixed_states.append(mixed_state)
            mixed_covariances.append(mixed_covariance)
        updated_states: list[Vector] = []
        updated_covariances: list[Matrix] = []
        log_weights: list[float] = []
        scan_nis: list[float] = []
        for model in range(2):
            state, covariance, log_likelihood, nis = kalman_step(
                mixed_states[model], mixed_covariances[model], measurement,
                models[model], processes[model], observation, measurement_covariance,
            )
            updated_states.append(state)
            updated_covariances.append(covariance)
            log_weights.append(
                math.log(predicted_probability[model]) + log_likelihood
                if predicted_probability[model] > 0 else -math.inf
            )
            scan_nis.append(nis)
        finite_weights = [weight for weight in log_weights if math.isfinite(weight)]
        if not finite_weights:
            raise ValueError("probability collapse")
        maximum = max(finite_weights)
        relative = [math.exp(weight - maximum) if math.isfinite(weight) else 0.0 for weight in log_weights]
        mode_probability = [weight / sum(relative) for weight in relative]
        combined = [sum(mode_probability[model] * updated_states[model][index] for model in range(2)) for index in range(6)]
        combined_covariance = zeros(6, 6)
        for model in range(2):
            offset = vector_subtract(updated_states[model], combined)
            contribution = matrix_add(updated_covariances[model], outer(offset, offset))
            combined_covariance = matrix_add(
                combined_covariance,
                matrix_scale(mode_probability[model], contribution),
            )
        combined_covariance = matrix_scale(
            0.5, matrix_add(combined_covariance, transpose(combined_covariance))
        )
        states, covariances = updated_states, updated_covariances
        combined_history.append(combined)
        combined_covariance_history.append(combined_covariance)
        probability_history.append((mode_probability[0], mode_probability[1]))
        nis_history.append((scan_nis[0], scan_nis[1]))
        model_history.append((updated_states[0][:], updated_states[1][:]))
        model_covariance_history.append((
            copy.deepcopy(updated_covariances[0]),
            copy.deepcopy(updated_covariances[1]),
        ))
    return {
        "states": combined_history,
        "covariances": combined_covariance_history,
        "probabilities": probability_history,
        "nis": nis_history,
        "model_states": model_history,
        "model_covariances": model_covariance_history,
    }


def score(result: dict[str, object], scene: dict[str, object]) -> dict[str, float]:
    errors = [
        math.hypot(state[0] - truth[0], state[3] - truth[3])
        for state, truth in zip(result["states"], scene["truth"])
    ]
    maneuver_errors = [error for error, flag in zip(errors, scene["maneuvers"]) if flag]
    straight_errors = [error for error, flag in zip(errors, scene["maneuvers"]) if not flag]
    rms = lambda values: math.sqrt(sum(value * value for value in values) / len(values))
    return {
        "overall": rms(errors),
        "maneuver": rms(maneuver_errors),
        "straight": rms(straight_errors),
        "maximum": max(errors),
    }


class P60ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "curriculum/modules.json").read_text(encoding="utf-8"))
        cls.source = (MODULE / "experiment.m").read_text(encoding="utf-8")
        cls.readme = (MODULE / "README.md").read_text(encoding="utf-8")
        cls.lesson = (MODULE / "lesson.md").read_text(encoding="utf-8")
        cls.walkthrough = (MODULE / "walkthrough.md").read_text(encoding="utf-8")
        cls.checks = (MODULE / "checks.md").read_text(encoding="utf-8")

    def test_identity_artifacts_prerequisite_and_single_newline_are_permanent(self) -> None:
        self.assertEqual(validate_p60_contract(ROOT, self.manifest), [])
        p59 = next(entry for entry in self.manifest["modules"] if entry["id"] == "P59")
        self.assertEqual(p59["status"], "implemented")
        for artifact in ARTIFACTS:
            payload = (MODULE / artifact).read_bytes()
            self.assertNotIn(b"\r", payload)
            self.assertTrue(payload.endswith(b"\n"), artifact)
            self.assertFalse(payload.endswith(b"\n\n"), artifact)

    def test_contract_rejects_missing_empty_malformed_duplicate_and_identity_drift(self) -> None:
        for manifest in (None, [], {}, {"modules": None}, {"modules": "P60"}):
            self.assertTrue(validate_p60_contract(ROOT, manifest))
        malformed = copy.deepcopy(self.manifest)
        malformed["modules"].append("bad")
        self.assertIn("every manifest module must be an object", validate_p60_contract(ROOT, malformed))
        duplicate = copy.deepcopy(self.manifest)
        duplicate["modules"].append(copy.deepcopy(EXPECTED_IDENTITY))
        self.assertIn("exactly one", " ".join(validate_p60_contract(ROOT, duplicate)))
        compatible = copy.deepcopy(self.manifest)
        next(entry for entry in compatible["modules"] if entry["id"] == "P60")["future_metadata"] = True
        self.assertEqual(validate_p60_contract(ROOT, compatible), [])
        for key in EXPECTED_IDENTITY:
            changed = copy.deepcopy(self.manifest)
            entry = next(item for item in changed["modules"] if item["id"] == "P60")
            entry[key] = 999 if key in {"number", "phase"} else "drift"
            self.assertTrue(validate_p60_contract(ROOT, changed), key)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            shutil.copytree(MODULE, fixture / EXPECTED_IDENTITY["folder"])
            target = fixture / EXPECTED_IDENTITY["folder"] / "experiment.m"
            target.unlink()
            self.assertIn("P60 missing experiment.m", validate_p60_contract(fixture, self.manifest))
            target.write_text("", encoding="utf-8")
            self.assertIn("P60 empty experiment.m", validate_p60_contract(fixture, self.manifest))

    def test_controls_reject_malformed_nonfinite_and_resource_inputs(self) -> None:
        reviewed = validate_controls()
        self.assertEqual(reviewed["max_model_updates"], 1500)
        bad = (
            {"unknown": 1}, {"seed": 0}, {"seed": MODULUS}, {"scans": True},
            {"scans": 47}, {"scans": 61}, {"dt": 0},
            {"sigma_position": math.nan},
            {"maneuver_acceleration": -1}, {"sigma_steady_acceleration": 0},
            {"sigma_maneuver_jerk": complex(1, 1)}, {"stay_probability": 0.5},
            {"stay_probability": 1}, {"initial_probability": (1, 1)},
            {"initial_probability": (math.nan, 0)}, {"acceleration_sweep": ()},
            {"acceleration_sweep": (0.8, 2, 2)},
            {"acceleration_sweep": (0.8, 1.2, 3.2)},
            {"persistence_sweep": (0.4, 0.94, 0.99)},
            {"persistence_sweep": (0.8, 0.94, 0.95, 0.97, 0.98, 0.99)},
            {"max_scans": 61}, {"max_cases": 6}, {"max_model_updates": 1501},
            {"max_random_per_scene": 121}, {"max_random_total": 481},
            {"max_figures": 7},
        )
        for controls in bad:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_controls(**controls)

    def test_private_seeded_record_is_exact_repeatable_and_bounded(self) -> None:
        expected = (
            1.4847920069867884,
            1.9773858803013205,
            0.3100537935711487,
            0.26093500376378875,
        )
        first = private_gaussian(6007, 120)
        self.assertEqual(first, private_gaussian(6007, 120))
        for actual, wanted in zip(first, expected):
            self.assertAlmostEqual(actual, wanted, places=14)
        for args in ((0, 1), (MODULUS, 1), (True, 1), (6007, 0), (6007, 121), (6007, 2.5)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                private_gaussian(*args)

    def test_baseline_probability_rise_error_improvement_and_repeatability(self) -> None:
        scene = build_scene()
        reviewed = run_imm(scene)
        repeated = run_imm(scene)
        fixed = run_fixed(scene)
        imm_score = score(reviewed, scene)
        fixed_score = score(fixed, scene)
        maneuver_probability = [probability[1] for probability, flag in zip(reviewed["probabilities"], scene["maneuvers"]) if flag]
        straight_probability = [probability[1] for probability, flag in zip(reviewed["probabilities"], scene["maneuvers"]) if not flag]
        self.assertEqual(reviewed, repeated)
        self.assertAlmostEqual(sum(maneuver_probability) / len(maneuver_probability), 0.5175913403309493, places=12)
        self.assertAlmostEqual(sum(straight_probability) / len(straight_probability), 0.34768296548420047, places=12)
        self.assertAlmostEqual(imm_score["overall"], 9.194530412939912, places=11)
        self.assertLess(imm_score["overall"], fixed_score["overall"])
        self.assertLess(imm_score["maneuver"], fixed_score["maneuver"])
        self.assertTrue(all(abs(sum(probability) - 1) < 1e-14 for probability in reviewed["probabilities"]))

    def test_combined_covariance_includes_conditioned_uncertainty_and_model_disagreement(self) -> None:
        reviewed = run_imm(build_scene())
        spread_traces: list[float] = []
        for combined, combined_covariance, probabilities, model_states, model_covariances in zip(
            reviewed["states"],
            reviewed["covariances"],
            reviewed["probabilities"],
            reviewed["model_states"],
            reviewed["model_covariances"],
        ):
            within_model = zeros(6, 6)
            between_model = zeros(6, 6)
            for probability, state, covariance in zip(
                probabilities, model_states, model_covariances
            ):
                within_model = matrix_add(
                    within_model, matrix_scale(probability, covariance)
                )
                offset = vector_subtract(state, combined)
                between_model = matrix_add(
                    between_model, matrix_scale(probability, outer(offset, offset))
                )
            expected = matrix_add(within_model, between_model)
            for row in range(6):
                for column in range(6):
                    self.assertAlmostEqual(
                        combined_covariance[row][column],
                        expected[row][column],
                        places=11,
                    )
                    self.assertAlmostEqual(
                        combined_covariance[row][column],
                        combined_covariance[column][row],
                        places=12,
                    )
                self.assertGreaterEqual(
                    combined_covariance[row][row] + 1e-12,
                    within_model[row][row],
                )
            spread_traces.append(sum(between_model[index][index] for index in range(6)))
        self.assertGreater(max(spread_traces), 1.0)

    def test_acceleration_and_persistence_sweeps_show_reviewed_tradeoffs(self) -> None:
        acceleration_probability: list[float] = []
        for acceleration in (0.8, 2.0, 3.2):
            scene = build_scene(maneuver_acceleration=acceleration)
            reviewed = run_imm(scene)
            fixed = run_fixed(scene)
            self.assertLess(score(reviewed, scene)["maneuver"], score(fixed, scene)["maneuver"])
            acceleration_probability.append(sum(
                probability[1]
                for probability, flag in zip(reviewed["probabilities"], scene["maneuvers"])
                if flag
            ) / 20)
        self.assertTrue(all(right > left for left, right in zip(acceleration_probability, acceleration_probability[1:])))

        scene = build_scene()
        switches: list[int] = []
        for stay in (0.80, 0.94, 0.99):
            reviewed = run_imm(scene, stay_probability=stay)
            dominant = [int(probability[1] > probability[0]) for probability in reviewed["probabilities"]]
            switches.append(sum(left != right for left, right in zip(dominant, dominant[1:])))
        self.assertEqual(switches, [12, 6, 4])

    def test_zero_support_broken_case_and_exact_recovery(self) -> None:
        scene = build_scene()
        reviewed = run_imm(scene)
        broken = run_imm(
            scene,
            initial_probability=(1.0, 0.0),
            transition_override=((1.0, 0.0), (0.0, 1.0)),
        )
        recovered = run_imm(scene)
        fixed = run_fixed(scene)
        self.assertTrue(all(probability[1] == 0 for probability in broken["probabilities"]))
        self.assertEqual(broken["states"], fixed["states"])
        self.assertGreater(score(broken, scene)["overall"], score(reviewed, scene)["overall"])
        self.assertEqual(recovered["states"], reviewed["states"])
        self.assertEqual(recovered["probabilities"], reviewed["probabilities"])

    def test_positive_transition_reactivates_a_zero_probability_mode(self) -> None:
        scene = build_scene()
        reactivated = run_imm(scene, initial_probability=(1.0, 0.0))
        fixed = run_fixed(scene)
        self.assertGreater(reactivated["probabilities"][0][1], 0.0)
        self.assertGreater(max(probability[1] for probability in reactivated["probabilities"]), 0.5)
        self.assertNotEqual(reactivated["states"], fixed["states"])

    def test_oracle_rejects_malformed_shapes_nonfinite_probabilities_and_transitions(self) -> None:
        for options in (
            {"seed": 0}, {"seed": True}, {"scans": 47}, {"scans": 81},
            {"dt": 0}, {"sigma_position": math.inf},
            {"maneuver_acceleration": 0},
        ):
            with self.subTest(options=options), self.assertRaises(ValueError):
                build_scene(**options)
        scene = build_scene()
        for malformed in (None, [], {}, {"measurements": []}):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                run_imm(malformed)
        for probability in ((1, 1), (-0.1, 1.1), (math.nan, 0), (1,), "10"):
            with self.subTest(probability=probability), self.assertRaises(ValueError):
                run_imm(scene, initial_probability=probability)
        for transition in (
            ((1, 0),), ((1, 1), (0, 1)), ((1, -1), (0, 1)),
            ((math.nan, 0), (0, 1)), "identity",
        ):
            with self.subTest(transition=transition), self.assertRaises(ValueError):
                run_imm(scene, transition_override=transition)
        corrupt = copy.deepcopy(scene)
        corrupt["measurements"][0] = (math.nan, 0.0)
        with self.assertRaises(ValueError):
            run_imm(corrupt)
        corrupt = copy.deepcopy(scene)
        corrupt["truth"][0] = (0.0,)
        with self.assertRaises(ValueError):
            run_imm(corrupt)

    def test_source_is_explicit_seeded_bounded_and_mutation_sensitive(self) -> None:
        self.assertEqual(p60_source_contract_errors(self.source), [])
        for marker in (
            "position_noise_sigma_m = 10.0;",
            "straight_block = [1 dt 0; 0 1 0; 0 0 0];",
            "maneuver_block = [1 dt 0.5*dt^2; 0 1 dt; 0 0 1];",
            "measurement_matrix = [1 0 0 0 0 0; 0 0 0 1 0 0];",
            "state_offset*state_offset.'",
            "log(det(innovation_covariance))",
            "relative_weight = exp(scan_log_weight - maximum_log_weight);",
        ):
            with self.subTest(mutated_marker=marker):
                mutated = self.source.replace(marker, "", 1)
                self.assertTrue(p60_source_contract_errors(mutated))
        self.assertTrue(p60_source_contract_errors(self.source + "\ntrackingIMM"))

    def test_docs_cover_dependencies_models_limits_recovery_and_claims(self) -> None:
        combined = "\n".join((self.readme, self.lesson, self.walkthrough, self.checks))
        for marker in (
            QUESTION, "P55", "P59", "Base MATLAB R2016b", "F_CV", "F_CA",
            "mu_(i|j)", "NIS_j", "log L_j", "Limiting cases",
            "maneuver_acceleration_sweep_mps2", "mode_stay_probability_sweep",
            "zero initial", "unreachable", "exact", "Ctrl+C", "10-second",
            "rollback", "temporary repository", "Claim boundary",
            "hardware/HIL", "do not prove", "coordinated", "1,500",
            "NIS alone does not determine",
        ):
            self.assertIn(marker, combined)
        self.assertNotIn("TODO", combined)
        self.assertNotIn("smaller normalized surprise produces a larger likelihood", combined.lower())

    def test_public_catalogs_describe_p60_without_freezing_future_state(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("Project 60 follows P59", root_readme)
        self.assertIn("Project 60 follows P59", start_here)
        self.assertRegex(module_index, r"\| \[P60\].*\| implemented \| 6 \|")

    def test_cli_timeout_isolation_rollback_recovery_and_future_compatibility(self) -> None:
        cli = ROOT / "bin/learn"
        repository_state = ROOT / ".learning/progress.json"
        before = repository_state.read_bytes() if repository_state.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir(parents=True)
            shutil.copy2(cli, fixture / "bin/learn")
            manifest_path = fixture / "curriculum/modules.json"
            manifest_path.write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")
            for module in self.manifest["modules"]:
                target = fixture / module["folder"] / "README.md"
                target.parent.mkdir(parents=True)
                shutil.copy2(ROOT / module["folder"] / "README.md", target)
            env = os.environ.copy()
            env["HOME"] = temporary
            start = subprocess.run(
                [str(fixture / "bin/learn"), "start", "60"], cwd=fixture,
                text=True, capture_output=True, env=env, timeout=10,
            )
            self.assertEqual(start.returncode, 0, start.stderr)
            self.assertIn("Tutor entry", start.stdout)
            rolled_back = copy.deepcopy(self.manifest)
            p60 = next(entry for entry in rolled_back["modules"] if entry["id"] == "P60")
            p59_before = copy.deepcopy(next(entry for entry in rolled_back["modules"] if entry["id"] == "P59"))
            p61_before = copy.deepcopy(next(entry for entry in rolled_back["modules"] if entry["id"] == "P61"))
            p60["status"] = "scaffolded"
            manifest_path.write_text(json.dumps(rolled_back, indent=2) + "\n", encoding="utf-8")
            stopped = subprocess.run(
                [str(fixture / "bin/learn"), "start", "60"], cwd=fixture,
                text=True, capture_output=True, env=env, timeout=10,
            )
            self.assertEqual(stopped.returncode, 3)
            self.assertIn("awaits Portfolio batch P60", stopped.stdout)
            self.assertEqual(next(entry for entry in rolled_back["modules"] if entry["id"] == "P59"), p59_before)
            self.assertEqual(next(entry for entry in rolled_back["modules"] if entry["id"] == "P61"), p61_before)
            manifest_path.write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")
            recovered = subprocess.run(
                [str(fixture / "bin/learn"), "start", "60"], cwd=fixture,
                text=True, capture_output=True, env=env, timeout=10,
            )
            self.assertEqual(recovered.returncode, 0)
        after = repository_state.read_bytes() if repository_state.exists() else None
        self.assertEqual(after, before)

    def test_default_tutor_entry_advances_from_completed_p59_without_state_loss(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            (fixture / "bin").mkdir(parents=True)
            (fixture / "curriculum").mkdir(parents=True)
            (fixture / ".learning").mkdir(parents=True)
            shutil.copy2(ROOT / "bin/learn", fixture / "bin/learn")
            shutil.copy2(ROOT / "curriculum/modules.json", fixture / "curriculum/modules.json")
            for module in self.manifest["modules"]:
                target = fixture / module["folder"] / "README.md"
                target.parent.mkdir(parents=True)
                shutil.copy2(ROOT / module["folder"] / "README.md", target)
            state = {
                "schema_version": 1,
                "current": "P59",
                "completed": [f"P{number:02d}" for number in range(1, 60)],
                "notes": {"P59": "kept"},
            }
            (fixture / ".learning/progress.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            proc = subprocess.run(
                [str(fixture / "bin/learn"), "start"], cwd=fixture,
                text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("P60", proc.stdout)
            saved = json.loads((fixture / ".learning/progress.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["completed"], state["completed"])
            self.assertEqual(saved["notes"], state["notes"])
            self.assertEqual(saved["current"], "P60")

    def test_retained_evidence_has_commands_claim_boundary_and_single_newline(self) -> None:
        evidence = sorted((ROOT / "docs/evidence").glob("P60-*.md"))
        self.assertEqual(len(evidence), 1)
        payload = evidence[0].read_bytes()
        self.assertTrue(payload.endswith(b"\n"))
        self.assertFalse(payload.endswith(b"\n\n"))
        text = payload.decode("utf-8")
        for marker in (
            "# P60 Retained Evidence", "Acceptance map", "Exact commands and results",
            "Figure and metric inventory", "Changed and preserved invariants",
            "Residual risks", "Rollback and recovery", "Unperformed validation",
            "python3 scripts/validate_curriculum.py", "python3 -m unittest discover",
            "./scripts/agent-verify.sh", "MATLAB", "unavailable", "static",
            "hardware/HIL", "field", "real-time", "production",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
