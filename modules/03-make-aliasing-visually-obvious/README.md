# P03: Make Aliasing Visually Obvious

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Scaffolded; implementation batch `P03` is pending

## Guiding question

Why does a high-frequency tone appear as a lower-frequency tone after sampling?

## Experiment

Sample a swept sinusoid while keeping the sample rate fixed and estimate its apparent discrete-time frequency.

## Procedure

Sweep the input from DC through several multiples of the sample rate. Plot true frequency versus apparent frequency and show representative time sequences near each fold.

## What this should teach

Aliasing is frequency folding around multiples of the sample rate, not random corruption.

## Completion condition

You can predict the alias frequency for a tone above Nyquist.

## Start or implement

```bash
./bin/learn start 3
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P03` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Make Aliasing Visually Obvious". The guiding question is: "Why does a high-frequency tone appear as a lower-frequency tone after sampling?" Use this experiment: Sample a swept sinusoid while keeping the sample rate fixed and estimate its apparent discrete-time frequency. Have me perform these actions: Sweep the input from DC through several multiples of the sample rate. Plot true frequency versus apparent frequency and show representative time sequences near each fold. The main concept I must learn is: Aliasing is frequency folding around multiples of the sample rate, not random corruption. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
