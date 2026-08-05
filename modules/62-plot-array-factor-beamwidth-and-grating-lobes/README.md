# P62: Plot Array Factor, Beamwidth, and Grating Lobes

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Implemented by batch `P62`

## Guiding question

How do aperture size and element spacing shape a beam pattern?

## Experiment

Compute the normalized receive array factor of a uniform linear array (ULA)
from the complex contribution of every element. The deterministic baseline uses
eight uniformly weighted elements at half-wavelength spacing and broadside
steering. Five tagged figures show linear and dB patterns, measured half-power
and first-null beamwidths, peak sidelobe level, spacing aliases, taper, and an
intentionally broken grating-lobe case.

## Procedure

Run one baseline, then change one physical control at a time:

1. sweep element count at fixed half-wavelength spacing;
2. sweep spacing at fixed element count and broadside steering;
3. replace uniform weights with an explicit Hamming taper; and
4. steer a one-wavelength array to `+30 deg`, observe the equal-height lobe at
   `-30 deg`, then recover with half-wavelength spacing.

Every pattern is formed from
`sum_m w_m exp(j 2*pi*m*(d/lambda)*(sin(theta)-sin(theta_0)))`. No phased-array
or antenna toolbox call hides that coherent sum.

## What this should teach

More aperture narrows the beam; spacing above the scan-dependent spatial
sampling limit creates aliases; taper lowers sidelobes at the cost of a wider
main lobe. Element count, spacing, and weights therefore change different
parts of the same spatial interference pattern.

## Completion condition

You can predict whether a chosen spacing will produce grating lobes over the
scan region, and you can explain why taper trades sidelobe level for beamwidth.

## Run the lesson

```bash
./bin/learn start 62
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P61 is the ordered prerequisite and supplies the ULA phase convention. P12 and
P33 provide the earlier time/frequency-domain windowing analogy. P62 uses base
MATLAB arithmetic and script-local functions, so it requires MATLAB R2016b or
newer and does not require Phased Array System Toolbox or Antenna Toolbox. The
angle grid, element count, sweep count, figures, and retained numeric arrays
have fixed ceilings.

This is an ideal narrowband, far-field, isotropic-element array-factor model.
It omits element pattern, mutual coupling, calibration error, multipath, finite
bandwidth, and platform structure. Static repository checks and an independent
Python oracle do not constitute MATLAB runtime, rendered-figure, antenna,
hardware/HIL, real-time, field, or operational-radar validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Plot Array Factor, Beamwidth, and Grating Lobes". The guiding question is: "How do aperture size and element spacing shape a beam pattern?" Use this experiment: Compute ULA array factors for several element counts, spacings, and tapers. Have me perform these actions: Plot linear and dB patterns. Measure main-lobe width, peak sidelobe, and grating-lobe locations. Compare uniform and tapered weights. The main concept I must learn is: More aperture narrows the beam; spacing above roughly half wavelength creates spatial aliases; taper lowers sidelobes at the cost of beamwidth. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
