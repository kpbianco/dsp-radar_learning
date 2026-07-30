# P37: Build a Pulse-Doppler Data Matrix

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P37` is pending

## Guiding question

What are fast time and slow time in a radar data block?

## Experiment

Simulate several pulsed-radar targets with independent ranges and velocities and arrange samples as fast-time by pulse.

## Procedure

Plot selected pulses, selected range bins across pulses, and the matrix magnitude. Label which dimension contains delay/range and which contains Doppler history.

## What this should teach

Pulse-Doppler processing separates within-pulse delay from pulse-to-pulse phase evolution.

## Completion condition

You can trace one target through raw data to its range bin and slow-time sinusoid.

## Start or implement

```bash
./bin/learn start 37
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P37` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build a Pulse-Doppler Data Matrix". The guiding question is: "What are fast time and slow time in a radar data block?" Use this experiment: Simulate several pulsed-radar targets with independent ranges and velocities and arrange samples as fast-time by pulse. Have me perform these actions: Plot selected pulses, selected range bins across pulses, and the matrix magnitude. Label which dimension contains delay/range and which contains Doppler history. The main concept I must learn is: Pulse-Doppler processing separates within-pulse delay from pulse-to-pulse phase evolution. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
