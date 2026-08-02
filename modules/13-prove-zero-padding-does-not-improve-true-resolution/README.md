# P13: Prove Zero-Padding Does Not Improve True Resolution

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Implemented by governed batch `P13`

## Guiding question

Why does a smoother FFT plot not necessarily contain more information?

## Experiment

Analyze the same 128 measured samples with 1x, 4x, and 16x FFT lengths, then
compare those interpolated views with records containing two and four times as
many measured samples. Two tones separated by 4 Hz deliberately sit inside the
short record's 8 Hz Rayleigh interval but outside the 512-sample record's 2 Hz
interval.

## Procedure

1. Inspect the 128-sample complex record and its 1x, 4x, and 16x spectra.
2. Confirm that display spacing shrinks from 8 Hz to 0.5 Hz while the measured
   samples, 0.125 s duration, and 8 Hz Rayleigh interval do not change.
3. Sweep observation length through 128, 256, and 512 real samples while
   keeping sample rate, tones, amplitudes, phases, and the shared noise prefix
   fixed.
4. Run the broken calculation that calls the 16x display spacing "resolution,"
   then recover by comparing the unchanged short-record response with the
   genuinely longer record.

## What this should teach

Zero-padding evaluates the same finite-record transform on a denser frequency
grid. It can make a peak easier to locate or a curve easier to inspect, but it
does not add independent measurements, narrow the physical main lobe, or
separate tones that the observation duration blends. More measured time can.

## Completion condition

You can distinguish visual frequency-grid density from actual resolving power.

## Dependencies and execution boundary

- Learning dependencies: P11 supplies `f_s/N` bin spacing and P12 supplies the
  finite-record/window response. This experiment uses a rectangular window so
  observation length is the only physical resolution control.
- Runtime dependency: base MATLAB only; no toolbox, file, network, audio,
  hardware, or external-data dependency.
- The private seeded stream produces one longest noise record normalized to
  0.002 V RMS across all 512 samples; shorter cases use unchanged prefixes and
  report their own realized RMS values. The script writes no files, does not
  alter MATLAB's global random stream, and replaces only figures tagged `P13`.
- Repository validation is static and independently reproduces the finite DFT
  equations. It does not claim MATLAB execution or rendered-figure validation.

## Start

```bash
./bin/learn start 13
```

Follow `walkthrough.md` one observation at a time and use `checks.md` before
recording learner completion.

## Recovery and rollback

Press Ctrl+C to cancel and rerun from the top; fixed resource ceilings keep the
work bounded and the private seed recreates the same samples. To roll back the
batch, remove only P13-owned artifacts, tests, catalog changes, and evidence,
then restore only the P13 manifest status to `scaffolded`. Preserve P12 and
ignored `.learning/` progress.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Prove Zero-Padding Does Not Improve True Resolution". The guiding question is: "Why does a smoother FFT plot not necessarily contain more information?" Use this experiment: Analyze one short data record with increasingly large zero-padded FFT lengths and compare it with a genuinely longer observation. Have me perform these actions: Plot the same windowed samples with 1x, 4x, and 16x zero-padding. Then collect four times more real samples and compare two nearby tones. The main concept I must learn is: Zero-padding interpolates the sampled spectrum; longer observation time narrows the physical main lobe and improves separability. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.
