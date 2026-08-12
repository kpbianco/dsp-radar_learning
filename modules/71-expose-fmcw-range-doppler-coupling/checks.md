# P71 checks: Predict the Range Bias

## Guiding question

Why can target motion bias the range estimated from one chirp?

1. What two physical terms share the measured up-chirp beat?

   **Correct:** Round-trip delay contributes `S(2R/c)` and radial motion
   contributes Doppler `2v/lambda`.

2. What mixer and velocity convention does this lesson use?

   **Correct:** `tx .* conj(rx)`, with positive velocity approaching.

3. Under that convention, what is the signed up-chirp beat?

   **Correct:** `f_beat = S(2R/c) - 2v/lambda`.

4. Does approaching motion raise or lower this beat?

   **Correct:** It lowers the beat because positive Doppler is subtracted.

5. What range does the stationary assumption compute?

   **Correct:** `R_stationary = c f_beat/(2S)`.

6. What is its range bias?

   **Correct:** `R_stationary - R = -c f_d/(2S) = -f_c v/S`.

7. Predict the sign for an approaching target.

   **Correct:** Negative: it appears too near.

8. Predict the sign for a receding target.

   **Correct:** Positive: it appears too far.

9. What happens at zero velocity?

   **Correct:** Doppler and coupling bias vanish, recovering P69's stationary
   range law.

10. What are the baseline delay and Doppler contributions?

    **Correct:** `150.000 kHz` from delay and about `10.267 kHz` from
    approaching Doppler.

11. What is the baseline signed beat?

    **Correct:** About `139.733 kHz`, the delay contribution minus Doppler.

12. What naive range and bias result?

    **Correct:** About `41.920 m` and `-3.080 m` for the true `45 m` target.

13. Did the target travel `3.080 m` during the chirp?

    **Correct:** No. It traveled only `20 m/s * 40 us = 0.8 mm`; the range
    bias is a frequency-interpretation error.

14. Predict the bias at `v = -30 m/s` with the baseline slope.

    **Correct:** `+4.620 m` because the target is receding.

15. Predict the bias at `v = +30 m/s`.

    **Correct:** `-4.620 m`.

16. Why is the velocity-sweep result a straight line?

    **Correct:** Carrier and slope are fixed, so `-f_c/S` is a constant
    multiplying velocity.

17. What changes in the slope sweep?

    **Correct:** Bandwidth and therefore `S = B/T`; range, velocity, carrier,
    duration, and sample rate remain fixed.

18. Why does steeper slope reduce bias in meters?

    **Correct:** The same Doppler error is divided by a larger beat-frequency
    change per meter.

19. Does steeper slope remove Doppler from the beat?

    **Correct:** No. It reduces `|f_c v/S|`; the beat still contains Doppler.

20. Can one noiseless beat determine both range and velocity?

    **Correct:** No. It is one equation with two unknowns.

21. Could a stationary target at `41.920 m` match the baseline beat?

    **Correct:** Yes. That is the single-chirp ambiguity made visible.

22. What independent information enables correction?

    **Correct:** Signed Doppler or radial velocity from another measurement,
    such as coherent chirps or another slope.

23. What is the correct baseline correction?

    **Correct:** `R = c(f_beat + f_d)/(2S)` for this declared convention.

24. What does the deliberately wrong correction do?

    **Correct:** It subtracts `f_d` again and doubles the bias to `-6.160 m`.

25. What changes during recovery?

    **Correct:** Only the correction sign; the measured beat and independently
    supplied velocity remain unchanged.

26. Why must the beat estimator retain sign?

    **Correct:** Strong approaching Doppler can drive the beat through DC to
    negative frequency, which magnitude or a positive-half spectrum obscures.

27. What happens when `f_d = S(2R/c)`?

    **Correct:** The signed beat is DC and the stationary conversion reports
    zero range despite nonzero true range.

28. What happens if `|f_beat| >= fs/2`?

    **Correct:** The sampled beat aliases, invalidating both naive and
    corrected interpretations.

29. Does zero-padding supply the missing velocity equation?

    **Correct:** No. It interpolates the same finite observation.

30. What model approximation is made within the chirp?

    **Correct:** Round-trip delay is frozen while constant carrier Doppler
    represents motion; range stretch/migration and acceleration are omitted.

31. What external state can cancellation leave behind?

    **Correct:** None. Partial figures and workspace arrays may remain, but the
    script starts no file transaction, worker, timer, network request, or
    hardware operation.

32. Does deterministic simulation prove operational radar performance?

    **Correct:** No. It makes this synthetic model repeatable and testable.

## Completion checklist

- I can state the mixer, chirp, and velocity sign conventions.
- I can separate delay and Doppler contributions to the signed beat.
- I can predict bias sign for approaching and receding targets.
- I can calculate how velocity and slope change bias magnitude.
- I can diagnose the wrong-sign correction and explain same-data recovery.
- I can explain why one chirp alone cannot identify both range and velocity.

## Short teach-back rubric

In about five sentences: state the signed beat equation and conventions,
explain the approaching-target bias, distinguish bias from target travel,
describe the velocity and slope trends, and name the independent information
needed for correction. Do not claim that one chirp estimates both unknowns or
that static validation is MATLAB, RF, or field evidence.
