# P49: Use Ordered-Statistic CFAR with Interfering Targets

**Phase 5: Detection and CFAR**  
**Status:** Implemented by batch `P49`

## Guiding question

How can CFAR resist several contaminated training cells?

## Experiment

Place four strong targets inside a weaker target's reference window. Compare
the arithmetic mean used by CA-CFAR with an explicitly sorted OS-CFAR
reference statistic as interferer count, interferer strength, and rank change.

## Procedure

Inspect the sorted training powers, select an ascending rank, and calibrate
that rank for the requested homogeneous false-alarm probability. Then sweep
the number and strength of interfering targets and compare OS-CFAR with
CA-CFAR on the same trials.

## What this should teach

The `k`th smallest of `N` training powers can leave as many as `N-k` very high
outliers above the selected sample. That resistance is limited: too high a
rank enters the contaminated tail, while changing rank without recalibrating
its multiplier can overspend the false-alarm budget.

## Completion condition

You can choose a rank with enough outlier capacity to preserve the target,
explain the detection cost of that choice, and keep the requested homogeneous
false-alarm probability through rank-specific calibration.

## Run it

```bash
./bin/learn start 49
```

Run `experiment.m` in MATLAB, then follow `walkthrough.md` one figure group at
a time. The script uses a private seeded stream and base MATLAB operations
only. It reads and writes no files and does not change MATLAB's global random
state.

## What is implemented

- a 256-cell square-law range profile whose weak primary target has four
  stronger neighbors inside its 24-cell reference window;
- explicit CA averaging, ascending sorting, `k`th-sample selection, and exact
  rank-specific homogeneous `Pfa` calibration;
- a contaminator-count sweep that crosses the `N-k` capacity boundary;
- an interferer-strength sweep comparing OS-CFAR and CA-CFAR;
- a rank sweep exposing robustness versus clean-scene detection tradeoffs; and
- an intentionally broken reused multiplier, followed by per-rank recovery.

## Dependencies and scope

P48 supplies equal-`Pfa` comparison discipline and nonhomogeneous-reference
intuition. P47 supplies finite-reference calibration discipline, P46 supplies
training-window contamination intuition, and P45 supplies the square-law CFAR
stencil. This lesson uses independent exponential background samples,
noncoherent point-power additions for training-cell contaminators, and a
deterministic complex-amplitude CUT in complex Gaussian noise for sweep `Pd`.
It does not claim correlated or measured clutter, target fluctuation,
sidelobes, 2-D CFAR, rare-event validation, hardware, or operational-radar
behavior. P50 owns 2-D CFAR, P51 owns broader stress cases, and P52 owns
dedicated false-alarm validation.

## Files

- `experiment.m` — bounded seeded experiment, five figure groups, and metrics
  retained in `results`.
- `lesson.md` — physical model, OS calibration equation, tradeoffs, and limits.
- `walkthrough.md` — baseline, three one-variable sweeps, broken case,
  recovery, cancellation, and rerun guidance.
- `checks.md` — observation, prediction, interpretation, and teach-back checks.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use Ordered-Statistic CFAR with Interfering Targets". The guiding question is: "How can CFAR resist several contaminated training cells?" Use this experiment: Place multiple strong targets close enough that they enter one another's training windows. Have me perform these actions: Sort training-cell powers and select different rank statistics. Compare OS-CFAR with CA-CFAR as the number and strength of interfering targets changes. The main concept I must learn is: Order statistics can reject a limited number of high outliers but require choosing a rank matched to expected contamination. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
