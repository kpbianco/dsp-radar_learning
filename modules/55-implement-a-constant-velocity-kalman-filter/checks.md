# Checks: Implement a Constant-Velocity Kalman Filter

Use these after the baseline, both sweeps, the mismatch pair, and recovery.

## Observation checks

1. Why does true velocity wander although the state transition is called
   constant velocity?
   - **Correct:** F predicts constant velocity for one interval; seeded unknown
     acceleration represents motion not captured by that mean prediction.
   - **Incorrect:** measurement noise physically accelerates the target.

2. What does an innovation outside `+/-2 sqrt(S)` mean?
   - **Correct:** the report-prediction disagreement is surprising under the
     assumed state and measurement uncertainties.
   - **Incorrect:** it proves the target truth is outside the radar beam.

3. Why do position and velocity gain have different units?
   - **Correct:** both multiply a metre innovation; position gain is
     dimensionless and velocity gain must convert metres to metres per second.
   - **Incorrect:** every Kalman gain is a unitless probability.

4. Why do gains settle after initialization?
   - **Correct:** repeated predict/update covariance recursion approaches a
     balance for fixed F, Q, H, and R.
   - **Incorrect:** the filter learns the future random accelerations.

## Prediction checks

1. Predict the effect of raising Q with R fixed.
   - **Correct:** predicted covariance grows more, generally raising gain and
     accepting more measurement correction.
   - **Incorrect:** the already-generated reports become noisier.

2. Predict the effect of raising R with Q fixed.
   - **Correct:** the report is declared less trustworthy, S grows, and gain
     generally falls toward prediction.
   - **Incorrect:** process acceleration becomes smaller.

3. Predict the result of Q zero in this accelerating scene.
   - **Correct:** the filter becomes overconfident in exact CV motion and can
     lag velocity changes with bounds too narrow for actual error.
   - **Incorrect:** Q zero is mathematically impossible for every target.

4. Predict the result of assuming `0.5 m` measurement noise when actual report
   noise is `25 m`.
   - **Correct:** the filter report-chases and normalized innovations reveal
     severe overconfidence.
   - **Incorrect:** sensor noise physically shrinks to `0.5 m`.

## Interpretation and failure checks

1. Is innovation the same as truth error?
   - **Correct:** no; it is report minus predicted report and is available
     without simulation truth.
   - **Incorrect:** yes; the tracker observes exact truth every scan.

2. Does a narrow P bound guarantee a better state estimate?
   - **Correct:** no; P is conditional on assumptions and can be narrow because
     Q or R was underestimated.
   - **Incorrect:** yes; confidence and correctness are identical.

3. Does Q inject random samples into the estimated state?
   - **Correct:** no; Q expands predicted covariance, while the state changes
     through F and the measurement innovation.
   - **Incorrect:** yes; Q is added directly to x_hat.

4. Why use `K = P_pred*H'/S` instead of a matrix inverse?
   - **Correct:** S is scalar for one position report, so scalar division is
     explicit, sufficient, and numerically clearer.
   - **Incorrect:** an inverse is hidden inside a tracking toolbox object.

5. Why use the Joseph covariance correction?
   - **Correct:** it preserves covariance symmetry and nonnegative variance
     more robustly under finite precision.
   - **Incorrect:** it changes the target motion model from linear to nonlinear.

6. Does two-sigma coverage near 95% on this record prove calibration?
   - **Correct:** no; it is a descriptive finite, correlated, single-seed
     diagnostic. Statistical proof needs an appropriate ensemble.
   - **Incorrect:** yes; every future track must have exactly 95% coverage.

7. Does P55 solve range-bearing nonlinearity or data association?
   - **Correct:** no; it assumes one scalar position report already belongs to
     one track. P56 and P57 add those mechanisms.
   - **Incorrect:** a small innovation proves report identity and linearity.

## Determinism, compatibility, and resource checks

- A private `mt19937ar` stream uses seed `5501`; global random state is not
  changed.
- One truth and report record is shared by baseline, both three-case sweeps,
  both broken mismatches, and exact reviewed recovery.
- The reviewed workload is 101 scans, ten filter runs, 1010 filter steps, and
  five figures tagged `P55`; every loop is bounded.
- The experiment performs no file, network, shell, timer, worker, service, or
  learner-state operation and requires no toolbox Kalman implementation.
- Script-local functions require MATLAB R2016b or later. Runtime compatibility,
  rendered plots, timing, and memory must be evidenced separately.

## Completion checklist

- [ ] I can state F, G, H, Q, and R with their physical roles.
- [ ] I can trace state/covariance prediction, innovation/S, gain, and correction.
- [ ] I can explain why larger Q increases measurement trust and larger R
  decreases it without changing the existing data.
- [ ] I can distinguish innovation, truth error, posterior P, and innovation S.
- [ ] I can diagnose under-Q and under-R overconfidence from bounds or NIS.
- [ ] I can explain why the reviewed tuning recovers both mismatch failures.

## Short teach-back rubric

In 60–90 seconds, answer the guiding question: **How do process noise and
measurement noise determine trust in prediction versus measurement?** A
complete teach-back must mention:

1. constant-velocity state prediction and covariance growth through Q;
2. innovation as report minus predicted report and S as its variance;
3. gain as relative predicted-versus-measurement uncertainty;
4. at least one under-Q or under-R overconfidence symptom; and
5. why two-sigma coverage or NIS from one seed is diagnostic, not proof.
