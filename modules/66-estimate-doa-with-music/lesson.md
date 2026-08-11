# P66 lesson: Noise-Subspace Nulls Become Direction Peaks

Guiding question: How can subspace methods resolve sources more finely than a conventional beam?

## Physical mental model

A narrowband plane wave reaches adjacent sensors with a repeatable phase
increment. For a half-wavelength uniform linear array (ULA), the
broadside-referenced steering vector is

```text
a_m(theta) = exp(j 2 pi m (d/lambda) sin(theta)),  m=0,...,M-1.
```

Each possible direction is therefore one vector in `M`-dimensional sensor
space. Conventional Bartlett scanning asks how much measured power lies along
each steering vector. Its angular width is set mainly by physical aperture, so
two sources inside one beam can form one broad shoulder.

MUSIC asks a different question: which steering vectors are almost orthogonal
to every measured noise-only direction? That geometric test can produce much
sharper peaks, but only when the data and model reveal the correct subspaces.

## From snapshots to an eigenspectrum

For `K` uncorrelated sources, one array snapshot is

```text
x[l] = A s[l] + n[l],
A = [a(theta_1) ... a(theta_K)].
```

Collect `L` snapshots as columns of `X` and estimate

```text
Rhat = X X^H / L.
```

The script Hermitian-symmetrizes `Rhat`, computes its eigenvectors, and sorts
the eigenvalues and matching eigenvectors together from largest to smallest:

```text
Rhat = U diag(lambda_1,...,lambda_M) U^H.
```

For ideal spatially white noise and enough data, the first `K` eigenvectors
span the source steering directions. The remaining columns

```text
En = U(:,K+1:M)
```

span the noise subspace. The eigenvectors are not individual source steering
vectors, and their complex phases are arbitrary. The subspace they span is
the meaningful object.

## Conventional Bartlett power versus MUSIC pseudospectrum

The normalized conventional scan is based on

```text
PB(theta) = a(theta)^H Rhat a(theta) / M^2.
```

It is received output power for a fixed steered sum. MUSIC instead forms

```text
PMUSIC(theta) = 1 / ||En^H a(theta)||^2.
```

At a modeled source direction, `a(theta)` lies nearly in the signal subspace,
so its noise-subspace projection is small and the reciprocal becomes large.
The baseline plot normalizes both curves to `0 dB`; absolute peak height is not
source power. Read peak angle and valley separation, not MUSIC peak amplitude,
as the main result.

In the reviewed six-degree scene, Bartlett remains higher at the midpoint than
at the two true angles: it has not split the pair. MUSIC has distinct peaks
near `-3 deg` and `+3 deg` with a deep intervening valley. This is conditional
super-resolution, not a claim of unlimited angular resolution.

## Sweep 1: source spacing tests angular separation

The spacing sweep reuses exactly the same two source waveforms and receiver
noise. Only the steering-vector angles move symmetrically around broadside.
The plotted truth-to-midpoint contrast is positive when the spectrum has a
valley at the midpoint relative to both truth angles.

MUSIC separates the reviewed four-degree case while the Bartlett contrast is
still negative. At extremely small separation, the two steering vectors become
nearly parallel and finite-data errors can erase the valley. At larger
separation, even the physical Bartlett aperture eventually forms two lobes.

## Sweep 2: SNR controls subspace evidence

Signal eigenvalues rise above the receiver-noise cluster as SNR increases. The
quantity `10 log10(lambda_2/lambda_3)` is the boundary between the assumed
two-dimensional signal subspace and the noise subspace. A larger gap makes
that partition less sensitive to sample error.

At `-10 dB` per source, selecting the two tallest local pseudospectrum maxima
can include a noise-driven direction. At high SNR, both estimates sit close to
truth. SNR does not lengthen the array; it makes the subspace estimate more
credible.

## Sweep 3: snapshots control covariance evidence

The snapshot sweep uses nested prefixes of one fixed `0 dB` record. Source
angles, amplitudes, waveforms, and noise realization do not change. More
snapshots usually stabilize the covariance and its eigenspaces, but individual
points need not improve monotonically.

More snapshots do not narrow the conventional physical beam. They reduce
finite-record error under the assumption that the scene remains stationary
throughout the record.

## Sweep 4: assumed source number changes both subspaces

MUSIC must be told `K` or obtain it from a separate model-order estimator. In
this lesson, `K` is deliberately visible rather than estimated automatically.

- `K=1` puts part of the second source direction into `En`, merging the
  reviewed pair near broadside.
- `K=2` makes the intended partition and localizes both sources.
- `K>2` removes noise-only eigenvectors from `En`; reviewed extra peaks are
  noise-subspace artifacts, not newly discovered emitters.

Overestimating `K` does not always create an artifact at a predictable angle.
The correct general statement is that the projection test has been weakened by
an incorrect partition.

## Broken case: coherence collapses source rank

Uncorrelated source waveforms supply two statistically independent covariance
directions. The broken case sets

```text
s_2[l] = exp(j phi) s_1[l].
```

Although two angles still illuminate the array, their waveform covariance has
rank one. The full-array eigenspectrum shows one dominant signal eigenvalue;
the second sits in the noise cluster. Asking raw MUSIC for two sources cannot
manufacture the missing independent dimension, so its peaks are wrong.

## Recovery: overlapping spatial subarrays

For each contiguous `P`-element subarray, the script forms a covariance from
the same coherent sensor record and then averages all `M-P+1` covariances:

```text
Rss = (1/J) sum_j X_j X_j^H / L,  J=M-P+1.
```

Moving the subarray start changes each source's phase reference differently.
The average restores rank for distinct ULA directions in this reviewed scene.
MUSIC then uses a `P`-element steering vector and recovers the two peaks.

Spatial smoothing is not free. It reduces the effective aperture from ten to
seven elements, assumes a calibrated ULA with shift-invariant subarrays, and
needs enough overlapping subarrays relative to the source count. It repairs
this coherence model; it does not repair arbitrary calibration, multipath, or
colored-noise errors.

## Limiting cases and claim boundary

- With zero signal power, no physically meaningful signal subspace exists;
  the tallest MUSIC maxima are noise fluctuations.
- With infinite independent snapshots and white noise, the sample subspaces
  approach their ensemble counterparts.
- When source steering vectors become identical, angle identifiability is lost
  even at high SNR.
- If `K>=M`, no nonempty noise subspace remains and MUSIC is undefined.
- Coherent sources can make signal covariance rank smaller than source count;
  spatial smoothing trades aperture for restored rank only under its ULA model.
- MUSIC peak height is not a calibrated source-power estimate and the scan grid
  does not create information between physical sensors.

The experiment is deterministic synthetic narrowband simulation. Repository
tests can establish its equations, bounds, and an independent numerical model;
they do not validate MATLAB rendering, array hardware, calibration, HIL,
real-time execution, field behavior, or an operational radar.
