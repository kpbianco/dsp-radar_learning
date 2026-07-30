# P30: Measure Range from Echo Delay

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P30` is pending

## Guiding question

How does round-trip delay become target range?

## Experiment

Transmit a finite pulse in simulation, insert one or more delayed attenuated echoes, add noise, and estimate delay by correlation.

## Procedure

Convert sample delay to seconds and range. Sweep sample rate and fractional-sample delay. Add a second target and vary separation.

## What this should teach

Monostatic range is c*tau/2, while sampling and waveform shape limit delay estimation precision.

## Completion condition

You can recover target range and explain the factor of two and the sample-quantization error.

## Start or implement

```bash
./bin/learn start 30
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P30` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Measure Range from Echo Delay". The guiding question is: "How does round-trip delay become target range?" Use this experiment: Transmit a finite pulse in simulation, insert one or more delayed attenuated echoes, add noise, and estimate delay by correlation. Have me perform these actions: Convert sample delay to seconds and range. Sweep sample rate and fractional-sample delay. Add a second target and vary separation. The main concept I must learn is: Monostatic range is c*tau/2, while sampling and waveform shape limit delay estimation precision. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
