# Checks: interpret the range-compressed phase history

Guiding question: **What information is created before azimuth focusing begins?**

Use these after observing the figures. Give the learner time to answer, then
correct the physical interpretation directly.

## Baseline observations

1. **What changes between the raw center-look echo and the matched output?**
   **Correct:** The long LFM returns become localized delay responses. The
   matched filter aligns chirp phase for one delay and sums it coherently.

2. **Which matrix dimension does P76 process?**
   **Correct:** Fast time, independently within every aperture row. Aperture
   positions are retained rather than coherently summed.

3. **What does one compressed ridge location represent?**
   **Correct:** Sampled monostatic slant range, after removing the known
   matched-filter delay from the displayed axis.

4. **Why is the output not yet a SAR image?**
   **Correct:** It has range localization but no azimuth/cross-range focus;
   aperture looks have not been path-compensated and added.

5. **What two kinds of information does the complex output contain?**
   **Correct:** Ridge location carries slant-range history, and complex ridge
   phase carries coherent path variation across platform positions.

6. **Why normalize the matched output by chirp energy?**
   **Correct:** An isolated unit-voltage echo then has approximately a
   unit-voltage peak rather than a peak scaled by pulse sample count.

7. **Why subtract `N-1` samples on the compressed range axis?**
   **Correct:** A causal length-N conjugate time-reversed filter moves the
   correlation peak by its linear-convolution delay.

8. **What proves the hand-written matched filter has the intended mechanics?**
   **Correct:** Its center row agrees numerically with base-MATLAB linear
   `conv`; the essential row-wise sum remains visible in the script.

## Bandwidth and spacing predictions

9. **At fixed sample rate, what happens when bandwidth rises?**
   **Correct:** The physical response narrows roughly with `c/(2B)`; range-grid
   spacing stays fixed because sample rate did not change.

10. **Does increasing sample rate alone improve `c/(2B)` resolution?**
    **Correct:** No. It produces denser samples of the response unless
    waveform bandwidth also increases.

11. **Why hold pulse duration fixed in the bandwidth sweep?**
    **Correct:** So narrowing can be attributed to bandwidth rather than a
    simultaneous duration change.

12. **What changes in the spacing sweep?**
    **Correct:** Only the two targets' range separation. Bandwidth, duration,
    sample rate, amplitudes, and phase convention stay fixed.

13. **Does a merged pair mean the target ranges are identical?**
    **Correct:** No. Distinct targets can be too close for the fixed waveform's
    responses to form a sufficiently deep valley.

14. **Is the 15 m pair's separation an azimuth-resolution result?**
    **Correct:** No. It is a fast-time range-resolution observation before
    azimuth focusing.

15. **Why may measured -3 dB width differ from exactly `c/(2B)`?**
    **Correct:** The formula is a nominal scale; the finite sampled rectangular
    LFM response and interpolated crossing rule set the measured value.

16. **If bandwidth approaches zero, what is the limiting behavior?**
    **Correct:** Delay responses broaden and nearby targets merge even on a
    finely sampled range grid.

## Phase preservation, failure, and recovery

17. **What is the expected monostatic path-phase factor?**
    **Correct:** `-4*pi*DeltaR/lambda`, because propagation travels to the
    target and back.

18. **Why subtract each target's perpendicular range in the phase law?**
    **Correct:** It removes one target-constant rotation for readable relative
    phase; it does not remove aperture phase curvature.

19. **What would double-count carrier phase?**
    **Correct:** Encoding carrier delay in the chirp and then multiplying by
    the same full carrier-delay phasor again.

20. **What remains visible after taking magnitude?**
    **Correct:** The range-response magnitude and its ridges remain exactly
    visible.

21. **What is destroyed after taking magnitude?**
    **Correct:** I/Q phase, including the coherent aperture progression needed
    for later cross-range focus.

22. **Why is a sharp magnitude map insufficient evidence of SAR readiness?**
    **Correct:** It proves range localization only. It cannot prove that
    relative phase across aperture positions survived.

23. **Does recovery estimate phase from magnitude?**
    **Correct:** No. That information is gone. Recovery uses the unchanged
    retained complex matrix.

24. **What does exact same-data recovery protect against?**
    **Correct:** A misleading demonstration that regenerates a luckier noise
    record or changes the scene while claiming to undo only phase loss.

25. **What does phase coherence near one mean here?**
    **Correct:** The observed normalized ridge phasors align with the modeled
    two-way path phasors across the reviewed aperture.

26. **Would one aperture position be enough for range compression? For SAR
    azimuth focus?**
    **Correct:** It is enough to compress range, but it provides no synthetic
    aperture history for cross-range focusing.

## Limits and common interpretation mistakes

27. **Is platform cross-range on the vertical image axis target cross-range?**
    **Correct:** No. It indexes antenna positions. Target cross-range is not
    focused into an image coordinate until later processing.

28. **Are LFM sidelobes extra targets?**
    **Correct:** No. They are matched-response structure from the finite
    rectangularly weighted waveform.

29. **What error comes from integer delay insertion?**
    **Correct:** True slant range is quantized by at most half the 1.25 m range
    sample spacing in the reviewed model.

30. **What happens if adjacent aperture phase changes exceed pi?**
    **Correct:** Spatial phase aliases. The experiment preflights every target
    below a `0.90*pi` limit.

31. **Does this experiment correct range-cell migration?**
    **Correct:** No. It preserves the slant-range histories. P78 owns explicit
    migration observation and correction.

32. **Name three model omissions.**
    **Correct:** Any three of fractional delay, within-pulse Doppler, clutter,
    multipath, propagation loss, antenna pattern, motion error, oscillator
    drift, extended targets, or calibration error.

33. **What does no optional toolbox mean for the learning objective?**
    **Correct:** LFM phase, echo placement, matched-filter sum, delay correction,
    private noise, and phase metric remain inspectable base-MATLAB operations.

34. **What validation was not established by static/oracle checks?**
    **Correct:** MATLAB/Octave parsing and execution, rendered figures, manual
    learning effectiveness, and any hardware, field, or operational result.

## Completion checklist

- Explain why range compression works along fast time and leaves aperture rows.
- Distinguish range sample spacing from bandwidth-controlled resolution.
- Identify the slant-range ridge and the preserved complex aperture phase.
- Predict bandwidth and target-spacing sweep behavior.
- Explain why magnitude-only data can look useful yet break later focus.
- State that P76 produces a range-compressed phase history, not a focused SAR
  image.

## Teach-back rubric

A complete two- or three-sentence teach-back must include all three points:

1. The LFM matched filter localizes each look in slant range with a resolution
   scale set mainly by bandwidth.
2. Independent row-wise processing preserves complex target phase across the
   synthetic aperture.
3. Azimuth focusing has not happened; taking magnitude keeps range ridges but
   destroys the phase that P77 needs.
