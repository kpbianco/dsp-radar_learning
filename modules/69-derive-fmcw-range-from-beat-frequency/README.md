# P69: Derive FMCW Range from Beat Frequency

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Implemented by governed batch `P69`

## Guiding question

Why does a delayed chirp produce a nearly constant beat frequency?

## Experiment

Generate one complex-baseband linear FMCW chirp, evaluate an attenuated echo at
the delayed time, multiply transmitted by conjugated received samples over
their valid overlap, and inspect the dechirped FFT. The script makes the mixer
sign, round-trip delay, chirp slope, overlap gate, FFT peak, and range
conversion visible.

## Procedure

Run the deterministic baseline, then change one cause at a time. The first
sweep changes target range with chirp slope fixed. The second changes chirp
slope with target range fixed. Compare transmitted and received instantaneous
frequency, mixer phase, beat spectrum, beat-frequency scaling, and recovered
range. Finally, apply an intentionally wrong one-way conversion, observe the
factor-of-two error, and recover with the monostatic round-trip factor.

## What this teaches

For an ideal stationary target and a linear up-chirp, the delayed echo has the
same frequency ramp as the transmitter but is displaced in time. During valid
overlap their frequency difference is constant:

```text
S = B/T,   tau = 2R/c,   f_b = S tau,   R = c f_b/(2S).
```

The script uses `beat = tx .* conj(rx)`, so a delayed ideal up-chirp produces a
positive beat frequency. That sign is part of the model, not an FFT accident.

## Completion condition

Estimated range follows the known target in the range sweep, beat frequency
scales with chirp slope, and using each case's slope converts those different
beat frequencies back to the same fixed range.

## Run the lesson

```bash
./bin/learn start 69
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P17 supplies complex mixing intuition, P30 connects monostatic delay to range,
P31 separates resolution from estimation accuracy, and P32 supplies linear-FM
phase and bandwidth intuition. P68 is the governed batch prerequisite.

The script requires MATLAB R2016b or newer and no optional toolbox. It uses a
private deterministic generator, explicit complex chirp phase, an overlap
mask rather than circular delay, a base-MATLAB FFT, bounded arrays, and six
tagged figure groups. It writes no file and starts no network request, timer,
worker, or external process.

This is a complex-baseband, single-stationary-target, ideal-linear-chirp model.
It omits Doppler, multipath, leakage, phase noise, ADC quantization, chirp
nonlinearity, propagation loss, and multiple-target resolution. Static tests
and a standard-library numerical oracle do not constitute MATLAB runtime,
rendered-figure, RF, bench, hardware/HIL, real-time, field, or operational-radar
validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Derive FMCW Range from Beat Frequency". The guiding question is: "Why does a delayed chirp produce a nearly constant beat frequency?" Use this experiment: Generate one linear FMCW chirp, delay and attenuate it, mix received with transmitted, and FFT the dechirped beat. Have me perform these actions: Sweep target range and chirp slope. Plot transmitted/received instantaneous frequency, mixer output, beat spectrum, and estimated range. The main concept I must learn is: For a stationary target and ideal linear chirp, beat frequency is proportional to delay and therefore range. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
