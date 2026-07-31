# Walkthrough

## Guiding question

What information is lost when a continuous-looking signal is represented by discrete samples?

Run `experiment.m` as one script, or run one `%%` section at a time after the
baseline controls exist. Keep all controls at their committed values first,
then change only the named variable.

## Baseline: separate the waveform from its measurements

Use the supplied 7 Hz cosine, 80 samples/s measurement rate, and one-second
record.

1. In the first panel, treat the dense curve as hidden ground truth. The stems
   are the only ADC-like measurements.
2. In the second panel, notice that the stored sequence has an integer sample
   index and amplitude, not a continuous time axis.
3. Compare the reference and the explicit piecewise-linear guess. Both pass
   through the samples; only one is the synthetic source equation.
4. Read the metrics. Expect 80 measurements, about 11.43 samples/cycle, a
   40 Hz Nyquist limit, and measurement-equation error near roundoff.

**One observation question:** In the interpolation figure, which parts came
from measurements and which parts were supplied by a drawing rule?

Expected observation: only the marked values and their times were measured.
Every line segment between them was added by the signal model or interpolator.

## Sweep 1: change only the measurement rate

Run the rate sweep `[80 16 12]` samples/s while keeping the 7 Hz signal fixed.

- At 80 samples/s, expect 11.43 samples/cycle and a close linear guess.
- At 16 samples/s, expect about 2.29 samples/cycle. This is above the 14
  samples/s strict threshold, but the straight segments visibly miss the
  curved peaks.
- At 12 samples/s, the 6 Hz Nyquist limit is below the 7 Hz source. Do not use
  the plausible line as evidence that the source was low frequency.

Physical connection: an ADC rate is meaningful together with the input
bandwidth. An analog anti-alias filter enforces that bandwidth before sampling.

## Sweep 2: shift only the measurement clock

Keep the rate at 16 samples/s and compare offsets of `0`, `0.25`, and `0.50`
sample intervals.

- The continuous source and sample rate remain unchanged.
- The stems move to different phases of the sinusoid, so the measured values
  and the linear-interpolation error change.
- None of the three sequences contains the unmeasured path between its stems.

Expected observation: a rate barely above twice the tone frequency can give
very different-looking sample patterns when the measurement clock shifts.
This does not contradict the ideal sampling theorem; that theorem assumes a
known band limit and an ideal reconstruction, not straight-line drawing.

Radar connection: changing ADC clock phase changes fast-time sample locations.
Changing the pulse timing similarly changes where slow-time Doppler phase is
measured.

## Broken case: several waveforms become one sequence

Run the deliberately broken section with `fs_bad = 12` samples/s.

The original 7 Hz waveform, a 5 Hz reflected candidate with phase `-phi`, and
a 19 Hz candidate all cross the same stems. The lower panel contains the only
stored sequence, so it cannot say which of those three continuous paths
occurred. Expect both printed sample-agreement errors to be near roundoff.

Common mistake: the 5 Hz curve is not a best-fit approximation. It is exactly
indistinguishable from the 7 Hz source at these measurement times.

## Recovery

Restore `fs_baseline = 80`, `sample_rates = [80 16 12]`, `fs_offset = 16`,
`sample_offset_fractions = [0 0.25 0.50]`, and `fs_bad = 12`, then rerun.
Every assertion should pass.

If a control assertion stops the script, restore finite positive real
amplitude, frequency, duration, and sample rates; a finite real phase; integer
record sizes; and the committed bounds of at most 20001 reference points, 5000
measurements per set, exactly three rate cases, and 12 clock-offset cases. The
baseline and offset rate must remain strictly above `2*f0`. The broken case
must keep `f0 < fs_bad < 2*f0`, and the display reference rate must remain
above `2*(f0 + fs_bad)`, so the documented alias relationship and every plotted
continuous candidate remain resolved.

To recover the broken case conceptually, raise the measurement rate and place
an analog low-pass filter before the sampler so input content is known to stay
below the new Nyquist frequency. Merely choosing a smoother line through the
same 12 samples/s sequence cannot recover which candidate generated it.

You are ready for the checks when you can identify measured facts versus
interpolation assumptions and can explain why distinct continuous sinusoids
produce exactly the same discrete sequence.
