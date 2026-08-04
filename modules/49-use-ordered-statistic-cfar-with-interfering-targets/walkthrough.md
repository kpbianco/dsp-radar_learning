# Walkthrough: watch contamination move through the sorted window

Run `experiment.m` from the top. It creates five P49-tagged figure groups and
a `results` structure. Work through one figure group at a time.

## Baseline — four nearby targets enter the primary training window

Keep the visible controls unchanged:

```text
N = 24 training cells
k = 18 ascending rank
primary target = range cell 128 at 15 dB
four reference interferers = 20 dB each
design Pfa = 10^-3
```

In Figure 1, locate the green primary-CUT marker. Compare its received power
with the blue CA and red OS thresholds. Expected observation: the four nearby
targets lift the CA threshold above the primary CUT, while rank-18 OS detects
it. This is masking by the reference window, not a weaker echo sample.

Figure 2 is the causal transition. The four large powers sit at the right end
of the sorted list. The CA mean moves toward them, while the selected 18th
sample remains below them. Count the six samples above rank 18: that is the
high-outlier capacity `N-k`, not a guarantee of six identical thresholds.

## Sweep 1 — change only interferer count

Figure 3 holds target SNR, interferer power, trial bank, stencil, rank, and
`Pfa` fixed. Only the number of strong training-cell interferers changes:

```text
interferer_count_sweep = [0 2 4 6 7 8]
```

Expected observation: CA detection declines as soon as strong cells enter the
mean. OS stays much higher through the bounded capacity region, then collapses
at seven when contamination first exceeds the six-cell allowance. At exactly
six, rank 18 selects the largest remaining clean sample, so some loss before
the cliff is expected; eight confirms the masked limiting behavior.

One-variable edit: change the `7` case to `5`, rerun, and compare that point
with six. Five retains one clean sample of spare margin, while six retains
none. Restore `7` afterward.

## Sweep 2 — change only interferer strength

Figure 4 holds the contaminator count at four and changes only their excess
power from `-20` through `30` dB.

Expected observation: at weak contamination, CA and OS are both useful. As
strength increases, the CA mean and threshold continue upward. The four large
values remain above rank 18, so OS detection becomes far less dependent on
their amplitude.

One-variable edit: change `interferer_excess_power_db` from `20` to `10`. This
moves the baseline target cluster and the count/rank sweeps together but leaves
the strength sweep cases intact. Predict which CA thresholds move most, rerun,
then restore `20`.

## Rank sweep — choose capacity before efficiency

The left side of Figure 5 holds four 20 dB contaminants fixed and recalibrates
each candidate rank. The vertical marker at `N-q = 20` is the largest rank
that can still select a clean sample in the infinitely strong-outlier limit.

Expected observation: ranks 12–18 preserve the weak CUT well. Rank 20 has no
spare margin and is more sensitive to the largest clean sample. Ranks 22 and
24 select contaminated powers and mask the CUT. A lower rank is not “free”:
its clean-scene distribution requires a different, often larger scale factor.

## Intentionally broken case — edit rank but reuse its multiplier

The right side of Figure 5 computes the exact homogeneous `Pfa` two ways. The
broken red curve reuses the rank-18 scale at every rank. At lower ranks the
selected sample is lower but the multiplier has not increased enough, so false
alarms exceed the design budget. At higher ranks it becomes overly
conservative.

Recovery: keep rank-specific calibration:

```text
alpha_k = calibrated_os_scale(N, k, requested_Pfa, iterations)
```

The green curve returns every candidate to `10^-3`. Only then is the rank-sweep
detection comparison fair. Do not “recover” by relabeling the broken rates or
retuning on the same plotted scene.

## Common interpretation mistakes

- “OS deletes the largest six samples.” It selects rank 18; the higher samples
  remain in the data and can affect other CUTs.
- “Six contaminants cause no change.” They change which clean sample lands at
  rank 18 even before the selected rank becomes contaminated.
- “The lowest rank is always safest.” It has more outlier capacity but a
  different multiplier, variance, and clean-scene detection cost.
- “CA and OS can share a multiplier.” Equal design `Pfa` requires calibration
  for each statistic and rank.
- “A deterministic seed proves operational performance.” It makes this
  synthetic experiment repeatable; it does not replace runtime, measured-data,
  or field validation.

## Cancellation, recovery, and rollback

Press Ctrl+C to cancel a long MATLAB run. No file, timer, worker, learner state,
or global random state needs cleanup. Rerun from the top: startup closes only
P49-tagged figures, recreates the private stream, validates all controls before
large allocations, and reconstructs the same trials.

If an edit trips a bound or assertion, restore the visible controls above and
rerun. Repository rollback removes P49-owned artifacts/catalog descriptions
and restores only P49's manifest status to `scaffolded`; it does not change P48
or any later module identity.

## Completion connection

Choose a rank for an expected maximum of four strong contaminated cells. State
its capacity `N-k`, explain why rank 22 fails here, and explain why the chosen
rank's multiplier must be recalibrated. That answer connects the sorted plot,
both contamination sweeps, and the false-alarm budget to the guiding question.
