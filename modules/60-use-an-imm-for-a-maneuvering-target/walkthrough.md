# Walkthrough: watch evidence move weight between motion models

Run `experiment.m` from this module directory. It is finite and stateless. It
uses private seeded arithmetic, leaves MATLAB's global random stream alone,
closes only stale figures tagged `P60`, preserves unrelated open figures,
creates only new figures tagged `P60`, and retains outputs in `p60_results`.

## Baseline observation

Before Figure 1, make one prediction: when a position report starts bending
away from the straight-line extrapolation, which model should find that report
less surprising?

Figure 1 shows the truth trajectory, noisy position reports, and the two truth
acceleration components. Red trajectory markers and nonzero acceleration mark
scans 16-25 and 39-48. Those truth arrays are an audit overlay; the trackers
receive only the blue report coordinates.

## Processing transition 1: compare one fixed explanation with a model bank

Figure 2 overlays the poorly matched fixed straight filter and the combined
IMM estimate. Follow each curve into the northward and westward bursts. The
straight filter keeps extrapolating its earlier velocity, while the
persistent-acceleration filter can learn curvature. The IMM bends toward the
conditioned estimate whose recent innovations fit better.

Figure 3 shows that transition directly. In the upper panel, read the red
maneuver probability alongside the dotted truth regime. It need not jump at
the exact first maneuver scan: acceleration is inferred from noisy positions,
not supplied as a flag. Compare its average level during red-marked scans with
its average during straight scans.

In the lower panel, compare position error in metres. Confirm the console
metrics report lower overall and maneuver-scan RMSE for the IMM than for the
fixed straight model.

## Processing transition 2: look inside the blend

Figure 4 separates the two conditioned north-position estimates. Both use the
same measurement at each scan, but their prediction matrices and process
covariances differ. The lower panel shows normalized innovation squared, one
term in each model's likelihood. Lower NIS rewards a better normalized fit,
while the likelihood's log-determinant term also penalizes a diffuse
innovation covariance; NIS alone does not determine which model earns more
weight.

Do not interpret the red probability as a maneuver sensor. It also depends on
initial probability, transition support, `Q`, `R`, and the completeness of the
two-model bank.

## Sweep 1: change only maneuver strength

The first panel of Figure 5 changes:

```matlab
maneuver_acceleration_sweep_mps2 = [0.8 2.0 3.2];
```

Seed, normalized noise samples, 10 m report-noise scale, scan interval, filter
tuning, and transition matrix stay fixed. The fixed straight model's
maneuver-scan RMSE grows sharply as its assumption becomes worse. The IMM also
has finite error, but remains lower in every reviewed case. Inspect
`p60_results.acceleration_maneuver_probability`: stronger bursts make the
maneuver model easier to distinguish on average.

## Sweep 2: change only mode persistence

The second panel of Figure 5 changes:

```matlab
mode_stay_probability_sweep = [0.80 0.94 0.99];
```

Every case uses the exact baseline measurement array. The left axis reports
overall position RMSE; the right axis counts changes in the dominant model.
Higher persistence lowers endpoint chatter but can delay a legitimate switch.
This is a stability/responsiveness trade, not proof that 0.99 is universally
better.

## Broken zero-support case and exact recovery

Figure 6 deliberately sets:

```matlab
broken_transition_probability = eye(2);
broken_initial_mode_probability = [1; 0];
```

The maneuver mode has no initial probability and no transition path from the
straight mode. Its probability remains exactly zero even during both bursts.
The broken combined estimate therefore follows the fixed straight result and
has larger error than the reviewed IMM.

Recovery restores `[0.85; 0.15]` and nonzero off-diagonal transitions, then
processes the identical `baseline_scene.measurement_m`. `recovery_exact = 1`
means both the combined-state and probability arrays exactly reproduce the
original baseline.

## Failure interpretation and recovery from bad inputs

If the maneuver probability does not rise on average, first restore seed 6007,
the reviewed model matrices, `Q`, `R`, and transition probabilities. If mode
probabilities do not sum to one, inspect the log-weight shift and final
normalization. If covariance becomes asymmetric, restore the Joseph update and
explicit symmetry operation. Never patch a probability curve by reading the
truth regime flag inside the tracker.

Malformed, complex, nonfinite, nonpositive, misordered, duplicate-baseline, or
oversized controls are rejected before large work or figure creation.
Malformed measurements, transition rows, and probability vectors are also
rejected. Correct the named input and rerun; the experiment writes no partial
output file.

If a foreground run or graphics render blocks, press Ctrl+C, close only figures
tagged `P60`, restore reviewed controls, and rerun from the top. There is no
timer, worker, callback, network operation, input file, or output file to
cancel. Learner CLI tests use a temporary repository and temporary `HOME` with
a 10-second subprocess timeout, so they neither read nor change personal
`.learning/` state.

Repository rollback removes only P60 module/test/evidence/catalog additions
and restores only P60 manifest status to `scaffolded`. P59 remains implemented;
later module state is derived from the canonical manifest and is not frozen by
P60 tests. Restoring the implementation and `implemented` status recovers tutor
entry without changing learner notes or completions.

## Concept connection

P55 showed how one motion model trades prediction against a noisy report. P59
showed that association cannot use hidden truth identity. P60 keeps that audit
boundary and asks a different uncertainty question: which motion law should
shape the next prediction? IMM represents that uncertainty with a small model
bank, transition memory, innovation evidence, and a weighted state/covariance.

## Expected observations

- the target alternates between straight motion and two acceleration bursts;
- the fixed straight model lags through both maneuvers;
- maneuver-model probability is higher on maneuver scans on average;
- IMM overall and maneuver position RMSE are lower than fixed-model RMSE;
- stronger bursts increase maneuver probability and expose fixed-model error;
- higher mode persistence reduces endpoint dominant-mode chatter;
- zero prior plus zero transition support makes the maneuver mode unreachable;
  and
- restoring support exactly recovers state and probability arrays on the same
  reports.

Static tests and an independent Python oracle are not MATLAB runtime or visual
evidence. They provide no hardware/HIL, field, real-time, RT1/RT2, Unreal,
signing, deployment, staging, or production validation.
