# P56 checks: explain the geometry before marking complete

Guiding question: **How can nonlinear radar measurements update Cartesian target state?**

## Observation checks

1. **Raw reports:** In Figure 1, why is the converted report cloud stretched
   mainly across the line of sight?
   - **Correct:** bearing error creates tangential displacement, while range
     error creates radial displacement.
   - **Incorrect:** x and y sensors have fixed independent noise everywhere.

2. **Branch cut:** Did the target physically reverse direction when displayed
   bearing crossed from positive to negative near `180 deg`?
   - **Correct:** no; only the `atan2` coordinate convention wrapped.
   - **Incorrect:** yes; bearing changed by almost a full turn.

3. **Smoothing:** After the warm-up, which position history is less scattered?
   - **Correct:** the EKF trajectory, because prediction and polar evidence are
     fused across scans.
   - **Incorrect:** raw conversion, because coordinate conversion is itself a
     tracker.

4. **Ellipse orientation:** Why do the covariance ellipses rotate?
   - **Correct:** radial and tangential directions rotate with line of sight.
   - **Incorrect:** the plot axes or sensor noise units changed between scans.

5. **Innovations:** Which residual is wrapped, and which is not?
   - **Correct:** bearing is wrapped to a local angle; range remains an ordinary
     metric difference.
   - **Incorrect:** both range and bearing should be wrapped.

6. **NIS:** Why can metres and radians contribute to one dimensionless NIS?
   - **Correct:** `S` carries their units, scale, and correlation.
   - **Incorrect:** the script silently converts range into degrees.

## Prediction checks

7. If assumed bearing standard deviation changes from `0.8` to `3.2 deg` while
   reports stay fixed, predict tangential posterior uncertainty.
   - **Correct:** it generally widens because direction is declared less
     precise.
   - **Incorrect:** it narrows because a larger number means more confidence.

8. At fixed `0.8 deg` angular accuracy, predict cross-range standard deviation
   when range doubles.
   - **Correct:** it approximately doubles in the small-angle limit
     `sigma_t = r*sigma_theta`.
   - **Incorrect:** it stays fixed because angular standard deviation stayed
     fixed.

9. If the measured report exactly equals `h(x_pred)`, what is the immediate
   state correction?
   - **Correct:** zero, because the innovation is zero.
   - **Incorrect:** nonzero, because Q always pushes the estimated state.

10. If the target approaches the radar origin, what happens to the bearing
    Jacobian?
    - **Correct:** its `1/r^2` terms become singular or ill-conditioned, so this
      reviewed EKF stops inside its minimum range.
    - **Incorrect:** it becomes more linear and needs no guard.

## Failure and recovery checks

11. Why does the broken unwrapped filter see a huge residual near the branch
    cut?
    - **Correct:** ordinary subtraction ignores that `+pi` and `-pi` are
      neighboring representations.
    - **Incorrect:** true target acceleration suddenly becomes enormous.

12. Why must recovery rerun the same reports rather than generate a new scene?
    - **Correct:** then angle wrapping is the only changed cause and exact state
      recovery is testable.
    - **Incorrect:** a new random record is required to prove the old record was
      wrong.

13. If NIS is large after setting bearing noise to `0.2 deg`, what is the first
    interpretation?
    - **Correct:** the assumed innovation covariance may be too small for the
      fixed reports.
    - **Incorrect:** low assumed noise physically improves the reports already
      measured.

14. What should you do after `P56:LinearizationSingularity`?
    - **Correct:** repair initialization/geometry or choose a method suited to
      near-origin uncertainty, then rerun from the top.
    - **Incorrect:** remove the range guard and accept division by nearly zero.

## Model and implementation checks

15. State the nonlinear prediction and the two Jacobian rows without discussing
    MATLAB syntax.
    - **Correct:** `h=[sqrt(px^2+py^2); atan2(py,px)]`; the first row is radial
      `[px/r,0,py/r,0]`, and the second is tangential
      `[-py/r^2,0,px/r^2,0]` for `[px,vx,py,vy]`.
    - **Incorrect:** `H` is a fixed Cartesian position selector.

16. Where is `H` evaluated?
    - **Correct:** at the predicted state before the measurement correction.
    - **Incorrect:** at unavailable truth or after the report has already
      corrected the state.

17. Why use the Joseph covariance update?
    - **Correct:** it better preserves covariance symmetry and nonnegative
      variance under finite precision.
    - **Incorrect:** it makes the nonlinear measurement model exact globally.

18. What remains outside P56?
    - **Correct:** P57 owns gating and association; operational calibration,
      maneuver models, track lifecycle, and real sensor effects also require
      more evidence.
    - **Incorrect:** this one-track synthetic EKF proves a complete operational
      radar tracker.

## Resource, compatibility, and claim checks

Confirm that the reviewed script uses seed `5601`, 101 scans, exactly three
bearing-noise cases, exactly three geometry ranges, five tagged figures, six
filter runs, no more than 600 predict/update transitions, and no more than 73
points per displayed ellipse. It uses base MATLAB and local functions compatible with
MATLAB R2016b or later. Ctrl+C cancels the finite foreground run; a clean rerun
reconstructs all state and changes no learner progress, file, service, device,
or network resource.

Repository tests provide deterministic static and host-language evidence. They
do not claim MATLAB execution, rendered figures, timing, memory, statistical
calibration, manual learning effectiveness, hardware/HIL, field, real-time,
deployment, or production behavior.

## Completion checklist

- [ ] I can explain why a range-bearing report is nonlinear in Cartesian state.
- [ ] I can identify radial and tangential rows of the Jacobian and their units.
- [ ] I can explain why fixed angular noise maps to more metres at longer range.
- [ ] I can explain why only the bearing innovation is wrapped.
- [ ] I can distinguish raw polar conversion from sequential EKF tracking.
- [ ] I can interpret a covariance ellipse and NIS without treating one seed as
      a statistical guarantee.
- [ ] I can describe the broken branch-cut case and deterministic recovery.

## Short teach-back rubric

In three or four sentences, answer the guiding question. A passing teach-back
must connect `h(x_pred)` and its local Jacobian to the Cartesian correction,
mention `R` in metres squared and radians squared, explain
`r*sigma_bearing_rad`, and state why the angular innovation is wrapped. Also
name one limit: near-origin geometry, poor initialization/large uncertainty,
single-seed evidence, or missing association. Do not mark personal completion
until the experiment completion condition has been observed and this teach-back
is conceptually correct.
