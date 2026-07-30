# P70: Create an FMCW Range-Doppler Map

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Scaffolded; implementation batch `P70` is pending

## Guiding question

How do fast-time beat frequency and chirp-to-chirp phase separate range and velocity?

## Experiment

Simulate many FMCW chirps with several moving targets and arrange dechirped samples as fast time by chirp.

## Procedure

FFT across samples for range, then across chirps for Doppler. Plot intermediate range profiles and the final map. Sweep chirp count and sample count.

## What this should teach

FMCW radar uses within-chirp frequency for range and across-chirp phase for Doppler, analogous to pulse-Doppler fast and slow time.

## Completion condition

Targets appear at expected range/velocity and resolution changes match observation dimensions.

## Start or implement

```bash
./bin/learn start 70
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P70` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Create an FMCW Range-Doppler Map". The guiding question is: "How do fast-time beat frequency and chirp-to-chirp phase separate range and velocity?" Use this experiment: Simulate many FMCW chirps with several moving targets and arrange dechirped samples as fast time by chirp. Have me perform these actions: FFT across samples for range, then across chirps for Doppler. Plot intermediate range profiles and the final map. Sweep chirp count and sample count. The main concept I must learn is: FMCW radar uses within-chirp frequency for range and across-chirp phase for Doppler, analogous to pulse-Doppler fast and slow time. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
