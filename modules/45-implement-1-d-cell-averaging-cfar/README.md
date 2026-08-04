# P45: Implement 1-D Cell-Averaging CFAR

**Phase 5: Detection and CFAR**  
**Status:** Implemented by batch `P45`

## Guiding question

How can the threshold adapt to the local noise level?

## Experiment

Create a range profile with slowly varying noise power and several targets, then estimate noise from training cells around each cell under test.

## Procedure

Implement CA-CFAR explicitly with guard cells, training cells, and a scale factor. Plot the profile, local threshold, detections, and excluded edge cells.

## What this should teach

CA-CFAR normalizes the detection threshold to nearby background estimates and maintains approximate Pfa in homogeneous noise.

## Completion condition

The threshold follows the background while remaining separated from target energy by guard cells.

## Run it

```bash
./bin/learn start 45
```

The learner CLI opens the module in tutor mode. Run `experiment.m` in MATLAB,
then use `walkthrough.md` to inspect one figure at a time. The script uses only
base MATLAB operations and a private seeded random stream; it reads no files,
writes no files, calls no services, and changes no global random state.

## What is implemented

- an explicit square-law, 1-D CA-CFAR loop whose leading and lagging training
  cells exclude the cell under test (CUT) and two guard cells per side;
- the exponential-noise scale factor
  `alpha = N * (Pfa^(-1/N) - 1)` for `N = 24` training cells;
- a seeded range profile with a slowly varying local noise-power background,
  three point targets, a following threshold, detections, and visibly excluded
  edge cells;
- two one-variable sweeps: requested false-alarm probability and a uniform
  scene-power scale that demonstrates exact normalized-decision invariance; and
- an intentionally broken dB-domain training average followed by exact recovery
  to the required linear-power arithmetic mean.

## Files

- `experiment.m` — bounded, seeded, sectioned MATLAB experiment with five
  figure groups and retained `results` metrics.
- `lesson.md` — physical model, equations, assumptions, limits, and mistakes.
- `walkthrough.md` — baseline, two sweeps, broken case, and recovery.
- `checks.md` — observation, prediction, interpretation, and teach-back checks.

## Dependencies and scope

P44 supplies conditioned detection and false-alarm probability language, and
P43 supplies the fixed-threshold failure that motivates local adaptation. P41
supplies range-varying background intuition. P45 uses a transparent square-law
power detector and homogeneous exponential-noise CA-CFAR model. It does not
claim exact false-alarm control at clutter edges, with correlated cells, or in
operational radar data; later P46-P52 modules vary reference geometry, compare
CFAR families, stress assumptions, and validate `Pfa` statistically.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Implement 1-D Cell-Averaging CFAR". The guiding question is: "How can the threshold adapt to the local noise level?" Use this experiment: Create a range profile with slowly varying noise power and several targets, then estimate noise from training cells around each cell under test. Have me perform these actions: Implement CA-CFAR explicitly with guard cells, training cells, and a scale factor. Plot the profile, local threshold, detections, and excluded edge cells. The main concept I must learn is: CA-CFAR normalizes the detection threshold to nearby background estimates and maintains approximate Pfa in homogeneous noise. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
