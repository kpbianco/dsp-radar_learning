# Checks: Build an Alpha-Beta Tracker

Use these after observing the baseline, both gain sweeps, and the broken-case
recovery.

## Observation checks

1. Why is corrected position smoother than the available reports on the first
   constant-velocity interval?
   - **Correct:** prediction carries prior motion information and alpha accepts
     only part of each noisy position innovation.
   - **Incorrect:** the tracker removes measurement noise from the sensor.

2. Why are there no innovation samples during a dropout?
   - **Correct:** innovation requires an available report minus prediction;
     without a report the tracker only coasts.
   - **Incorrect:** the innovation is zero because the target moved to zero.

3. Why does velocity not jump immediately from 20 to 32 m/s?
   - **Correct:** the fixed beta gain converts repeated position innovations
     into gradual velocity corrections.
   - **Incorrect:** the radar directly measures exact velocity here.

4. Why can prediction keep moving while reports are absent?
   - **Correct:** the last corrected velocity advances position by `T*v_hat`.
   - **Incorrect:** the tracker reads future reports during the gap.

## Prediction checks

1. Predict the immediate effect of raising alpha toward one with beta fixed.
   - **Correct:** corrected position follows each available noisy report more
     closely, reducing smoothing.
   - **Incorrect:** velocity correction necessarily becomes zero.

2. Predict the effect of raising beta with alpha fixed.
   - **Correct:** velocity responds faster to persistent innovations but carries
     more measurement-driven variation and may overshoot.
   - **Incorrect:** available position reports become less noisy.

3. Predict the state update for an unavailable report.
   - **Correct:** corrected state equals predicted state and velocity is held.
   - **Incorrect:** use a zero position report to keep array dimensions simple.

4. Predict what beta zero does from a zero velocity guess.
   - **Correct:** velocity remains zero, position lags moving truth, and dropout
     coasting fails to advance.
   - **Incorrect:** alpha eventually changes velocity even without beta.

## Interpretation and failure checks

1. Is the innovation equal to true position error?
   - **Correct:** no; it compares the available report with predicted position.
   - **Incorrect:** yes; operational trackers know target truth each scan.

2. Does lower constant-segment RMSE prove the gains are best for maneuvers?
   - **Correct:** no; stronger smoothing can increase response lag after model
     mismatch, so both intervals matter.
   - **Incorrect:** yes; one aggregate RMSE determines all tracking quality.

3. Is a stable alpha-beta pair automatically a good design?
   - **Correct:** no; stability is necessary, while noise, lag, dropout, and
     maneuver requirements choose among stable pairs.
   - **Incorrect:** yes; every stable pair has identical performance.

4. Does P54 solve false reports or report-to-track association?
   - **Correct:** no; it assumes one scalar report already belongs to this
     target. P57 introduces general association.
   - **Incorrect:** yes; a small innovation proves report identity.

5. Are alpha and beta Kalman probabilities?
   - **Correct:** no; they are fixed dimensionless gains in this simplified
     tracker. P55 derives gains from covariance.
   - **Incorrect:** yes; alpha plus beta must equal one.

6. Why must velocity correction include division by scan interval `T`?
   - **Correct:** residual has metres, so dividing by seconds gives a correction
     in metres per second.
   - **Incorrect:** it is an optional numerical scaling with no unit meaning.

## Determinism, compatibility, and resource checks

- A private `mt19937ar` stream uses seed `5401`; global random state is not
  changed.
- Truth, one seeded report record, and the availability mask are shared across
  baseline, sweeps, broken case, and recovery.
- The reviewed workload is 81 scans, three alpha cases, three beta cases, one
  baseline, one broken case, one recovery, 729 total tracker steps, and five
  figures tagged `P54`.
- Every loop is bounded; no file, network, shell, timer, worker, tracking object,
  external service, or learner-state operation is required.
- Script-local functions require MATLAB R2016b or later. MATLAB/Octave runtime
  compatibility must be evidenced separately from static checks.

## Completion checklist

- [ ] I can state the predict, innovation, and correction equations with units.
- [ ] I can explain alpha as immediate position trust and beta as velocity
  learning from a position residual.
- [ ] I can predict why alpha changes smoothing and beta changes response/noise.
- [ ] I can explain prediction-only coasting without inventing a zero report.
- [ ] I can identify velocity-change lag as constant-velocity model mismatch.
- [ ] I can explain why beta zero is broken and how positive beta recovers.

## Short teach-back rubric

In 60–90 seconds, answer the guiding question: **How can a simple predictor
smooth noisy position while following constant velocity?** A complete
teach-back must mention:

1. position and velocity prediction over scan interval `T`;
2. innovation as report minus predicted position;
3. alpha and `beta/T` corrections with their noise/lag tradeoff;
4. prediction-only coasting during missing reports; and
5. at least one model limit, such as maneuver lag, beta-zero failure, fixed
   gains without covariance, or assumed association.
