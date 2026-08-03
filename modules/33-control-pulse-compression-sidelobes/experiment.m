%% P33: Control Pulse-Compression Sidelobes
% Guiding question:
% Why can a strong target hide a weak nearby target after matched filtering?
% Model: y_w[k] = sum_n x[k+n] conj(s[n]) w[n].
% A taper w lowers sidelobes but widens the mainlobe and costs output SNR.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P33'));

%% Visible deterministic controls and resource ceilings
random_seed = 3301;
speed_of_light_mps = 299792458;
sample_rate_hz = 40e6;
capture_duration_s = 40e-6;
baseline_pulse_duration_s = 10e-6;
baseline_bandwidth_hz = 8e6;
strong_target_range_m = 2400;
weak_target_amplitude = 0.04;
weak_target_separation_samples = 17;
noise_sigma = 0.12;
taper_alpha_sweep = [0 0.5 1];
separation_sweep_samples = [7 13 17 32];
broken_separation_samples = 7;
comparison_tolerance = 1e-10;
max_record_samples = 1600;
max_pulse_samples = 400;
max_correlation_samples = 1999;
max_taper_cases = 3;
max_separation_cases = 4;
max_figure_groups = 6;
max_stored_numeric_values = 500000;

%% Validate controls before allocating experiment arrays
positive_controls = [speed_of_light_mps sample_rate_hz capture_duration_s ...
    baseline_pulse_duration_s baseline_bandwidth_hz strong_target_range_m ...
    weak_target_amplitude noise_sigma comparison_tolerance];
assert(all(isfinite(positive_controls)) && all(positive_controls > 0));
assert(isfinite(random_seed) && random_seed == floor(random_seed) && ...
    random_seed == 3301);
assert(baseline_bandwidth_hz < sample_rate_hz/2);
assert(isfinite(weak_target_separation_samples) && ...
    weak_target_separation_samples == floor(weak_target_separation_samples) && ...
    weak_target_separation_samples > 0);
assert(isfinite(broken_separation_samples) && ...
    broken_separation_samples == floor(broken_separation_samples) && ...
    broken_separation_samples > 0);
assert(numel(taper_alpha_sweep) >= 2 && ...
    numel(taper_alpha_sweep) <= max_taper_cases && ...
    all(isfinite(taper_alpha_sweep)) && ...
    all(taper_alpha_sweep >= 0 & taper_alpha_sweep <= 1) && ...
    all(diff(taper_alpha_sweep) > 0));
assert(numel(separation_sweep_samples) >= 2 && ...
    numel(separation_sweep_samples) <= max_separation_cases && ...
    all(isfinite(separation_sweep_samples)) && ...
    all(separation_sweep_samples == floor(separation_sweep_samples)) && ...
    all(separation_sweep_samples > 0) && ...
    all(diff(separation_sweep_samples) > 0));
assert(any(separation_sweep_samples == weak_target_separation_samples));
assert(any(separation_sweep_samples == broken_separation_samples));
resource_limits = [max_record_samples max_pulse_samples ...
    max_correlation_samples max_taper_cases max_separation_cases ...
    max_figure_groups max_stored_numeric_values];
assert(all(isfinite(resource_limits)) && all(resource_limits > 0) && ...
    all(resource_limits == floor(resource_limits)));

record_count = round(capture_duration_s*sample_rate_hz);
baseline_pulse_count = round(baseline_pulse_duration_s*sample_rate_hz);
correlation_count = record_count+baseline_pulse_count-1;
strong_delay_samples = round(2*strong_target_range_m*sample_rate_hz/...
    speed_of_light_mps);
weak_delay_samples = strong_delay_samples+weak_target_separation_samples;
largest_separation_samples = max([weak_target_separation_samples ...
    broken_separation_samples separation_sweep_samples]);
largest_delay_samples = strong_delay_samples+largest_separation_samples;
range_sample_spacing_m = speed_of_light_mps/(2*sample_rate_hz);
estimated_stored_numeric_values = 40*record_count+...
    50*correlation_count+20*baseline_pulse_count+...
    10*(max_taper_cases+max_separation_cases);
assert(record_count >= 1 && record_count <= max_record_samples);
assert(baseline_pulse_count >= 3 && ...
    baseline_pulse_count <= max_pulse_samples);
assert(correlation_count <= max_correlation_samples);
assert(largest_delay_samples+baseline_pulse_count <= record_count);
assert(max_figure_groups >= 6);
assert(estimated_stored_numeric_values <= max_stored_numeric_values);

%% Build the P32 LFM phase law and two zero-extended echoes explicitly
pulse_time_s = (0:baseline_pulse_count-1)/sample_rate_hz;
centered_pulse_time_s = pulse_time_s-...
    (baseline_pulse_count-1)/(2*sample_rate_hz);
chirp_rate_hz_per_s = baseline_bandwidth_hz/baseline_pulse_duration_s;
transmit_chirp = exp(1j*pi*chirp_rate_hz_per_s*centered_pulse_time_s.^2);
rectangular_weights = ones(1, baseline_pulse_count);
sample_index = 0:baseline_pulse_count-1;
hann_weights = 0.5-0.5*cos(2*pi*sample_index/(baseline_pulse_count-1));
rectangular_filter = fliplr(conj(transmit_chirp.*rectangular_weights));
hann_filter = fliplr(conj(transmit_chirp.*hann_weights));

strong_echo = complex(zeros(1, record_count));
weak_echo = complex(zeros(1, record_count));
strong_indices = strong_delay_samples+(1:baseline_pulse_count);
weak_indices = weak_delay_samples+(1:baseline_pulse_count);
strong_echo(strong_indices) = transmit_chirp;
weak_echo(weak_indices) = weak_target_amplitude*transmit_chirp;
clean_received_signal = strong_echo+weak_echo;

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
unit_noise = (randn(private_stream, 1, record_count)+...
    1j*randn(private_stream, 1, record_count))/sqrt(2);
received_signal = clean_received_signal+noise_sigma*unit_noise;

%% Baseline operation: expose the rectangular convolution sum
rectangular_noisy_response = complex(zeros(1, correlation_count));
for output_index = 1:correlation_count
    first_filter_index = max(1, output_index-record_count+1);
    last_filter_index = min(baseline_pulse_count, output_index);
    aligned_sum = 0;
    for filter_index = first_filter_index:last_filter_index
        received_index = output_index-filter_index+1;
        aligned_sum = aligned_sum+received_signal(received_index)*...
            rectangular_filter(filter_index);
    end
    rectangular_noisy_response(output_index) = aligned_sum;
end
rectangular_convolution_crosscheck = conv(received_signal, rectangular_filter);
crosscheck_error = max(abs(rectangular_noisy_response-...
    rectangular_convolution_crosscheck));
assert(crosscheck_error <= comparison_tolerance*...
    max(1, max(abs(rectangular_convolution_crosscheck))));

hann_noisy_response = conv(received_signal, hann_filter);
rectangular_clean_scene_response = conv(clean_received_signal, ...
    rectangular_filter);
hann_clean_scene_response = conv(clean_received_signal, hann_filter);
rectangular_strong_response = conv(strong_echo, rectangular_filter);
hann_strong_response = conv(strong_echo, hann_filter);

output_lags_samples = (0:correlation_count-1)-(baseline_pulse_count-1);
range_axis_m = speed_of_light_mps*output_lags_samples/(2*sample_rate_hz);
strong_output_index = strong_delay_samples+baseline_pulse_count;
weak_output_index = weak_delay_samples+baseline_pulse_count;
strong_target_sampled_range_m = strong_delay_samples*range_sample_spacing_m;
weak_target_sampled_range_m = weak_delay_samples*range_sample_spacing_m;

%% Measure isolated response width, peak sidelobes, SNR loss, and masking
[rectangular_width_m, rectangular_pslr_db] = characterize_response(...
    abs(rectangular_strong_response), range_sample_spacing_m);
[hann_width_m, hann_pslr_db] = characterize_response(...
    abs(hann_strong_response), range_sample_spacing_m);
rectangular_snr_loss_db = 10*log10(sum(rectangular_weights)^2/...
    (baseline_pulse_count*sum(rectangular_weights.^2)));
hann_snr_loss_db = 10*log10(sum(hann_weights)^2/...
    (baseline_pulse_count*sum(hann_weights.^2)));
rectangular_weak_peak = weak_target_amplitude*sum(rectangular_weights);
hann_weak_peak = weak_target_amplitude*sum(hann_weights);
rectangular_strong_leakage = abs(rectangular_strong_response(weak_output_index));
hann_strong_leakage = abs(hann_strong_response(weak_output_index));
rectangular_visibility_margin_db = 20*log10(rectangular_weak_peak/...
    rectangular_strong_leakage);
hann_visibility_margin_db = 20*log10(hann_weak_peak/hann_strong_leakage);
rectangular_weak_local_peak = ...
    abs(rectangular_clean_scene_response(weak_output_index)) > ...
    abs(rectangular_clean_scene_response(weak_output_index-1)) && ...
    abs(rectangular_clean_scene_response(weak_output_index)) > ...
    abs(rectangular_clean_scene_response(weak_output_index+1));
hann_weak_local_peak = abs(hann_clean_scene_response(weak_output_index)) > ...
    abs(hann_clean_scene_response(weak_output_index-1)) && ...
    abs(hann_clean_scene_response(weak_output_index)) > ...
    abs(hann_clean_scene_response(weak_output_index+1));
assert(rectangular_visibility_margin_db < 0);
assert(hann_visibility_margin_db > 0);
assert(~rectangular_weak_local_peak && hann_weak_local_peak);
assert(hann_pslr_db < rectangular_pslr_db-10);
assert(hann_width_m > 1.5*rectangular_width_m);
assert(hann_snr_loss_db < -1.5 && hann_snr_loss_db > -2);

rectangular_strong_peak = max(abs(rectangular_strong_response));
hann_strong_peak = max(abs(hann_strong_response));
rectangular_strong_db = 20*log10(max(abs(rectangular_strong_response)/...
    rectangular_strong_peak, 1e-8));
hann_strong_db = 20*log10(max(abs(hann_strong_response)/...
    hann_strong_peak, 1e-8));
isolated_view = range_axis_m >= strong_target_sampled_range_m-120 & ...
    range_axis_m <= strong_target_sampled_range_m+120;

figure('Name', 'P33 isolated response and weights', 'Tag', 'P33');
subplot(2, 1, 1);
plot(sample_index, rectangular_weights, 'LineWidth', 1.1);
hold on;
plot(sample_index, hann_weights, 'LineWidth', 1.2);
grid on;
xlabel('Replica sample index');
ylabel('Receive weight (linear)');
legend('Rectangular', 'Hann-like cosine', 'Location', 'best');
title('The taper reduces the contribution of pulse endpoints');
subplot(2, 1, 2);
plot(range_axis_m(isolated_view), rectangular_strong_db(isolated_view), ...
    'LineWidth', 1.1);
hold on;
plot(range_axis_m(isolated_view), hann_strong_db(isolated_view), ...
    'LineWidth', 1.2);
grid on;
xlabel('Filter-delay-corrected monostatic range c tau / 2 (m)');
ylabel('Magnitude relative to each filter peak (dB)');
legend('Rectangular', 'Hann-like cosine', 'Location', 'best');
title('Lower sidelobes require a wider mainlobe');
ylim([-65 3]);

rectangular_scene_db = 20*log10(max(abs(rectangular_noisy_response)/...
    rectangular_strong_peak, 1e-8));
hann_scene_db = 20*log10(max(abs(hann_noisy_response)/hann_strong_peak, 1e-8));
rectangular_clean_scene_db = 20*log10(max(...
    abs(rectangular_clean_scene_response)/rectangular_strong_peak, 1e-8));
hann_clean_scene_db = 20*log10(max(...
    abs(hann_clean_scene_response)/hann_strong_peak, 1e-8));
scene_view = range_axis_m >= strong_target_sampled_range_m-35 & ...
    range_axis_m <= weak_target_sampled_range_m+45;

figure('Name', 'P33 strong and weak target baseline', 'Tag', 'P33');
subplot(2, 1, 1);
plot(range_axis_m(scene_view), rectangular_clean_scene_db(scene_view), ...
    'LineWidth', 1.3);
hold on;
plot(range_axis_m(scene_view), rectangular_scene_db(scene_view), ...
    'LineWidth', 0.8);
plot(weak_target_sampled_range_m, ...
    rectangular_clean_scene_db(weak_output_index), ...
    'o', 'LineWidth', 1.2);
grid on;
xlabel('Filter-delay-corrected monostatic range c tau / 2 (m)');
ylabel('Matched output relative to strong-target peak (dB)');
title('Rectangular processing: strong-target sidelobe masks the weak echo');
legend('Clean scene', 'Seeded noisy scene', 'Expected weak range', ...
    'Location', 'best');
ylim([-50 3]);
subplot(2, 1, 2);
plot(range_axis_m(scene_view), hann_clean_scene_db(scene_view), ...
    'LineWidth', 1.3);
hold on;
plot(range_axis_m(scene_view), hann_scene_db(scene_view), 'LineWidth', 0.8);
plot(weak_target_sampled_range_m, hann_clean_scene_db(weak_output_index), ...
    'o', 'LineWidth', 1.2);
grid on;
xlabel('Filter-delay-corrected monostatic range c tau / 2 (m)');
ylabel('Tapered output relative to strong-target peak (dB)');
title('Hann-like processing: lower leakage exposes the weak echo');
legend('Clean scene', 'Seeded noisy scene', 'Expected weak range', ...
    'Location', 'best');
ylim([-50 3]);

%% Sweep 1: taper strength only, fixed waveform, scene, noise, and separation
taper_pslr_db = zeros(size(taper_alpha_sweep));
taper_width_m = zeros(size(taper_alpha_sweep));
taper_snr_loss_db = zeros(size(taper_alpha_sweep));
taper_visibility_margin_db = zeros(size(taper_alpha_sweep));
for taper_index = 1:numel(taper_alpha_sweep)
    alpha = taper_alpha_sweep(taper_index);
    weights = (1-alpha)+alpha*hann_weights;
    weighted_filter = fliplr(conj(transmit_chirp.*weights));
    weighted_strong_response = conv(strong_echo, weighted_filter);
    [taper_width_m(taper_index), taper_pslr_db(taper_index)] = ...
        characterize_response(abs(weighted_strong_response), ...
        range_sample_spacing_m);
    taper_snr_loss_db(taper_index) = 10*log10(sum(weights)^2/...
        (baseline_pulse_count*sum(weights.^2)));
    weak_peak = weak_target_amplitude*sum(weights);
    strong_leakage = abs(weighted_strong_response(weak_output_index));
    taper_visibility_margin_db(taper_index) = 20*log10(...
        weak_peak/strong_leakage);
end
assert(all(diff(taper_pslr_db) < 0));
assert(all(diff(taper_width_m) > 0));
assert(all(diff(taper_snr_loss_db) < 0));
assert(taper_visibility_margin_db(1) < 0 && ...
    taper_visibility_margin_db(end) > 0);

figure('Name', 'P33 taper-strength sweep', 'Tag', 'P33');
subplot(2, 2, 1);
plot(taper_alpha_sweep, taper_pslr_db, 'o-', 'LineWidth', 1.2);
grid on;
xlabel('Cosine taper strength alpha');
ylabel('Peak sidelobe ratio (dB)');
title('Sidelobes fall');
subplot(2, 2, 2);
plot(taper_alpha_sweep, taper_width_m, 's-', 'LineWidth', 1.2);
grid on;
xlabel('Cosine taper strength alpha');
ylabel('Full -3 dB range width (m)');
title('Mainlobe widens');
subplot(2, 2, 3);
plot(taper_alpha_sweep, taper_snr_loss_db, 'd-', 'LineWidth', 1.2);
grid on;
xlabel('Cosine taper strength alpha');
ylabel('Output-SNR change (dB)');
title('Unequal weighting costs SNR');
subplot(2, 2, 4);
plot(taper_alpha_sweep, taper_visibility_margin_db, '^-', ...
    'LineWidth', 1.2);
hold on;
plot(taper_alpha_sweep, zeros(size(taper_alpha_sweep)), '--');
grid on;
xlabel('Cosine taper strength alpha');
ylabel('Weak peak / strong leakage (dB)');
title('Positive margin means sidelobe masking is relieved');

%% Sweep 2: weak-target separation only, fixed waveform, amplitude, and filters
separation_sweep_m = separation_sweep_samples*range_sample_spacing_m;
rectangular_separation_margin_db = zeros(size(separation_sweep_samples));
hann_separation_margin_db = zeros(size(separation_sweep_samples));
for separation_index = 1:numel(separation_sweep_samples)
    candidate_output_index = strong_output_index+...
        separation_sweep_samples(separation_index);
    rectangular_separation_margin_db(separation_index) = 20*log10(...
        rectangular_weak_peak/abs(rectangular_strong_response(...
        candidate_output_index)));
    hann_separation_margin_db(separation_index) = 20*log10(...
        hann_weak_peak/abs(hann_strong_response(candidate_output_index)));
end
assert(rectangular_separation_margin_db(1) < 0 && ...
    hann_separation_margin_db(1) < 0);
assert(rectangular_separation_margin_db(3) < 0 && ...
    hann_separation_margin_db(3) > 0);
assert(rectangular_separation_margin_db(end) > 0 && ...
    hann_separation_margin_db(end) > 0);

figure('Name', 'P33 weak-target separation sweep', 'Tag', 'P33');
plot(separation_sweep_m, rectangular_separation_margin_db, 'o-', ...
    'LineWidth', 1.2);
hold on;
plot(separation_sweep_m, hann_separation_margin_db, 's-', ...
    'LineWidth', 1.2);
plot(separation_sweep_m, zeros(size(separation_sweep_m)), '--');
grid on;
xlabel('Weak-target separation from strong target (m)');
ylabel('Weak peak / strong leakage (dB)');
legend('Rectangular', 'Hann-like cosine', '0 dB visibility boundary', ...
    'Location', 'best');
title('Target position determines whether a taper helps');

%% Intentionally broken case: choose the lowest PSLR without checking width
broken_weak_delay_samples = strong_delay_samples+broken_separation_samples;
broken_weak_echo = complex(zeros(1, record_count));
broken_indices = broken_weak_delay_samples+(1:baseline_pulse_count);
broken_weak_echo(broken_indices) = weak_target_amplitude*transmit_chirp;
broken_received_signal = strong_echo+broken_weak_echo+noise_sigma*unit_noise;
broken_hann_response = conv(broken_received_signal, hann_filter);
broken_clean_hann_response = conv(strong_echo+broken_weak_echo, hann_filter);
broken_weak_output_index = broken_weak_delay_samples+baseline_pulse_count;
broken_visibility_margin_db = 20*log10(hann_weak_peak/...
    abs(hann_strong_response(broken_weak_output_index)));
broken_claim_revealed = broken_visibility_margin_db > 0;
broken_weak_local_peak = ...
    abs(broken_clean_hann_response(broken_weak_output_index)) > ...
    abs(broken_clean_hann_response(broken_weak_output_index-1)) && ...
    abs(broken_clean_hann_response(broken_weak_output_index)) > ...
    abs(broken_clean_hann_response(broken_weak_output_index+1));
broken_model_valid = false;
assert(~broken_claim_revealed && broken_visibility_margin_db < 0 && ...
    ~broken_weak_local_peak);

broken_hann_db = 20*log10(max(abs(broken_hann_response)/...
    hann_strong_peak, 1e-8));
broken_clean_hann_db = 20*log10(max(abs(broken_clean_hann_response)/...
    hann_strong_peak, 1e-8));
broken_weak_range_m = broken_weak_delay_samples*range_sample_spacing_m;
broken_view = range_axis_m >= strong_target_sampled_range_m-25 & ...
    range_axis_m <= broken_weak_range_m+45;

figure('Name', 'P33 broken lowest-PSLR choice', 'Tag', 'P33');
plot(range_axis_m(broken_view), broken_clean_hann_db(broken_view), ...
    'LineWidth', 1.3);
hold on;
plot(range_axis_m(broken_view), broken_hann_db(broken_view), ...
    'LineWidth', 0.8);
plot(broken_weak_range_m, broken_clean_hann_db(broken_weak_output_index), ...
    'o', 'LineWidth', 1.2);
grid on;
xlabel('Filter-delay-corrected monostatic range c tau / 2 (m)');
ylabel('Hann-like output relative to strong-target peak (dB)');
title('Broken rule: the close weak target lies inside the wider mainlobe');
legend('Clean scene', 'Seeded noisy scene', 'Expected weak range', ...
    'Location', 'best');
ylim([-45 3]);

%% Recovery: restore the validated separation and recreate the private seed
recovery_stream = RandStream('mt19937ar', 'Seed', random_seed);
recovery_unit_noise = (randn(recovery_stream, 1, record_count)+...
    1j*randn(recovery_stream, 1, record_count))/sqrt(2);
recovery_received_signal = strong_echo+weak_echo+noise_sigma*...
    recovery_unit_noise;
recovery_hann_response = conv(recovery_received_signal, hann_filter);
recovery_noise_exact_match = isequal(recovery_unit_noise, unit_noise);
recovery_response_exact_match = isequal(recovery_hann_response, ...
    hann_noisy_response);
recovered_model_valid = true;
assert(recovery_noise_exact_match && recovery_response_exact_match && ...
    recovered_model_valid && ~broken_model_valid);

recovery_hann_db = 20*log10(max(abs(recovery_hann_response)/...
    hann_strong_peak, 1e-8));
recovery_view = range_axis_m >= strong_target_sampled_range_m-25 & ...
    range_axis_m <= weak_target_sampled_range_m+45;

figure('Name', 'P33 recovery at validated separation', 'Tag', 'P33');
plot(range_axis_m(recovery_view), recovery_hann_db(recovery_view), ...
    'LineWidth', 1.2);
hold on;
plot(weak_target_sampled_range_m, recovery_hann_db(weak_output_index), ...
    'o', 'LineWidth', 1.2);
grid on;
xlabel('Filter-delay-corrected monostatic range c tau / 2 (m)');
ylabel('Recovered output relative to strong-target peak (dB)');
title('Recovery: check separation against width and sidelobe leakage');
ylim([-45 3]);

%% Report the physical trade rather than only the normalized pictures
fprintf('P33 pulse-compression sidelobe control baseline\n');
fprintf('  B = %.1f MHz, T = %.1f microseconds, samples = %d\n', ...
    baseline_bandwidth_hz/1e6, baseline_pulse_duration_s*1e6, ...
    baseline_pulse_count);
fprintf('  Weak amplitude = %.4f (%.2f dB relative to strong)\n', ...
    weak_target_amplitude, 20*log10(weak_target_amplitude));
fprintf('  Baseline separation = %d samples = %.3f m\n', ...
    weak_target_separation_samples, ...
    weak_target_separation_samples*range_sample_spacing_m);
fprintf('  Rectangular: PSLR %.2f dB, width %.2f m, SNR loss %.2f dB\n', ...
    rectangular_pslr_db, rectangular_width_m, rectangular_snr_loss_db);
fprintf('  Hann-like: PSLR %.2f dB, width %.2f m, SNR loss %.2f dB\n', ...
    hann_pslr_db, hann_width_m, hann_snr_loss_db);
fprintf('  Visibility margin: rectangular %.2f dB, Hann-like %.2f dB\n', ...
    rectangular_visibility_margin_db, hann_visibility_margin_db);
fprintf('  Distinct clean weak-target peak: rectangular %d, Hann-like %d\n', ...
    rectangular_weak_local_peak, hann_weak_local_peak);
fprintf('  Broken close-target Hann-like margin = %.2f dB\n', ...
    broken_visibility_margin_db);
fprintf('  Broken close-target distinct clean weak peak = %d\n', ...
    broken_weak_local_peak);
fprintf('  Explicit-convolution cross-check error = %.3g\n', crosscheck_error);
fprintf('  Recovery exact match = %d\n', recovery_response_exact_match);

%% Local transparent measurements used after the baseline operation is shown
function [width_m, pslr_db] = characterize_response(magnitude, spacing_m)
    [peak_value, peak_index] = max(magnitude);
    threshold = peak_value/sqrt(2);
    left_crossing_index = peak_index;
    while left_crossing_index > 1 && ...
            magnitude(left_crossing_index) >= threshold
        left_crossing_index = left_crossing_index-1;
    end
    right_crossing_index = peak_index;
    while right_crossing_index < numel(magnitude) && ...
            magnitude(right_crossing_index) >= threshold
        right_crossing_index = right_crossing_index+1;
    end
    assert(left_crossing_index >= 1 && ...
        right_crossing_index <= numel(magnitude));
    assert(magnitude(left_crossing_index) < threshold && ...
        magnitude(right_crossing_index) < threshold);
    left_fraction = (threshold-magnitude(left_crossing_index))/...
        (magnitude(left_crossing_index+1)-magnitude(left_crossing_index));
    right_fraction = (magnitude(right_crossing_index-1)-threshold)/...
        (magnitude(right_crossing_index-1)-magnitude(right_crossing_index));
    left_crossing = (left_crossing_index-1)+left_fraction;
    right_crossing = (right_crossing_index-2)+right_fraction;
    width_m = (right_crossing-left_crossing)*spacing_m;

    left_minimum = peak_index-1;
    while left_minimum > 1 && ...
            magnitude(left_minimum-1) < magnitude(left_minimum)
        left_minimum = left_minimum-1;
    end
    right_minimum = peak_index+1;
    while right_minimum < numel(magnitude) && ...
            magnitude(right_minimum+1) < magnitude(right_minimum)
        right_minimum = right_minimum+1;
    end
    sidelobe_peak = max([magnitude(1:left_minimum-1) ...
        magnitude(right_minimum+1:end)]);
    pslr_db = 20*log10(sidelobe_peak/peak_value);
end
