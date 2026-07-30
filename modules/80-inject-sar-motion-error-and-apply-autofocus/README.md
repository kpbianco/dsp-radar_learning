# P80: Inject SAR Motion Error and Apply Autofocus

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Scaffolded; implementation batch `P80` is pending

## Guiding question

How small a platform-position error is enough to blur a coherent image?

## Experiment

Add smooth and random path errors to SAR phase history before focusing.

## Procedure

Sweep error magnitude in fractions of wavelength. Observe image blur and phase error, then apply a simple phase-gradient or entropy-minimization autofocus concept to estimate a correction.

## What this should teach

SAR is highly phase-sensitive; navigation error becomes spatially coherent defocus that autofocus can partly remove from strong scene structure.

## Completion condition

You can show the image degrading with motion error and materially improving after estimated phase correction.

## Start or implement

```bash
./bin/learn start 80
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P80` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Inject SAR Motion Error and Apply Autofocus". The guiding question is: "How small a platform-position error is enough to blur a coherent image?" Use this experiment: Add smooth and random path errors to SAR phase history before focusing. Have me perform these actions: Sweep error magnitude in fractions of wavelength. Observe image blur and phase error, then apply a simple phase-gradient or entropy-minimization autofocus concept to estimate a correction. The main concept I must learn is: SAR is highly phase-sensitive; navigation error becomes spatially coherent defocus that autofocus can partly remove from strong scene structure. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
