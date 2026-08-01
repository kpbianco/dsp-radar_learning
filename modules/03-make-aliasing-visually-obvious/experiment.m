%% P03 - Make Aliasing Visually Obvious
% Guiding question:
% Why does a high-frequency tone appear as a lower-frequency tone after sampling?
%
% Dependency contract: base MATLAB only. No toolbox functions are required.
clear;
close all;
clc;
random_seed = 303;
rng(random_seed, 'twister');

%% Committed baseline controls - sweeps below vary one variable at a time
A = 1.0;                           % tone amplitude (arbitrary units)
f_input = 700.0;                   % continuous input frequency (Hz)
fs = 1000.0;                       % fixed sample rate (samples/s)
phi = pi/5;                        % input phase (rad)
duration = 0.2;                    % sampled record duration (s)
fs_display = 20000.0;              % dense display rate (points/s)
display_duration = 0.025;          % short time view (s)
max_display_points = 20001;        % resource ceiling for a dense view
max_samples_per_case = 5000;       % resource ceiling for a sampled record
max_sweep_cases = 128;             % resource ceiling for an edited sweep
max_representative_cases = 8;      % resource ceiling for time-sequence panels

% Fail before allocation if an edited control is malformed.
assert(isscalar(A) && isnumeric(A) && ~islogical(A) && ...
    isreal(A) && isfinite(A) && A > 0, ...
    'A must be one finite positive real scalar.');
assert(isscalar(f_input) && isnumeric(f_input) && ~islogical(f_input) && ...
    isreal(f_input) && isfinite(f_input) && f_input > 0, ...
    'f_input must be one finite positive real frequency in Hz.');
assert(isscalar(fs) && isnumeric(fs) && ~islogical(fs) && ...
    isreal(fs) && isfinite(fs) && fs > 0, ...
    'fs must be one finite positive real sample rate.');
assert(isscalar(phi) && isnumeric(phi) && ~islogical(phi) && ...
    isreal(phi) && isfinite(phi), ...
    'phi must be one finite real phase in radians.');
assert(isscalar(duration) && isnumeric(duration) && ~islogical(duration) && ...
    isreal(duration) && isfinite(duration) && duration > 0, ...
    'duration must be one finite positive real value in seconds.');
assert(isscalar(fs_display) && isnumeric(fs_display) && ...
    ~islogical(fs_display) && isreal(fs_display) && ...
    isfinite(fs_display) && fs_display > 2*f_input, ...
    'fs_display must be finite, real, and greater than 2*f_input.');
assert(isscalar(display_duration) && isnumeric(display_duration) && ...
    ~islogical(display_duration) && isreal(display_duration) && ...
    isfinite(display_duration) && display_duration > 0 && ...
    display_duration <= duration, ...
    'display_duration must be finite, positive, and no longer than duration.');

sample_count = round(duration*fs);
assert(sample_count >= 5 && abs(sample_count-duration*fs) < ...
    10*eps(max(1, duration*fs)), ...
    'duration*fs must be an integer of at least five samples.');
assert(sample_count <= max_samples_per_case, ...
    'A sampled record is limited to 5000 samples; reduce fs or duration.');
display_intervals = round(display_duration*fs_display);
assert(display_intervals >= 2 && ...
    abs(display_intervals-display_duration*fs_display) < ...
    10*eps(max(1, display_duration*fs_display)), ...
    'display_duration*fs_display must be an integer of at least two intervals.');
display_point_count = display_intervals + 1;
assert(display_point_count <= max_display_points, ...
    'A dense display is limited to 20001 points.');

%% Baseline - the sampler cannot distinguish the input from its fold
n = 0:sample_count-1;
t_sample = n/fs;
x_sample = A*cos(2*pi*f_input*t_sample + phi);

% Folding is explicit: subtract the nearest integer multiple of fs.
% A real cosine cannot reveal the sign, so the apparent frequency is the
% magnitude of the signed fold. A negative fold reverses cosine phase.
alias_order = round(f_input/fs);
f_alias_signed = f_input - alias_order*fs;
f_apparent = abs(f_alias_signed);
phi_alias = phi;
if f_alias_signed < 0
    phi_alias = -phi;
end
x_alias_at_samples = A*cos(2*pi*f_apparent*t_sample + phi_alias);

% Estimate apparent frequency from the samples themselves. A sampled cosine
% obeys x[n+1] + x[n-1] = 2*cos(omega)*x[n]. Solving that recurrence for
% cos(omega), then taking acos, gives the unsigned frequency in [0, fs/2].
x_center = x_sample(2:end-1);
x_neighbor_sum = x_sample(3:end) + x_sample(1:end-2);
recurrence_denominator = 2*sum(x_center.^2);
assert(recurrence_denominator > 100*eps(max(1, A^2)), ...
    'The baseline samples are degenerate for the recurrence estimator.');
cos_omega_hat = sum(x_center.*x_neighbor_sum)/recurrence_denominator;
cos_omega_hat = max(-1, min(1, cos_omega_hat));
f_apparent_hat = fs*acos(cos_omega_hat)/(2*pi);

t_display = (0:display_intervals)/fs_display;
x_input_display = A*cos(2*pi*f_input*t_display + phi);
x_alias_display = A*cos(2*pi*f_apparent*t_display + phi_alias);
sample_view = t_sample <= display_duration;

figure('Name', 'P03 baseline: one sample sequence, two continuous tones');
subplot(2,1,1);
plot(t_display, x_input_display, 'LineWidth', 1.1, ...
    'DisplayName', sprintf('input %.0f Hz', f_input));
hold on;
plot(t_display, x_alias_display, '--', 'LineWidth', 1.2, ...
    'DisplayName', sprintf('apparent %.0f Hz', f_apparent));
stem(t_sample(sample_view), x_sample(sample_view), 'filled', ...
    'DisplayName', sprintf('samples at %.0f samples/s', fs));
grid on;
xlabel('Time (s)');
ylabel('Amplitude (a.u.)');
title('Both continuous tones cross every stored measurement');
legend('Location', 'best');

subplot(2,1,2);
baseline_view_count = min(20, sample_count);
stem(n(1:baseline_view_count), x_sample(1:baseline_view_count), 'filled', ...
    'DisplayName', 'stored x[n]');
hold on;
plot(n(1:baseline_view_count), x_alias_at_samples(1:baseline_view_count), 'o', ...
    'DisplayName', 'samples predicted by folded tone');
grid on;
xlabel('Sample index n (samples)');
ylabel('Measured amplitude x[n] (a.u.)');
title(sprintf('Estimator sees %.3f Hz inside the 0 to %.0f Hz Nyquist interval', ...
    f_apparent_hat, fs/2));
legend('Location', 'best');

alias_argument_scale = 1 + max(abs([2*pi*f_input*t_sample + phi, ...
    2*pi*f_apparent*t_sample + phi_alias]));
alias_tolerance = min(1e-9*max(1, abs(A)), ...
    64*eps(max(1, abs(A)))*alias_argument_scale);
alias_sample_error = max(abs(x_sample-x_alias_at_samples));
estimator_error = abs(f_apparent_hat-f_apparent);

fprintf('P03 baseline metrics\n');
fprintf('  random seed                    = %d\n', random_seed);
fprintf('  input frequency                = %.3f Hz\n', f_input);
fprintf('  sample rate                    = %.3f samples/s\n', fs);
fprintf('  Nyquist limit                  = %.3f Hz\n', fs/2);
fprintf('  alias order                    = %d multiples of fs\n', alias_order);
fprintf('  signed folded frequency        = %.3f Hz\n', f_alias_signed);
fprintf('  apparent frequency             = %.3f Hz\n', f_apparent);
fprintf('  recurrence estimate            = %.6f Hz\n', f_apparent_hat);
fprintf('  estimator error                = %.3g Hz\n', estimator_error);
fprintf('  input/alias sample disagreement= %.3g a.u.\n', alias_sample_error);

assert(f_input > fs/2, ...
    'The committed baseline must keep the input above the Nyquist limit.');
assert(f_alias_signed < 0 && abs(f_alias_signed+300) < 1e-12, ...
    'The committed baseline must fold 700 Hz to signed -300 Hz.');
assert(alias_sample_error < alias_tolerance, ...
    'The input and correctly phased alias must agree at every sample.');
assert(estimator_error < 1e-8, ...
    'The recurrence estimator must recover the baseline apparent frequency.');

%% Parameter sweep 1 - sweep input frequency with sample rate fixed
input_frequency_sweep = 0:25:3000; % Hz, DC through three multiples of fs
assert(isvector(input_frequency_sweep) && ...
    isnumeric(input_frequency_sweep) && ~islogical(input_frequency_sweep) && ...
    isreal(input_frequency_sweep) && all(isfinite(input_frequency_sweep)) && ...
    all(input_frequency_sweep >= 0), ...
    'input_frequency_sweep must contain finite nonnegative real frequencies.');
assert(numel(input_frequency_sweep) >= 9 && ...
    numel(input_frequency_sweep) <= max_sweep_cases, ...
    'The input-frequency sweep must contain from 9 through 128 cases.');
assert(input_frequency_sweep(1) == 0 && ...
    input_frequency_sweep(end) >= 3*fs, ...
    'The input-frequency sweep must run from DC through at least 3*fs.');

signed_fold_sweep = zeros(size(input_frequency_sweep));
apparent_frequency_sweep = zeros(size(input_frequency_sweep));
estimated_frequency_sweep = zeros(size(input_frequency_sweep));
for frequency_index = 1:numel(input_frequency_sweep)
    f_case = input_frequency_sweep(frequency_index);
    x_case = A*cos(2*pi*f_case*n/fs + phi);
    fold_case = f_case - round(f_case/fs)*fs;
    signed_fold_sweep(frequency_index) = fold_case;
    apparent_frequency_sweep(frequency_index) = abs(fold_case);

    center_case = x_case(2:end-1);
    neighbor_case = x_case(3:end) + x_case(1:end-2);
    denominator_case = 2*sum(center_case.^2);
    assert(denominator_case > 100*eps(max(1, A^2)), ...
        'A sweep case is degenerate for the recurrence estimator.');
    cos_case = sum(center_case.*neighbor_case)/denominator_case;
    cos_case = max(-1, min(1, cos_case));
    estimated_frequency_sweep(frequency_index) = ...
        fs*acos(cos_case)/(2*pi);
end
sweep_estimator_error = ...
    max(abs(estimated_frequency_sweep-apparent_frequency_sweep));
assert(all(abs(signed_fold_sweep) <= fs/2 + 1e-10), ...
    'Every signed fold must remain inside the Nyquist interval.');
assert(sweep_estimator_error < 1e-8, ...
    'Every recurrence estimate must follow the theoretical alias fold.');

figure('Name', 'P03 sweep 1: deterministic folding across multiples of fs');
subplot(2,1,1);
plot(input_frequency_sweep, apparent_frequency_sweep, 'LineWidth', 1.4, ...
    'DisplayName', 'theoretical |fold|');
hold on;
plot(input_frequency_sweep, estimated_frequency_sweep, '.', ...
    'DisplayName', 'estimated from x[n] recurrence');
plot(input_frequency_sweep, (fs/2)*ones(size(input_frequency_sweep)), ':', ...
    'DisplayName', 'Nyquist limit');
grid on;
xlabel('Input frequency (Hz)');
ylabel('Apparent frequency (Hz)');
title('A fixed sampler creates a triangular frequency-folding pattern');
legend('Location', 'best');

subplot(2,1,2);
plot(input_frequency_sweep, signed_fold_sweep, 'LineWidth', 1.2, ...
    'DisplayName', 'signed fold');
hold on;
plot(input_frequency_sweep, (fs/2)*ones(size(input_frequency_sweep)), ':', ...
    'DisplayName', '+f_s/2');
plot(input_frequency_sweep, -(fs/2)*ones(size(input_frequency_sweep)), ':', ...
    'DisplayName', '-f_s/2');
grid on;
xlabel('Input frequency (Hz)');
ylabel('Signed folded frequency (Hz)');
title('The sign reverses at each reflected half of a fold');
legend('Location', 'best');

fprintf('P03 input-frequency sweep metrics\n');
fprintf('  sweep cases                    = %d cases\n', ...
    numel(input_frequency_sweep));
fprintf('  input range                    = %.1f to %.1f Hz\n', ...
    input_frequency_sweep(1), input_frequency_sweep(end));
fprintf('  maximum estimator error        = %.3g Hz\n', sweep_estimator_error);

%% Representative sequences - look immediately around two folds
representative_frequencies = [450 500 550 950 1000 1050]; % Hz
assert(isvector(representative_frequencies) && ...
    isnumeric(representative_frequencies) && ...
    ~islogical(representative_frequencies) && ...
    isreal(representative_frequencies) && ...
    all(isfinite(representative_frequencies)) && ...
    all(representative_frequencies >= 0), ...
    'representative_frequencies must contain finite nonnegative real values.');
assert(numel(representative_frequencies) >= 3 && ...
    numel(representative_frequencies) <= max_representative_cases, ...
    'Representative time-sequence panels require from three through eight cases.');

figure('Name', 'P03 sweep 1: representative sequences near folds');
representative_plot_rows = ceil(numel(representative_frequencies)/2);
for representative_index = 1:numel(representative_frequencies)
    f_case = representative_frequencies(representative_index);
    signed_case = f_case-round(f_case/fs)*fs;
    apparent_case = abs(signed_case);
    phase_case = phi;
    if signed_case < 0
        phase_case = -phi;
    end
    x_case = A*cos(2*pi*f_case*n/fs + phi);
    x_alias_case = A*cos(2*pi*apparent_case*n/fs + phase_case);
    representative_view_count = min(16, sample_count);

    subplot(representative_plot_rows,2,representative_index);
    stem(n(1:representative_view_count), ...
        x_case(1:representative_view_count), 'filled', ...
        'DisplayName', 'input samples');
    hold on;
    plot(n(1:representative_view_count), ...
        x_alias_case(1:representative_view_count), 'o', ...
        'DisplayName', 'fold prediction');
    grid on;
    xlabel('Sample index n (samples)');
    ylabel('Amplitude (a.u.)');
    title(sprintf('%.0f Hz input -> %.0f Hz apparent', f_case, apparent_case));
end

%% Parameter sweep 2 - hold the input fixed and change only sample rate
sample_rate_sweep = [2000 1200 1000 800]; % samples/s
assert(isvector(sample_rate_sweep) && isnumeric(sample_rate_sweep) && ...
    ~islogical(sample_rate_sweep) && isreal(sample_rate_sweep) && ...
    all(isfinite(sample_rate_sweep)) && all(sample_rate_sweep > 0), ...
    'sample_rate_sweep must contain finite positive real sample rates.');
assert(numel(sample_rate_sweep) >= 3 && ...
    numel(sample_rate_sweep) <= max_representative_cases, ...
    'The sample-rate sweep must contain from three through eight cases.');

sample_rate_aliases = zeros(size(sample_rate_sweep));
sample_rate_estimates = zeros(size(sample_rate_sweep));
figure('Name', 'P03 sweep 2: one tone seen by different sample rates');
rate_plot_rows = ceil(numel(sample_rate_sweep)/2);
for rate_index = 1:numel(sample_rate_sweep)
    fs_case = sample_rate_sweep(rate_index);
    sample_count_case = round(duration*fs_case);
    assert(sample_count_case >= 5 && ...
        abs(sample_count_case-duration*fs_case) < ...
        10*eps(max(1, duration*fs_case)), ...
        'Every rate case must create an integer record of at least five samples.');
    assert(sample_count_case <= max_samples_per_case, ...
        'Every sample-rate case is limited to 5000 samples.');
    n_case = 0:sample_count_case-1;
    x_case = A*cos(2*pi*f_input*n_case/fs_case + phi);
    signed_case = f_input-round(f_input/fs_case)*fs_case;
    sample_rate_aliases(rate_index) = abs(signed_case);

    center_case = x_case(2:end-1);
    neighbor_case = x_case(3:end) + x_case(1:end-2);
    denominator_case = 2*sum(center_case.^2);
    assert(denominator_case > 100*eps(max(1, A^2)), ...
        'A sample-rate case is degenerate for the recurrence estimator.');
    cos_case = sum(center_case.*neighbor_case)/denominator_case;
    cos_case = max(-1, min(1, cos_case));
    sample_rate_estimates(rate_index) = fs_case*acos(cos_case)/(2*pi);

    subplot(rate_plot_rows,2,rate_index);
    rate_view_count = min(16, sample_count_case);
    stem(n_case(1:rate_view_count), x_case(1:rate_view_count), 'filled');
    grid on;
    xlabel('Sample index n (samples)');
    ylabel('Amplitude (a.u.)');
    title(sprintf('f_s=%.0f samples/s -> %.0f Hz apparent', ...
        fs_case, sample_rate_aliases(rate_index)));

    fprintf(['P03 sample-rate sweep: fs = %.1f samples/s, Nyquist = %.1f Hz, ' ...
        'apparent = %.3f Hz, estimate = %.6f Hz\n'], ...
        fs_case, fs_case/2, sample_rate_aliases(rate_index), ...
        sample_rate_estimates(rate_index));
end
assert(max(abs(sample_rate_estimates-sample_rate_aliases)) < 1e-8, ...
    'Sample-rate sweep estimates must follow their theoretical folds.');
assert(all(sample_rate_aliases <= sample_rate_sweep/2 + 1e-10), ...
    'Every sample-rate case must fold inside its own Nyquist interval.');

%% Deliberately broken case - ignore phase reversal after a reflected fold
% A common wrong model uses |f_alias_signed| but keeps the original phase.
% It predicts the right apparent frequency and still misses the measurements.
f_wrong_alias = f_apparent;
phi_wrong_alias = phi;
x_wrong_alias_at_samples = ...
    A*cos(2*pi*f_wrong_alias*t_sample + phi_wrong_alias);
wrong_phase_error = max(abs(x_sample-x_wrong_alias_at_samples));
correct_phase_error = max(abs(x_sample-x_alias_at_samples));
x_wrong_alias_display = ...
    A*cos(2*pi*f_wrong_alias*t_display + phi_wrong_alias);

figure('Name', 'P03 broken case: right frequency, wrong reflected phase');
plot(t_display, x_input_display, 'LineWidth', 1.0, ...
    'DisplayName', sprintf('input %.0f Hz', f_input));
hold on;
plot(t_display, x_alias_display, '--', 'LineWidth', 1.2, ...
    'DisplayName', sprintf('correct %.0f Hz alias, phase -phi', f_apparent));
plot(t_display, x_wrong_alias_display, ':', 'LineWidth', 1.4, ...
    'DisplayName', sprintf('broken %.0f Hz alias, phase +phi', f_wrong_alias));
stem(t_sample(sample_view), x_sample(sample_view), 'filled', ...
    'DisplayName', 'stored samples');
grid on;
xlabel('Time (s)');
ylabel('Amplitude (a.u.)');
title('Broken model: taking absolute frequency without reversing phase');
legend('Location', 'best');

fprintf('P03 broken-case metrics\n');
fprintf('  correct reflected phase         = %.6f rad\n', phi_alias);
fprintf('  broken retained phase           = %.6f rad\n', phi_wrong_alias);
fprintf('  correct model sample error      = %.3g a.u.\n', correct_phase_error);
fprintf('  broken model sample error       = %.6f a.u.\n', wrong_phase_error);

assert(correct_phase_error < alias_tolerance, ...
    'Recovery must reverse phase and restore sample agreement.');
assert(wrong_phase_error > 0.5*A, ...
    'The intentionally broken phase model must visibly miss the samples.');

%% Completion summary
fprintf(['P03 complete: a real sampler maps every input frequency to a ' ...
    'deterministic fold between 0 and fs/2; the stored sequence alone cannot ' ...
    'identify which member of the alias family entered the sampler.\n']);
