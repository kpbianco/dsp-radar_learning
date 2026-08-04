# Walkthrough: vary one part of the CFAR stencil at a time

## Before running

Open `experiment.m` and note the visible controls: seed 4601, 256 cells at
15 m per cell, requested `Pfa = 1e-3`, baseline `T=12`, baseline `G=4`, guard
cases `[0 4 10]`, and training cases `[4 12 36]`. The largest reviewed stencil
is bounded before any random array is allocated.

Run the full script once. It creates five figure groups tagged `P46` and leaves
a compact `results` structure in the workspace.

## 1. Observe the seeded scene

In figure 1, first inspect the known mean background. It changes gradually,
with its steepest rise near the marked transition. Then inspect the observed
square-law profile. The random cell-to-cell variation is not the background
trend; it is one noisy realization around that trend.

Zoom mentally around the strong target. Its explicit sampled sinc response
occupies several range cells and has sidelobes. The compact weaker target is
farther away. The response extent is why guard cells have a physical role.

Concrete observation: identify the approximate distance in metres from the
strong target center to the last sidelobe you would not want in a background
estimate.

## 2. Read the baseline stencil and threshold

Figure 2 marks the baseline leading training cells, guards, CUT, lagging guards,
and lagging training cells around the strong target. The second panel overlays
the observed profile, baseline threshold, detections, and excluded edge CUTs.

Inspect `results.baseline_strong_target_margin`. A margin above one means the
CUT exceeds threshold. Also inspect `results.baseline_window_span_m` and
`results.baseline_excluded_edge_count`: protection and averaging consume real
range extent and edge coverage.

## 3. Sweep guard cells only

Figure 3 holds `T=12`, the profile, and requested `Pfa` fixed while `G` takes
the values 0, 4, and 10 per side. Follow each threshold near the strong target,
then compare the target-cell decision margin in the lower panel.

Expected observation: with zero guards, the target's own nearby response enters
the training mean and the strong CUT self-masks. Four guards restore a useful
margin. Ten guards move references farther beyond the sidelobes, but expand the
stencil and excluded edges. A higher margin here does not prove ten is best in
a changing background.

One-variable edit: change `guard_cell_sweep` to `[0 2 4 6 10]`, keeping its
order, bounds, and baseline value. Re-run and find the smallest guard count that
protects this response. Restore `[0 4 10]` afterward so later checks match the
reviewed baseline.

## 4. Sweep training cells only

Figure 4 holds `G=6`, the background-only seeded profile, and requested `Pfa`
fixed while `T` takes 4, 12, and 36 per side. The upper panel shows the local
background estimates. The lower panel separates observed roughness in a quiet
region from deterministic locality error near the clutter transition.

Expected observation: four cells per side react strongly to individual noise
samples. Thirty-six per side give a smoother estimate, but the wide stencil
smears the known transition and has the largest deterministic locality error.
The displayed span makes the cost tangible: `(2T+2G+1)*15 m`.

One-variable edit: change `training_cell_sweep` to `[4 8 12 24 36]`, leaving
all other controls fixed. Look for a knee where roughness has fallen but the
transition error and span have not yet become excessive. Restore the original
vector when finished.

## 5. Break the homogeneous-reference assumption

Figure 5 adds one strong neighboring return at cell 126. For the weaker target
CUT at cell 138, that neighbor lies exactly 12 cells away: inside the nominal
`G=4, T=12` leading training set. The nominal threshold rises above the weaker
CUT, so the desired target is masked.

The recovery uses `G=12`, which moves that known contaminator into the excluded
guard region, and recomputes both reference sums from the contaminated input.
The recovered threshold falls and the weaker CUT is detected again. Inspect
`results.broken_reference_contains_contaminator` and
`results.recovery_reference_excludes_contaminator`; both geometry checks must
tell the expected story.

Interpretation: widening guards is a valid recovery only when the necessary
extent is known and the more distant references remain representative. This
large moat is evidence that ordinary CA-CFAR geometry is strained, not a rule
to use 12 guards everywhere.

## Cancellation, rerun, and recovery

If you press Ctrl+C, no external or learner state needs rollback: the script
does not write files or call services. Rerun from the top. It clears partial
variables, closes only figures tagged `P46`, creates a fresh private stream,
and reconstructs the same scene. The recovery section does not reuse nominal
threshold arrays; it rebuilds reference indices and estimates from
`contaminated_profile_power`.

## Completion handoff

Use `checks.md`. You are ready for the short teach-back when you can justify a
guard size from response extent, explain the variance/locality tradeoff for
training cells, and recognize a contaminated reference set from its threshold
shape rather than calling the miss “low SNR” alone.
