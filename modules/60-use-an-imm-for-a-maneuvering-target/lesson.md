# Lesson: let motion explanations compete without discarding either one

## Guiding question

How can a tracker adapt when the target alternates between straight motion and maneuvers?

## Physical mental model

Imagine two observers watching the same radar reports. One expects the target
to keep its velocity; the other allows acceleration to persist. During a
straight segment, the first observer usually predicts more tightly. During an
acceleration burst, its reports become surprising while the second observer's
predictions bend with the target.

An interacting multiple-model (IMM) tracker keeps both explanations alive. It
does not select one forever. It transfers prior information between the two,
lets each filter process the new report, compares their normalized surprises,
and blends the resulting state estimates.

P59 is the contractual prerequisite. P55 is the conceptual prerequisite for
the Kalman prediction, innovation, gain, and correction used inside each mode.
This lesson changes motion uncertainty, not report-to-track association: there
is one target and one Cartesian position report at every scan.

## The shared state and the two motion models

Both filters use the same six-entry state so their estimates can be mixed:

```text
x = [east position, east velocity, east acceleration,
     north position, north velocity, north acceleration]^T.
```

For either axis, the straight model uses

```text
F_CV = [1  dt  0
        0   1  0
        0   0  0].
```

It keeps position and velocity but resets acceleration memory before the next
report. Small acceleration process noise prevents impossible certainty.

The maneuver model uses constant-acceleration kinematics over one scan:

```text
F_CA = [1  dt  dt^2/2
        0   1  dt
        0   0  1].
```

It carries acceleration forward and admits jerk process noise. This is not a
literal target-intent classifier or a full coordinated-turn model; it is a
local explanation that better follows the lesson's acceleration bursts.

Both models observe only position:

```text
z_k = H x_k + v_k,
H = [1 0 0 0 0 0
     0 0 0 1 0 0],     v_k ~ N(0, R).
```

## Interaction: share prior state without collapsing the model bank

Let `mu_i(k-1)` be the previous probability of source model `i`, and let
`p_ij` be the probability of moving from source model `i` to destination model
`j`. Before prediction, destination model `j` receives total prior support

```text
c_j = sum_i p_ij mu_i(k-1).
```

The conditional mixing weight is

```text
mu_(i|j) = p_ij mu_i(k-1) / c_j.
```

Those weights mix states:

```text
x0_j = sum_i mu_(i|j) x_i.
```

Covariance mixing must include both uncertainty within each source filter and
the spread between source estimates:

```text
P0_j = sum_i mu_(i|j) [P_i + (x_i - x0_j)(x_i - x0_j)^T].
```

Dropping the outer-product term would claim that two disagreeing filters are
as certain as two identical filters. `experiment.m` leaves this interaction
loop visible rather than calling a toolbox IMM object.

## Filter each explanation and measure its surprise

Each model performs its own Kalman prediction and update. Its innovation and
innovation covariance are

```text
nu_j = z_k - H x_j^-
S_j  = H P_j^- H^T + R.
```

The normalized innovation squared (NIS)

```text
NIS_j = nu_j^T S_j^-1 nu_j
```

asks how large the miss is relative to predicted uncertainty. The script uses
a linear solve, not a matrix inverse. For the two-dimensional report, the
Gaussian log likelihood is

```text
log L_j = -1/2 [2 log(2 pi) + log det(S_j) + NIS_j].
```

Likelihood is computed in the log domain before normalization so very small
numbers do not all underflow to zero.

## Update model probability and combine the estimates

The posterior mode probability is

```text
mu_j(k) = c_j L_j / sum_l c_l L_l.
```

Then the combined state is

```text
x_IMM = sum_j mu_j x_j.
```

Combined covariance again includes within-model covariance and disagreement:

```text
P_IMM = sum_j mu_j [P_j + (x_j - x_IMM)(x_j - x_IMM)^T].
```

Probability therefore moves smoothly with evidence. It need not be exactly
zero or one, and the most probable model need not supply the whole estimate.

## What the reviewed baseline demonstrates

The target flies straight, accelerates north on scans 16-25, flies straight
again, accelerates west on scans 39-48, and then flies straight. Seed 6007
creates one repeatable 10 m standard-deviation report record. Truth
acceleration and regime flags score and shade the experiment; they never enter
either filter.

The fixed comparison uses only the straight model. It is intentionally poorly
matched during both bursts. The IMM uses a 0.94 stay probability and starts
with the common time-zero kinematic estimate
`[0 m, 20 m/s, 0 m/s^2, 0 m, 5 m/s, 0 m/s^2]` and probabilities
`[0.85, 0.15]` for straight and maneuver. The first report arrives one second
later, so neither tracker reuses a measurement as an earlier state. On this
reviewed record:

- mean maneuver-model probability is higher on maneuver scans than on straight
  scans;
- IMM overall position RMSE is lower than fixed-model RMSE; and
- IMM maneuver-scan position RMSE is lower than fixed-model maneuver RMSE.

These are deterministic synthetic results, not a general performance bound.

## Read the two one-variable sweeps

### Maneuver acceleration

`maneuver_acceleration_sweep_mps2 = [0.8 2.0 3.2]` changes only burst
strength. Every case reuses seed 6007, scan times, report-noise scale, filter
tuning, and transition matrix. As the burst grows, the fixed straight model
lags more. The maneuver mode's average probability rises because persistent
acceleration makes its innovations relatively less surprising. The IMM stays
below the fixed model's maneuver RMSE in all reviewed cases.

### Mode persistence

`mode_stay_probability_sweep = [0.80 0.94 0.99]` changes only the symmetric
transition matrix on the identical baseline reports. Low persistence permits
quick switching but lets noise cause more dominant-mode chatter. High
persistence reduces switches but carries yesterday's explanation longer into
a new regime. The reviewed endpoints expose that responsiveness/stability
trade rather than declaring one probability universally best.

## Intentionally broken case and recovery

The broken case starts with `[1, 0]` mode probability and uses an identity
transition matrix. The maneuver model has neither prior support nor a path
from the straight model. Its predicted support `c_2` remains zero, so even a
good conditioned estimate cannot earn posterior probability. The “IMM” then
exactly behaves like the poorly matched fixed straight filter.

Recovery restores positive initial probability and off-diagonal transition
support, then reruns the exact same measurement array. Exact array equality
with the original IMM proves recovery from configuration, not from a luckier
noise realization.

## Limiting cases

- If both motion models and process covariances are identical, their state
  estimates carry no distinct motion information; probability differences are
  then driven only by priors and numerical symmetry.
- If measurement noise becomes very large, the likelihoods become less
  discriminating and transition priors dominate probability.
- If measurement noise becomes very small while the truth violates both
  models, both innovations can be large; choosing the less bad model does not
  make either model correct.
- As off-diagonal transition probability approaches zero, modes become hard
  to enter after their probability falls. Exact zero support is unrecoverable
  without reinitialization or a nonzero transition.
- As stay probability approaches one, mode chatter falls but response to a
  genuine regime change slows.
- As stay probability approaches one-half in this two-mode symmetric example,
  the prior forgets the previous mode at every scan and likelihood dominates.
- A persistent-acceleration model approximates these bursts. A real coordinated
  turn may require turn rate in the state and careful conversion/mixing.
- IMM can only choose among supplied explanations. An omitted or badly tuned
  motion regime remains model mismatch.

## Common interpretation mistakes

**Mistake:** mode probability is the probability that truth says the target is
maneuvering.

**Correction:** it is posterior weight within this two-model hypothesis set,
conditioned on its transition matrix, noise assumptions, and reports.

**Mistake:** the IMM runs two independent filters and averages them.

**Correction:** it first mixes prior states and covariances using transition
support, then filters, updates likelihoods, and combines posterior estimates.

**Mistake:** pick the largest probability and discard the other filter.

**Correction:** the combined estimate uses both conditioned states and retains
between-model covariance.

**Mistake:** a high stay probability is always better.

**Correction:** it reduces chatter and slows adaptation. The right value
depends on actual maneuver dwell times.

**Mistake:** the fixed model is bad because Kalman filtering fails.

**Correction:** its equations work as specified; the straight-motion model is
poorly matched to persistent acceleration.

**Mistake:** static Python tests prove the MATLAB figures.

**Correction:** they independently check contracts and arithmetic. A licensed
MATLAB run is separate evidence.

## Dependencies and claim boundary

The contractual prerequisite is P59; P55 provides the Kalman concepts reused
here. The implementation targets Base MATLAB R2016b or later with no toolbox,
file, network, timer, worker, or global random-stream dependency. It is bounded
to 60 scans, six sweep cases, 1,500 model updates, 480 private Gaussian values,
and six figures.

Static validation cannot establish MATLAB parsing/execution, rendered figures,
statistical calibration, educational effectiveness, hardware/HIL, field,
real-time, RT1/RT2, operational radar, signing, deployment, staging, or
production behavior.
