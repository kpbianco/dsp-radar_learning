# P25: Create and Equalize a Multipath Channel

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Implemented by batch `P25`

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

## Prerequisites and dependencies

- Complete [P24](../24-see-pulse-shaping-and-matched-filtering/) first. P25
  keeps its seeded, unit-energy QPSK and explicit root-raised-cosine waveform,
  then inserts a channel between the transmit and matched filters.
- P07 supplies the delayed-copy convolution model; P09 supplies FIR and
  frequency-response language; P23 supplies the constellation decisions.
- No Communications Toolbox is required. `experiment.m` explicitly builds the
  QPSK symbols, RRC pulse, delayed-tap channel, matched-filter sampler,
  convolution matrices, causal zero-forcing inverse, and regularized MMSE
  equalizer using base MATLAB operations.

## Start

```bash
./bin/learn start 25
```

Then read `lesson.md`, run `experiment.m`, and follow `walkthrough.md` one
observation at a time. Use `checks.md` for the final prediction and teach-back.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Create and Equalize a Multipath Channel". The guiding question is: "How do delayed copies distort symbols even when noise is small?" Use this experiment: Pass a pulse-shaped QPSK signal through a short multipath FIR channel with two or three echoes. Have me perform these actions: Inspect channel impulse response, eye closure, constellation smearing, and frequency-selective fading. Apply a simple zero-forcing or MMSE equalizer and compare noise enhancement. The main concept I must learn is: Multipath creates intersymbol interference and spectral nulls; equalization reverses channel effects imperfectly and can amplify noise. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
