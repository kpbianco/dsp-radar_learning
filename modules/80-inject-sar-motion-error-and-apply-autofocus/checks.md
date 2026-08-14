# P80 checks: Motion Error, Coherence, and Autofocus

The guiding question is: **How small a platform-position error is enough to blur a coherent image?**

Use these after observing the figures. Answers are included so the checks test
radar interpretation rather than MATLAB recall.

## Baseline observation checks

1. **What carrier and wavelength does the baseline use?**

   **Answer:** `10 GHz` and `30 mm`.

2. **What is the baseline line-of-sight error RMS?**

   **Answer:** `lambda/8 = 3.75 mm`.

3. **What two-way phase RMS does `lambda/8` path RMS create?**

   **Answer:** `4 pi (lambda/8)/lambda = pi/2 rad`.

4. **Why is the factor `4 pi` rather than `2 pi`?**

   **Answer:** The monostatic wave travels the range error outbound and again
   on return.

5. **Which metric exposes coherent loss even though every image is
   peak-normalized for display?**

   **Answer:** Peak retention relative to the ideal focused gate.

6. **What does increasing cross-range-cut entropy mean in this experiment?**

   **Answer:** Focused energy has spread over more cross-range hypotheses.

7. **What stays identical between ideal, blurred, and corrected baseline
   comparisons?**

   **Answer:** Scene, noise realization, aperture samples, bandwidth, planned
   geometry, image grid, and display settings.

8. **What changes before the blurred focus?**

   **Answer:** A common aperture-varying phase screen multiplies the ideal
   target signals; the receiver noise realization is retained.

## Interpretation and prediction checks

9. **Predict the two-way phase RMS for `lambda/16` path error.**

   **Answer:** `pi/4 rad`.

10. **Predict the physical RMS at `lambda/32` for this carrier.**

    **Answer:** `30/32 = 0.9375 mm`.

11. **Does a constant nonzero phase error blur magnitude?**

    **Answer:** No. It rotates every aperture phasor equally.

12. **What does a pure linear aperture-phase ramp usually do before higher
    order terms are considered?**

    **Answer:** It steers or shifts the cross-range image.

13. **Which component guarantees defocus in this lesson?**

    **Answer:** Aperture-varying nonlinear/irregular residual phase that prevents
    the true-pixel phasors from sharing one direction.

14. **Why is range resolution `c/(2B)` not the motion-error tolerance?**

    **Answer:** Range resolution comes from waveform bandwidth; coherent motion
    sensitivity is tied to carrier wavelength and phase variation.

15. **Should `lambda/16` be quoted as a universal SAR tolerance?**

    **Answer:** No. Loss also depends on the error distribution, correlation,
    aperture weighting, scene, SNR, and chosen metric.

16. **Why can two equal-RMS error histories blur differently?**

    **Answer:** Spatial correlation and phase shape determine how energy shifts
    or spreads; RMS alone discards that structure.

17. **What happens if an adjacent phase-gradient step exceeds `pi`?**

    **Answer:** The principal-angle measurement wraps, so simple integration
    follows an aliased gradient.

18. **Does being below `pi` guarantee a good estimate?**

    **Answer:** No. Low SNR, scene contamination, nulls, and model mismatch can
    still corrupt it.

## Autofocus operation checks

19. **What is removed from the strong reference gate before measuring its
    gradient?**

    **Answer:** The nominal planned-path phase for that target.

20. **What explicit quantity is measured between adjacent looks?**

    **Answer:** `angle(z_p conj(z_(p-1)))`.

21. **Why integrate phase differences rather than independently reading each
    wrapped phase?**

    **Answer:** Integration follows a sampled continuous phase path while each
    increment stays inside the unambiguous principal interval.

22. **Why is the estimate allowed to contain an unknown constant?**

    **Answer:** A common constant rotates image phase but does not alter focused
    magnitude.

23. **Where is the estimated correction applied?**

    **Answer:** The same `exp(-j phi_hat_p)` is applied to every retained range
    gate at aperture position `p`.

24. **Why is one correction shared across gates here?**

    **Answer:** The local experiment assumes one range-independent common phase
    screen over the small scene.

25. **Is the estimate a recovered physical navigation trajectory?**

    **Answer:** No. It is scene-derived residual phase with constant/linear and
    model ambiguities.

26. **What is the reference measurement SNR?**

    **Answer:** `35 dB`, using deterministic private noise.

27. **Does the script call a SAR or autofocus toolbox object?**

    **Answer:** No. History synthesis, coherent focus, gradient estimation, and
    correction are explicit base-MATLAB operations.

## Broken-case and recovery checks

28. **What assumption is intentionally broken?**

    **Answer:** The autofocus range gate is no longer dominated by one isolated
    scatterer; it includes `0.95` times a second target history.

29. **Why does the second target bias the estimate after nominal deramping?**

    **Answer:** Its different geometry leaves scene-dependent aperture phase in
    the vector sum, which is mistaken for common motion phase.

30. **Must broken autofocus make the image worse than doing nothing?**

    **Answer:** No. It may partly improve focus, but it materially underperforms
    the valid isolated-gate correction.

31. **What evidence proves recovery is fresh?**

    **Answer:** It starts from the unchanged retained errored history, reruns the
    isolated-gate estimate and focus, and exactly matches the earlier corrected
    result.

32. **Why not sharpen the already broken image?**

    **Answer:** Image-domain cosmetics cannot recover the correct aperture phase
    relationship; recovery must reprocess coherent history.

33. **What persistent state can the broken case corrupt?**

    **Answer:** None. The alternate reference is a bounded in-memory vector.

34. **How do you recover after Ctrl+C?**

    **Answer:** Rerun `experiment.m`; it closes stale P80 figures and rebuilds
    deterministic private state without external writes.

## Limits, compatibility, and evidence checks

35. **Which prerequisite provides the immediate resolution/aperture context?**

    **Answer:** P79; P75-P78 provide phase history, range compression,
    focusing, and migration correction.

36. **Which MATLAB compatibility is declared?**

    **Answer:** Base MATLAB R2016b or newer, because the script uses local
    functions and no optional toolbox.

37. **What is the reviewed operation bound?**

    **Answer:** `4,283,025` scheduled coherent contributions under a
    `4,500,000` ceiling. This includes range-response formation and
    target-to-image accumulation.

38. **Does the experiment write files or use network, workers, timers, GPU,
    or shell processes?**

    **Answer:** No.

39. **What does static validation prove?**

    **Answer:** Repository structure, declared contracts, source markers, and
    independent deterministic oracle behavior—not MATLAB execution.

40. **What validation is explicitly not implied?**

    **Answer:** MATLAB runtime when unavailable, physical navigation accuracy,
    hardware/HIL, bench, real-time, field, operational radar, signing,
    deployment, and production validation.

41. **What does repository rollback change?**

    **Answer:** Remove only P80-owned artifacts/test/evidence and restore only
    P80's manifest status to `scaffolded`, preserving P79, future entries,
    learner state, and operator-managed contracts.

## Short teach-back rubric

A completion-ready explanation should include all of these:

- convert one-way path error to monostatic two-way phase with
  `delta phi = -4 pi delta R/lambda`;
- distinguish constant rotation and linear shift from nonlinear/irregular
  defocus;
- explain why peak retention and cross-range-cut entropy together reveal lost
  coherence;
- describe nominal deramping, adjacent-gradient integration, and common phase
  correction without calling them a black box;
- state why a strong isolated range gate makes this simplified autofocus
  observable and why a comparable second scatterer biases it;
- explain that recovery reprocesses unchanged coherent history; and
- name at least two limits, such as gradient wrapping, low SNR, wide-scene
  space variance, moving targets, or absolute-location ambiguity.

Do not record personal completion until the learner gives that teach-back and
the module completion check has been run.
