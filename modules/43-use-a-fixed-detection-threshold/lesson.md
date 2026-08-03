# P43 lesson: Use a Fixed Detection Threshold

Guiding question: **Why does a threshold that works in one noise level fail in another?**

## Physical model: one number becomes one decision

P42 produced bright and dim processed cells, but brightness alone was not a
detection rule. P43 reduces one range cell to a real, signed matched-filter
amplitude (x). The target polarity is known and positive, so the detector is

\[
x \mathop{\gtrless}_{H_0}^{H_1} \gamma,
\]

where (\gamma) is one positive threshold in native amplitude units. The two
hypotheses are deliberately explicit:

\[
H_0: x=n, \qquad H_1: x=A+n, \qquad n\sim\mathcal{N}(0,\sigma^2).
\]

This is not a magnitude or power detector. For a real one-sided statistic,
the target-absent false-alarm probability and target-present detection
probability are

\[
P_{FA}=Q\!\left(\frac{\gamma}{\sigma}\right), \qquad
P_D=Q\!\left(\frac{\gamma-A}{\sigma}\right),
\]

with (Q(u)=\tfrac12\operatorname{erfc}(u/\sqrt{2})). A miss is the complement
(P_{miss}=1-P_D). The script calibrates

\[
\gamma=\sigma_0 Q^{-1}(P_{FA,design})
\]

only once, at reference RMS (\sigma_0). Figure 2 shows the two conditioned
populations and the same vertical threshold.

False alarms are counted only among target-absent trials. Detections and misses
are counted only among target-present trials. Pooling every crossing into one
rate would change the denominators whenever target prevalence changed and
would no longer estimate either (P_{FA}) or (P_D).

## Baseline: absolute calibration works at its design point

At (\sigma=\sigma_0), the threshold is about 2.326 reference-noise RMS for the
chosen 1% design false-alarm probability. The positive target amplitude is
four reference-noise RMS, so most target-present samples cross while only the
upper tail of target-absent samples does.

Figure 1 supplies a finite range-profile view with known target labels. It is
useful for seeing individual crossings, but four target cells cannot estimate
a probability well. Figure 2 and the reported metrics therefore use 20,000
independent H0 trials and 20,000 independent H1 trials.

## Sweep 1: spreading the background changes both tails

The first sweep changes only (\sigma). Target amplitude (A), threshold
(\gamma), standard-normal samples, and trial count stay fixed. Therefore

\[
\frac{\gamma}{\sigma}
\]

shrinks as noise RMS grows. More target-absent samples reach the fixed
amplitude line, so (P_{FA}) rises. Because this experiment chooses
(A>\gamma), increasing the spread also moves more target-present samples below
the line, so misses rise. The common standardized samples make each change a
controlled scaling experiment rather than a comparison of lucky noise draws.

The limiting cases make the mechanism concrete. As (\sigma\to0), H0 collapses
at zero and H1 collapses at (A); because (0<\gamma<A), both false alarms and
misses approach zero. As (\sigma\to\infty), the finite offsets become small
relative to the spread and both one-sided crossing probabilities approach
one half. A fixed threshold therefore cannot preserve the 1% design value over
an arbitrary background scale.

## Sweep 2: shifting the background also breaks calibration

The second sweep keeps (\sigma=\sigma_0) and adds a positive clutter pedestal
(\mu_c) to both hypotheses:

\[
H_0:x=\mu_c+n, \qquad H_1:x=\mu_c+A+n.
\]

Now

\[
P_{FA}=Q\!\left(\frac{\gamma-\mu_c}{\sigma_0}\right).
\]

The clutter model is a visible mean shift, not a claim that all radar clutter
is Gaussian or constant. It isolates one fact: when a target-absent
distribution moves toward an absolute line, false alarms rise. Detection may
also rise because everything moved upward; that is not improved selectivity.
The false-alarm count reveals the cost.

For a large positive pedestal, both H0 and H1 cross almost always, so the
detector stops separating them. For a large negative pedestal, both cross
rarely. Operational clutter can be correlated, heavy-tailed, range-dependent,
and Doppler-dependent; later CFAR lessons introduce local background
estimation rather than treating this pedestal as a complete clutter model.

## Intentionally broken claim: hidden adaptation

The broken case divides each noise case by its known true RMS before applying
the threshold in normalized units. Algebraically its decision is

\[
\frac{x}{\sigma_{case}} > \frac{\gamma}{\sigma_0}.
\]

Its false-alarm probability stays constant because the effective native-unit
threshold is now proportional to (\sigma_{case}). That result is useful, but
it is not the fixed detector promised by P43. It uses background knowledge to
adapt every case. The script flags the fixed-threshold claim as false.

Recovery returns to (x>\gamma) in amplitude units and proves that every H0
decision matches the original sweep exactly. P45 will estimate local
background from training cells and make the adaptive rule explicit; dividing
by an oracle RMS here is only a preview, not a CFAR implementation.

## Assumptions, compatibility, and boundaries

- The target contribution has known positive polarity. A negative target or
  unknown phase requires a different statistic.
- A two-sided absolute-value detector would have
  (P_{FA}=2Q(\gamma/\sigma)); complex magnitude is Rayleigh and power is
  exponential under ideal complex Gaussian noise. Those formulas are not
  interchangeable with this lesson's one-sided real model.
- Trials are independent within each hypothesis. The two hypotheses use
  separate private-stream noise draws; sweeps reuse standardized draws only to
  isolate the changed parameter.
- The target is deterministic and does not fluctuate. P41's Swerling models
  would require averaging detection probability over target amplitude.
- Very small false-alarm probabilities require far more trials than this
  bounded visual lesson. P52 later performs dedicated false-alarm validation.
- The script uses base MATLAB operations, a private seed, five tagged figures,
  bounded arrays, and no external I/O or persistent state.
- This is a synthetic statistical model, not measured receiver calibration,
  complex range-Doppler detection, CFAR, hardware, HIL, field, or operational
  radar validation.

## Common interpretation mistakes

- A fixed normalized threshold is not a fixed amplitude threshold if the
  normalization changes with the background.
- More total threshold crossings do not mean better detection; H0 crossings
  are false alarms.
- Noise RMS, noise variance, and noise power are related but not identical:
  variance is (\sigma^2), while this amplitude threshold is measured against
  RMS (\sigma).
- The clutter-pedestal sweep changes the mean; the noise sweep changes the
  standard deviation. Both can break one absolute calibration by different
  mechanisms.
- A single plotted profile is not enough to estimate a rare-event
  probability; use conditioned repeated trials and retain their denominators.

## Dependencies and connection

[P28](../28-connect-thresholds-to-roc-curves-and-estimator-limits/) introduced
H0/H1 probability bookkeeping and threshold tradeoffs. [P41](../41-model-ground-clutter-and-swerling-targets/)
distinguished correlated clutter and fluctuating targets from white noise.
[P42](../42-create-a-full-range-doppler-map/) produced range-Doppler cells but
explicitly stopped before detection. P43 applies the first decision rule;
[P44](../44-build-an-empirical-radar-roc-curve/) will sweep the threshold and
[P45](../45-implement-1-d-cell-averaging-cfar/) will adapt it from neighboring
training cells.
