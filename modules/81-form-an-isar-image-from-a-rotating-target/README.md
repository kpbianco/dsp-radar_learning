# P81: Form an ISAR Image from a Rotating Target

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Implemented by governed batch `P81`

## Guiding question

How does target rotation create synthetic aperture when the radar is stationary?

## Experiment

The experiment keeps a `10 GHz` monostatic radar fixed while ten seeded point
scatterers on a rigid target rotate through `6 deg`. A transparent
stepped-frequency echo model records complex phase versus frequency and aspect.
An explicit IFFT range-compresses every look. Known centroid translation is
then removed with the frequency-dependent two-way phase that aligns both the
range envelope and carrier phase, and an angle-domain FFT maps rotational phase
slope into cross-range.

The first sweep changes only angular aperture from `2 deg` through `8 deg`.
The second holds the same `6 deg` aspect samples and changes rotation rate,
showing that correct angle-domain focus is invariant while CPI and Doppler in
hertz change. The intentionally broken case omits translational alignment, so
the recognizable point layout smears. Recovery returns to the unchanged raw
complex history, aligns it, and freshly forms the original image.

## Learning goal

Explain how target-induced aspect diversity replaces platform motion, why
angular aperture controls cross-range resolution, why rotation rate controls
the time/Doppler scale rather than angular resolution when aspect support is
fixed, and why coherent translation compensation must precede ISAR focus.

## Prerequisites and dependencies

- P18 supplies complex I/Q and signed phase.
- P30 and P36 connect two-way delay, range, and coherent phase progression.
- P61-P63 connect phase slope to spatial steering and coherent sums.
- P75-P79 supply phase history, range compression, focusing, migration, and
  aperture-resolution context.
- P80 supplies the coherence and motion-error warning that ISAR now applies to
  target motion.
- Runtime target: base MATLAB R2016b or newer; no toolbox or external data is
  used.

The target is rigid, scatterers are isotropic and constant, aspect span is
small, rotation rate and centroid translation are known, and the stepped
frequencies are coherent. This is a range-versus-cross-range concept image,
not a calibrated shape, RCS, or operational target-recognition product.

## Run

```matlab
cd modules/81-form-an-isar-image-from-a-rotating-target
run('experiment.m')
```

Then follow `walkthrough.md` one transition at a time and use `checks.md` for
the completion conversation. The script writes no files and performs no
network, timer, worker, GPU, or external-process operation.

## Files

- `experiment.m` — deterministic stepped-frequency history, explicit range
  compression/alignment/angle focus, two sweeps, broken case, recovery,
  assertions, plots, and resource bounds
- `lesson.md` — physical model, scale equations, limiting cases, dependencies,
  and interpretation traps
- `walkthrough.md` — baseline, controlled sweeps, failure, recovery, and
  completion handoff
- `checks.md` — answered observation/prediction checks and teach-back rubric

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Keep the guiding question exactly:
"How does target rotation create synthetic aperture when the radar is
stationary?" Begin with the rigid scatterer layout and raw range profiles.
Show the explicit stepped-frequency echo, IFFT range compression, full
frequency-dependent translation correction, and angle-domain FFT before using
the word ISAR as a label. Change aperture angle while holding the look count
fixed. Then change rotation rate while holding the aspect samples fixed, and
separate CPI/Doppler-hertz effects from angular resolution. Deliberately omit
translation compensation and recover by reprocessing the unchanged complex
history. Distinguish small-angle cross-range from literal Cartesian truth,
range migration from phase coherence, and static/simulated evidence from
MATLAB runtime evidence. Teach physical meaning rather than MATLAB syntax.
