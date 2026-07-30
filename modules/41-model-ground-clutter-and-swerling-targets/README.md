# P41: Model Ground Clutter and Swerling Targets

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P41` is pending

## Guiding question

Why do clutter and target amplitude fluctuate differently from white noise?

## Experiment

Create range-dependent clutter with spatial correlation and target amplitudes following several simple Swerling-like fluctuation models.

## Procedure

Plot amplitude histograms, correlation, and pulse-to-pulse variation. Compare detection stability for a nonfluctuating target and fluctuating targets at equal average SNR.

## What this should teach

Radar backgrounds and targets often have structured, non-Gaussian, and correlated statistics that change detector performance.

## Completion condition

You can distinguish thermal noise, correlated clutter, and target fluctuation in simulated data.

## Start or implement

```bash
./bin/learn start 41
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P41` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Model Ground Clutter and Swerling Targets". The guiding question is: "Why do clutter and target amplitude fluctuate differently from white noise?" Use this experiment: Create range-dependent clutter with spatial correlation and target amplitudes following several simple Swerling-like fluctuation models. Have me perform these actions: Plot amplitude histograms, correlation, and pulse-to-pulse variation. Compare detection stability for a nonfluctuating target and fluctuating targets at equal average SNR. The main concept I must learn is: Radar backgrounds and targets often have structured, non-Gaussian, and correlated statistics that change detector performance. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
