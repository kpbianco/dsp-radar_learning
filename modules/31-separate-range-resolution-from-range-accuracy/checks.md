# Checks

## Guiding question

Why can an estimate be precise even when two targets cannot be resolved?

## Observation checks

1. At baseline bandwidth and 22 m spacing, how many physical local maxima are
   present in the matched response?
2. Which two reported widths shrink when bandwidth rises: nominal `c/(2B)`,
   measured full −3 dB response width, or range-bin spacing?
3. In the fixed-bandwidth SNR sweep, which changes: response width, estimator
   RMSE, or both?

## Prediction checks

1. Before viewing the 8 MHz case, predict whether the fixed 22 m pair will
   remain merged or produce two maxima. Tie the prediction to response width.
2. If the sample grid is interpolated another 100 times without changing the
   waveform, predict the number of physical maxima.
3. If SNR becomes very high but the pair remains well inside one response
   width, predict whether the one-target peak estimate equals either true range.

## Interpretation checks

1. Explain why sub-bin single-target error does not demonstrate sub-bin
   two-target resolution.
2. Distinguish accuracy, bias, precision/standard deviation, and RMSE using the
   metrics in Figure 5.
3. Explain why `c/(2B)` is labeled nominal while the script also measures the
   actual sampled matched-response width.
4. State what is held fixed in the bandwidth, separation, and SNR sweeps.

## Failure and recovery checks

1. What false assumption lets the broken method call two adjacent dense-grid
   samples two targets?
2. Why does local-maximum counting reject that report?
3. What physical change recovers two peaks, and why is it different from display
   interpolation?
4. Confirm that a private seed reproduces the received signal and matched
   response exactly after recovery.

Operationally, Ctrl+C cancels the bounded run. Rerun to recover from the
validated controls. Only figures tagged `P31` are replaced. Base MATLAB is the
only runtime dependency; there is no toolbox, worker, timer, file write,
`.learning/` mutation, network call, hardware action, or external transaction.
Rollback restores only P31 to `scaffolded` plus its P31-owned catalog, test, and
evidence changes.

## Completion checklist

- [ ] I can identify a case with one accurate isolated range estimate whose
      error is much smaller than the measured response width.
- [ ] I can identify a two-target case that remains one blended peak.
- [ ] I can explain how bandwidth changes resolution without claiming a
      pulse-shape-independent exact coefficient.
- [ ] I can explain why SNR and interpolation can improve estimation but cannot
      manufacture missing two-target information.
- [ ] I can reject the broken two-largest-display-samples rule.

## Short teach-back rubric

A complete teach-back names the two different questions—“are there two
distinguishable responses?” and “how far is this estimate from the modeled
target?”—then uses one plot to show bandwidth-driven peak separation and one
metric to show sub-response-width single-target error. It must also say why the
dense-grid broken case adds no waveform information.
