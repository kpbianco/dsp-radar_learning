# P09: Compare FIR and IIR Filters by Behavior

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Implemented by batch `P09`

## Guiding question

How can two filters with similar magnitude response behave differently in time and phase?

## Experiment

Design a modest low-pass FIR and IIR filter with comparable cutoff and apply them to a pulse, step, and noisy multitone signal.

## Procedure

Compare impulse response length, transient behavior, group delay, phase, ringing, and computational order. Run the IIR near an aggressive design to show sensitivity.

## What this should teach

Magnitude response alone does not describe delay, transient shape, stability, or numerical behavior.

## Completion condition

You can choose FIR or IIR based on the signal requirement rather than only filter order.

## Start

```bash
./bin/learn start 9
```

Tutor mode opens the implemented experiment, explanation, walkthrough, and
checks. The experiment uses deterministic synthetic signals and base MATLAB;
it does not require a toolbox, external data, or hardware.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Compare FIR and IIR Filters by Behavior". The guiding question is: "How can two filters with similar magnitude response behave differently in time and phase?" Use this experiment: Design a modest low-pass FIR and IIR filter with comparable cutoff and apply them to a pulse, step, and noisy multitone signal. Have me perform these actions: Compare impulse response length, transient behavior, group delay, phase, ringing, and computational order. Run the IIR near an aggressive design to show sensitivity. The main concept I must learn is: Magnitude response alone does not describe delay, transient shape, stability, or numerical behavior. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
