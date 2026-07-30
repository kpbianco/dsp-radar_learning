# P47: Measure CFAR Loss

**Phase 5: Detection and CFAR**  
**Status:** Scaffolded; implementation batch `P47` is pending

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

## Start or implement

```bash
./bin/learn start 47
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P47` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Measure CFAR Loss". The guiding question is: "How much extra SNR does adaptive threshold estimation cost?" Use this experiment: Compare an ideal detector using known noise power with CA-CFAR using finite training cells. Have me perform these actions: For a fixed Pfa, use Monte Carlo trials to find Pd versus SNR for both detectors. Repeat with several training-cell counts. The main concept I must learn is: Estimating background power adds uncertainty, causing CFAR loss that shrinks as more representative training data is used. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
