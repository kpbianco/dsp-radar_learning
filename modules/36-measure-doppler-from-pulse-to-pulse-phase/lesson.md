# P36 lesson: Pulse-to-Pulse Phase Is Doppler

## Guiding question

How does target velocity create coherent phase progression across pulses?

## The physical picture

Imagine looking at the same target range bin after every transmitted pulse.
If the radar and target keep a common phase reference, each complex sample is
another look at the target's carrier phase. A moving target changes the
round-trip path slightly between looks, so the I/Q phasor rotates by nearly
the same angle every pulse. That sequence of samples is **slow time**.

This lesson defines positive radial velocity as motion **toward** the radar.
An approaching target therefore has positive Doppler and counterclockwise
phase progression. A receding target has negative Doppler and clockwise
progression. Some radar texts use the opposite velocity convention; the
equations are consistent only when the convention is stated.

## From velocity to phase step

At carrier frequency `f_c`, the wavelength is

```text
lambda = c / f_c.
```

A monostatic radar sees a two-way path change, so

```text
f_d = 2 v_r / lambda = 2 v_r f_c / c.
```

The factor of two is physical: target motion changes both the outbound and
return path. With pulse repetition interval `T_r = 1/PRF`, the ideal complex
sample at pulse index `p` is

```text
x[p] = A exp(j(phi_0 + 2 pi f_d p T_r)).
```

The angle between adjacent pulses is consequently

```text
Delta_phi = angle(conj(x[p]) x[p+1])
          = 2 pi f_d / PRF                 rad/pulse.
```

The script averages adjacent conjugate products before taking the angle. It
also unwraps phase and fits a straight-line slope. Both expose the operation;
neither hides velocity inside a radar toolbox helper.

## The slow-time FFT

Across `N` pulses sampled at the PRF, Doppler behaves like an ordinary
discrete-time tone. The centered FFT grid has spacing

```text
Delta_f_d = PRF / N,
Delta_v   = lambda PRF / (2 N).
```

The FFT peak is a grid report, not an infinitely precise velocity. A true
Doppler between bins lands on the nearest bin and leaks into neighbors. More
coherent pulses extend observation time and narrow the bin spacing, but they
do not change the PRF or widen the unambiguous interval.

## What the sweeps isolate

### Signed velocity

At fixed carrier and PRF, Doppler and phase step are linear in radial
velocity. Zero velocity gives a flat phase sequence. Reversing velocity
reverses the phasor rotation and moves the FFT peak to the other side of zero.
The amplitude alone cannot reveal this sign.

### Carrier frequency

At the same physical velocity, a higher carrier has a shorter wavelength.
The same path change is therefore a larger fraction of a cycle, producing
larger `f_d` and phase step. The target did not speed up; the radar became more
phase-sensitive. At fixed PRF the unambiguous speed magnitude decreases as
wavelength decreases.

### Pulse count

At fixed PRF, increasing `N` narrows `PRF/N`. It improves the FFT grid and the
ability to separate nearby constant Dopplers during a coherent dwell. It does
not improve the unambiguous velocity limit, and real coherence loss can stop
longer dwells from helping.

## Limiting cases and aliasing

- At `v_r = 0`, `f_d = 0` and ideal phase is constant.
- Positive and negative velocities of equal magnitude have opposite phase
  slopes and symmetric Doppler locations.
- Pulse-to-pulse samples observe phase modulo `2*pi`. Dopplers separated by an
  integer multiple of PRF make the same samples.
- The signed unambiguous interval is `[-PRF/2, PRF/2)`, corresponding to
  `|v_r| < lambda PRF/4` away from the endpoint convention.
- A Doppler at or beyond that boundary aliases; unwrapping the already sampled
  phase cannot restore the missing cycle count.
- Acceleration, range migration, oscillator phase noise, clutter, multipath,
  missed detections, and fluctuating targets violate this ideal constant-tone
  model and belong to later processing stages.

P35 showed that periodic pulses make fast-time range ambiguous. P36 applies
the same sampling logic in slow time: the PRF samples Doppler and therefore
sets its aliasing interval. P18 supplies the signed complex-frequency picture,
P20 supplies noisy phase estimation, and P34 places Doppler beside delay in a
waveform response.

## Why the broken case fails

Taking `abs(x[p])` preserves return strength but discards the complex angle.
For a constant-amplitude target the resulting slow-time sequence is nearly
constant, so its spectrum sits at zero Doppler. The phase increment becomes
zero and approach cannot be distinguished from recession. This is not a
stationary-target measurement; it is a processing chain that threw away the
measurement needed for signed velocity.

Recovery restores the original complex coherent samples and recreates the
noise with the same private seed. The recovered phase estimate and samples
must match the baseline exactly.

## Common interpretation mistakes

- Omitting the monostatic factor of two gives the wrong velocity.
- Treating wrapped phase jumps as physical reversals confuses representation
  with motion.
- Calling the nearest FFT bin the exact Doppler ignores finite-grid error.
- Claiming more pulses widen the unambiguous interval confuses resolution with
  sampling rate.
- Claiming higher carrier changes target velocity confuses sensitivity with
  motion.
- Using magnitude-only integration and expecting signed Doppler ignores the
  coherent phase observable.

## Model and compatibility boundary

The experiment uses seeded synthetic complex samples at one already-selected
range bin. Base MATLAB arithmetic exposes the target model, adjacent product,
phase slope, window, FFT, axes, and conversions. It does not simulate waveform
propagation or prove MATLAB runtime, toolbox, hardware, HIL, field, real-time,
detector, deployment, or operational performance.
