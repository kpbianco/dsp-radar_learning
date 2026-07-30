# P83: Compare Range-Doppler Processing with a Small STAP Processor

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Scaffolded; implementation batch `P83` is pending

## Guiding question

When is Doppler filtering alone insufficient against clutter?

## Experiment

Create an airborne or moving-platform scenario with an array, clutter ridge, and a target embedded near that ridge.

## Procedure

Form a conventional range-Doppler map, then apply a small joint space-time adaptive processor using neighboring training snapshots. Compare output SINR and sensitivity to contaminated training.

## What this should teach

Clutter can occupy coupled angle-Doppler structure, requiring joint adaptive processing rather than independent beam and Doppler filters.

## Completion condition

The target becomes more visible after STAP and you can identify the cost of poor covariance training.

## Start or implement

```bash
./bin/learn start 83
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P83` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Compare Range-Doppler Processing with a Small STAP Processor". The guiding question is: "When is Doppler filtering alone insufficient against clutter?" Use this experiment: Create an airborne or moving-platform scenario with an array, clutter ridge, and a target embedded near that ridge. Have me perform these actions: Form a conventional range-Doppler map, then apply a small joint space-time adaptive processor using neighboring training snapshots. Compare output SINR and sensitivity to contaminated training. The main concept I must learn is: Clutter can occupy coupled angle-Doppler structure, requiring joint adaptive processing rather than independent beam and Doppler filters. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
