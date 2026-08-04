# P47: Measure CFAR Loss

**Phase 5: Detection and CFAR**  
**Status:** Implemented by batch `P47`

## Guiding question

How much extra SNR does adaptive threshold estimation cost?

## Experiment

Compare an ideal detector using known noise power with CA-CFAR using finite training cells.

## Procedure

For a fixed Pfa, use Monte Carlo trials to find Pd versus SNR for both detectors. Repeat with several training-cell counts.

## What this should teach

Estimating background power adds uncertainty, causing CFAR loss that shrinks as more representative training data is used.

## Completion condition

You can quantify the SNR penalty relative to a known-noise threshold.

## Run it

```bash
./bin/learn start 47
```

Run `experiment.m` in MATLAB, then use `walkthrough.md` to inspect one figure
group at a time. The script uses a private seeded random stream and base MATLAB
operations only. It reads no files, writes no files, calls no services, and
does not change MATLAB's global random state.

## What is implemented

- 50,000 deterministic homogeneous square-law Monte Carlo trials shared by a
  known-noise detector and transparent CA-CFAR detectors;
- empirical `Pd` versus SNR at equal requested `Pfa`, with required SNR found
  by visible linear interpolation at `Pd = 0.8`;
- a training-count sweep over 8, 16, 32, and 64 total reference cells;
- a requested-`Pfa` sweep showing that a stricter tail probability increases
  the finite-training penalty for the same 16-cell estimator; and
- an intentionally miscalibrated CA-CFAR comparison that appears to reduce
  loss only because it spends more false alarms, followed by exact finite-`N`
  recalibration.

## Dependencies and scope

P46 supplies the reference-window and finite-training-estimate intuition. P45
supplies the explicit square-law CA-CFAR statistic and finite-`N` multiplier.
P44 supplies empirical `Pd`/`Pfa` operating-curve interpretation, and P27
supplies independent-trial Monte Carlo discipline. This module isolates
homogeneous independent exponential reference powers: it does not model
clutter edges, contaminated references, correlated samples, fluctuating
targets, or receiver hardware. P48-P51 own nonhomogeneous CFAR behavior; P52
owns a dedicated rare-event `Pfa` validation study.

## Files

- `experiment.m` — bounded seeded experiment, five figure groups, and retained
  metrics in `results`.
- `lesson.md` — physical model, equal-`Pfa` comparison, loss definition, and
  limiting cases.
- `walkthrough.md` — baseline, two one-variable sweeps, broken calibration,
  recovery, and cancellation guidance.
- `checks.md` — observation, prediction, interpretation, and teach-back checks.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Measure CFAR Loss". The guiding question is: "How much extra SNR does adaptive threshold estimation cost?" Use this experiment: Compare an ideal detector using known noise power with CA-CFAR using finite training cells. Have me perform these actions: For a fixed Pfa, use Monte Carlo trials to find Pd versus SNR for both detectors. Repeat with several training-cell counts. The main concept I must learn is: Estimating background power adds uncertainty, causing CFAR loss that shrinks as more representative training data is used. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
