# P24: See Pulse Shaping and Matched Filtering

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Implemented by batch `P24`

## Guiding question

Why are symbols filtered before transmission and again at reception?

## Experiment

Transmit QPSK symbols through rectangular and root-raised-cosine pulse shapes, then matched-filter and sample them.

## Procedure

Plot transmitted waveform, spectrum, eye diagram, matched-filter output, and constellation before/after timing. Change roll-off and filter span.

## What this should teach

Pulse shaping controls occupied bandwidth and intersymbol interference; the matched filter maximizes sampled SNR for the known pulse.

## Completion condition

You can show an open eye and clean constellation only when timing and matched filtering are appropriate.

## Prerequisites and dependencies

- Complete [P23](../23-build-bpsk-and-qpsk-constellation-intuition/) first.
  P24 keeps its unit-energy QPSK mapping and adds the waveform between symbol
  decisions.
- P07 supplies the convolution mental model; P09 supplies FIR-filter and group
  delay language; P12 supplies finite-record spectrum interpretation.
- No Communications Toolbox is required. `experiment.m` uses base MATLAB and
  explicitly builds the rectangular pulse, root-raised-cosine taps,
  zero-stuffed waveform, matched filter, eye traces, timing samples, and hard
  decisions.

## Start

```bash
./bin/learn start 24
```

Then read `lesson.md`, run `experiment.m`, and follow `walkthrough.md` one
observation at a time. Use `checks.md` for the final prediction and teach-back.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "See Pulse Shaping and Matched Filtering". The guiding question is: "Why are symbols filtered before transmission and again at reception?" Use this experiment: Transmit QPSK symbols through rectangular and root-raised-cosine pulse shapes, then matched-filter and sample them. Have me perform these actions: Plot transmitted waveform, spectrum, eye diagram, matched-filter output, and constellation before/after timing. Change roll-off and filter span. The main concept I must learn is: Pulse shaping controls occupied bandwidth and intersymbol interference; the matched filter maximizes sampled SNR for the known pulse. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
