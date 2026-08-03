# P23 Walkthrough

## Guiding question

What do symbols, phase states, and decision regions look like in IQ?

Run `experiment.m` once without editing it. It uses private seed `1023`, closes
only figures tagged `P23`, and retains the important arrays and metrics in
`results`.

## 1. Baseline: connect bits to symbol coordinates

The first figure shows 24 of the 400 generated symbols. Follow one transition
at a time:

1. A BPSK bit selects either `I=-1` or `I=+1`; ideal Q stays zero.
2. Each QPSK symbol consumes an I-bit and a Q-bit.
3. Those two signs create one of four points at `(+/-1 +/- j)/sqrt(2)`.

Expected observation: BPSK has two phase states and one bit per symbol; QPSK
has four phase states and two bits per symbol. Both use unit symbol energy.

## 2. Baseline: see clusters and fixed decision regions

The second figure uses `Eb/N0=6 dB` and `phi=12 deg`. The black crosses are
ideal states, the colored dots are received symbols, and the black dashed lines
are the receiver's unchanged boundaries.

Inspect BPSK first. Noise creates I/Q spread and phase error lifts the two
centers off the I axis, but most I signs remain correct. Then inspect QPSK. Its
four centers rotate toward a neighboring boundary, so its minimum margin falls
faster. The lower panels mark actual bit errors by symbol index rather than
hiding them in a single BER number.

Expected observation: noise spreads individual points while phase error rotates
the cluster centers together.

## 3. Sweep 1: change SNR only

The third figure fixes phase error at zero and reuses the same bits and
standard-normal noise samples. Only

```text
Eb/N0 = [-4 0 4 8] dB
```

changes. The scale factors `sigma_BPSK` and `sigma_QPSK` shrink as SNR rises.
Compare `results.snr_sweep_bpsk_ber` and
`results.snr_sweep_qpsk_ber`.

Expected observation: the cluster centers stay on the ideal points while the
clouds tighten, so both BER curves are nonincreasing. Do not say the
constellation points move closer together; only the random displacement scale
changes.

## 4. Sweep 2: change carrier phase error only

The fourth figure restores `Eb/N0=8 dB`, reuses the same bits and noise, and
changes only

```text
phi = [0 15 30 50] deg.
```

Watch the entire QPSK constellation rotate while the I=0 and Q=0 decision
lines remain fixed. By 50 degrees every ideal center has crossed one of its
nearest boundaries. BPSK still has positive real projection because its
90-degree boundary margin is larger.

Expected observation: phase error moves centers coherently; it is not wider
noise. QPSK becomes confused by adjacent states first.

## 5. Broken case and recovery

The fifth figure intentionally applies an uncorrected `55 deg` rotation at a
high `16 dB Eb/N0`. This is not a low-SNR failure: the clusters are tight, but
they occupy the wrong decision regions. About one bit per QPSK symbol is at
risk, so the uncorrected BER remains near one half even as noise becomes small.

Recovery multiplies by the known inverse rotation:

```text
r_corrected = r*exp(-j*55*pi/180).
```

The recovered clusters return to the intended quadrants and the bounded seeded
case has zero recovered errors. In a real receiver the phase must be estimated;
using the exact value here isolates what carrier recovery is supposed to do.
Increasing SNR alone is not a recovery for a systematic reference error.

## Common interpretation mistakes

- The I and Q axes are orthogonal coordinates, not two successive time samples.
- The four QPSK points carry two bits each; four points do not mean four bits.
- QPSK is normalized by `sqrt(2)`, so each symbol—not each axis—has unit energy.
- A rotated cluster with small spread is a phase problem, not a noise problem.
- A bit error count and a symbol error count use different denominators.
- The plots show symbol-rate samples before P24 introduces pulse shape and
  matched-filter timing.

## Cancellation, recovery, isolation, and rollback

The base MATLAB script has fixed symbol, sweep, figure, and numeric-storage
ceilings and no worker, timer, network, file, device, or external transaction.
Ctrl+C is the timeout/cancellation path. Cancellation can leave caller
workspace variables, partial P23-tagged figures, and incomplete `results`; a
full rerun recreates all P23 values from the private seed and replaces only
P23-tagged figures. A rerun cannot restore a pre-existing caller variable that
the script overwrote.

The private `RandStream` does not change MATLAB's global random stream. The
experiment does not read or write `.learning/`, so learner progress is isolated
from simulation. Rollback removes only P23 artifacts/status/catalog/test
evidence and restores P23 to `scaffolded`; P22 and later canonical identities
remain unchanged.

## Completion connection

Before opening `checks.md`, explain aloud which geometry is changed by SNR,
which geometry is changed by phase error, and why an inverse phase rotation can
recover a tight cluster that more transmit power cannot.
