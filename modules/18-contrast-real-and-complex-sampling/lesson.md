# P18 Lesson: Frequency Sign Is Rotation Direction

## Guiding question

Why can complex samples distinguish positive and negative frequencies?

## Physical mental model

A complex sample is a two-coordinate measurement: `I` says where the rotating
arrow points horizontally and `Q` says where it points vertically. Successive
samples show whether the arrow advances counterclockwise or retreats clockwise.
A real sample keeps only the horizontal shadow. The same shadow is cast by an
arrow rotating in either direction, so the sign is lost with Q.

For paired complex tones,

\[
z_+[n]=A e^{j(2\pi f_0 n/f_s+\phi)},\qquad
z_-[n]=A e^{-j(2\pi f_0 n/f_s+\phi)}=z_+^*[n].
\]

Their sample-to-sample phase increments are `+2*pi*f0/fs` and
`-2*pi*f0/fs`. That sign creates counterclockwise and clockwise I/Q motion and
puts their centered-FFT peaks at `+f0` and `-f0`.

Taking only the real part gives

\[
\Re\{z_+[n]\}=\Re\{z_-[n]\}
=A\cos(2\pi f_0 n/f_s+\phi).
\]

The two candidates have become exactly the same sample stream. Its spectrum
must satisfy conjugate symmetry, `X[-k]=X^*[k]`, so magnitude appears at both
`+f0` and `-f0`. Those two lobes are one real cosine, not evidence for two
independent tones.

## Upper and lower RF sides around an LO

P17 changed the reference frame with a negative-exponent complex oscillator.
P18 supplies an upper and lower complex RF side around a 600 Hz LO:

\[
x_U(t)=A e^{j[2\pi(f_{LO}+\Delta)t+\phi]},\qquad
x_L(t)=A e^{j[2\pi(f_{LO}-\Delta)t-\phi]}.
\]

Multiplication by `exp(-j*2*pi*fLO*t)` gives

\[
x_U(t)e^{-j2\pi f_{LO}t}=A e^{j(2\pi\Delta t+\phi)},
\]

\[
x_L(t)e^{-j2\pi f_{LO}t}=A e^{-j(2\pi\Delta t+\phi)}.
\]

Complex downconversion therefore labels the upper side `+Delta` and the lower
side `-Delta`. No low-pass is needed for these already-complex single-side
inputs because multiplication creates one translated component per input.

The real comparison takes the real projection of each RF side and multiplies
it by `2*cos(2*pi*fLO*t)`. Each product contains a difference cosine and a high
sum term. The script constructs a 129-tap windowed-sinc low-pass explicitly and
removes its group delay. After the sum terms are rejected, both difference
outputs reduce to the same `A*cos(2*pi*Delta*t+phi)`. The factor of two is
visible: it compensates the one-half product coefficient from a cosine mixer.
It is distinct from P17's post-filter `2x` convention for complex mixing of a
real input.

## What the two sweeps expose

The frequency-offset sweep changes only `|f|` through 40, 160, and 400 Hz. The
I/Q arrows rotate more quickly while their estimated signs remain opposite;
the real projections still coincide. Speed changes, but the reason sign is
observable does not.

The sample-rate sweep changes only sample rate while holding the 160 Hz
continuous tone, amplitude, phase, and 0.5 s duration fixed. At 2048 and 512
samples/s, the signed discrete-time frequencies remain `+160` and `-160 Hz`.
At 256 samples/s they alias to `-96` and `+96 Hz`. Complex sampling preserves
the sign of the discrete-time rotation it actually measured, but it does not
defeat Nyquist or reveal which analog alias generated those samples.

## The deliberately broken case

The failure takes `real(z)` before estimating signed phase progression. Both
I/Q circles collapse onto the same horizontal line, the paired waveforms have
zero difference, and the complex phase-increment estimator degenerates to a
zero-sign answer. Magnitude plots still look healthy, which is why an I-only
receiver can hide this failure.

Recovery is not `abs(frequency)`. Recovery retains both I and Q, then measures
the signed phase increment or reads a signed centered spectrum. That restores
`+160 Hz` and `-160 Hz` as different observations.

## Limiting cases

- At `f=0`, there is no rotation direction to distinguish; the I/Q point is
  stationary but still retains amplitude and phase.
- At `|f|=fs/2` for even-rate sampling, `exp(+j*pi*n)` and `exp(-j*pi*n)` are
  identical. Positive and negative Nyquist are the same discrete-time point.
- Above the Nyquist interval, complex tones still alias modulo `fs`. I/Q
  distinguishes the signed alias, not the unknown original analog frequency.
- If Q is exactly zero, a nominally complex container carries only real data
  and has the same ambiguity as real sampling.
- Noise makes the rotation estimate fluctuate. Paired noise in this controlled
  experiment is conjugated so frequency sign is the only changed mechanism.
- A real cosine has amplitude `A/2` in each complex spectral copy; a complex
  exponential of amplitude `A` has one copy of amplitude `A`. Compare like
  conventions before interpreting gain.

## Radar connection

After downconversion, target Doppler, beat frequency, and coherent phase live
in I/Q rotation. Energy above and below the receiver LO can have identical real
beat magnitudes but opposite signed phase progression. Keeping Q lets a radar
separate approaching/receding sign conventions, positive/negative Doppler bins,
and upper/lower side information. Discarding Q can turn two physically distinct
returns into the same waveform before later processing even begins.

## Common interpretation mistakes

- Calling negative frequency negative energy; it denotes rotation direction.
- Counting the mirrored lobes of one real cosine as two independent signals.
- Believing a magnitude spectrum alone shows rotation direction.
- Assuming a complex-valued variable is informative when its Q channel was
  discarded or never measured.
- Claiming complex sampling removes the Nyquist limit; it changes the signed
  bandwidth representation but does not remove aliasing.
- Assuming a complex LO applied to a real RF input automatically removes its
  conjugate image. P17 shows that the real input still contains both sides and
  channel selection is required.
- Comparing real-cosine and complex-exponential spectral amplitudes without
  naming the factor-of-two convention.

## Dependencies and execution boundary

P11 supplies the centered signed FFT axis, P12 supplies conjugate-symmetry
intuition, P16 supplies analytic I/Q, and P17 supplies explicit complex mixing
and amplitude bookkeeping. P17 is the declared immediate prerequisite.

The script uses base MATLAB, a private seed, fixed arrays, an explicit FIR, two
bounded three-case sweeps, and six P18-tagged figure groups. It performs no
file, network, audio, timer, parallel, or background work. Ctrl+C cancels the
foreground run. Static repository tests do not prove MATLAB execution or human
interpretation of the plots.
