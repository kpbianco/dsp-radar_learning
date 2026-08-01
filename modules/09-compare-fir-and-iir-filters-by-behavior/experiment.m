%% P09 - Compare FIR and IIR Filters by Behavior
% Guiding question:
% How can two filters with similar magnitude response behave differently in
% time and phase?
%
% Base MATLAB only. The FIR sum and IIR recurrence are evaluated explicitly.

%% Visible controls - validate these before allocating experiment data
random_seed = 909;
fs_hz = 1000;
cutoff_hz = 100;
fir_tap_count = 21;
fir_design_cutoff_scale = 1.20;
iir_q = 1/sqrt(2);
response_sample_count = 160;
record_sample_count = 400;
step_onset_sample = 15;
pulse_onset_sample = 30;
pulse_width_samples = 12;
desired_tone_hz = 60;
interferer_tone_hz = 250;
noise_rms_v = 0.15;
frequency_grid_count = 1025;
settling_tolerance_fraction = 0.02;
tail_threshold = 1e-4;
comparison_tolerance = 1e-9;

fir_tap_count_sweep = [9 21 41];
iir_q_sweep = [0.50 1/sqrt(2) 2.00];
aggressive_pole_angle_hz = cutoff_hz;
broken_pole_radius = 1.02;
recovered_pole_radius = 0.98;

max_record_samples = 512;
max_response_samples = 256;
max_fir_taps = 81;
max_frequency_grid_count = 2049;
max_sweep_cases = 8;
max_figure_groups = 6;

assert(isscalar(random_seed) && isnumeric(random_seed) && isreal(random_seed) && ...
    ~islogical(random_seed) && isfinite(random_seed) && random_seed >= 0 && ...
    random_seed <= 2^32-1 && random_seed == floor(random_seed), ...
    'random_seed must be an integer scalar from zero through 2^32-1.');
assert(isscalar(fs_hz) && isnumeric(fs_hz) && isreal(fs_hz) && ...
    isfinite(fs_hz) && fs_hz > 0, 'fs_hz must be finite and positive.');
assert(isscalar(cutoff_hz) && isnumeric(cutoff_hz) && isreal(cutoff_hz) && ...
    isfinite(cutoff_hz) && cutoff_hz > 0 && cutoff_hz < fs_hz/2, ...
    'cutoff_hz must lie strictly between DC and Nyquist.');
assert(isscalar(fir_tap_count) && isnumeric(fir_tap_count) && ...
    isreal(fir_tap_count) && isfinite(fir_tap_count) && ...
    fir_tap_count >= 5 && fir_tap_count == floor(fir_tap_count) && ...
    mod(fir_tap_count, 2) == 1, ...
    'fir_tap_count must be an odd integer of at least five.');
assert(isscalar(fir_design_cutoff_scale) && ...
    isnumeric(fir_design_cutoff_scale) && isreal(fir_design_cutoff_scale) && ...
    isfinite(fir_design_cutoff_scale) && fir_design_cutoff_scale > 1 && ...
    fir_design_cutoff_scale*cutoff_hz < fs_hz/2, ...
    'The calibrated FIR design cutoff must remain below Nyquist.');
assert(isscalar(iir_q) && isnumeric(iir_q) && isreal(iir_q) && ...
    isfinite(iir_q) && iir_q > 0, 'iir_q must be finite and positive.');
assert(isscalar(response_sample_count) && isnumeric(response_sample_count) && ...
    isreal(response_sample_count) && isfinite(response_sample_count) && ...
    response_sample_count >= 64 && response_sample_count == floor(response_sample_count), ...
    'response_sample_count must be an integer of at least 64.');
assert(isscalar(record_sample_count) && isnumeric(record_sample_count) && ...
    isreal(record_sample_count) && isfinite(record_sample_count) && ...
    record_sample_count >= response_sample_count && ...
    record_sample_count == floor(record_sample_count), ...
    'record_sample_count must be an integer at least as large as the response.');
assert(isscalar(step_onset_sample) && isnumeric(step_onset_sample) && ...
    isreal(step_onset_sample) && ~islogical(step_onset_sample) && ...
    isfinite(step_onset_sample) && step_onset_sample == floor(step_onset_sample) && ...
    step_onset_sample >= 0 && step_onset_sample < response_sample_count, ...
    'step_onset_sample must be a valid zero-based response index.');
assert(isscalar(pulse_onset_sample) && isnumeric(pulse_onset_sample) && ...
    isreal(pulse_onset_sample) && ~islogical(pulse_onset_sample) && ...
    isfinite(pulse_onset_sample) && pulse_onset_sample == floor(pulse_onset_sample) && ...
    pulse_onset_sample >= 0 && pulse_onset_sample < response_sample_count, ...
    'pulse_onset_sample must be a valid zero-based response index.');
assert(isscalar(pulse_width_samples) && isnumeric(pulse_width_samples) && ...
    isreal(pulse_width_samples) && ~islogical(pulse_width_samples) && ...
    isfinite(pulse_width_samples) && pulse_width_samples == floor(pulse_width_samples) && ...
    pulse_width_samples >= 1 && ...
    pulse_onset_sample+pulse_width_samples <= response_sample_count, ...
    'The pulse must have positive integer width and fit in the response record.');
assert(isscalar(desired_tone_hz) && isnumeric(desired_tone_hz) && ...
    isreal(desired_tone_hz) && ~islogical(desired_tone_hz) && ...
    isfinite(desired_tone_hz) && ...
    desired_tone_hz > 0 && desired_tone_hz < cutoff_hz, ...
    'desired_tone_hz must lie inside the intended passband.');
assert(isscalar(interferer_tone_hz) && isnumeric(interferer_tone_hz) && ...
    isreal(interferer_tone_hz) && ~islogical(interferer_tone_hz) && ...
    isfinite(interferer_tone_hz) && ...
    interferer_tone_hz > cutoff_hz && interferer_tone_hz < fs_hz/2, ...
    'interferer_tone_hz must lie between cutoff and Nyquist.');
assert(isscalar(noise_rms_v) && isnumeric(noise_rms_v) && ...
    isreal(noise_rms_v) && ~islogical(noise_rms_v) && ...
    isfinite(noise_rms_v) && noise_rms_v >= 0, ...
    'noise_rms_v must be finite and nonnegative.');
assert(isscalar(frequency_grid_count) && isnumeric(frequency_grid_count) && ...
    isreal(frequency_grid_count) && ~islogical(frequency_grid_count) && ...
    isfinite(frequency_grid_count) && ...
    frequency_grid_count == floor(frequency_grid_count) && ...
    frequency_grid_count >= 257, 'frequency_grid_count must be an integer >= 257.');
assert(isscalar(settling_tolerance_fraction) && ...
    isnumeric(settling_tolerance_fraction) && isreal(settling_tolerance_fraction) && ...
    ~islogical(settling_tolerance_fraction) && ...
    isfinite(settling_tolerance_fraction) && settling_tolerance_fraction > 0 && ...
    settling_tolerance_fraction < 0.25, ...
    'settling_tolerance_fraction must be between zero and 0.25.');
assert(isscalar(tail_threshold) && isnumeric(tail_threshold) && ...
    isreal(tail_threshold) && ~islogical(tail_threshold) && ...
    isfinite(tail_threshold) && tail_threshold > 0, ...
    'tail_threshold must be finite and positive.');
assert(isscalar(comparison_tolerance) && isnumeric(comparison_tolerance) && ...
    isreal(comparison_tolerance) && ~islogical(comparison_tolerance) && ...
    isfinite(comparison_tolerance) && ...
    comparison_tolerance > 0, 'comparison_tolerance must be finite and positive.');
assert(isvector(fir_tap_count_sweep) && isnumeric(fir_tap_count_sweep) && ...
    isreal(fir_tap_count_sweep) && all(isfinite(fir_tap_count_sweep)) && ...
    numel(fir_tap_count_sweep) >= 2 && numel(fir_tap_count_sweep) <= max_sweep_cases && ...
    all(fir_tap_count_sweep >= 5) && ...
    all(fir_tap_count_sweep == floor(fir_tap_count_sweep)) && ...
    all(mod(fir_tap_count_sweep, 2) == 1) && all(diff(fir_tap_count_sweep) > 0), ...
    'FIR sweep tap counts must be increasing odd integers.');
assert(isvector(iir_q_sweep) && isnumeric(iir_q_sweep) && isreal(iir_q_sweep) && ...
    all(isfinite(iir_q_sweep)) && numel(iir_q_sweep) >= 2 && ...
    numel(iir_q_sweep) <= max_sweep_cases && all(iir_q_sweep > 0) && ...
    all(diff(iir_q_sweep) > 0), 'IIR Q sweep must be finite, positive, and increasing.');
assert(isscalar(aggressive_pole_angle_hz) && isnumeric(aggressive_pole_angle_hz) && ...
    isreal(aggressive_pole_angle_hz) && ~islogical(aggressive_pole_angle_hz) && ...
    isfinite(aggressive_pole_angle_hz) && ...
    aggressive_pole_angle_hz > 0 && aggressive_pole_angle_hz < fs_hz/2, ...
    'Aggressive pole angle must map inside the sampled band.');
assert(isscalar(broken_pole_radius) && isnumeric(broken_pole_radius) && ...
    isreal(broken_pole_radius) && ~islogical(broken_pole_radius) && ...
    isfinite(broken_pole_radius) && ...
    broken_pole_radius > 1, 'The deliberately broken pole radius must exceed one.');
assert(isscalar(recovered_pole_radius) && isnumeric(recovered_pole_radius) && ...
    isreal(recovered_pole_radius) && ~islogical(recovered_pole_radius) && ...
    isfinite(recovered_pole_radius) && ...
    recovered_pole_radius > 0 && recovered_pole_radius < 1, ...
    'The recovered pole radius must lie strictly inside the unit circle.');
assert(isequal(max_record_samples, 512) && ...
    isequal(max_response_samples, 256) && isequal(max_fir_taps, 81) && ...
    isequal(max_frequency_grid_count, 2049) && isequal(max_sweep_cases, 8) && ...
    isequal(max_figure_groups, 6), 'P09 resource ceilings must remain fixed.');
assert(record_sample_count <= max_record_samples && ...
    response_sample_count <= max_response_samples && ...
    fir_tap_count <= max_fir_taps && max(fir_tap_count_sweep) <= max_fir_taps && ...
    frequency_grid_count <= max_frequency_grid_count && max_figure_groups == 6, ...
    'Configured experiment exceeds a fixed P09 resource ceiling.');

%% Explicit FIR and IIR coefficient construction
% FIR: truncate an ideal low-pass impulse response with a symmetric Hamming
% window, then normalize its coefficient sum to one volt/volt at DC.
fir_half_order = (fir_tap_count-1)/2;
fir_design_cutoff_hz = fir_design_cutoff_scale*cutoff_hz;
fir_b = zeros(1, fir_tap_count);
for tap_index = 0:fir_tap_count-1
    centered_index = tap_index-fir_half_order;
    sinc_argument = 2*fir_design_cutoff_hz/fs_hz*centered_index;
    if centered_index == 0
        sinc_value = 1;
    else
        sinc_value = sin(pi*sinc_argument)/(pi*sinc_argument);
    end
    ideal_value = 2*fir_design_cutoff_hz/fs_hz*sinc_value;
    window_value = 0.54-0.46*cos(2*pi*tap_index/(fir_tap_count-1));
    fir_b(tap_index+1) = ideal_value*window_value;
end
fir_b = fir_b/sum(fir_b);

% IIR: bilinear-transform second-order low-pass coefficients. Q=1/sqrt(2)
% gives the Butterworth baseline. a(1)=1 and feedback is subtracted below.
iir_k = tan(pi*cutoff_hz/fs_hz);
iir_norm = 1/(1+iir_k/iir_q+iir_k^2);
iir_b = [iir_k^2 2*iir_k^2 iir_k^2]*iir_norm;
iir_a = [1 2*(iir_k^2-1)*iir_norm ...
    (1-iir_k/iir_q+iir_k^2)*iir_norm];
iir_discriminant = iir_a(2)^2-4*iir_a(3);
iir_poles = [(-iir_a(2)+sqrt(complex(iir_discriminant)))/2 ...
    (-iir_a(2)-sqrt(complex(iir_discriminant)))/2];

assert(abs(sum(fir_b)-1) < comparison_tolerance, 'FIR DC gain must be one.');
assert(max(abs(fir_b-fliplr(fir_b))) < comparison_tolerance, ...
    'FIR coefficients must remain symmetric for linear phase.');
assert(abs(sum(iir_b)/sum(iir_a)-1) < comparison_tolerance, ...
    'IIR DC gain must be one.');
assert(all(abs(iir_poles) < 1), 'Baseline IIR poles must remain inside the unit circle.');

%% Frequency response from the defining sums - no freqz or grpdelay
frequency_hz = linspace(0, fs_hz/2, frequency_grid_count);
omega_rad_per_sample = 2*pi*frequency_hz/fs_hz;
fir_response = zeros(1, frequency_grid_count);
iir_response = zeros(1, frequency_grid_count);
for frequency_index = 1:frequency_grid_count
    omega_now = omega_rad_per_sample(frequency_index);
    fir_sum = 0;
    for tap_index = 0:fir_tap_count-1
        fir_sum = fir_sum+fir_b(tap_index+1)*exp(-1j*omega_now*tap_index);
    end
    iir_numerator = iir_b(1)+iir_b(2)*exp(-1j*omega_now)+ ...
        iir_b(3)*exp(-2j*omega_now);
    iir_denominator = iir_a(1)+iir_a(2)*exp(-1j*omega_now)+ ...
        iir_a(3)*exp(-2j*omega_now);
    fir_response(frequency_index) = fir_sum;
    iir_response(frequency_index) = iir_numerator/iir_denominator;
end

fir_magnitude_db = 20*log10(max(abs(fir_response), 1e-8));
iir_magnitude_db = 20*log10(max(abs(iir_response), 1e-8));
fir_phase_rad = unwrap(angle(fir_response));
iir_phase_rad = unwrap(angle(iir_response));
group_delay_frequency_hz = (frequency_hz(1:end-1)+frequency_hz(2:end))/2;
fir_group_delay_samples = -diff(fir_phase_rad)./diff(omega_rad_per_sample);
iir_group_delay_samples = -diff(iir_phase_rad)./diff(omega_rad_per_sample);

fir_cutoff_index = find(abs(fir_response) <= 1/sqrt(2), 1, 'first');
iir_cutoff_index = find(abs(iir_response) <= 1/sqrt(2), 1, 'first');
assert(~isempty(fir_cutoff_index) && ~isempty(iir_cutoff_index), ...
    'Both low-pass responses must cross minus three decibels.');
fir_measured_cutoff_hz = frequency_hz(fir_cutoff_index);
iir_measured_cutoff_hz = frequency_hz(iir_cutoff_index);
cutoff_mismatch_hz = abs(fir_measured_cutoff_hz-iir_measured_cutoff_hz);
assert(cutoff_mismatch_hz <= 0.03*cutoff_hz, ...
    'Baseline FIR and IIR minus-three-decibel cutoffs are no longer comparable.');

[~, desired_frequency_index] = min(abs(frequency_hz-desired_tone_hz));
[~, interferer_frequency_index] = min(abs(frequency_hz-interferer_tone_hz));
[~, desired_delay_index] = min(abs(group_delay_frequency_hz-desired_tone_hz));
[~, interferer_delay_index] = min(abs(group_delay_frequency_hz-interferer_tone_hz));
fir_desired_group_delay_samples = fir_group_delay_samples(desired_delay_index);
iir_desired_group_delay_samples = iir_group_delay_samples(desired_delay_index);
fir_interferer_group_delay_samples = fir_group_delay_samples(interferer_delay_index);
iir_interferer_group_delay_samples = iir_group_delay_samples(interferer_delay_index);
assert(abs(fir_desired_group_delay_samples-fir_half_order) < 1e-6 && ...
    abs(fir_interferer_group_delay_samples-fir_half_order) < 1e-6, ...
    'Symmetric FIR group delay must equal half its order away from response nulls.');

%% Deterministic impulse, step, pulse, and noisy multitone inputs
response_sample_index = 0:response_sample_count-1;
response_time_ms = 1000*response_sample_index/fs_hz;
impulse_input_v = zeros(1, response_sample_count);
impulse_input_v(1) = 1;
step_input_v = zeros(1, response_sample_count);
step_input_v(step_onset_sample+1:end) = 1;
pulse_input_v = zeros(1, response_sample_count);
pulse_input_v(pulse_onset_sample+1:pulse_onset_sample+pulse_width_samples) = 1;

random_stream = RandStream('mt19937ar', 'Seed', random_seed);
record_sample_index = 0:record_sample_count-1;
record_time_ms = 1000*record_sample_index/fs_hz;
standard_normal_noise = randn(random_stream, 1, record_sample_count);
seed_signature = standard_normal_noise(1:4);
clean_multitone_v = sin(2*pi*desired_tone_hz*record_sample_index/fs_hz)+ ...
    0.65*sin(2*pi*interferer_tone_hz*record_sample_index/fs_hz+0.35);
noisy_multitone_v = clean_multitone_v+noise_rms_v*standard_normal_noise;

% Explicit causal FIR convolution and explicit causal IIR recurrence.
input_matrix_v = [impulse_input_v; step_input_v; pulse_input_v];
fir_output_matrix_v = zeros(size(input_matrix_v));
iir_output_matrix_v = zeros(size(input_matrix_v));
for signal_index = 1:size(input_matrix_v, 1)
    for output_index = 0:response_sample_count-1
        fir_accumulator = 0;
        for tap_index = 0:fir_tap_count-1
            input_index = output_index-tap_index;
            if input_index >= 0
                fir_accumulator = fir_accumulator+ ...
                    fir_b(tap_index+1)*input_matrix_v(signal_index, input_index+1);
            end
        end
        fir_output_matrix_v(signal_index, output_index+1) = fir_accumulator;

        iir_accumulator = iir_b(1)*input_matrix_v(signal_index, output_index+1);
        if output_index >= 1
            iir_accumulator = iir_accumulator+ ...
                iir_b(2)*input_matrix_v(signal_index, output_index)- ...
                iir_a(2)*iir_output_matrix_v(signal_index, output_index);
        end
        if output_index >= 2
            iir_accumulator = iir_accumulator+ ...
                iir_b(3)*input_matrix_v(signal_index, output_index-1)- ...
                iir_a(3)*iir_output_matrix_v(signal_index, output_index-1);
        end
        iir_output_matrix_v(signal_index, output_index+1) = iir_accumulator;
    end
end

fir_impulse_v = fir_output_matrix_v(1, :);
iir_impulse_v = iir_output_matrix_v(1, :);
fir_step_v = fir_output_matrix_v(2, :);
iir_step_v = iir_output_matrix_v(2, :);
fir_pulse_v = fir_output_matrix_v(3, :);
iir_pulse_v = iir_output_matrix_v(3, :);

fir_multitone_v = zeros(1, record_sample_count);
iir_multitone_v = zeros(1, record_sample_count);
for output_index = 0:record_sample_count-1
    fir_accumulator = 0;
    for tap_index = 0:fir_tap_count-1
        input_index = output_index-tap_index;
        if input_index >= 0
            fir_accumulator = fir_accumulator+ ...
                fir_b(tap_index+1)*noisy_multitone_v(input_index+1);
        end
    end
    fir_multitone_v(output_index+1) = fir_accumulator;

    iir_accumulator = iir_b(1)*noisy_multitone_v(output_index+1);
    if output_index >= 1
        iir_accumulator = iir_accumulator+iir_b(2)*noisy_multitone_v(output_index)- ...
            iir_a(2)*iir_multitone_v(output_index);
    end
    if output_index >= 2
        iir_accumulator = iir_accumulator+iir_b(3)*noisy_multitone_v(output_index-1)- ...
            iir_a(3)*iir_multitone_v(output_index-1);
    end
    iir_multitone_v(output_index+1) = iir_accumulator;
end

fir_last_tail_index = find(abs(fir_impulse_v) > tail_threshold, 1, 'last');
iir_last_tail_index = find(abs(iir_impulse_v) > tail_threshold, 1, 'last');
fir_tail_metric_found = ~isempty(fir_last_tail_index);
iir_tail_metric_found = ~isempty(iir_last_tail_index);
if fir_tail_metric_found
    fir_last_tail_sample = fir_last_tail_index-1;
else
    fir_last_tail_sample = NaN;
end
if iir_tail_metric_found
    iir_last_tail_sample = iir_last_tail_index-1;
else
    iir_last_tail_sample = NaN;
end
fir_step_overshoot_percent = 100*(max(fir_step_v)-1);
iir_step_overshoot_percent = 100*(max(iir_step_v)-1);
fir_settling_sample = NaN;
iir_settling_sample = NaN;
fir_settling_metric_found = false;
iir_settling_metric_found = false;
for candidate_index = step_onset_sample:response_sample_count-1
    if all(abs(fir_step_v(candidate_index+1:end)-1) <= settling_tolerance_fraction)
        fir_settling_sample = candidate_index;
        fir_settling_metric_found = true;
        break;
    end
end
for candidate_index = step_onset_sample:response_sample_count-1
    if all(abs(iir_step_v(candidate_index+1:end)-1) <= settling_tolerance_fraction)
        iir_settling_sample = candidate_index;
        iir_settling_metric_found = true;
        break;
    end
end
if fir_settling_metric_found
    fir_settling_after_onset_samples = fir_settling_sample-step_onset_sample;
else
    fir_settling_after_onset_samples = NaN;
end
if iir_settling_metric_found
    iir_settling_after_onset_samples = iir_settling_sample-step_onset_sample;
else
    iir_settling_after_onset_samples = NaN;
end

fir_multiplications_per_sample = fir_tap_count;
fir_additions_per_sample = fir_tap_count-1;
iir_multiplications_per_sample = 5;
iir_additions_per_sample = 4;

%% Parameter sweep 1 - change only FIR tap count
fir_sweep_response_db = zeros(numel(fir_tap_count_sweep), frequency_grid_count);
fir_sweep_delay_samples = zeros(size(fir_tap_count_sweep));
fir_sweep_interferer_magnitude_db = zeros(size(fir_tap_count_sweep));
fir_sweep_step_v = zeros(numel(fir_tap_count_sweep), response_sample_count);
for sweep_index = 1:numel(fir_tap_count_sweep)
    sweep_tap_count = fir_tap_count_sweep(sweep_index);
    sweep_half_order = (sweep_tap_count-1)/2;
    sweep_b = zeros(1, sweep_tap_count);
    for tap_index = 0:sweep_tap_count-1
        centered_index = tap_index-sweep_half_order;
        sinc_argument = 2*fir_design_cutoff_hz/fs_hz*centered_index;
        if centered_index == 0
            sinc_value = 1;
        else
            sinc_value = sin(pi*sinc_argument)/(pi*sinc_argument);
        end
        ideal_value = 2*fir_design_cutoff_hz/fs_hz*sinc_value;
        window_value = 0.54-0.46*cos(2*pi*tap_index/(sweep_tap_count-1));
        sweep_b(tap_index+1) = ideal_value*window_value;
    end
    sweep_b = sweep_b/sum(sweep_b);
    fir_sweep_delay_samples(sweep_index) = sweep_half_order;

    for frequency_index = 1:frequency_grid_count
        sweep_sum = 0;
        for tap_index = 0:sweep_tap_count-1
            sweep_sum = sweep_sum+sweep_b(tap_index+1)* ...
                exp(-1j*omega_rad_per_sample(frequency_index)*tap_index);
        end
        fir_sweep_response_db(sweep_index, frequency_index) = ...
            20*log10(max(abs(sweep_sum), 1e-8));
    end
    fir_sweep_interferer_magnitude_db(sweep_index) = ...
        fir_sweep_response_db(sweep_index, interferer_frequency_index);

    for output_index = 0:response_sample_count-1
        sweep_accumulator = 0;
        for tap_index = 0:sweep_tap_count-1
            input_index = output_index-tap_index;
            if input_index >= 0
                sweep_accumulator = sweep_accumulator+ ...
                    sweep_b(tap_index+1)*step_input_v(input_index+1);
            end
        end
        fir_sweep_step_v(sweep_index, output_index+1) = sweep_accumulator;
    end
end
assert(all(diff(fir_sweep_delay_samples) > 0), ...
    'Longer symmetric FIR filters must add more causal delay.');

%% Parameter sweep 2 - change only IIR Q (damping)
iir_q_sweep_response_db = zeros(numel(iir_q_sweep), frequency_grid_count);
iir_q_sweep_step_v = zeros(numel(iir_q_sweep), response_sample_count);
iir_q_sweep_overshoot_percent = zeros(size(iir_q_sweep));
iir_q_sweep_max_pole_radius = zeros(size(iir_q_sweep));
for sweep_index = 1:numel(iir_q_sweep)
    sweep_q = iir_q_sweep(sweep_index);
    sweep_norm = 1/(1+iir_k/sweep_q+iir_k^2);
    sweep_iir_b = [iir_k^2 2*iir_k^2 iir_k^2]*sweep_norm;
    sweep_iir_a = [1 2*(iir_k^2-1)*sweep_norm ...
        (1-iir_k/sweep_q+iir_k^2)*sweep_norm];
    sweep_discriminant = sweep_iir_a(2)^2-4*sweep_iir_a(3);
    sweep_poles = [(-sweep_iir_a(2)+sqrt(complex(sweep_discriminant)))/2 ...
        (-sweep_iir_a(2)-sqrt(complex(sweep_discriminant)))/2];
    iir_q_sweep_max_pole_radius(sweep_index) = max(abs(sweep_poles));
    assert(iir_q_sweep_max_pole_radius(sweep_index) < 1, ...
        'Every Q sweep case must remain stable.');

    for frequency_index = 1:frequency_grid_count
        omega_now = omega_rad_per_sample(frequency_index);
        sweep_numerator = sweep_iir_b(1)+sweep_iir_b(2)*exp(-1j*omega_now)+ ...
            sweep_iir_b(3)*exp(-2j*omega_now);
        sweep_denominator = sweep_iir_a(1)+sweep_iir_a(2)*exp(-1j*omega_now)+ ...
            sweep_iir_a(3)*exp(-2j*omega_now);
        iir_q_sweep_response_db(sweep_index, frequency_index) = ...
            20*log10(max(abs(sweep_numerator/sweep_denominator), 1e-8));
    end

    for output_index = 0:response_sample_count-1
        sweep_accumulator = sweep_iir_b(1)*step_input_v(output_index+1);
        if output_index >= 1
            sweep_accumulator = sweep_accumulator+ ...
                sweep_iir_b(2)*step_input_v(output_index)- ...
                sweep_iir_a(2)*iir_q_sweep_step_v(sweep_index, output_index);
        end
        if output_index >= 2
            sweep_accumulator = sweep_accumulator+ ...
                sweep_iir_b(3)*step_input_v(output_index-1)- ...
                sweep_iir_a(3)*iir_q_sweep_step_v(sweep_index, output_index-1);
        end
        iir_q_sweep_step_v(sweep_index, output_index+1) = sweep_accumulator;
    end
    iir_q_sweep_overshoot_percent(sweep_index) = ...
        100*(max(iir_q_sweep_step_v(sweep_index, :))-1);
end
assert(all(diff(iir_q_sweep_max_pole_radius) > 0) && ...
    all(diff(iir_q_sweep_overshoot_percent) > 0), ...
    'Increasing Q should move poles outward and increase step overshoot.');

%% Deliberately broken case - put a conjugate pole pair outside the unit circle
aggressive_pole_angle_rad = 2*pi*aggressive_pole_angle_hz/fs_hz;
broken_iir_a = [1 -2*broken_pole_radius*cos(aggressive_pole_angle_rad) ...
    broken_pole_radius^2];
broken_iir_b = [sum(broken_iir_a) 0 0];
recovered_iir_a = [1 -2*recovered_pole_radius*cos(aggressive_pole_angle_rad) ...
    recovered_pole_radius^2];
recovered_iir_b = [sum(recovered_iir_a) 0 0];

broken_impulse_v = zeros(1, response_sample_count);
recovered_impulse_v = zeros(1, response_sample_count);
for output_index = 0:response_sample_count-1
    input_now = double(output_index == 0);
    broken_accumulator = broken_iir_b(1)*input_now;
    recovered_accumulator = recovered_iir_b(1)*input_now;
    if output_index >= 1
        broken_accumulator = broken_accumulator- ...
            broken_iir_a(2)*broken_impulse_v(output_index);
        recovered_accumulator = recovered_accumulator- ...
            recovered_iir_a(2)*recovered_impulse_v(output_index);
    end
    if output_index >= 2
        broken_accumulator = broken_accumulator- ...
            broken_iir_a(3)*broken_impulse_v(output_index-1);
        recovered_accumulator = recovered_accumulator- ...
            recovered_iir_a(3)*recovered_impulse_v(output_index-1);
    end
    broken_impulse_v(output_index+1) = broken_accumulator;
    recovered_impulse_v(output_index+1) = recovered_accumulator;
end

tail_window_count = 32;
broken_early_rms_v = sqrt(mean(broken_impulse_v(1:tail_window_count).^2));
broken_late_rms_v = sqrt(mean(broken_impulse_v(end-tail_window_count+1:end).^2));
recovered_early_rms_v = sqrt(mean(recovered_impulse_v(1:tail_window_count).^2));
recovered_late_rms_v = sqrt(mean(recovered_impulse_v(end-tail_window_count+1:end).^2));
broken_tail_growth_ratio = broken_late_rms_v/broken_early_rms_v;
recovered_tail_decay_ratio = recovered_late_rms_v/recovered_early_rms_v;
assert(all(isfinite(broken_impulse_v)) && all(isfinite(recovered_impulse_v)), ...
    'The bounded broken/recovery demonstration must remain finite.');
assert(broken_tail_growth_ratio > 2 && recovered_tail_decay_ratio < 0.2, ...
    'Broken poles must grow while recovered poles decay over the fixed horizon.');

%% Plot only after all validation and numerical checks have passed
prior_p09_figures = findall(groot, 'Type', 'figure', 'Tag', 'P09');
close(prior_p09_figures);

figure('Name', 'P09 comparable cutoff, different phase', 'Tag', 'P09');
subplot(3, 1, 1);
plot(frequency_hz, fir_magnitude_db, 'LineWidth', 1.5); hold on;
plot(frequency_hz, iir_magnitude_db, '--', 'LineWidth', 1.5);
plot([fir_measured_cutoff_hz fir_measured_cutoff_hz], [-80 3], ':');
plot([iir_measured_cutoff_hz iir_measured_cutoff_hz], [-80 3], ':');
grid on; xlim([0 fs_hz/2]); ylim([-80 3]);
xlabel('Frequency (Hz)'); ylabel('Magnitude (dB)');
title('Comparable -3 dB cutoff does not make the filters equivalent');
legend('21-tap FIR', '2nd-order IIR', 'FIR -3 dB', 'IIR -3 dB', ...
    'Location', 'southwest');
subplot(3, 1, 2);
plot(frequency_hz, fir_phase_rad, 'LineWidth', 1.5); hold on;
plot(frequency_hz, iir_phase_rad, '--', 'LineWidth', 1.5);
grid on; xlim([0 200]);
xlabel('Frequency (Hz)'); ylabel('Unwrapped phase (rad)');
title('FIR phase is a line; IIR phase bends');
legend('FIR', 'IIR', 'Location', 'southwest');
subplot(3, 1, 3);
plot(group_delay_frequency_hz, fir_group_delay_samples, 'LineWidth', 1.5); hold on;
plot(group_delay_frequency_hz, iir_group_delay_samples, '--', 'LineWidth', 1.5);
grid on; xlim([0 200]); ylim([0 fir_half_order+3]);
xlabel('Frequency (Hz)'); ylabel('Group delay (samples)');
title('Delay is constant for this FIR and frequency-dependent for the IIR');
legend('FIR', 'IIR', 'Location', 'best');

figure('Name', 'P09 impulse step and pulse transients', 'Tag', 'P09');
subplot(3, 1, 1);
stem(response_sample_index, fir_impulse_v, '.', 'LineWidth', 1.0); hold on;
plot(response_sample_index, iir_impulse_v, '--', 'LineWidth', 1.5);
grid on; xlim([0 70]); xlabel('Sample index'); ylabel('Response (V/V)');
title('Finite FIR support versus decaying IIR memory');
legend('FIR', 'IIR', 'Location', 'best');
subplot(3, 1, 2);
plot(response_time_ms, step_input_v, ':', 'LineWidth', 1.0); hold on;
plot(response_time_ms, fir_step_v, 'LineWidth', 1.5);
plot(response_time_ms, iir_step_v, '--', 'LineWidth', 1.5);
grid on; xlim([0 80]); xlabel('Time (ms)'); ylabel('Amplitude (V)');
title('Same step, different delay and ringing');
legend('Input', 'FIR', 'IIR', 'Location', 'southeast');
subplot(3, 1, 3);
plot(response_time_ms, pulse_input_v, ':', 'LineWidth', 1.0); hold on;
plot(response_time_ms, fir_pulse_v, 'LineWidth', 1.5);
plot(response_time_ms, iir_pulse_v, '--', 'LineWidth', 1.5);
grid on; xlim([15 90]); xlabel('Time (ms)'); ylabel('Amplitude (V)');
title('Pulse edges expose timing and shape distortion');
legend('Input', 'FIR', 'IIR', 'Location', 'best');

figure('Name', 'P09 deterministic noisy multitone', 'Tag', 'P09');
subplot(2, 1, 1);
plot(record_time_ms, noisy_multitone_v, 'Color', [0.65 0.65 0.65]); hold on;
plot(record_time_ms, fir_multitone_v, 'LineWidth', 1.2);
plot(record_time_ms, iir_multitone_v, '--', 'LineWidth', 1.2);
grid on; xlim([100 180]); xlabel('Time (ms)'); ylabel('Voltage (V)');
title('Filtered waveforms retain different timing and shape');
legend('Noisy input', 'FIR output', 'IIR output', 'Location', 'best');
subplot(2, 1, 2);
bar([desired_tone_hz interferer_tone_hz], ...
    [fir_magnitude_db([desired_frequency_index interferer_frequency_index]); ...
    iir_magnitude_db([desired_frequency_index interferer_frequency_index])]');
grid on; xlabel('Tone frequency (Hz)'); ylabel('Filter magnitude (dB)');
title('Both pass 60 Hz; their far-stopband rejection is not identical');
legend('FIR', 'IIR', 'Location', 'best');

figure('Name', 'P09 sweep 1 FIR tap count', 'Tag', 'P09');
subplot(2, 1, 1);
hold on;
fir_sweep_legend = cell(1, numel(fir_tap_count_sweep));
for sweep_index = 1:numel(fir_tap_count_sweep)
    plot(frequency_hz, fir_sweep_response_db(sweep_index, :), 'LineWidth', 1.3);
    fir_sweep_legend{sweep_index} = sprintf('%d taps; delay %d samples', ...
        fir_tap_count_sweep(sweep_index), fir_sweep_delay_samples(sweep_index));
end
grid on; xlim([0 300]); ylim([-80 3]);
xlabel('Frequency (Hz)'); ylabel('Magnitude (dB)');
title('Sweep 1: change only FIR tap count');
legend(fir_sweep_legend, 'Location', 'southwest');
subplot(2, 1, 2);
hold on;
for sweep_index = 1:numel(fir_tap_count_sweep)
    plot(response_time_ms, fir_sweep_step_v(sweep_index, :), 'LineWidth', 1.3);
end
grid on; xlim([0 80]); xlabel('Time (ms)'); ylabel('Step output (V)');
title('Longer linear-phase FIR means more causal delay');
legend(fir_sweep_legend, 'Location', 'southeast');

figure('Name', 'P09 sweep 2 IIR damping', 'Tag', 'P09');
subplot(2, 1, 1);
hold on;
iir_sweep_legend = cell(1, numel(iir_q_sweep));
for sweep_index = 1:numel(iir_q_sweep)
    plot(frequency_hz, iir_q_sweep_response_db(sweep_index, :), 'LineWidth', 1.3);
    iir_sweep_legend{sweep_index} = sprintf('Q=%.3f; pole radius %.3f', ...
        iir_q_sweep(sweep_index), iir_q_sweep_max_pole_radius(sweep_index));
end
grid on; xlim([0 250]); ylim([-35 12]);
xlabel('Frequency (Hz)'); ylabel('Magnitude (dB)');
title('Sweep 2: change only IIR Q');
legend(iir_sweep_legend, 'Location', 'southwest');
subplot(2, 1, 2);
hold on;
for sweep_index = 1:numel(iir_q_sweep)
    plot(response_time_ms, iir_q_sweep_step_v(sweep_index, :), 'LineWidth', 1.3);
end
grid on; xlim([0 80]); xlabel('Time (ms)'); ylabel('Step output (V)');
title('Less damping produces more overshoot and ringing');
legend(iir_sweep_legend, 'Location', 'best');

figure('Name', 'P09 broken IIR stability and recovery', 'Tag', 'P09');
subplot(2, 1, 1);
semilogy(response_sample_index, max(abs(broken_impulse_v), 1e-8), ...
    'LineWidth', 1.5); hold on;
semilogy(response_sample_index, max(abs(recovered_impulse_v), 1e-8), ...
    '--', 'LineWidth', 1.5);
grid on; xlabel('Sample index'); ylabel('|Impulse response| (V/V)');
title('Broken radius 1.02 grows; recovered radius 0.98 decays');
legend('Broken IIR', 'Recovered IIR', 'Location', 'best');
subplot(2, 1, 2);
bar([1 2], [broken_tail_growth_ratio recovered_tail_decay_ratio]);
set(gca, 'XTick', [1 2], 'XTickLabel', {'Broken growth', 'Recovered decay'});
grid on; ylabel('Late-window RMS / early-window RMS');
title('The unit circle is the stability boundary');

%% Printed metrics and retained workspace summary - no file or learner-state write
fprintf('P09 baseline filter metrics\n');
fprintf('  FIR measured -3 dB cutoff       = %.3f Hz\n', fir_measured_cutoff_hz);
fprintf('  IIR measured -3 dB cutoff       = %.3f Hz\n', iir_measured_cutoff_hz);
fprintf('  cutoff mismatch                 = %.3f Hz\n', cutoff_mismatch_hz);
fprintf('  FIR group delay at %.1f Hz       = %.3f samples\n', ...
    desired_tone_hz, fir_desired_group_delay_samples);
fprintf('  IIR group delay at %.1f Hz       = %.3f samples\n', ...
    desired_tone_hz, iir_desired_group_delay_samples);
fprintf('  FIR impulse last > threshold    = sample %g (found=%d)\n', ...
    fir_last_tail_sample, fir_tail_metric_found);
fprintf('  IIR impulse last > threshold    = sample %g (found=%d; finite observation)\n', ...
    iir_last_tail_sample, iir_tail_metric_found);
fprintf('  FIR/IIR step overshoot          = %.3f / %.3f percent\n', ...
    fir_step_overshoot_percent, iir_step_overshoot_percent);
fprintf('  FIR settling after onset        = %g samples (found=%d)\n', ...
    fir_settling_after_onset_samples, fir_settling_metric_found);
fprintf('  IIR settling after onset        = %g samples (found=%d)\n', ...
    iir_settling_after_onset_samples, iir_settling_metric_found);
fprintf('  FIR arithmetic                  = %d multiplies, %d adds/sample\n', ...
    fir_multiplications_per_sample, fir_additions_per_sample);
fprintf('  IIR arithmetic                  = %d multiplies, %d adds/sample\n', ...
    iir_multiplications_per_sample, iir_additions_per_sample);
fprintf('P09 broken/recovery metrics\n');
fprintf('  broken pole radius              = %.3f\n', broken_pole_radius);
fprintf('  broken late/early RMS ratio     = %.3f\n', broken_tail_growth_ratio);
fprintf('  recovered pole radius           = %.3f\n', recovered_pole_radius);
fprintf('  recovered late/early RMS ratio  = %.3f\n', recovered_tail_decay_ratio);

results = struct();
results.random_seed = random_seed;
results.seed_signature = seed_signature;
results.fs_hz = fs_hz;
results.cutoff_hz = cutoff_hz;
results.fir_b = fir_b;
results.iir_b = iir_b;
results.iir_a = iir_a;
results.iir_poles = iir_poles;
results.frequency_hz = frequency_hz;
results.fir_response = fir_response;
results.iir_response = iir_response;
results.fir_measured_cutoff_hz = fir_measured_cutoff_hz;
results.iir_measured_cutoff_hz = iir_measured_cutoff_hz;
results.cutoff_mismatch_hz = cutoff_mismatch_hz;
results.fir_group_delay_samples = fir_group_delay_samples;
results.iir_group_delay_samples = iir_group_delay_samples;
results.fir_impulse_v = fir_impulse_v;
results.iir_impulse_v = iir_impulse_v;
results.fir_step_v = fir_step_v;
results.iir_step_v = iir_step_v;
results.fir_pulse_v = fir_pulse_v;
results.iir_pulse_v = iir_pulse_v;
results.tail_threshold = tail_threshold;
results.fir_last_tail_sample = fir_last_tail_sample;
results.iir_last_tail_sample = iir_last_tail_sample;
results.fir_tail_metric_found = fir_tail_metric_found;
results.iir_tail_metric_found = iir_tail_metric_found;
results.settling_tolerance_fraction = settling_tolerance_fraction;
results.fir_settling_after_onset_samples = fir_settling_after_onset_samples;
results.iir_settling_after_onset_samples = iir_settling_after_onset_samples;
results.fir_settling_metric_found = fir_settling_metric_found;
results.iir_settling_metric_found = iir_settling_metric_found;
results.noisy_multitone_v = noisy_multitone_v;
results.fir_multitone_v = fir_multitone_v;
results.iir_multitone_v = iir_multitone_v;
results.fir_tap_count_sweep = fir_tap_count_sweep;
results.fir_sweep_delay_samples = fir_sweep_delay_samples;
results.iir_q_sweep = iir_q_sweep;
results.iir_q_sweep_overshoot_percent = iir_q_sweep_overshoot_percent;
results.broken_pole_radius = broken_pole_radius;
results.broken_tail_growth_ratio = broken_tail_growth_ratio;
results.recovered_pole_radius = recovered_pole_radius;
results.recovered_tail_decay_ratio = recovered_tail_decay_ratio;
