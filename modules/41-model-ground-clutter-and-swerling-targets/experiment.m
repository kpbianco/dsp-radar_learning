%% P41: Model Ground Clutter and Swerling Targets
% Guiding question:
% Why do clutter and target amplitude fluctuate differently from white noise?
% White noise is independent and stationary in this model. Ground clutter has
% a range-dependent power envelope and correlated speckle. Swerling targets
% use explicit random power laws that may stay fixed or redraw each pulse.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P41'));

%% Visible deterministic controls and immutable resource ceilings
random_seed = 4101;
range_bin_count = 96;
pulse_count = 64;
range_start_km = 0.25;
range_spacing_km = 0.05;
noise_power = 1.0;
clutter_power_near = 25.0;
clutter_power_floor = 0.10;
clutter_decay_exponent = 2.0;
range_correlation = 0.85;
slow_time_correlation = 0.92;
maximum_correlation_lag = 12;
target_average_snr_db = -3.0;
target_trial_count = 2000;
integration_pulse_sweep = [1 2 4 8 16 32];
range_correlation_sweep = [0 0.50 0.85 0.97];
false_alarm_probability = 0.05;
broken_trial_count = 1024;
comparison_tolerance = 1e-10;
max_range_bins = 128;
max_pulses = 128;
max_trials = 4096;
max_sweep_cases = 8;
max_figure_groups = 6;
max_stored_numeric_values = 1200000;

%% Validate controls before allocating arrays
assert(~islogical(random_seed) && ~islogical(range_bin_count) && ...
    ~islogical(pulse_count) && ~islogical(range_start_km) && ...
    ~islogical(range_spacing_km) && ~islogical(noise_power) && ...
    ~islogical(clutter_power_near) && ~islogical(clutter_power_floor) && ...
    ~islogical(clutter_decay_exponent) && ...
    ~islogical(range_correlation) && ...
    ~islogical(slow_time_correlation) && ...
    ~islogical(maximum_correlation_lag) && ...
    ~islogical(target_average_snr_db) && ...
    ~islogical(target_trial_count) && ...
    ~islogical(false_alarm_probability) && ...
    ~islogical(broken_trial_count) && ...
    ~islogical(comparison_tolerance));
assert(~islogical(integration_pulse_sweep) && ...
    ~islogical(range_correlation_sweep));
all_scalar_controls = [random_seed range_bin_count pulse_count ...
    range_start_km range_spacing_km noise_power clutter_power_near ...
    clutter_power_floor clutter_decay_exponent range_correlation ...
    slow_time_correlation maximum_correlation_lag ...
    target_average_snr_db target_trial_count false_alarm_probability ...
    broken_trial_count comparison_tolerance max_range_bins max_pulses ...
    max_trials max_sweep_cases max_figure_groups ...
    max_stored_numeric_values];
assert(all(isfinite(all_scalar_controls)));
positive_controls = [range_bin_count pulse_count range_start_km ...
    range_spacing_km noise_power clutter_power_near clutter_power_floor ...
    clutter_decay_exponent maximum_correlation_lag target_trial_count ...
    false_alarm_probability broken_trial_count comparison_tolerance ...
    max_range_bins max_pulses max_trials max_sweep_cases ...
    max_figure_groups max_stored_numeric_values];
assert(all(positive_controls > 0));
integer_controls = [random_seed range_bin_count pulse_count ...
    maximum_correlation_lag target_trial_count broken_trial_count ...
    max_range_bins max_pulses max_trials max_sweep_cases ...
    max_figure_groups max_stored_numeric_values];
assert(all(integer_controls == floor(integer_controls)));
assert(random_seed == 4101);
assert(range_bin_count >= 32 && range_bin_count <= max_range_bins);
assert(pulse_count >= 32 && pulse_count <= max_pulses);
assert(maximum_correlation_lag < range_bin_count/2);
assert(target_trial_count >= 1000 && target_trial_count <= max_trials);
assert(broken_trial_count >= 512 && broken_trial_count <= max_trials);
assert(target_average_snr_db >= -20 && target_average_snr_db <= 20);
assert(range_correlation >= 0 && range_correlation < 1);
assert(slow_time_correlation >= 0 && slow_time_correlation < 1);
assert(false_alarm_probability < 0.5);
assert(numel(integration_pulse_sweep) >= 4 && ...
    numel(integration_pulse_sweep) <= max_sweep_cases && ...
    all(isfinite(integration_pulse_sweep)) && ...
    all(integration_pulse_sweep == floor(integration_pulse_sweep)) && ...
    all(integration_pulse_sweep > 0) && ...
    all(diff(integration_pulse_sweep) > 0) && ...
    max(integration_pulse_sweep) <= pulse_count);
assert(numel(range_correlation_sweep) >= 4 && ...
    numel(range_correlation_sweep) <= max_sweep_cases && ...
    all(isfinite(range_correlation_sweep)) && ...
    all(range_correlation_sweep >= 0) && ...
    all(range_correlation_sweep < 1) && ...
    all(diff(range_correlation_sweep) > 0) && ...
    any(abs(range_correlation_sweep-range_correlation) <= ...
    comparison_tolerance));
assert(max_range_bins == 128);
assert(max_pulses == 128);
assert(max_trials == 4096);
assert(max_sweep_cases == 8);
assert(max_figure_groups == 6);
assert(max_stored_numeric_values == 1200000);
assert(comparison_tolerance == 1e-10);

largest_integration_count = max(integration_pulse_sweep);
target_model_count = 5;
baseline_numeric_values = 16*range_bin_count*pulse_count;
target_phase_numeric_values = baseline_numeric_values+...
    (2*target_model_count+3)*target_trial_count*...
    largest_integration_count;
broken_phase_numeric_values = baseline_numeric_values+...
    5*broken_trial_count*range_bin_count;
estimated_stored_numeric_values = max(...
    [target_phase_numeric_values broken_phase_numeric_values]);
assert(estimated_stored_numeric_values <= max_stored_numeric_values);

%% Baseline background: range-dependent, correlated clutter versus white noise
private_stream = RandStream('mt19937ar', 'Seed', random_seed);
range_km = range_start_km+range_spacing_km*(0:range_bin_count-1);
clutter_power_profile = clutter_power_floor+clutter_power_near*...
    (range_km/range_start_km).^(-clutter_decay_exponent);

% Explicit separable AR(1) field. First correlate innovations across range,
% then preserve part of the previous pulse's field in slow time.
unit_clutter = complex(zeros(pulse_count, range_bin_count));
for pulse_index = 1:pulse_count
    white_innovation = (randn(private_stream, 1, range_bin_count)+...
        1j*randn(private_stream, 1, range_bin_count))/sqrt(2);
    spatial_innovation = complex(zeros(1, range_bin_count));
    spatial_innovation(1) = white_innovation(1);
    for range_index = 2:range_bin_count
        spatial_innovation(range_index) = ...
            range_correlation*spatial_innovation(range_index-1)+...
            sqrt(1-range_correlation^2)*white_innovation(range_index);
    end
    if pulse_index == 1
        unit_clutter(pulse_index, :) = spatial_innovation;
    else
        unit_clutter(pulse_index, :) = ...
            slow_time_correlation*unit_clutter(pulse_index-1, :)+...
            sqrt(1-slow_time_correlation^2)*spatial_innovation;
    end
end
clutter = unit_clutter.*sqrt(clutter_power_profile);
thermal_noise = sqrt(noise_power/2)*(...
    randn(private_stream, pulse_count, range_bin_count)+...
    1j*randn(private_stream, pulse_count, range_bin_count));
background = clutter+thermal_noise;
measured_clutter_power_profile = mean(abs(clutter).^2, 1);
measured_noise_power_profile = mean(abs(thermal_noise).^2, 1);

assert(clutter_power_profile(1) > 20*clutter_power_profile(end));
assert(abs(mean(abs(thermal_noise(:)).^2)-noise_power) < 0.20);

figure('Name', 'P41 baseline background structure', 'Tag', 'P41');
subplot(2, 2, 1);
imagesc(range_km, 0:pulse_count-1, ...
    10*log10(abs(background).^2/noise_power+eps));
axis xy;
colorbar;
xlabel('Range (km)');
ylabel('Pulse index');
title('Background power relative to thermal noise (dB)');
subplot(2, 2, 2);
semilogy(range_km, clutter_power_profile, '--', 'LineWidth', 1.2);
hold on;
semilogy(range_km, measured_clutter_power_profile, 'LineWidth', 1.2);
semilogy(range_km, measured_noise_power_profile, 'LineWidth', 1.2);
grid on;
xlabel('Range (km)');
ylabel('Mean power (amplitude^2)');
title('Range profile and one correlated-dwell estimate');
legend('Prescribed clutter profile', 'One-dwell measured clutter', ...
    'Measured white noise', 'Location', 'best');
subplot(2, 2, 3);
histogram(abs(thermal_noise(:))/sqrt(noise_power), 40, ...
    'Normalization', 'pdf');
hold on;
histogram(abs(clutter(:))/sqrt(mean(abs(clutter(:)).^2)), 40, ...
    'Normalization', 'pdf');
grid on;
xlabel('Amplitude / RMS amplitude');
ylabel('Probability density');
title('Aggregate clutter mixes unequal range-cell powers');
legend('White noise', 'Range-mixed clutter', 'Location', 'best');
subplot(2, 2, 4);
plot(range_km, abs(background(1, :)), 'LineWidth', 1.1);
hold on;
plot(range_km, abs(thermal_noise(1, :)), 'LineWidth', 1.1);
grid on;
xlabel('Range (km)');
ylabel('One-pulse amplitude');
title('Neighboring clutter cells move in correlated patches');
legend('Clutter + noise', 'White noise only', 'Location', 'best');

%% Explicit range and slow-time autocorrelation
correlation_lags = 0:maximum_correlation_lag;
clutter_range_correlation = zeros(size(correlation_lags));
noise_range_correlation = zeros(size(correlation_lags));
clutter_slow_time_correlation = zeros(size(correlation_lags));
noise_slow_time_correlation = zeros(size(correlation_lags));
for lag_index = 1:numel(correlation_lags)
    lag = correlation_lags(lag_index);
    clutter_left = unit_clutter(:, 1:range_bin_count-lag);
    clutter_right = unit_clutter(:, 1+lag:range_bin_count);
    noise_left = thermal_noise(:, 1:range_bin_count-lag);
    noise_right = thermal_noise(:, 1+lag:range_bin_count);
    clutter_range_correlation(lag_index) = real(...
        sum(conj(clutter_left(:)).*clutter_right(:))/...
        sqrt(sum(abs(clutter_left(:)).^2)*...
        sum(abs(clutter_right(:)).^2)));
    noise_range_correlation(lag_index) = real(...
        sum(conj(noise_left(:)).*noise_right(:))/...
        sqrt(sum(abs(noise_left(:)).^2)*sum(abs(noise_right(:)).^2)));

    clutter_early = unit_clutter(1:pulse_count-lag, :);
    clutter_late = unit_clutter(1+lag:pulse_count, :);
    noise_early = thermal_noise(1:pulse_count-lag, :);
    noise_late = thermal_noise(1+lag:pulse_count, :);
    clutter_slow_time_correlation(lag_index) = real(...
        sum(conj(clutter_early(:)).*clutter_late(:))/...
        sqrt(sum(abs(clutter_early(:)).^2)*...
        sum(abs(clutter_late(:)).^2)));
    noise_slow_time_correlation(lag_index) = real(...
        sum(conj(noise_early(:)).*noise_late(:))/...
        sqrt(sum(abs(noise_early(:)).^2)*sum(abs(noise_late(:)).^2)));
end

assert(abs(clutter_range_correlation(1)-1) <= comparison_tolerance);
assert(abs(clutter_slow_time_correlation(1)-1) <= ...
    comparison_tolerance);
assert(clutter_range_correlation(2) > noise_range_correlation(2)+0.5);
assert(clutter_slow_time_correlation(2) > ...
    noise_slow_time_correlation(2)+0.5);

figure('Name', 'P41 background correlation', 'Tag', 'P41');
subplot(2, 1, 1);
stem(correlation_lags, clutter_range_correlation, 'filled');
hold on;
plot(correlation_lags, noise_range_correlation, 'o-', ...
    'LineWidth', 1.1);
plot(correlation_lags, range_correlation.^correlation_lags, '--', ...
    'LineWidth', 1.2);
grid on;
xlabel('Range lag (bins)');
ylabel('Normalized correlation');
title('Range correlation: clutter has memory; white noise does not');
legend('Measured clutter', 'Measured white noise', 'AR(1) model', ...
    'Location', 'best');
subplot(2, 1, 2);
stem(correlation_lags, clutter_slow_time_correlation, 'filled');
hold on;
plot(correlation_lags, noise_slow_time_correlation, 'o-', ...
    'LineWidth', 1.1);
plot(correlation_lags, slow_time_correlation.^correlation_lags, '--', ...
    'LineWidth', 1.2);
grid on;
xlabel('Slow-time lag (pulses)');
ylabel('Normalized correlation');
title('Slow-time correlation: ground clutter changes gradually');
legend('Measured clutter', 'Measured white noise', 'AR(1) model', ...
    'Location', 'best');

%% Equal-average-SNR nonfluctuating and Swerling I-IV target powers
target_average_power = noise_power*10^(target_average_snr_db/10);
target_power = zeros(target_trial_count, largest_integration_count, ...
    target_model_count);
target_power(:, :, 1) = target_average_power;

% Swerling I/II: exponential power. I holds one draw for a dwell; II
% redraws each pulse. The inverse-CDF operation is P=-Pbar*log(U).
swerling_i_dwell_power = -target_average_power*log(max(...
    rand(private_stream, target_trial_count, 1), realmin));
target_power(:, :, 2) = repmat(swerling_i_dwell_power, 1, ...
    largest_integration_count);
target_power(:, :, 3) = -target_average_power*log(max(...
    rand(private_stream, target_trial_count, largest_integration_count), ...
    realmin));

% Swerling III/IV: gamma shape-two power from two exponential components.
swerling_iii_dwell_power = -(target_average_power/2)*log(max(...
    rand(private_stream, target_trial_count, 1).*...
    rand(private_stream, target_trial_count, 1), realmin));
target_power(:, :, 4) = repmat(swerling_iii_dwell_power, 1, ...
    largest_integration_count);
target_power(:, :, 5) = -(target_average_power/2)*log(max(...
    rand(private_stream, target_trial_count, largest_integration_count).*...
    rand(private_stream, target_trial_count, largest_integration_count), ...
    realmin));

target_model_names = {'Nonfluctuating', 'Swerling I', 'Swerling II', ...
    'Swerling III', 'Swerling IV'};

target_noise = sqrt(noise_power/2)*(...
    randn(private_stream, target_trial_count, largest_integration_count)+...
    1j*randn(private_stream, target_trial_count, ...
    largest_integration_count));
noise_only_trials = sqrt(noise_power/2)*(...
    randn(private_stream, target_trial_count, largest_integration_count)+...
    1j*randn(private_stream, target_trial_count, ...
    largest_integration_count));
target_phase_rad = 35*pi/180;
target_observation_power = zeros(size(target_power));
for model_index = 1:target_model_count
    target_samples = sqrt(target_power(:, :, model_index))*...
        exp(1j*target_phase_rad)+target_noise;
    target_observation_power(:, :, model_index) = abs(target_samples).^2;
end

target_average_power_by_model = squeeze(mean(mean(target_power, 1), 2));
target_finite_mean_relative_error = abs(...
    target_average_power_by_model-target_average_power)/...
    target_average_power;
assert(all(target_finite_mean_relative_error < 0.08));

baseline_integration_count = 16;
baseline_target_statistic = squeeze(mean(...
    target_observation_power(:, 1:baseline_integration_count, :), 2));
baseline_clean_dwell_power = squeeze(mean(...
    target_power(:, 1:baseline_integration_count, :), 2));
baseline_clean_power_cv = std(baseline_clean_dwell_power, 0, 1)./...
    mean(baseline_clean_dwell_power, 1);
baseline_noise_statistic = mean(...
    abs(noise_only_trials(:, 1:baseline_integration_count)).^2, 2);
sorted_noise_statistic = sort(baseline_noise_statistic);
threshold_index = ceil((1-false_alarm_probability)*target_trial_count);
baseline_detection_threshold = sorted_noise_statistic(threshold_index);
baseline_detection_rate = mean(...
    baseline_target_statistic > baseline_detection_threshold, 1);

assert(baseline_clean_power_cv(1) <= comparison_tolerance);
assert(baseline_clean_power_cv(2) > baseline_clean_power_cv(3));
assert(baseline_clean_power_cv(4) > baseline_clean_power_cv(5));

figure('Name', 'P41 target fluctuation baseline', 'Tag', 'P41');
subplot(2, 2, 1);
plot(0:largest_integration_count-1, ...
    squeeze(target_power(1, :, :))/target_average_power, ...
    'LineWidth', 1.1);
grid on;
xlabel('Pulse index');
ylabel('Target power / average power');
title('One dwell: slow versus fast fluctuation');
legend(target_model_names, 'Location', 'best');
subplot(2, 2, 2);
histogram(baseline_clean_dwell_power(:, 1)/target_average_power, 40, ...
    'Normalization', 'probability');
hold on;
histogram(baseline_clean_dwell_power(:, 2)/target_average_power, 40, ...
    'Normalization', 'probability');
histogram(baseline_clean_dwell_power(:, 3)/target_average_power, 40, ...
    'Normalization', 'probability');
grid on;
xlabel('Dwell-average target power / ensemble mean');
ylabel('Probability per bin');
title('Fast Swerling II fluctuation averages within a dwell');
legend('Nonfluctuating', 'Swerling I', 'Swerling II', ...
    'Location', 'best');
subplot(2, 2, 3);
bar(baseline_clean_power_cv);
grid on;
set(gca, 'XTick', 1:target_model_count, ...
    'XTickLabel', {'Steady', 'I', 'II', 'III', 'IV'});
ylabel('Dwell-power coefficient of variation');
title(sprintf('Variability after %d-pulse averaging', ...
    baseline_integration_count));
subplot(2, 2, 4);
bar(100*baseline_detection_rate);
grid on;
ylim([0 105]);
set(gca, 'XTick', 1:target_model_count, ...
    'XTickLabel', {'Steady', 'I', 'II', 'III', 'IV'});
ylabel('Target-present threshold crossings (%)');
title(sprintf('Equal average SNR = %.1f dB; unequal stability', ...
    target_average_snr_db));

%% Sweep 1: vary only prescribed range correlation
measured_range_correlation_sweep = zeros(size(range_correlation_sweep));
correlation_white_rows = (randn(private_stream, pulse_count, ...
    range_bin_count)+1j*randn(private_stream, pulse_count, ...
    range_bin_count))/sqrt(2);
for case_index = 1:numel(range_correlation_sweep)
    prescribed_correlation = range_correlation_sweep(case_index);
    correlation_rows = complex(zeros(pulse_count, range_bin_count));
    for pulse_index = 1:pulse_count
        row_white = correlation_white_rows(pulse_index, :);
        correlation_rows(pulse_index, 1) = row_white(1);
        for range_index = 2:range_bin_count
            correlation_rows(pulse_index, range_index) = ...
                prescribed_correlation*...
                correlation_rows(pulse_index, range_index-1)+...
                sqrt(1-prescribed_correlation^2)*row_white(range_index);
        end
    end
    left_cells = correlation_rows(:, 1:end-1);
    right_cells = correlation_rows(:, 2:end);
    measured_range_correlation_sweep(case_index) = real(...
        sum(conj(left_cells(:)).*right_cells(:))/...
        sqrt(sum(abs(left_cells(:)).^2)*sum(abs(right_cells(:)).^2)));
end
assert(all(diff(measured_range_correlation_sweep) > 0));
assert(abs(measured_range_correlation_sweep(1)) < 0.05);
assert(all(abs(measured_range_correlation_sweep-...
    range_correlation_sweep) < 0.06));

figure('Name', 'P41 range-correlation sweep', 'Tag', 'P41');
plot(range_correlation_sweep, range_correlation_sweep, '--', ...
    'LineWidth', 1.2);
hold on;
plot(range_correlation_sweep, measured_range_correlation_sweep, ...
    'o-', 'LineWidth', 1.3);
grid on;
axis([0 1 0 1]);
xlabel('Prescribed adjacent-bin correlation');
ylabel('Measured adjacent-bin correlation');
title('Sweep 1: range patches lengthen as AR memory increases');
legend('Ideal ensemble value', 'Seeded finite-field measurement', ...
    'Location', 'best');

%% Sweep 2: vary only noncoherent integration length
target_detection_rate_sweep = zeros(numel(integration_pulse_sweep), ...
    target_model_count);
clean_dwell_power_cv_sweep = zeros(size(target_detection_rate_sweep));
detection_threshold_sweep = zeros(size(integration_pulse_sweep));
for case_index = 1:numel(integration_pulse_sweep)
    integration_count = integration_pulse_sweep(case_index);
    noise_statistic = mean(...
        abs(noise_only_trials(:, 1:integration_count)).^2, 2);
    sorted_noise_statistic = sort(noise_statistic);
    detection_threshold_sweep(case_index) = ...
        sorted_noise_statistic(threshold_index);
    for model_index = 1:target_model_count
        observed_statistic = mean(target_observation_power(...
            :, 1:integration_count, model_index), 2);
        clean_statistic = mean(target_power(...
            :, 1:integration_count, model_index), 2);
        target_detection_rate_sweep(case_index, model_index) = ...
            mean(observed_statistic > ...
            detection_threshold_sweep(case_index));
        clean_dwell_power_cv_sweep(case_index, model_index) = ...
            std(clean_statistic)/mean(clean_statistic);
    end
end

assert(all(clean_dwell_power_cv_sweep(:, 1) <= comparison_tolerance));
assert(clean_dwell_power_cv_sweep(end, 3) < ...
    clean_dwell_power_cv_sweep(1, 3)/4);
assert(clean_dwell_power_cv_sweep(end, 2) > ...
    0.8*clean_dwell_power_cv_sweep(1, 2));

figure('Name', 'P41 integration-length sweep', 'Tag', 'P41');
subplot(2, 1, 1);
semilogx(integration_pulse_sweep, ...
    100*target_detection_rate_sweep, 'o-', 'LineWidth', 1.2);
grid on;
xlabel('Noncoherently averaged pulse count');
ylabel('Target-present threshold crossings (%)');
title('Sweep 2: equal average SNR does not give equal stability');
legend(target_model_names, 'Location', 'best');
subplot(2, 1, 2);
loglog(integration_pulse_sweep, clean_dwell_power_cv_sweep(:, 2:5), ...
    'o-', 'LineWidth', 1.2);
grid on;
xlabel('Noncoherently averaged pulse count');
ylabel('Clean dwell-power coefficient of variation');
title('Fast models average down; slow models retain dwell-to-dwell fades');
legend('Swerling I', 'Swerling II', 'Swerling III', 'Swerling IV', ...
    'Location', 'best');

%% Intentionally broken case: force one white-background threshold on clutter
% The retained summary metrics above no longer need the large Monte Carlo
% banks. Clear them before allocating the independent broken-case bank so the
% peak live numeric-value estimate remains valid and bounded.
clear target_power target_observation_power target_noise noise_only_trials;
clear target_samples noise_statistic sorted_noise_statistic clean_statistic;
clear observed_statistic correlation_rows correlation_white_rows;

broken_unit_clutter = complex(zeros(broken_trial_count, range_bin_count));
for trial_index = 1:broken_trial_count
    row_white = (randn(private_stream, 1, range_bin_count)+...
        1j*randn(private_stream, 1, range_bin_count))/sqrt(2);
    broken_unit_clutter(trial_index, 1) = row_white(1);
    for range_index = 2:range_bin_count
        broken_unit_clutter(trial_index, range_index) = ...
            range_correlation*...
            broken_unit_clutter(trial_index, range_index-1)+...
            sqrt(1-range_correlation^2)*row_white(range_index);
    end
end
broken_clutter = broken_unit_clutter.*sqrt(clutter_power_profile);
broken_noise = sqrt(noise_power/2)*(...
    randn(private_stream, broken_trial_count, range_bin_count)+...
    1j*randn(private_stream, broken_trial_count, range_bin_count));
broken_background_power = abs(broken_clutter+broken_noise).^2;
local_background_power = clutter_power_profile+noise_power;

% Broken: pretend every range cell has the same white-background mean power.
global_background_power = mean(local_background_power);
broken_global_threshold = -global_background_power*...
    log(false_alarm_probability);
broken_false_alarm_by_range = mean(...
    broken_background_power > broken_global_threshold, 1);

% Recovery: normalize by each cell's local expected background power first.
recovered_normalized_power = broken_background_power./...
    local_background_power;
recovered_normalized_threshold = -log(false_alarm_probability);
recovered_false_alarm_by_range = mean(...
    recovered_normalized_power > recovered_normalized_threshold, 1);
broken_model_valid = false;
recovered_model_valid = true;

near_range_cells = 1:16;
far_range_cells = range_bin_count-15:range_bin_count;
broken_near_false_alarm_rate = mean(...
    broken_false_alarm_by_range(near_range_cells));
broken_far_false_alarm_rate = mean(...
    broken_false_alarm_by_range(far_range_cells));
recovered_near_false_alarm_rate = mean(...
    recovered_false_alarm_by_range(near_range_cells));
recovered_far_false_alarm_rate = mean(...
    recovered_false_alarm_by_range(far_range_cells));

assert(broken_near_false_alarm_rate > ...
    5*max(broken_far_false_alarm_rate, 1/broken_trial_count));
assert(abs(recovered_near_false_alarm_rate-...
    false_alarm_probability) < 0.02);
assert(abs(recovered_far_false_alarm_rate-...
    false_alarm_probability) < 0.02);
assert(~broken_model_valid && recovered_model_valid);

figure('Name', 'P41 broken background model and recovery', 'Tag', 'P41');
subplot(2, 1, 1);
semilogy(range_km, local_background_power, 'LineWidth', 1.3);
hold on;
semilogy(range_km, global_background_power*...
    ones(size(range_km)), '--', 'LineWidth', 1.2);
grid on;
xlabel('Range (km)');
ylabel('Expected background power (amplitude^2)');
title('Broken assumption: one global mean erases the clutter profile');
legend('Actual local mean', 'Broken global mean', 'Location', 'best');
subplot(2, 1, 2);
plot(range_km, 100*broken_false_alarm_by_range, 'LineWidth', 1.2);
hold on;
plot(range_km, 100*recovered_false_alarm_by_range, 'LineWidth', 1.2);
plot(range_km, 100*false_alarm_probability*ones(size(range_km)), ...
    '--', 'LineWidth', 1.1);
grid on;
xlabel('Range (km)');
ylabel('Background threshold crossings (%)');
title('Local normalization restores a range-uniform reference rate');
legend('Broken global threshold', 'Recovered local normalization', ...
    'Requested reference rate', 'Location', 'best');

%% Retained console and workspace metrics
fprintf('\nP41 retained deterministic metrics\n');
fprintf('Private random seed: %d\n', random_seed);
fprintf('Range bins / baseline pulses: %d / %d\n', ...
    range_bin_count, pulse_count);
fprintf('Clutter near/far mean power: %.6f / %.6f amplitude^2\n', ...
    clutter_power_profile(1), clutter_power_profile(end));
fprintf('Measured adjacent-bin clutter/noise correlation: %.6f / %.6f\n', ...
    clutter_range_correlation(2), noise_range_correlation(2));
fprintf('Equal target average SNR: %.3f dB\n', target_average_snr_db);
fprintf('16-pulse clean-power CV, steady/I/II/III/IV: ');
fprintf('%.4f %.4f %.4f %.4f %.4f\n', baseline_clean_power_cv);
fprintf('16-pulse threshold crossings, steady/I/II/III/IV (%%): ');
fprintf('%.2f %.2f %.2f %.2f %.2f\n', 100*baseline_detection_rate);
fprintf('Broken near/far background crossings (%%): %.2f / %.2f\n', ...
    100*broken_near_false_alarm_rate, 100*broken_far_false_alarm_rate);
fprintf('Recovered near/far background crossings (%%): %.2f / %.2f\n', ...
    100*recovered_near_false_alarm_rate, ...
    100*recovered_far_false_alarm_rate);
fprintf(['Interpretation: correlation, range dependence, and target ' ...
    'fluctuation survive an equal-average-power description.\n']);

results = struct();
results.random_seed = random_seed;
results.range_km = range_km;
results.clutter_power_profile = clutter_power_profile;
results.measured_clutter_power_profile = measured_clutter_power_profile;
results.correlation_lags = correlation_lags;
results.clutter_range_correlation = clutter_range_correlation;
results.noise_range_correlation = noise_range_correlation;
results.clutter_slow_time_correlation = clutter_slow_time_correlation;
results.noise_slow_time_correlation = noise_slow_time_correlation;
results.target_model_names = target_model_names;
results.target_average_power_by_model = target_average_power_by_model;
results.target_finite_mean_relative_error = ...
    target_finite_mean_relative_error;
results.baseline_clean_power_cv = baseline_clean_power_cv;
results.baseline_detection_threshold = baseline_detection_threshold;
results.baseline_detection_rate = baseline_detection_rate;
results.range_correlation_sweep = range_correlation_sweep;
results.measured_range_correlation_sweep = ...
    measured_range_correlation_sweep;
results.integration_pulse_sweep = integration_pulse_sweep;
results.target_detection_rate_sweep = target_detection_rate_sweep;
results.clean_dwell_power_cv_sweep = clean_dwell_power_cv_sweep;
results.broken_false_alarm_by_range = broken_false_alarm_by_range;
results.recovered_false_alarm_by_range = recovered_false_alarm_by_range;
results.broken_near_false_alarm_rate = broken_near_false_alarm_rate;
results.broken_far_false_alarm_rate = broken_far_false_alarm_rate;
results.recovered_near_false_alarm_rate = recovered_near_false_alarm_rate;
results.recovered_far_false_alarm_rate = recovered_far_false_alarm_rate;
results.broken_model_valid = broken_model_valid;
results.recovered_model_valid = recovered_model_valid;
results.estimated_stored_numeric_values = ...
    estimated_stored_numeric_values;
