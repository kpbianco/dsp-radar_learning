# P20 Walkthrough — Read the Evidence Before Trusting the Number

## Guiding question

How accurately can frequency and phase be estimated from a finite noisy record?

P19 is the prerequisite. This walkthrough assumes the I/Q trajectory is not
dominated by the DC, gain, or quadrature errors diagnosed there.

## Baseline

1. Run `experiment.m` unchanged. The script uses private seed `1020`; it does
   not change MATLAB's global random stream.
2. In **Noisy rotating phasor**, inspect I and Q, then the I/Q plane. The clean
   pointer rotates smoothly while noise moves each measured endpoint.
3. In **Baseline frequency estimates**, read the `4 Hz` FFT spacing. The true
   `123.25 Hz` line is between grid points. Observe which method is locked to a
   bin and which two report sub-bin values.
4. Read the console errors in hertz. Do not choose a universal winner from this
   one realization.
5. In **Coherent phase estimates**, look for residual slope after each candidate
   frequency is removed. A frequency error becomes a phase ramp; the horizontal
   red level is the coherently combined initial-phase estimate.
6. Compare phase errors in radians modulo `2*pi`, not by ordinary subtraction.
   The baseline coherence should exceed the `0.20` reporting gate.

Expected observation: the peak-bin estimate carries visible grid error. The
interpolated peak and coherent phase increment can estimate between bins, but
their errors differ because they use different evidence.

## Sweep 1 — change only SNR

1. Move to **SNR estimator sweep**. The script uses `[-10 0 10 20] dB` and 40
   deterministic trials at each point.
2. Confirm that tone frequency, phase, amplitude, sample rate, 256-sample
   duration, and every estimator equation stay fixed. Only complex-noise RMS
   changes; the same standardized-noise trial rows are rescaled in every case.
3. Read frequency bias separately from frequency standard deviation. Bias is a
   repeatable offset; standard deviation is realization-to-realization spread.
4. Read circular phase bias separately from circular phase spread. Notice how
   low SNR weakens adjacent-product coherence and makes phase less stable.

Expected observation: higher SNR reduces random spread. Peak-bin bias can stop
improving after it is locked to the nearest grid point, while the sub-bin
methods continue to use phase or peak-shape information.

## Sweep 2 — change only record length

1. Move to **Record length estimator sweep**. Durations are `0.0625`, `0.125`,
   `0.25`, and `0.5 s` at the same sample rate and per-sample SNR.
2. Confirm that the physical tone, initial phase, noise-to-signal ratio, and 40
   trials remain fixed. Each duration uses prefixes of the same noise rows, so
   only the number of coherently observed samples changes.
3. Compare the bias and spread panels. Longer records narrow FFT spacing and
   accumulate more phase evidence.
4. Look for the peak-bin error floor: a longer record changes its grid, but it
   still reports a grid point. Sub-bin methods are not restricted to that
   output spacing.

Expected observation: longer coherent observation generally reduces spread,
especially for interpolated and phase-based estimates. Small non-monotonic
changes in one curve can occur because the fixed physical tone lands at a
different fractional position on each FFT grid.

## Broken case — wrapped endpoint phase and vanishing amplitude

1. In **Wrapped phase and low amplitude failure**, follow the noise-free phase
   sawtooth. The true accumulated phase crosses `2*pi` many times.
2. The broken endpoint method keeps only the principal angle between the first
   and last samples and divides it by elapsed time. Its near-zero answer is not
   evidence of a slow tone; the missing whole turns were discarded.
3. The recovered method forms every adjacent product, whose phase step is
   inside signed Nyquist, sums those products coherently, and then takes one
   angle. It recovers the noise-free `123.25 Hz` tone.
4. Inspect the low-amplitude I/Q cloud. Amplitude is `0.02 V`, but the exact
   baseline receiver-noise samples and RMS are reused. The raw phase-increment
   calculation still returns a number even though amplitude is the only changed
   input.
5. Compare its coherence with the `0.20` gate. The script stores the raw
   candidate for diagnosis but sets the reported estimate to `NaN`: rejected,
   not zero and not accepted.

Failure interpretation: phase wrapping is an ambiguity error; low amplitude is
an information failure. More decimal places repair neither one.

## Recovery, cancellation, isolation, compatibility, and bounds

- Rerun from the top unchanged to recover or repeat the canonical experiment;
  use the predefined sweep arrays for parameter changes. The private seed
  repeats the experiment without altering the global random stream. The fixed
  canonical guards intentionally reject ad hoc control edits until the
  corresponding tests and resource analysis are updated together.
- Invalid, nonfinite, logical, noncanonical, or oversized controls fail before
  random samples, FFTs, cleanup, or figures are created.
- Execution is foreground-only: two four-case sweeps, 40 trials per case, fixed
  three-estimator loops, and no unbounded loop, timer, worker, file, network,
  audio, or device lifetime. Ctrl+C cancels it directly.
- Ctrl+C after validation can leave a partial P20 figure set and
  empty/incomplete `results`. Rerun from the top to replace only P20-tagged figures
  and rebuild deterministic results.
- The script uses base MATLAB operations and has no toolbox, external service,
  file, or hardware dependency. Other modules' figures and learner state are
  isolated from P20 cleanup.
- The largest record is 512 samples, each sweep has four cases, trial count is
  40, six figure groups are fixed, and the conservative numeric-storage budget
  stays below 100000 values.
- Rollback removes only P20 artifacts, tests, evidence, and catalog text, then
  restores only P20's manifest/index status. Preserve implemented P19, later
  module identities, managed contracts, and local `.learning/` progress.

## Concept connection and completion handoff

P11–P13 established FFT bins, leakage, and the difference between display
density and information. P16–P19 established meaningful complex phase and a
usable I/Q receiver. P20 combines them: frequency and phase accuracy depend on
SNR, coherent duration, estimator assumptions, and confidence—not merely FFT
spacing.

Before completion, explain which estimator you would trust in the displayed
high-SNR/long-record region and which you would distrust in the low-coherence
case. Then answer the teach-back in `checks.md`; personal completion remains a
manual learner action.
