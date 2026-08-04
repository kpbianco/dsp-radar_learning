%% P53: Group Detection Cells into Target Reports
% Guiding question: How do several threshold-crossing cells become one physical detection?
% Dependencies: P42 range-Doppler axes, P50 2-D detector cells, and P52
% honest detector validation. This script uses base MATLAB only.

clear;
clc;
close(findobj(groot, 'Type', 'figure', 'Tag', 'P53'));

%% Visible controls and fixed resource ceilings
random_seed = 5301;
number_range_bins = 72;
number_velocity_bins = 65;
range_bin_spacing_m = 15;
velocity_bin_spacing_mps = 0.5;
normalized_detection_threshold = 1;
minimum_component_cells = 3;
centroid_weight_exponent = 1;
minimum_component_cell_sweep = [1 3 18];
centroid_weight_exponent_sweep = [0 1 2];

maximum_scene_cells = 20000;
maximum_component_queue_cells = 20000;
maximum_sweep_cases = 5;
maximum_figure_count = 6;

if ~isscalar(random_seed) || islogical(random_seed) || ~isreal(random_seed) || ...
        ~isfinite(random_seed) || random_seed ~= floor(random_seed) || ...
        random_seed ~= 5301
    error('P53:InvalidSeed', 'random_seed must be the integer 5301.');
end
if ~isscalar(number_range_bins) || ~isscalar(number_velocity_bins) || ...
        ~isscalar(minimum_component_cells) || ~isscalar(maximum_scene_cells) || ...
        ~isscalar(maximum_component_queue_cells) || ...
        ~isscalar(maximum_sweep_cases) || ~isscalar(maximum_figure_count) || ...
        islogical(number_range_bins) || islogical(number_velocity_bins) || ...
        islogical(minimum_component_cells) || islogical(maximum_scene_cells) || ...
        islogical(maximum_component_queue_cells) || ...
        islogical(maximum_sweep_cases) || islogical(maximum_figure_count)
    error('P53:InvalidIntegerControl', 'Scene, component, and resource controls must be scalar nonlogical integers.');
end
integer_controls = [number_range_bins number_velocity_bins minimum_component_cells ...
    maximum_scene_cells maximum_component_queue_cells maximum_sweep_cases maximum_figure_count];
if ~isreal(integer_controls) || ...
        any(~isfinite(integer_controls)) || any(integer_controls ~= floor(integer_controls))
    error('P53:InvalidIntegerControl', 'Scene, component, and resource controls must be finite integers.');
end
if number_range_bins ~= 72 || number_velocity_bins ~= 65 || ...
        number_range_bins*number_velocity_bins > maximum_scene_cells
    error('P53:SceneBound', 'The reviewed fixed-index scene must remain 72-by-65 and fit the cell budget.');
end
if minimum_component_cells < 1 || ...
        minimum_component_cells > number_range_bins*number_velocity_bins
    error('P53:InvalidMinimumCells', 'The baseline minimum component size must fit the reviewed scene.');
end
if maximum_scene_cells ~= 20000 || maximum_component_queue_cells ~= 20000 || ...
        maximum_sweep_cases ~= 5 || maximum_figure_count ~= 6
    error('P53:CeilingDrift', 'Fixed resource ceilings must not be increased by a learner edit.');
end
if maximum_component_queue_cells < number_range_bins*number_velocity_bins
    error('P53:QueueBound', 'The component queue must hold at most one copy of every scene cell.');
end
if ~isscalar(range_bin_spacing_m) || ~isscalar(velocity_bin_spacing_mps) || ...
        ~isscalar(normalized_detection_threshold) || ...
        ~isscalar(centroid_weight_exponent) || islogical(range_bin_spacing_m) || ...
        islogical(velocity_bin_spacing_mps) || ...
        islogical(normalized_detection_threshold) || ...
        islogical(centroid_weight_exponent)
    error('P53:InvalidRealControl', 'Scene spacings, threshold, and centroid exponent must be scalar nonlogical values.');
end
real_controls = [range_bin_spacing_m velocity_bin_spacing_mps ...
    normalized_detection_threshold centroid_weight_exponent];
if ~isreal(real_controls) || any(~isfinite(real_controls)) || ...
        range_bin_spacing_m ~= 15 || velocity_bin_spacing_mps ~= 0.5 || ...
        normalized_detection_threshold ~= 1 || centroid_weight_exponent < 0 || ...
        centroid_weight_exponent > 2
    error('P53:InvalidRealControl', 'Fixed scene spacings, threshold, or centroid exponent are outside reviewed limits.');
end
if ~isrow(minimum_component_cell_sweep) || ...
        numel(minimum_component_cell_sweep) < 3 || ...
        numel(minimum_component_cell_sweep) > maximum_sweep_cases || ...
        ~isreal(minimum_component_cell_sweep) || ...
        any(~isfinite(minimum_component_cell_sweep)) || ...
        islogical(minimum_component_cell_sweep) || ...
        any(minimum_component_cell_sweep ~= floor(minimum_component_cell_sweep)) || ...
        any(minimum_component_cell_sweep < 1) || ...
        any(minimum_component_cell_sweep > number_range_bins*number_velocity_bins) || ...
        any(diff(minimum_component_cell_sweep) <= 0) || ...
        ~any(minimum_component_cell_sweep == minimum_component_cells)
    error('P53:InvalidSizeSweep', 'Minimum-cell sweep must be an increasing integer row vector containing the baseline.');
end
if ~isrow(centroid_weight_exponent_sweep) || ...
        numel(centroid_weight_exponent_sweep) < 3 || ...
        numel(centroid_weight_exponent_sweep) > maximum_sweep_cases || ...
        ~isreal(centroid_weight_exponent_sweep) || ...
        any(~isfinite(centroid_weight_exponent_sweep)) || ...
        islogical(centroid_weight_exponent_sweep) || ...
        any(diff(centroid_weight_exponent_sweep) <= 0) || ...
        centroid_weight_exponent_sweep(1) < 0 || ...
        centroid_weight_exponent_sweep(end) > 2 || ...
        ~any(centroid_weight_exponent_sweep == centroid_weight_exponent)
    error('P53:InvalidWeightSweep', 'Weight sweep must increase from 0 through the baseline without exceeding 2.');
end

%% Deterministic range-Doppler detector scene
% Rows are range; columns are signed radial velocity. Positive velocity is
% approaching. The score is CUT power / detector threshold, so score > 1 is
% a threshold crossing. Seeded background texture is normalized into
% [0.25, 0.45], guaranteeing that background alone cannot cross threshold.
private_stream = RandStream('mt19937ar', 'Seed', random_seed);
range_axis_m = (0:number_range_bins-1)*range_bin_spacing_m;
velocity_axis_mps = ((0:number_velocity_bins-1) - floor(number_velocity_bins/2))*velocity_bin_spacing_mps;
[velocity_grid_mps, range_grid_m] = meshgrid(velocity_axis_mps, range_axis_m);

background_texture = abs(randn(private_stream, number_range_bins, number_velocity_bins));
background_texture = background_texture/max(background_texture(:));
normalized_score = 0.25 + 0.20*background_texture;

% [true range (m), true velocity (m/s), peak ratio, range width (bins), velocity width (bins)]
target_truth = [365.25  4.20  5.0  1.35  1.10; ...
                742.50 -6.25  3.6  1.05  1.30];
for target_index = 1:size(target_truth, 1)
    range_offset_bins = (range_grid_m - target_truth(target_index, 1))/range_bin_spacing_m;
    velocity_offset_bins = (velocity_grid_mps - target_truth(target_index, 2))/velocity_bin_spacing_mps;
    target_shape = target_truth(target_index, 3)*exp(-0.5*(...
        (range_offset_bins/target_truth(target_index, 4)).^2 + ...
        (velocity_offset_bins/target_truth(target_index, 5)).^2));
    normalized_score = normalized_score + target_shape;
end

% An asymmetric shoulder remains connected to target 1 and makes weighting
% visibly different from a geometric center. Two-cell sidelobes and isolated
% false detections are deliberately disconnected nuisance components.
shoulder = 1.8*exp(-0.5*(...
    ((range_grid_m - (target_truth(1, 1) + 1.8*range_bin_spacing_m))/(0.70*range_bin_spacing_m)).^2 + ...
    ((velocity_grid_mps - (target_truth(1, 2) + 0.8*velocity_bin_spacing_mps))/(0.65*velocity_bin_spacing_mps)).^2));
normalized_score = normalized_score + shoulder;

sidelobe_cells = [22 17 1.42; 22 18 1.24; 55 52 1.38; 56 52 1.20];
isolated_false_cells = [10 55 1.31; 35 9 1.27; 64 31 1.34];
for nuisance_index = 1:size(sidelobe_cells, 1)
    normalized_score(sidelobe_cells(nuisance_index, 1), sidelobe_cells(nuisance_index, 2)) = ...
        sidelobe_cells(nuisance_index, 3);
end
for nuisance_index = 1:size(isolated_false_cells, 1)
    normalized_score(isolated_false_cells(nuisance_index, 1), isolated_false_cells(nuisance_index, 2)) = ...
        isolated_false_cells(nuisance_index, 3);
end

detection_mask = normalized_score > normalized_detection_threshold;

figure('Name', 'P53 Figure 1: normalized detector score', 'Tag', 'P53');
imagesc(velocity_axis_mps, range_axis_m, normalized_score);
axis xy;
colorbar;
hold on;
plot(target_truth(:, 2), target_truth(:, 1), 'wx', 'LineWidth', 2, 'MarkerSize', 10);
contour(velocity_axis_mps, range_axis_m, normalized_score, ...
    [normalized_detection_threshold normalized_detection_threshold], 'w--', 'LineWidth', 1.2);
xlabel('Signed radial velocity (m/s; positive approaching)');
ylabel('Range (m)');
title('Detector score = CUT power / threshold; dashed contour is score 1');

%% Local-maximum selection: one deterministic representative per plateau
% A cell is a peak when no detected 3-by-3 neighbor is stronger. Equal
% plateaus keep only the first row-major cell, making reruns reproducible.
local_maximum_mask = select_local_maxima(normalized_score, detection_mask);

%% Explicit 8-connected grouping and excess-power weighted reports
% For component C, w=(score-1)^p and
%   range_hat = sum_C(w*range)/sum_C(w), velocity_hat = sum_C(w*velocity)/sum_C(w).
% The queue traversal, component labels, filtering, and report metrics are
% visible in group_detection_cells below; no image-processing toolbox is used.
[component_labels, baseline_reports, all_component_count] = group_detection_cells(...
    normalized_score, detection_mask, local_maximum_mask, range_axis_m, ...
    velocity_axis_mps, minimum_component_cells, centroid_weight_exponent, ...
    maximum_component_queue_cells);

baseline_truth_metrics = compare_known_truth_components(...
    baseline_reports, component_labels, target_truth(:, 1:2), ...
    range_axis_m, velocity_axis_mps);

figure('Name', 'P53 Figure 2: cells, peaks, and components', 'Tag', 'P53');
subplot(1, 3, 1);
imagesc(velocity_axis_mps, range_axis_m, detection_mask);
axis xy;
xlabel('Velocity (m/s)'); ylabel('Range (m)');
title(sprintf('Threshold cells: %d', nnz(detection_mask)));
subplot(1, 3, 2);
imagesc(velocity_axis_mps, range_axis_m, local_maximum_mask);
axis xy;
xlabel('Velocity (m/s)'); ylabel('Range (m)');
title(sprintf('Local maxima: %d', nnz(local_maximum_mask)));
subplot(1, 3, 3);
imagesc(velocity_axis_mps, range_axis_m, component_labels);
axis xy;
xlabel('Velocity (m/s)'); ylabel('Range (m)');
title(sprintf('Components: %d; accepted reports: %d', all_component_count, numel(baseline_reports)));

figure('Name', 'P53 Figure 3: recovered target reports', 'Tag', 'P53');
imagesc(velocity_axis_mps, range_axis_m, normalized_score);
axis xy;
colorbar;
hold on;
plot(target_truth(:, 2), target_truth(:, 1), 'wx', 'LineWidth', 2, 'MarkerSize', 10);
for report_index = 1:numel(baseline_reports)
    plot(baseline_reports(report_index).velocity_mps, baseline_reports(report_index).range_m, ...
        'ro', 'LineWidth', 1.6, 'MarkerSize', 9);
    text(baseline_reports(report_index).velocity_mps, baseline_reports(report_index).range_m, ...
        sprintf('  C%d: %d cells', baseline_reports(report_index).component_id, ...
        baseline_reports(report_index).cell_count), 'Color', 'w', 'FontWeight', 'bold');
end
xlabel('Signed radial velocity (m/s; positive approaching)');
ylabel('Range (m)');
title('Truth (white x) and grouped weighted reports (red o)');

%% Sweep 1: change only the minimum accepted component size
size_sweep_report_count = zeros(size(minimum_component_cell_sweep));
size_sweep_truth_count = zeros(size(minimum_component_cell_sweep));
for sweep_index = 1:numel(minimum_component_cell_sweep)
    [~, sweep_reports, ~] = group_detection_cells(...
        normalized_score, detection_mask, local_maximum_mask, range_axis_m, ...
        velocity_axis_mps, minimum_component_cell_sweep(sweep_index), ...
        centroid_weight_exponent, maximum_component_queue_cells);
    size_sweep_report_count(sweep_index) = numel(sweep_reports);
    report_components = [sweep_reports.component_id];
    truth_components = baseline_truth_metrics.component_id;
    size_sweep_truth_count(sweep_index) = sum(ismember(truth_components, report_components));
end

figure('Name', 'P53 Figure 4: minimum component size sweep', 'Tag', 'P53');
plot(minimum_component_cell_sweep, size_sweep_report_count, 'o-', 'LineWidth', 1.5);
hold on;
plot(minimum_component_cell_sweep, size_sweep_truth_count, 's-', 'LineWidth', 1.5);
grid on;
xlabel('Minimum accepted component size (cells)');
ylabel('Count (reports or retained known targets)');
legend('All accepted reports', 'Known target components retained', 'Location', 'best');
title('One-variable sweep: reject small nuisance components, then risk weak-target loss');

%% Sweep 2: change only the excess-power centroid exponent
weight_sweep_range_error_m = zeros(numel(centroid_weight_exponent_sweep), size(target_truth, 1));
weight_sweep_velocity_error_mps = zeros(numel(centroid_weight_exponent_sweep), size(target_truth, 1));
for sweep_index = 1:numel(centroid_weight_exponent_sweep)
    [sweep_labels, sweep_reports, ~] = group_detection_cells(...
        normalized_score, detection_mask, local_maximum_mask, range_axis_m, ...
        velocity_axis_mps, minimum_component_cells, ...
        centroid_weight_exponent_sweep(sweep_index), maximum_component_queue_cells);
    sweep_metrics = compare_known_truth_components(...
        sweep_reports, sweep_labels, target_truth(:, 1:2), range_axis_m, velocity_axis_mps);
    weight_sweep_range_error_m(sweep_index, :) = sweep_metrics.range_error_m;
    weight_sweep_velocity_error_mps(sweep_index, :) = sweep_metrics.velocity_error_mps;
end

figure('Name', 'P53 Figure 5: centroid weighting sweep', 'Tag', 'P53');
subplot(2, 1, 1);
plot(centroid_weight_exponent_sweep, weight_sweep_range_error_m, 'o-', 'LineWidth', 1.5);
grid on;
xlabel('Excess-power weight exponent p');
ylabel('Reported range error (m)');
title('p=0 is geometric; larger p pulls toward strong cells');
subplot(2, 1, 2);
plot(centroid_weight_exponent_sweep, weight_sweep_velocity_error_mps, 'o-', 'LineWidth', 1.5);
grid on;
xlabel('Excess-power weight exponent p');
ylabel('Reported velocity error (m/s)');
legend('Target 1', 'Target 2', 'Location', 'best');

%% Broken case: promote every local maximum directly to a tracker report
% Peak suppression reduces adjacent-cell duplicates but still promotes
% disconnected sidelobes and isolated false cells. It also quantizes position
% to cell centers and has no component extent or shape information.
[broken_rows, broken_columns] = find(local_maximum_mask);
broken_report_count = numel(broken_rows);
recovered_report_count = numel(baseline_reports);

figure('Name', 'P53 Figure 6: broken peak reports and grouped recovery', 'Tag', 'P53');
subplot(1, 2, 1);
imagesc(velocity_axis_mps, range_axis_m, normalized_score);
axis xy; hold on;
plot(velocity_axis_mps(broken_columns), range_axis_m(broken_rows), 'rx', 'LineWidth', 1.5);
xlabel('Velocity (m/s)'); ylabel('Range (m)');
title(sprintf('BROKEN: %d local maxima become reports', broken_report_count));
subplot(1, 2, 2);
imagesc(velocity_axis_mps, range_axis_m, normalized_score);
axis xy; hold on;
for report_index = 1:numel(baseline_reports)
    plot(baseline_reports(report_index).velocity_mps, baseline_reports(report_index).range_m, ...
        'go', 'LineWidth', 1.8, 'MarkerSize', 9);
end
xlabel('Velocity (m/s)'); ylabel('Range (m)');
title(sprintf('RECOVERY: %d grouped, filtered reports', recovered_report_count));

%% Metrics and reviewed-run assertions
fprintf('P53 baseline: %d threshold cells, %d local maxima, %d components, %d accepted reports.\n', ...
    nnz(detection_mask), nnz(local_maximum_mask), all_component_count, recovered_report_count);
for target_index = 1:size(target_truth, 1)
    fprintf(['Target %d: range error %.3f m, velocity error %.3f m/s, ' ...
        'shape uncertainty proxy [%.3f m, %.3f m/s].\n'], target_index, ...
        baseline_truth_metrics.range_error_m(target_index), ...
        baseline_truth_metrics.velocity_error_mps(target_index), ...
        baseline_truth_metrics.range_uncertainty_proxy_m(target_index), ...
        baseline_truth_metrics.velocity_uncertainty_proxy_mps(target_index));
end
fprintf('Broken local-max reports: %d; grouped recovery reports: %d.\n', ...
    broken_report_count, recovered_report_count);
fprintf('Shape uncertainty is an uncalibrated morphology proxy, not tracker covariance R.\n');

reviewed_run = random_seed == 5301 && number_range_bins == 72 && ...
    number_velocity_bins == 65 && range_bin_spacing_m == 15 && ...
    velocity_bin_spacing_mps == 0.5 && minimum_component_cells == 3 && ...
    centroid_weight_exponent == 1 && ...
    isequal(minimum_component_cell_sweep, [1 3 18]) && ...
    isequal(centroid_weight_exponent_sweep, [0 1 2]);
if reviewed_run
    assert(recovered_report_count == size(target_truth, 1), ...
        'Reviewed baseline should produce one accepted report per physical target.');
    assert(broken_report_count > recovered_report_count, ...
        'Broken peak-only reporting should over-report nuisance maxima.');
    assert(all(abs(baseline_truth_metrics.range_error_m) < range_bin_spacing_m), ...
        'Reviewed range centroids should remain within one range bin of truth.');
    assert(all(abs(baseline_truth_metrics.velocity_error_mps) < velocity_bin_spacing_mps), ...
        'Reviewed velocity centroids should remain within one velocity bin of truth.');
    assert(isequal(size_sweep_report_count, [7 2 1]), ...
        'Reviewed minimum-size sweep should reject nuisance components, then the compact target.');
    assert(isequal(size_sweep_truth_count, [2 2 1]), ...
        'Reviewed minimum-size sweep should retain two, two, then one known target component.');
end

results.random_seed = random_seed;
results.baseline_detection_cell_count = nnz(detection_mask);
results.baseline_local_maximum_count = nnz(local_maximum_mask);
results.baseline_component_count = all_component_count;
results.baseline_report_count = recovered_report_count;
results.baseline_reports = baseline_reports;
results.baseline_truth_metrics = baseline_truth_metrics;
results.minimum_component_cell_sweep = minimum_component_cell_sweep;
results.size_sweep_report_count = size_sweep_report_count;
results.size_sweep_truth_count = size_sweep_truth_count;
results.centroid_weight_exponent_sweep = centroid_weight_exponent_sweep;
results.weight_sweep_range_error_m = weight_sweep_range_error_m;
results.weight_sweep_velocity_error_mps = weight_sweep_velocity_error_mps;
results.broken_report_count = broken_report_count;
results.recovered_report_count = recovered_report_count;

%% Transparent local operations
function local_maximum_mask = select_local_maxima(score, detection_mask)
if ~ismatrix(score) || ~isequal(size(score), size(detection_mask)) || ...
        ~isreal(score) || any(~isfinite(score(:))) || any(score(:) < 0) || ...
        ~islogical(detection_mask)
    error('P53:InvalidPeakInput', 'Score and logical detection mask must be finite, real, and equal-sized.');
end
[number_rows, number_columns] = size(score);
local_maximum_mask = false(number_rows, number_columns);
plateau_visited = false(number_rows, number_columns);
plateau_queue_rows = zeros(number_rows*number_columns, 1);
plateau_queue_columns = zeros(number_rows*number_columns, 1);
for seed_row = 1:number_rows
    for seed_column = 1:number_columns
        if ~detection_mask(seed_row, seed_column) || plateau_visited(seed_row, seed_column)
            continue;
        end
        plateau_value = score(seed_row, seed_column);
        plateau_is_local_maximum = true;
        queue_head = 1;
        queue_tail = 1;
        plateau_queue_rows(1) = seed_row;
        plateau_queue_columns(1) = seed_column;
        plateau_visited(seed_row, seed_column) = true;
        while queue_head <= queue_tail
            current_row = plateau_queue_rows(queue_head);
            current_column = plateau_queue_columns(queue_head);
            queue_head = queue_head + 1;
            for row_step = -1:1
                for column_step = -1:1
                    if row_step == 0 && column_step == 0
                        continue;
                    end
                    neighbor_row = current_row + row_step;
                    neighbor_column = current_column + column_step;
                    if neighbor_row < 1 || neighbor_row > number_rows || ...
                            neighbor_column < 1 || neighbor_column > number_columns || ...
                            ~detection_mask(neighbor_row, neighbor_column)
                        continue;
                    end
                    neighbor_value = score(neighbor_row, neighbor_column);
                    if neighbor_value > plateau_value
                        plateau_is_local_maximum = false;
                    elseif neighbor_value == plateau_value && ...
                            ~plateau_visited(neighbor_row, neighbor_column)
                        queue_tail = queue_tail + 1;
                        plateau_queue_rows(queue_tail) = neighbor_row;
                        plateau_queue_columns(queue_tail) = neighbor_column;
                        plateau_visited(neighbor_row, neighbor_column) = true;
                    end
                end
            end
        end
        if plateau_is_local_maximum
            local_maximum_mask(seed_row, seed_column) = true;
        end
    end
end
end

function [labels, reports, component_count] = group_detection_cells(...
        score, detection_mask, local_maximum_mask, range_axis_m, ...
        velocity_axis_mps, minimum_cells, weight_exponent, maximum_queue_cells)
if ~ismatrix(score) || ~isreal(score) || any(~isfinite(score(:))) || ...
        any(score(:) < 0) || ...
        ~isequal(size(score), size(detection_mask), size(local_maximum_mask)) || ...
        ~islogical(detection_mask) || ~islogical(local_maximum_mask)
    error('P53:InvalidGroupInput', 'Score and logical masks must be finite, real, and equal-sized.');
end
[number_rows, number_columns] = size(score);
if ~isrow(range_axis_m) || numel(range_axis_m) ~= number_rows || ...
        ~isrow(velocity_axis_mps) || numel(velocity_axis_mps) ~= number_columns || ...
        any(~isfinite(range_axis_m)) || any(~isfinite(velocity_axis_mps)) || ...
        any(diff(range_axis_m) <= 0) || any(diff(velocity_axis_mps) <= 0) || ...
        any(diff(range_axis_m) ~= range_axis_m(2) - range_axis_m(1)) || ...
        any(diff(velocity_axis_mps) ~= velocity_axis_mps(2) - velocity_axis_mps(1))
    error('P53:InvalidAxes', 'Axes must be finite, uniform, increasing row vectors matching the scene.');
end
if ~isscalar(minimum_cells) || islogical(minimum_cells) || ~isfinite(minimum_cells) || ...
        minimum_cells ~= floor(minimum_cells) || minimum_cells < 1 || ...
        minimum_cells > number_rows*number_columns || ...
        ~isscalar(weight_exponent) || islogical(weight_exponent) || ~isreal(weight_exponent) || ...
        ~isfinite(weight_exponent) || weight_exponent < 0 || weight_exponent > 2 || ...
        ~isscalar(maximum_queue_cells) || islogical(maximum_queue_cells) || ...
        ~isfinite(maximum_queue_cells) || ...
        maximum_queue_cells ~= floor(maximum_queue_cells) || ...
        maximum_queue_cells < number_rows*number_columns
    error('P53:InvalidGroupControl', 'Grouping controls are malformed or exceed reviewed bounds.');
end
if any(detection_mask(:) & score(:) <= 1)
    error('P53:InvalidDetectionMask', 'Every detected cell must have normalized score greater than one.');
end

labels = zeros(number_rows, number_columns);
queue_rows = zeros(maximum_queue_cells, 1);
queue_columns = zeros(maximum_queue_cells, 1);
empty_report = struct('component_id', 0, 'range_m', 0, 'velocity_mps', 0, ...
    'peak_range_m', 0, 'peak_velocity_mps', 0, 'peak_score_ratio', 0, ...
    'integrated_excess_ratio', 0, 'cell_count', 0, 'range_extent_m', 0, ...
    'velocity_extent_mps', 0, 'effective_cell_count', 0, ...
    'range_uncertainty_proxy_m', 0, 'velocity_uncertainty_proxy_mps', 0);
reports = repmat(empty_report, 0, 1);
component_count = 0;

for seed_row = 1:number_rows
    for seed_column = 1:number_columns
        if ~detection_mask(seed_row, seed_column) || labels(seed_row, seed_column) ~= 0
            continue;
        end
        component_count = component_count + 1;
        queue_head = 1;
        queue_tail = 1;
        queue_rows(1) = seed_row;
        queue_columns(1) = seed_column;
        labels(seed_row, seed_column) = component_count;
        while queue_head <= queue_tail
            current_row = queue_rows(queue_head);
            current_column = queue_columns(queue_head);
            queue_head = queue_head + 1;
            for row_step = -1:1
                for column_step = -1:1
                    if row_step == 0 && column_step == 0
                        continue;
                    end
                    neighbor_row = current_row + row_step;
                    neighbor_column = current_column + column_step;
                    if neighbor_row < 1 || neighbor_row > number_rows || ...
                            neighbor_column < 1 || neighbor_column > number_columns
                        continue;
                    end
                    if detection_mask(neighbor_row, neighbor_column) && ...
                            labels(neighbor_row, neighbor_column) == 0
                        queue_tail = queue_tail + 1;
                        if queue_tail > maximum_queue_cells
                            error('P53:QueueOverflow', 'Connected-component queue exceeded its fixed bound.');
                        end
                        queue_rows(queue_tail) = neighbor_row;
                        queue_columns(queue_tail) = neighbor_column;
                        labels(neighbor_row, neighbor_column) = component_count;
                    end
                end
            end
        end

        component_rows = queue_rows(1:queue_tail);
        component_columns = queue_columns(1:queue_tail);
        component_cell_count = queue_tail;
        if component_cell_count < minimum_cells
            continue;
        end
        component_linear_indices = sub2ind(size(score), component_rows, component_columns);
        component_excess = score(component_linear_indices) - 1;
        weights = component_excess.^weight_exponent;
        weight_sum = sum(weights);
        if ~isfinite(weight_sum) || weight_sum <= 0
            error('P53:DegenerateWeights', 'Accepted components require positive finite centroid weight.');
        end
        component_ranges = reshape(range_axis_m(component_rows), [], 1);
        component_velocities = reshape(velocity_axis_mps(component_columns), [], 1);
        estimated_range_m = sum(weights.*component_ranges)/weight_sum;
        estimated_velocity_mps = sum(weights.*component_velocities)/weight_sum;
        effective_cell_count = weight_sum^2/sum(weights.^2);
        range_second_moment = sum(weights.*(component_ranges - estimated_range_m).^2)/weight_sum;
        velocity_second_moment = sum(weights.*(component_velocities - estimated_velocity_mps).^2)/weight_sum;
        range_bin_spacing = min(diff(range_axis_m));
        velocity_bin_spacing = min(diff(velocity_axis_mps));
        range_uncertainty_proxy_m = sqrt(range_second_moment/effective_cell_count + range_bin_spacing^2/12);
        velocity_uncertainty_proxy_mps = sqrt(velocity_second_moment/effective_cell_count + velocity_bin_spacing^2/12);

        peak_candidates = component_linear_indices(local_maximum_mask(component_linear_indices));
        if isempty(peak_candidates)
            [~, peak_offset] = max(score(component_linear_indices));
            peak_linear_index = component_linear_indices(peak_offset);
        else
            [~, peak_offset] = max(score(peak_candidates));
            peak_linear_index = peak_candidates(peak_offset);
        end
        [peak_row, peak_column] = ind2sub(size(score), peak_linear_index);

        report = empty_report;
        report.component_id = component_count;
        report.range_m = estimated_range_m;
        report.velocity_mps = estimated_velocity_mps;
        report.peak_range_m = range_axis_m(peak_row);
        report.peak_velocity_mps = velocity_axis_mps(peak_column);
        report.peak_score_ratio = score(peak_linear_index);
        report.integrated_excess_ratio = sum(component_excess);
        report.cell_count = component_cell_count;
        report.range_extent_m = max(component_ranges) - min(component_ranges) + range_bin_spacing;
        report.velocity_extent_mps = max(component_velocities) - min(component_velocities) + velocity_bin_spacing;
        report.effective_cell_count = effective_cell_count;
        report.range_uncertainty_proxy_m = range_uncertainty_proxy_m;
        report.velocity_uncertainty_proxy_mps = velocity_uncertainty_proxy_mps;
        reports(end + 1, 1) = report; %#ok<AGROW>
    end
end
end

function metrics = compare_known_truth_components(...
        reports, labels, truth_position, range_axis_m, velocity_axis_mps)
if size(truth_position, 2) ~= 2 || any(~isfinite(truth_position(:)))
    error('P53:InvalidTruth', 'Known synthetic truth must be finite [range, velocity] rows.');
end
target_count = size(truth_position, 1);
metrics.component_id = zeros(1, target_count);
metrics.range_error_m = nan(1, target_count);
metrics.velocity_error_mps = nan(1, target_count);
metrics.range_uncertainty_proxy_m = nan(1, target_count);
metrics.velocity_uncertainty_proxy_mps = nan(1, target_count);
for target_index = 1:target_count
    [~, nearest_range_row] = min(abs(range_axis_m - truth_position(target_index, 1)));
    [~, nearest_velocity_column] = min(abs(velocity_axis_mps - truth_position(target_index, 2)));
    component_id = labels(nearest_range_row, nearest_velocity_column);
    metrics.component_id(target_index) = component_id;
    report_index = find([reports.component_id] == component_id, 1, 'first');
    if component_id == 0 || isempty(report_index)
        error('P53:MissingTruthReport', 'A known target center has no accepted component report.');
    end
    metrics.range_error_m(target_index) = reports(report_index).range_m - truth_position(target_index, 1);
    metrics.velocity_error_mps(target_index) = reports(report_index).velocity_mps - truth_position(target_index, 2);
    metrics.range_uncertainty_proxy_m(target_index) = reports(report_index).range_uncertainty_proxy_m;
    metrics.velocity_uncertainty_proxy_mps(target_index) = reports(report_index).velocity_uncertainty_proxy_mps;
end
end
