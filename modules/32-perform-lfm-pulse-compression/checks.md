# P32 checks: Perform LFM Pulse Compression

Guiding question: **How can a long energetic pulse achieve short-pulse range resolution?**

Use the figures and printed metrics. These are interpretation checks, not a
MATLAB syntax quiz.

## Observation checks

1. What is much longer in Figure 2 than in Figure 3: the raw echo extent or the
   compressed response width?
2. At `[4 8 16]` MHz, does the measured full -3 dB width rise or fall?
3. At `[5 10 20]` microseconds with fixed 8 MHz bandwidth, which changes more:
   compressed width or `BT` processing gain?

Passing observation: you identify the long overlapping raw echoes, decreasing
bandwidth-sweep widths, and nearly constant duration-sweep widths.

## Prediction checks

1. If bandwidth doubles from 8 to 16 MHz at fixed duration, predict the nominal
   `c/(2B)` range scale.
2. If duration doubles at fixed bandwidth and peak power, predict the energy
   ratio and processing-gain change.
3. If sample rate increases but waveform bandwidth remains 8 MHz, predict
   whether physical range resolution improves.

Passing prediction: nominal width halves with doubled bandwidth, energy and
`BT` double for a 3 dB gain, and sample rate alone does not improve physical
resolution.

## Interpretation checks

1. Explain why a constant-magnitude pulse can still occupy wide bandwidth.
2. Explain why the matched filter is `fliplr(conj(transmit_chirp))`.
3. Distinguish `Fs*T` sampled coherent gain from `B*T` pulse-compression gain.
4. Explain why LFM sidelobes are not automatically extra targets.

Passing interpretation: you connect phase slope to instantaneous frequency,
conjugate time reversal to coherent alignment, and each gain to its stated
input-noise convention.

## Failure and recovery checks

1. On Figure 6's shared recovered-peak dB scale, what happens to peak height and
   width with the `0.55B` replica?
2. Why can the mismatched peak move away from the true delay?
3. What exact operation restores the baseline response?

Passing recovery: you identify chirp-rate mismatch, not random noise, as the
cause and restore the conjugate time-reversed transmitted waveform. A clean
rerun recreates the private seed and exact baseline. If needed, cancel with
Ctrl+C; there is no worker, timer, external transaction, or persistent resource
to clean up, and only figures tagged `P32` are closed.

## Completion checklist

- [ ] I can predict how bandwidth changes compressed width.
- [ ] I can predict how time-bandwidth product changes gain.
- [ ] I can explain why long duration and fine range resolution can coexist.
- [ ] I can account for the matched-filter delay in the range axis.
- [ ] I can diagnose a mismatched replica and recover the correct response.
- [ ] I know this base MATLAB simulation is not hardware, field, real-time, or
      operational-radar validation.

## Short teach-back rubric

Give two or three sentences that include all three ideas:

1. LFM puts a frequency label across a long energetic pulse.
2. The matched filter aligns that phase history into a width governed mainly by
   bandwidth.
3. Increasing duration at fixed bandwidth raises `BT` and energy without
   substantially narrowing the compressed response.

Completion means you can predict how bandwidth changes compressed width and
how time-bandwidth product changes gain. Personal completion is recorded only
after this teach-back through the learner CLI under ignored `.learning/` state.
