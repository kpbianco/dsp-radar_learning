# P06 Lesson — Use an Impulse to Reveal a System

## Guiding question

Why does an impulse response describe an LTI system?

## Physical mental model

Imagine tapping a room once and recording every reflection. That recording
reveals the direct arrival, echo delays, echo strengths, and decay. If the room
behaves linearly and does not change with time, any sound can be viewed as many
scaled, shifted taps. Add the recorded response to every tap and you reconstruct
what the room does to the whole sound.

A discrete unit impulse is one at `n = 0` and zero elsewhere. The output caused
by that impulse is the impulse response `h[n]`. Any input can be decomposed as
a sum of shifted impulses:

```text
x[n] = sum_k x[k] delta[n-k].
```

Linearity lets each impulse be scaled by `x[k]`; time invariance says shifting
the input shifts the same response. Therefore

```text
y[n] = sum_k x[k] h[n-k] = sum_k h[k] x[n-k].
```

That weighted sum of delayed input copies is linear convolution. The P06 plots
compare it with a separate direct implementation of each system so `conv` is a
check of the model, not an unexplained black box.

## What the four impulse responses say

- A pure delay has one tap at the delay. It makes exactly one shifted input copy.
- A length-`M` moving average has `M` equal taps of weight `1/M`. Nearby input
  copies overlap, smoothing fast changes while retaining constant level.
- An echo path has a direct tap of one and a later tap equal to the echo gain.
  Its output is the original plus one weaker delayed copy, like multipath radar
  or radio propagation.
- A damped resonator has a complex-conjugate pole pair at radius `r` and a
  fixed angle set by its ringing frequency. Its second-order feedback produces
  a decaying sinusoidal impulse response: infinitely many signed delayed
  copies. P06 records `N` of them, which is sufficient to reconstruct the first
  `N` causal outputs.

The comparison metric is maximum absolute voltage error between direct
processing and convolution. The completion condition is that all four errors
remain below the stated numerical tolerance.

## The two one-variable sweeps

The echo sweep holds gain fixed and moves only the second impulse-response tap.
The tap locations `8`, `32`, and `64` samples correspond to `8`, `32`, and
`64 ms` at `1000 samples/s`. Moving the tap moves the delayed input copy without
changing its amplitude.

The resonator sweep holds the input gain and `90 Hz` ringing frequency fixed
while changing only pole radius `r`. Its discrete decay time is

```text
tau_samples = -1/log(r),   for 0 < r < 1.
```

A radius closer to one spreads the damped oscillation over more lags. The
system remembers longer, so it rings longer after input changes.

## Limiting cases

- Delay `0 samples`: the pure-delay impulse response is at the origin, so the
  system becomes an identity wire.
- Moving-average length `1`: its only weight is one, so it also becomes the
  identity system.
- Echo gain `0`: the delayed path vanishes. An echo delay approaching the record
  length moves the echo outside the observed output even though the path exists.
- Resonator radius `r = 0`: only the driven first tap remains. As `r`
  approaches `1` from below, the fixed-frequency oscillation decays very
  slowly; a finite observation captures less of the total tail. A pole angle
  approaching zero moves the resonance toward DC rather than removing memory.
- A non-LTI system cannot be predicted by one fixed impulse response. Saturation
  violates linearity; a channel whose echo delay changes during the record
  violates time invariance.
- Infinite observation is an idealization. A stable IIR response continues
  forever, so a finite record describes only the output window it covers.

## Why the broken case fails

Multiplying two `N`-point FFTs and applying an `N`-point inverse FFT computes
circular convolution:

```text
y_circular[n] = sum_k h[k] x[(n-k) mod N].
```

The modulo operation wraps the late linear-convolution tail onto the beginning.
That is a boundary-condition mistake, not evidence that the impulse-response
model failed. Use direct linear convolution, or pad both sequences so the FFT
length is at least the full linear length before cropping the desired causal
window.

## Radar connection and common mistakes

A radar channel impulse response places taps at propagation delays. Tap delay
maps to path length; tap amplitude and phase describe attenuation and phase
shift. Closely spaced taps create multipath distortion, while a long response
can smear returns across range-time samples.

Do not confuse the input impulse with the response: the spike is the probe;
everything after the probe is system behavior. Do not assume every observed
system is LTI, do not discard filter startup as an error, and do not compare a
full convolution with a cropped direct output without aligning their time
support. Numerical agreement validates these deterministic models; it does not
prove a physical radar channel, hardware device, or changing environment is LTI.
