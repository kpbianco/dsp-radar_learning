# P50 checks: Apply 2-D CFAR to a Range-Doppler Map

Use these after the baseline, both one-variable sweeps, and the intentionally
broken case. Personal completion still requires a short teach-back.

## Observation checks

1. What two background changes are visible before any threshold is applied?
   - Expected: mean power grows gradually with range and forms a ridge near
     zero radial velocity.
2. What do the baseline target arrays report?
   - Expected: targets 1–3 are testable and detected; target 4 is not testable
     and therefore has no valid decision.
3. Why is `results.training_cell_count` 196?
   - Expected: the 17-by-13 outer rectangle has 221 cells; subtracting the
     5-by-5 guard+CUT rectangle leaves `221-25=196` training cells.
4. Where are threshold values `NaN`?
   - Expected: in the range and Doppler border bands where the complete outer
     rectangle does not fit.

## Prediction checks

1. If only `training_range_half_width` grows, which border changes?
   - Expected: more top/bottom range rows become untestable; the Doppler border
     width stays fixed.
2. If only `training_doppler_half_width` grows, which border changes?
   - Expected: more left/right Doppler columns become untestable; the range
     border width stays fixed.
3. If every map power is multiplied by four, what happens to the threshold and
   decisions in the ideal arithmetic?
   - Expected: every eligible local mean and threshold also multiplies by four,
     so CUT/threshold ratios and decisions stay unchanged.
4. If target spread reaches beyond the guards, what can happen?
   - Expected: target energy enters the training annulus, raises the CA mean,
     and can mask the target or a nearby weaker target.

## Interpretation checks

Mark each statement correct or incorrect and explain why.

1. “The border target is a miss.”
   - Incorrect. The baseline has no full-stencil test at that cell.
2. “The 2-D training region is two crossed 1-D strips.”
   - Incorrect. The rectangular annulus includes corner training cells.
3. “Because the threshold is plotted in dB, the detector should average dB.”
   - Incorrect. CA-CFAR averages linear square-law power; dB is display only.
4. “More training cells always improve detection.”
   - Incorrect. They reduce homogeneous estimate variance but reach farther
     into potentially different range/Doppler background and consume borders.
5. “The requested `Pfa=1e-3` was validated by this one map.”
   - Incorrect. It is a nominal IID-exponential design setting. P52 owns
     repeated rare-event validation.
6. “Zero padding is harmless because it produces finite thresholds.”
   - Incorrect. Invented zero-power references bias border estimates and do not
     satisfy the calibrated full-window model.

## Numeric and resource checks

- Confirm `results.training_cell_count == 196`.
- Confirm `results.target_is_detected(1:3)` are true and
  `results.target_is_testable(4)` is false.
- Confirm both sweep training-count arrays increase and both eligible-fraction
  arrays decrease.
- Confirm every retained array stays within the reviewed
  `max_stored_numeric_values` ceiling and the estimated stencil work stays
  within `max_training_sample_visits`.
- Confirm `results.broken_all_cells_calibrated_claim_is_valid == false` and
  `results.recovery_detection_matches_baseline == true`.

## Short teach-back rubric

In two or three sentences, answer the guiding question. A complete answer:

- says that each eligible range-Doppler CUT is compared with a scaled average
  of linear power from a guarded 2-D training annulus;
- distinguishes range extent from Doppler/velocity extent and connects guards
  to target response spread; and
- explains that a complete stencil is unavailable at map borders, so this
  implementation reports no decision there rather than inventing references.

Do not mark personal completion from plot appearance alone. The learner should
correctly explain the no-decision border and why the broken finite edge
threshold is not calibrated.
