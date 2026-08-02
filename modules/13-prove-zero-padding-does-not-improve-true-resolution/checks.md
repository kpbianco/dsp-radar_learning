# Checks: Prove Zero-Padding Does Not Improve True Resolution

## Guiding question

Why does a smoother FFT plot not necessarily contain more information?

Use the figures and retained `results` fields. These are observation,
prediction, and interpretation checks, not a MATLAB-syntax quiz.

## Baseline observation checks

1. Verify the short record contains 128 measured samples over 0.125 s and has
   `results.short_rayleigh_hz = 8` Hz.
2. Verify padding factors `[1 4 16]` produce display spacings `[8 2 0.5]` Hz
   while every `results.padding_rayleigh_hz` value stays 8 Hz.
3. Confirm `results.original_grid_error_v` stays near numerical roundoff: the
   original DFT bins are embedded unchanged in every padded spectrum.
4. Compare the explicit finite-sum probe with the 16x FFT value. Why is their
   agreement evidence of denser evaluation rather than extra measurement?
5. Inspect `results.observation_noise_rms_realized_v`. Why is exactly 0.002 V
   guaranteed only for the full 512-sample noise record, while preserving the
   128/256 prefixes is more important than renormalizing each sweep case?

## Predict, then verify

1. **Padding prediction:** if padding increases beyond 16x while `N=128`,
   predict display spacing, Rayleigh interval, and physical main-lobe width.
   Which quantities approach zero, and which remain fixed?
2. **Observation prediction:** before reading the observation-length figure,
   predict whether 4 Hz-separated tones are visible at 128 and 512 samples.
   Verify using `results.separation_rayleigh_ratio` and
   `results.midpoint_to_tone_level_db`.
3. **Sample-rate prediction:** if `f_s` doubles while the sample count remains
   128, predict both duration and Rayleigh interval. Explain why more samples
   per second are not automatically more observation time.

## Interpretation checks

1. Why is `f_s/N_fft` a display-grid spacing but `f_s/N` an observation scale
   when the FFT input contains only `N` nonzero measured samples?
2. Does a smooth 16x spectrum contain sixteen times as many independent
   measurements? No. It contains deterministic interpolated evaluations of the
   same 128-sample finite sum.
3. Can padding still improve a frequency estimate? It can reduce grid
   quantization or support interpolation for an already observable peak, but it
   does not create true two-signal resolving power.
4. In radar, distinguish zero-padded range/Doppler cells from physical range
   resolution (waveform bandwidth) and Doppler resolution (coherent time).
5. Why must comparisons state the window? A taper changes the main-lobe
   constant, although padding still cannot add information for any window.

## Failure classification

The broken report says the 16x short-record resolution is 0.5 Hz and therefore
the tones are eight resolution cells apart.

- The arithmetic `f_s/N_fft = 0.5 Hz` is correct.
- The failure is classification: that number is grid spacing, not true
  resolving power for 128 measured samples.
- Recovery reports the unchanged 8 Hz short-record Rayleigh interval and then
  uses 512 measured samples to reduce it to 2 Hz.
- Verify the short midpoint-to-tone level is above 0 dB (one central blend)
  while the longest-record midpoint is below -20 dB (two separated peaks).

Also classify malformed edits: a boolean/noninteger sample count, nonfinite or
complex values, a padding list other than `[1 4 16]`, duplicate/decreasing
observation multipliers, an FFT above 8192 points, tones outside `(0,f_s/2)`,
or parameters that no longer put the pair below short-record and above
long-record resolution. Each must stop before random, FFT, or figure allocation.

## Recovery, isolation, compatibility, and resource bounds

- Cancellation is Ctrl+C followed by deterministic rerun; there is no wait,
  asynchronous task, unbounded loop, or partial file output to recover.
- A private stream and prefix reuse isolate repeatability from MATLAB's global
  random state. Figures are isolated by tag `P13`.
- Base MATLAB operations expose signal formation, the finite sum, zero-padding,
  FFT normalization, and the midpoint metric; no spectral-estimator toolbox is
  required.
- Fixed ceilings bound the longest record, FFT, sweep cases, explicit terms,
  and four figure groups.

## Teach-back completion

In two or three sentences, answer the guiding question and contrast the 16x
short record with the four-times-longer record. Then give one radar example in
which zero-padding helps presentation or estimation without changing physical
resolution.

A complete teach-back includes:

- display spacing `f_s/N_fft` versus observation scale `1/T=f_s/N`;
- the same-samples interpolation argument;
- the short blended pair and long separated pair;
- one legitimate use of padding;
- one range or Doppler connection.

Do not record learner completion until the baseline, both one-variable sweeps,
the broken classification, recovery, and teach-back have been observed.
