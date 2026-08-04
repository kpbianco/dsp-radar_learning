# P50 walkthrough: Apply 2-D CFAR to a Range-Doppler Map

Guiding question: **How does local thresholding extend from one range profile
to two dimensions?**

Run `experiment.m` section by section. Observe one figure group at a time; the
goal is to read the local comparison, not to memorize MATLAB indexing.

## Baseline: map, stencil, threshold, decision

Run through **Baseline: estimate local power, build the threshold surface, and
decide**.

1. In Figure 1, find the raised background near zero velocity and the gradual
   increase with range. Match the three circles and one square to bright target
   neighborhoods.
2. In Figure 2, count the 17-by-13 outer rectangle and the 5-by-5 excluded
   guard+CUT rectangle. Confirm `results.training_cell_count` is `196`.
3. In Figure 3, compare the local mean and threshold surfaces. Then look at the
   CUT/threshold ratio: positive dB cells cross the threshold.
4. Inspect `results.target_is_testable` and `results.target_is_detected`.

Expected observation: the first three target CUTs are eligible and detected.
The fourth is neither detected nor missed; it is outside the white testable
interior because the complete stencil cannot fit around it.

Common mistake: treating the black truth crosses as detector input. The
training loop sees only the power map and fixed geometry; truth is used later
to report what happened.

## Sweep 1: vary only the range training half-width

Run **Sweep 1** with `range_training_sweep = [3 6 12]`.

- Doppler training width and both guard widths remain fixed.
- The physical range half-span grows by 30 m for every added range bin.
- Compare training-cell count, normalized estimate RMSE, target/non-target
  crossings, and the testable fraction.

Expected observation: the training count increases while the eligible map
fraction decreases. Only the top and bottom range borders grow; the fixed
Doppler outer width does not change.

Try `[2 6 10]`, rerun from control validation, and confirm the same geometry
direction. Restore `[3 6 12]` afterward.

Common mistake: requiring the realized crossing count to change monotonically.
All cases use one random map with a nonuniform background; the durable result
is the geometry and locality change, not a three-point `Pfa` estimate.

## Sweep 2: vary only the Doppler training half-width

Run **Sweep 2** with `doppler_training_sweep = [2 4 8]`.

- Range training width and both guard widths remain fixed.
- Convert the horizontal half-span to m/s using the reported 0.625 m/s bin
  spacing.
- Compare the normalized estimate error with the range sweep. A wider Doppler
  stencil mixes more of the central clutter ridge with off-ridge cells.

Expected observation: training count increases, the eligible fraction falls,
and only the left/right velocity borders grow. The zero-Doppler background
makes “more samples” different from “more representative samples.”

Try `[1 4 7]`, rerun from control validation, then restore `[2 4 8]`.

Common mistake: calling both sweeps equivalent window growth. One reaches
farther in physical range; the other reaches farther across radial velocity.

## Intentionally broken case: invent zero-power references

Run **Intentionally broken case**.

Expected observation: the left panel contains finite border thresholds and
white border crossings. The edge target is called a detection because missing
off-map training cells were silently replaced by zeros and still counted in
the denominator.

Explain the failure physically: the radar did not measure those zero-power
reference cells. The full-window `N` and `alpha` cannot be attached to a
window containing invented measurements.

Check that
`results.broken_all_cells_calibrated_claim_is_valid` is false. A colorful,
finite threshold surface is not evidence that its boundary statistics are
valid.

## Recovery

Run **Recovery**.

Expected observation: the right panel labels only the full-stencil interior as
testable. Confirm:

- `results.recovery_threshold_error` is at roundoff scale;
- `results.recovery_detection_matches_baseline` is true; and
- `results.recovered_edge_target_is_testable` is false.

Recovery means restoring no-decision borders, not changing the target truth or
calling the edge cell a miss. An operational detector that must cover the
boundary needs a separately specified and calibrated edge policy.

## Concept connection

Complete this sentence aloud:

> Two-dimensional CA-CFAR averages linear power in a guarded local
> neighborhood spanning ___ and ___; increasing only the range width excludes
> more ___ border cells, while increasing only the Doppler width excludes more
> ___ border cells.

The intended words are range, Doppler/velocity, range, and Doppler/velocity.
Then explain why a guard rectangle and a training rectangle play different
roles.

## Interruption, recovery, and rollback

If you press `Ctrl+C`, the script may leave partial workspace arrays or P50
figures, but it cannot leave an external transaction: there is no file,
network, worker, timer, or hardware output. Rerun from the top. `clearvars`
removes partial arrays, only P50-tagged figures close, and private seed `5001`
recreates the scene.

Repository rollback is bounded to removing P50-created artifacts and catalog
text and restoring only P50's manifest status to `scaffolded`. Preserve P49,
later module identities, ignored `.learning/` progress, and the operator-
managed active-batch contract.
