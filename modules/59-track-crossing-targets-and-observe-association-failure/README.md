# P59: Track Crossing Targets and Observe Association Failure

**Phase 6: Radar Tracking and Data Association**  
**Status:** Scaffolded; implementation batch `P59` is pending

## Guiding question

Why do simple nearest-neighbor trackers swap identities?

## Experiment

Simulate two targets crossing in position with similar velocities and noisy detections.

## Procedure

Run nearest-neighbor association and display identity history. Change measurement noise, update rate, and target separation. Add velocity or amplitude information to the association cost.

## What this should teach

Ambiguous geometry can cause coalescence or track swaps; richer state and measurement features reduce ambiguity but do not eliminate it.

## Completion condition

You can produce a repeatable identity swap and show one modification that lowers its probability.

## Start or implement

```bash
./bin/learn start 59
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P59` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Track Crossing Targets and Observe Association Failure". The guiding question is: "Why do simple nearest-neighbor trackers swap identities?" Use this experiment: Simulate two targets crossing in position with similar velocities and noisy detections. Have me perform these actions: Run nearest-neighbor association and display identity history. Change measurement noise, update rate, and target separation. Add velocity or amplitude information to the association cost. The main concept I must learn is: Ambiguous geometry can cause coalescence or track swaps; richer state and measurement features reduce ambiguity but do not eliminate it. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
