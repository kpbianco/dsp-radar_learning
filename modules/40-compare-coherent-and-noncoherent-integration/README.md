# P40: Compare Coherent and Noncoherent Integration

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P40`

## Guiding question

When should pulse phases be added and when should magnitudes be added?

## Experiment

Simulate repeated weak target returns with controlled phase coherence and noise.

## Procedure

Sum complex samples coherently, sum magnitudes or powers noncoherently, and compare output SNR versus number of pulses. Add phase jitter to break coherence.

## What this teaches

Coherent integration gives greater gain when phase is predictable. Power integration adds phase-insensitive evidence and is therefore more tolerant, but it separates target-present from noise-only data less efficiently.

## Completion condition

You can show the integration-gain trend and identify when phase errors destroy coherent benefit.

## Prerequisite

Complete [P39: Expose Blind Speeds and Use Staggered PRF](../39-expose-blind-speeds-and-use-staggered-prf/) first. P40 uses P39's distinction between processing samples coherently inside a dwell and combining evidence noncoherently when a trustworthy common phase reference is unavailable.

## Run the experiment

From MATLAB, change to this directory and run:

```matlab
experiment
```

The base-MATLAB script uses a private seeded random stream, bounded arrays, explicit complex and power sums, and four tagged figure groups. No toolbox is required. Work through [lesson.md](lesson.md), [walkthrough.md](walkthrough.md), and [checks.md](checks.md) alongside the figures.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Compare Coherent and Noncoherent Integration". The guiding question is: "When should pulse phases be added and when should magnitudes be added?" Use this experiment: Simulate repeated weak target returns with controlled phase coherence and noise. Have me perform these actions: Sum complex samples coherently, sum magnitudes or powers noncoherently, and compare output SNR versus number of pulses. Add phase jitter to break coherence. The main concept I must learn is: Coherent integration gives greater gain when phase is predictable; noncoherent integration is more tolerant but less efficient. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `experiment.m` — deterministic coherent/noncoherent integration experiment
- `lesson.md` — physical model, equations, limiting cases, and interpretation cautions
- `walkthrough.md` — baseline, two one-variable sweeps, broken case, and recovery
- `checks.md` — observation, prediction, and teach-back checks
