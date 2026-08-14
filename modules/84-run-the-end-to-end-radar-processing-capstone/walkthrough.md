# P84 walkthrough

## Guiding question

Can I trace a target from waveform generation through detection and tracking without treating any stage as a black box?

Run `experiment.m` once without editing it. Keep the Command Window metrics
visible. Inspect one transition at a time; the goal is to locate causes, not to
memorize a finished plot.

## Baseline: follow one moving target through eight stages

1. **Waveform:** In figure 1, identify the finite pulse and the linear
   instantaneous-frequency sweep. Record the separate values for range sample
   spacing and nominal range resolution.
2. **Scene and receiver:** In figure 2, compare measured and calibrated
   voltages. DC/image calibration changes samples before any range or Doppler
   decision exists.
3. **Matched filter:** In figure 3, follow the moving target near 1.65 km. The
   range profile is created by convolution with `conj(fliplr(s))`.
4. **Range-Doppler:** Read the vertical axis as range and the horizontal axis as
   signed approach speed. The stationary target and clutter occupy zero
   Doppler. The echo-like spur is a bright data artifact without target truth.
5. **Detection:** In the left panel of figure 4, CFAR compares every eligible
   CUT with local linear-power training. In the right panel, a threshold
   calibrated on the quiet range region is incorrectly reused beyond the
   clutter edge. Attribute its excess reports to the detector/background
   mismatch, not to extra targets.
6. **Clustering:** Red crosses are reports, not threshold cells. Inspect the
   strong/weak pair near 2.6 km: a merged report can score only one truth. The
   scorer maximizes feasible one-to-one matches rather than depending on truth
   list order.
7. **Tracking:** In figure 5, scan 4 is a coast. The moving echo amplitude was
   set to zero at scene construction, so the tracker predicts without an
   update and reacquires later.
8. **Ledger:** Inspect `p84_results.provenance`. For any surprising output,
   name its immediate input before jumping to a later explanation.

Expected baseline observations:

- a stationary target is hard to separate from the zero-Doppler clutter ridge;
- the moving target has positive Doppler while its range decreases across
  scans;
- the strong/weak pair is limited by compressed-response width, sidelobes, the
  CFAR stencil, and one-report-per-component grouping;
- the receiver spur can become a false report because no truth target created
  it;
- CA-CFAR is more controlled than the quiet-side fixed threshold at the
  clutter edge, but requested and empirical `Pfa` are not identical; and
- track RMSE remains finite through one bounded coast.

## Sweep 1: change only matched-filter taper

Use the existing `taper_sweep = [0 0.5 1]`. The raw and calibrated receiver
arrays do not change. Figure 6's left panel shows measured -3 dB range-response
width and weak/strong cell-power ratio.

Ask two separate questions: Did sidelobe behavior change? Did mainlobe width or
coherent gain change? A wider mainlobe can keep the weak neighbor merged even
if far sidelobes improve. Do not call display sample spacing “resolution.”

## Sweep 2: change only requested Pfa

The existing `pfa_sweep = [1e-4 1e-3 1e-2]` reuses the baseline power map.
Observe threshold-cell and report counts. Because the same CUT powers and
training means are retained, relaxing `Pfa` lowers the threshold and cannot
remove an existing crossing. More crossings are not automatically more
targets.

## Detector comparison: a deliberately invalid fixed-threshold transfer

The fixed threshold is estimated from a quiet range interval and applied to
the whole map. This is a useful detector in a homogeneous known background,
but the scene contains an explicit clutter step. Compare its `Pd`, empirical
false-cell rate, and false reports with CA-CFAR. Recovery is not a magic
threshold value: restore a detector whose local reference model matches the
question being asked, and keep edge CUTs ineligible when their stencil is
incomplete.

## Intentionally broken matched filter and exact recovery

The lower-left panel of figure 6 removes the conjugation from the time-reversed
LFM replica. Locate the
first wrong stage: waveform and receiver data are unchanged; the mismatch
begins at pulse compression. Then compare the downstream map and detection
mask.

Recovery processes `retained_corrected_cube` with the correct replica. The
script asserts exact equality of compressed samples, range-Doppler power,
threshold surface, and decisions with the original baseline. It does not hide
the failure by drawing new noise.

## Common interpretation mistakes

- “A high requested `Pfa` found more targets.” It found more threshold
  crossings; truth matching and false-report accounting decide what they mean.
- “The weak neighbor was detected because its truth marker is inside a blob.”
  One component/report can match only one truth.
- “The tracker filled in the missing measurement.” A coast is prediction only.
- “The Doppler sign is wrong because approach range decreases.” Positive
  approach Doppler corresponds to negative physical range rate.
- “The runtime is deterministic because the data are seeded.” Data are
  deterministic; `tic/toc` depends on the machine and current load.
- “CFAR achieved exactly the requested probability.” The local homogeneous
  exponential model is deliberately violated at the clutter edge.

## Recovery, interruption, and cleanup

The script writes no files and starts no background activity. Ctrl+C can leave
figures and local workspace values, but no partial dataset or external
transaction exists. Rerun to close only figures tagged `P84`, reconstruct the
private seeded samples, and reproduce the processing chain. Learner progress
is managed separately by `bin/learn` under ignored `.learning/`.

## Completion connection

Choose one true target, the receiver spur, the scan-4 miss, and one fixed-
threshold clutter-edge false report. For each, state where it was created,
which stages preserved or transformed it, and where it was detected, merged,
lost, or coasted. That explanation—not a visually pleasing final track—is the
capstone result.
