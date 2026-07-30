# P78: Observe and Correct Range-Cell Migration

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Scaffolded; implementation batch `P78` is pending

## Guiding question

Why does a target move through range bins during a long synthetic aperture?

## Experiment

Use a long aperture or squinted geometry so a point target traces a curved range history.

## Procedure

Plot the target migration before focusing. Compare processing that assumes a fixed range bin with interpolation/backprojection that follows the curved path.

## What this should teach

Changing slant range during aperture collection causes migration that must be compensated for high-resolution SAR.

## Completion condition

The corrected image concentrates energy that was smeared by fixed-bin processing.

## Start or implement

```bash
./bin/learn start 78
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P78` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Observe and Correct Range-Cell Migration". The guiding question is: "Why does a target move through range bins during a long synthetic aperture?" Use this experiment: Use a long aperture or squinted geometry so a point target traces a curved range history. Have me perform these actions: Plot the target migration before focusing. Compare processing that assumes a fixed range bin with interpolation/backprojection that follows the curved path. The main concept I must learn is: Changing slant range during aperture collection causes migration that must be compensated for high-resolution SAR. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
