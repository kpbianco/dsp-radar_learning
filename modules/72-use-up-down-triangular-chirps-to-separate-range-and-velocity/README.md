# P72: Use Up/Down Triangular Chirps to Separate Range and Velocity

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Scaffolded; implementation batch `P72` is pending

## Guiding question

How can opposite chirp slopes disentangle delay and Doppler?

## Experiment

Generate alternating up- and down-chirps for one moving target and measure both beat frequencies.

## Procedure

Solve the two equations for range and Doppler. Sweep range, velocity, and noise, and include an incorrect pairing case with multiple targets.

## What this should teach

Opposite slopes provide independent combinations of delay and Doppler but create association challenges in multi-target scenes.

## Completion condition

You recover range and velocity for one target and can explain why multiple targets complicate beat pairing.

## Start or implement

```bash
./bin/learn start 72
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P72` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use Up/Down Triangular Chirps to Separate Range and Velocity". The guiding question is: "How can opposite chirp slopes disentangle delay and Doppler?" Use this experiment: Generate alternating up- and down-chirps for one moving target and measure both beat frequencies. Have me perform these actions: Solve the two equations for range and Doppler. Sweep range, velocity, and noise, and include an incorrect pairing case with multiple targets. The main concept I must learn is: Opposite slopes provide independent combinations of delay and Doppler but create association challenges in multi-target scenes. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
