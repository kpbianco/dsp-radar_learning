# P07 Walkthrough — Understand Convolution as Echo Addition

## Guiding question

What is convolution actually doing at each output sample?

## Before running

P06 is the prerequisite. Run `experiment.m` from this module folder in base
MATLAB. It writes no files or learner progress, preserves the global random
stream and unrelated figures, and closes only earlier P07-tagged figures. Named
script variables in the current workspace are created or replaced.

The animation has eleven frames and at most `0.08 s` pause per frame with the
committed controls. Set `animation_pause_s = 0` if a noninteractive graphics
environment should render only the final frame.

## Baseline

1. Inspect **pulse and three-tap echo channel**. Point to the input pulse and
   the taps at delays `0`, `5`, and `9` samples. Read each tap as a delay and a
   signed scale, not as a separate output spike.
2. Inspect **delayed scaled copies add into the output** one row at a time.
   Trace the same seven-sample pulse shape in every path. Confirm that its
   horizontal position changes by the path delay and its height/sign changes by
   the path gain.
3. At output samples where rows overlap, add their vertical values. The bottom
   row should contain that signed sum.
4. Move to **manual addition equals convolution**. The shifted-copy result,
   explicit equation loop, and `conv` check should lie on one another. Read the
   two printed maximum errors; both must be below `comparison_tolerance_v`.
5. Freeze on the bar chart at `n = 14`. Say each path term aloud, including a
   zero term, then confirm that the red line is their sum.
6. Watch **bounded overlap-and-sum animation**. Treat each frame as one column
   of arithmetic, not as a new channel.

Observation question: at `n = 14`, which delayed input samples are selected by
the three taps, and why can a negative path reduce the output without removing
the path?

## Sweep 1

Run **Parameter sweep 1 - change only the middle echo delay**. Compare `3`, `5`,
and `7` samples while its gain remains `0.60 V/V`.

- Track the middle copy's leading edge and peak; both move by the delay change.
- Confirm its amplitude and shape stay fixed.
- Notice that the overlap pattern changes. That changes the sum even though no
  path gain changed.
- Convert samples to milliseconds with `1000*delay/fs`.

The physical interpretation is a changing propagation time for one path while
its attenuation stays fixed.

## Sweep 2

Run **Parameter sweep 2 - change only the signed third-path gain**. Its delay
stays at `9 samples`.

- Compare gains `-0.70`, `-0.35`, and `0.35 V/V`.
- A larger magnitude makes the third contribution larger without moving it.
- Switching sign turns cancellation into reinforcement wherever positive terms
  overlap.
- Do not call the negative case a negative delay or negative energy. It is a
  signed amplitude standing in for a phase reversal.

## Broken case

Run **Deliberately broken case - overwrite instead of add at overlaps**. The
closer delays `[0, 3, 6]` force several shifted copies to occupy the same output
samples. The red crosses come from retaining only the last assigned term. The
stemmed reference retains every term.

Classify this as an accumulation error. The delay model and convolution equation
are still valid; the implementation replaced addition with overwrite.

## Recovery

Restore `y[n] = y[n] + path_term` at every overlap. The recovered output uses
full linear convolution and must match the explicit accumulation below the
voltage tolerance.

If an edited control is malformed, an early assertion should fail before large
signal or sweep arrays are allocated. Restore the committed finite scalar,
vector, ordering, and resource-ceiling controls. If graphics are interrupted,
use Ctrl+C and rerun from the top; private seed 707 recovers the deterministic
state and only P07-tagged figures are replaced. There is no persistent file,
external transaction, or learner state to roll back.

## Concept connection

P06 showed that an impulse reveals `h[n]`. P07 now reads each nonzero sample of
that response as an instruction: make one delayed, scaled input copy. At every
output sample, collect the values from all copies that land there and add them.
That sample-by-sample addition is convolution.

For radar, say which path property controls horizontal displacement and which
controls signed contribution size. Keep target-range conversion separate until
the later round-trip-delay module.

## Completion handoff

Use `checks.md`. To meet the canonical completion condition, manually predict
the three isolated copy-center samples from the pulse center plus tap delays,
then explain how overlap can change the actual summed peak values. Finish with
the short teach-back before recording personal completion locally.
