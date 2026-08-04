%% P50: Apply 2-D CFAR to a Range-Doppler Map
% Guiding question:
% How does local thresholding extend from one range profile to two dimensions?
% Matrix convention: rows are range; columns are signed radial velocity.
% Positive radial velocity means approaching the radar.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P50'));

%% Visible deterministic controls and immutable resource ceilings
random_seed = 5001;
range_bin_count = 96;
doppler_bin_count = 64;
range_bin_spacing_m = 30;
velocity_bin_spacing_mps = 0.625;
design_false_alarm_probability = 1e-3;
training_range_half_width = 6;
guard_range_half_width = 2;
training_doppler_half_width = 4;
guard_doppler_half_width = 2;
range_training_sweep = [3 6 12];
doppler_training_sweep = [2 4 8];
target_range_bins = [28 53 76 4];
target_doppler_bins = [45 22 35 8];
target_peak_snr_db = [24 20 18 20];
target_range_response = [0.015 0.05 0.20 0.55 1 0.55 0.20 0.05 0.015];
target_doppler_response = [0.01 0.04 0.18 0.50 1 0.50 0.18 0.04 0.01];
display_floor_db = -45;
comparison_tolerance = 1e-11;
max_range_bins = 128;
max_doppler_bins = 96;
max_targets = 6;
max_training_half_width = 16;
max_sweep_cases = 4;
max_figure_groups = 6;
max_stored_numeric_values = 400000;
max_training_sample_visits = 30000000;

%% Reject malformed, ambiguous, or unbounded controls before allocation
positive_controls = [range_bin_count doppler_bin_count range_bin_spacing_m ...
    velocity_bin_spacing_mps design_false_alarm_probability ...
    training_range_half_width guard_range_half_width ...
    training_doppler_half_width guard_doppler_half_width ...
    max_range_bins max_doppler_bins max_targets max_training_half_width ...
    max_sweep_cases max_figure_groups max_stored_numeric_values ...
    max_training_sample_visits comparison_tolerance];
assert(all(isfinite(positive_controls)) && all(positive_controls > 0));
assert(~islogical(random_seed) && ~islogical(range_bin_count) && ...
    ~islogical(doppler_bin_count) && ~islogical(range_training_sweep) && ...
    ~islogical(doppler_training_sweep));
assert(isfinite(random_seed) && random_seed == floor(random_seed) && ...
    random_seed == 5001);
integer_controls = [range_bin_count doppler_bin_count ...
    training_range_half_width guard_range_half_width ...
    training_doppler_half_width guard_doppler_half_width ...
    range_training_sweep doppler_training_sweep target_range_bins ...
    target_doppler_bins max_range_bins max_doppler_bins max_targets ...
    max_training_half_width max_sweep_cases max_figure_groups ...
    max_stored_numeric_values max_training_sample_visits];
assert(all(integer_controls == floor(integer_controls)));
assert(max_range_bins == 128 && max_doppler_bins == 96 && ...
    max_targets == 6 && max_training_half_width == 16 && ...
    max_sweep_cases == 4 && max_figure_groups == 6 && ...
    max_stored_numeric_values == 400000 && ...
    max_training_sample_visits == 30000000);
assert(range_bin_count >= 32 && range_bin_count <= max_range_bins);
assert(doppler_bin_count >= 32 && doppler_bin_count <= max_doppler_bins && ...
    mod(doppler_bin_count, 2) == 0);
assert(design_false_alarm_probability >= 1e-6 && ...
    design_false_alarm_probability <= 0.1);
geometry_controls = [training_range_half_width guard_range_half_width ...
    training_doppler_half_width guard_doppler_half_width ...
    range_training_sweep doppler_training_sweep];
assert(all(geometry_controls >= 1) && ...
    all(geometry_controls <= max_training_half_width));
assert(numel(range_training_sweep) >= 3 && ...
    numel(range_training_sweep) <= max_sweep_cases && ...
    all(diff(range_training_sweep) > 0) && ...
    any(range_training_sweep == training_range_half_width));
assert(numel(doppler_training_sweep) >= 3 && ...
    numel(doppler_training_sweep) <= max_sweep_cases && ...
    all(diff(doppler_training_sweep) > 0) && ...
    any(doppler_training_sweep == training_doppler_half_width));
assert(numel(target_range_bins) == numel(target_doppler_bins) && ...
    numel(target_range_bins) == numel(target_peak_snr_db));
assert(numel(target_range_bins) >= 4 && ...
    numel(target_range_bins) <= max_targets);
assert(all(target_range_bins >= 1) && ...
    all(target_range_bins <= range_bin_count));
assert(all(target_doppler_bins >= 1) && ...
    all(target_doppler_bins <= doppler_bin_count));
assert(all(isfinite(target_peak_snr_db)) && ...
    all(target_peak_snr_db >= -10) && all(target_peak_snr_db <= 40));
assert(numel(target_range_response) == 9 && ...
    numel(target_doppler_response) == 9 && ...
    all(isfinite(target_range_response)) && ...
    all(isfinite(target_doppler_response)) && ...
    all(target_range_response >= 0) && all(target_doppler_response >= 0));
assert(target_range_response(5) == 1 && ...
    target_doppler_response(5) == 1 && ...
    all(target_range_response == fliplr(target_range_response)) && ...
    all(target_doppler_response == fliplr(target_doppler_response)));
assert(isfinite(display_floor_db) && display_floor_db <= -30 && ...
    display_floor_db >= -100);

largest_range_outer_half_width = max(range_training_sweep)+...
    guard_range_half_width;
largest_doppler_outer_half_width = max(doppler_training_sweep)+...
    guard_doppler_half_width;
assert(2*largest_range_outer_half_width+1 < range_bin_count && ...
    2*largest_doppler_outer_half_width+1 < doppler_bin_count);
estimated_stored_numeric_values = 34*range_bin_count*doppler_bin_count+5000;
estimated_training_sample_visits = (2+numel(range_training_sweep)+...
    numel(doppler_training_sweep))*range_bin_count*doppler_bin_count*...
    (2*largest_range_outer_half_width+1)*...
    (2*largest_doppler_outer_half_width+1);
assert(estimated_stored_numeric_values <= max_stored_numeric_values);
assert(estimated_training_sample_visits <= max_training_sample_visits);

%% Build a compact square-law range-Doppler map from the P42 convention
range_axis_m = (0:range_bin_count-1).'*range_bin_spacing_m;
doppler_axis_mps = (-doppler_bin_count/2:doppler_bin_count/2-1)*...
    velocity_bin_spacing_mps;
range_background_scale = 0.8+1.2*(range_axis_m/max(range_axis_m)).^2;
doppler_background_scale = 1+2.5*exp(-(doppler_axis_mps/2.5).^2);
background_mean_power = range_background_scale*doppler_background_scale;

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
complex_background = sqrt(background_mean_power/2).*(...
    randn(private_stream, range_bin_count, doppler_bin_count)+...
    1j*randn(private_stream, range_bin_count, doppler_bin_count));
range_doppler_power = abs(complex_background).^2;
target_support_mask = false(range_bin_count, doppler_bin_count);
target_count = numel(target_range_bins);
response_radius = 4;
for target_index = 1:target_count
    range_offsets = -response_radius:response_radius;
    doppler_offsets = -response_radius:response_radius;
    valid_range_offsets = range_offsets(target_range_bins(target_index)+...
        range_offsets >= 1 & target_range_bins(target_index)+...
        range_offsets <= range_bin_count);
    valid_doppler_offsets = doppler_offsets(...
        target_doppler_bins(target_index)+doppler_offsets >= 1 & ...
        target_doppler_bins(target_index)+doppler_offsets <= doppler_bin_count);
    response_rows = target_range_bins(target_index)+valid_range_offsets;
    response_columns = target_doppler_bins(target_index)+valid_doppler_offsets;
    range_weights = target_range_response(valid_range_offsets+response_radius+1);
    doppler_weights = target_doppler_response(...
        valid_doppler_offsets+response_radius+1);
    target_peak_power = background_mean_power(target_range_bins(target_index), ...
        target_doppler_bins(target_index))*10^(target_peak_snr_db(target_index)/10);
    range_doppler_power(response_rows, response_columns) = ...
        range_doppler_power(response_rows, response_columns)+...
        target_peak_power*(range_weights.'*doppler_weights);
    target_support_mask(response_rows, response_columns) = true;
end
range_doppler_db = 10*log10(max(range_doppler_power/...
    max(range_doppler_power(:)), 10^(display_floor_db/10)));

figure('Name', 'P50 input range-Doppler power map', 'Tag', 'P50');
subplot(1, 2, 1);
imagesc(doppler_axis_mps, range_axis_m/1e3, ...
    10*log10(background_mean_power));
axis xy;
colorbar;
xlabel('Radial velocity (m/s, positive approaching)');
ylabel('Range (km)');
title('Known mean background for scene construction (dB power)');
subplot(1, 2, 2);
imagesc(doppler_axis_mps, range_axis_m/1e3, range_doppler_db);
axis xy;
colorbar;
caxis([display_floor_db 0]);
hold on;
plot(doppler_axis_mps(target_doppler_bins(1:3)), ...
    range_axis_m(target_range_bins(1:3))/1e3, 'wo', ...
    'MarkerSize', 8, 'LineWidth', 1.3);
plot(doppler_axis_mps(target_doppler_bins(4)), ...
    range_axis_m(target_range_bins(4))/1e3, 'ws', ...
    'MarkerSize', 8, 'LineWidth', 1.3);
xlabel('Radial velocity (m/s, positive approaching)');
ylabel('Range (km)');
title('Seeded square-law map: circles testable; square at border');

%% Draw the baseline rectangular training, guard, and CUT stencil
range_outer_half_width = training_range_half_width+guard_range_half_width;
doppler_outer_half_width = training_doppler_half_width+...
    guard_doppler_half_width;
outer_row_offsets = -range_outer_half_width:range_outer_half_width;
outer_column_offsets = -doppler_outer_half_width:doppler_outer_half_width;
training_mask = true(numel(outer_row_offsets), numel(outer_column_offsets));
guard_rows = abs(outer_row_offsets) <= guard_range_half_width;
guard_columns = abs(outer_column_offsets) <= guard_doppler_half_width;
training_mask(guard_rows, guard_columns) = false;
training_cell_count = sum(training_mask(:));
expected_training_cell_count = ...
    (2*range_outer_half_width+1)*(2*doppler_outer_half_width+1)-...
    (2*guard_range_half_width+1)*(2*guard_doppler_half_width+1);
assert(training_cell_count == expected_training_cell_count);
cfar_scale_factor = training_cell_count*(...
    design_false_alarm_probability^(-1/training_cell_count)-1);

stencil_codes = double(training_mask);
stencil_codes(~training_mask) = 2;
stencil_codes(range_outer_half_width+1, doppler_outer_half_width+1) = 3;
figure('Name', 'P50 explicit 2-D CFAR stencil', 'Tag', 'P50');
imagesc(outer_column_offsets, outer_row_offsets, stencil_codes);
axis xy equal tight;
colorbar('Ticks', [1 2 3], ...
    'TickLabels', {'training', 'guard', 'CUT'});
xlabel('Doppler-bin offset from CUT');
ylabel('Range-bin offset from CUT');
title(sprintf('Rectangular stencil: N = %d training cells', ...
    training_cell_count));

%% Baseline: estimate local power, build the threshold surface, and decide
noise_power_estimate = nan(range_bin_count, doppler_bin_count);
cfar_threshold = nan(range_bin_count, doppler_bin_count);
testable_mask = false(range_bin_count, doppler_bin_count);
for range_index = 1+range_outer_half_width:...
        range_bin_count-range_outer_half_width
    for doppler_index = 1+doppler_outer_half_width:...
            doppler_bin_count-doppler_outer_half_width
        local_power = range_doppler_power(...
            range_index+outer_row_offsets, ...
            doppler_index+outer_column_offsets);
        training_power = local_power(training_mask);
        noise_power_estimate(range_index, doppler_index) = ...
            sum(training_power)/training_cell_count;
        cfar_threshold(range_index, doppler_index) = cfar_scale_factor*...
            noise_power_estimate(range_index, doppler_index);
        testable_mask(range_index, doppler_index) = true;
    end
end
cfar_detection = testable_mask & range_doppler_power > cfar_threshold;
target_is_testable = testable_mask(sub2ind(size(testable_mask), ...
    target_range_bins, target_doppler_bins));
target_is_detected = cfar_detection(sub2ind(size(cfar_detection), ...
    target_range_bins, target_doppler_bins));
assert(all(target_is_testable(1:3)) && ~target_is_testable(4));
assert(all(target_is_detected(1:3)) && ~target_is_detected(4));
eligible_fraction = sum(testable_mask(:))/numel(testable_mask);
false_alarm_count = sum(cfar_detection(:) & ~target_support_mask(:));
target_cut_to_threshold = nan(1, target_count);
for target_index = 1:target_count
    if target_is_testable(target_index)
        target_cut_to_threshold(target_index) = ...
            range_doppler_power(target_range_bins(target_index), ...
            target_doppler_bins(target_index))/...
            cfar_threshold(target_range_bins(target_index), ...
            target_doppler_bins(target_index));
    end
end

threshold_display_db = nan(size(cfar_threshold));
threshold_display_db(testable_mask) = 10*log10(...
    cfar_threshold(testable_mask));
cut_ratio_db = nan(size(cfar_threshold));
cut_ratio_db(testable_mask) = 10*log10(...
    range_doppler_power(testable_mask)./cfar_threshold(testable_mask));
[detection_rows, detection_columns] = find(cfar_detection);
figure('Name', 'P50 threshold surface and detections', 'Tag', 'P50');
subplot(1, 3, 1);
imagesc(doppler_axis_mps, range_axis_m/1e3, noise_power_estimate);
axis xy;
colorbar;
xlabel('Radial velocity (m/s)');
ylabel('Range (km)');
title('Local training-power mean (linear power)');
subplot(1, 3, 2);
imagesc(doppler_axis_mps, range_axis_m/1e3, threshold_display_db);
axis xy;
colorbar;
xlabel('Radial velocity (m/s)');
ylabel('Range (km)');
title('2-D CA-CFAR threshold (dB power)');
subplot(1, 3, 3);
imagesc(doppler_axis_mps, range_axis_m/1e3, cut_ratio_db);
axis xy;
colorbar;
caxis([-12 12]);
hold on;
plot(doppler_axis_mps(detection_columns), ...
    range_axis_m(detection_rows)/1e3, 'wo', 'MarkerSize', 5);
plot(doppler_axis_mps(target_doppler_bins), ...
    range_axis_m(target_range_bins)/1e3, 'kx', ...
    'MarkerSize', 8, 'LineWidth', 1.3);
xlabel('Radial velocity (m/s)');
ylabel('Range (km)');
title('CUT/threshold (dB); white detections, black truth');

%% Sweep 1: change only the range training half-width
range_case_count = numel(range_training_sweep);
range_sweep_training_count = zeros(1, range_case_count);
range_sweep_eligible_fraction = zeros(1, range_case_count);
range_sweep_normalized_estimate_rmse = zeros(1, range_case_count);
range_sweep_detected_target_count = zeros(1, range_case_count);
range_sweep_false_alarm_count = zeros(1, range_case_count);
range_sweep_outer_half_span_m = zeros(1, range_case_count);
for case_index = 1:range_case_count
    candidate_range_training = range_training_sweep(case_index);
    [candidate_threshold, candidate_estimate, candidate_detection, ...
        candidate_testable, candidate_training_count] = apply_ca_cfar_2d(...
        range_doppler_power, candidate_range_training, ...
        guard_range_half_width, training_doppler_half_width, ...
        guard_doppler_half_width, design_false_alarm_probability);
    range_sweep_training_count(case_index) = candidate_training_count;
    range_sweep_eligible_fraction(case_index) = ...
        sum(candidate_testable(:))/numel(candidate_testable);
    analysis_mask = candidate_testable & ~target_support_mask;
    normalized_estimate = candidate_estimate(analysis_mask)./...
        background_mean_power(analysis_mask);
    range_sweep_normalized_estimate_rmse(case_index) = ...
        sqrt(mean((normalized_estimate-1).^2));
    candidate_target_detection = candidate_detection(sub2ind(...
        size(candidate_detection), target_range_bins(1:3), ...
        target_doppler_bins(1:3)));
    range_sweep_detected_target_count(case_index) = ...
        sum(candidate_target_detection);
    range_sweep_false_alarm_count(case_index) = ...
        sum(candidate_detection(:) & ~target_support_mask(:));
    range_sweep_outer_half_span_m(case_index) = ...
        (candidate_range_training+guard_range_half_width)*...
        range_bin_spacing_m;
    assert(all(isfinite(candidate_threshold(candidate_testable))));
end
assert(all(diff(range_sweep_training_count) > 0));
assert(all(diff(range_sweep_eligible_fraction) < 0));

figure('Name', 'P50 range-window sweep', 'Tag', 'P50');
subplot(2, 2, 1);
plot(range_training_sweep, range_sweep_training_count, 'o-', ...
    'LineWidth', 1.2);
grid on;
xlabel('Range training half-width (bins/side)');
ylabel('Training-cell count N');
title('Only the range extent changes');
subplot(2, 2, 2);
plot(range_sweep_outer_half_span_m, range_sweep_eligible_fraction, ...
    'o-', 'LineWidth', 1.2);
grid on;
xlabel('Outer range half-span (m)');
ylabel('Testable map fraction');
title('Wider range stencil excludes more range-border rows');
subplot(2, 2, 3);
plot(range_training_sweep, range_sweep_normalized_estimate_rmse, ...
    'o-', 'LineWidth', 1.2);
grid on;
xlabel('Range training half-width (bins/side)');
ylabel('Normalized estimate RMSE');
title('Variance/locality tradeoff on the same map');
subplot(2, 2, 4);
plot(range_training_sweep, range_sweep_detected_target_count, ...
    'o-', 'LineWidth', 1.2);
hold on;
plot(range_training_sweep, range_sweep_false_alarm_count, ...
    's--', 'LineWidth', 1.2);
grid on;
xlabel('Range training half-width (bins/side)');
ylabel('Count');
title('Interior targets and non-target crossings');
legend('Detected interior target CUTs', 'Non-target crossings', ...
    'Location', 'best');

%% Sweep 2: change only the Doppler training half-width
doppler_case_count = numel(doppler_training_sweep);
doppler_sweep_training_count = zeros(1, doppler_case_count);
doppler_sweep_eligible_fraction = zeros(1, doppler_case_count);
doppler_sweep_normalized_estimate_rmse = zeros(1, doppler_case_count);
doppler_sweep_detected_target_count = zeros(1, doppler_case_count);
doppler_sweep_false_alarm_count = zeros(1, doppler_case_count);
doppler_sweep_outer_half_span_mps = zeros(1, doppler_case_count);
for case_index = 1:doppler_case_count
    candidate_doppler_training = doppler_training_sweep(case_index);
    [candidate_threshold, candidate_estimate, candidate_detection, ...
        candidate_testable, candidate_training_count] = apply_ca_cfar_2d(...
        range_doppler_power, training_range_half_width, ...
        guard_range_half_width, candidate_doppler_training, ...
        guard_doppler_half_width, design_false_alarm_probability);
    doppler_sweep_training_count(case_index) = candidate_training_count;
    doppler_sweep_eligible_fraction(case_index) = ...
        sum(candidate_testable(:))/numel(candidate_testable);
    analysis_mask = candidate_testable & ~target_support_mask;
    normalized_estimate = candidate_estimate(analysis_mask)./...
        background_mean_power(analysis_mask);
    doppler_sweep_normalized_estimate_rmse(case_index) = ...
        sqrt(mean((normalized_estimate-1).^2));
    candidate_target_detection = candidate_detection(sub2ind(...
        size(candidate_detection), target_range_bins(1:3), ...
        target_doppler_bins(1:3)));
    doppler_sweep_detected_target_count(case_index) = ...
        sum(candidate_target_detection);
    doppler_sweep_false_alarm_count(case_index) = ...
        sum(candidate_detection(:) & ~target_support_mask(:));
    doppler_sweep_outer_half_span_mps(case_index) = ...
        (candidate_doppler_training+guard_doppler_half_width)*...
        velocity_bin_spacing_mps;
    assert(all(isfinite(candidate_threshold(candidate_testable))));
end
assert(all(diff(doppler_sweep_training_count) > 0));
assert(all(diff(doppler_sweep_eligible_fraction) < 0));

figure('Name', 'P50 Doppler-window sweep', 'Tag', 'P50');
subplot(2, 2, 1);
plot(doppler_training_sweep, doppler_sweep_training_count, 'o-', ...
    'LineWidth', 1.2);
grid on;
xlabel('Doppler training half-width (bins/side)');
ylabel('Training-cell count N');
title('Only the Doppler extent changes');
subplot(2, 2, 2);
plot(doppler_sweep_outer_half_span_mps, ...
    doppler_sweep_eligible_fraction, 'o-', 'LineWidth', 1.2);
grid on;
xlabel('Outer Doppler half-span (m/s)');
ylabel('Testable map fraction');
title('Wider Doppler stencil excludes more velocity-border columns');
subplot(2, 2, 3);
plot(doppler_training_sweep, ...
    doppler_sweep_normalized_estimate_rmse, 'o-', 'LineWidth', 1.2);
grid on;
xlabel('Doppler training half-width (bins/side)');
ylabel('Normalized estimate RMSE');
title('A wider window mixes more of the clutter ridge');
subplot(2, 2, 4);
plot(doppler_training_sweep, ...
    doppler_sweep_detected_target_count, 'o-', 'LineWidth', 1.2);
hold on;
plot(doppler_training_sweep, doppler_sweep_false_alarm_count, ...
    's--', 'LineWidth', 1.2);
grid on;
xlabel('Doppler training half-width (bins/side)');
ylabel('Count');
title('Interior targets and non-target crossings');
legend('Detected interior target CUTs', 'Non-target crossings', ...
    'Location', 'best');

%% Intentionally broken case: zero-pad missing boundary references
% Missing training samples are treated as zero, yet the full N and alpha are
% retained. This produces finite border thresholds but not calibrated tests.
padded_power = zeros(range_bin_count+2*range_outer_half_width, ...
    doppler_bin_count+2*doppler_outer_half_width);
padded_power(range_outer_half_width+(1:range_bin_count), ...
    doppler_outer_half_width+(1:doppler_bin_count)) = range_doppler_power;
broken_threshold = zeros(size(range_doppler_power));
for range_index = 1:range_bin_count
    for doppler_index = 1:doppler_bin_count
        padded_local_power = padded_power(range_index+...
            (0:2*range_outer_half_width), doppler_index+...
            (0:2*doppler_outer_half_width));
        broken_threshold(range_index, doppler_index) = cfar_scale_factor*...
            sum(padded_local_power(training_mask))/training_cell_count;
    end
end
broken_detection = range_doppler_power > broken_threshold;
border_mask = ~testable_mask;
broken_border_detection_count = sum(broken_detection(:) & border_mask(:));
broken_edge_target_detected = broken_detection(target_range_bins(4), ...
    target_doppler_bins(4));
broken_all_cells_calibrated_claim_is_valid = false;
assert(broken_edge_target_detected && broken_border_detection_count >= 1);
assert(max(abs(broken_threshold(testable_mask)-...
    cfar_threshold(testable_mask))) <= comparison_tolerance*...
    max(1, max(cfar_threshold(testable_mask))));

%% Recovery: retain decisions only where the complete stencil exists
recovered_threshold = broken_threshold;
recovered_threshold(border_mask) = NaN;
recovered_detection = testable_mask & ...
    range_doppler_power > recovered_threshold;
recovery_threshold_error = max(abs(recovered_threshold(testable_mask)-...
    cfar_threshold(testable_mask)));
recovery_detection_matches_baseline = ...
    isequal(recovered_detection, cfar_detection);
recovered_edge_target_is_testable = testable_mask(target_range_bins(4), ...
    target_doppler_bins(4));
assert(recovery_threshold_error <= comparison_tolerance*...
    max(1, max(cfar_threshold(testable_mask))));
assert(recovery_detection_matches_baseline && ...
    ~recovered_edge_target_is_testable);

figure('Name', 'P50 broken border policy and recovery', 'Tag', 'P50');
subplot(1, 2, 1);
imagesc(doppler_axis_mps, range_axis_m/1e3, ...
    10*log10(max(broken_threshold, eps)));
axis xy;
colorbar;
hold on;
[broken_rows, broken_columns] = find(broken_detection & border_mask);
plot(doppler_axis_mps(broken_columns), range_axis_m(broken_rows)/1e3, ...
    'wo', 'MarkerSize', 5);
xlabel('Radial velocity (m/s)');
ylabel('Range (km)');
title('Broken: zero padding invents low border thresholds');
subplot(1, 2, 2);
imagesc(doppler_axis_mps, range_axis_m/1e3, double(testable_mask));
axis xy;
colorbar;
hold on;
plot(doppler_axis_mps(target_doppler_bins(4)), ...
    range_axis_m(target_range_bins(4))/1e3, 'ws', ...
    'MarkerSize', 8, 'LineWidth', 1.3);
xlabel('Radial velocity (m/s)');
ylabel('Range (km)');
title('Recovered policy: white interior is testable; border is not');

%% Compact retained results for inspection and checks
results = struct();
results.random_seed = random_seed;
results.range_axis_m = range_axis_m;
results.doppler_axis_mps = doppler_axis_mps;
results.background_mean_power = background_mean_power;
results.range_doppler_power = range_doppler_power;
results.training_cell_count = training_cell_count;
results.cfar_scale_factor = cfar_scale_factor;
results.testable_mask = testable_mask;
results.noise_power_estimate = noise_power_estimate;
results.cfar_threshold = cfar_threshold;
results.cfar_detection = cfar_detection;
results.target_is_testable = target_is_testable;
results.target_is_detected = target_is_detected;
results.target_cut_to_threshold = target_cut_to_threshold;
results.false_alarm_count = false_alarm_count;
results.eligible_fraction = eligible_fraction;
results.range_training_sweep = range_training_sweep;
results.range_sweep_training_count = range_sweep_training_count;
results.range_sweep_eligible_fraction = range_sweep_eligible_fraction;
results.range_sweep_normalized_estimate_rmse = ...
    range_sweep_normalized_estimate_rmse;
results.range_sweep_detected_target_count = ...
    range_sweep_detected_target_count;
results.range_sweep_false_alarm_count = range_sweep_false_alarm_count;
results.doppler_training_sweep = doppler_training_sweep;
results.doppler_sweep_training_count = doppler_sweep_training_count;
results.doppler_sweep_eligible_fraction = doppler_sweep_eligible_fraction;
results.doppler_sweep_normalized_estimate_rmse = ...
    doppler_sweep_normalized_estimate_rmse;
results.doppler_sweep_detected_target_count = ...
    doppler_sweep_detected_target_count;
results.doppler_sweep_false_alarm_count = doppler_sweep_false_alarm_count;
results.broken_border_detection_count = broken_border_detection_count;
results.broken_edge_target_detected = broken_edge_target_detected;
results.broken_all_cells_calibrated_claim_is_valid = ...
    broken_all_cells_calibrated_claim_is_valid;
results.recovery_threshold_error = recovery_threshold_error;
results.recovery_detection_matches_baseline = ...
    recovery_detection_matches_baseline;
results.recovered_edge_target_is_testable = ...
    recovered_edge_target_is_testable;
results.design_false_alarm_probability = design_false_alarm_probability;
results.estimated_stored_numeric_values = estimated_stored_numeric_values;
results.max_stored_numeric_values = max_stored_numeric_values;
results.estimated_training_sample_visits = estimated_training_sample_visits;
results.max_training_sample_visits = max_training_sample_visits;

fprintf('\nP50 2-D CA-CFAR metrics (seed %d)\n', random_seed);
fprintf('Map: %d range bins x %d Doppler bins; N = %d; alpha = %.6f\n', ...
    range_bin_count, doppler_bin_count, training_cell_count, ...
    cfar_scale_factor);
fprintf('Testable fraction %.3f; false alarms outside target support %d\n', ...
    eligible_fraction, false_alarm_count);
for target_index = 1:target_count
    fprintf(['Target %d: range %.3f km, velocity %+.3f m/s, ' ...
        'testable %d, detected %d, CUT/threshold %.3f\n'], ...
        target_index, range_axis_m(target_range_bins(target_index))/1e3, ...
        doppler_axis_mps(target_doppler_bins(target_index)), ...
        target_is_testable(target_index), target_is_detected(target_index), ...
        target_cut_to_threshold(target_index));
end
fprintf(['Broken border detections %d; edge target called %d; ' ...
    'recovery matches baseline %d\n'], broken_border_detection_count, ...
    broken_edge_target_detected, recovery_detection_matches_baseline);

function [threshold, estimate, detection, testable, training_count] = ...
        apply_ca_cfar_2d(power_map, training_range, guard_range, ...
        training_doppler, guard_doppler, requested_pfa)
% Explicit reusable form of the same baseline rectangular operation.
[range_count, doppler_count] = size(power_map);
range_outer = training_range+guard_range;
doppler_outer = training_doppler+guard_doppler;
row_offsets = -range_outer:range_outer;
column_offsets = -doppler_outer:doppler_outer;
mask = true(numel(row_offsets), numel(column_offsets));
mask(abs(row_offsets) <= guard_range, ...
    abs(column_offsets) <= guard_doppler) = false;
training_count = sum(mask(:));
alpha = training_count*(requested_pfa^(-1/training_count)-1);
estimate = nan(range_count, doppler_count);
threshold = nan(range_count, doppler_count);
testable = false(range_count, doppler_count);
for range_index = 1+range_outer:range_count-range_outer
    for doppler_index = 1+doppler_outer:doppler_count-doppler_outer
        local_power = power_map(range_index+row_offsets, ...
            doppler_index+column_offsets);
        estimate(range_index, doppler_index) = sum(local_power(mask))/...
            training_count;
        threshold(range_index, doppler_index) = alpha*...
            estimate(range_index, doppler_index);
        testable(range_index, doppler_index) = true;
    end
end
detection = testable & power_map > threshold;
end
