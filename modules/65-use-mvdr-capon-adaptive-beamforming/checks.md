# P65 checks: Constraint, Covariance, Nulls, and Robustness

Guiding question: How can a beamformer place data-dependent nulls on interference?

## Observation checks

1. **Covariance structure:** Why are off-diagonal entries visible?
   - **Correct:** plane waves impose repeatable phase relationships between sensors.
   - **Incorrect:** spatially white receiver noise is perfectly correlated.

2. **Dominant eigenvalue:** What creates it in the baseline?
   - **Correct:** the strong interferer dominates one spatial covariance direction.
   - **Incorrect:** the desired look constraint is already encoded in `Rhat`.

3. **Desired response:** Why do both baseline patterns reach `0 dB` at `3 deg`?
   - **Correct:** both weights are normalized for unit complex response there.
   - **Incorrect:** every beamformer has unit response at every source.

4. **Adaptive null:** Why is the MVDR interferer response deeper?
   - **Correct:** minimizing measured output power favors suppressing the strong covariance direction.
   - **Incorrect:** the code directly commands a null at the known interferer angle.

5. **Output bars:** What should MVDR reduce most strongly?
   - **Correct:** interference output while preserving desired output.
   - **Incorrect:** desired power, because it is weaker than the interferer.

6. **Finite snapshots:** Why does null depth fluctuate in the sweep?
   - **Correct:** each prefix gives a different-quality sample covariance estimate.
   - **Incorrect:** physical element spacing changes at every point.

## Prediction checks

7. **Move the interferer:** What should move if new stationary data are collected?
   - **Correct:** the learned adaptive null should follow its new covariance direction.
   - **Incorrect:** the hard desired constraint must move with it.

8. **More snapshots:** What improves under a stationary model?
   - **Correct:** covariance evidence generally stabilizes.
   - **Incorrect:** the ULA aperture becomes physically longer.

9. **Too few snapshots:** What happens when `L<M` without loading?
   - **Correct:** sample covariance rank is at most `L`, so a unique stable inverse is unavailable.
   - **Incorrect:** the covariance automatically becomes the identity.

10. **Increase loading from tiny to moderate:** What can improve under mismatch?
    - **Correct:** true-direction response, weight robustness, and output SINR.
    - **Incorrect:** the algorithm discovers the true angle without a model change.

11. **Very large loading:** What limiting behavior appears?
    - **Correct:** weights approach the conventional steering solution.
    - **Incorrect:** infinitely many arbitrarily deep nulls appear.

12. **Increase interferer power:** What new evidence does covariance emphasize?
    - **Correct:** the interferer's spatial direction becomes more costly in output power.
    - **Incorrect:** the desired steering vector changes sign.

## Interpretation checks

13. **Core objective:** What does MVDR minimize?
    - **Correct:** `w^H Rhat w` subject to one distortionless response constraint.
    - **Incorrect:** angular error from a known interferer label.

14. **Constraint:** What does `w^H a0=1` protect?
    - **Correct:** the assumed steering vector `a0`.
    - **Incorrect:** every possible desired steering mismatch near `a0`.

15. **Normalization:** Why divide `q` by `a0^H q`?
    - **Correct:** to enforce unit response after solving the covariance system.
    - **Incorrect:** to convert radians to degrees.

16. **Linear solve:** Why use `Rloaded\a0` instead of an explicit inverse?
    - **Correct:** the desired operation is solving one linear system more stably and directly.
    - **Incorrect:** backslash hides a phased-array toolbox beamformer.

17. **Data dependence:** What changes MVDR weights while conventional weights stay fixed?
    - **Correct:** a change in the estimated covariance scene.
    - **Incorrect:** only the plot color order.

18. **SINR accounting:** Why evaluate known synthetic components separately?
    - **Correct:** to distinguish desired preservation, interference rejection, and noise gain.
    - **Incorrect:** to use the finite output record as perfect ground truth.

19. **White-noise gain:** What does small `w^H w` mean?
    - **Correct:** less output power from unit spatially white sensor noise.
    - **Incorrect:** the interferer angle is exactly known.

20. **Capon naming:** What is shared with a Capon spatial scan?
    - **Correct:** covariance-inverse constrained steering mathematics.
    - **Incorrect:** this lesson already implements MUSIC subspace peaks.

## Broken case and recovery checks

21. **Self-nulling:** Why can the true desired source be suppressed?
    - **Correct:** it appears in training covariance but lies outside the wrong hard constraint.
    - **Incorrect:** the source samples were deleted from the scene.

22. **Broken promise:** What direction is still preserved exactly?
    - **Correct:** the incorrect assumed `6 deg` direction.
    - **Incorrect:** the true `3 deg` direction automatically.

23. **Loaded stage:** What changes?
    - **Correct:** only the diagonal loading applied to the same covariance and wrong steering model.
    - **Incorrect:** the desired source is regenerated at `6 deg`.

24. **Recovered stage:** What changes?
    - **Correct:** the assumed steering vector is restored to the true `3 deg` on unchanged data.
    - **Incorrect:** the covariance is tuned until a desired answer appears.

25. **Loading limitation:** What can loading not prove?
    - **Correct:** that the assumed steering direction or array calibration is correct.
    - **Incorrect:** that the weight norm is bounded.

## Lifecycle, compatibility, and resource checks

26. **Malformed input:** What happens to NaN powers, noninteger snapshots, unordered grids, duplicate loads, or oversized requests?
    - **Correct:** validation rejects them before reviewed arrays and plots are built.
    - **Incorrect:** the script silently sorts, rounds, or allocates without limit.

27. **Timeout and cancellation:** What remains after `Ctrl+C`?
    - **Correct:** no worker, file, checkpoint, or background process; rerun reconstructs the experiment.
    - **Incorrect:** covariance adaptation keeps running asynchronously.

28. **Isolation:** What does startup cleanup affect?
    - **Correct:** only figures tagged `P65`, without resetting global RNG.
    - **Incorrect:** every MATLAB figure and random stream.

29. **Resource bound:** What are the fixed ceilings?
    - **Correct:** 16 elements, 512 snapshots, 1,001 scan samples, eight sweep cases, 30,000 private values, 600,000 working values, and five figures.
    - **Incorrect:** matrix size grows until every interferer can be nulled.

30. **Rollback:** What canonical state changes if P65 is reverted?
    - **Correct:** only P65 returns to `scaffolded`; P64, later identities, and learner state remain preserved.
    - **Incorrect:** all Phase 7 modules and learner progress are deleted.

31. **Future compatibility:** What may permanent P65 tests assume?
    - **Correct:** P64 remains implemented and P65 keeps its identity; shared tests derive the moving frontier.
    - **Incorrect:** P65 must forever be the latest implemented module.

32. **Claim boundary:** What do repository checks prove?
    - **Correct:** bounded artifacts and an independent simulated model, not MATLAB rendering, antenna, HIL, field, or production behavior.
    - **Incorrect:** Python tests validate an operational adaptive array.

## Completion checklist

- [ ] I traced snapshots through `Rhat`, loading, the linear solve, and normalization.
- [ ] I explained why the MVDR null depends on measured covariance.
- [ ] I compared null depth, white-noise gain, and output SINR.
- [ ] I separated snapshot evidence from physical aperture.
- [ ] I diagnosed self-nulling caused by a mismatched hard constraint.
- [ ] I explained what loading repairs and what only model correction repairs.

## Short teach-back rubric

In two or three sentences, explain how MVDR uses the sample covariance to
minimize output power while its normalization preserves one assumed steering
vector, allowing strong interference to drive a data-dependent null. A
complete answer must also say why finite snapshots and steering mismatch can
cause instability or self-nulling, and why diagonal loading trades ideal
adaptivity for robustness rather than discovering the correct steering model.
