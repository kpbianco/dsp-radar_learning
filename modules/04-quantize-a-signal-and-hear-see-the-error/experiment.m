%% P04 - Quantize a Signal and Hear/See the Error
% Guiding question:
% How do ADC bit depth and full-scale range change the measurement?
%
% Dependency contract: P03 and base MATLAB only. No toolbox is required.
clear;
close all;
clc;
random_seed = 404;
rng(random_seed, 'twister');

%% Baseline controls - change one of these at a time
A = 0.9;                         % sinusoid peak amplitude (V)
f0 = 128;                        % sinusoid frequency (Hz)
phi = pi/7;                      % sinusoid phase (rad)
fs = 4096;                       % sample rate (samples/s)
duration = 0.25;                 % record duration (s)
bits_baseline = 6;               % baseline ADC resolution (bits)
full_scale = 1.0;                % bipolar ADC input limit +/- full_scale (V)
max_samples = 16384;             % resource ceiling for any record
max_sweep_cases = 8;             % resource ceiling for an edited sweep
max_bits = 16;                   % resource ceiling for ADC code levels

% Fail before allocation if an edited control is malformed or ambiguous.
assert(isscalar(A) && isnumeric(A) && ~islogical(A) && ...
    isreal(A) && isfinite(A) && A > 0, ...
    'A must be one finite positive real amplitude in volts.');
assert(isscalar(f0) && isnumeric(f0) && ~islogical(f0) && ...
    isreal(f0) && isfinite(f0) && f0 > 0, ...
    'f0 must be one finite positive real frequency in hertz.');
assert(isscalar(phi) && isnumeric(phi) && ~islogical(phi) && ...
    isreal(phi) && isfinite(phi), ...
    'phi must be one finite real phase in radians.');
assert(isscalar(fs) && isnumeric(fs) && ~islogical(fs) && ...
    isreal(fs) && isfinite(fs) && fs > 2*f0, ...
    'fs must be finite, real, and greater than 2*f0.');
assert(isscalar(duration) && isnumeric(duration) && ~islogical(duration) && ...
    isreal(duration) && isfinite(duration) && duration > 0, ...
    'duration must be one finite positive real value in seconds.');
assert(isscalar(full_scale) && isnumeric(full_scale) && ...
    ~islogical(full_scale) && isreal(full_scale) && ...
    isfinite(full_scale) && full_scale > 0, ...
    'full_scale must be one finite positive real voltage.');
assert(A < full_scale, ...
    'The baseline requires A < full_scale so it demonstrates quantization without clipping.');
assert(isscalar(bits_baseline) && isnumeric(bits_baseline) && ...
    ~islogical(bits_baseline) && isreal(bits_baseline) && ...
    isfinite(bits_baseline) && bits_baseline == floor(bits_baseline) && ...
    bits_baseline >= 2 && bits_baseline <= max_bits, ...
    'bits_baseline must be an integer from 2 through max_bits.');

sample_count = round(duration*fs);
assert(sample_count >= 16 && ...
    abs(sample_count-duration*fs) < 10*eps(max(1, duration*fs)), ...
    'duration*fs must be an integer record of at least 16 samples.');
assert(sample_count <= max_samples, ...
    'A record is limited to 16384 samples; reduce fs or duration.');
assert(mod(sample_count, 2) == 0, ...
    'Use an even sample count so the one-sided spectrum includes Nyquist exactly.');
assert(abs(f0*duration-round(f0*duration)) < ...
    10*eps(max(1, f0*duration)), ...
    'Choose duration so the tone completes an integer number of cycles.');

n = 0:sample_count-1;
t = n/fs;
x = A*cos(2*pi*f0*t + phi);

%% Baseline - explicit bipolar mid-rise quantizer
% The ADC accepts inputs from -full_scale through +full_scale and has
% level_count = 2^bits_baseline reconstruction levels. Its step is
% delta = 2*full_scale/level_count. Each input is first limited, assigned a
% code by floor((x + full_scale)/delta), bounded to a valid code, and mapped
% to the center of that code bin. No helper or quantizer toolbox call is used.
level_count = 2^bits_baseline;
delta = 2*full_scale/level_count;
baseline_clipped = x < -full_scale | x > full_scale;
x_limited = min(max(x, -full_scale), full_scale);
code = floor((x_limited + full_scale)/delta);
code = min(max(code, 0), level_count-1);
x_quantized = -full_scale + (code+0.5)*delta;
quantization_error = x_quantized-x;
baseline_clip_count = sum(baseline_clipped);
signal_rms = sqrt(mean(x.^2));
error_rms = sqrt(mean(quantization_error.^2));
measured_snr_db = 20*log10(signal_rms/error_rms);
ideal_full_scale_sine_sqnr_db = 6.02*bits_baseline + 1.76;
baseline_error_bound = delta/2 + 16*eps(full_scale);
assert(baseline_clip_count == 0, ...
    'The baseline must not clip; restore A below full_scale.');
assert(max(abs(quantization_error)) <= baseline_error_bound, ...
    'A non-clipping mid-rise quantizer must stay within half an LSB.');

view_sample_count = min(96, sample_count);
view = 1:view_sample_count;
figure('Name', 'P04 baseline: samples become voltage bins');
subplot(2,1,1);
plot(t(view), x(view), 'LineWidth', 1.2, ...
    'DisplayName', 'input samples');
hold on;
stairs(t(view), x_quantized(view), 'LineWidth', 1.2, ...
    'DisplayName', sprintf('%d-bit ADC output', bits_baseline));
grid on;
xlabel('Time (s)');
ylabel('Voltage (V)');
title(sprintf('One of %d levels replaces each input voltage', level_count));
legend('Location', 'best');

subplot(2,1,2);
stem(n(view), quantization_error(view), 'filled');
hold on;
plot(n(view), (delta/2)*ones(size(view)), ':', ...
    'DisplayName', '+0.5 LSB');
plot(n(view), -(delta/2)*ones(size(view)), ':', ...
    'DisplayName', '-0.5 LSB');
grid on;
xlabel('Sample index n (samples)');
ylabel('Quantization error x_q-x (V)');
title('Without clipping, mid-rise error remains inside half an LSB');

% The DFT operation is E[k] = sum_n e[n]*exp(-j*2*pi*k*n/N).
% Base MATLAB fft evaluates that sum efficiently. The one-sided magnitude is
% normalized by sample_count and referenced to full_scale in dBFS.
error_fft = fft(quantization_error);
one_sided_bins = 0:sample_count/2;
frequency_hz = one_sided_bins*fs/sample_count;
error_magnitude = abs(error_fft(1:sample_count/2+1))/sample_count;
error_magnitude(2:end-1) = 2*error_magnitude(2:end-1);
spectrum_floor = 1e-12;
error_dbfs = 20*log10(max(error_magnitude/full_scale, spectrum_floor));

figure('Name', 'P04 baseline: deterministic error spectrum');
plot(frequency_hz, error_dbfs, 'LineWidth', 1.1);
grid on;
xlabel('Frequency (Hz)');
ylabel('Error magnitude (dBFS)');
title('A sine can make deterministic, spur-like quantization error');

fprintf('P04 baseline metrics\n');
fprintf('  random seed                    = %d\n', random_seed);
fprintf('  tone/sample rate               = %.1f Hz / %.1f samples/s\n', f0, fs);
fprintf('  ADC range                      = %.3f to +%.3f V\n', -full_scale, full_scale);
fprintf('  bit depth and levels           = %d bits, %d levels\n', ...
    bits_baseline, level_count);
fprintf('  quantization step              = %.9f V/LSB\n', delta);
fprintf('  clipped samples                = %d samples\n', baseline_clip_count);
fprintf('  RMS quantization error         = %.9f V RMS\n', error_rms);
fprintf('  measured signal/error ratio    = %.3f dB\n', measured_snr_db);
fprintf('  ideal full-scale sine SQNR     = %.3f dB (reference only)\n', ...
    ideal_full_scale_sine_sqnr_db);

%% Parameter sweep 1 - change only ADC bit depth
bit_depths = [3 6 10 14];
assert(isvector(bit_depths) && isnumeric(bit_depths) && ...
    ~islogical(bit_depths) && isreal(bit_depths) && ...
    all(isfinite(bit_depths)) && all(bit_depths == floor(bit_depths)) && ...
    all(bit_depths >= 2) && all(bit_depths <= max_bits), ...
    'bit_depths must contain integer bit depths from 2 through max_bits.');
assert(isequal(bit_depths, [3 6 10 14]), ...
    'Keep the canonical comparison at 3, 6, 10, and 14 bits.');
assert(numel(bit_depths) <= max_sweep_cases, ...
    'The bit-depth sweep is limited to eight cases.');

bit_steps_v = zeros(size(bit_depths));
bit_error_rms_v = zeros(size(bit_depths));
bit_snr_db = zeros(size(bit_depths));
figure('Name', 'P04 sweep 1: bit depth');
for bit_index = 1:numel(bit_depths)
    bits_case = bit_depths(bit_index);
    levels_case = 2^bits_case;
    delta_case = 2*full_scale/levels_case;
    code_case = floor((x + full_scale)/delta_case);
    code_case = min(max(code_case, 0), levels_case-1);
    xq_case = -full_scale + (code_case+0.5)*delta_case;
    error_case = xq_case-x;
    bit_steps_v(bit_index) = delta_case;
    bit_error_rms_v(bit_index) = sqrt(mean(error_case.^2));
    bit_snr_db(bit_index) = 20*log10(signal_rms/bit_error_rms_v(bit_index));
    assert(max(abs(error_case)) <= delta_case/2 + 16*eps(full_scale), ...
        'Every non-clipping bit-depth case must remain inside half an LSB.');

    subplot(2,2,bit_index);
    stairs(t(view), xq_case(view), 'LineWidth', 1.0);
    hold on;
    plot(t(view), x(view), ':');
    grid on;
    xlabel('Time (s)');
    ylabel('Voltage (V)');
    title(sprintf('%d bits: step %.6f V/LSB', bits_case, delta_case));

    fprintf(['P04 bit sweep: bits = %d, levels = %d, step = %.9f V/LSB, ' ...
        'error RMS = %.9f V, SNR = %.3f dB\n'], ...
        bits_case, levels_case, delta_case, ...
        bit_error_rms_v(bit_index), bit_snr_db(bit_index));
end
assert(all(diff(bit_steps_v) < 0), ...
    'Increasing bit depth must reduce the voltage step.');
assert(all(diff(bit_error_rms_v) < 0), ...
    'The committed coherent tone must show lower RMS error at every higher bit depth.');

figure('Name', 'P04 sweep 1 metrics: resolution buys smaller error');
subplot(2,1,1);
semilogy(bit_depths, bit_error_rms_v, 'o-', 'LineWidth', 1.2);
grid on;
xlabel('ADC bit depth (bits)');
ylabel('Error (V RMS)');
title('More bits shrink the quantization step and RMS error');
subplot(2,1,2);
plot(bit_depths, bit_snr_db, 'o-', 'LineWidth', 1.2);
grid on;
xlabel('ADC bit depth (bits)');
ylabel('Measured signal/error ratio (dB)');
title('Measured SNR rises with bit depth for this non-clipping tone');

%% Parameter sweep 2 - change only the ADC full-scale range
% Keep the baseline samples x unchanged. Choose ADC limits that make the
% same A-volt peak use 90, 25, and 10 percent of the available range.
utilization_fractions = [0.90 0.25 0.10]; % A / ADC full-scale limit
full_scale_settings = A./utilization_fractions;
utilization_bits = 8;
assert(isvector(utilization_fractions) && ...
    isnumeric(utilization_fractions) && ~islogical(utilization_fractions) && ...
    isreal(utilization_fractions) && all(isfinite(utilization_fractions)) && ...
    all(utilization_fractions > 0) && all(utilization_fractions < 1), ...
    'utilization_fractions must contain finite real fractions between zero and one.');
assert(numel(utilization_fractions) >= 2 && ...
    numel(utilization_fractions) <= max_sweep_cases, ...
    'The utilization sweep requires from two through eight cases.');
assert(any(abs(utilization_fractions-0.90) < 10*eps(1)) && ...
    any(abs(utilization_fractions-0.10) < 10*eps(1)), ...
    'Compare a signal using 90 percent and 10 percent of full scale.');
assert(all(isfinite(full_scale_settings)) && ...
    all(full_scale_settings > A) && all(diff(full_scale_settings) > 0), ...
    'The committed ADC ranges must widen while the same input stays in range.');
assert(isscalar(utilization_bits) && isnumeric(utilization_bits) && ...
    ~islogical(utilization_bits) && isreal(utilization_bits) && ...
    isfinite(utilization_bits) && ...
    utilization_bits == floor(utilization_bits) && ...
    utilization_bits >= 2 && utilization_bits <= max_bits, ...
    'utilization_bits must be an integer from 2 through max_bits.');

utilization_levels = 2^utilization_bits;
utilization_steps_v = zeros(size(utilization_fractions));
utilization_error_rms_v = zeros(size(utilization_fractions));
utilization_snr_db = zeros(size(utilization_fractions));
utilization_clip_count = zeros(size(utilization_fractions));
figure('Name', 'P04 sweep 2: ADC full-scale range');
for utilization_index = 1:numel(utilization_fractions)
    utilization_case = utilization_fractions(utilization_index);
    full_scale_case = full_scale_settings(utilization_index);
    delta_case = 2*full_scale_case/utilization_levels;
    clipped_case = x < -full_scale_case | x > full_scale_case;
    limited_case = min(max(x, -full_scale_case), full_scale_case);
    code_case = floor((limited_case + full_scale_case)/delta_case);
    code_case = min(max(code_case, 0), utilization_levels-1);
    xq_case = -full_scale_case + (code_case+0.5)*delta_case;
    error_case = xq_case-x;
    utilization_steps_v(utilization_index) = delta_case;
    utilization_error_rms_v(utilization_index) = sqrt(mean(error_case.^2));
    utilization_snr_db(utilization_index) = ...
        20*log10(signal_rms/utilization_error_rms_v(utilization_index));
    utilization_clip_count(utilization_index) = sum(clipped_case);
    assert(utilization_clip_count(utilization_index) == 0, ...
        'A utilization case below full scale must not clip.');

    subplot(numel(utilization_fractions),1,utilization_index);
    plot(t(view), x(view), 'LineWidth', 1.1, ...
        'DisplayName', 'input');
    hold on;
    stairs(t(view), xq_case(view), 'LineWidth', 1.0, ...
        'DisplayName', '8-bit output');
    grid on;
    xlabel('Time (s)');
    ylabel('Voltage (V)');
    title(sprintf('Same %.3f V peak uses %.0f%% of +/-%0.3f V ADC', ...
        A, 100*utilization_case, full_scale_case));
    legend('Location', 'best');

    fprintf(['P04 full-scale sweep: use = %.0f percent, ADC limit = +/-%0.3f V, ' ...
        'step = %.9f V/LSB, error RMS = %.9f V, SNR = %.3f dB, clips = %d\n'], ...
        100*utilization_case, full_scale_case, delta_case, ...
        utilization_error_rms_v(utilization_index), ...
        utilization_snr_db(utilization_index), ...
        utilization_clip_count(utilization_index));
end
assert(all(diff(utilization_steps_v) > 0), ...
    'Widening the ADC range at fixed bit depth must increase the voltage step.');
utilization_snr_loss_db = utilization_snr_db(1)-utilization_snr_db(end);
expected_utilization_loss_db = ...
    20*log10(utilization_fractions(1)/utilization_fractions(end));
assert(utilization_snr_loss_db > 15, ...
    'The 10-percent case must visibly waste effective signal-to-error ratio.');

figure('Name', 'P04 sweep 2 metrics: unused range wastes effective bits');
semilogx(100*utilization_fractions, utilization_snr_db, 'o-', ...
    'LineWidth', 1.2);
grid on;
xlabel('Input peak / ADC full scale (%)');
ylabel('Measured signal/error ratio (dB)');
title(sprintf('Widening the range from 90%% to 10%% use costs %.1f dB here', ...
    utilization_snr_loss_db));

fprintf('  expected utilization-ratio loss = %.3f dB\n', ...
    expected_utilization_loss_db);
fprintf('  measured utilization loss      = %.3f dB\n', ...
    utilization_snr_loss_db);

%% Optional dither - add seeded TPDF dither before quantization
% The difference of two independent uniform variables is triangular. Its
% peak magnitude is one LSB. Dither trades a higher broadband floor for less
% signal-correlated, spur-like error; it is not an automatic SNR improvement.
dither = delta*(rand(size(x))-rand(size(x)));
x_with_dither = x+dither;
dither_clipped = x_with_dither < -full_scale | x_with_dither > full_scale;
x_dither_limited = min(max(x_with_dither, -full_scale), full_scale);
dither_code = floor((x_dither_limited + full_scale)/delta);
dither_code = min(max(dither_code, 0), level_count-1);
x_quantized_dither = -full_scale + (dither_code+0.5)*delta;
dither_total_error = x_quantized_dither-x;
dither_error_rms = sqrt(mean(dither_total_error.^2));
assert(sum(dither_clipped) == 0, ...
    'The committed dither case must not overload the ADC.');

baseline_error_centered = quantization_error-mean(quantization_error);
dither_error_centered = dither_total_error-mean(dither_total_error);
x_centered = x-mean(x);
baseline_error_correlation = sum(x_centered.*baseline_error_centered) / ...
    sqrt(sum(x_centered.^2)*sum(baseline_error_centered.^2));
dither_error_correlation = sum(x_centered.*dither_error_centered) / ...
    sqrt(sum(x_centered.^2)*sum(dither_error_centered.^2));

dither_error_fft = fft(dither_total_error);
dither_error_magnitude = ...
    abs(dither_error_fft(1:sample_count/2+1))/sample_count;
dither_error_magnitude(2:end-1) = ...
    2*dither_error_magnitude(2:end-1);
dither_error_dbfs = ...
    20*log10(max(dither_error_magnitude/full_scale, spectrum_floor));

figure('Name', 'P04 dither: trade tones for a broader noise floor');
subplot(2,1,1);
plot(n(view), quantization_error(view), 'DisplayName', 'without dither');
hold on;
plot(n(view), dither_total_error(view), ...
    'DisplayName', 'with seeded triangular dither');
grid on;
xlabel('Sample index n (samples)');
ylabel('Total measurement error (V)');
title('Dither changes the repeatable error pattern');
legend('Location', 'best');

subplot(2,1,2);
plot(frequency_hz, error_dbfs, 'DisplayName', 'without dither');
hold on;
plot(frequency_hz, dither_error_dbfs, ...
    'DisplayName', 'with triangular dither');
grid on;
xlabel('Frequency (Hz)');
ylabel('Error magnitude (dBFS)');
title('Dither spreads error energy instead of promising lower RMS error');
legend('Location', 'best');

fprintf('P04 dither metrics\n');
fprintf('  dither support                 = -%.9f to +%.9f V\n', delta, delta);
fprintf('  no-dither error RMS            = %.9f V\n', error_rms);
fprintf('  dithered total-error RMS       = %.9f V\n', dither_error_rms);
fprintf('  no-dither signal/error corr.   = %.6f\n', ...
    baseline_error_correlation);
fprintf('  dithered signal/error corr.    = %.6f\n', ...
    dither_error_correlation);

%% Deliberately broken case - choose too little range and clip
overload_amplitude = 1.35;       % V peak, deliberately above +/-1 V range
overload_bits = 8;
assert(isscalar(overload_amplitude) && isnumeric(overload_amplitude) && ...
    ~islogical(overload_amplitude) && isreal(overload_amplitude) && ...
    isfinite(overload_amplitude) && overload_amplitude > full_scale, ...
    'The broken case requires overload_amplitude greater than full_scale.');
assert(isscalar(overload_bits) && isnumeric(overload_bits) && ...
    ~islogical(overload_bits) && isreal(overload_bits) && ...
    isfinite(overload_bits) && overload_bits == floor(overload_bits) && ...
    overload_bits >= 2 && overload_bits <= max_bits, ...
    'overload_bits must be an integer from 2 through max_bits.');

x_overload = overload_amplitude*cos(2*pi*f0*t + phi);
overload_clipped = x_overload < -full_scale | x_overload > full_scale;
x_overload_limited = min(max(x_overload, -full_scale), full_scale);
overload_levels = 2^overload_bits;
overload_delta = 2*full_scale/overload_levels;
overload_code = floor((x_overload_limited + full_scale)/overload_delta);
overload_code = min(max(overload_code, 0), overload_levels-1);
x_overload_quantized = -full_scale + ...
    (overload_code+0.5)*overload_delta;
overload_error = x_overload_quantized-x_overload;
overload_clip_count = sum(overload_clipped);
overload_error_rms = sqrt(mean(overload_error.^2));
overload_peak_error = max(abs(overload_error));
assert(overload_clip_count > 0, ...
    'The deliberately broken case must contain clipped samples.');
assert(overload_error_rms > max(utilization_error_rms_v), ...
    'Clipping must be worse than every non-clipping utilization case.');

figure('Name', 'P04 broken case: clipping is not quantization noise');
subplot(2,1,1);
plot(t(view), x_overload(view), 'LineWidth', 1.1, ...
    'DisplayName', 'over-range input');
hold on;
stairs(t(view), x_overload_quantized(view), 'LineWidth', 1.2, ...
    'DisplayName', 'saturated ADC output');
plot(t(view), full_scale*ones(size(view)), ':', ...
    'DisplayName', '+full-scale input limit');
plot(t(view), -full_scale*ones(size(view)), ':', ...
    'DisplayName', '-full-scale input limit');
grid on;
xlabel('Time (s)');
ylabel('Voltage (V)');
title('Broken range choice flattens peaks and discards their height');
legend('Location', 'best');

subplot(2,1,2);
stem(n(view), overload_error(view), 'filled');
grid on;
xlabel('Sample index n (samples)');
ylabel('Clipping error x_q-x (V)');
title('Clipping error exceeds the half-LSB quantization bound');

fprintf('P04 broken-case metrics\n');
fprintf('  input peak / ADC limit         = %.3f V / %.3f V\n', ...
    overload_amplitude, full_scale);
fprintf('  clipped samples                = %d of %d samples\n', ...
    overload_clip_count, sample_count);
fprintf('  clipping-case error RMS        = %.9f V\n', overload_error_rms);
fprintf('  clipping-case peak error       = %.9f V\n', overload_peak_error);

%% Optional listening vectors - playback is intentionally not automatic
audio_gap_sample_count = round(0.10*fs);
assert(audio_gap_sample_count >= 0 && ...
    audio_gap_sample_count <= max_samples, ...
    'The optional audio gap is limited to max_samples; reduce fs.');
audio_preview_sample_count = 3*sample_count + 2*audio_gap_sample_count;
audio_error_preview_sample_count = 2*sample_count + audio_gap_sample_count;
assert(audio_preview_sample_count <= 5*max_samples, ...
    'The optional audio preview is limited to five maximum-size records.');
assert(audio_error_preview_sample_count <= 3*max_samples, ...
    'The optional error preview is limited to three maximum-size records.');
% Allocate only after every derived size has passed its resource ceiling.
audio_gap = zeros(1, audio_gap_sample_count);
audio_preview = [x, audio_gap, x_quantized, audio_gap, x_overload_quantized];
audio_error_gain = 8;
audio_error_preview = audio_error_gain*[quantization_error, audio_gap, ...
    dither_total_error];
assert(numel(audio_preview) == audio_preview_sample_count, ...
    'The allocated audio preview must match its preflight size.');
assert(numel(audio_error_preview) == audio_error_preview_sample_count, ...
    'The allocated error preview must match its preflight size.');
% To listen deliberately after inspecting levels, a learner may run:
% soundsc(audio_preview, fs) or soundsc(audio_error_preview, fs)
% Those commands are not executed here, so no audio device is required.

%% Completion summary
fprintf(['P04 complete: more bits shrink each voltage step; poor range use ' ...
    'wastes effective resolution; dither changes error structure; and ' ...
    'overload clipping discards amplitude information.\n']);
