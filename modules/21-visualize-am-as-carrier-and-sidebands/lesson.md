# P21 Lesson — A Message Makes Translated Copies of Itself

## Guiding question

How does a baseband waveform create RF sidebands?

## Physical mental model

Imagine a fast carrier whose height is controlled by a slow message. The
message does not slide the carrier frequency back and forth. Instead it changes
the carrier amplitude. In frequency, that multiplication makes translated
copies of the message centered on the carrier. Each baseband component gets a
lower and an upper RF location.

P20 is the immediate prerequisite in the ordered curriculum. P11–P13 made FFT
frequency locations and finite records concrete, P16 built an analytic signal,
and P17 showed that multiplication by an oscillator translates spectra. P21
combines those ideas in conventional amplitude modulation.

## The transparent AM model

Let `m(t)` be a normalized real message with `|m(t)| <= 1`. Conventional AM is

\[
s(t)=A_c[1+\mu m(t)]\cos(2\pi f_c t),
\]

where `Ac` is carrier amplitude in volts, `fc` is carrier frequency in hertz,
and `mu` is dimensionless modulation depth. The bracketed quantity is the
**signed envelope**. Its sign matters even though a magnitude detector cannot
display that sign.

For the single-tone message `m(t)=cos(2*pi*fm*t)`, the product identity gives

\[
s(t)=A_c\cos(2\pi f_c t)
+\frac{A_c\mu}{2}\cos[2\pi(f_c+f_m)t]
+\frac{A_c\mu}{2}\cos[2\pi(f_c-f_m)t].
\]

The RF spectrum therefore has a carrier at `fc` and equal sidebands at
`fc-fm` and `fc+fm`. Each sideband's sinusoid amplitude is `Ac*mu/2`. This is
the visible cause and effect: baseband frequency becomes offset from the
carrier, and modulation depth becomes sideband amplitude.

## A multitone message makes more pairs

If the message is

\[
m(t)=a_1\cos(2\pi f_1t)+a_2\cos(2\pi f_2t),
\]

linearity gives sidebands at `fc +/- f1` and `fc +/- f2`. Their amplitudes are
`Ac*mu*a1/2` and `Ac*mu*a2/2`. The carrier remains at `fc` because the constant
`1` in the signed envelope remains present. For a general bandlimited real
message, the same rule creates mirrored spectral copies rather than just four
discrete lines.

The single-tone-to-multitone transition holds the carrier, modulation depth,
record, detector operations, and exact receiver-noise samples fixed. Only the
message content changes, so the new sideband pairs have one cause rather than a
depth or noise confound.

The script uses a coherent record: all displayed tones land on the explicit
FFT grid. That keeps leakage from hiding the mapping. A real measurement need
not be bin centered, so P12's leakage lesson still applies.

## Envelope detection is magnitude detection

P16 showed how a real waveform can be converted to an analytic signal by an
explicit FFT mask: preserve DC and Nyquist, double positive-frequency bins,
and remove negative-frequency bins. P21 performs that operation directly and
takes the magnitude:

\[
e_{\rm mag}(t)=|s_a(t)|=A_c|1+\mu m(t)|.
\]

When `0 <= mu <= 1` and `|m(t)| <= 1`, the signed envelope never goes negative.
Then the absolute value changes nothing, so subtracting `Ac` and dividing by
`Ac*mu` recovers the normalized message.

When `mu > 1`, the signed envelope crosses zero. The RF carrier reverses by
180 degrees during the negative intervals. Magnitude discards that sign and
folds those intervals upward. This is over-modulation distortion, not noise
and not an FFT artifact.

## Coherent detection retains sign

The coherent detector knows the carrier phase and multiplies by twice the same
cosine:

\[
2s(t)\cos(2\pi f_c t)
=A_c[1+\mu m(t)]\{1+\cos(4\pi f_c t)\}.
\]

An explicit low-pass mask removes the doubled-carrier term, leaving the signed
baseband `Ac[1+mu*m(t)]`. Subtracting the DC carrier level and dividing by
`Ac*mu` recovers `m(t)` even when the envelope is negative. Coherent recovery
requires a phase- and frequency-aligned reference; that extra knowledge is why
it can distinguish a negative envelope from a positive magnitude.

## What the sweeps isolate

The modulation-depth sweep changes only `mu`: the message, carrier, sample
rate, record, and detector operations remain fixed. The minimum signed envelope
falls from positive to zero at `mu=1`, then becomes negative. In the clean
cases the envelope-detector error stays near numerical precision through the
zero-touching limit, then rises sharply, while coherent recovery stays intact.

The message-frequency sweep changes only `fm`. The carrier remains `3000 Hz`
and depth remains `0.60`. Each measured sideband moves the same number of hertz
away from the carrier as the originating baseband tone. The sweep exposes a
location rule, not a bandwidth estimate or an FM effect.

## Limiting cases

- At `mu=0`, only the carrier remains; there are no message sidebands and
  division by `mu` cannot define a recovered normalized message.
- As `mu` increases below one, each sideband grows linearly as `Ac*mu/2`.
- At `mu=1`, a full-scale negative message just touches a zero envelope. Ideal
  noiseless magnitude recovery still works, but any channel or detector error
  is most exposed at that zero.
- Above `mu=1`, the transmitted AM waveform still contains the signed message,
  but envelope magnitude recovery folds it.
- At `fm=0`, the message changes the carrier amplitude/DC envelope rather than
  making a separated sideband pair.
- As `fm` approaches the carrier or Nyquist limits, sideband overlap and
  sampling constraints break the simple separated-line view.
- A complex or single-sideband modulator need not create symmetric copies;
  P21's symmetry follows from a real message multiplied by a real cosine.
- A constant carrier phase error scales the recovered baseband by the phase
  projection (and can reverse its sign), even though the separated
  doubled-carrier term is still removed. Carrier frequency error produces a
  time-varying beat instead of the intended stationary baseband.

## Radar connection

Radar transmitters and receivers often move signals between complex baseband,
IF, and RF by multiplication. A pulsed envelope, coded waveform, or small
amplitude fluctuation creates occupied spectrum around a carrier just as this
message does. In a receiver, coherent I/Q processing preserves phase and sign,
which is essential when envelope-only processing would lose information. P21
is not an operational radar waveform validation; it is the translation model
that later radar modules build on.

## Common interpretation mistakes

- Saying the message energy moves to the carrier and disappears from baseband;
  multiplication creates translated copies in the RF signal.
- Calling `fc-fm` a negative frequency merely because it is the lower
  sideband; it is still a positive RF frequency in this example.
- Confusing sideband spacing with modulation depth. Frequency sets location;
  depth and message amplitude set line amplitude.
- Treating the drawn magnitude envelope as the signed quantity after it
  crosses zero.
- Claiming over-modulation destroys the message everywhere. It breaks ordinary
  envelope detection, while an aligned coherent detector can retain the sign.
- Assuming any peak near the carrier is a sideband without checking leakage,
  noise, the FFT grid, and the known message frequencies.
- Treating the ideal low-pass mask as a realizable causal filter. It is a
  transparent finite-record teaching operation; practical filters have delay
  and transition bands.

The central idea is simple but powerful: multiplication translates spectral
content, and a receiver's phase knowledge determines whether envelope sign is
recoverable.
