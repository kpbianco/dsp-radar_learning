# P46: Vary CFAR Guard and Training Cells

**Phase 5: Detection and CFAR**  
**Status:** Implemented by batch `P46`

## Guiding question

What happens when the CFAR reference window is too small, too large, or contaminated?

## Experiment

Use a strong target with realistic sidelobes and a background whose level changes gradually with range.

## Procedure

Sweep guard-cell and training-cell counts. Show target self-masking with too few guards, noisy threshold estimates with too few training cells, and poor locality with too many.

## What this should teach

CFAR window design balances estimator variance, target leakage protection, and adaptation to local background.

## Completion condition

You can justify a window size based on target extent, sidelobes, and expected clutter variation.

## Run it

```bash
./bin/learn start 46
```

Run `experiment.m` in MATLAB, then use `walkthrough.md` to inspect one figure
group at a time. The script uses a private seeded random stream and only base
MATLAB operations. It reads no files, writes no files, calls no services, and
does not change MATLAB's global random state.

## What is implemented

- an explicit square-law CA-CFAR loop with visible CUT, guard, and two-sided
  training geometry;
- a seeded complex-noise range profile, a gradual clutter transition, and an
  explicit sampled sinc response that gives one strong target a finite
  mainlobe and sidelobes;
- a guard sweep from zero to ten cells showing self-masking, protection, and
  the range span sacrificed to guard cells;
- a training sweep from four to 36 cells per side separating threshold
  roughness from deterministic locality error at the clutter transition; and
- an intentionally contaminated training window that masks a weaker CUT,
  followed by a wider-guard recovery computed from the original input.

## Dependencies and scope

P45 supplies the explicit 1-D CA-CFAR equation, finite-training-cell scale
factor, linear-power statistic, and excluded-edge policy. P44 supplies the
meaning of `Pfa`; P41 supplies range-varying background intuition. P46 varies
only the reference-window geometry and does not claim that one setting is
universally best. It does not replace GO/SO-CFAR or ordered-statistic CFAR:
P48 and P49 address clutter edges and interfering targets directly, while P52
owns statistical `Pfa` validation.

## Files

- `experiment.m` — bounded, seeded experiment with five figure groups and a
  retained `results` structure.
- `lesson.md` — physical model, geometry equations, tradeoffs, and limits.
- `walkthrough.md` — baseline, two one-variable sweeps, broken case, recovery,
  and cancellation guidance.
- `checks.md` — observation, prediction, interpretation, and teach-back checks.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Vary CFAR Guard and Training Cells". The guiding question is: "What happens when the CFAR reference window is too small, too large, or contaminated?" Use this experiment: Use a strong target with realistic sidelobes and a background whose level changes gradually with range. Have me perform these actions: Sweep guard-cell and training-cell counts. Show target self-masking with too few guards, noisy threshold estimates with too few training cells, and poor locality with too many. The main concept I must learn is: CFAR window design balances estimator variance, target leakage protection, and adaptation to local background. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
