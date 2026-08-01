# Lesson: An ADC Measures with Finite Voltage Bins

## Guiding question

How do ADC bit depth and full-scale range change the measurement?

## Physical model

P02 treated samples as measurements taken at discrete times, and P03 showed
that the timing choice can make frequencies ambiguous. P04 keeps those sample
times fixed and asks a different question: how precisely can each stored
sample describe voltage?

Imagine a ruler whose marks are voltage bins. More ADC bits add more marks
inside the same input range. A wider full-scale range spaces the marks farther
apart. A signal that uses only a small part of the ruler touches few marks even
if many are available. A signal beyond the ruler is not measured more
coarsely—it is cut off at the end, which is clipping.

## The quantizer used in the experiment

The script defines a bipolar input range from `-V_FS` through `+V_FS`. With
`B` bits there are

\[
L=2^B
\]

reconstruction levels, and the voltage width of one least-significant bit is

\[
\Delta=\frac{2V_{FS}}{2^B}.
\]

This module uses a mid-rise quantizer. After limiting the input to the accepted
range, it computes

\[
c=\left\lfloor\frac{x+V_{FS}}{\Delta}\right\rfloor,
\qquad 0\le c\le L-1,
\]

and reconstructs the center of that bin:

\[
x_q=-V_{FS}+(c+\tfrac12)\Delta.
\]

The endpoints are input limits, not reconstruction levels. The outermost
reported values are half an LSB inside them. For every input that stays within
range, the error `e = x_q - x` is therefore bounded by approximately
`Delta/2`. The quantizer, saturation, and error calculations are explicit in
the script; no toolbox quantizer hides the operation.

## What bit depth changes

Increasing `B` by one doubles the number of levels and halves `Delta`. The
3-, 6-, 10-, and 14-bit sweep keeps the waveform and full-scale range fixed,
so its shrinking staircase and RMS error isolate resolution from every other
mechanism.

For an ideal, nearly full-scale sine with no overload and a suitably behaved
error, a common reference is

\[
\mathrm{SQNR}_{ideal}\approx 6.02B+1.76\ \mathrm{dB}.
\]

That is a limiting model, not a promise for every record. A coherent sine can
make quantization error repeat with the signal and appear as discrete spectral
spurs. The experiment prints measured signal-to-error ratio and labels the
formula as a reference so the two are not confused.

## What full-scale utilization changes

The 8-bit utilization sweep holds `B` and every sample of the 0.9 V peak
sinusoid fixed, then changes `V_FS` so that same input uses 90%, 25%, and 10% of
the available peak range. Widening the range from `+/-1 V` to `+/-3.6 V` and
`+/-9 V` makes `Delta` larger. The desired signal is unchanged, so the coarser
voltage bins directly reduce its signal-to-error ratio.

Reducing range utilization from fraction `r_1=A/V_{FS,1}` to
`r_2=A/V_{FS,2}` predicts roughly

\[
20\log_{10}(r_1/r_2)\ \mathrm{dB}
\]

of signal-to-error loss when the quantization-noise model is appropriate. It
also wastes about `log2(r_1/r_2)` effective amplitude bits. Changing receiver
gain before the ADC can improve range use, but only while peaks and unexpected
interference remain inside the accepted voltage range.

## Dither changes error structure

Undithered quantization error is amplitude dependent. It can repeat at
harmonics of a sine and sound or look tonal. The optional section adds the
difference of two seeded uniform sequences before quantization, producing
triangular probability density function (TPDF) dither from `-Delta` through
`+Delta`.

Dither makes code decisions less locked to the signal. In the spectrum, energy
that occupied repeatable spurs spreads into a broader floor. The trade is
additional total error power. Dither is not added after quantization, cannot
repair clipping, and is not a universal SNR improvement.

The spectrum uses the discrete Fourier transform

\[
E[k]=\sum_{n=0}^{N-1} e[n]e^{-j2\pi kn/N}.
\]

Base MATLAB `fft` evaluates this stated operation efficiently. The committed
tone completes an integer number of cycles in the record, so spectral leakage
does not masquerade as quantization structure. Magnitudes are one-sided and
referenced to `V_FS` in dBFS.

## Clipping is a different and worse failure

The broken case drives a 1.35 V peak sine into a `+/-1 V` ADC. Saturation
flattens each over-range peak. Its error is not bounded by half an LSB and does
not disappear when more code levels are added inside the same range. The
missing peak height was never recorded; downstream digital processing cannot
recover it.

Poor utilization and clipping point in opposite gain directions:

- too little signal uses too few codes and wastes effective resolution;
- too much signal reaches an endpoint and loses amplitude information.

The engineering task is to choose analog gain and full-scale margin so normal
signals use much of the converter without allowing expected peaks, clutter, or
interference to overload it.

## Limiting cases and interpretation boundaries

- **One more bit:** `Delta` halves for the same full-scale range, but analog
  noise, nonlinearity, clock jitter, and front-end distortion may prevent a
  real converter from gaining a full effective bit.
- **Signal near zero:** a mid-rise converter reports one of two bins around
  zero; there is no exact zero reconstruction level. Another documented
  quantizer convention can choose differently, but its equation and step must
  remain internally consistent.
- **Exactly at an input endpoint:** the value is accepted and reconstructed at
  the center of the outer bin, half an LSB inward. Beyond the endpoint is
  overload.
- **Very small signal:** increasing digital gain afterward magnifies the same
  quantized steps; it does not recreate discarded voltage detail.
- **More bits during overload:** smaller in-range steps do not restore clipped
  peaks. Increase `V_FS`, reduce analog gain, or prevent the large input.
- **Dithered signal:** the error can become less correlated while its RMS value
  rises. Judge structure and power separately.

## Why radar engineers care

A radar ADC may need to preserve a weak target while a strong close return,
clutter component, leakage path, or interferer occupies much more voltage.
Unused ADC range raises the quantization floor relative to the weak return;
overload creates harmonics and loses strong-signal shape. Neither bit depth nor
full-scale range is radar range resolution. They are parts of the receiver's
amplitude accuracy and dynamic-range budget.

## Dependency and compatibility boundary

This lesson depends on P03's correctly sampled sequence. It uses base MATLAB
only. The experiment has finite bounded loops, no helper functions, automatic
playback, external files, toolboxes, hardware, or network requests. It prepares
optional audio-preview vectors, but listening is explicitly learner-triggered
and is not part of automated validation.
