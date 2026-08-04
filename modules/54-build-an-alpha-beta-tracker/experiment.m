%% P54: Build an Alpha-Beta Tracker
% Guiding question: How can a simple predictor smooth noisy position while following constant velocity?
% Dependencies: P53 supplies scalar target reports; P54 assumes one report is
% already associated to this track.
% P55 later replaces fixed gains with covariance-derived Kalman gains.
% This script uses base MATLAB only.

clear;
clc;

%% Visible controls and fixed resource ceilings
random_seed = 5401;
number_scans = 81;
scan_interval_s = 1;
initial_position_m = 1000;
initial_velocity_mps = 20;
changed_velocity_mps = 32;
velocity_change_scan = 41;
measurement_noise_std_m = 30;
dropout_scans = [18 19 20 66 67 68];
initial_velocity_estimate_mps = 0;
warmup_scans = 10;

alpha_gain = 0.35;
beta_gain = 0.08;
alpha_sweep = [0.10 0.35 0.85];
beta_sweep = [0.01 0.08 0.30];
broken_beta_gain = 0;

maximum_number_scans = 200;
maximum_sweep_cases = 5;
maximum_figure_count = 5;
maximum_tracker_steps = 1000;

integer_controls = [random_seed number_scans velocity_change_scan warmup_scans ...
    maximum_number_scans maximum_sweep_cases maximum_figure_count maximum_tracker_steps];
if ~isscalar(random_seed) || ~isscalar(number_scans) || ...
        ~isscalar(velocity_change_scan) || ~isscalar(warmup_scans) || ...
        ~isscalar(maximum_number_scans) || ~isscalar(maximum_sweep_cases) || ...
        ~isscalar(maximum_figure_count) || ~isscalar(maximum_tracker_steps) || ...
        islogical(random_seed) || islogical(number_scans) || ...
        islogical(velocity_change_scan) || islogical(warmup_scans) || ...
        islogical(maximum_number_scans) || islogical(maximum_sweep_cases) || ...
        islogical(maximum_figure_count) || islogical(maximum_tracker_steps) || ...
        ~isreal(integer_controls) || any(~isfinite(integer_controls)) || ...
        any(integer_controls ~= floor(integer_controls))
    error('P54:InvalidIntegerControl', ...
        'Seed, scan indices, and resource ceilings must be finite nonlogical integers.');
end
if random_seed ~= 5401 || number_scans ~= 81 || number_scans > maximum_number_scans
    error('P54:ReviewedScene', ...
        'The reviewed deterministic scene requires seed 5401 and 81 scans within its bound.');
end
if maximum_number_scans ~= 200 || maximum_sweep_cases ~= 5 || ...
        maximum_figure_count ~= 5 || maximum_tracker_steps ~= 1000
    error('P54:CeilingDrift', 'Fixed resource ceilings must not be increased or decreased.');
end
if warmup_scans < 0 || velocity_change_scan <= warmup_scans + 2 || ...
        velocity_change_scan >= number_scans - 2
    error('P54:InvalidManeuverScan', ...
        'Warm-up must be nonnegative and the velocity change must leave bounded comparison intervals.');
end

real_controls = [scan_interval_s initial_position_m initial_velocity_mps ...
    changed_velocity_mps measurement_noise_std_m initial_velocity_estimate_mps ...
    alpha_gain beta_gain broken_beta_gain];
if ~isscalar(scan_interval_s) || ~isscalar(initial_position_m) || ...
        ~isscalar(initial_velocity_mps) || ~isscalar(changed_velocity_mps) || ...
        ~isscalar(measurement_noise_std_m) || ...
        ~isscalar(initial_velocity_estimate_mps) || ~isscalar(alpha_gain) || ...
        ~isscalar(beta_gain) || ~isscalar(broken_beta_gain) || ...
        islogical(scan_interval_s) || islogical(initial_position_m) || ...
        islogical(initial_velocity_mps) || islogical(changed_velocity_mps) || ...
        islogical(measurement_noise_std_m) || ...
        islogical(initial_velocity_estimate_mps) || islogical(alpha_gain) || ...
        islogical(beta_gain) || islogical(broken_beta_gain) || ...
        ~isreal(real_controls) || any(~isfinite(real_controls))
    error('P54:InvalidRealControl', 'Physical and gain controls must be finite real nonlogical scalars.');
end
if scan_interval_s ~= 1 || scan_interval_s <= 0 || measurement_noise_std_m < 0
    error('P54:InvalidPhysicalControl', ...
        'The reviewed scan interval is one second and measurement noise cannot be negative.');
end
if initial_velocity_mps ~= 20 || changed_velocity_mps ~= 32 || ...
        changed_velocity_mps == initial_velocity_mps
    error('P54:InvalidVelocityScene', 'The reviewed scene requires a visible 20-to-32 m/s velocity change.');
end
validate_gain_pair(alpha_gain, beta_gain);
if broken_beta_gain ~= 0
    error('P54:BrokenCaseDrift', 'The reviewed broken limiting case requires beta equal to zero.');
end

if ~isrow(dropout_scans) || isempty(dropout_scans) || ...
        ~isreal(dropout_scans) || any(~isfinite(dropout_scans)) || ...
        islogical(dropout_scans) || any(dropout_scans ~= floor(dropout_scans)) || ...
        any(dropout_scans <= 1) || any(dropout_scans > number_scans) || ...
        any(diff(dropout_scans) <= 0)
    error('P54:InvalidDropouts', ...
        'Dropout scans must be unique increasing in-range integer indices after scan one.');
end
steady_window_scans = warmup_scans+1:velocity_change_scan-1;
if all(ismember(steady_window_scans, dropout_scans))
    error('P54:EmptySteadyWindow', ...
        'At least one report must remain in the steady comparison window.');
end
validate_gain_sweep(alpha_sweep, alpha_gain, beta_gain, true, maximum_sweep_cases);
validate_gain_sweep(beta_sweep, beta_gain, alpha_gain, false, maximum_sweep_cases);

tracker_run_count = 1 + numel(alpha_sweep) + numel(beta_sweep) + 1 + 1;
reviewed_tracker_steps = tracker_run_count*number_scans;
if reviewed_tracker_steps > maximum_tracker_steps
    error('P54:TrackerStepBound', 'Baseline, sweeps, broken case, and recovery exceed the tracker-step ceiling.');
end

% Validation above precedes random work, state allocation, and figure creation.
close(findobj(groot, 'Type', 'figure', 'Tag', 'P54'));

%% Deterministic scalar report scene
% Velocity is piecewise constant. The step deliberately violates the state
% carried by the tracker so lag is visible. Position remains continuous:
% interval k-1 to k uses velocity from scan k-1.
time_s = (0:number_scans-1)*scan_interval_s;
true_velocity_mps = initial_velocity_mps*ones(1, number_scans);
true_velocity_mps(velocity_change_scan:end) = changed_velocity_mps;
true_position_m = zeros(1, number_scans);
true_position_m(1) = initial_position_m;
for scan_index = 2:number_scans
    true_position_m(scan_index) = true_position_m(scan_index-1) + ...
        scan_interval_s*true_velocity_mps(scan_index-1);
end

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
measurement_position_m = true_position_m + ...
    measurement_noise_std_m*randn(private_stream, 1, number_scans);
measurement_available = true(1, number_scans);
measurement_available(dropout_scans) = false;
measurement_position_m(~measurement_available) = NaN;

figure('Name', 'P54 Figure 1: deterministic tracking scene', 'Tag', 'P54');
subplot(2, 1, 1);
plot(time_s, true_position_m, 'k-', 'LineWidth', 1.8);
hold on;
plot(time_s, measurement_position_m, '.', 'Color', [0.2 0.55 0.9], 'MarkerSize', 12);
plot(time_s(~measurement_available), true_position_m(~measurement_available), ...
    'x', 'Color', [0.45 0.45 0.45], 'LineWidth', 1.4, 'MarkerSize', 8);
xlabel('Time (s)');
ylabel('Position (m)');
title('Truth, noisy available reports, and dropout scans (gray x)');
legend('Truth', 'Available position report', 'Unavailable report', 'Location', 'northwest');
grid on;
subplot(2, 1, 2);
plot(time_s, true_velocity_mps, 'k-', 'LineWidth', 1.8);
xlabel('Time (s)');
ylabel('Velocity (m/s)');
title('Piecewise-constant truth: velocity change exposes model lag');
grid on;

%% Explicit baseline predict, innovation, and correction
% For an available report z(k):
% x_pred(k)=x_hat(k-1)+T*v_hat(k-1)
% r(k)=z(k)-x_pred(k)
% x_hat(k)=x_pred(k)+alpha*r(k)
% v_hat(k)=v_hat(k-1)+(beta/T)*r(k)
% For a dropout, x_hat=x_pred and v_hat=v_pred: no report is invented.
initial_position_estimate_m = measurement_position_m(1);
baseline = run_alpha_beta(measurement_position_m, measurement_available, ...
    scan_interval_s, alpha_gain, beta_gain, initial_position_estimate_m, ...
    initial_velocity_estimate_mps);

steady_mask = false(1, number_scans);
steady_mask(steady_window_scans) = true;
steady_received_mask = steady_mask & measurement_available;
evaluation_mask = false(1, number_scans);
evaluation_mask(warmup_scans+1:end) = true;
evaluation_received_mask = evaluation_mask & measurement_available;
maneuver_window = velocity_change_scan:min(number_scans, velocity_change_scan+14);

measurement_steady_rmse_m = root_mean_square(...
    measurement_position_m(steady_received_mask) - true_position_m(steady_received_mask));
baseline_steady_rmse_m = root_mean_square(...
    baseline.position_estimate_m(steady_received_mask) - true_position_m(steady_received_mask));
measurement_rmse_m = root_mean_square(...
    measurement_position_m(evaluation_received_mask) - true_position_m(evaluation_received_mask));
baseline_received_position_rmse_m = root_mean_square(...
    baseline.position_estimate_m(evaluation_received_mask) - true_position_m(evaluation_received_mask));
baseline_all_scan_position_rmse_m = root_mean_square(...
    baseline.position_estimate_m(evaluation_mask) - true_position_m(evaluation_mask));
baseline_velocity_rmse_mps = root_mean_square(...
    baseline.velocity_estimate_mps(evaluation_mask) - true_velocity_mps(evaluation_mask));
baseline_peak_post_change_absolute_error_m = max(abs(...
    true_position_m(maneuver_window) - baseline.position_estimate_m(maneuver_window)));
velocity_midpoint_mps = 0.5*(initial_velocity_mps + changed_velocity_mps);
baseline_midpoint_delay_scans = first_crossing_delay(...
    baseline.velocity_estimate_mps, velocity_change_scan, velocity_midpoint_mps);
baseline_dropout_max_error_m = max(abs(...
    baseline.position_estimate_m(dropout_scans) - true_position_m(dropout_scans)));

figure('Name', 'P54 Figure 2: baseline alpha-beta tracker', 'Tag', 'P54');
subplot(3, 1, 1);
plot(time_s, true_position_m, 'k-', 'LineWidth', 1.7);
hold on;
plot(time_s, measurement_position_m, '.', 'Color', [0.65 0.75 0.9]);
plot(time_s, baseline.position_prediction_m, '--', 'Color', [0.85 0.35 0.15]);
plot(time_s, baseline.position_estimate_m, 'b-', 'LineWidth', 1.3);
xlabel('Time (s)'); ylabel('Position (m)');
title(sprintf('Baseline: alpha=%.2f, beta=%.2f', alpha_gain, beta_gain));
legend('Truth', 'Report', 'One-step prediction', 'Corrected estimate', 'Location', 'northwest');
grid on;
subplot(3, 1, 2);
plot(time_s, true_velocity_mps, 'k-', 'LineWidth', 1.7);
hold on;
plot(time_s, baseline.velocity_estimate_mps, 'b-', 'LineWidth', 1.3);
xlabel('Time (s)'); ylabel('Velocity (m/s)');
title('Velocity changes only through beta/T times an available position innovation');
legend('Truth', 'Estimate', 'Location', 'southeast');
grid on;
subplot(3, 1, 3);
plot(time_s, baseline.innovation_m, 'Color', [0.45 0.1 0.65]);
hold on;
plot(time_s, true_position_m - baseline.position_estimate_m, 'k--');
plot(time_s, zeros(size(time_s)), 'k:');
xlabel('Time (s)'); ylabel('Position difference (m)');
title('Innovation has gaps during dropouts; it is not truth error');
legend('Innovation: report - prediction', 'Truth - estimate', 'Zero', 'Location', 'best');
grid on;

%% Sweep 1: change only alpha, keep beta and reports fixed
alpha_position_error_m = zeros(numel(alpha_sweep), number_scans);
alpha_prechange_received_rmse_m = zeros(1, numel(alpha_sweep));
alpha_peak_post_change_absolute_error_m = zeros(1, numel(alpha_sweep));
for sweep_index = 1:numel(alpha_sweep)
    sweep_track = run_alpha_beta(measurement_position_m, measurement_available, ...
        scan_interval_s, alpha_sweep(sweep_index), beta_gain, ...
        initial_position_estimate_m, initial_velocity_estimate_mps);
    alpha_position_error_m(sweep_index, :) = ...
        sweep_track.position_estimate_m - true_position_m;
    alpha_prechange_received_rmse_m(sweep_index) = root_mean_square(...
        alpha_position_error_m(sweep_index, steady_received_mask));
    alpha_peak_post_change_absolute_error_m(sweep_index) = ...
        max(abs(alpha_position_error_m(sweep_index, maneuver_window)));
end

figure('Name', 'P54 Figure 3: alpha sweep', 'Tag', 'P54');
subplot(2, 1, 1);
plot(time_s, alpha_position_error_m', 'LineWidth', 1.2);
hold on; plot(time_s, zeros(size(time_s)), 'k:');
xlabel('Time (s)'); ylabel('Estimate - truth (m)');
title(sprintf('Alpha sweep with beta fixed at %.2f', beta_gain));
alpha_labels = arrayfun(@(value) sprintf('alpha = %.2f', value), ...
    alpha_sweep, 'UniformOutput', false);
legend(alpha_labels, 'Location', 'best');
grid on;
subplot(2, 1, 2);
bar(alpha_sweep, [alpha_prechange_received_rmse_m; ...
    alpha_peak_post_change_absolute_error_m]');
xlabel('Alpha (dimensionless)'); ylabel('Position error metric (m)');
title('Pre-change smoothing and peak post-change absolute error');
legend('Pre-change received-scan RMSE', 'Peak post-change |error|', 'Location', 'best');
grid on;

%% Sweep 2: change only beta, keep alpha and reports fixed
beta_velocity_estimate_mps = zeros(numel(beta_sweep), number_scans);
beta_prechange_velocity_rmse_mps = zeros(1, numel(beta_sweep));
beta_midpoint_delay_scans = NaN(1, numel(beta_sweep));
for sweep_index = 1:numel(beta_sweep)
    sweep_track = run_alpha_beta(measurement_position_m, measurement_available, ...
        scan_interval_s, alpha_gain, beta_sweep(sweep_index), ...
        initial_position_estimate_m, initial_velocity_estimate_mps);
    beta_velocity_estimate_mps(sweep_index, :) = sweep_track.velocity_estimate_mps;
    beta_prechange_velocity_rmse_mps(sweep_index) = root_mean_square(...
        sweep_track.velocity_estimate_mps(steady_mask) - true_velocity_mps(steady_mask));
    beta_midpoint_delay_scans(sweep_index) = first_crossing_delay(...
        sweep_track.velocity_estimate_mps, velocity_change_scan, velocity_midpoint_mps);
end

figure('Name', 'P54 Figure 4: beta sweep', 'Tag', 'P54');
subplot(2, 1, 1);
plot(time_s, true_velocity_mps, 'k-', 'LineWidth', 1.8);
hold on;
plot(time_s, beta_velocity_estimate_mps', 'LineWidth', 1.1);
xlabel('Time (s)'); ylabel('Velocity (m/s)');
title(sprintf('Beta sweep with alpha fixed at %.2f', alpha_gain));
beta_labels = [{'Truth'} arrayfun(@(value) sprintf('beta = %.2f', value), ...
    beta_sweep, 'UniformOutput', false)];
legend(beta_labels, 'Location', 'southeast');
grid on;
subplot(2, 1, 2);
yyaxis left;
bar(beta_sweep, beta_prechange_velocity_rmse_mps, 0.45);
ylabel('Pre-change velocity RMSE after warm-up (m/s)');
yyaxis right;
plot(beta_sweep, beta_midpoint_delay_scans, 'ko-', 'LineWidth', 1.3);
ylabel('Midpoint crossing delay (scans)');
xlabel('Beta (dimensionless)');
title('Velocity noise and response delay must be read together');
grid on;

%% Broken case: beta zero prevents velocity learning; restore positive beta
broken = run_alpha_beta(measurement_position_m, measurement_available, ...
    scan_interval_s, alpha_gain, broken_beta_gain, initial_position_estimate_m, ...
    initial_velocity_estimate_mps);
recovered = run_alpha_beta(measurement_position_m, measurement_available, ...
    scan_interval_s, alpha_gain, beta_gain, initial_position_estimate_m, ...
    initial_velocity_estimate_mps);

broken_position_rmse_m = root_mean_square(...
    broken.position_estimate_m(evaluation_mask) - true_position_m(evaluation_mask));
broken_dropout_max_error_m = max(abs(...
    broken.position_estimate_m(dropout_scans) - true_position_m(dropout_scans)));
recovered_dropout_max_error_m = max(abs(...
    recovered.position_estimate_m(dropout_scans) - true_position_m(dropout_scans)));

figure('Name', 'P54 Figure 5: broken beta-zero case and recovery', 'Tag', 'P54');
subplot(2, 1, 1);
plot(time_s, true_position_m - broken.position_estimate_m, 'r-', 'LineWidth', 1.3);
hold on;
plot(time_s, true_position_m - recovered.position_estimate_m, 'b-', 'LineWidth', 1.3);
plot(time_s, zeros(size(time_s)), 'k:');
xlabel('Time (s)'); ylabel('Truth - estimate (m)');
title('Broken beta=0 position lag versus recovered tracker');
legend('Broken: beta=0', 'Recovered: beta=0.08', 'Zero', 'Location', 'best');
grid on;
subplot(2, 1, 2);
plot(time_s, true_velocity_mps, 'k-', 'LineWidth', 1.8);
hold on;
plot(time_s, broken.velocity_estimate_mps, 'r--', 'LineWidth', 1.3);
plot(time_s, recovered.velocity_estimate_mps, 'b-', 'LineWidth', 1.3);
xlabel('Time (s)'); ylabel('Velocity (m/s)');
title('Positive beta restores velocity learning and dropout coasting');
legend('Truth', 'Broken velocity', 'Recovered velocity', 'Location', 'southeast');
grid on;

%% Reviewed-run assertions and retained workspace results
reviewed_run = random_seed == 5401 && number_scans == 81 && ...
    scan_interval_s == 1 && initial_position_m == 1000 && ...
    initial_velocity_mps == 20 && changed_velocity_mps == 32 && ...
    velocity_change_scan == 41 && measurement_noise_std_m == 30 && ...
    isequal(dropout_scans, [18 19 20 66 67 68]) && ...
    initial_velocity_estimate_mps == 0 && warmup_scans == 10 && ...
    alpha_gain == 0.35 && beta_gain == 0.08 && broken_beta_gain == 0 && ...
    isequal(alpha_sweep, [0.10 0.35 0.85]) && ...
    isequal(beta_sweep, [0.01 0.08 0.30]) && ...
    maximum_number_scans == 200 && maximum_sweep_cases == 5 && ...
    maximum_figure_count == 5 && maximum_tracker_steps == 1000;

if reviewed_run
    assert(all(isfinite(baseline.position_estimate_m)), ...
        'P54:NonfinitePosition', 'Baseline position must remain finite.');
    assert(all(isfinite(baseline.velocity_estimate_mps)), ...
        'P54:NonfiniteVelocity', 'Baseline velocity must remain finite.');
    assert(all(isnan(baseline.innovation_m(~measurement_available))), ...
        'P54:DropoutInnovation', 'A dropout must not fabricate an innovation.');
    assert(all(baseline.position_estimate_m(dropout_scans) == ...
        baseline.position_prediction_m(dropout_scans)), ...
        'P54:DropoutCorrection', 'Dropout state must equal prediction-only coast.');
    assert(baseline_steady_rmse_m < measurement_steady_rmse_m, ...
        'P54:SmoothingFailure', 'Reviewed baseline must smooth the steady received reports.');
    assert(all(broken.velocity_estimate_mps == initial_velocity_estimate_mps), ...
        'P54:BrokenCaseFailure', 'Beta zero must leave velocity at its initial value.');
    assert(broken_position_rmse_m > baseline_all_scan_position_rmse_m && ...
        broken_dropout_max_error_m > recovered_dropout_max_error_m, ...
        'P54:RecoveryFailure', 'Positive beta must improve reviewed motion tracking and dropout coast.');
end

results.random_seed = random_seed;
results.time_s = time_s;
results.true_position_m = true_position_m;
results.true_velocity_mps = true_velocity_mps;
results.measurement_position_m = measurement_position_m;
results.measurement_available = measurement_available;
results.baseline = baseline;
results.measurement_rmse_m = measurement_rmse_m;
results.baseline_received_position_rmse_m = baseline_received_position_rmse_m;
results.baseline_all_scan_position_rmse_m = baseline_all_scan_position_rmse_m;
results.measurement_steady_rmse_m = measurement_steady_rmse_m;
results.baseline_steady_rmse_m = baseline_steady_rmse_m;
results.baseline_velocity_rmse_mps = baseline_velocity_rmse_mps;
results.baseline_peak_post_change_absolute_error_m = ...
    baseline_peak_post_change_absolute_error_m;
results.baseline_midpoint_delay_scans = baseline_midpoint_delay_scans;
results.baseline_dropout_max_error_m = baseline_dropout_max_error_m;
results.alpha_sweep = alpha_sweep;
results.alpha_prechange_received_rmse_m = alpha_prechange_received_rmse_m;
results.alpha_peak_post_change_absolute_error_m = ...
    alpha_peak_post_change_absolute_error_m;
results.beta_sweep = beta_sweep;
results.beta_prechange_velocity_rmse_mps = beta_prechange_velocity_rmse_mps;
results.beta_midpoint_delay_scans = beta_midpoint_delay_scans;
results.broken_position_rmse_m = broken_position_rmse_m;
results.broken_dropout_max_error_m = broken_dropout_max_error_m;
results.recovered_dropout_max_error_m = recovered_dropout_max_error_m;
results.reviewed_tracker_steps = reviewed_tracker_steps;

fprintf('\nP54 alpha-beta tracker metrics (seed %d)\n', random_seed);
fprintf('Available-measurement RMSE after warm-up: %.2f m\n', measurement_rmse_m);
fprintf('Baseline received-scan position RMSE after warm-up: %.2f m\n', ...
    baseline_received_position_rmse_m);
fprintf('Baseline all-scan position RMSE after warm-up: %.2f m\n', ...
    baseline_all_scan_position_rmse_m);
fprintf('Steady received report / track RMSE: %.2f m / %.2f m\n', ...
    measurement_steady_rmse_m, baseline_steady_rmse_m);
fprintf('Baseline velocity RMSE after warm-up: %.2f m/s\n', baseline_velocity_rmse_mps);
fprintf('Peak post-change absolute position error (15 scans): %.2f m\n', ...
    baseline_peak_post_change_absolute_error_m);
fprintf('Velocity midpoint crossing delay: %.0f scans\n', baseline_midpoint_delay_scans);
fprintf('Baseline / broken dropout max error: %.2f m / %.2f m\n', ...
    baseline_dropout_max_error_m, broken_dropout_max_error_m);
fprintf('Broken / recovered position RMSE: %.2f m / %.2f m\n', ...
    broken_position_rmse_m, baseline_all_scan_position_rmse_m);

%% Local transparent operations
function track = run_alpha_beta(measurement_m, available, sample_interval_s, ...
        alpha, beta, initial_position_m, initial_velocity_mps)
    if ~isnumeric(measurement_m) || ~isreal(measurement_m) || ...
            islogical(measurement_m) || ~isrow(measurement_m) || ...
            isempty(measurement_m) || ...
            ~isrow(available) || numel(available) ~= numel(measurement_m) || ...
            ~islogical(available)
        error('P54:InvalidMeasurementShape', ...
            'Measurements and logical availability must be nonempty equal-length row vectors.');
    end
    if ~available(1) || any(~isfinite(measurement_m(available))) || ...
            any(~isnan(measurement_m(~available)))
        error('P54:InvalidMeasurementValues', ...
            'Available reports must be finite, missing reports NaN, and scan one available.');
    end
    state_controls = [sample_interval_s alpha beta initial_position_m initial_velocity_mps];
    if ~isscalar(sample_interval_s) || ~isscalar(alpha) || ~isscalar(beta) || ...
            ~isscalar(initial_position_m) || ~isscalar(initial_velocity_mps) || ...
            islogical(sample_interval_s) || islogical(alpha) || islogical(beta) || ...
            islogical(initial_position_m) || islogical(initial_velocity_mps) || ...
            ~isreal(state_controls) || any(~isfinite(state_controls)) || ...
            sample_interval_s <= 0
        error('P54:InvalidTrackerControl', 'Tracker controls must be finite real nonlogical scalars and T positive.');
    end
    if beta == 0
        if alpha <= 0 || alpha >= 2
            error('P54:InvalidBrokenGain', 'Beta-zero limiting case still requires 0 < alpha < 2.');
        end
    else
        validate_gain_pair(alpha, beta);
    end

    sample_count = numel(measurement_m);
    position_prediction_m = zeros(1, sample_count);
    velocity_prediction_mps = zeros(1, sample_count);
    innovation_m = NaN(1, sample_count);
    position_estimate_m = zeros(1, sample_count);
    velocity_estimate_mps = zeros(1, sample_count);

    position_prediction_m(1) = initial_position_m;
    velocity_prediction_mps(1) = initial_velocity_mps;
    position_estimate_m(1) = initial_position_m;
    velocity_estimate_mps(1) = initial_velocity_mps;
    innovation_m(1) = measurement_m(1) - position_prediction_m(1);

    for sample_index = 2:sample_count
        position_prediction_m(sample_index) = position_estimate_m(sample_index-1) + ...
            sample_interval_s*velocity_estimate_mps(sample_index-1);
        velocity_prediction_mps(sample_index) = velocity_estimate_mps(sample_index-1);
        if available(sample_index)
            innovation_m(sample_index) = measurement_m(sample_index) - ...
                position_prediction_m(sample_index);
            position_estimate_m(sample_index) = position_prediction_m(sample_index) + ...
                alpha*innovation_m(sample_index);
            velocity_estimate_mps(sample_index) = velocity_prediction_mps(sample_index) + ...
                (beta/sample_interval_s)*innovation_m(sample_index);
        else
            position_estimate_m(sample_index) = position_prediction_m(sample_index);
            velocity_estimate_mps(sample_index) = velocity_prediction_mps(sample_index);
        end
    end

    track.position_prediction_m = position_prediction_m;
    track.velocity_prediction_mps = velocity_prediction_mps;
    track.innovation_m = innovation_m;
    track.position_estimate_m = position_estimate_m;
    track.velocity_estimate_mps = velocity_estimate_mps;
end

function validate_gain_pair(alpha, beta)
    gains = [alpha beta];
    if ~isscalar(alpha) || ~isscalar(beta) || islogical(alpha) || islogical(beta) || ...
            ~isreal(gains) || any(~isfinite(gains)) || alpha <= 0 || alpha >= 2 || ...
            beta <= 0 || beta >= 4 - 2*alpha
        error('P54:InvalidGainPair', ...
            'Stable reviewed gains require 0 < alpha < 2 and 0 < beta < 4-2*alpha.');
    end
end

function validate_gain_sweep(sweep, baseline, fixed_gain, alpha_is_swept, maximum_cases)
    if ~isrow(sweep) || numel(sweep) < 3 || numel(sweep) > maximum_cases || ...
            ~isreal(sweep) || any(~isfinite(sweep)) || islogical(sweep) || ...
            any(diff(sweep) <= 0) || ~any(sweep == baseline)
        error('P54:InvalidGainSweep', ...
            'Each gain sweep must be an increasing finite real row vector containing its baseline.');
    end
    for case_index = 1:numel(sweep)
        if alpha_is_swept
            validate_gain_pair(sweep(case_index), fixed_gain);
        else
            validate_gain_pair(fixed_gain, sweep(case_index));
        end
    end
end

function value = root_mean_square(samples)
    if isempty(samples) || ~isreal(samples) || any(~isfinite(samples))
        error('P54:InvalidMetricSamples', 'RMSE samples must be nonempty, finite, and real.');
    end
    value = sqrt(mean(samples.^2));
end

function delay_scans = first_crossing_delay(velocity_mps, change_scan, threshold_mps)
    crossing_offset = find(velocity_mps(change_scan:end) >= threshold_mps, 1, 'first');
    if isempty(crossing_offset)
        delay_scans = NaN;
    else
        delay_scans = crossing_offset - 1;
    end
end
