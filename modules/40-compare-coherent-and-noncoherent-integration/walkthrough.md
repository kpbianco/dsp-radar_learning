# Walkthrough: decide whether the pulse arrows share a direction

Guiding question: When should pulse phases be added and when should magnitudes be added?

Complete [P39](../39-expose-blind-speeds-and-use-staggered-prf/) first. Run `experiment` from this module directory. The script has fixed array and loop bounds, uses private seed `4001`, requires only base MATLAB, and creates four figure groups tagged `P40`.

## 1. Baseline: align the phase before adding

Keep the visible controls unchanged: 32 pulses, target amplitude 1, single-pulse SNR -8 dB, and a nominal 35-degree phase increment per pulse.

In Figure 1, inspect one transition at a time:

1. The raw I/Q samples wander because the target rotates and the single-pulse noise is stronger than the target.
2. Multiplication by the conjugate phase reference stops the clean target rotation, aiming it along positive I.
3. The cumulative complex-sum magnitude trends upward because aligned target amplitudes add in one direction.
4. The cumulative power also rises, but its noise-only mean rises too. Noncoherent processing is accumulating evidence, not canceling noise phasors.

Expected observation: the console reports a stable-phase coherent output SNR near 7.05 dB, which is -8 dB plus `10 log10(32)`. The observed one-realization statistics vary with the deterministic noise draw; the analytical trend does not.

Common mistake: do not compare the raw value of `abs(coherent_sum)^2` directly with `sum(abs(x).^2)`. Their noise-only means and variances differ. Figure 2 uses a common standardized separation for the fair comparison.

## 2. Sweep 1: change only integrated pulse count

Figure 2 uses `pulse_count_sweep = [1 2 4 8 16 32 64]` while holding target amplitude, single-pulse SNR, and perfect alignment fixed.

- The upper panel shows coherent output SNR increasing by 3.01 dB for every doubling of `N`.
- The lower panel compares detectability `d`: coherent `d=N*rho`, noncoherent power `d=sqrt(N)*rho`.

Expected observation: both methods coincide at one pulse. Beyond one pulse, the coherent curve separates more rapidly because the known target phase creates useful cross-pulse terms.

Common mistake: the lower noncoherent curve does not mean power integration loses target energy. It means its always-positive noise power fluctuates too, making target-present and noise-only data harder to separate.

## 3. Sweep 2: change only phase-jitter standard deviation

Figure 3 keeps 32 pulses and -8 dB single-pulse SNR fixed. It changes only independent Gaussian phase-jitter standard deviation through 0, 5, 15, 30, 60, 90, 120, and 180 degrees. The plotted coherent curve is the ensemble expectation `1+(N-1)*exp(-sigma_phi^2)`, not one lucky phase realization.

Expected observation: coherent output approaches its ideal value near zero jitter and falls toward the single-pulse SNR as phase uncertainty grows. The normalized target contribution to noncoherent power stays at one because rotation does not change magnitude.

Common mistake: “phase-insensitive” does not mean “more efficient.” It means the statistic does not depend on arrow direction. Figure 2 shows the efficiency cost under the stated noise model.

## 4. Intentionally broken case: trust only the nominal phase

Figure 4 applies the repeated residual phase cycle `[0 90 180 -90]` degrees after the nominal target phase. Those four unit phasors sum exactly to zero.

The broken processor removes only the nominal 35-degree progression and assumes the residual errors do not exist. Its cumulative coherent sum repeatedly returns to zero even though every pulse contains the same target magnitude.

Expected observation: the final broken coherent signal-power fraction is zero, while noncoherent signal energy remains one.

Failure interpretation: the target did not disappear from individual pulses. The processor destroyed its own target contribution by adding complex samples under a false phase model.

## 5. Recovery: use the actual pulse phase, or stay noncoherent

The recovered path removes both the nominal phase and the known residual error:

\[
x_ne^{-j\phi_n}e^{-j\epsilon_n}.
\]

Expected observation: the cumulative magnitude grows exactly to `N A`, the recovered coherent signal-power fraction becomes one, and the noncoherent energy fraction remains one before and after correction.

Concept connection: phase is valuable information only when it is referenced. If pulse phase can be tracked, align and add complex samples. If it cannot, retain honest phase-insensitive evidence rather than forcing an invalid coherent sum.

## Safe interruption, reset, rollback, and recovery

The script has no background worker, timer, network call, file I/O, hardware access, or persistent output. All arrays and sweeps are bounded before allocation. If you interrupt it with `Ctrl+C`, rerun `experiment`; `clearvars` removes partial workspace results, the private seed recreates the same noise, and cleanup closes only figures tagged `P40`.

Repository rollback is isolated: remove the four P40 implementation artifacts, restore the scaffold wording in its README, set only P40's manifest status back to `scaffolded`, and revert the P40 catalog, test, and evidence changes. Preserve P39, P41 identity, learner progress, and the operator-owned active-batch activation.

## 6. Optional controlled edit

Change `input_snr_db` from `-8.0` to `-4.0` and rerun without changing pulse count or phase controls.

Expected observation: both detectability curves shift upward because each pulse is stronger relative to noise, but their `N` versus `sqrt(N)` slopes and the normalized phase-jitter loss remain unchanged. Restore -8 dB before completing the checks.

## Completion checklist

- You can identify the conjugate phase-alignment operation before the complex sum.
- You can explain why stable coherent output SNR grows by `N`.
- You can explain why the noncoherent power statistic needs a different normalization.
- You can point to the jitter sweep where coherent cross-pulse benefit disappears.
- You can diagnose the broken case and state both valid recovery choices.
