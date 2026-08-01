# P09 Walkthrough — Compare FIR and IIR Filters by Behavior

## Guiding question

How can two filters with similar magnitude response behave differently in time and phase?

## Before running

P08 is the prerequisite. Run `experiment.m` from this module folder in base
MATLAB. It writes no files or learner progress, preserves the global random
stream and unrelated figures, and closes only earlier figures tagged `P09`.
Named script variables in the current workspace are created or replaced.

Every record, grid, loop, and sweep is finite and checked against a fixed
ceiling before use. There is no pause, input prompt, animation, timer, callback,
external wait, background job, file I/O, network I/O, or device access. If local
graphics block, Ctrl+C cancels the finite foreground script; rerun it from the
top after correcting the graphics environment.

## Baseline: start with the frequency behavior

1. Inspect **comparable cutoff, different phase**. Confirm both minus-three-
   decibel markers land near `100 Hz`. Say “comparable cutoff,” not “identical
   filters”: the curves separate in the transition band and stopband.
2. Look at phase before group delay. The FIR phase is nearly a straight line in
   its passband. The IIR phase bends.
3. Read the delay plot at `60 Hz`. The FIR is exactly `10 samples`; the IIR is
   shorter there but varies with frequency. A lower value is not automatically
   better if pulse shape or relative timing matters.
4. Read the printed arithmetic counts. The 21-tap FIR uses `21` multiplications
   and `20` additions per output sample. The biquad IIR uses `5` and `4`.

Observation question: if both cutoff markers coincide, which plotted evidence
proves that the filters still cannot be substituted blindly?

## Baseline: inspect impulse, step, and pulse

1. In the impulse plot, find the FIR's last nonzero tap at sample `20`. The IIR
   continues to decay; its threshold metric is only what fits in this finite
   observation window.
2. In the step plot, compare when each output begins moving, whether it
   overshoots, and when it remains within two percent of final value.
3. In the pulse plot, inspect both edges. The FIR's constant delay moves the
   waveform; the IIR's nonlinear phase and feedback change its shape as well as
   its apparent timing.
4. Do not shift either causal output just to make the overlay look favorable.

## Baseline: apply the same noisy multitone

The input contains a `60 Hz` desired tone, a `250 Hz` interferer, and `0.15 V`
RMS seeded noise. Both filters see the identical samples.

- Compare the time outputs between `100` and `180 ms`; they need not align.
- Compare the two bar pairs. Both pass 60 Hz, while the longer FIR rejects
  250 Hz more strongly.
- One deterministic seed demonstrates cause and effect. It does not establish a
  noise distribution, detection rate, or operational receiver result.

## Sweep 1: change only FIR tap count

Run **Parameter sweep 1** and compare `9`, `21`, and `41 taps`.

- The window family, design cutoff, sample rate, and step input are unchanged.
- Stopband rejection and transition sharpness generally improve with more taps.
- Constant group delay rises from `4` to `10` to `20 samples`.
- At `1000 samples/s`, those delays are also `4`, `10`, and `20 ms`. If sample
  rate changed, the sample delays would stay tied to order while seconds change.

Choose the 41-tap case only if the extra rejection is worth its computation and
latency. “FIR” alone does not imply low delay.

## Sweep 2: change only IIR Q

Run **Parameter sweep 2** and compare `Q = 0.5`, `1/sqrt(2)`, and `2`.

- Filter order, nominal cutoff, sample rate, and step input are unchanged.
- Pole radius and overshoot rise monotonically with Q in this controlled set.
- The `Q = 2` case rings and peaks more, but its poles remain inside the unit
  circle. It is aggressive, not yet unstable.
- Because Q changes magnitude as well as time response, use this sweep to study
  damping; do not keep claiming the three curves have matched magnitude.

## Broken case

Run **Deliberately broken case**. The conjugate poles use radius `1.02`, outside
the unit circle. On the logarithmic plot, the late impulse-response window has
more RMS energy than the early window. The fixed horizon prevents this teaching
case from consuming unbounded time or memory; it does not make the filter
stable.

Classify the failure as unstable feedback. It is not ordinary passband ripple,
an FIR truncation effect, a random-noise event, or a plotting scale problem.

## Recovery and rollback

Recovery changes only pole radius from `1.02` to `0.98`, preserving pole angle,
DC normalization, impulse input, and record length. The recovered late/early RMS
ratio falls below `0.2`, and the tail decays.

If an edited control is malformed, an assertion stops before P09 figures are
replaced. Restore the committed finite scalar/vector controls, stable baseline
poles, odd FIR tap counts, ordered sweep values, and fixed ceilings, then rerun
from private seed 909. No persistent file, external transaction, or learner
state needs recovery. Repository rollback is confined to the P09 artifacts and
shared P09 status/catalog/test edits; restore the manifest entry to `scaffolded`
if the implementation is removed.

The threshold and settling metrics also report a `found` flag. If no impulse
sample exceeds an edited threshold, or no step suffix stays within an edited
tolerance over the finite record, the corresponding sample metric is `NaN` and
`found=0`; the script does not mislabel the record endpoint as settling.

## Concept connection

P06 exposed a system through its impulse response, P07 made finite convolution
visible, and P08 used a sliding sum to locate a pattern. P09 adds feedback and
frequency-domain phase: two systems can agree on a cutoff while remembering and
delaying the same waveform differently.

For a radar-oriented choice, name the required passband/stopband behavior,
allowable latency, pulse-shape or phase fidelity, computation budget, numeric
precision, and stability margin. Then choose FIR or IIR from those requirements.

## Completion handoff

Use `checks.md`. To meet the canonical completion condition, give one example
where the FIR is the defensible choice and one where the IIR is, using observed
metrics rather than filter-family preference. Finish with the short teach-back
before recording personal completion locally.
