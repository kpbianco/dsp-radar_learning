# P69 checks: Interpret Beat Frequency as Delay

## Guiding question

Why does a delayed chirp produce a nearly constant beat frequency?

1. What does chirp slope mean physically?

   **Correct:** `S = B/T` is the rate of instantaneous-frequency change in
   hertz per second.

2. Why is monostatic delay `tau = 2R/c`?

   **Correct:** The wave travels from radar to target and back to the radar.

3. Why are the transmit and receive frequency ramps parallel?

   **Correct:** An ideal stationary echo is a delayed copy of the same linear
   chirp, so delay changes intercept but not slope.

4. Why is their frequency separation nearly constant?

   **Correct:** Subtracting two equal-slope lines cancels the time-dependent
   term and leaves `S tau`.

5. What interval contains a valid beat?

   **Correct:** Only the transmit/echo overlap `tau <= t < T` for this chirp.

6. Why not circularly shift the chirp to model delay?

   **Correct:** It would wrap late samples to the start and invent a pre-echo.

7. What mixer does P69 use?

   **Correct:** `tx .* conj(rx)`, which gives positive `f_b = S tau` for the
   reviewed ideal up-chirp.

8. What would reversing the mixer order do?

   **Correct:** It would reverse the beat sign, moving the ideal tone to
   negative frequency.

9. How does beat frequency become range?

   **Correct:** `R = c f_b/(2S)` after using the monostatic round-trip delay.

10. Why does the first sweep hold slope fixed?

    **Correct:** It isolates range/delay as the cause of beat-frequency change.

11. Predict the beat if range doubles at fixed slope.

    **Correct:** Round-trip delay and beat frequency both double.

12. What changes in the slope sweep?

    **Correct:** Bandwidth and therefore `S = B/T`; range, duration, sample
    grid, attenuation, FFT, and deterministic noise record remain fixed.

13. Predict the beat if slope doubles at fixed range.

    **Correct:** `f_b = S tau` doubles.

14. Why should slope-sweep range remain fixed?

    **Correct:** Each beat grows with its own slope, and division by that same
    slope cancels the change.

15. What happens if every slope-sweep case uses the baseline slope to convert?

    **Correct:** The estimated ranges scale incorrectly with case slope.

16. Why is the broken range approximately twice the known range?

    **Correct:** `c f_b/S` treats round-trip delay as one-way and omits the
    denominator's factor two.

17. What changes during recovery?

    **Correct:** Only the range formula. The exact same FFT beat estimate,
    slope, and simulated record are reused.

18. Does a sharper zero-padded plot prove better range resolution?

    **Correct:** No. Zero padding samples the spectrum more finely; bandwidth
    sets the ideal `c/(2B)` resolution scale.

19. Why use a window on the valid overlap?

    **Correct:** It reduces spectral leakage caused by observing a finite tone,
    though it also broadens the peak.

20. What does nearly straight mixer phase mean?

    **Correct:** Phase increases at an almost constant rate, so instantaneous
    beat frequency is nearly constant.

21. What happens as target range approaches zero?

    **Correct:** Delay and ideal beat approach zero, where real leakage and
    direct feedthrough would become important.

22. What happens if delay exceeds chirp duration?

    **Correct:** This record has no valid transmit/echo overlap and cannot form
    the intended beat.

23. What happens if slope is zero?

    **Correct:** Delay does not create a frequency difference, and `f_b/S` is
    not a usable range measurement.

24. Why must chirp bandwidth and beat frequency respect sampling limits?

    **Correct:** Otherwise the swept waveform or dechirped tone aliases.

25. Does P69 include target motion?

    **Correct:** No. Motion adds Doppler and can bias one-chirp range; later
    modules treat that coupling.

26. Does this result validate an RF radar?

    **Correct:** No. It is a deterministic complex-baseband teaching model,
    not measured hardware or field evidence.

## Completion checklist

- I can connect `S = B/T`, `tau = 2R/c`, and `f_b = S tau`.
- I can explain the valid-overlap gate and mixer sign.
- I can predict both one-variable sweeps.
- I can convert beat frequency to monostatic range with correct units.
- I can diagnose and recover the factor-of-two broken case.
- I can separate FFT display refinement from physical range resolution.

## Short teach-back rubric

In about four sentences: explain why an ideal delayed linear chirp makes a
constant beat, how `tx .* conj(rx)` sets its sign, how range and slope sweeps
change the beat, and why monostatic range needs the factor two. Do not call
zero padding new resolution or claim measured-radar performance.
