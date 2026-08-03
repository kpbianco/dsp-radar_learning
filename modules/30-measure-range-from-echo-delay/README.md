# P30: Measure Range from Echo Delay

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P30`

## Guiding question

How does round-trip delay become target range?

## Experiment

Transmit a finite pulse in simulation, insert delayed attenuated echoes without
circular wraparound, add seeded noise, and estimate delay with an explicit
correlation.

## Procedure

Convert sample lag to seconds and monostatic range. Sweep sample rate while
holding physical delay fixed, sweep fractional-sample delay, then add a second
target and vary only its separation.

## What this should teach

Monostatic range is `c*tau/2`. Sampling places the integer estimate on range
bins, interpolation can refine the peak without creating new waveform
bandwidth, and a finite pulse can merge nearby echoes.

## Completion condition

You can recover target range, explain the factor of two, bound integer-lag
sample quantization error, and distinguish a merged two-target response from a
single-target accuracy error.

## Start

```bash
./bin/learn start 30
```

Tutor mode can now use the runnable experiment, explanation, guided parameter
changes, broken case, and checks in this folder.

## Dependencies

- Conceptual: P08's explicit correlation locates a delayed known waveform;
  P29 establishes why echo amplitude can become small with range.
- Runtime: base MATLAB (MATLAB R2018b or newer for `xline`/`yline` plotting);
  no toolbox, external data, hardware, network, worker, or timer is required.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Measure Range from Echo Delay". The guiding question is: "How does round-trip delay become target range?" Use this experiment: Transmit a finite pulse in simulation, insert one or more delayed attenuated echoes, add noise, and estimate delay by correlation. Have me perform these actions: Convert sample delay to seconds and range. Sweep sample rate and fractional-sample delay. Add a second target and vary separation. The main concept I must learn is: Monostatic range is c*tau/2, while sampling and waveform shape limit delay estimation precision. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m` — explicit echo insertion, correlation, ranging, sweeps, failure, and recovery
- `lesson.md` — physical model, sampling limits, assumptions, and interpretation
- `walkthrough.md` — baseline, controlled changes, two-target case, and recovery
- `checks.md` — observation, prediction, failure, and teach-back checks
