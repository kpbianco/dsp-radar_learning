# P60 checks: explain how an IMM adapts without knowing target intent

Guiding question: **How can a tracker adapt when the target alternates between straight motion and maneuvers?**

## Observation checks

1. **Truth boundary:** What information enters both trackers?
   - **Correct:** the same noisy east/north position report at each scan.
   - **Incorrect:** the truth maneuver flag and acceleration schedule.

2. **Fixed-model lag:** Why does the orange estimate miss the curved parts?
   - **Correct:** its zero-acceleration transition is poorly matched to a
     persistent acceleration burst.
   - **Incorrect:** Kalman filters cannot track any moving target.

3. **Probability timing:** Must maneuver probability jump on the first burst
   scan?
   - **Correct:** no; acceleration is inferred from a sequence of noisy
     positions and the transition prior supplies inertia.
   - **Incorrect:** yes; the tracker reads the truth regime immediately.

4. **Model-conditioned estimates:** Why do two filters produce different
   states from one report?
   - **Correct:** their prediction matrices and process covariances create
     different priors and gains.
   - **Incorrect:** each filter receives a different noise realization.

5. **Baseline completion:** What two reviewed comparisons matter?
   - **Correct:** maneuver probability averages higher during maneuvers, and
     IMM overall/maneuver RMSE is lower than the fixed straight model.
   - **Incorrect:** maneuver probability must equal one on every maneuver scan.

## Prediction checks

6. **Stronger burst:** What should happen when only acceleration magnitude
   grows?
   - **Correct:** fixed-model lag grows and the maneuver explanation becomes
     easier to distinguish on average.
   - **Incorrect:** transition probabilities stop mattering entirely.

7. **Higher persistence:** What happens as stay probability approaches one?
   - **Correct:** dominant-mode chatter falls, but adaptation to a real regime
     change can slow.
   - **Incorrect:** likelihood instantly overrides the stronger prior.

8. **Large measurement noise:** What happens to model discrimination?
   - **Correct:** normalized likelihoods generally separate less, so transition
     priors carry more influence.
   - **Incorrect:** noisy reports reveal acceleration more precisely.

9. **Identical models:** If `F` and `Q` are identical for both modes, what
   motion distinction remains?
   - **Correct:** none in their conditioned state predictions; priors and
     numerical symmetry determine equal evidence.
   - **Incorrect:** the mode names alone make one a maneuver tracker.

10. **Missing model:** Can an IMM infer a turn law that no supplied model can
    represent well?
    - **Correct:** no; it can weight only the explanations in its bank.
    - **Incorrect:** interaction automatically invents a new dynamic model.

## Interpretation and algorithm checks

11. **Interaction:** What is mixed before each model predicts?
    - **Correct:** source states and covariances, using transition-conditioned
      probabilities.
    - **Incorrect:** truth trajectories and raw report coordinates.

12. **Covariance spread:** Why include `(x_i-x0_j)(x_i-x0_j)^T`?
    - **Correct:** disagreement between source estimates is uncertainty in the
      mixed prior.
    - **Incorrect:** it forces covariance to zero when models disagree.

13. **Likelihood:** What does normalized innovation squared measure?
    - **Correct:** squared report surprise relative to the model's innovation
      covariance.
    - **Incorrect:** Euclidean error with no uncertainty scale.

14. **Combination:** Does the largest probability model supply the complete
    IMM estimate?
    - **Correct:** no; all conditioned states and covariances are weighted.
    - **Incorrect:** yes; every scan is a hard mode switch.

15. **Probability meaning:** Is `mu_maneuver = 0.8` an 80% physical certainty
    that the target operator chose a maneuver?
    - **Correct:** no; it is posterior weight within this assumed model bank.
    - **Incorrect:** yes; it is a calibrated target-intent sensor.

16. **Numerical operation:** Why does the script use a linear solve and log
    likelihood?
    - **Correct:** the solve avoids explicit inversion, and shifted log weights
      avoid likelihood underflow during normalization.
    - **Incorrect:** they change the underlying Bayesian rule.

## Broken case and recovery checks

17. **Unreachable mode:** Why does maneuver probability remain zero?
    - **Correct:** it begins at zero and identity transitions provide no path
      from the supported straight mode.
    - **Incorrect:** the maneuver filter sees no measurements.

18. **Recovery:** What two supports are restored?
    - **Correct:** positive initial maneuver probability and positive
      off-diagonal transition probability.
    - **Incorrect:** truth acceleration is injected into the filter.

19. **Exact recovery:** Why compare exact arrays?
    - **Correct:** it proves configuration recovery on identical reports rather
      than a favorable new random record.
    - **Incorrect:** it proves operational radar performance.

## Safety, resource, compatibility, and lifecycle checks

20. **Malformed input:** What happens to a NaN noise scale, non-stochastic
    transition row, or probability vector that does not sum to one?
    - **Correct:** validation rejects it before bounded processing or figures.
    - **Incorrect:** the tracker silently clips and renormalizes every input.

21. **Resource bound:** What bounds the reviewed experiment?
    - **Correct:** 60 scans, at most five cases per sweep, six reviewed cases,
      1,500 model updates, 120 private Gaussian values per scene, 480 total,
      and six figures.
    - **Incorrect:** a background tracker runs until manually stopped.

22. **Cancellation:** What should you do after Ctrl+C?
    - **Correct:** close only `P60` figures if needed and rerun from the top;
      private seeds reconstruct the same arrays.
    - **Incorrect:** resume a hidden partial state file.

23. **Timeout and isolation:** What protects learner state in CLI tests?
    - **Correct:** a temporary repository and `HOME` plus a 10-second subprocess
      timeout.
    - **Incorrect:** tests edit the repository's personal `.learning/` file and
      restore it later.

24. **Rollback:** What canonical data changes during rollback?
    - **Correct:** only P60 returns to `scaffolded`; P59 and learner progress are
      preserved.
    - **Incorrect:** all later module identities are deleted.

25. **Compatibility:** What permanent frontier fact may P60 tests assert?
    - **Correct:** P59 is implemented and P60 retains its canonical identity;
      the shared test derives any later frontier from the manifest.
    - **Incorrect:** P60 must remain the latest implemented module and P61 must
      stay scaffolded forever.

26. **Dependencies:** What does P60 reuse?
    - **Correct:** P55's Kalman mechanics and P59's audit/truth boundary, with
      P59 as the contractual prerequisite.
    - **Incorrect:** an unexplained toolbox IMM object.

27. **Claim boundary:** What do repository tests establish?
    - **Correct:** static structure and an independent bounded numerical oracle,
      not MATLAB runtime, hardware/HIL, field, or production results.
    - **Incorrect:** Python tests prove rendered MATLAB figures and real-time
      radar safety.

## Completion checklist

- [ ] I traced interaction, two conditioned Kalman updates, likelihood, mode
  update, and state/covariance combination.
- [ ] I explained why maneuver probability responds after evidence accumulates.
- [ ] I compared IMM and fixed-model position RMSE in straight and maneuver
  regimes.
- [ ] I interpreted both one-variable sweeps without claiming a universal best
  persistence.
- [ ] I explained why zero probability plus zero transition support is
  unrecoverable.
- [ ] I recovered exactly on the unchanged measurement record.

## Short teach-back rubric

In two or three sentences, explain how transition-conditioned mixing keeps both
motion explanations connected, how normalized innovation likelihood moves
probability during an acceleration burst, and why the combined estimate can
beat a fixed straight model without knowing truth intent. A complete answer
also names the zero-support failure and the persistence-versus-responsiveness
trade.
