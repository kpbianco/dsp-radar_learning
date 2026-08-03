# P32 walkthrough: Perform LFM Pulse Compression

Guiding question: **How can a long energetic pulse achieve short-pulse range resolution?**

Run `experiment.m` once from the module folder. It is bounded, uses base MATLAB
only, and recreates a private deterministic noise stream without changing the
global random stream.

## Baseline observation: long in, narrow out

Start with Figures 1–3 and the printed baseline metrics.

1. In Figure 1, follow the I/Q rotation and the straight instantaneous-frequency
   line. The pulse magnitude is constant even though it occupies 8 MHz.
2. In Figure 2, compare the 10 microsecond raw echo extent with the 75 m target
   spacing. The long target echoes overlap across roughly 1,499 m of apparent
   range.
3. In Figure 3, find the two compressed peaks. The filter aligns the frequency
   history only at each target's delay.
4. Compare the printed measured full -3 dB width with `c/(2B)`. They should be
   similar scales, not identical definitions.

Expected observation: a long raw pulse can produce a narrow delay response
because duration and bandwidth are separate controls.

## Sweep one variable: bandwidth only

Figure 4 uses `[4 8 16]` MHz while holding duration at 10 microseconds and
holding the scene, amplitudes, sampling rate, and noise basis fixed.

- Read the measured width at each bandwidth.
- Double `B` mentally before looking at the next point: the nominal `c/(2B)`
  range scale should halve.
- Notice that this sweep does not add pulse samples. It changes phase slope and
  compressed width, not transmitted duration.

Expected observation: the measured widths decrease monotonically, following
the inverse-bandwidth trend.

## Sweep one variable: duration only

Figure 5 uses `[5 10 20]` microseconds while holding bandwidth at 8 MHz and
holding the scene, peak amplitude, sampling rate, and noise convention fixed.

- The upper plot should remain nearly level: fixed bandwidth preserves the
  compressed-width scale.
- The lower plot rises from `BT=40` through `80` to `160`, so the predicted
  processing gain rises by 3 dB whenever duration doubles.
- Connect this to energy: at fixed peak power, twice the duration sends twice
  the energy.

Expected observation: duration buys coherent energy without surrendering the
resolution supplied by bandwidth.

## Read the two processing-gain labels

The script prints sampled coherent gain `10*log10(Fs*T)` and waveform-bandwidth
processing gain `10*log10(B*T)`. Do not compare one label with the other's input
SNR. The measured value uses the same seeded white-noise record and references
input noise to the waveform's `B`-Hz bandwidth.

## Intentionally broken case: wrong replica chirp rate

Figure 6 compresses the isolated first echo with a replica using `0.55B`.
Both traces share the recovered exact-replica peak as the 0 dB reference.

- Observe that its energy spreads across a much wider range interval.
- Observe that its peak is lower on the shared dB scale and may move away from
  the true delay.
- Interpret the failure physically: the replica removes only part of the
  transmitted phase rotation, so the samples cannot add coherently.

This is a model mismatch, not random loss of resolution and not evidence of a
new target.

## Recover and connect the concept

The recovery restores `fliplr(conj(transmit_chirp))`, reconstructs the private
seed, and asserts that both noise and compressed baseline match exactly. The
narrow response returns because the receiver again knows the transmitted phase
history.

Say the connection in one sentence: **bandwidth determines the compressed delay
width, while duration supplies energy that the matched filter adds coherently.**

## Safe cancellation, clean rerun, and rollback

- Press Ctrl+C to cancel. All loops are finite; there is no worker, timer,
  network call, file write, external transaction, or hardware session to leave
  running.
- Rerun the whole script for recovery. It closes only figures tagged `P32`,
  creates the same private seed, and leaves the global random stream unchanged.
- The experiment never reads or writes `.learning/`; personal completion stays
  under the learner CLI.
- Batch rollback removes the P32 artifacts and test, restores this module's
  scaffold README and manifest status to `scaffolded`, and restores the public
  catalogs. It does not change P01–P31 or any later module identity.

Completion means you can predict how bandwidth changes compressed width and
how time-bandwidth product changes gain.
