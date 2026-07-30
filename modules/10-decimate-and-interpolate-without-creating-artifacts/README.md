# P10: Decimate and Interpolate Without Creating Artifacts

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Scaffolded; implementation batch `P10` is pending

## Guiding question

Why must filtering accompany sample-rate changes?

## Experiment

Create a two-tone signal, decimate it, then interpolate it back to the original sample rate with and without proper filters.

## Procedure

Place one tone safely inside the new bandwidth and one tone that will alias. Compare naive sample dropping, anti-alias filtering, zero insertion, and reconstruction filtering.

## What this should teach

Decimation narrows the usable bandwidth and interpolation creates spectral images unless filtering is applied.

## Completion condition

You can identify aliasing and interpolation images and show the filtered result removes them.

## Start or implement

```bash
./bin/learn start 10
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P10` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Decimate and Interpolate Without Creating Artifacts". The guiding question is: "Why must filtering accompany sample-rate changes?" Use this experiment: Create a two-tone signal, decimate it, then interpolate it back to the original sample rate with and without proper filters. Have me perform these actions: Place one tone safely inside the new bandwidth and one tone that will alias. Compare naive sample dropping, anti-alias filtering, zero insertion, and reconstruction filtering. The main concept I must learn is: Decimation narrows the usable bandwidth and interpolation creates spectral images unless filtering is applied. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
