# Walkthrough: choose the side by naming the failure

## Before running

Open `experiment.m` and find the visible controls: seed 4801, 240 range cells,
the first high-clutter cell at 121, a 12 dB power step, 12 training cells and 2
guards per side, four target probes, design `Pfa = 1e-3`, and 25,000 paired
sweep trials. Resource estimates and fixed ceilings are checked before random
arrays are allocated.

Run the script once. It creates five figure groups tagged `P48` and leaves a
compact `results` structure in the workspace. The baseline uses background-only
reference estimates so its four target probes cannot contaminate one another;
the second sweep introduces contamination deliberately.

## 1. Observe the baseline profile

Figure 1 overlays received square-law power, GO and SO thresholds, four known
target locations, and the clutter boundary. Far from the boundary, both sides
sample the same background population. Near cell 121, the thresholds separate
because one side begins to see the 12 dB brighter region.

Inspect `results.go_missed_target_cells` and
`results.so_missed_target_cells`. Relate every miss to the two side estimates;
do not explain it by detector name alone. Also compare the false-alarm counts
only on eligible non-target CUTs in `results.edge_zone`.

## 2. Follow leading and lagging estimates through the edge

Figure 2 zooms into the boundary. In the top panel, identify which mean rises
first as the stencil slides toward high clutter. In the bottom panel, connect
GO to `max(left,right)` and SO to `min(left,right)`, including their distinct
calibration factors.

Common mistake: GO does not mean “use the right side,” and SO does not mean
“use the left side.” Reverse the direction of the clutter step and the
geometric roles exchange while `max` and `min` keep the same meaning.

## 3. Sweep clutter contrast only

Figure 3 reuses the same normalized leading, lagging, and high-side CUT draws
while contrast changes through `[0 6 12 18]` dB. The CUT and lagging half are
in high clutter; the leading half remains in low clutter. This pairing makes
the change in contrast, rather than new random data, responsible for the
curve transition.

Expected observation: at zero contrast, both empirical false-alarm rates are
near the common homogeneous design value. As contrast grows, GO stays tied to
the high side while SO's edge false alarms rise dramatically.

One-variable edit: change `clutter_contrast_sweep_db` to `[0 3 6 9 12 18]`.
Keep it increasing, include the 12 dB baseline, and remain within the six-case
and 24 dB bounds. Re-run, inspect the transition, then restore the reviewed
vector.

## 4. Sweep one interfering reference target only

Figure 4 returns to homogeneous background and holds the weak CUT at 13 dB
SNR. One cell in the leading training half receives increasing excess power;
the lagging half remains clean. Every case reuses the same reference and CUT
noise.

Expected observation: GO detection probability falls when the contaminated
side becomes the maximum. SO remains controlled by the clean half and
preserves more weak-target detections. This does not justify SO at a clutter
edge because the smaller mean there may describe the wrong population.

One-variable edit: change `interferer_excess_power_sweep_db` to
`[-20 -10 0 10 20 30]`. Keep it increasing and inside the reviewed bounds.
After observing the smoother transition, restore the original vector.

## 5. Break calibration, recover it, then protect the edge

Figure 5 first applies the ordinary 24-cell CA multiplier to both variants.
The theoretical homogeneous false-alarm bars show the mismatch: GO underspends
the requested `Pfa`, while SO overspends it. Separate fixed-iteration
calibration returns both to `1e-3` before any behavior is compared.

The second panel exposes another broken conclusion: “always use SO because it
saved the weak target.” At the 12 dB high-side edge, SO's false-alarm
probability is much larger. The recovered choice uses GO when edge false-alarm
protection is the requirement. In another application, the protected failure
could justify a different selector.

## Cancellation, rerun, rollback, and recovery

If you press Ctrl+C, the script has no external or learner state to roll back.
It opens no files, workers, timers, network connections, or services. Rerun
from the top: it clears partial variables, closes only figures tagged `P48`,
creates a new private stream, and reconstructs the same scene and paired
trials. Calibration recovery recomputes both multipliers from the requested
homogeneous `Pfa`; it never relabels the broken shared scale as valid.

Repository rollback is separate: remove only the P48 implementation artifacts
and restore only P48's manifest status to `scaffolded`. P47 and P49 identities
must not change.

## Completion handoff

Use `checks.md`. You are ready for the teach-back when you can name the two
side populations for a CUT, explain both the GO edge-protection cost and the SO
one-sided-contamination benefit, and insist on equal homogeneous `Pfa` before
comparing them.
