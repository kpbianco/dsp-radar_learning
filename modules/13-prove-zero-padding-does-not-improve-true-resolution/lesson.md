# Lesson: Prove Zero-Padding Does Not Improve True Resolution

## Guiding question

Why does a smoother FFT plot not necessarily contain more information?

## Physical mental model

Imagine taking 128 measurements, placing them on a table, and then inserting
blank cards after the last measurement. The extra cards let you draw a smoother
curve through the spectral values, but they contain no new measurements. A
longer observation is different: it places more cards containing actual signal
values on the table. Those later samples reveal more relative phase evolution
between nearby tones.

In a radar range or Doppler FFT, zero-padding is a finer display ruler. More
waveform bandwidth or coherent observation time changes the physical response;
more zeros do not.

## One finite record, many display grids

For measured samples `x[n]`, `0 <= n < N`, the finite-record transform at any
frequency is

\[
X(f)=\sum_{n=0}^{N-1}x[n]e^{-j2\pi fn/f_s}.
\]

An `N_fft`-point FFT samples this same expression at

\[
f_k=k\frac{f_s}{N_{\mathrm{fft}}}.
\]

When `N_fft > N`, MATLAB appends zeros before evaluating those additional
frequency points. The display spacing is `f_s/N_fft`, but the independent
sample count remains `N` and the observed duration remains `T=N/f_s`.
Every original `N`-point DFT value is still present at every padding factor;
the padded FFT only inserts evaluations between them.

The experiment checks one dense-grid value with the explicit sum above before
using `fft`, and checks that the 1x DFT bins are identical inside every padded
spectrum.

## Resolution comes from observation time

For a rectangular observation, one tone has its first spectral nulls about
`1/T` hertz to either side of its frequency. The null-to-null main-lobe width
is therefore about

\[
B_{\mathrm{main}}=\frac{2}{T}=\frac{2f_s}{N}.
\]

The Rayleigh interval `1/T = f_s/N` is a useful resolution scale. It depends on
the number of measured samples, not the number of displayed FFT points. In the
baseline:

- 128 samples at 1024 samples/s give `T=0.125 s`, an 8 Hz Rayleigh interval,
  and a 16 Hz null-to-null rectangular main lobe;
- 16x padding changes display spacing from 8 Hz to 0.5 Hz, but all three
  physical quantities above stay fixed;
- 512 measured samples give `T=0.5 s`, a 2 Hz Rayleigh interval, and a 4 Hz
  null-to-null main lobe.

Windowing changes the main-lobe and sidelobe constants, as P12 showed, but no
window or padding factor creates observation time.

## Two close tones expose the distinction

The tones are at 198 Hz and 202 Hz, separated by 4 Hz. The 128-sample record
sees only half a Rayleigh interval between them. Its dense 16x plot shows one
smooth blended response centered near 200 Hz. A smoother blend is still a
blend.

The 512-sample record observes two Rayleigh intervals of separation. Relative
phase accumulates for four times as long, the individual main lobes narrow, and
two peaks with a deep midpoint valley become visible. The new separability came
from 384 additional nonzero measurements, not from grid interpolation.

## What zero-padding can improve

Zero-padding is useful. A denser grid can reduce the quantization of a
grid-based peak-location estimate, make lobe shapes legible, align displays,
and support interpolation after the information-bearing measurement. Those
are display or estimation conveniences. They must not be described as narrower
physical main lobes or new ability to distinguish overlapping signals.

## Broken interpretation and recovery

The broken case reports `f_s/N_fft = 0.5 Hz` for the 16x FFT and calls it true
resolution. That would predict that the 4 Hz-separated tones are eight
"resolution cells" apart. Yet the plotted short record still has one blended
peak because its true observation scale is `f_s/N = 8 Hz`.

Recovery labels the two quantities separately:

- **display-grid spacing:** `f_s/N_fft`, which padding can reduce;
- **finite-record Rayleigh interval:** `f_s/N`, which only more measured time
  reduces at fixed sample rate.

## Limiting cases

- **Padding tends to infinity with fixed `N`:** the plotted curve approaches a
  continuous-looking interpolation of the same finite transform; its physical
  main lobe does not shrink.
- **Measured duration grows with fixed `f_s`:** `1/T` decreases and nearby tone
  phase histories become distinguishable.
- **The tones coincide:** no amount of padding or observation time turns one
  frequency into two; they are the same component.
- **Tone separation is far above `1/T`:** even a coarse FFT grid may sample the
  two responses awkwardly, while padding makes their already-present
  separation easier to display.
- **Noise increases:** longer coherent observation can improve measurement, but
  zero-padding still adds no independent noise or signal samples.

## Radar connection and common interpretation mistakes

Range zero-padding creates more plotted range bins but does not beat the
waveform-bandwidth limit. Doppler zero-padding creates more velocity grid
points but does not beat the coherent-processing-interval limit. It may improve
peak interpolation or map presentation, not true target separation.

Common mistakes are calling every FFT point an independent measurement,
equating `f_s/N_fft` with resolution after padding, judging resolution only by
curve smoothness, and comparing a padded short record with an unpadded long
record without separating display spacing from observation duration.

## Prerequisite and next connection

P11 established the FFT grid and P12 established finite-record main lobes. P14
will change the question from resolution to estimator variance by comparing a
single periodogram with averaged Welch segments.
