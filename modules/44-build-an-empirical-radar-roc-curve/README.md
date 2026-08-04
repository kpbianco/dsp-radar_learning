# P44: Build an Empirical Radar ROC Curve

**Phase 5: Detection and CFAR**  
**Status:** Implemented by batch `P44`

## Guiding question

How does threshold choice trade probability of detection against false alarm?

## Experiment

Run many target-absent and target-present trials for a matched-filter output at several SNR values.

## Procedure

Sweep threshold, estimate Pfa and Pd, and plot ROC curves. Mark one operating point and calculate how many false alarms it implies for a large number of cells.

## What this should teach

ROC curves separate detector quality from a single threshold choice and reveal the operational cost of small Pfa.

## Completion condition

Your Monte Carlo Pfa and Pd are stable and you can select an operating point based on system-level false alarms.

## Run it

```bash
./bin/learn start 44
```

The learner CLI opens the module in tutor mode. Run `experiment.m` in MATLAB,
then use `walkthrough.md` to inspect one figure at a time. The script uses only
base MATLAB operations and a private seeded random stream; it reads no files,
writes no files, calls no services, and changes no global random state.

## What is implemented

- an explicit normalized matched filter for independent target-absent (H0) and
  target-present (H1) trial banks;
- a threshold sweep that estimates `Pfa` and `Pd` at -6, 0, 6, and 12 dB
  matched-filter SNR and compares them with the stated Gaussian model;
- a marked `Pfa = 0.001` operating point and its false-alarm burden across one
  million target-absent searched cells;
- a second sweep showing how finite Monte Carlo trial count controls probability
  resolution and estimate stability; and
- an intentionally broken cherry-pick/tune/score-on-the-same-bank case followed
  by a deterministic independent-bank recovery.

## Files

- `experiment.m` — bounded, seeded, sectioned MATLAB experiment with five
  figure groups and retained `results` metrics.
- `lesson.md` — physical model, equations, limits, and common mistakes.
- `walkthrough.md` — baseline, two sweeps, broken case, and recovery.
- `checks.md` — observation, prediction, interpretation, and teach-back checks.

## Dependencies and scope

P43 supplies the fixed-threshold and conditioned-probability foundation. P27
supplies independent Monte Carlo trial discipline, P24 supplies matched-filter
intuition, and P28 first connects a detector threshold to an ROC. P44 focuses
that foundation on radar operating-point selection and the system cost of
small false-alarm probability. The signed Gaussian detector is deliberately
transparent; it is not a magnitude, power, square-law, CFAR, hardware, or
operational-radar validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build an Empirical Radar ROC Curve". The guiding question is: "How does threshold choice trade probability of detection against false alarm?" Use this experiment: Run many target-absent and target-present trials for a matched-filter output at several SNR values. Have me perform these actions: Sweep threshold, estimate Pfa and Pd, and plot ROC curves. Mark one operating point and calculate how many false alarms it implies for a large number of cells. The main concept I must learn is: ROC curves separate detector quality from a single threshold choice and reveal the operational cost of small Pfa. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.
