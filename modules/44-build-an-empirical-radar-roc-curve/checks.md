# P44 checks: Build an Empirical Radar ROC Curve

Guiding question: **How does threshold choice trade probability of detection against false alarm?**

## Observation checks

1. In Figure 1, which population supplies the numerator and denominator of
   `Pfa`?

   Expected: threshold crossings among target-absent H0 trials divided only by
   the H0 trial count.

2. In Figure 2, what happens to both coordinates while the threshold rises on
   one SNR curve?

   Expected: both `Pfa` and `Pd` are non-increasing because fewer samples from
   both conditioned populations cross.

3. At a fixed `Pfa`, what changes as SNR rises from -6 to 12 dB?

   Expected: `Pd` rises because the H1 matched-filter distribution moves away
   from H0; the ROC bows toward the upper-left.

4. Why does Figure 4 show `1/N` beside the empirical `Pfa`?

   Expected: one event changes a count-based probability by `1/N`. A run with
   resolution larger than the probability of interest cannot characterize
   that tail precisely.

## Prediction checks

1. The threshold is raised while SNR and searched-cell count stay fixed. What
   happens to expected false alarms and detections?

   Expected: both fall. Whether this is a better operating point depends on the
   relative costs of false alarms and missed targets.

2. SNR rises while the threshold remains 3.09 noise RMS. Predict `Pfa` and
   `Pd`.

   Expected: `Pfa` stays fixed because H0 is unchanged; `Pd` rises because H1
   shifts right.

3. Per-cell `Pfa` stays 0.001 while target-absent searched cells rise from one
   million to two million. Predict expected false alarms per scan.

   Expected: they double from 1000 to 2000. The ROC itself does not move.

4. A 500-trial H0 bank reports zero false alarms. What can you conclude about
   true `Pfa`?

   Expected: only that this finite bank observed none. Its count resolution is
   0.002, so zero is not proof of zero probability or of meeting a much smaller
   operational requirement.

## Interpretation checks

1. Why is `d_prime = sqrt(SNR_MF)` rather than `SNR_MF`?

   Expected: matched-filter SNR is a power ratio, while `d_prime` measures an
   amplitude separation in units of standard deviation.

2. Why can target-present threshold crossings not be included in the
   false-alarm count?

   Expected: false alarm is conditioned on H0. H1 crossings are detections; a
   pooled denominator changes the metric with target prevalence.

3. Why do all SNR curves share the same empirical `Pfa` coordinates here?

   Expected: the same normalized H0 bank and threshold grid are used. Target
   SNR changes H1, not the target-absent distribution.

4. What exactly is broken when the quietest H0 trials are selected, their
   maximum becomes the threshold, and that same bank is evaluated?

   Expected: selection is biased and tuning/evaluation reuse the same finite
   noise samples, so zero crossings are guaranteed by construction and do not
   estimate unseen-tail risk.

5. Does agreement with the dashed Gaussian ROC validate a hardware radar?

   Expected: no. It checks the seeded signed-Gaussian model. A physical system
   can add mismatch, clutter, dependence, quantization, unknown phase, and
   other detector-statistic changes.

## Completion checklist

- I can identify H0 and H1 and keep the `Pfa` and `Pd` denominators separate.
- I can explain why raising threshold lowers both ROC coordinates.
- I can distinguish changing detector quality/SNR from moving along one curve.
- I can use `N_H0 * Pfa` to estimate false-alarm workload without calling it an
  exact per-scan count.
- I can explain why empirical probability has finite resolution and why zero
  observed events are not zero risk.
- I can identify the tune-and-score data-reuse failure and the independent-bank
  recovery.

## Short teach-back rubric

In two or three sentences, answer the guiding question and choose between two
hypothetical points: `(Pfa=0.01, Pd=0.95)` and `(Pfa=0.001, Pd=0.80)` for one
million target-absent cells per scan. A complete answer must:

- say that lowering threshold generally raises both detection and false-alarm
  probability;
- translate the points to about 10,000 versus 1,000 expected false alarms per
  scan; and
- state what operational miss/false-alarm cost or downstream capacity is still
  needed to choose, rather than calling either point universally best.

Personal completion remains a learner/tutor decision after this teach-back; it
is not established by repository tests or by simply running the script.
