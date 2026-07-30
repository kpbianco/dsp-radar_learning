# P16: Create an Analytic Signal with the Hilbert Transform

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Scaffolded; implementation batch `P16` is pending

## Guiding question

How can a real waveform be represented by a complex envelope?

## Experiment

Generate an amplitude- and phase-varying real bandpass signal, form its analytic signal, and extract envelope and instantaneous phase.

## Procedure

Compare the real signal, analytic magnitude, unwrapped phase, and instantaneous frequency. Include a case where amplitude approaches zero and phase becomes unstable.

## What this should teach

The analytic signal suppresses negative-frequency redundancy and exposes envelope and phase, but instantaneous phase is unreliable at low amplitude.

## Completion condition

You can recover the designed envelope and identify where instantaneous frequency becomes meaningless.

## Start or implement

```bash
./bin/learn start 16
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P16` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Create an Analytic Signal with the Hilbert Transform". The guiding question is: "How can a real waveform be represented by a complex envelope?" Use this experiment: Generate an amplitude- and phase-varying real bandpass signal, form its analytic signal, and extract envelope and instantaneous phase. Have me perform these actions: Compare the real signal, analytic magnitude, unwrapped phase, and instantaneous frequency. Include a case where amplitude approaches zero and phase becomes unstable. The main concept I must learn is: The analytic signal suppresses negative-frequency redundancy and exposes envelope and phase, but instantaneous phase is unreliable at low amplitude. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
