# P73 walkthrough: Separate Space from Slot Time

## Guiding question

How do multiple transmit and receive channels create more spatial samples?

Run `experiment.m` once from the top. It creates five figures tagged `P73` and
stores the reviewed arrays and metrics in `p73_results`. Follow one transition
at a time; the first observation is geometry, not MATLAB syntax.

## 1. Baseline geometry: add positions

Open **P73 physical and virtual geometry**. The upper panel shows four RX
antennas and two alternating TX antennas. The lower panel applies one visible
operation to every channel pair:

```text
x_virtual = x_TX + x_RX.
```

Expected positions in wavelengths:

```text
RX only:  [0, 0.5, 1.0, 1.5]
TX:       [0, 2.0]
virtual:  [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
```

Observe that the second TX is four receiver spacings from the first, so its
virtual block begins one `0.5 lambda` sample after the first block ends. There
is no duplicate and no gap. The physical receive aperture is `1.5 lambda`;
the virtual aperture is `3.5 lambda`.

## 2. Baseline beam pattern: compare aperture

Open **P73 RX-only and virtual beam comparison**. Both ideal curves match the
same `+18 deg` target, but the eight-position curve is substantially narrower.
Expected half-power widths are about `27.8 deg` and `13.5 deg`.

The lower panel scans deterministic `20 dB`-SNR data across `64` TDM cycles.
Both peaks should be close to `+18 deg`. The stationary baseline has no
inter-TX Doppler phase, so the position-sum interpretation is valid.

Do not call the virtual points eight simultaneous receivers. Four RX voltages
are sampled in each slot; orthogonal TX identity makes the two slot groups
separable and geometry lets them be treated as virtual positions.

## 3. Sweep 1: change only target separation

Open **P73 target-separation sweep**. Target powers are equal and incoherent,
their midpoint remains broadside, and the geometry, wavelength, scan grid, and
noise-free ideal model stay fixed. Only separation changes through
`[8, 16, 28] deg`.

At `16 deg`, inspect the upper panel:

- the four-RX curve has one merged broad maximum;
- the virtual curve has two maxima near the two truth markers; and
- the midpoint dip quantifies the visible separation.

The lower panel shows all three cases. At `8 deg` neither array resolves the
pair. At `28 deg` both do. The middle case isolates the useful resolution
region created by the larger virtual aperture.

Try changing only the middle separation from `16` to `20 deg`. Predict a
deeper virtual midpoint dip while the RX-only response remains merged. Restore
`16` afterward so the reviewed assertions describe the canonical experiment.

## 4. Sweep 2: change only radial velocity

Open **P73 velocity and TDM phase sweep**. Geometry, true `+18 deg` angle,
slot separation, SNR, cycles, and the deterministic noise array stay fixed.
Only radial velocity changes through `[-10, -5, 0, 5, 10] m/s`.

The upper panel is the temporal phase added between TX groups:

```text
Delta_phi_TDM = -2 pi (2v/lambda) T_slot.
```

The lower panel compares two angle paths. The uncompensated estimate moves
with velocity even though the target direction does not. Positive approaching
motion biases this dechirped-convention scan toward more-positive angle;
receding motion biases it toward more-negative angle. The compensated estimates
remain near `+18 deg`.

Try changing only the endpoint magnitude from `10` to `8 m/s` in both the
sweep and broken-case controls. Predict a smaller inter-TX phase and smaller
uncompensated bias. Restore `10` afterward.

## 5. Broken case: pretend sequential channels were simultaneous

Open **P73 broken motion phase and recovery**. The script reuses the existing
`+10 m/s` sweep record. No data are regenerated.

In the upper panel, the red phase trace contains a step at the boundary between
TX groups. The naive model calls all of that phase spatial, so the lower red
scan misses the true `+18 deg` direction by more than four degrees. This is not
a larger physical aperture or a new target angle. It is motion accumulated
during the `40 us` slot separation.

## 6. Recovery: estimate Doppler from like-with-like looks

The lag-one estimator compares each channel with itself one complete two-slot
cycle later. It therefore observes slow-time target rotation without crossing
from one TX position to another. Expected broken-case values are approximately:

```text
true Doppler                 +5.133 kHz
TX2-versus-TX1 phase         -1.290 rad
uncompensated angle          more than 4 deg high
recovered angle              within 0.3 deg of +18 deg
```

The blue trace applies `exp(+j 2 pi f_d_hat t_slot)` to each channel at its
known TX slot time. The spatial phase becomes smooth and the scan returns to
truth. Confirm that `broken_data` is unchanged and `recovered_data` is a new
derived array.

## Expected observations

- TX/RX position sums create eight unique half-wavelength virtual samples.
- Virtual aperture, not display density, narrows the beam.
- The `16 deg` equal-target pair is resolved virtually but not by four RX
  positions alone.
- Zero velocity adds zero inter-TX temporal phase.
- Velocity changes the naive angle even while true direction remains fixed.
- Same-TX Doppler estimation and known slot timing recover the unchanged data.

## Common interpretation corrections

- If you counted eight physical RX antennas, return to Figure 1: there are
  four RX channels reused under two TX illuminations.
- If you doubled every position because radar is monostatic, remove that
  factor; the virtual position is already the TX/RX path sum.
- If you say the dechirped steering sign matches P61's raw sample, include the
  conjugation introduced by `tx .* conj(rx)`.
- If you say zero-padding or scan-grid spacing improved resolution, compare
  the physical apertures.
- If you call compensation automatic, identify where the Doppler estimate and
  slot times came from and check their ambiguity limits.

## Cancellation, rerun recovery, isolation, and rollback

Press `Ctrl+C` between sections if needed. The script has no worker, timer,
network request, file write, or external process to cancel. An interruption
can leave partial P73 figures and workspace arrays, but no external persistent
state. Rerun from the top to close only figures tagged `P73`, rebuild
`p73_results`, and recreate the exact private deterministic noise. Unrelated
figures and variables are not broadly cleared.

Repository rollback is local to P73: remove its four implementation artifacts,
focused test, evidence, and catalog summary; restore its scaffold README and
only its manifest status to `scaffolded`. Preserve P72, later module identities,
ignored `.learning/` progress, and operator-managed contract activation.

## Completion connection

Explain in a few sentences why `x_TX+x_RX` increases spatial samples and
aperture, what the separation sweep proves, why TDM motion becomes a false
spatial phase, and how a same-TX Doppler estimate repairs the unchanged record.
