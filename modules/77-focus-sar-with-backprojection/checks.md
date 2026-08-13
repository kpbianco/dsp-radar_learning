# P77 Checks: Interpret Backprojection Focus

## Guiding question

How does compensating the correct path length focus a point in an image?

Use these after viewing the corresponding plot. Prediction questions are short
and tied directly to a visible result.

## Baseline observation checks

1. **What is the input to P77?**
   **Correct:** A complex range-compressed phase-history matrix: aperture
   positions by slant-range samples.

2. **Why is its magnitude display not already a ground image?**
   **Correct:** Rows still index platform looks; their path-dependent phases
   have not been mapped and combined into target cross-range/ground-range
   pixels.

3. **What does a target ridge location carry?**
   **Correct:** Sampled monostatic slant range for each aperture position.

4. **What does complex phase along that ridge carry?**
   **Correct:** Coherent two-way path-length change across the aperture.

5. **Why is the propagation phase `-4*pi*R/lambda`?**
   **Correct:** The monostatic wave travels the one-way distance twice.

6. **Why may one fixed `R_ref` be subtracted?**
   **Correct:** It removes a common phase rotation while preserving every
   aperture-dependent phase difference used for focus.

7. **What does ridge phase coherence near one establish?**
   **Correct:** Interpolated complex measurements align with the modeled
   two-way path phasors before imaging.

## Backprojection mechanics and predictions

8. **What three operations are performed for one pixel and one look?**
   **Correct:** Predict slant range, linearly sample that complex range row,
   and apply positive two-way phase compensation.

9. **Why is the compensation sign positive?**
   **Correct:** It conjugates the negative propagation phase so a matched path
   has approximately zero residual phase.

10. **Why interpolate along range?**
    **Correct:** A hypothesized slant range is usually between stored range
    samples; nearest-bin-only sampling adds avoidable quantization error.

11. **What happens at the correct pixel?**
    **Correct:** Samples land on the target ridge and compensated complex terms
    align, so voltage adds coherently.

12. **What happens at a wrong pixel?**
    **Correct:** It misses the range ridge, retains residual phase rotation, or
    both, so the aperture sum is weaker.

13. **Is this operation related to beamforming?**
    **Correct:** Yes. It is a delay-and-sum operation with a curved,
    range-dependent steering law for each image pixel.

14. **Would backprojecting only magnitude be equivalent?**
    **Correct:** No. Magnitude erases the phase that distinguishes coherent
    alignment from cancellation.

## Partial-aperture sweep

15. **What changes across the 21-, 61-, and 121-look images?**
    **Correct:** Only the centered number of aperture positions included in the
    coherent sum.

16. **Predict the unnormalized true-pixel voltage as look count rises.**
    **Correct:** It should grow approximately with coherent look count.

17. **Why divide displayed partial images by look count?**
    **Correct:** To compare response shape without letting the longer sum win
    merely because it contains more terms.

18. **Predict target-1 cross-range width as look count rises.**
    **Correct:** It narrows because the observed coherent angular aperture
    grows.

19. **Does adding repeated looks at one identical position improve cross-range
    resolution?**
    **Correct:** No. It can improve SNR but adds no new spatial path diversity.

20. **Does a longer aperture guarantee focus?**
    **Correct:** No. Phase coherence, geometry accuracy, spatial sampling, and
    scene stability are also required.

## Point-response interpretation

21. **Why inspect local windows around both targets?**
    **Correct:** A global maximum can prove only the stronger target focused;
    local peaks verify each modeled coordinate independently.

22. **What does the range cut primarily inherit?**
    **Correct:** The range-compressed point response and waveform bandwidth.

23. **What creates the cross-range cut's narrow peak?**
    **Correct:** Coherent phase alignment across different platform positions.

24. **What does full `-3 dB` width mean here?**
    **Correct:** The distance between interpolated points where voltage
    magnitude falls to `1/sqrt(2)` of the peak.

25. **Does one bright displayed pixel prove correct focusing?**
    **Correct:** No. Coordinate error, response cuts, coherence, and controlled
    failure/recovery provide stronger evidence.

## Wrong path, broken case, and recovery

26. **What changes in the path-error sweep?**
    **Correct:** Only the imager's assumed sinusoidal range-direction platform
    error; the complex measurement remains unchanged.

27. **Why can a 10 mm path error matter at a 60 mm wavelength?**
    **Correct:** Monostatic two-way phase error is `4*pi*DeltaR/lambda`, about
    `2.09 rad` for a 10 mm one-way error.

28. **Why does the sinusoidal error defocus?**
    **Correct:** Its residual phase varies across aperture position, so one
    common phase rotation cannot align all terms.

29. **Must a constant path offset blur image magnitude?**
    **Correct:** No. It may only rotate the complex image by a common phase.

30. **Must a constant wrong height blur this flat 2-D image?**
    **Correct:** No. It can map to a biased ground-range coordinate and remain
    sharp; geometry error can cause bias, blur, or both.

31. **What is the deliberately broken case?**
    **Correct:** Backprojection using the `10 mm` aperture-varying assumed path
    error, which drives the true-pixel coherent gain below the reviewed bound.

32. **What data does recovery use?**
    **Correct:** The unchanged original complex range-compressed phase history.

33. **What does exact recovery protect against?**
    **Correct:** Regenerating a luckier noise record or changing the scene while
    claiming to repair only the path model.

34. **Could recovery work from only the blurred magnitude image?**
    **Correct:** Not by this procedure; the aperture-indexed complex data and
    correct geometry are required.

## Limits, compatibility, and resources

35. **What happens with only one aperture position?**
    **Correct:** Range localization remains but cross-range synthetic-aperture
    focus does not.

36. **What happens as range bandwidth approaches zero?**
    **Correct:** The range response broadens, weakening range localization even
    if the aperture geometry is exact.

37. **What later module isolates range-cell migration?**
    **Correct:** P78. P77 follows hypothesized slant range but does not claim a
    dedicated migration study.

38. **What later modules own resolution/window and motion/autofocus studies?**
    **Correct:** P79 owns aperture/window resolution, and P80 owns motion error
    and autofocus.

39. **Name three omitted effects.**
    **Correct:** Any three of terrain, layover, shadow, extended reflectivity,
    antenna pattern, squint, propagation loss, clutter, autofocus, or
    calibration error.

40. **What toolbox is required?**
    **Correct:** None; the target is base MATLAB R2016b or newer.

41. **How is cancellation handled?**
    **Correct:** Ctrl+C stops the finite foreground script; no worker or
    background task persists, and rerunning from the top recovers
    deterministically.

42. **What bounds resource use?**
    **Correct:** Immutable ceilings cover aperture/range/image samples, targets,
    sweep cases, private noise, figures, pixel-look operations, and P77's
    incremental live workspace before large work is accepted. A local function
    workspace isolates those arrays from unrelated caller variables and prior
    reruns. The reviewed plan and cumulative executed counter must both equal
    `4,451,590` pixel-look operations, below the `5,000,000` cap.

43. **What did static/oracle checks not establish?**
    **Correct:** MATLAB/Octave execution, rendered figures, manual learning
    effectiveness, hardware/HIL, field, real-time, or operational performance.

## Completion checklist

- I can identify the range-compressed complex matrix that enters P77.
- I can state the predicted slant-range and two-way phase-compensation steps.
- I can explain why correct complex looks add coherently at a true pixel.
- I can predict partial-aperture cross-range narrowing.
- I can interpret range and cross-range point-response cuts.
- I can distinguish constant phase/bias errors from aperture-varying defocus.
- I can explain the same-data recovery and its claim boundary.

## Teach-back rubric

A complete two- or three-sentence teach-back must include all four points:

1. Each image pixel predicts one slant range per aperture position.
2. Backprojection interpolates the complex range-compressed sample and cancels
   its two-way carrier phase before summing.
3. Correct geometry aligns the terms and focuses the target at its coordinate.
4. Aperture-varying path error leaves residual phase, reducing coherent gain
   and spreading or shifting the point response.
