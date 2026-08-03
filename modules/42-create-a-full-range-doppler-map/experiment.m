%% P42: Create a Full Range-Doppler Map
% Guiding question:
% How do matched filtering and slow-time FFT combine to separate targets?
% Matrix convention: rows are fast-time/range samples; columns are pulses.
% Positive radial velocity means approaching the radar.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P42'));

%% Visible deterministic controls and immutable resource ceilings
random_seed = 4201;
speed_of_light_mps = 299792458;
carrier_frequency_hz = 10e9;
sample_rate_hz = 20e6;
pulse_repetition_frequency_hz = 4e3;
fast_time_sample_count = 512;
pulse_count = 64;
pulse_duration_s = 2.4e-6;
waveform_bandwidth_hz = 8e6;
target_ranges_m = [1200 1200 2400];
target_velocities_mps = [-7.5 10.3 10.3];
target_amplitudes = [1.00 0.80 0.65];
target_initial_phases_deg = [0 35 -50];
clutter_scatterer_count = 24;
clutter_amplitude = 0.055;
noise_rms = 0.35;
cpi_pulse_sweep = [16 32 64];
window_tone_offset_bins = 10.10;
display_floor_db = -55;
comparison_tolerance = 1e-10;
max_fast_time_samples = 512;
max_pulses = 128;
max_pulse_samples = 128;
max_targets = 6;
max_clutter_scatterers = 32;
max_sweep_cases = 6;
max_figure_groups = 7;
max_stored_numeric_values = 600000;

%% Reject malformed, ambiguous, or unbounded controls before allocation
positive_controls = [speed_of_light_mps carrier_frequency_hz sample_rate_hz ...
    pulse_repetition_frequency_hz fast_time_sample_count pulse_count ...
    pulse_duration_s waveform_bandwidth_hz clutter_scatterer_count ...
    max_fast_time_samples max_pulses max_pulse_samples max_targets ...
    max_clutter_scatterers max_sweep_cases max_figure_groups ...
    max_stored_numeric_values comparison_tolerance];
assert(all(isfinite(positive_controls)) && all(positive_controls > 0));
assert(~islogical(random_seed) && ~islogical(fast_time_sample_count) && ...
    ~islogical(pulse_count) && ~islogical(cpi_pulse_sweep));
assert(isfinite(random_seed) && random_seed == floor(random_seed) && ...
    random_seed == 4201);
integer_controls = [fast_time_sample_count pulse_count ...
    clutter_scatterer_count cpi_pulse_sweep max_fast_time_samples ...
    max_pulses max_pulse_samples max_targets max_clutter_scatterers ...
    max_sweep_cases max_figure_groups max_stored_numeric_values];
assert(all(integer_controls == floor(integer_controls)));
assert(max_fast_time_samples == 512 && max_pulses == 128 && ...
    max_pulse_samples == 128 && max_targets == 6 && ...
    max_clutter_scatterers == 32 && max_sweep_cases == 6 && ...
    max_figure_groups == 7 && max_stored_numeric_values == 600000);
assert(fast_time_sample_count >= 128 && ...
    fast_time_sample_count <= max_fast_time_samples);
assert(pulse_count >= 16 && pulse_count <= max_pulses && ...
    mod(pulse_count, 2) == 0);
assert(isfinite(noise_rms) && noise_rms >= 0 && ...
    isfinite(clutter_amplitude) && clutter_amplitude >= 0);
assert(isfinite(display_floor_db) && display_floor_db <= -30 && ...
    display_floor_db >= -100);
assert(numel(target_ranges_m) >= 3 && numel(target_ranges_m) <= max_targets);
assert(numel(target_ranges_m) == numel(target_velocities_mps) && ...
    numel(target_ranges_m) == numel(target_amplitudes) && ...
    numel(target_ranges_m) == numel(target_initial_phases_deg));
assert(all(isfinite(target_ranges_m)) && all(target_ranges_m > 0));
assert(all(isfinite(target_velocities_mps)) && ...
    all(isfinite(target_amplitudes)) && all(target_amplitudes > 0) && ...
    all(isfinite(target_initial_phases_deg)));
assert(target_ranges_m(1) == target_ranges_m(2));
assert(target_velocities_mps(2) == target_velocities_mps(3));
assert(clutter_scatterer_count >= 8 && ...
    clutter_scatterer_count <= max_clutter_scatterers);
assert(numel(cpi_pulse_sweep) >= 3 && ...
    numel(cpi_pulse_sweep) <= max_sweep_cases && ...
    all(cpi_pulse_sweep >= 16) && all(cpi_pulse_sweep <= pulse_count) && ...
    all(mod(cpi_pulse_sweep, 2) == 0) && ...
    all(diff(cpi_pulse_sweep) > 0) && ...
    cpi_pulse_sweep(end) == pulse_count);
assert(isfinite(window_tone_offset_bins) && ...
    abs(window_tone_offset_bins) < pulse_count/2-3);

%% Derive waveform, range, and Doppler coordinates
wavelength_m = speed_of_light_mps/carrier_frequency_hz;
pulse_sample_count = round(pulse_duration_s*sample_rate_hz);
assert(pulse_sample_count >= 16 && pulse_sample_count <= max_pulse_samples);
assert(waveform_bandwidth_hz < sample_rate_hz/2);
centered_pulse_time_s = ((0:pulse_sample_count-1).'-...
    (pulse_sample_count-1)/2)/sample_rate_hz;
chirp_rate_hz_per_s = waveform_bandwidth_hz/pulse_duration_s;
transmit_pulse = exp(1j*pi*chirp_rate_hz_per_s*...
    centered_pulse_time_s.^2);
matched_filter = conj(flipud(transmit_pulse));
range_sample_spacing_m = speed_of_light_mps/(2*sample_rate_hz);
nominal_range_resolution_m = speed_of_light_mps/(2*waveform_bandwidth_hz);
range_axis_m = (0:fast_time_sample_count-1).'*range_sample_spacing_m;
pulse_index = 0:pulse_count-1;
slow_time_s = pulse_index/pulse_repetition_frequency_hz;
doppler_axis_hz = (-pulse_count/2:pulse_count/2-1)*...
    pulse_repetition_frequency_hz/pulse_count;
velocity_axis_mps = doppler_axis_hz*wavelength_m/2;
doppler_bin_spacing_hz = pulse_repetition_frequency_hz/pulse_count;
velocity_bin_spacing_mps = doppler_bin_spacing_hz*wavelength_m/2;
unambiguous_range_m = speed_of_light_mps/(2*...
    pulse_repetition_frequency_hz);
unambiguous_velocity_mps = wavelength_m*...
    pulse_repetition_frequency_hz/4;
target_delay_samples = round(2*target_ranges_m/speed_of_light_mps*...
    sample_rate_hz);
target_range_bins = target_delay_samples+1;
target_measured_grid_ranges_m = range_axis_m(target_range_bins).';
target_doppler_hz = 2*target_velocities_mps/wavelength_m;
target_doppler_bins = zeros(size(target_doppler_hz));
for target_index = 1:numel(target_ranges_m)
    [~, target_doppler_bins(target_index)] = min(abs(...
        doppler_axis_hz-target_doppler_hz(target_index)));
end
assert(all(target_delay_samples >= 8));
assert(all(target_delay_samples+pulse_sample_count <= ...
    fast_time_sample_count));
assert(all(target_ranges_m < unambiguous_range_m));
assert(all(abs(target_velocities_mps) < unambiguous_velocity_mps));
assert(all(abs(target_measured_grid_ranges_m-target_ranges_m) <= ...
    range_sample_spacing_m/2+comparison_tolerance));
assert(numel(unique([target_range_bins(1) target_range_bins(3)])) == 2);
assert(numel(unique([target_doppler_bins(1) target_doppler_bins(2)])) == 2);

estimated_stored_numeric_values = ...
    14*fast_time_sample_count*pulse_count+...
    4*(fast_time_sample_count+pulse_count)+2000;
assert(estimated_stored_numeric_values <= max_stored_numeric_values);
assert(max_figure_groups >= 7);

%% Baseline scene: insert coherent moving targets and stationary clutter
target_count = numel(target_ranges_m);
clean_target_data = complex(zeros(fast_time_sample_count, pulse_count));
for target_index = 1:target_count
    echo_indices = target_delay_samples(target_index)+(1:pulse_sample_count);
    slow_time_phase = exp(1j*(target_initial_phases_deg(target_index)*...
        pi/180+2*pi*target_doppler_hz(target_index)*slow_time_s));
    clean_target_data(echo_indices, :) = ...
        clean_target_data(echo_indices, :)+...
        target_amplitudes(target_index)*transmit_pulse*slow_time_phase;
end

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
clutter_delay_samples = round(linspace(24, ...
    fast_time_sample_count-pulse_sample_count-12, ...
    clutter_scatterer_count));
clutter_range_taper = 1./sqrt(1+clutter_delay_samples/80);
clutter_coefficients = clutter_amplitude*clutter_range_taper.*...
    (randn(private_stream, 1, clutter_scatterer_count)+...
    1j*randn(private_stream, 1, clutter_scatterer_count))/sqrt(2);
clean_clutter_data = complex(zeros(fast_time_sample_count, pulse_count));
for clutter_index = 1:clutter_scatterer_count
    echo_indices = clutter_delay_samples(clutter_index)+...
        (1:pulse_sample_count);
    stationary_echo = clutter_coefficients(clutter_index)*transmit_pulse;
    clean_clutter_data(echo_indices, :) = ...
        clean_clutter_data(echo_indices, :)+repmat(stationary_echo, 1, pulse_count);
end
complex_noise = noise_rms/sqrt(2)*(...
    randn(private_stream, fast_time_sample_count, pulse_count)+...
    1j*randn(private_stream, fast_time_sample_count, pulse_count));
raw_data = clean_target_data+clean_clutter_data+complex_noise;
assert(isequal(size(raw_data), [fast_time_sample_count pulse_count]));

raw_data_db = 20*log10(max(abs(raw_data)/max(abs(raw_data(:))), ...
    10^(display_floor_db/20)));
instantaneous_frequency_mhz = chirp_rate_hz_per_s*...
    centered_pulse_time_s/1e6;
figure('Name', 'P42 raw coherent pulse train', 'Tag', 'P42');
subplot(2, 1, 1);
plot(1e6*centered_pulse_time_s, real(transmit_pulse), 'LineWidth', 1.0);
hold on;
plot(1e6*centered_pulse_time_s, instantaneous_frequency_mhz/...
    max(abs(instantaneous_frequency_mhz)), '--', 'LineWidth', 1.1);
grid on;
xlabel('Time inside pulse (microseconds)');
ylabel('I amplitude / normalized frequency');
title('LFM phase labels delay before matched filtering');
legend('Real transmit waveform', 'Normalized instantaneous frequency', ...
    'Location', 'best');
subplot(2, 1, 2);
imagesc(pulse_index, range_axis_m/1e3, raw_data_db);
axis xy;
colorbar;
caxis([display_floor_db 0]);
xlabel('Pulse index (slow time)');
ylabel('Apparent fast-time range (km)');
title('Raw long echoes, stationary clutter, and noise (normalized dB)');

%% Range compression: correlate each pulse along fast time only
% h[m]=conj(s[N-1-m]); y[r,p]=sum_m x[m,p] h[r-m].
% The full convolution peak includes N-1 filter samples. Selecting samples
% N through N+Nr-1 removes that fixed delay so row r maps to c*tau/2.
range_compressed = complex(zeros(fast_time_sample_count, pulse_count));
for pulse_number = 1:pulse_count
    full_response = conv(raw_data(:, pulse_number), matched_filter, 'full');
    range_compressed(:, pulse_number) = full_response(...
        pulse_sample_count:pulse_sample_count+fast_time_sample_count-1);
end
assert(isequal(size(range_compressed), size(raw_data)));
compressed_data_db = 20*log10(max(abs(range_compressed)/...
    max(abs(range_compressed(:))), 10^(display_floor_db/20)));
figure('Name', 'P42 range-compressed pulses', 'Tag', 'P42');
subplot(2, 1, 1);
plot(range_axis_m/1e3, abs(raw_data(:, 1))/max(abs(raw_data(:, 1))), ...
    'LineWidth', 1.0);
hold on;
plot(range_axis_m/1e3, abs(range_compressed(:, 1))/...
    max(abs(range_compressed(:, 1))), 'LineWidth', 1.2);
grid on;
xlabel('Range from fast time (km)');
ylabel('Normalized magnitude');
title('Matched filtering concentrates each long echo in range');
legend('Raw pulse 1', 'Compressed pulse 1', 'Location', 'best');
subplot(2, 1, 2);
imagesc(pulse_index, range_axis_m/1e3, compressed_data_db);
axis xy;
colorbar;
caxis([display_floor_db 0]);
xlabel('Pulse index (slow time)');
ylabel('Range after matched-filter alignment (km)');
title('Range-compressed matrix: range rows still retain pulse phase');

%% Slow-time windows and the Doppler spectrum of the shared range row
rectangular_window = ones(1, pulse_count);
hann_window = 0.5-0.5*cos(2*pi*pulse_index/(pulse_count-1));
shared_range_bin = target_range_bins(1);
shared_range_trace = range_compressed(shared_range_bin, :);
rectangular_shared_spectrum = fftshift(fft(shared_range_trace.*...
    rectangular_window, pulse_count))/sum(rectangular_window);
hann_shared_spectrum = fftshift(fft(shared_range_trace.*hann_window, ...
    pulse_count))/sum(hann_window);
shared_reference = max(abs([rectangular_shared_spectrum ...
    hann_shared_spectrum]));
figure('Name', 'P42 slow-time window and shared range row', 'Tag', 'P42');
subplot(2, 1, 1);
plot(pulse_index, rectangular_window, 'LineWidth', 1.1);
hold on;
plot(pulse_index, hann_window, 'LineWidth', 1.2);
grid on;
xlabel('Pulse index (slow time)');
ylabel('Window weight');
title('Window weights multiply each range row before its Doppler FFT');
legend('Rectangular', 'Hann', 'Location', 'best');
subplot(2, 1, 2);
plot(velocity_axis_mps, 20*log10(max(abs(...
    rectangular_shared_spectrum)/shared_reference, ...
    10^(display_floor_db/20))), 'LineWidth', 1.0);
hold on;
plot(velocity_axis_mps, 20*log10(max(abs(hann_shared_spectrum)/...
    shared_reference, 10^(display_floor_db/20))), 'LineWidth', 1.2);
grid on;
xlabel('Radial velocity (m/s, positive approaching)');
ylabel('Coherent-gain-normalized magnitude (dB)');
title('Two targets at one range separate through slow-time phase');
legend('Rectangular', 'Hann', 'Location', 'best');
ylim([display_floor_db 3]);

%% Final range-Doppler map: FFT across columns (dimension 2)
windowed_range_data = range_compressed.*hann_window;
range_doppler_complex = fftshift(fft(windowed_range_data, ...
    pulse_count, 2), 2)/sum(hann_window);
range_doppler_db = 20*log10(max(abs(range_doppler_complex)/...
    max(abs(range_doppler_complex(:))), 10^(display_floor_db/20)));
measured_target_ranges_m = zeros(1, target_count);
measured_target_velocities_mps = zeros(1, target_count);
measured_target_peak_indices = zeros(target_count, 2);
target_peak_magnitude = zeros(1, target_count);
search_range_radius_bins = ceil(1.5*nominal_range_resolution_m/...
    range_sample_spacing_m);
search_doppler_radius_bins = 2;
for target_index = 1:target_count
    range_indices = max(1, target_range_bins(target_index)-...
        search_range_radius_bins):min(fast_time_sample_count, ...
        target_range_bins(target_index)+search_range_radius_bins);
    doppler_indices = max(1, target_doppler_bins(target_index)-...
        search_doppler_radius_bins):min(pulse_count, ...
        target_doppler_bins(target_index)+search_doppler_radius_bins);
    local_map = abs(range_doppler_complex(range_indices, doppler_indices));
    [~, local_linear_index] = max(local_map(:));
    [local_range_index, local_doppler_index] = ind2sub(size(local_map), ...
        local_linear_index);
    measured_target_ranges_m(target_index) = ...
        range_axis_m(range_indices(local_range_index));
    measured_target_velocities_mps(target_index) = ...
        velocity_axis_mps(doppler_indices(local_doppler_index));
    measured_target_peak_indices(target_index, :) = ...
        [range_indices(local_range_index) ...
        doppler_indices(local_doppler_index)];
    target_peak_magnitude(target_index) = ...
        local_map(local_range_index, local_doppler_index);
end
map_median_magnitude = median(abs(range_doppler_complex(:)));
target_peak_to_median_db = 20*log10(target_peak_magnitude/...
    max(map_median_magnitude, eps));
assert(all(abs(measured_target_ranges_m-target_ranges_m) <= ...
    nominal_range_resolution_m));
assert(all(abs(measured_target_velocities_mps-target_velocities_mps) <= ...
    velocity_bin_spacing_mps+comparison_tolerance));
assert(size(unique(measured_target_peak_indices, 'rows'), 1) == ...
    target_count);
assert(all(target_peak_to_median_db > 20));

figure('Name', 'P42 full range-Doppler map', 'Tag', 'P42');
imagesc(velocity_axis_mps, range_axis_m/1e3, range_doppler_db);
axis xy;
colorbar;
caxis([display_floor_db 0]);
hold on;
plot(target_velocities_mps, target_ranges_m/1e3, 'wo', ...
    'MarkerSize', 8, 'LineWidth', 1.4);
xlabel('Radial velocity (m/s, positive approaching)');
ylabel('Range (km)');
title('Range-Doppler map after fast-time compression and slow-time FFT');

%% Sweep 1: change only CPI pulse count
cpi_case_count = numel(cpi_pulse_sweep);
cpi_velocity_spacing_mps = zeros(1, cpi_case_count);
cpi_duration_s = zeros(1, cpi_case_count);
figure('Name', 'P42 CPI-length sweep', 'Tag', 'P42');
for case_index = 1:cpi_case_count
    case_pulse_count = cpi_pulse_sweep(case_index);
    case_index_axis = 0:case_pulse_count-1;
    case_window = 0.5-0.5*cos(2*pi*case_index_axis/...
        (case_pulse_count-1));
    case_spectrum = fftshift(fft(shared_range_trace(1:case_pulse_count).*...
        case_window, case_pulse_count))/sum(case_window);
    case_velocity_axis_mps = (-case_pulse_count/2:...
        case_pulse_count/2-1)*pulse_repetition_frequency_hz/...
        case_pulse_count*wavelength_m/2;
    case_db = 20*log10(max(abs(case_spectrum)/max(abs(case_spectrum)), ...
        10^(display_floor_db/20)));
    cpi_velocity_spacing_mps(case_index) = wavelength_m/2*...
        pulse_repetition_frequency_hz/case_pulse_count;
    cpi_duration_s(case_index) = case_pulse_count/...
        pulse_repetition_frequency_hz;
    subplot(cpi_case_count, 1, case_index);
    plot(case_velocity_axis_mps, case_db, 'LineWidth', 1.2);
    grid on;
    xlabel('Radial velocity (m/s)');
    ylabel('Normalized magnitude (dB)');
    title(sprintf('%d pulses: CPI %.2f ms, velocity bins %.3f m/s', ...
        case_pulse_count, 1e3*cpi_duration_s(case_index), ...
        cpi_velocity_spacing_mps(case_index)));
    ylim([display_floor_db 3]);
end
assert(all(diff(cpi_velocity_spacing_mps) < 0));
assert(all(diff(cpi_duration_s) > 0));

%% Sweep 2: change only the slow-time window
ideal_slow_time_tone = exp(1j*2*pi*window_tone_offset_bins*...
    pulse_index/pulse_count);
window_names = {'Rectangular', 'Hann'};
window_bank = [rectangular_window; hann_window];
window_spectra_db = zeros(2, pulse_count);
window_mainlobe_width_bins = zeros(1, 2);
window_sidelobe_level_db = zeros(1, 2);
for window_index = 1:2
    case_window = window_bank(window_index, :);
    case_spectrum = fftshift(fft(ideal_slow_time_tone.*case_window, ...
        pulse_count))/sum(case_window);
    case_db = 20*log10(max(abs(case_spectrum)/max(abs(case_spectrum)), ...
        10^(display_floor_db/20)));
    window_spectra_db(window_index, :) = case_db;
    [~, peak_index] = max(abs(case_spectrum));
    window_mainlobe_width_bins(window_index) = sum(case_db >= -6);
    sidelobe_mask = true(1, pulse_count);
    guard_indices = max(1, peak_index-2):min(pulse_count, peak_index+2);
    sidelobe_mask(guard_indices) = false;
    window_sidelobe_level_db(window_index) = max(case_db(sidelobe_mask));
end
assert(window_sidelobe_level_db(2) < window_sidelobe_level_db(1));
assert(window_mainlobe_width_bins(2) > window_mainlobe_width_bins(1));
figure('Name', 'P42 slow-time window sweep', 'Tag', 'P42');
plot(velocity_axis_mps, window_spectra_db(1, :), 'LineWidth', 1.0);
hold on;
plot(velocity_axis_mps, window_spectra_db(2, :), 'LineWidth', 1.2);
grid on;
xlabel('Radial velocity (m/s)');
ylabel('Coherent-gain-normalized magnitude (dB)');
title('Hann lowers sidelobes but widens the Doppler mainlobe');
window_legend = {sprintf('%s: width %d bins, sidelobe %.1f dB', ...
    window_names{1}, window_mainlobe_width_bins(1), ...
    window_sidelobe_level_db(1)), ...
    sprintf('%s: width %d bins, sidelobe %.1f dB', ...
    window_names{2}, window_mainlobe_width_bins(2), ...
    window_sidelobe_level_db(2))};
legend(window_legend, 'Location', 'best');
ylim([display_floor_db 3]);

%% Intentionally broken case: transform fast time instead of slow time
% Dimension 1 is range. Its FFT creates fast-time frequency, not Doppler,
% so pulse columns remain pulse columns and no signed velocity axis exists.
broken_fast_time_spectrum = fftshift(fft(range_compressed, ...
    fast_time_sample_count, 1), 1);
broken_fast_frequency_axis = (-fast_time_sample_count/2:...
    fast_time_sample_count/2-1)/fast_time_sample_count;
broken_display_db = 20*log10(max(abs(broken_fast_time_spectrum)/...
    max(abs(broken_fast_time_spectrum(:))), 10^(display_floor_db/20)));
broken_model_valid = false;
assert(isequal(size(broken_fast_time_spectrum), ...
    [fast_time_sample_count pulse_count]));

%% Recovery: restore the slow-time window and dimension-2 FFT
recovered_range_doppler_complex = fftshift(fft(...
    range_compressed.*hann_window, pulse_count, 2), 2)/sum(hann_window);
recovered_model_valid = true;
recovery_error = max(abs(recovered_range_doppler_complex(:)-...
    range_doppler_complex(:)));
assert(recovery_error <= comparison_tolerance*...
    max(1, max(abs(range_doppler_complex(:)))));
figure('Name', 'P42 wrong-axis failure and recovery', 'Tag', 'P42');
subplot(1, 2, 1);
imagesc(pulse_index, broken_fast_frequency_axis, broken_display_db);
axis xy;
colorbar;
caxis([display_floor_db 0]);
xlabel('Pulse index (not Doppler)');
ylabel('Normalized fast-time frequency (cycles/sample)');
title('Broken: FFT across range rows');
subplot(1, 2, 2);
imagesc(velocity_axis_mps, range_axis_m/1e3, range_doppler_db);
axis xy;
colorbar;
caxis([display_floor_db 0]);
xlabel('Radial velocity (m/s)');
ylabel('Range (km)');
title('Recovered: FFT across slow-time columns');

%% Publish concise metrics for inspection and later detection lessons
results = struct();
results.random_seed = random_seed;
results.matrix_convention = ...
    'fast-time/range rows by slow-time/pulse columns';
results.sign_convention = 'positive radial velocity means approaching';
results.raw_matrix_size = size(raw_data);
results.range_compressed_matrix_size = size(range_compressed);
results.range_doppler_matrix_size = size(range_doppler_complex);
results.wavelength_m = wavelength_m;
results.pulse_sample_count = pulse_sample_count;
results.waveform_bandwidth_hz = waveform_bandwidth_hz;
results.nominal_range_resolution_m = nominal_range_resolution_m;
results.range_sample_spacing_m = range_sample_spacing_m;
results.unambiguous_range_m = unambiguous_range_m;
results.unambiguous_velocity_mps = unambiguous_velocity_mps;
results.doppler_bin_spacing_hz = doppler_bin_spacing_hz;
results.velocity_bin_spacing_mps = velocity_bin_spacing_mps;
results.target_ranges_m = target_ranges_m;
results.target_velocities_mps = target_velocities_mps;
results.target_measured_ranges_m = measured_target_ranges_m;
results.target_measured_velocities_mps = measured_target_velocities_mps;
results.target_peak_to_median_db = target_peak_to_median_db;
results.cpi_pulse_sweep = cpi_pulse_sweep;
results.cpi_duration_s = cpi_duration_s;
results.cpi_velocity_spacing_mps = cpi_velocity_spacing_mps;
results.window_names = window_names;
results.window_mainlobe_width_bins = window_mainlobe_width_bins;
results.window_sidelobe_level_db = window_sidelobe_level_db;
results.broken_operation = 'FFT along dimension 1 (fast time/range)';
results.broken_model_valid = broken_model_valid;
results.recovered_operation = ...
    'matched filtering along dimension 1, FFT along dimension 2';
results.recovered_model_valid = recovered_model_valid;
results.recovery_error = recovery_error;
results.estimated_stored_numeric_values = estimated_stored_numeric_values;
results.max_stored_numeric_values = max_stored_numeric_values;

fprintf('\nP42 range-Doppler metrics (seed %d)\n', random_seed);
fprintf('Range sample spacing %.3f m; nominal resolution %.3f m\n', ...
    range_sample_spacing_m, nominal_range_resolution_m);
fprintf('Doppler spacing %.3f Hz; velocity spacing %.3f m/s\n', ...
    doppler_bin_spacing_hz, velocity_bin_spacing_mps);
for target_index = 1:target_count
    fprintf(['Target %d: expected %.1f m, %+.2f m/s; measured ' ...
        '%.1f m, %+.2f m/s\n'], target_index, ...
        target_ranges_m(target_index), target_velocities_mps(target_index), ...
        measured_target_ranges_m(target_index), ...
        measured_target_velocities_mps(target_index));
end
fprintf('Broken valid: %d; recovered valid: %d; recovery error %.3g\n', ...
    broken_model_valid, recovered_model_valid, recovery_error);
