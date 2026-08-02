# Lesson: Separate Leakage from Noise

## Guiding question

Why does a perfectly clean tone spread across many FFT bins?

## Physical mental model

Imagine recording a continuously rotating phasor for exactly 128 samples, then
taping copies of that short recording end to end. The DFT analyzes those
periodic copies. If the phasor completes an integer number of turns in the
record, the end joins the beginning smoothly. If it completes 17.35 turns, the
periodic copy jumps at the join. Many DFT sinusoids are needed to represent
that artificial boundary, even though the original tone is perfectly clean.

That repeatable, tone-shaped spreading is **spectral leakage**. Noise is a
random process whose particular bin values change with the realization. A
single magnitude spectrum can contain both, so "not in the peak bin" does not
mean "noise."

## Finite observation creates the spectral shape

For a complex tone

\[
x[n]=A e^{j(2\pi f_0 n/f_s+\phi)},\qquad 0\le n<N,
\]

the finite record is the continuing tone multiplied by a window `w[n]`. Its
DFT at bin `k` is

\[
X_w[k]=\sum_{n=0}^{N-1}x[n]w[n]e^{-j2\pi kn/N}.
\]

Multiplication by `w[n]` in time shifts and sums the window's spectrum around
the tone frequency. A rectangular window has an abrupt edge, so its shifted
response has a narrow main lobe but sidelobes that fall slowly. Tapered windows
soften the record edges and lower sidelobes, but their wider main lobes blend
nearby frequencies more readily.

The script uses a complex tone so one positive-frequency response can be read
without the mirrored negative-frequency component of a real cosine. The same
finite-record leakage mechanism applies to a real sinusoid.

## Three metrics answer three different questions

Before comparing amplitude, the script divides by each window's coherent gain

\[
G_c=\frac{1}{N}\sum_{n=0}^{N-1}w[n].
\]

That corrects the response to an exact-bin tone. The remaining window metrics
have different physical meanings:

- **-3 dB main-lobe width (Hz or bins):** how closely two comparable tones can
  sit before their peaks blend. Narrower favors resolving neighbors.
- **Maximum sidelobe level (dBc):** how far a strong tone's deterministic
  skirt reaches above a weak nearby tone. More negative favors high dynamic
  range.
- **Peak amplitude error (dB):** how much the largest sampled response changes
  as a tone moves between bins. Flat-top weighting favors amplitude
  measurement by keeping its top broad, at the cost of a very wide main lobe.

The dense FFT in the plots samples the same finite-record transform more
finely. It makes widths and sidelobes easier to measure; it does not create a
longer observation or improve true resolution.

## Window tradeoffs, not a universal winner

- **Rectangular:** narrowest main lobe, largest first sidelobe (about -13 dBc),
  and substantial off-bin peak loss.
- **Hann:** wider main lobe and much lower sidelobes; a useful general taper.
- **Hamming:** first sidelobe lower than Hann, although distant sidelobes fall
  differently.
- **Blackman:** still wider main lobe with substantially suppressed sidelobes.
- **Flat-top:** widest main lobe, extremely low sidelobes, and the smallest
  off-bin peak-amplitude error in this comparison.

The correct choice follows the measurement: rectangular can separate close
similar-strength tones; Blackman can expose a weak neighbor beside a strong
one; flat-top can measure a single tone's amplitude accurately.

## Leakage and noise behave differently

For fixed tone frequency, phase, record, and window, clean-tone leakage repeats
exactly. Seeded noise adds irregular bin-to-bin variation and a broadband
floor. Changing the window reshapes the deterministic leakage pattern and also
changes the noise bandwidth, so a lower-looking floor is not automatically a
lower input noise power.

The broken estimator removes only the strongest rectangular-window bin and
calls every other bin noise. Parseval scaling makes the calculation look
reasonable, but the noiseless off-bin tone still has substantial deterministic
energy in those bins. In this synthetic lab the recovery subtracts the known
clean tone, leaving the exact injected noise. With measured data, use knowledge
of tone placement and window response, repeated records or averaging, and
guarded noise regions rather than blindly labeling all nonpeak energy.

## Limiting cases

- **Exact-bin tone plus rectangular window:** the periodic join is continuous,
  and an ideal complex tone occupies one DFT bin to numerical precision.
- **Half-bin tone:** no single DFT basis matches it; a rectangular window puts
  substantial energy in both nearest bins and many sidelobes.
- **Longer record at fixed sample rate:** bin spacing `f_s/N` shrinks and the
  physical main lobe narrows, because observation time—not zero-padding—grew.
- **Noise RMS approaches zero:** the structured leakage stays. This proves
  leakage does not require noise.
- **Tone becomes coherent:** rectangular leakage collapses, but a tapered
  window still deliberately spreads the tone according to its own response.

## Radar connection and common interpretation mistakes

Range and Doppler FFTs also process finite records. Strong clutter or a strong
target can leak through sidelobes and hide a weak nearby return. A narrow
main-lobe window helps separate close targets of similar strength; a
low-sidelobe window helps reveal a weak target near a strong one; amplitude
calibration requires coherent-gain awareness.

Common mistakes are calling every skirt a noise floor, believing a taper
removes leakage rather than reshaping it, comparing uncorrected window peaks,
and treating the dense plotted grid as better physical resolution. The plots
and metrics separate those mechanisms explicitly.

## Prerequisite and next connection

P11 supplies the bin map, `f_s/N` spacing, and exact-bin versus fractional-bin
placement used here. P13 uses the dense display-grid observation to prove why
zero-padding makes a spectrum smoother without adding independent information.
