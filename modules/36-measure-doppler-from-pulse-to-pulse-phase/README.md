# P36: Measure Doppler from Pulse-to-Pulse Phase

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P36`

## Guiding question

How does target velocity create coherent phase progression across pulses?

## Experiment

Generate one complex range-bin sample across a coherent train of pulses. The
baseline converts signed radial velocity to Doppler frequency and then to a
phase increment per pulse. It shows the I/Q rotation, unwrapped phase, and a
slow-time Doppler FFT before estimating velocity from both adjacent phase and
the FFT peak.

Three one-variable sweeps expose the physics:

1. signed velocity compares approaching, stationary, and receding targets;
2. carrier frequency changes phase sensitivity at fixed physical velocity;
3. coherent pulse count changes Doppler- and velocity-bin spacing at fixed
   PRF.

The intentionally broken case discards complex phase by taking magnitude
before Doppler processing. Its energy collapses toward zero Doppler and loses
velocity sign. Recovery restores the coherent samples and recreates the
private seeded noise exactly.

## What this teaches

Doppler is phase rotation in slow time. With positive velocity defined as
approaching, a monostatic radar uses

```text
lambda = c / f_c
f_d = 2 v_r / lambda
Delta_phi = 2 pi f_d / PRF
v_r = lambda f_d / 2
```

The phase step is observed modulo `2*pi`, so a fixed PRF gives the
unambiguous Doppler interval `[-PRF/2, PRF/2)`. More coherent pulses refine
the FFT grid; they do not widen that interval.

## Run

From the repository root, run:

```matlab
run('modules/36-measure-doppler-from-pulse-to-pulse-phase/experiment.m')
```

Inspect the six `P36`-tagged figure groups and the `results` structure. The
script is finite, noninteractive, seeded with a private `RandStream`, and
closes only figures tagged `P36`.

## Dependencies and compatibility

- P35 supplies the pulse repetition interval and periodic-pulse context.
- P18 supplies signed positive/negative frequency in complex samples.
- P20 supplies noisy tone phase/frequency estimation language.
- P34 supplies the delay-Doppler mismatch picture.

The transparent path uses base MATLAB complex arithmetic, `unwrap`, and
`fft`; no Phased Array System Toolbox object or Doppler conversion helper is
required. This is a one-range-bin narrowband, constant-velocity simulation,
not a propagation, detector, range-migration, clutter, hardware, HIL, field,
real-time, or operational-radar validation.

## Tutor entry

```bash
./bin/learn start 36
```

Begin with the baseline I/Q and phase plots. Ask which direction the phasor
rotates and where the signed FFT peak lies before changing one control.

## Completion condition

You can predict phase increment per pulse and velocity from the Doppler-bin
location, including the sign convention and the PRF aliasing limit.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Measure Doppler from Pulse-to-Pulse Phase". The guiding question is: "How does target velocity create coherent phase progression across pulses?" Use this experiment: Generate a complex target echo at one range bin across many pulses with controlled Doppler frequency. Have me perform these actions: Plot slow-time I/Q, unwrapped phase, and Doppler FFT. Sweep velocity, carrier frequency, and number of pulses. Compare approaching and receding targets. The main concept I must learn is: Doppler is observed as phase rotation across coherent pulses; sign and rate encode radial velocity. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `experiment.m` — deterministic slow-time simulation, estimates, sweeps,
  failure, and recovery
- `lesson.md` — physical model, limits, and interpretation
- `walkthrough.md` — guided observation and one-variable changes
- `checks.md` — observation, prediction, and teach-back checks
