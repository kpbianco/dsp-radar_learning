# P80: Inject SAR Motion Error and Apply Autofocus

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Implemented by governed batch `P80`

## Guiding question

How small a platform-position error is enough to blur a coherent image?

## Experiment

The experiment builds three deterministic, range-separated point-target phase
histories for a `10 GHz` monostatic SAR. It then multiplies every range gate by
the same aperture-varying two-way phase screen produced by a line-of-sight
platform error. The nominal focuser knows the planned track but not that error,
so coherent peaks spread and fall.

A transparent phase-gradient autofocus estimate comes from the strongest
isolated range gate: nominal target phase is removed, adjacent complex phase
differences are measured, integrated, and applied to every gate. The script
sweeps path-error RMS from zero through `lambda/4`, then holds RMS at
`lambda/8` while changing the error from smooth to short-correlated. A broken
case contaminates the autofocus gate with a comparable scatterer; recovery
returns to the unchanged measured phase history and the isolated gate.

## Learning goal

Connect millimetres of one-way line-of-sight position error to radians of
two-way phase error, recognize that aperture-varying phase causes defocus, and
explain both why a shared phase estimate can restore coherence and why scene
structure can make that estimate fail.

## Prerequisites and dependencies

- P18 supplies complex I/Q phase.
- P30 and P36 establish two-way delay and coherent phase progression.
- P61-P63 establish spatial steering and coherent aperture sums.
- P75 supplies the SAR phase-history model.
- P76 supplies range-separated complex histories.
- P77 supplies explicit path-compensated focusing.
- P78 supplies migration correction before azimuth focus.
- P79 supplies the resolution/aperture trade that motion error now degrades.
- Runtime target: base MATLAB R2016b or newer; no toolbox is used.

The common phase-screen approximation is local and range independent. It is
appropriate for this concept experiment, not a full navigation-error,
wide-scene, or space-variant autofocus model.

## Run

```matlab
cd modules/80-inject-sar-motion-error-and-apply-autofocus
run('experiment.m')
```

Then follow `walkthrough.md` one transition at a time and use `checks.md` for
the completion conversation. The script writes no files and performs no
network, timer, worker, GPU, or external-process operation.

## Files

- `experiment.m` — seeded phase history, explicit focus and phase-gradient
  correction, two sweeps, contaminated-gate failure, recovery, assertions,
  plots, and resource bounds
- `lesson.md` — physical model, equations, observability limits, and common
  interpretation mistakes
- `walkthrough.md` — baseline, one-variable sweeps, failure, recovery, and
  completion handoff
- `checks.md` — answered observation/prediction checks and teach-back rubric

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Keep the guiding question exactly:
"How small a platform-position error is enough to blur a coherent image?"
Begin with the ideal focused point scene, relate one-way path error to two-way
phase using `Delta phi = -4 pi Delta R/lambda`, and inspect the `lambda/8`
blurred result. Show the explicit coherent focus and adjacent-pulse
phase-gradient estimate before discussing autofocus by name. Sweep error RMS,
then change smooth/random error composition at fixed RMS. Deliberately
contaminate the autofocus range gate and recover from the unchanged phase
history using an isolated strong scatterer. Distinguish blur from shift,
navigation correction from autofocus, and simulated/static evidence from
MATLAB runtime evidence. Teach physical meaning rather than MATLAB syntax.
