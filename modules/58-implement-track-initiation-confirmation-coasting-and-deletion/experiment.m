%% P58: Implement Track Initiation, Confirmation, Coasting, and Deletion
% Guiding question: How does a radar avoid creating permanent tracks from single false alarms?
% Dependency: P57 supplies predict-first, gate-first, one-to-one association.
% This base-MATLAB script exposes every lifecycle transition on one bounded record.

clear;
clc;

%% Visible controls and fixed resource ceilings
false_alarm_seed = 5801;
target_noise_seed = 5802;
number_scans = 30;
scan_interval_s = 1;
target_start_scan = 4;
target_last_report_scan = 24;
target_initial_position_m = 1000;
target_velocity_mps = 12;
target_measurement_std_m = 3;
target_missed_scans = [6 12 13];
false_alarm_scans = [2 5 8 11 15 18 22 26];
association_gate_m = 40;
position_gain = 0.70;
velocity_gain = 0.20;

confirmation_m = 3;
confirmation_n = 4;
maximum_consecutive_coasts = 2;
confirmation_m_sweep = [1 3 4];
coast_limit_sweep_scans = [0 2 5];
broken_case_bypass_management = true;

maximum_detections_per_scan = 2;
maximum_total_tracks = 20;
maximum_sweep_cases = 5;
maximum_lifecycle_runs = 9;
maximum_pair_evaluations = 12000;
maximum_figure_count = 6;

integer_controls = {false_alarm_seed, target_noise_seed, number_scans, ...
    target_start_scan, target_last_report_scan, confirmation_m, confirmation_n, ...
    maximum_consecutive_coasts, maximum_detections_per_scan, ...
    maximum_total_tracks, maximum_sweep_cases, maximum_lifecycle_runs, ...
    maximum_pair_evaluations, maximum_figure_count};
if any(~cellfun(@is_valid_integer_scalar, integer_controls)) || ...
        any(cellfun(@(value) value < 0, integer_controls)) || ...
        any(~arrayfun(@is_valid_integer_scalar, target_missed_scans)) || ...
        any(~arrayfun(@is_valid_integer_scalar, false_alarm_scans))
    error('P58:InvalidIntegerControl', ...
        'Seeds, indices, counts, and ceilings must be finite nonlogical integers.');
end
if false_alarm_seed < 1 || target_noise_seed < 1 || ...
        false_alarm_seed >= 2147483647 || target_noise_seed >= 2147483647 || ...
        number_scans < 1 || target_start_scan < 1 || ...
        target_last_report_scan > number_scans || ...
        target_last_report_scan < target_start_scan
    error('P58:InvalidSceneIndex', 'Seeds and scan limits are outside their valid ranges.');
end
real_controls = {scan_interval_s, target_initial_position_m, target_velocity_mps, ...
    target_measurement_std_m, association_gate_m, position_gain, velocity_gain};
if any(~cellfun(@is_valid_real_scalar, real_controls)) || scan_interval_s <= 0 || ...
        target_measurement_std_m < 0 || association_gate_m <= 0 || ...
        position_gain <= 0 || position_gain > 1 || ...
        velocity_gain <= 0 || velocity_gain > 1
    error('P58:InvalidRealControl', ...
        'Intervals, positions, velocities, noise, gate, and gains must be finite and physical.');
end
if confirmation_m < 1 || confirmation_n < 1 || confirmation_m > confirmation_n
    error('P58:InvalidConfirmationPolicy', 'Require integer 1 <= M <= N.');
end
if numel(unique(target_missed_scans)) ~= numel(target_missed_scans) || ...
        any(diff(target_missed_scans) <= 0) || ...
        any(target_missed_scans < target_start_scan) || ...
        any(target_missed_scans > target_last_report_scan)
    error('P58:InvalidMissSchedule', ...
        'Target misses must be unique increasing scans inside target visibility.');
end
if numel(unique(false_alarm_scans)) ~= numel(false_alarm_scans) || ...
        any(diff(false_alarm_scans) <= 0) || ...
        any(false_alarm_scans < 1) || any(false_alarm_scans > number_scans)
    error('P58:InvalidFalseAlarmSchedule', ...
        'False-alarm scans must be unique increasing in-record indices.');
end
validate_sweep(confirmation_m_sweep, confirmation_m, maximum_sweep_cases, ...
    1, confirmation_n, 'confirmation M');
validate_sweep(coast_limit_sweep_scans, maximum_consecutive_coasts, ...
    maximum_sweep_cases, 0, number_scans, 'coast limit');
if ~isequal(confirmation_m_sweep, [1 3 4]) || ...
        ~isequal(coast_limit_sweep_scans, [0 2 5])
    error('P58:SweepDrift', 'Restore the two reviewed three-case sweeps.');
end
if false_alarm_seed ~= 5801 || target_noise_seed ~= 5802 || ...
        number_scans ~= 30 || target_start_scan ~= 4 || ...
        target_last_report_scan ~= 24 || ...
        ~isequal(target_missed_scans, [6 12 13]) || ...
        ~isequal(false_alarm_scans, [2 5 8 11 15 18 22 26]) || ...
        confirmation_m ~= 3 || confirmation_n ~= 4 || ...
        maximum_consecutive_coasts ~= 2
    error('P58:ReviewedScene', 'Restore the reviewed scene and 3-of-4, two-coast policy.');
end
if maximum_detections_per_scan ~= 2 || maximum_total_tracks ~= 20 || ...
        maximum_sweep_cases ~= 5 || maximum_lifecycle_runs ~= 9 || ...
        maximum_pair_evaluations ~= 12000 || maximum_figure_count ~= 6
    error('P58:CeilingDrift', 'Fixed resource ceilings must not be changed.');
end
if ~isscalar(broken_case_bypass_management) || ...
        ~islogical(broken_case_bypass_management) || ...
        ~broken_case_bypass_management
    error('P58:BrokenCaseControl', 'The reviewed broken-policy comparison must stay enabled.');
end

reviewed_lifecycle_run_count = 1 + numel(confirmation_m_sweep) + ...
    numel(coast_limit_sweep_scans) + 1 + 1;
reviewed_pair_slots = reviewed_lifecycle_run_count*number_scans* ...
    maximum_total_tracks*maximum_detections_per_scan;
if reviewed_lifecycle_run_count > maximum_lifecycle_runs || ...
        reviewed_pair_slots > maximum_pair_evaluations
    error('P58:ResourceBound', ...
        'The reviewed lifecycle work exceeds a fixed resource ceiling.');
end

% Validation and resource checks precede random work, history allocation, and figures.
close(findobj(groot, 'Type', 'figure', 'Tag', 'P58'));

%% Build one deterministic scan record with intermittent target reports and false alarms
scan_index = 1:number_scans;
target_visible = scan_index >= target_start_scan & ...
    scan_index <= target_last_report_scan;
target_report_available = target_visible & ...
    ~ismember(scan_index, target_missed_scans);
target_true_position_m = nan(1, number_scans);
target_true_position_m(target_visible) = target_initial_position_m + ...
    target_velocity_mps*scan_interval_s* ...
    (scan_index(target_visible) - target_start_scan);

number_target_reports = sum(target_report_available);
target_noise_m = target_measurement_std_m*seeded_gaussian_sequence( ...
    target_noise_seed, number_target_reports);
target_report_position_m = nan(1, number_scans);
target_report_position_m(target_report_available) = ...
    target_true_position_m(target_report_available) + target_noise_m;

false_alarm_uniform = seeded_uniform_sequence(false_alarm_seed, ...
    numel(false_alarm_scans));
false_alarm_position_m = 100 + 100*(0:numel(false_alarm_scans)-1) + ...
    20*(false_alarm_uniform - 0.5);
if min(diff(false_alarm_position_m)) <= 2*association_gate_m || ...
        max(false_alarm_position_m) + association_gate_m >= ...
        min(target_true_position_m(target_visible))
    error('P58:SceneIsolation', ...
        'Reviewed false reports must remain isolated from each other and target gates.');
end

detection_position_m = nan(maximum_detections_per_scan, number_scans);
detection_valid = false(maximum_detections_per_scan, number_scans);
detection_truth_id = zeros(maximum_detections_per_scan, number_scans);
for scan = 1:number_scans
    scan_position = [];
    scan_truth_id = [];
    if target_report_available(scan)
        scan_position(end + 1) = target_report_position_m(scan); %#ok<SAGROW>
        scan_truth_id(end + 1) = 1; %#ok<SAGROW>
    end
    false_index = find(false_alarm_scans == scan, 1);
    if ~isempty(false_index)
        scan_position(end + 1) = false_alarm_position_m(false_index); %#ok<SAGROW>
        scan_truth_id(end + 1) = 0; %#ok<SAGROW>
    end
    if numel(scan_position) > maximum_detections_per_scan
        error('P58:DetectionBound', 'A scan exceeds the fixed report ceiling.');
    end
    [scan_position, order] = sort(scan_position);
    scan_truth_id = scan_truth_id(order);
    detection_position_m(1:numel(scan_position), scan) = scan_position;
    detection_truth_id(1:numel(scan_position), scan) = scan_truth_id;
    detection_valid(1:numel(scan_position), scan) = true;
end

figure('Name', 'P58 Figure 1: intermittent reports and seeded false alarms', ...
    'Tag', 'P58');
truth_handle = plot(scan_index, target_true_position_m, 'k-', 'LineWidth', 1.5); hold on;
target_handle = plot(scan_index(target_report_available), ...
    target_report_position_m(target_report_available), 'go', 'MarkerSize', 6);
miss_handle = plot(target_missed_scans, target_true_position_m(target_missed_scans), ...
    'kx', 'MarkerSize', 9, 'LineWidth', 1.4);
false_handle = plot(false_alarm_scans, false_alarm_position_m, 'rx', ...
    'MarkerSize', 9, 'LineWidth', 1.4);
grid on;
xlabel('Scan index'); ylabel('Cartesian position (m)');
title('Reports are unlabeled to the manager; truth colors are scoring overlays');
legend([truth_handle target_handle miss_handle false_handle], ...
    {'Target truth', 'Available target report', 'Missed target report', ...
    'Seeded false alarm'}, 'Location', 'best');

%% Run the reviewed manager: predict, associate, initiate, confirm, coast, delete
baseline = run_track_manager(detection_position_m, detection_valid, ...
    scan_interval_s, association_gate_m, position_gain, velocity_gain, ...
    confirmation_m, confirmation_n, maximum_consecutive_coasts, ...
    maximum_total_tracks);
baseline_score = score_track_results(baseline, detection_truth_id, detection_valid);

target_track_id = baseline_score.confirmed_target_track_ids(1);
if baseline.allocated_track_count ~= 9 || ...
        baseline_score.target_confirmation_scan ~= 7 || ...
        baseline.deletion_scan(target_track_id) ~= 27 || ...
        baseline.lifecycle_history(target_track_id, 12) ~= 3 || ...
        baseline.lifecycle_history(target_track_id, 13) ~= 3 || ...
        baseline.lifecycle_history(target_track_id, 14) ~= 2 || ...
        baseline_score.false_confirmed_count ~= 0 || ...
        baseline_score.false_deleted_count ~= 8 || ...
        baseline.final_active_count ~= 0
    error('P58:BaselineInvariant', ...
        'The reviewed confirmation, coast, deletion, or false-track result drifted.');
end

figure('Name', 'P58 Figure 2: managed position histories', 'Tag', 'P58');
subplot(2, 1, 1);
plot(scan_index, target_true_position_m, 'k-', 'LineWidth', 1.5); hold on;
for track_id = 1:baseline.allocated_track_count
    plot(scan_index, baseline.position_history(track_id, :), '-', ...
        'LineWidth', 1.0, 'HandleVisibility', 'off');
end
plot(scan_index(target_report_available), ...
    target_report_position_m(target_report_available), 'go', 'MarkerSize', 5);
plot(false_alarm_scans, false_alarm_position_m, 'rx', 'MarkerSize', 7);
grid on; xlabel('Scan index'); ylabel('Cartesian position (m)');
title('Every unassigned report births a tentative trajectory');
legend({'Target truth', 'Available target report', 'False alarm'}, ...
    'Location', 'best');
subplot(2, 1, 2);
stairs(scan_index, baseline.tentative_count_history, 'Color', [0.85 0.55 0], ...
    'LineWidth', 1.3); hold on;
stairs(scan_index, baseline.confirmed_count_history, 'g-', 'LineWidth', 1.3);
stairs(scan_index, baseline.coasting_count_history, 'b-', 'LineWidth', 1.3);
grid on; xlabel('Scan index'); ylabel('Active track count');
title('Tentative evidence is separated from confirmed and coasting state');
legend({'Tentative', 'Confirmed with hit', 'Coasting'}, 'Location', 'best');

figure('Name', 'P58 Figure 3: lifecycle state and rolling score', 'Tag', 'P58');
subplot(2, 1, 1);
imagesc(scan_index, 1:baseline.allocated_track_count, ...
    baseline.lifecycle_history(1:baseline.allocated_track_count, :));
axis xy; colorbar; caxis([0 4]);
xlabel('Scan index'); ylabel('Track ID');
title('Track lifecycle state: 0 inactive, 1 tentative, 2 confirmed, 3 coasting, 4 deleted');
subplot(2, 1, 2);
stairs(scan_index, baseline.hit_score_history(target_track_id, :), ...
    'b-', 'LineWidth', 1.5); hold on;
plot([1 number_scans], [confirmation_m confirmation_m], 'r--', 'LineWidth', 1.2);
grid on; ylim([0 confirmation_n + 0.5]);
xlabel('Scan index'); ylabel('Hit score (detections in N scans)');
title(sprintf('Target Track %d confirms at score M, then coast logic takes over', ...
    target_track_id));
legend({'Rolling target-track score', 'Confirmation threshold M'}, ...
    'Location', 'best');

%% Sweep 1: vary only confirmation M on the same detections
confirmation_sweep_true_confirm_scan = zeros(size(confirmation_m_sweep));
confirmation_sweep_false_confirmed_count = zeros(size(confirmation_m_sweep));
confirmation_sweep_target_track_count = zeros(size(confirmation_m_sweep));
for sweep_index = 1:numel(confirmation_m_sweep)
    sweep_result = run_track_manager(detection_position_m, detection_valid, ...
        scan_interval_s, association_gate_m, position_gain, velocity_gain, ...
        confirmation_m_sweep(sweep_index), confirmation_n, ...
        maximum_consecutive_coasts, maximum_total_tracks);
    sweep_score = score_track_results(sweep_result, detection_truth_id, detection_valid);
    confirmation_sweep_true_confirm_scan(sweep_index) = ...
        sweep_score.target_confirmation_scan;
    confirmation_sweep_false_confirmed_count(sweep_index) = ...
        sweep_score.false_confirmed_count;
    confirmation_sweep_target_track_count(sweep_index) = ...
        sweep_score.confirmed_target_track_count;
end
if ~isequal(confirmation_sweep_true_confirm_scan, [4 7 11]) || ...
        ~isequal(confirmation_sweep_false_confirmed_count, [8 0 0])
    error('P58:ConfirmationSweepInvariant', ...
        'The reviewed M sweep no longer exposes false confirmation and latency.');
end

figure('Name', 'P58 Figure 4: confirmation threshold sweep', 'Tag', 'P58');
yyaxis left;
plot(confirmation_m_sweep, confirmation_sweep_true_confirm_scan, ...
    'bo-', 'LineWidth', 1.4, 'MarkerFaceColor', 'b');
ylabel('Earliest true confirmation scan');
yyaxis right;
plot(confirmation_m_sweep, confirmation_sweep_false_confirmed_count, ...
    'rs-', 'LineWidth', 1.4, 'MarkerFaceColor', 'r');
ylabel('Confirmed false-track count');
grid on; xlabel('Required hits M in fixed N = 4 scans');
title('Stricter confirmation rejects isolated alarms but delays declaration');

%% Sweep 2: vary only coast allowance L on the same detections
coast_sweep_gap_survived = false(size(coast_limit_sweep_scans));
coast_sweep_confirmed_target_tracks = zeros(size(coast_limit_sweep_scans));
coast_sweep_final_target_deletion_scan = zeros(size(coast_limit_sweep_scans));
for sweep_index = 1:numel(coast_limit_sweep_scans)
    sweep_result = run_track_manager(detection_position_m, detection_valid, ...
        scan_interval_s, association_gate_m, position_gain, velocity_gain, ...
        confirmation_m, confirmation_n, coast_limit_sweep_scans(sweep_index), ...
        maximum_total_tracks);
    sweep_score = score_track_results(sweep_result, detection_truth_id, detection_valid);
    coast_sweep_gap_survived(sweep_index) = sweep_score.short_gap_same_id_survived;
    coast_sweep_confirmed_target_tracks(sweep_index) = ...
        sweep_score.confirmed_target_track_count;
    coast_sweep_final_target_deletion_scan(sweep_index) = ...
        sweep_score.target_last_deletion_scan;
end
if ~isequal(coast_sweep_gap_survived, [false true true]) || ...
        ~isequal(coast_sweep_confirmed_target_tracks, [2 1 1]) || ...
        ~isequal(coast_sweep_final_target_deletion_scan, [25 27 30])
    error('P58:CoastSweepInvariant', ...
        'The reviewed coast sweep no longer exposes survival and stale deletion.');
end

figure('Name', 'P58 Figure 5: coast allowance sweep', 'Tag', 'P58');
subplot(2, 1, 1);
stairs(coast_limit_sweep_scans, coast_sweep_gap_survived, 'bo-', ...
    'LineWidth', 1.4, 'MarkerFaceColor', 'b');
grid on; ylim([-0.1 1.1]); yticks([0 1]);
xlabel('Allowed consecutive coasts L (scans)');
ylabel('Two-scan gap survived (logical)');
title('A dropout of r scans survives only when r <= L');
subplot(2, 1, 2);
yyaxis left;
plot(coast_limit_sweep_scans, coast_sweep_final_target_deletion_scan, ...
    'ks-', 'LineWidth', 1.4, 'MarkerFaceColor', [0.6 0.6 0.6]);
ylabel('Final target deletion scan');
yyaxis right;
plot(coast_limit_sweep_scans, coast_sweep_confirmed_target_tracks, ...
    'rd--', 'LineWidth', 1.2);
grid on; xlabel('Allowed consecutive coasts L (scans)');
ylabel('Confirmed target-track segments (tracks)');
title('More coasting preserves identity but delays stale-track removal');
legend({'Final target deletion scan', 'Confirmed target-track segments'}, ...
    'Location', 'best');

%% Broken case: make every report immediately confirmed and effectively immortal
if broken_case_bypass_management
    broken = run_track_manager(detection_position_m, detection_valid, ...
        scan_interval_s, association_gate_m, position_gain, velocity_gain, ...
        1, 1, number_scans, maximum_total_tracks);
else
    error('P58:BrokenCaseDisabled', 'The intentionally broken policy was not run.');
end
broken_score = score_track_results(broken, detection_truth_id, detection_valid);
recovered = run_track_manager(detection_position_m, detection_valid, ...
    scan_interval_s, association_gate_m, position_gain, velocity_gain, ...
    confirmation_m, confirmation_n, maximum_consecutive_coasts, ...
    maximum_total_tracks);
recovery_exact = lifecycle_results_equal(recovered, baseline);
if broken_score.false_confirmed_count ~= 8 || ...
        broken.final_active_count ~= 9 || ~recovery_exact
    error('P58:BrokenRecoveryInvariant', ...
        'Broken immediate/immortal tracks or exact deterministic recovery drifted.');
end

figure('Name', 'P58 Figure 6: broken policy and exact recovery', 'Tag', 'P58');
subplot(2, 1, 1);
stairs(scan_index, baseline.active_count_history, 'g-', 'LineWidth', 1.5); hold on;
stairs(scan_index, broken.active_count_history, 'r--', 'LineWidth', 1.5);
grid on; xlabel('Scan index'); ylabel('Active track count');
title('Broken 1-of-1 plus no practical deletion accumulates false tracks');
legend({'Reviewed manager', 'Broken bypass policy'}, 'Location', 'best');
subplot(2, 1, 2);
bar([baseline_score.false_confirmed_count broken_score.false_confirmed_count]);
grid on; xticks([1 2]); xticklabels({'Reviewed', 'Broken'});
ylabel('Confirmed false-track count');
title(sprintf('Recovery exactly reproduces baseline arrays: %d', recovery_exact));

%% Retained workspace and console metrics
baseline_target_confirmation_scan = baseline_score.target_confirmation_scan;
baseline_target_deletion_scan = baseline.deletion_scan(target_track_id);
baseline_false_track_count = baseline_score.false_track_count;
baseline_false_confirmed_count = baseline_score.false_confirmed_count;
baseline_false_deleted_count = baseline_score.false_deleted_count;
baseline_peak_active_tracks = baseline.peak_active_count;
baseline_short_gap_same_id_survived = baseline_score.short_gap_same_id_survived;
baseline_target_coast_scans = find( ...
    baseline.lifecycle_history(target_track_id, :) == 3);
broken_false_confirmed_count = broken_score.false_confirmed_count;
broken_final_active_tracks = broken.final_active_count;

fprintf('\nP58 reviewed lifecycle metrics\n');
fprintf('Target confirmation scan: %d\n', baseline_target_confirmation_scan);
fprintf('Target deletion scan: %d\n', baseline_target_deletion_scan);
fprintf('Target coast scans: %s scans\n', mat2str(baseline_target_coast_scans));
fprintf('False tracks initiated/deleted/confirmed: %d / %d / %d tracks\n', ...
    baseline_false_track_count, baseline_false_deleted_count, ...
    baseline_false_confirmed_count);
fprintf('Peak/final active tracks: %d / %d tracks\n', ...
    baseline_peak_active_tracks, baseline.final_active_count);
fprintf('Broken false confirmations/final active: %d / %d tracks\n', ...
    broken_false_confirmed_count, broken_final_active_tracks);
fprintf('Reviewed lifecycle runs/pair slots: %d / %d\n', ...
    reviewed_lifecycle_run_count, reviewed_pair_slots);
fprintf('Exact recovery: %d\n', recovery_exact);

%% Local functions
function result = run_track_manager(detection_position_m, detection_valid, ...
        scan_interval_s, association_gate_m, position_gain, velocity_gain, ...
        confirmation_m, confirmation_n, maximum_consecutive_coasts, ...
        maximum_total_tracks)
% Predict, associate, and then apply an explicit lifecycle state machine.

    if ~isnumeric(detection_position_m) || ~isreal(detection_position_m) || ...
            ~ismatrix(detection_position_m) || ~islogical(detection_valid) || ...
            ~isequal(size(detection_position_m), size(detection_valid)) || ...
            isempty(detection_position_m) || size(detection_position_m, 1) > 2 || ...
            size(detection_position_m, 2) > 30
        error('P58:MalformedDetectionRecord', ...
            'Detection values and logical validity mask must be matching bounded matrices.');
    end
    if any(~isfinite(detection_position_m(detection_valid))) || ...
            any(~isnan(detection_position_m(~detection_valid)))
        error('P58:InvalidDetectionValue', ...
            'Valid detections must be finite; unused detection slots must be NaN.');
    end
    if ~is_valid_integer_scalar(confirmation_m) || ...
            ~is_valid_integer_scalar(confirmation_n) || ...
            ~is_valid_integer_scalar(maximum_consecutive_coasts) || ...
            ~is_valid_integer_scalar(maximum_total_tracks) || confirmation_m < 1 || ...
            confirmation_n < 1 || confirmation_m > confirmation_n || ...
            confirmation_n > 30 || maximum_consecutive_coasts < 0 || ...
            maximum_consecutive_coasts > 30 || maximum_total_tracks < 1 || ...
            maximum_total_tracks > 20
        error('P58:InvalidManagerPolicy', ...
            'Manager policy must satisfy 1 <= M <= N and bounded nonnegative L.');
    end
    if ~is_valid_real_scalar(scan_interval_s) || ...
            ~is_valid_real_scalar(association_gate_m) || ...
            ~is_valid_real_scalar(position_gain) || ...
            ~is_valid_real_scalar(velocity_gain) || scan_interval_s <= 0 || ...
            association_gate_m <= 0 || position_gain <= 0 || position_gain > 1 || ...
            velocity_gain <= 0 || velocity_gain > 1
        error('P58:InvalidManagerScale', 'Manager intervals, gate, and gains are invalid.');
    end

    [maximum_detections_per_scan, number_scans] = size(detection_position_m);
    active = false(maximum_total_tracks, 1);
    confirmed = false(maximum_total_tracks, 1);
    position_m = zeros(maximum_total_tracks, 1);
    velocity_mps = zeros(maximum_total_tracks, 1);
    age_scans = zeros(maximum_total_tracks, 1);
    consecutive_misses = zeros(maximum_total_tracks, 1);
    hit_history = false(maximum_total_tracks, confirmation_n);
    birth_scan = zeros(maximum_total_tracks, 1);
    confirmation_scan = zeros(maximum_total_tracks, 1);
    deletion_scan = zeros(maximum_total_tracks, 1);
    allocated_track_count = 0;

    lifecycle_history = zeros(maximum_total_tracks, number_scans);
    hit_score_history = zeros(maximum_total_tracks, number_scans);
    miss_count_history = zeros(maximum_total_tracks, number_scans);
    position_history = nan(maximum_total_tracks, number_scans);
    assignment_index_history = zeros(maximum_total_tracks, number_scans);
    active_count_history = zeros(1, number_scans);
    tentative_count_history = zeros(1, number_scans);
    confirmed_count_history = zeros(1, number_scans);
    coasting_count_history = zeros(1, number_scans);

    for scan = 1:number_scans
        active_at_scan_start = find(active);
        predicted_position_m = position_m;
        predicted_position_m(active_at_scan_start) = ...
            position_m(active_at_scan_start) + ...
            scan_interval_s*velocity_mps(active_at_scan_start);

        % P57-compatible fixed-gate, globally nearest remaining valid pair.
        pair_distance_m = inf(maximum_total_tracks, maximum_detections_per_scan);
        for track_id = active_at_scan_start'
            for detection_index = find(detection_valid(:, scan))'
                residual_m = detection_position_m(detection_index, scan) - ...
                    predicted_position_m(track_id);
                if abs(residual_m) <= association_gate_m
                    pair_distance_m(track_id, detection_index) = abs(residual_m);
                end
            end
        end
        assigned_detection = zeros(maximum_total_tracks, 1);
        detection_used = false(maximum_detections_per_scan, 1);
        for assignment_step = 1:min(numel(active_at_scan_start), ...
                sum(detection_valid(:, scan)))
            [best_distance_m, linear_index] = min(pair_distance_m(:));
            if ~isfinite(best_distance_m)
                break;
            end
            [track_id, detection_index] = ind2sub(size(pair_distance_m), linear_index);
            assigned_detection(track_id) = detection_index;
            detection_used(detection_index) = true;
            pair_distance_m(track_id, :) = Inf;
            pair_distance_m(:, detection_index) = Inf;
        end

        % Existing tracks age once. A birth hit was already entered on initiation.
        for track_id = active_at_scan_start'
            age_scans(track_id) = age_scans(track_id) + 1;
            has_hit = assigned_detection(track_id) > 0;
            if confirmation_n > 1
                hit_history(track_id, 1:confirmation_n-1) = ...
                    hit_history(track_id, 2:confirmation_n);
            end
            hit_history(track_id, confirmation_n) = has_hit;

            if has_hit
                detection_index = assigned_detection(track_id);
                residual_m = detection_position_m(detection_index, scan) - ...
                    predicted_position_m(track_id);
                position_m(track_id) = predicted_position_m(track_id) + ...
                    position_gain*residual_m;
                velocity_mps(track_id) = velocity_mps(track_id) + ...
                    (velocity_gain/scan_interval_s)*residual_m;
                consecutive_misses(track_id) = 0;
                assignment_index_history(track_id, scan) = detection_index;
            else
                position_m(track_id) = predicted_position_m(track_id);
                consecutive_misses(track_id) = consecutive_misses(track_id) + 1;
            end

            hit_score = sum(hit_history(track_id, :));
            if ~confirmed(track_id) && hit_score >= confirmation_m
                confirmed(track_id) = true;
                confirmation_scan(track_id) = scan;
            end

            deleted_now = false;
            if ~confirmed(track_id) && age_scans(track_id) >= confirmation_n && ...
                    hit_score < confirmation_m
                active(track_id) = false;
                deletion_scan(track_id) = scan;
                deleted_now = true;
            elseif confirmed(track_id) && ...
                    consecutive_misses(track_id) > maximum_consecutive_coasts
                active(track_id) = false;
                deletion_scan(track_id) = scan;
                deleted_now = true;
            end

            if deleted_now
                lifecycle_history(track_id, scan) = 4;
            elseif ~confirmed(track_id)
                lifecycle_history(track_id, scan) = 1;
            elseif consecutive_misses(track_id) > 0
                lifecycle_history(track_id, scan) = 3;
            else
                lifecycle_history(track_id, scan) = 2;
            end
            hit_score_history(track_id, scan) = hit_score;
            miss_count_history(track_id, scan) = consecutive_misses(track_id);
            position_history(track_id, scan) = position_m(track_id);
        end

        % Each still-unassigned report initiates exactly one new tentative ID.
        for detection_index = find(detection_valid(:, scan) & ~detection_used)'
            if allocated_track_count >= maximum_total_tracks
                error('P58:TrackResourceBound', ...
                    'The scan record requires more track IDs than the fixed ceiling.');
            end
            allocated_track_count = allocated_track_count + 1;
            track_id = allocated_track_count;
            active(track_id) = true;
            confirmed(track_id) = confirmation_m <= 1;
            position_m(track_id) = detection_position_m(detection_index, scan);
            velocity_mps(track_id) = 0;
            age_scans(track_id) = 1;
            consecutive_misses(track_id) = 0;
            hit_history(track_id, :) = false;
            hit_history(track_id, confirmation_n) = true;
            birth_scan(track_id) = scan;
            assignment_index_history(track_id, scan) = detection_index;
            hit_score_history(track_id, scan) = 1;
            position_history(track_id, scan) = position_m(track_id);
            if confirmed(track_id)
                confirmation_scan(track_id) = scan;
                lifecycle_history(track_id, scan) = 2;
            else
                lifecycle_history(track_id, scan) = 1;
            end
        end

        tentative_count_history(scan) = sum(active & ~confirmed);
        confirmed_count_history(scan) = sum(active & confirmed & consecutive_misses == 0);
        coasting_count_history(scan) = sum(active & confirmed & consecutive_misses > 0);
        active_count_history(scan) = sum(active);
    end

    result.active = active;
    result.confirmed = confirmed;
    result.birth_scan = birth_scan;
    result.confirmation_scan = confirmation_scan;
    result.deletion_scan = deletion_scan;
    result.lifecycle_history = lifecycle_history;
    result.hit_score_history = hit_score_history;
    result.miss_count_history = miss_count_history;
    result.position_history = position_history;
    result.assignment_index_history = assignment_index_history;
    result.active_count_history = active_count_history;
    result.tentative_count_history = tentative_count_history;
    result.confirmed_count_history = confirmed_count_history;
    result.coasting_count_history = coasting_count_history;
    result.allocated_track_count = allocated_track_count;
    result.peak_active_count = max(active_count_history);
    result.final_active_count = active_count_history(end);
end

function score = score_track_results(result, detection_truth_id, detection_valid)
% Truth labels enter only here, after all associations and lifecycle decisions.
    if ~isequal(size(detection_truth_id), size(detection_valid)) || ...
            any(~ismember(detection_truth_id(detection_valid), [0 1])) || ...
            any(detection_truth_id(~detection_valid) ~= 0)
        error('P58:MalformedTruthLabels', 'Scoring labels do not match the scan record.');
    end
    [~, number_scans] = size(detection_truth_id);
    true_hit_count = zeros(size(result.birth_scan));
    false_hit_count = zeros(size(result.birth_scan));
    for track_id = 1:result.allocated_track_count
        for scan = 1:number_scans
            detection_index = result.assignment_index_history(track_id, scan);
            if detection_index > 0
                if detection_truth_id(detection_index, scan) == 1
                    true_hit_count(track_id) = true_hit_count(track_id) + 1;
                else
                    false_hit_count(track_id) = false_hit_count(track_id) + 1;
                end
            end
        end
    end
    birth_truth_id = zeros(size(result.birth_scan));
    for track_id = 1:result.allocated_track_count
        birth = result.birth_scan(track_id);
        birth_detection = result.assignment_index_history(track_id, birth);
        birth_truth_id(track_id) = detection_truth_id(birth_detection, birth);
    end
    allocated = result.birth_scan > 0;
    target_track = allocated & birth_truth_id == 1;
    false_track = allocated & birth_truth_id == 0;
    confirmed_target = target_track & result.confirmation_scan > 0;
    confirmed_false = false_track & result.confirmation_scan > 0;
    confirmed_target_ids = find(confirmed_target);
    if isempty(confirmed_target_ids)
        target_confirmation_scan = 0;
        target_last_deletion_scan = 0;
        short_gap_same_id_survived = false;
    else
        target_confirmation_scan = min(result.confirmation_scan(confirmed_target));
        target_last_deletion_scan = max(result.deletion_scan(confirmed_target));
        first_target_id = confirmed_target_ids(1);
        short_gap_same_id_survived = ...
            result.lifecycle_history(first_target_id, 12) == 3 && ...
            result.lifecycle_history(first_target_id, 13) == 3 && ...
            result.lifecycle_history(first_target_id, 14) == 2;
    end
    score.true_hit_count = true_hit_count;
    score.false_hit_count = false_hit_count;
    score.birth_truth_id = birth_truth_id;
    score.confirmed_target_track_ids = confirmed_target_ids;
    score.target_confirmation_scan = target_confirmation_scan;
    score.target_last_deletion_scan = target_last_deletion_scan;
    score.confirmed_target_track_count = sum(confirmed_target);
    score.false_track_count = sum(false_track);
    score.false_confirmed_count = sum(confirmed_false);
    score.false_deleted_count = sum(false_track & result.deletion_scan > 0);
    score.short_gap_same_id_survived = short_gap_same_id_survived;
end

function equal = lifecycle_results_equal(left, right)
% Compare every decision-bearing result, not a hand-set success flag.
    fields = {'active', 'confirmed', 'birth_scan', 'confirmation_scan', ...
        'deletion_scan', 'lifecycle_history', 'hit_score_history', ...
        'miss_count_history', 'position_history', 'assignment_index_history', ...
        'active_count_history', 'tentative_count_history', ...
        'confirmed_count_history', 'coasting_count_history', ...
        'allocated_track_count', 'peak_active_count', 'final_active_count'};
    equal = true;
    for field_index = 1:numel(fields)
        field_name = fields{field_index};
        equal = equal && isequaln(left.(field_name), right.(field_name));
    end
end

function values = seeded_uniform_sequence(seed, count)
% Minimal-standard Park-Miller sequence local to this script.
    if ~isscalar(seed) || ~isfinite(seed) || ~isreal(seed) || ...
            seed ~= floor(seed) || islogical(seed) || seed < 1 || ...
            seed >= 2147483647 || ~isscalar(count) || ~isfinite(count) || ...
            ~isreal(count) || count ~= floor(count) || islogical(count) || ...
            count < 1 || count > 60
        error('P58:InvalidSeedRequest', 'Seed and requested draw count are invalid.');
    end
    modulus = 2147483647;
    multiplier = 16807;
    state = seed;
    values = zeros(1, count);
    for sample_index = 1:count
        state = mod(multiplier*state, modulus);
        values(sample_index) = state/modulus;
    end
end

function values = seeded_gaussian_sequence(seed, count)
% Box-Muller transform over the private Park-Miller uniforms.
    uniforms = seeded_uniform_sequence(seed, 2*ceil(count/2));
    values = zeros(1, count);
    output_index = 1;
    for pair_index = 1:2:numel(uniforms)
        uniform_1 = max(uniforms(pair_index), 1/2147483647);
        uniform_2 = uniforms(pair_index + 1);
        radius = sqrt(-2*log(uniform_1));
        pair = radius*[cos(2*pi*uniform_2) sin(2*pi*uniform_2)];
        for component = 1:2
            if output_index <= count
                values(output_index) = pair(component);
                output_index = output_index + 1;
            end
        end
    end
end

function validate_sweep(values, baseline, maximum_cases, lower, upper, label)
    if ~isrow(values) || isempty(values) || numel(values) > maximum_cases || ...
            any(~isfinite(values)) || any(~isreal(values)) || ...
            any(values ~= floor(values)) || any(islogical(values)) || ...
            any(diff(values) <= 0) || any(values < lower) || any(values > upper) || ...
            sum(values == baseline) ~= 1
        error('P58:InvalidSweep', ...
            '%s sweep must be finite, increasing, bounded, and contain one baseline.', label);
    end
end

function valid = is_valid_integer_scalar(value)
    valid = isnumeric(value) && isscalar(value) && isreal(value) && ...
        isfinite(value) && ~islogical(value) && value == floor(value);
end

function valid = is_valid_real_scalar(value)
    valid = isnumeric(value) && isscalar(value) && isreal(value) && ...
        isfinite(value) && ~islogical(value);
end
