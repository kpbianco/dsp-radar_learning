# P35: Create Unambiguous-Range Aliasing

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P35` is pending

## Guiding question

Why can a distant target appear at a shorter false range?

## Experiment

Simulate periodic pulses and a target whose round-trip delay exceeds one pulse-repetition interval.

## Procedure

Vary PRF and target range. Fold received echoes into successive listening intervals and plot apparent versus true range.

## What this should teach

PRF sets an unambiguous range because pulse identity becomes uncertain when echoes arrive after the next transmission.

## Completion condition

You can calculate the folded apparent range for a target beyond the unambiguous interval.

## Start or implement

```bash
./bin/learn start 35
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P35` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Create Unambiguous-Range Aliasing". The guiding question is: "Why can a distant target appear at a shorter false range?" Use this experiment: Simulate periodic pulses and a target whose round-trip delay exceeds one pulse-repetition interval. Have me perform these actions: Vary PRF and target range. Fold received echoes into successive listening intervals and plot apparent versus true range. The main concept I must learn is: PRF sets an unambiguous range because pulse identity becomes uncertain when echoes arrive after the next transmission. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
