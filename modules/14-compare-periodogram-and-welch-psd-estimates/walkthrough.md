# Walkthrough: Compare Periodogram and Welch PSD Estimates

## Guiding question

Why does averaging make a noise spectrum easier to interpret?

Run `experiment.m` section by section. Read one processing transition or plot
at a time; the goal is estimator behavior, not MATLAB syntax.

## Baseline: one detailed view versus several averaged views

Keep the visible defaults. The same four-second record contains a 1 V tone at
160 Hz, a 0.12 V tone at 172 Hz, and 0.35 V RMS seeded white noise. Before
viewing the baseline, make one prediction: which estimate will have the more
jagged tone-free band?

Inspect the time trace, full-band PSD, and tone zoom.

- The full-record periodogram has 0.25 Hz spacing and preserves the finest
  observation-time detail, but one random realization creates large bin-to-bin
  fluctuations.
- The Welch estimate averages 15 Hann-windowed 512-sample segments. Its 2 Hz
  spacing is coarser, while its tone-free coefficient of variation and dB
  ripple are lower.
- Both axes report `V^2/Hz`. Check the retained power-error fields before
  interpreting heights; the one-sided scaling preserves window-normalized
  power and does not double DC or Nyquist.

Do not conclude that the smoother curve contains more frequency detail. It is
more stable statistically and coarser physically.

## Sweep 1: change only segment length

The first sweep reuses the exact record, Hann definition, 50% overlap, and all
tone/noise controls. Only `M` changes through `[1024 512 256]`.

Expected observations:

1. Frequency spacing grows from 1 to 2 to 4 Hz and the approximate Hann
   main-lobe width grows with it.
2. Complete segment count grows from 7 to 15 to 31, so the tone-free band
   becomes steadier.
3. Weak-tone valley prominence falls in the shortest case even as the noise
   background looks smoother.

This is the governing choice: retain enough segment time for the weakest
feature's separation, then average as much as the remaining data supports.

## Sweep 2: change only overlap

Now `M=512`, the Hann window, record, tones, and FFT spacing remain fixed. Only
overlap changes through 0%, 50%, and 75%.

- Raw segment count grows from 8 to 15 to 29.
- The 2 Hz frequency spacing and physical window response do not move.
- The approximate independent count trails raw `K`, especially at 75%,
  because adjacent windows reuse samples.

Do not promise monotonic improvement from one particular realization. Read
overlap as coverage with correlated reuse, not as free independent data.

## Repeated seeds: separate behavior from luck

The next bounded loop repeats 24 private seeds without changing the signal or
estimator controls. Read the 360 Hz probe plot and the two retained CV values.
The Welch points should cluster more tightly. This is stronger evidence than
judging smoothness from the seed-1014 baseline alone.

## Broken case: average the logarithmic display

The broken path converts each segment PSD to dB and averages those display
values. Its median noise-band level is too low. Classify the failure as an
averaging-domain error: the segment estimates were valid, but the nonlinear
logarithm was applied too early.

Recovery averages the linear `V^2/Hz` rows first and converts once. Verify that
`results.db_averaging_bias_db` is nonnegative and that
`results.recovered_noise_floor_bias_db` is visibly positive. This is Jensen's
inequality appearing in a measurement, not a plotting preference.

## Concept connection

For a Doppler processor, translate the two tones into strong and weak moving
returns and the background into receiver noise or diffuse clutter. A long
segment helps keep nearby velocities distinct. Several segments stabilize the
background estimate. High overlap may use the dwell more evenly but does not
add independent pulses.

State the measurement requirement before selecting `M`: how close are the
features, how weak is the one you care about, and how much noise-floor
uncertainty can the decision tolerate?

## Safe rerun, cancellation, recovery, and rollback

- Every visible control and fixed ceiling is validated before the private seed,
  record, FFT arrays, or figures are created. Malformed, nonfinite, fractional,
  nonprogressing, incomplete-segment, or oversized settings stop early.
- All loops have fixed bounds; there is no input wait, timer, background pool,
  network, file, audio, or hardware operation. Press Ctrl+C to cancel.
- Rerun from the top to recover: private seed 1014 reconstructs the baseline,
  the seed sweep is fixed, the script writes no files, does not alter MATLAB's
  global random stream, and deletes only figures tagged `P14`.
- To roll back the governed implementation, remove only P14-owned module,
  test, catalog, and evidence changes and set only the P14 manifest status to
  `scaffolded`. Preserve P13 and ignored learner progress.

## Expected final explanation

You should be able to say: a periodogram uses one long spectral view and is
high variance; Welch averages shorter segment PSDs in linear power, reducing
random variation while giving up frequency resolution. Segment length controls
that trade, and overlap adds correlated views rather than independent
observation time.
