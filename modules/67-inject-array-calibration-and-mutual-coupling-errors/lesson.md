# P67 lesson: The Beamformer Protects a Vector, Not an Angle

Guiding question: How sensitive are beamforming and DOA results to imperfect channels?

## Physical mental model

An ideal array treats its sensors like identical rulers placed at exactly known
locations. A wave from one angle then draws a predictable phase ramp across
those rulers. Real channels can have unequal gain and phase, elements can sit a
little away from their assumed locations, and energy received by one element
can couple into its neighbors. The measured ramp is bent and rescaled.

The processor does not see “ten degrees.” It sees a complex ten-number
signature and compares that signature with its model. If the signature is
wrong, a conventional scan can point or shape incorrectly, MUSIC loses exact
noise-subspace orthogonality, and MVDR can place low response on the desired
signal while perfectly preserving the wrong assumed vector.

## Nominal and physical array models

For nominal element position `p_m` measured in wavelengths, P61 established

```text
a0_m(theta) = exp(j 2 pi p_m sin(theta)).
```

P67 displaces each position by `delta_p_m`, assigns complex channel gain `g_m`,
and mixes neighboring channels with a simple reciprocal matrix `C`:

```text
ap_m(theta) = exp(j 2 pi (p_m + delta_p_m) sin(theta))
b(theta) = Dg C ap(theta),       Dg = diag(g_1,...,g_M).
```

`C` has ones on its diagonal, one complex coefficient on each nearest-neighbor
diagonal, and a smaller second-neighbor coefficient. Complex symmetry models
reciprocity in this deliberately simple narrowband example. It is not an
electromagnetic coupling solver.

With two uncorrelated source records in `S`, the impaired received record is

```text
Xerr = B diag(sqrt(P)) S + N,     B = [b(theta_1), b(theta_2)].
```

The exact same `S` and post-chain receiver-noise record `N` form the ideal and
impaired comparisons. This isolates array-model error from a lucky new random
trial.

## Three processors, one wrong dictionary

All three scans deliberately use the nominal steering matrix `A0`, even for
impaired data. Supplying the physical manifold would hide the sensitivity the
lesson is meant to expose.

The conventional Bartlett power is

```text
PB(theta) = a0(theta)^H Rhat a0(theta) / M^2.
```

Loaded MVDR/Capon uses

```text
Rload = Rhat + alpha trace(Rhat)/M I
PC(theta) = 1 / (a0(theta)^H Rload^-1 a0(theta)).
```

The script uses a linear solve, not an explicit inverse. MUSIC first whitens
the covariance and candidate dictionary with the known receiver-noise
covariance `Rn`, orders the whitened-covariance eigenvectors, assigns the last
`M-K` to `En`, and evaluates

```text
Wn Rn Wn^H = I
PMUSIC(theta) = 1 / ||En^H Wn a0(theta)||^2.
```

For ideal and impaired data, `Rn = sigma_n^2 I`, so whitening changes only a
common scale. After equalization, it prevents unequal receiver-noise variances
from masquerading as signal-subspace structure.

These are power-like spatial outputs, so their normalized plots use
`10 log10`. A physical beam voltage response such as `|w^H b(theta)|` uses
`20 log10`.

## Why MVDR can damage the desired source

At the known desired direction, loaded MVDR still enforces

```text
w^H a0(theta_cal) = 1.
```

It does not enforce `w^H b(theta_cal)=1`. If the desired source contributes to
the covariance but its physical signature differs from the protected vector,
MVDR is allowed to treat part of that source as interference. This is
self-nulling from steering mismatch. The experiment therefore evaluates each
beam on the actual manifold, not just on the nominal curve used to construct
the weights.

## Estimate one composite channel response

An independent calibration capture contains a known unit-magnitude pilot `s_c`
from known angle `theta_c`. Correlation estimates the received response:

```text
bhat_c = Xcal s_c^H / (Lcal sqrt(Pcal)).
qhat = bhat_c ./ a0(theta_c)
E = diag(1 ./ qhat)
Xcalibrated = E Xerr.
```

At the calibration direction, `E b(theta_c)` is driven toward
`a0(theta_c)`. That restores the signature protected by MVDR and searched by
the nominal scans. The capture is independent of the operational data, so it
does not leak truth from the evaluated record.

Receiver noise was added after `Dg C` in this model. Applying `E` also changes
that noise covariance from `sigma_n^2 I` to

```text
Rn,cal = sigma_n^2 E E^H.
```

The corrected analytical output SINR uses this covariance, and calibrated
MUSIC whitens with it before its eigenspace split. Replacing it with the
original white-noise covariance can either overstate or understate SINR and
can invalidate MUSIC's white-noise subspace interpretation.

## Sweep 1: one severity scale, one frozen array realization

The first sweep multiplies the same seeded gain, phase, and position-error
patterns by one dimensionless severity scale. Coupling, waveforms, receiver
noise, pilot, and calibration noise stay fixed. This is one experimental
control even though it represents a shared manufacturing-quality scale.

As severity rises, the uncalibrated MVDR response to the known source can fall
dramatically because the protected nominal vector and physical vector diverge.
Re-estimating `qhat` at each scale restores that direction. MUSIC bias is often
less dramatic than MVDR self-nulling in this particular record; sensitivity is
algorithm- and metric-dependent.

## Sweep 2: coupling exposes the local limit

The second sweep changes only one base coupling-strength control. Its tied
next-nearest coefficient follows the same fixed `0.30*c^2` rule; gain, phase,
position, coupling phase, source data, noise, and pilot remain unchanged.
The known calibration direction is still strongly corrected, but the residual
manifold error at the off-angle interferer is not forced to zero.

Why? Position error contributes

```text
exp(j 2 pi delta_p_m [sin(theta)-sin(theta_c)])
```

relative to the calibration direction, and `C a(theta)` is direction
dependent. A diagonal response measured at one angle cannot be a global
inverse for those mechanisms.

## Broken case and recovery

The broken path correlates the correct pilot but divides only by its measured
response. That quietly assumes the known source arrived at broadside. It
flattens the known nonzero phase ramp toward an all-ones vector, so nominal
processing interprets it near zero degrees and shifts the other source too.

Recovery uses the unchanged pilot and operational record but restores the
known steering vector in `qhat = bhat_c ./ a0(theta_c)`. No new noise draw and
no favorable rerun are involved.

## Limiting cases and claim boundary

- Zero gain, phase, position, and coupling error makes the physical manifold
  equal the nominal manifold; calibration then only adds finite-pilot noise.
- Infinite calibration SNR and snapshots make the known-direction composite
  response estimate exact in this stationary model.
- One known source estimates one effective response vector. It cannot identify
  every element position and every entry of `C` separately.
- A calibrated direction is not proof that every scan angle is calibrated.
- Stronger coupling can require multi-angle calibration or a fitted manifold,
  not merely more diagonal equalization.
- Calibration can color post-chain receiver noise and amplify weak channels;
  safe inversion and resource guards are part of the experiment.
- Time variation between calibration and operation is omitted.

The model omits element patterns, polarization, near-field curvature,
broadband coupling, multipath, colored external noise, calibration drift, and
electromagnetic validation. Static checks and a Python simulated oracle do not
validate MATLAB rendering, physical antennas, hardware/HIL, real-time systems,
field behavior, or an operational radar.
