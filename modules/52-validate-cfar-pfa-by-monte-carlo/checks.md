# Checks: validate the probability claim, not just the plot

## Observation checks

1. How many H0 CUTs were tested, how many baseline alarms occurred, and does
   their ratio equal `results.baseline_measured_pfa`?
2. Does the requested `Pfa` sweep follow exact homogeneous theory within its
   reported uncertainty? Which point has the largest relative interval?
3. When `N` changes from 8 to 64 and alpha is recalibrated each time, does
   measured Pfa systematically fall, or remain near the common request?
4. Which model-mismatch bar is conservative and which overspends? Explain each
   direction from the relationship between CUT and training powers.
5. What are the broken measured and exact probabilities, and which multiplier
   restores the requested operating point?

## Prediction checks

1. If independent trial count is multiplied by 100, by about what factor
   should a typical confidence width shrink?
2. If total `N` grows without bound under homogeneous independent exponential
   noise, what does alpha approach and what happens to achieved Pfa?
3. If log-texture standard deviation moves toward zero, which model does the
   compound-power case approach?
4. If edge CUTs without complete reference cells are added to the denominator
   but no valid decision is made for them, is the reported Pfa biased high or
   low?
5. Can a narrow Wilson interval distinguish correct scaling from a wrong
   clutter model by itself? Why not?

## Interpretation checks

- Correct: `Pfa_hat = false alarms / valid tested H0 CUTs`.
- Correct: the finite-`N` CA multiplier exactly targets homogeneous
  exponential Pfa in theory; Monte Carlo fluctuates around it.
- Correct: changing `N` requires recalibration even when requested Pfa stays
  fixed.
- Correct: the Wilson interval describes finite independent-trial counting
  uncertainty, conditional on the experiment's stationarity assumptions.
- Correct: correlation and texture are separate model changes; their
  departures need not have the same sign.
- Incorrect: every non-target plot from a target-filled scene belongs in a
  clean H0 Pfa estimate.
- Incorrect: more training cells should always reduce false alarms.
- Incorrect: reusing `-log(Pfa)` on a finite training mean is conservative.
- Incorrect: matching a seeded synthetic model validates measured clutter,
  RF hardware, or operational performance.

## Deterministic audit targets

- The reviewed run uses seed 5201, 200,000 tested CUTs, baseline `N=24`, and
  requested `Pfa=1e-3`.
- Exact homogeneous calibration is
  `(1 + alpha/N)^(-N) = Pfa` with
  `alpha = N*(Pfa^(-1/N)-1)`.
- The broken exact rate is
  `(1 + (-log(Pfa))/N)^(-N)`, greater than the request for finite `N`.
- The experiment is bounded by 55,000,000 generated random real values,
  1,000,000 peak stored numeric values, 3,000,000 threshold comparisons, and
  five figure groups.

## Completion checklist

- [ ] I counted only valid noise-only CUT decisions.
- [ ] I reported an alarm count, tested count, rate, and confidence interval.
- [ ] I explained why requested-Pfa and training-count sweeps stay calibrated
      under the homogeneous model.
- [ ] I explained the correlated and compound-lognormal departures without
      generalizing their direction to every clutter model.
- [ ] I identified the broken infinite-training multiplier and finite-`N`
      recovery.
- [ ] I kept simulation claims separate from hardware, field, and operational
      validation.

## Short teach-back rubric

In two or three sentences, answer the guiding question. A complete answer says
that the implemented finite-`N` CA detector matches requested Pfa within
Monte Carlo uncertainty for independent homogeneous exponential power,
defines the false-alarm numerator and valid-H0 denominator, and explains that
wrong scaling, correlation, or heavy-tailed texture can move achieved Pfa even
when the request printed by the code does not change.
