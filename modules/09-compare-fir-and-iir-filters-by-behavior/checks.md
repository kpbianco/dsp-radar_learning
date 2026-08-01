# P09 Checks — Compare FIR and IIR Filters by Behavior

## Guiding question

How can two filters with similar magnitude response behave differently in time and phase?

## Baseline observation checks

1. Are both measured minus-three-decibel cutoffs near `100 Hz`? Does that make
   the complete magnitude curves identical?
2. What constant group delay does the 21-tap FIR have? Is there one constant
   group delay you can quote for the IIR without naming a frequency?
3. Which impulse response has exact finite support, and what does the IIR
   tail-threshold metric actually mean?
4. Which filter uses fewer multiplications and additions per output sample?
5. On the step and pulse plots, separate pure causal delay from overshoot,
   ringing, and shape change.

Expected: the cutoff markers coincide within the grid resolution, but the full
magnitude curves do not. The FIR delay is `10 samples`; the IIR delay is
frequency-dependent. The FIR ends after tap 21, while the IIR threshold reports
only the last visible sample in a finite record. The second-order IIR uses less
arithmetic. Both delay and transient shape must be inspected.

## Predict, then verify

1. Before Sweep 1, predict the group delays for `9`, `21`, and `41` symmetric
   odd-length FIR taps.
2. If Q rises while IIR order and cutoff remain fixed, predict what happens to
   pole radius, step overshoot, and ringing.
3. If sample rate doubles but the 21 coefficients do not change, predict what
   happens to group delay in samples and in seconds.
4. If a conjugate pole radius changes from `0.98` to `1.02`, predict whether a
   longer observation makes the impulse tail look safer or more dangerous.
5. If only the magnitude response mattered and phase was unconstrained, which
   baseline arithmetic count supports the IIR choice? What extra stability and
   precision questions must still be answered?

## Interpretation checks

Mark each statement true or false and correct every false statement.

1. Matching the minus-three-decibel cutoff guarantees matching step response.
2. A symmetric 21-tap causal FIR has 10 samples of constant group delay.
3. A stable IIR has a finite impulse response once its samples are small enough.
4. An IIR can achieve useful selectivity with fewer operations by using feedback.
5. A pole radius of 1.02 is stable because the 160 plotted values remain finite.
6. Static and deterministic simulation checks validate a physical radar filter.

Expected: false, true, false, true, false, false. Cutoff omits phase and
transients; thresholding does not turn infinite support into finite support; a
pole outside the unit circle is unstable; and repository/simulation evidence is
not hardware or operational validation.

## Failure classification

- FIR delay is not `(M-1)/2`: check coefficient symmetry and the phase-slope
  calculation away from response nulls.
- Baseline cutoff markers separate: check the `1.20` FIR calibration scale,
  coefficient normalization, frequency grid, and IIR bilinear coefficients.
- IIR output grows in the baseline: check recurrence signs and verify both poles
  are strictly inside the unit circle.
- Every noise trace changes between cases: verify the same private seeded samples
  are reused; do not reseed inside a sweep.
- Increasing FIR tap count changes the IIR: the sweep is no longer isolated.
- Broken case decays: check that its radius is `1.02`, not the recovered `0.98`.
- Tail or settling metric prints `found=0`: the edited threshold/tolerance has
  no qualifying sample in the finite record; read the sample metric as `NaN`,
  not as zero or the record endpoint.

## Recovery, isolation, compatibility, and resource bounds

The broken filter recovers by moving its pole radius inside the unit circle, not
by shortening the plot or clipping the output. Malformed edits fail assertions;
restore committed controls and rerun from private seed 909. Valid reruns replace
only P09-tagged figures. No file, external transaction, or learner state is
written, so there is no persistent runtime rollback.

The record is capped at 512 samples, response at 256 samples, FIR at 81 taps,
frequency grid at 2049 points, each sweep at eight cases, and figures at six
groups. All loops have fixed upper bounds. There is no pause, prompt, timer,
callback, background work, file/network/device I/O, or asynchronous resource to
cancel. Ctrl+C is the foreground cancellation mechanism if local graphics
block. The experiment uses base MATLAB, a private `RandStream`, explicit sums
and recurrences, and tagged figures; it preserves the global random stream and
unrelated figures.

## Choice check

- Prefer the FIR when constant group delay or pulse-shape fidelity across the
  passband justifies its tap count and latency.
- Prefer the IIR when low arithmetic cost matters and its nonlinear phase,
  transient response, numeric sensitivity, and stability margin are acceptable.

These are examples, not universal rules. State the actual signal requirement.

## Teach-back completion

In two or three sentences, answer the guiding question using the matched cutoff,
the 10-sample FIR delay, the IIR recurrence, and the broken/recovered pole radii.
Then give one FIR-favoring and one IIR-favoring requirement.

A complete teach-back says that comparable magnitude at a cutoff does not fix
phase or memory: the symmetric FIR has finite support and constant 10-sample
delay, while the recursive IIR has frequency-dependent delay and a decaying
tail with much less arithmetic. It explains that feedback becomes unstable
outside the unit circle (`1.02`) and recovers inside it (`0.98`), then chooses a
filter based on timing/shape, selectivity, computation, and stability needs.
