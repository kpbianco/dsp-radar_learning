%% P39: Expose Blind Speeds and Use Staggered PRF
% Guiding question:
% Why can a moving target vanish in an MTI radar?
% Positive radial velocity means approaching the radar.
% Each PRF is processed as its own coherent dwell before noncoherent fusion.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P39'));

%% Visible deterministic controls and resource ceilings
random_seed = 3901;
speed_of_light_mps = 299792458;
carrier_frequency_hz = 10e9;
primary_prf_hz = 4.0e3;
secondary_prf_hz = 5.3e3;
pulse_count = 32;
target_amplitude = 1.0;
target_initial_phase_deg = 20;
noise_rms = 0.02;
detection_threshold_normalized = 0.30;
velocity_limit_mps = 150;
velocity_response_sample_count = 2401;
secondary_prf_sweep_hz = [4.0e3 4.2e3 4.5e3 4.9e3 5.3e3 5.7e3 6.2e3];
comparison_tolerance = 1e-10;
max_pulse_count = 128;
max_response_samples = 3001;
max_sweep_cases = 9;
max_figure_groups = 5;
max_stored_numeric_values = 100000;

%% Validate controls before allocating arrays
positive_controls = [speed_of_light_mps carrier_frequency_hz ...
    primary_prf_hz secondary_prf_hz pulse_count target_amplitude ...
    velocity_limit_mps velocity_response_sample_count ...
    comparison_tolerance max_pulse_count max_response_samples ...
    max_sweep_cases max_figure_groups max_stored_numeric_values];
assert(all(isfinite(positive_controls)) && all(positive_controls > 0));
assert(isfinite(random_seed) && random_seed == floor(random_seed) && ...
    random_seed == 3901);
assert(isfinite(target_initial_phase_deg));
assert(isfinite(noise_rms) && noise_rms >= 0);
assert(isfinite(detection_threshold_normalized) && ...
    detection_threshold_normalized > 0 && ...
    detection_threshold_normalized < 1);
integer_controls = [pulse_count velocity_response_sample_count ...
    max_pulse_count max_response_samples max_sweep_cases ...
    max_figure_groups max_stored_numeric_values];
assert(all(integer_controls == floor(integer_controls)));
assert(max_pulse_count == 128);
assert(max_response_samples == 3001);
assert(max_sweep_cases == 9);
assert(max_figure_groups == 5);
assert(max_stored_numeric_values == 100000);
assert(pulse_count >= 8 && pulse_count <= max_pulse_count);
assert(velocity_response_sample_count >= 101 && ...
    velocity_response_sample_count <= max_response_samples && ...
    mod(velocity_response_sample_count, 2) == 1);
assert(secondary_prf_hz ~= primary_prf_hz);
assert(numel(secondary_prf_sweep_hz) >= 3 && ...
    numel(secondary_prf_sweep_hz) <= max_sweep_cases && ...
    all(isfinite(secondary_prf_sweep_hz)) && ...
    all(secondary_prf_sweep_hz > 0) && ...
    all(diff(secondary_prf_sweep_hz) > 0) && ...
    any(secondary_prf_sweep_hz == primary_prf_hz) && ...
    any(secondary_prf_sweep_hz == secondary_prf_hz));
assert(max_figure_groups >= 5);

estimated_stored_numeric_values = ...
    24*velocity_response_sample_count+...
    30*pulse_count+50*numel(secondary_prf_sweep_hz);
assert(estimated_stored_numeric_values <= max_stored_numeric_values);

%% Physical model and the baseline blind target
wavelength_m = speed_of_light_mps/carrier_frequency_hz;
primary_pri_s = 1/primary_prf_hz;
secondary_pri_s = 1/secondary_prf_hz;
primary_blind_speed_spacing_mps = wavelength_m*primary_prf_hz/2;
secondary_blind_speed_spacing_mps = wavelength_m*secondary_prf_hz/2;
baseline_target_velocity_mps = primary_blind_speed_spacing_mps;
baseline_target_doppler_hz = 2*baseline_target_velocity_mps/wavelength_m;
primary_phase_increment_rad = 2*pi*baseline_target_doppler_hz/...
    primary_prf_hz;
secondary_phase_increment_rad = 2*pi*baseline_target_doppler_hz/...
    secondary_prf_hz;

assert(abs(baseline_target_doppler_hz-primary_prf_hz) <= ...
    comparison_tolerance*primary_prf_hz);
assert(abs(exp(1j*primary_phase_increment_rad)-1) <= ...
    comparison_tolerance);
assert(abs(exp(1j*secondary_phase_increment_rad)-1) > 0.1);

%% Baseline: apply the two-pulse subtraction at each PRF
pulse_index = 0:pulse_count-1;
primary_slow_time_s = pulse_index*primary_pri_s;
secondary_slow_time_s = pulse_index*secondary_pri_s;
initial_phase_rad = target_initial_phase_deg*pi/180;
primary_clean_sequence = target_amplitude*exp(1j*(initial_phase_rad+...
    2*pi*baseline_target_doppler_hz*primary_slow_time_s));
secondary_clean_sequence = target_amplitude*exp(1j*(initial_phase_rad+...
    2*pi*baseline_target_doppler_hz*secondary_slow_time_s));

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
primary_noise = noise_rms/sqrt(2)*(...
    randn(private_stream, 1, pulse_count)+...
    1j*randn(private_stream, 1, pulse_count));
secondary_noise = noise_rms/sqrt(2)*(...
    randn(private_stream, 1, pulse_count)+...
    1j*randn(private_stream, 1, pulse_count));
primary_observed_sequence = primary_clean_sequence+primary_noise;
secondary_observed_sequence = secondary_clean_sequence+secondary_noise;

% This is the essential MTI operation, shown explicitly rather than hidden.
primary_clean_output = primary_clean_sequence(2:end)-...
    primary_clean_sequence(1:end-1);
secondary_clean_output = secondary_clean_sequence(2:end)-...
    secondary_clean_sequence(1:end-1);
primary_observed_output = primary_observed_sequence(2:end)-...
    primary_observed_sequence(1:end-1);
secondary_observed_output = secondary_observed_sequence(2:end)-...
    secondary_observed_sequence(1:end-1);

primary_measured_gain = sqrt(mean(abs(primary_clean_output).^2))/...
    target_amplitude;
secondary_measured_gain = sqrt(mean(abs(secondary_clean_output).^2))/...
    target_amplitude;
primary_theory_gain = abs(1-exp(-1j*primary_phase_increment_rad));
secondary_theory_gain = abs(1-exp(-1j*secondary_phase_increment_rad));
assert(abs(primary_measured_gain-primary_theory_gain) <= ...
    comparison_tolerance);
assert(abs(secondary_measured_gain-secondary_theory_gain) <= ...
    comparison_tolerance);
assert(primary_measured_gain <= comparison_tolerance);
assert(secondary_measured_gain/2 > detection_threshold_normalized);

figure('Name', 'P39 blind target in two coherent dwells', 'Tag', 'P39');
subplot(2, 2, 1);
plot(pulse_index, angle(primary_clean_sequence)*180/pi, ...
    'o-', 'LineWidth', 1.1);
grid on;
xlabel('Pulse index');
ylabel('Sampled target phase (deg)');
title(sprintf('%.1f kHz: phase repeats modulo 360 deg', ...
    primary_prf_hz/1e3));
subplot(2, 2, 2);
plot(pulse_index, angle(secondary_clean_sequence)*180/pi, ...
    'o-', 'LineWidth', 1.1);
grid on;
xlabel('Pulse index');
ylabel('Sampled target phase (deg)');
title(sprintf('%.1f kHz: phase walks between pulses', ...
    secondary_prf_hz/1e3));
subplot(2, 2, 3);
plot(1:pulse_count-1, abs(primary_observed_output), 'LineWidth', 1.1);
hold on;
plot(1:pulse_count-1, abs(primary_clean_output), '--', 'LineWidth', 1.2);
grid on;
xlabel('Output pulse index');
ylabel('|x[n]-x[n-1]| (amplitude)');
title('Primary-PRF canceller output: target is blind');
legend('Target + noise', 'Target only', 'Location', 'best');
subplot(2, 2, 4);
plot(1:pulse_count-1, abs(secondary_observed_output), 'LineWidth', 1.1);
hold on;
plot(1:pulse_count-1, abs(secondary_clean_output), '--', ...
    'LineWidth', 1.2);
grid on;
xlabel('Output pulse index');
ylabel('|x[n]-x[n-1]| (amplitude)');
title('Secondary-PRF canceller output: target survives');
legend('Target + noise', 'Target only', 'Location', 'best');

%% Sweep 1: map blind speeds for both PRFs and combine amplitudes
velocity_axis_mps = linspace(-velocity_limit_mps, velocity_limit_mps, ...
    velocity_response_sample_count);
doppler_axis_hz = 2*velocity_axis_mps/wavelength_m;
primary_phase_axis_rad = 2*pi*doppler_axis_hz/primary_prf_hz;
secondary_phase_axis_rad = 2*pi*doppler_axis_hz/secondary_prf_hz;
primary_response = abs(1-exp(-1j*primary_phase_axis_rad));
secondary_response = abs(1-exp(-1j*secondary_phase_axis_rad));
primary_response_normalized = primary_response/2;
secondary_response_normalized = secondary_response/2;
combined_response_normalized = max(primary_response_normalized, ...
    secondary_response_normalized);
primary_detection = primary_response_normalized >= ...
    detection_threshold_normalized;
secondary_detection = secondary_response_normalized >= ...
    detection_threshold_normalized;
combined_detection = primary_detection | secondary_detection;

primary_blind_orders = ceil(-velocity_limit_mps/...
    primary_blind_speed_spacing_mps):floor(velocity_limit_mps/...
    primary_blind_speed_spacing_mps);
secondary_blind_orders = ceil(-velocity_limit_mps/...
    secondary_blind_speed_spacing_mps):floor(velocity_limit_mps/...
    secondary_blind_speed_spacing_mps);
primary_blind_velocities_mps = primary_blind_orders*...
    primary_blind_speed_spacing_mps;
secondary_blind_velocities_mps = secondary_blind_orders*...
    secondary_blind_speed_spacing_mps;
primary_blind_markers = zeros(size(primary_blind_velocities_mps));
secondary_blind_markers = zeros(size(secondary_blind_velocities_mps));

assert(any(primary_blind_orders == 1));
assert(any(secondary_blind_orders == 1));
assert(max(primary_response_normalized) <= 1+comparison_tolerance);
assert(max(secondary_response_normalized) <= 1+comparison_tolerance);

figure('Name', 'P39 velocity response and blind-speed nulls', 'Tag', 'P39');
subplot(2, 1, 1);
plot(velocity_axis_mps, primary_response_normalized, 'LineWidth', 1.3);
hold on;
plot(velocity_axis_mps, secondary_response_normalized, 'LineWidth', 1.3);
plot(primary_blind_velocities_mps, primary_blind_markers, 'vo', ...
    'MarkerFaceColor', 'w', 'LineWidth', 1.1);
plot(secondary_blind_velocities_mps, secondary_blind_markers, 'r^', ...
    'MarkerFaceColor', 'w', 'LineWidth', 1.1);
plot(velocity_axis_mps, detection_threshold_normalized*...
    ones(size(velocity_axis_mps)), 'k--', 'LineWidth', 1.0);
grid on;
xlabel('Radial velocity (m/s)');
ylabel('Normalized two-pulse gain');
title('Each PRF places nonzero blind-speed nulls differently');
legend(sprintf('PRF 1 = %.1f kHz', primary_prf_hz/1e3), ...
    sprintf('PRF 2 = %.1f kHz', secondary_prf_hz/1e3), ...
    'PRF 1 nulls', 'PRF 2 nulls', 'Detection threshold', ...
    'Location', 'best');
subplot(2, 1, 2);
plot(velocity_axis_mps, combined_response_normalized, ...
    'LineWidth', 1.4);
hold on;
plot(velocity_axis_mps, detection_threshold_normalized*...
    ones(size(velocity_axis_mps)), 'k--', 'LineWidth', 1.0);
grid on;
xlabel('Radial velocity (m/s)');
ylabel('Max normalized gain across PRFs');
title('Noncoherent max fusion fills the separated blind-speed holes');
legend('max(PRF 1, PRF 2)', 'Detection threshold', ...
    'Location', 'best');

figure('Name', 'P39 detection coverage', 'Tag', 'P39');
stairs(velocity_axis_mps, double(primary_detection), 'LineWidth', 1.2);
hold on;
stairs(velocity_axis_mps, double(secondary_detection), 'LineWidth', 1.2);
stairs(velocity_axis_mps, double(combined_detection), 'k', ...
    'LineWidth', 1.5);
grid on;
ylim([-0.1 1.1]);
xlabel('Radial velocity (m/s)');
ylabel('Threshold crossed (0 or 1)');
title('OR fusion recovers a target detected in either dwell');
legend('PRF 1 only', 'PRF 2 only', 'Combined OR', ...
    'Location', 'best');

%% Sweep 2: vary only the second PRF for the primary blind target
secondary_prf_sweep_gain_normalized = zeros(size(secondary_prf_sweep_hz));
for sweep_index = 1:numel(secondary_prf_sweep_hz)
    sweep_phase_increment_rad = 2*pi*baseline_target_doppler_hz/...
        secondary_prf_sweep_hz(sweep_index);
    secondary_prf_sweep_gain_normalized(sweep_index) = ...
        abs(1-exp(-1j*sweep_phase_increment_rad))/2;
end
broken_sweep_index = find(secondary_prf_sweep_hz == primary_prf_hz, 1);
recovered_sweep_index = find(secondary_prf_sweep_hz == secondary_prf_hz, 1);
assert(secondary_prf_sweep_gain_normalized(broken_sweep_index) <= ...
    comparison_tolerance);
assert(secondary_prf_sweep_gain_normalized(recovered_sweep_index) > ...
    detection_threshold_normalized);

figure('Name', 'P39 second-PRF parameter sweep', 'Tag', 'P39');
plot(secondary_prf_sweep_hz/1e3, ...
    secondary_prf_sweep_gain_normalized, 'o-', 'LineWidth', 1.3);
hold on;
plot(secondary_prf_sweep_hz/1e3, detection_threshold_normalized*...
    ones(size(secondary_prf_sweep_hz)), 'k--', 'LineWidth', 1.0);
grid on;
xlabel('Second PRF (kHz)');
ylabel('Normalized gain at primary blind speed');
title(sprintf('Move PRF 2 while target stays at %.2f m/s', ...
    baseline_target_velocity_mps));
legend('Second-dwell response', 'Detection threshold', ...
    'Location', 'best');

%% Intentionally broken case: use the same PRF twice, then recover
broken_secondary_prf_hz = primary_prf_hz;
broken_secondary_response_normalized = abs(1-exp(-1j*...
    (2*pi*doppler_axis_hz/broken_secondary_prf_hz)))/2;
broken_combined_response_normalized = max(primary_response_normalized, ...
    broken_secondary_response_normalized);
broken_baseline_gain_normalized = abs(1-exp(-1j*...
    (2*pi*baseline_target_doppler_hz/broken_secondary_prf_hz)))/2;
recovered_baseline_gain_normalized = max(primary_theory_gain, ...
    secondary_theory_gain)/2;
broken_model_valid = false;
recovered_model_valid = true;

assert(max(abs(broken_secondary_response_normalized-...
    primary_response_normalized)) <= comparison_tolerance);
assert(broken_baseline_gain_normalized <= comparison_tolerance);
assert(recovered_baseline_gain_normalized > ...
    detection_threshold_normalized);
assert(~broken_model_valid && recovered_model_valid);

figure('Name', 'P39 broken stagger and recovery', 'Tag', 'P39');
subplot(2, 1, 1);
plot(velocity_axis_mps, broken_combined_response_normalized, ...
    'LineWidth', 1.3);
hold on;
plot(velocity_axis_mps, detection_threshold_normalized*...
    ones(size(velocity_axis_mps)), 'k--', 'LineWidth', 1.0);
grid on;
xlabel('Radial velocity (m/s)');
ylabel('Max normalized gain');
title('Broken: both dwells use 4.0 kHz, so blind speeds coincide');
legend('Broken same-PRF fusion', 'Detection threshold', ...
    'Location', 'best');
subplot(2, 1, 2);
plot(velocity_axis_mps, combined_response_normalized, ...
    'LineWidth', 1.3);
hold on;
plot(velocity_axis_mps, detection_threshold_normalized*...
    ones(size(velocity_axis_mps)), 'k--', 'LineWidth', 1.0);
grid on;
xlabel('Radial velocity (m/s)');
ylabel('Max normalized gain');
title('Recovered: restore the 5.3 kHz second dwell');
legend('Staggered-PRF fusion', 'Detection threshold', ...
    'Location', 'best');

%% Retained console metrics
fprintf('\nP39 retained deterministic metrics\n');
fprintf('Wavelength: %.6f m\n', wavelength_m);
fprintf('PRF 1 / PRF 2: %.1f / %.1f kHz\n', ...
    primary_prf_hz/1e3, secondary_prf_hz/1e3);
fprintf('First positive blind speed, PRF 1: %.6f m/s\n', ...
    primary_blind_speed_spacing_mps);
fprintf('First positive blind speed, PRF 2: %.6f m/s\n', ...
    secondary_blind_speed_spacing_mps);
fprintf('Baseline target Doppler: %.3f Hz\n', ...
    baseline_target_doppler_hz);
fprintf('Normalized gain at baseline, PRF 1: %.6f\n', ...
    primary_theory_gain/2);
fprintf('Normalized gain at baseline, PRF 2: %.6f\n', ...
    secondary_theory_gain/2);
fprintf('Broken / recovered fused gain: %.6f / %.6f\n', ...
    broken_baseline_gain_normalized, recovered_baseline_gain_normalized);
fprintf(['Interpretation: the moving target repeats pulse-to-pulse at PRF 1, ' ...
    'but PRF 2 moves that nonzero null.\n']);
