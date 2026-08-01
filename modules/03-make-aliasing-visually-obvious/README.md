# P03: Make Aliasing Visually Obvious

**Phase 1: Signals, Sampling, and Systems**
**Status:** Implemented by batch `P03`

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

## Dependencies

- Curriculum prerequisite: P02, for samples as timed measurements.
- Runtime: base MATLAB only.
- Toolboxes, external data, helper functions, hardware, and network access: none.

The script writes frequency folding and the sample-recurrence estimator as
explicit arithmetic. Retained outputs include a 700 Hz baseline sampled at
1000 samples/s, an input-frequency sweep from DC through three sample-rate
multiples, representative sequences around folds, a sample-rate sweep, and a
deliberately broken reflected-phase model.

## Start or implement

```bash
./bin/learn start 3
```

Tutor mode uses the runnable experiment, lesson, walkthrough, and checks added
by Portfolio Control batch `P03`.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Make Aliasing Visually Obvious". The guiding question is: "Why does a high-frequency tone appear as a lower-frequency tone after sampling?" Use this experiment: Sample a swept sinusoid while keeping the sample rate fixed and estimate its apparent discrete-time frequency. Have me perform these actions: Sweep the input from DC through several multiples of the sample rate. Plot true frequency versus apparent frequency and show representative time sequences near each fold. The main concept I must learn is: Aliasing is frequency folding around multiples of the sample rate, not random corruption. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
