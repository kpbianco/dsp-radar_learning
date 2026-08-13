# P77 Walkthrough: Follow the Path, Then Add

## Guiding question

How does compensating the correct path length focus a point in an image?

Run `experiment.m` from this module directory. Keep the Command Window metrics
visible and inspect one figure or processing transition at a time.

## 1. Start from range-compressed complex data

Open **P77 input geometry and range-compressed phase history**.

The top panel shows one antenna visiting 121 known positions and two stationary
point targets. The middle panel is magnitude versus slant range and platform
position. Each target is already localized in range, but this is not a focused
ground image. The bottom panel compares one interpolated complex ridge phase
with its expected `-4*pi*(R-R_ref)/lambda` curve.

Expected observation: the ridge bends slightly in range and rotates many times
in phase. The phase coherence should exceed `0.99`; P76 preserved exactly the
information that P77 needs.

Concrete observation question: which axis is platform position, and why is it
not yet a target cross-range coordinate?

## 2. Sweep 1: accumulate aperture positions only

Open **P77 partial-aperture accumulation**. The images use the centered `21`,
`61`, and `121` looks. Carrier, target scene, range response, noise realization,
grid, and path model remain fixed.

Expected observation: both targets appear at stable coordinates while their
cross-range responses narrow as the coherent aperture grows. The printed
target-1 full `-3 dB` cross-range widths should decrease monotonically. The
unnormalized true-pixel voltage should grow with look count, while displayed
images are divided by count for a shape comparison.

Prediction before rerun: if you retained 91 centered looks, should the target-1
cross-range width fall between the 61- and 121-look cases?

Restore the reviewed look-count list before continuing.

## 3. Inspect the full focused image

Open **P77 correctly focused backprojection image**.

The white crosses are truth coordinates; they are not used to choose the image
peaks. Each target is searched in its own local window. The printed coordinate
errors must remain within one image-grid step in both dimensions.

At every pixel, the imager predicted slant range, linearly sampled the complex
range row, multiplied by positive two-way phase compensation, and added the
looks. A correct pixel succeeds in both range and phase. A wrong pixel usually
misses the ridge, fails phase alignment, or both.

## 4. Inspect point-target range and cross-range cuts

Open **P77 focused point-target response cuts**.

The upper cut holds target-1 cross-range fixed and varies ground range. The
lower cut holds its ground range fixed and varies cross-range. Read the printed
full `-3 dB` widths in metres.

Expected observation: range focusing is governed mainly by the existing
range-compressed response. Cross-range focus is created by coherent aperture
path matching. A bright peak alone is not enough evidence; location and both
cuts make the response interpretable.

## 5. Sweep 2: change only the assumed path

Open **P77 assumed-path-error sweep**. The complex measurement is unchanged.
Only a sinusoidal range-direction error in the imager's assumed platform path
changes through `0`, `5`, and `10 mm`.

The full-aperture baseline already supplies the `0 mm` image. The script forms
new images for `5 mm` and `10 mm`, then later performs a fresh correct-path
backprojection for recovery. This avoids duplicate zero-error work while still
testing recovery as processing rather than as an alias of the baseline array.

Expected observation: the true-pixel normalized coherent gain decreases from
near `1` toward roughly `0.75` and then below `0.35`. The `10 mm` image spreads
and its strongest response can shift because its residual phase varies across
the aperture.

Do not generalize this into "every geometry error blurs." A constant path error
can be only a global phase, and a constant wrong height can map to a biased
ground-range coordinate in this flat 2-D geometry. Aperture-varying residual
path is what guarantees the deliberate defocus here.

## 6. Broken path and same-data recovery

Open **P77 broken path and same-data recovery**.

The top panel shows residual phase at the target-1 pixel for the `10 mm` wrong
path. The terms no longer align around one complex direction. The lower panel
compares cross-range cuts from broken processing and recovered correct
processing.

Recovery uses the retained complex phase history without changing one sample.
It restores the zero-error geometry and must reproduce the baseline image
exactly. If acquisition had discarded phase, or if only the blurred magnitude
image remained, this recovery would not be possible.

## 7. Connect the processing chain

- P32 formed a narrow range response with a matched filter.
- P37 made the matrix dimensions explicit.
- P75 connected known antenna motion to phase history.
- P76 localized each aperture look in range while preserving complex phase.
- P77 samples those ranges, compensates their paths, and sums them into pixels.
- P78 will isolate range-cell migration; P79 will treat aperture/window
  resolution; P80 will treat motion error and autofocus.

The compact answer is: **the correct pixel predicts both where each echo lies
in range and how its phase rotated; compensation makes those complex looks add
instead of cancel.**

## Cancellation, rerun, recovery, and rollback

The script has finite loops, cumulative accounting for all 4,451,590 reviewed
pixel-look operations, immutable operation and storage ceilings, six tagged
figure groups, no worker, no timer, no callback, no background task, and no
file/network write. Press Ctrl+C to cancel the foreground run. Close partial P77
figures and rerun from the top; the private seed reproduces the same noise
without changing MATLAB's global random stream.

If a visible control fails validation, restore the reviewed values and rerun
from the top. Repository rollback is batch-local: restore P77's scaffold
README, remove its four implementation artifacts, focused test, and evidence,
change only P77 manifest status back to `scaffolded`, and restore P77's public
catalog lines. Preserve P76, later module identities/statuses, operator-managed
contracts, and personal `.learning/` state.

## Completion handoff

Use `checks.md`. Give a two- or three-sentence teach-back that mentions
hypothesized slant range, two-way phase compensation, coherent summation, and
why an aperture-varying path error defocuses the point.
