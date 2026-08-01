# P07 Lesson — Understand Convolution as Echo Addition

## Guiding question

What is convolution actually doing at each output sample?

## Physical mental model

Imagine one short radar pulse reaching a receiver along three paths. The direct
path arrives first. A second path arrives later and weaker. A third path arrives
later still, weaker again, and with opposite sign in this real-valued model—a
half-cycle phase reversal. The receiver does not label the paths separately. At
each sample it measures their signed sum.

The channel response is a list of path delays and gains. P07 uses

```text
h[0] = 1.00,   h[5] = 0.60,   h[9] = -0.35,
```

with all other `h[k]` equal to zero. Each nonzero tap makes one copy of the
entire input pulse:

```text
path contribution at n = h[k] x[n-k].
```

Adding all path contributions at a fixed output sample gives linear
convolution:

```text
y[n] = sum_k h[k] x[n-k].
```

That is the whole operation. The apparent complexity comes from repeating the
same multiply-and-add for every output sample and keeping the time support
aligned.

## Read the baseline plots

The first figure exposes the short input and the three channel taps. A tap's
horizontal coordinate is a delay in samples; at `1000 samples/s`, one sample is
one millisecond. Its vertical coordinate is signed path gain in `V/V`.

The second figure keeps the three shifted, scaled pulse copies in separate
rows. The bottom row is their vertical sum. Where only one row is nonzero, the
output equals that path contribution. Where rows overlap, positive terms add
and a negative term cancels part of the positive voltage.

The third figure compares three constructions:

1. shift and scale the input once per nonzero channel tap, then add rows;
2. evaluate `sum_k h[k]x[n-k]` with explicit nested loops; and
3. call base MATLAB `conv` only as a numerical cross-check.

The plotted curves and printed maximum errors should agree to the configured
voltage tolerance. The bar chart freezes output sample `n = 14`, so each term
entering that one sum remains visible.

The bounded animation repeats this with a very small sequence. One frame is one
output index. The upper panel shows the products for that index; the highlighted
lower sample is their sum. Nothing is sliding continuously in the mathematics:
the animation is a sequence of finite indexed sums.

## What the sweeps isolate

Sweep 1 changes only the middle path delay from `3` to `5` to `7` samples. Its
gain remains `0.60 V/V`. The whole middle copy moves horizontally. Its shape and
scale do not change, but which other path samples overlap it does.

Sweep 2 fixes all delays and changes only the third path gain from `-0.70` to
`-0.35` to `0.35 V/V`. Magnitude changes the contribution size. Sign changes
whether it reinforces or cancels positive overlapping terms. In a complex radar
model a path gain also carries phase; the signed real case is the simplest
visible slice of that behavior.

## Limiting cases

- If `h[0] = 1` and every other tap is zero, convolution returns the input: the
  channel is an identity path.
- If all tap gains are zero, every product is zero and so is the output.
- If one echo gain becomes zero, that delayed copy disappears without moving
  the other paths.
- If two taps have the same delay, they are indistinguishable in this model and
  their gains add into one effective tap.
- If a path delay exceeds the observed window, its copy exists but is not seen
  in that cropped view.
- If the pulse becomes one unit sample, the output is exactly `h[n]`; this is
  the P06 impulse-response connection.
- If path spacing is wider than the pulse support, the copies do not overlap.
  When spacing shrinks, output samples can contain several contributions.
- A finite input of length `N_x` and a finite response of length `N_h` have full
  linear-convolution support `N_x + N_h - 1`. Cropping that support can discard
  real late echoes.
- One fixed convolution response assumes a linear time-invariant channel.
  Saturation breaks linearity; moving taps during the record break time
  invariance.

## Why the broken case fails

The broken loop assigns a path term to an output sample even when an earlier
path already put a term there. Assignment overwrites history. Convolution needs
accumulation:

```text
wrong:   y[n] = h[k]x[n-k]
right:   y[n] = y[n] + h[k]x[n-k]
```

The broken case deliberately uses closer delays so several shifted pulse copies
overlap. Its residual localizes the missing terms. Recovery restores addition
at every overlap and checks the result against full linear convolution.

## Radar connection and common mistakes

In a sampled radar channel, delay maps to propagation time and therefore path
length; gain describes attenuation and phase. This lab uses one-way echo-channel
language, not the target-range equation. A monostatic target range later uses
round-trip delay and the factor of two.

Do not read tap index as an absolute clock time; it is delay relative to the
input. Do not assume a negative contribution is negative energy—it is signed
amplitude and can represent phase reversal. Do not add magnitudes when the
signals are coherent; add signed or complex samples first. Do not use a
same-length crop and then claim a late echo vanished physically. Finally,
agreement among deterministic constructions validates this discrete model, not
a physical channel, radar receiver, or time-varying environment.

P06 is the prerequisite, and this lesson uses base MATLAB only. No toolbox,
external data, helper, network, or hardware operation is needed.
