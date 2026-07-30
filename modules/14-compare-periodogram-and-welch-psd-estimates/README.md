# P14: Compare Periodogram and Welch PSD Estimates

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Scaffolded; implementation batch `P14` is pending

## Guiding question

Why does averaging make a noise spectrum easier to interpret?

## Experiment

Estimate the PSD of noisy tones using one periodogram and Welch averaging with different segment lengths and overlaps.

## Procedure

Repeat the experiment with different random seeds. Compare variance, frequency resolution, and weak-tone visibility as segment length and averaging change.

## What this should teach

PSD estimation trades resolution for statistical variance; averaging stabilizes noise estimates but shortens each effective observation.

## Completion condition

You can choose segment length and averaging based on the weakest feature you need to resolve.

## Start or implement

```bash
./bin/learn start 14
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P14` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Compare Periodogram and Welch PSD Estimates". The guiding question is: "Why does averaging make a noise spectrum easier to interpret?" Use this experiment: Estimate the PSD of noisy tones using one periodogram and Welch averaging with different segment lengths and overlaps. Have me perform these actions: Repeat the experiment with different random seeds. Compare variance, frequency resolution, and weak-tone visibility as segment length and averaging change. The main concept I must learn is: PSD estimation trades resolution for statistical variance; averaging stabilizes noise estimates but shortens each effective observation. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
