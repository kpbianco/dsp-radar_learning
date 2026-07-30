# P07: Understand Convolution as Echo Addition

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Scaffolded; implementation batch `P07` is pending

## Guiding question

What is convolution actually doing at each output sample?

## Experiment

Use a short pulse and a three-tap echo channel whose taps have visibly different delays and amplitudes.

## Procedure

Construct the output first by shifting and scaling copies of the input, then by convolution. Animate the overlap-and-sum process for a small sequence.

## What this should teach

Convolution is not an abstract command; it adds delayed, scaled contributions from the input according to the system response.

## Completion condition

You can manually predict the main peaks in the convolved output.

## Start or implement

```bash
./bin/learn start 7
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P07` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Understand Convolution as Echo Addition". The guiding question is: "What is convolution actually doing at each output sample?" Use this experiment: Use a short pulse and a three-tap echo channel whose taps have visibly different delays and amplitudes. Have me perform these actions: Construct the output first by shifting and scaling copies of the input, then by convolution. Animate the overlap-and-sum process for a small sequence. The main concept I must learn is: Convolution is not an abstract command; it adds delayed, scaled contributions from the input according to the system response. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
