# P40: Compare Coherent and Noncoherent Integration

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P40` is pending

## Guiding question

When should pulse phases be added and when should magnitudes be added?

## Experiment

Simulate repeated weak target returns with controlled phase coherence and noise.

## Procedure

Sum complex samples coherently, sum magnitudes or powers noncoherently, and compare output SNR versus number of pulses. Add phase jitter to break coherence.

## What this should teach

Coherent integration gives greater gain when phase is predictable; noncoherent integration is more tolerant but less efficient.

## Completion condition

You can show the integration-gain trend and identify when phase errors destroy coherent benefit.

## Start or implement

```bash
./bin/learn start 40
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P40` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Compare Coherent and Noncoherent Integration". The guiding question is: "When should pulse phases be added and when should magnitudes be added?" Use this experiment: Simulate repeated weak target returns with controlled phase coherence and noise. Have me perform these actions: Sum complex samples coherently, sum magnitudes or powers noncoherently, and compare output SNR versus number of pulses. Add phase jitter to break coherence. The main concept I must learn is: Coherent integration gives greater gain when phase is predictable; noncoherent integration is more tolerant but less efficient. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
