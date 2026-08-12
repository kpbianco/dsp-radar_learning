# P71: Expose FMCW Range-Doppler Coupling

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Implemented by governed batch `P71`

## Guiding question

Why can target motion bias the range estimated from one chirp?

## Experiment

Generate one deterministic complex sawtooth-FMCW up-chirp and a delayed,
Doppler-shifted echo. The script dechirps with the established
`tx .* conj(rx)` mixer, measures the signed beat, and displays its delay and
Doppler contributions separately. It compares the true range with the range
obtained by pretending the target is stationary.

## Procedure

Run the baseline from the visible waveform and target controls through the
signed beat estimate. Sweep radial velocity at fixed chirp slope, then sweep
chirp bandwidth (and therefore slope) at fixed velocity. Deliberately apply
the wrong Doppler-correction sign, diagnose the doubled range error, and
recover from the unchanged measured beat using independently supplied
velocity.

## What this teaches

For one up-chirp, positive velocity means approaching and

```text
f_delay = S(2R/c),       f_d = 2v/lambda,
f_beat = f_delay - f_d,  R_stationary = c f_beat/(2S),
range bias = R_stationary - R = -f_c v/S.
```

The beat is one measured number containing two unknown physical terms. An
approaching target lowers this signed beat and appears too near if Doppler is
ignored; a receding target appears too far. Independently known Doppler can
correct the same beat, while a single chirp alone cannot determine both range
and velocity.

## Completion condition

You can predict the sign and size of the stationary-assumption range bias for
an approaching or receding target, explain why steeper chirps reduce it, and
state what independent information is required to remove it.

## Run the lesson

```bash
./bin/learn start 71
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P17 supplies complex mixer-sign intuition, P36 supplies the signed Doppler
law, P69 derives stationary FMCW beat-to-range conversion, and P70 separates
fast- and slow-time processing under a stop-and-hop approximation. P70 is the
governed batch prerequisite.

The script requires MATLAB R2016b or newer and no optional toolbox. It uses
explicit quadratic phase, a manual Hann window, a base-MATLAB FFT, a private
deterministic noise generator, bounded arrays, and six tagged figure groups.
It writes no file and starts no network request, timer, worker, or external
process.

This is a first-order narrowband teaching model: range delay is frozen during
one chirp while carrier Doppler represents constant radial velocity. It omits
within-chirp range migration/stretch, acceleration, multipath, leakage, chirp
nonlinearity, phase noise, antenna effects, ADC quantization, detection, and
calibrated power. P72 introduces opposite slopes as an additional measurement.
Static tests and a standard-library numerical oracle do not constitute MATLAB
runtime, rendered-figure, RF, bench, hardware/HIL, real-time, field, or
operational-radar validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Expose FMCW Range-Doppler Coupling". The guiding question is: "Why can target motion bias the range estimated from one chirp?" Use this experiment: Simulate moving targets with a sawtooth FMCW waveform and compare beat frequency to the stationary-target assumption. Have me perform these actions: Sweep velocity and chirp slope. Calculate the beat contribution from delay and Doppler and plot the resulting range bias. The main concept I must learn is: A single FMCW beat contains both delay and Doppler terms, so range and velocity are coupled unless multiple chirps or slopes are used. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
