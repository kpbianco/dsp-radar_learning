# P71: Expose FMCW Range-Doppler Coupling

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Scaffolded; implementation batch `P71` is pending

## Guiding question

Why can target motion bias the range estimated from one chirp?

## Experiment

Simulate moving targets with a sawtooth FMCW waveform and compare beat frequency to the stationary-target assumption.

## Procedure

Sweep velocity and chirp slope. Calculate the beat contribution from delay and Doppler and plot the resulting range bias.

## What this should teach

A single FMCW beat contains both delay and Doppler terms, so range and velocity are coupled unless multiple chirps or slopes are used.

## Completion condition

You can predict the sign and size of range bias for an approaching or receding target.

## Start or implement

```bash
./bin/learn start 71
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P71` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Expose FMCW Range-Doppler Coupling". The guiding question is: "Why can target motion bias the range estimated from one chirp?" Use this experiment: Simulate moving targets with a sawtooth FMCW waveform and compare beat frequency to the stationary-target assumption. Have me perform these actions: Sweep velocity and chirp slope. Calculate the beat contribution from delay and Doppler and plot the resulting range bias. The main concept I must learn is: A single FMCW beat contains both delay and Doppler terms, so range and velocity are coupled unless multiple chirps or slopes are used. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
