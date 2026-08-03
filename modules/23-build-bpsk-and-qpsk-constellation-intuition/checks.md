# P23 Checks — Symbols, Phase States, and Decisions

## Guiding question

What do symbols, phase states, and decision regions look like in IQ?

Use one plot and one metric at a time. These checks test prediction and
interpretation, not MATLAB syntax.

## Baseline observations

1. For BPSK bit 0 and bit 1, what are the two ideal I coordinates? What is Q?
2. For QPSK bits `[1 0]`, which signs should I and Q have under this module's
   mapping?
3. Why is each QPSK coordinate divided by `sqrt(2)`?
4. In the baseline cluster plot, which feature signals noise and which feature
   signals carrier phase error?
5. Which exact sign tests produce the hard BPSK and QPSK decisions?

## Sweep predictions

1. Before reading Sweep 1, predict what stays fixed and what changes when
   `Eb/N0` moves from -4 to 8 dB.
2. At equal `Eb/N0` and zero phase error, why should normalized BPSK and QPSK
   have similar bit-error behavior even though QPSK carries two bits per symbol?
3. Before reading Sweep 2, predict whether QPSK first loses decision margin
   near 45 or 90 degrees.
4. Which pair of adjacent QPSK symbols becomes confused when rotation pushes a
   point across I=0? Which bit changes?
5. Why can BPSK retain the correct I sign at 50 degrees while a QPSK coordinate
   has already crossed a boundary?

## True or false

1. Lower SNR rotates all constellation centers by the same angle. **False.**
   It increases random spread around their average locations.
2. A constant phase error increases the magnitude of every ideal symbol.
   **False.** Rotation preserves magnitude.
3. QPSK has four ideal points and therefore carries four bits per symbol.
   **False.** Four choices encode `log2(4)=2` bits.
4. At exactly 45 degrees, an ideal QPSK center can lie on a fixed decision
   boundary. **True.** Its nearest-axis decision margin is zero.
5. Raising SNR repairs a 55-degree uncorrected QPSK phase error. **False.** It
   tightens clusters in the wrong quadrants.
6. Exact derotation also rotates circular receiver noise. **True.** Its
   distribution is unchanged even though each realized sample rotates.

## Broken-case diagnosis and recovery

1. Why is high BER at `Eb/N0=16 dB` evidence against “not enough power” as the
   broken-case diagnosis?
2. Which fixed boundary does each rotated QPSK state cross at 55 degrees?
3. What receiver assumption is intentionally broken? The hard decisions assume
   a phase-aligned carrier reference.
4. Why does multiplying by `exp(-j*phi_hat)` recover the geometry when
   `phi_hat=phi`?
5. If the estimate were 5 degrees low, what residual rotation would remain?

## Malformed input, resource, and operational checks

- A logical seed, nonfinite SNR, complex phase angle, changed sweep vector,
  noninteger or oversized symbol count, excessive display count, or expanded
  figure/numeric-storage ceiling must stop before random generation,
  allocation, P23 cleanup, or figure creation.
- Ctrl+C provides bounded timeout/cancellation. A full rerun replaces only
  P23-tagged figures and rebuilds workspace variables from private seed `1023`
  without changing the global random stream.
- The script uses base MATLAB and no file, network, device, worker, learner
  state, or persistent external transaction, so cancellation has no external
  transaction to roll back.

## Teach-back completion

In two or three sentences, answer the guiding question. A complete answer must
map BPSK and QPSK bits to IQ points, distinguish noise spread from coherent
phase rotation, name the fixed decision boundaries, predict why QPSK becomes
confused near 45 degrees, and explain inverse-rotation recovery. Name one
limiting assumption: perfect symbol timing, known phase for recovery, circular
Gaussian noise, independent bits, or no pulse-shaping/multipath effect.
