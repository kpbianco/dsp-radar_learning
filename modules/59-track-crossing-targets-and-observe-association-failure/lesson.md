# Lesson: identity is history, not a label carried by a detection

## Guiding question

**Why do simple nearest-neighbor trackers swap identities?**

Two radar plots can be physically close without containing enough information
to say which history produced which plot. A nearest-neighbor tracker has no
privileged access to truth. It predicts each established track, compares those
predictions with the current unlabeled reports, commits to pairs, and lets
those decisions change the next predictions. Near a crossing, one locally
reasonable link can therefore redirect an entire track history.

## Physical scene

P59 uses two targets whose velocities have equal magnitude and the same strong
along-track component:

```text
p_A(t) = [20t,  5t] m,    v_A = [20,  5] m/s
p_B(t) = [20t, -5t] m,    v_B = [20, -5] m/s.
```

They meet at `t = 0`. Twenty-five scans place the crossing at scan 13. Each
target produces one noisy Cartesian position report and one noisy auxiliary
Cartesian velocity report. The latter is an idealized Doppler-derived feature,
not a claim that every radar directly measures a complete velocity vector.
The script alternates report column order so array position cannot stand in for
target identity.

The two tracks already exist and are confirmed. Their separated pre-crossing
states initialize the experiment. P58 lifecycle logic is deliberately held
fixed: track birth or deletion cannot repair an incorrect association between
two live tracks.

## Predict before associating

For scan `k > 1`, each track uses the constant-velocity prediction

```text
p_i^-(k) = p_i^+(k-1) + dt v_i^+(k-1)
v_i^-(k) = v_i^+(k-1).
```

The position-only cost for track `i` and report `j` is

```text
Jp(i,j) = ||z_p,j - p_i^-||^2 / sigma_p^2.
```

Both numerator and denominator have square-metre units, so `Jp` is
dimensionless. The script evaluates all four costs explicitly. It repeatedly
selects the smallest remaining value and removes the chosen row and column.
That is a deterministic, one-to-one greedy nearest-neighbor rule, not a global
assignment optimizer.

After selection, an explicit alpha-beta update uses the position residual:

```text
r_i = z_p,j - p_i^-
p_i^+ = p_i^- + alpha r_i
v_i^+ = v_i^- + (beta/dt) r_i.
```

The assigned report thus affects the next prediction. Once both tracks take
the other targets' reports, the corrected states can support the swapped
interpretation rather than immediately undoing it.

## What the baseline demonstrates

With seed 5908, `sigma_p = 6 m`, `dt = 1 s`, `alpha = 0.60`, and
`beta = 0.25`, position-only association is correct through scan 13. At scan
14 it exchanges the two reports and continues following the other physical
targets. Across the two track rows this is:

- 24 wrong links: two wrong links on each of scans 14 through 25; and
- two identity transitions: one transition in each track's identity history.

A wrong-link count measures duration and multiplicity. An identity-transition
count measures changes in history. They are not interchangeable, and neither
is a track-birth/death count.

Truth IDs are stored separately and joined only after every association and
state update. They score the experiment; they never enter a cost.

## Add information in compatible units

The enriched cost adds a normalized auxiliary velocity residual:

```text
J(i,j) = Jp(i,j)
       + lambda_v ||z_v,j - v_i^-||^2 / sigma_v^2.
```

The velocity term is also dimensionless. Adding raw metres squared to raw
metres-per-second squared would make the answer depend on unit choice rather
than information quality. `lambda_v = 1` states that the reviewed velocity
noise scale is trusted as modeled.

The auxiliary velocity participates only in association. Position residuals
still drive the alpha-beta correction, isolating why the assignment changes.
On the seed-5908 record it prevents the swap entirely. Across 200 seeds it
lowers, but does not eliminate, failures. No single feature creates identity
information when the targets are indistinguishable in every measured feature.

Amplitude, class, or micro-Doppler features could be normalized and added by
the same principle. They would require their own calibrated uncertainty and
could be harmful when stale, biased, or correlated more strongly than the cost
model assumes.

## Read the three one-variable sweeps

Every case uses seeds 5901 through 6100 for both methods. Pairing preserves the
underlying standard-normal draws while only the named control changes.

### Position noise

`sigma_p = [2, 6, 10] m` widens the spatial report cloud. More trials become
ambiguous, and wrong histories last longer. The velocity feature helps at all
three reviewed noise levels, but its advantage shrinks when position evidence
becomes very poor.

### Update interval

`dt = [0.5, 1, 2] s` keeps 25 scans and the crossing at the center. Changing
this one control has two visible consequences in the fixed alpha-beta tracker:
a larger interval places adjacent scans farther from the ambiguous crossing,
while `(beta/dt)r` makes each residual's velocity correction smaller. Together
they lower failures in this reviewed exact constant-velocity scene. That
observed direction is not a universal claim that slower updates improve a
tracker. With acceleration, missed detections, or model error, a larger `dt`
usually also worsens prediction uncertainty.

### Closest approach

An along-track offset makes the trajectories miss by `[0, 12, 24] m` while
their velocities and noise stay fixed. More separation supplies spatial
evidence, so failure frequency falls. Separation helps because the pair costs
become distinguishable, not because the tracker learns hidden truth labels.

## Broken independent-nearest case

The intentionally broken path lets each track take its own row minimum. It
does not remove the selected report column. On 12 scans, both tracks consume
the same report. This is coalescence, not a valid one-to-one identity swap:
one physical measurement has been used twice.

Recovery restores both row and column removal, adds the reviewed velocity
term, and reruns on the identical arrays. Exact equality with the original
velocity-aware histories proves recovery from the algorithm choice rather
than from a new noise realization.

## Limiting cases

- As closest approach grows far beyond position noise, position-only links are
  usually unambiguous.
- At an exact crossing with identical position, velocity, amplitude, and class
  evidence, the target permutation is unobservable. A tie rule is repeatable,
  not informative.
- As `sigma_v` approaches infinity or `lambda_v` approaches zero, the enriched
  cost collapses to position-only association.
- If velocity separation approaches zero, the auxiliary term cannot distinguish
  the reports even when its noise is small.
- If the stated feature variance is too small, that feature is overweighted;
  one bad velocity report can dominate sound position evidence.
- If `dt` approaches zero in this discrete lesson, `(beta/dt)r` becomes highly
  sensitive to residual noise; `dt` must remain positive.
- Greedy one-to-one selection prevents report reuse but does not minimize total
  cost over all possible assignments and does not represent joint ambiguity.

## Common interpretation mistakes

**Mistake:** a detection contains its target ID.

**Correction:** identity is an audit label here. Association receives only
position and velocity measurements.

**Mistake:** two transitions mean only two bad associations.

**Correction:** the reviewed swap has two transitions but 24 wrong links
because the wrong histories persist for 12 scans.

**Mistake:** one-to-one nearest neighbor prevents identity swaps.

**Correction:** it prevents duplicate measurement use. It can still choose a
valid but incorrect permutation.

**Mistake:** the velocity-aware result proves velocity always solves crossing.

**Correction:** it lowers failures under the declared noise model. Identical or
miscalibrated features remain ambiguous and can make the result worse.

**Mistake:** the update-rate sweep proves slower radar updates are better.

**Correction:** its direction belongs to this centered, exact-CV construction;
real prediction uncertainty introduces another mechanism.

## Claim boundary

This is a bounded synthetic base-MATLAB model with idealized Cartesian reports.
Repository tests independently check the seeded arithmetic, cost, assignment,
state update, sweeps, broken path, recovery, resource limits, and learner CLI.
Static checks cannot prove MATLAB parsing or execution, rendered figures,
statistical calibration, educational effectiveness, hardware/HIL behavior,
real-time performance, operational radar performance, or field results.
