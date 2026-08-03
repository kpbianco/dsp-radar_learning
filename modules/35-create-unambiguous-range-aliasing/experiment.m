%% P35: Create Unambiguous-Range Aliasing
% Guiding question:
% Why can a distant target appear at a shorter false range?
% Model: PRI = 1/PRF, R_u = c*PRI/2, and
% R_apparent = R_true - floor(R_true/R_u)*R_u.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P35'));

%% Visible deterministic controls and resource ceilings
random_seed = 3501;
speed_of_light_mps = 299792458;
sample_rate_hz = 20e6;
baseline_prf_hz = 20e3;
baseline_true_range_m = 18e3;
pulse_width_s = 2e-6;
pulse_count = 6;
echo_amplitude = 0.7;
noise_standard_deviation = 0.004;
prf_sweep_hz = [10e3 15e3 20e3 25e3];
prf_curve_hz = linspace(8e3, 30e3, 221);
range_probe_m = [3e3 8e3 18e3];
range_sweep_point_count = 601;
boundary_probe_offset_m = 25;
comparison_tolerance_m = 1e-6;
max_pulse_count = 8;
max_range_sweep_cases = 6;
max_prf_sweep_cases = 5;
max_samples_per_pri = 2000;
max_timeline_samples = 16000;
max_range_sweep_points = 801;
max_prf_curve_points = 301;
max_figure_groups = 5;
max_stored_numeric_values = 100000;

%% Validate controls before allocating pulse-train arrays
positive_controls = [speed_of_light_mps sample_rate_hz baseline_prf_hz ...
    baseline_true_range_m pulse_width_s pulse_count echo_amplitude ...
    boundary_probe_offset_m comparison_tolerance_m max_pulse_count ...
    max_range_sweep_cases max_prf_sweep_cases max_samples_per_pri ...
    max_timeline_samples max_range_sweep_points max_prf_curve_points ...
    max_figure_groups max_stored_numeric_values];
assert(all(isfinite(positive_controls)) && all(positive_controls > 0));
assert(isfinite(random_seed) && random_seed == floor(random_seed) && ...
    random_seed == 3501);
assert(isfinite(noise_standard_deviation) && ...
    noise_standard_deviation >= 0);
integer_controls = [pulse_count range_sweep_point_count max_pulse_count ...
    max_range_sweep_cases max_prf_sweep_cases max_samples_per_pri ...
    max_timeline_samples max_range_sweep_points max_prf_curve_points ...
    max_figure_groups max_stored_numeric_values];
assert(all(integer_controls == floor(integer_controls)));
assert(pulse_count >= 4 && pulse_count <= max_pulse_count);
assert(numel(prf_sweep_hz) >= 2 && ...
    numel(prf_sweep_hz) <= max_prf_sweep_cases && ...
    all(isfinite(prf_sweep_hz)) && all(prf_sweep_hz > 0) && ...
    all(diff(prf_sweep_hz) > 0));
assert(numel(prf_curve_hz) >= numel(prf_sweep_hz) && ...
    numel(prf_curve_hz) <= max_prf_curve_points && ...
    all(isfinite(prf_curve_hz)) && all(prf_curve_hz > 0) && ...
    all(diff(prf_curve_hz) > 0));
assert(numel(range_probe_m) >= 2 && ...
    numel(range_probe_m) <= max_range_sweep_cases && ...
    all(isfinite(range_probe_m)) && all(range_probe_m >= 0) && ...
    all(diff(range_probe_m) > 0));
assert(range_sweep_point_count >= 101 && ...
    range_sweep_point_count <= max_range_sweep_points);
assert(any(prf_sweep_hz == baseline_prf_hz));
assert(any(range_probe_m == baseline_true_range_m));
assert(pulse_width_s < 1/max(prf_curve_hz));

%% Baseline operation: discard unavailable pulse identity and fold the delay
prf_hz = baseline_prf_hz;
true_range_m = baseline_true_range_m;
pri_s = 1/prf_hz;
unambiguous_range_m = speed_of_light_mps/(2*prf_hz);
round_trip_delay_s = 2*true_range_m/speed_of_light_mps;
ambiguity_order = floor(true_range_m/unambiguous_range_m);
apparent_range_m = true_range_m - ambiguity_order*unambiguous_range_m;
apparent_delay_s = round_trip_delay_s - ambiguity_order*pri_s;
delay_fold_range_m = speed_of_light_mps*apparent_delay_s/2;

assert(true_range_m > unambiguous_range_m);
assert(ambiguity_order >= 1 && ambiguity_order <= pulse_count-2);
assert(apparent_delay_s >= 0 && apparent_delay_s < pri_s);
assert(apparent_range_m >= 0 && apparent_range_m < unambiguous_range_m);
assert(abs(delay_fold_range_m-apparent_range_m) <= ...
    comparison_tolerance_m);
assert(abs(apparent_range_m-mod(true_range_m, ...
    unambiguous_range_m)) <= comparison_tolerance_m);

samples_per_pri = round(pri_s*sample_rate_hz);
pulse_width_samples = round(pulse_width_s*sample_rate_hz);
timeline_sample_count = pulse_count*samples_per_pri;
estimated_stored_numeric_values = 5*timeline_sample_count+...
    5*numel(prf_curve_hz)+5*range_sweep_point_count+100;
assert(samples_per_pri >= 10 && samples_per_pri <= max_samples_per_pri);
assert(pulse_width_samples >= 2 && pulse_width_samples < samples_per_pri);
assert(timeline_sample_count <= max_timeline_samples);
assert(estimated_stored_numeric_values <= max_stored_numeric_values);
assert(max_figure_groups >= 5);

%% Build periodic transmissions and delayed echoes explicitly
timeline_s = (0:timeline_sample_count-1)/sample_rate_hz;
transmit_train = zeros(1, timeline_sample_count);
private_stream = RandStream('mt19937ar', 'Seed', random_seed);
receive_train = noise_standard_deviation/sqrt(2)*(...
    randn(private_stream, 1, timeline_sample_count)+...
    1j*randn(private_stream, 1, timeline_sample_count));
transmit_start_samples = zeros(1, pulse_count);
echo_start_samples = NaN(1, pulse_count);

for pulse_index = 0:pulse_count-1
    transmit_start_sample = 1+pulse_index*samples_per_pri;
    transmit_start_samples(pulse_index+1) = transmit_start_sample;
    transmit_indices = transmit_start_sample:min(...
        transmit_start_sample+pulse_width_samples-1, ...
        timeline_sample_count);
    transmit_train(transmit_indices) = 1;

    echo_start_sample = transmit_start_sample+...
        round(round_trip_delay_s*sample_rate_hz);
    if echo_start_sample <= timeline_sample_count
        echo_start_samples(pulse_index+1) = echo_start_sample;
        echo_indices = echo_start_sample:min(...
            echo_start_sample+pulse_width_samples-1, ...
            timeline_sample_count);
        receive_train(echo_indices) = receive_train(echo_indices)+...
            echo_amplitude;
    end
end
assert(all(diff(transmit_start_samples) == samples_per_pri));
assert(sum(isfinite(echo_start_samples)) >= 2);

baseline_echo_sample = echo_start_samples(1);
baseline_echo_arrival_s = timeline_s(baseline_echo_sample);
listening_interval_start_sample = ...
    transmit_start_samples(ambiguity_order+1);
listening_interval_stop_sample = listening_interval_start_sample+...
    samples_per_pri-1;
measured_fast_time_s = baseline_echo_arrival_s-...
    timeline_s(listening_interval_start_sample);
measured_apparent_range_m = speed_of_light_mps*measured_fast_time_s/2;
sample_range_spacing_m = speed_of_light_mps/(2*sample_rate_hz);
assert(baseline_echo_sample >= listening_interval_start_sample && ...
    baseline_echo_sample <= listening_interval_stop_sample);
assert(abs(measured_apparent_range_m-apparent_range_m) <= ...
    sample_range_spacing_m/2+comparison_tolerance_m);

figure('Name', 'P35 pulse identity timeline', 'Tag', 'P35');
subplot(2, 1, 1);
plot(timeline_s*1e6, transmit_train, 'LineWidth', 1.2);
grid on;
xlabel('Absolute time (microseconds)');
ylabel('Transmit amplitude');
title('Periodic transmissions: each pulse has a hidden identity');
ylim([-0.1 1.2]);
subplot(2, 1, 2);
plot(timeline_s*1e6, abs(receive_train), 'LineWidth', 1.0);
hold on;
plot(baseline_echo_arrival_s*1e6, ...
    abs(receive_train(baseline_echo_sample)), 'ro', 'LineWidth', 1.4);
grid on;
xlabel('Absolute time (microseconds)');
ylabel('Received magnitude');
title('An old echo arrives after newer pulses were transmitted');
legend('Received train', 'Echo from first pulse', 'Location', 'best');

figure('Name', 'P35 baseline folded listening interval', 'Tag', 'P35');
subplot(1, 2, 1);
listening_indices = listening_interval_start_sample:...
    listening_interval_stop_sample;
fast_time_s = (0:samples_per_pri-1)/sample_rate_hz;
fast_range_m = speed_of_light_mps*fast_time_s/2;
plot(fast_time_s*1e6, abs(receive_train(listening_indices)), ...
    'LineWidth', 1.1);
hold on;
plot(measured_fast_time_s*1e6, ...
    abs(receive_train(baseline_echo_sample)), 'ro', 'LineWidth', 1.4);
grid on;
xlabel('Time since most recent transmit (microseconds)');
ylabel('Received magnitude');
title(sprintf('Folded interval reports %.3f km', ...
    apparent_range_m/1e3));
legend('Current listening interval', 'Old echo', 'Location', 'best');
subplot(1, 2, 2);
plot([1 2 3], [true_range_m unambiguous_range_m apparent_range_m]/1e3, ...
    'o-', 'LineWidth', 1.2, 'MarkerSize', 7);
grid on;
xlim([0.7 3.3]);
set(gca, 'XTick', [1 2 3], 'XTickLabel', ...
    {'True range', 'Unambiguous range', 'Apparent range'});
ylabel('Range (km)');
title(sprintf('Ambiguity order q = %d', ambiguity_order));

%% Sweep 1: change only PRF at a fixed 18 km true range
prf_curve_unambiguous_range_m = zeros(size(prf_curve_hz));
prf_curve_apparent_range_m = zeros(size(prf_curve_hz));
prf_curve_ambiguity_order = zeros(size(prf_curve_hz));
for prf_index = 1:numel(prf_curve_hz)
    candidate_prf_hz = prf_curve_hz(prf_index);
    candidate_unambiguous_range_m = ...
        speed_of_light_mps/(2*candidate_prf_hz);
    candidate_ambiguity_order = floor(true_range_m/...
        candidate_unambiguous_range_m);
    prf_curve_unambiguous_range_m(prf_index) = ...
        candidate_unambiguous_range_m;
    prf_curve_ambiguity_order(prf_index) = candidate_ambiguity_order;
    prf_curve_apparent_range_m(prf_index) = true_range_m-...
        candidate_ambiguity_order*candidate_unambiguous_range_m;
end
assert(all(diff(prf_curve_unambiguous_range_m) < 0));
assert(all(prf_curve_apparent_range_m >= 0));
assert(all(prf_curve_apparent_range_m < ...
    prf_curve_unambiguous_range_m));

prf_sweep_unambiguous_range_m = zeros(size(prf_sweep_hz));
prf_sweep_apparent_range_m = zeros(size(prf_sweep_hz));
prf_sweep_ambiguity_order = zeros(size(prf_sweep_hz));
for prf_index = 1:numel(prf_sweep_hz)
    candidate_prf_hz = prf_sweep_hz(prf_index);
    candidate_unambiguous_range_m = ...
        speed_of_light_mps/(2*candidate_prf_hz);
    candidate_ambiguity_order = floor(true_range_m/...
        candidate_unambiguous_range_m);
    prf_sweep_unambiguous_range_m(prf_index) = ...
        candidate_unambiguous_range_m;
    prf_sweep_ambiguity_order(prf_index) = candidate_ambiguity_order;
    prf_sweep_apparent_range_m(prf_index) = true_range_m-...
        candidate_ambiguity_order*candidate_unambiguous_range_m;
end

figure('Name', 'P35 PRF sweep', 'Tag', 'P35');
subplot(1, 2, 1);
plot(prf_curve_hz/1e3, prf_curve_unambiguous_range_m/1e3, ...
    'LineWidth', 1.2);
hold on;
plot(prf_sweep_hz/1e3, prf_sweep_unambiguous_range_m/1e3, ...
    'ko', 'MarkerFaceColor', 'w');
grid on;
xlabel('Pulse repetition frequency (kHz)');
ylabel('Unambiguous range (km)');
title('Higher PRF shortens the listening interval');
subplot(1, 2, 2);
plot(prf_curve_hz/1e3, prf_curve_apparent_range_m/1e3, ...
    'LineWidth', 1.2);
hold on;
plot(prf_sweep_hz/1e3, prf_sweep_apparent_range_m/1e3, ...
    'ko', 'MarkerFaceColor', 'w');
grid on;
xlabel('Pulse repetition frequency (kHz)');
ylabel('Apparent range of the 18 km target (km)');
title('Changing PRF moves an aliased target non-monotonically');

%% Sweep 2: change only true range at the baseline PRF
range_sweep_m = linspace(0, 3*unambiguous_range_m, ...
    range_sweep_point_count);
range_sweep_apparent_m = zeros(size(range_sweep_m));
range_sweep_ambiguity_order = zeros(size(range_sweep_m));
for range_index = 1:numel(range_sweep_m)
    candidate_true_range_m = range_sweep_m(range_index);
    candidate_ambiguity_order = floor(candidate_true_range_m/...
        unambiguous_range_m);
    range_sweep_ambiguity_order(range_index) = candidate_ambiguity_order;
    range_sweep_apparent_m(range_index) = candidate_true_range_m-...
        candidate_ambiguity_order*unambiguous_range_m;
end
assert(all(range_sweep_apparent_m >= 0));
assert(all(range_sweep_apparent_m < unambiguous_range_m+...
    comparison_tolerance_m));

range_probe_apparent_m = zeros(size(range_probe_m));
range_probe_ambiguity_order = zeros(size(range_probe_m));
for range_index = 1:numel(range_probe_m)
    candidate_true_range_m = range_probe_m(range_index);
    candidate_ambiguity_order = floor(candidate_true_range_m/...
        unambiguous_range_m);
    range_probe_ambiguity_order(range_index) = candidate_ambiguity_order;
    range_probe_apparent_m(range_index) = candidate_true_range_m-...
        candidate_ambiguity_order*unambiguous_range_m;
end

below_boundary_m = unambiguous_range_m-boundary_probe_offset_m;
above_boundary_m = unambiguous_range_m+boundary_probe_offset_m;
below_apparent_m = below_boundary_m;
above_apparent_m = above_boundary_m-unambiguous_range_m;
assert(below_apparent_m > unambiguous_range_m-...
    2*boundary_probe_offset_m);
assert(abs(above_apparent_m-boundary_probe_offset_m) <= ...
    comparison_tolerance_m);

figure('Name', 'P35 true-range sweep', 'Tag', 'P35');
subplot(2, 1, 1);
plot(range_sweep_m/1e3, range_sweep_apparent_m/1e3, ...
    'LineWidth', 1.2);
hold on;
plot(range_probe_m/1e3, range_probe_apparent_m/1e3, ...
    'ko', 'MarkerFaceColor', 'w');
plot([0 max(range_sweep_m)]/1e3, ...
    [unambiguous_range_m unambiguous_range_m]/1e3, '--');
grid on;
xlabel('True range (km)');
ylabel('Apparent range (km)');
title('Fixed-PRF range folding is a sawtooth');
legend('Folded range', 'Probe targets', 'R_u', 'Location', 'best');
subplot(2, 1, 2);
stairs(range_sweep_m/1e3, range_sweep_ambiguity_order, ...
    'LineWidth', 1.2);
grid on;
xlabel('True range (km)');
ylabel('Ambiguity order q (intervals)');
title('Each boundary loses one more pulse identity');

%% Intentionally broken case: use a pulse label the receiver does not have
broken_apparent_range_m = true_range_m;
broken_ambiguity_order = 0;
broken_model_valid = false;
assert(broken_apparent_range_m > unambiguous_range_m);
assert(abs(broken_apparent_range_m-apparent_range_m) > ...
    unambiguous_range_m);

%% Recovery: restore modulo folding and the seeded received train exactly
recovered_pri_s = 1/prf_hz;
recovered_unambiguous_range_m = speed_of_light_mps/(2*prf_hz);
recovered_ambiguity_order = floor(true_range_m/...
    recovered_unambiguous_range_m);
recovered_apparent_range_m = true_range_m-...
    recovered_ambiguity_order*recovered_unambiguous_range_m;
recovered_stream = RandStream('mt19937ar', 'Seed', random_seed);
recovered_receive_train = noise_standard_deviation/sqrt(2)*(...
    randn(recovered_stream, 1, timeline_sample_count)+...
    1j*randn(recovered_stream, 1, timeline_sample_count));
for pulse_index = 0:pulse_count-1
    echo_start_sample = transmit_start_samples(pulse_index+1)+...
        round(round_trip_delay_s*sample_rate_hz);
    if echo_start_sample <= timeline_sample_count
        echo_indices = echo_start_sample:min(...
            echo_start_sample+pulse_width_samples-1, ...
            timeline_sample_count);
        recovered_receive_train(echo_indices) = ...
            recovered_receive_train(echo_indices)+echo_amplitude;
    end
end
recovered_model_valid = true;
integer_interval_invariance_m = true_range_m+...
    3*unambiguous_range_m;
invariant_apparent_range_m = integer_interval_invariance_m-...
    floor(integer_interval_invariance_m/unambiguous_range_m)*...
    unambiguous_range_m;
assert(recovered_pri_s == pri_s);
assert(recovered_ambiguity_order == ambiguity_order);
assert(abs(recovered_apparent_range_m-apparent_range_m) <= ...
    comparison_tolerance_m);
assert(abs(invariant_apparent_range_m-apparent_range_m) <= ...
    comparison_tolerance_m);
assert(isequal(recovered_receive_train, receive_train));

figure('Name', 'P35 pulse-identity failure and recovery', 'Tag', 'P35');
plot([1 2 3], [apparent_range_m broken_apparent_range_m ...
    recovered_apparent_range_m]/1e3, 'o-', 'LineWidth', 1.2, ...
    'MarkerSize', 7);
grid on;
xlim([0.7 3.3]);
set(gca, 'XTick', [1 2 3], 'XTickLabel', ...
    {'Physical fold', 'Broken pulse label', 'Recovered fold'});
ylabel('Reported range (km)');
title('Unavailable pulse identity creates a false unambiguous answer');

%% Printed metrics and retained workspace results
fprintf('\nP35 baseline unambiguous-range aliasing\n');
fprintf('PRF: %.3f kHz; PRI: %.3f microseconds\n', ...
    prf_hz/1e3, pri_s*1e6);
fprintf('Unambiguous range: %.6f km\n', unambiguous_range_m/1e3);
fprintf('True range: %.6f km; round-trip delay: %.6f microseconds\n', ...
    true_range_m/1e3, round_trip_delay_s*1e6);
fprintf('Ambiguity order: %d; apparent delay: %.6f microseconds\n', ...
    ambiguity_order, apparent_delay_s*1e6);
fprintf('Apparent range: %.6f km; sample-grid display error: %.3f m\n', ...
    apparent_range_m/1e3, measured_apparent_range_m-apparent_range_m);
fprintf('\nPRF sweep at fixed %.3f km true range\n', true_range_m/1e3);
fprintf('PRF_kHz   R_u_km   q   R_apparent_km\n');
for prf_index = 1:numel(prf_sweep_hz)
    fprintf('%7.3f  %7.3f  %d   %10.3f\n', ...
        prf_sweep_hz(prf_index)/1e3, ...
        prf_sweep_unambiguous_range_m(prf_index)/1e3, ...
        prf_sweep_ambiguity_order(prf_index), ...
        prf_sweep_apparent_range_m(prf_index)/1e3);
end
fprintf('\nTrue-range probes at fixed %.3f kHz PRF\n', prf_hz/1e3);
fprintf('R_true_km   q   R_apparent_km\n');
for range_index = 1:numel(range_probe_m)
    fprintf('%9.3f   %d   %10.3f\n', range_probe_m(range_index)/1e3, ...
        range_probe_ambiguity_order(range_index), ...
        range_probe_apparent_m(range_index)/1e3);
end
fprintf('Broken model reports %.3f km; recovery restores %.3f km.\n', ...
    broken_apparent_range_m/1e3, recovered_apparent_range_m/1e3);

results = struct();
results.random_seed = random_seed;
results.prf_hz = prf_hz;
results.pri_s = pri_s;
results.unambiguous_range_m = unambiguous_range_m;
results.true_range_m = true_range_m;
results.round_trip_delay_s = round_trip_delay_s;
results.ambiguity_order = ambiguity_order;
results.apparent_delay_s = apparent_delay_s;
results.apparent_range_m = apparent_range_m;
results.measured_apparent_range_m = measured_apparent_range_m;
results.prf_sweep_hz = prf_sweep_hz;
results.prf_sweep_unambiguous_range_m = ...
    prf_sweep_unambiguous_range_m;
results.prf_sweep_apparent_range_m = prf_sweep_apparent_range_m;
results.prf_sweep_ambiguity_order = prf_sweep_ambiguity_order;
results.range_probe_m = range_probe_m;
results.range_probe_apparent_m = range_probe_apparent_m;
results.range_probe_ambiguity_order = range_probe_ambiguity_order;
results.broken_model_valid = broken_model_valid;
results.broken_apparent_range_m = broken_apparent_range_m;
results.recovered_model_valid = recovered_model_valid;
results.recovered_apparent_range_m = recovered_apparent_range_m;
results.invariant_apparent_range_m = invariant_apparent_range_m;
results.resource_bounds = struct('pulse_count', pulse_count, ...
    'timeline_sample_count', timeline_sample_count, ...
    'range_sweep_point_count', range_sweep_point_count, ...
    'prf_curve_point_count', numel(prf_curve_hz), ...
    'estimated_stored_numeric_values', estimated_stored_numeric_values, ...
    'max_stored_numeric_values', max_stored_numeric_values);
