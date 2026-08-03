# P43 walkthrough: Use a Fixed Detection Threshold

Guiding question: **Why does a threshold that works in one noise level fail in another?**

Run `experiment.m` section by section. Keep
`fixed_threshold_amplitude` visible. The important constraint is that this
number does not change during either valid sweep.

## Baseline: turn range-cell amplitudes into conditioned decisions

Run through **Baseline ensemble**.

1. In Figure 1, identify the black truth markers and red threshold crossings.
   A crossing outside the truth markers is a false alarm; a truth marker below
   the line is a miss.
2. In Figure 2, use the target-absent H0 distribution for false alarms and the
   target-present H1 distribution for detections and misses.
3. Read the empirical/model baseline values. The empirical result need not be
   exact, but it should be near the 1% design false-alarm probability and the
   Gaussian reference.

Expected observation: one absolute line makes sensible decisions at the noise
RMS for which it was calibrated. Most H0 samples are below it, and most H1
samples are above it.

Common mistake: dividing all crossings by all cells. `P_FA` is conditioned on
H0; `P_D` and `P_miss` are conditioned on H1.

## Sweep 1: change only noise RMS

Run **Sweep 1** with
`noise_rms_ratios = [0.75 1.00 1.25 1.50 2.00]`.

- Threshold, target amplitude, trial count, and standardized noise samples
  stay fixed.
- The upper plot tracks H0 crossings as the distribution spreads.
- The lower plot tracks H1 misses for the same positive target amplitude.

Expected observation: false alarms rise monotonically above the 1% design
point as RMS increases. Misses also rise because noise increasingly pushes
some target-present amplitudes below the fixed line.

For one controlled variation, change the final ratio from `2.00` to `1.75`,
rerun from validation, and compare only that endpoint. Restore `2.00` before
retaining results.

Common mistake: saying noise power doubled when RMS doubled. Doubling RMS
quadruples variance/power in this model.

## Sweep 2: change only the clutter pedestal

Run **Sweep 2** with
`clutter_pedestal_ratios = [0 0.5 1.0 1.5 2.0]`.

- Noise RMS, target amplitude, threshold, and random samples stay fixed.
- The positive pedestal shifts both H0 and H1 upward without widening them.
- Compare the false-alarm count with the missed-target count rather than
  judging total crossings alone.

Expected observation: false alarms rise as the target-absent background moves
toward the line. Misses may fall, but that does not mean selectivity improved;
the detector increasingly calls background a target too.

For a second one-variable variation, change the final pedestal ratio to `1.75`
and inspect the endpoint. Restore `2.0` afterward.

Common mistake: describing this positive pedestal as increased white-noise
variance. It is an explicit mean shift used to isolate a different calibration
failure.

## Intentionally broken case: normalize with oracle background knowledge

Run **Intentionally broken case**.

Expected observation: the dashed curve stays flat across noise RMS. That may
look like a successful fixed threshold, but the code divided every sample by
its case's true RMS. In native amplitude units, the decision line changed in
every case.

Explain the failure in one sentence: the result is adaptive because it uses
`case_sigma`; it cannot be evidence that one absolute threshold works across
background scales.

Common mistake: calling any constant number in normalized coordinates fixed.
The physical threshold is fixed only when the normalization scale is fixed.

## Recovery

Run **Recovery**. It reapplies the single
`fixed_threshold_amplitude` directly to each native-unit H0 sample. Confirm:

- `results.broken_fixed_threshold_claim` is false;
- `results.recovery_exact` is true;
- `results.recovered_pfa` matches `results.noise_empirical_pfa` exactly;
- false-alarm and miss counts retain the H0 and H1 denominators separately.

The recovery recomputes decisions from the retained standardized noise, not by
aliasing the baseline decision array. A clean rerun reconstructs the same
samples from private seed `4301`.

## Concept connection

Complete this sentence aloud:

> A fixed threshold is an absolute ___; changing background RMS changes the
> threshold measured in ___, while changing a pedestal moves the ___ toward
> the line.

The intended connection is amplitude, noise standard deviations, and H0
distribution. P43 exposes the problem. P44 explores threshold tradeoffs, and
P45 estimates local background to make adaptation explicit.

## Interruption, cancellation, recovery, and rollback

Pressing `Ctrl+C` cancels the bounded local calculation. It may leave partial
P43 figures or workspace variables, but no file, network, device, worker,
timer, or external transaction exists. Rerun from the top to clear only
figures tagged `P43`, reset workspace variables, validate bounds before
allocation, and recreate the private-seed data.

Repository rollback is file-local: remove P43's added learning artifacts,
focused test, evidence, and approved catalog text, then restore only P43's
manifest status to `scaffolded`. Preserve P42, P44 and later canonical
identities, ignored `.learning/` progress, and the operator-managed active
batch contract.
