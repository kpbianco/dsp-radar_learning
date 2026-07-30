# P74: Create a Micro-Doppler Spectrogram

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Scaffolded; implementation batch `P74` is pending

## Guiding question

How do rotating or swinging target parts produce time-varying Doppler around bulk motion?

## Experiment

Simulate a walking-like torso plus swinging limbs or a rotating blade and generate a slow-time radar return.

## Procedure

Plot raw phase, Doppler spectrum, and spectrogram. Change limb/rotor speed, carrier frequency, and STFT window length.

## What this should teach

Micro-Doppler reveals periodic component motion that is not represented by a single target velocity.

## Completion condition

You can identify the bulk Doppler and the side patterns caused by periodic motion.

## Start or implement

```bash
./bin/learn start 74
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P74` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Create a Micro-Doppler Spectrogram". The guiding question is: "How do rotating or swinging target parts produce time-varying Doppler around bulk motion?" Use this experiment: Simulate a walking-like torso plus swinging limbs or a rotating blade and generate a slow-time radar return. Have me perform these actions: Plot raw phase, Doppler spectrum, and spectrogram. Change limb/rotor speed, carrier frequency, and STFT window length. The main concept I must learn is: Micro-Doppler reveals periodic component motion that is not represented by a single target velocity. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
