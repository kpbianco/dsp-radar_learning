%% P57: Gate and Associate Detections by Nearest Neighbor
% Guiding question: Which measurement should update which track?
% Dependency: P56 supplies predicted state/covariance and innovation geometry.
% This script uses base MATLAB only and performs one bounded radar scan.

clear;
clc;

%% Visible controls and fixed resource ceilings
random_seed = 5701;
number_tracks = 3;
number_target_reports = 3;
number_clutter_reports = 3;
scan_interval_s = 1;
process_acceleration_std_mps2 = 1;
measurement_std_m = 6;
gate_threshold_d2 = 5.991;
gate_threshold_sweep_d2 = [0.5 5.991 13.816];
covariance_scale_sweep = [0.25 1 4];
gate_ellipse_point_count = 73;

maximum_tracks = 8;
maximum_measurements = 12;
maximum_sweep_cases = 5;
maximum_figure_count = 6;
maximum_pair_slots = 200;
maximum_ellipse_points = 73;

integer_controls = [random_seed number_tracks number_target_reports ...
    number_clutter_reports gate_ellipse_point_count maximum_tracks ...
    maximum_measurements maximum_sweep_cases maximum_figure_count ...
    maximum_pair_slots maximum_ellipse_points];
if any(~isfinite(integer_controls)) || any(~isreal(integer_controls)) || ...
        any(integer_controls ~= floor(integer_controls)) || ...
        any(integer_controls < 1) || any(islogical(integer_controls))
    error('P57:InvalidIntegerControl', ...
        'Seeds, counts, and resource ceilings must be positive finite nonlogical integers.');
end
real_controls = [scan_interval_s process_acceleration_std_mps2 ...
    measurement_std_m gate_threshold_d2];
if any(~isfinite(real_controls)) || any(~isreal(real_controls)) || ...
        any(real_controls <= 0) || any(islogical(real_controls))
    error('P57:InvalidRealControl', ...
        'Intervals, noise scales, and gate threshold must be positive finite real values.');
end
if random_seed ~= 5701 || number_tracks ~= 3 || ...
        number_target_reports ~= number_tracks || number_clutter_reports ~= 3
    error('P57:ReviewedScene', ...
        'Restore the reviewed seed and three-track/three-clutter scene.');
end
if scan_interval_s ~= 1 || process_acceleration_std_mps2 ~= 1 || ...
        measurement_std_m ~= 6 || gate_threshold_d2 ~= 5.991
    error('P57:TuningDrift', ...
        'Restore the reviewed motion, measurement, and 95 percent gate controls.');
end
if maximum_tracks ~= 8 || maximum_measurements ~= 12 || ...
        maximum_sweep_cases ~= 5 || maximum_figure_count ~= 6 || ...
        maximum_pair_slots ~= 200 || maximum_ellipse_points ~= 73 || ...
        gate_ellipse_point_count ~= 73
    error('P57:CeilingDrift', 'Fixed resource ceilings must not be changed.');
end
validate_sweep(gate_threshold_sweep_d2, gate_threshold_d2, ...
    maximum_sweep_cases, 'gate threshold');
validate_sweep(covariance_scale_sweep, 1, ...
    maximum_sweep_cases, 'covariance scale');
if ~isequal(gate_threshold_sweep_d2, [0.5 5.991 13.816]) || ...
        ~isequal(covariance_scale_sweep, [0.25 1 4])
    error('P57:SweepDrift', 'Restore the two reviewed three-case sweeps.');
end

number_measurements = number_target_reports + number_clutter_reports;
association_run_count = 1 + numel(gate_threshold_sweep_d2) + ...
    numel(covariance_scale_sweep) + 1 + 1;
reviewed_pair_slots = association_run_count*number_tracks*number_measurements;
if number_tracks > maximum_tracks || number_measurements > maximum_measurements || ...
        reviewed_pair_slots > maximum_pair_slots
    error('P57:ResourceBound', ...
        'The reviewed association work exceeds a fixed resource ceiling.');
end

% Validation above precedes random work, pair-matrix allocation, and figures.
close(findobj(groot, 'Type', 'figure', 'Tag', 'P57'));

%% Predict every constant-velocity track into the common scan
% State ordering is [px; vx; py; vy]. The three predicted positions are
% intentionally separated; Track 1 has much more along-x than cross-y uncertainty.
F = [1 scan_interval_s 0 0; 0 1 0 0; ...
    0 0 1 scan_interval_s; 0 0 0 1];
G = [0.5*scan_interval_s^2 0; scan_interval_s 0; ...
    0 0.5*scan_interval_s^2; 0 scan_interval_s];
Q = process_acceleration_std_mps2^2*(G*G');
H = [1 0 0 0; 0 0 1 0];
R = measurement_std_m^2*eye(2);

prior_state = [-20 20 0 0; 178 22 48 2; 375 25 -94 -6]';
prior_covariance = zeros(4, 4, number_tracks);
prior_covariance(:, :, 1) = diag([45^2 5^2 7^2 2^2]);
prior_covariance(:, :, 2) = diag([12^2 4^2 12^2 4^2]);
prior_covariance(:, :, 3) = diag([14^2 4^2 10^2 3^2]);

predicted_state = zeros(4, number_tracks);
predicted_covariance = zeros(4, 4, number_tracks);
predicted_measurement = zeros(2, number_tracks);
innovation_covariance = zeros(2, 2, number_tracks);
for track_index = 1:number_tracks
    predicted_state(:, track_index) = F*prior_state(:, track_index);
    predicted_covariance(:, :, track_index) = ...
        F*prior_covariance(:, :, track_index)*F' + Q;
    predicted_measurement(:, track_index) = H*predicted_state(:, track_index);
    innovation_covariance(:, :, track_index) = ...
        H*predicted_covariance(:, :, track_index)*H' + R;
end

%% Form seeded noisy target reports and unlabeled clutter detections
% Truth labels are retained only for scoring the lesson; the associator never sees them.
% A small explicit Park-Miller/Box-Muller generator makes this Gaussian record
% reproducible in the independent host-language oracle without touching MATLAB's
% global random stream.
target_prediction_offset_m = [44 4 -6; 0 -5 7];
target_truth_position_m = predicted_measurement + target_prediction_offset_m;
measurement_noise_m = measurement_std_m*seeded_gaussian_noise( ...
    random_seed, 2, number_target_reports);
target_report_m = target_truth_position_m + measurement_noise_m;
clutter_report_m = [0 110 520; 30 140 40];

measurement_m = [target_report_m(:, 2) clutter_report_m(:, 1) ...
    target_report_m(:, 1) clutter_report_m(:, 2) ...
    target_report_m(:, 3) clutter_report_m(:, 3)];
measurement_truth_id = [2 0 1 0 3 0];
expected_measurement_for_track = [3 1 5];

figure('Name', 'P57 Figure 1: predicted tracks and detections', 'Tag', 'P57');
prior_handle = plot(prior_state(1, :), prior_state(3, :), 'ko', ...
    'MarkerFaceColor', [0.75 0.75 0.75]); hold on;
prediction_handle = plot(predicted_measurement(1, :), predicted_measurement(2, :), ...
    'bs', 'MarkerSize', 9, 'LineWidth', 1.4);
truth_handle = plot(target_truth_position_m(1, :), target_truth_position_m(2, :), ...
    'g+', 'MarkerSize', 10, 'LineWidth', 1.6);
target_handle = plot(target_report_m(1, :), target_report_m(2, :), ...
    'go', 'MarkerSize', 7);
clutter_handle = plot(clutter_report_m(1, :), clutter_report_m(2, :), ...
    'rx', 'MarkerSize', 9, 'LineWidth', 1.5);
for track_index = 1:number_tracks
    quiver(prior_state(1, track_index), prior_state(3, track_index), ...
        predicted_state(1, track_index) - prior_state(1, track_index), ...
        predicted_state(3, track_index) - prior_state(3, track_index), 0, ...
        'Color', [0.25 0.25 0.25], 'HandleVisibility', 'off');
    text(predicted_measurement(1, track_index) + 7, ...
        predicted_measurement(2, track_index) + 7, sprintf('T%d', track_index));
end
for measurement_index = 1:number_measurements
    text(measurement_m(1, measurement_index) + 5, ...
        measurement_m(2, measurement_index) - 8, sprintf('D%d', measurement_index));
end
axis equal; grid on;
xlabel('Cartesian x (m)'); ylabel('Cartesian y (m)');
title('Prediction precedes association; detections arrive without truth labels');
legend([prior_handle prediction_handle truth_handle target_handle clutter_handle], ...
    {'Prior track state', 'Predicted track', 'Target truth', ...
    'Noisy target report', 'Clutter report'}, 'Location', 'best');

%% Compute every residual and squared Mahalanobis distance, then gate
% nu_ij = z_j - H*x_i, S_i = H*P_i*H' + R,
% d2_ij = nu_ij'*(S_i\nu_ij). No explicit inverse is formed.
[residual_m, squared_mahalanobis_distance] = association_distances( ...
    predicted_measurement, innovation_covariance, measurement_m);
gate_mask = squared_mahalanobis_distance <= gate_threshold_d2;

figure('Name', 'P57 Figure 2: residuals and uncertainty gates', 'Tag', 'P57');
for track_index = 1:number_tracks
    subplot(1, number_tracks, track_index);
    gate_xy = covariance_ellipse(predicted_measurement(:, track_index), ...
        innovation_covariance(:, :, track_index), sqrt(gate_threshold_d2), ...
        gate_ellipse_point_count);
    plot(gate_xy(1, :), gate_xy(2, :), 'b-', 'LineWidth', 1.4); hold on;
    plot(predicted_measurement(1, track_index), ...
        predicted_measurement(2, track_index), 'bs', 'MarkerFaceColor', 'b');
    for measurement_index = 1:number_measurements
        if gate_mask(track_index, measurement_index)
            color = [0.1 0.6 0.2];
            style = '-';
        else
            color = [0.75 0.2 0.15];
            style = ':';
        end
        plot([predicted_measurement(1, track_index) measurement_m(1, measurement_index)], ...
            [predicted_measurement(2, track_index) measurement_m(2, measurement_index)], ...
            style, 'Color', color, 'HandleVisibility', 'off');
        plot(measurement_m(1, measurement_index), measurement_m(2, measurement_index), ...
            'ko', 'MarkerSize', 4, 'HandleVisibility', 'off');
        text(measurement_m(1, measurement_index) + 4, ...
            measurement_m(2, measurement_index) - 5, ...
            sprintf('D%d', measurement_index), 'FontSize', 8);
    end
    axis equal; grid on;
    xlabel('Cartesian x (m)'); ylabel('Cartesian y (m)');
    title(sprintf('Track %d: green residuals pass', track_index));
end

%% Greedily select the nearest remaining valid track-report pair
baseline_assignment = greedy_nearest_neighbor( ...
    squared_mahalanobis_distance, gate_mask);
baseline_assigned_count = sum(baseline_assignment > 0);
baseline_correct_count = sum(baseline_assignment == expected_measurement_for_track);
baseline_clutter_assignment_count = sum( ...
    measurement_truth_id(baseline_assignment(baseline_assignment > 0)) == 0);
baseline_unassigned_measurements = setdiff(1:number_measurements, ...
    baseline_assignment(baseline_assignment > 0));

figure('Name', 'P57 Figure 3: gated distance matrix and assignments', 'Tag', 'P57');
subplot(1, 2, 1);
imagesc(squared_mahalanobis_distance); colorbar;
xlabel('Detection index'); ylabel('Track index');
title('Squared Mahalanobis distance d^2');
set(gca, 'XTick', 1:number_measurements, 'YTick', 1:number_tracks);
hold on;
for track_index = 1:number_tracks
    for measurement_index = 1:number_measurements
        if gate_mask(track_index, measurement_index)
            marker = 'G';
        else
            marker = 'X';
        end
        text(measurement_index, track_index, ...
            sprintf('%.2f %s', squared_mahalanobis_distance( ...
            track_index, measurement_index), marker), ...
            'HorizontalAlignment', 'center', 'Color', 'w', 'FontWeight', 'bold');
    end
end
subplot(1, 2, 2);
plot(predicted_measurement(1, :), predicted_measurement(2, :), ...
    'bs', 'MarkerSize', 9, 'LineWidth', 1.4); hold on;
plot(measurement_m(1, :), measurement_m(2, :), 'ko', 'MarkerSize', 6);
for track_index = 1:number_tracks
    gate_xy = covariance_ellipse(predicted_measurement(:, track_index), ...
        innovation_covariance(:, :, track_index), sqrt(gate_threshold_d2), ...
        gate_ellipse_point_count);
    plot(gate_xy(1, :), gate_xy(2, :), 'b:', 'HandleVisibility', 'off');
    measurement_index = baseline_assignment(track_index);
    if measurement_index > 0
        plot([predicted_measurement(1, track_index) measurement_m(1, measurement_index)], ...
            [predicted_measurement(2, track_index) measurement_m(2, measurement_index)], ...
            'g-', 'LineWidth', 1.8, 'HandleVisibility', 'off');
    end
end
plot(measurement_m(1, baseline_unassigned_measurements), ...
    measurement_m(2, baseline_unassigned_measurements), 'rx', ...
    'MarkerSize', 10, 'LineWidth', 1.5);
axis equal; grid on;
xlabel('Cartesian x (m)'); ylabel('Cartesian y (m)');
title('One report per track; unused detections remain clutter');
legend('Predicted track', 'Detection', 'Rejected/unassigned', 'Location', 'best');

%% Sweep 1: change only the gate threshold on the same distances
gate_sweep_candidate_count = zeros(size(gate_threshold_sweep_d2));
gate_sweep_assigned_count = zeros(size(gate_threshold_sweep_d2));
gate_sweep_correct_count = zeros(size(gate_threshold_sweep_d2));
for sweep_index = 1:numel(gate_threshold_sweep_d2)
    sweep_gate_mask = squared_mahalanobis_distance <= ...
        gate_threshold_sweep_d2(sweep_index);
    sweep_assignment = greedy_nearest_neighbor( ...
        squared_mahalanobis_distance, sweep_gate_mask);
    gate_sweep_candidate_count(sweep_index) = sum(sweep_gate_mask(:));
    gate_sweep_assigned_count(sweep_index) = sum(sweep_assignment > 0);
    gate_sweep_correct_count(sweep_index) = sum( ...
        sweep_assignment == expected_measurement_for_track);
end

figure('Name', 'P57 Figure 4: gate-threshold sweep', 'Tag', 'P57');
plot(gate_threshold_sweep_d2, gate_sweep_candidate_count, ...
    'o-', 'LineWidth', 1.4); hold on;
plot(gate_threshold_sweep_d2, gate_sweep_assigned_count, ...
    's-', 'LineWidth', 1.4);
plot(gate_threshold_sweep_d2, gate_sweep_correct_count, ...
    'd-', 'LineWidth', 1.4);
xlabel('Gate threshold d^2 (dimensionless)'); ylabel('Count per scan');
title('Sweep 1: wider gates admit more candidates, not more evidence');
legend('Valid track-report pairs', 'Assigned tracks', 'Correct assignments', ...
    'Location', 'best'); grid on;

%% Sweep 2: change only predicted covariance scale on the same detections
covariance_sweep_candidate_count = zeros(size(covariance_scale_sweep));
covariance_sweep_track1_target_d2 = zeros(size(covariance_scale_sweep));
covariance_sweep_track1_clutter_d2 = zeros(size(covariance_scale_sweep));
covariance_sweep_track1_gate_area_m2 = zeros(size(covariance_scale_sweep));
for sweep_index = 1:numel(covariance_scale_sweep)
    scaled_innovation_covariance = zeros(2, 2, number_tracks);
    for track_index = 1:number_tracks
        scaled_innovation_covariance(:, :, track_index) = ...
            covariance_scale_sweep(sweep_index)* ...
            H*predicted_covariance(:, :, track_index)*H' + R;
    end
    [~, scaled_distance] = association_distances( ...
        predicted_measurement, scaled_innovation_covariance, measurement_m);
    scaled_gate_mask = scaled_distance <= gate_threshold_d2;
    greedy_nearest_neighbor(scaled_distance, scaled_gate_mask);
    covariance_sweep_candidate_count(sweep_index) = sum(scaled_gate_mask(:));
    covariance_sweep_track1_target_d2(sweep_index) = scaled_distance(1, 3);
    covariance_sweep_track1_clutter_d2(sweep_index) = scaled_distance(1, 2);
    covariance_sweep_track1_gate_area_m2(sweep_index) = ...
        pi*gate_threshold_d2*sqrt(det(scaled_innovation_covariance(:, :, 1)));
end

figure('Name', 'P57 Figure 5: covariance-scale sweep', 'Tag', 'P57');
subplot(1, 3, 1);
semilogx(covariance_scale_sweep, covariance_sweep_track1_target_d2, ...
    'o-', 'LineWidth', 1.4); hold on;
semilogx(covariance_scale_sweep, covariance_sweep_track1_clutter_d2, ...
    's-', 'LineWidth', 1.4);
plot(covariance_scale_sweep, gate_threshold_d2*ones(size(covariance_scale_sweep)), ...
    'r--', 'LineWidth', 1.1);
xlabel('Predicted covariance scale'); ylabel('Track 1 distance d^2 (dimensionless)');
title('Same residual, different uncertainty context');
legend('True report D3', 'Cross-ellipse clutter D2', 'Gate threshold', ...
    'Location', 'best'); grid on;
subplot(1, 3, 2);
semilogx(covariance_scale_sweep, covariance_sweep_track1_gate_area_m2, ...
    'o-', 'LineWidth', 1.4);
xlabel('Predicted covariance scale'); ylabel('Track 1 gate area (m^2)');
title('Broader prediction makes a larger physical gate'); grid on;
subplot(1, 3, 3);
semilogx(covariance_scale_sweep, covariance_sweep_candidate_count, ...
    's-', 'LineWidth', 1.4);
xlabel('Predicted covariance scale'); ylabel('Valid pair count per scan');
title('Broader gates admit more association candidates'); grid on;

%% Broken case: ignore uncertainty and gating, then recover exactly
euclidean_squared_distance_m2 = zeros(number_tracks, number_measurements);
for track_index = 1:number_tracks
    for measurement_index = 1:number_measurements
        current_residual_m = residual_m(:, track_index, measurement_index);
        euclidean_squared_distance_m2(track_index, measurement_index) = ...
            current_residual_m'*current_residual_m;
    end
end
broken_assignment = greedy_nearest_neighbor( ...
    euclidean_squared_distance_m2, true(size(euclidean_squared_distance_m2)));
broken_correct_count = sum(broken_assignment == expected_measurement_for_track);
broken_clutter_assignment_count = sum( ...
    measurement_truth_id(broken_assignment(broken_assignment > 0)) == 0);
recovered_assignment = greedy_nearest_neighbor( ...
    squared_mahalanobis_distance, gate_mask);
recovery_exact = isequal(recovered_assignment, baseline_assignment);

figure('Name', 'P57 Figure 6: broken Euclidean association and recovery', 'Tag', 'P57');
subplot(1, 2, 1);
plot_association(predicted_measurement, innovation_covariance, measurement_m, ...
    broken_assignment, gate_threshold_d2, gate_ellipse_point_count, [0.8 0.2 0.1]);
title('Broken: Euclidean nearest neighbor without a gate');
subplot(1, 2, 2);
plot_association(predicted_measurement, innovation_covariance, measurement_m, ...
    recovered_assignment, gate_threshold_d2, gate_ellipse_point_count, [0.1 0.6 0.2]);
title('Recovered: Mahalanobis gate plus one-to-one nearest pair');

%% Deterministic acceptance checks and retained workspace metrics
assert(isequal(baseline_assignment, expected_measurement_for_track), ...
    'P57:BaselineAssignment', 'The reviewed baseline association changed.');
assert(baseline_assigned_count == number_tracks && baseline_correct_count == number_tracks, ...
    'P57:BaselineCompleteness', 'Every separated target must associate correctly.');
assert(baseline_clutter_assignment_count == 0, ...
    'P57:ClutterRejection', 'Nominal gating must reject all clutter assignments.');
assert(all(measurement_truth_id(baseline_unassigned_measurements) == 0), ...
    'P57:UnassignedIdentity', 'Only clutter may remain unassigned in the baseline.');
assert(gate_sweep_candidate_count(end) > gate_sweep_candidate_count(2), ...
    'P57:GateSweep', 'The loose gate must admit more valid pairs than the baseline gate.');
assert(all(diff(covariance_sweep_track1_target_d2) < 0), ...
    'P57:CovarianceSweep', 'Target distance must fall as prediction covariance grows.');
assert(broken_assignment(1) == 2 && baseline_assignment(1) == 3 && ...
    broken_correct_count < baseline_correct_count && broken_clutter_assignment_count > 0, ...
    'P57:BrokenCase', 'Ungated Euclidean distance must expose the reviewed clutter error.');
assert(recovery_exact, 'P57:Recovery', ...
    'Restoring the gate and Mahalanobis metric must recover the baseline exactly.');
assert(reviewed_pair_slots == 162 && association_run_count == 9, ...
    'P57:ResourceAccounting', 'Reviewed pair-slot accounting changed.');

fprintf('P57 baseline assignments [track -> detection]: [%d %d %d]\n', ...
    baseline_assignment);
fprintf('P57 broken assignments [track -> detection]: [%d %d %d]\n', ...
    broken_assignment);
fprintf('Correct assignments: baseline %d/%d, broken %d/%d\n', ...
    baseline_correct_count, number_tracks, broken_correct_count, number_tracks);
fprintf('Clutter assignments: baseline %d, broken %d\n', ...
    baseline_clutter_assignment_count, broken_clutter_assignment_count);
fprintf('Nominal gate threshold: %.3f dimensionless; valid pairs: %d\n', ...
    gate_threshold_d2, sum(gate_mask(:)));
fprintf('Association passes: %d; reviewed track-report pair slots: %d\n', ...
    association_run_count, reviewed_pair_slots);
fprintf('Deterministic recovery exact: %d\n', recovery_exact);

results.random_seed = random_seed;
results.predicted_state = predicted_state;
results.predicted_covariance = predicted_covariance;
results.measurement_m = measurement_m;
results.measurement_noise_m = measurement_noise_m;
results.measurement_truth_id = measurement_truth_id;
results.residual_m = residual_m;
results.innovation_covariance = innovation_covariance;
results.squared_mahalanobis_distance = squared_mahalanobis_distance;
results.gate_mask = gate_mask;
results.baseline_assignment = baseline_assignment;
results.gate_threshold_sweep_d2 = gate_threshold_sweep_d2;
results.gate_sweep_candidate_count = gate_sweep_candidate_count;
results.covariance_scale_sweep = covariance_scale_sweep;
results.covariance_sweep_track1_target_d2 = covariance_sweep_track1_target_d2;
results.covariance_sweep_track1_clutter_d2 = covariance_sweep_track1_clutter_d2;
results.broken_assignment = broken_assignment;
results.recovered_assignment = recovered_assignment;
results.reviewed_pair_slots = reviewed_pair_slots;

%% Local functions: validation, distance, assignment, and display
function validate_sweep(values, required_value, maximum_cases, description)
if ~isa(values, 'double') || ~isvector(values) || numel(values) < 3 || ...
        numel(values) > maximum_cases || ~isreal(values) || ...
        any(~isfinite(values)) || any(values <= 0) || any(diff(values) <= 0) || ...
        sum(values == required_value) ~= 1
    error('P57:InvalidSweep', ...
        '%s sweep must be increasing, positive, bounded, and contain its baseline once.', ...
        description);
end
end

function [residual_m, squared_distance] = association_distances( ...
        predicted_measurement, innovation_covariance, measurement_m)
if ~isa(predicted_measurement, 'double') || ...
        ~isa(innovation_covariance, 'double') || ~isa(measurement_m, 'double') || ...
        ~ismatrix(predicted_measurement) || ~ismatrix(measurement_m) || ...
        ndims(innovation_covariance) > 3 || ...
        size(predicted_measurement, 1) ~= 2 || size(measurement_m, 1) ~= 2 || ...
        size(innovation_covariance, 1) ~= 2 || ...
        size(innovation_covariance, 2) ~= 2 || ...
        size(innovation_covariance, 3) ~= size(predicted_measurement, 2) || ...
        isempty(predicted_measurement) || isempty(measurement_m) || ...
        ~isreal(predicted_measurement) || ~isreal(innovation_covariance) || ...
        ~isreal(measurement_m) || any(~isfinite(predicted_measurement(:))) || ...
        any(~isfinite(innovation_covariance(:))) || any(~isfinite(measurement_m(:)))
    error('P57:InvalidAssociationInput', ...
        'Predictions, 2-by-2 covariance pages, and detections must be finite real double arrays.');
end
track_count = size(predicted_measurement, 2);
measurement_count = size(measurement_m, 2);
if track_count > 8 || measurement_count > 12 || track_count*measurement_count > 96
    error('P57:AssociationInputBound', 'Association input exceeds reviewed dimensions.');
end
residual_m = zeros(2, track_count, measurement_count);
squared_distance = zeros(track_count, measurement_count);
for track_index = 1:track_count
    current_covariance = innovation_covariance(:, :, track_index);
    if max(max(abs(current_covariance - current_covariance'))) > 1e-10 || ...
            any(eig(current_covariance) <= 0)
        error('P57:InvalidInnovationCovariance', ...
            'Every innovation covariance must be symmetric positive definite.');
    end
    for measurement_index = 1:measurement_count
        residual_m(:, track_index, measurement_index) = ...
            measurement_m(:, measurement_index) - predicted_measurement(:, track_index);
        current_residual = residual_m(:, track_index, measurement_index);
        squared_distance(track_index, measurement_index) = ...
            current_residual'*(current_covariance\current_residual);
        if ~isfinite(squared_distance(track_index, measurement_index)) || ...
                squared_distance(track_index, measurement_index) < 0
            error('P57:InvalidDistance', ...
                'Squared Mahalanobis distances must remain finite and nonnegative.');
        end
    end
end
end

function standard_normal = seeded_gaussian_noise(seed, row_count, column_count)
if ~isa(seed, 'double') || ~isscalar(seed) || ~isfinite(seed) || ...
        ~isreal(seed) || seed ~= floor(seed) || seed <= 0 || seed >= 2147483647 || ...
        ~isa(row_count, 'double') || ~isscalar(row_count) || ...
        ~isfinite(row_count) || row_count ~= floor(row_count) || row_count <= 0 || ...
        ~isa(column_count, 'double') || ~isscalar(column_count) || ...
        ~isfinite(column_count) || column_count ~= floor(column_count) || ...
        column_count <= 0 || row_count*column_count > 96
    error('P57:InvalidNoiseRequest', ...
        'Seed and Gaussian-noise dimensions must be positive finite bounded integers.');
end
modulus = 2147483647;
multiplier = 16807;
state = seed;
normal_count = row_count*column_count;
pair_count = ceil(normal_count/2);
normal_sequence = zeros(1, 2*pair_count);
for pair_index = 1:pair_count
    state = mod(multiplier*state, modulus);
    uniform_1 = (state + 0.5)/modulus;
    state = mod(multiplier*state, modulus);
    uniform_2 = (state + 0.5)/modulus;
    radius = sqrt(-2*log(uniform_1));
    angle_rad = 2*pi*uniform_2;
    normal_sequence(2*pair_index-1) = radius*cos(angle_rad);
    normal_sequence(2*pair_index) = radius*sin(angle_rad);
end
standard_normal = reshape(normal_sequence(1:normal_count), row_count, column_count);
end

function assignment = greedy_nearest_neighbor(distance, valid_mask)
if ~isa(distance, 'double') || ~ismatrix(distance) || isempty(distance) || ...
        ~isreal(distance) || any(~isfinite(distance(:))) || any(distance(:) < 0) || ...
        ~islogical(valid_mask) || ~isequal(size(valid_mask), size(distance)) || ...
        size(distance, 1) > 8 || size(distance, 2) > 12 || numel(distance) > 96
    error('P57:InvalidAssignmentInput', ...
        'Distance and logical gate matrices must be finite, nonnegative, matched, and bounded.');
end
assignment = zeros(1, size(distance, 1));
working_distance = distance;
working_distance(~valid_mask) = Inf;
maximum_assignments = min(size(distance));
for assignment_index = 1:maximum_assignments
    [nearest_distance, linear_index] = min(working_distance(:));
    if ~isfinite(nearest_distance)
        break;
    end
    [track_index, measurement_index] = ind2sub(size(working_distance), linear_index);
    assignment(track_index) = measurement_index;
    working_distance(track_index, :) = Inf;
    working_distance(:, measurement_index) = Inf;
end
end

function ellipse_xy = covariance_ellipse(center_xy, covariance, scale, point_count)
if ~isa(center_xy, 'double') || ~isequal(size(center_xy), [2 1]) || ...
        ~isa(covariance, 'double') || ~isequal(size(covariance), [2 2]) || ...
        any(~isfinite(center_xy)) || any(~isfinite(covariance(:))) || ...
        ~isreal(center_xy) || ~isreal(covariance) || ...
        max(max(abs(covariance - covariance'))) > 1e-10 || ...
        any(eig(covariance) <= 0) || ~isa(scale, 'double') || ...
        ~isscalar(scale) || ~isfinite(scale) || ~isreal(scale) || scale <= 0 || ...
        ~isa(point_count, 'double') || ~isscalar(point_count) || ...
        ~isfinite(point_count) || point_count ~= floor(point_count) || ...
        point_count < 9 || point_count > 73
    error('P57:InvalidEllipseInput', ...
        'Ellipse inputs must be finite, positive definite, and bounded.');
end
[vectors, values] = eig(covariance);
angles = linspace(0, 2*pi, point_count);
ellipse_xy = center_xy + scale*vectors*sqrt(values)*[cos(angles); sin(angles)];
end

function plot_association(predicted_measurement, innovation_covariance, ...
        measurement_m, assignment, gate_threshold, point_count, link_color)
plot(predicted_measurement(1, :), predicted_measurement(2, :), ...
    'bs', 'MarkerSize', 9, 'LineWidth', 1.4); hold on;
plot(measurement_m(1, :), measurement_m(2, :), 'ko', 'MarkerSize', 6);
for track_index = 1:size(predicted_measurement, 2)
    gate_xy = covariance_ellipse(predicted_measurement(:, track_index), ...
        innovation_covariance(:, :, track_index), sqrt(gate_threshold), point_count);
    plot(gate_xy(1, :), gate_xy(2, :), 'b:', 'HandleVisibility', 'off');
    text(predicted_measurement(1, track_index) + 7, ...
        predicted_measurement(2, track_index) + 7, sprintf('T%d', track_index));
    measurement_index = assignment(track_index);
    if measurement_index > 0
        plot([predicted_measurement(1, track_index) measurement_m(1, measurement_index)], ...
            [predicted_measurement(2, track_index) measurement_m(2, measurement_index)], ...
            '-', 'Color', link_color, 'LineWidth', 1.8, 'HandleVisibility', 'off');
    end
end
for measurement_index = 1:size(measurement_m, 2)
    text(measurement_m(1, measurement_index) + 4, ...
        measurement_m(2, measurement_index) - 6, sprintf('D%d', measurement_index));
end
axis equal; grid on;
xlabel('Cartesian x (m)'); ylabel('Cartesian y (m)');
legend('Predicted track', 'Detection', 'Location', 'best');
end
