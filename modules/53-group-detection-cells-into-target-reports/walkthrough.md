# Walkthrough: watch cells become reports

Run `experiment.m` from the module directory. Work through one figure at a
time. The script is stateless: it does not read or write files or learner
progress.

## Baseline observation

Before Figure 1, make one prediction: will the number of tracker-ready reports
be closer to the number of threshold cells or to the number of physical
targets?

Figure 1 shows the normalized detector score. The dashed contour is `score=1`;
everything inside it is a threshold crossing. White crosses mark the two known
target centers. Notice the extended target footprints, an asymmetric shoulder,
small disconnected sidelobe blobs, and isolated false cells.

Figure 2 exposes three processing transitions:

1. Count raw threshold cells. One physical response covers several cells.
2. Inspect local maxima. Adjacent duplicates fall, but nuisance maxima remain.
3. Inspect explicit 8-connected labels and the accepted report count.

Pause here. Explain why local-maximum selection alone cannot tell a mainlobe
from a disconnected sidelobe or false cell.

Figure 3 overlays white truth crosses and red grouped centroids. Read the
console range error in metres and velocity error in metres per second. Compare
those sub-cell estimates with the discrete peak locations stored in each
report. Also inspect cell count, integrated excess strength, extent, and the
shape uncertainty proxy. Do not call that proxy tracker covariance.

Expected baseline observations:

- many threshold cells become a smaller set of local maxima;
- one- and two-cell nuisance components receive labels but fail the three-cell
  report policy;
- the two extended physical targets each produce one accepted report;
- the broken peak-only count is larger than the recovered grouped count; and
- each reviewed centroid stays within one range bin and one velocity bin of its
  known target.

## Sweep 1: change only minimum component size

Figure 4 was generated with:

```matlab
minimum_component_cell_sweep = [1 3 18];
```

Everything else, including the score map and centroid exponent, stays fixed.
At one cell, isolated false detections are accepted as reports. At three cells,
small nuisance blobs disappear while both target components remain. At 18, the
weaker compact target is rejected while the broader strong target remains.

Try `[1 2 3 18]` if you want to expose the two-cell sidelobe transition. Keep the
vector increasing, include the baseline value `3`, and remain within the fixed
five-case bound.

Physical connection: minimum component size is a spatial persistence rule. It
trades false-report rejection against sensitivity to small target footprints.

## Sweep 2: change only centroid weighting

Figure 5 was generated with:

```matlab
centroid_weight_exponent_sweep = [0 1 2];
```

The mask, component labels, and minimum size stay fixed. At `p=0`, all detected
cells contribute equally. At `p=1`, excess power pulls the report toward the
strong response. At `p=2`, the strongest cells dominate. Target 1 has an
intentional asymmetric shoulder, so increasing `p` need not monotonically
reduce both coordinate errors.

Physical connection: weighting chooses which part of an extended response is
treated as most representative. It changes the measurement without changing
which cells crossed threshold.

## Broken case: local maxima are reports

Figure 6 deliberately skips connected-component grouping, minimum-size
filtering, and centroiding. Every local maximum becomes a report at its cell
center. This path is broken even though peak selection itself is correct:

- isolated false cells and sidelobes still become reports;
- an extended or multi-peaked response can emit more than one report;
- position remains quantized to bin centers; and
- strength, extent, and shape information are absent.

Do not “repair” the plot by hiding unwanted markers or relabeling them. The
recovery is the right panel: restore 8-connected grouping, enforce the declared
minimum component size, and calculate weighted reports from all component
cells.

## Failure interpretation and limiting cases

If two physical targets touch above threshold, 8-connectivity can merge them.
That is a model limit, not a loop failure. Lowering the threshold can make
merging more likely; raising it can split one weak target. A future splitter may
use multiple peaks within a component, but it must be explicit and evaluated.

If a known target loses its accepted report after your edit, inspect in order:

1. Did the target center still cross normalized score one?
2. Did the minimum component size exceed the target footprint?
3. Did a changed scene move truth outside the reviewed axes?
4. Did the component merge with another target?

If an input guard fires, restore finite real spacings, increasing row-vector
sweeps, the fixed seed, and the resource ceilings. Do not increase a ceiling to
silence a malformed or runaway edit.

## Cancellation and deterministic recovery

Press Ctrl+C to cancel a run. Close partial P53 figures if desired, restore the
reviewed controls, and rerun from the top. The script closes only figures tagged
`P53`, recreates its private random stream, preallocates bounded component
queues, and has no persistent or external state. A clean rerun therefore
recovers the deterministic scene. This is a documented recovery path; it is
not evidence that MATLAB cancellation or a MATLAB runtime timeout was executed
in CI. Repository CLI subprocess tests use a 10-second timeout to prevent a hung
fixture from blocking validation.

## Concept connection

P50 and P52 establish which cells cross and whether that detector is calibrated.
P53 turns spatially related cells into measurements. P54 can now consume one
range/velocity report per target, while P57 later handles general association.

Finish by answering: which three assumptions—connectivity, minimum size, and
centroid weighting—most directly determine whether several cells become the
right physical report?
