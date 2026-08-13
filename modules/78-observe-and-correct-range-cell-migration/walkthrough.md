# Walkthrough: watch the delay curve, then follow it

Use one figure or processing transition at a time. The target is stationary.
The guiding question is: **Why does a target move through range bins during a long synthetic aperture?**

## Before running

Open `experiment.m` and find the visible baseline controls. The 400 m aperture,
`0.5 m` stored range spacing, `2 m` compressed-response resolution, and target
at `(60 m,1000 m)` are the important physical controls. The script uses seed
`7801`, base MATLAB only, finite foreground loops, and immutable operation and
storage ceilings.

One prediction only: should a fixed ground target remain in one slant-range
column while the radar crosses a long track?

Run:

```matlab
run('experiment.m')
```

## Transition 1: geometry becomes a curved range ridge

Inspect Figure 1. In the upper panel the target does not move. In the lower
panel its exact square-root slant range overlays the bright range-compressed
ridge. Read the printed migration in three units:

- about `33.25 m` of physical slant range;
- about `66.5` stored `0.5 m` range bins;
- about `16.6` physical `2 m` resolution cells.

Observation question: where is the platform when range stops decreasing and
starts increasing?

Expected observation: closest approach occurs near the target's `60 m`
cross-range coordinate. The slope is zero there, but the full-aperture range
span is not zero.

## Transition 2: explicitly align each aperture row

Inspect Figure 2. The left matrix is unchanged input. The right matrix uses

```text
requested input range = output range + (R_p-R_ref).
```

The code exposes the fractional index, left sample, and linear weight. No
`interp1`, circular shift, SAR toolbox, or hidden resampler performs the main
operation. The corrected ridge should occupy no more than about `1 m`, rather
than the original `33 m` span.

Do not say the target was moved to its true ground coordinate. This step only
changes the range sampling coordinate so all looks refer to one range.

## Transition 3: same phase correction, different range sampling

Inspect Figure 3. Both curves use the identical retained complex matrix and
the identical `+4*pi*R/lambda` phase compensation. The fixed-bin profile sums
the same range columns. The corrected profile first follows the curved ridge.

Expected baseline metrics are a corrected/fixed coherent peak gain greater
than `3` and a power-concentration gain greater than `1.4`. The exact printed
values include the seeded noise realization. This comparison isolates range
sampling: it is not “uncorrected phase versus corrected phase.”

## Sweep 1: change only aperture length

In Figure 4, left panel, compare `100`, `200`, and `400 m`. Target position,
range sampling, carrier, and platform spacing remain fixed.

Expected migration spans are approximately:

| Aperture | Range span | Stored 0.5 m bins |
| ---: | ---: | ---: |
| 100 m | 5.98 m | 12.0 |
| 200 m | 12.72 m | 25.4 |
| 400 m | 33.25 m | 66.5 |

The mechanism is geometric: a longer aperture includes more extreme slant
ranges. Do not attribute the change to added noise or different bandwidth.

## Sweep 2: change only squint offset

In Figure 4, right panel, compare target along-track offsets `0`, `60`, and
`80 m` while the 400 m track remains fixed.

Expected migration spans are approximately `19.80`, `33.25`, and `38.46 m`.
Broadside is symmetric. Increasing squint makes the center-referenced curve
more asymmetric and increases the reviewed span. The target remains stationary
in every case.

## Transition 4: fixed-bin smear versus corrected image

Inspect Figure 5. Every image pixel gets the same hypothesized two-way phase
compensation in both panels. The left processor repeatedly samples only the
pixel's center-look range. The right processor samples each aperture row at
that pixel's changing predicted slant range.

The corrected peak should land within one image-grid step of `(60 m,1000 m)`.
The fixed-bin true-pixel voltage should be less than `40%` of the corrected
value, and corrected peak-power concentration should improve by more than a
factor of `1.8`. This satisfies the completion condition: following migration
concentrates energy that the fixed-bin assumption smears.

## Broken case: reverse the interpolation sign

Inspect Figure 6. The broken mapping requests

```text
output range - (R_p-R_ref)
```

instead of the correct plus sign. The ridge span should exceed `1.8` times the
uncorrected span because the relative motion is approximately doubled. This is
not an edge-padding artifact: preflight retains range support around the raw
and wrong-sign paths.

## Recovery from unchanged complex data

Recovery does not shift the broken output back. The script freshly applies the
correct plus-sign interpolation to the byte-for-byte retained complex range
history. It asserts exact equality with the original correct matrix and
coherent profile, and it accounts for the recovery call in both predicted and
executed operation totals.

If you manually change a control and trigger an assertion, restore the visible
controls and rerun from the top. Seeded input and local-function isolation make
the baseline deterministic.

## Cancellation, timeout, and resource behavior

All work is finite and foreground-only. There is no worker, timer, callback,
file write, or background task. Press `Ctrl+C` to cancel a long local run; then
close any partial P78 figures and rerun from the top. Cancellation may leave
partial variables or figures in the current MATLAB session, but it cannot
modify the retained source or learner state. The repository test harness uses
bounded subprocess timeouts for CLI checks; no MATLAB timeout or cancellation
was exercised unless retained runtime evidence explicitly says so.

The reviewed ceilings cover `2001` aperture samples, `251` range samples,
`1500` image pixels, five cases per sweep, `800,000` private generator values,
`1,200,000` interpolation operations, `4,000,000` image operations,
`5,200,000` total operations, `12,000,000` eight-byte live-value equivalents,
and six tagged figure groups.

## Rollback and isolation

Batch rollback removes only P78 implementation artifacts and restores P78's
manifest status to `scaffolded`; it does not edit P77, future modules, managed
contracts, or personal `.learning/` progress. The experiment itself has no
external write, so recovery means rerunning from immutable inputs rather than
restoring a data file.

## Concept connection and completion handoff

- P76 created a range-compressed matrix whose aperture rows remain separate.
- P77 followed pixel-dependent slant range during backprojection.
- P78 isolates why a long or squinted aperture makes that path following
  necessary.
- P79 will distinguish aperture/window resolution effects from migration.
- P80 will address imperfect rather than known geometry.

Before completion, answer the teach-back in `checks.md`: distinguish a stored
range bin from a physical resolution cell, explain why phase compensation alone
cannot repair fixed-bin loss, and describe why the wrong sign doubles the
motion.
