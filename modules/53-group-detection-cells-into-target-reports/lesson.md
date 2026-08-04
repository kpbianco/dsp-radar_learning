# Lesson: from detector cells to one target measurement

## Guiding question

How do several threshold-crossing cells become one physical detection?

The threshold mask is not a target list. A resolved target normally spreads
over neighboring range-Doppler cells because the matched-filter response and
finite coherent processing interval have width. Sidelobes and noise can cross
the threshold too. Sending every `true` mask cell to a tracker would make one
object look like many measurements.

P53 begins Phase 6 by converting the detector output into reports. It depends
directly on P52's validation discipline, P50's two-dimensional detector cells,
and P42's axis convention: rows are range, columns are signed radial velocity,
and positive velocity is approaching. Grouping organizes threshold crossings;
it does not correct a bad threshold or a mismatched background model.

## 1. Normalize what the detector produced

The experiment uses a dimensionless score

```text
d(i,j) = CUT power(i,j) / threshold(i,j)
D(i,j) = true when d(i,j) > 1
```

This could come from a fixed threshold or CFAR. The grouping stage needs the
binary mask `D` and retains `d` for strength and centroid weights. Range remains
in metres and signed radial velocity in metres per second.

The seed affects a bounded background texture, but that texture stays below
one. Extended targets, disconnected sidelobes, and explicitly placed false
cells create all threshold crossings. The baseline behavior therefore does not
depend on one lucky random background spike.

## 2. Local maxima are representatives, not complete reports

A threshold blob can contain many cells. A 3-by-3 local-maximum test identifies
the strongest neighborhood representative. If equal samples form a plateau,
the first cell in row-major order wins so the result is deterministic.

Peak selection helps visualization and supplies a component peak location, but
it does not answer which peaks belong together. A sidelobe or isolated false
cell can also be a perfectly valid local maximum. That is why the broken case,
which promotes every local maximum directly to a tracker report, still
over-reports.

## 3. Connectivity defines a physical grouping assumption

The baseline uses 8-connectivity. Cells belong to the same component when a
path joins them through horizontal, vertical, or diagonal threshold neighbors.
The script labels them with an explicit bounded queue:

```text
start at the first unlabeled detection cell
label it and enqueue it
visit all eight neighbors of each queued cell
enqueue each unseen detected neighbor exactly once
finish when the queue is empty
```

No `bwconncomp`, `bwlabel`, `regionprops`, `imregionalmax`, or tracking object
hides this operation. A diagonal connection counts because discretized target
responses often touch diagonally.

Connectivity is useful but not omniscient. Two targets whose threshold regions
touch become one component. A single target split below threshold can become
two. Separating merged targets needs a deliberate multi-peak splitter or later
association model, not a claim that connected components solve every scene.

## 4. Component filtering removes small nuisance blobs

Let `|C|` be the number of threshold cells in component `C`. The baseline emits
a report only when

```text
|C| >= minimum_component_cells.
```

With a minimum of three, the seeded one- and two-cell nuisance components are
rejected while the extended target blobs remain. Sweep 1 changes only this
minimum. A minimum of one accepts false singletons; an excessive minimum can
delete a weak or compact target. Component size is therefore a policy choice,
not evidence that a cell is noise.

## 5. Weighted centroiding gives a sub-cell measurement

For detected cell `(i,j)` in component `C`, the baseline weight is the excess
above threshold:

```text
w(i,j) = (d(i,j) - 1)^p
range_hat = sum_C w(i,j) range(i) / sum_C w(i,j)
velocity_hat = sum_C w(i,j) velocity(j) / sum_C w(i,j)
```

Sweep 2 changes only `p`:

- `p = 0` gives every detected cell equal weight: the geometric center.
- `p = 1` uses linear excess power: the reviewed baseline.
- `p = 2` concentrates the estimate toward the strongest cells.

Weighting can move a centroid between bin centers, improving the cell-center
peak estimate for a smooth isolated response. It can also move the estimate
toward an asymmetric shoulder, sidelobe, saturation artifact, or interfering
target. Larger `p` is not automatically more accurate.

## 6. What one report contains

Each accepted component exports:

- weighted range in metres and signed radial velocity in metres per second;
- peak cell range/velocity and peak normalized score;
- integrated excess score, `sum_C(d - 1)`;
- detected cell count;
- occupied range and velocity extents, including one cell width;
- effective weighted cell count; and
- range/velocity shape-derived uncertainty proxies.

The effective count is

```text
N_eff = (sum w)^2 / sum(w^2).
```

The range proxy, for example, combines the weighted component second moment
with bin quantization:

```text
sigma_R,proxy = sqrt(weighted range spread / N_eff + Delta_R^2/12).
```

This summarizes observed blob shape. It is explicitly uncalibrated: it is not
the tracker measurement covariance `R`, a confidence interval, or proof of
Gaussian error. Calibration would require repeated truth-referenced trials
under the intended detector and scene model.

## 7. Truth comparison without stealing P57's job

Because this is a synthetic lesson, truth is known. The experiment reads the
component label at each known target center and compares that component's
report with the target's true range and velocity. It does not add an unexplained
nearest-neighbor association algorithm. General measurement-to-track
association belongs later in P57.

## Limiting cases and invariants

- One isolated detected cell is one component, but the baseline minimum-size
  policy rejects it.
- Diagonally touching cells are one component under 8-connectivity.
- A symmetric component has its centroid at the symmetry center.
- Uniformly scaling both CUT power and threshold leaves normalized score,
  mask, components, and centroid unchanged.
- Translating a component on uniform axes translates its report by the same
  amount.
- Touching target responses merge; a below-threshold gap separates them.
- Zero total centroid weight is invalid. With `d > 1` and `p` in `[0,2]`, the
  reviewed weights are positive.
- Shape extent grows when sidelobes join a component, but that does not make the
  proxy a calibrated statistical uncertainty.

## Common interpretation mistakes

**Mistake:** every local maximum is a physical target.
**Correction:** sidelobes and isolated false cells can be local maxima too.

**Mistake:** the strongest cell is always the best position estimate.
**Correction:** a centroid can recover sub-cell position, while asymmetric
energy can bias either peak or centroid.

**Mistake:** a larger minimum component size always improves quality.
**Correction:** it removes nuisance blobs and can also remove compact targets.

**Mistake:** one connected component always equals one object.
**Correction:** connectivity merges touching objects and splits responses with
gaps.

**Mistake:** component spread is tracker covariance.
**Correction:** it is an uncalibrated morphology proxy until repeated errors
against truth justify a covariance model.

## Claim boundary

This module is a seeded synthetic, base-MATLAB experiment. Static repository
checks inspect its equations, operations, bounds, and documentation. They do
not prove MATLAB execution, rendered plots, numerical fidelity, learning
effectiveness, hardware/HIL, real-time behavior, operational radar performance,
or field validity.
