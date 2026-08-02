# P19 Walkthrough: Read the Signature, Then Undo the Mechanism

## Guiding question

How do DC offset, gain mismatch, and quadrature error change an IQ spectrum?

Run `experiment.m` from the top with the visible controls unchanged. It uses a
private seed, a coherent `+160 Hz` calibration tone, bounded arrays, and no
files or external state. Keep `results` in the workspace so each observation
can be checked against a named metric.

## Baseline — inspect one impairment at a time

1. Start with the clean spectrum. Locate the desired peak at `+160 Hz`; the DC
   and `-160 Hz` image bins should sit near the deterministic noise floor.
2. Move to `DC only`. The new spike is at `0 Hz`, and the I/Q trajectory moves
   away from the origin without changing its circular shape.
3. Move to `Gain mismatch only`. The trajectory becomes an axis-aligned
   ellipse and a conjugate image appears at `-160 Hz`.
4. Move to `Quadrature error only`. The trajectory becomes tilted/sheared,
   `rho(I,Q)` moves away from zero, and the same image location appears.
5. Inspect `All impairments`. It combines a shifted center, unequal/tilted axes,
   a center spike, and a negative-frequency image.

Expected observation: the spectral location identifies the class of artifact,
while I/Q geometry helps separate offset, branch-scale, and phase-axis causes.
Do not call the negative-frequency copy a second transmitted tone.

## Correction stages — preserve the order

The third figure shows the combined input and each correction transition.

1. Read `results.estimated_dc_v`, then inspect `Mean removed`. The DC magnitude
   collapses, but image rejection barely changes because mean subtraction does
   not repair imbalance.
2. Read `results.estimated_i_gain` and `results.estimated_q_gain`. In `Gains
   normalized`, the ellipse axes are rescaled and IRR improves, but the
   quadrature shear remains.
3. Read `results.estimated_quadrature_error_deg`. The final stage subtracts the
   leaked I component from Q and divides by `cos(phiHat)`.
4. Compare the first and final entries of `results.stage_irr_db` and inspect
   `results.corrected_rmse_v`.

Expected observation: mean removal fixes the center spike, gain normalization
removes the axis-length mismatch, and the shear inverse removes the remaining
image. One number should not be used to claim that every mechanism is fixed.

## Sweep 1 — change only I-branch gain

The fourth figure holds Q gain at one and sets offset, quadrature error, and
noise to zero while `gI` changes through `1.00`, `1.10`, and `1.30`.

1. Predict whether the horizontal or vertical ellipse axis changes.
2. Read `results.gain_sweep_axis_ratio`; it should follow `gI`.
3. Read `results.gain_sweep_irr_db`; image rejection should fall as the two
   branch gains separate.

Physical connection: unequal receiver branch scale mixes the desired rotating
component with its conjugate. More eccentricity means more image amplitude.

## Sweep 2 — change only quadrature error

The fifth figure holds both gains at one and holds offset and noise at zero
while phase error changes through `0`, `5`, and `15 degrees`.

1. At zero error, confirm a circle and near-zero I/Q correlation.
2. At five and fifteen degrees, follow the growing tilt.
3. Compare `results.phase_sweep_correlation` with `sin(phi)` and watch
   `results.phase_sweep_irr_db` fall.

Physical connection: the receiver's Q axis is no longer perpendicular to I.
The amount of I visible in Q is the shear that creates the image.

## Broken case — rotate instead of unshearing

The final figure intentionally multiplies the gain-corrected samples by
`exp(-j*phiHat)`.

1. Compare `results.broken_irr_db` with the gain-corrected third entry of
   `results.stage_irr_db`. They are equal: rotation changes phase, not the
   desired/image magnitude ratio.
2. Inspect the broken trajectory. Its orientation changes, but its
   nonorthogonal-axis distortion remains.
3. Compare with the recovered trajectory and spectrum after
   `Q=(Q-I*sin(phiHat))/cos(phiHat)`.

Failure interpretation: carrier phase and quadrature-axis error are different
operations. A rotation repairs the reference angle of an already orthogonal
coordinate system; the shear inverse repairs the coordinate system itself.

Recovery: return to the staged path—remove mean, normalize branch gains,
estimate correlation, then invert the quadrature shear.

## Safe rerun, timeout, cancellation, recovery, isolation, and rollback

Every loop and allocation has a fixed ceiling. There is no prompt, wait,
timeout, timer, worker, file, network, system, or audio operation. Ctrl+C stops
the foreground script; an interruption after P19 cleanup begins can leave a
partial P19 figure set and empty/incomplete `results`. Rerun from the top to
recover.

Malformed controls fail before the private random stream, signal/FFT arrays,
figure cleanup, or new figures are created. A malformed rerun therefore
preserves the last valid P19 output. A valid rerun recreates the same noise,
replaces only P19-tagged figures and `results`, leaves the global random stream
unchanged, and does not affect unrelated figures or ignored `.learning/` state.

Rollback removes only P19-owned module artifacts, allowed P19/shared lifecycle
tests, allowed catalog edits, and P19 evidence, then restores only P19's
manifest status to `scaffolded`. Preserve implemented P18, every later
canonical module identity, learner state, and the operator-owned active-batch
record.

## Completion handoff

Use `checks.md`, then give a two- or three-sentence teach-back that maps DC,
gain mismatch, and quadrature error to their spectrum/trajectory signatures;
explains why correction order matters; and distinguishes a broken global
rotation from the recovered shear inverse.
