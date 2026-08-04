# Walkthrough: watch covariance become trust

Run `experiment.m` from the module directory. Work through one figure or
processing transition at a time. The script is stateless and does not read or
write files or learner progress.

## Baseline observation

Before Figure 1, make one prediction: will velocity remain exactly `20 m/s`
when the truth receives small unknown accelerations?

Figure 1 shows the seeded truth before filtering. Position reports scatter
around true position, while acceleration makes velocity wander rather than
remaining exactly constant. This is a *nearly* constant-velocity scene: `F`
predicts constant velocity for one interval and `Q` admits what that predictor
cannot know.

Figure 2 overlays corrected position and velocity with posterior two-sigma
bounds. Ignore the initial transient when the zero velocity guess is being
corrected. After the 15-scan warm-up, verify that most truth errors are inside
the bounds without expecting every sample to be contained.

Figure 3 separates the operational quantities from truth. Innovation is report
minus predicted report and is compared with `+/-2 sqrt(S)`. Position and
velocity gains evolve as covariance settles; they are not hand-selected alpha
and beta constants.

Read the console metrics in their declared units:

- raw report and baseline position RMSE in metres;
- baseline velocity RMSE in metres per second;
- posterior position, posterior velocity, and innovation two-sigma coverage as
  fractions from this one seeded record;
- mean normalized innovation squared;
- mean position gain (dimensionless) and velocity gain (`1/s`); and
- broken-case coverage, velocity RMSE, and NIS diagnostics.

## Sweep 1: change only Q

Figure 4 uses:

```matlab
process_std_sweep_mps2 = [0.10 0.80 3.20];
```

Each value is squared inside `Q = sigma_a^2 G G'`. Report noise remains `25 m`
and the exact same truth, measurements, and initial state are reused.

- `0.10 m/s^2` underestimates how much velocity can wander. The filter leans
  on prediction and its bounds can become too narrow.
- `0.80 m/s^2` matches the seeded scene's acceleration scale.
- `3.20 m/s^2` admits much more motion uncertainty, raises report trust, and
  makes the state more measurement-responsive.

Do not demand monotonic RMSE from one noise realization. The robust physical
transition is increasing predicted uncertainty and generally increasing gain.
Coverage says whether the claimed uncertainty remains plausible.

## Sweep 2: change only R

Figure 5 begins with:

```matlab
measurement_std_sweep_m = [5 25 100];
```

Each value is squared inside `R = sigma_z^2`; Q stays at the reviewed value.

- `5 m` makes the filter follow the noisy reports strongly and underestimates
  the actual `25 m` sensor scatter.
- `25 m` matches the generated report standard deviation.
- `100 m` tells the filter that reports are weak evidence, so gain falls and
  prediction dominates.

Connect this to the guiding question: trust follows *relative covariance*.
Changing R does not alter any report sample already generated.

## Broken mismatch pair and recovery

The last panel of Figure 5 compares normalized innovations for reviewed tuning
with an extreme broken R assumption of `0.5 m`. Report chasing and narrow
innovation bounds make NIS much larger than the recovered baseline.

The second failure sets Q to zero while the target still receives acceleration.
It is not plotted as a claim that Q zero is universally invalid; it is invalid
for this scene. Its position and velocity coverage plus velocity RMSE are
printed so covariance overconfidence is not hidden by position error alone.

Recover both failures by restoring:

```matlab
assumed_process_acceleration_std_mps2 = 0.8;
assumed_measurement_std_m = 25;
```

and rerunning from the top. Recovery reuses the same private seed, truth,
reports, initialization, predict/update equations, and resource ceilings.

## Failure interpretation and malformed-input recovery

If gain moves opposite to the expected direction, check that standard
deviations are squared exactly once and that `S = H*P_pred*H' + R`. If
covariance becomes asymmetric or negative, restore the Joseph update and final
symmetrization. If innovation resembles truth error, check that it is computed
from the report and predicted report, not simulation truth.

Input guards reject nonfinite, logical, complex, nonscalar, incorrectly shaped,
nonpositive-R, negative-Q-scale, malformed-sweep, and resource-ceiling edits
before random generation or state-history allocation. Restore the reviewed
controls instead of raising a ceiling to silence the guard.

## Cancellation, timeout, rollback, and deterministic recovery

Press Ctrl+C to cancel an interactive run. Partial workspace variables or P55
figures may remain. Rerun from the top: `clear` removes partial variables,
validation runs first, only figures tagged `P55` are closed, a private seeded
stream reconstructs the scene, and every filter state is reinitialized. There
is no persistent experiment state to roll back.

Repository CLI tests execute in isolated temporary repositories with a
10-second subprocess timeout. That bounds a hung fixture; it is not a claim
that MATLAB cancellation or a MATLAB runtime timeout was executed here.
Repository rollback removes P55 artifacts/catalog changes and restores only
P55 manifest status to `scaffolded`, leaving P54 and later identities intact.

## Concept connection and completion handoff

P54 made fixed-gain prediction intuitive. P55 shows how covariance produces
time-varying trust. P56 will reuse covariance with nonlinear measurement
geometry, and P57 will decide which report is eligible to update which track.

Finish by answering: how do Q, predicted covariance, R, innovation variance,
and Kalman gain work together to choose prediction-versus-measurement trust?
