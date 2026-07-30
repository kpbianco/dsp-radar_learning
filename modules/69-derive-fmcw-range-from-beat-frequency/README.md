# P69: Derive FMCW Range from Beat Frequency

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Scaffolded; implementation batch `P69` is pending

## Guiding question

Why does a delayed chirp produce a nearly constant beat frequency?

## Experiment

Generate one linear FMCW chirp, delay and attenuate it, mix received with transmitted, and FFT the dechirped beat.

## Procedure

Sweep target range and chirp slope. Plot transmitted/received instantaneous frequency, mixer output, beat spectrum, and estimated range.

## What this should teach

For a stationary target and ideal linear chirp, beat frequency is proportional to delay and therefore range.

## Completion condition

Estimated range follows the known target and scales correctly with chirp slope.

## Start or implement

```bash
./bin/learn start 69
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P69` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Derive FMCW Range from Beat Frequency". The guiding question is: "Why does a delayed chirp produce a nearly constant beat frequency?" Use this experiment: Generate one linear FMCW chirp, delay and attenuate it, mix received with transmitted, and FFT the dechirped beat. Have me perform these actions: Sweep target range and chirp slope. Plot transmitted/received instantaneous frequency, mixer output, beat spectrum, and estimated range. The main concept I must learn is: For a stationary target and ideal linear chirp, beat frequency is proportional to delay and therefore range. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
