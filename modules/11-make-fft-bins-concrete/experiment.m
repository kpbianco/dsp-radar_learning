%% P11: Make FFT Bins Concrete
% Guiding question: What frequency does each FFT bin represent?
% Learning dependency: P10 sample-rate and finite-record behavior.
% Base MATLAB only. The first spectrum is computed both as explicit DFT
% projections and with fft so the operation is visible before acceleration.

%% Visible controls
random_seed = 1011;
fs_hz = 1024;
record_sample_count = 64;
tone_bin = 9;                    % Zero-based DFT bin number, not MATLAB index.
tone_bin_offset = 0.0;           % Fractions of one bin.
tone_amplitude_v = 1.0;
tone_phase_rad = 0.35;
noise_rms_v = 0.002;
fractional_bin_sweep = [0 0.25 0.50];
record_length_sweep = [32 64 128];
phase_valid_threshold_v = 0.05;
comparison_tolerance = 1e-10;

% Fixed ceilings keep every rerun finite and cancellable with Ctrl+C.
max_record_samples = 256;
max_sweep_cases = 8;
max_figure_groups = 4;
max_explicit_dft_terms = 65536;

%% Validate controls before random, signal, DFT, or figure allocation
assert(isnumeric(random_seed) && isscalar(random_seed) && isreal(random_seed) && ...
    ~islogical(random_seed) && isfinite(random_seed) && random_seed >= 0 && ...
    random_seed <= 2^32 - 1 && random_seed == floor(random_seed), ...
    'random_seed must be an integer from 0 through 2^32-1.');
assert(isnumeric(fs_hz) && isscalar(fs_hz) && isreal(fs_hz) && ...
    ~islogical(fs_hz) && isfinite(fs_hz) && fs_hz > 0, ...
    'fs_hz must be finite, positive, and real.');
assert(isnumeric(record_sample_count) && isscalar(record_sample_count) && ...
    isreal(record_sample_count) && ~islogical(record_sample_count) && ...
    isfinite(record_sample_count) && record_sample_count >= 16 && ...
    record_sample_count == floor(record_sample_count) && ...
    mod(record_sample_count, 2) == 0, ...
    'record_sample_count must be an even integer of at least 16.');
assert(isnumeric(tone_bin) && isscalar(tone_bin) && isreal(tone_bin) && ...
    ~islogical(tone_bin) && isfinite(tone_bin) && tone_bin >= 1 && ...
    tone_bin == floor(tone_bin) && tone_bin < record_sample_count/2, ...
    'tone_bin must be an integer strictly between DC and Nyquist.');
assert(isnumeric(tone_bin_offset) && isscalar(tone_bin_offset) && ...
    isreal(tone_bin_offset) && ~islogical(tone_bin_offset) && ...
    isfinite(tone_bin_offset) && ...
    tone_bin_offset >= 0 && tone_bin_offset <= 0.5, ...
    'tone_bin_offset must lie from 0 through one-half bin.');
assert(isnumeric(tone_amplitude_v) && isscalar(tone_amplitude_v) && ...
    isreal(tone_amplitude_v) && isfinite(tone_amplitude_v) && ...
    tone_amplitude_v > 0, 'tone_amplitude_v must be finite and positive.');
assert(isnumeric(tone_phase_rad) && isscalar(tone_phase_rad) && ...
    isreal(tone_phase_rad) && isfinite(tone_phase_rad), ...
    'tone_phase_rad must be finite and real.');
assert(isnumeric(noise_rms_v) && isscalar(noise_rms_v) && ...
    isreal(noise_rms_v) && isfinite(noise_rms_v) && noise_rms_v >= 0 && ...
    noise_rms_v <= 0.05*tone_amplitude_v, ...
    'noise_rms_v must be from zero through 5 percent of tone amplitude.');
assert(isnumeric(fractional_bin_sweep) && isvector(fractional_bin_sweep) && ...
    isreal(fractional_bin_sweep) && all(isfinite(fractional_bin_sweep)) && ...
    all(fractional_bin_sweep >= 0) && all(fractional_bin_sweep <= 0.5) && ...
    numel(fractional_bin_sweep) >= 3 && all(diff(fractional_bin_sweep) > 0) && ...
    fractional_bin_sweep(1) == 0 && fractional_bin_sweep(end) == 0.5, ...
    'fractional_bin_sweep must increase uniquely from 0 through 0.5.');
assert(isnumeric(record_length_sweep) && isvector(record_length_sweep) && ...
    isreal(record_length_sweep) && all(isfinite(record_length_sweep)) && ...
    all(record_length_sweep >= 16) && ...
    all(record_length_sweep == floor(record_length_sweep)) && ...
    all(mod(record_length_sweep, 2) == 0) && numel(record_length_sweep) >= 3 && ...
    all(diff(record_length_sweep) > 0), ...
    'record_length_sweep must contain at least three unique increasing even lengths.');
assert(isnumeric(phase_valid_threshold_v) && isscalar(phase_valid_threshold_v) && ...
    isreal(phase_valid_threshold_v) && isfinite(phase_valid_threshold_v) && ...
    phase_valid_threshold_v > 0 && phase_valid_threshold_v < tone_amplitude_v, ...
    'phase_valid_threshold_v must be positive and below the tone amplitude.');
assert(isnumeric(comparison_tolerance) && isscalar(comparison_tolerance) && ...
    isreal(comparison_tolerance) && isfinite(comparison_tolerance) && ...
    comparison_tolerance > 0, 'comparison_tolerance must be finite and positive.');
assert(max_record_samples == 256 && max_sweep_cases == 8 && ...
    max_figure_groups == 4 && max_explicit_dft_terms == 65536, ...
    'P11 resource ceilings must remain fixed.');
assert(record_sample_count <= max_record_samples && ...
    all(record_length_sweep <= max_record_samples), ...
    'Record lengths exceed the P11 resource ceiling.');
assert(numel(fractional_bin_sweep) <= max_sweep_cases && ...
    numel(record_length_sweep) <= max_sweep_cases, ...
    'A P11 sweep exceeds the case ceiling.');
assert(record_sample_count^2 <= max_explicit_dft_terms, ...
    'The explicit baseline DFT exceeds its operation ceiling.');

%% Baseline: map zero-based bin k to f_k = k*fs/N
bin_spacing_hz = fs_hz/record_sample_count;
bin_numbers = 0:(record_sample_count - 1);
unshifted_frequency_hz = bin_numbers*bin_spacing_hz;
signed_frequency_hz = unshifted_frequency_hz;
signed_frequency_hz(bin_numbers > record_sample_count/2) = ...
    signed_frequency_hz(bin_numbers > record_sample_count/2) - fs_hz;
centered_frequency_hz = (-record_sample_count/2:(record_sample_count/2 - 1))*bin_spacing_hz;

sample_index = 0:(record_sample_count - 1);
time_s = sample_index/fs_hz;
tone_frequency_hz = (tone_bin + tone_bin_offset)*bin_spacing_hz;
stream = RandStream('mt19937ar', 'Seed', random_seed);
complex_noise_v = noise_rms_v/sqrt(2)*( ...
    randn(stream, 1, record_sample_count) + ...
    1j*randn(stream, 1, record_sample_count));
tone_v = tone_amplitude_v*exp(1j*(2*pi*tone_frequency_hz*time_s + tone_phase_rad));
observed_v = tone_v + complex_noise_v;

% Each DFT bin is a projection onto one discrete complex sinusoid.
% X[k] = sum_{n=0}^{N-1} x[n] exp(-j*2*pi*k*n/N)
dft_projection_v = complex(zeros(1, record_sample_count));
for bin_index = 1:record_sample_count
    k = bin_index - 1;
    basis = exp(-1j*2*pi*k*sample_index/record_sample_count);
    dft_projection_v(bin_index) = sum(observed_v.*basis);
end
fft_projection_v = fft(observed_v);
assert(max(abs(dft_projection_v - fft_projection_v)) < comparison_tolerance, ...
    'Explicit DFT projections and fft must agree.');

baseline_magnitude_v = abs(fft_projection_v)/record_sample_count;
baseline_phase_rad = angle(fft_projection_v);
baseline_phase_rad(baseline_magnitude_v < phase_valid_threshold_v) = NaN;
[baseline_peak_v, baseline_peak_index] = max(baseline_magnitude_v);
baseline_peak_bin = baseline_peak_index - 1;
baseline_peak_frequency_hz = signed_frequency_hz(baseline_peak_index);

baseline_peak_is_nearest = baseline_peak_bin == tone_bin || ...
    (abs(tone_bin_offset - 0.5) < comparison_tolerance && ...
    baseline_peak_bin == tone_bin + 1);
assert(baseline_peak_is_nearest, ...
    'The baseline peak must be one of the nearest DFT bins.');
assert(abs(baseline_peak_frequency_hz - tone_frequency_hz) <= ...
    bin_spacing_hz/2 + comparison_tolerance, ...
    'The baseline peak must be within one-half bin of the tone frequency.');

%% Sweep 1: change only fractional-bin offset
offset_case_count = numel(fractional_bin_sweep);
offset_spectrum_v = zeros(offset_case_count, record_sample_count);
offset_lower_magnitude_v = zeros(1, offset_case_count);
offset_upper_magnitude_v = zeros(1, offset_case_count);
offset_lower_phase_rad = zeros(1, offset_case_count);
offset_upper_phase_rad = zeros(1, offset_case_count);
offset_peak_bin = zeros(1, offset_case_count);

for sweep_index = 1:offset_case_count
    sweep_offset = fractional_bin_sweep(sweep_index);
    sweep_frequency_hz = (tone_bin + sweep_offset)*bin_spacing_hz;
    sweep_tone_v = tone_amplitude_v*exp(1j*( ...
        2*pi*sweep_frequency_hz*time_s + tone_phase_rad));
    % Reuse the identical seeded noise so offset is the only changed input.
    sweep_projection_v = fft(sweep_tone_v + complex_noise_v);
    offset_spectrum_v(sweep_index, :) = abs(sweep_projection_v)/record_sample_count;
    offset_lower_magnitude_v(sweep_index) = ...
        offset_spectrum_v(sweep_index, tone_bin + 1);
    offset_upper_magnitude_v(sweep_index) = ...
        offset_spectrum_v(sweep_index, tone_bin + 2);
    offset_lower_phase_rad(sweep_index) = angle(sweep_projection_v(tone_bin + 1));
    offset_upper_phase_rad(sweep_index) = angle(sweep_projection_v(tone_bin + 2));
    [~, peak_index] = max(offset_spectrum_v(sweep_index, :));
    offset_peak_bin(sweep_index) = peak_index - 1;
end

half_case_index = find(abs(fractional_bin_sweep - 0.5) < comparison_tolerance, 1);
assert(~isempty(half_case_index), 'The offset sweep must include a half-bin case.');
assert(offset_lower_magnitude_v(half_case_index) > 0.60*tone_amplitude_v && ...
    offset_upper_magnitude_v(half_case_index) > 0.60*tone_amplitude_v, ...
    'A half-bin tone must project strongly onto both neighboring bins.');

%% Sweep 2: change only record length for one fixed physical tone
% 144 Hz is half-bin for N=32 and exact-bin for N=64 and N=128 at 1024 Hz.
fixed_tone_frequency_hz = tone_bin*bin_spacing_hz;
length_case_count = numel(record_length_sweep);
record_bin_spacing_hz = zeros(1, length_case_count);
record_expected_bin = zeros(1, length_case_count);
record_peak_bin = zeros(1, length_case_count);
record_peak_frequency_hz = zeros(1, length_case_count);
record_peak_error_hz = zeros(1, length_case_count);
record_peak_magnitude_v = zeros(1, length_case_count);
record_spectra_v = cell(1, length_case_count);
record_frequency_axes_hz = cell(1, length_case_count);

for sweep_index = 1:length_case_count
    sweep_sample_count = record_length_sweep(sweep_index);
    sweep_sample_index = 0:(sweep_sample_count - 1);
    sweep_time_s = sweep_sample_index/fs_hz;
    sweep_tone_v = tone_amplitude_v*exp(1j*( ...
        2*pi*fixed_tone_frequency_hz*sweep_time_s + tone_phase_rad));
    sweep_projection_v = fft(sweep_tone_v);
    sweep_magnitude_v = abs(sweep_projection_v)/sweep_sample_count;
    sweep_spacing_hz = fs_hz/sweep_sample_count;
    sweep_frequency_axis_hz = (0:(sweep_sample_count - 1))*sweep_spacing_hz;
    sweep_signed_axis_hz = sweep_frequency_axis_hz;
    sweep_bins = 0:(sweep_sample_count - 1);
    sweep_signed_axis_hz(sweep_bins > sweep_sample_count/2) = ...
        sweep_signed_axis_hz(sweep_bins > sweep_sample_count/2) - fs_hz;
    [sweep_peak_v, sweep_peak_index] = max(sweep_magnitude_v);

    record_bin_spacing_hz(sweep_index) = sweep_spacing_hz;
    record_expected_bin(sweep_index) = fixed_tone_frequency_hz/sweep_spacing_hz;
    record_peak_bin(sweep_index) = sweep_peak_index - 1;
    record_peak_frequency_hz(sweep_index) = sweep_signed_axis_hz(sweep_peak_index);
    record_peak_error_hz(sweep_index) = ...
        record_peak_frequency_hz(sweep_index) - fixed_tone_frequency_hz;
    record_peak_magnitude_v(sweep_index) = sweep_peak_v;
    record_spectra_v{sweep_index} = sweep_magnitude_v;
    record_frequency_axes_hz{sweep_index} = sweep_signed_axis_hz;
end

assert(all(abs(record_bin_spacing_hz - fs_hz./record_length_sweep) < comparison_tolerance), ...
    'Each record length must use delta-f = fs/N.');
record_fractional_part = record_expected_bin - floor(record_expected_bin);
assert(any(abs(record_fractional_part - 0.5) < comparison_tolerance) && ...
    any(abs(record_expected_bin - round(record_expected_bin)) < comparison_tolerance), ...
    'The record sweep must exercise both half-bin and exact-bin tone placement.');

%% Broken case: confuse MATLAB index with zero-based bin number
broken_frequency_axis_hz = (1:record_sample_count)*bin_spacing_hz;
broken_reported_frequency_hz = broken_frequency_axis_hz(baseline_peak_index);
recovered_frequency_axis_hz = (0:(record_sample_count - 1))*bin_spacing_hz;
recovered_reported_frequency_hz = recovered_frequency_axis_hz(baseline_peak_index);
expected_peak_bin_frequency_hz = baseline_peak_bin*bin_spacing_hz;
broken_frequency_error_hz = ...
    broken_reported_frequency_hz - expected_peak_bin_frequency_hz;
recovered_frequency_error_hz = ...
    recovered_reported_frequency_hz - expected_peak_bin_frequency_hz;

assert(abs((broken_reported_frequency_hz - recovered_reported_frequency_hz) - ...
    bin_spacing_hz) < comparison_tolerance, ...
    'The broken one-based label must be wrong by exactly one bin.');
assert(abs(recovered_frequency_error_hz) < comparison_tolerance, ...
    'Recovery must use k = MATLAB index minus one.');

%% Retained workspace metrics
results.question = 'What frequency does each FFT bin represent?';
results.random_seed = random_seed;
results.fs_hz = fs_hz;
results.record_sample_count = record_sample_count;
results.record_duration_s = record_sample_count/fs_hz;
results.bin_spacing_hz = bin_spacing_hz;
results.baseline_tone_hz = tone_frequency_hz;
results.baseline_peak_bin = baseline_peak_bin;
results.baseline_peak_matlab_index = baseline_peak_index;
results.baseline_peak_frequency_hz = baseline_peak_frequency_hz;
results.baseline_peak_magnitude_v = baseline_peak_v;
results.fractional_bin_sweep = fractional_bin_sweep;
results.offset_lower_magnitude_v = offset_lower_magnitude_v;
results.offset_upper_magnitude_v = offset_upper_magnitude_v;
results.offset_lower_phase_rad = offset_lower_phase_rad;
results.offset_upper_phase_rad = offset_upper_phase_rad;
results.record_length_sweep = record_length_sweep;
results.record_bin_spacing_hz = record_bin_spacing_hz;
results.record_expected_bin = record_expected_bin;
results.record_peak_bin = record_peak_bin;
results.record_peak_frequency_hz = record_peak_frequency_hz;
results.record_peak_error_hz = record_peak_error_hz;
results.record_peak_magnitude_v = record_peak_magnitude_v;
results.broken_reported_frequency_hz = broken_reported_frequency_hz;
results.recovered_reported_frequency_hz = recovered_reported_frequency_hz;
results.expected_peak_bin_frequency_hz = expected_peak_bin_frequency_hz;
results.broken_frequency_error_hz = broken_frequency_error_hz;
results.recovered_frequency_error_hz = recovered_frequency_error_hz;

fprintf('P11 baseline: fs = %.0f samples/s, N = %d, delta-f = %.3f Hz\n', ...
    fs_hz, record_sample_count, bin_spacing_hz);
fprintf('Tone %.3f Hz -> bin %d -> MATLAB index %d, peak %.4f V\n', ...
    tone_frequency_hz, baseline_peak_bin, baseline_peak_index, baseline_peak_v);
fprintf('Half-bin neighbors: %.4f V at bin %d, %.4f V at bin %d\n', ...
    offset_lower_magnitude_v(half_case_index), tone_bin, ...
    offset_upper_magnitude_v(half_case_index), tone_bin + 1);
fprintf('Broken label %.3f Hz; recovered label %.3f Hz\n', ...
    broken_reported_frequency_hz, recovered_reported_frequency_hz);

%% Purposeful figures; replace only prior P11 figures
old_figures = findall(groot, 'Type', 'figure', 'Tag', 'P11');
delete(old_figures);

figure('Name', 'P11 baseline bin map', 'Tag', 'P11');
subplot(2, 2, 1);
plot(time_s*1000, real(observed_v), 'b.-', time_s*1000, imag(observed_v), 'r.-');
grid on;
xlabel('Time (ms)'); ylabel('I/Q amplitude (V)');
title('Finite complex-tone record');
legend('I', 'Q', 'Location', 'best');

subplot(2, 2, 2);
stem(bin_numbers, baseline_magnitude_v, 'filled');
grid on;
xlabel('Zero-based FFT bin k'); ylabel('|X[k]|/N (V)');
title(sprintf('Bin %d = %.1f Hz; tone = %.1f Hz', ...
    tone_bin, tone_bin*bin_spacing_hz, tone_frequency_hz));

subplot(2, 2, 3);
stem(centered_frequency_hz, fftshift(baseline_magnitude_v), 'filled');
grid on;
xlabel('Signed frequency (Hz)'); ylabel('|X[k]|/N (V)');
title('Same bins on a centered frequency axis');

subplot(2, 2, 4);
stem(bin_numbers, baseline_phase_rad, 'filled');
grid on;
xlabel('Zero-based FFT bin k'); ylabel('Projection phase (rad)');
title(sprintf('Phase shown only above %.2f V', phase_valid_threshold_v));

figure('Name', 'P11 fractional-bin sweep', 'Tag', 'P11');
subplot(2, 1, 1);
hold on;
nearby_bins = max(0, tone_bin - 3):min(record_sample_count - 1, tone_bin + 4);
for sweep_index = 1:offset_case_count
    plot(nearby_bins, offset_spectrum_v(sweep_index, nearby_bins + 1), '.-', ...
        'DisplayName', sprintf('offset = %.2f bin', fractional_bin_sweep(sweep_index)));
end
hold off; grid on;
xlabel('Zero-based FFT bin k'); ylabel('|X[k]|/N (V)');
title('Moving one tone between fixed projections');
legend('Location', 'best');

subplot(2, 1, 2);
plot(fractional_bin_sweep, offset_lower_magnitude_v, 'bo-', ...
    fractional_bin_sweep, offset_upper_magnitude_v, 'rs-');
grid on;
xlabel('Tone offset from lower bin (bin fractions)'); ylabel('Neighbor magnitude (V)');
title(sprintf('Energy shared by bins %d and %d', tone_bin, tone_bin + 1));
legend(sprintf('bin %d', tone_bin), sprintf('bin %d', tone_bin + 1), 'Location', 'best');

figure('Name', 'P11 record-length sweep', 'Tag', 'P11');
subplot(2, 1, 1);
hold on;
for sweep_index = 1:length_case_count
    positive_side = record_frequency_axes_hz{sweep_index} >= 0 & ...
        record_frequency_axes_hz{sweep_index} <= fs_hz/2;
    plot(record_frequency_axes_hz{sweep_index}(positive_side), ...
        record_spectra_v{sweep_index}(positive_side), '.-', ...
        'DisplayName', sprintf('N = %d, delta-f = %.1f Hz', ...
        record_length_sweep(sweep_index), record_bin_spacing_hz(sweep_index)));
end
hold off; grid on;
xlim([0 fs_hz/2]);
xlabel('Frequency (Hz)'); ylabel('|X[k]|/N (V)');
title(sprintf('Fixed %.1f Hz tone, only record length changes', fixed_tone_frequency_hz));
legend('Location', 'best');

subplot(2, 1, 2);
plot(record_length_sweep, record_bin_spacing_hz, 'ko-', ...
    record_length_sweep, abs(record_peak_error_hz), 'ms-');
grid on;
xlabel('Record length N (samples)'); ylabel('Frequency (Hz)');
title('Bin spacing and nearest-bin reporting error');
legend('delta-f = f_s/N', '|peak-bin error|', 'Location', 'best');

figure('Name', 'P11 broken axis and recovery', 'Tag', 'P11');
subplot(2, 1, 1);
stem(broken_frequency_axis_hz, baseline_magnitude_v, 'filled');
grid on; xlim([0 fs_hz/2]);
xlabel('Broken frequency label (Hz)'); ylabel('|X[k]|/N (V)');
title(sprintf('Broken: MATLAB index used as k -> reports %.1f Hz', ...
    broken_reported_frequency_hz));

subplot(2, 1, 2);
stem(recovered_frequency_axis_hz, baseline_magnitude_v, 'filled');
grid on; xlim([0 fs_hz/2]);
xlabel('Recovered frequency label (Hz)'); ylabel('|X[k]|/N (V)');
title(sprintf('Recovery: k = index - 1 -> reports %.1f Hz', ...
    recovered_reported_frequency_hz));
