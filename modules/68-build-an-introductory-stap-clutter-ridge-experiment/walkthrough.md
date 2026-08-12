# P68 walkthrough: Observe a Coupled Clutter Ridge

## Guiding question

How can space and slow time be processed together to suppress moving-platform clutter?

Run `experiment.m` once without editing it. The script is finite and
foreground-only. It creates six figures tagged `P68` and `p68_results`.

## Baseline: look at the scene before the weights

Start with **P68 clutter ridge**.

1. Follow the white dashed law through angle and normalized Doppler.
2. Locate the magenta target near `10.7 deg, 0.208 cycles/pulse`.
3. Notice that target angle and target Doppler each meet clutter separately,
   while the paired target point is off ridge.

Expected observation: no one angle or Doppler is globally clean. The useful
fact is the joint pairing.

Now inspect **P68 space-time covariance**. Eight elements times eight pulses
make 64 coordinates. Dominant eigenvalues represent learned ridge structure;
they do not count physical targets automatically.

## Processing transition: separate product versus joint weight

Open **P68 processor response maps** and read left to right.

- Fixed processing knows only the nominal target signature.
- Separate processing adapts one spatial and one Doppler weight, then
  multiplies their responses.
- Joint processing adapts all 64 paired coordinates.

The joint map can distribute low response along the tilted structure. Do not
decide from color alone; **P68 output SCNR comparison** uses known simulated
components and requires joint SCNR to beat separate SCNR by more than 10 dB.
The second panel is one noisy CUT realization and need not rank identically.

## Sweep 1: vary only clean training support

Open **P68 training support sweep**. Cases use `8, 16, 32, 64, 128` prefixes
of one unchanged clean record.

Expected observations:

- below 64 cells, raw covariance rank is bounded by cell count;
- loading keeps the solve finite;
- condition and SCNR change as evidence grows; and
- the reviewed full-support endpoint is useful without claiming monotonicity.

Physical connection: training cells are examples of interference. They add no
sensors, pulses, aperture, or CPI duration.

## Sweep 2: vary only contamination fraction

Open **P68 contamination and recovery**. Every case begins from the same clean
128-cell matrix. Only the stated prefix receives a fixed target-like return.

Expected observation: substantial leakage degrades output SCNR. Do not say
“MVDR always nulls its constraint.” The assumed vector retains unit response;
the actual target is slightly mismatched, so contaminated covariance can
suppress its unprotected component and change clutter/noise gain.

Try changing only `contamination_power_db` from `20` to `10`. Predict a less
severe final endpoint, without requiring monotonic intermediate points.

## Broken case

The intentionally broken case uses 40-percent contaminated training with the
declared `0.7 deg` and `0.008 cycles/pulse` mismatch. Its analytical SCNR must
be more than 10 dB below clean recovery even while its assumed-vector
constraint remains satisfied. This is a training/model failure, not a solver
failure or random target disappearance.

## Recovery on unchanged data

Recovery discards only injected target-like additions, reuses original clean
training, and recomputes the joint weight. The CUT never enters training.

```text
norm(recovered_weight - joint_weight) < 1e-12.
```

The recovery slice therefore overlays baseline.

## Cancellation and rerun recovery

Press `Ctrl+C` between figure sections if needed. There is no worker, timer,
network request, file write, or external process continuing in the background.
An interruption can leave already-created `P68` figures and intermediate
variables in the current MATLAB workspace, but it leaves no background or
external persistent state. Rerun the script to close only figures tagged
`P68`, clear and rebuild `p68_results`, regenerate private streams, and recover
the exact baseline. Unrelated figures and variables are not broadly cleared.

## Before the teach-back

Be ready to explain: one patch supplies paired spatial and pulse phase slopes;
platform motion maps angle onto a ridge; a separable product cannot shape an
arbitrary tilted notch; and joint adaptivity needs representative target-free
training plus an adequate steering model.
