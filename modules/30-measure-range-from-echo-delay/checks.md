# P30 Checks: Measure Range from Echo Delay

## Guiding question

How does round-trip delay become target range?

## Observation checks

1. What lag does the integer baseline select relative to the 120.35-sample
   truth? Expected: a whole-sample lag near the truth, not 120.35 itself.
2. What range step corresponds to one sample at 20 MHz? Expected:
   `c/(2*20 MHz)`, about 7.49 m.
3. Which plotted quantity identifies delay: received amplitude alone or the
   peak of the aligned pulse correlation? Expected: the correlation peak.
4. How many visible local peaks occur at the reviewed 0.5, 1.0, and 1.5
   microsecond separations? Expected: one, one, and two under the stated rule.

## Prediction checks

1. Predict the round-trip delay for a target at range `R`. Expected:
   `tau = 2*R/c`.
2. Predict the reported range if the correct delay is converted with `c*tau`
   instead of `c*tau/2`. Expected: twice the true one-way range.
3. Predict the integer range-bin spacing when sample rate doubles. Expected:
   it halves because `Delta R = c/(2*fs)`.
4. For an isolated clean peak and nearest integer lag, what is the usual
   quantization bound? Expected: half a sample, or `c/(4*fs)` metres.
5. Does parabolic peak interpolation guarantee that two merged targets become
   resolvable? Expected: no; it estimates the location of the observed peak
   and creates no new waveform bandwidth.

## Interpretation checks

- Explain why measured monostatic delay contains two propagation legs.
- Starting from 120 samples at 20 MHz, state the delay in seconds before
  converting it to range.
- Explain why zero padding outside the finite pulse is physically preferable
  to circularly shifting the echo record.
- Distinguish sample-grid spacing, sub-sample peak estimation, and the width of
  the pulse autocorrelation.
- Explain why echo amplitude changes correlation height but not the
  lag-to-range conversion.
- Name two assumptions that would fail for a real radar capture.

## Failure and recovery checks

1. What exactly is wrong in the broken case? Expected: it interprets a
   round-trip time as a one-way time; the correlation lag itself is unchanged.
2. Why is a decimal refined lag not automatically ground truth? Expected: it
   depends on noise, waveform peak shape, interpolation model, and timing
   calibration.
3. What proves deterministic recovery? Expected: a new private stream produces
   the exact same noise, received vector, and explicit correlation while the
   restored `c*tau/2` formula returns the measured range.
4. If a run is interrupted with `Ctrl+C`, why should it restart at the top?
   Expected: validation, seeded generation, results, assertions, and plots are
   one bounded run; partial workspace variables are not complete evidence.

## Malformed-input, compatibility, isolation, and resource checks

- Confirm nonfinite, logical, complex, nonpositive, out-of-order, or expanded
  controls fail before allocation, RNG, figure cleanup, or plotting.
- Confirm the script uses base MATLAB R2018b-or-newer plotting behavior and
  no toolbox, worker, timer, file, network, device, or external transaction.
- Confirm it uses a private seed without changing the global random stream,
  closes only figures tagged `P30`, and never writes `.learning/`.
- Confirm the ceilings: 640 record samples, 40 pulse samples, 640 correlation
  samples, four cases per sweep, six figure groups, and at most 50,000
  conservatively counted numeric values.
- Confirm rollback is local: remove P30-owned module/test/evidence changes and
  restore only P30 to `scaffolded`, preserving active control state, P29,
  later batches, and learner state.

## Completion checklist

- [ ] I can convert lag samples to seconds and then to `c*tau/2` range.
- [ ] I can explain the factor of two from the physical path.
- [ ] I can compute the integer range-bin spacing and half-bin bound.
- [ ] I can explain what peak interpolation can and cannot add.
- [ ] I can distinguish one merged response from one accurately located target.
- [ ] I can diagnose and recover the broken one-way conversion.

## Short teach-back rubric

In two or three sentences, answer: **How does round-trip delay become target
range?** A complete teach-back converts lag with `tau = lag/fs`, uses
`R = c*tau/2`, explains the return-trip factor, and distinguishes sample-grid
precision from finite-pulse target separation. It does not claim hardware,
field, probability-of-detection, or universal resolution validation.
