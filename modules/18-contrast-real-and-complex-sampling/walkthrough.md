# P18 Walkthrough: Keep the Direction of Rotation

## Guiding question

Why can complex samples distinguish positive and negative frequencies?

Run `experiment.m` from the top with its visible controls unchanged. The script
uses paired deterministic noise so direction is the only baseline difference,
writes no files, and retains source-computed metrics in `results`.

## Baseline — one view at a time

1. Start with the first time-domain panel. Compare the real projections of the
   `+160 Hz` and `-160 Hz` complex tones. They lie on top of one another, and
   `results.real_projection_rmse_v` should be at numerical zero.
2. Move to the two I/Q panels. Follow time forward: `+160 Hz` turns
   counterclockwise and `-160 Hz` turns clockwise. Read the signed estimates in
   the titles before inspecting any spectrum.
3. Look at the Q-versus-time panel. Q changes sign between the paired cases;
   this is the coordinate that the real projection discarded.
4. Open the centered-spectrum figure. The complex cases have separate peaks at
   `+160` and `-160 Hz`. The real projection has mirrored lobes at both places.

Expected observation: the I waveform and real magnitude spectrum cannot choose
between the two candidates. Joint I/Q phase progression can.

## Downconversion comparison

The third figure places clean RF sides 160 Hz above and below a 600 Hz LO.

1. Inspect the upper-side complex result. The negative-exponent LO leaves a
   `+160 Hz` counterclockwise baseband phasor.
2. Inspect the lower-side complex result. The same LO leaves a `-160 Hz`
   clockwise phasor.
3. Inspect the real-mixer panel only after those two. The explicit cosine mixer
   and FIR produce nearly identical real beat waveforms for both RF sides.

Expected observation: complex downconversion retains which side of the LO the
signal occupied. Real downconversion creates an unsigned cosine beat after the
high-frequency sum term is removed.

## Sweep 1 — change only frequency-offset magnitude

The fourth figure holds sample rate, record, amplitude, phase, and every other
control fixed while `|f|` changes through 40, 160, and 400 Hz.

1. Predict which paired trajectory is counterclockwise in every panel.
2. Compare how much arc each case covers per sample.
3. Read `results.offset_sweep_positive_frequency_hz` and its negative partner.
4. Check `results.offset_sweep_real_rmse_v`: changing rotation speed does not
   make the two real projections distinguishable.

Physical connection: frequency magnitude is rotation speed; frequency sign is
rotation direction. A second coordinate is needed at every nonzero speed.

## Sweep 2 — change only sample rate

The fifth figure holds the analog tone at 160 Hz and duration at 0.5 s while
sample rate changes through 2048, 512, and 256 samples/s.

1. At 2048 and 512 samples/s, locate the peaks at `+160` and `-160 Hz`.
2. Before reading the 256 samples/s title, fold `+160 Hz` into
   `[-128, 128)` and predict its signed alias.
3. Confirm that the original `+160 Hz` samples now rotate as `-96 Hz`; the
   original `-160 Hz` samples rotate as `+96 Hz`.

Expected observation: I/Q distinguishes the two sampled rotations, but sample
rate still limits which analog frequency produced them. Complex sampling does
not repeal aliasing.

## Broken case — discard Q

The final figure intentionally projects both clean tones onto I before applying
the phase-increment estimator.

1. In the left panel, see both trajectories collapse onto the same horizontal
   line. Their waveform RMSE is zero.
2. Notice that the broken signed estimates both report zero rather than
   `+160/-160 Hz`. A real adjacent-sample product has no complex angle that can
   encode direction.
3. In the right panel, retain Q and recover the opposite circles and signed
   estimates.

Failure interpretation: the estimator did not need a different threshold. Its
input representation destroyed the required information. Taking absolute
frequency would conceal the ambiguity rather than repair it.

Recovery: preserve I and Q through acquisition and downconversion, use a signed
FFT axis or phase progression, and verify the receiver's LO/Doppler sign
convention against P17.

## Safe rerun, cancellation, recovery, and rollback

All loops and allocations have fixed ceilings. Ctrl+C stops the foreground
script; there is no timer, worker, partial file, or external state to clean up.
Cancellation after P18 cleanup begins can leave a partial P18 figure set and
empty/incomplete `results`; rerun from the top to recover. Invalid controls fail
before random draws, signal/FFT/FIR allocation, or replacement of prior P18
output. A valid rerun recreates the same noise from its private seed without
changing the global random stream and replaces only P18-tagged figures and
`results`.

Rollback removes only P18-owned artifacts, allowed P18/shared lifecycle tests,
allowed catalog edits, and P18 evidence, then restores only P18's manifest
status to `scaffolded`. Preserve implemented P17, all later canonical identities,
ignored `.learning/` state, and the operator-owned active-batch record.

## Completion handoff

Use `checks.md`, then give a two- or three-sentence teach-back that explains why
the real projections coincide, ties signed frequency to I/Q rotation, and
states what complex sampling can and cannot recover after aliasing.
