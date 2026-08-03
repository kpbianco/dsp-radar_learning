# P25 Checks: Create and Equalize a Multipath Channel

## Guiding question

How do delayed copies distort symbols even when noise is small?

Use the retained plots and printed metrics from one full baseline run. These
checks test interpretation, not MATLAB syntax.

## Observation checks

1. **Identify the channel.** What are the three baseline path delays, in symbol
   periods? Point to the corresponding impulse-response stems.
2. **Separate noise from ISI.** What feature of the red eye or unequalized
   constellation shows structured, data-dependent interference rather than
   only circular random noise?
3. **Read the spectrum.** Where is the broken channel weakest in normalized
   frequency, and how deep is the printed minimum in dB?
4. **Measure improvement.** Record baseline unequalized, ZF, and MMSE EVM and
   SER. Both equalizers must improve EVM over the unequalized baseline.
5. **Measure cost.** Record ZF and MMSE noise gain in dB. A lower EVM does not
   prove that an equalizer has zero noise enhancement.

## Prediction checks

1. If the one-symbol echo magnitude grows while every other variable stays
   fixed, what should happen to unequalized EVM? Verify with sweep 1, and use
   the minimum-response curve to explain any nonlinearity.
2. Before viewing sweep 2, predict which failure dominates at very small
   `lambda` and which dominates at very large `lambda`: noise enhancement or
   residual channel distortion.
3. If the broken echo were exactly `-1` instead of `-0.999`, could any linear
   equalizer reconstruct the erased zero-frequency component from that noisy
   observation? Explain why more taps do not create missing information.
4. If all delayed gains became zero, predict the eye, constellation, and
   usefulness of equalization.

## Interpretation checks

Correct each false statement directly:

- “At 18 dB `E_s/N_0`, noise is small, so the channel cannot cause symbol
  errors.”
- “ZF guarantees zero EVM.”
- “MMSE is worse whenever it leaves visible residual ISI.”
- “A spectral null and eye closure are unrelated effects.”
- “The path with the smallest magnitude is always harmless.”

## Broken-case diagnosis and recovery

1. Confirm that `h=[1, -0.999]` creates a minimum below `-50 dB`.
2. Explain why the causal ZF tap-energy metric predicts noise amplification.
3. Select the regularization value nearest `10^(-18/10)`. Confirm that its EVM
   and noise gain are both lower than the broken causal-ZF values.
4. State the price of this recovery: the combined channel/equalizer response
   retains nonzero ISI.

## Operational and malformed-control checks

- Invalid, logical, complex, nonfinite, noninteger, noncanonical, oversized,
  or wrong-shaped controls must fail the assertions before private random
  generation, signal allocation, convolution, a linear solve, FFT work,
  P25-only figure cleanup, or figure creation.
- Interruption with **Ctrl+C** has no external transaction to roll back. A full
  rerun reconstructs deterministic variables and P25-tagged figures, but
  cannot restore workspace variables overwritten before cancellation.
- The private seed does not change MATLAB's global random stream; figures from
  other modules and `.learning/` state remain isolated.
- The resource ceilings are 480 symbols, 8 samples/symbol, 3 paths, a maximum
  2-symbol delay, 31 equalizer taps, 4 sweep cases, 5 figure groups, and
  750000 conservative stored numeric values. No worker or timer is started.
- Rollback restores only P25 to `scaffolded`; P24 and the permanent 84-module
  order remain intact. Base MATLAB remains the compatibility target.

## Completion teach-back rubric

In two or three sentences, answer the guiding question. A complete answer:

- connects delayed path taps to ISI, eye closure, constellation smearing, and
  frequency-selective fading;
- explains why a near-cancelling echo creates a deep null;
- contrasts ZF inversion with MMSE's residual-ISI/noise-gain trade; and
- identifies the channel delays and describes both the baseline improvement
  and the deep-null failure/recovery.
