# P66: Estimate DOA with MUSIC

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Implemented by batch `P66`

## Guiding question

How can subspace methods resolve sources more finely than a conventional beam?

## Experiment

Place two uncorrelated narrowband sources only six degrees apart on a
ten-element half-wavelength ULA. Form the sample covariance and its ordered
eigensystem explicitly, compare a conventional Bartlett scan with the MUSIC
pseudospectrum, and identify which angular peaks are supported by the estimated
noise subspace.

## Procedure

Run one deterministic baseline and then change one cause at a time:

1. sweep source separation while reusing the same waveforms and noise;
2. sweep per-source SNR and observe the signal/noise eigenvalue gap;
3. sweep snapshot count using nested prefixes of one unchanged record;
4. sweep the assumed source count on one unchanged covariance; and
5. make the sources coherent, observe rank collapse, then average overlapping
   subarray covariances to recover two peaks from the same sensor data.

No phased-array toolbox call hides covariance formation, eigenvalue ordering,
the noise-subspace projection, peak selection, or spatial smoothing.

## What this should teach

MUSIC separates estimated signal and noise subspaces. A steering vector at a
true source direction is nearly orthogonal to the noise subspace, so the
reciprocal projection makes a sharp peak even when the conventional receive
beam shows one broad shoulder. That super-resolution is conditional: weak or
short data blur the subspaces, a wrong source count partitions them incorrectly,
and coherent sources collapse the signal covariance rank.

## Completion condition

You can identify the two correct peaks, distinguish a pseudospectrum from
received power, and explain both source-count and coherence failures, including
why spatial smoothing restores rank while shortening the effective aperture.

## Run the lesson

```bash
./bin/learn start 66
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P61 supplies the broadside-referenced positive ULA phase convention, P62 the
aperture and conventional-beam limits, P63 the conjugate receive scan, and P65
the sample-covariance eigenspectrum that MUSIC partitions here. P67 will show
how calibration and coupling errors violate the ideal steering model.

The experiment uses base MATLAB arithmetic and script-local functions, so it
requires MATLAB R2016b or newer and no optional toolbox. Elements, sources,
snapshots, scan samples, sweep cases, deterministic private samples, working
arrays, and figures have immutable reviewed ceilings. It writes no file and
starts no network request, timer, worker, or external process.

This is a narrowband, far-field, stationary, complex-baseband ULA model with
isotropic ideal sensors and spatially white receiver noise. It omits element
patterns, coupling, calibration error, multipath, broadband and near-field
effects, colored noise, automatic source-number selection, detection, and
tracking. Static checks and an independent simulated oracle do not constitute
MATLAB runtime, rendered-figure, antenna, hardware/HIL, real-time, field, or
operational-radar validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Estimate DOA with MUSIC". The guiding question is: "How can subspace methods resolve sources more finely than a conventional beam?" Use this experiment: Simulate multiple uncorrelated narrowband sources and compute the sample covariance eigenspectrum and MUSIC pseudospectrum. Have me perform these actions: Sweep source spacing, SNR, snapshot count, and assumed source number. Add coherent sources to show failure, then decorrelate with spatial smoothing. The main concept I must learn is: MUSIC separates signal and noise subspaces and can provide super-resolution when its model assumptions are satisfied. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
