# P19 Lesson: Receiver Imbalance Creates Predictable Spectral Copies

## Guiding question

How do DC offset, gain mismatch, and quadrature error change an IQ spectrum?

## Physical mental model

P18 treated I and Q as the horizontal and vertical coordinates of a rotating
arrow. An ideal receiver measures those coordinates with the same scale, a
90-degree relationship, and an origin at zero. A direct-conversion receiver
can miss all three conditions:

- DC offset moves the origin, so the whole I/Q trajectory shifts.
- Unequal branch gains stretch one axis more than the other, turning a circle
  into an axis-aligned ellipse.
- Quadrature phase error mixes part of I into Q, tilting or shearing that
  ellipse.

Those geometry changes have spectral signatures. The offset creates a spike at
zero frequency. Either kind of I/Q imbalance creates a conjugate image of a
positive-frequency tone at the corresponding negative frequency.

## The explicit receiver model

Let the ideal complex tone be

\[
z[n]=I[n]+jQ[n]=A e^{j\theta[n]},\qquad
\theta[n]=2\pi f_0 n/f_s+\theta_0.
\]

The experiment uses the memoryless receiver model

\[
I_r[n]=g_I I[n]+d_I,
\]

\[
Q_r[n]=g_Q\big(Q[n]\cos\phi+I[n]\sin\phi\big)+d_Q.
\]

Here `dI,dQ` are offsets in volts, `gI,gQ` are dimensionless branch gains, and
`phi` is quadrature error. The sign of `phi` depends on the receiver's phase
convention; its magnitude controls the leakage in this model.

After removing DC, the impaired tone can be written as

\[
z_r[n]=\alpha e^{j\theta[n]}+\beta e^{-j\theta[n]},
\]

with

\[
\alpha={g_I+g_Qe^{j\phi}\over 2},\qquad
\beta={g_I-g_Qe^{-j\phi}\over 2}.
\]

`alpha` multiplies the desired `+f0` rotation. `beta` multiplies a new `-f0`
image. Image-rejection ratio is therefore

\[
\mathrm{IRR}=20\log_{10}{|\alpha|\over|\beta|}\ \mathrm{dB}.
\]

The script computes the same quantities transparently by projecting samples
onto `exp(+j*theta)` and `exp(-j*theta)`. The centered FFT supplies the picture;
the coherent projections supply the labeled desired/image metrics.

## What each isolated impairment does

DC alone changes `mean(z)` but does not create a deterministic conjugate image.
Its zero-frequency spike relative to the desired tone is

\[
20\log_{10}{|d_I+jd_Q|\over|\alpha|}\ \mathrm{dBc}.
\]

With gain mismatch alone (`phi=0`),

\[
\mathrm{IRR}={g_I+g_Q\over|g_I-g_Q|}
\]

before conversion to decibels. With equal gains and phase error alone,

\[
\mathrm{IRR}=\cot(|\phi|/2).
\]

Both imbalance mechanisms make an image, but their I/Q geometry differs:
gain mismatch changes the axis lengths while phase error creates nonzero I/Q
correlation.

## Why correction is staged

First estimate and subtract the mean:

\[
\hat d=\operatorname{mean}(z_r),\qquad z_0=z_r-\hat d.
\]

For a full-cycle circular calibration tone, each ideal branch has RMS
`A/sqrt(2)`. Estimate the two gains from branch RMS and divide them out:

\[
\hat g_I={\sqrt{2E[I_0^2]}\over A},\qquad
\hat g_Q={\sqrt{2E[Q_0^2]}\over A}.
\]

After gain normalization, the normalized cross-correlation is

\[
\rho={2E[I_gQ_g]\over A^2}=\sin\phi,
\qquad \hat\phi=\sin^{-1}(\rho).
\]

The correction must undo the quadrature shear:

\[
Q_c={Q_g-I_g\sin\hat\phi\over\cos\hat\phi},
\qquad z_c=I_g+jQ_c.
\]

Order matters. Removing the center first prevents offsets from contaminating
RMS and covariance. Normalizing branch scales next makes the cross-correlation
an estimate of phase error rather than a mixture of phase and gain effects.

## The two sweeps

The I-gain sweep holds Q gain at one, keeps the 1 V tone fixed, and holds DC,
quadrature error, and noise at zero. Increasing `gI` from 1 to 1.30 stretches
the horizontal axis and lowers image rejection monotonically.

The quadrature-error sweep holds both gains at one and holds DC, tone, and
noise fixed. Increasing error from 0 to 15 degrees increases I/Q correlation,
tilts the trajectory, and raises the negative-frequency image. Each sweep
changes one receiver mechanism.

## The deliberately broken case

A tempting repair is to rotate the whole gain-corrected complex stream by
`exp(-j*phiHat)`. That changes the phases of both desired and image components
but not either magnitude, so IRR is unchanged. A global rotation can repair a
common carrier phase; it cannot undo nonorthogonal I/Q axes. The shear inverse
above removes the I leakage from Q and improves IRR.

## Limiting cases

- With zero offset, equal gains, and zero phase error, the ideal image is zero;
  finite noise and arithmetic set the reported floor.
- DC removal cannot distinguish receiver offset from a real desired signal at
  zero frequency. A calibration assumption or separate reference is required.
- If the calibration record does not span balanced/full-cycle excitation,
  signal mean and covariance can masquerade as impairment.
- As `|phi|` approaches 90 degrees, `cos(phi)` approaches zero and the shear
  inverse becomes singular and noise-sensitive. This lesson deliberately
  constrains the model to `|phi|<45 degrees`.
- The `asin` estimator assumes the small-error branch. It cannot identify the
  correct quadrant for arbitrary phase errors.
- Dynamic, frequency-selective, nonlinear, clipping, timing-skew, and LO
  leakage mechanisms require richer receiver models than this static lesson.
- A stationary QPSK cloud would need symbol-aware interpretation. This module
  uses a rotating calibration tone, so the plotted curve is an I/Q trajectory,
  not a symbol constellation.

## Radar connection

In a homodyne radar receiver, DC leakage can cover zero-Doppler returns, while
gain and quadrature imbalance mirror a strong positive-Doppler or beat-frequency
component into the negative side. That false image can resemble a target in a
signed spectrum or range-Doppler map. Calibration improves the digital sample
stream, but it does not prove that every center spike or mirrored return in
operational data is receiver impairment.

## Common interpretation mistakes

- Calling every center bin a target or every image a second physical source.
- Treating DC subtraction as safe when a desired baseband signal can truly sit
  at DC.
- Using a global complex rotation to repair quadrature-axis nonorthogonality.
- Estimating phase before centering and gain-normalizing the branches.
- Calling an I/Q trajectory a QPSK constellation.
- Reporting a high ideal IRR without naming the noise and numerical floor.
- Assuming one calibration tone covers frequency-dependent hardware behavior.

## Dependencies and execution boundary

P18 is the immediate prerequisite: it establishes signed complex spectra,
conjugate images, and the information carried jointly by I and Q. P11 supplies
the centered FFT-frequency map.

The script uses base MATLAB, a private seed, one 4096-sample record, two fixed
three-case sweeps, and six P19-tagged figure groups. It performs no file,
network, audio, timer, parallel, or background work. Ctrl+C cancels only the
foreground run. Static Python validation does not prove MATLAB execution,
rendered plots, hardware behavior, or educational effectiveness.
