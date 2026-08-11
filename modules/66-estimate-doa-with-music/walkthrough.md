# P66 walkthrough: Split, Starve, Miscount, Smooth

Guiding question: How can subspace methods resolve sources more finely than a conventional beam?

Run `experiment.m` once from this module directory. It creates six tagged
figures and retains the numerical record in `p66_results`.

## Baseline observation 1: find the subspace boundary

Look only at **P66 covariance and eigenspaces**.

The covariance has organized off-diagonal structure because plane waves impose
repeatable phase relationships across sensors. In the eigenspectrum, locate
the dashed boundary after eigenvalue two.

Expected observation: two eigenvalues stand above a noise-like cluster. Do not
label the first eigenvector “the left source” and the second “the right source.”
The pair jointly spans the signal subspace; eigenvector phase and basis rotation
inside that subspace are not physical source labels.

## Baseline observation 2: compare the questions each scan asks

Open **P66 Bartlett and MUSIC baseline**. The dotted vertical lines mark the
true `-3 deg` and `+3 deg` directions.

Expected observation: conventional Bartlett power is one broad shoulder, with
its midpoint higher than its values at both truth angles. MUSIC produces two
local maxima separated by a deep valley.

Concept connection: Bartlett measures power passed by a physical steered sum.
MUSIC takes the reciprocal of noise-subspace projection. Its narrow peaks are
direction-consistency evidence, not narrow receive beams or source-power bars.

## Sweep 1: source separation

Open **P66 source-spacing sweep**. The top panel uses positive contrast to mean
that the two truth angles sit above the midpoint valley. Only the two source
angles change; waveform samples, noise samples, power, array, and scan grid stay
fixed.

Expected observations:

- MUSIC already has positive contrast in the reviewed four-degree case;
- Bartlett is still merged there and separates only at a wider spacing; and
- at the tightest spacing, finite-data MUSIC has little valley margin even
  though its selected local maxima remain near the pair.

One-variable change: edit only `source_spacing_sweep_deg` within its reviewed
bounds. If you regenerate noise for every point, the curve mixes spacing with
luck and no longer isolates the physical cause.

## Sweep 2: SNR

In **P66 SNR and snapshot sweeps**, inspect the top row first. Only per-source
SNR changes.

Expected observation: the `lambda_2/lambda_3` eigengap grows with SNR and the
angle error falls sharply. The `-10 dB` case selects a noise-driven peak far
from one true source; the high-SNR cases localize both.

Common interpretation mistake: saying that higher SNR lengthened the aperture.
It did not. It separated the signal eigenvalues from the noise cluster, making
the estimated subspaces more reliable.

## Sweep 3: snapshot count

Now inspect the bottom row. Every point is a nested prefix of the same `0 dB`
512-snapshot record. Only covariance evidence length changes.

Expected observation: short prefixes can select a distant spurious maximum;
the long prefix localizes the pair. The eigengap and angle error may wiggle
rather than improve at every point because finite-record errors are random.

One-variable change: edit only `snapshot_sweep`. Keep every value at least the
element count and no larger than the shared record. More snapshots assume the
scene remains stationary; mixing different scenes would answer another
question.

## Sweep 4: assumed source number

Open **P66 assumed source-count sweep**. Every curve uses the same baseline
covariance. Only `K`, the number of eigenvectors assigned to the signal
subspace, changes.

Expected observations:

- `K=1` produces a merged peak near broadside;
- `K=2` produces the intended pair; and
- `K=3` and `K=4` retain the pair but admit additional noise-driven structure.

Common interpretation mistake: calling every extra maximum a weak source.
Changing `K` did not change the received data. It changed which measured
eigenvectors were allowed to count as noise.

## Broken case: coherent sources

Open **P66 coherence failure and smoothing recovery** and first compare only
the full-array coherent eigenspectrum and dashed broken-MUSIC curve.

The second source waveform is an exact fixed-phase multiple of the first. The
two physical angles remain `-3 deg` and `+3 deg`, and receiver noise is
unchanged.

Expected observation: there is only one dominant signal eigenvalue. Raw MUSIC
is still told `K=2`, but its selected maxima do not recover the true pair.
This is a model-rank failure, not low angular scan resolution.

## Recovery: spatial smoothing on unchanged data

Now inspect the solid smoothed-MUSIC curve. The recovery slices the same
ten-sensor record into four overlapping seven-sensor views, forms each sample
covariance, averages them, and scans with the matching seven-element steering
vector.

Expected observation: a second eigenvalue separates from the noise cluster and
the two peaks return near truth. No source sample or noise sample is regenerated.

Concept connection: subarray translation supplies different phase references,
which restores covariance rank for distinct ULA directions. The price is a
shorter effective aperture and reliance on shift-invariant calibration.

## Failure interpretation checklist

- No two baseline peaks: check steering-sign convention, eigenvalue ordering,
  assumed `K`, scan coverage, SNR, and snapshots.
- Tall peak at a wrong angle: inspect local maxima and eigengap; normalization
  makes the tallest curve point `0 dB` even when it is noise-driven.
- Extra peaks after increasing `K`: suspect a weakened noise-subspace projector,
  not new data.
- Coherent recovery still merged: check that contiguous subarray covariances
  were averaged and that the reduced-aperture steering vector is used.
- Bartlett seems “worse”: it is showing realizable steered output power; MUSIC
  is a model-based pseudospectrum with different units and assumptions.

## Cancellation, rerun, and resource behavior

Pressing `Ctrl+C` stops the foreground script. There is no worker, timer,
network request, file output, checkpoint, or partial persistent state. Rerun
the script to reconstruct the same bounded private record. Startup closes only
figures tagged `P66`, clears only `p66_results`, and preserves unrelated figures
and MATLAB's global random stream.

The reviewed ceilings are 16 elements, four sources, 512 snapshots, 1,001 scan
samples, eight cases per sweep, 20,000 private values per request, 1,000,000
working numeric values, and six tagged figures. Input validation rejects
malformed, inconsistent, or oversized controls before data and plots are built.

When these observations make sense, use `checks.md` and give the short
teach-back. Plot production alone does not satisfy personal completion.
