# P26 Lesson: Use LMS to Cancel an Interferer

## Guiding question

How can an adaptive filter learn an unknown coupling path?

## Physical model

Imagine two receiver channels. The **primary** channel contains the signal we
want plus a strong unwanted waveform. A nearby **reference** channel measures
the source of that interference before it travels through an unknown cable,
antenna, leakage, or multipath coupling path.

The reference is not usually identical to the interference at the primary
sensor. If the unknown path has (L) taps, its contribution is

\[
i[n] = \sum_{k=0}^{L-1} h_k x[n-k] = \mathbf{h}^{T}\mathbf{x}_n.
\]

The primary measurement is

\[
d[n] = s[n] + i[n],
\]

where (s[n]) includes the desired waveform and independent receiver noise.
P25 made a fixed FIR path visible. P26 asks how to estimate those taps from
streaming samples when they are not known in advance.

## The canceller predicts, then subtracts

The adaptive filter forms its own interference estimate

\[
\hat{i}[n] = \mathbf{w}^{T}[n]\mathbf{x}_n
\]

and subtracts it from the primary input:

\[
e[n] = d[n]-\hat{i}[n].
\]

If the learned coefficients (mathbf{w}) approach the coupling path
(mathbf{h}), then (hat{i}) approaches (i). The error becomes mostly the
desired signal, rather than zero. That distinction matters: a nonzero output
does not by itself mean cancellation failed.

## Why the LMS update points the right way

LMS adjusts the taps in the direction that reduces instantaneous squared
error:

\[
\boxed{\mathbf{w}[n+1] = \mathbf{w}[n] + \mu e[n]\mathbf{x}_n}
\]

for this real-valued experiment. When a reference sample and the error have
the same sign, increasing the matching tap would have predicted more of the
primary interference, so the update is positive. Opposite signs move the tap
the other way. Repeating this noisy correction makes the average squared error
(E\{e^2[n]\}) fall toward its minimum.

The script keeps the multiply, subtraction, and coefficient update inside the
sample loop. No adaptive-filter toolbox call decides what LMS means.

## What the step size controls

The step size (mu) sets how far the coefficients move on each sample.

- A very small positive step is calm but slow. It may not finish learning
  before the path changes again.
- A moderate step learns and reacquires faster.
- A larger stable step keeps responding to random instantaneous error, so the
  taps wander more around their optimum. This is **misadjustment**.
- An oversized step makes the feedback update grow instead of settle.

For a reference correlation matrix \(\mathbf{R}_x\), the familiar ideal bound
for convergence of the **mean coefficient error**, under the usual LMS
independence assumptions, is

\[
0 < \mu < \frac{2}{\lambda_{\max}(\mathbf{R}_x)}.
\]

That mean-convergence condition is not a mean-square stability guarantee. Tap
and error power can diverge at a smaller step because mean-square behavior also
depends on filter length and fourth-order input statistics. For the ideal
independent white Gaussian input used as the reference model here, the
mean-square bound is

\[
0 < \mu < \frac{2}{(L+2)P_x} = 0.2.
\]

Finite-record edge effects mean this value is still a model reference, not a
measured universal threshold. The experiment avoids hiding either limit behind
an eigensolver and uses the much more conservative visible study rule

\[
\mu_{\text{study}} \le
\frac{0.1}{L\,P_x}, \qquad P_x=E\{x^2[n]\}.
\]

With eight taps and a unit-power reference, the study limit is \(0.0125\). The
baseline uses \(0.006\). The intentionally broken value \(0.35\) exceeds both
the study rule and the ideal white-Gaussian mean-square reference bound, and a
finite guard stops it before the coefficients consume unbounded numerical
range.

## The path-change transient is useful evidence

Halfway through the record, the true FIR coefficients change. The learned
weights are suddenly correct for the old path and wrong for the new one.
Coefficient mismatch and residual power rise together. Their later decline is
direct evidence of reacquisition; it is not a plotting artifact or a reset
performed at the change.

The 64-sample hold requirement prevents a single lucky low-mismatch sample
from being called reacquisition.

## Why reference quality matters

LMS can remove only the part of the primary input that the reference can
predict. In the second sweep,

\[
z[n] = \rho x[n] + \sqrt{1-\rho^2}\,v[n],
\]

where `v[n]` is fixed independent noise and the primary signal never changes.
At `rho=1`, the adaptive input is the true source reference. As `rho`
approaches zero, that input carries less information about the
coupled interference. A perfectly stable LMS filter with an uncorrelated
reference still cannot cancel what it cannot observe.

This is different from the unstable-step broken case. One fails because the
data do not identify the path; the other fails because the update gain is too
large.

## Reading the spectra

The primary spectrum contains the desired 700 Hz and 1100 Hz lines plus broad
reference-coupled energy. The script forms its Hann window explicitly and uses
an FFT only after the LMS loop. In settled intervals, the output spectrum
loses much of the broad interference while the two desired lines remain.

LMS is minimizing time-domain mean-square error, not editing chosen FFT bins.
The spectral improvement is a consequence of subtracting the predicted
waveform sample by sample.

## Limiting cases

- **(mu=0):** the weights never move; the output stays equal to the primary
  input.
- **Perfect reference, fixed representable path:** the taps can approach the
  path and the residual interference can approach zero, leaving desired signal
  and independent noise.
- **Reference uncorrelated with the interferer:** no tap vector can predict the
  unwanted waveform; stable adaptation cannot create missing information.
- **Too few taps:** even a perfect reference cannot represent the entire
  coupling path, so structured residual interference remains.
- **Desired signal correlated with the reference:** the canceller may also
  remove desired energy. Reference placement and signal independence are
  physical assumptions, not software details.
- **Path changes faster than convergence:** the coefficients chase a moving
  target and never reach the settled error floor.
- **Oversized step:** coefficient and error energy diverge; more samples do not
  repair an unstable update.

## Common interpretation mistakes

- “The error should become zero.” No: the error is the useful canceller output
  and should retain the desired signal and independent noise.
- “The learned taps are a universal channel estimate.” They describe only the
  local reference-to-primary coupling represented by this filter and data.
- “A faster step is always better.” Faster reacquisition usually brings more
  steady tap motion and may cross into instability.
- “The path-change spike proves a bug.” It proves the previously learned model
  has become stale.
- “Any nearby sensor is a usable reference.” Physical correlation, delay
  coverage, and reference quality determine what can be predicted.

## DSP and radar connection

The same structure appears in transmitter leakage cancellation, active noise
control, full-duplex radios, sidelobe cancellers, vibration removal, and radar
clutter/interference reference channels. Later adaptive arrays add spatial
channels, but the central question stays the same: what portion of the unwanted
measurement is predictable from the available reference data?
