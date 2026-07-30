# P58: Implement Track Initiation, Confirmation, Coasting, and Deletion

**Phase 6: Radar Tracking and Data Association**  
**Status:** Scaffolded; implementation batch `P58` is pending

## Guiding question

How does a radar avoid creating permanent tracks from single false alarms?

## Experiment

Feed a tracker intermittent target detections plus random false alarms and temporary missed detections.

## Procedure

Create tentative tracks, require M-of-N confirmation, allow limited coasting, and delete stale tracks. Plot lifecycle state and score over time.

## What this should teach

Track management converts uncertain detections into persistent objects while controlling false tracks and dropouts.

## Completion condition

True targets confirm and survive short misses, while isolated false alarms disappear quickly.

## Start or implement

```bash
./bin/learn start 58
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P58` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Implement Track Initiation, Confirmation, Coasting, and Deletion". The guiding question is: "How does a radar avoid creating permanent tracks from single false alarms?" Use this experiment: Feed a tracker intermittent target detections plus random false alarms and temporary missed detections. Have me perform these actions: Create tentative tracks, require M-of-N confirmation, allow limited coasting, and delete stale tracks. Plot lifecycle state and score over time. The main concept I must learn is: Track management converts uncertain detections into persistent objects while controlling false tracks and dropouts. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
