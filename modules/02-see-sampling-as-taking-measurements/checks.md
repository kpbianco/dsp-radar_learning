# Checks

## Guiding question

What information is lost when a continuous-looking signal is represented by discrete samples?

## Observe

1. In the baseline figure, what information is attached to each stem?
2. Which curve represents known synthetic ground truth, and which curve is a
   piecewise-linear assumption?
3. What printed metric states how many measurements describe one cycle?
4. At which sweep rate does the 7 Hz tone first exceed the Nyquist limit?

## Predict, then verify

1. Before changing `fs_baseline` from 80 to 40 samples/s, predict the new
   samples/cycle value and whether the continuous source frequency changes.
2. At 16 samples/s, predict whether shifting the clock by half a sample changes
   the source waveform, the measured values, both, or neither.
3. For `f0 = 7` Hz and `fs_bad = 12` samples/s, predict the reflected
   low-frequency candidate and its phase sign.
4. If the original frequency increases from 7 to 19 Hz while `fs_bad` stays at
   12 samples/s, predict whether the stored broken-case sequence changes.

## Interpret

- Explain why a plotted line through sample markers is not itself a
  measurement.
- Explain why a rate just above twice the tone can satisfy the ideal
  bandlimited condition while piecewise-linear interpolation remains visibly
  inaccurate.
- Explain the role of an analog anti-alias filter before a radar ADC.
- In the broken case, explain why 5, 7, and 19 Hz continuous sinusoids agree at
  every sample yet disagree between samples.
- Connect fast-time ADC sampling to slow-time pulse-to-pulse Doppler sampling.

## Recovery check

Restore the committed controls and confirm every assertion passes. If a guard
fails, use its message to restore finite real scalar controls, integer record
sizes, the 20001-point dense-reference ceiling, and the 5000-measurement
ceiling, with exactly three rate cases and no more than 12 clock-offset cases.
Keep baseline and offset rates above `2*f0`; keep the intentionally broken rate
between `f0` and `2*f0`; and keep the dense display rate above twice the highest
broken-case candidate, `f0 + fs_bad`.

Then describe the non-destructive recovery from alias ambiguity: restrict the
analog input bandwidth below Nyquist and resample at a sufficient rate. No
choice of interpolation can recover information that the measurements never
distinguished.

## Teach-back completion

In two or three sentences, answer:

**What information is lost when a continuous-looking signal is represented by discrete samples?**

A satisfactory answer:

- says samples retain amplitudes at known measurement instants, not the path
  between them;
- identifies interpolation as a model rather than new measured information;
- relates unique bandlimited reconstruction to a sample rate strictly above
  twice the highest admitted frequency; and
- uses the 5, 7, and 19 Hz broken case to explain how two or more different
  continuous signals can produce the same sample sequence.
