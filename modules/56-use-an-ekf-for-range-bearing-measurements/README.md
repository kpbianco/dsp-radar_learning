# P56: Use an EKF for Range-Bearing Measurements

**Phase 6: Radar Tracking and Data Association**  
**Status:** Scaffolded; implementation batch `P56` is pending

## Guiding question

How can nonlinear radar measurements update Cartesian target state?

## Experiment

Simulate a 2-D target measured only by noisy range and azimuth from a fixed radar.

## Procedure

Implement nonlinear measurement prediction and Jacobian. Compare raw polar measurements, Cartesian conversions, EKF trajectory, innovations, and covariance ellipse.

## What this should teach

Nonlinear measurement geometry creates range-dependent uncertainty and requires local linearization or another nonlinear filter.

## Completion condition

The tracker follows the target and the covariance shape changes sensibly with geometry.

## Start or implement

```bash
./bin/learn start 56
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P56` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use an EKF for Range-Bearing Measurements". The guiding question is: "How can nonlinear radar measurements update Cartesian target state?" Use this experiment: Simulate a 2-D target measured only by noisy range and azimuth from a fixed radar. Have me perform these actions: Implement nonlinear measurement prediction and Jacobian. Compare raw polar measurements, Cartesian conversions, EKF trajectory, innovations, and covariance ellipse. The main concept I must learn is: Nonlinear measurement geometry creates range-dependent uncertainty and requires local linearization or another nonlinear filter. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
