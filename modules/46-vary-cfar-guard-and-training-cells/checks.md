# Checks: CFAR window geometry

## Observation checks

1. With `G=0`, does the strong target cell sit above or below its CA-CFAR
   threshold? Which plotted samples raised that threshold?
2. In the training sweep, which case has the roughest observed background
   estimate in the quiet region? Which has the largest deterministic locality
   error at the gradual clutter transition?
3. How many edge CUTs are excluded for a stencil with `T` training and `G`
   guard cells per side?
4. In the broken case, is cell 126 a training cell, guard cell, or CUT when
   cell 138 is tested with `G=4, T=12`?

## Prediction checks

1. If the compressed target response becomes twice as wide while `G` stays
   fixed, what should happen to training contamination and target margin?
2. If `T` increases but `alpha` is accidentally left at its old value, have you
   isolated a window-size change? Why not?
3. If the background is perfectly homogeneous and reference cells are
   independent, what benefit should more training cells provide? What new cost
   appears when the background changes over range?
4. Would widening `G` always repair several unknown interfering targets?
   Explain when ordered-statistic CFAR would be the more credible next tool.

## Interpretation checks

- Correct: guards exclude expected target-response energy from the background
  estimator; they do not reduce the physical sidelobes.
- Correct: more training cells reduce sampling variability only while those
  cells remain representative of the CUT background.
- Correct: a smooth threshold can be locally biased across a clutter change.
- Correct: the finite-`N` `alpha` must be recomputed whenever `T` changes.
- Incorrect: every non-target-looking crossing near a strong sidelobe is an H0
  false alarm suitable for estimating `Pfa`.
- Incorrect: the broken weak-target miss proves the weak target's SNR changed;
  its CUT power is unchanged while a contaminated reference raises threshold.

## Completion checklist

- [ ] I can map `T` and `G` to the exact leading and lagging reference indices.
- [ ] I can identify self-masking in the guard sweep.
- [ ] I can distinguish threshold roughness from locality bias.
- [ ] I can explain why the very wide training case is smooth but poor near the
      transition.
- [ ] I can identify the contaminating cell and explain the bounded recovery.
- [ ] I can state why the recovery is not a universal CA-CFAR setting.

## Short teach-back rubric

In two or three sentences, justify a window for an expected target response and
background variation. A complete answer says guards must cover material target
energy, training cells must be numerous enough for a stable linear-power mean
but local enough to represent the CUT, and unexpected reference targets require
a different geometry or a more robust CFAR family rather than blind averaging.
