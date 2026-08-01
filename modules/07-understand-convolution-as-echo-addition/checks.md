# P07 Checks — Understand Convolution as Echo Addition

## Guiding question

What is convolution actually doing at each output sample?

## Baseline observation checks

1. Where are the three nonzero channel taps, and what do their horizontal and
   vertical coordinates mean?
2. Does each path row preserve the seven-sample pulse shape? Which operations
   change its position, magnitude, and sign?
3. At `n = 14`, which `x[n-k]` value does each tap select? Do the three plotted
   bars add to the printed `y[14]`?
4. Are both manual/explicit and explicit/`conv` maximum errors below
   `comparison_tolerance_v`?

Expected: taps are at `0`, `5`, and `9` samples with gains `1.00`, `0.60`, and
`-0.35 V/V`. Delay shifts a whole copy; gain scales or inverts it. Every output
sample is the signed sum of its visible path terms, and all three correct
constructions agree to numerical precision.

## Predict, then verify

1. The pulse peak is at input sample `n = 8`. Before reading the output, predict
   the centers of its direct and two echo copies. Explain why overlap can change
   the actual height at those samples.
2. If only the middle delay changes from `3` to `7` samples, predict what moves
   and what stays fixed. Verify with Sweep 1.
3. If only the third gain changes from `-0.35` to `0.35 V/V`, predict which
   samples move, which values change sign, and whether positive overlaps
   reinforce or cancel. Verify with Sweep 2.
4. If the input becomes a unit impulse at `n = 0`, predict the entire output.

## Interpretation checks

Mark each statement true or false and correct every false statement.

1. A tap at delay nine means the channel adds the scalar `-0.35` only at output
   sample nine.
2. For a fixed `n`, convolution multiplies every valid `x[n-k]` by `h[k]` and
   adds the products.
3. A negative real tap can cancel part of a positive overlapping contribution.
4. Changing a tap's delay changes the shape of the copied pulse.
5. Three matching implementations prove a physical radar channel is LTI.

Expected: false, true, true, false, false. A tap creates a shifted, scaled copy
of the whole input; delay moves rather than reshapes it; and deterministic model
agreement is not physical-channel validation.

## Failure classification

- Correct shape but every echo is one sample late: check the zero-based delay
  versus one-based MATLAB storage conversion.
- Late output is missing: check whether full `N_x + N_h - 1` linear support was
  cropped.
- Samples are wrong only where path copies overlap: check whether the code
  overwrites instead of accumulates contributions.
- Negative taps appear as positive peaks: check whether magnitudes were added
  before signed or complex samples.
- A guard fails before allocation: restore finite real controls, three ordered
  taps, matching gain/delay lengths, and the fixed resource ceilings.

## Recovery, isolation, compatibility, and resource bounds

Recovery from the broken case means adding every term at occupied output
samples, then comparing with full linear convolution. Recovery from malformed
edits means restoring committed controls and rerunning from private seed 707.
Re-running replaces only tagged P07 figures; no persistent files, external
transactions, or learner progress require rollback.

The baseline is capped at 256 input samples, 512 output samples, eight taps,
eight cases per sweep, and 64 animation frames. All loops are finite; the
committed animation pauses for less than one second total and can be disabled
with a zero pause. Ctrl+C is the applicable cancellation mechanism if graphics
block. There is no asynchronous job, callback, service wait, file/network/device
I/O, or background resource to cancel. The lab uses base MATLAB only, a private
`RandStream`, explicit loops, and tagged figures; it preserves unrelated figures
and the global random stream.

## Teach-back completion

In two or three sentences, answer the guiding question using one concrete
baseline tap and the frozen `n = 14` sample. Include why the overwrite case is
not convolution.

A complete teach-back says that each `h[k]` selects, delays, and scales
`x[n-k]`, and that `y[n]` is the signed sum of all such products at that output
index. It connects, for example, `h[5] = 0.60` to one five-sample-delayed input
copy, predicts copy centers at samples `8`, `13`, and `17`, and explains that
overwrite loses a contribution wherever copies overlap.
