# P06 Walkthrough — Use an Impulse to Reveal a System

## Guiding question

Why does an impulse response describe an LTI system?

## Before running

P05 is the prerequisite. Run `experiment.m` in base MATLAB from this module
folder. It uses a private seed and closes only earlier P06-tagged figures. It
writes no files and changes no learner progress, but its named script variables
are created or replaced in the current workspace.

## Baseline

1. Run through **Baseline controls** and inspect the two probes. The unit impulse
   isolates one instant; the general voltage record combines two tones, a short
   level change, and a small seeded broadband component.
2. Inspect **impulse responses reveal the systems** one panel at a time. Locate
   the delay tap, the nine equal moving-average taps, both echo taps, and the
   resonator's damped sinusoidal tail.
3. Move to **direct rule equals convolution**. Each solid direct output should
   lie on its dashed `conv(x,h)` reconstruction.
4. Read the numerical-agreement figure and printed metrics. Every maximum error
   must be below `comparison_tolerance_v`. That is this module's completion
   condition.

Observation question: which single response makes it easiest to point to a
physical second path, and what do its horizontal and vertical tap coordinates
mean?

## Sweep 1

Run **Parameter sweep 1 - change only echo delay**. Keep `echo_gain = 0.55`.
Compare `8`, `32`, and `64` samples of delay.

- Confirm that the second tap moves right while its height stays fixed.
- In the output plot, trace the same input feature and its delayed copy.
- Connect sample delay to milliseconds using `1000*delay/fs`.

Only path travel time changes. A radar interpretation is that the secondary
path length changes while its attenuation remains fixed.

## Sweep 2

Run **Parameter sweep 2 - change only resonator memory**. Compare radii `0.25`,
`0.70`, and `0.92`.

- Watch the `90 Hz` oscillation persist across more lags as the radius approaches one.
- Compare the printed decay time in samples and milliseconds.
- Notice that the output rings longer even though the input and resonant
  frequency are identical in all three cases.

The radius changes system memory, not input frequency, drive gain, or ring frequency.

## Broken case

Run **Deliberately broken case - unpadded FFT creates circular convolution**.
The dashed result is not the causal echo output because an `N`-point transform
forces the tail to wrap around to sample zero. The lower panel localizes the
error where wrapped samples appear. Classify this as a boundary/support error,
not a failure of LTI theory.

## Recovery

Use `conv(general_input_v, h_echo_path)` and keep the first `sample_count`
causal samples. For an FFT implementation, choose a transform length of at
least `2*sample_count-1` for these two length-`N` records. The recovered output
must again match the direct echo implementation below the voltage tolerance.

If plotting is interrupted, stop the finite script with Ctrl+C and rerun from
the top. Re-running from private seed 606 recovers the input and replaces only
P06-tagged figures; no partial file or learner-state cleanup is needed. Restore
the committed controls if malformed edits trigger an early assertion.

## Concept connection

The impulse response works because an LTI system applies the same shifted
response to every shifted impulse and adds the results. Say the echo example in
that language: each nonzero tap selects, scales, and delays a copy of the input.
Then contrast it with saturation or a moving channel, where one fixed response
would no longer predict every input or time.

## Completion handoff

Use `checks.md`. After the plot observations and predictions, give a short
teach-back that explains both why convolution succeeds and why circular
wraparound fails. Personal completion remains local and should be recorded only
after that teach-back.
