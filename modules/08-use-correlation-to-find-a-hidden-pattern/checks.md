# P08 Checks — Use Correlation to Find a Hidden Pattern

## Guiding question

How can a known waveform be located inside noise and delay?

## Baseline observation checks

1. What are the units of the reference, received record, lag, and correlation
   output in this experiment?
2. At lag `137`, what does each bar in the upper correlation figure multiply,
   and what does the last cumulative value equal?
3. Does the largest signed peak occur at `137 samples` (`17.125 ms`)? Is the
   delay error zero?
4. Is the explicit-versus-`conv` maximum error below
   `comparison_tolerance_v`?

Expected: the reference is dimensionless, `x[n]` and `r_xs[lag]` are volts, and
lag is in samples (with milliseconds derived from `fs`). Each bar is
`x[137+m]s[m]`; their signed sum is the correlation peak. The deterministic
baseline estimates the configured start, and both correct constructions agree
to numerical tolerance.

## Predict, then verify

1. If hidden amplitude rises while the exact noise stays fixed, predict what
   happens to the true-lag correlation and to the true delay.
2. If noise standard deviation rises while the hidden copy stays fixed, predict
   what happens to random off-peak structure. Does one seed prove a probability?
3. Before Sweep 2, predict which separation should merge most strongly and
   which should produce two distinct peaks.
4. If the positive hidden copy starts at sample zero, predict the correct lag
   and the broken raw-index report for a 26-sample reference.
5. If the hidden amplitude changes sign, predict the signed correlation peak
   before deciding whether `max` or `max(abs(...))` is appropriate.

## Interpretation checks

Mark each statement true or false and correct every false statement.

1. Correlation locates a pattern by comparing one received sample at a time.
2. Under P08's convention, positive lag means the reference begins later in the
   record.
3. A larger reference energy raises an unnormalized correlation peak even if
   similarity has not improved.
4. The index returned by `max(conv(x,fliplr(s)))` is already the physical delay.
5. Two merged correlation peaks prove that only one physical target exists.
6. Matching explicit loops and `conv` validates the synthetic discrete model,
   not an operational radar receiver.

Expected: false, true, true, false, false, true. Correlation adds a full set of
aligned products; vector index requires a lag origin; overlapping
autocorrelation lobes limit resolution; and deterministic model agreement is
not physical validation.

## Failure classification

- Estimate is exactly `M-1` samples late: check vector index versus lag origin.
- Peak has the right magnitude but negative sign: check hidden polarity or
  phase before switching to an absolute-peak search.
- All cases move when only amplitude should change: verify the same noise
  realization and delay are reused.
- Late copy weakens near a record boundary: check whether the reference is
  truncated and whether overlap normalization is needed.
- Several comparable peaks repeat periodically: inspect reference
  autocorrelation and ambiguity, not only noise level.
- A guard fails before allocation: restore finite real controls, integer delays,
  in-record support, increasing sweep vectors, and fixed resource ceilings.

## Recovery, isolation, compatibility, and resource bounds

Recovery from the broken case means mapping the maximum through
`correlation_lags_samples`, not changing the correct correlation values.
Recovery from malformed edits means restoring committed controls and rerunning
from private seed 808. After validation, re-running replaces only tagged P08
figures; malformed controls leave the last valid P08 figures intact. No
persistent files, external transactions, or learner progress require rollback.

The record is capped at 512 samples, reference at 64 samples, correlation at
1024 values, each sweep at eight cases, and figures at six groups. Every loop is
finite; there is no pause or external wait. Ctrl+C is the applicable cancellation
mechanism if local graphics block. There is no asynchronous job, callback,
service wait, file/network/device I/O, or background resource to cancel. The lab
uses base MATLAB only, a private `RandStream`, explicit loops, and tagged figures;
it preserves unrelated figures and the global random stream.

## Teach-back completion

In two or three sentences, answer the guiding question using the baseline lag
convention and the broken-case offset. Include why the peak can stand out even
when the raw waveform does not.

A complete teach-back says that P08 slides the known reference across the
record, multiplies aligned signed samples, and sums them, so coherent agreement
creates a peak at lag `137` while random noise contributions partly cancel. It
states that the maximum's vector index is not automatically delay—the 26-sample
reference creates a `25`-sample origin offset—and that the explicit lag vector
recovers the hidden start.
