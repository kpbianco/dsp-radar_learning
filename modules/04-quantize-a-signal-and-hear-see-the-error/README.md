# P04: Quantize a Signal and Hear/See the Error

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Scaffolded; implementation batch `P04` is pending

## Guiding question

How do ADC bit depth and full-scale range change the measurement?

## Experiment

Quantize the same sinusoid using several bit depths and full-scale settings, then plot the error and its spectrum.

## Procedure

Compare 3, 6, 10, and 14 bits. Repeat with the signal using most of full scale and only a small fraction. Add optional dither and observe the error spectrum.

## What this should teach

Quantization creates amplitude-dependent error; using too little ADC range wastes effective resolution, while clipping is much worse than quantization noise.

## Completion condition

You can distinguish quantization noise, clipping, and poor full-scale utilization from the plots.

## Start or implement

```bash
./bin/learn start 4
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P04` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Quantize a Signal and Hear/See the Error". The guiding question is: "How do ADC bit depth and full-scale range change the measurement?" Use this experiment: Quantize the same sinusoid using several bit depths and full-scale settings, then plot the error and its spectrum. Have me perform these actions: Compare 3, 6, 10, and 14 bits. Repeat with the signal using most of full scale and only a small fraction. Add optional dither and observe the error spectrum. The main concept I must learn is: Quantization creates amplitude-dependent error; using too little ADC range wastes effective resolution, while clipping is much worse than quantization noise. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
