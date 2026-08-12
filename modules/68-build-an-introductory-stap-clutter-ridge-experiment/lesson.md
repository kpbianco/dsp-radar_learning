# P68 lesson: Follow the Ridge, Not Either Axis Alone

## Guiding question

How can space and slow time be processed together to suppress moving-platform clutter?

## Physical mental model

Imagine the radar platform flying past many stationary ground patches. A patch
at one bearing produces a phase slope across array elements because its wave
arrives from that direction. The same patch produces a phase slope across
pulses because platform motion changes path length. Those slopes are two views
of one geometry, not independent labels.

Plot patch power against angle and Doppler. Ground returns trace a tilted
line-like band: the **clutter ridge**. A spatial notch ignores where a patch
sits in Doppler, and a Doppler notch ignores its angle. STAP keeps the pairing
and can spend its degrees of freedom along the ridge.

P37 established an element-by-pulse matrix, P41 distinguished clutter from
white noise, P42 transformed slow time, P61/P63 established the receive-array
phase convention, P65 exposed loaded MVDR, and P67 showed that a constraint
protects an assumed signature rather than physical truth.

## One patch becomes one space-time vector

For element index `m`, spacing `d/lambda`, and broadside-referenced angle
`theta`, the spatial steering entry is

```text
a_m(theta) = exp(j 2 pi m (d/lambda) sin(theta)).
```

For pulse index `p` and normalized Doppler `nu = f_d/PRF`,

```text
b_p(nu) = exp(j 2 pi p nu).
```

The script stores an `M`-element by `N`-pulse cell and stacks its columns in
MATLAB order. Its joint vector is therefore

```text
s(theta,nu) = kron(b(nu), a(theta)).
```

No STAP toolbox object constructs or processes the snapshot.

## Why a moving platform creates a ridge

In this ideal side-looking geometry, stationary ground at angle `theta` has

```text
nu_c(theta) = f_d,c/PRF
            = 2 v_platform sin(theta) / (lambda PRF)
            = beta sin(theta).
```

With `v_platform = 105 m/s`, `lambda = 0.03 m`, and `PRF = 20 kHz`,
`beta = 0.35 cycles/pulse per sin(theta)`. Clutter angles span `-60` to
`+60 deg`, so the ridge stays inside `-0.5 < nu < 0.5`.

The actual target is near `10.7 deg, 0.208 cycles/pulse`. Clutter exists near
that angle at another Doppler, and other clutter has Doppler near `0.208` at a
different angle. Either marginal overlaps clutter, while the paired target
point is at least `0.05 cycles/pulse` away from the ridge.

## Covariance is learned from neighboring range cells

Each target-free training cell uses fresh complex patch coefficients and noise
but the same ridge geometry:

```text
x_l = sum_k sqrt(P_k) s(theta_k,nu_c,k) gamma_k,l + n_l,
Rhat = (1/L) sum_l x_l x_l^H = X X^H / L.
```

`Rhat` is `MN` by `MN`, or `64 by 64` here. Its entries describe which
element-pulse coordinates vary together. Training cells are independent
idealized range samples; the target cell uses different private streams and
never enters clean training.

The analytical ruler is the known synthetic interference covariance

```text
Ri = sum_k P_k s_k s_k^H + sigma_n^2 I.
```

This does not pretend a real radar knows `Ri`; it provides a stable comparison
for weights created from finite training.

## Fixed, separate, and joint processing

The fixed matched weight is

```text
w_fixed = s0 / (s0^H s0).
```

Separate processing estimates an `M by M` spatial covariance and an `N by N`
slow-time covariance. It creates loaded MVDR weights and combines them:

```text
w_sep = kron(w_d, w_s).
```

That product adapts both axes but remains separable. Its 2-D response is a
product of one spatial and one Doppler shape, so it cannot freely bend a notch
along a coupled ridge.

Joint STAP solves one loaded `MN`-dimensional constrained problem:

```text
R_L = Rhat + alpha trace(Rhat)/(MN) I,
q   = R_L \ s0,
w   = q / (s0^H q),
w^H s0 = 1.
```

There is no explicit inverse. The normalization protects the **assumed**
target signature.

## Read output SCNR, not color alone

For actual target vector `s_t`, target power `P_t`, and simulated `Ri`,

```text
SCNR_out = P_t |w^H s_t|^2 / (w^H Ri w).
```

SCNR and covariance power use `10 log10`. A voltage response uses `20 log10`.
A normalized dark pixel can look impressive even when target or noise gain is
poor; SCNR accounts for numerator and denominator.

## Sweep 1: training support is evidence, not aperture

The support sweep uses prefixes of one unchanged record: `8, 16, 32, 64, 128`.
Geometry, ridge, target, loading, and values inside each prefix do not change.
With `L < MN`, sample-covariance rank cannot exceed `L`. Loading keeps the
solve finite but does not invent evidence. More support generally stabilizes
the reviewed endpoint; individual finite-record points need not improve
monotonically. Support does not increase aperture, pulse count, or CPI.

## Sweep 2 and broken case: contaminated training

The second sweep adds one target-like signature to `0, 5, 10, 20, 40 percent`
of the unchanged training cells. That violates the assumption that secondary
cells contain representative interference but no desired target.

With a fixed diagonal-loading term, an exact rank-one addition along the
constrained vector cancels out of the normalized MVDR solution. This script
instead recomputes loading from each covariance trace, so even perfectly
aligned contamination can slightly change the weight by changing the loading
level. The exact constraint still preserves the assumed signature itself.

The broken case retains a small declared mismatch: the constraint protects
`10.0 deg, 0.200`, while the injected and CUT target is `10.7 deg, 0.208`.
Contamination can then make the unprotected part of the actual target direction
expensive and attenuate it while the assumed vector still has unit response.

Recovery removes only the injected additions and recomputes the weight from
the original clean record. The CUT, assumptions, loading, and random clean
samples stay unchanged. The recovered weight is asserted equal to baseline.

## Limiting cases and claim boundary

- As platform speed tends to zero, `beta -> 0` and ground collapses toward
  zero Doppler.
- With `M = 1` there is no spatial discrimination; with `N = 1` there is no
  slow-time discrimination.
- If target and clutter have the same steering vector, perfect rejection and
  perfect preservation are contradictory.
- With fewer than `MN` training cells, raw covariance is rank deficient.
  Loading bounds the solve but does not make the estimate complete.
- More nonhomogeneous training can estimate the wrong covariance more firmly.
- The narrow ridge omits internal clutter motion, channel errors, antenna
  patterns, terrain variation, range dependence, and range migration.
- Patch reflectivities are independent circular Gaussian values, not measured
  clutter or a land-cover law.

Static repository checks and a standard-library Python oracle validate
structure, deterministic contracts, and the numerical premise. They do not
execute MATLAB, render figures, validate an antenna or platform, or establish
bench, hardware/HIL, real-time, field, or operational performance.

## Common interpretation mistakes

- Calling all clutter near-zero Doppler misses moving-platform coupling.
- Treating `kron(w_d,w_s)` as fully joint ignores its product restriction.
- Reading normalized color as SCNR ignores target and noise gain.
- Calling loading extra training data confuses robustness with evidence.
- Assuming more training always helps ignores contamination and nonstationarity.
- Saying contaminated MVDR must null its exact constraint ignores the model
  mismatch required by this broken case.
- Using `20 log10` for SCNR doubles the dB value incorrectly.
- Reading normalized Doppler as hertz forgets multiplication by `PRF`.
