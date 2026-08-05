# P59: Track Crossing Targets and Observe Association Failure

**Phase 6: Radar Tracking and Data Association**  
**Status:** Implemented by batch `P59`

## Guiding question

Why do simple nearest-neighbor trackers swap identities?

## Experiment

Simulate two established targets with equal speed and similar two-dimensional
velocity vectors crossing in position. Generate noisy Cartesian position and
auxiliary velocity reports from a private deterministic record. Compare a
position-only greedy nearest-neighbor tracker with the same tracker after a
normalized velocity term is added to its association cost.

## Procedure

Run explicit one-to-one nearest-neighbor association and display identity
history. Change measurement noise, update rate, and closest separation one at
a time over paired seeded trials. Add normalized velocity information to the
association cost. Then deliberately let tracks select reports independently,
observe report reuse and coalescence, and restore the reviewed one-to-one rule
on the identical input arrays.

## What this should teach

Ambiguous geometry can cause coalescence or track swaps; richer state and measurement features reduce ambiguity but do not eliminate it.

## Completion condition

You can produce the seed-5908 identity swap, distinguish wrong links from
identity transitions, and explain why the velocity-aware cost lowers failure
frequency without guaranteeing identity through every ambiguous crossing.

## Start or implement

```bash
./bin/learn start 59
```

Tutor mode starts with the baseline sections of `experiment.m`, then follows
`walkthrough.md` one observation at a time. Use `checks.md` for the final
teach-back before recording personal completion.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Track Crossing Targets and Observe Association Failure". The guiding question is: "Why do simple nearest-neighbor trackers swap identities?" Use this experiment: Simulate two targets crossing in position with similar velocities and noisy detections. Have me perform these actions: Run nearest-neighbor association and display identity history. Change measurement noise, update rate, and target separation. Add velocity or amplitude information to the association cost. The main concept I must learn is: Ambiguous geometry can cause coalescence or track swaps; richer state and measurement features reduce ambiguity but do not eliminate it. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Dependencies

- P57 supplies explicit greedy one-to-one nearest-neighbor association.
- P58 supplies the established-track lifecycle boundary; this experiment holds
  two confirmed tracks alive so initiation/deletion cannot mask association
  failure.
- Base MATLAB R2016b or later is sufficient. No toolbox, data file, network,
  worker, callback, or global random stream is used.

## Implemented files

- `experiment.m` — deterministic baseline, three controlled sweeps, broken
  report-reuse case, exact recovery, six figures, and bounded metrics.
- `lesson.md` — physical model, normalized costs, limiting cases, and scope.
- `walkthrough.md` — one transition at a time with expected observations.
- `checks.md` — observation, prediction, interpretation, recovery, and
  teach-back checks.
