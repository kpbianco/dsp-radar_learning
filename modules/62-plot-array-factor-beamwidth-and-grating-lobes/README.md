# P62: Plot Array Factor, Beamwidth, and Grating Lobes

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Scaffolded; implementation batch `P62` is pending

## Guiding question

How do aperture size and element spacing shape a beam pattern?

## Experiment

Compute ULA array factors for several element counts, spacings, and tapers.

## Procedure

Plot linear and dB patterns. Measure main-lobe width, peak sidelobe, and grating-lobe locations. Compare uniform and tapered weights.

## What this should teach

More aperture narrows the beam; spacing above roughly half wavelength creates spatial aliases; taper lowers sidelobes at the cost of beamwidth.

## Completion condition

You can predict whether a chosen spacing will produce grating lobes over the scan region.

## Start or implement

```bash
./bin/learn start 62
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P62` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Plot Array Factor, Beamwidth, and Grating Lobes". The guiding question is: "How do aperture size and element spacing shape a beam pattern?" Use this experiment: Compute ULA array factors for several element counts, spacings, and tapers. Have me perform these actions: Plot linear and dB patterns. Measure main-lobe width, peak sidelobe, and grating-lobe locations. Compare uniform and tapered weights. The main concept I must learn is: More aperture narrows the beam; spacing above roughly half wavelength creates spatial aliases; taper lowers sidelobes at the cost of beamwidth. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
