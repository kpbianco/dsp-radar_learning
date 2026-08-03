# Lesson: one noisy statistic, two different questions

## Guiding question

How do false alarms, detections, bias, variance, and theoretical bounds relate?

## Physical model

A receiver knows the shape and timing of a real pulse `s`, but it does not know
whether that pulse is present in a record. It compares two hypotheses:

\[
H_0:\;\mathbf r=\mathbf n,\qquad
H_1:\;\mathbf r=A\mathbf s+\mathbf n,
\]

where each noise sample is independent Gaussian with mean zero and variance
\(\sigma^2\). This module uses real noise, so \(\sigma^2\) is explicitly the
variance of one real sample. The matched filter reduces each record to

\[
u=\frac{\mathbf s^T\mathbf r}{\sigma\sqrt{\mathbf s^T\mathbf s}}.
\]

Under \(H_0\), \(u\) has mean zero and variance one. Under \(H_1\), it still
has variance one but its mean is

\[
d'=\frac{A\sqrt{\mathbf s^T\mathbf s}}{\sigma}=\sqrt{\mathrm{SNR}_{MF}},
\]

where the final equality uses this experiment's known positive signal polarity
(A>0). For an allowed signed amplitude, the more general relation is
(d'=\operatorname{sign}(A)\sqrt{\mathrm{SNR}_{MF}}).

The pulse samples add coherently in the numerator; independent noise adds in
power. That is why signal energy, observation duration, and SNR separate the
two distributions.

## Detection: a threshold creates an operating point

Declare a detection when \(u\geq\gamma\). With
\(Q(x)=\tfrac12\operatorname{erfc}(x/\sqrt2)\),

\[
P_{FA}=Q(\gamma),\qquad P_D=Q(\gamma-d').
\]

Lowering \(\gamma\) accepts more of both overlapping distributions: detections
increase and false alarms increase. Raising it rejects more of both. Sweeping
the threshold traces the ROC. The curve describes what this detector can trade
at this SNR; it does not select the best point by itself. False-alarm cost,
missed-target cost, revisit rate, and the number of searched cells belong to
the operating decision.

An empirical probability is a finite count divided by the number of
independent trials. A repeatable seed is useful, but it does not turn zero
observed false alarms into proof that \(P_{FA}=0\). P27's independent-trial
discipline still applies.

## Estimation: bias and variance are not ROC coordinates

When a target-present record is available, the pulse amplitude estimate is

\[
\hat A=\frac{\mathbf s^T\mathbf r}{\mathbf s^T\mathbf s}.
\]

For the stated known-waveform, known-timing, real-AWGN model,

\[
E[\hat A]=A,\qquad
\operatorname{var}(\hat A)=\frac{\sigma^2}{\mathbf s^T\mathbf s}.
\]

The Fisher information for amplitude is
\(I_A=(\mathbf s^T\mathbf s)/\sigma^2\), so the unbiased-estimator
Cramer-Rao lower bound (CRLB) is

\[
\operatorname{var}(\hat A)\geq\frac{1}{I_A}
=\frac{\sigma^2}{\mathbf s^T\mathbf s}.
\]

This linear estimator attains that bound under the exact model. Doubling a
same-amplitude pulse's coherent sample count doubles \(\mathbf s^T\mathbf s\)
and halves the bound. Lowering noise power at fixed amplitude and pulse energy
raises SNR and has the same inverse effect, which is the path swept in the
experiment. Raising SNR only by increasing the unknown true amplitude at fixed
noise does not change this absolute amplitude-variance bound; it improves
relative error instead. Bias is the mean signed error; variance is spread about
the estimator's own mean; and
\(\mathrm{RMSE}^2=\mathrm{variance}+\mathrm{bias}^2\). A low variance does not
excuse a large bias.

The CRLB is conditional on its assumptions. For delay estimation, information
depends on signal derivative energy, hence effective RMS bandwidth as well as
SNR and observation time. Unknown amplitude or phase, coarse delay grids,
model mismatch, boundary effects, and low-SNR outliers change the applicable
bound or prevent an estimator from approaching it. “Below the plotted bound”
usually signals bias, a convention mismatch, finite-trial fluctuation, or an
incorrect model—not super-resolution magic.

## The deliberately broken connection

The same matched-filter output drives detection and amplitude estimation.
Keeping only records with \(u\geq\gamma\) selects positive noise fluctuations.
The unconditional estimator is unbiased, but the detected-only sample mean is
biased upward. Detection has changed which population is being summarized.
The recovery is to report unconditional estimator performance on all
target-present trials, or explicitly label and model the conditional result.

This is why `P_D`, `P_FA`, bias, and variance belong in one lesson but not in
one interchangeable metric:

- `P_D` and `P_FA` describe threshold decisions under two hypotheses.
- bias and variance describe an estimator under a specified population/model.
- conditioning estimator reports on detector output couples the two and must
  be disclosed.

## Limiting cases

- Threshold \(\gamma\to-\infty\): both \(P_D\) and \(P_{FA}\) approach one.
- Threshold \(\gamma\to+\infty\): both approach zero.
- SNR \(\to0\): the two statistic distributions overlap and the ROC approaches
  the diagonal no-skill limit.
- Coherent energy grows or noise power falls: the distributions separate and
  the absolute amplitude CRLB falls inversely with information. Increasing only
  the true amplitude separates the detector distributions but leaves that
  absolute bound unchanged.
- Infinite independent trials: empirical probabilities and moments converge;
  one finite seeded run still fluctuates.
- Thresholding before estimation: the selected population remains biased even
  with many trials unless the conditioning is modeled.

## Common interpretation mistakes

- “A higher threshold improves the detector.” It reduces false alarms and
  detections; whether that is better depends on costs.
- “An ROC point is accuracy.” It is a pair of conditional probabilities, not a
  class-prevalence-weighted accuracy score.
- “Unbiased means precise.” An unbiased estimator may have large variance.
- “The CRLB is every estimator's observed variance.” It bounds unbiased
  estimators under a stated model and finite Monte Carlo results fluctuate.
- “Estimate only detections to remove bad samples.” That creates selection bias
  unless conditional performance is the declared quantity.
- “Seeded means independent.” The H0 and H1 banks must still contain distinct
  trials; reproducibility is not independence.

## DSP and radar connection

A radar cell under test produces a detection statistic and compares it with a
threshold. Later modules adapt that threshold with CFAR and validate very small
false-alarm rates. A detected cell may then become a range, Doppler, angle, or
amplitude estimate. The receiver must keep the detection operating point,
finite-trial evidence, estimator assumptions, and any detection-conditioned
bias visible when those reports feed a tracker.

Prerequisites: P27 for Monte Carlo independence, P08 for correlation, and P24
for matched-filter intuition. The experiment is an in-memory, bounded,
base-MATLAB synthetic model; it is not hardware or operational-radar evidence.
