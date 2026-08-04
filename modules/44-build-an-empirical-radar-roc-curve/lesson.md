# P44 lesson: Build an Empirical Radar ROC Curve

Guiding question: **How does threshold choice trade probability of detection against false alarm?**

## Physical model: one threshold cuts two populations

P43 used one threshold at one operating condition. P44 keeps that same
one-sided statistic and moves the threshold through every plausible operating
point. A real known pulse `s` is observed in independent noise records:

\[
H_0:\;\mathbf r=\mathbf n, \qquad
H_1:\;\mathbf r=A\mathbf s+\mathbf n.
\]

The target polarity is known and positive. The script forms the matched-filter
statistic explicitly and normalizes its target-absent noise RMS to one:

\[
u=\frac{\mathbf s^T\mathbf r}{\sigma\sqrt{\mathbf s^T\mathbf s}}.
\]

For independent real Gaussian noise, this gives

\[
u\mid H_0\sim\mathcal N(0,1),\qquad
u\mid H_1\sim\mathcal N(d',1),
\]

where

\[
d'=\frac{A\sqrt{\mathbf s^T\mathbf s}}{\sigma}
   =\sqrt{\mathrm{SNR}_{MF}}.
\]

Because SNR is a power ratio, the amplitude separation is
`sqrt(10^(SNR_dB/10))`, not `10^(SNR_dB/10)`. This signed-amplitude convention
continues P43. A magnitude or square-law detector has different distributions
and must not borrow these formulas without changing the model.

Declare a target when `u > gamma`. With
\(Q(x)=\tfrac12\operatorname{erfc}(x/\sqrt2)\),

\[
P_{FA}=Q(\gamma), \qquad P_D=Q(\gamma-d').
\]

The experiment never hides these operations behind `perfcurve`, a detection
toolbox, or a CFAR helper.

## What an empirical ROC contains

For every threshold, the target-absent trials answer one question:

\[
\widehat P_{FA}=\frac{\text{H0 threshold crossings}}
                         {\text{H0 trials}}.
\]

The separate target-present trials answer another:

\[
\widehat P_D=\frac{\text{H1 threshold crossings}}
                    {\text{H1 trials}}.
\]

Pairing those conditional estimates while moving `gamma` traces an empirical
ROC. Lowering the threshold admits more of both populations, so both
probabilities rise. Raising it rejects more of both, so both fall. The ROC
therefore describes available tradeoffs; it does not declare one point best.

The endpoint `(1,1)` means an infinitely low threshold declares everything a
target. The endpoint `(0,0)` means an infinitely high threshold declares
nothing. The finite trial bank creates a stepwise curve between them. Several
thresholds may produce the same count, especially in a rare tail.

## Sweep 1: SNR changes detector quality, threshold chooses a point

The script holds the H0 population and threshold grid fixed while changing
matched-filter SNR from -6 to 12 dB. Higher SNR moves only the H1 mean to the
right. At a fixed `Pfa`, more H1 samples cross, so the ROC bows farther toward
the upper-left corner.

This separates two ideas:

- changing SNR, waveform energy, or noise changes the detector's ROC curve;
- changing threshold moves the operating point along one curve.

At SNR approaching zero, `d'` approaches zero and H0/H1 become indistinguishable;
the ROC approaches the diagonal. At very large SNR, the populations separate
and a broad threshold region gives high `Pd` with low `Pfa`.

## One operating point becomes a system burden

The marked threshold is the Gaussian-model point `Pfa = 0.001`, about 3.09
noise RMS. The empirical estimate uses 60,000 H0 opportunities, while the
analytic value is a reference for this exact model. Searching one million
independent target-absent cells gives the expected count

\[
E[N_{FA}]=N_{H0}P_{FA}=10^6\times10^{-3}=1000.
\]

This is an expectation, not a guarantee of exactly 1000 alarms in every scan.
It also counts target-absent opportunities; target-present cells do not become
false alarms. If independent-cell assumptions are justified, the probability
of at least one false alarm is `1-(1-Pfa)^N`, but real radar cells can be
correlated. The experiment therefore reports expected count without claiming
independence-based scan statistics.

An apparently small per-cell probability can still overload plot extraction,
clustering, association, or tracking when the search contains many cells. ROC
selection needs those downstream costs plus the cost of missed targets.

## Sweep 2: probability resolution is not certainty

One observed event changes an empirical probability by `1/N`. At 500 trials,
the resolution is 0.002, already larger than the designed `Pfa`. Zero observed
false alarms at that size cannot prove zero risk. Roughly, a binomial estimate
has standard error

\[
\sqrt{\frac{\widehat p(1-\widehat p)}{N}},
\]

and rare probabilities need many expected tail events for useful relative
precision. The nested 500, 2,000, 10,000, and 60,000 trial prefixes make the
estimate's movement visible without changing the detector. P52 later performs
the dedicated small-`Pfa` validation work; P44 does not claim that 60,000
trials establish operational rare-event performance.

## Intentionally broken case and recovery

The broken case first cherry-picks the 250 quietest H0 scores, chooses their
largest value as a threshold, and then evaluates that same bank. Zero training
crossings are guaranteed by construction. Calling that zero operational `Pfa`
is biased selection plus data reuse, not evidence. The held-out H0 bank exposes
crossings that the tuning bank could not reveal.

Recovery restores the threshold chosen before looking at the samples, uses the
full independent H0 and H1 banks, and regenerates both banks from a private
seed. Exact score and decision reproduction confirms deterministic recovery.
It does not remove Monte Carlo uncertainty or validate a physical receiver.

## Limiting cases

- `gamma -> -infinity`: `Pfa -> 1` and `Pd -> 1`.
- `gamma -> +infinity`: `Pfa -> 0` and `Pd -> 0`.
- matched-filter SNR `-> 0`: H0 and H1 overlap and the ROC approaches the
  no-skill diagonal.
- matched-filter SNR `-> infinity`: H1 separates and the curve approaches the
  upper-left corner.
- trial count `-> infinity`: empirical conditional probabilities converge to
  their model values if trials are representative and independent.
- searched-cell count grows at fixed `Pfa`: expected false alarms grow
  linearly even though the ROC curve itself is unchanged.

## Common interpretation mistakes

- “A higher threshold improves the detector.” It reduces both false alarms and
  detections; whether that is preferable depends on costs.
- “A higher-SNR curve is just a different threshold.” SNR changes population
  separation and therefore the curve; threshold selects a point on it.
- “No observed false alarms means `Pfa = 0`.” A finite run has resolution
  `1/N`; zero counts only constrain what that run observed.
- “Divide every threshold crossing by every trial.” `Pfa` is conditioned on H0
  and `Pd` is conditioned on H1, so their denominators stay separate.
- “One million cells changes the ROC.” Cell count changes operational alarm
  burden, not the per-cell detector curve.
- “The Gaussian dashed curve proves the radar.” It checks this synthetic model;
  clutter, mismatch, dependence, quantization, and unknown target phase change
  real behavior.

## DSP and radar connection

P43 established why a fixed native-unit threshold drifts when background scale
changes. P44 holds that model fixed long enough to map all threshold choices
and price one choice at scan scale. P45 begins adapting threshold to local
background, and P52 later validates CFAR false-alarm probability. Prerequisites
are P43 directly, with P27 for Monte Carlo discipline, P24 for matched
filtering, and P28 for the earlier general ROC connection.

The script is a bounded, in-memory, seeded base-MATLAB simulation. It performs
no file, network, device, hardware, real-time, or operational-radar work.
