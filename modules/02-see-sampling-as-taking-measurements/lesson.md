# Lesson: A Sample Is a Measurement, Not a Tiny Piece of a Curve

## Guiding question

What information is lost when a continuous-looking signal is represented by discrete samples?

## Physical model

Imagine a voltmeter that opens its eyes only at regularly spaced instants. For
a continuous sinusoid

\[
x(t)=A\cos(2\pi f_0t+\phi),
\]

a sampler with interval \(T_s=1/f_s\) stores

\[
x[n]=x(nT_s)=A\cos\!\left(2\pi\frac{f_0}{f_s}n+\phi\right).
\]

The stored pair is the sample index (or its known time) and the measured
amplitude. Nothing in that sequence directly records the path taken between
two measurements. The baseline's dense curve is therefore a reference used by
the experiment, not extra information available to the sampler.

## What interpolation adds

The baseline draws a piecewise-linear interpolation. Between neighboring
measurements \(x[n]\) and \(x[n+1]\), it uses

\[
\widehat{x}(t)=(1-\alpha)x[n]+\alpha x[n+1],\qquad 0\leq\alpha\leq1.
\]

That straight line is an assumption about the missing interval. It passes
through the measurements but is not generally the original sinusoid. A
bandlimited signal can instead be reconstructed ideally with shifted sinc
functions when the sample rate is sufficiently high and the model's infinite
record assumptions hold. This lesson keeps the linear rule visible because
the important distinction is between measured facts and an added
reconstruction model.

## Sample rate and distinguishable frequency

For a signal known to contain no frequency at or above \(f_s/2\), the ideal
sampling theorem gives a unique bandlimited reconstruction. The quantity
\(f_s/2\) is the Nyquist frequency.

- Far above \(2f_0\), many measurements describe each cycle and even a simple
  line looks close to the reference.
- Just above \(2f_0\), an ideal infinite-record reconstruction can still be
  unique under the bandlimited model, but there are barely more than two
  measurements per cycle. Straight-line interpolation looks poor and timing
  phase matters visibly.
- Below \(2f_0\), the original tone is outside the permitted baseband. Several
  continuous sinusoids can produce the same sequence, so the samples alone
  cannot select the original one.

The broken case makes the last statement exact. At \(f_s=12\) samples/s,
samples of the 7 Hz tone also match a reflected 5 Hz cosine with reversed
phase and a 19 Hz cosine:

\[
\cos(2\pi 7n/12+\phi)
=\cos(2\pi 5n/12-\phi)
=\cos(2\pi 19n/12+\phi).
\]

The curves disagree between measurements. Their stored values agree to
floating-point roundoff.

## Limiting cases

- As \(f_s/f_0\) becomes very large, neighboring samples move closer together;
  the sampler still stores points, but many simple reconstructions improve.
- At exactly two samples per cycle, the result is fragile. A cosine sampled at
  its peaks alternates signs, while a phase-shifted cosine can be measured as
  all zeros. Equality at the Nyquist boundary is not a safe practical margin.
- If \(f_s<2f_0\), alias candidates are unavoidable unless some independent
  prior knowledge or analog filtering rules them out.
- At \(f_0=0\), the signal is constant, so every sample repeats one value and
  there is no between-sample motion to identify.
- A finite record adds another limit: it observes only a bounded time interval,
  even when its sample rate satisfies the ideal theorem.

## Radar meaning

A radar ADC takes fast-time voltage measurements; it never captures a literal
continuous line. The analog anti-alias filter limits which input frequencies
may reach the ADC so the digital sequence has a defensible interpretation.
Pulse-Doppler radar repeats the same idea in slow time: pulse-to-pulse samples
measure phase at the pulse repetition frequency, and Doppler frequencies
outside that unambiguous interval can make the same slow-time sequence.

## Prerequisites and dependencies

P01 is the curriculum prerequisite: its sinusoid and phase model are reused
here. The experiment uses base MATLAB only and requires no toolbox, external
data, helper function, hardware, or network access. Sampling, interpolation,
and every alias candidate are written as explicit arithmetic.

## Common interpretation mistakes

- A smooth plot command does not prove that the signal was measured between
  points. The renderer only joined or interpolated stored values.
- More samples improve description only when the input bandwidth is controlled;
  an arbitrarily high unknown input frequency can still have aliases.
- Being just above \(2f_0\) does not make piecewise-linear interpolation exact.
- The low-frequency alias is not noise or estimation error. It is a different
  continuous signal that agrees exactly at every measurement instant.
- The dense reference curve in this synthetic experiment represents ground
  truth supplied by the model, not information recovered from the samples.
