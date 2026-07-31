# P02: See Sampling as Taking Measurements

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Implemented by batch `P02`

## Guiding question

What information is lost when a continuous-looking signal is represented by discrete samples?

## Experiment

Create a dense reference sinusoid and overlay sample markers taken at several sample rates.

## Procedure

Use sample rates far above, near, and below twice the signal frequency. Reconstruct visually with interpolation and compare the samples to multiple continuous sinusoids that pass through them.

## What this should teach

Samples do not contain the line between points; the sample rate determines which underlying frequencies remain distinguishable.

## Completion condition

You can explain why two different continuous signals can produce the same sample sequence.

## Dependencies

- Curriculum prerequisite: P01, for sinusoid frequency and phase.
- Runtime: base MATLAB only.
- Toolboxes, external data, helper functions, hardware, and network access: none.

The script writes the sampling equation explicitly, constructs its
piecewise-linear interpolation from neighboring measurements, and proves that
5, 7, and 19 Hz continuous sinusoids share one 12 samples/s sequence. Retained
outputs include labeled baseline and interpolation views, a sample-rate sweep,
a measurement-clock-offset sweep, and one deliberately undersampled case.

## Start or implement

```bash
./bin/learn start 2
```

Tutor mode uses the runnable experiment, lesson, walkthrough, and checks added
by Portfolio Control batch `P02`.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "See Sampling as Taking Measurements". The guiding question is: "What information is lost when a continuous-looking signal is represented by discrete samples?" Use this experiment: Create a dense reference sinusoid and overlay sample markers taken at several sample rates. Have me perform these actions: Use sample rates far above, near, and below twice the signal frequency. Reconstruct visually with interpolation and compare the samples to multiple continuous sinusoids that pass through them. The main concept I must learn is: Samples do not contain the line between points; the sample rate determines which underlying frequencies remain distinguishable. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
