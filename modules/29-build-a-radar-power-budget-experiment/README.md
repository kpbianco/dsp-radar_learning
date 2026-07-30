# P29: Build a Radar Power-Budget Experiment

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P29` is pending

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

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P29` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build a Radar Power-Budget Experiment". The guiding question is: "How quickly does received echo power fall with range?" Use this experiment: Implement a monostatic radar range-equation calculator and simulate received power for several target RCS values and frequencies. Have me perform these actions: Sweep range on linear and log axes, then vary transmit power, antenna gain, wavelength, losses, and RCS one at a time. Add a receiver-noise floor and mark detection margin. The main concept I must learn is: Radar echo power falls approximately as range to the fourth power, making range far more expensive than it first appears. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
