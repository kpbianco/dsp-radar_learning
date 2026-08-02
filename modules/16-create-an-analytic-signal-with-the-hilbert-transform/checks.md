# P16 Checks: Ask Whether the Arrow Has Length

## Guiding question

How can a real waveform be represented by a complex envelope?

## Baseline observation checks

1. Why does the real waveform cross zero while analytic magnitude does not?
   Expected: the real waveform is one projection of the rotating complex arrow;
   magnitude measures its length and follows the positive envelope.
2. Which part of the analytic signal reconstructs the measured waveform?
   Expected: its real part, to numerical precision.
3. What happened to the negative-frequency copy?
   Expected: the FFT mask zeroed it and doubled ordinary positive-frequency
   bins, while DC and Nyquist were retained once.
4. What does the slope of unwrapped phase measure?
   Expected: cycles per second after scaling by `fs/(2*pi)`, interpreted here as
   instantaneous frequency of the dominant narrowband component.

## Sweep prediction checks

1. If envelope depth rises from 0.20 to 0.90, what changes physically?
   Expected: the minimum complex magnitude falls from 0.80 to 0.10 V; the
   designed phase/frequency law does not change.
2. Why can the deepest envelope still produce a noisier frequency estimate?
   Expected: a fixed perturbation creates a larger angular error on a shorter
   vector.
3. At 3 Hz phase modulation, what peak frequency deviations follow phase
   indices 0.20, 0.60, and 1.20 rad?
   Expected: 0.6, 1.8, and 3.6 Hz because deviation is `beta*f_mod`.
4. Does increasing phase deviation necessarily change analytic magnitude?
   No. This sweep changes angle motion while holding the designed envelope fixed.

## Broken-case and interpretation checks

1. Is the large raw frequency spike near the notch a real carrier excursion?
   No. Magnitude is below the noise scale, phase direction is unstable, and its
   numerical derivative magnifies the error.
2. What is phase at exactly zero complex magnitude?
   Undefined: every angle points to the same origin.
3. Why must the 0.05 V gate check both samples used by a phase difference?
   Frequency for interval `n` uses phase at `n-1` and `n`; one unreliable
   endpoint can corrupt the difference. The gate does not recover missing phase.
4. Is every multicomponent waveform guaranteed to have one useful
   instantaneous frequency?
   No. The interpretation is strongest for one dominant narrowband component;
   mixtures can produce ambiguous envelope/phase behavior.
5. Why keep DC and Nyquist rather than double them?
   They do not have distinct negative-frequency conjugate partners in an even
   sampled record.

## Malformed, resource, timeout, cancellation, and isolation checks

- A logical/nonfinite sample rate or seed, odd/wrong-size record, off-Nyquist
  carrier, noncanonical sweep, invalid notch, inconsistent reliability gate, or
  breached record/FFT/sweep/storage/figure ceiling must fail before random,
  signal, FFT, or figure allocation.
- Work is bounded by one 4096-sample record, two three-case sweep loops, a
  250000-value retained-storage estimate, and five figure groups. The script has
  no wait, interactive input, timer, parallel/background work, file/network, or
  audio operation. Ctrl+C cancels it.
- Rerun recovers without cleanup: only `P16`-tagged figures are removed and old
  `results` is cleared before validation. A private seed leaves the global
  random stream and unrelated figures untouched.
- Base MATLAB is the only runtime dependency. Static Python checks and an
  independent numerical model are not MATLAB execution or rendered figures.

## Recovery and rollback check

- Recovery: preserve the envelope observation and set unreliable frequency
  samples to `NaN`; do not conceal the failure with invented interpolation.
- Rollback: remove P16-owned module artifacts, P16/shared allowed tests, catalog
  changes, and P16 evidence; restore only P16 status to `scaffolded`. Preserve
  P15, later canonical identities, and local learner state.

## Teach-back completion

A satisfactory two- or three-sentence answer must:

- explain how doubling positive-frequency bins and zeroing negative-frequency
  bins produces a one-sided complex representation of the real signal;
- identify analytic magnitude as envelope and unwrapped-angle slope as
  instantaneous frequency for this dominant narrowband component; and
- reject phase/frequency estimates near zero magnitude rather than treating a
  noise-driven spike as physical motion.

Do not record personal completion until the learner has inspected the plots and
given this teach-back. Learner progress remains local under `.learning/`.
