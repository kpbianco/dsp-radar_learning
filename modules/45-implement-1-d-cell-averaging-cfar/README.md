# P45: Implement 1-D Cell-Averaging CFAR

**Phase 5: Detection and CFAR**  
**Status:** Scaffolded; implementation batch `P45` is pending

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

## Start or implement

```bash
./bin/learn start 45
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P45` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Implement 1-D Cell-Averaging CFAR". The guiding question is: "How can the threshold adapt to the local noise level?" Use this experiment: Create a range profile with slowly varying noise power and several targets, then estimate noise from training cells around each cell under test. Have me perform these actions: Implement CA-CFAR explicitly with guard cells, training cells, and a scale factor. Plot the profile, local threshold, detections, and excluded edge cells. The main concept I must learn is: CA-CFAR normalizes the detection threshold to nearby background estimates and maintains approximate Pfa in homogeneous noise. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
