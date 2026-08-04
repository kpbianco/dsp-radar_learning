%% P48: Compare GO-CFAR and SO-CFAR at a clutter edge
% Guiding question: Which side of a changing background should control the threshold?
clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P48'));
clc;

%% Visible experiment controls
random_seed = 4801;
range_cell_count = 240;
clutter_edge_cell = 121;             % First cell in the high-clutter region.
low_background_mean_power = 1;
clutter_step_db = 12;
training_cells_per_side = 12;
guard_cells_per_side = 2;
design_false_alarm_probability = 1e-3;
target_cells = [70 116 126 174];
target_excess_power_db = [16 13 13 16];
clutter_contrast_sweep_db = [0 6 12 18];
interferer_excess_power_sweep_db = [-20 0 10 20];
weak_target_snr_db = 13;
sweep_trial_count = 25000;
calibration_iteration_count = 80;

% Fixed reviewed ceilings keep edits finite before any random allocation.
max_range_cells = 320;
max_training_cells_per_side = 24;
max_guard_cells_per_side = 8;
max_targets = 8;
max_sweep_cases = 6;
max_sweep_trials = 30000;
max_calibration_iterations = 100;
max_generated_random_values = 1000000;
max_stored_numeric_values = 1500000;
max_figures = 5;

if max_range_cells ~= 320 || max_training_cells_per_side ~= 24 || ...
        max_guard_cells_per_side ~= 8 || max_targets ~= 8 || ...
        max_sweep_cases ~= 6 || max_sweep_trials ~= 30000 || ...
        max_calibration_iterations ~= 100 || ...
        max_generated_random_values ~= 1000000 || ...
        max_stored_numeric_values ~= 1500000 || max_figures ~= 5
    error('P48:CeilingControls', ...
        'Reviewed resource ceilings must remain fixed.');
end

integer_controls = {random_seed range_cell_count clutter_edge_cell ...
    training_cells_per_side guard_cells_per_side sweep_trial_count ...
    calibration_iteration_count max_range_cells max_training_cells_per_side ...
    max_guard_cells_per_side max_targets max_sweep_cases max_sweep_trials ...
    max_calibration_iterations max_generated_random_values ...
    max_stored_numeric_values max_figures};
for control_index = 1:numel(integer_controls)
    control_value = integer_controls{control_index};
    if ~isscalar(control_value) || ~isnumeric(control_value) || islogical(control_value) || ...
            ~isreal(control_value) || ~isfinite(control_value) || ...
            control_value ~= fix(control_value)
        error('P48:IntegerControls', 'Integer controls must be finite real integer scalars.');
    end
end
real_controls = {low_background_mean_power clutter_step_db ...
    design_false_alarm_probability weak_target_snr_db};
for control_index = 1:numel(real_controls)
    control_value = real_controls{control_index};
    if ~isscalar(control_value) || ~isnumeric(control_value) || islogical(control_value) || ...
            ~isreal(control_value) || ~isfinite(control_value)
        error('P48:RealControls', 'Physical controls must be finite real scalars.');
    end
end
if random_seed ~= 4801 || range_cell_count < 80 || range_cell_count > max_range_cells
    error('P48:DeterminismOrRange', 'Keep the reviewed seed and bounded range-cell count.');
end
if clutter_edge_cell <= 1 || clutter_edge_cell > range_cell_count
    error('P48:Edge', 'The clutter edge must lie inside the range profile.');
end
if low_background_mean_power <= 0 || clutter_step_db < 0 || clutter_step_db > 24
    error('P48:Background', 'Background power must be positive and contrast must be 0 to 24 dB.');
end
if training_cells_per_side < 2 || training_cells_per_side > max_training_cells_per_side || ...
        guard_cells_per_side < 0 || guard_cells_per_side > max_guard_cells_per_side
    error('P48:Stencil', 'Training or guard geometry exceeds reviewed bounds.');
end
stencil_half_width = training_cells_per_side + guard_cells_per_side;
if clutter_edge_cell <= stencil_half_width || ...
        clutter_edge_cell > range_cell_count-stencil_half_width
    error('P48:EdgeStencil', 'The full two-sided stencil must fit around the clutter edge.');
end
if ~isnumeric(target_cells) || ~isreal(target_cells) || ...
        any(~isfinite(target_cells)) || any(target_cells ~= fix(target_cells)) || ...
        isempty(target_cells) || numel(target_cells) > max_targets || ...
        numel(unique(target_cells)) ~= numel(target_cells) || ...
        any(target_cells <= stencil_half_width) || ...
        any(target_cells > range_cell_count-stencil_half_width)
    error('P48:Targets', 'Target cells must be unique bounded integer CUT locations.');
end
if ~isnumeric(target_excess_power_db) || ~isreal(target_excess_power_db) || ...
        any(~isfinite(target_excess_power_db)) || ...
        numel(target_excess_power_db) ~= numel(target_cells)
    error('P48:TargetPower', 'Each target needs one finite real excess-power value.');
end
if ~isnumeric(clutter_contrast_sweep_db) || ~isreal(clutter_contrast_sweep_db) || ...
        any(~isfinite(clutter_contrast_sweep_db)) || ...
        numel(clutter_contrast_sweep_db) < 3 || ...
        numel(clutter_contrast_sweep_db) > max_sweep_cases || ...
        any(diff(clutter_contrast_sweep_db) <= 0) || ...
        ~any(clutter_contrast_sweep_db == clutter_step_db) || ...
        clutter_contrast_sweep_db(1) < 0 || clutter_contrast_sweep_db(end) > 24
    error('P48:ContrastSweep', 'Contrast sweep must increase, include baseline, and stay bounded.');
end
if ~isnumeric(interferer_excess_power_sweep_db) || ...
        ~isreal(interferer_excess_power_sweep_db) || ...
        any(~isfinite(interferer_excess_power_sweep_db)) || ...
        numel(interferer_excess_power_sweep_db) < 3 || ...
        numel(interferer_excess_power_sweep_db) > max_sweep_cases || ...
        any(diff(interferer_excess_power_sweep_db) <= 0) || ...
        interferer_excess_power_sweep_db(1) < -30 || ...
        interferer_excess_power_sweep_db(end) > 30
    error('P48:InterfererSweep', 'Interferer sweep must be finite, increasing, and bounded.');
end
if design_false_alarm_probability <= 0 || design_false_alarm_probability >= 0.1
    error('P48:Pfa', 'Design Pfa must lie strictly between zero and 0.1.');
end
if sweep_trial_count < 1000 || sweep_trial_count > max_sweep_trials || ...
        calibration_iteration_count < 40 || ...
        calibration_iteration_count > max_calibration_iterations
    error('P48:WorkBounds', 'Trial or calibration work exceeds reviewed bounds.');
end
estimated_generated_random_values = range_cell_count + ...
    sweep_trial_count*(2*training_cells_per_side+3);
estimated_stored_numeric_values = ...
    sweep_trial_count*(2*training_cells_per_side+8) + 20*range_cell_count;
if estimated_generated_random_values > max_generated_random_values || ...
        estimated_stored_numeric_values > max_stored_numeric_values || max_figures ~= 5
    error('P48:ResourceCeiling', 'Reviewed random, storage, or figure ceiling exceeded.');
end

%% Calibrate GO and SO independently at the same homogeneous design Pfa
% Each side mean averages T exponential powers. For scale alpha:
% Pfa_SO = 2*sum_{k=0}^{T-1} T^(T+k)*Gamma(T+k) /
%          (Gamma(T)*k!*(2*T+alpha)^(T+k))
% Pfa_GO = 2*(T/(T+alpha))^T - Pfa_SO.
go_scale_factor = calibrated_variant_scale(training_cells_per_side, ...
    design_false_alarm_probability, 'GO', calibration_iteration_count);
so_scale_factor = calibrated_variant_scale(training_cells_per_side, ...
    design_false_alarm_probability, 'SO', calibration_iteration_count);
go_calibrated_pfa = homogeneous_variant_pfa(go_scale_factor, ...
    training_cells_per_side, 'GO');
so_calibrated_pfa = homogeneous_variant_pfa(so_scale_factor, ...
    training_cells_per_side, 'SO');
assert(abs(go_calibrated_pfa-design_false_alarm_probability) < 1e-12);
assert(abs(so_calibrated_pfa-design_false_alarm_probability) < 1e-12);

%% Build the seeded clutter-edge range profile
private_stream = RandStream('mt19937ar', 'Seed', random_seed);
range_cell = (1:range_cell_count).';
high_background_mean_power = low_background_mean_power*10^(clutter_step_db/10);
background_mean_power = low_background_mean_power*ones(range_cell_count, 1);
background_mean_power(clutter_edge_cell:end) = high_background_mean_power;
uniform_power_draw = max(rand(private_stream, range_cell_count, 1), realmin);
background_power = -background_mean_power.*log(uniform_power_draw);
received_power = background_power;
for target_index = 1:numel(target_cells)
    cut = target_cells(target_index);
    received_power(cut) = received_power(cut) + ...
        background_mean_power(cut)*10^(target_excess_power_db(target_index)/10);
end
% Keep the baseline target probes isolated from one another. The estimator sees
% the seeded background; sweep 2 introduces one known reference contaminator.
baseline_reference_power = background_power;

leading_mean_power = nan(range_cell_count, 1);
lagging_mean_power = nan(range_cell_count, 1);
go_threshold_power = nan(range_cell_count, 1);
so_threshold_power = nan(range_cell_count, 1);
go_detection = false(range_cell_count, 1);
so_detection = false(range_cell_count, 1);
valid_cut_cells = (stencil_half_width+1):(range_cell_count-stencil_half_width);
for cut = valid_cut_cells
    leading_cells = (cut-guard_cells_per_side-training_cells_per_side): ...
        (cut-guard_cells_per_side-1);
    lagging_cells = (cut+guard_cells_per_side+1): ...
        (cut+guard_cells_per_side+training_cells_per_side);
    leading_mean_power(cut) = sum(baseline_reference_power(leading_cells))/training_cells_per_side;
    lagging_mean_power(cut) = sum(baseline_reference_power(lagging_cells))/training_cells_per_side;
    go_background_estimate = max(leading_mean_power(cut), lagging_mean_power(cut));
    so_background_estimate = min(leading_mean_power(cut), lagging_mean_power(cut));
    go_threshold_power(cut) = go_scale_factor*go_background_estimate;
    so_threshold_power(cut) = so_scale_factor*so_background_estimate;
    go_detection(cut) = received_power(cut) > go_threshold_power(cut);
    so_detection(cut) = received_power(cut) > so_threshold_power(cut);
end
edge_zone = valid_cut_cells(abs(valid_cut_cells-clutter_edge_cell) <= stencil_half_width);
target_mask = false(range_cell_count, 1);
target_mask(target_cells) = true;
edge_false_alarm_cells = edge_zone(~target_mask(edge_zone));
go_edge_false_alarm_count = sum(go_detection(edge_false_alarm_cells));
so_edge_false_alarm_count = sum(so_detection(edge_false_alarm_cells));
go_missed_target_cells = target_cells(~go_detection(target_cells));
so_missed_target_cells = target_cells(~so_detection(target_cells));

figure('Name', 'P48 baseline range profile', 'Tag', 'P48');
semilogy(range_cell, max(received_power, 1e-6), 'k-', 'LineWidth', 1); hold on;
semilogy(range_cell, go_threshold_power, 'b-', 'LineWidth', 1.4);
semilogy(range_cell, so_threshold_power, 'r--', 'LineWidth', 1.4);
semilogy(target_cells, received_power(target_cells), 'ko', 'MarkerFaceColor', 'y');
plot([clutter_edge_cell clutter_edge_cell], ylim, 'Color', [0.2 0.5 0.2], 'LineStyle', ':');
grid on; xlabel('Range cell'); ylabel('Square-law power (linear units)');
title('Same CUT power, different side-selection thresholds');
legend('Received power', 'GO threshold', 'SO threshold', 'Known targets', ...
    'Clutter edge', 'Location', 'northwest');

%% Inspect the two side estimates around the boundary
inspection_cells = (clutter_edge_cell-stencil_half_width): ...
    (clutter_edge_cell+stencil_half_width);
figure('Name', 'P48 side estimates at edge', 'Tag', 'P48');
subplot(2, 1, 1);
semilogy(inspection_cells, leading_mean_power(inspection_cells), 'c-', 'LineWidth', 1.5); hold on;
semilogy(inspection_cells, lagging_mean_power(inspection_cells), 'm-', 'LineWidth', 1.5);
plot([clutter_edge_cell clutter_edge_cell], ylim, 'k:');
grid on; xlabel('CUT range cell'); ylabel('Mean reference power (linear units)');
title('Leading and lagging reference estimates');
legend('Leading/left mean', 'Lagging/right mean', 'Clutter edge', 'Location', 'northwest');
subplot(2, 1, 2);
semilogy(inspection_cells, go_threshold_power(inspection_cells), 'b-', 'LineWidth', 1.5); hold on;
semilogy(inspection_cells, so_threshold_power(inspection_cells), 'r--', 'LineWidth', 1.5);
semilogy(inspection_cells, received_power(inspection_cells), 'k.', 'MarkerSize', 10);
plot([clutter_edge_cell clutter_edge_cell], ylim, 'k:');
grid on; xlabel('CUT range cell'); ylabel('CUT and threshold power (linear units)');
title(sprintf('GO = %.3f max(side means), SO = %.3f min(side means)', ...
    go_scale_factor, so_scale_factor));
legend('GO threshold', 'SO threshold', 'CUT power', 'Clutter edge', 'Location', 'northwest');

%% Sweep 1: clutter contrast controls high-side edge false alarms
unit_left_reference_power = -log(max(rand(private_stream, sweep_trial_count, ...
    training_cells_per_side), realmin));
unit_right_reference_power = -log(max(rand(private_stream, sweep_trial_count, ...
    training_cells_per_side), realmin));
unit_cut_power = -log(max(rand(private_stream, sweep_trial_count, 1), realmin));
go_edge_false_alarm_probability = zeros(size(clutter_contrast_sweep_db));
so_edge_false_alarm_probability = zeros(size(clutter_contrast_sweep_db));
for contrast_index = 1:numel(clutter_contrast_sweep_db)
    contrast_linear = 10^(clutter_contrast_sweep_db(contrast_index)/10);
    % CUT and lagging references are just inside high clutter; leading references are low.
    leading_trial_mean = sum(unit_left_reference_power, 2)/training_cells_per_side;
    lagging_trial_mean = contrast_linear*sum(unit_right_reference_power, 2)/training_cells_per_side;
    high_side_cut_power = contrast_linear*unit_cut_power;
    go_trial_threshold = go_scale_factor*max(leading_trial_mean, lagging_trial_mean);
    so_trial_threshold = so_scale_factor*min(leading_trial_mean, lagging_trial_mean);
    go_edge_false_alarm_probability(contrast_index) = ...
        sum(high_side_cut_power > go_trial_threshold)/sweep_trial_count;
    so_edge_false_alarm_probability(contrast_index) = ...
        sum(high_side_cut_power > so_trial_threshold)/sweep_trial_count;
end
assert(so_edge_false_alarm_probability(end) > 10*go_edge_false_alarm_probability(end));

figure('Name', 'P48 clutter contrast sweep', 'Tag', 'P48');
semilogy(clutter_contrast_sweep_db, max(go_edge_false_alarm_probability, 0.5/sweep_trial_count), ...
    'bo-', 'LineWidth', 1.5, 'MarkerFaceColor', 'b'); hold on;
semilogy(clutter_contrast_sweep_db, max(so_edge_false_alarm_probability, 0.5/sweep_trial_count), ...
    'rs--', 'LineWidth', 1.5, 'MarkerFaceColor', 'r');
semilogy(clutter_contrast_sweep_db, design_false_alarm_probability*ones(size(clutter_contrast_sweep_db)), ...
    'k:', 'LineWidth', 1.2);
grid on; xlabel('High/low clutter contrast (dB)');
ylabel('Empirical high-side edge false-alarm probability');
title(sprintf('%d paired trials: edge protection as contrast grows', sweep_trial_count));
legend('GO-CFAR', 'SO-CFAR', 'Homogeneous design Pfa', 'Location', 'northwest');

%% Sweep 2: one contaminated side can make GO mask a weak CUT
unit_target_cut_noise = (randn(private_stream, sweep_trial_count, 1) + ...
    1i*randn(private_stream, sweep_trial_count, 1))/sqrt(2);
weak_target_cut_power = abs(unit_target_cut_noise + sqrt(10^(weak_target_snr_db/10))).^2;
clean_left_reference_power = unit_left_reference_power;
clean_right_reference_power = unit_right_reference_power;
go_interferer_sweep_pd = zeros(size(interferer_excess_power_sweep_db));
so_interferer_sweep_pd = zeros(size(interferer_excess_power_sweep_db));
for interferer_index = 1:numel(interferer_excess_power_sweep_db)
    contaminated_left_reference_power = clean_left_reference_power;
    contaminated_left_reference_power(:, 1) = ...
        contaminated_left_reference_power(:, 1) + ...
        10^(interferer_excess_power_sweep_db(interferer_index)/10);
    contaminated_left_mean = sum(contaminated_left_reference_power, 2)/training_cells_per_side;
    clean_right_mean = sum(clean_right_reference_power, 2)/training_cells_per_side;
    go_contaminated_threshold = go_scale_factor*max(contaminated_left_mean, clean_right_mean);
    so_contaminated_threshold = so_scale_factor*min(contaminated_left_mean, clean_right_mean);
    go_interferer_sweep_pd(interferer_index) = ...
        sum(weak_target_cut_power > go_contaminated_threshold)/sweep_trial_count;
    so_interferer_sweep_pd(interferer_index) = ...
        sum(weak_target_cut_power > so_contaminated_threshold)/sweep_trial_count;
end
assert(so_interferer_sweep_pd(end) > go_interferer_sweep_pd(end)+0.25);

figure('Name', 'P48 interfering target sweep', 'Tag', 'P48');
plot(interferer_excess_power_sweep_db, go_interferer_sweep_pd, 'bo-', ...
    'LineWidth', 1.5, 'MarkerFaceColor', 'b'); hold on;
plot(interferer_excess_power_sweep_db, so_interferer_sweep_pd, 'rs--', ...
    'LineWidth', 1.5, 'MarkerFaceColor', 'r');
grid on; ylim([0 1]); xlabel('One leading reference target excess power (dB)');
ylabel('Empirical weak-CUT detection probability');
title(sprintf('Homogeneous background, weak CUT SNR = %.1f dB', weak_target_snr_db));
legend('GO-CFAR', 'SO-CFAR', 'Location', 'southwest');

%% Broken calibration and recovery, then apply the selector to the protected failure
total_training_cell_count = 2*training_cells_per_side;
broken_shared_scale_factor = total_training_cell_count*( ...
    design_false_alarm_probability^(-1/total_training_cell_count)-1);
broken_shared_go_pfa = homogeneous_variant_pfa(broken_shared_scale_factor, ...
    training_cells_per_side, 'GO');
broken_shared_so_pfa = homogeneous_variant_pfa(broken_shared_scale_factor, ...
    training_cells_per_side, 'SO');
broken_shared_claim_is_valid = false;
recovered_equal_pfa = abs(go_calibrated_pfa-design_false_alarm_probability) < 1e-12 && ...
    abs(so_calibrated_pfa-design_false_alarm_probability) < 1e-12;
assert(go_scale_factor < broken_shared_scale_factor && ...
    broken_shared_scale_factor < so_scale_factor);
assert(broken_shared_go_pfa < design_false_alarm_probability && ...
    broken_shared_so_pfa > design_false_alarm_probability && ...
    ~broken_shared_claim_is_valid && recovered_equal_pfa);

baseline_contrast_index = find(clutter_contrast_sweep_db == clutter_step_db, 1);
broken_rule = 'Always use SO because it preserved the contaminated-window target';
broken_edge_false_alarm_probability = ...
    so_edge_false_alarm_probability(baseline_contrast_index);
recovery_rule = 'Use GO when a clutter-edge false alarm is the protected failure';
recovered_edge_false_alarm_probability = ...
    go_edge_false_alarm_probability(baseline_contrast_index);
broken_claim_is_valid = false;
recovery_reduces_edge_false_alarms = ...
    recovered_edge_false_alarm_probability < broken_edge_false_alarm_probability;
assert(~broken_claim_is_valid && recovery_reduces_edge_false_alarms);

figure('Name', 'P48 broken selection and recovery', 'Tag', 'P48');
subplot(1, 2, 1);
bar([broken_shared_go_pfa go_calibrated_pfa; ...
    broken_shared_so_pfa so_calibrated_pfa]);
set(gca, 'YScale', 'log', 'XTick', 1:2, 'XTickLabel', {'GO', 'SO'});
ylabel('Homogeneous false-alarm probability'); grid on;
title('Broken shared CA scale vs separate recovery');
legend('Broken shared scale', 'Recovered calibration', 'Location', 'northwest');
subplot(1, 2, 2);
bar([broken_edge_false_alarm_probability recovered_edge_false_alarm_probability]);
set(gca, 'YScale', 'log', 'XTick', 1:2, ...
    'XTickLabel', {'Broken: always SO', 'Recovered: GO at edge'});
ylabel('High-side edge false-alarm probability'); grid on;
title(sprintf('Paired sweep trials at %.0f dB contrast', clutter_step_db));

%% Retained metrics for inspection and tutor discussion
results = struct();
results.random_seed = random_seed;
results.model = 'independent exponential square-law power with an abrupt two-region mean';
results.range_cell = range_cell;
results.clutter_edge_cell = clutter_edge_cell;
results.background_mean_power = background_mean_power;
results.received_power = received_power;
results.baseline_reference_power = baseline_reference_power;
results.target_cells = target_cells;
results.training_cells_per_side = training_cells_per_side;
results.guard_cells_per_side = guard_cells_per_side;
results.design_false_alarm_probability = design_false_alarm_probability;
results.go_scale_factor = go_scale_factor;
results.so_scale_factor = so_scale_factor;
results.go_calibrated_pfa = go_calibrated_pfa;
results.so_calibrated_pfa = so_calibrated_pfa;
results.leading_mean_power = leading_mean_power;
results.lagging_mean_power = lagging_mean_power;
results.go_threshold_power = go_threshold_power;
results.so_threshold_power = so_threshold_power;
results.go_detection = go_detection;
results.so_detection = so_detection;
results.edge_zone = edge_zone;
results.go_edge_false_alarm_count = go_edge_false_alarm_count;
results.so_edge_false_alarm_count = so_edge_false_alarm_count;
results.go_missed_target_cells = go_missed_target_cells;
results.so_missed_target_cells = so_missed_target_cells;
results.clutter_contrast_sweep_db = clutter_contrast_sweep_db;
results.go_edge_false_alarm_probability = go_edge_false_alarm_probability;
results.so_edge_false_alarm_probability = so_edge_false_alarm_probability;
results.interferer_excess_power_sweep_db = interferer_excess_power_sweep_db;
results.go_interferer_sweep_pd = go_interferer_sweep_pd;
results.so_interferer_sweep_pd = so_interferer_sweep_pd;
results.broken_shared_scale_factor = broken_shared_scale_factor;
results.broken_shared_go_pfa = broken_shared_go_pfa;
results.broken_shared_so_pfa = broken_shared_so_pfa;
results.broken_shared_claim_is_valid = broken_shared_claim_is_valid;
results.recovered_equal_pfa = recovered_equal_pfa;
results.broken_rule = broken_rule;
results.broken_edge_false_alarm_probability = broken_edge_false_alarm_probability;
results.recovery_rule = recovery_rule;
results.recovered_edge_false_alarm_probability = recovered_edge_false_alarm_probability;
results.broken_claim_is_valid = broken_claim_is_valid;
results.recovery_reduces_edge_false_alarms = recovery_reduces_edge_false_alarms;
results.generated_random_value_bound = estimated_generated_random_values;
results.stored_numeric_value_bound = estimated_stored_numeric_values;

fprintf('P48 GO alpha %.6f, SO alpha %.6f at homogeneous Pfa %.3g.\n', ...
    go_scale_factor, so_scale_factor, design_false_alarm_probability);
fprintf('Baseline edge-zone false alarms: GO %d, SO %d.\n', ...
    go_edge_false_alarm_count, so_edge_false_alarm_count);
fprintf('Baseline missed targets: GO %d, SO %d.\n', ...
    numel(go_missed_target_cells), numel(so_missed_target_cells));
fprintf('At %.0f dB clutter contrast, edge Pfa: GO %.4g, SO %.4g.\n', ...
    clutter_step_db, recovered_edge_false_alarm_probability, ...
    broken_edge_false_alarm_probability);

%% Local functions: transparent homogeneous calibration, no CFAR toolbox
function probability = homogeneous_variant_pfa(alpha, training_per_side, variant)
if ~isscalar(alpha) || ~isnumeric(alpha) || ~isreal(alpha) || ...
        ~isfinite(alpha) || alpha < 0
    error('P48:Alpha', 'Scale factor must be a finite nonnegative real scalar.');
end
if ~isscalar(training_per_side) || ~isnumeric(training_per_side) || ...
        ~isreal(training_per_side) || ~isfinite(training_per_side) || ...
        training_per_side < 1 || training_per_side ~= fix(training_per_side)
    error('P48:TrainingCount', 'Per-side training count must be a positive integer.');
end
if ~(ischar(variant) && (strcmp(variant, 'GO') || strcmp(variant, 'SO')))
    error('P48:Variant', 'Variant must be GO or SO.');
end
term_sum = 0;
for order = 0:(training_per_side-1)
    log_term = (training_per_side+order)*log(training_per_side) + ...
        gammaln(training_per_side+order) - gammaln(training_per_side) - ...
        gammaln(order+1) - ...
        (training_per_side+order)*log(2*training_per_side+alpha);
    term_sum = term_sum + exp(log_term);
end
so_probability = 2*term_sum;
if strcmp(variant, 'SO')
    probability = so_probability;
else
    probability = 2*(training_per_side/(training_per_side+alpha))^training_per_side - ...
        so_probability;
end
end

function alpha = calibrated_variant_scale(training_per_side, requested_pfa, variant, iterations)
if ~isscalar(requested_pfa) || ~isnumeric(requested_pfa) || ...
        ~isreal(requested_pfa) || ~isfinite(requested_pfa) || ...
        requested_pfa <= 0 || requested_pfa >= 1
    error('P48:RequestedPfa', 'Requested Pfa must lie strictly between zero and one.');
end
if ~isscalar(iterations) || ~isnumeric(iterations) || ~isreal(iterations) || ...
        ~isfinite(iterations) || iterations < 1 || iterations ~= fix(iterations)
    error('P48:Iterations', 'Calibration iteration count must be a positive integer.');
end
lower_alpha = 0;
upper_alpha = 1;
calibration_bracketed = false;
for bracket_iteration = 1:32
    if homogeneous_variant_pfa(upper_alpha, training_per_side, variant) <= requested_pfa
        calibration_bracketed = true;
        break;
    end
    upper_alpha = 2*upper_alpha;
end
if ~calibration_bracketed
    error('P48:CalibrationBracket', 'Could not bracket a finite scale factor.');
end
for iteration = 1:iterations
    middle_alpha = 0.5*(lower_alpha+upper_alpha);
    if homogeneous_variant_pfa(middle_alpha, training_per_side, variant) > requested_pfa
        lower_alpha = middle_alpha;
    else
        upper_alpha = middle_alpha;
    end
end
alpha = 0.5*(lower_alpha+upper_alpha);
end
