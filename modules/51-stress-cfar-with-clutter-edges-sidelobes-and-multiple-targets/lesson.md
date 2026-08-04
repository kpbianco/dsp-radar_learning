# Lesson: Where do standard CFAR assumptions break?

## Start with the physical training window

A CFAR detector does not see a label saying “background,” “target,” or
“sidelobe.” It sees the cell under test (CUT), guard cells, and two groups of
training-cell powers. In homogeneous noise those training samples can act like
independent measurements of one local mean. At a clutter edge, beside a strong
compressed target, or inside a target group, that physical story is false.

This experiment combines four violations:

1. a 12 dB step divides low and high clutter;
2. a strong target has an explicit finite mainlobe and sidelobes;
3. weak and crowded targets occupy one another's reference windows; and
4. a broad noise-power swell makes the background nonuniform even away from
   the abrupt step.

All estimators operate on **linear square-law power**. Decibels are used only
to specify ratios or display results. Averaging dB values would estimate a
geometric mean and change the detector.

## Four answers from the same training cells

There are `T=12` leading and `T=12` lagging training cells, so `N=24`.
Let their means be `Z_L` and `Z_R`, let all reference powers be `x_i`, and let
`x_(k)` denote the kth value after an ascending sort. The four visible
statistics are

```text
Z_CA = (1/N) sum_i x_i
Z_GO = max(Z_L, Z_R)
Z_SO = min(Z_L, Z_R)
Z_OS = x_(k), with k = 18
```

Each threshold is `alpha_variant * Z_variant`; the CUT is detected only when
its power is strictly greater than that threshold. The choice is physical:

- CA blends both sides. A few large target-contaminated cells pull its mean up.
- GO follows the larger side. It protects a high-side clutter edge but can mask
  a low-side target beside that edge or a strong contaminator.
- SO follows the smaller side. It can ignore one contaminated side, but on the
  high side of a clutter edge it may use low-side references and admit false
  plots.
- OS ignores the largest `N-k=6` samples in the strong-outlier limit. That is a
  finite capacity, not immunity: seven strong contaminants reach the selected
  order statistic, and moderate sidelobes can change lower ranks too.

No selector is pointwise “most conservative” once it receives its own
calibration multiplier. Inspect the actual threshold, not only the raw
statistic.

## Equal nominal Pfa requires unequal scale factors

For independent exponential H0 power, CA's exact finite-`N` calibration is

```text
alpha_CA = N * (Pfa^(-1/N) - 1).
```

GO and SO use the maximum or minimum of two gamma-distributed side means, so
the script evaluates their exact homogeneous probabilities from finite sums
and solves for each multiplier with bounded bisection. OS uses

```text
Pfa_OS(alpha) = product from j=0 to k-1 of (N-j)/(N-j+alpha),
```

again solved by bounded bisection. At `Pfa=10^-3`, `N=24`, and `k=18`, the
four multipliers are approximately `8.0045`, `7.0890`, `10.4809`, and
`6.5024` for CA, GO, SO, and OS. “Same nominal Pfa” means each statistic is
calibrated under the same homogeneous model; it does not mean the multipliers
are equal or that achieved false-alarm rates remain equal in the stress scene.
P52 owns rare-event validation of achieved Pfa.

## Read disagreements from training contents

The representative-CUT figure retains CUT power, leading and lagging means,
the CA mean, and the selected OS power. These explain the major outcomes:

- At the weak neighbor, strong-target response energy enters reference cells.
  CA and often GO rise; SO can use a cleaner half; OS depends on how many high
  samples reach rank 18.
- At the low-side edge target, the lagging references include high clutter.
  GO deliberately follows that side, while SO deliberately avoids it.
- At the crowded target, other target peaks occupy both reference halves.
  Every statistic can be contaminated, and OS stops being robust when the
  number and strength of outliers reach its selected rank.
- In the smooth swell, neither side represents one constant local mean. A
  detection there can reflect nonuniform-background mismatch rather than a
  homogeneous H0 event.

The script assigns exactly one scene-based cause to every detector-mask
disagreement. It also separates known target-center hits/misses from
non-target threshold crossings. A crossing on modeled target sidelobe energy
is an operational false plot, not an H0 false alarm; a background-only crossing
is the statistical false-alarm category relevant to Pfa.

## What the two sweeps isolate

The clutter-contrast sweep reuses the same unit-power realization, target
geometry, ripple, and noise swell while changing only the step from 0 through
18 dB. GO should become useful for suppressing high-side edge crossings while
SO's clean-side preference becomes risky. Realized counts need not be perfectly
monotone in one short profile.

The target-density sweep uses paired trials and changes only how many strong
point targets contaminate the 24 reference cells. It crosses the rank-18 OS
capacity boundary at six versus seven high samples. CA responds to contaminator
energy, GO and SO depend on which halves are occupied, and OS depends on both
count and rank.

## Intentionally broken calibration and recovery

The broken case reuses CA's multiplier for GO, SO, and OS while claiming that
all four still have `Pfa=10^-3`. Exact homogeneous formulas expose the error:
GO becomes too conservative, SO too permissive, and OS too conservative for
this geometry. Raw crossing counts are then an unfair detector comparison.

**Recovery:** restore the separately solved CA, GO, SO, and rank-specific OS
multipliers before attributing differences to the stressors. Calibration makes
the homogeneous starting point fair; it does not repair nonhomogeneity or
training-cell contamination.

## Limiting cases and model boundary

- With zero clutter contrast, no target response in the references, and a
  locally constant mean, the four detectors satisfy their common nominal Pfa
  even though their realized masks differ.
- If the two side means are equal, GO and SO use the same raw statistic, but
  their thresholds still differ because their calibrated multipliers differ.
- One badly contaminated side favors SO; a high-side clutter edge favors GO.
- At most `N-k` sufficiently high outliers can sit above OS rank `k` without
  forcing that rank into the outlier group.
- Larger training windows reduce estimate roughness only while the samples
  still describe the CUT's background. More mismatched data is not better data.
- The power-domain model adds deterministic noncoherent target-response power
  to independent exponential background power. It does not model coherent
  phase addition, correlated measured clutter, fluctuating targets, detection
  grouping, or an operational radar.

## Prerequisite connections

P45 introduced explicit linear-power CA-CFAR. P48 separated the two side means
for GO and SO. P49 calibrated an ascending OS rank and exposed `N-k` capacity.
P50 established complete-stencil/no-decision boundaries. P51 combines those
operations in one adverse scene; P52 separately measures achieved Pfa rather
than inferring it from this illustrative profile.
