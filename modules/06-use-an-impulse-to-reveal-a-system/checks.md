# P06 Checks — Use an Impulse to Reveal a System

## Guiding question

Why does an impulse response describe an LTI system?

## Baseline observation checks

1. Which impulse response contains exactly one delayed copy, and at what lag?
2. Why do the moving-average weights sum to one even though each tap is smaller
   than the echo system's direct tap?
3. For all four systems, are the printed maximum direct/convolution errors below
   `comparison_tolerance_v`?

Expected: the pure delay has its unit tap at the configured delay; the moving
average preserves a constant input because its weights sum to one; all four
comparisons agree to numerical precision on the observed causal window.

## Predict, then verify

1. If echo delay increases but echo gain is fixed, predict which tap coordinate
   changes and which stays constant. Verify with Sweep 1.
2. If the resonator radius moves from `0.25` toward `0.92`, predict whether the
   response memory and ringing duration grow or shrink. Verify with Sweep 2.
3. If moving-average length becomes `1`, predict both `h[n]` and the output.

## Interpretation checks

Mark each statement true or false and correct every false statement.

1. The impulse response is the input spike itself.
2. LTI lets a general input be replaced by scaled, shifted impulses whose
   shifted responses add.
3. A long resonator response means each input sample influences more future
   output samples.
4. Agreement for these four models proves any physical radar channel is LTI.
5. Startup samples near `n = 0` are necessarily implementation errors.

Expected: false, true, true, false, false. The response is the system's output
to the spike; real channels can be nonlinear or time-varying; startup reflects
zero pre-record history in these causal experiments.

## Failure classification

- Solid and dashed curves differ only by a constant sample offset: check output
  alignment and crop support before changing the system equation.
- Error appears at the start after an unpadded FFT product: identify circular
  wraparound and recover with linear convolution or adequate zero-padding.
- Direct processing disagrees for every sample after changing one rule: the
  direct implementation and measured impulse response no longer describe the
  same system.
- A guard fails before allocation: restore a finite, scalar, in-range control;
  do not weaken the fixed resource ceiling.

## Recovery, isolation, and compatibility

There is no persistent file or learner-state mutation to roll back. Re-run from
the private seed after restoring committed controls. The experiment must
preserve the global random stream and unrelated figures, and must not
wholesale-clear the workspace or command window. Its finite bounded loops need
no timeout or asynchronous cancellation mechanism. It uses base MATLAB with no
toolbox, helper, external data, network, device, or service dependency.

## Teach-back completion

In two or three sentences, answer the guiding question using decomposition into
shifted impulses, linearity, and time invariance. Include one concrete tap from
the echo response and explain why the deliberately circular FFT result does not
invalidate the model.

A complete teach-back must say that `h[n]` determines the weights and delays in
the linear convolution sum, connect an echo tap to one scaled delayed input
copy, and classify wraparound as an incorrect boundary condition. Then confirm
that direct processing and convolution agreed below the stated voltage
tolerance for all four systems.
