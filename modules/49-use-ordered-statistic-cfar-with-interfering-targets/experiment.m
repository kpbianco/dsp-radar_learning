%% P49: Use ordered-statistic CFAR with interfering targets
% Guiding question: How can CFAR resist several contaminated training cells?
clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P49'));
clc;

%% Visible experiment controls
random_seed = 4901;
range_cell_count = 256;
background_mean_power = 1;
training_cells_per_side = 12;
guard_cells_per_side = 2;
design_false_alarm_probability = 1e-3;
primary_target_cell = 128;
primary_target_snr_db = 15;
interfering_target_cells = [115 120 136 141];
interferer_excess_power_db = 20;
os_rank = 18;                       % Ascending rank among N = 24 cells.
interferer_count_sweep = [0 2 4 6 7 8];
interferer_strength_sweep_db = [-20 0 10 20 30];
rank_sweep = [12 16 18 20 22 24];
sweep_target_snr_db = 13;
sweep_trial_count = 20000;
calibration_iteration_count = 80;

% Fixed reviewed ceilings keep edits finite before any random allocation.
max_range_cells = 320;
max_training_cells_per_side = 24;
max_guard_cells_per_side = 8;
max_targets = 10;
max_sweep_cases = 8;
max_sweep_trials = 25000;
max_calibration_iterations = 100;
max_generated_random_values = 600000;
max_stored_numeric_values = 1600000;
max_figures = 5;

if max_range_cells ~= 320 || max_training_cells_per_side ~= 24 || ...
        max_guard_cells_per_side ~= 8 || max_targets ~= 10 || ...
        max_sweep_cases ~= 8 || max_sweep_trials ~= 25000 || ...
        max_calibration_iterations ~= 100 || ...
        max_generated_random_values ~= 600000 || ...
        max_stored_numeric_values ~= 1600000 || max_figures ~= 5
    error('P49:CeilingControls', 'Reviewed resource ceilings must remain fixed.');
end

integer_controls = {random_seed range_cell_count training_cells_per_side ...
    guard_cells_per_side primary_target_cell os_rank sweep_trial_count ...
    calibration_iteration_count max_range_cells max_training_cells_per_side ...
    max_guard_cells_per_side max_targets max_sweep_cases max_sweep_trials ...
    max_calibration_iterations max_generated_random_values ...
    max_stored_numeric_values max_figures};
for control_index = 1:numel(integer_controls)
    control_value = integer_controls{control_index};
    if ~isscalar(control_value) || ~isnumeric(control_value) || islogical(control_value) || ...
            ~isreal(control_value) || ~isfinite(control_value) || ...
            control_value ~= fix(control_value)
        error('P49:IntegerControls', 'Integer controls must be finite real integer scalars.');
    end
end
real_controls = {background_mean_power design_false_alarm_probability ...
    primary_target_snr_db interferer_excess_power_db sweep_target_snr_db};
for control_index = 1:numel(real_controls)
    control_value = real_controls{control_index};
    if ~isscalar(control_value) || ~isnumeric(control_value) || islogical(control_value) || ...
            ~isreal(control_value) || ~isfinite(control_value)
        error('P49:RealControls', 'Physical controls must be finite real scalars.');
    end
end
if random_seed ~= 4901 || range_cell_count < 80 || range_cell_count > max_range_cells
    error('P49:DeterminismOrRange', 'Keep the reviewed seed and bounded range-cell count.');
end
if background_mean_power < 1e-6 || background_mean_power > 1e6
    error('P49:Background', ...
        'Background mean power must stay from 1e-6 through 1e6 linear units.');
end
if primary_target_snr_db < -30 || primary_target_snr_db > 40 || ...
        interferer_excess_power_db < -30 || interferer_excess_power_db > 40 || ...
        sweep_target_snr_db < -30 || sweep_target_snr_db > 40
    error('P49:TargetPowerBounds', 'Target and interferer powers must stay from -30 to 40 dB.');
end
if training_cells_per_side < 2 || ...
        training_cells_per_side > max_training_cells_per_side || ...
        guard_cells_per_side < 0 || guard_cells_per_side > max_guard_cells_per_side
    error('P49:Stencil', 'Training or guard geometry exceeds reviewed bounds.');
end
total_training_cell_count = 2*training_cells_per_side;
stencil_half_width = training_cells_per_side+guard_cells_per_side;
if primary_target_cell <= stencil_half_width || ...
        primary_target_cell > range_cell_count-stencil_half_width
    error('P49:PrimaryCell', 'The primary CUT must support the full two-sided stencil.');
end
if ~isnumeric(interfering_target_cells) || ~isreal(interfering_target_cells) || ...
        any(~isfinite(interfering_target_cells)) || ...
        any(interfering_target_cells ~= fix(interfering_target_cells)) || ...
        isempty(interfering_target_cells) || ...
        numel(interfering_target_cells)+1 > max_targets || ...
        numel(unique(interfering_target_cells)) ~= numel(interfering_target_cells) || ...
        any(interfering_target_cells < 1) || ...
        any(interfering_target_cells > range_cell_count) || ...
        any(interfering_target_cells == primary_target_cell)
    error('P49:InterfererCells', 'Interfering targets must be unique valid non-CUT cells.');
end
primary_left_training_cells = ...
    (primary_target_cell-guard_cells_per_side-training_cells_per_side): ...
    (primary_target_cell-guard_cells_per_side-1);
primary_right_training_cells = ...
    (primary_target_cell+guard_cells_per_side+1): ...
    (primary_target_cell+guard_cells_per_side+training_cells_per_side);
primary_training_cells = [primary_left_training_cells primary_right_training_cells];
if ~all(ismember(interfering_target_cells, primary_training_cells))
    error('P49:ContaminationGeometry', ...
        'Every interfering target must lie in the primary CUT training window.');
end
if design_false_alarm_probability < 1e-6 || design_false_alarm_probability >= 0.1
    error('P49:Pfa', 'Design Pfa must lie from 1e-6 inclusive to 0.1 exclusive.');
end
if os_rank < 1 || os_rank > total_training_cell_count
    error('P49:Rank', 'OS rank must index the ascending training-power list.');
end
if ~isnumeric(interferer_count_sweep) || ~isreal(interferer_count_sweep) || ...
        any(~isfinite(interferer_count_sweep)) || ...
        any(interferer_count_sweep ~= fix(interferer_count_sweep)) || ...
        numel(interferer_count_sweep) < 3 || ...
        numel(interferer_count_sweep) > max_sweep_cases || ...
        any(diff(interferer_count_sweep) <= 0) || interferer_count_sweep(1) ~= 0 || ...
        ~any(interferer_count_sweep == 4) || ...
        ~any(interferer_count_sweep == total_training_cell_count-os_rank+1) || ...
        interferer_count_sweep(end) > total_training_cell_count
    error('P49:CountSweep', 'Interferer-count sweep must start at zero and increase within N.');
end
if ~isnumeric(interferer_strength_sweep_db) || ...
        ~isreal(interferer_strength_sweep_db) || ...
        any(~isfinite(interferer_strength_sweep_db)) || ...
        numel(interferer_strength_sweep_db) < 3 || ...
        numel(interferer_strength_sweep_db) > max_sweep_cases || ...
        any(diff(interferer_strength_sweep_db) <= 0) || ...
        interferer_strength_sweep_db(1) < -30 || ...
        interferer_strength_sweep_db(end) > 40 || ...
        ~any(interferer_strength_sweep_db == interferer_excess_power_db)
    error('P49:StrengthSweep', ...
        'Strength sweep must increase, include baseline, and stay bounded.');
end
if ~isnumeric(rank_sweep) || ~isreal(rank_sweep) || ...
        any(~isfinite(rank_sweep)) || any(rank_sweep ~= fix(rank_sweep)) || ...
        numel(rank_sweep) < 3 || numel(rank_sweep) > max_sweep_cases || ...
        any(diff(rank_sweep) <= 0) || rank_sweep(1) < 1 || ...
        rank_sweep(end) > total_training_cell_count || ~any(rank_sweep == os_rank) || ...
        ~any(rank_sweep == 22)
    error('P49:RankSweep', 'Rank sweep must increase, include baseline, and stay within N.');
end
if sweep_trial_count < 1000 || sweep_trial_count > max_sweep_trials || ...
        calibration_iteration_count < 40 || ...
        calibration_iteration_count > max_calibration_iterations
    error('P49:WorkBounds', 'Trial or calibration work exceeds reviewed bounds.');
end
estimated_generated_random_values = range_cell_count + ...
    sweep_trial_count*(total_training_cell_count+2);
estimated_stored_numeric_values = ...
    sweep_trial_count*(3*total_training_cell_count+5) + 20*range_cell_count;
if estimated_generated_random_values > max_generated_random_values || ...
        estimated_stored_numeric_values > max_stored_numeric_values || max_figures ~= 5
    error('P49:ResourceCeiling', 'Reviewed random, storage, or figure ceiling exceeded.');
end

%% Calibrate CA and the selected OS rank at the same homogeneous Pfa
% For N exponential training powers and ascending order statistic X_(k):
% Pfa_OS(alpha) = product_{j=0}^{k-1} (N-j)/(N-j+alpha).
ca_scale_factor = total_training_cell_count*( ...
    design_false_alarm_probability^(-1/total_training_cell_count)-1);
os_scale_factor = calibrated_os_scale(total_training_cell_count, os_rank, ...
    design_false_alarm_probability, calibration_iteration_count);
os_calibrated_pfa = homogeneous_os_pfa(os_scale_factor, ...
    total_training_cell_count, os_rank);
assert(abs(os_calibrated_pfa-design_false_alarm_probability) < 1e-12);

%% Build the seeded multiple-target range profile
private_stream = RandStream('mt19937ar', 'Seed', random_seed);
range_cell = (1:range_cell_count).';
uniform_power_draw = max(rand(private_stream, range_cell_count, 1), realmin);
background_power = -background_mean_power*log(uniform_power_draw);
received_power = background_power;
received_power(primary_target_cell) = received_power(primary_target_cell) + ...
    background_mean_power*10^(primary_target_snr_db/10);
received_power(interfering_target_cells) = received_power(interfering_target_cells) + ...
    background_mean_power*10^(interferer_excess_power_db/10);

ca_threshold_power = nan(range_cell_count, 1);
os_threshold_power = nan(range_cell_count, 1);
ca_detection = false(range_cell_count, 1);
os_detection = false(range_cell_count, 1);
valid_cut_cells = (stencil_half_width+1):(range_cell_count-stencil_half_width);
for cut = valid_cut_cells
    left_training_cells = ...
        (cut-guard_cells_per_side-training_cells_per_side): ...
        (cut-guard_cells_per_side-1);
    right_training_cells = ...
        (cut+guard_cells_per_side+1): ...
        (cut+guard_cells_per_side+training_cells_per_side);
    reference_cells = [left_training_cells right_training_cells];
    reference_power = received_power(reference_cells);
    sorted_reference_power = sort(reference_power, 'ascend');
    ca_background_estimate = sum(reference_power)/total_training_cell_count;
    os_background_statistic = sorted_reference_power(os_rank);
    ca_threshold_power(cut) = ca_scale_factor*ca_background_estimate;
    os_threshold_power(cut) = os_scale_factor*os_background_statistic;
    ca_detection(cut) = received_power(cut) > ca_threshold_power(cut);
    os_detection(cut) = received_power(cut) > os_threshold_power(cut);
end
all_target_cells = [interfering_target_cells primary_target_cell];
baseline_primary_ca_detected = ca_detection(primary_target_cell);
baseline_primary_os_detected = os_detection(primary_target_cell);
assert(~baseline_primary_ca_detected && baseline_primary_os_detected);

figure('Name', 'P49 baseline contaminated range profile', 'Tag', 'P49');
semilogy(range_cell, max(received_power, 1e-6), 'k-', 'LineWidth', 1); hold on;
semilogy(range_cell, ca_threshold_power, 'b-', 'LineWidth', 1.4);
semilogy(range_cell, os_threshold_power, 'r--', 'LineWidth', 1.4);
semilogy(all_target_cells, received_power(all_target_cells), 'ko', ...
    'MarkerFaceColor', 'y');
plot([primary_target_cell primary_target_cell], ylim, 'g:', 'LineWidth', 1.2);
grid on; xlabel('Range cell'); ylabel('Square-law power (linear units)');
title('Nearby targets contaminate one another''s reference windows');
legend('Received power', 'CA threshold', 'OS threshold', 'Known targets', ...
    'Primary CUT', 'Location', 'northwest');

%% Inspect the primary CUT's sorted reference powers
primary_reference_power = received_power(primary_training_cells);
primary_sorted_reference_power = sort(primary_reference_power, 'ascend');
primary_ca_background_estimate = ...
    sum(primary_reference_power)/total_training_cell_count;
primary_os_background_statistic = primary_sorted_reference_power(os_rank);
primary_contaminated_reference_count = numel(interfering_target_cells);
outlier_capacity = total_training_cell_count-os_rank;

figure('Name', 'P49 sorted primary reference window', 'Tag', 'P49');
semilogy(1:total_training_cell_count, primary_sorted_reference_power, ...
    'ko-', 'LineWidth', 1.2, 'MarkerFaceColor', [0.7 0.7 0.7]); hold on;
semilogy(os_rank, primary_os_background_statistic, 'ro', ...
    'MarkerSize', 9, 'MarkerFaceColor', 'r');
plot(xlim, [primary_ca_background_estimate primary_ca_background_estimate], 'b--');
plot([os_rank os_rank], ylim, 'r:');
grid on; xlabel('Ascending training-power rank k');
ylabel('Training-cell power (linear units)');
title(sprintf('Primary CUT: rank %d leaves %d higher samples', os_rank, outlier_capacity));
legend('Sorted training powers', 'Selected OS sample', 'CA arithmetic mean', ...
    'Selected rank', 'Location', 'northwest');

%% Shared paired trials for all sweeps
unit_reference_power = -log(max(rand(private_stream, sweep_trial_count, ...
    total_training_cell_count), realmin));
unit_target_noise = (randn(private_stream, sweep_trial_count, 1) + ...
    1i*randn(private_stream, sweep_trial_count, 1))/sqrt(2);
target_cut_power = abs(unit_target_noise+sqrt(10^(sweep_target_snr_db/10))).^2;

%% Sweep 1: contamination count crosses the OS outlier capacity
count_sweep_ca_pd = zeros(size(interferer_count_sweep));
count_sweep_os_pd = zeros(size(interferer_count_sweep));
strong_interferer_power = 10^(interferer_excess_power_db/10);
for count_index = 1:numel(interferer_count_sweep)
    interferer_count = interferer_count_sweep(count_index);
    contaminated_reference_power = unit_reference_power;
    if interferer_count > 0
        contaminated_reference_power(:, 1:interferer_count) = ...
            contaminated_reference_power(:, 1:interferer_count) + strong_interferer_power;
    end
    sorted_contaminated_power = sort(contaminated_reference_power, 2, 'ascend');
    ca_trial_threshold = ca_scale_factor*sum(contaminated_reference_power, 2)/ ...
        total_training_cell_count;
    os_trial_threshold = os_scale_factor*sorted_contaminated_power(:, os_rank);
    count_sweep_ca_pd(count_index) = ...
        sum(target_cut_power > ca_trial_threshold)/sweep_trial_count;
    count_sweep_os_pd(count_index) = ...
        sum(target_cut_power > os_trial_threshold)/sweep_trial_count;
    clear contaminated_reference_power sorted_contaminated_power ...
        ca_trial_threshold os_trial_threshold;
end
assert(count_sweep_os_pd(interferer_count_sweep == 4) > ...
    count_sweep_ca_pd(interferer_count_sweep == 4)+0.25);
assert(count_sweep_os_pd(end) < 0.1);

figure('Name', 'P49 interferer count sweep', 'Tag', 'P49');
plot(interferer_count_sweep, count_sweep_ca_pd, 'bo-', ...
    'LineWidth', 1.5, 'MarkerFaceColor', 'b'); hold on;
plot(interferer_count_sweep, count_sweep_os_pd, 'rs--', ...
    'LineWidth', 1.5, 'MarkerFaceColor', 'r');
plot([outlier_capacity outlier_capacity], [0 1], 'k:', 'LineWidth', 1.2);
grid on; ylim([0 1]); xlabel('Strong interfering training cells (count)');
ylabel('Empirical weak-CUT detection probability');
title(sprintf('Rank %d capacity boundary: N-k = %d', os_rank, outlier_capacity));
legend('CA-CFAR', 'OS-CFAR', 'OS high-outlier capacity', 'Location', 'southwest');

%% Sweep 2: strength hurts CA before the selected OS sample enters the tail
strength_sweep_ca_pd = zeros(size(interferer_strength_sweep_db));
strength_sweep_os_pd = zeros(size(interferer_strength_sweep_db));
strength_sweep_interferer_count = primary_contaminated_reference_count;
for strength_index = 1:numel(interferer_strength_sweep_db)
    contaminated_reference_power = unit_reference_power;
    contaminator_power = 10^(interferer_strength_sweep_db(strength_index)/10);
    contaminated_reference_power(:, 1:strength_sweep_interferer_count) = ...
        contaminated_reference_power(:, 1:strength_sweep_interferer_count) + ...
        contaminator_power;
    sorted_contaminated_power = sort(contaminated_reference_power, 2, 'ascend');
    ca_trial_threshold = ca_scale_factor*sum(contaminated_reference_power, 2)/ ...
        total_training_cell_count;
    os_trial_threshold = os_scale_factor*sorted_contaminated_power(:, os_rank);
    strength_sweep_ca_pd(strength_index) = ...
        sum(target_cut_power > ca_trial_threshold)/sweep_trial_count;
    strength_sweep_os_pd(strength_index) = ...
        sum(target_cut_power > os_trial_threshold)/sweep_trial_count;
    clear contaminated_reference_power sorted_contaminated_power ...
        ca_trial_threshold os_trial_threshold;
end
assert(strength_sweep_os_pd(end) > strength_sweep_ca_pd(end)+0.5);

figure('Name', 'P49 interferer strength sweep', 'Tag', 'P49');
plot(interferer_strength_sweep_db, strength_sweep_ca_pd, 'bo-', ...
    'LineWidth', 1.5, 'MarkerFaceColor', 'b'); hold on;
plot(interferer_strength_sweep_db, strength_sweep_os_pd, 'rs--', ...
    'LineWidth', 1.5, 'MarkerFaceColor', 'r');
grid on; ylim([0 1]); xlabel('Each of four interferers excess power (dB)');
ylabel('Empirical weak-CUT detection probability');
title(sprintf('Paired trials, weak CUT SNR = %.1f dB', sweep_target_snr_db));
legend('CA-CFAR', 'OS-CFAR rank 18', 'Location', 'southwest');

%% Rank sweep, intentionally broken reused calibration, and recovery
% Release the last strength-sweep matrices before allocating rank-sweep copies.
clear contaminated_reference_power sorted_contaminated_power ...
    ca_trial_threshold os_trial_threshold;
rank_scale_factors = zeros(size(rank_sweep));
rank_sweep_os_pd = zeros(size(rank_sweep));
broken_reused_scale_pfa = zeros(size(rank_sweep));
recovered_rank_pfa = zeros(size(rank_sweep));
rank_reference_power = unit_reference_power;
rank_reference_power(:, 1:primary_contaminated_reference_count) = ...
    rank_reference_power(:, 1:primary_contaminated_reference_count) + ...
    strong_interferer_power;
sorted_rank_reference_power = sort(rank_reference_power, 2, 'ascend');
for rank_index = 1:numel(rank_sweep)
    candidate_rank = rank_sweep(rank_index);
    rank_scale_factors(rank_index) = calibrated_os_scale( ...
        total_training_cell_count, candidate_rank, ...
        design_false_alarm_probability, calibration_iteration_count);
    candidate_threshold = rank_scale_factors(rank_index)* ...
        sorted_rank_reference_power(:, candidate_rank);
    rank_sweep_os_pd(rank_index) = ...
        sum(target_cut_power > candidate_threshold)/sweep_trial_count;
    broken_reused_scale_pfa(rank_index) = homogeneous_os_pfa( ...
        os_scale_factor, total_training_cell_count, candidate_rank);
    recovered_rank_pfa(rank_index) = homogeneous_os_pfa( ...
        rank_scale_factors(rank_index), total_training_cell_count, candidate_rank);
end
broken_reused_scale_claim_is_valid = false;
recovered_rank_specific_calibration = ...
    max(abs(recovered_rank_pfa-design_false_alarm_probability)) < 1e-12;
assert(broken_reused_scale_pfa(1) > 5*design_false_alarm_probability);
assert(~broken_reused_scale_claim_is_valid && recovered_rank_specific_calibration);
assert(rank_sweep_os_pd(rank_sweep == 18) > rank_sweep_os_pd(rank_sweep == 22)+0.5);

figure('Name', 'P49 rank choice and broken calibration', 'Tag', 'P49');
subplot(1, 2, 1);
plot(rank_sweep, rank_sweep_os_pd, 'mo-', 'LineWidth', 1.5, ...
    'MarkerFaceColor', 'm'); hold on;
plot([total_training_cell_count-primary_contaminated_reference_count ...
    total_training_cell_count-primary_contaminated_reference_count], [0 1], 'k:');
grid on; ylim([0 1]); xlabel('Ascending OS rank k');
ylabel('Empirical weak-CUT detection probability');
title('Four 20 dB reference interferers');
legend('Rank-specific calibrated OS', 'Largest uncontaminated rank', ...
    'Location', 'southwest');
subplot(1, 2, 2);
semilogy(rank_sweep, broken_reused_scale_pfa, 'rx--', 'LineWidth', 1.5); hold on;
semilogy(rank_sweep, recovered_rank_pfa, 'go-', 'LineWidth', 1.5, ...
    'MarkerFaceColor', 'g');
semilogy(rank_sweep, design_false_alarm_probability*ones(size(rank_sweep)), ...
    'k:', 'LineWidth', 1.2);
grid on; xlabel('Ascending OS rank k');
ylabel('Exact homogeneous false-alarm probability');
title('Broken reused rank-18 scale vs recovery');
legend('Broken: reuse rank-18 scale', 'Recovered: recalibrate each rank', ...
    'Design Pfa', 'Location', 'southwest');

%% Retained metrics for inspection and tutor discussion
results = struct();
results.random_seed = random_seed;
results.model = ['independent exponential references with noncoherent point-power ' ...
    'contaminators and a deterministic complex-amplitude CUT in complex Gaussian noise'];
results.range_cell = range_cell;
results.background_power = background_power;
results.received_power = received_power;
results.primary_target_cell = primary_target_cell;
results.interfering_target_cells = interfering_target_cells;
results.primary_target_snr_db = primary_target_snr_db;
results.interferer_excess_power_db = interferer_excess_power_db;
results.primary_training_cells = primary_training_cells;
results.primary_sorted_reference_power = primary_sorted_reference_power;
results.primary_ca_background_estimate = primary_ca_background_estimate;
results.primary_os_background_statistic = primary_os_background_statistic;
results.ca_scale_factor = ca_scale_factor;
results.os_scale_factor = os_scale_factor;
results.design_false_alarm_probability = design_false_alarm_probability;
results.os_calibrated_pfa = os_calibrated_pfa;
results.os_rank = os_rank;
results.outlier_capacity = outlier_capacity;
results.ca_threshold_power = ca_threshold_power;
results.os_threshold_power = os_threshold_power;
results.ca_detection = ca_detection;
results.os_detection = os_detection;
results.baseline_primary_ca_detected = baseline_primary_ca_detected;
results.baseline_primary_os_detected = baseline_primary_os_detected;
results.interferer_count_sweep = interferer_count_sweep;
results.sweep_target_snr_db = sweep_target_snr_db;
results.sweep_trial_count = sweep_trial_count;
results.count_sweep_ca_pd = count_sweep_ca_pd;
results.count_sweep_os_pd = count_sweep_os_pd;
results.interferer_strength_sweep_db = interferer_strength_sweep_db;
results.strength_sweep_ca_pd = strength_sweep_ca_pd;
results.strength_sweep_os_pd = strength_sweep_os_pd;
results.rank_sweep = rank_sweep;
results.rank_outlier_capacity = total_training_cell_count-rank_sweep;
results.rank_scale_factors = rank_scale_factors;
results.rank_sweep_os_pd = rank_sweep_os_pd;
results.broken_reused_scale_pfa = broken_reused_scale_pfa;
results.recovered_rank_pfa = recovered_rank_pfa;
results.broken_reused_scale_claim_is_valid = broken_reused_scale_claim_is_valid;
results.recovered_rank_specific_calibration = recovered_rank_specific_calibration;
results.generated_random_value_bound = estimated_generated_random_values;
results.stored_numeric_value_bound = estimated_stored_numeric_values;

fprintf('P49 CA alpha %.6f, OS rank-%d alpha %.6f at Pfa %.3g.\n', ...
    ca_scale_factor, os_rank, os_scale_factor, design_false_alarm_probability);
fprintf('Primary CUT detected: CA %d, OS %d; four cells contaminate its window.\n', ...
    baseline_primary_ca_detected, baseline_primary_os_detected);
fprintf('Rank %d leaves %d higher samples; count sweep crosses that boundary.\n', ...
    os_rank, outlier_capacity);

%% Local functions: transparent OS probability and bounded calibration
function probability = homogeneous_os_pfa(alpha, training_count, rank)
if ~isscalar(alpha) || ~isnumeric(alpha) || islogical(alpha) || ...
        ~isreal(alpha) || ~isfinite(alpha) || alpha < 0
    error('P49:Alpha', 'Scale factor must be a finite nonnegative real scalar.');
end
if ~isscalar(training_count) || ~isnumeric(training_count) || ...
        islogical(training_count) || ~isreal(training_count) || ...
        ~isfinite(training_count) || training_count < 1 || ...
        training_count ~= fix(training_count)
    error('P49:TrainingCount', 'Training count must be a positive integer.');
end
if ~isscalar(rank) || ~isnumeric(rank) || islogical(rank) || ...
        ~isreal(rank) || ~isfinite(rank) || rank < 1 || ...
        rank > training_count || rank ~= fix(rank)
    error('P49:ProbabilityRank', 'Rank must be an integer from one through N.');
end
log_probability = 0;
for spacing_index = 0:(rank-1)
    log_probability = log_probability + ...
        log(training_count-spacing_index) - ...
        log(training_count-spacing_index+alpha);
end
probability = exp(log_probability);
end

function alpha = calibrated_os_scale(training_count, rank, requested_pfa, iterations)
if ~isscalar(requested_pfa) || ~isnumeric(requested_pfa) || ...
        islogical(requested_pfa) || ~isreal(requested_pfa) || ...
        ~isfinite(requested_pfa) || requested_pfa <= 0 || requested_pfa >= 1
    error('P49:RequestedPfa', 'Requested Pfa must lie strictly between zero and one.');
end
if ~isscalar(iterations) || ~isnumeric(iterations) || islogical(iterations) || ...
        ~isreal(iterations) || ~isfinite(iterations) || ...
        iterations < 1 || iterations ~= fix(iterations)
    error('P49:Iterations', 'Calibration iterations must be a positive integer.');
end
lower_alpha = 0;
upper_alpha = 1;
calibration_bracketed = false;
for bracket_iteration = 1:32
    if homogeneous_os_pfa(upper_alpha, training_count, rank) <= requested_pfa
        calibration_bracketed = true;
        break;
    end
    upper_alpha = 2*upper_alpha;
end
if ~calibration_bracketed
    error('P49:CalibrationBracket', 'Could not bracket a finite OS scale factor.');
end
for iteration = 1:iterations
    middle_alpha = 0.5*(lower_alpha+upper_alpha);
    if homogeneous_os_pfa(middle_alpha, training_count, rank) > requested_pfa
        lower_alpha = middle_alpha;
    else
        upper_alpha = middle_alpha;
    end
end
alpha = 0.5*(lower_alpha+upper_alpha);
end
