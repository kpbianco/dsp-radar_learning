%% P06 - Use an Impulse to Reveal a System
% Guiding question:
% Why does an impulse response describe an LTI system?
%
% Dependency contract: P05 and base MATLAB only. No toolbox, helper
% function, external data, device, or service is required. This finite script
% preserves unrelated figures and the global random stream. A rerun replaces
% only prior P06 figures, but still creates or replaces its named workspace
% variables, including results.
p06_figure_tag = 'P06ImpulseResponseLab';
prior_p06_figures = findall(groot, 'Type', 'figure', 'Tag', p06_figure_tag);
if ~isempty(prior_p06_figures)
    close(prior_p06_figures);
end
random_seed = 606;
random_stream = RandStream('mt19937ar', 'Seed', random_seed);

%% Baseline controls - change one at a time
fs = 1000;                       % sample rate (samples/s)
duration_s = 0.256;              % observed input/output duration (s)
delay_samples = 18;              % pure-delay amount (samples)
moving_average_length = 9;       % equal-weight averaging taps (samples)
echo_delay_samples = 32;         % secondary echo delay (samples)
echo_gain = 0.55;                % secondary echo amplitude (unitless)
resonator_radius = 0.86;         % complex-pole radius / memory (unitless)
resonator_frequency_hz = 90;     % ringing frequency (Hz)
resonator_input_gain = 0.15;     % resonator drive scale (V/V)
probe_noise_rms_v = 0.02;        % seeded broadband probe RMS (V RMS)
comparison_tolerance_v = 2e-12;  % direct/convolution agreement (V)
max_samples = 4096;              % fixed resource ceiling (samples)
max_sweep_cases = 8;             % fixed sweep ceiling (cases)
system_count = 4;                % delay, moving average, echo, resonator

% Fail before signal or response allocation if an edited control is malformed.
assert(isscalar(fs) && isnumeric(fs) && ~islogical(fs) && isreal(fs) && ...
    isfinite(fs) && fs > 0, ...
    'fs must be one finite positive real sample rate.');
assert(isscalar(duration_s) && isnumeric(duration_s) && ...
    ~islogical(duration_s) && isreal(duration_s) && ...
    isfinite(duration_s) && duration_s > 0, ...
    'duration_s must be one finite positive real duration.');
assert(isscalar(delay_samples) && isnumeric(delay_samples) && ...
    ~islogical(delay_samples) && isreal(delay_samples) && ...
    isfinite(delay_samples) && delay_samples == floor(delay_samples) && ...
    delay_samples >= 0, ...
    'delay_samples must be one finite nonnegative integer.');
assert(isscalar(moving_average_length) && isnumeric(moving_average_length) && ...
    ~islogical(moving_average_length) && isreal(moving_average_length) && ...
    isfinite(moving_average_length) && ...
    moving_average_length == floor(moving_average_length) && ...
    moving_average_length >= 1, ...
    'moving_average_length must be one finite positive integer.');
assert(isscalar(echo_delay_samples) && isnumeric(echo_delay_samples) && ...
    ~islogical(echo_delay_samples) && isreal(echo_delay_samples) && ...
    isfinite(echo_delay_samples) && ...
    echo_delay_samples == floor(echo_delay_samples) && ...
    echo_delay_samples >= 1, ...
    'echo_delay_samples must be one finite positive integer.');
assert(isscalar(echo_gain) && isnumeric(echo_gain) && ...
    ~islogical(echo_gain) && isreal(echo_gain) && isfinite(echo_gain) && ...
    abs(echo_gain) > 0 && abs(echo_gain) < 1, ...
    'echo_gain magnitude must be finite and between zero and one.');
assert(isscalar(resonator_radius) && isnumeric(resonator_radius) && ...
    ~islogical(resonator_radius) && isreal(resonator_radius) && ...
    isfinite(resonator_radius) && resonator_radius >= 0 && ...
    resonator_radius < 1, ...
    'resonator_radius must be a finite real coefficient in [0,1).');
assert(isscalar(resonator_frequency_hz) && ...
    isnumeric(resonator_frequency_hz) && ...
    ~islogical(resonator_frequency_hz) && isreal(resonator_frequency_hz) && ...
    isfinite(resonator_frequency_hz) && resonator_frequency_hz > 0 && ...
    resonator_frequency_hz < fs/2, ...
    'resonator_frequency_hz must be finite, positive, and below Nyquist.');
assert(isscalar(resonator_input_gain) && ...
    isnumeric(resonator_input_gain) && ~islogical(resonator_input_gain) && ...
    isreal(resonator_input_gain) && isfinite(resonator_input_gain) && ...
    resonator_input_gain > 0 && resonator_input_gain <= 1, ...
    'resonator_input_gain must be finite and in (0,1].');
assert(isscalar(probe_noise_rms_v) && isnumeric(probe_noise_rms_v) && ...
    ~islogical(probe_noise_rms_v) && isreal(probe_noise_rms_v) && ...
    isfinite(probe_noise_rms_v) && probe_noise_rms_v >= 0 && ...
    probe_noise_rms_v <= 0.1, ...
    'probe_noise_rms_v must be finite and between 0 and 0.1 V RMS.');
assert(isscalar(comparison_tolerance_v) && ...
    isnumeric(comparison_tolerance_v) && ~islogical(comparison_tolerance_v) && ...
    isreal(comparison_tolerance_v) && isfinite(comparison_tolerance_v) && ...
    comparison_tolerance_v > 0 && comparison_tolerance_v <= 1e-9, ...
    'comparison_tolerance_v must be finite, positive, and at most 1e-9 V.');
assert(isscalar(max_samples) && isnumeric(max_samples) && ...
    ~islogical(max_samples) && isreal(max_samples) && isfinite(max_samples) && ...
    max_samples == floor(max_samples) && max_samples == 4096, ...
    'max_samples is a fixed safety ceiling of 4096 samples.');
assert(isscalar(max_sweep_cases) && isnumeric(max_sweep_cases) && ...
    ~islogical(max_sweep_cases) && isreal(max_sweep_cases) && ...
    isfinite(max_sweep_cases) && ...
    max_sweep_cases == floor(max_sweep_cases) && max_sweep_cases == 8, ...
    'max_sweep_cases is a fixed safety ceiling of eight cases.');
assert(isscalar(system_count) && isnumeric(system_count) && ...
    ~islogical(system_count) && isreal(system_count) && ...
    isfinite(system_count) && system_count == 4, ...
    'system_count is fixed at the four canonical systems.');

resonator_angle_rad = 2*pi*resonator_frequency_hz/fs;
assert(abs(sin(resonator_angle_rad)) > 1e-6, ...
    'Resonator frequency must stay away from the degenerate DC/Nyquist limits.');
sample_count = round(duration_s*fs);
assert(sample_count >= 128 && ...
    abs(sample_count-duration_s*fs) < 10*eps(max(1, duration_s*fs)), ...
    'duration_s*fs must be an integer record of at least 128 samples.');
assert(sample_count <= max_samples, ...
    'The observation is limited to 4096 samples; reduce fs or duration_s.');
assert(delay_samples < sample_count, ...
    'delay_samples must be smaller than the observation.');
assert(moving_average_length <= min(64, sample_count), ...
    'moving_average_length must not exceed 64 samples or the observation.');
assert(echo_delay_samples < sample_count/2, ...
    'echo_delay_samples must be less than half the observation.');

n = 0:sample_count-1;
t_s = n/fs;
impulse = zeros(1, sample_count);
impulse(1) = 1;
probe_noise = randn(random_stream, 1, sample_count);
probe_noise = probe_noise-mean(probe_noise);
probe_noise = probe_noise_rms_v*probe_noise/sqrt(mean(probe_noise.^2));
general_input_v = 0.55*cos(2*pi*31.25*t_s + pi/7) + ...
    0.25*sin(2*pi*78.125*t_s) + probe_noise;
general_input_v(70:82) = general_input_v(70:82) + 0.45;
system_names = {'Pure delay', 'Moving average', 'Echo path', ...
    'Damped resonator'};

figure('Name', 'P06 baseline 1: two probes', 'Tag', p06_figure_tag);
subplot(2,1,1);
stem(n(1:64), impulse(1:64), 'filled');
grid on;
xlabel('Sample index n');
ylabel('Impulse amplitude (unitless)');
title('Unit impulse: one nonzero input sample');
subplot(2,1,2);
plot(t_s, general_input_v, 'LineWidth', 1.0);
grid on;
xlabel('Time (s)');
ylabel('Input voltage x[n] (V)');
title(sprintf('General deterministic input; private seed %d', random_seed));

%% Excite every system with the impulse - this measurement is h[n]
% Each system operation is visible. No filtering helper hides the response.
h_delay = zeros(1, sample_count);
for output_index = 1:sample_count
    source_index = output_index-delay_samples;
    if source_index >= 1
        h_delay(output_index) = impulse(source_index);
    end
end

h_moving_average = zeros(1, sample_count);
for output_index = 1:sample_count
    first_input_index = max(1, output_index-moving_average_length+1);
    h_moving_average(output_index) = ...
        sum(impulse(first_input_index:output_index))/moving_average_length;
end

h_echo_path = zeros(1, sample_count);
for output_index = 1:sample_count
    h_echo_path(output_index) = impulse(output_index);
    echo_source_index = output_index-echo_delay_samples;
    if echo_source_index >= 1
        h_echo_path(output_index) = h_echo_path(output_index) + ...
            echo_gain*impulse(echo_source_index);
    end
end

h_resonator = zeros(1, sample_count);
resonator_feedback_1 = 2*resonator_radius*cos(resonator_angle_rad);
resonator_feedback_2 = -resonator_radius^2;
for output_index = 1:sample_count
    previous_output_1 = 0;
    previous_output_2 = 0;
    if output_index >= 2
        previous_output_1 = h_resonator(output_index-1);
    end
    if output_index >= 3
        previous_output_2 = h_resonator(output_index-2);
    end
    h_resonator(output_index) = ...
        resonator_feedback_1*previous_output_1 + ...
        resonator_feedback_2*previous_output_2 + ...
        resonator_input_gain*impulse(output_index);
end

impulse_responses = [h_delay; h_moving_average; h_echo_path; h_resonator];
assert(abs(h_delay(delay_samples+1)-1) < 10*eps, ...
    'The delay impulse response must contain a unit sample at the set delay.');
assert(abs(sum(h_moving_average)-1) < 100*eps, ...
    'The moving-average impulse-response weights must sum to one.');
assert(abs(h_echo_path(1)-1) < 10*eps && ...
    abs(h_echo_path(echo_delay_samples+1)-echo_gain) < 10*eps, ...
    'The echo response must expose the direct and delayed paths.');
resonator_expected = resonator_input_gain*resonator_radius.^n .* ...
    sin((n+1)*resonator_angle_rad)/sin(resonator_angle_rad);
assert(all(abs(h_resonator-resonator_expected) < 500*eps), ...
    'The measured resonator response must follow its damped sinusoid.');

figure('Name', 'P06 baseline 2: impulse responses reveal the systems', ...
    'Tag', p06_figure_tag);
for system_index = 1:system_count
    subplot(2,2,system_index);
    stem(n(1:80), impulse_responses(system_index,1:80), 'filled');
    grid on;
    xlabel('Lag k (samples)');
    ylabel('h[k] (V/V)');
    title(system_names{system_index});
end

%% Process the general signal directly using the same four system rules
y_direct = zeros(system_count, sample_count);
for output_index = 1:sample_count
    source_index = output_index-delay_samples;
    if source_index >= 1
        y_direct(1,output_index) = general_input_v(source_index);
    end

    first_input_index = max(1, output_index-moving_average_length+1);
    y_direct(2,output_index) = ...
        sum(general_input_v(first_input_index:output_index))/moving_average_length;

    y_direct(3,output_index) = general_input_v(output_index);
    echo_source_index = output_index-echo_delay_samples;
    if echo_source_index >= 1
        y_direct(3,output_index) = y_direct(3,output_index) + ...
            echo_gain*general_input_v(echo_source_index);
    end

    previous_output_1 = 0;
    previous_output_2 = 0;
    if output_index >= 2
        previous_output_1 = y_direct(4,output_index-1);
    end
    if output_index >= 3
        previous_output_2 = y_direct(4,output_index-2);
    end
    y_direct(4,output_index) = ...
        resonator_feedback_1*previous_output_1 + ...
        resonator_feedback_2*previous_output_2 + ...
        resonator_input_gain*general_input_v(output_index);
end

%% Rebuild every output from weighted, delayed input copies
% Linear convolution states the LTI model explicitly:
% y[n] = sum_k h[k]*x[n-k]. MATLAB conv evaluates this finite sum. Because
% the resonator response is infinite, the N measured h samples reproduce the
% first N causal output samples exactly; its later tail is outside this view.
y_from_impulse = zeros(system_count, sample_count);
max_abs_error_v = zeros(1, system_count);
rms_error_v = zeros(1, system_count);
for system_index = 1:system_count
    full_linear_convolution = conv(general_input_v, ...
        impulse_responses(system_index,:));
    y_from_impulse(system_index,:) = ...
        full_linear_convolution(1:sample_count);
    residual_v = y_direct(system_index,:) - ...
        y_from_impulse(system_index,:);
    max_abs_error_v(system_index) = max(abs(residual_v));
    rms_error_v(system_index) = sqrt(mean(residual_v.^2));
end
assert(all(max_abs_error_v < comparison_tolerance_v), ...
    'Every direct system and impulse-response convolution must agree.');

figure('Name', 'P06 baseline 3: direct rule equals convolution', ...
    'Tag', p06_figure_tag);
for system_index = 1:system_count
    subplot(2,2,system_index);
    plot(t_s, y_direct(system_index,:), 'LineWidth', 1.2, ...
        'DisplayName', 'Direct system');
    hold on;
    plot(t_s, y_from_impulse(system_index,:), '--', 'LineWidth', 1.0, ...
        'DisplayName', 'conv(x,h)');
    grid on;
    xlabel('Time (s)');
    ylabel('Output voltage y[n] (V)');
    title(sprintf('%s; max error %.3e V', system_names{system_index}, ...
        max_abs_error_v(system_index)));
    legend('Location', 'best');
end

figure('Name', 'P06 baseline 4: numerical agreement metric', ...
    'Tag', p06_figure_tag);
semilogy(1:system_count, max(max_abs_error_v, eps), 'o-', ...
    'LineWidth', 1.2, 'MarkerSize', 7);
hold on;
semilogy([1 system_count], comparison_tolerance_v*[1 1], 'r--', ...
    'LineWidth', 1.0);
grid on;
xticks(1:system_count);
xticklabels(system_names);
xlabel('System');
ylabel('Maximum absolute error (V)');
title('Direct processing and convolution agree to numerical precision');
legend('Measured error', 'Required tolerance', 'Location', 'best');

fprintf('P06 impulse-response baseline metrics\n');
fprintf('  random seed / sample rate       = %d / %.1f samples/s\n', ...
    random_seed, fs);
fprintf('  observed input/output duration  = %.3f s (%d samples)\n', ...
    duration_s, sample_count);
for system_index = 1:system_count
    fprintf('  %-20s max error = %.6e V, RMS error = %.6e V\n', ...
        system_names{system_index}, max_abs_error_v(system_index), ...
        rms_error_v(system_index));
end

%% Parameter sweep 1 - change only echo delay
echo_delay_sweep_samples = [8 32 64];
assert(isvector(echo_delay_sweep_samples) && ...
    isnumeric(echo_delay_sweep_samples) && ...
    ~islogical(echo_delay_sweep_samples) && ...
    isreal(echo_delay_sweep_samples) && ...
    all(isfinite(echo_delay_sweep_samples)) && ...
    all(echo_delay_sweep_samples == floor(echo_delay_sweep_samples)) && ...
    all(echo_delay_sweep_samples >= 1) && ...
    all(echo_delay_sweep_samples < sample_count/2), ...
    'Echo-delay sweep values must be finite positive in-range integers.');
assert(numel(echo_delay_sweep_samples) >= 2 && ...
    numel(echo_delay_sweep_samples) <= max_sweep_cases, ...
    'The echo-delay sweep requires from two through eight cases.');
assert(isequal(echo_delay_sweep_samples, [8 32 64]), ...
    'Keep the canonical echo-delay sweep at 8, 32, and 64 samples.');

echo_sweep_outputs_v = zeros(numel(echo_delay_sweep_samples), sample_count);
echo_sweep_responses = zeros(numel(echo_delay_sweep_samples), sample_count);
echo_delay_sweep_ms = 1000*echo_delay_sweep_samples/fs;
for sweep_index = 1:numel(echo_delay_sweep_samples)
    delay_case = echo_delay_sweep_samples(sweep_index);
    echo_sweep_responses(sweep_index,1) = 1;
    echo_sweep_responses(sweep_index,delay_case+1) = echo_gain;
    echo_case_full = conv(general_input_v, ...
        echo_sweep_responses(sweep_index,:));
    echo_sweep_outputs_v(sweep_index,:) = echo_case_full(1:sample_count);
    fprintf('P06 echo sweep: delay = %d samples = %.3f ms, gain = %.2f\n', ...
        delay_case, echo_delay_sweep_ms(sweep_index), echo_gain);
end
assert(all(diff(echo_delay_sweep_ms) > 0), ...
    'Increasing delay samples must increase physical echo delay.');

figure('Name', 'P06 sweep 1: echo delay moves one response tap', ...
    'Tag', p06_figure_tag);
subplot(2,1,1);
for sweep_index = 1:numel(echo_delay_sweep_samples)
    stem(n(1:80), echo_sweep_responses(sweep_index,1:80), ...
        'DisplayName', sprintf('%.1f ms', echo_delay_sweep_ms(sweep_index)));
    hold on;
end
grid on;
xlabel('Lag k (samples)');
ylabel('h[k] (V/V)');
title(sprintf('Only delay changes; echo gain stays %.2f', echo_gain));
legend('Location', 'best');
subplot(2,1,2);
for sweep_index = 1:numel(echo_delay_sweep_samples)
    plot(t_s, echo_sweep_outputs_v(sweep_index,:), 'LineWidth', 1.0, ...
        'DisplayName', sprintf('%.1f ms', echo_delay_sweep_ms(sweep_index)));
    hold on;
end
grid on;
xlabel('Time (s)');
ylabel('Echo-path output (V)');
title('Moving one tap moves the delayed input copy');
legend('Location', 'best');

%% Parameter sweep 2 - change only resonator memory
resonator_radius_sweep = [0.25 0.70 0.92];
assert(isvector(resonator_radius_sweep) && ...
    isnumeric(resonator_radius_sweep) && ...
    ~islogical(resonator_radius_sweep) && ...
    isreal(resonator_radius_sweep) && ...
    all(isfinite(resonator_radius_sweep)) && ...
    all(resonator_radius_sweep >= 0) && all(resonator_radius_sweep < 1), ...
    'Resonator sweep values must be finite real coefficients in [0,1).');
assert(numel(resonator_radius_sweep) >= 2 && ...
    numel(resonator_radius_sweep) <= max_sweep_cases, ...
    'The resonator sweep requires from two through eight cases.');
assert(isequal(resonator_radius_sweep, [0.25 0.70 0.92]), ...
    'Keep the canonical resonator sweep at 0.25, 0.70, and 0.92.');

resonator_sweep_responses = zeros(numel(resonator_radius_sweep), sample_count);
resonator_sweep_outputs_v = zeros(numel(resonator_radius_sweep), sample_count);
resonator_time_constant_samples = zeros(size(resonator_radius_sweep));
for sweep_index = 1:numel(resonator_radius_sweep)
    radius_case = resonator_radius_sweep(sweep_index);
    resonator_sweep_responses(sweep_index,:) = ...
        resonator_input_gain*radius_case.^n .* ...
        sin((n+1)*resonator_angle_rad)/sin(resonator_angle_rad);
    resonator_case_full = conv(general_input_v, ...
        resonator_sweep_responses(sweep_index,:));
    resonator_sweep_outputs_v(sweep_index,:) = ...
        resonator_case_full(1:sample_count);
    resonator_time_constant_samples(sweep_index) = -1/log(radius_case);
    fprintf(['P06 resonator sweep: radius = %.2f, ring frequency = %.1f Hz, ' ...
        'time constant = %.3f samples = %.3f ms\n'], radius_case, ...
        resonator_frequency_hz, ...
        resonator_time_constant_samples(sweep_index), ...
        1000*resonator_time_constant_samples(sweep_index)/fs);
end
assert(all(diff(resonator_time_constant_samples) > 0), ...
    'A pole nearer one must produce a longer decay time.');

figure('Name', 'P06 sweep 2: the pole controls response memory', ...
    'Tag', p06_figure_tag);
subplot(2,1,1);
for sweep_index = 1:numel(resonator_radius_sweep)
    stem(n(1:64), resonator_sweep_responses(sweep_index,1:64), ...
        'DisplayName', sprintf('r = %.2f', resonator_radius_sweep(sweep_index)));
    hold on;
end
grid on;
xlabel('Lag k (samples)');
ylabel('h[k] (V/V)');
title(sprintf('Radius controls decay; ring frequency stays %.1f Hz', ...
    resonator_frequency_hz));
legend('Location', 'best');
subplot(2,1,2);
for sweep_index = 1:numel(resonator_radius_sweep)
    plot(t_s, resonator_sweep_outputs_v(sweep_index,:), 'LineWidth', 1.0, ...
        'DisplayName', sprintf('r = %.2f', resonator_radius_sweep(sweep_index)));
    hold on;
end
grid on;
xlabel('Time (s)');
ylabel('Resonator output (V)');
title('Longer impulse-response memory produces longer ringing');
legend('Location', 'best');

%% Deliberately broken case - unpadded FFT creates circular convolution
% An N-point FFT product computes
% y_circular[n] = sum_k h[k]*x[mod(n-k,N)], not causal linear convolution.
% The response tail wraps onto the record beginning. Recovery uses conv, or
% equivalently an FFT length of at least 2*N-1 before cropping the causal view.
broken_circular_output_v = real(ifft(fft(general_input_v, sample_count).* ...
    fft(h_echo_path, sample_count)));
correct_linear_full_v = conv(general_input_v, h_echo_path);
recovered_linear_output_v = correct_linear_full_v(1:sample_count);
broken_residual_v = broken_circular_output_v-recovered_linear_output_v;
broken_max_error_v = max(abs(broken_residual_v));
wrapped_tail_energy_v2 = sum(broken_residual_v(1:echo_delay_samples).^2);
assert(broken_max_error_v > 0.05, ...
    'The broken circular-convolution case must create visible wraparound.');
assert(wrapped_tail_energy_v2 > 1e-3, ...
    'The broken case must put nontrivial wrapped energy at the record start.');
assert(max(abs(recovered_linear_output_v-y_direct(3,:))) < ...
    comparison_tolerance_v, ...
    'Linear convolution must recover the direct echo-path output.');

figure('Name', 'P06 broken case: circular wraparound is not the LTI output', ...
    'Tag', p06_figure_tag);
subplot(2,1,1);
plot(t_s, recovered_linear_output_v, 'LineWidth', 1.2, ...
    'DisplayName', 'Correct linear convolution');
hold on;
plot(t_s, broken_circular_output_v, '--', 'LineWidth', 1.0, ...
    'DisplayName', 'Broken N-point circular convolution');
grid on;
xlabel('Time (s)');
ylabel('Echo-path output (V)');
title(sprintf('Insufficient FFT length wraps the tail; max error %.3f V', ...
    broken_max_error_v));
legend('Location', 'best');
subplot(2,1,2);
stem(n(1:80), broken_residual_v(1:80), 'filled');
grid on;
xlabel('Sample index n');
ylabel('Circular-minus-linear error (V)');
title(sprintf('Wrapped-start error energy = %.4f V^2', ...
    wrapped_tail_energy_v2));

fprintf('P06 broken case and recovery\n');
fprintf('  N-point circular max error      = %.6f V\n', broken_max_error_v);
fprintf('  wrapped-start error energy      = %.6f V^2\n', ...
    wrapped_tail_energy_v2);
fprintf('  recovered linear max error      = %.6e V\n', ...
    max(abs(recovered_linear_output_v-y_direct(3,:))));

%% Retain the measurements for inspection
results = struct();
results.random_seed = random_seed;
results.sample_rate_samples_per_s = fs;
results.time_s = t_s;
results.input_v = general_input_v;
results.system_names = system_names;
results.impulse_responses_v_per_v = impulse_responses;
results.direct_output_v = y_direct;
results.convolution_output_v = y_from_impulse;
results.max_abs_error_v = max_abs_error_v;
results.rms_error_v = rms_error_v;
results.echo_delay_sweep_samples = echo_delay_sweep_samples;
results.echo_delay_sweep_ms = echo_delay_sweep_ms;
results.resonator_radius_sweep = resonator_radius_sweep;
results.resonator_frequency_hz = resonator_frequency_hz;
results.resonator_time_constant_samples = resonator_time_constant_samples;
results.broken_circular_output_v = broken_circular_output_v;
results.recovered_linear_output_v = recovered_linear_output_v;
results.broken_max_error_v = broken_max_error_v;
results.wrapped_tail_energy_v2 = wrapped_tail_energy_v2;

% Every loop is finite and bounded by sample_count, system_count, or a sweep
% capped at max_sweep_cases. The script writes no files, changes no learner
% progress, starts no asynchronous task, and requires no cancellation API.
