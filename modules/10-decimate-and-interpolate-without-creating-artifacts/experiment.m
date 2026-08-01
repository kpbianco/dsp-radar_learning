%% P10 - Decimate and Interpolate Without Creating Artifacts
% Guiding question:
% Why must filtering accompany sample-rate changes?
%
% Dependency: P09 filter behavior. Base MATLAB only. The FIR design,
% convolution sums, sample selection, and zero insertion are all explicit.

%% Visible controls - validate before allocating records or replacing figures
random_seed = 1010;
fs_hz = 2400;
duration_s = 1;
decimation_factor = 4;
low_tone_hz = 90;
high_tone_hz = 420;
low_tone_amplitude_v = 1.00;
high_tone_amplitude_v = 0.65;
noise_rms_v = 0.01;
anti_alias_cutoff_hz = 240;
filter_tap_count = 65;
plot_floor_db = -90;
time_view_ms = 40;
comparison_tolerance = 1e-10;

high_tone_sweep_hz = [220 280 340 420];
reconstruction_tap_sweep = [9 17 33 65];

max_record_samples = 4800;
max_filter_taps = 129;
max_sweep_cases = 8;
max_figure_groups = 5;

assert(isscalar(random_seed) && isnumeric(random_seed) && isreal(random_seed) && ...
    ~islogical(random_seed) && isfinite(random_seed) && random_seed >= 0 && ...
    random_seed <= 2^32-1 && random_seed == floor(random_seed), ...
    'random_seed must be an integer scalar from zero through 2^32-1.');
assert(isscalar(fs_hz) && isnumeric(fs_hz) && isreal(fs_hz) && ...
    ~islogical(fs_hz) && isfinite(fs_hz) && fs_hz > 0, ...
    'fs_hz must be finite and positive.');
assert(isscalar(duration_s) && isnumeric(duration_s) && isreal(duration_s) && ...
    ~islogical(duration_s) && isfinite(duration_s) && duration_s > 0, ...
    'duration_s must be finite and positive.');
record_sample_count = fs_hz*duration_s;
assert(record_sample_count == floor(record_sample_count) && ...
    record_sample_count >= 256 && record_sample_count <= max_record_samples, ...
    'fs_hz times duration_s must be an integer within the record ceiling.');
assert(isscalar(decimation_factor) && isnumeric(decimation_factor) && ...
    isreal(decimation_factor) && ~islogical(decimation_factor) && ...
    isfinite(decimation_factor) && decimation_factor >= 2 && ...
    decimation_factor == floor(decimation_factor) && ...
    mod(record_sample_count, decimation_factor) == 0, ...
    'decimation_factor must be an integer divisor of the record length.');
fs_low_hz = fs_hz/decimation_factor;
new_nyquist_hz = fs_low_hz/2;
assert(isscalar(low_tone_hz) && isnumeric(low_tone_hz) && ...
    isreal(low_tone_hz) && ~islogical(low_tone_hz) && ...
    isfinite(low_tone_hz) && low_tone_hz > 0 && ...
    low_tone_hz < anti_alias_cutoff_hz, ...
    'low_tone_hz must lie safely inside the anti-alias passband.');
assert(isscalar(high_tone_hz) && isnumeric(high_tone_hz) && ...
    isreal(high_tone_hz) && ~islogical(high_tone_hz) && ...
    isfinite(high_tone_hz) && high_tone_hz > new_nyquist_hz && ...
    high_tone_hz < fs_hz/2, ...
    'high_tone_hz must exceed the new Nyquist limit but remain sampled originally.');
assert(isscalar(low_tone_amplitude_v) && isnumeric(low_tone_amplitude_v) && ...
    isreal(low_tone_amplitude_v) && ~islogical(low_tone_amplitude_v) && ...
    isfinite(low_tone_amplitude_v) && low_tone_amplitude_v > 0, ...
    'low_tone_amplitude_v must be finite and positive.');
assert(isscalar(high_tone_amplitude_v) && isnumeric(high_tone_amplitude_v) && ...
    isreal(high_tone_amplitude_v) && ~islogical(high_tone_amplitude_v) && ...
    isfinite(high_tone_amplitude_v) && high_tone_amplitude_v > 0, ...
    'high_tone_amplitude_v must be finite and positive.');
assert(isscalar(noise_rms_v) && isnumeric(noise_rms_v) && ...
    isreal(noise_rms_v) && ~islogical(noise_rms_v) && ...
    isfinite(noise_rms_v) && noise_rms_v >= 0, ...
    'noise_rms_v must be finite and nonnegative.');
assert(isscalar(anti_alias_cutoff_hz) && isnumeric(anti_alias_cutoff_hz) && ...
    isreal(anti_alias_cutoff_hz) && ~islogical(anti_alias_cutoff_hz) && ...
    isfinite(anti_alias_cutoff_hz) && anti_alias_cutoff_hz > low_tone_hz && ...
    anti_alias_cutoff_hz < new_nyquist_hz, ...
    'anti_alias_cutoff_hz must lie above the wanted tone and below new Nyquist.');
assert(isscalar(filter_tap_count) && isnumeric(filter_tap_count) && ...
    isreal(filter_tap_count) && ~islogical(filter_tap_count) && ...
    isfinite(filter_tap_count) && filter_tap_count >= 9 && ...
    filter_tap_count <= max_filter_taps && ...
    filter_tap_count == floor(filter_tap_count) && mod(filter_tap_count, 2) == 1, ...
    'filter_tap_count must be an odd integer within the filter ceiling.');
assert(isscalar(plot_floor_db) && isnumeric(plot_floor_db) && ...
    isreal(plot_floor_db) && isfinite(plot_floor_db) && plot_floor_db < 0, ...
    'plot_floor_db must be finite and negative.');
assert(isscalar(time_view_ms) && isnumeric(time_view_ms) && ...
    isreal(time_view_ms) && isfinite(time_view_ms) && time_view_ms > 0 && ...
    time_view_ms < 1000*duration_s, ...
    'time_view_ms must fit inside the record.');
assert(isscalar(comparison_tolerance) && isnumeric(comparison_tolerance) && ...
    isreal(comparison_tolerance) && isfinite(comparison_tolerance) && ...
    comparison_tolerance > 0, 'comparison_tolerance must be positive.');
assert(isvector(high_tone_sweep_hz) && isnumeric(high_tone_sweep_hz) && ...
    isreal(high_tone_sweep_hz) && all(isfinite(high_tone_sweep_hz)) && ...
    numel(high_tone_sweep_hz) >= 3 && numel(high_tone_sweep_hz) <= max_sweep_cases && ...
    all(high_tone_sweep_hz > low_tone_hz) && all(high_tone_sweep_hz < fs_hz/2) && ...
    all(diff(high_tone_sweep_hz) > 0) && ...
    any(high_tone_sweep_hz < new_nyquist_hz) && ...
    any(high_tone_sweep_hz > new_nyquist_hz), ...
    'The high-tone sweep must be increasing and straddle new Nyquist.');
assert(isvector(reconstruction_tap_sweep) && isnumeric(reconstruction_tap_sweep) && ...
    isreal(reconstruction_tap_sweep) && all(isfinite(reconstruction_tap_sweep)) && ...
    numel(reconstruction_tap_sweep) >= 3 && ...
    numel(reconstruction_tap_sweep) <= max_sweep_cases && ...
    all(reconstruction_tap_sweep >= 9) && ...
    all(reconstruction_tap_sweep <= max_filter_taps) && ...
    all(reconstruction_tap_sweep == floor(reconstruction_tap_sweep)) && ...
    all(mod(reconstruction_tap_sweep, 2) == 1) && ...
    all(diff(reconstruction_tap_sweep) > 0), ...
    'Reconstruction tap counts must be increasing odd integers within the ceiling.');
assert(max_figure_groups == 5, 'P10 resource ceilings must remain fixed.');

%% Deterministic two-tone input and explicit windowed-sinc low-pass FIR
stream = RandStream('mt19937ar', 'Seed', random_seed);
n = 0:record_sample_count-1;
t_s = n/fs_hz;
noise_v = noise_rms_v*randn(stream, 1, record_sample_count);
x_v = low_tone_amplitude_v*cos(2*pi*low_tone_hz*t_s + 0.20) + ...
    high_tone_amplitude_v*cos(2*pi*high_tone_hz*t_s - 0.35) + noise_v;

filter_delay_samples = (filter_tap_count-1)/2;
centered_tap_index = -filter_delay_samples:filter_delay_samples;
ideal_lowpass = zeros(1, filter_tap_count);
for tap_index = 1:filter_tap_count
    centered_index = centered_tap_index(tap_index);
    if centered_index == 0
        ideal_lowpass(tap_index) = 2*anti_alias_cutoff_hz/fs_hz;
    else
        ideal_lowpass(tap_index) = ...
            sin(2*pi*anti_alias_cutoff_hz*centered_index/fs_hz)/(pi*centered_index);
    end
end
hamming_window = 0.54 - 0.46*cos(2*pi*(0:filter_tap_count-1)/(filter_tap_count-1));
anti_alias_fir = ideal_lowpass .* hamming_window;
anti_alias_fir = anti_alias_fir/sum(anti_alias_fir);

% The anti-alias operation is the visible FIR sum y[n] = sum h[k]x[n-k].
filtered_full_v = zeros(1, record_sample_count+filter_tap_count-1);
for tap_index = 1:filter_tap_count
    output_indices = tap_index:tap_index+record_sample_count-1;
    filtered_full_v(output_indices) = filtered_full_v(output_indices) + ...
        anti_alias_fir(tap_index)*x_v;
end
filtered_aligned_v = filtered_full_v(...
    filter_delay_samples+1:filter_delay_samples+record_sample_count);

%% Baseline decimation - selection cannot remove energy that has already folded
% Naive sample dropping: y_naive[m] = x[mM].
decimated_naive_v = x_v(1:decimation_factor:end);
% Proper decimation: y_filtered[m] = sum h[k]x[mM-k].
decimated_filtered_v = filtered_aligned_v(1:decimation_factor:end);
low_sample_count = numel(decimated_naive_v);
t_low_s = (0:low_sample_count-1)/fs_low_hz;

alias_high_hz = abs(high_tone_hz - round(high_tone_hz/fs_low_hz)*fs_low_hz);
assert(alias_high_hz <= new_nyquist_hz, 'Fold calculation must land inside new Nyquist.');

original_spectrum_v = abs(fft(x_v))/record_sample_count;
original_spectrum_v = 2*original_spectrum_v(1:record_sample_count/2+1);
original_spectrum_v([1 end]) = original_spectrum_v([1 end])/2;
original_frequency_hz = (0:record_sample_count/2)*fs_hz/record_sample_count;

naive_low_spectrum_v = abs(fft(decimated_naive_v))/low_sample_count;
naive_low_spectrum_v = 2*naive_low_spectrum_v(1:low_sample_count/2+1);
naive_low_spectrum_v([1 end]) = naive_low_spectrum_v([1 end])/2;
filtered_low_spectrum_v = abs(fft(decimated_filtered_v))/low_sample_count;
filtered_low_spectrum_v = 2*filtered_low_spectrum_v(1:low_sample_count/2+1);
filtered_low_spectrum_v([1 end]) = filtered_low_spectrum_v([1 end])/2;
low_frequency_hz = (0:low_sample_count/2)*fs_low_hz/low_sample_count;

low_bin = round(low_tone_hz*low_sample_count/fs_low_hz)+1;
alias_bin = round(alias_high_hz*low_sample_count/fs_low_hz)+1;
assert(abs(low_frequency_hz(low_bin)-low_tone_hz) <= comparison_tolerance && ...
    abs(low_frequency_hz(alias_bin)-alias_high_hz) <= comparison_tolerance, ...
    'Baseline tone frequencies must align with the deterministic FFT grid.');
naive_alias_amplitude_v = naive_low_spectrum_v(alias_bin);
filtered_alias_amplitude_v = filtered_low_spectrum_v(alias_bin);
anti_alias_suppression_db = 20*log10(max(naive_alias_amplitude_v, eps)/ ...
    max(filtered_alias_amplitude_v, eps));

%% Baseline interpolation - zero insertion creates images; the FIR removes them
% Zero insertion: z[n] = y[n/L] when n is a multiple of L, otherwise zero.
zero_inserted_v = zeros(1, record_sample_count);
zero_inserted_v(1:decimation_factor:end) = decimated_filtered_v;

% Reconstruction uses L*h[k], so passband amplitude is restored as images fall.
reconstruction_fir = decimation_factor*anti_alias_fir;
reconstructed_full_v = zeros(1, record_sample_count+filter_tap_count-1);
for tap_index = 1:filter_tap_count
    output_indices = tap_index:tap_index+record_sample_count-1;
    reconstructed_full_v(output_indices) = reconstructed_full_v(output_indices) + ...
        reconstruction_fir(tap_index)*zero_inserted_v;
end
reconstructed_v = reconstructed_full_v(...
    filter_delay_samples+1:filter_delay_samples+record_sample_count);

zero_inserted_spectrum_v = abs(fft(zero_inserted_v))/record_sample_count;
zero_inserted_spectrum_v = 2*zero_inserted_spectrum_v(1:record_sample_count/2+1);
zero_inserted_spectrum_v([1 end]) = zero_inserted_spectrum_v([1 end])/2;
reconstructed_spectrum_v = abs(fft(reconstructed_v))/record_sample_count;
reconstructed_spectrum_v = 2*reconstructed_spectrum_v(1:record_sample_count/2+1);
reconstructed_spectrum_v([1 end]) = reconstructed_spectrum_v([1 end])/2;

first_image_hz = fs_low_hz-low_tone_hz;
baseband_bin = round(low_tone_hz*record_sample_count/fs_hz)+1;
image_bin = round(first_image_hz*record_sample_count/fs_hz)+1;
assert(abs(original_frequency_hz(baseband_bin)-low_tone_hz) <= comparison_tolerance && ...
    abs(original_frequency_hz(image_bin)-first_image_hz) <= comparison_tolerance, ...
    'Baseband and first-image frequencies must align with the deterministic FFT grid.');
zero_inserted_baseband_amplitude_v = zero_inserted_spectrum_v(baseband_bin);
reconstructed_baseband_amplitude_v = reconstructed_spectrum_v(baseband_bin);
zero_inserted_image_amplitude_v = zero_inserted_spectrum_v(image_bin);
reconstructed_image_amplitude_v = reconstructed_spectrum_v(image_bin);
image_suppression_db = 20*log10(max(zero_inserted_image_amplitude_v, eps)/ ...
    max(reconstructed_image_amplitude_v, eps));

assert(naive_alias_amplitude_v > 0.5*high_tone_amplitude_v, ...
    'The broken decimator must expose the aliased high tone.');
assert(filtered_alias_amplitude_v < 0.25*naive_alias_amplitude_v, ...
    'The anti-alias filter must suppress the tone that cannot fit.');
assert(zero_inserted_image_amplitude_v > 0.1*low_tone_amplitude_v, ...
    'Zero insertion must expose a visible first spectral image.');
assert(reconstructed_image_amplitude_v < 0.25*zero_inserted_image_amplitude_v, ...
    'The reconstruction filter must suppress the first image.');
assert(reconstructed_baseband_amplitude_v > 0.75*low_tone_amplitude_v, ...
    'Interpolation gain must restore most of the retained tone amplitude.');

%% Sweep 1 - change only the high tone across the new Nyquist boundary
sweep_alias_frequency_hz = zeros(size(high_tone_sweep_hz));
sweep_naive_alias_amplitude_v = zeros(size(high_tone_sweep_hz));
sweep_filtered_alias_amplitude_v = zeros(size(high_tone_sweep_hz));
for sweep_index = 1:numel(high_tone_sweep_hz)
    sweep_high_hz = high_tone_sweep_hz(sweep_index);
    sweep_input_v = low_tone_amplitude_v*cos(2*pi*low_tone_hz*t_s + 0.20) + ...
        high_tone_amplitude_v*cos(2*pi*sweep_high_hz*t_s - 0.35);
    sweep_filtered_full_v = zeros(1, record_sample_count+filter_tap_count-1);
    for tap_index = 1:filter_tap_count
        output_indices = tap_index:tap_index+record_sample_count-1;
        sweep_filtered_full_v(output_indices) = sweep_filtered_full_v(output_indices) + ...
            anti_alias_fir(tap_index)*sweep_input_v;
    end
    sweep_filtered_aligned_v = sweep_filtered_full_v(...
        filter_delay_samples+1:filter_delay_samples+record_sample_count);
    sweep_naive_v = sweep_input_v(1:decimation_factor:end);
    sweep_proper_v = sweep_filtered_aligned_v(1:decimation_factor:end);
    sweep_naive_spectrum_v = 2*abs(fft(sweep_naive_v))/low_sample_count;
    sweep_proper_spectrum_v = 2*abs(fft(sweep_proper_v))/low_sample_count;
    sweep_alias_hz = abs(sweep_high_hz - round(sweep_high_hz/fs_low_hz)*fs_low_hz);
    sweep_alias_bin = round(sweep_alias_hz*low_sample_count/fs_low_hz)+1;
    sweep_alias_frequency_hz(sweep_index) = sweep_alias_hz;
    sweep_naive_alias_amplitude_v(sweep_index) = sweep_naive_spectrum_v(sweep_alias_bin);
    sweep_filtered_alias_amplitude_v(sweep_index) = sweep_proper_spectrum_v(sweep_alias_bin);
end

%% Sweep 2 - change only reconstruction FIR length
sweep_image_amplitude_v = zeros(size(reconstruction_tap_sweep));
sweep_baseband_amplitude_v = zeros(size(reconstruction_tap_sweep));
for sweep_index = 1:numel(reconstruction_tap_sweep)
    sweep_tap_count = reconstruction_tap_sweep(sweep_index);
    sweep_delay = (sweep_tap_count-1)/2;
    sweep_centered_index = -sweep_delay:sweep_delay;
    sweep_ideal = zeros(1, sweep_tap_count);
    for tap_index = 1:sweep_tap_count
        centered_index = sweep_centered_index(tap_index);
        if centered_index == 0
            sweep_ideal(tap_index) = 2*anti_alias_cutoff_hz/fs_hz;
        else
            sweep_ideal(tap_index) = ...
                sin(2*pi*anti_alias_cutoff_hz*centered_index/fs_hz)/(pi*centered_index);
        end
    end
    sweep_window = 0.54 - 0.46*cos(2*pi*(0:sweep_tap_count-1)/(sweep_tap_count-1));
    sweep_reconstruction_fir = decimation_factor*sweep_ideal.*sweep_window;
    sweep_reconstruction_fir = sweep_reconstruction_fir/ ...
        sum(sweep_ideal.*sweep_window);
    sweep_output_full_v = zeros(1, record_sample_count+sweep_tap_count-1);
    for tap_index = 1:sweep_tap_count
        output_indices = tap_index:tap_index+record_sample_count-1;
        sweep_output_full_v(output_indices) = sweep_output_full_v(output_indices) + ...
            sweep_reconstruction_fir(tap_index)*zero_inserted_v;
    end
    sweep_output_v = sweep_output_full_v(...
        sweep_delay+1:sweep_delay+record_sample_count);
    sweep_output_spectrum_v = 2*abs(fft(sweep_output_v))/record_sample_count;
    sweep_baseband_amplitude_v(sweep_index) = sweep_output_spectrum_v(baseband_bin);
    sweep_image_amplitude_v(sweep_index) = sweep_output_spectrum_v(image_bin);
end

%% Purposeful figures - replace only figures from a prior P10 run
old_figures = findall(groot, 'Type', 'figure', 'Tag', 'P10');
delete(old_figures);
time_view_samples = min(record_sample_count, floor(time_view_ms*fs_hz/1000)+1);
time_view_low_samples = min(low_sample_count, floor(time_view_ms*fs_low_hz/1000)+1);

figure('Name', 'P10 baseline decimation', 'Tag', 'P10');
subplot(2, 2, 1);
plot(1000*t_s(1:time_view_samples), x_v(1:time_view_samples), 'Color', [0.2 0.2 0.2]);
grid on; xlabel('Time (ms)'); ylabel('Amplitude (V)');
title('Original two-tone samples');
subplot(2, 2, 2);
plot(original_frequency_hz, 20*log10(max(original_spectrum_v, 10^(plot_floor_db/20))));
grid on; xlim([0 fs_hz/2]); ylim([plot_floor_db 5]);
xlabel('Frequency (Hz)'); ylabel('Amplitude (dBV)');
title('Original spectrum');
subplot(2, 2, 3);
plot(1000*t_low_s(1:time_view_low_samples), decimated_naive_v(1:time_view_low_samples), 'r.-'); hold on;
plot(1000*t_low_s(1:time_view_low_samples), decimated_filtered_v(1:time_view_low_samples), 'b.-'); hold off;
grid on; xlabel('Time (ms)'); ylabel('Amplitude (V)');
legend('Naive sample dropping', 'Anti-alias then decimate', 'Location', 'best');
title(sprintf('At %.0f samples/s', fs_low_hz));
subplot(2, 2, 4);
plot(low_frequency_hz, 20*log10(max(naive_low_spectrum_v, 10^(plot_floor_db/20))), 'r'); hold on;
plot(low_frequency_hz, 20*log10(max(filtered_low_spectrum_v, 10^(plot_floor_db/20))), 'b');
plot([new_nyquist_hz new_nyquist_hz], [plot_floor_db 5], 'k:');
hold off; grid on; ylim([plot_floor_db 5]);
xlabel('Frequency (Hz)'); ylabel('Amplitude (dBV)');
legend('Naive', 'Filtered', 'New Nyquist', 'Location', 'best');
title(sprintf('%.0f Hz folds to %.0f Hz', high_tone_hz, alias_high_hz));

figure('Name', 'P10 baseline interpolation', 'Tag', 'P10');
subplot(2, 1, 1);
stem(1000*t_s(1:time_view_samples), zero_inserted_v(1:time_view_samples), ...
    'Marker', 'none', 'Color', [0.75 0.25 0.15]); hold on;
plot(1000*t_s(1:time_view_samples), reconstructed_v(1:time_view_samples), 'b'); hold off;
grid on; xlabel('Time (ms)'); ylabel('Amplitude (V)');
legend('Zero inserted', 'Reconstruction filtered', 'Location', 'best');
title('Zeros create gaps; the low-pass fills a band-limited waveform');
subplot(2, 1, 2);
plot(original_frequency_hz, 20*log10(max(zero_inserted_spectrum_v, 10^(plot_floor_db/20))), 'Color', [0.75 0.25 0.15]); hold on;
plot(original_frequency_hz, 20*log10(max(reconstructed_spectrum_v, 10^(plot_floor_db/20))), 'b');
plot([first_image_hz first_image_hz], [plot_floor_db 5], 'k:');
hold off; grid on; xlim([0 fs_hz/2]); ylim([plot_floor_db 5]);
xlabel('Frequency (Hz)'); ylabel('Amplitude (dBV)');
legend('Zero inserted', 'Reconstructed', 'First image', 'Location', 'best');
title(sprintf('Image at %.0f Hz; FIR suppression %.1f dB', first_image_hz, image_suppression_db));

figure('Name', 'P10 high-tone sweep', 'Tag', 'P10');
subplot(2, 1, 1);
plot(high_tone_sweep_hz, sweep_alias_frequency_hz, 'o-', 'LineWidth', 1.2); hold on;
fold_x_limits = [min(high_tone_sweep_hz) max(high_tone_sweep_hz)];
fold_y_limits = [0 new_nyquist_hz];
plot(fold_x_limits, [new_nyquist_hz new_nyquist_hz], 'k:');
plot([new_nyquist_hz new_nyquist_hz], fold_y_limits, 'k:');
hold off; grid on; xlim(fold_x_limits); ylim(fold_y_limits);
xlabel('Original high-tone frequency (Hz)'); ylabel('Observed low-rate frequency (Hz)');
title('Sweep 1: folding begins beyond new Nyquist');
subplot(2, 1, 2);
plot(high_tone_sweep_hz, sweep_naive_alias_amplitude_v, 'ro-', 'LineWidth', 1.2); hold on;
plot(high_tone_sweep_hz, sweep_filtered_alias_amplitude_v, 'bo-', 'LineWidth', 1.2); hold off;
grid on; xlabel('Original high-tone frequency (Hz)'); ylabel('Fold-component amplitude (V)');
legend('Naive sample dropping', 'Fixed anti-alias FIR', 'Location', 'best');
title('Filter removes content that will not fit');

figure('Name', 'P10 reconstruction sweep', 'Tag', 'P10');
subplot(2, 1, 1);
plot(reconstruction_tap_sweep, 20*log10(max(sweep_image_amplitude_v, eps)), 'o-', 'LineWidth', 1.2);
grid on; xlabel('Reconstruction FIR taps'); ylabel('First-image amplitude (dBV)');
title('Sweep 2: more taps sharpen image rejection');
subplot(2, 1, 2);
plot(reconstruction_tap_sweep, sweep_baseband_amplitude_v, 'o-', 'LineWidth', 1.2); hold on;
baseband_x_limits = [min(reconstruction_tap_sweep) max(reconstruction_tap_sweep)];
plot(baseband_x_limits, [low_tone_amplitude_v low_tone_amplitude_v], 'k:');
hold off; grid on; xlim(baseband_x_limits);
xlabel('Reconstruction FIR taps'); ylabel('Recovered 90 Hz amplitude (V)');
title('Interpolation gain restores the retained tone');

figure('Name', 'P10 broken case and recovery', 'Tag', 'P10');
subplot(2, 1, 1);
plot(low_frequency_hz, 20*log10(max(naive_low_spectrum_v, 10^(plot_floor_db/20))), 'r'); hold on;
plot(low_frequency_hz, 20*log10(max(filtered_low_spectrum_v, 10^(plot_floor_db/20))), 'b'); hold off;
grid on; ylim([plot_floor_db 5]); xlabel('Low-rate frequency (Hz)'); ylabel('Amplitude (dBV)');
legend('Broken: drop samples', 'Recovery: prefilter', 'Location', 'best');
title(sprintf('Decimation artifact at %.0f Hz', alias_high_hz));
subplot(2, 1, 2);
plot(original_frequency_hz, 20*log10(max(zero_inserted_spectrum_v, 10^(plot_floor_db/20))), 'r'); hold on;
plot(original_frequency_hz, 20*log10(max(reconstructed_spectrum_v, 10^(plot_floor_db/20))), 'b'); hold off;
grid on; xlim([0 fs_hz/2]); ylim([plot_floor_db 5]);
xlabel('Original-rate frequency (Hz)'); ylabel('Amplitude (dBV)');
legend('Broken: zero insertion only', 'Recovery: reconstruction FIR', 'Location', 'best');
title('Interpolation images are new copies, not new information');

%% Retained workspace metrics and concise console report
results = struct();
results.random_seed = random_seed;
results.fs_original_hz = fs_hz;
results.fs_low_hz = fs_low_hz;
results.new_nyquist_hz = new_nyquist_hz;
results.alias_high_hz = alias_high_hz;
results.naive_alias_amplitude_v = naive_alias_amplitude_v;
results.filtered_alias_amplitude_v = filtered_alias_amplitude_v;
results.anti_alias_suppression_db = anti_alias_suppression_db;
results.first_image_hz = first_image_hz;
results.zero_inserted_baseband_amplitude_v = zero_inserted_baseband_amplitude_v;
results.reconstructed_baseband_amplitude_v = reconstructed_baseband_amplitude_v;
results.zero_inserted_image_amplitude_v = zero_inserted_image_amplitude_v;
results.reconstructed_image_amplitude_v = reconstructed_image_amplitude_v;
results.image_suppression_db = image_suppression_db;
results.high_tone_sweep_hz = high_tone_sweep_hz;
results.sweep_alias_frequency_hz = sweep_alias_frequency_hz;
results.sweep_naive_alias_amplitude_v = sweep_naive_alias_amplitude_v;
results.sweep_filtered_alias_amplitude_v = sweep_filtered_alias_amplitude_v;
results.reconstruction_tap_sweep = reconstruction_tap_sweep;
results.sweep_image_amplitude_v = sweep_image_amplitude_v;
results.sweep_baseband_amplitude_v = sweep_baseband_amplitude_v;
results.comparison_tolerance = comparison_tolerance;

fprintf('Original Fs %.0f samples/s; decimated Fs %.0f samples/s; new Nyquist %.0f Hz.\n', ...
    fs_hz, fs_low_hz, new_nyquist_hz);
fprintf('Broken decimation: %.0f Hz appears at %.0f Hz with amplitude %.3f V.\n', ...
    high_tone_hz, alias_high_hz, naive_alias_amplitude_v);
fprintf('Anti-alias FIR reduces that component by %.1f dB before sample dropping.\n', ...
    anti_alias_suppression_db);
fprintf('Zero insertion places the first 90 Hz image at %.0f Hz.\n', first_image_hz);
fprintf('Reconstruction FIR suppresses that image by %.1f dB and restores %.3f V at 90 Hz.\n', ...
    image_suppression_db, reconstructed_baseband_amplitude_v);

% Recovery/cancellation/isolation: if a foreground graphics call is blocked,
% Ctrl+C and rerun after restoring valid controls. The private stream makes the
% rerun repeatable. Only figures tagged P10 are replaced; no file is written.
