# Lesson: uncertainty chooses the correction

## Guiding question

How do process noise and measurement noise determine trust in prediction versus measurement?

A radar position report is noisy. A constant-velocity prediction is also
imperfect because real targets accelerate. The Kalman filter carries both kinds
of uncertainty forward and uses their relative size to decide how strongly one
new report should correct position and velocity.

P54 used fixed alpha and beta. P55 keeps the same one-target, already-associated
scalar report but replaces those fixed gains with values computed from
covariance. P56 later introduces nonlinear range-bearing geometry, and P57
introduces report-to-track association.

## 1. The nearly-constant-velocity model

The state contains position in metres and velocity in metres per second:

```text
x(k) = [position(k); velocity(k)].
```

For scan interval `T`, the constant-velocity transition and scalar position
measurement are

```text
F = [1 T; 0 1],       H = [1 0]
x(k) = F x(k-1) + G a(k),    z(k) = H x(k) + n(k)
G = [T^2/2; T].
```

`F` says velocity advances position and otherwise persists. Unknown interval
acceleration `a(k)` admits departures from exact constant velocity. The truth
record uses seeded acceleration with standard deviation `sigma_a_actual`; the
filter knows only an assumed standard deviation.

## 2. Q and R describe different uncertainty sources

With the interval-acceleration convention used here,

```text
Q = sigma_a_assumed^2 G G'
R = sigma_z_assumed^2.
```

`Q` is state process covariance. Its entries have mixed state-covariance units:
position variance, position-velocity covariance, and velocity variance. `R` is
position-report variance in square metres. A standard deviation is squared
exactly once to form its variance.

`Q=0` does not mean every Kalman filter is broken. It means exact constant
velocity is being asserted. That assertion is deliberately wrong for this
seeded accelerating scene. `R` must be positive here because the sensor report
has nonzero noise and the scalar innovation variance must remain positive.

## 3. Predict state and uncertainty before using the report

```text
x_pred = F x_hat
P_pred = F P F' + Q.
```

The first equation moves the best state estimate. The second moves its
uncertainty and adds the uncertainty attributed to unknown acceleration. `Q`
does not randomly shake the estimate; it widens the filter's prediction model.

## 4. Innovation asks how surprising the report is

```text
innovation = z - H x_pred
S = H P_pred H' + R.
```

The innovation is report minus predicted report, in metres. It is not truth
error: an operational tracker does not know truth. `S` predicts innovation
variance from both state-prediction uncertainty and measurement uncertainty.
The plotted `+/-2 sqrt(S)` band makes unusually surprising reports visible.

## 5. The Kalman gain expresses relative trust

```text
K = P_pred H' / S
x_hat = x_pred + K innovation.
```

There is one scalar division, not a matrix inverse. The first gain component is
dimensionless and corrects position per metre of innovation. The second has
units `1/s` and converts that position disagreement into a velocity correction.

- Larger `Q` makes prediction uncertainty grow faster, usually raising gain
  and accepting more of the report.
- Larger `R` declares the report noisier, lowering gain and preserving more of
  the prediction.
- Smaller `Q` or `R` produces narrower model-conditioned bounds. Narrower is
  not automatically more accurate; a wrong assumption creates overconfidence.

## 6. Correct covariance without losing its meaning

The script uses the Joseph form:

```text
A = I - K H
P = A P_pred A' + K R K'.
```

This is algebraically equivalent to the ideal covariance update but better
preserves symmetry and nonnegative variance under finite precision. The script
then removes tiny numerical asymmetry by averaging `P` with `P'`. No tracking
toolbox object hides prediction, gain, or correction.

## 7. Read consistency as a diagnostic, not a promise

The baseline plots posterior state error against `+/-2 sqrt(P)` and innovation
against `+/-2 sqrt(S)`. It also reports the fraction inside those bands and the
mean normalized innovation squared,

```text
NIS = innovation^2 / S.
```

For a well-matched Gaussian model, two-sigma containment is commonly near 95%
over many independent samples and NIS averages near one. This lesson uses one
finite correlated track. Its statistics are descriptive evidence for tuning,
not proof of calibration, independence, or future performance.

## 8. The controlled sweeps and failures

The Q sweep changes only assumed acceleration standard deviation while keeping
`R`, truth, reports, initialization, and every random draw fixed. Low Q trusts
the CV prediction too long as true velocity wanders. High Q adapts faster but
lets report noise influence the state more strongly.

The R sweep changes only assumed report standard deviation while keeping `Q`
and the same data fixed. Low R follows reports aggressively; high R smooths
more and corrects more slowly.

Two limiting failures make overconfidence explicit:

- broken Q sets assumed acceleration to zero even though truth accelerates;
- broken R claims `0.5 m` report noise although the actual standard deviation
  is `25 m`.

Recovery restores the reviewed `0.8 m/s^2` and `25 m` assumptions and reruns
the same explicit operation on the same seeded record.

## Common interpretation mistakes

**Mistake:** Q adds visible random noise directly to the estimated state.
**Correction:** Q enters predicted covariance; the state changes through the
model and measurement innovation.

**Mistake:** the innovation is position truth error.
**Correction:** it is report minus predicted report and contains both state and
sensor uncertainty.

**Mistake:** low R improves the physical radar measurement.
**Correction:** it only tells the filter to trust each existing report more.

**Mistake:** a narrow covariance bound proves high accuracy.
**Correction:** covariance is conditional on the assumed model. Mismatch can
make a wrong estimate confidently wrong.

**Mistake:** Kalman gain is a probability and its components must sum to one.
**Correction:** the components map a position innovation into different state
units; velocity gain even carries units `1/s`.

**Mistake:** this filter solves nonlinear radar measurements and association.
**Correction:** P55 assumes one linear scalar report already belongs to the
track. P56 and P57 own those later mechanisms.

## Claim boundary

This is a seeded synthetic 1-D, base-MATLAB experiment. Static repository tests
and an independent host-language oracle inspect equations, input rejection,
bounds, and documentation. They do not prove MATLAB execution, rendered plots,
timing, memory use, statistical calibration, teaching effectiveness,
hardware/HIL, real-time behavior, operational radar tracking, or field results.
