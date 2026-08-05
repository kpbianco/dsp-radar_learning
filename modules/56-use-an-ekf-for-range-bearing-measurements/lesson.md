# Lesson: make a local Cartesian correction from polar evidence

## Guiding question

How can nonlinear radar measurements update Cartesian target state?

A radar naturally measures distance and direction. A tracker often stores
Cartesian position and velocity because straight-line motion is simple there.
The extended Kalman filter (EKF) connects those two coordinate systems by
asking how a small Cartesian displacement would change the predicted polar
report at the current predicted location.

P55 supplied covariance-based constant-velocity prediction for a linear
position report. P56 preserves that transparent prediction, adds nonlinear
measurement geometry, and still assumes one report is already associated with
one track. P57 adds association.

## 1. Predict in Cartesian coordinates

The state ordering is

```text
x = [px; vx; py; vy],
```

with positions in metres and velocities in metres per second. For scan interval
`T`, the model is

```text
F = [1 T 0 0; 0 1 0 0; 0 0 1 T; 0 0 0 1]
G = [T^2/2 0; T 0; 0 T^2/2; 0 T]
Q = sigma_a^2 G G'
x_pred = F x_hat
P_pred = F P F' + Q.
```

The two columns of `G` admit independent unknown x- and y-acceleration. As in
P55, `Q` widens predicted covariance; it does not add a visible random kick to
the estimated state.

## 2. Predict what the radar should measure

For predicted Cartesian position `(px,py)`, the radar model is

```text
h(x_pred) = [r; theta]
r = sqrt(px^2 + py^2)          metres
theta = atan2(py,px)           radians.
```

This is nonlinear: doubling `px` does not simply double both range and bearing.
Converting each noisy polar report to `(r cos(theta), r sin(theta))` is useful
for display, but it does not turn the noise into fixed, isotropic Cartesian
noise.

## 3. The Jacobian is a local geometry map

The EKF evaluates the derivative at the predicted state:

```text
H = [ px/r       0   py/r       0
     -py/r^2     0   px/r^2     0 ].
```

The first row is the radial unit vector: motion along the line of sight changes
range most. The second row is a range-scaled tangential direction: the same
sideways displacement changes angle less when the target is farther away.
Velocity columns are zero because one instantaneous polar report measures
position only; velocity becomes observable across repeated predictions and
updates.

This derivative is a local approximation. It is accurate when the prediction
uncertainty occupies a region where the curved range-bearing map is nearly
linear. It becomes unreliable near the radar, with a very poor initialization,
or with extremely broad angular uncertainty. The script rejects predicted
range at or below `25 m` rather than divide by nearly zero.

## 4. Keep metres and radians in their own covariance

The measurement covariance is

```text
R = diag([sigma_range_m^2, sigma_bearing_rad^2]).
```

Bearing degrees are converted once to radians before squaring. The range and
bearing residuals have different units, but `S` scales and correlates them so a
joint dimensionless consistency statistic remains meaningful:

```text
innovation = z - h(x_pred)
S = H P_pred H' + R
NIS = innovation' S^-1 innovation.
```

The code evaluates the last expression with a matrix solve, not an explicit
inverse.

## 5. Angles need a local difference

Ordinary subtraction fails at the branch cut. `+179 deg` and `-179 deg` are
only `2 deg` apart physically, not `358 deg`. Only the bearing component is
wrapped:

```text
delta_theta = atan2(sin(delta_theta), cos(delta_theta)).
```

Range is not wrapped, and neither state nor covariance is wrapped. Figure 5
turns this operation off on purpose. The huge residual then pulls the Cartesian
state the long way around the radar even though the report is nearby.

## 6. Correct state and covariance explicitly

```text
K = P_pred H' / S
x_hat = x_pred + K innovation
A = I - K H
P = A P_pred A' + K R K'.
```

`K` maps metres and radians into corrections for four state components. Its
entries are not probabilities and do not need to sum to one. The Joseph form
preserves covariance symmetry and nonnegative variance better under finite
precision; the script removes only tiny numerical asymmetry afterward.

## 7. Read covariance ellipses as geometry, not decoration

The 2-by-2 position block of `P` has eigenvectors that set ellipse orientation
and eigenvalues whose square roots set principal-axis standard deviations. The
display multiplies those axes by `sqrt(5.991)` for a nominal 95% ellipse in two
dimensions.

For small angle error,

```text
radial sigma approximately sigma_range
tangential sigma approximately range * sigma_bearing_rad.
```

Thus `0.8 deg` is about `7 m` cross-range at `500 m`, `21 m` at `1500 m`, and
`42 m` at `3000 m`. The second sweep makes this range dependence visible while
holding both sensor standard deviations fixed. The ellipse rotates with the
line of sight because radial and tangential directions rotate.

## 8. What the two sweeps isolate

The bearing-noise sweep reuses the exact same truth, polar reports,
initialization, process model, range noise, and random draws. Only assumed
`sigma_bearing` changes. A small value makes bearing evidence strong and can
make NIS expose overconfidence; a large value reduces angular trust and widens
tangential state uncertainty.

The geometry sweep does not invent new reports. It maps the same fixed
`sigma_range` and `sigma_bearing` at `500`, `1500`, and `3000 m`. Radial
uncertainty remains fixed while tangential uncertainty grows linearly in the
small-angle limit.

## Limiting cases

- With bearing variance approaching zero, a correct angle is very strong
  cross-range evidence, but an incorrectly tiny assumed variance makes the
  filter overconfident.
- With bearing variance very large, range still constrains the target radially
  while direction contributes little.
- At long range, the same angular standard deviation creates larger Cartesian
  uncertainty; angle need not become numerically noisier for metres of error to
  grow.
- Near zero range, bearing and its Jacobian are not well defined. This script
  stops instead of hiding the singularity.
- With zero angular innovation, the bearing part contributes no state
  correction even though its covariance still affects gain and posterior
  uncertainty.

## Common interpretation mistakes

**Mistake:** raw Cartesian conversion makes measurement noise Gaussian with the
same x/y variance everywhere.

**Correction:** polar noise maps into a rotated, range-dependent Cartesian
shape.

**Mistake:** the Jacobian is evaluated at truth or at the noisy report.

**Correction:** an operational EKF does not know truth; it linearizes `h` at the
predicted state.

**Mistake:** a bearing in degrees can be squared directly inside `R`.

**Correction:** the model uses radians, so degrees are converted once before
forming variance.

**Mistake:** `-179 deg - 179 deg` means a real `-358 deg` turn.

**Correction:** those directions are neighbors; wrap only the angular residual.

**Mistake:** ellipse rotation means the sensor itself changed.

**Correction:** fixed radial/tangential accuracy rotates with line-of-sight
geometry.

**Mistake:** a nominal 95% ellipse must contain exactly 95% of one track.

**Correction:** one finite, correlated, seeded record gives descriptive
coverage, not a calibration guarantee.

**Mistake:** the EKF solves association.

**Correction:** P56 assumes one report belongs to one track; P57 owns gating and
association.

## Claim boundary

This is a seeded synthetic 2-D, base-MATLAB lesson. Static repository tests and
an independent host-language oracle inspect equations, branch-cut behavior,
input rejection, bounds, recovery, and documentation. They do not prove MATLAB
execution, rendered plots, timing, memory use, statistical calibration,
educational effectiveness, hardware/HIL, real-time behavior, operational radar
tracking, or field results.
