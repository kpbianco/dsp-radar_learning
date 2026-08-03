# P35 checks: Create Unambiguous-Range Aliasing

Guiding question: **Why can a distant target appear at a shorter false range?**

Use the figures and printed metrics. These are interpretation checks, not a
MATLAB syntax quiz.

## Observation checks

1. Which transmitted pulse caused the marked baseline echo, and how many newer
   pulses leave before it arrives?
2. What true range, unambiguous range, ambiguity order, and apparent range are
   printed for the 20 kHz baseline?
3. What shape appears when true range crosses several fixed-PRF intervals?

Passing observation: you identify the first pulse, two elapsed complete PRIs,
the 18 km / 7.494811 km / `q=2` / 3.010377 km mapping, and the folded sawtooth.

## Prediction checks

1. At fixed true range, if PRF is reduced enough that `R_u` exceeds the target
   range, what are `q` and apparent range?
2. At fixed PRF, predict the apparent range of a target at
   `R = 2*R_u + 1 km`.
3. Predict the reports immediately below and immediately above `R_u`.
4. If the display sample rate doubles while PRF and waveform stay fixed, does
   physical unambiguous range change?

Passing prediction: the unambiguous case has `q=0` and `R_app=R`; the second
target reports 1 km; a boundary wraps from near `R_u` to near zero; display
sampling changes marker granularity but not `R_u`.

## Interpretation checks

1. Explain why the same arrival is at 120.083 microseconds on the absolute
   timeline and 20.083 microseconds in the current listening interval.
2. Distinguish unambiguous range from range resolution and range accuracy.
3. Why can 10 and 20 kHz both report the 18 km target near 3.010 km?
4. List the family of possible true ranges represented by one apparent range.
5. Why does a result near zero not guarantee detection in a real pulsed radar?

Passing interpretation: you connect the coordinate reset to missing pulse
identity, preserve the bandwidth/accuracy distinctions, include ambiguity
order, write candidates as `R_app + k*R_u`, and mention transmit blanking or
receiver recovery at the zero-delay boundary.

## Failure and recovery checks

1. What unavailable information makes the broken 18 km report possible?
2. Why is that report invalid even though it equals the simulated true range?
3. What exact state and operation does recovery restore?
4. Why does adding an integer multiple of `R_u` leave apparent range intact?

Passing recovery: you reject the hidden transmit-pulse label, restore the
quotient/remainder measurement, and identify exact reconstruction of the
private-seed trace. A clean rerun reproduces the result. If needed, cancel
with Ctrl+C; there is no worker, timer, external transaction, or persistent
resource to clean up, and only figures tagged `P35` are closed.

## Completion checklist

- [ ] I can compute PRI and `R_u` from PRF.
- [ ] I can convert true range to round-trip delay and ambiguity order.
- [ ] I can calculate `R_app = mod(R, R_u)` beyond one interval.
- [ ] I can explain why a PRF sweep produces branches and jumps.
- [ ] I can distinguish pulse-identity aliasing from resolution or accuracy.
- [ ] I can diagnose the hidden-label failure and recover the physical fold.
- [ ] I know this base MATLAB simulation is not hardware, HIL, field,
      real-time, detector, deployment, or operational-radar validation.

## Short teach-back rubric

Give two or three sentences that include all three ideas:

1. Periodic transmission limits the unique fast-time coordinate to one PRI,
   giving `R_u=c/(2*PRF)`.
2. An echo beyond that interval loses its pulse identity and reports the
   remainder `R_app=R-qR_u`.
3. Changing PRF changes the candidate family, while range resolution and the
   physical target location do not change merely because the label folds.

Completion means you can calculate the folded apparent range for a target beyond the unambiguous interval. Personal completion is recorded only after this teach-back through the learner CLI under ignored `.learning/` state.
