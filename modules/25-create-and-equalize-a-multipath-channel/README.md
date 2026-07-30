# P25: Create and Equalize a Multipath Channel

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Scaffolded; implementation batch `P25` is pending

## Guiding question

How do delayed copies distort symbols even when noise is small?

## Experiment

Pass a pulse-shaped QPSK signal through a short multipath FIR channel with two or three echoes.

## Procedure

Inspect channel impulse response, eye closure, constellation smearing, and frequency-selective fading. Apply a simple zero-forcing or MMSE equalizer and compare noise enhancement.

## What this should teach

Multipath creates intersymbol interference and spectral nulls; equalization reverses channel effects imperfectly and can amplify noise.

## Completion condition

You can identify the channel delays and demonstrate both improvement and failure of equalization near a deep null.

## Start or implement

```bash
./bin/learn start 25
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P25` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Create and Equalize a Multipath Channel". The guiding question is: "How do delayed copies distort symbols even when noise is small?" Use this experiment: Pass a pulse-shaped QPSK signal through a short multipath FIR channel with two or three echoes. Have me perform these actions: Inspect channel impulse response, eye closure, constellation smearing, and frequency-selective fading. Apply a simple zero-forcing or MMSE equalizer and compare noise enhancement. The main concept I must learn is: Multipath creates intersymbol interference and spectral nulls; equalization reverses channel effects imperfectly and can amplify noise. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
