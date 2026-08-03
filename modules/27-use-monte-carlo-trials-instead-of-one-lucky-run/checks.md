# P27 Checks: Use Monte Carlo Trials Instead of One Lucky Run

## Guiding question

Why is one noise realization not enough to judge an algorithm?

Use the plots and retained `results` values. These are interpretation checks,
not MATLAB syntax exercises.

## Observation checks

1. **Single trial:** What performance fact is missing from one correct noisy
   BPSK decision?
   - The probability that a new independent noise waveform causes an error.

2. **Running estimate:** Why do early errors move BER more than late errors?
   - Each event contributes \(1/N\); that contribution is large when \(N\) is
     small and shrinks as independent trials accumulate.

3. **Confidence interval:** What happens to Wilson width with more independent
   trials?
   - It generally narrows at roughly a \(1/\sqrt{N}\) rate under the stationary
     independent Bernoulli model.

4. **Distribution:** Why do the 40 block BER measurements differ even though
   every block uses the same receiver and \(E_b/N_0\)?
   - Each block receives different noise samples and therefore a different
     finite error count.

5. **Eb/N0 sweep:** Why do the statistic distributions create fewer errors as
   \(E_b/N_0\) increases?
   - Noise spread decreases relative to symbol energy, so fewer statistics
     cross the zero hard-decision boundary.

## Prediction checks

1. If `symbol_count` were one, what BER values could be reported?
   - Only zero or one; neither is a useful probability characterization.

2. If the trial count increases from 100 to 10,000, by about what factor does a
   typical standard-error scale shrink?
   - About ten, because uncertainty scales as \(1/\sqrt{N}\).

3. If a high-SNR run observes zero errors, is true BER exactly zero?
   - No. The run supplies a finite upper bound under its assumptions, not proof
     of an impossible error.

4. If the same noise waveform is processed by two different algorithms, can
   that common input be useful?
   - Yes, for a paired controlled comparison. It is still one realization per
     algorithm and cannot be counted repeatedly as independent trials.

5. Does using seed 2701 guarantee closeness to the analytic BER?
   - No. It guarantees reproducibility. Trial independence, count, and model
     correctness govern statistical usefulness.

## Correct these interpretations

- “The running BER should fall smoothly.”
  - Incorrect. Random error arrivals can move it up or down; only long-run
    convergence is expected.
- “A narrow Wilson interval proves the receiver model.”
  - Incorrect. Coverage relies on model assumptions, especially independent,
    stationary Bernoulli outcomes.
- “Four thousand identical columns are four thousand Monte Carlo trials.”
  - Incorrect. They contain one noise realization and have effective sample
    size one.
- “Zero observed errors proves perfect detection.”
  - Incorrect. It bounds a probability only within a stated finite-trial model.
- “Simulation BER is measured radar hardware performance.”
  - Incorrect. P27 uses normalized synthetic BPSK/AWGN data and makes no RF,
    bench, real-time, operational, or field claim.

## Failure, recovery, and operational checks

- Confirm `results.broken.unique_statistic_count == 1`, its reported BER is
  zero, and `results.broken.independence_valid` is false.
- Confirm `results.recovery.exact_match` is true after a fresh private-stream
  rerun, and distinguish repeatability from representativeness.
- Use **Ctrl+C** to cancel if needed, then rerun the whole script; do not treat
  partial arrays as final Monte Carlo evidence.
- Confirm reruns remove only `P27`-tagged figures and do not reset the global
  random stream, write files, touch `.learning/`, start workers/timers, or leave
  an external transaction to roll back.
- Confirm the fixed trial, waveform, sweep, figure, and numeric-value ceilings
  are validated before random generation or allocation.
- Confirm the matched filter, hard decision, BER, Wilson limits, and analytic
  `erfc` reference are explicit base-MATLAB operations.

## Completion checklist

- [ ] I can explain why one correct decision does not estimate BER.
- [ ] I can point to error events, the running estimate, and interval width.
- [ ] I can distinguish trial-count convergence from monotonic convergence.
- [ ] I can explain why repeated data invalidate an independence-based interval.
- [ ] I can state what a reproducible seed proves and what it does not prove.

## Short teach-back rubric

In two or three sentences, answer the guiding question. A complete answer says
that noise makes each independent outcome random, that averaging many trials
estimates probability with uncertainty that shrinks roughly as
\(1/\sqrt{N}\), and that copying or reseeding one lucky realization creates no
new evidence even if the result is exactly reproducible.

## Repository rollback

Rollback returns only P27 to `scaffolded` and removes its owned implementation,
test, catalog, and evidence additions. It preserves P26 and all canonical
identities. Runtime recovery is separate: regenerate the independent bank from
the private seed and rerun from the beginning.
