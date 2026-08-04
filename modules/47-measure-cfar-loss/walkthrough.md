# Walkthrough: measure loss only after matching Pfa

## Before running

Open `experiment.m` and note the visible controls: seed 4701, 50,000 trials,
SNR from 3 to 17 dB in 0.5 dB steps, requested `Pfa = 1e-3`, target
`Pd = 0.8`, baseline `N = 16`, training cases `[8 16 32 64]`, and requested
`Pfa` cases `[1e-2 1e-3 1e-4]`. All arrays and loops are checked against fixed
ceilings before random data is allocated.

Run the script once. It creates five figure groups tagged `P47` and leaves a
compact `results` structure in the workspace.

## 1. Observe why the CA threshold moves

Figure 1 uses the first 240 of the seeded trials. The known-noise threshold is
the same on every trial. The CA threshold changes because each 16-cell
arithmetic mean is a new background estimate. The target-present panel uses
the same CUT realization at 10 dB SNR and shows both threshold comparisons.

Concrete observation: find a trial whose target-present CUT power clears the
fixed known threshold but falls below the CA threshold. The target SNR did not
change; the estimated-background threshold happened to be high.

## 2. Measure the baseline SNR gap

Figure 2 plots raw empirical `Pd` versus SNR for the known-noise and 16-cell
CA detectors at the same requested `Pfa`. Follow the horizontal `Pd = 0.8`
line to each curve and then down to the SNR axis.

Inspect `results.known_snr_at_target_pd_db`,
`results.baseline_cfar_snr_at_target_pd_db`, and
`results.baseline_cfar_loss_db`. The last quantity is the horizontal SNR gap,
not a vertical `Pd` difference and not a threshold-multiplier ratio.

## 3. Sweep total training-cell count only

Figure 3 holds the CUT trials, target phase, SNR grid, requested `Pfa`, and
target `Pd` fixed while total `N` takes 8, 16, 32, and 64. Each case uses the
first `N` powers from the same seeded reference bank. Its exact finite-`N`
multiplier is recomputed.

Expected observation: the 8-cell curve needs the most SNR, and the loss bars
shrink toward zero as `N` grows. Inspect
`results.training_sweep_noise_estimate_std`: the standard deviation of the
background estimate should also fall.

One-variable edit: change `training_cell_count_sweep` to `[4 8 16 32 64]`.
Keep it increasing, within the 64-cell ceiling, and keep the baseline value.
Re-run and see how sharply the four-cell estimate increases loss. Restore the
reviewed vector afterward.

## 4. Sweep requested Pfa only

Figure 4 holds `N = 16`, the Monte Carlo samples, SNR grid, and target `Pd`
fixed while requested `Pfa` takes `1e-2`, `1e-3`, and `1e-4`. Both the ideal
and CA thresholds are recalibrated for every case before their required SNRs
are compared.

Expected observation: the measured finite-training loss grows as the false
alarm requirement becomes more stringent. This is not caused by a new noise
realization; every case reuses the same noise and target trials.

One-variable edit: change `false_alarm_probability_sweep` to
`[1e-2 3e-3 1e-3 3e-4 1e-4]`. Keep its descending order and reviewed five-case
limit. Re-run and observe the smoother loss trend, then restore the original
three values.

## 5. Break and recover equal-Pfa calibration

Figure 5 applies the known-noise multiplier `-log(Pfa)` to the random 16-cell
estimate. Its `Pd` curve looks much closer to the ideal curve, but the lower
panel reveals that its theoretical and empirical H0 false-alarm probabilities
are well above `1e-3`.

Recovery uses `alpha = N*(Pfa^(-1/N)-1)`, formed independently from the
requested probability and `N`, and recomputes every CA threshold comparison.
The recovered detector returns to the requested theoretical `Pfa`; its larger
SNR gap is the honest loss.

Common mistake: do not call the broken detector “more efficient.” It purchased
extra detections with extra false alarms, so it is a different operating point.

## Cancellation, rerun, and recovery

If you press Ctrl+C, no external or learner state needs rollback. The script
writes no files and starts no workers, timers, or services. Rerun from the top:
it clears partial variables, closes only figures tagged `P47`, creates a fresh
private stream, and reconstructs the same trials. The broken-case recovery
recomputes calibrated multipliers and decisions from the original seeded CUT
and reference statistics; it does not rename the broken curve as corrected.

## Completion handoff

Use `checks.md`. You are ready for the short teach-back when you can define
loss as a horizontal SNR difference at equal `Pd` and equal `Pfa`, explain why
finite reference data creates it, and diagnose a suspiciously small loss by
checking false-alarm calibration first.
