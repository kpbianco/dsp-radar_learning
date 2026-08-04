# Checks: which side should control?

## Observation checks

1. In figure 2, which one-sided estimate rises as the stencil approaches the
   high-clutter region, and which selector follows it?
2. Which known target locations are missed by each detector in the baseline?
   Explain each result from the side means and calibrated thresholds.
3. At 12 dB contrast, compare the retained GO and SO high-side edge
   false-alarm probabilities.
4. In figure 4, which detector preserves the weak CUT as one reference target
   becomes stronger, and which clean statistic makes that possible?

## Prediction checks

1. If the clutter step direction reversed, would GO change from `max` to `min`,
   or would only the physical side supplying the maximum change?
2. As clutter contrast tends upward, what happens to a high-side SO
   false-alarm probability when the minimum estimate remains tied to low
   clutter?
3. If strong targets contaminated both training halves, would SO still have a
   guaranteed clean estimate?
4. As representative per-side training count tends to infinity in homogeneous
   clutter, what happens to both side means and calibrated multipliers?

## Interpretation checks

- Correct: GO protects the high side of a clutter rise by selecting the larger
  reference estimate, but that same choice can mask a low-side target.
- Correct: SO can reject one contaminated training half only while the other
  half remains representative of the CUT background.
- Correct: leading and lagging describe index direction; GO and SO describe
  value selection.
- Correct: separate GO and SO calibration is required for an equal-`Pfa`
  comparison.
- Incorrect: the GO threshold is always numerically above the SO threshold.
  Their calibrated multipliers differ, so finite homogeneous samples can
  reverse the ordering.
- Incorrect: SO's higher detection probability automatically means it is the
  better edge detector. Its false-alarm probability must be checked.
- Incorrect: a 12 dB simulated step validates behavior in measured or
  correlated clutter.

## Completion checklist

- [ ] I can write both one-sided arithmetic power means and identify the guard
      and training cells.
- [ ] I can explain why GO uses `max` and SO uses `min` without tying either to
      a fixed geometric side.
- [ ] I can explain the low-side miss/high-side false-alarm tradeoff at an
      abrupt clutter increase.
- [ ] I can explain why a one-sided interfering target favors SO.
- [ ] I can diagnose the broken shared CA multiplier as an unequal-`Pfa`
      comparison.
- [ ] I can state the independent exponential-power and abrupt-edge model
      boundary.

## Short teach-back rubric

In two or three sentences, answer the guiding question. A complete answer says
that GO lets the brighter side control when clutter-edge false alarms are the
protected failure, while SO can let a clean quieter side control when only one
training half is contaminated. It also names the cost—GO can miss a low-side
edge target and SO can false alarm on the high side—and requires separate
equal-`Pfa` calibration before comparison.
