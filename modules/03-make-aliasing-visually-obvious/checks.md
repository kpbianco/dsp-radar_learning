# Checks

## Guiding question

Why does a high-frequency tone appear as a lower-frequency tone after sampling?

## Observe

1. Which two continuous curves cross every baseline sample stem?
2. What are the printed signed fold, apparent frequency, and recurrence estimate?
3. At which input frequencies does the sweep return to apparent DC?
4. What changes sign in the lower folding plot at each reflected half-cycle?

## Predict, then verify

1. For an 850 Hz tone sampled at 1000 samples/s, predict the signed fold,
   apparent frequency, and whether phase must reverse.
2. For a 1250 Hz tone at the same sample rate, predict the apparent frequency.
3. Hold a 700 Hz input fixed and change the sample rate from 1000 to 800
   samples/s. Predict the new apparent frequency before inspecting Sweep 2.
4. Predict the apparent frequency of a tone exactly at `2*fs` and describe the
   stored real sequence.

## Interpret

- Explain why aliasing is deterministic folding rather than random corruption.
- Explain why a 300 Hz estimate does not prove that the analog source was
  300 Hz.
- Explain why a negative signed fold requires phase reversal when represented
  as a positive-frequency real cosine.
- State what is special about DC, exactly Nyquist, and integer multiples of the
  sample rate.
- Connect an ADC anti-alias filter to pulse-Doppler PRF and ambiguous velocity.
- Explain what complex I/Q preserves that a real cosine sequence does not.

## Recovery check

Restore the committed controls and confirm every assertion passes. Confirm that
the correct reflected model has only roundoff-level sample disagreement while
the broken retained-phase model misses by more than 0.5 amplitude unit. If a
resource guard fails, return below 20001 dense points, 5000 samples per record,
128 frequency cases, and eight representative or sample-rate cases.

Then state the non-destructive system recovery: restrict analog bandwidth with
an anti-alias filter and sample sufficiently fast before interpreting the
sequence. No digital estimator can recover which analog alias-family member was
discarded at the sampling boundary.

## Teach-back completion

In two or three sentences, answer:

**Why does a high-frequency tone appear as a lower-frequency tone after sampling?**

A satisfactory answer:

- gives a correct folding rule using integer multiples of `fs`;
- predicts that 700 Hz at 1000 samples/s appears at 300 Hz;
- says the sampled sequence is identical to a correctly phased lower-frequency
  cosine, not randomly corrupted; and
- identifies input band limiting or prior band knowledge as necessary to choose
  the original analog frequency from its alias family.
