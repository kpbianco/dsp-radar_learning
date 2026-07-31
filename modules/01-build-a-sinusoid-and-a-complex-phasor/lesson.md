# Lesson: A Sinusoid Is a Rotating Vector's Shadow

## Guiding question

How do amplitude, frequency, and phase appear in time and in the complex plane?

## Physical model

Imagine a pointer of length \(A\) rotating around the origin. Its complex
position is

\[
z(t)=A e^{j(2\pi f_0t+\phi)}
    =A\cos(2\pi f_0t+\phi)+jA\sin(2\pi f_0t+\phi).
\]

The baseline figure shows both descriptions of that one motion:

\[
I(t)=\operatorname{real}\{z(t)\},\qquad
Q(t)=\operatorname{imag}\{z(t)\},\qquad
x(t)=I(t).
\]

The real cosine is the pointer's shadow on the horizontal, or I, axis. The
Q trace is its vertical coordinate. This is why the experiment's projection
error is approximately numerical roundoff rather than a modeling error.

## What each parameter does

- **Amplitude \(A\)** is peak height in the time plot and radius in the IQ
  plot. It does not change the number of cycles per second.
- **Frequency \(f_0\) in hertz** is cycles per second. The angular rate is
  \(\omega_0=2\pi f_0\) radians per second, so a larger magnitude of frequency
  makes the pointer rotate faster without changing its radius.
- **Phase \(\phi\) in radians** is the angle at \(t=0\). It changes the initial
  I and Q values without changing radius or rotation rate.

The three sweep figures isolate those effects one variable at a time.

## Rotation sign and radar meaning

With the usual \(I\)-right, \(Q\)-up axes, \(e^{+j2\pi f_0t}\) rotates
counterclockwise and \(e^{-j2\pi f_0t}\) rotates clockwise as time advances.
Complex I/Q data therefore preserves the sign of frequency. A real cosine
alone cannot distinguish the two directions because

\[
\cos(2\pi f_0t+\phi)
=\frac{1}{2}e^{j(2\pi f_0t+\phi)}
 +\frac{1}{2}e^{-j(2\pi f_0t+\phi)}.
\]

That sign becomes physically useful in an I/Q receiver: after a convention is
chosen, opposite Doppler shifts or mixer offsets rotate in opposite directions.

## Limiting cases

- At \(A=0\), every sample is zero, so phase and frequency cannot be observed.
- At \(f_0=0\), the pointer does not rotate; I and Q are constant values set by
  \(A\) and \(\phi\).
- Adding \(2\pi\) to phase returns the same starting point and waveform.
- When the sample rate is too low, the pointer still has a valid continuous
  rotation, but the measurements do not identify it uniquely. In the broken
  case, samples of the 5 Hz cosine at 8 samples/s exactly match samples from an
  apparent 3 Hz cosine with the corresponding phase reversal.

The broken figure therefore shows a measurement failure, not a failure of the
phasor model. Later sampling and aliasing modules develop this limit in detail.

## Prerequisites and dependencies

This is the first module, so it has no curriculum prerequisite. The experiment
uses base MATLAB only and requires no toolbox, external data, helper function,
hardware, or network access. It uses an explicit cosine and complex
exponential so the essential operation remains visible.

## Common interpretation mistakes

- Phase is not a time delay by itself. For a nonzero frequency, the equivalent
  delay also depends on frequency: \(\Delta t=-\Delta\phi/(2\pi f_0)\).
- A larger IQ circle means larger amplitude, not faster rotation.
- A static circle shows radius but not direction. Follow the ordered samples
  and direction arrow.
- A plausible line through undersampled points is not proof of the original
  continuous frequency.
