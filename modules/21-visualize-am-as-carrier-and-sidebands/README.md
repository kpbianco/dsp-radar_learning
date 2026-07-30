# P21: Visualize AM as Carrier and Sidebands

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Scaffolded; implementation batch `P21` is pending

## Guiding question

How does a baseband waveform create RF sidebands?

## Experiment

Amplitude-modulate a carrier with one tone and then with a multitone/message waveform.

## Procedure

Vary modulation depth from under-modulated through over-modulated. Plot message, envelope, RF time signal, and spectrum. Recover the message with envelope and coherent detection.

## What this should teach

AM maps baseband frequencies to symmetric sidebands; excessive depth causes envelope inversion and distortion.

## Completion condition

You can predict sideband locations and explain why coherent detection still works when envelope detection fails.

## Start or implement

```bash
./bin/learn start 21
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P21` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Visualize AM as Carrier and Sidebands". The guiding question is: "How does a baseband waveform create RF sidebands?" Use this experiment: Amplitude-modulate a carrier with one tone and then with a multitone/message waveform. Have me perform these actions: Vary modulation depth from under-modulated through over-modulated. Plot message, envelope, RF time signal, and spectrum. Recover the message with envelope and coherent detection. The main concept I must learn is: AM maps baseband frequencies to symmetric sidebands; excessive depth causes envelope inversion and distortion. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
