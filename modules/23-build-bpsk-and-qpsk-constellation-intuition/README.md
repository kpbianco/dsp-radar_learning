# P23: Build BPSK and QPSK Constellation Intuition

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Scaffolded; implementation batch `P23` is pending

## Guiding question

What do symbols, phase states, and decision regions look like in IQ?

## Experiment

Generate short random BPSK and QPSK symbol sequences, display ideal constellations, and add noise and phase rotation.

## Procedure

Show the symbol sequence in time, IQ points, and received clusters. Sweep SNR and carrier phase error. Make hard decisions and compare bit errors.

## What this should teach

Digital modulation converts bits to geometric signal points; noise and phase error move samples relative to decision boundaries.

## Completion condition

You can predict which symbols become confused for a given rotation or noise level.

## Start or implement

```bash
./bin/learn start 23
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P23` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build BPSK and QPSK Constellation Intuition". The guiding question is: "What do symbols, phase states, and decision regions look like in IQ?" Use this experiment: Generate short random BPSK and QPSK symbol sequences, display ideal constellations, and add noise and phase rotation. Have me perform these actions: Show the symbol sequence in time, IQ points, and received clusters. Sweep SNR and carrier phase error. Make hard decisions and compare bit errors. The main concept I must learn is: Digital modulation converts bits to geometric signal points; noise and phase error move samples relative to decision boundaries. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
