# Checks: Group Detection Cells into Target Reports

Use these after observing the baseline, both sweeps, and the broken recovery.

## Observation checks

1. Why is the threshold-cell count larger than the physical-target count?
   - **Correct:** a finite target response spans neighboring range-Doppler cells,
     and sidelobes or noise can cross too.
   - **Incorrect:** every crossing must be a separate target.

2. Why does local-maximum selection reduce reports but not solve the problem?
   - **Correct:** it suppresses neighboring lower cells, but disconnected
     sidelobes and false cells can still be maxima.
   - **Incorrect:** any 3-by-3 maximum is guaranteed to be a physical object.

3. What does the baseline three-cell minimum do?
   - **Correct:** it rejects the seeded one- and two-cell nuisance components.
   - **Incorrect:** it proves those components came from noise.

4. Why can the weighted centroid lie between bin centers?
   - **Correct:** it averages physical axis coordinates using positive
     excess-score weights.
   - **Incorrect:** grouping creates new range-Doppler resolution.

## Prediction checks

1. Predict the effect of changing minimum component size from three to one.
   - **Correct:** more nuisance components become reports; existing component
     centroids do not change because only acceptance changed.
   - **Incorrect:** every target centroid must move.

2. Predict the effect of increasing exponent `p` while keeping the mask fixed.
   - **Correct:** the centroid moves toward stronger excess-score cells; report
     count and component labels stay fixed.
   - **Incorrect:** the threshold mask necessarily gains cells.

3. Predict what 8-connectivity does to two diagonally touching detections.
   - **Correct:** it places them in one component.
   - **Incorrect:** diagonal cells are always separate.

4. Predict what happens when two target blobs touch above threshold.
   - **Correct:** basic connected-component grouping can merge them into one
     report, exposing a limiting case.
   - **Incorrect:** a component label automatically knows there are two targets.

## Interpretation and failure checks

1. The peak-only broken plot contains fewer markers than raw threshold cells.
   Is it now tracker-ready?
   - **Correct:** no. It still promotes nuisance maxima, quantizes position, and
     omits component extent and shape.
   - **Incorrect:** yes, because there is at most one marker per 3-by-3 patch.

2. Is the range/velocity shape uncertainty proxy a tracker covariance matrix?
   - **Correct:** no. It is an uncalibrated morphology summary with a bin-width
     term; repeated truth-referenced errors are needed for covariance.
   - **Incorrect:** yes, any component second moment is measurement covariance.

3. Can grouping repair an incorrectly calibrated CFAR threshold?
   - **Correct:** no. P53 organizes detector outputs; the P52 detector model and
     validation boundary still matter.
   - **Incorrect:** component filtering guarantees the requested false-alarm
     probability.

4. Why does synthetic truth lookup use the target center's component label?
   - **Correct:** it evaluates known components without hiding a general data
     association algorithm, which belongs later in P57.
   - **Incorrect:** it is a production association method.

## Determinism and resource checks

- The script uses private seed `5301`; global random state is not changed.
- Background score is bounded below threshold before targets and nuisance cells
  are added.
- The 72-by-65 scene has 4,680 cells, below the fixed 20,000-cell scene and
  queue ceilings.
- Component cells are labeled when enqueued, so no cell occupies the queue
  twice.
- Each sweep has three cases and all six figures are tagged `P53`.
- No file, network, shell, timer, worker, Image Processing Toolbox, or tracking
  toolbox operation is required.

## Completion checklist

- [ ] I can distinguish a threshold cell, a local maximum, a component, a
  target report, and a track.
- [ ] I can explain the 8-neighbor grouping rule and its touching-target limit.
- [ ] I can predict the nuisance-rejection/weak-target tradeoff of minimum size.
- [ ] I can explain how `w=(score-1)^p` moves a centroid.
- [ ] I can state why the broken peak-only path over-reports.
- [ ] I can describe position, strength, extent, and uncertainty fields without
  calling the shape proxy calibrated covariance.

## Short teach-back rubric

In 60–90 seconds, answer the guiding question: **How do several
threshold-crossing cells become one physical detection?** A complete teach-back
must mention:

1. local maxima as deterministic representatives rather than final truth;
2. 8-connected grouping and minimum-size filtering;
3. excess-power centroiding for one sub-cell position per accepted component;
4. report strength, extent, and the uncalibrated uncertainty proxy; and
5. at least one failure limit, such as a nuisance maximum, a compact target
   filtered out, or touching targets merged.
