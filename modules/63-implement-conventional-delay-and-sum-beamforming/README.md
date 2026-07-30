# P63: Implement Conventional Delay-and-Sum Beamforming

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Scaffolded; implementation batch `P63` is pending

## Guiding question

How does steering align one direction and misalign others?

## Experiment

Simulate two narrowband sources plus sensor noise on a ULA and scan conventional beamformer power versus angle.

## Procedure

Change source separation, SNR, snapshot count, and array size. Compare a single snapshot with covariance averaging.

## What this should teach

Beamforming coherently sums the desired spatial phase pattern while partially canceling mismatched directions.

## Completion condition

The scan peaks near the source angles when the array has enough aperture and SNR.

## Start or implement

```bash
./bin/learn start 63
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P63` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Implement Conventional Delay-and-Sum Beamforming". The guiding question is: "How does steering align one direction and misalign others?" Use this experiment: Simulate two narrowband sources plus sensor noise on a ULA and scan conventional beamformer power versus angle. Have me perform these actions: Change source separation, SNR, snapshot count, and array size. Compare a single snapshot with covariance averaging. The main concept I must learn is: Beamforming coherently sums the desired spatial phase pattern while partially canceling mismatched directions. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
