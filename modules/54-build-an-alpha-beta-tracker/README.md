# P54: Build an Alpha-Beta Tracker

**Phase 6: Radar Tracking and Data Association**  
**Status:** Implemented by batch `P54`

## Guiding question

How can a simple predictor smooth noisy position while following constant velocity?

## Experiment

Generate one target with noisy scalar position measurements, a reviewed
constant-velocity segment, a deliberate velocity change, and two bounded
measurement-dropout intervals. Compare raw measurements, one-step predictions,
corrected position, estimated velocity, innovations, and motion-model lag.

## Procedure

Implement the predict/update equations explicitly. Coast on prediction during
dropouts, sweep alpha and beta one at a time, and compare a broken zero-beta
position smoother with the recovered tracker.

## What this should teach

Alpha-beta tracking balances measurement smoothing against motion-change
responsiveness using a transparent constant-velocity predictor. Alpha corrects
position, beta corrects velocity, and neither gain creates information while a
radar report is absent.

## Dependencies and compatibility

- P53 is the direct implemented prerequisite: it turns detector cells into one
  position report per target. P54 assumes one already-associated scalar report
  per scan and does not claim to solve general data association.
- P27 motivates labeling this single seeded realization honestly rather than
  treating it as Monte Carlo performance evidence.
- P55 will replace fixed alpha and beta with covariance-derived Kalman gains;
  this module keeps the simpler fixed-gain mechanism visible.
- `experiment.m` uses base MATLAB only. Prediction, innovation, correction,
  dropout coasting, metrics, and sweeps are explicit; no Tracking Toolbox
  filter or object is required.
- The reviewed run is bounded to 81 scans, three cases per sweep, five tagged
  figures, and 729 tracker steps. It performs no file, network, shell, timer,
  worker, or learner-state operation.

## Completion condition

You can choose gains that reduce position noise without unacceptable lag after
the simulated velocity change, and explain why prediction rather than a fake
zero measurement is the correct action during a dropout.

## Start

```bash
./bin/learn start 54
```

Run `experiment.m`, then follow `walkthrough.md` one transition at a time and
finish with the short teach-back in `checks.md`.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build an Alpha-Beta Tracker". The guiding question is: "How can a simple predictor smooth noisy position while following constant velocity?" Use this experiment: Generate one target with constant velocity and noisy scalar position measurements, including occasional dropouts. Have me perform these actions: Implement predict/update equations explicitly. Sweep alpha and beta, plot estimate, prediction, residual, and lag during a velocity change. The main concept I must learn is: Alpha-beta tracking balances smoothing and responsiveness using a simplified constant-velocity model. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
