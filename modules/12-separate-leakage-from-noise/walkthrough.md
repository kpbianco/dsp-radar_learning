# Walkthrough: Separate Leakage from Noise

## Guiding question

Why does a perfectly clean tone spread across many FFT bins?

Run `experiment.m` section by section. Describe one visible cause/effect before
moving on; the goal is the finite-record behavior, not MATLAB syntax.

## Baseline: prove leakage exists without noise

Use the visible defaults: `fs_hz=1024`, `N=128`, and a unit complex tone at
17.35 bins (138.8 Hz). Before viewing the first figure, make one prediction:
will the clean blue trace be a one-bin spike or a repeatable skirt?

Observe the artificial join in the repeated record, then the clean and noisy
rectangular-window spectra.

- The record contains 17.35 cycles, so the periodic join has a visible jump.
- The perfectly clean tone has structured lobes despite zero input noise.
- Adding the 0.02 V RMS seeded noise does not create the leakage shape; it adds
  irregular variation and lifts the low-level floor.

Keep the clean trace as the reference. If its spreading is repeatable and tied
to the tone/window geometry, it is leakage, not a random realization.

## Sweep 1: change only the window

The first loop reuses the identical clean tone, phase, sample rate, and record.
Only `w[n]` changes among rectangular, Hann, Hamming, Blackman, and flat-top.
Read the dBc spectrum and the three metric panels together.

Expected observations:

1. Rectangular has the narrowest -3 dB main lobe but a first sidelobe near
   -13 dBc.
2. Hann, Hamming, and Blackman suppress sidelobes while widening the main lobe.
3. Flat-top has the widest main lobe but the smallest off-bin peak-amplitude
   error after coherent-gain correction.

Do not choose the lowest sidelobe automatically. State the task first:
resolving close equal targets, seeing a weak target near strong clutter, or
measuring one target's amplitude.

## Sweep 2: change only fractional-bin offset

The second loop holds the rectangular window and every physical control fixed
except the offset `[0, 0.20, 0.35, 0.50]` bin.

- At zero offset, the tone completes an integer number of cycles. The boundary
  jump and off-peak energy fraction fall to numerical zero.
- Moving away from the bin creates the boundary mismatch and deterministic
  spreading.
- At half a bin, neither neighboring basis sinusoid matches; more than half of
  the N-point DFT energy lies outside whichever single bin is largest.

This is the limiting-case check: noise never changed, yet leakage moved from
nearly zero to large.

## Broken case: treat nonpeak energy as noise

The broken calculation removes the strongest N-point DFT bin from the clean
off-bin tone and interprets the remaining Parseval energy as a noise RMS.
Inspect the bottom bar plot.

The true clean-input noise is exactly 0 V, but the broken estimate is far above
the actual 0.02 V seeded-noise level. Its arithmetic is not the failure; its
classification is. Deterministic leakage was put in the noise bucket.

## Recovery and concept connection

In this controlled simulation, subtract the known clean component in time or
spectrum. Both routes isolate the same private-seed noise realization, and
Parseval's relation makes the recovered spectral RMS equal the time-domain
RMS. Real measurements rarely provide the exact clean tone, so recover by
combining window-response knowledge, guarded regions, coherent sampling when
possible, and repeated records or averaging.

For a radar Doppler FFT, translate "tone" to strong clutter or a strong target:
its deterministic sidelobes can mask a weak nearby return. For a range FFT,
the same choice trades close-target separation against weak-near-strong
visibility and amplitude accuracy.

## Safe rerun, cancellation, and rollback

- The script validates every control before allocating random data, FFT arrays,
  or figures. Fixed ceilings bound the record, dense FFT, cases, and figures.
- Press Ctrl+C to cancel. Rerun from the top: the private seed recreates the
  noise, no files need cleanup, and only figures tagged `P12` are replaced.
- Editing a control to `NaN`, a complex value, an oversized FFT, a duplicate
  offset, or an unsupported window list fails before signal allocation.
- To roll back the governed implementation, remove only P12-owned module,
  test, catalog, and evidence changes and set only P12 back to `scaffolded`.
  Preserve P11 and ignored learner progress.

## Expected final explanation

You should be able to say: a finite record multiplies the signal by a window,
so the observed spectrum is the tone shaped by that window's response. An
off-bin clean tone therefore leaks deterministically; noise is a separate
random contribution. Window choice trades main-lobe width, sidelobe level, and
amplitude accuracy according to the measurement goal.
