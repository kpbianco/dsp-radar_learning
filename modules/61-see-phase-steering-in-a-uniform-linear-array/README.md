# P61: See Phase Steering in a Uniform Linear Array

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Implemented by batch `P61`

## Guiding question

How does a direction of arrival become a phase slope across sensors?

## Experiment

Simulate a narrowband plane wave arriving at a ULA and plot complex samples across elements.

## Procedure

Sweep arrival angle, spacing, and frequency. Unwrap inter-element phase and compare with the geometric delay formula.

## What this should teach

Far-field angle is encoded as a predictable spatial phase progression whose scale depends on wavelength and element spacing.

## Completion condition

You can infer arrival angle from the measured phase slope in an unambiguous case.

## Run the lesson

```bash
./bin/learn start 61
```

Then follow `walkthrough.md` one observation at a time and use `checks.md`
before giving the short teach-back.

## Dependencies and compatibility

P60 is the ordered curriculum prerequisite. P01 supplies the complex-phasor
picture, P20 supplies noisy phase-slope estimation, and P36 is the temporal
phase-progression analogue. P61 uses base MATLAB only, requires script-local
functions (MATLAB R2016b or newer), and does not require Phased Array System
Toolbox. The experiment is a bounded narrowband far-field simulation, not a
calibrated antenna, beamformer, hardware, HIL, or field result.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "See Phase Steering in a Uniform Linear Array". The guiding question is: "How does a direction of arrival become a phase slope across sensors?" Use this experiment: Simulate a narrowband plane wave arriving at a ULA and plot complex samples across elements. Have me perform these actions: Sweep arrival angle, spacing, and frequency. Unwrap inter-element phase and compare with the geometric delay formula. The main concept I must learn is: Far-field angle is encoded as a predictable spatial phase progression whose scale depends on wavelength and element spacing. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
