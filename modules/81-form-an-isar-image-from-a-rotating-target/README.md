# P81: Form an ISAR Image from a Rotating Target

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Scaffolded; implementation batch `P81` is pending

## Guiding question

How does target rotation create synthetic aperture when the radar is stationary?

## Experiment

Simulate several point scatterers on a rigid target rotating through a small angle while range profiles are collected.

## Procedure

Range-compress each pulse, align translational range motion, then FFT or focus across aspect angle. Change rotation rate and aperture angle.

## What this should teach

ISAR uses target-induced aspect change for cross-range, requiring motion compensation and approximately coherent rotation.

## Completion condition

The scatterer layout becomes recognizable and blurs when translational motion is left uncompensated.

## Start or implement

```bash
./bin/learn start 81
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P81` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Form an ISAR Image from a Rotating Target". The guiding question is: "How does target rotation create synthetic aperture when the radar is stationary?" Use this experiment: Simulate several point scatterers on a rigid target rotating through a small angle while range profiles are collected. Have me perform these actions: Range-compress each pulse, align translational range motion, then FFT or focus across aspect angle. Change rotation rate and aperture angle. The main concept I must learn is: ISAR uses target-induced aspect change for cross-range, requiring motion compensation and approximately coherent rotation. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
