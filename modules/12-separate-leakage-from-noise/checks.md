# Checks: Separate Leakage from Noise

## Guiding question

Why does a perfectly clean tone spread across many FFT bins?

Use the figures and retained `results` fields. These are observation and
interpretation checks, not a MATLAB-syntax quiz.

## Baseline observation checks

1. Verify `results.bin_spacing_hz` is 8 Hz and
   `results.tone_frequency_hz` is 138.8 Hz (17.35 bins).
2. Confirm the clean rectangular spectrum contains a structured skirt even
   though its input noise RMS is exactly zero.
3. Point to the difference between that repeatable skirt and the irregular
   floor added by the seeded 0.02 V RMS noise.
4. Explain why `results.record_wrap_jump_v` is evidence of a noncoherent
   finite record, not evidence of random noise.

## Predict, then verify

1. **Window prediction:** before reading the metric bars, predict which window
   gives the narrowest -3 dB main lobe, which most suppresses sidelobes, and
   which minimizes off-bin peak-amplitude error. Verify all three using
   `main_lobe_3db_width_hz`, `maximum_sidelobe_db_c`, and
   `peak_amplitude_error_db`.
2. **Offset prediction:** if `tone_bin_offset` becomes zero with a rectangular
   window, predict the boundary jump and off-peak energy fraction. Verify the
   first elements of `offset_wrap_jump_v` and
   `offset_off_peak_energy_fraction` approach numerical zero.
3. **Noise prediction:** if `noise_rms_v` is reduced while the tone and record
   stay fixed, predict which plotted structure remains and which floor moves.
   Explain before rerunning.

## Interpretation checks

1. Why does multiplying by a tapered window lower sidelobes but widen the main
   lobe? Tie the answer to the window spectrum, not to an `fft` option.
2. Why is coherent-gain division needed before comparing peak amplitude?
3. Does the 8192-point display FFT resolve two tones that the 128-sample record
   could not resolve? No: it samples the same finite-record transform more
   densely; observation time did not increase.
4. Select a window and justify it for each task:
   - two close, similar-strength tones;
   - one weak return beside a strong return;
   - accurate amplitude of one isolated tone.
5. In a Doppler spectrum, why might a stable skirt around strong clutter be
   leakage while a realization-varying broadband floor is noise?

## Failure classification

The broken estimate reports a large nonzero "noise RMS" for a perfectly clean
off-bin tone.

- The arithmetic is a valid off-peak energy calculation.
- The failure is the assumption that every nonpeak bin contains noise.
- Recovery in this controlled lab subtracts the known clean tone; the retained
  recovered RMS must equal the actual private-seed noise RMS.
- In measured data, name two safer tools: model/guard the window response,
  arrange coherent sampling when appropriate, or compare/average repeated
  records.

Also classify these malformed edits: nonfinite or complex controls, a record
above 512 samples, a dense FFT above 16384 points, nonincreasing offsets, or a
different window list. Each is an input-contract failure and must stop before
random, FFT, or figure allocation.

## Teach-back completion

In two or three sentences, answer the guiding question and distinguish leakage
from noise. Then name the three window tradeoff metrics and select a window for
one radar or DSP measurement goal.

A complete teach-back includes:

- finite observation/window multiplication as the cause;
- exact-bin and off-bin limiting behavior;
- deterministic leakage versus random noise;
- the main-lobe width, sidelobe level, and peak-amplitude tradeoff;
- one physically justified window choice.

Do not record learner completion until the baseline, both one-variable sweeps,
the broken classification, recovery, and teach-back have been observed.
