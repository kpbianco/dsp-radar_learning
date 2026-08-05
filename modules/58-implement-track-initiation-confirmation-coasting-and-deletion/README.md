# P58: Implement Track Initiation, Confirmation, Coasting, and Deletion

**Phase 6: Radar Tracking and Data Association**  
**Status:** Implemented by batch `P58`

## Guiding question

How does a radar avoid creating permanent tracks from single false alarms?

## Experiment

Feed a one-dimensional Cartesian tracker 30 scans containing one moving target,
three temporary target-report misses, and eight seeded false alarms. Each
unassigned report initiates one tentative track. The manager requires 3 hits in
the most recent 4 scans to confirm it, permits a confirmed track to coast for
2 consecutive misses, and deletes it on the third.

## Procedure

Predict every active track, gate reports in metres, and perform explicit
one-to-one nearest-neighbor association before changing lifecycle state. Shift
each tentative track's binary hit history, apply the `M-of-N` confirmation
test, coast confirmed tracks on prediction alone, and delete tentative or
confirmed tracks at their separate failure boundaries. Plot measurements,
track trajectories, lifecycle state, rolling hit score, and active-track
counts. Sweep confirmation threshold `M` and coast allowance `L` on the same
record, then bypass both safeguards as an intentionally broken policy before
restoring the reviewed manager exactly.

## What this should teach

Track management converts uncertain detections into persistent objects while
controlling false tracks and dropouts. Confirmation asks for repeated evidence;
coasting preserves an already credible object through a bounded absence;
deletion prevents old hypotheses from consuming attention forever.

## Dependencies and compatibility

- P57 is the direct implemented prerequisite. It supplies predict-first,
  gate-first, one-to-one association; P58 consumes those links and owns the
  lifecycle decisions that follow them.
- P54 and P55 supply prediction/correction intuition. P59 owns crossing-target
  identity failures; this lesson keeps reports spatially separated so lifecycle
  behavior is not confused with ambiguous association.
- `experiment.m` uses base MATLAB only. It explicitly implements prediction,
  fixed-distance gating, greedy one-to-one assignment, the rolling binary hit
  window, confirmation, prediction-only coasting, and deletion. Truth labels
  are retained only by a separate scoring pass and never affect association or
  lifecycle decisions.
- A private Park-Miller/Box-Muller generator makes the reviewed target noise and
  false-alarm positions repeatable without changing MATLAB's global random
  stream. No tracking object, assignment solver, file, network, shell, timer,
  worker, or persisted experiment state is used.
- The reviewed run is bounded to 30 scans, 2 reports per scan, 20 track IDs,
  9 lifecycle runs, 10,800 track-report pair slots, and 6 tagged figures.
  Script-local functions require MATLAB R2016b or later.

## Completion condition

The true target confirms on scan 7, remains the same track while coasting over
misses on scans 12 and 13, reacquires on scan 14, and deletes on scan 27 after
the target departs. All eight isolated false-alarm tracks delete without
confirmation under the reviewed 3-of-4 policy.

## Start

```bash
./bin/learn start 58
```

Run `experiment.m`, follow `walkthrough.md` one figure at a time, and finish
with the teach-back in `checks.md`.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Implement Track Initiation, Confirmation, Coasting, and Deletion". The guiding question is: "How does a radar avoid creating permanent tracks from single false alarms?" Use this experiment: Feed a tracker intermittent target detections plus random false alarms and temporary missed detections. Have me perform these actions: Create tentative tracks, require M-of-N confirmation, allow limited coasting, and delete stale tracks. Plot lifecycle state and score over time. The main concept I must learn is: Track management converts uncertain detections into persistent objects while controlling false tracks and dropouts. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
