# P27 Lesson: Use Monte Carlo Trials Instead of One Lucky Run

## Guiding question

Why is one noise realization not enough to judge an algorithm?

## Physical model

A receiver never gets to choose its next thermal-noise waveform. Even when the
transmitter, channel, and algorithm stay fixed, the next decision can differ
because the noise sample differs. One successful decision therefore describes
one event, not the probability of error.

P23 introduced BPSK symbols and P24 introduced matched filtering. P27 repeats
that transparent signal chain many times. A bit becomes
\(b_k\in\{-1,+1\}\), and a unit-energy pulse satisfies

\[
\sum_n p^2[n]=1.
\]

In trial \(k\), the received waveform is

\[
r_k[n]=\sqrt{E_b}\,b_kp[n]+w_k[n].
\]

The script explicitly correlates with the known pulse,

\[
z_k=\sum_n p[n]r_k[n],
\]

then decides \(+1\) when \(z_k\ge 0\) and \(-1\) otherwise. There is no
communications-toolbox detector hidden behind the decision.

## From outcomes to a probability estimate

Define the error indicator

\[
I_k=\begin{cases}1,&\hat b_k\ne b_k\\0,&\hat b_k=b_k.\end{cases}
\]

After \(N\) independent trials, the empirical BER is

\[
\hat P_e(N)=\frac{1}{N}\sum_{k=1}^{N} I_k.
\]

For coherent BPSK in real AWGN with variance \(N_0/2\), the reference result is

\[
P_e=Q\!\left(\sqrt{2E_b/N_0}\right)
=\frac{1}{2}\operatorname{erfc}\!\left(\sqrt{E_b/N_0}\right).
\]

The analytic curve is not inferred from the samples. It is an independent
model reference against which the finite Monte Carlo estimate can be checked.

## Why the running estimate wanders

The numerator is an integer error count. Early in a run, one new error changes
that count by a large fraction. Later, the same one error changes the average
only slightly. The running BER therefore jumps and wanders before it settles.
That motion is expected sampling variation, not algorithm instability.

For independent Bernoulli trials, the variance of the sample proportion is
approximately

\[
\operatorname{var}(\hat P_e)=\frac{P_e(1-P_e)}{N}.
\]

Uncertainty shrinks roughly as \(1/\sqrt{N}\), not \(1/N\). Reducing a typical
error bar by a factor of ten therefore takes about one hundred times as many
independent trials.

## The Wilson interval

A naive normal interval collapses to zero width when a short run observes zero
errors. P27 instead computes the 95% Wilson interval explicitly. With
\(\hat p=k/N\) and \(z=1.96\), its limits are

\[
\frac{\hat p+z^2/(2N)\ \pm\ z
\sqrt{\hat p(1-\hat p)/N+z^2/(4N^2)}}{1+z^2/N}.
\]

It remains finite at zero observed errors. “95%” describes long-run coverage
under the model assumptions; it is not a 95% guarantee that this particular
interval contains the truth.

## Independence is part of the experiment

The broken case selects one correctly decoded noisy waveform and repeats it
4,000 times. The report says zero errors, and blindly inserting \(N=4000\)
into a binomial interval makes that report look precise. But every statistic is
identical: the effective number of independent noise trials is one.

This is **pseudo-replication**. Repeated array entries, repeated plots, or
repeated processing of the same capture do not create new random evidence.
Confidence formulas based on independent Bernoulli trials no longer apply.

A reproducible seed solves a different problem. Seed 2701 lets another learner
reconstruct the same bank of independent pseudorandom draws and audit the
calculation. The seed does not certify that the bank is representative, so the
analytic reference and uncertainty checks still matter.

## Reading the two sweeps

The trial-count sweep uses prefixes of one fixed independent bank. Only \(N\)
changes. Short prefixes can land well above or below the analytic BER; longer
prefixes narrow the Wilson interval and usually settle closer to the model.

The \(E_b/N_0\) sweep keeps the symbols and normalized noise samples fixed and
changes only noise scale:

\[
\sigma=\sqrt{\frac{E_b}{2\,10^{(E_b/N_0)_{\mathrm{dB}}/10}}}.
\]

Using common random numbers makes the comparison controlled. More energy per
bit relative to noise separates the \(+1\) and \(-1\) matched-filter statistic
distributions, so fewer samples cross the zero decision boundary.

## Limiting cases

- **One trial:** the estimate is exactly zero or one. Neither value
  characterizes the underlying probability.
- **Many independent trials:** the empirical BER converges toward the true BER
  under the assumed stationary model.
- **\(E_b/N_0\to 0\):** the two hypotheses become indistinguishable and BER
  approaches 0.5.
- **\(E_b/N_0\to\infty\):** BER approaches zero, but zero errors in a finite
  run establishes an upper bound rather than proving exact zero.
- **Rare errors:** estimating a small BER requires enough trials to observe
  enough errors. A large nominal count with no independence is not enough.
- **Correlated or changing trials:** the ordinary binomial variance and Wilson
  interpretation no longer apply directly; effective sample size and the
  changing operating condition must be modeled.

## Common interpretation mistakes

- “The seed made the result statistically valid.” A seed makes it repeatable,
  while independence and adequate trial count make it informative.
- “Zero observed errors means zero BER.” It means the finite run observed none.
- “The running curve should decrease smoothly.” Error indicators arrive
  randomly, so a correct cumulative estimate wanders.
- “A narrow interval proves the model.” The interval is conditional on the
  trial model, especially independence and stationarity.
- “Four thousand copies are four thousand trials.” Copies contain one
  realization's information.
- “A Monte Carlo match validates hardware.” This synthetic normalized model
  says nothing by itself about RF impairments, calibration, or field behavior.

## DSP and radar connection

The same discipline applies to BER, estimator RMSE, probability of detection,
false-alarm probability, tracking loss, and CFAR validation. Later modules use
Monte Carlo trials for radar statistics, but the foundation is already here:
define one trial, vary the random input independently, retain the operating
condition, report uncertainty, and distinguish reproducibility from evidence
volume.
