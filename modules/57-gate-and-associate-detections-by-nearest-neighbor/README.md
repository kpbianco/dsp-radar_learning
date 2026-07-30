# P57: Gate and Associate Detections by Nearest Neighbor

**Phase 6: Radar Tracking and Data Association**  
**Status:** Scaffolded; implementation batch `P57` is pending

## Guiding question

Which measurement should update which track?

## Experiment

Create two or more tracks with clutter detections and noisy target reports.

## Procedure

Predict all tracks, compute measurement residuals and Mahalanobis distances, apply gates, then assign nearest valid measurements. Visualize gates and assignments.

## What this should teach

Association should account for predicted uncertainty, not only Euclidean distance; gating prevents implausible updates.

## Completion condition

Clutter outside the gate is rejected and assignments are correct while targets remain separated.

## Start or implement

```bash
./bin/learn start 57
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P57` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Gate and Associate Detections by Nearest Neighbor". The guiding question is: "Which measurement should update which track?" Use this experiment: Create two or more tracks with clutter detections and noisy target reports. Have me perform these actions: Predict all tracks, compute measurement residuals and Mahalanobis distances, apply gates, then assign nearest valid measurements. Visualize gates and assignments. The main concept I must learn is: Association should account for predicted uncertainty, not only Euclidean distance; gating prevents implausible updates. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
