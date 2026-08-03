# P28: Connect Thresholds to ROC Curves and Estimator Limits

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Implemented by governed batch `P28`

## Guiding question

How do false alarms, detections, bias, variance, and theoretical bounds relate?

## Experiment

Detect a known pulse in real additive white Gaussian noise while also estimating
its amplitude over many independent target-absent and target-present trials.
The script forms the matched-filter statistic explicitly, sweeps a normalized
threshold to form an empirical and analytic ROC, then sweeps matched-filter SNR
and compares amplitude-estimator bias and variance with the Cramer-Rao lower
bound for the stated known-timing model.

## Procedure

1. Inspect the known signed pulse, one target-absent record, one target-present
   record, and their matched-filter statistic distributions.
2. Sweep only the decision threshold and choose an operating point from the
   resulting `P_D` versus `P_FA` curve.
3. Sweep matched-filter SNR by changing only noise scale on one fixed
   standardized-noise bank while amplitude and pulse energy stay fixed. Compare
   empirical amplitude bias, variance, RMSE, and the stated CRLB.
4. Deliberately estimate amplitude only for threshold-crossing records. Observe
   the positive selection bias, then recover by estimating from all independent
   target-present records.

## What this teaches

Detection is a trade between probability of detection and false alarm; the ROC
describes the available trade, while the operating threshold encodes a mission
choice. Estimation accuracy is a separate statistical question. For the
unbiased amplitude estimator used here, variance falls as coherent signal
energy grows or noise power falls and meets the bound under the exact Gaussian,
known-waveform model. In this fixed-amplitude sweep, lower noise also means
higher SNR; raising SNR only by raising the unknown amplitude would improve
relative error without lowering this estimator's absolute variance bound.
Conditioning the estimates on detection changes the population and can create
bias even though the unconditioned estimator is unbiased.

## Prerequisites and dependencies

- P27 supplies the independent-trial and finite-Monte-Carlo discipline.
- P08 supplies correlation intuition; P24 supplies the matched-filter view.
- Base MATLAB only. No Statistics and Machine Learning, Communications, Radar,
  file, network, device, or external-data dependency is used.
- The experiment uses real noise with per-sample variance `noise_std^2`; it does
  not mix real and complex SNR conventions.

## Completion condition

You can choose an operating point on the ROC, explain why lowering the
threshold raises both `P_D` and `P_FA`, distinguish estimator bias from variance
and RMSE, and explain why more signal information lowers the variance bound.

## Run the lesson

```bash
./bin/learn start 28
```

Then run the experiment from the repository root:

```matlab
run('modules/28-connect-thresholds-to-roc-curves-and-estimator-limits/experiment.m')
```

Then follow [walkthrough.md](walkthrough.md) and use [checks.md](checks.md) for
the teach-back.

## Files

- `README.md` — canonical question, experiment, procedure, learning goal, and
  completion condition
- `experiment.m` — seeded baseline, threshold ROC, SNR/CRLB sweep, broken
  selection case, recovery, plots, assertions, and retained `results`
- `lesson.md` — physical/statistical model, equations, limits, and radar meaning
- `walkthrough.md` — guided observations and controlled changes
- `checks.md` — observation, prediction, interpretation, recovery, and
  teach-back checks

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Use the implemented P28 artifacts
to guide one plot or processing transition at a time. Begin with the question
“How do false alarms, detections, bias, variance, and theoretical bounds
relate?”, give a short physical model of overlapping matched-filter statistic
distributions, inspect the baseline, and ask one concrete observation question.
Tie each threshold change to both `P_FA` and `P_D`, and each fixed-amplitude
noise/SNR change to Fisher information and the stated amplitude CRLB rather
than MATLAB syntax.
Include the detected-only selection-bias failure, correct any claim that an ROC
selects mission costs or that every estimator must equal this CRLB, and finish
with the teach-back in `checks.md`.
