# Checks: clutter memory and Swerling fluctuation

Guiding question: Why do clutter and target amplitude fluctuate differently from white noise?

Use the six figure groups and console metrics. Explain the radar statistics and
physical behavior rather than MATLAB syntax.

## Observation checks

1. Which baseline plot shows that clutter mean power changes with range?
2. At lag one, how do the clutter and thermal-noise correlations differ?
3. In one dwell, which Swerling models hold one power and which redraw it each
   pulse?
4. After sixteen-pulse averaging, which pair has the larger clean dwell-power
   variability: I versus II, and III versus IV?
5. In the broken case, how do near- and far-range background crossing rates
   differ before recovery?

## Interpretation checks

6. Why is ground clutter not adequately described as louder white noise?
7. Why can the pooled clutter histogram have a wider tail even though the
   local speckle is complex Gaussian in this experiment?
8. What physical distinction do the slow and fast Swerling labels represent?
9. Why do more pulses average down Swerling II fades but not Swerling I fades?
10. Why does equal average SNR fail to specify one target-present threshold
    crossing rate?
11. Why is local normalization a recovery here but not a complete operational
    CFAR solution?

## Prediction checks

12. If adjacent-range correlation changes from 0 to nearly 1 while power stays
    fixed, what happens to the visible patch length and independent sample
    count?
13. At one pulse, how should the marginal power distributions of Swerling I
    and II compare? What about III and IV?
14. If 64 independent Swerling II powers are averaged, predict the clean-power
    coefficient of variation.
15. If `slow_time_correlation` becomes zero, what happens to clutter
    pulse-to-pulse memory while range correlation remains 0.85?
16. If the clutter profile becomes flat, what specific failure in Figure 6
    should disappear under the stated Gaussian model?

## Answers and evidence

1. Figure 1's prescribed/measured mean-power panel falls with range while the
   measured thermal-noise mean remains flat.
2. Clutter remains strongly positive near its prescribed 0.85 value; white
   noise fluctuates near zero away from lag zero.
3. Swerling I and III hold one dwell draw. Swerling II and IV redraw each
   pulse. The nonfluctuating target holds the ensemble mean everywhere.
4. I is more variable than II, and III is more variable than IV, because fast
   draws are averaged within the dwell.
5. The global threshold produces many near-range crossings and almost no
   far-range crossings. Local normalization brings both close to 5%.
6. Clutter has a range-dependent scale plus range and slow-time correlation;
   white noise is stationary and independent here.
7. Pooling different local Rayleigh scales creates a mixture. The aggregate
   distribution need not look like a single locally normalized Rayleigh law.
8. Slow models keep one cross-section draw over a dwell; fast models redraw
   from pulse to pulse.
9. Averaging independent exponential draws reduces variance. Repeating one
   slow draw supplies no new target-power realization.
10. The statistic distribution depends on fluctuation depth and persistence,
    not only its mean power.
11. The recovery uses the exact simulated local mean. A real detector must
    estimate background scale and handle edges, targets, and correlation.
12. Patches lengthen and the effective independent sample count decreases,
    even though the number of plotted range bins stays fixed.
13. Each pair has the same one-pulse marginal distribution. Their difference
    appears only across multiple pulses in a dwell.
14. Approximately `1/sqrt(64)=0.125`, before finite-trial variation.
15. Each pulse gets a fresh field, so slow-time correlations away from zero
    vanish; within-pulse range correlation remains.
16. Near and far cells would share one expected scale, so the range-dependent
    imbalance caused by the global mean would disappear.

## Short teach-back rubric

A complete teach-back should state all four ideas in about a minute:

- thermal noise is independent and stationary in this model, while clutter
  has range-dependent power and correlation;
- Swerling I/III are slow dwell-held power models and II/IV are fast
  pulse-redrawn models, with III/IV having lower power variance;
- independent fast fluctuation averages down with pulse count, while a slow
  fade remains, so equal average SNR does not imply equal stability;
- one global white-background threshold fails on heterogeneous clutter, and
  known local power normalization recovers the reference rate only within the
  stated model.

Before personal completion, use Figures 2, 5, and 6 to identify one memory
effect, one fluctuation effect, and the broken assumption plus recovery.
