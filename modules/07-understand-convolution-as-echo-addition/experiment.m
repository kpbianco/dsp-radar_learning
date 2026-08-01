%% P07 - Understand Convolution as Echo Addition
% Guiding question:
% What is convolution actually doing at each output sample?
%
% Dependency contract: P06 and base MATLAB only. No toolbox, helper
% function, external data, file, network, device, or service is required.
% The finite script uses a private deterministic stream, preserves unrelated
% figures and the global random stream, and replaces only prior P07 figures.
% It still creates or replaces its named workspace variables, including results.
p07_figure_tag = 'P07ConvolutionEchoLab';
prior_p07_figures = findall(groot, 'Type', 'figure', 'Tag', p07_figure_tag);
if ~isempty(prior_p07_figures)
    close(prior_p07_figures);
end

%% Baseline controls - change one at a time
random_seed = 707;
fs = 1000;                              % sample rate (samples/s)
input_sample_count = 40;                % finite input support (samples)
pulse_start_sample = 5;                 % first pulse sample, zero-based n
pulse_shape_v = [0.25 0.50 0.75 1.00 0.75 0.50 0.25]; % voltage (V)
tap_delays_samples = [0 5 9];           % path delays (samples)
tap_gains = [1.00 0.60 -0.35];         % signed path gains (V/V)
comparison_tolerance_v = 2e-12;         % implementation agreement (V)
animation_pause_s = 0.08;               % bounded display pause per frame (s)
max_input_samples = 256;                % fixed resource ceiling (samples)
max_output_samples = 512;               % fixed resource ceiling (samples)
max_taps = 8;                           % fixed resource ceiling (paths)
max_sweep_cases = 8;                    % fixed resource ceiling (cases)
max_animation_frames = 64;              % fixed resource ceiling (frames)
expected_tap_count = 3;                 % canonical direct plus two echoes
middle_delay_sweep_samples = [3 5 7];   % Sweep 1: only middle delay
third_gain_sweep = [-0.70 -0.35 0.35];  % Sweep 2: only third gain
inspection_output_sample = 14;          % overlap sample to explain, zero-based
broken_input_sample_count = 24;          % fixed failure-fixture input support
broken_pulse_start_sample = 5;           % fixed failure-fixture pulse onset
broken_pulse_shape_v = [0.25 0.50 0.75 1.00 0.75 0.50 0.25];
broken_delays_samples = [0 3 6];         % fixed overlapping path delays
broken_gains = [1.00 0.60 -0.35];        % fixed failure-fixture path gains

% Fail before signal, response, sweep-output, or animation allocation when an
% edited control is malformed. These guards also bound finite runtime/memory.
assert(isscalar(random_seed) && isnumeric(random_seed) && ...
    ~islogical(random_seed) && isreal(random_seed) && isfinite(random_seed) && ...
    random_seed == floor(random_seed) && random_seed >= 0 && ...
    random_seed <= 2^32-1, ...
    'random_seed must be one supported integer from zero through 2^32-1.');
assert(isscalar(fs) && isnumeric(fs) && ~islogical(fs) && isreal(fs) && ...
    isfinite(fs) && fs > 0, ...
    'fs must be one finite positive real sample rate.');
assert(isscalar(input_sample_count) && isnumeric(input_sample_count) && ...
    ~islogical(input_sample_count) && isreal(input_sample_count) && ...
    isfinite(input_sample_count) && input_sample_count == floor(input_sample_count) && ...
    input_sample_count >= 16, ...
    'input_sample_count must be one finite integer of at least 16 samples.');
assert(isvector(pulse_shape_v) && isnumeric(pulse_shape_v) && ...
    ~islogical(pulse_shape_v) && isreal(pulse_shape_v) && ...
    all(isfinite(pulse_shape_v)) && numel(pulse_shape_v) >= 3 && ...
    numel(pulse_shape_v) <= 32 && any(pulse_shape_v ~= 0), ...
    'pulse_shape_v must contain 3 through 32 finite real samples and be nonzero.');
assert(isscalar(pulse_start_sample) && isnumeric(pulse_start_sample) && ...
    ~islogical(pulse_start_sample) && isreal(pulse_start_sample) && ...
    isfinite(pulse_start_sample) && ...
    pulse_start_sample == floor(pulse_start_sample) && pulse_start_sample >= 0, ...
    'pulse_start_sample must be one finite nonnegative integer.');
assert(isvector(tap_delays_samples) && isnumeric(tap_delays_samples) && ...
    ~islogical(tap_delays_samples) && isreal(tap_delays_samples) && ...
    all(isfinite(tap_delays_samples)) && ...
    all(tap_delays_samples == floor(tap_delays_samples)) && ...
    all(tap_delays_samples >= 0), ...
    'tap_delays_samples must contain finite nonnegative integers.');
assert(isvector(tap_gains) && isnumeric(tap_gains) && ...
    ~islogical(tap_gains) && isreal(tap_gains) && all(isfinite(tap_gains)), ...
    'tap_gains must contain finite real path gains.');
assert(numel(tap_delays_samples) == expected_tap_count && ...
    numel(tap_gains) == expected_tap_count && ...
    expected_tap_count <= max_taps, ...
    'The canonical channel requires exactly three bounded taps.');
assert(tap_delays_samples(1) == 0 && ...
    all(diff(tap_delays_samples) > 0), ...
    'Tap delays must begin at zero and be strictly increasing.');
assert(all(tap_gains ~= 0) && ...
    numel(unique(abs(tap_gains))) == expected_tap_count, ...
    'All three path gains must be nonzero with visibly different magnitudes.');
assert(isscalar(comparison_tolerance_v) && ...
    isnumeric(comparison_tolerance_v) && ~islogical(comparison_tolerance_v) && ...
    isreal(comparison_tolerance_v) && isfinite(comparison_tolerance_v) && ...
    comparison_tolerance_v > 0 && comparison_tolerance_v <= 1e-9, ...
    'comparison_tolerance_v must be finite, positive, and at most 1e-9 V.');
assert(isscalar(animation_pause_s) && isnumeric(animation_pause_s) && ...
    ~islogical(animation_pause_s) && isreal(animation_pause_s) && ...
    isfinite(animation_pause_s) && animation_pause_s >= 0 && ...
    animation_pause_s <= 0.25, ...
    'animation_pause_s must be finite and between 0 and 0.25 seconds.');
assert(isscalar(max_input_samples) && max_input_samples == 256 && ...
    max_input_samples == floor(max_input_samples), ...
    'max_input_samples is a fixed safety ceiling of 256 samples.');
assert(isscalar(max_output_samples) && max_output_samples == 512 && ...
    max_output_samples == floor(max_output_samples), ...
    'max_output_samples is a fixed safety ceiling of 512 samples.');
assert(isscalar(max_taps) && max_taps == 8 && max_taps == floor(max_taps), ...
    'max_taps is a fixed safety ceiling of eight paths.');
assert(isscalar(max_sweep_cases) && max_sweep_cases == 8 && ...
    max_sweep_cases == floor(max_sweep_cases), ...
    'max_sweep_cases is a fixed safety ceiling of eight cases.');
assert(isscalar(max_animation_frames) && max_animation_frames == 64 && ...
    max_animation_frames == floor(max_animation_frames), ...
    'max_animation_frames is a fixed safety ceiling of 64 frames.');
assert(input_sample_count <= max_input_samples, ...
    'Reduce input_sample_count to the 256-sample ceiling.');
assert(pulse_start_sample + numel(pulse_shape_v) <= input_sample_count, ...
    'The complete pulse must fit inside the finite input record.');
output_sample_count = input_sample_count + tap_delays_samples(end);
assert(output_sample_count <= max_output_samples, ...
    'Input length plus channel delay exceeds the 512-sample output ceiling.');
assert(isscalar(inspection_output_sample) && ...
    isnumeric(inspection_output_sample) && ~islogical(inspection_output_sample) && ...
    isreal(inspection_output_sample) && isfinite(inspection_output_sample) && ...
    inspection_output_sample == floor(inspection_output_sample) && ...
    inspection_output_sample >= 0 && ...
    inspection_output_sample < output_sample_count, ...
    'inspection_output_sample must be a valid finite integer output sample.');
assert(isvector(middle_delay_sweep_samples) && ...
    isnumeric(middle_delay_sweep_samples) && ...
    ~islogical(middle_delay_sweep_samples) && ...
    isreal(middle_delay_sweep_samples) && ...
    all(isfinite(middle_delay_sweep_samples)) && ...
    all(middle_delay_sweep_samples == floor(middle_delay_sweep_samples)) && ...
    all(middle_delay_sweep_samples > tap_delays_samples(1)) && ...
    all(middle_delay_sweep_samples < tap_delays_samples(3)), ...
    'Middle-delay sweep values must be finite integers between the other taps.');
assert(numel(middle_delay_sweep_samples) >= 2 && ...
    numel(middle_delay_sweep_samples) <= max_sweep_cases && ...
    isequal(middle_delay_sweep_samples, [3 5 7]), ...
    'Keep the canonical middle-delay sweep at 3, 5, and 7 samples.');
assert(isvector(third_gain_sweep) && isnumeric(third_gain_sweep) && ...
    ~islogical(third_gain_sweep) && isreal(third_gain_sweep) && ...
    all(isfinite(third_gain_sweep)) && all(third_gain_sweep ~= 0), ...
    'Third-gain sweep values must be finite nonzero real gains.');
assert(numel(third_gain_sweep) >= 2 && ...
    numel(third_gain_sweep) <= max_sweep_cases && ...
    isequal(third_gain_sweep, [-0.70 -0.35 0.35]), ...
    'Keep the canonical third-gain sweep at -0.70, -0.35, and 0.35.');
assert(isscalar(broken_input_sample_count) && ...
    isnumeric(broken_input_sample_count) && ...
    ~islogical(broken_input_sample_count) && ...
    isreal(broken_input_sample_count) && isfinite(broken_input_sample_count) && ...
    broken_input_sample_count == 24, ...
    'broken_input_sample_count is fixed at 24 samples.');
assert(isscalar(broken_pulse_start_sample) && ...
    isnumeric(broken_pulse_start_sample) && ...
    ~islogical(broken_pulse_start_sample) && ...
    isreal(broken_pulse_start_sample) && isfinite(broken_pulse_start_sample) && ...
    broken_pulse_start_sample == 5, ...
    'broken_pulse_start_sample is fixed at sample five.');
assert(isequal(broken_pulse_shape_v, ...
    [0.25 0.50 0.75 1.00 0.75 0.50 0.25]), ...
    'Keep the fixed broken-case pulse shape.');
assert(isequal(broken_delays_samples, [0 3 6]) && ...
    isequal(broken_gains, [1.00 0.60 -0.35]), ...
    'Keep the fixed broken-case delays and gains.');
assert(broken_pulse_start_sample + numel(broken_pulse_shape_v) <= ...
    broken_input_sample_count, ...
    'The fixed broken-case pulse must fit inside its input record.');
broken_output_sample_count = broken_input_sample_count + ...
    broken_delays_samples(end);
assert(broken_output_sample_count <= max_output_samples, ...
    'The broken-case output exceeds the fixed output ceiling.');

%% Deterministic short pulse and explicit three-tap echo channel
% The private stream makes any future stochastic extension reproducible without
% changing MATLAB's global random stream. The canonical pulse itself stays
% simple enough to predict exactly by hand.
random_stream = RandStream('mt19937ar', 'Seed', random_seed);
seed_signature = rand(random_stream, 1, 4);
input_n = 0:input_sample_count-1;
output_n = 0:output_sample_count-1;
input_pulse_v = zeros(1, input_sample_count);
pulse_indices = pulse_start_sample + (0:numel(pulse_shape_v)-1);
input_pulse_v(pulse_indices+1) = pulse_shape_v;
channel_impulse_response = zeros(1, tap_delays_samples(end)+1);
channel_impulse_response(tap_delays_samples+1) = tap_gains;
tap_delays_ms = 1000*tap_delays_samples/fs;

figure('Name', 'P07 baseline 1: pulse and three-tap echo channel', ...
    'Tag', p07_figure_tag);
subplot(2,1,1);
stem(input_n, input_pulse_v, 'filled');
grid on;
xlabel('Input sample index n');
ylabel('Input voltage x[n] (V)');
title(sprintf('Short deterministic pulse; private seed %d', random_seed));
subplot(2,1,2);
stem(0:numel(channel_impulse_response)-1, channel_impulse_response, 'filled');
grid on;
xlabel('Path delay k (samples)');
ylabel('Path gain h[k] (V/V)');
title('Three paths: direct and two signed delayed echoes');

%% Build the output first as shifted and scaled copies
% For path p, contribution_p[n] = h[d_p]*x[n-d_p]. The inner assignment is
% visible; the output is the sample-by-sample sum across the three rows.
echo_contributions_v = zeros(expected_tap_count, output_sample_count);
for path_index = 1:expected_tap_count
    path_delay = tap_delays_samples(path_index);
    path_gain = tap_gains(path_index);
    for output_index = 1:output_sample_count
        output_sample = output_index-1;
        source_sample = output_sample-path_delay;
        if source_sample >= 0 && source_sample < input_sample_count
            echo_contributions_v(path_index, output_index) = ...
                path_gain*input_pulse_v(source_sample+1);
        end
    end
end
manual_echo_sum_v = sum(echo_contributions_v, 1);

figure('Name', 'P07 baseline 2: delayed scaled copies add into the output', ...
    'Tag', p07_figure_tag);
for path_index = 1:expected_tap_count
    subplot(expected_tap_count+1,1,path_index);
    stem(output_n, echo_contributions_v(path_index,:), 'filled');
    grid on;
    xlabel('Output sample index n');
    ylabel(sprintf('Path %d (V)', path_index));
    title(sprintf('h[%d]x[n-%d] = %.2f x[n-%d]', ...
        tap_delays_samples(path_index), tap_delays_samples(path_index), ...
        tap_gains(path_index), tap_delays_samples(path_index)));
end
subplot(expected_tap_count+1,1,expected_tap_count+1);
stem(output_n, manual_echo_sum_v, 'filled');
grid on;
xlabel('Output sample index n');
ylabel('Output voltage y[n] (V)');
title('Echo addition: y[n] is the vertical sum of the three rows');

%% Evaluate the convolution sum explicitly, then use conv only as a check
% Linear convolution is y[n] = sum_k h[k]*x[n-k]. This nested loop exposes
% every multiply and addition before the base MATLAB convenience function.
explicit_convolution_v = zeros(1, output_sample_count);
for output_index = 1:output_sample_count
    output_sample = output_index-1;
    for lag_index = 1:numel(channel_impulse_response)
        lag_sample = lag_index-1;
        source_sample = output_sample-lag_sample;
        if source_sample >= 0 && source_sample < input_sample_count
            explicit_convolution_v(output_index) = ...
                explicit_convolution_v(output_index) + ...
                channel_impulse_response(lag_index)* ...
                input_pulse_v(source_sample+1);
        end
    end
end
conv_output_v = conv(input_pulse_v, channel_impulse_response);
manual_vs_explicit_error_v = max(abs(manual_echo_sum_v-explicit_convolution_v));
explicit_vs_conv_error_v = max(abs(explicit_convolution_v-conv_output_v));
assert(manual_vs_explicit_error_v < comparison_tolerance_v, ...
    'Shifted-copy addition must match the explicit convolution sum.');
assert(explicit_vs_conv_error_v < comparison_tolerance_v, ...
    'The explicit convolution sum must match base MATLAB conv.');

selected_contributions_v = echo_contributions_v(:,inspection_output_sample+1);
selected_output_v = sum(selected_contributions_v);
assert(abs(selected_output_v-manual_echo_sum_v(inspection_output_sample+1)) < ...
    comparison_tolerance_v, ...
    'The inspected output must equal the visible path-contribution sum.');

figure('Name', 'P07 baseline 3: manual addition equals convolution', ...
    'Tag', p07_figure_tag);
subplot(2,1,1);
stem(output_n, manual_echo_sum_v, 'filled', ...
    'DisplayName', 'Shift and scale, then add');
hold on;
plot(output_n, explicit_convolution_v, 'ko', 'MarkerSize', 5, ...
    'DisplayName', 'Explicit sum over k');
plot(output_n, conv_output_v, 'r.', 'MarkerSize', 10, ...
    'DisplayName', 'conv(x,h) check');
grid on;
xlabel('Output sample index n');
ylabel('Output voltage y[n] (V)');
title('Three constructions agree sample for sample');
legend('Location', 'best');
subplot(2,1,2);
bar(1:expected_tap_count, selected_contributions_v);
hold on;
plot([0.5 expected_tap_count+0.5], [selected_output_v selected_output_v], ...
    'r--', 'LineWidth', 1.2);
grid on;
xticks(1:expected_tap_count);
xticklabels({'Direct', 'Echo 1', 'Echo 2'});
xlabel(sprintf('Contribution to output sample n = %d', inspection_output_sample));
ylabel('Signed contribution (V)');
title(sprintf('At n=%d, the bars add to y[n]=%.3f V', ...
    inspection_output_sample, selected_output_v));
legend('h[k]x[n-k]', 'Sum y[n]', 'Location', 'best');

fprintf('P07 convolution baseline metrics\n');
fprintf('  random seed / sample rate        = %d / %.1f samples/s\n', ...
    random_seed, fs);
fprintf('  input / output support           = %d / %d samples\n', ...
    input_sample_count, output_sample_count);
for path_index = 1:expected_tap_count
    fprintf('  path %d delay / gain              = %d samples = %.3f ms / %.2f V/V\n', ...
        path_index, tap_delays_samples(path_index), ...
        tap_delays_ms(path_index), tap_gains(path_index));
end
fprintf('  manual versus explicit max error = %.6e V\n', ...
    manual_vs_explicit_error_v);
fprintf('  explicit versus conv max error   = %.6e V\n', ...
    explicit_vs_conv_error_v);
fprintf('  y[%d] path terms / sum           = [%.3f %.3f %.3f] / %.3f V\n', ...
    inspection_output_sample, selected_contributions_v(1), ...
    selected_contributions_v(2), selected_contributions_v(3), selected_output_v);

%% Bounded overlap-and-sum animation for a small sequence
% Each frame fixes n, exposes h[k]*x[n-k] for every k, and adds those terms.
animation_input_v = [1.00 0.50 -0.25 0 0 0 0 0];
animation_response = [1.00 0 0.60 -0.35];
animation_frame_count = numel(animation_input_v) + ...
    numel(animation_response)-1;
assert(animation_frame_count <= max_animation_frames, ...
    'The overlap-and-sum animation exceeds the 64-frame ceiling.');
animation_products_v = zeros(animation_frame_count, ...
    numel(animation_response));
animation_output_v = zeros(1, animation_frame_count);
for frame_index = 1:animation_frame_count
    output_sample = frame_index-1;
    for lag_index = 1:numel(animation_response)
        lag_sample = lag_index-1;
        source_sample = output_sample-lag_sample;
        if source_sample >= 0 && source_sample < numel(animation_input_v)
            animation_products_v(frame_index,lag_index) = ...
                animation_response(lag_index)*animation_input_v(source_sample+1);
        end
    end
    animation_output_v(frame_index) = sum(animation_products_v(frame_index,:));
end
assert(max(abs(animation_output_v-conv(animation_input_v, ...
    animation_response))) < comparison_tolerance_v, ...
    'Every animation frame must implement one convolution output sample.');

animation_figure = figure('Name', ...
    'P07 baseline 4: bounded overlap-and-sum animation', ...
    'Tag', p07_figure_tag);
for frame_index = 1:animation_frame_count
    figure(animation_figure);
    clf(animation_figure);
    subplot(2,1,1);
    stem(0:numel(animation_response)-1, ...
        animation_products_v(frame_index,:), 'filled');
    grid on;
    xlabel('Lag k (samples)');
    ylabel('h[k]x[n-k] (V)');
    title(sprintf('Frame %d of %d: products contributing to n = %d', ...
        frame_index, animation_frame_count, frame_index-1));
    subplot(2,1,2);
    stem(0:animation_frame_count-1, animation_output_v, ...
        'Color', [0.75 0.75 0.75]);
    hold on;
    stem(frame_index-1, animation_output_v(frame_index), 'r', 'filled');
    grid on;
    xlabel('Output sample index n');
    ylabel('Accumulated output y[n] (V)');
    title(sprintf('Add the upper products: y[%d] = %.3f V', ...
        frame_index-1, animation_output_v(frame_index)));
    drawnow;
    if animation_pause_s > 0
        pause(animation_pause_s);
    end
end

%% Parameter sweep 1 - change only the middle echo delay
middle_delay_sweep_ms = 1000*middle_delay_sweep_samples/fs;
delay_sweep_outputs_v = zeros(numel(middle_delay_sweep_samples), ...
    output_sample_count);
for sweep_index = 1:numel(middle_delay_sweep_samples)
    case_delays = tap_delays_samples;
    case_delays(2) = middle_delay_sweep_samples(sweep_index);
    for path_index = 1:expected_tap_count
        for input_index = 1:input_sample_count
            output_index = input_index+case_delays(path_index);
            delay_sweep_outputs_v(sweep_index,output_index) = ...
                delay_sweep_outputs_v(sweep_index,output_index) + ...
                tap_gains(path_index)*input_pulse_v(input_index);
        end
    end
    fprintf('P07 delay sweep: middle path = %d samples = %.3f ms, gain = %.2f V/V\n', ...
        case_delays(2), middle_delay_sweep_ms(sweep_index), tap_gains(2));
end
assert(all(diff(middle_delay_sweep_ms) > 0), ...
    'Increasing middle-path samples must increase physical path delay.');

figure('Name', 'P07 sweep 1: path delay moves one whole echo copy', ...
    'Tag', p07_figure_tag);
for sweep_index = 1:numel(middle_delay_sweep_samples)
    plot(output_n, delay_sweep_outputs_v(sweep_index,:), 'LineWidth', 1.1, ...
        'DisplayName', sprintf('middle delay %.1f ms', ...
        middle_delay_sweep_ms(sweep_index)));
    hold on;
end
grid on;
xlabel('Output sample index n');
ylabel('Output voltage y[n] (V)');
title(sprintf('Only middle delay changes; its gain stays %.2f V/V', tap_gains(2)));
legend('Location', 'best');

%% Parameter sweep 2 - change only the signed third-path gain
gain_sweep_outputs_v = zeros(numel(third_gain_sweep), output_sample_count);
gain_sweep_third_contribution_v = zeros(numel(third_gain_sweep), ...
    output_sample_count);
for sweep_index = 1:numel(third_gain_sweep)
    case_gains = tap_gains;
    case_gains(3) = third_gain_sweep(sweep_index);
    for path_index = 1:expected_tap_count
        for input_index = 1:input_sample_count
            output_index = input_index+tap_delays_samples(path_index);
            path_term_v = case_gains(path_index)*input_pulse_v(input_index);
            gain_sweep_outputs_v(sweep_index,output_index) = ...
                gain_sweep_outputs_v(sweep_index,output_index) + path_term_v;
            if path_index == 3
                gain_sweep_third_contribution_v(sweep_index,output_index) = ...
                    path_term_v;
            end
        end
    end
    fprintf('P07 gain sweep: third path delay = %d samples, gain = %.2f V/V\n', ...
        tap_delays_samples(3), case_gains(3));
end
signed_gain_reversal_error_v = max(abs( ...
    gain_sweep_third_contribution_v(1,:) + ...
    2*gain_sweep_third_contribution_v(3,:)));
assert(max(abs(gain_sweep_third_contribution_v(3,:))) > 0 && ...
    signed_gain_reversal_error_v < comparison_tolerance_v, ...
    'Opposite signed gains must create opposite nonzero third-path contributions.');

figure('Name', 'P07 sweep 2: signed path gain controls addition or cancellation', ...
    'Tag', p07_figure_tag);
for sweep_index = 1:numel(third_gain_sweep)
    plot(output_n, gain_sweep_outputs_v(sweep_index,:), 'LineWidth', 1.1, ...
        'DisplayName', sprintf('third gain %.2f V/V', ...
        third_gain_sweep(sweep_index)));
    hold on;
end
grid on;
xlabel('Output sample index n');
ylabel('Output voltage y[n] (V)');
title(sprintf('Only third gain changes; its delay stays %d samples', ...
    tap_delays_samples(3)));
legend('Location', 'best');

%% Deliberately broken case - overwrite instead of add at overlaps
% The broken loop uses assignment when a shifted copy lands on an occupied
% output sample. It erases an earlier path contribution. Linear convolution
% requires accumulation with "+=" behavior: y[n] = y[n] + h[k]x[n-k].
broken_input_v = zeros(1, broken_input_sample_count);
broken_pulse_indices = broken_pulse_start_sample + ...
    (0:numel(broken_pulse_shape_v)-1);
broken_input_v(broken_pulse_indices+1) = broken_pulse_shape_v;
correct_accumulated_output_v = zeros(1, broken_output_sample_count);
broken_overwrite_output_v = zeros(1, broken_output_sample_count);
for path_index = 1:expected_tap_count
    for input_index = 1:broken_input_sample_count
        if broken_input_v(input_index) ~= 0
            output_index = input_index+broken_delays_samples(path_index);
            path_term_v = broken_gains(path_index)*broken_input_v(input_index);
            correct_accumulated_output_v(output_index) = ...
                correct_accumulated_output_v(output_index) + path_term_v;
            broken_overwrite_output_v(output_index) = path_term_v;
        end
    end
end
broken_response = zeros(1, broken_delays_samples(end)+1);
broken_response(broken_delays_samples+1) = broken_gains;
recovered_output_v = conv(broken_input_v, broken_response);
broken_residual_v = broken_overwrite_output_v-correct_accumulated_output_v;
broken_max_error_v = max(abs(broken_residual_v));
recovery_max_error_v = max(abs(recovered_output_v-correct_accumulated_output_v));
overlap_sample_count = sum(abs(broken_residual_v) > comparison_tolerance_v);
assert(broken_max_error_v > 0.25 && overlap_sample_count >= 3, ...
    'The overwrite failure must visibly lose several overlapping contributions.');
assert(recovery_max_error_v < comparison_tolerance_v, ...
    'Addition at overlaps must recover linear convolution.');

figure('Name', 'P07 broken case: overwrite loses overlapping echo terms', ...
    'Tag', p07_figure_tag);
subplot(2,1,1);
stem(0:broken_output_sample_count-1, correct_accumulated_output_v, 'filled', ...
    'DisplayName', 'Correct: add every path term');
hold on;
plot(0:broken_output_sample_count-1, broken_overwrite_output_v, 'rx', ...
    'MarkerSize', 7, 'DisplayName', 'Broken: overwrite occupied samples');
grid on;
xlabel('Output sample index n');
ylabel('Output voltage y[n] (V)');
title('Assignment is not convolution when shifted copies overlap');
legend('Location', 'best');
subplot(2,1,2);
stem(0:broken_output_sample_count-1, broken_residual_v, 'filled');
grid on;
xlabel('Output sample index n');
ylabel('Overwrite-minus-add error (V)');
title(sprintf('Broken max error %.3f V across %d affected samples', ...
    broken_max_error_v, overlap_sample_count));

fprintf('P07 broken/recovery metrics\n');
fprintf('  overwrite max error              = %.6f V\n', broken_max_error_v);
fprintf('  affected overlap samples         = %d samples\n', overlap_sample_count);
fprintf('  recovered versus correct error   = %.6e V\n', recovery_max_error_v);

%% Retained workspace summary - no file or learner-state write
results = struct();
results.random_seed = random_seed;
results.seed_signature = seed_signature;
results.fs_samples_per_s = fs;
results.tap_delays_samples = tap_delays_samples;
results.tap_delays_ms = tap_delays_ms;
results.tap_gains_v_per_v = tap_gains;
results.echo_contributions_v = echo_contributions_v;
results.manual_output_v = manual_echo_sum_v;
results.explicit_convolution_v = explicit_convolution_v;
results.conv_output_v = conv_output_v;
results.manual_vs_explicit_max_error_v = manual_vs_explicit_error_v;
results.explicit_vs_conv_max_error_v = explicit_vs_conv_error_v;
results.inspection_output_sample = inspection_output_sample;
results.inspection_contributions_v = selected_contributions_v;
results.inspection_output_v = selected_output_v;
results.middle_delay_sweep_samples = middle_delay_sweep_samples;
results.third_gain_sweep_v_per_v = third_gain_sweep;
results.signed_gain_reversal_error_v = signed_gain_reversal_error_v;
results.animation_frame_count = animation_frame_count;
results.broken_max_error_v = broken_max_error_v;
results.broken_overlap_sample_count = overlap_sample_count;
results.recovery_max_error_v = recovery_max_error_v;
