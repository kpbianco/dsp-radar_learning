# P50 lesson: Apply 2-D CFAR to a Range-Doppler Map

Guiding question: **How does local thresholding extend from one range profile
to two dimensions?**

## Start with the physical window

Project 42 made a matrix whose rows are range and whose columns are signed
Doppler. Project 45 slid a guarded stencil along one range profile. Put those
ideas together: center a rectangular stencil on one range-Doppler cell under
test (CUT), reserve a smaller rectangle around it as guards, and use every cell
in the surrounding rectangular annulus as local background evidence.

Range and Doppler are not interchangeable labels. A range guard protects
against matched-filter spread across neighboring delays. A Doppler guard
protects against finite-CPI mainlobe spread across neighboring velocity bins.
The annulus corners are valid training cells because this lesson implements a
full rectangular 2-D neighborhood, not two crossed 1-D stencils.

The script begins at P42's square-law output stage. It creates a compact
self-contained map with the same row/column convention, a range-dependent
background, a zero-Doppler clutter ridge, seeded complex Gaussian background,
and finite 2-D target responses. It does not depend on a saved P42 workspace.

## The explicit 2-D CA-CFAR operation

Let `Tr` and `Gr` be the training and guard half-widths in range. Let `Td` and
`Gd` be their Doppler counterparts. The outer half-widths are

`Hr = Tr + Gr`, and `Hd = Td + Gd`.

The outer rectangle contains

`(2*Hr + 1)*(2*Hd + 1)`

cells. The guarded rectangle, including the CUT, contains

`(2*Gr + 1)*(2*Gd + 1)`.

Therefore the number of training cells is

`N = (2*Hr + 1)*(2*Hd + 1) - (2*Gr + 1)*(2*Gd + 1)`.

For the baseline `(Tr,Gr,Td,Gd)=(6,2,4,2)`, the outer rectangle is 17 by 13,
the guarded rectangle is 5 by 5, and `N=196`. For each eligible CUT `(r,d)`,
the script indexes that annulus explicitly and averages **linear square-law
power**:

`p_hat[r,d] = sum(training powers)/N`.

Under independent identically distributed exponential CUT and training
powers, the CA scale for requested false-alarm probability `Pfa` is

`alpha = N*(Pfa^(-1/N) - 1)`.

The local threshold and strict decision are

`threshold[r,d] = alpha*p_hat[r,d]`,

`detect[r,d] = power[r,d] > threshold[r,d]`.

The code converts power with `10*log10` only for display. Averaging dB values
would estimate a geometric mean and would invalidate this calibration.

## What the baseline figures show

Figure 1 separates the known mean used to synthesize the background from the
one noisy square-law realization. The background grows with range and rises
near zero velocity, so one global native-unit threshold is not appropriate.
Three circle-marked target centers lie inside the testable region. A fourth
square-marked target lies near the lower-left map border.

Figure 2 makes the algorithm inspectable. Training cells surround the complete
guard+CUT rectangle; nothing about target truth enters this stencil.

Figure 3 shows the training-power estimate, threshold surface, and the ratio
of CUT power to threshold. A crossing has positive ratio in dB. The white
detection markers are cell decisions, while black crosses are truth used only
for reporting. Grouping neighboring crossings into one target report belongs
to P53, not this lesson.

The finite target response extends nine cells in each dimension. Most of its
mainlobe lies inside the two-bin guards, while small modeled sidelobe tails
reach the training annulus. That is deliberate: a guard must account for the
actual processed response, and finite tails can bias a CA estimate. P51 later
turns that effect into a dedicated stress test.

## Sweep 1: range width changes a range neighborhood

The range sweep changes only `Tr = [3 6 12]`. The Doppler training and both
guard widths stay fixed. Increasing `Tr` adds training rows, typically reduces
finite-sample roughness, and reaches farther through range-dependent
background. It also removes more rows from the testable top and bottom of the
map because a complete stencil needs more range support.

This is a variance/locality/coverage tradeoff, not a guarantee that every
realized false-alarm count decreases monotonically. The plot reports the
realized counts without turning one map into a rare-event `Pfa` validation.

## Sweep 2: Doppler width changes a velocity neighborhood

The Doppler sweep changes only `Td = [2 4 8]`. Range geometry remains fixed.
Increasing `Td` adds training columns and shrinks the eligible left/right
velocity border. It also mixes more of the zero-Doppler ridge with off-ridge
cells. A wide Doppler window can therefore have more samples yet be less local
to the CUT's velocity-dependent background.

The two sweeps cannot be replaced by one generic “window size” knob: they
touch different physical axes and exclude different borders.

## Intentionally broken border policy and recovery

The baseline assigns `NaN` thresholds and false decisions where the full
stencil does not fit. `NaN` means **no calibrated test**, not zero power, a
missed target, or an implementation crash.

The broken case pads the map with zeros, applies the full `N` and `alpha`, and
pretends the missing training cells were real zero-power measurements. Near a
boundary, that biases the estimated background and threshold downward. The
edge target then produces a tempting finite “detection,” but that comparison
does not satisfy the homogeneous full-window model.

Recovery does not reinterpret that result. It restores the complete-stencil
eligibility mask, returns the border threshold to `NaN`, and requires the
interior thresholds and decisions to match the baseline exactly. A different
edge policy—wrapping Doppler, clipping and recalibrating, or asymmetric
training—would be a new detector with its own model and validation.

## Assumptions and limiting cases

- The nominal `Pfa` equation assumes independent exponential square-law
  powers with a common local mean. Windowed/matched-filtered P42 cells can be
  correlated, and the synthetic background is not perfectly homogeneous, so
  `Pfa=1e-3` is a design setting here, not an achieved-rate claim. P52 owns
  Monte Carlo validation.
- With `Tr=Td=0`, there is no surrounding training annulus in this geometry;
  no CA estimate exists. This implementation rejects zero training widths.
- As `N` grows in a homogeneous scene, the CA estimate becomes less variable
  and `alpha` approaches `-log(Pfa)`. A larger stencil is not automatically
  better in a nonstationary scene because locality is lost.
- If guards are smaller than the processed target response, target energy
  enters training cells and raises its own threshold. More guard cells protect
  more spread but consume map coverage.
- If the map has fewer than `2*Hr+1` rows or `2*Hd+1` columns, no full-stencil
  CUT exists. The control checks reject such geometry before allocation.
- Doppler columns are not wrapped. The negative and positive velocity display
  edges are excluded just like range edges.
- Detections are individual cells. This module does not estimate `Pd`, group
  cells, track targets, or claim measured-clutter robustness.

## Common interpretation mistakes

1. “The border target was missed.” It received no baseline test; a no-decision
   is different from a below-threshold decision.
2. “A 2-D stencil is a range stencil plus a Doppler stencil.” The rectangular
   annulus includes its corners; two crossed averages are a different model.
3. “The threshold is in dB, so average the dB map.” The detector averages
   linear power and converts only the displayed result.
4. “More training cells always improve CFAR.” More cells reduce sampling
   variation only while remaining representative of the CUT background.
5. “Every white marker is a target.” A requested nonzero false-alarm rate and
   a spread target can both produce extra crossing cells.
6. “Truth markers make the threshold.” Truth masks are used only after the
   decisions to report target CUTs and exclude target support from the
   illustrative non-target count.

## Dependencies and claim boundary

P42 supplies the map semantics, P45 the 1-D square-law CA equation, P46 the
guard/training tradeoff, and direct prerequisite P49 the contrast between an
arithmetic mean and a robust order statistic. This script exposes the 2-D
indices, mask, arithmetic mean, scale factor, boundary policy, and strict
comparison using base MATLAB; no CFAR toolbox object hides the operation.

Static tests and independent mathematical oracles can check these contracts.
They are not MATLAB runtime, hardware/HIL, real-time, field, operational radar,
or educational-effectiveness evidence.
