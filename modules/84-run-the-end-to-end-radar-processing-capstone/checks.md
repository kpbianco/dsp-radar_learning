# P84 checks

## Guiding question

Can I trace a target from waveform generation through detection and tracking without treating any stage as a black box?

Use the plots and `p84_results` before reading the answers. These are
interpretation checks, not MATLAB-syntax questions.

## Observation checks

1. **Which two range quantities must not be confused?**

   Range sample spacing is `c/(2fs)`; nominal waveform resolution is
   `c/(2B)`. More samples do not by themselves narrow the physical response.

2. **Where is positive target velocity visible?**

   On the positive signed Doppler/approach-speed side of the range-Doppler
   map. Across scans, that same target's range decreases because its physical
   range rate is `-v_approach`.

3. **What creates the zero-Doppler ridge?**

   Seeded stationary clutter reflectivity, whose voltage scale steps upward
   beyond 1.8 km.

4. **Why is the bright spur a false report rather than a target?**

   It is injected as an echo-like receiver interference term but has no entry
   in target truth. Detection sees data, not intent.

5. **What creates the scan-4 coast?**

   The moving target's echo voltage is zeroed before receiver processing on
   scan 4. No report passes the gate, so the tracker predicts without updating.

6. **Which values are nondeterministic even though the scene is seeded?**

   Measured `tic/toc` runtime depends on execution environment and load.

## Interpretation and prediction checks

7. **Predict the result of increasing bandwidth while holding sample rate and
   SNR model valid.**

   Nominal range resolution `c/(2B)` improves until sampling/model limits are
   reached. The sample spacing does not change.

8. **Why must the matched replica be conjugate time-reversed?**

   Reversal aligns delays and conjugation cancels the waveform phase so
   coherent terms add at the correct lag. Reversal alone leaves LFM phase
   mismatch.

9. **If requested `Pfa` decreases, what happens to CA-CFAR `alpha`?**

   It increases, raising the threshold. Weak-target `Pd` can fall while false
   crossings generally fall on the same retained map.

10. **Why is measured false-cell rate not proof of the design Pfa?**

    The design derives from independent homogeneous exponential cells. Pulse
    compression, windowing, target responses, and a clutter edge introduce
    correlation and nonhomogeneity.

11. **Why are incomplete CFAR border stencils marked ineligible?**

    Zero-padding or shrinking them silently changes the reference sample count
    and threshold calibration.

12. **Can one connected component count as both the strong and weak nearby
    target?**

    No. Clustering creates one report, and one-to-one scoring permits that
    report to match only one truth opportunity. Maximum-cardinality matching
    also prevents an ambiguous report from making `Pd` depend on truth order.

13. **What does a cosine matched-filter taper trade?**

    It can reduce sidelobes but broadens the mainlobe and changes coherent
    gain. A nearby weak target may still remain merged.

14. **Why does the quiet-side fixed threshold fail after the clutter edge?**

    Its background estimate no longer represents the CUT region. Extra
    threshold crossings are created at the detector/model seam, not by extra
    physical targets.

15. **Does a coast add measurement information?**

    No. It propagates the prior state for a bounded interval and should become
    less trusted, not be described as a detection.

16. **What would a wrong approach/range-rate sign do?**

    The prediction would move away from an approaching target, increasing the
    innovation and eventually breaking the association gate.

17. **What proves exact broken-case recovery?**

    The retained calibrated input is unchanged, and the recovered compressed
    matrix, power map, threshold surface, and detection mask equal the baseline
    cell for cell.

18. **What happens when target Doppler exceeds `lambda*PRF/4` in magnitude?**

    Slow-time Doppler aliases into another signed velocity.

19. **Which stages use truth?**

    Only offline report scoring, plot markers, and RMSE calculation. Waveform,
    receiver, matched filter, map, threshold, clustering, initiation, gating,
    update, and coast decisions do not receive truth.

20. **What does static repository validation prove?**

    Artifact structure, source contracts, deterministic auxiliary checks, and
    learner-CLI behavior. It does not prove MATLAB execution, plots, runtime,
    numerical fidelity, hardware behavior, or learning effectiveness.

## Completion checklist and teach-back rubric

- Identify the stationary target, moving target, strong/weak pair, clutter
  edge, receiver spur, modeled miss, and at least one false report.
- State the units and operation at all eight provenance stages.
- Explain why fixed threshold and local CA-CFAR differ at the clutter edge.
- Explain both controlled sweeps without calling a display change new
  information.
- Locate the first wrong stage in the broken replica case and describe exact
  same-data recovery.
- Distinguish requested `Pfa`, empirical false-cell rate, false report count,
  `Pd`, range RMSE, resolution, and measured runtime.

An adequate teach-back is two or three sentences that traces one target and
one artifact from creation through the chain, identifies where the miss or
false alarm occurs, and names the retained intermediate product that makes the
diagnosis possible. A strong teach-back also explains why the final track
cannot repair information lost before detection.
