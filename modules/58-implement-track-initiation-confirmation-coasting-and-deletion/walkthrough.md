# Walkthrough: watch a report earn and lose persistence

Run `experiment.m` from the module directory. Work through one figure at a
time. The script has no file, network, worker, or learner-progress side effect.

## Baseline observation

Before Figure 1, make one prediction: will the target's confirmed ID survive
two consecutive missed reports when the coast allowance is two scans?

Figure 1 shows the fixed scan record. The black line is target truth in
Cartesian position, green circles are available noisy target reports, black x
markers are intentional misses, and red x markers are seeded false alarms.
Truth colors exist only for learning and scoring. The track manager receives
an unlabeled position list on each scan.

Figure 2 shows every trajectory initiated from an unassigned report. Most
short traces belong to isolated false alarms. The lower panel separates
tentative, confirmed-with-hit, and coasting counts. Observe that a false report
does create state temporarily; the safeguard is not “never initiate,” but
“do not grant permanence without repeated evidence.”

Figure 3 is the lifecycle record. State codes are `0 inactive`, `1 tentative`,
`2 confirmed`, `3 coasting`, and `4 deleted on this scan`. Follow the target
track through these transitions:

1. Birth as tentative on scan 4.
2. Hits on scans 4, 5, and 7 produce score 3 in the four-scan window.
3. Confirmation occurs on scan 7.
4. Misses on scans 12 and 13 produce two blue coasting cells.
5. The scan-14 hit returns the same ID to confirmed and resets misses.
6. After the last hit on scan 24, scans 25 and 26 coast; scan 27 is deletion.

The rolling score falls to two during the short dropout, but the confirmed
track survives because maintenance uses consecutive misses, not the original
confirmation threshold.

Read the console metrics in their declared units:

- target confirmation and deletion scan indices;
- target coast scans;
- false tracks initiated, deleted, and confirmed (tracks);
- peak and final active-track counts (tracks);
- broken-policy false confirmations and final active count (tracks);
- lifecycle runs and bounded track-report pair slots; and
- exact recovery as a logical value.

Expected baseline values include target confirmation on scan 7, deletion on
scan 27, eight false tracks initiated and deleted, zero false confirmations,
and zero active tracks at the final scan.

## Sweep 1: change only confirmation threshold M

Figure 4 reuses the exact detection arrays with:

```matlab
confirmation_m_sweep = [1 3 4];
confirmation_n = 4;
```

The gate, filter gains, target misses, false positions, and coast limit remain
fixed.

- `M=1`: true confirmation occurs on scan 4, but all eight false alarms also
  confirm.
- `M=3`: true confirmation occurs on scan 7 with zero false confirmations.
- `M=4`: true confirmation moves to scan 11 because the first tentative track
  cannot survive the early miss under a four-of-four rule.

Physical connection: `M` sets the evidence burden within a fixed observation
memory `N`. Increasing it controls false promotion at the cost of declaration
latency and possible track fragmentation.

## Sweep 2: change only coast allowance L

Figure 5 reuses the same arrays and baseline `3-of-4` policy with:

```matlab
coast_limit_sweep_scans = [0 2 5];
```

- `L=0`: the first missed scan deletes a confirmed track. The target later
  confirms again, so one physical target creates two confirmed segments.
- `L=2`: the same ID survives the two-scan gap and deletes on scan 27.
- `L=5`: the gap also survives, but stale deletion moves to scan 30.

Physical connection: coast allowance is a time budget in scans. It should be
chosen from expected detection gaps, maneuver-model credibility, and track
capacity—not from a desire to keep every display symbol alive.

## Broken case: bypass confirmation and practical deletion

Figure 6 deliberately runs `1-of-1` with a 30-scan coast allowance. It treats
one threshold crossing as proof of an object and makes stale deletion
unreachable during the reviewed record. The red active-track curve rises as
false reports arrive; all eight false tracks are confirmed and remain active
on the final scan.

Recovery restores:

```matlab
confirmation_m = 3;
confirmation_n = 4;
maximum_consecutive_coasts = 2;
```

and reruns the same detection matrices. `lifecycle_results_equal` compares
every decision-bearing baseline/recovery field, including birth, confirmation,
deletion, assignment, score, miss, position, and count histories. Do not
“recover” by using truth labels to delete clutter or by changing the random
record.

## Failure interpretation and limiting cases

If one report confirms immediately in the baseline, inspect whether `M` was
replaced by one or the birth state was created as confirmed. If a tentative
track never expires, inspect the `age >= N && score < M` boundary. If a track
deletes on its second miss when `L=2`, inspect whether deletion used `>= L`
instead of `> L`. If it reacquires with a new ID after two allowed misses,
inspect whether confirmed tracks were incorrectly tested against `score < M`.

Try limiting cases only after the baseline:

- `M=1` for immediate promotion;
- `M=N` for a consecutive-hit-like full window;
- `L=0` for delete-on-first-miss; and
- a coast limit at least as long as the remaining record for effectively
  immortal state over that horizon.

If a validation guard fires, restore finite real report positions, a logical
validity mask with `NaN` in unused slots, integer `1 <= M <= N`, nonnegative
integer `L`, strictly increasing bounded sweeps containing one baseline, and
the fixed resource ceilings. Do not raise a ceiling to hide malformed input.

## Cancellation, rollback, and deterministic recovery

Press Ctrl+C to cancel an interactive run. Partial workspace variables or P58
figures may remain. Rerun from the top: controls and resource ceilings are
validated before random draws or history allocation, only P58-tagged figures
are closed, both private seeds reconstruct the same record, and every track ID
and history is reinitialized. There is no external experiment state to roll
back or resume.

Repository learner-CLI fixtures use a 10-second subprocess timeout; this is not
a claim that MATLAB cancellation or a MATLAB runtime timeout was executed.
Repository rollback restores only P58's manifest status and removes P58-owned
artifacts/catalog additions; it does not alter P57 or any future module.

## Concept connection and completion handoff

P57 decides which gated report belongs to which prediction. P58 turns the
resulting hit/miss stream into lifecycle state. P59 will deliberately make
association ambiguous at a crossing; track management cannot repair an
identity swap that already occurred upstream.

Finish by answering: how do `M-of-N` evidence, a bounded coast allowance, and
stale deletion jointly prevent one false alarm from becoming permanent while
preserving a real target through short misses?
