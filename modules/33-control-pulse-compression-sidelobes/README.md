# P33: Control Pulse-Compression Sidelobes

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Scaffolded; implementation batch `P33` is pending

## Guiding question

Why can a strong target hide a weak nearby target after matched filtering?

## Experiment

Place a strong and weak target at neighboring ranges and process an LFM waveform with matched and tapered/mismatched filters.

## Procedure

Compare rectangular, Hann-like, Taylor-like, or other weighting on peak width, sidelobe level, and SNR loss. Move the weak target through the sidelobes.

## What this should teach

Sidelobe suppression trades peak SNR and main-lobe width for improved weak-target visibility.

## Completion condition

You can select weighting that reveals the weak target and quantify the resolution/SNR cost.

## Start or implement

```bash
./bin/learn start 33
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P33` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Control Pulse-Compression Sidelobes". The guiding question is: "Why can a strong target hide a weak nearby target after matched filtering?" Use this experiment: Place a strong and weak target at neighboring ranges and process an LFM waveform with matched and tapered/mismatched filters. Have me perform these actions: Compare rectangular, Hann-like, Taylor-like, or other weighting on peak width, sidelobe level, and SNR loss. Move the weak target through the sidelobes. The main concept I must learn is: Sidelobe suppression trades peak SNR and main-lobe width for improved weak-target visibility. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
