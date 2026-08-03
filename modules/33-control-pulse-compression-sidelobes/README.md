# P33: Control Pulse-Compression Sidelobes

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P33`

## Guiding question

Why can a strong target hide a weak nearby target after matched filtering?

## Experiment

Place a strong and weak target at neighboring ranges and process an LFM waveform with matched and tapered/mismatched filters.

## Procedure

Compare rectangular and explicitly constructed cosine weighting on peak width,
sidelobe level, output-SNR loss, and weak-target visibility. Sweep taper strength
and move the weak target through the strong target's compressed response.

## What this should teach

Sidelobe suppression trades peak SNR and main-lobe width for improved weak-target visibility.

## Completion condition

You can select weighting that reveals the weak target and quantify the resolution/SNR cost.

## Prerequisites and dependencies

- Complete P32 first so LFM generation, matched filtering, filter-delay removal,
  and compressed range width are familiar.
- Run in base MATLAB; no toolbox is required. The raised-cosine weights and
  convolution are visible in `experiment.m`.
- The experiment uses bounded deterministic complex-baseband point echoes. It
  is not a detector and does not model RF hardware, clutter, Doppler, or an
  operational radar.

## Start the implemented lesson

```bash
./bin/learn start 33
```

Run `experiment.m` for the deterministic baseline, taper-strength sweep,
target-separation sweep, deliberately invalid weighting choice, and exact
recovery. Then use `walkthrough.md` and `checks.md` for guided interpretation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Control Pulse-Compression Sidelobes". The guiding question is: "Why can a strong target hide a weak nearby target after matched filtering?" Use this experiment: Place a strong and weak target at neighboring ranges and process an LFM waveform with matched and tapered/mismatched filters. Have me perform these actions: Compare rectangular, Hann-like, Taylor-like, or other weighting on peak width, sidelobe level, and SNR loss. Move the weak target through the sidelobes. The main concept I must learn is: Sidelobe suppression trades peak SNR and main-lobe width for improved weak-target visibility. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
