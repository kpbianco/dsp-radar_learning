# Checks: Two-Pulse and Three-Pulse MTI

## Observation checks

1. Which matrix dimension is slow time in P38, and which explicit expressions
   prove that the cancellers operate on it?
2. At the clutter peaks, what changes between the unfiltered range profile and
   each correct canceller output?
3. Why is a moving target still visible in a range cell whose stationary
   clutter component cancels?
4. What are the measured and theoretical white-noise power gains for the two
   cancellers?

## Prediction checks

1. Before adding a target speed close to zero, predict which canceller gives it
   the smaller amplitude gain. Confirm with the velocity sweep.
2. For a fixed physical target velocity, predict what happens to canceller gain
   when PRF increases. Explain using phase change per PRI.
3. Predict the output for a Doppler equal to one PRF. Is that velocity inside
   the baseline unambiguous interval?

## Interpretation checks

1. Explain why `H2 = 1-exp(-j omega)` is zero for a stationary phasor.
2. Explain why squaring that factor broadens the near-zero rejection but does
   not make the three-pulse canceller universally better.
3. Distinguish target amplitude gain, target power gain, noise power gain, and
   target SNR change.
4. Explain why positive and negative Dopplers share the same response magnitude
   while their coherent phase rotations still have different signs.
5. Why do delay-line-canceller nulls repeat at integer multiples of PRF?

## Failure and recovery checks

1. State why differencing adjacent range rows is not MTI even when the result
   looks high-pass filtered.
2. Verify that the broken clutter residual is nonzero and
   `broken_model_valid` is false.
3. Verify that recovery uses the same private seed, restores slow-time
   differencing, reproduces both correct outputs exactly, and sets
   `recovered_model_valid` true.
4. Explain why valid `N-1` and `N-2` outputs avoid false zero-padding boundary
   transients.

## Compatibility, isolation, and resource checks

1. Confirm the main operation is explicit base MATLAB subtraction rather than
   an unexplained toolbox MTI or filter helper.
2. Confirm all range-bin controls are validated before they index an array.
3. Confirm sweeps, pulses, range samples, response samples, figure groups, and
   stored numeric values have finite declared ceilings.
4. Confirm the script closes only `P38`-tagged figures and private streams leave
   the global random stream alone.
5. Describe Ctrl+C cancellation, clean-rerun recovery, and rollback of a
   control edit. Name any worker, timer, network, hardware, file write, or
   external transaction that would require separate cleanup; there is none.

## Completion checklist

- [ ] I can identify the slow-time dimension without looking at MATLAB syntax.
- [ ] I can explain the two-pulse and three-pulse DC nulls physically.
- [ ] I can predict which velocities are preserved or attenuated by each
      canceller.
- [ ] I can account for both target gain and noise gain.
- [ ] I can recognize the wrong-axis failure and describe exact recovery.
- [ ] I can state why ideal simulation is not proof of real clutter rejection.

## Teach-back rubric

In two or three sentences, explain how subtracting adjacent coherent pulses
removes a stationary reflector, why a second difference changes slow-target
and noise response, and how PRF creates periodic blind-speed nulls. A complete
answer names the slow-time axis and does not claim that three-pulse processing
is always superior.
