# Walkthrough: see a blind target disappear, then move the null

Guiding question: Why can a moving target vanish in an MTI radar?

Run `experiment.m` and keep the controls at their defaults for the first pass. Change one requested control at a time so each plot has one physical cause.

## 1. Baseline: one moving target, two sampling schedules

The target velocity is set to the first positive blind speed of the 4.0 kHz primary PRF. Read the console values for wavelength, both first blind speeds, target Doppler, and normalized gains.

In Figure 1, compare the sampled phases and the target-only canceller outputs.

Expected observation: the primary phase grows by one complete revolution per pulse. Modulo 360 degrees, every sample is identical, and the clean two-pulse output is zero. The secondary dwell samples the same motion at 5.3 kHz, so its phase does not repeat and its clean output is clearly nonzero. Noise leaves a small primary residual, but it does not restore target gain.

Interpretation: the target vanishes because its sampled phase sequence lands on a canceller null, not because its physical velocity becomes zero.

## 2. Sweep 1: follow velocity across both response curves

Figure 2 sweeps only radial velocity from -150 to +150 m/s. The PRFs, carrier, and canceller stay fixed. Locate the circular markers for 4.0 kHz nulls and triangular markers for 5.3 kHz nulls.

Expected observation: the primary null spacing is about 59.96 m/s, while the secondary null spacing is about 79.44 m/s. At the primary first blind speed, the secondary curve is above the threshold. At the secondary first blind speed, the primary curve is high. The max-fused curve fills these nonzero individual holes but retains the common notch around zero.

Use Figure 3 to connect amplitude to a decision. The combined OR row is one wherever either individual dwell crosses the illustrative normalized threshold of 0.30.

Common mistake: a continuous gain curve is not a probability-of-detection curve. The 0/1 display is a deterministic threshold illustration for a unit target, not a performance guarantee.

## 3. Sweep 2: vary only the second PRF

Figure 4 holds the physical target at 59.96 m/s and changes `secondary_prf_sweep_hz`. Start with the provided cases:

```matlab
secondary_prf_sweep_hz = [4.0e3 4.2e3 4.5e3 4.9e3 5.3e3 5.7e3 6.2e3];
```

Expected observation: when PRF 2 equals 4.0 kHz, its normalized gain is zero because it duplicates the primary sampling schedule. Moving PRF 2 away moves the blind-speed grid and raises the response at the fixed target velocity. The response need not increase monotonically for arbitrary PRFs; it follows a sine of the Doppler-to-PRF ratio.

Concept connection: PRF diversity is useful because it changes the sampling phase increment for the same target, not because two identical observations are averaged.

## 4. Intentionally broken case: remove the diversity

The final section sets:

```matlab
broken_secondary_prf_hz = primary_prf_hz;
```

Figure 5's top panel is the broken result. Both response curves and all blind speeds coincide, so max/OR fusion cannot fill a hole. The baseline moving target remains absent.

This is not repaired by lowering the threshold: at the ideal target null, the target contribution is exactly zero, while a lower threshold merely admits more noise or clutter residue.

## 5. Recovery

The broken case is isolated in `broken_secondary_prf_hz`; it does not overwrite the valid 5.3 kHz control. The bottom panel deliberately returns to the already retained `secondary_prf_hz = 5.3e3` response. Rerun the script after any learner edit. The console reports a recovered normalized gain above the threshold at the primary blind target.

Expected observation: the recovery changes only the second sampling schedule. The target velocity and target Doppler remain the same.

## Safe interruption, reset, and rollback

The script has fixed loop and array bounds, no background worker, timer, network call, hardware access, or persistent output. If you interrupt it with `Ctrl+C`, rerun `experiment`; `clearvars` resets workspace results, the private seed recreates the noise, and cleanup closes only figures tagged `P39`.

Repository rollback is likewise isolated: remove the four P39 implementation artifacts, restore this README's scaffold wording, set only P39's manifest status back to `scaffolded`, and revert the P39 catalog/evidence/test changes. Do not change P38 or learner progress.

## 6. Optional controlled edit

Change `carrier_frequency_hz` to `8e9` and rerun, leaving both PRFs fixed.

Expected observation: wavelength increases by 25%, so both blind-speed spacings increase by 25% and their first positive markers remain inside the fixed ±150 m/s plot. This ties the velocity grid to wavelength as well as PRF. Restore 10 GHz before completing the checks.

## Completion checklist

- You can point to a nonzero velocity where the 4.0 kHz response is zero.
- You can calculate the first blind speed from \(\lambda f_r/2\).
- You can explain why 5.3 kHz produces a nonzero phase difference for that same target.
- You can explain why identical PRFs do not provide diversity.
- You can distinguish the desired zero-velocity notch from an unwanted nonzero blind speed.
