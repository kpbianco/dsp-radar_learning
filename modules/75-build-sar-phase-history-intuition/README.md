# P75: Build SAR Phase-History Intuition

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Scaffolded; implementation batch `P75` is pending

## Guiding question

Why does moving one antenna create a large synthetic aperture?

## Experiment

Simulate a monostatic radar moving along a straight track past one point target and record complex phase versus platform position and fast time.

## Procedure

Plot slant range, round-trip phase, and raw phase history. Change target cross-range position and aperture length.

## What this should teach

SAR cross-range information is encoded in coherent phase curvature collected from many platform positions.

## Completion condition

You can explain why two targets at the same range can have different aperture-phase histories.

## Start or implement

```bash
./bin/learn start 75
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P75` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build SAR Phase-History Intuition". The guiding question is: "Why does moving one antenna create a large synthetic aperture?" Use this experiment: Simulate a monostatic radar moving along a straight track past one point target and record complex phase versus platform position and fast time. Have me perform these actions: Plot slant range, round-trip phase, and raw phase history. Change target cross-range position and aperture length. The main concept I must learn is: SAR cross-range information is encoded in coherent phase curvature collected from many platform positions. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
