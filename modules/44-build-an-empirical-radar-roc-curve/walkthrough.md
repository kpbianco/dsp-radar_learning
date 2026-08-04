# P44 walkthrough: Build an Empirical Radar ROC Curve

Guiding question: **How does threshold choice trade probability of detection against false alarm?**

## Before running

Open `experiment.m`. The visible controls are bounded before allocation. Leave
the private seed, statistic convention, resource ceilings, and assertion
tolerances unchanged on the first run. `sample_count` stays 16 because it is
the dimension of the fixed reviewed pulse; the guided edits below change only
controls that preserve that shape. No toolbox, file, network, or device is
required. If you interrupt with Ctrl+C, rerun the whole script: `clearvars`,
P44-tag-only figure cleanup, and the private seed provide clean recovery
without changing MATLAB's global random stream.

## Baseline — see two populations become one statistic each

Run the complete script, then inspect only Figure 1.

1. The upper-left plot is the known 16-sample pulse.
2. The upper-right plot overlays one target-absent H0 record and one
   target-present H1 record at 6 dB matched-filter SNR. One lucky record is not
   a probability estimate.
3. The lower plot contains 60,000 explicit matched-filter outputs from each
   condition. H0 is centered near zero; H1 is shifted right by
   `d_prime = sqrt(SNR_MF)`.

Expected observation: the distributions overlap, so no vertical threshold can
retain every H1 sample while rejecting every H0 sample.

Concrete observation question: in Figure 1, which distribution supplies false
alarms, and which supplies detections and misses?

## Sweep 1 — change only matched-filter SNR

Move to Figure 2. The empirical markers come from thresholding the banks; the
dashed curves in the log-scale panel come from the stated Gaussian equations.

The script uses `snr_db_sweep = [-6 0 6 12]`. H0 stays the same because target
SNR does not change target-absent noise. Only H1 shifts. Follow a single
vertical `Pfa` value and compare `Pd` across curves.

Expected observations:

- moving along any one curve by raising threshold lowers both `Pfa` and `Pd`;
- increasing SNR raises `Pd` at the same `Pfa` and bows the curve upward; and
- the -6 dB curve lies much closer to the no-skill diagonal than the 12 dB
  curve.

One-variable edit: change only `baseline_snr_db` from `6` to `0`. Keep `0` in
`snr_db_sweep`, rerun, and use Figures 1, 4, and 5. The chosen baseline H1
population moves toward H0, the operating `Pd` falls, but the operating `Pfa`
does not change because it is defined under H0.

Restore `baseline_snr_db = 6` before continuing.

## Marked operating point — turn probability into workload

Read Figure 3 and these retained values:

- `results.operating_threshold_sigma`
- `results.operating_empirical_pfa`
- `results.operating_empirical_pd`
- `results.expected_false_alarms_per_scan_empirical`
- `results.expected_false_alarms_per_scan_design`

The reviewed threshold is about 3.09 noise RMS and has model
`Pfa = 0.001`. Across one million target-absent searched cells, the model
therefore expects 1000 false alarms per scan. The empirical count fluctuates
around that value because its probability came from a finite bank.

Expected observation: at the same marked threshold, `Pd` changes strongly with
SNR while the H0-derived `Pfa` is common to all SNR cases.

Common mistake: reading `0.001` as “almost no false alarms” without multiplying
by the number of target-absent detection opportunities.

## Sweep 2 — change only the number of Monte Carlo trials

Move to Figure 4. The detector, SNR, threshold, seed, and underlying full bank
stay fixed. Only the prefix length changes through 500, 2,000, 10,000, and
60,000 independent trials.

Expected observations:

- at 500 trials, one false alarm already represents probability 0.002, so the
  bank cannot finely resolve a design value of 0.001;
- `Pfa` can move sharply when the rare-event count changes by one; and
- the `Pd` error bars and probability resolution shrink as trials grow.

One-variable edit: change only `trial_count_sweep` to
`[1000 5000 20000 60000]`. Keep the final value equal to `trial_count`, rerun,
and compare Figure 4. The curve endpoints and detector have not changed; only
the evidence resolution has.

Restore the original vector before continuing.

## Intentionally broken case — cherry-pick, tune, and judge one tiny bank

Move to Figure 5. The broken path sorts all H0 scores, cherry-picks the quietest
250, places its threshold at their maximum, and then reports performance on
those same scores. Its zero training false-alarm count is guaranteed, not
discovered.

Expected observation: the held-out bank crosses the tuned threshold even
though the reused training bank reports zero. `results.broken_claim_is_valid`
is false because tuning and evaluation did not stay independent.

Failure interpretation: the threshold memorized a deliberately unrepresentative
bank's largest noise sample. It did not establish a population tail
probability. Raising `broken_training_count` changes the fitted maximum but
does not repair cherry-picking or data reuse.

## Recovery — preselect the point and regenerate independent banks

The recovery returns to the predeclared 3.09-RMS threshold, evaluates all H0
and H1 trials with their proper denominators, then recreates both banks with a
fresh private stream initialized to the same seed.

Check:

- `results.recovery_exact` is true;
- `results.recovered_empirical_pfa` equals the original operating `Pfa`; and
- `results.recovered_empirical_pd` equals the original 6 dB operating `Pd`.

This is deterministic simulation recovery, not proof of a physical receiver,
independent scan cells, or a production false-alarm rate.

## Concept connection and completion handoff

You are ready for the checks when you can connect all four statements:

1. H0 crossings divided by H0 trials estimate `Pfa`.
2. H1 crossings divided by H1 trials estimate `Pd`.
3. Threshold selects one point; SNR changes the available ROC curve.
4. Searched-cell count converts per-cell `Pfa` into an operational burden.

Use `checks.md` for the short teach-back. Do not mark personal completion until
the completion check and teach-back have both been reviewed.
