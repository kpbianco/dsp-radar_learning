# P77: Focus SAR with Backprojection

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Implemented by governed batch `P77`

## Guiding question

How does compensating the correct path length focus a point in an image?

## Experiment

A monostatic radar visits 121 known positions on a 30 m straight track. The
seeded synthetic input is already range-compressed: every aperture row contains
localized complex point-target responses whose phase follows the two-way slant
range. The script forms a 2-D ground image by explicitly doing three operations
for every pixel and aperture position:

1. predict that pixel's slant range;
2. linearly sample the complex range-compressed row at that range;
3. compensate `+4*pi*R/lambda` and add the looks coherently.

The baseline shows input geometry and phase history, partial images as 21, 61,
and 121 aperture positions accumulate, the final focused image, and point-target
range and cross-range cuts. A second one-variable sweep adds 0 mm, 5 mm, and
10 mm of sinusoidal assumed path error across the aperture. The `10 mm` case
is deliberately broken. The already-formed baseline supplies the zero-error
sweep case, while recovery deliberately reruns correct-geometry backprojection
on the unchanged complex measurement. Cumulative pixel-look accounting keeps
all executed image formation inside the reviewed operation ceiling.

## Learning goal

Explain that backprojection is a path-matched coherent sum. At a correct pixel,
the sampled range responses contain the target and the predicted phase cancels
its measured phase, so aperture looks add. At a wrong pixel or under a
non-rigid path model, residual phase rotates and the sum spreads or cancels.

## Prerequisites and dependencies

- P18 supplies complex-I/Q and phase-preservation intuition.
- P30 supplies monostatic `R = c*tau/2` ranging.
- P32 supplies range-compression response intuition.
- P37 supplies the fast-time/slow-time matrix orientation.
- P61-P63 supply coherent spatial steering intuition.
- P75 supplies SAR phase history, and governed P76 supplies the
  range-compressed complex matrix used here.
- Runtime target: base MATLAB R2016b or newer; no optional toolbox is used.

P78 will isolate range-cell migration, P79 will compare aperture and window
resolution, and P80 will treat motion error and autofocus. P77 follows the
hypothesized slant range during backprojection but does not claim those later
studies.

## Run

```matlab
cd modules/77-focus-sar-with-backprojection
run('experiment.m')
```

Then use `walkthrough.md` one processing transition at a time and `checks.md`
for the completion conversation. This is a bounded synthetic learning model,
not an operational SAR processor or hardware/field validation.

## Files

- `experiment.m` — deterministic phase-history synthesis, explicit
  backprojection, two physical sweeps, path-error failure, recovery, metrics,
  assertions, and resource bounds
- `lesson.md` — physical model, equations, limiting cases, and interpretation
  traps
- `walkthrough.md` — baseline observations, controlled changes, failure,
  recovery, cancellation, rollback, and concept connection
- `checks.md` — answered observation/prediction checks and teach-back rubric

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Keep the guiding question exactly:
"How does compensating the correct path length focus a point in an image?"
Begin with the range-compressed complex phase history. Inspect one processing
transition at a time, accumulate 21, 61, then 121 aperture positions, examine
range and cross-range cuts, and vary only the assumed path error. Make the
10 mm non-rigid path case fail, then recover from the unchanged complex input
with correct geometry. Teach physical meaning rather than MATLAB syntax, and do
not describe static checks as MATLAB runtime evidence.
