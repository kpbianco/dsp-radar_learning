# P06: Use an Impulse to Reveal a System

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Implemented by batch `P06`

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

## Run the lesson

```bash
./bin/learn start 6
```

Start with `lesson.md`, run the sectioned `experiment.m`, and use
`walkthrough.md` to inspect one processing transition at a time. Finish with
the interpretation and teach-back prompts in `checks.md`.

## Dependencies and compatibility

P05 is the curriculum prerequisite. The experiment uses base MATLAB only: no toolbox, helper function, external data,
file write, network/device access, or asynchronous task is required. A private seeded `RandStream` makes the small
broadband probe repeatable without changing MATLAB's global random stream.
The script avoids wholesale workspace or command-window clearing, preserves
unrelated figures, and replaces only earlier figures tagged for P06. It still
creates or replaces its named variables in the current workspace.

The direct delay, moving-average, echo, and resonator rules are written out
before `conv` rebuilds their outputs. The FFT appears only in the deliberately
broken circular-convolution case, after the wraparound equation is stated.
Static repository checks do not establish MATLAB runtime or rendered-figure
correctness; see the retained P06 evidence for the exact validation boundary.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use an Impulse to Reveal a System". The guiding question is: "Why does an impulse response describe an LTI system?" Use this experiment: Create several simple systems: delay, moving average, echo path, and resonator. Excite each with an impulse and with a general signal. Have me perform these actions: Plot the impulse response, then convolve it with the general signal. Compare the convolution result with a direct implementation of the same system. The main concept I must learn is: An LTI system output is a weighted sum of delayed input copies, fully determined by its impulse response. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
