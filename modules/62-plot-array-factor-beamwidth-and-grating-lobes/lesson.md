# P62 lesson: Aperture Is a Spatial Interference Experiment

The guiding question is: **How do aperture size and element spacing shape a beam pattern?**

P61 followed one arriving wavefront across an array and measured its phase
slope. P62 turns that same geometry around: choose a steering direction,
remove the phase slope expected from it, and add all element contributions.
Directions whose residual phases align add strongly; directions whose residual
phases wind around the complex plane cancel.

## From phase slope to array factor

Let `M` isotropic elements lie at positions `m d`, for `m=0,...,M-1`. Angles
are measured from broadside, as in P61. Write normalized spacing as
`q=d/lambda`, observation angle as `theta`, steering angle as `theta_0`, and a
real nonnegative excitation as `w_m`. After applying the steering conjugate,
element `m` contributes

```text
c_m(theta) = w_m exp(j 2 pi m q [sin(theta)-sin(theta_0)]).
```

The normalized array factor is the magnitude of their explicit coherent sum:

```text
AF(theta) = |sum_m c_m(theta)| / sum_m |w_m|.
```

At `theta=theta_0`, every residual phase is zero, so all contributions point
the same way and `AF=1`. Away from the steering direction, their angles spread
and the sum shrinks. This is the spatial analogue of the phasor cancellation
seen in spectral leakage and pulse-compression sidelobes; the independent
variable is direction cosine rather than time or frequency.

For uniform weights, the finite geometric sum can also be written

```text
AF(theta) = | sin(M psi/2) / [M sin(psi/2)] |,
psi = 2 pi q [sin(theta)-sin(theta_0)].
```

The script does not use this closed form because its removable `0/0` limit can
hide the physical addition. It forms every complex element contribution first.

## How the baseline metrics are measured

The baseline is `M=8`, `d=lambda/2`, and broadside steering with uniform
weights. Its physical sensor span is

```text
L = (M-1)d = 3.5 lambda.
```

The linear plot shows amplitude. The dB plot uses
`20 log10(AF)`, which is equivalent to `10 log10(AF^2)`. A display floor is
applied only after metrics are measured from the unclipped linear response.

- **Half-power beamwidth (HPBW):** the full angular distance between the two
  `AF=1/sqrt(2)` crossings around the intended peak. These are the `-3.0103 dB`
  amplitude points, not half-amplitude points.
- **First-null beamwidth (FNBW):** the full distance between the closest local
  minima on each side of the intended peak.
- **Peak sidelobe level (PSL):** the largest response outside those first
  nulls, expressed relative to the main peak in dB.

The reviewed grid and linear interpolation give approximately `12.803 deg`
HPBW, `28.950 deg` first-null width, and `-12.797 dB` peak sidelobe level.
Those are properties of this discrete eight-element uniform aperture, not
universal constants.

## Sweep 1: aperture narrows the beam

At fixed half-wavelength spacing, changing `M=[4,8,16]` changes the sensor span
from `1.5` to `3.5` to `7.5 lambda`. A larger aperture accumulates residual
phase faster as angle moves away from steering, so cancellation begins closer
to the peak. HPBW decreases monotonically.

More elements at fixed spacing increase both aperture and the number of
samples. The plotted result therefore does not isolate those two mathematical
effects separately; it answers the physical design question for a uniformly
filled ULA. More elements do not automatically lower the familiar uniform
first sidelobe far below about `-13 dB`; weights control that trade.

## Sweep 2: spacing can copy the main beam

At fixed `M=8`, larger spacing also creates a larger aperture and a narrower
local main lobe. But spatial phase is sampled only at element positions. A
second direction is perfectly coherent whenever

```text
q [sin(theta_g)-sin(theta_0)] = k,   k is a nonzero integer,

sin(theta_g) = sin(theta_0) + k/q.
```

It is a visible grating lobe only if the right side lies in `[-1,1]`. This
test matters: spacing above half wavelength does not produce a visible grating
lobe for every single steering angle. At broadside, `d=0.75 lambda` has no
equal-height copy in the visible region, while `d=lambda` reaches copies at the
two endfire boundaries. Half-wavelength spacing is the familiar guarantee for
unique steering over the full visible direction-cosine interval (with the
usual shared `+/-90 deg` endpoint boundary).

## Taper changes the aperture illumination

Uniform weights let the edge elements contribute fully. The lesson constructs
the symmetric Hamming weights directly:

```text
w_m = 0.54 - 0.46 cos(2 pi m/(M-1)).
```

Reducing edge contributions smooths the abrupt aperture boundary. The peak
sidelobe falls by more than `15 dB` in the reviewed case, but the effective
aperture shrinks and HPBW grows by more than `5 deg`. Taper does not remove a
true grating lobe: at an aliased direction every sampled phase is the same as
at the intended direction, so the same fixed weights add coherently in both.

## The intentionally broken case and recovery

The broken case steers to `+30 deg` with `d=lambda`. The order `k=-1` gives

```text
sin(theta_g) = sin(30 deg) - 1 = -0.5,
theta_g = -30 deg.
```

The `+30 deg` intended beam and `-30 deg` false beam are exactly equal at all
eight sampled elements. Calling the narrower local peak an improvement while
ignoring the false copy is the intended failure. Neither a finer plot grid nor
a taper restores information that was never sampled.

Recovery changes only spacing back to `lambda/2`. The old `-30 deg` direction
then produces alternating element phases and cancels exactly for eight uniform
elements, while the `+30 deg` steering direction stays coherent.

## Limiting cases and model boundary

- One element has no aperture, so its ideal isotropic array factor is flat.
- If all elements become co-located (`d -> 0`), normalized response becomes
  flat even when `M>1`; there is no spatial phase diversity.
- As aperture grows, the beam narrows in direction cosine. Away from
  broadside, mapping through inverse sine makes degree-domain beamwidth wider
  and asymmetric.
- At endfire, the broadside-referenced sine mapping reaches its boundary; a
  ULA cannot distinguish all 3-D directions sharing the same projected
  direction cosine.
- The ideal array factor multiplies, rather than replaces, a real element
  pattern. Isotropic elements are used here to isolate the array geometry.
- The model assumes a far-field plane wave, narrowband phase across the full
  aperture, synchronized calibrated channels, no mutual coupling, and no
  multipath. P67 will deliberately disturb calibration and coupling.

## Common interpretation mistakes

- Using cosine while labeling angle from broadside mixes angle conventions;
  this lesson requires sine.
- Calling every secondary peak a grating lobe confuses ordinary finite-aperture
  sidelobes with equal-height spatial replicas.
- Measuring `-3 dB` at amplitude `0.5` uses a `-6.02 dB` point. Half power is
  amplitude `1/sqrt(2)`.
- Measuring PSL after clipping at the display floor can invent a metric.
- Saying larger `M` always removes spatial aliases confuses narrower local
  lobes with uniqueness.
- Saying taper fixes aliasing ignores that intended and aliased steering
  vectors are identical at the sampled locations.
- Treating `(M-1)d` as an exact beamwidth formula skips the discrete coherent
  sum and the nonlinear sine-to-angle mapping.

## Dependencies, compatibility, and claim boundary

P61 is the ordered prerequisite and supplies the steering-vector phase slope.
P12 and P33 give useful window/taper analogies. The experiment uses base
MATLAB, direct complex arithmetic, bounded loops, and a private deterministic
probe generator that does not alter global random state. It writes no file,
uses no network, timer, worker, or persistent checkpoint, and requires
script-local functions (MATLAB R2016b or newer). Static and independent Python
checks do not prove MATLAB parsing/execution, rendered figures, educational
effectiveness, antenna behavior, hardware/HIL, real-time, field, deployment,
or production performance.
