# Checks: Compare Periodogram and Welch PSD Estimates

## Guiding question

Why does averaging make a noise spectrum easier to interpret?

Use the figures and retained `results` fields. These checks test observation,
prediction, and interpretation—not MATLAB syntax.

## Baseline observation checks

1. Verify `results.record_duration_s` is 4 s,
   `results.periodogram_bin_spacing_hz` is 0.25 Hz, and
   `results.welch_bin_spacing_hz` is 2 Hz.
2. Confirm `results.baseline_segment_count` is 15 and the two one-sided power
   errors are below the stated numerical tolerance.
3. Compare `periodogram_noise_cv` with `welch_noise_cv`, then compare the dB
   ripple metrics. Point to the steadier tone-free background without calling
   it finer resolution.
4. Locate the 160 and 172 Hz tones and explain why weak-tone height alone does
   not measure the estimator's frequency resolution.

## Predict, then verify

1. **Segment-length prediction:** before reading Sweep 1, predict what happens
   to bin spacing, number of averages, noise ripple, and weak-tone valley
   prominence when `M` falls from 1024 to 256. Verify all four retained arrays.
2. **Overlap prediction:** if overlap increases at fixed `M`, predict which of
   segment count, independent information, and frequency resolution can change.
   Verify that raw `K` grows, `K_eff` stays below it, and bin spacing remains 2
   Hz.
3. **New-seed prediction:** predict whether individual periodogram bins or
   Welch bins vary more across the 24 seeds. Verify the two probe CV values.
4. **No-noise limit:** if `noise_rms_v` approaches zero, predict which random
   fluctuation disappears and which Hann-shaped deterministic tone response
   remains. Explain before editing.

## Interpretation checks

1. Why is a periodogram jagged even when the underlying white-noise PSD is
   flat? Distinguish the process spectrum from one finite-record estimate.
2. Why must Welch average linear `V^2/Hz` rather than dB or complex FFT values?
3. Why does dividing by `fs_hz*sum(w.^2)` give a density, and why are only the
   interior one-sided bins doubled?
4. Is a 256-sample Welch estimate more resolving because it looks smoother?
   No: it has more averages but a shorter observation and broader Hann response.
5. Does 75% overlap create 29 independent records? Use the window-correlation
   metric and shared samples in your answer.
6. Choose a segment length for each case and justify the trade:
   - two close Doppler tones;
   - a broad noise-floor survey;
   - a weak isolated feature whose location is already known approximately.

## Failure classification and recovery

The broken case reports the mean of segment dB values below the dB of their
mean linear PSD.

- The individual segment PSDs and units are valid.
- The failure is applying a nonlinear display transform before averaging.
- Recovery averages linear power density first, then converts once to dB.
- `results.db_averaging_bias_db` must be nonnegative; the noise-band summary
  must show a positive recovered-minus-broken difference.

Also classify malformed edits: `NaN` or complex controls, a noninteger or odd
segment length, overlap outside `[0,1)`, overlap that makes no integer hop,
partial final segments, tone spacing that no longer crosses the long/short Hann
main-lobe boundary, duplicate seeds, a record or FFT above 4096, more than 32
segments, more than 24 seed trials, or changed canonical sweep lists. Each is
an input/resource-contract failure and must stop before random, FFT, or figure
allocation.

## Teach-back completion

In two or three sentences, answer the guiding question and choose `M` and
overlap for one DSP or radar measurement.

A complete teach-back includes:

- one finite-record periodogram versus an average of segment periodograms;
- linear `V^2/Hz` averaging and correct one-sided scaling;
- reduced variance versus lost segment-duration resolution;
- overlap correlation and diminishing returns;
- the broken dB-average classification and recovery;
- one physically justified choice for a weak spectral feature.

Do not record learner completion until the baseline, segment-length sweep,
overlap sweep, repeated-seed comparison, broken case, recovery, and teach-back
have been observed.
