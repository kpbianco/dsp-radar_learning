%% P84: Run the End-to-End Radar Processing Capstone
% Can I trace a target from waveform generation through detection and tracking without treating any stage as a black box?
% Base MATLAB R2016b+; deterministic synthetic data; no toolbox or external data.

old_p84_figures = findall(0, 'Type', 'figure', 'Tag', 'P84');
if ~isempty(old_p84_figures)
    close(old_p84_figures);
end
clear old_p84_figures p84_results
p84_results = run_p84_experiment();

function p84_results = run_p84_experiment()
%% Visible controls and immutable resource ceilings
controls = struct();
controls.seed = 8401;
controls.c_mps = 3.0e8;
controls.carrier_hz = 10.0e9;
controls.sample_rate_hz = 4.0e6;
controls.bandwidth_hz = 2.0e6;
controls.pulse_width_s = 8.0e-6;
controls.fast_time_samples = 128;
controls.pulses = 32;
controls.prf_hz = controls.sample_rate_hz/controls.fast_time_samples;
controls.scan_interval_s = 1.0;
controls.scans = 8;
controls.target_initial_range_m = [900 1650 2550 2625];
controls.target_approach_speed_mps = [0 30 -15 -15];
controls.target_voltage = [1.8 2.2 3.0 0.22];
controls.clutter_edge_range_m = 1800;
controls.quiet_clutter_voltage = 0.015;
controls.high_clutter_voltage = 0.20;
controls.noise_voltage = 0.18;
controls.receiver_image_coefficient = 0.12;
controls.receiver_dc = 0.04 + 0.03j;
controls.spur_range_m = 3900;
controls.spur_doppler_bin = 5;
controls.spur_voltage = 0.85;
controls.cfar_pfa = 1.0e-3;
controls.training_range = 4;
controls.guard_range = 2;
controls.training_doppler = 3;
controls.guard_doppler = 1;
controls.minimum_cluster_cells = 1;
controls.tracker_alpha = 0.65;
controls.tracker_beta = 0.18;
controls.tracker_range_gate_m = 225;
controls.tracker_velocity_gate_mps = 35;
controls.maximum_coast_scans = 2;
controls.taper_sweep = [0 0.5 1.0];
controls.pfa_sweep = [1.0e-4 1.0e-3 1.0e-2];
controls.display_floor_db = -45;
controls.max_fast_time_samples = 256;
controls.max_pulses = 64;
controls.max_scans = 12;
controls.max_targets = 6;
controls.max_sweep_cases = 4;
controls.max_map_evaluations = 20;
controls.max_cfar_training_visits = 1.2e7;
controls.max_private_values = 20000;
controls.max_working_values = 500000;
controls.max_reports_per_scan = 50;
controls.max_association_pairs = 10000;
controls.max_figures = 6;
resource_plan = validate_controls(controls);

wavelength_m = controls.c_mps/controls.carrier_hz;
range_sample_spacing_m = controls.c_mps/(2*controls.sample_rate_hz);
nominal_range_resolution_m = controls.c_mps/(2*controls.bandwidth_hz);
velocity_bin_spacing_mps = wavelength_m*controls.prf_hz/(2*controls.pulses);
unambiguous_range_m = controls.c_mps/(2*controls.prf_hz);
unambiguous_speed_mps = wavelength_m*controls.prf_hz/4;

fprintf('\nP84 baseline chain\n');
fprintf('Range sample spacing %.2f m; nominal range resolution %.2f m\n', ...
    range_sample_spacing_m, nominal_range_resolution_m);
fprintf('Velocity-bin spacing %.2f m/s; unambiguous limits %.1f m and +/-%.1f m/s\n', ...
    velocity_bin_spacing_mps, unambiguous_range_m, unambiguous_speed_mps);

%% Stage 1: form the explicit unit-energy LFM pulse
[transmit_pulse, transmit_time_s, instantaneous_frequency_hz] = ...
    make_lfm(controls.bandwidth_hz, controls);

figure('Name', 'P84 stage 1 - waveform', 'Tag', 'P84', 'Color', 'w');
subplot(2,1,1);
plot(1e6*transmit_time_s, real(transmit_pulse), 'LineWidth', 1.2);
grid on;
xlabel('Time from pulse center (microseconds)');
ylabel('In-phase voltage (normalized)');
title('Stage 1: explicit complex-baseband LFM pulse');
subplot(2,1,2);
plot(1e6*transmit_time_s, instantaneous_frequency_hz/1e6, ...
    'LineWidth', 1.4);
grid on;
xlabel('Time from pulse center (microseconds)');
ylabel('Instantaneous frequency (MHz)');
title('Phase slope sweeps the configured bandwidth');

%% Stages 2 and 3: scene echoes, clutter/noise, and receiver calibration
baseline_clock = tic;
[measured_cube, truth, scene_parts] = synthesize_scan( ...
    controls, transmit_pulse, 1);
retained_measured_cube = measured_cube;
corrected_cube = correct_receiver(measured_cube, controls);
retained_corrected_cube = corrected_cube;

range_axis_m = (0:controls.fast_time_samples-1)*range_sample_spacing_m;
figure('Name', 'P84 stages 2 and 3 - receiver', 'Tag', 'P84', 'Color', 'w');
subplot(2,1,1);
plot(range_axis_m/1000, abs(measured_cube(:,1)), 'Color', [0.85 0.33 0.10]);
hold on;
plot(range_axis_m/1000, abs(corrected_cube(:,1)), 'Color', [0 0.45 0.74]);
grid on;
xlabel('Apparent fast-time range (km)');
ylabel('Receiver voltage magnitude');
legend('Measured with image/DC', 'Calibrated', 'Location', 'best');
title('Stages 2-3: imperfections are added and inverted explicitly');
subplot(2,1,2);
plot(real(measured_cube(:)), imag(measured_cube(:)), '.', ...
    'Color', [0.85 0.33 0.10], 'MarkerSize', 3);
hold on;
plot(real(corrected_cube(:)), imag(corrected_cube(:)), '.', ...
    'Color', [0 0.45 0.74], 'MarkerSize', 3);
axis equal;
grid on;
xlabel('I voltage');
ylabel('Q voltage');
title('The receiver image term shears the complex samples');

%% Stages 4-7: matched filter, range-Doppler, CFAR, and clustering
baseline = process_record(corrected_cube, transmit_pulse, controls, ...
    controls.cfar_pfa, 0, false);
baseline_runtime_s = toc(baseline_clock);
baseline_score = score_reports(baseline.reports, baseline.detection, ...
    baseline.testable, truth, baseline.range_axis_m, ...
    baseline.velocity_axis_mps, controls);

quiet_rows = baseline.range_axis_m < controls.clutter_edge_range_m-300 & ...
    baseline.range_axis_m > 300;
quiet_power = baseline.power(quiet_rows, :);
fixed_threshold_power = -log(controls.cfar_pfa)*median(quiet_power(:))/log(2);
fixed_detection = baseline.testable & baseline.power > fixed_threshold_power;
fixed_reports = cluster_detections(fixed_detection, baseline.power, ...
    fixed_threshold_power*ones(size(baseline.power)), baseline.range_axis_m, ...
    baseline.velocity_axis_mps, controls.minimum_cluster_cells);
fixed_score = score_reports(fixed_reports, fixed_detection, ...
    baseline.testable, truth, baseline.range_axis_m, ...
    baseline.velocity_axis_mps, controls);

edge_region = baseline.testable & repmat( ...
    baseline.range_axis_m(:) >= controls.clutter_edge_range_m, 1, controls.pulses);
assert(sum(fixed_detection(edge_region)) > sum(baseline.detection(edge_region)), ...
    'P84:BrokenFixedThresholdNotVisible', ...
    'The quiet-side fixed threshold must overspend detections at the clutter edge.');

figure('Name', 'P84 stages 4 and 5 - range compression and Doppler', ...
    'Tag', 'P84', 'Color', 'w');
subplot(2,1,1);
plot(baseline.range_axis_m/1000, ...
    20*log10(max(abs(baseline.matched(:,1)), eps)), 'LineWidth', 1.2);
hold on;
for target_index = 1:numel(truth.range_m)
    plot(truth.range_m(target_index)/1000, ...
        20*log10(max(abs(baseline.matched(truth.range_index(target_index),1)),eps)), ...
        'ko', 'MarkerSize', 5);
end
grid on;
xlabel('Range (km)');
ylabel('Compressed voltage (dB re 1)');
title('Stage 4: conjugate time reversal concentrates echo energy');
subplot(2,1,2);
show_power_map(baseline.velocity_axis_mps, baseline.range_axis_m, ...
    baseline.power, controls.display_floor_db, ...
    'Stage 5: signed range-Doppler power');

figure('Name', 'P84 stages 6 and 7 - detection and reports', ...
    'Tag', 'P84', 'Color', 'w');
subplot(1,2,1);
show_detection_map(baseline, truth, ...
    sprintf('CA-CFAR: Pd %.2f, empirical false-cell rate %.3g', ...
    baseline_score.pd, baseline_score.empirical_false_cell_rate));
subplot(1,2,2);
fixed_view = baseline;
fixed_view.detection = fixed_detection;
fixed_view.reports = fixed_reports;
show_detection_map(fixed_view, truth, ...
    sprintf('Broken fixed threshold: %d false reports', fixed_score.false_reports));

%% Stage 8: repeat scans, gate reports, coast through a physical fade, and track
report_history = cell(1, controls.scans);
truth_history_m = zeros(1, controls.scans);
all_detection_opportunities = 0;
all_detection_matches = 0;
all_false_reports = 0;
for scan_index = 1:controls.scans
    [scan_measured, scan_truth] = synthesize_scan( ...
        controls, transmit_pulse, scan_index);
    scan_corrected = correct_receiver(scan_measured, controls);
    scan_product = process_record(scan_corrected, transmit_pulse, ...
        controls, controls.cfar_pfa, 0, false);
    scan_score = score_reports(scan_product.reports, ...
        scan_product.detection, scan_product.testable, scan_truth, ...
        scan_product.range_axis_m, scan_product.velocity_axis_mps, controls);
    report_history{scan_index} = scan_product.reports;
    truth_history_m(scan_index) = scan_truth.range_m(2);
    all_detection_opportunities = all_detection_opportunities+scan_score.opportunities;
    all_detection_matches = all_detection_matches+scan_score.matches;
    all_false_reports = all_false_reports+scan_score.false_reports;
end
track = alpha_beta_track(report_history, controls, truth_history_m);
track_rmse_m = sqrt(mean((track.range_m-truth_history_m).^2));
sequence_pd = all_detection_matches/max(all_detection_opportunities,1);

assert(~track.updated(4) && track.coast_count(4) >= 1, ...
    'P84:FadeMustCreateCoast', ...
    'The modeled moving-target fade on scan 4 must create a tracker coast.');

figure('Name', 'P84 stage 8 - tracking', 'Tag', 'P84', 'Color', 'w');
subplot(2,1,1);
plot(1:controls.scans, truth_history_m/1000, 'k-', 'LineWidth', 1.8);
hold on;
plot(1:controls.scans, track.range_m/1000, 'o-', ...
    'Color', [0 0.45 0.74], 'LineWidth', 1.5);
plot(find(~track.updated), track.range_m(~track.updated)/1000, ...
    'rs', 'MarkerSize', 8, 'LineWidth', 1.2);
grid on;
xlabel('Scan number');
ylabel('Range (km)');
legend('Moving-target truth (scoring only)', 'Alpha-beta estimate', ...
    'Coasted scan', 'Location', 'best');
title(sprintf('Stage 8: gated updates and coast; range RMSE %.1f m', track_rmse_m));
subplot(2,1,2);
stairs(1:controls.scans, track.updated, 'LineWidth', 1.5);
hold on;
stairs(1:controls.scans, track.coast_count, '--', 'LineWidth', 1.4);
grid on;
xlabel('Scan number');
ylabel('Update flag / coast count');
legend('Measurement update', 'Consecutive coasts', 'Location', 'best');
title('The scan-4 miss is created in the echo amplitude, not after detection');

%% Sweep 1: change only the explicit matched-filter taper on retained data
taper_case_count = numel(controls.taper_sweep);
taper_width_samples = zeros(1, taper_case_count);
taper_weak_to_strong_db = zeros(1, taper_case_count);
for case_index = 1:taper_case_count
    case_product = process_record(retained_corrected_cube, transmit_pulse, ...
        controls, controls.cfar_pfa, controls.taper_sweep(case_index), false);
    taper_width_samples(case_index) = response_width_samples( ...
        case_product.power(:, truth.doppler_index(3)), truth.range_index(3));
    weak_power = case_product.power(truth.range_index(4), truth.doppler_index(4));
    strong_power = case_product.power(truth.range_index(3), truth.doppler_index(3));
    taper_weak_to_strong_db(case_index) = 10*log10(max(weak_power,eps)/ ...
        max(strong_power,eps));
end

%% Sweep 2: change only requested Pfa on the retained range-Doppler map
pfa_case_count = numel(controls.pfa_sweep);
pfa_detection_cells = zeros(1, pfa_case_count);
pfa_false_cells = zeros(1, pfa_case_count);
pfa_report_count = zeros(1, pfa_case_count);
for case_index = 1:pfa_case_count
    [case_threshold, case_testable, case_detection] = ca_cfar_2d( ...
        baseline.power, controls.pfa_sweep(case_index), controls);
    case_reports = cluster_detections(case_detection, baseline.power, ...
        case_threshold, baseline.range_axis_m, baseline.velocity_axis_mps, ...
        controls.minimum_cluster_cells);
    case_score = score_reports(case_reports, case_detection, case_testable, ...
        truth, baseline.range_axis_m, baseline.velocity_axis_mps, controls);
    pfa_detection_cells(case_index) = sum(case_detection(:));
    pfa_false_cells(case_index) = case_score.false_cells;
    pfa_report_count(case_index) = numel(case_reports);
end
assert(all(diff(pfa_detection_cells) >= 0) && all(diff(pfa_false_cells) >= 0), ...
    'P84:PfaSweepNesting', ...
    'Relaxing requested Pfa must not remove a threshold crossing on fixed data.');

sweep_figure = figure('Name', 'P84 sweeps, broken case, and recovery', ...
    'Tag', 'P84', 'Color', 'w');
subplot(2,2,1);
yyaxis left;
plot(controls.taper_sweep, taper_width_samples, 'o-', 'LineWidth', 1.5);
ylabel('-3 dB response width (range samples)');
yyaxis right;
plot(controls.taper_sweep, taper_weak_to_strong_db, 's--', 'LineWidth', 1.5);
ylabel('Weak/strong cell power (dB)');
grid on;
xlabel('Cosine taper fraction');
title('Sweep 1: sidelobe control trades width and weak visibility');
subplot(2,2,2);
semilogx(controls.pfa_sweep, pfa_false_cells, 'o-', 'LineWidth', 1.5);
hold on;
semilogx(controls.pfa_sweep, pfa_report_count, 's--', 'LineWidth', 1.5);
grid on;
xlabel('Requested homogeneous-cell Pfa');
ylabel('Count on identical retained map');
legend('False threshold cells', 'Clustered reports', 'Location', 'best');
title('Sweep 2: detector sensitivity changes misses and false alarms');

%% Intentionally broken case: remove conjugation from the matched replica
broken = process_record(retained_corrected_cube, transmit_pulse, controls, ...
    controls.cfar_pfa, 0, true);
recovered = process_record(retained_corrected_cube, transmit_pulse, controls, ...
    controls.cfar_pfa, 0, false);
recovery_exact = isequal(recovered.matched, baseline.matched) && ...
    isequal(recovered.power, baseline.power) && ...
    isequal(recovered.detection, baseline.detection) && ...
    isequaln(recovered.threshold, baseline.threshold);
assert(recovery_exact, 'P84:RecoveryMustBeExact', ...
    'The retained calibrated samples must reproduce every baseline processing cell.');

correct_peak = max(baseline.power(:));
broken_peak = max(broken.power(:));
assert(broken_peak < correct_peak, 'P84:WrongReplicaMustLoseCompressionGain', ...
    'The wrong LFM replica must reduce the strongest compressed-map peak.');

figure(sweep_figure);
subplot(2,2,3);
show_power_map(broken.velocity_axis_mps, broken.range_axis_m, broken.power, ...
    controls.display_floor_db, 'Broken: no conjugation');
subplot(2,2,4);
show_power_map(baseline.velocity_axis_mps, baseline.range_axis_m, baseline.power, ...
    controls.display_floor_db, sprintf('Recovered baseline: exact = %d', recovery_exact));

%% Traceable results and provenance ledger
provenance = struct( ...
    'stage', {'waveform','scene','receiver','matched_filter','range_doppler', ...
    'cfar','clustering','tracking'}, ...
    'input', {'visible controls','LFM pulse','scene voltage','calibrated voltage', ...
    'compressed range-pulse matrix','linear power map','threshold mask','reports'}, ...
    'output', {'unit-energy LFM','echoes + clutter + noise','calibrated I/Q', ...
    'range-compressed matrix','signed power map','eligible detections', ...
    'range/velocity reports','range state and coast flags'}, ...
    'units', {'voltage','voltage','voltage','voltage','power', ...
    'logical','m and m/s','m and m/s'});

p84_results = struct();
p84_results.controls = controls;
p84_results.resource_plan = resource_plan;
p84_results.range_sample_spacing_m = range_sample_spacing_m;
p84_results.nominal_range_resolution_m = nominal_range_resolution_m;
p84_results.velocity_bin_spacing_mps = velocity_bin_spacing_mps;
p84_results.baseline = baseline;
p84_results.baseline_score = baseline_score;
p84_results.fixed_score = fixed_score;
p84_results.sequence_pd = sequence_pd;
p84_results.sequence_false_reports = all_false_reports;
p84_results.track = track;
p84_results.track_rmse_m = track_rmse_m;
p84_results.baseline_runtime_s = baseline_runtime_s;
p84_results.taper_width_samples = taper_width_samples;
p84_results.taper_weak_to_strong_db = taper_weak_to_strong_db;
p84_results.pfa_detection_cells = pfa_detection_cells;
p84_results.pfa_false_cells = pfa_false_cells;
p84_results.pfa_report_count = pfa_report_count;
p84_results.broken_peak_loss_db = 10*log10(max(broken_peak,eps)/max(correct_peak,eps));
p84_results.recovery_exact = recovery_exact;
p84_results.provenance = provenance;
p84_results.retained_input_exact = isequal(retained_measured_cube, measured_cube) && ...
    isequal(retained_corrected_cube, corrected_cube);
p84_results.scene_parts = scene_parts;

fprintf('Baseline CA-CFAR: Pd %.3f, cell false-crossing rate %.4g, %d false reports\n', ...
    baseline_score.pd, baseline_score.empirical_false_cell_rate, ...
    baseline_score.false_reports);
fprintf('Broken fixed threshold: Pd %.3f, cell false-crossing rate %.4g, %d false reports\n', ...
    fixed_score.pd, fixed_score.empirical_false_cell_rate, fixed_score.false_reports);
fprintf('Eight-scan Pd %.3f; tracker range RMSE %.2f m; measured baseline runtime %.4f s\n', ...
    sequence_pd, track_rmse_m, baseline_runtime_s);
fprintf('Wrong-replica peak change %.2f dB; exact same-data recovery = %d\n', ...
    p84_results.broken_peak_loss_db, recovery_exact);
end

function plan = validate_controls(c)
control_names = fieldnames(c);
for control_index = 1:numel(control_names)
    control_value = c.(control_names{control_index});
    assert(isnumeric(control_value) && ~islogical(control_value), ...
        'P84:NumericControls', 'Every visible control must be nonlogical numeric data.');
end
finite_scalars = [c.seed c.c_mps c.carrier_hz c.sample_rate_hz ...
    c.bandwidth_hz c.pulse_width_s c.fast_time_samples c.pulses ...
    c.prf_hz c.scan_interval_s c.scans c.clutter_edge_range_m ...
    c.quiet_clutter_voltage c.high_clutter_voltage c.noise_voltage ...
    c.receiver_image_coefficient real(c.receiver_dc) imag(c.receiver_dc) ...
    c.spur_range_m c.spur_doppler_bin c.spur_voltage c.cfar_pfa ...
    c.training_range c.guard_range c.training_doppler c.guard_doppler ...
    c.minimum_cluster_cells c.tracker_alpha c.tracker_beta ...
    c.tracker_range_gate_m c.tracker_velocity_gate_mps ...
    c.maximum_coast_scans c.taper_sweep c.pfa_sweep c.display_floor_db ...
    c.max_fast_time_samples c.max_pulses c.max_scans c.max_targets ...
    c.max_sweep_cases c.max_map_evaluations c.max_cfar_training_visits ...
    c.max_private_values c.max_working_values c.max_reports_per_scan ...
    c.max_association_pairs ...
    c.max_figures c.target_initial_range_m c.target_approach_speed_mps ...
    c.target_voltage];
assert(~islogical(c.seed) && all(isfinite(finite_scalars)) && isreal(finite_scalars));
integer_controls = [c.seed c.fast_time_samples c.pulses c.scans ...
    c.spur_doppler_bin c.training_range c.guard_range c.training_doppler ...
    c.guard_doppler c.minimum_cluster_cells c.maximum_coast_scans ...
    c.max_fast_time_samples c.max_pulses c.max_scans c.max_targets ...
    c.max_sweep_cases c.max_map_evaluations c.max_cfar_training_visits ...
    c.max_private_values c.max_working_values c.max_reports_per_scan ...
    c.max_association_pairs c.max_figures];
assert(all(integer_controls == floor(integer_controls)) && all(integer_controls > 0));
assert(c.seed < 2147483647 && c.c_mps > 0 && c.carrier_hz > 0 && ...
    c.sample_rate_hz > 0 && c.bandwidth_hz > 0 && ...
    c.bandwidth_hz < c.sample_rate_hz && c.pulse_width_s > 0);
pulse_samples = c.pulse_width_s*c.sample_rate_hz;
assert(pulse_samples == floor(pulse_samples) && pulse_samples >= 2);
assert(c.prf_hz == c.sample_rate_hz/c.fast_time_samples && ...
    c.scan_interval_s > 0);
assert(c.fast_time_samples <= c.max_fast_time_samples && ...
    c.pulses <= c.max_pulses && mod(c.pulses,2) == 0 && ...
    c.scans >= 4 && c.scans <= c.max_scans);
assert(numel(c.target_initial_range_m) == numel(c.target_approach_speed_mps) && ...
    numel(c.target_initial_range_m) == numel(c.target_voltage) && ...
    numel(c.target_initial_range_m) >= 4 && ...
    numel(c.target_initial_range_m) <= c.max_targets);
assert(all(c.target_initial_range_m > 0) && all(c.target_voltage > 0) && ...
    all(diff(c.target_initial_range_m) > 0));
wavelength_m = c.c_mps/c.carrier_hz;
unambiguous_range_m = c.c_mps/(2*c.prf_hz);
unambiguous_speed_mps = wavelength_m*c.prf_hz/4;
last_ranges_m = c.target_initial_range_m- ...
    c.target_approach_speed_mps*(c.scans-1)*c.scan_interval_s;
assert(all(c.target_initial_range_m < unambiguous_range_m) && ...
    all(last_ranges_m > 0 & last_ranges_m < unambiguous_range_m));
assert(all(abs(c.target_approach_speed_mps) < unambiguous_speed_mps));
range_spacing_m = c.c_mps/(2*c.sample_rate_hz);
all_target_bins = round([c.target_initial_range_m last_ranges_m]/range_spacing_m)+1;
assert(all(all_target_bins >= 1 & all_target_bins <= c.fast_time_samples));
doppler_bins = round(2*c.target_approach_speed_mps/wavelength_m/ ...
    c.prf_hz*c.pulses);
assert(all(doppler_bins >= -c.pulses/2 & doppler_bins <= c.pulses/2-1));
assert(c.clutter_edge_range_m > 0 && c.clutter_edge_range_m < unambiguous_range_m && ...
    c.high_clutter_voltage > c.quiet_clutter_voltage && ...
    c.quiet_clutter_voltage >= 0 && c.noise_voltage > 0);
quiet_calibration_rows = (0:c.fast_time_samples-1)*range_spacing_m > 300 & ...
    (0:c.fast_time_samples-1)*range_spacing_m < c.clutter_edge_range_m-300;
assert(any(quiet_calibration_rows));
assert(abs(c.receiver_image_coefficient) < 0.5 && ...
    abs(1-c.receiver_image_coefficient^2) > 0.5);
assert(c.spur_range_m > c.clutter_edge_range_m && ...
    c.spur_range_m < unambiguous_range_m && ...
    abs(c.spur_doppler_bin) < c.pulses/2 && c.spur_voltage > 0);
assert(round(c.spur_range_m/range_spacing_m)+1 <= c.fast_time_samples);
assert(c.cfar_pfa >= 1e-6 && c.cfar_pfa <= 0.1 && ...
    all(c.pfa_sweep >= 1e-6 & c.pfa_sweep <= 0.1) && ...
    all(diff(c.pfa_sweep) > 0));
assert(all(c.taper_sweep >= 0 & c.taper_sweep <= 1) && ...
    all(diff(c.taper_sweep) > 0));
assert(numel(c.taper_sweep) >= 3 && numel(c.taper_sweep) <= c.max_sweep_cases && ...
    numel(c.pfa_sweep) >= 3 && numel(c.pfa_sweep) <= c.max_sweep_cases);
range_outer = c.training_range+c.guard_range;
doppler_outer = c.training_doppler+c.guard_doppler;
assert(2*range_outer+1 < c.fast_time_samples && ...
    2*doppler_outer+1 < c.pulses);
assert(c.tracker_alpha > 0 && c.tracker_alpha <= 1 && ...
    c.tracker_beta > 0 && c.tracker_beta <= 1 && ...
    c.tracker_range_gate_m > 0 && c.tracker_velocity_gate_mps > 0 && ...
    c.maximum_coast_scans < c.scans);
assert(c.display_floor_db <= -30 && c.display_floor_db >= -100);
assert(c.max_fast_time_samples == 256 && c.max_pulses == 64 && ...
    c.max_scans == 12 && c.max_targets == 6 && c.max_sweep_cases == 4 && ...
    c.max_map_evaluations == 20 && c.max_cfar_training_visits == 12000000 && ...
    c.max_private_values == 20000 && c.max_working_values == 500000 && ...
    c.max_reports_per_scan == 50 && ...
    c.max_association_pairs == 10000 && c.max_figures == 6);

training_cells = (2*range_outer+1)*(2*doppler_outer+1)- ...
    (2*c.guard_range+1)*(2*c.guard_doppler+1);
map_evaluations = c.scans+numel(c.taper_sweep)+numel(c.pfa_sweep)+3;
testable_cells = (c.fast_time_samples-2*range_outer)* ...
    (c.pulses-2*doppler_outer);
cfar_visits = map_evaluations*testable_cells*training_cells;
private_values = 2*c.fast_time_samples*c.pulses;
working_values = 45*c.fast_time_samples*c.pulses+10000;
association_pairs = c.scans*c.max_reports_per_scan;
assert(map_evaluations <= c.max_map_evaluations && ...
    cfar_visits <= c.max_cfar_training_visits && ...
    private_values <= c.max_private_values && ...
    working_values <= c.max_working_values && ...
    association_pairs <= c.max_association_pairs);
plan = struct('map_evaluations', map_evaluations, ...
    'cfar_training_visits', cfar_visits, 'private_values', private_values, ...
    'working_values', working_values, 'association_pairs', association_pairs, ...
    'figures', c.max_figures);
end

function [pulse, time_s, frequency_hz] = make_lfm(bandwidth_hz, c)
pulse_samples = round(c.pulse_width_s*c.sample_rate_hz);
time_s = ((0:pulse_samples-1)-(pulse_samples-1)/2)/c.sample_rate_hz;
chirp_rate_hz_per_s = bandwidth_hz/c.pulse_width_s;
pulse = exp(1j*pi*chirp_rate_hz_per_s*time_s.^2);
pulse = pulse/sqrt(sum(abs(pulse).^2));
frequency_hz = chirp_rate_hz_per_s*time_s;
end

function [measured, truth, parts] = synthesize_scan(c, pulse, scan_index)
fast_count = c.fast_time_samples;
pulse_count = c.pulses;
wavelength_m = c.c_mps/c.carrier_hz;
range_spacing_m = c.c_mps/(2*c.sample_rate_hz);
range_m = c.target_initial_range_m- ...
    c.target_approach_speed_mps*(scan_index-1)*c.scan_interval_s;
range_index = round(range_m/range_spacing_m)+1;
doppler_hz = 2*c.target_approach_speed_mps/wavelength_m;
doppler_index = round(doppler_hz/c.prf_hz*pulse_count)+pulse_count/2+1;
visibility = ones(size(range_m));
if scan_index == 4
    visibility(2) = 0;
end

clutter_noise = private_complex_noise(c.seed+10, fast_count, 1, ...
    c.max_private_values);
clutter_scale = c.quiet_clutter_voltage*ones(fast_count,1);
range_axis_m = (0:fast_count-1).'*range_spacing_m;
clutter_scale(range_axis_m >= c.clutter_edge_range_m) = ...
    c.high_clutter_voltage;
clutter_reflectivity = clutter_scale.*clutter_noise;

reflectivity = repmat(clutter_reflectivity, 1, pulse_count);
for target_index = 1:numel(range_m)
    for pulse_index = 1:pulse_count
        phase = exp(1j*2*pi*doppler_hz(target_index)* ...
            (pulse_index-1)/c.prf_hz);
        reflectivity(range_index(target_index),pulse_index) = ...
            reflectivity(range_index(target_index),pulse_index)+ ...
            visibility(target_index)*c.target_voltage(target_index)*phase;
    end
end

spur_index = round(c.spur_range_m/range_spacing_m)+1;
ideal = zeros(fast_count, pulse_count);
for pulse_index = 1:pulse_count
    echoed = conv(reflectivity(:,pulse_index), pulse(:));
    ideal(:,pulse_index) = echoed(1:fast_count);
end
echo_clutter = ideal;
% A coherent receiver spur is added after propagation, before receiver noise.
% It has matched-waveform shape but no target-truth entry.
for pulse_index = 1:pulse_count
    available = min(numel(pulse), fast_count-spur_index+1);
    spur_rows = spur_index:spur_index+available-1;
    ideal(spur_rows,pulse_index) = ideal(spur_rows,pulse_index)+ ...
        c.spur_voltage*pulse(1:available).'*exp(1j*2*pi*c.spur_doppler_bin* ...
        (pulse_index-1)/pulse_count);
end
receiver_noise = c.noise_voltage*private_complex_noise( ...
    c.seed+100+scan_index, fast_count, pulse_count, c.max_private_values);
with_noise = ideal+receiver_noise;
measured = with_noise+c.receiver_image_coefficient*conj(with_noise)+c.receiver_dc;

truth = struct('range_m', range_m, 'approach_speed_mps', ...
    c.target_approach_speed_mps, 'range_index', range_index, ...
    'doppler_index', doppler_index, 'visibility', visibility);
parts = struct('ideal_echo_clutter', echo_clutter, ...
    'receiver_spur', ideal-echo_clutter, 'receiver_noise', receiver_noise, ...
    'clutter_reflectivity', clutter_reflectivity, 'spur_index', spur_index, ...
    'visibility', visibility);
end

function corrected = correct_receiver(measured, c)
centered = measured-c.receiver_dc;
epsilon = c.receiver_image_coefficient;
corrected = (centered-epsilon*conj(centered))/(1-epsilon^2);
end

function product = process_record(received, pulse, c, requested_pfa, taper, wrong_replica)
pulse_count = c.pulses;
range_spacing_m = c.c_mps/(2*c.sample_rate_hz);
wavelength_m = c.c_mps/c.carrier_hz;
pulse_samples = numel(pulse);
cosine = 0.5-0.5*cos(2*pi*(0:pulse_samples-1)/(pulse_samples-1));
replica = pulse.*((1-taper)+taper*cosine);
replica = replica/sqrt(sum(abs(replica).^2));
if wrong_replica
    matched_impulse = fliplr(replica);
else
    matched_impulse = conj(fliplr(replica));
end

matched = zeros(size(received));
for pulse_index = 1:pulse_count
    full_output = conv(received(:,pulse_index), matched_impulse(:));
    matched(:,pulse_index) = full_output(pulse_samples: ...
        pulse_samples+c.fast_time_samples-1);
end
slow_time_window = 0.5-0.5*cos(2*pi*(0:pulse_count-1)/(pulse_count-1));
slow_time_gain = sum(slow_time_window);
range_doppler = fftshift(fft(matched.*repmat(slow_time_window, ...
    c.fast_time_samples, 1), [], 2), 2)/slow_time_gain;
power_map = abs(range_doppler).^2;
[threshold, testable, detection] = ca_cfar_2d(power_map, requested_pfa, c);
range_axis_m = (0:c.fast_time_samples-1)*range_spacing_m;
doppler_frequency_hz = (-pulse_count/2:pulse_count/2-1)*c.prf_hz/pulse_count;
velocity_axis_mps = wavelength_m*doppler_frequency_hz/2;
reports = cluster_detections(detection, power_map, threshold, ...
    range_axis_m, velocity_axis_mps, c.minimum_cluster_cells);
assert(numel(reports) <= c.max_reports_per_scan, 'P84:ReportCountBound', ...
    'Clustered report count exceeds the reviewed per-scan tracking bound.');
product = struct('matched', matched, 'range_doppler', range_doppler, ...
    'power', power_map, 'threshold', threshold, 'testable', testable, ...
    'detection', detection, 'reports', reports, 'range_axis_m', range_axis_m, ...
    'velocity_axis_mps', velocity_axis_mps);
end

function [threshold, testable, detection] = ca_cfar_2d(power_map, requested_pfa, c)
[range_count, doppler_count] = size(power_map);
range_outer = c.training_range+c.guard_range;
doppler_outer = c.training_doppler+c.guard_doppler;
range_offsets = -range_outer:range_outer;
doppler_offsets = -doppler_outer:doppler_outer;
training_mask = true(numel(range_offsets), numel(doppler_offsets));
training_mask(abs(range_offsets) <= c.guard_range, ...
    abs(doppler_offsets) <= c.guard_doppler) = false;
training_count = sum(training_mask(:));
alpha = training_count*(requested_pfa^(-1/training_count)-1);
threshold = nan(size(power_map));
testable = false(size(power_map));
for range_index = 1+range_outer:range_count-range_outer
    for doppler_index = 1+doppler_outer:doppler_count-doppler_outer
        local = power_map(range_index+range_offsets, ...
            doppler_index+doppler_offsets);
        threshold(range_index,doppler_index) = ...
            alpha*sum(local(training_mask))/training_count;
        testable(range_index,doppler_index) = true;
    end
end
detection = testable & power_map > threshold;
end

function reports = cluster_detections(detection, power_map, threshold, ...
        range_axis_m, velocity_axis_mps, minimum_cells)
[range_count, doppler_count] = size(detection);
visited = false(size(detection));
empty_report = struct('range_m', {}, 'velocity_mps', {}, 'peak_power', {}, ...
    'cell_count', {}, 'range_index', {}, 'doppler_index', {});
reports = empty_report;
for seed_range = 1:range_count
    for seed_doppler = 1:doppler_count
        if ~detection(seed_range,seed_doppler) || visited(seed_range,seed_doppler)
            continue;
        end
        queue_range = zeros(1, range_count*doppler_count);
        queue_doppler = zeros(1, range_count*doppler_count);
        queue_range(1) = seed_range;
        queue_doppler(1) = seed_doppler;
        visited(seed_range,seed_doppler) = true;
        head = 1;
        tail = 1;
        component_range = zeros(1, range_count*doppler_count);
        component_doppler = zeros(1, range_count*doppler_count);
        component_count = 0;
        while head <= tail
            current_range = queue_range(head);
            current_doppler = queue_doppler(head);
            head = head+1;
            component_count = component_count+1;
            component_range(component_count) = current_range;
            component_doppler(component_count) = current_doppler;
            for range_step = -1:1
                for doppler_step = -1:1
                    neighbor_range = current_range+range_step;
                    neighbor_doppler = current_doppler+doppler_step;
                    if neighbor_range >= 1 && neighbor_range <= range_count && ...
                            neighbor_doppler >= 1 && neighbor_doppler <= doppler_count && ...
                            detection(neighbor_range,neighbor_doppler) && ...
                            ~visited(neighbor_range,neighbor_doppler)
                        tail = tail+1;
                        queue_range(tail) = neighbor_range;
                        queue_doppler(tail) = neighbor_doppler;
                        visited(neighbor_range,neighbor_doppler) = true;
                    end
                end
            end
        end
        if component_count < minimum_cells
            continue;
        end
        component_range = component_range(1:component_count);
        component_doppler = component_doppler(1:component_count);
        linear_index = sub2ind(size(power_map), component_range, component_doppler);
        excess = max(power_map(linear_index)./threshold(linear_index)-1, 0);
        if sum(excess) <= 0
            excess = ones(size(excess));
        end
        [peak_power, peak_offset] = max(power_map(linear_index));
        report = struct();
        report.range_m = sum(excess.*range_axis_m(component_range))/sum(excess);
        report.velocity_mps = sum(excess.*velocity_axis_mps(component_doppler))/sum(excess);
        report.peak_power = peak_power;
        report.cell_count = component_count;
        report.range_index = component_range(peak_offset);
        report.doppler_index = component_doppler(peak_offset);
        reports(end+1) = report; %#ok<AGROW>
    end
end
end

function score = score_reports(reports, detection, testable, truth, ...
        range_axis_m, velocity_axis_mps, c)
range_gate_m = max(c.c_mps/(2*c.bandwidth_hz), ...
    2*c.c_mps/(2*c.sample_rate_hz));
velocity_gate_mps = 1.5*(c.c_mps/c.carrier_hz)*c.prf_hz/(2*c.pulses);
[matches, used_reports] = maximum_truth_report_matching(reports, truth, ...
    range_gate_m, velocity_gate_mps);
truth_support = false(size(detection));
for target_index = 1:numel(truth.range_m)
    range_rows = max(1,truth.range_index(target_index)-c.guard_range): ...
        min(numel(range_axis_m),truth.range_index(target_index)+c.guard_range);
    doppler_columns = max(1,truth.doppler_index(target_index)-c.guard_doppler): ...
        min(numel(velocity_axis_mps),truth.doppler_index(target_index)+c.guard_doppler);
    truth_support(range_rows,doppler_columns) = true;
end
eligible_background = testable & ~truth_support;
false_cells = sum(detection(eligible_background));
background_cells = sum(eligible_background(:));
score = struct('matches', matches, 'opportunities', numel(truth.range_m), ...
    'pd', matches/numel(truth.range_m), ...
    'false_cells', false_cells, ...
    'background_cells', background_cells, ...
    'empirical_false_cell_rate', false_cells/max(background_cells,1), ...
    'false_reports', sum(~used_reports));
end

function [matches, used_reports] = maximum_truth_report_matching( ...
        reports, truth, range_gate_m, velocity_gate_mps)
% Each reachable bit mask represents a valid one-report/one-truth assignment.
% Retaining all reachable masks avoids truth-order-dependent greedy undercounts.
truth_count = numel(truth.range_m);
mask_count = 2^truth_count;
reachable_masks = false(1, mask_count);
reachable_masks(1) = true;
used_report_masks = false(mask_count, numel(reports));
for report_index = 1:numel(reports)
    prior_reachable = reachable_masks;
    prior_used = used_report_masks;
    for mask = 0:mask_count-1
        if ~prior_reachable(mask+1)
            continue;
        end
        for target_index = 1:truth_count
            target_bit = 2^(target_index-1);
            if bitand(mask, target_bit) ~= 0
                continue;
            end
            range_error = abs(reports(report_index).range_m- ...
                truth.range_m(target_index));
            velocity_error = abs(reports(report_index).velocity_mps- ...
                truth.approach_speed_mps(target_index));
            if range_error <= range_gate_m && velocity_error <= velocity_gate_mps
                next_mask = bitor(mask, target_bit);
                if ~reachable_masks(next_mask+1)
                    reachable_masks(next_mask+1) = true;
                    used_report_masks(next_mask+1,:) = prior_used(mask+1,:);
                    used_report_masks(next_mask+1,report_index) = true;
                end
            end
        end
    end
end

matches = 0;
best_mask = 0;
for mask = 0:mask_count-1
    if reachable_masks(mask+1)
        candidate_matches = sum(bitget(mask, 1:truth_count));
        if candidate_matches > matches
            matches = candidate_matches;
            best_mask = mask;
        end
    end
end
used_reports = used_report_masks(best_mask+1,:);
end

function track = alpha_beta_track(report_history, c, truth_history_m)
scan_count = numel(report_history);
range_state_m = zeros(1, scan_count);
range_rate_mps = zeros(1, scan_count);
updated = false(1, scan_count);
coast_count = zeros(1, scan_count);
initial_reports = report_history{1};
best = 0;
best_strength = -inf;
for report_index = 1:numel(initial_reports)
    candidate = initial_reports(report_index);
    if candidate.range_m > 1300 && candidate.range_m < 2000 && ...
            candidate.velocity_mps > 0 && candidate.peak_power > best_strength
        best = report_index;
        best_strength = candidate.peak_power;
    end
end
assert(best > 0, 'P84:TrackerInitiation', ...
    'The declared surveillance sector must contain an initiating report.');
range_state_m(1) = initial_reports(best).range_m;
range_rate_mps(1) = -initial_reports(best).velocity_mps;
updated(1) = true;

for scan_index = 2:scan_count
    predicted_range_m = range_state_m(scan_index-1)+ ...
        range_rate_mps(scan_index-1)*c.scan_interval_s;
    predicted_rate_mps = range_rate_mps(scan_index-1);
    reports = report_history{scan_index};
    best = 0;
    best_cost = inf;
    for report_index = 1:numel(reports)
        range_error = abs(reports(report_index).range_m-predicted_range_m);
        velocity_error = abs(reports(report_index).velocity_mps+predicted_rate_mps);
        cost = range_error/c.tracker_range_gate_m+ ...
            velocity_error/c.tracker_velocity_gate_mps;
        if range_error <= c.tracker_range_gate_m && ...
                velocity_error <= c.tracker_velocity_gate_mps && cost < best_cost
            best = report_index;
            best_cost = cost;
        end
    end
    if best > 0
        innovation_m = reports(best).range_m-predicted_range_m;
        range_state_m(scan_index) = predicted_range_m+c.tracker_alpha*innovation_m;
        range_rate_mps(scan_index) = predicted_rate_mps+ ...
            c.tracker_beta*innovation_m/c.scan_interval_s;
        updated(scan_index) = true;
        coast_count(scan_index) = 0;
    else
        range_state_m(scan_index) = predicted_range_m;
        range_rate_mps(scan_index) = predicted_rate_mps;
        coast_count(scan_index) = coast_count(scan_index-1)+1;
        assert(coast_count(scan_index) <= c.maximum_coast_scans, ...
            'P84:TrackerCoastBound', 'Track exceeded the configured coast bound.');
    end
end
track = struct('range_m', range_state_m, 'range_rate_mps', range_rate_mps, ...
    'updated', updated, 'coast_count', coast_count, ...
    'truth_for_offline_scoring_m', truth_history_m);
end

function width = response_width_samples(range_power, peak_index)
half_power = range_power(peak_index)/2;
left = peak_index;
right = peak_index;
while left > 1 && range_power(left-1) >= half_power
    left = left-1;
end
while right < numel(range_power) && range_power(right+1) >= half_power
    right = right+1;
end
width = right-left+1;
end

function noise = private_complex_noise(seed, rows, columns, maximum_values)
assert(~islogical(seed) && isfinite(seed) && seed == floor(seed) && ...
    seed > 0 && seed < 2147483647);
assert(~islogical(rows) && ~islogical(columns) && rows == floor(rows) && ...
    columns == floor(columns) && rows > 0 && columns > 0 && ...
    2*rows*columns <= maximum_values);
count = rows*columns;
uniforms = zeros(1, 2*count);
state = seed;
for index = 1:2*count
    state = mod(16807*state, 2147483647);
    uniforms(index) = state/2147483647;
end
radius = sqrt(-2*log(max(uniforms(1:count), realmin)));
angle = 2*pi*uniforms(count+1:end);
samples = radius.*exp(1j*angle)/sqrt(2);
noise = reshape(samples, rows, columns);
end

function show_power_map(velocity_axis_mps, range_axis_m, power_map, floor_db, plot_title)
normalized_power = power_map/max(power_map(:));
imagesc(velocity_axis_mps, range_axis_m/1000, ...
    10*log10(max(normalized_power,10^(floor_db/10))));
axis xy;
colorbar;
caxis([floor_db 0]);
xlabel('Approach speed (m/s)');
ylabel('Range (km)');
title(plot_title);
end

function show_detection_map(product, truth, plot_title)
imagesc(product.velocity_axis_mps, product.range_axis_m/1000, ...
    double(product.detection));
axis xy;
hold on;
plot(truth.approach_speed_mps, truth.range_m/1000, 'wo', ...
    'MarkerSize', 7, 'LineWidth', 1.3);
for report_index = 1:numel(product.reports)
    plot(product.reports(report_index).velocity_mps, ...
        product.reports(report_index).range_m/1000, 'rx', ...
        'MarkerSize', 8, 'LineWidth', 1.4);
end
colorbar;
xlabel('Approach speed (m/s)');
ylabel('Range (km)');
title(plot_title);
legend('Truth (scoring only)', 'Clustered report', 'Location', 'best');
end
