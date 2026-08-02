%% P12: Separate Leakage from Noise
% Guiding question: Why does a perfectly clean tone spread across many FFT bins?
% Learning dependency: P11 finite-record FFT bins and bin spacing.
% Base MATLAB only. Every window equation is visible before fft is used.

%% Visible controls
random_seed = 1012;
fs_hz = 1024;
record_sample_count = 128;
tone_bin = 17;                     % Zero-based DFT bin number.
tone_bin_offset = 0.35;            % Noncoherent fraction of one bin.
tone_amplitude_v = 1.0;
tone_phase_rad = 0.25;
noise_rms_v = 0.02;
window_names = {'Rectangular', 'Hann', 'Hamming', 'Blackman', 'Flat-top'};
offset_sweep_bins = [0 0.20 0.35 0.50];
display_fft_count = 8192;          % Dense display grid, not added resolution.
display_floor_db = -120;

% Fixed ceilings keep every rerun finite and cancellable with Ctrl+C.
max_record_samples = 512;
max_display_fft_count = 16384;
max_window_cases = 5;
max_sweep_cases = 8;
max_figure_groups = 4;

%% Validate controls before random, signal, FFT, or figure allocation
assert(isnumeric(random_seed) && isscalar(random_seed) && isreal(random_seed) && ...
    ~islogical(random_seed) && isfinite(random_seed) && random_seed >= 0 && ...
    random_seed <= 2^32 - 1 && random_seed == floor(random_seed), ...
    'random_seed must be an integer from 0 through 2^32-1.');
assert(isnumeric(fs_hz) && isscalar(fs_hz) && isreal(fs_hz) && ...
    ~islogical(fs_hz) && isfinite(fs_hz) && fs_hz > 0, ...
    'fs_hz must be finite, positive, and real.');
assert(isnumeric(record_sample_count) && isscalar(record_sample_count) && ...
    isreal(record_sample_count) && ~islogical(record_sample_count) && ...
    isfinite(record_sample_count) && record_sample_count >= 32 && ...
    record_sample_count == floor(record_sample_count) && ...
    mod(record_sample_count, 2) == 0, ...
    'record_sample_count must be an even integer of at least 32.');
assert(isnumeric(tone_bin) && isscalar(tone_bin) && isreal(tone_bin) && ...
    ~islogical(tone_bin) && isfinite(tone_bin) && tone_bin >= 1 && ...
    tone_bin == floor(tone_bin) && tone_bin < record_sample_count/2 - 1, ...
    'tone_bin must be an integer safely between DC and Nyquist.');
assert(isnumeric(tone_bin_offset) && isscalar(tone_bin_offset) && ...
    isreal(tone_bin_offset) && ~islogical(tone_bin_offset) && ...
    isfinite(tone_bin_offset) && tone_bin_offset > 0 && ...
    tone_bin_offset <= 0.5, ...
    'tone_bin_offset must be nonzero and no greater than one-half bin.');
assert(isnumeric(tone_amplitude_v) && isscalar(tone_amplitude_v) && ...
    isreal(tone_amplitude_v) && isfinite(tone_amplitude_v) && ...
    tone_amplitude_v > 0, ...
    'tone_amplitude_v must be finite, positive, and real.');
assert(isnumeric(tone_phase_rad) && isscalar(tone_phase_rad) && ...
    isreal(tone_phase_rad) && isfinite(tone_phase_rad), ...
    'tone_phase_rad must be finite and real.');
assert(isnumeric(noise_rms_v) && isscalar(noise_rms_v) && ...
    isreal(noise_rms_v) && isfinite(noise_rms_v) && noise_rms_v > 0 && ...
    noise_rms_v <= 0.20*tone_amplitude_v, ...
    'noise_rms_v must be positive and at most 20 percent of tone amplitude.');
assert(iscell(window_names) && numel(window_names) == 5 && ...
    isequal(window_names, ...
    {'Rectangular', 'Hann', 'Hamming', 'Blackman', 'Flat-top'}), ...
    'window_names must contain the five canonical windows in order.');
assert(isnumeric(offset_sweep_bins) && isvector(offset_sweep_bins) && ...
    isreal(offset_sweep_bins) && all(isfinite(offset_sweep_bins)) && ...
    numel(offset_sweep_bins) >= 3 && all(diff(offset_sweep_bins) > 0) && ...
    offset_sweep_bins(1) == 0 && offset_sweep_bins(end) == 0.5, ...
    'offset_sweep_bins must increase uniquely from 0 through 0.5.');
assert(isnumeric(display_fft_count) && isscalar(display_fft_count) && ...
    isreal(display_fft_count) && ~islogical(display_fft_count) && ...
    isfinite(display_fft_count) && display_fft_count >= record_sample_count && ...
    display_fft_count == floor(display_fft_count) && ...
    mod(display_fft_count, record_sample_count) == 0, ...
    'display_fft_count must be an integer multiple of record_sample_count.');
assert(isnumeric(display_floor_db) && isscalar(display_floor_db) && ...
    isreal(display_floor_db) && isfinite(display_floor_db) && ...
    display_floor_db <= -60 && display_floor_db >= -180, ...
    'display_floor_db must lie from -180 through -60 dB.');
assert(max_record_samples == 512 && max_display_fft_count == 16384 && ...
    max_window_cases == 5 && max_sweep_cases == 8 && ...
    max_figure_groups == 4, ...
    'P12 resource ceilings must remain fixed.');
assert(record_sample_count <= max_record_samples && ...
    display_fft_count <= max_display_fft_count, ...
    'Record or display FFT exceeds the P12 resource ceiling.');
assert(numel(window_names) <= max_window_cases && ...
    numel(offset_sweep_bins) <= max_sweep_cases, ...
    'A P12 sweep exceeds its case ceiling.');
assert((tone_bin + max(offset_sweep_bins))*fs_hz/record_sample_count < fs_hz/2, ...
    'The offset sweep must keep the tone below Nyquist.');

%% Deterministic baseline: clean off-bin tone and separate seeded noise
sample_index = 0:(record_sample_count - 1);
time_s = sample_index/fs_hz;
record_duration_s = record_sample_count/fs_hz;
bin_spacing_hz = fs_hz/record_sample_count;
tone_frequency_hz = (tone_bin + tone_bin_offset)*bin_spacing_hz;

clean_tone_v = tone_amplitude_v*exp(1j*( ...
    2*pi*tone_frequency_hz*time_s + tone_phase_rad));
stream = RandStream('mt19937ar', 'Seed', random_seed);
complex_noise_v = noise_rms_v/sqrt(2)*( ...
    randn(stream, 1, record_sample_count) + ...
    1j*randn(stream, 1, record_sample_count));
noisy_tone_v = clean_tone_v + complex_noise_v;
noise_rms_realized_v = sqrt(mean(abs(complex_noise_v).^2));

% A repeated finite record joins sample N back to sample 0. For a
% noninteger number of cycles, that artificial boundary has a phase jump.
record_wrap_jump_v = abs(tone_amplitude_v*exp(1j*( ...
    2*pi*tone_frequency_hz*record_duration_s + tone_phase_rad)) - ...
    tone_amplitude_v*exp(1j*tone_phase_rad));

dense_frequency_hz = (-display_fft_count/2:(display_fft_count/2 - 1))* ...
    fs_hz/display_fft_count;
rectangular_window = ones(1, record_sample_count);
rectangular_coherent_gain = sum(rectangular_window)/record_sample_count;
baseline_clean_magnitude_v = abs(fftshift(fft( ...
    clean_tone_v.*rectangular_window, display_fft_count)))/ ...
    (record_sample_count*rectangular_coherent_gain);
baseline_noisy_magnitude_v = abs(fftshift(fft( ...
    noisy_tone_v.*rectangular_window, display_fft_count)))/ ...
    (record_sample_count*rectangular_coherent_gain);
baseline_clean_db = 20*log10(max( ...
    baseline_clean_magnitude_v/tone_amplitude_v, 10^(display_floor_db/20)));
baseline_noisy_db = 20*log10(max( ...
    baseline_noisy_magnitude_v/tone_amplitude_v, 10^(display_floor_db/20)));

assert(record_wrap_jump_v > 0.5*tone_amplitude_v, ...
    'The noncoherent baseline must expose a visible record-boundary jump.');

%% Sweep 1: change only the window for one clean tone and record
window_case_count = numel(window_names);
window_samples = zeros(window_case_count, record_sample_count);
window_spectrum_db = zeros(window_case_count, display_fft_count);
coherent_gain = zeros(1, window_case_count);
peak_amplitude_error_db = zeros(1, window_case_count);
main_lobe_3db_width_hz = zeros(1, window_case_count);
main_lobe_3db_width_bins = zeros(1, window_case_count);
maximum_sidelobe_db_c = zeros(1, window_case_count);
first_null_half_width_bins = [1 2 2 3 5];

for window_index = 1:window_case_count
    n = sample_index;
    if window_index == 1
        window = ones(1, record_sample_count);
    elseif window_index == 2
        window = 0.5 - 0.5*cos(2*pi*n/record_sample_count);
    elseif window_index == 3
        window = 0.54 - 0.46*cos(2*pi*n/record_sample_count);
    elseif window_index == 4
        window = 0.42 - 0.50*cos(2*pi*n/record_sample_count) + ...
            0.08*cos(4*pi*n/record_sample_count);
    else
        % Five-term flat-top window, written explicitly instead of flattopwin.
        window = 0.21557895 - 0.41663158*cos(2*pi*n/record_sample_count) + ...
            0.277263158*cos(4*pi*n/record_sample_count) - ...
            0.083578947*cos(6*pi*n/record_sample_count) + ...
            0.006947368*cos(8*pi*n/record_sample_count);
    end

    window_samples(window_index, :) = window;
    coherent_gain(window_index) = sum(window)/record_sample_count;
    bin_magnitude_v = abs(fft(clean_tone_v.*window))/ ...
        (record_sample_count*coherent_gain(window_index));
    normalized_magnitude_v = abs(fftshift(fft( ...
        clean_tone_v.*window, display_fft_count)))/ ...
        (record_sample_count*coherent_gain(window_index));
    [peak_magnitude_v, peak_index] = max(normalized_magnitude_v);
    window_spectrum_db(window_index, :) = 20*log10(max( ...
        normalized_magnitude_v/peak_magnitude_v, 10^(display_floor_db/20)));
    peak_amplitude_error_db(window_index) = ...
        20*log10(max(bin_magnitude_v)/tone_amplitude_v);

    % The DFT frequency axis is circular. Triplication keeps both half-power
    % crossings adjacent even when a valid main lobe wraps at Nyquist.
    half_power_v = peak_magnitude_v/sqrt(2);
    circular_magnitude_v = [normalized_magnitude_v normalized_magnitude_v ...
        normalized_magnitude_v];
    circular_peak_index = peak_index + display_fft_count;
    left_below = find(circular_magnitude_v(1:circular_peak_index) < half_power_v);
    right_below = find(circular_magnitude_v(circular_peak_index:end) < ...
        half_power_v, 1);
    assert(~isempty(left_below) && ~isempty(right_below), ...
        'The circular display grid must contain both half-power crossings.');
    left_index = left_below(end) + 1;
    right_index = circular_peak_index + right_below(1) - 2;
    main_lobe_3db_width_hz(window_index) = ...
        (right_index - left_index)*fs_hz/display_fft_count;
    main_lobe_3db_width_bins(window_index) = ...
        main_lobe_3db_width_hz(window_index)/bin_spacing_hz;

    wrapped_frequency_offset_hz = mod(dense_frequency_hz - tone_frequency_hz + ...
        fs_hz/2, fs_hz) - fs_hz/2;
    outside_main_lobe = abs(wrapped_frequency_offset_hz) >= ...
        first_null_half_width_bins(window_index)*bin_spacing_hz;
    maximum_sidelobe_db_c(window_index) = ...
        max(window_spectrum_db(window_index, outside_main_lobe));
end

assert(maximum_sidelobe_db_c(1) < -10 && ...
    maximum_sidelobe_db_c(1) > -16, ...
    'The rectangular first sidelobe should be about -13 dBc.');
assert(maximum_sidelobe_db_c(2) < maximum_sidelobe_db_c(1) - 15, ...
    'Hann sidelobes must be lower than rectangular sidelobes.');
assert(maximum_sidelobe_db_c(4) < maximum_sidelobe_db_c(2) - 20, ...
    'Blackman sidelobes must be lower than Hann sidelobes.');
assert(main_lobe_3db_width_bins(2) > main_lobe_3db_width_bins(1), ...
    'Hann must trade a wider main lobe for lower sidelobes.');
assert(abs(peak_amplitude_error_db(5)) < abs(peak_amplitude_error_db(1)), ...
    'Flat-top must reduce off-bin peak-amplitude error versus rectangular.');

%% Sweep 2: change only fractional-bin offset with a rectangular window
offset_case_count = numel(offset_sweep_bins);
offset_spectrum_db = zeros(offset_case_count, display_fft_count);
offset_off_peak_energy_fraction = zeros(1, offset_case_count);
offset_wrap_jump_v = zeros(1, offset_case_count);

for sweep_index = 1:offset_case_count
    sweep_offset_bins = offset_sweep_bins(sweep_index);
    sweep_frequency_hz = (tone_bin + sweep_offset_bins)*bin_spacing_hz;
    sweep_tone_v = tone_amplitude_v*exp(1j*( ...
        2*pi*sweep_frequency_hz*time_s + tone_phase_rad));
    sweep_dft_v = fft(sweep_tone_v)/record_sample_count;
    sweep_energy_v2 = abs(sweep_dft_v).^2;
    offset_off_peak_energy_fraction(sweep_index) = ...
        1 - max(sweep_energy_v2)/sum(sweep_energy_v2);
    offset_wrap_jump_v(sweep_index) = abs(tone_amplitude_v*exp(1j*( ...
        2*pi*sweep_frequency_hz*record_duration_s + tone_phase_rad)) - ...
        tone_amplitude_v*exp(1j*tone_phase_rad));
    sweep_dense_magnitude_v = abs(fftshift(fft( ...
        sweep_tone_v, display_fft_count)))/record_sample_count;
    offset_spectrum_db(sweep_index, :) = 20*log10(max( ...
        sweep_dense_magnitude_v/tone_amplitude_v, 10^(display_floor_db/20)));
end

assert(offset_off_peak_energy_fraction(1) < 1e-20 && ...
    offset_wrap_jump_v(1) < 1e-10, ...
    'An exact-bin tone must reach the coherent no-leakage limiting case.');
assert(offset_off_peak_energy_fraction(end) > 0.50 && ...
    offset_wrap_jump_v(end) > tone_amplitude_v, ...
    'The half-bin case must spread substantial energy outside one peak bin.');

%% Broken case: call every nonpeak clean-tone bin "noise"
% Parseval scaling makes this a plausible but wrong RMS estimate. The input
% is noiseless, so every nonpeak term is deterministic leakage.
clean_rectangular_dft_v = fft(clean_tone_v)/record_sample_count;
clean_bin_energy_v2 = abs(clean_rectangular_dft_v).^2;
broken_noise_rms_v = sqrt(sum(clean_bin_energy_v2) - max(clean_bin_energy_v2));
true_clean_noise_rms_v = 0;

% Recovery in this controlled synthetic lab uses the known clean component.
% By linearity, noisy spectrum minus clean spectrum contains noise only.
recovered_noise_time_v = noisy_tone_v - clean_tone_v;
recovered_noise_spectrum_v = fft(noisy_tone_v)/record_sample_count - ...
    clean_rectangular_dft_v;
recovered_noise_rms_v = sqrt(sum(abs(recovered_noise_spectrum_v).^2));

assert(broken_noise_rms_v > 10*noise_rms_v, ...
    'The broken estimator must visibly confuse leakage with noise.');
assert(abs(recovered_noise_rms_v - noise_rms_realized_v) < 1e-12 && ...
    max(abs(recovered_noise_time_v - complex_noise_v)) < 1e-12, ...
    'Recovery must isolate the exact seeded noise realization.');

%% Retained workspace metrics
results.question = 'Why does a perfectly clean tone spread across many FFT bins?';
results.random_seed = random_seed;
results.fs_hz = fs_hz;
results.record_sample_count = record_sample_count;
results.record_duration_s = record_duration_s;
results.bin_spacing_hz = bin_spacing_hz;
results.tone_frequency_hz = tone_frequency_hz;
results.record_wrap_jump_v = record_wrap_jump_v;
results.noise_rms_requested_v = noise_rms_v;
results.noise_rms_realized_v = noise_rms_realized_v;
results.window_names = window_names;
results.coherent_gain = coherent_gain;
results.peak_amplitude_error_db = peak_amplitude_error_db;
results.main_lobe_3db_width_hz = main_lobe_3db_width_hz;
results.main_lobe_3db_width_bins = main_lobe_3db_width_bins;
results.maximum_sidelobe_db_c = maximum_sidelobe_db_c;
results.offset_sweep_bins = offset_sweep_bins;
results.offset_off_peak_energy_fraction = offset_off_peak_energy_fraction;
results.offset_wrap_jump_v = offset_wrap_jump_v;
results.true_clean_noise_rms_v = true_clean_noise_rms_v;
results.broken_noise_rms_v = broken_noise_rms_v;
results.recovered_noise_rms_v = recovered_noise_rms_v;

%% Purposeful figures (replace only figures created by P12)
old_figures = findall(0, 'Type', 'figure', 'Tag', 'P12');
if ~isempty(old_figures)
    close(old_figures);
end

figure('Name', 'P12 clean leakage versus noise', 'Tag', 'P12');
subplot(2, 1, 1);
plot(1000*(0:record_sample_count)/fs_hz, ...
    real([clean_tone_v clean_tone_v(1)]), 'LineWidth', 1.1);
grid on;
xlabel('Time in repeated record (ms)');
ylabel('In-phase amplitude (V)');
title(sprintf('Finite record joins back with %.3f V boundary jump', record_wrap_jump_v));
subplot(2, 1, 2);
plot(dense_frequency_hz, baseline_clean_db, 'LineWidth', 1.2);
hold on;
plot(dense_frequency_hz, baseline_noisy_db, 'LineWidth', 0.9);
hold off;
grid on;
xlim([tone_frequency_hz - 12*bin_spacing_hz, ...
    tone_frequency_hz + 12*bin_spacing_hz]);
ylim([display_floor_db 5]);
xlabel('Frequency (Hz)');
ylabel('Magnitude relative to tone (dB)');
legend('Perfectly clean tone', 'Same tone plus seeded noise', 'Location', 'best');
title('Leakage is structured; noise raises an irregular floor');

figure('Name', 'P12 window sweep', 'Tag', 'P12');
for window_index = 1:window_case_count
    plot(dense_frequency_hz, window_spectrum_db(window_index, :), ...
        'LineWidth', 1.1);
    hold on;
end
hold off;
grid on;
xlim([tone_frequency_hz - 12*bin_spacing_hz, ...
    tone_frequency_hz + 12*bin_spacing_hz]);
ylim([display_floor_db 5]);
xlabel('Frequency (Hz)');
ylabel('Magnitude relative to each peak (dBc)');
legend(window_names, 'Location', 'best');
title('Sweep 1: same clean tone and record; only the window changes');

figure('Name', 'P12 window metrics', 'Tag', 'P12');
subplot(3, 1, 1);
bar(main_lobe_3db_width_hz);
set(gca, 'XTick', 1:window_case_count, 'XTickLabel', window_names);
ylabel('-3 dB width (Hz)');
grid on;
title('Resolution cost');
subplot(3, 1, 2);
bar(peak_amplitude_error_db);
set(gca, 'XTick', 1:window_case_count, 'XTickLabel', window_names);
ylabel('Peak error (dB)');
grid on;
title('Off-bin amplitude accuracy after coherent-gain correction');
subplot(3, 1, 3);
bar(maximum_sidelobe_db_c);
set(gca, 'XTick', 1:window_case_count, 'XTickLabel', window_names);
ylabel('Max sidelobe (dBc)');
grid on;
title('Weak-near-strong visibility');

figure('Name', 'P12 offset sweep and broken noise estimate', 'Tag', 'P12');
subplot(2, 1, 1);
for sweep_index = 1:offset_case_count
    plot(dense_frequency_hz, offset_spectrum_db(sweep_index, :), ...
        'LineWidth', 1.0);
    hold on;
end
hold off;
grid on;
xlim([(tone_bin - 4)*bin_spacing_hz, (tone_bin + 5)*bin_spacing_hz]);
ylim([display_floor_db 5]);
xlabel('Frequency (Hz)');
ylabel('Magnitude relative to tone (dB)');
legend('0 bin', '0.20 bin', '0.35 bin', '0.50 bin', 'Location', 'best');
title('Sweep 2: only fractional-bin offset changes');
subplot(2, 1, 2);
bar([true_clean_noise_rms_v broken_noise_rms_v ...
    noise_rms_realized_v recovered_noise_rms_v]);
set(gca, 'XTick', 1:4, 'XTickLabel', ...
    {'True clean', 'Broken off-peak', 'Injected noise', 'Recovered'});
ylabel('RMS amplitude (V)');
grid on;
title('Broken case: off-peak energy is not automatically noise');

fprintf('P12 baseline: %.2f Hz tone = bin %.2f, record jump %.3f V.\n', ...
    tone_frequency_hz, tone_bin + tone_bin_offset, record_wrap_jump_v);
for window_index = 1:window_case_count
    fprintf('%-11s: width %.2f Hz, peak error %+.3f dB, sidelobe %.1f dBc.\n', ...
        window_names{window_index}, main_lobe_3db_width_hz(window_index), ...
        peak_amplitude_error_db(window_index), maximum_sidelobe_db_c(window_index));
end
fprintf('Broken noise estimate %.3f V; actual/recovered seeded noise %.3f/%.3f V.\n', ...
    broken_noise_rms_v, noise_rms_realized_v, recovered_noise_rms_v);
