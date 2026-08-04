# P55: Implement a Constant-Velocity Kalman Filter

**Phase 6: Radar Tracking and Data Association**  
**Status:** Implemented by batch `P55`

## Guiding question

How do process noise and measurement noise determine trust in prediction versus measurement?

## Experiment

Track one target's 1-D position and velocity from noisy scalar position reports.
Generate a seeded nearly-constant-velocity truth record, propagate state and
covariance explicitly, and compare actual errors with the filter's uncertainty.

## Procedure

Plot truth, reports, corrected state, two-sigma covariance bounds, innovations,
innovation bounds, and both Kalman-gain components. Sweep assumed process
acceleration and measurement standard deviation one at a time. Then run
separate under-Q and under-R failures and recover with the reviewed tuning.

## What this should teach

The Kalman filter does not choose trust by intuition alone. Predicted covariance
and `R` set the gain: more predicted uncertainty moves the state toward the new
report, while more measurement uncertainty keeps it nearer the prediction.

## Dependencies and compatibility

- P54 is the direct implemented prerequisite. It exposes the same position and
  velocity prediction with fixed alpha-beta gains; P55 derives time-varying
  gains from covariance.
- P27 motivates treating coverage and innovation statistics from one seed as
  descriptive evidence, not a Monte Carlo guarantee.
- P55 assumes one scalar report is already associated with this track. P56 owns
  nonlinear range-bearing updates and P57 owns general association.
- `experiment.m` uses base MATLAB only. The state prediction, innovation,
  scalar gain, state correction, and Joseph covariance correction are explicit;
  no tracking object, `kalman`, matrix inverse, file, network, or worker is used.
- The reviewed run is bounded to 101 scans, three cases in each sweep, five
  tagged figures, ten filter runs, and 1010 filter steps. Script-local functions
  require MATLAB R2016b or later.

## Completion condition

Most post-warm-up errors and innovations in the reviewed run remain inside the
filter's two-sigma bounds, and you can explain why underestimated `Q` or `R`
makes those bounds overconfident rather than changing physical truth.

## Start

```bash
./bin/learn start 55
```

Run `experiment.m`, follow `walkthrough.md` one figure at a time, and finish
with the teach-back in `checks.md`.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Implement a Constant-Velocity Kalman Filter". The guiding question is: "How do process noise and measurement noise determine trust in prediction versus measurement?" Use this experiment: Track 1-D or 2-D position and velocity with a linear state-space model and noisy measurements. Have me perform these actions: Plot state estimates, covariance bounds, innovations, and Kalman gain. Sweep Q and R and deliberately mismatch each. The main concept I must learn is: The Kalman filter propagates uncertainty and fuses model and measurement according to their covariances. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
