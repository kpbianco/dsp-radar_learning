# P54: Build an Alpha-Beta Tracker

**Phase 6: Radar Tracking and Data Association**  
**Status:** Scaffolded; implementation batch `P54` is pending

## Guiding question

How can a simple predictor smooth noisy position while following constant velocity?

## Experiment

Generate one target with constant velocity and noisy scalar position measurements, including occasional dropouts.

## Procedure

Implement predict/update equations explicitly. Sweep alpha and beta, plot estimate, prediction, residual, and lag during a velocity change.

## What this should teach

Alpha-beta tracking balances smoothing and responsiveness using a simplified constant-velocity model.

## Completion condition

You can choose gains that reduce noise without unacceptable lag for the simulated motion.

## Start or implement

```bash
./bin/learn start 54
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P54` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build an Alpha-Beta Tracker". The guiding question is: "How can a simple predictor smooth noisy position while following constant velocity?" Use this experiment: Generate one target with constant velocity and noisy scalar position measurements, including occasional dropouts. Have me perform these actions: Implement predict/update equations explicitly. Sweep alpha and beta, plot estimate, prediction, residual, and lag during a velocity change. The main concept I must learn is: Alpha-beta tracking balances smoothing and responsiveness using a simplified constant-velocity model. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
