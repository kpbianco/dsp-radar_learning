# P13: Prove Zero-Padding Does Not Improve True Resolution

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Scaffolded; implementation batch `P13` is pending

## Guiding question

Why does a smoother FFT plot not necessarily contain more information?

## Experiment

Analyze one short data record with increasingly large zero-padded FFT lengths and compare it with a genuinely longer observation.

## Procedure

Plot the same windowed samples with 1x, 4x, and 16x zero-padding. Then collect four times more real samples and compare two nearby tones.

## What this should teach

Zero-padding interpolates the sampled spectrum; longer observation time narrows the physical main lobe and improves separability.

## Completion condition

You can distinguish visual frequency-grid density from actual resolving power.

## Start or implement

```bash
./bin/learn start 13
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P13` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Prove Zero-Padding Does Not Improve True Resolution". The guiding question is: "Why does a smoother FFT plot not necessarily contain more information?" Use this experiment: Analyze one short data record with increasingly large zero-padded FFT lengths and compare it with a genuinely longer observation. Have me perform these actions: Plot the same windowed samples with 1x, 4x, and 16x zero-padding. Then collect four times more real samples and compare two nearby tones. The main concept I must learn is: Zero-padding interpolates the sampled spectrum; longer observation time narrows the physical main lobe and improves separability. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
