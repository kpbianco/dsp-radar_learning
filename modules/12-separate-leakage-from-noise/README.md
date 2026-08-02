# P12: Separate Leakage from Noise

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Implemented by governed batch `P12`

## Guiding question

Why does a perfectly clean tone spread across many FFT bins?

## Experiment

Observe a noiseless complex sinusoid at 17.35 bins through a finite 128-sample
record. First compare its structured rectangular-window leakage with a separate
seeded noise floor. Then keep the tone and record fixed while explicitly
constructing rectangular, Hann, Hamming, Blackman, and flat-top windows.

The script reports coherent gain, -3 dB main-lobe width in hertz and bins, peak
amplitude error in decibels, and maximum sidelobe level in dBc. A second sweep
moves only the tone's fractional-bin offset from an exact bin to half a bin.
The deliberately broken estimator calls every nonpeak bin "noise" even though
its input is perfectly clean; recovery uses the known components of this
controlled synthetic experiment to isolate the actual seeded noise.

## Procedure

1. Run the clean off-bin baseline and relate its record-boundary jump to its
   stable sidelobe pattern. Compare that with the irregular seeded noise floor.
2. Change only the window. Compare the main-lobe width, peak error, and maximum
   sidelobe metrics rather than declaring one window universally best.
3. Change only the fractional-bin offset. Observe the exact-bin no-leakage
   limiting case and the growing off-peak energy toward half a bin.
4. Run the broken noise estimate, explain why it is nonzero on a noiseless
   input, and verify the synthetic-ground-truth recovery.

## What this should teach

Spectral leakage comes from observing a continuing waveform for only a finite
time. The DFT treats that record as one period, so a noncoherent tone creates an
artificial join and projects onto many bins. That deterministic pattern is not
random noise. Windows reshape it: narrower main lobes help resolve neighbors,
lower sidelobes expose weak signals beside strong ones, and flat-top weighting
favors peak-amplitude accuracy.

## Completion condition

You can select a window based on whether the task is resolving neighbors,
measuring amplitude, or finding weak signals near strong ones, and you can
explain why energy outside the peak bin is not by itself proof of noise.

## Dependencies and execution boundary

- Learning dependency: P11, especially finite-record FFT bins, bin spacing,
  coherent placement, and fractional-bin offset.
- Runtime dependency: base MATLAB only. All five window equations and spectral
  scalings are explicit; no Signal Processing Toolbox helper is required.
- The experiment uses seeded synthetic complex noise from a private stream,
  replaces only figures tagged `P12`, writes no files, and leaves MATLAB's
  global random stream and unrelated figures unchanged.
- Dense zero-padding provides a display/measurement grid only; it is not a
  claim of improved physical resolution. P13 studies that distinction.
- Repository checks are static and use an independent Python model. They do
  not claim MATLAB execution or rendered-figure validation.

## Start

```bash
./bin/learn start 12
```

Follow `walkthrough.md` one observation at a time and use `checks.md` before
recording learner completion.

## Recovery and rollback

If a run is interrupted, press Ctrl+C and rerun the script; it has bounded
loops and no persistent partial output to clean up. To roll back the batch,
remove only P12-owned artifacts, tests, catalog changes, and evidence, then
restore the P12 manifest status to `scaffolded`. Preserve P11 and personal
`.learning/` state.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Separate Leakage from Noise". The guiding question is: "Why does a perfectly clean tone spread across many FFT bins?" Use this experiment: Analyze a noncoherent sinusoid using rectangular, Hann, Hamming, Blackman, and flat-top windows. Have me perform these actions: Keep the tone and record fixed while changing only the window. Compare main-lobe width, peak amplitude error, and sidelobe level on a dB plot. The main concept I must learn is: Spectral leakage comes from finite observation and endpoint discontinuity; windows trade resolution for sidelobe suppression or amplitude accuracy. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md` — module contract and execution boundary
- `experiment.m` — deterministic baseline, two sweeps, broken case, and plots
- `lesson.md` — physical model, equations, limiting cases, and radar meaning
- `walkthrough.md` — observation sequence and recovery
- `checks.md` — prediction, interpretation, and teach-back rubric
