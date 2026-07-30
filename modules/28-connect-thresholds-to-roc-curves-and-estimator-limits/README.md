# P28: Connect Thresholds to ROC Curves and Estimator Limits

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Scaffolded; implementation batch `P28` is pending

## Guiding question

How do false alarms, detections, bias, variance, and theoretical bounds relate?

## Experiment

Detect a known tone or pulse in Gaussian noise while also estimating its amplitude or delay over many trials.

## Procedure

Sweep the detector threshold to form an ROC curve. For the estimator, sweep SNR and compare empirical bias/variance with a simple Cramer-Rao-style lower bound or high-SNR scaling law.

## What this should teach

Detection is a trade between probability of detection and false alarm; estimation accuracy has limits set by SNR, bandwidth, and observation time.

## Completion condition

You can choose an operating point on the ROC and explain why estimator variance falls with more signal information.

## Start or implement

```bash
./bin/learn start 28
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P28` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Connect Thresholds to ROC Curves and Estimator Limits". The guiding question is: "How do false alarms, detections, bias, variance, and theoretical bounds relate?" Use this experiment: Detect a known tone or pulse in Gaussian noise while also estimating its amplitude or delay over many trials. Have me perform these actions: Sweep the detector threshold to form an ROC curve. For the estimator, sweep SNR and compare empirical bias/variance with a simple Cramer-Rao-style lower bound or high-SNR scaling law. The main concept I must learn is: Detection is a trade between probability of detection and false alarm; estimation accuracy has limits set by SNR, bandwidth, and observation time. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
