# P17 Lesson: Change the Reference That Measures Rotation

## Guiding question

How does multiplying by a complex oscillator move an RF/IF signal to baseband?

## Physical mental model

Imagine watching a carrier phasor while turning your own reference frame. If
the carrier turns at `fc` cycles/s and your reference turns at `fLO`, the motion
you see is only their difference. Matching the turns freezes the phasor;
turning more slowly leaves counterclockwise motion; turning faster makes the
phasor appear to rotate clockwise. Complex multiplication creates that rotating
reference frame without discarding the sign of the remaining motion.

For the measured real passband tone

\[
x(t)=A\cos(2\pi f_c t+\phi_c),
\]

the local oscillator is

\[
\ell(t)=e^{-j(2\pi f_{LO}t+\phi_{LO})}.
\]

Multiplying them gives two visible terms:

\[
x(t)\ell(t)=
\frac{A}{2}e^{j[2\pi(f_c-f_{LO})t+\phi_c-\phi_{LO}]}
+\frac{A}{2}e^{-j[2\pi(f_c+f_{LO})t+\phi_c+\phi_{LO}]}.
\]

The first is the desired signed difference frequency. The second is the
sum-frequency image. Multiplication moves both; the low-pass filter merely
keeps the translated copy near zero.

## Where the one-half amplitude comes from

A real cosine is the sum of positive- and negative-frequency complex arrows,
each with amplitude `A/2`. Negative-exponent mixing moves the positive-frequency
arrow toward zero, so the unscaled filtered output has amplitude `A/2`. That is
not loss or a filter bug. The experiment labels an explicit multiplication by
two after filtering so the reported complex-envelope magnitude equals the
original real cosine's peak amplitude `A`.

For an already analytic complex input from P16, the positive-frequency arrow
can carry amplitude `A` without a conjugate copy. In that convention no `2x`
real-input correction is needed. Amplitude claims must name which convention
they use.

## Signed baseband frequency and phase

After the filter and explicit real-input calibration,

\[
z_{BB}(t)\approx A e^{j[2\pi(f_c-f_{LO})t+\phi_c-\phi_{LO}]}.
\]

Therefore:

- `fc > fLO` gives positive baseband frequency and counterclockwise I/Q motion;
- `fc = fLO` gives a stationary I/Q point;
- `fc < fLO` gives negative baseband frequency and clockwise I/Q motion;
- increasing LO phase rotates the output angle negatively without changing its
  frequency or magnitude.

Negative baseband frequency is useful information, not an error. It tells which
side of the LO contained the RF energy and is one reason radar receivers retain
complex I/Q instead of one real baseband channel.

## The low-pass filter by hand

The script constructs an odd 129-tap ideal low-pass impulse response,

\[
h_d[n]=\begin{cases}
2f_{cut}/f_s,&n=0,\\
\sin(2\pi f_{cut}n/f_s)/(\pi n),&n\ne0,
\end{cases}
\]

multiplies it by an explicit Hamming window, normalizes its DC gain, and
convolves it with the mixer output. It then removes the known integer group
delay. The 80 Hz cutoff passes every `+36/0/-36 Hz` sweep result and is far from
the roughly `-(fc+fLO)` image. A fixed edge guard excludes convolution
transients from metrics; it does not conceal samples in the plots.

## The deliberately broken side selection

The broken case changes `exp(-j*2*pi*fLO*t)` to
`exp(+j*2*pi*fLO*t)` at a 216 Hz LO. For a real input, this does not yield zero:
the negative-frequency conjugate copy is also present. The positive-exponent
oscillator moves that copy to `-(fc-fLO) = -24 Hz`, conjugates the RF phase
convention, and reverses I/Q rotation. If the receiver contract says positive
RF maps through the negative-exponent LO, the output is now the wrong side.

Recovery restores the negative exponent and the intended `+24 Hz`. Calling a
276 Hz high-side LO itself "wrong" would be incorrect: it legitimately produces
`-36 Hz` and preserves side-of-LO information.

## Limiting cases

- Exact LO match produces DC. Phase remains measurable as the stationary I/Q
  angle even though frequency is zero.
- An LO offset of `Delta` produces `-Delta` when `fLO = fc + Delta` and
  `+Delta` when `fLO = fc - Delta`.
- If `|fc-fLO|` exceeds the low-pass passband, the desired signal is attenuated;
  mixing succeeded, but the selected channel does not include it.
- If the low-pass is omitted or too wide, the sum-frequency image remains in
  I/Q and the output is not a clean baseband representation.
- With zero noise and coherent tones, frequency, phase, and amplitude follow
  the equations up to FIR edge transients. Noise makes the I/Q point a small
  cloud but does not change the expected translation.
- A finite windowed-sinc FIR has transition width and ripple. An 80 Hz number
  is a design boundary, not an infinitely sharp spectral wall.
- For a real input either LO sign can select one conjugate copy; the receiver's
  sign convention determines which copy represents the intended RF side.

## Radar connection

An RF or IF radar return can contain target phase and Doppler close to a large
carrier or intermediate frequency. Downconversion subtracts the receiver LO so
the remaining complex phase evolves at a manageable signed beat/Doppler rate.
Matched filtering, coherent integration, Doppler FFTs, and angle processing can
then work on I/Q without losing whether phase advanced or retreated. A wrong
side convention reverses Doppler and phase signs even when magnitude looks
plausible, so sign is part of the interface contract.

## Common interpretation mistakes

- Saying the low-pass filter performs the frequency shift; multiplication does
  the shift and filtering selects one shifted copy.
- Expecting a real cosine's unscaled desired term to retain peak amplitude `A`
  instead of `A/2`.
- Treating negative baseband frequency as an alias or a failure.
- Calling a high-side LO wrong merely because it makes clockwise I/Q motion.
- Assuming `+j` mixing produces no baseband for a real input; it selects the
  conjugate negative-frequency RF copy.
- Ignoring LO phase even though it subtracts directly from recovered phase.
- Reading FIR edge transients as steady-state receiver behavior.

## Safe execution boundary

The experiment has fixed arrays, two three-case loops, a 129-tap FIR, five P17-
tagged figure groups, private deterministic noise, and no file/network/audio I/O
or background work. Ctrl+C cancels it. Correct a rejected control and rerun;
only P17 figures and `results` are replaced. Static tests cannot substitute for
MATLAB/Octave execution or human plot inspection.
