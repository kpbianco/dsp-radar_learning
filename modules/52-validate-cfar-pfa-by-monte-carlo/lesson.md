# Lesson: a requested probability is a model claim to test

## Start with the counted event

False-alarm probability is not “the number of dots that look wrong.” It is a
conditional probability under target absence. This experiment defines one
trial as one valid noise-only cell under test (CUT) plus all `N` reference
cells required by the detector. Every trial therefore contributes exactly one
tested CUT and either zero or one false alarm.

If `K` alarms occur among `M` independently generated trials, the measured
rate is

`Pfa_hat = K / M`.

Edge locations with incomplete stencils are not silently counted as tests.
Targets, sidelobes, and detections near modeled target responses are also
absent, so the numerator is genuinely an H0 false-alarm count.

## The homogeneous reference model

Let each complex noise sample have independent zero-mean Gaussian I and Q
components with total mean power one. Its square-law power

`z = |n|^2`

is exponential with mean one. CA-CFAR averages `N` independent reference
powers,

`p_hat = (1/N) * sum(|r_i|^2, i=1...N)`,

and declares a false alarm when

`z > alpha * p_hat`.

For an independent exponential CUT and references, the exact probability is

`Pfa(alpha,N) = (1 + alpha/N)^(-N)`.

Solving for the multiplier gives

`alpha(N,Pfa) = N * (Pfa^(-1/N) - 1)`.

The script exposes complex-noise generation, the square law, cumulative
training-power sums, arithmetic means, alpha, and every comparison. No CFAR or
probability toolbox object stands between the model and the count.

## Why Monte Carlo does not equal the requested value exactly

Even a correctly calibrated detector produces a random alarm count. For
independent Bernoulli outcomes, a typical standard deviation of the measured
rate is approximately

`sqrt(Pfa*(1-Pfa)/M)`.

The figures report a 95% Wilson interval rather than interpreting every small
difference as detector error. With `p_hat=K/M` and `q=1.96`, its limits are

`[p_hat + q^2/(2M) +/- q*sqrt(p_hat*(1-p_hat)/M + q^2/(4M^2))]`

divided by `1 + q^2/M`. It remains nonzero when `K=0`. The interval quantifies
finite-trial uncertainty conditional on independent stationary trials; it
does not certify the assumed clutter model.

## Read the controlled sweeps

Sweep 1 changes requested `Pfa` while holding the same trial bank, `N=24`, and
the homogeneous model fixed. Alpha is recomputed for each request. The
measured points should track the identity line within ordinary counting
uncertainty, while smaller probabilities show larger relative uncertainty
because fewer alarms are observed.

Sweep 2 changes total independent training count through 8, 16, 24, 32, and
64. Every case uses its own finite-`N` alpha. Under the assumed model all cases
retain the same `Pfa`; more training cells are not supposed to lower the
false-alarm rate when calibration is correct.

Sweep 3 holds requested `Pfa`, `N`, and alpha fixed and changes only the noise
model:

- the reference case has independent exponential powers;
- the correlated-Gaussian case gives every complex cell a shared component,
  so CUT and reference powers move together; and
- the compound-lognormal case multiplies every exponential power by an
  independent, unit-mean, heavy-tailed texture.

The correlated case is conservative here because a high CUT tends to arrive
with a high reference estimate. The heavy-tailed case overspends because an
unusually large CUT texture is not reliably represented by the finite
training mean. Both departures are predictable consequences of model
mismatch, not proof that correlation always helps or every non-Gaussian model
fails in the same direction.

## The deliberately broken scaling

As `N` tends to infinity, finite-`N` alpha approaches the known-noise limit

`alpha_infinity = -log(Pfa)`.

Using that smaller limiting multiplier on a finite random training mean is the
broken implementation. Its exact homogeneous false-alarm probability is

`Pfa_broken = (1 + (-log(Pfa))/N)^(-N)`,

which exceeds the request for finite `N`. Recovery recomputes
`N*(Pfa^(-1/N)-1)` from the actual reference count and reruns the same explicit
comparison. A detector that reports more detections only because it spends
more false alarms has not improved.

## Limiting cases and model boundaries

- As `M` grows, Monte Carlo uncertainty shrinks roughly as `1/sqrt(M)`.
- As `N` grows under independent homogeneous exponential noise, alpha tends
  to `-log(Pfa)` while achieved `Pfa` stays at the request.
- As correlation coefficient tends to zero, the correlated construction
  returns to the independent Gaussian model. As it tends to one, CUT and
  references become nearly the same complex sample and the threshold ratio
  changes radically.
- As log-texture standard deviation tends to zero, the compound model returns
  to exponential power. Stronger texture creates a heavier tail.
- More training cells help represent the background only while they remain
  local and statistically relevant. P46 and P51 showed the geometry failures
  that this isolated noise-only trial deliberately removes.
- A reproducible seed supports audit and rerun; it does not turn simulation
  into measured-clutter, hardware, field, or operational evidence.

## Common interpretation mistakes

1. “Requested `Pfa` is automatically achieved.” It is achieved only for the
   calibrated statistic under its assumptions and correct tested-cell count.
2. “Every plotted cell is a trial.” Only CUTs with complete required
   references and an H0 truth label belong in the denominator.
3. “More training cells should reduce `Pfa`.” Correct recalibration keeps
   `Pfa` fixed; the training count changes alpha and estimate variability.
4. “A narrow interval validates the clutter model.” It quantifies counting
   uncertainty inside the selected model.
5. “Correlated clutter always lowers false alarms.” That direction belongs to
   this shared-component example, not to all correlation structures.

## Connection to the implemented CFAR chain

P45 introduced the explicit CA stencil, P47 separated finite-`N` scaling from
the known-noise limit, and P51 classified adverse scene disagreements. P52
closes Phase 5 by auditing the probability claim itself: define a valid H0
trial, count numerator and denominator, attach uncertainty, compare with exact
homogeneous theory, and then break one assumption at a time.
