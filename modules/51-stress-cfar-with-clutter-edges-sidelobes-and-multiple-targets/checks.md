# Checks: Stress CFAR with Clutter Edges, Sidelobes, and Multiple Targets

Use these after viewing the named figure. They test physical interpretation,
not MATLAB syntax.

## Observation checks

1. In the combined scene, identify the abrupt clutter edge, the broad
   nonuniform noise swell, the strong target's off-center response, the weak
   neighbor, and the crowded target group.
2. At the edge-target inspection CUT, is the leading mean or lagging mean
   larger? Which raw statistic does GO choose, and which does SO choose?
3. At the crowded CUT, compare the CA mean with the rank-18 OS power. Which is
   more influenced by the strongest few reference cells?
4. Confirm that the first and last 15 cells have no decision from any detector.
   A missing full stencil means no calibrated test, not a non-detection.

## Prediction checks

1. Before selecting the 18 dB contrast case, predict whether GO or SO will make
   more high-side edge crossings. Explain the prediction from the two side
   means.
2. With `N=24` and ascending `k=18`, predict what changes when contamination
   grows from six sufficiently high training cells to seven.
3. If all scene powers and target additions were multiplied by four, predict
   the four masks. Each statistic and threshold scales by four, so the strict
   comparisons should be unchanged.
4. If only one reference half contains a strong target, predict why SO may
   recover a weak CUT while GO masks it—and why the same SO choice is dangerous
   on the high side of a clutter edge.

## Interpretation checks

- **Correct:** equal nominal homogeneous Pfa requires separately calibrated
  CA, GO, SO, and rank-specific OS multipliers.
- **Incorrect:** equal nominal Pfa means all detectors use CA's multiplier.
- **Correct:** a modeled sidelobe crossing is an operational false plot caused
  by target response; it is not an H0 background false alarm.
- **Incorrect:** every non-center crossing estimates achieved Pfa.
- **Correct:** `N-k=6` is the number of sufficiently high samples that can
  remain above rank 18 without entering the selected outlier group.
- **Incorrect:** OS ignores any six contaminants regardless of their strength
  or the clean-sample distribution.
- **Correct:** more training cells help only when they still describe the CUT's
  local background.
- **Incorrect:** one CFAR selector is universally best because it wins on this
  single seeded scene.

## Numeric and resource checks

- `N = 2T = 24`, `G = 3`, and the no-decision half-width is `T+G = 15` cells,
  or 450 m at 30 m per cell.
- At `Pfa=10^-3`, the retained CA/GO/SO/OS multipliers should be approximately
  `8.0045`, `7.0890`, `10.4809`, and `6.5024`.
- Reusing CA alpha gives exact homogeneous probabilities of approximately
  `1.000e-3`, `4.729e-4`, `3.869e-3`, and `2.845e-4`; therefore the shared-alpha
  comparison is intentionally broken.
- The experiment is bounded to 320 range cells, 10 targets, 8 cases per sweep,
  15,000 paired trials, 100 calibration iterations, 400,000 generated random
  values, 1,200,000 stored numeric values, 2,000,000 reviewed training-cell
  visits, and 7 figure groups.

## Completion checklist

- [ ] I inspected the received scene before the detector masks.
- [ ] I explained a weak-target miss from the actual contaminated references.
- [ ] I explained a clutter-edge disagreement from leading and lagging means.
- [ ] I explained the rank-18 OS capacity boundary without calling it immunity.
- [ ] I separated target-response false plots from H0 false alarms.
- [ ] I ran or inspected both one-variable sweeps.
- [ ] I identified why the shared-alpha case is broken and how Recovery works.
- [ ] I did not claim achieved Pfa, measured clutter, or operational validation.

## Short teach-back rubric

A complete teach-back answers “Where do standard CFAR assumptions break?” in
two or three sentences and includes all three points:

1. homogeneous, uncontaminated reference cells are the calibration assumption;
2. clutter edges, sidelobes, nonuniform noise, and multiple targets change the
   training statistic in detector-specific ways; and
3. detector choice and calibration must match the expected reference contents,
   so no CA/GO/SO/OS variant is universally best.
