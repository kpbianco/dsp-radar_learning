# P46: Vary CFAR Guard and Training Cells

**Phase 5: Detection and CFAR**  
**Status:** Scaffolded; implementation batch `P46` is pending

## Guiding question

What happens when the CFAR reference window is too small, too large, or contaminated?

## Experiment

Use a strong target with realistic sidelobes and a background whose level changes gradually with range.

## Procedure

Sweep guard-cell and training-cell counts. Show target self-masking with too few guards, noisy threshold estimates with too few training cells, and poor locality with too many.

## What this should teach

CFAR window design balances estimator variance, target leakage protection, and adaptation to local background.

## Completion condition

You can justify a window size based on target extent, sidelobes, and expected clutter variation.

## Start or implement

```bash
./bin/learn start 46
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P46` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Vary CFAR Guard and Training Cells". The guiding question is: "What happens when the CFAR reference window is too small, too large, or contaminated?" Use this experiment: Use a strong target with realistic sidelobes and a background whose level changes gradually with range. Have me perform these actions: Sweep guard-cell and training-cell counts. Show target self-masking with too few guards, noisy threshold estimates with too few training cells, and poor locality with too many. The main concept I must learn is: CFAR window design balances estimator variance, target leakage protection, and adaptation to local background. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
