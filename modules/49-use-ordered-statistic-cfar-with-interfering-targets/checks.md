# Checks: ordered-statistic CFAR under target contamination

Use the unchanged baseline unless a question explicitly names a sweep case.

## Observation checks

1. At the primary CUT, which threshold is above the 15 dB target: CA or
   rank-18 OS?
2. In the sorted reference plot, where do the four 20 dB interferers appear,
   and where is the selected sample?
3. At what count does the red detection curve cross beyond the `N-k = 6`
   capacity boundary?
4. In the strength sweep, which detector continues to change strongly after
   the four contaminators are already the largest samples?

## Prediction checks

1. With `N = 24` and `k = 20`, how many very high outliers can remain above the
   selected sample? What happens with five?
2. If four fixed interferers remain but rank changes from 18 to 22, predict
   whether the selected sample is clean in the strong-outlier limit.
3. If rank changes from 18 to 12 while the rank-18 multiplier is reused,
   predict whether homogeneous false alarms rise or fall.
4. If every reference power and the CUT power scale by the same positive
   factor, predict whether either calibrated detector's decision changes.

## Interpretation checks

- Correct: ascending rank `k` can keep up to `N-k` sufficiently high outliers
  above the selected sample.
- Incorrect: OS-CFAR identifies and removes targets. It only selects a sorted
  reference statistic; it does not label the high samples.
- Correct: contamination count and rank decide whether the selected statistic
  enters the outlier tail; contaminator strength then decides how severe the
  threshold jump is.
- Incorrect: equal requested `Pfa` means every rank uses the same multiplier.
  The exact order-statistic distribution changes with `k`.
- Correct: rank-specific calibration fixes the homogeneous false-alarm budget;
  it does not guarantee good behavior for unlimited nonhomogeneity.

## Compact numeric checks

- `N = 24`, `k = 18` gives `N-k = 6` high-outlier slots.
- At `Pfa = 10^-3`, rank-18 OS uses `alpha_18` approximately `6.50243`; the
  24-cell CA multiplier is approximately `8.00451`. Their numerical difference
  is not a direct ranking of detector quality because they multiply different
  statistics.
- Four strong contaminators leave 20 clean samples, so rank 18 has two clean
  samples of spare margin; rank 22 is already in the contaminated tail.
- Reusing `alpha_18` at rank 12 yields a homogeneous `Pfa` above the requested
  value; recalibrating rank 12 restores the target value.

## Completion checklist

- I can point from nearby targets to contaminated training cells and then to a
  raised threshold.
- I can compute `N-k` and distinguish capacity from an unchanged statistic.
- I can explain the count, strength, and rank sweep trends.
- I can explain why the reused-multiplier case is broken and how to recover.
- I can choose a rank for four expected outliers without claiming it handles
  unlimited targets.

## Short teach-back rubric

A complete two- or three-sentence teach-back says that CA averages every
training power, while OS selects a calibrated sorted rank; explains that rank
`k` has at most `N-k` high-outlier capacity; and states that a rank must be
chosen for expected contamination and recalibrated to preserve the homogeneous
false-alarm budget. It should not claim that OS recognizes targets, that the
capacity is unlimited, or that this simulation proves measured-radar behavior.
