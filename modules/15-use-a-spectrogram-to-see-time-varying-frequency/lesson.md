# P15 Lesson: Time and Frequency Share One Window

## Guiding question

How do window duration and overlap control time-frequency visibility?

## Physical mental model

Imagine sliding a short listening gate across the record. At each position you
ask, “Which sinusoidal patterns fit inside this gate?” The resulting spectrum is
one vertical spectrogram column. Sliding the gate creates the time axis.

A short gate changes position quickly and can say *when* a burst or hop occurred,
but it has observed only a few cycles. A long gate observes many cycles and can
distinguish nearby frequencies, but one column then summarizes a longer span of
time. This is the time-frequency uncertainty tradeoff in operational form.

## The explicit STFT operation

For frame `r`, window length `M`, and hop `H`, the script computes

\[
X_r[k] = \sum_{m=0}^{M-1} x[rH+m]w[m]e^{-j2\pi km/M}.
\]

The timestamp is the window center,

\[
t_r = \frac{rH+(M-1)/2}{f_s},
\]

not the frame start. The script scales each FFT as a one-sided PSD:

\[
P_r[k] = \frac{|X_r[k]|^2}{f_s\sum_m w^2[m]}
\quad \text{V}^2/\text{Hz},
\]

then doubles only interior positive-frequency bins. This is the same finite
record FFT from P11-P14, repeated at controlled positions. No spectrogram
convenience function hides frame extraction or scaling.

## What window duration controls

With sample rate `fs`, the FFT grid spacing for an unpadded `M`-sample frame is
`fs/M`. The symmetric Hann response has an approximate null-to-null main-lobe
width of `4*fs/M`. That width, rather than the pixel spacing alone, is the useful
scale for deciding whether close components can appear separately.

The P15 156-to-174 Hz hop spans 18 Hz:

- `M = 512`: 500 ms duration, 2 Hz bins, about 8 Hz Hann width. A frame centered
  on the hop contains enough cycles to show energy near both frequencies, but it
  mixes roughly a quarter-second from either side of the transition.
- `M = 128`: 125 ms duration, 8 Hz bins, about 32 Hz Hann width. It follows the
  hop more closely but the two responses blend.
- `M = 64`: 62.5 ms duration, 16 Hz bins, about 64 Hz Hann width. It localizes
  the 64-sample burst and the hop best, while nearby frequencies are broad.

These scales are useful engineering guides, not a promise that every peak pair
at one-main-lobe separation will be detected in noise.

## What overlap controls

Overlap changes hop size `H = M - overlap_samples` and therefore the time-column
spacing `H/fs`. At `M = 128`, the 0%, 50%, and 75% cases step by 125, 62.5, and
31.25 ms. They all retain 8 Hz bin spacing and the same roughly 32 Hz Hann
response.

More overlap can place a window center closer to a short event. In this record,
the 380 Hz burst begins at a boundary of the 0%-overlap grid and occupies the
first half of one Hann window, where it is downweighted. The 75%-overlap grid
includes a centered view and reports a stronger burst column. That is improved
*sampling of time positions*, not improved window resolution or independent new
data.

## The broken zero-padding interpretation

The broken case takes the 64-sample window and requests a 512-point FFT. The
display grid becomes 2 Hz, exactly like an unpadded 512-sample FFT, but the data
still span only 62.5 ms. The Hann response remains about 64 Hz wide, so the 18 Hz
hop separation is not physically resolved. Zero-padding interpolates the same
short-window spectrum; it does not observe more cycles. P13 established the
same distinction for one record, and P15 applies it to every time frame.

## Limiting cases

- As `M` approaches the full record, the spectrogram approaches one detailed
  spectrum with almost no transition timing.
- As `M` becomes very short, the columns follow rapid changes but tones spread
  across frequency.
- As overlap approaches 100%, plots become densely sampled and expensive while
  adjacent columns become highly redundant. Frequency response does not improve.
- At 0% overlap, work is small and columns are less redundant, but a short event
  can fall between useful window centers.
- More zero-padding approaches a smooth interpolation of the same window
  response; its true width stays fixed.

## Radar connection

A radar dwell often contains time-varying Doppler: an accelerating target, a
rotating blade, a vibrating structure, or a target that changes motion. A short
STFT window tracks fast Doppler changes but broadens velocity response. A long
window estimates a steadier Doppler more sharply but smears maneuvers. Overlap
controls how often the processor reports a view, with corresponding compute and
correlation costs. Module P74 will use this exact foundation for micro-Doppler.

## Common interpretation mistakes

- Calling FFT-bin spacing the same thing as physical resolution.
- Saying overlap improves frequency resolution; window duration controls the
  window response.
- Reading a long-window column as an instantaneous measurement at its center.
- Timestamping a frame at its first sample and shifting every event early.
- Treating adjacent high-overlap columns as independent observations.
- Reading low burst power at a Hann boundary as proof that no burst occurred.

## Safe execution boundary

The script uses finite loops, fixed storage ceilings, a private seed, and tagged
figures. It writes no files and does not alter the global random stream. Press
Ctrl+C to cancel and rerun from the top. A malformed control fails before random,
signal, FFT, spectrogram-matrix, or figure allocation. Each rerun first removes
prior P15-tagged figures and clears prior `results`, so a rejected input cannot
be confused with an older successful output. Rollback restores only P15's
manifest status to `scaffolded`; P14 and learner progress remain intact.
