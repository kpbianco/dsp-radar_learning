# Checks

## Guiding question

How do ADC bit depth and full-scale range change the measurement?

## Observe

1. What are the baseline number of levels, LSB voltage, clipped-sample count,
   RMS error, and measured signal-to-error ratio?
2. Does every non-clipping baseline error stay inside half an LSB?
3. Which spectral plot is more spur-like, and which has the broader floor?
4. How do the 3-bit and 14-bit staircases differ at the same voltage scale?
5. Which broken-case samples lose the original peak shape?

## Predict, then verify

1. With a `+/-1 V` range, predict `Delta` for 3, 6, 10, and 14 bits before
   reading the printed values.
2. Hold the same 0.9 V peak sine and 8 bits fixed, then widen the ADC from
   `+/-1 V` to `+/-9 V`. Predict whether clipped-sample count, absolute LSB
   voltage, and measured SNR should increase, decrease, or stay approximately
   fixed.
3. Raise bit depth from 8 to 12 while an input still reaches 1.35 V against a
   `+/-1 V` range. Predict which part of the clipping failure remains.
4. Add triangular dither before quantization. Predict separately what happens
   to error correlation, spectral structure, and total RMS error.

## Interpret

- Explain why one more bit halves the voltage step without changing full scale.
- Distinguish a small non-clipping signal that wastes ADC codes from an
  over-range signal that loses its peaks.
- Explain why quantization error from a sine need not be white or independent.
- Explain why the ideal `6.02B + 1.76 dB` SQNR is a reference condition rather
  than a guaranteed result for every signal and record.
- State where dither is added, what problem it changes, and what noise-power
  trade it introduces.
- Explain why digital gain and more in-range bits cannot recover an already
  clipped waveform.
- Connect ADC range use to weak-target visibility beside strong radar clutter
  or leakage without calling bit depth radar range resolution.

## Failure classification

For each observation, identify the dominant mechanism and the appropriate
first recovery:

1. Error is bounded by half an LSB, but a small waveform uses very few codes.
2. Output peaks are flat, clipped-sample count is nonzero, and error exceeds
   half an LSB.
3. Error spectrum contains repeatable lines even though no sample clips.
4. Dithered error has a broader floor and slightly greater RMS power.

The intended classifications are poor full-scale utilization, overload
clipping, signal-correlated quantization error, and the deliberate dither
trade, respectively.

## Recovery check

Restore the committed controls from the walkthrough and confirm every
assertion passes. Verify that the baseline and utilization sweeps have zero
clipped samples, the bit-depth sweep has decreasing LSB and RMS error, and the
broken case has a nonzero clipped-sample count with error greater than any
non-clipping utilization case.

If a malformed control fails early, restore finite positive real amplitude,
frequency, sample rate, duration, and full-scale values; finite real phase;
integer bit depths from 2 through 16; an even coherent record of 16 through
16384 samples; and at most eight cases per sweep. These guards prevent invalid
code counts, ambiguous spectra, excessive allocation, and indexing failures.

Then state the system recovery: remove overload by changing analog gain or
range before the ADC, preserve appropriate headroom, and use the remaining
range effectively. Do not describe post-ADC scaling as recovered resolution.

## Teach-back completion

In two or three sentences, answer:

**How do ADC bit depth and full-scale range change the measurement?**

A satisfactory answer:

- says `2^B` levels across `+/-V_FS` create step
  `Delta = 2*V_FS/2^B`;
- explains that more bits shrink in-range quantization error, while a signal
  using little range wastes effective resolution;
- distinguishes bounded in-range quantization error from destructive clipping;
  and
- states that dither can decorrelate tonal error by trading it for a broader
  noise floor, not by repairing overload.
