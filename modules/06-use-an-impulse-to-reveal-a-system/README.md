# P06: Use an Impulse to Reveal a System

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Scaffolded; implementation batch `P06` is pending

## Guiding question

Why does an impulse response describe an LTI system?

## Experiment

Create several simple systems: delay, moving average, echo path, and resonator. Excite each with an impulse and with a general signal.

## Procedure

Plot the impulse response, then convolve it with the general signal. Compare the convolution result with a direct implementation of the same system.

## What this should teach

An LTI system output is a weighted sum of delayed input copies, fully determined by its impulse response.

## Completion condition

Direct processing and convolution produce the same output to numerical precision.

## Start or implement

```bash
./bin/learn start 6
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P06` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use an Impulse to Reveal a System". The guiding question is: "Why does an impulse response describe an LTI system?" Use this experiment: Create several simple systems: delay, moving average, echo path, and resonator. Excite each with an impulse and with a general signal. Have me perform these actions: Plot the impulse response, then convolve it with the general signal. Compare the convolution result with a direct implementation of the same system. The main concept I must learn is: An LTI system output is a weighted sum of delayed input copies, fully determined by its impulse response. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
