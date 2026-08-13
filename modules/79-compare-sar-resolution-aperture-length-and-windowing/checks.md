# P79 checks: Resolution, Sidelobes, and Spatial Sampling

The guiding question is: **What controls range and cross-range resolution and sidelobes?**

Use these after observing the figures. Answers are included so the checks test
interpretation rather than MATLAB recall.

## Baseline observation checks

1. **What two independent coherent records form the local separable PSF?**

   **Answer:** Frequency samples across transmitted bandwidth form the range
   response. Phase-coherent platform positions across the synthetic aperture
   form the cross-range response.

2. **Why is an ideal point target not one image pixel?**

   **Answer:** Both coherent records are finite, so each focus response has a
   mainlobe and sidelobes. The plotted image is the scene convolved with those
   responses; pixel spacing only samples that result.

3. **For `B=200 MHz`, what nominal range-resolution scale should appear?**

   **Answer:** `c/(2B)=3e8/(4e8)=0.75 m`, the one-sided first-null/Rayleigh
   separation for the uniform band.

4. **For `lambda=0.03 m`, `R0=1000 m`, and `L=30 m`, what nominal
   cross-range scale should appear?**

   **Answer:** `lambda R0/(2L)=0.50 m` near broadside.

5. **Is full half-power width equal to one-sided first-null resolution?**

   **Answer:** No. For a uniform sinc-like response, full half-power width is
   about `0.886` times the one-sided first-null scale. Full first-null width is
   about twice that scale.

6. **Why must PSL be measured before the `-50 dB` display floor?**

   **Answer:** Clipping changes displayed minima and low sidelobes. Metrics
   must use the finite unclipped linear response so the plot cannot invent the
   result.

## Prediction and one-variable checks

7. **If bandwidth doubles while geometry is fixed, what happens?**

   **Answer:** Range width halves approximately. Cross-range width remains
   unchanged in this local model.

8. **If aperture length doubles while bandwidth and spacing are fixed, what
   happens?**

   **Answer:** Cross-range width halves approximately. Range width remains
   unchanged.

9. **If target range doubles at fixed wavelength and physical aperture, what
   happens to cross-range resolution?**

   **Answer:** The physical cross-range width roughly doubles because
   `Delta x=lambda R0/(2L)`.

10. **If carrier frequency doubles at fixed geometry and bandwidth, what
    happens to the ideal cross-range scale?**

    **Answer:** Wavelength halves, so cross-range width roughly halves. The
    bandwidth-controlled range scale stays fixed.

11. **Does doubling the number of output image pixels improve either physical
    resolution?**

    **Answer:** No. It samples the existing response more densely, just as FFT
    zero-padding made P13 smoother without adding information.

12. **Why is `L=(N-1)d`, not `Nd`?**

    **Answer:** `N` retained positions contain `N-1` intervals. Physical
    aperture is the distance from the first position to the last.

## Window interpretation checks

13. **Why does the Hamming aperture lower sidelobes?**

    **Answer:** It smooths the abrupt aperture edges, reducing the spectral
    leakage of the finite spatial record.

14. **Why does the Hamming mainlobe widen?**

    **Answer:** Downweighting edge looks reduces effective aperture, so
    off-target hypotheses accumulate less effective phase diversity.

15. **Does peak-normalizing both curves recover the tapered SNR loss?**

    **Answer:** No. Normalization compares shape only. It cannot restore
    collected signal energy or change the weighted-noise variance.

16. **Would the same idea work across frequency?**

    **Answer:** Yes. Frequency weighting can reduce range sidelobes, but it
    widens the range mainlobe and incurs a sensitivity cost. P79 changes only
    aperture weights to keep the dimensions separate.

17. **Is `-42 dB` a universal Hamming SAR sidelobe level?**

    **Answer:** No. It belongs to this discrete weight definition, grid, and
    exact geometry. The durable claim is the measured lower-PSL/wider-mainlobe
    trade.

## Broken-case and recovery checks

18. **What is deliberately broken?**

    **Answer:** Platform spacing is increased from `0.25 m` to `5 m` while the
    `30 m` physical endpoints and target scene remain fixed. Only seven spatial
    samples remain.

19. **Why are the aliases about `3 m` apart?**

    **Answer:** Near broadside, monostatic two-way sampling repeats after
    `Delta x=lambda R0/(2d)=0.03*1000/(2*5)=3 m`.

20. **Why does this formula differ from a one-way receive-array grating-lobe
    formula?**

    **Answer:** Monostatic SAR phase is `4*pi*R/lambda`; transmit and receive
    path changes both contribute. The two-way factor halves the spatial alias
    interval.

21. **Can a Hamming taper eliminate a true sparse-sampling replica?**

    **Answer:** No. If two candidate locations have the same phase at every
    retained position, any fixed set of weights combines them identically.

22. **Can a finer output grid eliminate it?**

    **Answer:** No. A finer grid interpolates the ambiguous response; it does
    not acquire missing platform positions.

23. **What makes the recovery credible?**

    **Answer:** It refocuses the byte-for-byte unchanged seeded scene using the
    original dense platform positions and exactly matches the baseline cut and
    image. It does not invert the already aliased image.

24. **If execution is cancelled, what persists?**

    **Answer:** No file, network, worker, timer, or checkpoint state persists.
    Partial figures/variables may remain in memory; rerunning closes tagged
    figures and deterministically rebuilds results.

## Model-boundary checks

25. **Why is this image called a local separable model?**

    **Answer:** It multiplies independent range and cross-range point responses
    near broadside. Wide scenes, squint, large fractional bandwidth, migration,
    and motion error can couple the axes and require fuller processing.

26. **Which prior module supplies the full focusing operation?**

    **Answer:** P77 supplies path-following backprojection; P78 isolates range
    migration. P79 uses their focused-response intuition to compare design
    controls.

27. **Does a static Python oracle prove that MATLAB rendered these figures?**

    **Answer:** No. It checks the same equations independently. MATLAB runtime,
    parser, graphics, and performance claims require an available named MATLAB
    execution and retained output.

28. **What does P80 add?**

    **Answer:** Unknown platform-position error and autofocus. P79 assumes the
    geometry used for focusing is correct.

## Malformed-input and resource checks

29. **What malformed controls must fail before large work begins?**

    **Answer:** Boolean/nonfinite/non-scalar physics, nested or unordered axes,
    nonpositive bandwidth/aperture/spacing, even or excessive frequency count,
    incompatible target rows, targets outside the image, off-grid endpoints,
    and zero/negative aperture weights.

30. **What prevents an accidental huge sweep?**

    **Answer:** Immutable limits cap frequency, aperture, response, image,
    target, sweep, generator, figure, coherent-operation, and live-storage
    counts. Predicted and executed coherent contributions must match.

## Completion checklist

- [ ] I can distinguish one-sided first-null resolution, half-power width,
  full first-null width, and display spacing.
- [ ] I can change range resolution with bandwidth without crediting aperture.
- [ ] I can change cross-range resolution with aperture/geometry without
  crediting bandwidth.
- [ ] I can explain why taper lowers sidelobes but widens the mainlobe and
  costs sensitivity.
- [ ] I can derive the monostatic sparse-aperture alias interval and explain
  why plotting or taper cannot recover missing samples.
- [ ] I can state the local separable model boundary and the static/runtime
  evidence boundary.

## Teach-back rubric

A complete short teach-back answers the guiding question in this form:

1. Range first-null scale is `c/(2B)`, so changing bandwidth changes range.
2. Broadside cross-range scale is `lambda R0/(2L)`, so wavelength, range, and
   aperture geometry change cross-range.
3. Aperture taper lowers sidelobes by smoothing edges, but widens the mainlobe
   and loses coherent sensitivity.
4. Platform spacing controls spatial ambiguity; the monostatic local alias
   interval is `lambda R0/(2d)`, and recovery needs denser measurements.

Do not record personal completion until the learner can explain all four
without treating pixel size as physical resolution.
