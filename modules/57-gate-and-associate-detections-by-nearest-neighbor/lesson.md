# Lesson: let uncertainty define what “near” means

## Guiding question

Which measurement should update which track?

A radar scan may contain several target reports and many clutter reports. A
tracker predicts where each target should appear, but prediction is uncertain.
Association is the decision that connects one new report to one predicted
track. The useful notion of “nearest” is therefore not simply the fewest
metres; it is the smallest residual relative to the uncertainty expected for
that track.

P53 turned threshold-crossing cells into reports. P55 predicted Cartesian state
and covariance, and P56 formed an innovation and its covariance. P57 exposes
the missing step between prediction and update. It decides which report, if
any, may supply the innovation. P58 will manage track birth/death, and P59 will
show why this simple rule can fail when targets cross.

## 1. Predict every track before looking at the reports

For state ordering

```text
x = [px; vx; py; vy],
```

the one-scan constant-velocity prediction is

```text
x_i^- = F x_i
P_i^- = F P_i F' + Q.
```

All tracks use the same scan time but keep their own covariance. Track 1 in the
experiment has a long x-axis uncertainty and a narrow y-axis uncertainty. That
shape matters: a 45 m residual along x can be plausible while a 30 m residual
along y is not.

## 2. Compare each track with each detection

The position-report model is deliberately linear:

```text
z = H x + v
H = [1 0 0 0; 0 0 1 0]
R = sigma_z^2 I.
```

For predicted track `i` and detection `j`, form

```text
nu_ij = z_j - H x_i^-
S_i = H P_i^- H' + R.
```

`nu_ij` is a two-component residual in metres. `S_i` is the expected residual
covariance in square metres. It includes prediction uncertainty and report
uncertainty. Leaving out either term changes the physical question being asked.

## 3. Normalize the residual by its uncertainty

The squared Mahalanobis distance is

```text
d_ij^2 = nu_ij' S_i^-1 nu_ij.
```

The script evaluates this as `nu'*(S\nu)`, not with an explicit inverse. The
result is dimensionless. Along a high-variance direction, a given metre error
contributes less distance; along a tightly predicted direction, the same metre
error contributes more.

If `S = sigma^2 I`, then `d^2` is just Euclidean squared distance divided by
`sigma^2`, so both metrics rank reports the same. They differ when track
uncertainties differ in size or direction. Figure 2 makes that difference
visible for Track 1.

## 4. Gate before assigning

A two-dimensional validation gate accepts a pair only when

```text
d_ij^2 <= gamma.
```

The seeded target reports use explicit standard-Gaussian Box-Muller draws scaled
by `sigma_z = 6 m`, matching the `R` model without changing MATLAB's global
random stream. The baseline uses `gamma = 5.991`, the familiar nominal 95%
chi-square boundary for two coordinates under a correct Gaussian innovation model. The plotted
ellipse has semi-axis lengths

```text
sqrt(gamma * lambda_1), sqrt(gamma * lambda_2),
```

where `lambda_1` and `lambda_2` are eigenvalues of `S`. The square root appears
only when drawing the ellipse; the gate comparison uses `d^2` against `gamma`.

A nominal probability is not a promise that 95% of reports in one tiny scene
will pass. It describes the model over repeated well-calibrated innovations.

## 5. Enforce a one-to-one nearest-neighbor decision

After gating, the script repeatedly selects the smallest remaining valid
`d^2`. It records that track-report pair and removes the selected row and
column. This enforces:

- at most one report updates a track; and
- at most one track consumes a report.

The rule is a transparent greedy nearest-neighbor method. It is not a globally
optimal assignment solver. MATLAB's column-major `min` provides a deterministic
tie order in this finite example, but a real interface should specify how exact
ties are resolved because a different tie can produce a different assignment.

Tracks with no gated report remain unassigned. Reports unused by every track
also remain unassigned; in the nominal baseline those unused reports happen to
be clutter, but a tight gate or competing track can leave a true report unused.
P57 does not create or delete tracks from those outcomes; that lifecycle
belongs to P58.

## 6. Read the gate-threshold sweep

The first sweep reuses exactly the same tracks, covariances, detections, and
distance matrix. Only `gamma` changes among `0.5`, `5.991`, and `13.816`.

- A very tight gate can reject the true report, producing a missed update.
- The nominal gate keeps the separated true pairs and excludes clutter.
- A loose gate admits more candidate pairs, including clutter. It does not make
  those reports more informative; it merely postpones rejection to the
  nearest-neighbor competition.

The count of assigned tracks cannot exceed either the number of tracks or the
number of reports because row and column removal impose the one-to-one rule.

## 7. Read the covariance-scale sweep

The second sweep holds the report record, prediction centres, measurement
noise, gate threshold, and association rule fixed. It multiplies only the
predicted covariance by `0.25`, `1`, or `4` before adding `R`.

As covariance grows, the same residual has a smaller normalized distance and
the gate ellipse has a larger area:

```text
area = pi * gamma * sqrt(det(S)).
```

This is not “free tolerance.” It is a statement that the prediction is less
precise. A broader gate can prevent missed updates after uncertain motion, but
it also admits more clutter and makes association less selective.

## 8. Understand the broken case and recovery

The broken path replaces `d^2` with raw Euclidean squared distance and sets
every pair valid. Track 1 then takes the clutter point 30 m away across its
narrow axis instead of its true report about 57 m away along its broad axis.
The point is closer in metres but far less consistent with Track 1's predicted
error shape.

Recovery restores both pieces of the model: Mahalanobis normalization and the
gate mask. It reruns on the same arrays and must exactly reproduce the baseline
assignment. Changing the seed or moving a detection would not isolate the
failure.

## Limiting cases

- If `P^-` approaches zero, the gate is controlled mostly by measurement noise
  `R`; a confident prediction rejects modest offsets.
- If `P^-` becomes very large, more reports enter the gate and association
  ambiguity increases even though their Euclidean positions did not change.
- If `R` becomes very large, the sensor supplies weak spatial discrimination.
- If a valid row has one candidate, nearest-neighbor selection is unambiguous.
- If no pair passes the gate, every track and report remains unassigned; this
  is a valid association result, not an algorithm crash.
- If two tracks compete for one report, the first selected pair consumes it;
  the other track cannot reuse it.
- If `S` is singular or not positive definite, Mahalanobis distance is not a
  valid uncertainty metric. The script rejects that input.

## Common interpretation mistakes

**Mistake:** the closest report in metres is always the most likely report.

**Correction:** closeness must be measured relative to each track's innovation
covariance; direction and scale matter.

**Mistake:** the gate threshold is an ellipse radius in metres.

**Correction:** `gamma` bounds dimensionless squared distance. Physical axes
come from `sqrt(gamma*lambda(S))`.

**Mistake:** use only measurement covariance `R` in the gate.

**Correction:** association uncertainty is `S = H P^- H' + R`.

**Mistake:** each track can independently choose its nearest report.

**Correction:** that can reuse one report. The selection must enforce both
row and column uniqueness.

**Mistake:** a loose gate improves detection quality.

**Correction:** it admits more hypotheses, including clutter; it trades missed
valid reports against ambiguity.

**Mistake:** an unassigned report should automatically start a track.

**Correction:** association and track initiation are separate decisions; P58
owns confirmation and deletion logic.

**Mistake:** greedy nearest neighbor is globally optimal.

**Correction:** it makes the best current valid pair and can be shortsighted in
crowded or crossing scenes. P59 examines that boundary.

## Claim boundary

This is a seeded synthetic, single-scan, base-MATLAB lesson. Static repository
tests and an independent host-language oracle inspect prediction, residuals,
innovation covariance, Mahalanobis distance, gating, uniqueness, malformed
inputs, sweeps, resource bounds, broken behavior, and exact recovery. They do
not prove MATLAB parsing/execution, rendered figures, timing, memory use,
statistical calibration, multi-scan tracking quality, educational effectiveness,
hardware/HIL, real-time behavior, operational radar performance, or field
results.
