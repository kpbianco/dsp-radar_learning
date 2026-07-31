%% P01 - Build a Sinusoid and a Complex Phasor
% Guiding question:
% How do amplitude, frequency, and phase appear in time and in the complex plane?
%
% Dependency contract: base MATLAB only. No toolbox functions are required.
clear;
close all;
clc;
random_seed = 84;
rng(random_seed, 'twister');

%% Baseline controls - change one of these at a time
A = 1.0;                 % signal amplitude (arbitrary units)
f0 = 5.0;                % frequency (Hz)
phi = pi/6;              % initial phase (rad)
fs = 200;                % sample rate (samples/s)
duration = 1.0;          % record duration (s)
max_baseline_samples = 5000; % resource ceiling for an edited baseline

% Fail clearly if an edited control cannot describe the intended baseline.
assert(isscalar(A) && isreal(A) && isfinite(A) && A > 0, ...
    'A must be one finite positive real scalar.');
assert(isscalar(f0) && isreal(f0) && isfinite(f0) && f0 > 0, ...
    'f0 must be one finite positive real frequency in Hz.');
assert(isscalar(phi) && isfinite(phi) && isreal(phi), ...
    'phi must be one finite real phase in radians.');
assert(isscalar(fs) && isreal(fs) && isfinite(fs) && fs > 2*f0, ...
    'fs must be finite, real, and greater than 2*f0 for the baseline.');
assert(isscalar(duration) && isreal(duration) && isfinite(duration) && duration > 0, ...
    'duration must be one finite positive real value in seconds.');

baseline_sample_count = round(duration*fs);
assert(baseline_sample_count >= 2 && ...
    abs(baseline_sample_count - duration*fs) < 10*eps(duration*fs), ...
    'duration*fs must be an integer of at least two samples.');
assert(baseline_sample_count <= max_baseline_samples, ...
    'The baseline is limited to 5000 samples; reduce fs or duration.');
t = (0:baseline_sample_count-1)/fs;

% The same angle drives both representations.
theta = 2*pi*f0*t + phi;
x = A*cos(theta);
z = A*exp(1j*theta);

%% Baseline figure - the real sinusoid is the I-axis projection
figure('Name', 'P01 baseline: time and complex-plane views');

subplot(3,1,1);
plot(t, x, 'LineWidth', 1.3);
grid on;
xlabel('Time (s)');
ylabel('Amplitude (a.u.)');
title('Real cosine x(t) = A cos(2\pi f_0 t + \phi)');

subplot(3,1,2);
plot(t, real(z), 'LineWidth', 1.2, 'DisplayName', 'I = real(z)');
hold on;
plot(t, imag(z), 'LineWidth', 1.2, 'DisplayName', 'Q = imag(z)');
grid on;
xlabel('Time (s)');
ylabel('Amplitude (a.u.)');
title('Complex phasor components');
legend('Location', 'best');

subplot(3,1,3);
plot(real(z), imag(z), 'LineWidth', 1.2);
hold on;
plot(real(z(1)), imag(z(1)), 'o', 'MarkerFaceColor', [0.85 0.33 0.10], ...
    'DisplayName', 'start');
quiver(real(z(1)), imag(z(1)), real(z(2)-z(1)), imag(z(2)-z(1)), ...
    0, 'LineWidth', 1.4, 'MaxHeadSize', 3, 'DisplayName', 'next-sample direction');
axis equal;
grid on;
xlabel('In-phase amplitude, I (a.u.)');
ylabel('Quadrature amplitude, Q (a.u.)');
title('IQ trajectory: radius A, starting angle \phi');
legend('Location', 'best');

max_projection_error = max(abs(x - real(z)));
max_radius_error = max(abs(abs(z) - A));
measured_initial_phase = atan2(imag(z(1)), real(z(1)));
samples_per_cycle = fs/f0;
cycles_in_record = f0*duration;

fprintf('P01 baseline metrics\n');
fprintf('  random seed             = %d\n', random_seed);
fprintf('  samples                 = %d\n', baseline_sample_count);
fprintf('  samples per cycle       = %.1f samples/cycle\n', samples_per_cycle);
fprintf('  cycles in record        = %.2f cycles\n', cycles_in_record);
fprintf('  initial phase           = %.6f rad\n', measured_initial_phase);
fprintf('  max projection error    = %.3g a.u.\n', max_projection_error);
fprintf('  max radius error        = %.3g a.u.\n', max_radius_error);

assert(max_projection_error < 1e-12, ...
    'The real cosine must equal the real part of the phasor.');
assert(max_radius_error < 1e-12, ...
    'The ideal phasor magnitude must remain equal to A.');

%% Rotation direction - frequency sign is visible only in complex data
direction_sample_count = min(baseline_sample_count, ...
    max(2, floor(fs/(4*f0)) + 1));
t_direction = (0:direction_sample_count-1)/fs;
z_positive = A*exp(1j*(2*pi*f0*t_direction + phi));
z_negative = A*exp(1j*(-2*pi*f0*t_direction + phi));
arrow_index = min(3, direction_sample_count);
positive_step_angle = angle(conj(z_positive(1))*z_positive(2));
negative_step_angle = angle(conj(z_negative(1))*z_negative(2));

assert(positive_step_angle > 0 && negative_step_angle < 0, ...
    'Positive and negative frequencies must advance in opposite directions.');
fprintf('P01 rotation metrics\n');
fprintf('  positive step angle     = %+.6f rad/sample\n', positive_step_angle);
fprintf('  negative step angle     = %+.6f rad/sample\n', negative_step_angle);

figure('Name', 'P01 positive and negative frequency direction');
subplot(1,2,1);
plot(real(z_positive), imag(z_positive), '.-', 'LineWidth', 1.2);
hold on;
plot(real(z_positive(1)), imag(z_positive(1)), 'o', ...
    'MarkerFaceColor', [0.85 0.33 0.10]);
quiver(real(z_positive(1)), imag(z_positive(1)), ...
    real(z_positive(arrow_index)-z_positive(1)), ...
    imag(z_positive(arrow_index)-z_positive(1)), 0, 'LineWidth', 1.3);
axis equal;
grid on;
xlabel('I (a.u.)');
ylabel('Q (a.u.)');
title(sprintf('Positive frequency: %+g Hz', f0));

subplot(1,2,2);
plot(real(z_negative), imag(z_negative), '.-', 'LineWidth', 1.2);
hold on;
plot(real(z_negative(1)), imag(z_negative(1)), 'o', ...
    'MarkerFaceColor', [0.85 0.33 0.10]);
quiver(real(z_negative(1)), imag(z_negative(1)), ...
    real(z_negative(arrow_index)-z_negative(1)), ...
    imag(z_negative(arrow_index)-z_negative(1)), 0, 'LineWidth', 1.3);
axis equal;
grid on;
xlabel('I (a.u.)');
ylabel('Q (a.u.)');
title(sprintf('Negative frequency: %+g Hz', -f0));

%% Parameter sweep 1 - amplitude changes radius, not rotation rate
amplitudes = [0.5 1.0 1.5];
figure('Name', 'P01 sweep 1: amplitude');
hold on;
grid on;
axis equal;
for k = 1:numel(amplitudes)
    z_amplitude = amplitudes(k)*exp(1j*theta);
    assert(max(abs(abs(z_amplitude) - amplitudes(k))) < 1e-12, ...
        'Each amplitude sweep radius must equal its requested amplitude.');
    plot(real(z_amplitude), imag(z_amplitude), 'LineWidth', 1.2, ...
        'DisplayName', sprintf('A = %.1f a.u.', amplitudes(k)));
end
xlabel('In-phase amplitude, I (a.u.)');
ylabel('Quadrature amplitude, Q (a.u.)');
title('Amplitude sweep: A controls IQ radius');
legend('Location', 'best');

%% Parameter sweep 2 - phase changes the starting point
phases = [0 pi/4 pi/2];
phase_colors = lines(numel(phases));
phase_view = t <= 2/f0;

figure('Name', 'P01 sweep 2: phase');
subplot(1,2,1);
hold on;
grid on;
for k = 1:numel(phases)
    x_phase = A*cos(2*pi*f0*t + phases(k));
    plot(t(phase_view), x_phase(phase_view), 'LineWidth', 1.2, ...
        'Color', phase_colors(k,:), ...
        'DisplayName', sprintf('\\phi = %.2f rad', phases(k)));
end
xlabel('Time (s)');
ylabel('Amplitude (a.u.)');
title('Same period, different point in the cycle');
legend('Location', 'best');

subplot(1,2,2);
hold on;
grid on;
axis equal;
reference_angle = linspace(0, 2*pi, 361);
plot(A*cos(reference_angle), A*sin(reference_angle), 'k:');
for k = 1:numel(phases)
    plot(A*cos(phases(k)), A*sin(phases(k)), 'o', ...
        'Color', phase_colors(k,:), 'MarkerFaceColor', phase_colors(k,:), ...
        'DisplayName', sprintf('\\phi = %.2f rad', phases(k)));
end
xlabel('Initial I (a.u.)');
ylabel('Initial Q (a.u.)');
title('Phase selects the starting point');
legend('Location', 'best');

%% Parameter sweep 3 - frequency changes cycles and rotation rate
frequencies = [2.5 5.0 10.0];
frequency_colors = lines(numel(frequencies));
frequency_view = t <= 0.4;

figure('Name', 'P01 sweep 3: frequency');
subplot(2,1,1);
hold on;
grid on;
for k = 1:numel(frequencies)
    x_frequency = A*cos(2*pi*frequencies(k)*t + phi);
    plot(t(frequency_view), x_frequency(frequency_view), 'LineWidth', 1.1, ...
        'Color', frequency_colors(k,:), ...
        'DisplayName', sprintf('f = %.1f Hz', frequencies(k)));
end
xlabel('Time (s)');
ylabel('Amplitude (a.u.)');
title('Frequency sweep: more cycles fit in the same time');
legend('Location', 'best');

subplot(2,1,2);
hold on;
grid on;
for k = 1:numel(frequencies)
    completed_rotations = frequencies(k)*t;
    plot(t(frequency_view), completed_rotations(frequency_view), ...
        'LineWidth', 1.2, 'Color', frequency_colors(k,:), ...
        'DisplayName', sprintf('f = %.1f Hz', frequencies(k)));
end
xlabel('Time (s)');
ylabel('Angle advanced (rotations)');
title('Frequency is the phasor rotation rate');
legend('Location', 'best');

%% Deliberately broken case - undersampling creates a convincing alias
fs_bad = 8;              % samples/s, below 2*f0 = 10 samples/s
assert(isscalar(fs_bad) && isreal(fs_bad) && isfinite(fs_bad) && fs_bad > 0, ...
    'fs_bad must be one finite positive real sample rate.');
assert(fs_bad < 2*f0, ...
    'The deliberately broken case must remain below the Nyquist rate.');

bad_sample_count = round(duration*fs_bad);
assert(bad_sample_count >= 2 && ...
    abs(bad_sample_count - duration*fs_bad) < 10*eps(duration*fs_bad), ...
    'duration*fs_bad must be an integer of at least two samples.');
assert(bad_sample_count <= max_baseline_samples, ...
    'The broken case is limited to 5000 samples; reduce fs_bad or duration.');
t_bad = (0:bad_sample_count-1)/fs_bad;
x_bad = A*cos(2*pi*f0*t_bad + phi);

signed_alias_frequency = f0 - round(f0/fs_bad)*fs_bad;
apparent_alias_frequency = abs(signed_alias_frequency);
if signed_alias_frequency < 0
    apparent_alias_phase = -phi;
else
    apparent_alias_phase = phi;
end
x_alias_dense = A*cos(2*pi*apparent_alias_frequency*t + apparent_alias_phase);
x_alias_at_samples = A*cos(2*pi*apparent_alias_frequency*t_bad + apparent_alias_phase);
alias_sample_error = max(abs(x_bad - x_alias_at_samples));

figure('Name', 'P01 broken case: undersampling');
plot(t, x, 'LineWidth', 1.1, ...
    'DisplayName', sprintf('true %.1f Hz waveform', f0));
hold on;
plot(t, x_alias_dense, '--', 'LineWidth', 1.2, ...
    'DisplayName', sprintf('apparent %.1f Hz alias', apparent_alias_frequency));
stem(t_bad, x_bad, 'filled', ...
    'DisplayName', sprintf('%.1f samples/s measurements', fs_bad));
grid on;
xlabel('Time (s)');
ylabel('Amplitude (a.u.)');
title('Broken case: two different waveforms match every sample');
legend('Location', 'best');

fprintf('P01 broken-case metrics\n');
fprintf('  sample rate             = %.1f samples/s\n', fs_bad);
fprintf('  Nyquist limit           = %.1f Hz\n', fs_bad/2);
fprintf('  true frequency          = %.1f Hz\n', f0);
fprintf('  apparent real frequency = %.1f Hz\n', apparent_alias_frequency);
fprintf('  sample agreement error  = %.3g a.u.\n', alias_sample_error);

assert(alias_sample_error < 1e-12, ...
    'The true tone and its alias must agree at every broken-case sample.');

%% Completion summary
fprintf(['P01 complete: amplitude maps to radius, phase to starting angle, ' ...
    'and frequency to rotation rate.\n']);
