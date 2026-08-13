# P75 Checks

## Guiding question

Why does moving one antenna create a large synthetic aperture?

Use these after viewing the corresponding plot. Prediction questions are short
and immediately tied to a visible result.

## Baseline observation checks

1. What makes the aperture synthetic rather than a physical 80 m antenna?
   **Correct:** one coherent antenna measurement is retained at each known
   platform position, so the ordered spatial samples span 80 m.
2. Where is slant range smallest for the centered target?
   **Correct:** at platform cross-range zero, the point of closest approach.
3. Why does less than one metre of range excursion produce many phase turns?
   **Correct:** monostatic phase measures the two-way path in wavelengths:
   `phi = -4*pi*R/lambda`.
4. What does fast time encode?
   **Correct:** echo delay and therefore apparent range through `R=c*tau/2`.
5. What does the alternating real-part pattern along aperture position encode?
   **Correct:** coherent carrier phase changing with the platform-target path.
6. Is the raw fast-time/aperture matrix already a focused SAR image?
   **Correct:** no; it is phase history awaiting later range and azimuth focus.

## Target cross-range prediction and interpretation

7. Predict what moves when target cross-range changes from `0` to `+20 m`.
   **Correct:** the range/phase vertex moves to platform position `+20 m`.
8. Does changing cross-range in this sweep change the declared closest range?
   **Correct:** no; every target retains a 1000 m closest slant range.
9. Why do the `-20` and `+20 m` histories differ even at equal closest range?
   **Correct:** their path minima occur at different platform positions, so the
   phase-curvature samples are shifted across the aperture.
10. What symmetry should the `-20` and `+20 m` cases show?
    **Correct:** mirror symmetry around platform position zero.
11. Could one magnitude sample at closest approach distinguish those targets?
    **Correct:** no; their cross-range distinction is carried by the ordered
    phase history across many positions.

## Aperture-length prediction and interpretation

12. Predict the phase-span change from a 20 m to an 80 m aperture.
    **Correct:** it increases strongly because the longer track samples a larger
    path-length excursion and angular span.
13. What remains fixed in the aperture sweep?
    **Correct:** target coordinate/range, carrier, spatial step, point response,
    and propagation model.
14. Does repeating many looks at exactly one position synthesize cross-range
    aperture?
    **Correct:** no; it may improve SNR but adds no new spatial phase samples.
15. Why enforce an adjacent phase-step limit below `pi` radians?
    **Correct:** to avoid spatial phase aliasing in the reviewed geometry.
16. Does a longer aperture alone guarantee a better image?
    **Correct:** no; coherent phase, position accuracy, adequate sampling, and
    target stability are also required.
17. Does increasing aperture length change local phase curvature at closest
    approach in this fixed geometry?
    **Correct:** no; it reveals a longer portion and larger phase span of the
    same curve. Local curvature is set by wavelength and closest range.

## Broken case and recovery

18. What survives after applying `abs` to the complex aperture record?
    **Correct:** echo magnitude/strength survives; signed spatial phase does not.
19. Why does the magnitude-only coherent score stay small?
    **Correct:** candidate phase compensation cannot align phase that was erased.
20. What record is used for recovery?
    **Correct:** an unchanged copy of the original complex I/Q measurement.
21. Can the recovery be performed if only magnitude was stored by the sensor?
    **Correct:** no; the lost phase is not recoverable from this measurement.
22. Why does the recovered score peak at the true cross-range coordinate?
    **Correct:** that candidate's predicted path cancels the measured phase
    curvature, so all aperture samples add coherently.

## Limits, compatibility, and resources

23. What happens as closest range becomes very large for a fixed short track?
    **Correct:** path curvature weakens and the observed phase histories become
    less distinguishable.
24. What happens at lower carrier frequency for the same geometry?
    **Correct:** wavelength increases and the same range excursion spans fewer
    phase turns.
25. What later module addresses motion-induced phase error?
    **Correct:** P80; P78 separately addresses range-cell migration.
26. Does this model validate terrain imaging or an operational radar?
    **Correct:** no; it is a bounded synthetic single-point-target lesson.
27. What toolbox is required?
    **Correct:** none; the target is base MATLAB R2016b or newer.
28. How is cancellation handled?
    **Correct:** Ctrl+C stops the foreground script; no worker or background
    task persists, and a rerun from the top deterministically recovers.
29. What protects memory and geometry?
    **Correct:** immutable ceilings bound aperture/fast-time/candidate/sweep
    sizes and working storage, while validation rejects malformed or aliased
    controls before large allocation.

## Completion checklist

- I can connect `R(x_p)` to two-way phase curvature.
- I can distinguish fast-time range from aperture-position phase history.
- I can predict how target cross-range shifts the phase-history vertex.
- I can predict why aperture length increases observed phase span.
- I can explain why magnitude-only samples cannot support coherent focusing.
- I can state the model and runtime claim boundaries.

## Teach-back rubric

A complete two- or three-sentence teach-back must include all three ideas:

1. One antenna becomes a synthetic aperture by preserving coherent I/Q at many
   known platform positions.
2. The monostatic two-way range law creates target-dependent phase curvature.
3. Equal-closest-range targets at different cross-range coordinates shift the
   curvature vertex, so their aperture-phase histories differ.
