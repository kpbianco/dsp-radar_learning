# P81 lesson: The Target Moves the Aperture

The guiding question is: **How does target rotation create synthetic aperture when the radar is stationary?**

P75-P80 moved a radar along a known path and used the changing look direction
to focus a stationary scene. P81 reverses the roles. The radar phase center
stays fixed. A rigid target rotates, so each scatterer presents a changing
two-way path. Relative motion is what creates angular diversity; the processor
does not care which side supplied it until motion compensation and coordinate
interpretation are needed.

## One explicit coherent echo model

Let scatterer `i` have target-fixed cross-range `x_i`, down-range `y_i`, and
complex reflectivity `a_i`. At aspect `theta_p`, its small-scene projected
range relative to the target centroid is

```text
r_i(theta_p) = x_i sin(theta_p) + y_i cos(theta_p).
```

If the centroid also translates by `d_p`, the coherent response at stepped
frequency `f_k = f_c + Delta f_k` is

```text
H[p,k] = sum_i a_i exp(-j 4 pi f_k
                        (d_p + r_i(theta_p))/c).
```

The `4 pi` is the monostatic outbound-plus-return phase. The script evaluates
this sum directly. There is no ISAR, phased-array, waveform, or image object
hiding the operation.

An IFFT across increasing `Delta f_k` performs range compression. Frequency
span `B` gives the familiar nominal range resolution

```text
delta_r approximately c/(2 B).
```

At `B = 600 MHz`, that is `0.25 m`. Complex phase must survive this step;
magnitude-only range profiles cannot later align cross-range phasors.

## Translation compensation has two inseparable parts

The known centroid translation is removed before range compression by

```text
H_aligned[p,k] = H[p,k] exp(+j 4 pi f_k d_p/c).
```

Using the full `f_k`, not only the carrier, matters:

- the offset-frequency term moves the range envelope back to one range cell;
- the carrier term restores the common pulse-to-pulse phase needed for focus.

Shifting only magnitude rows may make a range-profile plot look aligned while
leaving a carrier-phase error. Correcting only carrier phase preserves
coherence but leaves the envelope migrating. P81 performs both in one complex
multiplication.

## Rotation becomes cross-range phase slope

For a small aspect angle in radians,

```text
sin(theta) approximately theta,
cos(theta) approximately 1,
r_i(theta) approximately y_i + x_i theta.
```

After range compression has separated `y_i`, the carrier phase versus angle is

```text
s_i(theta) approximately A_i exp(-j 4 pi x_i theta/lambda).
```

That is a tone in angle with spatial frequency `-2 x_i/lambda` cycles per
radian. The explicit angle-domain FFT therefore uses

```text
x = -(lambda/2) f_theta.
```

The sign follows this experiment's positive-angle and FFT conventions. Change
either convention and the image can mirror without changing its focus.

For total angular aperture `Delta theta`, the small-angle cross-range scale is

```text
delta_x approximately lambda/(2 Delta theta).
```

At `10 GHz`, `lambda = 0.03 m`; a `6 deg` (`0.1047 rad`) aperture gives about
`0.143 m`. This is a point-response scale under the reviewed assumptions, not
a guarantee that every pair of aspect-dependent scatterers is resolved.

## Sweep 1: angular aperture is the synthetic aperture

The first sweep holds carrier, bandwidth, target, look count, reflectivity,
rotation-rate convention, and exact motion compensation fixed. It changes only
total aspect support: `2`, `4`, `6`, and `8 deg`.

The nominal `lambda/(2 Delta theta)` resolution decreases as angular support
grows. Layout correlation improves in the reviewed scene because cross-range
responses separate. The angular sample spacing also grows because look count
is fixed, so the unambiguous cross-range interval shrinks. A wider aperture is
not free: it needs adequate angular sampling, coherence, and a model that
remains valid over the larger rotation.

Limiting cases:

- At zero angular aperture there is range information but no cross-range
  phase diversity; an angle FFT cannot locate `x_i`.
- A very small nonzero aperture gives coarse cross-range response.
- A larger well-sampled aperture sharpens cross-range approximately as
  `1/Delta theta`.
- A very large aperture violates the linear small-angle model: `sin(theta)` is
  nonlinear and `y_i cos(theta)` migrates and adds phase curvature.
- Angular undersampling produces cross-range aliases even if the total aperture
  is long.

## Sweep 2: rate changes the clock, not fixed angular support

The second sweep uses the same 65 aspect angles from `-3` to `+3 deg`, but
rotation rates `3`, `6`, and `12 deg/s`. With angle `theta = omega t`, the CPI
is

```text
T_CPI = Delta theta/omega.
```

The cross-range Doppler for the small-angle model is approximately

```text
f_D,i = -(2/lambda) x_i omega.
```

Doubling rate halves the time needed to collect the same angles and doubles
the Doppler spread in hertz. After the processor uses the known angle samples,
the focused images match. Rotation rate alone does not improve cross-range
resolution when total angular aperture is held fixed.

Because the look count and aspect samples are fixed, their elapsed spacing also
changes: the implied PRFs are `32`, `64`, and `128 Hz`. Rotational Doppler stays
inside each corresponding Nyquist interval. The declared `2 m/s` centroid
motion would not be unambiguously inferable as an ordinary sampled Doppler at
those PRFs; this controlled experiment supplies its unwrapped displacement
sample by sample as known external motion-compensation information. It does not
claim to estimate translation from the slow-time record.

If CPI were held fixed instead, faster rotation would collect a larger angular
aperture and could improve resolution. That is a different controlled
experiment because two linked quantities change. Unknown or nonuniform rate
also makes an ordinary uniformly sampled slow-time FFT use the wrong angle
grid; resampling or motion estimation would be required.

## Broken case: leave translation uncompensated

The baseline centroid moves `2 m` from the first look to the last. Without the
frequency-dependent correction, scatterer envelopes occupy different range
bins and the wideband phase couples that range walk into the angle transform.
An angle FFT then combines unlike range samples, so the point layout smears and
correlation with the aligned image falls below the reviewed bound. The carrier
part of this constant-velocity translation is a linear phase ramp versus angle;
by itself it primarily shifts or wraps cross-range rather than defocusing a
point. Nonlinear residual translation would add true cross-range defocus.

This is not rotational range migration. Translational centroid motion is
common to every scatterer and is deliberately known here. Rotational migration
comes from the exact `x sin(theta) + y cos(theta)` geometry and becomes more
important for larger targets or aspect spans.

Recovery does not sharpen the broken magnitude image. It returns to the
numerically unchanged raw complex `H[p,k]`, applies full translation
compensation, range-compresses, and angle-focuses again. The recovered history
and image exactly match the earlier baseline within the script's deterministic
operation path.

## What the image means—and does not mean

- The vertical coordinate is projected range offset, not always literal
  target-fixed `y` outside the small-angle limit.
- The horizontal coordinate comes from rotational phase slope and the declared
  sign convention.
- Brightness is coherent complex reflectivity convolved with range and
  cross-range point responses; it is not calibrated RCS.
- Isotropic fixed scatterers make the shape stable. Real scattering centers
  can appear, disappear, scintillate, or move with aspect.
- Known rigid rotation makes the angle grid exact. Real ISAR generally must
  estimate translation, phase, and rotational motion from the data.
- A sharp-looking result is not proof that the motion model or absolute scale
  is correct. Incorrect rate can stretch cross-range; a phase ramp can shift or
  mirror a sharp image.

## Common interpretation mistakes

- Saying the stationary radar provides no aperture ignores relative aspect
  change supplied by target rotation.
- Saying faster rotation always gives finer cross-range confuses hertz/CPI
  with total angular support.
- Calling this a fixed-PRF rate sweep ignores that fixed look angles make PRF
  change with rate; known displacement is supplied rather than estimated.
- Using degrees inside the phase slope or resolution equation misses the
  required radians.
- Using `2 pi` instead of `4 pi` forgets the monostatic round trip.
- Aligning only range-profile magnitudes destroys or ignores carrier phase.
- Calling all blur translation error ignores rotational migration, angular
  nonlinearity, changing scatterers, and rate errors.
- Calling a pure linear carrier-phase ramp defocus ignores its shift/steering
  interpretation; the broken image also contains wideband envelope migration.
- Reading the small-angle axes as an exact Cartesian photograph over a large
  turn overstates the model.
- Trusting separately peak-normalized colors hides coherent loss; use retained
  truth-neighborhood power and image correlation metrics.

## Dependencies, compatibility, resources, and claim boundary

P18, P30, P36, P61-P63, and P75-P80 provide complex phase, two-way delay,
coherent slow time, spatial phase slope, SAR history, range compression,
focusing, migration, resolution, and coherence context. The script targets
base MATLAB R2016b or newer, uses explicit finite foreground loops plus base
`fft`/`ifft`, and uses a private seeded Park-Miller generator without touching
MATLAB's global random stream.

It creates exactly five tagged figure groups, schedules `670,800` explicit
scatterer-frequency-look contributions under a `900,000` ceiling, caps private
generator output at 64 values, and caps retained function-workspace inventory
at 2,500,000 eight-byte value equivalents. That inventory is a live-workspace
estimate, not peak MATLAB memory. The script performs no file/network I/O,
timer, worker, GPU, shell, checkpoint, or persistent-state operation. Ctrl+C
cancels finite foreground work; rerunning closes stale P81 figures and
reconstructs private state.

Static checks and the independent Python oracle do not prove MATLAB parsing,
figure rendering, runtime performance, educational effectiveness, real-target
scattering fidelity, physical radar/HIL, bench, real-time, field, RT1/RT2,
Unreal, operational radar, signing, deployment, or production behavior.

## Completion connection

You are ready to continue when you can explain that rigid target rotation
creates a two-way phase slope versus aspect; angular aperture, wavelength, and
angular sampling set the cross-range view; rate changes CPI and Doppler hertz
when angle support is fixed; and translation must be removed in complex
frequency history before range compression and angle focus.
