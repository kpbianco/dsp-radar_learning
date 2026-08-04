# P50: Apply 2-D CFAR to a Range-Doppler Map

**Phase 5: Detection and CFAR**  
**Status:** Implemented by governed batch `P50`

## Guiding question

How does local thresholding extend from one range profile to two dimensions?

## Experiment

Start from a compact, seeded square-law range-Doppler map with the same row
(range) and column (signed Doppler) convention established in Project 42.
Slide an explicit rectangular 2-D CA-CFAR stencil over every cell whose full
window fits. The stencil excludes a guarded rectangle around the cell under
test (CUT), averages the remaining training powers, scales that estimate for a
requested homogeneous false-alarm probability, and compares the CUT with the
local threshold.

## Procedure

1. Inspect the range-Doppler power map, its range-varying background, the
   zero-Doppler clutter ridge, three interior targets, and one deliberately
   untestable edge target.
2. Read the visible training/guard/CUT stencil and verify its training-cell
   count.
3. Inspect the local noise estimate, threshold surface, normalized CUT ratio,
   and detection overlay.
4. Change only the range training half-width, then only the Doppler training
   half-width. Compare estimator error, target decisions, and the shrinking
   eligible region.
5. Run the intentionally broken zero-padding case, which treats missing
   boundary references as zero and falsely labels every border cell as
   calibrated. Recover by requiring the complete stencil.

## What this teaches

Two-dimensional CFAR is the same local comparison learned in P45, but its
neighborhood now spans range and Doppler. The range and Doppler widths control
different physical neighborhoods. Target mainlobes and sidelobes require guard
space, and map boundaries are not testable under a full rectangular stencil.

## Completion condition

You can identify all three testable target CUTs, explain why the edge target
has no baseline decision, count the training cells from the two rectangles,
and predict which border grows when only one window dimension is enlarged.

## Dependencies and boundaries

- [P42](../42-create-a-full-range-doppler-map/) establishes the range-row,
  signed-Doppler-column map and window-spread interpretation.
- [P45](../45-implement-1-d-cell-averaging-cfar/) establishes square-law
  CA-CFAR estimation, guard cells, and finite-training calibration.
- [P46](../46-vary-cfar-guard-and-training-cells/) establishes guard/training
  geometry tradeoffs.
- [P49](../49-use-ordered-statistic-cfar-with-interfering-targets/) is the
  direct implemented prerequisite and contrasts a robust order statistic with
  the CA mean used here.
- P51 owns deliberate clutter-edge, sidelobe, and multiple-target stress
  testing; P52 owns rare-event validation of achieved `Pfa`.

The experiment uses base MATLAB, a private deterministic random stream,
bounded arrays and loops, and no external files, network, workers, timers, or
hardware. Its compact post-processing map is self-contained; it does not load
P42 workspace state or claim an operational radar data product.

## Run

```matlab
cd modules/50-apply-2-d-cfar-to-a-range-doppler-map
experiment
```

Run the script section by section with [walkthrough.md](walkthrough.md), then
use [checks.md](checks.md) for the observation and teach-back gate.

## Files

- `README.md` — learning contract and dependencies
- `experiment.m` — seeded range-Doppler map and explicit 2-D CA-CFAR
- `lesson.md` — physical model, equations, limits, and interpretation
- `walkthrough.md` — baseline, two one-variable sweeps, broken case, recovery
- `checks.md` — observation, prediction, interpretation, and teach-back checks
