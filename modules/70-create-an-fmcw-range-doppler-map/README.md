# P70: Create an FMCW Range-Doppler Map

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Implemented by governed batch `P70`

## Guiding question

How do fast-time beat frequency and chirp-to-chirp phase separate range and velocity?

## Experiment

Build a deterministic complex dechirped data matrix with fast-time samples in
rows and repeated FMCW chirps in columns. Three ideal point targets are chosen
so one pair shares range and another pair shares velocity. The script exposes
each target's beat tone and slow-time phase, applies an FFT down rows for range,
then an FFT across columns for signed Doppler.

## Procedure

Run the baseline from the visible physical controls through the final map.
Inspect the dechirped matrix, the range-FFT output that still retains chirp
columns, the slow-time phase histories, and the final range-Doppler map. Sweep
the number of coherent chirps, then sweep the number of retained fast-time
samples. Finally, discard complex phase deliberately, observe the invalid
velocity result, and recover on the unchanged complex range data.

## What this teaches

For the reviewed stop-and-hop FMCW model,

```text
f_b = S(2R/c),        f_d = 2v/lambda,
z[n,m] = a exp(j 2 pi (f_b n/fs - f_d m T_r) + j phi).
```

The tone along sample index `n` places a target in range. Under P69's
`tx .* conj(rx)` mixer, an approaching target has negative slow-time phase
rate, so the velocity display reverses the Doppler-frequency sign. A range FFT
preserves the columns; a Doppler FFT then resolves their phase histories.

## Completion condition

All three targets occupy distinct expected range/velocity neighborhoods, the
chirp-count sweep changes Doppler spacing, the retained-sample sweep changes
fast-time observation bandwidth and range spacing, and phase-discarding is
correctly rejected as a range-Doppler processor.

## Run the lesson

```bash
./bin/learn start 70
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P17 supplies complex mixing intuition, P36 supplies signed phase-to-Doppler
conversion, P37 fixes the fast-time-by-slow-time matrix convention, P42 shows
the analogous pulsed-radar map, and P69 derives the ideal FMCW beat-to-range
law. P69 is the governed batch prerequisite.

The script requires MATLAB R2016b or newer and no optional toolbox. It uses
explicit complex exponentials, manual Hann windows, base-MATLAB FFTs, a private
deterministic generator, bounded arrays, and seven tagged figure groups. It
writes no file and starts no network request, timer, worker, or external
process.

This is a complex-baseband dechirped, stop-and-hop, constant-velocity teaching
model. It intentionally omits within-chirp Doppler in the beat term, range
migration, FMCW range-Doppler coupling, transmitter leakage, chirp nonlinearity,
phase noise, multipath, antenna effects, ADC quantization, detection, and
calibrated power. P71 adds the omitted coupling. Static tests and a
standard-library numerical oracle do not constitute MATLAB runtime,
rendered-figure, RF, bench, hardware/HIL, real-time, field, or operational-radar
validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Create an FMCW Range-Doppler Map". The guiding question is: "How do fast-time beat frequency and chirp-to-chirp phase separate range and velocity?" Use this experiment: Simulate many FMCW chirps with several moving targets and arrange dechirped samples as fast time by chirp. Have me perform these actions: FFT across samples for range, then across chirps for Doppler. Plot intermediate range profiles and the final map. Sweep chirp count and sample count. The main concept I must learn is: FMCW radar uses within-chirp frequency for range and across-chirp phase for Doppler, analogous to pulse-Doppler fast and slow time. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
