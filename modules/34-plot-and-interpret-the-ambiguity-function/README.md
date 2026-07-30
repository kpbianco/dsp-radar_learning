# P34: Plot and Interpret the Ambiguity Function

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P34` is pending

## Guiding question

How does a waveform respond to simultaneous delay and Doppler mismatch?

## Experiment

Compute ambiguity surfaces for a rectangular pulse, LFM chirp, and phase-coded sequence.

## Procedure

Plot 2-D delay-Doppler magnitude and cuts through zero delay and zero Doppler. Change pulse duration, bandwidth, and code length.

## What this should teach

The ambiguity function summarizes waveform resolution, sidelobes, Doppler tolerance, and delay-Doppler coupling.

## Completion condition

You can point to the main lobe and explain which waveform is best for a chosen delay/Doppler requirement.

## Start or implement

```bash
./bin/learn start 34
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P34` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Plot and Interpret the Ambiguity Function". The guiding question is: "How does a waveform respond to simultaneous delay and Doppler mismatch?" Use this experiment: Compute ambiguity surfaces for a rectangular pulse, LFM chirp, and phase-coded sequence. Have me perform these actions: Plot 2-D delay-Doppler magnitude and cuts through zero delay and zero Doppler. Change pulse duration, bandwidth, and code length. The main concept I must learn is: The ambiguity function summarizes waveform resolution, sidelobes, Doppler tolerance, and delay-Doppler coupling. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
