# P10: Decimate and Interpolate Without Creating Artifacts

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Implemented by batch `P10`

## Guiding question

Why must filtering accompany sample-rate changes?

## Experiment

Create a two-tone signal, decimate it, then interpolate it back to the original sample rate with and without proper filters.

## Procedure

Place one tone safely inside the new bandwidth and one tone that will alias. Compare naive sample dropping, anti-alias filtering, zero insertion, and reconstruction filtering.

## What this should teach

Decimation narrows the usable bandwidth and interpolation creates spectral images unless filtering is applied.

## Completion condition

You can identify aliasing and interpolation images and show the filtered result removes them.

## Run the lab

```bash
./bin/learn start 10
```

Read `lesson.md`, run `experiment.m`, and follow `walkthrough.md` one figure at
a time. Use `checks.md` for the final interpretation and teach-back.

## Dependencies and compatibility

- Learning dependency: P09 filter behavior, especially passband, stopband, and
  finite FIR delay.
- Runtime dependency: base MATLAB only; no Signal Processing Toolbox, external
  data, network, audio device, or helper package is required.
- The windowed-sinc coefficients, FIR accumulation, sample selection, zero
  insertion, amplitude scaling, and spectral metrics are explicit in the
  script. `decimate`, `downsample`, `upsample`, `interp`, `resample`, `fir1`,
  and `filter` do not hide the operations.

The experiment is deterministic through a private seed-1010 random stream. It
uses finite resource ceilings, writes no files, preserves unrelated figures,
and leaves its metrics in the `results` structure.

## What the figures and metrics expose

1. A 2400-sample/s two-tone record contains a wanted 90 Hz tone and a 420 Hz
   tone that cannot fit after decimation by four.
2. Naive sample dropping folds 420 Hz to 180 Hz. A 65-tap anti-alias FIR removes
   that out-of-band energy before the new 600-sample/s representation is made.
3. Zero insertion returns the sample clock to 2400 samples/s but creates
   spectral images, including the first 90 Hz image at 510 Hz.
4. A reconstruction FIR with gain four suppresses the images and restores the
   retained tone's amplitude.
5. One sweep moves only the high tone across the new Nyquist boundary; another
   changes only reconstruction-filter length.
6. Two deliberately broken paths omit each required filter in turn: naive
   decimation exposes aliasing, and zero insertion without reconstruction
   exposes images. Their filtered comparisons use the same seeded input.

The retained evidence for this batch is in `docs/evidence/P10-2026-08-01.md`.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Decimate and Interpolate Without Creating Artifacts". The guiding question is: "Why must filtering accompany sample-rate changes?" Use this experiment: Create a two-tone signal, decimate it, then interpolate it back to the original sample rate with and without proper filters. Have me perform these actions: Place one tone safely inside the new bandwidth and one tone that will alias. Compare naive sample dropping, anti-alias filtering, zero insertion, and reconstruction filtering. The main concept I must learn is: Decimation narrows the usable bandwidth and interpolation creates spectral images unless filtering is applied. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`

## Rollback

Revert only the P10-owned artifacts and public catalog updates, then restore
P10's manifest status to `scaffolded`. Learner progress under `.learning/` is
personal state and is outside this rollback.
