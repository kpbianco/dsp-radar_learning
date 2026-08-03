%% P37: Build a Pulse-Doppler Data Matrix
% Guiding question:
% What are fast time and slow time in a radar data block?
% Matrix convention: rows are fast-time/range samples and columns are pulses.
% Positive radial velocity means approaching the radar.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P37'));

%% Visible deterministic controls and resource ceilings
random_seed = 3701;
speed_of_light_mps = 299792458;
carrier_frequency_hz = 10e9;
sample_rate_hz = 20e6;
pulse_repetition_frequency_hz = 5e3;
fast_time_sample_count = 256;
pulse_count = 32;
target_ranges_m = [450 900 1200];
target_velocities_mps = [0 12 -18];
target_amplitudes = [1.0 0.75 0.55];
target_initial_phase_deg = [0 40 -30];
range_response_sigma_samples = 1.2;
noise_rms = 0.02;
selected_pulses = [1 16 32];
range_sweep_m = [300 750 1200];
velocity_sweep_mps = [-18 0 18];
comparison_tolerance = 1e-10;
max_fast_time_samples = 512;
max_pulse_count = 128;
max_target_count = 6;
max_sweep_cases = 7;
max_figure_groups = 6;
max_stored_numeric_values = 1000000;

%% Validate controls before allocating the data matrix
positive_controls = [speed_of_light_mps carrier_frequency_hz ...
    sample_rate_hz pulse_repetition_frequency_hz ...
    fast_time_sample_count pulse_count range_response_sigma_samples ...
    max_fast_time_samples max_pulse_count max_target_count ...
    max_sweep_cases max_figure_groups max_stored_numeric_values ...
    comparison_tolerance];
assert(all(isfinite(positive_controls)) && all(positive_controls > 0));
assert(isfinite(random_seed) && random_seed == floor(random_seed) && ...
    random_seed == 3701);
assert(isfinite(noise_rms) && noise_rms >= 0);
integer_controls = [fast_time_sample_count pulse_count selected_pulses ...
    max_fast_time_samples max_pulse_count max_target_count ...
    max_sweep_cases max_figure_groups max_stored_numeric_values];
assert(all(integer_controls == floor(integer_controls)));
assert(fast_time_sample_count >= 32 && ...
    fast_time_sample_count <= max_fast_time_samples);
assert(pulse_count >= 8 && pulse_count <= max_pulse_count && ...
    mod(pulse_count, 2) == 0);
assert(numel(target_ranges_m) >= 2 && ...
    numel(target_ranges_m) <= max_target_count);
assert(numel(target_ranges_m) == numel(target_velocities_mps) && ...
    numel(target_ranges_m) == numel(target_amplitudes) && ...
    numel(target_ranges_m) == numel(target_initial_phase_deg));
assert(all(isfinite(target_ranges_m)) && all(target_ranges_m > 0) && ...
    all(diff(target_ranges_m) > 0));
assert(all(isfinite(target_velocities_mps)));
assert(all(isfinite(target_amplitudes)) && all(target_amplitudes > 0));
assert(all(isfinite(target_initial_phase_deg)));
assert(numel(selected_pulses) >= 2 && ...
    numel(selected_pulses) <= max_sweep_cases && ...
    all(selected_pulses >= 1) && all(selected_pulses <= pulse_count) && ...
    all(diff(selected_pulses) > 0));
assert(numel(range_sweep_m) >= 2 && ...
    numel(range_sweep_m) <= max_sweep_cases && ...
    all(isfinite(range_sweep_m)) && all(range_sweep_m > 0) && ...
    all(diff(range_sweep_m) > 0));
assert(numel(velocity_sweep_mps) >= 3 && ...
    numel(velocity_sweep_mps) <= max_sweep_cases && ...
    all(isfinite(velocity_sweep_mps)) && ...
    all(diff(velocity_sweep_mps) > 0) && ...
    any(velocity_sweep_mps < 0) && any(velocity_sweep_mps == 0) && ...
    any(velocity_sweep_mps > 0));

%% Axes and target coordinates
wavelength_m = speed_of_light_mps/carrier_frequency_hz;
pulse_repetition_interval_s = 1/pulse_repetition_frequency_hz;
range_bin_spacing_m = speed_of_light_mps/(2*sample_rate_hz);
fast_time_coordinate_span_s = (fast_time_sample_count-1)/sample_rate_hz;
recorded_range_axis_span_m = speed_of_light_mps*...
    fast_time_coordinate_span_s/2;
prf_unambiguous_range_m = speed_of_light_mps/(...
    2*pulse_repetition_frequency_hz);
unambiguous_doppler_hz = pulse_repetition_frequency_hz/2;
unambiguous_velocity_mps = wavelength_m*...
    pulse_repetition_frequency_hz/4;

fast_time_index = (0:fast_time_sample_count-1).';
fast_time_s = fast_time_index/sample_rate_hz;
range_axis_m = speed_of_light_mps*fast_time_s/2;
pulse_index = 0:pulse_count-1;
slow_time_s = pulse_index*pulse_repetition_interval_s;

target_delay_samples = round(2*target_ranges_m/speed_of_light_mps*...
    sample_rate_hz);
target_range_bins = target_delay_samples+1;
range_response_margin_samples = ceil(4*range_response_sigma_samples);
assert(all(target_range_bins > range_response_margin_samples) && ...
    all(target_range_bins <= fast_time_sample_count-...
    range_response_margin_samples));
target_measured_ranges_m = range_axis_m(target_range_bins).';
target_range_errors_m = target_measured_ranges_m-target_ranges_m;
target_doppler_hz = 2*target_velocities_mps/wavelength_m;
target_phase_increment_rad = 2*pi*target_doppler_hz/...
    pulse_repetition_frequency_hz;
coherent_dwell_s = (pulse_count-1)*pulse_repetition_interval_s;
max_neglected_range_change_m = max(abs(target_velocities_mps))*...
    coherent_dwell_s;
max_neglected_range_migration_bins = max_neglected_range_change_m/...
    range_bin_spacing_m;

assert(fast_time_coordinate_span_s < pulse_repetition_interval_s);
assert(recorded_range_axis_span_m < prf_unambiguous_range_m);
assert(numel(unique(target_range_bins)) == numel(target_range_bins));
assert(all(abs(target_range_errors_m) <= range_bin_spacing_m/2+...
    comparison_tolerance));
assert(all(abs(target_doppler_hz) < unambiguous_doppler_hz));
assert(all(abs(target_velocities_mps) < unambiguous_velocity_mps));
assert(max_neglected_range_migration_bins < 0.5);

estimated_stored_numeric_values = 12*fast_time_sample_count*pulse_count+...
    10*fast_time_sample_count*numel(range_sweep_m)+...
    10*pulse_count*numel(velocity_sweep_mps)+500;
assert(estimated_stored_numeric_values <= max_stored_numeric_values);
assert(max_figure_groups >= 6);

%% Baseline: form fast-time rows by slow-time pulse columns explicitly
target_count = numel(target_ranges_m);
clean_data_matrix = complex(zeros(fast_time_sample_count, pulse_count));
target_range_responses = zeros(fast_time_sample_count, target_count);
target_slow_time_sequences = complex(zeros(target_count, pulse_count));

for target_index = 1:target_count
    range_response = exp(-0.5*((fast_time_index-...
        target_delay_samples(target_index))/...
        range_response_sigma_samples).^2);
    slow_time_sequence = target_amplitudes(target_index)*exp(1j*(...
        target_initial_phase_deg(target_index)*pi/180+...
        2*pi*target_doppler_hz(target_index)*slow_time_s));
    target_range_responses(:, target_index) = range_response;
    target_slow_time_sequences(target_index, :) = slow_time_sequence;
    clean_data_matrix = clean_data_matrix+...
        range_response*slow_time_sequence;
end

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
complex_noise = noise_rms/sqrt(2)*(...
    randn(private_stream, fast_time_sample_count, pulse_count)+...
    1j*randn(private_stream, fast_time_sample_count, pulse_count));
data_matrix = clean_data_matrix+complex_noise;
assert(isequal(size(data_matrix), [fast_time_sample_count pulse_count]));

% Each selected row is one range cell sampled once per pulse in slow time.
selected_range_traces = data_matrix(target_range_bins, :);
measured_phase_increment_rad = zeros(1, target_count);
measured_doppler_hz = zeros(1, target_count);
for target_index = 1:target_count
    target_trace = selected_range_traces(target_index, :);
    adjacent_products = conj(target_trace(1:end-1)).*target_trace(2:end);
    measured_phase_increment_rad(target_index) = angle(sum(adjacent_products));
    measured_doppler_hz(target_index) = ...
        measured_phase_increment_rad(target_index)*...
        pulse_repetition_frequency_hz/(2*pi);
end
doppler_bin_spacing_hz = pulse_repetition_frequency_hz/pulse_count;
assert(all(abs(measured_doppler_hz-target_doppler_hz) < ...
    doppler_bin_spacing_hz/2));

figure('Name', 'P37 selected fast-time pulse columns', 'Tag', 'P37');
for plot_index = 1:numel(selected_pulses)
    subplot(numel(selected_pulses), 1, plot_index);
    selected_pulse = selected_pulses(plot_index);
    plot(range_axis_m, abs(data_matrix(:, selected_pulse)), ...
        'LineWidth', 1.1);
    hold on;
    plot(target_measured_ranges_m, ...
        abs(data_matrix(target_range_bins, selected_pulse)), ...
        'ro', 'LineWidth', 1.2);
    grid on;
    xlabel('Range from fast time (m)');
    ylabel('Relative magnitude');
    title(sprintf('Pulse column %d: delay peaks stay in the same rows', ...
        selected_pulse));
end

figure('Name', 'P37 selected slow-time range rows', 'Tag', 'P37');
for target_index = 1:target_count
    subplot(target_count, 1, target_index);
    unwrapped_phase_rad = unwrap(angle(selected_range_traces(target_index, :)));
    plot(pulse_index, unwrapped_phase_rad, 'o-', 'LineWidth', 1.1);
    grid on;
    xlabel('Pulse index (slow time)');
    ylabel('Unwrapped phase (rad)');
    title(sprintf('Range row %d (%.1f m): %.1f Hz Doppler', ...
        target_range_bins(target_index), ...
        target_measured_ranges_m(target_index), ...
        target_doppler_hz(target_index)));
end

matrix_magnitude_db = 20*log10(abs(data_matrix)/...
    max(abs(data_matrix(:)))+eps);
figure('Name', 'P37 pulse-Doppler data matrix', 'Tag', 'P37');
imagesc(pulse_index, range_axis_m, matrix_magnitude_db);
axis xy;
colorbar;
caxis([-50 0]);
xlabel('Pulse index (slow time / Doppler history)');
ylabel('Range from fast time (m)');
title('Rows contain delay/range; columns contain coherent pulse history');

%% Sweep 1: change only target range and watch the fast-time row move
range_sweep_bins = round(2*range_sweep_m/speed_of_light_mps*...
    sample_rate_hz)+1;
assert(all(range_sweep_bins > range_response_margin_samples) && ...
    all(range_sweep_bins <= fast_time_sample_count-...
    range_response_margin_samples));
range_sweep_measured_m = range_axis_m(range_sweep_bins).';
range_sweep_profiles = zeros(fast_time_sample_count, numel(range_sweep_m));
for sweep_index = 1:numel(range_sweep_m)
    candidate_delay_sample = range_sweep_bins(sweep_index)-1;
    range_sweep_profiles(:, sweep_index) = exp(-0.5*((...
        fast_time_index-candidate_delay_sample)/...
        range_response_sigma_samples).^2);
end
assert(all(diff(range_sweep_bins) > 0));
assert(all(abs(range_sweep_measured_m-range_sweep_m) <= ...
    range_bin_spacing_m/2+comparison_tolerance));

figure('Name', 'P37 range-to-row sweep', 'Tag', 'P37');
plot(range_axis_m, range_sweep_profiles, 'LineWidth', 1.2);
grid on;
xlabel('Range from fast time (m)');
ylabel('Ideal relative magnitude');
title('Changing range moves the response along fast-time rows');
legend(compose('True range %.0f m', range_sweep_m), ...
    'Location', 'best');

%% Sweep 2: change only velocity and watch slow-time phase change
velocity_sweep_doppler_hz = 2*velocity_sweep_mps/wavelength_m;
velocity_sweep_phase_increment_rad = 2*pi*...
    velocity_sweep_doppler_hz/pulse_repetition_frequency_hz;
velocity_sweep_sequences = complex(zeros(numel(velocity_sweep_mps), ...
    pulse_count));
for sweep_index = 1:numel(velocity_sweep_mps)
    velocity_sweep_sequences(sweep_index, :) = exp(1j*(...
        2*pi*velocity_sweep_doppler_hz(sweep_index)*slow_time_s));
end
assert(all(abs(velocity_sweep_doppler_hz) < unambiguous_doppler_hz));
assert(all(diff(velocity_sweep_phase_increment_rad) > 0));
assert(all(all(abs(abs(velocity_sweep_sequences)-1) <= ...
    comparison_tolerance)));

figure('Name', 'P37 velocity-to-column-phase sweep', 'Tag', 'P37');
plot(pulse_index, unwrap(angle(velocity_sweep_sequences), [], 2).', ...
    'LineWidth', 1.2);
grid on;
xlabel('Pulse index (slow time)');
ylabel('Unwrapped phase (rad)');
title('Velocity changes phase across columns, not the target range row');
legend(compose('Velocity %+.0f m/s', velocity_sweep_mps), ...
    'Location', 'best');

%% Intentionally broken case: discard complex phase before slow-time use
reference_target_index = 2;
reference_range_bin = target_range_bins(reference_target_index);
coherent_reference_trace = data_matrix(reference_range_bin, :);
broken_data_matrix = abs(data_matrix);
broken_reference_trace = broken_data_matrix(reference_range_bin, :);
broken_adjacent_products = conj(broken_reference_trace(1:end-1)).*...
    broken_reference_trace(2:end);
broken_phase_increment_rad = angle(sum(broken_adjacent_products));

slow_time_window = 0.5-0.5*cos(2*pi*pulse_index/(pulse_count-1));
doppler_axis_hz = (-pulse_count/2:pulse_count/2-1)*...
    pulse_repetition_frequency_hz/pulse_count;
coherent_spectrum = fftshift(fft(coherent_reference_trace.*...
    slow_time_window, pulse_count));
broken_spectrum = fftshift(fft(broken_reference_trace.*...
    slow_time_window, pulse_count));
[~, coherent_peak_index] = max(abs(coherent_spectrum));
[~, broken_peak_index] = max(abs(broken_spectrum));
coherent_peak_doppler_hz = doppler_axis_hz(coherent_peak_index);
broken_peak_doppler_hz = doppler_axis_hz(broken_peak_index);
broken_model_valid = false;
assert(abs(broken_phase_increment_rad) <= comparison_tolerance);
assert(broken_peak_doppler_hz == 0);

%% Recovery: restore complex matrix orientation and private-seed noise
recovered_stream = RandStream('mt19937ar', 'Seed', random_seed);
recovered_noise = noise_rms/sqrt(2)*(...
    randn(recovered_stream, fast_time_sample_count, pulse_count)+...
    1j*randn(recovered_stream, fast_time_sample_count, pulse_count));
recovered_data_matrix = clean_data_matrix+recovered_noise;
recovered_reference_trace = recovered_data_matrix(reference_range_bin, :);
recovered_adjacent_products = conj(recovered_reference_trace(1:end-1)).*...
    recovered_reference_trace(2:end);
recovered_phase_increment_rad = angle(sum(recovered_adjacent_products));
recovered_model_valid = true;
assert(isequal(recovered_data_matrix, data_matrix));
assert(abs(recovered_phase_increment_rad-...
    measured_phase_increment_rad(reference_target_index)) <= ...
    comparison_tolerance);

figure('Name', 'P37 phase-loss failure and recovery', 'Tag', 'P37');
subplot(1, 2, 1);
plot(pulse_index, unwrap(angle(coherent_reference_trace)), ...
    'o-', 'LineWidth', 1.1);
hold on;
plot(pulse_index, unwrap(angle(broken_reference_trace)), ...
    '--', 'LineWidth', 1.2);
grid on;
xlabel('Pulse index (slow time)');
ylabel('Unwrapped phase (rad)');
title('Magnitude preserves the row but erases Doppler phase');
legend('Coherent complex row', 'Broken magnitude-only row', ...
    'Location', 'best');
subplot(1, 2, 2);
coherent_spectrum_db = 20*log10(abs(coherent_spectrum)/...
    max(abs(coherent_spectrum))+eps);
broken_spectrum_db = 20*log10(abs(broken_spectrum)/...
    max(abs(broken_spectrum))+eps);
plot(doppler_axis_hz, coherent_spectrum_db, 'LineWidth', 1.2);
hold on;
plot(doppler_axis_hz, broken_spectrum_db, '--', 'LineWidth', 1.2);
grid on;
xlabel('Slow-time Doppler frequency (Hz)');
ylabel('Normalized magnitude (dB)');
title('Broken processing moves the target toward zero Doppler');
legend('Coherent complex row', 'Broken magnitude-only row', ...
    'Location', 'best');
ylim([-60 3]);

%% Publish concise metrics for inspection and later lessons
results = struct();
results.random_seed = random_seed;
results.matrix_convention = ...
    'fast-time/range rows by slow-time/pulse columns';
results.sign_convention = 'positive radial velocity means approaching';
results.matrix_size = size(data_matrix);
results.wavelength_m = wavelength_m;
results.range_bin_spacing_m = range_bin_spacing_m;
results.fast_time_coordinate_span_s = fast_time_coordinate_span_s;
results.recorded_range_axis_span_m = recorded_range_axis_span_m;
results.prf_unambiguous_range_m = prf_unambiguous_range_m;
results.pulse_repetition_interval_s = pulse_repetition_interval_s;
results.coherent_dwell_s = coherent_dwell_s;
results.max_neglected_range_change_m = max_neglected_range_change_m;
results.max_neglected_range_migration_bins = ...
    max_neglected_range_migration_bins;
results.unambiguous_doppler_hz = unambiguous_doppler_hz;
results.unambiguous_velocity_mps = unambiguous_velocity_mps;
results.target_ranges_m = target_ranges_m;
results.target_range_bins = target_range_bins;
results.target_measured_ranges_m = target_measured_ranges_m;
results.target_range_errors_m = target_range_errors_m;
results.target_velocities_mps = target_velocities_mps;
results.target_doppler_hz = target_doppler_hz;
results.target_phase_increment_rad = target_phase_increment_rad;
results.measured_doppler_hz = measured_doppler_hz;
results.range_sweep_m = range_sweep_m;
results.range_sweep_bins = range_sweep_bins;
results.velocity_sweep_mps = velocity_sweep_mps;
results.velocity_sweep_phase_increment_rad = ...
    velocity_sweep_phase_increment_rad;
results.reference_target_index = reference_target_index;
results.coherent_peak_doppler_hz = coherent_peak_doppler_hz;
results.broken_phase_increment_rad = broken_phase_increment_rad;
results.broken_peak_doppler_hz = broken_peak_doppler_hz;
results.broken_model_valid = broken_model_valid;
results.recovered_phase_increment_rad = recovered_phase_increment_rad;
results.recovered_model_valid = recovered_model_valid;
results.estimated_stored_numeric_values = estimated_stored_numeric_values;

fprintf('\nP37 baseline: fast-time rows by slow-time columns\n');
fprintf('  Matrix size: %d range samples x %d coherent pulses\n', ...
    fast_time_sample_count, pulse_count);
fprintf('  Fast-time spacing: %.3f ns; range-bin spacing: %.3f m\n', ...
    1e9/sample_rate_hz, range_bin_spacing_m);
fprintf('  Slow-time spacing (PRI): %.3f microseconds; PRF: %.3f kHz\n', ...
    pulse_repetition_interval_s*1e6, ...
    pulse_repetition_frequency_hz/1e3);
for target_index = 1:target_count
    fprintf(['  Target %d: true/measured range %.1f/%.1f m, row %d, ' ...
        'velocity %+.1f m/s, Doppler %+.1f Hz\n'], ...
        target_index, target_ranges_m(target_index), ...
        target_measured_ranges_m(target_index), ...
        target_range_bins(target_index), ...
        target_velocities_mps(target_index), ...
        target_doppler_hz(target_index));
end
fprintf('  Broken / recovered valid: %d / %d\n', ...
    broken_model_valid, recovered_model_valid);
