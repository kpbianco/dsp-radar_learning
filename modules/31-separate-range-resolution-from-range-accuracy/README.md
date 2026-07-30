# P31: Separate Range Resolution from Range Accuracy

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P31` is pending

## Guiding question

Why can an estimate be precise even when two targets cannot be resolved?

## Experiment

Simulate two echoes using pulses with several bandwidths and estimate both target peaks.

## Procedure

Hold SNR high while changing pulse width/bandwidth and target spacing. Then hold bandwidth fixed and improve interpolation or SNR for one target.

## What this should teach

Resolution is the ability to separate targets and is primarily bandwidth-driven; accuracy is estimation error and can be finer than the resolution cell.

## Completion condition

You can show a case with accurate single-target range but unresolved two-target range.

## Start or implement

```bash
./bin/learn start 31
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P31` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Separate Range Resolution from Range Accuracy". The guiding question is: "Why can an estimate be precise even when two targets cannot be resolved?" Use this experiment: Simulate two echoes using pulses with several bandwidths and estimate both target peaks. Have me perform these actions: Hold SNR high while changing pulse width/bandwidth and target spacing. Then hold bandwidth fixed and improve interpolation or SNR for one target. The main concept I must learn is: Resolution is the ability to separate targets and is primarily bandwidth-driven; accuracy is estimation error and can be finer than the resolution cell. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
