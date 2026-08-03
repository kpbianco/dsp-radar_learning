%% P34: Plot and Interpret the Ambiguity Function
% Guiding question:
% How does a waveform respond to simultaneous delay and Doppler mismatch?
% Model: chi[k,nu] = sum_n s[n] conj(s[n-k]) exp(-j*2*pi*nu*n/Fs).
% Delay shifts are zero filled. Magnitude is normalized by waveform energy.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P34'));

%% Visible deterministic controls and resource ceilings
random_seed = 3401;
sample_rate_hz = 10e6;
baseline_pulse_duration_s = 13e-6;
baseline_bandwidth_hz = 3e6;
baseline_code_length_chips = 13;
chip_duration_s = 1e-6;
doppler_limit_hz = 200e3;
doppler_bin_count = 101;
duration_sweep_s = [6.5e-6 13e-6 26e-6];
bandwidth_sweep_hz = [1.5e6 3e6 4.5e6];
code_length_sweep_chips = [7 13 31];
ridge_probe_doppler_hz = 120e3;
comparison_tolerance = 1e-10;
db_floor = -60;
max_signal_samples = 310;
max_surface_signal_samples = 160;
max_surface_delay_bins = 319;
max_doppler_bins = 121;
max_duration_cases = 3;
max_bandwidth_cases = 3;
max_code_length_cases = 3;
max_figure_groups = 7;
max_stored_numeric_values = 500000;
max_complex_multiply_accumulates = 10000000;

%% Validate controls before allocating ambiguity surfaces
positive_controls = [sample_rate_hz baseline_pulse_duration_s ...
    baseline_bandwidth_hz baseline_code_length_chips chip_duration_s ...
    doppler_limit_hz doppler_bin_count ridge_probe_doppler_hz ...
    comparison_tolerance max_signal_samples max_surface_signal_samples ...
    max_surface_delay_bins max_doppler_bins max_duration_cases ...
    max_bandwidth_cases max_code_length_cases max_figure_groups ...
    max_stored_numeric_values max_complex_multiply_accumulates];
assert(all(isfinite(positive_controls)) && all(positive_controls > 0));
assert(isfinite(random_seed) && random_seed == floor(random_seed) && ...
    random_seed == 3401);
assert(isfinite(db_floor) && db_floor < 0);
assert(baseline_bandwidth_hz < sample_rate_hz/2);
assert(ridge_probe_doppler_hz < doppler_limit_hz);
integer_controls = [baseline_code_length_chips doppler_bin_count ...
    max_signal_samples max_surface_signal_samples max_surface_delay_bins ...
    max_doppler_bins max_duration_cases max_bandwidth_cases ...
    max_code_length_cases max_figure_groups max_stored_numeric_values ...
    max_complex_multiply_accumulates];
assert(all(integer_controls == floor(integer_controls)));
assert(mod(doppler_bin_count, 2) == 1 && ...
    doppler_bin_count <= max_doppler_bins);
assert(numel(duration_sweep_s) >= 2 && ...
    numel(duration_sweep_s) <= max_duration_cases && ...
    all(isfinite(duration_sweep_s)) && all(duration_sweep_s > 0) && ...
    all(diff(duration_sweep_s) > 0));
assert(numel(bandwidth_sweep_hz) >= 2 && ...
    numel(bandwidth_sweep_hz) <= max_bandwidth_cases && ...
    all(isfinite(bandwidth_sweep_hz)) && ...
    all(bandwidth_sweep_hz > 0) && ...
    all(diff(bandwidth_sweep_hz) > 0) && ...
    max(bandwidth_sweep_hz) < sample_rate_hz/2);
assert(numel(code_length_sweep_chips) >= 2 && ...
    numel(code_length_sweep_chips) <= max_code_length_cases && ...
    all(isfinite(code_length_sweep_chips)) && ...
    all(code_length_sweep_chips == floor(code_length_sweep_chips)) && ...
    all(code_length_sweep_chips > 1) && ...
    all(diff(code_length_sweep_chips) > 0));
assert(any(abs(duration_sweep_s-baseline_pulse_duration_s) <= ...
    comparison_tolerance));
assert(any(abs(bandwidth_sweep_hz-baseline_bandwidth_hz) <= ...
    comparison_tolerance));
assert(any(code_length_sweep_chips == baseline_code_length_chips));

baseline_sample_count = round(baseline_pulse_duration_s*sample_rate_hz);
samples_per_chip = round(chip_duration_s*sample_rate_hz);
duration_sample_counts = round(duration_sweep_s*sample_rate_hz);
code_sample_counts = code_length_sweep_chips*samples_per_chip;
surface_delay_count = 2*baseline_sample_count-1;
doppler_axis_hz = linspace(-doppler_limit_hz, doppler_limit_hz, ...
    doppler_bin_count);
zero_doppler_index = (doppler_bin_count+1)/2;
estimated_stored_numeric_values = ...
    4*surface_delay_count*doppler_bin_count+...
    20*max_signal_samples+40*max_surface_delay_bins+...
    20*max_doppler_bins;
estimated_complex_multiply_accumulates = ...
    4*doppler_bin_count*baseline_sample_count^2+...
    sum(duration_sample_counts.^2+...
        duration_sample_counts*doppler_bin_count)+...
    numel(bandwidth_sweep_hz)*...
        (2*baseline_sample_count^2)+...
    sum(code_sample_counts.^2+code_sample_counts*doppler_bin_count)+...
    baseline_sample_count*surface_delay_count;
assert(baseline_sample_count >= 3 && ...
    baseline_sample_count <= max_surface_signal_samples);
assert(samples_per_chip >= 2);
assert(baseline_sample_count == ...
    baseline_code_length_chips*samples_per_chip);
assert(max([duration_sample_counts code_sample_counts]) <= ...
    max_signal_samples);
assert(surface_delay_count <= max_surface_delay_bins);
assert(estimated_stored_numeric_values <= max_stored_numeric_values);
assert(estimated_complex_multiply_accumulates <= ...
    max_complex_multiply_accumulates);
assert(max_figure_groups >= 7);
assert(abs(doppler_axis_hz(zero_doppler_index)) <= comparison_tolerance);

%% Build equal-duration rectangular, LFM, and seeded phase-coded waveforms
baseline_time_s = (0:baseline_sample_count-1)/sample_rate_hz;
centered_time_s = baseline_time_s-...
    (baseline_sample_count-1)/(2*sample_rate_hz);
rectangular_waveform = ones(1, baseline_sample_count);
chirp_rate_hz_per_s = baseline_bandwidth_hz/baseline_pulse_duration_s;
lfm_waveform = exp(1j*pi*chirp_rate_hz_per_s*centered_time_s.^2);

private_stream = RandStream('mt19937ar', 'Seed', random_seed);
maximum_code_length_chips = max(code_length_sweep_chips);
maximum_code_polarities = 2*(rand(private_stream, 1, ...
    maximum_code_length_chips) >= 0.5)-1;
phase_code_polarities = maximum_code_polarities(...
    1:baseline_code_length_chips);
phase_coded_waveform = complex(zeros(1, baseline_sample_count));
for chip_index = 1:baseline_code_length_chips
    chip_samples = (chip_index-1)*samples_per_chip+(1:samples_per_chip);
    phase_coded_waveform(chip_samples) = phase_code_polarities(chip_index);
end
assert(all(abs(phase_code_polarities) == 1));
assert(any(phase_code_polarities == 1) && any(phase_code_polarities == -1));
assert(numel(phase_coded_waveform) == baseline_sample_count);

figure('Name', 'P34 waveform phase histories', 'Tag', 'P34');
subplot(3, 1, 1);
plot(baseline_time_s*1e6, real(rectangular_waveform), 'LineWidth', 1.2);
grid on;
xlabel('Time within pulse (microseconds)');
ylabel('Real amplitude');
title('Rectangular pulse: no internal phase label');
ylim([-1.2 1.2]);
subplot(3, 1, 2);
plot(baseline_time_s*1e6, real(lfm_waveform), 'LineWidth', 1.1);
grid on;
xlabel('Time within pulse (microseconds)');
ylabel('Real amplitude');
title('LFM pulse: phase rate changes continuously');
ylim([-1.2 1.2]);
subplot(3, 1, 3);
stairs(baseline_time_s*1e6, real(phase_coded_waveform), ...
    'LineWidth', 1.2);
grid on;
xlabel('Time within pulse (microseconds)');
ylabel('BPSK chip polarity');
title('Seeded phase code: phase changes at chip boundaries');
ylim([-1.2 1.2]);

%% Baseline operation: explicit zero-filled delay and Doppler mismatch sum
baseline_delay_samples = -(baseline_sample_count-1):...
    (baseline_sample_count-1);
baseline_delay_us = 1e6*baseline_delay_samples/sample_rate_hz;
rectangular_ambiguity = explicit_ambiguity(rectangular_waveform, ...
    sample_rate_hz, baseline_delay_samples, doppler_axis_hz);
lfm_ambiguity = explicit_ambiguity(lfm_waveform, sample_rate_hz, ...
    baseline_delay_samples, doppler_axis_hz);
phase_code_ambiguity = explicit_ambiguity(phase_coded_waveform, ...
    sample_rate_hz, baseline_delay_samples, doppler_axis_hz);
zero_delay_index = baseline_sample_count;
origin_values = [rectangular_ambiguity(zero_doppler_index, ...
    zero_delay_index) lfm_ambiguity(zero_doppler_index, zero_delay_index) ...
    phase_code_ambiguity(zero_doppler_index, zero_delay_index)];
assert(max(abs(origin_values-1)) <= comparison_tolerance);
assert(max(rectangular_ambiguity(:)) <= 1+comparison_tolerance);
assert(max(lfm_ambiguity(:)) <= 1+comparison_tolerance);
assert(max(phase_code_ambiguity(:)) <= 1+comparison_tolerance);

figure('Name', 'P34 baseline ambiguity surfaces', 'Tag', 'P34');
subplot(1, 3, 1);
imagesc(baseline_delay_us, doppler_axis_hz/1e3, ...
    magnitude_db(rectangular_ambiguity, db_floor));
axis xy;
xlabel('Delay mismatch (microseconds)');
ylabel('Doppler mismatch (kHz)');
title('Rectangular ambiguity magnitude (dB)');
colorbar;
caxis([db_floor 0]);
subplot(1, 3, 2);
imagesc(baseline_delay_us, doppler_axis_hz/1e3, ...
    magnitude_db(lfm_ambiguity, db_floor));
axis xy;
xlabel('Delay mismatch (microseconds)');
ylabel('Doppler mismatch (kHz)');
title('LFM ambiguity magnitude (dB)');
colorbar;
caxis([db_floor 0]);
subplot(1, 3, 3);
imagesc(baseline_delay_us, doppler_axis_hz/1e3, ...
    magnitude_db(phase_code_ambiguity, db_floor));
axis xy;
xlabel('Delay mismatch (microseconds)');
ylabel('Doppler mismatch (kHz)');
title('Phase-code ambiguity magnitude (dB)');
colorbar;
caxis([db_floor 0]);

%% Zero-Doppler and zero-delay cuts expose different requirements
rectangular_delay_width_us = measure_mainlobe_width(baseline_delay_us, ...
    rectangular_ambiguity(zero_doppler_index, :));
lfm_delay_width_us = measure_mainlobe_width(baseline_delay_us, ...
    lfm_ambiguity(zero_doppler_index, :));
phase_code_delay_width_us = measure_mainlobe_width(baseline_delay_us, ...
    phase_code_ambiguity(zero_doppler_index, :));
rectangular_doppler_width_khz = measure_mainlobe_width(...
    doppler_axis_hz/1e3, rectangular_ambiguity(:, zero_delay_index).');
lfm_doppler_width_khz = measure_mainlobe_width(doppler_axis_hz/1e3, ...
    lfm_ambiguity(:, zero_delay_index).');
phase_code_doppler_width_khz = measure_mainlobe_width(...
    doppler_axis_hz/1e3, phase_code_ambiguity(:, zero_delay_index).');
phase_code_sidelobe_mask = abs(baseline_delay_samples) >= samples_per_chip;
phase_code_pslr_db = 20*log10(max(phase_code_ambiguity(...
    zero_doppler_index, phase_code_sidelobe_mask)));
assert(lfm_delay_width_us < rectangular_delay_width_us/5);
assert(phase_code_delay_width_us < rectangular_delay_width_us/5);

[~, lfm_ridge_indices] = max(lfm_ambiguity, [], 2);
lfm_ridge_delay_us = baseline_delay_us(lfm_ridge_indices);
[~, positive_probe_index] = min(abs(doppler_axis_hz-...
    ridge_probe_doppler_hz));
[~, negative_probe_index] = min(abs(doppler_axis_hz+...
    ridge_probe_doppler_hz));
expected_probe_delay_us = 1e6*ridge_probe_doppler_hz/...
    chirp_rate_hz_per_s;
measured_positive_ridge_us = lfm_ridge_delay_us(positive_probe_index);
measured_negative_ridge_us = lfm_ridge_delay_us(negative_probe_index);
assert(measured_positive_ridge_us > 0 && measured_negative_ridge_us < 0);
assert(abs(measured_positive_ridge_us-expected_probe_delay_us) <= ...
    2e6/sample_rate_hz);

figure('Name', 'P34 ambiguity cuts and LFM ridge', 'Tag', 'P34');
subplot(1, 3, 1);
plot(baseline_delay_us, magnitude_db(rectangular_ambiguity(...
    zero_doppler_index, :), db_floor), 'LineWidth', 1.1);
hold on;
plot(baseline_delay_us, magnitude_db(lfm_ambiguity(...
    zero_doppler_index, :), db_floor), 'LineWidth', 1.2);
plot(baseline_delay_us, magnitude_db(phase_code_ambiguity(...
    zero_doppler_index, :), db_floor), 'LineWidth', 1.1);
grid on;
xlabel('Delay mismatch (microseconds)');
ylabel('Normalized magnitude (dB)');
legend('Rectangular', 'LFM', 'Phase coded', 'Location', 'best');
title('Zero-Doppler cut: delay discrimination');
ylim([db_floor 3]);
subplot(1, 3, 2);
plot(doppler_axis_hz/1e3, magnitude_db(rectangular_ambiguity(:, ...
    zero_delay_index), db_floor), 'LineWidth', 1.1);
hold on;
plot(doppler_axis_hz/1e3, magnitude_db(lfm_ambiguity(:, ...
    zero_delay_index), db_floor), 'LineWidth', 1.2);
plot(doppler_axis_hz/1e3, magnitude_db(phase_code_ambiguity(:, ...
    zero_delay_index), db_floor), 'LineWidth', 1.1);
grid on;
xlabel('Doppler mismatch (kHz)');
ylabel('Normalized magnitude (dB)');
legend('Rectangular', 'LFM', 'Phase coded', 'Location', 'best');
title('Zero-delay cut: Doppler tolerance');
ylim([db_floor 3]);
subplot(1, 3, 3);
plot(lfm_ridge_delay_us, doppler_axis_hz/1e3, 'LineWidth', 1.2);
grid on;
xlabel('Delay at maximum LFM response (microseconds)');
ylabel('Doppler mismatch (kHz)');
title('LFM ridge: delay and Doppler are coupled');

%% Sweep 1: rectangular duration only
duration_delay_width_us = zeros(size(duration_sweep_s));
duration_doppler_width_khz = zeros(size(duration_sweep_s));
for duration_index = 1:numel(duration_sweep_s)
    candidate_count = duration_sample_counts(duration_index);
    candidate = ones(1, candidate_count);
    candidate_delays = -(candidate_count-1):(candidate_count-1);
    candidate_delay_us = 1e6*candidate_delays/sample_rate_hz;
    delay_cut = explicit_ambiguity(candidate, sample_rate_hz, ...
        candidate_delays, 0);
    doppler_cut = explicit_ambiguity(candidate, sample_rate_hz, 0, ...
        doppler_axis_hz);
    duration_delay_width_us(duration_index) = measure_mainlobe_width(...
        candidate_delay_us, delay_cut);
    duration_doppler_width_khz(duration_index) = measure_mainlobe_width(...
        doppler_axis_hz/1e3, doppler_cut.');
end
assert(all(diff(duration_delay_width_us) > 0));
assert(all(diff(duration_doppler_width_khz) < 0));

figure('Name', 'P34 rectangular-duration sweep', 'Tag', 'P34');
subplot(1, 2, 1);
plot(duration_sweep_s*1e6, duration_delay_width_us, 'o-', ...
    'LineWidth', 1.2);
grid on;
xlabel('Rectangular pulse duration (microseconds)');
ylabel('Full -3 dB delay width (microseconds)');
title('Longer unmodulated pulses widen delay response');
subplot(1, 2, 2);
plot(duration_sweep_s*1e6, duration_doppler_width_khz, 's-', ...
    'LineWidth', 1.2);
grid on;
xlabel('Rectangular pulse duration (microseconds)');
ylabel('Full -3 dB Doppler width (kHz)');
title('Longer coherent observation narrows Doppler response');

%% Sweep 2: LFM bandwidth only at fixed duration
bandwidth_delay_width_us = zeros(size(bandwidth_sweep_hz));
bandwidth_probe_ridge_us = zeros(size(bandwidth_sweep_hz));
for bandwidth_index = 1:numel(bandwidth_sweep_hz)
    candidate_bandwidth_hz = bandwidth_sweep_hz(bandwidth_index);
    candidate_chirp_rate = candidate_bandwidth_hz/...
        baseline_pulse_duration_s;
    candidate = exp(1j*pi*candidate_chirp_rate*centered_time_s.^2);
    zero_doppler_cut = explicit_ambiguity(candidate, sample_rate_hz, ...
        baseline_delay_samples, 0);
    probe_doppler_cut = explicit_ambiguity(candidate, sample_rate_hz, ...
        baseline_delay_samples, ridge_probe_doppler_hz);
    bandwidth_delay_width_us(bandwidth_index) = measure_mainlobe_width(...
        baseline_delay_us, zero_doppler_cut);
    [~, probe_delay_index] = max(probe_doppler_cut);
    bandwidth_probe_ridge_us(bandwidth_index) = ...
        baseline_delay_us(probe_delay_index);
end
assert(all(diff(bandwidth_delay_width_us) < 0));
assert(all(diff(abs(bandwidth_probe_ridge_us)) <= 0));

figure('Name', 'P34 LFM-bandwidth sweep', 'Tag', 'P34');
subplot(1, 2, 1);
plot(bandwidth_sweep_hz/1e6, bandwidth_delay_width_us, 'o-', ...
    'LineWidth', 1.2);
grid on;
xlabel('LFM swept bandwidth (MHz)');
ylabel('Full -3 dB delay width (microseconds)');
title('More LFM bandwidth narrows the zero-Doppler delay cut');
subplot(1, 2, 2);
plot(bandwidth_sweep_hz/1e6, bandwidth_probe_ridge_us, 's-', ...
    'LineWidth', 1.2);
grid on;
xlabel('LFM swept bandwidth (MHz)');
ylabel('Peak delay at +120 kHz Doppler (microseconds)');
title('Chirp slope controls the coupling displacement');

%% Sweep 3: code length only at fixed chip duration and seeded prefix
code_delay_width_us = zeros(size(code_length_sweep_chips));
code_doppler_width_khz = zeros(size(code_length_sweep_chips));
code_peak_sidelobe_db = zeros(size(code_length_sweep_chips));
for code_index = 1:numel(code_length_sweep_chips)
    candidate_chip_count = code_length_sweep_chips(code_index);
    candidate_count = candidate_chip_count*samples_per_chip;
    candidate = complex(zeros(1, candidate_count));
    candidate_polarities = maximum_code_polarities(1:candidate_chip_count);
    for chip_index = 1:candidate_chip_count
        chip_samples = (chip_index-1)*samples_per_chip+(1:samples_per_chip);
        candidate(chip_samples) = candidate_polarities(chip_index);
    end
    candidate_delays = -(candidate_count-1):(candidate_count-1);
    candidate_delay_us = 1e6*candidate_delays/sample_rate_hz;
    delay_cut = explicit_ambiguity(candidate, sample_rate_hz, ...
        candidate_delays, 0);
    doppler_cut = explicit_ambiguity(candidate, sample_rate_hz, 0, ...
        doppler_axis_hz);
    code_delay_width_us(code_index) = measure_mainlobe_width(...
        candidate_delay_us, delay_cut);
    code_doppler_width_khz(code_index) = measure_mainlobe_width(...
        doppler_axis_hz/1e3, doppler_cut.');
    sidelobe_mask = abs(candidate_delays) >= samples_per_chip;
    code_peak_sidelobe_db(code_index) = 20*log10(max(...
        delay_cut(sidelobe_mask)));
end
assert(all(diff(code_doppler_width_khz) < 0));
assert(all(code_delay_width_us < 2*chip_duration_s*1e6));

figure('Name', 'P34 phase-code-length sweep', 'Tag', 'P34');
subplot(1, 3, 1);
plot(code_length_sweep_chips, code_delay_width_us, 'o-', ...
    'LineWidth', 1.2);
grid on;
xlabel('Code length (chips)');
ylabel('Full -3 dB delay width (microseconds)');
title('Chip duration keeps the delay cell narrow');
subplot(1, 3, 2);
plot(code_length_sweep_chips, code_doppler_width_khz, 's-', ...
    'LineWidth', 1.2);
grid on;
xlabel('Code length (chips)');
ylabel('Full -3 dB Doppler width (kHz)');
title('More chips lengthen coherent observation');
subplot(1, 3, 3);
plot(code_length_sweep_chips, code_peak_sidelobe_db, 'd-', ...
    'LineWidth', 1.2);
grid on;
xlabel('Code length (chips)');
ylabel('Peak zero-Doppler delay sidelobe (dB)');
title('Sidelobes also depend on the code pattern');

%% Intentionally broken case: circular delay wraparound is not propagation
correct_rectangular_delay_cut = rectangular_ambiguity(...
    zero_doppler_index, :);
broken_circular_delay_cut = zeros(size(baseline_delay_samples));
for delay_index = 1:numel(baseline_delay_samples)
    delay_samples = baseline_delay_samples(delay_index);
    current_indices = 1:baseline_sample_count;
    wrapped_shifted_indices = mod((0:baseline_sample_count-1)-...
        delay_samples, baseline_sample_count)+1;
    broken_circular_delay_cut(delay_index) = abs(sum(...
        rectangular_waveform(current_indices).*conj(...
        rectangular_waveform(wrapped_shifted_indices))))/...
        sum(abs(rectangular_waveform).^2);
end
correct_extreme_delay_magnitude = correct_rectangular_delay_cut(1);
broken_extreme_delay_magnitude = broken_circular_delay_cut(1);
broken_model_valid = false;
assert(correct_extreme_delay_magnitude <= ...
    1/baseline_sample_count+comparison_tolerance);
assert(broken_extreme_delay_magnitude >= 1-comparison_tolerance);

%% Recovery: restore zero filling and recreate the private code exactly
recovered_stream = RandStream('mt19937ar', 'Seed', random_seed);
recovered_maximum_code_polarities = 2*(rand(recovered_stream, 1, ...
    maximum_code_length_chips) >= 0.5)-1;
recovered_phase_code_polarities = recovered_maximum_code_polarities(...
    1:baseline_code_length_chips);
recovered_phase_coded_waveform = complex(zeros(1, baseline_sample_count));
for chip_index = 1:baseline_code_length_chips
    chip_samples = (chip_index-1)*samples_per_chip+(1:samples_per_chip);
    recovered_phase_coded_waveform(chip_samples) = ...
        recovered_phase_code_polarities(chip_index);
end
recovered_phase_code_ambiguity = explicit_ambiguity(...
    recovered_phase_coded_waveform, sample_rate_hz, ...
    baseline_delay_samples, doppler_axis_hz);
recovered_model_valid = true;
assert(isequal(recovered_phase_code_polarities, phase_code_polarities));
assert(isequal(recovered_phase_coded_waveform, phase_coded_waveform));
assert(isequal(recovered_phase_code_ambiguity, phase_code_ambiguity));

figure('Name', 'P34 circular-shift failure and recovery', 'Tag', 'P34');
subplot(1, 2, 1);
plot(baseline_delay_us, magnitude_db(correct_rectangular_delay_cut, ...
    db_floor), 'LineWidth', 1.2);
hold on;
plot(baseline_delay_us, magnitude_db(broken_circular_delay_cut, ...
    db_floor), '--', 'LineWidth', 1.2);
grid on;
xlabel('Delay mismatch (microseconds)');
ylabel('Normalized magnitude (dB)');
legend('Correct zero-filled shift', 'Broken circular shift', ...
    'Location', 'best');
title('Circular wrap creates impossible overlap at extreme delay');
ylim([db_floor 3]);
subplot(1, 2, 2);
plot(baseline_delay_us, magnitude_db(phase_code_ambiguity(...
    zero_doppler_index, :), db_floor), 'LineWidth', 1.2);
hold on;
plot(baseline_delay_us, magnitude_db(recovered_phase_code_ambiguity(...
    zero_doppler_index, :), db_floor), '--', 'LineWidth', 1.0);
grid on;
xlabel('Delay mismatch (microseconds)');
ylabel('Normalized magnitude (dB)');
legend('Original zero-filled result', 'Recovered exact result', ...
    'Location', 'best');
title('Recovery restores the deterministic ambiguity cut');
ylim([db_floor 3]);

%% Report metrics with units and model boundaries
fprintf('\nP34 ambiguity-function baseline\n');
fprintf('  Seed: %d (private phase-code stream)\n', random_seed);
fprintf('  Fs: %.3f MHz, duration: %.3f us, LFM bandwidth: %.3f MHz\n', ...
    sample_rate_hz/1e6, baseline_pulse_duration_s*1e6, ...
    baseline_bandwidth_hz/1e6);
fprintf('  Code: %d chips, %.3f us/chip\n', ...
    baseline_code_length_chips, chip_duration_s*1e6);
fprintf('  Full -3 dB delay widths [rect LFM code]: [%.3f %.3f %.3f] us\n', ...
    rectangular_delay_width_us, lfm_delay_width_us, ...
    phase_code_delay_width_us);
fprintf('  Full -3 dB Doppler widths [rect LFM code]: [%.3f %.3f %.3f] kHz\n', ...
    rectangular_doppler_width_khz, lfm_doppler_width_khz, ...
    phase_code_doppler_width_khz);
fprintf('  Phase-code peak zero-Doppler delay sidelobe: %.3f dB\n', ...
    phase_code_pslr_db);
fprintf('  LFM ridge at +%.1f kHz: measured %.3f us, ideal %.3f us\n', ...
    ridge_probe_doppler_hz/1e3, measured_positive_ridge_us, ...
    expected_probe_delay_us);
fprintf('  Circular-shift extreme delay: correct %.6f, broken %.6f\n', ...
    correct_extreme_delay_magnitude, broken_extreme_delay_magnitude);
fprintf('  Operation estimate: %d / %d complex multiply-accumulates\n', ...
    estimated_complex_multiply_accumulates, ...
    max_complex_multiply_accumulates);
fprintf('  Recovery exact: %d; broken model valid: %d; recovered model valid: %d\n', ...
    isequal(recovered_phase_code_ambiguity, phase_code_ambiguity), ...
    broken_model_valid, recovered_model_valid);
fprintf(['  Simulation only: no noise, clutter, propagation, detector, RF, ' ...
    'hardware, or field validation.\n']);

%% Local functions keep the underlying operation visible
function ambiguity_magnitude = explicit_ambiguity(signal, sample_rate_hz, ...
    delay_samples, doppler_hz)
% |chi[k,nu]|/E uses a linear, zero-filled shift rather than circular wrap.
    assert(isvector(signal) && ~isempty(signal));
    assert(isfinite(sample_rate_hz) && sample_rate_hz > 0);
    assert(isvector(delay_samples) && all(isfinite(delay_samples)) && ...
        all(delay_samples == floor(delay_samples)));
    assert(isvector(doppler_hz) && all(isfinite(doppler_hz)));
    signal = reshape(signal, 1, []);
    delay_samples = reshape(delay_samples, 1, []);
    doppler_hz = reshape(doppler_hz, 1, []);
    sample_count = numel(signal);
    assert(all(abs(delay_samples) < sample_count));
    signal_energy = sum(abs(signal).^2);
    assert(isfinite(signal_energy) && signal_energy > 0);
    ambiguity_magnitude = zeros(numel(doppler_hz), numel(delay_samples));
    for delay_index = 1:numel(delay_samples)
        delay = delay_samples(delay_index);
        if delay >= 0
            current_indices = (1+delay):sample_count;
            shifted_indices = 1:(sample_count-delay);
        else
            current_indices = 1:(sample_count+delay);
            shifted_indices = (1-delay):sample_count;
        end
        zero_filled_overlap = signal(current_indices).*...
            conj(signal(shifted_indices));
        overlap_time_s = (current_indices-1)/sample_rate_hz;
        for doppler_index = 1:numel(doppler_hz)
            doppler_phasor = exp(-1j*2*pi*doppler_hz(doppler_index)*...
                overlap_time_s);
            ambiguity_magnitude(doppler_index, delay_index) = abs(sum(...
                zero_filled_overlap.*doppler_phasor))/signal_energy;
        end
    end
end

function width = measure_mainlobe_width(axis_values, magnitude)
% Interpolate the nearest -3 dB crossings around the largest sampled peak.
    axis_values = reshape(axis_values, 1, []);
    magnitude = reshape(magnitude, 1, []);
    assert(numel(axis_values) == numel(magnitude) && numel(magnitude) >= 3);
    assert(all(isfinite(axis_values)) && all(diff(axis_values) > 0));
    assert(all(isfinite(magnitude)) && all(magnitude >= 0));
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
    assert(left_index < peak_index && right_index > peak_index);
    assert(magnitude(left_index) < threshold && ...
        magnitude(right_index) < threshold);
    left_fraction = (threshold-magnitude(left_index))/...
        (magnitude(left_index+1)-magnitude(left_index));
    left_crossing = axis_values(left_index)+left_fraction*...
        (axis_values(left_index+1)-axis_values(left_index));
    right_fraction = (threshold-magnitude(right_index-1))/...
        (magnitude(right_index)-magnitude(right_index-1));
    right_crossing = axis_values(right_index-1)+right_fraction*...
        (axis_values(right_index)-axis_values(right_index-1));
    width = right_crossing-left_crossing;
    assert(isfinite(width) && width > 0);
end

function values_db = magnitude_db(values, floor_db)
    assert(isfinite(floor_db) && floor_db < 0);
    floor_linear = 10^(floor_db/20);
    values_db = 20*log10(max(abs(values), floor_linear));
end
