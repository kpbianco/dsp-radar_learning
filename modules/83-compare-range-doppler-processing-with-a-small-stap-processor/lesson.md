# P83 lesson: Follow the Clutter Ridge in Space and Slow Time

## Guiding question

When is Doppler filtering alone insufficient against clutter?

## Physical mental model

An airborne radar does not see stationary ground at one Doppler. Ground to the
left, broadside, and right has different line-of-sight velocity relative to the
moving platform. Each ground direction therefore contributes a different
spatial phase slope across the array and a linked pulse-to-pulse phase slope.
Those pairs form an angle-Doppler **ridge**.

A conventional range-Doppler processor in this lesson first points one fixed
beam and then tries Doppler frequencies one at a time. Its spatial response is
the same for every Doppler. If clutter from a direction inside that broad beam
has the target's Doppler, the Doppler filter cannot tell them apart.

The small STAP processor sees one 32-number snapshot: 4 array elements times 8
pulses. It learns which combinations of spatial and slow-time phase occur in
neighboring target-free range cells, then suppresses those combinations while
preserving the requested target pair.

## The already range-compressed data

Each relative range cell contains a matrix (X_r) with array element down rows
and pulse number across columns. P83 starts after waveform matched filtering;
it does not create range resolution. MATLAB column ordering makes the joint
snapshot

\[
\mathbf{x}_r = \operatorname{vec}(\mathbf{X}_r)
\in \mathbb{C}^{MN}, \qquad M=4,\quad N=8.
\]

This ordering matters. Element samples for pulse 1 come first, followed by the
elements for pulse 2. The matching steering vector is

\[
\mathbf{s}(\theta,\nu)
= \mathbf{d}(\nu)\otimes\mathbf{a}(\theta),
\]

where

\[
a_m(\theta)=e^{j2\pi(d/\lambda)m\sin\theta},\qquad
d_n(\nu)=e^{j2\pi n\nu}.
\]

Here (\nu=f_D/\mathrm{PRF}) is cycles per pulse. Positive (\nu) means positive
pulse-to-pulse complex phase rotation under the experiment's sign convention.

## Why moving ground forms a ridge

For the narrowband side-looking teaching geometry, a ground patch at angle
(\theta) has

\[
\nu_c(\theta)=
\frac{2v_p}{\lambda\,\mathrm{PRF}}\sin\theta.
\]

The baseline uses (v_p=90\ \mathrm{m/s}), (\lambda=0.03\ \mathrm{m}), and
PRF (20\ \mathrm{kHz}), so the slope is 0.30 cycles per pulse per
(\sin\theta). The target at (12.5^\circ,0.125) is only about 0.060 cycles per
pulse above its same-angle ground return. Ground from another angle also lies
near (\nu=0.125). Thus neither marginal coordinate is clean, although the
target's joint pair is distinct.

## The conventional reference processor

At each trial Doppler, the conventional path uses a fixed 12-degree spatial
look and a slow-time matched filter. In joint notation its weight is simply

\[
\mathbf{w}_{RD}=\frac{\mathbf{s}}{\mathbf{s}^H\mathbf{s}}.
\]

This is a separable fixed beam and Doppler filter, not an adaptive clutter-ridge
notch. It consumes exactly the same 4-by-8 samples as STAP. The comparison does
not give STAP extra aperture or coherent time.

For map display, conventional output power is divided by its expected output
power under the loaded neighboring-range covariance:

\[
T_{RD}=\frac{|\mathbf{w}_{RD}^H\mathbf{x}|^2}
{\mathbf{w}_{RD}^H\widehat{\mathbf{R}}_L\mathbf{w}_{RD}}.
\]

This makes a dimensionless normalized-power map. It is not a calibrated
detection statistic or probability of detection.

## Learn the joint covariance from neighboring range

The guarded cell under test is range cell 25. Two cells on either side are not
eligible for training. The reviewed clean secondary cells are 5–22 and 28–45,
giving 36 snapshots:

\[
\widehat{\mathbf{R}}
=\frac{1}{L}\sum_{\ell=1}^{L}
\mathbf{x}_\ell\mathbf{x}_\ell^H,
\qquad L=36.
\]

The covariance is not supplied by the known synthetic scene model. It is
estimated from the realized neighboring range data. The analytical clutter
plus noise covariance is retained only as a simulated ruler for output SCNR.

Thirty-six samples for a 32-dimensional problem is deliberately small. A
little diagonal loading makes the solve less brittle:

\[
\widehat{\mathbf{R}}_L
=\widehat{\mathbf{R}}
+\alpha\frac{\operatorname{tr}(\widehat{\mathbf{R}})}{MN}\mathbf{I},
\qquad \alpha=0.05.
\]

Loading is a robustness trade, not new information. Too little trusts a noisy
covariance; too much moves back toward a fixed matched filter.

## The small STAP operation

For each trial Doppler, the script exposes the two steps

\[
\mathbf{q}=\widehat{\mathbf{R}}_L^{-1}\mathbf{s},\qquad
\mathbf{w}_{STAP}=\frac{\mathbf{q}}{\mathbf{s}^H\mathbf{q}}.
\]

The denominator enforces (\mathbf{w}_{STAP}^H\mathbf{s}=1) for the assumed
signature. No matrix inverse is formed; the backslash solve applies the
operation directly. The adaptive-map value is the normalized matched-filter
form

\[
T_{STAP}=
\frac{|\mathbf{s}^H\widehat{\mathbf{R}}_L^{-1}\mathbf{x}|^2}
{\mathbf{s}^H\widehat{\mathbf{R}}_L^{-1}\mathbf{s}}.
\]

Both maps therefore use dimensionless normalized output power and the same
color limits. The separate target-to-background contrast numbers compare each
target cell with that processor's map median after excluding the guarded
target neighborhood.

## What the baseline demonstrates

The fixed-beam range-Doppler map is clutter-dominated: its global maximum is
not the target grid cell. The clean adaptive map makes range cell 25 at
normalized Doppler 0.120 its maximum. A known-component calculation also
compares target power with the exact synthetic clutter-plus-noise covariance.
That SCNR ruler is useful because one lucky noisy map cell can otherwise
confuse visibility with average performance.

STAP is not merely subtracting more total power. It changes the response as a
function of the joint angle-Doppler signature. A fixed Doppler notch would
remove every angle at that Doppler, including the target.

## Controlled change 1: distance from the ridge

The ridge-offset sweep uses `[0.01 0.03 0.06 0.10]` cycles per pulse at the
same target angle and holds clutter, training, target power, array, CPI, and
loading fixed. Close to the ridge, target and clutter signatures become nearly
the same and both processors struggle. Farther away, the joint processor has
room to place a clutter notch while preserving the target.

At exact overlap, no linear processor can both satisfy
(\mathbf{w}^H\mathbf{s}=1) and (\mathbf{w}^H\mathbf{s}=0). STAP cannot repeal
identifiability.

## Controlled change 2: clean training support

The support sweep uses prefixes `[8 16 24 36]` of one unchanged clean record.
With fewer than 32 snapshots, the unregularized sample covariance is rank
deficient. Loading permits a solve, but the learned clutter subspace is
uncertain. More homogeneous, independent support improves the reviewed SCNR.

More cells are not automatically better. Farther range cells may contain a
different clutter distribution; many wrong examples estimate the wrong
covariance confidently.

## Intentionally contaminated training

The broken path adds a strong target-like signature to 25% of the training
cells. The assumed constraint is at `(12 deg, 0.120)`, while the actual and
contaminating signature is `(12.5 deg, 0.125)`. The processor still has unit
response to the assumed vector. In this deterministic case, desired-target
output power changes by only about `-0.62 dB`; the dominant failure is that
known clutter-plus-noise output rises by about `22.86 dB`. The contaminated
covariance has taught a poor interference-rejection response, and the adaptive
normalization no longer gives the actual target useful contrast. Another map
cell wins.

Recovery does not try to subtract the injected training corruption. It
discards the broken covariance, reuses the retained clean training matrix and
unchanged measurement, and exactly reproduces the baseline map and metrics.
This is deterministic processing recovery, not a database or device rollback.

## Limiting cases

- If platform speed is zero, the ridge collapses toward zero Doppler.
- If the array has one element, spatial discrimination disappears.
- If there is one pulse, Doppler discrimination disappears.
- If target and clutter steering are identical, perfect preservation and
  perfect rejection are contradictory.
- If training support is below dimension, the unregularized covariance is
  rank deficient; loading allows a solve but does not supply missing samples.
- If training cells contain targets or different terrain, covariance adaptation
  can suppress desired energy, amplify residual interference, or distort the
  normalized adaptive score. P83's reviewed failure is primarily interference
  amplification, not a desired-signal null.
- If element spacing exceeds half a wavelength, spatial aliases can repeat.
- If `|nu| >= 0.5`, slow-time Doppler aliases.
- A longer CPI sharpens Doppler selectivity; STAP itself does not create more
  Doppler resolution.
- More range cells do not improve range resolution because these snapshots are
  already range compressed.

## Common interpretation mistakes

- Calling the conventional reference "Doppler only" while forgetting its
  fixed spatial beam; the missing capability is joint *adaptive* response.
- Comparing independently autoscaled colors as absolute clutter suppression.
- Reading normalized map power as probability of detection.
- Assuming the analytical covariance was used to design the weights.
- Treating diagonal loading as extra training data.
- Equating target-bin visibility in one draw with average output SCNR.
- Assuming every neighboring range cell is homogeneous and target free.
- Claiming STAP improves range or Doppler resolution.
- Calling a synthetic four-element processor operational radar validation.

## Dependencies and claim boundary

P37 and P42 established pulse-Doppler data and maps; P41 introduced ground
clutter; P61/P63 introduced ULA phase and fixed beams; P65 introduced loaded
MVDR; and P68 introduced the angle-Doppler clutter ridge and Kronecker
steering. P82 is the governed sequential prerequisite.

The source targets base MATLAB R2016b+ and uses no toolbox or external data.
Static checks and an independent equation oracle may validate contracts and
simulated behavior. They are not MATLAB runtime, physical radar/HIL, bench,
field, real-time, RT1/RT2, Unreal, signing, deployment, or production evidence.
