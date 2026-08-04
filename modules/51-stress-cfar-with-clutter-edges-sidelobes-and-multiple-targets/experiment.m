%% P51: Stress CFAR with Clutter Edges, Sidelobes, and Multiple Targets
% Guiding question: Where do standard CFAR assumptions break?
% Four detectors use the same nominal homogeneous Pfa, but their different
% training statistics respond differently when the reference cells are not
% identically distributed or contain target energy.

close(findall(groot, 'Type', 'figure', 'Tag', 'P51'));
clearvars;
clc;

%% Visible deterministic controls and immutable resource ceilings
random_seed = 5101;
range_cell_count = 256;
range_cell_spacing_m = 30;
design_false_alarm_probability = 1e-3;
training_cells_per_side = 12;
guard_cells_per_side = 3;
os_rank = 18;                         % Ascending rank among N = 24 cells.
calibration_iteration_count = 80;

clutter_edge_cell = 145;
baseline_clutter_contrast_db = 12;
clutter_contrast_sweep_db = [0 6 12 18];
strong_target_cell = 70;
weak_neighbor_cell = 82;
edge_target_cell = 141;
crowded_primary_cell = 205;
crowded_interferer_cells = [194 198 212 216];
target_cells = [strong_target_cell weak_neighbor_cell edge_target_cell ...
    crowded_primary_cell crowded_interferer_cells];
target_peak_snr_db = [28 14 14 13 20 20 20 20];
crowded_count_sweep = [0 2 4 6 7 8];
sweep_target_snr_db = 13;
sweep_interferer_excess_power_db = 20;
sweep_trial_count = 12000;

% A compact symmetric compressed-pulse response has a three-cell guardable
% mainlobe and visible sidelobes outside the guard.
target_response_offsets = -12:12;
target_power_response = [0.004 0.008 0.015 0.025 0.010 0.050 0.020 ...
    0.120 0.030 0.250 0.550 0.850 1.000 0.850 0.550 0.250 ...
    0.030 0.120 0.020 0.050 0.010 0.025 0.015 0.008 0.004];

max_range_cells = 320;
max_training_cells_per_side = 24;
max_guard_cells_per_side = 8;
max_targets = 10;
max_sweep_cases = 8;
max_sweep_trials = 15000;
max_calibration_iterations = 100;
max_generated_random_values = 400000;
max_stored_numeric_values = 1200000;
max_training_sample_visits = 2000000;
max_figure_groups = 7;

%% Reject malformed, ambiguous, or unbounded controls before allocation
if max_range_cells ~= 320 || max_training_cells_per_side ~= 24 || ...
        max_guard_cells_per_side ~= 8 || max_targets ~= 10 || ...
        max_sweep_cases ~= 8 || max_sweep_trials ~= 15000 || ...
        max_calibration_iterations ~= 100 || ...
        max_generated_random_values ~= 400000 || ...
        max_stored_numeric_values ~= 1200000 || ...
        max_training_sample_visits ~= 2000000 || max_figure_groups ~= 7
    error('P51:CeilingControls', 'Reviewed resource ceilings must remain fixed.');
end
integer_controls = {random_seed range_cell_count training_cells_per_side ...
    guard_cells_per_side os_rank calibration_iteration_count ...
    clutter_edge_cell strong_target_cell weak_neighbor_cell edge_target_cell ...
    crowded_primary_cell sweep_trial_count max_range_cells ...
    max_training_cells_per_side max_guard_cells_per_side max_targets ...
    max_sweep_cases max_sweep_trials max_calibration_iterations ...
    max_generated_random_values max_stored_numeric_values ...
    max_training_sample_visits max_figure_groups};
for control_index = 1:numel(integer_controls)
    control_value = integer_controls{control_index};
    if ~isscalar(control_value) || ~isnumeric(control_value) || ...
            islogical(control_value) || ~isreal(control_value) || ...
            ~isfinite(control_value) || control_value ~= fix(control_value)
        error('P51:IntegerControls', ...
            'Integer controls must be finite real integer scalars.');
    end
end
real_controls = {range_cell_spacing_m design_false_alarm_probability ...
    baseline_clutter_contrast_db sweep_target_snr_db ...
    sweep_interferer_excess_power_db};
for control_index = 1:numel(real_controls)
    control_value = real_controls{control_index};
    if ~isscalar(control_value) || ~isnumeric(control_value) || ...
            islogical(control_value) || ~isreal(control_value) || ...
            ~isfinite(control_value)
        error('P51:RealControls', ...
            'Physical controls must be finite real scalars.');
    end
end
if random_seed ~= 5101 || range_cell_count < 128 || ...
        range_cell_count > max_range_cells || range_cell_spacing_m <= 0
    error('P51:DeterminismOrRange', ...
        'Keep the reviewed seed and bounded positive range axis.');
end
if design_false_alarm_probability < 1e-6 || ...
        design_false_alarm_probability >= 0.1
    error('P51:Pfa', 'Design Pfa must lie from 1e-6 inclusive to 0.1 exclusive.');
end
if training_cells_per_side < 2 || ...
        training_cells_per_side > max_training_cells_per_side || ...
        guard_cells_per_side < 1 || ...
        guard_cells_per_side > max_guard_cells_per_side
    error('P51:Stencil', 'Training or guard geometry exceeds reviewed bounds.');
end
training_cell_count = 2*training_cells_per_side;
stencil_half_width = training_cells_per_side+guard_cells_per_side;
if os_rank < 1 || os_rank > training_cell_count
    error('P51:Rank', 'OS rank must index the ascending training powers.');
end
if clutter_edge_cell <= stencil_half_width || ...
        clutter_edge_cell > range_cell_count-stencil_half_width
    error('P51:Edge', 'The clutter edge must lie inside the full-stencil region.');
end
if ~isnumeric(target_cells) || ~isreal(target_cells) || ...
        any(~isfinite(target_cells)) || any(target_cells ~= fix(target_cells)) || ...
        isempty(target_cells) || numel(target_cells) > max_targets || ...
        numel(unique(target_cells)) ~= numel(target_cells) || ...
        any(target_cells <= stencil_half_width) || ...
        any(target_cells > range_cell_count-stencil_half_width)
    error('P51:Targets', 'Target cells must be unique valid full-stencil CUTs.');
end
if numel(target_peak_snr_db) ~= numel(target_cells) || ...
        any(~isfinite(target_peak_snr_db)) || ...
        any(target_peak_snr_db < -20) || any(target_peak_snr_db > 40)
    error('P51:TargetPowers', 'Every target needs one bounded finite peak SNR.');
end
if ~isnumeric(target_response_offsets) || ~isreal(target_response_offsets) || ...
        any(~isfinite(target_response_offsets)) || ...
        any(target_response_offsets ~= fix(target_response_offsets)) || ...
        numel(target_response_offsets) ~= numel(target_power_response) || ...
        mod(numel(target_power_response), 2) ~= 1 || ...
        any(diff(target_response_offsets) ~= 1) || ...
        target_response_offsets(1) ~= -target_response_offsets(end) || ...
        any(~isfinite(target_power_response)) || ...
        any(target_power_response < 0) || max(target_power_response) ~= 1 || ...
        max(abs(target_power_response-fliplr(target_power_response))) > 1e-12
    error('P51:TargetResponse', ...
        'Target response must be bounded, symmetric, contiguous, and unit peak.');
end
if ~isnumeric(clutter_contrast_sweep_db) || ...
        ~isreal(clutter_contrast_sweep_db) || ...
        any(~isfinite(clutter_contrast_sweep_db)) || ...
        numel(clutter_contrast_sweep_db) < 3 || ...
        numel(clutter_contrast_sweep_db) > max_sweep_cases || ...
        any(diff(clutter_contrast_sweep_db) <= 0) || ...
        ~any(clutter_contrast_sweep_db == baseline_clutter_contrast_db) || ...
        clutter_contrast_sweep_db(1) < 0 || ...
        clutter_contrast_sweep_db(end) > 24
    error('P51:ContrastSweep', ...
        'Contrast sweep must increase, include baseline, and stay bounded.');
end
if ~isnumeric(crowded_count_sweep) || ~isreal(crowded_count_sweep) || ...
        any(~isfinite(crowded_count_sweep)) || ...
        any(crowded_count_sweep ~= fix(crowded_count_sweep)) || ...
        numel(crowded_count_sweep) < 3 || ...
        numel(crowded_count_sweep) > max_sweep_cases || ...
        any(diff(crowded_count_sweep) <= 0) || crowded_count_sweep(1) ~= 0 || ...
        ~any(crowded_count_sweep == training_cell_count-os_rank) || ...
        ~any(crowded_count_sweep == training_cell_count-os_rank+1) || ...
        crowded_count_sweep(end) > training_cell_count
    error('P51:CrowdedSweep', ...
        'Count sweep must cross the OS outlier-capacity boundary within N.');
end
if sweep_target_snr_db < -20 || sweep_target_snr_db > 40 || ...
        sweep_interferer_excess_power_db < -20 || ...
        sweep_interferer_excess_power_db > 40 || ...
        sweep_trial_count < 1000 || sweep_trial_count > max_sweep_trials || ...
        calibration_iteration_count < 40 || ...
        calibration_iteration_count > max_calibration_iterations
    error('P51:WorkBounds', 'Sweep or calibration work exceeds reviewed bounds.');
end
estimated_generated_random_values = range_cell_count + ...
    sweep_trial_count*(training_cell_count+2);
estimated_stored_numeric_values = 40*range_cell_count + ...
    sweep_trial_count*(3*training_cell_count+12);
estimated_training_sample_visits = ...
    (1+numel(clutter_contrast_sweep_db))*range_cell_count*training_cell_count + ...
    numel(crowded_count_sweep)*sweep_trial_count*training_cell_count;
if estimated_generated_random_values > max_generated_random_values || ...
        estimated_stored_numeric_values > max_stored_numeric_values || ...
        estimated_training_sample_visits > max_training_sample_visits
    error('P51:ResourceCeiling', ...
        'Reviewed random, storage, or training-visit ceiling exceeded.');
end

%% Calibrate each statistic to the same homogeneous exponential-noise Pfa
ca_scale_factor = training_cell_count*( ...
    design_false_alarm_probability^(-1/training_cell_count)-1);
go_scale_factor = calibrated_variant_scale(training_cells_per_side, ...
    design_false_alarm_probability, 'GO', calibration_iteration_count);
so_scale_factor = calibrated_variant_scale(training_cells_per_side, ...
    design_false_alarm_probability, 'SO', calibration_iteration_count);
os_scale_factor = calibrated_os_scale(training_cell_count, os_rank, ...
    design_false_alarm_probability, calibration_iteration_count);
scale_factors = [ca_scale_factor go_scale_factor so_scale_factor os_scale_factor];
calibrated_homogeneous_pfa = [ ...
    (1+ca_scale_factor/training_cell_count)^(-training_cell_count) ...
    homogeneous_variant_pfa(go_scale_factor, training_cells_per_side, 'GO') ...
    homogeneous_variant_pfa(so_scale_factor, training_cells_per_side, 'SO') ...
    homogeneous_os_pfa(os_scale_factor, training_cell_count, os_rank)];
assert(max(abs(calibrated_homogeneous_pfa-design_false_alarm_probability)) < 1e-12);

%% Build one seeded scene with every named stressor visible
private_stream = RandStream('mt19937ar', 'Seed', random_seed);
range_cell = (1:range_cell_count).';
range_km = range_cell*range_cell_spacing_m/1000;
unit_background_power = -log(max(rand(private_stream, range_cell_count, 1), realmin));
low_side_mean_power = 1 + 0.20*cos(2*pi*range_cell/83);
clutter_multiplier = 10^(baseline_clutter_contrast_db/10);
high_side = range_cell >= clutter_edge_cell;
nonuniform_hump = 1 + 2.5*exp(-0.5*((range_cell-220)/18).^2);
background_mean_power = low_side_mean_power.* ...
    (1+(clutter_multiplier-1)*double(high_side)).*nonuniform_hump;
received_power = background_mean_power.*unit_background_power;
truth_target_mask = false(range_cell_count, 1);
modeled_target_response_power = zeros(range_cell_count, 1);
dominant_response_owner = zeros(range_cell_count, 1);
dominant_response_power = zeros(range_cell_count, 1);
for target_index = 1:numel(target_cells)
    center_cell = target_cells(target_index);
    truth_target_mask(center_cell) = true;
    peak_power = background_mean_power(center_cell)*10^(target_peak_snr_db(target_index)/10);
    response_cells = center_cell+target_response_offsets;
    inside = response_cells >= 1 & response_cells <= range_cell_count;
    target_addition = peak_power*target_power_response(inside).';
    active_cells = response_cells(inside);
    received_power(active_cells) = received_power(active_cells)+target_addition;
    modeled_target_response_power(active_cells) = ...
        modeled_target_response_power(active_cells)+target_addition;
    owner_update = target_addition > dominant_response_power(active_cells);
    dominant_response_power(active_cells(owner_update)) = target_addition(owner_update);
    dominant_response_owner(active_cells(owner_update)) = target_index;
end
response_artifact_mask = modeled_target_response_power > 0 & ~truth_target_mask;

figure('Name', 'P51 combined stress scene', 'Tag', 'P51');
semilogy(range_km, max(received_power, 1e-6), 'k-', 'LineWidth', 1); hold on;
semilogy(range_km, background_mean_power, 'c--', 'LineWidth', 1.4);
semilogy(range_km(target_cells), received_power(target_cells), 'ko', ...
    'MarkerFaceColor', 'y');
plot([range_km(clutter_edge_cell) range_km(clutter_edge_cell)], ylim, ...
    'm:', 'LineWidth', 1.4);
grid on; xlabel('Range (km)'); ylabel('Square-law power (linear units)');
title('One scene: clutter edge, sidelobes, weak neighbors, and target crowding');
legend('Received power', 'Known mean background', 'Known target centers', ...
    'Clutter edge', 'Location', 'northwest');

%% Baseline: expose all four training statistics before each decision
ca_threshold_power = nan(range_cell_count, 1);
go_threshold_power = nan(range_cell_count, 1);
so_threshold_power = nan(range_cell_count, 1);
os_threshold_power = nan(range_cell_count, 1);
leading_mean_power = nan(range_cell_count, 1);
lagging_mean_power = nan(range_cell_count, 1);
ca_mean_power = nan(range_cell_count, 1);
os_order_power = nan(range_cell_count, 1);
ca_detection = false(range_cell_count, 1);
go_detection = false(range_cell_count, 1);
so_detection = false(range_cell_count, 1);
os_detection = false(range_cell_count, 1);
valid_cut_cells = (stencil_half_width+1):(range_cell_count-stencil_half_width);
for cut = valid_cut_cells
    leading_cells = (cut-guard_cells_per_side-training_cells_per_side): ...
        (cut-guard_cells_per_side-1);
    lagging_cells = (cut+guard_cells_per_side+1): ...
        (cut+guard_cells_per_side+training_cells_per_side);
    reference_power = received_power([leading_cells lagging_cells]);
    leading_mean_power(cut) = sum(received_power(leading_cells))/training_cells_per_side;
    lagging_mean_power(cut) = sum(received_power(lagging_cells))/training_cells_per_side;
    ca_mean_power(cut) = sum(reference_power)/training_cell_count;
    sorted_reference_power = sort(reference_power, 'ascend');
    os_order_power(cut) = sorted_reference_power(os_rank);
    ca_threshold_power(cut) = ca_scale_factor*ca_mean_power(cut);
    go_threshold_power(cut) = go_scale_factor*max( ...
        leading_mean_power(cut), lagging_mean_power(cut));
    so_threshold_power(cut) = so_scale_factor*min( ...
        leading_mean_power(cut), lagging_mean_power(cut));
    os_threshold_power(cut) = os_scale_factor*os_order_power(cut);
    ca_detection(cut) = received_power(cut) > ca_threshold_power(cut);
    go_detection(cut) = received_power(cut) > go_threshold_power(cut);
    so_detection(cut) = received_power(cut) > so_threshold_power(cut);
    os_detection(cut) = received_power(cut) > os_threshold_power(cut);
end
detection_mask = [ca_detection go_detection so_detection os_detection];
threshold_power = [ca_threshold_power go_threshold_power ...
    so_threshold_power os_threshold_power];
detector_names = {'CA', 'GO', 'SO', 'OS'};
assert(all(all(isfinite(threshold_power(valid_cut_cells, :)))));
assert(~any(any(detection_mask(1:stencil_half_width, :))) && ...
    ~any(any(detection_mask((range_cell_count-stencil_half_width+1):end, :))));

figure('Name', 'P51 equal-Pfa detector thresholds', 'Tag', 'P51');
for detector_index = 1:4
    subplot(2, 2, detector_index);
    semilogy(range_km, max(received_power, 1e-6), 'k-', 'LineWidth', 0.8); hold on;
    semilogy(range_km, threshold_power(:, detector_index), ...
        'LineWidth', 1.3);
    detected_cells = find(detection_mask(:, detector_index));
    semilogy(range_km(detected_cells), received_power(detected_cells), ...
        'ro', 'MarkerSize', 4);
    plot([range_km(clutter_edge_cell) range_km(clutter_edge_cell)], ylim, 'm:');
    grid on; xlabel('Range (km)'); ylabel('Square-law power (linear units)');
    title(sprintf('%s-CFAR, calibrated homogeneous Pfa = %.3g', ...
        detector_names{detector_index}, design_false_alarm_probability));
end

%% Inspect representative CUTs: every disagreement begins in these references
inspection_cells = [weak_neighbor_cell edge_target_cell crowded_primary_cell];
inspection_labels = {'weak neighbor', 'clutter-edge target', 'crowded target'};
inspection_statistics = zeros(numel(inspection_cells), 5);
figure('Name', 'P51 representative training contents', 'Tag', 'P51');
for inspection_index = 1:numel(inspection_cells)
    cut = inspection_cells(inspection_index);
    leading_cells = (cut-guard_cells_per_side-training_cells_per_side): ...
        (cut-guard_cells_per_side-1);
    lagging_cells = (cut+guard_cells_per_side+1): ...
        (cut+guard_cells_per_side+training_cells_per_side);
    inspection_reference_cells = [leading_cells lagging_cells];
    inspection_reference_power = received_power(inspection_reference_cells);
    inspection_statistics(inspection_index, :) = [received_power(cut) ...
        leading_mean_power(cut) lagging_mean_power(cut) ...
        ca_mean_power(cut) os_order_power(cut)];
    subplot(numel(inspection_cells), 1, inspection_index);
    semilogy(inspection_reference_cells, max(inspection_reference_power, 1e-6), ...
        'ko', 'MarkerFaceColor', [0.75 0.75 0.75]); hold on;
    semilogy(cut, received_power(cut), 'rp', 'MarkerSize', 10, ...
        'MarkerFaceColor', 'r');
    plot([cut-guard_cells_per_side-0.5 cut-guard_cells_per_side-0.5], ...
        ylim, 'b:');
    plot([cut+guard_cells_per_side+0.5 cut+guard_cells_per_side+0.5], ...
        ylim, 'b:');
    grid on; xlabel('Range cell'); ylabel('Linear power');
    title(sprintf('%s CUT %d: leading mean %.2f, lagging mean %.2f, OS sample %.2f', ...
        inspection_labels{inspection_index}, cut, leading_mean_power(cut), ...
        lagging_mean_power(cut), os_order_power(cut)));
end

%% Classify target misses, response artifacts, H0 crossings, and disagreements
target_detection = detection_mask(target_cells, :);
target_context = {'strong-target mainlobe', ...
    'strong-target sidelobe/reference contamination', ...
    'clutter-edge mixed references', 'multiple-target reference contamination', ...
    'multiple-target reference contamination', ...
    'multiple-target reference contamination', ...
    'multiple-target reference contamination', ...
    'multiple-target reference contamination'};
target_margin_db = 10*log10(received_power(target_cells)./threshold_power(target_cells, :));
target_training_response_count = zeros(numel(target_cells), 2);
target_miss_cause_matrix = cell(numel(target_cells), 4);
detector_miss_explanations = { ...
    'CA arithmetic mean raised by the combined references', ...
    'GO selected the larger leading/lagging mean', ...
    'SO selected the smaller side but the CUT remained below its calibrated threshold', ...
    'OS rank-18 power was raised by the reference population'};
for target_index = 1:numel(target_cells)
    cut = target_cells(target_index);
    leading_cells = (cut-guard_cells_per_side-training_cells_per_side): ...
        (cut-guard_cells_per_side-1);
    lagging_cells = (cut+guard_cells_per_side+1): ...
        (cut+guard_cells_per_side+training_cells_per_side);
    target_training_response_count(target_index, :) = [ ...
        sum(modeled_target_response_power(leading_cells) > 0) ...
        sum(modeled_target_response_power(lagging_cells) > 0)];
    for detector_index = 1:4
        if target_detection(target_index, detector_index)
            target_miss_cause_matrix{target_index, detector_index} = 'detected';
        else
            target_miss_cause_matrix{target_index, detector_index} = sprintf( ...
                '%s: %s', target_context{target_index}, ...
                detector_miss_explanations{detector_index});
        end
    end
end
assert(all(~cellfun(@isempty, target_miss_cause_matrix(:))));

h0_category_names = {'clutter-edge stencil', ...
    'target-contaminated reference stencil', 'nonuniform-background stencil', ...
    'homogeneous sample fluctuation'};
h0_category = 4*ones(range_cell_count, 1);
h0_category(abs(range_cell-clutter_edge_cell) <= stencil_half_width) = 1;
local_background_ratio = nan(range_cell_count, 1);
for cut = valid_cut_cells
    leading_cells = (cut-guard_cells_per_side-training_cells_per_side): ...
        (cut-guard_cells_per_side-1);
    lagging_cells = (cut+guard_cells_per_side+1): ...
        (cut+guard_cells_per_side+training_cells_per_side);
    if h0_category(cut) == 4 && any(modeled_target_response_power( ...
            [leading_cells lagging_cells]) > 0)
        h0_category(cut) = 2;
    end
    local_background = background_mean_power((cut-stencil_half_width): ...
        (cut+stencil_half_width));
    local_background_ratio(cut) = max(local_background)/min(local_background);
end
h0_category(local_background_ratio > 1.5 & h0_category == 4) = 3;
h0_crossing_category_counts = zeros(4, numel(h0_category_names));
response_artifact_crossing_counts = zeros(4, numel(target_cells));
for detector_index = 1:4
    detector_h0_crossings = detection_mask(:, detector_index) & ...
        ~truth_target_mask & ~response_artifact_mask;
    for category_index = 1:numel(h0_category_names)
        h0_crossing_category_counts(detector_index, category_index) = sum( ...
            detector_h0_crossings & h0_category == category_index);
    end
    for target_index = 1:numel(target_cells)
        response_artifact_crossing_counts(detector_index, target_index) = sum( ...
            detection_mask(:, detector_index) & response_artifact_mask & ...
            dominant_response_owner == target_index);
    end
    noncenter_crossing_count = sum(detection_mask(:, detector_index) & ...
        ~truth_target_mask);
    assert(noncenter_crossing_count == ...
        sum(h0_crossing_category_counts(detector_index, :)) + ...
        sum(response_artifact_crossing_counts(detector_index, :)));
end
crossing_category_names = [h0_category_names {'modeled target-response artifact'}];
crossing_category_counts = [h0_crossing_category_counts ...
    sum(response_artifact_crossing_counts, 2)];
disagreement_mask = any(detection_mask ~= detection_mask(:, 1), 2);
disagreement_cells = find(disagreement_mask);
disagreement_causes = cell(numel(disagreement_cells), 1);
for disagreement_index = 1:numel(disagreement_cells)
    cut = disagreement_cells(disagreement_index);
    if truth_target_mask(cut)
        target_index = find(target_cells == cut, 1);
        disagreement_causes{disagreement_index} = target_context{target_index};
    elseif response_artifact_mask(cut)
        disagreement_causes{disagreement_index} = sprintf( ...
            'modeled response from target CUT %d', ...
            target_cells(dominant_response_owner(cut)));
    else
        disagreement_causes{disagreement_index} = ...
            h0_category_names{h0_category(cut)};
    end
end
assert(numel(disagreement_causes) == numel(disagreement_cells));
assert(~isempty(disagreement_cells));

figure('Name', 'P51 masks and causal classification', 'Tag', 'P51');
subplot(2, 1, 1);
imagesc(range_km, 1:4, detection_mask.'); axis xy;
colormap(gca, [1 1 1; 0.85 0.10 0.10]); caxis([0 1]);
set(gca, 'YTick', 1:4, 'YTickLabel', detector_names);
xlabel('Range (km)'); ylabel('Detector');
title('Detection masks: same nominal homogeneous Pfa, different local decisions');
subplot(2, 1, 2);
bar(1:5, crossing_category_counts.', 'grouped'); grid on;
set(gca, 'XTick', 1:5, 'XTickLabel', crossing_category_names);
xtickangle(20); ylabel('Non-target threshold crossings (count)');
xlabel('Known physical/model cause');
title('Response artifacts and H0 crossings have disjoint causes');
legend(detector_names, 'Location', 'northwest');

%% Sweep 1: change only clutter-edge contrast on the shared noise realization
contrast_case_count = numel(clutter_contrast_sweep_db);
contrast_edge_crossings = zeros(contrast_case_count, 4);
contrast_edge_target_detected = false(contrast_case_count, 4);
edge_evaluation_cells = ((clutter_edge_cell-stencil_half_width): ...
    (clutter_edge_cell+stencil_half_width)).';
for contrast_index = 1:contrast_case_count
    candidate_multiplier = 10^(clutter_contrast_sweep_db(contrast_index)/10);
    candidate_mean = low_side_mean_power.* ...
        (1+(candidate_multiplier-1)*double(high_side)).*nonuniform_hump;
    candidate_power = candidate_mean.*unit_background_power;
    for target_index = 1:numel(target_cells)
        center_cell = target_cells(target_index);
        candidate_peak = candidate_mean(center_cell)*10^(target_peak_snr_db(target_index)/10);
        response_cells = center_cell+target_response_offsets;
        inside = response_cells >= 1 & response_cells <= range_cell_count;
        candidate_power(response_cells(inside)) = candidate_power(response_cells(inside)) + ...
            candidate_peak*target_power_response(inside).';
    end
    [candidate_threshold, candidate_detection] = apply_four_cfar( ...
        candidate_power, training_cells_per_side, guard_cells_per_side, ...
        os_rank, scale_factors);
    contrast_edge_crossings(contrast_index, :) = sum( ...
        candidate_detection(edge_evaluation_cells, :) & ...
        ~truth_target_mask(edge_evaluation_cells), 1);
    contrast_edge_target_detected(contrast_index, :) = ...
        candidate_detection(edge_target_cell, :);
    assert(all(all(isfinite(candidate_threshold(valid_cut_cells, :)))));
end

figure('Name', 'P51 clutter-contrast sweep', 'Tag', 'P51');
subplot(1, 2, 1);
plot(clutter_contrast_sweep_db, contrast_edge_crossings, 'o-', 'LineWidth', 1.3);
grid on; xlabel('High/low clutter contrast (dB)');
ylabel('Non-target crossings near edge (count)');
title('Sweep 1: only clutter contrast changes'); legend(detector_names);
subplot(1, 2, 2);
imagesc(clutter_contrast_sweep_db, 1:4, contrast_edge_target_detected.'); axis xy;
colormap(gca, [1 1 1; 0.15 0.65 0.20]); caxis([0 1]);
set(gca, 'YTick', 1:4, 'YTickLabel', detector_names);
xlabel('High/low clutter contrast (dB)'); ylabel('Detector');
title('Weak edge-target decision');

%% Sweep 2: change only the number of strong training-cell targets
unit_reference_power = -log(max(rand(private_stream, sweep_trial_count, ...
    training_cell_count), realmin));
target_noise = (randn(private_stream, sweep_trial_count, 1) + ...
    1i*randn(private_stream, sweep_trial_count, 1))/sqrt(2);
target_cut_power = abs(target_noise+sqrt(10^(sweep_target_snr_db/10))).^2;
contamination_order = [1 13 2 14 3 15 4 16 5 17 6 18 7 19 8 20 9 21 10 22 11 23 12 24];
crowded_detection_probability = zeros(numel(crowded_count_sweep), 4);
for count_index = 1:numel(crowded_count_sweep)
    candidate_reference = unit_reference_power;
    contaminator_count = crowded_count_sweep(count_index);
    if contaminator_count > 0
        contaminated_columns = contamination_order(1:contaminator_count);
        candidate_reference(:, contaminated_columns) = ...
            candidate_reference(:, contaminated_columns) + ...
            10^(sweep_interferer_excess_power_db/10);
    end
    leading_trial_mean = sum(candidate_reference(:, 1:training_cells_per_side), 2)/ ...
        training_cells_per_side;
    lagging_trial_mean = sum(candidate_reference(:, ...
        (training_cells_per_side+1):end), 2)/training_cells_per_side;
    ca_trial_statistic = sum(candidate_reference, 2)/training_cell_count;
    sorted_trial_reference = sort(candidate_reference, 2, 'ascend');
    os_trial_statistic = sorted_trial_reference(:, os_rank);
    trial_threshold = [ca_scale_factor*ca_trial_statistic ...
        go_scale_factor*max(leading_trial_mean, lagging_trial_mean) ...
        so_scale_factor*min(leading_trial_mean, lagging_trial_mean) ...
        os_scale_factor*os_trial_statistic];
    crowded_detection_probability(count_index, :) = ...
        sum(target_cut_power > trial_threshold, 1)/sweep_trial_count;
end
os_outlier_capacity = training_cell_count-os_rank;
assert(any(crowded_count_sweep == os_outlier_capacity) && ...
    any(crowded_count_sweep == os_outlier_capacity+1));

figure('Name', 'P51 target-density sweep', 'Tag', 'P51');
plot(crowded_count_sweep, crowded_detection_probability, 'o-', 'LineWidth', 1.4);
hold on; plot([os_outlier_capacity os_outlier_capacity], [0 1], 'k:');
grid on; ylim([0 1]); xlabel('Strong target-contaminated training cells (count)');
ylabel('Empirical weak-CUT detection probability');
title(sprintf('Sweep 2: only target density changes; OS capacity N-k = %d', ...
    os_outlier_capacity));
legend([detector_names {'OS outlier capacity'}], 'Location', 'southwest');

%% Intentionally broken case: reuse CA alpha while claiming equal nominal Pfa
broken_shared_scale_factor = ca_scale_factor;
broken_homogeneous_pfa = [ ...
    (1+broken_shared_scale_factor/training_cell_count)^(-training_cell_count) ...
    homogeneous_variant_pfa(broken_shared_scale_factor, training_cells_per_side, 'GO') ...
    homogeneous_variant_pfa(broken_shared_scale_factor, training_cells_per_side, 'SO') ...
    homogeneous_os_pfa(broken_shared_scale_factor, training_cell_count, os_rank)];
broken_equal_pfa_claim_is_valid = false;
recovered_variant_specific_calibration = ...
    max(abs(calibrated_homogeneous_pfa-design_false_alarm_probability)) < 1e-12;
assert(abs(broken_homogeneous_pfa(1)-design_false_alarm_probability) < 1e-12);
assert(max(abs(broken_homogeneous_pfa(2:4)- ...
    design_false_alarm_probability)) > design_false_alarm_probability);
assert(~broken_equal_pfa_claim_is_valid && recovered_variant_specific_calibration);

figure('Name', 'P51 broken common multiplier and recovery', 'Tag', 'P51');
semilogy(1:4, broken_homogeneous_pfa, 'rx--', 'LineWidth', 1.5); hold on;
semilogy(1:4, calibrated_homogeneous_pfa, 'go-', 'LineWidth', 1.5, ...
    'MarkerFaceColor', 'g');
semilogy(1:4, design_false_alarm_probability*ones(1, 4), 'k:');
grid on; set(gca, 'XTick', 1:4, 'XTickLabel', detector_names);
xlabel('Detector statistic'); ylabel('Exact homogeneous false-alarm probability');
title('Intentionally broken shared alpha; recovery recalibrates each statistic');
legend('Broken: reuse CA alpha', 'Recovery: statistic-specific alpha', ...
    'Design Pfa', 'Location', 'southwest');

%% Retained metrics for inspection and tutor discussion
results = struct();
results.random_seed = random_seed;
results.model = ['independent exponential square-law background with a clutter step, ' ...
    'smooth nonuniform hump, deterministic compressed-target responses, and point-power sweep contaminants'];
results.range_km = range_km;
results.background_mean_power = background_mean_power;
results.received_power = received_power;
results.modeled_target_response_power = modeled_target_response_power;
results.response_artifact_mask = response_artifact_mask;
results.dominant_response_owner = dominant_response_owner;
results.target_cells = target_cells;
results.target_peak_snr_db = target_peak_snr_db;
results.truth_target_mask = truth_target_mask;
results.training_cells_per_side = training_cells_per_side;
results.guard_cells_per_side = guard_cells_per_side;
results.os_rank = os_rank;
results.os_outlier_capacity = os_outlier_capacity;
results.design_false_alarm_probability = design_false_alarm_probability;
results.scale_factors = scale_factors;
results.calibrated_homogeneous_pfa = calibrated_homogeneous_pfa;
results.threshold_power = threshold_power;
results.detection_mask = detection_mask;
results.leading_mean_power = leading_mean_power;
results.lagging_mean_power = lagging_mean_power;
results.ca_mean_power = ca_mean_power;
results.os_order_power = os_order_power;
results.inspection_cells = inspection_cells;
results.inspection_statistics = inspection_statistics;
results.target_detection = target_detection;
results.target_margin_db = target_margin_db;
results.target_training_response_count = target_training_response_count;
results.target_miss_cause_matrix = target_miss_cause_matrix;
results.h0_category_names = h0_category_names;
results.h0_crossing_category_counts = h0_crossing_category_counts;
results.response_artifact_crossing_counts = response_artifact_crossing_counts;
results.crossing_category_names = crossing_category_names;
results.crossing_category_counts = crossing_category_counts;
results.disagreement_cells = disagreement_cells;
results.disagreement_causes = disagreement_causes;
results.clutter_contrast_sweep_db = clutter_contrast_sweep_db;
results.contrast_edge_crossings = contrast_edge_crossings;
results.contrast_edge_target_detected = contrast_edge_target_detected;
results.crowded_count_sweep = crowded_count_sweep;
results.crowded_detection_probability = crowded_detection_probability;
results.broken_homogeneous_pfa = broken_homogeneous_pfa;
results.broken_equal_pfa_claim_is_valid = broken_equal_pfa_claim_is_valid;
results.recovered_variant_specific_calibration = recovered_variant_specific_calibration;
results.generated_random_value_bound = estimated_generated_random_values;
results.stored_numeric_value_bound = estimated_stored_numeric_values;
results.training_sample_visit_bound = estimated_training_sample_visits;
results.max_figure_groups = max_figure_groups;

fprintf('P51 nominal homogeneous Pfa %.3g; alpha CA/GO/SO/OS = %.4f %.4f %.4f %.4f.\n', ...
    design_false_alarm_probability, scale_factors);
for target_index = 1:numel(target_cells)
    fprintf('Target CUT %d detections [CA GO SO OS] = [%d %d %d %d], margins dB [%.1f %.1f %.1f %.1f].\n', ...
        target_cells(target_index), target_detection(target_index, :), ...
        target_margin_db(target_index, :));
end
fprintf('%d detector-disagreement cells classified from training contents/scene zones.\n', ...
    numel(disagreement_cells));
fprintf('Broken shared alpha actual Pfa [CA GO SO OS] = %.4g %.4g %.4g %.4g.\n', ...
    broken_homogeneous_pfa);

%% Local functions: transparent detector operations and bounded calibration
function [threshold_power, detection_mask] = apply_four_cfar( ...
        received_power, training_per_side, guard_per_side, rank, scale_factors)
if ~isnumeric(received_power) || ~isreal(received_power) || ...
        ~isvector(received_power) || isempty(received_power) || ...
        any(~isfinite(received_power)) || any(received_power < 0)
    error('P51:PowerInput', 'Power input must be a finite nonnegative real vector.');
end
received_power = received_power(:);
cell_count = numel(received_power);
integer_geometry = {training_per_side guard_per_side rank};
for geometry_index = 1:numel(integer_geometry)
    geometry_value = integer_geometry{geometry_index};
    if ~isscalar(geometry_value) || ~isnumeric(geometry_value) || ...
            islogical(geometry_value) || ~isreal(geometry_value) || ...
            ~isfinite(geometry_value) || geometry_value ~= fix(geometry_value)
        error('P51:DetectorControls', ...
            'Training, guard, and rank must be finite real integer scalars.');
    end
end
if training_per_side < 1 || guard_per_side < 0 || rank < 1 || ...
        rank > 2*training_per_side || ~isnumeric(scale_factors) || ...
        ~isreal(scale_factors) || numel(scale_factors) ~= 4 || ...
        any(~isfinite(scale_factors)) || any(scale_factors < 0)
    error('P51:DetectorParameters', ...
        'Detector geometry and four nonnegative finite scales are required.');
end
training_count = 2*training_per_side;
half_width = training_per_side+guard_per_side;
if cell_count <= 2*half_width
    error('P51:DetectorGeometry', 'Complete stencil and four scales are required.');
end
threshold_power = nan(cell_count, 4);
detection_mask = false(cell_count, 4);
for cut = (half_width+1):(cell_count-half_width)
    leading_cells = (cut-guard_per_side-training_per_side): ...
        (cut-guard_per_side-1);
    lagging_cells = (cut+guard_per_side+1): ...
        (cut+guard_per_side+training_per_side);
    reference_power = received_power([leading_cells lagging_cells]);
    leading_mean = sum(received_power(leading_cells))/training_per_side;
    lagging_mean = sum(received_power(lagging_cells))/training_per_side;
    sorted_reference = sort(reference_power, 'ascend');
    statistics = [sum(reference_power)/training_count ...
        max(leading_mean, lagging_mean) min(leading_mean, lagging_mean) ...
        sorted_reference(rank)];
    threshold_power(cut, :) = scale_factors.*statistics;
    detection_mask(cut, :) = received_power(cut) > threshold_power(cut, :);
end
end

function probability = homogeneous_variant_pfa(alpha, training_per_side, variant)
if ~isscalar(alpha) || ~isnumeric(alpha) || islogical(alpha) || ...
        ~isreal(alpha) || ~isfinite(alpha) || alpha < 0
    error('P51:Alpha', 'Scale factor must be finite, nonnegative, real, and scalar.');
end
if ~isscalar(training_per_side) || ~isnumeric(training_per_side) || ...
        islogical(training_per_side) || ~isreal(training_per_side) || ...
        ~isfinite(training_per_side) || training_per_side < 1 || ...
        training_per_side ~= fix(training_per_side)
    error('P51:TrainingCount', 'Per-side training count must be a positive integer.');
end
if ~(ischar(variant) && (strcmp(variant, 'GO') || strcmp(variant, 'SO')))
    error('P51:Variant', 'Variant must be GO or SO.');
end
term_sum = 0;
for order = 0:(training_per_side-1)
    log_term = (training_per_side+order)*log(training_per_side) + ...
        gammaln(training_per_side+order) - gammaln(training_per_side) - ...
        gammaln(order+1) - ...
        (training_per_side+order)*log(2*training_per_side+alpha);
    term_sum = term_sum+exp(log_term);
end
so_probability = 2*term_sum;
if strcmp(variant, 'SO')
    probability = so_probability;
else
    probability = 2*(training_per_side/(training_per_side+alpha))^ ...
        training_per_side-so_probability;
end
end

function probability = homogeneous_os_pfa(alpha, training_count, rank)
if ~isscalar(alpha) || ~isnumeric(alpha) || islogical(alpha) || ...
        ~isreal(alpha) || ~isfinite(alpha) || alpha < 0
    error('P51:OSAlpha', 'OS scale must be finite, nonnegative, real, and scalar.');
end
if ~isscalar(training_count) || ~isnumeric(training_count) || ...
        islogical(training_count) || ~isreal(training_count) || ...
        ~isfinite(training_count) || training_count < 1 || ...
        training_count ~= fix(training_count) || ~isscalar(rank) || ...
        ~isnumeric(rank) || islogical(rank) || ~isreal(rank) || ...
        ~isfinite(rank) || rank < 1 || rank > training_count || rank ~= fix(rank)
    error('P51:OSGeometry', 'OS training count and rank must be valid integers.');
end
log_probability = 0;
for spacing_index = 0:(rank-1)
    log_probability = log_probability + log(training_count-spacing_index) - ...
        log(training_count-spacing_index+alpha);
end
probability = exp(log_probability);
end

function alpha = calibrated_variant_scale(training_per_side, requested_pfa, variant, iterations)
if ~isscalar(requested_pfa) || ~isnumeric(requested_pfa) || ...
        islogical(requested_pfa) || ~isreal(requested_pfa) || ...
        ~isfinite(requested_pfa) || requested_pfa <= 0 || requested_pfa >= 1 || ...
        ~isscalar(iterations) || ~isnumeric(iterations) || islogical(iterations) || ...
        ~isreal(iterations) || ~isfinite(iterations) || ...
        iterations < 1 || iterations ~= fix(iterations)
    error('P51:VariantCalibration', ...
        'Calibration needs a valid probability and positive iteration count.');
end
alpha = bounded_bisection(requested_pfa, iterations, ...
    @(candidate) homogeneous_variant_pfa(candidate, training_per_side, variant));
end

function alpha = calibrated_os_scale(training_count, rank, requested_pfa, iterations)
if ~isscalar(requested_pfa) || ~isnumeric(requested_pfa) || ...
        islogical(requested_pfa) || ~isreal(requested_pfa) || ...
        ~isfinite(requested_pfa) || requested_pfa <= 0 || requested_pfa >= 1 || ...
        ~isscalar(iterations) || ~isnumeric(iterations) || islogical(iterations) || ...
        ~isreal(iterations) || ~isfinite(iterations) || ...
        iterations < 1 || iterations ~= fix(iterations)
    error('P51:OSCalibration', ...
        'Calibration needs a valid probability and positive iteration count.');
end
alpha = bounded_bisection(requested_pfa, iterations, ...
    @(candidate) homogeneous_os_pfa(candidate, training_count, rank));
end

function alpha = bounded_bisection(requested_pfa, iterations, probability_function)
lower_alpha = 0;
upper_alpha = 1;
calibration_bracketed = false;
for bracket_iteration = 1:32
    if probability_function(upper_alpha) <= requested_pfa
        calibration_bracketed = true;
        break;
    end
    upper_alpha = 2*upper_alpha;
end
if ~calibration_bracketed
    error('P51:CalibrationBracket', 'Could not bracket a finite scale factor.');
end
for iteration = 1:iterations
    middle_alpha = 0.5*(lower_alpha+upper_alpha);
    if probability_function(middle_alpha) > requested_pfa
        lower_alpha = middle_alpha;
    else
        upper_alpha = middle_alpha;
    end
end
alpha = 0.5*(lower_alpha+upper_alpha);
end
