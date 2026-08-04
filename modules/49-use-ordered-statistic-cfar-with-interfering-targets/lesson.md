# Lesson: robustness comes from choosing which reference sample can vote

## Guiding question

How can CFAR resist several contaminated training cells?

## Start with the physical window

A cell under test (CUT) is surrounded by guard cells and then training cells.
The guards keep the CUT's own response out of the background estimate. Nearby
targets can still land farther away, inside the training set. They are not
background, but an ordinary cell-averaging detector gives every one of them a
vote. Several strong votes lift the mean and can mask a weaker CUT.

This experiment uses square-law power. In homogeneous complex Gaussian noise,
each training power is an independent exponential random variable with local
mean power `mu`. Training-cell interferers are added as larger noncoherent
point powers. Sweep CUTs use a deterministic complex amplitude plus complex
Gaussian noise, whose magnitude squared supplies a target-present power sample.
P45 introduced the stencil, P46 showed contamination, P47 required equal-`Pfa`
comparisons, and P48 showed why nonhomogeneous references need deliberate
handling.

## CA-CFAR: every reference cell contributes

With `N` training powers `x_1, ..., x_N`, CA-CFAR uses

```text
m_CA = (1/N) sum_i x_i
threshold_CA = alpha_CA m_CA
alpha_CA = N(Pfa^(-1/N) - 1)
```

One target of power `I` raises the mean by `I/N`; several targets add their
contributions. This averaging is excellent for homogeneous background but is
not an outlier rejection rule.

## OS-CFAR: sort, then select one rank

Sort the same powers in ascending order:

```text
x_(1) <= x_(2) <= ... <= x_(N)
threshold_OS = alpha_k x_(k)
```

If `q` interfering targets become the `q` highest samples, the selected sample
still comes from the clean group while

```text
q <= N-k.
```

That is a capacity statement, not a promise that the statistic is numerically
unchanged. As outliers displace clean samples upward in the sorted list,
`x_(k)` becomes a higher clean order statistic and usually rises. Once
`q > N-k`, the selected rank enters the contaminated tail and the threshold can
jump sharply.

For the baseline, `N = 24` and `k = 18`, so six higher samples can be bypassed.
Four nearby targets fit inside that budget. CA sees all four powers; OS
selects below them.

## Each rank needs its own calibration

Under independent exponential background, the exact homogeneous false-alarm
probability for ascending rank `k` is

```text
Pfa_OS(alpha_k)
  = product from j=0 to k-1 of (N-j)/(N-j+alpha_k).
```

The script solves this visible monotone equation with fixed, bounded bisection.
It does not call a CFAR toolbox object. For `N = 24`, `k = 18`, and
`Pfa = 10^-3`, the scale is about `6.50243`. A scale calibrated for rank 18 is
not valid for rank 12 or 22. Reusing it after a rank edit is the broken case:
a lower selected sample with too-small a multiplier can produce excessive
false alarms. Recovery means recalibrating `alpha_k` for every candidate rank.

## Read the three tradeoffs

The count sweep changes only how many strong reference cells are contaminated.
CA degrades immediately; rank-18 OS remains useful through its capacity region
and then falls when the count crosses six.

The strength sweep holds four contaminators fixed. Their increasing power
drives the CA mean upward. OS is much less sensitive because those four values
remain above the selected sample.

The rank sweep holds four 20 dB contaminators fixed and recalibrates every
rank. Lower ranks leave more outlier slots but use a noisier, lower statistic
and a larger multiplier. Higher ranks can give good homogeneous efficiency,
but ranks above `N-q` select contaminated data in this scene. There is no rank
that is best without an expected contamination model.

## Limiting cases

- With `q = 0`, CA and calibrated OS both meet the same homogeneous `Pfa`, but
  finite-sample detection performance differs because their estimators differ.
- With `k = N`, OS selects the maximum and has zero high-outlier capacity. One
  strong training target can dominate it.
- With `k = 1`, OS selects the minimum and can bypass `N-1` high outliers, but
  its required multiplier is very large and the statistic is variable.
- With infinitely strong outliers but `q <= N-k`, their powers no longer
  directly set `x_(k)`; their count still changes which clean order statistic
  occupies rank `k`.
- With `q > N-k`, the selected sample becomes an outlier in the strong-target
  limit, so OS masking is unavoidable for that rank.
- As `N` grows, more references can reduce sampling uncertainty only if the
  added cells still represent the same local background.

## What this model does not prove

The lesson is a bounded simulation with independent exponential background,
point-power training contaminators, and deterministic-amplitude target-present
CUT trials. It does not validate correlated or measured clutter, target
fluctuation, sidelobes, clutter edges, 2-D neighborhoods, a rare-event
false-alarm rate, hardware, or operational radar. P50 extends the geometry,
P51 broadens the stress cases, and P52 owns dedicated `Pfa` validation.

The important connection is physical: OS-CFAR buys resistance by limiting how
many of the largest reference samples may influence the threshold. The rank is
therefore a design assumption about how many cells may be contaminated, and
its calibration is part of the detector—not an optional plotting choice.
