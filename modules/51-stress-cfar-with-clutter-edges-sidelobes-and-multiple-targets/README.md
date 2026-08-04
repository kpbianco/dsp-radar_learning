# P51: Stress CFAR with Clutter Edges, Sidelobes, and Multiple Targets

**Phase 5: Detection and CFAR**  
**Status:** Implemented by batch `P51`

## Guiding question

Where do standard CFAR assumptions break?

## Experiment

Create a scenario combining a clutter edge, a strong target with sidelobes, weak neighboring targets, and nonuniform noise.

## Procedure

Run CA, GO, SO, and OS variants with the same nominal Pfa. Compare masks and classify each miss or false alarm by cause.

## What this should teach

No CFAR variant is universally best; detector choice depends on background homogeneity and target density.

## Completion condition

You can explain every major detector disagreement using the training-cell contents.

## Prerequisites and boundaries

- P45 supplies the square-law CA-CFAR mean and finite-training-cell scale.
- P48 supplies separately calibrated GO and SO selectors at a clutter edge.
- P49 supplies the ascending-rank OS statistic and its finite outlier capacity.
- P50 supplies the complete-stencil/no-decision boundary policy used here.
- P52, not this lesson, validates achieved false-alarm probability with a
  dedicated rare-event Monte Carlo experiment.

The experiment uses base MATLAB only. It creates synthetic independent
square-law background samples, deterministic target responses, and compact
paired trials; it reads no external data and calls no CFAR toolbox object.

## Start or implement

```bash
./bin/learn start 51
```

Tutor mode should begin with the baseline stress scene, inspect one CUT's
training cells at a time, and use `walkthrough.md` to separate edge,
sidelobe, target-density, and calibration failures.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Stress CFAR with Clutter Edges, Sidelobes, and Multiple Targets". The guiding question is: "Where do standard CFAR assumptions break?" Use this experiment: Create a scenario combining a clutter edge, a strong target with sidelobes, weak neighboring targets, and nonuniform noise. Have me perform these actions: Run CA, GO, SO, and OS variants with the same nominal Pfa. Compare masks and classify each miss or false alarm by cause. The main concept I must learn is: No CFAR variant is universally best; detector choice depends on background homogeneity and target density. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
