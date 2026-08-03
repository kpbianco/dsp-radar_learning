# P43 checks: Use a Fixed Detection Threshold

Guiding question: **Why does a threshold that works in one noise level fail in another?**

Use Figures 1–5 and the `results` structure. Answer in terms of distributions,
units, and conditioned events rather than MATLAB syntax.

## Observation checks

1. What distinguishes a false alarm, a detection, and a miss in Figure 1?
2. Which distribution supplies the denominator for `P_FA`?
3. How close is the baseline empirical `P_FA` to the 1% design value?
4. What happens to false-alarm count as noise RMS rises with the threshold
   fixed?
5. What happens to missed-target count in the same noise sweep?
6. What happens to H0 crossings as the positive clutter pedestal rises?
7. Which curve in Figure 5 appears constant, and what hidden information did
   it use?
8. Which retained result proves exact recovery of the fixed decisions?

## Interpretation checks

1. Why is the one-sided real-Gaussian formula
   `Q(gamma/sigma)` appropriate here but not for magnitude or power?
2. Why must false alarms be counted only on target-absent trials?
3. Why does a fixed native-unit threshold correspond to fewer noise standard
   deviations when noise RMS increases?
4. Why can a positive clutter pedestal increase both detections and false
   alarms without improving discrimination?
5. How do the noise-RMS and clutter-pedestal sweeps break calibration by
   different mechanisms?
6. Why is dividing each case by its true RMS adaptive even though the
   normalized threshold number stays constant?
7. Why are common standardized noise samples useful for a one-variable sweep?
8. Why is a single range profile inadequate for validating a 1% false-alarm
   probability?

## Prediction checks

1. If noise RMS approaches zero while `0 < gamma < A`, what do `P_FA` and
   `P_miss` approach?
2. If noise RMS becomes very large while threshold and target amplitude remain
   finite, what do the one-sided H0 and H1 crossing probabilities approach?
3. If the detector used `abs(x) > gamma`, how would the H0 false-alarm formula
   change for zero-mean real Gaussian noise?
4. If RMS doubles, by what factor does Gaussian noise variance increase?
5. If a large positive pedestal pushes both H0 and H1 far above the threshold,
   can threshold crossings still separate targets from background?
6. If the threshold were multiplied by the actual local RMS, would it still be
   a fixed amplitude threshold?

## Failure, recovery, isolation, and resource checks

1. Verify `results.broken_fixed_threshold_claim == false` and explain why.
2. Verify `results.recovery_exact == true`; distinguish recomputation from
   simply copying the original result.
3. Explain why private seed `4301` makes a clean rerun deterministic without
   changing MATLAB's caller-global random stream.
4. Explain what `Ctrl+C` can leave behind and why no external rollback is
   needed.
5. Confirm controls are validated before random draws, allocation, or figure
   creation and that trials, cells, sweep cases, figures, and stored numeric
   values have fixed ceilings.
6. State the repository rollback boundary without changing P42, P44, later
   modules, `.learning/`, or `contracts/active-batch.yaml`.

## Completion checklist

- [ ] I can state the H0 and H1 amplitude models and threshold units.
- [ ] I can keep false-alarm, detection, and miss denominators separate.
- [ ] I can explain why larger noise RMS raises false alarms and misses here.
- [ ] I can distinguish a background mean shift from a variance change.
- [ ] I can identify hidden normalization as adaptation rather than a fixed
      threshold.
- [ ] I can explain the exact deterministic recovery and resource bounds.
- [ ] I can connect fixed-threshold failure to later ROC and CFAR modules.

## Answer key

1. A false alarm is an H0 cell above the line, a detection is an H1 cell above
   it, and a miss is an H1 cell below it.
2. Target-absent H0 trials only.
3. Within the script's 0.01 absolute-probability finite-trial tolerance of the
   0.01 design value and Gaussian model.
4. It rises monotonically.
5. It rises monotonically for this fixed positive target with `A > gamma`.
6. It rises because the H0 distribution moves toward and past the line.
7. The hidden-adaptation curve; it uses each case's true noise RMS.
8. `results.recovery_exact`.
9. The statistic is signed real amplitude with a known positive target, so H0
   has one upper Gaussian tail. Absolute value has two tails; complex magnitude
   and power have different distributions.
10. `P_FA` is the probability of deciding target present under H0. Mixing H1
    trials changes the event and denominator.
11. `gamma/sigma` decreases, so a larger upper fraction of H0 exceeds gamma.
12. It moves both populations upward; more true targets cross, but more
    background crosses too.
13. Noise changes spread; the pedestal changes mean.
14. The effective amplitude threshold becomes proportional to the case RMS.
15. They isolate scaling from random-realization differences and make crossing
    sets nested.
16. Four targets and 252 noise cells have too much rare-event sampling
    uncertainty; repeated conditioned trials are needed.
17. Both approach zero because H0 collapses below gamma and H1 above gamma.
18. Both crossing probabilities approach one half.
19. It becomes `2Q(gamma/sigma)` for a positive gamma.
20. Four.
21. No. Both hypotheses cross almost always, so the decisions lose
    discrimination.
22. No. It is an adaptive native-unit threshold.

## Short teach-back rubric

A complete teach-back should say, in about one minute:

- the detector compares a real positive-polarity amplitude with one fixed
  native-unit threshold;
- false alarms are H0 crossings, while detections and misses are H1 outcomes;
- increasing background spread or shifting its mean changes where one absolute
  threshold lies relative to H0, so its false-alarm probability drifts;
- normalizing with the current background can stabilize the rate, but that is
  adaptation and must be modeled and validated explicitly rather than called a
  fixed threshold.
