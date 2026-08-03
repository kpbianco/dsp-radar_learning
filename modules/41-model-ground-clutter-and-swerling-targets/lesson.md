# Lesson: the average power hides memory and fluctuation

## Guiding question

Why do clutter and target amplitude fluctuate differently from white noise?

## Physical mental model

Thermal noise is like fresh grain on every pixel of every pulse: knowing one
sample does not help predict its neighbor. Ground clutter is the return from a
physical surface. Adjacent range cells illuminate related terrain, nearby
scatterers form patches, and the surface changes slowly during a short dwell.
Its power also changes with range. That gives clutter both a spatial envelope
and memory.

A target is different again. Its radar cross section is the coherent sum of
returns from body parts. Small aspect or frequency changes can rearrange those
parts from reinforcement to cancellation. Swerling models do not explain the
geometry; they provide simple power distributions and say whether a draw is
held for a dwell or redrawn each pulse.

P41 depends on [P40](../40-compare-coherent-and-noncoherent-integration/).
P40 formed a phase-insensitive average of pulse powers. P41 shows why that
average can converge quickly for one target model and remain unstable for
another.

## White noise and the clutter field

The complex thermal-noise samples are independent circular Gaussian values

\[
w_{p,r}\sim\mathcal{CN}(0,\sigma_w^2),
\qquad E\{w_{p,r}w^*_{q,s}\}=0
\quad\text{when }(p,r)\ne(q,s).
\]

The experiment builds unit-power clutter speckle explicitly with two AR(1)
operations. First, range correlation is introduced:

\[
u_{p,r}=\alpha u_{p,r-1}+\sqrt{1-\alpha^2}\,e_{p,r}.
\]

Then the field is given slow-time memory:

\[
g_{p,r}=\beta g_{p-1,r}+\sqrt{1-\beta^2}\,u_{p,r}.
\]

Here `e` is fresh unit-power complex Gaussian innovation, `alpha` is
adjacent-range correlation, and `beta` is pulse-to-pulse correlation. A
range-dependent mean-power profile scales that speckle:

\[
P_c(R)=P_{\mathrm{floor}}+P_{\mathrm{near}}
\left(\frac{R}{R_{\mathrm{near}}}\right)^{-\eta},
\qquad c_{p,r}=\sqrt{P_c(R_r)}\,g_{p,r}.
\]

This is a teaching model, not a universal land-clutter law. It makes three
properties visible: mean power varies with range, neighboring cells are
correlated, and the background changes slowly from pulse to pulse. Thermal
noise has none of those properties here.

## Why the amplitude histogram needs context

At one range with fixed `P_c`, the modeled complex Gaussian speckle has a
Rayleigh amplitude distribution, just as circular complex thermal noise does
after its own scaling. But pooling cells from many unequal values of `P_c(R)`
creates a scale mixture with a wider tail. The baseline histogram deliberately
shows that aggregate nonstationarity.

A heavy-looking aggregate histogram therefore does not by itself prove a
non-Gaussian local scatterer law. Inspect the power profile and correlation as
well as the histogram. Real ground clutter may also require compound-Gaussian,
lognormal, Weibull, or measured-data models; P41 does not claim those.

## The four Swerling-like power models

Let `Pbar` be the same average target power for every model. The nonfluctuating
target uses `P=Pbar` every pulse and dwell.

Swerling I and II use exponential target power:

\[
f_P(p)=\frac{1}{\bar P}e^{-p/\bar P},\quad p\ge0,
\qquad P=-\bar P\log U,
\]

where `U` is uniform on `(0,1)`. Swerling I draws once and holds that target
power for every pulse in a dwell. Swerling II redraws it independently each
pulse.

Swerling III and IV use a gamma shape-two power law:

\[
P=-\frac{\bar P}{2}\log(U_1U_2),
\qquad \operatorname{var}(P)=\frac{\bar P^2}{2}.
\]

Swerling III holds one draw per dwell; Swerling IV redraws each pulse. Models
III and IV fluctuate less deeply than I and II because their power variance is
half as large. These labels describe idealized fluctuation cases, not target
classes or guaranteed operational behavior.

## Same average SNR, different dwell stability

All five models are parameterized with the same ensemble average power, so

\[
\overline{\mathrm{SNR}}=\frac{\bar P}{\sigma_w^2}
\]

is equal. Their finite seeded sample means differ slightly, as independent
Monte Carlo estimates should. For `N` pulses, the clean noncoherent
target-power average is

\[
\bar P_N=\frac{1}{N}\sum_{p=1}^{N}P_p.
\]

For a fast exponential model, its coefficient of variation falls as
`1/sqrt(N)`. For fast gamma shape two, it falls as `1/sqrt(2N)`. A slow model
holds one draw, so repeating that same fade does not average it away: Swerling
I remains near coefficient of variation one and Swerling III near
`1/sqrt(2)`. The nonfluctuating target stays at zero.

The experiment uses a seeded, empirical noise-only threshold only as a common
stability ruler. It is not a CFAR design or a complete ROC study. Later modules
derive and validate detectors. Here the important result is that equal average
SNR does not guarantee equal fractions of target-present dwells above the same
reference.

## What the six figure groups mean

1. **Baseline background structure:** power versus range and pulse, prescribed
   and measured profiles, aggregate amplitudes, and one range snapshot.
2. **Background correlation:** explicit normalized range and slow-time
   correlations for clutter and white noise.
3. **Target fluctuation baseline:** one dwell, dwell-power distributions,
   coefficients of variation, and common-threshold crossing rates.
4. **Range-correlation sweep:** measured adjacent-bin correlation while only
   `alpha` changes.
5. **Integration-length sweep:** stability and threshold crossings while only
   the averaged pulse count changes.
6. **Broken background model and recovery:** one global background mean creates
   range-biased crossings; local expected-power normalization restores a
   uniform reference rate.

## Limiting cases and model boundary

- `alpha=0`: range innovations are independent; prescribed adjacent-bin
  correlation is zero.
- `alpha` approaching one: neighboring range cells become nearly the same
  speckle, so many plotted cells do not mean many independent samples.
- `beta=0`: each pulse gets a fresh clutter field; `beta` approaching one makes
  clutter nearly frozen over the dwell.
- Flat `P_c(R)`: pooling range cells no longer creates a mixture of unequal
  local clutter scales.
- `N=1`: slow and fast members of each Swerling pair have the same one-pulse
  marginal power distribution.
- Large `N`: fast-model dwell averages stabilize; slow-model fades remain.
- Zero target power: target-present statistics reduce to noise-only statistics.
- Zero clutter: local normalization reduces to the familiar stationary white
  noise power model.

The experiment omits antenna pattern, terrain maps, grazing angle, Doppler
spectrum, platform motion, polarization, shadowing, coherent target phase,
range migration, compound clutter texture, interference, CFAR estimation,
and calibrated probability-of-detection claims. The fields and target powers
are synthetic. P42 adds a range-Doppler map; P43 and later modules develop
threshold and CFAR behavior.

## Common interpretation mistakes

- **“Clutter is just louder white noise.”** No. Its local power changes with
  range and its samples have range and slow-time memory.
- **“A Rayleigh local amplitude law means clutter and noise are identical.”**
  No. Correlation and nonstationarity remain different even when a marginal
  amplitude family matches after local scaling.
- **“Swerling I means the target is constant.”** It is constant only within a
  dwell; its dwell-to-dwell power is exponential.
- **“More pulses remove every fade.”** They average independent fast
  fluctuations, not a slow draw repeated through the dwell.
- **“Equal average SNR means equal detection probability.”** Averages omit the
  fluctuation distribution and the detector statistic.
- **“The broken global threshold is a CFAR implementation.”** It is an
  intentionally invalid stationary-background assumption used to motivate
  local normalization.
