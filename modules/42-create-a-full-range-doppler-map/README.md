# P42: Create a Full Range-Doppler Map

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by governed batch `P42`

## Guiding question

How do matched filtering and slow-time FFT combine to separate targets?

## Experiment

Simulate a coherent complex-baseband LFM pulse train containing three targets,
stationary clutter, and white noise. Two targets share a range and two share a
velocity. Compress every pulse along fast time with the explicit conjugate
time-reversed waveform, then window and transform every range row along slow
time to form a signed range-Doppler map.

## Procedure

1. Inspect the transmitted chirp and raw fast-time-by-pulse data.
2. Compare one raw pulse with the aligned range-compressed matrix.
3. Inspect rectangular and Hann slow-time windows and a selected range row.
4. Read the final map against the known target ranges and radial velocities.
5. Change only CPI length, then change only the slow-time window.
6. Deliberately take the FFT along the range dimension, diagnose why the result
   is not a range-Doppler map, and restore the slow-time transform.

## What this teaches

Fast-time matched filtering converts echo delay into range response. A
slow-time FFT converts coherent pulse-to-pulse phase into signed Doppler. The
operations act on different matrix dimensions: waveform bandwidth controls
range resolution, CPI duration controls Doppler-bin spacing, and windowing
trades sidelobes for mainlobe width and coherent gain.

## Completion condition

Every simulated target appears within one stated range-resolution cell and one
Doppler bin of its expected range and velocity. You can explain why the two
same-range targets require Doppler processing, why the two same-velocity
targets require range compression, and why the wrong-axis FFT is not a valid
range-Doppler map.

## Dependencies

- [P32: Perform LFM Pulse Compression](../32-perform-lfm-pulse-compression/)
  supplies the conjugate time-reversed matched-filter operation and delay
  alignment.
- [P36: Measure Doppler from Pulse-to-Pulse Phase](../36-measure-doppler-from-pulse-to-pulse-phase/)
  supplies the signed slow-time Doppler relation.
- [P37: Build a Pulse-Doppler Data Matrix](../37-build-a-pulse-doppler-data-matrix/)
  fixes the fast-time rows by slow-time columns convention.
- [P41: Model Ground Clutter and Swerling Targets](../41-model-ground-clutter-and-swerling-targets/)
  distinguishes stationary clutter from independent white noise.

The experiment uses base MATLAB only. It performs no file, network, hardware,
or toolbox I/O and keeps all arrays under explicit resource ceilings.

## Run

```bash
./bin/learn start 42
```

Then run `experiment.m` section by section and use `walkthrough.md` for one
observation at a time. Use `checks.md` before recording personal completion.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Create a Full Range-Doppler Map". The guiding question is: "How do matched filtering and slow-time FFT combine to separate targets?" Use this experiment: Simulate a coherent pulse train containing several targets, clutter, and noise, then apply range compression followed by Doppler FFT. Have me perform these actions: Display intermediate raw data, range-compressed pulses, slow-time windows, and the final range-Doppler map in dB. Vary CPI length and windowing. The main concept I must learn is: Range and Doppler processing are separable dimensions whose resolution and sidelobes depend on waveform bandwidth, CPI duration, and windows. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.
