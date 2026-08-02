# P18 Checks: Read Frequency Direction from I/Q

## Guiding question

Why can complex samples distinguish positive and negative frequencies?

## Baseline observation checks

1. What distinguishes the `+160 Hz` and `-160 Hz` complex sample streams?
   Expected: their sample-to-sample phase increments have opposite signs, so
   their I/Q trajectories rotate counterclockwise and clockwise and their
   centered-FFT peaks occupy opposite signed bins.
2. Why do their real projections coincide?
   Expected: the tones are conjugates, and conjugation leaves the real part
   unchanged: `real(z)=real(conj(z))`.
3. Why does the real spectrum show both `+160` and `-160 Hz`?
   Expected: a real sequence has conjugate-symmetric spectral copies. They are
   the redundant representation of one cosine, not two separately measured
   directions.
4. Is negative frequency negative power or negative energy?
   No. It is clockwise phase progression under this convention.

## Downconversion and sweep prediction checks

1. What does a negative-exponent 600 Hz complex LO produce from RF sides at
   760 and 440 Hz with paired phase?
   Expected: `+160 Hz` from the upper side and `-160 Hz` from the lower side.
2. Why do the filtered real-cosine mixer outputs coincide?
   Expected: after rejecting their different sum terms, both desired difference
   terms are the same real cosine. Real data keeps `|Delta|` but not side-of-LO.
3. As offset magnitude changes through 40, 160, and 400 Hz, what changes?
   Expected: rotation speed changes; direction remains opposite and the real
   projections remain identical.
4. At sample rates 2048, 512, and 256 samples/s, where does `+160 Hz` appear?
   Expected: `+160`, `+160`, then `-96 Hz`. The paired negative tone appears at
   `-160`, `-160`, then `+96 Hz`.
5. Does the 256 samples/s case show complex sampling failed?
   No. It correctly records the signed discrete-time aliases. The unknown
   analog frequency was already ambiguous because Nyquist was violated.

## Broken-case and interpretation checks

1. What does the broken case discard?
   It discards Q by applying `real(...)` before sign estimation.
2. Why do both broken estimates become zero instead of opposite signs?
   The real adjacent-sample product has no quadrature angle; the representation
   no longer contains rotation direction.
3. Why is `abs(frequency)` not recovery?
   It deliberately erases side-of-LO/Doppler direction and makes distinct
   physical cases look equal.
4. Does storing a real waveform in a complex numeric type restore information?
   No. A zero or invented Q channel is not an independent quadrature
   measurement.
5. Does a complex LO by itself remove both images from a real RF input?
   No. P17 shows that a real input has conjugate sides; multiplication moves
   them and a channel filter or analytic representation selects the desired one.
6. At exact DC or the even-rate Nyquist point, can the paired signs be distinct?
   No. DC has no rotation, and `exp(+j*pi*n)=exp(-j*pi*n)` at Nyquist.

## Malformed, resource, timeout, cancellation, and isolation checks

- A logical/nonfinite seed, rate, count, frequency, amplitude, phase, noise,
  LO, cutoff, tap count, guard, or duration; an odd/wrong record; off-Nyquist
  RF sides; a changed sweep; an even FIR; a cutoff that loses a desired beat or
  passes a sum term; a fractional sweep record; or a breached record/FFT/FIR/
  sweep/storage/figure ceiling must fail before random, signal, FFT, FIR, or
  figure allocation.
- Work is bounded by one 4096-sample baseline, one 129-tap FIR, two three-case
  loops, 180000 retained-value estimate, and six figure groups. There is no
  wait, prompt, timer, parallel/background, file/network, system, or audio
  operation. Ctrl+C cancels the foreground run, but an interrupt after cleanup
  can leave partial P18 figures and empty/incomplete `results`; rerun from the
  top to recover.
- A malformed rerun preserves the last valid P18 output because validation
  precedes cleanup. A valid rerun replaces only P18-tagged figures and
  `results`; its private stream leaves the global random stream and unrelated
  figures unchanged.
- Base MATLAB is the only runtime dependency. Static Python contracts and
  independent numerical models are not MATLAB/Octave execution or rendered
  plot evidence.

## Recovery and rollback check

- Recovery: retain both I and Q, rerun, and confirm phase-step estimates and
  signed centered-FFT peaks at `+160/-160 Hz`.
- Rollback: remove P18-owned artifacts, allowed P18/shared tests and catalog
  changes, and P18 evidence; restore only P18 status to `scaffolded`. Preserve
  implemented P17, later canonical identity, learner state, and active-batch
  activation.

## Teach-back completion

A satisfactory two- or three-sentence answer must:

- explain that a real projection cannot distinguish conjugate `+f` and `-f`
  tones because it creates the same cosine and mirrored spectrum;
- connect positive/negative frequency to counterclockwise/clockwise I/Q phase
  progression and to upper/lower side-of-LO after complex downconversion; and
- state that I/Q preserves the signed discrete-time frequency but cannot undo
  analog aliasing caused by an insufficient sample rate.

Do not record personal completion until the learner has inspected the plots and
given this teach-back. Learner progress remains local under `.learning/`.
