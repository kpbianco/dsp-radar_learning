# Lesson: A Sinusoid Is a Rotating Vector's Shadow

A complex phasor

\[
z(t)=A e^{j(2\pi f_0 t+\phi)}
\]

has constant radius `A`. Its angle starts at `phi` and advances at `2*pi*f0` radians per second. The in-phase component is its horizontal coordinate and the quadrature component is its vertical coordinate:

\[
I(t)=A\cos(2\pi f_0 t+\phi),\qquad Q(t)=A\sin(2\pi f_0 t+\phi).
\]

The ordinary real cosine is therefore just `real(z)`: the shadow of that rotating vector on the I axis. Increasing amplitude enlarges the IQ circle. Increasing frequency makes the point rotate faster. Changing phase rotates the starting point without changing radius or rotation rate.

Positive and negative complex frequencies are distinguishable because they rotate in opposite directions. A real cosine alone contains both directions as a conjugate pair, which becomes important later for I/Q receivers, mixers, Doppler sign, and image rejection.

The broken sampling case is not a phasor failure. It is a measurement failure: too few samples are taken to identify the actual rotation rate, so a different slower sinusoid can fit the same samples.
