# Walkthrough: Watch Stationary Phasors Subtract Away

## 1. Run the deterministic baseline

From the repository root, run:

```matlab
run('modules/38-implement-a-two-pulse-and-three-pulse-mti-canceller/experiment.m')
```

The script uses private seed `3801`. The first target deliberately shares a
range cell with strong stationary clutter. In the first figure, observe that
the clutter dominates the raw matrix and the target-alone trace is much
smaller.

Then inspect the clutter-suppression range-profile figure. The large stationary
peaks collapse after slow-time differencing while moving-target residuals and
noise remain.

**Observation question:** At the shared clutter/target range, what remains
after the constant pulse-to-pulse phasor is subtracted?

## 2. Read the response before judging an output peak

In the frequency-response figure, locate zero Doppler. Both curves reach zero.
Near zero, the three-pulse curve stays lower because its response is the square
of the two-pulse factor.

Now use the target/noise figure and `results` together. Compare:

- `two_pulse_target_gain` and `three_pulse_target_gain`;
- `noise_power_gain_theory`, which is `[2 6]`; and
- the reported target SNR changes.

Do not call the largest amplitude gain the best detector response without also
accounting for noise.

## 3. Sweep one variable: target velocity

The left sweep holds carrier, PRF, range, amplitude, and noise model fixed.
Only radial velocity changes. Notice:

- exactly zero velocity falls in both nulls;
- the three-pulse curve rises more slowly near zero; and
- positive and negative velocities have the same magnitude response even
  though their complex Doppler rotations have opposite signs.

Edit only `velocity_sweep_mps`, keep its values strictly increasing and inside
the printed unambiguous interval, and rerun. Add one small nonzero speed between
0 and 3 m/s. Predict which canceller attenuates it more, then inspect the plot.

## 4. Sweep one variable: PRF

The right sweep holds the target at `12 m/s`. Only PRF changes. Raising PRF
reduces phase change per pulse, moving this fixed Doppler toward the normalized
DC notch, so both gains fall. At the same time
`prf_sweep_unambiguous_velocity_mps` grows.

Change one PRF entry while keeping the list positive, strictly increasing, and
high enough that the fixed target remains unambiguous. Explain the response in
terms of phase per PRI rather than range.

## 5. Inspect the intentionally broken axis

The broken operation is

```text
X[2:end,:] - X[1:end-1,:]
```

It differences adjacent range rows. The final figure shows range edges around
stationary clutter rather than a stationary-clutter null. Check that
`broken_model_valid` is false and `broken_clutter_residual_ratio` is nonzero.

This failure can look like plausible high-pass filtering. The physical axis,
not visual activity, decides whether the operation is MTI.

## 6. Recover coherently

Recovery recreates the complex noise from the same private seed and restores
column-wise operations:

```text
X[:,2:end] - X[:,1:end-1]
X[:,3:end] - 2 X[:,2:end-1] + X[:,1:end-2]
```

In MATLAB notation these are the explicit expressions in `experiment.m`.
The script asserts exact equality between baseline and recovered matrices and
outputs. Confirm `recovered_model_valid` is true.

## 7. Connect the modules

P36 explains why a moving target rotates from pulse to pulse. P37 places those
pulses in columns. P38 subtracts adjacent columns to reject a constant phasor.
P39 follows the repeated response far enough to expose blind speeds.

## Cancellation, isolation, and rollback

The script has bounded arrays, bounded sweeps, finite loops, no worker, timer,
network, hardware, file write, or external transaction. Press Ctrl+C to cancel
a run; rerunning starts clean because only `P38` figures are closed and private
streams recreate the scene without changing MATLAB's global random state.

To roll back an experimental edit, restore the visible controls and rerun. A
clean rerun is also the recovery path after cancellation; there is no persisted
simulation state to migrate or undo.

## Expected observations

- Ideal stationary clutter has zero residual in both correct cancellers.
- The three-pulse notch is stronger near zero Doppler.
- The slow target can lose more amplitude in the three-pulse output.
- White-noise power rises by factors near 2 and 6 in the seeded measurement.
- Range-axis differencing leaves clutter edges and fails the MTI objective.
