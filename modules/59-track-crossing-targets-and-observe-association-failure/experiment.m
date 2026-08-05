%% P59 - Track Crossing Targets and Observe Association Failure
% Why do simple nearest-neighbor trackers swap identities?
% Base MATLAB, R2016b or later (local functions in scripts). No toolbox.

clear;
clc;

%% Visible reviewed controls
baseline_seed = 5908;
number_scans = 25;
scan_interval_s = 1.0;
position_noise_sigma_m = 6.0;
velocity_noise_sigma_mps = 3.0;
position_gain = 0.60;
velocity_gain = 0.25;
velocity_feature_weight = 1.0;
closest_approach_m = 0.0;
number_trials = 200;

position_noise_sweep_m = [2 6 10];
update_interval_sweep_s = [0.5 1 2];
closest_approach_sweep_m = [0 12 24];

maximum_scans = 25;
maximum_trials = 200;
maximum_sweep_cases = 5;
maximum_association_passes = 3605;
maximum_pair_evaluations = 360500;
maximum_random_values_per_scene = 200;
maximum_total_random_values = 360200;
maximum_figures = 6;

controls = struct( ...
    'seed', baseline_seed, ...
    'number_scans', number_scans, ...
    'scan_interval_s', scan_interval_s, ...
    'position_noise_sigma_m', position_noise_sigma_m, ...
    'velocity_noise_sigma_mps', velocity_noise_sigma_mps, ...
    'position_gain', position_gain, ...
    'velocity_gain', velocity_gain, ...
    'velocity_feature_weight', velocity_feature_weight, ...
    'closest_approach_m', closest_approach_m, ...
    'number_trials', number_trials, ...
    'position_noise_sweep_m', position_noise_sweep_m, ...
    'update_interval_sweep_s', update_interval_sweep_s, ...
    'closest_approach_sweep_m', closest_approach_sweep_m, ...
    'maximum_scans', maximum_scans, ...
    'maximum_trials', maximum_trials, ...
    'maximum_sweep_cases', maximum_sweep_cases, ...
    'maximum_association_passes', maximum_association_passes, ...
    'maximum_pair_evaluations', maximum_pair_evaluations, ...
    'maximum_random_values_per_scene', maximum_random_values_per_scene, ...
    'maximum_total_random_values', maximum_total_random_values, ...
    'maximum_figures', maximum_figures);
validate_controls(controls);

existing_figures = findall(0, 'Type', 'figure', 'Tag', 'P59');
if ~isempty(existing_figures)
    close(existing_figures);
end

%% Build one private, deterministic crossing record
% Target A: p_A(t) = [20t, 5t] m, v_A = [20, 5] m/s.
% Target B: p_B(t) = [20t,-5t] m, v_B = [20,-5] m/s.
% They have equal speed and similar forward velocity, but opposite cross-track
% components. Truth IDs are retained in a separate audit array and never enter
% the association cost or state update.
baseline_scene = build_scene(controls, baseline_seed, ...
    position_noise_sigma_m, scan_interval_s, closest_approach_m);

%% Baseline: position-only greedy nearest neighbor
% For every predicted track i and report j,
%   Jp(i,j) = ||z_p(j)-p_i^-||^2 / sigma_p^2.
% The smallest remaining pair is selected, then its row and column are removed.
position_only = run_tracker(baseline_scene, controls, 0.0, false);
position_metrics = score_identity(position_only.assignment, ...
    baseline_scene.report_truth_id);

%% Add normalized velocity information to the same association cost
%   J(i,j) = Jp(i,j) + lambda_v*||z_v(j)-v_i^-||^2/sigma_v^2.
% The velocity report changes association only; the alpha-beta state correction
% still uses position residuals so this comparison isolates richer association.
velocity_aware = run_tracker(baseline_scene, controls, ...
    velocity_feature_weight, false);
velocity_metrics = score_identity(velocity_aware.assignment, ...
    baseline_scene.report_truth_id);

assert(position_metrics.wrong_link_count == 24, ...
    'Reviewed baseline must contain 24 wrong links.');
assert(position_metrics.identity_transition_count == 2, ...
    'Reviewed baseline must contain two identity transitions.');
assert(velocity_metrics.wrong_link_count == 0, ...
    'Reviewed velocity-aware case must preserve both identities.');

%% Three controlled Monte Carlo sweeps
% Each paired case uses seeds 5901:6100 and the same standard-normal sequence
% for position-only and velocity-aware association. Only the named control
% changes. These are bounded synthetic trials, not operational probabilities.
[noise_position_failure, noise_velocity_failure, ...
    noise_position_wrong, noise_velocity_wrong] = run_sweep( ...
    controls, 'position_noise', position_noise_sweep_m);
[interval_position_failure, interval_velocity_failure, ...
    interval_position_wrong, interval_velocity_wrong] = run_sweep( ...
    controls, 'scan_interval', update_interval_sweep_s);
[separation_position_failure, separation_velocity_failure, ...
    separation_position_wrong, separation_velocity_wrong] = run_sweep( ...
    controls, 'closest_approach', closest_approach_sweep_m);

assert(all(noise_velocity_failure <= noise_position_failure), ...
    'Velocity feature must not increase reviewed noise-sweep failures.');
assert(all(interval_velocity_failure <= interval_position_failure), ...
    'Velocity feature must not increase reviewed interval-sweep failures.');
assert(all(separation_velocity_failure <= separation_position_failure), ...
    'Velocity feature must not increase reviewed separation-sweep failures.');

%% Intentionally broken case: independent row minima reuse one report
% Removing only a cost row lets both tracks consume the same detection. This
% violates P57's one-to-one invariant and makes the two estimates coalesce.
broken = run_tracker(baseline_scene, controls, 0.0, true);
broken_metrics = score_identity(broken.assignment, ...
    baseline_scene.report_truth_id);
assert(broken.duplicate_report_scan_count == 12, ...
    'Reviewed broken case must reuse a report on 12 scans.');

% Recovery restores row-and-column removal and the normalized velocity term on
% the exact same report arrays. No new random record is generated.
recovered = run_tracker(baseline_scene, controls, ...
    velocity_feature_weight, false);
recovery_exact = isequal(recovered.assignment, velocity_aware.assignment) && ...
    isequal(recovered.position_history_m, velocity_aware.position_history_m) && ...
    isequal(recovered.velocity_history_mps, velocity_aware.velocity_history_mps);
assert(recovery_exact, 'Recovery must exactly reproduce the reviewed baseline.');

%% Figure 1 - physical scene and auxiliary measurement
figure('Name', 'P59 Figure 1 - crossing input', 'Tag', 'P59', ...
    'Color', 'w');
subplot(1, 2, 1);
truth_a_handle = plot(squeeze(baseline_scene.truth_position_m(1,1,:)), ...
    squeeze(baseline_scene.truth_position_m(1,2,:)), 'k-', 'LineWidth', 1.8);
hold on;
truth_b_handle = plot(squeeze(baseline_scene.truth_position_m(2,1,:)), ...
    squeeze(baseline_scene.truth_position_m(2,2,:)), 'k--', 'LineWidth', 1.8);
for scan = 1:number_scans
    for report = 1:2
        truth_id = baseline_scene.report_truth_id(report, scan);
        if truth_id == 1
            marker_color = [0.15 0.45 0.85];
        else
            marker_color = [0.85 0.30 0.20];
        end
        plot(baseline_scene.report_position_m(report,1,scan), ...
            baseline_scene.report_position_m(report,2,scan), '.', ...
            'Color', marker_color, 'MarkerSize', 10, ...
            'HandleVisibility', 'off');
    end
end
crossing_handle = plot(0, 0, 'ko', 'MarkerSize', 9, 'LineWidth', 1.5);
grid on;
axis equal;
xlabel('Along-track position x (m)');
ylabel('Cross-track position y (m)');
title('Truth paths and noisy position reports');
legend([truth_a_handle truth_b_handle crossing_handle], ...
    'Truth A', 'Truth B', 'Nominal crossing', 'Location', 'best');

subplot(1, 2, 2);
time_s = baseline_scene.time_s;
velocity_a = nan(1, number_scans);
velocity_b = nan(1, number_scans);
for scan = 1:number_scans
    for report = 1:2
        if baseline_scene.report_truth_id(report,scan) == 1
            velocity_a(scan) = baseline_scene.report_velocity_mps(report,2,scan);
        else
            velocity_b(scan) = baseline_scene.report_velocity_mps(report,2,scan);
        end
    end
end
plot(time_s, velocity_a, 'o-', 'LineWidth', 1.2);
hold on;
plot(time_s, velocity_b, 's-', 'LineWidth', 1.2);
plot(time_s, 5*ones(size(time_s)), 'k:');
plot(time_s, -5*ones(size(time_s)), 'k:');
grid on;
xlabel('Time from crossing (s)');
ylabel('Auxiliary cross-track velocity (m/s)');
title('Noisy velocity feature');
legend('Reports from A', 'Reports from B', 'Truth +5 m/s', ...
    'Truth -5 m/s', 'Location', 'best');

%% Figure 2 - visible position-only identity swap
figure('Name', 'P59 Figure 2 - position-only swap', 'Tag', 'P59', ...
    'Color', 'w');
subplot(2, 1, 1);
plot(squeeze(position_only.position_history_m(1,1,:)), ...
    squeeze(position_only.position_history_m(1,2,:)), 'b-o', ...
    'LineWidth', 1.2, 'MarkerSize', 3);
hold on;
plot(squeeze(position_only.position_history_m(2,1,:)), ...
    squeeze(position_only.position_history_m(2,2,:)), 'r-s', ...
    'LineWidth', 1.2, 'MarkerSize', 3);
plot(squeeze(baseline_scene.truth_position_m(1,1,:)), ...
    squeeze(baseline_scene.truth_position_m(1,2,:)), 'k:');
plot(squeeze(baseline_scene.truth_position_m(2,1,:)), ...
    squeeze(baseline_scene.truth_position_m(2,2,:)), 'k--');
grid on;
axis equal;
xlabel('Along-track position x (m)');
ylabel('Cross-track position y (m)');
title('Position-only estimates change physical target after the crossing');
legend('Track 1 estimate', 'Track 2 estimate', 'Truth A', 'Truth B', ...
    'Location', 'best');

subplot(2, 1, 2);
imagesc(1:number_scans, 1:2, position_metrics.assigned_truth_id);
colormap(gca, [0.15 0.45 0.85; 0.85 0.30 0.20]);
caxis([1 2]);
set(gca, 'YTick', [1 2], 'YTickLabel', {'Track 1', 'Track 2'});
xlabel('Scan index');
ylabel('Tracker slot');
title(sprintf('Assigned truth ID: %d wrong links, %d transitions', ...
    position_metrics.wrong_link_count, ...
    position_metrics.identity_transition_count));
colorbar('Ticks', [1.25 1.75], 'TickLabels', {'Truth A', 'Truth B'});

%% Figure 3 - cost information changes the association decision
figure('Name', 'P59 Figure 3 - velocity-aware association', 'Tag', 'P59', ...
    'Color', 'w');
comparison_scan = 14;
subplot(1, 3, 1);
imagesc(position_only.position_cost(:,:,comparison_scan));
colorbar;
axis equal tight;
set(gca, 'XTick', [1 2], 'YTick', [1 2]);
xlabel('Report index');
ylabel('Track index');
title(sprintf('Position cost J_p, scan %d', comparison_scan));

subplot(1, 3, 2);
imagesc(velocity_aware.total_cost(:,:,comparison_scan));
colorbar;
axis equal tight;
set(gca, 'XTick', [1 2], 'YTick', [1 2]);
xlabel('Report index');
ylabel('Track index');
title('Position + velocity cost J');

subplot(1, 3, 3);
imagesc(1:number_scans, 1:2, velocity_metrics.assigned_truth_id);
colormap(gca, [0.15 0.45 0.85; 0.85 0.30 0.20]);
caxis([1 2]);
set(gca, 'YTick', [1 2], 'YTickLabel', {'Track 1', 'Track 2'});
xlabel('Scan index');
ylabel('Tracker slot');
title(sprintf('Velocity-aware: %d wrong, %d transitions', ...
    velocity_metrics.wrong_link_count, ...
    velocity_metrics.identity_transition_count));
colorbar('Ticks', [1.25 1.75], 'TickLabels', {'Truth A', 'Truth B'});

%% Figure 4 - measurement-noise sweep
figure('Name', 'P59 Figure 4 - position-noise sweep', 'Tag', 'P59', ...
    'Color', 'w');
subplot(1, 2, 1);
plot(position_noise_sweep_m, 100*noise_position_failure, 'o-', ...
    'LineWidth', 1.5);
hold on;
plot(position_noise_sweep_m, 100*noise_velocity_failure, 's-', ...
    'LineWidth', 1.5);
grid on;
xlabel('Position noise sigma per coordinate (m)');
ylabel('Trials with any wrong link (%)');
title(sprintf('Noise sweep, %d paired trials', number_trials));
legend('Position only', 'Position + velocity', 'Location', 'northwest');

subplot(1, 2, 2);
plot(position_noise_sweep_m, noise_position_wrong, 'o-', 'LineWidth', 1.5);
hold on;
plot(position_noise_sweep_m, noise_velocity_wrong, 's-', 'LineWidth', 1.5);
grid on;
xlabel('Position noise sigma per coordinate (m)');
ylabel('Mean wrong links per trial (links/trial)');
title('Error duration as ambiguity grows');
legend('Position only', 'Position + velocity', 'Location', 'northwest');

%% Figure 5 - update-rate and closest-approach sweeps
figure('Name', 'P59 Figure 5 - geometry and update sweeps', 'Tag', 'P59', ...
    'Color', 'w');
subplot(1, 2, 1);
plot(update_interval_sweep_s, 100*interval_position_failure, 'o-', ...
    'LineWidth', 1.5);
hold on;
plot(update_interval_sweep_s, 100*interval_velocity_failure, 's-', ...
    'LineWidth', 1.5);
grid on;
xlabel('Scan interval (s)');
ylabel('Trials with any wrong link (%)');
title('Fixed 25-scan update-interval sweep');
legend('Position only', 'Position + velocity', 'Location', 'northeast');

subplot(1, 2, 2);
plot(closest_approach_sweep_m, 100*separation_position_failure, 'o-', ...
    'LineWidth', 1.5);
hold on;
plot(closest_approach_sweep_m, 100*separation_velocity_failure, 's-', ...
    'LineWidth', 1.5);
grid on;
xlabel('Closest approach (m)');
ylabel('Trials with any wrong link (%)');
title('One-variable geometry sweep');
legend('Position only', 'Position + velocity', 'Location', 'northeast');

%% Figure 6 - broken reuse and deterministic recovery
figure('Name', 'P59 Figure 6 - broken and recovery', 'Tag', 'P59', ...
    'Color', 'w');
subplot(1, 2, 1);
stairs(1:number_scans, broken.assignment(1,:), 'b-', 'LineWidth', 1.4);
hold on;
stairs(1:number_scans, broken.assignment(2,:), 'r--', 'LineWidth', 1.4);
duplicate_scans = broken.assignment(1,:) == broken.assignment(2,:);
plot(find(duplicate_scans), broken.assignment(1,duplicate_scans), ...
    'ko', 'MarkerFaceColor', 'y');
grid on;
ylim([0.75 2.25]);
set(gca, 'YTick', [1 2]);
xlabel('Scan index');
ylabel('Selected report index');
title(sprintf('Broken: report reused on %d scans', ...
    broken.duplicate_report_scan_count));
legend('Track 1 choice', 'Track 2 choice', 'Duplicate use', ...
    'Location', 'best');

subplot(1, 2, 2);
bar([position_metrics.wrong_link_count, broken_metrics.wrong_link_count, ...
    velocity_metrics.wrong_link_count]);
set(gca, 'XTickLabel', {'Position NN', 'Broken reuse', 'Recovered'});
ylabel('Wrong association links (links)');
title(sprintf('Exact recovery = %d', recovery_exact));
grid on;

%% Retained console metrics
fprintf('\nP59 Track Crossing Targets and Observe Association Failure\n');
fprintf('Guiding question: Why do simple nearest-neighbor trackers swap identities?\n');
fprintf('Baseline seed: %d (private Park-Miller/Box-Muller record)\n', baseline_seed);
fprintf('Position-only: wrong links = %d links, identity transitions = %d transitions\n', ...
    position_metrics.wrong_link_count, ...
    position_metrics.identity_transition_count);
fprintf('Velocity-aware: wrong links = %d links, identity transitions = %d transitions\n', ...
    velocity_metrics.wrong_link_count, ...
    velocity_metrics.identity_transition_count);
fprintf('Broken independent nearest: duplicate-report scans = %d scans\n', ...
    broken.duplicate_report_scan_count);
fprintf('Recovery exact on identical input arrays: %d\n', recovery_exact);
fprintf('Reviewed work: %d trials, %d sweep cases, <= %d pair evaluations, %d figures\n', ...
    number_trials, numel(position_noise_sweep_m) + ...
    numel(update_interval_sweep_s) + numel(closest_approach_sweep_m), ...
    maximum_pair_evaluations, maximum_figures);

p59_results = struct( ...
    'baseline_scene', baseline_scene, ...
    'position_only', position_only, ...
    'position_metrics', position_metrics, ...
    'velocity_aware', velocity_aware, ...
    'velocity_metrics', velocity_metrics, ...
    'noise_position_failure', noise_position_failure, ...
    'noise_velocity_failure', noise_velocity_failure, ...
    'interval_position_failure', interval_position_failure, ...
    'interval_velocity_failure', interval_velocity_failure, ...
    'separation_position_failure', separation_position_failure, ...
    'separation_velocity_failure', separation_velocity_failure, ...
    'broken', broken, ...
    'broken_metrics', broken_metrics, ...
    'recovered', recovered, ...
    'recovery_exact', recovery_exact);

%% Local functions
function validate_controls(c)
integer_fields = {'seed','number_scans','number_trials','maximum_scans', ...
    'maximum_trials','maximum_sweep_cases','maximum_association_passes', ...
    'maximum_pair_evaluations','maximum_random_values_per_scene', ...
    'maximum_total_random_values','maximum_figures'};
for index = 1:numel(integer_fields)
    value = c.(integer_fields{index});
    if ~isnumeric(value) || ~isreal(value) || ~isscalar(value) || ...
            ~isfinite(value) || value ~= floor(value)
        error('P59:InvalidControl', '%s must be a finite real integer.', ...
            integer_fields{index});
    end
end
if c.maximum_scans ~= 25 || c.maximum_trials ~= 200 || ...
        c.maximum_sweep_cases ~= 5 || ...
        c.maximum_association_passes ~= 3605 || ...
        c.maximum_pair_evaluations ~= 360500 || ...
        c.maximum_random_values_per_scene ~= 200 || ...
        c.maximum_total_random_values ~= 360200 || ...
        c.maximum_figures ~= 6
    error('P59:ResourceBound', 'Reviewed resource ceilings are immutable.');
end
if c.seed < 1 || c.seed >= 2147483647
    error('P59:InvalidSeed', 'Seed must be in [1, 2147483646].');
end
if c.number_scans < 3 || c.number_scans > c.maximum_scans || ...
        c.number_trials < 1 || c.number_trials > c.maximum_trials
    error('P59:ResourceBound', 'Scan or trial count exceeds reviewed bounds.');
end
positive_fields = {'scan_interval_s','position_noise_sigma_m', ...
    'velocity_noise_sigma_mps','position_gain','velocity_gain'};
for index = 1:numel(positive_fields)
    value = c.(positive_fields{index});
    if ~isnumeric(value) || ~isreal(value) || ~isscalar(value) || ...
            ~isfinite(value) || value <= 0
        error('P59:InvalidControl', '%s must be positive and finite.', ...
            positive_fields{index});
    end
end
if c.position_gain > 1 || c.velocity_gain > 1
    error('P59:InvalidGain', 'Alpha-beta gains must be in (0,1].');
end
if ~isnumeric(c.velocity_feature_weight) || ...
        ~isreal(c.velocity_feature_weight) || ...
        ~isscalar(c.velocity_feature_weight) || ...
        ~isfinite(c.velocity_feature_weight) || c.velocity_feature_weight < 0
    error('P59:InvalidFeatureWeight', ...
        'Velocity feature weight must be finite and nonnegative.');
end
if ~isnumeric(c.closest_approach_m) || ~isreal(c.closest_approach_m) || ...
        ~isscalar(c.closest_approach_m) || ...
        ~isfinite(c.closest_approach_m) || c.closest_approach_m < 0
    error('P59:InvalidSeparation', ...
        'Closest approach must be finite and nonnegative.');
end
validate_sweep(c.position_noise_sweep_m, c.position_noise_sigma_m, ...
    c.maximum_sweep_cases, true, 'position noise');
validate_sweep(c.update_interval_sweep_s, c.scan_interval_s, ...
    c.maximum_sweep_cases, true, 'scan interval');
validate_sweep(c.closest_approach_sweep_m, c.closest_approach_m, ...
    c.maximum_sweep_cases, false, 'closest approach');
number_cases = numel(c.position_noise_sweep_m) + ...
    numel(c.update_interval_sweep_s) + numel(c.closest_approach_sweep_m);
association_passes = 2 + 2*c.number_trials*number_cases + 2;
pair_evaluations = association_passes*c.number_scans*4;
random_values_per_scene = c.number_scans*2*4;
total_random_values = random_values_per_scene*(c.number_trials*number_cases + 1);
if association_passes > c.maximum_association_passes || ...
        pair_evaluations > c.maximum_pair_evaluations || ...
        random_values_per_scene > c.maximum_random_values_per_scene || ...
        total_random_values > c.maximum_total_random_values
    error('P59:ResourceBound', 'Reviewed work ceiling drifted.');
end
end

function validate_sweep(values, baseline, maximum_cases, require_positive, name)
if ~isnumeric(values) || ~isreal(values) || isempty(values) || ...
        ~isvector(values) || any(~isfinite(values)) || ...
        numel(values) > maximum_cases || any(diff(values) <= 0)
    error('P59:InvalidSweep', '%s sweep must be finite and increasing.', name);
end
if (require_positive && any(values <= 0)) || ...
        (~require_positive && any(values < 0)) || sum(values == baseline) ~= 1
    error('P59:InvalidSweep', ...
        '%s sweep must contain its reviewed baseline once.', name);
end
end

function scene = build_scene(c, seed, sigma_position_m, interval_s, miss_m)
if ~isscalar(seed) || seed ~= floor(seed) || seed < 1 || seed >= 2147483647
    error('P59:InvalidSeed', 'Scene seed is outside the private generator range.');
end
if any(~isfinite([sigma_position_m interval_s miss_m])) || ...
        sigma_position_m <= 0 || interval_s <= 0 || miss_m < 0
    error('P59:InvalidScene', 'Scene scales must be finite and physical.');
end
normal_count = c.number_scans*2*4;
standard_normal = private_gaussian(seed, normal_count, ...
    c.maximum_random_values_per_scene);
noise_columns = reshape(standard_normal, 4, 2*c.number_scans);
centre_scan = (c.number_scans + 1)/2;
time_s = ((1:c.number_scans) - centre_scan)*interval_s;
truth_velocity_mps = [20 5; 20 -5];
truth_position_m = zeros(2, 2, c.number_scans);
report_position_m = zeros(2, 2, c.number_scans);
report_velocity_mps = zeros(2, 2, c.number_scans);
report_truth_id = zeros(2, c.number_scans);
for scan = 1:c.number_scans
    t = time_s(scan);
    truth_position_m(1,:,scan) = [20*t - miss_m/2, 5*t];
    truth_position_m(2,:,scan) = [20*t + miss_m/2, -5*t];
    unsorted_position = zeros(2,2);
    unsorted_velocity = zeros(2,2);
    for truth_id = 1:2
        column = 2*(scan-1) + truth_id;
        unsorted_position(truth_id,:) = ...
            truth_position_m(truth_id,:,scan) + ...
            sigma_position_m*noise_columns(1:2,column).';
        unsorted_velocity(truth_id,:) = truth_velocity_mps(truth_id,:) + ...
            c.velocity_noise_sigma_mps*noise_columns(3:4,column).';
    end
    if mod(scan,2) == 1
        report_order = [1 2];
    else
        report_order = [2 1];
    end
    report_position_m(:,:,scan) = unsorted_position(report_order,:);
    report_velocity_mps(:,:,scan) = unsorted_velocity(report_order,:);
    report_truth_id(:,scan) = report_order(:);
end
scene = struct( ...
    'time_s', time_s, ...
    'truth_position_m', truth_position_m, ...
    'truth_velocity_mps', truth_velocity_mps, ...
    'initial_position_m', truth_position_m(:,:,1), ...
    'initial_velocity_mps', truth_velocity_mps, ...
    'report_position_m', report_position_m, ...
    'report_velocity_mps', report_velocity_mps, ...
    'report_truth_id', report_truth_id, ...
    'position_noise_sigma_m', sigma_position_m, ...
    'velocity_noise_sigma_mps', c.velocity_noise_sigma_mps, ...
    'scan_interval_s', interval_s, ...
    'closest_approach_m', miss_m);
end

function result = run_tracker(scene, c, feature_weight, allow_report_reuse)
validate_scene(scene, c);
if ~isnumeric(feature_weight) || ~isscalar(feature_weight) || ...
        ~isreal(feature_weight) || ...
        ~isfinite(feature_weight) || feature_weight < 0 || ...
        ~islogical(allow_report_reuse) || ~isscalar(allow_report_reuse)
    error('P59:InvalidAssociationControl', ...
        'Feature weight and reuse flag are malformed.');
end
track_position_m = scene.initial_position_m;
track_velocity_mps = scene.initial_velocity_mps;
assignment = zeros(2, c.number_scans);
position_history_m = zeros(2,2,c.number_scans);
velocity_history_mps = zeros(2,2,c.number_scans);
prediction_history_m = zeros(2,2,c.number_scans);
position_cost = zeros(2,2,c.number_scans);
velocity_cost = zeros(2,2,c.number_scans);
total_cost = zeros(2,2,c.number_scans);
duplicate_report_scan_count = 0;
for scan = 1:c.number_scans
    if scan == 1
        predicted_position_m = track_position_m;
    else
        predicted_position_m = track_position_m + ...
            scene.scan_interval_s*track_velocity_mps;
    end
    predicted_velocity_mps = track_velocity_mps;
    prediction_history_m(:,:,scan) = predicted_position_m;
    for track = 1:2
        for report = 1:2
            position_residual_m = scene.report_position_m(report,:,scan) - ...
                predicted_position_m(track,:);
            velocity_residual_mps = scene.report_velocity_mps(report,:,scan) - ...
                predicted_velocity_mps(track,:);
            position_cost(track,report,scan) = ...
                sum(position_residual_m.^2)/scene.position_noise_sigma_m^2;
            velocity_cost(track,report,scan) = ...
                sum(velocity_residual_mps.^2)/scene.velocity_noise_sigma_mps^2;
            total_cost(track,report,scan) = position_cost(track,report,scan) + ...
                feature_weight*velocity_cost(track,report,scan);
        end
    end
    if allow_report_reuse
        for track = 1:2
            [~, assignment(track,scan)] = min(total_cost(track,:,scan));
        end
    else
        remaining_cost = total_cost(:,:,scan);
        for choice = 1:2
            [~, linear_index] = min(remaining_cost(:));
            [selected_track, selected_report] = ind2sub([2 2], linear_index);
            assignment(selected_track,scan) = selected_report;
            remaining_cost(selected_track,:) = inf;
            remaining_cost(:,selected_report) = inf;
        end
    end
    if assignment(1,scan) == assignment(2,scan)
        duplicate_report_scan_count = duplicate_report_scan_count + 1;
    end
    for track = 1:2
        report = assignment(track,scan);
        residual_m = scene.report_position_m(report,:,scan) - ...
            predicted_position_m(track,:);
        track_position_m(track,:) = predicted_position_m(track,:) + ...
            c.position_gain*residual_m;
        track_velocity_mps(track,:) = predicted_velocity_mps(track,:) + ...
            (c.velocity_gain/scene.scan_interval_s)*residual_m;
    end
    position_history_m(:,:,scan) = track_position_m;
    velocity_history_mps(:,:,scan) = track_velocity_mps;
end
result = struct( ...
    'assignment', assignment, ...
    'position_history_m', position_history_m, ...
    'velocity_history_mps', velocity_history_mps, ...
    'prediction_history_m', prediction_history_m, ...
    'position_cost', position_cost, ...
    'velocity_cost', velocity_cost, ...
    'total_cost', total_cost, ...
    'duplicate_report_scan_count', duplicate_report_scan_count);
end

function validate_scene(scene, c)
required = {'report_position_m','report_velocity_mps','report_truth_id', ...
    'initial_position_m','initial_velocity_mps','position_noise_sigma_m', ...
    'velocity_noise_sigma_mps','scan_interval_s'};
for index = 1:numel(required)
    if ~isfield(scene, required{index})
        error('P59:MalformedScene', 'Scene is missing %s.', required{index});
    end
end
numeric_arrays = {scene.report_position_m, scene.report_velocity_mps, ...
    scene.initial_position_m, scene.initial_velocity_mps};
for index = 1:numel(numeric_arrays)
    value = numeric_arrays{index};
    if ~isnumeric(value) || ~isreal(value) || any(~isfinite(value(:)))
        error('P59:MalformedScene', 'Scene arrays must be finite real numeric.');
    end
end
if ~isequal(size(scene.report_position_m), [2 2 c.number_scans]) || ...
        ~isequal(size(scene.report_velocity_mps), [2 2 c.number_scans]) || ...
        ~isequal(size(scene.report_truth_id), [2 c.number_scans]) || ...
        ~isequal(size(scene.initial_position_m), [2 2]) || ...
        ~isequal(size(scene.initial_velocity_mps), [2 2])
    error('P59:MalformedScene', 'Scene dimensions exceed the fixed two-target contract.');
end
if ~isnumeric(scene.report_truth_id) || ~isreal(scene.report_truth_id) || ...
        any(~isfinite(scene.report_truth_id(:)))
    error('P59:MalformedScene', 'Audit identities must be finite real numeric.');
end
for scan = 1:c.number_scans
    if ~isequal(sort(scene.report_truth_id(:,scan)), [1;2])
        error('P59:MalformedScene', ...
            'Each audit column must contain Truth A and Truth B exactly once.');
    end
end
if scene.position_noise_sigma_m <= 0 || ...
        scene.velocity_noise_sigma_mps <= 0 || scene.scan_interval_s <= 0
    error('P59:MalformedScene', 'Scene scales must be positive.');
end
end

function metrics = score_identity(assignment, report_truth_id)
if ~isequal(size(assignment), size(report_truth_id)) || ...
        any(assignment(:) ~= 1 & assignment(:) ~= 2) || ...
        any(report_truth_id(:) ~= 1 & report_truth_id(:) ~= 2)
    error('P59:MalformedAudit', 'Assignment audit arrays are malformed.');
end
for scan = 1:size(report_truth_id,2)
    if ~isequal(sort(report_truth_id(:,scan)), [1;2])
        error('P59:MalformedAudit', ...
            'Each audit column must contain both truth identities once.');
    end
end
assigned_truth_id = zeros(size(assignment));
for scan = 1:size(assignment,2)
    for track = 1:2
        assigned_truth_id(track,scan) = ...
            report_truth_id(assignment(track,scan),scan);
    end
end
expected_truth_id = repmat([1;2], 1, size(assignment,2));
wrong_link_count = sum(assigned_truth_id(:) ~= expected_truth_id(:));
identity_transition_count = sum(sum(diff(assigned_truth_id,1,2) ~= 0));
metrics = struct( ...
    'assigned_truth_id', assigned_truth_id, ...
    'wrong_link_count', wrong_link_count, ...
    'identity_transition_count', identity_transition_count, ...
    'any_failure', wrong_link_count > 0);
end

function [position_failure, velocity_failure, position_wrong, velocity_wrong] = ...
        run_sweep(c, sweep_name, sweep_values)
case_count = numel(sweep_values);
position_failures = zeros(1,case_count);
velocity_failures = zeros(1,case_count);
position_wrong_total = zeros(1,case_count);
velocity_wrong_total = zeros(1,case_count);
for trial = 1:c.number_trials
    trial_seed = 5900 + trial;
    for case_index = 1:case_count
        sigma_position_m = c.position_noise_sigma_m;
        interval_s = c.scan_interval_s;
        miss_m = c.closest_approach_m;
        if strcmp(sweep_name, 'position_noise')
            sigma_position_m = sweep_values(case_index);
        elseif strcmp(sweep_name, 'scan_interval')
            interval_s = sweep_values(case_index);
        elseif strcmp(sweep_name, 'closest_approach')
            miss_m = sweep_values(case_index);
        else
            error('P59:InvalidSweepName', 'Unknown sweep name.');
        end
        scene = build_scene(c, trial_seed, sigma_position_m, interval_s, miss_m);
        position_result = run_tracker(scene, c, 0.0, false);
        velocity_result = run_tracker(scene, c, c.velocity_feature_weight, false);
        position_score = score_identity(position_result.assignment, ...
            scene.report_truth_id);
        velocity_score = score_identity(velocity_result.assignment, ...
            scene.report_truth_id);
        position_failures(case_index) = position_failures(case_index) + ...
            position_score.any_failure;
        velocity_failures(case_index) = velocity_failures(case_index) + ...
            velocity_score.any_failure;
        position_wrong_total(case_index) = position_wrong_total(case_index) + ...
            position_score.wrong_link_count;
        velocity_wrong_total(case_index) = velocity_wrong_total(case_index) + ...
            velocity_score.wrong_link_count;
    end
end
position_failure = position_failures/c.number_trials;
velocity_failure = velocity_failures/c.number_trials;
position_wrong = position_wrong_total/c.number_trials;
velocity_wrong = velocity_wrong_total/c.number_trials;
end

function values = private_gaussian(seed, count, maximum_count)
if ~isscalar(seed) || seed ~= floor(seed) || seed < 1 || ...
        seed >= 2147483647 || ~isscalar(count) || count ~= floor(count) || ...
        count < 1 || count > maximum_count
    error('P59:PrivateRandomBound', ...
        'Private generator seed or count is outside reviewed bounds.');
end
modulus = 2147483647;
multiplier = 16807;
pair_count = ceil(count/2);
values = zeros(1, 2*pair_count);
state = seed;
for pair = 1:pair_count
    state = mod(multiplier*state, modulus);
    uniform_1 = (state + 0.5)/modulus;
    state = mod(multiplier*state, modulus);
    uniform_2 = (state + 0.5)/modulus;
    radius = sqrt(-2*log(uniform_1));
    angle_rad = 2*pi*uniform_2;
    values(2*pair-1) = radius*cos(angle_rad);
    values(2*pair) = radius*sin(angle_rad);
end
values = values(1:count);
end
