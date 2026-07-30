# P22: Relate FM Deviation to Bandwidth

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Scaffolded; implementation batch `P22` is pending

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

## Start or implement

```bash
./bin/learn start 22
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P22` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Relate FM Deviation to Bandwidth". The guiding question is: "How does instantaneous frequency motion create an FM spectrum?" Use this experiment: Frequency-modulate a carrier with a sinusoid using several modulation indices. Have me perform these actions: Plot instantaneous phase/frequency, RF waveform, and spectrum. Compare narrowband and wideband cases and test Carson-style bandwidth intuition experimentally. The main concept I must learn is: FM bandwidth grows with both message bandwidth and frequency deviation, and its spectrum contains multiple Bessel-like sidebands. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
