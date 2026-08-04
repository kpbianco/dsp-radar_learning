%% P55: Implement a Constant-Velocity Kalman Filter
% Guiding question: How do process noise and measurement noise determine trust in prediction versus measurement?
% Dependency: P54 supplies the visible constant-velocity prediction idea.
% P55 assumes one scalar position report is already associated to one track.
% This script uses base MATLAB only.

clear;
clc;

%% Visible controls and fixed resource ceilings
random_seed = 5501;
number_scans = 101;
scan_interval_s = 1;
initial_true_position_m = 1000;
initial_true_velocity_mps = 20;
actual_process_acceleration_std_mps2 = 0.8;
actual_measurement_std_m = 25;
initial_velocity_estimate_mps = 0;
initial_position_std_m = 25;
initial_velocity_std_mps = 15;
warmup_scans = 15;

assumed_process_acceleration_std_mps2 = 0.8;
assumed_measurement_std_m = 25;
process_std_sweep_mps2 = [0.10 0.80 3.20];
measurement_std_sweep_m = [5 25 100];
broken_process_std_mps2 = 0;
broken_measurement_std_m = 0.5;

maximum_number_scans = 200;
maximum_sweep_cases = 5;
maximum_figure_count = 5;
maximum_filter_steps = 1200;

integer_controls = [random_seed number_scans warmup_scans ...
    maximum_number_scans maximum_sweep_cases maximum_figure_count ...
    maximum_filter_steps];
if ~isscalar(random_seed) || ~isscalar(number_scans) || ...
        ~isscalar(warmup_scans) || ~isscalar(maximum_number_scans) || ...
        ~isscalar(maximum_sweep_cases) || ~isscalar(maximum_figure_count) || ...
        ~isscalar(maximum_filter_steps) || islogical(random_seed) || ...
        islogical(number_scans) || islogical(warmup_scans) || ...
        islogical(maximum_number_scans) || islogical(maximum_sweep_cases) || ...
        islogical(maximum_figure_count) || islogical(maximum_filter_steps) || ...
        ~isreal(integer_controls) || any(~isfinite(integer_controls)) || ...
        any(integer_controls ~= floor(integer_controls))
    error('P55:InvalidIntegerControl', ...
        'Seed, scan counts, warm-up, and resource ceilings must be finite nonlogical integers.');
end
if random_seed ~= 5501 || number_scans ~= 101 || ...
        number_scans > maximum_number_scans
    error('P55:ReviewedScene', ...
        'The reviewed deterministic scene requires seed 5501 and 101 scans within its bound.');
end
if maximum_number_scans ~= 200 || maximum_sweep_cases ~= 5 || ...
        maximum_figure_count ~= 5 || maximum_filter_steps ~= 1200
    error('P55:CeilingDrift', 'Fixed resource ceilings must not be changed.');
end
if warmup_scans < 1 || warmup_scans >= number_scans - 2
    error('P55:InvalidWarmup', 'Warm-up must leave at least three evaluation scans.');
end

real_controls = [scan_interval_s initial_true_position_m ...
    initial_true_velocity_mps actual_process_acceleration_std_mps2 ...
    actual_measurement_std_m initial_velocity_estimate_mps ...
    initial_position_std_m initial_velocity_std_mps ...
    assumed_process_acceleration_std_mps2 assumed_measurement_std_m ...
    broken_process_std_mps2 broken_measurement_std_m];
if ~isscalar(scan_interval_s) || ~isscalar(initial_true_position_m) || ...
        ~isscalar(initial_true_velocity_mps) || ...
        ~isscalar(actual_process_acceleration_std_mps2) || ...
        ~isscalar(actual_measurement_std_m) || ...
        ~isscalar(initial_velocity_estimate_mps) || ...
        ~isscalar(initial_position_std_m) || ...
        ~isscalar(initial_velocity_std_mps) || ...
        ~isscalar(assumed_process_acceleration_std_mps2) || ...
        ~isscalar(assumed_measurement_std_m) || ...
        ~isscalar(broken_process_std_mps2) || ...
        ~isscalar(broken_measurement_std_m) || ...
        islogical(scan_interval_s) || islogical(initial_true_position_m) || ...
        islogical(initial_true_velocity_mps) || ...
        islogical(actual_process_acceleration_std_mps2) || ...
        islogical(actual_measurement_std_m) || ...
        islogical(initial_velocity_estimate_mps) || ...
        islogical(initial_position_std_m) || ...
        islogical(initial_velocity_std_mps) || ...
        islogical(assumed_process_acceleration_std_mps2) || ...
        islogical(assumed_measurement_std_m) || ...
        islogical(broken_process_std_mps2) || ...
        islogical(broken_measurement_std_m) || ...
        ~isreal(real_controls) || any(~isfinite(real_controls))
    error('P55:InvalidRealControl', ...
        'Physical, uncertainty, and tuning controls must be finite real nonlogical scalars.');
end
if scan_interval_s ~= 1 || scan_interval_s <= 0 || ...
        actual_process_acceleration_std_mps2 < 0 || ...
        actual_measurement_std_m <= 0 || initial_position_std_m <= 0 || ...
        initial_velocity_std_mps <= 0 || ...
        assumed_process_acceleration_std_mps2 < 0 || ...
        assumed_measurement_std_m <= 0 || broken_process_std_mps2 ~= 0 || ...
        broken_measurement_std_m <= 0
    error('P55:InvalidPhysicalControl', ...
        'Time and standard deviations must have their reviewed finite positive or nonnegative domains.');
end
if actual_process_acceleration_std_mps2 ~= 0.8 || ...
        actual_measurement_std_m ~= 25 || ...
        assumed_process_acceleration_std_mps2 ~= 0.8 || ...
        assumed_measurement_std_m ~= 25 || broken_measurement_std_m ~= 0.5
    error('P55:TuningDrift', 'Restore the reviewed truth, baseline, and broken-case tuning.');
end
validate_std_sweep(process_std_sweep_mps2, ...
    assumed_process_acceleration_std_mps2, true, maximum_sweep_cases);
validate_std_sweep(measurement_std_sweep_m, assumed_measurement_std_m, ...
    false, maximum_sweep_cases);

filter_run_count = 1 + numel(process_std_sweep_mps2) + ...
    numel(measurement_std_sweep_m) + 2 + 1;
reviewed_filter_steps = filter_run_count*number_scans;
if reviewed_filter_steps > maximum_filter_steps
    error('P55:FilterStepBound', ...
        'Baseline, sweeps, failures, and recovery exceed the filter-step ceiling.');
end

% Validation above precedes random work, state-history allocation, and figures.
close(findobj(groot, 'Type', 'figure', 'Tag', 'P55'));

%% Deterministic nearly-constant-velocity scene
% x(k) = F*x(k-1) + G*a(k), where acceleration a(k) is unknown to the
% filter. z(k) = H*x(k) + n(k) is a scalar position report.
F = [1 scan_interval_s; 0 1];
G = [0.5*scan_interval_s^2; scan_interval_s];
H = [1 0];
time_s = (0:number_scans-1)*scan_interval_s;

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
actual_acceleration_mps2 = actual_process_acceleration_std_mps2* ...
    randn(private_stream, 1, number_scans-1);
true_state = zeros(2, number_scans);
true_state(:, 1) = [initial_true_position_m; initial_true_velocity_mps];
for scan_index = 2:number_scans
    true_state(:, scan_index) = F*true_state(:, scan_index-1) + ...
        G*actual_acceleration_mps2(scan_index-1);
end
measurement_noise_m = actual_measurement_std_m* ...
    randn(private_stream, 1, number_scans);
measurement_position_m = H*true_state + measurement_noise_m;

figure('Name', 'P55 Figure 1: deterministic tracking scene', 'Tag', 'P55');
subplot(2, 1, 1);
plot(time_s, true_state(1, :), 'k-', 'LineWidth', 1.7);
hold on;
plot(time_s, measurement_position_m, '.', 'Color', [0.25 0.55 0.9]);
xlabel('Time (s)'); ylabel('Position (m)');
title('Truth and noisy scalar position reports');
legend('Truth', 'Position report', 'Location', 'northwest'); grid on;
subplot(2, 1, 2);
plot(time_s, true_state(2, :), 'k-', 'LineWidth', 1.7);
hold on;
stairs(time_s(2:end), actual_acceleration_mps2, ...
    'Color', [0.8 0.3 0.15]);
xlabel('Time (s)'); ylabel('Velocity (m/s), acceleration (m/s^2)');
title('Unknown acceleration makes velocity wander around the CV prediction');
legend('True velocity', 'Interval acceleration', 'Location', 'best'); grid on;

%% Explicit baseline prediction, innovation, gain, and correction
initial_state_estimate = [measurement_position_m(1); initial_velocity_estimate_mps];
initial_covariance = diag([initial_position_std_m^2 initial_velocity_std_mps^2]);
baseline = run_cv_kalman(measurement_position_m, scan_interval_s, ...
    assumed_process_acceleration_std_mps2, assumed_measurement_std_m, ...
    initial_state_estimate, initial_covariance);

evaluation_indices = warmup_scans+1:number_scans;
baseline_position_error_m = baseline.state_estimate(1, :) - true_state(1, :);
baseline_velocity_error_mps = baseline.state_estimate(2, :) - true_state(2, :);
baseline_position_sigma_m = sqrt(baseline.posterior_variance(1, :));
baseline_velocity_sigma_mps = sqrt(baseline.posterior_variance(2, :));
baseline_innovation_sigma_m = sqrt(baseline.innovation_variance);

measurement_position_rmse_m = root_mean_square( ...
    measurement_position_m(evaluation_indices) - true_state(1, evaluation_indices));
baseline_position_rmse_m = root_mean_square( ...
    baseline_position_error_m(evaluation_indices));
baseline_velocity_rmse_mps = root_mean_square( ...
    baseline_velocity_error_mps(evaluation_indices));
baseline_position_coverage = mean(abs(baseline_position_error_m(evaluation_indices)) <= ...
    2*baseline_position_sigma_m(evaluation_indices));
baseline_velocity_coverage = mean(abs(baseline_velocity_error_mps(evaluation_indices)) <= ...
    2*baseline_velocity_sigma_mps(evaluation_indices));
baseline_innovation_coverage = mean(abs(baseline.innovation_m(evaluation_indices)) <= ...
    2*baseline_innovation_sigma_m(evaluation_indices));
baseline_mean_nis = mean((baseline.innovation_m(evaluation_indices).^2) ./ ...
    baseline.innovation_variance(evaluation_indices));
baseline_mean_position_gain = mean(baseline.kalman_gain(1, evaluation_indices));
baseline_mean_velocity_gain_per_s = mean(baseline.kalman_gain(2, evaluation_indices));

figure('Name', 'P55 Figure 2: baseline state and uncertainty', 'Tag', 'P55');
subplot(2, 1, 1);
plot(time_s, true_state(1, :), 'k-', 'LineWidth', 1.6); hold on;
plot(time_s, measurement_position_m, '.', 'Color', [0.75 0.82 0.92]);
plot(time_s, baseline.state_estimate(1, :), 'b-', 'LineWidth', 1.3);
plot(time_s, baseline.state_estimate(1, :) + 2*baseline_position_sigma_m, 'b--');
plot(time_s, baseline.state_estimate(1, :) - 2*baseline_position_sigma_m, 'b--');
xlabel('Time (s)'); ylabel('Position (m)');
title('Baseline corrected position and posterior two-sigma bounds');
legend('Truth', 'Report', 'Estimate', '+/- 2 sigma', 'Location', 'northwest'); grid on;
subplot(2, 1, 2);
plot(time_s, true_state(2, :), 'k-', 'LineWidth', 1.6); hold on;
plot(time_s, baseline.state_estimate(2, :), 'b-', 'LineWidth', 1.3);
plot(time_s, baseline.state_estimate(2, :) + 2*baseline_velocity_sigma_mps, 'b--');
plot(time_s, baseline.state_estimate(2, :) - 2*baseline_velocity_sigma_mps, 'b--');
xlabel('Time (s)'); ylabel('Velocity (m/s)');
title('Baseline corrected velocity and posterior two-sigma bounds');
legend('Truth', 'Estimate', '+/- 2 sigma', 'Location', 'best'); grid on;

figure('Name', 'P55 Figure 3: innovation and gain', 'Tag', 'P55');
subplot(3, 1, 1);
plot(time_s, baseline.innovation_m, 'Color', [0.45 0.1 0.65]); hold on;
plot(time_s, 2*baseline_innovation_sigma_m, 'k--');
plot(time_s, -2*baseline_innovation_sigma_m, 'k--');
plot(time_s, zeros(size(time_s)), 'k:');
xlabel('Time (s)'); ylabel('Innovation (m)');
title('Report minus predicted report with predicted two-sigma bounds');
legend('Innovation', '+/- 2 sqrt(S)', 'Location', 'best'); grid on;
subplot(3, 1, 2);
plot(time_s, baseline.kalman_gain(1, :), 'b-', 'LineWidth', 1.2);
xlabel('Time (s)'); ylabel('Position gain (dimensionless)');
title('Position correction per metre of innovation'); grid on;
subplot(3, 1, 3);
plot(time_s, baseline.kalman_gain(2, :), 'Color', [0.8 0.3 0.15], 'LineWidth', 1.2);
xlabel('Time (s)'); ylabel('Velocity gain (1/s)');
title('Velocity correction per metre of innovation'); grid on;

%% Sweep 1: change Q through assumed acceleration, keep R and data fixed
process_sweep_tracks = cell(1, numel(process_std_sweep_mps2));
process_velocity_error_mps = zeros(numel(process_std_sweep_mps2), number_scans);
process_position_rmse_m = zeros(1, numel(process_std_sweep_mps2));
process_position_coverage = zeros(1, numel(process_std_sweep_mps2));
process_mean_position_gain = zeros(1, numel(process_std_sweep_mps2));
for sweep_index = 1:numel(process_std_sweep_mps2)
    process_sweep_tracks{sweep_index} = run_cv_kalman( ...
        measurement_position_m, scan_interval_s, ...
        process_std_sweep_mps2(sweep_index), assumed_measurement_std_m, ...
        initial_state_estimate, initial_covariance);
    track = process_sweep_tracks{sweep_index};
    process_velocity_error_mps(sweep_index, :) = ...
        track.state_estimate(2, :) - true_state(2, :);
    process_position_rmse_m(sweep_index) = root_mean_square( ...
        track.state_estimate(1, evaluation_indices) - true_state(1, evaluation_indices));
    process_sigma_m = sqrt(track.posterior_variance(1, evaluation_indices));
    process_position_coverage(sweep_index) = mean(abs( ...
        track.state_estimate(1, evaluation_indices) - true_state(1, evaluation_indices)) <= ...
        2*process_sigma_m);
    process_mean_position_gain(sweep_index) = mean( ...
        track.kalman_gain(1, evaluation_indices));
end

figure('Name', 'P55 Figure 4: Q sweep', 'Tag', 'P55');
subplot(2, 1, 1);
plot(time_s, process_velocity_error_mps', 'LineWidth', 1.1); hold on;
plot(time_s, zeros(size(time_s)), 'k:');
xlabel('Time (s)'); ylabel('Velocity estimate - truth (m/s)');
title(sprintf('Q sweep via acceleration std; measurement std fixed at %.0f m', ...
    assumed_measurement_std_m));
process_labels = arrayfun(@(value) sprintf('sigma_a = %.2f m/s^2', value), ...
    process_std_sweep_mps2, 'UniformOutput', false);
legend(process_labels, 'Location', 'best'); grid on;
subplot(2, 1, 2);
plot(process_std_sweep_mps2, process_mean_position_gain, 'o-', 'LineWidth', 1.2); hold on;
plot(process_std_sweep_mps2, process_position_coverage, 's-', 'LineWidth', 1.2);
xlabel('Assumed acceleration std (m/s^2)'); ylabel('Gain or fraction');
title('Larger Q raises measurement trust; coverage diagnoses confidence');
legend('Mean position gain', 'Position two-sigma coverage', 'Location', 'best'); grid on;

%% Sweep 2: change R through assumed report noise, keep Q and data fixed
measurement_sweep_tracks = cell(1, numel(measurement_std_sweep_m));
measurement_position_error_m = zeros(numel(measurement_std_sweep_m), number_scans);
measurement_position_rmse_sweep_m = zeros(1, numel(measurement_std_sweep_m));
measurement_innovation_coverage = zeros(1, numel(measurement_std_sweep_m));
measurement_mean_position_gain = zeros(1, numel(measurement_std_sweep_m));
for sweep_index = 1:numel(measurement_std_sweep_m)
    measurement_sweep_tracks{sweep_index} = run_cv_kalman( ...
        measurement_position_m, scan_interval_s, ...
        assumed_process_acceleration_std_mps2, ...
        measurement_std_sweep_m(sweep_index), initial_state_estimate, ...
        initial_covariance);
    track = measurement_sweep_tracks{sweep_index};
    measurement_position_error_m(sweep_index, :) = ...
        track.state_estimate(1, :) - true_state(1, :);
    measurement_position_rmse_sweep_m(sweep_index) = root_mean_square( ...
        measurement_position_error_m(sweep_index, evaluation_indices));
    innovation_sigma_m = sqrt(track.innovation_variance(evaluation_indices));
    measurement_innovation_coverage(sweep_index) = mean(abs( ...
        track.innovation_m(evaluation_indices)) <= 2*innovation_sigma_m);
    measurement_mean_position_gain(sweep_index) = mean( ...
        track.kalman_gain(1, evaluation_indices));
end

figure('Name', 'P55 Figure 5: R sweep and broken mismatch recovery', 'Tag', 'P55');
subplot(3, 1, 1);
plot(time_s, measurement_position_error_m', 'LineWidth', 1.0); hold on;
plot(time_s, zeros(size(time_s)), 'k:');
xlabel('Time (s)'); ylabel('Position estimate - truth (m)');
title(sprintf('R sweep via report std; acceleration std fixed at %.2f m/s^2', ...
    assumed_process_acceleration_std_mps2));
measurement_labels = arrayfun(@(value) sprintf('sigma_z = %.1f m', value), ...
    measurement_std_sweep_m, 'UniformOutput', false);
legend(measurement_labels, 'Location', 'best'); grid on;
subplot(3, 1, 2);
plot(measurement_std_sweep_m, measurement_mean_position_gain, 'o-', 'LineWidth', 1.2); hold on;
plot(measurement_std_sweep_m, measurement_innovation_coverage, 's-', 'LineWidth', 1.2);
xlabel('Assumed measurement std (m)'); ylabel('Gain or fraction');
title('Larger R lowers report trust and widens innovation bounds');
legend('Mean position gain', 'Innovation two-sigma coverage', 'Location', 'best'); grid on;

%% Broken mismatches: underestimate Q or R; restore reviewed tuning
broken_q = run_cv_kalman(measurement_position_m, scan_interval_s, ...
    broken_process_std_mps2, assumed_measurement_std_m, ...
    initial_state_estimate, initial_covariance);
broken_r = run_cv_kalman(measurement_position_m, scan_interval_s, ...
    assumed_process_acceleration_std_mps2, broken_measurement_std_m, ...
    initial_state_estimate, initial_covariance);
recovered = run_cv_kalman(measurement_position_m, scan_interval_s, ...
    assumed_process_acceleration_std_mps2, assumed_measurement_std_m, ...
    initial_state_estimate, initial_covariance);

broken_q_position_sigma_m = sqrt(broken_q.posterior_variance(1, :));
broken_q_velocity_sigma_mps = sqrt(broken_q.posterior_variance(2, :));
broken_r_innovation_nis = (broken_r.innovation_m.^2) ./ broken_r.innovation_variance;
baseline_innovation_nis = (baseline.innovation_m.^2) ./ baseline.innovation_variance;
broken_q_position_coverage = mean(abs( ...
    broken_q.state_estimate(1, evaluation_indices) - true_state(1, evaluation_indices)) <= ...
    2*broken_q_position_sigma_m(evaluation_indices));
broken_q_velocity_coverage = mean(abs( ...
    broken_q.state_estimate(2, evaluation_indices) - true_state(2, evaluation_indices)) <= ...
    2*broken_q_velocity_sigma_mps(evaluation_indices));
broken_r_mean_nis = mean(broken_r_innovation_nis(evaluation_indices));
broken_q_velocity_rmse_mps = root_mean_square( ...
    broken_q.state_estimate(2, evaluation_indices) - true_state(2, evaluation_indices));

subplot(3, 1, 3);
plot(time_s, baseline_innovation_nis, 'b-', 'LineWidth', 1.0); hold on;
plot(time_s, broken_r_innovation_nis, 'r-', 'LineWidth', 1.0);
plot(time_s, ones(size(time_s)), 'k:');
xlabel('Time (s)'); ylabel('Normalized innovation squared');
title('Broken low-R confidence versus recovered reviewed tuning');
legend('Recovered/baseline', 'Broken R too small', 'Reference NIS = 1', ...
    'Location', 'best'); grid on;

%% Reviewed metrics, invariants, and retained workspace results
reviewed_run = random_seed == 5501 && number_scans == 101 && ...
    actual_process_acceleration_std_mps2 == 0.8 && ...
    actual_measurement_std_m == 25 && ...
    assumed_process_acceleration_std_mps2 == 0.8 && ...
    assumed_measurement_std_m == 25 && ...
    isequal(process_std_sweep_mps2, [0.10 0.80 3.20]) && ...
    isequal(measurement_std_sweep_m, [5 25 100]) && ...
    broken_process_std_mps2 == 0 && broken_measurement_std_m == 0.5 && ...
    reviewed_filter_steps == 1010;
assert(reviewed_run, 'P55:ReviewedRunDrift');
assert(all(isfinite(baseline.state_estimate(:))) && ...
    all(isfinite(baseline.posterior_variance(:))), 'P55:FiniteBaseline');
assert(all(baseline.posterior_variance(:) >= 0), 'P55:NegativeVariance');
assert(baseline_position_coverage > 0.5 && ...
    baseline_velocity_coverage > 0.5 && baseline_innovation_coverage > 0.5, ...
    'P55:BaselineConsistency');
assert(broken_r_mean_nis > baseline_mean_nis, 'P55:BrokenRNotVisible');
assert(max(abs(recovered.state_estimate(:) - baseline.state_estimate(:))) < 1e-10, ...
    'P55:RecoveryMismatch');

fprintf('\nP55 reviewed deterministic metrics (one seeded realization)\n');
fprintf('Measurement position RMSE after warm-up: %.3f m\n', measurement_position_rmse_m);
fprintf('Baseline position RMSE after warm-up: %.3f m\n', baseline_position_rmse_m);
fprintf('Baseline velocity RMSE after warm-up: %.3f m/s\n', baseline_velocity_rmse_mps);
fprintf('Baseline position two-sigma coverage: %.3f\n', baseline_position_coverage);
fprintf('Baseline velocity two-sigma coverage: %.3f\n', baseline_velocity_coverage);
fprintf('Baseline innovation two-sigma coverage: %.3f\n', baseline_innovation_coverage);
fprintf('Baseline mean normalized innovation squared: %.3f\n', baseline_mean_nis);
fprintf('Baseline mean gains: position %.4f, velocity %.4f 1/s\n', ...
    baseline_mean_position_gain, baseline_mean_velocity_gain_per_s);
fprintf(['Broken Q=0 position coverage: %.3f; velocity coverage: %.3f; ' ...
    'velocity RMSE: %.3f m/s\n'], broken_q_position_coverage, ...
    broken_q_velocity_coverage, broken_q_velocity_rmse_mps);
fprintf('Broken underestimated-R mean NIS: %.3f\n', broken_r_mean_nis);
fprintf('Filter runs: %d; total filter steps: %d; tagged figures: %d\n', ...
    filter_run_count, reviewed_filter_steps, maximum_figure_count);

results = struct();
results.random_seed = random_seed;
results.time_s = time_s;
results.true_state = true_state;
results.measurement_position_m = measurement_position_m;
results.baseline = baseline;
results.measurement_position_rmse_m = measurement_position_rmse_m;
results.baseline_position_rmse_m = baseline_position_rmse_m;
results.baseline_velocity_rmse_mps = baseline_velocity_rmse_mps;
results.baseline_position_coverage = baseline_position_coverage;
results.baseline_velocity_coverage = baseline_velocity_coverage;
results.baseline_innovation_coverage = baseline_innovation_coverage;
results.baseline_mean_nis = baseline_mean_nis;
results.process_std_sweep_mps2 = process_std_sweep_mps2;
results.process_position_rmse_m = process_position_rmse_m;
results.process_position_coverage = process_position_coverage;
results.process_mean_position_gain = process_mean_position_gain;
results.measurement_std_sweep_m = measurement_std_sweep_m;
results.measurement_position_rmse_sweep_m = measurement_position_rmse_sweep_m;
results.measurement_innovation_coverage = measurement_innovation_coverage;
results.measurement_mean_position_gain = measurement_mean_position_gain;
results.broken_q_position_coverage = broken_q_position_coverage;
results.broken_q_velocity_coverage = broken_q_velocity_coverage;
results.broken_q_velocity_rmse_mps = broken_q_velocity_rmse_mps;
results.broken_r_mean_nis = broken_r_mean_nis;
results.reviewed_filter_steps = reviewed_filter_steps;

%% Local functions keep the essential operation visible
function track = run_cv_kalman(measurement_m, sample_interval_s, ...
        process_acceleration_std_mps2, measurement_std_m, ...
        initial_state, initial_covariance)
    validate_filter_inputs(measurement_m, sample_interval_s, ...
        process_acceleration_std_mps2, measurement_std_m, ...
        initial_state, initial_covariance);

    sample_count = numel(measurement_m);
    F_local = [1 sample_interval_s; 0 1];
    G_local = [0.5*sample_interval_s^2; sample_interval_s];
    H_local = [1 0];
    Q_local = process_acceleration_std_mps2^2*(G_local*G_local');
    R_local = measurement_std_m^2;
    identity_state = eye(2);

    state_prediction = zeros(2, sample_count);
    state_estimate = zeros(2, sample_count);
    posterior_variance = zeros(2, sample_count);
    innovation_m = NaN(1, sample_count);
    innovation_variance = NaN(1, sample_count);
    kalman_gain = NaN(2, sample_count);

    state_prediction(:, 1) = initial_state;
    state_estimate(:, 1) = initial_state;
    covariance_estimate = initial_covariance;
    posterior_variance(:, 1) = diag(covariance_estimate);

    for sample_index = 2:sample_count
        state_prediction(:, sample_index) = F_local*state_estimate(:, sample_index-1);
        covariance_prediction = F_local*covariance_estimate*F_local' + Q_local;

        innovation_m(sample_index) = measurement_m(sample_index) - ...
            H_local*state_prediction(:, sample_index);
        innovation_variance(sample_index) = ...
            H_local*covariance_prediction*H_local' + R_local;
        kalman_gain(:, sample_index) = ...
            (covariance_prediction*H_local')/innovation_variance(sample_index);

        state_estimate(:, sample_index) = state_prediction(:, sample_index) + ...
            kalman_gain(:, sample_index)*innovation_m(sample_index);
        joseph_factor = identity_state - kalman_gain(:, sample_index)*H_local;
        covariance_estimate = joseph_factor*covariance_prediction*joseph_factor' + ...
            kalman_gain(:, sample_index)*R_local*kalman_gain(:, sample_index)';
        covariance_estimate = 0.5*(covariance_estimate + covariance_estimate');
        posterior_variance(:, sample_index) = diag(covariance_estimate);
    end

    track = struct();
    track.state_prediction = state_prediction;
    track.state_estimate = state_estimate;
    track.posterior_variance = posterior_variance;
    track.innovation_m = innovation_m;
    track.innovation_variance = innovation_variance;
    track.kalman_gain = kalman_gain;
end

function validate_filter_inputs(measurement_m, sample_interval_s, ...
        process_acceleration_std_mps2, measurement_std_m, ...
        initial_state, initial_covariance)
    if ~isnumeric(measurement_m) || ~isreal(measurement_m) || ...
            islogical(measurement_m) || ~isrow(measurement_m) || ...
            numel(measurement_m) < 2 || any(~isfinite(measurement_m))
        error('P55:InvalidMeasurement', ...
            'Measurement must be a finite real nonlogical row vector with at least two samples.');
    end
    scalar_inputs = [sample_interval_s process_acceleration_std_mps2 measurement_std_m];
    if ~isscalar(sample_interval_s) || ...
            ~isscalar(process_acceleration_std_mps2) || ...
            ~isscalar(measurement_std_m) || islogical(sample_interval_s) || ...
            islogical(process_acceleration_std_mps2) || ...
            islogical(measurement_std_m) || ~isreal(scalar_inputs) || ...
            any(~isfinite(scalar_inputs)) || sample_interval_s <= 0 || ...
            process_acceleration_std_mps2 < 0 || measurement_std_m <= 0
        error('P55:InvalidNoiseModel', ...
            'Interval and noise standard deviations must have valid finite scalar domains.');
    end
    if ~isnumeric(initial_state) || ~isreal(initial_state) || ...
            islogical(initial_state) || ~isequal(size(initial_state), [2 1]) || ...
            any(~isfinite(initial_state))
        error('P55:InvalidInitialState', 'Initial state must be a finite real 2-by-1 vector.');
    end
    if ~isnumeric(initial_covariance) || ~isreal(initial_covariance) || ...
            islogical(initial_covariance) || ...
            ~isequal(size(initial_covariance), [2 2]) || ...
            any(~isfinite(initial_covariance(:))) || ...
            max(max(abs(initial_covariance - initial_covariance'))) > 1e-12 || ...
            any(eig(initial_covariance) < -1e-12)
        error('P55:InvalidInitialCovariance', ...
            'Initial covariance must be finite, real, symmetric, and positive semidefinite.');
    end
end

function validate_std_sweep(values, baseline, allow_zero, maximum_cases)
    if ~isnumeric(values) || ~isreal(values) || islogical(values) || ...
            ~isrow(values) || numel(values) < 3 || ...
            numel(values) > maximum_cases || any(~isfinite(values)) || ...
            any(diff(values) <= 0) || ~any(values == baseline)
        error('P55:InvalidSweep', ...
            'Each sweep must be a finite increasing row with 3..maximum cases and its baseline.');
    end
    if (allow_zero && any(values < 0)) || (~allow_zero && any(values <= 0))
        error('P55:InvalidSweepDomain', 'Sweep standard deviations have an invalid domain.');
    end
end

function value = root_mean_square(samples)
    if isempty(samples) || ~isnumeric(samples) || ~isreal(samples) || ...
            islogical(samples) || any(~isfinite(samples(:)))
        error('P55:InvalidMetricInput', 'RMS input must be nonempty, finite, real, and numeric.');
    end
    value = sqrt(mean(samples(:).^2));
end
