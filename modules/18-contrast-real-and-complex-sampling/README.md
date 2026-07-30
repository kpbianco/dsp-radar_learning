# P18: Contrast Real and Complex Sampling

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Scaffolded; implementation batch `P18` is pending

## Guiding question

Why can complex samples distinguish positive and negative frequencies?

## Experiment

Generate positive- and negative-frequency complex tones and compare them with real cosines having the same magnitude spectrum.

## Procedure

Plot centered FFTs and time-domain IQ trajectories. Downconvert upper- and lower-side tones with real cosine mixing and complex mixing.

## What this should teach

Real signals have conjugate-symmetric spectra; complex IQ removes that redundancy and resolves frequency sign.

## Completion condition

You can explain image ambiguity in real sampling and how IQ data removes it.

## Start or implement

```bash
./bin/learn start 18
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P18` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Contrast Real and Complex Sampling". The guiding question is: "Why can complex samples distinguish positive and negative frequencies?" Use this experiment: Generate positive- and negative-frequency complex tones and compare them with real cosines having the same magnitude spectrum. Have me perform these actions: Plot centered FFTs and time-domain IQ trajectories. Downconvert upper- and lower-side tones with real cosine mixing and complex mixing. The main concept I must learn is: Real signals have conjugate-symmetric spectra; complex IQ removes that redundancy and resolves frequency sign. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
