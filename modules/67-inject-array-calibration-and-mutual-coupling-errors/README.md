# P67: Inject Array Calibration and Mutual-Coupling Errors

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Scaffolded; implementation batch `P67` is pending

## Guiding question

How sensitive are beamforming and DOA results to imperfect channels?

## Experiment

Apply random per-element gain/phase errors, element position errors, and a simple coupling matrix to simulated array data.

## Procedure

Compare conventional, MVDR, and MUSIC outputs before and after error. Estimate calibration using a known source and compensate the channel errors.

## What this should teach

Array algorithms depend on the steering-vector model; small channel errors can bias angles, raise sidelobes, and destroy adaptive nulls.

## Completion condition

Calibration materially restores the known-source angle and beam-pattern quality.

## Start or implement

```bash
./bin/learn start 67
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P67` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Inject Array Calibration and Mutual-Coupling Errors". The guiding question is: "How sensitive are beamforming and DOA results to imperfect channels?" Use this experiment: Apply random per-element gain/phase errors, element position errors, and a simple coupling matrix to simulated array data. Have me perform these actions: Compare conventional, MVDR, and MUSIC outputs before and after error. Estimate calibration using a known source and compensate the channel errors. The main concept I must learn is: Array algorithms depend on the steering-vector model; small channel errors can bias angles, raise sidelobes, and destroy adaptive nulls. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
