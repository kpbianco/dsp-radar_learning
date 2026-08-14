# P82: Build a Passive Radar Cross-Ambiguity Experiment

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Implemented by governed batch `P82`

## Guiding question

How can a known broadcast-like reference reveal delayed Doppler-shifted echoes without transmitting?

## Experiment

A deterministic complex baseband waveform stands in for a broadcast
illuminator. The reference receiver observes a high-quality copy. The
surveillance receiver observes strong zero-delay leakage, one delayed static
multipath copy, a much weaker delayed `+500 Hz` target echo, and noise. The
script evaluates the normalized cross-ambiguity sum explicitly on a delay and
Doppler grid before and after a one-coefficient least-squares direct-path
canceller.

The target is hidden by the origin peak before cancellation and is the map
maximum at `24` samples and `+500 Hz` afterward. Controlled cases then vary
target delay, target Doppler, coherent integration time, and reference-channel
quality. An intentionally under-cancelled case leaves the origin dominant;
recovery reprocesses the unchanged measured channels with the full projection.

## Learning goal

Explain why a passive receiver needs both a reference and a surveillance
channel, how delay and Doppler become the two matched coordinates, why the
direct path can dominate the map, and why coherent time and reference quality
control visibility. Distinguish bistatic excess path from monostatic range and
a one-tap teaching canceller from practical multipath cancellation.

## Prerequisites and dependencies

- P08 supplies correlation as a hidden-pattern locator.
- P18 supplies signed frequency in complex I/Q.
- P26 supplies adaptive interference-cancellation intuition.
- P34 supplies waveform ambiguity and mismatch intuition.
- P36 and P42 supply Doppler phase and range-Doppler map interpretation.
- Runtime target: base MATLAB R2016b or newer; no toolbox, external data, or
  transmitted waveform is used.

The illuminator, channels, delays, Dopplers, and cancellation coefficient are
known synthetic teaching quantities. The map is not a calibrated bistatic
range/velocity product and does not model antennas, synchronization
estimation, propagation geometry, broadcast standards, or operational clutter.

## Run

```matlab
cd modules/82-build-a-passive-radar-cross-ambiguity-experiment
run('experiment.m')
```

Then follow `walkthrough.md` one transition at a time and use `checks.md` for
the completion conversation. The script writes no files and performs no
network, timer, worker, GPU, or external-process operation.

## Files

- `experiment.m` — deterministic channel synthesis, explicit cancellation and
  cross-ambiguity, four controlled variations, failure, recovery, assertions,
  plots, and resource ceilings
- `lesson.md` — physical signal model, equations, limiting cases,
  dependencies, and interpretation traps
- `walkthrough.md` — baseline observation, one-variable changes, failure,
  recovery, and concept connection
- `checks.md` — answered observation/prediction checks and teach-back rubric

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Keep the guiding question exactly:
"How can a known broadcast-like reference reveal delayed Doppler-shifted echoes
without transmitting?" Begin with the reference and surveillance channels,
then show the explicit cross-ambiguity sum before naming the result. Compare
the same measurement before and after direct-path projection. Change target
delay, target Doppler, coherent integration time, and reference quality while
holding the other controls fixed. Deliberately under-cancel the direct path and
recover from the unchanged channels. Separate bistatic excess path from
monostatic range, signed Doppler from speed, one-tap cancellation from practical
multipath suppression, static/simulated evidence from MATLAB runtime evidence,
and physical meaning from MATLAB syntax.
