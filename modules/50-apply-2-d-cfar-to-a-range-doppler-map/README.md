# P50: Apply 2-D CFAR to a Range-Doppler Map

**Phase 5: Detection and CFAR**  
**Status:** Scaffolded; implementation batch `P50` is pending

## Guiding question

How does local thresholding extend from one range profile to two dimensions?

## Experiment

Use the range-Doppler map from Project 42 and build rectangular guard/training windows around each cell.

## Procedure

Implement 2-D CA-CFAR, visualize the threshold surface, and overlay detections. Vary the Doppler and range window sizes independently.

## What this should teach

2-D CFAR adapts to local background in both dimensions but must account for target spread, sidelobes, and map boundaries.

## Completion condition

Targets are detected at expected cells and you understand which border regions are not testable.

## Start or implement

```bash
./bin/learn start 50
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P50` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Apply 2-D CFAR to a Range-Doppler Map". The guiding question is: "How does local thresholding extend from one range profile to two dimensions?" Use this experiment: Use the range-Doppler map from Project 42 and build rectangular guard/training windows around each cell. Have me perform these actions: Implement 2-D CA-CFAR, visualize the threshold surface, and overlay detections. Vary the Doppler and range window sizes independently. The main concept I must learn is: 2-D CFAR adapts to local background in both dimensions but must account for target spread, sidelobes, and map boundaries. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
