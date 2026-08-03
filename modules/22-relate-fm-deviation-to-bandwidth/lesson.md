# P22 Lesson: Relate FM Deviation to Bandwidth

## Guiding question

How does instantaneous frequency motion create an FM spectrum?

## Physical picture

Imagine a phasor of fixed length rotating around a circle. AM, from P21,
changes the phasor's length. FM keeps the length fixed and changes how quickly
the angle advances. Closely spaced RF cycles mean faster rotation; widely
spaced cycles mean slower rotation. Repeating that speed-up and slow-down writes
a repeating pattern into phase, and a periodic phase pattern requires a ladder
of spectral lines.

For a sinusoidal message, the experiment constructs

```text
phi(t) = 2*pi*fc*t + beta*sin(2*pi*fm*t)
s(t)   = Ac*cos(phi(t))
beta   = Delta_f/fm
```

The instantaneous frequency is the phase slope measured in cycles per second:

```text
fi(t) = (1/(2*pi))*d phi(t)/dt
      = fc + Delta_f*cos(2*pi*fm*t).
```

`Delta_f` is the peak deviation in hertz. `beta` is dimensionless. Confusing
those two quantities, or forgetting the `1/(2*pi)` conversion from radians to
cycles, gives a physically wrong frequency trace.

## From motion to sidebands

The frequency motion repeats at `fm`, so the FM spectrum contains components at

```text
fc + n*fm,  n = 0, +/-1, +/-2, ...
```

Their amplitudes follow a Bessel-like redistribution set by `beta`; they are not
the single fixed pair produced by one-tone AM. Increasing `Delta_f` at fixed
`fm` increases `beta` and moves appreciable energy into more sideband orders.
Increasing `fm` at fixed `Delta_f` spreads adjacent orders farther apart even
though `beta` decreases. Those are two distinct ways bandwidth can grow.

The carrier line can become small or even pass through a Bessel zero. That does
not mean the transmitter stopped: the fixed phasor magnitude shows that energy
was redistributed into other lines.

## A measurable width and Carson's estimate

An ideal sinusoidal FM waveform has infinitely many nonzero sidebands, so it has
no exact finite spectral edge. This lesson measures the smallest symmetric
sideband order containing at least 98% of the clean, bin-centered RF line power:

```text
B98 = 2*N98*fm.
```

It then compares that finite-record measurement with Carson's rule:

```text
B_Carson approximately 2*(Delta_f + fm)
```

for a one-tone message. Carson's rule is an engineering estimate of occupied
width, not a brick-wall cutoff and not a sample-rate rule. A different power
percentage, spectral threshold, record length, or off-bin tone can move the
measured edge. P12 and P13 explain why leakage and the observation record must
not be confused with signal physics.

## Limiting cases

- If `Delta_f -> 0`, then `beta -> 0`: the phasor approaches an unmodulated
  carrier and the sidebands vanish.
- If `beta << 1`, narrowband FM is dominated by the carrier and first sideband
  pair, but the transmitted magnitude is still constant.
- If `beta` is large, many Bessel-like sideband pairs can be appreciable and
  `2*(Delta_f+fm)` is the useful width intuition.
- At fixed deviation, increasing `fm` increases line spacing while reducing
  `beta`; bandwidth cannot be inferred from `beta` alone.
- A real cosine has mirrored negative-frequency energy. The lesson measures the
  positive RF cluster and does not double-count its negative mirror.
- The highest instantaneous frequency and the chosen occupied spectral tail both
  need sampling margin below Nyquist. For this lesson's one-tone Carson/98%
  target, guard `fc + Delta_f + fm`, not merely `fc + Delta_f`. Ideal sinusoidal
  FM still has infinitely many smaller lines, so this is an explicit finite-power
  engineering boundary rather than a claim of perfectly alias-free sampling.

## Why radar engineers care

FM is the starting point for chirps and FMCW radar. Frequency deviation and
modulation rate determine occupied spectrum, sampling needs, and later range
processing behavior. The exact waveform changes in later radar modules, but the
core fact survives: a designed phase slope creates designed instantaneous
frequency, and that motion consumes spectrum without requiring amplitude
variation.

## Dependencies and boundary

P21 supplies modulation and sideband language; P11-P13 supply FFT and
finite-record interpretation; P16 supplies phase and instantaneous frequency.
The experiment is deterministic base MATLAB with explicit operations. It is a
sampled synthetic lesson, not a transmitter, spectrum-analyzer, hardware, HIL,
real-time, field, or operational-radar validation.
