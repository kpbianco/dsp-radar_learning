# P56: Use an EKF for Range-Bearing Measurements

**Phase 6: Radar Tracking and Data Association**  
**Status:** Implemented by batch `P56`

## Guiding question

How can nonlinear radar measurements update Cartesian target state?

## Experiment

Simulate one 2-D target measured only by noisy range and azimuth from a fixed
radar. The seeded trajectory passes behind the radar so the reported bearing
crosses the `+/-180 deg` branch cut while physical direction remains smooth.

## Procedure

Implement the nonlinear measurement prediction and Jacobian explicitly. Compare
raw polar measurements, Cartesian conversions, the EKF trajectory, wrapped
innovations, normalized innovation squared, and position covariance ellipses.
Sweep assumed bearing noise on the same reports, then sweep target range at fixed
angular accuracy. Finally, disable bearing-residual wrapping deliberately and
recover by restoring the local angular difference.

## What this should teach

Nonlinear measurement geometry creates range-dependent uncertainty and requires
local linearization or another nonlinear filter. A fixed bearing error produces
cross-range error that grows approximately as `range * bearing_error_rad`, and
the angular innovation must respect that `+pi` and `-pi` describe neighboring
directions.

## Dependencies and compatibility

- P55 is the direct implemented prerequisite. P56 keeps its constant-velocity
  state/covariance prediction but replaces the linear position report with an
  explicit nonlinear range-bearing prediction and Jacobian.
- P30 supplies the round-trip range interpretation, P18 supplies signed angle
  intuition, and P27 explains why one seeded record is descriptive rather than
  a calibration guarantee.
- One report is assumed to belong to this one track. P57 owns gating and
  report-to-track association.
- `experiment.m` uses base MATLAB only. It exposes `h(x)`, `H`, `Q`, `R`, the
  wrapped innovation, `S`, matrix-solved gain, state correction, and Joseph
  covariance correction; no tracking object, inverse, file, network, worker,
  or global random stream is used.
- The reviewed run is bounded to 101 scans, three cases in each sweep, five
  tagged figures, six filter runs, 600 predict/update transitions, and 73
  points per displayed ellipse. Script-local functions require MATLAB R2016b
  or later.

## Completion condition

The tracker follows the target and the covariance shape changes sensibly with
geometry. You can explain why tangential uncertainty grows with range, why the
Jacobian is evaluated at the prediction, and why an unwrapped branch-cut
residual can corrupt an otherwise reasonable update.

## Start

```bash
./bin/learn start 56
```

Run `experiment.m`, follow `walkthrough.md` one figure at a time, and finish
with the teach-back in `checks.md`.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use an EKF for Range-Bearing Measurements". The guiding question is: "How can nonlinear radar measurements update Cartesian target state?" Use this experiment: Simulate a 2-D target measured only by noisy range and azimuth from a fixed radar. Have me perform these actions: Implement nonlinear measurement prediction and Jacobian. Compare raw polar measurements, Cartesian conversions, EKF trajectory, innovations, and covariance ellipse. The main concept I must learn is: Nonlinear measurement geometry creates range-dependent uncertainty and requires local linearization or another nonlinear filter. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
