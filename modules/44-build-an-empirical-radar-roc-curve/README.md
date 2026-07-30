# P44: Build an Empirical Radar ROC Curve

**Phase 5: Detection and CFAR**  
**Status:** Scaffolded; implementation batch `P44` is pending

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

## Start or implement

```bash
./bin/learn start 44
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P44` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build an Empirical Radar ROC Curve". The guiding question is: "How does threshold choice trade probability of detection against false alarm?" Use this experiment: Run many target-absent and target-present trials for a matched-filter output at several SNR values. Have me perform these actions: Sweep threshold, estimate Pfa and Pd, and plot ROC curves. Mark one operating point and calculate how many false alarms it implies for a large number of cells. The main concept I must learn is: ROC curves separate detector quality from a single threshold choice and reveal the operational cost of small Pfa. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
