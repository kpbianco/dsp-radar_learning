# P42: Create a Full Range-Doppler Map

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P42` is pending

## Guiding question

How do matched filtering and slow-time FFT combine to separate targets?

## Experiment

Simulate a coherent pulse train containing several targets, clutter, and noise, then apply range compression followed by Doppler FFT.

## Procedure

Display intermediate raw data, range-compressed pulses, slow-time windows, and the final range-Doppler map in dB. Vary CPI length and windowing.

## What this should teach

Range and Doppler processing are separable dimensions whose resolution and sidelobes depend on waveform bandwidth, CPI duration, and windows.

## Completion condition

Every simulated target appears at the expected range and velocity with understandable resolution and sidelobes.

## Start or implement

```bash
./bin/learn start 42
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P42` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Create a Full Range-Doppler Map". The guiding question is: "How do matched filtering and slow-time FFT combine to separate targets?" Use this experiment: Simulate a coherent pulse train containing several targets, clutter, and noise, then apply range compression followed by Doppler FFT. Have me perform these actions: Display intermediate raw data, range-compressed pulses, slow-time windows, and the final range-Doppler map in dB. Vary CPI length and windowing. The main concept I must learn is: Range and Doppler processing are separable dimensions whose resolution and sidelobes depend on waveform bandwidth, CPI duration, and windows. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
