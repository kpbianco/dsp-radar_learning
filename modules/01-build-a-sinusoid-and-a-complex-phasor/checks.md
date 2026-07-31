# Checks

## Observe

1. Which plot directly shows amplitude as phasor radius?
2. With I to the right and Q upward, which way do positive and negative
   complex frequencies rotate as time advances?
3. Which sweep moves the starting point without changing the number of cycles?
4. What two printed errors confirm the projection and constant-radius models?

## Predict, then verify

1. If \(A\) changes from 1 to 2, predict the time-domain peak magnitude and IQ
   radius.
2. If \(f_0\) changes from 5 Hz to 10 Hz for a one-second record, predict the
   number of rotations and whether the radius changes.
3. If \(\phi=\pi/2\), predict I and Q at \(t=0\).
4. If the sign of \(f_0\) changes, predict what changes in the IQ trajectory
   and what remains the same in its radius.

## Interpret

- Explain why `real(z)` equals the real cosine rather than merely resembling
  it.
- Explain why a static IQ circle cannot reveal rotation direction unless the
  sample order or an arrow is shown.
- Explain how the phase slope in the frequency sweep connects to a frequency
  or Doppler shift.
- In the broken case, explain why both the 5 Hz and apparent 3 Hz curves agree
  exactly at an 8 samples/s measurement rate.

## Recovery check

Restore the committed baseline controls and confirm that every assertion
passes. If a baseline-control assertion fails, use its message to restore a
finite positive real amplitude and frequency, a finite real phase, a finite real
sample rate above \(2f_0\), a finite positive real duration, and an integer
sample count between 2 and 5000. The deliberately broken section has the
opposite sampling-rate contract: `fs_bad` must be finite, positive, and real,
remain below \(2f_0\), and produce an integer sample count from 2 through 5000
before the script allocates its measurement vector.

## Teach-back completion

In two or three sentences, answer:

**How do amplitude, frequency, and phase appear in time and in the complex plane?**

A satisfactory answer:

- maps amplitude to time-domain peak height and IQ radius;
- maps frequency to cycles per second and phasor rotation rate;
- maps phase to position within the cycle and initial complex-plane angle;
- connects the real cosine to the I-axis projection; and
- distinguishes positive from negative frequency by rotation direction.
