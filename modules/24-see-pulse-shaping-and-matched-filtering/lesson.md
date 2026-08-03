# P24 Lesson: See Pulse Shaping and Matched Filtering

## Guiding question

Why are symbols filtered before transmission and again at reception?

## Physical model

A QPSK symbol is one desired I/Q point per symbol interval. A transmitter
cannot send isolated mathematical points, so it launches a pulse for every
symbol. Those shifted pulses add to make a continuous complex-envelope
waveform. Pulse shaping chooses how that waveform occupies time and frequency.

A rectangular pulse changes abruptly at symbol boundaries. It is compact in
time, but its sinc-shaped spectrum has slowly decaying sidelobes. A
root-raised-cosine (RRC) pulse spreads smoothly across several symbols. Its
roll-off parameter trades occupied bandwidth for a gentler time response.

The neighboring RRC pulses visibly overlap. Overlap is not automatically
intersymbol interference (ISI): what matters is the combined response at the
receiver's decision times.

## From symbols to a sampled waveform

For unit-energy QPSK symbols from P23,

\[
a_k = \frac{I_k+jQ_k}{\sqrt{2}}, \qquad I_k,Q_k\in\{-1,+1\}.
\]

Zero stuffing puts each symbol on a sample grid separated by `sps` samples.
Convolution with the transmit pulse produces

\[
s[n] = \sum_k a_k p[n-kN_s],
\]

where \(N_s\) is the samples per symbol. The script forms this sum with
explicit zero insertion and `conv`, so the waveform is not hidden inside a
modulator or resampler object.

## Why the receiver uses a matched filter

For a known finite pulse \(p[n]\), the matched filter is its conjugated,
time-reversed copy:

\[
h_\text{MF}[n] = p^*[L-1-n].
\]

At its peak, the filter output is an inner product between the received
samples and the known pulse. In white noise, the Cauchy-Schwarz inequality
shows that this choice maximizes output signal-to-noise ratio at that sample.
The filter does not remove noise; it adds pulse-aligned signal samples
coherently while unrelated noise adds incoherently.

For a real symmetric RRC pulse, transmit and receive taps look the same. Their
convolution is approximately a raised-cosine response. An ideal raised-cosine
response is zero at every nonzero integer symbol offset:

\[
(p*h_\text{MF})(mT)=0, \qquad m=\pm1,\pm2,\ldots
\]

and equals one at \(m=0\). Therefore overlapping pulses add correctly at the
symbol clock. The finite tap span in this experiment only approximates the
infinite response, so a small residual ISI remains.

## Timing is part of the receiver

Both FIR filters add group delay. With an RRC span of `span` symbols and
`sps` samples per symbol, each symmetric filter delays the pulse by
`span*sps/2` samples. The cascade delay is therefore `span*sps`. Sampling
before compensating this delay, or sampling halfway between symbol times,
mixes contributions from adjacent symbols. The eye closes and the
constellation spreads even without noise.

That is why matched filtering and timing must be discussed together. A matched
filter evaluated at the wrong time is not the maximum-SNR decision statistic.

## What the two sweeps isolate

### Roll-off beta

The roll-off sweep keeps span, symbols, sample rate, and diagnostic method
fixed. Small beta approaches the minimum Nyquist bandwidth but creates longer
time tails; truncating those tails at a fixed span can leave more residual
ISI. Large beta uses more excess bandwidth and gives a more time-localized
pulse. The experiment reports a discrete 99%-power bandwidth estimate in
units of symbol rate \(R_s\); it is not a regulatory occupied-bandwidth
measurement.

### Finite filter span

The span sweep fixes beta and changes only how much of the ideal RRC tail is
retained. A two-symbol filter is inexpensive but severely truncated. Longer
spans use more taps and delay, while better approximating the zero-ISI sampled
response. Longer is not a universal guarantee for every beta and metric, but
the controlled `[2 4 6 8]` sequence exposes the dominant truncation effect.

## Limiting cases and common mistakes

- Beta approaching zero minimizes ideal excess bandwidth, but the pulse tails
  become long; a short implementation can perform poorly.
- Beta equal to one uses the widest raised-cosine transition band in this
  family, not infinite bandwidth.
- A rectangular pulse can still give zero ISI at its ideal matched sample
  times in this simple channel. Its main visible cost here is spectral
  sidelobes, not an automatic decision error.
- RRC is not itself the Nyquist raised-cosine response. The transmit and
  matched receive RRC filters form that response together.
- A clean eye in a synthetic white-noise channel does not prove immunity to
  multipath, carrier error, clock drift, nonlinear hardware, or colored noise.
- EVM includes amplitude and phase displacement; SER counts only boundary
  crossings. EVM can worsen before any decision changes.

## DSP and radar connection

Communications receivers use pulse shaping to control spectral occupancy and
matched filters to create high-SNR symbol decisions. Radar receivers use the
same matched-filter operation to concentrate a known echo waveform into a
delay peak. Later pulse-compression modules add sidelobe and Doppler tradeoffs,
but the core operation is already visible here: correlate with the known
transmit pulse, compensate its delay, then interpret the correctly timed
sample.

## Prerequisite connection

[P23](../23-build-bpsk-and-qpsk-constellation-intuition/) supplied the QPSK
points and sign decision regions. P24 explains the sample-rate waveform and
receiver processing that must occur before one clean point per symbol reaches
those regions. P07's echo-addition view of convolution and P09's FIR delay
language are the other useful foundations.
