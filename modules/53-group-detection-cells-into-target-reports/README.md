# P53: Group Detection Cells into Target Reports

**Phase 6: Radar Tracking and Data Association**  
**Status:** Scaffolded; implementation batch `P53` is pending

## Guiding question

How do several threshold-crossing cells become one physical detection?

## Experiment

Create a range-Doppler detection mask containing extended peaks, sidelobes, and isolated noise detections.

## Procedure

Apply local-maximum selection, connected-component grouping, and weighted centroiding. Compare reported range/velocity to the true target center.

## What this should teach

A detector marks cells, while a tracker needs one measurement with position, strength, extent, and uncertainty per target.

## Completion condition

One physical target produces one stable report rather than many neighboring reports.

## Start or implement

```bash
./bin/learn start 53
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P53` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Group Detection Cells into Target Reports". The guiding question is: "How do several threshold-crossing cells become one physical detection?" Use this experiment: Create a range-Doppler detection mask containing extended peaks, sidelobes, and isolated noise detections. Have me perform these actions: Apply local-maximum selection, connected-component grouping, and weighted centroiding. Compare reported range/velocity to the true target center. The main concept I must learn is: A detector marks cells, while a tracker needs one measurement with position, strength, extent, and uncertainty per target. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
