# P45 checks: Implement 1-D Cell-Averaging CFAR

## Guiding question

How can the threshold adapt to the local noise level?

Use the figures and retained `results` values. These are short concept checks,
not long derivations and not MATLAB syntax questions.

## Observation checks

1. In Figure 2, where is the typical CA-CFAR threshold higher: the lower- or
   higher-background half of eligible range cells? Point to the corresponding
   change in the local training estimate.
2. How many training samples form each estimate, how many guards lie on each
   side, and why are 14 CUTs excluded at each profile edge?
3. In Figure 4, what happens to the threshold when all scene power doubles?
   What happens to `observed power / threshold` and the decisions?
4. In Figure 5, is the dB-average threshold above or below the linear-power
   threshold? Confirm with `results.broken_threshold_ratio`.

## Prediction checks

1. Keep everything else fixed and lower requested `Pfa`. Predict the direction
   of `alpha`, the threshold, non-target crossings, and target detections.
2. Multiply noise and target power together by four. Predict the threshold
   multiplier and whether any normalized decision changes.
3. If an edge threshold were filled with zero instead of left invalid, predict
   what positive power samples there would do.
4. If the background changes sharply inside the training window, predict why
   the homogeneous-model `Pfa` claim may fail even though the code still runs.

## Interpretation checks

1. Explain why the CUT and guard cells cannot enter their own background
   estimate. Do not use target truth in your explanation.
2. Why does this power detector use
   `alpha = N*(Pfa^(-1/N)-1)` instead of the signed Gaussian threshold from
   P43/P44?
3. Why can the threshold look noisy even though the synthetic mean background
   changes slowly?
4. Why is averaging dB values not repaired merely by labeling the resulting
   curve “power”?
5. Does one 256-cell profile validate a requested `Pfa = 1e-3`? State what P52
   must add before making that statistical claim.

## Completion checklist

- [ ] I followed one CUT's leading training cells, guards, CUT, and lagging
  training cells without including the CUT or guards in the average.
- [ ] I observed the baseline threshold follow low and high local background.
- [ ] I completed the requested-`Pfa` and uniform-power sweeps one variable at
  a time.
- [ ] I explained the broken dB-domain average and exact linear-power recovery.
- [ ] I distinguished excluded edge cells from zero-threshold detections.
- [ ] I can state the homogeneous independent exponential-noise assumption.

## Short teach-back rubric

In two or three sentences, answer: **How can the threshold adapt to the local
noise level?** A complete teach-back should include all three ideas:

1. CA-CFAR estimates nearby mean power from explicit training cells while
   excluding guards and the CUT;
2. the requested `Pfa` scale factor multiplies that local linear-power estimate,
   so a local power change moves the threshold with it; and
3. the modeled `Pfa` is exact only for homogeneous independent exponential
   cells, while edges and nonhomogeneous backgrounds require explicit handling.

Do not mark personal completion until the learner has run the completion check
and given this teach-back. Personal progress belongs only under `.learning/`.
