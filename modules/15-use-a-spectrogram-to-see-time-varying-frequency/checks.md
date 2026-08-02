# P15 Checks: Read the Window Before Reading the Colors

## Guiding question

How do window duration and overlap control time-frequency visibility?

## Baseline observation checks

1. Which trace remains horizontal for the full record?
   Expected: the 90 Hz steady tone.
2. Where are the short event and the hop?
   Expected: the 380 Hz burst is centered at about 1.531 s, and the continuous-
   phase track changes from 156 to 174 Hz at 2.75 s.
3. What do 128 samples and 50% overlap mean at 1024 Hz?
   Expected: a 125 ms window and a 62.5 ms frame-center step.
4. Why is each timestamp at the window center?
   Expected: the column summarizes all samples in that window; assigning it to
   the first sample would shift the apparent event time early.

## Sweep prediction checks

1. Before comparing panels, predict which window best localizes the 64-sample
   burst.
   Expected: 64 samples; its time aperture matches the event scale.
2. Predict which window best separates an 18 Hz change near the hop?
   Expected: 512 samples; its approximate 8 Hz Hann width is narrower than the
   separation. The 128- and 64-sample widths are about 32 and 64 Hz.
3. If overlap rises from 0% to 75% at fixed `M = 128`, what stays fixed?
   Expected: window duration, 8 Hz FFT spacing, and about 32 Hz Hann width.
4. What changes?
   Expected: hop/column spacing falls from 125 to 31.25 ms, frame count grows,
   and a window center is more likely to land near a short event.

## Interpretation checks

1. Does the 75%-overlap spectrogram have four times better frequency resolution
   than 0% overlap?
   No. It samples time four times as often with the same window response.
2. Does a 512-point FFT of 64 samples produce 2 Hz physical resolution?
   No. It produces 2 Hz display spacing while the 64-sample Hann response stays
   roughly 64 Hz wide.
3. Why can the long window show energy at both hop frequencies near 2.75 s?
   It includes samples from both sides of the transition. That helps distinguish
   their frequencies but smears when the change occurred.
4. Why is a dim burst in the 0%-overlap panel not proof of absence?
   The event starts at a frame boundary and occupies the downweighted first half
   of one Hann window instead of being centered at its peak.
5. Are adjacent 75%-overlap columns independent new measurements?
   No. They reuse most of the same samples.

## Broken-case and recovery checks

- Broken claim: “The zero-padded short-window plot has 2 Hz resolution.”
- Classification: display-density error; it confuses FFT-grid interpolation with
  the finite observation's main-lobe width.
- Recovery: compare `hop_frequency_separation_hz` with
  `broken_true_main_lobe_width_hz`, then choose a longer actual window if close
  frequencies matter.
- Rollback: remove P15-owned artifacts and restore only P15's manifest status to
  `scaffolded`; do not alter P14 or learner state.

## Malformed, resource, timeout, and isolation checks

- A nonfinite/logical sample rate, invalid seed, odd or oversized window,
  overlap outside `[0,1)`, fractional/nonprogressing hop, off-band component,
  out-of-record event, changed canonical sweep, or breached storage ceiling must
  fail before random, signal, FFT, spectrogram-matrix, or figure allocation.
- Every loop is bounded by record, frame, sweep, FFT, and figure ceilings.
  Ctrl+C cancels; rerun recovers without cleanup because the script writes no
  files and launches no background work.
- The private seed leaves MATLAB's global random stream unchanged; figure
  cleanup is restricted to tag `P15`, and prior `results` is cleared at rerun
  start so a malformed run cannot expose stale output.
- Base MATLAB is the only runtime dependency. Static repository success is not
  MATLAB runtime or rendered-figure evidence.

## Teach-back completion

A satisfactory two- or three-sentence answer must:

- choose a short window for transient timing and a long window for the close hop
  frequencies;
- state that overlap controls time-column spacing, not the window's frequency
  response; and
- reject zero-padded bin spacing as proof of improved physical resolution.

Do not record personal completion until the learner has inspected the plots and
given this teach-back. Learner completion remains local under `.learning/`.
