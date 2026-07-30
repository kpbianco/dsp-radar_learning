# P38: Implement a Two-Pulse and Three-Pulse MTI Canceller

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P38` is pending

## Guiding question

How do simple delay-line cancellers remove stationary clutter?

## Experiment

Create slow-time data containing strong zero-Doppler clutter and weaker moving targets.

## Procedure

Apply first- and second-difference filters across pulses. Plot frequency response and compare clutter suppression, target attenuation, and noise amplification.

## What this should teach

MTI cancellers place spectral nulls at zero Doppler and periodically elsewhere; higher order sharpens clutter rejection but changes noise and target response.

## Completion condition

You can explain which velocities are preserved or attenuated by each canceller.

## Start or implement

```bash
./bin/learn start 38
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P38` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Implement a Two-Pulse and Three-Pulse MTI Canceller". The guiding question is: "How do simple delay-line cancellers remove stationary clutter?" Use this experiment: Create slow-time data containing strong zero-Doppler clutter and weaker moving targets. Have me perform these actions: Apply first- and second-difference filters across pulses. Plot frequency response and compare clutter suppression, target attenuation, and noise amplification. The main concept I must learn is: MTI cancellers place spectral nulls at zero Doppler and periodically elsewhere; higher order sharpens clutter rejection but changes noise and target response. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
