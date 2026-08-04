# Walkthrough: Diagnose CFAR by opening the training window

## Guiding question

Where do standard CFAR assumptions break?

Use the same rule throughout: explain a detector disagreement from the powers
inside its leading and lagging training cells before naming a preferred
variant.

## 1. Run the deterministic baseline

Run `experiment.m` from the top. The script uses private seed `5101`, closes
only figures tagged `P51`, and retains its outputs in `results`.

Look first at **P51 combined stress scene**.

**Expected observation:** the mean background steps upward at the clutter
edge and swells again at long range. The strong target produces response energy
away from its center, a weak neighbor sits inside its CFAR influence, and the
long-range group places several targets inside shared training windows.

Concrete observation question: which known target center is nearest the
abrupt change in mean background?

## 2. Compare one threshold panel at a time

Open **P51 equal-Pfa detector thresholds**. Start with CA, then GO, SO, and OS.
All four have nominal homogeneous `Pfa=10^-3`; they do not share one alpha.

**Expected observation:** the masks disagree most near the clutter edge,
strong-target response, and crowded group. A higher threshold is not evidence
that a detector is globally safer—it may be reacting to contaminated or
mismatched references.

Use `results.target_detection` to distinguish target-center hits and misses.
Use `results.target_miss_cause_matrix` for detector-specific miss explanations,
`results.response_artifact_crossing_counts` for target-response false plots,
and `results.h0_crossing_category_counts` for background-only crossings.
Sidelobe crossings are operational false plots on modeled target response, not
H0 false-alarm samples.

## 3. Explain the representative CUTs

Open **P51 representative training contents**. Each panel shows all 24
training powers and the guarded CUT. Read
`results.inspection_statistics` columns as

```text
[CUT power, leading mean, lagging mean, CA mean, rank-18 OS power].
```

At the weak neighbor, look for strong-target energy in one reference half. At
the low-side edge target, compare the low leading mean with the high lagging
mean. At the crowded target, count target-contaminated cells on both sides.

**Expected observation:** GO follows the larger side, SO follows the smaller
side, CA blends the sides, and OS responds to the value occupying rank 18.
That training content, not the algorithm's name, explains the threshold.

## 4. Read the mask and cause summary

Open **P51 masks and causal classification**.

**Expected observation:** each row is a different mask even though calibration
started from the same nominal homogeneous Pfa. Every disagreement cell has one
entry in `results.disagreement_causes`; every non-target crossing is assigned
to clutter edge, strong-target sidelobes, multiple targets, nonuniform noise,
or residual sample fluctuation.

Do not infer achieved Pfa from these counts. The cells are nonidentically
distributed, target response occupies some non-center cells, and the profile is
too short for a rare-event estimate.

## 5. Sweep 1 — change only clutter contrast

Open **P51 clutter-contrast sweep**. The cases are `[0 6 12 18]` dB. The same
unit background draw, target geometry, sidelobes, ripple, and noise swell are
reused.

**Expected observation:** increasing contrast makes the two side populations
less interchangeable. GO protects against low-side underestimation near the
edge but can mask the weak low-side target; SO preserves the low-side target
but can create more high-side edge crossings. CA and OS occupy different
compromises because one averages all values and the other selects one rank.

Optional one-variable edit: change `clutter_contrast_sweep_db` to
`[0 4 8 12 16]`. Keep every other control unchanged and remain within the
reviewed eight-case ceiling.

## 6. Sweep 2 — change only target density

Open **P51 target-density sweep**. The weak CUT and its paired noise trials stay
fixed while the number of 20 dB reference-cell contaminators changes through
`[0 2 4 6 7 8]`.

**Expected observation:** CA loses detection probability as high powers enter
the arithmetic mean. GO and SO differ according to whether both halves are
contaminated. Rank-18 OS can leave six sufficiently high samples above its
selected statistic; the seventh enters the rank boundary and its advantage
collapses. Capacity is count- and rank-dependent, not unlimited robustness.

Optional one-variable edit: change `sweep_interferer_excess_power_db` from 20
to 12 dB. Do not change the count sweep. Finite contaminants may then perturb
several ranks instead of behaving as perfectly separated high outliers.

## 7. Intentionally broken case and Recovery

Open **P51 broken common multiplier and recovery**.

The red curve is intentionally broken: it reuses CA alpha for all statistics
and falsely labels them equal-Pfa. The green curve recalibrates each selector.

**Expected observation:** only CA retains `10^-3` under the shared multiplier.
GO and OS become too conservative while SO becomes too permissive. The
**Recovery** is statistic-specific calibration before any scene comparison;
changing the legend or normalizing plotted counts cannot repair the error.

## Cancellation, clean rerun, and rollback

If a local run must be cancelled, press `Ctrl+C`. The script has no worker,
timer, file, network, or persistent learner-state side effect. Close partial
P51 figures if desired and **Rerun from the top**; the private stream recreates
the same scene and paired trials. A partial MATLAB cancellation was not
validated in repository CI.

Repository rollback is separate: remove only P51-created artifacts and catalog
text, then restore only P51's manifest status to `scaffolded`. Do not roll back
P50 or assume anything about P52's future status.

## Completion prompt

Give a two- or three-sentence teach-back answering the guiding question. Name
one scene where GO is preferable, one where SO or OS is preferable, and explain
both choices using the training-cell contents and calibration—not detector
labels alone.
