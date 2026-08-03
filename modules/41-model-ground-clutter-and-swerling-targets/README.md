# P41: Model Ground Clutter and Swerling Targets

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P41`

## Guiding question

Why do clutter and target amplitude fluctuate differently from white noise?

## Experiment

Create range-dependent clutter with spatial correlation and target amplitudes
following several simple Swerling-like fluctuation models.

## Procedure

Plot amplitude histograms, correlation, and pulse-to-pulse variation. Compare
detection stability for a nonfluctuating target and fluctuating targets at
equal average SNR.

## What this teaches

Radar backgrounds and targets often have structured, non-Gaussian, and
correlated statistics that change detector performance. Equal average power
does not imply equal dwell-to-dwell reliability.

## Completion condition

You can distinguish thermal noise, correlated clutter, and target fluctuation
in simulated data.

## Prerequisite

Complete [P40: Compare Coherent and Noncoherent Integration](../40-compare-coherent-and-noncoherent-integration/)
first. P41 uses P40's phase-insensitive pulse-power average, then changes the
background and target-amplitude statistics that feed that operation.

## Run the experiment

From MATLAB, change to this directory and run:

```matlab
experiment
```

The base-MATLAB script uses private seed `4101`, explicit correlated-field and
Swerling-power equations, bounded arrays, and six tagged figure groups. No
toolbox is required. Work through [lesson.md](lesson.md),
[walkthrough.md](walkthrough.md), and [checks.md](checks.md) alongside the
figures.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Model Ground Clutter and Swerling Targets". The guiding question is: "Why do clutter and target amplitude fluctuate differently from white noise?" Use this experiment: Create range-dependent clutter with spatial correlation and target amplitudes following several simple Swerling-like fluctuation models. Have me perform these actions: Plot amplitude histograms, correlation, and pulse-to-pulse variation. Compare detection stability for a nonfluctuating target and fluctuating targets at equal average SNR. The main concept I must learn is: Radar backgrounds and targets often have structured, non-Gaussian, and correlated statistics that change detector performance. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `experiment.m` — deterministic clutter and fluctuating-target experiment
- `lesson.md` — physical model, equations, limiting cases, and model boundary
- `walkthrough.md` — baseline, two one-variable sweeps, broken case, and recovery
- `checks.md` — observation, interpretation, prediction, and teach-back checks
