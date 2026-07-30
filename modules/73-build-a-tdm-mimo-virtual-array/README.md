# P73: Build a TDM-MIMO Virtual Array

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Scaffolded; implementation batch `P73` is pending

## Guiding question

How do multiple transmit and receive channels create more spatial samples?

## Experiment

Simulate a small TDM-MIMO FMCW radar, construct the virtual-element positions, and estimate target angle.

## Procedure

Compare physical RX-only and virtual-array beam patterns. Add target motion between transmit slots and observe angle/Doppler phase error.

## What this should teach

MIMO synthesizes a larger aperture from TX-RX position sums, but TDM timing couples target motion into virtual-array phase.

## Completion condition

You can draw the virtual geometry and show both resolution gain and motion-induced bias.

## Start or implement

```bash
./bin/learn start 73
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P73` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build a TDM-MIMO Virtual Array". The guiding question is: "How do multiple transmit and receive channels create more spatial samples?" Use this experiment: Simulate a small TDM-MIMO FMCW radar, construct the virtual-element positions, and estimate target angle. Have me perform these actions: Compare physical RX-only and virtual-array beam patterns. Add target motion between transmit slots and observe angle/Doppler phase error. The main concept I must learn is: MIMO synthesizes a larger aperture from TX-RX position sums, but TDM timing couples target motion into virtual-array phase. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
