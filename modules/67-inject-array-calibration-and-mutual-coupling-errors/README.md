# P67: Inject Array Calibration and Mutual-Coupling Errors

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Implemented by batch `P67`

## Guiding question

How sensitive are beamforming and DOA results to imperfect channels?

## Experiment

Drive the same deterministic two-source record through an ideal ten-element
half-wavelength ULA and a physical array with seeded per-element gain, phase,
and position errors plus a reciprocal nearest- and next-nearest-neighbor
coupling matrix. Compare conventional Bartlett, loaded MVDR/Capon, and MUSIC
outputs when every processor still assumes the ideal steering vectors.

Use an independent known-source pilot to estimate one composite complex
response per channel, apply the resulting diagonal equalizer to the operational
record, and compare the physical beam response, output SINR, and DOA peaks
before and after calibration.

## Procedure

Run one deterministic baseline and then change one cause at a time:

1. inspect the random gain, phase, position, and coupling errors;
2. compare ideal, impaired, and calibrated Bartlett, Capon, and MUSIC scans;
3. scale one fixed gain/phase/position error realization while coupling stays
   fixed;
4. sweep only mutual-coupling magnitude; and
5. deliberately forget the known pilot's steering phase, observe the apparent
   angle shift, then recover using the correct known-source model on the same
   data.

The covariance, loaded solve, receiver-noise prewhitening, eigenspace
projection, coupling matrix, pilot correlation, and diagonal compensation are
explicit base-MATLAB operations.

## What this should teach

Array algorithms protect and search for an assumed spatial signature, not an
angle in isolation. Imperfect complex channels, displaced elements, and mutual
coupling change that signature. Conventional lobes distort, MUSIC peaks bias,
and an adaptive beamformer can suppress the desired signal because its
distortionless constraint protects the wrong vector.

A known source can estimate the composite response at its direction and
materially restore that source. One source cannot separately identify every
gain, displacement, and entry of the coupling matrix, so a diagonal one-look
calibration is local rather than a universal inverse.

## Completion condition

You can explain why calibration materially restores the known-source angle and
beam response, identify the wrong-reference failure, and explain why residual
off-angle error remains and can grow as direction-dependent coupling becomes
stronger.

## Run the lesson

```bash
./bin/learn start 67
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P61 supplies the positive broadside-referenced ULA steering convention, P62
the physical aperture and pattern measures, P63 the conjugate receive scan,
P65 covariance-loaded MVDR, and P66 the MUSIC signal/noise partition. P68 can
reuse the lesson that adaptive processing is only as trustworthy as its
space-time steering model.

The script uses base MATLAB arithmetic and script-local functions, requiring
MATLAB R2016b or newer and no optional toolbox. Elements, sources, operational
and calibration snapshots, scan samples, sweep cases, private deterministic
values, working arrays, and figures have immutable reviewed ceilings. The
script writes no file and starts no network request, timer, worker, or external
process.

This is a narrowband, far-field, stationary complex-baseband model with
isotropic elements. Its simple reciprocal banded coupling matrix is
illustrative rather than an electromagnetic model. Receiver noise is injected
after the modeled array-error matrix; calibration therefore scales and colors
that receiver noise. The analytical output-SINR metric accounts for it, and
calibrated MUSIC whitens both covariance and nominal dictionary before the
signal/noise eigenspace split.
Static checks and a deterministic Python oracle do not constitute MATLAB
runtime, rendered-figure, antenna, bench, hardware/HIL, real-time, field, or
operational-radar validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Inject Array Calibration and Mutual-Coupling Errors". The guiding question is: "How sensitive are beamforming and DOA results to imperfect channels?" Use this experiment: Apply random per-element gain/phase errors, element position errors, and a simple coupling matrix to simulated array data. Have me perform these actions: Compare conventional, MVDR, and MUSIC outputs before and after error. Estimate calibration using a known source and compensate the channel errors. The main concept I must learn is: Array algorithms depend on the steering-vector model; small channel errors can bias angles, raise sidelobes, and destroy adaptive nulls. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
