# P60: Use an IMM for a Maneuvering Target

**Phase 6: Radar Tracking and Data Association**  
**Status:** Scaffolded; implementation batch `P60` is pending

## Guiding question

How can a tracker adapt when the target alternates between straight motion and maneuvers?

## Experiment

Simulate a trajectory with constant-velocity segments and coordinated turns or acceleration bursts.

## Procedure

Run separate motion-model filters and combine them with interacting multiple-model probabilities. Plot model probabilities, state error, and compare with one fixed model.

## What this should teach

IMM tracking handles uncertain motion by blending model-conditioned estimates and updating model likelihoods from innovations.

## Completion condition

Model probability rises during the matching motion regime and overall error improves over a single poorly matched model.

## Start or implement

```bash
./bin/learn start 60
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P60` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use an IMM for a Maneuvering Target". The guiding question is: "How can a tracker adapt when the target alternates between straight motion and maneuvers?" Use this experiment: Simulate a trajectory with constant-velocity segments and coordinated turns or acceleration bursts. Have me perform these actions: Run separate motion-model filters and combine them with interacting multiple-model probabilities. Plot model probabilities, state error, and compare with one fixed model. The main concept I must learn is: IMM tracking handles uncertain motion by blending model-conditioned estimates and updating model likelihoods from innovations. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
