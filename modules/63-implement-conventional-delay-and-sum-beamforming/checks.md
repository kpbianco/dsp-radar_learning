# P63 checks: Spatial Alignment, Resolution, and Averaging

Guiding question: How does steering align one direction and misalign others?

## Observation checks

1. **Sensor matrix:** What does one column of `X` represent?
   - **Correct:** one simultaneous complex sample across all array elements.
   - **Incorrect:** one angle bin after beamforming.

2. **Matched direction:** What happens to the residual element phases?
   - **Correct:** conjugate steering removes the modeled incoming slope, so the
     source contributions align.
   - **Incorrect:** each sensor is made noiseless before addition.

3. **Mismatched direction:** Why is its output usually smaller?
   - **Correct:** residual phases rotate with element index and partially
     cancel in the coherent sum.
   - **Incorrect:** off-target samples are deleted from `X`.

4. **Baseline peaks:** Where should the averaged scan peak?
   - **Correct:** within about `0.5 deg` of `-20` and `+25 deg` for the reviewed
     eight-element, 128-snapshot, `+10 dB` scene.
   - **Incorrect:** at the midpoint because there are two sources.

5. **One look versus 128:** What visibly changes?
   - **Correct:** the many-look scan has less random cross-term ripple and more
     stable peaks.
   - **Incorrect:** its physical array aperture becomes 128 times larger.

## Prediction checks

6. **Smaller separation:** What happens to the two scan peaks?
   - **Correct:** they bias together and may merge inside one conventional
     main lobe.
   - **Incorrect:** covariance averaging guarantees two exact peaks.

7. **More elements:** What changes at fixed half-wavelength spacing?
   - **Correct:** physical aperture grows, the main lobe narrows, and the fixed
     pair can become resolvable.
   - **Incorrect:** only the number of snapshots changes.

8. **More snapshots:** What changes at fixed array?
   - **Correct:** scan variance and random ripple decrease; ideal beamwidth
     stays set by aperture.
   - **Incorrect:** angular resolution becomes arbitrarily fine.

9. **Lower SNR:** What happens to the relative scan floor?
   - **Correct:** sensor noise contributes more output power and raises the
     off-source floor.
   - **Incorrect:** only the angle labels become noisier.

10. **Co-located elements:** What happens even with many snapshots?
    - **Correct:** noise can average, but no spatial phase diversity exists to
      form an angle-selective beam.
    - **Incorrect:** covariance rank alone creates direction information.

## Interpretation checks

11. **Core operation:** What is conventional delay-and-sum here?
    - **Correct:** `y=w^H x`, an explicit conjugate-weighted sum across sensor
      channels for each candidate direction.
    - **Incorrect:** a hidden toolbox beam object chooses the source angle.

12. **Power scan:** How is `P_DAS(theta)` formed?
    - **Correct:** average `|w(theta)^H x[ell]|^2` across snapshots.
    - **Incorrect:** average the sensor phases and discard magnitude.

13. **Covariance equivalence:** Why does `w^H Rhat w` match direct averaging?
    - **Correct:** substituting `Rhat=X X^H/L` expands to the same sum of
      squared beam outputs.
    - **Incorrect:** both expressions are normalized to share a plotted peak.

14. **Weight normalization:** Why divide `a(theta)` by `M`?
    - **Correct:** a perfectly matched unit-amplitude plane wave then has unit
      voltage gain after coherent addition.
    - **Incorrect:** it changes the source SNR before noise is generated.

15. **Spatial matched filter:** What is the template?
    - **Correct:** the steering vector predicted for one candidate direction.
    - **Incorrect:** the temporal waveform spectrum of the source.

16. **Source separation versus truth:** Does one merged peak prove one source?
    - **Correct:** no; the conventional aperture may be unable to resolve two
      close sources.
    - **Incorrect:** yes; every source always creates a separate local maximum.

17. **Single-snapshot covariance:** What is special about it?
    - **Correct:** `Rhat=x x^H` is rank one and retains that look's random
      cross-terms.
    - **Incorrect:** it is the exact ensemble covariance for any scene.

18. **Narrowband wording:** Is this script applying physical time delays?
    - **Correct:** no; it applies carrier-phase compensation under a narrowband
      approximation.
    - **Incorrect:** one phase value is an exact delay for every bandwidth.

19. **Normalized curves:** Can their peaks compare absolute receiver power?
    - **Correct:** no; per-curve dB normalization is for shape, while retained
      linear powers preserve absolute simulated values.
    - **Incorrect:** equal `0 dB` plotted peaks prove equal input SNR.

20. **Model boundary:** What is missing from the ideal ULA?
    - **Correct:** element patterns, calibration error, coupling, multipath,
      near-field curvature, bandwidth effects, and operational detection.
    - **Incorrect:** nothing relevant remains after adding sensor noise.

## Broken case and recovery checks

21. **Broken peaks:** Where do sources at `-20` and `+30 deg` appear?
    - **Correct:** near `+20` and `-30 deg` when the steering-vector phase sign
      is reversed.
    - **Incorrect:** both move to broadside.

22. **Exact diagnostic:** What curve identity reveals the error?
    - **Correct:** on the symmetric grid, `P_broken(theta)` equals
      `P_correct(-theta)` for the unchanged data.
    - **Incorrect:** only the maximum power happens to be similar.

23. **Why two asymmetric angles?** What do they make visible?
    - **Correct:** both mirrored labels can be checked without a symmetric
      fixture hiding the sign convention.
    - **Incorrect:** they create a new spatial alias at half-wavelength spacing.

24. **Recovery:** What changes?
    - **Correct:** the steering convention returns to `w=a(theta)/M`; data,
      geometry, SNR, snapshots, and grid stay fixed.
    - **Incorrect:** the source angles in `X` are rewritten after viewing the
      broken result.

25. **Hermitian transpose:** Why is the conjugate required?
    - **Correct:** it supplies the opposite phase needed to remove the modeled
      arrival slope.
    - **Incorrect:** it simply converts power from linear units to dB.

## Lifecycle, compatibility, and resource checks

26. **Malformed input:** What happens to NaN SNR, duplicate source angles,
    unordered grids, noninteger snapshots, or oversized arrays?
    - **Correct:** validation rejects them before reviewed data and figures are
      constructed.
    - **Incorrect:** the script silently sorts, clips, or reallocates them.

27. **Timeout and cancellation:** What remains after Ctrl+C?
    - **Correct:** no worker, file, or partial checkpoint; rerunning reconstructs
      the bounded deterministic experiment.
    - **Incorrect:** a background angular scan continues until killed.

28. **Isolation:** Does cleanup close unrelated figures or change global RNG?
    - **Correct:** no; cleanup is scoped to tag `P63`, and private generators
      hold local state.
    - **Incorrect:** `close all` and a global RNG reset are required.

29. **Resource bound:** What are the fixed ceilings?
    - **Correct:** 16 elements, two sources, 256 snapshots, 2,001 scan samples,
      five sweep cases, 20,000 private values, 500,000 working values, and five
      tagged figures.
    - **Incorrect:** scans grow until every local maximum becomes stable.

30. **Rollback:** What canonical state changes if P63 is reverted?
    - **Correct:** only P63 returns to `scaffolded`; P62, later module identity,
      and local learner progress are preserved.
    - **Incorrect:** Phase 7 and all learner notes must be deleted.

31. **Compatibility:** What may permanent P63 tests assume about later work?
    - **Correct:** P62 remains implemented and P63 retains its canonical
      identity; shared tests derive the moving frontier from the manifest.
    - **Incorrect:** P63 must always be the latest implemented module.

32. **Claim boundary:** What do repository checks prove?
    - **Correct:** artifact structure and an independent bounded simulated
      model, not MATLAB rendering, antenna, HIL, field, or production behavior.
    - **Incorrect:** Python tests validate operational radar performance.

## Completion checklist

- [ ] I traced angle through spatial phase, conjugate steering, and summation.
- [ ] I explained why `w^H Rhat w` equals averaged output power.
- [ ] I separated aperture-limited resolution from snapshot-limited variance.
- [ ] I connected lower SNR to a higher relative spatial scan floor.
- [ ] I diagnosed the mirrored broken scan as a phase-sign mismatch.
- [ ] I recovered on unchanged data with a consistent Hermitian convention.

## Short teach-back rubric

In two or three sentences, explain how conjugate steering removes one source's
spatial phase slope so its channels add coherently while other directions
partially cancel, why array aperture controls whether two sources resolve, and
why covariance averaging stabilizes but does not narrow that fixed response. A
complete answer also diagnoses the mirrored broken scan as a steering-sign
error and states that recovery changes the convention rather than the data.
