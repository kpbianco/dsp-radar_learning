# P49: Use Ordered-Statistic CFAR with Interfering Targets

**Phase 5: Detection and CFAR**  
**Status:** Scaffolded; implementation batch `P49` is pending

## Guiding question

How can CFAR resist several contaminated training cells?

## Experiment

Place multiple strong targets close enough that they enter one another's training windows.

## Procedure

Sort training-cell powers and select different rank statistics. Compare OS-CFAR with CA-CFAR as the number and strength of interfering targets changes.

## What this should teach

Order statistics can reject a limited number of high outliers but require choosing a rank matched to expected contamination.

## Completion condition

You can find a rank that preserves the target without allowing excessive false alarms.

## Start or implement

```bash
./bin/learn start 49
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P49` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use Ordered-Statistic CFAR with Interfering Targets". The guiding question is: "How can CFAR resist several contaminated training cells?" Use this experiment: Place multiple strong targets close enough that they enter one another's training windows. Have me perform these actions: Sort training-cell powers and select different rank statistics. Compare OS-CFAR with CA-CFAR as the number and strength of interfering targets changes. The main concept I must learn is: Order statistics can reject a limited number of high outliers but require choosing a rank matched to expected contamination. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
