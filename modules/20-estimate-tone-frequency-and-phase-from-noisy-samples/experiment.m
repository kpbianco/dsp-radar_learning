%% P20: Estimate Tone Frequency and Phase from Noisy Samples
% Guiding question: How accurately can frequency and phase be estimated from a finite noisy record?
% Base MATLAB only. The FFT interpolation, phase increment, coherent phase
% projection, circular errors, and confidence gate are explicit below.

%% Visible controls and fixed resource ceilings
random_seed = 1020;
fs_hz = 1024;
record_sample_count = 256;
tone_frequency_hz = 123.25;
tone_amplitude_v = 1;
tone_phase_rad = 2.70;
baseline_snr_db = 8;
snr_sweep_db = [-10 0 10 20];
record_length_sweep = [64 128 256 512];
trial_count = 40;
coherence_threshold = 0.20;
low_amplitude_v = 0.02;

max_record_samples = 512;
max_fft_length = 512;
max_sweep_cases = 4;
max_trials = 40;
max_stored_numeric_values = 100000;
max_figure_groups = 6;

%% Validate controls before random, signal, FFT, cleanup, or figure work
scalar_controls = [random_seed fs_hz record_sample_count ...
    tone_frequency_hz tone_amplitude_v tone_phase_rad baseline_snr_db ...
    trial_count coherence_threshold low_amplitude_v max_record_samples ...
    max_fft_length max_sweep_cases max_trials ...
    max_stored_numeric_values max_figure_groups];
assert(isnumeric(scalar_controls) && isreal(scalar_controls) && ...
    all(isfinite(scalar_controls)), ...
    'P20 scalar controls must be finite real numeric values.');
assert(~islogical(random_seed) && ~islogical(fs_hz) && ...
    ~islogical(record_sample_count) && ~islogical(tone_frequency_hz) && ...
    ~islogical(tone_amplitude_v) && ~islogical(tone_phase_rad) && ...
    ~islogical(baseline_snr_db) && ~islogical(trial_count) && ...
    ~islogical(coherence_threshold) && ~islogical(low_amplitude_v) && ...
    ~islogical(max_record_samples) && ~islogical(max_fft_length) && ...
    ~islogical(max_sweep_cases) && ~islogical(max_trials) && ...
    ~islogical(max_stored_numeric_values) && ...
    ~islogical(max_figure_groups), ...
    'P20 controls must not be logical values.');
assert(isscalar(random_seed) && isscalar(fs_hz) && ...
    isscalar(record_sample_count) && isscalar(tone_frequency_hz) && ...
    isscalar(tone_amplitude_v) && isscalar(tone_phase_rad) && ...
    isscalar(baseline_snr_db) && isscalar(trial_count) && ...
    isscalar(coherence_threshold) && isscalar(low_amplitude_v) && ...
    isscalar(max_record_samples) && isscalar(max_fft_length) && ...
    isscalar(max_sweep_cases) && isscalar(max_trials) && ...
    isscalar(max_stored_numeric_values) && isscalar(max_figure_groups), ...
    'P20 scalar controls must each contain exactly one value.');
assert(random_seed == 1020 && random_seed == floor(random_seed) && ...
    random_seed >= 0 && random_seed <= 2^32-1, ...
    'random_seed must be the canonical unsigned 32-bit seed 1020.');
assert(fs_hz == 1024 && record_sample_count == 256 && ...
    record_sample_count == floor(record_sample_count) && ...
    mod(record_sample_count, 2) == 0, ...
    'The canonical baseline is 256 samples at 1024 samples/s.');
assert(tone_frequency_hz == 123.25 && tone_frequency_hz > 0 && ...
    tone_frequency_hz < fs_hz/2 && ...
    tone_frequency_hz*record_sample_count/fs_hz ~= ...
    floor(tone_frequency_hz*record_sample_count/fs_hz), ...
    'The tone must remain the canonical positive fractional-bin tone.');
assert(tone_amplitude_v == 1 && tone_phase_rad == 2.70 && ...
    tone_phase_rad >= -pi && tone_phase_rad <= pi, ...
    'P20 requires the canonical amplitude and wrapped initial phase.');
assert(baseline_snr_db == 8 && baseline_snr_db >= -20 && ...
    baseline_snr_db <= 60, ...
    'The baseline SNR must be the canonical bounded 8 dB.');
assert(isnumeric(snr_sweep_db) && isvector(snr_sweep_db) && ...
    isreal(snr_sweep_db) && ~islogical(snr_sweep_db) && ...
    all(isfinite(snr_sweep_db)) && ...
    isequal(snr_sweep_db, [-10 0 10 20]), ...
    'snr_sweep_db must be exactly [-10 0 10 20].');
assert(isnumeric(record_length_sweep) && isvector(record_length_sweep) && ...
    isreal(record_length_sweep) && ~islogical(record_length_sweep) && ...
    all(isfinite(record_length_sweep)) && ...
    isequal(record_length_sweep, [64 128 256 512]) && ...
    all(record_length_sweep == floor(record_length_sweep)), ...
    'record_length_sweep must be exactly [64 128 256 512].');
assert(trial_count == 40 && trial_count == floor(trial_count) && ...
    coherence_threshold == 0.20 && coherence_threshold > 0 && ...
    coherence_threshold < 1 && low_amplitude_v == 0.02 && ...
    low_amplitude_v > 0 && low_amplitude_v < tone_amplitude_v, ...
    'P20 trial, coherence, and low-amplitude controls must remain canonical.');
assert(max_record_samples == 512 && max_fft_length == 512 && ...
    max_sweep_cases == 4 && max_trials == 40 && ...
    max_stored_numeric_values == 100000 && max_figure_groups == 6, ...
    'P20 resource ceilings must remain fixed.');
workspace_vector_equivalents = 80;
figure_vector_equivalents = 30;
resource_safety_vector_equivalents = 10;
estimated_stored_numeric_values = max_record_samples*( ...
    workspace_vector_equivalents + figure_vector_equivalents + ...
    resource_safety_vector_equivalents);
assert(record_sample_count <= max_record_samples && ...
    max(record_length_sweep) <= max_record_samples && ...
    max(record_length_sweep) <= max_fft_length && ...
    numel(snr_sweep_db) <= max_sweep_cases && ...
    numel(record_length_sweep) <= max_sweep_cases && ...
    trial_count <= max_trials && ...
    estimated_stored_numeric_values <= max_stored_numeric_values && ...
    6 <= max_figure_groups, ...
    'A P20 record, FFT, sweep, trial, storage, or figure ceiling was exceeded.');

% Validation succeeded: replace only this module's previous output state.
close(findall(groot, 'Type', 'figure', 'Tag', 'P20'));
results = struct();

%% Baseline: one noisy fractional-bin complex tone
private_stream = RandStream('mt19937ar', 'Seed', random_seed);
time_s = (0:record_sample_count-1)/fs_hz;
true_phase_v = 2*pi*tone_frequency_hz*time_s + tone_phase_rad;
clean_iq_v = tone_amplitude_v*exp(1j*true_phase_v);
noise_rms_v = tone_amplitude_v*10^(-baseline_snr_db/20);
complex_noise_v = noise_rms_v/sqrt(2)*( ...
    randn(private_stream, 1, record_sample_count) + ...
    1j*randn(private_stream, 1, record_sample_count));
noisy_iq_v = clean_iq_v + complex_noise_v;

baseline_fft_v = fft(noisy_iq_v);
baseline_fft_magnitude_v = abs(baseline_fft_v)/record_sample_count;
[~, peak_index] = max(baseline_fft_magnitude_v);
peak_zero_index = peak_index - 1;
if peak_zero_index >= record_sample_count/2
    peak_signed_bin = peak_zero_index - record_sample_count;
else
    peak_signed_bin = peak_zero_index;
end
peak_bin_frequency_hz = peak_signed_bin*fs_hz/record_sample_count;

left_index = mod(peak_index-2, record_sample_count) + 1;
right_index = mod(peak_index, record_sample_count) + 1;
log_left = log(max(baseline_fft_magnitude_v(left_index), eps));
log_center = log(max(baseline_fft_magnitude_v(peak_index), eps));
log_right = log(max(baseline_fft_magnitude_v(right_index), eps));
interpolation_denominator = log_left - 2*log_center + log_right;
assert(abs(interpolation_denominator) > eps, ...
    'The three-bin interpolation curvature is too small.');
interpolated_bin_offset = 0.5*(log_left-log_right)/ ...
    interpolation_denominator;
interpolated_bin_offset = max(-0.5, min(0.5, interpolated_bin_offset));
interpolated_signed_bin = peak_signed_bin + interpolated_bin_offset;
if interpolated_signed_bin >= record_sample_count/2
    interpolated_signed_bin = interpolated_signed_bin - record_sample_count;
elseif interpolated_signed_bin < -record_sample_count/2
    interpolated_signed_bin = interpolated_signed_bin + record_sample_count;
end
interpolated_frequency_hz = interpolated_signed_bin*fs_hz/record_sample_count;

adjacent_products_v2 = conj(noisy_iq_v(1:end-1)).*noisy_iq_v(2:end);
coherent_adjacent_product_v2 = sum(adjacent_products_v2);
phase_increment_rad = angle(coherent_adjacent_product_v2);
phase_increment_frequency_hz = phase_increment_rad*fs_hz/(2*pi);
baseline_coherence = abs(coherent_adjacent_product_v2)/ ...
    sum(abs(adjacent_products_v2));

estimator_names = {'Peak FFT bin', 'Interpolated FFT', 'Phase increment'};
baseline_frequency_estimates_hz = [peak_bin_frequency_hz ...
    interpolated_frequency_hz phase_increment_frequency_hz];
baseline_frequency_errors_hz = baseline_frequency_estimates_hz - ...
    tone_frequency_hz;
baseline_phase_estimates_rad = zeros(1, 3);
baseline_phase_errors_rad = zeros(1, 3);
for estimator_index = 1:3
    estimated_reference = exp(-1j*2*pi* ...
        baseline_frequency_estimates_hz(estimator_index)*time_s);
    baseline_phase_estimates_rad(estimator_index) = angle(sum( ...
        noisy_iq_v.*estimated_reference));
    phase_difference_rad = baseline_phase_estimates_rad(estimator_index) - ...
        tone_phase_rad;
    baseline_phase_errors_rad(estimator_index) = atan2( ...
        sin(phase_difference_rad), cos(phase_difference_rad));
end
assert(all(isfinite(baseline_frequency_estimates_hz)) && ...
    all(isfinite(baseline_phase_estimates_rad)) && ...
    baseline_coherence > coherence_threshold, ...
    'The deterministic baseline must produce finite, coherent estimates.');

fprintf('\nP20 baseline: fractional-bin tone in complex noise\n');
fprintf('  truth: %.3f Hz, initial phase %.3f rad, SNR %.1f dB, duration %.3f s\n', ...
    tone_frequency_hz, tone_phase_rad, baseline_snr_db, ...
    record_sample_count/fs_hz);
for estimator_index = 1:3
    fprintf('  %-17s %9.4f Hz (%+.4f Hz), phase %+.4f rad (%+.4f rad)\n', ...
        estimator_names{estimator_index}, ...
        baseline_frequency_estimates_hz(estimator_index), ...
        baseline_frequency_errors_hz(estimator_index), ...
        baseline_phase_estimates_rad(estimator_index), ...
        baseline_phase_errors_rad(estimator_index));
end
fprintf('  adjacent-product coherence: %.3f (gate %.2f)\n', ...
    baseline_coherence, coherence_threshold);

%% Baseline view 1: noisy samples are measurements of a rotating phasor
view_sample_count = 48;
view_indices = 1:view_sample_count;
figure('Name', 'P20 noisy rotating phasor', 'Tag', 'P20', ...
    'Color', 'w', 'Position', [50 50 1120 720]);
subplot(2, 2, 1);
plot(1000*time_s(view_indices), real(clean_iq_v(view_indices)), '-', ...
    'Color', [0.2 0.6 0.3]); hold on;
plot(1000*time_s(view_indices), real(noisy_iq_v(view_indices)), 'o', ...
    'Color', [0.2 0.35 0.8]);
grid on; xlabel('Time (ms)'); ylabel('In-phase sample I (V)');
legend('Clean', 'Noisy', 'Location', 'best');
title('Finite noisy I samples');
subplot(2, 2, 2);
plot(1000*time_s(view_indices), imag(clean_iq_v(view_indices)), '-', ...
    'Color', [0.2 0.6 0.3]); hold on;
plot(1000*time_s(view_indices), imag(noisy_iq_v(view_indices)), 'o', ...
    'Color', [0.75 0.25 0.25]);
grid on; xlabel('Time (ms)'); ylabel('Quadrature sample Q (V)');
legend('Clean', 'Noisy', 'Location', 'best');
title('Finite noisy Q samples');
subplot(2, 2, [3 4]);
plot(real(clean_iq_v(view_indices)), imag(clean_iq_v(view_indices)), '-', ...
    'Color', [0.2 0.6 0.3]); hold on;
plot(real(noisy_iq_v(view_indices)), imag(noisy_iq_v(view_indices)), 'o', ...
    'Color', [0.35 0.3 0.75]);
grid on; axis equal;
xlabel('In-phase sample I (V)'); ylabel('Quadrature sample Q (V)');
legend('Clean trajectory', 'Noisy measurements', 'Location', 'best');
title(sprintf('Rotation sampled for %.3f s at %.1f dB SNR', ...
    record_sample_count/fs_hz, baseline_snr_db));

%% Baseline view 2: FFT grid, sub-bin interpolation, and phase increment
frequency_axis_hz = (0:record_sample_count-1)*fs_hz/record_sample_count;
plot_floor_v = 1e-8;
figure('Name', 'P20 baseline frequency estimates', 'Tag', 'P20', ...
    'Color', 'w', 'Position', [80 70 1120 700]);
subplot(2, 1, 1);
plot(frequency_axis_hz, 20*log10(max(baseline_fft_magnitude_v, ...
    plot_floor_v)), 'o-', 'Color', [0.15 0.35 0.75]); hold on;
plot([tone_frequency_hz tone_frequency_hz], [-80 5], '-', ...
    'Color', [0.15 0.65 0.25]);
plot([peak_bin_frequency_hz peak_bin_frequency_hz], [-80 5], '--', ...
    'Color', [0.85 0.25 0.20]);
plot([interpolated_frequency_hz interpolated_frequency_hz], [-80 5], ':', ...
    'Color', [0.55 0.20 0.75]);
grid on; xlim([95 150]); ylim([-55 5]);
xlabel('Frequency (Hz)'); ylabel('Magnitude (dB re 1 V)');
legend('FFT samples', 'Truth', 'Peak bin', 'Interpolated peak', ...
    'Location', 'best');
title(sprintf('FFT spacing %.2f Hz; tone is between bins', ...
    fs_hz/record_sample_count));
subplot(2, 1, 2);
stem(1:3, baseline_frequency_errors_hz, 'filled', ...
    'Color', [0.25 0.45 0.75]);
grid on; xlim([0.5 3.5]);
set(gca, 'XTick', 1:3, 'XTickLabel', estimator_names);
ylabel('Frequency error (Hz)');
title(sprintf('Phase-increment coherence %.3f', baseline_coherence));

%% Baseline view 3: frequency error becomes phase slope after de-rotation
residual_phase_rad = zeros(3, record_sample_count);
for estimator_index = 1:3
    residual_iq_v = noisy_iq_v.*exp(-1j*2*pi* ...
        baseline_frequency_estimates_hz(estimator_index)*time_s);
    residual_phase_rad(estimator_index, :) = angle(residual_iq_v);
end
figure('Name', 'P20 coherent phase estimates', 'Tag', 'P20', ...
    'Color', 'w', 'Position', [110 90 1120 700]);
for estimator_index = 1:3
    subplot(2, 2, estimator_index);
    plot(1000*time_s, residual_phase_rad(estimator_index, :), '.', ...
        'Color', [0.20 0.40+0.10*estimator_index 0.70]);
    hold on;
    plot([1000*time_s(1) 1000*time_s(end)], ...
        [baseline_phase_estimates_rad(estimator_index) ...
        baseline_phase_estimates_rad(estimator_index)], '-', ...
        'Color', [0.85 0.25 0.15]);
    grid on; ylim([-pi pi]);
    xlabel('Time (ms)'); ylabel('Residual phase (rad)');
    title(sprintf('%s: phase error %+.3f rad', ...
        estimator_names{estimator_index}, ...
        baseline_phase_errors_rad(estimator_index)));
end
subplot(2, 2, 4);
stem(1:3, baseline_phase_errors_rad, 'filled', ...
    'Color', [0.55 0.25 0.70]);
grid on; xlim([0.5 3.5]); ylim([-pi pi]);
set(gca, 'XTick', 1:3, 'XTickLabel', estimator_names);
ylabel('Wrapped initial-phase error (rad)');
title('Compare phase modulo 2\pi');

%% Sweep 1: change only SNR and measure bias plus trial-to-trial spread
% Each row is one independent unit-RMS complex-noise trial. Reusing the same
% rows across SNR cases makes noise scale the only changed input. Sweep 2 uses
% prefixes of these same rows so record length is its only changed input.
sweep_standard_noise = 1/sqrt(2)*( ...
    randn(private_stream, trial_count, max_record_samples) + ...
    1j*randn(private_stream, trial_count, max_record_samples));
snr_frequency_bias_hz = zeros(3, numel(snr_sweep_db));
snr_frequency_std_hz = zeros(3, numel(snr_sweep_db));
snr_phase_bias_rad = zeros(3, numel(snr_sweep_db));
snr_phase_circular_std_rad = zeros(3, numel(snr_sweep_db));
snr_mean_coherence = zeros(size(snr_sweep_db));
for sweep_index = 1:numel(snr_sweep_db)
    case_noise_rms_v = tone_amplitude_v*10^(-snr_sweep_db(sweep_index)/20);
    frequency_error_trials_hz = zeros(3, trial_count);
    phase_error_trials_rad = zeros(3, trial_count);
    coherence_trials = zeros(1, trial_count);
    for trial_index = 1:trial_count
        trial_noise_v = case_noise_rms_v* ...
            sweep_standard_noise(trial_index, 1:record_sample_count);
        trial_iq_v = clean_iq_v + trial_noise_v;
        trial_fft_magnitude_v = abs(fft(trial_iq_v))/record_sample_count;
        [~, trial_peak_index] = max(trial_fft_magnitude_v);
        trial_peak_zero_index = trial_peak_index - 1;
        if trial_peak_zero_index >= record_sample_count/2
            trial_peak_bin = trial_peak_zero_index - record_sample_count;
        else
            trial_peak_bin = trial_peak_zero_index;
        end
        trial_left_index = mod(trial_peak_index-2, record_sample_count) + 1;
        trial_right_index = mod(trial_peak_index, record_sample_count) + 1;
        trial_log_left = log(max(trial_fft_magnitude_v(trial_left_index), eps));
        trial_log_center = log(max(trial_fft_magnitude_v(trial_peak_index), eps));
        trial_log_right = log(max(trial_fft_magnitude_v(trial_right_index), eps));
        trial_denominator = trial_log_left - 2*trial_log_center + trial_log_right;
        if abs(trial_denominator) > eps
            trial_delta = 0.5*(trial_log_left-trial_log_right)/trial_denominator;
        else
            trial_delta = 0;
        end
        trial_delta = max(-0.5, min(0.5, trial_delta));
        trial_interpolated_bin = trial_peak_bin + trial_delta;
        if trial_interpolated_bin >= record_sample_count/2
            trial_interpolated_bin = trial_interpolated_bin - record_sample_count;
        elseif trial_interpolated_bin < -record_sample_count/2
            trial_interpolated_bin = trial_interpolated_bin + record_sample_count;
        end
        trial_adjacent_v2 = conj(trial_iq_v(1:end-1)).*trial_iq_v(2:end);
        trial_coherent_product_v2 = sum(trial_adjacent_v2);
        trial_frequency_estimates_hz = [trial_peak_bin*fs_hz/record_sample_count ...
            trial_interpolated_bin*fs_hz/record_sample_count ...
            angle(trial_coherent_product_v2)*fs_hz/(2*pi)];
        coherence_trials(trial_index) = abs(trial_coherent_product_v2)/ ...
            sum(abs(trial_adjacent_v2));
        frequency_error_trials_hz(:, trial_index) = ...
            trial_frequency_estimates_hz(:) - tone_frequency_hz;
        for estimator_index = 1:3
            trial_reference = exp(-1j*2*pi* ...
                trial_frequency_estimates_hz(estimator_index)*time_s);
            trial_phase_estimate_rad = angle(sum(trial_iq_v.*trial_reference));
            trial_phase_difference_rad = trial_phase_estimate_rad-tone_phase_rad;
            phase_error_trials_rad(estimator_index, trial_index) = atan2( ...
                sin(trial_phase_difference_rad), cos(trial_phase_difference_rad));
        end
    end
    snr_frequency_bias_hz(:, sweep_index) = mean( ...
        frequency_error_trials_hz, 2);
    snr_frequency_std_hz(:, sweep_index) = std( ...
        frequency_error_trials_hz, 0, 2);
    snr_phase_bias_rad(:, sweep_index) = atan2(mean( ...
        sin(phase_error_trials_rad), 2), mean(cos(phase_error_trials_rad), 2));
    phase_resultant = abs(mean(exp(1j*phase_error_trials_rad), 2));
    snr_phase_circular_std_rad(:, sweep_index) = sqrt(max(0, ...
        -2*log(max(phase_resultant, eps))));
    snr_mean_coherence(sweep_index) = mean(coherence_trials);
end

figure('Name', 'P20 SNR estimator sweep', 'Tag', 'P20', ...
    'Color', 'w', 'Position', [140 100 1120 760]);
subplot(3, 2, 1);
plot(snr_sweep_db, snr_frequency_bias_hz.', 'o-', 'LineWidth', 1.2);
grid on; xlabel('SNR (dB)'); ylabel('Frequency bias (Hz)');
legend(estimator_names, 'Location', 'best'); title('Bias across 40 trials');
subplot(3, 2, 2);
semilogy(snr_sweep_db, max(snr_frequency_std_hz.', 1e-3), ...
    'o-', 'LineWidth', 1.2);
grid on; xlabel('SNR (dB)'); ylabel('Frequency standard deviation (Hz)');
title('Random spread falls as SNR rises');
subplot(3, 2, 3);
plot(snr_sweep_db, snr_phase_bias_rad.'*180/pi, 'o-', 'LineWidth', 1.2);
grid on; xlabel('SNR (dB)'); ylabel('Circular phase bias (deg)');
title('Phase bias is wrapped before averaging');
subplot(3, 2, 4);
semilogy(snr_sweep_db, max(snr_phase_circular_std_rad.'*180/pi, 0.01), ...
    'o-', 'LineWidth', 1.2);
grid on; xlabel('SNR (dB)'); ylabel('Phase circular std (deg)');
title('Wrapped phase spread');
subplot(3, 2, [5 6]);
plot(snr_sweep_db, snr_mean_coherence, 'o-', ...
    'Color', [0.20 0.55 0.35], 'LineWidth', 1.2); hold on;
plot([snr_sweep_db(1) snr_sweep_db(end)], ...
    [coherence_threshold coherence_threshold], 'k--');
grid on; ylim([0 1]); xlabel('SNR (dB)');
ylabel('Mean adjacent-product coherence (0 to 1)');
legend('Mean coherence', 'Reporting gate', 'Location', 'best');
title('Coherence has its own dimensionless scale');

%% Sweep 2: change only record length with SNR and tone fixed
length_frequency_bias_hz = zeros(3, numel(record_length_sweep));
length_frequency_std_hz = zeros(3, numel(record_length_sweep));
length_phase_bias_rad = zeros(3, numel(record_length_sweep));
length_phase_circular_std_rad = zeros(3, numel(record_length_sweep));
length_mean_coherence = zeros(size(record_length_sweep));
for sweep_index = 1:numel(record_length_sweep)
    case_sample_count = record_length_sweep(sweep_index);
    case_time_s = (0:case_sample_count-1)/fs_hz;
    case_clean_iq_v = tone_amplitude_v*exp(1j*( ...
        2*pi*tone_frequency_hz*case_time_s + tone_phase_rad));
    frequency_error_trials_hz = zeros(3, trial_count);
    phase_error_trials_rad = zeros(3, trial_count);
    coherence_trials = zeros(1, trial_count);
    for trial_index = 1:trial_count
        trial_noise_v = noise_rms_v* ...
            sweep_standard_noise(trial_index, 1:case_sample_count);
        trial_iq_v = case_clean_iq_v + trial_noise_v;
        trial_fft_magnitude_v = abs(fft(trial_iq_v))/case_sample_count;
        [~, trial_peak_index] = max(trial_fft_magnitude_v);
        trial_peak_zero_index = trial_peak_index - 1;
        if trial_peak_zero_index >= case_sample_count/2
            trial_peak_bin = trial_peak_zero_index - case_sample_count;
        else
            trial_peak_bin = trial_peak_zero_index;
        end
        trial_left_index = mod(trial_peak_index-2, case_sample_count) + 1;
        trial_right_index = mod(trial_peak_index, case_sample_count) + 1;
        trial_log_left = log(max(trial_fft_magnitude_v(trial_left_index), eps));
        trial_log_center = log(max(trial_fft_magnitude_v(trial_peak_index), eps));
        trial_log_right = log(max(trial_fft_magnitude_v(trial_right_index), eps));
        trial_denominator = trial_log_left - 2*trial_log_center + trial_log_right;
        if abs(trial_denominator) > eps
            trial_delta = 0.5*(trial_log_left-trial_log_right)/trial_denominator;
        else
            trial_delta = 0;
        end
        trial_delta = max(-0.5, min(0.5, trial_delta));
        trial_interpolated_bin = trial_peak_bin + trial_delta;
        if trial_interpolated_bin >= case_sample_count/2
            trial_interpolated_bin = trial_interpolated_bin - case_sample_count;
        elseif trial_interpolated_bin < -case_sample_count/2
            trial_interpolated_bin = trial_interpolated_bin + case_sample_count;
        end
        trial_adjacent_v2 = conj(trial_iq_v(1:end-1)).*trial_iq_v(2:end);
        trial_coherent_product_v2 = sum(trial_adjacent_v2);
        trial_frequency_estimates_hz = [trial_peak_bin*fs_hz/case_sample_count ...
            trial_interpolated_bin*fs_hz/case_sample_count ...
            angle(trial_coherent_product_v2)*fs_hz/(2*pi)];
        length_mean_coherence(sweep_index) = ...
            length_mean_coherence(sweep_index) + ...
            abs(trial_coherent_product_v2)/sum(abs(trial_adjacent_v2));
        frequency_error_trials_hz(:, trial_index) = ...
            trial_frequency_estimates_hz(:) - tone_frequency_hz;
        for estimator_index = 1:3
            trial_reference = exp(-1j*2*pi* ...
                trial_frequency_estimates_hz(estimator_index)*case_time_s);
            trial_phase_estimate_rad = angle(sum(trial_iq_v.*trial_reference));
            trial_phase_difference_rad = trial_phase_estimate_rad-tone_phase_rad;
            phase_error_trials_rad(estimator_index, trial_index) = atan2( ...
                sin(trial_phase_difference_rad), cos(trial_phase_difference_rad));
        end
    end
    length_frequency_bias_hz(:, sweep_index) = mean( ...
        frequency_error_trials_hz, 2);
    length_frequency_std_hz(:, sweep_index) = std( ...
        frequency_error_trials_hz, 0, 2);
    length_phase_bias_rad(:, sweep_index) = atan2(mean( ...
        sin(phase_error_trials_rad), 2), mean(cos(phase_error_trials_rad), 2));
    phase_resultant = abs(mean(exp(1j*phase_error_trials_rad), 2));
    length_phase_circular_std_rad(:, sweep_index) = sqrt(max(0, ...
        -2*log(max(phase_resultant, eps))));
    length_mean_coherence(sweep_index) = ...
        length_mean_coherence(sweep_index)/trial_count;
end

figure('Name', 'P20 record length estimator sweep', 'Tag', 'P20', ...
    'Color', 'w', 'Position', [170 110 1120 760]);
subplot(2, 2, 1);
plot(record_length_sweep/fs_hz, length_frequency_bias_hz.', ...
    'o-', 'LineWidth', 1.2);
grid on; xlabel('Observation duration (s)'); ylabel('Frequency bias (Hz)');
legend(estimator_names, 'Location', 'best'); title('Same tone and SNR');
subplot(2, 2, 2);
loglog(record_length_sweep/fs_hz, max(length_frequency_std_hz.', 1e-3), ...
    'o-', 'LineWidth', 1.2);
grid on; xlabel('Observation duration (s)');
ylabel('Frequency standard deviation (Hz)');
title('Longer coherent observation reduces spread');
subplot(2, 2, 3);
plot(record_length_sweep/fs_hz, length_phase_bias_rad.'*180/pi, ...
    'o-', 'LineWidth', 1.2);
grid on; xlabel('Observation duration (s)');
ylabel('Circular phase bias (deg)');
title('Frequency error couples into initial phase');
subplot(2, 2, 4);
loglog(record_length_sweep/fs_hz, ...
    max(length_phase_circular_std_rad.'*180/pi, 0.01), ...
    'o-', 'LineWidth', 1.2);
grid on; xlabel('Observation duration (s)');
ylabel('Phase circular std (deg)');
title('More coherent samples reduce phase spread');

%% Broken case: divide a wrapped endpoint angle, then ignore low amplitude
noise_free_iq_v = tone_amplitude_v*exp(1j*true_phase_v);
true_total_phase_change_rad = 2*pi*tone_frequency_hz* ...
    (record_sample_count-1)/fs_hz;
wrapped_endpoint_phase_change_rad = angle( ...
    noise_free_iq_v(end)*conj(noise_free_iq_v(1)));
broken_endpoint_frequency_hz = wrapped_endpoint_phase_change_rad*fs_hz/( ...
    2*pi*(record_sample_count-1));
noise_free_adjacent_v2 = conj(noise_free_iq_v(1:end-1)).* ...
    noise_free_iq_v(2:end);
recovered_frequency_hz = angle(sum(noise_free_adjacent_v2))*fs_hz/(2*pi);

low_amplitude_clean_iq_v = low_amplitude_v*exp(1j*true_phase_v);
% Reuse the baseline noise samples so amplitude is the only changed input.
low_amplitude_iq_v = low_amplitude_clean_iq_v + complex_noise_v;
low_amplitude_adjacent_v2 = conj(low_amplitude_iq_v(1:end-1)).* ...
    low_amplitude_iq_v(2:end);
low_amplitude_product_v2 = sum(low_amplitude_adjacent_v2);
low_amplitude_frequency_hz = angle(low_amplitude_product_v2)*fs_hz/(2*pi);
low_amplitude_coherence = abs(low_amplitude_product_v2)/ ...
    sum(abs(low_amplitude_adjacent_v2));
low_amplitude_reported_frequency_hz = NaN;
if low_amplitude_coherence >= coherence_threshold
    low_amplitude_reported_frequency_hz = low_amplitude_frequency_hz;
end
assert(abs(recovered_frequency_hz-tone_frequency_hz) < 1e-10 && ...
    abs(broken_endpoint_frequency_hz-tone_frequency_hz) > 100, ...
    'The noise-free broken endpoint and coherent recovery must stay distinct.');
assert(low_amplitude_coherence < coherence_threshold && ...
    isnan(low_amplitude_reported_frequency_hz), ...
    'The deterministic low-amplitude case must be rejected by coherence.');

figure('Name', 'P20 wrapped phase and low amplitude failure', 'Tag', 'P20', ...
    'Color', 'w', 'Position', [200 120 1120 760]);
subplot(2, 2, 1);
plot(1000*time_s, angle(noise_free_iq_v), '-', ...
    'Color', [0.30 0.40 0.75]);
grid on; ylim([-pi pi]);
xlabel('Time (ms)'); ylabel('Wrapped sample phase (rad)');
title(sprintf('True accumulated change %.1f rad wraps repeatedly', ...
    true_total_phase_change_rad));
subplot(2, 2, 2);
bar(1:2, [broken_endpoint_frequency_hz recovered_frequency_hz]);
hold on; plot([0.5 2.5], [tone_frequency_hz tone_frequency_hz], 'k--');
grid on; xlim([0.5 2.5]);
set(gca, 'XTick', 1:2, ...
    'XTickLabel', {'Wrapped endpoint', 'Coherent increments'});
ylabel('Frequency estimate (Hz)');
title('A wrapped total phase is not an unwrapped phase change');
subplot(2, 2, 3);
plot(real(low_amplitude_iq_v(view_indices)), ...
    imag(low_amplitude_iq_v(view_indices)), 'o', ...
    'Color', [0.80 0.25 0.20]);
grid on; axis equal;
xlabel('In-phase sample I (V)'); ylabel('Quadrature sample Q (V)');
title(sprintf('Amplitude %.2f V with fixed %.3f V noise RMS', ...
    low_amplitude_v, noise_rms_v));
subplot(2, 2, 4);
bar(1:2, [baseline_coherence low_amplitude_coherence]); hold on;
plot([0.5 2.5], [coherence_threshold coherence_threshold], 'k--');
grid on; ylim([0 1]); xlim([0.5 2.5]);
set(gca, 'XTick', 1:2, 'XTickLabel', {'Baseline', 'Low amplitude'});
ylabel('Adjacent-product coherence (0 to 1)');
title('Reject evidence below the coherence gate');

fprintf('\nP20 deliberately broken and low-amplitude cases\n');
fprintf('  wrapped endpoint: %.3f Hz versus true %.3f Hz\n', ...
    broken_endpoint_frequency_hz, tone_frequency_hz);
fprintf('  coherent adjacent increments recover %.3f Hz noise-free\n', ...
    recovered_frequency_hz);
fprintf('  low-amplitude candidate %.3f Hz has coherence %.3f: REJECTED\n', ...
    low_amplitude_frequency_hz, low_amplitude_coherence);
fprintf('  If interrupted with Ctrl+C, rerun from the top; only a partial P20 figure set and incomplete results can remain.\n');

%% Retained workspace results
results.random_seed = random_seed;
results.fs_hz = fs_hz;
results.record_sample_count = record_sample_count;
results.observation_duration_s = record_sample_count/fs_hz;
results.tone_frequency_hz = tone_frequency_hz;
results.tone_phase_rad = tone_phase_rad;
results.baseline_snr_db = baseline_snr_db;
results.time_s = time_s;
results.clean_iq_v = clean_iq_v;
results.noisy_iq_v = noisy_iq_v;
results.frequency_axis_hz = frequency_axis_hz;
results.baseline_fft_magnitude_v = baseline_fft_magnitude_v;
results.estimator_names = estimator_names;
results.baseline_frequency_estimates_hz = baseline_frequency_estimates_hz;
results.baseline_frequency_errors_hz = baseline_frequency_errors_hz;
results.baseline_phase_estimates_rad = baseline_phase_estimates_rad;
results.baseline_phase_errors_rad = baseline_phase_errors_rad;
results.baseline_coherence = baseline_coherence;
results.snr_sweep_db = snr_sweep_db;
results.snr_frequency_bias_hz = snr_frequency_bias_hz;
results.snr_frequency_std_hz = snr_frequency_std_hz;
results.snr_phase_bias_rad = snr_phase_bias_rad;
results.snr_phase_circular_std_rad = snr_phase_circular_std_rad;
results.snr_mean_coherence = snr_mean_coherence;
results.record_length_sweep = record_length_sweep;
results.length_frequency_bias_hz = length_frequency_bias_hz;
results.length_frequency_std_hz = length_frequency_std_hz;
results.length_phase_bias_rad = length_phase_bias_rad;
results.length_phase_circular_std_rad = length_phase_circular_std_rad;
results.length_mean_coherence = length_mean_coherence;
results.true_total_phase_change_rad = true_total_phase_change_rad;
results.wrapped_endpoint_phase_change_rad = wrapped_endpoint_phase_change_rad;
results.broken_endpoint_frequency_hz = broken_endpoint_frequency_hz;
results.recovered_frequency_hz = recovered_frequency_hz;
results.low_amplitude_frequency_hz = low_amplitude_frequency_hz;
results.low_amplitude_coherence = low_amplitude_coherence;
results.low_amplitude_reported_frequency_hz = ...
    low_amplitude_reported_frequency_hz;
