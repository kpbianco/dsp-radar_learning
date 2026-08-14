# P84: Run the End-to-End Radar Processing Capstone

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Implemented by governed batch `P84`

## Guiding question

Can I trace a target from waveform generation through detection and tracking without treating any stage as a black box?

## Experiment

Simulate a configurable radar scene with waveform, targets, clutter, noise,
receiver imperfections, matched filtering, range-Doppler processing, CFAR,
clustering, and tracking.

The runnable script exposes these eight transformations:

1. generate a unit-energy complex LFM pulse from its phase law;
2. convolve it with stationary and moving target reflectivity, a seeded clutter
   edge, a deterministic receiver spur, and complex noise;
3. add and explicitly invert DC leakage and a conjugate I/Q image;
4. compress every pulse with a conjugate time-reversed replica;
5. form signed range-Doppler power with a slow-time FFT;
6. compare a quiet-side fixed threshold with linear-power 2-D CA-CFAR;
7. turn 8-connected threshold cells into excess-power-weighted reports; and
8. gate reports into an alpha-beta range tracker that can coast through a miss.

Offline `Pd` scoring uses maximum-cardinality one-to-one truth/report matching,
so an ambiguous report cannot make the metric depend on truth-list order.

## Procedure

Build the chain in explicit stages and save an intermediate plot/data product
after each. Include at least one stationary and one moving target, a clutter
edge, a weak target beside a strong one, missed detections, and false alarms.
Compare at least two waveform or detector choices and summarize performance
using Pd, Pfa, RMSE, resolution, and runtime.

Run `experiment.m` and inspect the stage products in order. The first sweep
changes only the explicit matched-filter taper on one retained receiver record.
The second changes only requested CA-CFAR `Pfa` on one retained range-Doppler
map. The intentionally broken case removes conjugation from the LFM replica;
recovery reprocesses the exact same calibrated samples with the correct
replica. The fixed-threshold comparison is also deliberately applied outside
the homogeneous quiet region where it was calibrated.

## What this should teach

A radar system is a sequence of model-dependent transformations;
understanding intermediate data makes failures diagnosable and design
tradeoffs visible.

The script retains a `provenance` ledger in `p84_results`: every row names a
stage, input, output, and units. Truth is isolated from processing and is used
only to score reports and track error after decisions have been made.

## Completion condition

You can explain every target, artifact, miss, and false alarm by locating the
stage where it was created or lost.

## Dependencies and compatibility

The governed prerequisite is P83. Concept dependencies are
[P32 pulse compression](../32-perform-lfm-pulse-compression/),
[P33 sidelobe control](../33-control-pulse-compression-sidelobes/),
[P37 data-matrix orientation](../37-build-a-pulse-doppler-data-matrix/),
[P41 clutter](../41-model-ground-clutter-and-swerling-targets/),
[P42 range-Doppler processing](../42-create-a-full-range-doppler-map/),
[P50 2-D CFAR](../50-apply-2-d-cfar-to-a-range-doppler-map/),
[P52 empirical Pfa](../52-validate-cfar-pfa-by-monte-carlo/),
[P53 clustering](../53-group-detection-cells-into-target-reports/), and
[P54/P57/P58 tracking lifecycle](../58-implement-track-initiation-confirmation-coasting-and-deletion/).

The script targets base MATLAB R2016b or newer. It uses no toolbox object,
external data, global random stream, file/network I/O, worker, timer, GPU, or
persistent learner state. Shape, map-evaluation, stencil-visit, working-value,
and figure ceilings are checked before large allocation. Emitted reports are
checked against a visible per-scan ceiling before bounded tracker association.

## Start the lesson

```bash
./bin/learn start 84
```

Tutor mode should use `lesson.md`, reveal one stage at a time with
`walkthrough.md`, and finish with the interpretation and teach-back prompts in
`checks.md`.
