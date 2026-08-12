# P68 checks: Interpret the Ridge and the Training

## Guiding question

How can space and slow time be processed together to suppress moving-platform clutter?

1. What does each dashed-ridge point represent?

   **Correct:** One stationary ground patch with paired arrival angle and
   platform-induced normalized Doppler.

2. Why is the ridge tilted rather than at zero Doppler?

   **Correct:** Platform motion changes path length, with radial component set
   by patch angle.

3. Where is the target relative to clutter?

   **Correct:** Its joint point is off ridge although either marginal overlaps.

4. Why is covariance 64 by 64?

   **Correct:** Eight elements times eight pulses make 64 stacked samples.

5. What do dominant eigenvalues mean?

   **Correct:** Strong correlated ridge directions, not an automatic target count.

6. Why is separate processing not full STAP?

   **Correct:** `kron(w_d,w_s)` has a separable product response and cannot
   freely follow a coupled tilted ridge.

7. What does joint normalization promise?

   **Correct:** `w^H s_assumed = 1`, not unit gain for every nearby physical vector.

8. Why use a solve rather than an inverse?

   **Correct:** It exposes the constrained operation with better numerical practice.

9. Why does loading not replace support?

   **Correct:** It regularizes a solve but creates no independent observations.

10. Why are fewer than 64 training cells problematic?

    **Correct:** Raw 64-dimensional sample-covariance rank cannot exceed sample count.

11. Must every support point improve monotonically?

    **Correct:** No; finite prefixes vary. Rank and reviewed endpoints are the claims.

12. Why is clean training target-free?

    **Correct:** It should represent interference without teaching target suppression.

13. Would exact target-aligned rank-one contamination necessarily change exact
    constrained MVDR?

    **Correct:** With fixed loading, the normalized weight is unchanged. Here
    trace-scaled loading can change the weight slightly, but the exact
    constraint still preserves the assumed signature. Declared mismatch lets
    contamination attenuate the actual target in the broken case.

14. What changes in the contamination sweep?

    **Correct:** Only the fraction of unchanged training receiving fixed-power
    actual-target-like leakage.

15. What remains unchanged in recovery?

    **Correct:** Clean samples, CUT, assumption, ridge, loading, and private seeds.

16. Why use `10 log10` for SCNR and `20 log10` for response?

    **Correct:** SCNR is power; complex response is voltage/amplitude.

17. Does a dark normalized pixel prove detection?

    **Correct:** No; it omits absolute gains, thresholds, false alarms, and CUT variation.

18. If platform speed goes to zero, what happens?

    **Correct:** Ridge slope goes to zero and stationary ground approaches zero Doppler.

19. If pulse count becomes one, what disappears?

    **Correct:** Slow-time phase history and Doppler discrimination.

20. If target and clutter steering are identical, can both perfect rejection
    and preservation occur?

    **Correct:** No; those requirements contradict each other.

21. Is more training from different terrain automatically better?

    **Correct:** No; it can estimate the wrong covariance more confidently.

22. At `nu = 0.2` and `PRF = 20 kHz`, what is Doppler?

    **Correct:** `4 kHz`.

## Completion checklist

- I can map element and pulse slopes into one Kronecker vector.
- I can explain the moving-platform ridge.
- I can distinguish separable and joint responses.
- I can read SCNR with target, clutter, and noise.
- I can explain insufficient and contaminated training.
- I can explain why the broken case needs mismatch.

## Short teach-back rubric

In about four sentences: explain why ground forms an angle-Doppler ridge, why
the target overlaps either axis but separates jointly, why joint weights can
beat a separable product, and why limited or contaminated training plus model
mismatch degrades adaptation. Do not call normalized color a detector or claim
measured-radar performance.
