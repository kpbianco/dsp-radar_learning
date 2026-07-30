# P64: Build an Amplitude-Comparison Monopulse Experiment

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Scaffolded; implementation batch `P64` is pending

## Guiding question

How can sum and difference beams estimate small angle error around boresight?

## Experiment

Construct overlapping left/right or sum/difference beam patterns and simulate a target near boresight.

## Procedure

Plot sum, difference, and normalized difference/sum ratio versus angle. Add amplitude noise and calibration mismatch, then estimate angle from the ratio.

## What this should teach

Monopulse converts a single snapshot of relative channel response into a local angle-error estimate.

## Completion condition

The ratio is approximately monotonic near boresight and calibration error produces a visible angle bias.

## Start or implement

```bash
./bin/learn start 64
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P64` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build an Amplitude-Comparison Monopulse Experiment". The guiding question is: "How can sum and difference beams estimate small angle error around boresight?" Use this experiment: Construct overlapping left/right or sum/difference beam patterns and simulate a target near boresight. Have me perform these actions: Plot sum, difference, and normalized difference/sum ratio versus angle. Add amplitude noise and calibration mismatch, then estimate angle from the ratio. The main concept I must learn is: Monopulse converts a single snapshot of relative channel response into a local angle-error estimate. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
