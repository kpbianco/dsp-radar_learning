# Checks: CFAR loss at a fair operating point

## Observation checks

1. In figure 1, which threshold is constant across trials, and why does the
   other move even though the true mean background is one?
2. At `Pd = 0.8`, which detector requires more SNR in figure 2? State the gap
   in dB from the retained metrics.
3. Which total training count has the largest estimate standard deviation and
   the largest measured loss?
4. In figure 5, why does the broken curve look attractive, and which metric
   proves that the comparison is unfair?

## Prediction checks

1. If `N` increased without bound while references stayed independent and
   homogeneous, what should happen to `p_hat`, `alpha`, and CFAR loss?
2. If the requested `Pfa` becomes smaller while `N` remains 16, should the
   finite-training penalty become milder or stronger in this model?
3. If you compare the two detectors at the same `Pd` but fail to match `Pfa`,
   have you measured CFAR loss? Explain.
4. Would increasing `N` still guarantee improvement if the added cells crossed
   a clutter edge or contained another target? Connect your answer to P46.

## Interpretation checks

- Correct: loss is the extra required SNR in dB at a named `Pd`, with detector
  false-alarm probabilities matched.
- Correct: the finite-`N` CA multiplier is larger than `-log(Pfa)` and tends to
  it as `N` grows.
- Correct: more homogeneous independent training powers reduce estimate
  uncertainty; they do not create target energy.
- Correct: the nondecreasing envelope stabilizes crossing interpolation only;
  the plotted `Pd` values remain raw Monte Carlo measurements.
- Incorrect: the difference between the two threshold multipliers in dB is
  automatically the measured CFAR loss.
- Incorrect: the broken detector has almost no loss, so it is superior. Its H0
  false-alarm probability is several times the requested value.
- Incorrect: the 64-cell result proves that any wider real radar stencil is
  better. Representativeness and correlation are outside this homogeneous
  experiment.

## Completion checklist

- [ ] I can write both the fixed known-noise threshold and finite-`N` CA
      threshold operations.
- [ ] I can locate the two SNR crossings used to compute loss.
- [ ] I can explain why the loss shrinks from 8 to 64 training cells.
- [ ] I can explain why stricter `Pfa` exposes more finite-estimate cost.
- [ ] I can identify the broken detector's false-alarm overspend.
- [ ] I can state the homogeneous, independent, square-law model boundary.

## Short teach-back rubric

In two or three sentences, answer the guiding question. A complete answer
defines CFAR loss as extra SNR needed for the same `Pd` at the same `Pfa`, says
finite background estimation randomizes the threshold, and explains that more
representative independent training cells drive the estimate and multiplier
toward the known-noise limit so the loss shrinks.
