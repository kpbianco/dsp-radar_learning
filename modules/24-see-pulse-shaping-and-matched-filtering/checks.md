# P24 Checks: Pulse Shaping, Matched Filtering, and Timing

## Guiding question

Why are symbols filtered before transmission and again at reception?

Use the plots and retained `results` from `experiment.m`. Short physical
answers are enough; MATLAB syntax is not the learning target.

## Observation checks

1. Which pulse has abrupt time edges, and which spectrum has the slowly
   decaying sidelobes?
2. At what sample delay does the span-8 transmit/receive RRC cascade reach its
   symbol decisions when `sps=8`?
3. Which is smaller: `rrc_pre_filter_evm_pct` or
   `rrc_matched_evm_pct`? What receiver operation changed between them?
4. Does the noiseless span-8 combined response have exactly zero residual ISI,
   or a small finite-truncation error?

Expected observations: rectangular time edges produce sinc-like sidelobes;
the RRC cascade delay is 64 samples; matched and correctly timed samples have
lower EVM; finite span leaves a small residual rather than an ideal infinite
response.

## Prediction checks

1. If beta rises with span fixed, predict the direction of the measured
   occupied bandwidth.
2. If span rises from 2 to 8 symbols with beta fixed, predict the dominant
   change in truncation-driven ISI and the cost in taps/delay.
3. If the matched output is sampled half a symbol late in a noiseless channel,
   predict whether increasing `Es/N0` can restore the constellation.
4. If the pulse is known but the noise is strongly colored, is the plain
   white-noise matched-filter optimality claim sufficient without a whitening
   model?

## Correct these statements

- "Any overlap between shaped pulses is ISI."
- "The RRC transmitter alone has the complete raised-cosine zero-ISI
  response."
- "A matched filter removes noise."
- "Rectangular pulses always create symbol errors."
- "The smallest roll-off is always the best implementation."

Corrections should mention decision instants, the transmit/receive cascade,
maximum sampled SNR rather than noise removal, ideal rectangular timing, and
the bandwidth/time-tail trade.

## Broken-case diagnosis

The broken plot uses the correct pulse and matched filter with
`broken_timing_offset_samples = 4`.

1. Name the failed assumption.
2. Explain why the eye and constellation degrade without added noise.
3. Describe the one-variable recovery.

A complete diagnosis says the receiver sampled at `+0.5T`, so neighboring
symbol contributions were not at the raised-cosine zero crossings. Subtracting
the four-sample timing offset restores the original decision indices and the
noiseless baseline.

## Operational and compatibility check

What should you do if the bounded script must be canceled? Use **Ctrl+C**, then
perform a full rerun. The private seed rebuilds P24 deterministically without
changing the global random stream, but MATLAB cannot restore workspace
variables overwritten before cancellation. Only P24-tagged figures are closed.
The script uses base MATLAB, does not update `.learning/`, starts no worker or
timer, performs no external transaction, and writes no external file.

Repository rollback removes the P24-created artifacts, P24-named test and
evidence files, and P24 catalog additions, then returns only P24's manifest
status to `scaffolded`. It must not roll back P23 or rewrite later canonical
module identities.

## Teach-back rubric

In two or three sentences, answer the guiding question. A complete teach-back
must:

- connect transmit pulse shape to time behavior and occupied bandwidth;
- identify the receive filter as the conjugate time reverse that maximizes the
  known pulse's sampled SNR in white noise;
- explain that the RRC pair creates the near-Nyquist combined response; and
- state that total group-delay compensation and correct symbol timing are
  necessary for the open eye and clean constellation.

Name one limiting assumption: finite filter span, known pulse, white noise,
perfect carrier reference, no multipath, or known timing recovery offset.
