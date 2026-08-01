# P08 Walkthrough — Use Correlation to Find a Hidden Pattern

## Guiding question

How can a known waveform be located inside noise and delay?

## Before running

P07 is the prerequisite. Run `experiment.m` from this module folder in base
MATLAB. It writes no files or learner progress, preserves the global random
stream and unrelated figures, and closes only earlier P08-tagged figures. Named
script variables in the current workspace are created or replaced.

Every loop and array is finite and bounded. There is no animation, pause,
external wait, background task, callback, or asynchronous job. If graphics
block in the local environment, stop the finite script with Ctrl+C and rerun
from the top.

## Baseline

1. Inspect **known pattern hidden in a noisy record**. Read the reference as a
   signed dimensionless shape. Then look only at the full received record. Do
   not use the revealed zoom to guess the start.
2. Move to **explicit similarity versus relative delay**. In the upper panel,
   follow the bars `x[D+m]s[m]`. Positive and negative chips both contribute
   positively when the hidden pattern aligns with the same signed reference.
3. Follow the cumulative curve. It is one visible correlation sum, not a
   probability and not an energy detector.
4. In the lower panel, locate the largest signed peak. Read its horizontal
   coordinate as zero-based relative lag. Confirm that the configured and
   estimated delays are both `137 samples`, or `17.125 ms` at `8000 samples/s`.
5. Read the printed explicit-versus-`conv` maximum error. It must be below
   `comparison_tolerance_v`. Agreement checks the implementation, while the
   explicit sum explains the operation.

Observation question: why can the individual noisy samples look unconvincing
while their signed products form a strong peak at one alignment?

## Sweep 1

Run **Parameter sweep 1 - change only hidden amplitude**. Compare `0.10`,
`0.30`, and `0.65 V` while delay, code, record length, and every noise sample
remain fixed.

- The response at the true lag increases by amplitude change times code energy.
- A weak hidden copy can lose the global-maximum contest to a random noise peak.
- Increasing amplitude changes vertical peak strength, not the true horizontal
  delay.
- The legend reports the estimated delay for each case; treat a wrong weak-case
  estimate as a low-output-SNR observation, not a changed propagation delay.

## Controlled noise comparison

Run **Controlled noise comparison - change only noise standard deviation**.
The configured standard deviations are `0.20`, `0.50`, and `0.90 V`. The clean
hidden copy and standard-normal sample sequence are identical in every case.

- Random sidelobes grow as the noise multiplier grows.
- The clean aligned contribution stays fixed.
- A single seed illustrates a mechanism; it does not estimate detection
  probability or guarantee success for every noise realization.

## Sweep 2

Run **Parameter sweep 2 - change only second-copy separation**. A `0.50 V`
second copy begins `1`, `8`, or `32 samples` after the first. Both amplitudes,
the first delay, code, and noise remain fixed.

- At one-sample separation, the two autocorrelation main lobes overlap and look
  like one deformed dominant peak.
- At eight samples, inspect whether a shoulder or two local peaks is visible.
- At 32 samples, the two known delays have distinct peaks.
- Separation changes only horizontal spacing. It does not change either path's
  amplitude or the reference's inherent autocorrelation shape.

Connect this to radar carefully: two delay peaks are two modeled copies, not
validated targets or calibrated ranges.

## Broken case

Run **Deliberately broken case - report the convolution index as delay**. The
correlation values are still correct, but the red reported delay is `25 samples`
late because the 26-sample reference makes the correlation vector start at lag
`-25`, not zero.

Classify this as a coordinate-mapping error. It is not a noise failure, a wrong
reference, or a broken correlation sum. Subtracting one only converts MATLAB
storage to a zero-based vector index; it does not attach the physical lag origin.

## Recovery

Use `correlation_lags_samples(broken_peak_index)`. The recovered green marker
returns to `137 samples`, and `recovery_delay_error_samples` must be zero.

If an edited control is malformed, an early assertion should fail before record,
correlation, sweep-output allocation, or replacement of the last valid P08
figures. Restore the committed finite scalar, vector, fit, ordering, and
resource-ceiling controls. Re-running from private
seed 808 recovers the exact synthetic setup and replaces only P08-tagged figures.
There is no persistent file, external transaction, or learner state to roll back.

## Concept connection

P07 formed an output by sliding one signal relative to another and adding
products. P08 gives that sliding sum a new question: at which relative delay
does the received record most resemble a known reference? The answer is the lag
of the correlation peak, subject to waveform ambiguity and noise.

State the lag convention aloud, then explain how coherent aligned products make
the hidden start visible. Keep echo-to-range conversion separate until the later
round-trip-delay module.

## Completion handoff

Use `checks.md`. To meet the canonical completion condition, estimate the hidden
start from the correlation plot without using the revealed time zoom. Finish
with the short teach-back before recording personal completion locally.
