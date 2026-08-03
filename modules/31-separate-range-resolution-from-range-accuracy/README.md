# P31: Separate Range Resolution from Range Accuracy

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P31`

## Guiding question

Why can an estimate be precise even when two targets cannot be resolved?

## Experiment

Transmit a sampled Gaussian-envelope pulse, insert one or two zero-extended
fractional-delay echoes, add seeded noise, and form the matched response with an
explicit lag-by-lag inner product. Measure both the waveform response width and
the error of a single-target peak estimate.

## Procedure

Hold SNR and target spacing fixed while sweeping pulse bandwidth. Then hold
bandwidth fixed while sweeping target spacing. Finally, keep one isolated
target and the same waveform while comparing integer-bin and parabolic peak
estimates across SNR.

## What this should teach

Resolution asks whether two echoes produce two distinguishable response peaks;
it is primarily waveform-bandwidth driven. Accuracy is the error of an estimate
under a stated single-target model. At adequate SNR, interpolation can locate
one peak much more finely than the response width, but it adds no bandwidth and
cannot identify two targets hidden inside one blended peak.

## Completion condition

You can show an accurate single-target range whose error is much smaller than
the measured response width while a closer two-target case remains unresolved.

## Start

```bash
./bin/learn start 31
```

Tutor mode can now use the runnable experiment, explanation, guided parameter
changes, broken case, and checks in this folder.

## Dependencies

- Conceptual: P08 introduces explicit correlation; P13 separates display-grid
  density from true resolution; P28 separates estimator error from a detection
  decision; P30 converts matched-filter delay to monostatic range with
  `R = c*tau/2`.
- Runtime: base MATLAB (MATLAB R2018b or newer for `xline` plotting); no
  toolbox, external data, hardware, network, worker, or timer is required.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Separate Range Resolution from Range Accuracy". The guiding question is: "Why can an estimate be precise even when two targets cannot be resolved?" Use this experiment: Simulate two echoes using pulses with several bandwidths and estimate both target peaks. Have me perform these actions: Hold SNR high while changing pulse width/bandwidth and target spacing. Then hold bandwidth fixed and improve interpolation or SNR for one target. The main concept I must learn is: Resolution is the ability to separate targets and is primarily bandwidth-driven; accuracy is estimation error and can be finer than the resolution cell. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m` — explicit waveform, echoes, matched filter, sweeps, failure, and recovery
- `lesson.md` — physical model, bandwidth convention, estimation limits, and dependencies
- `walkthrough.md` — baseline, controlled changes, broken interpretation, and recovery
- `checks.md` — observation, prediction, interpretation, and teach-back checks
