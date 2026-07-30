# Walkthrough

## Baseline

Run `experiment.m` through the first figure. Locate the real cosine, I component, Q component, and IQ circle. Confirm that the real cosine and I component overlap exactly.

**Observation question:** As time increases, does the positive-frequency IQ point rotate counterclockwise or clockwise?

## Sweep 1: amplitude

Run the amplitude-sweep section. The three trajectories should have different radii but complete the same number of rotations. Halve `A` in the baseline and confirm that peak time-domain amplitude and IQ radius both halve.

## Sweep 2: phase

Run the phase-sweep section. The waveforms begin at different points in the cycle, but their spacing between peaks is unchanged. Set `phi = pi/2` and identify the initial I and Q values from the circle before reading the time plots.

## Broken case

Run the undersampled section with `fs_bad = 8`. A 5 Hz real tone is above the 4 Hz Nyquist limit, so the samples are compatible with a lower apparent frequency. Increase `fs_bad` to 12 and then 20 and observe when the measurements begin to represent the original oscillation clearly.

## Recovery

Return to `fs = 200`, then change only `f0`. Predict whether the IQ point will complete more or fewer rotations during the one-second record before running it.
