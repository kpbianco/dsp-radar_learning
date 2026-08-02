# P21 Walkthrough — Follow Baseband Energy into RF

## Guiding question

How does a baseband waveform create RF sidebands?

P20 is the immediate curriculum prerequisite. P11–P17 provide the FFT,
analytic-signal, and mixing operations used here; P18–P20 provide signed
frequency and coherent-receiver context.

## Baseline

1. Run `experiment.m` unchanged. Private seed `1021` generates the small RF
   noise vector without changing MATLAB's global random stream.
2. Before reading the spectrum, predict the three line locations for a
   `3000 Hz` carrier and `200 Hz` message.
3. In **Baseline AM in time**, inspect the normalized message first. Then
   compare the positive signed envelope with the fast RF voltage inside it.
   Modulation depth `0.60` keeps the signed envelope between `0.4 V` and
   `1.6 V`.
4. Compare envelope and coherent recovery against the message. Their small
   differences are due to the same seeded `0.005 V RMS` receiver noise.
5. In **Carrier and sidebands**, locate `2800`, `3000`, and `3200 Hz`. Read the
   measured line amplitudes in volts. The two sidebands should be close to the
   predicted `Ac*mu/2 = 0.30 V`.
6. Do not interpret the lower line as a negative RF frequency. “Lower” means
   below the positive `3000 Hz` carrier.

Expected observation: one baseband tone produces equal RF lines at the carrier
plus and minus the message frequency. Message frequency controls their offset;
depth controls their amplitude.

## Multitone transition

1. Move to **Multitone sideband mapping**. The message contains `100 Hz` with
   weight `0.60` and `350 Hz` with weight `0.40`.
2. Predict four sidebands before reading the plot: `fc +/- 100 Hz` and
   `fc +/- 350 Hz`.
3. Match each sideband pair to its message component. The heavier `100 Hz`
   component should make the larger pair.
4. Confirm that carrier, depth `0.60`, record, detector operations, and the exact
   receiver-noise samples remain fixed from the baseline. Only message content
   changes. Compare both recovered messages with the composite truth; weights
   summing to one keep the signed envelope nonnegative.

Expected observation: a multitone message does not make one vaguely wider
line. Each component produces its own symmetric pair with amplitude
proportional to its message weight.

## Sweep 1 — change only modulation depth

1. Inspect **Modulation depth sweep** at `mu = [0.20 0.60 1.00 1.40]`.
2. Confirm that message frequency, carrier, record, and detector operations
   stay fixed. This sweep changes only modulation depth and uses clean RF so
   noise cannot hide the mechanism.
3. Follow the minimum signed envelope. It is positive below one, reaches zero
   at one, and becomes negative above one.
4. Compare recovery RMSE. Magnitude-envelope and coherent recovery agree
   through `mu=1`; envelope error rises at `1.40`, while coherent error remains
   at numerical precision.

Expected observation: increasing depth grows sidebands linearly until the
signed envelope crosses zero. Crossing zero, not merely making “large
sidebands,” is the cause of ideal envelope-detector distortion.

## Sweep 2 — change only message frequency

1. Inspect **Sideband spacing sweep** at message frequencies
   `[100 200 400 700] Hz`.
2. Confirm that the `3000 Hz` carrier, modulation depth `0.60`, carrier
   amplitude, sample rate, and duration stay fixed. Only message frequency
   changes.
3. Watch the lower line move downward and the upper line move upward by equal
   amounts.
4. In the offset panel, compare both measured offsets with the diagonal
   expected line. Each offset should equal the message frequency to within the
   `10 Hz` FFT grid, and these coherent cases land exactly on bins.

Expected observation: doubling message frequency doubles sideband spacing but
does not change the ideal sideband amplitude for the fixed message amplitude
and depth.

## Broken case — over-modulated envelope recovery

1. In **Over-modulation failure and recovery**, inspect the signed envelope at
   depth `1.40`. It reaches `-0.4 V` during negative message peaks.
2. Compare it with the analytic-signal magnitude. Magnitude cannot be negative,
   so every inverted interval is folded upward.
3. In the RF panel, interpret a negative signed envelope as a 180-degree
   carrier phase reversal—not as negative voltage being impossible.
4. Compare recovered messages. The ordinary envelope detector is intentionally
   broken because it discarded sign. The coherent mixer uses a phase-aligned
   carrier, low-passes explicitly, and retains that sign.
5. Read the normalized RMSE values and the inverted-sample fraction. These
   metrics distinguish a visible fold from small numerical error.

Failure interpretation: over-modulation violates the nonnegative-envelope
assumption of magnitude detection. It does not contradict the AM spectrum or
prove that a phase-referenced coherent receiver must fail.

## Recovery, cancellation, isolation, compatibility, and bounds

- Rerun from the top unchanged to recover the canonical result. Use the two
  predefined sweep vectors for controlled changes; the fixed guards reject
  malformed, nonfinite, noncanonical, or oversized controls before signal
  allocation, FFT work, cleanup, or figures.
- Execution is foreground-only with two four-case sweeps, 2000 samples, six
  fixed figure groups, no unbounded loop, timer, worker, file, network, audio,
  device, or external transaction. Ctrl+C is the direct cancellation path.
- Ctrl+C after validation can leave a partial P21 figure set and
  empty/incomplete `results`. Rerun from the top to replace only P21-tagged
  figures and rebuild the same vectors from the private seed.
- P21 cleanup does not close other modules' figures, alter the global random
  stream, write files, or change ignored `.learning/` progress.
- The script uses base MATLAB operations. Its explicit FFT analytic and
  low-pass masks avoid toolbox compatibility and licensing dependencies. The
  largest record is 2000 samples, each sweep has four cases, and conservative
  numeric storage stays at or below 200000 values.
- Rollback removes only P21-owned artifacts, tests, evidence, and allowed
  catalog/lifecycle text, then restores only P21's manifest/index status to
  `scaffolded`. Preserve implemented P20, later module identities, managed
  contracts, workflows, and local learner progress.

## Concept connection and completion handoff

P17 translated a signal by mixing with an oscillator; P21 shows the same
operation from the transmitter side and keeps both real-cosine copies. P16's
analytic magnitude supplies envelope recovery, while P17's phase-referenced
mixing supplies coherent recovery. Later modulation and radar modules will use
the same baseband-to-RF mapping with richer messages.

Before personal completion, predict the RF locations produced by one new
baseband frequency and explain why a coherent receiver can recover an
over-modulated message that an envelope detector folds. Then give the
teach-back in `checks.md`; personal completion remains a manual learner action.
