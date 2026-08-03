# P23: Build BPSK and QPSK Constellation Intuition

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Implemented by batch `P23`

## Guiding question

What do symbols, phase states, and decision regions look like in IQ?

## Experiment

Generate short random BPSK and QPSK symbol sequences, display ideal
constellations, and add noise and phase rotation.

## Procedure

Show the symbol sequence in time, IQ points, and received clusters. Sweep SNR
and carrier phase error. Make hard decisions and compare bit errors.

## What this should teach

Digital modulation converts bits to geometric signal points; noise and phase
error move samples relative to decision boundaries.

## Completion condition

You can predict which symbols become confused for a given rotation or noise
level.

## Prerequisites and dependencies

- Complete [P22](../22-relate-fm-deviation-to-bandwidth/) first. Its complex
  phasor and phase-rotation view becomes the carrier-error model here.
- P17 through P19 supply complex baseband, I/Q axes, and receiver-impairment
  language.
- No Communications Toolbox or modulation toolbox is required. The script uses
  base MATLAB and explicitly maps bits, scales complex Gaussian noise, rotates
  symbols, and applies sign decisions.

## Start

```bash
./bin/learn start 23
```

Then read `lesson.md`, run `experiment.m`, and follow `walkthrough.md` one
observation at a time. Use `checks.md` for the final prediction and teach-back.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build BPSK and QPSK Constellation Intuition". The guiding question is: "What do symbols, phase states, and decision regions look like in IQ?" Use this experiment: Generate short random BPSK and QPSK symbol sequences, display ideal constellations, and add noise and phase rotation. Have me perform these actions: Show the symbol sequence in time, IQ points, and received clusters. Sweep SNR and carrier phase error. Make hard decisions and compare bit errors. The main concept I must learn is: Digital modulation converts bits to geometric signal points; noise and phase error move samples relative to decision boundaries. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
