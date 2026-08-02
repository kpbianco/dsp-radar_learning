# Lesson: Compare Periodogram and Welch PSD Estimates

## Guiding question

Why does averaging make a noise spectrum easier to interpret?

## Physical mental model

Imagine photographing rough ocean water. One sharp photograph preserves small
spatial detail, but a single random arrangement of waves can make the average
surface hard to judge. Averaging several photographs suppresses the accidental
wave pattern and reveals the stable background—provided each photograph still
has enough spatial extent to show the feature you care about.

A periodogram is the spectral version of one photograph. Welch's method cuts
one record into several windowed views, estimates a PSD from each view, and
averages their **linear power densities**. Random peaks do not recur at the
same bins, while real tones do. The average therefore steadies the background,
but each shorter segment has less observation time and a broader spectral
response.

## From a finite record to a calibrated PSD

For a real segment `x[n]` of length `M` and window `w[n]`, the experiment first
forms

\[
X_w[k]=\sum_{n=0}^{M-1}x[n]w[n]e^{-j2\pi kn/M}.
\]

With window energy \(U=\sum_n w^2[n]\), the two-sided density is

\[
P_2[k]=\frac{|X_w[k]|^2}{f_s U}\quad[\mathrm{V^2/Hz}].
\]

For real data, negative-frequency power mirrors positive-frequency power. The
one-sided PSD keeps bins from DC through Nyquist, doubles the interior bins,
and leaves DC and Nyquist unchanged. Its integral obeys

\[
\sum_k P_1[k]\,\Delta f
=\frac{\sum_n|x[n]w[n]|^2}{\sum_n w^2[n]},
\qquad \Delta f=\frac{f_s}{M}.
\]

That identity is checked for the full-record periodogram and every baseline
segment. It also explains why coherent-gain normalization, appropriate for
tone amplitude, is not the PSD normalization: noise density uses window
energy.

## Periodogram and Welch are one family

The full-record periodogram uses one Hann-windowed segment with `M=N=4096`.
Welch uses `M=512`, a 256-sample hop, and 15 complete segments:

\[
\widehat P_{W}[k]=\frac{1}{K}\sum_{r=0}^{K-1}\widehat P_r[k].
\]

If `M=N`, then `K=1` and Welch reduces to the same single-window periodogram.
At the other limit, smaller `M` gives more segments and usually lower variance,
but \(\Delta f=f_s/M\) grows and the Hann main lobe broadens. Welch is not a
more correct spectrum; it is a different bias/variance and resolution choice.

## Segment length: the central tradeoff

At 1024 Hz sampling, the 1024-, 512-, and 256-sample cases have 1, 2, and 4 Hz
frequency spacing. With 50% overlap they provide 7, 15, and 31 averages. The
shorter cases show a steadier noise band, while the long case better preserves
the valley around the weak 172 Hz tone beside the strong 160 Hz tone.

The script also reports an approximate Hann main-lobe null-to-null width of
`4*fs/M`. It is a physical window-response scale, not a claim that bin spacing
alone decides whether arbitrary tones are resolvable. Tone strength, separation,
window sidelobes, and noise also matter.

## Overlap: coverage, correlation, and diminishing returns

At fixed `M=512`, changing overlap does not change segment duration, FFT
spacing, Hann response, or physical resolution. It changes which samples enter
neighboring estimates. The record produces 8, 15, and 29 segments at 0%, 50%,
and 75% overlap.

Overlapping windows share samples, so their periodograms are correlated. The
experiment computes a window-correlation approximation to an effective
independent-average count. It is intentionally smaller than raw `K` at high
overlap. Thus 29 overlapping views do not provide the variance reduction of 29
independent records, and overlap approaching 100% mostly adds redundant work.

## Why repeated seeds matter

One noise realization can make either estimator look unusually favorable. The
24-seed sweep keeps sample rate, tones, amplitudes, window, segmentation, and
probe frequency fixed. At a tone-free 360 Hz bin, it compares coefficient of
variation across realizations. The Welch probe values cluster more tightly,
making the variance claim an ensemble observation rather than a lucky plot.

## Broken interpretation and recovery

The broken case converts every segment PSD to dB and then averages those dB
values. Because logarithms are nonlinear,

\[
\frac{1}{K}\sum_r 10\log_{10}P_r
\;\le\;10\log_{10}\!\left(\frac{1}{K}\sum_r P_r\right).
\]

The left side is a geometric-mean display and biases the reported background
low. Recovery is simple: average `V^2/Hz` values first, then convert the one
final estimate to dB. Averaging complex FFT values would be wrong for a
different reason—their random phases can cancel even when power is present.

## Limiting cases

- `M=N`, no overlap: one Welch segment equals the matched-window periodogram;
  no variance reduction occurs.
- More independent segments: the white-noise estimate approaches its stable
  ensemble level, while random bin-to-bin fluctuation falls.
- Very short segments: the estimate can look beautifully smooth while nearby
  tones merge into one broad feature.
- Overlap fixed while `M` changes: resolution follows `M`, not the percentage
  label.
- Overlap approaches `M-1` samples: segment count and computation grow rapidly,
  but adjacent estimates are nearly repetitions.
- Noise RMS approaches zero: the random floor disappears, but the finite Hann
  response around each deterministic tone remains.
- DC or Nyquist energy: those one-sided bins must not be doubled.

## Radar connection and common mistakes

A radar Doppler dwell or range-processing record also has finite duration.
Welch averaging can stabilize a clutter or receiver-noise PSD used to judge a
weak return, but segments that are too short can blur closely spaced Dopplers
or ranges. Overlap can use the available dwell more evenly, yet it cannot
manufacture independent pulses or observation time.

Common mistakes are treating a periodogram as wrong because it is jagged,
calling every short-segment Welch plot higher resolution because it looks
smoother, counting overlapping segments as independent, normalizing noise PSD
by coherent gain, doubling DC or Nyquist, and averaging dB values instead of
linear power.

## Prerequisite and next connection

P11 provides the hertz-per-bin map. P12 explains why the Hann window broadens
tones while controlling sidelobes. P13 proves that a denser FFT grid is not
longer observation time. P15 will reuse segmentation for a spectrogram, where
the trade becomes frequency visibility versus time localization rather than
variance versus frequency resolution.
