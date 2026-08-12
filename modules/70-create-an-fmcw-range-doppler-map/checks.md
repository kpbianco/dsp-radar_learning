# P70 checks: Separate Range and Velocity

## Guiding question

How do fast-time beat frequency and chirp-to-chirp phase separate range and velocity?

1. What does one matrix row index represent?

   **Correct:** A fast-time sample within one dechirped FMCW chirp.

2. What does one matrix column index represent?

   **Correct:** A coherent repeated chirp in slow time.

3. What target property sets the ideal fast-time beat in P70?

   **Correct:** Range through `f_b = S(2R/c)`.

4. What target property sets the chirp-to-chirp phase rate?

   **Correct:** Radial velocity through `f_d = 2v/lambda`; with P69's
   `tx .* conj(rx)` mixer, the dechirped slow-time frequency is `-f_d`.

5. Why do targets 1 and 2 share one range neighborhood?

   **Correct:** They both lie at `20 m`, so their ideal beat frequencies match.

6. How can those equal-range targets still separate?

   **Correct:** Their opposite velocities create opposite coherent phase slopes
   across chirps and different Doppler bins.

7. Why do targets 2 and 3 share one velocity column?

   **Correct:** They have the same positive Doppler frequency but different
   beat frequencies and therefore different range rows.

8. Which FFT dimension produces range?

   **Correct:** Dimension 1, down fast-time rows independently for every chirp.

9. Which FFT dimension produces Doppler?

   **Correct:** Dimension 2, across coherent chirp columns for every range row.

10. What remains after the range FFT but before the Doppler FFT?

    **Correct:** A complex range-by-chirp matrix whose columns still preserve
    the slow-time phase history.

11. Does `fftshift` create negative velocity?

    **Correct:** No. It only centers display order; complex phase direction
    and the declared mixer convention determine physical velocity sign.

12. Predict what happens if the chirp count doubles at fixed PRF.

    **Correct:** CPI doubles and Doppler/velocity bin spacing halves.

13. Does that chirp-count change improve the fast-time range grid?

    **Correct:** No. The fast-time record, chirp slope, and observed bandwidth
    remain unchanged.

14. What changes in the retained-sample sweep?

    **Correct:** The measured fast-time duration and therefore observed sweep
    bandwidth; sample rate, slope, chirp count, scene, and slow processing stay
    fixed.

15. Predict the range spacing for 256 retained samples.

    **Correct:** `2 m`, because the `20 us` record observes `75 MHz` of sweep.

16. Why is the 128-sample range response broader than the 512-sample response?

    **Correct:** It contains only one quarter of the measured time and swept
    bandwidth, so its finite-observation beat-frequency response is wider.

17. Would zero-padding 128 samples make them equivalent to 512 measured samples?

    **Correct:** No. It interpolates the short-record spectrum without adding
    time, swept bandwidth, or target-separation evidence.

18. Why is magnitude safe for plotting but unsafe before the Doppler FFT?

    **Correct:** A plotted magnitude can summarize a finished complex result,
    but taking magnitude first erases chirp-to-chirp phase direction and signed
    velocity.

19. What happens to the isolated moving target in the broken path?

    **Correct:** Its nearly constant range magnitude transforms near zero
    Doppler instead of its true positive velocity.

20. Why can equal-range mixtures create ghosts after magnitude?

    **Correct:** The magnitude of summed phasors can beat at their difference
    frequency, which is not either target's original signed Doppler.

21. What changes during recovery?

    **Correct:** Only the invalid magnitude input is replaced by the unchanged
    complex range data before the same window and column FFT.

22. What is the full-record ideal range scale?

    **Correct:** `c/(2B) = 1 m` for `B = 150 MHz`.

23. What is the baseline velocity-bin spacing?

    **Correct:** About `0.609 m/s` for 64 chirps at 20 kHz PRF and 77 GHz.

24. What happens if a beat exceeds `fs/2`?

    **Correct:** It aliases to a false beat frequency and therefore a false
    range.

25. What happens if Doppler exceeds half the chirp repetition frequency?

    **Correct:** Slow-time sampling aliases it to a false signed velocity.

26. Can this map separate two targets with identical range and velocity?

    **Correct:** No. They occupy the same 2-D response unless another diversity
    dimension or model difference is available.

27. Does P70 include range-Doppler coupling?

    **Correct:** No. It intentionally uses a separable stop-and-hop model; P71
    adds within-chirp Doppler and exposes the resulting range bias.

28. Is the range-Doppler map already a detector?

    **Correct:** No. It is a normalized coherent map without a threshold,
    false-alarm control, or calibrated target report.

29. Does the deterministic seed prove operational radar performance?

    **Correct:** No. It makes the synthetic lesson repeatable and testable.

30. What external state can cancellation leave behind?

    **Correct:** None. Partial figures and workspace arrays may remain, but the
    script starts no file transaction, worker, timer, network request, or
    hardware operation.

## Completion checklist

- I can identify fast time and slow time in the matrix.
- I can connect `f_b` with range and `f_d` with signed velocity.
- I can explain why the two FFTs act on different dimensions in order.
- I can predict both observation-count sweeps without invoking zero padding.
- I can diagnose the phase-discarding failure and same-data recovery.
- I can state the stop-and-hop model boundary and point to P71 for coupling.

## Short teach-back rubric

In about five sentences: explain what each matrix dimension measures, how the
range FFT preserves slow-time phase, how the Doppler FFT separates the
equal-range pair, why measured sample/chirp counts control different spacings,
and why taking magnitude before Doppler destroys signed velocity. Do not call
the normalized map a detector or claim MATLAB, RF, or field validation.
