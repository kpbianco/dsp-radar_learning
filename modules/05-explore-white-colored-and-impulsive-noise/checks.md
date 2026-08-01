# P05 Checks — Observe, Classify, and Explain

## Guiding question

**What does the word noise hide about time behavior and spectrum?**

Use the committed seed and controls. These are interpretation checks, not a
MATLAB syntax quiz.

## Baseline observation checks

Confirm all of the following before changing a parameter:

- all four centered records report `0.25 V RMS` within the script tolerance;
- the impulsive record has the largest crest factor and visible sparse
  outliers;
- the colored record has much stronger lag-one correlation than white noise;
- the colored record places a larger fraction of its power below 200 Hz;
- the narrowband record produces an oscillating autocorrelation and one
  target-frequency spectral line; and
- the time-domain tone SNR is common to all cases, while tone phasor error is
  not.

If any equal-RMS check fails, do not interpret the comparison. Recover using
the normalization procedure in the walkthrough.

## Predict, then verify

1. Increase only `colored_alpha` from `0.70` toward `0.95`. Predict which two
   metrics should rise together. Verify lag-one correlation and the fraction
   of power below 200 Hz both rise while RMS stays fixed.
2. Move the coherent narrowband interferer from zero offset to `16 Hz`.
   Predict whether its own spectral line disappears or merely moves away from
   the target basis. Verify the line remains but target phasor error collapses
   to the numerical floor for the committed coherent record.
3. Keep RMS fixed and make impulses rarer in a separate copy of the script.
   Predict the peak size required to carry similar average power. Rarer events
   generally require a larger crest factor; do not claim an exact monotonic
   result from one random realization.

## Identify from two views

For each unknown record, give one time-domain clue and one frequency-domain or
correlation clue:

1. Bell-shaped amplitudes, irregular samples, near-impulse autocorrelation,
   broad PSD.
2. Smooth runs, decaying autocorrelation, power concentrated near DC.
3. Periodic time record, oscillating autocorrelation, narrow spectral line.
4. Mostly quiet samples with rare peaks, long-tailed histogram, broad spectral
   reach.

The intended classifications are Gaussian white noise, low-pass colored
noise, narrowband interference, and impulsive noise.

## Interpretation checks

Mark each statement true or false and correct the false ones.

- Equal RMS records have equal average power over this finite record.
- Equal RMS records must have equal histograms and equal PSDs.
- A Gaussian-looking histogram proves samples are white.
- Large `alpha` in the one-pole recursion creates longer memory and a more
  low-pass spectrum.
- A target-frequency peak can contain coherent interference as well as target
  energy.
- A raw periodogram is a finite-record estimate, not exact ensemble truth.
- Digitally normalizing an already clipped hardware record repairs its lost
  peaks.

Only the first, fourth, fifth, and sixth statements are true.

## Failure classification

Name the dominant failure and first recovery for each observation:

1. The four generator outputs have visibly different RMS before any type
   comparison.
2. The PSD is flat-ish, but the histogram has rare extreme tails.
3. The histogram is bell-shaped, but adjacent samples and low-frequency power
   are strong.
4. The target bin is tall, yet its estimated phase and amplitude are badly
   biased.
5. The script rejects `alpha = 1` or an impulse record with zero RMS.

The intended classifications are unequal-power confounding, impulsive noise,
colored Gaussian noise, co-channel interference, and undefined normalization.
Recover by equal-RMS centering/scaling, robust outlier handling when justified,
band-aware processing, another separation dimension, or restoring a
nondegenerate bounded source respectively.

## Compatibility, bounds, and recovery check

Verify the script uses base MATLAB and explicit operations: a one-pole loop,
centered RMS scaling, direct lag products, the stated DFT/periodogram scaling,
and a direct coherent projection. It must not rely on `awgn`, `filter`,
`xcorr`, `periodogram`, `pwelch`, a toolbox object, external data, a device, a
network, or an asynchronous worker.

Restore the committed controls and confirm all finite bounds precede dependent
work: at most 16384 samples, 256 lags, 128 histogram bins, eight sweep cases,
and four baseline types. There is no persistent file or learner-state mutation
to roll back and no asynchronous task to cancel. The script must preserve the
global random stream and unrelated figures, and it must not wholesale-clear
the workspace or command window. Its named working variables may be created or
replaced. If execution is interrupted, close P05 figures if needed and rerun
from seed 505.

## Teach-back completion

In two or three sentences, answer:

**What does the word noise hide about time behavior and spectrum?**

A satisfactory answer:

- says RMS describes average power but not distribution, bandwidth,
  correlation, or impulsiveness;
- distinguishes white, low-pass colored, narrowband, and impulsive cases using
  both time/correlation and frequency evidence;
- explains why the same tone can be easier or less trustworthy under
  equal-RMS disturbances; and
- states why fair type comparison requires centering and equal-RMS scaling
  without pretending normalization can repair acquisition clipping.
