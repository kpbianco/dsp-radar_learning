# P29: Build a Radar Power-Budget Experiment

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P29`

## Guiding question

How quickly does received echo power fall with range?

## Experiment

Implement a monostatic radar range-equation calculator and simulate received power for several target RCS values and frequencies.

## Procedure

Sweep range on linear and log axes, then vary transmit power, antenna gain, wavelength, losses, and RCS one at a time. Add a receiver-noise floor and mark detection margin.

## What this should teach

Radar echo power falls approximately as range to the fourth power, making range far more expensive than it first appears.

## Completion condition

You can predict how much transmit power or antenna gain is needed to recover a lost range margin.

## Start or implement

```bash
./bin/learn start 29
```

Tutor mode can now use the runnable experiment, explanation, guided parameter changes, broken case, and checks in this folder.

## Dependencies

- Conceptual: P27's repeated-trial/noise intuition and P28's threshold-versus-detection-margin distinction.
- Runtime: base MATLAB only; no toolbox, external data, hardware, network, worker, or timer is required.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build a Radar Power-Budget Experiment". The guiding question is: "How quickly does received echo power fall with range?" Use this experiment: Implement a monostatic radar range-equation calculator and simulate received power for several target RCS values and frequencies. Have me perform these actions: Sweep range on linear and log axes, then vary transmit power, antenna gain, wavelength, losses, and RCS one at a time. Add a receiver-noise floor and mark detection margin. The main concept I must learn is: Radar echo power falls approximately as range to the fourth power, making range far more expensive than it first appears. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m` — explicit range equation, noise threshold, sweeps, failure, and recovery
- `lesson.md` — physical model, assumptions, limits, and interpretation
- `walkthrough.md` — baseline, controlled changes, broken case, and recovery
- `checks.md` — observation, prediction, interpretation, and teach-back checks
