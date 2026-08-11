# P66 checks: Peaks, Subspaces, Model Order, and Coherence

Guiding question: How can subspace methods resolve sources more finely than a conventional beam?

## Observation checks

1. **Covariance structure:** Why are off-diagonal entries visible?
   - **Correct:** each plane wave creates repeatable inter-sensor phase relationships.
   - **Incorrect:** spatially white receiver noise is identical at every sensor.

2. **Two large eigenvalues:** What do they mean in the baseline?
   - **Correct:** the data support an approximately two-dimensional signal subspace.
   - **Incorrect:** eigenvector one is permanently labeled as the left source.

3. **Noise subspace:** Which vectors enter `En` when `K=2` and `M=10`?
   - **Correct:** the eight eigenvectors associated with the smallest eigenvalues.
   - **Incorrect:** the two eigenvectors with the largest eigenvalues.

4. **Bartlett shoulder:** Why does it remain merged at six degrees?
   - **Correct:** the finite physical aperture gives a broad conventional response.
   - **Incorrect:** the scan grid contains no samples between the sources.

5. **MUSIC peaks:** Why do they appear at modeled source directions?
   - **Correct:** those steering vectors have small projection onto the estimated noise subspace.
   - **Incorrect:** the code inserts peak markers directly at the truth angles.

6. **Peak height:** Does the `0 dB` MUSIC peak report source power?
   - **Correct:** no; the normalized reciprocal projection is a pseudospectrum.
   - **Incorrect:** yes; it is calibrated received power in watts.

7. **Midpoint contrast:** What does a positive value mean?
   - **Correct:** both truth-angle values exceed the intervening midpoint value.
   - **Incorrect:** the midpoint is the strongest point.

8. **SNR sweep:** What grows between `lambda_2` and `lambda_3`?
   - **Correct:** evidence separating the assumed signal and noise subspaces.
   - **Incorrect:** physical element spacing.

9. **Snapshot sweep:** Why can neighboring points wiggle?
   - **Correct:** finite prefixes have different sample-covariance errors.
   - **Incorrect:** the source angles are regenerated at every point.

10. **Wrong `K`:** What changed in that sweep?
    - **Correct:** only the partition of one unchanged eigensystem.
    - **Incorrect:** new sources were added to the sensor record.

## Prediction checks

11. **Move the sources farther apart:** What happens first in this reviewed scene?
    - **Correct:** MUSIC valley contrast becomes strong before Bartlett fully splits.
    - **Incorrect:** the noise subspace disappears immediately.

12. **Make the sources coincident:** Can either method identify two angles?
    - **Correct:** no; their steering vectors become identical and angle identifiability is lost.
    - **Incorrect:** a finer scan grid guarantees two peaks.

13. **Lower SNR:** What becomes less reliable?
    - **Correct:** estimated eigenspace separation and therefore peak localization.
    - **Incorrect:** the known sensor coordinates physically move.

14. **Add stationary snapshots:** What can improve?
    - **Correct:** the sample covariance can approach its ensemble value.
    - **Incorrect:** the ULA aperture becomes longer.

15. **Overestimate `K`:** What is the safe prediction?
    - **Correct:** too few eigenvectors remain in `En`, weakening the noise projection test.
    - **Incorrect:** one false peak must always appear at exactly `20 deg`.

16. **Underestimate `K`:** What happens to an omitted signal direction?
    - **Correct:** some of its energy is assigned to the noise subspace and may be suppressed.
    - **Incorrect:** it is automatically restored by spectrum normalization.

17. **Make waveforms coherent:** What happens to ideal signal covariance rank?
    - **Correct:** it can fall below the number of physical source directions.
    - **Incorrect:** coherence creates an extra independent eigenvector.

18. **Shorten the smoothing subarray:** What tradeoff appears?
    - **Correct:** more translated views may be available, but effective aperture shrinks.
    - **Incorrect:** physical source SNR necessarily becomes infinite.

19. **Use element spacing above half wavelength:** What risk appears?
    - **Correct:** spatial aliases can create indistinguishable steering directions.
    - **Incorrect:** MUSIC automatically calibrates grating lobes away.

20. **Add colored sensor noise without modeling it:** What assumption fails?
    - **Correct:** the smallest-eigenvalue subspace is no longer an isotropic white-noise floor.
    - **Incorrect:** the steering vector stops containing phase.

## Interpretation checks

21. **Covariance operation:** What does `X X^H/L` average?
    - **Correct:** sensor outer products across snapshots.
    - **Incorrect:** source angles across scan bins.

22. **Eigenvalue sorting:** Why reorder eigenvectors with eigenvalues?
    - **Correct:** signal/noise membership depends on their matched eigenpairs.
    - **Incorrect:** sorting converts radians to degrees.

23. **Core MUSIC denominator:** What is measured by `||En^H a(theta)||^2`?
    - **Correct:** squared steering-vector energy projected into the noise subspace.
    - **Incorrect:** conventional beam output voltage.

24. **Super-resolution:** What makes the claim conditional?
    - **Correct:** model order, source independence, steering accuracy, SNR, and covariance evidence must be adequate.
    - **Incorrect:** every MUSIC peak is physically true at any SNR.

25. **Local maxima:** Why select genuine separated local peaks?
    - **Correct:** adjacent scan samples on one broad lobe are not two resolved sources.
    - **Incorrect:** the two largest samples always represent two emitters.

26. **Eigenvector phase:** Why not compare eigenvectors element by element?
    - **Correct:** eigenvector phase and basis within a degenerate subspace are nonunique.
    - **Incorrect:** MATLAB discards all complex phases.

27. **Spatial smoothing:** What data does recovery use?
    - **Correct:** overlapping contiguous subarrays of the unchanged coherent record.
    - **Incorrect:** newly generated independent source waveforms.

28. **Smoothing steering:** Why use seven sensor entries?
    - **Correct:** the averaged covariance belongs to a seven-element subarray aperture.
    - **Incorrect:** the original ten-element steering vector has no phase.

29. **Smoothing limitation:** What does it not repair?
    - **Correct:** arbitrary calibration, coupling, colored-noise, or non-ULA model errors.
    - **Incorrect:** coherent-source rank in the reviewed ideal ULA case.

30. **dB convention:** Why use `10 log10` for both spectra?
    - **Correct:** Bartlett and MUSIC curves are power-like quantities.
    - **Incorrect:** both are complex voltages.

## Lifecycle, compatibility, and resource checks

31. **Malformed input:** What happens to NaNs, booleans, unordered grids, duplicate cases, invalid `K`, or oversized requests?
    - **Correct:** validation rejects them before reviewed data and plots are built.
    - **Incorrect:** the script silently rounds, sorts, or allocates without limit.

32. **Timeout and cancellation:** What remains after `Ctrl+C`?
    - **Correct:** no worker, file, checkpoint, or background process; rerun reconstructs the record.
    - **Incorrect:** eigenspace processing continues asynchronously.

33. **Isolation:** What does startup cleanup affect?
    - **Correct:** only figures tagged `P66` and the prior `p66_results` variable.
    - **Incorrect:** every figure and MATLAB's global random stream.

34. **Resource bound:** What are the immutable ceilings?
    - **Correct:** 16 elements, four sources, 512 snapshots, 1,001 scan samples, eight sweep cases, 20,000 private values, 1,000,000 working values, and six figures.
    - **Incorrect:** matrix size grows until every possible direction is tested.

35. **Rollback:** What canonical state changes if P66 is reverted?
    - **Correct:** only P66 returns to `scaffolded`; P65 and later identities remain preserved.
    - **Incorrect:** all Phase 7 content and learner progress are deleted.

36. **Future compatibility:** What may permanent P66 tests assume?
    - **Correct:** P65 remains implemented and P66 keeps its identity; shared tests derive the moving frontier.
    - **Incorrect:** P66 must forever remain the latest implemented module.

37. **Claim boundary:** What do repository checks prove?
    - **Correct:** bounded artifacts and a deterministic simulated model, not MATLAB rendering, antenna, HIL, field, or production behavior.
    - **Incorrect:** Python tests certify an operational direction finder.

## Completion checklist

- [ ] I traced `X` through `Rhat`, ordered eigenpairs, `En`, and the reciprocal projection.
- [ ] I explained why Bartlett remains broad while MUSIC splits the reviewed pair.
- [ ] I separated source spacing from SNR and snapshot evidence.
- [ ] I diagnosed under- and over-estimated source count without calling every peak a source.
- [ ] I explained why coherence collapses rank and how same-data spatial smoothing restores it.
- [ ] I stated the aperture and model costs of smoothing and the limits of repository evidence.

## Short teach-back rubric

In two or three sentences, explain that MUSIC uses the sample-covariance
eigenvectors to find steering vectors nearly orthogonal to the estimated noise
subspace, creating sharper direction-consistency peaks than a conventional
power beam. A complete answer must also state why wrong source count or
coherent sources invalidate the subspace partition and why spatial smoothing
can restore rank only by using overlapping ULA subarrays with a shorter
effective aperture.
