# P70 walkthrough: Read the Matrix in Two Directions

## Guiding question

How do fast-time beat frequency and chirp-to-chirp phase separate range and velocity?

Run `experiment.m` once without editing it. The script is finite and
foreground-only. It creates seven figures tagged `P70` and `p70_results`.

## Baseline: identify the two clocks

Open **P70 dechirped fast-time by chirp matrix**. Read its axes before its
colors. Rows advance through the `40 us` fast-time record; columns advance
through `64` chirps separated by `50 us`.

Expected observation: one column is a mixture of fast oscillations rather than
three visible range spikes. Repetition across columns is coherent but not
identical because moving targets change phase between chirps.

Now open **P70 fast-time range FFT**. The upper panel should show range
neighborhoods near `20` and `23 m`, not three distinct peaks. Targets 1 and 2
share the same beat frequency because they share range. The lower image retains
all chirp columns after the row transform.

Common mistake: interpreting the lower panel as a finished range-Doppler map.
Its horizontal coordinate is still chirp index, not velocity.

## Processing transition: preserve phase, then transform columns

Open **P70 slow-time phase and Doppler**. In the upper panel, the two targets at
`20 m` have opposite unwrapped phase slopes. In the lower panel, those slopes
become peaks at equal-magnitude negative and positive velocity.

Open **P70 FMCW range-Doppler map** and match the three white truth circles:

- targets 1 and 2 share `20 m` but occupy opposite velocity bins;
- targets 2 and 3 share positive velocity but occupy `20` and `23 m`; and
- all three become distinct only after both transforms.

Expected baseline metrics are `1 m` range-bin spacing and about `0.609 m/s`
velocity-bin spacing. The bin-centered target velocities are about `-1.826`,
`+1.826`, and `+1.826 m/s`.

## Sweep 1: change only coherent chirp count

Open **P70 coherent chirp-count sweep**. The cases reuse the first `16`, `32`,
and `64` chirps from the unchanged shared-range trace.

Expected observations:

- CPI duration grows from `0.8` to `3.2 ms`;
- velocity spacing shrinks from about `2.435` to `0.609 m/s`; and
- the negative/positive pair becomes easier to distinguish.

Try changing only the first case from `16` to `8` chirps. Predict twice the
`16`-chirp velocity spacing and poorer separation. The validation accepts `8`
as the minimum reviewed case. Restore `16` afterward.

Common mistake: crediting a smoother plot or zero padding. Each case actually
contains a different number of coherent measurements.

## Sweep 2: change only retained fast-time sample count

Open **P70 retained sample-count sweep**. These cases use the first `128`,
`256`, and `512` rows of the same deterministic matrix. Sample rate and chirp
slope remain fixed.

Expected observations:

- observed sweep bandwidth grows from `37.5` to `150 MHz`;
- range spacing shrinks from `4` to `1 m`; and
- the positive-velocity targets at `20` and `23 m` change from a merged broad
  response to separate neighborhoods.

Try changing only the first case to `64` samples. Predict `18.75 MHz` observed
bandwidth and `8 m` range spacing. Restore `128` afterward.

Common mistake: saying the ADC sampled faster. `sample_rate_hz` never changes;
the longer cases retain more measured fast-time duration.

## Broken case: throw away slow-time phase

Open **P70 broken phase loss and recovery**. The left map was formed after
replacing every complex range sample by its magnitude. Range structure remains,
but the isolated moving target near `23 m` collapses near zero velocity. At the
shared range, magnitude beating can make symmetric ghost structure; it cannot
recover the original velocity signs.

Explain the failure in physical terms: velocity was stored as chirp-to-chirp
phase direction. `abs` erased that direction before the column FFT.

## Recovery on unchanged complex data

The right map restores the complex `range_data`, the same Hann weights, and the
dimension-2 FFT. Confirm:

- `p70_results.broken_velocity_sign_preserved` is false;
- `p70_results.recovered_velocity_sign_preserved` is true;
- `p70_results.recovery_error` is at roundoff scale; and
- measured target coordinates again match the retained truth arrays.

No target, noise sample, window, or axis was regenerated for the recovery. That
isolation shows phase loss was the cause.

## Cancellation, rerun recovery, and rollback

Press `Ctrl+C` between figure sections if needed. There is no worker, timer,
network request, file write, or external process continuing in the background.
An interruption can leave partial `P70` figures and intermediate workspace
arrays, but no background or external persistent state. Rerun from the top to
close only figures tagged `P70`, clear and rebuild `p70_results`, regenerate
the private noise stream, and recover the exact deterministic baseline.
Unrelated figures and variables are not broadly cleared.

Repository rollback is file-local: remove the P70 learning artifacts and
focused evidence/catalog changes, then restore only P70's manifest status to
`scaffolded`. Preserve P69, later module identities, ignored `.learning/`
progress, and the operator-managed active-batch contracts.

## Concept connection

Complete this sentence aloud:

> A tone along fast time estimates ___, while phase rate along chirps estimates
> signed ___; more measured fast-time samples observe more ___, while more
> coherent chirps extend the ___.

The intended answer is range, velocity, swept bandwidth, and CPI. The next
lesson asks what happens when motion also shifts the within-chirp beat.
