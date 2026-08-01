# P11: Make FFT Bins Concrete

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Implemented by governed batch `P11`

## Guiding question

What frequency does each FFT bin represent?

## Experiment

Generate complex tones exactly on a bin and at fractional-bin offsets, then
hold the physical tone fixed while changing the record length. The script
labels both zero-based bins and signed frequencies, compares explicit DFT
projections with `fft`, and exposes magnitude and phase in neighboring bins.

## Procedure

1. Run the coherent 64-sample baseline at 1024 samples/s and verify that
   zero-based bin 9 means 144 Hz while MATLAB array index 10 holds that bin.
2. Move the tone through offsets of 0, 0.25, and 0.50 bin without changing the
   sample rate, record, phase, amplitude, or seeded noise realization.
3. Keep the tone at 144 Hz and change only the record length among 32, 64, and
   128 samples. Compare the resulting bin spacing and nearest-bin report.
4. Run the deliberately broken frequency axis, which treats MATLAB's
   one-based array index as the zero-based DFT bin number, then recover with
   `k = index - 1`.

## What this should teach

FFT bins are projections onto discrete complex sinusoids determined jointly by
sample rate and record length. A bin is not a bucket that owns every nearby
frequency: an off-bin tone projects across several basis sinusoids, and phase
is interpretable only where projection magnitude is meaningful.

## Completion condition

You can calculate the expected bin number for a tone and explain what changes
when it lies between bins.

## Dependencies and execution boundary

- Learning dependency: P10, especially sample-rate and finite-record behavior.
- Runtime dependency: base MATLAB only; no toolbox, file, network, audio,
  hardware, or external-data dependency.
- The experiment uses a private seeded stream, replaces only figures tagged
  `P11`, writes no files, and leaves MATLAB's global random stream and unrelated
  figures alone.
- Repository checks are static and independently reproduce the DFT equations;
  they do not claim MATLAB execution or rendered-figure validation.

## Start

```bash
./bin/learn start 11
```

Follow `walkthrough.md` one observation at a time and use `checks.md` before
recording learner completion.

## Recovery and rollback

If a run is interrupted, press Ctrl+C and rerun the script; it has no persistent
partial output to clean up. To roll back the implementation batch, remove only
the P11-owned artifacts and tests/catalog changes and restore the P11 manifest status to `scaffolded`. Do not modify personal `.learning/` state.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Make FFT Bins Concrete". The guiding question is: "What frequency does each FFT bin represent?" Use this experiment: Generate tones exactly on a bin and halfway between bins for several record lengths. Have me perform these actions: Label the bin frequencies, place a coherent tone exactly on one, then move it by fractional-bin offsets. Compare magnitude and phase at neighboring bins. The main concept I must learn is: FFT bins are projections onto discrete complex sinusoids determined jointly by sample rate and record length. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short set of completion checks. End by asking me to explain the result in my own words and suggest one extension that builds on the project.
