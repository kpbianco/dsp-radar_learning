# P32 lesson: Perform LFM Pulse Compression

Guiding question: **How can a long energetic pulse achieve short-pulse range resolution?**

## Physical model: label time inside the pulse

An unmodulated long pulse occupies a long interval in fast time. Two echoes
whose leading edges are close together overlap, so pulse duration alone would
suggest poor range resolution. An LFM pulse adds a steadily changing frequency
label across that interval. Early samples have one frequency, later samples
have another, and a receiver that knows the label sequence can align them.

The complex-baseband waveform in Figure 1 is

\[
s(t)=\exp\left(j\pi k(t-T/2)^2\right),\qquad k=\frac{B}{T},
\]

for \(0\le t<T\). Its instantaneous frequency is approximately
\(f_i(t)=k(t-T/2)\), sweeping from \(-B/2\) to \(+B/2\). The magnitude stays
constant: bandwidth is carried by phase rotation, not by a short amplitude
envelope.

## The matched filter performs coherent alignment

For sampled pulse `s[m]`, the matched filter is its conjugate time reverse,

\[
h[m]=s^*[N-1-m],\qquad y[n]=\sum_m x[m]h[n-m].
\]

The script evaluates that sum explicitly before cross-checking it with base
MATLAB `conv`. At the correct echo delay every LFM phase term unwinds and adds
in phase. At other delays the phase terms mostly cancel. Figure 2 shows the raw
echoes extending across about \(cT/2\) metres; Figure 3 shows their energy
concentrated into separate delay peaks.

The convolution peak contains the matched-filter delay \(N-1\). The range axis
therefore uses

\[
R[n]=\frac{c}{2F_s}\left(n-(N-1)\right).
\]

Failing to subtract that filter delay produces a deterministic range bias.

## Bandwidth sets width; duration carries energy

For an ideal rectangular LFM spectrum, the characteristic range scale is

\[
\Delta R\approx\frac{c}{2B}.
\]

The exact full -3 dB width depends on the sampled waveform and the rectangular
time gate, so the experiment reports both measured width and the nominal
`c/(2B)` scale. Figure 4 changes only `B`: larger bandwidth produces a narrower
compressed response while pulse duration and transmitted sample count stay
fixed.

Figure 5 changes only `T`. Compressed width stays nearly fixed because `B`
stays fixed, while the time-bandwidth product \(BT\) grows. At fixed peak
power, a longer pulse contains more energy. This is the central bargain: long
duration supplies energy and large bandwidth supplies delay resolution.

## Two gain conventions that must not be mixed

With complex white sample noise of variance \(\sigma^2\), a length-\(N\)
unit-amplitude matched filter has a coherent per-sample SNR gain of
\(N=F_sT\). Radar texts commonly quote pulse-compression gain \(BT\), which
references the input noise to the waveform's \(B\)-Hz receiver bandwidth:

\[
\frac{\mathrm{SNR}_{out}}{\mathrm{SNR}_{in,B\text{-Hz}}}
=F_sT\frac{B}{F_s}=BT.
\]

The baseline prints both numbers and labels the convention. The measured
processing gain uses a seeded noise-only matched-filter output and the same
`B`-Hz input convention. It is expected to be near, not exactly equal to,
\(10\log_{10}(BT)\) because it is one finite noise record.

## The mismatch limit

Figure 6 deliberately builds a replica with only `0.55B`. Its chirp rate no
longer matches the transmitted phase history, so the terms cannot align across
the whole pulse. Both traces use the recovered peak as their 0 dB reference, so
the mismatch's peak loss remains visible while its response spreads. Restoring
`fliplr(conj(transmit_chirp))` recovers the narrow response exactly. Doppler,
clock error, waveform distortion, and calibration error can cause related
mismatch in a real radar; they are outside this delay-only lesson.

## Assumptions and limiting cases

- Echoes are integer-sample delayed, zero extended, stationary, and point-like.
  There is no circular shift or wraparound.
- The model is complex baseband with a rectangular pulse gate and constant
  amplitude. It omits RF hardware, propagation loss, clutter, Doppler, and
  detection thresholds.
- `B` remains below Nyquist. Near Nyquist the sampled chirp and its response
  become sensitive to sampling margin.
- If `B` approaches zero, the waveform becomes an unmodulated long pulse and
  compression loses its narrow peak. If `T` shrinks toward `1/B`, the energy
  advantage approaches that of a short pulse.
- Rectangular LFM has sidelobes. They are normal matched-filter structure, not
  extra targets; P33 will show how windowing trades sidelobes against width and
  gain.
- The local -3 dB width is a waveform metric, not a declaration that every
  target pair in noise is resolved.

## Common interpretation mistakes

- A long raw envelope does **not** force poor resolution when its phase carries
  large bandwidth and the receiver uses the matching replica.
- Increasing duration at fixed bandwidth raises energy and `BT`; it does not
  substantially narrow the compressed mainlobe.
- Increasing sample rate alone does not create waveform bandwidth or physical
  resolution.
- `10*log10(Fs*T)` and `10*log10(B*T)` answer different input-SNR conventions.
- `20*log10` applies to magnitude ratios; `10*log10` applies to power and SNR
  ratios.
- A mismatched filter can shift as well as broaden the largest response; its
  largest sample is not automatically the true target delay.

## Dependencies and concept connection

P31 established that waveform bandwidth controls response width independently
of estimator accuracy. P32 uses that idea inside an energetic long waveform:
correlation converts an LFM phase history into a narrow range response. The
experiment requires base MATLAB only and no toolbox. P33 builds directly on
the visible sidelobes by asking how they can hide a weaker nearby target.

Completion means you can predict how bandwidth changes compressed width and
how time-bandwidth product changes gain.
