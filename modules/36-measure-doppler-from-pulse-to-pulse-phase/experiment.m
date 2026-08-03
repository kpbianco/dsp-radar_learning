%% P36: Measure Doppler from Pulse-to-Pulse Phase
% Guiding question:
% How does target velocity create coherent phase progression across pulses?
% Sign convention: positive radial velocity means approaching the radar.
% Model: lambda = c/f_c, f_d = 2*v/lambda, and
% delta_phase = 2*pi*f_d/PRF radians per pulse.

clearvars;
close(findall(0, 'Type', 'figure', 'Tag', 'P36'));

%% Visible deterministic controls and resource ceilings
random_seed = 3601;
speed_of_light_mps = 299792458;
carrier_frequency_hz = 10e9;
pulse_repetition_frequency_hz = 4e3;
baseline_velocity_mps = 15;
pulse_count = 32;
echo_amplitude = 1;
initial_phase_deg = 25;
signal_to_noise_ratio_db = 20;
velocity_sweep_mps = [-20 -10 0 10 20];
carrier_sweep_hz = [5e9 10e9 15e9];
pulse_count_sweep = [8 16 32 64];
comparison_tolerance = 1e-10;
max_pulse_count = 128;
max_sweep_cases = 7;
max_figure_groups = 6;
max_stored_numeric_values = 50000;

%% Validate controls before allocating slow-time arrays
positive_controls = [speed_of_light_mps carrier_frequency_hz ...
    pulse_repetition_frequency_hz pulse_count echo_amplitude ...
    max_pulse_count max_sweep_cases max_figure_groups ...
    max_stored_numeric_values comparison_tolerance];
assert(all(isfinite(positive_controls)) && all(positive_controls > 0));
assert(isfinite(random_seed) && random_seed == floor(random_seed) && ...
    random_seed == 3601);
assert(isfinite(baseline_velocity_mps));
assert(isfinite(initial_phase_deg));
assert(isfinite(signal_to_noise_ratio_db));
integer_controls = [pulse_count pulse_count_sweep max_pulse_count ...
    max_sweep_cases max_figure_groups max_stored_numeric_values];
assert(all(integer_controls == floor(integer_controls)));
assert(pulse_count >= 4 && pulse_count <= max_pulse_count && ...
    mod(pulse_count, 2) == 0);
assert(numel(velocity_sweep_mps) >= 3 && ...
    numel(velocity_sweep_mps) <= max_sweep_cases && ...
    all(isfinite(velocity_sweep_mps)) && ...
    all(diff(velocity_sweep_mps) > 0) && ...
    any(velocity_sweep_mps < 0) && any(velocity_sweep_mps > 0));
assert(numel(carrier_sweep_hz) >= 2 && ...
    numel(carrier_sweep_hz) <= max_sweep_cases && ...
    all(isfinite(carrier_sweep_hz)) && ...
    all(carrier_sweep_hz > 0) && all(diff(carrier_sweep_hz) > 0) && ...
    any(carrier_sweep_hz == carrier_frequency_hz));
assert(numel(pulse_count_sweep) >= 2 && ...
    numel(pulse_count_sweep) <= max_sweep_cases && ...
    all(pulse_count_sweep >= 4) && ...
    all(pulse_count_sweep <= max_pulse_count) && ...
    all(mod(pulse_count_sweep, 2) == 0) && ...
    all(diff(pulse_count_sweep) > 0) && ...
    any(pulse_count_sweep == pulse_count));
estimated_stored_numeric_values = 30*max_pulse_count + ...
    20*(numel(velocity_sweep_mps)+numel(carrier_sweep_hz)+...
    numel(pulse_count_sweep));
assert(estimated_stored_numeric_values <= max_stored_numeric_values);
assert(max_figure_groups >= 6);

%% Baseline: build one coherent range-bin sample across pulses
wavelength_m = speed_of_light_mps/carrier_frequency_hz;
pulse_repetition_interval_s = 1/pulse_repetition_frequency_hz;
doppler_frequency_hz = 2*baseline_velocity_mps/wavelength_m;
phase_increment_rad = 2*pi*doppler_frequency_hz*...
    pulse_repetition_interval_s;
unambiguous_doppler_hz = pulse_repetition_frequency_hz/2;
unambiguous_velocity_mps = wavelength_m*...
    pulse_repetition_frequency_hz/4;
assert(abs(doppler_frequency_hz) < unambiguous_doppler_hz);
assert(abs(phase_increment_rad) < pi);

pulse_index = 0:pulse_count-1;
slow_time_s = pulse_index*pulse_repetition_interval_s;
initial_phase_rad = initial_phase_deg*pi/180;
clean_echo = echo_amplitude*exp(1j*(initial_phase_rad+...
    2*pi*doppler_frequency_hz*slow_time_s));
noise_rms = echo_amplitude*10^(-signal_to_noise_ratio_db/20);
private_stream = RandStream('mt19937ar', 'Seed', random_seed);
complex_noise = noise_rms/sqrt(2)*(...
    randn(private_stream, 1, pulse_count)+...
    1j*randn(private_stream, 1, pulse_count));
received_echo = clean_echo+complex_noise;

% Adjacent conjugate products expose the mean phase step directly.
adjacent_products = conj(received_echo(1:end-1)).*...
    received_echo(2:end);
estimated_phase_increment_rad = angle(sum(adjacent_products));
phase_estimated_doppler_hz = estimated_phase_increment_rad*...
    pulse_repetition_frequency_hz/(2*pi);
phase_estimated_velocity_mps = wavelength_m*...
    phase_estimated_doppler_hz/2;

% An explicit least-squares slope connects unwrapped phase to Doppler.
unwrapped_phase_rad = unwrap(angle(received_echo));
centered_time_s = slow_time_s-mean(slow_time_s);
centered_phase_rad = unwrapped_phase_rad-mean(unwrapped_phase_rad);
phase_slope_rad_per_s = sum(centered_time_s.*centered_phase_rad)/...
    sum(centered_time_s.^2);
slope_estimated_doppler_hz = phase_slope_rad_per_s/(2*pi);
slope_estimated_velocity_mps = wavelength_m*...
    slope_estimated_doppler_hz/2;

% The slow-time DFT is evaluated explicitly on the PRF-spaced frequency grid.
slow_time_window = 0.5-0.5*cos(2*pi*pulse_index/(pulse_count-1));
doppler_spectrum = fftshift(fft(received_echo.*slow_time_window, ...
    pulse_count));
doppler_axis_hz = (-pulse_count/2:pulse_count/2-1)*...
    pulse_repetition_frequency_hz/pulse_count;
doppler_magnitude_db = 20*log10(abs(doppler_spectrum)/...
    max(abs(doppler_spectrum))+eps);
[~, peak_index] = max(abs(doppler_spectrum));
fft_peak_doppler_hz = doppler_axis_hz(peak_index);
fft_peak_velocity_mps = wavelength_m*fft_peak_doppler_hz/2;
doppler_bin_spacing_hz = pulse_repetition_frequency_hz/pulse_count;
velocity_bin_spacing_mps = wavelength_m*doppler_bin_spacing_hz/2;

assert(abs(phase_estimated_doppler_hz-doppler_frequency_hz) < ...
    doppler_bin_spacing_hz/2);
assert(abs(slope_estimated_doppler_hz-doppler_frequency_hz) < ...
    doppler_bin_spacing_hz/2);
assert(abs(fft_peak_doppler_hz-doppler_frequency_hz) <= ...
    doppler_bin_spacing_hz/2+comparison_tolerance);

figure('Name', 'P36 slow-time complex echo', 'Tag', 'P36');
subplot(2, 1, 1);
plot(pulse_index, real(received_echo), 'o-', 'LineWidth', 1.1);
hold on;
plot(pulse_index, imag(received_echo), 's-', 'LineWidth', 1.1);
grid on;
xlabel('Pulse index');
ylabel('Range-bin amplitude (normalized)');
title('I and Q rotate coherently from pulse to pulse');
legend('I', 'Q', 'Location', 'best');
subplot(2, 1, 2);
plot(real(received_echo), imag(received_echo), 'o-', 'LineWidth', 1.1);
grid on;
axis equal;
xlabel('In-phase I (normalized)');
ylabel('Quadrature Q (normalized)');
title('Positive closing velocity rotates counterclockwise');

figure('Name', 'P36 phase slope and Doppler FFT', 'Tag', 'P36');
subplot(2, 1, 1);
plot(pulse_index, unwrapped_phase_rad, 'o-', 'LineWidth', 1.1);
hold on;
plot(pulse_index, initial_phase_rad+phase_increment_rad*pulse_index, ...
    '--', 'LineWidth', 1.2);
grid on;
xlabel('Pulse index');
ylabel('Unwrapped phase (rad)');
title(sprintf('Phase step %.3f rad/pulse', phase_increment_rad));
legend('Noisy measurement', 'Ideal progression', 'Location', 'best');
subplot(2, 1, 2);
plot(doppler_axis_hz, doppler_magnitude_db, 'LineWidth', 1.2);
hold on;
plot(fft_peak_doppler_hz, doppler_magnitude_db(peak_index), ...
    'ro', 'LineWidth', 1.4);
grid on;
xlabel('Doppler frequency (Hz)');
ylabel('Normalized magnitude (dB)');
title(sprintf('Slow-time FFT peak %.1f Hz (%.2f m/s)', ...
    fft_peak_doppler_hz, fft_peak_velocity_mps));
ylim([-60 3]);

%% Sweep 1: change only signed radial velocity
velocity_sweep_doppler_hz = 2*velocity_sweep_mps/wavelength_m;
velocity_sweep_phase_increment_rad = 2*pi*...
    velocity_sweep_doppler_hz/pulse_repetition_frequency_hz;
assert(all(abs(velocity_sweep_doppler_hz) < unambiguous_doppler_hz));
assert(all(diff(velocity_sweep_doppler_hz) > 0));
assert(all(sign(velocity_sweep_doppler_hz) == ...
    sign(velocity_sweep_mps)));

figure('Name', 'P36 velocity and direction sweep', 'Tag', 'P36');
subplot(1, 2, 1);
plot(velocity_sweep_mps, velocity_sweep_doppler_hz, ...
    'o-', 'LineWidth', 1.2);
grid on;
xlabel('Radial velocity (m/s; + approaching)');
ylabel('Doppler frequency (Hz)');
title('Approach and recession reverse Doppler sign');
subplot(1, 2, 2);
plot(velocity_sweep_mps, velocity_sweep_phase_increment_rad, ...
    'o-', 'LineWidth', 1.2);
grid on;
xlabel('Radial velocity (m/s; + approaching)');
ylabel('Phase increment (rad/pulse)');
title('Faster radial motion rotates farther each PRI');

%% Sweep 2: change only carrier frequency at fixed velocity
carrier_sweep_wavelength_m = speed_of_light_mps./carrier_sweep_hz;
carrier_sweep_doppler_hz = 2*baseline_velocity_mps./...
    carrier_sweep_wavelength_m;
carrier_sweep_phase_increment_rad = 2*pi*...
    carrier_sweep_doppler_hz/pulse_repetition_frequency_hz;
carrier_sweep_unambiguous_velocity_mps = ...
    carrier_sweep_wavelength_m*pulse_repetition_frequency_hz/4;
assert(all(abs(carrier_sweep_doppler_hz) < unambiguous_doppler_hz));
assert(all(diff(carrier_sweep_doppler_hz) > 0));
assert(all(diff(carrier_sweep_unambiguous_velocity_mps) < 0));

figure('Name', 'P36 carrier-frequency sweep', 'Tag', 'P36');
subplot(1, 2, 1);
plot(carrier_sweep_hz/1e9, carrier_sweep_phase_increment_rad, ...
    'o-', 'LineWidth', 1.2);
grid on;
xlabel('Carrier frequency (GHz)');
ylabel('Phase increment (rad/pulse)');
title(sprintf('Same %.1f m/s target, greater phase sensitivity', ...
    baseline_velocity_mps));
subplot(1, 2, 2);
plot(carrier_sweep_hz/1e9, carrier_sweep_unambiguous_velocity_mps, ...
    'o-', 'LineWidth', 1.2);
grid on;
xlabel('Carrier frequency (GHz)');
ylabel('Unambiguous speed magnitude (m/s)');
title('Higher carrier reduces the fixed-PRF velocity interval');

%% Sweep 3: change only pulse count at fixed PRF and velocity
pulse_count_bin_spacing_hz = pulse_repetition_frequency_hz./...
    pulse_count_sweep;
pulse_count_velocity_spacing_mps = wavelength_m*...
    pulse_count_bin_spacing_hz/2;
pulse_count_peak_hz = zeros(size(pulse_count_sweep));
for sweep_index = 1:numel(pulse_count_sweep)
    candidate_pulse_count = pulse_count_sweep(sweep_index);
    candidate_index = 0:candidate_pulse_count-1;
    candidate_echo = echo_amplitude*exp(1j*(initial_phase_rad+...
        2*pi*doppler_frequency_hz*candidate_index/...
        pulse_repetition_frequency_hz));
    candidate_window = 0.5-0.5*cos(2*pi*candidate_index/...
        (candidate_pulse_count-1));
    candidate_spectrum = fftshift(fft(candidate_echo.*...
        candidate_window, candidate_pulse_count));
    candidate_axis_hz = (-candidate_pulse_count/2:...
        candidate_pulse_count/2-1)*pulse_repetition_frequency_hz/...
        candidate_pulse_count;
    [~, candidate_peak_index] = max(abs(candidate_spectrum));
    pulse_count_peak_hz(sweep_index) = ...
        candidate_axis_hz(candidate_peak_index);
    assert(abs(pulse_count_peak_hz(sweep_index)-...
        doppler_frequency_hz) <= ...
        pulse_count_bin_spacing_hz(sweep_index)/2+...
        comparison_tolerance);
end
assert(all(diff(pulse_count_bin_spacing_hz) < 0));

figure('Name', 'P36 pulse-count sweep', 'Tag', 'P36');
subplot(1, 2, 1);
plot(pulse_count_sweep, pulse_count_bin_spacing_hz, ...
    'o-', 'LineWidth', 1.2);
grid on;
xlabel('Coherent pulse count');
ylabel('Doppler-bin spacing (Hz)');
title('More pulses refine the slow-time frequency grid');
subplot(1, 2, 2);
plot(pulse_count_sweep, pulse_count_velocity_spacing_mps, ...
    'o-', 'LineWidth', 1.2);
grid on;
xlabel('Coherent pulse count');
ylabel('Velocity-bin spacing (m/s)');
title('Longer coherent dwell narrows velocity bins');

%% Intentionally broken case: discard complex phase before Doppler processing
broken_echo = abs(received_echo);
broken_adjacent_products = conj(broken_echo(1:end-1)).*...
    broken_echo(2:end);
broken_phase_increment_rad = angle(sum(broken_adjacent_products));
broken_spectrum = fftshift(fft(broken_echo.*slow_time_window, pulse_count));
[~, broken_peak_index] = max(abs(broken_spectrum));
broken_peak_doppler_hz = doppler_axis_hz(broken_peak_index);
broken_velocity_mps = wavelength_m*broken_peak_doppler_hz/2;
broken_model_valid = false;
assert(abs(broken_phase_increment_rad) <= comparison_tolerance);
assert(broken_peak_doppler_hz == 0);

%% Recovery: restore coherent complex samples and private-seed noise exactly
recovered_stream = RandStream('mt19937ar', 'Seed', random_seed);
recovered_noise = noise_rms/sqrt(2)*(...
    randn(recovered_stream, 1, pulse_count)+...
    1j*randn(recovered_stream, 1, pulse_count));
recovered_echo = clean_echo+recovered_noise;
recovered_adjacent_products = conj(recovered_echo(1:end-1)).*...
    recovered_echo(2:end);
recovered_phase_increment_rad = angle(sum(recovered_adjacent_products));
recovered_doppler_hz = recovered_phase_increment_rad*...
    pulse_repetition_frequency_hz/(2*pi);
recovered_velocity_mps = wavelength_m*recovered_doppler_hz/2;
recovered_model_valid = true;
assert(isequal(recovered_echo, received_echo));
assert(abs(recovered_phase_increment_rad-...
    estimated_phase_increment_rad) <= comparison_tolerance);

figure('Name', 'P36 coherence failure and recovery', 'Tag', 'P36');
subplot(1, 2, 1);
plot(doppler_axis_hz, doppler_magnitude_db, 'LineWidth', 1.2);
hold on;
broken_magnitude_db = 20*log10(abs(broken_spectrum)/...
    max(abs(broken_spectrum))+eps);
plot(doppler_axis_hz, broken_magnitude_db, '--', 'LineWidth', 1.2);
grid on;
xlabel('Doppler frequency (Hz)');
ylabel('Normalized magnitude (dB)');
title('Magnitude-only processing moves energy to zero Doppler');
legend('Coherent complex echo', 'Broken magnitude-only echo', ...
    'Location', 'best');
ylim([-60 3]);
subplot(1, 2, 2);
plot([1 2 3], [phase_estimated_velocity_mps broken_velocity_mps ...
    recovered_velocity_mps], 'o-', 'LineWidth', 1.2);
grid on;
xlim([0.7 3.3]);
set(gca, 'XTick', [1 2 3], 'XTickLabel', ...
    {'Coherent', 'Magnitude only', 'Recovered'});
ylabel('Estimated radial velocity (m/s)');
title('Complex pulse-to-pulse phase carries signed velocity');

%% Publish concise metrics for inspection and later lessons
results = struct();
results.random_seed = random_seed;
results.sign_convention = 'positive radial velocity means approaching';
results.wavelength_m = wavelength_m;
results.pulse_repetition_interval_s = pulse_repetition_interval_s;
results.true_velocity_mps = baseline_velocity_mps;
results.true_doppler_hz = doppler_frequency_hz;
results.true_phase_increment_rad = phase_increment_rad;
results.phase_estimated_doppler_hz = phase_estimated_doppler_hz;
results.phase_estimated_velocity_mps = phase_estimated_velocity_mps;
results.slope_estimated_doppler_hz = slope_estimated_doppler_hz;
results.slope_estimated_velocity_mps = slope_estimated_velocity_mps;
results.fft_peak_doppler_hz = fft_peak_doppler_hz;
results.fft_peak_velocity_mps = fft_peak_velocity_mps;
results.doppler_bin_spacing_hz = doppler_bin_spacing_hz;
results.velocity_bin_spacing_mps = velocity_bin_spacing_mps;
results.unambiguous_doppler_hz = unambiguous_doppler_hz;
results.unambiguous_velocity_mps = unambiguous_velocity_mps;
results.velocity_sweep_mps = velocity_sweep_mps;
results.velocity_sweep_doppler_hz = velocity_sweep_doppler_hz;
results.carrier_sweep_hz = carrier_sweep_hz;
results.carrier_sweep_phase_increment_rad = ...
    carrier_sweep_phase_increment_rad;
results.pulse_count_sweep = pulse_count_sweep;
results.pulse_count_bin_spacing_hz = pulse_count_bin_spacing_hz;
results.broken_phase_increment_rad = broken_phase_increment_rad;
results.broken_peak_doppler_hz = broken_peak_doppler_hz;
results.broken_model_valid = broken_model_valid;
results.recovered_velocity_mps = recovered_velocity_mps;
results.recovered_model_valid = recovered_model_valid;
results.estimated_stored_numeric_values = ...
    estimated_stored_numeric_values;

fprintf('\nP36 baseline: pulse-to-pulse Doppler\n');
fprintf('  Sign convention: + velocity is approaching\n');
fprintf('  Carrier / wavelength: %.3f GHz / %.6f m\n', ...
    carrier_frequency_hz/1e9, wavelength_m);
fprintf('  PRF / PRI: %.3f kHz / %.3f microseconds\n', ...
    pulse_repetition_frequency_hz/1e3, ...
    pulse_repetition_interval_s*1e6);
fprintf('  True velocity / Doppler: %.3f m/s / %.3f Hz\n', ...
    baseline_velocity_mps, doppler_frequency_hz);
fprintf('  Ideal / measured phase step: %.6f / %.6f rad/pulse\n', ...
    phase_increment_rad, estimated_phase_increment_rad);
fprintf('  Phase estimate: %.3f Hz, %.3f m/s\n', ...
    phase_estimated_doppler_hz, phase_estimated_velocity_mps);
fprintf('  FFT peak: %.3f Hz, %.3f m/s; bin spacing %.3f Hz\n', ...
    fft_peak_doppler_hz, fft_peak_velocity_mps, ...
    doppler_bin_spacing_hz);
fprintf('  Unambiguous interval: [%.1f, %.1f) Hz, |v| < %.3f m/s\n', ...
    -unambiguous_doppler_hz, unambiguous_doppler_hz, ...
    unambiguous_velocity_mps);
fprintf('  Broken / recovered valid: %d / %d\n', ...
    broken_model_valid, recovered_model_valid);
