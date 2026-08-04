# P53: Group Detection Cells into Target Reports

**Phase 6: Radar Tracking and Data Association**  
**Status:** Implemented by batch `P53`

## Guiding question

How do several threshold-crossing cells become one physical detection?

## Experiment

Create a seeded range-Doppler detector-score map with two extended target
responses, asymmetric energy, disconnected sidelobes, and isolated false
detections. Observe the transition from threshold cells to deterministic local
maxima, explicit 8-connected components, and one weighted target report per
accepted component.

The report carries range, signed radial velocity, peak and integrated strength,
cell count, range/velocity extent, and an uncalibrated shape-derived uncertainty
proxy. It is deliberately richer than one binary detector cell, but it is not
yet a track.

## Procedure

1. Inspect the normalized score and raw threshold mask.
2. Select one local maximum per equal-valued plateau with a row-major tie rule.
3. Group threshold cells using a visible base-MATLAB 8-neighbor traversal.
4. Reject components smaller than the chosen minimum and compute centroids with
   weights `w = (score - 1)^p`.
5. Compare each known target's component report with its true range and velocity.
6. Sweep minimum component size and centroid exponent one variable at a time.
7. Break the processor by promoting every local maximum directly to a report,
   then recover grouping, filtering, and centroiding.

## What this should teach

A detector marks cells, while a tracker needs one measurement with position,
strength, extent, and uncertainty per target. Connectivity and filtering encode
assumptions: they can reject isolated nuisance cells, but touching target blobs
can also merge. The reported shape spread is a useful diagnostic, not a
calibrated tracker measurement covariance.

## Dependencies and compatibility

- P42 supplies the range-row and signed-velocity-column mental model.
- P50 supplies 2-D threshold-cell semantics.
- P52 is the direct implemented prerequisite and supplies honest detector-model
  validation; grouping cannot repair a miscalibrated detector.
- `experiment.m` uses base MATLAB only. Local maxima, connected components,
  filtering, centroids, extents, and uncertainty proxies are explicit. No Image
  Processing Toolbox or tracking toolbox object is required.
- The reviewed scene is bounded to 4,680 cells, a 20,000-cell queue ceiling,
  three cases per sweep, and six tagged figures. It performs no file, network,
  shell, timer, worker, or learner-state operation.

## Completion condition

One physical target produces one stable report rather than many neighboring
reports. You can explain why the broken peak-only path over-reports, how minimum
component size trades nuisance rejection against weak-target loss, and why
excess-power weighting can reduce or introduce centroid bias.

## Start

```bash
./bin/learn start 53
```

Run `experiment.m`, then use `walkthrough.md` one transition at a time and
finish with the short teach-back in `checks.md`.
