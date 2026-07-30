# P65: Use MVDR/Capon Adaptive Beamforming

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Scaffolded; implementation batch `P65` is pending

## Guiding question

How can a beamformer place data-dependent nulls on interference?

## Experiment

Simulate a weak desired source, strong interferer, and finite snapshots on a ULA.

## Procedure

Estimate covariance, form MVDR weights, and compare patterns/output SINR with conventional beamforming. Sweep snapshot count and diagonal loading.

## What this should teach

MVDR minimizes output power while preserving a chosen direction, but covariance errors can make it unstable.

## Completion condition

The adaptive pattern places a null near the interferer and you can show when loading improves robustness.

## Start or implement

```bash
./bin/learn start 65
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P65` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use MVDR/Capon Adaptive Beamforming". The guiding question is: "How can a beamformer place data-dependent nulls on interference?" Use this experiment: Simulate a weak desired source, strong interferer, and finite snapshots on a ULA. Have me perform these actions: Estimate covariance, form MVDR weights, and compare patterns/output SINR with conventional beamforming. Sweep snapshot count and diagonal loading. The main concept I must learn is: MVDR minimizes output power while preserving a chosen direction, but covariance errors can make it unstable. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
