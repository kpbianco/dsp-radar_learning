# P57: Gate and Associate Detections by Nearest Neighbor

**Phase 6: Radar Tracking and Data Association**  
**Status:** Implemented by batch `P57`

## Guiding question

Which measurement should update which track?

## Experiment

Predict three two-dimensional constant-velocity tracks into one radar scan.
Place one noisy report near each target and mix those reports with three clutter
detections. One track has a long, narrow uncertainty ellipse so its physically
correct report is farther away in Euclidean metres than a nearby clutter point.

## Procedure

Propagate every state and covariance, form each measurement residual and
innovation covariance, compute all squared Mahalanobis distances, apply a
two-dimensional gate, and greedily assign the nearest remaining valid pair.
Visualize the residual geometry, distance matrix, gates, and one-to-one links.
Sweep gate threshold and predicted-covariance scale on the same detections,
then deliberately replace uncertainty-aware gating with ungated Euclidean
nearest neighbor before restoring the reviewed method.

## What this should teach

Association should account for predicted uncertainty, not only Euclidean
distance. A gate rejects reports that are implausible for a particular track,
and one-to-one assignment prevents one detection from updating two tracks.

## Dependencies and compatibility

- P56 is the direct implemented prerequisite: it supplies predicted state,
  predicted covariance, measurement residual, and innovation covariance. P57
  uses the linear Cartesian position-report case so the association operation
  remains visible.
- P53 explains how detection cells become reports; P55 supplies the explicit
  constant-velocity covariance prediction. P58 owns track lifecycle logic, and
  P59 owns crossing-target identity failures.
- `experiment.m` uses base MATLAB only. A small explicit private
  Park-Miller/Box-Muller generator makes the seeded Gaussian report record
  cross-language reproducible. The script explicitly computes `F`, `G`, `Q`,
  `H`, `S`, every residual, every matrix-solved squared Mahalanobis distance,
  the gate mask, and the one-to-one greedy selection. No tracking object,
  assignment solver, explicit inverse, file, network, worker, timer, or global
  random stream is used.
- The reviewed run is bounded to three tracks, six detections, three cases in
  each sweep, six tagged figures, nine association passes, 162 track-report
  pair slots, and 73 points per gate ellipse. Sweep validation allows at most
  five cases, while the reviewed arrays are exact. Script-local functions
  require MATLAB R2016b or later.

## Completion condition

The three true reports are assigned to their three tracks, clutter outside the
nominal gates is rejected, and you can explain why the elongated track accepts
its along-ellipse report while rejecting the closer cross-ellipse clutter.

## Start

```bash
./bin/learn start 57
```

Run `experiment.m`, follow `walkthrough.md` one figure at a time, and finish
with the teach-back in `checks.md`.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Gate and Associate Detections by Nearest Neighbor". The guiding question is: "Which measurement should update which track?" Use this experiment: Create two or more tracks with clutter detections and noisy target reports. Have me perform these actions: Predict all tracks, compute measurement residuals and Mahalanobis distances, apply gates, then assign nearest valid measurements. Visualize gates and assignments. The main concept I must learn is: Association should account for predicted uncertainty, not only Euclidean distance; gating prevents implausible updates. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
