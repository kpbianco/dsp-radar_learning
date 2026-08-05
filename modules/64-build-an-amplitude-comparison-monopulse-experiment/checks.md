# P64 checks: Sum, Difference, Ratio, Bias, and Recovery

Guiding question: How can sum and difference beams estimate small angle error around boresight?

## Observation checks

1. **Beam crossing:** What happens to the two channel magnitudes at boresight?
   - **Correct:** the phase-aligned left and right beams have equal magnitude.
   - **Incorrect:** the right beam vanishes so only the left beam defines zero.

2. **Difference zero:** Why does `Delta` cross zero at boresight?
   - **Correct:** the matched channel voltages cancel in `(R-L)/2`.
   - **Incorrect:** the target echo itself has zero amplitude there.

3. **Sum reference:** Why is `Sigma` useful?
   - **Correct:** it supplies a common target-voltage reference and a warning
     when the normalized denominator is weak.
   - **Incorrect:** it independently scans every possible arrival direction.

4. **Ratio sign:** What does positive `Re{Delta/Sigma}` mean here?
   - **Correct:** the right-squinted response exceeds the left under the stated
     channel and angle convention.
   - **Incorrect:** the target range is increasing.

5. **Baseline:** What should the coherent estimate report?
   - **Correct:** close to the reviewed `+2 deg` target angle.
   - **Incorrect:** exactly `+3 deg` because that is the beam squint.

6. **Snapshot scatter:** What creates it?
   - **Correct:** independent receiver noise perturbs the two simultaneous
     complex channel voltages.
   - **Incorrect:** the fixed target moves to a new angle each snapshot.

## Prediction checks

7. **Move left:** What happens to the ratio?
   - **Correct:** it becomes negative inside the calibrated sector.
   - **Incorrect:** only its imaginary part can change.

8. **Common amplitude:** If target voltage doubles in both channels, what
   happens ideally?
   - **Correct:** `Delta` and `Sigma` both double, so their ratio stays fixed.
   - **Incorrect:** the estimated angle doubles.

9. **Larger squint:** What two changes should be judged together?
   - **Correct:** local ratio slope rises while boresight sum voltage falls for
     the reviewed cases.
   - **Incorrect:** aperture and snapshot count both double.

10. **Higher SNR:** What changes?
    - **Correct:** random snapshot angle error falls; the nominal calibration
      curve remains fixed.
    - **Incorrect:** the physical beam squint moves toward the target.

11. **More snapshots:** What cannot they remove?
    - **Correct:** a fixed right/left gain mismatch and its angle bias.
    - **Incorrect:** independent zero-mean receiver noise.

12. **Weak sum:** What happens to `Delta/Sigma`?
    - **Correct:** noise is amplified by the small denominator and the angle
      estimate becomes unsafe.
    - **Incorrect:** the ratio automatically becomes more accurate.

## Interpretation checks

13. **Core operation:** What is formed from the channels?
    - **Correct:** `Sigma=(R+L)/2`, `Delta=(R-L)/2`, and the signed real ratio.
    - **Incorrect:** a hidden toolbox object directly returns target angle.

14. **Why phase-align?** Why not subtract arbitrary complex beam outputs?
    - **Correct:** a shared boresight phase reference makes their subtraction
      represent the intended amplitude imbalance.
    - **Incorrect:** phase alignment converts voltage into power.

15. **Voltage versus power:** Which ratio does this lesson calibrate?
    - **Correct:** a phase-aligned complex-voltage difference/sum ratio.
    - **Incorrect:** `(P_R-P_L)/(P_R+P_L)` with the same guaranteed slope.

16. **Local linearization:** What does `eta approximately K theta` mean?
    - **Correct:** a first-order model near boresight with `K` in ratio/degree.
    - **Incorrect:** one exact global formula for every sidelobe.

17. **Lookup direction:** What is inverted?
    - **Correct:** the verified monotonic noise-free ratio versus angle record.
    - **Incorrect:** the noisy target samples are used to redefine truth.

18. **Coherent averaging:** What is averaged first?
    - **Correct:** complex `Delta` and `Sigma` channel samples before division.
    - **Incorrect:** clipped degree estimates, which would be equivalent.

19. **Saturation:** What does an estimate at `+4 deg` prove?
    - **Correct:** only that the noisy ratio reached the positive endpoint of
      this local calibrated estimator.
    - **Incorrect:** the target is globally and exactly at `+4 deg`.

20. **Global DOA:** Can the ratio search the whole visible array sector?
    - **Correct:** no; beam turns and nulls make the ratio nonunique outside
      the declared local monotonic interval.
    - **Incorrect:** yes; normalization removes every sidelobe ambiguity.

## Broken case and recovery checks

21. **Gain bias:** Why does `g=1.12` create a positive boresight ratio?
    - **Correct:** `(g-1)/(g+1)` is positive even when nominal `R=L`.
    - **Incorrect:** the target truth was changed to the right squint angle.

22. **Bias versus noise:** How does gain mismatch appear?
    - **Correct:** as a stable zero-crossing and angle offset.
    - **Incorrect:** only as zero-mean snapshot scatter.

23. **Recovery:** What changes?
    - **Correct:** the known inverse receiver gain is applied to the unchanged
      broken right channel.
    - **Incorrect:** the scene is regenerated with a target forced to zero.

24. **Same-data proof:** What equality should recovery restore?
    - **Correct:** the recovered ratio curve matches the nominal curve within
      numerical tolerance.
    - **Incorrect:** the broken and nominal right voltages remain identical.

25. **Wrong sign:** If `Delta` were coded as `(L-R)/2`, what changes?
    - **Correct:** the angle-error sign reverses under the same calibration.
    - **Incorrect:** only plot color changes.

## Lifecycle, compatibility, and resource checks

26. **Malformed input:** What happens to NaN SNR, noninteger snapshots,
    unordered grids, duplicate sweep values, or oversized requests?
    - **Correct:** validation rejects them before reviewed plots are built.
    - **Incorrect:** the script silently sorts, rounds, or grows without bound.

27. **Timeout and cancellation:** What remains after `Ctrl+C`?
    - **Correct:** no worker, file, checkpoint, or background process; rerunning
      reconstructs the deterministic experiment.
    - **Incorrect:** a hidden angular scan keeps running.

28. **Isolation:** What does startup cleanup affect?
    - **Correct:** only figures tagged `P64`; it does not reset global RNG or
      close unrelated figures.
    - **Incorrect:** every figure and MATLAB random stream must be cleared.

29. **Resource bound:** What are the fixed ceilings?
    - **Correct:** 16 elements, 512 snapshots, 1,001 angle samples, five sweep
      cases, 20,000 private values, 500,000 working values, and five figures.
    - **Incorrect:** the ratio lookup grows until it becomes globally unique.

30. **Rollback:** What canonical state changes if P64 is reverted?
    - **Correct:** only P64 returns to `scaffolded`; P63, later identities, and
      personal learner state remain preserved.
    - **Incorrect:** all Phase 7 modules and learner progress are deleted.

31. **Future compatibility:** What may permanent P64 tests assume?
    - **Correct:** P63 remains implemented and P64 keeps its canonical identity;
      shared tests derive the moving frontier from current manifest state.
    - **Incorrect:** P64 must forever be the latest implemented module.

32. **Claim boundary:** What do repository checks prove?
    - **Correct:** bounded artifact structure and an independent simulated
      model, not MATLAB rendering, antenna, HIL, field, or production behavior.
    - **Incorrect:** Python tests validate an operational radar tracker.

## Completion checklist

- [ ] I traced array samples through `L`, `R`, `Sigma`, `Delta`, and the ratio.
- [ ] I explained why the ratio sign is an angle-error direction near zero.
- [ ] I described the squint slope versus sum-strength tradeoff.
- [ ] I separated random SNR-limited error from fixed calibration bias.
- [ ] I diagnosed the false boresight angle from unequal channel gain.
- [ ] I recovered by calibrating the unchanged channel data.

## Short teach-back rubric

In two or three sentences, explain how simultaneous phase-aligned left/right
beam voltages form a strong sum reference and a signed difference that is
locally proportional to angle error. A complete answer must also say why the
ratio is valid only while its calibration is monotonic and `Sigma` is strong,
and why unequal receiver gain creates a bias that averaging cannot remove.
