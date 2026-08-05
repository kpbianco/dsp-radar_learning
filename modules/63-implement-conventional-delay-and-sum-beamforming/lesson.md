# P63 lesson: Steering Is a Spatial Matched Filter

The guiding question is: **How does steering align one direction and misalign others?**

P61 showed that direction appears as a phase slope across ULA sensors. P62
coherently added ideal element phasors to form an array factor. P63 applies the
same operation to noisy received data: each candidate direction is a spatial
template, and the conventional beamformer measures how well the array snapshot
matches that template.

## From two sources to sensor data

Let `M` sensors lie at positions `m d`, where `m=0,...,M-1`. Angle is measured
from broadside, normalized spacing is `q=d/lambda`, and the steering vector is

```text
a_m(theta) = exp(j 2 pi m q sin(theta)).
```

For two narrowband sources observed over `L` snapshots, the complex-baseband
sensor matrix is

```text
X = A_s S + N,
A_s = [a(theta_1)  a(theta_2)].
```

Each column of `X` is one simultaneous array snapshot. `S` holds the source
samples and `N` holds independent sensor noise. The reviewed SNR is nominal
per-source, per-sensor input SNR: each source has unit sample magnitude and the
complex sensor noise is scaled by `10^(-SNR/20)`.

This is the narrowband approximation. A single complex phase per channel can
represent propagation delay only when signal bandwidth is small enough that
the phase slope is effectively constant across the band. True broadband
delay-and-sum uses time delays or frequency-dependent phase; fixed phase
steering can produce beam squint.

## The conventional delay-and-sum operation

To inspect candidate direction `theta`, use a normalized fixed weight

```text
w(theta) = a(theta)/M.
```

The output for snapshot `ell` is the exposed Hermitian coherent sum

```text
y_theta[ell] = w(theta)^H x[ell]
             = (1/M) sum_m conj(a_m(theta)) x_m[ell].
```

If a source actually arrives from `theta`, `conj(a_m(theta))` removes its phase
slope. All `M` contributions have the same phase and add to unit normalized
voltage gain. For another direction `phi`, the residual contribution is

```text
(1/M) exp(j 2 pi m q [sin(phi)-sin(theta)]).
```

Those phasors rotate with element index and partially cancel. This is why a
beam is a spatial matched-filter response rather than a physical ray drawn out
of the antenna.

Figure 2 shows this operation before any repeated-case helper is used. The
matched residual phases lie on top of one another, so cumulative magnitude
grows steadily. Off-target residual phases wind, so the cumulative sum grows
and shrinks.

## Direct averaging and covariance averaging are the same scan

The conventional power estimate averages output power across snapshots:

```text
P_DAS(theta) = (1/L) sum_ell |w(theta)^H x[ell]|^2.
```

Define the sample covariance

```text
Rhat = X X^H / L.
```

Then the same quantity is

```text
P_DAS(theta) = w(theta)^H Rhat w(theta).
```

The script computes both paths and asserts agreement to numerical tolerance.
The covariance is not a new source of angular resolution; it is a compact way
to retain averaged spatial second-order information. With one snapshot,
`Rhat=x x^H` has rank one and carries every random cross-term from that look.
With many independent snapshots, source/noise cross-terms fluctuate in phase
and average toward zero, making the scan steadier.

## Sweep 1: source separation and array aperture

Two sources closer than the conventional main-lobe width need not make two
distinct peaks. The separation sweep holds array, SNR, and snapshot count fixed
while moving a symmetric pair from `6` through `12` to `24 deg`. The close
pair merges into one broad maximum; the widest pair resolves.

The array-size sub-sweep holds a `16 deg` pair, half-wavelength spacing, SNR,
and snapshots fixed while using `M=[4,8,16]`. Physical aperture is

```text
L_array = (M-1)d.
```

Four elements merge the pair. Eight and sixteen resolve it, and sixteen forms
the narrower lobes. This is the received-data version of P62's aperture result.
More snapshots cannot repair the four-element beamwidth because they estimate
the same broad fixed pattern more accurately.

## Sweep 2: SNR and snapshot reliability

At fixed geometry and `128` snapshots, the SNR sweep changes only sensor-noise
scale. Low input SNR raises the relative scan floor and can move local maxima;
high SNR exposes the two spatial responses cleanly.

At fixed data model and `0 dB` input SNR, the snapshot sweep reuses prefixes of
one deterministic 128-snapshot record. One snapshot contains strong accidental
source/source and source/noise cross-terms. Eight looks are steadier, and 128
looks reduce the reviewed off-source ripple. Snapshot averaging lowers
variance; it does not change element spacing, aperture, or theoretical
beamwidth.

## The intentionally broken case and recovery

The received model uses `a(theta)=exp(+j phase)`. The correct output contains
`a(theta)^H`, which supplies the negative compensating phase. The broken path
constructs its scan steering vector with the opposite sign and then still
takes a Hermitian transpose. It therefore tests `a(-theta)` while labeling the
axis `theta`.

For the same unchanged data and a symmetric scan grid,

```text
P_broken(theta) = P_correct(-theta).
```

Sources at `-20` and `+30 deg` appear at `+20` and `-30 deg`. The peaks are not
new arrivals, a random-noise effect, or a front/back ambiguity in this bounded
2-D model; they are an angle/phase convention error. Recovery restores
`w(theta)=a(theta)/M` and the Hermitian sum, moving both peaks back to their
true angles. The script asserts the entire broken curve equals the reversed
recovered curve, not merely that two hand-picked points look plausible.

## Limiting cases and model boundary

- One sensor has no spatial discrimination; every steering direction applies
  the same scalar magnitude.
- Co-located sensors have no direction-dependent phase slope, so coherent
  averaging improves noise but produces no angular beam.
- With infinite independent snapshots, the sample covariance approaches the
  model covariance, but finite aperture still limits conventional resolution.
- Two sources at the same direction are indistinguishable to this ULA scan.
- Half-wavelength spacing avoids the full-visible-sector spatial alias used in
  P62, but finite-aperture sidelobes remain.
- Correlated or coherent sources retain cross-terms under averaging and can
  distort conventional peaks; averaging is not guaranteed to separate them.
- A ULA measures projected direction cosine, not a unique 3-D direction.
- The simulation assumes far-field plane waves, narrowband signals,
  synchronized calibrated channels, isotropic elements, independent sources,
  spatially white noise, and no coupling or multipath.

P65 will make weights depend on `Rhat` to suppress interference, P66 will use
signal/noise subspaces, and P67 will show how channel error breaks the ideal
steering match.

## Common interpretation mistakes

- Saying the beamformer delays this narrowband complex record in seconds hides
  that it applies a carrier-phase compensation here.
- Omitting the conjugate from `w^H x` doubles or reverses the phase slope rather
  than removing it.
- Calling a single-snapshot curve a stable spectrum ignores its random
  cross-terms.
- Saying covariance averaging narrows the main lobe confuses variance with
  aperture resolution.
- Normalizing each curve and then claiming absolute output power is unchanged
  confuses display normalization with physical power.
- Treating a merged close pair as one proven source mistakes conventional
  resolution for scene truth.
- Calling the largest two samples the source angles can select samples from
  one broad lobe; distinct local peaks and the array resolution must be checked.
- Claiming two clean simulated peaks validate an antenna ignores element
  pattern, calibration, coupling, bandwidth, multipath, and hardware.

## Dependencies, compatibility, and claim boundary

P61 and P62 are the concept and ordering prerequisites. The experiment uses
base MATLAB, explicit matrix products, bounded loops, and private Park-Miller
and Box-Muller generators that do not alter global random state. It needs
script-local functions (MATLAB R2016b or newer), writes no file, and starts no
network, timer, worker, or checkpoint. Static source checks and an independent
Python simulation do not prove MATLAB parsing/execution, rendered plots,
educational effectiveness, antenna performance, hardware/HIL, real-time,
field, deployment, or production behavior.
