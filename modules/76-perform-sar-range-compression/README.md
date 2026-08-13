# P76: Perform SAR Range Compression

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Implemented by governed batch `P76`

## Guiding question

What information is created before azimuth focusing begins?

## Experiment

A monostatic 5 GHz radar visits 401 positions on an 80 m straight aperture. At
each position it transmits the same complex-baseband LFM pulse, receives the
integer-delayed echoes of three stationary point targets, and retains their
two-way carrier phase. The deterministic base-MATLAB script then applies an
explicit conjugate time-reversed matched filter independently along every
fast-time row.

The baseline compares one raw look with its compressed range profile, then
displays raw and range-compressed aperture-versus-range matrices. One sweep
changes only chirp bandwidth; a second changes only the range spacing of an
equal-amplitude target pair. The intentionally broken path takes magnitude
before later coherent processing: range ridges remain, but aperture phase is
lost. Recovery uses the unchanged complex compressed matrix.

## Learning goal

Explain that range compression creates a **complex range-compressed phase
history**: targets become localized in slant range, while the complex value
along each ridge preserves the aperture-dependent phase needed for later
cross-range focusing. It is not yet a SAR image because the aperture looks
have not been coherently combined.

## Prerequisites and dependencies

- P18 supplies complex-I/Q and phase-preservation intuition.
- P30 supplies the monostatic `R = c*tau/2` convention.
- P32 supplies explicit LFM matched-filter and bandwidth-resolution intuition.
- P37 supplies fast-time/slow-time matrix orientation.
- P75 is the governed curriculum prerequisite and supplies SAR phase history.
- Runtime target: base MATLAB R2016b or newer; no optional toolbox is used.

P77 will coherently focus the preserved aperture phase with backprojection.
P78 owns range-cell migration correction, and P79 owns SAR resolution and
windowing tradeoffs. P76 deliberately stops before azimuth focusing.

## Run

```matlab
cd modules/76-perform-sar-range-compression
run('experiment.m')
```

Then use `walkthrough.md` one observation at a time and `checks.md` for the
completion conversation. The script is a bounded synthetic learning model,
not an operational SAR processor or hardware/field validation. Its immutable
working-storage ceiling is 12,000,000 eight-byte value equivalents, and it
creates exactly six tagged figure groups.

## Files

- `experiment.m` — seeded point-target echo simulation, explicit row-wise
  matched filtering, two physical sweeps, magnitude-only failure, recovery,
  metrics, assertions, and resource bounds
- `lesson.md` — physical model, equations, limiting cases, and interpretation
  traps
- `walkthrough.md` — baseline observations, controlled changes, broken case,
  recovery, cancellation, rollback, and concept connection
- `checks.md` — answered observation/prediction checks and teach-back rubric

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Keep the guiding question exactly:
"What information is created before azimuth focusing begins?" Begin with one
raw LFM echo row and its compressed profile. Then inspect the aperture-range
matrix one processing stage at a time, vary bandwidth and target range spacing
one variable at a time, discard complex phase as the deliberate failure, and
recover from the unchanged complex matrix. Keep range compression distinct
from azimuth focusing and teach physical meaning rather than MATLAB syntax.
