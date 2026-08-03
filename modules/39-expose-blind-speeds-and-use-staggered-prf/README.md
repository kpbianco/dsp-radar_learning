# P39: Expose Blind Speeds and Use Staggered PRF

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P39`

## Guiding question

Why can a moving target vanish in an MTI radar?

## Experiment

Sweep target velocity through the frequency response of an MTI canceller for one PRF, then repeat with a second PRF.

## Procedure

Plot output amplitude versus velocity and mark blind-speed nulls. Combine detections or amplitudes from staggered PRFs and show coverage improvement.

## What this teaches

Blind speeds occur when Doppler phase repeats at the canceller null; staggered PRFs move the nonzero nulls so they do not coincide. A target at the first blind speed of the 4.0 kHz dwell is recovered by a separately processed 5.3 kHz dwell. The zero-velocity clutter notch remains common and intentional.

## Completion condition

You can calculate the first blind speed and demonstrate recovery using another PRF.

## Prerequisite

Complete [P38: Implement a Two-Pulse and Three-Pulse MTI Canceller](../38-implement-a-two-pulse-and-three-pulse-mti-canceller/) first. P39 uses P38's explicit slow-time subtraction, `x[n] - x[n-1]`, and follows its Doppler response across multiple PRFs.

## Run the experiment

From MATLAB, change to this directory and run:

```matlab
experiment
```

The base-MATLAB script uses a private seeded random stream, bounded arrays, explicit difference equations, and five tagged figure groups. No toolbox is required. Work through [lesson.md](lesson.md), [walkthrough.md](walkthrough.md), and [checks.md](checks.md) alongside the figures.

## Files

- `experiment.m` — deterministic blind-speed and staggered-PRF experiment
- `lesson.md` — physical model, equations, limits, and interpretation cautions
- `walkthrough.md` — baseline, two one-variable sweeps, broken case, and recovery
- `checks.md` — observation, prediction, and teach-back checks

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Expose Blind Speeds and Use Staggered PRF". The guiding question is: "Why can a moving target vanish in an MTI radar?" Use this experiment: Sweep target velocity through the frequency response of an MTI canceller for one PRF, then repeat with a second PRF. Have me perform these actions: Plot output amplitude versus velocity and mark blind-speed nulls. Combine detections or amplitudes from staggered PRFs and show coverage improvement. The main concept I must learn is: Blind speeds occur when Doppler phase repeats at the canceller null; staggered PRFs move the nulls so they do not coincide. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.
