# P55: Implement a Constant-Velocity Kalman Filter

**Phase 6: Radar Tracking and Data Association**  
**Status:** Scaffolded; implementation batch `P55` is pending

## Guiding question

How do process noise and measurement noise determine trust in prediction versus measurement?

## Experiment

Track 1-D or 2-D position and velocity with a linear state-space model and noisy measurements.

## Procedure

Plot state estimates, covariance bounds, innovations, and Kalman gain. Sweep Q and R and deliberately mismatch each.

## What this should teach

The Kalman filter propagates uncertainty and fuses model and measurement according to their covariances.

## Completion condition

Most estimation errors remain consistent with predicted uncertainty and you can explain over- and under-confident tuning.

## Start or implement

```bash
./bin/learn start 55
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P55` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Implement a Constant-Velocity Kalman Filter". The guiding question is: "How do process noise and measurement noise determine trust in prediction versus measurement?" Use this experiment: Track 1-D or 2-D position and velocity with a linear state-space model and noisy measurements. Have me perform these actions: Plot state estimates, covariance bounds, innovations, and Kalman gain. Sweep Q and R and deliberately mismatch each. The main concept I must learn is: The Kalman filter propagates uncertainty and fuses model and measurement according to their covariances. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
