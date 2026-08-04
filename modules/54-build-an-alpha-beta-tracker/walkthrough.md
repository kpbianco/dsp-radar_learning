# Walkthrough: watch prediction become a track

Run `experiment.m` from the module directory. Work through one figure at a
time. The script is stateless and does not read or write files or learner
progress.

## Baseline observation

Before Figure 1, make one prediction: during the first three-scan dropout, will
the corrected track hold its last position or keep moving?

Figure 1 establishes the scene before tracking. Its upper panel overlays truth,
available noisy position reports, and gray x markers at unavailable scans. Its
lower panel shows the true velocity changing from 20 to 32 m/s. Confirm that
the truth position remains continuous even though the velocity changes.

Figure 2 then overlays truth, reports, one-step prediction, and corrected
position. Its next panels separate velocity and innovation. Notice three
transitions:

1. Early innovations teach the zero initial velocity guess.
2. During each dropout, prediction continues at the current velocity estimate.
3. After the velocity change, prediction initially lags until repeated positive
   innovations raise the velocity estimate.

The innovation plot has gaps during dropouts because no residual exists without
a report. The velocity estimate is smoother than a two-report difference would
be, but it does not jump instantly to the new truth velocity.

Read the console metrics in their declared units:

- raw available-measurement position RMSE (m) on received scans;
- baseline corrected-position RMSE (m) on those same received scans;
- baseline all-scan position RMSE (m), including prediction-only dropouts;
- constant-segment position RMSE (m);
- velocity RMSE (m/s);
- peak post-change absolute position error over 15 scans (m);
- first velocity-midpoint crossing delay (scans); and
- maximum absolute error while coasting through a dropout (m).

Expected baseline observations are that corrected position is less noisy than
the raw reports on the reviewed constant-velocity interval, every unavailable
scan uses prediction only, the velocity change creates visible nonzero lag,
and the estimate then moves toward the new velocity.

## Sweep 1: change only alpha

Figure 3 uses:

```matlab
alpha_sweep = [0.10 0.35 0.85];
```

Beta remains `0.08`; truth, reports, dropouts, scan interval, initialization,
and every other control remain fixed.

- At alpha `0.10`, position leans heavily on prediction and is smooth but slow
  to remove a position mismatch.
- At alpha `0.35`, the reviewed baseline balances noise rejection and response.
- At alpha `0.85`, corrected position follows noisy reports closely and loses
  much of its smoothing.

Physical connection: alpha is the fraction of the current position innovation
accepted immediately. It does not change how much velocity is corrected from
that same innovation.

## Sweep 2: change only beta

Figure 4 uses:

```matlab
beta_sweep = [0.01 0.08 0.30];
```

Alpha remains `0.35` and the same measurement record is reused.

- At beta `0.01`, velocity changes slowly and the post-change lag persists.
- At beta `0.08`, the baseline adapts over several reports.
- At beta `0.30`, velocity reacts quickly but visibly carries more measurement
  noise and may overshoot.

Physical connection: `beta/T` converts a position innovation into a velocity
correction. Compare velocity noise and position lag together rather than
choosing the fastest-looking trace.

## Broken case: remove velocity learning

Figure 5 deliberately runs the same tracker with `beta=0` from the same zero
velocity guess. Prediction is still computed and alpha still corrects position,
but velocity remains zero. The result is a position-only smoother that trails
constant motion, fails to coast forward through dropouts, and cannot adapt its
motion prediction after the velocity change.

The recovery is the reviewed positive beta path. Restore:

```matlab
beta_gain = 0.08;
```

and rerun the full predict/innovation/correct sequence. Do not “repair” the
broken curve by changing truth, hiding dropout samples, or using future
measurements.

## Failure interpretation and limiting cases

If the track jumps toward zero during a dropout, inspect whether missing
reports were converted to numeric zeros. If it freezes, inspect whether the
prediction step was replaced by holding the last corrected position. If
velocity correction changes with the units chosen for seconds, inspect the
required division by `T`.

If a gain guard fires, restore finite real scalar gains inside the documented
stability region, an increasing row-vector sweep containing its baseline, a
positive scan interval, unique in-range integer dropout indices, and the fixed
resource ceilings. Warm-up must be nonnegative, and at least one received
report must remain in the steady comparison window so its RMSE is defined. Do
not increase a ceiling to silence a malformed edit.

Try the noiseless limiting case only after the baseline: set measurement noise
to zero, remove dropouts, and initialize the true velocity. Constant-velocity
innovations should remain zero. Reintroducing the velocity change should make
innovations nonzero because the old state no longer matches the target.

## Cancellation and deterministic recovery

Press Ctrl+C to cancel an interactive run. Partial workspace variables or P54
figures may remain. Restore the reviewed controls and rerun from the top. The
script validates controls before random work, closes only figures tagged
`P54`, recreates its private seeded stream, reconstructs truth and reports, and
reinitializes every tracker state. It has no external state to roll back.

This is the recovery procedure, not a claim that MATLAB cancellation or a
MATLAB runtime timeout was executed in CI. Repository learner-CLI fixtures use
a 10-second subprocess timeout so a hung fixture cannot block validation.

## Concept connection and completion handoff

P53 supplies one report per target. P54 converts successive reports into a
smoothed position and velocity using fixed trust. P55 will make that trust
depend on covariance, while P57 will decide which report belongs to which
track.

Finish by answering: how do alpha, beta, prediction-only dropout coasting, and
constant-velocity model mismatch jointly determine noise smoothing and lag?
