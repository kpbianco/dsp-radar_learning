# P48: Compare GO-CFAR and SO-CFAR at a Clutter Edge

**Phase 5: Detection and CFAR**  
**Status:** Implemented by batch `P48`

## Guiding question

Which side of a changing background should control the threshold?

## Experiment

Create a sharp transition from low to high clutter with targets on both sides
and near the boundary.

## Procedure

Compute leading and lagging training-window estimates, then apply greatest-of
and smallest-of logic. Compare false alarms and missed detections around the
edge.

## What this should teach

GO-CFAR is conservative near clutter increases, while SO-CFAR can preserve
targets in certain multiple-target situations but may false alarm at edges.

## Completion condition

You can explain why the two detectors behave differently for each target
location.

## Run it

```bash
./bin/learn start 48
```

Run `experiment.m` in MATLAB, then use `walkthrough.md` one figure group at a
time. The script uses a private seeded random stream and base MATLAB
operations only. It reads and writes no files and does not change MATLAB's
global random state.

## What is implemented

- an explicit 240-cell square-law range profile with a 12 dB clutter step,
  four targets on both sides of the edge, and separate leading/lagging means;
- independently calibrated GO and SO scale factors for the same homogeneous
  design `Pfa`, followed by visible `max` and `min` threshold selection;
- a clutter-contrast sweep measuring high-side edge false alarms;
- a one-sided interfering-target sweep measuring weak-CUT detection; and
- an intentionally broken “always use SO” choice at the edge, recovered by
  selecting GO when false-alarm protection is the requirement.

## Dependencies and scope

P47 supplies equal-`Pfa` comparison discipline and finite-reference
uncertainty. P46 supplies reference-window contamination and geometry
intuition. P45 supplies the explicit square-law CFAR stencil. This module uses
independent exponential power samples and an abrupt two-region background; it
does not claim measured-clutter, correlated-clutter, rare-event, 2-D, hardware,
or operational-radar behavior. P49 owns ordered-statistic CFAR, P50 owns 2-D
CFAR, P51 owns broader stress testing, and P52 owns dedicated `Pfa` validation.

## Files

- `experiment.m` — bounded seeded experiment, five figure groups, and metrics
  retained in `results`.
- `lesson.md` — physical model, calibrated GO/SO equations, and limiting cases.
- `walkthrough.md` — baseline, two sweeps, broken choice, recovery, and rerun
  guidance.
- `checks.md` — observation, prediction, interpretation, and teach-back checks.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Compare GO-CFAR and SO-CFAR at a Clutter Edge". The guiding question is: "Which side of a changing background should control the threshold?" Use this experiment: Create a sharp transition from low to high clutter with targets on both sides and near the boundary. Have me perform these actions: Compute leading and lagging training-window estimates, then apply greatest-of and smallest-of logic. Compare false alarms and missed detections around the edge. The main concept I must learn is: GO-CFAR is conservative near clutter increases, while SO-CFAR can preserve targets in certain multiple-target situations but may false alarm at edges. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
