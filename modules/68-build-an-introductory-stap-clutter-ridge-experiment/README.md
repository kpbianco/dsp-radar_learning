# P68: Build an Introductory STAP Clutter-Ridge Experiment

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Scaffolded; implementation batch `P68` is pending

## Guiding question

How can space and slow time be processed together to suppress moving-platform clutter?

## Experiment

Create a small space-time data cube with clutter occupying an angle-Doppler ridge, one moving target, and thermal noise.

## Procedure

Visualize angle-Doppler power, form a space-time covariance, compare separate spatial/Doppler filtering with a joint adaptive weight, and vary training support.

## What this should teach

STAP exploits joint spatial and Doppler structure to suppress clutter that overlaps the target in either dimension alone.

## Completion condition

The joint filter improves target-to-clutter ratio and you can identify degradation from insufficient or contaminated training data.

## Start or implement

```bash
./bin/learn start 68
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P68` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build an Introductory STAP Clutter-Ridge Experiment". The guiding question is: "How can space and slow time be processed together to suppress moving-platform clutter?" Use this experiment: Create a small space-time data cube with clutter occupying an angle-Doppler ridge, one moving target, and thermal noise. Have me perform these actions: Visualize angle-Doppler power, form a space-time covariance, compare separate spatial/Doppler filtering with a joint adaptive weight, and vary training support. The main concept I must learn is: STAP exploits joint spatial and Doppler structure to suppress clutter that overlaps the target in either dimension alone. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
