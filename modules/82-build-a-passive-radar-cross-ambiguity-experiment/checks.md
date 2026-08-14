# P82 checks: Interpret the Passive Cross-Ambiguity Map

## Guiding question

How can a known broadcast-like reference reveal delayed Doppler-shifted echoes without transmitting?

Use these after observing the figures. Answers are included so the conversation
can correct interpretation directly rather than become a syntax quiz.

## Baseline observation checks

1. **What are the two measured channels?**

   **Answer:** A reference channel aimed at the illuminator and a surveillance
   channel containing leakage, multipath, the target echo, and noise.

2. **Did this receiver transmit the reference?**

   **Answer:** No. It observes a synthetic non-cooperative illuminator in this
   passive teaching model.

3. **Why does the surveillance magnitude resemble the reference?**

   **Answer:** Direct-path voltage `2.50` is much larger than target voltage
   `0.18`.

4. **Where is the uncancelled global peak?**

   **Answer:** Zero delay and zero Doppler, the direct path.

5. **Where is the post-cancellation target peak?**

   **Answer:** Delay 24 samples and Doppler `+500 Hz`.

6. **What does delay 24 mean physically?**

   **Answer:** The target copy arrives 24 samples after the direct reference,
   corresponding here to `36 km` of bistatic excess path.

7. **Why is that not automatically 36 km of target range?**

   **Answer:** Passive delay constrains transmitter-target-receiver path excess;
   position requires the bistatic geometry.

8. **Why are the before/after plots on a common scale?**

   **Answer:** Separate peak normalization would hide how much weaker the
   residual and target are than the original direct path.

## Equation and sign checks

9. **What operation tests delay?**

   **Answer:** Multiply surveillance by the conjugate of a zero-filled delayed
   reference copy and sum coherently.

10. **What operation tests Doppler?**

    **Answer:** Multiply by `exp(-j*2*pi*f*n/fs)` before summing.

11. **Why does a generated `+500 Hz` echo peak at trial `+500 Hz`?**

    **Answer:** The negative trial phasor cancels the echo's positive phase
    rotation.

12. **What would reversing the trial-phasor sign do?**

    **Answer:** It would mirror the Doppler coordinate and report the positive
    echo at a negative trial Doppler.

13. **Why use complex samples?**

    **Answer:** Complex phase distinguishes positive from negative frequency.

14. **What does normalized coherence equal at a perfect match?**

    **Answer:** It approaches one when one noiseless channel is a scaled matched
    copy over the reviewed support.

15. **Does a dense delay grid create delay resolution?**

    **Answer:** No. Waveform bandwidth and autocorrelation determine delay
    resolution.

16. **Does a dense Doppler grid replace a long CPI?**

    **Answer:** No. It can interpolate; observed coherent duration controls the
    Doppler mainlobe scale.

## Cancellation checks

17. **What coefficient is estimated?**

    **Answer:** `q^H*y/(q^H*q)`, the complex least-squares scale of the measured
    reference inside surveillance.

18. **What does one-tap cancellation remove?**

    **Answer:** The complete surveillance projection onto the unshifted
    measured reference. In this baseline that chiefly suppresses the dominant
    zero-delay direct path.

19. **Why does the delayed static multipath remain?**

    **Answer:** Its 11-sample shifted reference is not a separate column in the
    cancellation model, so it remains a distinct path here. Finite-record
    correlation with the unshifted reference can still bias the coefficient or
    attenuate part of it.

20. **Would more delayed cancellation taps always be better?**

    **Answer:** No. A tap at a slow target's delay can project away that target.

21. **Why does a poor reference hurt cancellation?**

    **Answer:** The noisy reference is a worse predictor of the clean leakage.

22. **Why is zero reference projection at the origin not sufficient proof of
    a good canceller?**

    **Answer:** Least squares makes the residual orthogonal to its fitted
    reference even if that reference poorly represents the actual direct path.

23. **What is broken by 20% cancellation?**

    **Answer:** Most direct leakage remains, so the origin still wins.

24. **What is retained for recovery?**

    **Answer:** The unchanged measured reference and surveillance channels.

## Sweep prediction checks

25. **If delay changes from 24 to 48 samples, what moves?**

    **Answer:** The target peak moves to delay 48 while Doppler remains
    `+500 Hz`.

26. **If Doppler changes from `+500` to `-500 Hz`, what moves?**

    **Answer:** The peak changes Doppler row and keeps delay 24.

27. **What is difficult about a zero-Doppler target?**

    **Answer:** It shares stationary clutter's Doppler row and may be removed by
    a cancellation dictionary at its delay.

28. **Why does target contrast rise with longer integration here?**

    **Answer:** Correctly modeled target phase adds coherently while unrelated
    background grows less coherently.

29. **Name one reason longer integration would stop helping.**

    **Answer:** Acceleration, oscillator/clock mismatch, waveform change, or a
    time-varying channel can break coherence.

30. **What stays fixed in the reference-quality sweep?**

    **Answer:** The clean illuminator, surveillance scene, target, surveillance
    noise, delay-Doppler grid, and CPI.

31. **At the poorest reference endpoint, why can another cell win?**

    **Answer:** Reference mismatch weakens target coherence and leaves stronger
    leakage/mismatch structure.

32. **If target voltage were zero, what should disappear?**

    **Answer:** The deterministic target response at delay 24 and `+500 Hz`;
    only leakage, multipath, and noise structure would remain.

## Limiting-case and safety checks

33. **What happens near a record-length delay?**

    **Answer:** Very few samples overlap, so little coherent energy is
    available.

34. **What happens beyond Doppler Nyquist?**

    **Answer:** Doppler aliases in this sampled model.

35. **Can passive Doppler be converted with `2v/lambda` here?**

    **Answer:** No. Bistatic geometry and carrier information are required.

36. **Does the script use a toolbox ambiguity function?**

    **Answer:** No. It exposes delayed products, trial phasors, sums, and
    normalization using base MATLAB.

37. **What persists if Ctrl+C interrupts the run?**

    **Answer:** No module data or external transaction; rerun rebuilds private
    deterministic inputs and closes only P82-tagged figures.

38. **What does static validation prove?**

    **Answer:** Repository structure, source markers, deterministic independent
    model facts, and tutor/manifest contracts—not MATLAB execution.

39. **What physical evidence was produced?**

    **Answer:** None; there was no hardware/HIL, bench, field, real-time, or
    operational passive-radar validation.

40. **What is the rollback boundary?**

    **Answer:** Restore only P82 artifacts and its manifest/catalog state;
    preserve P81, future identities, learner state, and governed contracts.

## Teach-back rubric

A complete short teach-back should say all of the following:

- the two receive channels observe the same illuminator through different
  paths;
- cross-ambiguity searches delayed reference copies and signed phase rates;
- direct-path correlation dominates until a transparent projection suppresses
  it;
- the recovered `(24, +500 Hz)` peak is an excess-delay/Doppler coordinate, not
  a calibrated position or speed;
- coherent time and reference quality govern visibility; and
- one-tap synthetic cancellation is intuition for, not validation of, a
  practical passive radar.

Do not mark personal completion from automated checks alone; the learner should
give this teach-back first.
