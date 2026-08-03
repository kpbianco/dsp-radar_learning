# P43: Use a Fixed Detection Threshold

**Phase 5: Detection and CFAR**  
**Status:** Implemented by governed batch `P43`

## Guiding question

Why does a threshold that works in one noise level fail in another?

## Experiment

Generate target-absent and target-present range cells with a deterministic
real Gaussian receiver model. Calibrate one positive-amplitude threshold at a
reference noise level, then keep that threshold fixed while noise RMS and a
positive clutter pedestal change.

## Procedure

1. Inspect a seeded range profile containing four known positive-polarity
   targets and apply the threshold directly in amplitude units.
2. Compare empirical false-alarm and detection probabilities with the
   one-sided Gaussian equations at the calibration point.
3. Sweep noise RMS without changing target amplitude or threshold.
4. Sweep a positive clutter pedestal without changing noise RMS, target
   amplitude, or threshold.
5. Break the fixed-threshold premise by secretly normalizing every case with
   its true noise RMS, then recover the original fixed decisions exactly.

## What this teaches

A fixed amplitude threshold is tied to an absolute receiver scale. Its
false-alarm probability is not constant when the target-absent distribution
moves or spreads. Detection and miss rates must be conditioned on target
presence; a raw count of all threshold crossings mixes two different events.

## Completion condition

You can use the plots and retained counts to show why false alarms rise when
noise RMS or the clutter pedestal increases, why target misses rise with noise
RMS for this fixed positive target, and why dividing by the actual background
scale is an adaptive detector rather than the fixed detector being studied.

## Dependencies and runtime

[P42](../42-create-a-full-range-doppler-map/) supplies the range-cell context
and establishes that bright processed cells are not detections until an
explicit decision rule is applied. [P28](../28-connect-thresholds-to-roc-curves-and-estimator-limits/)
introduced threshold-conditioned probabilities; P43 now holds one threshold
fixed while the background changes.

The script uses base MATLAB only, a private deterministic random stream,
bounded arrays, and no file, network, device, timer, worker, or persistent
state. It models a real, signed, positive-polarity amplitude statistic; it is
not a complex-magnitude, power, CFAR, hardware, or operational-radar model.

## Start

```bash
./bin/learn start 43
```

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use a Fixed Detection Threshold". The guiding question is: "Why does a threshold that works in one noise level fail in another?" Use this experiment: Generate range cells containing Gaussian noise and occasional targets, then detect cells above a fixed threshold. Have me perform these actions: Set a threshold for one noise variance, then change noise power and clutter background without retuning. Count false alarms and missed detections. The main concept I must learn is: A fixed amplitude threshold does not maintain constant false-alarm probability when the background level changes. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.
