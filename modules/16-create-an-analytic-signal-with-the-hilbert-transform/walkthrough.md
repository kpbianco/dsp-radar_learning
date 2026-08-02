# P16 Walkthrough: Follow the Complex Arrow

## Guiding question

How can a real waveform be represented by a complex envelope?

Run `experiment.m` from the top with its visible controls unchanged. The script
uses a private deterministic seed, writes no files, and retains labeled metrics
in `results`.

## Baseline

1. In the first panel, look at only the first 0.12 s of the real 240 Hz carrier.
   Its rapid zero crossings do not reveal the slowly changing amplitude directly.
2. In the envelope panel, compare the designed curve with `|analytic signal|`.
   The magnitude follows the 2 Hz amplitude modulation instead of crossing zero
   with the carrier.
3. In the phase panel, the unwrapped angle follows a steadily rising carrier
   phase with a small 3 Hz wobble.
4. In the frequency panel, that phase slope oscillates around 240 Hz with peak
   deviation `0.60*3 = 1.8 Hz`.
5. In the spectrum figure, compare the real signal's mirrored lobes with the
   analytic signal's one-sided spectrum. Confirm that `real(analytic_signal)`
   reconstructs the input to numerical precision.

Expected observation: one complex sequence exposes envelope and phase while
retaining the original real waveform as its real part. The explicit FFT mask
removes negative-frequency redundancy; it does not invent a second measurement.

## Sweep 1 — Change only envelope depth

The third figure keeps carrier, phase law, phase deviation, sample rate, record,
and noise realization fixed. Only envelope depth changes through 0.20, 0.60,
and 0.90.

1. Read the designed minima: 0.80, 0.40, and 0.10 V.
2. Compare each recovered magnitude with its designed envelope.
3. Compare the instantaneous-frequency traces. Their designed curve is identical,
   but the deepest envelope makes the same noise more influential near minima.

Expected observation: envelope depth controls complex-arrow length, not the
designed phase law. Confidence in angle and frequency nevertheless depends on
that length.

## Sweep 2 — Change only phase-deviation index

The fourth figure fixes envelope, carrier, modulation rate, record, and noise.
Only phase deviation changes through 0.20, 0.60, and 1.20 radians.

1. Predict the peak frequency deviations before reading the titles.
2. Confirm `beta*3 Hz` gives 0.6, 1.8, and 3.6 Hz.
3. Notice that the envelope is unchanged even as phase slope swings farther.

Physical connection: phase is accumulated frequency. A larger phase wobble at
the same rate requires a larger instantaneous-frequency excursion.

## Broken case — Trust phase at vanishing amplitude

The final figure uses the same designed phase but creates a short amplitude
notch with a 0.001 V minimum and adds 0.010 V RMS noise.

1. Find where recovered magnitude crosses the visible 0.05 V threshold.
2. Observe the phase error near the notch. The complex vector is so short that
   noise controls its direction.
3. Compare the raw frequency spike with the green amplitude-gated result.

Failure interpretation: the spike is not a physical 240 Hz carrier suddenly
accelerating. Phase has become ill-conditioned near the complex-plane origin,
and differentiation amplifies its jump.

Recovery: report instantaneous frequency only when analytic magnitude supports
a stable angle at both ends of the phase-difference interval. Mark rejected
samples unavailable (`NaN`); do not interpolate through them and pretend the
missing phase was measured.

## Concept connection

- P11 supplies the positive/negative FFT-bin map used by the mask.
- P12 explains why a real record has conjugate mirrored spectral content.
- P15 introduces time-varying frequency as a visible signal property.
- P17 will multiply this one-sided complex representation by a complex
  oscillator to move the carrier to baseband.
- Radar Doppler and coherent integration depend on phase only when return
  magnitude/SNR is sufficient.

## Safe rerun, cancellation, recovery, and rollback

All arrays and loops have fixed ceilings. Press Ctrl+C to cancel; no background
task or partial file remains. Correct a malformed value and rerun from the top.
The rerun removes prior P16-tagged figures and clears old `results` before
validation, then recreates the same private noise. Rollback removes only
P16-owned artifacts/catalog entries/tests/evidence and restores only P16's
manifest status to `scaffolded`; P15 and `.learning/` state remain intact.

## Completion handoff

Use `checks.md`, then give a two- or three-sentence teach-back that explains the
FFT mask, identifies magnitude and angle, and states why instantaneous frequency
must be rejected near a magnitude null.
