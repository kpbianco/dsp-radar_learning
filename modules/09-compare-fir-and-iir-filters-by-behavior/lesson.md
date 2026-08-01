# P09 Lesson — Compare FIR and IIR Filters by Behavior

## Guiding question

How can two filters with similar magnitude response behave differently in time and phase?

## Physical mental model

A filter is a weighted memory. The FIR in this lab remembers a fixed window of
21 input samples. After the last coefficient has passed an impulse, its output
is exactly zero. The IIR remembers two past outputs as well as current and past
inputs. Feedback lets a second-order filter produce a useful low-pass response
with little arithmetic, but its memory decays instead of ending at a fixed tap.

The baseline filters are calibrated to the same measured `100 Hz` minus-three-
decibel point at `1000 samples/s`. That makes their low-pass intent comparable,
not identical. Their stopbands, phase, delay, and transients remain free to
differ—and those differences are the lesson.

## The two operations made visible

For FIR coefficients `b[k]`, the causal output is the finite sum

```text
y_FIR[n] = sum from k=0 to M-1 of b[k] x[n-k].
```

The script constructs an ideal low-pass impulse response, multiplies it by a
symmetric Hamming window, and normalizes its DC gain. Symmetry gives exact
linear phase wherever the response is nonzero:

```text
b[k] = b[M-1-k]
group delay = (M-1)/2 = 10 samples.
```

The IIR is a bilinear-transform second-order low-pass. With `a[0]=1`, its
difference equation is

```text
y_IIR[n] = b0 x[n] + b1 x[n-1] + b2 x[n-2]
           - a1 y[n-1] - a2 y[n-2].
```

Those two feedback terms give the filter an impulse response that is
theoretically infinite. Stable poles make it decay; they do not make it finite.
The explicit recurrence is evaluated sample by sample—`filter`, `fir1`,
`butter`, `freqz`, `grpdelay`, and opaque toolbox design calls are not used.

## Read magnitude, phase, and group delay together

For either coefficient set, the frequency response is evaluated directly:

```text
H(exp(j omega)) = numerator(exp(j omega)) / denominator(exp(j omega)).
```

Magnitude answers how much a sinusoid is scaled. Phase answers how its angle is
shifted. Group delay is the negative phase slope,

```text
tau_g(omega) = -d phase(H) / d omega,
```

measured here in samples. The symmetric FIR phase is a straight line and its
group delay is 10 samples. The IIR phase bends, so a 60 Hz component and a
250 Hz component do not experience one universal delay. Calling “the IIR
delay” a single number without naming frequency is therefore incomplete.

The first plot also exposes a useful warning: matching the cutoff does not
match the whole magnitude curve. The FIR has more coefficients and much deeper
rejection at 250 Hz; the IIR uses only five multiplications and four additions
per output sample. Filter choice is a requirements trade, not a winner-takes-all
order comparison.

## Time behavior of the same three inputs

An impulse reveals memory. The 21-tap FIR response occupies samples `0` through
`20` and is then exactly zero. The IIR response continues below any chosen
measurement threshold; its reported “last visible sample” is a finite-record
observation, never proof of finite support.

A step exposes delay, overshoot, and settling. A pulse exposes both rising and
falling edges. The FIR delays its symmetric shape by 10 samples and can ring
slightly because an abrupt edge contains frequencies across the transition
band. The Butterworth IIR begins responding sooner but overshoots and reshapes
the two edges according to its nonlinear phase and feedback memory.

The noisy multitone contains a desired 60 Hz tone, a 250 Hz interferer, and
seeded white voltage noise. Both filters retain the desired band. Their output
waveforms do not align sample for sample, and the FIR rejects the far interferer
more strongly. The seed makes one run reproducible; it does not estimate a
probability or validate every noise realization.

## What the controlled sweeps isolate

Sweep 1 changes only FIR tap count from `9` to `21` to `41`. Sample rate,
window family, design cutoff, input step, and every IIR property stay fixed.
More taps sharpen frequency selectivity, but a symmetric causal FIR also moves
its constant delay from `4` to `10` to `20 samples`. More taps are not free.

Sweep 2 changes only IIR quality factor `Q` from `0.5` to `1/sqrt(2)` to `2`.
Cutoff, sample rate, order, and step input stay fixed. Increasing `Q` moves the
poles closer to the unit circle, reduces damping, and increases resonant peaking,
overshoot, and ringing. This sweep intentionally stops holding the magnitude
curves equally comparable so that damping is the only mechanism under study.

## Stability, sensitivity, and the broken case

For the deliberately simple conjugate-pole demonstration,

```text
A(z) = 1 - 2 r cos(theta) z^-1 + r^2 z^-2.
```

The poles have radius `r`. At `r = 1.02`, feedback grows rather than decays;
the finite 160-sample impulse response is still bounded as an experiment, but
the model is unstable and deliberately invalid. Recovery changes only the
radius to `0.98`, putting both poles inside the unit circle. The recovered tail
decays. A finite plot that has not yet overflowed is not evidence of stability;
pole location is the governing criterion.

Coefficient quantization and arithmetic precision matter more as poles approach
the unit circle because a small coefficient error can move a pole materially.
This script uses double precision and does not claim fixed-point robustness.

## Limiting cases

- If the FIR has one tap `[1]`, it has no smoothing, no history, and zero delay.
- If a symmetric FIR has `M` odd taps, its exact causal group delay is
  `(M-1)/2`; changing sample rate changes delay in seconds, not in samples.
- If all feedback coefficients are zero, the recursive equation reduces to an
  FIR operation.
- If every IIR pole has magnitude strictly below one, its natural response
  decays in exact arithmetic; a pole on the unit circle does not decay.
- If any pole magnitude exceeds one, some bounded input or initial condition
  produces an unbounded response even when a short plot looks harmless.
- If `Q` is very small, the second-order section is heavily damped and slow to
  build resonance. If `Q` grows, peaking and ringing grow before instability is
  reached.
- Matching only DC gain says nothing about cutoff. Matching only cutoff says
  nothing about stopband, phase, group delay, or settling.
- Zero-phase forward/backward filtering can remove phase distortion offline,
  but it is noncausal, changes the magnitude response, and is not a substitute
  for a causal real-time comparison.

## Radar connection and common interpretation mistakes

Radar receiver filters often trade pulse shape and timing fidelity against
selectivity, latency, and computation. A linear-phase FIR can preserve relative
timing across a bandwidth, useful before pulse timing or matched filtering. A
small IIR can suppress out-of-band content efficiently when frequency-dependent
phase and feedback transients are acceptable. Neither choice is universal.

Do not infer that lower order means lower delay at every frequency. Do not call
a thresholded IIR tail its impulse-response length. Do not blame every pulse
distortion on magnitude when nonlinear phase can move frequency components by
different delays. Do not treat a stable floating-point simulation as proof of
fixed-point, hardware, real-time, or operational radar behavior.

P08 is the declared prerequisite. P09 uses base MATLAB, deterministic synthetic
data, finite loops, and no external file, network, device, or hardware access.
