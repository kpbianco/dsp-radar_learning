# P80 lesson: Millimetres of Motion Become Radians of Phase

The guiding question is: **How small a platform-position error is enough to blur a coherent image?**

P79 sharpened a point by collecting a long synthetic aperture. That sharpness
depends on knowing the relative phase of every look. P80 keeps the same basic
coherent sum and asks what happens when the actual line-of-sight platform path
departs from the planned path by only a few millimetres.

## From path error to a common phase screen

For platform position `x_p` and target `(x_t,R_t)`, the planned slant range is

```text
R_p,t = sqrt((x_p-x_t)^2 + R_t^2).
```

Ignoring one constant reference-range rotation, the ideal monostatic phase
history in one range gate is

```text
s_p,t = a_t exp(-j 4 pi (R_p,t-R_ref)/lambda).
```

Suppose an unmeasured line-of-sight position error `delta R_p` changes slowly
enough across this small scene that every range gate sees approximately the
same extra path. The received signal gets the multiplicative phase screen

```text
e_p = exp(j delta phi_p),
delta phi_p = -4 pi delta R_p/lambda,
s_error,p,t = s_p,t e_p + n_p,t.
```

The `4 pi` contains both the outbound and return path. A one-way line-of-sight
error of `lambda/2` produces a full `2 pi` phase turn. At the experiment's
`10 GHz` carrier, `lambda = 30 mm`; therefore:

| Path-error RMS | Millimetres | Two-way phase RMS |
|---|---:|---:|
| `lambda/32` | `0.9375 mm` | `pi/8 rad` |
| `lambda/16` | `1.875 mm` | `pi/4 rad` |
| `lambda/8` | `3.75 mm` | `pi/2 rad` |
| `lambda/4` | `7.5 mm` | `pi rad` |

This conversion—not MATLAB syntax—is why radar navigation tolerances can be
far smaller than a range-resolution cell.

## Why varying phase blurs while constant phase does not

The nominal focuser still compensates the planned path:

```text
I_t(x) = (1/P) sum_p s_error,p,t
                  exp(+j 4 pi (R_p(x)-R_ref)/lambda).
```

At the correct target coordinate, the planned propagation phase cancels, but
`delta phi_p` remains. If it varies across the aperture, the remaining phasors
no longer point together: the coherent peak falls and energy spreads across
cross-range. The experiment measures both mean peak retention and mean entropy
of the three cross-range cuts. Peak retention falls with lost coherence;
cross-range-cut entropy rises when energy spreads along that axis.

Important limiting cases make the language precise:

- A **constant** phase screen rotates the complex image but does not blur its
  magnitude.
- A **linear** phase ramp mainly shifts the cross-range image because it looks
  like a steering error.
- Curved or irregular aperture phase changes the point-spread shape and causes
  defocus.
- A gross range error can also move energy between range cells. This local
  experiment assumes P78-style range alignment has already isolated gates.

Motion error can contain constant, linear, and defocusing parts together.
Autofocus cannot uniquely label all of them without external position or scene
information.

## The explicit phase-gradient autofocus estimate

The strongest target occupies its own range gate. Its nominal phase is known
from the planned geometry, so the script first deramps that gate:

```text
z_p = s_error,p,ref exp(+j 4 pi (R_p,ref-R_ref)/lambda).
```

Ideally `z_p = a_ref exp(j delta phi_p)`. Its unknown target phase is a
constant. Instead of taking one wrapped phase angle and hoping it never crosses
`+/-pi`, the script measures adjacent gradients:

```text
g_p = angle(z_p conj(z_(p-1))),
phi_hat_p = phi_hat_(p-1) + g_p.
```

It then applies one common correction to every range gate:

```text
s_corrected,p,t = s_error,p,t exp(-j phi_hat_p).
```

The estimate is defined only up to one constant phase, which does not matter to
focused magnitude. The reviewed error templates keep every adjacent true phase
step below `0.9 pi`, avoiding gradient wrapping. The reference has `35 dB`
measurement SNR, so correction is close but not magically exact.

This is a deliberately small phase-gradient autofocus concept. Production PGA
usually selects prominent scatterers across many range bins, recenters image
energy, rejects bad bins, filters gradient estimates, iterates, and manages
linear-phase ambiguity. Nothing here claims that full algorithm.

## Read the two sweeps differently

### Error-magnitude sweep

The first sweep holds one mixed smooth/short-correlated error shape fixed and
scales only its RMS from zero through `lambda/4`. Because

```text
phase RMS = 4 pi (path-error RMS)/lambda,
```

the last case has `pi rad` RMS. Uncorrected coherent peak decreases
monotonically in the reviewed scene while cross-range-cut entropy increases. Autofocus uses
the same retained noisy measurement rule for every case and restores the mean
peak above `0.95` of ideal.

Do not turn `lambda/16` or any other fraction into a universal blur threshold.
Coherent loss depends on the phase-error distribution, spatial correlation,
aperture weighting, target scene, and metric. The sweep answers “how small” for
this declared scene and shows the governing wavelength scale.

### Error-composition sweep

The second sweep fixes path RMS at `lambda/8` and changes the normalized shape
from smooth to short-correlated. Equal RMS does not imply the same point-spread
shape. A smooth low-order error may produce a broad structured distortion; a
short-correlated error spreads energy differently and asks the gradient
estimator to follow larger adjacent changes.

The plot includes the largest adjacent phase step. This is an observability and
sampling check, not a claim that every below-`pi` error is easy to estimate in
noise.

## Intentionally broken case: a non-isolated reference

The correct estimator relies on one dominant range-isolated scatterer. The
broken case adds `0.95` times a second target's history into that gate before
estimating the gradient. After deramping for target one, target two retains its
own deterministic aperture phase. The angle of their vector sum mixes scene
structure with motion:

```text
z_broken,p = z_ref,p + 0.95 z_interferer,p.
```

That estimate still may improve part of the image, but it materially
underperforms the isolated-gate estimate. The failure is not “autofocus always
worsens images”; it is “a violated dominant-scatterer assumption biases this
estimator.”

Recovery starts from the numerically unchanged retained errored phase history,
selects the isolated gate, estimates again, and freshly refocuses. It
does not apply a cosmetic sharpening filter to the broken image.

## What autofocus can and cannot know

- Autofocus estimates residual phase from scene data; navigation-aided motion
  compensation uses external trajectory measurements. They can complement one
  another.
- A common phase screen can be corrected across this local scene. Wide scenes,
  squint, topography, and range-dependent motion may require space-variant
  correction.
- A strong point-like reference makes this demonstration observable. Distributed
  scenes, moving targets, low SNR, and several comparable scatterers can bias or
  destabilize the estimate.
- Constant phase is unobservable in image magnitude. Linear phase is entangled
  with image position. Autofocus may sharpen while leaving an absolute phase or
  location bias.
- Cross-range-cut entropy and peak concentration are focus metrics, not proof
  that geographic coordinates or reflectivity amplitudes are correct.

## Common interpretation mistakes

- Using `2 pi delta R/lambda` forgets the monostatic round trip; the experiment
  uses `4 pi`.
- Comparing millimetres with `c/(2B)` misses the issue. Range resolution and
  carrier-phase coherence are different scales.
- Saying any nonzero path error blurs ignores constant and linear components.
- Calling a shifted sharp point “defocused” confuses location with width.
- Calling an autofocus estimate a recovered navigation trajectory ignores its
  constant/linear ambiguities and scene dependence.
- Judging only a peak-normalized image hides coherent-gain loss. P80 retains
  peak relative to the ideal image before display normalization.
- Treating lower cross-range-cut entropy as guaranteed truth ignores the possibility of
  over-focusing one bright scatterer or using the wrong scene model.
- Believing autofocus reconstructs discarded range cells ignores P78; this
  lesson begins after range gates are aligned.

## Dependencies, compatibility, resources, and claim boundary

P18, P30, P36, P61-P63, and P75-P79 provide complex phase, two-way geometry,
spatial sums, phase history, range separation, focusing, migration correction,
and aperture-resolution context. The experiment uses base MATLAB R2016b or
newer, explicit complex operations, finite foreground loops, and a private
Park-Miller/Box-Muller generator that does not alter global random state.

It creates exactly five tagged figure groups, schedules `4,283,025` coherent
contributions under a `4,500,000` ceiling, and caps the retained function
workspace inventory at `2,000,000` eight-byte value equivalents. It performs
no file or network I/O, timer,
worker, GPU, shell, checkpoint, or persistent-state operation. Ctrl+C cancels
finite foreground work; rerunning closes stale P80 figures and reconstructs
all private state.

Static checks and the independent Python oracle do not prove MATLAB parsing,
figure rendering, runtime performance, educational effectiveness, navigation
accuracy, hardware/HIL, bench, real-time, field, operational radar, signing,
deployment, or production behavior.

## Completion connection

You are ready to continue when you can say: a one-way aperture path error
creates twice-traveled phase `-4 pi delta R/lambda`; only the
aperture-varying part destroys coherent focus; a scene-derived phase-gradient
estimate can restore a shared phase screen when a strong range-isolated
scatterer makes the error observable, but scene contamination and phase
ambiguities limit what autofocus can recover.
