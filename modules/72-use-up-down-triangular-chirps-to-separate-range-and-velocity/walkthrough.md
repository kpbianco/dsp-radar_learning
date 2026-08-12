# P72 walkthrough: Reverse One Cause

## Guiding question

How can opposite chirp slopes disentangle delay and Doppler?

Run `experiment.m` once without editing it. The script is finite and
foreground-only. It creates seven figures tagged `P72` and retains
`p72_results`.

## Baseline: compare the two slopes

Open **P72 triangular chirp legs and echoes**. On the up leg, delay moves the
echo backward along a rising ramp while approaching Doppler shifts it upward.
On the down leg, delay reverses its signed effect because the ramp falls, but
approaching Doppler still shifts the echo upward.

Open **P72 signed up and down beats**. Read the peak signs, not just their
magnitudes:

- `f_up` is near `+139.733 kHz`;
- `f_down` is near `-160.267 kHz`;
- their half-difference is `150.000 kHz` of delay beat; and
- negative half their sum is `+10.267 kHz` of Doppler.

Expected observation: changing slope reversed the delay contribution but did
not reverse Doppler.

## Processing transition: solve the two equations

Open **P72 range and velocity solution**. The left panel applies

```text
R = c(f_up - f_down)/(4S),
```

and the right applies

```text
v = -lambda(f_up + f_down)/4.
```

Both estimates should nearly overlay the `45 m` and `+20 m/s` truths. This is
the new information compared with P71: a second slope made the two unknowns
identifiable for one associated target.

## Sweep 1: change only range

Open **P72 range sweep**. Velocity, carrier, slope magnitude, duration, sample
rate, amplitude, phase, and normalized noise streams remain fixed while range
takes `15, 30, 45, 60, 75 m`.

Expected observations:

- estimated range follows the diagonal;
- estimated velocity stays near `+20 m/s`; and
- physically, the signed up/down beats move farther apart as delay grows.

Try changing only `range_sweep_m` to `[10 25 45 65 80]`, predict the same two
trends, then restore the reviewed vector.

## Sweep 2: change only velocity

Open **P72 velocity sweep**. Range stays `45 m` while velocity takes
`-30, -15, 0, +15, +30 m/s`. Every case reuses the same two distinct private
normalized noise streams.

Expected observations:

- estimated range stays near `45 m` because Doppler cancels in the difference;
- estimated velocity follows the signed diagonal; and
- both signed beats translate together as Doppler changes.

Try changing only `velocity_sweep_mps` to `[-40 -20 0 20 40]`. Predict that
range remains fixed and both beats shift by `-2v/lambda`, then restore the
reviewed vector.

## Sweep 3: change only receiver noise

Open **P72 noise sweep**. Geometry and waveform controls stay fixed. The first
point has zero noise and should have numerical errors near zero. Later points
scale two distinct deterministic noise streams.

Expected observation: range and velocity errors become visible as the two
beat estimates are perturbed. Do not require every single absolute-error point
to rise; one fixed random realization need not be monotonic.

## Broken case: pair different targets

Open **P72 multi-target pairing failure and recovery**. The upper panel shows
two detected up beats and two detected down beats from targets at `30 m,
+15 m/s` and `65 m, -10 m/s`.

The broken path sorts each signed list in the same order. Because down-beat
ordering reverses with range here, the resulting cross-target pairs produce
ghost reports near the middle ranges with extreme velocities. The equations
still solve exactly; they cannot know that the two frequencies came from
different echoes.

Common mistake: saying the implausible velocity proves wrong pairing in every
scene. A feasibility gate helps this reviewed scene, but wrong pairs can be
plausible. The general solution needs another association cue.

## Recovery on unchanged detections

The recovery changes only the down-beat permutation. Confirm:

- `p72_results.detected_up_hz` is unchanged;
- `p72_results.detected_down_hz` is unchanged;
- `wrong_paired_down_hz` uses the same ascending order;
- `correct_paired_down_hz` reverses that two-target order; and
- recovered reports return near `30 m, +15 m/s` and `65 m, -10 m/s`.

No waveform, echo, noise sample, FFT, or detected beat is regenerated during
recovery. This isolates association from measurement quality.

## Limiting observations

- At zero velocity, the two beats are opposite signs with equal magnitudes.
- At zero delay, both beats contain only `-f_d`, so their difference is zero.
- At zero slope, the range equations are singular.
- A beat at or beyond Nyquist aliases before the solve.
- A target delay leaving fewer than two common overlap samples is rejected.
- Sequential legs assume negligible state change between them.

## Cancellation, rerun recovery, and rollback

Press `Ctrl+C` between figure sections if needed. There is no worker, timer,
network request, file write, or external process continuing in the background.
An interruption can leave partial `P72` figures and workspace arrays, but no
external persistent state. Rerun from the top to close only figures tagged
`P72`, clear and rebuild `p72_results`, and regenerate the same private noise
streams. Unrelated figures and variables are not broadly cleared.

Repository rollback is file-local: remove the P72 learning artifacts and
focused evidence/catalog changes, then restore only P72's manifest status to
`scaffolded`. Preserve P71, later module identities, ignored `.learning/`
progress, and operator-managed active-batch contracts.

## Concept connection and completion handoff

Complete this sentence aloud:

> Reversing chirp slope reverses the ___ contribution but preserves the ___
> sign, so beat ___ isolates range and beat ___ isolates velocity; with
> multiple targets the remaining problem is ___.

The intended answer is delay, Doppler, difference, sum, and association.
