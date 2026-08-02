# P20 Lesson — Frequency and Phase Are Estimates, Not Labels

## Guiding question

How accurately can frequency and phase be estimated from a finite noisy record?

## Physical mental model

A complex tone is a pointer rotating in the I/Q plane. Frequency is how much
angle the pointer gains per second; initial phase is where it pointed at the
first sample. Noise jitters every measured pointer. A finite record therefore
contains only a limited arc of noisy evidence, not an exact frequency label.

P19 is the immediate prerequisite: it shows how DC, unequal I/Q gains, and
quadrature shear distort that rotating pointer. P20 assumes those receiver
errors are small or corrected, leaving the single-tone model

\[
x[n] = A e^{j(2\pi f_0 n/f_s + \phi_0)} + w[n],\quad n=0,\ldots,N-1,
\]

where `A` is volts, `f0` and `fs` are hertz, `phi0` is radians, and `w[n]` is
circular complex noise. In the script, SNR means `A^2/E{|w|^2}`.

## Three visible frequency estimates

### Peak FFT bin

The FFT tests the record against a grid `fk = k*fs/N`. Choosing the largest
magnitude gives

\[
\hat f_{\rm bin}=k_{\max}\frac{f_s}{N}.
\]

It is robust and easy to see, but it reports only a grid point. For the P20
baseline, the tone is deliberately between bins, so a residual error remains
even when noise is small.

### Interpolated FFT peak

The script takes the logarithmic magnitudes of the winning bin and its two
neighbors. A parabola through those three samples gives the explicit offset

\[
\delta=\frac{1}{2}\frac{L_{-1}-L_{+1}}
{L_{-1}-2L_0+L_{+1}},\qquad
\hat f_{\rm int}=(k_{\max}+\delta)\frac{f_s}{N}.
\]

This uses the shape around the peak to reduce bin-grid quantization. It does
not create a longer observation or guarantee an unbiased answer: a rectangular
window's main lobe is not exactly parabolic, and noise can move all three
samples.

### Coherent phase increment

For a noise-free tone, each adjacent product removes initial phase:

\[
x^*[n]x[n+1]=A^2 e^{j2\pi f_0/f_s}.
\]

P20 adds those complex products first and takes one angle afterward:

\[
\hat f_{\rm PI}=\frac{f_s}{2\pi}
\angle\left(\sum_{n=0}^{N-2}x^*[n]x[n+1]\right).
\]

Adding before taking the angle is coherent accumulation. The estimator is
signed and assumes one per-sample phase step in `[-pi, pi)`, the complex
sampling Nyquist interval. Multiple tones, acceleration, phase noise, or a
tone outside that interval violate the model.

## Phase follows the frequency estimate

Initial phase is estimated by de-rotating with a candidate frequency and
adding the aligned samples:

\[
\hat\phi_0=\angle\left(\sum_{n=0}^{N-1}
x[n]e^{-j2\pi\hat f n/f_s}\right).
\]

If `fhat` is wrong, a residual phase slope remains across the record and the
sum partly cancels. Frequency error therefore turns into phase error. Because
angles differing by `2*pi` name the same direction, P20 compares phase with

\[
e_\phi=\operatorname{atan2}(\sin(\hat\phi_0-\phi_0),
\cos(\hat\phi_0-\phi_0)).
\]

Ordinary subtraction would incorrectly call `+pi` and `-pi` almost `2*pi`
apart.

## Bias, spread, and reliability

Bias is the average signed error over the 40 seeded trials. Standard deviation
is the trial-to-trial spread. Phase uses a circular mean and circular standard
deviation because its endpoints join. A small error in one lucky realization
does not prove a low-variance estimator; P27 later makes this Monte Carlo idea
the central lesson.

The adjacent-product coherence metric is

\[
C=\frac{|\sum x^*[n]x[n+1]|}{\sum |x^*[n]x[n+1]|},\quad 0\le C\le 1.
\]

Aligned rotations approach one. Randomly directed products cancel toward zero.
P20's `0.20` gate is an instructional confidence check, not a universal
detection threshold or calibrated probability of correctness.

## What the sweeps isolate

The SNR sweep changes only noise RMS. The same independent standardized-noise
rows are scaled in every case; tone, phase, sample rate, record length, trial
count, and estimator equations stay fixed. At low SNR, peak
selection can jump bins, interpolation follows a noisy shape, and adjacent
products lose coherence.

The record-length sweep changes only `N`. Each case uses a prefix of the same
standardized-noise trial rows; SNR per sample, tone, phase, sample rate, and
trial count stay fixed. More samples provide a longer coherent
aperture, shrink FFT spacing, and usually reduce random spread. The peak-bin
method can still plateau at its nearest grid point; interpolation and coherent
phase can exploit sub-bin information.

## Broken case and recovery

The broken estimator takes only the first and last noise-free samples, calls
their principal angle the total phase change, and divides by elapsed time.
The true phasor completes many turns, so `angle` discards unknown multiples of
`2*pi`. The result is a confident but aliased near-zero frequency. The recovery
uses adjacent increments: each individual step is inside `[-pi, pi)`, and the
complex products are summed before one angle is taken.

The second failure is not a coding bug. Tone amplitude falls to `0.02 V` while
the exact baseline receiver-noise samples and their RMS stay fixed, so amplitude
is the only changed input. The candidate frequency is then supported by low
coherence and is withheld. Recovery means restore signal amplitude, reduce
noise, observe longer, or use a stronger signal model—not merely print more
digits.

## Limiting cases

- As SNR tends to infinity, peak-bin error retains grid quantization for an
  off-bin tone; interpolation and coherent phase approach their deterministic
  model limits.
- As duration grows at fixed per-sample SNR, coherent information grows and
  spread generally falls, but model mismatch can become more visible too.
- As amplitude tends to zero at fixed receiver noise, frequency and phase
  become noise-driven; an estimate still exists numerically but has no useful
  support.
- At zero frequency, phase increment is zero and initial phase remains
  measurable if amplitude is present.
- At the signed Nyquist boundary, `+pi` and `-pi` are the same sampled rotation;
  the phase-increment estimate cannot distinguish the two endpoints.
- With two tones, the adjacent products and one FFT peak describe a mixture,
  not two independent single-tone estimates.

## Radar connection

In coherent radar, beat frequency can encode range and pulse-to-pulse phase can
encode Doppler. A longer dwell or better SNR can improve estimation, but only
while target motion and waveform assumptions remain valid. Low target
amplitude, fading, clutter, acceleration, oscillator phase noise, or receiver
I/Q error can break the single-stable-tone model. Reporting a frequency without
a confidence indicator can turn noise into a believable false range or speed.

## Common interpretation mistakes

- Calling FFT spacing `fs/N` the unavoidable frequency-estimation accuracy.
- Treating zero-padding or three-bin interpolation as additional observation
  time.
- Averaging wrapped phase values with ordinary linear arithmetic.
- Estimating phase without stating the time origin or the frequency used for
  de-rotation.
- Assuming the phase-increment method is unambiguous outside signed Nyquist.
- Calling the estimator with the smallest error in one seeded record universally
  best.
- Accepting a low-amplitude number without checking coherence or another
  confidence measure.

The point is not to memorize a winner. It is to connect each estimator's error
to observation time, SNR, phase coherence, and the validity of its model.
