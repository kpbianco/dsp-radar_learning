# P33 walkthrough: Control Pulse-Compression Sidelobes

Guiding question: **Why can a strong target hide a weak nearby target after matched filtering?**

Run `experiment.m` once from this module folder. It uses base MATLAB, bounded
arrays and loops, and a private deterministic noise stream without changing the
global random stream.

## Baseline observation: the strong target has structure around it

Start with Figures 1 and 2 and the printed baseline metrics.

1. In Figure 1, compare the rectangular and Hann-like receive weights. Then
   compare their isolated strong-target responses, each normalized to its own
   peak so response shape is visible.
2. Read the printed PSLR and full -3 dB widths. The Hann-like response should
   have much lower peak sidelobes and a wider mainlobe.
3. In Figure 2, locate the weak target about 63.7 m to the right of the strong
   one. With rectangular processing, its expected contribution is below the
   strong target's leakage. With the Hann-like filter, the clean leakage margin
   becomes positive and the noisy profile exposes the neighbor.
4. Read the output-SNR change separately. About -1.77 dB is the SNR trade; the
   roughly -6 dB raw peak change from summing smaller weights is not the same
   quantity.

Expected observation: sidelobe suppression can expose a weak nearby echo, but
the shaped response is wider and no longer has the rectangular matched
filter's maximum white-noise SNR.

## Sweep one variable: taper strength only

Figure 3 uses `alpha = [0 0.5 1]` while holding the LFM pulse, two-target
scene, target amplitudes, separation, and seeded noise basis fixed.

- Follow PSLR downward as cosine weighting becomes stronger.
- Follow full -3 dB range width upward.
- Keep the SNR label distinct from raw peak normalization.
- Find where the weak-peak/strong-leakage margin crosses 0 dB.

Expected observation: stronger tapering makes the baseline sidelobe less able
to mask the weak target, but the improvement is purchased with mainlobe width
and output SNR.

## Sweep one variable: target separation only

Figure 4 uses offsets `[7 13 17 32]` samples, approximately
`[26.2 48.7 63.7 119.9]` m. Weak amplitude, waveform, and both filters remain
fixed.

- At seven samples, both margins are negative: the target is too close for the
  chosen weak amplitude and responses.
- At 13 samples, the Hann-like leakage margin is already positive, although
  complex overlap can still prevent a distinct local maximum.
- At 17 samples, the rectangular response still has negative margin and no
  weak-target local peak, while the Hann-like profile exposes one.
- At 32 samples, both filters have positive clean leakage margin.
- Notice that the values need not change monotonically because sidelobes
  ripple with delay.

Expected observation: there is no filter that wins at every separation. The
target's location relative to both mainlobe and sidelobes matters.

## Intentionally broken case: choose by PSLR alone

Figure 5 applies the rule “always use the filter with the lowest PSLR” to the
seven-sample scene. The Hann-like filter is selected without checking its
wider mainlobe.

- The weak-target marker lies in the strong target's mainlobe region.
- The printed Hann-like visibility margin remains negative.
- Do not interpret the single broad feature as proof that the weak target is
  absent. The processing choice cannot separate it in this scene.

This is a broken decision rule, not a random noise failure and not evidence
that tapering never works.

## Recover and connect the concept

Figure 6 restores the validated 17-sample separation and reconstructs the
private noise seed. The script asserts exact equality with the original
Hann-like baseline. A real design could instead keep the closer scene and
choose a narrower filter, accepting higher sidelobes.

Say the connection in one sentence: **receive tapering lowers a strong target's
sidelobes, but it spends mainlobe width and output SNR, so weighting must match
the separation and dynamic-range problem.**

## Safe cancellation, clean rerun, and rollback

- Press Ctrl+C to cancel. Every loop is bounded; there is no worker, timer,
  network call, file write, external transaction, or hardware session to leave
  running.
- Rerun the whole script for recovery. It closes only figures tagged `P33`,
  recreates the same private seed, and leaves the global random stream
  unchanged.
- The experiment never reads or writes `.learning/`; learner completion stays
  isolated in the CLI's ignored local state.
- Batch rollback removes the P33 implementation artifacts, test, and evidence;
  restores the scaffold README and P33 manifest status to `scaffolded`; and
  restores the public catalogs. It preserves P01-P32 and every later module
  identity.

Completion means you can select weighting that reveals the weak target and quantify the resolution/SNR cost.
