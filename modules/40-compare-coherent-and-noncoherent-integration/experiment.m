%% P40: Compare Coherent and Noncoherent Integration
% Guiding question:
% When should pulse phases be added and when should magnitudes be added?
% Coherent processing aligns a trustworthy phase history before adding
% complex samples. Noncoherent processing adds power evidence and discards
% phase. The two output statistics therefore need different normalizations.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P40'));

%% Visible deterministic controls and immutable resource ceilings
random_seed = 4001;
pulse_count = 32;
target_amplitude = 1.0;
input_snr_db = -8.0;
target_initial_phase_deg = 25;
nominal_phase_increment_deg = 35;
pulse_count_sweep = [1 2 4 8 16 32 64];
phase_jitter_std_sweep_deg = [0 5 15 30 60 90 120 180];
broken_phase_jitter_cycle_deg = [0 90 180 -90];
comparison_tolerance = 1e-10;
max_pulse_count = 128;
max_sweep_cases = 12;
max_figure_groups = 4;
max_stored_numeric_values = 50000;

%% Validate controls before allocating arrays
assert(~islogical(random_seed) && ~islogical(pulse_count) && ...
    ~islogical(target_amplitude) && ~islogical(input_snr_db) && ...
    ~islogical(target_initial_phase_deg) && ...
    ~islogical(nominal_phase_increment_deg));
assert(~islogical(pulse_count_sweep) && ...
    ~islogical(phase_jitter_std_sweep_deg) && ...
    ~islogical(broken_phase_jitter_cycle_deg));
positive_controls = [pulse_count target_amplitude comparison_tolerance ...
    max_pulse_count max_sweep_cases max_figure_groups ...
    max_stored_numeric_values];
assert(all(isfinite(positive_controls)) && all(positive_controls > 0));
assert(isfinite(random_seed) && random_seed == floor(random_seed) && ...
    random_seed == 4001);
assert(isfinite(input_snr_db) && input_snr_db >= -40 && ...
    input_snr_db <= 20);
assert(isfinite(target_initial_phase_deg));
assert(isfinite(nominal_phase_increment_deg));
integer_controls = [pulse_count max_pulse_count max_sweep_cases ...
    max_figure_groups max_stored_numeric_values];
assert(all(integer_controls == floor(integer_controls)));
assert(max_pulse_count == 128);
assert(max_sweep_cases == 12);
assert(max_figure_groups == 4);
assert(max_stored_numeric_values == 50000);
assert(comparison_tolerance == 1e-10);
assert(pulse_count >= 4 && pulse_count <= max_pulse_count && ...
    mod(pulse_count, numel(broken_phase_jitter_cycle_deg)) == 0);
assert(numel(pulse_count_sweep) >= 4 && ...
    numel(pulse_count_sweep) <= max_sweep_cases && ...
    all(isfinite(pulse_count_sweep)) && ...
    all(pulse_count_sweep == floor(pulse_count_sweep)) && ...
    all(pulse_count_sweep > 0) && ...
    all(diff(pulse_count_sweep) > 0) && ...
    max(pulse_count_sweep) <= max_pulse_count && ...
    any(pulse_count_sweep == pulse_count));
assert(numel(phase_jitter_std_sweep_deg) >= 4 && ...
    numel(phase_jitter_std_sweep_deg) <= max_sweep_cases && ...
    all(isfinite(phase_jitter_std_sweep_deg)) && ...
    all(phase_jitter_std_sweep_deg >= 0) && ...
    all(diff(phase_jitter_std_sweep_deg) > 0) && ...
    phase_jitter_std_sweep_deg(1) == 0 && ...
    phase_jitter_std_sweep_deg(end) <= 180);
assert(numel(broken_phase_jitter_cycle_deg) == 4 && ...
    all(isfinite(broken_phase_jitter_cycle_deg)) && ...
    isequal(broken_phase_jitter_cycle_deg, [0 90 180 -90]));
assert(max_figure_groups >= 4);

estimated_stored_numeric_values = 120*pulse_count+...
    50*numel(pulse_count_sweep)+...
    50*numel(phase_jitter_std_sweep_deg);
assert(estimated_stored_numeric_values <= max_stored_numeric_values);

%% Physical model and one deterministic weak-target dwell
input_snr_linear = 10^(input_snr_db/10);
noise_power = target_amplitude^2/input_snr_linear;
noise_rms = sqrt(noise_power);
pulse_index = 0:pulse_count-1;
integrated_pulse_count = 1:pulse_count;
nominal_phase_rad = (target_initial_phase_deg+...
    nominal_phase_increment_deg*pulse_index)*pi/180;
phase_reference = exp(1j*nominal_phase_rad);
clean_samples = target_amplitude*phase_reference;

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
complex_noise = noise_rms/sqrt(2)*(...
    randn(private_stream, 1, pulse_count)+...
    1j*randn(private_stream, 1, pulse_count));
observed_samples = clean_samples+complex_noise;

% Essential coherent operation: preserve complex values and align phase first.
phase_aligned_samples = observed_samples.*conj(phase_reference);
coherent_sum = sum(phase_aligned_samples);
coherent_power_statistic = abs(coherent_sum)^2;

% Essential noncoherent operation: add nonnegative power evidence.
% This is not an unbiased estimate of coherent output SNR.
noncoherent_power_statistic = sum(abs(observed_samples).^2);
coherent_cumulative_sum = cumsum(phase_aligned_samples);
noncoherent_cumulative_power = cumsum(abs(observed_samples).^2);
noise_only_mean_power = integrated_pulse_count*noise_power;
target_present_mean_power = integrated_pulse_count*...
    (noise_power+target_amplitude^2);

baseline_coherent_output_snr_linear = ...
    pulse_count*input_snr_linear;
baseline_coherent_output_snr_db = ...
    10*log10(baseline_coherent_output_snr_linear);
baseline_coherent_detectability = pulse_count*input_snr_linear;
baseline_noncoherent_detectability = ...
    sqrt(pulse_count)*input_snr_linear;

assert(abs(sum(clean_samples.*conj(phase_reference))-...
    pulse_count*target_amplitude) <= comparison_tolerance);
assert(baseline_coherent_detectability > ...
    baseline_noncoherent_detectability);

figure('Name', 'P40 baseline pulse integration', 'Tag', 'P40');
subplot(2, 2, 1);
plot(pulse_index, real(observed_samples), 'o-', 'LineWidth', 1.0);
hold on;
plot(pulse_index, imag(observed_samples), 's-', 'LineWidth', 1.0);
grid on;
xlabel('Pulse index');
ylabel('Complex return amplitude');
title(sprintf('Raw weak returns: input SNR = %.1f dB', input_snr_db));
legend('I', 'Q', 'Location', 'best');
subplot(2, 2, 2);
plot(pulse_index, real(phase_aligned_samples), 'o-', 'LineWidth', 1.0);
hold on;
plot(pulse_index, imag(phase_aligned_samples), 's-', 'LineWidth', 1.0);
grid on;
xlabel('Pulse index');
ylabel('Phase-aligned amplitude');
title('Known phase history rotates the target toward +I');
legend('Aligned I', 'Aligned Q', 'Location', 'best');
subplot(2, 2, 3);
plot(integrated_pulse_count, abs(coherent_cumulative_sum), ...
    'LineWidth', 1.3);
hold on;
plot(integrated_pulse_count, integrated_pulse_count*target_amplitude, '--', ...
    'LineWidth', 1.1);
grid on;
xlabel('Integrated pulse count');
ylabel('|cumulative complex sum| (amplitude)');
title('Coherent addition: target amplitudes share a direction');
legend('Observed', 'Noise-free target', 'Location', 'best');
subplot(2, 2, 4);
plot(integrated_pulse_count, noncoherent_cumulative_power, ...
    'LineWidth', 1.3);
hold on;
plot(integrated_pulse_count, noise_only_mean_power, '--', ...
    'LineWidth', 1.1);
plot(integrated_pulse_count, target_present_mean_power, ':', ...
    'LineWidth', 1.3);
grid on;
xlabel('Integrated pulse count');
ylabel('Cumulative power (amplitude^2)');
title('Noncoherent addition: target and noise powers both accumulate');
legend('Observed power', 'Noise-only mean', 'Target-present mean', ...
    'Location', 'best');

%% Sweep 1: vary only pulse count under stable phase
coherent_output_snr_sweep_linear = ...
    input_snr_linear*pulse_count_sweep;
coherent_output_snr_sweep_db = ...
    10*log10(coherent_output_snr_sweep_linear);
coherent_detectability_sweep = ...
    input_snr_linear*pulse_count_sweep;
noncoherent_detectability_sweep = ...
    input_snr_linear*sqrt(pulse_count_sweep);

assert(abs(coherent_output_snr_sweep_db(1)-input_snr_db) <= ...
    comparison_tolerance);
assert(all(coherent_detectability_sweep(2:end) > ...
    noncoherent_detectability_sweep(2:end)));
assert(all(diff(coherent_output_snr_sweep_db) > 0));

figure('Name', 'P40 pulse-count sweep', 'Tag', 'P40');
subplot(2, 1, 1);
semilogx(pulse_count_sweep, coherent_output_snr_sweep_db, ...
    'o-', 'LineWidth', 1.3);
hold on;
semilogx(pulse_count_sweep, input_snr_db*...
    ones(size(pulse_count_sweep)), '--', 'LineWidth', 1.1);
grid on;
xlabel('Integrated pulse count');
ylabel('Coherent output SNR (dB)');
title('Stable phase gives 10 log_{10}(N) coherent SNR gain');
legend('Phase-aligned complex sum', 'Single-pulse SNR', ...
    'Location', 'best');
subplot(2, 1, 2);
loglog(pulse_count_sweep, coherent_detectability_sweep, ...
    'o-', 'LineWidth', 1.3);
hold on;
loglog(pulse_count_sweep, noncoherent_detectability_sweep, ...
    's-', 'LineWidth', 1.3);
grid on;
xlabel('Integrated pulse count');
ylabel('Detectability index d (standard deviations)');
title('Fair statistic comparison: coherent d grows N, power d grows sqrt(N)');
legend('Coherent power statistic', 'Noncoherent power statistic', ...
    'Location', 'best');

%% Sweep 2: vary only independent Gaussian phase-jitter standard deviation
phase_jitter_std_sweep_rad = phase_jitter_std_sweep_deg*pi/180;
phase_coherence_factor = exp(-(phase_jitter_std_sweep_rad).^2);
coherent_effective_gain = 1+(pulse_count-1)*phase_coherence_factor;
coherent_jitter_output_snr_linear = ...
    input_snr_linear*coherent_effective_gain;
coherent_jitter_output_snr_db = ...
    10*log10(coherent_jitter_output_snr_linear);
coherent_signal_power_fraction = coherent_effective_gain/pulse_count;
noncoherent_signal_energy_fraction = ...
    ones(size(phase_jitter_std_sweep_deg));

assert(abs(coherent_effective_gain(1)-pulse_count) <= ...
    comparison_tolerance);
assert(all(diff(coherent_effective_gain) < 0));
assert(coherent_effective_gain(end) < 1.01);
assert(all(noncoherent_signal_energy_fraction == 1));

figure('Name', 'P40 phase-jitter sweep', 'Tag', 'P40');
subplot(2, 1, 1);
plot(phase_jitter_std_sweep_deg, coherent_jitter_output_snr_db, ...
    'o-', 'LineWidth', 1.3);
hold on;
plot(phase_jitter_std_sweep_deg, input_snr_db*...
    ones(size(phase_jitter_std_sweep_deg)), '--', 'LineWidth', 1.1);
grid on;
xlabel('Phase-jitter standard deviation (deg)');
ylabel('Expected coherent output SNR (dB)');
title('Unknown pulse phase erases coherent gain');
legend('Coherent output', 'Single-pulse limit', 'Location', 'best');
subplot(2, 1, 2);
plot(phase_jitter_std_sweep_deg, coherent_signal_power_fraction, ...
    'o-', 'LineWidth', 1.3);
hold on;
plot(phase_jitter_std_sweep_deg, ...
    noncoherent_signal_energy_fraction, 's-', 'LineWidth', 1.3);
grid on;
xlabel('Phase-jitter standard deviation (deg)');
ylabel('Retained signal evidence (normalized)');
title('Power addition is phase-insensitive but less statistically efficient');
legend('Coherent sum power / ideal', 'Noncoherent signal energy / ideal', ...
    'Location', 'best');

%% Intentionally broken case: untracked phase jitter, then exact recovery
broken_phase_jitter_pattern_deg = repmat(...
    broken_phase_jitter_cycle_deg, 1, ...
    pulse_count/numel(broken_phase_jitter_cycle_deg));
broken_phase_jitter_pattern_rad = ...
    broken_phase_jitter_pattern_deg*pi/180;
broken_clean_samples = target_amplitude*phase_reference.*...
    exp(1j*broken_phase_jitter_pattern_rad);

% Broken: remove only nominal phase and pretend the residual jitter is zero.
broken_nominally_aligned_samples = ...
    broken_clean_samples.*conj(phase_reference);
broken_coherent_sum = sum(broken_nominally_aligned_samples);

% Recovery: a valid pulse-by-pulse phase estimate removes the actual error.
recovered_phase_aligned_samples = ...
    broken_clean_samples.*conj(phase_reference).*...
    exp(-1j*broken_phase_jitter_pattern_rad);
recovered_coherent_sum = sum(recovered_phase_aligned_samples);
broken_coherent_signal_power_fraction = ...
    abs(broken_coherent_sum)^2/(pulse_count*target_amplitude)^2;
recovered_coherent_signal_power_fraction = ...
    abs(recovered_coherent_sum)^2/(pulse_count*target_amplitude)^2;
broken_noncoherent_signal_energy_fraction = ...
    sum(abs(broken_clean_samples).^2)/...
    (pulse_count*target_amplitude^2);
broken_model_valid = false;
recovered_model_valid = true;

assert(broken_coherent_signal_power_fraction <= comparison_tolerance);
assert(abs(recovered_coherent_signal_power_fraction-1) <= ...
    comparison_tolerance);
assert(abs(broken_noncoherent_signal_energy_fraction-1) <= ...
    comparison_tolerance);
assert(~broken_model_valid && recovered_model_valid);

figure('Name', 'P40 broken phase model and recovery', 'Tag', 'P40');
subplot(2, 1, 1);
plot(integrated_pulse_count, ...
    abs(cumsum(broken_nominally_aligned_samples)), ...
    'LineWidth', 1.3);
hold on;
plot(integrated_pulse_count, ...
    abs(cumsum(recovered_phase_aligned_samples)), ...
    'LineWidth', 1.3);
grid on;
xlabel('Integrated pulse count');
ylabel('|cumulative complex sum| (amplitude)');
title('Broken quadrature phase cycle cancels; tracked phase recovers');
legend('Broken: nominal reference only', ...
    'Recovered: pulse phase tracked', 'Location', 'best');
subplot(2, 1, 2);
bar([broken_coherent_signal_power_fraction ...
    recovered_coherent_signal_power_fraction ...
    broken_noncoherent_signal_energy_fraction]);
grid on;
set(gca, 'XTick', 1:3, 'XTickLabel', ...
    {'Broken coherent', 'Recovered coherent', 'Noncoherent energy'});
ylabel('Retained signal evidence (normalized)');
title('Phase tracking changes coherent evidence, not accumulated energy');

%% Retained console and workspace metrics
fprintf('\nP40 retained deterministic metrics\n');
fprintf('Private random seed: %d\n', random_seed);
fprintf('Pulse count: %d\n', pulse_count);
fprintf('Single-pulse input SNR: %.3f dB\n', input_snr_db);
fprintf('Stable-phase coherent output SNR: %.3f dB\n', ...
    baseline_coherent_output_snr_db);
fprintf('Coherent / noncoherent detectability d: %.6f / %.6f\n', ...
    baseline_coherent_detectability, ...
    baseline_noncoherent_detectability);
fprintf('Observed coherent power statistic: %.6f amplitude^2\n', ...
    coherent_power_statistic);
fprintf('Observed noncoherent power statistic: %.6f amplitude^2\n', ...
    noncoherent_power_statistic);
fprintf('Broken / recovered coherent evidence: %.6f / %.6f\n', ...
    broken_coherent_signal_power_fraction, ...
    recovered_coherent_signal_power_fraction);
fprintf(['Interpretation: add complex samples only after establishing a ' ...
    'valid phase reference; otherwise add phase-insensitive evidence.\n']);

results = struct();
results.random_seed = random_seed;
results.pulse_count = pulse_count;
results.input_snr_db = input_snr_db;
results.noise_power = noise_power;
results.phase_reference = phase_reference;
results.clean_samples = clean_samples;
results.observed_samples = observed_samples;
results.coherent_sum = coherent_sum;
results.coherent_power_statistic = coherent_power_statistic;
results.noncoherent_power_statistic = noncoherent_power_statistic;
results.pulse_count_sweep = pulse_count_sweep;
results.coherent_output_snr_sweep_db = coherent_output_snr_sweep_db;
results.coherent_detectability_sweep = coherent_detectability_sweep;
results.noncoherent_detectability_sweep = ...
    noncoherent_detectability_sweep;
results.phase_jitter_std_sweep_deg = phase_jitter_std_sweep_deg;
results.coherent_jitter_output_snr_db = ...
    coherent_jitter_output_snr_db;
results.coherent_signal_power_fraction = ...
    coherent_signal_power_fraction;
results.noncoherent_signal_energy_fraction = ...
    noncoherent_signal_energy_fraction;
results.broken_phase_jitter_pattern_deg = ...
    broken_phase_jitter_pattern_deg;
results.broken_coherent_signal_power_fraction = ...
    broken_coherent_signal_power_fraction;
results.recovered_coherent_signal_power_fraction = ...
    recovered_coherent_signal_power_fraction;
results.broken_noncoherent_signal_energy_fraction = ...
    broken_noncoherent_signal_energy_fraction;
results.broken_model_valid = broken_model_valid;
results.recovered_model_valid = recovered_model_valid;
results.estimated_stored_numeric_values = ...
    estimated_stored_numeric_values;
