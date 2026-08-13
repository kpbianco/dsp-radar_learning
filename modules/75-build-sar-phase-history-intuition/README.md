# P75: Build SAR Phase-History Intuition

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Implemented by governed batch `P75`

## Guiding question

Why does moving one antenna create a large synthetic aperture?

## Experiment

A monostatic radar visits 401 uniformly spaced positions on an 80 m straight
track and observes one stationary point target. The deterministic base-MATLAB
script computes slant range, two-way delay, the round-trip carrier phase, and a
complex fast-time return explicitly. The rows of that return are separate
antenna positions: motion has turned one physical antenna into a coherent
sequence of spatial samples.

The baseline exposes geometry, range, phase curvature, and the raw
fast-time/aperture matrix. One controlled sweep moves only the target's
cross-range coordinate; a second changes only aperture length. An intentionally
broken path discards I/Q phase, then compares it with recovery from the
unchanged complex record using an explicit hypothesized-path coherent sum.

## Learning goal

Explain that the synthetic aperture is created by preserving the phase of many
looks from known platform positions—not merely by moving the antenna. Relate a
target's cross-range coordinate to the location of its phase-history vertex,
and relate a longer aperture to a larger observed range change and phase span.
Aperture length reveals more of the curved history; it does not change the
target geometry's local curvature at closest approach.

## Prerequisites and dependencies

- P18 supplies complex-I/Q and phase-preservation intuition.
- P30 supplies the monostatic `R = c*tau/2` delay convention.
- P36 connects two-way path change to coherent pulse-to-pulse phase.
- P61-P63 connect spatial phase samples, aperture, and coherent steering.
- P74 is the governed curriculum prerequisite.
- Runtime target: base MATLAB R2016b or newer; no optional toolbox is used.

P76 will add range compression, P77 will form a SAR image with backprojection,
and P78 will isolate range-cell migration. This module deliberately stops at
one point target and one transparent cross-range coherent sum.

## Run

```matlab
cd modules/75-build-sar-phase-history-intuition
run('experiment.m')
```

Then use `walkthrough.md` one observation at a time and `checks.md` for the
completion conversation. The script is a bounded synthetic learning model, not
an operational SAR design or hardware/field validation.

## Files

- `experiment.m` — deterministic point-target model, raw phase history, two
  physical sweeps, magnitude-only failure, same-data recovery, and bounds
- `lesson.md` — physical model, equations, limits, and interpretation traps
- `walkthrough.md` — baseline observations, controlled changes, failure,
  recovery, cancellation, rollback, and concept connection
- `checks.md` — answered observation/prediction checks and teach-back rubric

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Keep the guiding question exactly:
"Why does moving one antenna create a large synthetic aperture?" Begin with one
antenna visiting known positions and the two-way path-length phase model.
Inspect one baseline plot at a time, change target cross-range and aperture
length one variable at a time, make the magnitude-only failure explicit, and
finish with a short teach-back. Do not turn the lesson into MATLAB syntax
instruction or describe static checks as MATLAB runtime evidence.
