# P27: Use Monte Carlo Trials Instead of One Lucky Run

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Scaffolded; implementation batch `P27` is pending

## Guiding question

Why is one noise realization not enough to judge an algorithm?

## Experiment

Choose a simple detector or estimator and repeat it over hundreds or thousands of random trials.

## Procedure

Plot trial outcomes, running mean, confidence interval, and final empirical distribution. Repeat with too few trials and compare apparent conclusions.

## What this should teach

Random algorithms must be characterized statistically; reproducible seeds and sufficient trial count prevent misleading examples.

## Completion condition

Your reported probability or RMSE stabilizes as trials increase and repeats with the same seed.

## Start or implement

```bash
./bin/learn start 27
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P27` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use Monte Carlo Trials Instead of One Lucky Run". The guiding question is: "Why is one noise realization not enough to judge an algorithm?" Use this experiment: Choose a simple detector or estimator and repeat it over hundreds or thousands of random trials. Have me perform these actions: Plot trial outcomes, running mean, confidence interval, and final empirical distribution. Repeat with too few trials and compare apparent conclusions. The main concept I must learn is: Random algorithms must be characterized statistically; reproducible seeds and sufficient trial count prevent misleading examples. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
