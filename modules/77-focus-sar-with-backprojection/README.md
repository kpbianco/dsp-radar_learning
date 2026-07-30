# P77: Focus SAR with Backprojection

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Scaffolded; implementation batch `P77` is pending

## Guiding question

How does compensating the correct path length focus a point in an image?

## Experiment

Use range-compressed phase history and form an image over a 2-D ground grid by delay/phase compensation and coherent summation.

## Procedure

Show partial images as aperture positions accumulate. Compare correct geometry with a wrong platform height or path. Plot point-target response in range and cross-range.

## What this should teach

Backprojection focuses by aligning each pixel hypothesis with the measured round-trip path across the aperture.

## Completion condition

Point targets focus at correct coordinates and defocus when geometry is intentionally wrong.

## Start or implement

```bash
./bin/learn start 77
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P77` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Focus SAR with Backprojection". The guiding question is: "How does compensating the correct path length focus a point in an image?" Use this experiment: Use range-compressed phase history and form an image over a 2-D ground grid by delay/phase compensation and coherent summation. Have me perform these actions: Show partial images as aperture positions accumulate. Compare correct geometry with a wrong platform height or path. Plot point-target response in range and cross-range. The main concept I must learn is: Backprojection focuses by aligning each pixel hypothesis with the measured round-trip path across the aperture. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
