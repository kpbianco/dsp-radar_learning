# P81 checks: Rotation, Alignment, and Cross-Range

The guiding question is: **How does target rotation create synthetic aperture when the radar is stationary?**

Use these after observing the figures. Answers are included so the checks test
radar interpretation rather than MATLAB recall.

## Baseline observation checks

1. **What moves in this experiment?**

   **Answer:** The rigid target rotates and its centroid translates; the radar
   phase center is stationary.

2. **What are the baseline carrier, wavelength, and stepped bandwidth?**

   **Answer:** `10 GHz`, `0.03 m`, and `600 MHz`.

3. **What nominal range resolution follows from that bandwidth?**

   **Answer:** `c/(2B) = 0.25 m`.

4. **What angular aperture and look count are used?**

   **Answer:** `6 deg` sampled at 65 uniform aspect angles.

5. **At `6 deg/s`, what is the CPI?**

   **Answer:** `6 deg / 6 deg/s = 1 s`.

6. **How far does the centroid translate during that CPI?**

   **Answer:** `2 m/s * 1 s = 2 m` from first to last look.

7. **Which first plot proves range compression happened before focus?**

   **Answer:** The aspect-versus-range profile images produced by the explicit
   IFFT across stepped frequency.

8. **Which baseline metrics are computed before dB display clipping?**

   **Answer:** Truth-neighborhood power capture and the truth-to-background
   peak ratio.

## Model and operation checks

9. **What is a scatterer's exact projected target-relative range?**

   **Answer:** `x_i sin(theta) + y_i cos(theta)`.

10. **Why does the echo use `4 pi f R/c`?**

    **Answer:** Monostatic propagation traverses range outbound and on return.

11. **What explicit operation performs range compression?**

    **Answer:** An IFFT across uniformly stepped frequency samples.

12. **Why must the frequency history remain complex?**

    **Answer:** Cross-range focus depends on coherent phase progression across
    aspect; magnitudes cannot preserve or restore it.

13. **What translation correction is applied?**

    **Answer:** Multiply look `p`, frequency `k` by
    `exp(+j 4 pi f_k d_p/c)`.

14. **What does the offset-frequency part of that correction do?**

    **Answer:** It aligns the range envelope across looks.

15. **What does the carrier part do?**

    **Answer:** It removes common pulse-to-pulse phase so aspect samples can
    add coherently.

16. **What small-angle phase law exposes cross-range?**

    **Answer:** `s_i(theta) approximately A_i exp(-j 4 pi x_i theta/lambda)`.

17. **How is angle-frequency mapped to cross-range here?**

    **Answer:** `x = -(lambda/2) f_theta`; the minus sign follows the declared
    rotation and FFT conventions.

18. **Does the script call an opaque ISAR or radar toolbox processor?**

    **Answer:** No. Echo synthesis, compensation, IFFT, FFT, metrics, and
    displays are explicit base-MATLAB operations.

## Aperture and rate prediction checks

19. **What is the nominal `6 deg` cross-range resolution?**

    **Answer:** `0.03/(2 * 6*pi/180)`, about `0.143 m`.

20. **What happens to nominal cross-range resolution if angular aperture
    doubles?**

    **Answer:** It halves under the reviewed small-angle, well-sampled model.

21. **What happens at zero angular aperture?**

    **Answer:** Range may remain observable, but there is no rotational phase
    diversity from which to estimate cross-range.

22. **Why is the aperture equation written in radians?**

    **Answer:** Phase slope and spatial frequency use dimensionless angular
    measure; inserting degrees introduces a factor-of-`180/pi` scale error.

23. **If rate doubles while the same angles are retained, what happens to
    CPI?**

    **Answer:** It halves.

24. **What happens to cross-range Doppler magnitude in hertz?**

    **Answer:** It doubles because `f_D approximately -2 x omega/lambda`.

25. **What else changes when the same 65 angles arrive at a different rate?**

    **Answer:** The implied PRF changes with the inverse look spacing: `32`,
    `64`, and `128 Hz` for the reviewed rate cases.

26. **What happens to the correctly angle-mapped focused image?**

    **Answer:** It remains the same because wavelength, aspect samples, and
    scene are unchanged.

27. **When could faster rotation improve resolution?**

    **Answer:** If CPI were held fixed so faster rotation collected a larger
    total angular aperture, assuming sampling/coherence/model limits hold.

28. **Why can a wide aperture eventually hurt this simple FFT model?**

    **Answer:** `sin(theta)` becomes nonlinear, `y cos(theta)` migrates and
    curves phase, scattering changes with aspect, and angular sampling may
    alias.

29. **What does coarse angular sampling cause?**

    **Answer:** Repeated or aliased cross-range locations even if nominal
    resolution from total aperture is fine.

## Broken-case and recovery checks

30. **What assumption is intentionally broken?**

    **Answer:** Known centroid translation is left uncompensated before range
    compression and angle focus.

31. **Why is the broken result blurred in range?**

    **Answer:** The centroid traverses about `2 m`, so a fixed range bin does
    not contain the same scatterer history across the CPI.

32. **What does the constant-velocity carrier phase do by itself?**

    **Answer:** It is a linear phase ramp versus angle, so it primarily shifts
    or wraps cross-range rather than defocusing a point.

33. **Why is shifting only magnitude rows insufficient?**

    **Answer:** It does not restore the carrier phase required for coherent
    cross-range focus.

34. **Does a separately peak-normalized bright pixel prove recovery?**

    **Answer:** No. The full layout and retained image correlation must agree.

35. **What is the recovery input?**

    **Answer:** The numerically unchanged raw complex stepped-frequency
    history—not the broken image.

36. **What proves the recovery path is exact here?**

    **Answer:** Recomputed aligned history and focused image are asserted
    element-for-element equal to the earlier deterministic baseline.

37. **Is translational migration the same as rotational migration?**

    **Answer:** No. Translation is a common centroid path; rotational migration
    follows each scatterer's `x sin(theta)+y cos(theta)` geometry.

38. **What persistent state can the broken case corrupt?**

    **Answer:** None; all alternate processing is bounded in memory and the
    script writes no file or external state.

39. **How do you recover after Ctrl+C?**

    **Answer:** Rerun `experiment.m`; it closes stale tagged figures and
    reconstructs deterministic private state.

## Limits, compatibility, and evidence checks

40. **What scatterer assumptions make the layout stable?**

    **Answer:** A rigid target with isotropic, fixed complex point
    reflectivities over a small aspect interval.

41. **Is the displayed image a literal optical photograph?**

    **Answer:** No. It is projected range versus phase-derived cross-range
    under a small-angle model.

42. **What immediate prerequisite supplies the coherence warning?**

    **Answer:** P80; P75-P79 supply the SAR history, compression, focus,
    migration, and resolution foundation.

43. **Which MATLAB compatibility is declared?**

    **Answer:** Base MATLAB R2016b or newer, with no optional toolbox.

44. **What is the reviewed explicit contribution bound?**

    **Answer:** `670,800` scatterer-frequency-look contributions under a
    `900,000` ceiling.

45. **What side effects are excluded?**

    **Answer:** File/network I/O, timers, workers, GPU, external processes,
    checkpoints, and persistent state.

46. **What does static validation prove?**

    **Answer:** Repository structure, source contracts, deterministic Python
    oracle behavior, bounds, and recovery semantics—not MATLAB execution.

47. **What validation is explicitly not implied?**

    **Answer:** MATLAB parsing/runtime when unavailable, real scattering
    fidelity, physical radar/HIL, bench, real-time, field, RT1/RT2, Unreal,
    operational radar, signing, deployment, or production validation.

48. **What does repository rollback change?**

    **Answer:** Remove only P81-owned artifacts/test/evidence and restore only
    P81's manifest status to `scaffolded`, preserving P80, future entries,
    learner state, and operator-managed contracts.

## Short teach-back rubric

A completion-ready explanation should include all of these:

- write the two-way stepped-frequency phase for a rotating point scatterer;
- connect the frequency IFFT to range and the angle FFT phase slope to
  cross-range;
- state how wavelength, angular aperture, and angular sampling affect the
  cross-range view;
- distinguish rotation rate/CPI/Doppler hertz from fixed angular-aperture
  resolution;
- explain why translation compensation must align both envelope and carrier
  phase before focus;
- describe recovery from unchanged complex history rather than image
  sharpening; and
- name at least two limits, such as large-angle nonlinearity, rotational
  migration, angular aliasing, unknown rate, or aspect-dependent scattering.

Do not record personal completion until the learner gives that teach-back and
the module completion check has been run.
