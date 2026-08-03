# P34 checks: Plot and Interpret the Ambiguity Function

Guiding question: **How does a waveform respond to simultaneous delay and Doppler mismatch?**

Use the figures and printed metrics. These are interpretation checks, not a
MATLAB syntax quiz.

## Observation checks

1. Which equal-duration waveform has the broadest zero-Doppler delay cut?
2. Which surface has a diagonal ridge through the origin?
3. What stays on the chip-duration scale as code length grows, and what gets
   narrower?

Passing observation: you identify the rectangular pulse's broad delay cut,
the LFM ridge, the phase code's chip-scale delay width, and its narrowing
Doppler width with more chips.

## Prediction checks

1. If rectangular-pulse duration doubles, predict the directions of full
   -3 dB delay width and Doppler width.
2. If LFM bandwidth doubles at fixed duration, predict zero-Doppler delay
   width and the magnitude of ridge displacement at a fixed Doppler.
3. If the Doppler plotting grid is made four times denser without changing
   pulse duration, predict whether physical Doppler tolerance changes.

Passing prediction: longer rectangular duration widens delay and narrows
Doppler; more LFM bandwidth narrows delay and reduces fixed-Doppler coupling
shift; plot density alone changes neither waveform property.

## Interpretation checks

1. Explain what one bright cell `|chi(tau,nu)|` means physically.
2. Distinguish a zero-Doppler cut from the complete ambiguity surface.
3. Explain why normalized magnitude cannot compare transmitted energy or
   detection SNR.
4. Explain why LFM ridge displacement is coupling rather than another target.
5. Explain why code length alone does not determine peak sidelobe level.

Passing interpretation: you connect coherent sample addition to joint
mismatch, use each cut for the correct axis, preserve the normalization
boundary, and distinguish waveform structure from a target scene.

## Failure and recovery checks

1. Why does the broken rectangular delay cut remain at one near the record
   boundary?
2. When would circular shifting describe a different valid model, and why is
   that model wrong for an isolated transmitted pulse?
3. What exact state and operation does recovery restore?

Passing recovery: you identify modulo wraparound, require zero-filled linear
overlap for propagation delay, and restore both the private code seed and the
explicit ambiguity sum. A clean rerun reproduces the exact surface. If needed,
cancel with Ctrl+C; there is no worker, timer, external transaction, or
persistent resource to clean up, and only figures tagged `P34` are closed.

## Completion checklist

- [ ] I can locate and interpret the ambiguity mainlobe and sidelobes.
- [ ] I can use the zero-Doppler and zero-delay cuts without confusing them.
- [ ] I can predict the duration, bandwidth, and code-length sweep directions.
- [ ] I can explain LFM delay-Doppler coupling from `nu = K*tau`.
- [ ] I can diagnose circular wraparound and recover zero-filled delay.
- [ ] I know this base MATLAB simulation is not hardware, field, real-time,
      detector, or operational-radar validation.

## Short teach-back rubric

Give two or three sentences that include all three ideas:

1. The ambiguity surface is normalized matched response versus simultaneous
   delay and Doppler mismatch.
2. Duration, bandwidth, chip duration, and code pattern shape different parts
   of the surface.
3. The best waveform depends on required delay resolution, Doppler tolerance,
   sidelobes, and acceptable coupling.

Completion means you can point to the main lobe and explain which waveform is best for a chosen delay/Doppler requirement. Personal completion is recorded only after this teach-back through the learner CLI under ignored `.learning/` state.
