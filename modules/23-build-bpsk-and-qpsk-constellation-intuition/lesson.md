# P23 Lesson — Bits Become Geometry

## Guiding question

What do symbols, phase states, and decision regions look like in IQ?

## Physical mental model

A complex baseband sample is an arrow. Its horizontal coordinate is the
in-phase value `I`; its vertical coordinate is the quadrature value `Q`. A
digital transmitter chooses one of a few allowed arrows for each symbol. The
receiver sees a displaced arrow and asks which fixed region contains it.

BPSK uses two phase states on the real axis:

```text
b = 0 -> s = -1,       b = 1 -> s = +1.
```

The ideal boundary is `I=0`. The Q coordinate is useful for seeing channel
rotation and noise, but an aligned BPSK hard decision needs only the sign of I.

QPSK carries two bits per symbol. This module maps the two bits independently
to the signs of I and Q and normalizes the symbol energy:

```text
s = ((2*b_I-1) + j*(2*b_Q-1))/sqrt(2).
```

The four points all have `|s|^2=1`. The boundaries `I=0` and `Q=0` divide the
plane into four quadrants. Neighboring points differ by one bit under this
mapping, so a single boundary crossing usually flips one bit.

## Noise turns points into clusters

For either modulation the received symbol is

```text
r = s*exp(j*phi) + n.
```

`phi` is carrier phase error and `n` is complex Gaussian receiver noise. For a
fair bit-energy comparison at `gamma_b = 10^(Eb/N0/10)`, the script uses

```text
sigma_BPSK = sqrt(1/(2*gamma_b))
sigma_QPSK = sqrt(1/(4*gamma_b)).
```

QPSK has unit symbol energy spread across two bits, so its per-axis signal and
noise scales are both lower. With perfect phase alignment, BPSK and Gray-like
QPSK therefore have the same ideal bit-error behavior at the same `Eb/N0`.
Lower SNR broadens the clusters without moving their centers.

## Phase error moves centers, not boundaries

Multiplication by `exp(j*phi)` rotates every ideal point by `phi` while
preserving magnitude. An uncorrected receiver still tests the old boundaries.
QPSK's nearest ideal point is 45 degrees from a boundary, so a rotation near
45 degrees removes its decision margin. BPSK has 90 degrees to its real-axis
sign boundary and is less phase-sensitive in this simple aligned model.

This does not mean QPSK is intrinsically unusable. A receiver estimates carrier
phase and derotates:

```text
r_corrected = r*exp(-j*phi_hat).
```

When `phi_hat=phi`, the centers return to their original quadrants. Noise is
rotated too, but circular Gaussian noise has the same distribution after
rotation.

## Limiting cases

- As `Eb/N0` tends to infinity and phase is aligned, clusters collapse onto
  ideal points and hard-decision BER tends to zero.
- As `Eb/N0` falls, points cross boundaries even though their average centers
  remain correct.
- At a QPSK phase error of 45 degrees, ideal centers sit on boundaries. Noise
  then decides the affected bit; the uncorrected receiver has lost margin.
- Just beyond 45 degrees, at least one QPSK coordinate has the wrong sign even
  with little noise. More transmit power cannot repair a rotated reference.
- Near 90 degrees, an uncorrected BPSK point loses its I projection; beyond 90
  degrees the BPSK sign is reversed.

## Common interpretation mistakes

- A constellation is not the physical path traveled between symbols here. It
  is a set of symbol-rate observations; pulse shaping comes in P24.
- Q is not “noise.” BPSK's ideal Q is zero, but QPSK deliberately carries a
  second bit on that axis.
- SNR changes cluster spread. A constant carrier phase error rotates cluster
  centers. Those signatures should not be confused.
- A hard-decision boundary is a receiver rule, not a wall that changes the
  waveform.
- Comparing raw symbol errors between BPSK and QPSK is not a fair bit
  comparison. This module reports bit errors and uses `Eb/N0`.
- A corrected-looking constellation does not prove timing, pulse-shaping, or
  multipath recovery. Those mechanisms are isolated in later modules.

## Why this matters for radar and communications

Communication receivers use these decisions directly. Coherent radars also
depend on stable I/Q phase: pulse-to-pulse Doppler, coded waveforms, and array
processing all treat phase as information. A constant common phase rotates the
whole observation but does not by itself change Doppler phase slope or array
steering. Time-varying phase/frequency error can bias Doppler or reduce coherent
code gain, while element-dependent phase errors can distort a beam. This
constellation is the smallest visible example of the reference-alignment idea.

P22 supplied the phase-state viewpoint; P17 through P19 supplied complex
baseband and I/Q impairment intuition. P24 will add samples between these ideal
symbol instants and show why matched filtering is needed before making the same
kind of decisions.
