%% P32: Perform LFM Pulse Compression
% Guiding question: How can a long energetic pulse achieve short-pulse range resolution?
% Base MATLAB only. The script builds a complex-baseband linear-FM pulse,
% inserts two zero-extended echoes, performs the matched-filter sum explicitly,
% sweeps bandwidth and duration independently, breaks the replica chirp rate,
% and then proves deterministic recovery.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P32'));

%% Visible controls and fixed resource bounds
random_seed = 3201;
speed_of_light_mps = 299792458;
sample_rate_hz = 40e6;
capture_duration_s = 40e-6;
baseline_pulse_duration_s = 10e-6;
baseline_bandwidth_hz = 8e6;
bandwidth_sweep_hz = [4e6 8e6 16e6];
duration_sweep_s = [5e-6 10e-6 20e-6];
first_target_range_m = 2400;
second_target_separation_m = 75;
first_echo_amplitude = 1;
second_echo_amplitude = 0.65;
noise_sigma = 2;
broken_replica_bandwidth_scale = 0.55;
comparison_tolerance = 1e-10;
max_record_samples = 1600;
max_pulse_samples = 800;
max_correlation_samples = 2400;
max_bandwidth_cases = 3;
max_duration_cases = 3;
max_figure_groups = 6;
max_stored_numeric_values = 500000;

%% Validate every control before allocating experiment arrays
assert(isfinite(random_seed) && random_seed == 3201 && random_seed > 0);
assert(isfinite(speed_of_light_mps) && speed_of_light_mps > 0);
assert(isfinite(sample_rate_hz) && sample_rate_hz > 0);
assert(isfinite(capture_duration_s) && capture_duration_s > 0);
assert(isfinite(baseline_pulse_duration_s) && baseline_pulse_duration_s > 0);
assert(isfinite(baseline_bandwidth_hz) && baseline_bandwidth_hz > 0);
assert(all(isfinite(bandwidth_sweep_hz)) && all(diff(bandwidth_sweep_hz) > 0));
assert(all(isfinite(duration_sweep_s)) && all(diff(duration_sweep_s) > 0));
assert(max(bandwidth_sweep_hz) < sample_rate_hz/2);
assert(numel(bandwidth_sweep_hz) <= max_bandwidth_cases);
assert(numel(duration_sweep_s) <= max_duration_cases);
assert(isfinite(first_target_range_m) && first_target_range_m > 0);
assert(isfinite(second_target_separation_m) && second_target_separation_m > 0);
assert(isfinite(first_echo_amplitude) && first_echo_amplitude > 0);
assert(isfinite(second_echo_amplitude) && second_echo_amplitude > 0);
assert(isfinite(noise_sigma) && noise_sigma > 0);
assert(isfinite(broken_replica_bandwidth_scale) && ...
    broken_replica_bandwidth_scale > 0 && broken_replica_bandwidth_scale < 1);
assert(isfinite(comparison_tolerance) && comparison_tolerance > 0);

record_count = round(capture_duration_s*sample_rate_hz);
baseline_pulse_count = round(baseline_pulse_duration_s*sample_rate_hz);
duration_sample_counts = round(duration_sweep_s*sample_rate_hz);
first_delay_samples = round(2*first_target_range_m*sample_rate_hz/...
    speed_of_light_mps);
second_delay_samples = round(2*(first_target_range_m+...
    second_target_separation_m)*sample_rate_hz/speed_of_light_mps);
max_full_correlation_count = record_count+max(duration_sample_counts)-1;
estimated_stored_numeric_values = 80*record_count+...
    40*max_full_correlation_count+20*sum(duration_sample_counts);
assert(record_count >= 1 && record_count <= max_record_samples);
assert(baseline_pulse_count >= 2 && baseline_pulse_count <= max_pulse_samples);
assert(all(duration_sample_counts >= 2) && ...
    max(duration_sample_counts) <= max_pulse_samples);
assert(max_full_correlation_count <= max_correlation_samples);
assert(second_delay_samples+max(duration_sample_counts) <= record_count);
assert(max_figure_groups == 6);
assert(estimated_stored_numeric_values <= max_stored_numeric_values);
% Validation succeeded: all later arrays and loops have deterministic ceilings.

%% Build the baseline LFM pulse from its phase law
% s(t)=exp(j*pi*k*(t-T/2)^2), k=B/T, and f_inst(t)=k*(t-T/2).
baseline_chirp_rate_hz_per_s = baseline_bandwidth_hz/...
    baseline_pulse_duration_s;
baseline_time_s = (0:baseline_pulse_count-1)/sample_rate_hz;
baseline_centered_time_s = baseline_time_s-...
    (baseline_pulse_count-1)/(2*sample_rate_hz);
transmit_chirp = exp(1j*pi*baseline_chirp_rate_hz_per_s*...
    baseline_centered_time_s.^2);
baseline_instantaneous_frequency_hz = baseline_chirp_rate_hz_per_s*...
    baseline_centered_time_s;
matched_filter = fliplr(conj(transmit_chirp));
time_bandwidth_product = baseline_bandwidth_hz*baseline_pulse_duration_s;
nominal_resolution_m = speed_of_light_mps/(2*baseline_bandwidth_hz);
raw_pulse_range_extent_m = speed_of_light_mps*baseline_pulse_duration_s/2;

figure('Name', 'P32 transmit LFM', 'Tag', 'P32');
subplot(2, 1, 1);
plot(1e6*baseline_time_s, real(transmit_chirp), 'LineWidth', 1.1);
hold on;
plot(1e6*baseline_time_s, imag(transmit_chirp), 'LineWidth', 1.1);
grid on;
xlabel('Pulse time (microseconds)');
ylabel('Complex amplitude');
legend('I', 'Q', 'Location', 'best');
title('Constant-amplitude LFM pulse: phase rotation stores the bandwidth');
subplot(2, 1, 2);
plot(1e6*baseline_time_s, baseline_instantaneous_frequency_hz/1e6, ...
    'LineWidth', 1.2);
grid on;
xlabel('Pulse time (microseconds)');
ylabel('Instantaneous frequency (MHz)');
title('Linear sweep from approximately -B/2 to +B/2');

%% Insert two delayed, zero-extended echoes and add private seeded noise
first_echo = complex(zeros(1, record_count));
second_echo = complex(zeros(1, record_count));
first_indices = first_delay_samples+(1:baseline_pulse_count);
second_indices = second_delay_samples+(1:baseline_pulse_count);
first_echo(first_indices) = first_echo_amplitude*transmit_chirp;
second_echo(second_indices) = second_echo_amplitude*transmit_chirp;
clean_received_signal = first_echo+second_echo;
private_stream = RandStream('mt19937ar', 'Seed', random_seed);
unit_noise = (randn(private_stream, 1, record_count)+...
    1j*randn(private_stream, 1, record_count))/sqrt(2);
noise = noise_sigma*unit_noise;
received_signal = clean_received_signal+noise;
received_range_axis_m = speed_of_light_mps*(0:record_count-1)/...
    (2*sample_rate_hz);

figure('Name', 'P32 raw long echoes', 'Tag', 'P32');
plot(received_range_axis_m, abs(first_echo), 'LineWidth', 1.1);
hold on;
plot(received_range_axis_m, abs(second_echo), 'LineWidth', 1.1);
plot(received_range_axis_m, abs(clean_received_signal), 'k', 'LineWidth', 1.0);
grid on;
xlabel('Apparent monostatic range c t / 2 (m)');
ylabel('Raw echo magnitude');
legend('Target 1 echo', 'Target 2 echo', 'Coherent sum', 'Location', 'best');
title('The raw echoes each occupy the long-pulse range extent');

%% Perform the baseline matched-filter operation explicitly
% h[q]=conj(s[N-1-q]); y[n]=sum_m x[m]*h[n-m].
explicit_compressed_signal = complex(zeros(1, ...
    record_count+baseline_pulse_count-1));
for output_index = 1:numel(explicit_compressed_signal)
    received_start = max(1, output_index-baseline_pulse_count+1);
    received_stop = min(record_count, output_index);
    aligned_sum = 0;
    for received_index = received_start:received_stop
        filter_index = output_index-received_index+1;
        aligned_sum = aligned_sum+received_signal(received_index)*...
            matched_filter(filter_index);
    end
    explicit_compressed_signal(output_index) = aligned_sum;
end
convolution_crosscheck = conv(received_signal, matched_filter);
crosscheck_error = max(abs(explicit_compressed_signal-convolution_crosscheck));
assert(crosscheck_error <= comparison_tolerance*...
    max(1, max(abs(convolution_crosscheck))));

baseline_lags_samples = (0:numel(explicit_compressed_signal)-1)-...
    (baseline_pulse_count-1);
baseline_range_axis_m = speed_of_light_mps*baseline_lags_samples/...
    (2*sample_rate_hz);
baseline_clean_single_response = conv(first_echo, matched_filter);
baseline_width_m = measure_half_power_width(abs(...
    baseline_clean_single_response), speed_of_light_mps/(2*sample_rate_hz));
compressed_db = 20*log10(max(abs(explicit_compressed_signal)/...
    max(abs(explicit_compressed_signal)), 1e-8));
baseline_view = baseline_range_axis_m >= first_target_range_m-150 & ...
    baseline_range_axis_m <= first_target_range_m+...
    second_target_separation_m+150;

figure('Name', 'P32 compressed echoes', 'Tag', 'P32');
plot(baseline_range_axis_m(baseline_view), compressed_db(baseline_view), ...
    'LineWidth', 1.2);
grid on;
xlabel('Matched-filter monostatic range c tau / 2 (m)');
ylabel('Normalized matched-output magnitude (dB)');
title('Pulse compression reveals two delay peaks from the long echoes');
ylim([-45 3]);

%% Measure sampled coherent gain and B*T processing gain honestly
% Per-sample white-noise gain is Fs*T. Referencing input noise to the
% waveform's B-Hz receiver bandwidth converts that ratio to B*T.
baseline_noise_response = conv(noise, matched_filter);
full_overlap_indices = baseline_pulse_count:record_count;
baseline_output_noise_power = mean(abs(baseline_noise_response(...
    full_overlap_indices)).^2);
baseline_signal_peak_power = max(abs(baseline_clean_single_response)).^2;
baseline_output_snr_db = 10*log10(baseline_signal_peak_power/...
    baseline_output_noise_power);
baseline_input_inband_snr_db = 10*log10(first_echo_amplitude^2/...
    (noise_sigma^2*(baseline_bandwidth_hz/sample_rate_hz)));
measured_processing_gain_db = baseline_output_snr_db-...
    baseline_input_inband_snr_db;
predicted_processing_gain_db = 10*log10(time_bandwidth_product);
sampled_coherent_gain_db = 10*log10(baseline_pulse_count);
assert(abs(measured_processing_gain_db-predicted_processing_gain_db) < 3);

%% Sweep 1: bandwidth only, fixed duration, scene, amplitudes, and noise
bandwidth_width_m = zeros(size(bandwidth_sweep_hz));
bandwidth_nominal_resolution_m = zeros(size(bandwidth_sweep_hz));
bandwidth_time_bandwidth_product = zeros(size(bandwidth_sweep_hz));
for case_index = 1:numel(bandwidth_sweep_hz)
    case_bandwidth_hz = bandwidth_sweep_hz(case_index);
    [case_chirp, ~] = make_lfm(case_bandwidth_hz, ...
        baseline_pulse_duration_s, sample_rate_hz);
    case_echo = complex(zeros(1, record_count));
    case_echo(first_delay_samples+(1:numel(case_chirp))) = ...
        first_echo_amplitude*case_chirp;
    case_response = conv(case_echo, fliplr(conj(case_chirp)));
    bandwidth_width_m(case_index) = measure_half_power_width(...
        abs(case_response), speed_of_light_mps/(2*sample_rate_hz));
    bandwidth_nominal_resolution_m(case_index) = ...
        speed_of_light_mps/(2*case_bandwidth_hz);
    bandwidth_time_bandwidth_product(case_index) = case_bandwidth_hz*...
        baseline_pulse_duration_s;
end
assert(all(diff(bandwidth_width_m) < 0));
assert(all(diff(bandwidth_nominal_resolution_m) < 0));

figure('Name', 'P32 bandwidth sweep', 'Tag', 'P32');
plot(bandwidth_sweep_hz/1e6, bandwidth_width_m, 'o-', 'LineWidth', 1.2);
hold on;
plot(bandwidth_sweep_hz/1e6, bandwidth_nominal_resolution_m, 's--', ...
    'LineWidth', 1.2);
grid on;
xlabel('Chirp bandwidth B (MHz)');
ylabel('Compressed range width (m)');
legend('Measured full -3 dB width', 'Nominal c/(2B)', 'Location', 'best');
title('More bandwidth narrows the compressed response at fixed duration');

%% Sweep 2: duration only, fixed bandwidth, scene, amplitude, and noise basis
duration_width_m = zeros(size(duration_sweep_s));
duration_time_bandwidth_product = baseline_bandwidth_hz*duration_sweep_s;
duration_predicted_gain_db = 10*log10(duration_time_bandwidth_product);
for case_index = 1:numel(duration_sweep_s)
    case_duration_s = duration_sweep_s(case_index);
    [case_chirp, ~] = make_lfm(baseline_bandwidth_hz, case_duration_s, ...
        sample_rate_hz);
    case_echo = complex(zeros(1, record_count));
    case_echo(first_delay_samples+(1:numel(case_chirp))) = ...
        first_echo_amplitude*case_chirp;
    case_response = conv(case_echo, fliplr(conj(case_chirp)));
    duration_width_m(case_index) = measure_half_power_width(...
        abs(case_response), speed_of_light_mps/(2*sample_rate_hz));
end
range_sample_spacing_m = speed_of_light_mps/(2*sample_rate_hz);
assert(max(duration_width_m)-min(duration_width_m) < range_sample_spacing_m);
assert(all(diff(duration_time_bandwidth_product) > 0));
assert(all(diff(duration_predicted_gain_db) > 0));

figure('Name', 'P32 duration sweep', 'Tag', 'P32');
subplot(2, 1, 1);
plot(duration_sweep_s*1e6, duration_width_m, 'o-', 'LineWidth', 1.2);
grid on;
xlabel('Pulse duration T (microseconds)');
ylabel('Compressed range width (m)');
title('At fixed B, duration barely changes compressed width');
subplot(2, 1, 2);
plot(duration_sweep_s*1e6, duration_predicted_gain_db, 's-', ...
    'LineWidth', 1.2);
grid on;
xlabel('Pulse duration T (microseconds)');
ylabel('B T processing gain (dB)');
title('At fixed B, a longer pulse carries more coherent energy');

%% Intentionally broken case: compress with a mismatched chirp-rate replica
broken_replica_bandwidth_hz = broken_replica_bandwidth_scale*...
    baseline_bandwidth_hz;
[broken_replica, ~] = make_lfm(broken_replica_bandwidth_hz, ...
    baseline_pulse_duration_s, sample_rate_hz);
broken_matched_filter = fliplr(conj(broken_replica));
broken_response = conv(first_echo, broken_matched_filter);
broken_width_m = measure_half_power_width(abs(broken_response), ...
    range_sample_spacing_m);
broken_peak = max(abs(broken_response));
recovered_peak = max(abs(baseline_clean_single_response));
mismatch_peak_loss_db = 20*log10(broken_peak/recovered_peak);
broken_model_valid = false;
assert(broken_peak < 0.5*recovered_peak);
assert(broken_width_m > 5*baseline_width_m);
assert(mismatch_peak_loss_db < -6);

%% Recovery: restore the transmitted replica and recreate the private seed
recovery_matched_filter = fliplr(conj(transmit_chirp));
recovery_stream = RandStream('mt19937ar', 'Seed', random_seed);
recovery_unit_noise = (randn(recovery_stream, 1, record_count)+...
    1j*randn(recovery_stream, 1, record_count))/sqrt(2);
recovery_received_signal = clean_received_signal+noise_sigma*...
    recovery_unit_noise;
recovery_response = conv(recovery_received_signal, recovery_matched_filter);
recovery_noise_exact_match = isequal(recovery_unit_noise, unit_noise);
recovery_response_exact_match = isequal(recovery_response, ...
    convolution_crosscheck);
recovered_model_valid = true;
assert(recovery_noise_exact_match && recovery_response_exact_match && ...
    recovered_model_valid && ~broken_model_valid);

broken_lags_samples = (0:numel(broken_response)-1)-...
    (numel(broken_replica)-1);
broken_range_axis_m = speed_of_light_mps*broken_lags_samples/...
    (2*sample_rate_hz);
mismatch_reference_peak = recovered_peak;
broken_db = 20*log10(max(abs(broken_response)/mismatch_reference_peak, 1e-8));
recovered_db = 20*log10(max(abs(baseline_clean_single_response)/...
    mismatch_reference_peak, 1e-8));
mismatch_view = baseline_range_axis_m >= first_target_range_m-350 & ...
    baseline_range_axis_m <= first_target_range_m+350;
broken_view = broken_range_axis_m >= first_target_range_m-350 & ...
    broken_range_axis_m <= first_target_range_m+350;

figure('Name', 'P32 mismatch and recovery', 'Tag', 'P32');
plot(broken_range_axis_m(broken_view), broken_db(broken_view), ...
    'LineWidth', 1.1);
hold on;
plot(baseline_range_axis_m(mismatch_view), recovered_db(mismatch_view), ...
    'LineWidth', 1.2);
grid on;
xlabel('Matched-filter monostatic range c tau / 2 (m)');
ylabel('Matched output relative to recovered peak (dB)');
legend('Broken 0.55B replica', 'Recovered exact replica', 'Location', 'best');
title('Chirp-rate mismatch spreads coherent energy instead of compressing it');
ylim([-45 3]);

%% Report the measurements that connect energy and resolution
fprintf('P32 LFM pulse compression baseline\n');
fprintf('  B = %.1f MHz, T = %.1f microseconds, B*T = %.1f\n', ...
    baseline_bandwidth_hz/1e6, baseline_pulse_duration_s*1e6, ...
    time_bandwidth_product);
fprintf('  Raw pulse range extent = %.2f m\n', raw_pulse_range_extent_m);
fprintf('  Nominal c/(2B) range scale = %.2f m\n', nominal_resolution_m);
fprintf('  Measured full -3 dB compressed width = %.2f m\n', baseline_width_m);
fprintf('  Sampled coherent gain Fs*T = %.2f dB\n', sampled_coherent_gain_db);
fprintf('  Predicted B*T processing gain = %.2f dB\n', ...
    predicted_processing_gain_db);
fprintf('  Measured B-Hz-referenced processing gain = %.2f dB\n', ...
    measured_processing_gain_db);
fprintf('  Mismatch peak loss = %.2f dB\n', mismatch_peak_loss_db);
fprintf('  Broken width %.2f m; recovered width %.2f m\n', broken_width_m, ...
    baseline_width_m);
fprintf('  Explicit-convolution cross-check error = %.3g\n', crosscheck_error);
fprintf('  Recovery exact match = %d\n', recovery_response_exact_match);

%% Local transparent helpers used only after the baseline operation is shown
function [waveform, time_s] = make_lfm(bandwidth_hz, pulse_duration_s, ...
        sample_rate_hz)
    pulse_count = round(pulse_duration_s*sample_rate_hz);
    time_s = (0:pulse_count-1)/sample_rate_hz;
    centered_time_s = time_s-(pulse_count-1)/(2*sample_rate_hz);
    chirp_rate_hz_per_s = bandwidth_hz/pulse_duration_s;
    waveform = exp(1j*pi*chirp_rate_hz_per_s*centered_time_s.^2);
end

function width_units = measure_half_power_width(magnitude, unit_spacing)
    [peak_value, peak_index] = max(magnitude);
    threshold = peak_value/sqrt(2);
    left_index = peak_index;
    while left_index > 1 && magnitude(left_index) >= threshold
        left_index = left_index-1;
    end
    right_index = peak_index;
    while right_index < numel(magnitude) && ...
            magnitude(right_index) >= threshold
        right_index = right_index+1;
    end
    assert(left_index >= 1 && right_index <= numel(magnitude));
    assert(magnitude(left_index) < threshold && ...
        magnitude(right_index) < threshold);
    left_fraction = (threshold-magnitude(left_index))/...
        (magnitude(left_index+1)-magnitude(left_index));
    right_fraction = (magnitude(right_index-1)-threshold)/...
        (magnitude(right_index-1)-magnitude(right_index));
    left_crossing = (left_index-1)+left_fraction;
    right_crossing = (right_index-2)+right_fraction;
    width_units = (right_crossing-left_crossing)*unit_spacing;
end
