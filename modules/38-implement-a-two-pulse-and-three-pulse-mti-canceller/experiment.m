%% P38: Implement a Two-Pulse and Three-Pulse MTI Canceller
% Guiding question:
% How do simple delay-line cancellers remove stationary clutter?
% Matrix convention: rows are fast-time/range samples and columns are pulses.
% Positive radial velocity means approaching the radar.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P38'));

%% Visible deterministic controls and resource ceilings
random_seed = 3801;
speed_of_light_mps = 299792458;
carrier_frequency_hz = 10e9;
sample_rate_hz = 20e6;
pulse_repetition_frequency_hz = 5e3;
fast_time_sample_count = 128;
pulse_count = 64;
clutter_range_bins = [25 63 100];
clutter_amplitudes = [20 12 8];
clutter_initial_phase_deg = [0 50 -35];
clutter_width_samples = 1.8;
target_range_bins = [63 92];
target_velocities_mps = [3 15];
target_amplitudes = [1.0 0.8];
target_initial_phase_deg = [25 -45];
target_width_samples = 1.2;
noise_rms = 0.08;
velocity_sweep_mps = [-30 -15 -3 0 3 15 30];
prf_sweep_hz = [3e3 4e3 5e3 7e3 9e3];
prf_sweep_target_velocity_mps = 12;
response_sample_count = 1001;
comparison_tolerance = 1e-10;
max_fast_time_samples = 256;
max_pulse_count = 128;
max_component_count = 8;
max_sweep_cases = 9;
max_response_samples = 2001;
max_figure_groups = 6;
max_stored_numeric_values = 1000000;

%% Validate controls before allocating matrices or indexing range rows
positive_controls = [speed_of_light_mps carrier_frequency_hz ...
    sample_rate_hz pulse_repetition_frequency_hz fast_time_sample_count ...
    pulse_count clutter_width_samples target_width_samples ...
    response_sample_count comparison_tolerance max_fast_time_samples ...
    max_pulse_count max_component_count max_sweep_cases ...
    max_response_samples max_figure_groups max_stored_numeric_values];
assert(all(isfinite(positive_controls)) && all(positive_controls > 0));
assert(isfinite(random_seed) && random_seed == floor(random_seed) && ...
    random_seed == 3801);
assert(isfinite(noise_rms) && noise_rms >= 0);
integer_controls = [fast_time_sample_count pulse_count clutter_range_bins ...
    target_range_bins response_sample_count max_fast_time_samples ...
    max_pulse_count max_component_count max_sweep_cases ...
    max_response_samples max_figure_groups max_stored_numeric_values];
assert(all(integer_controls == floor(integer_controls)));
assert(fast_time_sample_count >= 32 && ...
    fast_time_sample_count <= max_fast_time_samples);
assert(pulse_count >= 8 && pulse_count <= max_pulse_count && ...
    mod(pulse_count, 2) == 0);
assert(numel(clutter_range_bins) >= 1 && ...
    numel(clutter_range_bins) <= max_component_count);
assert(numel(clutter_range_bins) == numel(clutter_amplitudes) && ...
    numel(clutter_range_bins) == numel(clutter_initial_phase_deg));
assert(numel(target_range_bins) >= 1 && ...
    numel(target_range_bins) <= max_component_count);
assert(numel(target_range_bins) == numel(target_velocities_mps) && ...
    numel(target_range_bins) == numel(target_amplitudes) && ...
    numel(target_range_bins) == numel(target_initial_phase_deg));
assert(all(clutter_range_bins >= 1) && ...
    all(clutter_range_bins <= fast_time_sample_count) && ...
    numel(unique(clutter_range_bins)) == numel(clutter_range_bins));
assert(all(target_range_bins >= 1) && ...
    all(target_range_bins <= fast_time_sample_count) && ...
    numel(unique(target_range_bins)) == numel(target_range_bins));
assert(all(isfinite(clutter_amplitudes)) && all(clutter_amplitudes > 0));
assert(all(isfinite(clutter_initial_phase_deg)));
assert(all(isfinite(target_velocities_mps)));
assert(all(isfinite(target_amplitudes)) && all(target_amplitudes > 0));
assert(all(isfinite(target_initial_phase_deg)));
assert(numel(velocity_sweep_mps) >= 3 && ...
    numel(velocity_sweep_mps) <= max_sweep_cases && ...
    all(isfinite(velocity_sweep_mps)) && ...
    all(diff(velocity_sweep_mps) > 0) && ...
    any(velocity_sweep_mps < 0) && any(velocity_sweep_mps == 0) && ...
    any(velocity_sweep_mps > 0));
assert(numel(prf_sweep_hz) >= 3 && ...
    numel(prf_sweep_hz) <= max_sweep_cases && ...
    all(isfinite(prf_sweep_hz)) && all(prf_sweep_hz > 0) && ...
    all(diff(prf_sweep_hz) > 0));
assert(isfinite(prf_sweep_target_velocity_mps) && ...
    prf_sweep_target_velocity_mps ~= 0);
assert(response_sample_count <= max_response_samples && ...
    mod(response_sample_count, 2) == 1);

%% Physical axes, Doppler coordinates, and bounded model assumptions
wavelength_m = speed_of_light_mps/carrier_frequency_hz;
pulse_repetition_interval_s = 1/pulse_repetition_frequency_hz;
range_bin_spacing_m = speed_of_light_mps/(2*sample_rate_hz);
range_axis_m = (0:fast_time_sample_count-1).'*range_bin_spacing_m;
pulse_index = 0:pulse_count-1;
slow_time_s = pulse_index*pulse_repetition_interval_s;
target_doppler_hz = 2*target_velocities_mps/wavelength_m;
target_phase_increment_rad = 2*pi*target_doppler_hz/...
    pulse_repetition_frequency_hz;
unambiguous_doppler_hz = pulse_repetition_frequency_hz/2;
unambiguous_velocity_mps = wavelength_m*pulse_repetition_frequency_hz/4;
blind_speed_spacing_mps = wavelength_m*pulse_repetition_frequency_hz/2;
coherent_dwell_s = (pulse_count-1)*pulse_repetition_interval_s;
max_range_migration_bins = max(abs(target_velocities_mps))*...
    coherent_dwell_s/range_bin_spacing_m;

assert(all(abs(target_doppler_hz) < unambiguous_doppler_hz));
assert(all(abs(target_velocities_mps) < unambiguous_velocity_mps));
assert(max_range_migration_bins < 0.5);
assert(all(abs(2*velocity_sweep_mps/wavelength_m) < ...
    unambiguous_doppler_hz));
prf_sweep_target_doppler_hz = 2*prf_sweep_target_velocity_mps/...
    wavelength_m;
assert(all(abs(prf_sweep_target_doppler_hz) < prf_sweep_hz/2));

estimated_stored_numeric_values = ...
    28*fast_time_sample_count*pulse_count+...
    20*response_sample_count+...
    50*(numel(velocity_sweep_mps)+numel(prf_sweep_hz));
assert(estimated_stored_numeric_values <= max_stored_numeric_values);
assert(max_figure_groups >= 6);

%% Baseline: strong stationary clutter plus weaker moving targets and noise
fast_time_index = (0:fast_time_sample_count-1).';
clutter_profile = complex(zeros(fast_time_sample_count, 1));
for clutter_index = 1:numel(clutter_range_bins)
    envelope = exp(-0.5*((fast_time_index-(...
        clutter_range_bins(clutter_index)-1))/clutter_width_samples).^2);
    clutter_profile = clutter_profile+clutter_amplitudes(clutter_index)*...
        exp(1j*clutter_initial_phase_deg(clutter_index)*pi/180)*envelope;
end
clutter_matrix = clutter_profile*ones(1, pulse_count);

target_count = numel(target_range_bins);
target_components = complex(zeros(fast_time_sample_count, pulse_count, ...
    target_count));
target_matrix = complex(zeros(fast_time_sample_count, pulse_count));
for target_index = 1:target_count
    range_envelope = exp(-0.5*((fast_time_index-(...
        target_range_bins(target_index)-1))/target_width_samples).^2);
    slow_time_sequence = target_amplitudes(target_index)*exp(1j*(...
        target_initial_phase_deg(target_index)*pi/180+...
        2*pi*target_doppler_hz(target_index)*slow_time_s));
    target_components(:, :, target_index) = ...
        range_envelope*slow_time_sequence;
    target_matrix = target_matrix+target_components(:, :, target_index);
end

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
noise_matrix = noise_rms/sqrt(2)*(...
    randn(private_stream, fast_time_sample_count, pulse_count)+...
    1j*randn(private_stream, fast_time_sample_count, pulse_count));
data_matrix = clutter_matrix+target_matrix+noise_matrix;
assert(isequal(size(data_matrix), [fast_time_sample_count pulse_count]));

figure('Name', 'P38 baseline slow-time scene', 'Tag', 'P38');
subplot(1, 2, 1);
imagesc(pulse_index, range_axis_m, 20*log10(abs(data_matrix)/...
    max(abs(data_matrix(:)))+eps));
axis xy;
colorbar;
caxis([-50 0]);
xlabel('Pulse index (slow time)');
ylabel('Range from fast time (m)');
title('Strong stationary clutter masks weaker moving targets');
subplot(1, 2, 2);
plot(pulse_index, real(data_matrix(target_range_bins(1), :)), ...
    'LineWidth', 1.1);
hold on;
plot(pulse_index, real(target_components(target_range_bins(1), :, 1)), ...
    '--', 'LineWidth', 1.2);
grid on;
xlabel('Pulse index (slow time)');
ylabel('In-phase amplitude');
title('Target 1 shares a range cell with stationary clutter');
legend('Observed clutter + target + noise', 'Moving target alone', ...
    'Location', 'best');

%% Apply transparent two-pulse and three-pulse cancellers along slow time
two_pulse_coefficients = [1 -1];
three_pulse_coefficients = [1 -2 1];
two_pulse_output = data_matrix(:, 2:end)-data_matrix(:, 1:end-1);
three_pulse_output = data_matrix(:, 3:end)-...
    2*data_matrix(:, 2:end-1)+data_matrix(:, 1:end-2);

two_pulse_clutter = clutter_matrix(:, 2:end)-clutter_matrix(:, 1:end-1);
three_pulse_clutter = clutter_matrix(:, 3:end)-...
    2*clutter_matrix(:, 2:end-1)+clutter_matrix(:, 1:end-2);
two_pulse_noise = noise_matrix(:, 2:end)-noise_matrix(:, 1:end-1);
three_pulse_noise = noise_matrix(:, 3:end)-...
    2*noise_matrix(:, 2:end-1)+noise_matrix(:, 1:end-2);

clutter_input_rms = sqrt(mean(abs(clutter_matrix(:)).^2));
two_pulse_clutter_residual_ratio = ...
    sqrt(mean(abs(two_pulse_clutter(:)).^2))/clutter_input_rms;
three_pulse_clutter_residual_ratio = ...
    sqrt(mean(abs(three_pulse_clutter(:)).^2))/clutter_input_rms;
assert(two_pulse_clutter_residual_ratio <= comparison_tolerance);
assert(three_pulse_clutter_residual_ratio <= comparison_tolerance);

target_input_rms = zeros(1, target_count);
two_pulse_target_gain = zeros(1, target_count);
three_pulse_target_gain = zeros(1, target_count);
for target_index = 1:target_count
    component = target_components(:, :, target_index);
    component_two_pulse = component(:, 2:end)-component(:, 1:end-1);
    component_three_pulse = component(:, 3:end)-...
        2*component(:, 2:end-1)+component(:, 1:end-2);
    target_input_rms(target_index) = sqrt(mean(abs(component(:)).^2));
    two_pulse_target_gain(target_index) = ...
        sqrt(mean(abs(component_two_pulse(:)).^2))/...
        target_input_rms(target_index);
    three_pulse_target_gain(target_index) = ...
        sqrt(mean(abs(component_three_pulse(:)).^2))/...
        target_input_rms(target_index);
end
theoretical_two_pulse_target_gain = ...
    2*abs(sin(target_phase_increment_rad/2));
theoretical_three_pulse_target_gain = ...
    4*sin(target_phase_increment_rad/2).^2;
assert(all(abs(two_pulse_target_gain-...
    theoretical_two_pulse_target_gain) <= comparison_tolerance));
assert(all(abs(three_pulse_target_gain-...
    theoretical_three_pulse_target_gain) <= comparison_tolerance));

noise_input_power = mean(abs(noise_matrix(:)).^2);
two_pulse_noise_power = mean(abs(two_pulse_noise(:)).^2);
three_pulse_noise_power = mean(abs(three_pulse_noise(:)).^2);
two_pulse_noise_power_gain_theory = sum(two_pulse_coefficients.^2);
three_pulse_noise_power_gain_theory = sum(three_pulse_coefficients.^2);
two_pulse_noise_power_gain_measured = two_pulse_noise_power/noise_input_power;
three_pulse_noise_power_gain_measured = ...
    three_pulse_noise_power/noise_input_power;
assert(abs(two_pulse_noise_power_gain_measured-...
    two_pulse_noise_power_gain_theory)/...
    two_pulse_noise_power_gain_theory < 0.15);
assert(abs(three_pulse_noise_power_gain_measured-...
    three_pulse_noise_power_gain_theory)/...
    three_pulse_noise_power_gain_theory < 0.15);

%% Frequency response: DC and every integer PRF are nulls
normalized_doppler = linspace(-1, 1, response_sample_count);
response_phase_rad = 2*pi*normalized_doppler;
two_pulse_response = 1-exp(-1j*response_phase_rad);
three_pulse_response = (1-exp(-1j*response_phase_rad)).^2;
two_pulse_response_magnitude = abs(two_pulse_response);
three_pulse_response_magnitude = abs(three_pulse_response);
response_doppler_hz = normalized_doppler*...
    pulse_repetition_frequency_hz;
response_velocity_mps = wavelength_m*response_doppler_hz/2;
dc_index = (response_sample_count+1)/2;
assert(two_pulse_response_magnitude(dc_index) <= comparison_tolerance);
assert(three_pulse_response_magnitude(dc_index) <= comparison_tolerance);
assert(two_pulse_response_magnitude(1) <= comparison_tolerance && ...
    two_pulse_response_magnitude(end) <= comparison_tolerance);
assert(three_pulse_response_magnitude(1) <= comparison_tolerance && ...
    three_pulse_response_magnitude(end) <= comparison_tolerance);

figure('Name', 'P38 MTI frequency responses', 'Tag', 'P38');
subplot(2, 1, 1);
plot(response_doppler_hz, two_pulse_response_magnitude, ...
    'LineWidth', 1.2);
hold on;
plot(response_doppler_hz, three_pulse_response_magnitude, ...
    '--', 'LineWidth', 1.2);
grid on;
xlabel('Doppler frequency (Hz)');
ylabel('Amplitude gain');
title('Delay-line cancellers place periodic nulls at integer PRFs');
legend('Two-pulse: |1 - exp(-j\omega)|', ...
    'Three-pulse: |1 - exp(-j\omega)|^2', 'Location', 'best');
subplot(2, 1, 2);
plot(response_velocity_mps, 20*log10(max(...
    two_pulse_response_magnitude, 1e-6)), 'LineWidth', 1.2);
hold on;
plot(response_velocity_mps, 20*log10(max(...
    three_pulse_response_magnitude, 1e-6)), '--', 'LineWidth', 1.2);
grid on;
xlabel('Velocity equivalent at this PRF (m/s; aliases outside unambiguous interval)');
ylabel('Amplitude gain (dB)');
title('The second difference makes a broader, deeper near-zero notch');
legend('Two-pulse', 'Three-pulse', 'Location', 'best');
ylim([-120 15]);

%% Compare range profiles, target response, and noise cost
raw_range_rms = sqrt(mean(abs(data_matrix).^2, 2));
two_pulse_range_rms = sqrt(mean(abs(two_pulse_output).^2, 2));
three_pulse_range_rms = sqrt(mean(abs(three_pulse_output).^2, 2));
figure('Name', 'P38 clutter suppression across range', 'Tag', 'P38');
plot(range_axis_m, 20*log10(raw_range_rms+eps), 'LineWidth', 1.1);
hold on;
plot(range_axis_m, 20*log10(two_pulse_range_rms+eps), ...
    'LineWidth', 1.1);
plot(range_axis_m, 20*log10(three_pulse_range_rms+eps), ...
    '--', 'LineWidth', 1.1);
grid on;
xlabel('Range from fast time (m)');
ylabel('RMS magnitude (dB relative amplitude)');
title('Slow-time differences remove stationary clutter range peaks');
legend('Unfiltered', 'Two-pulse output', 'Three-pulse output', ...
    'Location', 'best');

two_pulse_target_snr_gain_db = 10*log10(...
    two_pulse_target_gain.^2/two_pulse_noise_power_gain_theory);
three_pulse_target_snr_gain_db = 10*log10(...
    three_pulse_target_gain.^2/three_pulse_noise_power_gain_theory);
figure('Name', 'P38 target and noise tradeoff', 'Tag', 'P38');
subplot(1, 2, 1);
bar(target_velocities_mps, [two_pulse_target_gain.' ...
    three_pulse_target_gain.']);
grid on;
xlabel('Target radial velocity (m/s)');
ylabel('Target amplitude gain');
title('Target gain depends on pulse-to-pulse phase change');
legend('Two-pulse', 'Three-pulse', 'Location', 'best');
subplot(1, 2, 2);
bar([two_pulse_noise_power_gain_theory ...
    three_pulse_noise_power_gain_theory; ...
    two_pulse_noise_power_gain_measured ...
    three_pulse_noise_power_gain_measured].');
grid on;
set(gca, 'XTickLabel', {'Two-pulse', 'Three-pulse'});
ylabel('White-noise power gain');
title('Differencing also amplifies and colors white noise');
legend('Theory', 'Seeded measurement', 'Location', 'best');

%% Sweep 1: change only target velocity
velocity_sweep_doppler_hz = 2*velocity_sweep_mps/wavelength_m;
velocity_sweep_phase_rad = 2*pi*velocity_sweep_doppler_hz/...
    pulse_repetition_frequency_hz;
velocity_sweep_two_pulse_gain = ...
    2*abs(sin(velocity_sweep_phase_rad/2));
velocity_sweep_three_pulse_gain = ...
    4*sin(velocity_sweep_phase_rad/2).^2;
assert(velocity_sweep_two_pulse_gain(velocity_sweep_mps == 0) == 0);
assert(velocity_sweep_three_pulse_gain(velocity_sweep_mps == 0) == 0);

%% Sweep 2: change only PRF for one physical target velocity
prf_sweep_phase_rad = 2*pi*prf_sweep_target_doppler_hz./prf_sweep_hz;
prf_sweep_two_pulse_gain = 2*abs(sin(prf_sweep_phase_rad/2));
prf_sweep_three_pulse_gain = 4*sin(prf_sweep_phase_rad/2).^2;
prf_sweep_unambiguous_velocity_mps = wavelength_m*prf_sweep_hz/4;
assert(all(diff(prf_sweep_two_pulse_gain) < 0));
assert(all(diff(prf_sweep_three_pulse_gain) < 0));
assert(all(diff(prf_sweep_unambiguous_velocity_mps) > 0));

figure('Name', 'P38 velocity and PRF sweeps', 'Tag', 'P38');
subplot(1, 2, 1);
plot(velocity_sweep_mps, velocity_sweep_two_pulse_gain, ...
    'o-', 'LineWidth', 1.2);
hold on;
plot(velocity_sweep_mps, velocity_sweep_three_pulse_gain, ...
    's--', 'LineWidth', 1.2);
grid on;
xlabel('Target radial velocity (m/s)');
ylabel('Amplitude gain');
title('Sweep 1: low-speed targets sit near the clutter notch');
legend('Two-pulse', 'Three-pulse', 'Location', 'best');
subplot(1, 2, 2);
plot(prf_sweep_hz/1e3, prf_sweep_two_pulse_gain, ...
    'o-', 'LineWidth', 1.2);
hold on;
plot(prf_sweep_hz/1e3, prf_sweep_three_pulse_gain, ...
    's--', 'LineWidth', 1.2);
grid on;
xlabel('Pulse repetition frequency (kHz)');
ylabel('Amplitude gain at fixed 12 m/s');
title('Sweep 2: higher PRF moves fixed Doppler closer to DC');
legend('Two-pulse', 'Three-pulse', 'Location', 'best');

%% Intentionally broken case: difference fast time instead of slow time
broken_fast_time_output = data_matrix(2:end, :)-data_matrix(1:end-1, :);
broken_fast_time_clutter = clutter_matrix(2:end, :)-...
    clutter_matrix(1:end-1, :);
broken_clutter_residual_ratio = sqrt(mean(...
    abs(broken_fast_time_clutter(:)).^2))/clutter_input_rms;
broken_model_valid = false;
assert(broken_clutter_residual_ratio > 0.05);

%% Recovery: restore slow-time axis and recreate the private-seed scene
recovered_stream = RandStream('mt19937ar', 'Seed', random_seed);
recovered_noise_matrix = noise_rms/sqrt(2)*(...
    randn(recovered_stream, fast_time_sample_count, pulse_count)+...
    1j*randn(recovered_stream, fast_time_sample_count, pulse_count));
recovered_data_matrix = clutter_matrix+target_matrix+...
    recovered_noise_matrix;
recovered_two_pulse_output = recovered_data_matrix(:, 2:end)-...
    recovered_data_matrix(:, 1:end-1);
recovered_three_pulse_output = recovered_data_matrix(:, 3:end)-...
    2*recovered_data_matrix(:, 2:end-1)+...
    recovered_data_matrix(:, 1:end-2);
recovered_model_valid = true;
assert(isequal(recovered_data_matrix, data_matrix));
assert(isequal(recovered_two_pulse_output, two_pulse_output));
assert(isequal(recovered_three_pulse_output, three_pulse_output));

broken_range_axis_m = 0.5*(range_axis_m(1:end-1)+range_axis_m(2:end));
broken_range_rms = sqrt(mean(abs(broken_fast_time_output).^2, 2));
figure('Name', 'P38 wrong-axis failure and recovery', 'Tag', 'P38');
plot(broken_range_axis_m, 20*log10(broken_range_rms+eps), ...
    'LineWidth', 1.1);
hold on;
plot(range_axis_m, 20*log10(two_pulse_range_rms+eps), ...
    'LineWidth', 1.1);
plot(range_axis_m, 20*log10(three_pulse_range_rms+eps), ...
    '--', 'LineWidth', 1.1);
grid on;
xlabel('Range from fast time (m)');
ylabel('RMS magnitude (dB relative amplitude)');
title('Wrong-axis differences create range edges; slow-time differences cancel clutter');
legend('Broken: difference range rows', 'Recovered two-pulse', ...
    'Recovered three-pulse', 'Location', 'best');

%% Publish concise metrics for inspection and later validation
results = struct();
results.random_seed = random_seed;
results.matrix_convention = ...
    'rows are fast-time/range samples; columns are slow-time pulses';
results.velocity_sign_convention = 'positive means approaching';
results.wavelength_m = wavelength_m;
results.pulse_repetition_frequency_hz = pulse_repetition_frequency_hz;
results.pulse_repetition_interval_s = pulse_repetition_interval_s;
results.range_bin_spacing_m = range_bin_spacing_m;
results.target_velocities_mps = target_velocities_mps;
results.target_doppler_hz = target_doppler_hz;
results.target_phase_increment_rad = target_phase_increment_rad;
results.unambiguous_velocity_mps = unambiguous_velocity_mps;
results.blind_speed_spacing_mps = blind_speed_spacing_mps;
results.two_pulse_coefficients = two_pulse_coefficients;
results.three_pulse_coefficients = three_pulse_coefficients;
results.two_pulse_clutter_residual_ratio = ...
    two_pulse_clutter_residual_ratio;
results.three_pulse_clutter_residual_ratio = ...
    three_pulse_clutter_residual_ratio;
results.two_pulse_target_gain = two_pulse_target_gain;
results.three_pulse_target_gain = three_pulse_target_gain;
results.two_pulse_target_snr_gain_db = two_pulse_target_snr_gain_db;
results.three_pulse_target_snr_gain_db = three_pulse_target_snr_gain_db;
results.noise_power_gain_theory = [two_pulse_noise_power_gain_theory ...
    three_pulse_noise_power_gain_theory];
results.noise_power_gain_measured = [two_pulse_noise_power_gain_measured ...
    three_pulse_noise_power_gain_measured];
results.velocity_sweep_mps = velocity_sweep_mps;
results.velocity_sweep_two_pulse_gain = velocity_sweep_two_pulse_gain;
results.velocity_sweep_three_pulse_gain = velocity_sweep_three_pulse_gain;
results.prf_sweep_hz = prf_sweep_hz;
results.prf_sweep_two_pulse_gain = prf_sweep_two_pulse_gain;
results.prf_sweep_three_pulse_gain = prf_sweep_three_pulse_gain;
results.broken_clutter_residual_ratio = broken_clutter_residual_ratio;
results.broken_model_valid = broken_model_valid;
results.recovered_model_valid = recovered_model_valid;
results.resource_estimate_numeric_values = estimated_stored_numeric_values;

fprintf('\nP38 two-pulse and three-pulse MTI canceller\n');
fprintf('  Seed: %d (private stream; recovery is exact)\n', random_seed);
fprintf('  PRF: %.1f Hz, wavelength: %.6f m\n', ...
    pulse_repetition_frequency_hz, wavelength_m);
fprintf('  Stationary-clutter residual ratios: two %.3g, three %.3g\n', ...
    two_pulse_clutter_residual_ratio, ...
    three_pulse_clutter_residual_ratio);
for target_index = 1:target_count
    fprintf(['  Target %d: velocity %+.1f m/s, Doppler %+.1f Hz, ' ...
        'two/three gains %.3f / %.3f\n'], target_index, ...
        target_velocities_mps(target_index), ...
        target_doppler_hz(target_index), ...
        two_pulse_target_gain(target_index), ...
        three_pulse_target_gain(target_index));
end
fprintf('  White-noise power gain theory: two %.1f, three %.1f\n', ...
    two_pulse_noise_power_gain_theory, ...
    three_pulse_noise_power_gain_theory);
fprintf('  Wrong-axis clutter residual ratio: %.3f (broken)\n', ...
    broken_clutter_residual_ratio);
fprintf('  Recovery flags: broken=%d, recovered=%d\n', ...
    broken_model_valid, recovered_model_valid);
