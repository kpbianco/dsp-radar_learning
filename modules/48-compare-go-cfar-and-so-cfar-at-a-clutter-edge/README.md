# P48: Compare GO-CFAR and SO-CFAR at a Clutter Edge

**Phase 5: Detection and CFAR**  
**Status:** Scaffolded; implementation batch `P48` is pending

## Guiding question

Which side of a changing background should control the threshold?

## Experiment

Create a sharp transition from low to high clutter with targets on both sides and near the boundary.

## Procedure

Compute leading and lagging training-window estimates, then apply greatest-of and smallest-of logic. Compare false alarms and missed detections around the edge.

## What this should teach

GO-CFAR is conservative near clutter increases, while SO-CFAR can preserve targets in certain multiple-target situations but may false alarm at edges.

## Completion condition

You can explain why the two detectors behave differently for each target location.

## Start or implement

```bash
./bin/learn start 48
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P48` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Compare GO-CFAR and SO-CFAR at a Clutter Edge". The guiding question is: "Which side of a changing background should control the threshold?" Use this experiment: Create a sharp transition from low to high clutter with targets on both sides and near the boundary. Have me perform these actions: Compute leading and lagging training-window estimates, then apply greatest-of and smallest-of logic. Compare false alarms and missed detections around the edge. The main concept I must learn is: GO-CFAR is conservative near clutter increases, while SO-CFAR can preserve targets in certain multiple-target situations but may false alarm at edges. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
