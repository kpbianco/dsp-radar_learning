# Walkthrough: connect a threshold decision to an estimator report

## Guiding question

How do false alarms, detections, bias, variance, and theoretical bounds relate?

## Before running

Run the complete script from a clean MATLAB session. It validates all canonical
controls and resource ceilings before random generation, allocation, figure
cleanup, or plotting. It creates two independent 12,000-record banks in memory,
uses a private seed, opens five figure groups tagged `P28`, performs no file,
network, device, worker, timer, or external transaction, and leaves a `results`
structure in the caller workspace.

If plotting blocks or you need to cancel, press `Ctrl+C`. Re-run the entire
script; do not resume in the middle with a partly populated workspace. The
private seed recreates both H0 and H1 banks without changing MATLAB's global
random stream. Only figures tagged `P28` are replaced.

## Baseline: observe the signal flow

Run the script once. In **P28 Known-pulse signal flow** inspect the pulse and
one record under each hypothesis, then the normalized statistic distributions.
The single records can look ambiguous; the many-trial distributions reveal the
mean separation. Confirm that the vertical threshold cuts the right tails of
both distributions.

Observation question: at `gamma = 1.5` noise sigma, which shaded/discrete tail
becomes `P_FA`, and which becomes `P_D`?

Read the printed baseline `P_FA` and `P_D` and compare them with the analytic
values in `results.baseline`. Small differences are finite Monte Carlo error,
not a different detector.

## Sweep one variable: threshold only

Open **P28 Receiver operating characteristic** and **P28 Threshold
consequences**. The script reuses the same H0/H1 statistic banks at every point;
only `threshold_sigma_sweep` changes. Follow the points from `gamma = -1` to
`gamma = 3`; the plotted `(1,1)` and `(0,0)` endpoints show the exact
`gamma -> -Inf` and `gamma -> +Inf` decision limits.

- Predict before looking: will raising the threshold move toward the ROC's
  lower-left or upper-right?
- Confirm that both empirical `P_FA` and `P_D` never increase as threshold
  rises.
- At the marked `gamma = 1.5` point, state a hypothetical mission reason to
  accept more false alarms or more misses. The curve cannot choose that cost
  trade for you.

Do not compare different threshold points as if they were independent Monte
Carlo experiments. Common random numbers make this a paired, controlled sweep;
they do not multiply the number of trials.

## Sweep one variable: noise scale (and therefore matched-filter SNR)

Open **P28 Estimator limits**. The same standardized H1 noise bank and the same
pulse/amplitude are used for every `estimator_snr_db_sweep` value. Only the
noise scale changes, so at fixed amplitude and pulse energy it also changes the
matched-filter SNR.

- Bias should remain near zero relative to the estimator standard deviation.
- Variance and `RMSE^2` should fall as noise power falls.
- Along this fixed-amplitude, fixed-energy path, the CRLB falls as `1/SNR`, and
  this particular linear Gaussian estimator tracks it because its assumptions
  match the generated data. Raising SNR only by raising the unknown amplitude
  would improve relative error, not this absolute variance bound.

Now connect the plots physically: increasing coherent pulse energy or observing
more same-amplitude known samples increases Fisher information just as reducing
noise does. A delay-estimation bound would additionally depend on effective
bandwidth; this amplitude experiment does not claim to measure delay accuracy.

## Intentionally broken case: report only detections

Open **P28 Selection-bias failure and recovery**. The broken report retains only
H1 records whose statistic crosses the operating threshold. Those records are
preferentially accompanied by positive projected noise, so the detected-only
mean amplitude is too high.

The `results.broken.unbiased_claim_valid` flag is deliberately `false`. Compare
the empirical selected bias with the analytic truncated-Gaussian bias. More
trials would make that biased conditional mean more stable; they would not make
it unconditional.

## Recover

Recovery restores all independent H1 amplitude estimates and recreates both
noise banks from a fresh private stream with the same seed. Confirm:

- `results.recovery.uses_all_h1_trials` is true;
- `results.recovery.exact_seed_match` is true;
- recovered bias is small compared with the baseline CRLB standard deviation.

The recovery does not erase `results.broken`; it preserves the failure for
comparison. If interrupted, a full rerun replaces only P28 figures and results.

## Isolation, compatibility, and rollback

- Base MATLAB operations are used; no opaque detector, ROC, fitting, or CRLB
  toolbox function hides the model.
- Runtime is bounded by fixed trials, samples, sweep cases, storage, and five
  figure groups. There is no asynchronous work to await and no partial external
  transaction to roll back.
- `.learning/` is not read or written by the experiment. Learner completion is
  separate and manual.
- Rollback of the governed implementation removes the four completion
  artifacts, restores this module brief/status to `scaffolded`, and restores
  only the P28 manifest/catalog lifecycle entries. It does not touch P27 or
  personal learner state.

## Completion connection

Choose one plotted ROC operating point and explain the false-alarm/miss trade.
Then explain in two or three sentences why the all-trial estimator is unbiased,
why its variance falls with signal information, and why the detected-only
report is biased. Use `checks.md` before recording personal completion.
