# P64 walkthrough: Observe, Change One Control, Break, Recover

Guiding question: How can sum and difference beams estimate small angle error around boresight?

Run `experiment.m` once from this module directory. The script creates five
figures and retains the numerical record in `p64_results`.

## Baseline observation 1: overlapping beams become an error sensor

Look only at **P64 beam and comparator patterns**.

1. In the top panel, find where `|L|` and `|R|` cross.
2. Notice that `|Sigma|` remains strong while `|Delta|` reaches zero there.
3. In the bottom panel, follow the red ratio curve from `-4` to `+4 deg`.

Expected observation: `Re{Delta/Sigma}` is zero at boresight and rises
monotonically through the calibrated interval. Its sign says which squinted
beam is stronger.

Concept connection: the two simultaneous voltages provide a common-amplitude
reference and a signed imbalance without scanning the antenna.

## Baseline observation 2: one snapshot versus coherent averaging

Now inspect **P64 noisy baseline estimate**.

The blue and green dots are one angle measurement per receiver-noise snapshot.
The red lines come from averaging complex `Delta` and `Sigma` channels first,
then forming their ratio.

Expected observation: individual estimates scatter around the `+2 deg` truth;
the coherently averaged estimate is much closer. Samples that exceed the local
ratio calibration saturate visibly at `+/-4 deg` rather than being
extrapolated into a false global bearing.

Do not interpret more snapshots as a narrower physical beam. They reduce
random receiver error for this coherent target; the fixed weights and aperture
have not changed.

## Sweep 1: beam squint

Open **P64 beam-squint sweep**. Compare `1.5`, `3.0`, and `5.0 deg` squint while
the array, spacing, and angle grid stay fixed.

Expected observations:

- larger squint makes the ratio curve steeper near zero;
- larger squint also lowers the boresight sum voltage; and
- sensitivity and usable sum-channel strength must be judged together.

One-variable change: edit only

```matlab
squint_sweep_deg = [1.5 3.0 5.0];
```

within the validated reviewed cases. A steeper curve is not automatically a
better global angle estimate because the ratio is still local and sum-channel
noise matters.

## Sweep 2: receiver SNR

Open **P64 SNR sweep**. Every point uses the same target and normalized noise
record; only the noise amplitude changes.

Expected observations:

- single-snapshot angle RMSE falls as SNR rises;
- the coherently averaged estimate approaches the fixed `+2 deg` truth; and
- the angle calibration curve does not change with SNR.

Concept connection: random noise controls precision, whereas the ideal beam
geometry controls the nominal ratio-to-angle map.

## Broken case: a receiver imbalance impersonates target motion

Inspect **P64 calibration mismatch and recovery**. The target is held at
boresight while only the right-channel voltage gain becomes `1.12`.

Expected observation: the dashed broken ratio no longer crosses zero at true
boresight, and the bar chart reports a positive false angle. This is a bias,
not random scatter and not real target movement.

Common interpretation mistake: saying that target amplitude failed to cancel.
A common target amplitude still cancels. The problem is unequal receiver gain,
which does not multiply both channels equally.

## Recovery

The script applies

```text
R_recovered = R_broken / 1.12
```

to the already formed broken right channel. It does not change the target
angle, regenerate data, or tune the calibration to the desired answer.

Expected observation: the recovered curve lies on the ideal curve and the
boresight estimate returns to `0 deg` within numerical tolerance.

## Failure interpretation checklist

- A ratio sign reversal suggests swapped channels or a difference-sign error.
- A constant zero-crossing offset suggests channel gain/phase calibration.
- Large angle jumps with weak `Sigma` suggest denominator failure, not rapid
  target motion.
- Saturation at `+/-4 deg` says "outside this local calibration," not "proven
  to be exactly four degrees away."
- A stable bias will not disappear merely by adding snapshots.

## Cancellation, rerun, and resource behavior

Pressing `Ctrl+C` stops the foreground script. There is no worker, timer,
network request, file output, checkpoint, or partial persistent state. Rerun
the script to reconstruct the same bounded private-noise record. Startup closes
only figures tagged `P64`, so unrelated figures and MATLAB's global random
state are preserved.

The reviewed ceilings are 16 elements, 512 snapshots, 1,001 angle samples,
five sweep cases, 20,000 private generator values per request, 500,000 working
numeric values, and five tagged figures. Input validation rejects malformed or
oversized reviewed controls before data and plots are constructed.

When these observations make sense, use `checks.md` and give the short
teach-back. Do not mark the module complete from plot production alone.
