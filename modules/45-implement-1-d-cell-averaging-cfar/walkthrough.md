# P45 walkthrough: Implement 1-D Cell-Averaging CFAR

## Guiding question

How can the threshold adapt to the local noise level?

Run `experiment.m` once without editing its controls. It uses private seed
4501, only base MATLAB operations, five bounded figure groups, and no file,
network, shell, timer, or learner-state access.

## Baseline — watch the local scale become a threshold

Start with Figure 1. The upper trace is the mean power used to synthesize the
background; the lower trace is one random observed power profile plus three
targets. Do not expect individual noise samples to lie on the mean curve.

Now inspect Figure 2. In the upper panel, follow the black threshold from low-
background range cells toward high-background cells. In the lower panel,
compare the 24-cell training average with the known synthetic mean. Notice the
gray edge markers: 14 CUTs at each end are excluded because 12 training and two
guard cells do not fit on both sides.

Expected observation: the threshold fluctuates locally but its typical level
rises with the background. The three injected targets cross it, while each
decision uses only nearby leading and lagging training power.

Common mistake: reading the known background curve as detector input. It is
shown only for explanation. The detector sees `profile_power` and never uses
target truth or `background_mean_power` in its CA estimate.

Record these baseline values from the command window or `results`:

- `training_cell_count` and `cfar_scale_factor`;
- eligible and excluded CUT counts;
- target detections and non-target crossings; and
- low- versus high-background median thresholds in linear power units.

## Sweep 1 — change only requested false-alarm probability

Keep the range profile, training cells, guards, and all targets fixed. Figure 3
uses `Pfa = 1e-2`, `1e-3`, and `1e-4`.

Before looking at the lines, predict only the direction: will asking for fewer
false alarms move `alpha` and the threshold up or down?

Expected observation: smaller requested `Pfa` makes
`N*(Pfa^(-1/N)-1)` larger, so all local thresholds rise and threshold-crossing
counts cannot increase. A target may eventually be missed if the requirement
becomes strict enough.

Common mistake: treating the few non-target counts in one seeded profile as a
measured probability. With only 228 eligible CUTs, a `1e-3` claim is below one
expected event per profile. P52 will use many independent trials.

## Sweep 2 — change only the scene power scale

Figure 4 multiplies the complete observed scene by 0.5, 1, and 2. The window,
`Pfa`, target-to-background ratios, and unit-noise realization do not change.

Expected observation: each training average and threshold scales in exact
proportion to the scene. In the lower panel the three curves of
`observed power / threshold` coincide, so target and false-alarm decisions are
identical at every scale.

Connect this result to P43: a fixed native-unit threshold would not move and
would change its decisions. CA-CFAR adapts because both numerator and local
reference carry the same power scale.

Common mistake: saying CFAR “removes noise.” The noisy samples remain. CFAR
changes the comparison level using a local estimate.

## Intentionally broken case — average the dB plot

Figure 5 repeats the same training geometry but first converts each training
power to dB, averages those dB values, and converts back. That is a geometric
mean, not the arithmetic mean required by the exponential CA-CFAR model.

Expected observation: the red broken threshold lies below the correct black
threshold. Every correct detection remains a broken detection, and the broken
case can add non-target crossings. `broken_claim_is_valid` is deliberately
false even if one target picture happens to look attractive.

Common mistake: assuming an average is unchanged by a logarithmic display
conversion. In general,
`10^(mean(10*log10(z))/10) <= mean(z)` for positive unequal powers.

## Recovery — restore the estimator domain

Recovery does not tune a compensating multiplier. It returns to linear power,
computes the arithmetic training-cell mean, and then applies the reviewed
`alpha`. The script requires `recovery_exact` to reproduce the baseline
threshold (including NaN edge markers) and decisions exactly.

If you interrupt with Ctrl+C, rerun the full script. `clearvars` removes partial
workspace values, only figures tagged `P45` are closed, and a fresh private
stream recreates the same scene. No external write, background task, or global
random state needs rollback. This is recovery guidance, not evidence that
runtime cancellation was exercised in this environment.

## Concept connection and completion handoff

Connect the plots in one chain:

1. square-law noise power supplies an exponential local background;
2. guards separate the CUT from the training samples;
3. their linear-power average estimates the local mean;
4. `alpha` maps requested `Pfa` to a power threshold under the homogeneous
   independent model; and
5. uniform power changes scale the estimate and threshold together, preserving
   normalized decisions.

You are ready for `checks.md` when you can answer the guiding question, explain
why edges are excluded, and identify why dB-domain averaging breaks the model.
