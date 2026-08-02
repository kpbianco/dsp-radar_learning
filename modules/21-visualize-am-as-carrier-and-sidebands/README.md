# P21: Visualize AM as Carrier and Sidebands

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Implemented by governed batch `P21`

## Guiding question

How does a baseband waveform create RF sidebands?

## Experiment

Amplitude-modulate a carrier first with one tone and then with a two-tone
message. Inspect the message, signed envelope, RF waveform, spectrum, and two
explicit recovery paths.

## Procedure

Run the deterministic baseline, map each baseband frequency to symmetric RF
sidebands, sweep modulation depth from under-modulated through over-modulated,
and sweep message frequency while the carrier stays fixed. The intentionally
broken case shows envelope inversion: magnitude detection folds the message,
while coherent detection retains its sign.

## What this teaches

Multiplication by a carrier translates every baseband spectral component to
both sides of the carrier. Modulation depth controls sideband amplitude. When
the signed envelope crosses zero, an ordinary envelope detector cannot know
that the carrier reversed phase, but a phase-referenced coherent detector can.

## Dependencies

P20 is the immediate curriculum prerequisite. P11–P13 supply FFT-bin and
finite-record spectrum intuition; P16 constructs an analytic signal; P17
explains coherent mixing; and P18–P20 establish signed frequency, receiver
quality, and coherent evidence. P21 uses only base MATLAB operations and no
external data, toolbox, service, or hardware dependency.

## Completion condition

You can predict sideband locations and explain why coherent detection still
works when envelope detection fails.

## Start

```bash
./bin/learn start 21
```

Then run `experiment.m` unchanged and follow `walkthrough.md` one plot or
processing transition at a time.

## Files

- `experiment.m` — seeded AM construction, spectra, recovery, sweeps, and failure
- `lesson.md` — physical model, equations, limiting cases, and radar connection
- `walkthrough.md` — baseline, two one-variable sweeps, broken case, and recovery
- `checks.md` — observation, prediction, interpretation, and teach-back checks

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. The guiding question is: "How does
a baseband waveform create RF sidebands?" Begin with multiplication as spectral
translation, then inspect the message, signed envelope, RF waveform, and
spectrum one at a time. Have me predict the carrier plus/minus message
frequencies before reading the baseline. Compare a single tone with the
multitone message, then use the depth and message-frequency sweeps to connect
baseband cause to RF effect. Use the over-modulated case to make me explain why
magnitude-envelope recovery folds while coherent mixing preserves sign. Focus
on physical interpretation rather than MATLAB syntax.
