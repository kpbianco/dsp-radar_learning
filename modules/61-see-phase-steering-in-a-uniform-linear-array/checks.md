# P61 checks: Phase Steering and Spatial Sampling

Guiding question: How does a direction of arrival become a phase slope across sensors?

## Observation checks

1. **Baseline delay:** Why is adjacent delay negative at `+30 deg`?
   - **Correct:** sensors toward +x receive the incoming wave earlier under the
     stated geometry.
   - **Incorrect:** negative delay means the source has negative bearing.

2. **Baseline slope:** What ideal phase step should appear for `d=lambda/2`
   and `theta=30 deg`?
   - **Correct:** `2*pi*(1/2)*sin(30 deg) = pi/2 rad/element`.
   - **Incorrect:** `pi rad/element` from a monostatic factor of two.

3. **Amplitude:** Does a unit-magnitude snapshot imply zero direction?
   - **Correct:** no; direction is in relative phase even when magnitudes match.
   - **Incorrect:** yes; steering requires an amplitude ramp.

4. **Wrapped plot:** Are jumps near `+/-pi` physical angle changes?
   - **Correct:** no; they are principal-phase coordinate wraps.
   - **Incorrect:** yes; the wavefront changes direction between sensors.

5. **Noisy fit:** Why use all sensors for the straight-line slope?
   - **Correct:** a multi-sensor fit averages bounded phase perturbations.
   - **Incorrect:** it makes an aliased slope unique.

## Prediction checks

6. **Broadside:** What happens at zero degrees?
   - **Correct:** geometric delay and ideal phase slope are zero.
   - **Incorrect:** phase alternates by pi because the array has two sides.

7. **Negative bearing:** What changes when `+30 deg` becomes `-30 deg`?
   - **Correct:** slope reverses sign while its ideal magnitude stays equal.
   - **Incorrect:** only amplitude changes.

8. **Larger physical spacing:** At fixed angle and frequency, what changes?
   - **Correct:** both path-delay magnitude and phase-step magnitude increase.
   - **Incorrect:** neither changes because the element count is fixed.

9. **Higher carrier:** At fixed physical array and angle, what changes?
   - **Correct:** wavelength shrinks and phase step grows; geometric delay stays
     fixed.
   - **Incorrect:** path length grows with carrier frequency.

10. **More elements:** Can adding elements repair a one-cycle-per-element
    alias without other information?
    - **Correct:** no; it repeats more indistinguishable spatial samples.
    - **Incorrect:** yes; any array with at least eight elements is unique.

## Interpretation and operation checks

11. **Core equation:** Where does direction enter the steering sample?
    - **Correct:** through `m*(d/lambda)*sin(theta)` inside complex phase.
    - **Incorrect:** through a toolbox beamwidth parameter.

12. **Adjacent product:** Why use `conj(x_m)*x_(m+1)`?
    - **Correct:** common initial phase cancels, leaving the adjacent step.
    - **Incorrect:** conjugation doubles the one-way path.

13. **Angle convention:** When would cosine replace sine?
    - **Correct:** when angle is measured from the array axis rather than
      broadside, with all labels and equations updated consistently.
    - **Incorrect:** whenever angle is negative.

14. **Temporal analogy:** What differs from P36 Doppler phase progression?
    - **Correct:** P61 samples a one-way wavefront in space; P36 samples a
      monostatic round-trip path change in slow time.
    - **Incorrect:** they both require the Doppler factor of two.

15. **Frequency sweep:** Why hold spacing in metres fixed?
    - **Correct:** that isolates wavelength change for the same physical array.
    - **Incorrect:** `d` must be reset to `lambda/2` or frequency has no units.

## Broken case and recovery checks

16. **Exact alias:** Why can `+36.87 deg` and `-23.58 deg` be identical at
    `d=lambda`?
    - **Correct:** their direction cosines differ by one spatial cycle per
      element, invisible at integer sample positions.
    - **Incorrect:** seeded noise accidentally makes them close.

17. **Unwrap limit:** Why does unwrapping not recover `+36.87 deg`?
    - **Correct:** the inter-sensor cycle count was not sampled.
    - **Incorrect:** MATLAB needs a larger unwrap tolerance to reveal truth.

18. **Recovery:** What single physical control is restored?
    - **Correct:** spacing returns to half wavelength while the source and
      carrier remain fixed.
    - **Incorrect:** the true angle is supplied to the estimator as its answer.

## Lifecycle, compatibility, and resource checks

19. **Malformed input:** What happens to NaN frequency, one sensor, an
    unordered sweep, or too many sweep cases?
    - **Correct:** validation rejects the controls before the reviewed arrays
      and figures are built.
    - **Incorrect:** the script silently clips or sorts them.

20. **Resource bound:** What bounds this experiment?
    - **Correct:** at most 32 elements, seven cases per sweep, 64 private random
      values, 5,000 reviewed numeric values, and five tagged figures.
    - **Incorrect:** a background direction search runs until stopped.

21. **Cancellation:** What happens after Ctrl+C?
    - **Correct:** no worker or file remains; rerunning reconstructs data from
      the private seed, and tagged cleanup leaves unrelated figures alone.
    - **Incorrect:** resume an unvalidated partial snapshot file.

22. **Rollback:** What canonical status changes if P61 is rolled back?
    - **Correct:** only P61 returns to `scaffolded`; P60, later identities, and
      personal learner progress are preserved.
    - **Incorrect:** the whole Phase 7 catalog is deleted.

23. **Compatibility:** What may permanent P61 tests assume about future work?
    - **Correct:** P60 is implemented and P61 keeps its canonical identity;
      shared tests derive the moving frontier from the manifest.
    - **Incorrect:** later batches can never advance beyond P61.

24. **Claim boundary:** What do repository checks prove?
    - **Correct:** structure plus an independent bounded numerical model, not a
      MATLAB runtime, rendered-figure, antenna, HIL, field, or production run.
    - **Incorrect:** Python validation certifies operational angle accuracy.

## Completion checklist

- [ ] I traced source angle through delay, carrier phase, spatial slope, and
  inverse-sine angle inference.
- [ ] I stated the array axis, broadside reference, and phase sign convention.
- [ ] I explained broadside and equal/opposite-angle limiting cases.
- [ ] I separated physical-spacing delay from frequency-dependent phase.
- [ ] I explained why two aliased directions have identical samples.
- [ ] I recovered the true angle by returning to unambiguous spacing.

## Short teach-back rubric

In two or three sentences, explain how a one-way inter-sensor delay becomes
`2*pi*(d/lambda)*sin(theta)` radians per element, how its sign identifies a
side of broadside under the stated convention, and why inverse sine works only
when spatial sampling leaves a unique slope. A complete answer also explains
why phase unwrapping cannot restore a missed whole spatial cycle.
