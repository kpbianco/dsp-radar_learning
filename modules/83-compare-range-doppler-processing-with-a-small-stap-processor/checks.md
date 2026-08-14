# P83 checks: Interpret the Range-Doppler and STAP Comparison

## Guiding question

When is Doppler filtering alone insufficient against clutter?

Use these after observing the figures. Answers are included so the conversation
can correct interpretation directly rather than become a syntax quiz.

## Baseline observation checks

1. **What is one data snapshot in P83?**

   **Answer:** The already range-compressed complex samples from 4 array
   elements over 8 coherent pulses at one relative range cell.

2. **Do the two processors receive different apertures or CPIs?**

   **Answer:** No. Both receive the same 4-by-8 samples.

3. **What does the conventional processor do?**

   **Answer:** It applies one fixed 12-degree spatial beam and then a bank of
   slow-time Doppler matched filters.

4. **Why call it insufficient if it already uses a beam?**

   **Answer:** The beam is fixed and separable; it cannot adapt its spatial
   response differently along the coupled clutter ridge at each Doppler.

5. **Where is the target?**

   **Answer:** Range cell 25, actual angle `12.5 deg`, and normalized Doppler
   `0.125 cycles/pulse`; the map's nearest assumed Doppler is `0.120`.

6. **Which baseline map has the target as its global maximum?**

   **Answer:** The clean small-STAP adaptive map.

7. **What dominates the conventional map?**

   **Answer:** Finite-record moving-platform clutter cells inside the broad
   fixed beam and Doppler responses.

8. **Does one bright adaptive-map cell prove detection performance?**

   **Answer:** No. It is one deterministic normalized-power realization without
   a calibrated threshold or false-alarm experiment.

## Ridge and steering checks

9. **Why is stationary ground not all at zero Doppler?**

   **Answer:** Platform motion gives different ground look directions different
   radial velocities and thus different pulse-to-pulse phase slopes.

10. **What is the ridge equation here?**

    **Answer:** `nu_c(theta) = 2*v_p*sin(theta)/(lambda*PRF)`.

11. **What is the reviewed ridge slope?**

    **Answer:** `0.30 cycles/pulse per sin(angle)`.

12. **What does `nu = 0.125` mean at a 20 kHz PRF?**

    **Answer:** A Doppler of `2500 Hz` under this sampled phase convention.

13. **What phase order does `kron(doppler, space)` match?**

    **Answer:** All element samples for one pulse, then all elements for the
    next pulse, matching column-wise vectorization of element-by-pulse data.

14. **Why is the target hard even though its angle is known approximately?**

    **Answer:** A four-element fixed beam is broad, and clutter from another
    angle can share the target Doppler.

15. **What happens if target and clutter steering are identical?**

    **Answer:** No linear weight can both preserve and null the same vector.

16. **What happens if platform speed becomes zero?**

    **Answer:** The modeled ground ridge collapses toward zero Doppler.

17. **What disappears with one array element?**

    **Answer:** Spatial discrimination.

18. **What disappears with one pulse?**

    **Answer:** Slow-time Doppler discrimination.

## Covariance and adaptive-operation checks

19. **Where does the sample covariance come from?**

    **Answer:** Thirty-six clean neighboring range snapshots, excluding two
    guard cells on each side of the CUT.

20. **Does the STAP weight use the analytical scene covariance?**

    **Answer:** No. That known covariance only scores simulated component SCNR;
    weights use the realized neighboring-range sample covariance.

21. **What does the outer product `x*x^H` record?**

    **Answer:** Correlation among every element/pulse coordinate for one
    training snapshot.

22. **Why divide the covariance sum by training count?**

    **Answer:** To form the average second-moment estimate over secondary cells.

23. **What does diagonal loading add?**

    **Answer:** A scaled identity that improves numerical and model-mismatch
    robustness; it does not add observed clutter examples.

24. **Why solve instead of form `inv(R)`?**

    **Answer:** The linear solve applies the needed operation more directly and
    avoids an unnecessary explicit inverse.

25. **What does the STAP normalization enforce?**

    **Answer:** Unit response to the assumed target steering vector.

26. **What does the adaptive map normalize?**

    **Answer:** Whitened matched-output power by the assumed steering's loaded-
    covariance response, yielding a dimensionless normalized-power value.

27. **Why keep output SCNR separate from map color?**

    **Answer:** SCNR uses known simulated component powers, while one map also
    contains a particular random clutter/noise realization.

## Sweep prediction checks

28. **What changes in the ridge-offset sweep?**

    **Answer:** Only the target's normalized Doppler distance above its local
    clutter ridge.

29. **Why does STAP improve as ridge offset grows?**

    **Answer:** The target joint steering vector becomes more distinct from the
    learned clutter subspace.

30. **Would a denser plotted Doppler grid create more true resolution?**

    **Answer:** No. The eight observed pulses set the slow-time resolution
    scale; denser trials only interpolate.

31. **What changes in the support sweep?**

    **Answer:** Only how many prefix snapshots from the same clean 36-cell
    record estimate the covariance.

32. **Why is an 8-snapshot, 32-dimensional covariance rank deficient?**

    **Answer:** Eight outer products span at most eight independent directions.

33. **Does a successful loaded solve mean the covariance is accurate?**

    **Answer:** No. Loading ensures invertibility/conditioning, not correct
    subspace estimation.

34. **Is more training always better?**

    **Answer:** No. Nonhomogeneous terrain or targets can provide more examples
    of the wrong covariance.

## Broken-case and recovery checks

35. **What is deliberately corrupted?**

    **Answer:** Twenty-five percent of the neighboring covariance-training
    snapshots receive a strong target-like component.

36. **Does the broken path change the CUT measurement?**

    **Answer:** No. Only the learned covariance changes.

37. **Why does output SCNR collapse despite a distortionless constraint?**

    **Answer:** The constraint preserves `(12 deg, 0.120)`. In this reviewed
    case, desired-target output power changes by only about `-0.62 dB`, while
    known clutter-plus-noise output rises by about `22.86 dB`. The demonstrated
    failure is primarily lost interference rejection, not target self-nulling.

38. **Would exact aligned rank-one contamination necessarily self-null an
    exactly constrained target?**

    **Answer:** No. An exact distortionless constraint preserves that exact
    vector. Desired-response change, residual-interference gain, and adaptive
    normalization must be inspected separately before calling a failure a
    target null.

39. **What is retained for recovery?**

    **Answer:** The untouched clean training matrix and unchanged complete
    range record.

40. **What must exact recovery reproduce?**

    **Answer:** The clean covariance, adaptive map, target weight, SCNR, and
    measurement values.

## Limits, safety, and claim checks

41. **Does STAP improve range resolution in this module?**

    **Answer:** No. Range cells already exist before this processor.

42. **Does STAP add pulses or improve Doppler resolution?**

    **Answer:** No. Both paths use eight pulses; STAP changes interference
    rejection in joint space-time coordinates.

43. **What happens beyond normalized Doppler magnitude 0.5?**

    **Answer:** Slow-time Doppler aliases.

44. **What happens if element spacing exceeds half a wavelength?**

    **Answer:** Spatial aliases/grating responses can repeat.

45. **What persists if Ctrl+C interrupts the run?**

    **Answer:** No module data or external transaction. Rerun rebuilds private
    samples and closes only figures tagged `P83`.

46. **What does static validation prove?**

    **Answer:** Repository structure, source contracts, and independent model
    facts—not MATLAB execution or plotted numerical correctness.

47. **What physical evidence was produced?**

    **Answer:** None; no hardware/HIL, bench, field, real-time, or operational
    radar validation occurred.

48. **What is the rollback boundary?**

    **Answer:** Restore only P83 artifacts and its manifest/catalog state;
    preserve P82, P84 identity/future status, learner state, contracts, and
    unrelated modules.

## Teach-back rubric

A complete short teach-back should say all of the following:

- moving-platform ground creates linked angle and Doppler phase slopes;
- a fixed beam followed by a Doppler filter cannot adapt along that ridge;
- STAP estimates one joint covariance from guarded neighboring range cells and
  whitens the target steering vector;
- ridge overlap, limited support, mismatch, and contaminated training bound the
  benefit;
- STAP changes interference rejection, not the observed aperture, CPI, range
  resolution, or Doppler resolution; and
- the synthetic result is intuition, not operational-radar validation.

Do not mark personal completion from automated checks alone; the learner should
give this teach-back first.
