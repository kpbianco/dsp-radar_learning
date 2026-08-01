# P05 Walkthrough — Inspect One View at a Time

## Guiding question

**What does the word noise hide about time behavior and spectrum?**

Run `experiment.m` with the committed controls first. It uses seed 505 and
keeps each baseline noise record at `0.25 V RMS`. If a plotting environment
blocks, stop the finite script with Ctrl+C, close its figures, restore the
controls, and rerun; no partial file or learner-state cleanup is needed.

## Baseline

### 1. Observe the short time records

Look at only the first figure. Confirm that every title reports the same RMS.
Then identify the additional clue each record exposes:

- Gaussian white noise changes irregularly from sample to sample.
- Low-pass colored noise makes smoother runs because adjacent samples share
  memory.
- Co-channel narrowband interference repeats periodically.
- Impulsive noise spends much of its time near zero and occasionally jumps.

Do not rank the records by a few visible peaks. The RMS control has already
made their average powers equal; the time plot is revealing delivery pattern.

### 2. Compare distributions

Move to the common-edge histograms. White and low-pass colored records can
both look bell-shaped. That is the important observation: a histogram discards
sample order, so it cannot diagnose whiteness. The narrowband sinusoid spends
more samples near its turning points. The impulsive record has a concentrated
center and long tails; the title reports any samples beyond the common view.

### 3. Compare memory

Inspect the normalized autocorrelations. White noise and sparse impulses
should lose most correlation after lag zero. Colored noise should decay
slowly. The narrowband interferer should oscillate because delaying a sinusoid
changes its phase predictably.

Connect the colored trace to the recursion before moving on: `alpha = 0.92`
feeds most of the previous output into the next sample.

### 4. Compare spectra

Inspect the one-sided raw periodograms. Use the axes: frequency is hertz and
PSD is `dB V^2/Hz`.

- White-noise power is broadly spread, though one finite periodogram is jagged.
- Colored-noise power is strongest near DC.
- Narrowband interference occupies the target-frequency line.
- Sparse impulses have broad spectral reach even though their time behavior is
  unlike Gaussian white noise.

Compare the reported fraction of power below 200 Hz. That metric and the
lag-one correlation are different views of the same colored-noise memory.

### 5. Add the same tone

The target is a `0.18 V` peak tone at `512 Hz`. The printed time-domain SNR is
identical in all four panels because each noise RMS is identical. Now compare
the target phasor errors.

The low-pass colored case can preserve the target estimate well because little
of its power reaches 512 Hz. The co-channel interferer produces the worst
ambiguity: the line can look strong while its amplitude and phase are not
trustworthy. This is why “I can see a peak” is not a complete detection claim.

## Sweep 1 — Change only colored-noise memory

The script reuses the same Gaussian driver with

```text
colored_alphas = [0 0.70 0.95]
```

and renormalizes every result to the same `0.25 V RMS`. Observe the PSD overlay
first, then the metric panel.

- At `alpha = 0`, output samples are the independent driver.
- At `alpha = 0.70`, adjacent samples share visible memory.
- At `alpha = 0.95`, the waveform changes slowly and much more power lies
  below 200 Hz.

Only `alpha` changes. RMS, record, driver, and PSD scaling stay fixed. Explain
the paired movement: rising lag-one correlation in time accompanies increasing
low-frequency power concentration.

Restore `colored_alphas = [0 0.70 0.95]` before continuing.

## Sweep 2 — Change only narrowband offset

The same-RMS interferer moves from the target bin to coherent offsets:

```text
interference_offsets_hz = [0 16 128]
```

At zero offset, target and interference project onto the same complex
sinusoid. At 16 and 128 Hz offsets, this one-second rectangular record contains
integer cycles of the difference frequency, so the unwanted sinusoid is
orthogonal to the exact target projection. The plot floor is numerical, not a
promise that arbitrary off-frequency interference never leaks.

Change only the first nonzero offset from `16` to `16.5` and rerun if your
MATLAB environment is available. The coherence assertion will deliberately
reject that edit because the committed comparison depends on integer-bin
orthogonality. Restore `[0 16 128]` afterward. Noncoherent leakage and
windowing are treated in later spectral modules.

## Broken case — Compare unequal raw generator scales

The final figure deliberately skips centering and equal-RMS normalization.
The bar chart should show a large ratio between the loudest and quietest raw
sources. Any tone-error ranking now mixes two variables:

1. how much total power the raw generator happened to produce; and
2. how that power is distributed in time and frequency.

That comparison is invalid for the guiding question. A unit Gaussian sample,
a unit cosine, a smoothed Gaussian process, and a mostly-zero impulse process
do not share a common RMS merely because their source constants look similar.

## Recovery

Recover the fair experiment non-destructively:

1. Restore seed 505 and all baseline controls.
2. Subtract each finite record’s sample mean.
3. Measure centered RMS with `sqrt(mean(x.^2))`.
4. Refuse a zero-RMS record instead of dividing by zero.
5. Rescale each centered record to `noise_rms_target`.
6. Verify the equal-RMS assertion passes before interpreting distribution,
   autocorrelation, PSD, or tone error.

If an input guard fails, restore finite real scalar controls, an even coherent
record of 256 through 16384 samples, 1 through 256 lags smaller than the
record, 16 through 128 histogram bins, coefficients in `[0,1)`, a sparse
impulse probability below `0.25`, and at most eight cases per sweep.

The script writes no files and changes no learner progress, so cancellation
does not require file or learner-state rollback. It uses a private random
stream, does not wholesale-clear the workspace or command window, and closes
only earlier figures tagged as P05 output. Like any script, it creates or
replaces its named working variables, including `results`.
Re-running from the seed recovers the same MATLAB realization. This software
normalization also does
not recover analog or ADC clipping; prevent or repair overload at the
acquisition boundary.

## Concept connection

For a radar or communications receiver, ask four questions after measuring
power:

- Are the amplitudes light-tailed or dominated by outliers?
- How wide is the occupied bandwidth, and does it overlap the target?
- How long does the disturbance remain correlated?
- Can another dimension distinguish a co-channel source?

You are ready for the checks when you can identify all four baseline types
from both time and frequency evidence and explain why equal RMS alone cannot
predict target-tone bias.
