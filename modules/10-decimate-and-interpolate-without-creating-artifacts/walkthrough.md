# P10 Walkthrough — Decimate and Interpolate Without Creating Artifacts

## Guiding question

Why must filtering accompany sample-rate changes?

## Before running

Open `experiment.m` and leave the baseline controls unchanged. The script uses
base MATLAB, a private seed-1010 random stream, bounded loops, and five P10-only
figure groups. It writes no files and does not close unrelated figures.

The signal begins at 2400 samples/s with a 90 Hz wanted tone and a 420 Hz
out-of-band tone. Decimation by four produces 600 samples/s and a 300 Hz
Nyquist limit. Before looking at the plots, make one prediction: where will
420 Hz appear if every fourth sample is kept without filtering?

## Baseline: observe decimation before interpolation

Run the script and inspect **P10 baseline decimation** only.

1. Confirm the original spectrum has lines near 90 Hz and 420 Hz.
2. In the low-rate spectrum, find the naive red line near 180 Hz. Verify the
   fold calculation \(|420-600|=180\) Hz in the title and console metrics.
3. Compare the filtered blue spectrum. The 90 Hz component remains, while the
   component that would fold to 180 Hz is strongly reduced.
4. Do not call the 180 Hz line “new noise.” It is a deterministic false
   identity caused by representing 420 Hz on a 600-sample/s grid.

Now inspect **P10 baseline interpolation**.

1. The stem trace is the zero-inserted sequence, not a completed waveform.
2. Find the wanted baseband line at 90 Hz and its first image at
   \(600-90=510\) Hz.
3. Compare the reconstructed blue spectrum. The low-pass removes the image and
   its gain of four restores the baseband amplitude toward one volt.
4. Relate the time and frequency views: smoothing the inserted gaps and
   selecting the baseband spectral copy are the same filtering operation.

## Sweep 1: change only the high-tone frequency

Inspect **P10 high-tone sweep**. The sample rates, factor, amplitudes, 90 Hz
tone, FIR, record, and phases stay fixed. Only
`high_tone_sweep_hz = [220 280 340 420]` changes.

- At 220 and 280 Hz, the high tone is still below the 300 Hz new Nyquist
  boundary, so its low-rate frequency has not folded. The 280 Hz case lies in
  the practical filter's transition region and may already be attenuated.
- At 340 Hz, the naive observation turns back to 260 Hz.
- At 420 Hz, it turns back farther to 180 Hz.
- The fixed anti-alias FIR increasingly rejects tones that cannot fit. This is
  why a practical cutoff includes margin below new Nyquist rather than waiting
  for the exact boundary.

This sweep changes frequency, not sample rate or filter design. The bend in
observed frequency is therefore the folding mechanism itself.

## Sweep 2: change only reconstruction-filter length

Inspect **P10 reconstruction sweep**. The zero-stuffed baseline sequence,
interpolation factor, cutoff, sample rates, and window family stay fixed. Only
`reconstruction_tap_sweep = [9 17 33 65]` changes.

- Read the first-image amplitude at 510 Hz. More taps give the low-pass more
  frequency selectivity and drive that image downward.
- Read the recovered 90 Hz amplitude. The factor-of-four coefficient gain is
  present for every case, so a missing amplitude is not confused with image
  rejection.
- Remember the cost: longer FIRs require more multiply-adds and introduce more
  delay. “Longest available” is not automatically the engineering choice.

## Broken case

Inspect **P10 broken case and recovery**. The red paths intentionally perform
naive sample dropping and zero insertion without their filters.

- Failure 1 is irreversible aliasing: the original 420 Hz tone occupies a
  false 180 Hz low-rate bin.
- Failure 2 is interpolation imaging: interpolation images remain at 510 Hz
  and higher.
- The two failures have different ordering. Anti-alias filtering belongs
  before decimation; reconstruction filtering belongs after zero insertion.

If either red result looks acceptable, check the spectrum rather than only the
time trace. A plausible-looking waveform can still contain a false in-band
tone or strong images.

## Recovery and rollback

Restore the baseline controls, keep both explicit FIR sums enabled, and rerun.
The private seed makes the noise repeatable. Early validation occurs before
P10 figures are replaced, so malformed values such as an even tap count, a
cutoff at/above new Nyquist, a noninteger factor, or an excessive record fail
without erasing the last good P10 result.

If a foreground graphics call blocks, use Ctrl+C, close only the affected P10
figure if needed, and rerun. The script has no timer, callback, background job,
network, device, or persistent write to cancel or recover. Repository rollback
means reverting only P10 artifacts/catalog changes and restoring P10 manifest
status to `scaffolded`; it does not change personal `.learning/` state.

## Concept connection and completion handoff

Connect the experiment to a radar channelizer: before lowering the rate, which
analogous energy must be rejected, and what false interpretation could result
if it folds into a target-bearing band? Then use `checks.md`. Completion
requires identifying both the 180 Hz alias and 510 Hz image, explaining the
required filter order, and showing the filtered recovery.
