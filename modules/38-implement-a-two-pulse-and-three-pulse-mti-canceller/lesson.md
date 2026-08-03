# Lesson: A Difference Across Pulses Is a Doppler Filter

## Start with the physical picture

A stationary reflector returns the same complex phasor on every coherent pulse.
Subtract two adjacent pulse samples and those equal phasors cancel. A moving
target rotates in phase between pulses, so its two samples are unequal and a
residual remains. MTI is therefore a slow-time high-pass operation, not a
range-domain subtraction.

P38 keeps P37's matrix convention:

```text
X[range sample, pulse]
```

Every canceller operates across columns. Each range row is filtered
independently.

## Scene and Doppler model

The idealized complex scene is

```text
X[r,p] = C[r]
       + sum_k A_k g[r-r_k] exp(j(phi_k + 2 pi f_d,k p/PRF))
       + W[r,p]

lambda = c/f_c
f_d,k = 2 v_k/lambda
omega_k = 2 pi f_d,k/PRF
```

`C[r]` is a stationary complex clutter profile, constant from pulse to pulse.
`g[r-r_k]` places a moving target at a range row. `W[r,p]` is circular complex
white noise. Positive radial velocity means approaching the radar. The factor
of two in Doppler comes from the monostatic out-and-back path.

## Two pulses: the first difference

The two-pulse canceller stores one delayed pulse and subtracts it:

```text
y2[p] = x[p] - x[p-1]
h2 = [1, -1]
H2(exp(j omega)) = 1 - exp(-j omega)
|H2| = 2 |sin(omega/2)|
```

At zero Doppler, `omega=0`, so the response is exactly zero. Close to zero,
`|H2|` grows approximately in proportion to `|omega|`. Slow targets can
therefore be attenuated along with clutter.

## Three pulses: the second difference

Apply the first-difference idea twice:

```text
y3[p] = x[p] - 2 x[p-1] + x[p-2]
h3 = [1, -2, 1]
H3(exp(j omega)) = (1 - exp(-j omega))^2
|H3| = 4 sin^2(omega/2)
```

Near zero, `|H3|` grows approximately as `omega^2`. That broader near-zero
notch gives stronger rejection of very slow clutter-like motion. It also
removes more of a genuinely slow target than the two-pulse canceller.

## Periodic nulls and blind speeds

Slow time samples Doppler once per PRI, so frequency is periodic with PRF. Both
cancellers are zero whenever

```text
f_d = m PRF
v_blind = m lambda PRF/2,  m = 0, +/-1, +/-2, ...
```

Only the `m=0` null lies inside the usual unambiguous Doppler interval
`-PRF/2 <= f_d < PRF/2`. The other nulls are aliased copies. P39 will use this
fact to expose blind speeds and stagger PRF.

## Target gain is not the same as detection improvement

At a target's Doppler, `|H|` is its amplitude gain and `|H|^2` is its power
gain. A gain above one does not mean the filter created target information; it
is the scale of a differencing filter. Detection also depends on output noise.

For white input noise, FIR output noise power is multiplied by the sum of
squared coefficient magnitudes:

```text
two-pulse noise power gain   = 1^2 + (-1)^2 = 2
three-pulse noise power gain = 1^2 + (-2)^2 + 1^2 = 6
```

The corresponding noise RMS gains are `sqrt(2)` and `sqrt(6)`. Adjacent output
noise samples are correlated because they reuse input samples. P38 reports
target SNR change as `10 log10(|H|^2/sum(|h|^2))` so target amplification is not
confused with SNR improvement.

## Why changing PRF changes the response to the same target

For fixed physical Doppler, raising PRF shortens the PRI and reduces phase
change per pulse:

```text
omega = 2 pi f_d/PRF
```

The target moves closer to the zero-Doppler notch in normalized slow-time
frequency, so both canceller gains fall. At the same time the unambiguous
velocity interval grows. PRF choice therefore couples ambiguity coverage and
MTI response.

## The broken case and recovery

`X[2:end,:] - X[1:end-1,:]` subtracts neighboring range rows. A stationary
clutter profile is not constant across range, so this produces edges around
clutter peaks rather than canceling them. Its output may look busy and
high-pass filtered, but it is not an MTI result.

Recovery restores subtraction across columns, recreates the noise with the
same private seed, and proves exact equality with the original correct
two-pulse and three-pulse outputs. Valid differences are not zero-padded: the
two-pulse output has `N-1` coherent looks and the three-pulse output has `N-2`,
avoiding artificial boundary transients.

## Limiting cases and model boundary

- `f_d = 0`: ideal stationary clutter cancels exactly in both filters.
- `|f_d| -> 0`: the second difference falls toward zero faster, so it rejects
  more near-zero energy and more slow-target energy.
- `|f_d| = PRF/2`: amplitude gains are 2 and 4, while the noise gains remain 2
  and 6 in power.
- `f_d = m PRF`: both filters have periodic blind-speed nulls.
- A drifting or Doppler-spread clutter phasor is not constant and will leave a
  residual; an ideal DC null does not promise complete real-clutter removal.
- Taking magnitude or real part before differencing destroys coherent phase
  information and changes the filter behavior.
- The script neglects acceleration and range migration and does not model a
  transmitted waveform, antenna, propagation, receiver, or detector.

## Common interpretation mistakes

- **“Three-pulse is always better.”** It has a sharper clutter notch, but it
  can suppress slow targets more and raises white-noise power by six.
- **“A taller filtered target means SNR improved.”** Compare target power gain
  with noise power gain before saying that.
- **“Any difference operation is MTI.”** The difference must be along coherent
  slow time, not range.
- **“The zero-Doppler null removes every kind of clutter.”** Motion, platform
  effects, phase noise, and clutter spread move energy away from exact DC.

## Connections

- P36 turns radial velocity into pulse-to-pulse phase.
- P37 arranges that phase history along matrix columns.
- P38 filters those columns with explicit delay-line cancellers.
- P39 examines the periodic blind-speed consequence.
