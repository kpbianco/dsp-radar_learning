# P17 Walkthrough: Watch the Difference Frequency Rotate

## Guiding question

How does multiplying by a complex oscillator move an RF/IF signal to baseband?

Run `experiment.m` from the top with its visible controls unchanged. The script
uses a private deterministic seed, writes no files, and retains labeled metrics
in `results`.

## Baseline

1. In the first panel, inspect only the real 240 Hz passband measurement. Its
   rapid oscillation hides the fixed carrier phase.
2. In the second panel, compare real and imaginary mixer outputs before the
   low-pass. They still contain rapid motion because multiplication created both
   a difference term and a `-480 Hz` sum-frequency image.
3. In the filtered panel, read the nearly constant I and Q values. The exact
   240 Hz LO made `fc-fLO = 0 Hz`; it did not erase the carrier's phase.
4. In the I/Q panel, locate the stationary point near angle `0.35 rad` and
   magnitude `1 V`. The displayed magnitude includes a labeled `2x` calibration;
   `results.unscaled_mixer_gain` should be near one half.
5. In the spectrum figure, follow the copies from `+/-240 Hz`, to `0` and
   `-480 Hz`, then see the FIR keep only the term near zero.

Expected observation: multiplication changes the frequency coordinates of both
RF spectral copies. The explicit FIR selects the desired difference term, and
the explicit gain accounts for a real cosine splitting across two copies.

## Sweep 1 — Change only LO frequency

The third figure holds carrier, phase, amplitude, sample rate, record, filter,
and the exact same noise samples fixed. Only LO frequency changes through 204,
240, and 276 Hz.

1. Before reading the titles, compute `240-fLO` for each row.
2. At 204 Hz, follow the counterclockwise circle and confirm `+36 Hz`.
3. At 240 Hz, find the stationary point at `0 Hz`.
4. At 276 Hz, follow the clockwise circle and confirm `-36 Hz`.
5. Compare `results.lo_sweep_amplitude_v`; the signed translation changes while
   calibrated magnitude stays near 1 V.

Expected observation: an LO above the carrier is not broken. Complex I/Q keeps
the negative sign that a real-only baseband representation would obscure.

## Sweep 2 — Change only LO phase

The fourth figure fixes LO frequency exactly on the carrier and changes only LO
phase through `0`, `pi/2`, and `pi` radians.

1. Predict the output angle with `phiBB = 0.35 - phiLO`.
2. Watch the stationary I/Q point rotate clockwise as LO phase increases.
3. Confirm the magnitude stays near 1 V and frequency remains zero.

Physical connection: frequency offset controls how fast the relative phasor
rotates; phase offset controls where that phasor starts. A coherent radar
receiver must keep both conventions consistent across channels and pulses.

## Broken case — Select the conjugate RF side

The final figure uses a 216 Hz LO, where the intended negative-exponent mixer
should produce `240-216 = +24 Hz`.

1. Inspect the left trajectory after the script deliberately changes the
   oscillator to `exp(+j*2*pi*fLO*t)`.
2. Observe clockwise motion and the estimated `-24 Hz` result. Signal magnitude
   still looks healthy, which makes this sign failure easy to miss.
3. Compare the recovered right trajectory after restoring the negative
   exponent. It rotates counterclockwise at `+24 Hz`.

Failure interpretation: a real waveform contains both conjugate RF sides. The
wrong oscillator sign selected the other copy and reversed frequency/phase; it
did not demonstrate failed mixing or an empty channel.

Recovery: restore the receiver's declared negative-exponent convention and
verify signed frequency with phase slope or a signed spectrum. Do not repair the
error by taking absolute frequency, because that throws away side-of-LO
information.

## Concept connection

- P11 supplies the signed FFT axis used to locate both mixer products.
- P12 explains why the real input begins with conjugate spectral copies.
- P16 packages a real waveform as one-sided analytic I/Q; that representation
  would not need the real-input one-half amplitude correction used here.
- P18 will contrast what real and complex sampling preserve about frequency
  sign.
- Radar Doppler sign, coherent phase, and channel calibration all depend on the
  same LO frequency/phase convention shown here.

## Safe rerun, cancellation, recovery, and rollback

All arrays and loops have fixed ceilings. Press Ctrl+C to cancel; no background
task or partial file remains. Correct a malformed value and rerun from the top.
The rerun removes prior P17-tagged figures and clears old `results` before
validation, then recreates the same private noise without changing the global
stream or unrelated figures.

Rollback removes only P17-owned module artifacts, P17/shared allowed lifecycle
tests, allowed catalog entries, and P17 evidence, then restores only P17's
manifest status to `scaffolded`. Preserve implemented P16, later canonical
identities, ignored `.learning/` state, and the operator's active-batch record.

## Completion handoff

Use `checks.md`, then give a two- or three-sentence teach-back that predicts
signed baseband frequency and rotation, explains the one-half real-input mixer
gain, and separates mixing from low-pass selection.
