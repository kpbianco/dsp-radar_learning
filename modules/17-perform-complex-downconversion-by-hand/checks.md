# P17 Checks: Keep the Sign of the Difference

## Guiding question

How does multiplying by a complex oscillator move an RF/IF signal to baseband?

## Baseline observation checks

1. Where do the two RF copies at `+240` and `-240 Hz` move after multiplying by
   the 240 Hz negative-exponent LO?
   Expected: the positive copy moves to `0 Hz`; the negative copy moves to
   `-480 Hz`.
2. Which operation performs translation and which selects the receiver channel?
   Expected: complex multiplication translates both copies; the low-pass FIR
   selects the difference-frequency copy near zero.
3. Why is the unscaled desired term about `0.5 V` for a `1 V` real cosine?
   Expected: the real cosine divides equally into positive- and negative-
   frequency complex exponentials. The visible `2x` calibration restores the
   real peak-amplitude convention.
4. What information remains when exact LO match makes frequency zero?
   Expected: the stationary I/Q point retains carrier amplitude and relative
   phase `phiRF-phiLO`.

## Sweep prediction checks

1. What are `fBB` and rotation for LOs 204, 240, and 276 Hz with a 240 Hz RF?
   Expected: `+36 Hz` counterclockwise, `0 Hz` stationary, and `-36 Hz`
   clockwise because `fBB=fc-fLO`.
2. Is the 276 Hz high-side LO a failure?
   No. It creates valid negative baseband frequency and preserves which side of
   the LO contained the RF signal.
3. If only LO phase rises by `pi/2`, what changes?
   Expected: output phase falls by `pi/2`; calibrated magnitude and baseband
   frequency remain unchanged.
4. If the low-pass cutoff were below `|fc-fLO|`, did mixing fail?
   No. Translation still occurred, but the chosen channel filter attenuated the
   desired result.

## Broken-case and interpretation checks

1. Why does `exp(+j*2*pi*fLO*t)` still yield baseband from a real input?
   Expected: the input contains a negative-frequency conjugate RF copy, and the
   positive-exponent LO translates that copy toward zero.
2. At a 216 Hz LO, what distinguishes the wrong and recovered conventions?
   Expected: the broken positive exponent selects `-24 Hz` clockwise motion;
   the declared negative exponent selects `+24 Hz` counterclockwise motion.
3. Why is taking `abs(frequency)` not a valid recovery?
   It discards side-of-LO and direction information needed for coherent DSP and
   radar Doppler interpretation.
4. Does low-pass filtering correct a wrong mixer sign?
   No. Both translated candidates can lie inside the same passband; the sign
   convention must be correct before filtering.
5. Would an already analytic positive-frequency input contain the same
   conjugate image?
   No. P16's one-sided analytic representation suppresses the redundant
   negative-frequency copy; its amplitude convention also differs from a real
   cosine's `A/2` term.

## Malformed, resource, timeout, cancellation, and isolation checks

- A logical/nonfinite seed, sample rate, amplitude, phase, noise, LO, cutoff,
  tap count, or guard; an odd/wrong-size record; an off-Nyquist carrier/LO; a
  noncoherent canonical tone; a changed sweep; an even/wrong FIR length; a
  cutoff that excludes a sweep beat or approaches the image; or a breached
  record/FFT/FIR/sweep/storage/figure ceiling must fail before random, signal,
  FIR, FFT, or figure allocation.
- Work is bounded by one 4096-sample record, one 129-tap FIR, two three-case
  loops, 180000 retained-value estimate, and five figure groups. The script has
  no wait, interactive input, timer, parallel/background work, file/network,
  system, or audio operation. Ctrl+C cancels the foreground run.
- Rerun recovers without cleanup: only P17-tagged figures are removed and old
  `results` is cleared before validation. A private seed leaves MATLAB's global
  random stream and unrelated figures untouched.
- Base MATLAB is the only runtime dependency. Static Python checks and an
  independent numerical model are not MATLAB/Octave execution or rendered
  figures.

## Recovery and rollback check

- Recovery: restore `exp(-j*2*pi*fLO*t)`, rerun, and verify signed phase slope;
  do not hide a side-selection error with absolute value.
- Rollback: remove P17-owned artifacts, allowed P17/shared tests and catalog
  changes, and P17 evidence; restore only P17 status to `scaffolded`. Preserve
  implemented P16, later canonical identity, local learner state, and the
  operator's active-batch record.

## Teach-back completion

A satisfactory two- or three-sentence answer must:

- predict `fBB=fc-fLO` and connect its sign to I/Q rotation direction;
- explain that a real cosine creates desired and sum-frequency mixer terms of
  amplitude `A/2`, with an explicit `2x` calibration if real peak amplitude
  should be reported; and
- state that multiplication translates both terms while low-pass filtering
  selects one, including why reversing the oscillator sign selects the
  conjugate side rather than producing no signal.

Do not record personal completion until the learner has inspected the plots and
given this teach-back. Learner progress remains local under `.learning/`.
