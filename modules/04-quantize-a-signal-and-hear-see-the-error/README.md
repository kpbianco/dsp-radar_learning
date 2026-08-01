# P04: Quantize a Signal and Hear/See the Error

**Phase 1: Signals, Sampling, and Systems**
**Status:** Implemented by Portfolio Control batch `P04`

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

## Run the experiment

```bash
./bin/learn start 4
```

Run `experiment.m` from this directory. It uses a deterministic coherent
sinusoid and an explicit bipolar mid-rise quantizer. The baseline shows the
stair-step measurement, time-domain error, and error spectrum. Two sweeps hold
all but one mechanism fixed: ADC bit depth `[3 6 10 14]`, then the ADC
full-scale setting while the same sinusoid is reused. A seeded
triangular-dither comparison and a
deliberately overloaded clipping case make the different error mechanisms
visible.

The script prepares bounded audio-preview vectors but never starts playback.
Optional listening is a learner-triggered action described in the walkthrough,
so automated runs do not require an audio device.

## Dependencies and compatibility

- Curriculum prerequisite: P03, including its sampling and aliasing model.
- Runtime: base MATLAB only; no toolbox, helper function, external data,
  hardware, audio device, or network access is required.
- Quantization, saturation, error, metrics, and spectrum scaling are written as
  explicit arithmetic. Base MATLAB `fft` evaluates the stated DFT equation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Quantize a Signal and Hear/See the Error". The guiding question is: "How do ADC bit depth and full-scale range change the measurement?" Use this experiment: Quantize the same sinusoid using several bit depths and full-scale settings, then plot the error and its spectrum. Have me perform these actions: Compare 3, 6, 10, and 14 bits. Repeat with the signal using most of full scale and only a small fraction. Add optional dither and observe the error spectrum. The main concept I must learn is: Quantization creates amplitude-dependent error; using too little ADC range wastes effective resolution, while clipping is much worse than quantization noise. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m` — deterministic baseline, two sweeps, dither, and clipping
- `lesson.md` — physical model, equations, limiting cases, and radar connection
- `walkthrough.md` — guided observations and non-destructive recovery
- `checks.md` — prediction, interpretation, and teach-back rubric
