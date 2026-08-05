# Lesson: evidence earns persistence, and misses spend it

## Guiding question

How does a radar avoid creating permanent tracks from single false alarms?

A detector reports evidence from one scan. A track claims that reports across
time describe one persistent object. Those are different statements. If every
unassigned threshold crossing became a permanent track, clutter and receiver
noise would steadily fill the display with objects that never existed.

P58 puts an explicit lifecycle after P57 association. P57 answers which report,
if any, belongs to each prediction. P58 decides whether an unassigned report
has earned a new track, whether repeated hits make that hypothesis credible,
how long an established track may survive missing reports, and when stale state
must be removed.

## 1. Association happens before lifecycle management

Each active scalar Cartesian track predicts one scan ahead:

```text
x_i^-(k) = x_i(k-1) + T v_i(k-1).
```

For every predicted track `i` and report `j`, the experiment forms the residual
`z_j(k)-x_i^-(k)`, rejects pairs outside a fixed gate in metres, and repeatedly
selects the nearest remaining pair. Selecting one pair removes its track row
and report column, so one report cannot update two tracks.

The fixed gate is appropriate only because this controlled scene gives every
track the same assumed position scale. P57 shows the fuller uncertainty-aware
Mahalanobis gate. P59 later shows how nearest-neighbor identity can fail at a
crossing. Here all false reports are deliberately separated from each other
and from the target gate so the lifecycle state, rather than ambiguous
association, determines the result.

An assigned report corrects the simple position/velocity state:

```text
r_i(k) = z_j(k) - x_i^-(k)
x_i(k) = x_i^-(k) + alpha r_i(k)
v_i(k) = v_i(k-1) + (beta/T) r_i(k).
```

An unassigned active track keeps the prediction. An unassigned report starts
one new tentative track. Truth labels never enter these operations; the script
uses only each birth report's retained label afterward to classify a
target-origin or false-origin track for scoring. A false-origin track does not
become a target-origin track merely because it later steals a target report.

## 2. Initiation starts a hypothesis, not a declaration

The first unassigned report creates a tentative track with a zero velocity
guess. Its birth report counts as a hit. For track `i`, let

```text
h_i(k) = 1 when a report was assigned, otherwise 0
s_i(k) = sum of the most recent N values of h_i.
```

Before birth, missing history entries are zero. The reviewed policy is
`M=3`, `N=4`: confirm as soon as

```text
s_i(k) >= M.
```

The target reports on scans 4, 5, and 7, with a miss on scan 6. Its four-scan
history at scan 7 contains three hits, so the track confirms. A single isolated
false alarm has score one, accumulates misses, and reaches age `N` without the
required evidence. It is deleted as tentative.

This is not a probability calculation hidden in a tracker object. It is a
visible sliding binary history and a threshold. Under a simplified model where
each scan independently produces a false hit in one gate with probability `p`,
the unconditional chance of at least `M` false hits in an arbitrary `N`-scan
window is

```text
P_window = sum from j=M to N of C(N,j) p^j (1-p)^(N-j).
```

For a tentative track that already exists because its birth hit occurred, the
conditional chance of promotion within that first window is instead

```text
P_confirm | birth = sum from j=M-1 to N-1 of C(N-1,j) p^j (1-p)^((N-1)-j).
```

The distinction matters because initiation has already supplied one counted
hit. Real clutter can be correlated and gates can overlap, so both binomial
values are intuition aids, not operational calibration claims.

## 3. Confirmation is not recomputed as tentative evidence forever

Once confirmed, a track does not revert merely because its rolling `M-of-N`
score falls below `M`. Confirmation and maintenance answer different questions:

- initiation asks whether a new hypothesis has enough repeated evidence;
- maintenance asks whether an established object has been missing too long.

During the reviewed two-scan target dropout, the score falls from three to two,
but the same confirmed ID remains alive. Treating `s<M` as a deletion rule for
confirmed tracks would silently turn the confirmation window into an overly
strict maintenance rule.

## 4. Coasting spends a bounded absence allowance

Let `c_i(k)` be consecutive misses since the latest assigned report:

```text
c_i(k) = 0                         on a hit
c_i(k) = c_i(k-1) + 1              on a miss.
```

For a confirmed track with coast allowance `L`:

```text
1 <= c_i(k) <= L        -> coast on prediction
c_i(k) > L             -> delete.
```

The reviewed `L=2` permits exactly two missing scans. The target coasts on
scans 12 and 13, reacquires on scan 14, resets `c` to zero, and retains its ID.
After the final target report on scan 24, it coasts on scans 25 and 26 and is
deleted on scan 27, the third miss.

Coasting does not invent a detection. It says the motion model may carry the
object temporarily. A Kalman implementation would also grow covariance during
prediction-only scans; this small fixed-gain manager isolates lifecycle timing.

## 5. Legal state transitions

The experiment records five numeric display codes:

```text
0 inactive
1 tentative
2 confirmed with a current hit
3 coasting (confirmed but currently missed)
4 deletion event on this scan.
```

The permitted transitions are:

```text
inactive -> tentative
tentative -> tentative, confirmed, or deleted
confirmed -> confirmed, coasting, or deleted when L=0
coasting -> confirmed, coasting, or deleted.
```

A deleted ID is never recycled, never predicts again, and never receives a
later report. Deletion code 4 is retained on its event scan; later zeros mean
inactive, not that the deletion never happened.

## 6. What each controlled sweep changes

The confirmation sweep changes only `M=[1,3,4]`; `N=4`, the detections, gate,
gains, and coast limit remain fixed.

- `M=1` confirms the target immediately but also confirms all eight isolated
  false alarms.
- `M=3` confirms the target on scan 7 and confirms no false track.
- `M=4` requires four hits in the four-scan window. The first target tentative
  expires after its early miss; a replacement confirms on scan 11.

Increasing `M` rejects weak evidence but delays or fragments a true track.

The coast sweep changes only `L=[0,2,5]`; `M=3`, `N=4`, and the same record
remain fixed.

- `L=0` deletes on the first miss, so the two-scan gap splits the target into
  two confirmed track segments.
- `L=2` preserves one ID across the gap and deletes three scans after departure.
- `L=5` also preserves the gap but leaves the stale track until scan 30.

Increasing `L` improves dropout tolerance while increasing stale-track memory.

## 7. Broken case and deterministic recovery

The intentionally broken policy bypasses both safeguards: every birth is
confirmed by `1-of-1`, and `L=30` makes deletion unreachable within this
30-scan record. Every isolated false alarm becomes a confirmed active track;
the final scan contains nine active tracks from one true object and eight false
reports.

Recovery does not delete hand-picked false IDs or generate a more favorable
scene. It reruns the same arrays with `3-of-4` and `L=2`, then compares every
decision-bearing result array with the baseline. Exact equality is required.

## Limiting cases and invariants

- `M=1` means one report is enough for immediate confirmation.
- `M=N` requires hits on every scan of a full confirmation window; one miss can
  force a tentative replacement.
- `L=0` deletes a confirmed track on its first miss.
- A dropout of `r` consecutive scans survives exactly when `r <= L`.
- `L` at least as long as the remaining record behaves as an immortal track in
  that record; it is not proof the target persists.
- A hit resets the consecutive-miss counter to zero.
- A birth report counts once; an assigned report cannot also initiate another
  track.
- A confirmed track never deconfirms solely because its rolling score falls.
- Scores remain integers from zero through `N`; lifecycle IDs are positive and
  never recycled.
- Truth labels may score an association after the fact but must not choose it.

## Common interpretation mistakes

**Mistake:** a tentative track is a detected physical object.
**Correction:** it is a time-local hypothesis awaiting repeated evidence.

**Mistake:** `3-of-4` means three consecutive hits.
**Correction:** one miss is permitted anywhere in the four-scan window.

**Mistake:** a confirmed track should be deleted when its rolling score drops
below three.
**Correction:** maintenance uses consecutive misses and `L`; confirmation is a
one-way promotion in this lesson.

**Mistake:** coasting repeats the last measurement.
**Correction:** it propagates the motion prediction without a measurement
correction.

**Mistake:** a larger coast allowance is always safer.
**Correction:** it preserves dropouts but also retains stale state and consumes
track capacity longer.

**Mistake:** scoring truth labels are available to the tracker.
**Correction:** the manager receives only positions and validity; truth is
joined to retained assignments in a separate audit pass.

## Claim boundary

This is a seeded synthetic, one-dimensional Cartesian, base-MATLAB experiment.
Static repository checks and an independent host-language oracle inspect its
state equations, transition boundaries, deterministic inputs, resource bounds,
and documentation. They do not prove MATLAB execution, rendered figures,
timing, memory, educational effectiveness, hardware/HIL, real-time behavior,
operational radar performance, or field performance.
