# P61 lesson: Direction Becomes a Spatial Phase Slope

## Guiding question

How does a direction of arrival become a phase slope across sensors?

## The physical picture

Place identical sensors along the positive x-axis and look broadside,
perpendicular to the array. A far-away source produces an almost flat wavefront.
At broadside that wavefront reaches every sensor together. When the source moves
toward one end of the array, the wavefront reaches that end first. A narrowband
receiver sees this small time advance as a phase advance from one sensor to the
next.

P61 numbers elements as `m = 0, 1, ..., M-1`, measures `theta` from broadside,
and calls angles toward the positive-x end positive. Its analytic carrier is
`exp(+j 2 pi f t)`. With this convention, positive angle creates a positive,
counterclockwise phase slope across increasing element index. A different sign
convention is valid only if geometry, delay, phase, and inverse-angle signs all
change together.

## From geometry to the steering vector

For spacing `d`, element position is `x_m = m d`. Relative to element zero, the
arrival-time delay is

```text
tau_m = -m d sin(theta) / c.              seconds
```

The negative sign says the positive-x element receives an advance for a
positive angle. With wavelength `lambda = c/f`, one simultaneous ideal complex
sample is

```text
x_m = A exp(j(phi_0 - 2 pi f tau_m))
    = A exp(j(phi_0 + 2 pi m (d/lambda) sin(theta))).
```

Therefore each step along the ULA adds

```text
Delta_phi = 2 pi (d/lambda) sin(theta)    rad/element.
```

The vector of these complex samples is the receive steering vector. The script
constructs every exponential directly; no array toolbox object hides the path
delay or phase operation.

## Reading the baseline plots

At 3 GHz, the wavelength is about `0.09993 m`. The eight-element baseline uses
half-wavelength spacing and a `+30 deg` source. Its ideal adjacent phase step is
exactly `pi/2 rad/element`, while its adjacent arrival-time advance is
`-83.333 ps`. The I/Q point rotates counterclockwise as sensor index grows.

Principal phase is confined to `[-pi, pi]`, so the first phase plot has jumps.
In this unambiguous case, `unwrap` removes representation jumps. A straight-line
fit then estimates the spatial slope and inverts the model:

```text
theta_hat = asin(Delta_phi_hat * lambda / (2 pi d)).
```

The seeded noise makes the fit imperfect but repeatable. The fit uses all eight
sensors; the adjacent conjugate product
`conj(x_m) x_(m+1)` provides a second visible estimate of the same step.

## What the controlled sweeps expose

### Arrival angle

At fixed spacing and frequency, slope follows `sin(theta)`. Broadside produces
zero slope. Equal positive and negative angles produce equal and opposite
slopes. Near endfire, equal angle increments do not produce equal slope
increments because sine flattens.

### Spacing and frequency

Both act through electrical spacing `d/lambda`:

- increasing physical `d` increases geometric delay and phase;
- increasing `f` while physical `d` stays fixed shortens wavelength and
  increases phase, but geometric delay does not change.

The two paths in Figure 4 reach the same electrical spacings and therefore the
same slopes. If `d` were silently reset to `lambda/2` at every frequency, the
frequency effect would disappear; that would be a different experiment.

## The intentionally broken case: spatial aliasing

At `d = lambda`, a source at `asin(0.6) = 36.87 deg` advances phase by `1.2 pi`
per element. The sampled principal step is `-0.8 pi`, exactly the step produced
by `asin(-0.4) = -23.58 deg`. Their complex samples are identical at every
integer sensor position. A principal-step inverse therefore returns the false
negative angle.

`unwrap` cannot repair this. It sees only sampled phases and chooses a locally
short step; the missing full spatial cycle was never measured. Recovery restores
half-wavelength spacing while keeping source, frequency, element count, and
initial phase fixed. The true step becomes `0.6 pi`, inside the principal
interval, and the inferred angle returns exactly.

## Limiting cases and model boundary

- At broadside, `sin(theta)=0`, so ideal phase is flat across sensors.
- As spacing or frequency approaches zero, slope approaches zero and angle
  becomes poorly observable from phase.
- One sensor has no inter-element slope. More sensors improve a noisy fit but
  do not remove an alias created by excessive spacing.
- `d <= lambda/2` is the familiar full-field sampling rule, but at exactly
  half wavelength the two endfire endpoints share the `+/-pi` boundary. For a
  smaller scan sector, the uniqueness condition can be relaxed accordingly.
- A linear array measures the direction cosine along its axis; without another
  aperture it cannot resolve every 3-D direction or distinguish front/back
  elevation configurations that share that direction cosine.
- The plane-wave model assumes far field, a narrowband signal over the array
  delay spread, synchronized calibrated channels, and negligible coupling and
  multipath. P67 will deliberately violate calibration assumptions.

This is one-way propagation between a source and array elements. Do not copy
P36's monostatic Doppler factor of two: P36 measures a round-trip path change;
P61 measures a one-way inter-sensor path difference.

## Common interpretation mistakes

- Measuring from the array axis but using the broadside `sin(theta)` equation
  mixes sine and cosine conventions.
- Reversing the adjacent conjugate-product order reverses the inferred sign.
- Treating a wrapped principal step as a unique physical slope ignores spatial
  sampling.
- Believing `unwrap` knows the true angle gives it information not present in
  the samples.
- Holding `d/lambda` fixed during a frequency sweep hides the intended
  frequency sensitivity.
- Calling the spatial samples a beam pattern skips ahead: P61 observes phase;
  P62 and P63 will form patterns and combine channels.

## Dependencies and claim boundary

P60 is the ordered prerequisite. P01 provides phasors, P20 provides noisy phase
estimation, and P36 provides the analogous phase slope in time. The experiment
uses base MATLAB arithmetic, bounded arrays, and a private deterministic normal
generator that does not alter MATLAB's global random stream. It writes no files,
uses no network, timer, worker, or persistent state, and makes no MATLAB runtime,
hardware/HIL, real-time, field, or operational-radar claim by itself.
