# Walkthrough: Prove Zero-Padding Does Not Improve True Resolution

## Guiding question

Why does a smoother FFT plot not necessarily contain more information?

Run `experiment.m` section by section. Discuss one plot or processing change at
a time; the target is the physical distinction between interpolation and new
measurement time.

## Baseline: the same 128 samples on three grids

Use the defaults: `fs_hz=1024`, 128 short-record samples, equal complex tones
at 198 Hz and 202 Hz, and a private-seed noise record normalized to 0.002 V RMS
over its full 512 samples. The short case reuses the first 128 noise samples,
so its realized RMS is reported rather than forced to the full-record value.
Before viewing the spectra, make one prediction: will the 16x curve be
smoother, and will it show two physical peaks?

First inspect the time samples. All padding cases use this exact 0.125 s record;
no sample is regenerated. Then inspect the 1x, 4x, and 16x spectra.

- Grid spacing changes from 8 Hz to 2 Hz to 0.5 Hz.
- The original 128 DFT values are unchanged inside each padded result.
- The 4x and 16x curves expose the shape between coarse bins, but the nearby
  tones remain one blended short-record response.

The explicit finite-sum probe and the matching 16x FFT point confirm that the
dense FFT evaluates the same measured record rather than a new signal.

## Sweep 1: change only the zero-padding factor

Read the padding-invariant figure. The measured sample count stays 128, the
duration stays 0.125 s, the Rayleigh interval stays 8 Hz, and rectangular
null-to-null width stays 16 Hz. Only `N_fft` and `f_s/N_fft` change.

Expected observation: the display-spacing line falls by sixteen times while
the physical-resolution line is flat. The maximum mismatch at original DFT
bins remains at numerical roundoff. This is interpolation with a denser ruler.

## Sweep 2: change only measured observation length

Now use prefixes of one deterministic 512-sample record. The cases contain 128,
256, and 512 measured samples; they keep the sample rate, tone frequencies,
amplitudes, phases, rectangular window, dense display FFT, and corresponding
noise prefix fixed. Compare `results.observation_noise_rms_realized_v` to see
the small prefix-to-prefix RMS variation without rescaling any shared sample.

- At 128 samples, 4 Hz is only 0.5 Rayleigh interval and the midpoint near
  200 Hz is the top of one blended response.
- At 256 samples, separation reaches one Rayleigh interval and a strong
  midpoint valley appears.
- At 512 samples, separation is two Rayleigh intervals; two peaks sit near the
  true tones and the midpoint valley is deep.

This is the physical change: later nonzero samples add relative phase history
and narrow the rectangular response.

## Broken case: call display spacing true resolution

The broken report uses `1024/2048 = 0.5 Hz` and claims the short record resolves
the tones because 4 Hz spans eight plotted points. Compare that claim with the
16x short-record spectrum. It is smooth, but it is still a single blended
response.

Recover by reporting the short record's 8 Hz Rayleigh interval alongside the
0.5 Hz grid spacing. Then compare the genuinely long record: its 2 Hz Rayleigh
interval, not its plotting grid, makes the 4 Hz-separated tones visible.

## Concept connection and completion handoff

Translate this result to radar. More zero-padded Doppler cells interpolate one
coherent processing interval; a longer coherent interval improves physical
Doppler resolution. More zero-padded range cells interpolate one matched-filter
response; waveform bandwidth controls physical range resolution.

Before completion, explain whether padding can help peak estimation even though
it cannot separate an unresolved pair. A correct answer distinguishes easier
curve sampling from new independent information.

## Safe rerun, cancellation, recovery, and rollback

- All controls are validated before random data, signal vectors, FFT arrays, or
  figures are allocated. Fixed ceilings bound samples, FFT points, sweep cases,
  explicit sums, and figures.
- Press Ctrl+C to cancel. Rerun from the top: the private seed reproduces the
  longest record, shorter cases reuse prefixes, no files need cleanup, and only
  figures tagged `P13` are replaced.
- Nonfinite or complex controls, unsupported padding factors, nonincreasing
  observation multipliers, tones at/above Nyquist, excessive resources, or a
  setup that does not cross the short/long resolution boundary fails early.
- Rollback removes only P13-owned module, test, catalog, and evidence changes
  and restores only P13 to `scaffolded`; P12 and ignored learner state remain.

## Expected final explanation

You should be able to say: zero-padding reduces the plotted grid spacing by
evaluating the same finite-record transform at more frequencies, so it makes a
smoother curve without narrowing the true main lobe. At fixed sample rate,
collecting more measured samples increases observation time, reduces the
`1/T` resolution scale, and can separate tones that the short record blends.
