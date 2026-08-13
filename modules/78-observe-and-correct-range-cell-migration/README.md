# P78: Observe and Correct Range-Cell Migration

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Implemented by governed batch `P78`

## Guiding question

Why does a target move through range bins during a long synthetic aperture?

## Experiment

A stationary point target sits at `(60 m, 1000 m)` while a monostatic radar
crosses a 400 m straight track. Its exact slant range
`R(x_p) = sqrt((x_p-x_t)^2+y_t^2)` changes by about 33.25 m: 66.5 stored
`0.5 m` bins, or 16.6 physical `2 m` range-resolution cells. The seeded
range-compressed complex matrix therefore contains a curved ridge.

The script makes the range-cell migration correction visible. For each
aperture row it linearly samples the original matrix at
`r + (R(x_p)-R_ref)`, which aligns the target at one reference range. A
fixed-bin coherent profile and image use the same complex data and the same
two-way phase compensation, so their loss is caused only by ignoring the
changing range sample. Path-following interpolation concentrates the energy.

Two controlled sweeps vary only aperture length and only target squint offset.
The intentionally broken case reverses the interpolation sign, nearly doubling
the ridge motion. Recovery freshly reapplies the correct sign to the unchanged
complex input.

## Learning goal

Explain that the target is not moving across the ground image. Platform motion
changes its round-trip delay, so its localized range response crosses stored
range bins during the aperture. Phase compensation cannot recover samples that
a fixed range bin never captured; range interpolation must follow the curved
path before the coherent aperture sum can concentrate the target.

## Prerequisites and dependencies

- P18 supplies complex-I/Q and phase-preservation intuition.
- P30 supplies monostatic `R = c*tau/2` ranging.
- P32 and P76 supply range-compressed response and fast-time/slow-time matrix
  intuition.
- P37 supplies the range-column/aperture-row orientation.
- P75 supplies exact SAR slant-range history.
- Governed P77 supplies explicit path-following backprojection; P78 isolates
  why its range interpolation is necessary.
- Runtime target: base MATLAB R2016b or newer; no optional toolbox is used.

P79 will separately compare SAR resolution, aperture length, and windowing.
P80 will treat unknown motion error and autofocus. P78 assumes known geometry
and does not claim either later topic.

## Run

```matlab
cd modules/78-observe-and-correct-range-cell-migration
run('experiment.m')
```

Then follow `walkthrough.md` one transition at a time and use `checks.md` for
the completion conversation. This is a bounded deterministic synthetic model,
not an operational SAR processor or hardware/field result.

## Files

- `experiment.m` — deterministic curved range history, explicit correction,
  two one-variable sweeps, fixed-bin comparison, wrong-sign failure,
  same-data recovery, metrics, assertions, and resource bounds
- `lesson.md` — physical model, equations, limiting cases, and interpretation
  traps
- `walkthrough.md` — baseline observations, controlled changes, failure,
  recovery, cancellation, rollback, and concept connection
- `checks.md` — answered observation/prediction checks and teach-back rubric

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Keep the guiding question exactly:
"Why does a target move through range bins during a long synthetic aperture?"
Begin with the stationary target and its exact changing slant range. Inspect the
uncorrected range-compressed ridge, then the explicit linear interpolation that
aligns it. Compare fixed-bin and path-following processing using identical
complex data and identical phase compensation. Vary only aperture length, then
only squint offset. Make the wrong interpolation sign double the migration and
recover from the byte-for-byte unchanged complex input. Distinguish stored
sampling bins from physical range-resolution cells, teach physical meaning
rather than MATLAB syntax, and never describe static checks as MATLAB runtime
evidence.
