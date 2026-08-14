# P83: Compare Range-Doppler Processing with a Small STAP Processor

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Implemented by governed batch `P83`

## Guiding question

When is Doppler filtering alone insufficient against clutter?

## Experiment

A deterministic moving-platform scene produces coupled angle-Doppler ground
clutter in 48 range cells. Each range cell is a transparent 4-element by
8-pulse space-time snapshot. A target at range cell 25 sits close to the
clutter ridge: a fixed spatial beam followed by a Doppler bank leaves it below
strong clutter cells, while a loaded joint space-time covariance solve makes
the target the strongest cell in the adaptive range-Doppler map.

The script varies target distance from the ridge and the number of clean
neighboring training cells. An intentionally broken covariance includes
strong target-like contamination in 25% of the training cells. Recovery
discards that covariance and rebuilds the processor from the unchanged clean
training record.

## Learning goal

Explain why moving-platform clutter couples angle and Doppler, why a fixed beam
and a Doppler filter cannot follow that ridge, how a small STAP weight uses the
joint covariance, and why covariance support, loading, guard cells, and clean
training control whether adaptation rejects clutter or instead raises residual
interference around a mismatched target.

## Prerequisites and dependencies

- P37 and P42 supply pulse-Doppler matrices and range-Doppler map reading.
- P41 supplies distributed ground-clutter intuition.
- P61 and P63 supply ULA phase and fixed beamforming.
- P65 supplies loaded MVDR covariance weighting.
- P68 supplies the introductory angle-Doppler clutter ridge and Kronecker
  space-time steering model.
- P82 is the governed batch prerequisite.
- Runtime target: base MATLAB R2016b or newer; no toolbox, external data,
  parallel worker, GPU, device, network, or file output is used.

This is a narrowband synthetic teaching model. The known covariance is used
only to score simulated component powers; the adaptive weights see the sample
covariance from neighboring range cells. No detection probability, calibrated
radar performance, operational clutter rejection, or hardware behavior is
claimed.

## Run

```matlab
cd modules/83-compare-range-doppler-processing-with-a-small-stap-processor
run('experiment.m')
```

Then follow `walkthrough.md` one transition at a time and use `checks.md` for
the completion conversation. Rerunning closes only figures tagged `P83` and
reconstructs the same private deterministic samples.

## Files

- `experiment.m` — moving-platform clutter, conventional and adaptive maps,
  two sweeps, contamination failure, exact recovery, assertions, plots, and
  resource ceilings
- `lesson.md` — physical model, explicit equations, limits, dependencies, and
  interpretation traps
- `walkthrough.md` — baseline observations, one-variable changes, failure,
  recovery, and concept connection
- `checks.md` — answered observation/prediction checks and teach-back rubric

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Keep the guiding question exactly:
"When is Doppler filtering alone insufficient against clutter?" Begin with the
moving-platform angle-Doppler ridge, then compare one conventional fixed-beam
range-Doppler map with one small joint adaptive map on honest background-relative
scales. Expose the Kronecker steering vector, neighboring-range sample
covariance, diagonal loading, and distortionless solve before naming STAP.
Change target distance from the ridge and clean training support one variable
at a time. Contaminate the training cells deliberately, separate desired-target
response from lost interference rejection, and recover from the unchanged
clean record. Separate map visibility from output SCNR, sample covariance from
the known simulated covariance, and static/simulated evidence from MATLAB
runtime or physical validation.
