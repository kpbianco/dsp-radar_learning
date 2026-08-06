# P65 lesson: Preserve One Direction, Spend Freedom on Nulls

Guiding question: How can a beamformer place data-dependent nulls on interference?

## Physical mental model

A conventional beamformer decides its weights from geometry alone. It aligns
the desired direction and accepts whatever sidelobes that aperture produces.
MVDR listens to the scene first. It keeps one hard promise—unit response in the
assumed look direction—then uses the remaining spatial degrees of freedom to
minimize received output power. A strong interferer is expensive in that
objective, so the solution usually spends a degree of freedom on a null there.

The null is data-dependent: moving the interferer while keeping the look
direction fixed changes the covariance and therefore changes the weights.

## From array snapshots to covariance

P61–P63 use the broadside-referenced steering vector

```text
a_m(theta) = exp(j 2 pi m (d/lambda) sin(theta)).
```

For desired waveform `s`, interferer `i`, and receiver noise `n`, each column
of the array record is

```text
x[l] = sqrt(Ps) a(theta_s) s[l]
     + sqrt(Pi) a(theta_i) i[l] + n[l].
```

Collect `L` snapshots into `X` and estimate

```text
Rhat = X X^H / L.
```

Entry `(m,n)` records how sensors `m` and `n` vary together. Strong coherent
spatial structure creates dominant covariance directions. With few snapshots,
`Rhat` is noisy; when `L<M`, its rank cannot exceed `L`, so an unregularized
inverse is not dependable.

## The MVDR/Capon constraint and solution

The beamformer output is `y=w^H x`. MVDR solves

```text
minimize    w^H Rhat w
subject to  w^H a0 = 1,
```

where `a0` is the assumed steering vector. The exposed solution is

```text
q = Rloaded \ a0
w = q / (a0^H q)
Rloaded = Rhat + alpha (trace(Rhat)/M) I.
```

The denominator is essential: it enforces `w^H a0=1`. The script verifies this
numerically. The backslash solves a linear system; it does not form a matrix
inverse. Conventional weights `wCBF=a0/M` obey the same unit-response
constraint but do not use `Rhat`.

The name Capon often refers to scanning `1/(a^H R^-1 a)` as a spatial
spectrum. This module uses the same constrained weights at one chosen look
direction; P66 will turn covariance structure into a DOA scan.

## Reading pattern and output SINR together

The pattern `|w^H a(theta)|` shows angular response. A deep response at the
known interferer angle is evidence of spatial rejection in this model, but
pattern depth alone is not the performance goal. The analytical output SINR is

```text
SINRout = Ps |w^H as|^2
          / (Pi |w^H ai|^2 + sigma_n^2 w^H w).
```

This separates desired, interference, and white-noise contributions without
calling the finite record itself ground truth. White-noise gain is
`1/(w^H w)`. Aggressive weights may deepen one null while amplifying receiver
noise, so the experiment reports null response, white-noise gain, and SINR.

## Sweep 1: snapshots change covariance evidence

The snapshot sweep takes prefixes of one 256-snapshot record. Geometry, source
powers, loading rule, and random record do not change. Short prefixes give a
noisy or rank-deficient covariance estimate. Loading keeps the solve finite,
but the learned null and output SINR vary because the evidence is limited.
Longer records generally stabilize the covariance subspaces; no claim is made
that every individual null-depth point must improve monotonically.

More snapshots do not narrow the physical conventional beam. They improve an
estimate of spatial second-order statistics under the stationarity assumption.

## Sweep 2: diagonal loading buys robustness

The loading term adds equal positive power to every sensor-space direction.
Its scale follows average measured sensor power, so `alpha` is dimensionless.
Small `alpha` trusts the sample covariance almost completely. Large `alpha`
makes the weights approach a conventional steering solution:

```text
alpha -> infinity: wMVDR -> a0/(a0^H a0).
```

With only eight snapshots and a three-degree steering mismatch, tiny loading
lets MVDR treat the true desired steering vector as suppressible energy. A
moderate load reduces that self-nulling and raises true-direction response and
SINR. Excessive loading gives away adaptive interference rejection. Thus the
useful loading region balances model robustness against null depth.

## Broken case: the constraint protects the wrong direction

The constraint is only as correct as `a0`. In the broken case, the true desired
source stays at `3 deg`, but the beamformer is told `6 deg`. With almost no
loading and a sample-starved covariance, it preserves `6 deg` exactly while
placing low response near the true desired signal—the desired signal has
contaminated its own training covariance and is self-nulled.

Recovery has two visible stages on unchanged data:

1. moderate loading makes the mismatched weights less sharp and improves true
   response without pretending the assumed angle is correct;
2. restoring `a0=a(3 deg)` fixes the model and reapplies the unit-response
   constraint to the actual desired direction.

Loading is therefore a robustness tool, not a substitute for calibration or
correct steering knowledge.

## Limiting cases and claim boundary

- With no directional interference and many accurate snapshots, loaded MVDR
  tends toward a conventional look beam for spatially white noise.
- As `alpha` becomes very large, covariance differences matter less and the
  adaptive weights approach conventional weights.
- With fewer snapshots than elements, the raw sample covariance is singular or
  nearly singular; positive loading supplies a bounded reviewed solve.
- A distortionless constraint protects the assumed vector, not every signal
  near its angle and not a mismatched true vector.
- One `M`-element weight vector has finite spatial degrees of freedom; it
  cannot place arbitrary independent nulls while preserving arbitrary looks.
- Output SINR here uses known synthetic component powers. Real systems must
  estimate performance with separate training and calibration evidence.

The model is narrowband, far-field, stationary, and ideal except for finite
snapshots, white receiver noise, and one explicit steering mismatch. Static
repository checks and a Python oracle do not validate MATLAB rendering,
antennas, hardware/HIL, real-time execution, field behavior, or an operational
radar.
