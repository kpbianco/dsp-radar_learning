# P82 walkthrough: From Illuminator Leakage to a Target Peak

## Guiding question

How can a known broadcast-like reference reveal delayed Doppler-shifted echoes without transmitting?

Run `experiment.m` from this module directory. Keep the Command Window visible
and inspect one figure group at a time. The script uses base MATLAB R2016b+ and
seeded private samples; it does not require a toolbox, recording, network, or
transmitter.

## Baseline transition 1: identify the two ears

In **P82 passive channels and reference spectrum**:

1. Read the upper traces as two receivers, not transmit and receive signals.
2. The surveillance trace divided by direct gain resembles the reference
   because leakage dominates it.
3. The lower panel shows a broad complex-baseband spectrum. Broad waveform
   variation is what makes different delays distinguishable.

Expected observation: the weak target is not obvious in the raw magnitude.
Nothing is wrong; delay-Doppler coherence, not a time-trace bump, is the useful
measurement.

## Baseline transition 2: compare before and after on one scale

Open **P82 ambiguity before and after direct cancellation**.

1. In the left panel locate `(0 km, 0 Hz)`. This is the strong direct path.
2. Notice that both matched-voltage panels use the left panel's peak as `0 dB`.
3. In the right panel find the target near `36 km` excess path and `+500 Hz`.
4. Check the printed peak coordinates and target-to-median contrast.

Expected observation: before cancellation the global peak is `(0 samples,
0 Hz)`; afterward it is `(24 samples, +500 Hz)`. The delayed stationary
multipath remains near `(11 samples, 0 Hz)`, demonstrating that a one-tap
canceller is not multipath cancellation.

Do not call `36 km` target range. It is (c\tau), the received path-length
excess relative to the direct signal. Bistatic geometry is required to turn
that contour into a position.

## Controlled change 1: move delay only

In the left panel of **P82 target delay and Doppler sweeps**, the target delay
takes values `[12 24 48]` samples. Doppler, channel gains, waveform, noise, and
integration time stay fixed.

Expected observation: estimated delay follows the truth line while the
estimated Doppler remains `+500 Hz`. Delay selects which shifted reference copy
matches; it does not create the Doppler phase rotation.

## Controlled change 2: move Doppler only

Now use the right panel. The target Doppler takes `[-500 0 +500] Hz`; delay
stays at 24 samples.

Expected observation: estimated Doppler preserves sign and follows the truth
line while estimated delay remains 24 samples. At `0 Hz`, the target enters the
stationary-clutter row but is still separated by delay in this small model.

This pair of sub-sweeps is a coordinate check: delay moves columns; Doppler
moves rows. If the `+500 Hz` generated echo appeared at `-500 Hz`, the trial
phasor sign would be reversed.

## Controlled change 3: collect longer

In the left panel of **P82 integration and reference-quality sweeps**, compare
`5.12`, `10.24`, and `20.48 ms` prefixes of the same deterministic record.

Expected observation: target-to-median contrast rises by several decibels per
doubling, while nominal (1/T) Doppler resolution falls. Longer coherent time
adds the modeled target phase consistently. It does not improve the waveform's
delay bandwidth.

In real passive radar, clock offset, oscillator offset, acceleration, and
channel change can stop this gain. The lesson's exact coherence is a controlled
limit, not an operational promise.

## Controlled change 4: damage the reference

In the right panel, read reference quality from `35` down to `5 dB`; the axis
is intentionally reversed so quality worsens left-to-right. The surveillance
record does not change.

Expected observation: normalized target coherence declines. At high quality
the target owns the map; at `5 dB` it no longer does. A noisy reference weakens
both echo matching and reconstruction of leakage.

Common mistake: interpreting this as a target-SNR sweep. Target voltage and
surveillance noise are fixed. Only the receiver's knowledge of the illuminator
is degraded.

## Intentionally broken case: leave most leakage behind

Open **P82 under-cancellation and recovery**.

1. The broken panel subtracts only `20%` of the least-squares coefficient.
2. The origin remains dominant on the shared scale.
3. Recovery discards the broken residual, starts from the unchanged reference
   and surveillance channels, and applies the full coefficient.

Expected observation: the recovered map exactly matches the baseline
post-cancellation map. This is processing recovery, not recovery of an external
device or persistent transaction.

If the run or graphics window blocks, interrupt the foreground script with
Ctrl+C and rerun it. The loops are finite and bounded; there is no file,
network, worker, timer, GPU, callback, or asynchronous job to cancel. Rerun
closes only stale figures tagged `P82` and reconstructs the same inputs.

## Connect the result

Complete this sentence aloud:

> A passive target becomes visible when the surveillance channel contains a
> delayed, phase-rotating copy that matches the measured reference, but strong
> reference-correlated leakage must first be suppressed because ...

A complete answer should mention coherent summation, the zero-delay/zero-
Doppler origin, reference quality, and the limitation of one-tap cancellation.

## Completion handoff

Use `checks.md` for observation and prediction checks. Before personal
completion, teach back:

1. why the receiver needs two channels;
2. what positive delay and positive Doppler mean in the implemented equation;
3. why the direct path wins before cancellation;
4. why longer CPI helps only while coherence holds; and
5. why a practical canceller needs more than this one coefficient.

To roll back this governed implementation, restore the P82 scaffold README,
remove only its four added lesson artifacts, tests, and evidence, and return
only P82's manifest/catalog state to scaffolded. Preserve P81, future module
identities, learner state, and the operator-managed active-batch contract.

Repository validation is static/simulated unless an actual MATLAB command,
version, output, and artifacts are retained. It does not establish physical
radar/HIL, field, RT1/RT2, Unreal, signing, deployment, or production evidence.
