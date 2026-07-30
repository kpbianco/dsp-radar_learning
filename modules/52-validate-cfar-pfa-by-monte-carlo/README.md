# P52: Validate CFAR Pfa by Monte Carlo

**Phase 5: Detection and CFAR**  
**Status:** Scaffolded; implementation batch `P52` is pending

## Guiding question

Does the implemented detector actually achieve the requested false-alarm probability?

## Experiment

Run many noise-only profiles or maps through your CFAR implementation and count tested cells and detections.

## Procedure

Sweep requested Pfa, training-cell count, and noise distribution. Add correlated or non-Gaussian clutter to show model mismatch. Include confidence intervals for the measured rate.

## What this should teach

CFAR is constant only under its assumed statistical model and correct scaling; implementation details can quietly change Pfa.

## Completion condition

Measured Pfa matches theory in homogeneous Gaussian noise and departs predictably under mismatched clutter.

## Start or implement

```bash
./bin/learn start 52
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P52` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Validate CFAR Pfa by Monte Carlo". The guiding question is: "Does the implemented detector actually achieve the requested false-alarm probability?" Use this experiment: Run many noise-only profiles or maps through your CFAR implementation and count tested cells and detections. Have me perform these actions: Sweep requested Pfa, training-cell count, and noise distribution. Add correlated or non-Gaussian clutter to show model mismatch. Include confidence intervals for the measured rate. The main concept I must learn is: CFAR is constant only under its assumed statistical model and correct scaling; implementation details can quietly change Pfa. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
