# P21 Checks — Carrier, Sidebands, and Envelope Sign

## Guiding question

How does a baseband waveform create RF sidebands?

Use the console metrics and one plot at a time. These checks test prediction
and interpretation, not MATLAB syntax.

## Baseline observations

1. For `fc=3000 Hz` and `fm=200 Hz`, where are the carrier and both sidebands?
2. With `Ac=1 V` and `mu=0.60`, what is each ideal sideband amplitude? Compare
   `Ac*mu/2` with the measured spectrum.
3. Which time-domain quantity follows the normalized message: the instantaneous
   RF samples or the carrier's signed envelope?
4. Why are the upper and lower sideband amplitudes equal for a real cosine
   message and real cosine carrier?

## Multitone and sweep predictions

1. Before looking, predict every RF line produced by baseband tones at `100`
   and `350 Hz` around a `3000 Hz` carrier.
2. Which multitone sideband pair should be larger, and why?
3. Before reading the depth sweep, predict the first `mu` for which the signed
   envelope can become negative when `|m(t)| <= 1`.
4. Before reading the frequency sweep, predict what changes when `fm` doubles:
   sideband offset, sideband amplitude, or both.
5. Why does the clean coherent-recovery error stay small through the
   over-modulated point while magnitude-envelope error grows?

## True or false

1. A `200 Hz` message changes the `3000 Hz` carrier into one line at `3200 Hz`.
   **False.** Real AM retains the carrier and makes symmetric lines at `2800`
   and `3200 Hz`.
2. Modulation depth controls sideband spacing. **False.** Message frequency
   controls spacing; depth and message amplitude control sideband amplitude.
3. A lower sideband at `2800 Hz` is a negative frequency. **False.** It is a
   positive RF frequency below the positive carrier.
4. At `mu=1`, the ideal signed envelope just touches zero for a full-scale
   negative message. **True.** It becomes negative only above one.
5. Over-modulation removes the signed message from the transmitted waveform.
   **False.** Magnitude detection loses the sign; aligned coherent mixing can
   retain it.
6. Every real baseband tone creates a pair of RF offsets under real-cosine AM.
   **True.** The product identity creates sum and difference frequencies.

## Broken-case diagnosis

1. Why does the analytic-signal magnitude fold the negative envelope upward?
   Absolute value maps both `+e(t)` and `-e(t)` to the same magnitude.
2. What physical event accompanies negative signed envelope? The carrier has
   reversed phase by 180 degrees during that interval.
3. What extra information lets coherent detection distinguish the reversal? A
   frequency- and phase-aligned carrier reference preserves the mixer's sign.
4. Would a badly phase- or frequency-offset coherent reference still recover
   perfectly? No. A constant phase error scales or reverses the recovered
   baseband projection, while a frequency error creates a time-varying beat.
   The separated high-frequency mixer product can still be low-passed, so
   “coherent” is not automatically “correct.”

## Malformed input, resource, and recovery checks

- A logical seed, nonfinite sample rate, complex carrier, changed sweep vector,
  odd or oversized record, out-of-band message, expanded figure count, or
  numeric-storage ceiling above the canonical value must stop before random
  generation, signal allocation, FFT work, P21 cleanup, or figure creation.
- Ctrl+C is the timeout/cancellation path for this bounded foreground script.
  A full rerun replaces only P21-tagged figures and reconstructs `results` from
  private seed `1021` without changing the global random stream.
- No file, network, audio, device, worker, learner state, or persistent external
  data is opened, so cancellation has no external transaction to roll back.

## Teach-back completion

In two or three sentences, answer the guiding question. A complete answer must
predict `fc-fm` and `fc+fm`, connect modulation depth to sideband amplitude,
explain the signed-envelope zero crossing above `mu=1`, and state why coherent
detection can recover sign that envelope magnitude discards. Also name one
limiting assumption, such as a real message, separated bands, coherent
reference alignment, or ideal finite-record filtering.
