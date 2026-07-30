# P43: Use a Fixed Detection Threshold

**Phase 5: Detection and CFAR**  
**Status:** Scaffolded; implementation batch `P43` is pending

## Guiding question

Why does a threshold that works in one noise level fail in another?

## Experiment

Generate range cells containing Gaussian noise and occasional targets, then detect cells above a fixed threshold.

## Procedure

Set a threshold for one noise variance, then change noise power and clutter background without retuning. Count false alarms and missed detections.

## What this should teach

A fixed amplitude threshold does not maintain constant false-alarm probability when the background level changes.

## Completion condition

You can show false alarms rising or detections disappearing as the background departs from the assumed level.

## Start or implement

```bash
./bin/learn start 43
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P43` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use a Fixed Detection Threshold". The guiding question is: "Why does a threshold that works in one noise level fail in another?" Use this experiment: Generate range cells containing Gaussian noise and occasional targets, then detect cells above a fixed threshold. Have me perform these actions: Set a threshold for one noise variance, then change noise power and clutter background without retuning. Count false alarms and missed detections. The main concept I must learn is: A fixed amplitude threshold does not maintain constant false-alarm probability when the background level changes. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
