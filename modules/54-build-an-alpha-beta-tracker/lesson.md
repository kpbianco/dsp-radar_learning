# Lesson: fixed-gain prediction and correction

## Guiding question

How can a simple predictor smooth noisy position while following constant velocity?

A radar report is a noisy observation of where a target was at one scan. A
track is a time-connected estimate of where the target is now and how it is
moving. P54 starts from the single scalar report supplied by P53 and makes the
smallest useful tracking model visible: position plus constant velocity.

The model is intentionally narrow. There is one target, one already-associated
position report per available scan, and no false reports. P57 handles general
measurement association. P55 later derives time-varying trust from process and
measurement covariance; P54 keeps alpha and beta fixed so their physical roles
are easy to see.

## 1. Predict before looking at the new report

Let the previous corrected state be position `x_hat(k-1)` in metres and
velocity `v_hat(k-1)` in metres per second. With scan interval `T` seconds, the
constant-velocity prediction is

```text
x_pred(k) = x_hat(k-1) + T v_hat(k-1)
v_pred(k) = v_hat(k-1).
```

This is dead reckoning for one scan. It converts velocity into a position
increment with the required factor `T`. A positive velocity advances position;
a negative velocity reduces it under the same sign convention.

## 2. The innovation measures what prediction missed

When a position report `z(k)` is available, form the innovation, also called
the residual,

```text
r(k) = z(k) - x_pred(k).
```

The residual is not the measurement error `z-x_true`, because operationally the
tracker does not know truth. It is the disagreement between the new report and
the predicted report. A positive residual says the report is ahead of the
prediction.

## 3. Alpha and beta split one residual across two state components

The explicit correction is

```text
x_hat(k) = x_pred(k) + alpha r(k)
v_hat(k) = v_pred(k) + (beta/T) r(k).
```

Alpha is dimensionless: it assigns a fraction of a position residual to
position. Beta is also dimensionless, and division by `T` converts the position
residual into a velocity correction.

- Small alpha rejects more measurement noise but lets prediction dominate.
- Large alpha makes corrected position follow each noisy report more closely.
- Small beta changes velocity slowly and creates longer lag after a maneuver.
- Large beta changes velocity quickly but injects more report noise into the
  velocity estimate and can ring when gains are too aggressive.

With a report on every constant-interval scan, the reviewed gains lie inside
the standard stable region for this form,
`0 < alpha < 2` and `0 < beta < 4 - 2 alpha`. Stability does not make every
stable pair equally useful; the experiment exposes the noise/lag tradeoff.
Dropouts switch to prediction-only dynamics, so this inequality is not a claim
that arbitrary missing-report patterns meet a particular performance bound.

## 4. A dropout means predict, not update

When no report exists at scan `k`, there is no innovation to compute. The
tracker coasts:

```text
x_hat(k) = x_pred(k)
v_hat(k) = v_pred(k)
r(k) = unavailable.
```

Substituting zero for a missing report would invent a target at the origin and
pull the track toward it. Holding the last corrected position would also throw
away the velocity model. Prediction-only coasting is the honest statement:
the state advances using its existing motion assumption, but uncertainty would
grow in a fuller tracker.

This alpha-beta filter does not carry covariance, so it cannot quantify that
growth. P55 adds that capability.

## 5. Why a velocity change creates lag

The target begins at constant velocity, then changes to a second constant
velocity. The tracker continues predicting with its old velocity until
innovations accumulate. Beta turns those position disagreements into velocity
corrections, while alpha prevents the entire noisy residual from jumping
directly into position.

The lag is therefore expected model mismatch, not proof that prediction is
wrong. With zero measurement noise, correct initial state, and truly constant
velocity, every innovation is zero and the state propagates exactly. After a
velocity step, nonzero innovations are the evidence that the old model state
must adapt.

## 6. What each controlled sweep changes

Sweep 1 varies only alpha while beta, measurements, dropouts, initial state,
and truth stay fixed. The corrected position moves from prediction-dominated to
measurement-following. Position noise generally rises as alpha approaches one.

Sweep 2 varies only beta while alpha and the same scene stay fixed. Larger beta
usually reaches the changed velocity sooner, but the velocity trace becomes
more sensitive to noisy innovations. Position and velocity behavior must be
read together; choosing beta from one attractive position sample is unsafe.

## 7. Broken limiting case: beta equals zero

The broken path retains the same prediction and alpha correction but forces
the velocity correction to zero:

```text
v_hat(k) = v_pred(k).
```

Starting from a zero velocity guess, velocity never learns. Position correction
becomes a lagging exponential smoother that repeatedly chases a moving target.
During a dropout it coasts at the wrong zero velocity, making the defect
especially visible. Restoring positive beta recovers the complete tracker.

Beta zero is a useful mathematical limiting case, but it fails this module's
completion condition. It is not hidden behind a toolbox object or a cosmetic
plot change.

## Limiting cases and invariants

- With zero innovation, prediction and correction are identical.
- With `alpha=1`, corrected position equals the available report, so position
  smoothing disappears even though velocity still uses beta.
- With `beta=0`, velocity never changes from its initial value.
- During a dropout, changing alpha or beta has no immediate effect because no
  correction is made.
- Translating all positions and the initial position estimate by the same
  constant translates every prediction and correction by that constant;
  velocity and innovations are unchanged.
- For noiseless constant velocity and the correct initial state, the tracker is
  exact after every prediction.
- A long acceleration or turn violates the constant-velocity model. Fixed gains
  can follow it only through repeated residual corrections.
- Alpha-beta gains are not probabilities, and the residual is not target truth.

## Common interpretation mistakes

**Mistake:** smoothing creates a more accurate measurement sensor.
**Correction:** the tracker combines noisy reports with a motion assumption;
model mismatch can make the smoothed track worse during maneuvers.

**Mistake:** alpha controls position and beta controls velocity independently.
**Correction:** both act on the same position innovation, so each influences
future position predictions.

**Mistake:** a missing report should be replaced by zero.
**Correction:** zero is a physical position measurement. A dropout supplies no
measurement and must use prediction only.

**Mistake:** larger gains are always more responsive and therefore better.
**Correction:** response speed rises at the cost of greater noise sensitivity
and, near stability limits, oscillation.

**Mistake:** alpha-beta tracking solves measurement association.
**Correction:** P54 assumes the scalar report already belongs to this track;
gating and association are introduced in P57.

**Mistake:** fixed alpha and beta are a Kalman covariance solution.
**Correction:** they are selected constants. P55 computes gains from explicit
uncertainty models.

## Claim boundary

This is a seeded synthetic, scalar, base-MATLAB experiment. Static repository
checks and independent host-language oracles inspect its equations, bounds, and
documentation. They do not prove MATLAB execution, rendered figures, timing,
memory, learning effectiveness, hardware/HIL, real-time behavior, operational radar
tracking, or field performance.
