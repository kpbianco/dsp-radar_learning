# Lesson: adaptation spends SNR to learn the background

## Start with the physical comparison

Both detectors observe the same square-law CUT power. The ideal detector is
given the true mean noise power, normalized here to one. CA-CFAR must estimate
that mean from a finite set of nearby reference cells. Its threshold therefore
moves from trial to trial even though the physical background is homogeneous.
That extra uncertainty is the source of CFAR loss in this experiment.

The comparison is fair only when both detectors have the same false-alarm
probability. A detector with a lower threshold may show more detections, but it
has not reduced loss if it also produces more false alarms.

## The two threshold operations

For complex Gaussian noise with unit mean square-law power, an H0 CUT statistic
`z = |n|^2` is exponential and

`P(z > eta) = exp(-eta)`.

The detector that knows the true noise power therefore uses

`eta_known = -log(Pfa)`.

CA-CFAR instead averages `N` independent reference powers,

`p_hat = (1/N) * sum(|r_i|^2, i = 1...N)`,

and detects when

`z > alpha(N,Pfa) * p_hat`,

where the exact homogeneous exponential-noise multiplier is

`alpha(N,Pfa) = N * (Pfa^(-1/N) - 1)`.

The script exposes the complex-noise generation, square-law powers, cumulative
reference sums, arithmetic means, multipliers, and comparisons. No CFAR,
probability-distribution, ROC, or interpolation toolbox helper hides them.

## What “CFAR loss” means here

At one selected detection probability, `Pd_target = 0.8`, the script reads the
required SNR from each empirical `Pd` curve by linear interpolation between the
two neighboring SNR grid points. It defines

`CFAR loss (dB) = SNR_required,CFAR - SNR_required,known`.

The raw Monte Carlo curves remain plotted. A transparent nondecreasing envelope
is used only to make crossing interpolation robust to small finite-trial
wiggles. The result is a model- and operating-point-specific SNR penalty, not a
universal constant for every radar.

## Why finite training creates the penalty

The ideal threshold is fixed because the background mean is known. The CA
threshold is the product of a finite-sample estimate and a larger multiplier.
Sometimes the estimate falls low and sometimes it rises high. The multiplier
is calibrated so those variations still average to the requested H0 `Pfa`, but
high threshold realizations lose some target detections. Reaching the same
`Pd` therefore requires more target SNR.

Increasing `N` makes `p_hat` concentrate around the true mean and moves
`alpha(N,Pfa)` toward `-log(Pfa)`. The 8-, 16-, 32-, and 64-cell curves should
approach the known-noise curve in that order, and their measured losses should
shrink.

## Why a stricter Pfa can cost more

Reducing `Pfa` pushes the decision farther into the noise tail. With finite
training data, uncertainty in the estimated scale matters more there. The
second sweep holds `N = 16`, the trials, SNR grid, and target `Pd` fixed while
changing only requested `Pfa`. In this model the loss grows as `Pfa` moves from
`1e-2` to `1e-4`.

## The broken comparison

A tempting shortcut is to use the known-noise multiplier `-log(Pfa)` on the
random CA estimate. That is not the finite-`N` calibration. Its actual H0 false
alarm probability is

`Pfa_broken = (1 + (-log(Pfa))/N)^(-N)`,

which is greater than the requested value for finite `N`. The broken detector
can look close to the ideal `Pd` curve because it quietly lowered its effective
threshold. Recovery recomputes `alpha(N,Pfa)` and then compares SNR at equal
false-alarm probability.

## Limiting cases and interpretation boundaries

- As `N` tends to infinity, `p_hat` tends to the true mean and
  `alpha(N,Pfa)` tends to `-log(Pfa)`; loss tends toward zero under this model.
- With very small `N`, the estimate and threshold are highly variable, so loss
  is larger.
- `N` means total independent reference powers here. If a range stencil is
  symmetric, that total would be split between its two sides.
- More reference cells help only while they remain independent and
  representative. P46 showed how wide windows can lose locality or collect
  target energy.
- `Pd = 0.8` is a reporting point, not a special physical law. Another target
  `Pd`, target model, integration scheme, or `Pfa` produces another loss.
- Monte Carlo resolution is finite. P47 uses enough trials to reveal the SNR
  trend; it does not replace the dedicated rare-event validation in P52.

## What this experiment establishes

It establishes a deterministic simulated comparison for a single-pulse,
nonfluctuating complex target in independent homogeneous complex Gaussian
noise with square-law detection. It does not establish loss for measured
clutter, correlated training data, fluctuating targets, multi-pulse
integration, hardware, or an operational radar.
