%% P44: Build an Empirical Radar ROC Curve
% Guiding question:
% How does threshold choice trade probability of detection against false alarm?
% Statistic convention: one real, signed, normalized matched-filter output.
% A known positive-polarity target shifts the statistic toward larger values.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P44'));

%% Visible deterministic controls and immutable resource ceilings
random_seed = 4401;
sample_count = 16;
trial_count = 60000;
signal_amplitude = 1.0;
snr_db_sweep = [-6 0 6 12];
baseline_snr_db = 6;
threshold_sigma_sweep = [-1 0 1 2 2.5 3.090232306 3.5 4 5];
design_false_alarm_probability = 0.001;
operating_threshold_index = 6;
trial_count_sweep = [500 2000 10000 60000];
searched_cell_count = 1000000;
broken_training_count = 250;
comparison_tolerance = 1e-9;
probability_tolerance = 0.015;
max_sample_count = 32;
max_trial_count = 60000;
max_snr_cases = 6;
max_threshold_cases = 12;
max_trial_count_cases = 6;
max_searched_cells = 10000000;
max_figure_groups = 5;
max_stored_numeric_values = 2400000;

%% Reject malformed, ambiguous, or unbounded controls before allocation
scalar_controls = [random_seed sample_count trial_count signal_amplitude ...
    baseline_snr_db design_false_alarm_probability ...
    operating_threshold_index searched_cell_count broken_training_count ...
    comparison_tolerance probability_tolerance max_sample_count ...
    max_trial_count max_snr_cases max_threshold_cases ...
    max_trial_count_cases max_searched_cells max_figure_groups ...
    max_stored_numeric_values];
assert(all(isfinite(scalar_controls)));
assert(isreal(scalar_controls) && isreal(snr_db_sweep) && ...
    isreal(threshold_sigma_sweep) && isreal(trial_count_sweep));
assert(~islogical(random_seed) && ~islogical(sample_count) && ...
    ~islogical(trial_count) && ~islogical(snr_db_sweep) && ...
    ~islogical(threshold_sigma_sweep) && ...
    ~islogical(trial_count_sweep) && ~islogical(searched_cell_count));
integer_controls = [random_seed sample_count trial_count ...
    operating_threshold_index trial_count_sweep searched_cell_count ...
    broken_training_count max_sample_count max_trial_count max_snr_cases ...
    max_threshold_cases max_trial_count_cases max_searched_cells ...
    max_figure_groups max_stored_numeric_values];
assert(all(integer_controls == floor(integer_controls)));
assert(random_seed == 4401 && signal_amplitude > 0);
% The reviewed pulse below has exactly 16 samples. Keep this dimension fixed;
% accepting a different in-range value would make the later template/noise
% multiplication structurally inconsistent.
assert(sample_count == 16 && sample_count <= max_sample_count);
assert(trial_count >= 10000 && trial_count <= max_trial_count);
assert(numel(snr_db_sweep) >= 3 && numel(snr_db_sweep) <= max_snr_cases && ...
    all(isfinite(snr_db_sweep)) && all(diff(snr_db_sweep) > 0) && ...
    any(snr_db_sweep == baseline_snr_db));
assert(numel(threshold_sigma_sweep) >= 7 && ...
    numel(threshold_sigma_sweep) <= max_threshold_cases && ...
    all(isfinite(threshold_sigma_sweep)) && ...
    all(diff(threshold_sigma_sweep) > 0));
assert(operating_threshold_index >= 1 && ...
    operating_threshold_index <= numel(threshold_sigma_sweep));
assert(design_false_alarm_probability > 0 && ...
    design_false_alarm_probability < 0.5);
assert(numel(trial_count_sweep) >= 3 && ...
    numel(trial_count_sweep) <= max_trial_count_cases && ...
    all(trial_count_sweep >= 100) && ...
    all(diff(trial_count_sweep) > 0) && ...
    trial_count_sweep(end) == trial_count);
assert(searched_cell_count >= trial_count && ...
    searched_cell_count <= max_searched_cells);
assert(broken_training_count >= 100 && ...
    broken_training_count < trial_count/10);
assert(max_sample_count == 32 && max_trial_count == 60000 && ...
    max_snr_cases == 6 && max_threshold_cases == 12 && ...
    max_trial_count_cases == 6 && max_searched_cells == 10000000 && ...
    max_figure_groups == 5 && max_stored_numeric_values == 2400000);

% This conservative bound counts both full noise matrices even though each is
% cleared before the other is allocated, plus every retained score and table.
estimated_stored_numeric_values = 2*sample_count*trial_count+...
    6*trial_count+100*(numel(snr_db_sweep)*...
    numel(threshold_sigma_sweep)+numel(trial_count_sweep));
assert(estimated_stored_numeric_values <= max_stored_numeric_values);

%% Build the pulse and form independent normalized matched-filter statistics
template = [1 1 1 -1 1 -1 -1 1 -1 1 -1 -1 -1 1 1 -1].';
assert(numel(template) == sample_count);
template_energy = sum(template.^2);
assert(template_energy > 0);

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
unit_noise_h0 = randn(private_stream, sample_count, trial_count);
normalized_noise_h0 = (template.'*unit_noise_h0)/sqrt(template_energy);
baseline_snr_linear = 10^(baseline_snr_db/10);
baseline_noise_rms = signal_amplitude*sqrt(...
    template_energy/baseline_snr_linear);
example_received_h0 = baseline_noise_rms*unit_noise_h0(:, 1);
clear unit_noise_h0;

unit_noise_h1 = randn(private_stream, sample_count, trial_count);
normalized_noise_h1 = (template.'*unit_noise_h1)/sqrt(template_energy);
example_received_h1 = signal_amplitude*template+...
    baseline_noise_rms*unit_noise_h1(:, 1);
clear unit_noise_h1;
assert(~isequal(normalized_noise_h0, normalized_noise_h1));

baseline_d_prime = sqrt(baseline_snr_linear);
baseline_score_h0 = normalized_noise_h0;
baseline_score_h1 = baseline_d_prime+normalized_noise_h1;
example_score_h0 = template.'*example_received_h0/...
    (baseline_noise_rms*sqrt(template_energy));
example_score_h1 = template.'*example_received_h1/...
    (baseline_noise_rms*sqrt(template_energy));
assert(abs(example_score_h0-baseline_score_h0(1)) <= ...
    comparison_tolerance);
assert(abs(example_score_h1-baseline_score_h1(1)) <= ...
    comparison_tolerance);

figure('Name', 'P44 matched-filter statistic formation', 'Tag', 'P44');
subplot(2, 2, 1);
stem(0:sample_count-1, template, 'filled');
grid on;
xlabel('Fast-time sample index');
ylabel('Known pulse amplitude');
title('Known matched-filter template');
subplot(2, 2, 2);
plot(0:sample_count-1, example_received_h0, 'o-', 'LineWidth', 1.1);
hold on;
plot(0:sample_count-1, example_received_h1, 's-', 'LineWidth', 1.1);
grid on;
xlabel('Fast-time sample index');
ylabel('Received amplitude (amplitude units)');
title('One target-absent and one target-present record');
legend('H0: target absent', 'H1: target present', 'Location', 'best');
subplot(2, 2, [3 4]);
histogram(baseline_score_h0, 70, 'Normalization', 'probability');
hold on;
histogram(baseline_score_h1, 70, 'Normalization', 'probability');
grid on;
xlabel('Normalized matched-filter statistic u (noise RMS)');
ylabel('Empirical probability per histogram bin');
title('Matched filtering reduces each record to one decision statistic');
legend('H0', 'H1 at 6 dB', 'Location', 'best');

%% Sweep 1: move one threshold across H0 and several H1 SNR cases
threshold_count = numel(threshold_sigma_sweep);
snr_case_count = numel(snr_db_sweep);
d_prime_sweep = sqrt(10.^(snr_db_sweep/10));
false_alarm_counts = zeros(1, threshold_count);
empirical_pfa = zeros(1, threshold_count);
analytic_pfa = zeros(1, threshold_count);
detection_counts = zeros(snr_case_count, threshold_count);
miss_counts = zeros(snr_case_count, threshold_count);
empirical_pd = zeros(snr_case_count, threshold_count);
analytic_pd = zeros(snr_case_count, threshold_count);

for threshold_index = 1:threshold_count
    threshold_sigma = threshold_sigma_sweep(threshold_index);
    false_alarm_decisions = normalized_noise_h0 > threshold_sigma;
    false_alarm_counts(threshold_index) = sum(false_alarm_decisions);
    empirical_pfa(threshold_index) = ...
        false_alarm_counts(threshold_index)/trial_count;
    analytic_pfa(threshold_index) = 0.5*erfc(...
        threshold_sigma/sqrt(2));
    for snr_index = 1:snr_case_count
        target_present_score = d_prime_sweep(snr_index)+...
            normalized_noise_h1;
        detection_decisions = target_present_score > threshold_sigma;
        detection_counts(snr_index, threshold_index) = ...
            sum(detection_decisions);
        miss_counts(snr_index, threshold_index) = trial_count-...
            detection_counts(snr_index, threshold_index);
        empirical_pd(snr_index, threshold_index) = ...
            detection_counts(snr_index, threshold_index)/trial_count;
        analytic_pd(snr_index, threshold_index) = 0.5*erfc((...
            threshold_sigma-d_prime_sweep(snr_index))/sqrt(2));
    end
end
assert(all(diff(false_alarm_counts) <= 0));
assert(all(all(diff(detection_counts, 1, 2) <= 0)));
assert(all(all(detection_counts+miss_counts == trial_count)));
assert(all(diff(empirical_pd(:, operating_threshold_index)) > 0));
assert(max(abs(empirical_pfa-analytic_pfa)) < probability_tolerance);
assert(max(abs(empirical_pd(:)-analytic_pd(:))) < probability_tolerance);

% Add the limiting thresholds only for drawing the complete ROC endpoints.
roc_empirical_pfa = [1 empirical_pfa 0];
roc_analytic_pfa = [1 analytic_pfa 0];
roc_empirical_pd = [ones(snr_case_count, 1) empirical_pd ...
    zeros(snr_case_count, 1)];
roc_analytic_pd = [ones(snr_case_count, 1) analytic_pd ...
    zeros(snr_case_count, 1)];
probability_plot_floor = 0.5/trial_count;

figure('Name', 'P44 empirical ROC curves', 'Tag', 'P44');
subplot(1, 2, 1);
hold on;
for snr_index = 1:snr_case_count
    plot(roc_empirical_pfa, roc_empirical_pd(snr_index, :), 'o-', ...
        'LineWidth', 1.2, 'DisplayName', ...
        sprintf('Empirical %g dB', snr_db_sweep(snr_index)));
end
plot([0 1], [0 1], 'k:', 'LineWidth', 1.1, ...
    'DisplayName', 'No-skill diagonal');
grid on;
xlabel('False-alarm probability P_{FA}');
ylabel('Detection probability P_D');
title('Sweep threshold: one ROC per matched-filter SNR');
legend('Location', 'southeast');
subplot(1, 2, 2);
hold on;
for snr_index = 1:snr_case_count
    semilogx(max(roc_empirical_pfa, probability_plot_floor), ...
        roc_empirical_pd(snr_index, :), 'o-', 'LineWidth', 1.2, ...
        'DisplayName', sprintf('%g dB', snr_db_sweep(snr_index)));
    semilogx(max(roc_analytic_pfa, probability_plot_floor), ...
        roc_analytic_pd(snr_index, :), '--', 'LineWidth', 0.9, ...
        'HandleVisibility', 'off');
end
grid on;
xlabel('False-alarm probability P_{FA} (log scale)');
ylabel('Detection probability P_D');
title('Low-P_{FA} region: empirical markers, Gaussian model dashed');
legend('Location', 'southeast');

%% Mark one operating point and translate it into false alarms per scan
design_threshold_sigma = sqrt(2)*erfcinv(...
    2*design_false_alarm_probability);
operating_threshold_sigma = ...
    threshold_sigma_sweep(operating_threshold_index);
assert(abs(operating_threshold_sigma-design_threshold_sigma) < 1e-8);
operating_empirical_pfa = empirical_pfa(operating_threshold_index);
operating_analytic_pfa = analytic_pfa(operating_threshold_index);
operating_empirical_pd = empirical_pd(:, operating_threshold_index);
operating_analytic_pd = analytic_pd(:, operating_threshold_index);
expected_false_alarms_per_scan_empirical = ...
    searched_cell_count*operating_empirical_pfa;
expected_false_alarms_per_scan_design = ...
    searched_cell_count*design_false_alarm_probability;
assert(false_alarm_counts(operating_threshold_index) > 0);
assert(abs(operating_analytic_pfa-design_false_alarm_probability) < ...
    comparison_tolerance);
assert(abs(expected_false_alarms_per_scan_design-1000) < ...
    comparison_tolerance);

figure('Name', 'P44 threshold operating-point trade', 'Tag', 'P44');
subplot(2, 1, 1);
semilogy(threshold_sigma_sweep, max(empirical_pfa, ...
    probability_plot_floor), 'o-', 'LineWidth', 1.3);
hold on;
semilogy(threshold_sigma_sweep, max(analytic_pfa, ...
    probability_plot_floor), '--', 'LineWidth', 1.1);
plot(operating_threshold_sigma, max(operating_empirical_pfa, ...
    probability_plot_floor), 'rp', 'MarkerSize', 12, 'LineWidth', 1.4);
grid on;
xlabel('Threshold \gamma (noise RMS)');
ylabel('False-alarm probability P_{FA}');
title(sprintf(['Operating point implies %.0f empirical false alarms ' ...
    'per %d searched cells'], expected_false_alarms_per_scan_empirical, ...
    searched_cell_count));
legend('Empirical', 'Gaussian model', 'Marked operating point', ...
    'Location', 'southwest');
subplot(2, 1, 2);
hold on;
for snr_index = 1:snr_case_count
    plot(threshold_sigma_sweep, empirical_pd(snr_index, :), 'o-', ...
        'LineWidth', 1.2, 'DisplayName', ...
        sprintf('%g dB', snr_db_sweep(snr_index)));
end
grid on;
xlabel('Threshold \gamma (noise RMS)');
ylabel('Detection probability P_D');
title('Raising the same threshold also removes target-present crossings');
legend('Location', 'southwest');

%% Sweep 2: change only Monte Carlo trial count at the operating point
trial_case_count = numel(trial_count_sweep);
trial_sweep_false_alarm_counts = zeros(1, trial_case_count);
trial_sweep_detection_counts = zeros(1, trial_case_count);
trial_sweep_empirical_pfa = zeros(1, trial_case_count);
trial_sweep_empirical_pd = zeros(1, trial_case_count);
trial_sweep_probability_resolution = zeros(1, trial_case_count);
trial_sweep_pfa_standard_error = zeros(1, trial_case_count);
trial_sweep_pd_standard_error = zeros(1, trial_case_count);
for trial_index = 1:trial_case_count
    case_trial_count = trial_count_sweep(trial_index);
    case_h0 = normalized_noise_h0(1:case_trial_count);
    case_h1 = baseline_d_prime+...
        normalized_noise_h1(1:case_trial_count);
    trial_sweep_false_alarm_counts(trial_index) = ...
        sum(case_h0 > operating_threshold_sigma);
    trial_sweep_detection_counts(trial_index) = ...
        sum(case_h1 > operating_threshold_sigma);
    trial_sweep_empirical_pfa(trial_index) = ...
        trial_sweep_false_alarm_counts(trial_index)/case_trial_count;
    trial_sweep_empirical_pd(trial_index) = ...
        trial_sweep_detection_counts(trial_index)/case_trial_count;
    trial_sweep_probability_resolution(trial_index) = 1/case_trial_count;
    trial_sweep_pfa_standard_error(trial_index) = sqrt(max(...
        trial_sweep_empirical_pfa(trial_index)*...
        (1-trial_sweep_empirical_pfa(trial_index))/case_trial_count, 0));
    trial_sweep_pd_standard_error(trial_index) = sqrt(max(...
        trial_sweep_empirical_pd(trial_index)*...
        (1-trial_sweep_empirical_pd(trial_index))/case_trial_count, 0));
end
assert(trial_sweep_false_alarm_counts(end) == ...
    false_alarm_counts(operating_threshold_index));
baseline_snr_index = find(snr_db_sweep == baseline_snr_db, 1);
assert(trial_sweep_detection_counts(end) == ...
    detection_counts(baseline_snr_index, operating_threshold_index));
assert(all(diff(trial_sweep_probability_resolution) < 0));

figure('Name', 'P44 Monte Carlo stability sweep', 'Tag', 'P44');
subplot(2, 1, 1);
loglog(trial_count_sweep, max(trial_sweep_empirical_pfa, ...
    trial_sweep_probability_resolution/2), 'o-', 'LineWidth', 1.3);
hold on;
loglog(trial_count_sweep, design_false_alarm_probability*...
    ones(size(trial_count_sweep)), '--', 'LineWidth', 1.1);
loglog(trial_count_sweep, trial_sweep_probability_resolution, ':', ...
    'LineWidth', 1.1);
grid on;
xlabel('Independent target-absent trial count');
ylabel('P_{FA} estimate or probability resolution');
title('Rare false alarms need enough independent opportunities');
legend('Empirical P_{FA}', 'Gaussian-model P_{FA}', 'One count / trials', ...
    'Location', 'southwest');
subplot(2, 1, 2);
errorbar(trial_count_sweep, trial_sweep_empirical_pd, ...
    1.96*trial_sweep_pd_standard_error, 'o-', 'LineWidth', 1.2);
hold on;
plot(trial_count_sweep, operating_analytic_pd(baseline_snr_index)*...
    ones(size(trial_count_sweep)), '--', 'LineWidth', 1.1);
grid on;
xlabel('Independent target-present trial count');
ylabel('Detection probability P_D at 6 dB');
title('Finite-trial P_D settles around the model value');
legend('Empirical with approximate 95% bars', 'Gaussian model', ...
    'Location', 'best');

%% Intentionally broken case: cherry-pick, tune, and score one tiny bank
sorted_noise_h0 = sort(normalized_noise_h0);
broken_training_h0 = sorted_noise_h0(1:broken_training_count);
broken_holdout_h0 = sorted_noise_h0(broken_training_count+1:end);
assert(max(broken_holdout_h0) > max(broken_training_h0));
broken_tuned_threshold_sigma = max(broken_training_h0);
broken_training_false_alarm_count = sum(...
    broken_training_h0 > broken_tuned_threshold_sigma);
broken_training_empirical_pfa = ...
    broken_training_false_alarm_count/broken_training_count;
broken_holdout_false_alarm_count = sum(...
    broken_holdout_h0 > broken_tuned_threshold_sigma);
broken_holdout_empirical_pfa = broken_holdout_false_alarm_count/...
    numel(broken_holdout_h0);
broken_claim_zero_operational_pfa = true;
broken_claim_is_valid = false;
assert(broken_training_false_alarm_count == 0);
assert(broken_holdout_false_alarm_count > 0);
assert(~broken_claim_is_valid);

%% Recovery: restore a predetermined threshold and independent full banks
recovery_stream = RandStream('mt19937ar', 'Seed', random_seed);
recovery_unit_noise_h0 = randn(recovery_stream, sample_count, trial_count);
recovery_normalized_noise_h0 = ...
    (template.'*recovery_unit_noise_h0)/sqrt(template_energy);
clear recovery_unit_noise_h0;
recovery_unit_noise_h1 = randn(recovery_stream, sample_count, trial_count);
recovery_normalized_noise_h1 = ...
    (template.'*recovery_unit_noise_h1)/sqrt(template_energy);
clear recovery_unit_noise_h1;
recovery_exact = isequal(recovery_normalized_noise_h0, ...
    normalized_noise_h0) && isequal(recovery_normalized_noise_h1, ...
    normalized_noise_h1);
recovered_false_alarm_decisions = ...
    recovery_normalized_noise_h0 > operating_threshold_sigma;
recovered_detection_decisions = baseline_d_prime+...
    recovery_normalized_noise_h1 > operating_threshold_sigma;
recovered_empirical_pfa = ...
    sum(recovered_false_alarm_decisions)/trial_count;
recovered_empirical_pd = ...
    sum(recovered_detection_decisions)/trial_count;
assert(recovery_exact);
assert(abs(recovered_empirical_pfa-operating_empirical_pfa) <= ...
    comparison_tolerance);
assert(abs(recovered_empirical_pd-...
    operating_empirical_pd(baseline_snr_index)) <= comparison_tolerance);

figure('Name', 'P44 broken tuning and recovery', 'Tag', 'P44');
subplot(1, 2, 1);
bar([broken_training_empirical_pfa broken_holdout_empirical_pfa ...
    recovered_empirical_pfa]);
set(gca, 'XTickLabel', {'Tuning bank', 'Held-out bank', ...
    'Recovered design'});
grid on;
ylabel('Empirical false-alarm probability P_{FA}');
title('Zero on reused tuning data is not zero operational P_{FA}');
subplot(1, 2, 2);
plot([operating_empirical_pfa recovered_empirical_pfa], ...
    [operating_empirical_pd(baseline_snr_index) recovered_empirical_pd], ...
    'o-', 'LineWidth', 1.3, 'MarkerSize', 8);
grid on;
xlabel('False-alarm probability P_{FA}');
ylabel('Detection probability P_D at 6 dB');
title('Private-seed recovery reproduces the reviewed operating point');

%% Retained metrics for inspection and tutor dialogue
results.controls = struct( ...
    'random_seed', random_seed, ...
    'sample_count', sample_count, ...
    'trial_count', trial_count, ...
    'signal_amplitude', signal_amplitude, ...
    'snr_db_sweep', snr_db_sweep, ...
    'baseline_snr_db', baseline_snr_db, ...
    'threshold_sigma_sweep', threshold_sigma_sweep, ...
    'design_false_alarm_probability', design_false_alarm_probability, ...
    'trial_count_sweep', trial_count_sweep, ...
    'searched_cell_count', searched_cell_count);
results.template = template;
results.template_energy = template_energy;
results.d_prime_sweep = d_prime_sweep;
results.empirical_pfa = empirical_pfa;
results.analytic_pfa = analytic_pfa;
results.empirical_pd = empirical_pd;
results.analytic_pd = analytic_pd;
results.false_alarm_counts = false_alarm_counts;
results.detection_counts = detection_counts;
results.miss_counts = miss_counts;
results.operating_threshold_sigma = operating_threshold_sigma;
results.operating_empirical_pfa = operating_empirical_pfa;
results.operating_empirical_pd = operating_empirical_pd;
results.expected_false_alarms_per_scan_empirical = ...
    expected_false_alarms_per_scan_empirical;
results.expected_false_alarms_per_scan_design = ...
    expected_false_alarms_per_scan_design;
results.trial_sweep_false_alarm_counts = ...
    trial_sweep_false_alarm_counts;
results.trial_sweep_detection_counts = trial_sweep_detection_counts;
results.trial_sweep_empirical_pfa = trial_sweep_empirical_pfa;
results.trial_sweep_empirical_pd = trial_sweep_empirical_pd;
results.trial_sweep_probability_resolution = ...
    trial_sweep_probability_resolution;
results.broken_tuned_threshold_sigma = broken_tuned_threshold_sigma;
results.broken_training_empirical_pfa = broken_training_empirical_pfa;
results.broken_holdout_empirical_pfa = broken_holdout_empirical_pfa;
results.broken_claim_zero_operational_pfa = ...
    broken_claim_zero_operational_pfa;
results.broken_claim_is_valid = broken_claim_is_valid;
results.recovery_exact = recovery_exact;
results.recovered_empirical_pfa = recovered_empirical_pfa;
results.recovered_empirical_pd = recovered_empirical_pd;
results.estimated_stored_numeric_values = estimated_stored_numeric_values;
results.max_stored_numeric_values = max_stored_numeric_values;
results.max_figure_groups = max_figure_groups;
