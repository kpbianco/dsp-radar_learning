# Checks: interpret range-cell migration

Use these after observing the figures. Prediction answers should name the
physical mechanism, not MATLAB syntax.

Guiding question: Why does a target move through range bins during a long synthetic aperture?

## Observation checks

1. **Did the target move in ground coordinates?**

   **Correct:** No. Its ground coordinate remains `(60 m,1000 m)`; only radar
   position and therefore monostatic slant delay change.

2. **What curve predicts the bright ridge?**

   **Correct:** `R(x_p)=sqrt((x_p-x_t)^2+y_t^2)`.

3. **How large is baseline migration?**

   **Correct:** About `33.25 m`, `66.5` stored `0.5 m` bins, or `16.6` physical
   `2 m` resolution cells.

4. **Where is the range minimum?**

   **Correct:** At closest approach, near platform cross-range `x_p=60 m`.

5. **Does zero slope at closest approach mean zero aperture migration?**

   **Correct:** No. It is one local point on a curve with a nonzero total span.

6. **What changes between Figure 2's panels?**

   **Correct:** Each row's range sampling coordinate is shifted by its known
   `DeltaR`; the underlying complex measurement is retained.

7. **What corrected ridge span is accepted?**

   **Correct:** At most `1 m` in the seeded sampled baseline.

8. **What remains identical in the fixed and corrected profile comparison?**

   **Correct:** Complex input and two-way carrier-phase compensation.

9. **What operation differs in that comparison?**

   **Correct:** Fixed columns versus linear sampling along the curved range
   path.

10. **Where should the corrected image peak?**

    **Correct:** Within one `2 m` cross-range and `1 m` ground-range grid step
    of `(60 m,1000 m)`.

11. **What happens when aperture length increases?**

    **Correct:** More extreme viewing ranges are included, so migration span
    increases for the reviewed geometry.

12. **What happens when reviewed squint offset increases?**

    **Correct:** The center-referenced curve becomes more asymmetric and its
    range span increases.

13. **What does the wrong-sign ridge do?**

    **Correct:** It spans more than `1.8` times the uncorrected ridge because
    relative migration is approximately doubled.

14. **Does recovery reuse the broken output?**

    **Correct:** No. It freshly resamples the unchanged retained complex input.

15. **What proves deterministic recovery?**

    **Correct:** The recovered correction matrix and coherent profile match the
    original correct results exactly.

## Interpretation and prediction checks

16. **Why does a stationary target cross range bins?**

    **Correct:** Range bins encode measured delay, and platform motion changes
    the target's round-trip slant delay.

17. **If stored spacing halves, does migration in metres double?**

    **Correct:** No. Only the count of stored bins doubles; geometry in metres
    is unchanged.

18. **Is one stored range bin necessarily one resolution cell?**

    **Correct:** No. Sampling density and waveform-limited physical resolution
    are distinct.

19. **Can perfect phase compensation make an empty fixed range column contain
target energy?**

    **Correct:** No. Phase rotates available complex samples; it does not move
    magnitude from other range columns.

20. **Why is the phase factor two-way?**

    **Correct:** Monostatic propagation traverses range on transmit and again
    on receive, giving `4*pi*R/lambda`.

21. **Why is interpolation needed rather than integer shifting?**

    **Correct:** Exact slant ranges generally fall between stored range
    samples.

22. **What does `r+DeltaR` accomplish at `r=R_ref`?**

    **Correct:** It requests the original target location `R_ref+DeltaR=R_p`.

23. **Why does the opposite sign double migration?**

    **Correct:** Sampling `r-DeltaR` places a target near
    `R_ref+2*DeltaR` instead of at `R_ref`.

24. **Does subtracting one constant reference range remove migration?**

    **Correct:** No. It changes the origin but leaves path-dependent variation.

25. **Is a straight magnitude ridge a fully focused SAR result?**

    **Correct:** No. Coherent focus also requires preserved I/Q and correct
    aperture phase compensation.

26. **Would magnitude-only data support this coherent image?**

    **Correct:** No. It could show or align a ridge but cannot preserve the
    required carrier phase.

27. **Does one known `DeltaR_p` align every target in a wide scene?**

    **Correct:** No. Each candidate position has a different range history;
    wide-scene correction is pixel-dependent.

28. **Why is path-following backprojection suitable here?**

    **Correct:** It predicts and interpolates each pixel's range separately
    before phase compensation and coherent addition.

29. **When can fixed-bin processing be a reasonable approximation?**

    **Correct:** When aperture migration is small relative to the physical
    range resolution for the needed accuracy.

30. **Does broadside geometry eliminate migration?**

    **Correct:** No. It makes the range curve symmetric, not constant.

31. **What does a constant range bias do?**

    **Correct:** It shifts the aligned reference range; it does not remove the
    changing part of the path.

32. **Why does the script use exact square-root range?**

    **Correct:** It is the governing geometry across the long aperture; a
    parabola is only a limiting approximation.

33. **What could fake improved concentration at a range-gate edge?**

    **Correct:** Truncating the migrated or wrong-sign response; preflight
    therefore requires interpolation support and response margin.

34. **Why must recovery begin from unchanged input?**

    **Correct:** Resampling an already resampled product compounds interpolation
    error and does not demonstrate exact rollback.

35. **If target geometry is wrong, is this exact correction still exact?**

    **Correct:** No. The assumed path will not follow the measured ridge; P80
    later treats motion error and autofocus.

36. **What do the operation counters include?**

    **Correct:** Baseline correction, wrong-sign failure, fresh recovery, and
    both fixed and path-following image calls.

37. **What should `Ctrl+C` leave running?**

    **Correct:** Nothing. The script has no worker, timer, callback, or
    background task; close partial figures and rerun from the top.

38. **Does a static Python oracle prove MATLAB figures rendered correctly?**

    **Correct:** No. It validates permanent equations/contracts only; MATLAB
    runtime and manual plot review require separate evidence.

39. **Does this experiment validate a real radar?**

    **Correct:** No. It is seeded synthetic base-MATLAB learning evidence, not
    hardware, HIL, real-time, field, deployment, or production validation.

## Completion checklist

- [ ] I identified the exact slant-range curve in the uncorrected matrix.
- [ ] I distinguished metres, stored bins, and physical resolution cells.
- [ ] I explained the explicit fractional-index interpolation.
- [ ] I compared fixed and corrected processing with the same phase model.
- [ ] I connected longer aperture and larger squint to migration geometry.
- [ ] I explained why the wrong sign approximately doubles migration.
- [ ] I verified recovery starts from unchanged complex data.
- [ ] I can state the runtime and validation claim boundary.

## Short teach-back rubric

In two or three sentences, answer the guiding question and connect it to the
completion condition. A complete answer must say that platform motion changes
a stationary target's slant delay, causing its compressed response to cross
range bins; distinguish range interpolation from phase compensation; and say
that following the curved path concentrates energy smeared by fixed-bin
processing. Also mention that stored bin count is not physical resolution.

Do not record personal completion until the learner gives this teach-back and
the tutor has checked the observed baseline metrics.
