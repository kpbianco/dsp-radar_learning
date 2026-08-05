# P62 checks: Beamwidth, Sidelobes, and Spatial Aliases

Guiding question: How do aperture size and element spacing shape a beam pattern?

## Observation checks

1. **Coherent peak:** Why is normalized `AF=1` at the steering angle?
   - **Correct:** steering removes the modeled phase slope, so all weighted
     element contributions align before normalization.
   - **Incorrect:** one element becomes stronger than the others.

2. **Half-power level:** Which linear magnitude defines the HPBW crossings?
   - **Correct:** `1/sqrt(2)`, because its squared magnitude is one half.
   - **Incorrect:** `0.5`, which is one-quarter power and `-6.02 dB`.

3. **First-null width:** Which points define FNBW?
   - **Correct:** the closest local minima on opposite sides of the intended
     main peak.
   - **Incorrect:** the two highest sidelobes.

4. **Peak sidelobe:** Where is PSL measured?
   - **Correct:** from the largest unclipped response outside the first-null
     main-lobe region, relative to the main peak.
   - **Incorrect:** from the dB display after its floor is applied.

5. **Baseline:** What do eight half-wavelength elements produce?
   - **Correct:** about `12.803 deg` HPBW, `28.950 deg` FNBW, and
     `-12.797 dB` PSL in the reviewed broadside grid.
   - **Incorrect:** exactly `1/M` degrees of beamwidth with no sidelobes.

## Prediction checks

6. **More elements:** What happens when `M` increases at fixed spacing?
   - **Correct:** the physical aperture grows and the local main lobe narrows.
   - **Incorrect:** only the plotted peak height grows after normalization.

7. **Co-located elements:** What happens as `d` approaches zero?
   - **Correct:** residual spatial phase vanishes and the normalized isotropic
     array factor becomes flat.
   - **Incorrect:** beamwidth approaches zero because elements are closer.

8. **Larger spacing:** Is a narrower local peak the whole result?
   - **Correct:** no; the visible sector must also be checked for equal-height
     spatial replicas.
   - **Incorrect:** yes; spacing can increase without a sampling tradeoff.

9. **Hamming taper:** What changes relative to uniform weights?
   - **Correct:** peak sidelobes fall while the main lobe widens.
   - **Incorrect:** both sidelobes and beamwidth decrease for free.

10. **Scanning away from broadside:** Does the same direction-cosine width
    remain the same width in degrees?
    - **Correct:** no; inverse-sine mapping widens and skews the degree-domain
      beam near endfire.
    - **Incorrect:** yes; sine is linear over the full visible region.

## Interpretation checks

11. **Core operation:** What creates the pattern?
    - **Correct:** the magnitude of an explicit weighted sum of complex
      residual phase contributions across elements.
    - **Incorrect:** a toolbox object's hidden beamwidth setting.

12. **Angle convention:** Why does the equation use `sin(theta)`?
    - **Correct:** angle is measured from array broadside; an axis-referenced
      convention would require a consistent cosine equation and new labels.
    - **Incorrect:** sine is always required for any antenna coordinate system.

13. **Aperture versus count:** What span does the baseline occupy?
    - **Correct:** `(M-1)d = 3.5 lambda`; eight sensors create seven intervals.
    - **Incorrect:** `Md = 4 lambda` between the first and last sensors.

14. **Ordinary sidelobe or grating lobe:** What distinguishes them here?
    - **Correct:** a grating lobe is an equal-height coherent replica predicted
      by an integer spatial-cycle condition; a normal sidelobe is lower.
    - **Incorrect:** every local maximum outside the main lobe is a grating lobe.

15. **Element pattern:** Does this ideal array factor describe a full antenna?
    - **Correct:** no; a real element pattern and array imperfections also shape
      the total response.
    - **Incorrect:** yes; isotropic-element simulation certifies the antenna.

## Broken case and recovery checks

16. **Exact false peak:** Why do `+30 deg` and `-30 deg` both reach `0 dB` at
    `d=lambda`?
    - **Correct:** their direction-cosine difference creates one whole spatial
      cycle per element, so every sampled residual phase matches.
    - **Incorrect:** the dB floor raises the false direction to the peak.

17. **Predict a grating direction:** Which equation should be checked?
    - **Correct:** `sin(theta_g)=sin(theta_0)+k/(d/lambda)` for nonzero integer
      `k`, retaining only values in `[-1,1]`.
    - **Incorrect:** every spacing above `lambda/2` maps to `theta_g=90 deg`.

18. **Why not taper recovery?**
    - **Correct:** identical sampled steering vectors remain identical under
      any common fixed weights.
    - **Incorrect:** sufficiently low Hamming edge weights change the alias
      direction but not the intended direction.

19. **Physical recovery:** What single control changes?
    - **Correct:** spacing returns from one wavelength to half wavelength while
      the intended angle, element count, weights, and grid remain fixed.
    - **Incorrect:** the false peak is deleted from the stored plot array.

20. **Broadside qualification:** Does `d=0.75 lambda` create an equal-height
    broadside lobe in the full visible interval?
    - **Correct:** no; the nonzero integer candidates lie outside the allowed
      direction-cosine interval.
    - **Incorrect:** yes; crossing `lambda/2` guarantees an alias for every
      single steering angle.

## Lifecycle, compatibility, and resource checks

21. **Malformed input:** What happens to NaN spacing, one element, an unordered
    angle grid, a duplicate sweep value, or an oversized grid?
    - **Correct:** validation rejects it before reviewed arrays and figures are
      constructed.
    - **Incorrect:** the script silently sorts, clips, or allocates it.

22. **Timeout and cancellation:** What remains after Ctrl+C?
    - **Correct:** no worker, file, or partial checkpoint; rerunning reconstructs
      the bounded deterministic experiment.
    - **Incorrect:** a background angular search continues until killed.

23. **Isolation:** Does cleanup close unrelated figures or change global RNG?
    - **Correct:** no; cleanup is scoped to tag `P62`, and the private generator
      holds its own local state.
    - **Incorrect:** `close all` and a global RNG reset are required.

24. **Resource bound:** What are the fixed ceilings?
    - **Correct:** 32 elements, 10,001 angles, five cases per sweep, eight probe
      angles, 250,000 retained numeric values, and five tagged figures.
    - **Incorrect:** the scan adaptively expands until every sidelobe converges.

25. **Rollback:** What canonical state changes if P62 is reverted?
    - **Correct:** only P62 returns to `scaffolded`; P61, later identities, and
      local learner progress are preserved.
    - **Incorrect:** Phase 7 and all learner notes must be deleted.

26. **Compatibility:** What may permanent P62 tests assume about later work?
    - **Correct:** P61 remains implemented and P62 retains its canonical
      identity; shared tests derive the moving frontier from the manifest.
    - **Incorrect:** P62 must always be the latest implemented module.

27. **Claim boundary:** What do repository checks prove?
    - **Correct:** artifact structure and an independent bounded numerical
      model, not MATLAB rendering, antenna, HIL, field, or production behavior.
    - **Incorrect:** Python tests validate operational radar beam performance.

## Completion checklist

- [ ] I traced direction through residual element phase and coherent sum.
- [ ] I measured HPBW at `1/sqrt(2)` and PSL outside the first nulls.
- [ ] I connected increasing filled aperture to decreasing beamwidth.
- [ ] I explained the sidelobe-versus-beamwidth taper trade.
- [ ] I used the integer direction-cosine equation to predict a grating lobe.
- [ ] I explained why half-wavelength recovery works and taper does not.

## Short teach-back rubric

In two or three sentences, explain how `(M-1)d` sets the physical aperture and
therefore the rate of angular phase cancellation, how sampled spatial phase
creates equal-height replicas when the integer grating equation enters the
visible interval, and why taper lowers sidelobes by reducing effective edge
aperture at the cost of a wider main lobe. A complete answer distinguishes an
ordinary sidelobe from a grating lobe and names half-wavelength spacing as the
full-visible-field sampling recovery used here.
