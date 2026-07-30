# P39: Expose Blind Speeds and Use Staggered PRF

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P39` is pending

## Guiding question

Why can a moving target vanish in an MTI radar?

## Experiment

Sweep target velocity through the frequency response of an MTI canceller for one PRF, then repeat with a second PRF.

## Procedure

Plot output amplitude versus velocity and mark blind-speed nulls. Combine detections or amplitudes from staggered PRFs and show coverage improvement.

## What this should teach

Blind speeds occur when Doppler phase repeats at the canceller null; staggered PRFs move the nulls so they do not coincide.

## Completion condition

You can calculate the first blind speed and demonstrate recovery using another PRF.

## Start or implement

```bash
./bin/learn start 39
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P39` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Expose Blind Speeds and Use Staggered PRF". The guiding question is: "Why can a moving target vanish in an MTI radar?" Use this experiment: Sweep target velocity through the frequency response of an MTI canceller for one PRF, then repeat with a second PRF. Have me perform these actions: Plot output amplitude versus velocity and mark blind-speed nulls. Combine detections or amplitudes from staggered PRFs and show coverage improvement. The main concept I must learn is: Blind speeds occur when Doppler phase repeats at the canceller null; staggered PRFs move the nulls so they do not coincide. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
