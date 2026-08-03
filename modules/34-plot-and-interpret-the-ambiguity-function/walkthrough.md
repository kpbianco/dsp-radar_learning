# P34 walkthrough: Plot and Interpret the Ambiguity Function

Guiding question: **How does a waveform respond to simultaneous delay and Doppler mismatch?**

Run `experiment.m` once from this module folder. It uses base MATLAB, bounded
arrays and loops, and a private deterministic stream for the phase code. It
does not change the global random stream.

## Baseline observation: compare the same coordinates

Start with the `P34 waveform phase histories`,
`P34 baseline ambiguity surfaces`, and `P34 ambiguity cuts and LFM ridge`
windows, plus the printed baseline metrics. MATLAB window numbers depend on
other figures already open, so use these stable names throughout the lesson.

1. `P34 waveform phase histories` shows equal-duration rectangular, LFM, and
   binary phase-coded waveforms. Compare phase behavior, not just their unit
   envelopes.
2. In `P34 baseline ambiguity surfaces`, locate
   `(0 microseconds, 0 kHz)` on every surface. Each is one there because
   magnitude is normalized by its own energy.
3. Follow the rectangular surface away from the origin. Its broad delay
   response comes from simple time overlap.
4. Follow the LFM brightness diagonally. Positive Doppler mismatch moves the
   best response to positive delay under the script's sign convention.
5. Look for the phase code's compact delay mainlobe and structured sidelobes.
6. In `P34 ambiguity cuts and LFM ridge`, compare zero-Doppler delay widths
   separately from zero-delay Doppler widths. Then read the LFM ridge rather
   than inferring the full surface from either cut.

Expected observation: LFM and phase coding sharpen delay response relative to
an equal-duration unmodulated pulse, while finite duration still sets a broad
scale for Doppler response. LFM's narrow response is tilted in the joint
plane.

## Sweep one variable: rectangular duration

`P34 rectangular-duration sweep` uses `[6.5 13 26]` microseconds with
amplitude and sample rate fixed.

- Track full -3 dB delay width upward as the pulse gets longer.
- Track full -3 dB Doppler width downward.
- Do not call the narrower Doppler cut a pulse-train velocity estimate. It is
  the single-pulse coherent mismatch response.

Expected observation: an unmodulated pulse trades delay discrimination for
Doppler tolerance through its duration.

## Sweep one variable: LFM bandwidth

`P34 LFM-bandwidth sweep` uses `[1.5 3 4.5]` MHz at the same 13-microsecond
duration.

- Track zero-Doppler delay width downward as bandwidth grows.
- At the fixed +120 kHz Doppler probe, track the peak delay toward zero.
- Relate the movement to `tau = nu/K` and `K = B/T`.

Expected observation: more bandwidth narrows the delay cut and steepens chirp
rate, reducing the delay displacement for a fixed Doppler mismatch.

## Sweep one variable: code length

`P34 phase-code-length sweep` uses seeded prefixes of `[7 13 31]` chips while
each chip remains one microsecond.

- Confirm that delay width remains on the chip-duration scale.
- Track Doppler width downward as total code duration grows.
- Observe the sidelobe metric without expecting monotonic improvement. The
  added polarities change the code correlation as well as its duration.

Expected observation: chip duration and total duration control different
axes, while code selection controls the off-origin delay structure.

## Intentionally broken case: make delay circular

`P34 circular-shift failure and recovery` replaces zero filling with modulo
indexing only in the broken path.

- At the largest-magnitude delay, the correct rectangular-pulse overlap has
  only one shared sample and normalized magnitude `1/N`.
- The broken curve stays at one because samples leaving one end re-enter at
  the other.
- Reject the interpretation that a long isolated pulse physically matches
  itself at every delay. The algorithm silently changed the signal into a
  periodic record.

This is a boundary-condition failure, not a new ambiguity property.

## Recover and connect the concept

The recovery restores explicit linear overlap bounds, reconstructs the
private code from seed 3401, and recomputes the full phase-code surface. The
script asserts exact equality with the baseline surface.

Say the connection in one sentence: **the ambiguity function is the matched
response over joint delay and Doppler mismatch, so waveform duration,
bandwidth, and phase pattern trade delay width, Doppler width, sidelobes, and
coupling rather than optimizing one universal score.**

## Safe cancellation, clean rerun, and rollback

- Press Ctrl+C to cancel. Every loop has a validated finite delay, Doppler, or
  sweep bound; there is no worker, timer, network call, file write, external
  transaction, or hardware session to leave running.
- Rerun the whole script for recovery. It closes only figures tagged `P34`,
  reconstructs the private seed, and leaves the global random stream and
  unrelated figures unchanged.
- The experiment never reads or writes `.learning/`; learner completion stays
  isolated in ignored CLI state.
- Batch rollback removes the four P34 implementation artifacts, P34 test, and
  P34 evidence; restores the scaffold README and P34 manifest status to
  `scaffolded`; and restores the public catalogs. It preserves P01-P33 and all
  later module identities.

Completion means you can point to the main lobe and explain which waveform is best for a chosen delay/Doppler requirement.
