# P36: Measure Doppler from Pulse-to-Pulse Phase

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P36` is pending

## Guiding question

How does target velocity create coherent phase progression across pulses?

## Experiment

Generate a complex target echo at one range bin across many pulses with controlled Doppler frequency.

## Procedure

Plot slow-time I/Q, unwrapped phase, and Doppler FFT. Sweep velocity, carrier frequency, and number of pulses. Compare approaching and receding targets.

## What this should teach

Doppler is observed as phase rotation across coherent pulses; sign and rate encode radial velocity.

## Completion condition

You can predict phase increment per pulse and velocity from the Doppler-bin location.

## Start or implement

```bash
./bin/learn start 36
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P36` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Measure Doppler from Pulse-to-Pulse Phase". The guiding question is: "How does target velocity create coherent phase progression across pulses?" Use this experiment: Generate a complex target echo at one range bin across many pulses with controlled Doppler frequency. Have me perform these actions: Plot slow-time I/Q, unwrapped phase, and Doppler FFT. Sweep velocity, carrier frequency, and number of pulses. Compare approaching and receding targets. The main concept I must learn is: Doppler is observed as phase rotation across coherent pulses; sign and rate encode radial velocity. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
