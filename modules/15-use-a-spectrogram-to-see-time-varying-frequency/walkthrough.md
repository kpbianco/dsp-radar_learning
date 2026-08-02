# P15 Walkthrough: One Time-Frequency Tradeoff at a Time

## Guiding question

How do window duration and overlap control time-frequency visibility?

Run `experiment.m` from the top. Keep the visible controls unchanged for the
first pass. The script is deterministic, writes no files, and uses a private
seed without changing MATLAB's global random stream.

## Baseline

1. In the first figure, identify the horizontal 90 Hz track, the rising
   220-to-320 Hz chirp, the short 380 Hz flash, and the 156-to-174 Hz hop.
2. Read the baseline metrics: 128 samples is 125 ms, the 50% overlap produces a
   62.5 ms column step, the FFT grid is 8 Hz, and the approximate Hann width is
   32 Hz.
3. Find the chirp ridge. Its stair steps follow the 8 Hz grid; they do not mean
   the physical chirp jumps every 8 Hz.

Expected observation: the baseline shows all four behaviors, but the burst
occupies more than its true 62.5 ms duration and the 18 Hz hop frequencies are
not sharply separated by a roughly 32 Hz window response.

## Sweep 1 — Change only window duration

The second figure holds the record, Hann shape, 50% overlap fraction, amplitude
scaling, and display floor fixed. Only `M` changes through 512, 128, and 64.

1. Compare the 380 Hz burst from top to bottom. The 512-sample view spreads it
   over time; the 64-sample view places its peak at the true center.
2. Compare a column centered at the 2.75 s hop. The long view can show narrow
   energy near both 156 and 174 Hz because 18 Hz exceeds its roughly 8 Hz Hann
   width. The short response is roughly 64 Hz wide and blends them.
3. Read `results.window_resolution_ratio`: values above one put the hop spacing
   beyond the approximate main-lobe width; values below one do not.

Physical connection: longer coherent observation accumulates more cycles and
sharpens frequency, while shorter observation narrows the time aperture.

## Sweep 2 — Change only overlap

The third figure fixes `M = 128` and changes overlap through 0%, 50%, and 75%.

1. Confirm all three panels report the same 8 Hz bins and roughly 32 Hz Hann
   width.
2. Compare column spacing: 125, 62.5, then 31.25 ms.
3. At 380 Hz, compare the burst peak. The 0%-overlap grid places the burst at a
   Hann boundary; 75% overlap supplies a centered frame and captures it more
   strongly.

Expected observation: overlap makes the time grid denser and reduces alignment
risk, but the width of tone tracks in frequency does not improve.

## Broken case — Mistake display density for resolution

The left panel of the fourth figure uses the 64-sample window but pads its FFT
to 512 points. It intentionally labels the tempting, broken claim: “2 Hz pixels
mean 2 Hz resolution.”

1. Compare its 2 Hz grid with its 64 Hz approximate Hann width.
2. Compare the right panel, which has the same 2 Hz grid from 512 actual samples
   and an 8 Hz Hann width.
3. Around the hop, decide which plot had enough observed cycles to distinguish
   an 18 Hz separation.

Failure interpretation: padding created more samples of a broad curve, not a
narrower curve. The display looks smoother but contains no additional
short-window information.

Recovery: judge frequency visibility from the window duration/response and
physical separation, then use zero-padding only when a denser display or peak
interpolation is useful.

## Concept connection

- P11 supplies `f_k = k*fs/M`.
- P12 explains why the Hann window broadens a tone while reducing distant
  leakage.
- P13 warns that zero-padding changes the grid but not finite-record resolution.
- P14 shows that overlap reuses data and produces correlated estimates.
- P74 will interpret time-varying Doppler using the same STFT choices.

## Safe rerun, cancellation, recovery, and rollback

All loops and arrays have fixed ceilings. Press Ctrl+C to cancel; there is no
background task or partial output file. Correct malformed values and rerun from
the top. The rerun removes old P15-tagged figures and clears old `results` before
validation; after valid controls, the private stream reconstructs the same noise.
To roll back, remove only P15-owned content/tests/evidence
and restore only its manifest status to `scaffolded`; preserve P14 and ignored
`.learning/` state.

## Completion handoff

Use `checks.md`. Then give a two- or three-sentence teach-back that chooses one
window for transient timing and one for close-frequency visibility, and explains
why overlap cannot make both arbitrarily precise.
