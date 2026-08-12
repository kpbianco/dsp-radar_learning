# P71 lesson: One Beat, Two Causes

## Guiding question

Why can target motion bias the range estimated from one chirp?

## Physical mental model

An up-chirp is a rising whistle. A delayed copy lags behind the whistle, so
mixing transmit and echo produces a pitch proportional to round-trip delay.
A moving target shifts the whole echo whistle through Doppler at the same
time. The mixer hears only the combined pitch; it does not attach labels that
say which part came from delay and which part came from motion.

P17 established complex mixer signs, P36 connected radial velocity to signed
Doppler, P69 established the stationary FMCW range law, and P70 intentionally
kept range beat and slow-time Doppler separate. P70 is this lesson's governed
prerequisite. P71 restores the Doppler term inside one chirp.

## Declare the signs before interpreting the beat

This module retains the earlier repository conventions:

- the dechirp mixer is `tx .* conj(rx)`;
- the waveform is an up-chirp with positive slope `S`;
- positive radial velocity means approaching; and
- approaching motion produces positive carrier Doppler `f_d = 2v/lambda`.

For a centered complex chirp and a frozen round-trip delay `tau = 2R/c`,

```text
tx(t) = exp(j pi S (t - T/2)^2),
rx(t) = exp(j pi S (t - tau - T/2)^2 + j 2 pi f_d t + j phi).
```

Multiplying `tx(t)` by `conj(rx(t))` makes a complex beat whose time-dependent
phase is

```text
2 pi (S tau - f_d)t.
```

The constant phase terms change the phasor's starting angle but not its beat
frequency. The signed result is therefore

```text
f_beat = f_delay - f_d = S(2R/c) - 2v/lambda.
```

The sign is not universal across every radar text: changing mixer order,
velocity sign, or chirp direction changes the displayed signs. The physical
lesson is invariant only after the convention is declared.

## The stationary conversion becomes biased

P69's stationary conversion assumes every hertz of beat came from delay:

```text
R_stationary = c f_beat/(2S).
```

Substitute the moving-target beat:

```text
R_stationary = R - c f_d/(2S)
             = R - f_c v/S,
range bias   = R_stationary - R = -f_c v/S.
```

With the baseline `R = 45 m`, `v = +20 m/s`, `f_c = 77 GHz`, and
`S = 0.5 THz/s`, the delay contribution is `150 kHz`, Doppler is about
`10.267 kHz`, and the measured beat is about `139.733 kHz`. Treating it as a
stationary beat reports about `41.920 m`: an approaching target is biased
`3.080 m` too near.

The target moves only `0.8 mm` during this `40 us` chirp. That is not the
`3.080 m` range bias. The bias is a frequency-interpretation error amplified
by `c/(2S)`, not the distance traveled during the measurement.

## Why one chirp cannot untangle the terms

One signed beat supplies one equation:

```text
f_beat = S(2R/c) - 2v/lambda.
```

Both `R` and `v` are unknown. A moving target at `45 m` can produce exactly
the same beat as a stationary target at `41.920 m` in the baseline. A clean,
high-SNR beat or a larger FFT cannot resolve this ambiguity because both
scenes generate the same ideal tone.

If velocity is supplied independently, the same measurement can be corrected:

```text
R_corrected = c(f_beat + f_d)/(2S).
```

P70 obtains Doppler from coherent chirp-to-chirp phase under its model. P72
will show how opposite up/down slopes provide another equation. The important
boundary here is that the correction must not pretend velocity was discovered
from this one beat alone.

## Sweep 1: velocity controls sign and size

Holding range, carrier, and slope fixed gives a straight line:

```text
range bias = -(f_c/S)v.
```

For velocities `-30, -15, 0, +15, +30 m/s`, the reviewed biases are
`+4.62, +2.31, 0, -2.31, -4.62 m`. Receding motion raises the beat under this
convention and appears too far; approaching motion lowers it and appears too
near. Zero velocity restores P69 exactly. Every case reuses the same private
noise samples so velocity is the only changed input.

## Sweep 2: slope controls the conversion scale

The bandwidth sweep changes only `B` while chirp duration stays `40 us`, so
`S = B/T` changes. At `v = +20 m/s`, bandwidths of
`10, 15, 20, 25, 30 MHz` produce biases of approximately
`-6.160, -4.107, -3.080, -2.464, -2.053 m`.

Steeper slope makes delay contribute more beat frequency per meter while the
same carrier Doppler stays fixed. Ignoring Doppler is therefore less damaging
in meters, though it never becomes conceptually valid merely because the error
is small. The same private noise samples are reused across these cases too.

## Intentionally broken correction and recovery

The correct correction adds the approaching Doppler back to the measured
beat. The broken path subtracts it:

```text
R_wrong = c(f_beat - f_d)/(2S).
```

For the baseline, this doubles the original error and reports `38.840 m`.
Recovery reuses the unchanged measured beat and the same independently known
velocity, changes only the correction sign, and returns `45.000 m`. This
isolates sign interpretation rather than regenerating a favorable signal.

## Signed-frequency and limiting cases

- At `v = 0`, Doppler vanishes and P69's stationary law is recovered.
- As positive slope grows, `|f_c v/S|` shrinks. At zero slope, FMCW range
  conversion is undefined.
- When `f_d = S tau`, the signed beat is DC and a nonzero approaching target
  appears at zero range under the stationary assumption.
- When `f_d > S tau`, the beat becomes negative. Taking magnitude or retaining
  only a positive FFT half discards essential direction information.
- If `|f_beat| >= fs/2`, sampled beat frequency aliases and neither the naive
  nor corrected estimate is trustworthy.
- If `tau >= T`, the transmitted and delayed copies do not overlap within the
  reviewed chirp record.
- A denser zero-padded FFT interpolates the spectrum; it does not create a
  second equation for range and velocity.
- The frozen-delay, carrier-Doppler model assumes constant velocity and
  negligible range migration/stretch during one chirp. Long chirps, extreme
  motion, or wide fractional bandwidth require a more exact time-scaling
  model.

## Common interpretation mistakes

- Saying approaching motion always raises the dechirped beat ignores mixer and
  chirp sign. Under this declared convention it lowers the up-chirp beat.
- Calling the range bias target travel confuses measurement interpretation
  with physical displacement.
- Using `abs(f_beat)` silently turns a signed ambiguity into a false positive
  range.
- Claiming a high-resolution FFT separates range and velocity ignores that one
  tone still supplies only one equation.
- Applying a Doppler correction without an independent velocity source hides
  the information required by the recovery.
- Reversing the correction sign doubles the coupling error instead of removing
  it.
- Treating normalized spectral magnitude as calibrated power or a detection
  exceeds this lesson.

Static repository validation and a standard-library numerical oracle verify
the deterministic model contract and expected metrics. They do not execute
MATLAB, inspect rendered figures, or establish RF, bench, hardware/HIL,
real-time, field, or operational performance.
