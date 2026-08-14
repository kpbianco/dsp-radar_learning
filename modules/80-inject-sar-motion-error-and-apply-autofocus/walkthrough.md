# P80 walkthrough: Blur the Aperture, Then Estimate Its Phase

The guiding question is: **How small a platform-position error is enough to blur a coherent image?**

Run `experiment.m` once. It creates five tagged figure groups and prints
millimetre, radian, coherent-peak, cross-range-cut entropy, and phase-estimation
metrics. Work
through one processing transition at a time.

## 1. Baseline: convert motion into phase before judging an image

The fixed controls are a `10 GHz` carrier (`lambda = 30 mm`), a `30 m`
aperture sampled every `0.25 m`, three range-isolated targets, and `35 dB`
measurement SNR.

Figure 1 shows the reviewed `lambda/8` RMS line-of-sight error. Its RMS is only
`3.75 mm`, but two-way phase RMS is `pi/2 rad`:

```text
delta phi_rms = 4 pi (3.75 mm)/(30 mm) = pi/2.
```

Inspect the curve rather than only its RMS. It contains smooth drift plus a
short-correlated component, so it cannot be removed by one constant rotation.
The red phase-gradient estimate should closely follow the black injected phase
after their arbitrary constants are removed.

Concrete observation question: is `3.75 mm` small relative to range resolution,
wavelength, or both—and which comparison predicts coherent blur?

## 2. Follow one coherent transition

Figure 2 keeps the scene, noise realization, planned geometry, bandwidth,
aperture, and display floor fixed.

1. **Ideal nominal-track focus:** the explicit path compensation aligns each
   range gate. White crosses show truth; normalized color shows shape.
2. **Errored phase history:** the same signal is multiplied by
   `exp(j delta phi_p)` before focusing with nominal geometry. The reported
   mean peak retention falls below `0.65`, while cross-range-cut entropy rises.
3. **Autofocus corrected:** nominal phase is removed from the strongest
   isolated gate, adjacent phase differences are integrated, and
   `exp(-j phi_hat_p)` is applied to all gates. The mean peak returns above
   `0.95` of ideal and mean cross-range-cut entropy falls by more than `0.8 nat`.

The images are normalized separately for visibility. Use printed peak
retention—not apparent color brightness—to discuss coherent gain.

## 3. Sweep 1: change only error RMS

Figure 3 uses `0`, `lambda/32`, `lambda/16`, `lambda/8`, and `lambda/4` RMS.
The normalized error shape, target scene, SNR, aperture, and focuser remain
fixed.

- The corresponding phase RMS values are `0`, `pi/8`, `pi/4`, `pi/2`, and
  `pi rad`.
- The reviewed uncorrected mean peak falls monotonically. Near `lambda/16`,
  loss is already visible even though the path RMS is under `2 mm`.
- At `lambda/4`, the uncorrected mean peak is below `0.40` of ideal.
- Corrected peaks remain above `0.95`, and corrected cross-range-cut entropy
  remains close to the ideal concentration.

This is a controlled result, not a universal tolerance. Restore the reviewed
values before running completion checks after local edits.

## 4. Sweep 2: hold RMS fixed and change correlation

Figure 4 holds path-error RMS at `lambda/8` and moves the composition from
fully smooth to fully short-correlated.

- Equal RMS cases need not have equal uncorrected peak or the same blur shape.
- Increasing the short-correlated fraction generally raises the largest
  adjacent phase step, which challenges a sampled gradient estimate.
- The red dashed bound is `0.9 pi`; every reviewed case stays below it.
- The strong isolated reference allows the simple estimator to correct both
  families here. That does not mean correlation is irrelevant at lower SNR or
  after gradient wrapping.

Prediction before comparing the right panel: if an adjacent true phase step
crosses `pi`, will `angle(z_p conj(z_(p-1)))` report the original step or a
wrapped alias? It reports the wrapped principal value.

## 5. Broken case: violate the reference-gate assumption

Figure 5 deliberately constructs the autofocus input from the strongest gate
plus `0.95` times a second target's gate. The target geometry is not changed;
only the estimator's gate selection is corrupted.

1. Compare the magenta mixed-gate estimate with the black injected phase.
   Scene-dependent phase appears in what the processor calls motion.
2. Inspect the broken image and its peak-retention title. It can improve over
   the uncorrected image yet still remain materially worse than correct
   autofocus. “Some improvement” does not validate the estimate.
3. Compare the blue recovered estimate. It comes from the isolated range gate
   and tracks the common phase screen.
4. Inspect the recovered image. The script asserts it exactly matches the
   earlier corrected result because both start from the same retained data and
   deterministic estimator.

This failure is bounded and in memory. It does not corrupt a measurement file,
device, learner state, or external service.

## 6. Recovery, cancellation, rerun, and isolation

Recovery does not sharpen the broken image. It returns to the numerically
unchanged retained errored complex history, selects the isolated strong gate, estimates
the phase again, corrects every gate, and freshly refocuses.

The script has finite foreground loops and no timer, worker, file, network,
GPU, subprocess, or checkpoint. Press Ctrl+C to cancel. Cancellation may leave
partial figures and variables, but no persistent state. Rerun `experiment.m`;
its first lines close prior figures tagged `P80` and reconstruct the same
private noise and motion templates without changing MATLAB's global random
stream.

## 7. Connect the concepts

- P75: target geometry creates coherent two-way phase history.
- P76/P78: range gates must remain complex and aligned before azimuth focus.
- P77: nominal path compensation focuses the scene and exposes residual path
  error.
- P79: longer apertures sharpen cross-range but demand coherence over more
  positions.
- P80: autofocus estimates a residual phase screen from the scene; it does not
  replace waveform bandwidth, aperture sampling, migration correction, or
  absolute navigation.
- P81: target rotation will create synthetic-aperture phase from another
  geometry, with related coherence sensitivities.

The concise answer is: at `10 GHz`, millimetre-scale aperture-dependent path
error already corresponds to substantial two-way phase; whether it blurs
depends on its variation across the aperture, and autofocus succeeds only when
the scene makes that common phase observable.

## Rollback and completion handoff

Repository rollback removes only the P80 implementation/test/evidence and
restores only P80's manifest status to `scaffolded`. Preserve P79, future
module identities and statuses, personal `.learning/` state, and
operator-managed batch contracts.

Use `checks.md`. Completion requires a short teach-back that converts a path
error fraction to phase, distinguishes constant/linear phase from defocus, and
explains why the contaminated reference gate defeats this simple estimator.
