# Lesson: phase is information only when its reference is trustworthy

## Guiding question

When should pulse phases be added and when should magnitudes be added?

## Physical mental model

Imagine each pulse return as an arrow in the I/Q plane. A target with predictable phase produces arrows whose directions can be rotated onto one common axis. Add those aligned arrows and the target grows in one direction while random noise partly cancels. That is coherent integration.

If the pulse phases are unknown, adding the arrows can make a real target cancel itself. Squaring each arrow length and adding the powers avoids that cancellation. The cost is that noise power is also always positive, so target-present and noise-only results separate more slowly. That is noncoherent power integration.

P40 depends on [P39](../39-expose-blind-speeds-and-use-staggered-prf/): P39 processed each uniform-PRI dwell coherently but fused separate PRF decisions noncoherently. Here we isolate that choice and measure its consequence.

## One model, two statistics

For pulse `n`, use the complex range-bin sample

\[
x_n=Ae^{j(\phi_n+\epsilon_n)}+w_n,
\]

where `A` is target amplitude, `phi_n` is the predicted phase history, `epsilon_n` is untracked phase error, and `w_n` is circular complex noise with mean power `sigma_w^2`.

When `phi_n` is known, align before adding:

\[
z_c=\sum_{n=0}^{N-1}x_ne^{-j\phi_n}.
\]

With `epsilon_n=0`, target amplitude grows as `N`, target power as `N^2`, and noise power as `N`. The single-pulse SNR is defined by the displayed relation below.

\[
\rho=\frac{A^2}{\sigma_w^2}, \qquad
\mathrm{SNR}_{c,\mathrm{out}}=N\rho.
\]

When phase is not trustworthy, P40 uses the explicit power statistic

\[
T_{nc}=\sum_{n=0}^{N-1}|x_n|^2.
\]

This is phase-insensitive, but it is not an unbiased estimate of coherent output SNR. To compare the two differently distributed statistics, the experiment uses the noise-only standardized mean separation, or detectability index `d`. For the coherent power statistic `T_c=|z_c|^2` and the noncoherent power statistic above,

\[
d_c=N\rho, \qquad d_{nc}=\sqrt{N}\rho.
\]

Both start at the same single-pulse value. Under this simple known-amplitude model, coherent separation grows linearly with pulse count while power-statistic separation grows with its square root. Detection probability at a chosen false-alarm rate would require the full statistic distributions and belongs to later ROC/CFAR modules.

## Why phase jitter removes coherent gain

For independent zero-mean Gaussian phase error with standard deviation `sigma_phi` radians,

\[
E\{|\textstyle\sum e^{j\epsilon_n}|^2\}
=N+N(N-1)e^{-\sigma_\phi^2}.
\]

After division by the integrated noise power, the coherent SNR gain relative to one pulse is

\[
G_c=1+(N-1)e^{-\sigma_\phi^2}.
\]

At zero jitter, `G_c=N`. As phase becomes effectively random, the cross-terms vanish and `G_c` approaches 1: adding more untracked phasors supplies no ensemble coherent gain. The target contribution to `sum(|x_n|^2)` stays `N A^2`, so its phase-insensitive evidence is unchanged.

## What the four figure groups mean

1. **Baseline pulse integration:** raw noisy I/Q samples, phase-aligned samples, the cumulative complex sum, and cumulative power against noise-only and target-present means.
2. **Pulse-count sweep:** coherent output SNR and a fair detectability comparison as only `N` changes.
3. **Phase-jitter sweep:** expected coherent loss from the Gaussian phase-error model while noncoherent signal energy stays normalized to one.
4. **Broken model and recovery:** an intentionally severe quadrature phase cycle cancels the nominally aligned complex sum; removing the actual pulse errors restores it. Power evidence is unchanged in both cases.

## When to choose each operation

- Add complex samples coherently when pulse timing, Doppler compensation, oscillator phase, and calibration provide a defensible common phase reference.
- Add magnitudes or powers noncoherently when only phase-insensitive evidence is comparable across looks, such as independently processed dwells with an unreliable phase relationship.
- If a phase estimator becomes available and its error is small enough, align with it and regain coherent benefit.
- Do not create a phase reference by assumption. A wrong reference can be worse than discarding phase honestly.

## Limiting cases and model boundary

- `N=1`: coherent and noncoherent processing have no integration advantage.
- Perfect phase with `N>1`: coherent output SNR gains `10 log10(N)` dB.
- Effectively random phase: coherent gain approaches one pulse, while accumulated power still contains all `N A^2` target energy.
- Zero noise: both statistics contain target evidence, but coherent addition still depends on alignment.
- Zero target amplitude: power accumulation remains positive because it accumulates noise; a positive statistic alone is not proof of a target.
- Known pulse-by-pulse phase error: exact derotation recovers the ideal coherent sum in this model.

The experiment models one complex range bin, constant target amplitude, independent complex Gaussian noise, and either a known nominal phase or prescribed phase error. It omits amplitude fluctuation, clutter correlation, phase-estimation error, acceleration, range migration, threshold selection, and probability of detection. P41 adds fluctuating targets and clutter; later detection modules add thresholds and ROC behavior.

## Common interpretation mistakes

- **“Coherent means sum magnitudes.”** No. Coherent integration preserves I/Q, aligns phase, and then sums complex values.
- **“Power integration has the same output SNR formula.”** No. Its noise-only distribution differs, so P40 labels its standardized separation `d`, not a coherent SNR estimate.
- **“Jitter reduces every pulse magnitude.”** In this model it rotates pulse arrows without changing their lengths. The loss appears in cross-pulse complex addition.
- **“The broken quadrature cycle is typical random jitter.”** It is a deterministic worst-case teaching pattern chosen to make cancellation exact and visible.
- **“More pulses always help coherently.”** Only if the phase model remains valid over the integration interval.
