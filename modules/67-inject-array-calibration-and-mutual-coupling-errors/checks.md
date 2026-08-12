# P67 checks: Calibration, Coupling, and Model Trust

Guiding question: How sensitive are beamforming and DOA results to imperfect channels?

Use these after inspecting the figures and retained `p67_results` metrics.

## Observation checks

1. Do ideal and impaired records use the same source waveforms and receiver noise?
   **Correct:** Yes. Only the array manifold changes.

2. Are the per-element gain, phase, and position profiles deterministic?
   **Correct:** Yes. A private seeded generator freezes them.

3. Does the coupling matrix mix only the same channel?
   **Correct:** No. It includes nearest- and smaller next-nearest-neighbor terms.

4. Is the coupling matrix presented as a full electromagnetic model?
   **Correct:** No. It is an illustrative narrowband reciprocal banded model.

5. Does the impaired scan use the actual manifold as its search dictionary?
   **Correct:** No. It deliberately uses the nominal dictionary to expose mismatch.

6. Is Bartlett a power scan?
   **Correct:** Yes. It evaluates a covariance quadratic form.

7. Is the Capon curve formed with an explicit matrix inverse?
   **Correct:** No. The script uses a loaded linear solve.

8. Is MUSIC pseudospectrum height the received source power?
   **Correct:** No. It is reciprocal noise-subspace projection.

9. Are spatial power outputs plotted with `10 log10`?
   **Correct:** Yes.

10. Is physical voltage response plotted with `20 log10`?
    **Correct:** Yes.

11. Can the impaired MUSIC peak move only a little while MVDR desired response collapses?
    **Correct:** Yes. Different algorithms expose mismatch through different metrics.

12. Is the physical MVDR pattern evaluated against actual arrival signatures?
    **Correct:** Yes. Otherwise the nominal constraint would hide response loss.

## Interpretation checks

13. What exactly does MVDR preserve?
    **Correct:** Unit response to the assumed look steering vector.

14. Does that guarantee unit response to a mismatched physical source?
    **Correct:** No.

15. Why can the desired signal be self-nulled?
    **Correct:** Its physical signature contributes covariance energy outside the protected assumed vector.

16. What does the pilot correlation estimate?
    **Correct:** The composite received array response at one known direction.

17. Why divide that response by nominal known-source steering?
    **Correct:** To separate the intended spatial phase ramp from composite channel distortion.

18. Does one pilot separately identify gains, positions, and every coupling coefficient?
    **Correct:** No.

19. What does the diagonal equalizer guarantee in the ideal calibration limit?
    **Correct:** It maps the physical response at the calibration direction to the nominal response.

20. Does it guarantee the same mapping at every other angle?
    **Correct:** No.

21. Why is position error direction dependent?
    **Correct:** Its residual phase depends on `sin(theta)-sin(theta_cal)`.

22. Why is coupling direction dependent?
    **Correct:** The mixed vector `C a(theta)` changes with the incoming phase slope.

23. Does more pilot SNR turn a diagonal estimate into a full coupling inverse?
    **Correct:** No. Better evidence does not change identifiability.

24. Is calibration derived from the operational evaluation record?
    **Correct:** No. It uses an independent known pilot capture.

25. Why use the same operational data before and after correction?
    **Correct:** It isolates compensation from random-trial variation.

26. Why retain absolute known-source response as well as normalized curves?
    **Correct:** Per-curve normalization can hide gain or self-nulling loss.

27. Does calibration leave receiver noise unchanged in this model?
    **Correct:** No. The equalizer scales and colors post-chain receiver noise.

28. Does corrected output SINR account for that noise covariance?
   **Correct:** Yes. It uses `sigma_n^2 E E^H`.

29. Does calibrated MUSIC ignore that colored receiver-noise covariance?
    **Correct:** No. It whitens both covariance and nominal steering dictionary
    before partitioning the eigenspace.

## Sweep and failure checks

30. What changes in Sweep 1?
    **Correct:** One severity scale multiplies fixed gain, phase, and position patterns.

31. What stays fixed in Sweep 1?
    **Correct:** Coupling and every source, receiver-noise, pilot, and pilot-noise record.

32. Must every MUSIC RMSE point worsen monotonically with severity?
    **Correct:** No. Fixed error components can partly cancel in one deterministic trial.

33. What changes in Sweep 2?
    **Correct:** One base coupling-strength control; the tied next-nearest term
    follows its fixed `0.30*c^2` rule.

34. What is the direct evidence of coupling's off-angle limit?
    **Correct:** Residual calibrated manifold error at the non-calibration source angle.

35. Does a nonmonotonic DOA error point prove coupling helped?
    **Correct:** No. Read the controlled mechanism and direct manifold metric.

36. What incorrect assumption creates the broken case?
    **Correct:** It treats a known non-broadside pilot as though its nominal steering vector were all ones.

37. What happens to the known source phase slope in that broken case?
    **Correct:** It is flattened toward a broadside signature.

38. Does broken-case recovery regenerate a favorable record?
    **Correct:** No. It changes only the known steering reference.

39. What result should recovery materially restore?
    **Correct:** The known-source angle/signature and physical beam response.

40. What remains after recovery?
    **Correct:** Finite-pilot error and direction-dependent off-angle residuals.

41. Is a restored known source proof of hardware or field performance?
    **Correct:** No. This is a bounded synthetic narrowband model.

## Prediction checks

42. If all impairments are zero, what should the physical manifold equal?
    **Correct:** The nominal manifold, aside from finite calibration-estimation noise if correction is applied.

43. If phase mismatch grows while MVDR still protects nominal steering, what can happen to desired response?
    **Correct:** It can fall sharply through self-nulling.

44. If coupling grows, should one-angle diagonal calibration force off-angle error to zero?
    **Correct:** No.

45. If the calibration channel estimate approaches zero, should the script divide by it?
    **Correct:** No. The safe-inversion guard must refuse the case.

46. If an element displacement reorders sensors, should the result be trusted?
    **Correct:** No. The physical-order guard must stop.

47. If the calibration source angle metadata is wrong, where will its corrected signature tend to point?
    **Correct:** Toward the wrong assumed reference angle.

48. Would scanning impaired data with the exact physical manifold test sensitivity to model error?
    **Correct:** No. It would give the processor the answer and hide the mismatch.

49. What broader lesson carries into STAP?
    **Correct:** Adaptive suppression depends on accurate multidimensional steering models and calibration evidence.

## Short teach-back rubric

A complete teach-back should:

- state that Bartlett, MVDR/Capon, and MUSIC compare data with assumed spatial
  signatures;
- connect gain, phase, position, and coupling errors to steering-vector
  mismatch;
- explain the independent known-source correlation and diagonal correction;
- use the broken broadside-reference case to show why calibration metadata
  matters; and
- distinguish material known-direction recovery from universal array-manifold,
  MATLAB-runtime, antenna, hardware, or field validation.
