# P66: Estimate DOA with MUSIC

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Scaffolded; implementation batch `P66` is pending

## Guiding question

How can subspace methods resolve sources more finely than a conventional beam?

## Experiment

Simulate multiple uncorrelated narrowband sources and compute the sample covariance eigenspectrum and MUSIC pseudospectrum.

## Procedure

Sweep source spacing, SNR, snapshot count, and assumed source number. Add coherent sources to show failure, then decorrelate with spatial smoothing.

## What this should teach

MUSIC separates signal and noise subspaces and can provide super-resolution when its model assumptions are satisfied.

## Completion condition

You can identify correct peaks and explain failures from source-count error or coherence.

## Start or implement

```bash
./bin/learn start 66
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P66` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Estimate DOA with MUSIC". The guiding question is: "How can subspace methods resolve sources more finely than a conventional beam?" Use this experiment: Simulate multiple uncorrelated narrowband sources and compute the sample covariance eigenspectrum and MUSIC pseudospectrum. Have me perform these actions: Sweep source spacing, SNR, snapshot count, and assumed source number. Add coherent sources to show failure, then decorrelate with spatial smoothing. The main concept I must learn is: MUSIC separates signal and noise subspaces and can provide super-resolution when its model assumptions are satisfied. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
