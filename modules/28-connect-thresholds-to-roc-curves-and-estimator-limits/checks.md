# Checks: ROC choices and estimator limits

## Guiding question

How do false alarms, detections, bias, variance, and theoretical bounds relate?

## Observation checks

- In the statistic-distribution plot, identify the H0 area to the right of the
  threshold as false alarms and the H1 area to the right as detections.
- Confirm from `results.roc` that raising `gamma` never increases empirical
  `P_FA` or `P_D`.
- Confirm that the displayed `(1,1)` and `(0,0)` endpoints correspond to the
  all-detect and no-detect infinite-threshold limits.
- At the marked operating point, compare empirical and analytic probabilities
  without demanding exact equality from 12,000 trials.
- Confirm that estimator bias stays near zero while variance and the CRLB fall
  as the fixed-amplitude sweep lowers noise and thereby raises matched SNR.
- Confirm that endpoint histogram bins include Gaussian tails and that both
  displayed probability masses sum to one.

## Prediction checks

- If the threshold is lowered, predict both `P_FA` and `P_D` before reading the
  curve. Both should rise.
- If coherent template energy doubles while real-noise variance stays fixed,
  predict the amplitude CRLB. It halves.
- If trial count increases without changing SNR, predict the physical ROC and
  CRLB versus the uncertainty of their empirical estimates. The model curves
  and bound do not change; Monte Carlo uncertainty shrinks.
- If only detected target records are averaged, predict the amplitude bias. It
  moves positive because thresholding retains upward projected-noise samples.

## Interpretation checks

- Correct: the ROC is a family of threshold operating points for fixed detector
  and SNR. Incorrect: the ROC chooses mission costs automatically.
- Correct: bias, variance, and RMSE are distinct. Incorrect: a small variance
  guarantees a small total error.
- Correct: this estimator attains the amplitude CRLB under the stated
  known-timing real-AWGN model. Incorrect: every estimator at every SNR must
  equal this bound.
- Correct: zero observed events in a finite run is limited evidence. Incorrect:
  it proves zero false-alarm probability.
- Correct: common random numbers isolate a sweep variable. Incorrect: reusing a
  bank creates additional independent trials.

## Failure and recovery checks

- Verify `results.broken.unbiased_claim_valid == false` and explain the changed
  population, not merely the numerical offset.
- Verify the selected empirical bias is close to the stated analytic
  truncated-Gaussian bias.
- Verify recovery uses all H1 trials and exactly reproduces both private-seed
  noise banks.
- If execution is cancelled with `Ctrl+C`, re-run the whole script. Do not use
  partial workspace variables as evidence.

## Resource, isolation, and compatibility checks

- The canonical bounds are 12,000 trials per hypothesis, 16 samples, nine
  threshold cases, seven estimator-SNR cases, five P28 figure groups, and at
  most 2,500,000 conservatively counted numeric values.
- The experiment uses no worker, timer, file, network, device, or external
  transaction and does not write `.learning/`.
- It uses a private seed rather than MATLAB's global random state and closes
  only figures tagged `P28`.
- It is base MATLAB and keeps the matched filter, Gaussian-tail reference,
  estimator, Fisher information, CRLB, and failure condition visible.

## Completion checklist

- [ ] I can choose an ROC operating point and name the competing costs.
- [ ] I can explain why one threshold changes both `P_FA` and `P_D`.
- [ ] I can distinguish estimator bias, variance, and RMSE.
- [ ] I can distinguish lower-noise/coherent-energy improvements in the
      absolute CRLB from an amplitude-only SNR increase that improves relative
      error.
- [ ] I can explain why detected-only estimation is conditionally biased.
- [ ] I can state that this synthetic static/runtime boundary is not hardware,
      field, or operational-radar validation.

## Short teach-back rubric

A complete two- or three-sentence teach-back says: (1) how threshold movement
trades false alarms against detections, (2) why more signal information lowers
the amplitude-estimator variance bound under the stated model, and (3) why
conditioning estimates on detections creates selection bias. Personal
completion still requires this human explanation; repository checks cannot
prove it.
