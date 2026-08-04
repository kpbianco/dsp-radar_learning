%% P45: Implement 1-D Cell-Averaging CFAR
% Guiding question:
% How can the threshold adapt to the local noise level?
% Statistic convention: nonnegative square-law power in each range cell.
% The CA-CFAR reference window excludes the CUT and its guard cells.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P45'));

%% Visible deterministic controls and immutable resource ceilings
random_seed = 4501;
cell_count = 256;
range_resolution_m = 15;
training_cells_per_side = 12;
guard_cells_per_side = 2;
design_false_alarm_probability = 1e-3;
target_cells = [62 132 211];
target_snr_db = [19 17 20];
target_phase_rad = [0.2 -0.8 1.1];
false_alarm_probability_sweep = [1e-2 1e-3 1e-4];
background_scale_sweep = [0.5 1 2];
comparison_tolerance = 1e-10;
max_cell_count = 512;
max_training_cells_per_side = 32;
max_guard_cells_per_side = 8;
max_target_count = 6;
max_probability_cases = 5;
max_background_scale_cases = 5;
max_figure_groups = 5;
max_stored_numeric_values = 50000;

%% Reject malformed, ambiguous, or unbounded controls before allocation
scalar_controls = [random_seed cell_count range_resolution_m ...
    training_cells_per_side guard_cells_per_side ...
    design_false_alarm_probability comparison_tolerance ...
    max_cell_count max_training_cells_per_side ...
    max_guard_cells_per_side max_target_count max_probability_cases ...
    max_background_scale_cases max_figure_groups ...
    max_stored_numeric_values];
assert(all(isfinite(scalar_controls)));
assert(isreal(scalar_controls) && isreal(target_cells) && ...
    isreal(target_snr_db) && isreal(target_phase_rad) && ...
    isreal(false_alarm_probability_sweep) && ...
    isreal(background_scale_sweep));
assert(~islogical(random_seed) && ~islogical(cell_count) && ...
    ~islogical(range_resolution_m) && ...
    ~islogical(training_cells_per_side) && ...
    ~islogical(guard_cells_per_side) && ~islogical(target_cells) && ...
    ~islogical(target_snr_db) && ~islogical(target_phase_rad) && ...
    ~islogical(false_alarm_probability_sweep) && ...
    ~islogical(background_scale_sweep) && ...
    ~islogical(comparison_tolerance));
integer_controls = [random_seed cell_count training_cells_per_side ...
    guard_cells_per_side target_cells max_cell_count ...
    max_training_cells_per_side max_guard_cells_per_side ...
    max_target_count max_probability_cases max_background_scale_cases ...
    max_figure_groups max_stored_numeric_values];
assert(all(integer_controls == floor(integer_controls)));
assert(random_seed == 4501 && range_resolution_m > 0);
assert(cell_count == 256 && cell_count <= max_cell_count);
assert(training_cells_per_side >= 2 && ...
    training_cells_per_side <= max_training_cells_per_side);
assert(guard_cells_per_side >= 1 && ...
    guard_cells_per_side <= max_guard_cells_per_side);
assert(2*(training_cells_per_side+guard_cells_per_side)+1 < ...
    cell_count);
assert(numel(target_cells) >= 2 && numel(target_cells) <= max_target_count);
assert(numel(target_cells) == numel(target_snr_db) && ...
    numel(target_cells) == numel(target_phase_rad));
assert(all(target_cells >= 1) && all(target_cells <= cell_count) && ...
    all(diff(target_cells) > 0) && all(isfinite(target_snr_db)) && ...
    all(isfinite(target_phase_rad)));
assert(all(diff(target_cells) > ...
    2*(training_cells_per_side+guard_cells_per_side)));
assert(numel(false_alarm_probability_sweep) >= 3 && ...
    numel(false_alarm_probability_sweep) <= max_probability_cases && ...
    all(isfinite(false_alarm_probability_sweep)) && ...
    all(false_alarm_probability_sweep > 0) && ...
    all(false_alarm_probability_sweep < 0.5) && ...
    all(diff(false_alarm_probability_sweep) < 0) && ...
    any(false_alarm_probability_sweep == design_false_alarm_probability));
assert(numel(background_scale_sweep) >= 3 && ...
    numel(background_scale_sweep) <= max_background_scale_cases && ...
    all(isfinite(background_scale_sweep)) && ...
    all(background_scale_sweep > 0) && ...
    all(diff(background_scale_sweep) > 0) && ...
    any(background_scale_sweep == 1));
assert(design_false_alarm_probability > 0 && ...
    design_false_alarm_probability < 0.5);
assert(comparison_tolerance > 0 && comparison_tolerance <= 1e-6);
assert(max_cell_count == 512 && max_training_cells_per_side == 32 && ...
    max_guard_cells_per_side == 8 && max_target_count == 6 && ...
    max_probability_cases == 5 && max_background_scale_cases == 5 && ...
    max_figure_groups == 5 && max_stored_numeric_values == 50000);

valid_first_cell = training_cells_per_side+guard_cells_per_side+1;
valid_last_cell = cell_count-training_cells_per_side-guard_cells_per_side;
assert(all(target_cells >= valid_first_cell) && ...
    all(target_cells <= valid_last_cell));
estimated_stored_numeric_values = 40*cell_count+...
    12*cell_count*numel(false_alarm_probability_sweep)+...
    12*cell_count*numel(background_scale_sweep)+1000;
assert(estimated_stored_numeric_values <= max_stored_numeric_values);

%% Build a slowly varying range background and inject point targets
cell_index = 1:cell_count;
range_axis_m = (cell_index-1)*range_resolution_m;
background_mean_power = 0.65+0.0045*cell_index+...
    0.32*(1+sin(2*pi*(cell_index-18)/190));
assert(all(isfinite(background_mean_power)) && ...
    all(background_mean_power > 0));

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
unit_noise_i = randn(private_stream, 1, cell_count);
unit_noise_q = randn(private_stream, 1, cell_count);
unit_complex_noise = (unit_noise_i+1i*unit_noise_q)/sqrt(2);
received = sqrt(background_mean_power).*unit_complex_noise;
target_amplitude = sqrt(background_mean_power(target_cells).*...
    10.^(target_snr_db/10));
received(target_cells) = received(target_cells)+...
    target_amplitude.*exp(1i*target_phase_rad);
profile_power = abs(received).^2;
target_mask = false(1, cell_count);
target_mask(target_cells) = true;
assert(all(isfinite(profile_power)) && all(profile_power >= 0));

example_cut_cell = target_cells(2);
example_leading_training_cells = example_cut_cell-guard_cells_per_side-...
    training_cells_per_side:example_cut_cell-guard_cells_per_side-1;
example_leading_guard_cells = example_cut_cell-guard_cells_per_side:...
    example_cut_cell-1;
example_lagging_guard_cells = example_cut_cell+1:...
    example_cut_cell+guard_cells_per_side;
example_lagging_training_cells = example_cut_cell+guard_cells_per_side+1:...
    example_cut_cell+guard_cells_per_side+training_cells_per_side;

figure('Name', 'P45 deterministic range profile', 'Tag', 'P45');
subplot(3, 1, 1);
plot(range_axis_m, 10*log10(background_mean_power), 'LineWidth', 1.4);
grid on;
xlabel('Range (m)');
ylabel('Mean background power (dB power units)');
title('Slowly varying local noise power');
subplot(3, 1, 2);
plot(range_axis_m, 10*log10(max(profile_power, realmin)), ...
    'LineWidth', 1.0);
hold on;
plot(range_axis_m(target_cells), ...
    10*log10(max(profile_power(target_cells), realmin)), ...
    'rv', 'MarkerFaceColor', 'r');
grid on;
xlabel('Range (m)');
ylabel('Observed square-law power (dB power units)');
title('One seeded range profile with three point targets');
legend('Observed profile', 'Injected target cells', 'Location', 'best');
subplot(3, 1, 3);
hold on;
stem(range_axis_m(example_leading_training_cells), ...
    profile_power(example_leading_training_cells), 'b', 'filled');
stem(range_axis_m(example_leading_guard_cells), ...
    profile_power(example_leading_guard_cells), 'Color', [0.95 0.65 0.1], ...
    'Marker', 'square');
stem(range_axis_m(example_cut_cell), profile_power(example_cut_cell), ...
    'r', 'filled', 'Marker', 'diamond');
stem(range_axis_m(example_lagging_guard_cells), ...
    profile_power(example_lagging_guard_cells), 'Color', [0.95 0.65 0.1], ...
    'Marker', 'square');
stem(range_axis_m(example_lagging_training_cells), ...
    profile_power(example_lagging_training_cells), 'b', 'filled');
grid on;
xlabel('Range (m)');
ylabel('Observed power (power units)');
title('One CA-CFAR stencil: training | guards | CUT | guards | training');
legend('Leading training', 'Leading guards', 'CUT', 'Lagging guards', ...
    'Lagging training', 'Location', 'best');

%% Baseline: implement CA-CFAR explicitly in linear power
training_cell_count = 2*training_cells_per_side;
cfar_scale_factor = training_cell_count*(...
    design_false_alarm_probability^(-1/training_cell_count)-1);
eligible_cut_mask = false(1, cell_count);
eligible_cut_mask(valid_first_cell:valid_last_cell) = true;
excluded_edge_mask = ~eligible_cut_mask;
noise_estimate_power = nan(1, cell_count);
threshold_power = nan(1, cell_count);
detection_mask = false(1, cell_count);

for cut_cell = valid_first_cell:valid_last_cell
    leading_training_cells = cut_cell-guard_cells_per_side-...
        training_cells_per_side:cut_cell-guard_cells_per_side-1;
    lagging_training_cells = cut_cell+guard_cells_per_side+1:...
        cut_cell+guard_cells_per_side+training_cells_per_side;
    training_cells = [leading_training_cells lagging_training_cells];
    assert(numel(training_cells) == training_cell_count);
    assert(~any(training_cells == cut_cell));
    assert(all(abs(training_cells-cut_cell) > guard_cells_per_side));
    noise_estimate_power(cut_cell) = mean(profile_power(training_cells));
    threshold_power(cut_cell) = ...
        cfar_scale_factor*noise_estimate_power(cut_cell);
    detection_mask(cut_cell) = ...
        profile_power(cut_cell) > threshold_power(cut_cell);
end

assert(all(isnan(threshold_power(excluded_edge_mask))));
assert(all(isfinite(threshold_power(eligible_cut_mask))));
assert(all(threshold_power(eligible_cut_mask) > 0));
assert(all(detection_mask(target_cells)));
assert(~any(detection_mask(excluded_edge_mask)));
false_alarm_mask = detection_mask & eligible_cut_mask & ~target_mask;
baseline_detection_count = sum(detection_mask);
baseline_target_detection_count = sum(detection_mask(target_cells));
baseline_false_alarm_count = sum(false_alarm_mask);
low_background_cells = eligible_cut_mask & ...
    background_mean_power <= median(background_mean_power(eligible_cut_mask));
high_background_cells = eligible_cut_mask & ...
    background_mean_power > median(background_mean_power(eligible_cut_mask));
low_background_median_threshold = median(threshold_power(low_background_cells));
high_background_median_threshold = median(threshold_power(high_background_cells));
assert(high_background_median_threshold > low_background_median_threshold);

figure('Name', 'P45 baseline CA-CFAR', 'Tag', 'P45');
subplot(2, 1, 1);
plot(range_axis_m, 10*log10(max(profile_power, realmin)), ...
    'Color', [0.2 0.35 0.75], 'LineWidth', 1.0);
hold on;
plot(range_axis_m, 10*log10(max(threshold_power, realmin)), ...
    'k-', 'LineWidth', 1.4);
plot(range_axis_m(detection_mask), ...
    10*log10(max(profile_power(detection_mask), realmin)), ...
    'ro', 'MarkerFaceColor', 'r');
plot(range_axis_m(excluded_edge_mask), ...
    10*log10(max(profile_power(excluded_edge_mask), realmin)), ...
    'x', 'Color', [0.55 0.55 0.55]);
grid on;
xlabel('Range (m)');
ylabel('Power (dB power units)');
title(sprintf('Baseline CA-CFAR: P_{FA}=%.0e, N=%d, G=%d per side', ...
    design_false_alarm_probability, training_cell_count, ...
    guard_cells_per_side));
legend('Observed profile', 'Adaptive threshold', 'Detections', ...
    'Excluded edge CUTs', 'Location', 'best');
subplot(2, 1, 2);
plot(range_axis_m, background_mean_power, '--', 'LineWidth', 1.3);
hold on;
plot(range_axis_m, noise_estimate_power, 'LineWidth', 1.1);
plot(range_axis_m(excluded_edge_mask), ...
    0.9*min(background_mean_power)*ones(1, sum(excluded_edge_mask)), ...
    'x', 'Color', [0.55 0.55 0.55]);
grid on;
xlabel('Range (m)');
ylabel('Local mean power estimate (power units)');
title('Training-cell average follows the background; edges remain undecided');
legend('True local mean used to synthesize data', ...
    'CA training-cell estimate', 'Excluded edge CUTs', 'Location', 'best');

%% Sweep 1: change only the requested false-alarm probability
probability_case_count = numel(false_alarm_probability_sweep);
probability_sweep_scale_factor = zeros(1, probability_case_count);
probability_sweep_threshold_power = nan(probability_case_count, cell_count);
probability_sweep_detection_mask = false(probability_case_count, cell_count);
probability_sweep_detection_count = zeros(1, probability_case_count);
probability_sweep_target_detection_count = zeros(1, probability_case_count);
probability_sweep_false_alarm_count = zeros(1, probability_case_count);

for probability_index = 1:probability_case_count
    requested_pfa = false_alarm_probability_sweep(probability_index);
    probability_sweep_scale_factor(probability_index) = ...
        training_cell_count*(requested_pfa^(-1/training_cell_count)-1);
    probability_sweep_threshold_power(probability_index, eligible_cut_mask) = ...
        probability_sweep_scale_factor(probability_index)*...
        noise_estimate_power(eligible_cut_mask);
    probability_sweep_detection_mask(probability_index, eligible_cut_mask) = ...
        profile_power(eligible_cut_mask) > ...
        probability_sweep_threshold_power(probability_index, eligible_cut_mask);
    probability_sweep_detection_count(probability_index) = ...
        sum(probability_sweep_detection_mask(probability_index, :));
    probability_sweep_target_detection_count(probability_index) = sum(...
        probability_sweep_detection_mask(probability_index, target_cells));
    probability_sweep_false_alarm_count(probability_index) = sum(...
        probability_sweep_detection_mask(probability_index, :) & ...
        eligible_cut_mask & ~target_mask);
end

assert(all(diff(probability_sweep_scale_factor) > 0));
assert(all(diff(probability_sweep_detection_count) <= 0));
assert(all(diff(probability_sweep_false_alarm_count) <= 0));

figure('Name', 'P45 design Pfa sweep', 'Tag', 'P45');
subplot(2, 1, 1);
plot(range_axis_m, 10*log10(max(profile_power, realmin)), ...
    'Color', [0.65 0.65 0.65], 'LineWidth', 0.9);
hold on;
for probability_index = 1:probability_case_count
    plot(range_axis_m, 10*log10(max(...
        probability_sweep_threshold_power(probability_index, :), realmin)), ...
        'LineWidth', 1.2, 'DisplayName', sprintf('P_{FA}=%.0e', ...
        false_alarm_probability_sweep(probability_index)));
end
grid on;
xlabel('Range (m)');
ylabel('Power (dB power units)');
title('Sweep 1: lower requested P_{FA} raises the local threshold');
legend('Observed profile', 'P_{FA}=10^{-2}', 'P_{FA}=10^{-3}', ...
    'P_{FA}=10^{-4}', 'Location', 'best');
subplot(2, 1, 2);
semilogx(false_alarm_probability_sweep, ...
    probability_sweep_false_alarm_count, 'o-', 'LineWidth', 1.2);
hold on;
semilogx(false_alarm_probability_sweep, ...
    probability_sweep_target_detection_count, 's-', 'LineWidth', 1.2);
grid on;
xlabel('Requested false-alarm probability P_{FA}');
ylabel('Count in this profile (cells)');
title('Realized counts are finite-profile observations, not P_{FA} validation');
legend('Non-target threshold crossings', 'Injected target detections', ...
    'Location', 'best');

%% Sweep 2: scale the entire local scene and verify normalized invariance
background_case_count = numel(background_scale_sweep);
background_sweep_profile_power = zeros(background_case_count, cell_count);
background_sweep_threshold_power = nan(background_case_count, cell_count);
background_sweep_detection_mask = false(background_case_count, cell_count);
background_sweep_false_alarm_count = zeros(1, background_case_count);
background_sweep_target_detection_count = zeros(1, background_case_count);
background_sweep_threshold_ratio = zeros(1, background_case_count);

for background_index = 1:background_case_count
    background_scale = background_scale_sweep(background_index);
    scaled_profile_power = background_scale*profile_power;
    background_sweep_profile_power(background_index, :) = scaled_profile_power;
    for cut_cell = valid_first_cell:valid_last_cell
        leading_training_cells = cut_cell-guard_cells_per_side-...
            training_cells_per_side:cut_cell-guard_cells_per_side-1;
        lagging_training_cells = cut_cell+guard_cells_per_side+1:...
            cut_cell+guard_cells_per_side+training_cells_per_side;
        training_cells = [leading_training_cells lagging_training_cells];
        scaled_noise_estimate_power = mean(scaled_profile_power(training_cells));
        background_sweep_threshold_power(background_index, cut_cell) = ...
            cfar_scale_factor*scaled_noise_estimate_power;
        background_sweep_detection_mask(background_index, cut_cell) = ...
            scaled_profile_power(cut_cell) > ...
            background_sweep_threshold_power(background_index, cut_cell);
    end
    background_sweep_false_alarm_count(background_index) = sum(...
        background_sweep_detection_mask(background_index, :) & ...
        eligible_cut_mask & ~target_mask);
    background_sweep_target_detection_count(background_index) = sum(...
        background_sweep_detection_mask(background_index, target_cells));
    background_sweep_threshold_ratio(background_index) = median(...
        background_sweep_threshold_power(background_index, eligible_cut_mask)./...
        threshold_power(eligible_cut_mask));
    assert(max(abs(background_sweep_threshold_power(...
        background_index, eligible_cut_mask)-background_scale*...
        threshold_power(eligible_cut_mask))) <= comparison_tolerance*...
        max(threshold_power(eligible_cut_mask)));
    assert(isequal(background_sweep_detection_mask(background_index, :), ...
        detection_mask));
end

assert(all(background_sweep_false_alarm_count == baseline_false_alarm_count));
assert(all(background_sweep_target_detection_count == ...
    baseline_target_detection_count));
assert(max(abs(background_sweep_threshold_ratio-background_scale_sweep)) <= ...
    comparison_tolerance);

figure('Name', 'P45 background scale sweep', 'Tag', 'P45');
subplot(2, 1, 1);
hold on;
for background_index = 1:background_case_count
    plot(range_axis_m, 10*log10(max(background_sweep_threshold_power(...
        background_index, :), realmin)), 'LineWidth', 1.2, ...
        'DisplayName', sprintf('Background scale %.1f', ...
        background_scale_sweep(background_index)));
end
grid on;
xlabel('Range (m)');
ylabel('CA-CFAR threshold (dB power units)');
title('Sweep 2: threshold moves with the local power scale');
legend('Location', 'best');
subplot(2, 1, 2);
hold on;
for background_index = 1:background_case_count
    normalized_profile = background_sweep_profile_power(...
        background_index, eligible_cut_mask)./...
        background_sweep_threshold_power(background_index, eligible_cut_mask);
    plot(range_axis_m(eligible_cut_mask), normalized_profile, ...
        'LineWidth', 1.0, 'DisplayName', sprintf('Scale %.1f', ...
        background_scale_sweep(background_index)));
end
plot(range_axis_m(eligible_cut_mask), ...
    ones(1, sum(eligible_cut_mask)), 'k--', 'LineWidth', 1.2);
grid on;
xlabel('Range (m)');
ylabel('Observed power / local threshold (ratio)');
title('Normalized decisions coincide when scene power scales uniformly');
legend('Location', 'best');

%% Intentionally broken case: average dB values instead of linear power
broken_noise_estimate_power = nan(1, cell_count);
broken_threshold_power = nan(1, cell_count);
broken_detection_mask = false(1, cell_count);
for cut_cell = valid_first_cell:valid_last_cell
    leading_training_cells = cut_cell-guard_cells_per_side-...
        training_cells_per_side:cut_cell-guard_cells_per_side-1;
    lagging_training_cells = cut_cell+guard_cells_per_side+1:...
        cut_cell+guard_cells_per_side+training_cells_per_side;
    training_cells = [leading_training_cells lagging_training_cells];
    training_power_db = 10*log10(max(profile_power(training_cells), realmin));
    broken_noise_estimate_power(cut_cell) = ...
        10^(mean(training_power_db)/10);
    broken_threshold_power(cut_cell) = ...
        cfar_scale_factor*broken_noise_estimate_power(cut_cell);
    broken_detection_mask(cut_cell) = ...
        profile_power(cut_cell) > broken_threshold_power(cut_cell);
end

broken_false_alarm_count = sum(broken_detection_mask & ...
    eligible_cut_mask & ~target_mask);
broken_target_detection_count = sum(broken_detection_mask(target_cells));
broken_threshold_ratio = median(broken_threshold_power(eligible_cut_mask)./...
    threshold_power(eligible_cut_mask));
broken_claim_is_valid = false;
assert(all(broken_noise_estimate_power(eligible_cut_mask) <= ...
    noise_estimate_power(eligible_cut_mask)*(1+comparison_tolerance)));
assert(broken_threshold_ratio < 1);
assert(broken_false_alarm_count >= baseline_false_alarm_count);
assert(all(broken_detection_mask(detection_mask)));

% Recovery recomputes the reviewed linear-power arithmetic mean from input.
recovery_noise_estimate_power = nan(1, cell_count);
recovery_threshold_power = nan(1, cell_count);
recovery_detection_mask = false(1, cell_count);
for cut_cell = valid_first_cell:valid_last_cell
    leading_training_cells = cut_cell-guard_cells_per_side-...
        training_cells_per_side:cut_cell-guard_cells_per_side-1;
    lagging_training_cells = cut_cell+guard_cells_per_side+1:...
        cut_cell+guard_cells_per_side+training_cells_per_side;
    training_cells = [leading_training_cells lagging_training_cells];
    recovery_noise_estimate_power(cut_cell) = ...
        mean(profile_power(training_cells));
    recovery_threshold_power(cut_cell) = ...
        cfar_scale_factor*recovery_noise_estimate_power(cut_cell);
    recovery_detection_mask(cut_cell) = profile_power(cut_cell) > ...
        recovery_threshold_power(cut_cell);
end
recovery_exact = isequaln(recovery_noise_estimate_power, ...
    noise_estimate_power) && ...
    isequaln(recovery_threshold_power, threshold_power) && ...
    isequal(recovery_detection_mask, detection_mask);
assert(recovery_exact);

figure('Name', 'P45 broken dB averaging and recovery', 'Tag', 'P45');
subplot(2, 1, 1);
plot(range_axis_m, 10*log10(max(profile_power, realmin)), ...
    'Color', [0.65 0.65 0.65], 'LineWidth', 0.9);
hold on;
plot(range_axis_m, 10*log10(max(threshold_power, realmin)), ...
    'k-', 'LineWidth', 1.4);
plot(range_axis_m, 10*log10(max(broken_threshold_power, realmin)), ...
    'r--', 'LineWidth', 1.3);
grid on;
xlabel('Range (m)');
ylabel('Power (dB power units)');
title('Broken case: averaging in dB biases the background estimate low');
legend('Observed profile', 'Correct linear-power threshold', ...
    'Broken dB-average threshold', 'Location', 'best');
subplot(2, 1, 2);
bar([baseline_false_alarm_count broken_false_alarm_count; ...
    baseline_target_detection_count broken_target_detection_count]);
grid on;
set(gca, 'XTickLabel', {'Non-target crossings', 'Target detections'});
ylabel('Count in this profile (cells)');
title(sprintf('Recovery restores the baseline exactly: %d', recovery_exact));
legend('Correct/recovered', 'Broken dB averaging', 'Location', 'best');

%% Retain compact metrics for inspection after the script finishes
results = struct();
results.random_seed = random_seed;
results.range_axis_m = range_axis_m;
results.background_mean_power = background_mean_power;
results.profile_power = profile_power;
results.target_cells = target_cells;
results.target_snr_db = target_snr_db;
results.training_cells_per_side = training_cells_per_side;
results.guard_cells_per_side = guard_cells_per_side;
results.training_cell_count = training_cell_count;
results.valid_first_cell = valid_first_cell;
results.valid_last_cell = valid_last_cell;
results.design_false_alarm_probability = design_false_alarm_probability;
results.cfar_scale_factor = cfar_scale_factor;
results.eligible_cut_mask = eligible_cut_mask;
results.excluded_edge_mask = excluded_edge_mask;
results.eligible_cut_count = sum(eligible_cut_mask);
results.excluded_edge_count = sum(excluded_edge_mask);
results.example_cut_cell = example_cut_cell;
results.example_leading_training_cells = example_leading_training_cells;
results.example_leading_guard_cells = example_leading_guard_cells;
results.example_lagging_guard_cells = example_lagging_guard_cells;
results.example_lagging_training_cells = example_lagging_training_cells;
results.noise_estimate_power = noise_estimate_power;
results.threshold_power = threshold_power;
results.detection_mask = detection_mask;
results.baseline_detection_count = baseline_detection_count;
results.baseline_target_detection_count = baseline_target_detection_count;
results.baseline_false_alarm_count = baseline_false_alarm_count;
results.low_background_median_threshold = low_background_median_threshold;
results.high_background_median_threshold = high_background_median_threshold;
results.false_alarm_probability_sweep = false_alarm_probability_sweep;
results.probability_sweep_scale_factor = probability_sweep_scale_factor;
results.probability_sweep_false_alarm_count = ...
    probability_sweep_false_alarm_count;
results.probability_sweep_target_detection_count = ...
    probability_sweep_target_detection_count;
results.background_scale_sweep = background_scale_sweep;
results.background_sweep_threshold_ratio = background_sweep_threshold_ratio;
results.background_sweep_false_alarm_count = ...
    background_sweep_false_alarm_count;
results.background_sweep_target_detection_count = ...
    background_sweep_target_detection_count;
results.broken_threshold_ratio = broken_threshold_ratio;
results.broken_false_alarm_count = broken_false_alarm_count;
results.broken_target_detection_count = broken_target_detection_count;
results.broken_claim_is_valid = broken_claim_is_valid;
results.recovery_exact = recovery_exact;
results.estimated_stored_numeric_values = estimated_stored_numeric_values;
results.max_stored_numeric_values = max_stored_numeric_values;
results.max_figure_groups = max_figure_groups;

fprintf('P45 CA-CFAR baseline: alpha=%.6f, eligible CUTs=%d, excluded edges=%d.\n', ...
    cfar_scale_factor, sum(eligible_cut_mask), sum(excluded_edge_mask));
fprintf('Targets detected=%d/%d; non-target crossings=%d in this seeded profile.\n', ...
    baseline_target_detection_count, numel(target_cells), ...
    baseline_false_alarm_count);
fprintf('Median threshold: low-background %.3f, high-background %.3f power units.\n', ...
    low_background_median_threshold, high_background_median_threshold);
fprintf('Broken dB-average threshold ratio=%.3f; recovery exact=%d.\n', ...
    broken_threshold_ratio, recovery_exact);
