# Walkthrough: watch two valid tracks exchange their histories

Run `experiment.m` from this module directory. It is finite and stateless. It
uses private seeded arithmetic, does not alter MATLAB's global random stream,
and retains its outputs in `p59_results`.

## Baseline observation

Before Figure 1, make one prediction: when the two position predictions overlap,
what measurement tells the tracker which report belongs to the earlier Track 1
history?

Figure 1 shows two equal-speed paths crossing at the center. The noisy dots are
position reports; their colors are truth used only for your audit. The second
panel shows an auxiliary cross-track velocity measurement. The reports arrive
in alternating column order, so report index is not identity.

Figure 2 first shows the position-only track estimates. Then read its identity
history one row at a time. Both rows are correct through scan 13. From scan 14
through scan 25, Track 1 follows Truth B and Track 2 follows Truth A. Confirm
the console metrics:

```text
Position-only: wrong links = 24 links, identity transitions = 2 transitions
```

The tracker did not lose either confirmed slot. It exchanged which physical
target each slot represented.

## Processing transition: add normalized velocity

Figure 3 compares the two `2 x 2` cost matrices at scan 14. Position-only cost
is built from metres divided by `sigma_p`; the enriched cost adds velocity
residuals divided by `sigma_v`. Both totals are dimensionless.

Read the velocity-aware identity history. It remains Truth A for Track 1 and
Truth B for Track 2 on every scan of the reviewed record:

```text
Velocity-aware: wrong links = 0 links, identity transitions = 0 transitions
```

Nothing about the position reports or alpha-beta update changed. The new
information changes which report is allowed to feed each history.

## Sweep 1: position measurement noise

Figure 4 changes only

```matlab
position_noise_sweep_m = [2 6 10];
```

Each point summarizes 200 paired trials. As the position cloud broadens, the
two permutations become harder to distinguish. Compare both failure frequency
and mean wrong links: the first asks whether any failure occurred; the second
shows how long and how widely it persisted.

The velocity-aware curve stays lower in the reviewed cases but does not stay at
zero. That is the completion condition's “lowers its probability,” not a claim
of perfect identity.

## Sweep 2: update interval

The left panel of Figure 5 changes only

```matlab
update_interval_sweep_s = [0.5 1 2];
```

All cases contain 25 scans centered on the crossing. Larger intervals place
the neighboring samples physically farther from the exact intersection and
reduce each residual's velocity correction through `(beta/dt)r`. Failure falls
under those two consequences in this fixed-gain, constant-velocity scene. State
the scope aloud: maneuver and process-noise effects are absent, so this is not
a recommendation to lower radar update rate.

## Sweep 3: closest approach

The right panel of Figure 5 changes only

```matlab
closest_approach_sweep_m = [0 12 24];
```

Velocity, measurement noise, gains, and number of scans stay fixed. Increasing
miss distance supplies stronger spatial separation. Verify that both methods'
failure frequency falls and the velocity-aware curve remains lower.

## Broken report reuse and recovery

Figure 6 deliberately removes the chosen report column from neither track's
competition. Each track independently takes its nearest report. Yellow markers
show 12 scans on which both tracks consume one report. This violates the
one-to-one association invariant inherited from P57 and causes coalescence.

Recovery uses the same arrays and restores:

```text
select minimum -> remove selected track row -> remove selected report column
```

It also restores the reviewed normalized velocity cost. `recovery_exact = 1`
means assignment, position history, and velocity history exactly equal the
original velocity-aware result.

## Failure interpretation and recovery from bad inputs

If the baseline does not show 24 wrong links, rerun from the top with seed
5908 and the reviewed controls. If both tracks select the same report outside
the broken section, inspect column removal. If velocity dominates unexpectedly,
check that its residual is divided by `sigma_v^2` before adding it to position
cost.

Malformed, complex, nonfinite, nonpositive, misordered, duplicate-baseline, or
oversized controls are rejected before random generation, large allocation, or
figure creation. Correct the named value and rerun; the script persists no
partial experiment state.

If a foreground run or graphics render blocks, press Ctrl+C, close only figures
tagged `P59`, restore the reviewed controls, and rerun from the top. There is no
timer, worker, callback, network operation, input file, or output file to
cancel. Learner CLI tests use a temporary repository and `HOME` with a
10-second subprocess timeout, so they do not alter personal `.learning/` state.

Repository rollback is limited to P59's module files, P59 test/evidence and
catalog additions, plus restoring only P59 manifest status to `scaffolded`.
P58 remains the prerequisite and later module state is not frozen by P59.

## Concept connection

P57 established gating and one-to-one nearest-neighbor mechanics. P58 managed
track existence after hits and misses. P59 shows that valid live tracks and a
valid one-to-one assignment can still carry the wrong identities. Richer
features reduce ambiguity; joint or multi-hypothesis methods would represent
it more honestly, but they cannot recover information the sensor never
measured.

## Expected observations

- the truth paths and position predictions overlap at the crossing;
- seed 5908 makes position-only greedy association swap both identities;
- the swap has 24 wrong links but only two identity transitions;
- normalized velocity preserves identity in the reviewed baseline;
- more position noise increases failure in the paired sweep;
- more closest separation decreases failure;
- update-interval direction is specific to the exact-CV sampled scene;
- independent row minima reuse one report on 12 scans; and
- restoring one-to-one velocity-aware association exactly recovers the result.

Static tests and a Python oracle are not MATLAB runtime or visual evidence.
They provide no hardware/HIL, field, real-time, RT1/RT2, Unreal, signing,
deployment, staging, or production validation.
