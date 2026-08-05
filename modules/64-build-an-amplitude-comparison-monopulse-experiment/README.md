# P64: Build an Amplitude-Comparison Monopulse Experiment

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Implemented by batch `P64`

## Guiding question

How can sum and difference beams estimate small angle error around boresight?

## Experiment

Form two fixed ULA receive beams squinted to either side of boresight. Align
their boresight phases, combine their complex voltages into sum (`Sigma`) and
difference (`Delta`) channels, and use the signed real part of `Delta/Sigma` as
a local angle-error measurement. A seeded target and receiver-noise record make
the single-snapshot and coherently averaged estimates repeatable.

## Procedure

Run one deterministic baseline and then change one physical control at a time:

1. inspect the overlapping left/right beams and the sum, difference, and
   normalized `Delta/Sigma` patterns;
2. follow a `+2 deg` target from array samples to noisy channel ratios and an
   angle estimate;
3. sweep beam squint while holding the array and angle grid fixed;
4. sweep receiver SNR on one unchanged target geometry; and
5. apply a right-channel gain mismatch, observe its false boresight error, then
   recover by applying the known inverse calibration to the unchanged data.

No phased-array toolbox call hides steering, coherent summation, the channel
hybrid, or ratio-to-angle interpolation.

## What this should teach

Monopulse turns simultaneous relative channel response into a local angle-error
estimate. The difference channel changes sign at boresight, while the sum
channel supplies the reference and warns when the ratio is unsafe. The method
is local: outside the calibrated monotonic interval, the same ratio need not
identify a unique angle.

## Completion condition

The normalized ratio is monotonic over the reviewed `+/-4 deg` calibration
sector, the deterministic baseline estimates the `+2 deg` target, and you can
explain why a right-channel gain error creates a visible boresight bias.

## Run the lesson

```bash
./bin/learn start 64
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P61 supplies the broadside-referenced ULA phase convention, P62 supplies beam
pattern and aperture intuition, and P63 supplies explicit conjugate receive
steering. P67 will generalize the single gain mismatch into broader array
calibration and mutual-coupling errors.

The experiment uses base MATLAB arithmetic and script-local functions, so it
requires MATLAB R2016b or newer and no optional toolbox. Elements, snapshots,
angle samples, sweep cases, private deterministic samples, working arrays, and
figures have immutable ceilings. It writes no file and starts no network,
timer, worker, or external process.

This is a narrowband, far-field, complex-baseband ULA model with synchronized,
isotropic elements and one stationary coherent target. It omits element
patterns, coupling, multipath, near-field curvature, broadband squint,
automatic calibration estimation, target scintillation, detection, and
tracking. Static checks and an independent Python oracle do not constitute
MATLAB runtime, rendered-figure, antenna, hardware/HIL, real-time, field, or
operational-radar validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build an Amplitude-Comparison Monopulse Experiment". The guiding question is: "How can sum and difference beams estimate small angle error around boresight?" Use this experiment: Construct overlapping left/right or sum/difference beam patterns and simulate a target near boresight. Have me perform these actions: Plot sum, difference, and normalized difference/sum ratio versus angle. Add amplitude noise and calibration mismatch, then estimate angle from the ratio. The main concept I must learn is: Monopulse converts a single snapshot of relative channel response into a local angle-error estimate. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
