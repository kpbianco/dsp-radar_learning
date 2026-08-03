# P22: Relate FM Deviation to Bandwidth

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Implemented by batch `P22`

## Guiding question

How does instantaneous frequency motion create an FM spectrum?

## Experiment

Frequency-modulate a carrier with a sinusoid using several modulation indices.

## Procedure

Plot instantaneous phase/frequency, RF waveform, and spectrum. Compare narrowband and wideband cases and test Carson-style bandwidth intuition experimentally.

## What this should teach

FM bandwidth grows with both message bandwidth and frequency deviation, and its spectrum contains multiple Bessel-like sidebands.

## Completion condition

You can explain why the amplitude stays constant while spectral width changes strongly.

## Prerequisites

- Complete [P21](../21-visualize-am-as-carrier-and-sidebands/) first so carrier,
  message, and sideband language is familiar.
- P11 through P13 supply the FFT-bin, leakage, and finite-record bandwidth
  ideas used by the measurement.
- P16 supplies the phase and instantaneous-frequency interpretation.

No modulation toolbox is required. The script uses base MATLAB operations and
shows the phase law, phase derivative, FFT, line-power sum, and aliasing check.

## Start

```bash
./bin/learn start 22
```

Then read `lesson.md`, run `experiment.m`, and follow `walkthrough.md` one
observation at a time. Use `checks.md` for the final interpretation and
teach-back.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Relate FM Deviation to Bandwidth". The guiding question is: "How does instantaneous frequency motion create an FM spectrum?" Use this experiment: Frequency-modulate a carrier with a sinusoid using several modulation indices. Have me perform these actions: Plot instantaneous phase/frequency, RF waveform, and spectrum. Compare narrowband and wideband cases and test Carson-style bandwidth intuition experimentally. The main concept I must learn is: FM bandwidth grows with both message bandwidth and frequency deviation, and its spectrum contains multiple Bessel-like sidebands. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
