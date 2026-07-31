%% P02 - See Sampling as Taking Measurements
% Guiding question:
% What information is lost when a continuous-looking signal is represented by discrete samples?
%
% Dependency contract: base MATLAB only. No toolbox functions are required.
clear;
close all;
clc;
random_seed = 202;
rng(random_seed, 'twister');

%% Baseline controls - change one of these at a time
A = 1.0;                         % signal amplitude (arbitrary units)
f0 = 7.0;                        % continuous tone frequency (Hz)
phi = pi/5;                      % continuous tone phase (rad)
duration = 1.0;                  % observation duration (s)
fs_reference = 2000;             % dense display rate (points/s)
fs_baseline = 80;                % measurement rate (samples/s)
max_reference_points = 20001;    % resource ceiling for the dense display
max_measurement_samples = 5000;  % resource ceiling for any measurement set
max_sweep_cases = 12;            % resource ceiling for edited sweep vectors

% Fail clearly before allocation if an edited control is malformed.
assert(isscalar(A) && isnumeric(A) && ~islogical(A) && ...
    isreal(A) && isfinite(A) && A > 0, ...
    'A must be one finite positive real scalar.');
assert(isscalar(f0) && isnumeric(f0) && ~islogical(f0) && ...
    isreal(f0) && isfinite(f0) && f0 > 0, ...
    'f0 must be one finite positive real frequency in Hz.');
assert(isscalar(phi) && isnumeric(phi) && ~islogical(phi) && ...
    isreal(phi) && isfinite(phi), ...
    'phi must be one finite real phase in radians.');
assert(isscalar(duration) && isnumeric(duration) && ~islogical(duration) && ...
    isreal(duration) && isfinite(duration) && duration > 0, ...
    'duration must be one finite positive real value in seconds.');
assert(isscalar(fs_reference) && isnumeric(fs_reference) && ...
    ~islogical(fs_reference) && isreal(fs_reference) && ...
    isfinite(fs_reference) && fs_reference > 2*f0, ...
    'fs_reference must be finite, real, and greater than 2*f0.');
assert(isscalar(fs_baseline) && isnumeric(fs_baseline) && ...
    ~islogical(fs_baseline) && isreal(fs_baseline) && ...
    isfinite(fs_baseline) && fs_baseline > 2*f0, ...
    'fs_baseline must be finite, real, and greater than 2*f0.');

reference_intervals = round(duration*fs_reference);
assert(reference_intervals >= 2 && ...
    abs(reference_intervals - duration*fs_reference) < ...
    10*eps(duration*fs_reference), ...
    'duration*fs_reference must be an integer of at least two intervals.');
reference_point_count = reference_intervals + 1;
assert(reference_point_count <= max_reference_points, ...
    'The dense reference is limited to 20001 points; reduce fs_reference or duration.');

baseline_sample_count = round(duration*fs_baseline);
assert(baseline_sample_count >= 2 && ...
    abs(baseline_sample_count - duration*fs_baseline) < ...
    10*eps(duration*fs_baseline), ...
    'duration*fs_baseline must be an integer of at least two samples.');
assert(baseline_sample_count <= max_measurement_samples, ...
    'A measurement set is limited to 5000 samples; reduce fs_baseline or duration.');

% The dense curve is a display reference. The ADC-like measurements are only
% the values of the same equation at n/fs_baseline.
t_dense = (0:reference_intervals)/fs_reference;
x_dense = A*cos(2*pi*f0*t_dense + phi);
n_baseline = 0:baseline_sample_count-1;
t_baseline = n_baseline/fs_baseline;
x_baseline = A*cos(2*pi*f0*t_baseline + phi);
x_reference_at_samples = A*cos(2*pi*f0*t_baseline + phi);
measurement_error = max(abs(x_baseline - x_reference_at_samples));

%% Baseline figure - a sampler keeps values, not the line between them
figure('Name', 'P02 baseline: continuous-looking reference and measurements');

subplot(2,1,1);
plot(t_dense, x_dense, 'LineWidth', 1.2, ...
    'DisplayName', sprintf('dense %.0f point/s reference', fs_reference));
hold on;
stem(t_baseline, x_baseline, 'filled', ...
    'DisplayName', sprintf('measurements at %.0f samples/s', fs_baseline));
grid on;
xlabel('Time (s)');
ylabel('Amplitude (a.u.)');
title('Measurements retain values only at the marked instants');
legend('Location', 'best');

subplot(2,1,2);
stem(n_baseline, x_baseline, 'filled');
grid on;
xlabel('Sample index n (samples)');
ylabel('Measured amplitude x[n] (a.u.)');
title('The stored object is a sequence indexed by integer n');

% Draw a piecewise-linear guess explicitly. Uniform sample timing lets each
% display point identify its two neighboring measurements directly, so work
% grows with display points rather than display points times measurements.
baseline_reconstruction_view = t_dense <= t_baseline(end);
t_baseline_reconstruction = t_dense(baseline_reconstruction_view);
x_baseline_true_view = x_dense(baseline_reconstruction_view);
baseline_segment = floor(t_baseline_reconstruction*fs_baseline) + 1;
baseline_segment = min(max(baseline_segment, 1), baseline_sample_count-1);
alpha = (t_baseline_reconstruction - t_baseline(baseline_segment)) ...
    ./ (t_baseline(baseline_segment+1) - t_baseline(baseline_segment));
x_baseline_linear = (1-alpha).*x_baseline(baseline_segment) ...
    + alpha.*x_baseline(baseline_segment+1);
baseline_linear_rmse = sqrt(mean((x_baseline_linear - x_baseline_true_view).^2));

figure('Name', 'P02 baseline: interpolation is an added assumption');
plot(t_baseline_reconstruction, x_baseline_true_view, 'LineWidth', 1.2, ...
    'DisplayName', 'unobserved reference between samples');
hold on;
plot(t_baseline_reconstruction, x_baseline_linear, '--', 'LineWidth', 1.2, ...
    'DisplayName', 'piecewise-linear guess');
stem(t_baseline, x_baseline, 'filled', 'DisplayName', 'stored samples');
grid on;
xlabel('Time (s)');
ylabel('Amplitude (a.u.)');
title('A line can be drawn through samples, but the samples did not store it');
legend('Location', 'best');

fprintf('P02 baseline metrics\n');
fprintf('  random seed               = %d\n', random_seed);
fprintf('  tone frequency            = %.1f Hz\n', f0);
fprintf('  measurement rate          = %.1f samples/s\n', fs_baseline);
fprintf('  Nyquist limit             = %.1f Hz\n', fs_baseline/2);
fprintf('  samples per cycle         = %.3f samples/cycle\n', fs_baseline/f0);
fprintf('  dense reference points    = %d points\n', reference_point_count);
fprintf('  stored measurements       = %d samples\n', baseline_sample_count);
fprintf('  measurement equation error= %.3g a.u.\n', measurement_error);
fprintf('  linear interpolation RMSE = %.6f a.u.\n', baseline_linear_rmse);

assert(measurement_error < 1e-12, ...
    'Each stored value must equal the continuous equation at its sample instant.');

%% Parameter sweep 1 - far above, near, and below twice the tone frequency
sample_rates = [80 16 12];       % samples/s: far above, near, and below 2*f0
assert(isvector(sample_rates) && isnumeric(sample_rates) && ...
    ~islogical(sample_rates) && isreal(sample_rates) && ...
    all(isfinite(sample_rates)) && all(sample_rates > 0), ...
    'sample_rates must contain finite positive real values.');
assert(numel(sample_rates) == 3, ...
    'sample_rates must contain exactly three far, near, and below-Nyquist cases.');
assert(sample_rates(1) > 4*f0, ...
    'The first sweep rate must remain far above twice the tone frequency.');
assert(sample_rates(2) > 2*f0 && sample_rates(2) < 3*f0, ...
    'The second sweep rate must remain near and above twice the tone frequency.');
assert(sample_rates(3) < 2*f0, ...
    'The third sweep rate must remain below twice the tone frequency.');

rate_sweep_rmse = zeros(size(sample_rates));
figure('Name', 'P02 sweep 1: measurement rate');
for rate_index = 1:numel(sample_rates)
    fs_sweep = sample_rates(rate_index);
    sweep_sample_count = round(duration*fs_sweep);
    assert(sweep_sample_count >= 2 && ...
        abs(sweep_sample_count - duration*fs_sweep) < 10*eps(duration*fs_sweep), ...
        'Every rate sweep must create an integer record of at least two samples.');
    assert(sweep_sample_count <= max_measurement_samples, ...
        'Every rate sweep is limited to 5000 samples.');
    t_sweep = (0:sweep_sample_count-1)/fs_sweep;
    x_sweep = A*cos(2*pi*f0*t_sweep + phi);

    sweep_view = t_dense <= t_sweep(end);
    t_sweep_reconstruction = t_dense(sweep_view);
    x_sweep_true = x_dense(sweep_view);
    sweep_segment = floor(t_sweep_reconstruction*fs_sweep) + 1;
    sweep_segment = min(max(sweep_segment, 1), sweep_sample_count-1);
    alpha = (t_sweep_reconstruction - t_sweep(sweep_segment)) ...
        ./ (t_sweep(sweep_segment+1) - t_sweep(sweep_segment));
    x_sweep_linear = (1-alpha).*x_sweep(sweep_segment) ...
        + alpha.*x_sweep(sweep_segment+1);
    rate_sweep_rmse(rate_index) = ...
        sqrt(mean((x_sweep_linear - x_sweep_true).^2));

    subplot(numel(sample_rates),1,rate_index);
    plot(t_sweep_reconstruction, x_sweep_true, 'LineWidth', 1.0, ...
        'DisplayName', sprintf('true %.1f Hz waveform', f0));
    hold on;
    plot(t_sweep_reconstruction, x_sweep_linear, '--', 'LineWidth', 1.1, ...
        'DisplayName', 'linear guess');
    stem(t_sweep, x_sweep, 'filled', ...
        'DisplayName', sprintf('%.0f samples/s', fs_sweep));
    grid on;
    xlabel('Time (s)');
    ylabel('Amplitude (a.u.)');
    title(sprintf('f_s = %.0f samples/s, %.2f samples/cycle, Nyquist = %.1f Hz', ...
        fs_sweep, fs_sweep/f0, fs_sweep/2));
    legend('Location', 'best');

    fprintf(['P02 rate sweep: fs = %.1f samples/s, %.3f samples/cycle, ' ...
        'linear RMSE = %.6f a.u.\n'], ...
        fs_sweep, fs_sweep/f0, rate_sweep_rmse(rate_index));
end
assert(rate_sweep_rmse(1) < rate_sweep_rmse(2), ...
    'The far-above-Nyquist linear guess should beat the near-Nyquist guess.');

%% Parameter sweep 2 - move the measurement clock without changing the signal
fs_offset = 16;                   % samples/s, just above twice f0
sample_offset_fractions = [0 0.25 0.50]; % fractions of one sample interval
assert(isscalar(fs_offset) && isnumeric(fs_offset) && ~islogical(fs_offset) && ...
    isreal(fs_offset) && isfinite(fs_offset) && fs_offset > 2*f0, ...
    'fs_offset must be finite, real, and greater than 2*f0.');
assert(isvector(sample_offset_fractions) && ...
    isnumeric(sample_offset_fractions) && ~islogical(sample_offset_fractions) && ...
    isreal(sample_offset_fractions) && all(isfinite(sample_offset_fractions)) && ...
    all(sample_offset_fractions >= 0) && all(sample_offset_fractions < 1), ...
    'Sample offsets must be finite real fractions from 0 up to but not including 1.');
assert(numel(sample_offset_fractions) <= max_sweep_cases, ...
    'The measurement-clock-offset sweep is limited to 12 cases.');

offset_sample_count = floor(duration*fs_offset);
assert(offset_sample_count >= 2 && offset_sample_count <= max_measurement_samples, ...
    'The offset sweep must contain from 2 through 5000 samples.');
offset_sweep_rmse = zeros(size(sample_offset_fractions));
figure('Name', 'P02 sweep 2: measurement-clock offset');
for offset_index = 1:numel(sample_offset_fractions)
    offset_fraction = sample_offset_fractions(offset_index);
    t_offset = ((0:offset_sample_count-1) + offset_fraction)/fs_offset;
    assert(t_offset(end) < duration, ...
        'Every offset-sweep measurement must remain inside the observation window.');
    x_offset = A*cos(2*pi*f0*t_offset + phi);

    offset_view = t_dense >= t_offset(1) & t_dense <= t_offset(end);
    t_offset_reconstruction = t_dense(offset_view);
    x_offset_true = x_dense(offset_view);
    offset_segment = floor((t_offset_reconstruction-t_offset(1))*fs_offset) + 1;
    offset_segment = min(max(offset_segment, 1), offset_sample_count-1);
    alpha = (t_offset_reconstruction - t_offset(offset_segment)) ...
        ./ (t_offset(offset_segment+1) - t_offset(offset_segment));
    x_offset_linear = (1-alpha).*x_offset(offset_segment) ...
        + alpha.*x_offset(offset_segment+1);
    offset_sweep_rmse(offset_index) = ...
        sqrt(mean((x_offset_linear - x_offset_true).^2));

    subplot(numel(sample_offset_fractions),1,offset_index);
    plot(t_offset_reconstruction, x_offset_true, 'LineWidth', 1.0, ...
        'DisplayName', 'same continuous waveform');
    hold on;
    plot(t_offset_reconstruction, x_offset_linear, '--', 'LineWidth', 1.1, ...
        'DisplayName', 'linear guess');
    stem(t_offset, x_offset, 'filled', ...
        'DisplayName', sprintf('clock offset = %.2f sample', offset_fraction));
    grid on;
    xlabel('Time (s)');
    ylabel('Amplitude (a.u.)');
    title(sprintf('Same f_s, measurement clock shifted by %.2f sample', ...
        offset_fraction));
    legend('Location', 'best');

    fprintf(['P02 offset sweep: offset = %.2f sample, first time = %.6f s, ' ...
        'linear RMSE = %.6f a.u.\n'], ...
        offset_fraction, t_offset(1), offset_sweep_rmse(offset_index));
end

%% Deliberately broken case - three continuous sinusoids make one sequence
fs_bad = 12;                      % samples/s, below 2*f0 = 14 samples/s
assert(isscalar(fs_bad) && isnumeric(fs_bad) && ~islogical(fs_bad) && ...
    isreal(fs_bad) && isfinite(fs_bad) && fs_bad > 0, ...
    'fs_bad must be one finite positive real sample rate.');
assert(fs_bad > f0 && fs_bad < 2*f0, ...
    'The broken case requires f0 < fs_bad < 2*f0.');

bad_sample_count = round(duration*fs_bad);
assert(bad_sample_count >= 2 && ...
    abs(bad_sample_count - duration*fs_bad) < 10*eps(duration*fs_bad), ...
    'duration*fs_bad must be an integer of at least two samples.');
assert(bad_sample_count <= max_measurement_samples, ...
    'The broken measurement set is limited to 5000 samples.');
t_bad = (0:bad_sample_count-1)/fs_bad;
x_bad = A*cos(2*pi*f0*t_bad + phi);

% Frequencies separated by integer multiples of fs produce the same samples.
% For the reflected low alias, cosine's even symmetry reverses the phase.
f_alias_low = fs_bad - f0;
phi_alias_low = -phi;
f_alias_high = f0 + fs_bad;
assert(fs_reference > 2*f_alias_high, ...
    ['fs_reference must exceed twice the highest broken-case candidate ' ...
    'frequency (f0 + fs_bad) so every displayed curve is resolved.']);
x_alias_low_at_samples = A*cos(2*pi*f_alias_low*t_bad + phi_alias_low);
x_alias_high_at_samples = A*cos(2*pi*f_alias_high*t_bad + phi);
low_alias_sample_error = max(abs(x_bad - x_alias_low_at_samples));
high_alias_sample_error = max(abs(x_bad - x_alias_high_at_samples));
alias_argument_scale = 1 + max(abs([2*pi*f0*t_bad + phi, ...
    2*pi*f_alias_low*t_bad + phi_alias_low, ...
    2*pi*f_alias_high*t_bad + phi]));
alias_tolerance = min(1e-9*max(1, abs(A)), ...
    64*eps(max(1, abs(A)))*alias_argument_scale);

x_alias_low_dense = A*cos(2*pi*f_alias_low*t_dense + phi_alias_low);
x_alias_high_dense = A*cos(2*pi*f_alias_high*t_dense + phi);

figure('Name', 'P02 broken case: indistinguishable continuous candidates');
subplot(2,1,1);
plot(t_dense, x_dense, 'LineWidth', 1.0, ...
    'DisplayName', sprintf('original %.1f Hz', f0));
hold on;
plot(t_dense, x_alias_low_dense, '--', 'LineWidth', 1.1, ...
    'DisplayName', sprintf('low candidate %.1f Hz', f_alias_low));
plot(t_dense, x_alias_high_dense, ':', 'LineWidth', 1.2, ...
    'DisplayName', sprintf('high candidate %.1f Hz', f_alias_high));
stem(t_bad, x_bad, 'filled', ...
    'DisplayName', sprintf('shared %.0f samples/s measurements', fs_bad));
grid on;
xlabel('Time (s)');
ylabel('Amplitude (a.u.)');
title('Broken case: different continuous paths cross every measurement');
legend('Location', 'best');

subplot(2,1,2);
stem(0:bad_sample_count-1, x_bad, 'filled');
grid on;
xlabel('Sample index n (samples)');
ylabel('Measured amplitude x[n] (a.u.)');
title('All three candidates become exactly the same stored sequence');

fprintf('P02 broken-case metrics\n');
fprintf('  sample rate               = %.1f samples/s\n', fs_bad);
fprintf('  Nyquist limit             = %.1f Hz\n', fs_bad/2);
fprintf('  original frequency        = %.1f Hz\n', f0);
fprintf('  low candidate frequency   = %.1f Hz\n', f_alias_low);
fprintf('  high candidate frequency  = %.1f Hz\n', f_alias_high);
fprintf('  low-candidate sample error= %.3g a.u.\n', low_alias_sample_error);
fprintf('  high-candidate sample error= %.3g a.u.\n', high_alias_sample_error);
fprintf('  sample-agreement tolerance= %.3g a.u.\n', alias_tolerance);

assert(low_alias_sample_error < alias_tolerance, ...
    'The original and reflected low-frequency candidate must share every sample.');
assert(high_alias_sample_error < alias_tolerance, ...
    'Frequencies separated by fs_bad must share every sample.');

%% Completion summary
fprintf(['P02 complete: samples retain measured values and timing, but not a ' ...
    'unique continuous path between measurements.\n']);
