%% P43: Use a Fixed Detection Threshold
% Guiding question:
% Why does a threshold that works in one noise level fail in another?
% Statistic convention: one real, signed matched-filter amplitude per range
% cell. A known positive-polarity target adds positive amplitude.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P43'));

%% Visible deterministic controls and immutable resource ceilings
random_seed = 4301;
range_cell_count = 256;
target_cell_indices = [48 103 171 226];
trial_count = 20000;
reference_noise_rms = 1.0;
target_amplitude = 4.0;
design_false_alarm_probability = 0.01;
noise_rms_ratios = [0.75 1.00 1.25 1.50 2.00];
clutter_pedestal_ratios = [0 0.5 1.0 1.5 2.0];
comparison_tolerance = 1e-12;
probability_tolerance = 0.01;
max_range_cells = 512;
max_trials = 25000;
max_targets = 8;
max_sweep_cases = 9;
max_figure_groups = 5;
max_stored_numeric_values = 800000;

%% Reject malformed, ambiguous, or unbounded controls before allocation
positive_controls = [range_cell_count trial_count reference_noise_rms ...
    target_amplitude design_false_alarm_probability ...
    comparison_tolerance probability_tolerance max_range_cells max_trials ...
    max_targets max_sweep_cases max_figure_groups ...
    max_stored_numeric_values];
assert(all(isfinite(positive_controls)) && all(positive_controls > 0));
assert(~islogical(random_seed) && ~islogical(range_cell_count) && ...
    ~islogical(trial_count) && ~islogical(target_cell_indices) && ...
    ~islogical(noise_rms_ratios) && ~islogical(clutter_pedestal_ratios));
assert(isfinite(random_seed) && random_seed == floor(random_seed) && ...
    random_seed == 4301);
integer_controls = [range_cell_count target_cell_indices trial_count ...
    max_range_cells max_trials max_targets max_sweep_cases ...
    max_figure_groups max_stored_numeric_values];
assert(all(integer_controls == floor(integer_controls)));
assert(max_range_cells == 512 && max_trials == 25000 && ...
    max_targets == 8 && max_sweep_cases == 9 && ...
    max_figure_groups == 5 && max_stored_numeric_values == 800000);
assert(range_cell_count >= 64 && range_cell_count <= max_range_cells);
assert(trial_count >= 10000 && trial_count <= max_trials);
assert(numel(target_cell_indices) >= 2 && ...
    numel(target_cell_indices) <= max_targets);
assert(all(target_cell_indices >= 1) && ...
    all(target_cell_indices <= range_cell_count) && ...
    all(diff(target_cell_indices) > 0));
assert(design_false_alarm_probability > 0 && ...
    design_false_alarm_probability < 0.5);
assert(numel(noise_rms_ratios) >= 3 && ...
    numel(noise_rms_ratios) <= max_sweep_cases && ...
    all(isfinite(noise_rms_ratios)) && all(noise_rms_ratios > 0) && ...
    all(diff(noise_rms_ratios) > 0) && ...
    any(abs(noise_rms_ratios-1) <= comparison_tolerance));
assert(numel(clutter_pedestal_ratios) >= 3 && ...
    numel(clutter_pedestal_ratios) <= max_sweep_cases && ...
    all(isfinite(clutter_pedestal_ratios)) && ...
    all(clutter_pedestal_ratios >= 0) && ...
    all(diff(clutter_pedestal_ratios) > 0) && ...
    clutter_pedestal_ratios(1) == 0);

% This deliberately counts overwritten loop temporaries as simultaneously
% live, plus the retained trial-by-noise-case decision matrix.
estimated_stored_numeric_values = 20*trial_count+...
    trial_count*numel(noise_rms_ratios)+8*range_cell_count+...
    40*(numel(noise_rms_ratios)+...
    numel(clutter_pedestal_ratios));
assert(estimated_stored_numeric_values <= max_stored_numeric_values);
assert(max_figure_groups >= 5);

%% Calibrate one absolute threshold at the reference background
% H0: x=n, H1: x=A+n, n~N(0,sigma^2), decide H1 when x>gamma.
% P_FA=Q(gamma/sigma); P_D=Q((gamma-A)/sigma),
% where Q(u)=0.5*erfc(u/sqrt(2)).
normalized_threshold = sqrt(2)*erfcinv(...
    2*design_false_alarm_probability);
fixed_threshold_amplitude = reference_noise_rms*normalized_threshold;
assert(isfinite(normalized_threshold) && normalized_threshold > 0);
assert(fixed_threshold_amplitude < target_amplitude);

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
standard_noise_h0 = randn(private_stream, trial_count, 1);
standard_noise_h1 = randn(private_stream, trial_count, 1);
range_profile_noise = reference_noise_rms*...
    randn(private_stream, range_cell_count, 1);
assert(~isequal(standard_noise_h0, standard_noise_h1));

%% Baseline range profile and conditioned decision bookkeeping
target_mask = false(range_cell_count, 1);
target_mask(target_cell_indices) = true;
baseline_range_profile = range_profile_noise;
baseline_range_profile(target_mask) = ...
    baseline_range_profile(target_mask)+target_amplitude;
baseline_range_detections = baseline_range_profile > ...
    fixed_threshold_amplitude;
profile_false_alarm_count = sum(baseline_range_detections & ~target_mask);
profile_detection_count = sum(baseline_range_detections & target_mask);
profile_miss_count = sum(~baseline_range_detections & target_mask);
assert(profile_detection_count+profile_miss_count == numel(target_cell_indices));

figure('Name', 'P43 fixed-threshold range profile', 'Tag', 'P43');
stem(1:range_cell_count, baseline_range_profile, '.', 'LineWidth', 0.8);
hold on;
plot([1 range_cell_count], fixed_threshold_amplitude*[1 1], 'r--', ...
    'LineWidth', 1.4);
plot(target_cell_indices, baseline_range_profile(target_mask), 'ko', ...
    'MarkerSize', 7, 'LineWidth', 1.2);
plot(find(baseline_range_detections), ...
    baseline_range_profile(baseline_range_detections), 'rx', ...
    'MarkerSize', 8, 'LineWidth', 1.2);
grid on;
xlabel('Range-cell index');
ylabel('Signed detector amplitude (amplitude units)');
title('One fixed threshold turns cell amplitudes into decisions');
legend('Measured cell', 'Fixed threshold', 'True target', ...
    'Threshold crossing', 'Location', 'best');

%% Baseline ensemble: verify target-absent and target-present probabilities
baseline_h0 = reference_noise_rms*standard_noise_h0;
baseline_h1 = target_amplitude+reference_noise_rms*standard_noise_h1;
baseline_false_alarm_decisions = baseline_h0 > fixed_threshold_amplitude;
baseline_detection_decisions = baseline_h1 > fixed_threshold_amplitude;
baseline_false_alarm_count = sum(baseline_false_alarm_decisions);
baseline_detection_count = sum(baseline_detection_decisions);
baseline_miss_count = trial_count-baseline_detection_count;
baseline_empirical_pfa = baseline_false_alarm_count/trial_count;
baseline_empirical_pd = baseline_detection_count/trial_count;
baseline_empirical_pmiss = baseline_miss_count/trial_count;
baseline_analytic_pfa = 0.5*erfc(fixed_threshold_amplitude/...
    (sqrt(2)*reference_noise_rms));
baseline_analytic_pd = 0.5*erfc((fixed_threshold_amplitude-...
    target_amplitude)/(sqrt(2)*reference_noise_rms));
assert(abs(baseline_analytic_pfa-design_false_alarm_probability) <= ...
    comparison_tolerance);
assert(abs(baseline_empirical_pfa-baseline_analytic_pfa) < ...
    probability_tolerance);
assert(abs(baseline_empirical_pd-baseline_analytic_pd) < ...
    probability_tolerance);
assert(abs(baseline_empirical_pd+baseline_empirical_pmiss-1) <= ...
    comparison_tolerance);

figure('Name', 'P43 conditioned baseline distributions', 'Tag', 'P43');
histogram(baseline_h0, 60, 'Normalization', 'probability');
hold on;
histogram(baseline_h1, 60, 'Normalization', 'probability');
plot(fixed_threshold_amplitude*[1 1], ylim, 'k--', 'LineWidth', 1.4);
grid on;
xlabel('Signed detector amplitude (amplitude units)');
ylabel('Empirical probability per histogram bin');
title('False alarms use H0 cells; detections and misses use H1 cells');
legend('Target absent (H0)', 'Target present (H1)', 'Fixed threshold', ...
    'Location', 'best');

%% Sweep 1: hold the threshold and target fixed while noise RMS changes
noise_case_count = numel(noise_rms_ratios);
noise_rms_sweep = reference_noise_rms*noise_rms_ratios;
noise_empirical_pfa = zeros(1, noise_case_count);
noise_empirical_pd = zeros(1, noise_case_count);
noise_analytic_pfa = zeros(1, noise_case_count);
noise_analytic_pd = zeros(1, noise_case_count);
noise_false_alarm_counts = zeros(1, noise_case_count);
noise_detection_counts = zeros(1, noise_case_count);
noise_miss_counts = zeros(1, noise_case_count);
fixed_noise_decisions_h0 = false(trial_count, noise_case_count);
for case_index = 1:noise_case_count
    case_sigma = noise_rms_sweep(case_index);
    case_h0 = case_sigma*standard_noise_h0;
    case_h1 = target_amplitude+case_sigma*standard_noise_h1;
    fixed_noise_decisions_h0(:, case_index) = ...
        case_h0 > fixed_threshold_amplitude;
    case_detection_decisions = case_h1 > fixed_threshold_amplitude;
    noise_false_alarm_counts(case_index) = ...
        sum(fixed_noise_decisions_h0(:, case_index));
    noise_detection_counts(case_index) = sum(case_detection_decisions);
    noise_miss_counts(case_index) = trial_count-...
        noise_detection_counts(case_index);
    noise_empirical_pfa(case_index) = ...
        noise_false_alarm_counts(case_index)/trial_count;
    noise_empirical_pd(case_index) = ...
        noise_detection_counts(case_index)/trial_count;
    noise_analytic_pfa(case_index) = 0.5*erfc(...
        fixed_threshold_amplitude/(sqrt(2)*case_sigma));
    noise_analytic_pd(case_index) = 0.5*erfc((...
        fixed_threshold_amplitude-target_amplitude)/(sqrt(2)*case_sigma));
end
assert(all(diff(noise_false_alarm_counts) > 0));
assert(all(diff(noise_detection_counts) < 0));
assert(all(noise_detection_counts+noise_miss_counts == trial_count));
assert(max(abs(noise_empirical_pfa-noise_analytic_pfa)) < ...
    probability_tolerance);
assert(max(abs(noise_empirical_pd-noise_analytic_pd)) < ...
    probability_tolerance);

figure('Name', 'P43 fixed threshold versus noise RMS', 'Tag', 'P43');
subplot(2, 1, 1);
plot(noise_rms_ratios, noise_empirical_pfa, 'o-', 'LineWidth', 1.3);
hold on;
plot(noise_rms_ratios, noise_analytic_pfa, '--', 'LineWidth', 1.2);
grid on;
xlabel('Noise RMS / reference noise RMS');
ylabel('False-alarm probability P_{FA}');
title('Fixed amplitude threshold loses its designed false-alarm rate');
legend('Empirical', 'Gaussian model', 'Location', 'best');
subplot(2, 1, 2);
plot(noise_rms_ratios, 1-noise_empirical_pd, 'o-', 'LineWidth', 1.3);
hold on;
plot(noise_rms_ratios, 1-noise_analytic_pd, '--', 'LineWidth', 1.2);
grid on;
xlabel('Noise RMS / reference noise RMS');
ylabel('Miss probability P_{miss}');
title('The same fixed target is missed more often as noise spreads');
legend('Empirical', 'Gaussian model', 'Location', 'best');

%% Sweep 2: hold noise, target, and threshold fixed; raise clutter pedestal
clutter_case_count = numel(clutter_pedestal_ratios);
clutter_pedestal_sweep = reference_noise_rms*clutter_pedestal_ratios;
clutter_empirical_pfa = zeros(1, clutter_case_count);
clutter_empirical_pd = zeros(1, clutter_case_count);
clutter_analytic_pfa = zeros(1, clutter_case_count);
clutter_analytic_pd = zeros(1, clutter_case_count);
clutter_false_alarm_counts = zeros(1, clutter_case_count);
clutter_detection_counts = zeros(1, clutter_case_count);
clutter_miss_counts = zeros(1, clutter_case_count);
for case_index = 1:clutter_case_count
    case_pedestal = clutter_pedestal_sweep(case_index);
    clutter_h0 = case_pedestal+reference_noise_rms*standard_noise_h0;
    clutter_h1 = case_pedestal+target_amplitude+...
        reference_noise_rms*standard_noise_h1;
    clutter_false_alarm_counts(case_index) = ...
        sum(clutter_h0 > fixed_threshold_amplitude);
    clutter_detection_counts(case_index) = ...
        sum(clutter_h1 > fixed_threshold_amplitude);
    clutter_miss_counts(case_index) = trial_count-...
        clutter_detection_counts(case_index);
    clutter_empirical_pfa(case_index) = ...
        clutter_false_alarm_counts(case_index)/trial_count;
    clutter_empirical_pd(case_index) = ...
        clutter_detection_counts(case_index)/trial_count;
    clutter_analytic_pfa(case_index) = 0.5*erfc((...
        fixed_threshold_amplitude-case_pedestal)/...
        (sqrt(2)*reference_noise_rms));
    clutter_analytic_pd(case_index) = 0.5*erfc((...
        fixed_threshold_amplitude-case_pedestal-target_amplitude)/...
        (sqrt(2)*reference_noise_rms));
end
assert(all(diff(clutter_false_alarm_counts) > 0));
assert(all(diff(clutter_detection_counts) >= 0));
assert(all(clutter_detection_counts+clutter_miss_counts == trial_count));
assert(max(abs(clutter_empirical_pfa-clutter_analytic_pfa)) < ...
    probability_tolerance);
assert(max(abs(clutter_empirical_pd-clutter_analytic_pd)) < ...
    probability_tolerance);

figure('Name', 'P43 fixed threshold versus clutter pedestal', 'Tag', 'P43');
subplot(2, 1, 1);
plot(clutter_pedestal_ratios, clutter_empirical_pfa, 'o-', ...
    'LineWidth', 1.3);
hold on;
plot(clutter_pedestal_ratios, clutter_analytic_pfa, '--', ...
    'LineWidth', 1.2);
grid on;
xlabel('Positive clutter pedestal / reference noise RMS');
ylabel('False-alarm probability P_{FA}');
title('A shifted target-absent background crosses the fixed threshold');
legend('Empirical', 'Gaussian model', 'Location', 'best');
subplot(2, 1, 2);
plot(clutter_pedestal_ratios, clutter_miss_counts, 'o-', ...
    'LineWidth', 1.3);
grid on;
xlabel('Positive clutter pedestal / reference noise RMS');
ylabel('Missed target count out of trials');
title('More crossings do not mean the detector became more selective');

%% Intentionally broken case: silently adapt to each true noise RMS
adaptive_pfa = zeros(1, noise_case_count);
adaptive_threshold_normalized = fixed_threshold_amplitude/...
    reference_noise_rms;
for case_index = 1:noise_case_count
    case_sigma = noise_rms_sweep(case_index);
    normalized_h0 = (case_sigma*standard_noise_h0)/case_sigma;
    adaptive_decisions = normalized_h0 > adaptive_threshold_normalized;
    adaptive_pfa(case_index) = sum(adaptive_decisions)/trial_count;
end
broken_fixed_threshold_claim = false;
assert(max(abs(adaptive_pfa-adaptive_pfa(1))) <= comparison_tolerance);

%% Recovery: restore one threshold in native amplitude units
recovered_pfa = zeros(1, noise_case_count);
recovery_exact = true;
for case_index = 1:noise_case_count
    recovered_h0 = noise_rms_sweep(case_index)*standard_noise_h0;
    recovered_decisions_h0 = recovered_h0 > fixed_threshold_amplitude;
    recovery_exact = recovery_exact && isequal(recovered_decisions_h0, ...
        fixed_noise_decisions_h0(:, case_index));
    recovered_pfa(case_index) = sum(recovered_decisions_h0)/trial_count;
end
assert(recovery_exact);
assert(max(abs(recovered_pfa-noise_empirical_pfa)) <= ...
    comparison_tolerance);

figure('Name', 'P43 broken adaptation and fixed recovery', 'Tag', 'P43');
plot(noise_rms_ratios, noise_empirical_pfa, 'o-', 'LineWidth', 1.3);
hold on;
plot(noise_rms_ratios, adaptive_pfa, 's--', 'LineWidth', 1.3);
plot(noise_rms_ratios, recovered_pfa, 'x:', 'LineWidth', 1.4);
grid on;
xlabel('Noise RMS / reference noise RMS');
ylabel('False-alarm probability P_{FA}');
title('Normalizing by true case RMS is adaptation, not a fixed threshold');
legend('Actual fixed threshold', 'Broken claim: hidden adaptation', ...
    'Recovered fixed threshold', 'Location', 'best');

%% Retained metrics for inspection and tutor dialogue
fprintf('Fixed threshold = %.4f amplitude units (%.4f reference sigma)\n', ...
    fixed_threshold_amplitude, normalized_threshold);
fprintf('Baseline P_FA empirical/model = %.5f / %.5f\n', ...
    baseline_empirical_pfa, baseline_analytic_pfa);
fprintf('Baseline P_D empirical/model = %.5f / %.5f\n', ...
    baseline_empirical_pd, baseline_analytic_pd);
fprintf('Noise sweep false alarms = %s out of %d H0 trials\n', ...
    mat2str(noise_false_alarm_counts), trial_count);
fprintf('Noise sweep misses = %s out of %d H1 trials\n', ...
    mat2str(noise_miss_counts), trial_count);
fprintf('Clutter sweep false alarms = %s out of %d H0 trials\n', ...
    mat2str(clutter_false_alarm_counts), trial_count);
fprintf('Broken hidden-adaptation P_FA = %s\n', mat2str(adaptive_pfa, 5));
fprintf('Exact fixed-threshold recovery = %d\n', recovery_exact);

results = struct();
results.random_seed = random_seed;
results.statistic_model = ...
    'real signed positive-polarity amplitude; decide H1 when x > gamma';
results.range_cell_count = range_cell_count;
results.target_cell_indices = target_cell_indices;
results.trial_count_per_hypothesis = trial_count;
results.reference_noise_rms = reference_noise_rms;
results.target_amplitude = target_amplitude;
results.design_false_alarm_probability = design_false_alarm_probability;
results.fixed_threshold_amplitude = fixed_threshold_amplitude;
results.normalized_threshold = normalized_threshold;
results.profile_false_alarm_count = profile_false_alarm_count;
results.profile_detection_count = profile_detection_count;
results.profile_miss_count = profile_miss_count;
results.baseline_empirical_pfa = baseline_empirical_pfa;
results.baseline_analytic_pfa = baseline_analytic_pfa;
results.baseline_empirical_pd = baseline_empirical_pd;
results.baseline_analytic_pd = baseline_analytic_pd;
results.baseline_empirical_pmiss = baseline_empirical_pmiss;
results.noise_rms_ratios = noise_rms_ratios;
results.noise_false_alarm_counts = noise_false_alarm_counts;
results.noise_detection_counts = noise_detection_counts;
results.noise_miss_counts = noise_miss_counts;
results.noise_empirical_pfa = noise_empirical_pfa;
results.noise_empirical_pd = noise_empirical_pd;
results.noise_analytic_pfa = noise_analytic_pfa;
results.noise_analytic_pd = noise_analytic_pd;
results.clutter_pedestal_ratios = clutter_pedestal_ratios;
results.clutter_false_alarm_counts = clutter_false_alarm_counts;
results.clutter_detection_counts = clutter_detection_counts;
results.clutter_miss_counts = clutter_miss_counts;
results.clutter_empirical_pfa = clutter_empirical_pfa;
results.clutter_empirical_pd = clutter_empirical_pd;
results.clutter_analytic_pfa = clutter_analytic_pfa;
results.clutter_analytic_pd = clutter_analytic_pd;
results.broken_fixed_threshold_claim = broken_fixed_threshold_claim;
results.adaptive_pfa = adaptive_pfa;
results.recovery_exact = recovery_exact;
results.recovered_pfa = recovered_pfa;
results.estimated_stored_numeric_values = estimated_stored_numeric_values;
results.max_stored_numeric_values = max_stored_numeric_values;
results.max_figure_groups = max_figure_groups;
