# Walkthrough: separate background memory from target fades

Guiding question: Why do clutter and target amplitude fluctuate differently from white noise?

Complete [P40](../40-compare-coherent-and-noncoherent-integration/) first. Run
`experiment` from this module directory. The script has fixed array and loop
bounds, uses private seed `4101`, requires only base MATLAB, and creates six
figure groups tagged `P41`.

## 1. Baseline: inspect structure before averaging it away

Keep the visible controls unchanged: 96 range bins, 64 pulses, unit thermal
noise power, adjacent-range correlation `0.85`, slow-time correlation `0.92`,
and a clutter profile that decays from near to far range.

Inspect Figure 1 one transition at a time:

1. The power image contains patches that extend across neighboring range cells
   and persist over pulses. White noise alone would look like fresh grain.
2. The prescribed and measured clutter powers trend downward with range while
   the white-noise mean stays flat.
3. The range-mixed clutter amplitude has a wider tail because it pools cells
   with unequal scales.
4. One pulse shows related neighboring clutter amplitudes rather than an
   independent cell-to-cell sequence.

Expected observation: the console reports a near-range clutter mean power more
than twenty times the far-range value. The finite measured profile ripples
around the prescribed curve because correlated samples provide fewer
independent averages.

Common mistake: do not infer a local non-Gaussian clutter law from the pooled
histogram alone. The current local speckle is complex Gaussian; the aggregate
tail comes from mixing unequal range-dependent powers.

## 2. Baseline correlation: ask whether neighbors carry memory

Figure 2 calculates normalized correlation from explicit conjugate products.
The range panel compares clutter with thermal noise and the prescribed
`alpha^lag` curve. The slow-time panel does the same for `beta^lag`.

Expected observation: clutter correlation starts at one and decays gradually;
white-noise correlations away from lag zero fluctuate around zero. The seeded
finite field does not land exactly on every ensemble curve.

Common mistake: correlation is not the same as high power. A high-power white
process can remain uncorrelated, while a lower-power process can retain strong
memory.

## 3. Baseline targets: compare equal average SNR without hiding fades

Figure 3 gives every target law the same -3 dB ensemble average SNR. Their
finite seeded sample means differ slightly rather than being forced equal.
Read each panel in order:

1. The nonfluctuating target stays flat. Swerling I and III hold one random
   level throughout the displayed dwell. Swerling II and IV redraw every
   pulse.
2. Sixteen-pulse averaging narrows the Swerling II distribution but cannot
   narrow a Swerling I draw that was merely repeated.
3. The clean dwell-power coefficient of variation quantifies that visual
   spread.
4. The common noise-only threshold produces different target-present crossing
   rates despite equal average SNR.

Expected observation: fast models II and IV are more stable after sixteen
pulses than slow models I and III. Models III and IV also fluctuate less than
their I/II counterparts because their shape-two power law has lower variance.

Common mistake: Swerling I is not nonfluctuating. It is slow fluctuating: one
random power is fixed within a dwell and changes between dwells.

## 4. Sweep 1: change only adjacent-range correlation

Figure 4 changes `range_correlation_sweep = [0 0.50 0.85 0.97]`. It holds
range bins, pulses, innovation power, and the underlying seeded innovation
matrix fixed. Each case applies a different `alpha` to the same innovations,
so correlation is the only changed input.

Expected observation: measured correlation tracks the prescribed diagonal.
At zero, neighbors are independent apart from finite-sample error. Near 0.97,
patches span many cells and the effective number of independent range samples
is much smaller than the plotted cell count.

Common mistake: correlation does not create average power. The
`sqrt(1-alpha^2)` innovation scaling keeps the unit-field ensemble power fixed
while changing its memory.

## 5. Sweep 2: change only the number of averaged pulses

Figure 5 changes `integration_pulse_sweep = [1 2 4 8 16 32]`. For each length,
the script builds a noise-only empirical threshold at the same requested
reference rate and evaluates all target models with the same average power.

Expected observation: Swerling II clean-power variability trends toward
`1/sqrt(N)` and Swerling IV toward `1/sqrt(2N)`. Swerling I and III stay near
their one-draw limits because additional pulses repeat the same dwell power.
The threshold-crossing curves reflect both that variability and thermal noise.

Common mistake: this is not coherent integration. The statistic averages
`|x|^2`, so it does not align target phase. The sweep isolates amplitude-power
statistics introduced after P40.

## 6. Intentionally broken case: call heterogeneous clutter white

Figure 6 deliberately replaces the range-dependent expected background power
with one global mean, then applies the corresponding exponential-power
threshold everywhere.

Expected observation: near-range cells cross the broken threshold far too
often while far-range cells almost never cross it. One nominal threshold does
not create one false-alarm behavior when the background scale changes with
range.

Failure interpretation: the random draws are not defective. The processor
discarded known range dependence and used the stationary white-noise model
outside its assumptions.

## 7. Recovery: normalize the local background scale

The recovered path divides each cell power by its local expected clutter-plus-
noise power before comparing with the common normalized threshold:

\[
T_{p,r}=\frac{|c_{p,r}+w_{p,r}|^2}{P_c(R_r)+\sigma_w^2},
\qquad \gamma=-\log(P_{FA}).
\]

Expected observation: near and far background crossing rates return close to
the same 5% reference value in this known-model simulation.

Concept connection: the recovery works because the script knows the true local
mean. It is an oracle normalization, not a CFAR algorithm. An operational
detector must estimate its background without allowing a target, clutter edge,
or correlated samples to corrupt that estimate. Those tradeoffs belong to the
later CFAR modules.

## Safe interruption, reset, rollback, and recovery

The script has no background worker, timer, network call, file I/O, hardware
access, or persistent output. Every loop, array, sweep, and trial count is
bounded before allocation. If you interrupt it with `Ctrl+C`, rerun
`experiment`; `clearvars` removes partial workspace results, private seed
`4101` recreates the draws, and cleanup closes only figures tagged `P41`.

Repository rollback is isolated: remove the four P41 implementation artifacts,
restore the scaffold wording in its README, set only P41's manifest status back
to `scaffolded`, and revert the P41 catalog, test, and evidence changes.
Preserve P40, P42 identity, learner progress, and the operator-owned active-
batch activation.

## 8. Optional controlled edit

Change `slow_time_correlation` from `0.92` to `0.20` and rerun without changing
the range profile or `range_correlation`.

Expected observation: the range patches still exist within each pulse, but
they change much more rapidly down the pulse axis and the slow-time correlation
curve decays faster. Restore `0.92` before completing the checks.

## Completion checklist

- You can identify range dependence and memory separately from average power.
- You can explain the range and slow-time AR operations physically.
- You can distinguish slow Swerling I/III from fast Swerling II/IV.
- You can explain why equal average SNR does not guarantee equal dwell
  stability.
- You can diagnose the global-threshold failure and state why local
  normalization recovers only this known-model case.
