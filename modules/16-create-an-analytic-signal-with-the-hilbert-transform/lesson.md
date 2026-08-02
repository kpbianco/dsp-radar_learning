# P16 Lesson: Magnitude Gives Phase a Reliable Direction

## Guiding question

How can a real waveform be represented by a complex envelope?

## Physical mental model

A real sinusoid is the horizontal shadow of a rotating arrow. From the shadow
alone, clockwise and counterclockwise rotations are mixed together. The analytic
signal supplies the missing vertical coordinate, making one complex arrow

\[
z(t)=x(t)+j\widehat{x}(t)=A(t)e^{j\phi(t)}.
\]

Its horizontal projection is the measured real signal `x(t)`. Its length
`|z(t)|` is the envelope `A(t)`, and its angle `arg(z(t))` is phase `phi(t)`.
This is a representation of the original real waveform, not a second physical
sensor measurement.

## The explicit Hilbert-transform operation

For an even `N`-sample record, the experiment transforms the real signal to
`X[k]` and multiplies it by

\[
H[k]=\begin{cases}
1, & k=0 \text{ or } k=N/2,\\
2, & 0<k<N/2,\\
0, & N/2<k<N.
\end{cases}
\]

Then

\[
z[n]=\operatorname{IFFT}\{X[k]H[k]\}.
\]

The real signal split its energy between conjugate positive and negative
frequencies. Doubling the positive half preserves amplitude while zeroing the
negative half removes redundant rotation. DC and Nyquist are unique real bins,
so they are retained rather than doubled. This is the discrete Hilbert analytic
signal; the script exposes the mask instead of calling `hilbert()`.

## Envelope, phase, and instantaneous frequency

The script reads

\[
\widehat{A}[n]=|z[n]|,\qquad
\widehat{\phi}[n]=\operatorname{unwrap}(\arg z[n]),
\]

and estimates phase slope with one-sample differences,

\[
\widehat{f}_i[n]=\frac{f_s}{2\pi}
\left(\widehat{\phi}[n]-\widehat{\phi}[n-1]\right).
\]

In the baseline, the designed phase is a 240 Hz carrier plus a 3 Hz sinusoidal
phase variation. A phase-deviation index `beta` therefore creates peak frequency
deviation `beta*3 Hz`. The phase-index sweep makes that proportionality visible.

## Why envelope depth matters

The envelope is `1 + m*cos(2*pi*2*t)`. Raising depth `m` from 0.20 to 0.90
changes only the arrow length: its minimum falls from 0.80 V to 0.10 V while the
designed phase law stays fixed. Small noise moves a short arrow's angle more
than a long arrow's angle, so frequency estimates become increasingly noisy at
the deepest minima even before a true null occurs.

This does not mean envelope modulation physically changes the designed carrier
frequency. It changes confidence in an angle-based estimate.

## The deliberately broken near-zero case

At the Gaussian notch, designed magnitude falls to 0.001 V while noise RMS is
0.010 V. The complex sample passes close to the origin. At the origin, every
angle describes the same zero-length vector, so phase is undefined. Near it,
tiny noise can rotate the measured vector drastically; differentiating that
angle magnifies the jump into an impressive but meaningless instantaneous-
frequency spike.

The recovery is epistemic rather than magical: retain the envelope, but mark a
one-sample frequency interval unavailable unless magnitude is at least 0.05 V
at both phase samples used by the difference. An amplitude gate does not
reconstruct phase information that was never reliable.

## Limiting cases

- With constant positive envelope and linear phase, the analytic signal is a
  constant-radius phasor and instantaneous frequency is constant.
- As envelope variation becomes slower than the carrier, magnitude tracks the
  designed modulation cleanly; if modulation overlaps or crosses the carrier,
  the simple envelope interpretation can fail.
- As magnitude approaches zero, phase variance grows without bound and phase
  at an exact zero is undefined.
- With no noise and no exact zero, phase can remain mathematically continuous,
  but a near-zero measurement is still poorly conditioned to any disturbance.
- The one-sample phase difference approaches a derivative as sampling becomes
  dense; at finite sample rate it is an average slope over one interval.
- An FFT-based Hilbert transform treats the finite record as periodic, so
  discontinuous record edges can create boundary artifacts. The baseline uses
  coherent modulation and excludes a small edge guard from accuracy metrics.

## DSP and radar connection

Radar receivers routinely describe a real RF or IF waveform by complex I/Q.
The complex envelope makes amplitude, phase, Doppler phase progression, matched
filtering, and downconversion easier to express without duplicating negative
frequency. But an I/Q sample with very low magnitude cannot support a reliable
phase or Doppler estimate. Practical processors therefore carry magnitude/SNR
quality alongside phase-derived measurements. P17 will take this analytic
signal and move its carrier to complex baseband by hand.

## Common interpretation mistakes

- Treating the analytic signal as extra measured information rather than a
  one-sided representation of the same real record.
- Doubling DC or Nyquist along with ordinary positive-frequency bins.
- Calling `abs(x)` the envelope; the real carrier crosses zero every half-cycle.
- Reading wrapped phase jumps as frequency impulses instead of unwrapping first.
- Trusting phase or its derivative when analytic magnitude is near zero.
- Treating an amplitude gate as though it recovered the rejected phase samples.
- Assuming every multicomponent waveform has one physically meaningful
  instantaneous frequency; the interpretation is clearest for one dominant
  narrowband component.

## Safe execution boundary

The script has fixed arrays, two three-case loops, five tagged figure groups,
private deterministic noise, and no file/network/audio I/O or background work.
Ctrl+C cancels it. A malformed control fails before random, signal, FFT, or
figure allocation, and rerunning removes only stale P16 figures/results. Static
tests cannot substitute for MATLAB execution or human inspection.
