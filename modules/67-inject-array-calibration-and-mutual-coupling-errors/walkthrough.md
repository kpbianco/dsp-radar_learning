# P67 walkthrough: Break the Array Model, Then Repair One Direction

Guiding question: How sensitive are beamforming and DOA results to imperfect channels?

## Before running

The source at `-15 deg` is a strong interferer and the known calibration/desired
source is at `+10 deg`. Every ideal, impaired, and calibrated comparison reuses
the same operational waveforms and receiver noise. The calibration pilot and
its noise are also frozen but are independent of the operational record.

Prediction: which will show the more dramatic model-mismatch symptom in this
record—MUSIC angle bias or MVDR desired-response loss?

## Baseline observation 1: inspect the physical error

Run `experiment.m` and stop at **P67 physical array errors**.

Observe one plot at a time:

1. channel amplitudes are not identical;
2. channel phases have a seeded nonzero spread;
3. physical positions differ from their half-wavelength grid without changing
   sensor order; and
4. the coupling matrix moves some received voltage to adjacent sensors.

These are four ways to alter a steering vector before any algorithm runs.

## Baseline observation 2: compare the three spatial scans

Open **P67 spatial algorithm comparison**.

- Bartlett reports received spatial power through a conventional scan.
- Capon adapts the covariance at every trial angle.
- MUSIC reports reciprocal noise-subspace projection, not received power.

For calibrated data, the script first whitens the covariance and nominal scan
vectors with the known equalized receiver-noise covariance. This preserves the
white-noise assumption behind the MUSIC signal/noise eigenspace split.

For each row compare ideal, impaired, and calibrated curves. Record
`p67_results.impaired_music_peaks_deg` and
`p67_results.calibrated_music_peaks_deg`. The calibration should materially
restore the known `+10 deg` source, while the off-angle source can retain a
small residual bias.

Do not conclude that the narrowest curve is automatically the most accurate.
Check its peak against truth and remember which manifold the scan assumed.

## Baseline observation 3: evaluate the beam on the physical array

Open **P67 beam response and SINR**. The horizontal axis is the actual arrival
angle. The impaired curve evaluates the MVDR weights against the impaired
manifold, not against the nominal pattern that would make the constraint look
perfect.

Compare:

- `known_response_before_db` and `known_response_after_db`;
- interferer response in the three `*_mvdr_metrics` records; and
- analytical output SINR, including calibrated receiver-noise coloring.

Expected observation: MVDR can lose far more desired response than the MUSIC
peak moves. One algorithm protects an exact assumed vector; the other searches
for approximate subspace orthogonality.

## Sweep 1: scale gain, phase, and position error severity

Open **P67 channel-error severity sweep**. Only
`error_scale_sweep` changes. It scales three frozen per-element manufacturing
error patterns together; mutual coupling and every data/noise record stay
unchanged.

Inspect the known-source response first. As the physical signature moves away
from the nominal signature, uncalibrated MVDR can self-null the desired source.
The known-source pilot makes the calibrated response remain close to the
promised look response.

Then inspect MUSIC angle RMSE. Do not demand monotonic movement at every point:
different fixed error components can partly cancel at one angle. The valid
connection is that model mismatch changes the subspace/steering alignment and
calibration anchors one reviewed direction.

## Sweep 2: vary only mutual coupling

Open **P67 mutual-coupling sweep**. Only one base coupling-strength control
changes; the next-nearest term follows its fixed `0.30*c^2` rule. Coupling
phase, gain, phase, position, pilot, sources, and noise are unchanged.

The lower plot is the key: it measures residual calibrated manifold error at
the off-angle `-15 deg` source. A one-look diagonal calibration can make the
known `+10 deg` response accurate without learning a global inverse of `C`.
Increasing direction-dependent mixing therefore leaves angle-dependent
residuals.

Do not interpret a nonmonotonic MUSIC RMSE point as proof that added coupling
is beneficial. This is one deterministic covariance record; use the direct
off-angle manifold-error metric to see the controlled mechanism.

## Broken case: silently assume the pilot came from broadside

Open **P67 broken calibration and recovery**. The broken operation is

```text
Ewrong = diag(1 ./ bhat_c).
```

It removes the measured phase ramp instead of mapping it back to the known
`+10 deg` nominal ramp. The first subplot shows the known source becoming an
all-ones, broadside-like vector. The second subplot shows the resulting
Bartlett, Capon, and MUSIC error on the unchanged operational record.

Inspect `p67_results.wrong_music_rmse_deg`. The failure is metadata/model
error, not low calibration SNR.

## Recovery: restore the known steering phase

The recovery uses

```text
qhat = bhat_c ./ a0(theta_c)
E = diag(1 ./ qhat).
```

Compare the broken MUSIC curve with recovered MUSIC. No waveform, receiver
noise, pilot, or calibration-noise sample changes. Recovery comes only from
using the correct known-source model.

## Common interpretation mistakes

- “Calibration found every gain, position, and coupling coefficient.” No. It
  estimated one composite response vector at one angle.
- “The MVDR constraint proves unity response to the real desired source.” It
  proves unity response to the assumed steering vector.
- “MUSIC height is received source power.” It is reciprocal projection on an
  estimated noise subspace.
- “Normalize every physical beam curve and the mismatch is gone.” Independent
  normalization can hide absolute desired-response loss; P67 retains that
  metric separately.
- “A restored calibration angle validates all angles.” Position and coupling
  effects are direction dependent.
- “Calibration leaves receiver noise unchanged.” Equalization scales and colors
  post-chain receiver noise; depending on the channel and weights, treating it
  as white can overstate or understate output SINR and breaks ordinary MUSIC's
  white-noise subspace interpretation.

## Cancellation, recovery, isolation, and resource bounds

The script runs in the foreground. Press `Ctrl+C` to cancel; there is no
worker, timer, callback, network request, file write, or external process to
continue afterward. A rerun closes only figures tagged `P67` and clears only
`p67_results`, so partial persistent state is not reused and unrelated figures
remain open.

The reviewed ceilings are 16 elements, three sources, 512 operational and 512
calibration snapshots, 1,001 scan samples, eight cases per sweep, 30,000
private deterministic values per request, 1,000,000 working numeric values,
and six tagged figures. Invalid, nonfinite, ill-conditioned, reordered-element,
or excessive configurations stop before a result is trusted.

## Concept connection and completion handoff

P61–P63 made geometry and receive phase alignment visible. P65 and P66 then
trusted that steering model for adaptive nulling and subspace DOA. P67 shows
the price of that trust. P68 will extend the same model-integrity problem into
space-time processing.

For the completion teach-back, answer in three parts:

1. name one visible symptom of steering-vector mismatch;
2. explain what the known-source correlation estimates; and
3. explain why that one-look diagonal estimate cannot globally remove position
   and mutual-coupling error.
