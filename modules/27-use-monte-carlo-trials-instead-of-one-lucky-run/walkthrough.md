# P27 Walkthrough: Use Monte Carlo Trials Instead of One Lucky Run

## Guiding question

Why is one noise realization not enough to judge an algorithm?

## Before running

P23 is the symbol/decision prerequisite and P24 is the matched-filter
prerequisite. Run `experiment.m` from this folder. It uses base MATLAB, a
private seed, 4,000 bounded trials, 16 samples per symbol, and five P27-tagged
figure groups. It writes no files and does not change MATLAB's global random
stream.

## 1. Inspect one trial without trusting it

Open **P27 Matched-filter signal flow**. The upper plot shows one transmitted
pulse and its noisy received waveform. This particular trial is decoded
correctly.

Ask one observation question: what fact is missing if all you know is that this
one decision was correct?

The missing fact is how often another independent noise waveform moves the
matched-filter statistic across zero. One outcome cannot reveal that
probability. The lower plot uses all independent trials and shows the overlap
between statistics for transmitted \(-1\) and \(+1\).

## 2. Watch random outcomes become a running estimate

Open **P27 Running Monte Carlo estimate**. Read the upper error indicator first:
each trial is either correct (0) or wrong (1). Then inspect the lower running
BER.

Expected observations:

- The estimate jumps sharply at small trial counts.
- Later errors still move it, but by less.
- The two Wilson limits narrow as independent evidence accumulates.
- The analytic reference can fall outside an individual pointwise 95%
  interval, and the empirical estimate need not approach theory monotonically.
- The final printed error count is substantial enough to make the BER more
  informative than a zero-error anecdote.

## 3. Read the final empirical distributions

The decision-statistic distributions show why errors occur: noise sometimes
pushes a \(+1\) statistic below zero or a \(-1\) statistic above zero.
Because Gaussian noise has unbounded tails, the first and last display bins
absorb any statistic beyond the labeled finite grid so the probability mass is
not silently discarded.

Next open **P27 Empirical BER distribution**. The 4,000 trials are divided into
40 non-overlapping blocks of 100. Every block uses the same receiver and
operating point, yet their measured BER values differ. That spread is the
finite-sample behavior hidden by a single final average.

## 4. Sweep one variable: independent trial count

The first controlled sweep uses fixed prefixes:

```text
N = [10, 25, 100, 500, 4000]
```

The BPSK symbols, normalized noise bank, pulse, \(E_b/N_0=2\) dB, detector,
and seed remain fixed. Only the number of included independent trials changes.

Expected observation: short estimates can look surprisingly good or bad, and
their Wilson intervals are wide. The 4,000-trial interval is narrower than the
10-trial interval. Do not claim every longer prefix must be closer to theory;
convergence is statistical, not monotonic.

## 5. Sweep one variable: energy per bit relative to noise

The second sweep uses:

```text
E_b/N_0 = [-4, -2, 0, 2, 4] dB
```

Keep the 4,000 symbols, unit-Gaussian noise samples, pulse, and decision rule
fixed. Change only the scale of the noise. Empirical and analytic BER should
fall as \(E_b/N_0\) rises because fewer matched-filter statistics cross zero.

This is a controlled comparison, not five unrelated lucky runs: common random
numbers expose the effect of noise scale with less run-to-run distraction.

## 6. Diagnose the intentionally broken case

Open **P27 Broken reuse and recovery**. The script finds one correctly decoded
baseline trial and repeats its received waveform 4,000 times. The nominal BER
is zero and a blindly calculated Wilson upper limit is very small.

That conclusion is invalid. `results.broken.unique_statistic_count` is one and
`results.broken.independence_valid` is false. The array has 4,000 columns, but
the experiment contains only one noise realization. This failure models a
reseed-inside-the-loop bug, reused capture, cached trial, or accidental copy.

## 7. Recover with independent trials

Recovery does not continue from the copied bank. It creates a fresh private
stream with seed 2701, regenerates the 4,000 independent symbol/noise trials,
and reruns the explicit matched filter and hard decision. The script requires
an exact match to every baseline symbol, noise sample, statistic, and outcome.

Reproducibility proves the experiment can be audited. Agreement with analytic
BER and a sensible interval support the statistical interpretation.

## 8. Operational behavior and isolation

- Press **Ctrl+C** to cancel a mistaken run. There is no worker, timer, or
  background task to clean up.
- A full rerun removes only figures tagged `P27` and replaces P27 workspace
  results from its private seed. It leaves unrelated figures, the global random
  stream, and `.learning/` unchanged.
- Cancellation may leave partially assigned workspace variables. Rerun the
  entire script before interpreting them. The script cannot restore unrelated
  caller variables overwritten before cancellation.
- There is no network request, external transaction, persisted simulation
  output, toolbox dependency, or hardware input.
- Fixed ceilings are 4,000 trials, 16 samples per symbol, five cases in each
  sweep, five figure groups, and 700,000 conservatively counted numeric values.

## Completion connection

Explain why the independent running estimate becomes more useful with trial
count, why the copied-noise report is invalid even though it is reproducible,
and what a finite zero-error result can and cannot establish.

## Rollback

Repository rollback removes the four P27 implementation artifacts, P27-named
test/evidence files and catalog additions, restores this README to its
scaffolded brief, and restores only P27's manifest status to `scaffolded`.
P26 and later canonical module identities remain unchanged.
