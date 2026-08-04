# P45 lesson: Implement 1-D Cell-Averaging CFAR

## Guiding question

How can the threshold adapt to the local noise level?

## Physical mental model

Imagine sliding a small stencil along range. Its center is the cell under test
(CUT). The nearest cells on each side are guards, so energy from the possible
target does not define its own threshold. The cells beyond the guards are
training cells: nearby background measurements used to estimate what “normal”
power looks like at that range.

The stencil does not know target truth. It repeats the same local operation at
every eligible CUT. Near the start and end of the profile there are not enough
cells on both sides, so this lesson labels those edge CUTs as excluded rather
than silently giving them a zero threshold.

## The square-law background model

The receiver in this lesson supplies one complex noise sample per range cell.
For independent zero-mean Gaussian I and Q components, square-law power

`z[k] = |x[k]|^2`

is exponential. Its mean is the local background power. The synthetic mean
changes slowly with range; one threshold cannot suit the whole profile, but a
short local window sees an approximately homogeneous background.

With `T` training cells on each side and `G` guards on each side, the total
training count is

`N = 2*T`.

For CUT `k`, the explicit CA estimate is

`p_hat[k] = (sum(left training powers) + sum(right training powers)) / N`.

Neither the CUT nor its guards enter that sum. The decision is

`detect[k] = z[k] > alpha * p_hat[k]`.

For independent, identically distributed exponential training cells and CUT,
the scale factor for a requested false-alarm probability is

`alpha = N * (Pfa^(-1/N) - 1)`.

This formula is for power, not signed Gaussian amplitude. Reusing the P43/P44
Gaussian-amplitude threshold would mix detector models and give the wrong
false-alarm behavior.

## What each figure means

Figure 1 separates the known mean background used to synthesize the scene from
the noisy power actually observed. A local estimator can follow the former
only approximately because it sees a finite random sample.

Figure 2 shows the baseline CA-CFAR signal flow. The local training average
wanders around the true background; multiplying it by `alpha` creates a
threshold with the same broad shape. Target cells above the threshold are
detections. Edge cells carry no decision because the full stencil does not fit.

Figure 3 changes only requested `Pfa`. A smaller request increases `alpha`, so
every eligible local threshold rises. Counts from one 256-cell profile are
illustrations, not a validation of a rare probability. Dedicated Monte Carlo
validation belongs to P52.

Figure 4 multiplies the entire observed scene by 0.5, 1, or 2 while leaving the
CFAR geometry and requested `Pfa` fixed. The training estimate and threshold
scale by the same factor. Therefore `observed power / threshold` and every
decision remain exactly unchanged. This is the cleanest answer to the guiding
question: CA-CFAR compares a cell with its local scale rather than with one
fixed number in receiver units.

Figure 5 deliberately averages training samples after converting them to dB.
The arithmetic mean of dB values is a geometric mean in linear power. For
unequal positive samples, the geometric mean is below the arithmetic mean, so
the broken threshold is biased low and cannot use the exponential CA-CFAR
scale-factor claim. Recovery means returning to the arithmetic mean of linear
power before applying `alpha`.

## Limiting cases and boundaries

- In perfectly homogeneous independent exponential noise, the stated `alpha`
  gives the modeled single-CUT `Pfa`.
- In a slowly varying background, the result is approximate: the reference
  window must be local enough that CUT and training cells have nearly the same
  distribution.
- More training cells reduce estimate variance but reach farther away. Fewer
  cells are more local but make a noisier threshold. P46 explores that trade.
- Guard cells protect the estimate from target energy or a matched-filter
  mainlobe. Too few or too many guards are geometry decisions studied in P46.
- A clutter edge, nearby interfering target, correlated cells, or a non-
  exponential background violates the simple CA model. GO-, SO-, OS-, 2-D,
  and stress-test lessons P48-P52 address those cases.
- Lower requested `Pfa` raises the threshold and can reduce target detection.
  CFAR adapts scale; it does not remove the detection tradeoff learned in P44.
- Excluded edges need an explicit system policy such as smaller windows,
  asymmetric windows, padding, or no decision. This lesson chooses no decision.

## Common interpretation mistakes

1. “The threshold should be smooth.” It is a local estimate from random power,
   so it fluctuates even when the underlying mean changes smoothly.
2. “Every non-target crossing disproves CFAR.” A nonzero requested `Pfa`
   permits false alarms. One short profile cannot estimate `Pfa` accurately.
3. “The target mask helps the detector.” Truth labels are used only to report
   metrics; the CA loop sees powers and fixed window geometry only.
4. “Average the plotted dB curve.” The CA equation averages linear power. Plot
   units do not change the estimator domain.
5. “NaN edge thresholds are failures.” They deliberately encode cells where a
   full two-sided window cannot be formed; zero would be a dangerous threshold.

## Dependencies and claim boundary

P43 demonstrates why one fixed native-unit threshold fails as background power
changes. P44 defines conditioned `Pfa`/`Pd` and the cost of a threshold choice.
P41 provides range-varying clutter intuition. This module uses base MATLAB and
an explicit loop so no toolbox CFAR black box hides the training indices,
average, scale factor, or comparison.

The experiment is a bounded synthetic model. It is not MATLAB-runtime evidence
unless it is actually run and recorded, and it is not hardware, HIL, field,
real-time, or operational-radar validation.
