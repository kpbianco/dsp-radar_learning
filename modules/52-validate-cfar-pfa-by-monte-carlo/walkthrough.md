# Walkthrough: audit the false-alarm denominator before trusting CFAR

## Before running

Open `experiment.m` and note the visible controls: seed 5201, 200,000
independent noise-only CUTs, blocks of 2,000 trials, requested `Pfa=1e-3`,
baseline total `N=24`, requested-probability cases `[1e-2 3e-3 1e-3]`, and
training-count cases `[8 16 24 32 64]`. The mismatch controls are complex
correlation `0.65` and log-texture standard deviation `0.90`.

Run the complete script once. It creates five figure groups tagged `P52` and
leaves a compact `results` structure. Generation and comparisons are blocked
and checked against immutable ceilings before the private random stream is
created.

## 1. Establish one valid trial and the baseline count

Open **P52 homogeneous baseline**. The upper panel shows 240 independent H0
CUT powers and their trial-varying finite-`N` thresholds. A red marker is a
false alarm, not a bug by itself: a request of `1e-3` permits rare crossings.

The lower panel accumulates alarms over increasing tested-CUT counts. Early
estimates jump because the numerator is a small integer. The 95% Wilson limits
narrow as independent evidence accumulates.

Inspect `results.baseline_alarm_count`, `results.tested_cut_count`, and
`results.baseline_measured_pfa`. Confirm that the third value is exactly the
first divided by the second. Then read the retained Wilson limits. The correct
baseline conclusion is statistical agreement with the homogeneous theory,
not exact decimal equality.

## 2. Sweep 1: requested Pfa only

Open **P52 requested Pfa sweep**. The same homogeneous trials and `N=24` are
used for every point; only the request and its finite-`N` alpha change.

Expected observation: measured rates follow the exact iid-theory line. The
lowest requested rate has the fewest alarms and the largest relative interval.

One-variable edit: change `false_alarm_probability_sweep` to
`[1e-2 3e-3 1e-3 3e-4]`. Keep it decreasing, inside the six-case ceiling, and
include the baseline value. Re-run, read the larger relative uncertainty of
the added rare point, then restore the reviewed vector.

## 3. Sweep 2: total training count only

Open **P52 training count sweep**. Every point uses the same requested
`Pfa=1e-3` and homogeneous trial bank. The detector recomputes
`alpha=N*(Pfa^(-1/N)-1)` for each `N`.

Expected observation: all measured points remain statistically consistent
with the same requested rate even though their alpha values differ. This is
the “constant” in CFAR under the stated model.

One-variable edit: change `training_cell_count_sweep` to
`[4 8 16 24 32 64]`. Keep the baseline and resource limits. Re-run and compare
`results.training_scale_factor`; the four-cell alpha is larger, but its
correctly calibrated measured Pfa still targets `1e-3`. Restore the reviewed
vector afterward.

## 4. Sweep 3: change only the noise model

Open **P52 noise model mismatch**. Requested Pfa, total `N`, the finite-`N`
alpha, tested-CUT count, and mean power remain fixed.

- Independent exponential power should remain near `1e-3`.
- The shared-component correlated Gaussian construction should be
  conservative because CUT and training estimate rise together.
- Independent lognormal texture should create far more crossings because the
  CUT can receive a rare scale burst not represented by its references.

This is the third controlled sweep, not an alternative calibration. The point
is to expose that the same alpha carries a statistical model contract.

One-variable edit: reduce `texture_log_standard_deviation` from `0.90` to
`0.45`. Keep everything else fixed. The compound result should move toward
the iid rate as the heavy tail weakens. Restore `0.90` after observing it.

## 5. Run the intentionally broken case and recover

Open **P52 broken scaling and recovery**. The broken detector takes the
known-noise limit `-log(Pfa)` and applies it to a finite 24-cell training mean.
Its measured rate and exact formula both exceed `1e-3`.

Recovery recomputes the finite-`N` alpha from the actual training count and
reuses the homogeneous baseline decisions. Inspect
`results.broken_theoretical_pfa` and
`results.recovered_theoretical_pfa`. The latter should equal the request to
numerical precision; the Monte Carlo measurement still has finite uncertainty.

Common mistake: do not describe the broken detector as more sensitive. It
changed the operating point by purchasing extra alarms.

## Cancellation, timeout, rerun, and recovery

Pressing Ctrl+C may leave partial workspace arrays, but there is no file,
learner-state, worker, timer, or service to roll back. Rerun from the top: the
script clears partial variables, closes only P52-tagged figures, creates a
fresh private stream, and reconstructs the same trials. If a constrained
environment times out, reduce `trial_count` for exploration, set the final
value in `running_trial_counts` to the same count, and keep the block size
as an exact divisor. These are linked bookkeeping controls, not a second
physical mechanism. Restore both reviewed values before treating the retained
interval as the module baseline.

The calibrated recovery is deterministic and local: recompute alpha from `N`
and requested Pfa, then repeat the comparison. It does not relabel broken
counts or reuse an incomplete run as final evidence.

## Completion handoff

Use `checks.md`. You are ready for the teach-back when you can define the H0
numerator and denominator, explain why a correct finite run needs an interval,
and distinguish scaling error from statistical-model mismatch.
