# P72 lesson: Two Slopes, Two Unknowns

## Guiding question

How can opposite chirp slopes disentangle delay and Doppler?

## Physical mental model

P71 listened to one rising whistle. Echo delay and target motion both changed
its measured pitch, so one beat could not say how much came from range and how
much came from velocity. P72 adds a falling whistle. Reversing the chirp slope
reverses delay's effect on the signed beat, while carrier Doppler keeps the
same sign. That controlled reversal supplies a second view of the same two
unknowns.

P17 established the complex mixer sign, P36 established signed radial
Doppler, P69 established FMCW delay-to-range conversion, and P70 separated two
observation dimensions. P71 is this module's governed prerequisite because it
made the single-slope ambiguity visible.

## Declare the signs before combining measurements

This lesson retains the repository convention:

- the dechirp mixer is `tx .* conj(rx)`;
- the up-leg slope is `+S` and the equal-magnitude down-leg slope is `-S`;
- positive radial velocity means approaching; and
- approaching motion gives `f_d = 2v/lambda > 0`.

For a frozen round-trip delay `tau = 2R/c`, the transmitted and received
complex phases on a leg with signed slope `k` are

```text
tx_k(t) = exp(j pi k (t - T/2)^2),
rx_k(t) = exp(j pi k (t - tau - T/2)^2
              + j 2 pi f_d t + j phi).
```

The time-dependent phase of `tx_k(t) conj(rx_k(t))` is

```text
2 pi (k tau - f_d)t.
```

Substitute `k = +S` and `k = -S`:

```text
f_up   =  S tau - f_d,
f_down = -S tau - f_d.
```

The down beat is normally negative in this signed convention. Taking absolute
value or keeping only the positive FFT half would erase the algebra needed by
this lesson.

## Difference isolates delay; sum isolates Doppler

Subtract the down beat from the up beat:

```text
(f_up - f_down)/2 = S tau.
```

Doppler cancels, so

```text
tau = (f_up - f_down)/(2S),
R   = c(f_up - f_down)/(4S).
```

Add the beats:

```text
-(f_up + f_down)/2 = f_d,
v = lambda f_d/2 = -lambda(f_up + f_down)/4.
```

This is a transparent two-by-two solve, not a hidden radar toolbox call. Its
determinant is proportional to `S`, so zero slope is singular: two constant
tones with no slope reversal cannot encode delay this way.

## Baseline numbers

For `f_c = 77 GHz`, `B = 20 MHz`, `T = 40 us`, `R = 45 m`, and
`v = +20 m/s`:

```text
S       = 0.5 THz/s,
tau     = 0.300 us,
S tau   = 150.000 kHz,
f_d     = 10.266667 kHz,
f_up    = +139.733333 kHz,
f_down  = -160.266667 kHz.
```

Half their difference is `150 kHz`, which returns `45 m`. Negative half their
sum is `10.266667 kHz`, which returns `+20 m/s`. The target travels only
`1.6 mm` during the two idealized `40 us` legs; the model treats both legs as
sharing one delay and Doppler state.

## Sweep 1: range moves the beats apart

Hold velocity fixed and increase range. `S tau` grows, so the up beat moves
upward and the down beat moves downward by equal amounts. Their difference
changes, but their sum remains `-2f_d`. The range estimate follows the target
while the velocity estimate stays fixed.

This is the visible signature of delay: opposite motion on the two signed beat
axes.

## Sweep 2: velocity translates both beats together

Hold range fixed and sweep velocity through receding, zero, and approaching.
Positive approaching Doppler subtracts from both beats, moving both signed
frequencies downward together. Their separation remains `2S tau`, so range
stays fixed; their sum changes, so velocity follows the sweep.

At `v = 0`, `f_down = -f_up` and the recovered velocity is zero. That is the
stationary P69 limit.

## Sweep 3: noise perturbs both combinations

The experiment creates two distinct deterministic unit-noise streams and
scales them through the reviewed RMS values. It does not reuse identical
noise on both legs, which would create artificial cancellation. If the beat
errors are `e_up` and `e_down`, then

```text
range error    = c(e_up - e_down)/(4S),
velocity error = -lambda(e_up + e_down)/4.
```

The noiseless case recovers the algebra exactly. A single seeded realization
need not have error that grows monotonically at every step, so the plot is an
observation of this realization, not a universal error curve.

## Broken case: the equations cannot label targets

With two targets, the up spectrum contains two beats and the down spectrum
contains two beats. Neither list says which entries share one physical echo.
The deliberately broken path sorts both signed lists in the same order. Under
the reviewed scene, that crosses the targets and creates two plausible ghost
range/velocity reports.

Every up/down pair exactly solves the two equations. A zero algebraic residual
therefore cannot prove an association correct. Restoring the known pairing on
the unchanged detected beat lists recovers the two targets, but a real system
needs an additional association cue: track continuity, another ramp, angle,
amplitude, a feasible-state gate, or other scene information. Sorting alone is
not a general solution.

## Limiting cases and model boundary

- At `v = 0`, the beats are equal in magnitude and opposite in sign.
- At `tau = 0`, both beats equal `-f_d`; their difference reports zero range.
- If `f_d = S tau`, the up beat reaches DC. Its sign reverses for still larger
  approaching Doppler.
- If `f_d = -S tau`, the down beat reaches DC.
- At `S = 0`, the range solve divides by zero and the two measurements are not
  independent.
- If either signed beat reaches `fs/2` in magnitude, sampling aliases it.
- If `tau >= T`, the delayed and transmitted legs do not overlap in this
  record.
- Unequal slope magnitudes require the general two-equation system; the simple
  sum/difference formulas assume `+S` and `-S`.
- Real triangular ramps are sequential. Acceleration, appreciable migration,
  or a turnaround transient means the two legs no longer observe exactly one
  common `tau` and `f_d`.
- Zero-padding interpolates each finite spectrum. It neither resolves
  unresolved tones nor supplies target association.

## Common interpretation mistakes

- Using beat magnitudes with signed formulas silently changes the model.
- Saying the down chirp reverses Doppler is wrong; slope reversal changes the
  delay term, not the carrier Doppler sign.
- Calling the beat difference Doppler swaps the two physical combinations.
- Claiming two slopes solve every multi-target scene ignores the pairing
  permutation.
- Treating sorted peaks as identity labels confuses numerical order with
  target association.
- Expecting one noisy realization to show monotonic error with RMS overstates
  what the deterministic sweep demonstrates.
- Treating adjacent ramps as simultaneous ignores migration and acceleration.
- Treating normalized spectra as calibrated power or detection exceeds this
  lesson.

Static repository validation and a standard-library numerical oracle verify
the deterministic model contract and expected metrics. They do not execute
MATLAB, inspect rendered figures, or establish RF, bench, hardware/HIL,
real-time, field, or operational performance.
