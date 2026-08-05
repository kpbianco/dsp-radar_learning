# Walkthrough: watch local geometry turn polar evidence into a track

Run `experiment.m` from this module directory. The script is finite, stateless,
and uses a private seed. Work through one figure or processing transition at a
time rather than treating all five figures as one dashboard.

## Baseline observation

Before Figure 1, make one prediction: as the target passes behind the radar,
will its physical direction jump by nearly 360 degrees when the displayed
bearing changes from positive to negative?

Figure 1 shows truth and raw polar-to-Cartesian reports. Range remains in
metres. Bearing is displayed in degrees and crosses the `+/-180 deg` convention
even though the x-y path stays continuous. The converted reports spread mostly
across the line of sight because a fixed angular error becomes a sideways
position error.

Figure 2 adds the EKF trajectory and selected nominal 95% covariance ellipses.
Ignore the first 15 scans while velocity is learned from repeated position
updates. Then compare raw conversion error with EKF error. Watch each ellipse
rotate with line of sight and change its radial/tangential proportions.

Figure 3 keeps the two innovation units separate. The range residual is in
metres; the bearing residual is wrapped and displayed in degrees. NIS combines
both using `S` and is dimensionless. A few samples outside a nominal 95% bound
do not by themselves disprove the model.

Read the console metrics in their declared units:

- raw and EKF Cartesian position RMSE in metres;
- position-ellipse and joint-innovation coverage as fractions;
- mean NIS as dimensionless descriptive evidence;
- mean posterior radial and tangential standard deviations in metres;
- broken-case position RMSE in metres and maximum bearing residual in degrees;
- total filter runs, bounded predict/update transitions, and tagged figure count.

## Sweep 1: change only assumed bearing noise

Figure 4 begins with

```matlab
bearing_std_sweep_deg = [0.2 0.8 3.2];
```

The script reuses the same truth, range-bearing samples, initial state,
covariance, Q, range standard deviation, and random draws.

- `0.2 deg` declares direction highly precise. The correction trusts bearing
  strongly and tangential covariance becomes narrow; NIS can reveal that this
  is more confidence than the actual `0.8 deg` reports deserve.
- `0.8 deg` matches the generated bearing-noise scale.
- `3.2 deg` treats direction as weak evidence. Tangential covariance widens and
  prediction/range carry more of the update.

Do not require RMSE to change monotonically in one realization. The reliable
cause/effect is that declared angular uncertainty changes angular trust and the
tangential covariance scale.

## Sweep 2: change only target range in the local noise map

The lower panel holds `sigma_range = 18 m` and `sigma_bearing = 0.8 deg` while
evaluating the same ray at

```matlab
geometry_range_sweep_m = [500 1500 3000];
```

Radial standard deviation stays at `18 m`. Tangential standard deviation grows
approximately as `r*sigma_theta`: about `7`, `21`, then `42 m`. The
Jacobian-mapped covariance major axis is the larger of the radial and
tangential values: range error dominates at `500 m`, then bearing error
dominates at the longer ranges. The radar angle did not become noisier; the
same angular wedge simply spans more metres farther away.

## Broken branch-cut subtraction and recovery

Figure 5 reruns the exact same record with only `wrap_innovation = false`. Near
the branch cut, ordinary subtraction can produce a residual beyond `180 deg`
instead of the small local difference. The linearized correction then points
the track around the wrong side of the radar and position error rises.

Recovery restores

```matlab
innovation(2,k) = atan2(sin(innovation(2,k)), cos(innovation(2,k)));
```

and reruns from the top. The recovered state history must exactly match the
baseline because seed, reports, initialization, model, and every other control
are unchanged.

## Failure interpretation and malformed-input recovery

If the ellipse becomes implausibly narrow tangentially, check that bearing
degrees were converted to radians before squaring. If the track jumps at
`+/-180 deg`, check wrapping before changing Q or inventing a maneuver. If the
script reports `P56:LinearizationSingularity`, the predicted position is within
the reviewed `25 m` guard where this Jacobian is not acceptable; use a valid
initialization or a filter designed for that geometry.

The helper rejects malformed measurement shape, nonfinite values, nonpositive
range, bearing outside `[-pi,pi]`, invalid noise scales, malformed state or
covariance, near-origin initialization, and a nonlogical wrap flag before an
update. Correct the named input and rerun the entire script; no partial result
is persisted.

If graphics or a local foreground run blocks, press Ctrl+C. Close only figures
tagged `P56` if necessary, restore reviewed controls, and rerun from the top.
There is no callback, timer, worker, network request, file write, or background
job to cancel. The learner CLI tests use a 10-second subprocess timeout and a
temporary `HOME` so validation cannot mutate repository learner state.

Repository rollback is bounded to the P56 module, P56-owned test/evidence and
catalog additions, plus restoring only P56 manifest status to `scaffolded`.
The isolated test performs that rollback and recovery in a temporary fixture
while preserving P55 and the complete P57 identity object. It does not assume
that later batches remain pending.

## Concept connection

P55 showed that covariance controls prediction-versus-measurement trust for a
linear report. P56 shows that `H` first rotates and scales that trust according
to local radar geometry. P57 will use the resulting innovation covariance to
ask which report should update which track.

## Expected observations

- raw Cartesian reports are anisotropic rather than a round fixed-noise cloud;
- the EKF smooths position while learning velocity across scans;
- covariance ellipses rotate and change shape with line of sight;
- larger assumed bearing noise widens tangential uncertainty and reduces
  angular trust;
- fixed bearing noise maps to more cross-range metres at longer range; and
- unwrapped branch-cut subtraction creates a huge false innovation, while
  deterministic recovery restores the baseline.

Static tests and the Python oracle cannot substitute for MATLAB execution or
visual inspection. They also provide no hardware/HIL, field, real-time,
deployment, or production validation.
