# P26: Use LMS to Cancel an Interferer

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Implemented by batch `P26`

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

## Prerequisites and dependencies

- **P25** supplies the FIR-path view: a received signal can contain delayed,
  scaled copies of another waveform.
- **P07** supplies convolution as weighted echo addition.
- **Base MATLAB only:** the LMS estimate and coefficient update are explicit;
  no adaptive-filter toolbox object hides the operation.

## Start

```bash
./bin/learn start 26
```

Tutor mode opens the implemented experiment, explanation, walkthrough, and
checks. Run the script from this folder so its retained `results` structure is
available for guided inspection.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use LMS to Cancel an Interferer". The guiding question is: "How can an adaptive filter learn an unknown coupling path?" Use this experiment: Create a desired signal corrupted by a correlated reference interference passed through an unknown FIR path. Have me perform these actions: Run LMS with several step sizes. Plot filter coefficients, error power, and residual spectrum over time. Include a path change halfway through. The main concept I must learn is: Adaptive filtering minimizes error from data; step size trades convergence speed, misadjustment, and stability. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md` — canonical question, experiment, and completion contract
- `experiment.m` — deterministic LMS baseline, two sweeps, guarded failure,
  recovery, metrics, and figures
- `lesson.md` — physical model, update equation, stability, and limiting cases
- `walkthrough.md` — observation-first baseline and parameter changes
- `checks.md` — interpretation, prediction, recovery, and teach-back checks
