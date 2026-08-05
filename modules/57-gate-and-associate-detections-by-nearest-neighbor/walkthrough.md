# Walkthrough: watch a gate turn predictions into admissible choices

Run `experiment.m` from this module directory. The script is finite, stateless,
and uses a private seed. Work through one figure or processing transition at a
time.

## Baseline observation

Before Figure 1, make one prediction: should a report that is closest in metres
always update a track?

Figure 1 shows the prior and predicted state for three tracks, hidden target
truth used only for scoring, three noisy target reports, and three clutter
reports. Association receives only the six unlabeled detections. Check that all
predictions happen before any pair is selected.

Figure 2 isolates each track. The blue ellipse is its nominal validation gate.
Green residual lines terminate at detections whose squared Mahalanobis distance
passes; red dotted lines fail. For Track 1, compare true report `D3` along the
wide gate direction with clutter `D2` across the narrow direction. `D2` is
closer in metres but outside the uncertainty-shaped gate.

Figure 3 shows the complete `3 x 6` distance matrix. Each cell displays
dimensionless `d^2` and `G` or `X` for gate pass/fail. The right panel draws the
one-to-one selected links. Confirm the baseline mapping printed in the console:

```text
Track 1 -> D3
Track 2 -> D1
Track 3 -> D5
```

Only `D2`, `D4`, and `D6` remain unused, and their retained truth IDs are zero
because they are clutter. Truth IDs never enter the association function.

Read the console metrics in their declared units:

- squared Mahalanobis distance and gate threshold are dimensionless;
- x/y residuals and ellipse axes are in metres;
- ellipse area is in square metres;
- assignment, candidate, and clutter counts are per scan; and
- association passes and track-report pair slots are finite counts.

## Sweep 1: change only the gate threshold

Figure 4 uses

```matlab
gate_threshold_sweep_d2 = [0.5 5.991 13.816];
```

The prediction, covariance, report noise, clutter, residuals, and distance
matrix do not change.

- At `0.5`, at least one physically correct pair may be too unlikely for the
  deliberately tight gate.
- At `5.991`, all three separated targets associate and no clutter is selected.
- At `13.816`, Track 1's cross-ellipse clutter becomes a valid candidate, so
  valid-pair count increases even though the report record contains no new
  information.

Distinguish candidate count from assignment count. The one-to-one constraint
can still produce at most three assignments.

## Sweep 2: change only predicted covariance scale

Figure 5 uses

```matlab
covariance_scale_sweep = [0.25 1 4];
```

The predicted centres, reports, `R`, gate threshold, and nearest-neighbor rule
stay fixed. The left panel shows that Track 1's true-report and clutter
distances both shrink as predicted uncertainty grows. Their rates differ
because the ellipse is anisotropic. The centre panel shows physical gate area;
the right panel shows total valid-pair count without mixing their units.

Do not interpret a larger gate as a better tracker. It honestly represents a
less certain prediction and creates more opportunity for clutter competition.

## Broken Euclidean/no-gate path and recovery

Figure 6 changes two coupled pieces that define the deliberately naive method:
it uses raw Euclidean squared metres as its score and treats every pair as
valid. The same one-to-one greedy selection then gives Track 1 the closer
clutter `D2`, leaving its true `D3` unused. The broken path therefore has fewer
correct assignments and at least one clutter assignment.

Recovery restores the reviewed uncertainty-aware metric and gate on the exact
same prediction and detection arrays:

```matlab
d2 = residual'*(S\residual);
valid = d2 <= gate_threshold_d2;
```

The recovered assignment must equal the baseline exactly. This demonstrates
recovery from the isolated algorithm choice, not from a lucky new noise draw.

## Failure interpretation and malformed-input recovery

If one detection is linked twice, verify that selecting a pair removes both
its track row and measurement column. If ellipse axes look wrong, verify that
the plot uses `sqrt(gamma)` while the gate compares `d^2 <= gamma`. If the
correct report is unexpectedly rejected, inspect both `P^-` and `R` inside
`S` before widening the gate.

The helpers reject malformed shapes, unsupported numeric classes, complex or
nonfinite values, negative distances, nonlogical gate masks, mismatched matrix
sizes, nonsymmetric or non-positive-definite innovation covariance, invalid
sweeps, and inputs beyond the reviewed track/report/pair bounds. Correct the
named input and rerun the entire script; no partial result is persisted.

If graphics or a local foreground run blocks, press Ctrl+C. Close only figures
tagged `P57` if necessary, restore the reviewed controls, and rerun from the
top. There is no callback, timer, worker, network request, file write, or
background job to cancel. Learner-interface tests use a 10-second subprocess
timeout and a temporary `HOME`, so validation cannot mutate repository learner
state.

Repository rollback is bounded to the P57 module, P57-owned test/evidence and
catalog additions, plus restoring only P57 manifest status to `scaffolded`.
The isolated test performs that rollback and recovery in a temporary fixture
while preserving P56 and the complete P58 identity object. It does not assume
that any later module remains pending.

## Concept connection

P56 used one already-associated report to form a nonlinear EKF correction.
P57 uses the same innovation-covariance idea before correction, across every
track-report pair. P58 will interpret unassigned tracks and reports over time;
P59 will challenge this greedy rule with crossing targets.

## Expected observations

- gates follow predicted uncertainty shape rather than a fixed metre radius;
- the nominal assignment is `[3 1 5]` for Tracks 1–3;
- outside-gate clutter remains unassigned;
- a looser threshold or broader covariance admits more candidates;
- one-to-one removal prevents detection reuse;
- ungated Euclidean distance selects Track 1's closer clutter; and
- restoring Mahalanobis gating exactly recovers the baseline.

Static tests and the Python oracle cannot substitute for MATLAB execution or
visual inspection. They also provide no hardware/HIL, field, real-time,
RT1/RT2, Unreal, signing, deployment, staging, or production validation.
