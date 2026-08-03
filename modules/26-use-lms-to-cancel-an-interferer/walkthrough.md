# P26 Walkthrough: Use LMS to Cancel an Interferer

## Guiding question

How can an adaptive filter learn an unknown coupling path?

## Before running

P25 is the immediate prerequisite: it showed that an FIR path creates weighted
delayed copies. Here the same path is unknown to the canceller. The eight LMS
coefficients begin at zero and must learn only from the primary/reference
sample relationship.

Run `experiment.m` from this module folder. It uses base MATLAB, a private seed,
6,000 samples, bounded loops, and five tagged figure groups. It does not change
MATLAB's global random stream or write files.

## 1. Establish the baseline signal flow

Start with `baseline_step_size = 0.006`. In **P26 Signal flow and
cancellation**, inspect the primary and desired traces, then the true and
estimated interference traces.

Expected observations:

- The early estimate starts near zero because every learned tap starts at
  zero.
- The estimate comes to overlap the true coupled interference.
- At sample 3001 the true path changes without resetting LMS. The estimate is
  briefly wrong, then follows the new coupling.
- The error trace keeps the desired two-tone waveform and receiver noise. It
  is not supposed to collapse to zero.

The printed suppression values compare true-interference power with residual
interference power in settled windows. They do not count desired signal power
as uncancelled interference.

## 2. Watch the coefficients learn and reacquire

Open **P26 Learned coupling coefficients**. The upper plot contains all eight
coefficient histories. The lower plot compresses their disagreement with the
active true path into RMS coefficient mismatch.

Observe one processing transition at a time:

1. At startup, mismatch falls as the zero coefficients approach `path_before`.
2. At the vertical path-change marker, mismatch jumps because the weights still
   describe the old path.
3. LMS continues from those old weights; it is not secretly reinitialized.
4. Reacquisition is recorded only after mismatch stays below 0.08 for 64
   consecutive samples.

Connect this to the power plot. The residual-power burst and coefficient-error
burst should occur at the same physical event.

## 3. Connect time-domain learning to the residual spectrum

The explicit windowed FFT compares the primary with the settled canceller
output before and after the path change.

Look for broad primary interference falling while the desired 700 Hz and
1100 Hz lines remain visible. This does not mean LMS targeted those frequency
bins. The sample-by-sample predictor removed the waveform component correlated
with the reference, and its spectral energy fell as a consequence.

## 4. Sweep one variable: LMS step size

The first sweep uses

```text
mu = [0.0005, 0.002, 0.006, 0.012]
```

Change only the step size. The reference, desired signal, receiver noise,
unknown paths, change time, filter length, and initial zero weights remain
fixed for every case.

Expected observations:

- `0.0005` moves so slowly that it does not satisfy the post-change
  reacquisition rule within this finite record.
- `0.002` reacquires, but later than the baseline.
- `0.006` is the baseline compromise.
- `0.012` reacquires faster but shows more steady error/misadjustment.

Do not choose a step only from the lowest final point of one noisy record. A
useful choice must be stable, fast enough for the expected path motion, and
quiet enough after convergence.

## 5. Sweep one variable: reference correlation

Keep the primary signal, true interference, baseline step, filter length, and
all fixed random sequences unchanged. Change only how much of the true source
reference appears in the adaptive input:

```text
rho = [1.00, 0.75, 0.50, 0.25, 0.00]
```

Expected observation: residual suppression falls as `rho` falls. At `rho=0`,
the adaptive input is independent of the actual coupled interference, so a
stable algorithm cannot infer the unknown path. This sweep diagnoses an
information problem, not a step-size problem.

## 6. Run the intentionally broken case

The broken case changes only the step size to `0.35`, far above the visible
conservative study limit. It keeps the same primary, reference, path, starting
weights, and LMS equation.

For this ideal eight-tap, unit-power white-Gaussian reference model, `0.35`
also exceeds the mean-square bound `2/((L+2)P_x) = 0.2`. It remains below the
looser mean-coefficient bound near `2`, which is why those two notions of LMS
convergence must not be treated as interchangeable.

Expected observation: error and weight norm grow instead of settling. A
finite-value/resource guard stops the loop before error exceeds `1e6`, weight
norm exceeds `1e4`, or nonfinite values spread. The stop is a safety boundary,
not a claim that `0.35` is the exact theoretical stability boundary.

### Recovery

Reset the broken weights to zero and perform a full rerun with
`baseline_step_size = 0.006`. The script verifies that this clean rerun exactly
reproduces the private-seed baseline and reacquires after the path change.
Reducing the plotted axis or continuing from the already divergent weights is
not recovery.

## 7. Operational behavior and isolation

- Press **Ctrl+C** to cancel a slow or mistaken run. MATLAB stops between
  operations; there is no background worker or timer to clean up.
- A full rerun removes only figures tagged `P26` and reconstructs P26 data from
  its private seed. It leaves unrelated figures and MATLAB's global random
  stream alone.
- Cancellation can leave partially assigned P26 workspace variables. A rerun
  replaces them, but the script cannot restore caller workspace variables that
  the caller overwrote before or during the run.
- The experiment has no external transaction, network access, or persisted
  simulation output. It never reads or writes `.learning/`; learner progress
  remains the CLI's local concern.
- The fixed ceilings are 6,000 samples, eight taps, four step cases, five
  reference cases, a 2,048-point FFT, five figures, and 500,000 conservative
  stored numeric values.

## Completion connection

Choose a stable step size and justify it using both reacquisition time and
settled output behavior. Then point to the coefficient mismatch and residual
power transitions that show the filter reacquiring the changed interference
path.

## Rollback

Repository rollback removes the four P26 implementation artifacts, its P26
test/evidence files and catalog additions, restores this README to its
scaffolded brief, and restores only P26's manifest status to `scaffolded`.
P25 and later canonical module identities stay unchanged.
