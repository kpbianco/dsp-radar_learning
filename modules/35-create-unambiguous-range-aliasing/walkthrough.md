# P35 walkthrough: Create Unambiguous-Range Aliasing

Guiding question: **Why can a distant target appear at a shorter false range?**

Run `experiment.m` once from this module folder. It uses base MATLAB, bounded
arrays and loops, and a private seed for a faint repeatable noise floor. It
does not change the global random stream.

## Baseline observation: follow one old echo

Start with `P35 pulse identity timeline` and
`P35 baseline folded listening interval`, then read the printed metrics.
MATLAB window numbers depend on other open figures, so use these stable names.

1. In the timeline, locate transmissions at 0, 50, and 100 microseconds.
2. Follow the marked echo from the first pulse to about 120.083 microseconds.
   Two newer pulses have already left, so its ambiguity order is `q=2`.
3. In the folded listening interval, reset the clock at the 100-microsecond
   transmission. The same echo is now about 20.083 microseconds into the
   current interval.
4. Convert that fast time with `c*tau/2`. The receiver reports about
   3.010377 km even though the true target is at 18 km.
5. Compare true range, `R_u = 7.494811 km`, and apparent range in the right
   subplot. The sample-grid marker may differ from the continuous metric by
   at most half a range sample.

Expected observation: propagation remains causal on the absolute timeline,
but forgetting the originating pulse removes two complete PRIs from the
reported delay.

## Sweep one variable: pulse repetition frequency

`P35 PRF sweep` holds true range at 18 km. Only PRF changes from 8 to 30 kHz;
the marked cases are `[10 15 20 25]` kHz.

- In the left subplot, confirm that higher PRF reduces unambiguous range
  smoothly because `R_u=c/(2*PRF)`.
- In the right subplot, do not expect a smooth bias. Follow each apparent
  range branch until `q` changes and the remainder jumps.
- Compare 10 and 20 kHz. Both put the target near 3.010 km, but their
  ambiguity orders are one and two.
- At 25 kHz the target falls near zero apparent range. Treat that as the ideal
  remainder, not proof that an echo is visible during real transmit blanking.

Expected observation: PRF controls the length of the ambiguity interval;
changing the interval moves a folded target non-monotonically.

## Sweep one variable: true target range

`P35 true-range sweep` holds PRF at 20 kHz and moves true range through three
unambiguous intervals.

- From zero to `R_u`, the apparent-range curve follows true range.
- Just below each multiple of `R_u`, it approaches the end of the interval.
- Just above the boundary, it returns near zero and ambiguity order increases.
- Compare the marked 3, 8, and 18 km targets. The 3 km target is unambiguous;
  the latter two lose one and two pulse labels respectively.

Expected observation: apparent versus true range is a sawtooth. An integer
multiple of `R_u` changes the candidate true range without changing the ideal
apparent gate.

## Intentionally broken case: reveal the hidden pulse label

`P35 pulse-identity failure and recovery` compares three reports.

1. `Physical fold` uses only time since the most recent transmission and
   reports about 3.010 km.
2. `Broken pulse label` traces the echo back to its original simulated pulse
   and reports 18 km.
3. Reject the broken report for this receiver. The simulation knows the event
   label, but a periodic fixed-PRF measurement did not encode or observe it.
4. `Recovered fold` discards that unavailable label and returns exactly to the
   baseline quotient/remainder result.

Failure interpretation: a correct number produced with unavailable
information is still an invalid measurement model. This is not a range-
resolution, numerical-rounding, or speed-of-light failure.

## Recover and connect the concept

Recovery recomputes PRI, unambiguous range, ambiguity order, and apparent
range. It recreates the private seed and entire received train exactly, then
verifies that adding three `R_u` intervals preserves the apparent gate.

Say the connection in one sentence: **a fixed PRF repeats the range-time
coordinate every `c/(2*PRF)`, so an echo delayed by whole PRIs loses its
transmit-pulse identity and appears at the remainder range.**

## Safe cancellation, clean rerun, and rollback

- Press Ctrl+C to cancel. Every pulse, range, and PRF loop has a validated
  finite bound; there is no worker, timer, network call, hardware session,
  file write, or external transaction to leave running.
- Rerun the whole script for recovery. It closes only figures tagged `P35`,
  reconstructs the private seed, and leaves the global random stream and
  unrelated figures unchanged.
- The script never reads or writes `.learning/`; personal progress stays in
  ignored learner-CLI state.
- Batch rollback removes the four P35 implementation artifacts, P35 test, and
  P35 evidence; restores this README and the P35 manifest status to
  `scaffolded`; and restores the public catalogs. It preserves P01-P34 and all
  later module identities.

Completion means you can calculate the folded apparent range for a target beyond the unambiguous interval.
