# P84: Run the End-to-End Radar Processing Capstone

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Scaffolded; implementation batch `P84` is pending

## Guiding question

Can I trace a target from waveform generation through detection and tracking without treating any stage as a black box?

## Experiment

Simulate a configurable radar scene with waveform, targets, clutter, noise, receiver imperfections, matched filtering, range-Doppler processing, CFAR, clustering, and tracking.

## Procedure

Build the chain in explicit stages and save an intermediate plot/data product after each. Include at least one stationary and one moving target, a clutter edge, a weak target beside a strong one, missed detections, and false alarms. Compare at least two waveform or detector choices and summarize performance using Pd, Pfa, RMSE, resolution, and runtime.

## What this should teach

A radar system is a sequence of model-dependent transformations; understanding intermediate data makes failures diagnosable and design tradeoffs visible.

## Completion condition

You can explain every target, artifact, miss, and false alarm by locating the stage where it was created or lost.

## Start or implement

```bash
./bin/learn start 84
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P84` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Run the End-to-End Radar Processing Capstone". The guiding question is: "Can I trace a target from waveform generation through detection and tracking without treating any stage as a black box?" Use this experiment: Simulate a configurable radar scene with waveform, targets, clutter, noise, receiver imperfections, matched filtering, range-Doppler processing, CFAR, clustering, and tracking. Have me perform these actions: Build the chain in explicit stages and save an intermediate plot/data product after each. Include at least one stationary and one moving target, a clutter edge, a weak target beside a strong one, missed detections, and false alarms. Compare at least two waveform or detector choices and summarize performance using Pd, Pfa, RMSE, resolution, and runtime. The main concept I must learn is: A radar system is a sequence of model-dependent transformations; understanding intermediate data makes failures diagnosable and design tradeoffs visible. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
