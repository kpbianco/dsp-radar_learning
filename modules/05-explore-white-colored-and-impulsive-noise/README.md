# P05: Explore White, Colored, and Impulsive Noise

**Phase 1: Signals, Sampling, and Systems**
**Status:** Implemented by batch `P05`

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

## Run the experiment

```bash
./bin/learn start 5
```

Then run `experiment.m` in MATLAB and use `walkthrough.md` one processing
transition at a time. The script is deterministic: rerunning its committed
controls starts from seed 505.

## Dependencies and compatibility

- Curriculum prerequisite: implemented module P04.
- Runtime: base MATLAB only; no toolbox, helper function, external data,
  hardware, audio device, network access, or asynchronous task is required.
  A private seeded random stream and P05-tagged figures preserve the global
  session RNG and unrelated figures. The script does not wholesale-clear the
  workspace or command window, but it does create or replace its named working
  variables, including `results`.
- The one-pole recursion, equal-RMS normalization, autocorrelation, raw
  one-sided PSD scaling, and coherent tone projection are visible in the
  script. `fft` evaluates the DFT equation stated beside it rather than hiding
  the spectral operation.
- MATLAB or a compatible runtime still needs to execute the script before its
  figures or MATLAB-seeded values can be claimed as runtime evidence.

## Learning files

- `experiment.m` — seeded baseline, two parameter sweeps, and broken case
- `lesson.md` — physical model, equations, limits, and radar connection
- `walkthrough.md` — guided observations and recovery
- `checks.md` — prediction, interpretation, and teach-back rubric

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Explore White, Colored, and Impulsive Noise". The guiding question is: "What does the word noise hide about time behavior and spectrum?" Use this experiment: Generate Gaussian white noise, low-pass colored noise, narrowband interference, and impulsive outliers with the same RMS level. Have me perform these actions: Plot short time records, histograms, autocorrelation, and PSD for each noise type. Add each to the same tone and compare detectability. The main concept I must learn is: Equal RMS noise can behave very differently depending on distribution, bandwidth, correlation, and impulsiveness. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.
