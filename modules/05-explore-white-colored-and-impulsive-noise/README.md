# P05: Explore White, Colored, and Impulsive Noise

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Scaffolded; implementation batch `P05` is pending

## Guiding question

What does the word noise hide about time behavior and spectrum?

## Experiment

Generate Gaussian white noise, low-pass colored noise, narrowband interference, and impulsive outliers with the same RMS level.

## Procedure

Plot short time records, histograms, autocorrelation, and PSD for each noise type. Add each to the same tone and compare detectability.

## What this should teach

Equal RMS noise can behave very differently depending on distribution, bandwidth, correlation, and impulsiveness.

## Completion condition

You can identify each noise type from both time and frequency views.

## Start or implement

```bash
./bin/learn start 5
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P05` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Explore White, Colored, and Impulsive Noise". The guiding question is: "What does the word noise hide about time behavior and spectrum?" Use this experiment: Generate Gaussian white noise, low-pass colored noise, narrowband interference, and impulsive outliers with the same RMS level. Have me perform these actions: Plot short time records, histograms, autocorrelation, and PSD for each noise type. Add each to the same tone and compare detectability. The main concept I must learn is: Equal RMS noise can behave very differently depending on distribution, bandwidth, correlation, and impulsiveness. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
