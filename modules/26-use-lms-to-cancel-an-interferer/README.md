# P26: Use LMS to Cancel an Interferer

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Scaffolded; implementation batch `P26` is pending

## Guiding question

How can an adaptive filter learn an unknown coupling path?

## Experiment

Create a desired signal corrupted by a correlated reference interference passed through an unknown FIR path.

## Procedure

Run LMS with several step sizes. Plot filter coefficients, error power, and residual spectrum over time. Include a path change halfway through.

## What this should teach

Adaptive filtering minimizes error from data; step size trades convergence speed, misadjustment, and stability.

## Completion condition

You can choose a stable step size and show the filter reacquiring after the interference path changes.

## Start or implement

```bash
./bin/learn start 26
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P26` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use LMS to Cancel an Interferer". The guiding question is: "How can an adaptive filter learn an unknown coupling path?" Use this experiment: Create a desired signal corrupted by a correlated reference interference passed through an unknown FIR path. Have me perform these actions: Run LMS with several step sizes. Plot filter coefficients, error power, and residual spectrum over time. Include a path change halfway through. The main concept I must learn is: Adaptive filtering minimizes error from data; step size trades convergence speed, misadjustment, and stability. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
