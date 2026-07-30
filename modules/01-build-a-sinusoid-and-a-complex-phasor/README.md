# P01: Build a Sinusoid and a Complex Phasor

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Implemented reference module

## Guiding question

How do amplitude, frequency, and phase appear in time and in the complex plane?

## Experiment

Generate one real cosine and one complex exponential with the same amplitude, frequency, and phase. Plot real/imaginary parts and animate or sample the complex phasor.

## Procedure

Change amplitude, phase, and frequency one at a time. Compare a positive-frequency complex exponential with a negative-frequency one. Plot several cycles and the corresponding IQ trajectory.

## What this should teach

A real sinusoid is the projection of rotating complex motion; phase is an initial angle and frequency is rotation rate.

## Completion condition

You can predict the time plot and IQ rotation direction before running the script.

## Start or implement

```bash
./bin/learn start 1
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P01` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build a Sinusoid and a Complex Phasor". The guiding question is: "How do amplitude, frequency, and phase appear in time and in the complex plane?" Use this experiment: Generate one real cosine and one complex exponential with the same amplitude, frequency, and phase. Plot real/imaginary parts and animate or sample the complex phasor. Have me perform these actions: Change amplitude, phase, and frequency one at a time. Compare a positive-frequency complex exponential with a negative-frequency one. Plot several cycles and the corresponding IQ trajectory. The main concept I must learn is: A real sinusoid is the projection of rotating complex motion; phase is an initial angle and frequency is rotation rate. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
- `LEARNER_NOTES.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
