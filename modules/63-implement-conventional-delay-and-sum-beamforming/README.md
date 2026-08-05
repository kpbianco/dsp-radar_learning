# P63: Implement Conventional Delay-and-Sum Beamforming

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Implemented by batch `P63`

## Guiding question

How does steering align one direction and misalign others?

## Experiment

Simulate two narrowband sources plus independent sensor noise on a uniform
linear array (ULA). Form every scan weight explicitly, apply `w(theta)^H X`,
and compare direct snapshot averaging with the covariance expression
`w(theta)^H Rhat w(theta)`. Five tagged figures expose the received sensor
data, phase alignment, resolution, data-quality tradeoffs, and a broken
steering-sign convention.

## Procedure

Run one deterministic baseline, then change one physical control at a time:

1. compare a single-snapshot scan with a 128-snapshot covariance average;
2. sweep source separation at fixed array, SNR, and snapshot count;
3. sweep array size for one fixed two-source scene;
4. sweep SNR and snapshot count independently; and
5. reverse the steering-vector phase sign, observe mirrored peaks, then recover
   with the Hermitian delay-and-sum convention on the unchanged data.

No phased-array toolbox call hides the coherent sum or covariance quadratic
form.

## What this should teach

Conventional beamforming aligns the spatial phase expected from one direction
before adding sensor channels. A matched direction adds coherently; a
mismatched direction winds around the complex plane and partially cancels.
Array aperture controls angular resolution, while SNR and independent snapshot
averaging control how reliably the fixed beam pattern is estimated.

## Completion condition

The scan peaks near both source angles when aperture and SNR suffice, and you
can explain why more snapshots stabilize the scan without narrowing the
physical beam.

## Run the lesson

```bash
./bin/learn start 63
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P61 supplies the broadside-referenced ULA phase convention. P62 supplies the
array-factor, beamwidth, sidelobe, aperture, and spatial-alias concepts that
the received-data scan now uses. P65 will compare this fixed conventional
beamformer with adaptive MVDR weights, P66 will introduce MUSIC, and P67 will
disturb the ideal channel calibration assumed here.

The experiment uses base MATLAB arithmetic and script-local functions, so it
requires MATLAB R2016b or newer and no optional toolbox. Scan angles, elements,
sources, snapshots, sweep cases, private deterministic samples, working arrays,
and figures have immutable ceilings. It writes no file and starts no network,
timer, worker, or external process.

This is a complex-baseband, narrowband, far-field model with synchronized,
calibrated, isotropic sensors and independent source snapshots. Phase steering
is not true-time-delay broadband steering; wideband signals may squint. The
model omits coupling, calibration error, multipath, element pattern, near-field
curvature, and operational detection logic. Static checks and an independent
Python oracle do not constitute MATLAB runtime, rendered-figure, antenna,
hardware/HIL, real-time, field, or operational-radar validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Implement Conventional Delay-and-Sum Beamforming". The guiding question is: "How does steering align one direction and misalign others?" Use this experiment: Simulate two narrowband sources plus sensor noise on a ULA and scan conventional beamformer power versus angle. Have me perform these actions: Change source separation, SNR, snapshot count, and array size. Compare a single snapshot with covariance averaging. The main concept I must learn is: Beamforming coherently sums the desired spatial phase pattern while partially canceling mismatched directions. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
