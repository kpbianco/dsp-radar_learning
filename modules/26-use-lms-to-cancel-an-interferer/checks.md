# P26 Checks: Use LMS to Cancel an Interferer

## Guiding question

How can an adaptive filter learn an unknown coupling path?

Use the plots and retained `results` values. These are interpretation checks,
not MATLAB syntax exercises.

## Observation checks

1. **Signal flow:** Early in the record, why is the LMS interference estimate
   poor even though its reference already contains the source waveform?
   - The coefficients start at zero. Correlation supplies evidence over
     repeated samples; it does not provide the unknown path instantly.

2. **Desired output:** After convergence, why does `baseline_error` still have
   visible 700 Hz and 1100 Hz content?
   - Error is the canceller output: desired signal plus independent noise and
     residual interference. Successful interference cancellation is not a
     zero-output objective.

3. **Path change:** Which two plots react together at sample 3001?
   - RMS coefficient mismatch and residual/error power rise because the old
     learned taps no longer predict the new coupling.

4. **Reacquisition:** What makes the reacquisition metric stronger than one
   low-mismatch sample?
   - Mismatch must stay below 0.08 for 64 consecutive samples.

5. **Spectrum:** What changes, and what should remain?
   - Broad reference-correlated interference falls. Desired 700 Hz and 1100 Hz
     lines remain because they are independent of the reference.

## Prediction checks

1. Predict the result of setting `mu=0` before looking at the limiting cases.
   - The weights remain zero, the estimate remains zero, and error equals the
     primary input.

2. Which reacquires sooner, `mu=0.002` or `mu=0.012`?
   - `0.012`, provided it remains stable; its larger updates move toward the
     changed path faster.

3. Does the faster stable step guarantee the lowest settled output power?
   - No. Larger steps keep reacting more strongly to random instantaneous
     error and usually increase misadjustment.

4. If the reference correlation is zero but the step stays at `0.006`, will a
   longer run reveal the true FIR taps?
   - No. Independent data do not identify the coupling. More samples improve
     an estimate only when the required information is present.

5. If the real coupling needs 12 taps but the adaptive filter retains eight,
   what remains after convergence?
   - The representable part can be learned, but delayed structure outside the
     eight-tap model remains as residual interference.

## Correct these interpretations

- “The path-change spike is numerical instability.”
  - Incorrect. The stable baseline spike occurs because a physically changed
    path makes the old model stale; falling mismatch afterward proves recovery.

- “The learned coefficients are the radar channel.”
  - Too broad. They estimate this local reference-to-primary interference
    coupling within an eight-tap model.

- “Any reference lets LMS cancel any interferer.”
  - Incorrect. Only primary content predictable from that reference is
    cancellable.

- “The broken guard proves the exact maximum stable step.”
  - Incorrect. It bounds resource use for one deliberately oversized step.
    Mean-coefficient convergence depends on the reference correlation
    eigenvalues, while mean-square stability is stricter and also depends on
    filter length and higher-order input statistics.

## Failure, recovery, and operational checks

- Confirm `results.broken.guard_triggered` is true and its stop sample is
  finite and inside the 6,000-sample record.
- Confirm a full rerun from zero weights at the stable private-seed baseline
  reproduces `baseline_error` and reacquires the second path.
- If you use **Ctrl+C**, rerun the whole script; do not interpret partial
  workspace arrays as settled results.
- Confirm the rerun removes only `P26`-tagged figures, does not reset the global
  random stream, and does not touch `.learning/`.
- There is no worker, timer, external transaction, or saved result to roll
  back. A rerun cannot restore unrelated caller workspace variables that were
  overwritten before cancellation.
- Confirm the implementation uses base MATLAB and the sample-by-sample update,
  with P25 as the FIR-path prerequisite.

## Completion checklist

- [ ] I can point to the learned coefficients approaching both true paths.
- [ ] I can show residual power rising at the change and falling after
      reacquisition.
- [ ] I can choose a stable step using speed and settled behavior, not speed
      alone.
- [ ] I can distinguish an unstable update from an uninformative reference.
- [ ] I can explain why the desired output remains after cancellation.

## Short teach-back rubric

In two or three sentences, explain how LMS learns the unknown coupling, how
step size changes the learning behavior, and what proves reacquisition after
the path changes. A complete answer mentions correlation-driven prediction,
the convergence/misadjustment/stability trade, and the post-change fall in both
coefficient mismatch and residual power.

## Repository rollback

Rollback returns only P26 to `scaffolded` and removes its owned implementation,
test, catalog, and evidence additions. It preserves P25 and all canonical
identities. This repository rollback is separate from runtime recovery, which
is a deterministic full rerun with stable zero-initialized weights.
