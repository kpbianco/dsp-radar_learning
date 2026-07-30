# P82: Build a Passive Radar Cross-Ambiguity Experiment

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Scaffolded; implementation batch `P82` is pending

## Guiding question

How can a known broadcast-like reference reveal delayed Doppler-shifted echoes without transmitting?

## Experiment

Create a wideband reference waveform, a surveillance channel containing direct-path leakage plus delayed/Doppler-shifted target copies, and noise.

## Procedure

Compute delay-Doppler cross-ambiguity before and after direct-path cancellation. Sweep target delay, Doppler, integration time, and reference quality.

## What this should teach

Passive radar compares a reference signal with a surveillance channel; direct-path and multipath cancellation are central challenges.

## Completion condition

The target peak appears at correct delay/Doppler only after the dominant direct component is sufficiently suppressed.

## Start or implement

```bash
./bin/learn start 82
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P82` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build a Passive Radar Cross-Ambiguity Experiment". The guiding question is: "How can a known broadcast-like reference reveal delayed Doppler-shifted echoes without transmitting?" Use this experiment: Create a wideband reference waveform, a surveillance channel containing direct-path leakage plus delayed/Doppler-shifted target copies, and noise. Have me perform these actions: Compute delay-Doppler cross-ambiguity before and after direct-path cancellation. Sweep target delay, Doppler, integration time, and reference quality. The main concept I must learn is: Passive radar compares a reference signal with a surveillance channel; direct-path and multipath cancellation are central challenges. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
