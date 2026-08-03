# P30 Walkthrough: Measure Range from Echo Delay

## Guiding question

How does round-trip delay become target range?

Run `experiment.m` from this module folder. Read the controls before the plots:
a 20 MHz receiver, one-microsecond pulse, 6.0175 microsecond round-trip delay,
and a small seeded noise term. The script validates every input and resource
ceiling before allocation, random generation, figure cleanup, or plotting. Its
values remain in `results` for inspection.

## 1. Baseline observation: follow the clock

Inspect the first figure one panel at a time. The top panel is the known pulse;
the bottom panel puts its delayed attenuated copy on receive fast time. The
delay is fractional, so the echo edges need not coincide exactly with sample
times.

Now inspect the correlation figure. The peak lies near 902 m because the script
first converts lag to seconds and then uses `R = c*tau/2`. Compare the red
integer-lag line with the green refined line and the black true range.

Concrete observation question: is the 120.35-sample truth reported directly by
the integer peak, or does that peak first snap to a whole-sample lag?

The printed range-bin step is about 7.49 m. The baseline integer error is
bounded by half that step, and the local parabolic interpolation reduces it for
this reviewed peak. That reduction is model-specific, not a promise for every
noise level or waveform.

## 2. Sweep one variable: sample rate only

The third figure holds the physical delay, pulse duration, amplitude, and noise
condition fixed; the sweep itself is noise-free. Only sample rate changes
through 10, 20, and 40 MHz.

- The lower panel should halve the lag-to-range spacing each time sample rate
  doubles.
- The upper panel need not improve monotonically at every chosen fractional
  phase: the continuous delay lands at different places within each grid.
- Every clean integer estimate must stay within half of its own range-bin
  spacing.

Prediction before reading the lower panel: what is the 40 MHz spacing if the
20 MHz spacing is about 7.49 m?

## 3. Sweep one variable: fractional delay only

The fourth figure keeps the 20 MHz rate and the integer part of the delay at
120 samples. Only the fractional part changes through 0, 0.25, 0.5, and 0.75
sample.

The integer estimate forms a staircase. The three-point refinement uses local
correlation curvature and follows the fractional motion more closely, though
it retains small waveform-dependent bias away from the symmetric half-sample
case. This sweep would be meaningless if echo insertion rounded the delay.

Do not interpret the refined decimal as extra bandwidth or guaranteed
accuracy. It is an estimate inferred from several samples of a known peak.

## 4. Add a second target and vary only separation

The fifth figure adds a second echo at 0.65 times the first amplitude. The
separation changes through 0.5, 1.0, and 1.5 microseconds, corresponding to
about 74.9, 149.9, and 224.8 m of monostatic range separation. The pulse,
amplitudes, sample rate, first delay, and noise-free condition stay fixed.

Under the explicit local-peak rule, the first two cases show one visible peak;
their overlapping pulse autocorrelations merge or form a shoulder. The widest
case shows two. A merged response is a target-separation problem, not evidence
that the first target's range clock suddenly became inaccurate.

## 5. Intentionally broken case: use the delay as one way

The final figure compares four range reports. The broken bar computes
`R_broken = c*tau`, so it is exactly twice the measured `c*tau/2` value.
Correlation, sample rate, and measured lag did not change. Only the physical
interpretation dropped the return trip.

Failure interpretation: the clock measured transmitter-to-target-to-receiver
time. Multiplying that full time by propagation speed gives the full path
length, not the target's one-way range.

## 6. Recover and connect the concept

Recovery restores `R = c*tau/2`, rebuilds a private stream from seed 3001, and
recomputes the received vector and explicit correlation. All recovered numeric
vectors must exactly match the baseline. The recovered range equals the
refined measured range; it need not equal truth exactly because the estimator
still has finite-sample and peak-shape error.

Give the completion connection in plain language: starting from a correlation
lag in samples, how do you reach monostatic range, where does the factor of two
enter, and what do sample rate and pulse shape limit differently?

## Safe rerun, cancellation, isolation, and rollback

- The script uses base MATLAB only, fixed finite arrays, bounded `for` loops,
  no worker, no timer, and no external transaction. It should finish promptly.
- If execution must be cancelled, use `Ctrl+C`. Rerun from the top; partial
  workspace values are not evidence of a complete run.
- The private seed does not replace or advance MATLAB's global random stream.
  Cleanup closes only figures tagged `P30`; unrelated figures stay open.
- No file, network, device, or `.learning/` write occurs. Learner progress
  remains isolated under `.learning/` through `bin/learn` only.
- Malformed controls fail before allocation, RNG use, or figure cleanup, so the
  last good figures remain available while the control is corrected.
- Repository rollback removes only P30-owned artifacts/tests/evidence and
  restores only P30's manifest status to `scaffolded`. It preserves the
  operator-managed active-batch file, P29, later module state, and learner data.
